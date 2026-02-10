"""
Prompt Template endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.prompt_template import (
    PromptTemplateCreate, 
    PromptTemplateUpdate, 
    PromptTemplateResponse, 
    PromptTemplateListResponse
)
from app.services.prompt_template import PromptTemplateService

router = APIRouter()


def get_prompt_template_service(db: Session = Depends(get_db)) -> PromptTemplateService:
    """
    Dependency to get PromptTemplateService instance
    
    Args:
        db: Database session
        
    Returns:
        PromptTemplateService instance
    """
    return PromptTemplateService(db)


@router.post("", response_model=PromptTemplateResponse, status_code=201)
def create_template(
    template_in: PromptTemplateCreate,
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    Create a new prompt template
    
    Args:
        template_in: Prompt template creation data
        service: Prompt template service
        
    Returns:
        Created prompt template
        
    Raises:
        HTTPException: If template_name already exists
    """
    return service.create_template(template_in)


@router.get("/all", response_model=PromptTemplateListResponse)
def get_all_templates(
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    Get all prompt templates without pagination
    
    Args:
        service: Prompt template service
        
    Returns:
        List of all prompt templates, ordered by updated_at desc
    """
    return service.get_all_templates()


@router.get("/{template_id}", response_model=PromptTemplateResponse)
def get_template(
    template_id: str,
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    Get prompt template by ID
    
    Args:
        template_id: Prompt template ID
        service: Prompt template service
        
    Returns:
        Prompt template details
        
    Raises:
        HTTPException: If template not found
    """
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="找不到提示词模板")
    return template


@router.get("", response_model=PromptTemplateListResponse)
def get_templates(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    keyword: Optional[str] = Query(None, description="Keyword to search across template_name, system_prompt, user_prompt, function_category, owner, qc_number, prompt_source, and remarks"),
    owner: Optional[str] = Query(None, description="Filter by owner (fuzzy match)"),
    qc_number: Optional[str] = Query(None, description="Filter by QC number (fuzzy match)"),
    prompt_source: Optional[str] = Query(None, description="Filter by prompt source (fuzzy match)"),
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    Get all prompt templates with pagination and optional keyword search and filters
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        keyword: Keyword to search across multiple fields (fuzzy match on template_name, system_prompt, user_prompt, function_category, owner, qc_number, prompt_source, remarks)
        owner: Filter by owner (fuzzy match)
        qc_number: Filter by QC number (fuzzy match)
        prompt_source: Filter by prompt source (fuzzy match)
        service: Prompt template service
        
    Returns:
        List of prompt templates with pagination, ordered by updated_at desc
    """
    return service.get_templates(skip=skip, limit=limit, keyword=keyword, owner=owner, qc_number=qc_number, prompt_source=prompt_source)


@router.put("/{template_id}", response_model=PromptTemplateResponse)
def update_template(
    template_id: str,
    template_in: PromptTemplateUpdate,
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    Update a prompt template
    
    Args:
        template_id: Prompt template ID
        template_in: Updated prompt template data
        service: Prompt template service
        
    Returns:
        Updated prompt template
        
    Raises:
        HTTPException: If template not found or template_name conflicts
    """
    template = service.update_template(template_id, template_in)
    if not template:
        raise HTTPException(status_code=404, detail="找不到提示词模板")
    return template


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: str,
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    Delete a prompt template and all associated use cases
    
    Args:
        template_id: Prompt template ID
        service: Prompt template service
        
    Raises:
        HTTPException: If template not found
        
    Note:
        This operation will cascade delete all prompt use cases that reference this template.
        The deletion is handled at the database level via foreign key constraint (ON DELETE CASCADE).
    """
    success = service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="找不到提示词模板")

