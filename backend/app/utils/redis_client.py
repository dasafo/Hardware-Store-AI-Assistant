#!/usr/bin/env python3

import os
import json
import redis
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import hashlib
from app.utils.logger import logger, log_with_context

class RedisClient:
    """Redis client for caching embeddings and search results"""
    
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "redis")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD") or None
        self._client = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """Establish connection to Redis server."""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test the connection
            self._client.ping()
            self.connected = True
            log_with_context(
                logger,
                "info",
                "Redis connection established successfully"
            )
        except redis.ConnectionError as e:
            self.connected = False
            log_with_context(
                logger,
                "warning",
                "Redis connection failed - caching disabled",
                error=str(e)
            )
        except Exception as e:
            self.connected = False
            log_with_context(
                logger,
                "error",
                "Unexpected error connecting to Redis",
                error=str(e)
            )
    
    def is_connected(self) -> bool:
        """Check if Redis is connected and available."""
        if not self.connected:
            return False
        
        try:
            self._client.ping()
            return True
        except:
            self.connected = False
            log_with_context(
                logger,
                "warning",
                "Redis connection lost - caching disabled"
            )
            return False
    
    def _safe_execute(self, operation_name: str, func, *args, **kwargs):
        """Safely execute Redis operations with error handling."""
        if not self.is_connected():
            return None
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            log_with_context(
                logger,
                "error",
                f"Redis {operation_name} operation failed",
                error=str(e)
            )
            return None
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create a consistent cache key"""
        # Hash long identifiers to keep keys manageable
        if len(identifier) > 100:
            identifier = hashlib.md5(identifier.encode()).hexdigest()
        return f"hsai:{prefix}:{identifier}"
    
    # ═══════════════════════════════════════════════════════
    # EMBEDDING CACHE
    # ═══════════════════════════════════════════════════════
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text"""
        def _get():
            key = self._make_key("embedding", text)
            cached = self._client.get(key)
            if cached:
                return json.loads(cached)
            return None
        
        result = self._safe_execute("get_embedding", _get)
        if result:
            log_with_context(
                logger,
                "debug",
                "Embedding cache hit",
                text_length=len(text)
            )
        return result
    
    def set_embedding(self, text: str, embedding: List[float], ttl: int = 3600) -> bool:
        """Cache embedding for text with TTL (default 1 hour)"""
        def _set():
            key = self._make_key("embedding", text)
            value = json.dumps(embedding)
            return self._client.setex(key, ttl, value)
        
        result = self._safe_execute("set_embedding", _set)
        if result:
            log_with_context(
                logger,
                "debug",
                "Embedding cached",
                text_length=len(text),
                ttl=ttl
            )
        return result
    
    # ═══════════════════════════════════════════════════════
    # SEARCH RESULTS CACHE
    # ═══════════════════════════════════════════════════════
    
    def get_search_results(self, query: str, top_k: int = 5) -> Optional[List[Dict]]:
        """Get cached search results"""
        def _get():
            cache_key = f"{query}::{top_k}"
            key = self._make_key("search", cache_key)
            cached = self._client.get(key)
            if cached:
                return json.loads(cached)
            return None
        
        result = self._safe_execute("get_search_results", _get)
        if result:
            log_with_context(
                logger,
                "debug",
                "Search results cache hit",
                query=query,
                top_k=top_k,
                results_count=len(result)
            )
        return result
    
    def set_search_results(self, query: str, results: List[Dict], top_k: int = 5, ttl: int = 1800) -> bool:
        """Cache search results with TTL (default 30 minutes)"""
        def _set():
            cache_key = f"{query}::{top_k}"
            key = self._make_key("search", cache_key)
            value = json.dumps(results)
            return self._client.setex(key, ttl, value)
        
        result = self._safe_execute("set_search_results", _set)
        if result:
            log_with_context(
                logger,
                "debug",
                "Search results cached",
                query=query,
                top_k=top_k,
                results_count=len(results),
                ttl=ttl
            )
        return result
    
    # ═══════════════════════════════════════════════════════
    # VECTOR SEARCH CACHE (SKUs)
    # ═══════════════════════════════════════════════════════
    
    def get_vector_skus(self, embedding_hash: str, top_k: int = 5) -> Optional[List[str]]:
        """Get cached SKUs from vector search"""
        def _get():
            cache_key = f"{embedding_hash}::{top_k}"
            key = self._make_key("vector", cache_key)
            cached = self._client.get(key)
            if cached:
                return json.loads(cached)
            return None
        
        result = self._safe_execute("get_vector_skus", _get)
        if result:
            log_with_context(
                logger,
                "debug",
                "Vector search cache hit",
                embedding_hash=embedding_hash,
                top_k=top_k,
                results_count=len(result)
            )
        return result
    
    def set_vector_skus(self, embedding_hash: str, skus: List[str], top_k: int = 5, ttl: int = 900) -> bool:
        """Cache SKUs from vector search with TTL (default 15 minutes)"""
        def _set():
            cache_key = f"{embedding_hash}::{top_k}"
            key = self._make_key("vector", cache_key)
            value = json.dumps(skus)
            return self._client.setex(key, ttl, value)
        
        result = self._safe_execute("set_vector_skus", _set)
        if result:
            log_with_context(
                logger,
                "debug",
                "Vector search results cached",
                embedding_hash=embedding_hash,
                top_k=top_k,
                results_count=len(skus),
                ttl=ttl
            )
        return result
    
    # ═══════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════
    
    def hash_embedding(self, embedding: List[float]) -> str:
        """Create a hash from embedding for caching vector results"""
        # Convert to string and hash for consistent keys
        embedding_str = json.dumps(embedding, sort_keys=True)
        return hashlib.md5(embedding_str.encode()).hexdigest()
    
    def clear_cache(self, pattern: str = None) -> int:
        """Clear cache keys matching pattern"""
        def _clear():
            if pattern:
                keys = self._client.keys(f"hsai:{pattern}:*")
            else:
                keys = self._client.keys("hsai:*")
            
            if keys:
                return self._client.delete(*keys)
            return 0
        
        result = self._safe_execute("clear_cache", _clear)
        return result
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        def _get_stats():
            info = self._client.info()
            embedding_keys = len(self._client.keys("hsai:embedding:*"))
            search_keys = len(self._client.keys("hsai:search:*"))
            vector_keys = len(self._client.keys("hsai:vector:*"))
            
            return {
                "connected": True,
                "total_keys": info.get("db0", {}).get("keys", 0) if "db0" in info else 0,
                "embedding_cache_keys": embedding_keys,
                "search_cache_keys": search_keys,
                "vector_cache_keys": vector_keys,
                "memory_usage": info.get("used_memory_human", "unknown"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
            }
        
        result = self._safe_execute("get_cache_stats", _get_stats)
        return result

# Global Redis client instance
redis_client = RedisClient() 