from typing import List
from fastapi import HTTPException
from app.models.document import DocumentCreate
from app.repositories.document_repository import DocumentRepository
from app.services.llama_parse_service import LlamaParseService
from app.repositories.file_repository import FileRepository
import json
from app.core.config import settings
import os
from pathlib import Path

class DocumentService:
    """文档服务层"""
    
    def __init__(
        self,
        document_repository: DocumentRepository,
        file_repository: FileRepository,
        llama_parse_service: LlamaParseService
    ):
        self.document_repository = document_repository
        self.file_repository = file_repository
        self.llama_parse_service = llama_parse_service
        
    async def parse_and_save(self, file_id: int) -> None:
        """
        解析文件并保存到数据库
        
        Args:
            file_id: 文件ID
        """
        # 获取文件信息
        file = await self.file_repository.get_file_by_id(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
            
        # 解析文件
        documents = await self.llama_parse_service.parse_file(file.storage_path)
        
        print(f"解析文件 '{file.original_name}' (ID:{file_id}) 得到 {len(documents)} 个文档块")
        
        # 创建文档记录
        doc_creates = []
        for i, doc in enumerate(documents):
            content = doc.get_content()
            if not content:  # 跳过空内容
                continue
                
            # 为文档内容生成标签
            print(f"为文档块 {i+1}/{len(documents)} 生成标签...")
            label = await self._generate_label_with_4o_mini(content)
                
            doc_create = DocumentCreate(
                file_id=file_id,
                content=content,
                sequence=i,
                label=label  # 添加生成的标签
            )
            doc_creates.append(doc_create)
            
        # 批量保存到数据库
        if doc_creates:
            docs = await self.document_repository.create_many(doc_creates)
            print(f"成功保存 {len(docs)} 个文档块到数据库，并生成了标签")
        else:
            print("没有有效的文档内容需要保存")
            
    async def get_file_documents(self, file_id: int) -> List[str]:
        """
        获取文件的所有文档内容
        
        Args:
            file_id: 文件ID
            
        Returns:
            List[str]: 文档内容列表
        """
        documents = await self.document_repository.get_by_file_id(file_id)
        return [doc.content for doc in documents]
        
    async def generate_label(self, document_id: int) -> str:
        """
        为文档生成标签
        
        Args:
            document_id: 文档ID
            
        Returns:
            str: 生成的标签
        """
        # 获取文档
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
            
        # 调用4o-mini模型生成标签
        label = await self._generate_label_with_4o_mini(document.content)
        
        # 更新文档标签
        await self.document_repository.update_label(document_id, label)
        
        return label
        
    async def generate_labels_for_file(self, file_id: int, force_regenerate: bool = False) -> int:
        """
        为文件的所有文档生成标签
        
        Args:
            file_id: 文件ID
            force_regenerate: 是否强制重新生成已有标签
            
        Returns:
            int: 成功生成标签的文档数量
        """
        # 获取文件信息
        file = await self.file_repository.get_file_by_id(file_id)
        if not file:
            print(f"文件ID:{file_id} 不存在")
            return 0
            
        print(f"开始处理文件: '{file.original_name}' (ID:{file_id})")
        
        # 获取文件的所有文档
        documents = await self.document_repository.get_by_file_id(file_id)
        if not documents:
            print(f"文件ID:{file_id} 没有找到文档")
            return 0
            
        total_docs = len(documents)
        print(f"开始为文件 '{file.original_name}' (ID:{file_id})的{total_docs}个文档生成标签")
        
        # 为每个文档生成标签并更新
        document_ids = []
        labels = []
        
        for idx, doc in enumerate(documents, 1):
            try:
                # 检查文档是否已有标签（如果不是强制重新生成）
                if doc.label and not force_regenerate:
                    print(f"文档 [{idx}/{total_docs}] ID:{doc.id} 已有标签: {doc.label[:30]}...")
                    continue
                    
                print(f"处理文档 [{idx}/{total_docs}] ID:{doc.id}")
                label = await self._generate_label_with_4o_mini(doc.content)
                if label:
                    document_ids.append(doc.id)
                    labels.append(label)
                else:
                    print(f"警告: 文档ID:{doc.id} 生成的标签为空")
                    
                # 每处理10个文档，输出进度
                if idx % 10 == 0 or idx == total_docs:
                    print(f"进度: {idx}/{total_docs} ({idx/total_docs*100:.1f}%)")
                    
            except Exception as e:
                print(f"处理文档ID:{doc.id}时出错: {str(e)}")
                continue
            
        # 批量更新文档标签
        if document_ids:
            updated_count = await self.document_repository.update_many_labels(document_ids, labels)
            print(f"成功更新{updated_count}个文档的标签")
            return updated_count
        else:
            print("没有文档需要更新标签")
            return 0
        
    async def _generate_label_with_4o_mini(self, content: str) -> str:
        """
        使用4o-mini模型生成标签
        
        Args:
            content: 文档内容
            
        Returns:
            str: 生成的标签
        """
        # 导入必要的库
        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate
        
        prompt_template = ""
        # 读取提示词文件
        try:
            # 尝试获取项目根目录
            root_dir = Path(__file__).parent.parent.parent.absolute()
            prompt_file_path = os.path.join(root_dir, "prompt", "label.prompt")
            
            # 尝试打开文件
            with open(prompt_file_path, "r", encoding="utf-8") as f:
                prompt_template = f.read().strip()
                print(f"成功读取提示词文件: {prompt_file_path}")
        except Exception as e:
            print(f"读取提示词文件时出错: {str(e)}")
            print(f"尝试的文件路径: {prompt_file_path}")
            # 使用默认提示词
            prompt_template = "生成描述该文本的标签，概括该文本主要描述的内容，不超过50个字：\n\n文本：{content}"
            print(f"使用默认提示词模板: {prompt_template}")
        
        try:
            # 使用Langchain调用模型
            chat = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.5,
                api_key=settings.OPENAI_API_KEY_CHINA,
                base_url=settings.OPENAI_API_BASE_CHINA,
            )
            
            # 创建聊天提示模板
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个文本标签生成助手，请生成简短的标签来概括文本内容。"),
                ("human", prompt_template)  # 提示词模板中已包含{content}占位符
            ])
            
            # 生成标签，传入变量以替换占位符
            chain = prompt | chat
            response = await chain.ainvoke({"content": content})
            
            # 获取结果
            label = response.content.strip()
            
            # 确保标签不超过50个字符
            if len(label) > 50:
                label = label[:50]
                
            return label
            
        except Exception as e:
            print(f"生成标签时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return "" 