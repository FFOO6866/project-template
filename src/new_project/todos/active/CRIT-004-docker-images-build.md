# CRIT-004-Docker-Images-Build

## Description
Create missing Dockerfiles and build all required Docker images for production services to enable complete enterprise stack deployment.

## Current Critical Issue
- Missing Dockerfiles preventing service deployment
- Production docker-compose.yml references non-existent images
- 6 critical service images need to be built before deployment
- Service containers cannot start without proper base images

## Acceptance Criteria
- [ ] All 6 production Dockerfiles created and validated
- [ ] Docker images built successfully without errors
- [ ] Images tagged properly for production deployment
- [ ] All service dependencies included in images
- [ ] Multi-stage builds optimized for production
- [ ] Security best practices implemented in all images
- [ ] Image size optimized for deployment efficiency

## Dependencies
- CRIT-001: Docker Desktop installed
- CRIT-002: Docker daemon verified
- CRIT-003: Port connection issues resolved
- Production docker-compose.yml file available

## Risk Assessment
- **HIGH**: Missing Python dependencies may cause build failures
- **MEDIUM**: Dockerfile configuration errors may break services
- **MEDIUM**: Image size optimization may require multiple iterations
- **LOW**: Build time may be significant for first-time builds

## Required Docker Images
1. **Nexus Gateway Service** (docker/Dockerfile.nexus-gateway)
2. **DataFlow Service** (docker/Dockerfile.dataflow-service)
3. **MCP Server** (docker/Dockerfile.mcp-server)
4. **Classification Service** (docker/Dockerfile.classification-service)
5. **Workflow Engine** (docker/Dockerfile.workflow-engine)
6. **Frontend Service** (docker/Dockerfile.frontend) - if needed

## Subtasks
- [ ] Create Nexus Gateway Dockerfile (Est: 15min)
- [ ] Create DataFlow Service Dockerfile (Est: 15min)
- [ ] Create MCP Server Dockerfile (Est: 15min)
- [ ] Create Classification Service Dockerfile (Est: 15min)
- [ ] Build all Docker images (Est: 20min)
- [ ] Test image functionality (Est: 10min)

## Testing Requirements
- [ ] Build tests: All images build without errors
- [ ] Runtime tests: Containers start successfully
- [ ] Integration tests: Services can communicate via Docker network

## Dockerfile Templates

### Base Python Service Template
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["python", "-m", "src.service_main"]
```

## Build Commands
```bash
# 1. Build Nexus Gateway
docker build -f docker/Dockerfile.nexus-gateway -t horme-nexus-gateway:latest .

# 2. Build DataFlow Service
docker build -f docker/Dockerfile.dataflow-service -t horme-dataflow:latest .

# 3. Build MCP Server
docker build -f docker/Dockerfile.mcp-server -t horme-mcp-server:latest .

# 4. Build Classification Service
docker build -f docker/Dockerfile.classification-service -t horme-classification:latest .

# 5. Build all services with compose
docker-compose -f docker-compose.production.yml build

# 6. Verify all images built
docker images | grep horme
```

## Image Optimization
```dockerfile
# Multi-stage build example
FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY src/ ./src/

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

CMD ["python", "-m", "src.main"]
```

## Service-Specific Requirements

### Nexus Gateway Service
- FastAPI framework
- Database connectivity
- WebSocket support
- JWT authentication
- Health check endpoints

### DataFlow Service
- PostgreSQL integration
- DataFlow framework
- Model auto-generation
- Background task processing

### MCP Server
- WebSocket server
- Agent communication
- Tool execution
- Real-time messaging

### Classification Service
- OpenAI API integration
- Machine learning models
- Async processing
- Result caching

## Validation Steps
```bash
# 1. Test container startup
docker run --rm horme-nexus-gateway:latest --help

# 2. Test service health
docker run -d --name test-nexus -p 8000:8000 horme-nexus-gateway:latest
curl http://localhost:8000/health
docker stop test-nexus && docker rm test-nexus

# 3. Test with compose
docker-compose -f docker-compose.production.yml config
docker-compose -f docker-compose.production.yml build --no-cache
```

## Expected Resolution Time
45 minutes maximum

## Definition of Done
- [ ] All 6 production Dockerfiles created and tested
- [ ] All Docker images built successfully
- [ ] Images properly tagged for production use
- [ ] Container startup verified for all services
- [ ] No build errors or missing dependencies
- [ ] Images optimized for size and security
- [ ] Ready for full docker-compose deployment

## Next Actions After Completion
1. Deploy full production stack with docker-compose
2. Verify all services start and are healthy
3. Test inter-service communication and networking