"""
业务服务层导出
"""
from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS = {
    "process_chat_message": ("app.services.agent_service", "process_chat_message"),
    "embed_text": ("app.services.rag_service", "embed_text"),
    "retrieve_context": ("app.services.rag_service", "retrieve_context"),
    "build_rag_prompt": ("app.services.rag_service", "build_rag_prompt"),
    "insert_documents": ("app.services.rag_service", "insert_documents"),
    "search_similar": ("app.services.rag_service", "search_similar"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attribute_name = _EXPORTS[name]
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
