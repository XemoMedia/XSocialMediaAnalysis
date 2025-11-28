"""
Comment service layer.
Handles business logic for comment operations.
"""
from typing import List
from app.repositories.comment_repository import CommentRepository
from app.services.sentiment_service import SentimentService
from app.schemas.sentiment_schemas import SentimentResult, SentimentAnalysisResponse
import logging

logger = logging.getLogger(__name__)


class CommentService:
    """
    Service for comment-related business logic.
    Coordinates between repository and sentiment analysis service.
    """
    
    def __init__(self, comment_repository: CommentRepository, sentiment_service: SentimentService):
        """
        Initialize service with dependencies.
        
        Args:
            comment_repository: Repository for database operations
            sentiment_service: Service for sentiment analysis
        """
        self.comment_repository = comment_repository
        self.sentiment_service = sentiment_service
    
    def analyze_sentiment_by_ids(self, ids: List[str]) -> SentimentAnalysisResponse:
        """
        Fetch comments by IDs and perform sentiment analysis.
        
        Args:
            ids: List of comment IDs to analyze
            
        Returns:
            SentimentAnalysisResponse with analysis results
        """
        logger.info(f"Analyzing sentiment for {len(ids)} comment IDs")
        
        # Fetch comments from database
        comments = self.comment_repository.find_by_ids(ids)
        logger.info(f"Found {len(comments)} comments in database")
        
        if not comments:
            return SentimentAnalysisResponse(
                results=[],
                total_analyzed=0,
                total_requested=len(ids)
            )
        
        # Extract texts for sentiment analysis
        texts = [comment.text for comment in comments if comment.text]
        
        # Perform sentiment analysis
        sentiment_results = self.sentiment_service.analyze_multiple(texts)
        
        # Combine comment data with sentiment results
        results = []
        for i, comment in enumerate(comments):
            if i < len(sentiment_results):
                sentiment_data = sentiment_results[i]
                results.append(SentimentResult(
                    id=comment.id,
                    text=comment.text or "",
                    sentiment=sentiment_data["sentiment"],
                    polarity=sentiment_data["polarity"],
                    emotion=sentiment_data.get("emotion")
                ))
        
        logger.info(f"Successfully analyzed {len(results)} comments")
        
        return SentimentAnalysisResponse(
            results=results,
            total_analyzed=len(results),
            total_requested=len(ids)
        )

