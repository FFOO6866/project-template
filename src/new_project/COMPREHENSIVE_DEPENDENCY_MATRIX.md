# Comprehensive Dependency Matrix with Versions and Compatibility

**Status:** In Progress  
**Date:** 2025-08-03  
**Authors:** Requirements Analysis Specialist  
**Project:** Kailash SDK Multi-Framework Implementation  
**Purpose:** Production readiness dependency validation and compatibility matrix

---

## Executive Summary

This comprehensive dependency matrix provides detailed version requirements, compatibility constraints, and cross-platform dependencies for achieving 100% production readiness. The analysis identifies critical compatibility issues and provides specific version constraints for each framework component.

### Critical Compatibility Issues Identified
1. **Unix-only Dependencies**: `resource` module blocking Windows development
2. **Version Conflicts**: Potential conflicts between Core SDK, DataFlow, and Nexus requirements
3. **Service Dependencies**: Database and AI service version constraints
4. **Cross-Platform Requirements**: Windows + WSL2 + Docker compatibility matrix

## 1. Core System Dependencies

### Python Environment Requirements
| Component | Version | Windows Native | WSL2/Linux | Docker | Criticality | Notes |
|-----------|---------|----------------|------------|---------|-------------|--------|
| Python | >=3.11,<3.13 | ✅ | ✅ | ✅ | CRITICAL | Type hints, performance improvements |
| pip | >=23.0 | ✅ | ✅ | ✅ | CRITICAL | Security updates, resolver improvements |
| venv | Built-in | ✅ | ✅ | ✅ | HIGH | Virtual environment isolation |
| wheel | >=0.40.0 | ✅ | ✅ | ✅ | HIGH | Binary package distribution |
| setuptools | >=65.0 | ✅ | ✅ | ✅ | HIGH | Package building and installation |

### Operating System Compatibility Matrix
| OS Component | Windows 11 | WSL2 Ubuntu 22.04 | Docker Desktop | Required | Compatibility Notes |
|--------------|------------|-------------------|-----------------|----------|-------------------|
| Base OS | ✅ Required | ✅ Required | ✅ Required | CRITICAL | Windows 11 with WSL2 support |
| File System | NTFS | ext4 | overlay2 | HIGH | Cross-FS performance considerations |
| Networking | Windows TCP | Linux TCP | Docker network | HIGH | Port mapping and service discovery |
| Process Management | Windows | systemd | containerd | MEDIUM | Service lifecycle management |
| Memory Management | Windows VM | Linux VM | Docker memory | HIGH | Resource allocation and limits |

## 2. Kailash SDK Framework Dependencies

### Core SDK Dependencies
| Package | Version | Source | Windows | Linux | Docker | Criticality | Purpose |
|---------|---------|--------|---------|--------|---------|-------------|---------|
| kailash | >=0.9.9 | PyPI | ❌ | ✅ | ✅ | CRITICAL | Core workflow framework |
| pydantic | >=2.0.0,<3.0.0 | PyPI | ✅ | ✅ | ✅ | CRITICAL | Data validation and serialization |
| pydantic-settings | >=2.0.0 | PyPI | ✅ | ✅ | ✅ | HIGH | Configuration management |
| typing-extensions | >=4.5.0 | PyPI | ✅ | ✅ | ✅ | HIGH | Type system enhancements |
| python-multipart | >=0.0.6 | PyPI | ✅ | ✅ | ✅ | MEDIUM | File upload handling |

#### Unix Dependency Issues (Windows Incompatible)
| Module | Location | Issue | WSL2 Resolution | Alternative |
|--------|----------|-------|-----------------|-------------|
| resource | kailash/nodes/code/python.py:54 | Unix-only module | ✅ Available in Linux | psutil for cross-platform |
| fcntl | Various SDK locations | File control Unix-only | ✅ Available in Linux | filelock for cross-platform |
| pwd | User management modules | Unix password database | ✅ Available in Linux | getpass for cross-platform |
| grp | Group management modules | Unix group database | ✅ Available in Linux | No direct alternative needed |

### DataFlow Framework Dependencies
| Package | Version | Source | Compatibility | Criticality | Purpose |
|---------|---------|--------|---------------|-------------|---------|
| kailash[dataflow] | >=0.9.9 | PyPI | WSL2+Docker | CRITICAL | Database framework extension |
| sqlalchemy | >=2.0.0,<3.0.0 | PyPI | ✅ Cross-platform | CRITICAL | ORM and database abstraction |
| asyncpg | >=0.28.0 | PyPI | ✅ Cross-platform | CRITICAL | Async PostgreSQL driver |
| alembic | >=1.12.0 | PyPI | ✅ Cross-platform | HIGH | Database migrations |
| psycopg2-binary | >=2.9.7 | PyPI | ✅ Cross-platform | HIGH | PostgreSQL adapter |

### Nexus Platform Dependencies
| Package | Version | Source | Compatibility | Criticality | Purpose |
|---------|---------|--------|---------------|-------------|---------|
| kailash[nexus] | >=0.9.9 | PyPI | WSL2+Docker | CRITICAL | Multi-channel platform |
| fastapi | >=0.104.0,<1.0.0 | PyPI | ✅ Cross-platform | CRITICAL | REST API framework |
| uvicorn[standard] | >=0.24.0 | PyPI | ✅ Cross-platform | CRITICAL | ASGI server |
| websockets | >=11.0.0 | PyPI | ✅ Cross-platform | HIGH | WebSocket support |
| python-jose[cryptography] | >=3.3.0 | PyPI | ✅ Cross-platform | HIGH | JWT token handling |
| passlib[bcrypt] | >=1.7.4 | PyPI | ✅ Cross-platform | HIGH | Password hashing |

## 3. Database and Service Dependencies

### PostgreSQL Dependencies
| Component | Version | Installation | Configuration | Criticality | Notes |
|-----------|---------|-------------|---------------|-------------|--------|
| PostgreSQL Server | 15.x | Docker Official | postgresql.conf | CRITICAL | Primary database |
| pgvector Extension | >=0.5.0 | Docker Extension | CREATE EXTENSION | HIGH | Vector similarity search |
| PostGIS Extension | >=3.3.0 | Docker Extension | Spatial data | MEDIUM | Geographic data support |
| pg_stat_statements | Built-in | Enable in config | Performance monitoring | MEDIUM | Query performance analysis |

#### PostgreSQL Configuration Matrix
```yaml
postgresql.conf:
  max_connections: 200
  shared_buffers: 256MB
  effective_cache_size: 1GB
  maintenance_work_mem: 64MB
  checkpoint_completion_target: 0.9
  wal_buffers: 16MB
  default_statistics_target: 100
  random_page_cost: 1.1
  effective_io_concurrency: 200
  work_mem: 4MB
  min_wal_size: 1GB
  max_wal_size: 4GB
```

### Neo4j Dependencies
| Component | Version | Installation | Configuration | Criticality | Notes |
|-----------|---------|-------------|---------------|-------------|--------|
| Neo4j Community | 5.3.x | Docker Official | neo4j.conf | HIGH | Graph database |
| APOC Plugin | >=5.3.0 | Docker Plugin | apoc.conf | HIGH | Extended procedures |
| GDS Plugin | >=2.4.0 | Docker Plugin | gds.conf | MEDIUM | Graph data science |
| Memory Settings | 4GB heap | Environment | NEO4J_dbms_memory | HIGH | Performance optimization |

#### Neo4j Configuration Matrix
```yaml
neo4j.conf:
  dbms.default_database: neo4j
  dbms.memory.heap.initial_size: 2g
  dbms.memory.heap.max_size: 4g
  dbms.memory.pagecache.size: 2g
  dbms.connector.bolt.enabled: true
  dbms.connector.http.enabled: true
  dbms.security.auth_enabled: true
  dbms.logs.query.enabled: INFO
```

### ChromaDB Dependencies
| Component | Version | Installation | Configuration | Criticality | Notes |
|-----------|---------|-------------|---------------|-------------|--------|
| ChromaDB Server | >=0.4.15 | pip install | settings.yaml | HIGH | Vector database |
| Sentence Transformers | >=2.2.0 | pip install | Model cache | HIGH | Text embeddings |
| OpenAI Embeddings | API | Environment | OPENAI_API_KEY | MEDIUM | Alternative embeddings |
| ONNX Runtime | >=1.15.0 | pip install | Runtime config | MEDIUM | Model optimization |

### Redis Dependencies
| Component | Version | Installation | Configuration | Criticality | Notes |
|-----------|---------|-------------|---------------|-------------|--------|
| Redis Server | 7.x | Docker Official | redis.conf | HIGH | Caching and sessions |
| Redis Modules | Built-in | Docker Config | Module loading | MEDIUM | Extended functionality |
| Memory Policy | allkeys-lru | Configuration | Eviction policy | HIGH | Memory management |
| Persistence | RDB + AOF | Configuration | Data durability | MEDIUM | Backup strategy |

## 4. AI and ML Dependencies

### OpenAI Integration
| Component | Version | Source | Configuration | Criticality | Purpose |
|-----------|---------|--------|---------------|-------------|---------|
| openai | >=1.0.0,<2.0.0 | PyPI | API Key | HIGH | GPT-4 integration |
| tiktoken | >=0.5.0 | PyPI | Token counting | HIGH | Token management |
| tenacity | >=8.2.0 | PyPI | Retry logic | MEDIUM | API resilience |
| httpx | >=0.24.0 | PyPI | HTTP client | MEDIUM | Async API calls |

### Machine Learning Dependencies
| Package | Version | Source | Compatibility | Purpose | Notes |
|---------|---------|--------|---------------|---------|--------|
| scikit-learn | >=1.3.0,<2.0.0 | PyPI | ✅ Cross-platform | ML algorithms | Classification models |
| numpy | >=1.24.0,<2.0.0 | PyPI | ✅ Cross-platform | Numerical computing | Core dependency |
| pandas | >=2.0.0,<3.0.0 | PyPI | ✅ Cross-platform | Data manipulation | Data processing |
| scipy | >=1.10.0 | PyPI | ✅ Cross-platform | Scientific computing | Statistical functions |
| matplotlib | >=3.7.0 | PyPI | ✅ Cross-platform | Visualization | Performance charts |

## 5. Testing Framework Dependencies

### Core Testing Dependencies
| Package | Version | Source | Compatibility | Purpose | Configuration |
|---------|---------|--------|---------------|---------|---------------|
| pytest | >=7.4.0,<8.0.0 | PyPI | ✅ Cross-platform | Test framework | pytest.ini |
| pytest-asyncio | >=0.21.0 | PyPI | ✅ Cross-platform | Async testing | Loop policy |
| pytest-cov | >=4.1.0 | PyPI | ✅ Cross-platform | Coverage reporting | .coveragerc |
| pytest-xdist | >=3.3.0 | PyPI | ✅ Cross-platform | Parallel testing | Workers config |
| pytest-mock | >=3.11.0 | PyPI | ✅ Cross-platform | Mocking framework | Mock objects |

### Testing Infrastructure Dependencies
| Component | Purpose | Docker Image | Configuration | Criticality |
|-----------|---------|--------------|---------------|-------------|
| PostgreSQL Test DB | Integration testing | postgres:15-alpine | test-database.env | CRITICAL |
| Neo4j Test Instance | Graph testing | neo4j:5.3-community | test-neo4j.env | HIGH |
| ChromaDB Test Service | Vector testing | chromadb/chroma:latest | test-chroma.env | HIGH |
| Redis Test Cache | Cache testing | redis:7-alpine | test-redis.env | MEDIUM |

#### Test Configuration Matrix
```yaml
pytest.ini:
  addopts:
    - "--strict-markers"
    - "--strict-config" 
    - "--cov=src"
    - "--cov-report=term-missing"
    - "--cov-report=html"
    - "--cov-report=xml"
    - "--cov-fail-under=85"
  markers:
    - "unit: Unit tests"
    - "integration: Integration tests"  
    - "e2e: End-to-end tests"
    - "slow: Slow running tests"
    - "windows: Windows-specific tests"
```

## 6. Development Tool Dependencies

### Development Environment Tools
| Tool | Version | Installation | Purpose | Criticality |
|------|---------|-------------|---------|-------------|
| VS Code | Latest | Microsoft Store | IDE | HIGH |
| Remote-WSL Extension | Latest | VS Code Marketplace | WSL2 integration | CRITICAL |
| Python Extension | Latest | VS Code Marketplace | Python support | CRITICAL |
| Docker Extension | Latest | VS Code Marketplace | Container management | HIGH |
| GitLens | Latest | VS Code Marketplace | Git integration | MEDIUM |

### Code Quality Tools
| Package | Version | Source | Purpose | Configuration |
|---------|---------|--------|---------|---------------|
| black | >=23.0.0 | PyPI | Code formatting | pyproject.toml |
| isort | >=5.12.0 | PyPI | Import sorting | .isort.cfg |
| flake8 | >=6.0.0 | PyPI | Linting | .flake8 |
| mypy | >=1.5.0 | PyPI | Type checking | mypy.ini |
| pre-commit | >=3.3.0 | PyPI | Git hooks | .pre-commit-config.yaml |

### Documentation Tools
| Package | Version | Source | Purpose | Notes |
|---------|---------|--------|---------|--------|
| sphinx | >=7.0.0 | PyPI | Documentation generation | docs/conf.py |
| sphinx-rtd-theme | >=1.3.0 | PyPI | Documentation theme | ReadTheDocs style |
| myst-parser | >=2.0.0 | PyPI | Markdown support | MyST format |
| sphinx-autodoc | Built-in | Sphinx | API documentation | Docstring extraction |

## 7. Production Deployment Dependencies

### Container Runtime Dependencies
| Component | Version | Source | Purpose | Criticality |
|-----------|---------|--------|---------|-------------|
| Docker Engine | >=24.0.0 | Docker Inc | Container runtime | CRITICAL |
| Docker Compose | >=2.20.0 | Docker Inc | Service orchestration | CRITICAL |
| Docker Desktop | >=4.20.0 | Docker Inc | Windows integration | HIGH |
| WSL2 Integration | Latest | Windows Feature | Linux compatibility | CRITICAL |

### Production Service Dependencies
| Service | Image | Version | Purpose | Resource Requirements |
|---------|-------|---------|---------|----------------------|
| Application | python:3.11-slim | Custom build | Main application | 2GB RAM, 1 CPU |
| PostgreSQL | postgres:15-alpine | 15.4 | Primary database | 4GB RAM, 2 CPU |
| Neo4j | neo4j:5.3-community | 5.3.0 | Graph database | 4GB RAM, 2 CPU |
| ChromaDB | chromadb/chroma:latest | 0.4.15 | Vector database | 2GB RAM, 1 CPU |
| Redis | redis:7-alpine | 7.2 | Cache and sessions | 1GB RAM, 0.5 CPU |
| Nginx | nginx:alpine | 1.25 | Load balancer | 512MB RAM, 0.5 CPU |

### Monitoring and Observability
| Tool | Version | Purpose | Configuration |
|------|---------|---------|---------------|
| Prometheus | >=2.45.0 | Metrics collection | prometheus.yml |
| Grafana | >=10.0.0 | Metrics visualization | grafana.ini |
| Jaeger | >=1.47.0 | Distributed tracing | jaeger-config.yaml |
| Loki | >=2.8.0 | Log aggregation | loki-config.yaml |

## 8. Security and Compliance Dependencies

### Security Libraries
| Package | Version | Source | Purpose | Notes |
|---------|---------|--------|---------|--------|
| cryptography | >=41.0.0 | PyPI | Encryption and signing | FIPS compliance |
| bcrypt | >=4.0.0 | PyPI | Password hashing | Secure defaults |
| pyjwt[crypto] | >=2.8.0 | PyPI | JWT token handling | RS256 support |
| python-multipart | >=0.0.6 | PyPI | File upload security | Size limits |
| python-jose | >=3.3.0 | PyPI | JOSE implementation | Token validation |

### Security Scanning Tools
| Tool | Version | Purpose | Integration |
|------|---------|---------|-------------|
| bandit | >=1.7.5 | Security linting | Pre-commit hook |
| safety | >=2.3.0 | Dependency scanning | CI/CD pipeline |
| semgrep | >=1.30.0 | Static analysis | GitHub Actions |
| trivy | >=0.44.0 | Container scanning | Docker build |

## 9. Version Compatibility Matrix

### Python Version Compatibility
| Python Version | Core SDK | DataFlow | Nexus | AI Components | Status |
|----------------|----------|----------|-------|---------------|---------|
| 3.11.x | ✅ Full | ✅ Full | ✅ Full | ✅ Full | Recommended |
| 3.12.x | ✅ Full | ✅ Full | ✅ Full | ✅ Full | Supported |
| 3.10.x | ⚠️ Limited | ❌ No | ❌ No | ⚠️ Limited | Deprecated |
| 3.13.x | ❌ No | ❌ No | ❌ No | ❌ No | Not supported |

### Operating System Compatibility
| OS Version | Native Support | WSL2 Support | Docker Support | Recommendation |
|------------|----------------|--------------|----------------|----------------|
| Windows 11 | ❌ No | ✅ Full | ✅ Full | Use WSL2 + Docker |
| Windows 10 | ❌ No | ⚠️ Limited | ⚠️ Limited | Upgrade to Windows 11 |
| Ubuntu 22.04 | ✅ Full | N/A | ✅ Full | Native development |
| Ubuntu 20.04 | ⚠️ Limited | N/A | ✅ Full | Upgrade recommended |
| macOS | ⚠️ Limited | N/A | ✅ Full | Use Docker |

### Database Version Compatibility
| Database | Minimum Version | Recommended | Latest Tested | Notes |
|----------|----------------|-------------|---------------|--------|
| PostgreSQL | 13.x | 15.x | 15.4 | Vector extension support |
| Neo4j | 4.4.x | 5.3.x | 5.3.0 | APOC compatibility |
| Redis | 6.x | 7.x | 7.2 | Module support |
| ChromaDB | 0.4.x | 0.4.15 | 0.4.15 | Embedding compatibility |

## 10. Dependency Resolution Strategy

### Installation Order (Critical Path)
```bash
# Phase 1: System Dependencies
1. Windows 11 with WSL2 enabled
2. Docker Desktop with WSL2 backend
3. VS Code with Remote-WSL extension
4. Git for Windows with WSL2 integration

# Phase 2: Python Environment (in WSL2)
5. Python 3.11+ from deadsnakes PPA
6. pip, venv, wheel, setuptools upgrades
7. Virtual environment creation and activation

# Phase 3: Core SDK Dependencies
8. pip install kailash>=0.9.9
9. pip install pydantic>=2.0.0 pydantic-settings
10. Validate SDK imports: python -c "from kailash.workflow.builder import WorkflowBuilder"

# Phase 4: Framework Extensions
11. pip install kailash[dataflow] kailash[nexus]
12. pip install sqlalchemy asyncpg alembic
13. pip install fastapi uvicorn websockets

# Phase 5: Service Dependencies (Docker)
14. docker-compose up -d postgresql neo4j chromadb redis
15. Validate service connectivity
16. Run health checks for all services

# Phase 6: Development Tools
17. pip install pytest pytest-asyncio pytest-cov
18. pip install black isort flake8 mypy
19. pre-commit install
```

### Conflict Resolution Matrix
| Conflict Type | Resolution Strategy | Prevention |
|---------------|-------------------|------------|
| Version conflicts | Pin exact versions in requirements.txt | Dependency tree analysis |
| Platform compatibility | Use WSL2 for Unix dependencies | Cross-platform testing |
| Service port conflicts | Docker Compose port mapping | Port allocation matrix |
| Environment variables | Use .env files with prefixes | Variable naming convention |

### Dependency Lock Files
```yaml
requirements.txt: # Production dependencies
  - Exact versions for reproducible builds
  - Security-patched versions only
  - Cross-platform compatibility verified

requirements-dev.txt: # Development dependencies
  - Testing frameworks and tools
  - Code quality and formatting tools
  - Documentation generation tools

requirements-test.txt: # Testing dependencies
  - Test runners and fixtures
  - Mock and stub libraries
  - Test database tools

docker-compose.yml: # Service dependencies
  - Exact image tags for reproducibility
  - Environment configuration
  - Volume and network definitions
```

## 11. Validation and Testing Strategy

### Dependency Validation Pipeline
```bash
# Automated validation script
#!/bin/bash

# Phase 1: Environment validation
echo "=== Environment Validation ==="
python --version
pip --version
docker --version
wsl --status

# Phase 2: SDK compatibility
echo "=== SDK Compatibility ==="
python -c "from kailash.workflow.builder import WorkflowBuilder; print('✓ Core SDK')"
python -c "import kailash.dataflow; print('✓ DataFlow')"
python -c "import kailash.nexus; print('✓ Nexus')"

# Phase 3: Service connectivity
echo "=== Service Connectivity ==="
python -c "import psycopg2; print('✓ PostgreSQL')"
python -c "from neo4j import GraphDatabase; print('✓ Neo4j')"
python -c "import chromadb; print('✓ ChromaDB')"
python -c "import redis; print('✓ Redis')"

# Phase 4: Performance baseline
echo "=== Performance Baseline ==="
python -m pytest tests/performance/ --benchmark-only
```

### Continuous Integration Validation
- Dependency security scanning with safety and bandit
- License compliance checking
- Version compatibility matrix testing
- Cross-platform build verification
- Performance regression detection

## Conclusion

This comprehensive dependency matrix provides the foundation for reliable production deployment. Key success factors:

1. **WSL2 + Docker Strategy**: Resolves Windows compatibility while maintaining development familiarity
2. **Exact Version Pinning**: Ensures reproducible builds across environments  
3. **Service Orchestration**: Docker Compose for consistent service deployment
4. **Validation Pipeline**: Automated verification of all dependencies
5. **Conflict Resolution**: Clear strategies for handling dependency conflicts

**Next Steps**: Implement automated dependency validation pipeline and begin systematic installation following the critical path order.