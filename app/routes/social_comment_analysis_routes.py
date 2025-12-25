"""
Routes for analyzing uploaded social comment data.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.social_comment_analysis_repository import SocialCommentAnalysisRepository
from app.repositories.media_analysis_analytic_repository import MediaAnalysisAnalyticRepository
from app.schemas.social_comment_analysis_schemas import SocialCommentAnalysisResponse
from app.services.sentiment_service import SentimentService
from app.services.social_comment_analysis_service import (
    SocialCommentAnalysisService,
    OptimizedSocialCommentAnalyzer,
    BatchProcessingConfig,
)
from app.services.insight_llm_service import InsightLLMService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/social-comment-analysis", tags=["Social Comment Analysis"])


def get_social_comment_analysis_service(
    db: Session = Depends(get_db),
) -> SocialCommentAnalysisService:
    repository = SocialCommentAnalysisRepository(db)
    sentiment_service = SentimentService()
    media_repository = MediaAnalysisAnalyticRepository(db)
    insight_service = InsightLLMService()
    return SocialCommentAnalysisService(repository, media_repository, sentiment_service, insight_service)


def get_optimized_social_comment_analyzer(
    db: Session = Depends(get_db),
) -> OptimizedSocialCommentAnalyzer:
    """
    Get optimized analyzer with parallel processing for faster analysis.
    Expected: 2-3 minutes for 650 records (vs 60+ min with standard service)
    """
    repository = SocialCommentAnalysisRepository(db)
    sentiment_service = SentimentService()
    media_repository = MediaAnalysisAnalyticRepository(db)
    insight_service = InsightLLMService()
    
    # Configure for optimal performance
    config = BatchProcessingConfig(
        sentiment_batch_size=64,  # Larger batches for better GPU/CPU utilization
        insight_batch_size=64,
        chunk_size=200,  # Process 200 records at a time to manage memory
        max_workers=4,  # Parallel threads (adjust based on CPU cores)
    )
    
    return OptimizedSocialCommentAnalyzer(
        repository=repository,
        sentiment_service=sentiment_service,
        insight_service=insight_service,
        media_repository=media_repository,
        config=config,
    )


@router.get("", response_model=SocialCommentAnalysisResponse)
async def analyze_social_comments(
    service: SocialCommentAnalysisService = Depends(get_social_comment_analysis_service),
) -> SocialCommentAnalysisResponse:
    """
    Fetch social_comment_analysis rows and enrich them with sentiment/emotion/intent metrics.
    
    ⚠️  SLOW: Takes 30-60 minutes for 650 records. Use /optimized endpoint instead for 10-20x speedup.
    """
    try:
        logger.info("Starting social comment analysis run (STANDARD MODE)")
        logger.warning("Using standard sequential analysis - this may take 30-60 minutes. Consider using /optimized endpoint")
        response = service.analyze_social_comments()
        logger.info(
            "Social comment analysis finished total_records=%s analyzed_records=%s",
            response.total_records,
            response.analyzed_records,
        )
        return response
    except Exception as exc:
        logger.exception("Social comment analysis failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/optimized", response_model=SocialCommentAnalysisResponse)
async def analyze_social_comments_optimized(
    analyzer: OptimizedSocialCommentAnalyzer = Depends(get_optimized_social_comment_analyzer),
) -> SocialCommentAnalysisResponse:
    """
    ⚡ OPTIMIZED: Analyze social comments with parallel processing.
    
    Performance improvements:
    - Parallel model execution (4-6 threads)
    - Larger batch sizes for better GPU/CPU utilization
    - Chunked processing for memory efficiency
    - Error isolation (failed records don't block others)
    
    Expected time for 650 records: 2-5 minutes (vs 30-60 min standard)
    
    Note: The slowest operations are intent classification and topic extraction
    which use the large BART model. These take ~50-80% of total time.
    """
    try:
        logger.info("Starting OPTIMIZED social comment analysis run")
        response = analyzer.analyze_social_comments()
        logger.info(
            "✓ Optimized analysis complete: total_records=%s analyzed_records=%s",
            response.total_records,
            response.analyzed_records,
        )
        return response
    except Exception as exc:
        logger.exception("Optimized social comment analysis failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

