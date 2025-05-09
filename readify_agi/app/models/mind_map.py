from pydantic import BaseModel, ConfigDict
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Text, ForeignKey, Index
from app.core.database import Base
from datetime import datetime

class MindMapDB(Base):
    """思维导图数据库模型"""
    __tablename__ = "mind_map"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="思维导图ID")
    project_id = Column(BigInteger, nullable=False, comment="工程id")
    file_id = Column(BigInteger, nullable=False, comment="所属文件ID")
    title = Column(String(255), nullable=False, comment="思维导图标题")
    type = Column(String(10), nullable=False, comment="笔记类型")
    description = Column(Text, nullable=True, comment="思维导图描述")
    user_id = Column(BigInteger, nullable=False, comment="创建者用户ID")
    created_at = Column(BigInteger, nullable=False, comment="创建时间")
    updated_at = Column(BigInteger, nullable=False, comment="更新时间")
    is_deleted = Column(Boolean, nullable=False, default=False, comment="逻辑删除标记，0-未删除，1-已删除")
    
    # 索引
    __table_args__ = (
        Index('idx_user_id', user_id),
    )
    
    def __repr__(self):
        return f"<MindMap(id={self.id}, title={self.title})>"


class MindMapCreate(BaseModel):
    """创建思维导图请求模型"""
    project_id: int
    file_id: int
    title: str
    type: str
    description: Optional[str] = None
    user_id: int


class MindMapResponse(BaseModel):
    """思维导图响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    file_id: int
    title: str
    type: str
    description: Optional[str] = None
    user_id: int
    created_at: int
    updated_at: int 