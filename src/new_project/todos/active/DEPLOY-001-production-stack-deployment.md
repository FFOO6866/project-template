# DEPLOY-001-Production-Stack-Deployment

## Description
Deploy complete production enterprise stack with all 7 services using Docker Compose to achieve 100% production readiness.

## Current Status
Ready to deploy after critical blocking issues resolved:
- Docker Desktop installed and operational
- Connection timeout issues fixed
- All Docker images built successfully
- Environment configuration prepared

## Acceptance Criteria
- [ ] All 7 services deployed and running
- [ ] PostgreSQL database accessible with health checks
- [ ] Redis cache operational with authentication
- [ ] Nexus Gateway API endpoints responding
- [ ] DataFlow service connected to database
- [ ] MCP server accepting WebSocket connections
- [ ] Classification service integrated with OpenAI
- [ ] Nginx reverse proxy routing traffic correctly
- [ ] All services healthy and passing health checks

## Dependencies
- CRIT-001: Docker Desktop installed
- CRIT-002: Docker daemon operational  
- CRIT-003: Port connectivity working
- CRIT-004: All Docker images built
- Environment variables configured (.env file)

## Risk Assessment
- **HIGH**: Service startup order dependencies may cause failures
- **MEDIUM**: Database initialization may take time
- **MEDIUM**: Network configuration between services
- **LOW**: Resource constraints on development machine

## Production Services Stack
1. **PostgreSQL Database** - Primary data storage
2. **Redis Cache** - Session and data caching
3. **Nexus Gateway** - REST API and WebSocket server
4. **DataFlow Service** - Database operations with auto-generated nodes
5. **MCP Server** - AI agent communication server
6. **Classification Service** - OpenAI-powered classification
7. **Nginx Proxy** - Reverse proxy and load balancer

## Subtasks
- [ ] Prepare production environment file (Est: 10min)
- [ ] Deploy database services first (Est: 10min)
- [ ] Deploy backend application services (Est: 15min)
- [ ] Deploy proxy and gateway services (Est: 10min)
- [ ] Verify all services healthy (Est: 15min)

## Testing Requirements
- [ ] Service tests: All containers start successfully
- [ ] Health tests: All health checks passing
- [ ] Integration tests: Service-to-service communication
- [ ] E2E tests: Complete workflow functionality

## Pre-Deployment Checklist
```bash
# 1. Verify Docker environment
docker --version
docker-compose --version
docker system info

# 2. Check available resources
docker system df
docker stats --no-stream

# 3. Verify images are available
docker images | grep horme

# 4. Validate compose file
docker-compose -f docker-compose.production.yml config
```

## Environment Configuration
```bash
# Create production .env file
cat > .env << EOF
# Database Configuration
POSTGRES_PASSWORD=secure_postgres_password_2024
POSTGRES_USER=horme_user
POSTGRES_DB=horme_product_db

# Redis Configuration  
REDIS_PASSWORD=secure_redis_password_2024

# JWT and Security
JWT_SECRET=secure_jwt_secret_key_2024_production

# OpenAI Integration
OPENAI_API_KEY=your_openai_api_key_here

# Logging
LOG_LEVEL=INFO

# Environment
NODE_ENV=production
NEXUS_ENV=production
DATAFLOW_ENV=production
MCP_ENV=production
CLASSIFICATION_ENV=production
EOF
```

## Deployment Commands
```bash
# 1. Start infrastructure services first
docker-compose -f docker-compose.production.yml up -d postgres redis

# 2. Wait for database to be ready
docker-compose -f docker-compose.production.yml exec postgres pg_isready -U horme_user

# 3. Start application services
docker-compose -f docker-compose.production.yml up -d nexus-gateway dataflow-service

# 4. Start AI and communication services
docker-compose -f docker-compose.production.yml up -d mcp-server classification-service

# 5. Start reverse proxy
docker-compose -f docker-compose.production.yml up -d nginx

# 6. Verify all services
docker-compose -f docker-compose.production.yml ps
```

## Service Health Verification
```bash
# 1. Check all containers are running
docker-compose -f docker-compose.production.yml ps

# 2. Test database connectivity
docker-compose -f docker-compose.production.yml exec postgres psql -U horme_user -d horme_product_db -c "SELECT version();"

# 3. Test Redis connectivity
docker-compose -f docker-compose.production.yml exec redis redis-cli ping

# 4. Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# 5. Test WebSocket connectivity
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" http://localhost:3000/

# 6. Test reverse proxy
curl http://localhost/health
```

## Monitoring and Logs
```bash
# 1. Monitor all service logs
docker-compose -f docker-compose.production.yml logs -f

# 2. Monitor specific service
docker-compose -f docker-compose.production.yml logs -f nexus-gateway

# 3. Check resource usage
docker stats

# 4. View container details
docker-compose -f docker-compose.production.yml top
```

## Troubleshooting Common Issues
```bash
# 1. Restart specific service
docker-compose -f docker-compose.production.yml restart nexus-gateway

# 2. Rebuild and restart service
docker-compose -f docker-compose.production.yml up -d --build nexus-gateway

# 3. Check service dependencies
docker-compose -f docker-compose.production.yml config --services

# 4. Scale services if needed
docker-compose -f docker-compose.production.yml up -d --scale nexus-gateway=2
```

## Expected Resolution Time
60 minutes maximum

## Performance Targets
- **API Response Time**: <200ms for standard requests
- **Database Query Time**: <50ms for indexed queries  
- **WebSocket Latency**: <100ms for real-time communication
- **Service Startup**: <30s for all services to be healthy
- **Memory Usage**: <4GB total for all services

## Definition of Done
- [ ] All 7 services running without errors
- [ ] All health checks passing consistently
- [ ] Database schemas initialized and accessible
- [ ] API endpoints responding correctly
- [ ] WebSocket connections working
- [ ] OpenAI integration functional
- [ ] Nginx proxy routing traffic correctly
- [ ] Logs showing no critical errors
- [ ] Performance targets met
- [ ] Ready for end-to-end testing

## Next Actions After Completion
1. Run comprehensive end-to-end tests
2. Validate DataFlow @db.model functionality
3. Test classification workflows
4. Performance and load testing
5. Security and monitoring setup