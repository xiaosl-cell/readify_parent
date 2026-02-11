"""
Prompt Template repository
"""
from typing import List, Optional
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate
from app.repositories.base import BaseRepository


class PromptTemplateRepository(BaseRepository[PromptTemplate]):
    """
    Repository for Prompt Template
    """
    
    def __init__(self, db: Session):
        super().__init__(PromptTemplate, db)
    
    def get_by_name(self, template_name: str) -> Optional[PromptTemplate]:
        """
        Get prompt template by name

        Args:
            template_name: Template name

        Returns:
            PromptTemplate instance or None
        """
        return self.db.query(self.model).filter(self.model.template_name == template_name).first()

    def get_by_code(self, template_code: str) -> Optional[PromptTemplate]:
        """
        Get prompt template by code

        Args:
            template_code: Template code

        Returns:
            PromptTemplate instance or None
        """
        return self.db.query(self.model).filter(self.model.template_code == template_code).first()
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        keyword: Optional[str] = None,
        owner: Optional[str] = None,
        qc_number: Optional[str] = None,
        prompt_source: Optional[str] = None
    ) -> List[PromptTemplate]:
        """
        Get all prompt templates with pagination and optional keyword search and filters
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            keyword: Keyword to search across multiple fields (template_name, system_prompt, user_prompt, function_category, owner, qc_number, prompt_source, remarks)
            owner: Filter by owner (fuzzy match)
            qc_number: Filter by QC number (fuzzy match)
            prompt_source: Filter by prompt source (fuzzy match)
            
        Returns:
            List of PromptTemplate instances ordered by updated_at desc
        """
        query = self.db.query(self.model)
        
        # 如果有关键字，进行多字段模糊查询
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    self.model.template_name.like(search_pattern),
                    self.model.system_prompt.like(search_pattern),
                    self.model.user_prompt.like(search_pattern),
                    self.model.function_category.like(search_pattern),
                    self.model.remarks.like(search_pattern),
                    self.model.owner.like(search_pattern),
                    self.model.qc_number.like(search_pattern),
                    self.model.prompt_source.like(search_pattern)
                )
            )
        
        # 如果指定了负责人过滤，进行模糊匹配
        if owner:
            query = query.filter(self.model.owner.like(f"%{owner}%"))
        
        # 如果指定了QC号过滤，进行模糊匹配
        if qc_number:
            query = query.filter(self.model.qc_number.like(f"%{qc_number}%"))
        
        # 如果指定了提示词来源过滤，进行模糊匹配
        if prompt_source:
            query = query.filter(self.model.prompt_source.like(f"%{prompt_source}%"))
        
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
        owner: Optional[str] = None,
        qc_number: Optional[str] = None,
        prompt_source: Optional[str] = None
    ) -> int:
        """
        Count prompt templates with optional filters
        
        Args:
            keyword: Keyword to search across multiple fields
            owner: Filter by owner (fuzzy match)
            qc_number: Filter by QC number (fuzzy match)
            prompt_source: Filter by prompt source (fuzzy match)
            
        Returns:
            Total count of filtered templates
        """
        query = self.db.query(func.count(self.model.id))
        
        # 如果有关键字，进行多字段模糊查询
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    self.model.template_name.like(search_pattern),
                    self.model.system_prompt.like(search_pattern),
                    self.model.user_prompt.like(search_pattern),
                    self.model.function_category.like(search_pattern),
                    self.model.remarks.like(search_pattern),
                    self.model.owner.like(search_pattern),
                    self.model.qc_number.like(search_pattern),
                    self.model.prompt_source.like(search_pattern)
                )
            )
        
        # 如果指定了负责人过滤，进行模糊匹配
        if owner:
            query = query.filter(self.model.owner.like(f"%{owner}%"))
        
        # 如果指定了QC号过滤，进行模糊匹配
        if qc_number:
            query = query.filter(self.model.qc_number.like(f"%{qc_number}%"))
        
        # 如果指定了提示词来源过滤，进行模糊匹配
        if prompt_source:
            query = query.filter(self.model.prompt_source.like(f"%{prompt_source}%"))
        
        return query.scalar() or 0

