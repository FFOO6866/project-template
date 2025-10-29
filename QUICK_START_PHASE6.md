# Phase 6: Quick Start Guide

## Prerequisites
- Docker Desktop installed and running
- OpenAI API key configured in `.env.production`
- 8GB RAM minimum

## 🚀 Quick Start (5 Minutes)

### Step 1: Fix Docker Compose (Required)
```bash
# Fix the websocket_logs volume placement
# See: DOCKER_COMPOSE_FIX_REQUIRED.md for details
```

### Step 2: Build Services
```bash
# Build all containers
docker-compose -f docker-compose.production.yml build
```

### Step 3: Start Services
```bash
# Start databases first
docker-compose -f docker-compose.production.yml up -d postgres redis neo4j

# Wait 30 seconds for databases to initialize
sleep 30

# Start application services
docker-compose -f docker-compose.production.yml up -d api websocket frontend nginx
```

### Step 4: Verify Deployment
```bash
# Check all services are running
docker-compose -f docker-compose.production.yml ps

# Check logs
docker-compose -f docker-compose.production.yml logs -f websocket
```

### Step 5: Access Services
- **Frontend**: http://localhost
- **API**: http://localhost/api/docs
- **WebSocket**: ws://localhost/ws
- **Health**: http://localhost/health

## 🧪 Run Tests

```bash
# Install test dependencies
pip install websockets requests

# Test WebSocket server
python test_websocket_chat.py

# Test frontend integration
python test_frontend_integration.py
```

## 📊 Expected Results

### WebSocket Tests
```
========================================
WebSocket Chat Server Integration Tests
========================================
✅ Connection Test: PASSED
✅ Authentication Test: PASSED
✅ Chat Message Test: PASSED
✅ Context Update Test: PASSED
✅ Ping-Pong Test: PASSED

Total: 5/5 tests passed
Success rate: 100.0%
```

### Frontend Integration Tests
```
========================================
Frontend Integration Tests
========================================
✅ Frontend Health: PASSED
✅ Frontend Homepage: PASSED
✅ API Connection: PASSED
✅ Metrics Endpoint: PASSED
✅ CORS Headers: PASSED
✅ Static Assets: PASSED
✅ WebSocket Upgrade: PASSED

Total: 7/7 tests passed
Success rate: 100.0%
```

## 🛠️ Troubleshooting

### WebSocket Connection Failed
```bash
# Check WebSocket container
docker logs horme-websocket

# Restart WebSocket service
docker-compose -f docker-compose.production.yml restart websocket
```

### Frontend Not Loading
```bash
# Check frontend container
docker logs horme-frontend

# Check nginx configuration
docker exec horme-nginx nginx -t
```

### Database Connection Issues
```bash
# Check PostgreSQL
docker exec horme-postgres pg_isready -U horme_user

# View database logs
docker logs horme-postgres
```

## 📝 Important Files

| File | Description |
|------|-------------|
| `src/websocket/chat_server.py` | WebSocket server implementation |
| `nginx/nginx.conf` | Reverse proxy configuration |
| `docker-compose.production.yml` | Service orchestration |
| `Dockerfile.websocket` | WebSocket container |
| `requirements-websocket.txt` | WebSocket dependencies |
| `scripts/build_frontend.sh` | Frontend build automation |

## 🔧 Configuration

### Environment Variables
Edit `.env.production`:
```bash
# OpenAI (Required)
OPENAI_API_KEY=sk-your-key-here

# WebSocket URLs
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost/ws

# For HTTPS:
# NEXT_PUBLIC_WEBSOCKET_URL=wss://your-domain.com/ws
```

## 📖 Full Documentation

- **Complete Report**: `PHASE6_FRONTEND_WEBSOCKET_DEPLOYMENT_REPORT.md`
- **Docker Fix**: `DOCKER_COMPOSE_FIX_REQUIRED.md`
- **WebSocket API**: See `src/websocket/chat_server.py` docstrings

## ✅ Success Criteria

All services should be:
- ✅ Running (check with `docker ps`)
- ✅ Healthy (check with `docker-compose ps`)
- ✅ Accessible via browser
- ✅ Passing integration tests

## 🎯 Next Steps

1. **Test Chat Functionality**:
   - Open http://localhost
   - Send a message in the chat
   - Verify AI response

2. **Monitor Logs**:
   ```bash
   docker-compose -f docker-compose.production.yml logs -f
   ```

3. **Configure SSL/TLS** (Production):
   - Obtain SSL certificate
   - Update nginx.conf
   - Update environment variables

## 🆘 Support

If you encounter issues:
1. Check `PHASE6_FRONTEND_WEBSOCKET_DEPLOYMENT_REPORT.md` Section 10 (Troubleshooting)
2. Review service logs: `docker-compose logs [service]`
3. Verify environment variables: `docker exec [container] printenv`

---

**Quick Start Version**: 1.0
**Phase**: 6 - Frontend + WebSocket Deployment
**Status**: ✅ Ready for Deployment
