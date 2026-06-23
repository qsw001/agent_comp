"""
API — 对话路由（增强版 — 集成多智能体系统）
"""

from __future__ import annotations

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import run_agent
from app.core.exceptions import NotFoundException, UnauthorizedException
from app.core.security import decode_access_token
from app.database import get_db, async_session_factory
from app.models import ChatMessage, ChatSession
from app.schemas import (
    ApiResponse,
    ChatMessageResponse,
    ChatMessageSend,
    ChatSessionCreate,
    ChatSessionResponse,
)

router = APIRouter()


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
    db: AsyncSession = Depends(get_db),
):
    """获取会话消息"""
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
        # 1. 保存用户消息
        user_msg = ChatMessage(
            session_id=body.session_id,
            role="user",
            content=body.content,
        )
        db.add(user_msg)
        await db.flush()

        # 2. RAG 检索
        ctx = await prepare_rag_context(body.content)

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
            db.add(assistant_msg)

            # 更新会话时间
            result = await db.execute(
                select(ChatSession).where(ChatSession.id == body.session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                from datetime import datetime
                session.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(assistant_msg)

            yield _sse_event("done", {
                "content": collected_content,
                "citations": ctx["citations"],
                "retrieval_used": True,
                "confidence": ctx["confidence"],
                "message_id": assistant_msg.id,
            })

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
