# Horme POV - Demo Port Reference

## Service Port Mappings

### Frontend & User Interfaces
| Service | Host Port | Container Port | URL | Description |
|---------|-----------|----------------|-----|-------------|
| **Frontend (Next.js)** | **3010** | 3000 | http://localhost:3010 | Main web interface |
| Your Other App | 3000 | - | http://localhost:3000 | (No conflict) |

### Backend APIs
| Service | Host Port | Container Port | URL | Description |
|---------|-----------|----------------|-----|-------------|
| **API Server (FastAPI)** | **8002** | 8000 | http://localhost:8002 | REST API endpoints |
| **WebSocket Chat** | **8001** | 8001 | ws://localhost:8001 | Real-time chat |
| **MCP Server** | **3004** | 3001 | http://localhost:3004 | Model Context Protocol |
| **Nexus Platform** | **8090** | 8090 | http://localhost:8090 | Multi-channel platform |

### Databases
| Service | Host Port | Container Port | Connection String | Description |
|---------|-----------|----------------|-------------------|-------------|
| **PostgreSQL** | **5434** | 5432 | postgresql://horme_user:***@localhost:5434/horme_db | Main database |
| **Redis** | **6381** | 6379 | redis://:***@localhost:6381/0 | Cache & sessions |
| **Neo4j** | **7687** | 7687 | bolt://neo4j:***@localhost:7687 | Knowledge graph |
| **Neo4j Browser** | **7474** | 7474 | http://localhost:7474 | Neo4j web UI |

### Reverse Proxy & Monitoring
| Service | Host Port | Container Port | URL | Description |
|---------|-----------|----------------|-----|-------------|
| Nginx (HTTP) | 80 | 80 | http://localhost | Reverse proxy |
| Nginx (HTTPS) | 443 | 443 | https://localhost | SSL termination |
| Prometheus | 9091 | 9090 | http://localhost:9091 | Metrics collection |
| Grafana | 3011 | 3000 | http://localhost:3011 | Monitoring dashboards |

## Quick Start for Demo

### 1. Start Core Services
```bash
docker-compose -f docker-compose.production.yml --env-file .env.production up -d postgres redis neo4j
```

### 2. Start Application Services
```bash
docker-compose -f docker-compose.production.yml --env-file .env.production up -d api frontend websocket
```

### 3. Access Your Demo

**Frontend:** Open http://localhost:3010 in your browser
**API Docs:** Visit http://localhost:8002/docs for Swagger UI
**Health Check:** curl http://localhost:8002/health

## Port Conflict Check

Before starting, verify no conflicts:
```bash
# Windows
netstat -ano | findstr ":3010 :8002 :8001"

# Should return empty if ports are free
```

## Testing API from Frontend

Your frontend on port 3010 will connect to:
- API: http://localhost:8002
- WebSocket: ws://localhost:8001

These are already configured in `.env.production`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8002
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001
```

## Key API Endpoints for Demo

### Product Search
```bash
curl -X POST http://localhost:8002/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cordless drill safety equipment",
    "limit": 10
  }'
```

### Project Recommendations
```bash
curl -X POST http://localhost:8002/api/projects/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "home_renovation",
    "skill_level": "intermediate",
    "budget_max": 5000
  }'
```

### Health Check
```bash
curl http://localhost:8002/health
```

## Troubleshooting

### Port 3010 Already in Use
```bash
# Change in .env.production
FRONTEND_PORT=3011

# Restart frontend
docker-compose -f docker-compose.production.yml --env-file .env.production up -d frontend
```

### Port 8002 Already in Use
```bash
# Change in .env.production
API_PORT=8003

# Restart API
docker-compose -f docker-compose.production.yml --env-file .env.production up -d api
```

## Service Dependencies

```
Frontend (3010)
    ↓
    └─→ API (8002)
            ↓
            ├─→ PostgreSQL (5434)
            ├─→ Redis (6381)
            ├─→ Neo4j (7687)
            └─→ OpenAI API
```

---

**Last Updated:** 2025-10-18
**Configuration File:** .env.production
**Docker Compose:** docker-compose.production.yml
