# DOCKER-001-Build-Missing-Docker-Images

## Description
Create and build all required Dockerfiles for the enterprise stack services that are currently missing. The docker-compose.production.yml references 6 services but several Dockerfiles are missing or incomplete.

## Acceptance Criteria
- [ ] Dockerfile.nexus-gateway created and builds successfully
- [ ] Dockerfile.dataflow-service created and builds successfully
- [ ] Dockerfile.mcp-server created and builds successfully
- [ ] Dockerfile.classification-service created and builds successfully
- [ ] All Docker images build without errors
- [ ] Images optimized for production (multi-stage builds, minimal base images)
- [ ] Health checks implemented in all service images

## Dependencies
- PROD-001: Docker environment setup complete
- Existing source code for each service
- Base images available (Python, Node.js, etc.)

## Risk Assessment
- **HIGH**: Missing source code for services may require implementation
- **MEDIUM**: Python dependency conflicts between services
- **MEDIUM**: Docker build context size may cause slow builds
- **LOW**: Base image vulnerabilities requiring security patches

## Subtasks
- [ ] Audit existing Dockerfiles in docker/ directory (Est: 30min) - Identify missing files
- [ ] Create Dockerfile.nexus-gateway (Est: 45min) - Python FastAPI service with health checks
- [ ] Create Dockerfile.dataflow-service (Est: 45min) - DataFlow framework service
- [ ] Create Dockerfile.mcp-server (Est: 45min) - MCP WebSocket server implementation
- [ ] Create Dockerfile.classification-service (Est: 45min) - AI classification service with GPU support
- [ ] Build and test all Docker images (Est: 30min) - Verify successful builds
- [ ] Optimize image sizes and security (Est: 30min) - Multi-stage builds and minimal base images

## Testing Requirements
- [ ] Unit tests: Each Dockerfile builds without errors
- [ ] Integration tests: Built images can start and respond to health checks
- [ ] E2E tests: docker-compose build completes successfully for all services

## Service Implementation Requirements

### Nexus Gateway (Port 8000)
- FastAPI application with REST endpoints
- JWT authentication middleware
- Database connection to PostgreSQL
- Redis session storage
- Health check endpoint at /health
- WebSocket support for real-time communication

### DataFlow Service
- Kailash DataFlow framework integration
- @db.model decorator functionality
- Auto-generated node creation (9 nodes per model)
- PostgreSQL database integration
- Model validation and migration support

### MCP Server (Port 3000)
- WebSocket server for AI agent communication
- MCP protocol implementation
- Tool registration and execution
- Workflow deployment capability
- Connection pooling and session management

### Classification Service
- OpenAI API integration
- UNSPSC/ETIM classification models
- GPU acceleration support (optional)
- Batch processing capability
- Model caching and optimization

## Definition of Done
- [ ] All 4 missing Dockerfiles created and functional
- [ ] docker-compose -f docker-compose.production.yml build completes successfully
- [ ] All built images have health check endpoints
- [ ] Images follow security best practices (non-root users, minimal attack surface)
- [ ] Build process documented and reproducible
- [ ] Image sizes optimized (under 500MB per service)
- [ ] Ready to proceed with DEPLOY-001 (Production Docker Compose Configuration)