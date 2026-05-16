"""
业务服务层 — Agent 编排服务
"""
from __future__ import annotations

from app.agents.graph import run_agent


async def process_chat_message(
    user_id: str,
    session_id: str,
    message: str,
) -> str:
    """
    处理对话消息，调用 Agent 生成回复

    Args:
        user_id: 用户 ID
        session_id: 会话 ID
        message: 用户消息

    Returns:
        Agent 回复
    """
    result = await run_agent(
        user_input=message,
        user_id=user_id,
        thread_id=session_id,
    )
    return result.get("agent_output", "抱歉，我暂时无法处理这个请求。")
