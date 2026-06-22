"""
PDF 处理器 — 解析 PDF 文件并提取页级文本

Python 3.9 兼容，使用 pdfplumber 解析。
对扫描件 PDF 自动降级为 OCR（pytesseract + chi_sim）。
"""
from __future__ import annotations

import re
import warnings
from typing import Any, Callable, Dict, List, Optional

import pdfplumber
from pdfplumber.page import Page

# pytesseract 按需导入（仅当 OCR fallback 时）
_ocr_available = False
try:
    import pytesseract
    _ocr_available = True
except ImportError:
    pass

# ─── 章节/节标题识别正则 ─────────────────────────────────

# "第X章" 或 "第N章"
CHAPTER_RE = re.compile(r"^第[一二三四五六七八九十百千\d]+章\s*(.*)$")
# 节标题：如 "1.1"、"2.3.1"
SECTION_RE = re.compile(r"^(\d+\.\d+(?:\.\d+)?)\s+(.*)$")
# 中文序号章节：如 "一、"、"（一）"
CN_CHAPTER_RE = re.compile(r"^[（\(]?[一二三四五六七八九十]+[）\)、.．]\s*(.*)$")

# ─── 页眉页脚正则 ──────────────────────────────────────

HEADER_FOOTER_PATTERNS = [
    re.compile(r"^\d+$"),                       # 纯数字页码
    re.compile(r"^第\d+页$"),                    # "第1页"
    re.compile(r"^随机过程与排队论\s*$"),          # 书名
    re.compile(r"^随机过程及应用\s*$"),              # 书名
    re.compile(r"^\d+/\d+$"),                     # "5/223"
    re.compile(r"^第\d+章\s*$"),                  # "第1章" 孤行
    re.compile(r"^\d+\s*$"),                      # 孤行页码
    re.compile(r"^-\s*\d+\s*-$"),                 # "- 5 -"
]

# ─── 公告页/目录页关键词 ──────────────────────────────

FRONT_MATTER_KEYWORDS = [
    "前言", "序言", "引言", "目录", "内容简介", "出版说明",
    "编辑说明", "编委会", "主编", "作者简介",
]

# OCR DPI — 200 足够中文印刷体识别，速度比 300 DPI 快 2x 以上
OCR_DPI = 200


def extract_pdf(
    filepath: str,
    ocr_fallback: bool = True,
    progress_callback: Optional[Callable[[int, int, int, bool], None]] = None,
) -> List[Dict[str, Any]]:
    """
    解析 PDF，按页提取文本。

    首先尝试 pdfplumber 内置的 extract_text()；
    如果页文本为空或极短（< 20 字符），且 ocr_fallback=True，
    自动降级为 Tesseract OCR（chi_sim 中文模型）。

    Args:
        filepath: PDF 文件路径
        ocr_fallback: 是否允许 OCR 降级
        progress_callback: 进度回调 fn(当前页码, 总页数, 字符数, 是否使用了OCR)

    Returns:
        list[dict]: 每页信息，包含:
            - page_num (int): 页码（从 1 开始）
            - text (str): 清洗后的文本
            - has_text (bool): 是否包含有效文本
            - total_pages (int): PDF 总页数
            - raw_length (int): 原始文本长度
            - ocr_used (bool): 是否使用了 OCR
    """
    pages: List[Dict[str, Any]] = []
    with pdfplumber.open(filepath) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages, 1):
            # 1. 尝试内置文本提取
            page_text = page.extract_text(x_tolerance=3, y_tolerance=3)
            raw_text = page_text or ""
            ocr_used = False

            # 2. 如果文本太少，尝试 OCR 降级
            if (len(raw_text.strip()) < 20) and ocr_fallback:
                ocr_text = _ocr_page(page)
                if ocr_text and len(ocr_text.strip()) > len(raw_text.strip()):
                    raw_text = ocr_text
                    ocr_used = True

            cleaned = clean_page_text(raw_text)
            has_text = len(cleaned.strip()) >= 5

            page_info = {
                "page_num": i,
                "text": cleaned,
                "has_text": has_text,
                "total_pages": total,
                "raw_length": len(raw_text),
                "ocr_used": ocr_used,
            }
            pages.append(page_info)

            if progress_callback:
                progress_callback(i, total, len(cleaned), ocr_used)

    return pages


def _ocr_page(page: Page) -> str:
    """
    对单页 PDF 执行 OCR 提取文本。

    返回空字符串表示 OCR 失败。
    """
    if not _ocr_available:
        return ""

    try:
        im = page.to_image(resolution=OCR_DPI)
        text = pytesseract.image_to_string(
            im.original,
            lang="chi_sim+eng",  # 中文 + 英文（公式符号）
            config="--psm 6",    # 假定为统一文本块
        )
        return text or ""
    except Exception as exc:
        warnings.warn(f"OCR failed on page {page.page_number}: {exc}")
        return ""


def clean_page_text(text: str) -> str:
    """清洗单页文本 — 移除页眉页脚、零宽字符、压缩空行"""
    if not text:
        return ""

    # 1. 移除零宽字符和特殊空白
    text = re.sub(r"[​﻿\xa0 - ]", "", text)
    # 2. 统一换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.split("\n")
    cleaned_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue

        # 检查是否是页眉页脚
        is_header_footer = any(p.fullmatch(stripped) for p in HEADER_FOOTER_PATTERNS)
        if is_header_footer:
            continue

        cleaned_lines.append(stripped)

    # 3. 合并断行
    merged: List[str] = []
    sentence_end_chars = set("。；！？：.?!;:）」』】》\"'")
    for line in cleaned_lines:
        if not line:
            merged.append(line)
            continue

        if merged and merged[-1] and not merged[-1][-1] in sentence_end_chars:
            if line and line[0].isprintable():
                merged[-1] = merged[-1] + line
                continue

        merged.append(line)

    # 4. 连续空行压缩（3+ → 2）
    result = "\n".join(merged)
    result = re.sub(r"\n{4,}", "\n\n", result)
    # 5. 压缩行首行尾空白
    result = re.sub(r" +\n", "\n", result)
    result = re.sub(r"\n +", "\n", result)

    return result.strip()


def detect_chapters(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    识别每页所属的章节。

    遍历所有页，通过行级正则匹配识别章节标题，
    并回填每页的 chapter 字段。

    Args:
        pages: extract_pdf 的输出

    Returns:
        新增 chapter/章节名 字段后的 pages
    """
    current_chapter: Optional[str] = None

    for page in pages:
        text = page.get("text", "")
        lines = text.split("\n")

        chapter_found: Optional[str] = None
        for line in lines:
            stripped = line.strip()

            # 匹配 "第X章 ..."
            m = CHAPTER_RE.match(stripped)
            if m:
                chapter_found = stripped
                break

            # 匹配中文序号章节（仅当还没识别到任何章节时）
            if current_chapter is None:
                m = CN_CHAPTER_RE.match(stripped)
                if m and m.group(1).strip() and len(m.group(1).strip()) <= 30:
                    chapter_found = stripped
                    break

        if chapter_found:
            current_chapter = chapter_found
            page["chapter"] = current_chapter
        else:
            page["chapter"] = current_chapter or ""

    return pages


def get_chapter_title(text: str) -> Optional[str]:
    """从文本中提取第一个匹配的章节标题"""
    lines = text.split("\n")
    for line in lines:
        stripped = line.strip()
        m = CHAPTER_RE.match(stripped)
        if m:
            return stripped
    return None


def get_first_section(text: str) -> Optional[str]:
    """获取文本中出现的第一个节标题"""
    lines = text.split("\n")
    for line in lines:
        stripped = line.strip()
        m = SECTION_RE.match(stripped)
        if m:
            return m.group(2).strip()
    return None


# ─── 分块 & Hash ─────────────────────────────────────────


def compute_content_hash(text: str) -> str:
    """计算文本的 SHA256 哈希（用于去重）"""
    return __import__("hashlib").sha256(text.encode("utf-8")).hexdigest()


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 100,
) -> list[str]:
    """
    将长文本按近似 chunk_size 中文字符切分，overlap 字符重叠。

    尽量在句子边界（。！？；\\n）处断开，避免截断语义。

    Args:
        text: 输入文本
        chunk_size: 每块目标字符数（约 800 中文字符）
        overlap: 与上一块的字符重叠数（约 100 中文字符）

    Returns:
        文本块列表
    """
    if not text or not text.strip():
        return []

    # 按句子边界拆分（同时保留分隔符在各自句子末尾）
    sentence_endings = re.compile(r"(?<=[。！？；.!?;])(?=\s*[^\s])")
    raw_sentences = sentence_endings.split(text)

    # 对过长的句子（如公式密集区域）按换行再切一次
    sentences: list[str] = []
    for seg in raw_sentences:
        if len(seg) > chunk_size * 1.5:
            # 按换行拆开
            sub_segments = [s.strip() for s in seg.split("\n") if s.strip()]
            sentences.extend(sub_segments)
        elif seg.strip():
            sentences.append(seg.strip())

    if not sentences:
        return [text.strip()]

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_len = 0

    for sent in sentences:
        sent_len = len(sent)

        if current_len + sent_len > chunk_size and current_chunk:
            # 当前 chunk 已满，保存并开始新 chunk
            chunk_text_val = "".join(current_chunk)
            chunks.append(chunk_text_val)

            # overlap: 从已保存的 chunk 尾部取约 overlap 字符作为新 chunk 起点
            overlap_text = chunk_text_val[-overlap:] if len(chunk_text_val) > overlap else chunk_text_val
            current_chunk = [overlap_text]
            current_len = len(overlap_text)

        current_chunk.append(sent)
        current_len += sent_len

    # 最后一个 chunk
    if current_chunk:
        last = "".join(current_chunk).strip()
        if last:
            chunks.append(last)

    return chunks


def build_chunks(
    pages: list[dict[str, Any]],
    source_file: str,
    subject: str = "随机过程及应用",
    chunk_size: int = 800,
    overlap: int = 100,
    content_type: str = "textbook",
) -> list[dict[str, Any]]:
    """
    将按页解析的结果转化为带完整元数据的文本块列表。

    Args:
        pages: extract_pdf + detect_chapters 的输出
        source_file: PDF 文件名
        subject: 课程/科目名
        chunk_size: 每块目标字符数
        overlap: 重叠字符数
        content_type: 内容类型标签

    Returns:
        list[dict]: 每个 dict 包含:
            title, content, type, subject, source_file,
            page_number, chapter, chunk_id, content_hash, metadata
    """
    import hashlib
    import os

    chunks: list[dict[str, Any]] = []
    filename = os.path.basename(source_file)
    # 用于 chunk_id 的简短主题 slug
    subject_slug = re.sub(r"[^a-zA-Z0-9一-鿿]+", "_", subject).strip("_") or "doc"

    for page in pages:
        page_num = page.get("page_num", 0)
        chapter = page.get("chapter", "") or ""
        text = page.get("text", "") or ""

        if not text.strip():
            continue

        page_chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

        # 尝试从页面文本中提取更精确的标题
        page_title = get_chapter_title(text) or get_first_section(text) or chapter or f"第{page_num}页"

        for seq, chunk_content in enumerate(page_chunks, 1):
            content_hash = compute_content_hash(chunk_content)
            # chunk_id = 8-char hash + page + seq
            short_hash = content_hash[:8]
            chunk_id = f"{subject_slug}_p{page_num:04d}_s{seq:03d}_{short_hash}"

            chunks.append({
                "title": page_title,
                "content": chunk_content,
                "type": content_type,
                "subject": subject,
                "source_file": filename,
                "page_number": page_num,
                "chapter": chapter,
                "chunk_id": chunk_id,
                "content_hash": content_hash,
                "metadata": {
                    "page_num": page_num,
                    "chunk_seq": seq,
                    "total_chunks_on_page": len(page_chunks),
                    "ocr_used": page.get("ocr_used", False),
                },
            })

    return chunks
