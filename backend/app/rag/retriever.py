"""
RAG — 检索器
"""
from __future__ import annotations

import re
from typing import Any

from app.config import settings
from app.rag.embeddings import embed_batch
from app.rag.vector_store import get_qdrant_client

# ─── 查询扩展：口语化前缀 → 规范化查询 ─────────────────

# 口语化引导词，去除后得到核心主题
_QUERY_PREFIX_RE = re.compile(
    r"^(讲讲|介绍|解释|说一下|说说|谈谈|什么是|什么叫|请说明|请介绍|请解释|简述|概述)\s*"
)

# 核心主题后缀模板
_EXPANSION_SUFFIXES = ["是什么", "定义", "基本概念", ""]


def _expand_queries(user_input: str) -> list[str]:
    """
    将口语化查询扩展为多个规范化检索查询。

    "讲讲随机过程" → ["随机过程定义", "随机过程基本概念", "随机过程"]
    "介绍泊松过程" → ["泊松过程定义", "泊松过程基本概念", "泊松过程"]
    """
    # 提取核心主题：去除口语前缀
    core = _QUERY_PREFIX_RE.sub("", user_input).strip()
    if not core:
        return [user_input]

    # 若已经是规范形式（什么/定义开头），直接返回原查询
    if user_input.startswith(("什么是", "定义", "什么叫")):
        return [user_input]

    # 生成扩展查询，去重保持顺序
    seen = set()
    queries = []
    for suffix in _EXPANSION_SUFFIXES:
        q = (core + suffix).strip()
        if q and q not in seen:
            seen.add(q)
            queries.append(q)
    return queries


async def _multi_query_retrieve(
    queries: list[str],
    top_k: int = 5,
    score_threshold: float = 0.45,
) -> list[dict[str, Any]]:
    """
    对多个查询分别检索，合并去重后按 score 降序返回。
    已见 chunk_id 不再重复加入。
    """
    seen_ids: set[str] = set()
    merged: list[dict[str, Any]] = []

    for q in queries:
        results = await _search_qdrant(
            query=q,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        for r in results:
            cid = r.get("chunk_id", "")
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                merged.append(r)

    merged.sort(key=lambda x: x.get("score", 0), reverse=True)
    return merged[:top_k]


async def _search_qdrant(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.5,
    filters: dict | None = None,
) -> list[dict[str, Any]]:
    """
    直接通过 query_points API 检索 Qdrant（绕过已废弃的 client.search()）。

    Returns:
        list[dict]: 每项含 id, score, payload 字段
    """
    client = get_qdrant_client()
    collection = settings.QDRANT_COLLECTION
    query_vector = embed_batch([query])[0]

    response = client.query_points(
        collection_name=collection,
        query=query_vector,
        limit=top_k,
        score_threshold=score_threshold,
        with_payload=True,
    )

    points = response.points if hasattr(response, "points") else []
    return [
        {
            "id": p.id,
            "score": p.score,
            **p.payload,
        }
        for p in points
    ]


async def retrieve_context(
    query: str,
    top_k: int = 3,
    filters: dict | None = None,
) -> str:
    """
    检索 RAG 上下文文本

    将匹配的文档拼成上下文字符串，供 LLM 使用。

    Args:
        query: 用户问题
        top_k: 检索文档数
        filters: 过滤条件

    Returns:
        上下文文本
    """
    results = await _search_qdrant(
        query=query,
        top_k=top_k,
        score_threshold=0.5,
        filters=filters,
    )

    if not results:
        return ""

    context_parts = []
    for i, doc in enumerate(results, 1):
        title = doc.get("title", "未命名")
        content = doc.get("content", "")
        context_parts.append(f"[{i}] {title}\n{content}")

    return "\n\n---\n\n".join(context_parts)


def build_rag_prompt(query: str, context: str) -> list[dict]:
    """
    构建包含 RAG 上下文的 LLM Prompt

    Args:
        query: 用户问题
        context: 检索到的上下文文本

    Returns:
        消息列表
    """
    system_prompt = (
        "你是 AI 教育助手，负责根据提供的参考资料回答用户的问题。\n\n"
        "规则：\n"
        "1. 如果参考资料中有相关信息，请优先基于资料回答，并引用来源\n"
        "2. 如果资料中没有相关信息，请用自己的知识回答，但明确说明这不是来自参考资料\n"
        "3. 回答要详细、有条理，适合学习场景\n"
        "4. 鼓励用户追问和深入探讨"
    )

    messages = [{"role": "system", "content": system_prompt}]

    if context:
        messages.append({
            "role": "system",
            "content": f"以下是相关的参考资料：\n\n{context}",
        })

    messages.append({"role": "user", "content": query})

    return messages


async def retrieve_with_metadata(
    query: str,
    top_k: int = 5,
    filters: dict | None = None,
    score_threshold: float = 0.5,
) -> tuple[str, list[dict]]:
    """
    检索 RAG 上下文，同时返回结构化结果用于构建 citations。

    Args:
        query: 用户问题
        top_k: 检索文档数
        filters: 过滤条件
        score_threshold: 相似度阈值

    Returns:
        (context_string, results_list)
        - context_string: 拼接的上下文文本（供 LLM prompt 使用）
        - results_list: 原始检索结果列表，每项含 score, page_number, chapter 等
    """
    results = await _search_qdrant(
        query=query,
        top_k=top_k,
        score_threshold=score_threshold,
        filters=filters,
    )

    if not results:
        return "", []

    context_parts = []
    for i, doc in enumerate(results, 1):
        title = doc.get("title", "未命名")
        content = doc.get("content", "")
        page = doc.get("page_number", "?")
        chapter = doc.get("chapter", "")
        source = f"[来源: {chapter} 第{page}页]" if chapter else f"[来源: 第{page}页]"
        context_parts.append(f"[{i}] {title} {source}\n{content}")

    context = "\n\n---\n\n".join(context_parts)
    return context, results


async def retrieve_robust(
    user_input: str,
    top_k: int = 5,
    score_threshold: float = 0.45,
) -> tuple[str, list[dict]]:
    """
    鲁棒检索 — 先尝试原始查询，无结果时自动扩展查询词。

    Args:
        user_input: 用户原始输入
        top_k: 返回文档数
        score_threshold: 相似度阈值（比 retrieve_with_metadata 略低以增加召回）

    Returns:
        (context_string, results_list)
    """
    # 1. 先尝试原始查询
    results = await _search_qdrant(
        query=user_input,
        top_k=top_k,
        score_threshold=score_threshold,
    )

    # 2. 若无结果，尝试扩展查询
    if not results:
        expanded = _expand_queries(user_input)
        if len(expanded) > 1:
            results = await _multi_query_retrieve(
                queries=expanded,
                top_k=top_k,
                score_threshold=score_threshold,
            )

    if not results:
        return "", []

    context_parts = []
    for i, doc in enumerate(results, 1):
        title = doc.get("title", "未命名")
        content = doc.get("content", "")
        page = doc.get("page_number", "?")
        chapter = doc.get("chapter", "")
        source = f"[来源: {chapter} 第{page}页]" if chapter else f"[来源: 第{page}页]"
        context_parts.append(f"[{i}] {title} {source}\n{content}")

    context = "\n\n---\n\n".join(context_parts)
    return context, results
