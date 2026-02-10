"""
Base schema classes for common fields
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    """
    基础实体 Schema，包含常用字段：
    - id: 字符串类型主键
    - created_at: 创建时间
    - updated_at: 更新时间
    - created_by: 创建人
    - updated_by: 更新人
    """
    id: str = Field(..., description="唯一标识符")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[str] = Field(None, description="创建人ID")
    updated_by: Optional[str] = Field(None, description="更新人ID")

    class Config:
        from_attributes = True


class BaseCreateSchema(BaseModel):
    """
    基础创建 Schema - 创建时不需要 id、时间戳等字段
    """
    created_by: Optional[str] = Field(None, description="创建人ID")


class BaseUpdateSchema(BaseModel):
    """
    基础更新 Schema - 更新时只需要更新人字段
    """
    updated_by: Optional[str] = Field(None, description="更新人ID")


class BasePaginationResponse(BaseModel):
    """
    基础分页响应 Schema
    """
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class BaseListResponse(BaseModel):
    """
    基础列表响应 Schema
    """
    total: int = Field(..., description="总数量")
    
    
class BaseResponse(BaseModel):
    """
    基础 API 响应 Schema
    """
    success: bool = Field(True, description="操作是否成功")
    message: str = Field("操作成功", description="响应消息")
    code: int = Field(200, description="响应代码")


class ErrorResponse(BaseResponse):
    """
    错误响应 Schema
    """
    success: bool = Field(False, description="操作失败")
    message: str = Field("操作失败", description="错误消息")
    code: int = Field(400, description="错误代码")
    detail: Optional[str] = Field(None, description="详细错误信息")
