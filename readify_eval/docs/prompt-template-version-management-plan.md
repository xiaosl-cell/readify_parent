# 提示词模板版本管理 — 实现方案

## 1. 背景与目标

**现状：** `eval_prompt_templates` 表支持模板 CRUD，但每次修改是原地覆盖，无版本历史。`TestExecution` 通过快照字段（`rendered_system_prompt`、`llm_params_snapshot` 等）保留了执行时的状态，但无法回溯模板本身的变更轨迹。

**目标：**

- 模板每次更新自动生成版本记录，支持完整变更追溯
- 支持版本列表查看、任意两版本 diff 对比、一键回滚到历史版本
- `TestExecution` 快照关联到具体版本号，建立精确溯源链路
- 前端提供版本历史列表、diff 视图、回滚操作入口

---

## 2. 数据库设计

### 2.1 新增表 `eval_prompt_template_versions`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | `VARCHAR(36)` | PK, UUID | 版本记录主键 |
| `template_id` | `VARCHAR(36)` | FK → `eval_prompt_templates.id`, NOT NULL, INDEX | 所属模板 |
| `version` | `INT` | NOT NULL | 版本号（同一 template_id 下自增，从 1 开始） |
| `template_name` | `VARCHAR(255)` | NOT NULL | 快照：模板名称 |
| `system_prompt` | `TEXT` | | 快照：系统提示词 |
| `user_prompt` | `TEXT` | | 快照：用户提示词 |
| `max_tokens` | `VARCHAR(50)` | | 快照：max_tokens |
| `top_p` | `VARCHAR(50)` | | 快照：top_p |
| `top_k` | `VARCHAR(50)` | | 快照：top_k |
| `temperature` | `VARCHAR(50)` | | 快照：temperature |
| `evaluation_strategies` | `JSON` | | 快照：评估策略 |
| `function_category` | `VARCHAR(255)` | | 快照：功能分类 |
| `remarks` | `TEXT` | | 快照：备注 |
| `owner` | `VARCHAR(255)` | | 快照：负责人 |
| `qc_number` | `VARCHAR(255)` | | 快照：质检编号 |
| `prompt_source` | `VARCHAR(255)` | | 快照：来源 |
| `change_log` | `TEXT` | | 变更说明（用户填写或自动生成） |
| `created_at` | `DATETIME` | NOT NULL | 版本创建时间 |
| `created_by` | `VARCHAR(36)` | | 版本创建人 |

**唯一约束：** `UNIQUE(template_id, version)`

**索引：** `INDEX(template_id, version DESC)` — 加速按模板查最新版本

### 2.2 修改 `eval_prompt_templates` 表

新增字段：

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `current_version` | `INT` | NOT NULL, DEFAULT 0 | 当前版本号，0 表示尚未创建版本 |

### 2.3 修改 `eval_test_executions` 表

新增字段：

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `template_version` | `INT` | | 执行时的模板版本号 |
| `template_version_id` | `VARCHAR(36)` | | 执行时的版本记录 ID |

---

## 3. Model 层

### 3.1 新增 `app/models/prompt_template_version.py`

```python
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey, UniqueConstraint, Index
from datetime import datetime
import uuid

from app.models.base import Base


class PromptTemplateVersion(Base):
    """提示词模板版本记录"""
    __tablename__ = "eval_prompt_template_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    template_id = Column(String(36), ForeignKey("eval_prompt_templates.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    version = Column(Integer, nullable=False)

    # 模板快照字段（与 PromptTemplate 一一对应）
    template_name = Column(String(255), nullable=False)
    system_prompt = Column(Text, nullable=True)
    user_prompt = Column(Text, nullable=True)
    max_tokens = Column(String(50), nullable=True)
    top_p = Column(String(50), nullable=True)
    top_k = Column(String(50), nullable=True)
    temperature = Column(String(50), nullable=True)
    evaluation_strategies = Column(JSON, nullable=True)
    function_category = Column(String(255), nullable=True)
    remarks = Column(Text, nullable=True)
    owner = Column(String(255), nullable=True)
    qc_number = Column(String(255), nullable=True)
    prompt_source = Column(String(255), nullable=True)

    # 版本元信息
    change_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(36), nullable=True)

    __table_args__ = (
        UniqueConstraint("template_id", "version", name="uq_template_version"),
        Index("ix_template_version_desc", "template_id", version.desc()),
    )
```

### 3.2 修改 `app/models/prompt_template.py`

```python
# 在 PromptTemplate 类中新增字段：
current_version = Column(Integer, nullable=False, default=0, comment="当前版本号")
```

### 3.3 修改 `app/models/test_task.py`

```python
# 在 TestExecution 类中新增字段：
template_version = Column(Integer, nullable=True, comment="执行时的模板版本号")
template_version_id = Column(String(36), nullable=True, comment="执行时的版本记录ID")
```

### 3.4 注册 Model

在 `app/models/__init__.py` 中添加：

```python
from app.models.prompt_template_version import PromptTemplateVersion
```

---

## 4. Repository 层

### 4.1 新增 `app/repositories/prompt_template_version.py`

```python
from typing import List, Optional
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt_template_version import PromptTemplateVersion
from app.repositories.base import BaseRepository


class PromptTemplateVersionRepository(BaseRepository[PromptTemplateVersion]):
    def __init__(self, db: AsyncSession):
        super().__init__(PromptTemplateVersion, db)

    async def get_latest_version_number(self, template_id: str) -> int:
        """获取指定模板的最新版本号，无版本则返回 0"""
        query = select(func.coalesce(func.max(PromptTemplateVersion.version), 0)).where(
            PromptTemplateVersion.template_id == template_id
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def get_by_template_and_version(
        self, template_id: str, version: int
    ) -> Optional[PromptTemplateVersion]:
        """根据模板 ID 和版本号查询"""
        query = select(PromptTemplateVersion).where(
            PromptTemplateVersion.template_id == template_id,
            PromptTemplateVersion.version == version,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_versions_by_template(
        self, template_id: str, page: int = 1, page_size: int = 20
    ) -> List[PromptTemplateVersion]:
        """分页获取模板的版本列表（按版本号倒序）"""
        query = (
            select(PromptTemplateVersion)
            .where(PromptTemplateVersion.template_id == template_id)
            .order_by(desc(PromptTemplateVersion.version))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_template(self, template_id: str) -> int:
        """统计模板的版本数量"""
        query = select(func.count()).where(
            PromptTemplateVersion.template_id == template_id
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def delete_by_template(self, template_id: str) -> int:
        """删除模板的所有版本（级联删除时使用）"""
        from sqlalchemy import delete as sql_delete
        query = sql_delete(PromptTemplateVersion).where(
            PromptTemplateVersion.template_id == template_id
        )
        result = await self.db.execute(query)
        return result.rowcount
```

---

## 5. Schema 层

### 5.1 新增 `app/schemas/prompt_template_version.py`

```python
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class VersionResponse(BaseModel):
    """版本详情响应"""
    id: str
    template_id: str
    version: int
    template_name: str
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    max_tokens: Optional[str] = None
    top_p: Optional[str] = None
    top_k: Optional[str] = None
    temperature: Optional[str] = None
    evaluation_strategies: Optional[list] = None
    function_category: Optional[str] = None
    remarks: Optional[str] = None
    owner: Optional[str] = None
    qc_number: Optional[str] = None
    prompt_source: Optional[str] = None
    change_log: Optional[str] = None
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class VersionListResponse(BaseModel):
    """版本列表响应"""
    items: List[VersionResponse]
    total: int


class VersionDiffField(BaseModel):
    """单个字段的 diff 结果"""
    field: str
    field_label: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None


class VersionDiffResponse(BaseModel):
    """两版本 diff 响应"""
    template_id: str
    from_version: int
    to_version: int
    changes: List[VersionDiffField]


class RollbackRequest(BaseModel):
    """回滚请求"""
    change_log: Optional[str] = Field(None, description="回滚说明，不填则自动生成")
```

### 5.2 修改 `app/schemas/prompt_template.py`

在 `PromptTemplateResponse` 中新增字段：

```python
current_version: int = 0
```

在 `PromptTemplateUpdate` 中新增可选字段：

```python
change_log: Optional[str] = Field(None, description="本次变更说明")
```

---

## 6. Service 层

### 6.1 修改 `app/services/prompt_template.py`

核心改动：在 `update_template` 中集成版本创建逻辑。

```python
# 新增依赖
from app.repositories.prompt_template_version import PromptTemplateVersionRepository
from app.models.prompt_template_version import PromptTemplateVersion


class PromptTemplateService:
    def __init__(self, db):
        self.db = db
        self.repo = PromptTemplateRepository(db)
        self.version_repo = PromptTemplateVersionRepository(db)  # 新增
        self.use_case_repo = PromptUseCaseRepository(db)

    async def update_template(self, template_id: str, data: PromptTemplateUpdate):
        """更新模板，自动创建版本记录"""
        template = await self.repo.get(template_id)
        if not template:
            raise ValueError("模板不存在")

        # 名称冲突检查（保持现有逻辑）
        if data.template_name:
            existing = await self.repo.get_by_name(data.template_name)
            if existing and existing.id != template_id:
                raise ValueError(f"模板名称 '{data.template_name}' 已存在")

        # ---- 新增：创建版本快照（在更新前） ----
        change_log = data.change_log if hasattr(data, 'change_log') else None
        await self._create_version_snapshot(template, change_log)

        # 执行更新（保持现有逻辑）
        update_data = data.model_dump(exclude_unset=True, exclude={"change_log"})
        updated = await self.repo.update(template_id, update_data)
        return PromptTemplateResponse.model_validate(updated)

    async def _create_version_snapshot(
        self, template, change_log: str = None
    ) -> PromptTemplateVersion:
        """为当前模板状态创建版本快照"""
        next_version = await self.version_repo.get_latest_version_number(template.id) + 1

        version_record = PromptTemplateVersion(
            template_id=template.id,
            version=next_version,
            template_name=template.template_name,
            system_prompt=template.system_prompt,
            user_prompt=template.user_prompt,
            max_tokens=template.max_tokens,
            top_p=template.top_p,
            top_k=template.top_k,
            temperature=template.temperature,
            evaluation_strategies=template.evaluation_strategies,
            function_category=template.function_category,
            remarks=template.remarks,
            owner=template.owner,
            qc_number=template.qc_number,
            prompt_source=template.prompt_source,
            change_log=change_log or f"版本 {next_version}",
            created_by=template.updated_by,
        )
        created = await self.version_repo.create(version_record)

        # 更新模板的 current_version
        await self.repo.update(template.id, {"current_version": next_version})

        return created

    async def create_template(self, data: PromptTemplateCreate):
        """创建模板（保持现有逻辑，创建后自动生成 v1）"""
        # ... 现有创建逻辑 ...
        template = await self.repo.create(entity)

        # 创建初始版本 v1
        await self._create_version_snapshot(template, "初始版本")

        return PromptTemplateResponse.model_validate(template)

    async def delete_template(self, template_id: str):
        """删除模板（新增：级联删除版本记录）"""
        template = await self.repo.get(template_id)
        if not template:
            raise ValueError("模板不存在")

        # 删除关联用例（保持现有逻辑）
        await self.use_case_repo.delete_by_template(template_id)
        # 新增：删除版本记录
        await self.version_repo.delete_by_template(template_id)
        # 删除模板
        await self.repo.delete(template_id)
```

### 6.2 新增版本管理方法（追加到 `PromptTemplateService`）

```python
    # ---- 版本管理方法 ----

    async def get_version_list(
        self, template_id: str, page: int = 1, page_size: int = 20
    ) -> VersionListResponse:
        """获取版本列表"""
        template = await self.repo.get(template_id)
        if not template:
            raise ValueError("模板不存在")

        versions = await self.version_repo.get_versions_by_template(
            template_id, page, page_size
        )
        total = await self.version_repo.count_by_template(template_id)

        return VersionListResponse(
            items=[VersionResponse.model_validate(v) for v in versions],
            total=total,
        )

    async def get_version_detail(
        self, template_id: str, version: int
    ) -> VersionResponse:
        """获取指定版本详情"""
        record = await self.version_repo.get_by_template_and_version(
            template_id, version
        )
        if not record:
            raise ValueError(f"版本 {version} 不存在")
        return VersionResponse.model_validate(record)

    async def diff_versions(
        self, template_id: str, from_version: int, to_version: int
    ) -> VersionDiffResponse:
        """对比两个版本的差异"""
        v_from = await self.version_repo.get_by_template_and_version(
            template_id, from_version
        )
        v_to = await self.version_repo.get_by_template_and_version(
            template_id, to_version
        )
        if not v_from or not v_to:
            raise ValueError("指定的版本不存在")

        # 需要对比的字段及其中文标签
        diff_fields = {
            "template_name": "模板名称",
            "system_prompt": "系统提示词",
            "user_prompt": "用户提示词",
            "max_tokens": "最大Token数",
            "top_p": "Top P",
            "top_k": "Top K",
            "temperature": "温度",
            "evaluation_strategies": "评估策略",
            "function_category": "功能分类",
            "remarks": "备注",
            "owner": "负责人",
            "qc_number": "质检编号",
            "prompt_source": "来源",
        }

        changes = []
        for field, label in diff_fields.items():
            old_val = getattr(v_from, field)
            new_val = getattr(v_to, field)

            # JSON 字段特殊处理
            if field == "evaluation_strategies":
                old_val = json.dumps(old_val, ensure_ascii=False) if old_val else None
                new_val = json.dumps(new_val, ensure_ascii=False) if new_val else None

            if str(old_val) != str(new_val):
                changes.append(VersionDiffField(
                    field=field,
                    field_label=label,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=str(new_val) if new_val is not None else None,
                ))

        return VersionDiffResponse(
            template_id=template_id,
            from_version=from_version,
            to_version=to_version,
            changes=changes,
        )

    async def rollback_to_version(
        self, template_id: str, target_version: int, change_log: str = None
    ) -> PromptTemplateResponse:
        """
        回滚到指定版本。
        策略：用目标版本的快照内容覆盖当前模板，同时生成一个新版本记录。
        """
        template = await self.repo.get(template_id)
        if not template:
            raise ValueError("模板不存在")

        target = await self.version_repo.get_by_template_and_version(
            template_id, target_version
        )
        if not target:
            raise ValueError(f"版本 {target_version} 不存在")

        # 先为当前状态创建版本快照（保存回滚前的状态）
        rollback_log = change_log or f"回滚到版本 {target_version}"
        await self._create_version_snapshot(template, f"回滚前快照（即将{rollback_log}）")

        # 用目标版本的内容覆盖模板
        rollback_data = {
            "template_name": target.template_name,
            "system_prompt": target.system_prompt,
            "user_prompt": target.user_prompt,
            "max_tokens": target.max_tokens,
            "top_p": target.top_p,
            "top_k": target.top_k,
            "temperature": target.temperature,
            "evaluation_strategies": target.evaluation_strategies,
            "function_category": target.function_category,
            "remarks": target.remarks,
            "owner": target.owner,
            "qc_number": target.qc_number,
            "prompt_source": target.prompt_source,
        }
        updated = await self.repo.update(template_id, rollback_data)

        # 再创建一个版本记录，标记这是回滚后的状态
        await self._create_version_snapshot(updated, rollback_log)

        return PromptTemplateResponse.model_validate(updated)
```

---

## 7. API 层

### 7.1 修改 `app/api/v1/endpoints/prompt_template.py`

在现有路由文件中追加版本管理端点：

```python
from app.schemas.prompt_template_version import (
    VersionResponse,
    VersionListResponse,
    VersionDiffResponse,
    RollbackRequest,
)


@router.get("/{template_id}/versions", response_model=VersionListResponse,
            summary="获取模板版本列表")
async def get_template_versions(
    template_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: PromptTemplateService = Depends(get_prompt_template_service),
):
    return await service.get_version_list(template_id, page, page_size)


@router.get("/{template_id}/versions/{version}", response_model=VersionResponse,
            summary="获取指定版本详情")
async def get_template_version_detail(
    template_id: str,
    version: int,
    service: PromptTemplateService = Depends(get_prompt_template_service),
):
    return await service.get_version_detail(template_id, version)


@router.get("/{template_id}/versions/diff", response_model=VersionDiffResponse,
            summary="对比两个版本差异")
async def diff_template_versions(
    template_id: str,
    from_version: int = Query(..., description="起始版本号"),
    to_version: int = Query(..., description="目标版本号"),
    service: PromptTemplateService = Depends(get_prompt_template_service),
):
    return await service.diff_versions(template_id, from_version, to_version)


@router.post("/{template_id}/rollback/{version}", response_model=PromptTemplateResponse,
             summary="回滚到指定版本")
async def rollback_template_version(
    template_id: str,
    version: int,
    body: RollbackRequest = None,
    service: PromptTemplateService = Depends(get_prompt_template_service),
):
    change_log = body.change_log if body else None
    return await service.rollback_to_version(template_id, version, change_log)
```

### 7.2 完整 API 清单

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| `GET` | `/prompt-templates/{id}/versions` | 分页获取版本列表 | 新增 |
| `GET` | `/prompt-templates/{id}/versions/{version}` | 获取版本详情 | 新增 |
| `GET` | `/prompt-templates/{id}/versions/diff?from_version=1&to_version=3` | 版本 diff | 新增 |
| `POST` | `/prompt-templates/{id}/rollback/{version}` | 回滚到指定版本 | 新增 |
| `PUT` | `/prompt-templates/{id}` | 更新模板（自动创建版本） | 改造 |
| `POST` | `/prompt-templates` | 创建模板（自动创建 v1） | 改造 |
| `DELETE` | `/prompt-templates/{id}` | 删除模板（级联删除版本） | 改造 |

---

## 8. 数据库迁移

### 8.1 Alembic 迁移脚本

```bash
cd readify_eval/backend
alembic revision --autogenerate -m "add_prompt_template_version_management"
alembic upgrade head
```

迁移内容（自动生成后需要检查）：

1. 创建 `eval_prompt_template_versions` 表
2. 在 `eval_prompt_templates` 表中新增 `current_version` 列（INT, DEFAULT 0）
3. 在 `eval_test_executions` 表中新增 `template_version` 和 `template_version_id` 列

### 8.2 数据迁移（存量模板）

迁移脚本执行后，需要为已有模板生成初始版本（v1）：

```python
# 在迁移脚本的 upgrade() 末尾或单独的数据迁移脚本中
def migrate_existing_templates():
    """为存量模板创建初始版本记录"""
    # 1. 查询所有 current_version = 0 的模板
    # 2. 为每个模板创建 v1 版本记录（快照当前内容）
    # 3. 更新模板的 current_version = 1
```

---

## 9. TestExecution 溯源增强

### 9.1 执行时记录版本

在测试执行创建流程中（`test_execution_service.py` 或相关 service），创建 `TestExecution` 时同步记录模板的当前版本：

```python
# 在创建 TestExecution 时
template = await prompt_template_repo.get(template_id)
execution = TestExecution(
    # ... 现有字段 ...
    template_version=template.current_version,
    template_version_id=None,  # 可选：通过 version_repo 查 ID
)
```

### 9.2 查询增强

`TestExecution` 查询接口返回时，附带 `template_version` 信息，便于溯源：

```python
# 在 TestExecution 的响应 schema 中新增
template_version: Optional[int] = None
template_version_id: Optional[str] = None
```

---

## 10. 版本管理策略

### 10.1 版本创建时机

| 操作 | 是否创建版本 | 说明 |
|------|-------------|------|
| 创建模板 | 是（v1） | 作为初始基线 |
| 更新模板 | 是（v_n+1） | 更新前快照当前状态 |
| 回滚 | 是（v_n+1, v_n+2） | 回滚前快照 + 回滚后快照 |
| 删除模板 | 级联删除 | 所有版本一并删除 |

### 10.2 存储策略

- **全量快照**：每个版本存储完整的模板内容，非增量 diff。优点是简单可靠，回滚直接覆盖；缺点是存储冗余，但提示词模板数据量小，不构成问题。
- **版本号连续自增**：同一模板下的 version 从 1 递增，不复用已删除的版本号。

### 10.3 并发控制

当前架构中模板更新频率低，暂不引入乐观锁。如后续出现并发编辑场景，可在 `eval_prompt_templates` 表增加 `version_seq`（乐观锁字段），更新时 `WHERE version_seq = ?` 做 CAS 校验。

---

## 11. 实施步骤

```
步骤 1：Model + Migration
  ├── 新建 prompt_template_version.py Model
  ├── 修改 PromptTemplate Model（加 current_version）
  ├── 修改 TestExecution Model（加 template_version 字段）
  ├── 注册 Model 到 __init__.py
  └── 执行 alembic 迁移 + 存量数据迁移

步骤 2：Repository
  └── 新建 PromptTemplateVersionRepository

步骤 3：Schema
  ├── 新建 prompt_template_version.py schemas
  └── 修改 PromptTemplate schemas（加 current_version / change_log）

步骤 4：Service
  ├── 改造 create_template（创建后生成 v1）
  ├── 改造 update_template（更新前生成版本快照）
  ├── 改造 delete_template（级联删除版本）
  └── 新增 get_version_list / get_version_detail / diff_versions / rollback_to_version

步骤 5：API
  └── 在 prompt_template.py 路由中新增 4 个版本管理端点

步骤 6：TestExecution 溯源
  ├── 执行创建时记录 template_version
  └── 响应 schema 返回版本号

步骤 7：前端（后续）
  ├── 版本历史列表面板
  ├── 版本 diff 对比视图
  └── 回滚确认操作
```

---

## 12. 注意事项

1. **向后兼容**：`current_version` 默认值为 0，存量数据不影响现有功能；版本相关字段均为可选（nullable）。
2. **级联删除**：删除模板时 `ondelete="CASCADE"` 在数据库层面保证版本记录一致性，Service 层也做了显式删除。
3. **change_log 可选**：更新模板时 `change_log` 为可选字段，不填则自动生成 `"版本 N"`。
4. **diff 端点路由顺序**：`/versions/diff` 路径需放在 `/versions/{version}` 前面，否则 `diff` 会被 FastAPI 当作 `{version}` 参数解析。
5. **存量迁移**：上线时需执行一次存量模板的 v1 初始化，确保所有模板都有基线版本。
