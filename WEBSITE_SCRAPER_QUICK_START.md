# Website Price Scraper - Quick Start Guide

**Date**: 2025-10-23
**Status**: ✅ Ready to Run - Fully Automated

---

## Executive Summary

**Fuzzy Matching Result**: **0 matches** found between ERP CSV and database
- ERP products (cutting wheels) ≠ Database products (bins, wipers, safety)
- **ERP CSV is completely unusable** for current database

**Solution**: SKU-based website scraping from horme.com.sg

---

## The Scraper: `scrape_website_by_sku_search.py`

### Key Features

✅ **Fully Automated** - Runs continuously until all products processed
✅ **Auto-Login** - Uses your credentials automatically
✅ **SKU Search** - Searches by product SKU (not broken catalogue IDs)
✅ **Multiple Price Extraction Methods** - JSON-LD, meta tags, CSS selectors
✅ **Real-Time Database Updates** - Prices saved immediately
✅ **Checkpoint System** - Saves progress every 10 products
✅ **Resume Capability** - Can stop/restart anytime
✅ **Progress Tracking** - Shows ETA and success rate
✅ **Headless Mode** - Can run invisible in background

---

## Quick Start (Recommended)

### Option 1: Visible Browser (Watch It Work)

```bash
cd scripts
python scrape_website_by_sku_search.py
```

**What happens:**
- Browser opens (you can see it)
- Logs into horme.com.sg
- Processes 50 products per batch
- Shows progress every batch
- Runs until complete (6-8 hours)

### Option 2: Headless Mode (Overnight/Background)

```bash
cd scripts
python scrape_website_by_sku_search.py --headless
```

**What happens:**
- Browser runs invisibly
- Perfect for overnight scraping
- Same features, no visual window
- Check progress in terminal output

---

## What to Expect

### Performance Estimates

| Metric | Estimate |
|--------|----------|
| **Total Products** | 15,509 |
| **Batch Size** | 50 products |
| **Total Batches** | ~310 batches |
| **Time per Product** | ~2-3 seconds |
| **Total Time** | 6-8 hours |
| **Success Rate** | 30-60% |
| **Expected Prices** | 4,500-9,000 |

### Progress Output

You'll see updates like this:

```
[BATCH] Loaded 50 products (IDs: 1 to 50)

[1/50] SKU: 050001101 | WINDOW WIPER 8"...
  [OK] Price found: S$15.50

[2/50] SKU: 050000101 | MOBILE BIN WITH WHEELS-120LTR...
  [OK] Price found: S$89.90

...

[CHECKPOINT] Saved at product 10
  Progress: 10 processed, 7 prices found

[PROGRESS] Total processed: 50
           Prices found: 35
           Success rate: 70.0%
           Time elapsed: 2.5 minutes
           Est. completion: 7.5 hours (450 minutes)

[INFO] Waiting 5 seconds before next batch...
```

---

## Monitoring Progress

### Check Database Coverage (In Another Terminal)

```bash
docker exec horme-postgres psql -U horme_user -d horme_db -c "
SELECT
    COUNT(*) as total,
    COUNT(price) as with_price,
    ROUND(100.0 * COUNT(price) / COUNT(*), 2) as coverage
FROM products;"
```

### Check Checkpoint File

```bash
cd scripts
type website_sku_scraping_checkpoint.json
```

Shows:
- Last processed product ID
- Total products processed
- Prices found
- Success rate

---

## Resume After Interruption

If the scraper stops (computer restart, error, manual stop):

```bash
cd scripts
python scrape_website_by_sku_search.py
```

It will **automatically resume** from the last checkpoint!

---

## Troubleshooting

### Issue: "Login Failed"

**Solution**:
- Check credentials in script are correct
- Try running in visible mode (not headless) to see what's happening
- Website may have changed login flow

### Issue: "Search box not found"

**Solution**:
- Website structure may have changed
- Run in visible mode to see page
- May need to update selectors in script

### Issue: Low Success Rate (<20%)

**Possible Causes**:
- Products not available on website
- Search not finding products
- Price extraction failing

**Solution**:
- Let it run for 100+ products first
- Check what pages are being loaded (visible mode)
- May need to adjust search/extraction logic

### Issue: Script Hangs

**Solution**:
1. Press Ctrl+C to stop
2. Check checkpoint file (progress is saved)
3. Run script again (will resume)

---

## Expected Final Results

### Scenario 1: Optimistic (60% success rate)

```
Before Scraping:
  Total: 19,143 products
  With prices: 3,634 (19%)

After Scraping:
  Total: 19,143 products
  With prices: 12,900 (67%)  ← +9,266 new prices
```

### Scenario 2: Realistic (45% success rate)

```
Before Scraping:
  Total: 19,143 products
  With prices: 3,634 (19%)

After Scraping:
  Total: 19,143 products
  With prices: 10,600 (55%)  ← +6,966 new prices
```

### Scenario 3: Conservative (30% success rate)

```
Before Scraping:
  Total: 19,143 products
  With prices: 3,634 (19%)

After Scraping:
  Total: 19,143 products
  With prices: 8,300 (43%)  ← +4,666 new prices
```

All scenarios are **acceptable for production** (>40% coverage).

---

## After Scraping Completes

### 1. Verify Results

```bash
docker exec horme-postgres psql -U horme_user -d horme_db -c "
SELECT
    COUNT(*) as total,
    COUNT(price) as with_price,
    COUNT(CASE WHEN price > 0 THEN 1 END) as with_nonzero_price,
    ROUND(100.0 * COUNT(price) / COUNT(*), 2) as coverage,
    MIN(price) as min_price,
    MAX(price) as max_price,
    ROUND(AVG(price), 2) as avg_price
FROM products;"
```

### 2. Generate Embeddings (For AI Chat)

```bash
cd scripts
python generate_product_embeddings.py
```

**Time**: 20-30 minutes
**Cost**: ~$0.05 (OpenAI embedding API)

### 3. Test Quotation System

```bash
curl -X POST http://localhost:8000/api/quotations \
  -H "Content-Type: application/json" \
  -d '{
    "document": "test_rfp.txt",
    "customer": "Test Customer"
  }'
```

Should now return quotations with **real prices**!

---

## Technical Details

### How It Works

1. **Login Phase**:
   - Navigates to horme.com.sg
   - Finds login link/form (multiple strategies)
   - Fills credentials
   - Submits and verifies login

2. **Search Phase** (per product):
   - Finds search box on page
   - Enters product SKU
   - Submits search (Enter key)
   - Waits for results

3. **Extraction Phase**:
   - Checks JSON-LD structured data
   - Checks meta tags
   - Checks price CSS selectors
   - Checks data attributes
   - Returns first valid price found

4. **Update Phase**:
   - Updates product in database
   - Saves checkpoint
   - Continues to next product

### Checkpointing

Checkpoint saved every 10 products:

```json
{
  "last_product_id": 150,
  "timestamp": 1729650000.0,
  "stats": {
    "products_processed": 150,
    "prices_found": 95,
    "products_updated": 95,
    "not_found": 42,
    "errors": 13,
    "start_time": 1729640000.0
  }
}
```

### Price Extraction Methods

**Priority Order**:

1. **JSON-LD** (most reliable)
   - Structured data in `<script type="application/ld+json">`
   - Standard e-commerce format

2. **Meta Tags**
   - `<meta property="product:price:amount">`
   - OpenGraph pricing data

3. **CSS Selectors**
   - `.price`, `.product-price`, `[class*="price"]`
   - Common e-commerce patterns

4. **Data Attributes**
   - `data-price-amount`
   - Programmatic price storage

---

## Command Reference

```bash
# Run with visible browser
python scrape_website_by_sku_search.py

# Run headless (background)
python scrape_website_by_sku_search.py --headless

# Check database coverage
docker exec horme-postgres psql -U horme_user -d horme_db -c "SELECT COUNT(*) as total, COUNT(price) as with_price FROM products;"

# View checkpoint
cat website_sku_scraping_checkpoint.json

# Resume after interruption
python scrape_website_by_sku_search.py  # (auto-resumes)
```

---

## Configuration

Edit these constants in the script if needed:

```python
# Website credentials
WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

# Scraping configuration
BATCH_SIZE = 50            # Products per batch
REQUEST_DELAY = 2          # Seconds between requests
MAX_RETRIES = 3            # Retry attempts per product
```

---

## Files Created

```
scripts/
├── scrape_website_by_sku_search.py          # Main scraper (AUTOMATED)
├── website_sku_scraping_checkpoint.json     # Progress checkpoint
├── fuzzy_match_erp_to_database.py          # ERP matching (0 results)
└── erp_product_prices.csv                   # ERP data (unusable)
```

---

## Next Steps

1. **Start the scraper** (choose visible or headless mode)
2. **Let it run** (6-8 hours, can run overnight)
3. **Monitor progress** (terminal output + database queries)
4. **Verify results** (check final coverage)
5. **Generate embeddings** (for AI chat functionality)
6. **Test quotation system** (with real prices!)

---

## Success Criteria

✅ **Minimum Acceptable**: 40% price coverage (7,600+ products)
✅ **Good Result**: 50% price coverage (9,500+ products)
✅ **Excellent Result**: 60%+ price coverage (11,500+ products)

Current: **19% coverage** (3,634 products)
Target: **40-60% coverage** (7,600-11,500 products)

---

## Ready to Start?

```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\scripts
python scrape_website_by_sku_search.py
```

**Good luck! The scraper will take care of everything automatically.**

---

**Last Updated**: 2025-10-23T02:45:00+08:00
