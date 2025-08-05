# ADR-004: Test Infrastructure Recovery Architecture

## Status
Proposed

## Context

The project's test infrastructure has experienced a complete breakdown with 0% test success rate. Analysis reveals systematic issues across multiple layers:

1. **Missing Dependencies**: 15+ critical packages not installed
2. **Service Infrastructure**: External services (PostgreSQL, Neo4j, ChromaDB, OpenAI) not configured
3. **SDK Compatibility**: Kailash SDK import failures and version mismatches
4. **Platform Issues**: Windows-specific compatibility problems
5. **Test Isolation**: No proper test environment isolation

The existing test structure includes 32 test files across 3 tiers (unit/integration/e2e) but none can execute successfully. This blocks all development activities and prevents code quality validation.

**Constraints**:
- Must support Windows development environment
- Must integrate with existing Kailash SDK patterns
- Must support real infrastructure testing (no mocking in Tiers 2-3)
- Must complete recovery within 7 days
- Must achieve 100% test success rate

**Requirements**:
- PostgreSQL for DataFlow model testing
- Neo4j for knowledge graph operations
- ChromaDB for vector database testing
- OpenAI API for AI integration tests
- Docker for service orchestration
- Windows compatibility patches

## Decision

We will implement a **Layered Test Infrastructure Architecture** with the following key decisions:

### 1. Multi-Tier Testing Strategy
- **Tier 1 (Unit)**: Fast tests with selective mocking, <1s per test
- **Tier 2 (Integration)**: Real services, no mocking, <5s per test
- **Tier 3 (E2E)**: Complete workflows, <10s per test

### 2. Service Orchestration Approach
- Use Docker Compose for all external services
- Implement service health checks before test execution
- Provide fallback mechanisms for service failures
- Support both Docker Desktop (Windows) and native Docker

### 3. SDK Compatibility Strategy
- Pin Kailash SDK to compatible version (0.3.0)
- Implement Windows resource module patch
- Use 3-method parameter pattern consistently
- Always use `runtime.execute(workflow.build())`

### 4. Database Management Approach
- PostgreSQL as primary test database
- Separate test schemas for isolation
- Automatic test data cleanup between tests
- Connection pooling for performance

### 5. Development Environment Strategy
- Support Windows 10/11 with WSL2 option
- Provide native Windows compatibility patches
- Docker Desktop integration
- Comprehensive environment validation scripts

## Consequences

### Positive
- **Complete Test Recovery**: 100% test success rate achievable
- **Platform Compatibility**: Full Windows development support
- **Service Integration**: Real infrastructure testing capabilities
- **Development Velocity**: Unblocked development workflow
- **Quality Assurance**: Comprehensive test coverage validation
- **CI/CD Ready**: GitHub Actions integration prepared
- **Scalable Architecture**: Supports parallel test execution
- **Maintainable Structure**: Clear separation of concerns

### Negative
- **Initial Complexity**: 7-day setup and recovery period
- **Resource Requirements**: Higher memory/CPU usage with real services
- **Infrastructure Dependencies**: Requires Docker and external services
- **Learning Curve**: Team needs to understand new test patterns
- **Maintenance Overhead**: Regular service updates and monitoring needed
- **Cost Implications**: OpenAI API usage costs for AI tests

## Alternatives Considered

### Option 1: Mock-Heavy Approach
**Description**: Use extensive mocking to avoid external service dependencies
**Pros**: 
- Faster test execution
- No external service requirements
- Simpler setup
**Cons**: 
- Doesn't validate real integrations
- Mock maintenance burden
- False sense of test coverage
**Why Rejected**: Fails to meet "real infrastructure" requirement for Tiers 2-3

### Option 2: Cloud-Based Testing Services
**Description**: Use cloud-hosted databases and services for testing
**Pros**: 
- No local infrastructure setup
- Managed service reliability
- Scalable resources
**Cons**: 
- Network dependency for all tests
- Cost implications
- Slower test execution
- Security concerns for test data
**Why Rejected**: Creates external dependencies and violates local development principle

### Option 3: Lightweight Service Alternatives
**Description**: Use in-memory databases and lightweight service alternatives
**Pros**: 
- Faster startup times
- Lower resource usage
- Simpler configuration
**Cons**: 
- Different behavior from production services
- Limited feature compatibility
- Doesn't test real integrations
**Why Rejected**: PostgreSQL-specific features (JSONB, GIN indexes) required for DataFlow

## Implementation Plan

### Phase 1: Foundation Setup (Days 1-2)
```bash
# Core dependencies installation
pip install -r requirements-test.txt

# Database setup
docker-compose -f docker-compose.test.yml up -d postgresql
python setup_test_database.py

# Windows compatibility
python apply_windows_patches.py

# Basic validation
python validate_test_environment.py
```

### Phase 2: Service Integration (Days 3-4)
```bash
# All services deployment
docker-compose -f docker-compose.test.yml up -d

# Service health validation
python test_service_health.py

# Integration validation
pytest tests/integration/ -v --timeout=300
```

### Phase 3: Test Recovery (Days 5-6)
```bash
# Full test suite execution
pytest tests/ -v --timeout=600 --maxfail=5

# Performance validation
pytest tests/ --durations=20 --benchmark

# Coverage reporting
pytest tests/ --cov=src --cov-report=html
```

### Phase 4: CI/CD Integration (Day 7)
```yaml
# GitHub Actions workflow
name: Test Infrastructure
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
```

## Technical Specifications

### Service Configuration
```yaml
# docker-compose.test.yml
version: '3.8'
services:
  postgresql:
    image: postgres:15
    environment:
      POSTGRES_DB: test_horme_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d test_horme_db"]
      interval: 10s
      timeout: 5s
      retries: 5
      
  neo4j:
    image: neo4j:5.0
    environment:
      NEO4J_AUTH: neo4j/testpassword
      NEO4J_PLUGINS: '["apoc"]'
    ports:
      - "7474:7474"
      - "7687:7687"
    healthcheck:
      test: ["CMD-SHELL", "cypher-shell -u neo4j -p testpassword 'RETURN 1'"]
      interval: 15s
      timeout: 10s
      retries: 5
      
  chromadb:
    image: ghcr.io/chroma-core/chroma:latest
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 3
```

### Test Environment Configuration
```python
# test_config.py
import os
from pathlib import Path

# Base configuration
PROJECT_ROOT = Path(__file__).parent.parent
TEST_DATA_DIR = PROJECT_ROOT / "test-data"
REPORTS_DIR = PROJECT_ROOT / "test-reports"

# Database configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://test_user:test_password@localhost:5432/test_horme_db"
)

# Service endpoints
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = ("neo4j", "testpassword")

CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Test execution configuration
TEST_TIMEOUT = int(os.getenv("TEST_TIMEOUT", "300"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
PARALLEL_TESTS = os.getenv("PARALLEL_TESTS", "false").lower() == "true"
```

### Performance Thresholds
```python
# Performance requirements
PERFORMANCE_THRESHOLDS = {
    "unit_test_max_duration": 1.0,      # seconds
    "integration_test_max_duration": 5.0,  # seconds
    "e2e_test_max_duration": 10.0,     # seconds
    "total_suite_max_duration": 900,   # 15 minutes
    "database_operation_max_duration": 1.0,  # seconds
    "api_response_max_duration": 2.0,  # seconds
}
```

## Monitoring and Validation

### Health Check Framework
```python
# health_checks.py
async def validate_test_environment():
    """Comprehensive test environment validation"""
    checks = [
        check_python_dependencies(),
        check_database_connectivity(),
        check_neo4j_connectivity(),
        check_chromadb_connectivity(),
        check_openai_api_access(),
        check_docker_services(),
        check_sdk_compatibility(),
        check_performance_baseline()
    ]
    
    results = await asyncio.gather(*checks)
    return all(results)
```

### Error Reporting
```python
# test_reporting.py
class TestInfrastructureReporter:
    """Comprehensive test infrastructure reporting"""
    
    def generate_infrastructure_report(self):
        return {
            "environment": self.get_environment_info(),
            "services": self.get_service_status(),
            "dependencies": self.get_dependency_status(),
            "performance": self.get_performance_metrics(),
            "failures": self.get_failure_analysis()
        }
```

This architecture decision provides a robust foundation for test infrastructure recovery while maintaining compatibility with existing SDK patterns and supporting future development needs.