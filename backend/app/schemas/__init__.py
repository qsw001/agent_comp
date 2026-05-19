"""
Pydantic Schema — API 请求/响应模型
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ─── 通用 ────────────────────────────────────────────

class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应"""
    success: bool = True
    data: Optional[T] = None
    error: Optional[ApiError] = None
    meta: Optional[PaginationMeta] = None


class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, list[str]]] = None


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class MessageResponse(BaseModel):
    message: str


# ─── Auth ────────────────────────────────────────────

def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("邮箱格式不合法")
    return email


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class EmailCodeSendRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class EmailCodeVerifyRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    code: str = Field(pattern=r"^\d{6}$")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    created_at: datetime


# ─── 画像 ────────────────────────────────────────────

class DimensionData(BaseModel):
    name: str
    value: float = Field(ge=0, le=100)
    label: str
    description: Optional[str] = None


class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    dimensions: list[DimensionData] = Field(min_length=6)


class ProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    summary: Optional[str]
    dimensions: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime


# ─── 对话 ────────────────────────────────────────────

class ChatSessionCreate(BaseModel):
    title: str = "新会话"


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageSend(BaseModel):
    session_id: str
    content: str


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    content_type: str
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime


# ─── 学习内容 ────────────────────────────────────────

class LearningContentResponse(BaseModel):
    id: str
    title: str
    type: str
    subject: str
    difficulty: int
    content: str
    description: Optional[str]
    tags: list[str]
    created_at: datetime


class LearningPathResponse(BaseModel):
    id: str
    profile_id: str
    goal: str
    nodes: list[dict[str, Any]]
    progress: float
    created_at: datetime
    updated_at: datetime


class EvaluationSubmit(BaseModel):
    content_id: str
    score: float = Field(ge=0, le=100)
    feedback: Optional[str] = None


class EvaluationResponse(BaseModel):
    id: str
    profile_id: str
    content_id: str
    score: float
    feedback: Optional[str]
    submitted_at: datetime


class LearningProgressResponse(BaseModel):
    profile_id: str
    total_contents: int
    completed_contents: int
    average_score: float
    time_spent_minutes: int
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
