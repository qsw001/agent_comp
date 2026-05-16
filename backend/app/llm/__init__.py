"""
LLM Provider — 统一工厂 & 注册中心
"""
from __future__ import annotations

from functools import lru_cache
from typing import AsyncGenerator

from app.config import settings
from app.llm.base import BaseLLM, LLMConfig, LLMResponse


class LLMFactory:
    """LLM Provider 工厂，支持按名称获取和自动 fallback"""

    _providers: dict[str, type[BaseLLM]] = {}
    _instances: dict[str, BaseLLM] = {}

    @classmethod
    def register(cls, name: str, provider_cls: type[BaseLLM]):
        """注册 Provider"""
        cls._providers[name] = provider_cls

    @classmethod
    def get_provider(cls, name: str | None = None) -> BaseLLM:
        """获取 Provider 实例（带缓存）"""
        name = name or settings.LLM_DEFAULT_PROVIDER

        if name not in cls._providers:
            raise ValueError(f"Unknown LLM provider: {name}")

        if name not in cls._instances:
            cls._instances[name] = cls._providers[name]()

        return cls._instances[name]

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """获取所有已注册 Provider 名称"""
        return list(cls._providers.keys())

    @classmethod
    async def chat(
        cls,
        messages: list[dict],
        provider: str | None = None,
        config: LLMConfig | None = None,
    ) -> LLMResponse:
        """对话补全（首选 Provider 失败时自动 fallback）"""
        providers_to_try = cls._get_providers_in_order(provider)

        last_error = None
        for p_name in providers_to_try:
            try:
                instance = cls.get_provider(p_name)
                return await instance.chat(messages, config)
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    @classmethod
    async def chat_stream(
        cls,
        messages: list[dict],
        provider: str | None = None,
        config: LLMConfig | None = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话补全"""
        instance = cls.get_provider(provider)
        async for chunk in instance.chat_stream(messages, config):
            yield chunk

    @classmethod
    def _get_providers_in_order(cls, preferred: str | None = None) -> list[str]:
        """获取尝试顺序（首选 + fallback）"""
        if not settings.ENV == "development":
            # 生产环境只尝试已配置的
            configured = []
            for p_name, p_cls in cls._providers.items():
                if _is_provider_configured(p_name):
                    configured.append(p_name)

            if preferred and preferred in configured:
                configured.remove(preferred)
                return [preferred] + configured
            return configured

        # 开发环境全部试
        all_providers = list(cls._providers.keys())
        if preferred and preferred in all_providers:
            all_providers.remove(preferred)
            return [preferred] + all_providers
        return all_providers


def _is_provider_configured(name: str) -> bool:
    """检查 Provider 的 API Key 是否已配置"""
    key_map = {
        "xunfei": settings.XUNFEI_API_KEY,
        "deepseek": settings.DEEPSEEK_API_KEY,
        "qwen": settings.QWEN_API_KEY,
        "zhipu": settings.ZHIPU_API_KEY,
    }
    return bool(key_map.get(name, ""))


# ─── 注册所有 Provider ─────────────────────────────

def register_all_providers():
    """注册所有 LLM Provider"""
    from app.llm.xunfei import XunfeiSparkLLM
    from app.llm.deepseek import DeepSeekLLM
    from app.llm.qwen import QwenLLM
    from app.llm.zhipu import ZhipuLLM

    LLMFactory.register("xunfei", XunfeiSparkLLM)
    LLMFactory.register("deepseek", DeepSeekLLM)
    LLMFactory.register("qwen", QwenLLM)
    LLMFactory.register("zhipu", ZhipuLLM)


# 默认注册
register_all_providers()
