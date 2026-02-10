"""
System Configuration database model
"""
from sqlalchemy import Column, String, Text

from app.models.base import BaseEntity, AuditMixin


class SystemConfig(BaseEntity, AuditMixin):
    """
    系统配置数据库模型
    """
    __tablename__ = "eval_system_configs"

    config_code = Column(String(255), nullable=False, unique=True, index=True, comment="配置编码")
    config_name = Column(String(255), nullable=False, index=True, comment="配置名称")
    config_description = Column(Text, nullable=True, comment="配置描述")
    config_content = Column(Text, nullable=False, comment="配置内容")

    def __repr__(self):
        return f"<SystemConfig(id={self.id}, config_code='{self.config_code}', config_name='{self.config_name}')>"

