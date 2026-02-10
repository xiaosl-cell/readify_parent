"""
Health check endpoints
"""
from fastapi import APIRouter
from datetime import datetime

from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Health check endpoint
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "app_name": settings.app.name,
        "version": settings.app.version,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/")
def root():
    """
    Root endpoint
    
    Returns:
        API information
    """
    return {
        "app_name": settings.app.name,
        "version": settings.app.version,
        "description": settings.app.description,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

