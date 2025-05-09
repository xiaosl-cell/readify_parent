from typing import List
from app.services.text_workflow_service import TextWorkflowService

class TextRepairService:
    """文本修复服务"""
    
    def __init__(self):
        self.workflow_service = TextWorkflowService()
        
    async def repair_text(self, text: str) -> List[str]:
        """
        修复文本内容
        
        Args:
            text: 需要修复的文本内容
            
        Returns:
            str: 修复后的文本内容
        """
        # 调用工作流服务进行文本修复
        result = await self.workflow_service.text_repair(text)
        
        # 返回修复后的文本
        return result.get("paragraphs")
