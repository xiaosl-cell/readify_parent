"""
FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import setup_logging
from app.core.database import init_db, close_db, is_async_db
from app.api.v1 import api_router
from app.services.sentence_bert import get_sentence_bert_service
from app.services.scheduler import start_scheduler, stop_scheduler
from app.middleware import RequestLoggingMiddleware


# Configure logging with daily rotation
setup_logging(
    log_level=settings.logging.level,
    log_format=settings.logging.format,
    log_dir=settings.logging.log_dir,
    log_file=settings.logging.log_file,
    backup_count=settings.logging.backup_count,
    console_output=settings.logging.console_output,
    console_level=settings.logging.console_level,
    file_level=settings.logging.file_level
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    logger.info("Starting up application...")
    
    if is_async_db:
        await init_db()
    else:
        init_db()
    
    logger.info("Database initialized successfully")
    
    # 预加载 Sentence-BERT 模型
    logger.info("Pre-loading Sentence-BERT model...")
    try:
        sbert_service = get_sentence_bert_service()
        if sbert_service.is_model_loaded():
            logger.info("Sentence-BERT model pre-loaded successfully")
        else:
            logger.warning("Sentence-BERT model pre-loading failed")
    except Exception as e:
        logger.error(f"Failed to pre-load Sentence-BERT model: {str(e)}")
    
    # 启动后台定时任务调度器
    logger.info("Starting background scheduler...")
    try:
        await start_scheduler()
        logger.info("Background scheduler started (checking for evaluation timeouts every 5 minutes)")
    except Exception as e:
        logger.error(f"Failed to start background scheduler: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # 停止后台定时任务调度器
    logger.info("Stopping background scheduler...")
    try:
        await stop_scheduler()
        logger.info("Background scheduler stopped")
    except Exception as e:
        logger.warning(f"Failed to stop background scheduler: {str(e)}")
    
    if is_async_db:
        await close_db()
    else:
        close_db()
    
    logger.info("Application shut down successfully")


# Create FastAPI application
app = FastAPI(
    title=settings.app.name,
    description=settings.app.description,
    version=settings.app.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)


# Include API router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level=settings.logging.level.lower()
    )

