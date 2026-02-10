"""
Simple script to run the FastAPI application
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.service.port,
        reload=settings.app.debug,
        log_level=settings.logging.level.lower()
    )

