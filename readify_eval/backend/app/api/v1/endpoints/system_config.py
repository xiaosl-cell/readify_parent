"""
System Configuration endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.system_config import (
    SystemConfigCreate, 
    SystemConfigUpdate, 
    SystemConfigResponse, 
    SystemConfigListResponse,
    SystemConfigBatchRequest,
    SystemConfigBatchResponse
)
from app.services.system_config import SystemConfigService

router = APIRouter()


def get_system_config_service(db: Session = Depends(get_db)) -> SystemConfigService:
    """
    Dependency to get SystemConfigService instance
    
    Args:
        db: Database session
        
    Returns:
        SystemConfigService instance
    """
    return SystemConfigService(db)


@router.post("", response_model=SystemConfigResponse, status_code=201)
def create_config(
    config_in: SystemConfigCreate,
    service: SystemConfigService = Depends(get_system_config_service)
):
    """
    Create a new system configuration
    
    Args:
        config_in: System configuration creation data
        service: System configuration service
        
    Returns:
        Created system configuration
        
    Raises:
        HTTPException: If config_code already exists
    """
    return service.create_config(config_in)


@router.get("/{config_id}", response_model=SystemConfigResponse)
def get_config(
    config_id: str,
    service: SystemConfigService = Depends(get_system_config_service)
):
    """
    Get system configuration by ID
    
    Args:
        config_id: System configuration ID
        service: System configuration service
        
    Returns:
        System configuration details
        
    Raises:
        HTTPException: If configuration not found
    """
    config = service.get_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="找不到系统配置")
    return config


@router.get("/by-code/{config_code}", response_model=SystemConfigResponse)
def get_config_by_code(
    config_code: str,
    service: SystemConfigService = Depends(get_system_config_service)
):
    """
    Get system configuration by code
    
    Args:
        config_code: Configuration code
        service: System configuration service
        
    Returns:
        System configuration details
        
    Raises:
        HTTPException: If configuration not found
    """
    config = service.get_config_by_code(config_code)
    if not config:
        raise HTTPException(status_code=404, detail="找不到系统配置")
    return config


@router.get("", response_model=SystemConfigListResponse)
def get_configs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    keyword: Optional[str] = Query(None, description="Keyword to search across config_code, config_name, config_description, and config_content"),
    service: SystemConfigService = Depends(get_system_config_service)
):
    """
    Get all system configurations with pagination and optional keyword search
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        keyword: Keyword to search across multiple fields (fuzzy match on config_code, config_name, config_description, config_content)
        service: System configuration service
        
    Returns:
        List of system configurations with pagination, ordered by updated_at desc
    """
    return service.get_configs(skip=skip, limit=limit, keyword=keyword)


@router.put("/{config_id}", response_model=SystemConfigResponse)
def update_config(
    config_id: str,
    config_in: SystemConfigUpdate,
    service: SystemConfigService = Depends(get_system_config_service)
):
    """
    Update a system configuration
    
    Args:
        config_id: System configuration ID
        config_in: Updated system configuration data
        service: System configuration service
        
    Returns:
        Updated system configuration
        
    Raises:
        HTTPException: If configuration not found or config_code conflicts
    """
    config = service.update_config(config_id, config_in)
    if not config:
        raise HTTPException(status_code=404, detail="找不到系统配置")
    return config


@router.delete("/{config_id}", status_code=204)
def delete_config(
    config_id: str,
    service: SystemConfigService = Depends(get_system_config_service)
):
    """
    Delete a system configuration
    
    Args:
        config_id: System configuration ID
        service: System configuration service
        
    Raises:
        HTTPException: If configuration not found
    """
    success = service.delete_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="找不到系统配置")


@router.post("/batch", response_model=SystemConfigBatchResponse)
def get_configs_by_codes(
    request: SystemConfigBatchRequest,
    service: SystemConfigService = Depends(get_system_config_service)
):
    """
    Batch get system configurations by config codes
    
    Args:
        request: Batch request containing list of config codes
        service: System configuration service
        
    Returns:
        List of system configurations matching the provided codes
    """
    return service.get_configs_by_codes(request.config_codes)

