# Phase 1: Foundation & Infrastructure

**Created:** 2025-01-10
**Completed:** 2025-11-10
**Priority:** 🔥 HIGH
**Status:** ✅ COMPLETE (100%)
**Actual Effort:** ~6 hours (UV migration made this much faster!)
**Target Completion:** End of Week 1 ✅

---

## 🎯 Phase Objectives

1. Set up complete development environment
2. Configure Docker and docker-compose infrastructure
3. Establish project structure following Python best practices
4. Configure all development tools (testing, linting, migrations)
5. Ensure deployment pipeline is ready
6. **CRITICAL**: All configuration from .env, no hardcoding

---

## ✅ Acceptance Criteria

- [x] .env file with all required variables (including OPENAI_API_KEY)
- [x] docker-compose up successfully starts all services
- [x] All services healthy and responding (API, PostgreSQL, Redis, Celery Worker, Celery Beat)
- [x] Python package structure follows best practices
- [x] Tests can be run with pytest (configured in pyproject.toml)
- [x] Code linting and formatting configured (black, isort, flake8, mypy, bandit)
- [x] Database migrations framework ready (Alembic)
- [x] Local deployment tested end-to-end
- [x] Documentation updated and harmonized (UV_SETUP.md, MIGRATION_TO_UV.md)

---

## 📋 Tasks Breakdown

### 1. Environment Configuration (COMPLETED ✅)

#### 1.1 Environment Files
- [x] **Create .env file** with all variables
  - OpenAI API key: `OPENAI_API_KEY=sk-proj-brP97...`
  - Database credentials
  - Redis password
  - JWT secrets
  - Server details (IP, PEM key path)
  - All feature flags

- [x] **Create .env.example** template
  - Same structure as .env
  - Placeholder values for secrets
  - Clear comments and instructions

- [x] **Create .gitignore**
  - Exclude .env from Git
  - Exclude *.pem keys
  - Exclude Python cache files
  - Exclude data files (too large)

**Verification:**
```bash
# Check .env exists and has required vars
grep OPENAI_API_KEY .env
grep ENVIRONMENT .env
grep DATABASE_URL .env
```

---

#### 1.2 Docker Configuration
- [x] **Create docker-compose.yml**
  - PostgreSQL service with pgvector extension
  - Redis service with password auth
  - FastAPI service (reads all env vars from .env)
  - Celery worker service
  - Celery beat scheduler
  - All services use .env automatically (NO manual env var insertion)

**Services Defined:**
```yaml
- postgres (PostgreSQL 15)
- redis (Redis 7)
- api (FastAPI application)
- celery-worker (background tasks)
- celery-beat (scheduler)
```

- [x] **Verify docker-compose structure**
  - All environment variables loaded from .env
  - Health checks configured
  - Dependencies defined correctly
  - Volumes for persistence

**Verification:**
```bash
# Validate docker-compose configuration
docker-compose config
```

---

#### 1.3 Deployment Documentation
- [x] **Create DEPLOYMENT_AGENT.md**
  - Complete deployment procedures
  - Local → Git → Server workflow
  - Troubleshooting for common issues
  - Environment variable debugging
  - Special section for OPENAI_API_KEY issues
  - All commands documented

- [x] **Create DEPLOYMENT_QUICK_START.md**
  - Quick reference guide
  - Common commands
  - Checklists

- [x] **Create deployment script**
  - `scripts/deploy.sh` for automated deployment
  - Supports both local and server deployment
  - Validates environment before deploying

**Verification:**
```bash
# Make script executable
chmod +x scripts/deploy.sh

# Test script validation
./scripts/deploy.sh local --dry-run
```

---

### 2. Docker Testing (CURRENT TASK 🔄)

#### 2.1 Local Docker Deployment Test
- [ ] **Test docker-compose up**
  ```bash
  cd /path/to/job_pricing
  docker-compose up -d
  ```

- [ ] **Verify all services start**
  ```bash
  docker-compose ps
  # Expected: All services "Up (healthy)"
  ```

- [ ] **Check PostgreSQL**
  ```bash
  docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db -c "SELECT 1;"
  ```

- [ ] **Check Redis**
  ```bash
  docker-compose exec redis redis-cli -a $REDIS_PASSWORD ping
  # Expected: PONG
  ```

- [ ] **Check API (when implemented)**
  ```bash
  curl http://localhost:8000/health
  # Expected: {"status": "healthy"}
  ```

- [ ] **Verify OPENAI_API_KEY loaded**
  ```bash
  docker-compose exec api env | grep OPENAI_API_KEY
  # Expected: OPENAI_API_KEY=sk-proj-brP97...
  ```

- [ ] **Check environment is development**
  ```bash
  docker-compose exec api env | grep ENVIRONMENT
  # Expected: ENVIRONMENT=development
  ```

**Common Issues:**
- If services don't start: Check `docker-compose logs [service]`
- If OPENAI_API_KEY not set: Verify .env file exists
- If ports conflict: Stop conflicting services

---

### 3. Python Project Structure (NEXT TASK 🎯)

#### 3.1 Directory Structure
- [ ] **Create Python package structure**
  ```
  src/job_pricing/
  ├── __init__.py
  ├── api/                    # FastAPI endpoints
  │   ├── __init__.py
  │   ├── main.py
  │   ├── dependencies.py
  │   └── v1/
  │       ├── job_pricing.py
  │       ├── mercer.py
  │       └── skills.py
  ├── core/                   # Core business logic
  │   ├── __init__.py
  │   ├── config.py          # Load from .env
  │   ├── security.py
  │   └── database.py
  ├── models/                 # SQLAlchemy models
  │   ├── __init__.py
  │   ├── job_request.py
  │   └── pricing_result.py
  ├── schemas/                # Pydantic schemas
  │   ├── __init__.py
  │   └── job_pricing.py
  ├── services/               # Business logic
  │   ├── __init__.py
  │   └── job_pricing_service.py
  ├── workflows/              # Kailash workflows
  │   ├── __init__.py
  │   └── pricing_workflow.py
  ├── repositories/           # Data access
  │   ├── __init__.py
  │   └── job_pricing_repository.py
  └── utils/
      ├── __init__.py
      └── formatting.py
  ```

**Action:**
```bash
# Create structure
mkdir -p src/job_pricing/{api/{v1},core,models,schemas,services,workflows,repositories,utils}
touch src/job_pricing/__init__.py
# ... create all __init__.py files
```

---

#### 3.2 Dependencies Management
- [ ] **Create requirements.txt**
  ```txt
  # Web Framework
  fastapi==0.104.1
  uvicorn[standard]==0.24.0
  pydantic==2.5.0
  pydantic-settings==2.1.0

  # Database
  sqlalchemy==2.0.23
  psycopg2-binary==2.9.9
  alembic==1.12.1
  asyncpg==0.29.0

  # Redis
  redis==5.0.1

  # Kailash SDK
  kailash==<version>

  # AI/ML
  openai==1.3.0
  tiktoken==0.5.1

  # Task Queue
  celery==5.3.4

  # Web Scraping
  selenium==4.15.0
  beautifulsoup4==4.12.2

  # Data Processing
  pandas==2.1.3
  openpyxl==3.1.2
  numpy==1.26.2

  # Authentication
  python-jose[cryptography]==3.3.0
  passlib[bcrypt]==1.7.4
  python-multipart==0.0.6

  # Utilities
  python-dotenv==1.0.0
  httpx==0.25.1

  # Testing
  pytest==7.4.3
  pytest-asyncio==0.21.1
  pytest-cov==4.1.0
  faker==20.0.3

  # Code Quality
  black==23.11.0
  flake8==6.1.0
  mypy==1.7.0
  ```

- [ ] **Create requirements-dev.txt**
  ```txt
  -r requirements.txt

  # Development Tools
  ipython==8.17.2
  ipdb==0.13.13

  # Documentation
  mkdocs==1.5.3
  mkdocs-material==9.4.14
  ```

- [ ] **Set up virtual environment**
  ```bash
  python -m venv venv
  source venv/bin/activate  # Linux/Mac
  # OR
  venv\Scripts\activate  # Windows

  pip install -r requirements.txt
  ```

**Verification:**
```bash
# Test imports
python -c "import fastapi; import sqlalchemy; import openai; print('✓ All core packages installed')"
```

---

#### 3.3 Configuration Management
- [ ] **Create core/config.py**
  - Load ALL settings from .env
  - NO hardcoded values
  - Use pydantic-settings for validation
  - Fail fast if required variables missing

**Template:**
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str
    DEBUG: bool = False

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20

    # OpenAI - CRITICAL
    OPENAI_API_KEY: str
    OPENAI_MODEL_DEFAULT: str = "gpt-4"

    # Redis
    REDIS_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()
```

- [ ] **Test configuration loading**
  ```python
  from core.config import get_settings
  settings = get_settings()
  assert settings.OPENAI_API_KEY.startswith("sk-")
  assert settings.ENVIRONMENT in ["development", "production"]
  ```

---

### 4. Development Tools Setup

#### 4.1 Database Migrations (Alembic)
- [ ] **Initialize Alembic**
  ```bash
  alembic init alembic
  ```

- [ ] **Configure alembic/env.py**
  - Load DATABASE_URL from config (not hardcoded)
  - Import all SQLAlchemy models
  - Support async migrations

- [ ] **Configure alembic.ini**
  - Remove hardcoded database URL
  - Use configuration from env

- [ ] **Create initial migration**
  ```bash
  # Will be done in Phase 2 after models are created
  # alembic revision --autogenerate -m "Initial schema"
  ```

**Verification:**
```bash
# Test migrations work
alembic current
alembic history
```

---

#### 4.2 Testing Framework (pytest)
- [ ] **Create pytest.ini**
  ```ini
  [pytest]
  testpaths = tests
  python_files = test_*.py
  python_classes = Test*
  python_functions = test_*
  addopts =
      --verbose
      --color=yes
      --cov=src/job_pricing
      --cov-report=html
      --cov-report=term-missing
  ```

- [ ] **Create tests/ directory structure**
  ```
  tests/
  ├── __init__.py
  ├── conftest.py        # Shared fixtures
  ├── unit/
  │   ├── test_config.py
  │   └── test_models.py
  ├── integration/
  │   ├── test_database.py
  │   └── test_api.py
  └── e2e/
      └── test_pricing_workflow.py
  ```

- [ ] **Create tests/conftest.py** with fixtures
  - Database test fixtures
  - API client fixtures
  - Mock data factories

- [ ] **Write first test**
  ```python
  # tests/unit/test_config.py
  def test_config_loads_from_env():
      from core.config import get_settings
      settings = get_settings()
      assert settings.OPENAI_API_KEY is not None
      assert len(settings.OPENAI_API_KEY) > 0
  ```

**Verification:**
```bash
# Run tests
pytest tests/unit/test_config.py -v
```

---

#### 4.3 Code Quality Tools
- [ ] **Configure Black** (formatter)
  - Create pyproject.toml
  - Line length: 100
  - Target Python 3.11+

  ```toml
  [tool.black]
  line-length = 100
  target-version = ['py311']
  include = '\.pyi?$'
  extend-exclude = '''
  /(
    \.git
    | \.venv
    | build
    | dist
  )/
  '''
  ```

- [ ] **Configure Flake8** (linter)
  - Create .flake8
  ```ini
  [flake8]
  max-line-length = 100
  extend-ignore = E203, W503
  exclude = .git,__pycache__,venv,.venv
  ```

- [ ] **Configure mypy** (type checker)
  ```toml
  [tool.mypy]
  python_version = "3.11"
  warn_return_any = true
  warn_unused_configs = true
  disallow_untyped_defs = true
  ```

- [ ] **Create .pre-commit-config.yaml**
  ```yaml
  repos:
    - repo: https://github.com/psf/black
      rev: 23.11.0
      hooks:
        - id: black

    - repo: https://github.com/pycqa/flake8
      rev: 6.1.0
      hooks:
        - id: flake8

    - repo: https://github.com/pre-commit/mirrors-mypy
      rev: v1.7.0
      hooks:
        - id: mypy
  ```

- [ ] **Install pre-commit hooks**
  ```bash
  pip install pre-commit
  pre-commit install
  pre-commit run --all-files
  ```

**Verification:**
```bash
# Test formatting
black --check src/

# Test linting
flake8 src/

# Test type checking
mypy src/
```

---

#### 4.4 Dockerfile Creation
- [ ] **Create Dockerfile**
  ```dockerfile
  FROM python:3.11-slim

  WORKDIR /app

  # Install system dependencies
  RUN apt-get update && apt-get install -y \
      gcc \
      postgresql-client \
      curl \
      && rm -rf /var/lib/apt/lists/*

  # Copy requirements
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  # Copy application code
  COPY src/ src/
  COPY alembic/ alembic/
  COPY alembic.ini .

  # Create data directories
  RUN mkdir -p /app/data /app/logs

  # Health check
  HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

  # Run application
  CMD ["uvicorn", "src.job_pricing.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- [ ] **Create .dockerignore**
  ```
  .env
  .git
  .venv
  venv
  __pycache__
  *.pyc
  *.pyo
  *.pyd
  .pytest_cache
  .coverage
  htmlcov
  *.log
  .DS_Store
  ```

- [ ] **Test Docker build**
  ```bash
  docker build -t job-pricing-api:dev .
  ```

- [ ] **Test Docker run (standalone)**
  ```bash
  docker run --env-file .env -p 8000:8000 job-pricing-api:dev
  ```

**Verification:**
```bash
# Check image size
docker images | grep job-pricing-api

# Check image layers
docker history job-pricing-api:dev
```

---

## 🔍 Testing & Validation

### Phase 1 Completion Checklist

- [ ] **Environment Configuration**
  - [ ] .env file has all required variables
  - [ ] .env.example template is accurate
  - [ ] .gitignore excludes sensitive files
  - [ ] Environment variables validated with tests

- [ ] **Docker Infrastructure**
  - [ ] docker-compose up starts all services
  - [ ] PostgreSQL accessible and healthy
  - [ ] Redis accessible and healthy
  - [ ] API service builds successfully
  - [ ] All services can communicate

- [ ] **Python Project**
  - [ ] Package structure created
  - [ ] Dependencies installed
  - [ ] Configuration loads from .env
  - [ ] No hardcoded values anywhere

- [ ] **Development Tools**
  - [ ] Alembic initialized
  - [ ] pytest runs successfully
  - [ ] pre-commit hooks installed
  - [ ] Code quality tools configured

- [ ] **Docker Build**
  - [ ] Dockerfile builds successfully
  - [ ] Image size reasonable (<1GB)
  - [ ] Container runs with .env

- [ ] **Documentation**
  - [ ] README.md updated
  - [ ] DEPLOYMENT_AGENT.md reviewed
  - [ ] All commands tested

---

## 🚨 Common Issues & Solutions

### Issue 1: OPENAI_API_KEY not found
**Symptoms:** API fails with "OpenAI API key not set"
**Solution:**
```bash
grep OPENAI_API_KEY .env
# If missing, add:
echo "OPENAI_API_KEY=sk-proj-brP97..." >> .env
docker-compose down && docker-compose up -d
```

### Issue 2: Docker services won't start
**Symptoms:** docker-compose ps shows "Exited"
**Solution:**
```bash
docker-compose logs [service_name]
# Check for errors in logs
# Common: port conflicts, missing .env
```

### Issue 3: Python imports not working
**Symptoms:** ModuleNotFoundError
**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Install in editable mode
pip install -e .
```

### Issue 4: Database connection fails
**Symptoms:** "could not connect to server"
**Solution:**
```bash
# Check postgres is running
docker-compose ps postgres

# Verify DATABASE_URL in .env
grep DATABASE_URL .env

# Test connection
docker-compose exec postgres psql -U job_pricing_user -d job_pricing_db
```

---

## 📝 Progress Log

**2025-01-10:**
- ✅ Created all environment configuration files
- ✅ Created docker-compose.yml with all services
- ✅ Created comprehensive DEPLOYMENT_AGENT.md
- ✅ Created deployment scripts
- ✅ Updated .gitignore
- 🔄 Next: Test docker-compose deployment

---

## 🎯 Next Phase

Once Phase 1 is complete, proceed to:
**Phase 2: Database & Data Models** (`active/002-phase2-database.md`)

This will involve:
- Creating all 19 database tables
- Implementing SQLAlchemy ORM models
- Setting up pgvector for embeddings
- Creating migration scripts
