"""
Repository layer for reply database operations.
Follows repository pattern similar to Spring Boot.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.reply_model import Reply


class ReplyRepository:
    """
    Repository for reply database operations.
    Handles all database queries related to replies.
    """
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def find_by_ids(self, ids: List[str]) -> List[Reply]:
        """
        Find replies by their IDs.
        
        Args:
            ids: List of reply IDs to fetch
            
        Returns:
            List of Reply entities
        """
        return self.db.query(Reply).filter(Reply.id.in_(ids)).all()
    
    def find_by_id(self, reply_id: str) -> Optional[Reply]:
        """
        Find a single reply by ID.
        
        Args:
            reply_id: Reply ID
            
        Returns:
            Reply entity or None if not found
        """
        return self.db.query(Reply).filter(Reply.id == reply_id).first()
    
    def find_all(self, limit: Optional[int] = None) -> List[Reply]:
        """
        Find all replies with optional limit.
        
        Args:
            limit: Maximum number of replies to return
            
        Returns:
            List of Reply entities
        """
        query = self.db.query(Reply)
        if limit:
            query = query.limit(limit)
        return query.all()

