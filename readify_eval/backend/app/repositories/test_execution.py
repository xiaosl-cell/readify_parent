"""
Test Execution repository
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.test_task import TestExecution
from app.repositories.base import BaseRepository


class TestExecutionRepository(BaseRepository[TestExecution]):
    """
    测试执行记录Repository
    """

    def __init__(self, db: Session):
        super().__init__(TestExecution, db)

    def get_by_task_id(
        self,
        task_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[TestExecution], int]:
        """
        根据任务ID获取执行记录列表
        
        Args:
            task_id: 任务ID
            skip: 跳过记录数
            limit: 返回记录数上限
            
        Returns:
            (执行记录列表, 总数)
        """
        query = self.db.query(self.model).filter(
            self.model.test_task_id == task_id
        )
        
        total = query.count()
        items = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()
        
        return items, total

    def list_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[TestExecution], int]:
        """
        根据多种条件过滤执行记录列表
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数上限
            filters: 过滤条件字典
                - task_id: 任务ID
                - status: 执行状态
                - use_case_id: 用例ID
                - ai_model_id: AI模型ID
                
        Returns:
            (执行记录列表, 总数)
        """
        query = self.db.query(self.model)
        
        if filters:
            if "task_id" in filters and filters["task_id"]:
                query = query.filter(self.model.test_task_id == filters["task_id"])
            
            if "status" in filters and filters["status"]:
                query = query.filter(self.model.status == filters["status"])
            
            if "use_case_id" in filters and filters["use_case_id"]:
                query = query.filter(self.model.prompt_use_case_id == filters["use_case_id"])
            
            if "ai_model_id" in filters and filters["ai_model_id"]:
                query = query.filter(self.model.ai_model_id == filters["ai_model_id"])
        
        total = query.count()
        items = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()
        
        return items, total

    def count_by_task_and_status(self, task_id: str, status: str) -> int:
        """
        统计指定任务和状态的执行记录数量
        
        Args:
            task_id: 任务ID
            status: 执行状态
            
        Returns:
            执行记录数量
        """
        return self.db.query(self.model).filter(
            and_(
                self.model.test_task_id == task_id,
                self.model.status == status
            )
        ).count()

    def get_all_by_task_id(self, task_id: str) -> List[TestExecution]:
        """
        获取指定任务的所有执行记录（不分页）
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行记录列表
        """
        return self.db.query(self.model).filter(
            self.model.test_task_id == task_id
        ).order_by(self.model.created_at.desc()).all()
    
    def get_successful_executions_by_task_id(self, task_id: str) -> List[TestExecution]:
        """
        获取指定任务的所有成功执行记录
        
        Args:
            task_id: 任务ID
            
        Returns:
            成功的执行记录列表
        """
        return self.db.query(self.model).filter(
            and_(
                self.model.test_task_id == task_id,
                self.model.status == "success"
            )
        ).order_by(self.model.created_at.desc()).all()

