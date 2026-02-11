"""
Test Task service
"""
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, BackgroundTasks
import httpx
import logging

logger = logging.getLogger(__name__)

from app.repositories.test_task import TestTaskRepository, TestExecutionRepository
from app.repositories.prompt_use_case import PromptUseCaseRepository
from app.repositories.ai_model import AIModelRepository
from app.repositories.system_config import SystemConfigRepository
from app.repositories.prompt_template_version import PromptTemplateVersionRepository
from app.schemas.test_task import (
    TestTaskCreate,
    TestTaskUpdate,
    TestTaskResponse,
    TestTaskListResponse,
    TestExecutionResponse,
    TestTaskStatusResponse
)
from app.models.test_task import TaskStatus, ExecutionStatus


class TestTaskService:
    """
    测试任务业务逻辑
    """
    
    def __init__(self, db: Session):
        self.task_repository = TestTaskRepository(db)
        self.execution_repository = TestExecutionRepository(db)
        self.use_case_repository = PromptUseCaseRepository(db)
        self.ai_model_repository = AIModelRepository(db)
        self.system_config_repository = SystemConfigRepository(db)
        self.version_repository = PromptTemplateVersionRepository(db)
        self.db = db
    
    def _resolve_param_value(self, param_value: Optional[str], config_code: str) -> Optional[str]:
        """
        解析参数值，处理 __USE_SYSTEM_DEFAULT__ 和 __NONE__ 特殊值
        
        Args:
            param_value: 参数值
            config_code: 系统配置编码
            
        Returns:
            解析后的参数值，如果是 __NONE__ 返回 None
        """
        if not param_value:
            # 如果没有值，查询系统默认值
            config = self.system_config_repository.get_by_code(config_code)
            return config.config_content if config else None
        
        if param_value == "__NONE__":
            return None
        
        if param_value == "__USE_SYSTEM_DEFAULT__":
            # 查询系统默认值
            config = self.system_config_repository.get_by_code(config_code)
            return config.config_content if config else None
        
        # 返回具体的值
        return param_value
    
    def create_test_task(self, task_in: TestTaskCreate) -> TestTaskResponse:
        """
        创建测试任务
        
        Args:
            task_in: 测试任务创建数据
            
        Returns:
            创建的测试任务
            
        Raises:
            HTTPException: 如果AI模型不存在或用例不存在
        """
        # 验证AI模型是否存在
        ai_model = self.ai_model_repository.get(task_in.ai_model_id)
        if not ai_model:
            raise HTTPException(
                status_code=404,
                detail=f"找不到 ID 为 '{task_in.ai_model_id}' 的 AI 模型"
            )
        
        # 验证所有用例是否存在
        use_cases = []
        for use_case_id in task_in.use_case_ids:
            use_case = self.use_case_repository.get(use_case_id)
            if not use_case:
                raise HTTPException(
                    status_code=404,
                    detail=f"找不到 ID 为 '{use_case_id}' 的用例"
                )
            use_cases.append(use_case)
        
        # 创建任务
        task_dict = {
            "task_name": task_in.task_name,
            "task_description": task_in.task_description,
            "status": TaskStatus.PENDING.value,
            "total_cases": len(task_in.use_case_ids),
            "completed_cases": 0,
            "success_cases": 0,
            "failed_cases": 0,
            "ai_model_id": task_in.ai_model_id,
            "ai_model_name": ai_model.model_name,  # 保存AI模型名称快照
            "remarks": task_in.remarks,
            "created_by": task_in.created_by,
            "updated_by": task_in.created_by
        }
        
        task = self.task_repository.create(task_dict)
        
        # 为每个用例创建执行记录
        for use_case in use_cases:
            # 处理系统提示词
            system_prompt = use_case.rendered_system_prompt
            if use_case.template and use_case.template.system_prompt:
                template_system_prompt = use_case.template.system_prompt
                
                # 先判断是否为特殊值
                if template_system_prompt == "__NONE__":
                    system_prompt = ""
                elif template_system_prompt == "__USE_SYSTEM_DEFAULT__":
                    # 使用系统默认值
                    resolved_system_prompt = self._resolve_param_value(
                        template_system_prompt,
                        "DEFAULT_SYSTEM_PROMPT"
                    )
                    if resolved_system_prompt is not None:
                        # 系统默认值也需要进行变量替换
                        from app.services.prompt_use_case import PromptUseCaseService
                        system_prompt = PromptUseCaseService.render_template(
                            resolved_system_prompt,
                            use_case.template_variables,
                            validate=False
                        )
                    else:
                        system_prompt = use_case.rendered_system_prompt
                else:
                    # 具体的值，需要进行变量替换
                    from app.services.prompt_use_case import PromptUseCaseService
                    system_prompt = PromptUseCaseService.render_template(
                        template_system_prompt,
                        use_case.template_variables,
                        validate=False
                    )
            
            # 获取模板的LLM参数，处理特殊值
            llm_params = {}
            if use_case.template:
                # 处理 max_tokens
                max_tokens = self._resolve_param_value(
                    use_case.template.max_tokens,
                    "DEFAULT_MAX_TOKENS"
                )
                llm_params['max_tokens'] = max_tokens
                
                # 处理 temperature
                temperature = self._resolve_param_value(
                    use_case.template.temperature,
                    "DEFAULT_TEMPERATURE"
                )
                llm_params['temperature'] = temperature
                
                # 处理 top_p
                top_p = self._resolve_param_value(
                    use_case.template.top_p,
                    "DEFAULT_TOP_P"
                )
                llm_params['top_p'] = top_p
                
                # 处理 top_k
                top_k = self._resolve_param_value(
                    use_case.template.top_k,
                    "DEFAULT_TOP_K"
                )
                llm_params['top_k'] = top_k
            
            # 获取评估策略快照（来自提示词模板）
            evaluation_strategies_snapshot = None
            if use_case.template and use_case.template.evaluation_strategies:
                evaluation_strategies_snapshot = json.dumps(
                    use_case.template.evaluation_strategies,
                    ensure_ascii=False
                )
            
            # 获取模板版本溯源信息
            template_version = None
            template_version_id = None
            if use_case.template:
                template_version = getattr(use_case.template, 'current_version', None)
                if template_version:
                    version_obj = self.version_repository.get_by_template_id_and_version(
                        use_case.template.id, template_version
                    )
                    if version_obj:
                        template_version_id = version_obj.id

            execution_dict = {
                "test_task_id": task.id,
                "status": ExecutionStatus.PENDING.value,
                "prompt_use_case_id": use_case.id,
                "prompt_use_case_name": use_case.use_case_name,
                "llm_params_snapshot": json.dumps(llm_params, ensure_ascii=False),
                "rendered_system_prompt": system_prompt,
                "rendered_user_prompt": use_case.rendered_user_prompt,
                "ai_model_id": task_in.ai_model_id,
                "ai_model_name": ai_model.model_name,
                "reference_answer": use_case.reference_answer,  # 参考答案来自提示词用例
                "evaluation_strategies_snapshot": evaluation_strategies_snapshot,  # 评估策略来自提示词模板
                "template_version": template_version,  # 提示词模板版本号
                "template_version_id": template_version_id,  # 提示词模板版本ID
                "created_by": task_in.created_by,
                "updated_by": task_in.created_by
            }
            self.execution_repository.create(execution_dict)
        
        self.db.commit()
        
        return TestTaskResponse.model_validate(task)
    
    def get_test_task(self, task_id: str) -> Optional[TestTaskResponse]:
        """
        获取测试任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            测试任务或None
        """
        task = self.task_repository.get(task_id)
        if task:
            return TestTaskResponse.model_validate(task)
        return None
    
    # 注意：get_test_task_detail 方法已移除
    # 请使用 get_test_task 获取任务信息，然后通过 TestExecutionService 分页查询执行记录
    
    def get_test_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        ai_model_id: Optional[str] = None
    ) -> TestTaskListResponse:
        """
        获取测试任务列表
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数上限
            keyword: 关键词搜索
            status: 状态过滤
            ai_model_id: AI模型ID过滤
            
        Returns:
            测试任务列表
        """
        items, total = self.task_repository.search(
            skip=skip,
            limit=limit,
            keyword=keyword,
            status=status,
            ai_model_id=ai_model_id
        )
        
        return TestTaskListResponse(
            total=total,
            items=[TestTaskResponse.model_validate(t) for t in items]
        )
    
    def update_test_task(
        self,
        task_id: str,
        task_in: TestTaskUpdate
    ) -> Optional[TestTaskResponse]:
        """
        更新测试任务
        
        Args:
            task_id: 任务ID
            task_in: 更新数据
            
        Returns:
            更新后的任务或None
        """
        task = self.task_repository.get(task_id)
        if not task:
            return None
        
        # 只允许更新基本信息，不允许修改状态和统计信息
        update_dict = task_in.model_dump(exclude_unset=True, exclude={'status'})
        
        updated_task = self.task_repository.update(task_id, update_dict)
        if updated_task:
            self.db.commit()
            return TestTaskResponse.model_validate(updated_task)
        return None
    
    def delete_test_task(self, task_id: str) -> bool:
        """
        删除测试任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        success = self.task_repository.delete(task_id)
        if success:
            self.db.commit()
        return success
    
    def get_task_status(self, task_id: str) -> Optional[TestTaskStatusResponse]:
        """
        获取任务执行状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态或None
        """
        task = self.task_repository.get(task_id)
        if not task:
            return None
        
        progress_percentage = 0.0
        if task.total_cases > 0:
            progress_percentage = (task.completed_cases / task.total_cases) * 100
        
        return TestTaskStatusResponse(
            task_id=task.id,
            status=task.status,
            total_cases=task.total_cases,
            completed_cases=task.completed_cases,
            success_cases=task.success_cases,
            failed_cases=task.failed_cases,
            progress_percentage=round(progress_percentage, 2)
        )
    
    def start_task_execution(self, task_id: str, background_tasks: BackgroundTasks) -> TestTaskResponse:
        """
        启动任务执行
        
        Args:
            task_id: 任务ID
            background_tasks: FastAPI 后台任务
            
        Returns:
            更新后的任务
            
        Raises:
            HTTPException: 如果任务不存在或状态不允许启动
        """
        task = self.task_repository.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="找不到任务")
        
        # 只有待执行和部分完成的任务可以启动
        if task.status not in [TaskStatus.PENDING.value, TaskStatus.PARTIAL.value]:
            raise HTTPException(
                status_code=400,
                detail=f"无法启动状态为 '{task.status}' 的任务"
            )
        
        # 更新任务状态为执行中
        task.status = TaskStatus.RUNNING.value
        self.db.commit()
        
        # 在后台执行任务
        background_tasks.add_task(self._execute_task_sync, task_id)
        
        return TestTaskResponse.model_validate(task)
    
    def cancel_task_execution(self, task_id: str) -> TestTaskResponse:
        """
        取消任务执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            更新后的任务
            
        Raises:
            HTTPException: 如果任务不存在或状态不允许取消
        """
        task = self.task_repository.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="找不到任务")
        
        # 只有执行中的任务可以取消
        if task.status != TaskStatus.RUNNING.value:
            raise HTTPException(
                status_code=400,
                detail=f"无法取消状态为 '{task.status}' 的任务"
            )
        
        # 更新任务状态为已取消
        task.status = TaskStatus.CANCELLED.value
        self.db.commit()
        
        return TestTaskResponse.model_validate(task)
    
    def restart_test_task(self, task_id: str, background_tasks: BackgroundTasks, force: bool = False) -> TestTaskResponse:
        """
        重启测试任务（针对运行中或部分完成的任务）
        
        Args:
            task_id: 任务ID
            background_tasks: FastAPI 后台任务
            force: 是否强制重启（忽略10分钟限制）
            
        Returns:
            更新后的任务
            
        Raises:
            HTTPException: 如果任务不存在或不满足重启条件
        """
        task = self.task_repository.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="找不到测试任务")
        
        # 检查状态：pending、partial、cancelled、running 都可以重启
        if task.status not in [TaskStatus.PENDING.value, TaskStatus.PARTIAL.value, TaskStatus.CANCELLED.value, TaskStatus.RUNNING.value]:
            raise HTTPException(
                status_code=400,
                detail=f"无法重启状态为 '{task.status}' 的测试任务（只能重启 pending、partial、cancelled 或 running 状态的任务）"
            )
        
        # 如果是 running 状态，检查是否满足重启条件（10分钟未更新）
        if task.status == TaskStatus.RUNNING.value and not force:
            can_restart, message = self._check_can_restart_task(task)
            if not can_restart:
                raise HTTPException(status_code=400, detail=message)
        
        # 更新任务状态为执行中
        task.status = TaskStatus.RUNNING.value
        task.updated_at = datetime.utcnow()
        self.db.commit()
        
        # 在后台执行任务
        background_tasks.add_task(self._execute_task_sync, task_id)
        
        return TestTaskResponse.model_validate(task)
    
    def _check_can_restart_task(self, task) -> Tuple[bool, str]:
        """
        检查是否可以重启运行中的任务
        
        Args:
            task: 任务对象
            
        Returns:
            (是否可以重启, 消息)
        """
        if task.status != TaskStatus.RUNNING.value:
            return True, "非运行中状态，可以重启"
        
        # 检查最后更新时间
        now = datetime.utcnow()
        time_since_update = now - task.updated_at
        
        # 10分钟 = 600秒
        if time_since_update.total_seconds() < 600:
            remaining_seconds = 600 - time_since_update.total_seconds()
            remaining_minutes = int(remaining_seconds / 60)
            return False, f"任务运行中且最近有更新，需等待 {remaining_minutes} 分钟后才能重启"
        
        return True, "任务超过10分钟未更新，可以重启"
    
    def check_and_mark_timeout_tasks(self) -> List[str]:
        """
        检查并标记超时的测试任务（30分钟未更新的运行中任务）
        
        Returns:
            被标记为部分完成的任务ID列表
        """
        marked_ids = []
        
        try:
            # 查询所有运行中的任务
            running_tasks, _ = self.task_repository.search(
                skip=0,
                limit=10000,
                status=TaskStatus.RUNNING.value
            )
            
            now = datetime.utcnow()
            timeout_threshold = timedelta(minutes=30)
            
            for task in running_tasks:
                time_since_update = now - task.updated_at
                
                # 检查是否超过30分钟
                if time_since_update >= timeout_threshold:
                    logger.warning(
                        f"测试任务 {task.id} 超过30分钟未更新，将状态标记为部分完成。"
                        f"最后更新时间: {task.updated_at}, 已过时长: {time_since_update}"
                    )
                    
                    # 标记为部分完成而非失败，因为部分用例可能已经成功
                    task.status = TaskStatus.PARTIAL.value
                    marked_ids.append(task.id)
            
            if marked_ids:
                self.db.commit()
                logger.info(f"已标记 {len(marked_ids)} 个超时测试任务为部分完成: {marked_ids}")
            
        except Exception as e:
            logger.error(f"检查超时测试任务时出错: {str(e)}")
            self.db.rollback()
        
        return marked_ids
    
    def _execute_task_sync(self, task_id: str):
        """
        执行任务（同步包装方法）
        
        Args:
            task_id: 任务ID
        """
        # 创建新的事件循环并运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._execute_task(task_id))
        finally:
            loop.close()
    
    async def _execute_task(self, task_id: str):
        """
        执行任务（异步方法）
        
        Args:
            task_id: 任务ID
        """
        try:
            # 获取任务信息
            task = self.task_repository.get(task_id)
            if not task:
                return
            
            # 获取AI模型信息
            ai_model = self.ai_model_repository.get(task.ai_model_id)
            if not ai_model:
                # 任务失败
                task.status = TaskStatus.PARTIAL.value
                self.db.commit()
                return
            
            # 获取待执行的记录
            pending_executions = self.execution_repository.get_pending_executions(task_id, limit=10000)
            
            # 逐个执行
            for execution in pending_executions:
                # 检查任务是否被取消
                self.db.refresh(task)
                if task.status == TaskStatus.CANCELLED.value:
                    break
                
                # 执行单个用例
                await self._execute_single_case(execution, ai_model)
                
                # 更新任务统计
                self._update_task_statistics(task_id)
            
            # 更新最终状态
            self._finalize_task_status(task_id)
            
        except Exception as e:
            # 任务执行出错
            task = self.task_repository.get(task_id)
            if task:
                task.status = TaskStatus.PARTIAL.value
                self.db.commit()
    
    async def _execute_single_case(self, execution: any, ai_model: any):
        """
        执行单个测试用例
        
        Args:
            execution: 执行记录
            ai_model: AI模型
        """
        start_time = datetime.utcnow()
        execution.start_time = start_time
        execution.status = ExecutionStatus.PENDING.value
        self.db.commit()
        
        try:
            # 构建请求数据
            request_data = {
                "model": ai_model.model_name,
                "messages": []
            }
            
            # 添加系统提示词
            if execution.rendered_system_prompt:
                request_data["messages"].append({
                    "role": "system",
                    "content": execution.rendered_system_prompt
                })
            
            # 添加用户提示词
            if execution.rendered_user_prompt:
                request_data["messages"].append({
                    "role": "user",
                    "content": execution.rendered_user_prompt
                })
            
            # 添加 LLM 参数（从快照中获取）
            if execution.llm_params_snapshot:
                try:
                    llm_params = json.loads(execution.llm_params_snapshot)
                    if 'max_tokens' in llm_params and llm_params['max_tokens']:
                        request_data['max_tokens'] = int(llm_params['max_tokens'])
                    if 'temperature' in llm_params and llm_params['temperature']:
                        request_data['temperature'] = float(llm_params['temperature'])
                    if 'top_p' in llm_params and llm_params['top_p']:
                        request_data['top_p'] = float(llm_params['top_p'])
                    if 'top_k' in llm_params and llm_params['top_k']:
                        request_data['top_k'] = int(llm_params['top_k'])
                except (json.JSONDecodeError, ValueError):
                    pass  # 如果解析失败，使用默认参数
            
            # 调用AI模型API
            async with httpx.AsyncClient(timeout=300.0) as client:
                # 构建请求头
                headers = {"Content-Type": "application/json"}
                if ai_model.api_key:
                    headers["Authorization"] = f"Bearer {ai_model.api_key}"
                
                # 记录模型调用开始时间
                model_start_time = datetime.utcnow()
                
                response = await client.post(
                    f"{ai_model.api_endpoint}/v1/chat/completions",
                    json=request_data,
                    headers=headers
                )
                
                # 记录模型响应结束时间
                model_end_time = datetime.utcnow()
                execution.model_response_duration = (model_end_time - model_start_time).total_seconds()
                
                response.raise_for_status()
                result = response.json()
                
                # 提取输出结果
                output = self._extract_output(result)
                
                # 更新执行记录
                execution.status = ExecutionStatus.SUCCESS.value
                execution.output_result = output
                execution.error_message = None
                
        except Exception as e:
            # 执行失败
            execution.status = ExecutionStatus.FAILED.value
            execution.error_message = str(e)
        
        finally:
            # 更新执行时间
            end_time = datetime.utcnow()
            execution.end_time = end_time
            execution.execution_duration = (end_time - start_time).total_seconds()
            self.db.commit()
    
    def _extract_output(self, response_data: dict) -> str:
        """
        从API响应中提取输出结果
        
        Args:
            response_data: API响应数据
            
        Returns:
            输出结果文本
        """
        # 尝试不同的响应格式
        if "choices" in response_data and len(response_data["choices"]) > 0:
            choice = response_data["choices"][0]
            if "message" in choice:
                return choice["message"].get("content", "")
            elif "text" in choice:
                return choice["text"]
        
        # 如果无法提取，返回整个响应的JSON字符串
        return json.dumps(response_data, ensure_ascii=False)
    
    def _update_task_statistics(self, task_id: str):
        """
        更新任务统计信息
        
        Args:
            task_id: 任务ID
        """
        task = self.task_repository.get(task_id)
        if not task:
            return
        
        # 统计各状态的执行记录数
        completed_count = self.execution_repository.count_by_task_id_and_status(
            task_id, ExecutionStatus.SUCCESS.value
        ) + self.execution_repository.count_by_task_id_and_status(
            task_id, ExecutionStatus.FAILED.value
        )
        success_count = self.execution_repository.count_by_task_id_and_status(
            task_id, ExecutionStatus.SUCCESS.value
        )
        failed_count = self.execution_repository.count_by_task_id_and_status(
            task_id, ExecutionStatus.FAILED.value
        )
        
        # 更新统计信息
        task.completed_cases = completed_count
        task.success_cases = success_count
        task.failed_cases = failed_count
        
        self.db.commit()
    
    def _finalize_task_status(self, task_id: str):
        """
        完成任务，更新最终状态
        
        Args:
            task_id: 任务ID
        """
        task = self.task_repository.get(task_id)
        if not task:
            return
        
        # 如果已被取消，不改变状态
        if task.status == TaskStatus.CANCELLED.value:
            return
        
        # 根据完成情况设置状态
        if task.completed_cases == task.total_cases:
            task.status = TaskStatus.COMPLETED.value
        elif task.completed_cases > 0:
            task.status = TaskStatus.PARTIAL.value
        else:
            task.status = TaskStatus.PENDING.value
        
        self.db.commit()
    
    # ============= 执行记录相关方法 =============
    # 注意：执行记录查询方法已迁移到 TestExecutionService
    # 请使用 app/services/test_execution.py 中的 TestExecutionService 进行执行记录查询

