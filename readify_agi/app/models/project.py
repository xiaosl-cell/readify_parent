from pydantic import BaseModel
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ProjectDB(Base):
    """项目数据库模型"""
    __tablename__ = "project"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    name = Column(String(100), nullable=False, comment="工程名称")
    description = Column(Text, nullable=True, comment="工程描述")
    create_time = Column(BigInteger, nullable=False, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, comment="更新时间")
    deleted = Column(Boolean, default=False, nullable=False, comment="是否删除")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name})>"


class ProjectCreate(BaseModel):
    """创建项目请求模型"""
    user_id: int
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """项目响应模型"""
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    create_time: int
    update_time: int
    
    class Config:
        from_attributes = True 