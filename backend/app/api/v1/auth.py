"""
API — 认证路由
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.exceptions import UnauthorizedException, ValidationException
from app.database import get_db
from app.models import User
from app.schemas import (
    ApiResponse,
    EmailCodeSendRequest,
    EmailCodeVerifyRequest,
    LoginRequest,
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.email_code_service import (
    create_and_send_email_code,
    verify_email_code,
)

router = APIRouter()


# ─── 开发环境：免密码测试登录 ──────────────────────

class DevLoginRequest(BaseModel):
    username: str


@router.post("/dev-login", response_model=ApiResponse[TokenResponse])
async def dev_login(body: DevLoginRequest, db: AsyncSession = Depends(get_db)):
    """开发环境测试登录 — 跳过密码验证，仅限 ENV=development"""
    if settings.ENV != "development":
        raise UnauthorizedException("dev-login 仅在开发环境可用")

    identifier = body.username.strip()
    result = await db.execute(
        select(User).where(
            (User.username == identifier) | (User.email == identifier.lower())
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException("用户不存在")
    if not user.is_active:
        raise UnauthorizedException("账号已被禁用")

    token = create_access_token(sub=user.id)

    return ApiResponse(data=TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRATION_HOURS,
    ))


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/send-email-code", response_model=ApiResponse[MessageResponse])
async def send_email_code(body: EmailCodeSendRequest):
    """发送邮箱验证码"""
    await create_and_send_email_code(body.email)
    return ApiResponse(data=MessageResponse(message="验证码已发送"))


@router.post("/verify-email-code", response_model=ApiResponse[MessageResponse])
async def verify_email_code_route(body: EmailCodeVerifyRequest):
    """校验邮箱验证码"""
    await verify_email_code(body.email, body.code)
    return ApiResponse(data=MessageResponse(message="验证成功"))


@router.post("/register", response_model=ApiResponse[UserResponse])
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    username = body.username.strip()
    email = body.email.strip().lower()

    if not username:
        raise ValidationException("用户名不能为空")
    if not email:
        raise ValidationException("邮箱不能为空")

    result = await db.execute(
        select(User).where(
            (User.username == username) | (User.email == email)
        )
    )
    if result.scalar_one_or_none():
        raise ValidationException("用户名或邮箱已被注册")

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return ApiResponse(data=_to_user_response(user))


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    identifier = body.username.strip()
    result = await db.execute(
        select(User).where(
            (User.username == identifier) | (User.email == identifier.lower())
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise UnauthorizedException("用户名或密码错误")
    if not user.is_active:
        raise UnauthorizedException("账号已被禁用")

    token = create_access_token(sub=user.id)

    return ApiResponse(data=TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRATION_HOURS,
    ))


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户信息"""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise UnauthorizedException("Token 无效或已过期")

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException("用户不存在")
    if not user.is_active:
        raise UnauthorizedException("账号已被禁用")

    return ApiResponse(data=_to_user_response(user))
