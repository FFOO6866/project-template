# INFRA-005: Docker Infrastructure Setup for Production Readiness

**Created:** 2025-08-04  
**Assigned:** testing-specialist + infrastructure-team  
**Priority:** 🚨 P0 - IMMEDIATE  
**Status:** PENDING  
**Estimated Effort:** 2 hours  
**Due Date:** 2025-08-04 (Critical for compliance tests)

## Description

Deploy the 5 required Docker services (PostgreSQL, Neo4j, ChromaDB, Redis, OpenAI integration) to enable real infrastructure testing and resolve the 3 failing compliance tests. This establishes production-like testing infrastructure with NO MOCKING policy.

## Critical Infrastructure Requirements

**Available Services** (from `tests/utils/docker-compose.test.yml`):
1. **PostgreSQL** (pgvector) - Port 5434 - Primary database
2. **Redis** - Port 6380 - Caching and session storage  
3. **Ollama** - Port 11435 - Local AI model serving
4. **MySQL** - Port 3307 - Alternative database
5. **MongoDB** - Port 27017 - Document database
6. **Mock API** - Port 8888 - API testing service

**Current Status:** 0/6 services running (ready to deploy)
**Target Status:** 6/6 services operational with health checks passing

## Acceptance Criteria

- [ ] PostgreSQL database service running and accessible from Windows
- [ ] Neo4j knowledge graph database operational with required plugins
- [ ] ChromaDB vector database service running with API access
- [ ] Redis caching service configured and accessible
- [ ] OpenAI integration environment properly configured
- [ ] All services accessible from Windows development environment
- [ ] Service health monitoring operational
- [ ] Compliance tests can connect to real services (NO MOCKING)

## Subtasks

- [ ] Docker Environment Validation and Setup (Est: 30min)
  - Verification: Docker Desktop and WSL2 integration working
  - Output: Docker environment ready for service deployment
- [ ] PostgreSQL Database Deployment (Est: 45min)
  - Verification: PostgreSQL running with proper database and user setup
  - Output: Database accessible for DataFlow model operations
- [ ] Neo4j Knowledge Graph Setup (Est: 60min)
  - Verification: Neo4j with APOC plugins running and accessible
  - Output: Graph database ready for relationship modeling
- [ ] ChromaDB Vector Database Deployment (Est: 45min)
  - Verification: ChromaDB API accessible for embedding operations
  - Output: Vector database operational for AI workflows
- [ ] Redis and OpenAI Integration (Est: 30min)
  - Verification: Redis caching and OpenAI API configuration working
  - Output: Supporting services operational
- [ ] Service Health Validation (Est: 30min)
  - Verification: All 5 services passing health checks
  - Output: Complete infrastructure operational

## Dependencies

- Docker Desktop for Windows (already installed)
- WSL2 environment (already operational based on current output)
- System resources (16GB+ RAM recommended for all services)
- Network configuration (ports available)

## Risk Assessment

- **MEDIUM**: Resource requirements may impact system performance
- **MEDIUM**: Port conflicts with existing services
- **LOW**: Initial Docker image download time
- **LOW**: Service startup coordination dependencies

## Technical Implementation Plan

### Phase 5A: Docker Environment Validation (15 minutes)
```bash
# EXACT COMMANDS to execute:
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov

# Validate Docker environment
docker --version
docker-compose --version

# Check WSL2 integration status
wsl --list --verbose
docker system info | findstr "Operating System"

# Validate existing docker-compose file
dir tests\utils\docker-compose.test.yml
type tests\utils\docker-compose.test.yml | findstr "services:"
```

### Phase 5B: Service Deployment Using Existing Configuration (1.5 hours)
```bash
# EXACT DEPLOYMENT COMMANDS:
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov

# Deploy all test infrastructure services
docker-compose -f tests/utils/docker-compose.test.yml up -d

# Wait for services to start
echo "Waiting for services to initialize..."
timeout /t 60

# Check service status
docker-compose -f tests/utils/docker-compose.test.yml ps

# View service logs
docker-compose -f tests/utils/docker-compose.test.yml logs --tail=10
```

**Note**: Using existing `tests/utils/docker-compose.test.yml` instead of creating new configuration:
version: '3.8'

networks:
  kailash-network:
    driver: bridge

volumes:
  postgres-data:
  neo4j-data:
  redis-data:
  chromadb-data:

services:
  # PostgreSQL - Primary database
  postgres:
    image: postgres:15-alpine
    container_name: kailash-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: kailash_dev
      POSTGRES_USER: kailash_user
      POSTGRES_PASSWORD: kailash_dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
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
      NEO4J_PLUGINS: '["apoc"]'
      NEO4J_apoc_export_file_enabled: true
      NEO4J_apoc_import_file_enabled: true
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j-data:/data
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

  # ChromaDB - Vector database
  chromadb:
    image: chromadb/chroma:latest
    container_name: kailash-chromadb
    restart: unless-stopped
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

  # Service Health Monitor
  health-monitor:
    image: alpine:latest
    container_name: kailash-health-monitor
    restart: unless-stopped
    command: |
      sh -c "
        while true; do
          echo '=== Service Health Check ===' 
          echo 'PostgreSQL:' && nc -z postgres 5432 && echo 'OK' || echo 'FAIL'
          echo 'Neo4j:' && nc -z neo4j 7474 && echo 'OK' || echo 'FAIL' 
          echo 'Redis:' && nc -z redis 6379 && echo 'OK' || echo 'FAIL'
          echo 'ChromaDB:' && nc -z chromadb 8000 && echo 'OK' || echo 'FAIL'
          sleep 30
        done
      "
    depends_on:
      - postgres
      - neo4j
      - redis
      - chromadb
    networks:
      - kailash-network
```

### Phase 5C: Service Health Validation (30 minutes)
```bash
# EXACT VALIDATION COMMANDS:
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov

# Check all service health
docker-compose -f tests/utils/docker-compose.test.yml ps

# Test each service individually
echo "Testing PostgreSQL..."
docker exec kailash_sdk_test_postgres pg_isready -U test_user -d kailash_test

echo "Testing Redis..."
docker exec kailash_sdk_test_redis redis-cli ping

echo "Testing MySQL..."
docker exec kailash_sdk_test_mysql mysqladmin ping -h localhost

echo "Testing MongoDB..."
docker exec kailash_sdk_test_mongodb mongosh --eval "db.adminCommand('ping')"

echo "Testing Mock API..."
curl -f http://localhost:8888/health

echo "Testing Ollama..."
curl -f http://localhost:11435/api/tags

# Test service connectivity with Python
python -c "
import psycopg2
import redis
import requests
import pymongo
import pymysql

print('=== Service Connectivity Test ===')

# Test PostgreSQL (port 5434)
try:
    conn = psycopg2.connect(
        host='localhost', port=5434,
        database='kailash_test', user='test_user',
        password='test_password'
    )
    print('✓ PostgreSQL (5434) connection successful')
    conn.close()
except Exception as e:
    print(f'✗ PostgreSQL connection failed: {e}')

# Test Redis (port 6380)
try:
    r = redis.Redis(host='localhost', port=6380)
    r.ping()
    print('✓ Redis (6380) connection successful')
except Exception as e:
    print(f'✗ Redis connection failed: {e}')

# Test MySQL (port 3307)
try:
    conn = pymysql.connect(
        host='localhost', port=3307,
        user='kailash_test', password='test_password',
        database='kailash_test'
    )
    print('✓ MySQL (3307) connection successful')
    conn.close()
except Exception as e:
    print(f'✗ MySQL connection failed: {e}')

# Test MongoDB (port 27017)
try:
    client = pymongo.MongoClient('mongodb://kailash:kailash123@localhost:27017/')
    client.admin.command('ping')
    print('✓ MongoDB (27017) connection successful')
    client.close()
except Exception as e:
    print(f'✗ MongoDB connection failed: {e}')

# Test Mock API (port 8888)
try:
    response = requests.get('http://localhost:8888/health', timeout=5)
    if response.status_code == 200:
        print('✓ Mock API (8888) connection successful')
    else:
        print(f'✗ Mock API health check failed: {response.status_code}')
except Exception as e:
    print(f'✗ Mock API connection failed: {e}')

# Test Ollama (port 11435)
try:
    response = requests.get('http://localhost:11435/api/tags', timeout=10)
    if response.status_code == 200:
        print('✓ Ollama (11435) connection successful')
    else:
        print(f'✗ Ollama health check failed: {response.status_code}')
except Exception as e:
    print(f'✗ Ollama connection failed: {e}')

print('=== Service Test Complete ===')
"
```

### Phase 5D: OpenAI Integration Configuration (30 minutes)
```python
# Configure OpenAI integration for testing
import os

# Create environment configuration file
env_config = '''
# OpenAI Configuration for Testing
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ORG_ID=your_org_id_here

# Database Connections
DATABASE_URL=postgresql://kailash_user:kailash_dev_password@localhost:5432/kailash_dev
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=kailash_neo4j_password
REDIS_URL=redis://:kailash_redis_password@localhost:6379
CHROMADB_URL=http://localhost:8000

# Service Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
'''

with open('.env.testing', 'w') as f:
    f.write(env_config)
    
print("OpenAI integration environment configuration created")
```

## Testing Requirements

### Infrastructure Tests (Critical Priority)
- [ ] All 5 services starting and running successfully
- [ ] Service health checks passing
- [ ] Database connectivity from Windows development environment
- [ ] Port accessibility and network configuration

### Integration Tests (After Infrastructure)
- [ ] Compliance tests connecting to real services
- [ ] DataFlow models using PostgreSQL database
- [ ] Vector operations using ChromaDB
- [ ] Knowledge graph operations using Neo4j

### Performance Tests (After Integration)
- [ ] Service response times under load
- [ ] Resource usage and memory consumption
- [ ] Concurrent connection handling

## Definition of Done

- [ ] All 5 required services running and healthy
- [ ] Service health monitoring operational
- [ ] All services accessible from Windows development environment
- [ ] Compliance tests can connect to real infrastructure
- [ ] No mocking required for Tier 2-3 testing
- [ ] Service configuration documented and automated

## Environment Setup Script

```bash
# Quick deployment script
#!/bin/bash
# deploy-infrastructure.sh

echo "🚀 Deploying Kailash SDK infrastructure services"

# Create docker-compose file
cat > docker-compose.production-services.yml << 'EOF'
[Docker Compose content from Phase 5B]
EOF

# Deploy services
docker-compose -f docker-compose.production-services.yml up -d

# Wait for startup
echo "⏳ Waiting for services to start..."
sleep 60

# Validate deployment
echo "✅ Validating service deployment..."
docker-compose -f docker-compose.production-services.yml ps

echo "🎉 Infrastructure deployment complete!"
echo "Services available at:"
echo "  PostgreSQL: localhost:5432"
echo "  Neo4j: http://localhost:7474"  
echo "  Redis: localhost:6379"
echo "  ChromaDB: http://localhost:8000"
```

## Success Metrics

- **Service Availability**: 5/5 services running and healthy
- **Connectivity**: 100% success rate for service connections from tests
- **Health Checks**: All services passing automated health validation
- **Compliance Tests**: 3/3 compliance tests now using real infrastructure

## Next Actions After Completion

1. **TEST-007**: Compliance test infrastructure fixes (depends on Docker services)
2. **FOUND-003**: DataFlow models using PostgreSQL (depends on database service)
3. **VALID-001**: Production readiness validation (includes infrastructure health)

This task establishes the critical infrastructure foundation for all subsequent testing and production readiness activities.