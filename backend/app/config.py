"""
AI 教育平台 — 配置管理
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── 应用 ────────────────────────────────────────
    APP_NAME: str = "AI Education Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENV: Literal["development", "staging", "production"] = "development"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production", "false", "0", "no", "off"}:
                return False
            if normalized in {"debug", "dev", "development", "true", "1", "yes", "on"}:
                return True
        return value

    # ─── 数据库 ──────────────────────────────────────
    POSTGRES_USER: str = "edulab"
    POSTGRES_PASSWORD: str = "edulab_pass"
    POSTGRES_DB: str = "ai_education"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ─── Redis ────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # ─── Qdrant ───────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "learning_resources"

    @property
    def QDRANT_URL(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"

    # ─── Auth ─────────────────────────────────────────
    JWT_SECRET: str = "change-this-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # ─── SMTP ─────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_SECURE: bool = False
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = ""
    SMTP_TIMEOUT_SECONDS: int = 10

    @field_validator("SMTP_PORT", mode="before")
    @classmethod
    def parse_smtp_port(cls, value):
        if value == "":
            return 587
        return value

    @field_validator("SMTP_SECURE", mode="before")
    @classmethod
    def parse_smtp_secure(cls, value):
        if value == "":
            return False
        return value

    # ─── LLM Provider ─────────────────────────────────
    # 讯飞星火（首选）
    XUNFEI_APP_ID: str = ""
    XUNFEI_API_KEY: str = ""
    XUNFEI_API_SECRET: str = ""

    # 备选 Provider
    DEEPSEEK_API_KEY: str = ""
    QWEN_API_KEY: str = ""
    ZHIPU_API_KEY: str = ""

    # LLM 默认配置
    LLM_DEFAULT_PROVIDER: str = "xunfei"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096

    # ─── CORS ─────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


settings = Settings()
