"""
API — 学习内容 & 路径路由
"""

from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.database import get_db
from app.models import LearningContent, LearningPath
from app.schemas import ApiResponse, LearningContentResponse, LearningPathResponse

router = APIRouter()


@router.get("/content", response_model=ApiResponse[list[LearningContentResponse]])
async def list_content(
    subject: str | None = None,
    type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取学习内容列表"""
    query = select(LearningContent).order_by(LearningContent.created_at.desc())

    if subject:
        query = query.where(LearningContent.subject == subject)
    if type:
        query = query.where(LearningContent.type == type)

    result = await db.execute(query)
    contents = result.scalars().all()

    return ApiResponse(data=[
        LearningContentResponse(
            id=c.id,
            title=c.title,
            type=c.type,
            subject=c.subject,
            difficulty=c.difficulty,
            content=c.content,
            description=c.description,
            tags=c.tags,
            created_at=c.created_at,
        ) for c in contents
    ])


@router.get("/content/{content_id}", response_model=ApiResponse[LearningContentResponse])
async def get_content(content_id: str, db: AsyncSession = Depends(get_db)):
    """获取学习内容详情"""
    result = await db.execute(
        select(LearningContent).where(LearningContent.id == content_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise NotFoundException("LearningContent", content_id)

    return ApiResponse(data=LearningContentResponse(
        id=content.id,
        title=content.title,
        type=content.type,
        subject=content.subject,
        difficulty=content.difficulty,
        content=content.content,
        description=content.description,
        tags=content.tags,
        created_at=content.created_at,
    ))


@router.get("/path/{profile_id}", response_model=ApiResponse[LearningPathResponse])
async def get_learning_path(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取学习路径"""
    result = await db.execute(
        select(LearningPath)
        .where(LearningPath.profile_id == profile_id)
        .order_by(LearningPath.created_at.desc())
        .limit(1)
    )
    path = result.scalar_one_or_none()
    if not path:
        raise NotFoundException("LearningPath", profile_id)

    return ApiResponse(data=LearningPathResponse(
        id=path.id,
        profile_id=path.profile_id,
        goal=path.goal,
        nodes=path.nodes,
        progress=path.progress,
        created_at=path.created_at,
        updated_at=path.updated_at,
    ))
