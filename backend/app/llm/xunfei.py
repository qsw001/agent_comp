"""
LLM Provider — 讯飞星火 Spark
"""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from base64 import b64encode
from datetime import datetime, timezone
from typing import AsyncGenerator

import httpx

from app.config import settings
from app.llm.base import BaseLLM, LLMConfig, LLMResponse


class XunfeiSparkLLM(BaseLLM):
    """
    讯飞星火认知大模型

    API 文档: https://www.xfyun.cn/doc/spark/API.html
    """

    API_DOMAIN = "spark-api.xf-yun.com"
    API_VERSION = "v4.0"  # 星火 4.0

    def __init__(self):
        self.app_id = settings.XUNFEI_APP_ID
        self.api_key = settings.XUNFEI_API_KEY
        self.api_secret = settings.XUNFEI_API_SECRET

    def _build_url(self) -> str:
        """构建 WebSocket URL"""
        now = datetime.now(timezone.utc)
        date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

        # 构建签名
        signature_origin = f"host: {self.API_DOMAIN}\ndate: {date}\nGET /{self.API_VERSION}/chat HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode(),
            signature_origin.encode(),
            digestmod=hashlib.sha256,
        ).digest()
        signature = b64encode(signature_sha).decode()

        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature={signature}'
        )
        authorization = b64encode(authorization_origin.encode()).decode()

        return (
            f"wss://{self.API_DOMAIN}/{self.API_VERSION}/chat"
            f"?authorization={authorization}&date={date}&host={self.API_DOMAIN}"
        )

    def _build_messages(self, messages: list[dict]) -> list[dict]:
        """构建讯飞格式消息"""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]

    async def chat(self, messages: list[dict], config: LLMConfig | None = None) -> LLMResponse:
        cfg = config or LLMConfig()

        # HTTP 调用（星火 v4 支持 HTTP）
        url = f"https://{self.API_DOMAIN}/{self.API_VERSION}/chat"

        payload = {
            "header": {
                "app_id": self.app_id,
                "uid": str(uuid.uuid4()),
            },
            "parameter": {
                "chat": {
                    "domain": "4.0Ultra",
                    "temperature": cfg.temperature,
                    "max_tokens": cfg.max_tokens,
                    "top_k": 4,
                }
            },
            "payload": {
                "message": {
                    "text": self._build_messages(messages),
                }
            },
        }

        # 构建鉴权 Header
        now = datetime.now(timezone.utc)
        date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
        signature = self._build_authorization("POST", url, date)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": signature,
                    "Content-Type": "application/json",
                    "Date": date,
                },
                timeout=60,
            )
            result = response.json()

        if result.get("header", {}).get("code") != 0:
            error_msg = result.get("header", {}).get("message", "Unknown error")
            raise RuntimeError(f"讯飞 API 调用失败: {error_msg}")

        text = result.get("payload", {}).get("choices", {}).get("text", [])
        content = "".join(item.get("content", "") for item in text)

        return LLMResponse(
            content=content,
            usage=result.get("payload", {}).get("usage", {}),
            raw=result,
        )

    async def chat_stream(
        self, messages: list[dict], config: LLMConfig | None = None
    ) -> AsyncGenerator[str, None]:
        """讯飞流式响应用于 SSE"""
        # 使用 WebSocket 实现流式
        # 为简化目前返回 HTTP 单次结果（实际应用应使用 ws）
        result = await self.chat(messages, config)
        yield result.content

    def _build_authorization(self, method: str, url: str, date: str) -> str:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        signature_origin = f"host: {parsed.hostname}\ndate: {date}\n{method} /{self.API_VERSION}/chat HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode(),
            signature_origin.encode(),
            digestmod=hashlib.sha256,
        ).digest()
        signature = b64encode(signature_sha).decode()

        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature={signature}'
        )
        return b64encode(authorization_origin.encode()).decode()
