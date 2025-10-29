"""
Production Monitoring System
Provides structured logging, health checks, metrics collection, and alerting
"""

import logging
import logging.handlers
import time
import threading
import json
import os
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from contextlib import contextmanager
import traceback
import socket
import platform

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class HealthCheckResult:
    """Health check result"""
    name: str
    status: HealthStatus
    message: str = ""
    response_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Metric:
    """Metric data point"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags
        }

@dataclass
class Alert:
    """Alert configuration and state"""
    name: str
    condition: Callable[[Any], bool]
    message: str
    severity: str = "warning"
    cooldown_minutes: int = 5
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    is_active: bool = False

class StructuredLogger:
    """Production-grade structured logging"""
    
    def __init__(self, name: str = "production", log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        # Configure formatters
        self.setup_formatters()
        self.setup_handlers()
        
    def setup_formatters(self):
        """Setup log formatters"""
        # JSON formatter for structured logs
        self.json_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s", '
            '"module": "%(module)s", "function": "%(funcName)s", '
            '"line": %(lineno)d, "thread": "%(threadName)s"}'
        )
        
        # Human-readable formatter for console
        self.console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def setup_handlers(self):
        """Setup log handlers"""
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.console_formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "application.log"),
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10
        )
        file_handler.setFormatter(self.json_formatter)
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "errors.log"),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        error_handler.setFormatter(self.json_formatter)
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)
        
    def log_request(self, method: str, path: str, response_time: float, 
                   status_code: int, user_id: str = None, **kwargs):
        """Log HTTP request"""
        extra = {
            'event_type': 'http_request',
            'method': method,
            'path': path,
            'response_time_ms': round(response_time * 1000, 2),
            'status_code': status_code,
            'user_id': user_id,
            **kwargs
        }
        
        level = logging.ERROR if status_code >= 500 else logging.INFO
        self.logger.log(level, f"{method} {path} - {status_code} ({response_time*1000:.2f}ms)", extra=extra)
        
    def log_database_operation(self, operation: str, table: str, 
                             execution_time: float, affected_rows: int = 0, **kwargs):
        """Log database operation"""
        extra = {
            'event_type': 'database_operation',
            'operation': operation,
            'table': table,
            'execution_time_ms': round(execution_time * 1000, 2),
            'affected_rows': affected_rows,
            **kwargs
        }
        
        level = logging.WARNING if execution_time > 1.0 else logging.DEBUG
        self.logger.log(level, f"DB {operation} on {table} ({execution_time*1000:.2f}ms)", extra=extra)
        
    def log_error(self, error: Exception, context: Dict[str, Any] = None, **kwargs):
        """Log error with full context"""
        context = context or {}
        extra = {
            'event_type': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'stack_trace': traceback.format_exc(),
            'context': context,
            **kwargs
        }
        
        self.logger.error(f"Error: {type(error).__name__}: {error}", extra=extra)
        
    def log_business_event(self, event_type: str, details: Dict[str, Any], **kwargs):
        """Log business events"""
        extra = {
            'event_type': 'business_event',
            'business_event_type': event_type,
            'details': details,
            **kwargs
        }
        
        self.logger.info(f"Business Event: {event_type}", extra=extra)

class MetricsCollector:
    """Collects and aggregates system metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.retention_hours = retention_hours
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        
    def increment(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment counter metric"""
        with self._lock:
            key = self._get_metric_key(name, tags)
            self.counters[key] += value
            
            metric = Metric(name, self.counters[key], MetricType.COUNTER, tags=tags or {})
            self.metrics[key].append(metric)
            
    def gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set gauge metric"""
        with self._lock:
            key = self._get_metric_key(name, tags)
            self.gauges[key] = value
            
            metric = Metric(name, value, MetricType.GAUGE, tags=tags or {})
            self.metrics[key].append(metric)
            
    def histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record histogram value"""
        with self._lock:
            key = self._get_metric_key(name, tags)
            self.histograms[key].append(value)
            
            # Keep only recent values (last 1000)
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]
                
            metric = Metric(name, value, MetricType.HISTOGRAM, tags=tags or {})
            self.metrics[key].append(metric)
            
    @contextmanager
    def timer(self, name: str, tags: Dict[str, str] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            self.histogram(name, execution_time * 1000, tags)  # Store in milliseconds
            
    def _get_metric_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Generate metric key including tags"""
        if not tags:
            return name
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
        
    def _cleanup_worker(self):
        """Background cleanup of old metrics"""
        while True:
            try:
                time.sleep(3600)  # Run every hour
                self._cleanup_old_metrics()
            except Exception as e:
                logging.error(f"Metrics cleanup failed: {e}")
                
    def _cleanup_old_metrics(self):
        """Remove old metric data"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        with self._lock:
            for key, metric_queue in self.metrics.items():
                # Remove old metrics
                while metric_queue and metric_queue[0].timestamp < cutoff_time:
                    metric_queue.popleft()
                    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get metrics summary for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        summary = {}
        
        with self._lock:
            for key, metric_queue in self.metrics.items():
                recent_metrics = [m for m in metric_queue if m.timestamp >= cutoff_time]
                
                if not recent_metrics:
                    continue
                    
                metric_name = recent_metrics[0].name
                metric_type = recent_metrics[0].metric_type
                
                if metric_type == MetricType.COUNTER:
                    summary[key] = {
                        'type': 'counter',
                        'current': recent_metrics[-1].value,
                        'total_increase': recent_metrics[-1].value - (recent_metrics[0].value if len(recent_metrics) > 1 else 0)
                    }
                elif metric_type == MetricType.GAUGE:
                    values = [m.value for m in recent_metrics]
                    summary[key] = {
                        'type': 'gauge',
                        'current': values[-1],
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values)
                    }
                elif metric_type == MetricType.HISTOGRAM:
                    values = [m.value for m in recent_metrics]
                    values.sort()
                    n = len(values)
                    summary[key] = {
                        'type': 'histogram',
                        'count': n,
                        'min': values[0],
                        'max': values[-1],
                        'avg': sum(values) / n,
                        'p50': values[n // 2],
                        'p95': values[int(n * 0.95)] if n > 20 else values[-1],
                        'p99': values[int(n * 0.99)] if n > 100 else values[-1]
                    }
                    
        return summary

class HealthChecker:
    """Health check system for monitoring service health"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.results: Dict[str, HealthCheckResult] = {}
        self._lock = threading.RLock()
        
    def register_check(self, name: str, check_func: Callable[[], HealthCheckResult]):
        """Register health check function"""
        with self._lock:
            self.checks[name] = check_func
            
    def run_check(self, name: str) -> HealthCheckResult:
        """Run specific health check"""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check '{name}' not found"
            )
            
        start_time = time.time()
        try:
            result = self.checks[name]()
            result.response_time_ms = (time.time() - start_time) * 1000
            
            with self._lock:
                self.results[name] = result
                
            return result
            
        except Exception as e:
            result = HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
            
            with self._lock:
                self.results[name] = result
                
            return result
            
    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks"""
        results = {}
        
        for name in self.checks:
            results[name] = self.run_check(name)
            
        return results
        
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""
        if not self.results:
            return HealthStatus.UNKNOWN
            
        unhealthy_count = sum(1 for r in self.results.values() if r.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for r in self.results.values() if r.status == HealthStatus.DEGRADED)
        
        if unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

class SystemMetrics:
    """Collects system-level metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.collect_thread = threading.Thread(target=self._collect_worker, daemon=True)
        self.collect_thread.start()
        
    def _collect_worker(self):
        """Background worker to collect system metrics"""
        while True:
            try:
                self.collect_system_metrics()
                time.sleep(30)  # Collect every 30 seconds
            except Exception as e:
                logging.error(f"System metrics collection failed: {e}")
                
    def collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.gauge("system.cpu.usage_percent", cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics.gauge("system.memory.usage_percent", memory.percent)
            self.metrics.gauge("system.memory.available_bytes", memory.available)
            self.metrics.gauge("system.memory.used_bytes", memory.used)
            
            # Disk metrics
            disk = psutil.disk_usage('.')
            self.metrics.gauge("system.disk.usage_percent", (disk.used / disk.total) * 100)
            self.metrics.gauge("system.disk.free_bytes", disk.free)
            
            # Network metrics (if available)
            try:
                net_io = psutil.net_io_counters()
                self.metrics.gauge("system.network.bytes_sent", net_io.bytes_sent)
                self.metrics.gauge("system.network.bytes_recv", net_io.bytes_recv)
            except:
                pass
                
            # Process metrics
            process = psutil.Process()
            self.metrics.gauge("process.memory.rss_bytes", process.memory_info().rss)
            self.metrics.gauge("process.cpu.usage_percent", process.cpu_percent())
            self.metrics.gauge("process.threads.count", process.num_threads())
            
        except Exception as e:
            logging.error(f"Failed to collect system metrics: {e}")

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        
        # Start alert checking thread
        self.check_thread = threading.Thread(target=self._check_worker, daemon=True)
        self.check_thread.start()
        
    def register_alert(self, alert: Alert):
        """Register new alert"""
        with self._lock:
            self.alerts[alert.name] = alert
            
    def _check_worker(self):
        """Background worker to check alerts"""
        while True:
            try:
                self.check_alerts()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logging.error(f"Alert checking failed: {e}")
                
    def check_alerts(self):
        """Check all registered alerts"""
        current_time = datetime.now()
        
        with self._lock:
            for alert_name, alert in self.alerts.items():
                try:
                    # Skip if in cooldown period
                    if (alert.last_triggered and 
                        current_time - alert.last_triggered < timedelta(minutes=alert.cooldown_minutes)):
                        continue
                        
                    # Get recent metrics for evaluation
                    metrics_summary = self.metrics.get_metrics_summary(hours=1)
                    
                    # Check condition
                    if alert.condition(metrics_summary):
                        if not alert.is_active:
                            # Alert triggered
                            alert.is_active = True
                            alert.last_triggered = current_time
                            alert.trigger_count += 1
                            
                            self._send_alert(alert, metrics_summary)
                    else:
                        if alert.is_active:
                            # Alert resolved
                            alert.is_active = False
                            self._send_alert_resolved(alert)
                            
                except Exception as e:
                    logging.error(f"Error checking alert {alert_name}: {e}")
                    
    def _send_alert(self, alert: Alert, context: Dict[str, Any]):
        """Send alert notification"""
        alert_data = {
            'name': alert.name,
            'message': alert.message,
            'severity': alert.severity,
            'timestamp': datetime.now().isoformat(),
            'trigger_count': alert.trigger_count,
            'context': context
        }
        
        # Log alert
        logging.warning(f"ALERT: {alert.name} - {alert.message}", extra={'alert_data': alert_data})
        
        # Add to history
        self.alert_history.append(alert_data)
        
        # Keep only recent alerts (last 1000)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
            
    def _send_alert_resolved(self, alert: Alert):
        """Send alert resolution notification"""
        resolved_data = {
            'name': alert.name,
            'message': f"Alert '{alert.name}' has been resolved",
            'severity': 'info',
            'timestamp': datetime.now().isoformat()
        }
        
        logging.info(f"RESOLVED: {alert.name}", extra={'alert_data': resolved_data})

class ProductionMonitor:
    """Main production monitoring system"""
    
    def __init__(self):
        self.logger = StructuredLogger()
        self.metrics = MetricsCollector()
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager(self.metrics)
        self.system_metrics = SystemMetrics(self.metrics)
        
        # Setup default health checks
        self.setup_default_health_checks()
        
        # Setup default alerts
        self.setup_default_alerts()
        
    def setup_default_health_checks(self):
        """Setup default health checks"""
        def check_system_resources():
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = (psutil.disk_usage('.').used / psutil.disk_usage('.').total) * 100
            
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High resource usage: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_percent}%"
            elif cpu_percent > 70 or memory_percent > 70 or disk_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Elevated resource usage: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Resource usage normal: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_percent}%"
                
            return HealthCheckResult(
                name="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent
                }
            )
            
        self.health_checker.register_check("system_resources", check_system_resources)
        
    def setup_default_alerts(self):
        """Setup default alerts"""
        # High CPU alert
        cpu_alert = Alert(
            name="high_cpu_usage",
            condition=lambda metrics: any(
                m.get('current', 0) > 85 for k, m in metrics.items() 
                if 'system.cpu.usage_percent' in k
            ),
            message="CPU usage is critically high",
            severity="critical"
        )
        self.alert_manager.register_alert(cpu_alert)
        
        # High memory alert
        memory_alert = Alert(
            name="high_memory_usage",
            condition=lambda metrics: any(
                m.get('current', 0) > 90 for k, m in metrics.items()
                if 'system.memory.usage_percent' in k
            ),
            message="Memory usage is critically high",
            severity="critical"
        )
        self.alert_manager.register_alert(memory_alert)
        
    def get_status_dashboard(self) -> Dict[str, Any]:
        """Get complete system status dashboard"""
        health_results = self.health_checker.run_all_checks()
        overall_status = self.health_checker.get_overall_status()
        metrics_summary = self.metrics.get_metrics_summary(hours=1)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status.value,
            'health_checks': {name: asdict(result) for name, result in health_results.items()},
            'metrics': metrics_summary,
            'active_alerts': [
                alert.name for alert in self.alert_manager.alerts.values() 
                if alert.is_active
            ],
            'system_info': {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'hostname': socket.gethostname(),
                'uptime_seconds': time.time() - psutil.boot_time()
            }
        }

# Global monitoring instance
_monitor: Optional[ProductionMonitor] = None

def get_monitor() -> ProductionMonitor:
    """Get global monitoring instance"""
    global _monitor
    if _monitor is None:
        _monitor = ProductionMonitor()
    return _monitor

def setup_monitoring():
    """Initialize monitoring system"""
    monitor = get_monitor()
    logging.info("Production monitoring system initialized")
    return monitor

# Initialize monitoring on module import
setup_monitoring()