from sqlalchemy import Column, BigInteger, String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.core.database import Base

class RepairDocumentDB(Base):
    """修复后的文档内容数据库模型"""
    __tablename__ = "repair_document"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    file_id = Column(BigInteger, ForeignKey("file.id"), nullable=False, comment="关联的文件ID")
    content = Column(Text, nullable=False, comment="修复后的文本内容")
    sequence = Column(Integer, nullable=False, comment="文档块序号")
    create_time = Column(BigInteger, nullable=False, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, comment="更新时间")
    deleted = Column(Boolean, nullable=False, default=False, comment="是否删除")
    
    # 删除关联关系
    # file = relationship("FileDB", back_populates="repair_documents")

class RepairDocumentBase(BaseModel):
    """修复文档基础模型"""
    model_config = ConfigDict(from_attributes=True)
    
    file_id: int
    content: str
    sequence: int
    
class RepairDocumentCreate(RepairDocumentBase):
    """修复文档创建模型"""
    pass

class RepairDocumentResponse(RepairDocumentBase):
    """修复文档响应模型"""
    id: int
    create_time: int
    update_time: int
    deleted: bool = False 