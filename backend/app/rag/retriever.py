"""
RAG — 检索器
"""
from __future__ import annotations

from app.rag.vector_store import search_similar


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
    results = await search_similar(
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
