"""
Production Infrastructure Package
Comprehensive production-grade infrastructure for database operations, error handling,
monitoring, performance optimization, and system management.
"""

from .database_abstraction import (
    DatabaseAbstraction, 
    DatabaseConfig, 
    ConnectionPool,
    TransactionManager,
    get_database,
    close_database
)

from .unique_constraint_manager import (
    UniqueIDGenerator,
    ConstraintValidator, 
    AtomicOperations,
    ConstraintConfig,
    get_id_generator,
    get_constraint_validator,
    get_atomic_operations
)

from .error_handling import (
    ErrorHandler,
    CircuitBreaker,
    RetryManager,
    ErrorInfo,
    ErrorSeverity,
    ErrorCategory,
    CircuitBreakerOpenException,
    get_error_handler,
    with_circuit_breaker,
    with_retry,
    with_error_handling
)

from .monitoring import (
    ProductionMonitor,
    StructuredLogger,
    MetricsCollector,
    HealthChecker,
    HealthStatus,
    MetricType,
    get_monitor,
    setup_monitoring
)

from .performance_optimization import (
    PerformanceManager,
    LRUCache,
    MultiLevelCache,
    QueryOptimizer,
    CacheLevel,
    get_performance_manager,
    cached,
    performance_monitored
)

from .production_system import (
    ProductionSystem,
    ProductionConfig,
    get_production_system,
    initialize_production_system,
    start_production_system,
    shutdown_production_system
)

__version__ = "1.0.0"
__author__ = "Production Infrastructure Team"

__all__ = [
    # Database
    'DatabaseAbstraction',
    'DatabaseConfig', 
    'ConnectionPool',
    'TransactionManager',
    'get_database',
    'close_database',
    
    # Unique Constraints
    'UniqueIDGenerator',
    'ConstraintValidator',
    'AtomicOperations', 
    'ConstraintConfig',
    'get_id_generator',
    'get_constraint_validator',
    'get_atomic_operations',
    
    # Error Handling
    'ErrorHandler',
    'CircuitBreaker',
    'RetryManager',
    'ErrorInfo',
    'ErrorSeverity', 
    'ErrorCategory',
    'CircuitBreakerOpenException',
    'get_error_handler',
    'with_circuit_breaker',
    'with_retry',
    'with_error_handling',
    
    # Monitoring
    'ProductionMonitor',
    'StructuredLogger',
    'MetricsCollector',
    'HealthChecker',
    'HealthStatus',
    'MetricType',
    'get_monitor',
    'setup_monitoring',
    
    # Performance
    'PerformanceManager',
    'LRUCache',
    'MultiLevelCache', 
    'QueryOptimizer',
    'CacheLevel',
    'get_performance_manager',
    'cached',
    'performance_monitored',
    
    # Production System
    'ProductionSystem',
    'ProductionConfig',
    'get_production_system',
    'initialize_production_system',
    'start_production_system',
    'shutdown_production_system'
]