# ADR-003: Docker Consolidation and Containerization Standards

## Status
Accepted

## Context
The Horme POV project grew organically with multiple Docker Compose files, inconsistent container configurations, and complex deployment patterns. The system requires standardized containerization to support development, testing, and production environments reliably.

### Current Challenges
- 15+ different Docker Compose files with overlapping configurations
- Inconsistent port mappings and environment variables
- Ad-hoc container networking and dependency management
- Manual container health checks and monitoring
- Complex deployment scripts with environment-specific logic

### Requirements
- Unified container orchestration for all environments
- Consistent networking and service discovery
- Standardized health checks and monitoring
- Simplified deployment with profile-based configuration
- Resource limits and security constraints
- Multi-stage builds for optimized container sizes

## Decision
We consolidate all Docker configurations into a single, profile-based orchestration system with standardized containerization patterns.

### Container Architecture
```yaml
# docker-compose.consolidated.yml - Single source of truth
version: '3.8'
services:
  # Core Services
  postgres:
    image: postgres:15-alpine
    profiles: ["default", "production", "monitoring"]
    
  redis:
    image: redis:7-alpine  
    profiles: ["default", "production"]
    
  # Application Services
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
      target: production
    profiles: ["default", "production"]
    
  mcp:
    build:
      context: .
      dockerfile: Dockerfile.mcp-lightweight
    profiles: ["default", "production", "monitoring"]
    
  frontend:
    build:
      context: fe-reference
      dockerfile: Dockerfile
    profiles: ["default", "production"]
```

### Standardized Dockerfile Patterns
```dockerfile
# Multi-stage production build
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM python:3.11-alpine AS production
RUN adduser -D -s /bin/sh appuser
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --chown=appuser:appuser . .
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
EXPOSE 8000
CMD ["python", "-m", "src.production_api"]
```

## Deployment Profiles

### Default Profile
**Purpose**: Development and basic testing
**Services**: PostgreSQL, Redis, API, MCP, Frontend
**Resources**: Standard limits for development
**Ports**: Alternative ports to avoid Windows conflicts

### Production Profile  
**Purpose**: Production deployment with full security
**Services**: All default + Nginx reverse proxy + SSL termination
**Resources**: Production resource limits and constraints
**Security**: Non-root users, read-only containers, secrets management

### Monitoring Profile
**Purpose**: Observability and metrics collection
**Services**: All default + Prometheus, Grafana, AlertManager
**Resources**: Additional monitoring overhead
**Dashboards**: Pre-configured Grafana dashboards

### Admin Profile
**Purpose**: Database administration and maintenance
**Services**: All default + PgAdmin, Redis Commander
**Resources**: Administrative tool access
**Security**: Restricted network access, admin authentication

## Container Standards

### Security Requirements
```yaml
# Security configuration template
security_opt:
  - no-new-privileges:true
read_only: true
user: "1001:1001"  # Non-root user
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE  # Only if needed
tmpfs:
  - /tmp:rw,noexec,nosuid,size=100m
```

### Resource Limits
```yaml
# Resource constraints
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 1G
    reservations:
      cpus: '0.25' 
      memory: 512M
```

### Health Checks
```yaml
# Standardized health check
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  start_period: 40s
  retries: 3
```

## Consequences

### Positive
- **Simplified Deployment**: Single command deployment with profiles
- **Environment Consistency**: Same containers across all environments
- **Resource Optimization**: Efficient resource utilization with limits
- **Security Hardening**: Standardized security configurations
- **Maintenance Reduction**: Single configuration to maintain
- **Debugging Improvement**: Consistent logging and monitoring

### Negative
- **Migration Complexity**: Consolidating existing configurations
- **Profile Learning Curve**: Understanding profile system
- **Resource Requirements**: Higher minimum resource requirements
- **Debugging Changes**: Different debugging approach needed
- **Breaking Changes**: Existing deployment scripts need updates

## Alternatives Considered

### Option 1: Keep Multiple Compose Files
- **Description**: Maintain separate Docker Compose files per environment
- **Pros**: Environment-specific optimizations, gradual changes
- **Cons**: Configuration drift, maintenance overhead, inconsistency
- **Why Rejected**: Scales poorly, creates environment-specific bugs

### Option 2: Kubernetes Migration
- **Description**: Move to Kubernetes orchestration
- **Pros**: Enterprise-grade orchestration, scaling, service mesh
- **Cons**: Complexity overhead, learning curve, infrastructure requirements
- **Why Rejected**: Overkill for current scale, deployment complexity

### Option 3: Single Container Approach
- **Description**: Run all services in one container
- **Pros**: Simple deployment, minimal orchestration
- **Cons**: Poor separation of concerns, scaling limitations, debugging difficulty
- **Why Rejected**: Anti-pattern, poor operational characteristics

## Implementation Plan

### Phase 1: Consolidation (Complete)
1. Create `docker-compose.consolidated.yml` with all services
2. Implement profile-based service selection
3. Standardize all Dockerfile patterns
4. Update deployment scripts to use profiles

### Phase 2: Security Hardening (Complete)
1. Implement non-root user patterns
2. Add resource limits to all services
3. Implement standardized health checks
4. Add security scanning to build pipeline

### Phase 3: Optimization (Complete)
1. Multi-stage builds for all containers
2. Container image optimization
3. Network optimization and isolation
4. Performance monitoring integration

## Container Image Standards

### Base Image Selection
- **Python Services**: `python:3.11-alpine` for production
- **Node.js Services**: `node:18-alpine` for production
- **Database Services**: Official Alpine variants when available
- **Utility Containers**: `alpine:latest` with minimal packages

### Image Optimization
- Multi-stage builds to minimize final image size
- `.dockerignore` to exclude unnecessary files
- Layer caching optimization for faster builds
- Security scanning in CI pipeline

### Tagging Strategy
```bash
# Image tagging pattern
horme-api:latest          # Latest development build
horme-api:v1.2.3         # Semantic version release
horme-api:sha-abc123     # Git commit hash
horme-api:production     # Current production version
```

## Deployment Commands

### Development
```bash
# Start development environment
docker-compose -f docker-compose.consolidated.yml up -d

# View logs
docker-compose -f docker-compose.consolidated.yml logs -f [service]

# Scale specific services
docker-compose -f docker-compose.consolidated.yml up -d --scale api=3
```

### Production
```bash
# Production deployment with all profiles
docker-compose -f docker-compose.consolidated.yml --profile production up -d

# Monitoring enabled
docker-compose -f docker-compose.consolidated.yml --profile monitoring up -d

# Full stack with admin tools
docker-compose -f docker-compose.consolidated.yml --profile default --profile admin up -d
```

## Validation Criteria
- [ ] Single consolidated Docker Compose file operational
- [ ] All deployment profiles functional
- [ ] Resource limits enforced on all containers
- [ ] Security standards implemented across all images
- [ ] Health checks operational for all services
- [ ] Multi-stage builds optimized for size and security
- [ ] Documentation updated for new deployment patterns