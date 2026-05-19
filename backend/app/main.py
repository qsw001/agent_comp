"""
FastAPI 应用入口
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.v1.auth import router as auth_router
from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.core.exceptions import AppException
from app.core.redis import close_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info(f"📦 Environment: {settings.ENV}")
    yield
    await close_redis_client()
    logger.info("👋 Application shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于大模型的个性化资源生成与学习多智能体系统",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
)

# ─── CORS ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 路由 ────────────────────────────────────────────
app.include_router(api_v1_router)
app.include_router(auth_router, prefix="/auth", tags=["认证"])


# ─── 全局异常处理 ────────────────────────────────────
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求参数校验失败",
                "details": {"errors": [str(error) for error in exc.errors()]},
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
            },
        },
    )


# ─── 健康检查 ────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
    }
