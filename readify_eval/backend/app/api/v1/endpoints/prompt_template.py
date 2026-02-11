"""
Prompt Template endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.prompt_template import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptTemplateListResponse
)
from app.schemas.prompt_template_version import (
    PromptTemplateVersionResponse,
    PromptTemplateVersionListResponse,
    PromptTemplateVersionDiffResponse,
)
from app.services.prompt_template import PromptTemplateService

router = APIRouter()


def get_prompt_template_service(db: Session = Depends(get_db)) -> PromptTemplateService:
    """
    Dependency to get PromptTemplateService instance

    Args:
        db: Database session

    Returns:
        PromptTemplateService instance
    """
    return PromptTemplateService(db)


@router.post("", response_model=PromptTemplateResponse, status_code=201)
def create_template(
    template_in: PromptTemplateCreate,
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    Create a new prompt template

    Args:
        template_in: Prompt template creation data
        service: Prompt template service

    Returns:
        Created prompt template

    Raises:
        HTTPException: If template_name already exists
    """
    return service.create_template(template_in)


@router.get("/all", response_model=PromptTemplateListResponse)
def get_all_templates(
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    Get all prompt templates without pagination

    Args:
        service: Prompt template service

    Returns:
        List of all prompt templates, ordered by updated_at desc
    """
    return service.get_all_templates()


@router.get("/by-name/{template_name}", response_model=PromptTemplateResponse)
def get_template_by_name(
    template_name: str,
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    根据模板名称查询提示词模板

    Args:
        template_name: 提示词模板名称
        service: 提示词模板服务

    Returns:
        提示词模板详情

    Raises:
        HTTPException: 模板不存在时抛出 404
    """
    template = service.get_template_by_name(template_name)
    if not template:
        raise HTTPException(status_code=404, detail=f"找不到名为 '{template_name}' 的提示词模板")
    return template


# ============= 版本管理端点 =============
# 注意：diff 路由必须在 {version} 路由之前声明，避免路径冲突

@router.get("/{template_id}/versions/diff", response_model=PromptTemplateVersionDiffResponse)
def diff_template_versions(
    template_id: str,
    from_version: int = Query(..., ge=1, description="对比起始版本号"),
    to_version: int = Query(..., ge=1, description="对比目标版本号"),
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    对比两个版本之间的差异

    Args:
        template_id: 模板ID
        from_version: 起始版本号
        to_version: 目标版本号
        service: Prompt template service

    Returns:
        两个版本之间的字段差异列表
    """
    return service.diff_template_versions(template_id, from_version, to_version)


@router.get("/{template_id}/versions/{version}", response_model=PromptTemplateVersionResponse)
def get_template_version(
    template_id: str,
    version: int,
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    获取模板的指定版本详情

    Args:
        template_id: 模板ID
        version: 版本号
        service: Prompt template service

    Returns:
        版本详情（包含该版本的完整模板快照）
    """
    return service.get_template_version(template_id, version)


@router.get("/{template_id}/versions", response_model=PromptTemplateVersionListResponse)
def get_template_versions(
    template_id: str,
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数上限"),
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    获取模板的版本列表

    Args:
        template_id: 模板ID
        skip: 跳过记录数
        limit: 返回记录数上限
        service: Prompt template service

    Returns:
        版本列表，按版本号降序排列
    """
    return service.get_template_versions(template_id, skip=skip, limit=limit)


@router.post("/{template_id}/versions/{version}/rollback", response_model=PromptTemplateResponse)
def rollback_template_version(
    template_id: str,
    version: int,
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    将模板回滚到指定版本

    回滚会创建一个新版本（版本号递增），内容恢复为目标版本的快照。

    Args:
        template_id: 模板ID
        version: 要回滚到的版本号
        service: Prompt template service

    Returns:
        回滚后的模板（版本号已递增）
    """
    return service.rollback_template_version(template_id, version)


# ============= 模板 CRUD 端点 =============

@router.get("/{template_id}", response_model=PromptTemplateResponse)
def get_template(
    template_id: str,
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    Get prompt template by ID

    Args:
        template_id: Prompt template ID
        service: Prompt template service

    Returns:
        Prompt template details

    Raises:
        HTTPException: If template not found
    """
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="找不到提示词模板")
    return template


@router.get("", response_model=PromptTemplateListResponse)
def get_templates(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    keyword: Optional[str] = Query(None, description="Keyword to search across template_name, system_prompt, user_prompt, function_category, owner, qc_number, prompt_source, and remarks"),
    owner: Optional[str] = Query(None, description="Filter by owner (fuzzy match)"),
    qc_number: Optional[str] = Query(None, description="Filter by QC number (fuzzy match)"),
    prompt_source: Optional[str] = Query(None, description="Filter by prompt source (fuzzy match)"),
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    Get all prompt templates with pagination and optional keyword search and filters

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        keyword: Keyword to search across multiple fields (fuzzy match on template_name, system_prompt, user_prompt, function_category, owner, qc_number, prompt_source, remarks)
        owner: Filter by owner (fuzzy match)
        qc_number: Filter by QC number (fuzzy match)
        prompt_source: Filter by prompt source (fuzzy match)
        service: Prompt template service

    Returns:
        List of prompt templates with pagination, ordered by updated_at desc
    """
    return service.get_templates(skip=skip, limit=limit, keyword=keyword, owner=owner, qc_number=qc_number, prompt_source=prompt_source)


@router.put("/{template_id}", response_model=PromptTemplateResponse)
def update_template(
    template_id: str,
    template_in: PromptTemplateUpdate,
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    Update a prompt template

    Args:
        template_id: Prompt template ID
        template_in: Updated prompt template data
        service: Prompt template service

    Returns:
        Updated prompt template

    Raises:
        HTTPException: If template not found or template_name conflicts
    """
    template = service.update_template(template_id, template_in)
    if not template:
        raise HTTPException(status_code=404, detail="找不到提示词模板")
    return template


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: str,
    service: PromptTemplateService = Depends(get_prompt_template_service)
):
    """
    Delete a prompt template and all associated use cases and version history

    Args:
        template_id: Prompt template ID
        service: Prompt template service

    Raises:
        HTTPException: If template not found

    Note:
        This operation will cascade delete all prompt use cases and version history
        that reference this template.
    """
    success = service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="找不到提示词模板")
