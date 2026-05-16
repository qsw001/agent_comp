"""
API — 评估路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.database import get_db
from app.models import Evaluation, LearnerProfile
from app.schemas import (
    ApiResponse,
    EvaluationResponse,
    EvaluationSubmit,
    LearningProgressResponse,
)

router = APIRouter()


@router.post("/submit", response_model=ApiResponse[EvaluationResponse])
async def submit_evaluation(
    body: EvaluationSubmit,
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """提交学习评估"""
    eval_ = Evaluation(
        profile_id=profile_id,
        content_id=body.content_id,
        score=body.score,
        feedback=body.feedback,
    )
    db.add(eval_)
    await db.flush()
    await db.refresh(eval_)

    return ApiResponse(data=EvaluationResponse(
        id=eval_.id,
        profile_id=eval_.profile_id,
        content_id=eval_.content_id,
        score=eval_.score,
        feedback=eval_.feedback,
        submitted_at=eval_.submitted_at,
    ))


@router.get("/progress/{profile_id}", response_model=ApiResponse[LearningProgressResponse])
async def get_progress(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取学习进度"""
    from app.models import LearningContent

    # 获取该画像的所有评估记录
    eval_result = await db.execute(
        select(Evaluation).where(Evaluation.profile_id == profile_id)
    )
    evaluations = eval_result.scalars().all()

    # 内容总数（简单取评估内容的去重数）
    total_result = await db.execute(select(LearningContent))
    total_contents = len(total_result.scalars().all())

    completed = len(set(e.content_id for e in evaluations))
    avg_score = sum(e.score for e in evaluations) / len(evaluations) if evaluations else 0

    return ApiResponse(data=LearningProgressResponse(
        profile_id=profile_id,
        total_contents=total_contents,
        completed_contents=completed,
        average_score=round(avg_score, 1),
        time_spent_minutes=0,
        strengths=["基础知识扎实", "逻辑思维能力强"],
        weaknesses=["需要加强实践应用", "复杂问题拆解能力有待提升"],
        recommendations=["增加项目实战任务", "推荐参加编程竞赛训练"],
    ))
