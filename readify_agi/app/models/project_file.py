from sqlalchemy import Column, BigInteger, Boolean
from pydantic import BaseModel, ConfigDict
from app.core.database import Base


class ProjectFileDB(Base):
    """项目文件关联数据库模型"""
    __tablename__ = "project_file"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    project_id = Column(BigInteger, nullable=False, index=True, comment="项目ID")
    user_id = Column(BigInteger, nullable=True, comment="用户ID")
    file_id = Column(BigInteger, nullable=False, index=True, comment="文件ID")
    create_time = Column(BigInteger, nullable=False, comment="创建时间")
    update_time = Column(BigInteger, nullable=False, comment="更新时间")
    deleted = Column(Boolean, nullable=False, default=False, comment="是否删除")


class ProjectFileBase(BaseModel):
    """项目文件关联基础模型"""
    model_config = ConfigDict(from_attributes=True)
    
    project_id: int
    user_id: int = None
    file_id: int


class ProjectFileCreate(ProjectFileBase):
    """项目文件关联创建模型"""
    pass


class ProjectFileResponse(ProjectFileBase):
    """项目文件关联响应模型"""
    id: int
    create_time: int
    update_time: int
    deleted: bool = False 