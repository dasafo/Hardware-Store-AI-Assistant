#!/usr/bin/env python3

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel
from app.utils.redis_client import redis_client
from app.utils.auth import admin_guard

router = APIRouter(tags=["cache"])

class CacheStatsResponse(BaseModel):
    connected: bool
    total_keys: int = 0
    embedding_cache_keys: int = 0
    search_cache_keys: int = 0
    vector_cache_keys: int = 0
    memory_usage: str = "unknown"
    hits: int = 0
    misses: int = 0
    error: str = None

class CacheClearResponse(BaseModel):
    success: bool
    keys_deleted: int
    message: str

@router.get("/cache/stats", response_model=CacheStatsResponse)
def get_cache_stats():
    """
    Get Redis cache statistics and health status.
    
    Returns comprehensive information about cache usage, hit/miss ratios,
    and memory consumption.
    """
    try:
        stats = redis_client.get_cache_stats()
        return CacheStatsResponse(**stats)
    except Exception as e:
        return CacheStatsResponse(
            connected=False,
            error=str(e)
        )

@router.delete("/cache/clear", response_model=CacheClearResponse)
def clear_cache(
    pattern: str = None,
    user=Depends(admin_guard)  # ⬅️ Requires admin authentication
):
    """
    Clear cache entries (Admin only).
    
    - **pattern**: Optional pattern to match cache keys (e.g., 'embedding', 'search', 'vector')
    - If no pattern provided, clears ALL cache entries
    
    Examples:
    - Clear all: DELETE /cache/clear
    - Clear embeddings: DELETE /cache/clear?pattern=embedding
    - Clear searches: DELETE /cache/clear?pattern=search
    """
    try:
        if not redis_client.is_connected():
            raise HTTPException(
                status_code=503,
                detail="Redis is not connected"
            )
        
        keys_deleted = redis_client.clear_cache(pattern)
        
        if pattern:
            message = f"Cleared {keys_deleted} cache entries matching pattern '{pattern}'"
        else:
            message = f"Cleared all {keys_deleted} cache entries"
        
        return CacheClearResponse(
            success=True,
            keys_deleted=keys_deleted,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )

@router.get("/cache/health")
def cache_health():
    """
    Simple health check for Redis connection.
    """
    is_connected = redis_client.is_connected()
    
    if is_connected:
        return {
            "status": "healthy",
            "redis_connected": True,
            "message": "Cache is operational"
        }
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy", 
                "redis_connected": False,
                "message": "Redis is not accessible"
            }
        ) 