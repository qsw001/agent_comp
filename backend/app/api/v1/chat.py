"""
API — 对话路由（增强版 — 集成多智能体系统）
"""

from __future__ import annotations

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import run_agent
from app.core.exceptions import NotFoundException, UnauthorizedException
from app.core.security import decode_access_token
from app.database import get_db, async_session_factory
from app.models import ChatMessage, ChatSession, UserMemory
from app.schemas import (
    ApiResponse,
    ChatMessageResponse,
    ChatMessageSend,
    ChatSessionCreate,
    ChatSessionRename,
    ChatSessionResponse,
    MessageResponse,
)

router = APIRouter()


async def _get_recent_history(
    db: AsyncSession,
    session_id: str,
    limit: int = 8,
    max_chars: int = 600,
) -> list[dict]:
    """
    获取会话近期对话历史，用于短期记忆注入。

    按 created_at 降序取最近 limit 条有效的 user/assistant 消息，
    再反转为时间正序。排除空消息和错误提示类内容。

    Args:
        db: 数据库会话
        session_id: 会话 ID
        limit: 最大历史消息条数
        max_chars: 单条消息最长字符数（超出截断）

    Returns:
        list[dict]: [{"role": "user", "content": "..."}, ...]
    """
    from sqlalchemy import desc

    result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id,
            ChatMessage.role.in_(["user", "assistant"]),
            ChatMessage.content.isnot(None),
            ChatMessage.content != "",
        )
        .order_by(desc(ChatMessage.created_at))
        .limit(limit)
    )
    messages = result.scalars().all()
    # 反转为时间正序（旧→新）
    messages.reverse()
    return [
        {
            "role": msg.role,
            "content": msg.content[:max_chars] if len(msg.content) > max_chars else msg.content,
        }
        for msg in messages
    ]


async def _get_long_term_memories(
    db: AsyncSession,
    user_id: str,
    limit: int = 8,
    max_chars: int = 300,
) -> list[dict]:
    """
    读取当前用户的重要长期学习记忆，用于注入 QA Prompt。

    按 importance DESC、updated_at DESC 排序，最多取 limit 条。
    仅读取 VALID_MEMORY_TYPES 类型的记忆。

    Args:
        db: 数据库会话
        user_id: 用户 ID
        limit: 最大记忆条数
        max_chars: 单条 content 最长字符数（超出截断）

    Returns:
        list[dict]: [{"memory_type": "weak_point", "content": "..."}, ...]
    """
    from sqlalchemy import desc
    from app.models.user_memory import VALID_MEMORY_TYPES

    result = await db.execute(
        select(UserMemory)
        .where(
            UserMemory.user_id == user_id,
            UserMemory.memory_type.in_(VALID_MEMORY_TYPES),
            UserMemory.content.isnot(None),
            UserMemory.content != "",
        )
        .order_by(desc(UserMemory.importance), desc(UserMemory.updated_at))
        .limit(limit)
    )
    memories = result.scalars().all()
    return [
        {
            "memory_type": m.memory_type,
            "content": m.content[:max_chars] if len(m.content) > max_chars else m.content,
        }
        for m in memories
    ]


async def _extract_and_store_learning_memories(
    db: AsyncSession,
    user_id: str,
    user_message_id: str,
    user_question: str,
    assistant_answer: str,
) -> None:
    """
    从 QA 对话中提取值得长期记住的学习信息，保存到 user_memories。

    通过 LLM 分析学生提问与 AI 回答，提取稳定的学习特征（薄弱点、偏好、目标等），
    经校验和去重后入库。提取失败静默跳过，绝不影响主对话流程。

    Args:
        db: 数据库会话
        user_id: 用户 ID
        user_message_id: 触发此轮记忆提取的用户消息 ID
        user_question: 用户原始问题
        assistant_answer: AI 最终回答全文
    """
    import re as _re
    from datetime import datetime, timezone
    from app.llm import LLMFactory
    from app.llm.base import LLMConfig
    from app.models.user_memory import UserMemory, VALID_MEMORY_TYPES

    # ── 系统提示词：严格限定记忆提取范围 ──
    _EXTRACTION_SYSTEM_PROMPT = """\
You are a learning memory extractor. Analyze the student's question and the AI tutor's answer.
Output a STRICT JSON array of learning insights worth remembering across sessions.

RULES:
1. Maximum 3 items. Return [] if nothing is worth long-term storage.
2. ONLY record information the student EXPLICITLY stated about themselves.
   Do NOT infer, deduce, guess, or speculate the student's knowledge level, weakness,
   or any other trait from their question topic, phrasing, frequency, or difficulty.

3. **FORBIDDEN INFERENCE — DO NOT generate these memory_types from ordinary questions:**
   - "What is X?" / "X是什么" / "解释X" / "讲讲X" / "X的定义" / "X和Y的区别"
   - Such questions are ordinary knowledge-seeking. They reveal NOTHING about the student.
   - From these questions, do NOT generate: knowledge_level, weak_point, learning_goal.

4. **ONLY generate each memory_type if the student explicitly said something like:**

   knowledge_level ONLY IF the student said:
     "我不会" "看不懂" "不理解" "没学过" "零基础" "基础差"
     "我学过X" "我掌握了X" "我对X很熟悉" "我忘了X" "还记得X"

   weak_point ONLY IF the student said:
     "我总是分不清" "容易混淆" "容易错" "搞混了" "总弄错"
     "这是我的薄弱点" "我不擅长" "X对我来说很困难" "难在X"

   learning_preference ONLY IF the student said:
     "我希望" "请按X方式" "我偏好" "我喜欢X方式" "以后讲解时"
     "下次请" "多用X" "少用X" "先给X再给Y"

   learning_goal ONLY IF the student said:
     "我在准备X" "我的目标" "正在备考" "期末" "考研" "面试"
     "想学完X" "计划X周内" "复习X"

   course_context ONLY IF the student said:
     "我学到第X章" "正在学X" "已经学完X" "刚开始学" "进度到X"

   personal_fact ONLY IF the student stated a personal fact directly relevant to their learning:
     "我是X专业" "我在X年级" "我从事X工作" "我的背景是X"

5. If the student did NOT use any of the above signal words, return [].

6. memory_type MUST be one of:
   learning_goal, knowledge_level, weak_point, learning_preference, course_context, personal_fact

7. importance must be between 0.3 and 1.0. Higher = more valuable to remember long-term.

8. content must be a SHORT, ATOMIC, SELF-CONTAINED statement about the student (≤150 characters).
   Use consistent phrasing. Prefer simple declarative sentences.
   Example good content: "总是混淆平稳增量与独立增量"
   Example bad content: "学生总是分不清平稳增量和独立增量这两个概念，希望在后续讲解中多做对比。"

DO NOT RECORD:
- Anything from one-off factual questions, casual chat, thanks, or greetings
- Passwords, phone numbers, ID numbers, addresses, or any sensitive personal data
- Personal info unrelated to learning (hobbies, relationships, etc.)
- AI tutor's answer content — only record what the STUDENT revealed about themselves

Output format (JSON array only, no extra text):
[{"should_store": true, "memory_type": "weak_point", "content": "...", "importance": 0.7}]"""

    extraction_messages = [
        {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Student question:\n" + user_question + "\n\n"
                "AI tutor answer:\n" + assistant_answer[:2000] + "\n\n"
                "Extract learning memories worth storing long-term (or [] if none)."
            ),
        },
    ]

    # ── 调用 LLM ──
    try:
        extraction_config = LLMConfig(temperature=0.2, max_tokens=1024)
        response = await LLMFactory.chat(extraction_messages, config=extraction_config)
        raw_output = response.content.strip() if response and response.content else ""
    except Exception:
        return  # LLM 调用失败，静默跳过

    if not raw_output:
        return

    # ── 解析 JSON（兼容 markdown code block 包裹） ──
    json_match = _re.search(r'\[[\s\S]*\]', raw_output)
    if not json_match:
        return
    try:
        items = json.loads(json_match.group(0))
    except (json.JSONDecodeError, TypeError):
        return
    if not isinstance(items, list) or len(items) == 0:
        return

    # ── 敏感信息过滤正则 ──
    _SENSITIVE_PATTERNS = [
        _re.compile(r'\b1[3-9]\d{9}\b'),                     # 手机号
        _re.compile(r'\b\d{17}[\dXx]\b'),                    # 身份证
        _re.compile(r'\b\d{15,19}\b'),                       # 银行卡等长数字
        _re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'),  # 邮箱
    ]

    def _contains_sensitive(text: str) -> bool:
        return any(p.search(text) for p in _SENSITIVE_PATTERNS)

    # ── 逐条校验并入库 ──
    stored_count = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        if not item.get("should_store", False):
            continue

        memory_type = str(item.get("memory_type", "")).strip()
        content = str(item.get("content", "")).strip()
        importance = float(item.get("importance", 0))

        # 校验字段合法性
        if memory_type not in VALID_MEMORY_TYPES:
            continue
        if not content or len(content) > 300:
            continue
        if importance < 0.3 or importance > 1.0:
            continue
        if _contains_sensitive(content):
            continue

        # 代码级防线：校验 user_question 中是否包含对应类型的显式信号
        if not _has_explicit_signal(memory_type, user_question):
            continue

        # 去重：检查同一 (user_id, memory_type) 下是否有内容高度相似的记忆
        existing = await db.execute(
            select(UserMemory).where(
                UserMemory.user_id == user_id,
                UserMemory.memory_type == memory_type,
            )
        )
        existing_mems = existing.scalars().all()
        norm_new = _normalize_for_dedup(content)

        match = _find_similar_memory(norm_new, existing_mems)
        if match is not None:
            # 合并：保留信息更完整的一条，importance 取最大值
            best_content = content if len(content) >= len(match.content) else match.content
            best_importance = max(importance, match.importance)
            match.content = best_content
            match.importance = best_importance
            match.updated_at = datetime.now(timezone.utc)
            db.add(match)
            stored_count += 1
            continue

        memory = UserMemory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
            source_message_id=user_message_id,
        )
        db.add(memory)
        stored_count += 1

    if stored_count > 0:
        try:
            await db.commit()
        except Exception:
            await db.rollback()


# ── 代码级防线：各 memory_type 的用户显式信号词表 ──
# 若 user_question 中不包含对应类型的信号词，即使 LLM 返回了候选记忆也会被丢弃。

_SIGNAL_PATTERNS: dict[str, str] = {
    "knowledge_level":
        "不会|看不懂|不理解|没学过|零基础|基础差|不熟|搞不懂|"
        "我学过|我掌握了|我了解|我熟悉|我很熟|还记得|我忘了|忘记了|忘了|"
        "对我来说.*简单|对我来说.*容易|我已经会了",
    "weak_point":
        "分不清|容易错|易混淆|搞混|弄错|总是错|老错|常错|"
        "薄弱|不擅长|困难|难在|很难|太难|我的弱项|我最大的问题|"
        "搞不清楚|弄不明白|老搞混",
    "learning_preference":
        "希望|请按|偏好|喜欢|以后|下次|讲解时|多用|少用|"
        "先.*再|多.*少|尽量|最好是|能不能|可以不可|"
        "我比较喜欢|我想要.*方式",
    "learning_goal":
        "准备|目标|考试|复习|想学完|计划|备考|期末|考研|面试|"
        "我打算|我要学|我的方向|想达到|冲刺",
    "course_context":
        "学到第|正在学|已经学完|进度|第.*章|刚开始|快学完了|"
        "我目前.*章|上到|讲到了|学到.*节|学完.*章",
    "personal_fact":
        "我是.*专业|我在.*年级|我工作|我从事|我的背景是|我的专业是|"
        "我现在.*工作|我是.*学生|我读",
}


def _has_explicit_signal(memory_type: str, user_question: str) -> bool:
    """
    代码级防线：校验 user_question 中是否包含对应 memory_type 的显式信号词。

    仅检查用户原始提问文本，不依赖 LLM 判断。若没有匹配信号，该候选记忆
    将被丢弃，无论 LLM 如何判断。

    Args:
        memory_type: 记忆类型 (learning_goal / knowledge_level 等)
        user_question: 用户原始提问文本

    Returns:
        True 当且仅当 user_question 中包含了该类型的显式信号词
    """
    import re as _signal_re

    pattern_str = _SIGNAL_PATTERNS.get(memory_type)
    if not pattern_str:
        return True  # 未知类型放行（VALID_MEMORY_TYPES 已在调用方校验）

    return bool(_signal_re.search(pattern_str, user_question))


def _normalize_for_dedup(text: str) -> str:
    """规范化文本用于去重比对：去标点、合并空白、同义表达归一化"""
    import re as _re
    t = text.strip().lower()
    t = _re.sub(r'\s+', ' ', t)           # 合并空白
    t = _re.sub(r'[，。「」、；：？！]', '', t)  # 去除中文标点
    t = _re.sub(r'[,.\-;:?!]', '', t)     # 去除英文标点
    # 同义表达归一化
    for src, dst in _SYNONYM_MAP.items():
        t = t.replace(src, dst)
    return t


def _find_similar_memory(norm_content: str, existing_mems: list) -> object | None:
    """
    在已有记忆中查找与候选内容近似的记录。

    判断规则（按优先级）：
    1. 规范化文本精确匹配 → 重复
    2. 字符 bigram Jaccard ≥ 0.70 → 重复
    3. 公共子串覆盖率 ≥ 0.65（对短句/长句语义等价特别有效）

    Returns:
        匹配的已有 UserMemory 对象，无匹配则返回 None
    """
    if not norm_content or not existing_mems:
        return None

    for m in existing_mems:
        norm_existing = _normalize_for_dedup(m.content)

        # 规则 1：精确匹配
        if norm_existing == norm_content:
            return m

        # 规则 2：bigram Jaccard
        if _bigram_jaccard(norm_existing, norm_content) >= 0.70:
            return m

        # 规则 3：公共子串覆盖率（较短文本被较长文本覆盖的比例）
        shorter = norm_content if len(norm_content) <= len(norm_existing) else norm_existing
        coverage = _common_substring_coverage(shorter, norm_existing if shorter == norm_content else norm_content)
        if coverage >= 0.65:
            return m

    return None


def _bigram_jaccard(a: str, b: str) -> float:
    """字符 bigram Jaccard 相似度"""
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    bg_a = {a[i:i + 2] for i in range(len(a) - 1)} if len(a) >= 2 else {a}
    bg_b = {b[i:i + 2] for i in range(len(b) - 1)} if len(b) >= 2 else {b}
    if not bg_a or not bg_b:
        return 0.0
    return len(bg_a & bg_b) / len(bg_a | bg_b)


def _common_substring_coverage(short: str, long: str) -> float:
    """
    计算 short 中有多少比例的字符被「与 long 共享的 ≥2 字子串」覆盖。

    例：short="容易混淆平稳增量与独立增量", long="学生总是混淆平稳增量…"
        → 公共子串 "混淆平稳增量" 和 "独立增量" 覆盖 short 中大部分字符
        → 返回 ~0.85
    """
    if not short or not long:
        return 0.0
    if short in long:
        return 1.0

    # 找出所有长度 ≥ 2 的公共子串
    n = len(short)
    covered = [False] * n

    # 用集合记录 short 中所有 ≥2 字子串，在 long 中查找
    for i in range(n - 1):
        for j in range(i + 2, n + 1):
            sub = short[i:j]
            if sub in long:
                for k in range(i, j):
                    covered[k] = True

    return sum(covered) / n if n > 0 else 0.0


# ── 弱同义表达归一化（在规范化阶段应用） ──
_SYNONYM_MAP: dict[str, str] = {
    "分不清": "混淆",
    "区别不清": "混淆",
    "搞不清": "混淆",
    "弄不清": "混淆",
    "很弱": "薄弱",
    "不擅长": "薄弱",
    "不太理解": "薄弱",
    "理不清": "混淆",
}


async def _get_current_user_id(authorization: str | None = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException()
    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise UnauthorizedException("Token 无效或已过期")
    return payload["sub"]


@router.post("/session", response_model=ApiResponse[ChatSessionResponse])
async def create_session(
    body: ChatSessionCreate,
    user_id: str = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建对话会话"""
    session = ChatSession(user_id=user_id, title=body.title)
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return ApiResponse(data=ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
    ))


@router.get("/sessions", response_model=ApiResponse[list[ChatSessionResponse]])
async def list_sessions(
    user_id: str = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的会话列表"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    return ApiResponse(data=[
        ChatSessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
        ) for s in sessions
    ])


@router.get("/{session_id}/messages", response_model=ApiResponse[list[ChatMessageResponse]])
async def get_messages(
    session_id: str,
    user_id: str = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取会话消息（仅限当前用户自己的会话）"""
    # 校验会话归属
    session_result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if session is None or session.user_id != user_id:
        raise NotFoundException(resource="会话", resource_id=session_id)

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()

    return ApiResponse(data=[
        ChatMessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            content_type=m.content_type,
            metadata=m.metadata_,
            created_at=m.created_at,
        ) for m in messages
    ])


@router.delete("/sessions/{session_id}", response_model=ApiResponse[MessageResponse])
async def delete_session(
    session_id: str,
    user_id: str = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除会话（仅限当前用户自己的会话），同时删除关联消息"""
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None or session.user_id != user_id:
        raise NotFoundException(resource="会话", resource_id=session_id)

    # 手动删除关联消息（模型无 cascade）
    await db.execute(
        delete(ChatMessage).where(ChatMessage.session_id == session_id)
    )
    await db.delete(session)
    await db.commit()

    return ApiResponse(data=MessageResponse(message="会话已删除"))


@router.patch("/sessions/{session_id}", response_model=ApiResponse[ChatSessionResponse])
async def rename_session(
    session_id: str,
    body: ChatSessionRename,
    user_id: str = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """重命名会话（仅限当前用户自己的会话）"""
    title = body.title.strip()
    if not title:
        from app.core.exceptions import ValidationException
        raise ValidationException("会话名称不能为空")

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None or session.user_id != user_id:
        raise NotFoundException(resource="会话", resource_id=session_id)

    session.title = title
    from datetime import datetime
    session.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)

    return ApiResponse(data=ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
    ))


@router.post("/send", response_model=ApiResponse[ChatMessageResponse])
async def send_message(
    body: ChatMessageSend,
    user_id: str = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    发送消息 — 通过多智能体系统处理。
    根据用户意图自动路由到 profiling / content_gen / qa / path_planning / evaluation。
    """
    # 短期记忆：获取会话近期对话历史（在保存当前消息之前，避免自引用）
    conversation_context = await _get_recent_history(db, body.session_id)
    # 长期记忆：获取跨会话学习信息
    long_term_memories = await _get_long_term_memories(db, user_id)

    # 保存用户消息
    user_msg = ChatMessage(
        session_id=body.session_id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)

    # ── 调用多智能体系统 ──
    try:
        agent_result = await run_agent(
            user_input=body.content,
            user_id=user_id,
            thread_id=body.session_id,
            conversation_context=conversation_context,
            long_term_memories=long_term_memories,
        )

        agent_output = agent_result.get("agent_output", "")
        generated_resources = agent_result.get("generated_resources", [])
        profile_dims = agent_result.get("profile_dimensions", [])
        assessment_data = agent_result.get("assessment_data")
        is_complete = agent_result.get("is_complete", False)
        citations = agent_result.get("citations", [])
        retrieval_used = agent_result.get("retrieval_used", False)
        confidence = agent_result.get("confidence")

        # 构建元数据
        metadata = {
            "agent_used": agent_result.get("next_agent", "qa_agent"),
            "profile_dimensions_count": len(profile_dims),
            "profile_complete": is_complete,
            "citations": citations,
            "retrieval_used": retrieval_used,
            "confidence": confidence,
        }
        if generated_resources:
            metadata["resources"] = generated_resources
        if assessment_data:
            metadata["assessment"] = assessment_data

    except Exception as e:
        agent_output = f"抱歉，处理你的请求时出现了问题：{str(e)}\n请稍后重试。"
        metadata = {"error": str(e)}

    # 保存助手回复
    assistant_msg = ChatMessage(
        session_id=body.session_id,
        role="assistant",
        content=agent_output,
        content_type="markdown",
        metadata_=metadata,
    )
    db.add(assistant_msg)

    # 更新会话时间
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == body.session_id)
    )
    session = result.scalar_one_or_none()
    if session:
        from datetime import datetime
        session.updated_at = datetime.utcnow()

    await db.flush()
    await db.refresh(assistant_msg)

    # 异步提取长期学习记忆（失败不影响主流程）
    try:
        await _extract_and_store_learning_memories(
            db=db,
            user_id=user_id,
            user_message_id=user_msg.id,
            user_question=body.content,
            assistant_answer=agent_output,
        )
    except Exception:
        pass  # 记忆提取失败，静默跳过

    return ApiResponse(data=ChatMessageResponse(
        id=assistant_msg.id,
        session_id=assistant_msg.session_id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        content_type=assistant_msg.content_type,
        metadata=assistant_msg.metadata_,
        created_at=assistant_msg.created_at,
    ))


# ─── SSE 辅助 ───────────────────────────────────────

def _sse_event(event: str, data: dict | str) -> str:
    """构建一条 SSE 事件字符串"""
    payload = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else data
    return f"event: {event}\ndata: {payload}\n\n"


# ─── 流式 QA 接口 ───────────────────────────────────

@router.post("/send/stream")
async def send_message_stream(
    body: ChatMessageSend,
    user_id: str = Depends(_get_current_user_id),
):
    """
    SSE 流式问答 — 仅服务 QA/RAG 路径。

    事件类型:
      token — LLM 生成文本片段
      done  — 流结束，携带 citations
      error — 错误信息
    """
    from app.agents.nodes import prepare_rag_context
    from app.llm import LLMFactory

    # 使用独立 DB 会话（流式生成器生命周期超出 Depends 范围）
    db = async_session_factory()

    try:
        # 0. 短期记忆：获取会话近期对话历史（在保存当前消息之前，避免自引用）
        conversation_context = await _get_recent_history(db, body.session_id)
        # 长期记忆：获取跨会话学习信息
        long_term_memories = await _get_long_term_memories(db, user_id)

        # 1. 保存用户消息（立即提交，确保在流式生成器启动前持久化）
        user_msg = ChatMessage(
            session_id=body.session_id,
            role="user",
            content=body.content,
        )
        db.add(user_msg)
        await db.commit()
        await db.refresh(user_msg)
        user_msg_id = user_msg.id

        # 2. RAG 检索（携带会话历史 + 长期记忆一并注入 Prompt）
        ctx = await prepare_rag_context(
            body.content,
            conversation_context=conversation_context,
            long_term_memories=long_term_memories,
        )

        # 3. 检索失败 → 返回拒答 done 事件
        if not ctx["success"]:
            assistant_msg = ChatMessage(
                session_id=body.session_id,
                role="assistant",
                content=ctx["no_results_message"] or "",
                content_type="markdown",
                metadata_={
                    "citations": [],
                    "retrieval_used": False,
                    "confidence": None,
                },
            )
            db.add(assistant_msg)
            await db.commit()

            async def no_results_generator():
                yield _sse_event("done", {
                    "content": ctx["no_results_message"] or "",
                    "citations": [],
                    "retrieval_used": False,
                    "confidence": None,
                    "message_id": assistant_msg.id,
                })

            return StreamingResponse(
                no_results_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        # 4. 检索成功 → 流式 LLM
        async def stream_generator():
            collected_content = ""
            db2 = async_session_factory()
            try:
                try:
                    async for token in LLMFactory.chat_stream(ctx["llm_messages"]):
                        collected_content += token
                        yield _sse_event("token", {"content": token})
                except Exception as exc:
                    yield _sse_event("error", {"message": f"LLM 调用失败: {exc}"})
                    return

                # 构建 metadata
                metadata = {
                    "citations": ctx["citations"],
                    "retrieval_used": True,
                    "confidence": ctx["confidence"],
                }

                # 保存助手消息到 DB
                assistant_msg = ChatMessage(
                    session_id=body.session_id,
                    role="assistant",
                    content=collected_content,
                    content_type="markdown",
                    metadata_=metadata,
                )
                db2.add(assistant_msg)

                # 更新会话时间
                result = await db2.execute(
                    select(ChatSession).where(ChatSession.id == body.session_id)
                )
                session = result.scalar_one_or_none()
                if session:
                    from datetime import datetime
                    session.updated_at = datetime.utcnow()

                await db2.commit()
                await db2.refresh(assistant_msg)

                # 异步提取长期学习记忆（失败不影响 SSE 流）
                try:
                    await _extract_and_store_learning_memories(
                        db=db2,
                        user_id=user_id,
                        user_message_id=user_msg_id,
                        user_question=body.content,
                        assistant_answer=collected_content,
                    )
                except Exception:
                    pass  # 静默跳过

                yield _sse_event("done", {
                    "content": collected_content,
                    "citations": ctx["citations"],
                    "retrieval_used": True,
                    "confidence": ctx["confidence"],
                    "message_id": assistant_msg.id,
                })
            finally:
                await db2.close()

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as exc:
        await db.rollback()
        async def error_generator():
            yield _sse_event("error", {"message": str(exc)})
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    finally:
        await db.close()
