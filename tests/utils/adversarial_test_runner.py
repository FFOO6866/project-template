"""
Adversarial Test Runner - Orchestrates Red Team Testing Infrastructure

This module provides the test execution infrastructure for running adversarial 
quotation tests against the live system with real Docker infrastructure.

CRITICAL: NO MOCK DATA - All tests run against actual services.
"""

import asyncio
import docker
import time
import logging
import json
import subprocess
import signal
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import psycopg2
import redis
import requests
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestInfrastructureConfig:
    """Configuration for test infrastructure."""
    postgres_host: str = 'localhost'
    postgres_port: int = 5434
    postgres_db: str = 'horme_test'
    postgres_user: str = 'test_user'
    postgres_password: str = 'test_password'
    
    redis_host: str = 'localhost'
    redis_port: int = 6380
    redis_db: int = 0
    
    minio_host: str = 'localhost'
    minio_port: int = 9001
    minio_access_key: str = 'testuser'
    minio_secret_key: str = 'testpass123'
    
    api_host: str = 'localhost'
    api_port: int = 8000
    
    mcp_host: str = 'localhost'  
    mcp_port: int = 3002

class AdversarialTestInfrastructure:
    """Manages real test infrastructure for adversarial testing."""
    
    def __init__(self, config: Optional[TestInfrastructureConfig] = None):
        self.config = config or TestInfrastructureConfig()
        self.docker_client = None
        self.containers = {}
        self.infrastructure_ready = False
        
    def setup_infrastructure(self) -> bool:
        """Setup real Docker infrastructure for testing."""
        logger.info("Setting up real test infrastructure...")
        
        try:
            # Initialize Docker client
            self.docker_client = docker.from_env()
            logger.info("✅ Docker client connected")
            
            # Start test infrastructure using docker-compose
            result = self._start_test_containers()
            if not result:
                logger.error("❌ Failed to start test containers")
                return False
            
            # Wait for services to be ready
            ready = self._wait_for_services_ready(timeout=120)
            if not ready:
                logger.error("❌ Services did not become ready within timeout")
                return False
                
            # Validate all connections
            validation = self._validate_infrastructure_connectivity()
            if not validation:
                logger.error("❌ Infrastructure connectivity validation failed")
                return False
                
            self.infrastructure_ready = True
            logger.info("✅ Test infrastructure is ready")
            return True
            
        except Exception as e:
            logger.error(f"❌ Infrastructure setup failed: {e}")
            return False
    
    def _start_test_containers(self) -> bool:
        """Start test containers using docker-compose."""
        try:
            # Use the test docker-compose file
            compose_file = Path(__file__).parent / 'docker-compose.test.yml'
            
            if not compose_file.exists():
                logger.error(f"Docker compose file not found: {compose_file}")
                return False
            
            # Start containers
            cmd = [
                'docker-compose', 
                '-f', str(compose_file),
                'up', '-d',
                '--remove-orphans'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Docker compose failed: {result.stderr}")
                return False
            
            logger.info("✅ Test containers started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start containers: {e}")
            return False
    
    def _wait_for_services_ready(self, timeout: int = 120) -> bool:
        """Wait for all services to be healthy and ready."""
        logger.info(f"Waiting for services to be ready (timeout: {timeout}s)...")
        
        start_time = time.time()
        services = {
            'PostgreSQL': self._check_postgres_ready,
            'Redis': self._check_redis_ready,
            'MinIO': self._check_minio_ready
        }
        
        while time.time() - start_time < timeout:
            all_ready = True
            
            for service_name, check_func in services.items():
                if not check_func():
                    all_ready = False
                    logger.info(f"⏳ {service_name} not ready yet...")
                    break
                else:
                    logger.info(f"✅ {service_name} is ready")
            
            if all_ready:
                logger.info("✅ All services are ready")
                return True
            
            time.sleep(5)
        
        logger.error(f"❌ Services not ready within {timeout}s timeout")
        return False
    
    def _check_postgres_ready(self) -> bool:
        """Check if PostgreSQL is ready."""
        try:
            conn = psycopg2.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password,
                connect_timeout=5
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
            return True
        except Exception:
            return False
    
    def _check_redis_ready(self) -> bool:
        """Check if Redis is ready."""
        try:
            client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            client.ping()
            return True
        except Exception:
            return False
    
    def _check_minio_ready(self) -> bool:
        """Check if MinIO is ready."""
        try:
            response = requests.get(
                f'http://{self.config.minio_host}:{self.config.minio_port}/minio/health/live',
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _validate_infrastructure_connectivity(self) -> bool:
        """Validate full infrastructure connectivity."""
        logger.info("Validating infrastructure connectivity...")
        
        validations = {
            'postgres_connection': self._validate_postgres_connection,
            'redis_connection': self._validate_redis_connection,
            'minio_connection': self._validate_minio_connection
        }
        
        all_valid = True
        for validation_name, validation_func in validations.items():
            try:
                if validation_func():
                    logger.info(f"✅ {validation_name} validated")
                else:
                    logger.error(f"❌ {validation_name} validation failed")
                    all_valid = False
            except Exception as e:
                logger.error(f"❌ {validation_name} validation error: {e}")
                all_valid = False
        
        return all_valid
    
    def _validate_postgres_connection(self) -> bool:
        """Validate PostgreSQL connection and basic operations."""
        try:
            conn = psycopg2.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password
            )
            cursor = conn.cursor()
            
            # Test table creation
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS infrastructure_test (
                    id SERIAL PRIMARY KEY,
                    test_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Test insert/select
            cursor.execute("INSERT INTO infrastructure_test (test_value) VALUES (%s)", ('connectivity_test',))
            cursor.execute("SELECT test_value FROM infrastructure_test WHERE test_value = %s", ('connectivity_test',))
            result = cursor.fetchone()
            
            # Cleanup
            cursor.execute("DELETE FROM infrastructure_test WHERE test_value = %s", ('connectivity_test',))
            conn.commit()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"PostgreSQL validation failed: {e}")
            return False
    
    def _validate_redis_connection(self) -> bool:
        """Validate Redis connection and basic operations."""
        try:
            client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db
            )
            
            # Test set/get
            test_key = 'infrastructure_test'
            test_value = 'connectivity_test'
            
            client.set(test_key, test_value)
            retrieved_value = client.get(test_key)
            client.delete(test_key)
            
            return retrieved_value.decode() == test_value if retrieved_value else False
            
        except Exception as e:
            logger.error(f"Redis validation failed: {e}")
            return False
    
    def _validate_minio_connection(self) -> bool:
        """Validate MinIO connection and basic operations."""
        try:
            # Basic health check
            response = requests.get(
                f'http://{self.config.minio_host}:{self.config.minio_port}/minio/health/live',
                timeout=5
            )
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"MinIO validation failed: {e}")
            return False
    
    def get_infrastructure_status(self) -> Dict[str, Any]:
        """Get current infrastructure status."""
        if not self.infrastructure_ready:
            return {'ready': False, 'message': 'Infrastructure not initialized'}
        
        status = {
            'ready': True,
            'services': {
                'postgres': {
                    'ready': self._check_postgres_ready(),
                    'connection_string': f'postgresql://{self.config.postgres_user}:***@{self.config.postgres_host}:{self.config.postgres_port}/{self.config.postgres_db}'
                },
                'redis': {
                    'ready': self._check_redis_ready(),
                    'connection_string': f'redis://{self.config.redis_host}:{self.config.redis_port}/{self.config.redis_db}'
                },
                'minio': {
                    'ready': self._check_minio_ready(),
                    'endpoint': f'http://{self.config.minio_host}:{self.config.minio_port}'
                }
            }
        }
        
        return status
    
    def cleanup_infrastructure(self):
        """Cleanup test infrastructure."""
        logger.info("Cleaning up test infrastructure...")
        
        try:
            compose_file = Path(__file__).parent / 'docker-compose.test.yml'
            
            if compose_file.exists():
                cmd = [
                    'docker-compose', 
                    '-f', str(compose_file),
                    'down', '--volumes', '--remove-orphans'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("✅ Test infrastructure cleaned up")
                else:
                    logger.warning(f"⚠️ Cleanup warning: {result.stderr}")
            
            self.infrastructure_ready = False
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

class AdversarialTestExecutor:
    """Execute adversarial tests with real infrastructure coordination."""
    
    def __init__(self):
        self.infrastructure = AdversarialTestInfrastructure()
        self.test_results = []
        self.execution_context = {}
    
    def setup_test_environment(self) -> bool:
        """Setup complete test environment."""
        logger.info("🔄 Setting up adversarial test environment...")
        
        # Setup infrastructure
        if not self.infrastructure.setup_infrastructure():
            return False
        
        # Prepare test databases and schemas
        if not self._prepare_test_databases():
            return False
        
        # Validate quotation system integration
        if not self._validate_quotation_system_integration():
            return False
        
        logger.info("✅ Test environment ready for adversarial testing")
        return True
    
    def _prepare_test_databases(self) -> bool:
        """Prepare test databases with required schemas."""
        logger.info("Preparing test databases...")
        
        try:
            # PostgreSQL schema setup
            conn = psycopg2.connect(
                host=self.infrastructure.config.postgres_host,
                port=self.infrastructure.config.postgres_port,
                database=self.infrastructure.config.postgres_db,
                user=self.infrastructure.config.postgres_user,
                password=self.infrastructure.config.postgres_password
            )
            cursor = conn.cursor()
            
            # Create adversarial test results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS adversarial_test_results (
                    id SERIAL PRIMARY KEY,
                    test_id VARCHAR(255) UNIQUE NOT NULL,
                    category VARCHAR(100),
                    attack_type VARCHAR(100),
                    severity VARCHAR(50),
                    success BOOLEAN,
                    precision DECIMAL(5,4),
                    recall DECIMAL(5,4),
                    f1_score DECIMAL(5,4),
                    financial_accuracy DECIMAL(5,4),
                    processing_time_ms INTEGER,
                    vulnerabilities TEXT,
                    business_failures TEXT,
                    test_data JSONB,
                    result_data JSONB,
                    test_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_adversarial_test_category ON adversarial_test_results(category);
                CREATE INDEX IF NOT EXISTS idx_adversarial_test_attack_type ON adversarial_test_results(attack_type);
                CREATE INDEX IF NOT EXISTS idx_adversarial_test_timestamp ON adversarial_test_results(test_timestamp);
            """)
            
            # Create quotation test tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quotation_test_tracking (
                    id SERIAL PRIMARY KEY,
                    quote_number VARCHAR(255),
                    test_id VARCHAR(255),
                    customer_name VARCHAR(255),
                    total_amount DECIMAL(10,2),
                    processing_status VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ PostgreSQL schemas prepared")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database preparation failed: {e}")
            return False
    
    def _validate_quotation_system_integration(self) -> bool:
        """Validate integration with quotation system."""
        logger.info("Validating quotation system integration...")
        
        try:
            # Import and test quotation system components
            from src.workflows.quotation_generation import QuotationGenerationWorkflow
            from kailash.runtime.local import LocalRuntime
            
            # Create test workflow
            workflow = QuotationGenerationWorkflow()
            runtime = LocalRuntime()
            
            # Test basic functionality
            test_requirements = [{
                'description': 'Integration Test Tool',
                'category': 'test',
                'quantity': 1
            }]
            
            test_pricing = {
                'pricing_results': {
                    'test_item': {
                        'product_id': 'TEST-001',
                        'product_name': 'Integration Test Product',
                        'final_unit_price': 100.00,
                        'total_price': 100.00,
                        'quantity': 1,
                        'savings_breakdown': {'total_savings': 0.0}
                    }
                }
            }
            
            result = workflow.execute_quotation_generation(
                test_requirements, 
                test_pricing,
                customer_name='Integration Test Customer'
            )
            
            if result.get('success'):
                logger.info("✅ Quotation system integration validated")
                return True
            else:
                logger.error(f"❌ Quotation system integration failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Quotation system validation failed: {e}")
            return False
    
    @contextmanager
    def test_execution_context(self):
        """Context manager for test execution."""
        try:
            # Setup
            if not self.setup_test_environment():
                raise RuntimeError("Failed to setup test environment")
            
            self.execution_context = {
                'start_time': time.time(),
                'infrastructure_status': self.infrastructure.get_infrastructure_status()
            }
            
            yield self
            
        finally:
            # Cleanup
            self.execution_context['end_time'] = time.time()
            self.execution_context['duration'] = self.execution_context['end_time'] - self.execution_context['start_time']
            
            # Generate execution report
            self._generate_execution_report()
            
            # Cleanup infrastructure
            self.infrastructure.cleanup_infrastructure()
    
    def _generate_execution_report(self):
        """Generate test execution report."""
        report = {
            'execution_summary': {
                'start_time': self.execution_context.get('start_time'),
                'end_time': self.execution_context.get('end_time'),
                'total_duration': self.execution_context.get('duration'),
                'infrastructure_status': self.execution_context.get('infrastructure_status')
            },
            'test_results_summary': {
                'total_tests_executed': len(self.test_results),
                'infrastructure_type': 'real_docker_containers',
                'mocking_used': False
            }
        }
        
        # Save execution report
        report_path = Path('adversarial_test_execution_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📊 Execution report saved: {report_path}")

def run_adversarial_tests():
    """Main function to run adversarial tests with real infrastructure."""
    
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("🛑 Received shutdown signal, cleaning up...")
        sys.exit(0)
    
    # Setup signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    executor = AdversarialTestExecutor()
    
    try:
        with executor.test_execution_context():
            logger.info("🚀 Starting adversarial quotation tests...")
            
            # Import test components
            from test_adversarial_quotation_generator import AdversarialRFQGenerator, QuotationSystemValidator
            
            # Generate test cases
            generator = AdversarialRFQGenerator(seed=42)
            test_cases = generator.generate_all_test_cases()
            logger.info(f"Generated {len(test_cases)} adversarial test cases")
            
            # Execute validation
            validator = QuotationSystemValidator()
            results = validator.validate_test_suite(test_cases, parallel_workers=8)
            
            # Store results
            executor.test_results = results
            
            logger.info("✅ Adversarial testing completed successfully")
            return results
            
    except Exception as e:
        logger.error(f"❌ Adversarial testing failed: {e}")
        raise

if __name__ == "__main__":
    """Execute adversarial testing infrastructure."""
    
    print("🔴 ADVERSARIAL TEST INFRASTRUCTURE")
    print("=" * 50)
    print("🐳 Using REAL Docker containers")
    print("🚫 NO MOCK DATA ALLOWED")
    print("🔧 PostgreSQL + Redis + MinIO + Real APIs")
    print("=" * 50)
    
    try:
        results = run_adversarial_tests()
        print("✅ Adversarial testing infrastructure execution completed")
        
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        sys.exit(1)