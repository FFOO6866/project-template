# Horme POV Configuration Management

## Overview

Horme POV uses centralized configuration management through environment variables. **ALL configuration must be provided via environment variables** - no hardcoded values, no defaults for sensitive data, and no fallbacks that could hide misconfiguration.

This document provides a complete reference for all configuration variables.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Principles](#configuration-principles)
- [Required vs Optional Variables](#required-vs-optional-variables)
- [Configuration Categories](#configuration-categories)
  - [Environment & Application](#environment--application)
  - [Database (PostgreSQL)](#database-postgresql)
  - [Redis Cache](#redis-cache)
  - [Neo4j Knowledge Graph](#neo4j-knowledge-graph)
  - [Security & Authentication](#security--authentication)
  - [OpenAI API](#openai-api)
  - [Hybrid Recommendation Engine](#hybrid-recommendation-engine)
  - [Product Classification](#product-classification)
  - [API Configuration](#api-configuration)
  - [MCP Server](#mcp-server)
  - [WebSocket Chat Server](#websocket-chat-server)
  - [Web Scraping](#web-scraping)
  - [Feature Flags](#feature-flags)
  - [Monitoring & Observability](#monitoring--observability)
  - [Docker & Network](#docker--network)
- [Validation Rules](#validation-rules)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

1. **Copy the template**:
   ```bash
   cp .env.production.template .env.production
   ```

2. **Generate secrets**:
   ```bash
   # Application secrets (64 characters)
   openssl rand -hex 32 > SECRET_KEY
   openssl rand -hex 32 > JWT_SECRET
   openssl rand -hex 32 > ADMIN_PASSWORD

   # Database/service passwords (48 characters)
   openssl rand -hex 24 > POSTGRES_PASSWORD
   openssl rand -hex 24 > REDIS_PASSWORD
   openssl rand -hex 24 > NEO4J_PASSWORD
   ```

3. **Fill in required values** in `.env.production`

4. **Validate configuration**:
   ```bash
   python -c "from src.core.config import config; print('✅ Configuration valid')"
   ```

---

## Configuration Principles

### Fail-Fast Philosophy

Horme POV follows a **fail-fast** approach to configuration:

- ❌ **NO hardcoded defaults** for sensitive values
- ❌ **NO fallback values** that could hide misconfigurations
- ❌ **NO localhost in production** (enforced by validators)
- ✅ **FAIL immediately** if required config is missing
- ✅ **VALIDATE on startup** before accepting requests
- ✅ **CLEAR error messages** explaining what's missing

### Why Fail-Fast?

```python
# ❌ BAD: Silent failure with defaults
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
# App starts, but uses wrong Redis → data corruption

# ✅ GOOD: Immediate failure with clear error
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    raise ValueError(
        "CRITICAL: REDIS_URL not configured. "
        "Set REDIS_URL environment variable. "
        "Example: redis://:password@redis:6379/0"
    )
```

**Benefits:**
- Catch configuration errors during deployment, not in production
- No silent failures that corrupt data or skip security
- Clear error messages guide operators to fix issues
- Production deployments are guaranteed to be properly configured

---

## Required vs Optional Variables

### Required Variables (Production)

These variables **MUST** be set or the application will refuse to start:

```bash
# Environment
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/horme_db

# Redis
REDIS_URL=redis://:password@redis:6379/0

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<generated-secret>

# OpenAI
OPENAI_API_KEY=sk-proj-...

# Security
SECRET_KEY=<generated-secret>
JWT_SECRET=<generated-secret>
ADMIN_PASSWORD=<generated-secret>

# CORS
CORS_ORIGINS=https://app.example.com

# Hybrid Recommendation Engine (must sum to 1.0)
HYBRID_WEIGHT_COLLABORATIVE=0.25
HYBRID_WEIGHT_CONTENT_BASED=0.25
HYBRID_WEIGHT_KNOWLEDGE_GRAPH=0.30
HYBRID_WEIGHT_LLM_ANALYSIS=0.20
```

### Optional Variables

These have sensible defaults but can be overridden:

```bash
# Application
APP_NAME=horme-pov
DEBUG=false
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8002
API_WORKERS=4

# Features
ENABLE_AI_CLASSIFICATION=true
ENABLE_IMAGE_ANALYSIS=true
ENABLE_SEMANTIC_SEARCH=true
```

---

## Configuration Categories

### Environment & Application

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | **YES** | - | Environment type: `development`, `staging`, or `production` |
| `APP_NAME` | No | `horme-pov` | Application name |
| `DEBUG` | No | `false` | Debug mode (MUST be `false` in production) |
| `LOG_LEVEL` | No | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

**Validation:**
- `ENVIRONMENT` must be one of: `development`, `staging`, `production`
- `DEBUG` must be `false` in production
- `LOG_LEVEL` must be a valid logging level

**Example:**
```bash
ENVIRONMENT=production
APP_NAME=horme-pov
DEBUG=false
LOG_LEVEL=INFO
```

---

### Database (PostgreSQL)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | **YES** | - | PostgreSQL connection string |
| `POSTGRES_DB` | **YES** | - | Database name |
| `POSTGRES_USER` | **YES** | - | Database user |
| `POSTGRES_PASSWORD` | **YES** | - | Database password (32+ chars) |
| `POSTGRES_PORT` | No | `5434` | External port mapping |
| `DATABASE_POOL_SIZE` | No | `20` | Connection pool size (1-100) |
| `DATABASE_MAX_OVERFLOW` | No | `10` | Max overflow connections (0-50) |
| `DATABASE_POOL_TIMEOUT` | No | `30` | Pool timeout in seconds (5-300) |

**Validation:**
- `DATABASE_URL` must start with `postgresql://` or `postgres://`
- `DATABASE_URL` must include credentials (`user:password@host`)
- `DATABASE_URL` cannot contain `localhost` in production
- Password must be 32+ characters in production

**Docker Format (REQUIRED):**
```bash
# Use Docker service name 'postgres', internal port 5432
DATABASE_URL=postgresql://horme_user:SECRET_HERE@postgres:5432/horme_db
```

**Generate Password:**
```bash
openssl rand -hex 24
```

---

### Redis Cache

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | **YES** | - | Redis connection string |
| `REDIS_PASSWORD` | **YES** | - | Redis password (32+ chars) |
| `REDIS_PORT` | No | `6381` | External port mapping |
| `REDIS_MAX_CONNECTIONS` | No | `50` | Max connections (1-200) |
| `REDIS_SOCKET_TIMEOUT` | No | `5` | Socket timeout in seconds (1-30) |

**Validation:**
- `REDIS_URL` must start with `redis://`
- `REDIS_URL` cannot contain `localhost` in production
- Password must be 32+ characters in production

**Docker Format (REQUIRED):**
```bash
# Use Docker service name 'redis', internal port 6379
REDIS_URL=redis://:SECRET_HERE@redis:6379/0
```

**Generate Password:**
```bash
openssl rand -hex 24
```

---

### Neo4j Knowledge Graph

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEO4J_URI` | **YES** | - | Neo4j connection URI |
| `NEO4J_USER` | **YES** | - | Neo4j username |
| `NEO4J_PASSWORD` | **YES** | - | Neo4j password (32+ chars) |
| `NEO4J_DATABASE` | No | `neo4j` | Database name |

**Validation:**
- `NEO4J_URI` must start with `bolt://`, `neo4j://`, or `neo4j+s://`
- `NEO4J_URI` cannot contain `localhost` in production
- Password must be 32+ characters in production

**Docker Format (REQUIRED):**
```bash
# Use Docker service name 'neo4j', port 7687
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<generated-secret>
```

**Generate Password:**
```bash
openssl rand -hex 24
```

---

### Security & Authentication

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | **YES** | - | Application secret key (64+ chars) |
| `JWT_SECRET` | **YES** | - | JWT signing secret (64+ chars) |
| `ADMIN_PASSWORD` | **YES** | - | Admin password (64+ chars) |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `JWT_EXPIRATION_HOURS` | No | `24` | Token expiration (1-168 hours) |

**Validation:**
- Secrets must be 16+ characters minimum
- Secrets must be 32+ characters in production (64+ recommended)
- Secrets cannot be common weak values (`secret`, `password`, `admin`, `123456`, etc.)

**Generate Secrets:**
```bash
# Generate 64-character secrets (recommended)
openssl rand -hex 32  # SECRET_KEY
openssl rand -hex 32  # JWT_SECRET
openssl rand -hex 32  # ADMIN_PASSWORD
```

**Security Notes:**
- **NEVER** use the same secret for multiple purposes
- **ROTATE** secrets every 90 days minimum
- **STORE** secrets in a secure vault (AWS Secrets Manager, HashiCorp Vault)
- **NEVER** commit secrets to git

---

### OpenAI API

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | **YES** | - | OpenAI API key (starts with `sk-`) |
| `OPENAI_MODEL` | No | `gpt-4-turbo-preview` | Model to use |
| `OPENAI_MAX_TOKENS` | No | `2000` | Max tokens per request (100-4000) |
| `OPENAI_TEMPERATURE` | No | `0.1` | Model temperature (0.0-2.0) |

**Validation:**
- `OPENAI_API_KEY` must start with `sk-`
- `OPENAI_API_KEY` must be at least 20 characters

**Get API Key:**
1. Visit https://platform.openai.com/api-keys
2. Create new secret key
3. Copy and store securely

**Example:**
```bash
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_HERE
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.1
```

---

### Hybrid Recommendation Engine

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HYBRID_WEIGHT_COLLABORATIVE` | **YES** | - | Collaborative filtering weight (0.0-1.0) |
| `HYBRID_WEIGHT_CONTENT_BASED` | **YES** | - | Content-based filtering weight (0.0-1.0) |
| `HYBRID_WEIGHT_KNOWLEDGE_GRAPH` | **YES** | - | Knowledge graph weight (0.0-1.0) |
| `HYBRID_WEIGHT_LLM_ANALYSIS` | **YES** | - | LLM analysis weight (0.0-1.0) |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | Sentence transformer model |
| `RECOMMENDATION_CACHE_TTL` | No | `3600` | Cache TTL in seconds (60-86400) |

**CRITICAL Validation:**
- All four weights **MUST SUM TO EXACTLY 1.0**
- Each weight must be between 0.0 and 1.0
- Application will fail startup if weights don't sum to 1.0 (with 0.01 tolerance)

**Recommended Weights:**
```bash
HYBRID_WEIGHT_COLLABORATIVE=0.25    # 25% - User behavior patterns
HYBRID_WEIGHT_CONTENT_BASED=0.25    # 25% - Text similarity
HYBRID_WEIGHT_KNOWLEDGE_GRAPH=0.30  # 30% - Graph relationships
HYBRID_WEIGHT_LLM_ANALYSIS=0.20     # 20% - AI analysis
# Total: 1.00 (100%)
```

**Algorithm Explanation:**

1. **Collaborative Filtering (0.25)**: User purchase patterns and co-purchase analysis
2. **Content-Based (0.25)**: TF-IDF, keyword matching, semantic similarity
3. **Knowledge Graph (0.30)**: Product-task relationships from Neo4j
4. **LLM Analysis (0.20)**: GPT-4 semantic requirement matching

**Embedding Models:**
- `all-MiniLM-L6-v2` (default, fast, good quality)
- `all-mpnet-base-v2` (slower, higher quality)
- `multi-qa-mpnet-base-dot-v1` (optimized for Q&A)

---

### Product Classification

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CLASSIFICATION_CONFIDENCE_THRESHOLD` | No | `0.7` | Confidence threshold (0.0-1.0) |
| `CLASSIFICATION_CACHE_TTL` | No | `86400` | Cache TTL in seconds (60-604800) |

**Example:**
```bash
CLASSIFICATION_CONFIDENCE_THRESHOLD=0.7  # 70% confidence minimum
CLASSIFICATION_CACHE_TTL=86400           # 24 hours
```

**Threshold Guidelines:**
- `0.5-0.6`: Low confidence (more matches, less accuracy)
- `0.7-0.8`: Medium confidence (balanced)
- `0.9-1.0`: High confidence (fewer matches, high accuracy)

---

### API Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_HOST` | No | `0.0.0.0` | API bind host |
| `API_PORT` | No | `8002` | API port (1024-65535) |
| `API_WORKERS` | No | `4` | Worker processes (1-32) |
| `CORS_ORIGINS` | **YES** | - | Allowed CORS origins (comma-separated) |
| `MAX_REQUEST_SIZE` | No | `10485760` | Max request size (10MB) |
| `RATE_LIMIT_PER_MINUTE` | No | `100` | Rate limit (1-10000) |

**CORS Validation (Production):**
- **NO WILDCARDS** (`*`) allowed
- **HTTPS ONLY** - all origins must start with `https://`
- Must be comma-separated list

**Example:**
```bash
# Development
CORS_ORIGINS=http://localhost:3000,http://localhost:3010

# Production
CORS_ORIGINS=https://app.example.com,https://dashboard.example.com
```

---

### MCP Server

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MCP_HOST` | No | `0.0.0.0` | MCP server host |
| `MCP_PORT` | No | `3004` | MCP server port (1024-65535) |
| `MCP_TRANSPORT` | No | `websocket` | Transport type |

**Example:**
```bash
MCP_HOST=0.0.0.0
MCP_PORT=3004
MCP_TRANSPORT=websocket
```

---

### WebSocket Chat Server

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WEBSOCKET_HOST` | No | `0.0.0.0` | WebSocket host |
| `WEBSOCKET_PORT` | No | `8001` | WebSocket port (1024-65535) |

**Example:**
```bash
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8001
```

**Client Connection:**
```javascript
// Development
const ws = new WebSocket('ws://localhost:8001');

// Production
const ws = new WebSocket('wss://chat.example.com');
```

---

### Web Scraping

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SCRAPING_PORT` | No | `8003` | Scraping service port |
| `SCRAPING_WORKERS` | No | `2` | Number of workers |
| `SCRAPING_RATE_LIMIT` | No | `3.0` | Requests per second (0.1-10.0) |
| `SCRAPING_MAX_CONCURRENT` | No | `5` | Max concurrent requests (1-20) |
| `GOOGLE_API_KEY` | No | - | Google API key (optional) |
| `GOOGLE_SEARCH_ENGINE_ID` | No | - | Google Search Engine ID (optional) |

**Example:**
```bash
SCRAPING_PORT=8003
SCRAPING_WORKERS=2
SCRAPING_RATE_LIMIT=3.0
SCRAPING_MAX_CONCURRENT=5
```

---

### Feature Flags

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENABLE_AI_CLASSIFICATION` | No | `true` | Enable AI intent classification |
| `ENABLE_IMAGE_ANALYSIS` | No | `true` | Enable image analysis |
| `ENABLE_SEMANTIC_SEARCH` | No | `true` | Enable semantic search |
| `ENABLE_AUDIT_LOGGING` | No | `true` | Enable audit logging |

**Example:**
```bash
ENABLE_AI_CLASSIFICATION=true
ENABLE_IMAGE_ANALYSIS=true
ENABLE_SEMANTIC_SEARCH=true
ENABLE_AUDIT_LOGGING=true
```

---

### Monitoring & Observability

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROMETHEUS_PORT` | No | `9091` | Prometheus metrics port |
| `GRAFANA_PORT` | No | `3011` | Grafana dashboard port |
| `GRAFANA_PASSWORD` | No | - | Grafana admin password |
| `JAEGER_HOST` | No | `jaeger` | Jaeger tracing host |
| `JAEGER_PORT` | No | `6831` | Jaeger agent port |

**Example:**
```bash
PROMETHEUS_PORT=9091
GRAFANA_PORT=3011
GRAFANA_PASSWORD=<generated-secret>
JAEGER_HOST=jaeger
JAEGER_PORT=6831
```

---

### Docker & Network

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `COMPOSE_PROJECT_NAME` | No | `horme-pov` | Docker Compose project name |
| `DOCKER_NETWORK` | No | `horme-isolated-network` | Docker network name |
| `DOCKER_BUILDKIT` | No | `1` | Enable BuildKit |
| `COMPOSE_DOCKER_CLI_BUILD` | No | `1` | Use Docker CLI build |

**Example:**
```bash
COMPOSE_PROJECT_NAME=horme-pov
DOCKER_NETWORK=horme-isolated-network
DOCKER_BUILDKIT=1
COMPOSE_DOCKER_CLI_BUILD=1
```

---

## Validation Rules

### Startup Validation

On application startup, the configuration system validates:

1. **Required Fields**: All required fields must be set
2. **Security**: Secrets must meet minimum length requirements
3. **Production Constraints**:
   - No `localhost` in connection URLs
   - `DEBUG` must be `false`
   - CORS origins must use HTTPS
   - Secrets must be 32+ characters (64+ recommended)
4. **Hybrid Weights**: Must sum to 1.0 (±0.01 tolerance)
5. **URL Formats**: Database/Redis/Neo4j URLs must be valid
6. **API Keys**: OpenAI key must start with `sk-`

### Validation Example

```python
from src.core.config import config

# Automatic validation on import
# If any validation fails, application will not start

# Access validated configuration
print(config.ENVIRONMENT)  # 'production'
print(config.DATABASE_URL)  # postgresql://...
print(config.is_production())  # True
```

### Validation Errors

**Example Error (Missing Required Field):**
```
ValueError: Missing required configuration fields: OPENAI_API_KEY, SECRET_KEY.
Set these in your .env.production file or as environment variables.
```

**Example Error (Weak Secret):**
```
ValueError: SECRET_KEY must be at least 32 characters in production.
Generate with: openssl rand -hex 32
```

**Example Error (Hybrid Weights):**
```
ValueError: Hybrid recommendation engine weights must sum to 1.0, got 0.95.
Current weights: collaborative=0.25, content_based=0.25,
knowledge_graph=0.25, llm_analysis=0.20
```

---

## Security Best Practices

### 1. Secret Management

**Generate Strong Secrets:**
```bash
# Application secrets (64 characters)
openssl rand -hex 32  # SECRET_KEY
openssl rand -hex 32  # JWT_SECRET
openssl rand -hex 32  # ADMIN_PASSWORD

# Service passwords (48 characters)
openssl rand -hex 24  # POSTGRES_PASSWORD
openssl rand -hex 24  # REDIS_PASSWORD
openssl rand -hex 24  # NEO4J_PASSWORD
```

**Store Securely:**
- Use secrets management service (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault)
- **NEVER** commit `.env.production` to git (it's in `.gitignore`)
- Restrict file permissions: `chmod 600 .env.production`

**Rotate Regularly:**
- Rotate all secrets every 90 days minimum
- Rotate immediately if:
  - Secret is exposed/leaked
  - Employee with access leaves
  - Security incident occurs

### 2. Production Constraints

**Enforced by Validators:**
- ✅ No `localhost` in production URLs
- ✅ `DEBUG` must be `false`
- ✅ CORS uses HTTPS only
- ✅ No wildcard (`*`) CORS origins
- ✅ Secrets are 32+ characters

**Manual Checks:**
- Review logs for sensitive data leakage
- Enable audit logging (`ENABLE_AUDIT_LOGGING=true`)
- Monitor failed authentication attempts
- Set up alerting for security events

### 3. Docker Security

**Network Isolation:**
```bash
# Use Docker service names, not localhost
DATABASE_URL=postgresql://user:pass@postgres:5432/db  # ✅ Correct
DATABASE_URL=postgresql://user:pass@localhost:5432/db  # ❌ Wrong
```

**Container Security:**
- All containers run as non-root users
- Multi-stage builds minimize attack surface
- Regular security updates for base images
- Minimal required capabilities

### 4. Access Control

**Principle of Least Privilege:**
- Database users have minimal required permissions
- API keys have restricted scopes
- Service accounts are single-purpose

**Audit Trail:**
- All configuration changes logged
- Track who accessed what and when
- Monitor for unauthorized access attempts

---

## Troubleshooting

### Configuration Not Loading

**Problem:** Configuration validation fails on startup

**Solutions:**

1. **Check .env.production exists**:
   ```bash
   ls -la .env.production
   ```

2. **Verify required fields are set**:
   ```bash
   grep "ENVIRONMENT=" .env.production
   grep "DATABASE_URL=" .env.production
   grep "REDIS_URL=" .env.production
   ```

3. **Test configuration**:
   ```bash
   python -c "from src.core.config import config; print('✅ Valid')"
   ```

### Hybrid Weights Don't Sum to 1.0

**Problem:**
```
ValueError: Hybrid recommendation engine weights must sum to 1.0, got 0.95
```

**Solution:**
```bash
# Check current values
grep "HYBRID_WEIGHT" .env.production

# Ensure they sum to 1.0
HYBRID_WEIGHT_COLLABORATIVE=0.25
HYBRID_WEIGHT_CONTENT_BASED=0.25
HYBRID_WEIGHT_KNOWLEDGE_GRAPH=0.30
HYBRID_WEIGHT_LLM_ANALYSIS=0.20
# Total: 1.00 ✅
```

### Connection Refused Errors

**Problem:** Cannot connect to database/Redis/Neo4j

**Solutions:**

1. **Check Docker service names** (not localhost):
   ```bash
   # ❌ Wrong
   DATABASE_URL=postgresql://user:pass@localhost:5432/db

   # ✅ Correct
   DATABASE_URL=postgresql://user:pass@postgres:5432/db
   ```

2. **Verify services are running**:
   ```bash
   docker ps | grep postgres
   docker ps | grep redis
   docker ps | grep neo4j
   ```

3. **Check Docker network**:
   ```bash
   docker network inspect horme-isolated-network
   ```

### Secret Validation Failures

**Problem:**
```
ValueError: SECRET_KEY cannot be a common/weak value. Use: openssl rand -hex 32
```

**Solution:**
```bash
# Generate new secret
openssl rand -hex 32

# Update .env.production
SECRET_KEY=<generated-value>
```

### OpenAI API Errors

**Problem:** OpenAI API key invalid or quota exceeded

**Solutions:**

1. **Verify key format**:
   ```bash
   # Must start with 'sk-'
   OPENAI_API_KEY=sk-proj-...
   ```

2. **Check quota**:
   - Visit https://platform.openai.com/usage
   - Verify billing and limits

3. **Test key**:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

---

## Additional Resources

- **Configuration Template**: `.env.production.template`
- **Validation Code**: `src/core/config.py`
- **Docker Guide**: `CLAUDE.md`
- **Security Hardening**: `SECURITY_HARDENING_GUIDE.md`
- **Production Deployment**: `PRODUCTION_DEPLOYMENT_GUIDE.md`

---

## Quick Reference

### Minimum Production Configuration

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:$(openssl rand -hex 24)@postgres:5432/horme_db

# Redis
REDIS_URL=redis://:$(openssl rand -hex 24)@redis:6379/0

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=$(openssl rand -hex 24)

# OpenAI
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
ADMIN_PASSWORD=$(openssl rand -hex 32)

# CORS
CORS_ORIGINS=https://app.example.com

# Hybrid Weights (must sum to 1.0)
HYBRID_WEIGHT_COLLABORATIVE=0.25
HYBRID_WEIGHT_CONTENT_BASED=0.25
HYBRID_WEIGHT_KNOWLEDGE_GRAPH=0.30
HYBRID_WEIGHT_LLM_ANALYSIS=0.20
```

### Validation Command

```bash
# Quick validation
python -c "from src.core.config import config; print(f'✅ Configuration valid for {config.ENVIRONMENT}')"
```

---

**Last Updated**: 2025-01-27
**Version**: 1.0.0
**Maintainer**: Horme POV Development Team
