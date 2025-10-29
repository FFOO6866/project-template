# ADR-009: UV Package Manager Migration

## Status
**Proposed** - Pending Approval

## Context

### Current State
The Horme POV project currently uses pip and requirements.txt files for dependency management across 6 distinct services:
- API Server (FastAPI)
- WebSocket Server
- Nexus Platform
- MCP Server
- Knowledge Graph Service
- Intent Classification Service

**Problems with Current Approach:**

1. **Massive Dependency Duplication** (156 declarations for 47 unique packages)
   - Average 3.3x duplication across requirements files
   - Maintenance nightmare: updating a package requires changes in 3-4 files
   - High risk of version drift between services

2. **12 Critical Version Conflicts**
   - OpenAI SDK: 4 different versions (1.3.7, 1.10.0, 1.51.2, >=1.0.0)
   - FastAPI: 2 versions (0.104.1, 0.109.0)
   - PyJWT: Conflicting packages (PyJWT vs python-jwt)
   - Core libraries (pydantic, redis, numpy) with multiple versions

3. **No Reproducible Builds**
   - No lockfile mechanism
   - `pip freeze` output is not portable
   - Different environments produce different installations
   - Docker builds are non-deterministic

4. **Slow Installation Times**
   - Average 5-8 minutes for full dependency install
   - Poor Docker layer caching
   - Redundant dependency resolution on every install

5. **Deprecated Packages**
   - `python-jwt` (should be PyJWT)
   - `asyncio` (stdlib, shouldn't be in requirements)
   - `pathlib2` (stdlib in Python 3.11+)

6. **Poor Developer Experience**
   - Complex onboarding (6+ requirements files to understand)
   - Manual virtual environment management
   - No clear dependency graph
   - Difficult to debug dependency conflicts

### Why UV?

**UV** is a next-generation Python package manager written in Rust by Astral (creators of Ruff):

**Performance Benefits:**
- 10-100x faster than pip for dependency resolution
- 2-5x faster installation times
- Efficient caching and parallel downloads

**Reliability Benefits:**
- Universal lockfile (uv.lock) for reproducible builds
- Cross-platform compatibility
- Conflict detection during lock file generation

**Developer Experience Benefits:**
- Automatic virtual environment management
- Workspace support for monorepo structures
- PEP 621 compliant (modern pyproject.toml)
- Drop-in pip replacement (`uv pip install`)

**Enterprise Benefits:**
- Better security auditing (lockfile with hashes)
- Faster CI/CD pipelines
- Smaller Docker images
- Easier dependency governance

### Constraints

1. **Backward Compatibility**: Must maintain compatibility with existing Docker infrastructure
2. **Team Learning Curve**: 5-person team needs to learn UV commands
3. **CI/CD Integration**: GitHub Actions and GitLab CI must be updated
4. **Migration Timeline**: Cannot exceed 3-day window
5. **Zero Downtime**: Services must remain available during migration
6. **Rollback Plan**: Must be able to revert to pip within 1 hour

---

## Decision

We will migrate from pip + requirements.txt to UV + pyproject.toml using a **workspace-based monorepo structure**.

### Architecture

```
horme-pov/
├── pyproject.toml              # Root workspace configuration
├── uv.lock                     # Universal lockfile (committed)
│
├── packages/
│   ├── horme-core/             # Shared utilities
│   ├── horme-api/              # API service
│   ├── horme-websocket/        # WebSocket service
│   ├── horme-nexus/            # Nexus platform
│   ├── horme-mcp/              # MCP server
│   ├── horme-knowledge-graph/  # Knowledge graph
│   └── horme-intent-classification/
│
├── tests/                      # Shared test suite
├── deployment/                 # Docker + K8s configs
└── docs/
```

### Core Principles

1. **Single Source of Truth**
   - Root `pyproject.toml` defines all shared dependencies
   - Service-specific dependencies in service `pyproject.toml`
   - Single `uv.lock` for entire workspace

2. **Optional Dependencies for Services**
   ```toml
   [project.optional-dependencies]
   api = ["openai==1.51.2", "torch==2.1.2", ...]
   websocket = [...]
   nexus = [...]
   all = ["horme-pov[api,websocket,nexus,...]"]
   ```

3. **Docker-First Development**
   - UV integrated into all Dockerfiles
   - Multi-stage builds for minimal image size
   - Cache optimization with `uv cache`

4. **Gradual Migration**
   - Phase 1: Core dependencies + API service
   - Phase 2: WebSocket + Nexus services
   - Phase 3: MCP + ML services
   - Phase 4: Cleanup + documentation

### Version Resolution Strategy

| Package | Current Conflicts | Canonical Version | Rationale |
|---------|------------------|-------------------|-----------|
| **openai** | 1.3.7, 1.10.0, 1.51.2 | **1.51.2** | Latest stable, backward compatible API |
| **fastapi** | 0.104.1, 0.109.0 | **0.109.0** | Security patches, minor version bump |
| **pydantic** | 2.4.0, 2.5.0, 2.5.3 | **2.5.3** | Bug fixes, no breaking changes |
| **PyJWT** | PyJWT 2.8.0, python-jwt 4.0.0 | **PyJWT==2.8.0** | python-jwt is deprecated |
| **redis** | 4.0.0, 5.0.0, 5.0.1 | **5.0.1** | Latest stable, async support |
| **numpy** | 1.24.0, 1.25.2, 1.26.3 | **1.26.3** | Python 3.11 wheel support |

### Example Root `pyproject.toml`

```toml
[project]
name = "horme-pov"
version = "0.1.0"
description = "Enterprise AI Recommendation System"
requires-python = ">=3.11"
authors = [
    {name = "Horme Team", email = "dev@horme.example"}
]
readme = "README.md"
license = {text = "Proprietary"}

dependencies = [
    # Core Web Framework (All Services)
    "fastapi==0.109.0",
    "uvicorn[standard]==0.27.0",
    "python-multipart==0.0.6",
    "pydantic==2.5.3",
    "pydantic-settings==2.1.0",

    # Database - PostgreSQL (All DB Services)
    "asyncpg==0.29.0",
    "psycopg2-binary==2.9.9",
    "sqlalchemy==2.0.25",
    "alembic==1.13.1",

    # Cache - Redis (All Caching Services)
    "redis==5.0.1",
    "hiredis==2.3.2",

    # HTTP & Networking (All Services)
    "httpx==0.26.0",
    "requests==2.31.0",
    "aiohttp==3.9.1",
    "websockets==12.0",

    # Configuration (All Services)
    "python-dotenv==1.0.0",
    "pyyaml==6.0.1",

    # Logging & Monitoring (All Services)
    "structlog==24.1.0",
    "prometheus-client==0.19.0",

    # Security (Core)
    "cryptography==42.0.0",
]

[project.optional-dependencies]
# Production API Server
api = [
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "pyjwt==2.8.0",
    "openai==1.51.2",
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

# WebSocket Server
websocket = [
    "openai==1.51.2",
]

# Nexus Platform
nexus = [
    "nexus>=1.0.0",
    "kailash>=1.0.0",
    "dataflow>=1.0.0",
    "pyjwt==2.8.0",
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

# MCP Server
mcp = [
    "kailash[full]==0.9.9",
    "fastmcp==0.1.0",
    "sse-starlette==1.6.5",
    "pyjwt[crypto]==2.8.0",
    "opentelemetry-api==1.21.0",
    "opentelemetry-sdk==1.21.0",
    "opentelemetry-instrumentation-fastapi==0.42b0",
    "circuitbreaker==1.4.0",
    "limiter==0.3.1",
    "celery[redis]==5.3.4",
    "aio-pika==9.3.1",
    "aiofiles==23.2.1",
    "marshmallow==3.20.1",
    "kubernetes==28.1.0",
]

# Knowledge Graph Service
knowledge-graph = [
    "neo4j==5.16.0",
    "chromadb==0.4.22",
    "sentence-transformers==2.3.1",
    "openai==1.51.2",
    "numpy==1.26.3",
    "scikit-learn==1.4.0",
    "aiofiles==23.2.1",
]

# Intent Classification Service
intent-classification = [
    "torch==2.1.2",
    "transformers==4.37.0",
    "scikit-learn==1.4.0",
    "numpy==1.26.3",
    "spacy>=3.6.0",
    "cachetools==5.3.2",
    "jupyter>=1.0.0",
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
]

# Translation Service
translation = [
    "openai==1.51.2",
    "langdetect>=1.0.9",
    "fasttext>=0.9.2",
]

# Testing Infrastructure
test = [
    "pytest==7.4.4",
    "pytest-asyncio==0.23.3",
    "pytest-timeout>=2.1.0",
    "pytest-xdist>=3.0.0",
    "pytest-cov>=4.0.0",
    "pytest-benchmark>=4.0.0",
    "locust>=2.15.0",
    "faker==22.5.1",
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
]

# Development Tools
dev = [
    "black==24.1.1",
    "ruff>=0.1.0",
    "mypy==1.8.0",
    "isort==5.13.2",
    "mkdocs==1.5.3",
    "mkdocs-material==9.5.6",
]

# Install everything
all = [
    "horme-pov[api,websocket,nexus,mcp,knowledge-graph,intent-classification,translation,test,dev]"
]

[tool.uv]
dev-dependencies = [
    "ruff>=0.1.0",
]

[tool.uv.workspace]
members = [
    "packages/*",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Docker Integration Pattern

**Before (pip)**:
```dockerfile
# Dockerfile.api (OLD)
FROM python:3.11-slim
WORKDIR /app
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt
COPY . .
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0"]
```

**After (UV)**:
```dockerfile
# Dockerfile.api (NEW)
FROM python:3.11-slim AS builder

# Install UV
RUN pip install --no-cache-dir uv

# Copy dependency files
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install dependencies (frozen lockfile, production only, API extras)
RUN uv sync --frozen --no-dev --extra api

# Production stage
FROM python:3.11-slim

# Copy installed packages from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
WORKDIR /app
COPY . .

# Use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Run application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Benefits of UV Docker Pattern:**
- Smaller final image (no build tools)
- Faster builds (cached dependency layer)
- Reproducible (frozen lockfile)
- Secure (only production dependencies)

---

## Consequences

### Positive Consequences

1. **68% Reduction in Dependency Duplication**
   - From 156 declarations to 50 unique entries
   - Single source of truth for versions
   - Easier maintenance and upgrades

2. **3-5x Faster Installation Times**
   - UV benchmark: 10-100x faster dependency resolution
   - Parallel downloads and installs
   - Efficient caching mechanism
   - **Expected**: 5-8 min → 1-2 min install time

3. **Reproducible Builds Across All Environments**
   - `uv.lock` with exact versions and hashes
   - Cross-platform compatibility
   - Deterministic Docker builds
   - Eliminates "works on my machine" issues

4. **Better Developer Experience**
   - Automatic virtual environment management
   - Clear dependency graph (`uv tree`)
   - Faster onboarding (single command: `uv sync`)
   - Better error messages for conflicts

5. **Enhanced Security Posture**
   - Lockfile with SHA256 hashes
   - Easy audit trail for dependencies
   - Vulnerability scanning integration
   - Clear dependency provenance

6. **Improved CI/CD Performance**
   - Faster GitHub Actions workflows
   - Better cache hit rates
   - Parallel test execution
   - Reduced cloud costs (faster builds)

7. **Modern Python Packaging Standards**
   - PEP 621 compliant (pyproject.toml)
   - Better ecosystem compatibility
   - Future-proof architecture
   - Industry best practices

### Negative Consequences

1. **Team Learning Curve**
   - New commands to learn (`uv sync`, `uv add`, `uv lock`)
   - Different mental model from pip
   - Documentation needs updating
   - **Mitigation**:
     - UV is pip-compatible (`uv pip install` works)
     - Comprehensive migration guide
     - Team training session (2 hours)
     - Cheat sheet for common commands

2. **Migration Effort Required**
   - 13 requirements files to consolidate
   - Docker build patterns to update
   - CI/CD pipeline changes
   - **Estimated effort**: 2-3 developer-days
   - **Mitigation**: Phased migration with rollback points

3. **Initial Stability Risk**
   - UV is relatively new (v0.1.x)
   - Potential edge cases with complex dependencies
   - Less mature ecosystem than pip
   - **Mitigation**:
     - Extensive testing before rollout
     - Keep pip as fallback option
     - Gradual service migration
     - Rollback plan ready

4. **Docker Build Pattern Changes**
   - Different layer caching behavior
   - New multi-stage build patterns
   - Potential image size changes (initially)
   - **Mitigation**:
     - Benchmark before/after
     - Optimize layer ordering
     - Document best practices

5. **Lockfile Merge Conflicts**
   - `uv.lock` is large JSON file
   - Git merge conflicts likely
   - **Mitigation**:
     - Use `uv lock --upgrade` after merge
     - Document conflict resolution process
     - Consider branch protection rules

6. **Tooling Compatibility**
   - Some IDE integrations may lag
   - Third-party tools expect requirements.txt
   - Vulnerability scanners may need updating
   - **Mitigation**:
     - UV can export to requirements.txt format
     - Most tools now support pyproject.toml
     - Document workarounds

### Technical Debt Addressed

1. **Eliminates Version Drift**
   - Single canonical version for each package
   - Workspace ensures consistency
   - Lockfile prevents accidental upgrades

2. **Removes Deprecated Packages**
   - python-jwt → PyJWT
   - asyncio (stdlib, not needed)
   - pathlib2 (stdlib in Python 3.11+)

3. **Centralizes Configuration**
   - All metadata in pyproject.toml
   - No more scattered config files
   - PEP 621 standard compliance

---

## Alternatives Considered

### Alternative 1: Poetry

**Pros:**
- Mature ecosystem (5+ years)
- Good workspace support
- Excellent dependency resolver

**Cons:**
- Slow dependency resolution (5-10 min)
- Large lockfile (poetry.lock)
- Heavier tooling footprint
- Custom build backend (complexity)

**Rejected because**: Performance is critical for CI/CD and developer productivity. Poetry's slow resolver is a known pain point.

### Alternative 2: PDM

**Pros:**
- PEP 621 compliant
- Good performance
- Modern architecture

**Cons:**
- Smaller community
- Less Docker integration examples
- Fewer enterprise adoptions
- Learning curve similar to Poetry

**Rejected because**: UV has better performance benchmarks and stronger momentum in the ecosystem (Astral backing).

### Alternative 3: Pip + pip-tools

**Pros:**
- Familiar to team
- Widely used and stable
- Good IDE support

**Cons:**
- Still slow compared to UV
- Requires manual requirements.in/out management
- No workspace support
- No automatic venv management

**Rejected because**: Doesn't solve core problems (duplication, speed, reproducibility). Incremental improvement only.

### Alternative 4: Keep Current Pip Setup

**Pros:**
- Zero migration effort
- No learning curve
- Known behavior

**Cons:**
- All current problems remain
- Technical debt accumulates
- Slower CI/CD
- Poor developer experience

**Rejected because**: Status quo is not sustainable. Version conflicts and duplication are causing real problems.

---

## Implementation Plan

### Phase 1: Foundation (Day 1, Hours 1-4)

**Goals**: Set up UV infrastructure and test with core service

1. **Install UV globally**
   ```bash
   pip install uv
   uv --version
   ```

2. **Backup existing requirements**
   ```bash
   mkdir -p .migration-backup/$(date +%Y%m%d)
   cp requirements*.txt .migration-backup/$(date +%Y%m%d)/
   cp src/*/requirements*.txt .migration-backup/$(date +%Y%m%d)/
   ```

3. **Create root `pyproject.toml`**
   - Use template from this ADR
   - Consolidate shared dependencies
   - Define all optional dependency groups
   - Resolve version conflicts

4. **Generate lockfile**
   ```bash
   uv lock
   # Expected: ~10 seconds for full resolution
   ```

5. **Test API service locally**
   ```bash
   uv sync --extra api
   uv run pytest tests/unit/api/
   uv run python -m src.api.main  # Smoke test
   ```

6. **Update Dockerfile.api**
   - Implement multi-stage build pattern
   - Test Docker build
   - Compare image size (before/after)

**Success Criteria**:
- [ ] uv.lock generated successfully
- [ ] API service installs and runs
- [ ] All API unit tests pass
- [ ] Docker image builds and runs

### Phase 2: Service Migration (Day 1-2, Hours 5-12)

**Goals**: Migrate remaining services

7. **WebSocket Service**
   ```bash
   uv sync --extra websocket
   uv run pytest tests/unit/websocket/
   docker build -f Dockerfile.websocket -t horme-websocket:uv-test .
   ```

8. **Nexus Platform**
   ```bash
   uv sync --extra nexus
   uv run pytest tests/unit/nexus/
   docker build -f Dockerfile.nexus -t horme-nexus:uv-test .
   ```

9. **MCP Server**
   ```bash
   uv sync --extra mcp
   uv run pytest tests/unit/mcp/
   docker build -f Dockerfile.mcp -t horme-mcp:uv-test .
   ```

10. **ML Services (Knowledge Graph + Intent Classification)**
    ```bash
    uv sync --extra knowledge-graph --extra intent-classification
    uv run pytest tests/unit/knowledge_graph/ tests/unit/intent_classification/
    ```

**Success Criteria**:
- [ ] All services install successfully
- [ ] All unit tests pass
- [ ] All Docker images build
- [ ] No import errors

### Phase 3: Integration Testing (Day 2, Hours 13-18)

**Goals**: Verify services work together

11. **Integration tests**
    ```bash
    uv sync --all-extras
    uv run pytest tests/integration/
    ```

12. **Docker Compose testing**
    ```bash
    docker-compose -f docker-compose.test.yml build
    docker-compose -f docker-compose.test.yml up -d
    uv run pytest tests/e2e/
    docker-compose -f docker-compose.test.yml down
    ```

13. **Performance benchmarking**
    ```bash
    # Install time comparison
    time pip install -r requirements.txt  # Baseline
    time uv sync --all-extras             # UV

    # Docker build time comparison
    time docker build -f Dockerfile.api.old -t api:pip .
    time docker build -f Dockerfile.api -t api:uv .

    # Expected: 40-60% time reduction
    ```

14. **Load testing (if time permits)**
    ```bash
    uv run locust -f tests/performance/locustfile.py --host http://localhost:8000
    ```

**Success Criteria**:
- [ ] All integration tests pass
- [ ] E2E tests pass
- [ ] Performance metrics meet targets
- [ ] No regression in functionality

### Phase 4: Documentation & Rollout (Day 3, Hours 19-24)

**Goals**: Update documentation and prepare for team rollout

15. **Update CLAUDE.md**
    ```markdown
    ## UV Package Manager (New)

    ### Installation
    uv sync --all-extras

    ### Adding dependencies
    uv add package-name

    ### Running tests
    uv run pytest tests/

    ### Docker development
    docker-compose up  # Now uses UV
    ```

16. **Update deployment scripts**
    ```bash
    # deploy-docker.bat
    - Replace pip install with uv sync
    - Update health checks
    - Add UV cache management
    ```

17. **Update CI/CD pipelines**
    ```yaml
    # .github/workflows/test.yml
    - name: Setup UV
      uses: astral-sh/setup-uv@v1
    - name: Install dependencies
      run: uv sync --all-extras
    - name: Run tests
      run: uv run pytest tests/
    ```

18. **Create migration guide**
    - Common tasks cheat sheet
    - Troubleshooting guide
    - Rollback procedures
    - FAQ section

19. **Team training**
    - 2-hour workshop
    - Live demo of common workflows
    - Q&A session
    - Hands-on practice

20. **Remove old requirements files**
    ```bash
    # After successful validation
    git rm requirements*.txt
    git rm src/*/requirements*.txt
    git rm deployment/docker/requirements*.txt

    git commit -m "feat: Migrate from pip to UV package manager

    - Consolidate 13 requirements files into single pyproject.toml
    - Resolve 12 version conflicts
    - Remove 4 deprecated packages
    - Add workspace structure for monorepo
    - Update all Dockerfiles to use UV
    - Update CI/CD pipelines
    - 68% reduction in dependency duplication
    - 3-5x faster installation times

    See ADR-009 for full rationale and implementation details"
    ```

**Success Criteria**:
- [ ] All documentation updated
- [ ] Team trained and onboarded
- [ ] CI/CD pipelines working
- [ ] Old files removed from repo
- [ ] Migration guide published

---

## Monitoring & Success Metrics

### Key Performance Indicators (KPIs)

1. **Installation Speed**
   - **Baseline (pip)**: 5-8 minutes
   - **Target (UV)**: < 2 minutes
   - **Measurement**: CI/CD pipeline duration

2. **Docker Build Speed**
   - **Baseline**: 10-15 minutes (full build)
   - **Target**: < 7 minutes
   - **Measurement**: Docker build time logs

3. **Image Size**
   - **Baseline**: 1.8-2.2 GB (API image)
   - **Target**: < 1.8 GB (multi-stage build optimization)
   - **Measurement**: `docker images` output

4. **Developer Onboarding Time**
   - **Baseline**: 30-45 minutes (manual setup)
   - **Target**: < 10 minutes (automated setup)
   - **Measurement**: New developer survey

5. **Dependency Conflicts**
   - **Baseline**: 12 known conflicts
   - **Target**: 0 conflicts
   - **Measurement**: `uv lock` success rate

### Validation Checklist

**Functional Requirements**:
- [ ] All services install and run
- [ ] All tests pass (unit, integration, e2e)
- [ ] Docker images build successfully
- [ ] No runtime import errors
- [ ] All optional extras install correctly

**Performance Requirements**:
- [ ] Install time < 50% of pip baseline
- [ ] Docker build time < 70% of pip baseline
- [ ] Lock file generation < 10 seconds
- [ ] No increase in image size (or < 5%)

**Quality Requirements**:
- [ ] Zero version conflicts in uv.lock
- [ ] All deprecated packages replaced
- [ ] 100% documentation coverage
- [ ] Rollback plan tested and verified

**Operational Requirements**:
- [ ] CI/CD pipelines working
- [ ] Monitoring dashboards updated
- [ ] Team trained on UV commands
- [ ] Troubleshooting guide published

---

## Rollback Plan

### Immediate Rollback (< 1 hour)

**Trigger Conditions**:
- Critical service failure
- Unresolvable dependency conflicts
- Docker build failures
- Team consensus to abort

**Rollback Procedure**:
```bash
# 1. Restore requirements files
cp .migration-backup/$(date +%Y%m%d)/*.txt .
git checkout HEAD -- Dockerfile.*

# 2. Rebuild Docker images
docker-compose build

# 3. Restart services
docker-compose up -d

# 4. Validate health
./scripts/health-check.sh

# 5. Notify team
echo "Rollback complete. Using pip requirements.txt"
```

**Expected Duration**: 30-60 minutes

### Partial Rollback (Service-Specific)

If only specific services have issues:

```bash
# Keep UV for working services, revert problematic ones
# Example: Revert MCP service only

# Dockerfile.mcp (revert to pip)
git checkout HEAD -- Dockerfile.mcp deployment/docker/requirements-mcp-production.txt

# Rebuild only MCP
docker-compose build horme-mcp
docker-compose up -d horme-mcp
```

### Lockfile Recovery

If `uv.lock` becomes corrupted:

```bash
# Delete corrupted lockfile
rm uv.lock

# Regenerate from pyproject.toml
uv lock

# Validate
uv sync --all-extras
uv run pytest tests/unit/
```

---

## Risk Mitigation

### Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Version conflicts during migration** | Medium | High | Pre-validate with `uv lock --dry-run`, test each service independently |
| **Docker build failures** | Low | High | Multi-stage builds with fallback, comprehensive testing before rollout |
| **Team resistance to change** | Medium | Medium | Training session, cheat sheet, UV is pip-compatible (`uv pip`) |
| **CI/CD pipeline breakage** | Low | High | Test in separate branch, parallel pip/UV workflows during transition |
| **Lockfile merge conflicts** | High | Low | Document resolution process, use `uv lock --upgrade` after merge |
| **Third-party tool incompatibility** | Low | Medium | UV can export requirements.txt, most tools support pyproject.toml |
| **Performance regression** | Very Low | Medium | Benchmark before/after, UV is faster in all scenarios |
| **Dependency installation failures** | Low | High | UV has better error messages, fallback to pip if needed |

### Pre-Migration Validation

```bash
# 1. Dry-run lockfile generation
uv lock --dry-run

# 2. Validate all extras
uv sync --all-extras --dry-run

# 3. Check for conflicts
uv tree --conflicts

# 4. Export to requirements.txt for comparison
uv pip compile pyproject.toml --all-extras -o uv-generated.txt
diff requirements.txt uv-generated.txt

# 5. Test in isolated environment
docker build -f Dockerfile.api.uv-test -t api:uv-validation .
docker run --rm api:uv-validation python -c "import fastapi; import openai; print('OK')"
```

---

## Future Enhancements

### Post-Migration Improvements

1. **Dependency Scanning**
   - Integrate `uv audit` for vulnerability scanning
   - Automate dependency updates with Dependabot
   - Track dependency licenses

2. **Workspace Optimization**
   - Move `src/new_project/` into workspace
   - Create shared `horme-core` package
   - Optimize cross-package dependencies

3. **Advanced Caching**
   - UV cache server for team
   - Docker layer optimization
   - CI/CD cache strategies

4. **Tooling Integration**
   - Pre-commit hooks for lockfile validation
   - IDE integration improvements
   - Custom UV plugins

---

## References

### Documentation
- [UV Official Documentation](https://github.com/astral-sh/uv)
- [PEP 621 - Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- [UV Migration Guide](https://github.com/astral-sh/uv/blob/main/docs/guides/migrate-from-pip.md)

### Related ADRs
- [ADR-003: Docker Consolidation](ADR-003-docker-consolidation.md)
- [ADR-004: Production Deployment](ADR-004-production-deployment.md)
- [ADR-002: Testing Strategy](ADR-002-testing-strategy.md)

### Related Documents
- [UV Migration Analysis Report](../../UV_MIGRATION_ANALYSIS.md)
- [CLAUDE.md](../../CLAUDE.md)
- [Docker Deployment Guide](../../DEPLOYMENT_QUICKSTART_GUIDE.md)

---

## Approval

**Decision Date**: 2025-10-18
**Review Date**: 2025-11-18 (30 days post-migration)
**Approved By**: [Pending]

**Stakeholders**:
- [ ] Tech Lead
- [ ] DevOps Lead
- [ ] Backend Team
- [ ] QA Team

**Next Steps**:
1. Review this ADR with stakeholders
2. Schedule 3-day migration window
3. Assign migration team (2 developers)
4. Execute Phase 1 with validation checkpoints
5. Document learnings and update this ADR

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Status**: Proposed
