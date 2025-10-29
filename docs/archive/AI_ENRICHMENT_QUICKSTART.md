# 🤖 AI-Powered Product Enrichment - Quick Start Guide

## Problem Solved

Docker containers cannot reach horme.com.sg (blocked by firewall/Cloudflare), but the host machine can. This script runs on your host computer with full web access while connecting to the Docker database.

## Prerequisites

1. **Python 3.9+** installed on host machine
2. **Docker services running** (database must be accessible on localhost:10620)
3. **OpenAI API Key** configured

## Installation (One-Time Setup)

### Step 1: Install Dependencies

```bash
# Install required packages
pip install psycopg2-binary playwright openai beautifulsoup4

# Install Playwright browsers
python -m playwright install chromium
```

### Step 2: Set Environment Variables

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"
$env:DB_HOST="localhost"
$env:DB_PORT="10620"
$env:DB_NAME="horme_db"
$env:DB_USER="horme_user"
$env:DB_PASSWORD="horme_password"

# Windows (CMD)
set OPENAI_API_KEY=your-api-key-here
set DB_HOST=localhost
set DB_PORT=10620
set DB_NAME=horme_db
set DB_USER=horme_user
set DB_PASSWORD=horme_password

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
export DB_HOST="localhost"
export DB_PORT="10620"
export DB_NAME="horme_db"
export DB_USER="horme_user"
export DB_PASSWORD="horme_password"
```

## Running the Enrichment

### Quick Test (100 products)

```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov
python scripts\ai_enrichment_host.py
```

### Full Enrichment (All products)

```bash
# Process 1000 products at a time
set BATCH_SIZE=1000
python scripts\ai_enrichment_host.py

# Run multiple times until all products are enriched
```

## Configuration Options

Set these environment variables to customize behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `BATCH_SIZE` | 100 | Number of products to process per run |
| `MAX_CONCURRENT` | 5 | Concurrent browser instances |
| `CONFIDENCE_THRESHOLD` | 0.7 | Minimum AI confidence for match (0.0-1.0) |
| `OPENAI_API_KEY` | Required | Your OpenAI API key |
| `DB_HOST` | localhost | Database host |
| `DB_PORT` | 10620 | Database port (mapped from Docker) |

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    HOST MACHINE                         │
│                                                         │
│  1. Python Script (ai_enrichment_host.py)               │
│     ├─ Playwright Browser (Chrome)                     │
│     │  └─ Access horme.com.sg ✓ (no Docker blocking)   │
│     │                                                   │
│     ├─ OpenAI GPT-4                                     │
│     │  └─ Intelligent product matching                 │
│     │                                                   │
│     └─ PostgreSQL Client                                │
│        └─ Connect to localhost:10620                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Port 10620
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  DOCKER CONTAINER                       │
│                                                         │
│  PostgreSQL Database                                    │
│  └─ products table (19,143 products)                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Expected Output

```
================================================================================
AI-POWERED PRODUCT ENRICHMENT - HOST VERSION
================================================================================
Database: localhost:10620/horme_db
Batch size: 100
Max concurrent: 5
Confidence threshold: 0.7
================================================================================

Found 100 products to enrich
================================================================================

[1] Processing: 0500000694 - CORDLESS DRILL 9.6V...
  Search query: 'MAKITA CORDLESS DRILL 9.6V'
  ✓ MATCHED - Price: SGD 189.00 (confidence: 0.92)

[2] Processing: 0500000791 - SAFETY HELMET BLUE...
  Search query: '3M SAFETY HELMET BLUE'
  ✓ MATCHED - Price: SGD 45.50 (confidence: 0.88)

[3] Processing: 0500000854 - CLEANING SOLUTION 5L...
  Search query: 'CLEANING SOLUTION 5L'
  ✗ NOT FOUND - No confident match (confidence: 0.45)

...

================================================================================
ENRICHMENT COMPLETE
================================================================================
Processed:        100
Matched:          78
Prices Extracted: 78
Not Found:        22
Errors:           0
================================================================================
```

## Estimated Costs & Timeline

### For 19,143 Products

**OpenAI API Costs** (GPT-4 Turbo):
- ~$0.01-0.03 per product
- Total: **$190-575** (one-time cost)

**Time Required**:
- ~10-15 seconds per product (including AI analysis)
- Total: **~50-80 hours** (can run in background)

**Recommended Approach**:
Run in batches overnight:
```bash
# Day 1: First 1000 products
set BATCH_SIZE=1000
python scripts\ai_enrichment_host.py

# Day 2: Next 1000 products
python scripts\ai_enrichment_host.py

# Continue until complete...
```

## Success Metrics

After running enrichment, check database:

```bash
docker exec horme-postgres psql -U horme_user -d horme_db -c "
SELECT
    COUNT(*) as total_products,
    COUNT(price) as products_with_price,
    ROUND(AVG(price), 2) as avg_price,
    COUNT(*) FILTER (WHERE enrichment_status = 'completed') as enriched,
    COUNT(*) FILTER (WHERE enrichment_status = 'not_found') as not_found
FROM products;
"
```

Expected results after successful enrichment:
```
 total_products | products_with_price | avg_price | enriched | not_found
----------------+---------------------+-----------+----------+-----------
         19,143 |              15,000 |    125.50 |   15,000 |     4,143
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'playwright'"
```bash
pip install playwright
python -m playwright install chromium
```

### "psycopg2.OperationalError: could not connect to server"
- Ensure Docker containers are running: `docker ps`
- Check database port is mapped: `docker port horme-postgres`
- Verify port 10620 is accessible: `telnet localhost 10620`

### "openai.AuthenticationError"
- Ensure OPENAI_API_KEY is set correctly
- Verify API key is valid: https://platform.openai.com/api-keys

### "Page.goto: net::ERR_CONNECTION_REFUSED"
- This should NOT happen on host machine
- If it does, check your internet connection
- Try accessing https://www.horme.com.sg in browser

## Next Steps After Enrichment

1. **Verify quotations have prices**:
   ```bash
   docker exec horme-api python scripts/test_quotation_generation.py
   ```

2. **Test end-to-end workflow**:
   - Upload RFP document
   - Check generated quotation shows real prices

3. **Deploy to production**:
   - All prices populated ✓
   - System ready for real customers ✓

## Alternative: Get Price List from Horme

If AI enrichment is too slow or expensive:

1. **Contact Horme** and request price list (Excel/CSV)
2. **Import directly** using simple script (30 minutes vs 50 hours)
3. **100% accuracy** vs 70-85% AI accuracy

Both approaches work - choose based on:
- **Time**: Import = 30 min, AI = 50 hours
- **Cost**: Import = Free, AI = $190-575
- **Accuracy**: Import = 100%, AI = 70-85%
- **Coverage**: Import = depends on list, AI = best effort

## Support

Created: 2025-10-22
Status: READY FOR TESTING
