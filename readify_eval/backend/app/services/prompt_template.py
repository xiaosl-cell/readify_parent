"""
Prompt Template service
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.prompt_template import PromptTemplateRepository
from app.repositories.prompt_template_version import PromptTemplateVersionRepository
from app.repositories.prompt_use_case import PromptUseCaseRepository
from app.schemas.prompt_template import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptTemplateListResponse
)
from app.schemas.prompt_template_version import (
    PromptTemplateVersionResponse,
    PromptTemplateVersionListResponse,
    PromptTemplateVersionDiff,
    PromptTemplateVersionDiffResponse,
)

# 版本快照包含的字段
VERSION_SNAPSHOT_FIELDS = [
    "template_code", "template_name", "system_prompt", "user_prompt", "function_category",
    "remarks", "max_tokens", "top_p", "top_k", "temperature",
    "evaluation_strategies", "owner", "qc_number", "prompt_source",
]

# 字段中文名映射（用于 diff 显示）
FIELD_LABELS = {
    "template_code": "模板编码",
    "template_name": "模板名称",
    "system_prompt": "系统提示词",
    "user_prompt": "用户提示词",
    "function_category": "所属功能",
    "remarks": "备注",
    "max_tokens": "最大Token数",
    "top_p": "Top P",
    "top_k": "Top K",
    "temperature": "温度",
    "evaluation_strategies": "评估策略",
    "owner": "负责人",
    "qc_number": "QC号",
    "prompt_source": "提示词来源",
}


class PromptTemplateService:
    """
    Business logic for Prompt Template operations
    """

    def __init__(self, db: Session):
        self.repository = PromptTemplateRepository(db)
        self.version_repository = PromptTemplateVersionRepository(db)
        self.use_case_repository = PromptUseCaseRepository(db)
        self.db = db

    def _create_version_snapshot(self, template, version: int, change_log: Optional[str] = None):
        """
        为模板创建一个版本快照

        Args:
            template: 模板 ORM 对象
            version: 版本号
            change_log: 变更说明
        """
        version_dict = {
            "template_id": template.id,
            "version": version,
            "change_log": change_log,
            "created_by": template.updated_by or template.created_by,
            "updated_by": template.updated_by or template.created_by,
        }
        for field in VERSION_SNAPSHOT_FIELDS:
            version_dict[field] = getattr(template, field, None)

        self.version_repository.create(version_dict)

    def create_template(self, template_in: PromptTemplateCreate) -> PromptTemplateResponse:
        """
        Create a new prompt template

        Args:
            template_in: Prompt template creation data

        Returns:
            Created prompt template

        Raises:
            HTTPException: If template_name or template_code already exists
        """
        # Check if template_name already exists
        existing = self.repository.get_by_name(template_in.template_name)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"模板名称 '{template_in.template_name}' 已存在"
            )

        # Check if template_code already exists
        if template_in.template_code:
            existing_code = self.repository.get_by_code(template_in.template_code)
            if existing_code:
                raise HTTPException(
                    status_code=400,
                    detail=f"模板编码 '{template_in.template_code}' 已存在"
                )

        change_log = template_in.change_log
        template_dict = template_in.model_dump(exclude={"change_log"})
        template_dict["current_version"] = 1
        template = self.repository.create(template_dict)

        # 创建 v1 版本快照
        self._create_version_snapshot(template, version=1, change_log=change_log or "初始版本")

        return PromptTemplateResponse.model_validate(template)

    def get_template(self, template_id: str) -> Optional[PromptTemplateResponse]:
        """
        Get prompt template by ID

        Args:
            template_id: Prompt template ID

        Returns:
            Prompt template or None
        """
        template = self.repository.get(template_id)
        if template:
            return PromptTemplateResponse.model_validate(template)
        return None

    def get_template_by_name(self, template_name: str) -> Optional[PromptTemplateResponse]:
        """
        Get prompt template by name

        Args:
            template_name: Template name

        Returns:
            Prompt template or None
        """
        template = self.repository.get_by_name(template_name)
        if template:
            return PromptTemplateResponse.model_validate(template)
        return None

    def get_templates(
        self,
        skip: int = 0,
        limit: int = 100,
        keyword: Optional[str] = None,
        owner: Optional[str] = None,
        qc_number: Optional[str] = None,
        prompt_source: Optional[str] = None
    ) -> PromptTemplateListResponse:
        """
        Get all prompt templates with pagination and optional keyword search and filters

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            keyword: Keyword to search across multiple fields (template_name, system_prompt, user_prompt, function_category, owner, qc_number, prompt_source, remarks)
            owner: Filter by owner (fuzzy match)
            qc_number: Filter by QC number (fuzzy match)
            prompt_source: Filter by prompt source (fuzzy match)

        Returns:
            List of prompt templates with total count
        """
        templates = self.repository.get_all(
            skip=skip,
            limit=limit,
            keyword=keyword,
            owner=owner,
            qc_number=qc_number,
            prompt_source=prompt_source
        )

        # 如果有任何过滤条件，计算过滤后的总数；否则是数据库总数
        if keyword or owner or qc_number or prompt_source:
            total = self.repository.count_filtered(
                keyword=keyword,
                owner=owner,
                qc_number=qc_number,
                prompt_source=prompt_source
            )
        else:
            total = self.repository.count()

        return PromptTemplateListResponse(
            total=total,
            items=[PromptTemplateResponse.model_validate(t) for t in templates]
        )

    def get_all_templates(self) -> PromptTemplateListResponse:
        """
        Get all prompt templates without pagination

        Returns:
            List of all prompt templates ordered by updated_at desc
        """
        templates = self.repository.get_all(skip=0, limit=10000)

        return PromptTemplateListResponse(
            total=len(templates),
            items=[PromptTemplateResponse.model_validate(t) for t in templates]
        )

    def update_template(
        self,
        template_id: str,
        template_in: PromptTemplateUpdate
    ) -> Optional[PromptTemplateResponse]:
        """
        Update a prompt template

        Args:
            template_id: Prompt template ID
            template_in: Updated prompt template data

        Returns:
            Updated prompt template or None

        Raises:
            HTTPException: If template_name conflicts with existing template
        """
        # If updating template_name, check for conflicts
        if template_in.template_name:
            existing = self.repository.get_by_name(template_in.template_name)
            if existing and existing.id != template_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"模板名称 '{template_in.template_name}' 已存在"
                )

        # If updating template_code, check for conflicts
        if template_in.template_code:
            existing_code = self.repository.get_by_code(template_in.template_code)
            if existing_code and existing_code.id != template_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"模板编码 '{template_in.template_code}' 已存在"
                )

        change_log = template_in.change_log
        template_dict = template_in.model_dump(exclude_unset=True, exclude={"change_log"})

        # 递增版本号
        current_template = self.repository.get(template_id)
        if not current_template:
            return None

        new_version = (current_template.current_version or 0) + 1
        template_dict["current_version"] = new_version

        template = self.repository.update(template_id, template_dict)
        if template:
            # 创建新版本快照
            self._create_version_snapshot(template, version=new_version, change_log=change_log)
            return PromptTemplateResponse.model_validate(template)
        return None

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a prompt template and all associated use cases and versions

        Args:
            template_id: Prompt template ID

        Returns:
            True if deleted, False if not found

        Note:
            This will manually delete all prompt use cases and version history
            associated with this template first, then delete the template itself.
        """
        # 检查模板是否存在
        template = self.repository.get(template_id)
        if not template:
            return False

        # 获取并删除所有关联的用例
        use_cases = self.use_case_repository.get_by_template_id(template_id, skip=0, limit=10000)
        use_case_count = len(use_cases)

        # 先删除所有关联的用例
        for use_case in use_cases:
            self.use_case_repository.delete(use_case.id)

        # 删除所有关联的版本记录
        version_count = self.version_repository.delete_by_template_id(template_id)

        # 提交用例和版本删除
        self.db.commit()

        # 然后删除模板
        success = self.repository.delete(template_id)

        if success and (use_case_count > 0 or version_count > 0):
            print(f"Deleted template {template_id} with {use_case_count} use cases and {version_count} versions")

        return success

    # ============= 版本管理方法 =============

    def get_template_versions(
        self,
        template_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> PromptTemplateVersionListResponse:
        """
        获取模板的版本列表

        Args:
            template_id: 模板ID
            skip: 跳过记录数
            limit: 返回记录数上限

        Returns:
            版本列表
        """
        template = self.repository.get(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="找不到提示词模板")

        versions = self.version_repository.get_by_template_id(template_id, skip=skip, limit=limit)
        total = self.version_repository.count_by_template_id(template_id)

        return PromptTemplateVersionListResponse(
            total=total,
            items=[PromptTemplateVersionResponse.model_validate(v) for v in versions]
        )

    def get_template_version(
        self,
        template_id: str,
        version: int
    ) -> PromptTemplateVersionResponse:
        """
        获取模板的指定版本详情

        Args:
            template_id: 模板ID
            version: 版本号

        Returns:
            版本详情
        """
        version_obj = self.version_repository.get_by_template_id_and_version(template_id, version)
        if not version_obj:
            raise HTTPException(status_code=404, detail=f"找不到版本 v{version}")

        return PromptTemplateVersionResponse.model_validate(version_obj)

    def diff_template_versions(
        self,
        template_id: str,
        from_version: int,
        to_version: int
    ) -> PromptTemplateVersionDiffResponse:
        """
        对比两个版本之间的差异

        Args:
            template_id: 模板ID
            from_version: 起始版本号
            to_version: 目标版本号

        Returns:
            差异列表
        """
        from_obj = self.version_repository.get_by_template_id_and_version(template_id, from_version)
        if not from_obj:
            raise HTTPException(status_code=404, detail=f"找不到版本 v{from_version}")

        to_obj = self.version_repository.get_by_template_id_and_version(template_id, to_version)
        if not to_obj:
            raise HTTPException(status_code=404, detail=f"找不到版本 v{to_version}")

        diffs: List[PromptTemplateVersionDiff] = []
        for field in VERSION_SNAPSHOT_FIELDS:
            old_val = getattr(from_obj, field, None)
            new_val = getattr(to_obj, field, None)
            if old_val != new_val:
                diffs.append(PromptTemplateVersionDiff(
                    field=field,
                    field_label=FIELD_LABELS.get(field, field),
                    old_value=old_val,
                    new_value=new_val,
                ))

        return PromptTemplateVersionDiffResponse(
            template_id=template_id,
            from_version=from_version,
            to_version=to_version,
            diffs=diffs,
        )

    def rollback_template_version(
        self,
        template_id: str,
        version: int
    ) -> PromptTemplateResponse:
        """
        将模板回滚到指定版本

        Args:
            template_id: 模板ID
            version: 要回滚到的版本号

        Returns:
            回滚后的模板
        """
        template = self.repository.get(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="找不到提示词模板")

        version_obj = self.version_repository.get_by_template_id_and_version(template_id, version)
        if not version_obj:
            raise HTTPException(status_code=404, detail=f"找不到版本 v{version}")

        # 用版本快照的内容覆盖模板
        rollback_dict = {}
        for field in VERSION_SNAPSHOT_FIELDS:
            rollback_dict[field] = getattr(version_obj, field, None)

        new_version = (template.current_version or 0) + 1
        rollback_dict["current_version"] = new_version

        updated_template = self.repository.update(template_id, rollback_dict)
        if not updated_template:
            raise HTTPException(status_code=500, detail="回滚失败")

        # 创建新版本快照（记录回滚操作）
        self._create_version_snapshot(
            updated_template,
            version=new_version,
            change_log=f"从 v{version} 回滚"
        )

        self.db.commit()
        return PromptTemplateResponse.model_validate(updated_template)
