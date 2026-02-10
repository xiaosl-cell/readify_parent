"""
AI Model endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ai_model import (
    AIModelCreate, AIModelUpdate, AIModelResponse, AIModelListResponse,
    ChatCompletionRequest, ChatCompletionResponse
)
from app.services.ai_model import AIModelService
from app.models.ai_model import ModelCategory

router = APIRouter()


def get_ai_model_service(db: Session = Depends(get_db)) -> AIModelService:
    """
    Dependency to get AIModelService instance
    
    Args:
        db: Database session
        
    Returns:
        AIModelService instance
    """
    return AIModelService(db)


@router.post("", response_model=AIModelResponse, status_code=201)
def create_model(
    model_in: AIModelCreate,
    service: AIModelService = Depends(get_ai_model_service)
):
    """
    Create a new AI model
    
    Args:
        model_in: AI model creation data
        service: AI model service
        
    Returns:
        Created AI model
        
    Raises:
        HTTPException: If model_id already exists
    """
    return service.create_model(model_in)


@router.get("/{model_id}", response_model=AIModelResponse)
def get_model(
    model_id: str,
    service: AIModelService = Depends(get_ai_model_service)
):
    """
    Get AI model by ID
    
    Args:
        model_id: AI model ID
        service: AI model service
        
    Returns:
        AI model details
        
    Raises:
        HTTPException: If model not found
    """
    model = service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="找不到 AI 模型")
    return model


@router.get("", response_model=AIModelListResponse)
def get_models(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    enabled_only: bool = Query(False, description="Return only enabled models"),
    search: Optional[str] = Query(None, description="Search by model name"),
    category: Optional[ModelCategory] = Query(None, description="Filter by model category (Reasoning/Instruction)"),
    service: AIModelService = Depends(get_ai_model_service)
):
    """
    Get all AI models with pagination and optional filters
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        enabled_only: Return only enabled models
        search: Search by model name (partial match)
        category: Filter by model category (Reasoning/Instruction)
        service: AI model service
        
    Returns:
        List of AI models with pagination
    """
    if search:
        return service.search_models(name=search, skip=skip, limit=limit, enabled_only=enabled_only, category=category)
    if enabled_only:
        return service.get_enabled_models(skip=skip, limit=limit, category=category)
    return service.get_models(skip=skip, limit=limit, category=category)


@router.put("/{model_id}", response_model=AIModelResponse)
def update_model(
    model_id: str,
    model_in: AIModelUpdate,
    service: AIModelService = Depends(get_ai_model_service)
):
    """
    Update an AI model
    
    Args:
        model_id: AI model ID
        model_in: Updated AI model data
        service: AI model service
        
    Returns:
        Updated AI model
        
    Raises:
        HTTPException: If model not found or model_id conflicts
    """
    model = service.update_model(model_id, model_in)
    if not model:
        raise HTTPException(status_code=404, detail="找不到 AI 模型")
    return model


@router.delete("/{model_id}", status_code=204)
def delete_model(
    model_id: str,
    service: AIModelService = Depends(get_ai_model_service)
):
    """
    Delete an AI model
    
    Args:
        model_id: AI model ID
        service: AI model service
        
    Raises:
        HTTPException: If model not found
    """
    success = service.delete_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="找不到 AI 模型")


@router.post("/{model_id}/chat", response_model=ChatCompletionResponse)
async def chat_completion(
    model_id: str,
    request: ChatCompletionRequest,
    service: AIModelService = Depends(get_ai_model_service)
):
    """
    调用大模型生成文本（中转接口，避免前端跨域问题）
    
    Args:
        model_id: AI模型ID
        request: 聊天请求数据
        service: AI模型服务
        
    Returns:
        生成的文本响应
        
    Raises:
        HTTPException: 如果模型不存在、未启用或调用失败
    """
    return await service.chat_completion(model_id, request)

