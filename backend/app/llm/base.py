"""
LLM Provider — 基础抽象类
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """LLM 配置"""
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    stream: bool = False
    extra_params: dict = field(default_factory=dict)


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    finish_reason: str = "stop"
    usage: dict | None = None
    raw: dict | None = None


class BaseLLM(ABC):
    """LLM Provider 基类"""

    @abstractmethod
    async def chat(self, messages: list[dict], config: LLMConfig | None = None) -> LLMResponse:
        """
        对话补全

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            config: LLM 调用配置

        Returns:
            LLMResponse
        """
        ...

    @abstractmethod
    async def chat_stream(
        self, messages: list[dict], config: LLMConfig | None = None
    ):
        """
        流式对话补全（异步生成器）

        Args:
            messages: 消息列表
            config: LLM 调用配置

        Yields:
            文本片段
        """
        ...
        yield ""  # placeholder
