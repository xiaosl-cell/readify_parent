"""
Evaluation Comparison repositories
"""
from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.repositories.base import BaseRepository
from app.models.evaluation import EvaluationComparison, EvaluationResult, EvaluationTemplateDimensionStats


class EvaluationComparisonRepository(BaseRepository[EvaluationComparison]):
    """
    评估对比仓储类
    """
    
    def __init__(self, db: Session):
        super().__init__(EvaluationComparison, db)
    
    def search(
        self,
        skip: int = 0,
        limit: int = 100,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        test_task_id: Optional[str] = None
    ) -> Tuple[List[EvaluationComparison], int]:
        """
        搜索评估对比记录
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数上限
            keyword: 关键词搜索（对比名称）
            status: 状态过滤
            test_task_id: 测试任务ID
            
        Returns:
            (记录列表, 总数)
        """
        query = self.db.query(self.model)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    self.model.comparison_name.like(f"%{keyword}%"),
                    self.model.comparison_description.like(f"%{keyword}%")
                )
            )
        
        # 状态过滤
        if status:
            query = query.filter(self.model.status == status)
        
        # 测试任务过滤
        if test_task_id:
            query = query.filter(self.model.test_task_id == test_task_id)
        
        # 统计总数
        total = query.count()
        
        # 分页查询
        items = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()
        
        return items, total
    
    def count_by_status(self, status: str) -> int:
        """
        统计指定状态的对比记录数
        
        Args:
            status: 状态
            
        Returns:
            记录数
        """
        return self.db.query(func.count(self.model.id)).filter(
            self.model.status == status
        ).scalar()


class EvaluationResultRepository(BaseRepository[EvaluationResult]):
    """
    评估结果明细仓储类
    """
    
    def __init__(self, db: Session):
        super().__init__(EvaluationResult, db)
    
    def get_by_comparison_id(
        self,
        comparison_id: str,
        skip: int = 0,
        limit: int = 100,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        status: Optional[str] = None,
        evaluation_strategy: Optional[str] = None
    ) -> Tuple[List[EvaluationResult], int]:
        """
        根据对比ID获取评估结果列表
        
        Args:
            comparison_id: 对比ID
            skip: 跳过记录数
            limit: 返回记录数上限
            min_score: 最小分数过滤
            max_score: 最大分数过滤
            status: 状态过滤
            evaluation_strategy: 评估策略过滤
            
        Returns:
            (记录列表, 总数)
        """
        query = self.db.query(self.model).filter(
            self.model.comparison_id == comparison_id
        )
        
        # 分数范围过滤
        if min_score is not None:
            query = query.filter(self.model.score >= min_score)
        if max_score is not None:
            query = query.filter(self.model.score <= max_score)
        
        # 状态过滤
        if status:
            query = query.filter(self.model.status == status)
        
        # 评估策略过滤
        if evaluation_strategy:
            query = query.filter(self.model.evaluation_strategy == evaluation_strategy)
        
        # 统计总数
        total = query.count()
        
        # 分页查询，按分数降序排列
        items = query.order_by(self.model.score.desc()).offset(skip).limit(limit).all()
        
        return items, total
    
    def get_pending_results(self, comparison_id: str, limit: int = 1000) -> List[EvaluationResult]:
        """
        获取待计算的评估结果
        
        Args:
            comparison_id: 对比ID
            limit: 返回记录数上限
            
        Returns:
            待计算的记录列表
        """
        return self.db.query(self.model).filter(
            and_(
                self.model.comparison_id == comparison_id,
                self.model.status == "pending"
            )
        ).limit(limit).all()
    
    def count_by_comparison_and_status(self, comparison_id: str, status: str) -> int:
        """
        统计指定对比和状态的结果数
        
        Args:
            comparison_id: 对比ID
            status: 状态
            
        Returns:
            记录数
        """
        return self.db.query(func.count(self.model.id)).filter(
            and_(
                self.model.comparison_id == comparison_id,
                self.model.status == status
            )
        ).scalar()
    
    def get_score_stats_by_strategy(self, comparison_id: str, evaluation_strategy: str) -> dict:
        """
        获取指定策略的分数统计信息
        
        Args:
            comparison_id: 对比ID
            evaluation_strategy: 评估策略
            
        Returns:
            统计信息字典
        """
        results = self.db.query(
            func.avg(self.model.score).label('avg'),
            func.min(self.model.score).label('min'),
            func.max(self.model.score).label('max'),
            func.count(self.model.id).label('count')
        ).filter(
            and_(
                self.model.comparison_id == comparison_id,
                self.model.evaluation_strategy == evaluation_strategy,
                self.model.status == "success",
                self.model.score.isnot(None)
            )
        ).first()
        
        return {
            'avg': float(results.avg) if results.avg else None,
            'min': float(results.min) if results.min else None,
            'max': float(results.max) if results.max else None,
            'count': results.count or 0
        }
    
    def get_all_strategies_stats(self, comparison_id: str) -> dict:
        """
        获取所有策略的统计信息
        
        Args:
            comparison_id: 对比ID
            
        Returns:
            各策略统计信息字典
        """
        # 获取该对比下的所有策略
        strategies = self.db.query(self.model.evaluation_strategy).filter(
            self.model.comparison_id == comparison_id
        ).distinct().all()
        
        stats = {}
        for (strategy,) in strategies:
            stats[strategy] = self.get_score_stats_by_strategy(comparison_id, strategy)
        
        return stats


class EvaluationTemplateDimensionStatsRepository(BaseRepository[EvaluationTemplateDimensionStats]):
    """
    评估模板维度统计仓储类
    """
    
    def __init__(self, db: Session):
        super().__init__(EvaluationTemplateDimensionStats, db)
    
    def get_by_comparison_id(
        self,
        comparison_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[EvaluationTemplateDimensionStats], int]:
        """
        根据对比ID获取统计记录列表
        
        Args:
            comparison_id: 对比ID
            skip: 跳过记录数
            limit: 返回记录数上限
            
        Returns:
            (记录列表, 总数)
        """
        query = self.db.query(self.model).filter(
            self.model.comparison_id == comparison_id
        )
        
        # 统计总数
        total = query.count()
        
        # 分页查询，按模板ID和策略排序
        items = query.order_by(
            self.model.prompt_template_id,
            self.model.evaluation_strategy
        ).offset(skip).limit(limit).all()
        
        return items, total
    
    def delete_by_comparison_id(self, comparison_id: str) -> int:
        """
        删除指定对比ID的所有统计记录
        
        Args:
            comparison_id: 对比ID
            
        Returns:
            删除的记录数
        """
        deleted = self.db.query(self.model).filter(
            self.model.comparison_id == comparison_id
        ).delete(synchronize_session=False)
        
        return deleted
    
    def get_by_template_and_strategy(
        self,
        comparison_id: str,
        prompt_template_id: str,
        evaluation_strategy: str
    ) -> Optional[EvaluationTemplateDimensionStats]:
        """
        根据对比ID、模板ID和策略获取统计记录
        
        Args:
            comparison_id: 对比ID
            prompt_template_id: 提示词模板ID
            evaluation_strategy: 评估策略
            
        Returns:
            统计记录或None
        """
        return self.db.query(self.model).filter(
            and_(
                self.model.comparison_id == comparison_id,
                self.model.prompt_template_id == prompt_template_id,
                self.model.evaluation_strategy == evaluation_strategy
            )
        ).first()
    
    def get_stats_grouped_by_template(
        self,
        comparison_id: str
    ) -> Dict[str, List[Dict]]:
        """
        获取按模板分组的统计信息
        
        Args:
            comparison_id: 对比ID
            
        Returns:
            按模板ID分组的统计信息字典
        """
        stats_list = self.db.query(self.model).filter(
            self.model.comparison_id == comparison_id
        ).order_by(
            self.model.prompt_template_id,
            self.model.evaluation_strategy
        ).all()
        
        # 按模板ID分组
        grouped = {}
        for stat in stats_list:
            if stat.prompt_template_id not in grouped:
                grouped[stat.prompt_template_id] = []
            
            grouped[stat.prompt_template_id].append({
                'template_id': stat.prompt_template_id,
                'template_name': stat.prompt_template_name,
                'strategy': stat.evaluation_strategy,
                'avg_score': stat.avg_score,
                'min_score': stat.min_score,
                'max_score': stat.max_score,
                'sample_count': stat.sample_count
            })
        
        return grouped

