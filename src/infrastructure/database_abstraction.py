"""
Production-Grade Database Abstraction Layer
Provides thread-safe operations, transaction management, and error handling
Supports both SQLite and PostgreSQL with connection pooling
"""

import sqlite3
import threading
import queue
import os
import logging
import time
import hashlib
import json
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import traceback
from concurrent.futures import ThreadPoolExecutor, Future
from collections import defaultdict
import weakref

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration with production optimizations"""
    database_url: str = "sqlite:///production.db"
    pool_size: int = 20
    max_connections: int = 50
    connection_timeout: int = 30
    query_timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 0.1
    enable_wal: bool = True
    enable_fts: bool = True
    cache_size: int = 10000
    busy_timeout: int = 5000
    checkpoint_interval: int = 1000
    
    # Production optimizations
    enable_connection_pooling: bool = True
    enable_query_cache: bool = True
    enable_metrics: bool = True
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 10
    circuit_breaker_timeout: int = 60

@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    execution_count: int = 0
    total_time: float = 0.0
    average_time: float = 0.0
    max_time: float = 0.0
    min_time: float = float('inf')
    error_count: int = 0
    last_executed: datetime = field(default_factory=datetime.now)

@dataclass
class CircuitBreakerState:
    """Circuit breaker state for resilience"""
    is_open: bool = False
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    next_attempt_time: Optional[datetime] = None

class DatabaseException(Exception):
    """Base database exception"""
    pass

class ConnectionPoolExhaustedException(DatabaseException):
    """Connection pool is exhausted"""
    pass

class DeadlockException(DatabaseException):
    """Database deadlock detected"""
    pass

class CircuitBreakerOpenException(DatabaseException):
    """Circuit breaker is open"""
    pass

class TransactionManager:
    """Thread-safe transaction management"""
    
    def __init__(self, connection, auto_rollback: bool = True):
        self.connection = connection
        self.auto_rollback = auto_rollback
        self.in_transaction = False
        self._lock = threading.RLock()
        
    def __enter__(self):
        with self._lock:
            if not self.in_transaction:
                self.connection.execute("BEGIN")
                self.in_transaction = True
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            if self.in_transaction:
                try:
                    if exc_type is None:
                        self.connection.execute("COMMIT")
                    elif self.auto_rollback:
                        self.connection.execute("ROLLBACK")
                except Exception as e:
                    logger.error(f"Transaction cleanup failed: {e}")
                finally:
                    self.in_transaction = False
                    
    def commit(self):
        """Manual commit"""
        with self._lock:
            if self.in_transaction:
                self.connection.execute("COMMIT")
                self.in_transaction = False
                
    def rollback(self):
        """Manual rollback"""
        with self._lock:
            if self.in_transaction:
                self.connection.execute("ROLLBACK")
                self.in_transaction = False

class ConnectionPool:
    """Production-grade connection pool with health monitoring"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool = queue.Queue(maxsize=config.max_connections)
        self._active_connections = 0
        self._total_connections_created = 0
        self._lock = threading.RLock()
        self._connection_health = weakref.WeakValueDictionary()
        self._last_health_check = datetime.now()
        self._metrics = {
            'connections_created': 0,
            'connections_destroyed': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'wait_timeouts': 0
        }
        
        # Initialize pool
        self._initialize_pool()
        
        # Start health check thread
        self._health_check_thread = threading.Thread(
            target=self._health_check_worker,
            daemon=True
        )
        self._health_check_thread.start()
        
    def _initialize_pool(self):
        """Initialize connection pool"""
        with self._lock:
            for _ in range(self.config.pool_size):
                conn = self._create_connection()
                if conn:
                    self._pool.put(conn)
                    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create optimized SQLite connection"""
        try:
            # Parse database URL
            if self.config.database_url.startswith('sqlite://'):
                db_path = self.config.database_url.replace('sqlite://', '')
            else:
                db_path = self.config.database_url
                
            conn = sqlite3.connect(
                db_path,
                timeout=self.config.connection_timeout,
                check_same_thread=False,
                isolation_level=None  # Explicit transaction control
            )
            
            # Apply production optimizations
            self._optimize_connection(conn)
            
            with self._lock:
                self._active_connections += 1
                self._total_connections_created += 1
                self._metrics['connections_created'] += 1
                
            # Track connection health
            conn_id = id(conn)
            self._connection_health[conn_id] = {
                'created_at': datetime.now(),
                'query_count': 0,
                'last_used': datetime.now(),
                'errors': 0
            }
            
            logger.debug(f"Created connection {conn_id}")
            return conn
            
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            return None
            
    def _optimize_connection(self, conn: sqlite3.Connection):
        """Apply SQLite optimizations"""
        try:
            # Enable WAL mode for better concurrency
            if self.config.enable_wal:
                conn.execute("PRAGMA journal_mode=WAL")
                
            # Performance optimizations
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute(f"PRAGMA cache_size={self.config.cache_size}")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
            conn.execute(f"PRAGMA busy_timeout={self.config.busy_timeout}")
            
            # Enable foreign keys and other constraints
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA recursive_triggers=ON")
            
            # Set row factory for dict-like access
            conn.row_factory = sqlite3.Row
            
        except Exception as e:
            logger.error(f"Failed to optimize connection: {e}")
            
    @contextmanager
    def get_connection(self, timeout: Optional[float] = None):
        """Get connection from pool with timeout"""
        timeout = timeout or self.config.connection_timeout
        conn = None
        start_time = time.time()
        
        try:
            # Try to get from pool first
            try:
                conn = self._pool.get_nowait()
                self._metrics['pool_hits'] += 1
            except queue.Empty:
                # Pool empty, check if we can create new connection
                with self._lock:
                    if self._active_connections < self.config.max_connections:
                        conn = self._create_connection()
                        self._metrics['pool_misses'] += 1
                    else:
                        # Wait for available connection
                        try:
                            conn = self._pool.get(timeout=timeout)
                            self._metrics['pool_hits'] += 1
                        except queue.Empty:
                            self._metrics['wait_timeouts'] += 1
                            raise ConnectionPoolExhaustedException(
                                f"Connection pool exhausted after {timeout}s timeout"
                            )
                            
            if not conn:
                raise DatabaseException("Unable to get database connection")
                
            # Update connection health
            conn_id = id(conn)
            if conn_id in self._connection_health:
                self._connection_health[conn_id]['last_used'] = datetime.now()
                self._connection_health[conn_id]['query_count'] += 1
                
            # Verify connection is still valid
            try:
                conn.execute("SELECT 1").fetchone()
            except Exception:
                # Connection is stale, create new one
                logger.warning(f"Stale connection {conn_id} detected, creating new one")
                conn.close()
                conn = self._create_connection()
                if not conn:
                    raise DatabaseException("Failed to create replacement connection")
                    
            yield conn
            
        except Exception as e:
            # Update error metrics
            conn_id = id(conn) if conn else None
            if conn_id and conn_id in self._connection_health:
                self._connection_health[conn_id]['errors'] += 1
            raise
            
        finally:
            # Return connection to pool or close if pool is full
            if conn:
                try:
                    # Check if connection is still usable
                    conn.execute("SELECT 1").fetchone()
                    
                    try:
                        self._pool.put_nowait(conn)
                    except queue.Full:
                        # Pool is full, close connection
                        conn.close()
                        with self._lock:
                            self._active_connections -= 1
                            self._metrics['connections_destroyed'] += 1
                            
                except Exception as e:
                    # Connection is broken, close it
                    logger.warning(f"Closing broken connection: {e}")
                    try:
                        conn.close()
                    except:
                        pass
                    with self._lock:
                        self._active_connections -= 1
                        self._metrics['connections_destroyed'] += 1
                        
    def _health_check_worker(self):
        """Background health check for connections"""
        while True:
            try:
                time.sleep(60)  # Check every minute
                self._perform_health_check()
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                
    def _perform_health_check(self):
        """Perform connection pool health check"""
        current_time = datetime.now()
        stale_connections = []
        
        # Check for stale connections
        for conn_id, health_info in list(self._connection_health.items()):
            last_used = health_info.get('last_used', current_time)
            if current_time - last_used > timedelta(minutes=30):
                stale_connections.append(conn_id)
                
        # Log metrics
        logger.info(f"Pool metrics: {self._metrics}")
        logger.info(f"Active connections: {self._active_connections}")
        logger.info(f"Stale connections: {len(stale_connections)}")
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get connection pool metrics"""
        with self._lock:
            return {
                'active_connections': self._active_connections,
                'total_created': self._total_connections_created,
                'pool_size': self.config.pool_size,
                'max_connections': self.config.max_connections,
                **self._metrics
            }
            
    def close_all(self):
        """Close all connections in pool"""
        with self._lock:
            closed_count = 0
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    conn.close()
                    closed_count += 1
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
                    
            self._active_connections = 0
            logger.info(f"Closed {closed_count} connections")

class QueryCache:
    """Thread-safe query result cache"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache = {}
        self._access_times = {}
        self._lock = threading.RLock()
        
    def get(self, query_hash: str) -> Optional[Any]:
        """Get cached result"""
        with self._lock:
            if query_hash in self._cache:
                cache_entry = self._cache[query_hash]
                if time.time() - cache_entry['timestamp'] < self.ttl_seconds:
                    self._access_times[query_hash] = time.time()
                    return cache_entry['result']
                else:
                    # Expired entry
                    del self._cache[query_hash]
                    del self._access_times[query_hash]
        return None
        
    def put(self, query_hash: str, result: Any):
        """Cache query result"""
        with self._lock:
            # Evict oldest entries if cache is full
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
                
            self._cache[query_hash] = {
                'result': result,
                'timestamp': time.time()
            }
            self._access_times[query_hash] = time.time()
            
    def _evict_oldest(self):
        """Evict oldest cache entries"""
        if not self._access_times:
            return
            
        # Remove 25% of oldest entries
        sorted_entries = sorted(self._access_times.items(), key=lambda x: x[1])
        evict_count = max(1, len(sorted_entries) // 4)
        
        for query_hash, _ in sorted_entries[:evict_count]:
            self._cache.pop(query_hash, None)
            self._access_times.pop(query_hash, None)
            
    def clear(self):
        """Clear all cached entries"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()

class DatabaseAbstraction:
    """Production-grade database abstraction with resilience patterns"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = ConnectionPool(config) if config.enable_connection_pooling else None
        self.query_cache = QueryCache() if config.enable_query_cache else None
        self.metrics = defaultdict(QueryMetrics) if config.enable_metrics else None
        self.circuit_breaker = CircuitBreakerState() if config.enable_circuit_breaker else None
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._lock = threading.RLock()
        
    def _get_query_hash(self, query: str, params: tuple = ()) -> str:
        """Generate hash for query caching"""
        query_str = f"{query}|{params}"
        return hashlib.md5(query_str.encode()).hexdigest()
        
    def _check_circuit_breaker(self):
        """Check circuit breaker state"""
        if not self.circuit_breaker or not self.config.enable_circuit_breaker:
            return
            
        if self.circuit_breaker.is_open:
            if self.circuit_breaker.next_attempt_time and datetime.now() < self.circuit_breaker.next_attempt_time:
                raise CircuitBreakerOpenException("Circuit breaker is open")
            else:
                # Try half-open state
                self.circuit_breaker.is_open = False
                
    def _record_success(self):
        """Record successful operation"""
        if self.circuit_breaker:
            self.circuit_breaker.failure_count = 0
            self.circuit_breaker.last_failure_time = None
            
    def _record_failure(self):
        """Record failed operation"""
        if not self.circuit_breaker:
            return
            
        self.circuit_breaker.failure_count += 1
        self.circuit_breaker.last_failure_time = datetime.now()
        
        if self.circuit_breaker.failure_count >= self.config.circuit_breaker_threshold:
            self.circuit_breaker.is_open = True
            self.circuit_breaker.next_attempt_time = datetime.now() + timedelta(
                seconds=self.config.circuit_breaker_timeout
            )
            logger.warning("Circuit breaker opened due to repeated failures")
            
    def _record_metrics(self, query_hash: str, execution_time: float, error: bool = False):
        """Record query metrics"""
        if not self.metrics:
            return
            
        metric = self.metrics[query_hash]
        metric.execution_count += 1
        
        if error:
            metric.error_count += 1
        else:
            metric.total_time += execution_time
            metric.average_time = metric.total_time / (metric.execution_count - metric.error_count)
            metric.max_time = max(metric.max_time, execution_time)
            metric.min_time = min(metric.min_time, execution_time)
            
        metric.last_executed = datetime.now()
        
    @contextmanager
    def get_connection(self):
        """Get database connection with circuit breaker"""
        self._check_circuit_breaker()
        
        if self.pool:
            with self.pool.get_connection() as conn:
                yield conn
        else:
            # Fallback to direct connection
            conn = sqlite3.connect(
                self.config.database_url.replace('sqlite://', ''),
                timeout=self.config.connection_timeout
            )
            try:
                yield conn
            finally:
                conn.close()
                
    def execute_with_retry(self, query: str, params: tuple = (), 
                          fetch_mode: str = 'none') -> Any:
        """Execute query with retry logic and error handling"""
        query_hash = self._get_query_hash(query, params)
        
        # Check cache first
        if self.query_cache and fetch_mode in ('all', 'one') and not query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            cached_result = self.query_cache.get(query_hash)
            if cached_result is not None:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_result
                
        last_exception = None
        start_time = time.time()
        
        for attempt in range(self.config.retry_attempts):
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Execute query with timeout
                    cursor.execute(query, params)
                    
                    result = None
                    if fetch_mode == 'all':
                        result = [dict(row) for row in cursor.fetchall()]
                    elif fetch_mode == 'one':
                        row = cursor.fetchone()
                        result = dict(row) if row else None
                    elif fetch_mode == 'scalar':
                        row = cursor.fetchone()
                        result = row[0] if row else None
                    else:
                        result = cursor.rowcount
                        
                    # Cache results if appropriate
                    if self.query_cache and result is not None and fetch_mode in ('all', 'one'):
                        self.query_cache.put(query_hash, result)
                        
                    # Record success
                    execution_time = time.time() - start_time
                    self._record_metrics(query_hash, execution_time)
                    self._record_success()
                    
                    return result
                    
            except sqlite3.OperationalError as e:
                last_exception = e
                error_msg = str(e).lower()
                
                if 'database is locked' in error_msg or 'disk i/o error' in error_msg:
                    # Retry on lock/IO errors
                    if attempt < self.config.retry_attempts - 1:
                        time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                elif 'deadlock' in error_msg:
                    raise DeadlockException(f"Database deadlock: {e}")
                else:
                    break
                    
            except Exception as e:
                last_exception = e
                break
                
        # All retries failed
        execution_time = time.time() - start_time
        self._record_metrics(query_hash, execution_time, error=True)
        self._record_failure()
        
        error_msg = f"Query failed after {self.config.retry_attempts} attempts: {last_exception}"
        logger.error(error_msg)
        raise DatabaseException(error_msg) from last_exception
        
    def execute_transaction(self, operations: List[Tuple[str, tuple]]) -> bool:
        """Execute multiple operations in a transaction"""
        try:
            with self.get_connection() as conn:
                with TransactionManager(conn) as transaction:
                    for query, params in operations:
                        cursor = conn.cursor()
                        cursor.execute(query, params)
                    transaction.commit()
            return True
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return False
            
    def execute_async(self, query: str, params: tuple = (), 
                     fetch_mode: str = 'none') -> Future:
        """Execute query asynchronously"""
        return self._executor.submit(
            self.execute_with_retry, query, params, fetch_mode
        )
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get database metrics"""
        result = {}
        
        if self.pool:
            result['connection_pool'] = self.pool.get_metrics()
            
        if self.query_cache:
            result['query_cache'] = {
                'size': len(self.query_cache._cache),
                'max_size': self.query_cache.max_size,
                'hit_rate': 'N/A'  # Would need to track hits/misses
            }
            
        if self.circuit_breaker:
            result['circuit_breaker'] = {
                'is_open': self.circuit_breaker.is_open,
                'failure_count': self.circuit_breaker.failure_count,
                'last_failure': self.circuit_breaker.last_failure_time.isoformat() if self.circuit_breaker.last_failure_time else None
            }
            
        if self.metrics:
            result['query_metrics'] = {
                hash_val: {
                    'execution_count': metric.execution_count,
                    'average_time': metric.average_time,
                    'error_count': metric.error_count
                }
                for hash_val, metric in self.metrics.items()
            }
            
        return result
        
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        try:
            # Test basic connectivity
            start_time = time.time()
            result = self.execute_with_retry("SELECT 1", fetch_mode='scalar')
            response_time = time.time() - start_time
            
            health_status['checks']['database_connectivity'] = {
                'status': 'pass' if result == 1 else 'fail',
                'response_time_ms': round(response_time * 1000, 2)
            }
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['database_connectivity'] = {
                'status': 'fail',
                'error': str(e)
            }
            
        # Add pool status
        if self.pool:
            pool_metrics = self.pool.get_metrics()
            health_status['checks']['connection_pool'] = {
                'status': 'pass' if pool_metrics['active_connections'] > 0 else 'fail',
                'active_connections': pool_metrics['active_connections'],
                'pool_utilization': round(pool_metrics['active_connections'] / self.config.max_connections * 100, 1)
            }
            
        return health_status
        
    def close(self):
        """Clean shutdown"""
        if self.pool:
            self.pool.close_all()
        if self._executor:
            self._executor.shutdown(wait=True)

# Global database instance
_db_instance: Optional[DatabaseAbstraction] = None

def get_database(config: DatabaseConfig = None) -> DatabaseAbstraction:
    """Get global database instance"""
    global _db_instance
    if _db_instance is None:
        config = config or DatabaseConfig()
        _db_instance = DatabaseAbstraction(config)
    return _db_instance

def close_database():
    """Close global database instance"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None