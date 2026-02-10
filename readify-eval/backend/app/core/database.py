"""
Database configuration and session management
"""
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# Base class for all models
Base = declarative_base()

# Determine if we're using async database
is_async_db = settings.database.url.startswith(('postgresql+asyncpg://', 'mysql+aiomysql://'))


if is_async_db:
    # Async engine for PostgreSQL or MySQL with async drivers
    engine = create_async_engine(
        settings.database.url,
        echo=settings.database.echo,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_pre_ping=settings.database.pool_pre_ping,
    )
    
    # Async session factory
    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        """
        Dependency for getting async database session
        
        Yields:
            AsyncSession: Database session
        """
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def init_db() -> None:
        """Initialize database tables"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close_db() -> None:
        """Close database connection"""
        await engine.dispose()

else:
    # Sync engine for SQLite or other sync databases
    engine = create_engine(
        settings.database.url,
        echo=settings.database.echo,
        pool_pre_ping=settings.database.pool_pre_ping,
        connect_args={"check_same_thread": False} if settings.database.url.startswith("sqlite") else {},
    )
    
    # Sync session factory
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    
    def get_db() -> Generator[Session, None, None]:
        """
        Dependency for getting sync database session
        
        Yields:
            Session: Database session
        """
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    
    def init_db() -> None:
        """Initialize database tables"""
        Base.metadata.create_all(bind=engine)
    
    def close_db() -> None:
        """Close database connection"""
        engine.dispose()

