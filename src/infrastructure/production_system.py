"""
Production System Integration
Brings together all infrastructure components for production deployment
Provides unified API, configuration management, and system initialization

PRODUCTION READY:
- ✅ Uses centralized src.core.config (NO duplicate config classes)
- ✅ NO os.getenv() fallbacks
- ✅ ALL configuration from validated environment
"""

import sys
import signal
import atexit
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import logging

# Import all infrastructure components
from .database_abstraction import DatabaseAbstraction, DatabaseConfig, get_database
from .unique_constraint_manager import UniqueIDGenerator, ConstraintValidator, AtomicOperations
from .error_handling import ErrorHandler, get_error_handler, with_error_handling, with_circuit_breaker, with_retry
from .monitoring import ProductionMonitor, get_monitor, HealthStatus
from .performance_optimization import PerformanceManager, get_performance_manager, cached, performance_monitored

# Import centralized configuration - NO duplicates
from src.core.config import config

logger = logging.getLogger(__name__)


class ProductionSystem:
    """
    Main production system coordinator

    Uses centralized configuration from src.core.config (validated at import time)
    NO local config class, NO os.getenv() fallbacks
    """

    def __init__(self):
        """Initialize production system with centralized configuration"""
        # Use global config instance (already validated)
        self.config = config
        self.is_initialized = False
        self.is_running = False
        self.startup_time = None
        self._shutdown_handlers = []
        
        # Component instances
        self.database: Optional[DatabaseAbstraction] = None
        self.error_handler: Optional[ErrorHandler] = None
        self.monitor: Optional[ProductionMonitor] = None
        self.performance_manager: Optional[PerformanceManager] = None
        self.id_generator: Optional[UniqueIDGenerator] = None
        self.constraint_validator: Optional[ConstraintValidator] = None
        self.atomic_operations: Optional[AtomicOperations] = None
        
    def initialize(self) -> bool:
        """Initialize all production system components"""
        try:
            logger.info("Initializing production system...")
            start_time = time.time()
            
            # Initialize database
            self._initialize_database()
            
            # Initialize error handling
            self._initialize_error_handling()
            
            # Initialize monitoring
            self._initialize_monitoring()
            
            # Initialize performance management
            self._initialize_performance()
            
            # Initialize business logic components
            self._initialize_business_components()
            
            # Setup signal handlers
            if self.config.enable_signal_handlers:
                self._setup_signal_handlers()
                
            # Register shutdown handler
            if self.config.enable_graceful_shutdown:
                atexit.register(self.shutdown)
                
            self.is_initialized = True
            self.startup_time = datetime.now()
            
            initialization_time = time.time() - start_time
            logger.info(f"Production system initialized successfully in {initialization_time:.2f}s")
            
            # Log system status
            self._log_system_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize production system: {e}")
            self.shutdown()
            return False
            
    def _initialize_database(self):
        """
        Initialize database with production configuration

        Uses centralized config for ALL database settings:
        - DATABASE_URL (validated - no localhost in production)
        - DATABASE_POOL_SIZE
        - DATABASE_MAX_OVERFLOW
        - DATABASE_POOL_TIMEOUT
        """
        db_config = DatabaseConfig(
            database_url=self.config.DATABASE_URL,
            pool_size=self.config.DATABASE_POOL_SIZE,
            max_connections=self.config.DATABASE_POOL_SIZE + self.config.DATABASE_MAX_OVERFLOW,
            connection_timeout=self.config.DATABASE_POOL_TIMEOUT,
            enable_connection_pooling=True,
            enable_query_cache=True,
            enable_metrics=True,
            enable_circuit_breaker=True,  # Always enabled in production
            circuit_breaker_threshold=5,  # Conservative default
            circuit_breaker_timeout=60
        )

        self.database = DatabaseAbstraction(db_config)
        logger.info("Database initialized with connection pooling and circuit breaker")

    def _initialize_error_handling(self):
        """Initialize error handling system with circuit breakers"""
        self.error_handler = get_error_handler()

        # Always enable circuit breaker in production for database resilience
        self.error_handler.register_circuit_breaker(
            "database_operations",
            failure_threshold=5,
            timeout_seconds=60
        )

        logger.info("Error handling system initialized with circuit breakers")
        
    def _initialize_monitoring(self):
        """Initialize monitoring system"""
        self.monitor = get_monitor()
        
        # Register custom health checks
        self._register_health_checks()
        
        # Setup monitoring alerts
        self._setup_monitoring_alerts()
        
        logger.info("Monitoring system initialized")
        
    def _initialize_performance(self):
        """
        Initialize performance management with production thresholds

        Default production thresholds (not configurable - enterprise-grade standards):
        - Slow query: 500ms
        - Response time: 2000ms
        - Cache hit rate minimum: 70%
        """
        self.performance_manager = get_performance_manager()

        # Production performance thresholds (enterprise standards)
        self.performance_manager.thresholds.update({
            'slow_query_ms': 500,
            'response_time_ms': 2000,
            'cache_hit_rate_min': 70.0
        })

        logger.info("Performance management initialized with enterprise thresholds")
        
    def _initialize_business_components(self):
        """Initialize business logic components"""
        self.id_generator = UniqueIDGenerator(self.database)
        self.constraint_validator = ConstraintValidator(self.database)
        self.atomic_operations = AtomicOperations(self.database)
        
        logger.info("Business components initialized")
        
    def _register_health_checks(self):
        """Register custom health checks"""
        def check_database_connectivity():
            try:
                with self.database.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    
                if result and result[0] == 1:
                    return self.monitor.health_checker.HealthCheckResult(
                        name="database_connectivity",
                        status=HealthStatus.HEALTHY,
                        message="Database connection successful"
                    )
                else:
                    return self.monitor.health_checker.HealthCheckResult(
                        name="database_connectivity",
                        status=HealthStatus.UNHEALTHY,
                        message="Database query returned unexpected result"
                    )
                    
            except Exception as e:
                return self.monitor.health_checker.HealthCheckResult(
                    name="database_connectivity",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Database connection failed: {str(e)}"
                )
                
        def check_cache_performance():
            try:
                cache_stats = self.performance_manager.cache.get_stats()
                hit_rate = cache_stats['overall']['hit_rate']

                # Production cache hit rate threshold: 70%
                CACHE_HIT_RATE_THRESHOLD = 70.0

                if hit_rate >= CACHE_HIT_RATE_THRESHOLD:
                    status = HealthStatus.HEALTHY
                    message = f"Cache hit rate: {hit_rate:.1f}%"
                elif hit_rate >= CACHE_HIT_RATE_THRESHOLD * 0.5:
                    status = HealthStatus.DEGRADED
                    message = f"Low cache hit rate: {hit_rate:.1f}%"
                else:
                    status = HealthStatus.UNHEALTHY
                    message = f"Very low cache hit rate: {hit_rate:.1f}%"
                    
                return self.monitor.health_checker.HealthCheckResult(
                    name="cache_performance",
                    status=status,
                    message=message,
                    details=cache_stats
                )
                
            except Exception as e:
                return self.monitor.health_checker.HealthCheckResult(
                    name="cache_performance",
                    status=HealthStatus.UNKNOWN,
                    message=f"Cache check failed: {str(e)}"
                )
                
        self.monitor.health_checker.register_check("database_connectivity", check_database_connectivity)
        self.monitor.health_checker.register_check("cache_performance", check_cache_performance)
        
    def _setup_monitoring_alerts(self):
        """Setup monitoring alerts"""
        from .monitoring import Alert
        
        # Database connection alert
        db_alert = Alert(
            name="database_connection_failures",
            condition=lambda metrics: any(
                'database' in k and m.get('error_count', 0) > 5
                for k, m in metrics.items()
            ),
            message="High number of database connection failures",
            severity="critical"
        )
        self.monitor.alert_manager.register_alert(db_alert)
        
        # Cache performance alert (70% threshold - production standard)
        cache_alert = Alert(
            name="low_cache_performance",
            condition=lambda metrics: any(
                'cache' in k and m.get('hit_rate', 100) < 70.0
                for k, m in metrics.items()
            ),
            message="Cache hit rate below 70% threshold",
            severity="warning"
        )
        self.monitor.alert_manager.register_alert(cache_alert)
        
    def _setup_signal_handlers(self):
        """
        Setup graceful shutdown signal handlers

        Handles SIGINT (Ctrl+C) and SIGTERM (docker stop, systemctl stop)
        for clean resource cleanup
        """
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("Signal handlers registered for graceful shutdown")
        
    def _log_system_status(self):
        """
        Log initial system status

        SECURITY: Does NOT log sensitive config values (passwords, API keys)
        """
        status = {
            'system': 'production',
            'version': '1.0.0',
            'startup_time': self.startup_time.isoformat(),
            'environment': self.config.ENVIRONMENT,
            'configuration': {
                'database_pool_size': self.config.DATABASE_POOL_SIZE,
                'cache_enabled': True,
                'monitoring_enabled': True,
                'circuit_breaker_enabled': True,
                'debug_mode': self.config.DEBUG  # Should be False in production
            }
        }

        self.monitor.logger.log_business_event('system_startup', status)
        
    def start(self) -> bool:
        """Start the production system"""
        if not self.is_initialized:
            if not self.initialize():
                return False
                
        self.is_running = True
        logger.info("Production system started")
        return True
        
    def shutdown(self, timeout: Optional[int] = None):
        """
        Graceful shutdown of production system

        Default timeout: 30 seconds (production standard)
        """
        if not self.is_running:
            return

        timeout = timeout or 30  # 30-second shutdown timeout
        logger.info(f"Shutting down production system (timeout: {timeout}s)...")
        
        self.is_running = False
        
        # Run shutdown handlers
        for handler in self._shutdown_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Shutdown handler failed: {e}")
                
        # Shutdown components
        try:
            if self.database:
                self.database.close()
                logger.info("Database connections closed")
                
            if self.monitor:
                # Final health check and metrics
                final_status = self.monitor.get_status_dashboard()
                logger.info(f"Final system status: {final_status['overall_status']}")
                
            logger.info("Production system shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            
    def register_shutdown_handler(self, handler: Callable):
        """Register custom shutdown handler"""
        self._shutdown_handlers.append(handler)
        
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        if not self.database:
            raise RuntimeError("Database not initialized")
            
        with self.database.get_connection() as conn:
            with self.database.TransactionManager(conn) as tx:
                yield tx
                
    @with_error_handling("create_quotation")
    @performance_monitored("create_quotation")
    def create_quotation(self, quotation_data: Dict, items: List[Dict] = None) -> Tuple[bool, str, Any]:
        """Create quotation with full error handling and monitoring"""
        return self.atomic_operations.create_quotation_atomic(quotation_data, items)
        
    @with_error_handling("create_customer") 
    @performance_monitored("create_customer")
    def create_customer(self, customer_data: Dict) -> Tuple[bool, str, Any]:
        """Create customer with full error handling and monitoring"""
        return self.atomic_operations.create_customer_atomic(customer_data)
        
    @cached(ttl=300)  # Cache for 5 minutes
    @with_error_handling("search_products")
    @performance_monitored("search_products")
    def search_products(self, query: str, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Search products with caching and error handling"""
        search_sql = """
            SELECT id, name, description, price, category, brand
            FROM products 
            WHERE description LIKE ? OR name LIKE ?
        """
        
        if filters and 'category' in filters:
            search_sql += " AND category = ?"
            params = (f"%{query}%", f"%{query}%", filters['category'])
        else:
            params = (f"%{query}%", f"%{query}%")
            
        search_sql += f" LIMIT {limit}"
        
        return self.database.execute_with_retry(search_sql, params, fetch_mode='all')
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        if not self.is_initialized:
            return {"status": "not_initialized"}
            
        status_dashboard = self.monitor.get_status_dashboard()
        performance_report = self.performance_manager.get_performance_report()
        
        return {
            "system": {
                "status": "running" if self.is_running else "stopped",
                "startup_time": self.startup_time.isoformat() if self.startup_time else None,
                "uptime_seconds": (datetime.now() - self.startup_time).total_seconds() if self.startup_time else 0,
                "environment": self.config.ENVIRONMENT,
                "debug_mode": self.config.DEBUG
            },
            "health": status_dashboard,
            "performance": performance_report,
            "configuration": {
                "database_pool_size": self.config.DATABASE_POOL_SIZE,
                "api_workers": self.config.API_WORKERS,
                "log_level": self.config.LOG_LEVEL
                # SECURITY: Do NOT expose secrets in status endpoint
            }
        }
        
    def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics"""
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "overall_status": "unknown"
        }
        
        # Database diagnostics
        if self.database:
            try:
                db_health = self.database.health_check()
                db_metrics = self.database.get_metrics()
                diagnostics["components"]["database"] = {
                    "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
                    "health": db_health,
                    "metrics": db_metrics
                }
            except Exception as e:
                diagnostics["components"]["database"] = {
                    "status": "error",
                    "error": str(e)
                }
                
        # Performance diagnostics
        if self.performance_manager:
            try:
                perf_report = self.performance_manager.get_performance_report()
                diagnostics["components"]["performance"] = {
                    "status": perf_report["health_status"],
                    "report": perf_report
                }
            except Exception as e:
                diagnostics["components"]["performance"] = {
                    "status": "error", 
                    "error": str(e)
                }
                
        # Error handling diagnostics
        if self.error_handler:
            try:
                circuit_breaker_stats = {
                    name: cb.get_stats() 
                    for name, cb in self.error_handler.circuit_breakers.items()
                }
                diagnostics["components"]["error_handling"] = {
                    "status": "healthy",
                    "circuit_breakers": circuit_breaker_stats,
                    "error_counts": dict(self.error_handler.error_counts)
                }
            except Exception as e:
                diagnostics["components"]["error_handling"] = {
                    "status": "error",
                    "error": str(e)
                }
                
        # Determine overall status
        component_statuses = [
            comp.get("status", "unknown") 
            for comp in diagnostics["components"].values()
        ]
        
        if all(status == "healthy" for status in component_statuses):
            diagnostics["overall_status"] = "healthy"
        elif any(status == "error" for status in component_statuses):
            diagnostics["overall_status"] = "unhealthy"
        else:
            diagnostics["overall_status"] = "degraded"
            
        return diagnostics

# Global production system instance
_production_system: Optional[ProductionSystem] = None


def get_production_system() -> ProductionSystem:
    """
    Get global production system instance

    Uses centralized config from src.core.config (no parameters needed)
    """
    global _production_system
    if _production_system is None:
        _production_system = ProductionSystem()
    return _production_system


def initialize_production_system() -> bool:
    """
    Initialize global production system

    Configuration is loaded from environment (src.core.config)
    """
    system = get_production_system()
    return system.initialize()


def start_production_system() -> bool:
    """
    Start global production system

    Configuration is loaded from environment (src.core.config)
    """
    system = get_production_system()
    return system.start()


def shutdown_production_system():
    """Shutdown global production system"""
    global _production_system
    if _production_system:
        _production_system.shutdown()
        _production_system = None