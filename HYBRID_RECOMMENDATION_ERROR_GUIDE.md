# Hybrid Recommendation Engine - Error Handling Guide

## Overview

The Hybrid Recommendation Engine uses a **FAIL-FAST** approach with NO fallback logic or simulated data. When dependencies are unavailable or data is insufficient, the system raises clear errors instead of returning neutral/hardcoded scores.

This guide explains what each error means and how to fix it.

---

## Configuration Errors

### Error: "Algorithm weights not properly configured"

**Full Message:**
```
CRITICAL: Algorithm weights not properly configured in environment variables.
Required: HYBRID_WEIGHT_COLLABORATIVE, HYBRID_WEIGHT_CONTENT_BASED,
HYBRID_WEIGHT_KNOWLEDGE_GRAPH, HYBRID_WEIGHT_LLM_ANALYSIS.
```

**Cause:** Missing or invalid algorithm weight environment variables.

**Fix:**
1. Add to `.env` file:
```bash
HYBRID_WEIGHT_COLLABORATIVE=0.25
HYBRID_WEIGHT_CONTENT_BASED=0.25
HYBRID_WEIGHT_KNOWLEDGE_GRAPH=0.30
HYBRID_WEIGHT_LLM_ANALYSIS=0.20
```

2. Ensure weights sum to 1.0 (±0.01 tolerance)

3. Restart application to load new environment variables

---

## Database Errors

### Error: "PostgreSQL connection required for collaborative filtering"

**Full Message:**
```
CRITICAL: PostgreSQL connection required for collaborative filtering: {error}.
Set DATABASE_URL environment variable or pass database_connection parameter.
```

**Cause:** PostgreSQL database not connected.

**Fix:**
1. Verify PostgreSQL is running:
```bash
docker ps | grep postgres
```

2. Check `DATABASE_URL` in `.env`:
```bash
DATABASE_URL=postgresql://horme_user:password@localhost:5433/horme_db
```

3. Test connection:
```bash
psql -U horme_user -h localhost -p 5433 -d horme_db
```

---

### Error: "Database query failed for user purchase history"

**Full Message:**
```
Database query failed for user purchase history: {error}.
Ensure PostgreSQL is running and quote_items/quotations tables exist.
Run database migrations if needed.
```

**Cause:** Missing database tables or invalid schema.

**Fix:**
1. Run database migrations:
```bash
docker exec horme-postgres psql -U horme_user -d horme_db -f /path/to/schema.sql
```

2. Verify tables exist:
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('quotations', 'quote_items');
```

3. Check table structure matches expected schema:
   - `quotations` table needs: `id`, `customer_email`, `status`
   - `quote_items` table needs: `id`, `quotation_id`, `category`, etc.

---

### Error: "No purchase history for user"

**Message:** Returns 0.0 collaborative score (not an error, but low score)

**Cause:** User has no completed quotations in database.

**Explanation:** This is expected behavior for new users. The system returns 0.0 instead of a fallback score.

**Fix (if unexpected):**
1. Verify user email in database:
```sql
SELECT * FROM quotations WHERE customer_email = 'user@example.com';
```

2. Ensure quotations have status 'accepted' or 'sent':
```sql
UPDATE quotations SET status = 'accepted' WHERE id = 'xxx';
```

---

## OpenAI API Errors

### Error: "OpenAI API key not configured"

**Full Message:**
```
CRITICAL: OpenAI API key not configured.
Set OPENAI_API_KEY environment variable to use LLM requirement extraction.
Cannot fall back to regex - that would violate production data quality standards.
```

**Cause:** Missing or invalid OpenAI API key.

**Fix:**
1. Add to `.env` file:
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
OPENAI_MODEL=gpt-4-turbo-preview
```

2. Verify API key is valid:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

3. Check API key has sufficient credits/quota

---

### Error: "OpenAI API call failed"

**Full Message:**
```
OpenAI API call failed: {error}.
Check API key validity, rate limits, and network connectivity.
Model: gpt-4-turbo-preview
```

**Cause:** API request failed (rate limit, network, invalid model, etc.)

**Fix:**
1. **Rate limit exceeded**: Wait or upgrade plan
   - Check: `x-ratelimit-remaining` in API response headers

2. **Invalid model**: Update `OPENAI_MODEL` to valid model:
   ```bash
   OPENAI_MODEL=gpt-4-turbo-preview  # or gpt-4, gpt-3.5-turbo
   ```

3. **Network issues**: Check internet connectivity
   ```bash
   curl -I https://api.openai.com
   ```

4. **Insufficient credits**: Add credits to OpenAI account

---

## Embedding Model Errors

### Error: "Sentence transformer embedding model not loaded"

**Full Message:**
```
CRITICAL: Sentence transformer embedding model not loaded.
Check that sentence-transformers is installed and model 'all-MiniLM-L6-v2' is available.
Cannot provide fallback score - embeddings are required for content-based filtering.
```

**Cause:** sentence-transformers package not installed or model download failed.

**Fix:**
1. Install sentence-transformers:
```bash
pip install sentence-transformers
```

2. Test model loading:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
```

3. If download fails, check internet connection or use alternative model:
```python
# In code, update model name
embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
```

---

## Redis Errors

### Error: "Redis cache unavailable"

**Message:** Warning (not critical error)
```
⚠️ Redis cache unavailable: {error}. Caching disabled.
```

**Cause:** Redis server not running or connection failed.

**Impact:**
- Recommendation engine still works
- Co-purchase patterns won't be available (returns 0.0 score)
- Slower performance without caching

**Fix:**
1. Start Redis:
```bash
docker-compose up -d redis
```

2. Verify Redis connection:
```bash
redis-cli -h localhost -p 6380 ping
```

3. Update `REDIS_URL` in `.env`:
```bash
REDIS_URL=redis://localhost:6380/0
```

---

## Neo4j Knowledge Graph Errors

### Error: "Neo4j query failed for product"

**Full Message:**
```
Neo4j query failed for product {id}: {error}.
Ensure Neo4j is running and knowledge graph is populated.
Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD environment variables.
```

**Cause:** Neo4j not running, wrong credentials, or empty graph.

**Fix:**
1. Start Neo4j:
```bash
docker-compose up -d neo4j
```

2. Verify credentials in `.env`:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

3. Test connection:
```bash
cypher-shell -a bolt://localhost:7687 -u neo4j -p password
```

4. Verify graph has data:
```cypher
MATCH (n) RETURN count(n);
```

5. If graph is empty, run knowledge graph population scripts

---

## Content-Based Filtering Errors

### Error: "Empty text provided for TF-IDF calculation"

**Cause:** Product has no name, description, or category.

**Fix:**
1. Check product data in database:
```sql
SELECT id, name, description, category FROM products WHERE id = 'xxx';
```

2. Ensure products have at least one text field populated

3. Update product records with missing data

---

### Error: "Product has no text content for scoring"

**Cause:** Product missing all text fields (name, description, category, brand).

**Fix:**
1. Identify products with missing data:
```sql
SELECT id FROM products
WHERE (name IS NULL OR name = '')
AND (description IS NULL OR description = '')
AND (category IS NULL OR category = '');
```

2. Update products with minimum required data:
```sql
UPDATE products
SET description = 'No description available'
WHERE description IS NULL OR description = '';
```

---

## Data Quality Errors

### Error: "No requirements extracted from RFP"

**Cause:** OpenAI returned empty requirements list from RFP text.

**Fix:**
1. Verify RFP text is not empty:
```python
print(f"RFP length: {len(rfp_text)} chars")
```

2. Check RFP contains actual requirements (not just filler text)

3. Adjust OpenAI prompt if requirements are very domain-specific

4. Verify OpenAI API key has sufficient quota

---

## Debugging Tips

### Enable Debug Logging

Add to your application:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:
```bash
LOG_LEVEL=DEBUG
```

### Check All Dependencies

Run this diagnostic script:
```python
import sys

def check_dependencies():
    errors = []

    # Check PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        print("✅ PostgreSQL: Connected")
        conn.close()
    except Exception as e:
        errors.append(f"❌ PostgreSQL: {e}")

    # Check Redis
    try:
        import redis
        r = redis.from_url(os.getenv('REDIS_URL'))
        r.ping()
        print("✅ Redis: Connected")
    except Exception as e:
        print(f"⚠️ Redis: {e} (optional)")

    # Check OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        print("✅ OpenAI: API key configured")
    except Exception as e:
        errors.append(f"❌ OpenAI: {e}")

    # Check sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embeddings: Model loaded")
    except Exception as e:
        errors.append(f"❌ Embeddings: {e}")

    # Check Neo4j
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
        driver.verify_connectivity()
        print("✅ Neo4j: Connected")
        driver.close()
    except Exception as e:
        errors.append(f"❌ Neo4j: {e}")

    if errors:
        print("\n🚨 Critical errors found:")
        for error in errors:
            print(error)
        sys.exit(1)
    else:
        print("\n✅ All dependencies OK")

check_dependencies()
```

---

## Emergency Fallback (NOT RECOMMENDED)

If you absolutely must run with missing dependencies (e.g., for testing), you can:

1. **Comment out weight validation** (NOT for production):
```python
# TEMPORARY WORKAROUND - REMOVE IN PRODUCTION
# total_weight = sum(self.weights.values())
# if not (0.99 <= total_weight <= 1.01):
#     raise ValueError(...)
```

2. **Use mock data** (NOT for production):
```python
# TEMPORARY WORKAROUND - REMOVE IN PRODUCTION
if not self.openai_client:
    logger.warning("Using mock requirements - TESTING ONLY")
    return ["mock requirement 1", "mock requirement 2"]
```

**WARNING:** These workarounds violate production data quality standards and should NEVER be deployed to production.

---

## Production Readiness Checklist

Before deploying to production, verify:

- [ ] All environment variables configured in `.env`
- [ ] PostgreSQL running with correct schema
- [ ] OpenAI API key valid with sufficient credits
- [ ] sentence-transformers model downloaded
- [ ] Neo4j running with populated knowledge graph
- [ ] Redis running (optional but recommended)
- [ ] Algorithm weights sum to 1.0
- [ ] All database tables have sample data
- [ ] Diagnostic script passes all checks

---

## Support

If you encounter errors not covered in this guide:

1. Check application logs for detailed error messages
2. Run the diagnostic script above
3. Verify all environment variables are set correctly
4. Ensure all Docker containers are running
5. Check that database schema matches expected structure

For persistent issues, review the source code error messages - they contain specific fix instructions.
