# MCP-001-Fix-MCP-Server-Dependencies

## Description
Resolve missing dependencies causing the MCP server to restart in loops. The MCP server is critical for AI agent communication and workflow execution but is currently failing to start properly.

## Acceptance Criteria
- [ ] MCP server starts without restart loops
- [ ] All Python dependencies installed and compatible
- [ ] WebSocket server operational on port 3000
- [ ] MCP protocol implementation functional
- [ ] Health monitoring shows stable status
- [ ] Log files show successful startup without errors

## Dependencies
- DOCKER-001: MCP server Docker image built
- PROD-002-EXEC: PostgreSQL and Redis services running
- Database connection and environment configuration

## Risk Assessment
- **HIGH**: Python dependency version conflicts causing import errors
- **HIGH**: Missing required system packages in Docker image
- **MEDIUM**: Network port conflicts on port 3000
- **MEDIUM**: Database connection timeout causing startup failures
- **LOW**: Memory allocation insufficient for MCP server

## Subtasks
- [ ] Analyze current MCP server error logs (Est: 15min) - Identify specific dependency failures
- [ ] Audit requirements.txt for MCP server (Est: 15min) - Check for missing or conflicting packages
- [ ] Update Dockerfile.mcp-server with missing dependencies (Est: 30min) - System packages and Python requirements
- [ ] Implement proper dependency pinning (Est: 15min) - Lock versions for stability
- [ ] Add health check and startup validation (Est: 15min) - Container health monitoring
- [ ] Configure proper logging and error handling (Est: 15min) - Debug startup issues
- [ ] Test MCP server startup in isolation (Est: 15min) - Verify fixes work

## Common MCP Server Dependencies
- websockets (WebSocket server implementation)
- asyncio (Async programming support)
- pydantic (Data validation and serialization)
- sqlalchemy (Database ORM)
- redis (Redis client)
- uvloop (High-performance async event loop)
- python-json-logger (Structured logging)
- prometheus-client (Metrics collection)

## MCP Server Requirements
- WebSocket server on port 3000
- MCP protocol message handling
- Tool registration and execution
- Session management and authentication
- Database connection for persistence
- Redis integration for caching
- Metrics collection and health monitoring

## Testing Requirements
- [ ] Unit tests: MCP server starts without errors
- [ ] Integration tests: WebSocket connections can be established
- [ ] E2E tests: MCP protocol messages processed correctly

## Container Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python /app/health_check.py || exit 1
```

## Environment Variables Required
- MCP_ENV=production
- DATABASE_URL=postgresql://horme_user:password@postgres:5432/horme_product_db
- REDIS_URL=redis://:password@redis:6379/2
- MCP_LOG_LEVEL=INFO
- MCP_PORT=3000
- MCP_HOST=0.0.0.0

## Definition of Done
- [ ] MCP server container starts and stays running
- [ ] No restart loops in Docker container status
- [ ] WebSocket server accepts connections on port 3000
- [ ] Health check endpoint responds with 200 OK
- [ ] Log files show successful startup messages
- [ ] All required dependencies installed and working
- [ ] Database and Redis connections established
- [ ] Memory usage stable under normal operation
- [ ] Ready for MCP-002 (MCP WebSocket Configuration)