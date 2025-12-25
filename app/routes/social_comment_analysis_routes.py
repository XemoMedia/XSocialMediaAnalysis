"""
Routes for analyzing uploaded social comment data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.social_comment_analysis_repository import SocialCommentAnalysisRepository
from app.repositories.media_analysis_analytic_repository import MediaAnalysisAnalyticRepository
from app.schemas.social_comment_analysis_schemas import SocialCommentAnalysisResponse
from app.services.sentiment_service import SentimentService
from app.services.social_comment_analysis_service import SocialCommentAnalysisService
from app.services.insight_llm_service import InsightLLMService

router = APIRouter(prefix="/api/v1/social-comment-analysis", tags=["Social Comment Analysis"])


def get_social_comment_analysis_service(
    db: Session = Depends(get_db),
) -> SocialCommentAnalysisService:
    repository = SocialCommentAnalysisRepository(db)
    sentiment_service = SentimentService()
    media_repository = MediaAnalysisAnalyticRepository(db)
    insight_service = InsightLLMService()
    return SocialCommentAnalysisService(repository, media_repository, sentiment_service, insight_service)


@router.get("", response_model=SocialCommentAnalysisResponse)
async def analyze_social_comments(
    service: SocialCommentAnalysisService = Depends(get_social_comment_analysis_service),
) -> SocialCommentAnalysisResponse:
    """
    Fetch social_comment_analysis rows and enrich them with sentiment/emotion/intent metrics.
    """
    try:
        return service.analyze_social_comments()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

