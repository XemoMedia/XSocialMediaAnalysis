"""
Repository layer for sentiment analysis database operations.
Follows repository pattern similar to Spring Boot.
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.sentiment_analysis_model import SentimentAnalysis
import uuid


class SentimentAnalysisRepository:
    """
    Repository for sentiment analysis database operations.
    Handles all database queries related to sentiment analysis records.
    """
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def save(self, sentiment_analysis: SentimentAnalysis) -> SentimentAnalysis:
        """
        Save a sentiment analysis record to the database.
        
        Args:
            sentiment_analysis: SentimentAnalysis entity to save
            
        Returns:
            Saved SentimentAnalysis entity with generated ID
        """
        try:
            # Generate UUID if not provided
            if not sentiment_analysis.id:
                sentiment_analysis.id = str(uuid.uuid4())
            
            self.db.add(sentiment_analysis)
            self.db.commit()
            self.db.refresh(sentiment_analysis)
            return sentiment_analysis
        except Exception as e:
            # Rollback on error
            self.db.rollback()
            raise
    
    def find_by_id(self, analysis_id: str) -> Optional[SentimentAnalysis]:
        """
        Find a sentiment analysis record by ID.
        
        Args:
            analysis_id: Sentiment analysis ID
            
        Returns:
            SentimentAnalysis entity or None if not found
        """
        return self.db.query(SentimentAnalysis).filter(SentimentAnalysis.id == analysis_id).first()
    
    def find_by_source(self, source_id: str, source_type: str) -> List[SentimentAnalysis]:
        """
        Find sentiment analysis records by source ID and type.
        
        Args:
            source_id: Source ID (Post, Comment, or Reply ID) as string
            source_type: Source type (POST, COMMENT, REPLY)
            
        Returns:
            List of SentimentAnalysis entities
        """
        return self.db.query(SentimentAnalysis).filter(
            SentimentAnalysis.source_id == source_id,
            SentimentAnalysis.source_type == source_type
        ).all()
    
    def find_all(self, limit: Optional[int] = None) -> List[SentimentAnalysis]:
        """
        Find all sentiment analysis records with optional limit.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of SentimentAnalysis entities
        """
        query = self.db.query(SentimentAnalysis).order_by(SentimentAnalysis.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

