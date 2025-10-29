#!/usr/bin/env python3
"""
Simple Health Check Script for Docker Services
Basic validation without external dependencies
"""

import subprocess
import socket
import time
import json
import sys
from datetime import datetime

class SimpleHealthChecker:
    """Simple health checker using only standard library"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'summary': {
                'total_checked': 0,
                'healthy': 0,
                'unhealthy': 0,
                'overall_status': 'UNKNOWN'
            }
        }
        
        # Service ports to check
        self.service_ports = {
            'postgres': 5433,
            'redis': 6380,
            'api': 8000,
            'mcp': 3002,
            'frontend': 3000,
            'nexus': 8080
        }
        
        self.container_names = {
            'postgres': 'horme-postgres',
            'redis': 'horme-redis',
            'api': 'horme-api',
            'mcp': 'horme-mcp',
            'frontend': 'horme-frontend',
            'nexus': 'horme-nexus'
        }
    
    def check_all_services(self):
        """Check health of all services"""
        print("Running simple health check...")
        
        # Check Docker daemon
        self._check_docker_daemon()
        
        # Check containers
        self._check_containers()
        
        # Check network connectivity
        self._check_network_ports()
        
        # Generate summary
        self._generate_summary()
        
        return self.results
    
    def _check_docker_daemon(self):
        """Check if Docker daemon is running"""
        try:
            result = subprocess.run(['docker', 'version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self._record_result('docker_daemon', True, "Docker daemon is running")
                print("[OK] Docker daemon: RUNNING")
            else:
                self._record_result('docker_daemon', False, f"Docker daemon error: {result.stderr}")
                print("[ERROR] Docker daemon: ERROR")
                
        except Exception as e:
            self._record_result('docker_daemon', False, f"Docker daemon check failed: {str(e)}")
            print(f"[ERROR] Docker daemon: ERROR - {str(e)}")
    
    def _check_containers(self):
        """Check container status"""
        try:
            result = subprocess.run(['docker', 'ps', '-a', '--format', 'json'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self._record_result('container_check', False, f"Cannot list containers: {result.stderr}")
                return
            
            # Parse container information
            containers = {}
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    try:
                        container = json.loads(line)
                        containers[container['Names']] = container
                    except:
                        continue
            
            # Check expected containers
            for service, container_name in self.container_names.items():
                if container_name in containers:
                    container = containers[container_name]
                    status = container['State']
                    is_running = status == 'running'
                    
                    self._record_result(f'container_{service}', is_running, 
                                      f"Container {container_name}: {status}")
                    
                    if is_running:
                        print(f"[OK] {service} container: RUNNING")
                    else:
                        print(f"[ERROR] {service} container: {status}")
                else:
                    self._record_result(f'container_{service}', False, 
                                      f"Container {container_name} not found")
                    print(f"[ERROR] {service} container: NOT FOUND")
                    
        except Exception as e:
            self._record_result('container_check', False, f"Container check error: {str(e)}")
            print(f"[ERROR] Container check error: {str(e)}")
    
    def _check_network_ports(self):
        """Check if service ports are accessible"""
        for service, port in self.service_ports.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    self._record_result(f'port_{service}', True, f"Port {port} is accessible")
                    print(f"[OK] {service} port {port}: ACCESSIBLE")
                else:
                    self._record_result(f'port_{service}', False, f"Port {port} is not accessible")
                    print(f"[ERROR] {service} port {port}: NOT ACCESSIBLE")
                    
            except Exception as e:
                self._record_result(f'port_{service}', False, f"Port check error: {str(e)}")
                print(f"[ERROR] {service} port {port}: ERROR - {str(e)}")
    
    def _record_result(self, test_name, success, message):
        """Record test result"""
        self.results['services'][test_name] = {
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['summary']['total_checked'] += 1
        if success:
            self.results['summary']['healthy'] += 1
        else:
            self.results['summary']['unhealthy'] += 1
    
    def _generate_summary(self):
        """Generate summary and save report"""
        summary = self.results['summary']
        
        if summary['unhealthy'] == 0:
            summary['overall_status'] = 'HEALTHY'
        elif summary['healthy'] > summary['unhealthy']:
            summary['overall_status'] = 'DEGRADED'
        else:
            summary['overall_status'] = 'UNHEALTHY'
        
        # Save report
        report_file = 'simple_health_check_report.json'
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print("\n" + "="*50)
        print("SIMPLE HEALTH CHECK SUMMARY")
        print("="*50)
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Total Checks: {summary['total_checked']}")
        print(f"Healthy: {summary['healthy']}")
        print(f"Unhealthy: {summary['unhealthy']}")
        print(f"Report saved: {report_file}")
        print("="*50)
    
    def start_missing_services(self):
        """Try to start missing services"""
        print("\nAttempting to start missing services...")
        
        # Check which compose file to use
        compose_files = [
            'docker-compose.consolidated.yml',
            'docker-compose.production.yml',
            'docker-compose.yml'
        ]
        
        compose_file = None
        for file in compose_files:
            try:
                result = subprocess.run(['ls', file], capture_output=True, timeout=5)
                if result.returncode == 0:
                    compose_file = file
                    break
            except:
                continue
        
        if not compose_file:
            print("[ERROR] No suitable docker-compose file found")
            return False
        
        print(f"Using compose file: {compose_file}")
        
        try:
            # Start services
            result = subprocess.run([
                'docker-compose', '-f', compose_file, 'up', '-d'
            ], capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                print("[OK] Services startup command executed successfully")
                print("Waiting for services to initialize...")
                time.sleep(30)
                return True
            else:
                print(f"[ERROR] Service startup failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Service startup error: {str(e)}")
            return False


def main():
    """Main execution"""
    checker = SimpleHealthChecker()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'start':
        # Try to start services first
        checker.start_missing_services()
        time.sleep(10)
    
    # Run health check
    results = checker.check_all_services()
    
    # Return appropriate exit code
    if results['summary']['overall_status'] == 'HEALTHY':
        sys.exit(0)
    elif results['summary']['overall_status'] == 'DEGRADED':
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()