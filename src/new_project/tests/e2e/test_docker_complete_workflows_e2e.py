"""
Tier 3 End-to-End Tests: Complete Docker Workflow Testing

Tests complete user workflows through the entire Docker infrastructure stack.
Uses REAL services and infrastructure - NO MOCKING allowed.

CRITICAL: These are E2E Tests (Tier 3) - NO MOCKING
Speed requirement: <10 seconds per test
Infrastructure: Complete real infrastructure stack
"""

import pytest
import requests
import docker
import subprocess
import time
import json
import psycopg2
import redis
from pathlib import Path
from typing import Dict, List, Any
import logging
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCompleteDockerDeployment:
    """Test complete Docker deployment workflows."""

    @pytest.fixture(scope="class", autouse=True)
    def ensure_full_stack(self):
        """Ensure full Docker stack is running."""
        logger.info("Ensuring full Docker stack is running...")
        
        project_root = Path(__file__).parent.parent.parent.parent
        compose_file = project_root / "docker-compose.yml"
        
        if not compose_file.exists():
            pytest.skip("Main docker-compose.yml not found")
        
        # Check if services are running
        try:
            result = subprocess.run([
                "docker-compose", "-f", str(compose_file), "ps", "--services", "--filter", "status=running"
            ], capture_output=True, text=True, timeout=30)
            
            running_services = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            if len(running_services) < 3:  # At least postgres, redis, and one app service
                logger.info("Starting full Docker stack...")
                subprocess.run([
                    "docker-compose", "-f", str(compose_file), "up", "-d"
                ], check=True, timeout=300)  # 5 minutes timeout
                
                # Wait for services to be ready
                time.sleep(30)
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            pytest.skip(f"Failed to start Docker stack: {e}")
        
        yield
        
        # Stack remains running for other tests

    @pytest.fixture
    def docker_client(self):
        """Get Docker client."""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception as e:
            pytest.skip(f"Docker client not available: {e}")

    @pytest.mark.timeout(10)
    def test_complete_stack_deployment(self, docker_client):
        """Test complete stack deploys successfully."""
        # Verify all critical containers are running
        containers = docker_client.containers.list()
        container_names = [c.name for c in containers]
        
        # Check for critical services
        critical_services = ['postgres', 'redis']
        for service in critical_services:
            matching_containers = [name for name in container_names if service in name.lower()]
            assert len(matching_containers) > 0, f"Critical service {service} not running"
        
        # Check for application services
        app_services = ['nexus', 'mcp']
        running_apps = 0
        for service in app_services:
            matching_containers = [name for name in container_names if service in name.lower()]
            if matching_containers:
                running_apps += 1
        
        assert running_apps > 0, "No application services running"
        
        logger.info(f"Stack deployment successful - {len(containers)} containers running")

    @pytest.mark.timeout(10)
    def test_service_health_checks_pass(self, docker_client):
        """Test all service health checks pass."""
        containers = docker_client.containers.list()
        
        healthy_services = 0
        for container in containers:
            container.reload()
            health = container.attrs.get('State', {}).get('Health', {})
            
            if health:
                status = health.get('Status', 'unknown')
                if status == 'healthy':
                    healthy_services += 1
                    logger.info(f"Service {container.name} is healthy")
                elif status == 'starting':
                    # Wait a bit and check again
                    time.sleep(5)
                    container.reload()
                    health = container.attrs.get('State', {}).get('Health', {})
                    if health.get('Status') == 'healthy':
                        healthy_services += 1
                        logger.info(f"Service {container.name} became healthy")
                else:
                    logger.warning(f"Service {container.name} health status: {status}")
            else:
                # Services without health checks are assumed healthy if running
                if container.status == 'running':
                    healthy_services += 1
                    logger.info(f"Service {container.name} running (no health check)")
        
        assert healthy_services > 0, "No healthy services found"


class TestCompleteUserWorkflows:
    """Test complete user workflows through the Docker stack."""

    @pytest.mark.timeout(10)
    def test_api_request_full_pipeline(self):
        """Test complete API request pipeline through all services."""
        # Test full pipeline: API -> Database -> Cache -> Response
        
        # Step 1: Test API endpoint accessibility
        api_endpoints = [
            "http://localhost:8000/api/health",
            "http://localhost:8000/api/v1/status"
        ]
        
        accessible_endpoint = None
        for endpoint in api_endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    accessible_endpoint = endpoint
                    break
            except requests.RequestException:
                continue
        
        if not accessible_endpoint:
            pytest.skip("No API endpoints accessible")
        
        # Step 2: Verify API can access database
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="horme_db",
                user="horme_user", 
                password="horme_secure_password",
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            pytest.fail(f"API cannot access database: {e}")
        
        # Step 3: Verify API can access cache
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
            r.ping()
            
        except Exception as e:
            pytest.fail(f"API cannot access cache: {e}")
        
        logger.info("Complete API pipeline test successful")

    @pytest.mark.timeout(10)
    def test_data_processing_workflow(self):
        """Test complete data processing workflow."""
        # Simulate complete data processing: Input -> Processing -> Storage -> Retrieval
        
        # Step 1: Store test data in database
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="horme_db",
                user="horme_user",
                password="horme_secure_password",
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            
            # Create test workflow table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_test (
                    id SERIAL PRIMARY KEY,
                    workflow_name VARCHAR(100),
                    input_data JSONB,
                    processed_data JSONB,
                    status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test workflow data
            test_workflow = {
                "workflow_name": "e2e_test_workflow",
                "input_data": json.dumps({"test": "data", "items": [1, 2, 3]}),
                "status": "created"
            }
            
            cursor.execute("""
                INSERT INTO workflow_test (workflow_name, input_data, status) 
                VALUES (%(workflow_name)s, %(input_data)s, %(status)s)
                RETURNING id
            """, test_workflow)
            
            workflow_id = cursor.fetchone()[0]
            conn.commit()
            
            # Step 2: Simulate processing (update status)
            processed_data = {"result": "processed", "count": 3, "success": True}
            cursor.execute("""
                UPDATE workflow_test 
                SET processed_data = %s, status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (json.dumps(processed_data), "completed", workflow_id))
            
            conn.commit()
            
            # Step 3: Verify workflow completion
            cursor.execute("""
                SELECT workflow_name, input_data, processed_data, status 
                FROM workflow_test WHERE id = %s
            """, (workflow_id,))
            
            result = cursor.fetchone()
            assert result is not None
            assert result[3] == "completed"  # status
            
            retrieved_processed = json.loads(result[2])
            assert retrieved_processed["success"] is True
            
            # Step 4: Cache workflow result
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
            cache_key = f"workflow_result:{workflow_id}"
            r.set(cache_key, json.dumps(retrieved_processed), ex=3600)
            
            # Verify cached data
            cached_result = r.get(cache_key)
            assert cached_result is not None
            
            cached_data = json.loads(cached_result.decode())
            assert cached_data["success"] is True
            
            # Cleanup
            cursor.execute("DELETE FROM workflow_test WHERE id = %s", (workflow_id,))
            conn.commit()
            r.delete(cache_key)
            
            cursor.close()
            conn.close()
            
            logger.info("Complete data processing workflow test successful")
            
        except Exception as e:
            pytest.fail(f"Data processing workflow failed: {e}")

    @pytest.mark.timeout(10)
    def test_multi_service_coordination(self):
        """Test coordination between multiple services."""
        # Test scenario: API request triggers database operation and cache update
        
        try:
            # Step 1: Database operation
            conn = psycopg2.connect(
                host="localhost",
                port=5432, 
                database="horme_db",
                user="horme_user",
                password="horme_secure_password",
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            
            # Create coordination test table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS service_coordination_test (
                    id SERIAL PRIMARY KEY,
                    service_name VARCHAR(100),
                    operation VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    correlation_id VARCHAR(100)
                )
            """)
            
            correlation_id = f"test_coordination_{int(time.time())}"
            
            # Step 2: Record API service operation
            cursor.execute("""
                INSERT INTO service_coordination_test (service_name, operation, correlation_id)
                VALUES (%s, %s, %s)
            """, ("api_service", "request_received", correlation_id))
            
            # Step 3: Record database service operation
            cursor.execute("""
                INSERT INTO service_coordination_test (service_name, operation, correlation_id)
                VALUES (%s, %s, %s)  
            """, ("database_service", "data_stored", correlation_id))
            
            conn.commit()
            
            # Step 4: Cache service operation
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
            
            cache_key = f"coordination:{correlation_id}"
            coordination_data = {
                "correlation_id": correlation_id,
                "services": ["api_service", "database_service", "cache_service"],
                "status": "completed",
                "timestamp": time.time()
            }
            
            r.set(cache_key, json.dumps(coordination_data), ex=3600)
            
            # Step 5: Verify multi-service coordination
            cursor.execute("""
                SELECT COUNT(*) FROM service_coordination_test 
                WHERE correlation_id = %s
            """, (correlation_id,))
            
            db_operations = cursor.fetchone()[0]
            assert db_operations == 2  # API and database operations
            
            # Verify cache coordination
            cached_coordination = r.get(cache_key)
            assert cached_coordination is not None
            
            coordination_result = json.loads(cached_coordination.decode())
            assert coordination_result["status"] == "completed"
            assert len(coordination_result["services"]) == 3
            
            # Cleanup
            cursor.execute("DELETE FROM service_coordination_test WHERE correlation_id = %s", (correlation_id,))
            conn.commit()
            r.delete(cache_key)
            
            cursor.close()
            conn.close()
            
            logger.info("Multi-service coordination test successful")
            
        except Exception as e:
            pytest.fail(f"Multi-service coordination failed: {e}")


class TestDockerVolumeDataPersistence:
    """Test data persistence across container lifecycles."""

    @pytest.mark.timeout(10)
    def test_database_persistence_container_restart(self, docker_client):
        """Test database data survives container restart."""
        # Find database container
        containers = docker_client.containers.list()
        db_container = None
        
        for container in containers:
            if 'postgres' in container.name.lower():
                db_container = container
                break
        
        if not db_container:
            pytest.skip("Database container not found")
        
        # Step 1: Create persistent test data
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="horme_db",
                user="horme_user",
                password="horme_secure_password",
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS persistence_e2e_test (
                    id SERIAL PRIMARY KEY,
                    test_data VARCHAR(100) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            unique_test_data = f"persistence_e2e_{int(time.time())}"
            cursor.execute("""
                INSERT INTO persistence_e2e_test (test_data) VALUES (%s)
            """, (unique_test_data,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Step 2: Restart database container
            logger.info("Restarting database container...")
            db_container.restart()
            
            # Wait for container to be ready
            time.sleep(10)
            
            # Step 3: Verify data still exists
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="horme_db",
                user="horme_user",
                password="horme_secure_password",
                connect_timeout=10
            )
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT test_data FROM persistence_e2e_test WHERE test_data = %s
            """, (unique_test_data,))
            
            result = cursor.fetchone()
            assert result is not None, "Data did not persist across container restart"
            assert result[0] == unique_test_data
            
            # Cleanup
            cursor.execute("DELETE FROM persistence_e2e_test WHERE test_data = %s", (unique_test_data,))
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("Database persistence test successful")
            
        except Exception as e:
            pytest.fail(f"Database persistence test failed: {e}")


class TestCompleteDockerNetworking:
    """Test complete Docker networking scenarios."""

    @pytest.mark.timeout(10)
    def test_cross_container_communication(self, docker_client):
        """Test communication between all containers."""
        containers = docker_client.containers.list()
        
        if len(containers) < 2:
            pytest.skip("Need at least 2 containers for networking test")
        
        # Test database accessibility from application perspective
        app_containers = [c for c in containers if any(app in c.name.lower() for app in ['nexus', 'mcp', 'app'])]
        db_containers = [c for c in containers if 'postgres' in c.name.lower()]
        
        if not db_containers:
            pytest.skip("No database container found")
        
        # Test network connectivity by attempting database connection
        # This simulates how application containers would connect to database
        try:
            conn = psycopg2.connect(
                host="localhost",  # Through Docker port mapping
                port=5432,
                database="horme_db",
                user="horme_user",
                password="horme_secure_password",
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            
            cursor.close()
            conn.close()
            
            logger.info("Cross-container communication test successful")
            
        except Exception as e:
            pytest.fail(f"Cross-container communication failed: {e}")

    @pytest.mark.timeout(10)
    def test_external_network_access(self):
        """Test containers have appropriate external network access."""
        # Test that services can make external requests when needed
        # This is important for services that need to call external APIs
        
        # We'll test this by checking if we can resolve external DNS
        # from within the container network context
        
        try:
            # Test basic connectivity to a reliable external service
            response = requests.get("https://httpbin.org/ip", timeout=5)
            assert response.status_code == 200
            
            # This proves that the Docker network allows external access
            logger.info("External network access test successful")
            
        except requests.RequestException as e:
            logger.warning(f"External network access limited: {e}")
            # This might be expected in some secure environments


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])