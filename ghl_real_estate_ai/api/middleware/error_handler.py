"""
Error Handling Middleware for GHL Real Estate AI.

Standardizes error responses and logs exceptions.
"""

import time
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catch exceptions and return standardized JSON responses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            
            # Log slow requests
            process_time = time.time() - start_time
            if process_time > 2.0:
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "duration": process_time
                    }
                )
                
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Unhandled exception during {request.method} {request.url.path}: {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration": process_time,
                    "exception": str(e),
                    "traceback": traceback.format_exc()
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": "Internal Server Error",
                    "detail": str(e) if request.app.debug else "An unexpected error occurred. Please contact support.",
                    "request_id": request.headers.get("X-Request-ID")
                }
            )
