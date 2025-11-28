"""
API routes for sentiment analysis endpoints.
Similar to Spring Boot controllers.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.comment_repository import CommentRepository
from app.repositories.reply_repository import ReplyRepository
from app.repositories.sentiment_analysis_repository import SentimentAnalysisRepository
from app.services.sentiment_service import SentimentService
from app.services.comment_service import CommentService
from app.schemas.sentiment_schemas import SentimentAnalysisRequest, SentimentAnalysisResponse
import logging

logger = logging.getLogger(__name__)

# Create router (similar to @RestController in Spring Boot)
router = APIRouter(prefix="/api/v1/sentiment", tags=["Sentiment Analysis"])


def get_comment_service(db: Session = Depends(get_db)) -> CommentService:
    """
    Dependency injection for CommentService.
    Similar to @Autowired in Spring Boot.
    
    Args:
        db: Database session from dependency injection
        
    Returns:
        CommentService instance
    """
    comment_repository = CommentRepository(db)
    sentiment_service = SentimentService()
    return CommentService(comment_repository, sentiment_service)


def get_reply_repository(db: Session = Depends(get_db)) -> ReplyRepository:
    """
    Dependency injection for ReplyRepository.
    Similar to @Autowired in Spring Boot.
    
    Args:
        db: Database session from dependency injection
        
    Returns:
        ReplyRepository instance
    """
    return ReplyRepository(db)


def get_sentiment_analysis_repository(db: Session = Depends(get_db)) -> SentimentAnalysisRepository:
    """
    Dependency injection for SentimentAnalysisRepository.
    
    Args:
        db: Database session from dependency injection
        
    Returns:
        SentimentAnalysisRepository instance
    """
    return SentimentAnalysisRepository(db)


@router.post("/analyze", response_model=SentimentAnalysisResponse)
async def analyze_sentiment_by_ids(
    request: SentimentAnalysisRequest,
    comment_service: CommentService = Depends(get_comment_service),
    reply_repository: ReplyRepository = Depends(get_reply_repository),
    sentiment_analysis_repository: SentimentAnalysisRepository = Depends(get_sentiment_analysis_repository)
):
    """
    Analyze sentiment for comments and replies by their IDs and save results to database.
    
    This endpoint:
    1. Receives lists of comment IDs and reply IDs
    2. Fetches the comments and replies from the database
    3. Performs sentiment analysis on each comment and reply
    4. Saves analysis results to sentiment_analysis table
    5. Returns the results with sentiment, polarity, and emotion
    
    Args:
        request: Request containing list of comment IDs and reply IDs
        comment_service: Injected CommentService
        reply_repository: Injected ReplyRepository
        sentiment_analysis_repository: Injected SentimentAnalysisRepository
        
    Returns:
        SentimentAnalysisResponse with analysis results
        
    Raises:
        HTTPException: If no IDs provided or service error occurs
    """
    try:
        total_requested = len(request.commentIds) + len(request.repliedIds)
        logger.info(f"Received sentiment analysis request for {len(request.commentIds)} comments and {len(request.repliedIds)} replies")
        
        if not request.commentIds and not request.repliedIds:
            raise HTTPException(status_code=400, detail="At least one comment ID or reply ID must be provided")
        
        # Get sentiment service instance
        sentiment_service = SentimentService()
        
        # Analyze and save results
        results = []
        saved_count = 0
        
        # Process comments
        if request.commentIds:
            # Fetch comments from database using the comment service's repository
            comments = comment_service.comment_repository.find_by_ids(request.commentIds)
            logger.info(f"Found {len(comments)} comments in database")
            
            for comment in comments:
                try:
                    # Analyze sentiment and emotion
                    analysis_result = sentiment_service.analyze_text(comment.text or "")
                    
                    # Use original comment ID as string
                    source_id = comment.id or ""
                    
                    # Save to sentiment_analysis table
                    sentiment_service.save_analysis_result(
                        repository=sentiment_analysis_repository,
                        source_id=source_id,
                        source_type="COMMENT",
                        text=comment.text or "",
                        analysis_result=analysis_result
                    )
                    saved_count += 1
                    
                    # Add to response results
                    results.append({
                        "id": comment.id,
                        "text": comment.text or "",
                        "sentiment": analysis_result.get("sentiment", "neutral"),
                        "polarity": analysis_result.get("polarity", 0.0),
                        "emotion": analysis_result.get("emotion", "neutral"),
                        "sourceType": "COMMENT"
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing comment {comment.id}: {e}", exc_info=True)
                    # Continue with next comment even if one fails
                    continue
        
        # Process replies
        if request.repliedIds:
            # Fetch replies from database using the reply repository
            replies = reply_repository.find_by_ids(request.repliedIds)
            logger.info(f"Found {len(replies)} replies in database")
            
            for reply in replies:
                try:
                    # Analyze sentiment and emotion
                    analysis_result = sentiment_service.analyze_text(reply.text or "")
                    
                    # Use original reply ID as string
                    source_id = reply.id or ""
                    
                    # Save to sentiment_analysis table
                    sentiment_service.save_analysis_result(
                        repository=sentiment_analysis_repository,
                        source_id=source_id,
                        source_type="REPLY",
                        text=reply.text or "",
                        analysis_result=analysis_result
                    )
                    saved_count += 1
                    
                    # Add to response results
                    results.append({
                        "id": reply.id,
                        "text": reply.text or "",
                        "sentiment": analysis_result.get("sentiment", "neutral"),
                        "polarity": analysis_result.get("polarity", 0.0),
                        "emotion": analysis_result.get("emotion", "neutral"),
                        "sourceType": "REPLY"
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing reply {reply.id}: {e}", exc_info=True)
                    # Continue with next reply even if one fails
                    continue
        
        logger.info(f"Successfully analyzed and saved {saved_count} out of {total_requested} items (comments + replies)")
        
        # Convert results to SentimentResult format
        from app.schemas.sentiment_schemas import SentimentResult
        sentiment_results = [
            SentimentResult(
                id=r["id"],
                text=r["text"],
                sentiment=r["sentiment"],
                polarity=r["polarity"],
                emotion=r.get("emotion"),
                sourceType=r.get("sourceType")
            )
            for r in results
        ]
        
        return SentimentAnalysisResponse(
            results=sentiment_results,
            total_analyzed=len(sentiment_results),
            total_requested=total_requested
        )
        
    except Exception as e:
        logger.error(f"Error processing sentiment analysis request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

