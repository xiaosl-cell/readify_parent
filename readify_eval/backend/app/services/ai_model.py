"""
AI Model service
"""
import json
import httpx
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.ai_model import AIModelRepository
from app.schemas.ai_model import (
    AIModelCreate, AIModelUpdate, AIModelResponse, AIModelListResponse,
    ChatCompletionRequest, ChatCompletionResponse, ChatMessage
)
from app.models.ai_model import ModelCategory


class AIModelService:
    """
    Business logic for AI Model operations
    """
    
    def __init__(self, db: Session):
        self.repository = AIModelRepository(db)
    
    def create_model(self, model_in: AIModelCreate) -> AIModelResponse:
        """
        Create a new AI model
        
        Args:
            model_in: AI model creation data
            
        Returns:
            Created AI model
            
        Raises:
            HTTPException: If model_id already exists
        """
        # Check if model_id already exists
        existing = self.repository.get_by_model_id(model_in.model_id)
        if existing:
            raise HTTPException(status_code=400, detail=f"模型 ID '{model_in.model_id}' 已存在")
        
        model_dict = model_in.model_dump()
        model = self.repository.create(model_dict)
        return AIModelResponse.model_validate(model)
    
    def get_model(self, model_id: str) -> Optional[AIModelResponse]:
        """
        Get AI model by ID
        
        Args:
            model_id: AI model ID
            
        Returns:
            AI model or None
        """
        model = self.repository.get(model_id)
        if model:
            return AIModelResponse.model_validate(model)
        return None
    
    def get_model_by_model_id(self, model_id: str) -> Optional[AIModelResponse]:
        """
        Get AI model by model_id field
        
        Args:
            model_id: Model ID field
            
        Returns:
            AI model or None
        """
        model = self.repository.get_by_model_id(model_id)
        if model:
            return AIModelResponse.model_validate(model)
        return None
    
    def get_models(self, skip: int = 0, limit: int = 100, category: Optional[ModelCategory] = None) -> AIModelListResponse:
        """
        Get all AI models with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            category: Filter by model category
            
        Returns:
            List of AI models with total count
        """
        models = self.repository.get_all(skip=skip, limit=limit, category=category)
        total = self.repository.count()
        
        return AIModelListResponse(
            total=total,
            items=[AIModelResponse.model_validate(m) for m in models]
        )
    
    def get_enabled_models(self, skip: int = 0, limit: int = 100, category: Optional[ModelCategory] = None) -> AIModelListResponse:
        """
        Get all enabled AI models
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            category: Filter by model category
            
        Returns:
            List of enabled AI models
        """
        models = self.repository.get_enabled(skip=skip, limit=limit, category=category)
        total = len(models)
        
        return AIModelListResponse(
            total=total,
            items=[AIModelResponse.model_validate(m) for m in models]
        )
    
    def search_models(self, name: str, skip: int = 0, limit: int = 100, enabled_only: bool = False, category: Optional[ModelCategory] = None) -> AIModelListResponse:
        """
        Search AI models by name
        
        Args:
            name: Model name (partial match)
            skip: Number of records to skip
            limit: Maximum number of records to return
            enabled_only: Filter only enabled models
            category: Filter by model category
            
        Returns:
            List of matching AI models
        """
        models = self.repository.search_by_name(name, skip=skip, limit=limit, enabled_only=enabled_only, category=category)
        total = len(models)
        
        return AIModelListResponse(
            total=total,
            items=[AIModelResponse.model_validate(m) for m in models]
        )
    
    def update_model(self, model_id: str, model_in: AIModelUpdate) -> Optional[AIModelResponse]:
        """
        Update an AI model
        
        Args:
            model_id: AI model ID
            model_in: Updated AI model data
            
        Returns:
            Updated AI model or None
            
        Raises:
            HTTPException: If model_id conflicts with existing model
        """
        # If updating model_id, check for conflicts
        if model_in.model_id:
            existing = self.repository.get_by_model_id(model_in.model_id)
            if existing and existing.id != model_id:
                raise HTTPException(status_code=400, detail=f"模型 ID '{model_in.model_id}' 已存在")
        
        model_dict = model_in.model_dump(exclude_unset=True)
        model = self.repository.update(model_id, model_dict)
        if model:
            return AIModelResponse.model_validate(model)
        return None
    
    def delete_model(self, model_id: str) -> bool:
        """
        Delete an AI model
        
        Args:
            model_id: AI model ID
            
        Returns:
            True if deleted, False if not found
        """
        return self.repository.delete(model_id)
    
    async def chat_completion(self, model_id: str, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        调用大模型生成文本（中转方法）
        
        Args:
            model_id: AI模型ID
            request: 聊天请求数据
            
        Returns:
            生成的文本响应
            
        Raises:
            HTTPException: 如果模型不存在或调用失败
        """  
        # 获取AI模型信息
        model = self.repository.get(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"找不到 ID 为 '{model_id}' 的 AI 模型")
        
        if not model.is_enabled:
            raise HTTPException(status_code=400, detail=f"AI 模型 '{model.model_name}' 未启用")
        
        # 构建请求数据
        request_data = {
            "model": request.model or model.model_name,
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages]
        }
        
        # 添加可选参数
        if request.max_tokens is not None:
            request_data['max_tokens'] = request.max_tokens
        if request.temperature is not None:
            request_data['temperature'] = request.temperature
        if request.top_p is not None:
            request_data['top_p'] = request.top_p
        if request.top_k is not None:
            request_data['top_k'] = request.top_k
        
        # 构建API端点URL
        api_endpoint = model.api_endpoint.rstrip('/')
        if not api_endpoint.endswith('/v1/chat/completions'):
            if api_endpoint.endswith('/v1'):
                api_url = f"{api_endpoint}/chat/completions"
            elif api_endpoint.endswith('/chat/completions'):
                api_url = api_endpoint
            else:
                api_url = f"{api_endpoint}/v1/chat/completions"
        else:
            api_url = api_endpoint
        
        # 构建请求头
        headers = {"Content-Type": "application/json"}
        if model.api_key:
            headers["Authorization"] = f"Bearer {model.api_key}"
        
        try:
            # 调用AI模型API（使用300秒超时，与test_task.py保持一致）
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    api_url,
                    json=request_data,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                # 提取生成的文本内容
                content = ""
                if result.get("choices") and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice:
                        content = choice["message"].get("content", "")
                    elif "text" in choice:
                        content = choice["text"]
                elif result.get("content"):
                    content = result["content"]
                elif result.get("text"):
                    content = result["text"]
                elif result.get("message") and result["message"].get("content"):
                    content = result["message"]["content"]
                else:
                    # 如果无法提取，返回整个响应的JSON字符串
                    content = json.dumps(result, ensure_ascii=False)
                
                return ChatCompletionResponse(
                    content=content,
                    raw_response=result
                )
        except httpx.HTTPStatusError as e:
            error_detail = f"AI模型调用失败 (HTTP {e.response.status_code})"
            try:
                error_body = e.response.json()
                if "error" in error_body:
                    error_detail = error_body["error"].get("message", error_detail)
            except:
                error_detail = f"{error_detail}: {e.response.text}"
            raise HTTPException(status_code=502, detail=error_detail)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="AI模型调用超时（超过300秒）")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI模型调用失败: {str(e)}")

