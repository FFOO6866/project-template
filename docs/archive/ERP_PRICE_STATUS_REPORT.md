# ERP Price Retrieval Status Report
**Date**: 2025-10-22
**System**: Horme POV Production Database

---

## 📊 Current Database Status

### Product Inventory
- **Total Products**: **19,143**
- **ERP Total**: 69,926 products available
- **Database Coverage**: 27.4% (only ~1/4 of ERP products imported)

### Price Coverage
| Metric | Count | Percentage |
|--------|-------|------------|
| Total Products | 19,143 | 100.00% |
| **With Prices** | **3,634** | **18.98%** |
| With Valid Prices (>$0) | 3,633 | 18.97% |
| **WITHOUT Prices** | **15,509** | **81.02%** ❌ |

### Enrichment Status
| Status | Count | Percentage |
|--------|-------|------------|
| Failed | 9,741 | 50.9% |
| Not Applicable | 9,302 | 48.6% |
| Not Found | 100 | 0.5% |

---

## 🚨 **CRITICAL STATUS: PRICE RETRIEVAL NOT RUNNING**

### Evidence
- ❌ No checkpoint file found (`erp_extraction_checkpoint.json`)
- ❌ No CSV output files found
- ❌ 81% of products missing prices
- ❌ 50% of products have "failed" enrichment
- ✅ Database container: **HEALTHY** (running on port 5432)

### Impact
- **AI Chat**: Can only provide recommendations for 3,634 products (19%)
- **Quotations**: Cannot generate accurate quotes for 81% of inventory
- **Product Search**: Missing price data for semantic recommendations

---

## 🛠️ Available ERP Extraction Tools

### 1. Full ERP Extraction (Recommended)
**Script**: `scripts/extract_all_erp_prices.py`

**What it does**:
- Logs into Horme ERP admin panel (https://www.horme.com.sg/admin/)
- Scrapes ALL 69,926 products across ~2,797 pages
- Extracts: SKU, Name, Price, Specifications
- Updates PostgreSQL database in real-time
- Saves backup CSV file
- Supports checkpoint/resume on interruption

**Credentials** (hardcoded):
- Username: `integrum`
- Password: `@ON2AWYH4B3`

**Timeline**:
- **Pages**: ~2,797
- **Products**: 69,926
- **Speed**: ~10-15 products/second
- **Estimated Time**: **2-4 hours**

**Command**:
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\scripts
python extract_all_erp_prices.py
```

### 2. Quick Price Update (Existing Products Only)
**Script**: `scripts/extract_targeted_prices.py`

**What it does**:
- Only updates the 19,143 products already in database
- Faster, focused extraction
- Ideal for price refresh

**Timeline**:
- **Products**: 19,143
- **Estimated Time**: **30-60 minutes**

**Command**:
```bash
python extract_targeted_prices.py --existing-only
```

### 3. Automated Extraction
**Script**: `scripts/automated_erp_extraction.py`

**What it does**:
- Fully automated, no interaction required
- Comprehensive logging
- Real-time database updates

### 4. Monitor Progress
**Script**: `scripts/monitor_extraction.py`

**What it does**:
- Monitors active extraction progress
- Reports every 5 minutes:
  - Pages processed
  - Products extracted
  - Speed (products/sec)
  - ETA for completion

**Command** (run in separate terminal):
```bash
python monitor_extraction.py
```

---

## 🚀 Recommended Action Plan

### Step 1: Prepare Environment

```bash
# Install dependencies
pip install playwright beautifulsoup4 psycopg2-binary pandas

# Install Playwright browser
playwright install chromium

# Set environment variables (if needed)
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=horme_db
set DB_USER=horme_user
set DB_PASSWORD=96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42
```

### Step 2: Run Full ERP Extraction

**Terminal 1** - Run extraction:
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\scripts
python extract_all_erp_prices.py
```

**Terminal 2** - Monitor progress:
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\scripts
python monitor_extraction.py
```

### Step 3: Generate Embeddings

After price extraction completes, generate embeddings for semantic search:

```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov

# Set OpenAI API key
set OPENAI_API_KEY=your-api-key-here

# Generate embeddings for all products
python scripts/generate_product_embeddings.py
```

**Timeline for embeddings**:
- 19k products: ~20-30 minutes
- 70k products (after full extraction): ~60-90 minutes

### Step 4: Verify Results

```bash
# Check price coverage
docker exec horme-postgres psql -U horme_user -d horme_db -c "SELECT COUNT(*) as total, COUNT(price) as with_price, ROUND(100.0 * COUNT(price) / COUNT(*), 2) as coverage FROM products;"

# Check embedding coverage
docker exec horme-postgres psql -U horme_user -d horme_db -c "SELECT COUNT(*) as total, COUNT(embedding) as with_embedding, ROUND(100.0 * COUNT(embedding) / COUNT(*), 2) as coverage FROM products;"
```

---

## 📈 Expected Results After Full Extraction

### Database Inventory
- Total Products: **69,926** (from 19,143)
- Price Coverage: **~95-100%** (from 19%)
- Embedding Coverage: **100%** (after generation)

### AI Chat Capabilities
- ✅ Full semantic search across all products
- ✅ Accurate price recommendations
- ✅ Complete product specifications
- ✅ Real-time inventory status

### Business Impact
- ✅ Complete quotation generation
- ✅ Comprehensive product recommendations
- ✅ Accurate pricing data
- ✅ Better customer experience

---

## ⚠️ Important Notes

### ERP Credentials Security
**CRITICAL**: The ERP credentials are currently **hardcoded** in the extraction scripts:
- Username: `integrum`
- Password: `@ON2AWYH4B3`

**Recommendation**: After testing, move these to environment variables:
```bash
set ERP_USERNAME=integrum
set ERP_PASSWORD=@ON2AWYH4B3
```

### Checkpoint System
The extraction supports **resume on failure**:
- Saves progress to `erp_extraction_checkpoint.json`
- If interrupted, run script again - it will resume from last page
- Can safely stop/start without losing progress

### Database Performance
During extraction:
- Database will receive ~10-15 INSERT/UPDATE per second
- Monitor disk space (CSV backup created)
- PostgreSQL should have adequate connections (check `max_connections`)

### Network Requirements
- Stable internet connection required
- Playwright runs headless Chromium browser
- ~100-200 KB per page load
- Total bandwidth: ~500 MB - 1 GB for full extraction

---

## 🔧 Troubleshooting

### Issue: "Login failed"
**Cause**: ERP credentials invalid or changed
**Solution**:
1. Verify credentials at https://www.horme.com.sg/admin/admin_login.aspx
2. Update credentials in script if needed

### Issue: "Database connection failed"
**Cause**: PostgreSQL not running or wrong credentials
**Solution**:
```bash
# Check database status
docker ps --filter "name=postgres"

# Test connection
docker exec horme-postgres psql -U horme_user -d horme_db -c "SELECT 1;"
```

### Issue: "Playwright not found"
**Cause**: Playwright browsers not installed
**Solution**:
```bash
playwright install chromium
```

### Issue: Extraction too slow
**Cause**: Network latency or rate limiting
**Solution**:
- Adjust `time.sleep()` values in script
- Run during off-peak hours
- Consider running on server closer to ERP

---

## 📊 Cost Analysis

### ERP Extraction
- **Time**: 2-4 hours (one-time)
- **Bandwidth**: ~500 MB - 1 GB
- **Cost**: FREE (using internal ERP access)

### Embedding Generation
- **API**: OpenAI text-embedding-3-small
- **Cost**: ~$0.02 per 1,000 tokens
- **Products**: 70,000
- **Estimated Cost**: **~$0.15 - $0.30** (very cheap!)

### AI Chat (Ongoing)
- **Model**: GPT-4
- **Cost per chat**: ~$0.03
- **Monthly** (1,000 chats): ~$30

**Total Initial Setup Cost**: **$0.30 - $0.60** (embeddings only)

---

## 📞 Support

### Scripts Location
```
C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\scripts\
├── extract_all_erp_prices.py          # Full extraction
├── extract_targeted_prices.py         # Existing products only
├── automated_erp_extraction.py        # Automated version
├── monitor_extraction.py              # Progress monitor
└── generate_product_embeddings.py     # Embedding generation
```

### Logs
- Extraction logs: Console output + checkpoint file
- Database logs: `docker logs horme-postgres`
- Embedding logs: Console output

---

## ✅ Action Items Summary

1. [ ] Install dependencies (playwright, beautifulsoup4, psycopg2-binary)
2. [ ] Run full ERP extraction: `python extract_all_erp_prices.py`
3. [ ] Monitor progress: `python monitor_extraction.py`
4. [ ] Verify price coverage reaches 95%+
5. [ ] Generate embeddings: `python generate_product_embeddings.py`
6. [ ] Test AI chat with real product queries
7. [ ] Document final results

**Estimated Total Time**: 3-5 hours (mostly automated)

---

**Status**: ⚠️ **READY TO START** - All scripts and infrastructure in place, waiting for execution.
