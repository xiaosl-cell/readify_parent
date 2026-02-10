"""
Example model - you can delete this file and create your own models
"""
from sqlalchemy import Column, String, Boolean, Text

from app.models.base import BaseEntity, AuditMixin


class ExampleModel(BaseEntity, AuditMixin):
    """
    示例数据库模型，继承基础实体类
    """
    __tablename__ = "eval_examples"

    title = Column(String(255), nullable=False, index=True, comment="标题")
    description = Column(Text, nullable=True, comment="描述")
    is_active = Column(Boolean, default=True, comment="是否激活")

    def __repr__(self):
        return f"<ExampleModel(id={self.id}, title='{self.title}')>"

