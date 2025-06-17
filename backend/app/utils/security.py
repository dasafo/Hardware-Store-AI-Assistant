# utils/security.py

import os
import time
import hashlib
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from threading import Lock
from fastapi import Header, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from app.utils.logger import logger, log_with_context

# ═══════════════════════════════════════════════════════
# API KEY AUTHENTICATION
# ═══════════════════════════════════════════════════════

# Load API keys from environment variables
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "hsai-admin-key-change-me")
USER_API_KEY = os.getenv("USER_API_KEY", "hsai-user-key-change-me")

# Security headers
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class APIKeyAuth:
    """API Key authentication handler"""
    
    def __init__(self):
        self.admin_keys = set()
        self.user_keys = set()
        self._load_api_keys()
    
    def _load_api_keys(self):
        """Load API keys from environment variables"""
        # Admin keys (comma-separated)
        admin_keys_env = os.getenv("ADMIN_API_KEYS", ADMIN_API_KEY)
        self.admin_keys = {key.strip() for key in admin_keys_env.split(",") if key.strip()}
        
        # User keys (comma-separated)
        user_keys_env = os.getenv("USER_API_KEYS", USER_API_KEY)
        self.user_keys = {key.strip() for key in user_keys_env.split(",") if key.strip()}
        
        log_with_context(
            logger,
            "info",
            "API keys loaded",
            admin_keys_count=len(self.admin_keys),
            user_keys_count=len(self.user_keys)
        )
    
    def verify_admin_key(self, api_key: str) -> bool:
        """Verify admin API key"""
        return api_key in self.admin_keys
    
    def verify_user_key(self, api_key: str) -> bool:
        """Verify user API key (includes admin keys)"""
        return api_key in self.user_keys or api_key in self.admin_keys
    
    def get_key_type(self, api_key: str) -> Optional[str]:
        """Get the type of API key"""
        if api_key in self.admin_keys:
            return "admin"
        elif api_key in self.user_keys:
            return "user"
        return None

# Global API key auth instance
api_auth = APIKeyAuth()

# ═══════════════════════════════════════════════════════
# RATE LIMITING
# ═══════════════════════════════════════════════════════

class RateLimiter:
    """In-memory rate limiter with sliding window"""
    
    def __init__(self):
        self._requests = defaultdict(lambda: deque())
        self._lock = Lock()
        
        # Rate limits from environment variables
        self.default_requests_per_minute = int(os.getenv("RATE_LIMIT_DEFAULT", "60"))
        self.admin_requests_per_minute = int(os.getenv("RATE_LIMIT_ADMIN", "300"))
        self.user_requests_per_minute = int(os.getenv("RATE_LIMIT_USER", "120"))
        
        log_with_context(
            logger,
            "info",
            "Rate limiter initialized",
            default_rpm=self.default_requests_per_minute,
            admin_rpm=self.admin_requests_per_minute,
            user_rpm=self.user_requests_per_minute
        )
    
    def _get_rate_limit(self, key_type: Optional[str]) -> int:
        """Get rate limit based on key type"""
        if key_type == "admin":
            return self.admin_requests_per_minute
        elif key_type == "user":
            return self.user_requests_per_minute
        else:
            return self.default_requests_per_minute
    
    def is_allowed(self, identifier: str, key_type: Optional[str] = None) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed under rate limit
        
        Args:
            identifier: IP address or user identifier
            key_type: Type of API key (admin, user, or None)
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        rate_limit = self._get_rate_limit(key_type)
        
        with self._lock:
            # Clean old requests outside the window
            requests_queue = self._requests[identifier]
            while requests_queue and requests_queue[0] < window_start:
                requests_queue.popleft()
            
            # Check if under limit
            current_requests = len(requests_queue)
            
            if current_requests >= rate_limit:
                # Rate limit exceeded
                oldest_request = requests_queue[0] if requests_queue else current_time
                reset_time = int(oldest_request + 60)
                
                return False, {
                    "limit": rate_limit,
                    "remaining": 0,
                    "reset": reset_time,
                    "current": current_requests
                }
            
            # Allow request and record it
            requests_queue.append(current_time)
            remaining = rate_limit - current_requests - 1
            
            return True, {
                "limit": rate_limit,
                "remaining": remaining,
                "reset": int(current_time + 60),
                "current": current_requests + 1
            }
    
    def get_stats(self) -> Dict[str, int]:
        """Get rate limiter statistics"""
        with self._lock:
            current_time = time.time()
            window_start = current_time - 60
            
            active_ips = 0
            total_requests = 0
            
            for ip, requests_queue in self._requests.items():
                # Clean old requests
                while requests_queue and requests_queue[0] < window_start:
                    requests_queue.popleft()
                
                if requests_queue:
                    active_ips += 1
                    total_requests += len(requests_queue)
            
            return {
                "active_ips": active_ips,
                "total_requests_last_minute": total_requests,
                "tracked_ips": len(self._requests)
            }

# Global rate limiter instance
rate_limiter = RateLimiter()

# ═══════════════════════════════════════════════════════
# DEPENDENCY FUNCTIONS
# ═══════════════════════════════════════════════════════

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers (behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"

def check_rate_limit(request: Request, key_type: Optional[str] = None):
    """Check rate limit for request"""
    client_ip = get_client_ip(request)
    
    is_allowed, rate_info = rate_limiter.is_allowed(client_ip, key_type)
    
    if not is_allowed:
        log_with_context(
            logger,
            "warning",
            "Rate limit exceeded",
            client_ip=client_ip,
            key_type=key_type or "anonymous",
            limit=rate_info["limit"],
            current=rate_info["current"]
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "limit": rate_info["limit"],
                "remaining": rate_info["remaining"],
                "reset": rate_info["reset"],
                "retry_after": rate_info["reset"] - int(time.time())
            },
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset"]),
                "Retry-After": str(rate_info["reset"] - int(time.time()))
            }
        )
    
    # Add rate limit headers to successful requests
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(rate_info["limit"]),
        "X-RateLimit-Remaining": str(rate_info["remaining"]),
        "X-RateLimit-Reset": str(rate_info["reset"])
    }

def require_api_key(request: Request, api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Require valid API key (admin or user)"""
    if not api_key:
        log_with_context(
            logger,
            "warning",
            "Missing API key",
            client_ip=get_client_ip(request),
            path=request.url.path
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    key_type = api_auth.get_key_type(api_key)
    if not key_type:
        log_with_context(
            logger,
            "warning",
            "Invalid API key",
            client_ip=get_client_ip(request),
            path=request.url.path,
            api_key_preview=api_key[:8] + "..." if len(api_key) > 8 else api_key
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Check rate limit based on key type
    check_rate_limit(request, key_type)
    
    log_with_context(
        logger,
        "info",
        "API key authenticated",
        client_ip=get_client_ip(request),
        key_type=key_type,
        path=request.url.path
    )
    
    # Store key type in request state
    request.state.api_key_type = key_type
    return {"key_type": key_type, "api_key": api_key}

def require_admin_key(request: Request, api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Require admin API key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if not api_auth.verify_admin_key(api_key):
        log_with_context(
            logger,
            "warning",
            "Invalid admin API key attempt",
            client_ip=get_client_ip(request),
            path=request.url.path,
            api_key_preview=api_key[:8] + "..." if len(api_key) > 8 else api_key
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    # Check rate limit for admin
    check_rate_limit(request, "admin")
    
    log_with_context(
        logger,
        "info",
        "Admin API key authenticated",
        client_ip=get_client_ip(request),
        path=request.url.path
    )
    
    request.state.api_key_type = "admin"
    return {"key_type": "admin", "api_key": api_key}

def check_public_rate_limit(request: Request):
    """Check rate limit for public endpoints (no API key required)"""
    check_rate_limit(request, None)

# ═══════════════════════════════════════════════════════
# LEGACY COMPATIBILITY
# ═══════════════════════════════════════════════════════

def admin_guard(x_api_key: str = Header(...)):
    """Legacy admin guard for backward compatibility"""
    if not api_auth.verify_admin_key(x_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return True 