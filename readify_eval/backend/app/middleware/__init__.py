"""
Middleware package
"""
from app.middleware.logging import RequestLoggingMiddleware

__all__ = ["RequestLoggingMiddleware"]

