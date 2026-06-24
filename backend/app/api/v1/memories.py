"""
API — 长期学习记忆查询与删除
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.chat import _get_current_user_id
from app.core.exceptions import NotFoundException, UnauthorizedException
from app.database import get_db
from app.models.user_memory import UserMemory, VALID_MEMORY_TYPES
from app.schemas import ApiResponse, MemoryResponse, MessageResponse

router = APIRouter()


_VALID_TYPES_TUPLE = tuple(sorted(VALID_MEMORY_TYPES))


@router.get("", response_model=ApiResponse[list[MemoryResponse]])
async def list_memories(
    user_id: str = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
    memory_type: str | None = Query(
        default=None,
        description=f"按记忆类型过滤，可选: {', '.join(_VALID_TYPES_TUPLE)}",
    ),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """查询当前用户的长期学习记忆，按 importance 和更新时间降序排列"""
    if memory_type is not None and memory_type not in VALID_MEMORY_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"无效的 memory_type: {memory_type}，可选值为 {', '.join(_VALID_TYPES_TUPLE)}",
        )

    stmt = (
        select(UserMemory)
        .where(UserMemory.user_id == user_id)
    )
    if memory_type is not None:
        stmt = stmt.where(UserMemory.memory_type == memory_type)

    stmt = stmt.order_by(
        UserMemory.importance.desc(),
        UserMemory.updated_at.desc(),
    ).offset(offset).limit(limit)

    result = await db.execute(stmt)
    memories = result.scalars().all()

    return ApiResponse(data=[
        MemoryResponse(
            id=m.id,
            memory_type=m.memory_type,
            content=m.content,
            importance=m.importance,
            source_message_id=m.source_message_id,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in memories
    ])


@router.delete("/{memory_id}", response_model=ApiResponse[MessageResponse])
async def delete_memory(
    memory_id: str,
    user_id: str = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除当前用户的一条长期学习记忆"""
    result = await db.execute(
        select(UserMemory).where(UserMemory.id == memory_id)
    )
    memory = result.scalar_one_or_none()

    if memory is None or memory.user_id != user_id:
        raise NotFoundException(resource="记忆", resource_id=memory_id)

    await db.delete(memory)
    await db.commit()

    return ApiResponse(data=MessageResponse(message="记忆已删除"))
