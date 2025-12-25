"""
Pydantic schemas for enriched social comment analysis responses.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class EmotionScore(BaseModel):
    emotion: str = Field(..., description="Detected emotion label")
    score: float = Field(..., description="Confidence score between 0 and 1")


class SocialCommentInsight(BaseModel):
    id: str
    username: Optional[str]
    platform: Optional[str]
    brand: Optional[str]
    comment: Optional[str]
    sentiment: str
    sentiment_score: float
    polarity: float
    emotion: str
    emotion_scores: List[EmotionScore] = Field(default_factory=list)
    intent: str
    intent_confidence: float
    language: str
    toxicity: str
    toxicity_score: float
    sarcasm: str
    sarcasm_score: float
    topics: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    risk_index: float


class SocialCommentAnalysisResponse(BaseModel):
    total_records: int
    analyzed_records: int
    results: List[SocialCommentInsight]

