from typing import List
import os
from llama_cloud_services import LlamaParse
from llama_index.core import Document
from app.core.config import settings

class LlamaParseService:
    def __init__(self):
        """
        初始化LlamaParse服务
        """
        self.parser = LlamaParse(api_key=settings.LLAMA_PARSE_API_KEY)
        
    async def parse_file(self, file_path: str) -> List[Document]:
        """
        解析文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Document: 解析后的文档对象
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        documents = await self.parser.aload_data(file_path)
        if not documents:
            raise ValueError(f"文件解析失败: {file_path}")
        return documents  # 返回第一个文档
