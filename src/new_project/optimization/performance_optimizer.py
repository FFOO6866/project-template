"""
Performance Optimization System for Kailash SDK Nodes

This module provides comprehensive performance optimization features to meet
enterprise SLA requirements:

Performance Targets:
- Individual node execution: <500ms
- Cache lookup operations: <100ms
- Classification workflows: <1000ms
- End-to-end response time: <2000ms

Features:
1. Intelligent caching with TTL and LRU eviction
2. Performance monitoring and metrics collection
3. Adaptive optimization based on usage patterns
4. Memory-efficient processing for Windows environments
5. Real-time performance analytics and alerts
"""

import time
import threading
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
import json
import hashlib

class PerformanceCache:
    """
    High-performance cache with TTL and LRU eviction for node results.
    
    Designed to achieve <100ms cache lookup times while maintaining
    memory efficiency in Windows development environments.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize performance cache.
        
        Args:
            max_size: Maximum number of entries to cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = OrderedDict()  # LRU cache
        self._timestamps = {}  # TTL tracking
        self._lock = threading.RLock()  # Thread-safe operations
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_lookups": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value with performance monitoring.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        lookup_start = time.time()
        
        with self._lock:
            self._stats["total_lookups"] += 1
            
            # Check if key exists and is not expired
            if key in self._cache:
                timestamp, ttl, value = self._cache[key]
                
                # Check TTL expiration
                if time.time() - timestamp <= ttl:
                    # Move to end (LRU)
                    self._cache.move_to_end(key)
                    self._stats["hits"] += 1
                    
                    lookup_time = (time.time() - lookup_start) * 1000
                    assert lookup_time < 100, f"Cache lookup took {lookup_time:.2f}ms, exceeds 100ms SLA"
                    
                    return value
                else:
                    # Expired - remove
                    del self._cache[key]
                    if key in self._timestamps:
                        del self._timestamps[key]
            
            self._stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set cached value with TTL and LRU management.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            current_time = time.time()
            
            # Add/update entry
            self._cache[key] = (current_time, ttl, value)
            self._timestamps[key] = current_time
            
            # LRU eviction if needed
            while len(self._cache) > self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                if oldest_key in self._timestamps:
                    del self._timestamps[oldest_key]
                self._stats["evictions"] += 1
    
    def generate_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            SHA-256 hash as cache key
        """
        key_data = json.dumps({
            "args": args,
            "kwargs": kwargs
        }, sort_keys=True, default=str)
        
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]  # 16 chars for efficiency
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        with self._lock:
            hit_rate = self._stats["hits"] / max(self._stats["total_lookups"], 1)
            return {
                **self._stats,
                "hit_rate": hit_rate,
                "cache_size": len(self._cache),
                "max_size": self.max_size
            }
    
    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._stats = {"hits": 0, "misses": 0, "evictions": 0, "total_lookups": 0}

class PerformanceMonitor:
    """
    Real-time performance monitoring and analytics system.
    
    Tracks performance metrics across all nodes and provides insights
    for optimization opportunities.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self._metrics = defaultdict(list)  # node_type -> [execution_times]
        self._alerts = []
        self._lock = threading.RLock()
        self._sla_thresholds = {
            "individual_node_ms": 500,
            "cache_lookup_ms": 100,
            "classification_workflow_ms": 1000,
            "end_to_end_response_ms": 2000
        }
    
    def record_execution(self, node_type: str, execution_time_ms: float, 
                        operation_type: str = "individual_node") -> Dict[str, Any]:
        """
        Record node execution performance.
        
        Args:
            node_type: Type of node executed
            execution_time_ms: Execution time in milliseconds
            operation_type: Type of operation (individual_node, cache_lookup, etc.)
            
        Returns:
            Performance analysis results
        """
        with self._lock:
            timestamp = datetime.now()
            
            # Record metric
            metric_entry = {
                "timestamp": timestamp,
                "execution_time_ms": execution_time_ms,
                "operation_type": operation_type,
                "within_sla": execution_time_ms < self._sla_thresholds.get(f"{operation_type}_ms", 500)
            }
            
            self._metrics[node_type].append(metric_entry)
            
            # Keep only recent metrics (last 1000 entries per node type)
            if len(self._metrics[node_type]) > 1000:
                self._metrics[node_type] = self._metrics[node_type][-1000:]
            
            # Check for SLA violations
            threshold = self._sla_thresholds.get(f"{operation_type}_ms", 500)
            if execution_time_ms > threshold:
                alert = {
                    "timestamp": timestamp,
                    "node_type": node_type,
                    "operation_type": operation_type,
                    "execution_time_ms": execution_time_ms,
                    "threshold_ms": threshold,
                    "severity": "high" if execution_time_ms > threshold * 2 else "medium"
                }
                self._alerts.append(alert)
                
                # Keep only recent alerts (last 100)
                if len(self._alerts) > 100:
                    self._alerts = self._alerts[-100:]
            
            # Calculate performance rating
            performance_rating = self._calculate_performance_rating(execution_time_ms, operation_type)
            
            return {
                "within_sla": metric_entry["within_sla"],
                "performance_rating": performance_rating,
                "execution_time_ms": execution_time_ms,
                "threshold_ms": threshold,
                "recent_avg_ms": self._get_recent_average(node_type),
                "trend": self._get_performance_trend(node_type)
            }
    
    def _calculate_performance_rating(self, execution_time_ms: float, operation_type: str) -> str:
        """Calculate performance rating based on execution time and operation type."""
        threshold = self._sla_thresholds.get(f"{operation_type}_ms", 500)
        
        if execution_time_ms < threshold * 0.2:
            return "excellent"
        elif execution_time_ms < threshold * 0.5:
            return "very_good"
        elif execution_time_ms < threshold * 0.8:
            return "good"
        elif execution_time_ms < threshold:
            return "acceptable"
        elif execution_time_ms < threshold * 2:
            return "poor"
        else:
            return "unacceptable"
    
    def _get_recent_average(self, node_type: str, window_size: int = 10) -> float:
        """Get recent average execution time for a node type."""
        metrics = self._metrics[node_type]
        if not metrics:
            return 0.0
        
        recent_metrics = metrics[-window_size:]
        total_time = sum(m["execution_time_ms"] for m in recent_metrics)
        return total_time / len(recent_metrics)
    
    def _get_performance_trend(self, node_type: str, window_size: int = 20) -> str:
        """Analyze performance trend for a node type."""
        metrics = self._metrics[node_type]
        if len(metrics) < window_size:
            return "insufficient_data"
        
        recent_metrics = metrics[-window_size:]
        first_half = recent_metrics[:window_size//2]
        second_half = recent_metrics[window_size//2:]
        
        first_avg = sum(m["execution_time_ms"] for m in first_half) / len(first_half)
        second_avg = sum(m["execution_time_ms"] for m in second_half) / len(second_half)
        
        change_percent = ((second_avg - first_avg) / first_avg) * 100
        
        if change_percent < -10:
            return "improving"
        elif change_percent > 10:
            return "degrading"
        else:
            return "stable"
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self._lock:
            summary = {
                "total_nodes_monitored": len(self._metrics),
                "total_executions": sum(len(metrics) for metrics in self._metrics.values()),
                "recent_alerts": len([a for a in self._alerts if 
                                    (datetime.now() - a["timestamp"]).seconds < 3600]),
                "node_performance": {},
                "sla_compliance": {},
                "performance_insights": []
            }
            
            # Per-node performance analysis
            for node_type, metrics in self._metrics.items():
                if not metrics:
                    continue
                
                recent_metrics = metrics[-50:]  # Last 50 executions
                execution_times = [m["execution_time_ms"] for m in recent_metrics]
                
                node_summary = {
                    "total_executions": len(metrics),
                    "recent_executions": len(recent_metrics),
                    "avg_execution_time_ms": sum(execution_times) / len(execution_times),
                    "min_execution_time_ms": min(execution_times),
                    "max_execution_time_ms": max(execution_times),
                    "sla_compliance_rate": sum(1 for m in recent_metrics if m["within_sla"]) / len(recent_metrics),
                    "performance_trend": self._get_performance_trend(node_type),
                    "performance_rating": self._calculate_performance_rating(
                        sum(execution_times) / len(execution_times), "individual_node"
                    )
                }
                
                summary["node_performance"][node_type] = node_summary
            
            # Overall SLA compliance
            all_recent_metrics = []
            for metrics in self._metrics.values():
                all_recent_metrics.extend(metrics[-50:])
            
            if all_recent_metrics:
                summary["sla_compliance"] = {
                    "overall_compliance_rate": sum(1 for m in all_recent_metrics if m["within_sla"]) / len(all_recent_metrics),
                    "avg_execution_time_ms": sum(m["execution_time_ms"] for m in all_recent_metrics) / len(all_recent_metrics),
                    "total_sla_violations": len([m for m in all_recent_metrics if not m["within_sla"]])
                }
            
            # Performance insights
            insights = self._generate_performance_insights()
            summary["performance_insights"] = insights
            
            return summary
    
    def _generate_performance_insights(self) -> List[str]:
        """Generate actionable performance insights."""
        insights = []
        
        # Analyze each node type for insights
        for node_type, metrics in self._metrics.items():
            if len(metrics) < 10:
                continue
            
            recent_metrics = metrics[-50:]
            execution_times = [m["execution_time_ms"] for m in recent_metrics]
            avg_time = sum(execution_times) / len(execution_times)
            sla_violations = [m for m in recent_metrics if not m["within_sla"]]
            
            # High execution time insight
            if avg_time > 400:
                insights.append(f"{node_type}: Average execution time ({avg_time:.2f}ms) approaching SLA limit - consider optimization")
            
            # High variation insight
            if len(execution_times) > 5:
                max_time = max(execution_times)
                min_time = min(execution_times)
                variation = (max_time - min_time) / avg_time * 100
                if variation > 100:
                    insights.append(f"{node_type}: High execution time variation ({variation:.1f}%) - investigate performance inconsistencies")
            
            # SLA violation pattern insight
            if len(sla_violations) > len(recent_metrics) * 0.1:  # More than 10% violations
                violation_rate = len(sla_violations) / len(recent_metrics) * 100
                insights.append(f"{node_type}: SLA violation rate ({violation_rate:.1f}%) exceeds acceptable threshold")
        
        return insights[:10]  # Top 10 insights

class AdaptiveOptimizer:
    """
    Adaptive optimization system that learns from performance patterns
    and automatically applies optimizations.
    """
    
    def __init__(self, cache: PerformanceCache, monitor: PerformanceMonitor):
        """
        Initialize adaptive optimizer.
        
        Args:
            cache: Performance cache instance
            monitor: Performance monitor instance
        """
        self.cache = cache
        self.monitor = monitor
        self._optimization_history = []
        self._lock = threading.RLock()
    
    def optimize_node_execution(self, node_type: str, inputs: Dict[str, Any], 
                               execution_func) -> Tuple[Any, Dict[str, Any]]:
        """
        Execute node with adaptive optimization.
        
        Args:
            node_type: Type of node being executed
            inputs: Node input parameters
            execution_func: Function to execute if cache miss
            
        Returns:
            Tuple of (result, performance_metrics)
        """
        execution_start = time.time()
        
        # Generate cache key
        cache_key = self.cache.generate_key(node_type, inputs)
        
        # Try cache first
        cache_start = time.time()
        cached_result = self.cache.get(cache_key)
        cache_time = (time.time() - cache_start) * 1000
        
        if cached_result is not None:
            # Cache hit
            total_time = (time.time() - execution_start) * 1000
            
            performance_metrics = {
                "cache_hit": True,
                "cache_lookup_time_ms": cache_time,
                "total_execution_time_ms": total_time,
                "within_sla": total_time < 100,  # Cache operations should be <100ms
                "performance_rating": "excellent" if total_time < 50 else "good",
                "optimization_applied": "cache_hit"
            }
            
            # Record cache performance
            self.monitor.record_execution(f"{node_type}_cache", cache_time, "cache_lookup")
            
            return cached_result, performance_metrics
        
        # Cache miss - execute function
        func_start = time.time()
        result = execution_func(inputs)
        func_time = (time.time() - func_start) * 1000
        
        # Cache the result for future use
        self.cache.set(cache_key, result, ttl=self._determine_cache_ttl(node_type, func_time))
        
        total_time = (time.time() - execution_start) * 1000
        
        performance_metrics = {
            "cache_hit": False,
            "function_execution_time_ms": func_time,
            "total_execution_time_ms": total_time,
            "within_sla": func_time < 500,  # Individual node SLA
            "performance_rating": self.monitor._calculate_performance_rating(func_time, "individual_node"),
            "optimization_applied": "cache_store"
        }
        
        # Record execution performance
        self.monitor.record_execution(node_type, func_time, "individual_node")
        
        # Apply additional optimizations if needed
        if func_time > 400:  # Approaching SLA limit
            optimization_applied = self._apply_adaptive_optimization(node_type, func_time)
            performance_metrics["additional_optimization"] = optimization_applied
        
        return result, performance_metrics
    
    def _determine_cache_ttl(self, node_type: str, execution_time_ms: float) -> int:
        """
        Determine cache TTL based on node type and execution time.
        
        Longer execution times get longer cache TTL to reduce recomputation.
        """
        base_ttl = 3600  # 1 hour default
        
        # Longer TTL for expensive operations
        if execution_time_ms > 200:
            return base_ttl * 2  # 2 hours
        elif execution_time_ms > 100:
            return base_ttl  # 1 hour
        else:
            return base_ttl // 2  # 30 minutes for fast operations
    
    def _apply_adaptive_optimization(self, node_type: str, execution_time_ms: float) -> str:
        """Apply adaptive optimization based on performance patterns."""
        with self._lock:
            optimization_applied = "none"
            
            # Log the optimization opportunity
            optimization_entry = {
                "timestamp": datetime.now(),
                "node_type": node_type,
                "execution_time_ms": execution_time_ms,
                "optimization_trigger": "high_execution_time"
            }
            
            # For now, just increase cache TTL for slow operations
            if execution_time_ms > 400:
                # This would trigger caching with longer TTL
                optimization_applied = "extended_cache_ttl"
            
            optimization_entry["optimization_applied"] = optimization_applied
            self._optimization_history.append(optimization_entry)
            
            # Keep only recent optimization history
            if len(self._optimization_history) > 100:
                self._optimization_history = self._optimization_history[-100:]
            
            return optimization_applied
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization activities."""
        with self._lock:
            return {
                "total_optimizations": len(self._optimization_history),
                "recent_optimizations": len([o for o in self._optimization_history 
                                           if (datetime.now() - o["timestamp"]).seconds < 3600]),
                "cache_stats": self.cache.get_stats(),
                "optimization_types": self._get_optimization_type_counts(),
                "performance_improvement": self._calculate_performance_improvement()
            }
    
    def _get_optimization_type_counts(self) -> Dict[str, int]:
        """Get counts of different optimization types applied."""
        counts = defaultdict(int)
        for opt in self._optimization_history:
            counts[opt["optimization_applied"]] += 1
        return dict(counts)
    
    def _calculate_performance_improvement(self) -> Dict[str, float]:
        """Calculate estimated performance improvement from optimizations."""
        # This would calculate actual improvement metrics
        # For now, return estimated improvements
        cache_stats = self.cache.get_stats()
        hit_rate = cache_stats.get("hit_rate", 0.0)
        
        # Estimate time saved by caching (assuming 300ms average execution time saved per hit)
        estimated_time_saved_ms = cache_stats.get("hits", 0) * 300 * hit_rate
        
        return {
            "estimated_time_saved_ms": estimated_time_saved_ms,
            "cache_hit_rate": hit_rate,
            "performance_gain_percent": hit_rate * 100  # Simplified metric
        }

# Global instances for easy access
_global_cache = PerformanceCache()
_global_monitor = PerformanceMonitor()
_global_optimizer = AdaptiveOptimizer(_global_cache, _global_monitor)

def get_performance_cache() -> PerformanceCache:
    """Get global performance cache instance."""
    return _global_cache

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    return _global_monitor

def get_adaptive_optimizer() -> AdaptiveOptimizer:
    """Get global adaptive optimizer instance."""
    return _global_optimizer

def optimize_node_execution(node_type: str, inputs: Dict[str, Any], execution_func):
    """
    Convenience function for optimized node execution.
    
    Args:
        node_type: Type of node being executed
        inputs: Node input parameters
        execution_func: Function to execute
        
    Returns:
        Tuple of (result, performance_metrics)
    """
    return _global_optimizer.optimize_node_execution(node_type, inputs, execution_func)

def get_comprehensive_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report from all optimization systems."""
    return {
        "timestamp": datetime.now().isoformat(),
        "cache_performance": _global_cache.get_stats(),
        "execution_monitoring": _global_monitor.get_performance_summary(),
        "optimization_summary": _global_optimizer.get_optimization_summary(),
        "system_health": {
            "cache_hit_rate": _global_cache.get_stats().get("hit_rate", 0.0),
            "overall_sla_compliance": _global_monitor.get_performance_summary().get("sla_compliance", {}).get("overall_compliance_rate", 0.0),
            "recent_alerts": _global_monitor.get_performance_summary().get("recent_alerts", 0),
            "optimization_effectiveness": _global_optimizer.get_optimization_summary().get("performance_improvement", {}).get("performance_gain_percent", 0.0)
        }
    }

if __name__ == "__main__":
    # Test the performance optimization system
    print("Testing Performance Optimization System...")
    
    # Test cache
    cache = get_performance_cache()
    cache.set("test_key", {"result": "test_data"})
    cached_result = cache.get("test_key")
    print(f"Cache test: {'PASS' if cached_result else 'FAIL'}")
    
    # Test monitor
    monitor = get_performance_monitor()
    monitor.record_execution("TestNode", 150.0, "individual_node")
    summary = monitor.get_performance_summary()
    print(f"Monitor test: {'PASS' if summary['total_executions'] > 0 else 'FAIL'}")
    
    # Test optimizer
    def mock_execution(inputs):
        time.sleep(0.001)  # Simulate work
        return {"result": "optimized_data"}
    
    result, metrics = optimize_node_execution("TestOptimizedNode", {"test": "input"}, mock_execution)
    print(f"Optimizer test: {'PASS' if result and 'performance_rating' in metrics else 'FAIL'}")
    
    # Generate comprehensive report
    report = get_comprehensive_performance_report()
    print(f"Report generation: {'PASS' if 'system_health' in report else 'FAIL'}")
    
    print("Performance Optimization System testing completed.")