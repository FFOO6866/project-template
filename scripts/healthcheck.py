#!/usr/bin/env python3
"""
Comprehensive health check service for Horme POV production deployment.
Monitors all services and provides detailed status reporting.
"""

import os
import time
import json
import logging
import requests
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List
import psutil
import docker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self):
        self.check_interval = int(os.getenv('CHECK_INTERVAL', 30))
        self.services = self._parse_services()
        self.docker_client = None
        self.status_history = []
        
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Could not connect to Docker daemon: {e}")
    
    def _parse_services(self) -> Dict[str, int]:
        """Parse services configuration from environment"""
        services_str = os.getenv('SERVICES', '')
        services = {}
        
        for service in services_str.split(','):
            if ':' in service:
                name, port = service.split(':')
                services[name.strip()] = int(port.strip())
        
        return services
    
    def check_service_health(self, service: str, port: int) -> Dict[str, Any]:
        """Check health of individual service"""
        status = {
            'service': service,
            'port': port,
            'healthy': False,
            'response_time': None,
            'error': None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            start_time = time.time()
            
            # Determine health check URL based on service
            if service == 'nginx':
                url = f'http://{service}:{port}/health'
            elif service == 'api':
                url = f'http://{service}:{port}/health'
            elif service == 'frontend':
                url = f'http://{service}:{port}/api/health'
            else:
                # For database services, just check if port is open
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((service, port))
                sock.close()
                
                if result == 0:
                    status['healthy'] = True
                    status['response_time'] = time.time() - start_time
                else:
                    status['error'] = f'Port {port} not accessible'
                
                return status
            
            # HTTP health check
            response = requests.get(url, timeout=10)
            response_time = time.time() - start_time
            
            status['response_time'] = response_time
            status['status_code'] = response.status_code
            
            if response.status_code == 200:
                status['healthy'] = True
                try:
                    status['response_data'] = response.json()
                except:
                    status['response_data'] = response.text[:200]
            else:
                status['error'] = f'HTTP {response.status_code}'
                
        except requests.exceptions.Timeout:
            status['error'] = 'Request timeout'
        except requests.exceptions.ConnectionError:
            status['error'] = 'Connection refused'
        except Exception as e:
            status['error'] = str(e)
        
        return status
    
    def check_docker_containers(self) -> List[Dict[str, Any]]:
        """Check Docker container status"""
        containers = []
        
        if not self.docker_client:
            return containers
        
        try:
            for container in self.docker_client.containers.list(all=True):
                container_info = {
                    'name': container.name,
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'created': container.attrs['Created'],
                    'healthy': container.status == 'running'
                }
                
                # Get container stats if running
                if container.status == 'running':
                    try:
                        stats = container.stats(stream=False)
                        # Calculate CPU and memory usage
                        cpu_percent = self._calculate_cpu_percent(stats)
                        memory_usage = stats['memory_stats'].get('usage', 0) / (1024 * 1024)  # MB
                        memory_limit = stats['memory_stats'].get('limit', 0) / (1024 * 1024)  # MB
                        
                        container_info.update({
                            'cpu_percent': cpu_percent,
                            'memory_usage_mb': memory_usage,
                            'memory_limit_mb': memory_limit,
                            'memory_percent': (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
                        })
                    except Exception as e:
                        logger.warning(f"Could not get stats for {container.name}: {e}")
                
                containers.append(container_info)
                
        except Exception as e:
            logger.error(f"Error checking Docker containers: {e}")
        
        return containers
    
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU usage percentage from Docker stats"""
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * 100.0
                return round(cpu_percent, 2)
        except (KeyError, ZeroDivisionError):
            pass
        
        return 0.0
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run complete health check of all services"""
        logger.info("Running comprehensive health check...")
        
        health_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_healthy': True,
            'services': {},
            'containers': [],
            'system_resources': {},
            'summary': {
                'total_services': len(self.services),
                'healthy_services': 0,
                'unhealthy_services': 0,
                'total_containers': 0,
                'running_containers': 0
            }
        }
        
        # Check individual services
        for service, port in self.services.items():
            service_status = self.check_service_health(service, port)
            health_report['services'][service] = service_status
            
            if service_status['healthy']:
                health_report['summary']['healthy_services'] += 1
            else:
                health_report['summary']['unhealthy_services'] += 1
                health_report['overall_healthy'] = False
        
        # Check Docker containers
        containers = self.check_docker_containers()
        health_report['containers'] = containers
        health_report['summary']['total_containers'] = len(containers)
        health_report['summary']['running_containers'] = sum(
            1 for c in containers if c['status'] == 'running'
        )
        
        # Check system resources
        health_report['system_resources'] = self.check_system_resources()
        
        # Store in history (keep last 100 checks)
        self.status_history.append(health_report)
        if len(self.status_history) > 100:
            self.status_history.pop(0)
        
        return health_report
    
    def log_health_summary(self, report: Dict[str, Any]):
        """Log health check summary"""
        summary = report['summary']
        logger.info(
            f"Health Check Summary: "
            f"{summary['healthy_services']}/{summary['total_services']} services healthy, "
            f"{summary['running_containers']}/{summary['total_containers']} containers running"
        )
        
        # Log unhealthy services
        for service, status in report['services'].items():
            if not status['healthy']:
                logger.warning(f"Service {service} is unhealthy: {status.get('error', 'Unknown error')}")
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        logger.info(f"Starting health check monitoring (interval: {self.check_interval}s)")
        logger.info(f"Monitoring services: {list(self.services.keys())}")
        
        while True:
            try:
                report = self.run_comprehensive_health_check()
                self.log_health_summary(report)
                
                # Save report to file for external access
                with open('/tmp/health_report.json', 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Health check monitoring stopped")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)

def main():
    """Main entry point"""
    checker = HealthChecker()
    
    # Run initial health check
    initial_report = checker.run_comprehensive_health_check()
    print(json.dumps(initial_report, indent=2, default=str))
    
    # Start monitoring loop
    checker.run_monitoring_loop()

if __name__ == '__main__':
    main()