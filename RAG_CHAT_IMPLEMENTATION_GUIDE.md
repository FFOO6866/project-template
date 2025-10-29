# RAG-Based AI Chat Implementation Guide

## Overview

The Horme POV AI chat has been upgraded from simple keyword matching to **Retrieval Augmented Generation (RAG)** using OpenAI embeddings and PostgreSQL pgvector for semantic search.

### What Changed

**Before (Keyword Matching):**
- Simple regex pattern matching on product names
- Limited to exact keyword matches
- No understanding of semantic meaning
- Example: "sanders for metal" would only match products with word "sanders"

**After (RAG with Semantic Search):**
- Vector embeddings capture semantic meaning
- Understands related concepts (e.g., "grinding" → "sander", "cordless" → "battery powered")
- Hybrid search combines semantic similarity + keyword matching
- AI provides context-aware recommendations based on actual product data

---

## Architecture

### Components

1. **Embedding Service** (`src/services/embedding_service.py`)
   - Generates 1536-dimensional embeddings using OpenAI text-embedding-3-small
   - Stores embeddings in PostgreSQL with pgvector extension
   - Provides semantic search and hybrid search capabilities

2. **Chat Endpoint** (`src/nexus_backend_api.py` line 1116-1252)
   - Receives user query
   - Generates query embedding
   - Performs hybrid search (70% semantic + 30% keyword)
   - Sends top 10 products to GPT-4 for intelligent response

3. **Database Layer** (`init-scripts/02-add-vector-support.sql`)
   - pgvector extension for vector operations
   - vector(1536) column for embeddings
   - IVFFlat index for fast similarity search
   - Helper functions: `find_similar_products()`, `cosine_similarity()`

### Data Flow

```
User Query
    ↓
Generate Query Embedding (OpenAI API)
    ↓
Hybrid Search:
  - 70% Semantic Similarity (vector <=> operator)
  - 30% Keyword Matching (regex patterns)
    ↓
Top 10 Matching Products
    ↓
Build Context with Product Details
    ↓
Send to GPT-4 with System Prompt
    ↓
AI-Generated Response with Product Recommendations
    ↓
Return to User
```

---

## Setup Instructions

### Prerequisites

1. **PostgreSQL with pgvector extension installed**
   ```bash
   # Check if pgvector is available
   psql -U horme_user -d horme_db -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
   ```

2. **OpenAI API Key**
   ```bash
   # Set environment variable
   export OPENAI_API_KEY='your-openai-api-key'
   ```

### Step 1: Initialize Vector Support

Run the database migration to add vector columns:

```bash
# From project root
psql -U horme_user -d horme_db -f init-scripts/02-add-vector-support.sql
```

This will:
- Enable pgvector extension
- Add `embedding vector(1536)` column to products table
- Create IVFFlat indexes for fast similarity search
- Create helper functions for semantic search

### Step 2: Generate Product Embeddings

Generate embeddings for all products in the database:

```bash
# Install dependencies
pip install openai asyncpg

# Run embedding generation script
python scripts/generate_product_embeddings.py

# Optional: Limit number of products
python scripts/generate_product_embeddings.py --limit 100

# Optional: Force regenerate existing embeddings
python scripts/generate_product_embeddings.py --force

# Optional: Custom batch size
python scripts/generate_product_embeddings.py --batch-size 50
```

**Expected Output:**
```
================================================================================
Product Embedding Generation
================================================================================
Started at: 2025-10-22T10:30:00
Database: localhost:5433/horme_db
Force regenerate: False
Batch size: 100

Connecting to database...
✅ Connected to database

📊 Current Status:
   Total products: 500
   Products with embeddings: 0
   Products without embeddings: 500
   Coverage: 0.0%
   Embedding model: text-embedding-3-small
   Embedding dimensions: 1536

🔄 Generating embeddings...
   This may take a few minutes depending on the number of products...

Batch 1: Generated and stored 100 embeddings
Batch 2: Generated and stored 100 embeddings
...

================================================================================
✅ Embedding Generation Complete!
================================================================================
Products processed: 500
Embeddings generated: 500
Status: completed
Model used: text-embedding-3-small
Dimensions: 1536

Updated coverage:
   Products with embeddings: 500
   Coverage: 100.0%

Completed at: 2025-10-22T10:35:00

🎯 Next steps:
   1. Embeddings are now available for semantic search
   2. AI chat will use vector similarity to find relevant products
   3. Test the chat with queries like:
      - 'I need sanders for metal and plastic'
      - 'What cordless drills do you have?'
      - 'Show me safety equipment'
```

### Step 3: Test the Chat

The chat endpoint is now ready with RAG capabilities!

**Frontend Usage:**
1. Open the Horme POV application
2. Navigate to chat interface
3. Try semantic queries:
   - "I need tools for sanding metal and plastic"
   - "What cordless battery-powered drills do you recommend?"
   - "Show me safety gear for construction workers"

**Backend API Testing:**
```bash
# Test via curl
curl -X POST http://localhost:8002/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need sanders for metal and plastic surfaces"
  }'
```

---

## Performance

### Embedding Generation
- **Speed**: ~100ms per product
- **Batch Processing**: 100 products per OpenAI API call
- **Estimated Time**: ~5 minutes for 1000 products

### Semantic Search
- **Query Time**: <50ms for 10,000+ products (with IVFFlat index)
- **Vector Dimension**: 1536 (OpenAI text-embedding-3-small)
- **Index Type**: IVFFlat with cosine similarity
- **Hybrid Search**: Combines semantic (70%) + keyword (30%)

### AI Response Generation
- **Model**: GPT-4
- **Max Tokens**: 800
- **Temperature**: 0.7
- **Response Time**: ~2-3 seconds

---

## Embedding Service API

### Generate Text Embedding

```python
from src.services.embedding_service import EmbeddingService

embedding_service = EmbeddingService(db_pool)
embedding = await embedding_service.generate_text_embedding("sander for metal")
# Returns: List[float] with 1536 dimensions
```

### Semantic Product Search

```python
products = await embedding_service.semantic_product_search(
    query="sanders for metal and plastic",
    limit=10,
    min_similarity=0.5  # Minimum cosine similarity threshold
)

# Returns:
# [
#   {
#     "id": 123,
#     "name": "Bosch Random Orbital Sander",
#     "description": "...",
#     "similarity_score": 0.87,
#     "price": 129.90,
#     ...
#   },
#   ...
# ]
```

### Hybrid Search (Recommended)

```python
products = await embedding_service.hybrid_search(
    query="cordless drill",
    limit=10,
    semantic_weight=0.7,  # 70% semantic similarity
    keyword_weight=0.3    # 30% keyword matching
)

# Returns products ranked by hybrid score:
# [
#   {
#     "id": 456,
#     "name": "Makita 18V Cordless Drill",
#     "semantic_score": 0.92,
#     "keyword_score": 1.0,
#     "hybrid_score": 0.944,  # (0.92 * 0.7) + (1.0 * 0.3)
#     ...
#   },
#   ...
# ]
```

### Get Embedding Statistics

```python
stats = await embedding_service.get_embedding_statistics()

# Returns:
# {
#   "total_products": 500,
#   "products_with_embeddings": 500,
#   "products_without_embeddings": 0,
#   "coverage_percentage": 100.0,
#   "embedding_model": "text-embedding-3-small",
#   "embedding_dimensions": 1536
# }
```

---

## Database Schema

### Products Table

```sql
-- Embedding column
ALTER TABLE products ADD COLUMN embedding vector(1536);

-- Index for fast similarity search
CREATE INDEX products_embedding_idx
ON products USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Helper Functions

```sql
-- Cosine similarity helper
SELECT cosine_similarity(
  product_embedding,
  query_embedding
) FROM products;

-- Find similar products
SELECT * FROM find_similar_products(
  query_embedding => '[0.1, 0.2, ...]'::vector(1536),
  limit_count => 10,
  min_similarity => 0.7
);
```

---

## Troubleshooting

### Issue: "No products found"

**Cause**: Embeddings not generated yet

**Solution**:
```bash
python scripts/generate_product_embeddings.py
```

### Issue: "OpenAI API error"

**Cause**: Missing or invalid API key

**Solution**:
```bash
export OPENAI_API_KEY='sk-your-valid-api-key'
```

### Issue: "Vector dimension mismatch"

**Cause**: Database has 384-dimensional vectors, code uses 1536

**Solution**:
```bash
# Re-run migration to update dimensions
psql -U horme_user -d horme_db -f init-scripts/02-add-vector-support.sql

# Regenerate embeddings
python scripts/generate_product_embeddings.py --force
```

### Issue: "Slow search performance"

**Cause**: Missing or outdated index

**Solution**:
```sql
-- Rebuild index
DROP INDEX IF EXISTS products_embedding_idx;
CREATE INDEX products_embedding_idx
ON products USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Analyze table for query optimization
ANALYZE products;
```

---

## Cost Considerations

### OpenAI API Costs

**text-embedding-3-small pricing** (as of 2025):
- $0.00002 per 1,000 tokens
- Average product description: ~100 tokens
- **Cost for 1,000 products**: ~$0.002 (very cheap!)

**GPT-4 pricing**:
- Input: $0.03 per 1,000 tokens
- Output: $0.06 per 1,000 tokens
- Average chat: ~500 input tokens + 300 output tokens
- **Cost per chat**: ~$0.033

**Monthly estimate** (1000 products, 1000 chats/month):
- Embeddings (one-time): $0.002
- Chat: $33/month
- **Total**: ~$33/month

---

## Next Steps

1. **Monitor Performance**
   - Track search latency
   - Monitor OpenAI API costs
   - Analyze user query patterns

2. **Optimize Embeddings**
   - Regenerate embeddings when products updated
   - Implement incremental updates
   - Add embedding generation to product creation workflow

3. **Enhance Chat**
   - Add conversation history
   - Implement user preferences
   - Add product comparison features
   - Include product images in responses

4. **Scale Considerations**
   - Consider HNSW index for >100K products
   - Implement caching for common queries
   - Add batch embedding updates

---

## Technical Details

### Vector Similarity Operators

- `<=>`: Cosine distance (used for ordering)
- `cosine_similarity(a, b)`: Returns 0-1 score (1 = identical)
- IVFFlat index: Approximate nearest neighbor search

### Embedding Model

- **Model**: text-embedding-3-small
- **Dimensions**: 1536
- **Context Window**: 8,191 tokens
- **Best for**: Short to medium text (product descriptions)

### Search Algorithms

**Semantic Search**:
```sql
ORDER BY embedding <=> query_embedding
```

**Hybrid Search**:
```sql
(semantic_score * 0.7) + (keyword_score * 0.3) AS hybrid_score
ORDER BY hybrid_score DESC
```

---

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs: `logs/api.log`
3. Test embedding service directly:
   ```bash
   python -c "
   import asyncio
   from src.services.embedding_service import EmbeddingService
   # Test code here
   "
   ```
