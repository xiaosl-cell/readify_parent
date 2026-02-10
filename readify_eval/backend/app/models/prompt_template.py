"""
Prompt Template database model
"""
from sqlalchemy import Column, String, Text, JSON

from app.models.base import BaseEntity, AuditMixin


class PromptTemplate(BaseEntity, AuditMixin):
    """
    提示词模板数据库模型
    """
    __tablename__ = "eval_prompt_templates"

    template_name = Column(String(255), nullable=False, index=True, comment="提示词模板名称")
    system_prompt = Column(Text, nullable=True, comment="系统提示词模板")
    user_prompt = Column(Text, nullable=True, comment="用户提示词模板")
    function_category = Column(String(255), nullable=True, comment="所属功能")
    remarks = Column(Text, nullable=True, comment="备注")
    max_tokens = Column(String(50), nullable=True, comment="最大生成token数")
    top_p = Column(String(50), nullable=True, comment="核采样参数")
    top_k = Column(String(50), nullable=True, comment="top-k采样参数")
    temperature = Column(String(50), nullable=True, comment="温度参数")
    evaluation_strategies = Column(JSON, nullable=True, comment="评估策略列表（可多选）：精确匹配、JSON键匹配、答案准确率、事实正确性、语义相似性、BLEU、ROUGE")
    owner = Column(String(255), nullable=True, comment="负责人")
    qc_number = Column(String(255), nullable=True, comment="QC号")
    prompt_source = Column(String(255), nullable=True, comment="提示词来源")  

    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, template_name='{self.template_name}')>"
