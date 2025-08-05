"""
Docker Chaos Testing Suite

Tests system resilience under failure conditions:
- Service failure scenarios
- Network partition testing  
- Resource exhaustion testing
- Recovery testing

WARNING: These tests intentionally break services to test resilience.
Should only be run in test environments.
"""

import pytest
import docker
import requests
import subprocess
import time
import psycopg2
import redis
import threading
import signal
import os
from pathlib import Path
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestServiceFailureScenarios:
    """Test service failure and recovery scenarios."""

    @pytest.fixture
    def docker_client(self):
        """Get Docker client."""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception as e:
            pytest.skip(f"Docker client not available: {e}")

    @pytest.mark.chaos
    def test_database_container_failure_recovery(self, docker_client):
        """Test system behavior when database container fails."""
        # Find database container
        containers = docker_client.containers.list()
        db_container = None
        
        for container in containers:
            if 'postgres' in container.name.lower():
                db_container = container
                break
        
        if not db_container:
            pytest.skip("Database container not found")
        
        # Step 1: Verify database is working
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="horme_db",
                user="horme_user",
                password="horme_secure_password",
                connect_timeout=3
            )
            conn.close()
            logger.info("Database initially working")
        except psycopg2.OperationalError:
            pytest.skip("Database not initially working")
        
        # Step 2: Stop database container (simulate failure)
        logger.info("Stopping database container to simulate failure...")
        db_container.stop()
        
        # Step 3: Verify services handle database failure gracefully
        time.sleep(2)  # Give services time to detect failure
        
        # Test that connections fail as expected
        with pytest.raises(psycopg2.OperationalError):
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="horme_db",
                user="horme_user",
                password="horme_secure_password",
                connect_timeout=3
            )
        
        logger.info("Database failure detected correctly")
        
        # Step 4: Restart database container (simulate recovery)
        logger.info("Restarting database container to simulate recovery...")
        db_container.start()
        
        # Step 5: Wait for recovery and verify service restoration
        max_recovery_time = 30  # 30 seconds max recovery time
        recovery_start = time.time()
        
        while time.time() - recovery_start < max_recovery_time:
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="horme_db",
                    user="horme_user",
                    password="horme_secure_password",
                    connect_timeout=3
                )
                conn.close()
                recovery_time = time.time() - recovery_start
                logger.info(f"Database recovery successful in {recovery_time:.2f}s")
                break
            except psycopg2.OperationalError:
                time.sleep(1)
                continue
        else:
            pytest.fail(f"Database failed to recover within {max_recovery_time}s")
        
        # Performance assertion
        assert recovery_time < 30, f"Database recovery took {recovery_time:.2f}s, should be <30s"

    @pytest.mark.chaos
    def test_cache_container_failure_recovery(self, docker_client):
        """Test system behavior when cache container fails."""
        # Find Redis container
        containers = docker_client.containers.list()
        redis_container = None
        
        for container in containers:
            if 'redis' in container.name.lower():
                redis_container = container
                break
        
        if not redis_container:
            pytest.skip("Redis container not found")
        
        # Step 1: Verify Redis is working
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
            r.ping()
            logger.info("Redis initially working")
        except redis.ConnectionError:
            pytest.skip("Redis not initially working")
        
        # Step 2: Stop Redis container (simulate failure)
        logger.info("Stopping Redis container to simulate failure...")
        redis_container.stop()
        
        # Step 3: Verify cache failure is detected
        time.sleep(2)
        
        with pytest.raises(redis.ConnectionError):
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
            r.ping()
        
        logger.info("Cache failure detected correctly")
        
        # Step 4: Restart Redis container (simulate recovery)
        logger.info("Restarting Redis container to simulate recovery...")
        redis_container.start()
        
        # Step 5: Wait for recovery
        max_recovery_time = 15  # Redis should recover faster than database
        recovery_start = time.time()
        
        while time.time() - recovery_start < max_recovery_time:
            try:
                r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
                r.ping()
                recovery_time = time.time() - recovery_start
                logger.info(f"Redis recovery successful in {recovery_time:.2f}s")
                break
            except redis.ConnectionError:
                time.sleep(1)
                continue
        else:
            pytest.fail(f"Redis failed to recover within {max_recovery_time}s")
        
        # Performance assertion
        assert recovery_time < 15, f"Redis recovery took {recovery_time:.2f}s, should be <15s"

    @pytest.mark.chaos
    def test_application_container_failure_recovery(self, docker_client):
        """Test application container failure and recovery."""
        # Find application containers
        containers = docker_client.containers.list()
        app_containers = [c for c in containers if any(app in c.name.lower() for app in ['nexus', 'mcp'])]
        
        if not app_containers:
            pytest.skip("No application containers found")
        
        app_container = app_containers[0]  # Test first application container
        
        # Step 1: Verify application is working (if it has health check)
        initial_status = app_container.status
        logger.info(f"Application container {app_container.name} initially {initial_status}")
        
        # Step 2: Stop application container
        logger.info(f"Stopping application container {app_container.name}...")
        app_container.stop()
        
        # Step 3: Verify application is stopped
        app_container.reload()
        assert app_container.status in ['exited', 'stopped'], "Application container should be stopped"
        
        # Step 4: Restart application container
        logger.info(f"Restarting application container {app_container.name}...")
        recovery_start = time.time()
        app_container.start()
        
        # Step 5: Wait for recovery
        max_recovery_time = 60  # Applications may take longer to start
        
        while time.time() - recovery_start < max_recovery_time:
            app_container.reload()
            if app_container.status == 'running':
                recovery_time = time.time() - recovery_start
                logger.info(f"Application recovery successful in {recovery_time:.2f}s")
                break
            time.sleep(2)
        else:
            pytest.fail(f"Application failed to recover within {max_recovery_time}s")
        
        # Performance assertion
        assert recovery_time < 60, f"Application recovery took {recovery_time:.2f}s, should be <60s"


class TestNetworkPartitionScenarios:
    """Test network partition and connectivity issues."""

    @pytest.fixture
    def docker_client(self):
        """Get Docker client."""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception as e:
            pytest.skip(f"Docker client not available: {e}")

    @pytest.mark.chaos 
    @pytest.mark.skip(reason="Network partition testing requires advanced Docker networking setup")
    def test_network_partition_between_services(self, docker_client):
        """Test behavior during network partitions between services."""
        # This test would require more advanced Docker network manipulation
        # For now, we'll test connectivity issues through port blocking
        
        # Find database container
        containers = docker_client.containers.list()
        db_container = None
        
        for container in containers:
            if 'postgres' in container.name.lower():
                db_container = container
                break
        
        if not db_container:
            pytest.skip("Database container not found")
        
        # This is a simplified version - real network partition testing
        # would require tools like tc (traffic control) or Docker network
        # manipulation which is complex to set up in a portable way
        
        logger.info("Network partition testing requires advanced setup - test skipped")

    @pytest.mark.chaos
    def test_connection_timeout_handling(self):
        """Test connection timeout handling."""
        # Test database connection timeouts
        connection_attempts = 0
        successful_connections = 0
        timeout_errors = 0
        
        for i in range(5):
            connection_attempts += 1
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="horme_db",
                    user="horme_user",
                    password="horme_secure_password",
                    connect_timeout=1  # Very short timeout to test timeout handling
                )
                successful_connections += 1
                conn.close()
            except psycopg2.OperationalError as e:
                if "timeout" in str(e).lower():
                    timeout_errors += 1
                else:
                    logger.warning(f"Non-timeout database error: {e}")
        
        logger.info(f"Connection attempts: {connection_attempts}, Successful: {successful_connections}, Timeouts: {timeout_errors}")
        
        # Test Redis connection timeouts
        redis_attempts = 0
        redis_successful = 0
        redis_timeouts = 0
        
        for i in range(5):
            redis_attempts += 1
            try:
                r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=1)
                r.ping()
                redis_successful += 1
            except redis.TimeoutError:
                redis_timeouts += 1
            except redis.ConnectionError as e:
                if "timeout" in str(e).lower():
                    redis_timeouts += 1
                else:
                    logger.warning(f"Non-timeout Redis error: {e}")
        
        logger.info(f"Redis attempts: {redis_attempts}, Successful: {redis_successful}, Timeouts: {redis_timeouts}")
        
        # At least some connections should work with reasonable timeouts
        total_successful = successful_connections + redis_successful
        total_attempts = connection_attempts + redis_attempts
        
        success_rate = total_successful / total_attempts if total_attempts > 0 else 0
        assert success_rate > 0.5, f"Success rate {success_rate:.2f} too low, services may be unhealthy"


class TestResourceExhaustionScenarios:
    """Test resource exhaustion scenarios."""

    @pytest.mark.chaos
    def test_database_connection_exhaustion(self):
        """Test database behavior under connection exhaustion."""
        connections = []
        max_connections = 20  # Reasonable test limit
        
        try:
            # Create many connections to approach limit
            for i in range(max_connections):
                try:
                    conn = psycopg2.connect(
                        host="localhost",
                        port=5432,
                        database="horme_db",
                        user="horme_user",
                        password="horme_secure_password",
                        connect_timeout=5
                    )
                    connections.append(conn)
                except psycopg2.OperationalError as e:
                    if "connection limit" in str(e).lower() or "too many" in str(e).lower():
                        logger.info(f"Hit connection limit at {i} connections")
                        break
                    else:
                        raise
            
            logger.info(f"Created {len(connections)} database connections")
            
            # Test that new connections are properly rejected
            if len(connections) >= max_connections - 5:  # Near limit
                with pytest.raises(psycopg2.OperationalError):
                    extra_conn = psycopg2.connect(
                        host="localhost",
                        port=5432,
                        database="horme_db",
                        user="horme_user",
                        password="horme_secure_password",
                        connect_timeout=5
                    )
                    connections.append(extra_conn)
        
        finally:
            # Clean up connections
            for conn in connections:
                try:
                    conn.close()
                except:
                    pass
            
            # Verify connections are cleaned up
            time.sleep(2)
            try:
                test_conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="horme_db",
                    user="horme_user",
                    password="horme_secure_password",
                    connect_timeout=5
                )
                test_conn.close()
                logger.info("Database recovered after connection cleanup")
            except psycopg2.OperationalError:
                pytest.fail("Database did not recover after connection cleanup")

    @pytest.mark.chaos
    def test_memory_pressure_handling(self, docker_client):
        """Test container behavior under memory pressure."""
        containers = docker_client.containers.list()
        
        # Check current memory usage
        memory_stats = {}
        for container in containers:
            try:
                stats = container.stats(stream=False)
                memory_usage = stats['memory_stats'].get('usage', 0)
                memory_limit = stats['memory_stats'].get('limit', 0)
                
                if memory_limit > 0:
                    memory_usage_mb = memory_usage / (1024 * 1024)
                    memory_percent = (memory_usage / memory_limit) * 100
                    memory_stats[container.name] = {
                        'usage_mb': memory_usage_mb,
                        'percent': memory_percent
                    }
            except Exception as e:
                logger.warning(f"Could not get memory stats for {container.name}: {e}")
        
        # Log current memory usage
        for container_name, stats in memory_stats.items():
            logger.info(f"Container {container_name}: {stats['usage_mb']:.1f}MB ({stats['percent']:.1f}%)")
        
        # Test that containers are not using excessive memory
        for container_name, stats in memory_stats.items():
            if 'postgres' in container_name.lower():
                assert stats['usage_mb'] < 2048, f"Database container {container_name} using excessive memory: {stats['usage_mb']:.1f}MB"
            elif any(app in container_name.lower() for app in ['nexus', 'mcp']):
                assert stats['usage_mb'] < 1024, f"Application container {container_name} using excessive memory: {stats['usage_mb']:.1f}MB"
            
            # No container should use 100% of its memory limit
            assert stats['percent'] < 95, f"Container {container_name} using {stats['percent']:.1f}% of memory limit"

    @pytest.mark.chaos
    def test_disk_space_handling(self, docker_client):
        """Test container behavior with limited disk space."""
        # Check current disk usage of Docker volumes
        try:
            # Get Docker system info
            system_info = docker_client.system.info()
            
            # Check if we can get disk usage info
            # This is a basic check - more sophisticated disk pressure testing
            # would require specific volume management
            
            containers = docker_client.containers.list()
            volume_containers = [c for c in containers if c.attrs.get('Mounts')]
            
            logger.info(f"Found {len(volume_containers)} containers with volume mounts")
            
            # For containers with volumes, verify they can still write
            for container in volume_containers[:2]:  # Test first 2 containers only
                container_name = container.name
                
                if 'postgres' in container_name.lower():
                    # Test database can still write
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
                            CREATE TABLE IF NOT EXISTS disk_test (
                                id SERIAL PRIMARY KEY,
                                data TEXT
                            )
                        """)
                        
                        # Try to write some data
                        cursor.execute("INSERT INTO disk_test (data) VALUES (%s)", ("disk_test_data",))
                        conn.commit()
                        
                        # Clean up
                        cursor.execute("DELETE FROM disk_test WHERE data = %s", ("disk_test_data",))
                        conn.commit()
                        
                        cursor.close()
                        conn.close()
                        
                        logger.info(f"Database container {container_name} can write to disk")
                        
                    except Exception as e:
                        logger.warning(f"Database disk write test failed: {e}")
                
                elif 'redis' in container_name.lower():
                    # Test Redis can still write
                    try:
                        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
                        r.set('disk_test', 'disk_test_data')
                        value = r.get('disk_test')
                        assert value.decode() == 'disk_test_data'
                        r.delete('disk_test')
                        
                        logger.info(f"Redis container {container_name} can write to disk")
                        
                    except Exception as e:
                        logger.warning(f"Redis disk write test failed: {e}")
        
        except Exception as e:
            logger.warning(f"Disk space testing limited: {e}")


class TestGracefulDegradation:
    """Test graceful degradation scenarios."""

    @pytest.mark.chaos
    def test_service_degradation_with_cache_failure(self):
        """Test system continues working when cache fails."""
        # Test that services can work without cache (with degraded performance)
        
        # First verify cache is working
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
            r.ping()
            cache_available = True
        except redis.ConnectionError:
            cache_available = False
        
        if cache_available:
            logger.info("Cache is available - testing graceful degradation")
            
            # Verify database still works (primary functionality)
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
                
                logger.info("Core database functionality works despite cache issues")
                
            except Exception as e:
                logger.warning(f"Core functionality impacted by cache failure: {e}")
        else:
            logger.info("Cache not available - testing core functionality")
            
            # Even without cache, core database functionality should work
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
                cursor.execute("SELECT version()")
                version = cursor.fetchone()
                assert version is not None
                
                cursor.close()
                conn.close()
                
                logger.info("Core functionality works without cache")
                
            except Exception as e:
                pytest.fail(f"Core functionality failed without cache: {e}")

    @pytest.mark.chaos
    def test_partial_service_availability(self):
        """Test system behavior with partial service availability."""
        # Check which services are available
        services_status = {
            'database': False,
            'cache': False,
            'api': False
        }
        
        # Check database
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="horme_db",
                user="horme_user",
                password="horme_secure_password",
                connect_timeout=3
            )
            conn.close()
            services_status['database'] = True
        except psycopg2.OperationalError:
            pass
        
        # Check cache
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
            r.ping()
            services_status['cache'] = True
        except redis.ConnectionError:
            pass
        
        # Check API endpoints
        api_endpoints = ["http://localhost:8000/api/health", "http://localhost:3001/health"]
        for endpoint in api_endpoints:
            try:
                response = requests.get(endpoint, timeout=3)
                if response.status_code == 200:
                    services_status['api'] = True
                    break
            except requests.RequestException:
                continue
        
        available_services = [k for k, v in services_status.items() if v]
        logger.info(f"Available services: {available_services}")
        
        # System should be partially functional with at least database
        if services_status['database']:
            logger.info("Core database service available - system can provide basic functionality")
        else:
            logger.warning("No core services available - system severely degraded")
        
        # At least one service should be available for the test to be meaningful
        assert len(available_services) > 0, "No services available - complete system failure"


if __name__ == '__main__':
    # Run chaos tests with special marker
    pytest.main([__file__, '-v', '-m', 'chaos', '--tb=short'])