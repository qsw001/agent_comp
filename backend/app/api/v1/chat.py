"""
API — 对话路由
"""
from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, UnauthorizedException
from app.core.security import decode_access_token
from app.database import get_db
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
    """发送消息（SSE 流式待实现）"""
    # 保存用户消息
    user_msg = ChatMessage(
        session_id=body.session_id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)

    # TODO: 调用 AI Agent 生成回复
    # 目前返回占位回复
    assistant_msg = ChatMessage(
        session_id=body.session_id,
        role="assistant",
        content=f"你好！我是 AI 学习助手。我收到了你的消息：「{body.content}」。\n\n多智能体系统正在开发中，敬请期待。",
        content_type="markdown",
    )
    db.add(assistant_msg)
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
