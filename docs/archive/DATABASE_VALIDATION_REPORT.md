# Database Schema Validation Report
**Date:** 2025-10-18
**Status:** CRITICAL SCHEMA MISMATCH

## Executive Summary

**CRITICAL FINDINGS:**
1. PostgreSQL database initialized with WRONG schema (init-production-database.sql)
2. DataFlow models defined in production_models.py are NOT created
3. Neo4j is DOWN due to memory configuration error
4. Redis is functional but not password-protected as configured

---

## 1. PostgreSQL Schema Status

### Connection Details
- **Host:** horme-postgres (Docker container)
- **Port:** 5434 (external), 5432 (internal)
- **Database:** horme_db
- **User:** horme_user
- **Status:** HEALTHY (container running)

### Schema Mismatch Analysis

#### Expected Tables (from production_models.py - 21 models)
The following DataFlow models are defined but **NOT created in database:**

1. **Category** - Product categories with hierarchical support
2. **Brand** - Product brands and manufacturers
3. **Supplier** - Suppliers and data sources
4. **Product** - Core product catalog with enrichment tracking
5. **ProductPricing** - Product pricing history and variations
6. **ProductSpecification** - Technical specifications and attributes
7. **ProductInventory** - Inventory tracking and stock levels
8. **WorkRecommendation** - AI-generated work recommendations
9. **RFPDocument** - Request for Proposal documents and analysis
10. **Quotation** - Generated quotations and proposals
11. **QuotationItem** - Individual line items in quotations
12. **Customer** - Customer and client information
13. **ActivityLog** - System activity and user actions tracking
14. **OSHAStandard** - OSHA safety standards (29 CFR)
15. **ANSIStandard** - ANSI/ISEA/ASTM safety standards
16. **ToolRiskClassification** - Risk classifications for tools and equipment
17. **TaskHazardMapping** - Hazard mappings for specific tasks
18. **ANSIEquipmentSpecification** - ANSI equipment specifications and certifications
19. **UNSPSCCode** - UNSPSC classification codes
20. **ETIMClass** - ETIM classification codes
21. **ProductClassification** - Links products to UNSPSC and ETIM classifications

#### Actually Created Tables (from init-production-database.sql)

**Schema: dataflow (5 tables)**
- products (18 columns) - DIFFERENT structure than production_models.py
- product_enrichment (7 columns) - NOT in production_models.py
- suppliers (12 columns) - DIFFERENT structure
- product_suppliers (11 columns) - NOT in production_models.py
- quotations (14 columns) - DIFFERENT structure

**Schema: nexus (4 tables)**
- users
- api_keys
- workflow_executions
- sessions

**Schema: mcp (2 tables)**
- connections
- tool_executions

**Schema: monitoring (3 tables)**
- system_metrics
- application_logs
- health_checks

**Schema: public (0 tables)**
- Empty (DataFlow models should create tables here)

### Data Status
- **Products Count:** 3 (sample data from init script)
- **Categories Count:** 0 (table doesn't exist)
- **Brands Count:** 0 (table doesn't exist)
- **Suppliers Count:** 0 (actual supplier table exists but is empty)
- **Quotations Count:** 0

### Schema Comparison: dataflow.products

**init-production-database.sql structure:**
```sql
- id (UUID)
- product_id (VARCHAR)
- name (VARCHAR 500)
- description (TEXT)
- category (VARCHAR) -- flat field
- subcategory (VARCHAR)
- brand (VARCHAR) -- flat field
- model (VARCHAR)
- sku (VARCHAR)
- price (DECIMAL)
- currency (VARCHAR)
- availability (VARCHAR)
- specifications (JSONB)
- attributes (JSONB)
- images (JSONB)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- is_active (BOOLEAN)
```

**production_models.py Product model:**
```python
- sku (str)
- name (str)
- slug (str)
- description (Optional[str])
- category_id (Optional[int]) -- foreign key
- brand_id (Optional[int]) -- foreign key
- supplier_id (Optional[int]) -- foreign key
- status (str) -- active/inactive/discontinued
- is_published (bool)
- availability (str)
- currency (str)
- base_price (Optional[Decimal])
- catalogue_item_id (Optional[int])
- source_url (Optional[str])
- images_url (Optional[str])
- enriched_description (Optional[str])
- technical_specs (Optional[Dict])
- supplier_info (Optional[Dict])
- competitor_data (Optional[Dict])
- enrichment_status (str)
- enrichment_source (Optional[str])
- last_enriched (Optional[datetime])
- import_metadata (Optional[Dict])
- created_at (datetime)
- updated_at (datetime)
- deleted_at (datetime) -- soft delete
- version (int) -- versioning
```

**KEY DIFFERENCES:**
- production_models uses foreign keys (category_id, brand_id, supplier_id)
- init script uses flat VARCHAR fields
- production_models has soft delete and versioning
- production_models has enrichment tracking fields
- init script uses UUID primary keys
- production_models auto-generates integer IDs

---

## 2. Neo4j Knowledge Graph Status

### Connection Details
- **Host:** horme-neo4j (Docker container)
- **Port:** 7687 (Bolt), 7474 (HTTP)
- **User:** neo4j
- **Password:** Configured
- **Status:** FAILED - CONTAINER DOWN

### Critical Error
```
ERROR Invalid memory configuration - exceeds physical memory.
Check the configured values for server.memory.pagecache.size
and server.memory.heap.max_size
```

### Expected Schema (Not Created)
Based on project documentation, should contain:

**Node Types:**
- Product
- Task
- UNSPSCCode
- ETIMClass
- Category
- Brand
- Supplier
- SafetyStandard
- Tool
- Hazard

**Relationship Types:**
- BELONGS_TO_CATEGORY
- MANUFACTURED_BY
- REQUIRES_PPE
- HAS_HAZARD
- COMPATIBLE_WITH
- CLASSIFIED_AS
- USED_FOR_TASK

**Current State:**
- **Node Types:** 0 (database not accessible)
- **Relationships:** 0 (database not accessible)
- **Indexes:** 0 (database not accessible)
- **Constraints:** 0 (database not accessible)

### Required Actions
1. Fix Docker memory allocation for Neo4j container
2. Reduce heap size and page cache configuration
3. Run population script: scripts/populate_neo4j_graph.py

---

## 3. Redis Cache Status

### Connection Details
- **Host:** horme-redis (Docker container)
- **Port:** 6381 (external), 6379 (internal)
- **Password:** Configured but NOT enforced
- **Status:** HEALTHY (container running)

### Configuration Issue
```
AUTH failed: ERR AUTH <password> called without any password
configured for the default user. Are you sure your configuration
is correct?
```

Redis is accepting connections WITHOUT password authentication despite password being configured in .env.production.

### Current State
- **Total Connections:** 100
- **Keyspace Hits:** 0
- **Keyspace Misses:** 0
- **Database Size:** 1 key
- **Memory Usage:** Not checked

### Security Risk
**HIGH:** Redis is accessible without authentication, allowing unauthorized access to cache data.

---

## 4. Critical Schema Misalignment

### Root Cause Analysis

**PROBLEM:**
Two different database schemas exist in the codebase:

1. **init-production-database.sql** (legacy/different design)
   - UUID-based IDs
   - Flat category/brand/supplier fields
   - Different table structure
   - Missing many production_models.py tables

2. **production_models.py** (DataFlow-based, intended design)
   - Auto-incrementing integer IDs
   - Normalized design with foreign keys
   - Comprehensive business models (21 tables)
   - Enterprise features (soft delete, versioning, audit logs)

**IMPACT:**
- Application code expects production_models.py schema
- Database has init-production-database.sql schema
- **RESULT: All DataFlow-based code will FAIL**

### Missing Tables (Production Critical)

These tables are defined in production_models.py but **DO NOT EXIST** in database:

**Core Product Management:**
- category (product categories)
- brand (brands and manufacturers)
- productpricing (pricing history)
- productspecification (technical specs)
- productinventory (stock tracking)

**Business Operations:**
- customer (client information)
- workrecommendation (AI recommendations)
- rfpdocument (RFP processing)
- quotationitem (quotation line items)
- activitylog (audit trail)

**Safety & Compliance:**
- oshastandard (OSHA regulations)
- ansistandard (ANSI standards)
- toolriskclassification (tool safety)
- taskhazardmapping (hazard tracking)
- ansiequipmentspecification (equipment specs)

**Product Classification:**
- unspsc_codes (UNSPSC classification)
- etim_classes (ETIM classification)
- product_classifications (classification links)

---

## 5. Recommended Immediate Actions

### Priority 1: Fix Neo4j (CRITICAL)
```bash
# Update docker-compose.production.yml Neo4j memory settings
NEO4J_dbms_memory_heap_max__size=512M  # Reduce from current value
NEO4J_dbms_memory_pagecache_size=256M  # Reduce from current value

# Restart Neo4j
docker-compose -f docker-compose.production.yml restart neo4j
```

### Priority 2: Align PostgreSQL Schema (CRITICAL)
**Option A: Use DataFlow Auto-Migration (Recommended)**
```python
# Create migration script: scripts/migrate_to_production_models.py
from src.models.production_models import db
import asyncio

async def migrate():
    # DataFlow will detect differences and create migration plan
    success, migrations = await db.auto_migrate(dry_run=True)

    # Review migration plan
    print("Proposed Migrations:")
    for migration in migrations:
        print(f"- {migration.description}")
        print(f"  Safety: {migration.safety_level}")

    # Apply if safe
    if success:
        await db.auto_migrate(auto_confirm=True)

asyncio.run(migrate())
```

**Option B: Drop and Recreate (Data Loss)**
```sql
-- WARNING: DELETES ALL DATA
DROP SCHEMA dataflow CASCADE;
-- Then run production_models.py initialization
```

**Option C: Manual Migration (Time-Consuming)**
- Write SQL migration scripts to transform existing data
- Add missing tables
- Migrate data from flat structure to normalized structure

### Priority 3: Fix Redis Authentication (HIGH)
```bash
# Update docker-compose.production.yml
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD}

# Restart Redis
docker-compose -f docker-compose.production.yml restart redis
```

### Priority 4: Initialize Missing Tables
```bash
# After fixing schema alignment, run:
uv run python scripts/load_classification_data.py
uv run python scripts/load_safety_standards_postgresql.py
uv run python scripts/populate_neo4j_graph.py
```

---

## 6. Database Initialization Checklist

### PostgreSQL
- [x] Database created (horme_db)
- [x] Schemas created (nexus, dataflow, mcp, monitoring)
- [ ] **Production models tables created (0/21 DataFlow models)**
- [ ] **Category table exists**
- [ ] **Brand table exists**
- [ ] **Supplier table normalized (currently flat)**
- [ ] **Product table matches production_models.py**
- [x] Sample data loaded (3 products - wrong structure)
- [ ] Indexes created for production models
- [ ] Foreign key constraints created
- [ ] Soft delete columns added
- [ ] Version columns added
- [ ] Audit log triggers created

### Neo4j
- [ ] **Container running (FAILED - memory error)**
- [ ] Database accessible
- [ ] Product nodes created
- [ ] Task nodes created
- [ ] Classification nodes created (UNSPSC, ETIM)
- [ ] Safety standard nodes created
- [ ] Relationships created
- [ ] Indexes created
- [ ] Constraints created

### Redis
- [x] Container running
- [x] Database accessible
- [ ] **Password authentication enabled (NOT ENFORCED)**
- [ ] Connection pooling configured
- [ ] Cache TTL policies set

---

## 7. Production Readiness Assessment

### Database Layer: NOT READY ❌

**Blocking Issues:**
1. Schema mismatch between init script and production models
2. Neo4j down due to memory misconfiguration
3. Redis authentication not enforced
4. 21 critical business tables missing
5. No data in classification tables (UNSPSC, ETIM)
6. No safety standards data loaded
7. No knowledge graph populated

**Estimated Fix Time:** 4-8 hours
- Fix Neo4j memory: 30 minutes
- Schema migration: 2-4 hours
- Data loading: 2-3 hours
- Validation testing: 1 hour

---

## 8. Next Steps

### Immediate (Today)
1. Fix Neo4j memory configuration
2. Decide on schema migration strategy (recommend Option A)
3. Run DataFlow auto-migration
4. Verify all 21 tables created
5. Fix Redis authentication

### Short-term (This Week)
1. Load classification data (UNSPSC, ETIM)
2. Load safety standards (OSHA, ANSI)
3. Populate Neo4j knowledge graph
4. Run comprehensive validation tests
5. Update init scripts to use production_models.py

### Documentation Updates Needed
1. Update deployment documentation with correct initialization
2. Document schema migration process
3. Add validation checklist to deployment guide
4. Update docker-compose.production.yml with correct settings

---

## Contact & Escalation

**Critical Issues Identified:**
- Database schema does not match application code
- Production deployment would fail immediately
- No business logic tables exist
- Knowledge graph unavailable

**Recommended Action:** HALT deployment until schema alignment is complete.

---

**Report Generated:** 2025-10-18 03:31 UTC
**Validation Tool:** Direct database inspection via Docker exec
**Environment:** Local Docker development environment
