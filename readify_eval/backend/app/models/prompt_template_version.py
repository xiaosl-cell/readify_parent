"""
Prompt Template Version database model
"""
from sqlalchemy import Column, String, Text, JSON, Integer

from app.models.base import BaseEntity, AuditMixin


class PromptTemplateVersion(BaseEntity, AuditMixin):
    """
    提示词模板版本历史数据库模型
    """
    __tablename__ = "eval_prompt_template_versions"

    template_id = Column(String(36), nullable=False, index=True, comment="关联的提示词模板ID")
    version = Column(Integer, nullable=False, comment="版本号")
    change_log = Column(Text, nullable=True, comment="变更说明")

    # 版本快照字段（记录该版本时的模板内容）
    template_code = Column(String(100), nullable=True, comment="模板编码")
    template_name = Column(String(255), nullable=False, comment="提示词模板名称")
    system_prompt = Column(Text, nullable=True, comment="系统提示词模板")
    user_prompt = Column(Text, nullable=True, comment="用户提示词模板")
    function_category = Column(String(255), nullable=True, comment="所属功能")
    remarks = Column(Text, nullable=True, comment="备注")
    max_tokens = Column(String(50), nullable=True, comment="最大生成token数")
    top_p = Column(String(50), nullable=True, comment="核采样参数")
    top_k = Column(String(50), nullable=True, comment="top-k采样参数")
    temperature = Column(String(50), nullable=True, comment="温度参数")
    evaluation_strategies = Column(JSON, nullable=True, comment="评估策略列表")
    owner = Column(String(255), nullable=True, comment="负责人")
    qc_number = Column(String(255), nullable=True, comment="QC号")
    prompt_source = Column(String(255), nullable=True, comment="提示词来源")

    def __repr__(self):
        return f"<PromptTemplateVersion(id={self.id}, template_id='{self.template_id}', version={self.version})>"
