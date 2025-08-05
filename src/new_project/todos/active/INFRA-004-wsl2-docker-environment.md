# INFRA-004: WSL2 + Docker Hybrid Environment Deployment

**Created:** 2025-08-02  
**Assigned:** Infrastructure & DevOps Team  
**Priority:** 🚨 P0 - CRITICAL  
**Status:** PENDING  
**Estimated Effort:** 12 hours  
**Due Date:** 2025-08-06 (96-hour critical deployment)

## Description

Deploy a comprehensive WSL2 + Docker hybrid environment to provide real infrastructure services for Tier 2-3 testing. This eliminates the NO MOCKING requirement and establishes production-like testing infrastructure with PostgreSQL, Neo4j, Redis, and other required services.

## Strategic Approach

The hybrid Windows + WSL2 + Docker strategy addresses critical infrastructure needs:
- **Windows Host**: Primary development environment with SDK compatibility fixes
- **WSL2 Ubuntu**: Unix-compatible environment for services requiring Linux
- **Docker Services**: Production-like databases and services for real testing
- **Cross-Platform Networking**: Seamless communication between all environments

## Acceptance Criteria

- [ ] WSL2 Ubuntu environment fully operational with Docker support
- [ ] PostgreSQL database service running and accessible from Windows
- [ ] Neo4j knowledge graph database operational with APOC plugins
- [ ] Redis caching service configured and accessible
- [ ] ChromaDB vector database service running
- [ ] Cross-platform networking between Windows, WSL2, and Docker configured
- [ ] Service health monitoring and automated startup configured
- [ ] Development environment can seamlessly use all services
- [ ] Test infrastructure can connect to all real services (NO MOCKING)

## Subtasks

- [ ] WSL2 Environment Setup and Configuration (Est: 3h)
  - Verification: Ubuntu WSL2 instance running with Docker Desktop integration
  - Output: Fully configured WSL2 environment with development tools
- [ ] Docker Services Infrastructure Deployment (Est: 4h)
  - Verification: All required services running and healthy
  - Output: Production-ready database and service containers
- [ ] Cross-Platform Network Configuration (Est: 2h)
  - Verification: Windows development environment can access all WSL2/Docker services
  - Output: Seamless networking between all environments
- [ ] Service Health Monitoring and Management (Est: 2h)
  - Verification: Automated health checks and service recovery
  - Output: Robust service management and monitoring system
- [ ] Development Environment Integration (Est: 1h)
  - Verification: All development tools and IDEs can access services
  - Output: Unified development experience across environments

## Dependencies

- **INFRA-001**: Windows SDK Compatibility (for development environment)
- **INFRA-003**: Test Infrastructure Recovery (for test service integration)
- Windows 10/11 with WSL2 support
- Docker Desktop for Windows
- Adequate system resources (16GB+ RAM recommended)

## Risk Assessment

- **HIGH**: Complex multi-environment setup may have networking issues
- **HIGH**: Resource requirements may exceed available system capacity
- **MEDIUM**: Windows Defender or antivirus may interfere with WSL2/Docker
- **MEDIUM**: Port conflicts between Windows and WSL2 services
- **LOW**: Docker image pull times may be significant on first setup

## Technical Implementation Plan

### Phase 4A: WSL2 Foundation Setup (Hours 1-3)
```bash
# WSL2 Environment Setup Script
#!/bin/bash
# wsl2_setup.sh - Complete WSL2 environment configuration

set -e

echo "🚀 Setting up WSL2 Ubuntu environment for Kailash SDK development"

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential development tools
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    tree \
    jq \
    unzip \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Install Python 3.11 and development tools
sudo apt install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    python3-setuptools

# Set Python 3.11 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Install Node.js (for any web interface needs)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Docker CLI (Docker Desktop provides daemon)
sudo apt install -y docker.io
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create development directory structure
mkdir -p ~/development/kailash-sdk
mkdir -p ~/development/docker-services
mkdir -p ~/development/logs

echo "✅ WSL2 Ubuntu environment setup completed"
echo "📝 Please restart WSL2 session to ensure all changes take effect"
```

### Phase 4B: Docker Services Infrastructure (Hours 4-7)
```yaml
# docker-compose.production-services.yml
# Complete production-like service stack for development and testing
version: '3.8'

networks:
  kailash-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  postgres-data:
  neo4j-data:
  neo4j-logs:
  neo4j-import:
  neo4j-plugins:
  redis-data:
  chromadb-data:

services:
  # PostgreSQL - Primary database for structured data
  postgres:
    image: postgres:15-alpine
    container_name: kailash-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: kailash_dev
      POSTGRES_USER: kailash_user
      POSTGRES_PASSWORD: kailash_dev_password
      POSTGRES_MULTIPLE_DATABASES: "kailash_test,horme_dev,horme_test"
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/postgres:/docker-entrypoint-initdb.d
    networks:
      - kailash-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kailash_user -d kailash_dev"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Neo4j - Knowledge graph database
  neo4j:
    image: neo4j:5.3-community
    container_name: kailash-neo4j
    restart: unless-stopped
    environment:
      NEO4J_AUTH: neo4j/kailash_neo4j_password
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
      NEO4J_apoc_export_file_enabled: true
      NEO4J_apoc_import_file_enabled: true
      NEO4J_apoc_import_file_use__neo4j__config: true
      NEO4JLABS_PLUGINS: '["apoc", "graph-data-science"]'
      NEO4J_dbms_security_procedures_unrestricted: "apoc.*,gds.*"
      NEO4J_dbms_memory_heap_initial__size: 1G
      NEO4J_dbms_memory_heap_max__size: 2G
      NEO4J_dbms_memory_pagecache_size: 1G
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j-data:/data
      - neo4j-logs:/logs
      - neo4j-import:/var/lib/neo4j/import
      - neo4j-plugins:/plugins
    networks:
      - kailash-network
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "kailash_neo4j_password", "RETURN 'Health Check' as status"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis - Caching and session storage
  redis:
    image: redis:7-alpine
    container_name: kailash-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass kailash_redis_password
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - kailash-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # ChromaDB - Vector database for embeddings
  chromadb:
    image: chromadb/chroma:latest
    container_name: kailash-chromadb
    restart: unless-stopped
    environment:
      CHROMA_SERVER_AUTH_CREDENTIALS_PROVIDER: chromadb.auth.basic.BasicAuthCredentialsProvider
      CHROMA_SERVER_AUTH_PROVIDER: chromadb.auth.basic.BasicAuthServerProvider
    ports:
      - "8000:8000"
    volumes:
      - chromadb-data:/chroma/chroma
    networks:
      - kailash-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Elasticsearch - Full-text search and analytics
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    container_name: kailash-elasticsearch
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    networks:
      - kailash-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # MinIO - S3-compatible object storage
  minio:
    image: minio/minio:latest
    container_name: kailash-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: kailash_minio_user
      MINIO_ROOT_PASSWORD: kailash_minio_password
    ports:
      - "9000:9000"  # API
      - "9001:9001"  # Console
    volumes:
      - minio-data:/data
    networks:
      - kailash-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Service Health Monitor
  health-monitor:
    build:
      context: ./monitoring
      dockerfile: Dockerfile.health-monitor
    container_name: kailash-health-monitor
    restart: unless-stopped
    environment:
      MONITOR_INTERVAL: 30
      NOTIFICATION_WEBHOOK: ""
    depends_on:
      - postgres
      - neo4j
      - redis
      - chromadb
      - elasticsearch
      - minio
    networks:
      - kailash-network
    volumes:
      - ./monitoring/logs:/app/logs

volumes:
  elasticsearch-data:
  minio-data:
```

### Phase 4C: Cross-Platform Network Configuration (Hours 8-9)
```python
# network_configurator.py
import subprocess
import socket
import time
import os
from typing import Dict, List, Tuple

class CrossPlatformNetworkConfigurator:
    """Configure networking between Windows, WSL2, and Docker"""
    
    def __init__(self):
        self.services = {
            "postgres": {"port": 5432, "health_endpoint": None},
            "neo4j": {"port": 7474, "health_endpoint": "http://localhost:7474"},
            "redis": {"port": 6379, "health_endpoint": None},
            "chromadb": {"port": 8000, "health_endpoint": "http://localhost:8000/api/v1/heartbeat"},
            "elasticsearch": {"port": 9200, "health_endpoint": "http://localhost:9200/_cluster/health"},
            "minio": {"port": 9000, "health_endpoint": "http://localhost:9000/minio/health/live"}
        }
        
        self.wsl_ip = self._get_wsl_ip()
        self.windows_ip = self._get_windows_ip()
    
    def configure_networking(self) -> Dict[str, any]:
        """Configure complete cross-platform networking"""
        
        results = {
            "wsl_ip": self.wsl_ip,
            "windows_ip": self.windows_ip,
            "port_forwards": [],
            "firewall_rules": [],
            "connectivity_tests": {}
        }
        
        # Configure port forwarding
        for service, config in self.services.items():
            port = config["port"]
            forward_result = self._configure_port_forward(service, port)
            results["port_forwards"].append(forward_result)
        
        # Configure Windows Firewall rules
        firewall_results = self._configure_firewall_rules()
        results["firewall_rules"] = firewall_results
        
        # Test connectivity
        for service, config in self.services.items():
            connectivity = self._test_service_connectivity(service, config)
            results["connectivity_tests"][service] = connectivity
        
        return results
    
    def _get_wsl_ip(self) -> str:
        """Get WSL2 IP address"""
        try:
            result = subprocess.run(
                ["wsl", "hostname", "-I"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "172.20.0.1"  # Default WSL2 IP
    
    def _get_windows_ip(self) -> str:
        """Get Windows host IP from WSL2 perspective"""
        try:
            result = subprocess.run(
                ["wsl", "ip", "route", "show", "default"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            # Parse default gateway IP
            lines = result.stdout.split('\n')
            for line in lines:
                if 'default' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        return parts[2]
        except subprocess.CalledProcessError:
            pass
        
        return "host.docker.internal"
    
    def _configure_port_forward(self, service: str, port: int) -> Dict[str, any]:
        """Configure port forwarding for service"""
        
        # Windows netsh port forwarding
        try:
            cmd = [
                "netsh", "interface", "portproxy", "add", "v4tov4",
                f"listenaddress=0.0.0.0",
                f"listenport={port}",
                f"connectaddress={self.wsl_ip}",
                f"connectport={port}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return {
                "service": service,
                "port": port,
                "status": "success" if result.returncode == 0 else "failed",
                "command": " ".join(cmd),
                "output": result.stdout,
                "error": result.stderr
            }
            
        except Exception as e:
            return {
                "service": service,
                "port": port,
                "status": "error",
                "error": str(e)
            }
    
    def _configure_firewall_rules(self) -> List[Dict[str, any]]:
        """Configure Windows Firewall rules for services"""
        
        firewall_rules = []
        
        for service, config in self.services.items():
            port = config["port"]
            
            # Inbound rule
            rule_name = f"Kailash-{service.capitalize()}-Inbound"
            cmd = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}",
                "dir=in",
                "action=allow",
                "protocol=TCP",
                f"localport={port}"
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                firewall_rules.append({
                    "rule_name": rule_name,
                    "service": service,
                    "port": port,
                    "direction": "inbound",
                    "status": "success" if result.returncode == 0 else "failed",
                    "output": result.stdout,
                    "error": result.stderr
                })
            except Exception as e:
                firewall_rules.append({
                    "rule_name": rule_name,
                    "service": service,
                    "error": str(e)
                })
        
        return firewall_rules
    
    def _test_service_connectivity(self, service: str, config: Dict[str, any]) -> Dict[str, any]:
        """Test connectivity to service from Windows"""
        
        port = config["port"]
        health_endpoint = config["health_endpoint"]
        
        connectivity_result = {
            "service": service,
            "port_accessible": False,
            "health_check": False,
            "response_time": None
        }
        
        # Test port connectivity
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', port))
            response_time = time.time() - start_time
            sock.close()
            
            connectivity_result["port_accessible"] = result == 0
            connectivity_result["response_time"] = response_time
            
        except Exception as e:
            connectivity_result["port_error"] = str(e)
        
        # Test health endpoint if available
        if health_endpoint:
            try:
                import requests
                response = requests.get(health_endpoint, timeout=10)
                connectivity_result["health_check"] = response.status_code == 200
                connectivity_result["health_response"] = response.status_code
            except Exception as e:
                connectivity_result["health_error"] = str(e)
        
        return connectivity_result

# Service management utilities
class ServiceManager:
    """Manage Docker services across WSL2 environment"""
    
    def __init__(self):
        self.compose_file = "docker-compose.production-services.yml"
    
    def start_all_services(self) -> Dict[str, any]:
        """Start all infrastructure services"""
        try:
            result = subprocess.run([
                "wsl", "docker-compose", "-f", self.compose_file, "up", "-d"
            ], capture_output=True, text=True, check=True)
            
            return {
                "status": "success",
                "output": result.stdout,
                "services_started": self._get_running_services()
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "failed",
                "error": e.stderr,
                "returncode": e.returncode
            }
    
    def stop_all_services(self) -> Dict[str, any]:
        """Stop all infrastructure services"""
        try:
            result = subprocess.run([
                "wsl", "docker-compose", "-f", self.compose_file, "down"
            ], capture_output=True, text=True, check=True)
            
            return {
                "status": "success",
                "output": result.stdout
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "failed",
                "error": e.stderr
            }
    
    def get_service_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of all services"""
        try:
            result = subprocess.run([
                "wsl", "docker-compose", "-f", self.compose_file, "ps", "--format", "json"
            ], capture_output=True, text=True, check=True)
            
            import json
            services = json.loads(result.stdout)
            
            status_dict = {}
            for service in services:
                status_dict[service['Service']] = {
                    "state": service['State'],
                    "status": service.get('Status', ''),
                    "ports": service.get('Publishers', [])
                }
            
            return status_dict
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_running_services(self) -> List[str]:
        """Get list of currently running services"""
        try:
            result = subprocess.run([
                "wsl", "docker-compose", "-f", self.compose_file, "ps", "--services", "--filter", "status=running"
            ], capture_output=True, text=True, check=True)
            
            return result.stdout.strip().split('\n')
        except:
            return []
```

## Testing Requirements

### Infrastructure Tests (Priority 1)
- [ ] WSL2 environment functionality validation
- [ ] Docker services startup and health checks
- [ ] Cross-platform network connectivity tests
- [ ] Service port accessibility from Windows

### Integration Tests (Priority 2)
- [ ] Database connection tests from Windows development environment
- [ ] Service communication tests between all components
- [ ] Performance validation of cross-platform operations
- [ ] Resource usage and capacity testing

### End-to-End Tests (Priority 3)
- [ ] Complete development workflow validation
- [ ] Test infrastructure using real services
- [ ] Production-like load testing
- [ ] Disaster recovery and service restart testing

## Definition of Done

- [ ] All acceptance criteria met and verified
- [ ] WSL2 Ubuntu environment fully operational with all development tools
- [ ] All required services running and accessible from Windows
- [ ] Cross-platform networking seamlessly configured
- [ ] Service health monitoring operational
- [ ] Development environment can use all services without mocking
- [ ] Complete documentation and automation scripts available
- [ ] Resource usage optimized and system stable

## Environment Setup Scripts

```bash
# Quick setup command
curl -sSL https://raw.githubusercontent.com/your-repo/kailash-sdk/main/scripts/setup-wsl2-environment.sh | bash

# Manual setup
git clone https://github.com/your-repo/kailash-sdk.git
cd kailash-sdk/infrastructure
./setup-wsl2-environment.sh
docker-compose -f docker-compose.production-services.yml up -d
python network_configurator.py --configure-all
```

## Progress Tracking

**Phase 4A (Hours 1-3):** [ ] WSL2 Ubuntu environment setup and configuration  
**Phase 4B (Hours 4-7):** [ ] Docker services infrastructure deployment  
**Phase 4C (Hours 8-9):** [ ] Cross-platform network configuration  
**Phase 4D (Hours 10-11):** [ ] Service health monitoring and management  
**Phase 4E (Hour 12):** [ ] Development environment integration validation  

## Success Metrics

- **Service Availability**: 99.9% uptime for all critical services
- **Network Performance**: <10ms latency between Windows and WSL2 services
- **Resource Efficiency**: <50% system resource utilization under normal load
- **Setup Time**: Complete environment deployment in <30 minutes
- **Test Integration**: 100% test infrastructure can use real services

## Next Actions After Completion

1. **INFRA-005**: SDK registration compliance (depends on working test infrastructure)
2. **INFRA-006**: DataFlow auto-generation validation (needs database services)
3. **INFRA-007**: Progress validation checkpoints (uses service health monitoring)

This deployment provides the robust infrastructure foundation needed for all subsequent development and testing activities.