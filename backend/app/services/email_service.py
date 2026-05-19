"""
业务服务层 — 邮件发送
"""
from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from app.config import settings
from app.core.exceptions import AppException


def _validate_smtp_settings() -> None:
    missing: list[str] = []
    if not settings.SMTP_HOST:
        missing.append("SMTP_HOST")
    if not settings.SMTP_FROM:
        missing.append("SMTP_FROM")
    if bool(settings.SMTP_USER) != bool(settings.SMTP_PASS):
        missing.append("SMTP_USER/SMTP_PASS")

    if missing:
        raise AppException(
            status_code=500,
            code="EMAIL_CONFIG_ERROR",
            message=f"邮件服务未配置，请检查 {', '.join(missing)}",
        )


def _send_email_code_sync(to_email: str, code: str) -> None:
    _validate_smtp_settings()

    message = EmailMessage()
    message["Subject"] = "邮箱验证码"
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message.set_content(
        f"你的验证码是：{code}\n验证码 5 分钟内有效，请勿泄露给他人。"
    )

    if settings.SMTP_SECURE:
        with smtplib.SMTP_SSL(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=settings.SMTP_TIMEOUT_SECONDS,
        ) as server:
            if settings.SMTP_USER and settings.SMTP_PASS:
                server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.send_message(message)
        return

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=settings.SMTP_TIMEOUT_SECONDS,
    ) as server:
        server.ehlo()
        if server.has_extn("starttls"):
            server.starttls()
            server.ehlo()
        if settings.SMTP_USER and settings.SMTP_PASS:
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.send_message(message)


async def send_email_code(to_email: str, code: str) -> None:
    """发送邮箱验证码。"""
    try:
        await asyncio.to_thread(_send_email_code_sync, to_email, code)
    except AppException:
        raise
    except smtplib.SMTPException as exc:
        raise AppException(
            status_code=502,
            code="EMAIL_SEND_ERROR",
            message="验证码邮件发送失败，请稍后再试",
        ) from exc
    except OSError as exc:
        raise AppException(
            status_code=502,
            code="EMAIL_SEND_ERROR",
            message="验证码邮件发送失败，请稍后再试",
        ) from exc
