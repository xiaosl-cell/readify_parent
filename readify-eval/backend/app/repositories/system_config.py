"""
System Configuration repository
"""
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig
from app.repositories.base import BaseRepository


class SystemConfigRepository(BaseRepository[SystemConfig]):
    """
    Repository for System Configuration
    """
    
    def __init__(self, db: Session):
        super().__init__(SystemConfig, db)
    
    def get_by_code(self, config_code: str) -> Optional[SystemConfig]:
        """
        Get system configuration by code
        
        Args:
            config_code: Configuration code
            
        Returns:
            SystemConfig instance or None
        """
        return self.db.query(self.model).filter(self.model.config_code == config_code).first()
    
    def get_all(self, skip: int = 0, limit: int = 100, keyword: Optional[str] = None) -> List[SystemConfig]:
        """
        Get all system configurations with pagination and optional keyword search
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            keyword: Keyword to search across multiple fields (config_code, config_name, config_description, config_content)
            
        Returns:
            List of SystemConfig instances ordered by updated_at desc
        """
        query = self.db.query(self.model)
        
        # 如果有关键字，进行多字段模糊查询
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    self.model.config_code.like(search_pattern),
                    self.model.config_name.like(search_pattern),
                    self.model.config_description.like(search_pattern),
                    self.model.config_content.like(search_pattern)
                )
            )
        
        return (
            query
            .order_by(self.model.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_codes(self, config_codes: List[str]) -> List[SystemConfig]:
        """
        Get system configurations by multiple codes
        
        Args:
            config_codes: List of configuration codes
            
        Returns:
            List of SystemConfig instances
        """
        return self.db.query(self.model).filter(self.model.config_code.in_(config_codes)).all()

