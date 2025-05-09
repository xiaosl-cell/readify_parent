from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from pydantic import BaseModel

from app.services.text_workflow_service import TextWorkflowService

router = APIRouter()

class TextRequest(BaseModel):
    text: str


@router.post("/process", response_model=Dict[str, Any])
async def process_text(
    request: TextRequest,
    service: TextWorkflowService = Depends(lambda: TextWorkflowService())
) -> Dict[str, Any]:
    """
    处理文本的完整工作流，包括：
    1. 检查格式问题
    2. 修复格式
    3. 语义分段
    """
    return await service.text_repair(request.text)