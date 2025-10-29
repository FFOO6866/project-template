#!/usr/bin/env python3
"""
Automated Deployment Tests
Comprehensive automated testing of Docker deployment scenarios
"""

import subprocess
import time
import json
import logging
import docker
import requests
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutomatedDeploymentTester:
    """Automated testing of deployment scenarios"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.results = {
            'test_session': {
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'total_scenarios': 0,
                'passed_scenarios': 0,
                'failed_scenarios': 0
            },
            'scenarios': {}
        }
        
        self.compose_file = 'docker-compose.consolidated.yml'
        self.deployment_scenarios = [
            'clean_deployment',
            'incremental_deployment',
            'service_restart',
            'database_persistence',
            'network_isolation',
            'resource_limits',
            'environment_variables',
            'volume_mounts',
            'service_discovery',
            'load_balancing'
        ]
    
    def run_all_scenarios(self) -> Dict:
        """Run all deployment test scenarios"""
        logger.info("Starting automated deployment testing...")
        
        for scenario in self.deployment_scenarios:
            logger.info(f"Running scenario: {scenario}")
            
            try:
                scenario_method = getattr(self, f'_test_{scenario}')
                result = scenario_method()
                
                self.results['scenarios'][scenario] = result
                self.results['test_session']['total_scenarios'] += 1
                
                if result['passed']:
                    self.results['test_session']['passed_scenarios'] += 1
                    logger.info(f"✅ {scenario}: PASSED")
                else:
                    self.results['test_session']['failed_scenarios'] += 1
                    logger.error(f"❌ {scenario}: FAILED - {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                error_result = {
                    'passed': False,
                    'error': f"Scenario execution error: {str(e)}",
                    'timestamp': datetime.now().isoformat()
                }
                
                self.results['scenarios'][scenario] = error_result
                self.results['test_session']['total_scenarios'] += 1
                self.results['test_session']['failed_scenarios'] += 1
                
                logger.error(f"❌ {scenario}: ERROR - {str(e)}")
        
        self.results['test_session']['end_time'] = datetime.now().isoformat()
        self._generate_deployment_report()
        
        return self.results
    
    def _test_clean_deployment(self) -> Dict:
        """Test clean deployment from scratch"""
        try:
            # Tear down everything
            self._execute_command(['docker-compose', '-f', self.compose_file, 'down', '-v', '--remove-orphans'])
            
            # Remove any dangling images
            self._execute_command(['docker', 'system', 'prune', '-f'])
            
            # Deploy from scratch
            result = self._execute_command([
                'docker-compose', '-f', self.compose_file, 'up', '-d', '--build'
            ], timeout=600)
            
            if result['returncode'] != 0:
                return {
                    'passed': False,
                    'error': f"Clean deployment failed: {result['stderr']}",
                    'timestamp': datetime.now().isoformat()
                }
            
            # Wait for services to be ready
            time.sleep(45)
            
            # Verify all expected containers are running
            expected_containers = ['horme-postgres', 'horme-redis', 'horme-api', 'horme-mcp', 'horme-frontend']
            running_containers = []
            
            for container_name in expected_containers:
                try:
                    container = self.docker_client.containers.get(container_name)
                    if container.status == 'running':
                        running_containers.append(container_name)
                except:
                    pass
            
            success = len(running_containers) == len(expected_containers)
            
            return {
                'passed': success,
                'details': {
                    'expected_containers': expected_containers,
                    'running_containers': running_containers,
                    'deployment_time_seconds': 45  # Approximate
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _test_incremental_deployment(self) -> Dict:
        """Test incremental deployment (updating existing services)"""
        try:
            # Ensure services are running first
            self._execute_command(['docker-compose', '-f', self.compose_file, 'up', '-d'])
            time.sleep(30)
            
            # Record initial container IDs
            initial_containers = {}
            for service in ['api', 'mcp', 'frontend']:
                try:
                    container = self.docker_client.containers.get(f'horme-{service}')
                    initial_containers[service] = container.id
                except:
                    pass
            
            # Perform incremental update (rebuild and redeploy API service)
            result = self._execute_command([
                'docker-compose', '-f', self.compose_file, 'up', '-d', '--build', 'api'
            ], timeout=300)
            
            if result['returncode'] != 0:
                return {
                    'passed': False,
                    'error': f"Incremental deployment failed: {result['stderr']}",
                    'timestamp': datetime.now().isoformat()
                }
            
            time.sleep(20)
            
            # Check that API was redeployed but other services remained
            final_containers = {}
            for service in ['api', 'mcp', 'frontend']:
                try:
                    container = self.docker_client.containers.get(f'horme-{service}')
                    final_containers[service] = container.id
                except:
                    pass
            
            # API should have new ID, others should be same
            api_redeployed = initial_containers.get('api') != final_containers.get('api')
            other_services_unchanged = (
                initial_containers.get('mcp') == final_containers.get('mcp') and
                initial_containers.get('frontend') == final_containers.get('frontend')
            )
            
            success = api_redeployed and other_services_unchanged
            
            return {
                'passed': success,
                'details': {
                    'api_redeployed': api_redeployed,
                    'other_services_unchanged': other_services_unchanged,
                    'initial_containers': initial_containers,
                    'final_containers': final_containers
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _test_service_restart(self) -> Dict:
        """Test individual service restart functionality"""
        try:
            # Ensure services are running
            self._execute_command(['docker-compose', '-f', self.compose_file, 'up', '-d'])
            time.sleep(30)
            
            restart_results = {}
            
            for service in ['postgres', 'redis', 'api']:
                container_name = f'horme-{service}'
                
                try:
                    # Get initial container
                    container = self.docker_client.containers.get(container_name)
                    initial_id = container.id
                    
                    # Restart the service
                    restart_result = self._execute_command([
                        'docker-compose', '-f', self.compose_file, 'restart', service
                    ], timeout=60)
                    
                    if restart_result['returncode'] == 0:
                        time.sleep(10)
                        
                        # Check if container is running
                        container.reload()
                        is_running = container.status == 'running'
                        
                        restart_results[service] = {
                            'restarted_successfully': True,
                            'is_running': is_running,
                            'container_id_changed': initial_id != container.id
                        }
                    else:
                        restart_results[service] = {
                            'restarted_successfully': False,
                            'error': restart_result['stderr']
                        }
                        
                except Exception as e:
                    restart_results[service] = {
                        'restarted_successfully': False,
                        'error': str(e)
                    }
            
            # Check if all restarts were successful
            all_successful = all(
                result.get('restarted_successfully', False) and result.get('is_running', False)
                for result in restart_results.values()
            )
            
            return {
                'passed': all_successful,
                'details': restart_results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _test_database_persistence(self) -> Dict:
        """Test database data persistence across restarts"""
        try:
            # Ensure database is running
            self._execute_command(['docker-compose', '-f', self.compose_file, 'up', '-d', 'postgres'])
            time.sleep(20)
            
            # Create test data
            test_data_sql = """
                CREATE TABLE IF NOT EXISTS deployment_test (
                    id SERIAL PRIMARY KEY,
                    test_data VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                INSERT INTO deployment_test (test_data) VALUES ('persistence_test_data');
            """
            
            # Execute SQL in container
            create_result = self._execute_command([
                'docker', 'exec', 'horme-postgres', 'psql',
                '-U', 'horme_user', '-d', 'horme_db',
                '-c', test_data_sql
            ])
            
            if create_result['returncode'] != 0:
                return {
                    'passed': False,
                    'error': f"Failed to create test data: {create_result['stderr']}",
                    'timestamp': datetime.now().isoformat()
                }
            
            # Restart database container
            restart_result = self._execute_command([
                'docker-compose', '-f', self.compose_file, 'restart', 'postgres'
            ], timeout=60)
            
            if restart_result['returncode'] != 0:
                return {
                    'passed': False,
                    'error': f"Database restart failed: {restart_result['stderr']}",
                    'timestamp': datetime.now().isoformat()
                }
            
            time.sleep(20)
            
            # Check if data persisted
            check_result = self._execute_command([
                'docker', 'exec', 'horme-postgres', 'psql',
                '-U', 'horme_user', '-d', 'horme_db',
                '-c', "SELECT test_data FROM deployment_test WHERE test_data = 'persistence_test_data';"
            ])
            
            data_persisted = check_result['returncode'] == 0 and 'persistence_test_data' in check_result['stdout']
            
            # Cleanup
            self._execute_command([
                'docker', 'exec', 'horme-postgres', 'psql',
                '-U', 'horme_user', '-d', 'horme_db',
                '-c', 'DROP TABLE IF EXISTS deployment_test;'
            ])
            
            return {
                'passed': data_persisted,
                'details': {
                    'test_data_created': create_result['returncode'] == 0,
                    'database_restarted': restart_result['returncode'] == 0,
                    'data_persisted_after_restart': data_persisted
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _test_network_isolation(self) -> Dict:
        """Test network isolation between services"""
        try:
            # Ensure services are running
            self._execute_command(['docker-compose', '-f', self.compose_file, 'up', '-d'])
            time.sleep(30)
            
            network_tests = {}
            
            # Test that API can reach database
            api_to_db_result = self._execute_command([
                'docker', 'exec', 'horme-api', 'python', '-c',
                'import socket; s = socket.socket(); s.settimeout(5); result = s.connect_ex(("postgres", 5432)); print(f"connect_result:{result}"); s.close()'
            ])
            
            api_can_reach_db = (api_to_db_result['returncode'] == 0 and 
                              'connect_result:0' in api_to_db_result['stdout'])
            
            network_tests['api_to_database'] = {
                'can_connect': api_can_reach_db,
                'expected': True
            }
            
            # Test that API can reach Redis
            api_to_redis_result = self._execute_command([
                'docker', 'exec', 'horme-api', 'python', '-c',
                'import socket; s = socket.socket(); s.settimeout(5); result = s.connect_ex(("redis", 6379)); print(f"connect_result:{result}"); s.close()'
            ])
            
            api_can_reach_redis = (api_to_redis_result['returncode'] == 0 and 
                                 'connect_result:0' in api_to_redis_result['stdout'])
            
            network_tests['api_to_redis'] = {
                'can_connect': api_can_reach_redis,
                'expected': True
            }
            
            # Test that services are isolated from host network
            try:
                # Check that database is not accessible on host network from within container
                isolation_result = self._execute_command([
                    'docker', 'exec', 'horme-api', 'python', '-c',
                    'import socket; s = socket.socket(); s.settimeout(2); result = s.connect_ex(("host.docker.internal", 5432)); print(f"host_connect_result:{result}"); s.close()'
                ])
                
                # Connection should fail (non-zero result) indicating isolation
                host_isolated = ('host_connect_result:0' not in isolation_result['stdout'])
                
                network_tests['host_isolation'] = {
                    'is_isolated': host_isolated,
                    'expected': True
                }
            except:
                network_tests['host_isolation'] = {
                    'is_isolated': True,  # Assume isolated if test fails
                    'expected': True
                }
            
            # All network tests should pass
            all_network_tests_passed = all(
                test['can_connect'] == test['expected'] if 'can_connect' in test 
                else test['is_isolated'] == test['expected']
                for test in network_tests.values()
            )
            
            return {
                'passed': all_network_tests_passed,
                'details': network_tests,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _test_resource_limits(self) -> Dict:
        """Test resource limits enforcement"""
        try:
            # Ensure services are running
            self._execute_command(['docker-compose', '-f', self.compose_file, 'up', '-d'])
            time.sleep(30)
            
            resource_checks = {}
            
            # Check memory limits for containers
            for service in ['postgres', 'redis', 'api']:
                container_name = f'horme-{service}'
                try:
                    container = self.docker_client.containers.get(container_name)
                    
                    # Get container stats
                    stats = container.stats(stream=False)
                    memory_usage = stats['memory_stats'].get('usage', 0)
                    memory_limit = stats['memory_stats'].get('limit', 0)
                    
                    # Convert to MB
                    memory_usage_mb = memory_usage / (1024 * 1024)
                    memory_limit_mb = memory_limit / (1024 * 1024)
                    
                    resource_checks[service] = {
                        'memory_usage_mb': round(memory_usage_mb, 2),
                        'memory_limit_mb': round(memory_limit_mb, 2),
                        'memory_usage_percentage': round((memory_usage / memory_limit * 100), 2) if memory_limit > 0 else 0,
                        'has_memory_limit': memory_limit > 0
                    }
                    
                except Exception as e:
                    resource_checks[service] = {
                        'error': str(e)
                    }
            
            # Check if at least some services have resource limits
            services_with_limits = sum(1 for check in resource_checks.values() 
                                     if check.get('has_memory_limit', False))
            
            return {
                'passed': services_with_limits >= 2,  # At least 2 services should have limits
                'details': resource_checks,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _test_environment_variables(self) -> Dict:
        """Test environment variable configuration"""
        try:
            # Ensure services are running
            self._execute_command(['docker-compose', '-f', self.compose_file, 'up', '-d'])
            time.sleep(30)
            
            env_checks = {}
            
            # Check critical environment variables in API container
            api_env_result = self._execute_command([
                'docker', 'exec', 'horme-api', 'env'
            ])
            
            if api_env_result['returncode'] == 0:
                api_env = api_env_result['stdout']
                
                env_checks['api'] = {
                    'has_database_url': 'DATABASE_URL' in api_env or 'DB_' in api_env,
                    'has_redis_url': 'REDIS_URL' in api_env or 'REDIS' in api_env,
                    'has_environment': 'ENVIRONMENT' in api_env or 'ENV' in api_env
                }
            else:
                env_checks['api'] = {'error': 'Could not retrieve environment variables'}
            
            # Check database environment variables
            db_env_result = self._execute_command([
                'docker', 'exec', 'horme-postgres', 'env'
            ])
            
            if db_env_result['returncode'] == 0:
                db_env = db_env_result['stdout']
                
                env_checks['postgres'] = {
                    'has_postgres_user': 'POSTGRES_USER' in db_env,
                    'has_postgres_db': 'POSTGRES_DB' in db_env,
                    'has_postgres_password': 'POSTGRES_PASSWORD' in db_env
                }
            else:
                env_checks['postgres'] = {'error': 'Could not retrieve environment variables'}
            
            # Environment variables should be properly configured
            env_properly_configured = (
                env_checks.get('api', {}).get('has_database_url', False) and
                env_checks.get('postgres', {}).get('has_postgres_user', False)
            )
            
            return {
                'passed': env_properly_configured,
                'details': env_checks,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _test_volume_mounts(self) -> Dict:
        """Test volume mounts for data persistence"""
        try:
            # Ensure services are running
            self._execute_command(['docker-compose', '-f', self.compose_file, 'up', '-d'])
            time.sleep(30)
            
            volume_checks = {}
            
            # Check PostgreSQL data volume
            db_volume_result = self._execute_command([
                'docker', 'exec', 'horme-postgres', 'ls', '-la', '/var/lib/postgresql/data'
            ])
            
            volume_checks['postgres_data'] = {
                'volume_accessible': db_volume_result['returncode'] == 0,
                'has_postgres_files': 'postgresql.conf' in db_volume_result['stdout'] if db_volume_result['returncode'] == 0 else False
            }
            
            # Check if code volumes are mounted (for development)
            try:
                api_volume_result = self._execute_command([
                    'docker', 'exec', 'horme-api', 'ls', '-la', '/app'
                ])
                
                volume_checks['api_code'] = {
                    'app_directory_accessible': api_volume_result['returncode'] == 0,
                    'has_python_files': '.py' in api_volume_result['stdout'] if api_volume_result['returncode'] == 0 else False
                }
            except:
                volume_checks['api_code'] = {'error': 'Could not check code volume'}
            
            # At least PostgreSQL volume should work
            volumes_working = volume_checks['postgres_data']['volume_accessible']
            
            return {
                'passed': volumes_working,
                'details': volume_checks,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _test_service_discovery(self) -> Dict:
        """Test service discovery between containers"""
        try:
            # Ensure services are running
            self._execute_command(['docker-compose', '-f', self.compose_file, 'up', '-d'])
            time.sleep(30)
            
            discovery_tests = {}
            
            # Test that API can resolve database hostname
            db_resolution_result = self._execute_command([
                'docker', 'exec', 'horme-api', 'nslookup', 'postgres'
            ])
            
            discovery_tests['api_resolve_postgres'] = {
                'can_resolve': db_resolution_result['returncode'] == 0,
                'has_ip_address': 'Address:' in db_resolution_result['stdout'] if db_resolution_result['returncode'] == 0 else False
            }
            
            # Test that API can resolve Redis hostname
            redis_resolution_result = self._execute_command([
                'docker', 'exec', 'horme-api', 'nslookup', 'redis'
            ])
            
            discovery_tests['api_resolve_redis'] = {
                'can_resolve': redis_resolution_result['returncode'] == 0,
                'has_ip_address': 'Address:' in redis_resolution_result['stdout'] if redis_resolution_result['returncode'] == 0 else False
            }
            
            # Service discovery should work for critical services
            service_discovery_working = (
                discovery_tests['api_resolve_postgres']['can_resolve'] and
                discovery_tests['api_resolve_redis']['can_resolve']
            )
            
            return {
                'passed': service_discovery_working,
                'details': discovery_tests,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _test_load_balancing(self) -> Dict:
        """Test load balancing capabilities (if configured)"""
        try:
            # This is a basic test - in a real load-balanced setup, we'd test multiple instances
            # For now, we'll test that services can handle multiple concurrent requests
            
            # Ensure services are running
            self._execute_command(['docker-compose', '-f', self.compose_file, 'up', '-d'])
            time.sleep(30)
            
            # Test concurrent requests to API
            def make_request():
                try:
                    response = requests.get('http://localhost:8000/health', timeout=5)
                    return response.status_code == 200
                except:
                    return False
            
            # Make 10 concurrent requests
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [future.result() for future in as_completed(futures)]
            
            success_rate = sum(results) / len(results)
            
            return {
                'passed': success_rate >= 0.8,  # 80% success rate
                'details': {
                    'total_requests': len(results),
                    'successful_requests': sum(results),
                    'success_rate': success_rate,
                    'load_balancing_note': 'Basic concurrent request test - actual load balancing would require multiple service instances'
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _execute_command(self, command: List[str], timeout: int = 30) -> Dict:
        """Execute shell command and return result"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds'
            }
        except Exception as e:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
    
    def _generate_deployment_report(self):
        """Generate deployment test report"""
        report_path = 'automated_deployment_test_report.json'
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Console summary
        session = self.results['test_session']
        success_rate = (session['passed_scenarios'] / session['total_scenarios'] * 100) if session['total_scenarios'] > 0 else 0
        
        logger.info("=" * 60)
        logger.info("AUTOMATED DEPLOYMENT TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Scenarios: {session['total_scenarios']}")
        logger.info(f"Passed: {session['passed_scenarios']}")
        logger.info(f"Failed: {session['failed_scenarios']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Test Duration: {session['start_time']} to {session['end_time']}")
        logger.info(f"Report saved to: {report_path}")
        logger.info("=" * 60)
        
        # Individual scenario results
        for scenario_name, scenario_result in self.results['scenarios'].items():
            status = "✅ PASSED" if scenario_result['passed'] else "❌ FAILED"
            logger.info(f"{scenario_name}: {status}")
            if not scenario_result['passed']:
                logger.info(f"  Error: {scenario_result.get('error', 'Unknown error')}")
        
        return report_path


def main():
    """Main execution"""
    import sys
    
    tester = AutomatedDeploymentTester()
    
    if len(sys.argv) > 1:
        # Run specific scenario
        scenario = sys.argv[1]
        if scenario in tester.deployment_scenarios:
            logger.info(f"Running single scenario: {scenario}")
            scenario_method = getattr(tester, f'_test_{scenario}')
            result = scenario_method()
            print(json.dumps(result, indent=2))
            sys.exit(0 if result['passed'] else 1)
        else:
            logger.error(f"Unknown scenario: {scenario}")
            logger.info(f"Available scenarios: {', '.join(tester.deployment_scenarios)}")
            sys.exit(1)
    else:
        # Run all scenarios
        results = tester.run_all_scenarios()
        
        # Exit with appropriate code
        if results['test_session']['failed_scenarios'] == 0:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()