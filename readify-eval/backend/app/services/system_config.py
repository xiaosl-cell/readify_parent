"""
System Configuration service
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.system_config import SystemConfigRepository
from app.schemas.system_config import (
    SystemConfigCreate, 
    SystemConfigUpdate, 
    SystemConfigResponse, 
    SystemConfigListResponse,
    SystemConfigBatchResponse
)


class SystemConfigService:
    """
    Business logic for System Configuration operations
    """
    
    def __init__(self, db: Session):
        self.repository = SystemConfigRepository(db)
    
    def create_config(self, config_in: SystemConfigCreate) -> SystemConfigResponse:
        """
        Create a new system configuration
        
        Args:
            config_in: System configuration creation data
            
        Returns:
            Created system configuration
            
        Raises:
            HTTPException: If config_code already exists
        """
        # Check if config_code already exists
        existing = self.repository.get_by_code(config_in.config_code)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"配置代码 '{config_in.config_code}' 已存在"
            )
        
        config_dict = config_in.model_dump()
        config = self.repository.create(config_dict)
        return SystemConfigResponse.model_validate(config)
    
    def get_config(self, config_id: str) -> Optional[SystemConfigResponse]:
        """
        Get system configuration by ID
        
        Args:
            config_id: System configuration ID
            
        Returns:
            System configuration or None
        """
        config = self.repository.get(config_id)
        if config:
            return SystemConfigResponse.model_validate(config)
        return None
    
    def get_config_by_code(self, config_code: str) -> Optional[SystemConfigResponse]:
        """
        Get system configuration by code
        
        Args:
            config_code: Configuration code
            
        Returns:
            System configuration or None
        """
        config = self.repository.get_by_code(config_code)
        if config:
            return SystemConfigResponse.model_validate(config)
        return None
    
    def get_configs(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        keyword: Optional[str] = None
    ) -> SystemConfigListResponse:
        """
        Get all system configurations with pagination and optional keyword search
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            keyword: Keyword to search across multiple fields (config_code, config_name, config_description, config_content)
            
        Returns:
            List of system configurations with total count
        """
        configs = self.repository.get_all(skip=skip, limit=limit, keyword=keyword)
        
        # 如果有关键字搜索，total就是结果数量；否则是数据库总数
        if keyword:
            total = len(configs)
        else:
            total = self.repository.count()
        
        return SystemConfigListResponse(
            total=total,
            items=[SystemConfigResponse.model_validate(c) for c in configs]
        )
    
    def update_config(
        self, 
        config_id: str, 
        config_in: SystemConfigUpdate
    ) -> Optional[SystemConfigResponse]:
        """
        Update a system configuration
        
        Args:
            config_id: System configuration ID
            config_in: Updated system configuration data
            
        Returns:
            Updated system configuration or None
            
        Raises:
            HTTPException: If config_code conflicts with existing configuration
        """
        # If updating config_code, check for conflicts
        if config_in.config_code:
            existing = self.repository.get_by_code(config_in.config_code)
            if existing and existing.id != config_id:
                raise HTTPException(
                    status_code=400, 
                    detail=f"配置代码 '{config_in.config_code}' 已存在"
                )
        
        config_dict = config_in.model_dump(exclude_unset=True)
        config = self.repository.update(config_id, config_dict)
        if config:
            return SystemConfigResponse.model_validate(config)
        return None
    
    def delete_config(self, config_id: str) -> bool:
        """
        Delete a system configuration
        
        Args:
            config_id: System configuration ID
            
        Returns:
            True if deleted, False if not found
        """
        return self.repository.delete(config_id)
    
    def get_configs_by_codes(self, config_codes: list[str]) -> SystemConfigBatchResponse:
        """
        Get system configurations by multiple codes
        
        Args:
            config_codes: List of configuration codes
            
        Returns:
            Batch response with list of system configurations
        """
        configs = self.repository.get_by_codes(config_codes)
        return SystemConfigBatchResponse(
            total=len(configs),
            items=[SystemConfigResponse.model_validate(c) for c in configs]
        )

