"""
Evaluation Comparison schemas
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

from app.schemas.base import BaseEntity


# ============= 评估对比相关 Schema =============

class EvaluationComparisonCreate(BaseModel):
    """创建评估对比的请求 Schema"""
    comparison_name: str = Field(..., description="对比名称")
    comparison_description: Optional[str] = Field(None, description="对比描述")
    test_task_id: str = Field(..., description="测试任务ID")
    evaluation_model_id: Optional[str] = Field(None, description="评估模型ID（当使用LLM评估策略时必填）")
    remarks: Optional[str] = Field(None, description="备注信息")
    created_by: Optional[str] = Field(None, description="创建人ID")


class EvaluationComparisonUpdate(BaseModel):
    """更新评估对比的请求 Schema"""
    comparison_name: Optional[str] = Field(None, description="对比名称")
    comparison_description: Optional[str] = Field(None, description="对比描述")
    remarks: Optional[str] = Field(None, description="备注信息")
    updated_by: Optional[str] = Field(None, description="更新人ID")


class EvaluationComparisonResponse(BaseEntity):
    """评估对比响应 Schema"""
    comparison_name: str = Field(..., description="对比名称")
    comparison_description: Optional[str] = Field(None, description="对比描述")
    test_task_id: str = Field(..., description="测试任务ID")
    test_task_name: Optional[str] = Field(None, description="测试任务名称")
    evaluation_strategies: str = Field(..., description="评估策略列表（JSON格式）")
    evaluation_model_id: Optional[str] = Field(None, description="评估模型ID")
    evaluation_model_name: Optional[str] = Field(None, description="评估模型名称")
    status: str = Field(..., description="对比状态")
    total_pairs: int = Field(..., description="评估对数总数")
    completed_pairs: int = Field(..., description="已完成对数")
    dimension_averages: Optional[str] = Field(None, description="各维度平均分（JSON格式）")
    remarks: Optional[str] = Field(None, description="备注信息")

    class Config:
        from_attributes = True


class EvaluationComparisonListResponse(BaseModel):
    """评估对比列表响应 Schema"""
    total: int = Field(..., description="总数量")
    items: List[EvaluationComparisonResponse] = Field(..., description="评估对比列表")


class EvaluationComparisonStatusResponse(BaseModel):
    """评估对比状态响应 Schema"""
    comparison_id: str = Field(..., description="对比ID")
    status: str = Field(..., description="对比状态")
    total_pairs: int = Field(..., description="评估对数总数")
    completed_pairs: int = Field(..., description="已完成对数")
    progress_percentage: float = Field(..., description="完成进度百分比")


# ============= 评估结果明细相关 Schema =============

class EvaluationResultResponse(BaseEntity):
    """评估结果明细响应 Schema"""
    comparison_id: str = Field(..., description="对比ID")
    execution_id: str = Field(..., description="测试执行记录ID")
    prompt_use_case_id: Optional[str] = Field(None, description="用例ID（快照）")
    prompt_use_case_name: Optional[str] = Field(None, description="用例名称（快照，用于显示）")
    model_output: Optional[str] = Field(None, description="模型输出结果")
    reference_answer: Optional[str] = Field(None, description="参考答案")
    evaluation_strategy: str = Field(..., description="评估策略")
    score: Optional[float] = Field(None, description="评估分数")
    result_details: Optional[str] = Field(None, description="评估结果详情（JSON格式）")
    status: str = Field(..., description="计算状态")
    error_message: Optional[str] = Field(None, description="错误信息")

    class Config:
        from_attributes = True


class EvaluationResultListResponse(BaseModel):
    """评估结果明细列表响应 Schema"""
    total: int = Field(..., description="总数量")
    items: List[EvaluationResultResponse] = Field(..., description="评估结果列表")


# ============= 评估执行相关 Schema =============

class EvaluationComparisonStartRequest(BaseModel):
    """启动评估对比的请求 Schema"""
    comparison_id: str = Field(..., description="对比ID")


class EvaluationComparisonStatsResponse(BaseModel):
    """评估对比统计响应 Schema"""
    comparison_id: str = Field(..., description="对比ID")
    comparison_name: str = Field(..., description="对比名称")
    test_task_name: str = Field(..., description="测试任务名称")
    total_pairs: int = Field(..., description="评估对数总数")
    strategy_stats: dict = Field(..., description="各策略的统计信息")


class ScoreRangeFilter(BaseModel):
    """分数范围过滤"""
    min_score: Optional[float] = Field(None, description="最小分数")
    max_score: Optional[float] = Field(None, description="最大分数")


# ============= 评估模板维度统计相关 Schema =============

class EvaluationTemplateDimensionStatsResponse(BaseEntity):
    """评估模板维度统计响应 Schema"""
    comparison_id: str = Field(..., description="对比ID")
    prompt_template_id: str = Field(..., description="提示词模板ID")
    prompt_template_name: Optional[str] = Field(None, description="提示词模板名称")
    evaluation_strategy: str = Field(..., description="评估策略")
    avg_score: Optional[float] = Field(None, description="平均分")
    min_score: Optional[float] = Field(None, description="最小分")
    max_score: Optional[float] = Field(None, description="最大分")
    sample_count: int = Field(..., description="样本数量")

    class Config:
        from_attributes = True


class EvaluationTemplateDimensionStatsListResponse(BaseModel):
    """评估模板维度统计列表响应 Schema"""
    total: int = Field(..., description="总数量")
    items: List[EvaluationTemplateDimensionStatsResponse] = Field(..., description="统计记录列表")


class TemplateStrategyStats(BaseModel):
    """模板策略统计"""
    template_id: str = Field(..., description="模板ID")
    template_name: Optional[str] = Field(None, description="模板名称")
    strategy: str = Field(..., description="评估策略")
    avg_score: Optional[float] = Field(None, description="平均分")
    min_score: Optional[float] = Field(None, description="最小分")
    max_score: Optional[float] = Field(None, description="最大分")
    sample_count: int = Field(..., description="样本数量")


class TemplateGroupedStatsResponse(BaseModel):
    """按模板分组的统计响应"""
    comparison_id: str = Field(..., description="对比ID")
    templates: Dict[str, List[TemplateStrategyStats]] = Field(..., description="按模板ID分组的统计信息")


# ============= 综合评估统计相关 Schema =============

class StrategyScoreStats(BaseModel):
    """策略分数统计"""
    avg: Optional[float] = Field(None, description="平均分")
    min: Optional[float] = Field(None, description="最小分")
    max: Optional[float] = Field(None, description="最大分")
    count: int = Field(0, description="样本数量")


class UseCaseResultItem(BaseModel):
    """用例结果项"""
    strategy: str = Field(..., description="评估策略")
    score: Optional[float] = Field(None, description="评估分数")
    status: str = Field(..., description="结果状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    model_output: Optional[str] = Field(None, description="模型输出结果")
    reference_answer: Optional[str] = Field(None, description="参考答案")


class UseCaseStats(BaseModel):
    """用例统计信息"""
    use_case_id: str = Field(..., description="用例ID")
    use_case_name: str = Field(..., description="用例名称")
    rendered_system_prompt: Optional[str] = Field(None, description="渲染后的系统提示词（快照）")
    rendered_user_prompt: Optional[str] = Field(None, description="渲染后的用户提示词（快照）")
    llm_params: Optional[Dict] = Field(None, description="LLM参数快照（JSON）")
    response_time: Optional[float] = Field(None, description="模型响应耗时（秒）")
    execution_error: Optional[str] = Field(None, description="执行错误信息")
    results: List[UseCaseResultItem] = Field(..., description="该用例的所有评估结果")


class TemplateDetailStats(BaseModel):
    """模板详细统计信息"""
    template_id: str = Field(..., description="模板ID")
    template_name: Optional[str] = Field(None, description="模板名称")
    system_prompt: Optional[str] = Field(None, description="系统提示词模板")
    user_prompt: Optional[str] = Field(None, description="用户提示词模板")
    function_category: Optional[str] = Field(None, description="功能分类")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    top_p: Optional[float] = Field(None, description="Top P参数")
    top_k: Optional[int] = Field(None, description="Top K参数")
    temperature: Optional[float] = Field(None, description="Temperature参数")
    use_case_count: int = Field(..., description="用例数量")
    strategies: Dict[str, StrategyScoreStats] = Field(..., description="各策略统计")
    use_cases: List[UseCaseStats] = Field(..., description="用例详情列表")


class OverallStats(BaseModel):
    """整体统计信息"""
    total_use_cases: int = Field(..., description="总用例数量")
    total_templates: int = Field(..., description="总模板数量")
    total_pairs: int = Field(..., description="评估对数总数")
    completed_pairs: int = Field(..., description="已完成对数")
    failed_pairs: int = Field(..., description="失败对数")
    success_pairs: int = Field(..., description="成功对数")
    test_task_name: Optional[str] = Field(None, description="测试任务名称")
    evaluation_model_name: Optional[str] = Field(None, description="评估模型名称")
    strategies: Dict[str, StrategyScoreStats] = Field(..., description="各策略整体统计")


class ComprehensiveEvaluationStatsResponse(BaseModel):
    """综合评估统计响应"""
    comparison_id: str = Field(..., description="对比ID")
    comparison_name: str = Field(..., description="对比名称")
    status: str = Field(..., description="对比状态")
    overall_stats: OverallStats = Field(..., description="整体统计信息")
    template_stats: List[TemplateDetailStats] = Field(..., description="各模板详细统计")

