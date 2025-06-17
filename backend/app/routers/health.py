from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import time
import psycopg2
import redis
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
import os
from datetime import datetime
from app.utils.logger import logger, log_with_context
from app.utils.redis_client import redis_client
from app.utils.metrics import metrics

router = APIRouter()

class HealthStatus(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"
    uptime_seconds: float
    services: Dict[str, Any]

class ServiceHealth(BaseModel):
    status: str
    response_time_ms: float
    details: Dict[str, Any] = {}

# Store startup time
startup_time = time.time()

def check_postgres() -> Dict[str, Any]:
    """Check PostgreSQL database health."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="hardware_store",
            user="postgres",
            password="postgres",
            port="5432"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result and result[0] == 1:
            return {
                "status": "healthy",
                "message": "PostgreSQL is responding correctly"
            }
        else:
            return {
                "status": "unhealthy",
                "message": "PostgreSQL query returned unexpected result"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"PostgreSQL connection failed: {str(e)}"
        }

def check_redis() -> Dict[str, Any]:
    """Check Redis health."""
    try:
        if not redis_client.is_connected():
            return {
                "status": "unhealthy",
                "message": "Redis connection failed"
            }
        
        # Get cache stats to verify Redis is working
        stats = redis_client.get_cache_stats()
        if stats:
            return {
                "status": "healthy",
                "message": "Redis is responding correctly",
                "details": {
                    "connected": stats.get("connected", False),
                    "total_keys": stats.get("total_keys", 0),
                    "memory_usage": stats.get("memory_usage", "unknown")
                }
            }
        else:
            return {
                "status": "unhealthy", 
                "message": "Redis connection is unstable"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Redis health check failed: {str(e)}"
        }

def check_qdrant() -> Dict[str, Any]:
    """Check Qdrant vector database health."""
    try:
        client = QdrantClient(host="localhost", port=6333)
        collections = client.get_collections()
        
        return {
            "status": "healthy",
            "message": f"Qdrant is responding correctly with {len(collections.collections)} collections"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Qdrant connection failed: {str(e)}"
        }

def check_ollama() -> Dict[str, Any]:
    """Check Ollama embedding service health."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model.get("name", "unknown") for model in models]
            
            return {
                "status": "healthy",
                "message": f"Ollama is responding correctly with {len(models)} models",
                "available_models": model_names
            }
        else:
            return {
                "status": "unhealthy",
                "message": f"Ollama returned status code {response.status_code}"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Ollama connection failed: {str(e)}"
        }

@router.get("/health")
def health_check():
    """
    Comprehensive health check for all services.
    """
    log_with_context(
        logger,
        "info",
        "Health check requested"
    )
    
    # Check all services
    postgres_health = check_postgres()
    redis_health = check_redis()
    qdrant_health = check_qdrant()
    ollama_health = check_ollama()
    
    # Determine overall health
    services = {
        "postgres": postgres_health,
        "redis": redis_health,
        "qdrant": qdrant_health,
        "ollama": ollama_health
    }
    
    # Count healthy services
    healthy_services = sum(1 for service in services.values() if service["status"] == "healthy")
    total_services = len(services)
    
    overall_status = "healthy" if healthy_services == total_services else "degraded"
    if healthy_services == 0:
        overall_status = "unhealthy"
    
    result = {
        "status": overall_status,
        "timestamp": "2024-01-01T00:00:00Z",  # This will be updated by logging middleware
        "services": services,
        "summary": {
            "healthy_services": healthy_services,
            "total_services": total_services,
            "health_percentage": round((healthy_services / total_services) * 100, 1)
        }
    }
    
    log_with_context(
        logger,
        "info",
        "Health check completed",
        overall_status=overall_status,
        healthy_services=healthy_services,
        total_services=total_services
    )
    
    return result

@router.get("/health/postgres")
def postgres_health():
    """Check PostgreSQL database health specifically."""
    return check_postgres()

@router.get("/health/redis")
def redis_health():
    """Check Redis cache health specifically."""
    return check_redis()

@router.get("/health/qdrant")
def qdrant_health():
    """Check Qdrant vector database health specifically."""
    return check_qdrant()

@router.get("/health/ollama")
def ollama_health():
    """Check Ollama embedding service health specifically."""
    return check_ollama()

@router.get("/metrics")
def get_metrics():
    """
    Get application performance metrics.
    """
    log_with_context(
        logger,
        "info",
        "Metrics requested"
    )
    
    try:
        all_metrics = metrics.get_all_metrics()
        
        log_with_context(
            logger,
            "info",
            "Metrics retrieved successfully",
            total_requests=sum(m.get("total_requests", 0) for m in all_metrics.get("requests", {}).values()),
            total_service_calls=sum(m.get("total_calls", 0) for m in all_metrics.get("services", {}).values())
        )
        
        return all_metrics
        
    except Exception as e:
        log_with_context(
            logger,
            "error",
            "Failed to retrieve metrics",
            error=str(e)
        )
        return {
            "error": "Failed to retrieve metrics",
            "message": str(e)
        }

@router.post("/metrics/reset")
def reset_metrics():
    """
    Reset all application metrics.
    """
    log_with_context(
        logger,
        "warning",
        "Metrics reset requested"
    )
    
    try:
        metrics.reset_metrics()
        
        log_with_context(
            logger,
            "info",
            "Metrics reset successfully"
        )
        
        return {
            "status": "success",
            "message": "All metrics have been reset"
        }
        
    except Exception as e:
        log_with_context(
            logger,
            "error",
            "Failed to reset metrics",
            error=str(e)
        )
        return {
            "status": "error",
            "message": f"Failed to reset metrics: {str(e)}"
        }

@router.get("/health/ready")
def readiness_check():
    """
    Kubernetes-style readiness check
    Returns 200 if service is ready to accept traffic
    """
    postgres_health = check_postgres()
    
    if postgres_health["status"] == "healthy":
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/health/live")
def liveness_check():
    """
    Kubernetes-style liveness check
    Returns 200 if service is alive
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat() + "Z"} 