# Horme POV - Production Deployment Guide
**Step-by-Step Instructions to Deploy Real Product System**

**Version**: 1.0
**Date**: 2025-01-17
**Status**: Ready for Execution

---

## Quick Start (TL;DR)

```bash
# 1. Clean codebase
python scripts/cleanup_duplicate_files.py

# 2. Configure environment
cp .env.production.template .env.production
# Edit .env.production with real values

# 3. Start Docker stack
docker-compose -f docker-compose.production.yml up -d

# 4. Initialize database
docker exec -i horme-postgres psql -U horme_user -d horme_db < init-scripts/01-unified-schema.sql
docker exec -i horme-postgres psql -U horme_user -d horme_db < init-scripts/02-auth-schema.sql
docker exec -i horme-postgres psql -U horme_user -d horme_db < init-scripts/03-production-data-schema.sql

# 5. Load product data (19,143 products)
docker exec horme-api python scripts/load_horme_products.py

# 6. Enrich products from web (9,764 products, ~2-5 hours)
docker exec horme-enrichment-worker python scripts/scrape_horme_product_details.py

# 7. Populate knowledge graph
docker exec horme-api python scripts/populate_neo4j_graph.py

# 8. Verify deployment
curl http://localhost:8002/health
```

---

## Prerequisites

### Required Software
- **Docker Desktop** 20.10+ (with WSL2 backend on Windows)
- **Python** 3.11+ (for running scripts outside Docker)
- **PostgreSQL Client** (optional, for debugging)
- **Git** (for version control)

### Required Accounts
- **OpenAI API Key** - Get from https://platform.openai.com/api-keys
  - Estimated cost: $50-200 for initial enrichment
  - GPT-4-turbo-preview recommended

### Required Data
- `ProductData (Top 3 Cats).xlsx` - Located in `docs/reference/`
  - 17,266 single products
  - 1,877 package products
  - Total: 19,143 products

---

## Step 1: Codebase Cleanup (30 minutes)

### Objective
Remove all duplicate and mock data files to ensure only one working version exists.

### Execution

```bash
# Review files that will be deleted
python scripts/cleanup_duplicate_files.py --dry-run  # (if you add this flag)

# Execute cleanup
python scripts/cleanup_duplicate_files.py
```

**Expected Output**:
```
Files deleted: 65/65
Directories deleted: 2/2
```

### What Gets Removed
- 6 duplicate recommendation engines
- 5 duplicate API servers
- 10+ duplicate RFP systems
- 3 duplicate Nexus platforms
- 10+ duplicate enrichment pipelines
- All demo/test files in `src/`
- All mock data files

### What Gets Kept (Production Files)
```
src/
├── ai/
│   └── hybrid_recommendation_engine.py    # THE recommendation engine
├── core/
│   ├── neo4j_knowledge_graph.py           # THE knowledge graph
│   ├── postgresql_database.py             # THE database layer
│   ├── auth.py                            # THE authentication
│   └── config.py                          # THE configuration
├── models/
│   └── production_models.py                # THE data models
├── workflows/
│   └── product_matching.py                 # THE workflow (cleaned)
├── production_api_server.py                # THE API server
├── production_api_endpoints.py             # THE endpoints
├── nexus_production_api.py                 # THE Nexus platform
└── nexus_production_mcp.py                 # THE MCP integration
```

---

## Step 2: Environment Configuration (15 minutes)

### Create .env.production

```bash
# Copy template
cp .env.production.template .env.production

# Generate secure passwords
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET
openssl rand -hex 32  # For POSTGRES_PASSWORD
openssl rand -hex 32  # For REDIS_PASSWORD
openssl rand -hex 32  # For NEO4J_PASSWORD
```

### Edit .env.production

```bash
# ============================================================================
# DATABASE (REQUIRED)
# ============================================================================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=horme_db
POSTGRES_USER=horme_user
POSTGRES_PASSWORD=<PASTE_GENERATED_PASSWORD_HERE>
DATABASE_URL=postgresql://horme_user:<PASSWORD>@postgres:5432/horme_db

# ============================================================================
# REDIS CACHE (REQUIRED)
# ============================================================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<PASTE_GENERATED_PASSWORD_HERE>
REDIS_URL=redis://:<PASSWORD>@redis:6379/0

# ============================================================================
# NEO4J KNOWLEDGE GRAPH (REQUIRED)
# ============================================================================
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<PASTE_GENERATED_PASSWORD_HERE>
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687

# ============================================================================
# OPENAI API (REQUIRED)
# ============================================================================
OPENAI_API_KEY=sk-<YOUR_OPENAI_API_KEY>
OPENAI_MODEL=gpt-4-turbo-preview

# ============================================================================
# HYBRID RECOMMENDATION WEIGHTS (REQUIRED - must sum to 1.0)
# ============================================================================
HYBRID_WEIGHT_COLLABORATIVE=0.25
HYBRID_WEIGHT_CONTENT_BASED=0.25
HYBRID_WEIGHT_KNOWLEDGE_GRAPH=0.30
HYBRID_WEIGHT_LLM_ANALYSIS=0.20

# ============================================================================
# WEB SCRAPING (REQUIRED)
# ============================================================================
SCRAPING_USER_AGENT=Mozilla/5.0 (compatible; HormeBot/1.0)
SCRAPING_RATE_LIMIT=1
SCRAPING_TIMEOUT=30
SCRAPING_MAX_RETRIES=3

# ============================================================================
# SECURITY (REQUIRED)
# ============================================================================
SECRET_KEY=<PASTE_GENERATED_64_CHAR_HEX>
JWT_SECRET=<PASTE_GENERATED_64_CHAR_HEX>
ADMIN_PASSWORD=<PASTE_GENERATED_64_CHAR_HEX>

# ============================================================================
# APPLICATION
# ============================================================================
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8002
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**CRITICAL**: Replace all `<PASTE_...>` placeholders with real values!

---

## Step 3: Database Schema Extension (10 minutes)

### Create Production Schema File

**File**: `init-scripts/03-production-data-schema.sql`

```sql
-- Category/Task Keyword Mappings
CREATE TABLE IF NOT EXISTS category_keyword_mappings (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    weight DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(category, keyword)
);

CREATE INDEX idx_category_keywords ON category_keyword_mappings(category, keyword);

-- Task Keyword Mappings
CREATE TABLE IF NOT EXISTS task_keyword_mappings (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    weight DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(task_id, keyword)
);

CREATE INDEX idx_task_keywords ON task_keyword_mappings(task_id, keyword);

-- Product Enrichment Log
CREATE TABLE IF NOT EXISTS product_enrichment_log (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    catalogue_id INTEGER,
    enrichment_status VARCHAR(50) NOT NULL,
    enrichment_started_at TIMESTAMP,
    enrichment_completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_enrichment_status ON product_enrichment_log(enrichment_status, product_id);

-- Web Scraping Queue
CREATE TABLE IF NOT EXISTS scraping_queue (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    priority INTEGER DEFAULT 5,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    product_id INTEGER REFERENCES products(id),
    catalogue_id INTEGER,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    scheduled_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(url)
);

CREATE INDEX idx_scraping_queue_status ON scraping_queue(status, priority, scheduled_at);
```

---

## Step 4: Docker Deployment (20 minutes)

### Start Production Stack

```bash
# Build and start all services
docker-compose -f docker-compose.production.yml up -d --build

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Check service health
docker-compose -f docker-compose.production.yml ps
```

**Expected Output**:
```
NAME              STATUS
horme-postgres    healthy
horme-redis       healthy
horme-neo4j       healthy
horme-api         healthy
```

### Initialize Database

```bash
# Run schema migrations
docker exec -i horme-postgres psql -U horme_user -d horme_db < init-scripts/01-unified-schema.sql
docker exec -i horme-postgres psql -U horme_user -d horme_db < init-scripts/02-auth-schema.sql
docker exec -i horme-postgres psql -U horme_user -d horme_db < init-scripts/03-production-data-schema.sql

# Verify tables created
docker exec -it horme-postgres psql -U horme_user -d horme_db -c "\dt"
```

**Expected Output**: ~30+ tables created

---

## Step 5: Load Product Data (30 minutes)

### Execute Excel Data Loader

```bash
# Set environment (if running outside Docker)
export DATABASE_URL="postgresql://horme_user:<PASSWORD>@localhost:5433/horme_db"

# Run loader
python scripts/load_horme_products.py

# OR inside Docker
docker exec horme-api python scripts/load_horme_products.py
```

**Expected Output**:
```
Categories: 3 loaded
Brands: 50-100 loaded
Single SKU: 17,266 loaded, 0 failed
Package SKU: 1,877 loaded, 0 failed
TOTAL: 19,143 loaded, 0 failed
ENRICHMENT: 9,764 products queued for web scraping
```

### Verify Data Loaded

```bash
# Check product count
docker exec -it horme-postgres psql -U horme_user -d horme_db -c "SELECT COUNT(*) FROM products;"

# Check categories
docker exec -it horme-postgres psql -U horme_user -d horme_db -c "SELECT name, COUNT(*) FROM categories c JOIN products p ON c.id = p.category_id GROUP BY c.name;"

# Check scraping queue
docker exec -it horme-postgres psql -U horme_user -d horme_db -c "SELECT COUNT(*) FROM scraping_queue WHERE status = 'pending';"
```

**Expected**: 19,143 products, 9,764 in queue

---

## Step 6: Web Enrichment (2-5 hours)

### Execute Web Scraper

```bash
# Set environment
export DATABASE_URL="postgresql://horme_user:<PASSWORD>@localhost:5433/horme_db"
export OPENAI_API_KEY="sk-your-key"
export SCRAPING_RATE_LIMIT=1

# Run scraper (LONG RUNNING - 2-5 hours)
python scripts/scrape_horme_product_details.py

# OR inside Docker
docker exec horme-enrichment-worker python scripts/scrape_horme_product_details.py

# Monitor progress in separate terminal
tail -f logs/web_scraping.log
```

**Expected Output**:
```
Rate Limit: 1.0 requests/second
Max Concurrent: 3 workers
Timeout: 30 seconds

Queue Statistics:
  Pending: 9,764
  Processing: 0
  Completed: 0
  Failed: 0

Processing: SKU ABC123 (Catalogue ID: 1234)
  Fetched https://www.horme.com.sg/product.aspx?id=1234
  AI extraction successful
  SUCCESS: SKU ABC123 enriched

Progress: 100 processed, 95 successful, 5 failed
...

ENRICHMENT COMPLETE
Total Processed: 9,764
Successful: 9,500 (97.3%)
Failed: 264 (2.7%)
```

### Handle Failures

If scraping fails for some products:

```bash
# Check failed items
docker exec -it horme-postgres psql -U horme_user -d horme_db -c \
  "SELECT COUNT(*), error_message FROM scraping_queue WHERE status = 'failed' GROUP BY error_message;"

# Retry failed items (reset status)
docker exec -it horme-postgres psql -U horme_user -d horme_db -c \
  "UPDATE scraping_queue SET status = 'pending', retry_count = retry_count + 1 WHERE status = 'failed' AND retry_count < 3;"

# Run scraper again (will only process pending items)
python scripts/scrape_horme_product_details.py
```

---

## Step 7: Knowledge Graph Population (20 minutes)

### Create Neo4j Populator Script

**File**: `scripts/populate_neo4j_graph.py` (create this)

```python
"""
Populate Neo4j Knowledge Graph from PostgreSQL
"""

import os
import psycopg2
from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

def main():
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(DATABASE_URL)

    # Connect to Neo4j
    neo4j_driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    logger.info("Populating Neo4j knowledge graph...")

    # Load products from PostgreSQL
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT p.id, p.sku, p.name, p.description,
                   c.name as category, b.name as brand
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE p.is_published = true
        """)
        products = cur.fetchall()

    logger.info(f"Found {len(products)} products to load")

    # Create product nodes in Neo4j
    with neo4j_driver.session() as session:
        for idx, (pid, sku, name, desc, category, brand) in enumerate(products):
            session.run("""
                MERGE (p:Product {id: $id, sku: $sku})
                SET p.name = $name,
                    p.description = $description,
                    p.category = $category,
                    p.brand = $brand
            """, id=pid, sku=sku, name=name, description=desc or '',
                 category=category or '', brand=brand or '')

            if (idx + 1) % 100 == 0:
                logger.info(f"  Loaded {idx+1} products...")

    logger.info(f"Successfully loaded {len(products)} products into Neo4j")

    pg_conn.close()
    neo4j_driver.close()

if __name__ == "__main__":
    main()
```

### Execute

```bash
python scripts/populate_neo4j_graph.py
```

**Expected Output**:
```
Loaded 19,143 products into Neo4j
```

---

## Step 8: Verification & Testing (30 minutes)

### Health Checks

```bash
# API health
curl http://localhost:8002/health

# Neo4j browser
open http://localhost:7474
# Login: neo4j / <your_password>

# Run Cypher query
MATCH (p:Product) RETURN count(p)
# Expected: 19,143
```

### Test Product Search

```bash
# Search for products
curl -X POST http://localhost:8002/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "cordless drill", "limit": 10}'
```

**Expected**: Real Horme products, NO mock data

### Test Hybrid Recommendations

```bash
# Get recommendations for RFP
curl -X POST http://localhost:8002/api/process-rfp \
  -H "Content-Type: application/json" \
  -d '{
    "rfp_text": "We need power tools for construction project",
    "customer_name": "Test Construction Co"
  }'
```

**Expected**: Product recommendations with hybrid scores, explainability

---

## Step 9: Production Monitoring (Ongoing)

### Metrics to Track

```bash
# Database size
docker exec -it horme-postgres psql -U horme_user -d horme_db -c \
  "SELECT pg_size_pretty(pg_database_size('horme_db'));"

# Product statistics
docker exec -it horme-postgres psql -U horme_user -d horme_db -c \
  "SELECT
     COUNT(*) as total,
     COUNT(*) FILTER (WHERE enrichment_status = 'completed') as enriched,
     COUNT(*) FILTER (WHERE enrichment_status = 'pending') as pending,
     COUNT(*) FILTER (WHERE enrichment_status = 'failed') as failed
   FROM products;"

# Neo4j statistics
# In Neo4j browser: CALL db.stats()
```

### Log Monitoring

```bash
# API logs
docker logs -f horme-api

# Enrichment logs
tail -f logs/web_scraping.log

# Database logs
docker logs -f horme-postgres
```

---

## Troubleshooting

### Issue: Products Not Loading

```bash
# Check Excel file exists
ls -lh docs/reference/ProductData\ \(Top\ 3\ Cats\).xlsx

# Check database connection
docker exec -it horme-postgres psql -U horme_user -d horme_db -c "SELECT 1;"

# Check loader logs
tail -f logs/data_loading.log
```

### Issue: Web Scraping Blocked

```bash
# Reduce rate limit
export SCRAPING_RATE_LIMIT=0.5  # 1 request every 2 seconds

# Change user agent
export SCRAPING_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

### Issue: Neo4j Not Starting

```bash
# Check Neo4j logs
docker logs horme-neo4j

# Increase memory limits in docker-compose.production.yml
NEO4J_server_memory_heap_max__size=2G
```

---

## Success Criteria

- [ ] 19,143 products loaded in PostgreSQL
- [ ] 9,500+ products enriched from horme.com.sg (>97%)
- [ ] Neo4j has 19,143 product nodes
- [ ] API returns real products (no mock data)
- [ ] Hybrid recommendations working (all 4 algorithms)
- [ ] Response time < 500ms for product search
- [ ] No duplicate files in codebase
- [ ] All environment variables configured
- [ ] Docker health checks passing

---

## Timeline Summary

| Step | Duration | Cumulative |
|------|----------|------------|
| 1. Cleanup | 30 min | 0.5 hr |
| 2. Configuration | 15 min | 0.75 hr |
| 3. Schema | 10 min | 1 hr |
| 4. Docker | 20 min | 1.3 hr |
| 5. Load Data | 30 min | 1.8 hr |
| 6. Web Scraping | 2-5 hr | 4-7 hr |
| 7. Neo4j | 20 min | 4.5-7.5 hr |
| 8. Verification | 30 min | 5-8 hr |

**Total: 5-8 hours** (depending on scraping speed)

---

## Next Steps After Deployment

1. **Create Admin User**:
   ```bash
   curl -X POST http://localhost:8002/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","email":"admin@horme.com","password":"<SECURE_PASSWORD>","role":"admin"}'
   ```

2. **Set Up Monitoring**: Prometheus + Grafana dashboards

3. **Configure Backups**: Automated database and Neo4j backups

4. **Load Testing**: Test with 100 concurrent users

5. **SSL/TLS**: Set up HTTPS with Let's Encrypt

6. **Frontend Integration**: Deploy Next.js frontend

---

**Deployment Status**: Ready for execution
**Support**: Check logs in `logs/` directory for issues
