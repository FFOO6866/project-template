# AI Model Configuration Quick Reference

## Environment Variables

Add these to `.env.production` before deployment:

```bash
# OpenAI API Configuration
OPENAI_TIMEOUT=120
OPENAI_MAX_RETRIES=3

# Embedding Model (SentenceTransformer)
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Intent Classification
INTENT_CLASSIFIER_MODEL_PATH=/app/models/intent_classifier
INTENT_TRAINING_DATA_PATH=/app/src/intent_classification/training_data.json

# SQLite Migration
SQLITE_DATA_DIR=/app
```

## Deployment Commands

### Build Containers
```bash
# Rebuild PostgreSQL with pgvector
docker-compose -f docker-compose.production.yml build postgres

# Rebuild API with pre-downloaded models
docker-compose -f docker-compose.production.yml build api

# Start all services
docker-compose -f docker-compose.production.yml up -d
```

### Verify Installation
```bash
# Check pgvector extension
docker exec horme-postgres psql -U horme_user -d horme_db -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

# Check vector columns
docker exec horme-postgres psql -U horme_user -d horme_db -c "\d products"

# Check similarity functions
docker exec horme-postgres psql -U horme_user -d horme_db -c "SELECT proname FROM pg_proc WHERE proname LIKE '%similar%';"
```

## Semantic Search Usage

### Find Similar Products
```sql
SELECT * FROM find_similar_products(
    '[0.1, 0.2, ..., 0.384]'::vector(384),  -- Query embedding
    10,                                       -- Limit
    0.7                                       -- Min similarity threshold
);
```

### Find Similar Work Recommendations
```sql
SELECT * FROM find_similar_work_recommendations(
    '[0.1, 0.2, ..., 0.384]'::vector(384),
    10,
    0.6
);
```

### Manual Similarity Check
```sql
SELECT
    name,
    cosine_similarity(embedding, '[0.1, 0.2, ...]'::vector(384)) as similarity
FROM products
WHERE embedding IS NOT NULL
ORDER BY similarity DESC
LIMIT 10;
```

## Python Usage

### Generate Embeddings
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("product description")
# embedding is numpy array of shape (384,)
```

### Store in Database
```python
import psycopg2
from psycopg2.extensions import register_adapter, AsIs
import numpy as np

# Adapt numpy array to PostgreSQL array
def adapt_numpy_array(numpy_array):
    return AsIs(f"'{numpy_array.tolist()}'::vector")

register_adapter(np.ndarray, adapt_numpy_array)

# Insert with embedding
cursor.execute(
    "UPDATE products SET embedding = %s WHERE id = %s",
    (embedding, product_id)
)
```

### Query Similar Items
```python
# Get embedding for query
query_embedding = model.encode("looking for power drill")

# Find similar products
cursor.execute(
    "SELECT * FROM find_similar_products(%s::vector(384), %s, %s)",
    (query_embedding.tolist(), 10, 0.7)
)
results = cursor.fetchall()
```

## Troubleshooting

### pgvector Extension Missing
```bash
# Check if extension exists
docker exec horme-postgres ls -la /usr/local/share/postgresql/extension/ | grep vector

# If missing, rebuild postgres container
docker-compose -f docker-compose.production.yml build postgres --no-cache
docker-compose -f docker-compose.production.yml up -d postgres
```

### Models Not Downloaded
```bash
# Check model cache in container
docker exec horme-api ls -la /root/.cache/torch/sentence_transformers/

# If missing, rebuild API container
docker-compose -f docker-compose.production.yml build api --no-cache
docker-compose -f docker-compose.production.yml up -d api
```

### Vector Column Missing
```bash
# Run vector support script manually
docker exec -i horme-postgres psql -U horme_user -d horme_db < init-scripts/02-add-vector-support.sql
```

### Environment Variables Not Loading
```bash
# Check if .env.production is being loaded
docker-compose -f docker-compose.production.yml config

# Verify env vars in running container
docker exec horme-api env | grep EMBEDDING
```

## Performance Tuning

### Vector Index Optimization
```sql
-- Adjust IVFFLAT lists based on dataset size
-- Rule of thumb: lists = sqrt(total_rows)

-- For 10,000 products
CREATE INDEX products_embedding_idx
ON products USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- For 100,000 products
CREATE INDEX products_embedding_idx
ON products USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 316);
```

### Query Performance
```sql
-- Use EXPLAIN ANALYZE to check query performance
EXPLAIN ANALYZE
SELECT * FROM find_similar_products('[...]'::vector(384), 10, 0.7);
```

## Common Patterns

### Batch Embedding Generation
```python
from sentence_transformers import SentenceTransformer
import psycopg2

model = SentenceTransformer('all-MiniLM-L6-v2')

# Fetch products without embeddings
cursor.execute("SELECT id, description FROM products WHERE embedding IS NULL LIMIT 100")
products = cursor.fetchall()

# Generate embeddings in batch
descriptions = [p[1] for p in products]
embeddings = model.encode(descriptions, batch_size=32, show_progress_bar=True)

# Update database
for (product_id, _), embedding in zip(products, embeddings):
    cursor.execute(
        "UPDATE products SET embedding = %s WHERE id = %s",
        (embedding.tolist(), product_id)
    )
connection.commit()
```

### Hybrid Search (Keyword + Semantic)
```sql
-- Combine full-text search with semantic search
SELECT
    p.*,
    ts_rank(to_tsvector('english', description), query) as text_score,
    cosine_similarity(embedding, $1::vector(384)) as semantic_score,
    (ts_rank(to_tsvector('english', description), query) * 0.3 +
     cosine_similarity(embedding, $1::vector(384)) * 0.7) as combined_score
FROM
    products p,
    plainto_tsquery('english', $2) query
WHERE
    to_tsvector('english', description) @@ query
    OR cosine_similarity(embedding, $1::vector(384)) > 0.5
ORDER BY combined_score DESC
LIMIT 20;
```

## Files Reference

### Configuration Files
- `.env.production` - Environment variables
- `docker-compose.production.yml` - Service orchestration

### Docker Files
- `Dockerfile.postgres` - PostgreSQL with pgvector
- `Dockerfile.api` - API with pre-downloaded models

### SQL Scripts
- `init-scripts/02-add-vector-support.sql` - Vector extension setup

### Python Scripts
- `scripts/download_models.py` - Pre-download AI models
- `scripts/validate_ai_model_config.py` - Validation script

### Source Code
- `src/intent_classification/intent_classifier.py` - Intent classification
- `src/ai/hybrid_recommendation_engine.py` - Recommendation system
- `src/knowledge_graph/search.py` - Semantic search

---

**Last Updated:** 2025-10-18
**Version:** 1.0
