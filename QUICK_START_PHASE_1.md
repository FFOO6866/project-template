# Quick Start Guide - Phase 1 Neo4j Integration

**Purpose**: Get Neo4j knowledge graph running and tested in 5 minutes
**Status**: Ready for deployment

---

## Prerequisites

- [x] Docker Desktop installed and running
- [x] `.env.production` file exists with credentials
- [x] Python 3.11+ installed
- [x] All dependencies in `requirements.txt`

---

## Step 1: Start Neo4j Service (1 minute)

```bash
# Start Neo4j, PostgreSQL, and Redis
docker-compose -f docker-compose.production.yml up -d neo4j postgres redis

# Wait for services to be healthy (30 seconds)
docker-compose -f docker-compose.production.yml ps

# Expected output:
# horme-neo4j      Up (healthy)   7474/tcp, 7687/tcp
# horme-postgres   Up (healthy)   5432/tcp
# horme-redis      Up (healthy)   6379/tcp
```

**Check Neo4j is ready**:
```bash
# View Neo4j logs
docker-compose -f docker-compose.production.yml logs neo4j | tail -20

# Expected output:
# Started.
# Remote interface available at http://localhost:7474/
```

---

## Step 2: Install Python Dependencies (1 minute)

```bash
# Install Neo4j driver (if not already installed)
pip install neo4j==5.16.0

# Or install all dependencies
pip install -r requirements.txt
```

---

## Step 3: Run Integration Tests (2 minutes)

```bash
# Run comprehensive test suite
python test_neo4j_integration.py
```

**Expected Output**:
```
================================================================================
# Neo4j Knowledge Graph Integration Tests
# Phase 1: Enterprise AI Recommendation System
================================================================================

✅ NEO4J_URI: bolt://neo4j:7687
✅ NEO4J_USER: neo4j
✅ NEO4J_PASSWORD: ********

================================================================================
TEST 1: Neo4j Connection
================================================================================
✅ Neo4j connection successful

================================================================================
TEST 2: Schema Verification
================================================================================
✅ Schema initialized successfully
   - Constraints: 7
   - Indexes: 13
   - Total nodes: 9
   - Node counts by type:
     * Skill: 4
     * SafetyEquipment: 5

================================================================================
TEST 3: Create Sample Nodes
================================================================================
✅ Sample product node created
✅ Sample task node created
✅ USED_FOR relationship created
✅ Found 1 products for task
   - Test Cordless Drill (TEST-DRILL-001) - required

================================================================================
TEST 4: PostgreSQL-Neo4j Integration
================================================================================
✅ PostgreSQL connection successful
⚠️ No products to sync (database empty - import products first)

================================================================================
TEST 5: Knowledge Graph Recommendations
================================================================================
✅ Found recommendations for test tasks

================================================================================
TEST SUMMARY
================================================================================
Connection Test: ✅ PASSED
Schema Verification: ✅ PASSED
Sample Node Creation: ✅ PASSED
PostgreSQL Integration: ✅ PASSED
Knowledge Graph Recommendations: ✅ PASSED

Total: 5 tests
Passed: 5
Failed: 0
Success Rate: 100%

🎉 ALL TESTS PASSED! Neo4j integration is ready for Phase 2.
```

---

## Step 4: Access Neo4j Browser (Optional)

Open Neo4j browser UI to explore the graph:

**URL**: http://localhost:7474

**Login**:
- Username: `neo4j`
- Password: (get from `.env.production` - `NEO4J_PASSWORD` variable)

**Try these queries**:

```cypher
// View all nodes
MATCH (n) RETURN n LIMIT 25

// View skill levels
MATCH (s:Skill) RETURN s.name, s.level, s.description

// View safety equipment
MATCH (se:SafetyEquipment)
RETURN se.name, se.category, se.standard, se.mandatory

// View test product and task
MATCH (p:Product)-[r:USED_FOR]->(t:Task)
WHERE p.sku = 'TEST-DRILL-001'
RETURN p, r, t
```

---

## Step 5: Sync Products from PostgreSQL (if products exist)

```python
# Run this in Python shell or script
from src.core.postgresql_database import get_database

db = get_database()

# Sync first 100 products (for testing)
sync_result = db.sync_products_to_knowledge_graph(limit=100)

print(f"Status: {sync_result['status']}")
print(f"Synced: {sync_result['synced']} products")
print(f"Failed: {sync_result['failed']} products")
print(f"Success Rate: {sync_result['sync_percentage']}%")
```

**Expected Output** (if products exist):
```
Status: success
Synced: 95 products
Failed: 5 products
Success Rate: 95.0%
```

**Expected Output** (if no products):
```
Status: warning
Message: No products to sync
Synced: 0
```

---

## Troubleshooting

### Issue: "Connection refused" error

**Cause**: Neo4j container not started or not healthy

**Fix**:
```bash
# Check container status
docker-compose -f docker-compose.production.yml ps neo4j

# If not running, start it
docker-compose -f docker-compose.production.yml up -d neo4j

# Wait 30 seconds for startup
```

### Issue: "Authentication failed" error

**Cause**: Wrong password or NEO4J_PASSWORD not set

**Fix**:
```bash
# Check .env.production has NEO4J_PASSWORD
grep NEO4J_PASSWORD .env.production

# If missing, add it:
# NEO4J_PASSWORD=your_secure_password_here
```

### Issue: "Schema not initialized" error

**Cause**: Schema init script not executed

**Fix**:
```bash
# Manually run schema initialization
docker exec -it horme-neo4j cypher-shell -u neo4j -p YOUR_PASSWORD -f /docker-entrypoint-initdb.d/neo4j-schema.cypher
```

### Issue: "No products to sync" warning

**Cause**: PostgreSQL database is empty

**Fix**: Import products first:
```bash
# Import from Excel (if you have products.xlsx)
python -c "
from src.core.postgresql_database import get_database
db = get_database()
db.import_products_from_excel('path/to/products.xlsx')
"

# Then retry sync
python -c "
from src.core.postgresql_database import get_database
db = get_database()
result = db.sync_products_to_knowledge_graph()
print(result)
"
```

---

## Verification Checklist

- [ ] Docker Desktop is running
- [ ] Neo4j container is healthy (`docker ps` shows "Up (healthy)")
- [ ] PostgreSQL container is healthy
- [ ] Redis container is healthy
- [ ] Neo4j browser accessible at http://localhost:7474
- [ ] All 5 integration tests pass
- [ ] Sample product and task nodes created
- [ ] Products synced from PostgreSQL (if available)

---

## Next Steps

Once all tests pass:

1. **Import Products** (if not done):
   - Use `import_products_from_excel()` method
   - Or manually add products via API

2. **Sync to Neo4j**:
   - Run `sync_products_to_knowledge_graph()` for all products
   - Verify sync completed successfully

3. **Create Task Nodes** (Phase 2 prerequisite):
   - Define DIY tasks (drill holes, paint walls, install shelves, etc.)
   - Create task nodes in Neo4j
   - Link products to tasks via USED_FOR relationships

4. **Test Recommendations**:
   - Use `get_knowledge_graph_recommendations()` method
   - Verify relevant products returned for task descriptions

5. **Proceed to Phase 2**:
   - UNSPSC/ETIM classification implementation
   - See `PHASE_1_NEO4J_IMPLEMENTATION_COMPLETE.md` for details

---

## Quick Commands Reference

```bash
# Start services
docker-compose -f docker-compose.production.yml up -d neo4j postgres redis

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f neo4j

# Run tests
python test_neo4j_integration.py

# Stop services
docker-compose -f docker-compose.production.yml down

# Stop and remove volumes (fresh start)
docker-compose -f docker-compose.production.yml down -v
```

---

## Performance Notes

**Current Configuration**:
- Neo4j heap: 512MB initial, 2GB max
- Page cache: 1GB
- Suitable for: 10,000-50,000 products

**If you have more products**:
- Edit `docker-compose.production.yml`
- Increase `NEO4J_dbms_memory_heap_max__size` to 4GB
- Increase `NEO4J_dbms_memory_pagecache_size` to 2GB

---

## Support

**Documentation**:
- `PHASE_1_NEO4J_IMPLEMENTATION_COMPLETE.md` - Complete implementation guide
- `docs/adr/ADR-008-enterprise-recommendation-system-implementation.md` - Architecture decisions

**Test Output**: If tests fail, share the output with your team for debugging

**Neo4j Documentation**: https://neo4j.com/docs/

---

**Last Updated**: 2025-01-16
**Phase**: 1 of 6 complete
**Status**: ✅ Ready for Testing
