"""
API v1 — 路由聚合
"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.profile import router as profile_router
from app.api.v1.chat import router as chat_router
from app.api.v1.learning import router as learning_router
from app.api.v1.evaluation import router as evaluation_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router, prefix="/auth", tags=["认证"])
router.include_router(profile_router, prefix="/profile", tags=["画像"])
router.include_router(chat_router, prefix="/chat", tags=["对话"])
router.include_router(learning_router, prefix="/learning", tags=["学习"])
router.include_router(evaluation_router, prefix="/evaluation", tags=["评估"])
