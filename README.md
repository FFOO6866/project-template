# Horme POV - Production System

Production-ready RFP processing system with enterprise authentication and database integration.

## Quick Start

### Prerequisites
- Docker Desktop (with WSL2 backend on Windows)
- PostgreSQL credentials configured in `.env.production`

### 1. Configure Environment
```bash
# Copy and configure production environment
cp .env.example .env.production
# Edit .env.production with your secure keys
```

### 2. Start Production System
```bash
docker-compose -f docker-compose.production.yml up -d
```

### 3. Initialize Database
```bash
docker exec -i horme-postgres psql -U horme_user -d horme_db < init-scripts/02-auth-schema.sql
```

### 4. Access Services
- **API**: http://localhost:8002
- **API Docs**: http://localhost:8002/docs
- **Health Check**: http://localhost:8002/health

## Project Structure

```
horme-pov/
├── CLAUDE.md                          # Development guidelines
├── README.md                          # This file
├── docker-compose.production.yml      # Production orchestration
├── Dockerfile.api                     # API service container
├── Dockerfile.nexus                   # Nexus platform container
├── init-scripts/                      # Database initialization
│   └── 02-auth-schema.sql            # Authentication tables
├── src/                               # Application source code
│   ├── core/                         # Core authentication system
│   │   ├── auth.py                   # Database-backed auth
│   │   └── config.py                 # Configuration management
│   ├── production_api_server.py      # Main API server
│   ├── production_api_endpoints.py   # Business logic endpoints
│   └── nexus_backend_api.py         # Nexus platform API
├── tests/                            # Test suite
├── scripts/                          # Deployment scripts
├── docs/                             # Documentation
└── fe-reference/                     # Frontend reference

```

## Architecture

### Authentication System
- **Database**: PostgreSQL with bcrypt password hashing
- **Caching**: Redis for session management
- **Tokens**: JWT with 24-hour expiration
- **Audit**: All authentication events logged

### Security Features
- ✅ No hardcoded credentials
- ✅ Database-backed authentication
- ✅ Fail-fast configuration validation
- ✅ Account lockout after failed attempts
- ✅ Audit logging for compliance

## Configuration

### Required Environment Variables

See `.env.example` for full list. Key variables:

```bash
# Security (Required)
SECRET_KEY=<64-char-hex>
JWT_SECRET=<64-char-hex>
ADMIN_PASSWORD=<64-char-hex>

# Database (Required)
DATABASE_URL=postgresql://user:pass@postgres:5432/horme_db
REDIS_URL=redis://:password@redis:6379/0

# External Services
OPENAI_API_KEY=sk-...

# API Configuration
API_HOST=0.0.0.0
API_PORT=8002
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## Production Deployment

### Security Checklist
- [ ] Generate secure keys: `openssl rand -hex 32`
- [ ] Configure `.env.production` with real values
- [ ] Update CORS_ORIGINS with production domains
- [ ] Initialize database with authentication schema
- [ ] Create admin user via API
- [ ] Verify health checks pass

### Deployment Commands
```bash
# Build and start services
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Stop services
docker-compose -f docker-compose.production.yml down
```

## API Usage

### Authentication
```bash
# Register user
curl -X POST http://localhost:8002/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user","email":"user@example.com","password":"SecurePass123","role":"user"}'

# Login
curl -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"SecurePass123"}'
```

### RFP Processing
```bash
# Process RFP (requires authentication token)
curl -X POST http://localhost:8002/api/process-rfp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"rfp_text":"...","customer_name":"Customer Co","use_workflow":true}'
```

## Development

See [CLAUDE.md](./CLAUDE.md) for detailed development guidelines.

### Key Principles
- All development in Docker containers
- No local Python/Node execution
- Database-backed everything (no in-memory storage)
- Fail-fast on configuration errors

## Testing

```bash
# Run test suite in container
docker exec horme-api pytest tests/

# Run specific test
docker exec horme-api pytest tests/unit/test_auth.py
```

## Monitoring

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics` (Prometheus format)
- **Logs**: Structured JSON logging via structlog

## Support

For issues and questions:
1. Check logs: `docker-compose logs -f`
2. Verify configuration: Review `.env.production`
3. Check database: `docker exec horme-postgres psql -U horme_user -d horme_db`

## License

Proprietary - All rights reserved
