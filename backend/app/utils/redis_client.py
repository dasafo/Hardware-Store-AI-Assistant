#!/usr/bin/env python3

import os
import json
import redis
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import hashlib

class RedisClient:
    """Redis client for caching embeddings and search results"""
    
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "redis")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD") or None
        self._client = None
    
    @property
    def client(self):
        """Lazy connection to Redis"""
        if self._client is None:
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
        return self._client
    
    def is_connected(self) -> bool:
        """Check if Redis is connected and responding"""
        try:
            return self.client.ping()
        except:
            return False
    
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
        try:
            key = self._make_key("embedding", text)
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            print(f"Redis get_embedding error: {e}")
            return None
    
    def set_embedding(self, text: str, embedding: List[float], ttl: int = 3600) -> bool:
        """Cache embedding for text with TTL (default 1 hour)"""
        try:
            key = self._make_key("embedding", text)
            value = json.dumps(embedding)
            return self.client.setex(key, ttl, value)
        except Exception as e:
            print(f"Redis set_embedding error: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════
    # SEARCH RESULTS CACHE
    # ═══════════════════════════════════════════════════════
    
    def get_search_results(self, query: str, top_k: int = 5) -> Optional[List[Dict]]:
        """Get cached search results"""
        try:
            cache_key = f"{query}::{top_k}"
            key = self._make_key("search", cache_key)
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            print(f"Redis get_search_results error: {e}")
            return None
    
    def set_search_results(self, query: str, results: List[Dict], top_k: int = 5, ttl: int = 1800) -> bool:
        """Cache search results with TTL (default 30 minutes)"""
        try:
            cache_key = f"{query}::{top_k}"
            key = self._make_key("search", cache_key)
            value = json.dumps(results)
            return self.client.setex(key, ttl, value)
        except Exception as e:
            print(f"Redis set_search_results error: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════
    # VECTOR SEARCH CACHE (SKUs)
    # ═══════════════════════════════════════════════════════
    
    def get_vector_skus(self, embedding_hash: str, top_k: int = 5) -> Optional[List[str]]:
        """Get cached SKUs from vector search"""
        try:
            cache_key = f"{embedding_hash}::{top_k}"
            key = self._make_key("vector", cache_key)
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            print(f"Redis get_vector_skus error: {e}")
            return None
    
    def set_vector_skus(self, embedding_hash: str, skus: List[str], top_k: int = 5, ttl: int = 900) -> bool:
        """Cache SKUs from vector search with TTL (default 15 minutes)"""
        try:
            cache_key = f"{embedding_hash}::{top_k}"
            key = self._make_key("vector", cache_key)
            value = json.dumps(skus)
            return self.client.setex(key, ttl, value)
        except Exception as e:
            print(f"Redis set_vector_skus error: {e}")
            return False
    
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
        try:
            if pattern:
                keys = self.client.keys(f"hsai:{pattern}:*")
            else:
                keys = self.client.keys("hsai:*")
            
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Redis clear_cache error: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = self.client.info()
            embedding_keys = len(self.client.keys("hsai:embedding:*"))
            search_keys = len(self.client.keys("hsai:search:*"))
            vector_keys = len(self.client.keys("hsai:vector:*"))
            
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
        except Exception as e:
            return {"connected": False, "error": str(e)}

# Global Redis client instance
redis_client = RedisClient() 