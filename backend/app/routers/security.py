# routers/security.py

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.utils.security import (
    require_admin_key, 
    require_api_key, 
    rate_limiter, 
    api_auth,
    get_client_ip
)
from app.utils.logger import logger, log_with_context

router = APIRouter(tags=["security"])

# ═══════════════════════════════════════════════════════
# RESPONSE MODELS
# ═══════════════════════════════════════════════════════

class RateLimitStats(BaseModel):
    active_ips: int
    total_requests_last_minute: int
    tracked_ips: int
    limits: Dict[str, int]

class SecurityInfo(BaseModel):
    rate_limiting_enabled: bool
    api_key_auth_enabled: bool
    admin_keys_count: int
    user_keys_count: int
    rate_limits: Dict[str, int]
    security_headers_enabled: bool

class APIKeyValidation(BaseModel):
    valid: bool
    key_type: Optional[str]
    message: str

class RateLimitCheck(BaseModel):
    allowed: bool
    limit: int
    remaining: int
    reset: int
    client_ip: str

# ═══════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════

@router.get("/security/info", response_model=SecurityInfo)
def get_security_info():
    """
    Get general security configuration information.
    Public endpoint that shows security features without sensitive details.
    """
    log_with_context(
        logger,
        "info",
        "Security info requested"
    )
    
    return SecurityInfo(
        rate_limiting_enabled=True,
        api_key_auth_enabled=True,
        admin_keys_count=len(api_auth.admin_keys),
        user_keys_count=len(api_auth.user_keys),
        rate_limits={
            "default": rate_limiter.default_requests_per_minute,
            "user": rate_limiter.user_requests_per_minute,
            "admin": rate_limiter.admin_requests_per_minute
        },
        security_headers_enabled=True
    )

@router.get("/security/rate-limit/stats", response_model=RateLimitStats)
def get_rate_limit_stats(request: Request, auth=Depends(require_admin_key)):
    """
    Get rate limiting statistics (Admin only).
    Shows current rate limiting activity and configuration.
    """
    log_with_context(
        logger,
        "info",
        "Rate limit stats requested",
        client_ip=get_client_ip(request),
        admin_key_type=auth["key_type"]
    )
    
    stats = rate_limiter.get_stats()
    
    return RateLimitStats(
        active_ips=stats["active_ips"],
        total_requests_last_minute=stats["total_requests_last_minute"],
        tracked_ips=stats["tracked_ips"],
        limits={
            "default": rate_limiter.default_requests_per_minute,
            "user": rate_limiter.user_requests_per_minute,
            "admin": rate_limiter.admin_requests_per_minute
        }
    )

@router.get("/security/rate-limit/check", response_model=RateLimitCheck)
def check_rate_limit_status(request: Request):
    """
    Check current rate limit status for the requesting IP.
    Public endpoint to help clients understand their rate limit status.
    """
    client_ip = get_client_ip(request)
    
    # Get current rate limit status without incrementing
    is_allowed, rate_info = rate_limiter.is_allowed(client_ip, None)
    
    # We need to "undo" the increment that was done by is_allowed
    # This is a bit hacky but necessary for a check endpoint
    if is_allowed and client_ip in rate_limiter._requests:
        with rate_limiter._lock:
            if rate_limiter._requests[client_ip]:
                rate_limiter._requests[client_ip].pop()  # Remove the request we just added
                rate_info["remaining"] += 1
                rate_info["current"] -= 1
    
    log_with_context(
        logger,
        "info",
        "Rate limit status checked",
        client_ip=client_ip,
        allowed=is_allowed,
        remaining=rate_info["remaining"]
    )
    
    return RateLimitCheck(
        allowed=is_allowed,
        limit=rate_info["limit"],
        remaining=rate_info["remaining"],
        reset=rate_info["reset"],
        client_ip=client_ip
    )

@router.post("/security/api-key/validate", response_model=APIKeyValidation)
def validate_api_key(request: Request, auth=Depends(require_api_key)):
    """
    Validate an API key and return its type.
    Requires a valid API key to use.
    """
    log_with_context(
        logger,
        "info",
        "API key validation requested",
        client_ip=get_client_ip(request),
        key_type=auth["key_type"]
    )
    
    return APIKeyValidation(
        valid=True,
        key_type=auth["key_type"],
        message=f"Valid {auth['key_type']} API key"
    )

@router.post("/security/rate-limit/reset")
def reset_rate_limits(request: Request, auth=Depends(require_admin_key)):
    """
    Reset all rate limiting data (Admin only).
    Clears all tracked IP addresses and their request counts.
    """
    log_with_context(
        logger,
        "warning",
        "Rate limit reset requested",
        client_ip=get_client_ip(request),
        admin_key_type=auth["key_type"]
    )
    
    # Clear all rate limiting data
    with rate_limiter._lock:
        cleared_ips = len(rate_limiter._requests)
        rate_limiter._requests.clear()
    
    log_with_context(
        logger,
        "info",
        "Rate limits reset successfully",
        cleared_ips=cleared_ips,
        admin_ip=get_client_ip(request)
    )
    
    return {
        "status": "success",
        "message": f"Rate limits reset for {cleared_ips} IP addresses",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@router.get("/security/headers/test")
def test_security_headers(request: Request):
    """
    Test endpoint to verify security headers are being applied.
    Returns information about the request and expected security headers.
    """
    client_ip = get_client_ip(request)
    
    log_with_context(
        logger,
        "info",
        "Security headers test requested",
        client_ip=client_ip
    )
    
    return {
        "message": "Security headers test endpoint",
        "client_ip": client_ip,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "expected_headers": [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Referrer-Policy",
            "Content-Security-Policy",
            "Permissions-Policy",
            "X-Security-Middleware",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ],
        "note": "Check response headers to verify security middleware is working"
    }

@router.get("/security/audit")
def security_audit(request: Request, auth=Depends(require_admin_key)):
    """
    Security audit endpoint (Admin only).
    Provides comprehensive security status and recommendations.
    """
    log_with_context(
        logger,
        "info",
        "Security audit requested",
        client_ip=get_client_ip(request),
        admin_key_type=auth["key_type"]
    )
    
    rate_stats = rate_limiter.get_stats()
    
    # Basic security checks
    audit_results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "security_features": {
            "rate_limiting": {
                "enabled": True,
                "status": "active",
                "active_ips": rate_stats["active_ips"],
                "total_requests": rate_stats["total_requests_last_minute"]
            },
            "api_key_auth": {
                "enabled": True,
                "admin_keys": len(api_auth.admin_keys),
                "user_keys": len(api_auth.user_keys)
            },
            "security_headers": {
                "enabled": True,
                "status": "active"
            },
            "logging": {
                "enabled": True,
                "structured": True
            }
        },
        "recommendations": [
            "Ensure API keys are rotated regularly",
            "Monitor rate limiting logs for abuse patterns",
            "Review security headers periodically",
            "Consider implementing IP whitelisting for admin endpoints",
            "Set up automated security monitoring alerts"
        ]
    }
    
    log_with_context(
        logger,
        "info",
        "Security audit completed",
        admin_ip=get_client_ip(request),
        features_checked=len(audit_results["security_features"])
    )
    
    return audit_results 