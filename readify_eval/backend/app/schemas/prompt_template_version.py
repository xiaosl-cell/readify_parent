"""
Prompt Template Version schemas
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

from app.schemas.base import BaseEntity, BaseListResponse


class PromptTemplateVersionResponse(BaseEntity):
    """提示词模板版本响应 Schema"""
    template_id: str = Field(..., description="关联的提示词模板ID")
    version: int = Field(..., description="版本号")
    change_log: Optional[str] = Field(None, description="变更说明")

    # 版本快照字段
    template_code: Optional[str] = Field(None, description="模板编码")
    template_name: str = Field(..., description="提示词模板名称")
    system_prompt: Optional[str] = Field(None, description="系统提示词模板")
    user_prompt: Optional[str] = Field(None, description="用户提示词模板")
    function_category: Optional[str] = Field(None, description="所属功能")
    remarks: Optional[str] = Field(None, description="备注")
    max_tokens: Optional[str] = Field(None, description="最大生成token数")
    top_p: Optional[str] = Field(None, description="核采样参数")
    top_k: Optional[str] = Field(None, description="top-k采样参数")
    temperature: Optional[str] = Field(None, description="温度参数")
    evaluation_strategies: Optional[List] = Field(None, description="评估策略列表")
    owner: Optional[str] = Field(None, description="负责人")
    qc_number: Optional[str] = Field(None, description="QC号")
    prompt_source: Optional[str] = Field(None, description="提示词来源")

    class Config:
        from_attributes = True


class PromptTemplateVersionListResponse(BaseListResponse):
    """提示词模板版本列表响应 Schema"""
    items: List[PromptTemplateVersionResponse] = Field(..., description="版本列表")


class PromptTemplateVersionDiff(BaseModel):
    """提示词模板版本差异响应 Schema"""
    field: str = Field(..., description="字段名")
    field_label: str = Field(..., description="字段中文名")
    old_value: Optional[Any] = Field(None, description="旧值")
    new_value: Optional[Any] = Field(None, description="新值")


class PromptTemplateVersionDiffResponse(BaseModel):
    """提示词模板版本差异比较响应 Schema"""
    template_id: str = Field(..., description="模板ID")
    from_version: int = Field(..., description="对比起始版本号")
    to_version: int = Field(..., description="对比目标版本号")
    diffs: List[PromptTemplateVersionDiff] = Field(..., description="差异列表")
