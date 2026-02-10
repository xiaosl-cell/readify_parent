"""
Prompt Use Case database model
"""
from sqlalchemy import Column, String, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseEntity, AuditMixin


class PromptUseCase(BaseEntity, AuditMixin):
    """
    提示词模板用例数据库模型
    """
    __tablename__ = "eval_prompt_use_cases"

    use_case_name = Column(String(255), nullable=False, comment="用例名称")
    template_id = Column(String(36), nullable=False, index=True, comment="关联的提示词模板ID")
    template_variables = Column(JSON, nullable=True, comment="用于填充模板的变量（JSON格式）")
    rendered_system_prompt = Column(Text, nullable=True, comment="渲染后的系统提示词最终文本")
    rendered_user_prompt = Column(Text, nullable=True, comment="渲染后的用户提示词最终文本")
    reference_answer = Column(Text, nullable=True, comment="参考答案")
    remarks = Column(Text, nullable=True, comment="备注信息")

    # 关系（仅逻辑关联，不在数据库层面创建外键约束）
    template = relationship("PromptTemplate", foreign_keys=[template_id], primaryjoin="PromptUseCase.template_id==PromptTemplate.id", backref="use_cases")

    def __repr__(self):
        return f"<PromptUseCase(id={self.id}, use_case_name='{self.use_case_name}', template_id='{self.template_id}')>"

