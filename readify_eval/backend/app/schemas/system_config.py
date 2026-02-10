"""
System Configuration schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.base import BaseEntity, BaseCreateSchema, BaseUpdateSchema, BaseListResponse


class SystemConfigBase(BaseModel):
    """系统配置基础 Schema"""
    config_code: str = Field(..., min_length=1, max_length=255, description="配置编码")
    config_name: str = Field(..., min_length=1, max_length=255, description="配置名称")
    config_description: Optional[str] = Field(None, description="配置描述")
    config_content: str = Field(..., min_length=1, description="配置内容")


class SystemConfigCreate(SystemConfigBase, BaseCreateSchema):
    """创建系统配置的 Schema"""
    pass


class SystemConfigUpdate(BaseUpdateSchema):
    """更新系统配置的 Schema"""
    config_code: Optional[str] = Field(None, min_length=1, max_length=255, description="配置编码")
    config_name: Optional[str] = Field(None, min_length=1, max_length=255, description="配置名称")
    config_description: Optional[str] = Field(None, description="配置描述")
    config_content: Optional[str] = Field(None, min_length=1, description="配置内容")


class SystemConfigResponse(SystemConfigBase, BaseEntity):
    """系统配置响应 Schema，继承基础实体"""
    
    class Config:
        from_attributes = True


class SystemConfigListResponse(BaseListResponse):
    """系统配置列表响应 Schema"""
    items: List[SystemConfigResponse] = Field(..., description="系统配置列表")


class SystemConfigBatchRequest(BaseModel):
    """批量获取系统配置的请求 Schema"""
    config_codes: List[str] = Field(..., min_length=1, description="配置编码列表")


class SystemConfigBatchResponse(BaseModel):
    """批量获取系统配置的响应 Schema"""
    items: List[SystemConfigResponse] = Field(..., description="系统配置列表")
    total: int = Field(..., description="返回的配置数量")
