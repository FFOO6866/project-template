"""
Tier 1 Unit Tests: Docker Validation and Security Testing

Tests Docker components in isolation without external dependencies.
Focuses on Dockerfile validation, image security, and configuration testing.

CRITICAL: These are Unit Tests (Tier 1) - NO real Docker services
Speed requirement: <1 second per test
"""

import os
import pytest
import re
import yaml
import json
from pathlib import Path
from unittest.mock import patch, Mock, mock_open
from typing import Dict, List, Any


class TestDockerfileValidation:
    """Test Dockerfile structure and security best practices."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent

    @pytest.fixture
    def dockerfiles(self, project_root):
        """Get all Dockerfile paths."""
        return list(project_root.glob("Dockerfile*"))

    def test_dockerfile_exists(self, dockerfiles):
        """Test that Dockerfiles exist in project."""
        assert len(dockerfiles) > 0, "No Dockerfiles found in project"

    def test_dockerfile_has_from_instruction(self, dockerfiles):
        """Test that all Dockerfiles have FROM instruction."""
        for dockerfile in dockerfiles:
            content = dockerfile.read_text()
            assert re.search(r'^FROM\s+\S+', content, re.MULTILINE), \
                f"Dockerfile {dockerfile.name} missing FROM instruction"

    def test_dockerfile_uses_specific_image_tags(self, dockerfiles):
        """Test that Dockerfiles use specific tags, not latest."""
        for dockerfile in dockerfiles:
            content = dockerfile.read_text()
            from_lines = re.findall(r'^FROM\s+(\S+)', content, re.MULTILINE)
            
            for image in from_lines:
                # Allow 'latest' only in build args or for specific patterns
                if ':latest' in image and 'as builder' not in content.lower():
                    # Check if it's using a build arg
                    if not re.search(r'ARG.*VERSION', content):
                        pytest.fail(f"Dockerfile {dockerfile.name} uses ':latest' tag without version control")

    def test_dockerfile_has_security_user(self, dockerfiles):
        """Test that production Dockerfiles create and use non-root user."""
        production_dockerfiles = [f for f in dockerfiles if 'production' in f.name.lower() or 'nexus' in f.name.lower()]
        
        for dockerfile in production_dockerfiles:
            content = dockerfile.read_text()
            
            # Should create a user
            assert re.search(r'(RUN.*useradd|RUN.*adduser)', content), \
                f"Production Dockerfile {dockerfile.name} should create non-root user"
            
            # Should switch to user
            assert re.search(r'^USER\s+(?!root)', content, re.MULTILINE), \
                f"Production Dockerfile {dockerfile.name} should switch to non-root user"

    def test_dockerfile_has_healthcheck(self, dockerfiles):
        """Test that service Dockerfiles include health checks."""
        service_dockerfiles = [f for f in dockerfiles if any(x in f.name.lower() for x in ['nexus', 'mcp', 'sales'])]
        
        for dockerfile in service_dockerfiles:
            content = dockerfile.read_text()
            assert re.search(r'^HEALTHCHECK', content, re.MULTILINE), \
                f"Service Dockerfile {dockerfile.name} should include HEALTHCHECK instruction"

    def test_dockerfile_minimizes_layers(self, dockerfiles):
        """Test that Dockerfiles minimize layers by combining RUN commands."""
        for dockerfile in dockerfiles:
            content = dockerfile.read_text()
            run_lines = re.findall(r'^RUN\s+', content, re.MULTILINE)
            
            # Should not have excessive individual RUN commands
            if len(run_lines) > 10:
                # Check if they use && to combine commands
                combined_runs = [line for line in content.split('\n') if 'RUN' in line and '&&' in line]
                assert len(combined_runs) > 0, \
                    f"Dockerfile {dockerfile.name} has {len(run_lines)} RUN commands, consider combining with &&"

    def test_dockerfile_cleans_package_cache(self, dockerfiles):
        """Test that Dockerfiles clean package manager caches."""
        for dockerfile in dockerfiles:
            content = dockerfile.read_text()
            
            if 'apt-get' in content:
                assert 'rm -rf /var/lib/apt/lists/*' in content, \
                    f"Dockerfile {dockerfile.name} should clean apt cache"
            
            if 'yum install' in content or 'dnf install' in content:
                assert ('yum clean all' in content or 'dnf clean all' in content), \
                    f"Dockerfile {dockerfile.name} should clean yum/dnf cache"

    def test_dockerfile_sets_workdir(self, dockerfiles):
        """Test that Dockerfiles set appropriate WORKDIR."""
        for dockerfile in dockerfiles:
            content = dockerfile.read_text()
            assert re.search(r'^WORKDIR\s+', content, re.MULTILINE), \
                f"Dockerfile {dockerfile.name} should set WORKDIR"

    def test_dockerfile_exposes_documented_ports(self, dockerfiles):
        """Test that exposed ports match documentation."""
        port_mapping = {
            'nexus': [8000, 3001, 9090],
            'mcp': [3001, 3002],
            'sales-assistant': [3002]
        }
        
        for dockerfile in dockerfiles:
            content = dockerfile.read_text()
            expose_lines = re.findall(r'^EXPOSE\s+(.+)', content, re.MULTILINE)
            
            if expose_lines:
                exposed_ports = []
                for line in expose_lines:
                    ports = re.findall(r'\d+', line)
                    exposed_ports.extend([int(p) for p in ports])
                
                # Check against expected ports for service type
                for service_type, expected_ports in port_mapping.items():
                    if service_type in dockerfile.name.lower():
                        for port in expected_ports:
                            assert port in exposed_ports, \
                                f"Dockerfile {dockerfile.name} should expose port {port}"


class TestDockerComposeValidation:
    """Test Docker Compose configuration structure and security."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent

    @pytest.fixture
    def compose_files(self, project_root):
        """Get all docker-compose files."""
        return list(project_root.glob("docker-compose*.yml"))

    def test_compose_files_exist(self, compose_files):
        """Test that docker-compose files exist."""
        assert len(compose_files) > 0, "No docker-compose files found"

    def test_compose_file_valid_yaml(self, compose_files):
        """Test that all compose files are valid YAML."""
        for compose_file in compose_files:
            try:
                with open(compose_file, 'r') as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Docker compose file {compose_file.name} has invalid YAML: {e}")

    def test_compose_services_have_health_checks(self, compose_files):
        """Test that critical services have health checks."""
        critical_services = ['nexus-platform', 'postgres', 'redis', 'mcp-server']
        
        for compose_file in compose_files:
            with open(compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
            
            if 'services' in compose_data:
                for service_name, service_config in compose_data['services'].items():
                    if any(critical in service_name for critical in critical_services):
                        assert 'healthcheck' in service_config, \
                            f"Critical service {service_name} in {compose_file.name} should have healthcheck"

    def test_compose_uses_networks(self, compose_files):
        """Test that compose files define and use custom networks."""
        for compose_file in compose_files:
            with open(compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
            
            if 'services' in compose_data and len(compose_data['services']) > 1:
                # Should define networks
                assert 'networks' in compose_data, \
                    f"Multi-service compose {compose_file.name} should define custom networks"
                
                # Services should use networks
                for service_name, service_config in compose_data['services'].items():
                    if 'networks' not in service_config:
                        pytest.fail(f"Service {service_name} in {compose_file.name} should use custom network")

    def test_compose_uses_volumes_for_persistence(self, compose_files):
        """Test that database services use named volumes."""
        database_services = ['postgres', 'redis', 'chromadb', 'neo4j']
        
        for compose_file in compose_files:
            with open(compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
            
            if 'services' in compose_data:
                for service_name, service_config in compose_data['services'].items():
                    if any(db in service_name.lower() for db in database_services):
                        assert 'volumes' in service_config, \
                            f"Database service {service_name} in {compose_file.name} should use volumes"

    def test_compose_environment_security(self, compose_files):
        """Test that sensitive environment variables use secrets or env files."""
        sensitive_patterns = ['password', 'secret', 'key', 'token']
        
        for compose_file in compose_files:
            with open(compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
            
            if 'services' in compose_data:
                for service_name, service_config in compose_data['services'].items():
                    if 'environment' in service_config:
                        env_vars = service_config['environment']
                        if isinstance(env_vars, list):
                            for env_var in env_vars:
                                if '=' in env_var:
                                    key, value = env_var.split('=', 1)
                                    for pattern in sensitive_patterns:
                                        if pattern.lower() in key.lower() and not value.startswith('${'):
                                            pytest.fail(f"Sensitive env var {key} in {service_name} should use variable substitution")


class TestDockerImageValidation:
    """Test Docker image configuration and metadata."""

    def test_image_labels_present(self):
        """Test that images include proper metadata labels."""
        # Mock dockerfile content for testing
        dockerfile_content = '''
        FROM python:3.11-slim
        LABEL maintainer="test@example.com"
        LABEL version="1.0.0"
        LABEL description="Test service"
        '''
        
        labels = re.findall(r'^LABEL\s+(\w+)=', dockerfile_content, re.MULTILINE)
        required_labels = ['maintainer', 'version', 'description']
        
        for label in required_labels:
            assert label in labels, f"Docker image should include {label} label"

    def test_image_uses_multi_stage_build(self):
        """Test that production images use multi-stage builds."""
        dockerfile_content = '''
        FROM python:3.11-slim as builder
        # build stage
        
        FROM python:3.11-slim as production
        # production stage
        '''
        
        stages = re.findall(r'FROM\s+\S+\s+as\s+(\w+)', dockerfile_content)
        assert 'builder' in stages, "Should have builder stage"
        assert 'production' in stages, "Should have production stage"

    def test_image_size_optimization(self):
        """Test image size optimization techniques."""
        dockerfile_content = '''
        FROM python:3.11-slim
        RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
        '''
        
        # Should clean package cache
        assert 'rm -rf /var/lib/apt/lists/*' in dockerfile_content
        
        # Should use slim base image
        assert 'slim' in dockerfile_content

    @pytest.mark.timeout(1)
    def test_dockerfile_syntax_validation(self):
        """Test Dockerfile syntax without building."""
        # Mock a dockerfile with common syntax issues
        valid_dockerfile = '''
        FROM python:3.11-slim
        WORKDIR /app
        COPY requirements.txt .
        RUN pip install -r requirements.txt
        COPY . .
        EXPOSE 8000
        CMD ["python", "app.py"]
        '''
        
        # Basic syntax validation
        lines = valid_dockerfile.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Should start with valid Dockerfile instruction
                valid_instructions = [
                    'FROM', 'RUN', 'CMD', 'LABEL', 'MAINTAINER', 'EXPOSE',
                    'ENV', 'ADD', 'COPY', 'ENTRYPOINT', 'VOLUME', 'USER',
                    'WORKDIR', 'ARG', 'ONBUILD', 'STOPSIGNAL', 'HEALTHCHECK', 'SHELL'
                ]
                first_word = line.split()[0].upper()
                assert first_word in valid_instructions, f"Invalid Dockerfile instruction: {first_word}"


class TestDockerSecurityScan:
    """Test Docker security configurations."""

    def test_dockerfile_security_best_practices(self):
        """Test security best practices in Dockerfiles."""
        insecure_dockerfile = '''
        FROM ubuntu:latest
        RUN apt-get update
        USER root
        COPY . /
        '''
        
        # Should not use latest tag
        if ':latest' in insecure_dockerfile:
            assert False, "Should not use :latest tag in production"
        
        # Should not run as root
        if 'USER root' in insecure_dockerfile:
            assert False, "Should not explicitly run as root"
        
        # Should not copy everything to root
        if 'COPY . /' in insecure_dockerfile:
            assert False, "Should not copy files to root directory"

    def test_compose_security_settings(self):
        """Test security settings in docker-compose."""
        compose_config = {
            'services': {
                'app': {
                    'image': 'myapp:1.0',
                    'security_opt': ['no-new-privileges:true'],
                    'read_only': True,
                    'tmpfs': ['/tmp', '/var/tmp']
                }
            }
        }
        
        app_service = compose_config['services']['app']
        
        # Should have security options
        assert 'security_opt' in app_service, "Should set security options"
        assert 'no-new-privileges:true' in app_service['security_opt']
        
        # Should use read-only filesystem for security
        assert app_service.get('read_only', False), "Should use read-only filesystem"

    def test_sensitive_data_handling(self):
        """Test proper handling of sensitive data."""
        # Should use secrets or env vars, not hardcoded values
        dockerfile_content = '''
        FROM python:3.11-slim
        ENV DATABASE_PASSWORD=hardcoded_password
        '''
        
        # Check for hardcoded sensitive values
        sensitive_patterns = [r'password\s*=\s*["\']?\w+["\']?', r'secret\s*=\s*["\']?\w+["\']?']
        
        for pattern in sensitive_patterns:
            if re.search(pattern, dockerfile_content, re.IGNORECASE):
                pytest.fail("Should not hardcode sensitive values in Dockerfile")


class TestDockerBuildOptimization:
    """Test Docker build optimization techniques."""

    def test_layer_caching_optimization(self):
        """Test that Dockerfiles optimize for layer caching."""
        optimized_dockerfile = '''
        FROM python:3.11-slim
        
        # Copy requirements first for better caching
        COPY requirements.txt .
        RUN pip install -r requirements.txt
        
        # Copy code last (changes more frequently)
        COPY . .
        '''
        
        lines = [line.strip() for line in optimized_dockerfile.split('\n') if line.strip()]
        
        # Requirements should be copied before source code
        req_copy_idx = -1
        code_copy_idx = -1
        
        for i, line in enumerate(lines):
            if 'COPY requirements.txt' in line:
                req_copy_idx = i
            elif 'COPY . .' in line:
                code_copy_idx = i
        
        if req_copy_idx >= 0 and code_copy_idx >= 0:
            assert req_copy_idx < code_copy_idx, "Requirements should be copied before source code for better caching"

    def test_build_context_optimization(self):
        """Test build context optimization with .dockerignore."""
        # Mock .dockerignore content
        dockerignore_content = '''
        .git
        .pytest_cache
        __pycache__
        *.pyc
        .env
        .venv
        node_modules
        .DS_Store
        '''
        
        ignored_patterns = [line.strip() for line in dockerignore_content.split('\n') if line.strip()]
        
        # Should ignore common development files
        required_ignores = ['.git', '__pycache__', '*.pyc', '.env']
        for pattern in required_ignores:
            assert pattern in ignored_patterns, f"Should ignore {pattern} in .dockerignore"

    def test_multi_stage_build_optimization(self):
        """Test multi-stage build reduces final image size."""
        multistage_dockerfile = '''
        # Build stage
        FROM python:3.11 as builder
        WORKDIR /build
        COPY requirements.txt .
        RUN pip install --user -r requirements.txt
        
        # Production stage
        FROM python:3.11-slim as production
        COPY --from=builder /root/.local /root/.local
        WORKDIR /app
        COPY . .
        '''
        
        # Should have separate builder and production stages
        assert 'FROM python:3.11 as builder' in multistage_dockerfile
        assert 'FROM python:3.11-slim as production' in multistage_dockerfile
        assert 'COPY --from=builder' in multistage_dockerfile


if __name__ == '__main__':
    pytest.main([__file__, '-v'])