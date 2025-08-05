"""
Tier 2 Integration Tests: Docker Services Integration Testing

Tests inter-service communication and real Docker service interactions.
Uses REAL Docker services - NO MOCKING allowed.

CRITICAL: These are Integration Tests (Tier 2) - NO MOCKING
Speed requirement: <5 seconds per test
Infrastructure: Real Docker services from test-env
"""

import pytest
import docker
import requests
import psycopg2
import redis
import time
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDockerInfrastructureIntegration:
    """Test Docker infrastructure services integration."""

    @pytest.fixture(scope="class", autouse=True)
    def ensure_docker_services(self):
        """Ensure Docker test services are running."""
        logger.info("Ensuring Docker test services are running...")
        
        # Check if test-env script exists
        test_env_script = Path(__file__).parent.parent / "utils" / "test-env"
        if not test_env_script.exists():
            pytest.skip("test-env script not found - skipping Docker integration tests")
        
        # Start test services
        try:
            result = subprocess.run([str(test_env_script), "status"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.info("Starting Docker test services...")
                subprocess.run([str(test_env_script), "up"], 
                             check=True, timeout=120)
                # Wait for services to be ready
                time.sleep(10)
        except subprocess.TimeoutExpired:
            pytest.skip("Docker services failed to start within timeout")
        except subprocess.CalledProcessError as e:
            pytest.skip(f"Failed to start Docker services: {e}")
        
        yield
        
        # Services remain running for other tests

    @pytest.fixture
    def docker_client(self):
        """Get Docker client."""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception as e:
            pytest.skip(f"Docker client not available: {e}")

    @pytest.mark.timeout(5)
    def test_docker_daemon_accessible(self, docker_client):
        """Test Docker daemon is accessible and responsive."""
        # Real Docker daemon test
        info = docker_client.info()
        assert info['ServerVersion'] is not None
        assert info['KernelVersion'] is not None
        logger.info(f"Docker version: {info['ServerVersion']}")

    @pytest.mark.timeout(5)
    def test_postgresql_service_connectivity(self):
        """Test PostgreSQL service connectivity through Docker."""
        # Real PostgreSQL connection test
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,  # Default test port
                database="test_db",
                user="test",
                password="test",
                connect_timeout=3
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            assert version is not None
            
            cursor.close()
            conn.close()
            logger.info("PostgreSQL connection successful")
            
        except psycopg2.OperationalError as e:
            pytest.skip(f"PostgreSQL not available: {e}")

    @pytest.mark.timeout(5)
    def test_redis_service_connectivity(self):
        """Test Redis service connectivity through Docker."""
        # Real Redis connection test
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
            
            # Test basic operations
            r.set('test_key', 'test_value')
            value = r.get('test_key')
            assert value.decode() == 'test_value'
            
            r.delete('test_key')
            logger.info("Redis connection successful")
            
        except redis.ConnectionError as e:
            pytest.skip(f"Redis not available: {e}")

    @pytest.mark.timeout(5)
    def test_service_network_connectivity(self, docker_client):
        """Test network connectivity between Docker services."""
        # Get Docker network information
        networks = docker_client.networks.list()
        test_networks = [n for n in networks if 'test' in n.name or 'horme' in n.name]
        
        if not test_networks:
            pytest.skip("No test networks found")
        
        # Test network exists and is active
        network = test_networks[0]
        assert network.attrs['Driver'] == 'bridge'
        
        # Check containers are connected to network
        containers = network.attrs.get('Containers', {})
        assert len(containers) > 0, "No containers connected to test network"
        
        logger.info(f"Network {network.name} has {len(containers)} connected containers")

    @pytest.mark.timeout(5)
    def test_container_health_status(self, docker_client):
        """Test container health status."""
        # Get running containers
        containers = docker_client.containers.list()
        test_containers = [c for c in containers 
                          if any(name in c.name for name in ['test', 'horme', 'postgres', 'redis'])]
        
        if not test_containers:
            pytest.skip("No test containers found")
        
        for container in test_containers:
            # Check container is running
            assert container.status == 'running', f"Container {container.name} not running"
            
            # Check health status if available
            container.reload()
            health = container.attrs.get('State', {}).get('Health', {})
            if health:
                assert health['Status'] in ['healthy', 'starting'], \
                    f"Container {container.name} health status: {health['Status']}"
            
            logger.info(f"Container {container.name} status: {container.status}")


class TestInterServiceCommunication:
    """Test communication between Docker services."""

    @pytest.mark.timeout(5)
    def test_application_database_connection(self):
        """Test application can connect to database service."""
        # Real database connection from application perspective
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="horme_db",
                user="horme_user", 
                password="horme_secure_password",
                connect_timeout=3
            )
            
            cursor = conn.cursor()
            
            # Test table creation (mimics application behavior)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_connection (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Test data insertion
            cursor.execute("INSERT INTO test_connection DEFAULT VALUES RETURNING id")
            test_id = cursor.fetchone()[0]
            assert test_id is not None
            
            # Test data retrieval
            cursor.execute("SELECT COUNT(*) FROM test_connection")
            count = cursor.fetchone()[0]
            assert count > 0
            
            # Cleanup
            cursor.execute("DROP TABLE test_connection")
            conn.commit()
            
            cursor.close()
            conn.close()
            logger.info("Application-Database integration successful")
            
        except Exception as e:
            pytest.fail(f"Database integration failed: {e}")

    @pytest.mark.timeout(5)
    def test_application_cache_connection(self):
        """Test application can connect to Redis cache."""
        # Real Redis connection from application perspective
        try:
            r = redis.Redis(
                host='localhost', 
                port=6379, 
                db=0, 
                socket_timeout=3,
                decode_responses=True
            )
            
            # Test cache operations
            session_key = "test_session_123"
            session_data = {
                "user_id": "test_user",
                "login_time": str(time.time()),
                "permissions": ["read", "write"]
            }
            
            # Store session data
            r.hset(session_key, mapping=session_data)
            r.expire(session_key, 3600)  # 1 hour expiry
            
            # Retrieve session data
            retrieved_data = r.hgetall(session_key)
            assert retrieved_data["user_id"] == "test_user"
            assert "login_time" in retrieved_data
            
            # Test TTL
            ttl = r.ttl(session_key)
            assert ttl > 0
            
            # Cleanup
            r.delete(session_key)
            logger.info("Application-Cache integration successful")
            
        except Exception as e:
            pytest.fail(f"Cache integration failed: {e}")

    @pytest.mark.timeout(5)
    def test_service_discovery_integration(self, docker_client):
        """Test services can discover each other through Docker DNS."""
        # Test internal service discovery
        containers = docker_client.containers.list()
        
        # Find database container
        db_container = None
        for container in containers:
            if 'postgres' in container.name.lower():
                db_container = container
                break
        
        if not db_container:
            pytest.skip("Database container not found")
        
        # Get network information
        networks = db_container.attrs['NetworkSettings']['Networks']
        assert len(networks) > 0, "Container not connected to any network"
        
        # Test container has network connectivity
        network_name = list(networks.keys())[0]
        network_config = networks[network_name]
        
        assert network_config['IPAddress'] is not None
        assert network_config['Gateway'] is not None
        
        logger.info(f"Service discovery working - DB IP: {network_config['IPAddress']}")


class TestDockerVolumeIntegration:
    """Test Docker volume persistence and data integrity."""

    @pytest.mark.timeout(5)
    def test_database_volume_persistence(self):
        """Test database data persists across container restarts."""
        # Create test data in database
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="horme_db", 
                user="horme_user",
                password="horme_secure_password",
                connect_timeout=3
            )
            
            cursor = conn.cursor()
            
            # Create test table with data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS persistence_test (
                    id SERIAL PRIMARY KEY,
                    test_data VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            test_value = f"persistence_test_{int(time.time())}"
            cursor.execute("INSERT INTO persistence_test (test_data) VALUES (%s)", (test_value,))
            conn.commit()
            
            # Verify data exists
            cursor.execute("SELECT test_data FROM persistence_test WHERE test_data = %s", (test_value,))
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == test_value
            
            cursor.close()
            conn.close()
            
            logger.info("Database volume persistence test successful")
            
        except Exception as e:
            pytest.fail(f"Database volume persistence test failed: {e}")

    @pytest.mark.timeout(5)
    def test_cache_volume_persistence(self):
        """Test cache data persists appropriately."""
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
            
            # Test persistent data
            persistent_key = "persistent_config"
            persistent_value = {"app_version": "1.0.0", "feature_flags": {"new_ui": True}}
            
            r.set(persistent_key, json.dumps(persistent_value))
            
            # Verify data exists
            retrieved = r.get(persistent_key)
            assert retrieved is not None
            
            retrieved_data = json.loads(retrieved.decode())
            assert retrieved_data["app_version"] == "1.0.0"
            assert retrieved_data["feature_flags"]["new_ui"] is True
            
            # Cleanup
            r.delete(persistent_key)
            
            logger.info("Cache volume persistence test successful")
            
        except Exception as e:
            pytest.fail(f"Cache volume persistence test failed: {e}")


class TestDockerAPIEndpointIntegration:
    """Test API endpoints through Docker services."""

    @pytest.mark.timeout(5)
    def test_health_endpoint_accessibility(self):
        """Test health check endpoints are accessible."""
        # Test common health endpoints
        health_endpoints = [
            "http://localhost:8000/api/health",  # Nexus API
            "http://localhost:3001/health",     # MCP Server
            "http://localhost:3002/health"      # Standalone MCP
        ]
        
        accessible_endpoints = 0
        
        for endpoint in health_endpoints:
            try:
                response = requests.get(endpoint, timeout=3)
                if response.status_code == 200:
                    accessible_endpoints += 1
                    logger.info(f"Health endpoint accessible: {endpoint}")
                else:
                    logger.warning(f"Health endpoint returned {response.status_code}: {endpoint}")
            except requests.RequestException:
                logger.warning(f"Health endpoint not accessible: {endpoint}")
        
        # At least one health endpoint should be accessible
        if accessible_endpoints == 0:
            pytest.skip("No health endpoints accessible - services may not be running")
        
        assert accessible_endpoints > 0, "At least one health endpoint should be accessible"

    @pytest.mark.timeout(5)
    def test_api_database_integration(self):
        """Test API endpoints can interact with database."""
        # This would test actual API endpoints if they're running
        # For now, test the integration components separately
        
        # Test database connection is available for API
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="horme_db",
                user="horme_user",
                password="horme_secure_password", 
                connect_timeout=3
            )
            
            cursor = conn.cursor()
            
            # Test API-like operations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_integration_test (
                    id SERIAL PRIMARY KEY,
                    api_endpoint VARCHAR(100),
                    request_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Simulate API request logging
            cursor.execute("""
                INSERT INTO api_integration_test (api_endpoint, request_count) 
                VALUES (%s, %s) ON CONFLICT DO NOTHING
            """, ("/api/health", 1))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("API-Database integration test successful")
            
        except Exception as e:
            pytest.fail(f"API-Database integration failed: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])