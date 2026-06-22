"""
RAG — 检索器
"""
from __future__ import annotations

from typing import Any

from app.config import settings
from app.rag.embeddings import embed_batch
from app.rag.vector_store import get_qdrant_client


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
