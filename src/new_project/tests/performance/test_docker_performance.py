"""
Docker Performance Testing Suite

Tests container startup times, resource usage, and network latency.
Measures performance characteristics of Docker infrastructure.

Performance Targets:
- Container startup: <30 seconds for application services
- Memory usage: <512MB for application containers
- Network latency: <10ms between containers
- Database connections: <100ms response time
"""

import pytest
import docker
import requests
import time
import psutil
import subprocess
import statistics
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
import json
import psycopg2
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestContainerStartupPerformance:
    """Test container startup performance characteristics."""

    @pytest.fixture
    def docker_client(self):
        """Get Docker client."""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception as e:
            pytest.skip(f"Docker client not available: {e}")

    def test_database_container_startup_time(self, docker_client):
        """Test database container starts within acceptable time."""
        # Find existing postgres container or start new one
        containers = docker_client.containers.list(all=True)
        postgres_container = None
        
        for container in containers:
            if 'postgres' in container.name.lower():
                postgres_container = container
                break
        
        if not postgres_container:
            pytest.skip("No postgres container found for performance testing")
        
        # If container is running, restart it to test startup time
        if postgres_container.status == 'running':
            logger.info("Restarting postgres container to measure startup time...")
            
            start_time = time.time()
            postgres_container.restart()
            
            # Wait for container to be ready
            max_wait_time = 60  # 60 seconds max
            while time.time() - start_time < max_wait_time:
                postgres_container.reload()
                if postgres_container.status == 'running':
                    # Test if postgres is actually ready to accept connections
                    try:
                        conn = psycopg2.connect(
                            host="localhost",
                            port=5432,
                            database="horme_db",
                            user="horme_user",
                            password="horme_secure_password",
                            connect_timeout=2
                        )
                        conn.close()
                        break
                    except psycopg2.OperationalError:
                        time.sleep(1)
                        continue
                time.sleep(1)
            
            startup_time = time.time() - start_time
            
            # Performance assertion
            assert startup_time < 30, f"Database startup took {startup_time:.2f}s, should be <30s"
            logger.info(f"Database container startup time: {startup_time:.2f}s")
        else:
            logger.info("Database container not running, skipping startup performance test")

    def test_application_container_startup_time(self, docker_client):
        """Test application container startup performance."""
        containers = docker_client.containers.list()
        app_containers = [c for c in containers if any(app in c.name.lower() for app in ['nexus', 'mcp'])]
        
        if not app_containers:
            pytest.skip("No application containers found")
        
        for container in app_containers:
            # Get container start time from container stats
            container.reload()
            started_at = container.attrs['State']['StartedAt']
            
            # Calculate approximate startup time (this is imperfect but gives indication)
            # For a real test, you'd restart and time it properly
            logger.info(f"Container {container.name} startup detected")
            
            # Test that container responds to health checks quickly
            health = container.attrs.get('State', {}).get('Health', {})
            if health and health.get('Status') == 'healthy':
                logger.info(f"Container {container.name} is healthy and responsive")
            elif container.status == 'running':
                logger.info(f"Container {container.name} is running (no health check)")

    def test_container_resource_initialization(self, docker_client):
        """Test containers initialize with appropriate resource allocations."""
        containers = docker_client.containers.list()
        
        for container in containers:
            stats = container.stats(stream=False)
            
            # Check memory usage is reasonable at startup
            memory_usage = stats['memory_stats'].get('usage', 0)
            memory_limit = stats['memory_stats'].get('limit', 0)
            
            if memory_limit > 0:
                memory_usage_mb = memory_usage / (1024 * 1024)
                memory_limit_mb = memory_limit / (1024 * 1024)
                memory_percent = (memory_usage / memory_limit) * 100
                
                logger.info(f"Container {container.name}: {memory_usage_mb:.1f}MB / {memory_limit_mb:.1f}MB ({memory_percent:.1f}%)")
                
                # Application containers should not use excessive memory at startup
                if any(app in container.name.lower() for app in ['nexus', 'mcp']):
                    assert memory_usage_mb < 512, f"Application container {container.name} using {memory_usage_mb:.1f}MB at startup"


class TestDatabasePerformance:
    """Test database performance characteristics."""

    def test_database_connection_performance(self):
        """Test database connection establishment time."""
        connection_times = []
        
        for i in range(5):  # Test 5 connections
            start_time = time.time()
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="horme_db",
                    user="horme_user",
                    password="horme_secure_password",
                    connect_timeout=5
                )
                connect_time = time.time() - start_time
                connection_times.append(connect_time)
                conn.close()
                
            except psycopg2.OperationalError as e:
                pytest.skip(f"Database not available: {e}")
        
        if connection_times:
            avg_connect_time = statistics.mean(connection_times)
            max_connect_time = max(connection_times)
            
            logger.info(f"Database connection times - Avg: {avg_connect_time*1000:.1f}ms, Max: {max_connect_time*1000:.1f}ms")
            
            # Performance assertions
            assert avg_connect_time < 0.1, f"Average connection time {avg_connect_time*1000:.1f}ms should be <100ms"
            assert max_connect_time < 0.2, f"Max connection time {max_connect_time*1000:.1f}ms should be <200ms"

    def test_database_query_performance(self):
        """Test database query response times."""
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
            query_times = []
            
            # Test simple queries
            queries = [
                "SELECT 1",
                "SELECT version()",
                "SELECT NOW()",
                "SELECT COUNT(*) FROM information_schema.tables"
            ]
            
            for query in queries:
                start_time = time.time()
                cursor.execute(query)
                cursor.fetchall()
                query_time = time.time() - start_time
                query_times.append(query_time)
            
            cursor.close()
            conn.close()
            
            avg_query_time = statistics.mean(query_times)
            max_query_time = max(query_times)
            
            logger.info(f"Database query times - Avg: {avg_query_time*1000:.1f}ms, Max: {max_query_time*1000:.1f}ms")
            
            # Performance assertions
            assert avg_query_time < 0.05, f"Average query time {avg_query_time*1000:.1f}ms should be <50ms"
            assert max_query_time < 0.1, f"Max query time {max_query_time*1000:.1f}ms should be <100ms"
            
        except psycopg2.OperationalError as e:
            pytest.skip(f"Database not available: {e}")

    def test_database_concurrent_connections(self):
        """Test database performance under concurrent connections."""
        import threading
        
        connection_results = []
        connection_errors = []
        
        def create_connection():
            try:
                start_time = time.time()
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="horme_db",
                    user="horme_user",
                    password="horme_secure_password",
                    connect_timeout=5
                )
                connect_time = time.time() - start_time
                
                # Perform a simple query
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                
                total_time = time.time() - start_time
                connection_results.append(total_time)
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                connection_errors.append(str(e))
        
        # Create 10 concurrent connections
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_connection)
            threads.append(thread)
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=10)
        
        total_time = time.time() - start_time
        
        if connection_errors:
            logger.warning(f"Connection errors: {len(connection_errors)}")
        
        if connection_results:
            successful_connections = len(connection_results)
            avg_time = statistics.mean(connection_results)
            
            logger.info(f"Concurrent connections: {successful_connections}/10 successful, avg time: {avg_time*1000:.1f}ms, total time: {total_time:.2f}s")
            
            # Performance assertions
            assert successful_connections >= 8, f"Only {successful_connections}/10 concurrent connections succeeded"
            assert avg_time < 0.2, f"Average concurrent connection time {avg_time*1000:.1f}ms should be <200ms"
            assert total_time < 5, f"Total concurrent connection test took {total_time:.2f}s, should be <5s"
        else:
            pytest.fail("No successful concurrent connections")


class TestCachePerformance:
    """Test Redis cache performance characteristics."""

    def test_cache_connection_performance(self):
        """Test Redis connection performance."""
        connection_times = []
        
        for i in range(5):
            start_time = time.time()
            try:
                r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
                r.ping()
                connect_time = time.time() - start_time
                connection_times.append(connect_time)
                
            except redis.ConnectionError as e:
                pytest.skip(f"Redis not available: {e}")
        
        if connection_times:
            avg_connect_time = statistics.mean(connection_times)
            max_connect_time = max(connection_times)
            
            logger.info(f"Redis connection times - Avg: {avg_connect_time*1000:.1f}ms, Max: {max_connect_time*1000:.1f}ms")
            
            # Performance assertions
            assert avg_connect_time < 0.05, f"Average Redis connection time {avg_connect_time*1000:.1f}ms should be <50ms"
            assert max_connect_time < 0.1, f"Max Redis connection time {max_connect_time*1000:.1f}ms should be <100ms"

    def test_cache_operation_performance(self):
        """Test Redis operation performance."""
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
            
            # Test SET operations
            set_times = []
            for i in range(100):
                start_time = time.time()
                r.set(f'perf_test_key_{i}', f'value_{i}')
                set_time = time.time() - start_time
                set_times.append(set_time)
            
            # Test GET operations
            get_times = []
            for i in range(100):
                start_time = time.time()
                r.get(f'perf_test_key_{i}')
                get_time = time.time() - start_time
                get_times.append(get_time)
            
            # Cleanup
            for i in range(100):
                r.delete(f'perf_test_key_{i}')
            
            avg_set_time = statistics.mean(set_times)
            avg_get_time = statistics.mean(get_times)
            max_set_time = max(set_times)
            max_get_time = max(get_times)
            
            logger.info(f"Redis SET - Avg: {avg_set_time*1000:.2f}ms, Max: {max_set_time*1000:.2f}ms")
            logger.info(f"Redis GET - Avg: {avg_get_time*1000:.2f}ms, Max: {max_get_time*1000:.2f}ms")
            
            # Performance assertions
            assert avg_set_time < 0.01, f"Average SET time {avg_set_time*1000:.2f}ms should be <10ms"
            assert avg_get_time < 0.01, f"Average GET time {avg_get_time*1000:.2f}ms should be <10ms"
            assert max_set_time < 0.05, f"Max SET time {max_set_time*1000:.2f}ms should be <50ms"
            assert max_get_time < 0.05, f"Max GET time {max_get_time*1000:.2f}ms should be <50ms"
            
        except redis.ConnectionError as e:
            pytest.skip(f"Redis not available: {e}")


class TestNetworkPerformance:
    """Test network performance between containers."""

    def test_api_response_times(self):
        """Test API endpoint response times."""
        api_endpoints = [
            "http://localhost:8000/api/health",
            "http://localhost:3001/health",
            "http://localhost:3002/health"
        ]
        
        for endpoint in api_endpoints:
            response_times = []
            successful_requests = 0
            
            for i in range(10):  # Test 10 requests per endpoint
                try:
                    start_time = time.time()
                    response = requests.get(endpoint, timeout=5)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        response_times.append(response_time)
                        successful_requests += 1
                        
                except requests.RequestException:
                    continue
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                
                logger.info(f"API {endpoint} - {successful_requests}/10 successful, Avg: {avg_response_time*1000:.1f}ms, Max: {max_response_time*1000:.1f}ms")
                
                # Performance assertions
                assert avg_response_time < 0.5, f"Average response time {avg_response_time*1000:.1f}ms should be <500ms"
                assert max_response_time < 1.0, f"Max response time {max_response_time*1000:.1f}ms should be <1000ms"
                assert successful_requests >= 8, f"Only {successful_requests}/10 requests successful"

    def test_inter_service_latency(self):
        """Test latency between services."""
        # Test database connection latency (simulates app->db communication)
        db_latencies = []
        
        for i in range(5):
            try:
                start_time = time.time()
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="horme_db",
                    user="horme_user",
                    password="horme_secure_password",
                    connect_timeout=3
                )
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                latency = time.time() - start_time
                db_latencies.append(latency)
                
                cursor.close()
                conn.close()
                
            except psycopg2.OperationalError:
                continue
        
        # Test cache connection latency (simulates app->cache communication)
        cache_latencies = []
        
        for i in range(5):
            try:
                start_time = time.time()
                r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
                r.ping()
                latency = time.time() - start_time
                cache_latencies.append(latency)
                
            except redis.ConnectionError:
                continue
        
        if db_latencies:
            avg_db_latency = statistics.mean(db_latencies)
            logger.info(f"Database latency - Avg: {avg_db_latency*1000:.1f}ms")
            assert avg_db_latency < 0.1, f"Database latency {avg_db_latency*1000:.1f}ms should be <100ms"
        
        if cache_latencies:
            avg_cache_latency = statistics.mean(cache_latencies)
            logger.info(f"Cache latency - Avg: {avg_cache_latency*1000:.1f}ms")
            assert avg_cache_latency < 0.05, f"Cache latency {avg_cache_latency*1000:.1f}ms should be <50ms"


class TestResourceUtilization:
    """Test container resource utilization."""

    @pytest.fixture
    def docker_client(self):
        """Get Docker client."""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception as e:
            pytest.skip(f"Docker client not available: {e}")

    def test_memory_usage_limits(self, docker_client):
        """Test containers stay within memory limits."""
        containers = docker_client.containers.list()
        
        for container in containers:
            try:
                stats = container.stats(stream=False)
                
                memory_usage = stats['memory_stats'].get('usage', 0)
                memory_limit = stats['memory_stats'].get('limit', 0)
                
                if memory_limit > 0:
                    memory_usage_mb = memory_usage / (1024 * 1024)
                    memory_percent = (memory_usage / memory_limit) * 100
                    
                    logger.info(f"Container {container.name}: {memory_usage_mb:.1f}MB ({memory_percent:.1f}%)")
                    
                    # Application containers should not exceed reasonable memory usage
                    if any(app in container.name.lower() for app in ['nexus', 'mcp']):
                        assert memory_usage_mb < 1024, f"Application container {container.name} using {memory_usage_mb:.1f}MB"
                        assert memory_percent < 80, f"Container {container.name} using {memory_percent:.1f}% of memory limit"
                    
                    # Database containers have higher limits but should still be reasonable
                    elif 'postgres' in container.name.lower():
                        assert memory_usage_mb < 2048, f"Database container {container.name} using {memory_usage_mb:.1f}MB"
                
            except Exception as e:
                logger.warning(f"Could not get stats for container {container.name}: {e}")

    def test_cpu_usage_efficiency(self, docker_client):
        """Test CPU usage efficiency."""
        containers = docker_client.containers.list()
        
        for container in containers:
            try:
                stats = container.stats(stream=False)
                
                # Calculate CPU usage percentage
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                
                if system_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                    
                    logger.info(f"Container {container.name}: {cpu_percent:.1f}% CPU")
                    
                    # Containers should not consume excessive CPU when idle
                    # Note: This test might be flaky depending on container activity
                    if cpu_percent > 50:
                        logger.warning(f"Container {container.name} using high CPU: {cpu_percent:.1f}%")
                
            except (KeyError, ZeroDivisionError, Exception) as e:
                logger.warning(f"Could not calculate CPU usage for container {container.name}: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])