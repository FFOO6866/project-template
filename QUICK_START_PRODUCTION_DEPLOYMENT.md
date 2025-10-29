# HORME POV - QUICK START PRODUCTION DEPLOYMENT
**Target**: Deploy to http://localhost:3010 (frontend) + http://localhost:8002 (backend)
**Time**: 90 minutes total
**Date**: 2025-10-27

---

## ⚡ SUPER QUICK START (Copy-Paste Commands)

### Step 1: Clean Up Duplicates (Skip if Already Clean)
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov
python scripts\cleanup_duplicate_files.py
# Type "yes" when prompted
```

### Step 2: Remove MCP Service (Quick Fix)
```bash
# Open docker-compose.production.yml
# Comment out lines 152-198 (MCP service section)
# Or I can do this for you
```

### Step 3: Start Services
```bash
# Start infrastructure
docker-compose -f docker-compose.production.yml up -d postgres redis neo4j

# Wait 60 seconds for health checks...

# Start applications
docker-compose -f docker-compose.production.yml up -d api frontend websocket

# Wait 60 seconds for health checks...

# Start supporting services
docker-compose -f docker-compose.production.yml up -d nginx email-monitor healthcheck
```

### Step 4: Test
```bash
# Test backend
curl http://localhost:8002/api/health

# Test frontend (open browser)
start http://localhost:3010

# Test API docs
start http://localhost:8002/docs
```

---

## 📋 SERVICE CHECKLIST

After deployment, verify these are working:

### Main Services ✅
- [ ] Frontend (UI): http://localhost:3010
- [ ] Backend API: http://localhost:8002
- [ ] API Documentation: http://localhost:8002/docs
- [ ] WebSocket Chat: ws://localhost:8001

### Supporting Services ✅
- [ ] PostgreSQL Database: localhost:5432
- [ ] Redis Cache: localhost:6379
- [ ] Neo4j Knowledge Graph:
  - [ ] Browser: http://localhost:7474
  - [ ] Bolt: bolt://localhost:7687

---

## 🔧 TROUBLESHOOTING

### Frontend Shows 500 Errors?
```bash
# Rebuild frontend
docker-compose -f docker-compose.production.yml build frontend
docker-compose -f docker-compose.production.yml up -d frontend
```

### Backend Won't Start?
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs api

# Check database connection
docker-compose -f docker-compose.production.yml exec postgres pg_isready
```

### View All Logs?
```bash
docker-compose -f docker-compose.production.yml logs -f
```

### Restart Everything?
```bash
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

---

## ✅ SUCCESS CRITERIA

You know it's working when:
1. ✅ `curl http://localhost:8002/api/health` returns `{"status": "healthy"}`
2. ✅ Frontend loads at http://localhost:3010 (no 500 errors)
3. ✅ API docs visible at http://localhost:8002/docs
4. ✅ All containers show "healthy" in `docker ps`

---

## 📖 FULL DETAILS

See `PRODUCTION_READINESS_COMPLETE_AUDIT_2025.md` for:
- Complete audit results
- Detailed execution plan
- Troubleshooting guide
- Production readiness checklist
