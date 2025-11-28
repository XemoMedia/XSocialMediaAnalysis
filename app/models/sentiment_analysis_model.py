"""
Sentiment analysis model representing the sentiment_analysis table in the database.
"""
from sqlalchemy import Column, String, Text, DateTime, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base
import uuid


class SentimentAnalysis(Base):
    """
    Sentiment analysis entity model.
    Maps to the 'sentiment_analysis' table in PostgreSQL.
    """
    __tablename__ = "sentiment_analysis"
    
    # ID as UUID string (as requested)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String, nullable=False, index=True)  # Store original string IDs (comment/reply IDs)
    source_type = Column(String(20), nullable=False, index=True)  # POST, COMMENT, REPLY
    sentiment = Column(String(20), nullable=False)  # positive, negative, neutral
    sentiment_score = Column(DECIMAL(5, 4))  # Score from 0-1
    top_emotion = Column(String(50))  # Top emotion detected
    emotion_scores = Column(JSONB)  # JSON array of all emotions with scores
    analyzed_text = Column(Text)  # Raw text analyzed
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

