"""
Test Task repository
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.test_task import TestTask, TestExecution
from app.repositories.base import BaseRepository


class TestTaskRepository(BaseRepository[TestTask]):
    """
    测试任务仓储类
    """
    
    def __init__(self, db: Session):
        super().__init__(TestTask, db)
    
    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[TestTask]:
        """
        根据状态获取测试任务列表
        
        Args:
            status: 任务状态
            skip: 跳过记录数
            limit: 返回记录数上限
            
        Returns:
            测试任务列表
        """
        return self.db.query(self.model).filter(
            self.model.status == status
        ).order_by(
            self.model.updated_at.desc()
        ).offset(skip).limit(limit).all()
    
    def search(
        self,
        skip: int = 0,
        limit: int = 100,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        ai_model_id: Optional[str] = None
    ) -> tuple[List[TestTask], int]:
        """
        搜索测试任务
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数上限
            keyword: 关键词（模糊搜索任务名称和描述）
            status: 任务状态过滤
            ai_model_id: AI模型ID过滤
            
        Returns:
            (测试任务列表, 总数)
        """
        query = self.db.query(self.model)
        
        # 关键词搜索
        if keyword:
            search_filter = or_(
                self.model.task_name.ilike(f"%{keyword}%"),
                self.model.task_description.ilike(f"%{keyword}%"),
                self.model.remarks.ilike(f"%{keyword}%")
            )
            query = query.filter(search_filter)
        
        # 状态过滤
        if status:
            query = query.filter(self.model.status == status)
        
        # AI模型过滤
        if ai_model_id:
            query = query.filter(self.model.ai_model_id == ai_model_id)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        items = query.order_by(
            self.model.updated_at.desc()
        ).offset(skip).limit(limit).all()
        
        return items, total
    
    def update_task_stats(
        self,
        task_id: str,
        completed_cases: int,
        success_cases: int,
        failed_cases: int
    ) -> Optional[TestTask]:
        """
        更新任务统计信息
        
        Args:
            task_id: 任务ID
            completed_cases: 完成用例数
            success_cases: 成功用例数
            failed_cases: 失败用例数
            
        Returns:
            更新后的任务
        """
        task = self.get(task_id)
        if task:
            task.completed_cases = completed_cases
            task.success_cases = success_cases
            task.failed_cases = failed_cases
            self.db.flush()
            self.db.refresh(task)
        return task


class TestExecutionRepository(BaseRepository[TestExecution]):
    """
    测试执行记录仓储类
    """
    
    def __init__(self, db: Session):
        super().__init__(TestExecution, db)
    
    def get_by_task_id(self, task_id: str, skip: int = 0, limit: int = 100) -> List[TestExecution]:
        """
        根据任务ID获取执行记录列表
        
        Args:
            task_id: 任务ID
            skip: 跳过记录数
            limit: 返回记录数上限
            
        Returns:
            执行记录列表
        """
        return self.db.query(self.model).filter(
            self.model.test_task_id == task_id
        ).order_by(
            self.model.created_at.asc()
        ).offset(skip).limit(limit).all()
    
    def count_by_task_id(self, task_id: str) -> int:
        """
        统计任务的执行记录总数
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行记录总数
        """
        return self.db.query(func.count(self.model.id)).filter(
            self.model.test_task_id == task_id
        ).scalar()
    
    def get_by_task_id_and_status(
        self,
        task_id: str,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TestExecution]:
        """
        根据任务ID和状态获取执行记录列表
        
        Args:
            task_id: 任务ID
            status: 执行状态
            skip: 跳过记录数
            limit: 返回记录数上限
            
        Returns:
            执行记录列表
        """
        return self.db.query(self.model).filter(
            self.model.test_task_id == task_id,
            self.model.status == status
        ).order_by(
            self.model.created_at.asc()
        ).offset(skip).limit(limit).all()
    
    def count_by_task_id_and_status(self, task_id: str, status: str) -> int:
        """
        统计任务下指定状态的执行记录数
        
        Args:
            task_id: 任务ID
            status: 执行状态
            
        Returns:
            记录数
        """
        return self.db.query(func.count(self.model.id)).filter(
            self.model.test_task_id == task_id,
            self.model.status == status
        ).scalar()
    
    def get_pending_executions(self, task_id: str, limit: int = 10) -> List[TestExecution]:
        """
        获取待执行的记录
        
        Args:
            task_id: 任务ID
            limit: 返回记录数上限
            
        Returns:
            待执行的记录列表
        """
        return self.get_by_task_id_and_status(task_id, "pending", 0, limit)
    
    def search(
        self,
        skip: int = 0,
        limit: int = 100,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        use_case_id: Optional[str] = None
    ) -> tuple[List[TestExecution], int]:
        """
        搜索执行记录
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数上限
            task_id: 任务ID过滤
            status: 状态过滤
            use_case_id: 用例ID过滤
            
        Returns:
            (执行记录列表, 总数)
        """
        query = self.db.query(self.model)
        
        # 任务ID过滤
        if task_id:
            query = query.filter(self.model.test_task_id == task_id)
        
        # 状态过滤
        if status:
            query = query.filter(self.model.status == status)
        
        # 用例ID过滤
        if use_case_id:
            query = query.filter(self.model.prompt_use_case_id == use_case_id)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        items = query.order_by(
            self.model.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return items, total

