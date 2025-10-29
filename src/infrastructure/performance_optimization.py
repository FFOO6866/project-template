"""
Performance Optimization System
Provides multi-level caching, query optimization, response time monitoring, and resource management
"""

import time
import threading
import hashlib
import pickle
import json
import gzip
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, OrderedDict
from contextlib import contextmanager
from functools import wraps, lru_cache
import weakref
import sqlite3
import logging

from .database_abstraction import DatabaseAbstraction, get_database
from .monitoring import get_monitor

logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    L1_MEMORY = "l1_memory"      # In-memory, fastest
    L2_DISK = "l2_disk"          # Disk-based, persistent
    L3_DISTRIBUTED = "l3_distributed"  # Distributed cache (future)

@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    size_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    size_bytes: int
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if not self.ttl_seconds:
            return False
        return datetime.now() - self.created_at > timedelta(seconds=self.ttl_seconds)
        
    def update_access(self):
        """Update access statistics"""
        self.last_accessed = datetime.now()
        self.access_count += 1

class LRUCache:
    """Thread-safe LRU cache with TTL and size limits"""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100, default_ttl: int = 3600):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()
        self._lock = threading.RLock()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None
                
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                return None
                
            # Update access and move to end (most recent)
            entry.update_access()
            self._cache.move_to_end(key)
            
            self._stats.hits += 1
            return entry.value
            
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            # Calculate size
            size_bytes = self._calculate_size(value)
            
            with self._lock:
                # Remove existing entry
                if key in self._cache:
                    old_entry = self._cache[key]
                    self._stats.size_bytes -= old_entry.size_bytes
                    del self._cache[key]
                    
                # Create new entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    size_bytes=size_bytes,
                    ttl_seconds=ttl or self.default_ttl
                )
                
                # Check memory limit
                if self._stats.size_bytes + size_bytes > self.max_memory_bytes:
                    self._evict_lru()
                    
                # Check size limit
                if len(self._cache) >= self.max_size:
                    self._evict_lru()
                    
                self._cache[key] = entry
                self._stats.size_bytes += size_bytes
                self._stats.sets += 1
                
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
            
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                self._stats.size_bytes -= entry.size_bytes
                del self._cache[key]
                self._stats.deletes += 1
                return True
        return False
        
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()
            
    def _evict_lru(self):
        """Evict least recently used entries"""
        while (len(self._cache) >= self.max_size or 
               self._stats.size_bytes > self.max_memory_bytes):
            if not self._cache:
                break
                
            # Remove oldest entry
            key, entry = self._cache.popitem(last=False)
            self._stats.size_bytes -= entry.size_bytes
            self._stats.evictions += 1
            
    def _calculate_size(self, value: Any) -> int:
        """Estimate memory size of value"""
        try:
            return len(pickle.dumps(value))
        except:
            # Fallback estimation
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (list, tuple)):
                return sum(self._calculate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(self._calculate_size(k) + self._calculate_size(v) 
                          for k, v in value.items())
            else:
                return 64  # Default estimate
                
    def _cleanup_worker(self):
        """Background cleanup of expired entries"""
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"Cache cleanup failed: {e}")
                
    def _cleanup_expired(self):
        """Remove expired entries"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                entry = self._cache[key]
                self._stats.size_bytes -= entry.size_bytes
                del self._cache[key]
                self._stats.evictions += 1
                
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self._stats

class DiskCache:
    """Persistent disk-based cache"""
    
    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 500):
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._stats = CacheStats()
        self._lock = threading.RLock()
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load existing cache stats
        self._load_stats()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        try:
            file_path = self._get_cache_path(key)
            
            if not os.path.exists(file_path):
                self._stats.misses += 1
                return None
                
            # Read metadata and check expiration
            metadata = self._read_metadata(key)
            if metadata and self._is_expired(metadata):
                self._remove_file(key)
                self._stats.misses += 1
                self._stats.evictions += 1
                return None
                
            # Read value
            with gzip.open(file_path, 'rb') as f:
                data = pickle.load(f)
                
            # Update access time in metadata
            self._update_access(key)
            
            self._stats.hits += 1
            return data
            
        except Exception as e:
            logger.error(f"Disk cache get failed for key {key}: {e}")
            self._stats.misses += 1
            return None
            
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in disk cache"""
        try:
            file_path = self._get_cache_path(key)
            
            # Serialize and compress
            with gzip.open(file_path, 'wb') as f:
                pickle.dump(value, f)
                
            # Create metadata
            file_size = os.path.getsize(file_path)
            metadata = {
                'key': key,
                'size_bytes': file_size,
                'created_at': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'ttl_seconds': ttl,
                'access_count': 0
            }
            
            self._write_metadata(key, metadata)
            
            with self._lock:
                self._stats.sets += 1
                self._stats.size_bytes += file_size
                
            # Check size limits and cleanup if needed
            self._cleanup_if_needed()
            
            return True
            
        except Exception as e:
            logger.error(f"Disk cache set failed for key {key}: {e}")
            return False
            
    def delete(self, key: str) -> bool:
        """Delete key from disk cache"""
        try:
            if self._remove_file(key):
                self._stats.deletes += 1
                return True
        except Exception as e:
            logger.error(f"Disk cache delete failed for key {key}: {e}")
        return False
        
    def _get_cache_path(self, key: str) -> str:
        """Get file path for cache key"""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.cache")
        
    def _get_metadata_path(self, key: str) -> str:
        """Get metadata file path for cache key"""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.meta")
        
    def _read_metadata(self, key: str) -> Optional[Dict]:
        """Read metadata for cache key"""
        try:
            metadata_path = self._get_metadata_path(key)
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return None
        
    def _write_metadata(self, key: str, metadata: Dict):
        """Write metadata for cache key"""
        try:
            metadata_path = self._get_metadata_path(key)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        except Exception as e:
            logger.error(f"Failed to write metadata: {e}")
            
    def _update_access(self, key: str):
        """Update access time in metadata"""
        metadata = self._read_metadata(key)
        if metadata:
            metadata['last_accessed'] = datetime.now().isoformat()
            metadata['access_count'] = metadata.get('access_count', 0) + 1
            self._write_metadata(key, metadata)
            
    def _is_expired(self, metadata: Dict) -> bool:
        """Check if cache entry is expired"""
        ttl = metadata.get('ttl_seconds')
        if not ttl:
            return False
            
        created_at = datetime.fromisoformat(metadata['created_at'])
        return datetime.now() - created_at > timedelta(seconds=ttl)
        
    def _remove_file(self, key: str) -> bool:
        """Remove cache and metadata files"""
        try:
            cache_path = self._get_cache_path(key)
            metadata_path = self._get_metadata_path(key)
            
            removed = False
            if os.path.exists(cache_path):
                file_size = os.path.getsize(cache_path)
                os.remove(cache_path)
                self._stats.size_bytes -= file_size
                removed = True
                
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
                
            return removed
            
        except Exception as e:
            logger.error(f"Failed to remove cache file: {e}")
            return False
            
    def _cleanup_if_needed(self):
        """Cleanup cache if size limits exceeded"""
        if self._stats.size_bytes > self.max_size_bytes:
            self._cleanup_lru()
            
    def _cleanup_lru(self):
        """Remove least recently used entries"""
        try:
            # Get all cache files with metadata
            cache_files = []
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    key_hash = filename[:-6]  # Remove .cache extension
                    metadata_path = os.path.join(self.cache_dir, f"{key_hash}.meta")
                    
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                                
                            last_accessed = datetime.fromisoformat(metadata['last_accessed'])
                            cache_files.append((last_accessed, key_hash, metadata))
                            
                        except:
                            continue
                            
            # Sort by last accessed time
            cache_files.sort(key=lambda x: x[0])
            
            # Remove oldest entries until under size limit
            for last_accessed, key_hash, metadata in cache_files:
                if self._stats.size_bytes <= self.max_size_bytes * 0.8:  # 80% of limit
                    break
                    
                cache_path = os.path.join(self.cache_dir, f"{key_hash}.cache")
                metadata_path = os.path.join(self.cache_dir, f"{key_hash}.meta")
                
                try:
                    if os.path.exists(cache_path):
                        file_size = os.path.getsize(cache_path)
                        os.remove(cache_path)
                        self._stats.size_bytes -= file_size
                        
                    if os.path.exists(metadata_path):
                        os.remove(metadata_path)
                        
                    self._stats.evictions += 1
                    
                except Exception as e:
                    logger.error(f"Failed to remove cache file during cleanup: {e}")
                    
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
            
    def _load_stats(self):
        """Load cache statistics from disk"""
        try:
            stats_path = os.path.join(self.cache_dir, "stats.json")
            if os.path.exists(stats_path):
                with open(stats_path, 'r') as f:
                    stats_data = json.load(f)
                    self._stats = CacheStats(**stats_data)
        except:
            pass
            
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self._stats

class MultiLevelCache:
    """Multi-level cache system (L1: Memory, L2: Disk)"""
    
    def __init__(self, l1_config: Dict = None, l2_config: Dict = None):
        l1_config = l1_config or {}
        l2_config = l2_config or {}
        
        self.l1_cache = LRUCache(**l1_config)
        self.l2_cache = DiskCache(**l2_config)
        
        self._stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'total_misses': 0,
            'promotions': 0  # L2 -> L1 promotions
        }
        self._lock = threading.RLock()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache"""
        # Try L1 first
        value = self.l1_cache.get(key)
        if value is not None:
            with self._lock:
                self._stats['l1_hits'] += 1
            return value
            
        # Try L2
        value = self.l2_cache.get(key)
        if value is not None:
            with self._lock:
                self._stats['l2_hits'] += 1
                self._stats['promotions'] += 1
                
            # Promote to L1
            self.l1_cache.set(key, value)
            return value
            
        # Cache miss
        with self._lock:
            self._stats['total_misses'] += 1
        return None
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in multi-level cache"""
        # Set in both levels
        l1_success = self.l1_cache.set(key, value, ttl)
        l2_success = self.l2_cache.set(key, value, ttl)
        
        return l1_success or l2_success
        
    def delete(self, key: str) -> bool:
        """Delete key from all cache levels"""
        l1_deleted = self.l1_cache.delete(key)
        l2_deleted = self.l2_cache.delete(key)
        
        return l1_deleted or l2_deleted
        
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        l1_stats = self.l1_cache.get_stats()
        l2_stats = self.l2_cache.get_stats()
        
        total_hits = self._stats['l1_hits'] + self._stats['l2_hits']
        total_requests = total_hits + self._stats['total_misses']
        
        return {
            'overall': {
                'total_requests': total_requests,
                'total_hits': total_hits,
                'total_misses': self._stats['total_misses'],
                'hit_rate': (total_hits / total_requests * 100) if total_requests > 0 else 0,
                'l1_hit_rate': (self._stats['l1_hits'] / total_requests * 100) if total_requests > 0 else 0,
                'l2_hit_rate': (self._stats['l2_hits'] / total_requests * 100) if total_requests > 0 else 0,
                'promotions': self._stats['promotions']
            },
            'l1_memory': {
                'hits': l1_stats.hits,
                'misses': l1_stats.misses,
                'hit_rate': l1_stats.hit_rate,
                'size_bytes': l1_stats.size_bytes,
                'evictions': l1_stats.evictions
            },
            'l2_disk': {
                'hits': l2_stats.hits,
                'misses': l2_stats.misses,
                'hit_rate': l2_stats.hit_rate,
                'size_bytes': l2_stats.size_bytes,
                'evictions': l2_stats.evictions
            }
        }

class QueryOptimizer:
    """Database query optimization and analysis"""
    
    def __init__(self, db: DatabaseAbstraction = None):
        self.db = db or get_database()
        self.query_patterns = {}
        self.slow_queries = []
        self.query_stats = defaultdict(list)
        self._lock = threading.RLock()
        
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query for optimization opportunities"""
        query_lower = query.lower().strip()
        analysis = {
            'query_type': self._get_query_type(query_lower),
            'complexity': self._assess_complexity(query_lower),
            'optimization_suggestions': [],
            'estimated_cost': 0
        }
        
        # Check for common optimization opportunities
        if 'select *' in query_lower:
            analysis['optimization_suggestions'].append("Avoid SELECT *, specify only needed columns")
            analysis['estimated_cost'] += 10
            
        if 'like' in query_lower and query_lower.count('%') > 0:
            if query_lower.find("'%") != -1:
                analysis['optimization_suggestions'].append("Leading wildcard LIKE queries cannot use indexes")
                analysis['estimated_cost'] += 20
                
        if 'order by' in query_lower and 'limit' not in query_lower:
            analysis['optimization_suggestions'].append("ORDER BY without LIMIT may be expensive")
            analysis['estimated_cost'] += 15
            
        if query_lower.count('join') > 3:
            analysis['optimization_suggestions'].append("Multiple JOINs may benefit from query restructuring")
            analysis['estimated_cost'] += 25
            
        if 'group by' in query_lower and 'having' not in query_lower:
            analysis['optimization_suggestions'].append("Consider adding HAVING clause to filter groups")
            
        return analysis
        
    def optimize_query(self, query: str) -> str:
        """Suggest optimized version of query"""
        optimized = query
        query_lower = query.lower()
        
        # Replace SELECT * with specific columns (placeholder logic)
        if 'select *' in query_lower and 'from products' in query_lower:
            optimized = query.replace(
                'SELECT *',
                'SELECT id, name, description, price, category, brand'
            )
            
        # Add LIMIT if missing on potentially large result sets
        if ('select' in query_lower and 'limit' not in query_lower and 
            'count(' not in query_lower):
            optimized += ' LIMIT 1000'
            
        return optimized
        
    def record_query_execution(self, query: str, execution_time: float, row_count: int = 0):
        """Record query execution metrics"""
        with self._lock:
            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            
            self.query_stats[query_hash].append({
                'execution_time': execution_time,
                'row_count': row_count,
                'timestamp': datetime.now()
            })
            
            # Track slow queries
            if execution_time > 1.0:  # Queries taking more than 1 second
                self.slow_queries.append({
                    'query': query,
                    'execution_time': execution_time,
                    'row_count': row_count,
                    'timestamp': datetime.now(),
                    'analysis': self.analyze_query(query)
                })
                
                # Keep only recent slow queries
                if len(self.slow_queries) > 100:
                    self.slow_queries = self.slow_queries[-100:]
                    
    def get_query_recommendations(self) -> List[Dict[str, Any]]:
        """Get query optimization recommendations"""
        recommendations = []
        
        # Analyze slow queries
        for slow_query in self.slow_queries[-10:]:  # Last 10 slow queries
            recommendations.append({
                'type': 'slow_query',
                'query': slow_query['query'][:100] + '...' if len(slow_query['query']) > 100 else slow_query['query'],
                'execution_time': slow_query['execution_time'],
                'suggestions': slow_query['analysis']['optimization_suggestions']
            })
            
        # Check for frequently executed queries
        for query_hash, executions in self.query_stats.items():
            if len(executions) > 100:  # Frequently executed
                avg_time = sum(e['execution_time'] for e in executions) / len(executions)
                if avg_time > 0.5:  # Average time > 500ms
                    recommendations.append({
                        'type': 'frequent_slow_query',
                        'query_hash': query_hash,
                        'execution_count': len(executions),
                        'average_time': avg_time,
                        'suggestion': 'Consider caching results or adding indexes'
                    })
                    
        return recommendations
        
    def _get_query_type(self, query: str) -> str:
        """Determine query type"""
        if query.startswith('select'):
            return 'SELECT'
        elif query.startswith('insert'):
            return 'INSERT'
        elif query.startswith('update'):
            return 'UPDATE'
        elif query.startswith('delete'):
            return 'DELETE'
        else:
            return 'OTHER'
            
    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity"""
        score = 0
        
        # Count complexity indicators
        score += query.count('join') * 2
        score += query.count('subselect') * 3
        score += query.count('union') * 2
        score += query.count('group by')
        score += query.count('order by')
        score += query.count('having')
        
        if score == 0:
            return 'SIMPLE'
        elif score <= 3:
            return 'MODERATE'
        elif score <= 8:
            return 'COMPLEX'
        else:
            return 'VERY_COMPLEX'

class PerformanceManager:
    """Main performance management system"""
    
    def __init__(self):
        self.cache = MultiLevelCache()
        self.query_optimizer = QueryOptimizer()
        self.monitor = get_monitor()
        
        # Performance thresholds
        self.thresholds = {
            'slow_query_ms': 500,
            'response_time_ms': 2000,
            'cache_hit_rate_min': 70.0,
            'memory_usage_max': 85.0
        }
        
    @contextmanager
    def performance_tracking(self, operation_name: str, **context):
        """Context manager for performance tracking"""
        start_time = time.time()
        
        try:
            with self.monitor.metrics.timer(f"operation.{operation_name}", tags=context):
                yield
        finally:
            execution_time = time.time() - start_time
            
            # Log slow operations
            if execution_time * 1000 > self.thresholds['slow_query_ms']:
                self.monitor.logger.log_business_event(
                    'slow_operation',
                    {
                        'operation': operation_name,
                        'execution_time_ms': execution_time * 1000,
                        'context': context
                    }
                )
                
    def cache_decorator(self, key_func: Callable = None, ttl: int = 3600):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                    
                # Try cache first
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                    
                # Execute function
                with self.performance_tracking(func.__name__):
                    result = func(*args, **kwargs)
                    
                # Cache result
                self.cache.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator
        
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        cache_stats = self.cache.get_stats()
        query_recommendations = self.query_optimizer.get_query_recommendations()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cache_performance': cache_stats,
            'query_optimization': {
                'slow_queries_count': len(self.query_optimizer.slow_queries),
                'recommendations': query_recommendations
            },
            'performance_thresholds': self.thresholds,
            'health_status': self._assess_performance_health(cache_stats)
        }
        
    def _assess_performance_health(self, cache_stats: Dict[str, Any]) -> str:
        """Assess overall performance health"""
        issues = []
        
        # Check cache hit rate
        overall_hit_rate = cache_stats['overall']['hit_rate']
        if overall_hit_rate < self.thresholds['cache_hit_rate_min']:
            issues.append(f"Low cache hit rate: {overall_hit_rate:.1f}%")
            
        # Check for slow queries
        if len(self.query_optimizer.slow_queries) > 10:
            issues.append(f"High number of slow queries: {len(self.query_optimizer.slow_queries)}")
            
        if not issues:
            return "HEALTHY"
        elif len(issues) <= 2:
            return "DEGRADED"
        else:
            return "UNHEALTHY"

# Global performance manager
_performance_manager: Optional[PerformanceManager] = None

def get_performance_manager() -> PerformanceManager:
    """Get global performance manager instance"""
    global _performance_manager
    if _performance_manager is None:
        _performance_manager = PerformanceManager()
    return _performance_manager

# Convenience decorators
def cached(ttl: int = 3600, key_func: Callable = None):
    """Decorator for caching function results"""
    return get_performance_manager().cache_decorator(key_func, ttl)

def performance_monitored(operation_name: str = None):
    """Decorator for performance monitoring"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            pm = get_performance_manager()
            
            with pm.performance_tracking(op_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator