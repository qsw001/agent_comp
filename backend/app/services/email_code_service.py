"""
业务服务层 — 邮箱验证码
"""
from __future__ import annotations

import secrets

from redis.exceptions import RedisError

from app.core.exceptions import AppException, ValidationException
from app.core.redis import get_redis_client
from app.services.email_service import send_email_code

EMAIL_CODE_TTL_SECONDS = 5 * 60
EMAIL_CODE_SEND_INTERVAL_SECONDS = 60


def normalize_email(email: str) -> str:
    return email.strip().lower()


def generate_email_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _code_key(email: str) -> str:
    return f"email_code:{email}"


def _rate_limit_key(email: str) -> str:
    return f"email_code_rate:{email}"


async def create_and_send_email_code(email: str) -> None:
    """生成、保存并发送邮箱验证码。"""
    normalized_email = normalize_email(email)
    redis = get_redis_client()
    rate_limit_key = _rate_limit_key(normalized_email)
    code_key = _code_key(normalized_email)

    try:
        can_send = await redis.set(
            rate_limit_key,
            "1",
            ex=EMAIL_CODE_SEND_INTERVAL_SECONDS,
            nx=True,
        )
        if not can_send:
            raise ValidationException("同一邮箱 60 秒内不能重复发送验证码")

        code = generate_email_code()
        await redis.set(code_key, code, ex=EMAIL_CODE_TTL_SECONDS)
    except RedisError as exc:
        raise AppException(
            status_code=503,
            code="VERIFICATION_CODE_STORE_ERROR",
            message="验证码服务暂不可用，请稍后再试",
        ) from exc

    try:
        await send_email_code(normalized_email, code)
    except Exception:
        try:
            await redis.delete(code_key, rate_limit_key)
        except RedisError:
            pass
        raise


async def verify_email_code(email: str, code: str) -> None:
    """校验邮箱验证码，成功后立即删除。"""
    normalized_email = normalize_email(email)
    redis = get_redis_client()
    code_key = _code_key(normalized_email)

    try:
        stored_code = await redis.get(code_key)
    except RedisError as exc:
        raise AppException(
            status_code=503,
            code="VERIFICATION_CODE_STORE_ERROR",
            message="验证码服务暂不可用，请稍后再试",
        ) from exc

    if stored_code is None:
        raise ValidationException("验证码已过期")
    if not secrets.compare_digest(stored_code, code):
        raise ValidationException("验证码错误")

    try:
        await redis.delete(code_key)
    except RedisError as exc:
        raise AppException(
            status_code=503,
            code="VERIFICATION_CODE_STORE_ERROR",
            message="验证码服务暂不可用，请稍后再试",
        ) from exc
