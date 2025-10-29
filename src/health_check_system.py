"""
Comprehensive Health Check System for VM Infrastructure
Provides detailed health monitoring for all services with database connectivity validation
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import psycopg2
import redis
import requests
from urllib.parse import urlparse
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthCheckResult:
    def __init__(self, service_name: str, status: str, message: str, 
                 response_time_ms: float = 0, details: Dict = None):
        self.service_name = service_name
        self.status = status  # 'healthy', 'unhealthy', 'degraded'
        self.message = message
        self.response_time_ms = response_time_ms
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            'service_name': self.service_name,
            'status': self.status,
            'message': self.message,
            'response_time_ms': self.response_time_ms,
            'details': self.details,
            'timestamp': self.timestamp
        }

class DatabaseHealthChecker:
    """Specialized database connectivity checker with VM optimizations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        parsed = urlparse(database_url)
        self.connection_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:] if parsed.path else '',
            'user': parsed.username,
            'password': parsed.password,
            'connect_timeout': 10,
            'application_name': 'horme-health-check'
        }

    def check_connectivity(self) -> HealthCheckResult:
        """Test basic database connectivity"""
        start_time = time.time()
        try:
            conn = psycopg2.connect(**self.connection_params)
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
            conn.close()
            
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                'database_connectivity',
                'healthy',
                'Database connection successful',
                response_time,
                {'connection_time_ms': response_time}
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                'database_connectivity',
                'unhealthy',
                f'Database connection failed: {str(e)}',
                response_time,
                {'error': str(e)}
            )

    def check_performance(self) -> HealthCheckResult:
        """Test database performance with typical queries"""
        start_time = time.time()
        try:
            conn = psycopg2.connect(**self.connection_params)
            with conn.cursor() as cursor:
                # Test query performance
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_connections,
                        MAX(EXTRACT(EPOCH FROM (now() - query_start))) as longest_query_time
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """)
                stats = cursor.fetchone()
                
                # Test table access
                cursor.execute("""
                    SELECT schemaname, tablename, n_tup_ins + n_tup_upd + n_tup_del as total_operations
                    FROM pg_stat_user_tables 
                    ORDER BY total_operations DESC 
                    LIMIT 5
                """)
                table_stats = cursor.fetchall()
            
            conn.close()
            
            response_time = (time.time() - start_time) * 1000
            
            status = 'healthy'
            if response_time > 5000:  # 5 second threshold
                status = 'degraded'
            elif response_time > 10000:  # 10 second threshold
                status = 'unhealthy'
            
            return HealthCheckResult(
                'database_performance',
                status,
                f'Database performance check completed',
                response_time,
                {
                    'active_connections': stats[0] if stats else 0,
                    'longest_query_time': stats[1] if stats and stats[1] else 0,
                    'table_activity': [{'schema': t[0], 'table': t[1], 'operations': t[2]} for t in table_stats]
                }
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                'database_performance',
                'unhealthy',
                f'Database performance check failed: {str(e)}',
                response_time,
                {'error': str(e)}
            )

class RedisHealthChecker:
    """Redis connectivity and performance checker"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        parsed = urlparse(redis_url)
        self.redis_client = redis.Redis(
            host=parsed.hostname,
            port=parsed.port or 6379,
            password=parsed.password,
            socket_timeout=10,
            socket_connect_timeout=10,
            decode_responses=True
        )

    def check_connectivity(self) -> HealthCheckResult:
        """Test Redis connectivity"""
        start_time = time.time()
        try:
            response = self.redis_client.ping()
            response_time = (time.time() - start_time) * 1000
            
            if response:
                return HealthCheckResult(
                    'redis_connectivity',
                    'healthy',
                    'Redis connection successful',
                    response_time
                )
            else:
                return HealthCheckResult(
                    'redis_connectivity',
                    'unhealthy',
                    'Redis ping failed',
                    response_time
                )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                'redis_connectivity',
                'unhealthy',
                f'Redis connection failed: {str(e)}',
                response_time,
                {'error': str(e)}
            )

    def check_performance(self) -> HealthCheckResult:
        """Test Redis performance and memory usage"""
        start_time = time.time()
        try:
            info = self.redis_client.info()
            response_time = (time.time() - start_time) * 1000
            
            memory_used_mb = info.get('used_memory', 0) / 1024 / 1024
            memory_peak_mb = info.get('used_memory_peak', 0) / 1024 / 1024
            connected_clients = info.get('connected_clients', 0)
            
            status = 'healthy'
            if memory_used_mb > 200:  # 200MB threshold
                status = 'degraded'
            elif connected_clients > 50:  # 50 clients threshold
                status = 'degraded'
            
            return HealthCheckResult(
                'redis_performance',
                status,
                f'Redis performance check completed',
                response_time,
                {
                    'memory_used_mb': round(memory_used_mb, 2),
                    'memory_peak_mb': round(memory_peak_mb, 2),
                    'connected_clients': connected_clients,
                    'total_commands_processed': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                'redis_performance',
                'unhealthy',
                f'Redis performance check failed: {str(e)}',
                response_time,
                {'error': str(e)}
            )

class ServiceHealthChecker:
    """HTTP service health checker for API, MCP, and Nexus services"""
    
    def __init__(self, service_name: str, health_url: str, timeout: int = 10):
        self.service_name = service_name
        self.health_url = health_url
        self.timeout = timeout

    def check_service(self) -> HealthCheckResult:
        """Check service health endpoint"""
        start_time = time.time()
        try:
            response = requests.get(
                self.health_url, 
                timeout=self.timeout,
                headers={'User-Agent': 'horme-health-checker/1.0'}
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return HealthCheckResult(
                        self.service_name,
                        'healthy',
                        f'{self.service_name} service is healthy',
                        response_time,
                        data
                    )
                except:
                    return HealthCheckResult(
                        self.service_name,
                        'healthy',
                        f'{self.service_name} service responded',
                        response_time
                    )
            else:
                return HealthCheckResult(
                    self.service_name,
                    'unhealthy',
                    f'{self.service_name} returned status {response.status_code}',
                    response_time,
                    {'status_code': response.status_code}
                )
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                self.service_name,
                'unhealthy',
                f'{self.service_name} health check timed out',
                response_time,
                {'timeout': self.timeout}
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                self.service_name,
                'unhealthy',
                f'{self.service_name} health check failed: {str(e)}',
                response_time,
                {'error': str(e)}
            )

class ComprehensiveHealthChecker:
    """Main health checker orchestrating all service checks"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.redis_url = os.getenv('REDIS_URL')
        
        # Initialize individual checkers
        self.db_checker = DatabaseHealthChecker(self.database_url) if self.database_url else None
        self.redis_checker = RedisHealthChecker(self.redis_url) if self.redis_url else None
        
        # Service checkers
        self.service_checkers = [
            ServiceHealthChecker('api', 'http://localhost:8002/health'),
            ServiceHealthChecker('mcp', 'http://localhost:3004/health'),
            ServiceHealthChecker('nexus', 'http://localhost:8090/health'),
            ServiceHealthChecker('frontend', 'http://localhost:3010/api/health'),
        ]

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks concurrently"""
        results = []
        start_time = time.time()
        
        # Database checks
        if self.db_checker:
            results.append(self.db_checker.check_connectivity())
            results.append(self.db_checker.check_performance())
        
        # Redis checks
        if self.redis_checker:
            results.append(self.redis_checker.check_connectivity())
            results.append(self.redis_checker.check_performance())
        
        # Service checks
        for service_checker in self.service_checkers:
            results.append(service_checker.check_service())
        
        total_time = (time.time() - start_time) * 1000
        
        # Calculate overall status
        healthy_count = sum(1 for r in results if r.status == 'healthy')
        degraded_count = sum(1 for r in results if r.status == 'degraded')
        unhealthy_count = sum(1 for r in results if r.status == 'unhealthy')
        
        if unhealthy_count > 0:
            overall_status = 'unhealthy'
        elif degraded_count > 0:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        return {
            'overall_status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'total_checks': len(results),
            'healthy_checks': healthy_count,
            'degraded_checks': degraded_count,
            'unhealthy_checks': unhealthy_count,
            'total_check_time_ms': round(total_time, 2),
            'checks': [result.to_dict() for result in results],
            'summary': {
                'database_connectivity': next((r.status for r in results if r.service_name == 'database_connectivity'), 'unknown'),
                'database_performance': next((r.status for r in results if r.service_name == 'database_performance'), 'unknown'),
                'redis_connectivity': next((r.status for r in results if r.service_name == 'redis_connectivity'), 'unknown'),
                'redis_performance': next((r.status for r in results if r.service_name == 'redis_performance'), 'unknown'),
                'services': {
                    checker.service_name: next((r.status for r in results if r.service_name == checker.service_name), 'unknown')
                    for checker in self.service_checkers
                }
            }
        }

    def get_simple_status(self) -> Dict[str, str]:
        """Get a simple status check for quick validation"""
        try:
            # Quick database check
            db_status = 'unknown'
            if self.db_checker:
                result = self.db_checker.check_connectivity()
                db_status = result.status
            
            # Quick Redis check
            redis_status = 'unknown'
            if self.redis_checker:
                result = self.redis_checker.check_connectivity()
                redis_status = result.status
            
            return {
                'status': 'healthy' if db_status == 'healthy' and redis_status == 'healthy' else 'unhealthy',
                'database': db_status,
                'redis': redis_status,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# FastAPI health endpoints
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

def setup_health_endpoints(app: FastAPI):
    """Setup health check endpoints for FastAPI applications"""
    
    health_checker = ComprehensiveHealthChecker()
    
    @app.get("/health")
    async def health_check():
        """Simple health check endpoint"""
        status = health_checker.get_simple_status()
        status_code = 200 if status['status'] == 'healthy' else 503
        return JSONResponse(content=status, status_code=status_code)
    
    @app.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check with all service statuses"""
        results = await health_checker.run_all_checks()
        status_code = 200 if results['overall_status'] == 'healthy' else 503
        return JSONResponse(content=results, status_code=status_code)
    
    @app.get("/health/database")
    async def database_health():
        """Database-specific health check"""
        if not health_checker.db_checker:
            return JSONResponse(content={'error': 'Database not configured'}, status_code=503)
        
        connectivity = health_checker.db_checker.check_connectivity()
        performance = health_checker.db_checker.check_performance()
        
        status = 'healthy' if connectivity.status == 'healthy' and performance.status in ['healthy', 'degraded'] else 'unhealthy'
        status_code = 200 if status == 'healthy' else 503
        
        return JSONResponse(content={
            'status': status,
            'connectivity': connectivity.to_dict(),
            'performance': performance.to_dict()
        }, status_code=status_code)
    
    @app.get("/health/redis")
    async def redis_health():
        """Redis-specific health check"""
        if not health_checker.redis_checker:
            return JSONResponse(content={'error': 'Redis not configured'}, status_code=503)
        
        connectivity = health_checker.redis_checker.check_connectivity()
        performance = health_checker.redis_checker.check_performance()
        
        status = 'healthy' if connectivity.status == 'healthy' and performance.status in ['healthy', 'degraded'] else 'unhealthy'
        status_code = 200 if status == 'healthy' else 503
        
        return JSONResponse(content={
            'status': status,
            'connectivity': connectivity.to_dict(),
            'performance': performance.to_dict()
        }, status_code=status_code)

if __name__ == "__main__":
    # Command line health check
    import sys
    
    async def main():
        checker = ComprehensiveHealthChecker()
        
        if len(sys.argv) > 1 and sys.argv[1] == '--simple':
            # Simple status check
            result = checker.get_simple_status()
            print(json.dumps(result, indent=2))
            sys.exit(0 if result['status'] == 'healthy' else 1)
        else:
            # Full health check
            results = await checker.run_all_checks()
            print(json.dumps(results, indent=2))
            sys.exit(0 if results['overall_status'] == 'healthy' else 1)
    
    asyncio.run(main())