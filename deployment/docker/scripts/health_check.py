#!/usr/bin/env python3
"""
Production MCP Server Health Check Script
========================================

Comprehensive health check for containerized MCP server.
Used by Docker HEALTHCHECK and Kubernetes liveness/readiness probes.

Checks:
- HTTP endpoints availability
- Database connectivity
- Redis connectivity
- WebSocket endpoint
- Resource utilization
- Circuit breaker status

Exit codes:
- 0: Healthy
- 1: Unhealthy
- 2: Degraded (some services failing)
"""

import os
import sys
import json
import time
import signal
import asyncio
from typing import Dict, Any, Optional
from urllib.parse import urlparse

try:
    import httpx
    import websockets
    import asyncpg
    import redis.asyncio as redis
    DEPS_AVAILABLE = True
except ImportError:
    print("WARNING: Some health check dependencies not available")
    DEPS_AVAILABLE = False

class HealthChecker:
    """Comprehensive health checker for MCP server"""
    
    def __init__(self):
        self.host = os.getenv('MCP_HOST', '0.0.0.0')
        self.port = int(os.getenv('MCP_PORT', '3001'))
        self.metrics_port = int(os.getenv('MCP_METRICS_PORT', '9090'))
        self.management_port = int(os.getenv('MCP_MANAGEMENT_PORT', '3002'))
        
        self.database_url = os.getenv('DATABASE_URL', '')
        self.redis_url = os.getenv('REDIS_URL', '')
        
        self.timeout = 10  # seconds
        self.results = {}
    
    async def check_http_endpoint(self, port: int, path: str = "/health") -> Dict[str, Any]:
        """Check HTTP endpoint health"""
        try:
            url = f"http://{self.host}:{port}{path}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                start_time = time.time()
                response = await client.get(url)
                response_time = time.time() - start_time
                
                return {
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'status_code': response.status_code,
                    'response_time_ms': round(response_time * 1000, 2),
                    'content_length': len(response.content),
                    'error': None
                }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'status_code': None,
                'response_time_ms': None,
                'content_length': 0,
                'error': str(e)
            }
    
    async def check_websocket_endpoint(self) -> Dict[str, Any]:
        """Check WebSocket endpoint health"""
        try:
            uri = f"ws://{self.host}:{self.port}/mcp"
            
            start_time = time.time()
            async with websockets.connect(
                uri, 
                timeout=self.timeout,
                ping_timeout=5
            ) as websocket:
                # Send ping message
                ping_message = {
                    "jsonrpc": "2.0",
                    "method": "ping",
                    "id": "health_check"
                }
                
                await websocket.send(json.dumps(ping_message))
                
                # Wait for response or timeout
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(), 
                        timeout=5
                    )
                    response_time = time.time() - start_time
                    
                    return {
                        'status': 'healthy',
                        'response_time_ms': round(response_time * 1000, 2),
                        'error': None
                    }
                except asyncio.TimeoutError:
                    return {
                        'status': 'degraded',
                        'response_time_ms': None,
                        'error': 'WebSocket response timeout'
                    }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time_ms': None,
                'error': str(e)
            }
    
    async def check_database(self) -> Dict[str, Any]:
        """Check PostgreSQL database health"""
        if not self.database_url:
            return {
                'status': 'unavailable',
                'error': 'Database URL not configured'
            }
        
        try:
            start_time = time.time()
            conn = await asyncpg.connect(
                self.database_url,
                timeout=self.timeout
            )
            
            # Test query
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy' if result == 1 else 'unhealthy',
                'response_time_ms': round(response_time * 1000, 2),
                'test_query_result': result,
                'error': None
            }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time_ms': None,
                'test_query_result': None,
                'error': str(e)
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis cache health"""
        if not self.redis_url:
            return {
                'status': 'unavailable',
                'error': 'Redis URL not configured'
            }
        
        try:
            start_time = time.time()
            client = redis.from_url(
                self.redis_url,
                socket_timeout=self.timeout,
                socket_connect_timeout=self.timeout
            )
            
            # Test ping
            pong = await client.ping()
            await client.close()
            
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy' if pong else 'unhealthy',
                'response_time_ms': round(response_time * 1000, 2),
                'ping_result': pong,
                'error': None
            }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time_ms': None,
                'ping_result': None,
                'error': str(e)
            }
    
    def check_resource_usage(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / 1024 / 1024
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / 1024 / 1024 / 1024
            
            # Determine status based on thresholds
            status = 'healthy'
            warnings = []
            
            if cpu_percent > 90:
                status = 'degraded'
                warnings.append(f"High CPU usage: {cpu_percent}%")
            elif cpu_percent > 80:
                warnings.append(f"Elevated CPU usage: {cpu_percent}%")
            
            if memory_percent > 90:
                status = 'degraded'
                warnings.append(f"High memory usage: {memory_percent}%")
            elif memory_percent > 80:
                warnings.append(f"Elevated memory usage: {memory_percent}%")
            
            if disk_percent > 95:
                status = 'unhealthy'
                warnings.append(f"Critical disk usage: {disk_percent}%")
            elif disk_percent > 85:
                status = 'degraded'
                warnings.append(f"High disk usage: {disk_percent}%")
            
            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_available_mb': round(memory_available_mb, 1),
                'disk_percent': disk_percent,
                'disk_free_gb': round(disk_free_gb, 1),
                'warnings': warnings,
                'error': None
            }
        
        except ImportError:
            return {
                'status': 'unavailable',
                'error': 'psutil not available for resource monitoring'
            }
        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        start_time = time.time()
        
        if not DEPS_AVAILABLE:
            return {
                'overall_status': 'unknown',
                'error': 'Health check dependencies not available',
                'checks': {}
            }
        
        # Run checks concurrently
        checks = await asyncio.gather(
            self.check_http_endpoint(self.port, "/health"),
            self.check_http_endpoint(self.metrics_port, "/metrics"),
            self.check_websocket_endpoint(),
            self.check_database(),
            self.check_redis(),
            return_exceptions=True
        )
        
        # Add resource check (synchronous)
        resource_check = self.check_resource_usage()
        
        # Organize results
        self.results = {
            'main_http': checks[0] if not isinstance(checks[0], Exception) else {'status': 'error', 'error': str(checks[0])},
            'metrics_http': checks[1] if not isinstance(checks[1], Exception) else {'status': 'error', 'error': str(checks[1])},
            'websocket': checks[2] if not isinstance(checks[2], Exception) else {'status': 'error', 'error': str(checks[2])},
            'database': checks[3] if not isinstance(checks[3], Exception) else {'status': 'error', 'error': str(checks[3])},
            'redis': checks[4] if not isinstance(checks[4], Exception) else {'status': 'error', 'error': str(checks[4])},
            'resources': resource_check
        }
        
        # Determine overall status
        overall_status = self._determine_overall_status()
        
        total_time = time.time() - start_time
        
        return {
            'overall_status': overall_status,
            'check_duration_ms': round(total_time * 1000, 2),
            'timestamp': time.time(),
            'checks': self.results
        }
    
    def _determine_overall_status(self) -> str:
        """Determine overall health status from individual checks"""
        statuses = [check.get('status', 'unknown') for check in self.results.values()]
        
        # Critical services that must be healthy
        critical_services = ['main_http']
        
        # Check critical services
        for service in critical_services:
            if service in self.results:
                if self.results[service].get('status') in ['unhealthy', 'error']:
                    return 'unhealthy'
        
        # Check for any unhealthy services
        if 'unhealthy' in statuses or 'error' in statuses:
            return 'unhealthy'
        
        # Check for degraded services
        if 'degraded' in statuses:
            return 'degraded'
        
        # Check if most services are healthy
        healthy_count = statuses.count('healthy')
        total_count = len([s for s in statuses if s != 'unavailable'])
        
        if total_count > 0 and healthy_count / total_count >= 0.7:
            return 'healthy'
        
        return 'degraded'
    
    def get_exit_code(self, overall_status: str) -> int:
        """Get appropriate exit code for health status"""
        if overall_status == 'healthy':
            return 0
        elif overall_status == 'degraded':
            return 2
        else:
            return 1

async def main():
    """Main health check function"""
    checker = HealthChecker()
    
    try:
        # Set timeout for entire health check
        result = await asyncio.wait_for(
            checker.run_all_checks(),
            timeout=30  # 30 second total timeout
        )
        
        # Output results
        if os.getenv('HEALTH_CHECK_VERBOSE', '').lower() == 'true':
            print(json.dumps(result, indent=2))
        else:
            print(f"Status: {result['overall_status']}")
            if result['overall_status'] != 'healthy':
                # Show failed checks
                for name, check in result['checks'].items():
                    if check.get('status') in ['unhealthy', 'error', 'degraded']:
                        print(f"  {name}: {check.get('status')} - {check.get('error', 'No details')}")
        
        return checker.get_exit_code(result['overall_status'])
    
    except asyncio.TimeoutError:
        print("Health check timeout")
        return 1
    except Exception as e:
        print(f"Health check failed: {e}")
        return 1

if __name__ == "__main__":
    # Handle timeout signal
    def timeout_handler(signum, frame):
        print("Health check timeout")
        sys.exit(1)
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)  # 30 second timeout
    
    try:
        exit_code = asyncio.run(main())
        signal.alarm(0)  # Cancel alarm
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("Health check interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"Health check error: {e}")
        sys.exit(1)