"""
Comment model representing the comments table in the database.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class SocialMediaType(enum.Enum):
    """Social media platform types."""
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"


class Comment(Base):
    """
    Comment entity model.
    Maps to the 'comments' table in PostgreSQL.
    """
    __tablename__ = "comments"
    
    id = Column(String, primary_key=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime)
    account_id = Column(String)
    username = Column(String)
    post_id = Column(String, ForeignKey("post.id"))
    social_media_type = Column(SQLEnum(SocialMediaType))
    created_date = Column(DateTime)
    last_modified_date = Column(DateTime)
    
    # Relationship to Post (optional, if needed)
    # post = relationship("Post", back_populates="comments")

