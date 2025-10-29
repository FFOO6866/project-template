# How to Start Frontend and Backend Services

## Quick Start (Recommended)

### Prerequisites
1. **Docker Desktop must be running**
   - Download from: https://www.docker.com/products/docker-desktop
   - Start Docker Desktop application
   - Wait for "Docker Desktop is running" status

### Option 1: Start with Docker Compose (Full Stack - RECOMMENDED)

This starts all services (Backend API, Frontend, PostgreSQL, Redis):

```bash
# Windows
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov

# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Stop services
docker-compose -f docker-compose.production.yml down
```

**Access Services**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8002
- API Health Check: http://localhost:8002/api/health

---

### Option 2: Start Services Individually (Development)

#### Step 1: Start Database Services First

**Start PostgreSQL:**
```bash
docker run -d \
  --name horme-postgres \
  -e POSTGRES_DB=horme_db \
  -e POSTGRES_USER=horme_user \
  -e POSTGRES_PASSWORD=96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42 \
  -p 5434:5432 \
  postgres:16
```

**Start Redis:**
```bash
docker run -d \
  --name horme-redis \
  --requirepass d0b6c3e5f14c813879c0cc08bfb5f81bea3d1f4aa584e7b3 \
  -p 6381:6379 \
  redis:7-alpine
```

#### Step 2: Start Backend API

**Option A: Using Python Directly** (if dependencies installed):
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov

# Set environment variables
set DATABASE_URL=postgresql://horme_user:96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42@localhost:5434/horme_db
set REDIS_URL=redis://:d0b6c3e5f14c813879c0cc08bfb5f81bea3d1f4aa584e7b3@localhost:6381/0
set JWT_SECRET=24d17531e3bab10fd01b58c7894438642b06ddf2cb942dc773cde369735cdf88
set NEXUS_JWT_SECRET=24d17531e3bab10fd01b58c7894438642b06ddf2cb942dc773cde369735cdf88
set SECRET_KEY=3ef4de347f3aafe9bef36b4359135ef3f005ba61ffda96ae111fc072f776979c
set CORS_ORIGINS=http://localhost:3000,http://localhost:3010,http://localhost:8002
set ENVIRONMENT=development
set ADMIN_EMAIL=admin@yourdomain.com
set ADMIN_PASSWORD_HASH=$2b$12$MEFztYPalfwuGYTH9yBmvOvYSHdyUPwxMCqWSfCnuYi3Wu0.Gw1Zi

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start backend
python -m uvicorn src.nexus_backend_api:app --host 0.0.0.0 --port 8002 --reload
```

**Option B: Using Docker**:
```bash
docker build -f Dockerfile.api -t horme-api .
docker run -d \
  --name horme-api \
  --env-file .env.production \
  -p 8002:8002 \
  --link horme-postgres:postgres \
  --link horme-redis:redis \
  horme-api
```

#### Step 3: Start Frontend

**Option A: Using Node.js Directly** (if Node.js installed):
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\frontend

# Install dependencies (if not already done)
npm install

# Create .env.local
echo NEXT_PUBLIC_API_URL=http://localhost:8002 > .env.local
echo NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001 >> .env.local

# Start frontend
npm run dev
```

**Option B: Using Docker**:
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\frontend

docker build -t horme-frontend .
docker run -d \
  --name horme-frontend \
  -e NEXT_PUBLIC_API_URL=http://localhost:8002 \
  -e NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001 \
  -p 3000:3000 \
  horme-frontend
```

---

## Troubleshooting

### "Docker Desktop is not running"
1. Open Docker Desktop application
2. Wait for it to fully start (whale icon should be steady)
3. Retry the docker commands

### "Port already in use"
```bash
# Find process using port
netstat -ano | findstr :8002
netstat -ano | findstr :3000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### "Cannot connect to database"
```bash
# Check if PostgreSQL is running
docker ps | findstr postgres

# Check PostgreSQL logs
docker logs horme-postgres

# Test connection
docker exec -it horme-postgres psql -U horme_user -d horme_db -c "SELECT 1"
```

### "Backend throws errors"
```bash
# Check backend logs
docker logs horme-api -f

# Or if running directly, check terminal output
```

### "Frontend cannot connect to backend"
1. Verify backend is running: http://localhost:8002/api/health
2. Check browser console for CORS errors
3. Verify NEXT_PUBLIC_API_URL is correct in .env.local

---

## Health Checks

### Backend API
```bash
curl http://localhost:8002/api/health
# Expected: {"status":"healthy"}
```

### Frontend
```bash
curl http://localhost:3000
# Expected: HTML response
```

### Database
```bash
docker exec -it horme-postgres psql -U horme_user -d horme_db -c "SELECT version()"
```

### Redis
```bash
docker exec -it horme-redis redis-cli ping
# Expected: PONG
```

---

## Stopping Services

### Stop Docker Compose Stack
```bash
docker-compose -f docker-compose.production.yml down
```

### Stop Individual Containers
```bash
docker stop horme-api horme-frontend horme-postgres horme-redis
docker rm horme-api horme-frontend horme-postgres horme-redis
```

### Stop Python/Node Directly
- Press `Ctrl+C` in the terminal running the service

---

## Access the Application

Once both services are running:

1. **Frontend**: http://localhost:3000
   - Main dashboard
   - Document upload interface
   - Chat interface

2. **Backend API**: http://localhost:8002
   - API documentation: http://localhost:8002/docs
   - Health check: http://localhost:8002/api/health

3. **Admin Login**:
   - Email: admin@yourdomain.com
   - Password: `2Cbs_Ehbz4wLTOVW8vS6KmoRsLOpl7xLJGo0TlG85Q0`

---

## Development Workflow

### Making Code Changes

**Backend**:
- Files auto-reload when changed (if running with `--reload` flag)
- Check terminal for any errors
- Test changes via http://localhost:8002/docs

**Frontend**:
- Hot Module Replacement (HMR) enabled
- Changes reflect immediately in browser
- Check browser console for errors

---

## Production Deployment

For production deployment, see:
- `SECURITY_FIXES_IMPLEMENTATION_REPORT.md`
- `PRODUCTION_READINESS_CRITICAL_AUDIT.md`

Key steps:
1. Update CORS_ORIGINS in .env.production
2. Update ADMIN_EMAIL in .env.production
3. Set ENVIRONMENT=production
4. Use `docker-compose -f docker-compose.production.yml`
5. Enable HTTPS with reverse proxy (nginx/traefik)

---

## Support

For issues, check:
1. Docker logs: `docker logs <container-name>`
2. Application logs in `logs/` directory
3. Browser console (F12) for frontend errors
4. `CLAUDE.md` for project documentation
