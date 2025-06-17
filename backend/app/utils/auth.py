# utils/auth.py
"""
Authentication utilities for the Hardware Store AI Assistant.
Legacy compatibility module that imports from the new security system.
"""

import os
from fastapi import HTTPException, Header
from typing import Optional

# Import from new security system for backward compatibility
from app.utils.security import (
    api_auth,
    require_admin_key as new_require_admin_key,
    require_api_key as new_require_api_key,
    APIKeyAuth,
    get_client_ip
)
from app.utils.logger import logger, log_with_context

# Legacy API key (deprecated, use environment variables instead)
API_KEY = os.getenv("ADMIN_API_KEYS", "super-secret-admin").split(",")[0]

def admin_guard(x_api_key: Optional[str] = Header(None)):
    """
    Legacy admin guard function for backward compatibility.
    
    DEPRECATED: Use require_admin_key from app.utils.security instead.
    This function is maintained for backward compatibility only.
    """
    log_with_context(
        logger,
        "warning",
        "Using deprecated admin_guard function",
        function="admin_guard",
        recommendation="Use require_admin_key from app.utils.security"
    )
    
    if not x_api_key:
        log_with_context(
            logger,
            "warning",
            "Admin access denied - no API key provided",
            function="admin_guard"
        )
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide X-API-Key header."
        )
    
    # Check if it's a valid admin key using the new system
    if api_auth.is_admin_key(x_api_key):
        log_with_context(
            logger,
            "info",
            "Admin access granted via legacy function",
            function="admin_guard",
            key_type="admin"
        )
        return True
    
    # Check legacy API key for backward compatibility
    if x_api_key == API_KEY:
        log_with_context(
            logger,
            "warning",
            "Admin access granted via legacy API key",
            function="admin_guard",
            recommendation="Update to use new API key system"
        )
        return True
    
    log_with_context(
        logger,
        "warning",
        "Admin access denied - invalid API key",
        function="admin_guard"
    )
    raise HTTPException(
        status_code=403,
        detail="Invalid API key"
    )

# Export new functions for easy migration
require_admin_key = new_require_admin_key
require_api_key = new_require_api_key

# Legacy exports for backward compatibility
__all__ = [
    "API_KEY",
    "admin_guard",
    "require_admin_key", 
    "require_api_key",
    "api_auth",
    "get_client_ip"
]
