"""
RAG — 向量数据库 Qdrant
"""

from __future__ import annotations
from typing import Optional

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

from app.config import settings
from app.rag.embeddings import embed_batch


def get_qdrant_client() -> QdrantClient:
    """获取 Qdrant 客户端"""
    return QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
    )


async def ensure_collection(
    collection_name: Optional[str] = None,
    vector_size: int = 768,
):
    """确保集合存在（不存在则创建）"""
    client = get_qdrant_client()
    name = collection_name or settings.QDRANT_COLLECTION

    collections = client.get_collections().collections
    if not any(c.name == name for c in collections):
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
        # 创建 payload 索引
        client.create_payload_index(
            collection_name=name,
            field_name="title",
            field_schema=models.TextIndexParams(
                type=models.TextIndexType.TEXT,
                tokenizer=models.TokenizerType.MULTILINGUAL,
            ),
        )


async def insert_documents(
    documents: list[dict[str, Any]],
    collection_name: Optional[str] = None,
):
    """
    插入文档到向量库

    Args:
        documents: 文档列表，每项含 id, title, content, metadata
        collection_name: 集合名
    """
    collection = collection_name or settings.QDRANT_COLLECTION
    await ensure_collection(collection)

    client = get_qdrant_client()
    texts = [doc.get("content", "") for doc in documents]
    embeddings = embed_batch(texts)

    points = [
        models.PointStruct(
            id=doc.get("id", hash(doc.get("title", ""))),
            vector=emb,
            payload={
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "type": doc.get("type", ""),
                "subject": doc.get("subject", ""),
                "difficulty": doc.get("difficulty", 3),
                "tags": doc.get("tags", []),
                "metadata": doc.get("metadata", {}),
            },
        )
        for doc, emb in zip(documents, embeddings)
    ]

    client.upsert(collection_name=collection, points=points)


async def search_similar(
    query: str,
    top_k: int = 5,
    collection_name: Optional[str] = None,
    score_threshold: float = 0.6,
    filters: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """
    语义搜索

    Args:
        query: 查询文本
        top_k: 返回数量
        collection_name: 集合名
        score_threshold: 相似度阈值
        filters: 过滤条件

    Returns:
        匹配文档列表
    """
    collection = collection_name or settings.QDRANT_COLLECTION
    client = get_qdrant_client()

    query_vector = embed_batch([query])[0]

    # 构建过滤条件
    query_filter = None
    if filters:
        must_conditions = []
        for key, value in filters.items():
            if isinstance(value, list):
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchAny(any=value),
                    )
                )
            else:
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    )
                )
        query_filter = models.Filter(must=must_conditions)

    search_result = client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=top_k,
        score_threshold=score_threshold,
        query_filter=query_filter,
    )

    return [
        {
            "id": hit.id,
            "score": hit.score,
            **hit.payload,
        }
        for hit in search_result
    ]


async def delete_collection(collection_name: Optional[str] = None):
    """删除集合"""
    client = get_qdrant_client()
    name = collection_name or settings.QDRANT_COLLECTION
    client.delete_collection(collection_name=name)
