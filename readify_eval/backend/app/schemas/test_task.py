"""
Test Task schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.base import BaseEntity


# ============= 测试任务相关 Schema =============

class TestTaskCreate(BaseModel):
    """创建测试任务的请求 Schema"""
    task_name: str = Field(..., description="任务名称")
    task_description: Optional[str] = Field(None, description="任务描述")
    use_case_ids: List[str] = Field(..., description="要执行的用例ID列表")
    ai_model_id: str = Field(..., description="使用的AI模型ID")
    remarks: Optional[str] = Field(None, description="备注信息")
    created_by: Optional[str] = Field(None, description="创建人ID")


class TestTaskUpdate(BaseModel):
    """更新测试任务的请求 Schema"""
    task_name: Optional[str] = Field(None, description="任务名称")
    task_description: Optional[str] = Field(None, description="任务描述")
    remarks: Optional[str] = Field(None, description="备注信息")
    updated_by: Optional[str] = Field(None, description="更新人ID")


class TestTaskResponse(BaseEntity):
    """测试任务响应 Schema"""
    task_name: str = Field(..., description="任务名称")
    task_description: Optional[str] = Field(None, description="任务描述")
    status: str = Field(..., description="任务状态")
    total_cases: int = Field(..., description="用例总数")
    completed_cases: int = Field(..., description="完成用例数")
    success_cases: int = Field(..., description="成功用例数")
    failed_cases: int = Field(..., description="失败用例数")
    ai_model_id: Optional[str] = Field(None, description="使用的AI模型ID")
    ai_model_name: Optional[str] = Field(None, description="AI模型名称")
    remarks: Optional[str] = Field(None, description="备注信息")

    class Config:
        from_attributes = True


class TestTaskListResponse(BaseModel):
    """测试任务列表响应 Schema"""
    total: int = Field(..., description="总数量")
    items: List[TestTaskResponse] = Field(..., description="测试任务列表")


# ============= 测试执行记录相关 Schema =============

class TestExecutionResponse(BaseEntity):
    """测试执行记录响应 Schema"""
    test_task_id: str = Field(..., description="测试任务ID")
    status: str = Field(..., description="执行状态")
    prompt_use_case_id: Optional[str] = Field(None, description="提示词用例ID（快照）")
    prompt_use_case_name: Optional[str] = Field(None, description="提示词用例名称（快照，用于显示）")
    llm_params_snapshot: Optional[str] = Field(None, description="LLM参数快照（JSON格式）")
    rendered_system_prompt: Optional[str] = Field(None, description="渲染后的系统提示词")
    rendered_user_prompt: Optional[str] = Field(None, description="渲染后的用户提示词")
    ai_model_id: Optional[str] = Field(None, description="使用的AI模型ID")
    ai_model_name: Optional[str] = Field(None, description="AI模型名称")
    reference_answer: Optional[str] = Field(None, description="参考答案（快照，来自提示词用例）")
    evaluation_strategies_snapshot: Optional[str] = Field(None, description="评估策略快照（JSON格式，来自提示词模板）")
    template_version: Optional[int] = Field(None, description="执行时使用的提示词模板版本号")
    template_version_id: Optional[str] = Field(None, description="执行时使用的提示词模板版本ID")
    output_result: Optional[str] = Field(None, description="输出结果")
    start_time: Optional[datetime] = Field(None, description="开始执行时间")
    end_time: Optional[datetime] = Field(None, description="结束执行时间")
    execution_duration: Optional[float] = Field(None, description="执行耗时（秒）")
    model_response_duration: Optional[float] = Field(None, description="模型响应耗时（秒）")
    error_message: Optional[str] = Field(None, description="错误信息")

    class Config:
        from_attributes = True


class TestExecutionListResponse(BaseModel):
    """测试执行记录列表响应 Schema"""
    total: int = Field(..., description="总数量")
    items: List[TestExecutionResponse] = Field(..., description="执行记录列表")


# 注意：执行记录已移至独立的 /api/v1/executions 接口进行分页查询
# 不再在任务详情中返回所有执行记录，避免数据量过大
# 前端应通过 GET /api/v1/executions?task_id={task_id} 分页查询执行记录


# ============= 任务执行相关 Schema =============

class TestTaskStartRequest(BaseModel):
    """启动测试任务的请求 Schema"""
    task_id: str = Field(..., description="任务ID")


class TestTaskCancelRequest(BaseModel):
    """取消测试任务的请求 Schema"""
    task_id: str = Field(..., description="任务ID")


class TestTaskStatusResponse(BaseModel):
    """测试任务状态响应 Schema"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    total_cases: int = Field(..., description="用例总数")
    completed_cases: int = Field(..., description="完成用例数")
    success_cases: int = Field(..., description="成功用例数")
    failed_cases: int = Field(..., description="失败用例数")
    progress_percentage: float = Field(..., description="完成进度百分比")

