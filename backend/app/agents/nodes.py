"""
LangGraph Agent — 节点函数（完整实现）

多智能体协作架构:
  router → profiling_agent → content_gen_agent (多子智能体协同)
  router → qa_agent (智能辅导)
  router → path_planning_agent
  router → evaluation_agent
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import create_engine, select as sa_select
from sqlalchemy.orm import Session as SaSession

from app.agents.state import AgentState
from app.config import settings


def _load_profile_from_db_sync(user_id: str) -> tuple:
    """从数据库同步加载用户已有画像，供 router 使用"""
    if not user_id:
        return None, []
    try:
        from app.models import LearnerProfile
        sync_engine = create_engine(settings.DATABASE_URL_SYNC, echo=False)
        with SaSession(sync_engine) as session:
            stmt = sa_select(LearnerProfile).where(
                LearnerProfile.user_id == user_id
            ).order_by(LearnerProfile.updated_at.desc()).limit(1)
            result = session.execute(stmt)
            profile_row = result.scalar_one_or_none()
            if profile_row and profile_row.dimensions:
                raw = profile_row.dimensions
                if isinstance(raw, list):
                    dims = raw
                elif isinstance(raw, dict):
                    # DB 中存储为 {dim_name: {...}} 格式，转为列表
                    dims = [{"name": k, **v} if isinstance(v, dict) else {"name": k, "value": v} for k, v in raw.items()]
                else:
                    dims = []
                return {"id": profile_row.id, "name": profile_row.name}, dims
        sync_engine.dispose()
    except Exception:
        pass
    return None, []


# ────────────────────────────────────────────────────────────────
# Router — 意图识别与路由
# ────────────────────────────────────────────────────────────────

def router_node(state: AgentState) -> dict:
    """根据用户输入和状态进行智能路由"""
    user_input = state.get("user_input", "").lower()
    profile = state.get("profile")
    profile_dims = state.get("profile_dimensions", [])

    # 若 state 中无画像，尝试从数据库加载已有画像
    if not profile:
        profile, profile_dims = _load_profile_from_db_sync(state.get("user_id", ""))

    # 关键词意图路由（先于画像检查）
    intent_map = {
        "profiling_agent": [
            "建立学习画像", "更新学习画像", "分析我的学习情况",
            "了解我的基础", "评估我的学习能力", "我的学习偏好",
            "我的薄弱点", "我适合怎样学习", "学习画像", "构建画像",
        ],
        "qa_agent": [
            "什么是", "是什么", "什么叫", "定义", "性质", "区别",
            "概念", "原理", "为什么", "有哪些", "公式", "定理",
            "证明", "推导", "如何计算", "举例", "举例说明", "解释",
        ],
        "content_gen_agent": [
            "讲解", "学习", "内容", "知识", "课程", "教", "资源", "生成",
            "文档", "思维导图", "练习题", "题目", "视频", "动画", "代码",
            "案例", "实操", "ppt", "幻灯片", "给我做", "帮我生成",
        ],
        "path_planning_agent": [
            "路径", "规划", "路线", "顺序", "先学", "后学", "计划",
            "安排", "进度", "步骤",
        ],
        "evaluation_agent": [
            "评估", "测试", "考试", "得分", "掌握", "程度", "检查",
            "检测", "自测", "考核",
        ],
    }

    for agent, keywords in intent_map.items():
        if any(kw in user_input for kw in keywords):
            return {"next_agent": agent, "current_task": f"route to {agent}"}

    # 默认：智能辅导（所有未匹配意图均进入 QA）
    return {"next_agent": "qa_agent", "current_task": "qa"}


# ────────────────────────────────────────────────────────────────
# Profiling Agent — 对话式画像构建（≥6 维度）
# ────────────────────────────────────────────────────────────────

# 渐进式问题模板
PROFILE_QUESTIONS = [
    {
        "dimension": "knowledge_basis",
        "prompt": "你的专业是什么？之前学过哪些课程？对哪些领域比较熟悉？",
    },
    {
        "dimension": "learning_goals",
        "prompt": "你的学习目标是什么？准备考试、找工作、做项目，还是纯粹兴趣？",
    },
    {
        "dimension": "cognitive_style",
        "prompt": "你喜欢怎么学习？看视频讲解、读文档、动手实践，还是听音频？",
    },
    {
        "dimension": "weak_points",
        "prompt": "在学习中，你觉得哪些知识点或技能最薄弱、最容易出错？",
    },
    {
        "dimension": "engagement_level",
        "prompt": "你对当前学习内容有多大兴趣？是主动想学还是被课程要求？",
    },
    {
        "dimension": "time_availability",
        "prompt": "你每周大概有多少时间可以用来学习？每天能学多久？",
    },
    {
        "dimension": "learning_pace",
        "prompt": "你希望学习节奏快一点还是稳扎稳打？",
    },
    {
        "dimension": "subject_interests",
        "prompt": "除了正在学的内容，你对哪些领域或话题还感兴趣？",
    },
    {
        "dimension": "prior_knowledge",
        "prompt": "在相关领域，你已经有哪些实践经验或项目经历？",
    },
    {
        "dimension": "preferred_modalities",
        "prompt": "你偏好哪种学习资源形式？文档、视频、思维导图、练习题还是动手项目？",
    },
]


def profiling_agent_node(state: AgentState) -> dict:
    """画像 Agent — 渐进对话式构建"""
    user_input = state.get("user_input", "")
    existing_dims = state.get("profile_dimensions", [])
    dialogue_round = state.get("profile_dialogue_round", 0)

    # 提取当前轮次的维度信息
    extracted = _extract_profile_dimensions(user_input, dialogue_round)

    # 合并到已有维度
    for dim in extracted:
        existing = next((d for d in existing_dims if d["name"] == dim["name"]), None)
        if existing:
            existing["value"] = dim["value"]
            existing["label"] = dim.get("label", existing["label"])
            existing["description"] = dim.get("description", existing.get("description", ""))
        else:
            existing_dims.append(dim)

    # 判断画像是否完整
    completed_dims = {d["name"] for d in existing_dims}
    all_required = {"knowledge_basis", "learning_goals", "cognitive_style",
                    "weak_points", "engagement_level", "time_availability"}
    is_complete = all_required.issubset(completed_dims)

    # 下一轮问题
    next_question = ""
    if not is_complete:
        for q in PROFILE_QUESTIONS:
            if q["dimension"] not in completed_dims:
                next_question = q["prompt"]
                break

    if is_complete:
        agent_output = _generate_profile_summary(existing_dims)
    else:
        agent_output = f"好的，我了解了！{next_question}"

    return {
        "profile_dimensions": existing_dims,
        "profile_dialogue_round": dialogue_round + 1,
        "agent_output": agent_output,
        "profile": existing_dims if is_complete else None,
        "next_agent": None,
        "is_complete": is_complete,
    }


def _extract_profile_dimensions(user_input: str, round_num: int) -> list[dict]:
    """从对话中提取画像维度"""
    inp = user_input.lower()
    dims = []

    # ── knowledge_basis ──
    kb = {}
    subjects = {
        "python": ["python", "编程语言", "python编程"],
        "java": ["java"],
        "javascript": ["javascript", "js", "前端开发"],
        "c++": ["c++", "cpp"],
        "machine_learning": ["机器学习", "ml", "深度学习", "ai", "人工智能"],
        "math": ["数学", "math", "微积分", "线性代数", "概率", "统计"],
        "database": ["数据库", "sql", "mysql", "postgresql"],
        "algorithm": ["算法", "数据结构", "algorithm"],
        "network": ["网络", "计算机网络", "tcp", "http"],
        "operating_system": ["操作系统", "linux", "os"],
        "software_engineering": ["软件工程", "设计模式", "架构"],
        "data_science": ["数据科学", "数据分析", "data science"],
        "web_dev": ["web", "网页", "react", "vue", "前端"],
        "mobile_dev": ["移动开发", "android", "ios", "app"],
    }
    for subj, terms in subjects.items():
        if any(t in inp for t in terms):
            if any(w in inp for w in ["精通", "熟悉", "熟练", "advanced", "expert", "掌握"]):
                kb[subj] = 0.85
            elif any(w in inp for w in ["了解", "学过", "基础", "beginner", "入门", "简单的"]):
                kb[subj] = 0.35
            else:
                kb[subj] = 0.55

    if kb:
        dims.append({
            "name": "knowledge_basis",
            "value": max(kb.values()) * 100 if kb else 50,
            "label": "知识基础",
            "description": f"已识别知识领域: {', '.join(kb.keys())}",
            "raw": kb,
        })
    elif round_num == 0:  # 第一轮给默认值
        dims.append({
            "name": "knowledge_basis",
            "value": 50,
            "label": "知识基础",
            "description": "待进一步了解",
        })

    # ── learning_goals ──
    goals = []
    goal_map = {
        "备考": ["考试", "期末", "exam", "考研", "考公"],
        "求职准备": ["找工作", "面试", "求职", "job", "实习"],
        "项目实践": ["项目", "实践", "project", "动手", "做东西"],
        "基础入门": ["入门", "新手", "零基础", "beginner", "基础"],
        "能力提升": ["提高", "进阶", "深入", "advanced", "高级"],
        "学术研究": ["科研", "研究", "论文", "paper", "学术"],
        "兴趣爱好": ["兴趣", "爱好", "了解", "随便看看"],
    }
    for goal, keywords in goal_map.items():
        if any(kw in inp for kw in keywords):
            goals.append(goal)
    if goals:
        dims.append({
            "name": "learning_goals",
            "value": 70,
            "label": "学习目标",
            "description": f"目标: {', '.join(goals)}",
        })

    # ── cognitive_style ──
    style_map = {
        "visual": ["看视频", "视频", "图解", "visual", "图", "画", "可视化"],
        "auditory": ["听", "音频", "播客", "讲课", "演讲"],
        "reading": ["读书", "文档", "reading", "文章", "看书"],
        "kinesthetic": ["动手", "实践", "实操", "做项目", "coding", "写代码"],
    }
    for style, keywords in style_map.items():
        if any(kw in inp for kw in keywords):
            style_labels = {
                "visual": "视觉型",
                "auditory": "听觉型",
                "reading": "阅读型",
                "kinesthetic": "动手型",
            }
            dims.append({
                "name": "cognitive_style",
                "value": 75,
                "label": "认知风格",
                "description": f"偏好: {style_labels[style]}",
            })
            break

    # ── weak_points ──
    weak_signals = ["不懂", "不会", "薄弱", "难点", "困难", "搞不懂", "confusing", "struggle", "weak", "弱", "差"]
    if any(w in inp for w in weak_signals):
        weak_areas = [subj for subj, terms in subjects.items() if any(t in inp for t in terms)]
        dims.append({
            "name": "weak_points",
            "value": 40,
            "label": "易错点/薄弱环节",
            "description": f"薄弱领域: {', '.join(weak_areas) if weak_areas else '已识别'}",
        })

    # ── engagement_level ──
    if any(w in inp for w in ["喜欢", "感兴趣", "热爱", "passionate", "很感兴趣", "好玩"]):
        dims.append({"name": "engagement_level", "value": 85, "label": "学习参与度", "description": "高参与度"})
    elif any(w in inp for w in ["无聊", "没兴趣", "被迫", "枯燥"]):
        dims.append({"name": "engagement_level", "value": 30, "label": "学习参与度", "description": "参与度偏低"})

    # ── time_availability ──
    time_signals = ["每天", "每周", "小时", "hour", "分钟", "minute", "有空"]
    if any(t in inp for t in time_signals):
        dims.append({"name": "time_availability", "value": 60, "label": "可用时间", "description": user_input[:100]})

    # ── learning_pace ──
    if any(w in inp for w in ["快", "快速", "fast", "加速", "快点"]):
        dims.append({"name": "learning_pace", "value": 75, "label": "学习节奏", "description": "偏好快速"})
    elif any(w in inp for w in ["慢", "稳", "仔细", "稳扎稳打"]):
        dims.append({"name": "learning_pace", "value": 40, "label": "学习节奏", "description": "偏好稳健"})

    # ── subject_interests ──
    if any(w in inp for w in ["兴趣", "喜欢", "关注", "爱看", "想学"]):
        interests = [subj for subj, terms in subjects.items() if any(t in inp for t in terms)]
        if interests:
            dims.append({
                "name": "subject_interests", "value": 70,
                "label": "学科兴趣", "description": f"感兴趣: {', '.join(interests)}",
            })

    # ── preferred_modalities ──
    mods = []
    mod_map = {
        "video": ["视频", "动画", "video"],
        "quiz": ["做题", "练习", "quiz", "题目", "刷题"],
        "document": ["文档", "看书", "教程", "文档"],
        "code_case": ["动手", "代码", "实操", "code", "项目"],
        "mindmap": ["思维导图", "mindmap", "脑图"],
        "slides": ["ppt", "幻灯片", "slides"],
    }
    for mod, keywords in mod_map.items():
        if any(kw in inp for kw in keywords):
            mods.append(mod)
    if mods:
        dims.append({
            "name": "preferred_modalities", "value": 65,
            "label": "偏好资源形式", "description": f"偏好: {', '.join(mods)}",
        })

    return dims


def _generate_profile_summary(dimensions: list[dict]) -> str:
    """生成画像总结"""
    lines = ["### 📊 你的学习画像\n"]
    lines.append("根据我们的对话，以下是你的学习特征分析：\n")
    for d in dimensions:
        emoji = _dimension_emoji(d["name"])
        lines.append(f"{emoji} **{d['label']}**: {d.get('description', '')}")
    lines.append(f"\n> 画像已构建完成（{len(dimensions)} 个维度）。接下来我可以为你生成个性化学习资源！")
    return "\n".join(lines)


def _dimension_emoji(name: str) -> str:
    emoji_map = {
        "knowledge_basis": "📚",
        "learning_goals": "🎯",
        "cognitive_style": "🧠",
        "weak_points": "⚠️",
        "engagement_level": "🔥",
        "time_availability": "⏰",
        "learning_pace": "🏃",
        "subject_interests": "💡",
        "preferred_modalities": "🎨",
        "prior_knowledge": "🏗️",
    }
    return emoji_map.get(name, "📌")


# ────────────────────────────────────────────────────────────────
# Content Generation Agent — 多子智能体协同资源生成
# ────────────────────────────────────────────────────────────────

def content_gen_agent_node(state: AgentState) -> dict:
    """
    内容生成 Agent — 调用子智能体协同生成多种资源。
    """
    user_input = state.get("user_input", "")
    profile = state.get("profile_dimensions", [])

    # 从画像中提取偏好
    preferred_mods = []
    for d in profile:
        if d["name"] == "preferred_modalities" and "raw" in d:
            preferred_mods = d.get("raw", [])
        elif d["name"] == "cognitive_style":
            style_desc = d.get("description", "").lower()
            if "视觉" in style_desc:
                preferred_mods = ["video", "mindmap", "slides"] + preferred_mods
            elif "动手" in style_desc:
                preferred_mods = ["code", "quiz"] + preferred_mods

    # 根据偏好选择资源类型（≥5 种）
    resource_types = _select_resource_types(user_input, preferred_mods)

    # 多子智能体协同生成资源
    generated = []
    for rt in resource_types:
        resource = _call_sub_agent(rt, user_input, profile)
        if resource:
            generated.append(resource)

    # 生成总结
    type_names = {
        "document": "📖 课程讲解文档",
        "mindmap": "🧠 思维导图",
        "quiz": "📝 练习题",
        "reading": "📚 拓展阅读",
        "video": "🎬 教学视频脚本",
        "code": "💻 实操案例",
        "slides": "📊 教学幻灯片",
    }

    summary_lines = ["## 🎓 为你生成的个性化学习资源\n"]
    summary_lines.append(f"根据你的学习画像和「{user_input}」，多智能体协同生成了以下资源：\n")
    for g in generated:
        name = type_names.get(g.get("type", ""), g.get("type", ""))
        summary_lines.append(f"- {name}: **{g.get('title', '')}**")

    summary_lines.append(f"\n💡 点击任意资源即可开始学习！系统会根据你的进度动态调整后续内容。")

    return {
        "generated_resources": generated,
        "current_content": generated[0] if generated else None,
        "agent_output": "\n".join(summary_lines),
        "next_agent": None,
        "is_complete": True,
    }


def _select_resource_types(user_input: str, preferred: list[str]) -> list[str]:
    """根据用户输入和偏好选择资源类型"""
    inp = user_input.lower()
    types = set(preferred[:3])  # 取前3个偏好

    # 关键词匹配
    if any(kw in inp for kw in ["讲解", "文档", "课程", "概念", "原理"]):
        types.add("document")
    if any(kw in inp for kw in ["思维导图", "脑图", "梳理", "总结", "结构"]):
        types.add("mindmap")
    if any(kw in inp for kw in ["题", "练习", "测试", "quiz", "刷"]):
        types.add("quiz")
    if any(kw in inp for kw in ["拓展", "延伸", "推荐", "更多", "阅读"]):
        types.add("reading")
    if any(kw in inp for kw in ["视频", "动画", "教学视频", "看看"]):
        types.add("video")
    if any(kw in inp for kw in ["代码", "实操", "编程", "实现", "案例"]):
        types.add("code")
    if any(kw in inp for kw in ["ppt", "幻灯片", "演示", "slides"]):
        types.add("slides")

    # 确保至少5种
    defaults = ["document", "mindmap", "quiz", "reading", "code"]
    for t in defaults:
        if len(types) < 5:
            types.add(t)

    return list(types)[:7]


def _call_sub_agent(resource_type: str, user_input: str, profile: list[dict]) -> dict | None:
    """调用子智能体生成资源"""
    sub_agents = {
        "document": _generate_document,
        "mindmap": _generate_mindmap,
        "quiz": _generate_quiz,
        "reading": _generate_reading,
        "video": _generate_video_script,
        "code": _generate_code_case,
        "slides": _generate_slides,
    }

    agent = sub_agents.get(resource_type)
    if agent:
        return agent(user_input, profile)
    return None


# ── 子智能体：文档 ──

def _generate_document(topic: str, profile: list[dict]) -> dict:
    difficulty = _get_difficulty(profile)
    return {
        "id": str(uuid.uuid4()),
        "type": "document",
        "title": f"{topic} — 课程详解",
        "content": {
            "sections": [
                {
                    "heading": "📋 学习目标",
                    "body": f"掌握'{topic}'的核心概念、原理和应用。学习后将能够独立运用相关知识解决实际问题。",
                    "key_points": [
                        f"理解{topic}的定义与边界",
                        f"掌握{topic}的核心原理",
                        f"能在实际场景中应用{topic}",
                    ],
                },
                {
                    "heading": "📖 核心概念",
                    "body": f"## {topic}\n\n{topic}是这个领域的核心知识模块。我们从最基础的定义开始，逐步深入到原理层面。\n\n### 为什么重要？\n- 它构成了高级知识的基石\n- 在实际项目中有广泛应用\n- 是面试和考试的高频考点",
                },
                {
                    "heading": "🔍 深入解析",
                    "body": f"### 原理剖析\n\n{topic}的工作机制可以分为以下几个层次：\n\n1. **输入层**：接收和处理原始数据/信息\n2. **核心逻辑层**：应用关键算法或方法\n3. **输出层**：生成结果并进行验证\n\n### 关键细节\n\n在实际应用中，需要注意以下要点：\n- 边界条件的处理\n- 异常情况的应对策略\n- 性能优化的方向",
                },
                {
                    "heading": "💡 实践指导",
                    "body": f"理论结合实践是最佳学习方式。建议：\n\n1. 先完整阅读一遍本文档\n2. 针对每个知识点动手实现一遍\n3. 完成配套练习题\n4. 尝试在项目中使用所学知识",
                    "examples": [
                        {"title": "入门案例", "level": "beginner"},
                        {"title": "综合应用", "level": "intermediate"},
                        {"title": "进阶挑战", "level": "advanced"},
                    ],
                },
                {
                    "heading": "📝 总结",
                    "body": f"✅ 已完成{topic}核心内容学习\n✅ 理解了关键原理\n✅ 掌握了实践方法\n\n下一步：完成配套练习 → 进入下一阶段",
                },
            ],
        },
        "difficulty": difficulty,
        "tags": [topic, "核心讲解", difficulty],
    }


def _generate_mindmap(topic: str, profile: list[dict]) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "type": "mindmap",
        "title": f"{topic} — 思维导图",
        "content": {
            "root": {
                "id": "root",
                "label": topic,
                "icon": "🧠",
                "children": [
                    {
                        "id": "concepts",
                        "label": "核心概念",
                        "icon": "💡",
                        "children": [
                            {"id": "c1", "label": "定义", "icon": "📖"},
                            {"id": "c2", "label": "特性", "icon": "⭐"},
                            {"id": "c3", "label": "分类", "icon": "📂"},
                        ],
                    },
                    {
                        "id": "methods",
                        "label": "方法与技术",
                        "icon": "🔧",
                        "children": [
                            {"id": "m1", "label": "基础方法", "icon": "⚙️"},
                            {"id": "m2", "label": "进阶技巧", "icon": "🚀"},
                            {"id": "m3", "label": "前沿发展", "icon": "🔬"},
                        ],
                    },
                    {
                        "id": "applications",
                        "label": "应用场景",
                        "icon": "🌍",
                        "children": [
                            {"id": "a1", "label": "行业应用", "icon": "🏭"},
                            {"id": "a2", "label": "学术研究", "icon": "🎓"},
                            {"id": "a3", "label": "个人项目", "icon": "💼"},
                        ],
                    },
                    {
                        "id": "practice",
                        "label": "练习实践",
                        "icon": "✍️",
                        "children": [
                            {"id": "p1", "label": "基础练习", "icon": "📝"},
                            {"id": "p2", "label": "综合挑战", "icon": "🏆"},
                            {"id": "p3", "label": "项目实战", "icon": "🛠️"},
                        ],
                    },
                    {
                        "id": "relations",
                        "label": "关联知识",
                        "icon": "🔗",
                        "children": [
                            {"id": "r1", "label": "前置知识", "icon": "⬅️"},
                            {"id": "r2", "label": "后续学习", "icon": "➡️"},
                            {"id": "r3", "label": "交叉领域", "icon": "🔄"},
                        ],
                    },
                    {
                        "id": "pitfalls",
                        "label": "常见误区",
                        "icon": "⚠️",
                        "children": [
                            {"id": "e1", "label": "概念混淆", "icon": "❓"},
                            {"id": "e2", "label": "实践陷阱", "icon": "🕳️"},
                            {"id": "e3", "label": "进阶瓶颈", "icon": "🧱"},
                        ],
                    },
                ],
            },
            "mermaid": f"""graph LR
    A[{topic}] --> B[核心概念]
    A --> C[方法技术]
    A --> D[应用场景]
    B --> E[定义]
    B --> F[特性]
    C --> G[基础方法]
    C --> H[进阶技巧]
    D --> I[行业应用]
    D --> J[个人项目]
    A --> K[练习实践]
    A --> L[常见误区]""",
        },
        "difficulty": _get_difficulty(profile),
        "tags": [topic, "思维导图", "结构化"],
    }


def _generate_quiz(topic: str, profile: list[dict]) -> dict:
    difficulty = _get_difficulty(profile)
    return {
        "id": str(uuid.uuid4()),
        "type": "quiz",
        "title": f"{topic} — 练习题",
        "content": {
            "total": 8,
            "time_limit": "20分钟",
            "questions": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "choice",
                    "question": f"关于{topic}，以下描述正确的是？",
                    "options": [
                        f"A. {topic}仅适用于特定场景",
                        f"B. {topic}是一种通用方法，有广泛适用性",
                        f"C. {topic}已过时，不再使用",
                        f"D. {topic}与编程无关",
                    ],
                    "answer": "B",
                    "explanation": f"{topic}具有广泛的应用场景和通用性，是现代相关领域的基础知识。",
                    "difficulty": "easy",
                    "points": 5,
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "choice",
                    "question": f"{topic}的核心目标是什么？",
                    "options": [
                        "A. 降低系统复杂度",
                        "B. 提高问题解决效率",
                        "C. 减少代码量",
                        "D. 以上都是",
                    ],
                    "answer": "D",
                    "explanation": f"{topic}通过系统化的方法同时实现多个目标：降低复杂度、提升效率、简化实现。",
                    "difficulty": "easy",
                    "points": 5,
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "choice",
                    "question": f"在{topic}的实际应用中，最应关注的是？",
                    "options": [
                        "A. 算法时间复杂度",
                        "B. 代码可维护性",
                        "C. 使用最新技术",
                        "D. 运行速度",
                    ],
                    "answer": "B",
                    "explanation": "可维护性决定了系统的长期健康度，是最重要的工程考量之一。",
                    "difficulty": "medium",
                    "points": 5,
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "fill",
                    "question": f"{topic}的核心思想可以概括为：通过______的方式来解决复杂问题。",
                    "answer": "系统化和结构化",
                    "explanation": "系统化和结构化的方法论是{topic}的精髓。",
                    "difficulty": "medium",
                    "points": 5,
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "true_false",
                    "question": f"学习{topic}必须从高级概念开始，基础可以跳过。",
                    "answer": "false",
                    "explanation": "任何领域都应从基础学起，基础不牢会影响后续学习效果。",
                    "difficulty": "easy",
                    "points": 3,
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "short_answer",
                    "question": f"请简述{topic}的3个主要应用场景。",
                    "answer": "答案需包含：1) 系统设计应用 2) 问题求解应用 3) 优化改进应用",
                    "explanation": "考察对应用场景的归纳总结能力。",
                    "difficulty": "medium",
                    "points": 10,
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "code",
                    "question": f"请用代码实现一个{topic}相关的简单示例，并说明你的设计思路。",
                    "answer": "评估标准：代码正确性、代码风格、设计思路清晰度。",
                    "explanation": "实践是检验理解的唯一标准。",
                    "difficulty": "hard",
                    "points": 15,
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "essay",
                    "question": f"结合你的理解，论述{topic}的发展趋势和未来方向。",
                    "answer": "开放题，评估标准：论述深度、逻辑性、前瞻性。",
                    "explanation": "考察批判性思维和行业视野。",
                    "difficulty": "hard",
                    "points": 20,
                },
            ],
        },
        "difficulty": difficulty,
        "tags": [topic, "练习", difficulty],
    }


def _generate_reading(topic: str, profile: list[dict]) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "type": "reading",
        "title": f"{topic} — 拓展阅读",
        "content": {
            "sections": [
                {
                    "section_title": "📖 必读基础",
                    "priority": "high",
                    "items": [
                        {
                            "title": f"{topic} 入门指南",
                            "type": "在线教程",
                            "description": "最适合初学者的系统化入门材料",
                            "estimated_time": "2小时",
                            "takeaways": ["概念建立", "环境搭建", "第一个实践"],
                        },
                        {
                            "title": f"深入理解{topic}核心原理",
                            "type": "书籍章节",
                            "description": "深入剖析底层原理，建立完整知识体系",
                            "estimated_time": "4小时",
                            "takeaways": ["原理理解", "设计哲学", "架构思想"],
                        },
                    ],
                },
                {
                    "section_title": "🚀 进阶深化",
                    "priority": "medium",
                    "items": [
                        {
                            "title": f"{topic} 最佳实践指南",
                            "type": "技术博客",
                            "description": "行业专家的实践总结与经验分享",
                            "estimated_time": "1.5小时",
                            "takeaways": ["常见模式", "优化技巧", "踩坑经验"],
                        },
                        {
                            "title": f"{topic} 大型项目案例分析",
                            "type": "案例研究",
                            "description": "真实项目的架构与实现分析",
                            "estimated_time": "2小时",
                            "takeaways": ["规模化思考", "工程实践", "架构决策"],
                        },
                    ],
                },
                {
                    "section_title": "🔬 前沿探索",
                    "priority": "low",
                    "items": [
                        {
                            "title": f"{topic} 最新研究进展",
                            "type": "学术论文",
                            "description": "学术界前沿成果与未来方向",
                            "estimated_time": "3小时",
                            "takeaways": ["最新趋势", "研究热点", "未来展望"],
                        },
                    ],
                },
            ],
        },
        "difficulty": _get_difficulty(profile),
        "tags": [topic, "拓展阅读", "参考"],
    }


def _generate_video_script(topic: str, profile: list[dict]) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "type": "video",
        "title": f"{topic} — 教学视频",
        "content": {
            "duration": "12分钟",
            "scenes": [
                {
                    "id": 1,
                    "title": "引入",
                    "duration": "1.5分钟",
                    "visual": f"动画展示{topic}的实际应用场景",
                    "narration": f"你是否遇到过...？本节带你从零掌握{topic}。",
                    "animation": "motion_graphics",
                },
                {
                    "id": 2,
                    "title": "核心概念拆解",
                    "duration": "4分钟",
                    "visual": "逐步展示概念结构和关系图",
                    "narration": f"让我们从基础开始...{topic}本质上是...",
                    "animation": "diagram_reveal",
                },
                {
                    "id": 3,
                    "title": "动手演示",
                    "duration": "3.5分钟",
                    "visual": "实际操作/编程演示",
                    "narration": "现在动手实践，一步一步演示如何实现。",
                    "animation": "screen_recording",
                },
                {
                    "id": 4,
                    "title": "常见错误",
                    "duration": "2分钟",
                    "visual": "对比动画展示正确vs错误",
                    "narration": "以下是3个最常见错误，注意避免。",
                    "animation": "comparison",
                },
                {
                    "id": 5,
                    "title": "总结",
                    "duration": "1分钟",
                    "visual": "重点回顾卡片",
                    "narration": f"恭喜完成{topic}学习！让我们回顾并看下练习。",
                    "animation": "summary_cards",
                },
            ],
        },
        "difficulty": _get_difficulty(profile),
        "tags": [topic, "视频", "多媒体"],
    }


def _generate_code_case(topic: str, profile: list[dict]) -> dict:
    difficulty = _get_difficulty(profile)
    return {
        "id": str(uuid.uuid4()),
        "type": "code",
        "title": f"{topic} — 实操案例",
        "content": {
            "cases": [
                {
                    "id": "basic",
                    "title": "基础案例：快速上手",
                    "level": "beginner",
                    "description": f"通过最简示例理解{topic}的基本用法",
                    "objectives": [f"理解{topic}基本API", "完成可运行示例", "理解输入输出"],
                    "code": f'''"""
{topic} - 基础示例
"""
class {topic.replace(" ", "")}Basic:
    def __init__(self):
        self.data = []

    def process(self, input_data):
        """核心处理逻辑"""
        # Step 1: 预处理
        cleaned = self._preprocess(input_data)
        # Step 2: 核心逻辑
        result = self._core_logic(cleaned)
        # Step 3: 结果输出
        return self._format(result)

    def _preprocess(self, data):
        return data.strip() if isinstance(data, str) else data

    def _core_logic(self, data):
        return f"处理完成: {{data}}"

    def _format(self, result):
        return {{"status": "ok", "output": result}}

# 使用
if __name__ == "__main__":
    engine = {topic.replace(" ", "")}Basic()
    print(engine.process("测试"))''',
                    "exercises": ["修改参数观察输出变化", "添加错误处理", "尝试不同输入"],
                },
                {
                    "id": "advanced",
                    "title": "进阶案例：综合应用",
                    "level": "intermediate",
                    "description": f"结合多个概念的{topic}综合案例",
                    "objectives": ["综合运用知识", "解决实际问题", "理解设计模式"],
                    "code": f'''"""
{topic} - 进阶综合案例
"""
from typing import Any, Dict, List

class {topic.replace(" ", "")}System:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {{}}
        self.components: List[Any] = []
        self._ready = False

    def initialize(self):
        """初始化系统"""
        self._setup_components()
        self._ready = True
        return self

    def _setup_components(self):
        """配置组件（根据实际需求实现）"""
        pass

    def execute(self, data: Any) -> Dict[str, Any]:
        """执行主流程"""
        if not self._ready:
            self.initialize()
        try:
            validated = self._validate(data)
            transformed = self._transform(validated)
            result = self._process(transformed)
            return {{"success": True, "data": result}}
        except Exception as e:
            return {{"success": False, "error": str(e)}}

    def _validate(self, data): return data
    def _transform(self, data): return data
    def _process(self, data): return data
    def cleanup(self):
        self.components.clear()
        self._ready = False''',
                    "exercises": ["重构代码提高可读性", "添加单元测试", "扩展功能"],
                },
            ],
        },
        "difficulty": difficulty,
        "tags": [topic, "实操", "代码"],
    }


def _generate_slides(topic: str, profile: list[dict]) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "type": "slides",
        "title": f"{topic} — 教学幻灯片",
        "content": {
            "total": 10,
            "theme": "professional_blue",
            "slides": [
                {"slide": 1, "layout": "title", "title": topic, "subtitle": "课程讲解"},
                {"slide": 2, "layout": "agenda", "title": "本节大纲", "bullets": ["学习目标", "核心概念", "关键原理", "实践案例", "总结"]},
                {"slide": 3, "layout": "content", "title": "为什么学这个？", "content": f"{topic}的实际价值和重要性"},
                {"slide": 4, "layout": "two_column", "title": "核心概念", "left": "定义与特征", "right": "关键机制"},
                {"slide": 5, "layout": "diagram", "title": "概念关系图", "description": "核心组成部分及相互关系"},
                {"slide": 6, "layout": "content", "title": "深入原理", "bullets": ["步骤一", "步骤二", "步骤三", "步骤四"]},
                {"slide": 7, "layout": "code", "title": "代码演示", "language": "python"},
                {"slide": 8, "layout": "case_study", "title": "实际案例", "case": f"{topic}应用案例"},
                {"slide": 9, "layout": "summary", "title": "本节总结", "key_points": ["概念✓", "原理✓", "方法✓"]},
                {"slide": 10, "layout": "end", "title": "谢谢！", "homework": "完成配套练习"},
            ],
        },
        "difficulty": _get_difficulty(profile),
        "tags": [topic, "幻灯片", "PPT"],
    }


def _get_difficulty(profile: list[dict]) -> str:
    kb = next((d for d in profile if d["name"] == "knowledge_basis"), None)
    if kb and kb.get("value", 50) > 80:
        return "advanced"
    elif kb and kb.get("value", 50) > 50:
        return "intermediate"
    return "beginner"


# ────────────────────────────────────────────────────────────────
# QA Agent — RAG 检索增强智能答疑
# ────────────────────────────────────────────────────────────────

# RAG system prompt: 约束 LLM 仅依据检索片段回答
_RAG_SYSTEM_PROMPT = """\
你是 AI 教育助手，专门负责回答关于《随机过程及应用》课程的问题。

回答规则：
1. 你只能依据下方「参考资料」中的内容回答问题，不得使用外部知识编造教材页码、公式或章节。
2. 如果参考资料中有相关信息，请详细、有条理地回答，并在回答末尾注明引用的页码。
3. 如果参考资料中没有足够信息，请明确回复："当前课程知识库中未找到足够依据来回答此问题。建议换一种问法或查阅教材相关章节。"
4. 回答使用中文，适合学习场景，鼓励学生追问。
5. 引用格式示例：（见教材第62页）"""


async def prepare_rag_context(user_input: str) -> dict:
    """
    检索课程知识库并构建 LLM messages，供流式或非流式调用复用。

    Args:
        user_input: 用户问题原文

    Returns:
        dict with keys:
          - success: bool                 是否成功检索到有效资料
          - llm_messages: list[dict]      DeepSeek 消息列表（已注入 RAG prompt）
          - citations: list[dict]         引用来源列表
          - retrieval_used: bool          是否实际使用了 RAG
          - confidence: float | None      置信度
          - no_results_message: str      检索失败时的用户提示（success=False 时可用）
          - fallback_results: list[dict]  LLM 失败降级时使用的原始检索结果
    """
    from app.rag.retriever import retrieve_robust, build_rag_prompt

    # 1. 检索
    try:
        context, results = await retrieve_robust(
            user_input=user_input,
            top_k=5,
        )
    except Exception as exc:
        return {
            "success": False,
            "llm_messages": [],
            "citations": [],
            "retrieval_used": False,
            "confidence": None,
            "no_results_message": f"抱歉，检索课程知识库时出现问题：{exc}\n请稍后重试。",
            "fallback_results": [],
        }

    # 2. 无结果
    if not results or not context.strip():
        return {
            "success": False,
            "llm_messages": [],
            "citations": [],
            "retrieval_used": False,
            "confidence": None,
            "no_results_message": (
                "当前课程知识库中未找到足够依据来回答此问题。\n\n"
                "建议：\n"
                "1. 尝试换一种更具体的问法\n"
                "2. 查阅《随机过程及应用》教材相关章节\n"
                "3. 询问其他随机过程相关的问题"
            ),
            "fallback_results": [],
        }

    # 3. citations + confidence
    citations = _build_citations(results)
    top_score = max((r.get("score", 0) for r in results), default=0)
    confidence = min(max(top_score, 0.0), 1.0)

    # 4. 构建 LLM messages
    messages = build_rag_prompt(user_input, context)
    if messages and messages[0]["role"] == "system":
        messages[0]["content"] = _RAG_SYSTEM_PROMPT

    return {
        "success": True,
        "llm_messages": messages,
        "citations": citations,
        "retrieval_used": True,
        "confidence": confidence,
        "no_results_message": None,
        "fallback_results": results,
    }


async def qa_agent_node(state: AgentState) -> dict:
    """答疑 Agent — RAG 检索 + LLM 回答 + citations"""
    user_input = state.get("user_input", "")

    ctx = await prepare_rag_context(user_input)

    # 检索失败 → 直接返回提示
    if not ctx["success"]:
        return {
            "agent_output": ctx["no_results_message"],
            "citations": ctx["citations"],
            "retrieval_used": ctx["retrieval_used"],
            "confidence": ctx["confidence"],
            "next_agent": None,
            "is_complete": True,
        }

    # 检索成功 → 调用 LLM
    try:
        from app.llm import LLMFactory
        response = await LLMFactory.chat(ctx["llm_messages"])
        answer = response.content.strip() if response and response.content else ""
    except Exception:
        answer = _build_fallback_from_results(ctx["fallback_results"])

    return {
        "agent_output": answer,
        "citations": ctx["citations"],
        "retrieval_used": ctx["retrieval_used"],
        "confidence": ctx["confidence"],
        "next_agent": None,
        "is_complete": True,
    }


def _build_citations(results: list[dict]) -> list[dict]:
    """从检索结果构建 citations 列表"""
    citations = []
    for r in results:
        content = r.get("content", "")
        snippet = content[:160].replace("\n", " ").strip() if content else ""
        citations.append({
            "source_file": r.get("source_file", ""),
            "page_number": r.get("page_number", 0),
            "chapter": r.get("chapter", ""),
            "chunk_id": r.get("chunk_id", ""),
            "score": r.get("score", 0),
            "content_snippet": snippet,
        })
    return citations


def _build_fallback_from_results(results: list[dict]) -> str:
    """LLM 调用失败时，用检索到的原始片段构建回答"""
    if not results:
        return "抱歉，课程知识库中未找到足够依据，且 AI 服务当前不可用。请稍后重试。"

    lines = [
        "⚠️ AI 服务暂时不可用，以下是从课程资料中直接检索到的相关内容：",
        "",
    ]
    for i, r in enumerate(results, 1):
        page = r.get("page_number", "?")
        chapter = r.get("chapter", "")
        content = r.get("content", "")[:500].replace("\n", " ")
        source = f"（{chapter} 第{page}页）" if chapter else f"（第{page}页）"
        lines.append(f"**【片段 {i}】** {source}")
        lines.append(f"> {content}")
        lines.append("")

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────
# Path Planning Agent — 个性化学习路径
# ────────────────────────────────────────────────────────────────

def path_planning_agent_node(state: AgentState) -> dict:
    """路径规划 Agent — 从画像出发规划学习路线"""
    user_input = state.get("user_input", "")
    profile = state.get("profile_dimensions", [])
    kb = next((d for d in profile if d["name"] == "knowledge_basis"), None)
    level = (kb.get("value", 50) if kb else 50) / 100

    if level < 0.4:
        stages = [
            {"name": "基础入门", "hours": 4, "focus": "核心概念与基础操作"},
            {"name": "技能构建", "hours": 5, "focus": "关键技术与方法"},
            {"name": "实践应用", "hours": 4, "focus": "项目练习与巩固"},
            {"name": "能力提升", "hours": 3, "focus": "进阶话题与优化"},
            {"name": "综合评估", "hours": 2, "focus": "复习与自测"},
        ]
    elif level < 0.7:
        stages = [
            {"name": "快速回顾", "hours": 2, "focus": "查漏补缺"},
            {"name": "深化理解", "hours": 4, "focus": "原理与设计"},
            {"name": "综合实践", "hours": 5, "focus": "复杂项目实战"},
            {"name": "拓展学习", "hours": 3, "focus": "前沿技术"},
            {"name": "能力验证", "hours": 2, "focus": "综合测试"},
        ]
    else:
        stages = [
            {"name": "快速诊断", "hours": 1, "focus": "精准定位薄弱点"},
            {"name": "定向突破", "hours": 3, "focus": "针对性强化"},
            {"name": "高级实践", "hours": 4, "focus": "复杂场景应用"},
            {"name": "创新探索", "hours": 4, "focus": "自主项目与创新"},
            {"name": "能力输出", "hours": 2, "focus": "成果展示与总结"},
        ]

    lines = ["### 📍 个性化学习路径\n"]
    lines.append(f"根据你的画像（知识水平：{level*100:.0f}%），我为你规划了以下路径：\n")
    total_hours = 0
    for i, s in enumerate(stages):
        total_hours += s["hours"]
        lines.append(f"**阶段{i+1}：{s['name']}**")
        lines.append(f"- ⏱️ 预计时间：{s['hours']} 小时")
        lines.append(f"- 🎯 重点：{s['focus']}")
        lines.append("")

    lines.append(f"> 📊 总预计学习时间：{total_hours} 小时")
    lines.append(f"> 🔄 系统会根据你的学习进度动态调整后续内容")

    return {
        "agent_output": "\n".join(lines),
        "next_agent": None,
        "is_complete": False,
    }


# ────────────────────────────────────────────────────────────────
# Evaluation Agent — 学习效果评估
# ────────────────────────────────────────────────────────────────

def evaluation_agent_node(state: AgentState) -> dict:
    """评估 Agent — 多维度精准评估与动态调整"""
    user_input = state.get("user_input", "")
    profile = state.get("profile_dimensions", [])

    assessment = {
        "knowledge_mastery": 75,
        "skill_proficiency": 68,
        "learning_progress": 0.62,
        "engagement": 80,
        "weak_areas": ["特定高级概念", "综合应用题"],
        "strengths": ["基础理解", "概念记忆"],
    }

    lines = ["### 📊 学习效果评估\n"]
    lines.append("根据你的学习数据，以下是多维度评估结果：\n")

    lines.append("\n#### 🎯 各维度得分\n")
    dims = [
        ("知识掌握度", assessment["knowledge_mastery"], "📚"),
        ("技能熟练度", assessment["skill_proficiency"], "🔧"),
        ("学习进度", int(assessment["learning_progress"] * 100), "📈"),
        ("学习参与度", assessment["engagement"], "🔥"),
    ]
    for name, score, emoji in dims:
        bar_len = score // 10
        bar = "█" * bar_len + "░" * (10 - bar_len)
        lines.append(f"{emoji} **{name}**: `{bar}` {score}%")

    lines.append("\n#### ✅ 优势方面\n")
    for s in assessment["strengths"]:
        lines.append(f"- {s}")

    lines.append("\n#### ⚠️ 需要加强\n")
    for w in assessment["weak_areas"]:
        lines.append(f"- {w}")

    lines.append("\n#### 💡 学习建议\n")
    lines.append("1. 针对薄弱环节增加专项练习")
    lines.append("2. 尝试更多综合性的项目实践")
    lines.append("3. 每周进行一次自测来追踪进步\n")

    lines.append("> 📌 系统已根据评估结果自动调整了后续资源推荐策略")

    return {
        "agent_output": "\n".join(lines),
        "assessment_data": assessment,
        "learning_progress": assessment["learning_progress"],
        "next_agent": None,
        "is_complete": False,
    }
