"""
Agent 核心 — 状态定义
"""
from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """多智能体系统全局状态"""

    # 当前消息
    messages: Annotated[list[dict], add_messages]

    # 用户信息
    user_id: str
    user_input: str

    # 画像状态
    profile: dict[str, Any] | None
    profile_dimensions: list[dict[str, Any]]

    # 对话上下文
    history: list[dict[str, str]]

    # 输出
    agent_output: str | None
    next_agent: str | None
    is_complete: bool

    # 任务追踪
    current_task: str | None
    errors: list[str]
