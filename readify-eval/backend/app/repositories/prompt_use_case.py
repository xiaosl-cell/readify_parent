"""
Prompt Use Case repository
"""
from typing import List, Optional, Sequence
from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload

from app.models.prompt_use_case import PromptUseCase
from app.repositories.base import BaseRepository


class PromptUseCaseRepository(BaseRepository[PromptUseCase]):
    """
    Repository for Prompt Use Case
    """
    
    def __init__(self, db: Session):
        super().__init__(PromptUseCase, db)
    
    def get_with_template(self, use_case_id: str) -> Optional[PromptUseCase]:
        """
        Get prompt use case by ID with template relationship loaded
        
        Args:
            use_case_id: Use case ID
            
        Returns:
            PromptUseCase instance with template loaded, or None
        """
        return (
            self.db.query(self.model)
            .options(joinedload(self.model.template))
            .filter(self.model.id == use_case_id)
            .first()
        )
    
    def get_by_template_id(self, template_id: str, skip: int = 0, limit: int = 100) -> List[PromptUseCase]:
        """
        Get all use cases for a specific template
        
        Args:
            template_id: Template ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of PromptUseCase instances ordered by updated_at desc
        """
        return (
            self.db.query(self.model)
            .filter(self.model.template_id == template_id)
            .order_by(self.model.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_ids(self, use_case_ids: Sequence[str]) -> List[PromptUseCase]:
        """
        Batch fetch prompt use cases by IDs.

        Args:
            use_case_ids: Iterable of use case IDs

        Returns:
            List of PromptUseCase records.
        """
        ids = [i for i in use_case_ids if i]
        if not ids:
            return []
        return self.db.query(self.model).filter(self.model.id.in_(ids)).all()
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        keyword: Optional[str] = None,
        template_id: Optional[str] = None
    ) -> List[PromptUseCase]:
        """
        Get all prompt use cases with pagination and optional filters
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            keyword: Keyword to search across multiple fields
            template_id: Filter by template ID
            
        Returns:
            List of PromptUseCase instances ordered by updated_at desc
        """
        query = self.db.query(self.model)
        
        # 如果指定了模板ID，添加过滤条件
        if template_id:
            query = query.filter(self.model.template_id == template_id)
        
        # 如果有关键字，进行多字段模糊查询
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    self.model.use_case_name.like(search_pattern),
                    self.model.remarks.like(search_pattern)
                )
            )
        
        return (
            query
            .order_by(self.model.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def count_filtered(
        self,
        keyword: Optional[str] = None,
        template_id: Optional[str] = None
    ) -> int:
        """
        Count prompt use cases with optional filters
        
        Args:
            keyword: Keyword to search across multiple fields
            template_id: Filter by template ID
            
        Returns:
            Total count of matching records
        """
        query = self.db.query(func.count(self.model.id))
        
        # 如果指定了模板ID，添加过滤条件
        if template_id:
            query = query.filter(self.model.template_id == template_id)
        
        # 如果有关键字，进行多字段模糊查询
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    self.model.use_case_name.like(search_pattern),
                    self.model.remarks.like(search_pattern)
                )
            )
        
        return query.scalar()

