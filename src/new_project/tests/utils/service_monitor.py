#!/usr/bin/env python3
"""
Service Health Monitoring System for Kailash SDK Test Infrastructure
====================================================================

This module provides comprehensive service health monitoring, automated
startup, and recovery for the Docker-based test infrastructure.

CRITICAL: Implements NO MOCKING policy by ensuring real services are
always available for Tier 2 (Integration) and Tier 3 (E2E) tests.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import socket
import requests
import psycopg2
from redis import Redis
import neo4j
import chromadb


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceHealth:
    """Service health status information."""
    name: str
    status: str  # 'healthy', 'unhealthy', 'starting', 'stopped', 'unknown'
    port: int
    host: str = "localhost"
    response_time_ms: Optional[float] = None
    last_check: Optional[float] = None
    error_message: Optional[str] = None
    uptime_seconds: Optional[float] = None
    restart_count: int = 0


class ServiceMonitor:
    """
    Comprehensive service health monitoring and management system.
    
    This class provides:
    1. Real-time health monitoring for all test services
    2. Automated service startup and recovery
    3. Performance monitoring and SLA validation
    4. Cross-platform network configuration
    5. Service dependency management
    """
    
    def __init__(self, compose_file: str = "docker-compose.test.yml"):
        """Initialize the service monitor."""
        self.compose_file = compose_file
        self.project_root = self._find_project_root()
        self.compose_path = os.path.join(self.project_root, compose_file)
        
        # Service configurations
        self.services = {
            "postgresql": {
                "port": 5432,
                "health_check": self._check_postgresql,
                "startup_timeout": 60,
                "dependencies": [],
                "critical": True
            },
            "neo4j": {
                "port": 7474,
                "bolt_port": 7687,
                "health_check": self._check_neo4j,
                "startup_timeout": 120,
                "dependencies": [],
                "critical": True
            },
            "chromadb": {
                "port": 8000,
                "health_check": self._check_chromadb,
                "startup_timeout": 45,
                "dependencies": [],
                "critical": True
            },
            "redis": {
                "port": 6379,
                "health_check": self._check_redis,
                "startup_timeout": 30,
                "dependencies": [],
                "critical": True
            },
            "elasticsearch": {
                "port": 9200,
                "health_check": self._check_elasticsearch,
                "startup_timeout": 180,
                "dependencies": [],
                "critical": True
            },
            "minio": {
                "port": 9000,
                "admin_port": 9001,
                "health_check": self._check_minio,
                "startup_timeout": 45,
                "dependencies": [],
                "critical": False
            }
        }
        
        # Monitoring state
        self.service_health: Dict[str, ServiceHealth] = {}
        self.monitoring_active = False
        self.auto_recovery_enabled = True
        self.performance_history: Dict[str, List[float]] = {}
    
    def _find_project_root(self) -> str:
        """Find the project root directory."""
        current_dir = Path(__file__).parent
        while current_dir != current_dir.parent:
            if (current_dir / "docker-compose.test.yml").exists():
                return str(current_dir)
            current_dir = current_dir.parent
        return str(Path(__file__).parent.parent)
    
    async def start_all_services(self, 
                                services: Optional[List[str]] = None,
                                wait_for_health: bool = True) -> bool:
        """
        Start all required services with dependency management.
        
        Args:
            services: Specific services to start (default: all core services)
            wait_for_health: Wait for services to become healthy
            
        Returns:
            bool: True if all services started successfully
        """
        target_services = services or list(self.services.keys())
        logger.info(f"Starting services: {target_services}")
        
        try:
            # Start services using docker-compose
            cmd = [
                "docker-compose", "-f", self.compose_path,
                "up", "-d"
            ] + target_services
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to start services: {result.stderr}")
                return False
            
            logger.info("Docker services started, waiting for health checks...")
            
            if wait_for_health:
                return await self.wait_for_all_healthy(target_services, timeout=300)
            else:
                return True
                
        except Exception as e:
            logger.error(f"Error starting services: {e}")
            return False
    
    async def wait_for_all_healthy(self, 
                                 services: List[str], 
                                 timeout: int = 300) -> bool:
        """
        Wait for all services to become healthy.
        
        Args:
            services: List of service names to wait for
            timeout: Maximum wait time in seconds
            
        Returns:
            bool: True if all services are healthy within timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            health_status = await self.check_all_services(services)
            
            unhealthy_services = [
                name for name, health in health_status.items()
                if health.status != 'healthy'
            ]
            
            if not unhealthy_services:
                elapsed = time.time() - start_time
                logger.info(f"All services healthy after {elapsed:.1f}s")
                return True
            
            logger.info(f"Waiting for services: {unhealthy_services}")
            await asyncio.sleep(5)
        
        logger.error(f"Services not healthy within {timeout}s")
        return False
    
    async def check_all_services(self, 
                               services: Optional[List[str]] = None) -> Dict[str, ServiceHealth]:
        """
        Check health of all specified services.
        
        Args:
            services: Services to check (default: all services)
            
        Returns:
            dict: Service name -> ServiceHealth mapping
        """
        target_services = services or list(self.services.keys())
        
        # Run health checks concurrently
        tasks = []
        for service_name in target_services:
            if service_name in self.services:
                task = asyncio.create_task(
                    self._run_health_check(service_name)
                )
                tasks.append((service_name, task))
        
        # Collect results
        health_results = {}
        for service_name, task in tasks:
            try:
                health_results[service_name] = await task
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                health_results[service_name] = ServiceHealth(
                    name=service_name,
                    status='unknown',
                    port=self.services[service_name]['port'],
                    error_message=str(e)
                )
        
        # Update internal state
        self.service_health.update(health_results)
        return health_results
    
    async def _run_health_check(self, service_name: str) -> ServiceHealth:
        """Run health check for a specific service."""
        service_config = self.services[service_name]
        start_time = time.time()
        
        try:
            # Run the health check function
            is_healthy = await asyncio.get_event_loop().run_in_executor(
                None, service_config['health_check']
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Track performance history
            if service_name not in self.performance_history:
                self.performance_history[service_name] = []
            self.performance_history[service_name].append(response_time)
            
            # Keep only last 100 measurements
            if len(self.performance_history[service_name]) > 100:
                self.performance_history[service_name] = \
                    self.performance_history[service_name][-100:]
            
            return ServiceHealth(
                name=service_name,
                status='healthy' if is_healthy else 'unhealthy',
                port=service_config['port'],
                response_time_ms=response_time,
                last_check=time.time()
            )
            
        except Exception as e:
            return ServiceHealth(
                name=service_name,
                status='unhealthy',
                port=service_config['port'],
                error_message=str(e),
                last_check=time.time()
            )
    
    async def start_monitoring(self, interval: int = 30):
        """
        Start continuous service monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        self.monitoring_active = True
        logger.info(f"Starting service monitoring (interval: {interval}s)")
        
        while self.monitoring_active:
            try:
                health_status = await self.check_all_services()
                
                # Check for unhealthy services
                unhealthy_services = [
                    name for name, health in health_status.items()
                    if health.status == 'unhealthy' and self.services[name].get('critical', False)
                ]
                
                if unhealthy_services and self.auto_recovery_enabled:
                    logger.warning(f"Unhealthy services detected: {unhealthy_services}")
                    await self._attempt_recovery(unhealthy_services)
                
                # Log status summary
                healthy_count = sum(1 for h in health_status.values() if h.status == 'healthy')
                total_count = len(health_status)
                logger.info(f"Service health: {healthy_count}/{total_count} services healthy")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval)
    
    async def _attempt_recovery(self, unhealthy_services: List[str]):
        """
        Attempt to recover unhealthy services.
        
        Args:
            unhealthy_services: List of service names to recover
        """
        logger.info(f"Attempting recovery for services: {unhealthy_services}")
        
        for service_name in unhealthy_services:
            try:
                # Restart the specific service
                cmd = [
                    "docker-compose", "-f", self.compose_path,
                    "restart", service_name
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                
                if result.returncode == 0:
                    logger.info(f"Restarted service: {service_name}")
                    
                    # Update restart count
                    if service_name in self.service_health:
                        self.service_health[service_name].restart_count += 1
                else:
                    logger.error(f"Failed to restart {service_name}: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Recovery failed for {service_name}: {e}")
    
    def stop_monitoring(self):
        """Stop service monitoring."""
        self.monitoring_active = False
        logger.info("Service monitoring stopped")
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance statistics for all services.
        
        Returns:
            dict: Service performance statistics
        """
        stats = {}
        
        for service_name, measurements in self.performance_history.items():
            if measurements:
                stats[service_name] = {
                    'avg_response_time_ms': sum(measurements) / len(measurements),
                    'min_response_time_ms': min(measurements),
                    'max_response_time_ms': max(measurements),
                    'measurements_count': len(measurements)
                }
        
        return stats
    
    def export_health_report(self, filename: Optional[str] = None) -> str:
        """
        Export comprehensive health report.
        
        Args:
            filename: Output filename (default: auto-generated)
            
        Returns:
            str: Path to the exported report
        """
        if not filename:
            timestamp = int(time.time())
            filename = f"service_health_report_{timestamp}.json"
        
        report = {
            'timestamp': time.time(),
            'services': {
                name: asdict(health) 
                for name, health in self.service_health.items()
            },
            'performance_stats': self.get_performance_stats(),
            'infrastructure_config': {
                'compose_file': self.compose_file,
                'monitoring_active': self.monitoring_active,
                'auto_recovery_enabled': self.auto_recovery_enabled
            }
        }
        
        filepath = os.path.join(self.project_root, filename)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Health report exported to: {filepath}")
        return filepath
    
    # Service-specific health check methods
    def _check_postgresql(self) -> bool:
        """Check PostgreSQL health."""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="test_user",
                password="test_password",
                database="test_horme_db",
                connect_timeout=5
            )
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            conn.close()
            return result[0] == 1
        except Exception:
            return False
    
    def _check_neo4j(self) -> bool:
        """Check Neo4j health."""
        try:
            driver = neo4j.GraphDatabase.driver(
                "bolt://localhost:7687",
                auth=("neo4j", "testpassword"),
                connection_timeout=10
            )
            with driver.session() as session:
                result = session.run("RETURN 1 as health")
                record = result.single()
            driver.close()
            return record["health"] == 1
        except Exception:
            return False
    
    def _check_chromadb(self) -> bool:
        """Check ChromaDB health."""
        try:
            response = requests.get(
                "http://localhost:8000/api/v1/heartbeat",
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _check_redis(self) -> bool:
        """Check Redis health."""
        try:
            client = Redis(
                host="localhost",
                port=6379,
                password="testredispass",
                socket_timeout=5,
                socket_connect_timeout=5
            )
            response = client.ping()
            client.close()
            return response is True
        except Exception:
            return False
    
    def _check_elasticsearch(self) -> bool:
        """Check Elasticsearch health."""
        try:
            response = requests.get(
                "http://localhost:9200/_cluster/health",
                timeout=15
            )
            if response.status_code == 200:
                health_data = response.json()
                return health_data.get('status') in ['green', 'yellow']
            return False
        except Exception:
            return False
    
    def _check_minio(self) -> bool:
        """Check MinIO health."""
        try:
            response = requests.get(
                "http://localhost:9000/minio/health/live",
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False


async def main():
    """Main CLI entry point for service monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Kailash SDK Service Health Monitor"
    )
    parser.add_argument(
        "--start", 
        action="store_true",
        help="Start all services and begin monitoring"
    )
    parser.add_argument(
        "--check", 
        action="store_true",
        help="Check health of all services once"
    )
    parser.add_argument(
        "--monitor", 
        type=int, 
        default=0,
        help="Start continuous monitoring (interval in seconds)"
    )
    parser.add_argument(
        "--services", 
        nargs="*",
        help="Specific services to target"
    )
    parser.add_argument(
        "--export-report", 
        action="store_true",
        help="Export health report to JSON"
    )
    
    args = parser.parse_args()
    
    monitor = ServiceMonitor()
    
    if args.start:
        success = await monitor.start_all_services(args.services)
        if success:
            print("✅ All services started successfully")
        else:
            print("❌ Failed to start some services")
            return 1
    
    if args.check:
        health_status = await monitor.check_all_services(args.services)
        
        print("\n=== Service Health Status ===")
        for name, health in health_status.items():
            status_emoji = "✅" if health.status == "healthy" else "❌"
            response_time = f" ({health.response_time_ms:.1f}ms)" if health.response_time_ms else ""
            print(f"{status_emoji} {name}: {health.status}{response_time}")
        
        unhealthy_count = sum(1 for h in health_status.values() if h.status != 'healthy')
        if unhealthy_count == 0:
            print("\n🎉 All services are healthy!")
        else:
            print(f"\n⚠️  {unhealthy_count} services are unhealthy")
    
    if args.monitor > 0:
        try:
            await monitor.start_monitoring(args.monitor)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\n👋 Monitoring stopped")
    
    if args.export_report:
        report_path = monitor.export_health_report()
        print(f"📊 Health report exported: {report_path}")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)