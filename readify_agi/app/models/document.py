from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, BigInteger, Text, Integer, ForeignKey, Boolean

from app.core.database import Base


class DocumentDB(Base):
    """文档解析内容数据库模型"""
    __tablename__ = "document"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    file_id = Column(BigInteger, ForeignKey("file.id"), nullable=False, comment="关联的文件ID")
    content = Column(Text, nullable=False, comment="解析的文本内容")
    label = Column(Text, nullable=True, comment="文本内容概括标签")
    sequence = Column(Integer, nullable=False, comment="文档块序号")
    create_time = Column(BigInteger, nullable=False, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, comment="更新时间")
    deleted = Column(Boolean, nullable=False, default=False, comment="是否删除")
    
    # 删除关联关系
    # file = relationship("FileDB", back_populates="documents")

class DocumentBase(BaseModel):
    """文档基础模型"""
    model_config = ConfigDict(from_attributes=True)
    
    file_id: int
    content: str
    sequence: int
    label: str = None
    
class DocumentCreate(DocumentBase):
    """文档创建模型"""
    pass

class DocumentResponse(DocumentBase):
    """文档响应模型"""
    id: int
    create_time: int
    update_time: int
    deleted: bool = False 