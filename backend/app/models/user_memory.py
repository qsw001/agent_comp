"""
数据库模型 — 长期学习记忆（跨会话持久化）
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# 允许的 memory_type 值
VALID_MEMORY_TYPES = frozenset({
    "learning_goal",        # 学习目标
    "knowledge_level",      # 知识点掌握程度
    "weak_point",           # 薄弱环节 / 易错点
    "learning_preference",  # 学习偏好 / 风格
    "course_context",       # 课程进度 / 上下文
    "personal_fact",        # 与学习相关的个人事实
})


class UserMemory(Base):
    """跨会话长期学习记忆"""
    __tablename__ = "user_memories"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    memory_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="learning_goal | knowledge_level | weak_point | "
                "learning_preference | course_context | personal_fact",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="记忆正文，用自然语言描述",
    )
    importance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
        comment="重要性 0.0 ~ 1.0，用于筛选排序",
    )
    source_message_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("chat_messages.id"),
        nullable=True,
        comment="产生该记忆的原始消息 ID",
    )
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        comment="扩展字段（topic / confidence / expires_at 等）",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<UserMemory {self.memory_type}: {self.content[:40]}>"
