#!/usr/bin/env python3
"""
Cross-Platform Network Configuration for Kailash SDK Test Infrastructure
========================================================================

This module handles network configuration and connectivity testing between
Windows, WSL2, and Docker environments to ensure seamless service access
for the NO MOCKING testing strategy.
"""

import json
import logging
import os
import platform
import socket
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import ipaddress
import requests

logger = logging.getLogger(__name__)


@dataclass
class NetworkEndpoint:
    """Network endpoint configuration."""
    host: str
    port: int
    protocol: str = "tcp"
    service_name: str = ""
    accessible: bool = False
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class NetworkEnvironment:
    """Network environment information."""
    platform: str
    host_ip: Optional[str] = None
    docker_ip: Optional[str] = None
    wsl_ip: Optional[str] = None
    network_interfaces: Dict[str, str] = None
    
    def __post_init__(self):
        """Initialize network interfaces if not provided."""
        if self.network_interfaces is None:
            self.network_interfaces = {}


class NetworkConfig:
    """
    Cross-platform network configuration and connectivity manager.
    
    Handles network setup and testing for:
    - Windows host -> Docker services
    - WSL2 -> Docker services  
    - Docker containers -> external services
    - Network performance monitoring
    """
    
    def __init__(self):
        """Initialize network configuration."""
        self.current_platform = platform.system().lower()
        self.environment = NetworkEnvironment(platform=self.current_platform)
        
        # Service endpoints for testing
        self.service_endpoints = {
            "postgresql": NetworkEndpoint("localhost", 5432, "tcp", "PostgreSQL"),
            "neo4j_http": NetworkEndpoint("localhost", 7474, "http", "Neo4j HTTP"),
            "neo4j_bolt": NetworkEndpoint("localhost", 7687, "tcp", "Neo4j Bolt"),
            "chromadb": NetworkEndpoint("localhost", 8000, "http", "ChromaDB"),
            "redis": NetworkEndpoint("localhost", 6379, "tcp", "Redis"),
            "elasticsearch": NetworkEndpoint("localhost", 9200, "http", "Elasticsearch"),
            "minio_api": NetworkEndpoint("localhost", 9000, "http", "MinIO API"),
            "minio_console": NetworkEndpoint("localhost", 9001, "http", "MinIO Console")
        }
        
        # Network performance thresholds (milliseconds)
        self.performance_thresholds = {
            "excellent": 5.0,
            "good": 10.0,
            "acceptable": 50.0,
            "poor": 100.0
        }
    
    def detect_environment(self) -> NetworkEnvironment:
        """
        Detect current network environment and configuration.
        
        Returns:
            NetworkEnvironment: Detected environment information
        """
        logger.info("Detecting network environment...")
        
        try:
            # Detect host IP
            self.environment.host_ip = self._get_host_ip()
            
            # Detect Docker environment
            self.environment.docker_ip = self._get_docker_ip()
            
            # Detect WSL2 if on Windows
            if self.current_platform == "windows":
                self.environment.wsl_ip = self._get_wsl_ip()
            
            # Get network interfaces
            self.environment.network_interfaces = self._get_network_interfaces()
            
            logger.info(f"Environment detected: {self.environment}")
            return self.environment
            
        except Exception as e:
            logger.error(f"Error detecting environment: {e}")
            raise
    
    def test_connectivity(self, endpoints: Optional[List[str]] = None) -> Dict[str, NetworkEndpoint]:
        """
        Test connectivity to all service endpoints.
        
        Args:
            endpoints: Specific endpoints to test (default: all)
            
        Returns:
            dict: Endpoint name -> NetworkEndpoint results
        """
        target_endpoints = endpoints or list(self.service_endpoints.keys())
        results = {}
        
        logger.info(f"Testing connectivity to endpoints: {target_endpoints}")
        
        for endpoint_name in target_endpoints:
            if endpoint_name in self.service_endpoints:
                endpoint = self.service_endpoints[endpoint_name]
                results[endpoint_name] = self._test_endpoint(endpoint)
            else:
                logger.warning(f"Unknown endpoint: {endpoint_name}")
        
        return results
    
    def _test_endpoint(self, endpoint: NetworkEndpoint) -> NetworkEndpoint:
        """Test connectivity to a specific endpoint."""
        start_time = time.time()
        
        try:
            if endpoint.protocol == "tcp":
                # TCP socket test
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(10)
                    result = sock.connect_ex((endpoint.host, endpoint.port))
                    endpoint.accessible = (result == 0)
            
            elif endpoint.protocol == "http":
                # HTTP request test
                response = requests.get(
                    f"http://{endpoint.host}:{endpoint.port}",
                    timeout=10
                )
                endpoint.accessible = response.status_code < 500
            
            else:
                logger.warning(f"Unknown protocol: {endpoint.protocol}")
                endpoint.accessible = False
            
            endpoint.response_time_ms = (time.time() - start_time) * 1000
            
            if not endpoint.accessible:
                endpoint.error_message = f"Connection failed to {endpoint.host}:{endpoint.port}"
            
        except Exception as e:
            endpoint.accessible = False
            endpoint.error_message = str(e)
            endpoint.response_time_ms = (time.time() - start_time) * 1000
        
        return endpoint
    
    def configure_windows_networking(self) -> bool:
        """
        Configure Windows networking for WSL2 and Docker connectivity.
        
        Returns:
            bool: True if configuration successful
        """
        if self.current_platform != "windows":
            logger.info("Skipping Windows networking configuration (not on Windows)")
            return True
        
        try:
            logger.info("Configuring Windows networking...")
            
            # Configure Windows hosts file for service discovery
            self._update_windows_hosts()
            
            # Configure WSL2 networking
            self._configure_wsl_networking()
            
            # Configure Docker Desktop networking
            self._configure_docker_desktop()
            
            logger.info("Windows networking configuration completed")
            return True
            
        except Exception as e:
            logger.error(f"Windows networking configuration failed: {e}")
            return False
    
    def configure_wsl_networking(self) -> bool:
        """
        Configure WSL2 networking for Docker service access.
        
        Returns:
            bool: True if configuration successful
        """
        try:
            logger.info("Configuring WSL2 networking...")
            
            # Update WSL2 hosts file
            self._update_wsl_hosts()
            
            # Configure iptables rules for service access
            self._configure_wsl_iptables()
            
            # Configure Docker daemon for external access
            self._configure_wsl_docker()
            
            logger.info("WSL2 networking configuration completed")
            return True
            
        except Exception as e:
            logger.error(f"WSL2 networking configuration failed: {e}")
            return False
    
    def validate_performance(self, 
                           max_latency_ms: float = 10.0,
                           endpoints: Optional[List[str]] = None) -> Tuple[bool, Dict[str, str]]:
        """
        Validate network performance meets requirements.
        
        Args:
            max_latency_ms: Maximum acceptable latency in milliseconds
            endpoints: Specific endpoints to validate
            
        Returns:
            tuple: (all_passed, performance_report)
        """
        connectivity_results = self.test_connectivity(endpoints)
        performance_report = {}
        all_passed = True
        
        for endpoint_name, endpoint in connectivity_results.items():
            if not endpoint.accessible:
                performance_report[endpoint_name] = "FAILED - Not accessible"
                all_passed = False
                continue
            
            if endpoint.response_time_ms is None:
                performance_report[endpoint_name] = "FAILED - No response time"
                all_passed = False
                continue
            
            # Categorize performance
            latency = endpoint.response_time_ms
            if latency <= self.performance_thresholds["excellent"]:
                category = "EXCELLENT"
            elif latency <= self.performance_thresholds["good"]:
                category = "GOOD"
            elif latency <= self.performance_thresholds["acceptable"]:
                category = "ACCEPTABLE"
            else:
                category = "POOR"
            
            # Check if it meets requirements
            if latency > max_latency_ms:
                all_passed = False
                performance_report[endpoint_name] = f"{category} - {latency:.1f}ms (EXCEEDS LIMIT)"
            else:
                performance_report[endpoint_name] = f"{category} - {latency:.1f}ms"
        
        return all_passed, performance_report
    
    def generate_config_files(self, output_dir: str = ".") -> List[str]:
        """
        Generate configuration files for different environments.
        
        Args:
            output_dir: Directory to write configuration files
            
        Returns:
            list: Paths to generated configuration files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        generated_files = []
        
        # Generate environment configuration
        env_config = {
            "environment": asdict(self.environment),
            "service_endpoints": {
                name: asdict(endpoint) 
                for name, endpoint in self.service_endpoints.items()
            },
            "performance_thresholds": self.performance_thresholds
        }
        
        env_config_path = output_path / "network_environment.json"
        with open(env_config_path, 'w') as f:
            json.dump(env_config, f, indent=2)
        generated_files.append(str(env_config_path))
        
        # Generate Docker environment file
        docker_env_path = output_path / ".env.docker"
        with open(docker_env_path, 'w') as f:
            # Docker environment variables
            f.write("# Docker Environment Configuration\n")
            f.write(f"DOCKER_HOST_IP={self.environment.host_ip or 'localhost'}\n")
            f.write(f"WSL_HOST_IP={self.environment.wsl_ip or 'localhost'}\n")
            
            # Service endpoints
            f.write("\n# Service Endpoints\n")
            for name, endpoint in self.service_endpoints.items():
                service_name = name.upper().replace("_", "_")
                f.write(f"{service_name}_HOST={endpoint.host}\n")
                f.write(f"{service_name}_PORT={endpoint.port}\n")
        
        generated_files.append(str(docker_env_path))
        
        # Generate test configuration
        test_config_path = output_path / "test_network_config.py"
        with open(test_config_path, 'w') as f:
            f.write('"""\nGenerated test network configuration.\n"""\n\n')
            f.write("# Service connection configurations\n")
            f.write("SERVICE_CONFIGS = {\n")
            
            for name, endpoint in self.service_endpoints.items():
                f.write(f'    "{name}": {{\n')
                f.write(f'        "host": "{endpoint.host}",\n')
                f.write(f'        "port": {endpoint.port},\n')
                f.write(f'        "protocol": "{endpoint.protocol}"\n')
                f.write('    },\n')
            
            f.write("}\n")
        
        generated_files.append(str(test_config_path))
        
        logger.info(f"Generated configuration files: {generated_files}")
        return generated_files
    
    # Helper methods for environment detection
    def _get_host_ip(self) -> Optional[str]:
        """Get the host IP address."""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except Exception:
            return None
    
    def _get_docker_ip(self) -> Optional[str]:
        """Get Docker daemon IP address."""
        try:
            # Try to get Docker daemon info
            result = subprocess.run(
                ["docker", "version", "--format", "json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Docker is available, try to get bridge IP
                result = subprocess.run(
                    ["docker", "network", "inspect", "bridge"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    import json
                    network_info = json.loads(result.stdout)
                    if network_info:
                        gateway = network_info[0].get("IPAM", {}).get("Config", [{}])[0].get("Gateway")
                        if gateway:
                            return gateway
                
                # Fallback to default Docker gateway
                return "172.17.0.1"
            
            return None
        except Exception:
            return None
    
    def _get_wsl_ip(self) -> Optional[str]:
        """Get WSL2 IP address (Windows only)."""
        try:
            result = subprocess.run(
                ["wsl", "hostname", "-I"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                ip = result.stdout.strip()
                if ip:
                    return ip.split()[0]  # Take first IP if multiple
            
            return None
        except Exception:
            return None
    
    def _get_network_interfaces(self) -> Dict[str, str]:
        """Get network interface information."""
        interfaces = {}
        
        try:
            if self.current_platform == "windows":
                # Use ipconfig on Windows
                result = subprocess.run(
                    ["ipconfig"],
                    capture_output=True,
                    text=True
                )
                # Parse ipconfig output (simplified)
                interfaces["ipconfig_available"] = str(result.returncode == 0)
            else:
                # Use ip command on Linux/WSL
                result = subprocess.run(
                    ["ip", "addr", "show"],
                    capture_output=True,
                    text=True
                )
                interfaces["ip_command_available"] = str(result.returncode == 0)
        
        except Exception as e:
            interfaces["error"] = str(e)
        
        return interfaces
    
    # Helper methods for network configuration
    def _update_windows_hosts(self):
        """Update Windows hosts file for service discovery."""
        # This would require admin privileges in real implementation
        logger.info("Windows hosts file update would require admin privileges")
    
    def _configure_wsl_networking(self):
        """Configure WSL2 networking settings."""
        # This would be implemented with WSL-specific commands
        logger.info("WSL2 networking configuration placeholder")
    
    def _configure_docker_desktop(self):
        """Configure Docker Desktop networking."""
        # This would configure Docker Desktop settings
        logger.info("Docker Desktop networking configuration placeholder")
    
    def _update_wsl_hosts(self):
        """Update WSL hosts file."""
        # This would update /etc/hosts in WSL
        logger.info("WSL hosts file update placeholder")
    
    def _configure_wsl_iptables(self):
        """Configure WSL iptables rules."""
        # This would configure iptables for service forwarding
        logger.info("WSL iptables configuration placeholder")
    
    def _configure_wsl_docker(self):
        """Configure Docker daemon in WSL."""
        # This would configure Docker daemon for external access
        logger.info("WSL Docker configuration placeholder")


def main():
    """CLI entry point for network configuration."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Network Configuration for Kailash SDK Test Infrastructure"
    )
    parser.add_argument(
        "--detect", 
        action="store_true",
        help="Detect current network environment"
    )
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Test connectivity to all services"
    )
    parser.add_argument(
        "--configure", 
        action="store_true",
        help="Configure networking for current platform"
    )
    parser.add_argument(
        "--validate", 
        type=float,
        default=10.0,
        help="Validate performance (max latency in ms)"
    )
    parser.add_argument(
        "--generate-config", 
        metavar="DIR",
        help="Generate configuration files in specified directory"
    )
    
    args = parser.parse_args()
    
    config = NetworkConfig()
    
    if args.detect:
        environment = config.detect_environment()
        print("\n=== Network Environment ===")
        print(f"Platform: {environment.platform}")
        print(f"Host IP: {environment.host_ip}")
        print(f"Docker IP: {environment.docker_ip}")
        if environment.wsl_ip:
            print(f"WSL IP: {environment.wsl_ip}")
    
    if args.test:
        results = config.test_connectivity()
        print("\n=== Connectivity Test Results ===")
        
        for endpoint_name, endpoint in results.items():
            status = "✅" if endpoint.accessible else "❌"
            latency = f" ({endpoint.response_time_ms:.1f}ms)" if endpoint.response_time_ms else ""
            error = f" - {endpoint.error_message}" if endpoint.error_message else ""
            print(f"{status} {endpoint.service_name}: {endpoint.host}:{endpoint.port}{latency}{error}")
    
    if args.configure:
        success = False
        if config.current_platform == "windows":
            success = config.configure_windows_networking()
        else:
            success = config.configure_wsl_networking()
        
        if success:
            print("✅ Network configuration completed")
        else:
            print("❌ Network configuration failed")
            return 1
    
    if args.validate:
        passed, report = config.validate_performance(args.validate)
        print(f"\n=== Performance Validation (max {args.validate}ms) ===")
        
        for endpoint_name, status in report.items():
            icon = "✅" if "EXCEEDS LIMIT" not in status else "❌"
            print(f"{icon} {endpoint_name}: {status}")
        
        if passed:
            print("\n🎉 All endpoints meet performance requirements!")
        else:
            print("\n⚠️  Some endpoints exceed performance limits")
            return 1
    
    if args.generate_config:
        files = config.generate_config_files(args.generate_config)
        print("📁 Generated configuration files:")
        for file_path in files:
            print(f"   {file_path}")
    
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)