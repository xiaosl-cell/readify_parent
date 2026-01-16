from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1 import file_router
from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import close_db_connection
from app.core.nacos_client import start_nacos, stop_nacos
import logging
from contextlib import asynccontextmanager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 定义生命周期上下文管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting app, initializing resources...")
    await start_nacos()
    yield
    logger.info("Shutting down app, releasing resources...")
    await stop_nacos()
    await close_db_connection()
    logger.info("Database connection pool closed")

app = FastAPI(
    title="Readify AGI",
    description="Readify AGI 项目的 API 服务",
    version="1.0.0",
    lifespan=lifespan
)

# 请求日志中间件
@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    logger.debug(f"收到请求: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 基础路由
@app.get("/")
async def root():
    return {"message": "Welcome to Readify AGI!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# API路由
app.include_router(file_router.router, prefix="/api/v1", tags=["files"])
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on port %s...", settings.SERVICE_PORT)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        log_level="info"
    )  
