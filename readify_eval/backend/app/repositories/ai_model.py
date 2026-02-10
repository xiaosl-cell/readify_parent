"""
AI Model repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.ai_model import AIModel, ModelCategory
from app.repositories.base import BaseRepository


class AIModelRepository(BaseRepository[AIModel]):
    """
    Repository for AI Model
    """
    
    def __init__(self, db: Session):
        super().__init__(AIModel, db)
    
    def get_by_model_id(self, model_id: str) -> Optional[AIModel]:
        """
        Get AI model by model_id
        
        Args:
            model_id: Model ID
            
        Returns:
            AIModel instance or None
        """
        return self.db.query(self.model).filter(self.model.model_id == model_id).first()
    
    def get_enabled(self, skip: int = 0, limit: int = 100, category: Optional[ModelCategory] = None) -> List[AIModel]:
        """
        Get all enabled AI models
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            category: Filter by model category
            
        Returns:
            List of enabled AIModel instances ordered by updated_at desc
        """
        query = self.db.query(self.model).filter(self.model.is_enabled == True)
        
        if category:
            query = query.filter(self.model.category == category)
        
        return query.order_by(self.model.updated_at.desc()).offset(skip).limit(limit).all()
    
    def get_all(self, skip: int = 0, limit: int = 100, category: Optional[ModelCategory] = None) -> List[AIModel]:
        """
        Get all AI models with pagination and optional category filter
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            category: Filter by model category
            
        Returns:
            List of model instances ordered by updated_at desc
        """
        query = self.db.query(self.model)
        
        if category:
            query = query.filter(self.model.category == category)
        
        return query.order_by(self.model.updated_at.desc()).offset(skip).limit(limit).all()
    
    def search_by_name(self, name: str, skip: int = 0, limit: int = 100, enabled_only: bool = False, category: Optional[ModelCategory] = None) -> List[AIModel]:
        """
        Search AI models by name
        
        Args:
            name: Model name (partial match)
            skip: Number of records to skip
            limit: Maximum number of records to return
            enabled_only: Filter only enabled models
            category: Filter by model category
            
        Returns:
            List of matching AIModel instances ordered by updated_at desc
        """
        query = self.db.query(self.model).filter(self.model.model_name.like(f"%{name}%"))
        
        if enabled_only:
            query = query.filter(self.model.is_enabled == True)
        
        if category:
            query = query.filter(self.model.category == category)
        
        return query.order_by(self.model.updated_at.desc()).offset(skip).limit(limit).all()

