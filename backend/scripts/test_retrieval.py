"""
临时检索验证脚本 — 测试 Qdrant RAG 语义检索效果

用法:
    cd backend
    PYTHONPATH=. python scripts/test_retrieval.py

只读 Qdrant，不写入、不删除、不调用 LLM。
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent  # backend/
sys.path.insert(0, str(_PROJECT_ROOT))

from app.config import settings
from app.rag.embeddings import embed_batch
from app.rag.vector_store import get_qdrant_client

TEST_QUESTIONS = [
    "什么是随机过程？",
    "泊松过程的定义是什么？",
    "马尔可夫链具有什么性质？",
    "平稳过程的定义是什么？",
    "时间序列分析研究什么？",
]

TOP_K = 3
CONTENT_PREVIEW_LEN = 160


async def main():
    print("=" * 64)
    print("  Qdrant RAG 检索验证")
    print("=" * 64)
    print(f"  Collection: {settings.QDRANT_COLLECTION}")
    print(f"  测试问题数: {len(TEST_QUESTIONS)}")
    print(f"  每问题 top: {TOP_K}")
    print()

    client = get_qdrant_client()
    collection = settings.QDRANT_COLLECTION

    for qi, question in enumerate(TEST_QUESTIONS, 1):
        print(f"─── [{qi}/{len(TEST_QUESTIONS)}] {question} ───")
        print()

        try:
            # 生成查询向量
            query_vector = embed_batch([question])[0]

            # 使用 query_points（qdrant-client 1.16.x API）
            response = client.query_points(
                collection_name=collection,
                query=query_vector,
                limit=TOP_K,
                score_threshold=0.5,
                with_payload=True,
            )
        except Exception as exc:
            print(f"  ❌ 检索异常: {exc}")
            print()
            continue

        # response.points 是 list[ScoredPoint]
        points = response.points if hasattr(response, "points") else []

        if not points:
            print(f"  ⚠️ 无匹配结果（collection 可能为空或 score < 0.5）")
            print()
            continue

        for ri, point in enumerate(points, 1):
            score = point.score
            payload = point.payload or {}

            page = payload.get("page_number", "缺失")
            chapter = payload.get("chapter", "缺失")
            source = payload.get("source_file", "缺失")
            content = payload.get("content", "")

            score_str = f"{score:.4f}" if isinstance(score, float) else str(score)

            content_preview = content[:CONTENT_PREVIEW_LEN] if content else "缺失"
            if len(content) > CONTENT_PREVIEW_LEN:
                content_preview += "…"

            # 将换行统一为空格以便单行展示
            content_preview = content_preview.replace("\n", " ")

            print(f"  [{ri}] score={score_str}  page={page}  chapter={chapter}")
            print(f"      source_file={source}")
            print(f"      content: {content_preview}")
            print()

    print("=" * 64)
    print("  检索验证完成")
    print("=" * 64)


if __name__ == "__main__":
    asyncio.run(main())
