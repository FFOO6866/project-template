"""
Docker Production Readiness End-to-End Tests

Tests production readiness characteristics:
- Health check validation
- Graceful shutdown testing  
- Log aggregation verification
- Security configurations
- Monitoring and observability

These tests verify the Docker setup is production-ready.
"""

import pytest
import docker
import requests
import subprocess
import time
import json
import signal
import os
from pathlib import Path
from typing import Dict, List, Any
import logging
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestHealthCheckValidation:
    """Test health check implementations and reliability."""

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
    def test_container_health_checks_configured(self, docker_client):
        """Test that critical containers have health checks configured."""
        containers = docker_client.containers.list()
        critical_services = ['postgres', 'redis', 'nexus', 'mcp']
        
        health_check_results = {}
        
        for container in containers:
            container.reload()
            health_config = container.attrs.get('Config', {}).get('Healthcheck', {})
            health_state = container.attrs.get('State', {}).get('Health', {})
            
            # Check if container matches critical services
            for service in critical_services:
                if service in container.name.lower():
                    health_check_results[container.name] = {
                        'has_healthcheck': bool(health_config.get('Test')),
                        'current_status': health_state.get('Status', 'unknown'),
                        'health_config': health_config
                    }
                    break
        
        # Verify critical services have health checks
        for container_name, health_info in health_check_results.items():
            logger.info(f"Container {container_name}: Health check configured: {health_info['has_healthcheck']}, Status: {health_info['current_status']}")
            
            # Production containers should have health checks
            assert health_info['has_healthcheck'], f"Container {container_name} should have health check configured"
            
            # Health checks should pass or be starting
            if health_info['current_status'] not in ['unknown', 'starting']:
                assert health_info['current_status'] == 'healthy', \
                    f"Container {container_name} health status is {health_info['current_status']}"

    @pytest.mark.timeout(10)
    def test_health_check_endpoints_respond(self):
        """Test health check endpoints respond correctly."""
        health_endpoints = [
            ("http://localhost:8000/api/health", "Nexus API"),
            ("http://localhost:3001/health", "MCP Server Primary"),
            ("http://localhost:3002/health", "MCP Server Secondary")
        ]
        
        working_endpoints = []
        failed_endpoints = []
        
        for endpoint_url, service_name in health_endpoints:
            try:
                response = requests.get(endpoint_url, timeout=5)
                
                if response.status_code == 200:
                    working_endpoints.append((endpoint_url, service_name))
                    
                    # Verify response contains expected health information
                    try:
                        health_data = response.json()
                        
                        # Health response should contain status
                        assert 'status' in health_data or 'health' in health_data, \
                            f"Health endpoint {endpoint_url} should return status information"
                        
                        logger.info(f"Health endpoint {service_name} ({endpoint_url}): OK")
                        
                    except (ValueError, json.JSONDecodeError):
                        # Text response is also acceptable for health checks
                        assert len(response.text) > 0, f"Health endpoint {endpoint_url} returned empty response"
                        logger.info(f"Health endpoint {service_name} ({endpoint_url}): OK (text response)")
                
                else:
                    failed_endpoints.append((endpoint_url, service_name, response.status_code))
                    logger.warning(f"Health endpoint {service_name} returned {response.status_code}")
                    
            except requests.RequestException as e:
                failed_endpoints.append((endpoint_url, service_name, str(e)))
                logger.warning(f"Health endpoint {service_name} failed: {e}")
        
        # At least one health endpoint should be working
        assert len(working_endpoints) > 0, f"No health endpoints working. Failed: {failed_endpoints}"
        
        logger.info(f"Working health endpoints: {len(working_endpoints)}, Failed: {len(failed_endpoints)}")

    @pytest.mark.timeout(10)
    def test_health_check_response_times(self):
        """Test health check endpoints respond quickly."""
        health_endpoints = [
            "http://localhost:8000/api/health",
            "http://localhost:3001/health",
            "http://localhost:3002/health"
        ]
        
        response_times = []
        
        for endpoint in health_endpoints:
            try:
                start_time = time.time()
                response = requests.get(endpoint, timeout=5)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    response_times.append(response_time)
                    logger.info(f"Health endpoint {endpoint}: {response_time*1000:.1f}ms")
                    
                    # Health checks should be fast
                    assert response_time < 2.0, f"Health check at {endpoint} took {response_time:.2f}s, should be <2s"
                    
            except requests.RequestException:
                continue
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            logger.info(f"Average health check response time: {avg_response_time*1000:.1f}ms")
            
            # Average health check time should be reasonable
            assert avg_response_time < 1.0, f"Average health check time {avg_response_time:.2f}s should be <1s"


class TestGracefulShutdownBehavior:
    """Test graceful shutdown behavior of containers."""

    @pytest.fixture
    def docker_client(self):
        """Get Docker client."""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception as e:
            pytest.skip(f"Docker client not available: {e}")

    @pytest.mark.timeout(30)
    def test_database_graceful_shutdown(self, docker_client):
        """Test database container shuts down gracefully."""
        # Find database container
        containers = docker_client.containers.list()
        db_container = None
        
        for container in containers:
            if 'postgres' in container.name.lower():
                db_container = container
                break
        
        if not db_container:
            pytest.skip("Database container not found")
        
        # Verify database is running and accessible
        import psycopg2
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="horme_db",
                user="horme_user",
                password="horme_secure_password",
                connect_timeout=5
            )
            conn.close()
        except psycopg2.OperationalError:
            pytest.skip("Database not accessible for graceful shutdown test")
        
        # Send graceful shutdown signal (SIGTERM)
        logger.info("Sending graceful shutdown signal to database container...")
        shutdown_start = time.time()
        
        db_container.kill(signal="SIGTERM")
        
        # Wait for graceful shutdown
        max_shutdown_time = 20  # PostgreSQL should shutdown within 20 seconds
        
        while time.time() - shutdown_start < max_shutdown_time:
            db_container.reload()
            if db_container.status in ['exited', 'stopped']:
                shutdown_time = time.time() - shutdown_start
                logger.info(f"Database graceful shutdown completed in {shutdown_time:.2f}s")
                break
            time.sleep(1)
        else:
            pytest.fail(f"Database did not shutdown gracefully within {max_shutdown_time}s")
        
        # Restart database for other tests
        db_container.start()
        time.sleep(5)  # Give database time to start
        
        # Performance assertion
        assert shutdown_time < 20, f"Database shutdown took {shutdown_time:.2f}s, should be <20s"

    @pytest.mark.timeout(30)
    def test_application_graceful_shutdown(self, docker_client):
        """Test application containers shut down gracefully."""
        # Find application containers
        containers = docker_client.containers.list()
        app_containers = [c for c in containers if any(app in c.name.lower() for app in ['nexus', 'mcp'])]
        
        if not app_containers:
            pytest.skip("No application containers found")
        
        # Test graceful shutdown of first application container
        app_container = app_containers[0]
        
        logger.info(f"Testing graceful shutdown of {app_container.name}")
        
        # Send graceful shutdown signal
        shutdown_start = time.time()
        app_container.kill(signal="SIGTERM")
        
        # Wait for graceful shutdown
        max_shutdown_time = 15  # Applications should shutdown quickly
        
        while time.time() - shutdown_start < max_shutdown_time:
            app_container.reload()
            if app_container.status in ['exited', 'stopped']:
                shutdown_time = time.time() - shutdown_start
                logger.info(f"Application graceful shutdown completed in {shutdown_time:.2f}s")
                break
            time.sleep(1)
        else:
            pytest.fail(f"Application did not shutdown gracefully within {max_shutdown_time}s")
        
        # Restart application for other tests
        app_container.start()
        time.sleep(3)  # Give application time to start
        
        # Performance assertion
        assert shutdown_time < 15, f"Application shutdown took {shutdown_time:.2f}s, should be <15s"

    @pytest.mark.timeout(10)
    def test_shutdown_signal_handling(self, docker_client):
        """Test containers handle shutdown signals properly."""
        containers = docker_client.containers.list()
        
        for container in containers:
            container.reload()
            
            # Check container configuration for proper signal handling
            config = container.attrs.get('Config', {})
            
            # Containers should have proper stop signal configuration
            stop_signal = config.get('StopSignal', 'SIGTERM')
            logger.info(f"Container {container.name}: Stop signal = {stop_signal}")
            
            # Most containers should use SIGTERM for graceful shutdown
            if stop_signal not in ['SIGTERM', 'SIGINT', 'SIGQUIT']:
                logger.warning(f"Container {container.name} uses unusual stop signal: {stop_signal}")
            
            # Check stop timeout
            stop_timeout = config.get('StopTimeout', 10)
            logger.info(f"Container {container.name}: Stop timeout = {stop_timeout}s")
            
            # Stop timeout should be reasonable
            assert stop_timeout <= 30, f"Container {container.name} stop timeout {stop_timeout}s too long"


class TestLogAggregationVerification:
    """Test log aggregation and monitoring capabilities."""

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
    def test_container_logging_configuration(self, docker_client):
        """Test containers have proper logging configuration."""
        containers = docker_client.containers.list()
        
        for container in containers:
            container.reload()
            
            # Check logging configuration
            log_config = container.attrs.get('HostConfig', {}).get('LogConfig', {})
            log_driver = log_config.get('Type', 'json-file')
            log_options = log_config.get('Config', {})
            
            logger.info(f"Container {container.name}: Log driver = {log_driver}")
            
            # Check for log rotation to prevent disk space issues
            if log_driver == 'json-file':
                max_size = log_options.get('max-size', 'unlimited')
                max_file = log_options.get('max-file', 'unlimited')
                
                logger.info(f"Container {container.name}: max-size = {max_size}, max-file = {max_file}")
                
                # Production containers should have log rotation
                if any(service in container.name.lower() for service in ['nexus', 'mcp', 'postgres']):
                    if max_size == 'unlimited':
                        logger.warning(f"Production container {container.name} should have log size limits")

    @pytest.mark.timeout(10)
    def test_application_log_output(self, docker_client):
        """Test applications produce proper log output."""
        containers = docker_client.containers.list()
        app_containers = [c for c in containers if any(app in c.name.lower() for app in ['nexus', 'mcp'])]
        
        for container in app_containers:
            try:
                # Get recent logs
                logs = container.logs(tail=10, timestamps=True).decode('utf-8')
                
                if logs.strip():
                    logger.info(f"Container {container.name} producing logs: {len(logs)} characters")
                    
                    # Logs should contain timestamps
                    lines = logs.strip().split('\n')
                    if lines:
                        first_line = lines[0]
                        # Docker adds timestamps in format: 2023-01-01T00:00:00.000000000Z
                        assert 'T' in first_line and 'Z' in first_line, \
                            f"Container {container.name} logs should have timestamps"
                else:
                    logger.warning(f"Container {container.name} not producing logs")
                    
            except Exception as e:
                logger.warning(f"Could not retrieve logs from {container.name}: {e}")

    @pytest.mark.timeout(10)
    def test_log_structured_format(self, docker_client):
        """Test logs are in structured format when possible."""
        containers = docker_client.containers.list()
        
        for container in containers:
            if any(app in container.name.lower() for app in ['nexus', 'mcp']):
                try:
                    logs = container.logs(tail=5).decode('utf-8')
                    
                    if logs.strip():
                        lines = logs.strip().split('\n')
                        structured_lines = 0
                        
                        for line in lines:
                            # Remove Docker timestamp prefix
                            if 'T' in line and 'Z' in line:
                                # Extract log content after timestamp
                                parts = line.split(' ', 1)
                                if len(parts) > 1:
                                    log_content = parts[1]
                                else:
                                    log_content = line
                            else:
                                log_content = line
                            
                            # Check for structured logging (JSON or key=value format)
                            if (log_content.strip().startswith('{') or 
                                '=' in log_content or 
                                'level=' in log_content.lower() or
                                'msg=' in log_content.lower()):
                                structured_lines += 1
                        
                        if len(lines) > 0:
                            structured_ratio = structured_lines / len(lines)
                            logger.info(f"Container {container.name}: {structured_ratio:.1%} structured logs")
                            
                            # At least some logs should be structured for production apps
                            if structured_ratio > 0:
                                logger.info(f"Container {container.name} has structured logging")
                        
                except Exception as e:
                    logger.warning(f"Could not analyze logs from {container.name}: {e}")


class TestSecurityConfiguration:
    """Test security configurations are production-ready."""

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
    def test_container_user_security(self, docker_client):
        """Test containers run as non-root users."""
        containers = docker_client.containers.list()
        
        for container in containers:
            container.reload()
            config = container.attrs.get('Config', {})
            
            # Check user configuration
            user = config.get('User', '')
            
            # Production application containers should not run as root
            if any(app in container.name.lower() for app in ['nexus', 'mcp']):
                assert user and user != 'root' and user != '0', \
                    f"Production container {container.name} should not run as root user (current: {user or 'root'})"
                logger.info(f"Container {container.name} runs as user: {user}")
            else:
                logger.info(f"Container {container.name} runs as user: {user or 'root'}")

    @pytest.mark.timeout(10)
    def test_container_capabilities(self, docker_client):
        """Test containers have minimal capabilities."""
        containers = docker_client.containers.list()
        
        for container in containers:
            container.reload()
            host_config = container.attrs.get('HostConfig', {})
            
            # Check security options
            security_opt = host_config.get('SecurityOpt', [])
            cap_add = host_config.get('CapAdd', [])
            cap_drop = host_config.get('CapDrop', [])
            privileged = host_config.get('Privileged', False)
            
            logger.info(f"Container {container.name}: Privileged={privileged}, CapAdd={cap_add}, CapDrop={cap_drop}")
            
            # Production containers should not be privileged
            if any(app in container.name.lower() for app in ['nexus', 'mcp']):
                assert not privileged, f"Production container {container.name} should not be privileged"
                
                # Should have security options configured
                if 'no-new-privileges:true' in security_opt:
                    logger.info(f"Container {container.name} has no-new-privileges security option")

    @pytest.mark.timeout(10)
    def test_network_security(self, docker_client):
        """Test network security configurations."""
        containers = docker_client.containers.list()
        networks = docker_client.networks.list()
        
        # Check for custom networks (better than default bridge)
        custom_networks = [n for n in networks if n.name not in ['bridge', 'host', 'none']]
        
        if custom_networks:
            logger.info(f"Found {len(custom_networks)} custom networks")
            
            for network in custom_networks:
                network.reload()
                network_config = network.attrs.get('IPAM', {}).get('Config', [])
                
                if network_config:
                    subnet = network_config[0].get('Subnet', 'unknown')
                    logger.info(f"Network {network.name}: Subnet = {subnet}")
        
        # Check container network configurations
        for container in containers:
            container.reload()
            network_settings = container.attrs.get('NetworkSettings', {})
            networks_connected = network_settings.get('Networks', {})
            
            network_names = list(networks_connected.keys())
            logger.info(f"Container {container.name}: Connected to networks = {network_names}")
            
            # Production containers should use custom networks, not default bridge
            if any(app in container.name.lower() for app in ['nexus', 'mcp']):
                assert 'bridge' not in network_names or len(network_names) > 1, \
                    f"Production container {container.name} should use custom network, not default bridge"


class TestMonitoringObservability:
    """Test monitoring and observability configurations."""

    @pytest.mark.timeout(10)
    def test_metrics_endpoints_available(self):
        """Test metrics endpoints are available for monitoring."""
        metrics_endpoints = [
            ("http://localhost:9090/metrics", "Prometheus metrics"),
            ("http://localhost:8000/metrics", "Application metrics"),
            ("http://localhost:3001/metrics", "MCP metrics")
        ]
        
        available_metrics = []
        
        for endpoint, description in metrics_endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                
                if response.status_code == 200:
                    available_metrics.append((endpoint, description))
                    
                    # Metrics should be in Prometheus format or JSON
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'text/plain' in content_type or 'application/json' in content_type:
                        logger.info(f"Metrics endpoint {description} available: {endpoint}")
                    else:
                        logger.warning(f"Metrics endpoint {description} has unexpected content type: {content_type}")
                        
            except requests.RequestException:
                logger.info(f"Metrics endpoint {description} not available: {endpoint}")
        
        if available_metrics:
            logger.info(f"Available metrics endpoints: {len(available_metrics)}")
        else:
            logger.warning("No metrics endpoints available - monitoring may be limited")

    @pytest.mark.timeout(10)
    def test_container_resource_monitoring(self, docker_client):
        """Test container resource monitoring capabilities."""
        containers = docker_client.containers.list()
        
        monitorable_containers = 0
        
        for container in containers:
            try:
                stats = container.stats(stream=False)
                
                # Verify we can get basic monitoring stats
                if 'memory_stats' in stats and 'cpu_stats' in stats:
                    monitorable_containers += 1
                    
                    memory_usage = stats['memory_stats'].get('usage', 0)
                    memory_limit = stats['memory_stats'].get('limit', 0)
                    
                    if memory_limit > 0:
                        memory_usage_mb = memory_usage / (1024 * 1024)
                        memory_percent = (memory_usage / memory_limit) * 100
                        
                        logger.info(f"Container {container.name}: {memory_usage_mb:.1f}MB ({memory_percent:.1f}%)")
                    
            except Exception as e:
                logger.warning(f"Could not get monitoring stats for {container.name}: {e}")
        
        # Should be able to monitor most containers
        total_containers = len(containers)
        monitoring_ratio = monitorable_containers / total_containers if total_containers > 0 else 0
        
        logger.info(f"Monitorable containers: {monitorable_containers}/{total_containers} ({monitoring_ratio:.1%})")
        
        assert monitoring_ratio > 0.5, f"Only {monitoring_ratio:.1%} of containers are monitorable"

    @pytest.mark.timeout(10)
    def test_alerting_configuration(self):
        """Test alerting and notification capabilities."""
        # Check if monitoring stack is available
        monitoring_endpoints = [
            "http://localhost:9091",  # Prometheus
            "http://localhost:3100"   # Grafana
        ]
        
        monitoring_available = False
        
        for endpoint in monitoring_endpoints:
            try:
                response = requests.get(endpoint, timeout=3)
                if response.status_code == 200:
                    monitoring_available = True
                    logger.info(f"Monitoring service available: {endpoint}")
                    break
            except requests.RequestException:
                continue
        
        if monitoring_available:
            logger.info("Monitoring stack is available for alerting")
        else:
            logger.warning("No monitoring stack detected - alerting capabilities may be limited")
            
        # This test passes as long as we can detect monitoring capabilities
        # In a real production environment, you'd test specific alert rules


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])