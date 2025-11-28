"""
Repository layer for comment database operations.
Follows repository pattern similar to Spring Boot.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.comment_model import Comment


class CommentRepository:
    """
    Repository for comment database operations.
    Handles all database queries related to comments.
    """
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def find_by_ids(self, ids: List[str]) -> List[Comment]:
        """
        Find comments by their IDs.
        
        Args:
            ids: List of comment IDs to fetch
            
        Returns:
            List of Comment entities
        """
        return self.db.query(Comment).filter(Comment.id.in_(ids)).all()
    
    def find_by_id(self, comment_id: str) -> Optional[Comment]:
        """
        Find a single comment by ID.
        
        Args:
            comment_id: Comment ID
            
        Returns:
            Comment entity or None if not found
        """
        return self.db.query(Comment).filter(Comment.id == comment_id).first()
    
    def find_all(self, limit: Optional[int] = None) -> List[Comment]:
        """
        Find all comments with optional limit.
        
        Args:
            limit: Maximum number of comments to return
            
        Returns:
            List of Comment entities
        """
        query = self.db.query(Comment)
        if limit:
            query = query.limit(limit)
        return query.all()

