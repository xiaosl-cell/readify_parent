from sqlalchemy import Column, BigInteger, String, Boolean
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from app.core.database import Base

class FileDB(Base):
    """文件数据库模型"""
    __tablename__ = "file"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    original_name = Column(String(255), nullable=False, comment="原始文件名")
    storage_name = Column(String(100), nullable=False, comment="存储文件名")
    size = Column(BigInteger, nullable=False, comment="文件大小(字节)")
    mime_type = Column(String(100), comment="文件MIME类型")
    storage_path = Column(String(500), nullable=False, comment="存储路径")
    md5 = Column(String(32), comment="文件MD5值")
    create_time = Column(BigInteger, nullable=False, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, comment="更新时间")
    deleted = Column(Boolean, nullable=False, default=False, comment="是否删除")
    vectorized = Column(Boolean, nullable=False, default=False, comment="是否已向量化")

class FileBase(BaseModel):
    """文件基础模型"""
    model_config = ConfigDict(from_attributes=True)
    
    original_name: str
    storage_name: str
    size: int
    mime_type: Optional[str] = None
    storage_path: str
    md5: Optional[str] = None
    
class FileCreate(FileBase):
    """文件创建模型"""
    pass

class FileResponse(FileBase):
    """文件响应模型"""
    id: int
    create_time: int
    update_time: int
    deleted: bool = False
    vectorized: bool = False 