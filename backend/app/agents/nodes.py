"""
LangGraph Agent — 节点函数
"""
from __future__ import annotations

from typing import Any

from app.agents.state import AgentState


def router_node(state: AgentState) -> dict:
    """
    路由节点 — 根据用户输入和当前状态决定下一个 Agent
    """
    user_input = state.get("user_input", "").lower()
    profile = state.get("profile")

    # 判断意图
    if not profile:
        next_agent = "profiling_agent"
    elif any(kw in user_input for kw in ["讲解", "学习", "内容", "知识", "课程", "教"]):
        next_agent = "content_gen_agent"
    elif any(kw in user_input for kw in ["路径", "规划", "路线", "顺序", "先学"]):
        next_agent = "path_planning_agent"
    elif any(kw in user_input for kw in ["题", "评估", "测试", "考", "分"]):
        next_agent = "evaluation_agent"
    else:
        next_agent = "qa_agent"

    return {"next_agent": next_agent, "current_task": f"route to {next_agent}"}


def profiling_agent_node(state: AgentState) -> dict:
    """
    画像 Agent — 通过对话收集用户特征，构建画像
    """
    user_input = state.get("user_input", "")

    # TODO: 调用 LLM 分析用户输入，提取特征
    # 占位实现
    dimensions = [
        {"name": "knowledge", "value": 60, "label": "知识水平", "description": "基础知识掌握程度"},
        {"name": "cognitive", "value": 70, "label": "认知风格", "description": "偏向视觉型学习"},
        {"name": "weakness", "value": 50, "label": "易错点", "description": "需要重点加强的薄弱环节"},
        {"name": "preference", "value": 75, "label": "偏好形式", "description": "偏好互动式学习"},
        {"name": "speed", "value": 65, "label": "学习速度", "description": "中等偏快"},
        {"name": "depth", "value": 55, "label": "理解深度", "description": "需加强应用"},
    ]

    agent_output = (
        f"我已根据你的输入「{user_input}」初步分析了你的学习特征。\n\n"
        f"你的知识基础较为扎实，偏向视觉型学习风格，"
        f"适合通过例题讲解 + 思维导图的方式学习新知识。"
    )

    return {
        "profile_dimensions": dimensions,
        "agent_output": agent_output,
        "next_agent": None,
        "is_complete": True,
    }


def content_gen_agent_node(state: AgentState) -> dict:
    """
    内容生成 Agent — 根据画像动态生成学习内容
    """
    user_input = state.get("user_input", "")

    # TODO: 调用 LLM + RAG 生成个性化内容
    agent_output = (
        f"好的，我来为你生成关于「{user_input}」的学习内容。\n\n"
        f"## 核心概念\n\n"
        f"这是根据你的学习风格和当前水平量身定制的讲解。\n\n"
        f"### 要点\n\n"
        f"1. 概念理解\n"
        f"2. 关键原理\n"
        f"3. 实际应用\n\n"
        f"需要我更详细地展开某个部分吗？还是想看看思维导图版本的总结？"
    )

    return {
        "current_content": {
            "title": user_input,
            "type": "explanation",
            "content": agent_output,
        },
        "agent_output": agent_output,
        "next_agent": None,
        "is_complete": False,
    }


def qa_agent_node(state: AgentState) -> dict:
    """
    答疑 Agent — 结合 RAG 进行多轮问答
    """
    user_input = state.get("user_input", "")

    # TODO: 调用 LLM + RAG 检索相关知识点
    # 占位实现
    agent_output = (
        f"这是一个很好的问题！关于「{user_input}」，我可以从以下几个方面为你解答：\n\n"
        f"1. **基本概念**：...\n"
        f"2. **核心原理**：...\n"
        f"3. **实践技巧**：...\n\n"
        f"需要我深入讲解某个具体方面吗？或者看看相关的练习题？"
    )

    return {
        "agent_output": agent_output,
        "next_agent": None,
        "is_complete": False,
    }


def path_planning_agent_node(state: AgentState) -> dict:
    """
    路径规划 Agent — 规划最优学习路径
    """
    user_input = state.get("user_input", "")

    agent_output = (
        f"根据你的学习目标和当前水平，我为你规划了以下学习路径：\n\n"
        f"### 📍 学习路线\n\n"
        f"**阶段一：基础知识**\n"
        f"- 目标：掌握核心概念\n"
        f"- 预计时间：2-3 小时\n\n"
        f"**阶段二：理解深化**\n"
        f"- 目标：理解原理与应用场景\n"
        f"- 预计时间：3-4 小时\n\n"
        f"**阶段三：实践应用**\n"
        f"- 目标：通过练习巩固知识\n"
        f"- 预计时间：4-5 小时\n\n"
        f"我会根据你的学习进度动态调整这个计划。"
    )

    return {
        "agent_output": agent_output,
        "next_agent": None,
        "is_complete": False,
    }


def evaluation_agent_node(state: AgentState) -> dict:
    """
    评估 Agent — 出题评估并反馈
    """
    user_input = state.get("user_input", "")

    agent_output = (
        f"好的，让我来评估一下你对「{user_input}」的掌握程度：\n\n"
        f"### 📝 自测题\n\n"
        f"**Q1:** 请简要描述核心概念是什么？\n\n"
        f"**Q2:** 以下哪个选项最能说明其应用场景？\n"
        f"A. ...\nB. ...\nC. ...\nD. ...\n\n"
        f"**Q3:** 请举一个实际应用的例子。\n\n"
        f"请告诉我你的答案，我来给你评分和反馈！"
    )

    return {
        "agent_output": agent_output,
        "next_agent": None,
        "is_complete": False,
    }
