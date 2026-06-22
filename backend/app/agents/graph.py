"""
LangGraph Agent — Agent 图编排
"""

from __future__ import annotations
from typing import Optional

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState, AGENT_ROUTER, AGENT_PROFILING, AGENT_CONTENT_GEN, AGENT_QA, AGENT_PATH_PLANNING, AGENT_EVALUATION
from app.agents.nodes import (
    router_node,
    profiling_agent_node,
    content_gen_agent_node,
    qa_agent_node,
    path_planning_agent_node,
    evaluation_agent_node,
)


def should_continue(state: AgentState) -> str:
    """条件边 — 判断是否继续或结束"""
    if state.get("is_complete"):
        return "end"
    return "continue"


# ─── 构建图 ─────────────────────────────────────────

def build_agent_graph() -> StateGraph:
    """构建多智能体状态图"""
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node(AGENT_ROUTER, router_node)
    workflow.add_node(AGENT_PROFILING, profiling_agent_node)
    workflow.add_node(AGENT_CONTENT_GEN, content_gen_agent_node)
    workflow.add_node(AGENT_QA, qa_agent_node)
    workflow.add_node(AGENT_PATH_PLANNING, path_planning_agent_node)
    workflow.add_node(AGENT_EVALUATION, evaluation_agent_node)

    # 入口 → Router
    workflow.set_entry_point(AGENT_ROUTER)

    # Router → 各 Agent（条件路由）
    workflow.add_conditional_edges(
        AGENT_ROUTER,
        lambda state: state.get("next_agent", AGENT_QA),
        {
            AGENT_PROFILING: AGENT_PROFILING,
            AGENT_CONTENT_GEN: AGENT_CONTENT_GEN,
            AGENT_QA: AGENT_QA,
            AGENT_PATH_PLANNING: AGENT_PATH_PLANNING,
            AGENT_EVALUATION: AGENT_EVALUATION,
        },
    )

    # 各 Agent → Router（完成后返回路由）
    for agent in [AGENT_PROFILING, AGENT_CONTENT_GEN, AGENT_QA, AGENT_PATH_PLANNING, AGENT_EVALUATION]:
        workflow.add_conditional_edges(
            agent,
            should_continue,
            {
                "continue": AGENT_ROUTER,  # 未完成 → 返回 Router
                "end": END,                # 已完成 → 结束
            },
        )

    # 编译
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)

    return graph


# 全局单例
agent_graph = build_agent_graph()


async def run_agent(user_input: str, user_id: str, thread_id: Optional[str] = None) -> dict:
    """
    运行 Agent 并返回结果

    Args:
        user_input: 用户输入
        user_id: 用户 ID
        thread_id: 线程 ID（用于多轮对话上下文）

    Returns:
        Agent 输出
    """
    import uuid

    config = {
        "configurable": {
            "thread_id": thread_id or str(uuid.uuid4()),
            "user_id": user_id,
        }
    }

    initial_state: AgentState = {
        "messages": [],
        "user_id": user_id,
        "user_input": user_input,
        "profile": None,
        "profile_dimensions": [],
        "profile_dialogue_round": 0,
        "current_content": None,
        "content_type": None,
        "generated_resources": [],
        "conversation_context": [],
        "agent_output": None,
        "next_agent": None,
        "is_complete": False,
        "current_task": None,
        "errors": [],
        "assessment_data": None,
        "learning_progress": 0.0,
        "citations": [],
        "retrieval_used": False,
        "confidence": None,
    }

    result = await agent_graph.ainvoke(initial_state, config)
    return result
