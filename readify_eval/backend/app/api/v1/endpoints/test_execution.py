"""
Test Execution endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.test_task import (
    TestExecutionResponse,
    TestExecutionListResponse
)
from app.services.test_execution import TestExecutionService

router = APIRouter()


def get_test_execution_service(db: Session = Depends(get_db)) -> TestExecutionService:
    """
    依赖注入：获取TestExecutionService实例
    
    Args:
        db: 数据库会话
        
    Returns:
        TestExecutionService实例
    """
    return TestExecutionService(db)


@router.get("/{execution_id}", response_model=TestExecutionResponse)
def get_execution(
    execution_id: str = Path(..., description="执行记录ID"),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    获取执行记录详情
    
    根据执行记录ID获取单个执行记录的详细信息，包括执行状态、结果、耗时等。
    
    Args:
        execution_id: 执行记录ID
        service: 执行记录服务
        
    Returns:
        执行记录详情
        
    Raises:
        HTTPException: 如果执行记录不存在
    """
    execution = service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="找不到执行记录")
    return execution


@router.get("", response_model=TestExecutionListResponse)
def get_executions(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数上限"),
    task_id: Optional[str] = Query(None, description="任务ID过滤"),
    status: Optional[str] = Query(None, description="执行状态过滤（pending/success/failed）"),
    use_case_id: Optional[str] = Query(None, description="用例ID过滤"),
    ai_model_id: Optional[str] = Query(None, description="AI模型ID过滤"),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    获取执行记录列表（分页）
    
    支持分页和多种过滤条件。结果按创建时间倒序排列。
    这是主要的执行记录查询接口，前端可以通过task_id参数分页查询指定任务的执行记录。
    
    Args:
        skip: 跳过记录数（用于分页）
        limit: 返回记录数上限（用于分页）
        task_id: 任务ID过滤（可选，用于查询特定任务的执行记录）
        status: 执行状态过滤（pending/success/failed）
        use_case_id: 用例ID过滤（可选）
        ai_model_id: AI模型ID过滤（可选）
        service: 执行记录服务
        
    Returns:
        执行记录列表及总数
        
    Examples:
        - 查询所有执行记录: GET /api/v1/executions?skip=0&limit=20
        - 查询指定任务的执行记录: GET /api/v1/executions?task_id=xxx&skip=0&limit=20
        - 查询指定任务的失败记录: GET /api/v1/executions?task_id=xxx&status=failed
    """
    return service.get_executions(
        skip=skip,
        limit=limit,
        task_id=task_id,
        status=status,
        use_case_id=use_case_id,
        ai_model_id=ai_model_id
    )


@router.post("/tasks/{task_id}/backfill")
def backfill_task_successful_outputs(
    task_id: str = Path(..., description="测试任务ID"),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    批量回填：将测试任务下所有成功执行的测试记录的生成内容回填到对应测试用例的参考答案
    
    此接口会遍历指定测试任务下所有状态为 success 的执行记录，将其 output_result 字段
    的值更新到对应提示词用例的 reference_answer 字段。
    
    **回填规则**：
    - 只处理状态为 success 的执行记录
    - 跳过没有 use_case_id 的记录
    - 跳过没有 output_result 的记录
    - 跳过对应用例不存在的记录
    
    Args:
        task_id: 测试任务ID
        service: 执行记录服务
        
    Returns:
        回填结果统计
        {
            "total_executions": 总执行记录数,
            "updated_use_cases": 更新的用例数,
            "skipped": 跳过数,
            "details": [详细列表]
        }
    
    Examples:
        POST /api/v1/executions/tasks/{task_id}/backfill
        
        Response:
        {
            "total_executions": 10,
            "updated_use_cases": 8,
            "skipped": 2,
            "details": [...]
        }
    """
    return service.backfill_task_successful_outputs(task_id)


@router.post("/{execution_id}/backfill")
def backfill_single_execution_output(
    execution_id: str = Path(..., description="执行记录ID"),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    单条回填：将单条测试执行记录的生成内容回填到对应测试用例的参考答案
    
    此接口将指定执行记录的 output_result 字段值更新到对应提示词用例的 reference_answer 字段。
    
    **回填规则**：
    - 只处理状态为 success 的执行记录
    - 必须有 use_case_id
    - 必须有 output_result
    - 对应的用例必须存在
    
    Args:
        execution_id: 执行记录ID
        service: 执行记录服务
        
    Returns:
        回填结果
        {
            "execution_id": 执行记录ID,
            "use_case_id": 用例ID,
            "use_case_name": 用例名称,
            "old_reference_answer": 旧参考答案,
            "new_reference_answer": 新参考答案,
            "status": "updated" | "skipped",
            "reason": 跳过原因（如果跳过）
        }
        
    Raises:
        HTTPException: 如果执行记录不存在
        
    Examples:
        POST /api/v1/executions/{execution_id}/backfill
        
        Response (成功):
        {
            "execution_id": "xxx",
            "use_case_id": "yyy",
            "use_case_name": "测试用例1",
            "old_reference_answer": "旧答案",
            "new_reference_answer": "新答案",
            "status": "updated"
        }
        
        Response (跳过):
        {
            "execution_id": "xxx",
            "use_case_id": "yyy",
            "status": "skipped",
            "reason": "执行状态为 failed，仅支持成功状态的记录"
        }
    """
    return service.backfill_single_execution_output(execution_id)


@router.delete("/{execution_id}", status_code=204)
def delete_execution(
    execution_id: str = Path(..., description="执行记录ID"),
    service: TestExecutionService = Depends(get_test_execution_service)
):
    """
    删除执行记录
    
    硬删除指定的执行记录（永久删除，不可恢复）。
    
    Args:
        execution_id: 执行记录ID
        service: 执行记录服务
        
    Raises:
        HTTPException: 如果执行记录不存在
    """
    success = service.delete_execution(execution_id)
    if not success:
        raise HTTPException(status_code=404, detail="找不到执行记录")

