"""
Production Monitoring and Health Check System for Nexus Platform
===============================================================

Comprehensive monitoring system with:
- Health checks for all system components
- Performance metrics collection
- Alert system with notifications
- Prometheus metrics export
- System resource monitoring
- Database connection monitoring
"""

import asyncio
import psutil
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from nexus_enhanced_config import enhanced_config
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    response_time_ms: float
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "response_time_ms": self.response_time_ms,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class MetricPoint:
    """Single metric measurement"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels
        }

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Alert:
    """System alert"""
    id: str
    level: AlertLevel
    title: str
    message: str
    component: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }

class HealthChecker:
    """Health check system for monitoring system components"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.results: Dict[str, HealthCheckResult] = {}
        self.check_interval = enhanced_config.health_check.health_check_interval
        self.running = False
        self.check_task: Optional[asyncio.Task] = None
        
        # Register default health checks
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks"""
        if enhanced_config.health_check.check_database:
            self.register_check("database", self._check_database)
        
        if enhanced_config.health_check.check_redis and enhanced_config.redis.enabled:
            self.register_check("redis", self._check_redis)
        
        if enhanced_config.health_check.check_external_apis:
            self.register_check("external_apis", self._check_external_apis)
        
        self.register_check("system_resources", self._check_system_resources)
        self.register_check("disk_space", self._check_disk_space)
        self.register_check("memory_usage", self._check_memory_usage)
        self.register_check("cpu_usage", self._check_cpu_usage)
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    async def run_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check"""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                response_time_ms=0,
                message=f"Check '{name}' not found"
            )
        
        start_time = time.time()
        try:
            result = await self.checks[name]()
            response_time = (time.time() - start_time) * 1000
            
            if isinstance(result, HealthCheckResult):
                result.response_time_ms = response_time
                return result
            else:
                # Assume boolean result
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message="OK" if result else "Check failed"
                )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Health check '{name}' failed: {e}")
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Error: {str(e)}"
            )
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks"""
        tasks = {name: self.run_check(name) for name in self.checks.keys()}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        check_results = {}
        for name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                check_results[name] = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    message=f"Check failed: {str(result)}"
                )
            else:
                check_results[name] = result
        
        self.results = check_results
        return check_results
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.running:
            return
        
        self.running = True
        self.check_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        if not self.running:
            return
        
        self.running = False
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.running:
            try:
                await self.run_all_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""
        if not self.results:
            return HealthStatus.UNKNOWN
        
        statuses = [result.status for result in self.results.values()]
        
        if any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    # Default health check implementations
    async def _check_database(self) -> HealthCheckResult:
        """Check database connectivity and performance"""
        try:
            from dataflow_models import db
            
            runtime = LocalRuntime()
            workflow = WorkflowBuilder()
            workflow.add_node("AsyncSQLQueryNode", "db_health", {
                "query": "SELECT 1 as healthy, NOW() as timestamp, pg_database_size(current_database()) as db_size",
                "parameters": {},
                "connection_pool": db.connection_pool
            })
            
            start_time = time.time()
            results, _ = runtime.execute(workflow.build())
            query_time = (time.time() - start_time) * 1000
            
            db_result = results.get("db_health", [])
            if db_result:
                db_size_mb = db_result[0].get("db_size", 0) / (1024 * 1024)
                
                return HealthCheckResult(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=query_time,
                    message=f"Database responsive (query: {query_time:.1f}ms)",
                    details={
                        "query_time_ms": query_time,
                        "database_size_mb": round(db_size_mb, 2),
                        "connection_pool_active": True
                    }
                )
            else:
                return HealthCheckResult(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=query_time,
                    message="Database query returned no results"
                )
        
        except Exception as e:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"Database connection failed: {str(e)}"
            )
    
    async def _check_redis(self) -> HealthCheckResult:
        """Check Redis connectivity"""
        try:
            import redis.asyncio as redis
            
            redis_client = redis.from_url(enhanced_config.redis.url)
            start_time = time.time()
            
            # Test basic operations
            await redis_client.set("health_check", "ok", ex=60)
            result = await redis_client.get("health_check")
            ping_result = await redis_client.ping()
            
            response_time = (time.time() - start_time) * 1000
            
            if result == b"ok" and ping_result:
                info = await redis_client.info()
                return HealthCheckResult(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message=f"Redis responsive (ping: {response_time:.1f}ms)",
                    details={
                        "ping_time_ms": response_time,
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory_mb": info.get("used_memory", 0) / (1024 * 1024),
                        "redis_version": info.get("redis_version", "unknown")
                    }
                )
            else:
                return HealthCheckResult(
                    name="redis",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message="Redis operations failed"
                )
        
        except Exception as e:
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"Redis connection failed: {str(e)}"
            )
    
    async def _check_external_apis(self) -> HealthCheckResult:
        """Check external API connectivity"""
        # This is a placeholder - implement based on your external dependencies
        return HealthCheckResult(
            name="external_apis",
            status=HealthStatus.HEALTHY,
            response_time_ms=0,
            message="No external APIs configured"
        )
    
    async def _check_system_resources(self) -> HealthCheckResult:
        """Check overall system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            messages = []
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 70:
                status = HealthStatus.DEGRADED
                messages.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
            
            if memory_percent > 90:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High memory usage: {memory_percent:.1f}%")
            elif memory_percent > 70:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
                messages.append(f"Elevated memory usage: {memory_percent:.1f}%")
            
            if disk_percent > 95:
                status = HealthStatus.UNHEALTHY
                messages.append(f"Low disk space: {disk_percent:.1f}% used")
            elif disk_percent > 80:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
                messages.append(f"Disk space warning: {disk_percent:.1f}% used")
            
            message = "; ".join(messages) if messages else "System resources within normal limits"
            
            return HealthCheckResult(
                name="system_resources",
                status=status,
                response_time_ms=1000,  # Approximate time for system calls
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "memory_total_gb": memory.total / (1024**3),
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_total_gb": disk.total / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                }
            )
        
        except Exception as e:
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"Failed to check system resources: {str(e)}"
            )
    
    async def _check_disk_space(self) -> HealthCheckResult:
        """Check disk space availability"""
        try:
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            free_gb = disk.free / (1024**3)
            
            if disk_percent > 95:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: Only {free_gb:.1f}GB free ({100-disk_percent:.1f}% free)"
            elif disk_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Warning: {free_gb:.1f}GB free ({100-disk_percent:.1f}% free)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Sufficient disk space: {free_gb:.1f}GB free ({100-disk_percent:.1f}% free)"
            
            return HealthCheckResult(
                name="disk_space",
                status=status,
                response_time_ms=10,
                message=message,
                details={
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": free_gb,
                    "percent_used": disk_percent
                }
            )
        
        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"Failed to check disk space: {str(e)}"
            )
    
    async def _check_memory_usage(self) -> HealthCheckResult:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            available_gb = memory.available / (1024**3)
            
            if memory_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: High memory usage {memory_percent:.1f}% (only {available_gb:.1f}GB available)"
            elif memory_percent > 75:
                status = HealthStatus.DEGRADED
                message = f"Warning: Elevated memory usage {memory_percent:.1f}% ({available_gb:.1f}GB available)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {memory_percent:.1f}% ({available_gb:.1f}GB available)"
            
            return HealthCheckResult(
                name="memory_usage",
                status=status,
                response_time_ms=5,
                message=message,
                details={
                    "total_gb": memory.total / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "available_gb": available_gb,
                    "percent_used": memory_percent,
                    "buffers_gb": memory.buffers / (1024**3),
                    "cached_gb": memory.cached / (1024**3)
                }
            )
        
        except Exception as e:
            return HealthCheckResult(
                name="memory_usage",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"Failed to check memory usage: {str(e)}"
            )
    
    async def _check_cpu_usage(self) -> HealthCheckResult:
        """Check CPU usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: High CPU usage {cpu_percent:.1f}%"
            elif cpu_percent > 70:
                status = HealthStatus.DEGRADED
                message = f"Warning: Elevated CPU usage {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_percent:.1f}%"
            
            return HealthCheckResult(
                name="cpu_usage",
                status=status,
                response_time_ms=1000,  # cpu_percent(interval=1) takes ~1 second
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "cpu_count": cpu_count,
                    "load_avg_1min": load_avg[0],
                    "load_avg_5min": load_avg[1],
                    "load_avg_15min": load_avg[2]
                }
            )
        
        except Exception as e:
            return HealthCheckResult(
                name="cpu_usage",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"Failed to check CPU usage: {str(e)}"
            )

class MetricsCollector:
    """Collect and export metrics for monitoring"""
    
    def __init__(self):
        self.metrics: List[MetricPoint] = []
        self.max_metrics = 10000  # Keep last 10k metrics
        self.collection_interval = enhanced_config.monitoring.metrics_interval
        self.running = False
        self.collection_task: Optional[asyncio.Task] = None
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a single metric point"""
        metric = MetricPoint(name=name, value=value, labels=labels or {})
        self.metrics.append(metric)
        
        # Keep only recent metrics
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
    
    async def start_collection(self):
        """Start automatic metrics collection"""
        if self.running:
            return
        
        self.running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collection started")
    
    async def stop_collection(self):
        """Stop metrics collection"""
        if not self.running:
            return
        
        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Metrics collection stopped")
    
    async def _collection_loop(self):
        """Continuous metrics collection loop"""
        while self.running:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(5)
    
    async def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent()
            self.record_metric("system_cpu_percent", cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.record_metric("system_memory_percent", memory.percent)
            self.record_metric("system_memory_used_bytes", memory.used)
            self.record_metric("system_memory_available_bytes", memory.available)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.record_metric("system_disk_percent", (disk.used / disk.total) * 100)
            self.record_metric("system_disk_used_bytes", disk.used)
            self.record_metric("system_disk_free_bytes", disk.free)
            
            # Process metrics
            process = psutil.Process()
            self.record_metric("process_cpu_percent", process.cpu_percent())
            self.record_metric("process_memory_percent", process.memory_percent())
            self.record_metric("process_memory_rss_bytes", process.memory_info().rss)
            
        except Exception as e:
            logger.error(f"System metrics collection error: {e}")
    
    def get_metrics(self, name: str = None, since: datetime = None) -> List[MetricPoint]:
        """Get metrics, optionally filtered by name and time"""
        filtered_metrics = self.metrics
        
        if name:
            filtered_metrics = [m for m in filtered_metrics if m.name == name]
        
        if since:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= since]
        
        return filtered_metrics
    
    def get_latest_metrics(self) -> Dict[str, float]:
        """Get latest value for each metric"""
        latest = {}
        for metric in reversed(self.metrics):
            if metric.name not in latest:
                latest[metric.name] = metric.value
        
        return latest
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        latest = self.get_latest_metrics()
        
        for name, value in latest.items():
            # Convert metric name to Prometheus format
            prom_name = name.replace('.', '_').replace('-', '_')
            lines.append(f"# TYPE {prom_name} gauge")
            lines.append(f"{prom_name} {value}")
        
        return '\n'.join(lines)

class AlertManager:
    """Manage system alerts and notifications"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[Callable] = []
        
        # Setup default handlers
        if enhanced_config.email.enabled:
            self.register_handler(self._send_email_alert)
        
        if enhanced_config.monitoring.alert_webhook_url:
            self.register_handler(self._send_webhook_alert)
    
    def register_handler(self, handler: Callable):
        """Register alert handler"""
        self.alert_handlers.append(handler)
    
    async def create_alert(self, alert_id: str, level: AlertLevel, title: str, 
                          message: str, component: str) -> Alert:
        """Create and process new alert"""
        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            component=component
        )
        
        self.alerts[alert_id] = alert
        
        # Send to handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
        
        logger.warning(f"Alert created: {alert.level.value.upper()} - {alert.title}")
        return alert
    
    async def resolve_alert(self, alert_id: str):
        """Resolve an existing alert"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            logger.info(f"Alert resolved: {alert.title}")
        else:
            logger.warning(f"Cannot resolve alert: {alert_id} not found")
    
    async def _send_email_alert(self, alert: Alert):
        """Send alert via email"""
        try:
            if not enhanced_config.email.enabled:
                return
            
            msg = MimeMultipart()
            msg['From'] = enhanced_config.email.from_address
            msg['To'] = ', '.join(enhanced_config.monitoring.alert_email_recipients)
            msg['Subject'] = f"[{alert.level.value.upper()}] {alert.title}"
            
            body = f"""
Alert Details:
- Level: {alert.level.value.upper()}
- Component: {alert.component}
- Time: {alert.timestamp.isoformat()}
- Message: {alert.message}

This is an automated alert from the Nexus Sales Assistant Platform.
"""
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(enhanced_config.email.smtp_host, enhanced_config.email.smtp_port)
            if enhanced_config.email.use_tls:
                server.starttls()
            
            if enhanced_config.email.smtp_username:
                server.login(enhanced_config.email.smtp_username, enhanced_config.email.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_webhook_alert(self, alert: Alert):
        """Send alert via webhook"""
        try:
            webhook_url = enhanced_config.monitoring.alert_webhook_url
            if not webhook_url:
                return
            
            payload = {
                "alert": alert.to_dict(),
                "platform": "nexus_sales_assistant",
                "environment": enhanced_config.environment
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent: {alert.title}")
                    else:
                        logger.warning(f"Webhook alert failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        active_alerts = self.get_active_alerts()
        
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
            "warning_alerts": len([a for a in active_alerts if a.level == AlertLevel.WARNING]),
            "info_alerts": len([a for a in active_alerts if a.level == AlertLevel.INFO]),
            "components_with_alerts": list(set(a.component for a in active_alerts))
        }

class NexusMonitoringSystem:
    """Main monitoring system coordinator"""
    
    def __init__(self):
        self.health_checker = HealthChecker()
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.running = False
        
        # Setup health check based alerting
        self._setup_health_alerting()
    
    def _setup_health_alerting(self):
        """Setup automatic alerting based on health checks"""
        # This would be called periodically to check health and create alerts
        pass
    
    async def start(self):
        """Start all monitoring components"""
        if self.running:
            return
        
        self.running = True
        
        await self.health_checker.start_monitoring()
        await self.metrics_collector.start_collection()
        
        logger.info("Nexus monitoring system started")
    
    async def stop(self):
        """Stop all monitoring components"""
        if not self.running:
            return
        
        self.running = False
        
        await self.health_checker.stop_monitoring()
        await self.metrics_collector.stop_collection()
        
        logger.info("Nexus monitoring system stopped")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        # Run fresh health checks
        health_results = await self.health_checker.run_all_checks()
        overall_status = self.health_checker.get_overall_status()
        
        # Get latest metrics
        latest_metrics = self.metrics_collector.get_latest_metrics()
        
        # Get alert summary
        alert_summary = self.alert_manager.get_alert_summary()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status.value,
            "health_checks": {name: result.to_dict() for name, result in health_results.items()},
            "metrics": latest_metrics,
            "alerts": alert_summary,
            "monitoring": {
                "health_check_interval": self.health_checker.check_interval,
                "metrics_collection_interval": self.metrics_collector.collection_interval,
                "total_metrics_collected": len(self.metrics_collector.metrics)
            }
        }

# Global monitoring system instance
monitoring_system = NexusMonitoringSystem()

# Export for use in main application
__all__ = [
    'HealthStatus',
    'HealthCheckResult',
    'MetricPoint',
    'AlertLevel',
    'Alert',
    'HealthChecker',
    'MetricsCollector',
    'AlertManager',
    'NexusMonitoringSystem',
    'monitoring_system'
]