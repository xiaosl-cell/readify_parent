"""
Test Execution service
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.test_execution import TestExecutionRepository
from app.repositories.prompt_use_case import PromptUseCaseRepository
from app.schemas.test_task import TestExecutionResponse, TestExecutionListResponse
from app.models.test_task import TestExecution


class TestExecutionService:
    """
    测试执行记录服务层
    """

    def __init__(self, db: Session):
        self.db = db
        self.execution_repo = TestExecutionRepository(db)
        self.use_case_repo = PromptUseCaseRepository(db)

    def get_execution(self, execution_id: str) -> Optional[TestExecutionResponse]:
        """
        获取单个执行记录详情
        
        Args:
            execution_id: 执行记录ID
            
        Returns:
            执行记录详情，如果不存在返回None
        """
        execution = self.execution_repo.get(execution_id)
        if not execution:
            return None
        
        return TestExecutionResponse.model_validate(execution)

    def get_executions(
        self,
        skip: int = 0,
        limit: int = 100,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        use_case_id: Optional[str] = None,
        ai_model_id: Optional[str] = None
    ) -> TestExecutionListResponse:
        """
        获取执行记录列表（分页）
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数上限
            task_id: 任务ID过滤
            status: 执行状态过滤
            use_case_id: 用例ID过滤
            ai_model_id: AI模型ID过滤
            
        Returns:
            执行记录列表响应
        """
        # 构建过滤条件
        filters: Dict[str, Any] = {}
        if task_id:
            filters["task_id"] = task_id
        if status:
            filters["status"] = status
        if use_case_id:
            filters["use_case_id"] = use_case_id
        if ai_model_id:
            filters["ai_model_id"] = ai_model_id
        
        # 查询执行记录
        executions, total = self.execution_repo.list_with_filters(
            skip=skip,
            limit=limit,
            filters=filters if filters else None
        )
        
        # 转换为响应模型
        items = [TestExecutionResponse.model_validate(execution) for execution in executions]
        
        return TestExecutionListResponse(total=total, items=items)

    def get_executions_by_task(
        self,
        task_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> TestExecutionListResponse:
        """
        根据任务ID获取执行记录列表（分页）
        
        Args:
            task_id: 任务ID
            skip: 跳过记录数
            limit: 返回记录数上限
            
        Returns:
            执行记录列表响应
        """
        executions, total = self.execution_repo.get_by_task_id(
            task_id=task_id,
            skip=skip,
            limit=limit
        )
        
        items = [TestExecutionResponse.model_validate(execution) for execution in executions]
        
        return TestExecutionListResponse(total=total, items=items)

    def delete_execution(self, execution_id: str) -> bool:
        """
        删除执行记录（硬删除，永久删除）
        
        Args:
            execution_id: 执行记录ID
            
        Returns:
            是否删除成功
        """
        return self.execution_repo.delete(execution_id)
    
    def backfill_task_successful_outputs(self, task_id: str) -> Dict[str, Any]:
        """
        将测试任务下所有成功执行的测试记录的生成内容回填到对应测试用例的参考答案
        
        Args:
            task_id: 测试任务ID
            
        Returns:
            回填结果统计
            {
                "total_executions": 总执行记录数,
                "updated_use_cases": 更新的用例数,
                "skipped": 跳过数（无用例ID或用例不存在）,
                "details": [更新详情列表]
            }
            
        Raises:
            HTTPException: 如果任务不存在
        """
        # 获取所有成功的执行记录
        successful_executions = self.execution_repo.get_successful_executions_by_task_id(task_id)
        
        if not successful_executions:
            return {
                "total_executions": 0,
                "updated_use_cases": 0,
                "skipped": 0,
                "details": []
            }
        
        updated_count = 0
        skipped_count = 0
        details = []
        
        for execution in successful_executions:
            # 检查是否有用例ID
            if not execution.prompt_use_case_id:
                skipped_count += 1
                details.append({
                    "execution_id": execution.id,
                    "status": "skipped",
                    "reason": "无用例ID"
                })
                continue
            
            # 检查是否有输出结果
            if not execution.output_result:
                skipped_count += 1
                details.append({
                    "execution_id": execution.id,
                    "use_case_id": execution.prompt_use_case_id,
                    "status": "skipped",
                    "reason": "无输出结果"
                })
                continue
            
            # 获取用例
            use_case = self.use_case_repo.get(execution.prompt_use_case_id)
            if not use_case:
                skipped_count += 1
                details.append({
                    "execution_id": execution.id,
                    "use_case_id": execution.prompt_use_case_id,
                    "status": "skipped",
                    "reason": "用例不存在"
                })
                continue
            
            # 更新用例的参考答案
            self.use_case_repo.update(execution.prompt_use_case_id, {
                "reference_answer": execution.output_result
            })
            
            # 同步更新该用例关联的所有测试执行记录的参考答案快照
            self._update_execution_reference_answers(
                execution.prompt_use_case_id,
                execution.output_result
            )
            
            updated_count += 1
            details.append({
                "execution_id": execution.id,
                "use_case_id": execution.prompt_use_case_id,
                "use_case_name": use_case.use_case_name,
                "status": "updated"
            })
        
        # 提交事务
        self.db.commit()
        
        return {
            "total_executions": len(successful_executions),
            "updated_use_cases": updated_count,
            "skipped": skipped_count,
            "details": details
        }
    
    def backfill_single_execution_output(self, execution_id: str) -> Dict[str, Any]:
        """
        将单条测试执行记录的生成内容回填到对应测试用例的参考答案
        
        Args:
            execution_id: 执行记录ID
            
        Returns:
            回填结果
            {
                "execution_id": 执行记录ID,
                "use_case_id": 用例ID,
                "use_case_name": 用例名称,
                "status": "updated" | "skipped",
                "reason": 跳过原因（如果跳过）
            }
            
        Raises:
            HTTPException: 如果执行记录不存在
        """
        # 获取执行记录
        execution = self.execution_repo.get(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="找不到执行记录")
        
        # 检查执行状态
        if execution.status != "success":
            return {
                "execution_id": execution_id,
                "use_case_id": execution.prompt_use_case_id,
                "status": "skipped",
                "reason": f"执行状态为 {execution.status}，仅支持成功状态的记录"
            }
        
        # 检查是否有用例ID
        if not execution.prompt_use_case_id:
            return {
                "execution_id": execution_id,
                "use_case_id": None,
                "status": "skipped",
                "reason": "无用例ID"
            }
        
        # 检查是否有输出结果
        if not execution.output_result:
            return {
                "execution_id": execution_id,
                "use_case_id": execution.prompt_use_case_id,
                "status": "skipped",
                "reason": "无输出结果"
            }
        
        # 获取用例
        use_case = self.use_case_repo.get(execution.prompt_use_case_id)
        if not use_case:
            return {
                "execution_id": execution_id,
                "use_case_id": execution.prompt_use_case_id,
                "status": "skipped",
                "reason": "用例不存在"
            }
        
        # 更新用例的参考答案
        self.use_case_repo.update(execution.prompt_use_case_id, {
            "reference_answer": execution.output_result
        })
        
        # 同步更新该用例关联的所有测试执行记录的参考答案快照
        updated_execution_count = self._update_execution_reference_answers(
            execution.prompt_use_case_id,
            execution.output_result
        )
        
        # 提交事务
        self.db.commit()
        
        return {
            "execution_id": execution_id,
            "use_case_id": execution.prompt_use_case_id,
            "use_case_name": use_case.use_case_name,
            "old_reference_answer": use_case.reference_answer,
            "new_reference_answer": execution.output_result,
            "updated_execution_count": updated_execution_count,
            "status": "updated"
        }
    
    def _update_execution_reference_answers(
        self, 
        use_case_id: str, 
        reference_answer: str
    ) -> int:
        """
        更新指定用例关联的所有测试执行记录的参考答案快照
        
        Args:
            use_case_id: 用例ID
            reference_answer: 新的参考答案
            
        Returns:
            更新的执行记录数量
        """
        # 获取该用例关联的所有执行记录
        executions = self.db.query(TestExecution).filter(
            TestExecution.prompt_use_case_id == use_case_id
        ).all()
        
        # 批量更新参考答案快照
        updated_count = 0
        for execution in executions:
            execution.reference_answer = reference_answer
            updated_count += 1
        
        return updated_count

