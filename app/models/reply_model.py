"""
Reply model representing the replies table in the database.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.comment_model import SocialMediaType


class Reply(Base):
    """
    Reply entity model.
    Maps to the 'replies' table in PostgreSQL.
    """
    __tablename__ = "replies"
    
    id = Column(String, primary_key=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime)
    account_id = Column(String)
    username = Column(String)
    comment_id = Column(String, ForeignKey("comments.id"))
    social_media_type = Column(SQLEnum(SocialMediaType))
    created_date = Column(DateTime)
    last_modified_date = Column(DateTime)
    
    # Relationship to Comment (optional, if needed)
    # comment = relationship("Comment", back_populates="replies")

