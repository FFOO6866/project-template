# Horme POV Development Environment

## 🐳 Docker-First Development Policy

### CRITICAL: All Development Must Use Docker
**This project runs EXCLUSIVELY in Docker containers. No local/host development is permitted.**

## 🖥️ VM Production Deployment

### VM Requirements
- **CPU**: 2+ cores (4+ recommended for production)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 20GB minimum (50GB+ recommended)
- **OS**: Ubuntu 20.04+ LTS, CentOS 8+, or equivalent
- **Network**: Internet connectivity for Docker image pulls

### VM Security Hardening
```bash
# Run security hardening script
sudo ./scripts/vm-security-hardening.sh

# Validate VM requirements
./scripts/vm-requirements-check.sh
```

### VM Production Quick Start
```bash
# 1. Prepare VM environment
sudo ./scripts/vm-security-hardening.sh

# 2. Deploy production stack
./deploy-vm-production.sh

# 3. Validate deployment
./scripts/validate-vm-deployment.sh
```

### Quick Start
```bash
# Windows
.\verify-docker-setup.ps1          # Verify Docker is ready
.\deploy-docker.bat full            # Build and start all services

# Linux/Mac
./deploy-docker.sh full             # Build and start all services
```

### Service Access

#### Development Environment
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **MCP Server**: ws://localhost:3002
- **Nexus Platform**: http://localhost:8080
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6380

#### VM Production Environment
- **Frontend**: https://your-domain.com
- **API**: https://your-domain.com/api
- **MCP Server**: wss://your-domain.com/ws
- **PostgreSQL**: VM-IP:5433 (secured)
- **Redis**: VM-IP:6380 (secured)
- **Monitoring**: https://your-domain.com/grafana

### Development Workflow
1. **NEVER install dependencies locally** - All dependencies are in containers
2. **NEVER run Python/Node directly** - Use docker-compose exec
3. **ALWAYS use Docker volumes** for code changes (hot reload enabled)
4. **ALWAYS test in containers** - No local testing

### Container Commands
```bash
# View logs
.\deploy-docker.bat logs [service]

# Enter container shell
docker exec -it horme-api /bin/bash

# Run Python commands in container
docker exec horme-api python -m src.some_module

# Run tests in container
docker exec horme-api pytest tests/

# Database operations
docker exec horme-postgres psql -U horme_user -d horme_db
```

## 🏗️ Architecture Overview

### Core SDK (`src/kailash/`)
**Foundational building blocks** for workflow automation:
- **Purpose**: Custom workflows, fine-grained control, integrations
- **Components**: WorkflowBuilder, LocalRuntime, 110+ nodes, MCP integration
- **Usage**: Direct workflow construction with full programmatic control
- **Container**: Included in API and MCP server images

### DataFlow (`sdk-users/apps/dataflow/`)
**Zero-config database framework** built on Core SDK:
- **Purpose**: Database operations with automatic model-to-node generation
- **Features**: @db.model decorator generates 9 nodes per model automatically. DataFlow IS NOT AN ORM!
- **Usage**: Database-first applications with enterprise features
- **Container**: `horme-dataflow` service

### Nexus (`sdk-users/apps/nexus/`)
**Multi-channel platform** built on Core SDK:
- **Purpose**: Deploy workflows as API + CLI + MCP simultaneously
- **Features**: Unified sessions, zero-config platform deployment
- **Usage**: Platform applications requiring multiple access methods
- **Container**: `horme-nexus` service

### Critical Relationships
- **All services run in isolated containers** with network communication
- **PostgreSQL and Redis** are shared between all services via Docker network
- **No direct file system access** - Use Docker volumes for persistence

## 🎯 Specialized Subagents

### Docker & Infrastructure
- **docker-specialist** → Container optimization, multi-stage builds, health checks
- **compose-specialist** → Docker Compose orchestration, networking, volumes

### Analysis & Planning
- **ultrathink-analyst** → Deep failure analysis, complexity assessment
- **requirements-analyst** → Requirements breakdown, ADR creation
- **sdk-navigator** → Find patterns before coding, resolve errors during development
- **framework-advisor** → Choose Core SDK, DataFlow, or Nexus; coordinates with specialists

### Framework Implementation
- **nexus-specialist** → Multi-channel platform implementation (API/CLI/MCP)
- **dataflow-specialist** → Database operations with auto-generated nodes (PostgreSQL-only alpha)

### Core Implementation  
- **pattern-expert** → Workflow patterns, nodes, parameters
- **tdd-implementer** → Test-first development
- **intermediate-reviewer** → Review after todos and implementation
- **gold-standards-validator** → Compliance checking

### Testing & Validation
- **testing-specialist** → 3-tier strategy with real infrastructure in containers
- **documentation-validator** → Test code examples, ensure accuracy

### Release & Operations
- **todo-manager** → Task management and project tracking
- **mcp-specialist** → MCP server implementation and integration
- **git-release-specialist** → Git workflows, CI validation, releases

## ⚡ Essential Pattern (All Frameworks)
```python
# This code runs INSIDE containers, not on host
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

workflow = WorkflowBuilder()
workflow.add_node("NodeName", "id", {"param": "value"})  # String-based
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())  # ALWAYS .build()
```

## 🚨 Emergency Fixes

### Docker Issues
- **Container not starting** → Check `.\deploy-docker.bat logs [service]`
- **Port conflicts** → Check ports in `.env.production`, use alternative ports
- **Database connection failed** → Ensure postgres container is healthy: `.\deploy-docker.bat health`
- **Code changes not reflecting** → Restart container: `docker-compose restart [service]`

### Application Issues
- **"Missing required inputs"** → Use sdk-navigator for common-mistakes.md solutions
- **Parameter issues** → Use pattern-expert for 3-method parameter guide
- **Test failures** → Use testing-specialist for real infrastructure setup in containers
- **DataFlow errors** → Use dataflow-specialist for PostgreSQL-specific debugging
- **Nexus platform issues** → Use nexus-specialist for multi-channel troubleshooting
- **Framework selection** → Use framework-advisor to coordinate appropriate specialists

## ⚠️ Critical Rules

### 🚨 PRODUCTION CODE QUALITY STANDARDS (ABSOLUTE REQUIREMENTS)

**These rules are MANDATORY and NON-NEGOTIABLE for all code contributions:**

#### 1. ❌ ZERO TOLERANCE FOR MOCK DATA
- **NEVER** return mock/fake/dummy data from any function
- **NEVER** use fallback data when real data is unavailable
- **NEVER** simulate responses - if service is down, fail gracefully with proper error
- **ALWAYS** query real databases, call real APIs, use real external services
- **VIOLATION EXAMPLES:**
  ```python
  # ❌ FORBIDDEN
  return [{'id': 'mock_001', 'name': 'Sample Product'}]
  return {'status': 'ok'}  # Without checking actual status
  if data is None: return FALLBACK_DATA  # NO FALLBACKS

  # ✅ REQUIRED
  data = await db.fetch("SELECT * FROM products WHERE id = $1", id)
  if not data:
      raise HTTPException(status_code=404, detail="Product not found")
  return data
  ```

#### 2. ❌ ZERO TOLERANCE FOR HARDCODING
- **NEVER** hardcode credentials, API keys, passwords, secrets
- **NEVER** hardcode URLs, connection strings, service endpoints
- **NEVER** hardcode configuration values
- **ALWAYS** use environment variables via `config` module
- **VIOLATION EXAMPLES:**
  ```python
  # ❌ FORBIDDEN
  redis_url = "redis://localhost:6379"
  password = "admin123"
  api_key = "sk-your-key-here"

  # ✅ REQUIRED
  from src.core.config import config
  redis_url = config.REDIS_URL
  password = config.DATABASE_PASSWORD
  api_key = config.OPENAI_API_KEY
  ```

#### 3. ❌ ZERO TOLERANCE FOR SIMULATED/FALLBACK DATA
- **NEVER** provide default/fallback responses when real service fails
- **NEVER** catch exceptions and return fake success responses
- **ALWAYS** let errors propagate to proper error handlers
- **ALWAYS** return real errors to clients (properly formatted)
- **VIOLATION EXAMPLES:**
  ```python
  # ❌ FORBIDDEN
  try:
      result = await openai_service.classify(query)
  except:
      result = {'intent': 'general', 'confidence': 0.5}  # FAKE FALLBACK

  # ✅ REQUIRED
  try:
      result = await openai_service.classify(query)
  except OpenAIError as e:
      logger.error(f"OpenAI classification failed: {e}")
      raise HTTPException(status_code=503, detail="AI service unavailable")
  ```

#### 4. ✅ ALWAYS CHECK FOR EXISTING CODE
- **Before creating ANY new file**, search for existing implementations
- **Use `Glob` and `Grep` tools** to find related code
- **ENHANCE existing code** instead of creating duplicates
- **If similar code exists**, refactor and reuse instead of duplicating
- **REQUIRED WORKFLOW:**
  ```bash
  # 1. Search for existing implementations
  Glob: "**/*product*.py"
  Grep: "def.*search.*product" in src/

  # 2. If found, enhance existing code
  # 3. If not found, create new with proper placement
  ```

#### 5. 🧹 MANDATORY HOUSEKEEPING
- **ALWAYS** follow the established directory structure
- **ALWAYS** delete unused/deprecated files
- **ALWAYS** update imports when moving files
- **ALWAYS** maintain consistent naming conventions
- **DIRECTORY STRUCTURE:**
  ```
  src/
  ├── core/           # Config, auth, logging (shared)
  ├── repositories/   # Data access layer (DB queries)
  ├── services/       # Business logic layer
  ├── api/            # API endpoints and routes
  ├── models/         # Data models and schemas
  └── utils/          # Helper functions

  tests/
  ├── unit/           # Unit tests (isolated)
  ├── integration/    # Integration tests (real DB)
  └── e2e/            # End-to-end tests (full stack)
  ```

### 🔍 CODE REVIEW CHECKLIST (Required Before Commit)

Run these checks before ANY commit:

```bash
# 1. Search for mock data patterns
grep -r "mock\|fake\|dummy\|sample" src/ --include="*.py"
# ✅ Should return: ZERO results

# 2. Search for hardcoded credentials
grep -r "password.*=.*['\"]" src/ --include="*.py"
grep -r "localhost" src/production_*.py
# ✅ Should return: ZERO results

# 3. Search for fallback data
grep -r "fallback\|default.*return\|except.*return.*{" src/ --include="*.py"
# ✅ Should return: ZERO results (except proper error handling)

# 4. Search for TODO/FIXME comments
grep -r "TODO\|FIXME\|HACK" src/ --include="*.py"
# ✅ Should be addressed before commit

# 5. Validate configuration
uv run python scripts/validate_config.py
# ✅ Should pass all checks
```

### 🚫 ANTI-PATTERNS (Strictly Forbidden)

| Anti-Pattern | Why Forbidden | Correct Approach |
|--------------|---------------|------------------|
| Mock user validation | Security vulnerability | Real database auth check |
| Localhost URLs in prod code | Won't work in containers | Use service names or env vars |
| Try-except with fake returns | Hides real errors | Let errors propagate |
| Hardcoded admin passwords | Critical security flaw | Use bcrypt + database |
| `if not data: return []` | Hides missing data issues | `raise HTTPException(404)` |
| Duplicate repository classes | Code maintenance nightmare | Reuse existing repos |
| Mixed concerns in files | Difficult to test/maintain | Separate layers (repo/service/api) |

### Docker Rules
- **ALWAYS develop in containers** - No local Python/Node execution
- **NEVER commit .env files** - Use .env.production.template
- **ALWAYS use Docker networks** - No localhost connections between services
- **NEVER hardcode ports** - Use environment variables
- **ALWAYS include health checks** - Every service must have health endpoints
- **ALWAYS use UV** for Python dependency management in containers

### Application Rules
- ALWAYS: `runtime.execute(workflow.build())`
- NEVER: `workflow.execute(runtime)`
- String-based nodes: `workflow.add_node("NodeName", "id", {})`
- Real infrastructure: NO MOCKING in Tiers 2-3 tests (use test containers)

### 📖 Reference Documentation
See `PRODUCTION_READINESS_PLAN.md` for complete implementation guide

## 📁 Project Structure (Containerized)

```
horme-pov/
├── docker-compose.consolidated.yml  # Main orchestration file
├── .env.production                  # Environment configuration (DO NOT COMMIT)
├── deploy-docker.bat               # Windows deployment script
├── deploy-docker.sh                # Linux/Mac deployment script
├── verify-docker-setup.ps1         # Docker verification script
├── Dockerfile.api                  # API service container
├── Dockerfile.mcp-lightweight      # MCP server container
├── Dockerfile.nexus-backend        # Nexus platform container
├── Dockerfile.dataflow-import      # DataFlow service container
├── Dockerfile.horme-pipeline       # Enrichment pipeline container
├── fe-reference/
│   └── Dockerfile                  # Frontend container
├── src/                           # Application code (mounted as volume)
├── data/                          # Persistent data (Docker volumes)
└── logs/                          # Container logs (Docker volumes)
```

## 🚀 Deployment Profiles

### Default Profile
Basic services: PostgreSQL, Redis, API, MCP, Frontend

### Production Profile
Includes: Nginx reverse proxy with SSL termination

### Monitoring Profile
Includes: Prometheus, Grafana dashboards

### Admin Profile
Includes: PgAdmin for database management

### Usage
```bash
.\deploy-docker.bat start              # Default profile
.\deploy-docker.bat start production   # Production with Nginx
.\deploy-docker.bat start monitoring   # With metrics
.\deploy-docker.bat start all         # All profiles
```

## 📊 Container Resource Limits

Each service has defined resource limits:
- **API**: 1GB RAM, 0.5 CPU
- **MCP**: 1GB RAM, 0.5 CPU
- **Nexus**: 1GB RAM, 0.5 CPU
- **PostgreSQL**: 2GB RAM, 1.0 CPU
- **Redis**: 512MB RAM, 0.25 CPU
- **Frontend**: 512MB RAM, 0.25 CPU

## 🔒 Security in Containers

### Development Security
- All containers run as **non-root users**
- **Multi-stage builds** minimize attack surface
- **Health checks** ensure service availability
- **Isolated networks** prevent unauthorized access
- **Environment variables** for all secrets (never hardcoded)

### VM Production Security (Additional)
- **Container hardening**: Seccomp profiles, capability dropping, read-only filesystems
- **Network segmentation**: Multiple isolated networks with firewall rules
- **SSL/TLS termination**: Nginx with security headers and HSTS
- **Rate limiting**: DDoS protection and API throttling
- **Security monitoring**: Fail2ban, intrusion detection, log monitoring
- **Vulnerability scanning**: Regular container and OS security updates

## 📝 Important Notes

### Development Environment
1. **Windows Users**: Ensure Docker Desktop is running with WSL2 backend
2. **Port Mappings**: Alternative ports used to avoid Windows conflicts
3. **Volume Mounts**: Code is mounted read-only in production containers
4. **Hot Reload**: Enabled in development for Python and Node.js
5. **Database Migrations**: Run automatically on container startup

### VM Production Environment
1. **SSL Certificates**: Generate or obtain valid SSL certificates before deployment
2. **Domain Configuration**: Update DNS records to point to VM IP address
3. **Firewall Rules**: Configure VM firewall to allow necessary ports
4. **Backup Strategy**: Set up automated backups for database and volumes
5. **Monitoring Alerts**: Configure alerting for system health and security events
6. **Security Updates**: Enable automatic security updates for the host OS
7. **Log Rotation**: Configure log rotation to prevent disk space issues

## 🚨 VM Production Emergency Procedures

### Service Recovery
```bash
# Check service status
./scripts/health-check-vm.sh

# Restart failed services
docker-compose -f docker-compose.vm-production.yml restart [service]

# View service logs
docker-compose -f docker-compose.vm-production.yml logs -f [service]

# Database backup
./scripts/backup-database-vm.sh

# Full system restart
./deploy-vm-production.sh restart
```

### Security Incident Response
```bash
# Check for suspicious activity
sudo journalctl -f | grep -E "(WARN|ERROR|FAIL)"

# Review fail2ban status
sudo fail2ban-client status

# Check firewall rules
sudo ufw status verbose

# Isolate compromised service
docker-compose -f docker-compose.vm-production.yml stop [service]
```