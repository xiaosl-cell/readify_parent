from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Text, ForeignKey, Index
from app.core.database import Base
from datetime import datetime

class MindMapNodeDB(Base):
    """思维导图节点数据库模型"""
    __tablename__ = "mind_map_node"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="节点唯一标识")
    project_id = Column(BigInteger, nullable=True, comment="工程id")
    mind_map_id = Column(BigInteger, nullable=False, comment="所属思维导图ID")
    file_id = Column(BigInteger, nullable=False, comment="所属文件ID")
    parent_id = Column(BigInteger, nullable=True, comment="父节点ID，根节点为NULL")
    content = Column(Text, nullable=True, comment="节点内容")
    sequence = Column(Integer, nullable=False, default=0, comment="同级节点间的排序顺序")
    level = Column(Integer, nullable=False, default=0, comment="节点层级，根节点为0")
    created_time = Column(BigInteger, nullable=False, comment="创建时间")
    updated_time = Column(BigInteger, nullable=False, comment="更新时间")
    deleted = Column(Boolean, nullable=False, default=False, comment="是否删除，0-未删除，1-已删除")
    
    # 索引
    __table_args__ = (
        Index('idx_file_id', file_id),
        Index('idx_parent_id', parent_id),
        Index('idx_sort', file_id, parent_id, sequence)
    )
    
    def __repr__(self):
        return f"<MindMapNode(id={self.id}, file_id={self.file_id})>"


class MindMapNodeCreate(BaseModel):
    """创建思维导图节点请求模型"""
    project_id: Optional[int] = None
    mind_map_id: int
    file_id: int
    parent_id: Optional[int] = None
    content: Optional[str] = None
    sequence: int = 0
    level: int = 0


class MindMapNodeResponse(BaseModel):
    """思维导图节点响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: Optional[int] = None
    mind_map_id: int
    file_id: int
    parent_id: Optional[int] = None
    content: Optional[str] = None
    sequence: int
    level: int
    created_time: int
    updated_time: int


class MindMapNodeTreeResponse(MindMapNodeResponse):
    """思维导图节点树响应模型"""
    children: List['MindMapNodeTreeResponse'] = [] 