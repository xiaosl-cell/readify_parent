"""
Prompt Use Case schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.schemas.base import BaseEntity, BaseCreateSchema, BaseUpdateSchema, BaseListResponse


class PromptUseCaseBase(BaseModel):
    """提示词用例基础 Schema"""
    use_case_name: str = Field(..., min_length=1, max_length=255, description="用例名称")
    template_id: str = Field(..., min_length=1, max_length=36, description="关联的提示词模板ID")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="用于填充模板的变量（JSON格式）")
    reference_answer: Optional[str] = Field(None, description="参考答案")
    remarks: Optional[str] = Field(None, description="备注信息")


class PromptUseCaseCreate(PromptUseCaseBase, BaseCreateSchema):
    """创建提示词用例的 Schema"""
    pass


class PromptUseCaseUpdate(BaseUpdateSchema):
    """更新提示词用例的 Schema"""
    use_case_name: Optional[str] = Field(None, min_length=1, max_length=255, description="用例名称")
    template_id: Optional[str] = Field(None, min_length=1, max_length=36, description="关联的提示词模板ID")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="用于填充模板的变量（JSON格式）")
    reference_answer: Optional[str] = Field(None, description="参考答案")
    remarks: Optional[str] = Field(None, description="备注信息")


class PromptUseCaseResponse(PromptUseCaseBase, BaseEntity):
    """提示词用例响应 Schema，继承基础实体"""
    rendered_system_prompt: Optional[str] = Field(None, description="渲染后的系统提示词最终文本")
    rendered_user_prompt: Optional[str] = Field(None, description="渲染后的用户提示词最终文本")
    
    class Config:
        from_attributes = True


class PromptUseCaseListResponse(BaseListResponse):
    """提示词用例列表响应 Schema"""
    items: List[PromptUseCaseResponse] = Field(..., description="提示词用例列表")

