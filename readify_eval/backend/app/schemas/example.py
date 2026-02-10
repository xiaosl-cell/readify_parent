"""
Example schemas - you can delete this file and create your own schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.base import BaseEntity, BaseCreateSchema, BaseUpdateSchema, BaseListResponse


class ExampleBase(BaseModel):
    """示例基础 Schema"""
    title: str = Field(..., min_length=1, max_length=255, description="标题")
    description: Optional[str] = Field(None, description="描述")
    is_active: bool = Field(True, description="是否激活")


class ExampleCreate(ExampleBase, BaseCreateSchema):
    """创建示例的 Schema"""
    pass


class ExampleUpdate(BaseUpdateSchema):
    """更新示例的 Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="标题")
    description: Optional[str] = Field(None, description="描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class ExampleResponse(ExampleBase, BaseEntity):
    """示例响应 Schema，继承基础实体"""
    
    class Config:
        from_attributes = True


class ExampleListResponse(BaseListResponse):
    """示例列表响应 Schema"""
    items: List[ExampleResponse] = Field(..., description="示例列表")

