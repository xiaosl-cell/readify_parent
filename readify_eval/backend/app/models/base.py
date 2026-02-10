"""
Base model classes for common fields
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr

from app.core.database import Base


class BaseEntity(Base):
    """
    基础实体类，包含常用字段：
    - id: 字符串类型主键 (UUID)
    - created_at: 创建时间
    - updated_at: 更新时间
    - created_by: 创建人
    - updated_by: 更新人
    """
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        """自动生成表名（将类名转为下划线格式，并添加 eval_ 前缀）"""
        import re
        return 'eval_' + re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
    
    # 字符串类型主键，使用 UUID
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # 用户字段
    created_by = Column(String(36), nullable=True, comment="创建人ID")
    updated_by = Column(String(36), nullable=True, comment="更新人ID")

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"


class AuditMixin:
    """
    审计混入类，提供审计相关方法
    """
    
    def set_created_by(self, user_id: str):
        """设置创建人"""
        self.created_by = user_id
        if not self.updated_by:
            self.updated_by = user_id
    
    def set_updated_by(self, user_id: str):
        """设置更新人"""
        self.updated_by = user_id
    
    def to_dict(self, exclude_fields: set = None):
        """转换为字典"""
        exclude_fields = exclude_fields or set()
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
        return result
