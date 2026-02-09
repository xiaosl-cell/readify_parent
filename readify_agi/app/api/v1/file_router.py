from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.user_context import UserContext, get_user_context
from app.models.file import FileCreate, FileResponse, FileDB
from app.repositories.file_repository import FileRepository
from app.repositories.document_repository import DocumentRepository
from app.services.file_service import FileService
from app.services.document_service import DocumentService
from app.services.llama_parse_service import LlamaParseService
from app.services.file_vectorize_service import FileVectorizeService
from app.services.vector_store_service import VectorStoreService, Visibility
from app.services.file_search_service import FileSearchService
from app.services.file_process_service import FileProcessService
from app.services.callback_service import CallbackService

# 创建路由器
router = APIRouter(prefix="/files")

# 依赖注入
async def get_file_service(db: AsyncSession = Depends(get_db)) -> FileService:
    """获取文件服务实例"""
    file_repository = FileRepository(db)
    return FileService(file_repository)

async def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """获取文档服务实例"""
    doc_repository = DocumentRepository(db)
    file_repository = FileRepository(db)
    llama_service = LlamaParseService()
    return DocumentService(doc_repository, file_repository, llama_service)

async def get_file_vectorize_service(db: AsyncSession = Depends(get_db)) -> FileVectorizeService:
    """获取文件向量化服务实例"""
    file_repository = FileRepository(db)
    document_repository = DocumentRepository(db)
    vector_store_service = VectorStoreService()
    return FileVectorizeService(
        file_repository,
        document_repository,
        vector_store_service
    )

async def get_file_search_service(db: AsyncSession = Depends(get_db)) -> FileSearchService:
    """获取文件搜索服务实例"""
    file_repository = FileRepository(db)
    vector_store_service = VectorStoreService()
    return FileSearchService(file_repository, vector_store_service)

async def get_file_process_service(db: AsyncSession = Depends(get_db)) -> FileProcessService:
    """获取文件处理服务实例"""
    file_repository = FileRepository(db)
    document_repository = DocumentRepository(db)
    llama_parse_service = LlamaParseService()
    vector_store_service = VectorStoreService()
    callback_service = CallbackService()
    return FileProcessService(
        file_repository,
        document_repository,
        llama_parse_service,
        vector_store_service,
        callback_service
    )

# 路由定义
@router.get("/", response_model=List[FileResponse])
async def list_files(
    skip: int = 0,
    limit: int = 100,
    service: FileService = Depends(get_file_service)
):
    """获取文件列表"""
    return await service.get_files(skip, limit)

@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: int,
    service: FileService = Depends(get_file_service)
):
    """获取指定文件"""
    return await service.get_file(file_id)

@router.post("/", response_model=FileResponse)
async def create_file(
    file: FileCreate,
    service: FileService = Depends(get_file_service)
):
    """创建文件"""
    return await service.create_file(file)

@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    service: FileService = Depends(get_file_service)
):
    """删除文件"""
    return await service.delete_file(file_id)

@router.get("/parse/{file_id}")
async def parse_file(
    file_id: int,
    service: DocumentService = Depends(get_document_service)
):
    """
    解析指定ID的文件并存储解析结果

    Args:
        file_id: 文件ID
        :param file_id:
        :param service:
    """
    await service.parse_and_save(file_id)
    return {"message": "文件解析完成"}

@router.post("/{file_id}/vectorize")
async def vectorize_file(
    file_id: int,
    project_id: Optional[int] = Query(None, description="项目ID"),
    visibility: str = Query(Visibility.PRIVATE, description="可见性级别: private/project/public"),
    user_ctx: UserContext = Depends(get_user_context),
    service: FileVectorizeService = Depends(get_file_vectorize_service)
) -> dict:
    """
    向量化指定文件的内容（异步任务）

    Args:
        file_id: 文件ID
        project_id: 项目ID（可选）
        visibility: 可见性级别
        user_ctx: 用户上下文（从请求头自动提取）

    Returns:
        dict: 处理结果
    """
    try:
        await service.vectorize_file(
            file_id,
            user_id=user_ctx.user_id or 0,
            project_id=project_id or 0,
            visibility=visibility,
        )
        return {
            "message": "向量化任务已启动",
            "file_id": file_id,
            "status": "processing",
            "user_id": user_ctx.user_id,
            "visibility": visibility,
            "note": "任务已进入后台处理队列，请稍后查看处理结果"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动向量化任务失败: {str(e)}")

@router.get("/{file_id}/search")
async def search_in_file(
    file_id: int,
    query: str = Query(..., description="搜索文本"),
    top_k: int = Query(5, description="返回结果数量"),
    project_id: Optional[int] = Query(None, description="项目ID（用于项目级权限过滤）"),
    user_ctx: UserContext = Depends(get_user_context),
    service: FileSearchService = Depends(get_file_search_service)
) -> List[Dict[str, Any]]:
    """
    在指定文件中搜索相似文本

    Args:
        file_id: 文件ID
        query: 搜索文本
        top_k: 返回结果数量
        project_id: 项目ID（用于项目级权限过滤）
        user_ctx: 用户上下文（从请求头自动提取）

    Returns:
        List[Dict[str, Any]]: 搜索结果列表，包含：
            - content: 文本内容
            - score: 相似度分数
            - metadata: 元数据
    """
    try:
        results = await service.search_in_file(
            file_id=file_id,
            query_text=query,
            top_k=top_k,
            user_id=user_ctx.user_id,
            user_role=user_ctx.user_role,
            project_id=project_id,
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.post("/{file_id}/process")
async def process_file(
    file_id: int,
    project_id: Optional[int] = Query(None, description="项目ID"),
    visibility: str = Query(Visibility.PRIVATE, description="可见性级别: private/project/public"),
    user_ctx: UserContext = Depends(get_user_context),
    service: FileProcessService = Depends(get_file_process_service)
) -> dict:
    """
    异步处理文件：解析并向量化

    该接口会异步执行以下操作：
    1. 解析文件内容（若已有解析结果则覆盖）
    2. 向量化文件内容（若已有向量则覆盖）
    3. 更新文件状态（vectorized=True）
    4. 回调通知第三方接口处理完成

    Args:
        file_id: 文件ID
        project_id: 项目ID（可选）
        visibility: 可见性级别
        user_ctx: 用户上下文（从请求头自动提取）

    Returns:
        dict: 处理结果
    """
    try:
        await service.process_file(
            file_id,
            user_id=user_ctx.user_id or 0,
            project_id=project_id or 0,
            visibility=visibility,
        )
        return {
            "message": "文件处理任务已启动",
            "file_id": file_id,
            "status": "processing",
            "user_id": user_ctx.user_id,
            "visibility": visibility,
            "note": "任务已进入后台处理队列，完成后将通过回调接口通知"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动处理任务失败: {str(e)}")

@router.get("/project/{project_id}/search")
async def search_in_project(
    project_id: int,
    query: str = Query(..., description="搜索文本"),
    top_k: int = Query(5, description="返回结果数量"),
    user_ctx: UserContext = Depends(get_user_context),
    service: FileService = Depends(get_file_service)
) -> List[Dict[str, Any]]:
    """
    基于project_id的向量检索

    根据项目ID查询相关文件，并在这些文件中执行向量检索，找出与输入文本最相似的内容

    Args:
        project_id: 项目ID
        query: 搜索文本
        top_k: 返回结果数量
        user_ctx: 用户上下文（从请求头自动提取）

    Returns:
        List[Dict[str, Any]]: 搜索结果列表，包含：
            - content: 文本内容
            - distance: 相似度距离
            - file_id: 文件ID
            - file_name: 文件名称
    """
    try:
        results = await service.search_files_by_vector(
            project_id=project_id,
            input_text=query,
            top_k=top_k,
            user_id=user_ctx.user_id,
            user_role=user_ctx.user_role,
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"项目文件向量检索失败: {str(e)}")