from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import AsyncGenerator
from .config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 连接前进行ping检测
    pool_recycle=1800,   # 半小时回收一次连接
    pool_size=20,        # 连接池大小
    max_overflow=10,     # 最大溢出连接数
    echo=False,          # 生产环境不记录每个SQL日志
    future=True          # 使用SQLAlchemy 2.0风格
)

# 创建异步会话工厂
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False      # 防止自动刷新导致的额外查询
)

# 创建基类
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# 优雅关闭数据库连接池的函数
async def close_db_connection():
    """关闭数据库连接池"""
    await engine.dispose() 