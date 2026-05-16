"""
Agent 核心 — 图编排
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState


def router_node(state: AgentState) -> dict:
    """路由节点"""
    user_input = state.get("user_input", "").lower()
    profile = state.get("profile")

    if not profile:
        return {"next_agent": "profiling", "current_task": "构建学习者画像"}
    elif any(kw in user_input for kw in ["讲解", "学习", "内容", "知识", "课程"]):
        return {"next_agent": "content_gen", "current_task": "生成学习内容"}
    elif any(kw in user_input for kw in ["路径", "规划", "路线", "顺序"]):
        return {"next_agent": "path_planning", "current_task": "规划学习路径"}
    elif any(kw in user_input for kw in ["题", "评估", "测试", "考", "分"]):
        return {"next_agent": "evaluation", "current_task": "评估学习效果"}
    else:
        return {"next_agent": "qa", "current_task": "答疑解惑"}


def profiling_node(state: AgentState) -> dict:
    return {
        "profile_dimensions": [
            {"name": "knowledge", "value": 60, "label": "知识水平"},
            {"name": "cognitive", "value": 70, "label": "认知风格"},
            {"name": "weakness", "value": 50, "label": "易错点"},
            {"name": "preference", "value": 75, "label": "偏好形式"},
            {"name": "speed", "value": 65, "label": "学习速度"},
            {"name": "depth", "value": 55, "label": "理解深度"},
        ],
        "agent_output": "我已分析了你的学习特征，为你构建了初步画像。",
        "is_complete": True,
    }


def content_gen_node(state: AgentState) -> dict:
    return {
        "agent_output": f"为你生成关于「{state['user_input']}」的学习内容（待 LLM 实现）",
        "is_complete": True,
    }


def qa_node(state: AgentState) -> dict:
    return {
        "agent_output": f"关于「{state['user_input']}」的解答（待 LLM + RAG 实现）",
        "is_complete": True,
    }


def path_planning_node(state: AgentState) -> dict:
    return {
        "agent_output": "已为你规划学习路径（待 LLM 实现）",
        "is_complete": True,
    }


def evaluation_node(state: AgentState) -> dict:
    return {
        "agent_output": "已生成评估题目（待 LLM 实现）",
        "is_complete": True,
    }


def should_continue(state: AgentState) -> str:
    return "end" if state.get("is_complete") else "continue"


def build_graph() -> StateGraph:
    """构建 Agent 图"""
    workflow = StateGraph(AgentState)

    workflow.add_node("router", router_node)
    workflow.add_node("profiling", profiling_node)
    workflow.add_node("content_gen", content_gen_node)
    workflow.add_node("qa", qa_node)
    workflow.add_node("path_planning", path_planning_node)
    workflow.add_node("evaluation", evaluation_node)

    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        lambda s: s.get("next_agent", "qa"),
        {
            "profiling": "profiling",
            "content_gen": "content_gen",
            "qa": "qa",
            "path_planning": "path_planning",
            "evaluation": "evaluation",
        },
    )

    for node in ["profiling", "content_gen", "qa", "path_planning", "evaluation"]:
        workflow.add_conditional_edges(
            node,
            should_continue,
            {"continue": "router", "end": END},
        )

    return workflow.compile(checkpointer=MemorySaver())


graph = build_graph()


async def run(user_input: str, user_id: str, thread_id: str | None = None) -> dict:
    """运行 Agent"""
    import uuid
    config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4()), "user_id": user_id}}
    state = AgentState(
        messages=[],
        user_id=user_id,
        user_input=user_input,
        profile=None,
        profile_dimensions=[],
        history=[],
        agent_output=None,
        next_agent=None,
        is_complete=False,
        current_task=None,
        errors=[],
    )
    return await graph.ainvoke(state, config)
