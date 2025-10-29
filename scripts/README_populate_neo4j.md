# Neo4j Knowledge Graph Population Script

## Overview

`populate_neo4j_graph.py` is a production-ready script that loads product relationships from PostgreSQL into Neo4j knowledge graph for the Horme POV Enterprise AI Recommendation System.

## Features

✅ **Complete Data Migration**
- Fetches all 19,143 products from PostgreSQL
- Creates Product nodes with full properties (id, sku, name, category, brand, description)
- Creates Category and Brand nodes with relationships
- Generates product similarity edges based on category matching
- Creates task-product recommendation relationships

✅ **Production Standards**
- Batch processing (1000 products at a time) for performance
- Comprehensive error handling with fail-fast
- Transaction-based operations for data consistency
- Progress logging with real-time metrics
- Idempotent design (safe to run multiple times)
- NO mock/fallback data - real connections only
- NO hardcoded credentials - uses environment variables

✅ **Performance Optimized**
- Creates indexes and constraints before data load
- Bulk operations for product nodes
- Efficient relationship creation
- Typical runtime: 2-5 minutes for full dataset

## Prerequisites

### 1. PostgreSQL Database
- Products must be loaded (19,143 products)
- Run product import first: `python scripts/import_excel_to_database.py`

### 2. Neo4j Instance
- Neo4j 5.x or later running
- Sufficient memory for graph operations (2GB+ recommended)

### 3. Environment Variables
Required in `.env.production`:

```bash
# PostgreSQL Configuration
DATABASE_URL=postgresql://user:password@postgres:5432/horme_db

# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
NEO4J_DATABASE=neo4j
```

## Usage

### Basic Usage

```bash
# Run the script
python scripts/populate_neo4j_graph.py
```

### Docker Container Usage

```bash
# Run inside API container
docker exec -it horme-api python scripts/populate_neo4j_graph.py

# Or using docker-compose
docker-compose exec api python scripts/populate_neo4j_graph.py
```

## What Gets Created

### 1. Product Nodes (19,143)
```cypher
(p:Product {
  id: 1,
  sku: "SKU-12345",
  name: "Cordless Drill",
  category: "18 - Tools",
  brand: "Bosch",
  description: "Professional cordless drill with battery",
  keywords: ["drill", "cordless", "power tool"]
})
```

### 2. Category Nodes (~50)
```cypher
(c:Category {
  id: 1,
  name: "18 - Tools",
  slug: "18-tools"
})

(p:Product)-[:IN_CATEGORY]->(c:Category)
```

### 3. Brand Nodes (~200)
```cypher
(b:Brand {
  id: 1,
  name: "Bosch",
  slug: "bosch"
})

(p:Product)-[:OF_BRAND]->(b:Brand)
```

### 4. Task Nodes (7)
```cypher
(t:Task {
  id: "task_drill_hole",
  name: "Drill Hole in Material",
  description: "Drilling holes in various materials",
  category: "drilling",
  skill_level: "beginner",
  estimated_time_minutes: 15
})
```

### 5. Product Similarity Edges (~50,000)
```cypher
(p1:Product)-[:SIMILAR_TO {
  similarity_score: 0.85,
  reason: "same_category",
  created_at: datetime()
}]->(p2:Product)
```

### 6. Task-Product Relationships (~10,000)
```cypher
(p:Product)-[:USED_FOR {
  necessity: "required",  // required, recommended, or optional
  usage_notes: "Used for drilling holes"
}]->(t:Task)
```

## Performance Metrics

Typical execution times on production hardware:

| Step | Time | Details |
|------|------|---------|
| Connection Validation | 1-2s | PostgreSQL + Neo4j |
| Product Fetch | 5-10s | 19,143 products from PostgreSQL |
| Index Creation | 2-3s | Constraints and indexes |
| Product Nodes | 60-90s | Batch creation (1000/batch) |
| Category Nodes | 5-10s | ~50 categories |
| Brand Nodes | 10-15s | ~200 brands |
| Task Nodes | 1s | 7 tasks |
| Similarity Edges | 30-60s | ~50,000 edges |
| Task Relationships | 20-40s | ~10,000 relationships |
| **Total** | **2-5 min** | Complete graph population |

## Output Example

```
================================================================================
Starting Neo4j Knowledge Graph Population
================================================================================

[Step 1/8] Validating database connections...
✅ PostgreSQL connection verified
✅ Neo4j connection verified

[Step 2/8] Initializing database connections...

[Step 3/8] Fetching products from PostgreSQL...
✅ Fetched 19143 products from PostgreSQL
Found 19143 products to sync

[Step 4/8] Creating indexes and constraints...
✅ Created indexes and constraints

[Step 5/8] Creating product nodes...
Processing batch 1/20 (1000 products)...
✅ Created 1000 product nodes
Processing batch 2/20 (1000 products)...
✅ Created 1000 product nodes
...
✅ Total products created: 19143 (failed: 0)

[Step 6/8] Creating category and brand nodes...
✅ Created 52 category nodes with relationships
✅ Created 203 brand nodes with relationships

[Step 7/8] Creating task nodes...
✅ Created 7 task nodes

[Step 8/8] Creating relationships...
✅ Created 48523 product similarity edges
✅ Created 9847 task-product relationships

================================================================================
Neo4j Knowledge Graph Population Complete!
================================================================================
Products created:        19143
Categories created:      52
Brands created:          203
Tasks created:           7
Similarity edges:        48523
Task relationships:      9847
Total time:              187.45s
================================================================================

Final Neo4j Graph Statistics:
Total nodes:             19405
Total relationships:     78413
```

## Error Handling

The script follows **fail-fast** principles:

### Connection Errors
```
❌ PostgreSQL connection failed: could not connect to server
RuntimeError: Cannot connect to PostgreSQL: connection refused
```

**Solution**: Ensure PostgreSQL is running and DATABASE_URL is correct

### No Products Found
```
❌ No products found in PostgreSQL
RuntimeError: Product fetch failed: No products to sync
```

**Solution**: Run product import first: `python scripts/import_excel_to_database.py`

### Neo4j Connection Failed
```
❌ Neo4j connection failed: ServiceUnavailable
RuntimeError: Cannot connect to Neo4j: connection refused
```

**Solution**: Ensure Neo4j is running and NEO4J_URI is correct

## Idempotency

The script is **idempotent** and safe to run multiple times:

- Uses `MERGE` instead of `CREATE` for nodes
- Relationship creation checks for existing relationships
- Indexes use `IF NOT EXISTS` clause
- No data duplication on re-runs

## Verification

After running, verify the graph state:

```bash
# Run verification script
python scripts/verify_neo4j_population.py

# Or use Neo4j Browser
# Connect to http://localhost:7474
# Run: MATCH (n) RETURN labels(n) as NodeType, count(n) as Count
```

Expected counts:
- Product nodes: 19,143
- Category nodes: ~50
- Brand nodes: ~200
- Task nodes: 7
- Total nodes: ~19,400
- Total relationships: ~78,000

## Troubleshooting

### Out of Memory Errors

If Neo4j runs out of memory:

1. Reduce `BATCH_SIZE` in script (from 1000 to 500)
2. Increase Neo4j heap size in neo4j.conf:
   ```
   dbms.memory.heap.initial_size=2g
   dbms.memory.heap.max_size=4g
   ```

### Slow Performance

If population is slow:

1. Check Neo4j is using SSD storage
2. Ensure network latency is low (same Docker network)
3. Monitor system resources during execution

### Partial Completion

If script fails mid-execution:

1. Check logs for specific error
2. Fix the issue
3. Re-run script (idempotent design will resume)

## Related Scripts

- `scripts/import_excel_to_database.py` - Load products into PostgreSQL first
- `scripts/verify_neo4j_population.py` - Verify graph population
- `scripts/load_category_task_mappings.py` - Load task mappings

## Production Deployment

For production deployment:

1. Run during off-peak hours (initial load)
2. Monitor memory and CPU usage
3. Verify graph statistics after completion
4. Run verification script
5. Test recommendation queries

## Support

For issues or questions:
- Check logs: `cat logs/neo4j_population.log`
- Review error messages in console output
- Consult Neo4j docs: https://neo4j.com/docs/
- Check PostgreSQL connection: `python scripts/test_database_connection.py`
