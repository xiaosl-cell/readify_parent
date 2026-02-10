"""
Prompt Template service
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.prompt_template import PromptTemplateRepository
from app.repositories.prompt_use_case import PromptUseCaseRepository
from app.schemas.prompt_template import (
    PromptTemplateCreate, 
    PromptTemplateUpdate, 
    PromptTemplateResponse, 
    PromptTemplateListResponse
)


class PromptTemplateService:
    """
    Business logic for Prompt Template operations
    """
    
    def __init__(self, db: Session):
        self.repository = PromptTemplateRepository(db)
        self.use_case_repository = PromptUseCaseRepository(db)
        self.db = db
    
    def create_template(self, template_in: PromptTemplateCreate) -> PromptTemplateResponse:
        """
        Create a new prompt template
        
        Args:
            template_in: Prompt template creation data
            
        Returns:
            Created prompt template
            
        Raises:
            HTTPException: If template_name already exists
        """
        # Check if template_name already exists
        existing = self.repository.get_by_name(template_in.template_name)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"模板名称 '{template_in.template_name}' 已存在"
            )
        
        template_dict = template_in.model_dump()
        template = self.repository.create(template_dict)
        return PromptTemplateResponse.model_validate(template)
    
    def get_template(self, template_id: str) -> Optional[PromptTemplateResponse]:
        """
        Get prompt template by ID
        
        Args:
            template_id: Prompt template ID
            
        Returns:
            Prompt template or None
        """
        template = self.repository.get(template_id)
        if template:
            return PromptTemplateResponse.model_validate(template)
        return None
    
    def get_template_by_name(self, template_name: str) -> Optional[PromptTemplateResponse]:
        """
        Get prompt template by name
        
        Args:
            template_name: Template name
            
        Returns:
            Prompt template or None
        """
        template = self.repository.get_by_name(template_name)
        if template:
            return PromptTemplateResponse.model_validate(template)
        return None
    
    def get_templates(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        keyword: Optional[str] = None,
        owner: Optional[str] = None,
        qc_number: Optional[str] = None,
        prompt_source: Optional[str] = None
    ) -> PromptTemplateListResponse:
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
            List of prompt templates with total count
        """
        templates = self.repository.get_all(
            skip=skip, 
            limit=limit, 
            keyword=keyword,
            owner=owner,
            qc_number=qc_number,
            prompt_source=prompt_source
        )
        
        # 如果有任何过滤条件，计算过滤后的总数；否则是数据库总数
        if keyword or owner or qc_number or prompt_source:
            total = self.repository.count_filtered(
                keyword=keyword,
                owner=owner,
                qc_number=qc_number,
                prompt_source=prompt_source
            )
        else:
            total = self.repository.count()
        
        return PromptTemplateListResponse(
            total=total,
            items=[PromptTemplateResponse.model_validate(t) for t in templates]
        )
    
    def get_all_templates(self) -> PromptTemplateListResponse:
        """
        Get all prompt templates without pagination
        
        Returns:
            List of all prompt templates ordered by updated_at desc
        """
        templates = self.repository.get_all(skip=0, limit=10000)
        
        return PromptTemplateListResponse(
            total=len(templates),
            items=[PromptTemplateResponse.model_validate(t) for t in templates]
        )
    
    def update_template(
        self, 
        template_id: str, 
        template_in: PromptTemplateUpdate
    ) -> Optional[PromptTemplateResponse]:
        """
        Update a prompt template
        
        Args:
            template_id: Prompt template ID
            template_in: Updated prompt template data
            
        Returns:
            Updated prompt template or None
            
        Raises:
            HTTPException: If template_name conflicts with existing template
        """
        # If updating template_name, check for conflicts
        if template_in.template_name:
            existing = self.repository.get_by_name(template_in.template_name)
            if existing and existing.id != template_id:
                raise HTTPException(
                    status_code=400, 
                    detail=f"模板名称 '{template_in.template_name}' 已存在"
                )
        
        template_dict = template_in.model_dump(exclude_unset=True)
        template = self.repository.update(template_id, template_dict)
        if template:
            return PromptTemplateResponse.model_validate(template)
        return None
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a prompt template and all associated use cases
        
        Args:
            template_id: Prompt template ID
            
        Returns:
            True if deleted, False if not found
            
        Note:
            This will manually delete all prompt use cases associated with this template first,
            then delete the template itself.
        """
        # 检查模板是否存在
        template = self.repository.get(template_id)
        if not template:
            return False
        
        # 获取并删除所有关联的用例
        use_cases = self.use_case_repository.get_by_template_id(template_id, skip=0, limit=10000)
        use_case_count = len(use_cases)
        
        # 先删除所有关联的用例
        for use_case in use_cases:
            self.use_case_repository.delete(use_case.id)
        
        # 提交用例删除
        self.db.commit()
        
        # 然后删除模板
        success = self.repository.delete(template_id)
        
        if success and use_case_count > 0:
            # 可以在这里添加日志
            print(f"Deleted template {template_id} and {use_case_count} associated use cases")
        
        return success

