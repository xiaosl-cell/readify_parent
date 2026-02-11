"""
Test Task database models
"""
import enum
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship

from app.models.base import BaseEntity, AuditMixin


class TaskStatus(str, enum.Enum):
    """测试任务状态枚举"""
    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    PARTIAL = "partial"  # 部分完成


class ExecutionStatus(str, enum.Enum):
    """执行记录状态枚举"""
    PENDING = "pending"  # 待执行
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败


class TestTask(BaseEntity, AuditMixin):
    """
    测试任务数据库模型
    """
    __tablename__ = "eval_test_tasks"

    task_name = Column(String(255), nullable=False, index=True, comment="任务名称")
    task_description = Column(Text, nullable=True, comment="任务描述")
    status = Column(String(50), nullable=False, default=TaskStatus.PENDING.value, index=True, comment="任务状态")
    total_cases = Column(Integer, nullable=False, default=0, comment="用例总数")
    completed_cases = Column(Integer, nullable=False, default=0, comment="完成用例数")
    success_cases = Column(Integer, nullable=False, default=0, comment="成功用例数")
    failed_cases = Column(Integer, nullable=False, default=0, comment="失败用例数")
    ai_model_id = Column(String(36), nullable=True, index=True, comment="使用的AI模型ID")
    ai_model_name = Column(String(255), nullable=True, comment="AI模型名称（快照）")
    remarks = Column(Text, nullable=True, comment="备注信息")

    # 关系（仅逻辑关联，不在数据库层面创建外键约束）
    ai_model = relationship("AIModel", foreign_keys=[ai_model_id], primaryjoin="TestTask.ai_model_id==AIModel.id", backref="test_tasks")
    executions = relationship("TestExecution", foreign_keys="TestExecution.test_task_id", primaryjoin="TestTask.id==TestExecution.test_task_id", back_populates="test_task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestTask(id={self.id}, task_name='{self.task_name}', status='{self.status}')>"


class TestExecution(BaseEntity, AuditMixin):
    """
    测试执行记录数据库模型
    """
    __tablename__ = "eval_test_executions"

    test_task_id = Column(String(36), nullable=False, index=True, comment="测试任务ID")
    status = Column(String(50), nullable=False, default=ExecutionStatus.PENDING.value, index=True, comment="执行状态")
    
    # 快照字段（用于记录执行时的配置和输入）
    prompt_use_case_id = Column(String(36), nullable=True, index=True, comment="提示词用例ID（快照，不维护外键关系）")
    prompt_use_case_name = Column(String(255), nullable=True, comment="提示词用例名称（快照，用于显示）")
    llm_params_snapshot = Column(Text, nullable=True, comment="LLM参数快照（JSON格式：max_tokens, temperature, top_p, top_k）")
    rendered_system_prompt = Column(Text, nullable=True, comment="渲染后的系统提示词（快照）")
    rendered_user_prompt = Column(Text, nullable=True, comment="渲染后的用户提示词（快照）")
    ai_model_id = Column(String(36), nullable=True, comment="使用的AI模型ID")
    ai_model_name = Column(String(255), nullable=True, comment="AI模型名称（快照）")
    
    # 快照字段（从关联的提示词用例和模板获取）
    reference_answer = Column(Text, nullable=True, comment="参考答案（快照，来自提示词用例）")
    evaluation_strategies_snapshot = Column(Text, nullable=True, comment="评估策略快照（JSON格式，来自提示词模板）")
    
    # 提示词模板版本溯源
    template_version = Column(Integer, nullable=True, comment="执行时使用的提示词模板版本号")
    template_version_id = Column(String(36), nullable=True, comment="执行时使用的提示词模板版本ID")

    # 执行结果
    output_result = Column(Text, nullable=True, comment="输出结果")
    start_time = Column(DateTime, nullable=True, comment="开始执行时间")
    end_time = Column(DateTime, nullable=True, comment="结束执行时间")
    execution_duration = Column(Float, nullable=True, comment="执行耗时（秒）")
    model_response_duration = Column(Float, nullable=True, comment="模型响应耗时（秒）")
    error_message = Column(Text, nullable=True, comment="错误信息")

    # 关系（仅逻辑关联，不在数据库层面创建外键约束）
    test_task = relationship("TestTask", foreign_keys=[test_task_id], primaryjoin="TestExecution.test_task_id==TestTask.id", back_populates="executions")

    def __repr__(self):
        return f"<TestExecution(id={self.id}, test_task_id='{self.test_task_id}', status='{self.status}')>"

