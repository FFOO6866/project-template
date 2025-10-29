# PRODUCTION DEPLOYMENT CHECKLIST
**Quick Reference Guide for Deployment**

---

## 🚨 BLOCKING ISSUES (Must Fix Before Deployment)

- [ ] **FIX:** `src/production_mcp_server.py` contains mock data (lines 1284-1523)
  - **Action:** Rename to `demo_mcp_server.py` OR replace mocks with real implementations
  - **Severity:** CRITICAL - violates production standards

- [ ] **GENERATE:** All secrets in `.env.production`
  ```bash
  openssl rand -hex 32  # SECRET_KEY
  openssl rand -hex 32  # JWT_SECRET
  openssl rand -hex 32  # ADMIN_PASSWORD
  openssl rand -hex 24  # POSTGRES_PASSWORD
  openssl rand -hex 24  # REDIS_PASSWORD
  openssl rand -hex 24  # NEO4J_PASSWORD
  ```

- [ ] **VALIDATE:** Configuration is complete
  ```bash
  python scripts/validate_config.py
  # Must show: ✅ All configuration valid
  ```

- [ ] **TEST:** Run full test suite
  ```bash
  pytest tests/ -v --cov
  # All tests must pass
  ```

- [ ] **VERIFY:** Authentication works end-to-end
  ```bash
  # Start services
  docker-compose up -d

  # Test registration
  curl -X POST http://localhost:8002/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"TestPass123!","username":"testuser"}'

  # Test login
  curl -X POST http://localhost:8002/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"TestPass123!"}'
  ```

---

## 📋 REQUIRED ENVIRONMENT VARIABLES

### Critical (Application Won't Start)
- [ ] `ENVIRONMENT=production`
- [ ] `DATABASE_URL=postgresql://user:pass@postgres:5432/db`
- [ ] `REDIS_URL=redis://:pass@redis:6379/0`
- [ ] `NEO4J_URI=bolt://neo4j:7687`
- [ ] `NEO4J_USER=neo4j`
- [ ] `NEO4J_PASSWORD=<generated>`
- [ ] `OPENAI_API_KEY=sk-proj-...`
- [ ] `SECRET_KEY=<generated-64-chars>`
- [ ] `JWT_SECRET=<generated-64-chars>`
- [ ] `ADMIN_PASSWORD=<generated-64-chars>`
- [ ] `CORS_ORIGINS=https://app.example.com`

### Hybrid Recommendation Engine (Must Sum to 1.0)
- [ ] `HYBRID_WEIGHT_COLLABORATIVE=0.25`
- [ ] `HYBRID_WEIGHT_CONTENT_BASED=0.25`
- [ ] `HYBRID_WEIGHT_KNOWLEDGE_GRAPH=0.30`
- [ ] `HYBRID_WEIGHT_LLM_ANALYSIS=0.20`

### Collaborative Filtering Thresholds
- [ ] `CF_MIN_USER_SIMILARITY=0.3`
- [ ] `CF_MIN_ITEM_SIMILARITY=0.4`

---

## 🔧 DEPLOYMENT STEPS

### 1. Prepare Environment
```bash
# Clone repository
git clone <repository-url>
cd horme-pov

# Copy environment template
cp .env.production.template .env.production

# Generate secrets (DO NOT SKIP THIS)
# Fill in .env.production with generated values
```

### 2. Validate Configuration
```bash
python scripts/validate_config.py
```

### 3. Initialize Databases
```bash
# Start database services
docker-compose up -d postgres redis neo4j

# Wait for startup
sleep 60

# Initialize schema
docker exec horme-postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -f /init-scripts/init-production-database.sql

# Verify
docker exec horme-postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"
```

### 4. Deploy Services
```bash
# Build and start
docker-compose up --build -d

# Check health
docker-compose ps
curl http://localhost:8002/health
```

### 5. Verify Deployment
```bash
# Check logs
docker-compose logs -f api

# Test authentication (see above)

# Monitor metrics
curl http://localhost:9091/metrics
```

---

## ✅ CODE QUALITY VERIFICATION

### All Fixed (No Action Needed)
- ✅ `src/production_api_endpoints.py` - All violations fixed
- ✅ `src/production_api_server.py` - No hardcoding
- ✅ `src/production_nexus_diy_platform.py` - All mocks removed
- ✅ `src/production_cli_interface.py` - Uses config
- ✅ `src/infrastructure/production_system.py` - Uses config
- ✅ `src/nexus_production_api.py` - Real auth implemented
- ✅ `src/core/config.py` - Comprehensive validation

### Needs Attention
- ⚠️ `src/production_mcp_server.py` - **HAS MOCK DATA** (see blocking issues)

---

## 🔒 SECURITY CHECKLIST

- [ ] All secrets generated with `openssl rand`
- [ ] No secrets in git repository
- [ ] `.env.production` in `.gitignore`
- [ ] `DEBUG=false` in production
- [ ] CORS origins use HTTPS only
- [ ] No wildcard (*) in CORS
- [ ] No localhost in connection URLs
- [ ] All passwords hashed with bcrypt
- [ ] JWT tokens properly validated
- [ ] Rate limiting enabled
- [ ] SQL injection tested
- [ ] XSS prevention verified

---

## 📊 MONITORING CHECKLIST

- [ ] Prometheus metrics accessible (port 9091)
- [ ] Grafana dashboards configured (port 3011)
- [ ] Application logs collected
- [ ] Error alerting configured
- [ ] Database performance monitored
- [ ] Cache hit rate tracked
- [ ] API latency tracked

---

## 💾 BACKUP CHECKLIST

- [ ] PostgreSQL automated backups (daily)
- [ ] Neo4j automated backups (daily)
- [ ] Backup restoration tested
- [ ] Recovery procedures documented
- [ ] Backup retention policy defined (30 days recommended)

---

## 🧪 TESTING CHECKLIST

- [ ] Unit tests pass: `pytest tests/unit/ -v`
- [ ] Integration tests pass: `pytest tests/integration/ -v`
- [ ] E2E tests pass: `pytest tests/e2e/ -v`
- [ ] Load testing completed (100 concurrent users)
- [ ] Security testing completed (OWASP ZAP)
- [ ] Authentication flow tested manually
- [ ] All API endpoints respond correctly

---

## 🚀 PRODUCTION READINESS GATES

### Gate 1: Code Quality ✅ 95%
- [x] No mock data (except production_mcp_server.py)
- [x] No hardcoded credentials
- [x] No fallback data in business logic
- [x] Centralized configuration
- [x] Proper error handling

### Gate 2: Configuration ⏳
- [ ] All required variables set
- [ ] All secrets generated
- [ ] Validation passes
- [ ] No localhost in production URLs

### Gate 3: Testing ⏳
- [ ] All tests pass
- [ ] Security testing complete
- [ ] Load testing complete
- [ ] Manual testing complete

### Gate 4: Infrastructure ⏳
- [ ] Databases initialized
- [ ] Services deployed
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Backups configured

---

## 🎯 DEPLOYMENT DECISION

**Can deploy to production?**
- ✅ Code is clean (except MCP server)
- ⏳ Configuration complete
- ⏳ Tests passing
- ⏳ Infrastructure ready

**Current Status:** 🟡 **NOT READY**

**Blocking Issues:** 4
1. Production MCP server has mock data
2. Secrets not generated
3. Tests not run
4. Security testing not done

**Estimated Time to Ready:** 1-2 weeks

---

## 📞 QUICK COMMANDS

### Check Service Health
```bash
docker-compose ps
curl http://localhost:8002/health
```

### View Logs
```bash
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Restart Services
```bash
docker-compose restart api
docker-compose restart postgres
```

### Database Access
```bash
# PostgreSQL
docker exec -it horme-postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

# Redis
docker exec -it horme-redis redis-cli

# Neo4j
open http://localhost:7474  # Browser interface
```

### Generate Secret
```bash
openssl rand -hex 32
```

### Validate Config
```bash
python scripts/validate_config.py
```

---

**For detailed information, see:**
- `FINAL_PRODUCTION_READINESS_VALIDATION.md` - Complete validation report
- `.env.production.template` - All environment variables
- `PRODUCTION_READINESS_ACTUAL_STATUS.md` - Previous audit results
