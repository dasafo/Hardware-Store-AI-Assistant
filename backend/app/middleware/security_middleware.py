# middleware/security_middleware.py

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from app.utils.security import check_public_rate_limit, get_client_ip
from app.utils.logger import logger, log_with_context

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware that applies:
    - Rate limiting for public endpoints
    - Security headers
    - Request validation
    """
    
    def __init__(self, app, enable_rate_limiting: bool = True):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        
        # Security headers to add to all responses
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        # Endpoints that should skip rate limiting (already protected by API keys)
        self.skip_rate_limiting = {
            "/cache/clear",
            "/reindex",
            "/metrics/reset"
        }
        
        log_with_context(
            logger,
            "info",
            "Security middleware initialized",
            rate_limiting_enabled=self.enable_rate_limiting,
            skip_rate_limiting_paths=len(self.skip_rate_limiting)
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = get_client_ip(request)
        path = request.url.path
        method = request.method
        
        # Skip rate limiting for certain endpoints or if disabled
        should_rate_limit = (
            self.enable_rate_limiting and 
            path not in self.skip_rate_limiting and
            not path.startswith("/health") and  # Health checks are exempt
            not path.startswith("/docs") and    # API docs are exempt
            not path.startswith("/openapi.json") and
            not path.startswith("/redoc")
        )
        
        try:
            # Apply rate limiting for public endpoints
            if should_rate_limit:
                # This will raise HTTPException if rate limit is exceeded
                check_public_rate_limit(request)
            
            # Process the request
            response = await call_next(request)
            
            # Add security headers
            for header_name, header_value in self.security_headers.items():
                response.headers[header_name] = header_value
            
            # Add rate limit headers if they were set during processing
            if hasattr(request.state, 'rate_limit_headers'):
                for header_name, header_value in request.state.rate_limit_headers.items():
                    response.headers[header_name] = header_value
            
            # Add security-related custom headers
            response.headers["X-Security-Middleware"] = "active"
            
            process_time = time.time() - start_time
            
            # Log successful security check
            log_with_context(
                logger,
                "debug",
                "Security middleware processed request",
                client_ip=client_ip,
                method=method,
                path=path,
                rate_limited=should_rate_limit,
                process_time_ms=round(process_time * 1000, 2)
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log security-related errors
            if "Rate limit exceeded" in str(e):
                log_with_context(
                    logger,
                    "warning",
                    "Request blocked by rate limiter",
                    client_ip=client_ip,
                    method=method,
                    path=path,
                    error=str(e),
                    process_time_ms=round(process_time * 1000, 2)
                )
            else:
                log_with_context(
                    logger,
                    "error",
                    "Security middleware error",
                    client_ip=client_ip,
                    method=method,
                    path=path,
                    error=str(e),
                    process_time_ms=round(process_time * 1000, 2)
                )
            
            # Re-raise the exception to be handled by FastAPI
            raise 