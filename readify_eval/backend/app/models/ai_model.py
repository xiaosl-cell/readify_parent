"""
AI Model database model
"""
import enum
from sqlalchemy import Column, String, Boolean, Enum

from app.models.base import BaseEntity, AuditMixin


class ModelCategory(str, enum.Enum):
    """模型类别枚举"""
    REASONING = "Reasoning"
    INSTRUCTION = "Instruction"


class AIModel(BaseEntity, AuditMixin):
    """
    AI模型数据库模型
    """
    __tablename__ = "eval_ai_models"

    model_name = Column(String(255), nullable=False, index=True, comment="模型名称")
    model_id = Column(String(255), nullable=False, unique=True, index=True, comment="模型ID")
    api_endpoint = Column(String(500), nullable=False, comment="访问接口")
    api_key = Column(String(500), nullable=True, comment="API密钥")
    is_enabled = Column(Boolean, default=True, comment="状态（是否启用）")
    category = Column(Enum(ModelCategory), nullable=False, default=ModelCategory.INSTRUCTION, comment="模型类别")

    def __repr__(self):
        return f"<AIModel(id={self.id}, model_name='{self.model_name}', model_id='{self.model_id}')>"

