"""
Prompt Use Case endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.prompt_use_case import (
    PromptUseCaseCreate, 
    PromptUseCaseUpdate, 
    PromptUseCaseResponse, 
    PromptUseCaseListResponse
)
from app.services.prompt_use_case import PromptUseCaseService

router = APIRouter()


def get_prompt_use_case_service(db: Session = Depends(get_db)) -> PromptUseCaseService:
    """
    Dependency to get PromptUseCaseService instance
    
    Args:
        db: Database session
        
    Returns:
        PromptUseCaseService instance
    """
    return PromptUseCaseService(db)


@router.post("", response_model=PromptUseCaseResponse, status_code=201)
def create_use_case(
    use_case_in: PromptUseCaseCreate,
    service: PromptUseCaseService = Depends(get_prompt_use_case_service)
):
    """
    Create a new prompt use case
    
    The system will automatically render the prompts by replacing variables in the template.
    Variables in the template should be in the format: <$variable_name>
    
    Args:
        use_case_in: Prompt use case creation data
        service: Prompt use case service
        
    Returns:
        Created prompt use case with rendered prompts
        
    Raises:
        HTTPException: If template not found
    """
    return service.create_use_case(use_case_in)


@router.get("/all", response_model=PromptUseCaseListResponse)
def get_all_use_cases(
    service: PromptUseCaseService = Depends(get_prompt_use_case_service)
):
    """
    Get all prompt use cases without pagination
    
    Args:
        service: Prompt use case service
        
    Returns:
        List of all prompt use cases, ordered by updated_at desc
    """
    return service.get_all_use_cases()


@router.get("/{use_case_id}", response_model=PromptUseCaseResponse)
def get_use_case(
    use_case_id: str,
    service: PromptUseCaseService = Depends(get_prompt_use_case_service)
):
    """
    Get prompt use case by ID
    
    Args:
        use_case_id: Prompt use case ID
        service: Prompt use case service
        
    Returns:
        Prompt use case details
        
    Raises:
        HTTPException: If use case not found
    """
    use_case = service.get_use_case(use_case_id)
    if not use_case:
        raise HTTPException(status_code=404, detail="找不到提示词用例")
    return use_case


@router.get("", response_model=PromptUseCaseListResponse)
def get_use_cases(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    keyword: Optional[str] = Query(None, description="Keyword to search across use_case_name and remarks"),
    template_id: Optional[str] = Query(None, description="Filter by template ID"),
    service: PromptUseCaseService = Depends(get_prompt_use_case_service)
):
    """
    Get all prompt use cases with pagination and optional filters
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        keyword: Keyword to search (fuzzy match on use_case_name, remarks)
        template_id: Filter by template ID
        service: Prompt use case service
        
    Returns:
        List of prompt use cases with pagination, ordered by updated_at desc
    """
    return service.get_use_cases(skip=skip, limit=limit, keyword=keyword, template_id=template_id)


@router.put("/{use_case_id}", response_model=PromptUseCaseResponse)
def update_use_case(
    use_case_id: str,
    use_case_in: PromptUseCaseUpdate,
    service: PromptUseCaseService = Depends(get_prompt_use_case_service)
):
    """
    Update a prompt use case
    
    If template_id or template_variables are updated, the system will automatically
    re-render the prompts with the new template and/or variables.
    
    Args:
        use_case_id: Prompt use case ID
        use_case_in: Updated prompt use case data
        service: Prompt use case service
        
    Returns:
        Updated prompt use case with re-rendered prompts
        
    Raises:
        HTTPException: If use case not found or template not found
    """
    use_case = service.update_use_case(use_case_id, use_case_in)
    if not use_case:
        raise HTTPException(status_code=404, detail="找不到提示词用例")
    return use_case


@router.delete("/{use_case_id}", status_code=204)
def delete_use_case(
    use_case_id: str,
    service: PromptUseCaseService = Depends(get_prompt_use_case_service)
):
    """
    Delete a prompt use case
    
    Args:
        use_case_id: Prompt use case ID
        service: Prompt use case service
        
    Raises:
        HTTPException: If use case not found
    """
    success = service.delete_use_case(use_case_id)
    if not success:
        raise HTTPException(status_code=404, detail="找不到提示词用例")

