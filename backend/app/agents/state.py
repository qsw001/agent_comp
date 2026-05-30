"""
LangGraph Agent — 状态定义（增强版）
"""

from __future__ import annotations
from typing import Optional, Any, Literal
from typing import Annotated, TypedDict

from langgraph.graph import add_messages


class AgentState(TypedDict):
    """多智能体系统全局状态"""

    # 当前消息
    messages: Annotated[list[dict], add_messages]

    # 用户信息
    user_id: str
    user_input: str

    # ── 画像状态 ──
    profile: Optional[dict[str, Any]]
    profile_dimensions: list[dict[str, Any]]
    profile_dialogue_round: int  # 对话轮次，渐进式构建

    # ── 学习内容 ──
    current_content: Optional[dict[str, Any]]
    content_type: Optional[Literal["document", "mindmap", "quiz", "reading", "video", "code", "slides"]]
    generated_resources: list[dict[str, Any]]  # 生成的资源列表

    # ── 对话上下文 ──
    conversation_context: list[dict[str, str]]
    agent_output: Optional[str]

    # ── 路由 ──
    next_agent: Optional[str]
    is_complete: bool

    # ── 任务追踪 ──
    current_task: Optional[str]
    errors: list[str]

    # ── 评估 ──
    assessment_data: Optional[dict[str, Any]]
    learning_progress: float  # 0.0-1.0


AGENT_ROUTER = "router"
AGENT_PROFILING = "profiling_agent"
AGENT_CONTENT_GEN = "content_gen_agent"
AGENT_QA = "qa_agent"
AGENT_PATH_PLANNING = "path_planning_agent"
AGENT_EVALUATION = "evaluation_agent"
