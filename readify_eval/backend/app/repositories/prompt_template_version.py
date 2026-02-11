"""
Prompt Template Version repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.prompt_template_version import PromptTemplateVersion
from app.repositories.base import BaseRepository


class PromptTemplateVersionRepository(BaseRepository[PromptTemplateVersion]):
    """
    Repository for Prompt Template Version
    """

    def __init__(self, db: Session):
        super().__init__(PromptTemplateVersion, db)

    def get_by_template_id(
        self,
        template_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[PromptTemplateVersion]:
        """
        获取指定模板的所有版本，按版本号降序排列

        Args:
            template_id: 模板ID
            skip: 跳过记录数
            limit: 返回记录数上限

        Returns:
            版本列表
        """
        return (
            self.db.query(self.model)
            .filter(self.model.template_id == template_id)
            .order_by(self.model.version.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_template_id(self, template_id: str) -> int:
        """
        获取指定模板的版本总数

        Args:
            template_id: 模板ID

        Returns:
            版本总数
        """
        from sqlalchemy import func
        return (
            self.db.query(func.count(self.model.id))
            .filter(self.model.template_id == template_id)
            .scalar() or 0
        )

    def get_by_template_id_and_version(
        self,
        template_id: str,
        version: int
    ) -> Optional[PromptTemplateVersion]:
        """
        获取指定模板的指定版本

        Args:
            template_id: 模板ID
            version: 版本号

        Returns:
            版本实例或None
        """
        return (
            self.db.query(self.model)
            .filter(
                self.model.template_id == template_id,
                self.model.version == version
            )
            .first()
        )

    def get_latest_version(self, template_id: str) -> Optional[PromptTemplateVersion]:
        """
        获取指定模板的最新版本

        Args:
            template_id: 模板ID

        Returns:
            最新版本实例或None
        """
        return (
            self.db.query(self.model)
            .filter(self.model.template_id == template_id)
            .order_by(self.model.version.desc())
            .first()
        )

    def delete_by_template_id(self, template_id: str) -> int:
        """
        删除指定模板的所有版本

        Args:
            template_id: 模板ID

        Returns:
            删除的记录数
        """
        count = (
            self.db.query(self.model)
            .filter(self.model.template_id == template_id)
            .delete()
        )
        self.db.flush()
        return count
