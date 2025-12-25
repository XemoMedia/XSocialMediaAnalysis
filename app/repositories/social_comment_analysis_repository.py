"""
Repository layer for the social_comment_analysis table.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.social_comment_analysis_model import SocialCommentAnalysis


class SocialCommentAnalysisRepository:
    """Encapsulates read operations for social comment analysis records."""

    def __init__(self, db: Session):
        self.db = db

    def find_all(self, limit: Optional[int] = None) -> List[SocialCommentAnalysis]:
        query = self.db.query(SocialCommentAnalysis).order_by(SocialCommentAnalysis.created_date.asc())
        if limit:
            query = query.limit(limit)
        return query.all()

