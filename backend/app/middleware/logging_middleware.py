import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from app.utils.logger import logger, log_with_context
from app.utils.metrics import metrics

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic logging of HTTP requests and responses.
    Also collects performance metrics for monitoring.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extract request information
        method = request.method
        url = str(request.url)
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Add request ID to request state for downstream use
        request.state.request_id = request_id
        
        # Log incoming request
        log_with_context(
            logger,
            "info",
            "Incoming request",
            request_id=request_id,
            method=method,
            path=path,
            url=url,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        # Process request and handle any errors
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Record metrics
            metrics.record_request(method, path, process_time, response.status_code)
            
            # Log successful response
            log_with_context(
                logger,
                "info",
                "Request completed",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2)
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            
            return response
            
        except Exception as e:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time
            
            # Record error metrics (assuming 500 status for unhandled exceptions)
            metrics.record_request(method, path, process_time, 500)
            
            # Log error
            log_with_context(
                logger,
                "error",
                "Request failed with unhandled exception",
                request_id=request_id,
                method=method,
                path=path,
                error=str(e),
                error_type=type(e).__name__,
                process_time_ms=round(process_time * 1000, 2)
            )
            
            # Re-raise the exception to be handled by FastAPI's exception handlers
            raise 