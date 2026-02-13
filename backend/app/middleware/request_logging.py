"""
Request logging middleware for FastAPI.

Automatically logs all incoming requests and outgoing responses,
generates unique request IDs, and tracks request duration.
"""

import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.monitoring.context import set_request_id

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all HTTP requests and responses.
    
    For each request, this middleware:
    1. Generates a unique request_id
    2. Sets the request_id in context (available to all async code)
    3. Logs the incoming request
    4. Times the request execution
    5. Logs the response with status code and duration
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and response.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            The HTTP response
        """
        # Generate unique request ID (8-character UUID)
        request_id = str(uuid.uuid4())[:8]
        
        # Set request_id in context (propagates through async calls)
        set_request_id(request_id)
        
        # Start timing
        start = time.perf_counter()
        
        # Log incoming request
        logger.info(
            "request_start",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            
            # Log successful response
            logger.info(
                "request_complete",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2)
                }
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            
            # Log failed request
            logger.error(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e)
                }
            )
            
            # Re-raise the exception to be handled by FastAPI
            raise
