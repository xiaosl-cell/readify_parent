"""
Evaluation Comparison database models
"""
import enum
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseEntity, AuditMixin


class ComparisonStatus(str, enum.Enum):
    """评估对比状态枚举"""
    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class ResultStatus(str, enum.Enum):
    """评估结果状态枚举"""
    PENDING = "pending"  # 待计算
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败


class EvaluationStrategy(str, enum.Enum):
    """评估策略枚举"""
    EXACT_MATCH = "exact_match"  # 精确匹配 - 与参考答案完全一致
    JSON_KEY_MATCH = "json_key_match"  # JSON键匹配 - 校验输出是否为JSON且键集合与参考一致
    ANSWER_ACCURACY = "answer_accuracy"  # 答案准确率 - LLM评估生成答案与参考答案的语义一致性程度
    FACTUAL_CORRECTNESS = "factual_correctness"  # 事实正确性 - 检查LLM生成的答案与标准答案相比，事实是否正确
    SEMANTIC_SIMILARITY = "semantic_similarity"  # 语义相似性 - 使用BERT系列模型计算生成内容与参考答案的语义相似度
    BLEU = "bleu"  # BLEU - 基于n-gram匹配评估生成文本质量，常用于机器翻译
    ROUGE = "rouge"  # ROUGE - 基于召回率的n-gram重叠度量，常用于文本摘要评估


class EvaluationComparison(BaseEntity, AuditMixin):
    """
    评估对比数据库模型
    """
    __tablename__ = "eval_evaluation_comparisons"

    comparison_name = Column(String(255), nullable=False, comment="对比名称")
    comparison_description = Column(Text, nullable=True, comment="对比描述")
    test_task_id = Column(String(36), nullable=False, index=True, comment="测试任务ID")
    test_task_name = Column(String(255), nullable=True, comment="测试任务名称（快照）")
    evaluation_strategies = Column(Text, nullable=False, comment="评估策略列表（JSON格式）")
    evaluation_model_id = Column(String(36), nullable=True, index=True, comment="评估模型ID（用于LLM评估策略）")
    evaluation_model_name = Column(String(255), nullable=True, comment="评估模型名称（快照）")
    status = Column(String(50), nullable=False, default=ComparisonStatus.PENDING.value, index=True, comment="对比状态")
    total_pairs = Column(Integer, nullable=False, default=0, comment="评估对数总数")
    completed_pairs = Column(Integer, nullable=False, default=0, comment="已完成对数")
    dimension_averages = Column(Text, nullable=True, comment="各维度平均分（JSON格式）")
    remarks = Column(Text, nullable=True, comment="备注信息")

    # 关系（仅逻辑关联，不在数据库层面创建外键约束）
    test_task = relationship("TestTask", foreign_keys=[test_task_id], primaryjoin="EvaluationComparison.test_task_id==TestTask.id", backref="evaluations")
    evaluation_model = relationship("AIModel", foreign_keys=[evaluation_model_id], primaryjoin="EvaluationComparison.evaluation_model_id==AIModel.id", backref="evaluations")
    results = relationship("EvaluationResult", foreign_keys="EvaluationResult.comparison_id", primaryjoin="EvaluationComparison.id==EvaluationResult.comparison_id", back_populates="comparison", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EvaluationComparison(id={self.id}, comparison_name='{self.comparison_name}', status='{self.status}')>"


class EvaluationResult(BaseEntity, AuditMixin):
    """
    评估结果明细数据库模型
    """
    __tablename__ = "eval_evaluation_results"

    comparison_id = Column(String(36), nullable=False, index=True, comment="对比ID")
    execution_id = Column(String(36), nullable=False, index=True, comment="测试执行记录ID")
    prompt_use_case_id = Column(String(36), nullable=True, index=True, comment="用例ID（快照，不维护外键关系）")
    prompt_use_case_name = Column(String(255), nullable=True, comment="用例名称（快照，用于显示）")
    model_output = Column(Text, nullable=True, comment="模型输出结果（快照）")
    reference_answer = Column(Text, nullable=True, comment="参考答案（快照）")
    evaluation_strategy = Column(String(100), nullable=False, index=True, comment="评估策略")
    score = Column(Float, nullable=True, comment="评估分数（不同策略有不同含义）")
    result_details = Column(Text, nullable=True, comment="评估结果详情（JSON格式）")
    status = Column(String(50), nullable=False, default=ResultStatus.PENDING.value, index=True, comment="计算状态")
    error_message = Column(Text, nullable=True, comment="错误信息")

    # 关系（仅逻辑关联，不在数据库层面创建外键约束）
    comparison = relationship("EvaluationComparison", foreign_keys=[comparison_id], primaryjoin="EvaluationResult.comparison_id==EvaluationComparison.id", back_populates="results")
    execution = relationship("TestExecution", foreign_keys=[execution_id], primaryjoin="EvaluationResult.execution_id==TestExecution.id", backref="evaluation_results")

    def __repr__(self):
        return f"<EvaluationResult(id={self.id}, comparison_id='{self.comparison_id}', strategy='{self.evaluation_strategy}', score={self.score})>"


class EvaluationTemplateDimensionStats(BaseEntity, AuditMixin):
    """
    评估结果按提示词模板分组的维度统计数据库模型
    """
    __tablename__ = "eval_evaluation_template_dimension_stats"

    comparison_id = Column(String(36), nullable=False, index=True, comment="对比ID")
    prompt_template_id = Column(String(36), nullable=False, index=True, comment="提示词模板ID")
    prompt_template_name = Column(String(255), nullable=True, comment="提示词模板名称（快照）")
    evaluation_strategy = Column(String(100), nullable=False, index=True, comment="评估策略")
    avg_score = Column(Float, nullable=True, comment="平均分")
    min_score = Column(Float, nullable=True, comment="最小分")
    max_score = Column(Float, nullable=True, comment="最大分")
    sample_count = Column(Integer, nullable=False, default=0, comment="样本数量")

    def __repr__(self):
        return f"<EvaluationTemplateDimensionStats(id={self.id}, comparison_id='{self.comparison_id}', template_id='{self.prompt_template_id}', strategy='{self.evaluation_strategy}', avg={self.avg_score})>"
