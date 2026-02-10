"""
Evaluation Comparison service
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any, Set
from sqlalchemy.orm import Session
from fastapi import HTTPException, BackgroundTasks
import logging

from ragas.dataset_schema import SingleTurnSample
from ragas.metrics import ExactMatch, AnswerAccuracy, BleuScore, RougeScore, ChrfScore
from ragas.metrics._factual_correctness import FactualCorrectness
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI

from app.repositories.evaluation import (
    EvaluationComparisonRepository, 
    EvaluationResultRepository,
    EvaluationTemplateDimensionStatsRepository
)
from app.repositories.test_task import TestTaskRepository, TestExecutionRepository
from app.repositories.prompt_use_case import PromptUseCaseRepository
from app.repositories.prompt_template import PromptTemplateRepository
from app.services.sentence_bert import get_sentence_bert_service
from app.schemas.evaluation import (
    EvaluationComparisonCreate,
    EvaluationComparisonUpdate,
    EvaluationComparisonResponse,
    EvaluationComparisonListResponse,
    EvaluationComparisonStatusResponse,
    EvaluationResultResponse,
    EvaluationResultListResponse,
    EvaluationComparisonStatsResponse
)
from app.models.evaluation import ComparisonStatus, ResultStatus, EvaluationStrategy
from app.repositories.ai_model import AIModelRepository

logger = logging.getLogger(__name__)

# 需要 LLM 评估的策略
LLM_EVALUATION_STRATEGIES = {
    EvaluationStrategy.ANSWER_ACCURACY.value,
    EvaluationStrategy.FACTUAL_CORRECTNESS.value
}


class EvaluationService:
    """
    评估对比业务逻辑
    """
    
    def __init__(self, db: Session):
        self.comparison_repository = EvaluationComparisonRepository(db)
        self.result_repository = EvaluationResultRepository(db)
        self.template_stats_repository = EvaluationTemplateDimensionStatsRepository(db)
        self.task_repository = TestTaskRepository(db)
        self.execution_repository = TestExecutionRepository(db)
        self.use_case_repository = PromptUseCaseRepository(db)
        self.template_repository = PromptTemplateRepository(db)
        self.ai_model_repository = AIModelRepository(db)
        self.db = db
    
    def create_comparison(self, comparison_in: EvaluationComparisonCreate) -> EvaluationComparisonResponse:
        """
        创建评估对比
        
        Args:
            comparison_in: 评估对比创建数据
            
        Returns:
            创建的评估对比
            
        Raises:
            HTTPException: 如果任务不存在或任务未完成
        """
        # 验证测试任务是否存在
        test_task = self.task_repository.get(comparison_in.test_task_id)
        if not test_task:
            raise HTTPException(
                status_code=404,
                detail=f"找不到 ID 为 '{comparison_in.test_task_id}' 的测试任务"
            )
        
        # 验证任务是否已完成
        if test_task.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"测试任务必须已完成（当前状态：{test_task.status}）"
            )
        
        # 获取任务的成功执行记录
        executions = self.execution_repository.get_by_task_id_and_status(
            task_id=comparison_in.test_task_id,
            status="success",
            skip=0,
            limit=10000
        )
        
        if not executions:
            raise HTTPException(
                status_code=400,
                detail="测试任务没有成功的执行记录"
            )
        
        # 从执行记录中收集所有的评估策略（去重）
        all_strategies = set()
        for execution in executions:
            if execution.evaluation_strategies_snapshot:
                try:
                    strategies = json.loads(execution.evaluation_strategies_snapshot)
                    if isinstance(strategies, list):
                        all_strategies.update(strategies)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"执行记录 {execution.id} 的评估策略快照解析失败")
        
        if not all_strategies:
            raise HTTPException(
                status_code=400,
                detail="测试任务的执行记录中没有配置评估策略"
            )
        
        # 验证评估策略
        valid_strategies = [s.value for s in EvaluationStrategy]
        for strategy in all_strategies:
            if strategy not in valid_strategies:
                logger.warning(f"发现无效的评估策略：{strategy}，将被忽略")
                all_strategies.discard(strategy)
        
        if not all_strategies:
            raise HTTPException(
                status_code=400,
                detail="测试任务的执行记录中没有有效的评估策略"
            )
        
        # 检查是否需要评估模型
        needs_llm_evaluation = bool(all_strategies & LLM_EVALUATION_STRATEGIES)
        
        evaluation_model = None
        evaluation_model_name = None
        
        if needs_llm_evaluation:
            # 如果包含需要LLM评估的策略，evaluation_model_id 必填
            if not comparison_in.evaluation_model_id:
                llm_strategies_used = [s for s in all_strategies if s in LLM_EVALUATION_STRATEGIES]
                raise HTTPException(
                    status_code=400,
                    detail=f"评估策略中包含 {', '.join(llm_strategies_used)}，必须提供评估模型ID（evaluation_model_id）"
                )
            
            # 验证评估模型是否存在
            evaluation_model = self.ai_model_repository.get(comparison_in.evaluation_model_id)
            if not evaluation_model:
                raise HTTPException(
                    status_code=404,
                    detail=f"找不到 ID 为 '{comparison_in.evaluation_model_id}' 的评估模型"
                )
            
            evaluation_model_name = evaluation_model.model_name
        
        # 计算总的评估对数
        total_pairs = 0
        for execution in executions:
            if execution.evaluation_strategies_snapshot:
                try:
                    strategies = json.loads(execution.evaluation_strategies_snapshot)
                    if isinstance(strategies, list):
                        # 只计算有效的策略
                        valid_exec_strategies = [s for s in strategies if s in valid_strategies]
                        total_pairs += len(valid_exec_strategies)
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # 创建对比记录
        comparison_dict = {
            "comparison_name": comparison_in.comparison_name,
            "comparison_description": comparison_in.comparison_description,
            "test_task_id": comparison_in.test_task_id,
            "test_task_name": test_task.task_name,
            "evaluation_strategies": json.dumps(sorted(list(all_strategies)), ensure_ascii=False),
            "evaluation_model_id": comparison_in.evaluation_model_id,
            "evaluation_model_name": evaluation_model_name,
            "status": ComparisonStatus.PENDING.value,
            "total_pairs": total_pairs,
            "completed_pairs": 0,
            "remarks": comparison_in.remarks,
            "created_by": comparison_in.created_by,
            "updated_by": comparison_in.created_by
        }
        
        comparison = self.comparison_repository.create(comparison_dict)
        
        # 为每个执行记录创建评估结果记录（根据该执行记录的评估策略）
        for execution in executions:
            if not execution.evaluation_strategies_snapshot:
                continue
            
            try:
                strategies = json.loads(execution.evaluation_strategies_snapshot)
                if not isinstance(strategies, list):
                    continue
                
                # 只为有效的策略创建评估结果
                for strategy in strategies:
                    if strategy not in valid_strategies:
                        continue
                    
                    result_dict = {
                        "comparison_id": comparison.id,
                        "execution_id": execution.id,
                        "prompt_use_case_id": execution.prompt_use_case_id,
                        "prompt_use_case_name": execution.prompt_use_case_name,
                        "model_output": execution.output_result,
                        "reference_answer": execution.reference_answer,
                        "evaluation_strategy": strategy,
                        "status": ResultStatus.PENDING.value,
                        "created_by": comparison_in.created_by,
                        "updated_by": comparison_in.created_by
                    }
                    self.result_repository.create(result_dict)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"跳过执行记录 {execution.id}：评估策略快照解析失败 - {str(e)}")
                continue
        
        self.db.commit()
        
        return EvaluationComparisonResponse.model_validate(comparison)
    
    def get_comparison(self, comparison_id: str) -> Optional[EvaluationComparisonResponse]:
        """
        获取评估对比
        
        Args:
            comparison_id: 对比ID
            
        Returns:
            评估对比或None
        """
        comparison = self.comparison_repository.get(comparison_id)
        if comparison:
            return EvaluationComparisonResponse.model_validate(comparison)
        return None
    
    def get_comparisons(
        self,
        skip: int = 0,
        limit: int = 100,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        test_task_id: Optional[str] = None
    ) -> EvaluationComparisonListResponse:
        """
        获取评估对比列表
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数上限
            keyword: 关键词搜索
            status: 状态过滤
            test_task_id: 测试任务ID
            
        Returns:
            评估对比列表
        """
        items, total = self.comparison_repository.search(
            skip=skip,
            limit=limit,
            keyword=keyword,
            status=status,
            test_task_id=test_task_id
        )
        
        return EvaluationComparisonListResponse(
            total=total,
            items=[EvaluationComparisonResponse.model_validate(c) for c in items]
        )
    
    def update_comparison(
        self,
        comparison_id: str,
        comparison_in: EvaluationComparisonUpdate
    ) -> Optional[EvaluationComparisonResponse]:
        """
        更新评估对比
        
        Args:
            comparison_id: 对比ID
            comparison_in: 更新数据
            
        Returns:
            更新后的对比或None
        """
        comparison = self.comparison_repository.get(comparison_id)
        if not comparison:
            return None
        
        # 只允许更新基本信息，不允许修改状态和统计信息
        update_dict = comparison_in.model_dump(exclude_unset=True, exclude={'status'})
        
        updated_comparison = self.comparison_repository.update(comparison_id, update_dict)
        if updated_comparison:
            self.db.commit()
            return EvaluationComparisonResponse.model_validate(updated_comparison)
        return None
    
    def delete_comparison(self, comparison_id: str) -> bool:
        """
        删除评估对比
        
        Args:
            comparison_id: 对比ID
            
        Returns:
            是否删除成功
        """
        success = self.comparison_repository.delete(comparison_id)
        if success:
            self.db.commit()
        return success
    
    def get_comparison_status(self, comparison_id: str) -> Optional[EvaluationComparisonStatusResponse]:
        """
        获取对比执行状态
        
        Args:
            comparison_id: 对比ID
            
        Returns:
            对比状态或None
        """
        comparison = self.comparison_repository.get(comparison_id)
        if not comparison:
            return None
        
        progress_percentage = 0.0
        if comparison.total_pairs > 0:
            progress_percentage = (comparison.completed_pairs / comparison.total_pairs) * 100
        
        return EvaluationComparisonStatusResponse(
            comparison_id=comparison.id,
            status=comparison.status,
            total_pairs=comparison.total_pairs,
            completed_pairs=comparison.completed_pairs,
            progress_percentage=round(progress_percentage, 2)
        )
    
    def start_comparison(self, comparison_id: str, background_tasks: BackgroundTasks) -> EvaluationComparisonResponse:
        """
        启动评估对比计算
        
        Args:
            comparison_id: 对比ID
            background_tasks: FastAPI 后台任务
            
        Returns:
            更新后的对比
            
        Raises:
            HTTPException: 如果对比不存在或状态不允许启动
        """
        comparison = self.comparison_repository.get(comparison_id)
        if not comparison:
            raise HTTPException(status_code=404, detail="找不到评估对比")
        
        # 只有待执行和失败的对比可以启动
        if comparison.status not in [ComparisonStatus.PENDING.value, ComparisonStatus.FAILED.value]:
            raise HTTPException(
                status_code=400,
                detail=f"无法启动状态为 '{comparison.status}' 的评估对比"
            )
        
        # 更新对比状态为执行中
        comparison.status = ComparisonStatus.RUNNING.value
        self.db.commit()
        
        # 在后台执行对比计算
        background_tasks.add_task(self._execute_comparison_sync, comparison_id)
        
        return EvaluationComparisonResponse.model_validate(comparison)
    
    def restart_comparison(self, comparison_id: str, background_tasks: BackgroundTasks, force: bool = False) -> EvaluationComparisonResponse:
        """
        重启评估对比计算（针对运行中的任务）
        
        Args:
            comparison_id: 对比ID
            background_tasks: FastAPI 后台任务
            force: 是否强制重启（忽略10分钟限制）
            
        Returns:
            更新后的对比
            
        Raises:
            HTTPException: 如果对比不存在或不满足重启条件
        """
        comparison = self.comparison_repository.get(comparison_id)
        if not comparison:
            raise HTTPException(status_code=404, detail="找不到评估对比")
        
        # 检查状态：pending、failed、running 都可以重启
        if comparison.status not in [ComparisonStatus.PENDING.value, ComparisonStatus.FAILED.value, ComparisonStatus.RUNNING.value]:
            raise HTTPException(
                status_code=400,
                detail=f"无法重启状态为 '{comparison.status}' 的评估对比（只能重启 pending、failed 或 running 状态的任务）"
            )
        
        # 如果是 running 状态，检查是否满足重启条件（10分钟未更新）
        if comparison.status == ComparisonStatus.RUNNING.value and not force:
            can_restart, message = self._check_can_restart(comparison)
            if not can_restart:
                raise HTTPException(status_code=400, detail=message)
        
        # 更新对比状态为执行中
        comparison.status = ComparisonStatus.RUNNING.value
        comparison.updated_at = datetime.utcnow()
        self.db.commit()
        
        # 在后台执行对比计算
        background_tasks.add_task(self._execute_comparison_sync, comparison_id)
        
        return EvaluationComparisonResponse.model_validate(comparison)
    
    def _check_can_restart(self, comparison) -> Tuple[bool, str]:
        """
        检查是否可以重启运行中的任务
        
        Args:
            comparison: 对比对象
            
        Returns:
            (是否可以重启, 消息)
        """
        if comparison.status != ComparisonStatus.RUNNING.value:
            return True, "非运行中状态，可以重启"
        
        # 检查最后更新时间
        now = datetime.utcnow()
        time_since_update = now - comparison.updated_at
        
        # 10分钟 = 600秒
        if time_since_update.total_seconds() < 600:
            remaining_seconds = 600 - time_since_update.total_seconds()
            remaining_minutes = int(remaining_seconds / 60)
            return False, f"任务运行中且最近有更新，需等待 {remaining_minutes} 分钟后才能重启"
        
        return True, "任务超过10分钟未更新，可以重启"
    
    def check_and_mark_timeout_comparisons(self) -> List[str]:
        """
        检查并标记超时的评估对比（30分钟未更新的运行中任务）
        
        Returns:
            被标记为失败的对比ID列表
        """
        marked_ids = []
        
        try:
            # 查询所有运行中的对比
            running_comparisons, _ = self.comparison_repository.search(
                skip=0,
                limit=10000,
                status=ComparisonStatus.RUNNING.value
            )
            
            now = datetime.utcnow()
            timeout_threshold = timedelta(minutes=30)
            
            for comparison in running_comparisons:
                time_since_update = now - comparison.updated_at
                
                # 检查是否超过30分钟
                if time_since_update >= timeout_threshold:
                    logger.warning(
                        f"评估对比 {comparison.id} 超过30分钟未更新，将状态标记为失败。"
                        f"最后更新时间: {comparison.updated_at}, 已过时长: {time_since_update}"
                    )
                    
                    comparison.status = ComparisonStatus.FAILED.value
                    marked_ids.append(comparison.id)
            
            if marked_ids:
                self.db.commit()
                logger.info(f"已标记 {len(marked_ids)} 个超时评估对比为失败: {marked_ids}")
            
        except Exception as e:
            logger.error(f"检查超时评估对比时出错: {str(e)}")
            self.db.rollback()
        
        return marked_ids
    
    def _execute_comparison_sync(self, comparison_id: str):
        """
        执行对比计算（同步包装方法）
        
        Args:
            comparison_id: 对比ID
        """
        # 创建新的事件循环并运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._execute_comparison(comparison_id))
        finally:
            loop.close()
    
    async def _execute_comparison(self, comparison_id: str):
        """
        执行对比计算（异步方法）
        
        Args:
            comparison_id: 对比ID
        """
        try:
            # 获取对比信息
            comparison = self.comparison_repository.get(comparison_id)
            if not comparison:
                return
            
            # 设置当前comparison_id，供评估方法使用（如_evaluate_answer_accuracy）
            self._current_comparison_id = comparison_id
            
            # 获取待计算的结果记录
            pending_results = self.result_repository.get_pending_results(comparison_id, limit=10000)
            
            # 按策略分组计算
            if pending_results:
                # 获取已完成的数量（处理重新启动的情况）
                already_completed = (
                    self.result_repository.count_by_comparison_and_status(comparison_id, ResultStatus.SUCCESS.value) +
                    self.result_repository.count_by_comparison_and_status(comparison_id, ResultStatus.FAILED.value)
                )
                
                total = len(pending_results)
                for index, result in enumerate(pending_results, 1):
                    try:
                        # 获取用户输入（从关联的execution记录）
                        user_input = ""
                        if result.execution and result.execution.rendered_user_prompt:
                            user_input = result.execution.rendered_user_prompt
                        
                        # 根据策略调用相应的评估方法
                        score, details = await self._evaluate_by_strategy(
                            result.evaluation_strategy,
                            result.model_output or "",
                            result.reference_answer or "",
                            user_input=user_input
                        )
                        
                        result.score = score
                        result.result_details = json.dumps(details, ensure_ascii=False) if details else None
                        result.status = ResultStatus.SUCCESS.value
                        result.error_message = None
                        
                    except Exception as e:
                        logger.error(f"Failed to evaluate result {result.id}: {str(e)}")
                        result.status = ResultStatus.FAILED.value
                        result.error_message = str(e)
                    
                    # 直接更新 completed_pairs 计数（包含已完成的数量）
                    comparison.completed_pairs = already_completed + index
                    
                    # 每处理完一个结果就立即提交到数据库
                    self.db.commit()
                    
                    # 记录进度日志
                    if index % 10 == 0 or index == total:
                        current_total = already_completed + index
                        progress = current_total * 100 // comparison.total_pairs if comparison.total_pairs > 0 else 0
                        logger.info(f"评估对比 {comparison_id} 进度: {current_total}/{comparison.total_pairs} ({progress}%)")
            
            # 清除当前comparison_id
            if hasattr(self, '_current_comparison_id'):
                delattr(self, '_current_comparison_id')
            
            # 更新最终状态（统计信息在循环中已实时更新）
            self._finalize_comparison_status(comparison_id)
            
            logger.info(f"评估对比 {comparison_id} 执行完成")
            
        except Exception as e:
            logger.error(f"Failed to execute comparison: {str(e)}")
            # 清除当前comparison_id
            if hasattr(self, '_current_comparison_id'):
                delattr(self, '_current_comparison_id')
            # 对比执行出错
            comparison = self.comparison_repository.get(comparison_id)
            if comparison:
                comparison.status = ComparisonStatus.FAILED.value
                self.db.commit()
    
    async def _evaluate_by_strategy(
        self, 
        strategy: str, 
        model_output: str, 
        reference_answer: str,
        user_input: str = ""
    ) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
        """
        根据策略评估模型输出
        
        Args:
            strategy: 评估策略
            model_output: 模型输出
            reference_answer: 参考答案
            user_input: 用户输入（可选，某些策略如AnswerAccuracy需要）
            
        Returns:
            (分数, 详情字典)
        """
        if strategy == EvaluationStrategy.EXACT_MATCH.value:
            return await self._evaluate_exact_match(model_output, reference_answer)
        elif strategy == EvaluationStrategy.JSON_KEY_MATCH.value:
            return await self._evaluate_json_key_match(model_output, reference_answer)
        elif strategy == EvaluationStrategy.ANSWER_ACCURACY.value:
            return await self._evaluate_answer_accuracy(model_output, reference_answer, user_input)
        elif strategy == EvaluationStrategy.FACTUAL_CORRECTNESS.value:
            return await self._evaluate_factual_correctness(model_output, reference_answer)
        elif strategy == EvaluationStrategy.SEMANTIC_SIMILARITY.value:
            return await self._evaluate_semantic_similarity(model_output, reference_answer)
        elif strategy == EvaluationStrategy.BLEU.value:
            return await self._evaluate_bleu(model_output, reference_answer)
        elif strategy == EvaluationStrategy.ROUGE.value:
            return await self._evaluate_rouge(model_output, reference_answer)
        elif strategy == EvaluationStrategy.CHRF.value:
            return await self._evaluate_chrf(model_output, reference_answer)
        else:
            raise ValueError(f"不支持的评估策略：{strategy}")
    
    # ============= 评估策略实现方法（待实现） =============
    
    async def _evaluate_exact_match(
        self, 
        model_output: str, 
        reference_answer: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        精确匹配 - 与参考答案完全一致
        
        使用ragas的ExactMatch指标检查响应是否与参考文本完全相同。
        适用于需要确保生成的响应与预期输出逐字匹配的场景。
        
        Args:
            model_output: 模型输出
            reference_answer: 参考答案
            
        Returns:
            (分数, 详情字典) - 分数为 1.0（完全匹配）或 0.0（不匹配）
        """
        try:
            # 创建SingleTurnSample用于ragas评估
            sample = SingleTurnSample(
                response=model_output,
                reference=reference_answer
            )
            
            # 创建ExactMatch评分器
            scorer = ExactMatch()
            
            # 执行评分
            score = await scorer.single_turn_ascore(sample)
            
            # 构建详情字典
            details = {
                "method": "ragas_exact_match",
                "model_output": model_output,
                "reference_answer": reference_answer,
                "is_exact_match": score == 1.0,
                "output_length": len(model_output),
                "reference_length": len(reference_answer)
            }
            
            logger.info(f"精确匹配评估完成: score={score}, match={score == 1.0}")
            
            return float(score), details
            
        except Exception as e:
            logger.error(f"精确匹配评估失败: {str(e)}")
            raise Exception(f"精确匹配评估失败: {str(e)}")

    async def _evaluate_json_key_match(
        self,
        model_output: str,
        reference_answer: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        JSON 键匹配 - 校验输出是否为 JSON 且键集合与参考答案一致。
        
        Args:
            model_output: 模型输出
            reference_answer: 参考答案（期望为 JSON）
        
        Returns:
            (分数, 详情字典) - 键集合一致且输出可解析为 JSON 时为 1.0，否则为 0.0
        """
        try:
            reference_obj = json.loads(reference_answer)
        except json.JSONDecodeError as e:
            logger.error(f"参考答案不是有效 JSON，无法进行键校验: {str(e)}")
            raise ValueError("参考答案不是有效的 JSON，无法进行键校验")
        
        reference_keys = self._extract_json_keys(reference_obj)
        details: Dict[str, Any] = {
            "method": "json_key_match",
            "reference_is_valid_json": True,
            "reference_keys": sorted(reference_keys)
        }
        
        try:
            output_obj = json.loads(model_output)
        except json.JSONDecodeError as e:
            details.update({
                "output_is_valid_json": False,
                "error": f"输出不是有效 JSON: {str(e)}"
            })
            logger.info("JSON 键匹配评估：输出不是有效 JSON")
            return 0.0, details
        
        output_keys = self._extract_json_keys(output_obj)
        missing_keys = reference_keys - output_keys
        extra_keys = output_keys - reference_keys
        keys_match = not missing_keys and not extra_keys
        
        details.update({
            "output_is_valid_json": True,
            "output_keys": sorted(output_keys),
            "missing_keys": sorted(missing_keys),
            "extra_keys": sorted(extra_keys),
            "keys_match": keys_match
        })
        
        score = 1.0 if keys_match else 0.0
        logger.info(
            f"JSON 键匹配评估完成: match={keys_match}, missing={len(missing_keys)}, extra={len(extra_keys)}"
        )
        
        return score, details
    
    async def _evaluate_answer_accuracy(
        self, 
        model_output: str, 
        reference_answer: str,
        user_input: str = ""
    ) -> Tuple[float, Dict[str, Any]]:
        """
        答案准确率 - LLM 评估生成答案与参考答案的语义一致性程度
        
        使用ragas的AnswerAccuracy指标，通过两个独立的"LLM-as-a-Judge"提示来评估
        模型输出与参考答案的一致性。每个评判返回评分(0, 2, 或 4)，然后转换到[0,1]
        范围并取平均值。
        
        Args:
            model_output: 模型输出
            reference_answer: 参考答案
            user_input: 用户输入（可选，用于提供问题上下文）
            
        Returns:
            (分数, 详情字典) - 分数范围 0.0-1.0
        """
        try:
            # 获取当前对比的evaluation_model
            comparison_id = None
            evaluation_model = None
            
            # 从当前执行上下文中获取comparison信息
            # 注意：这需要在调用_evaluate_answer_accuracy之前设置
            if hasattr(self, '_current_comparison_id'):
                comparison_id = self._current_comparison_id
                comparison = self.comparison_repository.get(comparison_id)
                if comparison and comparison.evaluation_model_id:
                    evaluation_model = self.ai_model_repository.get(comparison.evaluation_model_id)
            
            if not evaluation_model:
                raise ValueError("未找到评估模型，答案准确率需要指定evaluation_model_id")
            
            # 创建OpenAI兼容的LLM客户端
            # 使用evaluation_model的配置
            # 构建base_url（去掉可能的/v1/chat/completions后缀）
            base_url = evaluation_model.api_endpoint.rstrip('/')
            if base_url.endswith('/v1/chat/completions'):
                base_url = base_url[:-len('/v1/chat/completions')]
            elif base_url.endswith('/chat/completions'):
                base_url = base_url[:-len('/chat/completions')]
            if not base_url.endswith('/v1'):
                base_url = base_url + '/v1'
            
            llm = ChatOpenAI(
                model=evaluation_model.model_name,
                base_url=base_url,
                api_key=evaluation_model.api_key or "dummy-key",
                temperature=0.0,  # 评估时使用确定性输出
                timeout=300.0
            )
            
            # 包装为Ragas LLM
            ragas_llm = LangchainLLMWrapper(llm)
            
            # 创建SingleTurnSample用于ragas评估
            # AnswerAccuracy需要user_input（问题）, response（模型输出）, reference（参考答案）
            sample = SingleTurnSample(
                user_input=user_input,  # 用户问题/提示词
                response=model_output,
                reference=reference_answer
            )
            
            # 创建AnswerAccuracy评分器
            scorer = AnswerAccuracy(llm=ragas_llm)
            
            # 执行评分
            score = await scorer.single_turn_ascore(sample)
            
            # 构建详情字典
            details = {
                "method": "ragas_answer_accuracy",
                "evaluation_model": evaluation_model.model_name,
                "evaluation_model_id": evaluation_model.model_id,
                "user_input": user_input,
                "model_output": model_output,
                "reference_answer": reference_answer,
                "output_length": len(model_output),
                "reference_length": len(reference_answer),
                "description": "使用两个独立的LLM评判进行评分，每个返回0/2/4，转换到0-1范围后取平均"
            }
            
            logger.info(f"答案准确率评估完成: score={score}, model={evaluation_model.model_name}")
            
            return float(score), details
            
        except Exception as e:
            logger.error(f"答案准确率评估失败: {str(e)}")
            raise Exception(f"答案准确率评估失败: {str(e)}")
    
    async def _evaluate_factual_correctness(
        self, 
        model_output: str, 
        reference_answer: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        事实正确性 - 检查 LLM 生成的答案与标准答案相比，事实是否正确
        
        使用ragas的FactualCorrectness指标，通过LLM将response和reference分解为claims，
        然后使用自然语言推理确定事实重叠。通过precision、recall和F1 score量化事实准确性。
        
        计算公式：
        - TP = response中存在于reference中的claims数量
        - FP = response中不存在于reference中的claims数量  
        - FN = reference中不存在于response中的claims数量
        - F1 Score = 2 × Precision × Recall / (Precision + Recall)
        
        Args:
            model_output: 模型输出
            reference_answer: 参考答案
            
        Returns:
            (分数, 详情字典) - 分数范围 0.0-1.0，默认使用F1模式
        """
        try:
            # 获取当前对比的evaluation_model
            comparison_id = None
            evaluation_model = None
            
            # 从当前执行上下文中获取comparison信息
            if hasattr(self, '_current_comparison_id'):
                comparison_id = self._current_comparison_id
                comparison = self.comparison_repository.get(comparison_id)
                if comparison and comparison.evaluation_model_id:
                    evaluation_model = self.ai_model_repository.get(comparison.evaluation_model_id)
            
            if not evaluation_model:
                raise ValueError("未找到评估模型，事实正确性需要指定evaluation_model_id")
            
            # 创建OpenAI兼容的LLM客户端
            # 构建base_url（去掉可能的/v1/chat/completions后缀）
            base_url = evaluation_model.api_endpoint.rstrip('/')
            if base_url.endswith('/v1/chat/completions'):
                base_url = base_url[:-len('/v1/chat/completions')]
            elif base_url.endswith('/chat/completions'):
                base_url = base_url[:-len('/chat/completions')]
            if not base_url.endswith('/v1'):
                base_url = base_url + '/v1'
            
            llm = ChatOpenAI(
                model=evaluation_model.model_name,
                base_url=base_url,
                api_key=evaluation_model.api_key or "dummy-key",
                temperature=0.0,  # 评估时使用确定性输出
                timeout=300.0
            )
            
            # 包装为Ragas LLM
            ragas_llm = LangchainLLMWrapper(llm)
            
            # 创建SingleTurnSample用于ragas评估
            # FactualCorrectness需要response和reference
            sample = SingleTurnSample(
                response=model_output,
                reference=reference_answer
            )
            
            # 创建FactualCorrectness评分器
            # mode: "precision", "recall", 或 "F1"（默认）
            # atomicity: "low" 或 "high" - 控制claim分解的细粒度
            # coverage: "low" 或 "high" - 控制claim的完整性
            scorer = FactualCorrectness(
                llm=ragas_llm, 
                mode="F1",  # 使用F1模式，平衡precision和recall
                atomicity="high",  # 高原子性，分解为更细粒度的claims
                coverage="high"  # 高覆盖度，捕获所有信息
            )
            
            # 执行评分
            score = await scorer.single_turn_ascore(sample)
            
            # 构建详情字典
            details = {
                "method": "ragas_factual_correctness",
                "evaluation_model": evaluation_model.model_name,
                "evaluation_model_id": evaluation_model.model_id,
                "model_output": model_output,
                "reference_answer": reference_answer,
                "output_length": len(model_output),
                "reference_length": len(reference_answer),
                "mode": "F1",
                "atomicity": "high",
                "coverage": "high",
                "description": "使用LLM将response和reference分解为claims，通过自然语言推理计算F1 score来量化事实准确性"
            }
            
            logger.info(f"事实正确性评估完成: score={score}, model={evaluation_model.model_name}")
            
            return float(score), details
            
        except Exception as e:
            logger.error(f"事实正确性评估失败: {str(e)}")
            raise Exception(f"事实正确性评估失败: {str(e)}")
    
    async def _evaluate_semantic_similarity(
        self, 
        model_output: str, 
        reference_answer: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        语义相似性 - 使用 Sentence-BERT 模型计算生成内容与参考答案的语义相似度
        
        使用项目中预加载的 paraphrase-multilingual-MiniLM-L12-v2 模型，
        通过计算模型输出和参考答案的向量表示之间的余弦相似度来量化语义相似性。
        
        该方法不依赖 LLM，计算速度快，成本低，适合大规模评估。
        
        Args:
            model_output: 模型输出
            reference_answer: 参考答案
            
        Returns:
            (分数, 详情字典) - 分数范围 0.0-1.0
        """
        try:
            # 获取 Sentence-BERT 服务实例
            sbert_service = get_sentence_bert_service()
            
            # 检查模型是否已加载
            if not sbert_service.is_model_loaded():
                raise RuntimeError("Sentence-BERT 模型未加载")
            
            # 检查输入是否为空
            if not model_output or not reference_answer:
                logger.warning("模型输出或参考答案为空，语义相似度设为0")
                return 0.0, {
                    "method": "sentence_bert_cosine_similarity",
                    "model_output": model_output or "",
                    "reference_answer": reference_answer or "",
                    "error": "输入为空",
                    "description": "使用 Sentence-BERT 计算余弦相似度"
                }
            
            # 计算语义相似度（余弦相似度）
            similarity_score = sbert_service.compute_similarity(
                model_output, 
                reference_answer
            )
            
            # 获取模型信息
            model_info = sbert_service.get_model_info()
            
            # 构建详情字典
            details = {
                "method": "sentence_bert_cosine_similarity",
                "model_name": "paraphrase-multilingual-MiniLM-L12-v2",
                "model_path": model_info.get("model_path", "unknown"),
                "similarity_metric": "cosine",
                "model_output": model_output,
                "reference_answer": reference_answer,
                "output_length": len(model_output),
                "reference_length": len(reference_answer),
                "description": "使用 Sentence-BERT 模型计算文本向量的余弦相似度，范围 0-1，值越高表示语义越相似"
            }
            
            logger.info(f"语义相似性评估完成: score={similarity_score:.4f}")
            
            return float(similarity_score), details
            
        except Exception as e:
            logger.error(f"语义相似性评估失败: {str(e)}")
            raise Exception(f"语义相似性评估失败: {str(e)}")
    
    async def _evaluate_bleu(
        self, 
        model_output: str, 
        reference_answer: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        BLEU - 基于 n-gram 匹配评估生成文本质量，常用于机器翻译
        
        使用 ragas 的 BleuScore 指标，通过计算 response 和 reference 之间的
        n-gram precision 和 brevity penalty 来评估文本质量。
        
        BLEU (Bilingual Evaluation Understudy) 最初设计用于机器翻译评估，
        但也广泛应用于其他自然语言生成任务。该方法不依赖 LLM，计算快速。
        
        评分机制：
        - 基于 n-gram（1-4）的精确匹配
        - 考虑简短惩罚（brevity penalty）
        - 范围 0.0-1.0，1.0 表示完美匹配
        
        Args:
            model_output: 模型输出
            reference_answer: 参考答案
            
        Returns:
            (分数, 详情字典) - 分数范围 0.0-1.0
        """
        try:
            # 检查输入是否为空
            if not model_output or not reference_answer:
                logger.warning("模型输出或参考答案为空，BLEU 分数设为 0")
                return 0.0, {
                    "method": "ragas_bleu_score",
                    "model_output": model_output or "",
                    "reference_answer": reference_answer or "",
                    "error": "输入为空",
                    "description": "使用 BLEU 评估基于 n-gram 的文本匹配质量"
                }
            
            # 创建 SingleTurnSample 用于 ragas 评估
            sample = SingleTurnSample(
                response=model_output,
                reference=reference_answer
            )
            
            # 创建 BleuScore 评分器
            scorer = BleuScore()
            
            # 执行评分
            score = await scorer.single_turn_ascore(sample)
            
            # 构建详情字典
            details = {
                "method": "ragas_bleu_score",
                "metric_type": "n-gram_precision",
                "n_gram_range": "1-4",
                "includes_brevity_penalty": True,
                "model_output": model_output,
                "reference_answer": reference_answer,
                "output_length": len(model_output),
                "reference_length": len(reference_answer),
                "output_words": len(model_output.split()),
                "reference_words": len(reference_answer.split()),
                "description": "BLEU 评分基于 n-gram 精确匹配和简短惩罚，常用于机器翻译和文本生成质量评估"
            }
            
            logger.info(f"BLEU 评估完成: score={score:.4f}")
            
            return float(score), details
            
        except Exception as e:
            logger.error(f"BLEU 评估失败: {str(e)}")
            raise Exception(f"BLEU 评估失败: {str(e)}")
    
    async def _evaluate_rouge(
        self, 
        model_output: str, 
        reference_answer: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        ROUGE - 基于召回率的 n-gram 重叠度量，常用于文本摘要评估
        
        使用 ragas 的 RougeScore 指标，通过计算 response 和 reference 之间的
        n-gram 召回率、精确率和 F1 分数来评估文本质量。
        
        ROUGE (Recall-Oriented Understudy for Gisting Evaluation) 主要用于评估
        文本摘要质量，关注生成文本对参考文本的覆盖程度。该方法不依赖 LLM。
        
        评分机制：
        - 默认使用 ROUGE-L（最长公共子序列）
        - 默认计算 F1 分数（可配置为 precision 或 recall）
        - 范围 0.0-1.0，1.0 表示完美匹配
        
        Args:
            model_output: 模型输出
            reference_answer: 参考答案
            
        Returns:
            (分数, 详情字典) - 分数范围 0.0-1.0
        """
        try:
            # 检查输入是否为空
            if not model_output or not reference_answer:
                logger.warning("模型输出或参考答案为空，ROUGE 分数设为 0")
                return 0.0, {
                    "method": "ragas_rouge_score",
                    "model_output": model_output or "",
                    "reference_answer": reference_answer or "",
                    "error": "输入为空",
                    "description": "使用 ROUGE 评估基于召回率的文本重叠质量"
                }
            
            # 创建 SingleTurnSample 用于 ragas 评估
            sample = SingleTurnSample(
                response=model_output,
                reference=reference_answer
            )
            
            # 创建 RougeScore 评分器
            # rouge_type: "rougeL" (默认), "rouge1", "rouge2"
            # mode: "fmeasure" (默认), "precision", "recall"
            scorer = RougeScore(rouge_type="rougeL", mode="fmeasure")
            
            # 执行评分
            score = await scorer.single_turn_ascore(sample)
            
            # 构建详情字典
            details = {
                "method": "ragas_rouge_score",
                "rouge_type": "rougeL",
                "mode": "fmeasure",
                "metric_type": "longest_common_subsequence",
                "model_output": model_output,
                "reference_answer": reference_answer,
                "output_length": len(model_output),
                "reference_length": len(reference_answer),
                "output_words": len(model_output.split()),
                "reference_words": len(reference_answer.split()),
                "description": "ROUGE-L 评分基于最长公共子序列，使用 F1 分数，常用于文本摘要质量评估"
            }
            
            logger.info(f"ROUGE 评估完成: score={score:.4f}")
            
            return float(score), details
            
        except Exception as e:
            logger.error(f"ROUGE 评估失败: {str(e)}")
            raise Exception(f"ROUGE 评估失败: {str(e)}")
    
    async def _evaluate_chrf(
        self, 
        model_output: str, 
        reference_answer: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        CHRF - 基于字符级 F-score 的评估指标，对形态丰富的语言更友好
        
        使用 ragas 的 ChrfScore 指标，通过计算字符 n-gram 的 F-score 来评估
        response 和 reference 的相似度。
        
        CHRF (Character n-gram F-score) 与 BLEU 不同，它：
        - 使用字符级 n-gram 而非词级
        - 同时考虑 precision 和 recall
        - 对形态丰富的语言（如中文、德语）更友好
        - 对释义和灵活措辞更宽容
        
        评分机制：
        - 基于字符 n-gram（默认 1-6）
        - 计算 F-score（precision 和 recall 的调和平均）
        - 范围 0.0-1.0，1.0 表示完美匹配
        
        Args:
            model_output: 模型输出
            reference_answer: 参考答案
            
        Returns:
            (分数, 详情字典) - 分数范围 0.0-1.0
        """
        try:
            # 检查输入是否为空
            if not model_output or not reference_answer:
                logger.warning("模型输出或参考答案为空，CHRF 分数设为 0")
                return 0.0, {
                    "method": "ragas_chrf_score",
                    "model_output": model_output or "",
                    "reference_answer": reference_answer or "",
                    "error": "输入为空",
                    "description": "使用 CHRF 评估基于字符 n-gram 的文本质量"
                }
            
            # 创建 SingleTurnSample 用于 ragas 评估
            sample = SingleTurnSample(
                response=model_output,
                reference=reference_answer
            )
            
            # 创建 ChrfScore 评分器
            scorer = ChrfScore()
            
            # 执行评分
            score = await scorer.single_turn_ascore(sample)
            
            # 构建详情字典
            details = {
                "method": "ragas_chrf_score",
                "metric_type": "character_n-gram_f-score",
                "n_gram_range": "1-6",
                "considers_precision_recall": True,
                "model_output": model_output,
                "reference_answer": reference_answer,
                "output_length": len(model_output),
                "reference_length": len(reference_answer),
                "output_chars": len(model_output.replace(" ", "")),
                "reference_chars": len(reference_answer.replace(" ", "")),
                "description": "CHRF 评分基于字符级 n-gram F-score，对形态丰富的语言和释义更友好"
            }
            
            logger.info(f"CHRF 评估完成: score={score:.4f}")
            
            return float(score), details
            
        except Exception as e:
            logger.error(f"CHRF 评估失败: {str(e)}")
            raise Exception(f"CHRF 评估失败: {str(e)}")
    
    # ============= 辅助方法 =============

    def _extract_json_keys(self, obj: Any, prefix: str = "") -> Set[str]:
        """
        将 JSON 对象的键展开为扁平集合，使用点号连接嵌套层级。
        列表元素沿用相同前缀，不要求固定长度。
        """
        keys: Set[str] = set()
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current = f"{prefix}.{key}" if prefix else key
                keys.add(current)
                keys.update(self._extract_json_keys(value, current))
        elif isinstance(obj, list):
            for item in obj:
                keys.update(self._extract_json_keys(item, prefix))
        
        return keys
    
    def _update_comparison_statistics(self, comparison_id: str):
        """
        更新对比统计信息
        
        Args:
            comparison_id: 对比ID
        """
        comparison = self.comparison_repository.get(comparison_id)
        if not comparison:
            return
        
        # 统计完成的对数
        completed_count = (
            self.result_repository.count_by_comparison_and_status(comparison_id, ResultStatus.SUCCESS.value) +
            self.result_repository.count_by_comparison_and_status(comparison_id, ResultStatus.FAILED.value)
        )
        
        # 更新统计信息
        comparison.completed_pairs = completed_count
        
        self.db.commit()
    
    def _finalize_comparison_status(self, comparison_id: str):
        """
        完成对比，更新最终状态
        
        Args:
            comparison_id: 对比ID
        """
        comparison = self.comparison_repository.get(comparison_id)
        if not comparison:
            return
        
        # 根据完成情况设置状态
        if comparison.completed_pairs == comparison.total_pairs:
            comparison.status = ComparisonStatus.COMPLETED.value
            
            # 计算各维度的平均分并存储
            self._calculate_and_store_dimension_averages(comparison_id)
            
            # 计算并存储按模板分组的维度统计
            self._calculate_and_store_template_dimension_stats(comparison_id)
        else:
            comparison.status = ComparisonStatus.FAILED.value
        
        self.db.commit()
    
    def _calculate_and_store_dimension_averages(self, comparison_id: str):
        """
        计算并存储各维度的平均分
        
        Args:
            comparison_id: 对比ID
        """
        try:
            # 获取所有策略的统计信息
            strategy_stats = self.result_repository.get_all_strategies_stats(comparison_id)
            
            # 构建维度平均分字典
            dimension_averages = {}
            for strategy, stats in strategy_stats.items():
                if stats.get('avg') is not None:
                    dimension_averages[strategy] = {
                        'average': round(stats['avg'], 4),
                        'min': round(stats['min'], 4) if stats.get('min') is not None else None,
                        'max': round(stats['max'], 4) if stats.get('max') is not None else None,
                        'count': stats.get('count', 0)
                    }
            
            # 存储到数据库
            comparison = self.comparison_repository.get(comparison_id)
            if comparison:
                comparison.dimension_averages = json.dumps(dimension_averages, ensure_ascii=False)
                logger.info(f"已存储评估对比 {comparison_id} 的维度平均分: {dimension_averages}")
        
        except Exception as e:
            logger.error(f"计算维度平均分失败: {str(e)}")
            # 不抛出异常，避免影响评估完成状态
    
    def _calculate_and_store_template_dimension_stats(self, comparison_id: str):
        """
        计算并存储按提示词模板分组的维度统计
        
        Args:
            comparison_id: 对比ID
        """
        try:
            # 先删除该对比已有的模板统计记录
            self.template_stats_repository.delete_by_comparison_id(comparison_id)
            self.db.commit()
            
            # 获取该对比的所有成功的评估结果
            results, _ = self.result_repository.get_by_comparison_id(
                comparison_id=comparison_id,
                status=ResultStatus.SUCCESS.value,
                skip=0,
                limit=10000
            )
            
            # 按 (模板ID, 策略) 分组收集分数
            template_strategy_scores = {}  # {(template_id, strategy): [scores]}
            template_names = {}  # {template_id: template_name}
            
            for result in results:
                if result.score is None or result.prompt_use_case_id is None:
                    continue
                
                # 通过用例ID获取模板ID
                use_case = self.use_case_repository.get(result.prompt_use_case_id)
                if not use_case or not use_case.template_id:
                    logger.warning(f"用例 {result.prompt_use_case_id} 不存在或没有关联模板")
                    continue
                
                template_id = use_case.template_id
                strategy = result.evaluation_strategy
                
                # 记录模板名称
                if template_id not in template_names:
                    template = self.template_repository.get(template_id)
                    template_names[template_id] = template.template_name if template else None
                
                # 添加分数到分组
                key = (template_id, strategy)
                if key not in template_strategy_scores:
                    template_strategy_scores[key] = []
                template_strategy_scores[key].append(result.score)
            
            # 计算每个分组的统计信息并存储
            stats_count = 0
            for (template_id, strategy), scores in template_strategy_scores.items():
                if not scores:
                    continue
                
                avg_score = sum(scores) / len(scores)
                min_score = min(scores)
                max_score = max(scores)
                sample_count = len(scores)
                
                # 创建统计记录
                stats_dict = {
                    'comparison_id': comparison_id,
                    'prompt_template_id': template_id,
                    'prompt_template_name': template_names.get(template_id),
                    'evaluation_strategy': strategy,
                    'avg_score': round(avg_score, 4),
                    'min_score': round(min_score, 4),
                    'max_score': round(max_score, 4),
                    'sample_count': sample_count,
                    'created_by': 'system',
                    'updated_by': 'system'
                }
                
                self.template_stats_repository.create(stats_dict)
                stats_count += 1
            
            self.db.commit()
            logger.info(f"已存储评估对比 {comparison_id} 的模板维度统计，共 {stats_count} 条记录")
        
        except Exception as e:
            logger.error(f"计算模板维度统计失败: {str(e)}")
            self.db.rollback()
            # 不抛出异常，避免影响评估完成状态
    
    # ============= 评估结果相关方法 =============
    
    def get_results(
        self,
        comparison_id: str,
        skip: int = 0,
        limit: int = 100,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        status: Optional[str] = None,
        evaluation_strategy: Optional[str] = None
    ) -> EvaluationResultListResponse:
        """
        获取评估结果列表
        
        Args:
            comparison_id: 对比ID
            skip: 跳过记录数
            limit: 返回记录数上限
            min_score: 最小分数
            max_score: 最大分数
            status: 状态过滤
            evaluation_strategy: 评估策略过滤
            
        Returns:
            评估结果列表
        """
        items, total = self.result_repository.get_by_comparison_id(
            comparison_id=comparison_id,
            skip=skip,
            limit=limit,
            min_score=min_score,
            max_score=max_score,
            status=status,
            evaluation_strategy=evaluation_strategy
        )
        
        return EvaluationResultListResponse(
            total=total,
            items=[EvaluationResultResponse.model_validate(r) for r in items]
        )
    
    def get_result(self, result_id: str) -> Optional[EvaluationResultResponse]:
        """
        获取评估结果详情
        
        Args:
            result_id: 结果ID
            
        Returns:
            评估结果或None
        """
        result = self.result_repository.get(result_id)
        if result:
            return EvaluationResultResponse.model_validate(result)
        return None
    
    def get_comparison_stats(self, comparison_id: str) -> Optional[EvaluationComparisonStatsResponse]:
        """
        获取评估对比统计信息
        
        Args:
            comparison_id: 对比ID
            
        Returns:
            统计信息或None
        """
        comparison = self.comparison_repository.get(comparison_id)
        if not comparison:
            return None
        
        # 获取各策略的统计信息
        strategy_stats = self.result_repository.get_all_strategies_stats(comparison_id)
        
        return EvaluationComparisonStatsResponse(
            comparison_id=comparison.id,
            comparison_name=comparison.comparison_name,
            test_task_name=comparison.test_task_name or "",
            total_pairs=comparison.total_pairs,
            strategy_stats=strategy_stats
        )
    
    def get_template_dimension_stats(self, comparison_id: str):
        """
        获取按模板分组的维度统计信息
        
        Args:
            comparison_id: 对比ID
            
        Returns:
            按模板分组的统计信息
        """
        from app.schemas.evaluation import (
            EvaluationTemplateDimensionStatsListResponse,
            EvaluationTemplateDimensionStatsResponse
        )
        
        comparison = self.comparison_repository.get(comparison_id)
        if not comparison:
            return None
        
        # 获取统计记录
        items, total = self.template_stats_repository.get_by_comparison_id(
            comparison_id=comparison_id,
            skip=0,
            limit=10000
        )
        
        return EvaluationTemplateDimensionStatsListResponse(
            total=total,
            items=[EvaluationTemplateDimensionStatsResponse.model_validate(item) for item in items]
        )
    
    def get_comprehensive_evaluation_stats(self, comparison_id: str):
        """
        获取综合评估统计信息
        
        包括：
        1. 整体统计信息（总用例数、总模板数、各策略整体统计）
        2. 各模板统计信息（用例数、各策略统计）
        3. 各模板下的用例详情（每个用例在各策略上的得分）
        
        Args:
            comparison_id: 对比ID
            
        Returns:
            综合评估统计信息
        """
        from app.schemas.evaluation import (
            ComprehensiveEvaluationStatsResponse,
            OverallStats,
            TemplateDetailStats,
            UseCaseStats,
            UseCaseResultItem,
            StrategyScoreStats
        )
        
        # 获取对比信息
        comparison = self.comparison_repository.get(comparison_id)
        if not comparison:
            return None
        
        # 获取预计算的模板维度统计数据（用于模板名称快照、以及各模板下各策略统计）
        template_stats_records, _ = self.template_stats_repository.get_by_comparison_id(
            comparison_id=comparison_id,
            skip=0,
            limit=10000
        )
        
        # 构建模板ID集合和模板快照信息字典
        template_ids = set()
        template_snapshot_dict = {}  # {template_id: prompt_template_name}
        for stats_record in template_stats_records:
            template_ids.add(stats_record.prompt_template_id)
            if stats_record.prompt_template_id not in template_snapshot_dict:
                template_snapshot_dict[stats_record.prompt_template_id] = stats_record.prompt_template_name
        
        # 获取所有评估结果
        results, _ = self.result_repository.get_by_comparison_id(
            comparison_id=comparison_id,
            skip=0,
            limit=10000
        )
        
        # 获取执行记录，用于获取LLM参数等信息（按需获取）
        execution_info = {}  # {execution_id: execution_object}
        
        # 建立用例ID到模板ID的映射：使用真实关联（PromptUseCase.template_id），避免“策略交集推断”导致错分/漏分
        use_case_to_template: Dict[str, str] = {}
        use_case_ids = {r.prompt_use_case_id for r in results if r.prompt_use_case_id}
        if use_case_ids:
            try:
                use_cases = self.use_case_repository.get_by_ids(list(use_case_ids))
                for uc in use_cases:
                    if uc and uc.id and uc.template_id:
                        use_case_to_template[uc.id] = uc.template_id
            except Exception as e:
                logger.warning(f"批量获取用例模板映射失败，将导致部分用例无法归类到模板: {str(e)}")
        
        # 按模板ID分组收集数据
        template_data = {}  # {template_id: {use_case_id: {strategy: result}}}
        all_strategies = set()
        
        for result in results:
            if not result.prompt_use_case_id:
                continue
            
            use_case_id = result.prompt_use_case_id
            strategy = result.evaluation_strategy
            
            # 获取模板ID（从映射中获取）
            template_id = use_case_to_template.get(use_case_id)
            if not template_id:
                continue
            
            # 记录策略
            all_strategies.add(strategy)
            
            # 组织数据结构
            if template_id not in template_data:
                template_data[template_id] = {}
            if use_case_id not in template_data[template_id]:
                template_data[template_id][use_case_id] = {}
            
            template_data[template_id][use_case_id][strategy] = {
                'result_id': result.id,
                'execution_id': result.execution_id,
                'score': result.score,
                'status': result.status,
                'error_message': result.error_message,
                'model_output': result.model_output,
                'reference_answer': result.reference_answer,
                'use_case_name': result.prompt_use_case_name  # 使用快照字段
            }
        
        # 计算整体统计
        overall_strategy_scores = {strategy: [] for strategy in all_strategies}
        for template_id, use_cases in template_data.items():
            for use_case_id, strategies in use_cases.items():
                for strategy, result_data in strategies.items():
                    if result_data['score'] is not None and result_data['status'] == 'success':
                        overall_strategy_scores[strategy].append(result_data['score'])
        
        # 只包含有数据的策略
        overall_strategies_stats = {}
        for strategy, scores in overall_strategy_scores.items():
            if scores:
                overall_strategies_stats[strategy] = StrategyScoreStats(
                    avg=round(sum(scores) / len(scores), 4),
                    min=round(min(scores), 4),
                    max=round(max(scores), 4),
                    count=len(scores)
                )
        
        # 统计总用例数（去重）
        all_use_case_ids = set()
        for template_id, use_cases in template_data.items():
            all_use_case_ids.update(use_cases.keys())
        total_use_cases = len(all_use_case_ids)
        total_templates = len(template_data)
        
        # 统计成功和失败的对数
        failed_pairs = self.result_repository.count_by_comparison_and_status(
            comparison_id, ResultStatus.FAILED.value
        )
        success_pairs = self.result_repository.count_by_comparison_and_status(
            comparison_id, ResultStatus.SUCCESS.value
        )
        
        overall_stats = OverallStats(
            total_use_cases=total_use_cases,
            total_templates=total_templates,
            total_pairs=comparison.total_pairs,
            completed_pairs=comparison.completed_pairs,
            failed_pairs=failed_pairs,
            success_pairs=success_pairs,
            test_task_name=comparison.test_task_name,
            evaluation_model_name=comparison.evaluation_model_name,
            strategies=overall_strategies_stats
        )
        
        # 构建模板统计数据的查找字典: {(template_id, strategy): stats_record}
        template_stats_dict = {}
        for stats_record in template_stats_records:
            key = (stats_record.prompt_template_id, stats_record.evaluation_strategy)
            template_stats_dict[key] = stats_record
        
        # 构建模板统计信息
        template_stats_list = []
        template_name_cache: Dict[str, Optional[str]] = dict(template_snapshot_dict)
        for template_id, use_cases in template_data.items():
            # 从预计算的统计数据中获取该模板下各策略的统计
            template_strategies_stats = {}
            for strategy in all_strategies:
                key = (template_id, strategy)
                if key in template_stats_dict:
                    stats_record = template_stats_dict[key]
                    template_strategies_stats[strategy] = StrategyScoreStats(
                        avg=round(stats_record.avg_score, 4) if stats_record.avg_score is not None else None,
                        min=round(stats_record.min_score, 4) if stats_record.min_score is not None else None,
                        max=round(stats_record.max_score, 4) if stats_record.max_score is not None else None,
                        count=stats_record.sample_count
                    )
            
            # 构建用例详情列表
            use_case_stats_list = []
            for use_case_id, strategies in use_cases.items():
                # 获取执行记录信息（从任意一个结果的execution_id，按需获取）
                execution = None
                execution_id = None
                for strategy_data in strategies.values():
                    if strategy_data.get('execution_id'):
                        execution_id = strategy_data['execution_id']
                        # 按需获取执行记录
                        if execution_id not in execution_info:
                            execution_info[execution_id] = self.execution_repository.get(execution_id)
                        execution = execution_info.get(execution_id)
                        break
                
                # 构建结果列表
                results_list = []
                for strategy in sorted(all_strategies):
                    if strategy in strategies:
                        result_data = strategies[strategy]
                        results_list.append(UseCaseResultItem(
                            strategy=strategy,
                            score=result_data['score'],
                            status=result_data['status'],
                            error_message=result_data['error_message'],
                            model_output=result_data['model_output'],
                            reference_answer=result_data['reference_answer']
                        ))
                
                # 准备LLM参数
                llm_params = None
                if execution and execution.llm_params_snapshot:
                    try:
                        llm_params = json.loads(execution.llm_params_snapshot)
                    except:
                        llm_params = None
                
                # 获取用例名称（从结果的快照字段中获取）
                use_case_name = None
                for strategy_data in strategies.values():
                    if strategy_data.get('use_case_name'):
                        use_case_name = strategy_data['use_case_name']
                        break
                
                use_case_stats_list.append(UseCaseStats(
                    use_case_id=use_case_id,
                    use_case_name=use_case_name or "",
                    rendered_system_prompt=execution.rendered_system_prompt if execution else None,
                    rendered_user_prompt=execution.rendered_user_prompt if execution else None,
                    llm_params=llm_params,
                    response_time=execution.model_response_duration if execution else None,
                    execution_error=execution.error_message if execution else None,
                    results=results_list
                ))
            
            # 按用例名称排序
            use_case_stats_list.sort(key=lambda x: x.use_case_name)
            
            # 获取模板名称：优先使用快照字段；缺失时按需查询一次并缓存
            template_name = template_name_cache.get(template_id)
            if template_name is None:
                try:
                    template = self.template_repository.get(template_id)
                    template_name = template.template_name if template else None
                except Exception:
                    template_name = None
                template_name_cache[template_id] = template_name
            system_prompt = None
            user_prompt = None
            function_category = None
            
            # 从第一个执行记录中获取LLM参数（因为同一模板的参数应该一致）
            llm_max_tokens = None
            llm_temperature = None
            llm_top_p = None
            llm_top_k = None
            
            # 遍历该模板下的用例，找到第一个有执行记录的
            for use_case_id in use_cases.keys():
                for strategy_data in use_cases[use_case_id].values():
                    execution_id = strategy_data.get('execution_id')
                    if execution_id:
                        execution = execution_info.get(execution_id)
                        if execution and execution.llm_params_snapshot:
                            try:
                                llm_params = json.loads(execution.llm_params_snapshot)
                                # 提取参数，注意可能是字符串类型需要转换
                                if 'max_tokens' in llm_params and llm_params['max_tokens']:
                                    llm_max_tokens = int(llm_params['max_tokens']) if isinstance(llm_params['max_tokens'], str) else llm_params['max_tokens']
                                if 'temperature' in llm_params and llm_params['temperature']:
                                    llm_temperature = float(llm_params['temperature']) if isinstance(llm_params['temperature'], str) else llm_params['temperature']
                                if 'top_p' in llm_params and llm_params['top_p']:
                                    llm_top_p = float(llm_params['top_p']) if isinstance(llm_params['top_p'], str) else llm_params['top_p']
                                if 'top_k' in llm_params and llm_params['top_k']:
                                    llm_top_k = int(llm_params['top_k']) if isinstance(llm_params['top_k'], str) else llm_params['top_k']
                                break
                            except (json.JSONDecodeError, ValueError, TypeError) as e:
                                logger.warning(f"解析LLM参数失败: {str(e)}")
                                pass
                    if llm_max_tokens is not None:  # 如果已经找到参数就跳出
                        break
                if llm_max_tokens is not None:
                    break
            
            template_stats_list.append(TemplateDetailStats(
                template_id=template_id,
                template_name=template_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                function_category=function_category,
                max_tokens=llm_max_tokens,
                top_p=llm_top_p,
                top_k=llm_top_k,
                temperature=llm_temperature,
                use_case_count=len(use_cases),
                strategies=template_strategies_stats,
                use_cases=use_case_stats_list
            ))
        
        # 按模板名称排序
        template_stats_list.sort(key=lambda x: x.template_name or "")
        
        return ComprehensiveEvaluationStatsResponse(
            comparison_id=comparison.id,
            comparison_name=comparison.comparison_name,
            status=comparison.status,
            overall_stats=overall_stats,
            template_stats=template_stats_list
        )
