"""
Pydantic Schema — API 请求/响应模型
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ─── 通用 ────────────────────────────────────────────

class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应"""
    success: bool = True
    data: T | None = None
    error: ApiError | None = None
    meta: PaginationMeta | None = None


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, list[str]] | None = None


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ─── Auth ────────────────────────────────────────────

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
    description: str | None = None


class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    dimensions: list[DimensionData] = Field(min_length=6)


class ProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    summary: str | None
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
    metadata: dict[str, Any] | None = None
    created_at: datetime


# ─── 学习内容 ────────────────────────────────────────

class LearningContentResponse(BaseModel):
    id: str
    title: str
    type: str
    subject: str
    difficulty: int
    content: str
    description: str | None
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
    feedback: str | None = None


class EvaluationResponse(BaseModel):
    id: str
    profile_id: str
    content_id: str
    score: float
    feedback: str | None
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
