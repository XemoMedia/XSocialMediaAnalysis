"""
SQLAlchemy model for the social_comment_analysis table populated by the Java service.
"""
from sqlalchemy import Column, DateTime, String, Text
from app.database import Base


class SocialCommentAnalysis(Base):
    """
    Lightweight representation of the social_comment_analysis table.

    The Java upload service writes into this table; this model lets the Python service
    query the same data for downstream analytics.
    """

    __tablename__ = "social_comment_analysis"

    id = Column(String, primary_key=True)
    username = Column(String(128))
    comment = Column(Text)
    platform = Column(String(64))
    brand = Column(String(128))
    created_date = Column(DateTime)
    last_modified_date = Column(DateTime)

