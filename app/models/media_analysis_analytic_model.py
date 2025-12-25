"""
SQLAlchemy model mapping to the media_analysis_analytics table managed by the Java service.
"""
from sqlalchemy import Boolean, Column, DateTime, Float, String, Text, UniqueConstraint
from app.database import Base


class MediaAnalysisAnalytic(Base):
    __tablename__ = "media_analysis_analytics"
    __table_args__ = (UniqueConstraint("social_comment_analysis_id", name="uq_media_analysis_social_id"),)

    id = Column(String, primary_key=True)
    social_comment_analysis_id = Column(String, nullable=False)
    language = Column(String(64))
    is_code_switched = Column("is_code_switched", Boolean)
    is_transliterated = Column("is_transliterated", Boolean)
    sentiment = Column(String(64))
    intent = Column(String(64))
    toxicity = Column(String(64))
    emotion = Column(String(64))
    sarcasm = Column(String(64))
    risk_index = Column(Float)
    topics = Column(Text)
    entities = Column(Text)
    notes = Column(Text)
    created_date = Column(DateTime)
    last_modified_date = Column(DateTime)

