"""
Test Task endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.test_task import (
    TestTaskCreate,
    TestTaskUpdate,
    TestTaskResponse,
    TestTaskListResponse,
    TestTaskStatusResponse
)
from app.services.test_task import TestTaskService

router = APIRouter()


def get_test_task_service(db: Session = Depends(get_db)) -> TestTaskService:
    """
    依赖注入：获取TestTaskService实例
    
    Args:
        db: 数据库会话
        
    Returns:
        TestTaskService实例
    """
    return TestTaskService(db)


# ============= 测试任务相关接口 =============

@router.post("", response_model=TestTaskResponse, status_code=201)
def create_test_task(
    task_in: TestTaskCreate,
    service: TestTaskService = Depends(get_test_task_service)
):
    """
    创建测试任务
    
    创建一个新的测试任务，包含要执行的用例列表和使用的AI模型。
    任务创建后会自动为每个用例创建执行记录，状态为待执行。
    
    Args:
        task_in: 测试任务创建数据
        service: 测试任务服务
        
    Returns:
        创建的测试任务
        
    Raises:
        HTTPException: 如果AI模型不存在或用例不存在
    """
    return service.create_test_task(task_in)


@router.get("/{task_id}", response_model=TestTaskResponse)
def get_test_task(
    task_id: str = Path(..., description="任务ID"),
    service: TestTaskService = Depends(get_test_task_service)
):
    """
    获取测试任务基本信息
    
    Args:
        task_id: 任务ID
        service: 测试任务服务
        
    Returns:
        测试任务基本信息
        
    Raises:
        HTTPException: 如果任务不存在
    """
    task = service.get_test_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="找不到测试任务")
    return task


@router.get("", response_model=TestTaskListResponse)
def get_test_tasks(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数上限"),
    keyword: Optional[str] = Query(None, description="关键词（搜索任务名称、描述、备注）"),
    status: Optional[str] = Query(None, description="任务状态过滤"),
    ai_model_id: Optional[str] = Query(None, description="AI模型ID过滤"),
    service: TestTaskService = Depends(get_test_task_service)
):
    """
    获取测试任务列表
    
    支持分页和多种过滤条件。结果按更新时间倒序排列。
    
    Args:
        skip: 跳过记录数
        limit: 返回记录数上限
        keyword: 关键词（模糊搜索任务名称、描述、备注）
        status: 任务状态过滤（pending/running/completed/cancelled/partial）
        ai_model_id: AI模型ID过滤
        service: 测试任务服务
        
    Returns:
        测试任务列表及总数
    """
    return service.get_test_tasks(
        skip=skip,
        limit=limit,
        keyword=keyword,
        status=status,
        ai_model_id=ai_model_id
    )


@router.put("/{task_id}", response_model=TestTaskResponse)
def update_test_task(
    task_id: str = Path(..., description="任务ID"),
    task_in: TestTaskUpdate = ...,
    service: TestTaskService = Depends(get_test_task_service)
):
    """
    更新测试任务
    
    只能更新任务的基本信息（名称、描述、备注），不能修改状态和统计信息。
    
    Args:
        task_id: 任务ID
        task_in: 更新数据
        service: 测试任务服务
        
    Returns:
        更新后的测试任务
        
    Raises:
        HTTPException: 如果任务不存在
    """
    task = service.update_test_task(task_id, task_in)
    if not task:
        raise HTTPException(status_code=404, detail="找不到测试任务")
    return task


@router.delete("/{task_id}", status_code=204)
def delete_test_task(
    task_id: str = Path(..., description="任务ID"),
    service: TestTaskService = Depends(get_test_task_service)
):
    """
    删除测试任务
    
    删除任务会同时删除所有关联的执行记录（级联删除）。
    
    Args:
        task_id: 任务ID
        service: 测试任务服务
        
    Raises:
        HTTPException: 如果任务不存在
    """
    success = service.delete_test_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="找不到测试任务")


# ============= 任务执行控制接口 =============

@router.post("/{task_id}/start", response_model=TestTaskResponse)
def start_task_execution(
    background_tasks: BackgroundTasks,
    task_id: str = Path(..., description="任务ID"),
    service: TestTaskService = Depends(get_test_task_service)
):
    """
    启动任务执行
    
    将任务状态更新为"执行中"，并在后台异步执行所有待执行的用例。
    只有状态为"待执行"或"部分完成"的任务可以启动。
    
    Args:
        background_tasks: FastAPI 后台任务
        task_id: 任务ID
        service: 测试任务服务
        
    Returns:
        更新后的测试任务
        
    Raises:
        HTTPException: 如果任务不存在或状态不允许启动
    """
    return service.start_task_execution(task_id, background_tasks)


@router.post("/{task_id}/cancel", response_model=TestTaskResponse)
def cancel_task_execution(
    task_id: str = Path(..., description="任务ID"),
    service: TestTaskService = Depends(get_test_task_service)
):
    """
    取消任务执行
    
    将任务状态更新为"已取消"，停止后续用例的执行。
    只有状态为"执行中"的任务可以取消。
    
    Args:
        task_id: 任务ID
        service: 测试任务服务
        
    Returns:
        更新后的测试任务
        
    Raises:
        HTTPException: 如果任务不存在或状态不允许取消
    """
    return service.cancel_task_execution(task_id)


@router.post("/{task_id}/restart", response_model=TestTaskResponse)
def restart_task_execution(
    background_tasks: BackgroundTasks,
    task_id: str = Path(..., description="任务ID"),
    force: bool = Query(False, description="是否强制重启（忽略10分钟限制）"),
    service: TestTaskService = Depends(get_test_task_service)
):
    """
    重启测试任务
    
    **使用场景**：
    - 测试任务运行中但长时间无进展
    - 测试任务部分完成，需要继续执行剩余用例
    - 测试任务已取消，需要重新运行
    
    **重启条件**：
    - `pending`、`partial`、`cancelled` 状态：可以直接重启
    - `running` 状态：
      - 默认需要最后更新时间超过 10 分钟才能重启
      - 可以通过 `force=true` 参数强制重启（谨慎使用）
    - `completed` 状态：不允许重启
    
    **重启行为**：
    - 只会重新执行状态为 `pending` 的测试执行记录
    - 已成功或已失败的执行记录不会重新执行
    - 计算过程在后台异步执行
    
    **参数说明**：
    - `force`: 
      - `false`（默认）：运行中的任务需要等待10分钟无更新才能重启
      - `true`：立即重启，忽略时间限制（适用于确认任务已卡住的情况）
    
    **示例**：
    ```
    # 正常重启（需要满足10分钟条件）
    POST /api/v1/test-tasks/{task_id}/restart
    
    # 强制重启（立即重启）
    POST /api/v1/test-tasks/{task_id}/restart?force=true
    ```
    
    Args:
        background_tasks: FastAPI 后台任务
        task_id: 任务ID
        force: 是否强制重启
        service: 测试任务服务
        
    Returns:
        更新后的测试任务
        
    Raises:
        HTTPException: 如果任务不存在或不满足重启条件
    """
    return service.restart_test_task(task_id, background_tasks, force=force)


@router.post("/check-timeout", summary="检查并标记超时的测试任务")
def check_timeout_tasks(
    service: TestTaskService = Depends(get_test_task_service)
):
    """
    检查并标记超时的测试任务
    
    **功能说明**：
    - 检查所有运行中（`running`）的测试任务
    - 如果最后更新时间超过 30 分钟，自动标记为部分完成（`partial`）
    - 标记为部分完成后，可以通过启动或重启接口继续执行
    
    **使用场景**：
    - 可以手动调用此接口进行检查
    - 建议配置定时任务（如每5-10分钟）自动调用此接口
    - 用于清理长时间卡住的测试任务
    
    **返回**：
    - 被标记为部分完成的任务ID列表
    - 如果没有超时任务，返回空列表
    
    **示例**：
    ```json
    {
      "message": "检查完成",
      "marked_count": 2,
      "marked_ids": ["task-123", "task-456"]
    }
    ```
    
    Args:
        service: 测试任务服务
        
    Returns:
        检查结果
    """
    marked_ids = service.check_and_mark_timeout_tasks()
    
    return {
        "message": "检查完成",
        "marked_count": len(marked_ids),
        "marked_ids": marked_ids
    }


@router.get("/{task_id}/status", response_model=TestTaskStatusResponse)
def get_task_status(
    task_id: str = Path(..., description="任务ID"),
    service: TestTaskService = Depends(get_test_task_service)
):
    """
    获取任务执行状态
    
    返回任务的实时执行状态，包括进度百分比和各项统计。
    
    Args:
        task_id: 任务ID
        service: 测试任务服务
        
    Returns:
        任务执行状态
        
    Raises:
        HTTPException: 如果任务不存在
    """
    status = service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="找不到测试任务")
    return status


# ============= 执行记录相关接口 =============
# 注意：执行记录接口已迁移至 /api/v1/executions
# 请使用独立的 test_execution 模块进行执行记录的分页查询

