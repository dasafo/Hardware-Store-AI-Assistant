# utils/metrics.py

import time
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from threading import Lock
from datetime import datetime, timedelta
from app.utils.logger import logger, log_with_context

class MetricsCollector:
    """Simple in-memory metrics collector for monitoring application performance."""
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self._lock = Lock()
        
        # Request metrics
        self._request_counts = defaultdict(int)
        self._request_durations = defaultdict(lambda: deque(maxlen=max_samples))
        self._error_counts = defaultdict(int)
        
        # Service metrics
        self._service_calls = defaultdict(int)
        self._service_durations = defaultdict(lambda: deque(maxlen=max_samples))
        self._service_errors = defaultdict(int)
        
        # Cache metrics
        self._cache_hits = defaultdict(int)
        self._cache_misses = defaultdict(int)
        
        # Custom counters
        self._counters = defaultdict(int)
        self._gauges = {}
        
        # Start time
        self._start_time = datetime.utcnow()
        
        log_with_context(
            logger,
            "info",
            "Metrics collector initialized",
            max_samples=max_samples
        )
    
    def record_request(self, method: str, path: str, duration: float, status_code: int):
        """Record HTTP request metrics."""
        with self._lock:
            endpoint = f"{method} {path}"
            self._request_counts[endpoint] += 1
            self._request_durations[endpoint].append(duration)
            
            if status_code >= 400:
                self._error_counts[endpoint] += 1
    
    def record_service_call(self, service: str, operation: str, duration: float, success: bool = True):
        """Record service call metrics."""
        with self._lock:
            service_op = f"{service}.{operation}"
            self._service_calls[service_op] += 1
            self._service_durations[service_op].append(duration)
            
            if not success:
                self._service_errors[service_op] += 1
    
    def record_cache_hit(self, cache_type: str):
        """Record cache hit."""
        with self._lock:
            self._cache_hits[cache_type] += 1
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss."""
        with self._lock:
            self._cache_misses[cache_type] += 1
    
    def increment_counter(self, name: str, value: int = 1):
        """Increment a custom counter."""
        with self._lock:
            self._counters[name] += value
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge value."""
        with self._lock:
            self._gauges[name] = value
    
    def get_request_metrics(self) -> Dict[str, Any]:
        """Get request metrics summary."""
        with self._lock:
            metrics = {}
            
            for endpoint, count in self._request_counts.items():
                durations = list(self._request_durations[endpoint])
                errors = self._error_counts[endpoint]
                
                if durations:
                    avg_duration = sum(durations) / len(durations)
                    max_duration = max(durations)
                    min_duration = min(durations)
                    
                    # Calculate percentiles
                    sorted_durations = sorted(durations)
                    p95_idx = int(0.95 * len(sorted_durations))
                    p99_idx = int(0.99 * len(sorted_durations))
                    
                    metrics[endpoint] = {
                        "total_requests": count,
                        "error_count": errors,
                        "error_rate": errors / count if count > 0 else 0,
                        "avg_duration_ms": round(avg_duration * 1000, 2),
                        "min_duration_ms": round(min_duration * 1000, 2),
                        "max_duration_ms": round(max_duration * 1000, 2),
                        "p95_duration_ms": round(sorted_durations[p95_idx] * 1000, 2) if p95_idx < len(sorted_durations) else 0,
                        "p99_duration_ms": round(sorted_durations[p99_idx] * 1000, 2) if p99_idx < len(sorted_durations) else 0,
                    }
            
            return metrics
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get service metrics summary."""
        with self._lock:
            metrics = {}
            
            for service_op, count in self._service_calls.items():
                durations = list(self._service_durations[service_op])
                errors = self._service_errors[service_op]
                
                if durations:
                    avg_duration = sum(durations) / len(durations)
                    max_duration = max(durations)
                    
                    metrics[service_op] = {
                        "total_calls": count,
                        "error_count": errors,
                        "error_rate": errors / count if count > 0 else 0,
                        "avg_duration_ms": round(avg_duration * 1000, 2),
                        "max_duration_ms": round(max_duration * 1000, 2),
                    }
            
            return metrics
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache metrics summary."""
        with self._lock:
            metrics = {}
            
            all_cache_types = set(self._cache_hits.keys()) | set(self._cache_misses.keys())
            
            for cache_type in all_cache_types:
                hits = self._cache_hits[cache_type]
                misses = self._cache_misses[cache_type]
                total = hits + misses
                
                metrics[cache_type] = {
                    "hits": hits,
                    "misses": misses,
                    "total_requests": total,
                    "hit_rate": hits / total if total > 0 else 0,
                }
            
            return metrics
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics."""
        uptime = datetime.utcnow() - self._start_time
        
        with self._lock:
            return {
                "uptime_seconds": uptime.total_seconds(),
                "uptime_human": str(uptime).split('.')[0],  # Remove microseconds
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "start_time": self._start_time.isoformat() + "Z",
            }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "requests": self.get_request_metrics(),
            "services": self.get_service_metrics(),
            "cache": self.get_cache_metrics(),
            "system": self.get_system_metrics(),
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        with self._lock:
            self._request_counts.clear()
            self._request_durations.clear()
            self._error_counts.clear()
            self._service_calls.clear()
            self._service_durations.clear()
            self._service_errors.clear()
            self._cache_hits.clear()
            self._cache_misses.clear()
            self._counters.clear()
            self._gauges.clear()
            self._start_time = datetime.utcnow()
        
        log_with_context(
            logger,
            "info",
            "All metrics reset"
        )

# Context manager for timing operations
class Timer:
    """Context manager for timing operations."""
    
    def __init__(self, metrics_collector: MetricsCollector, metric_type: str, name: str):
        self.metrics_collector = metrics_collector
        self.metric_type = metric_type
        self.name = name
        self.start_time = None
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is not None:
            self.success = False
        
        if self.metric_type == "service":
            service, operation = self.name.split(".", 1)
            self.metrics_collector.record_service_call(service, operation, duration, self.success)
        
        return False  # Don't suppress exceptions

# Global metrics collector instance
metrics = MetricsCollector()

def time_service_call(service: str, operation: str):
    """Decorator/context manager for timing service calls."""
    return Timer(metrics, "service", f"{service}.{operation}") 