"""
API — 画像路由
"""

from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, UnauthorizedException
from app.core.security import decode_access_token
from app.database import get_db
from app.models import LearnerProfile, User
from app.schemas import ApiResponse, DimensionData, ProfileCreate, ProfileResponse

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


@router.post("/create", response_model=ApiResponse[ProfileResponse])
async def create_profile(
    body: ProfileCreate,
    user_id: str = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建学习者画像"""
    # 检查是否已存在
    existing = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        return ApiResponse(
            success=False,
            error={"code": "ALREADY_EXISTS", "message": "画像已存在"},
        )

    dimensions_dict = {d.name: {"value": d.value, "label": d.label, "description": d.description} for d in body.dimensions}

    profile = LearnerProfile(
        user_id=user_id,
        name=body.name,
        dimensions=dimensions_dict,
        status="completed",
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)

    return ApiResponse(data=ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        summary=profile.summary,
        dimensions=profile.dimensions,
        status=profile.status,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    ))


@router.get("/{profile_id}", response_model=ApiResponse[ProfileResponse])
async def get_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取画像详情"""
    result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise NotFoundException("Profile", profile_id)

    return ApiResponse(data=ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        summary=profile.summary,
        dimensions=profile.dimensions,
        status=profile.status,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    ))


@router.get("/me", response_model=ApiResponse[ProfileResponse])
async def get_my_profile(
    user_id: str = Depends(_get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的画像"""
    result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise NotFoundException("Profile", user_id)

    return ApiResponse(data=ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        summary=profile.summary,
        dimensions=profile.dimensions,
        status=profile.status,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    ))
