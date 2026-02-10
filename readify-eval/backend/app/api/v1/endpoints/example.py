"""
Example endpoints - you can delete this file and create your own endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.example import ExampleCreate, ExampleUpdate, ExampleResponse, ExampleListResponse
from app.services.example import ExampleService

router = APIRouter()


def get_example_service(db: Session = Depends(get_db)) -> ExampleService:
    """
    Dependency to get ExampleService instance
    
    Args:
        db: Database session
        
    Returns:
        ExampleService instance
    """
    return ExampleService(db)


@router.post("", response_model=ExampleResponse, status_code=201)
def create_example(
    example_in: ExampleCreate,
    service: ExampleService = Depends(get_example_service)
):
    """
    Create a new example
    
    Args:
        example_in: Example creation data
        service: Example service
        
    Returns:
        Created example
    """
    return service.create_example(example_in)


@router.get("/{example_id}", response_model=ExampleResponse)
def get_example(
    example_id: str,
    service: ExampleService = Depends(get_example_service)
):
    """
    Get example by ID
    
    Args:
        example_id: Example ID
        service: Example service
        
    Returns:
        Example details
        
    Raises:
        HTTPException: If example not found
    """
    example = service.get_example(example_id)
    if not example:
        raise HTTPException(status_code=404, detail="找不到示例")
    return example


@router.get("", response_model=ExampleListResponse)
def get_examples(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    active_only: bool = Query(False, description="Return only active examples"),
    service: ExampleService = Depends(get_example_service)
):
    """
    Get all examples with pagination
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: Return only active examples
        service: Example service
        
    Returns:
        List of examples with pagination
    """
    if active_only:
        return service.get_active_examples(skip=skip, limit=limit)
    return service.get_examples(skip=skip, limit=limit)


@router.put("/{example_id}", response_model=ExampleResponse)
def update_example(
    example_id: str,
    example_in: ExampleUpdate,
    service: ExampleService = Depends(get_example_service)
):
    """
    Update an example
    
    Args:
        example_id: Example ID
        example_in: Updated example data
        service: Example service
        
    Returns:
        Updated example
        
    Raises:
        HTTPException: If example not found
    """
    example = service.update_example(example_id, example_in)
    if not example:
        raise HTTPException(status_code=404, detail="找不到示例")
    return example


@router.delete("/{example_id}", status_code=204)
def delete_example(
    example_id: str,
    service: ExampleService = Depends(get_example_service)
):
    """
    Delete an example
    
    Args:
        example_id: Example ID
        service: Example service
        
    Raises:
        HTTPException: If example not found
    """
    success = service.delete_example(example_id)
    if not success:
        raise HTTPException(status_code=404, detail="找不到示例")

