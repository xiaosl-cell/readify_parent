"""
AI Model schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.base import BaseEntity, BaseCreateSchema, BaseUpdateSchema, BaseListResponse
from app.models.ai_model import ModelCategory


class AIModelBase(BaseModel):
    """AI模型基础 Schema"""
    model_name: str = Field(..., min_length=1, max_length=255, description="模型名称")
    model_id: str = Field(..., min_length=1, max_length=255, description="模型ID")
    api_endpoint: str = Field(..., min_length=1, max_length=500, description="访问接口")
    api_key: Optional[str] = Field(None, max_length=500, description="API密钥")
    is_enabled: bool = Field(True, description="状态（是否启用）")
    category: ModelCategory = Field(ModelCategory.INSTRUCTION, description="模型类别（Reasoning/Instruction）")


class AIModelCreate(AIModelBase, BaseCreateSchema):
    """创建AI模型的 Schema"""
    pass


class AIModelUpdate(BaseUpdateSchema):
    """更新AI模型的 Schema"""
    model_name: Optional[str] = Field(None, min_length=1, max_length=255, description="模型名称")
    model_id: Optional[str] = Field(None, min_length=1, max_length=255, description="模型ID")
    api_endpoint: Optional[str] = Field(None, min_length=1, max_length=500, description="访问接口")
    api_key: Optional[str] = Field(None, max_length=500, description="API密钥")
    is_enabled: Optional[bool] = Field(None, description="状态（是否启用）")
    category: Optional[ModelCategory] = Field(None, description="模型类别（Reasoning/Instruction）")


class AIModelResponse(AIModelBase, BaseEntity):
    """AI模型响应 Schema，继承基础实体"""
    
    class Config:
        from_attributes = True


class AIModelListResponse(BaseListResponse):
    """AI模型列表响应 Schema"""
    items: List[AIModelResponse] = Field(..., description="AI模型列表")


class ChatMessage(BaseModel):
    """聊天消息 Schema"""
    role: str = Field(..., description="消息角色 (system/user/assistant)")
    content: str = Field(..., description="消息内容")


class ChatCompletionRequest(BaseModel):
    """调用大模型的请求 Schema"""
    messages: List[ChatMessage] = Field(..., description="消息列表")
    model: Optional[str] = Field(None, description="模型ID（可选，如果不提供则使用AI模型配置的model_id）")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    temperature: Optional[float] = Field(None, description="温度参数")
    top_p: Optional[float] = Field(None, description="Top-p参数")
    top_k: Optional[int] = Field(None, description="Top-k参数")


class ChatCompletionResponse(BaseModel):
    """调用大模型的响应 Schema"""
    content: str = Field(..., description="生成的文本内容")
    raw_response: Optional[dict] = Field(None, description="原始API响应（用于调试）")
