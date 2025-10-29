#!/usr/bin/env python3
"""
Health Check Validation Script
Validates all Docker services health checks and readiness
"""

import subprocess
import time
import requests
import psycopg2
import redis
import docker
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HealthCheckValidator:
    """Validates health checks for all Docker services"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'summary': {
                'total_services': 0,
                'healthy_services': 0,
                'unhealthy_services': 0,
                'overall_status': 'UNKNOWN'
            }
        }
        
        self.service_checks = {
            'postgres': {
                'container_name': 'horme-postgres',
                'check_method': self._check_postgres,
                'required': True,
                'timeout': 30
            },
            'redis': {
                'container_name': 'horme-redis',
                'check_method': self._check_redis,
                'required': True,
                'timeout': 10
            },
            'api': {
                'container_name': 'horme-api',
                'check_method': self._check_api,
                'required': True,
                'timeout': 15
            },
            'mcp': {
                'container_name': 'horme-mcp',
                'check_method': self._check_mcp,
                'required': True,
                'timeout': 10
            },
            'frontend': {
                'container_name': 'horme-frontend',
                'check_method': self._check_frontend,
                'required': True,
                'timeout': 15
            },
            'nexus': {
                'container_name': 'horme-nexus',
                'check_method': self._check_nexus,
                'required': False,
                'timeout': 15
            }
        }
    
    def validate_all_services(self) -> Dict:
        """Validate health of all services"""
        logger.info("Starting comprehensive health check validation...")
        
        for service_name, config in self.service_checks.items():
            logger.info(f"Checking {service_name}...")
            
            start_time = time.time()
            health_result = self._validate_service_health(service_name, config)
            end_time = time.time()
            
            health_result['check_duration_ms'] = round((end_time - start_time) * 1000, 2)
            self.results['services'][service_name] = health_result
            self.results['summary']['total_services'] += 1
            
            if health_result['healthy']:
                self.results['summary']['healthy_services'] += 1
                logger.info(f"✅ {service_name}: HEALTHY")
            else:
                self.results['summary']['unhealthy_services'] += 1
                logger.error(f"❌ {service_name}: UNHEALTHY - {health_result.get('error', 'Unknown error')}")
        
        # Determine overall status
        if self.results['summary']['unhealthy_services'] == 0:
            self.results['summary']['overall_status'] = 'HEALTHY'
        elif self.results['summary']['healthy_services'] > 0:
            self.results['summary']['overall_status'] = 'DEGRADED'
        else:
            self.results['summary']['overall_status'] = 'UNHEALTHY'
        
        self._generate_health_report()
        return self.results
    
    def _validate_service_health(self, service_name: str, config: Dict) -> Dict:
        """Validate health of a specific service"""
        result = {
            'service_name': service_name,
            'healthy': False,
            'container_status': 'unknown',
            'container_running': False,
            'health_check_passed': False,
            'error': None,
            'details': {}
        }
        
        try:
            # Check if container exists and is running
            container = self.docker_client.containers.get(config['container_name'])
            result['container_status'] = container.status
            result['container_running'] = container.status == 'running'
            
            if not result['container_running']:
                result['error'] = f"Container not running: {container.status}"
                return result
            
            # Run service-specific health check
            health_check_result = config['check_method']()
            result['health_check_passed'] = health_check_result['success']
            result['details'] = health_check_result.get('details', {})
            
            if not result['health_check_passed']:
                result['error'] = health_check_result.get('error', 'Health check failed')
                return result
            
            result['healthy'] = True
            
        except docker.errors.NotFound:
            result['error'] = f"Container '{config['container_name']}' not found"
        except Exception as e:
            result['error'] = f"Health check error: {str(e)}"
        
        return result
    
    def _check_postgres(self) -> Dict:
        """Check PostgreSQL health"""
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5433,
                database='horme_db',
                user='horme_user',
                password='horme_secure_password',
                connect_timeout=10
            )
            
            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            # Check database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size('horme_db'))")
            db_size = cursor.fetchone()[0]
            
            # Check active connections
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            active_connections = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'details': {
                    'test_query_result': result[0] if result else None,
                    'database_size': db_size,
                    'active_connections': active_connections
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _check_redis(self) -> Dict:
        """Check Redis health"""
        try:
            r = redis.Redis(host='localhost', port=6380, db=0, socket_timeout=10)
            
            # Test ping
            ping_result = r.ping()
            
            # Get info
            info = r.info()
            
            # Test set/get
            test_key = f"health_check_{int(time.time())}"
            r.set(test_key, "test_value", ex=60)  # Expire in 60 seconds
            test_value = r.get(test_key)
            r.delete(test_key)
            
            return {
                'success': True,
                'details': {
                    'ping_successful': ping_result,
                    'redis_version': info.get('redis_version'),
                    'connected_clients': info.get('connected_clients'),
                    'used_memory_human': info.get('used_memory_human'),
                    'test_set_get_successful': test_value == b'test_value'
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _check_api(self) -> Dict:
        """Check API health"""
        try:
            # Check health endpoint
            response = requests.get('http://localhost:8000/health', timeout=10)
            
            if response.status_code == 200:
                try:
                    health_data = response.json()
                except:
                    health_data = {'status': 'unknown'}
                
                # Test a simple endpoint
                try:
                    test_response = requests.get('http://localhost:8000/', timeout=5)
                    root_accessible = test_response.status_code in [200, 404]  # 404 is okay if no root route
                except:
                    root_accessible = False
                
                return {
                    'success': True,
                    'details': {
                        'health_endpoint_status': response.status_code,
                        'health_data': health_data,
                        'response_time_ms': response.elapsed.total_seconds() * 1000,
                        'root_endpoint_accessible': root_accessible
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"Health endpoint returned status {response.status_code}"
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _check_mcp(self) -> Dict:
        """Check MCP server health"""
        try:
            import socket
            
            # Test if MCP port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex(('localhost', 3002))
            sock.close()
            
            if result == 0:
                # Port is open - try to get container logs to verify it's actually running
                container = self.docker_client.containers.get('horme-mcp')
                logs = container.logs(tail=10).decode()
                
                # Look for startup indicators in logs
                startup_indicators = ['server running', 'listening', 'started', 'ready']
                has_startup_log = any(indicator in logs.lower() for indicator in startup_indicators)
                
                return {
                    'success': True,
                    'details': {
                        'port_accessible': True,
                        'has_startup_logs': has_startup_log,
                        'recent_logs_sample': logs[-200:] if logs else 'No logs'
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"MCP port 3002 not accessible (connection result: {result})"
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _check_frontend(self) -> Dict:
        """Check Frontend health"""
        try:
            response = requests.get('http://localhost:3000', timeout=10)
            
            if response.status_code == 200:
                # Check if it looks like a valid HTML response
                content = response.text.lower()
                is_html = '<html' in content or '<!doctype html' in content
                has_title = '<title>' in content
                
                return {
                    'success': True,
                    'details': {
                        'status_code': response.status_code,
                        'response_time_ms': response.elapsed.total_seconds() * 1000,
                        'content_type': response.headers.get('content-type', 'unknown'),
                        'is_html': is_html,
                        'has_title': has_title,
                        'content_length': len(response.content)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"Frontend returned status {response.status_code}"
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _check_nexus(self) -> Dict:
        """Check Nexus platform health (optional service)"""
        try:
            response = requests.get('http://localhost:8080/health', timeout=10)
            
            if response.status_code == 200:
                try:
                    health_data = response.json()
                except:
                    health_data = {'status': 'responding'}
                
                return {
                    'success': True,
                    'details': {
                        'health_endpoint_status': response.status_code,
                        'health_data': health_data,
                        'response_time_ms': response.elapsed.total_seconds() * 1000
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"Nexus health endpoint returned status {response.status_code}"
                }
                
        except Exception as e:
            # For optional services, we might be more lenient
            return {'success': False, 'error': str(e)}
    
    def _generate_health_report(self):
        """Generate health check report"""
        report_path = 'health_check_report.json'
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Console summary
        summary = self.results['summary']
        logger.info("=" * 50)
        logger.info("HEALTH CHECK VALIDATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Overall Status: {summary['overall_status']}")
        logger.info(f"Total Services: {summary['total_services']}")
        logger.info(f"Healthy: {summary['healthy_services']}")
        logger.info(f"Unhealthy: {summary['unhealthy_services']}")
        logger.info(f"Report saved to: {report_path}")
        logger.info("=" * 50)
        
        # Detailed service status
        for service_name, service_result in self.results['services'].items():
            status = "✅ HEALTHY" if service_result['healthy'] else "❌ UNHEALTHY"
            duration = service_result.get('check_duration_ms', 0)
            logger.info(f"{service_name}: {status} ({duration}ms)")
            if not service_result['healthy']:
                logger.info(f"  Error: {service_result.get('error', 'Unknown')}")
        
        return report_path
    
    def wait_for_services(self, max_wait_seconds: int = 120, check_interval: int = 5) -> bool:
        """Wait for all required services to be healthy"""
        logger.info(f"Waiting for services to be healthy (max {max_wait_seconds}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            results = self.validate_all_services()
            
            if results['summary']['overall_status'] == 'HEALTHY':
                logger.info(f"✅ All services healthy after {time.time() - start_time:.1f}s")
                return True
            
            unhealthy_services = [
                name for name, result in results['services'].items()
                if not result['healthy'] and self.service_checks[name]['required']
            ]
            
            logger.info(f"Still waiting for: {', '.join(unhealthy_services)}")
            time.sleep(check_interval)
        
        logger.error(f"❌ Services not healthy after {max_wait_seconds}s timeout")
        return False


def main():
    """Main execution"""
    import sys
    
    validator = HealthCheckValidator()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'wait':
        # Wait for services mode
        max_wait = int(sys.argv[2]) if len(sys.argv) > 2 else 120
        success = validator.wait_for_services(max_wait)
        sys.exit(0 if success else 1)
    else:
        # One-time validation mode
        results = validator.validate_all_services()
        
        # Exit with appropriate code
        if results['summary']['overall_status'] == 'HEALTHY':
            sys.exit(0)
        elif results['summary']['overall_status'] == 'DEGRADED':
            sys.exit(2)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()