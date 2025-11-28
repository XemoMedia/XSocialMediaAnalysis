"""
Pydantic schemas for sentiment analysis requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class SentimentAnalysisRequest(BaseModel):
    """Request schema for sentiment analysis by IDs."""
    commentIds: List[str] = Field(default_factory=list, description="List of comment IDs to analyze")
    repliedIds: List[str] = Field(default_factory=list, description="List of reply IDs to analyze")


class SentimentResult(BaseModel):
    """Individual sentiment analysis result."""
    id: str = Field(..., description="Comment or Reply ID")
    text: str = Field(..., description="Comment or Reply text")
    sentiment: str = Field(..., description="Sentiment label: positive, negative, or neutral")
    polarity: float = Field(..., description="Polarity score from -1.0 to 1.0")
    emotion: Optional[str] = Field(None, description="Detected emotion")
    sourceType: Optional[str] = Field(None, description="Type of source: COMMENT or REPLY")


class SentimentAnalysisResponse(BaseModel):
    """Response schema for sentiment analysis."""
    results: List[SentimentResult] = Field(..., description="List of sentiment analysis results")
    total_analyzed: int = Field(..., description="Total number of comments and replies analyzed")
    total_requested: int = Field(..., description="Total number of IDs requested (comments + replies)")

