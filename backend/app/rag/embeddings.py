"""
RAG — Embedding 模型
"""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer


# 默认 Embedding 模型
# 支持中文 + 英文，768 维
DEFAULT_MODEL = "BAAI/bge-large-zh-v1.5"


@lru_cache(maxsize=1)
def get_embedding_model(model_name: str = DEFAULT_MODEL) -> SentenceTransformer:
    """获取（缓存）Embedding 模型"""
    return SentenceTransformer(model_name)


def embed_text(text: str, model_name: str = DEFAULT_MODEL) -> list[float]:
    """对单段文本生成 Embedding"""
    model = get_embedding_model(model_name)
    return model.encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str], model_name: str = DEFAULT_MODEL) -> list[list[float]]:
    """对批量文本生成 Embedding"""
    model = get_embedding_model(model_name)
    embeddings = model.encode(texts, normalize_embeddings=True)
    return [emb.tolist() for emb in embeddings]
