"""
数据库模型 — 学习者画像
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class LearnerProfile(Base):
    """学习者画像"""
    __tablename__ = "learner_profiles"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSON 存储画像维度 { "knowledge": 65, "cognitive": 78, ... }
    dimensions: Mapped[dict] = mapped_column(JSONB, default=dict)

    # 画像构建状态
    status: Mapped[str] = mapped_column(
        String(32), default="building", comment="building | completed"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联
    user = relationship("User", back_populates="profile")
    learning_paths = relationship("LearningPath", back_populates="profile")
    evaluations = relationship("Evaluation", back_populates="profile")

    def __repr__(self) -> str:
        return f"<LearnerProfile {self.name}>"
