"""
Database models layer
"""
from app.core.database import Base
from .base import BaseEntity, AuditMixin
from .example import ExampleModel
from .ai_model import AIModel, ModelCategory
from .prompt_template import PromptTemplate
from .prompt_template_version import PromptTemplateVersion
from .prompt_use_case import PromptUseCase
from .system_config import SystemConfig
from .test_task import TestTask, TestExecution, TaskStatus, ExecutionStatus
from .evaluation import (
    EvaluationComparison, 
    EvaluationResult, 
    EvaluationTemplateDimensionStats,
    ComparisonStatus, 
    ResultStatus
)

# Import all models here for Alembic to detect them
# from app.models.user import User
# from app.models.item import Item

__all__ = [
    "Base", "BaseEntity", "AuditMixin", "ExampleModel",
    "AIModel", "ModelCategory",
    "PromptTemplate", "PromptTemplateVersion", "PromptUseCase",
    "SystemConfig",
    "TestTask", "TestExecution", "TaskStatus", "ExecutionStatus",
    "EvaluationComparison", "EvaluationResult", "EvaluationTemplateDimensionStats",
    "ComparisonStatus", "ResultStatus"
]

