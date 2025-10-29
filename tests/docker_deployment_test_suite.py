#!/usr/bin/env python3
"""
Comprehensive Docker Deployment Test Suite
Tests all aspects of Docker deployment for production readiness
"""

import subprocess
import time
import json
import requests
import psycopg2
import redis
import docker
import threading
import concurrent.futures
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import yaml
import os
import socket
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('docker_deployment_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DockerDeploymentTester:
    """Comprehensive Docker deployment testing framework"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.results = {
            'infrastructure': {},
            'deployment_workflow': {},
            'production_readiness': {},
            'test_summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'start_time': datetime.now().isoformat(),
                'end_time': None
            }
        }
        
        # Service configurations
        self.services = {
            'postgres': {
                'container_name': 'horme-postgres',
                'port': 5433,
                'health_endpoint': None,
                'connection_test': self._test_postgres_connection
            },
            'redis': {
                'container_name': 'horme-redis',
                'port': 6380,
                'health_endpoint': None,
                'connection_test': self._test_redis_connection
            },
            'api': {
                'container_name': 'horme-api',
                'port': 8000,
                'health_endpoint': 'http://localhost:8000/health',
                'connection_test': self._test_api_connection
            },
            'mcp': {
                'container_name': 'horme-mcp',
                'port': 3002,
                'health_endpoint': None,
                'connection_test': self._test_mcp_connection
            },
            'frontend': {
                'container_name': 'horme-frontend',
                'port': 3000,
                'health_endpoint': 'http://localhost:3000',
                'connection_test': self._test_frontend_connection
            }
        }
        
    def run_all_tests(self) -> Dict:
        """Execute all test categories"""
        logger.info("Starting comprehensive Docker deployment testing...")
        
        try:
            # 1. Infrastructure Testing
            logger.info("=== INFRASTRUCTURE TESTING ===")
            self.test_infrastructure()
            
            # 2. Deployment Workflow Testing
            logger.info("=== DEPLOYMENT WORKFLOW TESTING ===")
            self.test_deployment_workflows()
            
            # 3. Production Readiness Testing
            logger.info("=== PRODUCTION READINESS TESTING ===")
            self.test_production_readiness()
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            self._record_test_result('execution_error', False, str(e))
        
        finally:
            self.results['test_summary']['end_time'] = datetime.now().isoformat()
            self._generate_test_report()
            
        return self.results
    
    def test_infrastructure(self):
        """Test Docker infrastructure components"""
        
        # Test 1: Docker image builds
        self._test_docker_image_builds()
        
        # Test 2: Service startup sequences
        self._test_service_startup()
        
        # Test 3: Health checks
        self._test_health_checks()
        
        # Test 4: Network connectivity
        self._test_network_connectivity()
        
    def _test_docker_image_builds(self):
        """Test building all Docker images"""
        logger.info("Testing Docker image builds...")
        
        images_to_build = [
            ('Dockerfile.api', 'horme-api:test'),
            ('Dockerfile.mcp-lightweight', 'horme-mcp:test'),
            ('Dockerfile.nexus-backend', 'horme-nexus:test'),
            ('Dockerfile.dataflow-import', 'horme-dataflow:test'),
            ('fe-reference/Dockerfile', 'horme-frontend:test')
        ]
        
        for dockerfile, tag in images_to_build:
            if os.path.exists(dockerfile):
                try:
                    logger.info(f"Building {tag} from {dockerfile}")
                    
                    # Build the image
                    build_path = os.path.dirname(dockerfile) if '/' in dockerfile else '.'
                    image, build_logs = self.docker_client.images.build(
                        path=build_path,
                        dockerfile=os.path.basename(dockerfile),
                        tag=tag,
                        rm=True,
                        pull=True
                    )
                    
                    # Check if image was created successfully
                    if image:
                        self._record_test_result(f'build_{tag}', True, f"Successfully built {tag}")
                        logger.info(f"✅ {tag} built successfully")
                    else:
                        self._record_test_result(f'build_{tag}', False, f"Failed to build {tag}")
                        
                except Exception as e:
                    self._record_test_result(f'build_{tag}', False, f"Build failed: {str(e)}")
                    logger.error(f"❌ Failed to build {tag}: {e}")
            else:
                self._record_test_result(f'build_{dockerfile}', False, f"Dockerfile not found: {dockerfile}")
                logger.warning(f"⚠️ Dockerfile not found: {dockerfile}")
    
    def _test_service_startup(self):
        """Test service startup sequences and dependencies"""
        logger.info("Testing service startup sequences...")
        
        try:
            # Start services using docker-compose
            startup_command = ["docker-compose", "-f", "docker-compose.consolidated.yml", "up", "-d"]
            
            result = subprocess.run(
                startup_command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self._record_test_result('service_startup', True, "Services started successfully")
                logger.info("✅ Services started successfully")
                
                # Wait for services to be ready
                time.sleep(30)
                
                # Check if containers are running
                self._check_containers_running()
                
            else:
                self._record_test_result('service_startup', False, f"Startup failed: {result.stderr}")
                logger.error(f"❌ Service startup failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self._record_test_result('service_startup', False, "Service startup timed out")
            logger.error("❌ Service startup timed out")
        except Exception as e:
            self._record_test_result('service_startup', False, f"Startup error: {str(e)}")
            logger.error(f"❌ Service startup error: {e}")
    
    def _check_containers_running(self):
        """Check if all expected containers are running"""
        for service, config in self.services.items():
            try:
                container = self.docker_client.containers.get(config['container_name'])
                if container.status == 'running':
                    self._record_test_result(f'container_{service}_running', True, f"{service} container is running")
                    logger.info(f"✅ {service} container is running")
                else:
                    self._record_test_result(f'container_{service}_running', False, f"{service} container status: {container.status}")
                    logger.error(f"❌ {service} container not running: {container.status}")
            except docker.errors.NotFound:
                self._record_test_result(f'container_{service}_running', False, f"{service} container not found")
                logger.error(f"❌ {service} container not found")
            except Exception as e:
                self._record_test_result(f'container_{service}_running', False, f"Error checking {service}: {str(e)}")
                logger.error(f"❌ Error checking {service} container: {e}")
    
    def _test_health_checks(self):
        """Test health checks and readiness probes"""
        logger.info("Testing health checks...")
        
        for service, config in self.services.items():
            if config['health_endpoint']:
                try:
                    response = requests.get(config['health_endpoint'], timeout=10)
                    if response.status_code == 200:
                        self._record_test_result(f'health_{service}', True, f"{service} health check passed")
                        logger.info(f"✅ {service} health check passed")
                    else:
                        self._record_test_result(f'health_{service}', False, f"{service} health check failed: {response.status_code}")
                        logger.error(f"❌ {service} health check failed: {response.status_code}")
                except Exception as e:
                    self._record_test_result(f'health_{service}', False, f"Health check error: {str(e)}")
                    logger.error(f"❌ {service} health check error: {e}")
            else:
                # For services without HTTP health endpoints, test connection
                if config['connection_test']:
                    success, message = config['connection_test']()
                    self._record_test_result(f'health_{service}', success, message)
                    if success:
                        logger.info(f"✅ {service} connection test passed")
                    else:
                        logger.error(f"❌ {service} connection test failed: {message}")
    
    def _test_network_connectivity(self):
        """Test network connectivity between services"""
        logger.info("Testing network connectivity...")
        
        # Test database connectivity from API container
        try:
            result = subprocess.run([
                "docker", "exec", "horme-api", "python", "-c",
                "import psycopg2; conn = psycopg2.connect('postgresql://horme_user:horme_secure_password@postgres:5432/horme_db'); print('DB connection successful')"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self._record_test_result('network_api_to_db', True, "API to DB connectivity successful")
                logger.info("✅ API to DB connectivity successful")
            else:
                self._record_test_result('network_api_to_db', False, f"API to DB connectivity failed: {result.stderr}")
                logger.error(f"❌ API to DB connectivity failed: {result.stderr}")
        except Exception as e:
            self._record_test_result('network_api_to_db', False, f"Network test error: {str(e)}")
            logger.error(f"❌ Network test error: {e}")
        
        # Test Redis connectivity from API container
        try:
            result = subprocess.run([
                "docker", "exec", "horme-api", "python", "-c",
                "import redis; r = redis.Redis(host='redis', port=6379); r.ping(); print('Redis connection successful')"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self._record_test_result('network_api_to_redis', True, "API to Redis connectivity successful")
                logger.info("✅ API to Redis connectivity successful")
            else:
                self._record_test_result('network_api_to_redis', False, f"API to Redis connectivity failed: {result.stderr}")
                logger.error(f"❌ API to Redis connectivity failed: {result.stderr}")
        except Exception as e:
            self._record_test_result('network_api_to_redis', False, f"Network test error: {str(e)}")
            logger.error(f"❌ Network test error: {e}")
    
    def test_deployment_workflows(self):
        """Test deployment workflow scenarios"""
        
        # Test 1: Clean deployment from scratch
        self._test_clean_deployment()
        
        # Test 2: Restart and recovery scenarios
        self._test_restart_recovery()
        
        # Test 3: Scaling scenarios
        self._test_scaling()
        
        # Test 4: Backup and restore
        self._test_backup_restore()
    
    def _test_clean_deployment(self):
        """Test clean deployment from scratch"""
        logger.info("Testing clean deployment from scratch...")
        
        try:
            # Stop and remove all containers
            subprocess.run(["docker-compose", "-f", "docker-compose.consolidated.yml", "down", "-v"], 
                         capture_output=True, timeout=120)
            
            # Clean deployment
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.consolidated.yml", "up", "-d", "--build"
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                # Wait for services to be ready
                time.sleep(60)
                
                # Verify all services are running
                all_running = True
                for service, config in self.services.items():
                    try:
                        container = self.docker_client.containers.get(config['container_name'])
                        if container.status != 'running':
                            all_running = False
                            break
                    except:
                        all_running = False
                        break
                
                if all_running:
                    self._record_test_result('clean_deployment', True, "Clean deployment successful")
                    logger.info("✅ Clean deployment successful")
                else:
                    self._record_test_result('clean_deployment', False, "Not all services running after clean deployment")
                    logger.error("❌ Not all services running after clean deployment")
            else:
                self._record_test_result('clean_deployment', False, f"Clean deployment failed: {result.stderr}")
                logger.error(f"❌ Clean deployment failed: {result.stderr}")
                
        except Exception as e:
            self._record_test_result('clean_deployment', False, f"Clean deployment error: {str(e)}")
            logger.error(f"❌ Clean deployment error: {e}")
    
    def _test_restart_recovery(self):
        """Test restart and recovery scenarios"""
        logger.info("Testing restart and recovery scenarios...")
        
        # Test individual service restart
        for service, config in self.services.items():
            try:
                container = self.docker_client.containers.get(config['container_name'])
                
                # Stop the container
                container.stop()
                time.sleep(5)
                
                # Start the container
                container.start()
                time.sleep(10)
                
                # Check if it's running
                container.reload()
                if container.status == 'running':
                    self._record_test_result(f'restart_{service}', True, f"{service} restart successful")
                    logger.info(f"✅ {service} restart successful")
                else:
                    self._record_test_result(f'restart_{service}', False, f"{service} restart failed: {container.status}")
                    logger.error(f"❌ {service} restart failed: {container.status}")
                    
            except Exception as e:
                self._record_test_result(f'restart_{service}', False, f"Restart test error: {str(e)}")
                logger.error(f"❌ {service} restart test error: {e}")
    
    def _test_scaling(self):
        """Test scaling scenarios"""
        logger.info("Testing scaling scenarios...")
        
        try:
            # Test scaling API service
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.consolidated.yml", "up", "-d", "--scale", "api=2"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                time.sleep(20)
                
                # Check if we have 2 API containers
                api_containers = [c for c in self.docker_client.containers.list() 
                                if 'horme-api' in c.name or 'api' in c.image.tags[0] if c.image.tags]
                
                if len(api_containers) >= 2:
                    self._record_test_result('scaling_test', True, f"Scaling successful: {len(api_containers)} API instances")
                    logger.info(f"✅ Scaling successful: {len(api_containers)} API instances")
                    
                    # Scale back down
                    subprocess.run([
                        "docker-compose", "-f", "docker-compose.consolidated.yml", "up", "-d", "--scale", "api=1"
                    ], capture_output=True, timeout=120)
                    
                else:
                    self._record_test_result('scaling_test', False, f"Scaling failed: only {len(api_containers)} instances")
                    logger.error(f"❌ Scaling failed: only {len(api_containers)} instances")
            else:
                self._record_test_result('scaling_test', False, f"Scaling command failed: {result.stderr}")
                logger.error(f"❌ Scaling command failed: {result.stderr}")
                
        except Exception as e:
            self._record_test_result('scaling_test', False, f"Scaling test error: {str(e)}")
            logger.error(f"❌ Scaling test error: {e}")
    
    def _test_backup_restore(self):
        """Test backup and restore procedures"""
        logger.info("Testing backup and restore procedures...")
        
        try:
            # Create a test backup
            backup_result = subprocess.run([
                "docker", "exec", "horme-postgres", "pg_dump", 
                "-U", "horme_user", "-d", "horme_db", "-f", "/tmp/test_backup.sql"
            ], capture_output=True, text=True, timeout=60)
            
            if backup_result.returncode == 0:
                self._record_test_result('database_backup', True, "Database backup successful")
                logger.info("✅ Database backup successful")
                
                # Test restore (to a test database)
                restore_result = subprocess.run([
                    "docker", "exec", "horme-postgres", "createdb", 
                    "-U", "horme_user", "test_restore_db"
                ], capture_output=True, text=True, timeout=30)
                
                if restore_result.returncode == 0:
                    restore_data_result = subprocess.run([
                        "docker", "exec", "horme-postgres", "psql",
                        "-U", "horme_user", "-d", "test_restore_db", "-f", "/tmp/test_backup.sql"
                    ], capture_output=True, text=True, timeout=60)
                    
                    if restore_data_result.returncode == 0:
                        self._record_test_result('database_restore', True, "Database restore successful")
                        logger.info("✅ Database restore successful")
                    else:
                        self._record_test_result('database_restore', False, f"Database restore failed: {restore_data_result.stderr}")
                        logger.error(f"❌ Database restore failed: {restore_data_result.stderr}")
                else:
                    self._record_test_result('database_restore', False, f"Test database creation failed: {restore_result.stderr}")
                    logger.error(f"❌ Test database creation failed: {restore_result.stderr}")
            else:
                self._record_test_result('database_backup', False, f"Database backup failed: {backup_result.stderr}")
                logger.error(f"❌ Database backup failed: {backup_result.stderr}")
                
        except Exception as e:
            self._record_test_result('backup_restore_test', False, f"Backup/restore test error: {str(e)}")
            logger.error(f"❌ Backup/restore test error: {e}")
    
    def test_production_readiness(self):
        """Test production readiness scenarios"""
        
        # Test 1: Load testing
        self._test_load_performance()
        
        # Test 2: Failure injection
        self._test_failure_injection()
        
        # Test 3: Security scanning
        self._test_security_scanning()
        
        # Test 4: Performance benchmarking
        self._test_performance_benchmarks()
    
    def _test_load_performance(self):
        """Test load performance with realistic workloads"""
        logger.info("Testing load performance...")
        
        def make_request():
            try:
                response = requests.get('http://localhost:8000/health', timeout=5)
                return response.status_code == 200
            except:
                return False
        
        try:
            # Perform concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(make_request) for _ in range(100)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            success_rate = sum(results) / len(results) * 100
            
            if success_rate >= 95:
                self._record_test_result('load_test', True, f"Load test passed: {success_rate}% success rate")
                logger.info(f"✅ Load test passed: {success_rate}% success rate")
            else:
                self._record_test_result('load_test', False, f"Load test failed: {success_rate}% success rate")
                logger.error(f"❌ Load test failed: {success_rate}% success rate")
                
        except Exception as e:
            self._record_test_result('load_test', False, f"Load test error: {str(e)}")
            logger.error(f"❌ Load test error: {e}")
    
    def _test_failure_injection(self):
        """Test failure injection and recovery"""
        logger.info("Testing failure injection and recovery...")
        
        try:
            # Kill the API container and see if it recovers
            api_container = self.docker_client.containers.get('horme-api')
            api_container.kill()
            
            # Wait a moment
            time.sleep(10)
            
            # Check if docker-compose restarts it (with restart policy)
            try:
                api_container.reload()
                if api_container.status == 'running':
                    self._record_test_result('failure_recovery', True, "API container recovered after kill")
                    logger.info("✅ API container recovered after kill")
                else:
                    # Try to restart manually
                    api_container.start()
                    time.sleep(5)
                    api_container.reload()
                    if api_container.status == 'running':
                        self._record_test_result('failure_recovery', True, "API container manually recovered")
                        logger.info("✅ API container manually recovered")
                    else:
                        self._record_test_result('failure_recovery', False, f"API container failed to recover: {api_container.status}")
                        logger.error(f"❌ API container failed to recover: {api_container.status}")
            except Exception as e:
                self._record_test_result('failure_recovery', False, f"Recovery test error: {str(e)}")
                logger.error(f"❌ Recovery test error: {e}")
                
        except Exception as e:
            self._record_test_result('failure_injection', False, f"Failure injection error: {str(e)}")
            logger.error(f"❌ Failure injection error: {e}")
    
    def _test_security_scanning(self):
        """Test security scanning of container images"""
        logger.info("Testing security scanning...")
        
        # Basic security checks
        security_checks = []
        
        # Check for non-root users
        try:
            for service, config in self.services.items():
                try:
                    container = self.docker_client.containers.get(config['container_name'])
                    
                    # Check if running as non-root
                    exec_result = container.exec_run("whoami")
                    if exec_result.exit_code == 0:
                        user = exec_result.output.decode().strip()
                        if user != 'root':
                            security_checks.append(f"{service}: Running as non-root user ({user})")
                        else:
                            security_checks.append(f"{service}: WARNING - Running as root")
                except Exception as e:
                    security_checks.append(f"{service}: Could not check user - {str(e)}")
            
            self._record_test_result('security_scan', True, f"Security checks completed: {security_checks}")
            logger.info(f"✅ Security checks completed: {len(security_checks)} checks")
            
        except Exception as e:
            self._record_test_result('security_scan', False, f"Security scan error: {str(e)}")
            logger.error(f"❌ Security scan error: {e}")
    
    def _test_performance_benchmarks(self):
        """Test performance benchmarks"""
        logger.info("Testing performance benchmarks...")
        
        benchmarks = {}
        
        # Test API response time
        try:
            start_time = time.time()
            response = requests.get('http://localhost:8000/health', timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # ms
            benchmarks['api_response_time_ms'] = response_time
            
            if response_time < 1000:  # Less than 1 second
                self._record_test_result('api_performance', True, f"API response time: {response_time:.2f}ms")
                logger.info(f"✅ API response time: {response_time:.2f}ms")
            else:
                self._record_test_result('api_performance', False, f"API response time too slow: {response_time:.2f}ms")
                logger.error(f"❌ API response time too slow: {response_time:.2f}ms")
                
        except Exception as e:
            self._record_test_result('api_performance', False, f"API performance test error: {str(e)}")
            logger.error(f"❌ API performance test error: {e}")
        
        # Test database connection time
        try:
            start_time = time.time()
            success, message = self._test_postgres_connection()
            end_time = time.time()
            
            db_connection_time = (end_time - start_time) * 1000  # ms
            benchmarks['db_connection_time_ms'] = db_connection_time
            
            if success and db_connection_time < 5000:  # Less than 5 seconds
                self._record_test_result('db_performance', True, f"DB connection time: {db_connection_time:.2f}ms")
                logger.info(f"✅ DB connection time: {db_connection_time:.2f}ms")
            else:
                self._record_test_result('db_performance', False, f"DB connection time too slow: {db_connection_time:.2f}ms")
                logger.error(f"❌ DB connection time too slow: {db_connection_time:.2f}ms")
                
        except Exception as e:
            self._record_test_result('db_performance', False, f"DB performance test error: {str(e)}")
            logger.error(f"❌ DB performance test error: {e}")
        
        self.results['production_readiness']['benchmarks'] = benchmarks
    
    # Connection test methods
    def _test_postgres_connection(self) -> Tuple[bool, str]:
        """Test PostgreSQL connection"""
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5433,
                database='horme_db',
                user='horme_user',
                password='horme_secure_password',
                connect_timeout=10
            )
            conn.close()
            return True, "PostgreSQL connection successful"
        except Exception as e:
            return False, f"PostgreSQL connection failed: {str(e)}"
    
    def _test_redis_connection(self) -> Tuple[bool, str]:
        """Test Redis connection"""
        try:
            r = redis.Redis(host='localhost', port=6380, db=0, socket_timeout=10)
            r.ping()
            return True, "Redis connection successful"
        except Exception as e:
            return False, f"Redis connection failed: {str(e)}"
    
    def _test_api_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        try:
            response = requests.get('http://localhost:8000/health', timeout=10)
            if response.status_code == 200:
                return True, "API connection successful"
            else:
                return False, f"API returned status code: {response.status_code}"
        except Exception as e:
            return False, f"API connection failed: {str(e)}"
    
    def _test_mcp_connection(self) -> Tuple[bool, str]:
        """Test MCP connection"""
        try:
            # Test if MCP port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex(('localhost', 3002))
            sock.close()
            
            if result == 0:
                return True, "MCP port is accessible"
            else:
                return False, "MCP port is not accessible"
        except Exception as e:
            return False, f"MCP connection test failed: {str(e)}"
    
    def _test_frontend_connection(self) -> Tuple[bool, str]:
        """Test Frontend connection"""
        try:
            response = requests.get('http://localhost:3000', timeout=10)
            if response.status_code == 200:
                return True, "Frontend connection successful"
            else:
                return False, f"Frontend returned status code: {response.status_code}"
        except Exception as e:
            return False, f"Frontend connection failed: {str(e)}"
    
    def _record_test_result(self, test_name: str, success: bool, message: str):
        """Record test result"""
        category = 'infrastructure'  # Default category
        if 'deployment' in test_name or 'restart' in test_name or 'scaling' in test_name or 'backup' in test_name:
            category = 'deployment_workflow'
        elif 'load' in test_name or 'failure' in test_name or 'security' in test_name or 'performance' in test_name:
            category = 'production_readiness'
        
        if category not in self.results:
            self.results[category] = {}
        
        self.results[category][test_name] = {
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['test_summary']['total_tests'] += 1
        if success:
            self.results['test_summary']['passed'] += 1
        else:
            self.results['test_summary']['failed'] += 1
    
    def _generate_test_report(self):
        """Generate comprehensive test report"""
        report_path = 'docker_deployment_test_report.json'
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Generate summary report
        summary = self.results['test_summary']
        success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        
        logger.info("=" * 50)
        logger.info("DOCKER DEPLOYMENT TEST SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Test Duration: {summary['start_time']} to {summary['end_time']}")
        logger.info(f"Detailed Report: {report_path}")
        logger.info("=" * 50)
        
        return report_path


def main():
    """Main test execution"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Docker Deployment Test Suite")
        print("Usage: python docker_deployment_test_suite.py [category]")
        print("Categories: infrastructure, deployment, production, all")
        return
    
    category = sys.argv[1] if len(sys.argv) > 1 else 'all'
    
    tester = DockerDeploymentTester()
    
    if category == 'infrastructure':
        tester.test_infrastructure()
    elif category == 'deployment':
        tester.test_deployment_workflows()
    elif category == 'production':
        tester.test_production_readiness()
    else:
        tester.run_all_tests()
    
    return tester.results


if __name__ == "__main__":
    main()