"""
Logging middleware for request/response tracking
"""
import time
import logging
import json
from typing import Callable, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log incoming requests and outgoing responses with body content
    """
    
    # 配置项
    MAX_BODY_LOG_SIZE = 10000  # 最大记录的body大小（字符）
    SENSITIVE_FIELDS = {"password", "token", "secret", "api_key", "apiKey"}  # 敏感字段
    SKIP_PATHS = {"/docs", "/redoc", "/openapi.json", "/favicon.ico"}  # 跳过的路径
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log relevant information including body
        """
        # Skip logging for certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Get request details
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # Read and log request body
        request_body = await self._get_request_body(request)
        
        # Log incoming request with body
        log_message = f"[{method}] {url} - Client: {client_host}"
        if request_body:
            log_message += f"\nRequest Body: {request_body}"
        logger.info(log_message)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Read response body and get new response object
            response, response_body = await self._get_response_body(response)
            
            # Log response with body
            response_log = (
                f"[{method}] {url} - Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            if response_body:
                response_log += f"\nResponse Body: {response_body}"
            logger.info(response_log)
            
            # Add processing time to response headers
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"[{method}] {url} - Error: {str(e)} - "
                f"Time: {process_time:.3f}s",
                exc_info=True
            )
            
            # Re-raise the exception to be handled by FastAPI
            raise
    
    async def _get_request_body(self, request: Request) -> str:
        """
        Read and return request body, handling different content types
        """
        try:
            content_type = request.headers.get("content-type", "")
            
            # Skip for multipart/form-data (file uploads)
            if "multipart/form-data" in content_type:
                return "[File Upload - Content Not Logged]"
            
            # Read body
            body = await request.body()
            
            if not body:
                return ""
            
            # Try to decode as JSON
            try:
                body_str = body.decode("utf-8")
                
                # If it's JSON, parse and mask sensitive fields
                if "application/json" in content_type:
                    try:
                        body_json = json.loads(body_str)
                        body_json = self._mask_sensitive_data(body_json)
                        body_str = json.dumps(body_json, ensure_ascii=False, indent=2)
                    except json.JSONDecodeError:
                        pass
                
                # Truncate if too long
                if len(body_str) > self.MAX_BODY_LOG_SIZE:
                    body_str = body_str[:self.MAX_BODY_LOG_SIZE] + "... [truncated]"
                
                return body_str
                
            except UnicodeDecodeError:
                return f"[Binary Content - {len(body)} bytes]"
                
        except Exception as e:
            logger.debug(f"Failed to read request body: {e}")
            return "[Error reading body]"
    
    async def _get_response_body(self, response: Response) -> Tuple[Response, str]:
        """
        Read and return response body along with a new response object
        """
        try:
            # Only log JSON responses
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                return response, "[Non-JSON Response - Content Not Logged]"
            
            # Read response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            if not response_body:
                # Create new response with empty body
                new_response = Response(
                    content=b"",
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
                return new_response, ""
            
            try:
                body_str = response_body.decode("utf-8")
                
                # Try to parse and format JSON
                try:
                    body_json = json.loads(body_str)
                    masked_body_json = self._mask_sensitive_data(body_json)
                    body_str_for_log = json.dumps(masked_body_json, ensure_ascii=False, indent=2)
                except json.JSONDecodeError:
                    body_str_for_log = body_str
                
                # Truncate if too long (for logging only)
                if len(body_str_for_log) > self.MAX_BODY_LOG_SIZE:
                    body_str_for_log = body_str_for_log[:self.MAX_BODY_LOG_SIZE] + "... [truncated]"
                
                # Create new response with the same body (original, not masked)
                new_response = Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
                
                return new_response, body_str_for_log
                
            except UnicodeDecodeError:
                new_response = Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
                return new_response, f"[Binary Content - {len(response_body)} bytes]"
                
        except Exception as e:
            logger.debug(f"Failed to read response body: {e}")
            return response, "[Error reading response body]"
    
    def _mask_sensitive_data(self, data):
        """
        Recursively mask sensitive fields in dictionaries
        """
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    masked_data[key] = "***MASKED***"
                elif isinstance(value, (dict, list)):
                    masked_data[key] = self._mask_sensitive_data(value)
                else:
                    masked_data[key] = value
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data

