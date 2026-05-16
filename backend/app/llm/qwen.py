"""
LLM Provider — 通义千问 Qwen
"""
from __future__ import annotations

from typing import AsyncGenerator

import httpx

from app.config import settings
from app.llm.base import BaseLLM, LLMConfig, LLMResponse


class QwenLLM(BaseLLM):
    """
    通义千问 API 封装

    API 文档: https://help.aliyun.com/zh/model-studio/
    """

    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    MODEL = "qwen-plus"

    def __init__(self):
        self.api_key = settings.QWEN_API_KEY

    async def chat(self, messages: list[dict], config: LLMConfig | None = None) -> LLMResponse:
        cfg = config or LLMConfig()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.MODEL,
                    "messages": messages,
                    "temperature": cfg.temperature,
                    "max_tokens": cfg.max_tokens,
                },
                timeout=60,
            )
            result = response.json()

        return LLMResponse(
            content=result["choices"][0]["message"]["content"],
            usage=result.get("usage"),
            raw=result,
        )

    async def chat_stream(
        self, messages: list[dict], config: LLMConfig | None = None
    ) -> AsyncGenerator[str, None]:
        cfg = config or LLMConfig()

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.MODEL,
                    "messages": messages,
                    "temperature": cfg.temperature,
                    "max_tokens": cfg.max_tokens,
                    "stream": True,
                },
                timeout=120,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        import json
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
