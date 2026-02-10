"""
后台定时任务调度器
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.core.database import SessionLocal
from app.services.evaluation import EvaluationService
from app.services.test_task import TestTaskService

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """
    后台定时任务调度器
    """
    
    def __init__(self):
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已经在运行中")
            return
        
        self.running = True
        logger.info("后台调度器启动")
        
        # 创建定时任务
        self.task = asyncio.create_task(self._run_scheduler())
    
    async def stop(self):
        """停止调度器"""
        if not self.running:
            return
        
        self.running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("后台调度器已停止")
    
    async def _run_scheduler(self):
        """运行调度器主循环"""
        # 等待5秒后开始第一次检查（避免启动时立即执行）
        await asyncio.sleep(5)
        
        while self.running:
            try:
                await self._check_timeout_evaluations()
                await self._check_timeout_test_tasks()
            except Exception as e:
                logger.error(f"执行定时任务时出错: {str(e)}", exc_info=True)
            
            # 每5分钟检查一次
            await asyncio.sleep(300)
    
    async def _check_timeout_evaluations(self):
        """检查超时的评估任务"""
        db = SessionLocal()
        try:
            service = EvaluationService(db)
            marked_ids = service.check_and_mark_timeout_comparisons()
            
            if marked_ids:
                logger.info(
                    f"[定时任务] 检查评估超时完成，标记了 {len(marked_ids)} 个超时评估对比为失败: {marked_ids}"
                )
            else:
                logger.debug(f"[定时任务] 检查评估超时完成，没有发现超时任务 ({datetime.utcnow().isoformat()})")
        except Exception as e:
            logger.error(f"检查评估超时任务失败: {str(e)}", exc_info=True)
        finally:
            db.close()
    
    async def _check_timeout_test_tasks(self):
        """检查超时的测试任务"""
        db = SessionLocal()
        try:
            service = TestTaskService(db)
            marked_ids = service.check_and_mark_timeout_tasks()
            
            if marked_ids:
                logger.info(
                    f"[定时任务] 检查测试任务超时完成，标记了 {len(marked_ids)} 个超时测试任务为部分完成: {marked_ids}"
                )
            else:
                logger.debug(f"[定时任务] 检查测试任务超时完成，没有发现超时任务 ({datetime.utcnow().isoformat()})")
        except Exception as e:
            logger.error(f"检查测试任务超时失败: {str(e)}", exc_info=True)
        finally:
            db.close()


# 全局调度器实例
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """获取调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


async def start_scheduler():
    """启动全局调度器"""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler():
    """停止全局调度器"""
    scheduler = get_scheduler()
    await scheduler.stop()

