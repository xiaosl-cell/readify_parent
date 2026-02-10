"""
Evaluation Comparison API endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.evaluation import EvaluationService
from app.schemas.evaluation import (
    EvaluationComparisonCreate,
    EvaluationComparisonUpdate,
    EvaluationComparisonResponse,
    EvaluationComparisonListResponse,
    EvaluationComparisonStatusResponse,
    EvaluationComparisonStartRequest,
    EvaluationResultResponse,
    EvaluationResultListResponse,
    EvaluationComparisonStatsResponse,
    EvaluationTemplateDimensionStatsListResponse,
    ComprehensiveEvaluationStatsResponse
)

router = APIRouter()


@router.post("/", response_model=EvaluationComparisonResponse, summary="创建评估对比")
def create_comparison(
    comparison_in: EvaluationComparisonCreate,
    db: Session = Depends(get_db)
):
    """
    创建评估对比
    
    - **comparison_name**: 对比名称
    - **comparison_description**: 对比描述（可选）
    - **test_task_id**: 测试任务ID
    - **evaluation_model_id**: 评估模型ID（可选，但当评估策略中包含需要LLM评估的策略时必填）
    - **remarks**: 备注信息（可选）
    - **created_by**: 创建人ID（可选）
    
    测试任务必须是已完成状态，且有成功的执行记录。
    
    **评估策略自动识别**：
    - 评估策略不需要手动指定，系统会自动从测试任务的执行记录中获取评估策略配置
    - 每个执行记录在创建时已经保存了其对应的提示词模板的评估策略快照（evaluation_strategies_snapshot）
    
    **评估模型要求**：
    - 如果评估策略中包含 `answer_accuracy`（答案准确率）或 `factual_correctness`（事实正确性），
      则必须提供 `evaluation_model_id`
    - 评估模型用于调用 LLM 来评估答案的准确性和事实正确性
    - 其他策略（精确匹配、语义相似性、BLEU、ROUGE）不需要评估模型
    
    系统会自动：
    1. 收集测试任务中所有执行记录配置的评估策略（去重）
    2. 检查是否需要评估模型，如果需要但未提供则返回错误
    3. 为每个执行记录根据其配置的策略创建对应的评估结果记录
    4. 不同的执行记录可能有不同的评估策略组合
    
    支持的评估策略：
    - exact_match: 精确匹配
    - answer_accuracy: 答案准确率 ⚠️ 需要评估模型
    - factual_correctness: 事实正确性 ⚠️ 需要评估模型
    - semantic_similarity: 语义相似性
    - bleu: BLEU
    - rouge: ROUGE
    """
    service = EvaluationService(db)
    return service.create_comparison(comparison_in)


@router.get("/", response_model=EvaluationComparisonListResponse, summary="获取评估对比列表")
def get_comparisons(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数上限"),
    keyword: Optional[str] = Query(None, description="关键词搜索（对比名称、描述）"),
    status: Optional[str] = Query(None, description="状态过滤：pending/running/completed/failed"),
    test_task_id: Optional[str] = Query(None, description="测试任务ID过滤"),
    db: Session = Depends(get_db)
):
    """
    获取评估对比列表，支持分页和过滤
    """
    service = EvaluationService(db)
    return service.get_comparisons(
        skip=skip,
        limit=limit,
        keyword=keyword,
        status=status,
        test_task_id=test_task_id
    )


@router.get("/{comparison_id}", response_model=EvaluationComparisonResponse, summary="获取评估对比详情")
def get_comparison(
    comparison_id: str,
    db: Session = Depends(get_db)
):
    """
    根据ID获取评估对比详情
    """
    service = EvaluationService(db)
    comparison = service.get_comparison(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="找不到评估对比")
    return comparison


@router.put("/{comparison_id}", response_model=EvaluationComparisonResponse, summary="更新评估对比")
def update_comparison(
    comparison_id: str,
    comparison_in: EvaluationComparisonUpdate,
    db: Session = Depends(get_db)
):
    """
    更新评估对比基本信息（名称、描述、备注）
    """
    service = EvaluationService(db)
    comparison = service.update_comparison(comparison_id, comparison_in)
    if not comparison:
        raise HTTPException(status_code=404, detail="找不到评估对比")
    return comparison


@router.delete("/{comparison_id}", summary="删除评估对比")
def delete_comparison(
    comparison_id: str,
    db: Session = Depends(get_db)
):
    """
    删除评估对比及其所有结果记录
    """
    service = EvaluationService(db)
    success = service.delete_comparison(comparison_id)
    if not success:
        raise HTTPException(status_code=404, detail="找不到评估对比")
    return {"message": "评估对比删除成功"}


@router.post("/{comparison_id}/start", response_model=EvaluationComparisonResponse, summary="启动评估对比")
def start_comparison(
    comparison_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    启动评估对比计算
    
    - 只有状态为 pending 或 failed 的对比可以启动
    - 计算过程在后台异步执行
    - 根据选择的评估策略分别计算每个执行记录的评估分数
    """
    service = EvaluationService(db)
    return service.start_comparison(comparison_id, background_tasks)


@router.post("/{comparison_id}/restart", response_model=EvaluationComparisonResponse, summary="重启评估对比")
def restart_comparison(
    comparison_id: str,
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="是否强制重启（忽略10分钟限制）"),
    db: Session = Depends(get_db)
):
    """
    重启评估对比计算
    
    **使用场景**：
    - 评估任务运行中但长时间无进展
    - 评估任务已失败，需要重新运行
    - 评估任务未完成，需要继续执行剩余用例
    
    **重启条件**：
    - `pending`、`failed` 状态：可以直接重启
    - `running` 状态：
      - 默认需要最后更新时间超过 10 分钟才能重启
      - 可以通过 `force=true` 参数强制重启（谨慎使用）
    - `completed` 状态：不允许重启
    
    **重启行为**：
    - 只会重新执行状态为 `pending` 的评估结果
    - 已成功或已失败的评估结果不会重新执行
    - 计算过程在后台异步执行
    
    **参数说明**：
    - `force`: 
      - `false`（默认）：运行中的任务需要等待10分钟无更新才能重启
      - `true`：立即重启，忽略时间限制（适用于确认任务已卡住的情况）
    
    **示例**：
    ```
    # 正常重启（需要满足10分钟条件）
    POST /api/v1/evaluations/{comparison_id}/restart
    
    # 强制重启（立即重启）
    POST /api/v1/evaluations/{comparison_id}/restart?force=true
    ```
    """
    service = EvaluationService(db)
    return service.restart_comparison(comparison_id, background_tasks, force=force)


@router.post("/check-timeout", summary="检查并标记超时的评估对比")
def check_timeout_comparisons(
    db: Session = Depends(get_db)
):
    """
    检查并标记超时的评估对比
    
    **功能说明**：
    - 检查所有运行中（`running`）的评估对比
    - 如果最后更新时间超过 30 分钟，自动标记为失败（`failed`）
    - 标记为失败后，可以通过启动接口重新运行
    
    **使用场景**：
    - 可以手动调用此接口进行检查
    - 建议配置定时任务（如每5-10分钟）自动调用此接口
    - 用于清理长时间卡住的评估任务
    
    **返回**：
    - 被标记为失败的评估对比ID列表
    - 如果没有超时任务，返回空列表
    
    **示例**：
    ```json
    {
      "message": "检查完成",
      "marked_count": 2,
      "marked_ids": ["comp-123", "comp-456"]
    }
    ```
    """
    service = EvaluationService(db)
    marked_ids = service.check_and_mark_timeout_comparisons()
    
    return {
        "message": "检查完成",
        "marked_count": len(marked_ids),
        "marked_ids": marked_ids
    }


@router.get("/{comparison_id}/status", response_model=EvaluationComparisonStatusResponse, summary="获取评估对比状态")
def get_comparison_status(
    comparison_id: str,
    db: Session = Depends(get_db)
):
    """
    获取评估对比的执行状态和进度
    """
    service = EvaluationService(db)
    status = service.get_comparison_status(comparison_id)
    if not status:
        raise HTTPException(status_code=404, detail="找不到评估对比")
    return status


@router.get("/{comparison_id}/stats", response_model=EvaluationComparisonStatsResponse, summary="获取评估对比统计")
def get_comparison_stats(
    comparison_id: str,
    db: Session = Depends(get_db)
):
    """
    获取评估对比的统计信息，包括各评估策略的分数分布
    """
    service = EvaluationService(db)
    stats = service.get_comparison_stats(comparison_id)
    if not stats:
        raise HTTPException(status_code=404, detail="找不到评估对比")
    return stats


@router.get("/{comparison_id}/template-stats", response_model=EvaluationTemplateDimensionStatsListResponse, summary="获取按模板分组的维度统计")
def get_template_dimension_stats(
    comparison_id: str,
    db: Session = Depends(get_db)
):
    """
    获取按提示词模板分组的维度统计信息
    
    - 返回每个模板在每个评估策略上的平均分、最小值、最大值和样本数量
    - 用于对比不同提示词模板在各个维度上的表现
    - 在评估完成后自动计算并存储
    
    返回的统计信息包括：
    - 模板ID和名称
    - 评估策略
    - 平均分、最小分、最大分
    - 样本数量
    """
    service = EvaluationService(db)
    stats = service.get_template_dimension_stats(comparison_id)
    if not stats:
        raise HTTPException(status_code=404, detail="找不到评估对比")
    return stats


@router.get("/{comparison_id}/comprehensive-stats", response_model=ComprehensiveEvaluationStatsResponse, summary="获取综合评估统计")
def get_comprehensive_evaluation_stats(
    comparison_id: str,
    db: Session = Depends(get_db)
):
    """
    获取综合评估统计信息，包含三层结构：
    
    **1. 整体统计信息（overall_stats）**
    - 总用例数量
    - 总模板数量
    - 各评估策略的整体统计（平均分、最小值、最大值、样本数）
    
    **2. 模板统计信息（template_stats）**
    - 每个模板的基本信息（ID、名称、用例数量）
    - 该模板下各评估策略的统计（平均分、最小值、最大值、样本数）
    - 该模板下所有用例的详细信息
    
    **3. 用例详细信息（嵌套在模板下）**
    - 每个用例的基本信息（ID、名称）
    - 该用例在各评估策略上的得分和状态
    
    **使用场景**：
    - 全面了解评估结果的整体表现
    - 对比不同模板的效果差异
    - 查看具体用例在各维度上的得分
    - 分析哪些模板或用例表现较好/较差
    
    **响应结构示例**：
    ```json
    {
      "comparison_id": "comp-123",
      "comparison_name": "GPT-4 vs Claude",
      "status": "completed",
      "overall_stats": {
        "total_use_cases": 20,
        "total_templates": 3,
        "strategies": {
          "exact_match": {"avg": 0.8, "min": 0.0, "max": 1.0, "count": 20},
          "semantic_similarity": {"avg": 0.85, "min": 0.65, "max": 0.98, "count": 20}
        }
      },
      "template_stats": [
        {
          "template_id": "tpl-001",
          "template_name": "简洁提示词",
          "use_case_count": 10,
          "strategies": {
            "exact_match": {"avg": 0.75, "min": 0.0, "max": 1.0, "count": 10}
          },
          "use_cases": [
            {
              "use_case_id": "case-001",
              "use_case_name": "用例1",
              "results": [
                {"strategy": "exact_match", "score": 0.85, "status": "success"},
                {"strategy": "semantic_similarity", "score": 0.92, "status": "success"}
              ]
            }
          ]
        }
      ]
    }
    ```
    """
    service = EvaluationService(db)
    stats = service.get_comprehensive_evaluation_stats(comparison_id)
    if not stats:
        raise HTTPException(status_code=404, detail="找不到评估对比")
    return stats


# ============= 评估结果相关接口 =============

@router.get("/{comparison_id}/results", response_model=EvaluationResultListResponse, summary="获取评估结果列表")
def get_results(
    comparison_id: str,
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数上限"),
    min_score: Optional[float] = Query(None, description="最小分数过滤"),
    max_score: Optional[float] = Query(None, description="最大分数过滤"),
    status: Optional[str] = Query(None, description="状态过滤：pending/success/failed"),
    evaluation_strategy: Optional[str] = Query(None, description="评估策略过滤"),
    db: Session = Depends(get_db)
):
    """
    获取评估结果列表，支持分页和过滤
    
    - 结果按分数降序排列
    - 可以按分数范围过滤，用于找出分数过高或过低的用例
    - 可以按评估策略过滤
    """
    service = EvaluationService(db)
    return service.get_results(
        comparison_id=comparison_id,
        skip=skip,
        limit=limit,
        min_score=min_score,
        max_score=max_score,
        status=status,
        evaluation_strategy=evaluation_strategy
    )


@router.get("/results/{result_id}", response_model=EvaluationResultResponse, summary="获取评估结果详情")
def get_result(
    result_id: str,
    db: Session = Depends(get_db)
):
    """
    根据ID获取评估结果详情
    """
    service = EvaluationService(db)
    result = service.get_result(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="找不到评估结果")
    return result

