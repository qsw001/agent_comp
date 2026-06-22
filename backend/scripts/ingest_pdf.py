"""
PDF 入库脚本 — 解析 PDF → 分块 → 嵌入 → 写入 Qdrant

用法:
    cd backend
    PYTHONPATH=. python scripts/ingest_pdf.py --pdf-path ../data/随机过程及应用.pdf
    PYTHONPATH=. python scripts/ingest_pdf.py --pdf-path ../data/随机过程及应用.pdf --dry-run
    PYTHONPATH=. python scripts/ingest_pdf.py --pdf-path ../data/随机过程及应用.pdf --force
    PYTHONPATH=. python scripts/ingest_pdf.py --pdf-path ../data/random.pdf --collection my_collection

Python 3.9 兼容。
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# 将 backend/ 加入 sys.path，确保可导入 app 包
_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent  # backend/
sys.path.insert(0, str(_PROJECT_ROOT))

from app.rag.pdf_processor import (
    extract_pdf,
    detect_chapters,
    build_chunks,
    compute_content_hash,
)
from app.rag.vector_store import ensure_collection, insert_documents, get_qdrant_client


# ─── 常量 ──────────────────────────────────────────────────

DEFAULT_CHUNK_SIZE = 800       # 中文字符数
DEFAULT_OVERLAP = 100          # overlap 字符数
DEFAULT_SUBJECT = "随机过程及应用"
DEFAULT_COLLECTION = "learning_resources"
CACHE_SCHEMA_VERSION = 1


# ─── 缓存管理 ──────────────────────────────────────────


def _get_cache_dir() -> Path:
    """获取缓存目录（data/.ingest_cache/）"""
    cache_dir = _PROJECT_ROOT.parent / "data" / ".ingest_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_cache_file(source_stem: str) -> Path:
    """获取单个 PDF 的缓存文件路径"""
    return _get_cache_dir() / f"{source_stem}.json"


def load_cache(source_stem: str) -> Set[str]:
    """加载已入库的 content_hash 集合"""
    cache_file = _get_cache_file(source_stem)
    if not cache_file.exists():
        return set()
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "chunk_hashes" in data:
            return set(data["chunk_hashes"])
        if isinstance(data, list):
            return set(data)
    except (json.JSONDecodeError, KeyError, OSError):
        return set()
    return set()


def save_cache(
    source_stem: str,
    chunk_hashes: Set[str],
    pdf_path: Path,
):
    """持久化缓存（合并已有 + 新增 hash）"""
    existing = load_cache(source_stem)
    merged = existing | chunk_hashes

    cache_data = {
        "version": CACHE_SCHEMA_VERSION,
        "source_stem": source_stem,
        "pdf_path": str(pdf_path.resolve()),
        "pdf_size": pdf_path.stat().st_size,
        "chunk_hashes": sorted(merged),
    }

    cache_file = _get_cache_file(source_stem)
    cache_file.write_text(
        json.dumps(cache_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_cache(source_stem: str):
    """删除指定 PDF 的缓存文件"""
    cache_file = _get_cache_file(source_stem)
    if cache_file.exists():
        cache_file.unlink()
        print(f"  🗑️  已清除缓存: {cache_file.name}")


# ─── 统计 ──────────────────────────────────────────────


def print_statistics(
    *,
    total_pages: int,
    valid_pages: int,
    skipped_pages: int,
    ocr_pages: int,
    chapters: List[str],
    total_chunks: int,
    new_chunks: int,
    duplicate_chunks: int,
    elapsed: float,
    is_dry_run: bool = False,
):
    """打印格式化的统计报告"""
    bar = "═" * 50
    print(f"\n{bar}")
    if is_dry_run:
        print(" 📋 Dry-Run 报告（未写入任何数据）")
    else:
        print(" ✅ PDF 入库完成报告")
    print(bar)

    rows = [
        ("总页数", str(total_pages)),
        ("有效页数", str(valid_pages)),
        ("跳过页数", str(skipped_pages)),
        ("OCR 辅助页数", str(ocr_pages)),
        ("章节数", str(len(chapters))),
        ("Chunk 总数", str(total_chunks)),
        ("新增 Chunk", str(new_chunks)),
        ("重复 Chunk", str(duplicate_chunks)),
        ("耗时", f"{elapsed:.1f}s"),
    ]

    for label, value in rows:
        print(f"  {label:<18}: {value}")

    if chapters:
        print(f"  {'章节列表':<18}:")
        for ch in chapters:
            print(f"    • {ch}")

    print(bar)
    print()


# ─── 主流程 ──────────────────────────────────────────


async def run_ingest(
    pdf_path: Path,
    collection: str,
    chunk_size: int,
    overlap: int,
    subject: str,
    dry_run: bool,
    force: bool,
):
    """执行完整的 PDF 入库流程"""
    if not pdf_path.exists():
        print(f"❌ 文件不存在: {pdf_path}")
        sys.exit(1)

    if not dry_run:
        # 预先检查 Qdrant 连通性
        try:
            client = get_qdrant_client()
            client.get_collections()
        except Exception as exc:
            print(f"❌ 无法连接 Qdrant: {exc}")
            print("   请先执行: docker compose up -d qdrant")
            sys.exit(1)

    source_stem = pdf_path.stem
    t_start = time.time()

    # ── 1. 解析 PDF ─────────────────────────────────
    print(f"📄 正在解析: {pdf_path.name}")
    print(f"   集合: {collection}  |  chunk_size: {chunk_size}  |  overlap: {overlap}")

    raw_pages = extract_pdf(str(pdf_path), ocr_fallback=True)
    pages = detect_chapters(raw_pages)

    total_pages = len(pages)
    pages_with_text = [p for p in pages if p.get("has_text")]
    valid_pages = len(pages_with_text)
    skipped_pages = total_pages - valid_pages
    ocr_pages = [p for p in pages if p.get("ocr_used")]

    # 记录警告
    for p in pages:
        if not p.get("has_text"):
            warnings.warn(f"第 {p['page_num']} 页: 无有效文本（可能为空页或扫描页）")
        elif p.get("ocr_used"):
            warnings.warn(f"第 {p['page_num']} 页: 使用 OCR 提取（原始文本不足）")

    print(f"   总页数: {total_pages}  |  有效: {valid_pages}  |  跳过: {skipped_pages}")
    if ocr_pages:
        ocr_nums = [p["page_num"] for p in ocr_pages]
        print(f"   OCR 页: {len(ocr_pages)} 页 → 页码 {ocr_nums[:10]}{'...' if len(ocr_nums) > 10 else ''}")

    if valid_pages == 0:
        print("❌ PDF 中未提取到任何有效文本，终止处理")
        sys.exit(1)

    # ── 2. 识别章节 ─────────────────────────────────
    chapters_set: Set[str] = {p.get("chapter", "") for p in pages if p.get("chapter")}
    chapters = sorted(c for c in chapters_set if c)
    print(f"   识别到 {len(chapters)} 个章节")

    # ── 3. 分块 ─────────────────────────────────────
    print(f"🔪 正在分块 (size={chunk_size}, overlap={overlap}) ...")
    all_chunks = build_chunks(
        pages,
        source_file=str(pdf_path),
        subject=subject,
        chunk_size=chunk_size,
        overlap=overlap,
    )
    total_chunks = len(all_chunks)
    print(f"   生成 {total_chunks} 个 chunk")

    # ── 4. 去重（基于 content_hash 缓存） ─────────
    if force:
        clear_cache(source_stem)
        existing_hashes: Set[str] = set()
    else:
        existing_hashes = load_cache(source_stem)
        if existing_hashes:
            print(f"   缓存中有 {len(existing_hashes)} 个已知 chunk")

    new_chunks: List[Dict[str, Any]] = []
    duplicate_count = 0
    for ch in all_chunks:
        h = ch["content_hash"]
        if h in existing_hashes:
            duplicate_count += 1
        else:
            new_chunks.append(ch)

    print(f"   新增: {len(new_chunks)}  |  重复: {duplicate_count}")

    # ── Dry-Run 输出 ────────────────────────────────
    if dry_run:
        if new_chunks:
            print(f"\n─── Chunk 预览（前 5 个）───")
            for ch in new_chunks[:5]:
                print(f"  [{ch['chunk_id']}]")
                print(f"     title:      {ch['title'][:60]}")
                print(f"     chapter:    {ch['chapter'][:40]}")
                print(f"     page:       {ch['page_number']}")
                print(f"     hash:       {ch['content_hash'][:16]}...")
                print(f"     content:    {ch['content'][:100].replace(chr(10), ' ')}...")
                print()

        elapsed = time.time() - t_start
        print_statistics(
            total_pages=total_pages,
            valid_pages=valid_pages,
            skipped_pages=skipped_pages,
            ocr_pages=len(ocr_pages),
            chapters=chapters,
            total_chunks=total_chunks,
            new_chunks=len(new_chunks),
            duplicate_chunks=duplicate_count,
            elapsed=elapsed,
            is_dry_run=True,
        )
        return

    # ── 5. 写入 Qdrant ───────────────────────────────
    if not new_chunks:
        print("✅ 全部 chunk 已存在，无需入库")
        elapsed = time.time() - t_start
        print_statistics(
            total_pages=total_pages,
            valid_pages=valid_pages,
            skipped_pages=skipped_pages,
            ocr_pages=len(ocr_pages),
            chapters=chapters,
            total_chunks=total_chunks,
            new_chunks=0,
            duplicate_chunks=duplicate_count,
            elapsed=elapsed,
        )
        return

    # --force 时清除该源文件的旧记录
    if force:
        try:
            client = get_qdrant_client()
            source_filename = os.path.basename(pdf_path)
            from qdrant_client.http import models as qmodels
            client.delete(
                collection_name=collection,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="source_file",
                                match=qmodels.MatchValue(value=source_filename),
                            )
                        ]
                    )
                ),
            )
            print(f"   🧹 已清除 '{source_filename}' 的旧记录")
        except Exception as exc:
            print(f"   ⚠️  清除旧记录失败（可能无旧数据）: {exc}")

    print(f"🔮 正在嵌入并写入 {len(new_chunks)} 个 chunk 到 Qdrant ...")
    t_write = time.time()

    await ensure_collection(collection)
    await insert_documents(new_chunks, collection_name=collection)

    write_time = time.time() - t_write
    print(f"   写入完成 ({write_time:.1f}s)")

    # ── 6. 更新缓存 ──────────────────────────────────
    new_hashes = {c["content_hash"] for c in new_chunks}
    save_cache(source_stem, new_hashes, pdf_path)
    print(f"   📝 缓存已更新 (+{len(new_hashes)} 条)")

    # ── 7. 输出统计 ──────────────────────────────────
    elapsed = time.time() - t_start
    print_statistics(
        total_pages=total_pages,
        valid_pages=valid_pages,
        skipped_pages=skipped_pages,
        ocr_pages=len(ocr_pages),
        chapters=chapters,
        total_chunks=total_chunks,
        new_chunks=len(new_chunks),
        duplicate_chunks=duplicate_count,
        elapsed=elapsed,
    )


# ─── CLI ───────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="将 PDF 解析、分块、嵌入并写入 Qdrant 向量库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  PYTHONPATH=. python scripts/ingest_pdf.py --pdf-path ../data/随机过程及应用.pdf\n"
            "  PYTHONPATH=. python scripts/ingest_pdf.py --pdf-path ../data/random.pdf --dry-run\n"
            "  PYTHONPATH=. python scripts/ingest_pdf.py --pdf-path ../data/random.pdf --force\n"
            "  PYTHONPATH=. python scripts/ingest_pdf.py --pdf-path ../data/random.pdf --collection my_coll\n"
        ),
    )
    parser.add_argument(
        "--pdf-path",
        type=str,
        required=True,
        help="PDF 文件路径",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=DEFAULT_COLLECTION,
        help=f"Qdrant collection 名称（默认: {DEFAULT_COLLECTION}）",
    )
    parser.add_argument(
        "--subject",
        type=str,
        default=DEFAULT_SUBJECT,
        help=f"课程/科目名（默认: {DEFAULT_SUBJECT}）",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"分块目标字符数（默认: {DEFAULT_CHUNK_SIZE}）",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=DEFAULT_OVERLAP,
        help=f"相邻块 overlap 字符数（默认: {DEFAULT_OVERLAP}）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-Run 模式：仅解析和分块，不写入 Qdrant",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新入库，忽略本地缓存并清除旧记录",
    )

    args = parser.parse_args()
    pdf_path = Path(args.pdf_path).resolve()

    asyncio.run(
        run_ingest(
            pdf_path=pdf_path,
            collection=args.collection,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
            subject=args.subject,
            dry_run=args.dry_run,
            force=args.force,
        )
    )


if __name__ == "__main__":
    main()
