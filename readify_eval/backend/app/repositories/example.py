"""
Example repository - you can delete this file and create your own repositories
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.example import ExampleModel
from app.repositories.base import BaseRepository


class ExampleRepository(BaseRepository[ExampleModel]):
    """
    Repository for Example model
    """
    
    def __init__(self, db: Session):
        super().__init__(ExampleModel, db)
    
    def get_by_title(self, title: str) -> Optional[ExampleModel]:
        """
        Get example by title
        
        Args:
            title: Example title
            
        Returns:
            ExampleModel instance or None
        """
        return self.db.query(self.model).filter(self.model.title == title).first()
    
    def get_active(self, skip: int = 0, limit: int = 100) -> List[ExampleModel]:
        """
        Get all active examples
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active ExampleModel instances
        """
        return (
            self.db.query(self.model)
            .filter(self.model.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

