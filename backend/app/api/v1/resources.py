"""
API — 资源生成与获取路由
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import run_agent
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.database import get_db
from app.schemas import ApiResponse

router = APIRouter()


async def _get_current_user_id(authorization: str | None = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException()
    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise UnauthorizedException("Token 无效或已过期")
    return payload["sub"]


@router.post("/generate")
async def generate_resources(
    body: dict,
    user_id: str = Depends(_get_current_user_id),
):
    """
    多智能体协同生成个性化资源。
    请求体: { "topic": "...", "types": ["document","mindmap","quiz","reading","code"], "profile_dims": [...] }
    返回: 生成的资源列表
    """
    topic = body.get("topic", "")
    requested_types = body.get("types", [])
    profile_dims = body.get("profile_dims", [])

    # 构造触发内容生成的输入
    types_hint = "、".join(requested_types) if requested_types else "讲解、思维导图、练习题、拓展阅读、实操案例"
    input_text = f"请为我生成关于{topic}的学习资源，包括{types_hint}"

    result = await run_agent(
        user_input=input_text,
        user_id=user_id,
    )

    return ApiResponse(
        success=True,
        message=f"已生成 {len(result.get('generated_resources', []))} 个资源",
        data={
            "resources": result.get("generated_resources", []),
            "agent_output": result.get("agent_output", ""),
        },
    )


@router.get("/profile-resources")
async def get_resources_for_profile(
    topic: str,
    user_id: str = Depends(_get_current_user_id),
):
    """根据用户画像获取个性化资源推荐"""
    # 先走一遍 profiling 获取当前画像，再生成资源
    profile_result = await run_agent(
        user_input=f"我想学习{topic}，帮我分析一下我的学习特征",
        user_id=user_id,
    )

    result = await run_agent(
        user_input=f"请根据我的画像为{topic}生成全部学习资源",
        user_id=user_id,
    )

    return ApiResponse(
        success=True,
        data={
            "resources": result.get("generated_resources", []),
            "summary": result.get("agent_output", ""),
        },
    )
