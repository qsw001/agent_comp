"""
业务服务层 — RAG 检索服务
"""
from __future__ import annotations

from app.rag.embeddings import embed_text
from app.rag.retriever import retrieve_context, build_rag_prompt
from app.rag.vector_store import insert_documents, search_similar

__all__ = [
    "embed_text",
    "retrieve_context",
    "build_rag_prompt",
    "insert_documents",
    "search_similar",
]
