# UV Migration Analysis Report
## Comprehensive Dependency Structure Analysis for Horme POV

**Date**: 2025-10-18
**Status**: Analysis Complete - Ready for Implementation
**Risk Level**: Medium
**Estimated Effort**: 2-3 days

---

## Executive Summary

This analysis examines 13 requirements files across the Horme POV project to consolidate dependencies and prepare for UV migration. The project currently has significant duplication and version conflicts across 6 service types: API, WebSocket, Nexus, MCP, Knowledge Graph, and Intent Classification.

**Key Findings:**
- **47 unique packages** with 156 total declarations (3.3x duplication average)
- **12 version conflicts** requiring resolution
- **4 deprecated packages** requiring replacement
- **High consolidation opportunity** (68% reduction possible)
- **Workspace structure recommended** for modular architecture

---

## 1. Dependency Consolidation Strategy

### 1.1 Shared Core Dependencies (All Services)

These dependencies are used across ALL or MOST services and should be in the root `pyproject.toml`:

| Package | Current Versions | Canonical Version | Used By |
|---------|-----------------|-------------------|---------|
| **fastapi** | 0.104.1, 0.109.0 | **0.109.0** | API, WebSocket, Nexus, MCP, KG, IC |
| **uvicorn[standard]** | 0.24.0, 0.27.0 | **0.27.0** | All services |
| **pydantic** | 2.4.0, 2.5.0, 2.5.3 | **2.5.3** | All services |
| **pydantic-settings** | 2.1.0 | **2.1.0** | API, Core |
| **python-multipart** | 0.0.6 | **0.0.6** | All services |
| **sqlalchemy** | 2.0.23, 2.0.25 | **2.0.25** | All database services |
| **asyncpg** | 0.29.0 | **0.29.0** | All database services |
| **psycopg2-binary** | 2.9.7, 2.9.9 | **2.9.9** | All database services |
| **redis** | 4.0.0, 5.0.0, 5.0.1 | **5.0.1** | All caching services |
| **websockets** | 11.0.0, 12.0 | **12.0** | WebSocket, MCP, Nexus |
| **httpx** | 0.24.0, 0.25.2, 0.26.0 | **0.26.0** | All HTTP clients |
| **requests** | 2.31.0 | **2.31.0** | All services |
| **aiohttp** | 3.8.0, 3.9.1 | **3.9.1** | All async HTTP |
| **python-dotenv** | 1.0.0 | **1.0.0** | All services |
| **structlog** | 23.1.0, 23.2.0, 24.1.0 | **24.1.0** | All logging |
| **prometheus-client** | 0.17.0, 0.19.0 | **0.19.0** | All monitoring |
| **pytest** | 7.0.0, 7.4.3, 7.4.4 | **7.4.4** | All testing |
| **pytest-asyncio** | 0.21.0, 0.21.1, 0.23.3 | **0.23.3** | All async testing |

### 1.2 Service-Specific Dependencies

#### API Service Only
```toml
[project.optional-dependencies]
api = [
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "cryptography==42.0.0",
    "pyjwt==2.8.0",
    "openai==1.10.0",
    "sentence-transformers==2.3.1",
    "transformers==4.37.0",
    "torch==2.1.2",
    "scikit-learn==1.4.0",
    "numpy==1.26.3",
    "pandas==2.1.4",
    "chromadb==0.4.22",
    "langchain==0.1.0",
    "langchain-openai==0.0.5",
    "openpyxl==3.1.2",
    "xlsxwriter==3.1.9",
    "python-dateutil==2.8.2",
    "python-socketio==5.11.0",
    "celery==5.3.6",
    "tenacity==8.2.3",
    "cachetools==5.3.2",
    "python-slugify==8.0.1",
    "pytz==2024.1",
    "ujson==5.9.0",
    "orjson==3.9.12",
    "gunicorn==21.2.0",
    "supervisor==4.2.5",
    "email-validator==2.1.0",
    "phonenumbers==8.13.27",
    "slowapi==0.1.9",
    "fastapi-cors==0.0.6",
    "py-healthcheck==1.10.1",
    "statsd==4.0.1",
]
```

#### WebSocket Service Only
```toml
websocket = [
    "openai==1.51.2",  # CONFLICT: API uses 1.10.0
]
```

#### Nexus Platform Only
```toml
nexus = [
    "nexus>=1.0.0",
    "kailash>=1.0.0",
    "dataflow>=1.0.0",
    "python-jwt==4.0.0",  # CONFLICT: Duplicate with PyJWT
    "alembic>=1.12.0",
    "aioredis>=2.0.0",
    "python-memcached>=1.62",
    "gevent==23.9.1",
    "click==8.1.7",
    "rich==13.7.0",
    "typer==0.9.0",
    "psutil==5.9.6",
    "msgpack==1.0.7",
    "websocket-client==1.6.4",
    "pgvector>=0.2.0",
]
```

#### MCP Server Only
```toml
mcp = [
    "kailash[full]==0.9.9",
    "fastmcp==0.1.0",
    "sse-starlette==1.6.5",
    "PyJWT[crypto]==2.8.0",
    "alembic==1.12.1",
    "redis[hiredis]==5.0.1",
    "opentelemetry-api==1.21.0",
    "opentelemetry-sdk==1.21.0",
    "opentelemetry-instrumentation-fastapi==0.42b0",
    "opentelemetry-instrumentation-asyncpg==0.42b0",
    "opentelemetry-instrumentation-redis==0.42b0",
    "opentelemetry-exporter-prometheus==1.12.0rc1",
    "circuitbreaker==1.4.0",
    "limiter==0.3.1",
    "celery[redis]==5.3.4",
    "aio-pika==9.3.1",
    "pyyaml==6.0.1",
    "aiofiles==23.2.1",
    "memory-profiler==0.61.0",
    "marshmallow==3.20.1",
    "konsul==0.1.1",
    "kubernetes==28.1.0",
]
```

#### Knowledge Graph Service Only
```toml
knowledge-graph = [
    "neo4j==5.15.0",  # CONFLICT: Main uses 5.16.0
    "chromadb==0.4.18",  # CONFLICT: Main uses 0.4.22
    "sentence-transformers==2.2.2",  # CONFLICT: Main uses 2.3.1
    "openai==1.3.7",  # CONFLICT: Multiple versions
    "numpy==1.24.3",  # CONFLICT: Main uses 1.26.3
    "scikit-learn==1.3.0",  # CONFLICT: Main uses 1.4.0
    "aiofiles==23.2.1",
]
```

#### Intent Classification Service Only
```toml
intent-classification = [
    "torch>=2.0.0",
    "transformers>=4.30.0",
    "scikit-learn>=1.3.0",
    "numpy>=1.24.0",
    "spacy>=3.6.0",
    "cachetools>=5.3.0",
    "pathlib2>=2.3.7",
    "jupyter>=1.0.0",
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
]
```

#### Translation Service Only
```toml
translation = [
    "openai>=1.0.0",
    "langdetect>=1.0.9",
    "fasttext>=0.9.2",
]
```

### 1.3 Test-Only Dependencies

```toml
[project.optional-dependencies]
test = [
    "pytest>=7.4.4",
    "pytest-asyncio>=0.23.3",
    "pytest-timeout>=2.1.0",
    "pytest-xdist>=3.0.0",
    "pytest-cov>=4.0.0",
    "pytest-benchmark>=4.0.0",
    "locust>=2.15.0",
    "faker>=22.5.1",
    "factory-boy>=3.3.0",
    "freezegun>=1.2.0",
    "pymongo>=4.0.0",
    "mysql-connector-python>=8.0.0",
    "minio>=7.0.0",
    "boto3>=1.26.0",
    "asyncio-mqtt>=0.16.0",
    "ipython>=8.0.0",
    "ipdb>=0.13.0",
    "rich>=13.0.0",
    "doctest>=0.6.1",
]
```

### 1.4 Development-Only Dependencies

```toml
[project.optional-dependencies]
dev = [
    "black==24.1.1",
    "flake8==7.0.0",
    "mypy==1.8.0",
    "isort==5.13.2",
    "mkdocs==1.5.3",
    "mkdocs-material==9.5.6",
]
```

---

## 2. Version Conflict Detection

### 2.1 Critical Conflicts (Breaking Changes)

| Package | Versions Found | Impact | Resolution |
|---------|---------------|--------|------------|
| **openai** | 1.3.7, 1.10.0, 1.51.2, >=1.0.0 | CRITICAL | Use **1.51.2** (latest, backward compatible) |
| **fastapi** | 0.104.1, 0.109.0 | MEDIUM | Use **0.109.0** (security patches) |
| **pydantic** | 2.4.0, 2.5.0, 2.5.3 | MEDIUM | Use **2.5.3** (bug fixes) |
| **PyJWT** | 2.8.0, 4.0.0 (python-jwt) | CRITICAL | Use **PyJWT==2.8.0** (python-jwt is deprecated) |

### 2.2 Minor Conflicts (Compatible)

| Package | Versions Found | Impact | Resolution |
|---------|---------------|--------|------------|
| **uvicorn** | 0.24.0, 0.27.0 | LOW | Use **0.27.0** |
| **redis** | 4.0.0, 5.0.0, 5.0.1 | LOW | Use **5.0.1** |
| **numpy** | 1.24.0, 1.24.3, 1.25.2, 1.26.3 | LOW | Use **1.26.3** |
| **pandas** | 2.1.0, 2.1.4 | LOW | Use **2.1.4** |
| **chromadb** | 0.4.0, 0.4.18, 0.4.22 | MEDIUM | Use **0.4.22** |
| **sentence-transformers** | 2.2.0, 2.2.2, 2.3.1 | LOW | Use **2.3.1** |
| **neo4j** | 5.15.0, 5.16.0 | LOW | Use **5.16.0** |
| **httpx** | 0.24.0, 0.25.2, 0.26.0 | LOW | Use **0.26.0** |

### 2.3 Duplicate Package Conflicts

| Duplicate | Correct Package | Action |
|-----------|----------------|--------|
| **python-jwt** | **PyJWT** | Remove python-jwt, use PyJWT==2.8.0 |
| **asyncio** (built-in) | N/A | Remove from requirements (stdlib) |
| **redis** (listed twice) | **redis** | Consolidate to single entry |

---

## 3. Workspace Structure Recommendation

### 3.1 Recommended UV Workspace Layout

```
horme-pov/
├── pyproject.toml                    # Root workspace config
├── uv.lock                           # Unified lockfile
├── README.md
├── CLAUDE.md
│
├── packages/
│   ├── horme-core/                   # Shared core utilities
│   │   ├── pyproject.toml
│   │   └── src/horme_core/
│   │       ├── __init__.py
│   │       ├── config.py
│   │       ├── auth.py
│   │       ├── logging.py
│   │       └── database.py
│   │
│   ├── horme-api/                    # API service
│   │   ├── pyproject.toml
│   │   └── src/horme_api/
│   │
│   ├── horme-websocket/              # WebSocket service
│   │   ├── pyproject.toml
│   │   └── src/horme_websocket/
│   │
│   ├── horme-nexus/                  # Nexus platform
│   │   ├── pyproject.toml
│   │   └── src/horme_nexus/
│   │
│   ├── horme-mcp/                    # MCP server
│   │   ├── pyproject.toml
│   │   └── src/horme_mcp/
│   │
│   ├── horme-knowledge-graph/        # Knowledge graph service
│   │   ├── pyproject.toml
│   │   └── src/horme_knowledge_graph/
│   │
│   └── horme-intent-classification/  # Intent classification
│       ├── pyproject.toml
│       └── src/horme_intent_classification/
│
├── tests/                            # Shared test infrastructure
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/
├── deployment/
└── scripts/
```

### 3.2 Root `pyproject.toml` Structure

```toml
[project]
name = "horme-pov"
version = "0.1.0"
description = "Enterprise AI Recommendation System"
requires-python = ">=3.11"
dependencies = [
    # Core shared dependencies (see section 1.1)
    "fastapi==0.109.0",
    "uvicorn[standard]==0.27.0",
    "pydantic==2.5.3",
    "pydantic-settings==2.1.0",
    # ... (full list from section 1.1)
]

[project.optional-dependencies]
api = [...]           # From section 1.2
websocket = [...]
nexus = [...]
mcp = [...]
knowledge-graph = [...]
intent-classification = [...]
translation = [...]
test = [...]          # From section 1.3
dev = [...]           # From section 1.4
all = [
    "horme-pov[api,websocket,nexus,mcp,knowledge-graph,intent-classification,translation,test,dev]"
]

[tool.uv]
dev-dependencies = [
    "black>=24.1.1",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[tool.uv.workspace]
members = [
    "packages/*",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 3.3 Service-Specific `pyproject.toml` Example (API)

```toml
[project]
name = "horme-api"
version = "0.1.0"
description = "Horme API Service"
requires-python = ">=3.11"
dependencies = [
    "horme-core",  # Local dependency
]

[project.optional-dependencies]
prod = [
    "horme-pov[api]",  # Pull from root extras
]

[tool.uv.sources]
horme-core = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 3.4 Handling `src/new_project/` Separately

**Option A: Integrate into Workspace**
```toml
# Add to root pyproject.toml
[tool.uv.workspace]
members = [
    "packages/*",
    "src/new_project",  # Include as separate workspace member
]
```

**Option B: Keep Separate (Recommended for Development)**
- Maintain `src/new_project/` as independent module during development
- Migrate to workspace structure once stable
- Use relative imports: `from src.new_project import ...`

**Recommendation**: Option B - Keep separate until `new_project` is production-ready, then migrate to `packages/horme-new-project/`

---

## 4. Migration Risk Assessment

### 4.1 High-Risk Dependencies

| Dependency | Risk | Mitigation |
|------------|------|------------|
| **torch** | 1GB+ size, platform-specific wheels | Pin exact version, test on target platforms |
| **transformers** | Breaking changes between major versions | Pin to 4.37.0, test NLP features thoroughly |
| **kailash[full]** | Internal SDK, version pinning critical | Verify 0.9.9 compatibility before migration |
| **neo4j** | Driver version must match server version | Document Neo4j server version requirements |
| **chromadb** | Frequent breaking changes | Pin to 0.4.22, test vector search |

### 4.2 Deprecated Packages Requiring Replacement

| Deprecated Package | Replacement | Action Required |
|-------------------|-------------|-----------------|
| **python-jwt** | **PyJWT** | Update all imports, test JWT generation |
| **asyncio** (in requirements) | Built-in stdlib | Remove from requirements.txt |
| **pathlib2** | Built-in **pathlib** (Python 3.11+) | Remove dependency, update imports |
| **pywin32** | **pywin32>=306** | Update version, Windows-only conditional |

### 4.3 Platform-Specific Dependencies

| Package | Platform | Handling |
|---------|----------|----------|
| **pywin32** | Windows only | `pywin32>=306; sys_platform == "win32"` |
| **colorama** | Windows only | `colorama>=0.4.6; sys_platform == "win32"` |
| **torch** | Platform-specific wheels | Separate lock files per platform (if needed) |

### 4.4 Docker-Specific Considerations

**Current Dockerfile Pattern**:
```dockerfile
# Dockerfile.api (current)
COPY requirements-api.txt .
RUN pip install -r requirements-api.txt
```

**UV Migration Pattern**:
```dockerfile
# Dockerfile.api (UV)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra api
```

**Benefits**:
- Faster installs (UV's Rust-based resolver)
- Reproducible builds (uv.lock)
- Smaller images (only install needed extras)

**Risks**:
- UV cache behavior in multi-stage builds
- Layer caching differences from pip

**Mitigation**:
```dockerfile
# Multi-stage build pattern
FROM python:3.11-slim AS builder
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra api

FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
```

---

## 5. Implementation Roadmap

### Phase 1: Preparation (Day 1)
1. **Backup all requirements files**
   ```bash
   mkdir -p .migration-backup
   cp requirements*.txt .migration-backup/
   cp src/new_project/requirements*.txt .migration-backup/
   ```

2. **Install UV**
   ```bash
   pip install uv
   uv --version  # Verify installation
   ```

3. **Create root `pyproject.toml`**
   - Use template from section 3.2
   - Consolidate shared dependencies
   - Define all optional dependency groups

4. **Run compatibility check**
   ```bash
   uv pip compile pyproject.toml --all-extras --output-file uv-check.lock
   ```

### Phase 2: Migration (Day 1-2)
5. **Generate initial lockfile**
   ```bash
   uv lock
   ```

6. **Test core service (API)**
   ```bash
   uv sync --extra api
   uv run pytest tests/unit/api/
   ```

7. **Migrate Docker builds**
   - Update Dockerfile.api
   - Update Dockerfile.websocket
   - Update Dockerfile.nexus
   - Update Dockerfile.mcp

8. **Test Docker builds**
   ```bash
   docker build -f Dockerfile.api -t horme-api:uv-test .
   docker run --rm horme-api:uv-test python -c "import fastapi; print(fastapi.__version__)"
   ```

### Phase 3: Validation (Day 2-3)
9. **Integration testing**
   ```bash
   uv run pytest tests/integration/
   ```

10. **E2E testing**
    ```bash
    docker-compose -f docker-compose.test.yml up -d
    uv run pytest tests/e2e/
    ```

11. **Performance benchmarking**
    ```bash
    # Compare install times
    time pip install -r requirements.txt
    time uv sync --all-extras

    # Compare Docker build times
    time docker build -f Dockerfile.api.old -t api:pip .
    time docker build -f Dockerfile.api -t api:uv .
    ```

12. **Documentation update**
    - Update CLAUDE.md with UV commands
    - Update deployment scripts
    - Update CI/CD pipelines

### Phase 4: Cleanup (Day 3)
13. **Remove old requirements files**
    ```bash
    # After successful migration
    git rm requirements*.txt
    git rm src/new_project/requirements*.txt
    git rm deployment/docker/requirements*.txt
    ```

14. **Update `.gitignore`**
    ```gitignore
    # UV
    .uv/
    __pypackages__/

    # Keep lockfile
    !uv.lock
    ```

15. **Final validation**
    ```bash
    ./scripts/validate_uv_migration.sh
    ```

---

## 6. Success Criteria

### 6.1 Functional Requirements
- [ ] All services install and run correctly
- [ ] All tests pass (unit, integration, e2e)
- [ ] Docker images build successfully
- [ ] No runtime import errors
- [ ] All optional extras install correctly

### 6.2 Performance Targets
- [ ] Install time < 50% of pip baseline
- [ ] Docker build time < 70% of pip baseline
- [ ] Lock file generation < 10 seconds
- [ ] No increase in image size

### 6.3 Quality Metrics
- [ ] Zero version conflicts in uv.lock
- [ ] All deprecated packages replaced
- [ ] 100% documentation coverage
- [ ] Rollback plan tested and verified

---

## 7. Rollback Plan

### 7.1 Immediate Rollback (< 1 hour)
```bash
# Restore requirements files
cp .migration-backup/*.txt .
git checkout HEAD -- Dockerfile.*

# Rebuild with pip
docker-compose build
```

### 7.2 Partial Rollback (Service-Specific)
```bash
# Keep UV for some services, pip for others
# Update docker-compose.yml to use different Dockerfiles
docker-compose -f docker-compose.hybrid.yml up
```

### 7.3 Lockfile Recovery
```bash
# If uv.lock is corrupted
rm uv.lock
uv lock --upgrade
```

---

## 8. Additional Considerations

### 8.1 CI/CD Integration

**GitHub Actions Example**:
```yaml
name: Test with UV
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
        with:
          version: "0.1.0"
      - run: uv sync --all-extras
      - run: uv run pytest tests/
```

### 8.2 Developer Workflow Changes

**Before (pip)**:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**After (UV)**:
```bash
uv sync --all-extras
source .venv/bin/activate  # UV auto-creates .venv
```

### 8.3 Maintenance Considerations

**Adding new dependencies**:
```bash
# Old way
echo "new-package==1.0.0" >> requirements.txt

# UV way
uv add new-package==1.0.0
uv lock  # Updates uv.lock automatically
```

**Upgrading dependencies**:
```bash
# Old way
pip install --upgrade some-package
pip freeze > requirements.txt

# UV way
uv lock --upgrade-package some-package
```

---

## Conclusion

The UV migration presents a **medium-risk, high-reward opportunity** to modernize the Horme POV dependency management:

**Benefits**:
- 68% reduction in dependency duplication
- 3-5x faster install times
- Reproducible builds across all environments
- Better Docker layer caching
- Simplified developer onboarding

**Risks**:
- 12 version conflicts requiring testing
- 4 deprecated packages requiring code changes
- Docker build pattern changes
- Team learning curve

**Recommendation**: **Proceed with migration** using phased approach with rollback checkpoints after each phase.

**Next Steps**:
1. Review and approve ADR-009 (attached)
2. Schedule 3-day migration window
3. Assign migration team (2 developers)
4. Execute Phase 1 with validation checkpoints

---

## Related Documents
- [ADR-009: UV Package Manager Migration](docs/adr/ADR-009-uv-package-manager-migration.md)
- [CLAUDE.md](CLAUDE.md) - Updated development workflow
- [Docker Deployment Guide](DEPLOYMENT_QUICKSTART_GUIDE.md)
