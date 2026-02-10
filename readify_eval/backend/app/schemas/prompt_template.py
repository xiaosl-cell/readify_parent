"""
Prompt Template schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.schemas.base import BaseEntity, BaseCreateSchema, BaseUpdateSchema, BaseListResponse
from app.models.evaluation import EvaluationStrategy

# 定义特殊标记常量
USE_SYSTEM_DEFAULT = "__USE_SYSTEM_DEFAULT__"
NONE_VALUE = "__NONE__"


def validate_llm_param(value: Optional[str], param_type: str, min_val: Optional[float] = None, max_val: Optional[float] = None) -> Optional[str]:
    """
    验证 LLM 参数值
    
    Args:
        value: 参数值
        param_type: 参数类型 ('int' 或 'float')
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        验证后的值
        
    Raises:
        ValueError: 如果值无效
    """
    if value is None:
        return None
    
    # 允许特殊标记
    if value in [USE_SYSTEM_DEFAULT, NONE_VALUE]:
        return value
    
    # 验证具体数值
    try:
        if param_type == 'int':
            num_val = int(value)
        elif param_type == 'float':
            num_val = float(value)
        else:
            raise ValueError(f"不支持的参数类型: {param_type}")
        
        # 范围检查
        if min_val is not None and num_val < min_val:
            raise ValueError(f"值 {num_val} 小于最小值 {min_val}")
        if max_val is not None and num_val > max_val:
            raise ValueError(f"值 {num_val} 大于最大值 {max_val}")
        
        return value
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"无效的{param_type}值: {value}")
        raise


class PromptTemplateBase(BaseModel):
    """提示词模板基础 Schema"""
    template_name: str = Field(..., min_length=1, max_length=255, description="提示词模板名称")
    system_prompt: Optional[str] = Field(None, description="系统提示词模板")
    user_prompt: Optional[str] = Field(None, description="用户提示词模板")
    function_category: Optional[str] = Field(None, max_length=255, description="所属功能")
    remarks: Optional[str] = Field(None, description="备注")
    
    # LLM参数：字符串类型，支持特殊标记或具体数值
    max_tokens: Optional[str] = Field(
        None, 
        max_length=50,
        description="最大生成token数。可以是：'__USE_SYSTEM_DEFAULT__'（使用系统默认）、'__NONE__'（不设置）或具体整数值（如'100'）"
    )
    top_p: Optional[str] = Field(
        None, 
        max_length=50,
        description="核采样参数。可以是：'__USE_SYSTEM_DEFAULT__'（使用系统默认）、'__NONE__'（不设置）或0.0-1.0之间的浮点数（如'0.9'）"
    )
    top_k: Optional[str] = Field(
        None, 
        max_length=50,
        description="top-k采样参数。可以是：'__USE_SYSTEM_DEFAULT__'（使用系统默认）、'__NONE__'（不设置）或非负整数（如'50'）"
    )
    temperature: Optional[str] = Field(
        None, 
        max_length=50,
        description="温度参数。可以是：'__USE_SYSTEM_DEFAULT__'（使用系统默认）、'__NONE__'（不设置）或0.0-2.0之间的浮点数（如'0.7'）"
    )
    
    # 评估相关字段  
    evaluation_strategies: Optional[List[EvaluationStrategy]] = Field(
        None,
        description="评估策略列表（可多选）：精确匹配、JSON键匹配、答案准确率、事实正确性、语义相似性、BLEU、ROUGE、CHRF"
    )
    
    # 新增字段
    owner: Optional[str] = Field(None, max_length=255, description="负责人")
    qc_number: Optional[str] = Field(None, max_length=255, description="QC号")
    prompt_source: Optional[str] = Field(None, max_length=255, description="提示词来源")

    @field_validator('max_tokens')
    @classmethod
    def validate_max_tokens(cls, v: Optional[str]) -> Optional[str]:
        """验证 max_tokens"""
        return validate_llm_param(v, 'int', min_val=1)
    
    @field_validator('top_p')
    @classmethod
    def validate_top_p(cls, v: Optional[str]) -> Optional[str]:
        """验证 top_p"""
        return validate_llm_param(v, 'float', min_val=0.0, max_val=1.0)
    
    @field_validator('top_k')
    @classmethod
    def validate_top_k(cls, v: Optional[str]) -> Optional[str]:
        """验证 top_k"""
        return validate_llm_param(v, 'int', min_val=0)
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: Optional[str]) -> Optional[str]:
        """验证 temperature"""
        return validate_llm_param(v, 'float', min_val=0.0, max_val=2.0)


class PromptTemplateCreate(PromptTemplateBase, BaseCreateSchema):
    """创建提示词模板的 Schema"""
    pass


class PromptTemplateUpdate(BaseUpdateSchema):
    """更新提示词模板的 Schema"""
    template_name: Optional[str] = Field(None, min_length=1, max_length=255, description="提示词模板名称")
    system_prompt: Optional[str] = Field(None, description="系统提示词模板")
    user_prompt: Optional[str] = Field(None, description="用户提示词模板")
    function_category: Optional[str] = Field(None, max_length=255, description="所属功能")
    remarks: Optional[str] = Field(None, description="备注")
    max_tokens: Optional[str] = Field(None, max_length=50, description="最大生成token数")
    top_p: Optional[str] = Field(None, max_length=50, description="核采样参数")
    top_k: Optional[str] = Field(None, max_length=50, description="top-k采样参数")
    temperature: Optional[str] = Field(None, max_length=50, description="温度参数")
    evaluation_strategies: Optional[List[EvaluationStrategy]] = Field(None, description="评估策略列表")
    owner: Optional[str] = Field(None, max_length=255, description="负责人")
    qc_number: Optional[str] = Field(None, max_length=255, description="QC号")
    prompt_source: Optional[str] = Field(None, max_length=255, description="提示词来源")

    @field_validator('max_tokens')
    @classmethod
    def validate_max_tokens(cls, v: Optional[str]) -> Optional[str]:
        """验证 max_tokens"""
        return validate_llm_param(v, 'int', min_val=1)
    
    @field_validator('top_p')
    @classmethod
    def validate_top_p(cls, v: Optional[str]) -> Optional[str]:
        """验证 top_p"""
        return validate_llm_param(v, 'float', min_val=0.0, max_val=1.0)
    
    @field_validator('top_k')
    @classmethod
    def validate_top_k(cls, v: Optional[str]) -> Optional[str]:
        """验证 top_k"""
        return validate_llm_param(v, 'int', min_val=0)
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: Optional[str]) -> Optional[str]:
        """验证 temperature"""
        return validate_llm_param(v, 'float', min_val=0.0, max_val=2.0)


class PromptTemplateResponse(PromptTemplateBase, BaseEntity):
    """提示词模板响应 Schema，继承基础实体"""
    
    class Config:
        from_attributes = True


class PromptTemplateListResponse(BaseListResponse):
    """提示词模板列表响应 Schema"""
    items: List[PromptTemplateResponse] = Field(..., description="提示词模板列表")
