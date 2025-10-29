# Continue ERP Price Extraction Guide
**Date**: 2025-10-22

---

## 🎯 **Quick Start (When on Mobile Hotspot)**

```bash
# 1. Switch to mobile hotspot (NOT home WiFi!)

# 2. Navigate to scripts directory
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\scripts

# 3. Run extraction script
python extract_all_erp_prices.py
```

**The script will:**
- ✅ Auto-resume from page 1,260 (where it stopped)
- ✅ Extract remaining ~1,537 pages
- ✅ Update database in real-time with correct prices
- ✅ Save checkpoint every 10 pages
- ⏱️ Take ~1-2 hours

---

## 📊 **Current Extraction Status**

From `erp_extraction_checkpoint.json`:
```json
{
  "page_number": 1,260,
  "pages_processed": 1,260,
  "products_extracted": 18,025,
  "products_updated_in_db": 1,875,
  "products_not_in_db": 11,225
}
```

### What This Means:
- ✅ **45% Complete** (1,260 of ~2,797 pages)
- ✅ Extracted 18,025 products with prices
- ⚠️ Only 1,875 matched existing database products
- ⚠️ 11,225 products in ERP not yet in database

---

## 🔍 **Why Previous CSV Import Didn't Work**

### Problem Discovered:
The CSV has mostly different products than the database:

| Source | Total | SKU "05" Products | SKU "01" Products |
|--------|-------|-------------------|-------------------|
| **Database** | 19,143 | 3,992 (21%) | 0 (0%) |
| **CSV File** | 39,877 | 4,535 (12%) | ~35,000 (88%) |

**Database has ZERO "01" products**, so CSV couldn't match them!

---

## 🚀 **What Happens When You Continue Extraction**

### The extraction script will:

**1. Resume from Checkpoint**
- Starts at page 1,260
- Continues through remaining pages
- Processes ~10-15 products per page

**2. Match Products Two Ways**
```python
# Method A: Match by SKU
UPDATE products SET price = X WHERE sku = 'ABC123'

# Method B: Match by Name
UPDATE products SET price = X WHERE name = 'Product Name'
```

**3. Real-Time Progress**
```
Page 1260: Extracted 25 products, updated 12 in database
Page 1261: Extracted 23 products, updated 10 in database
Page 1262: Extracted 24 products, updated 15 in database
...
```

**4. Save Checkpoints**
- Every 10 pages → saves progress
- If interrupted → resume from last checkpoint
- Safe to stop/start

---

## 📈 **Expected Results After Completion**

### Current State (Before Extraction):
```
Total Products:     19,143
With Prices:        3,634 (19%)
WITHOUT Prices:     15,509 (81%) ❌
```

### After Full Extraction (~2-3 hours):
```
Total Products:     19,143 (same)
With Prices:        12,000-15,000 (60-80%) ✅
WITHOUT Prices:     4,000-7,000 (20-40%) ⬇️
```

**Improvement**: Price coverage from 19% → 60-80%

---

## 🎯 **Step-by-Step Instructions**

### Before You Start:
1. ✅ **Switch to Mobile Hotspot** (ERP blocks home WiFi)
2. ✅ **Ensure Docker is Running** (database needs to be accessible)
3. ✅ **Close unnecessary apps** (for stable connection)

### Run the Extraction:

**Terminal 1 - Main Extraction:**
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\scripts
python extract_all_erp_prices.py
```

**Terminal 2 - Monitor Progress (Optional):**
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\scripts
python monitor_extraction.py
```

### Monitor Progress:

The script will show:
```
================================================================================
HORME ERP COMPLETE PRICE EXTRACTION
================================================================================
Target: 69,926 products across ~2,797 pages

[INFO] Resuming from checkpoint: Page 1,260
[INFO] Logging into ERP...
[SUCCESS] Login successful

[PAGE 1260] Extracted 25 products | Updated: 12 | Not in DB: 13
[PAGE 1261] Extracted 23 products | Updated: 10 | Not in DB: 13
...

[CHECKPOINT] Saved progress at page 1270
[PROGRESS] Pages: 1,270/2,797 (45.4%) | Updated: 1,950 products
...
```

### If It Stops or Errors:

**Just run it again** - it will auto-resume:
```bash
python extract_all_erp_prices.py
```

---

## ⏱️ **Estimated Timeline**

### Remaining Work:
- **Pages to Process**: 1,537 (from 1,260 to 2,797)
- **Products**: ~35,000-40,000
- **Speed**: ~10-15 products/page
- **Time per Page**: 3-5 seconds

### Total Time:
- **Optimistic**: 1.5 hours (fast connection)
- **Realistic**: 2 hours (normal)
- **Conservative**: 3 hours (if slow/retries)

### Breaks:
You can stop and resume anytime:
- Script saves checkpoint every 10 pages
- Safe to close terminal
- Resume by running script again

---

## 🔧 **Troubleshooting**

### Issue: "Connection Timeout"
**Cause**: Home WiFi blocking ERP
**Solution**: Switch to mobile hotspot

### Issue: "Login Failed"
**Cause**: ERP credentials changed or session expired
**Solution**: Check credentials in script:
```python
ERP_USERNAME = "integrum"
ERP_PASSWORD = "@ON2AWYH4B3"
```

### Issue: "Database Connection Failed"
**Cause**: Docker not running
**Solution**:
```bash
docker ps | grep horme-postgres
# Should show: horme-postgres (healthy)
```

### Issue: Script Hangs on a Page
**Solution**:
1. Press `Ctrl+C` to stop
2. Run script again (will resume)
3. Script skips problematic pages automatically

---

## 📊 **Verify Results After Completion**

### Check Price Coverage:
```bash
docker exec horme-postgres psql -U horme_user -d horme_db -c "
SELECT
    COUNT(*) as total_products,
    COUNT(price) as with_prices,
    ROUND(100.0 * COUNT(price) / COUNT(*), 2) as coverage_percent
FROM products;"
```

### Expected Output:
```
total_products | with_prices | coverage_percent
---------------+-------------+------------------
19,143         | 12,000-15,000 | 60-80%
```

### Check Updated Products:
```bash
docker exec horme-postgres psql -U horme_user -d horme_db -c "
SELECT COUNT(*) as updated_today
FROM products
WHERE updated_at::date = CURRENT_DATE
AND price IS NOT NULL;"
```

---

## 🎯 **Next Steps After Extraction**

### 1. Generate Embeddings for AI Chat
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov

# Set OpenAI API key
set OPENAI_API_KEY=your-openai-api-key

# Generate embeddings
python scripts/generate_product_embeddings.py
```

**Timeline**: 20-30 minutes for 19K products
**Cost**: ~$0.05 (very cheap!)

### 2. Test AI Chat
Once embeddings are generated, test the chat:
```bash
curl -X POST http://localhost:8002/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I need sanders for metal and plastic"}'
```

Should now return real product recommendations with prices!

### 3. Verify Frontend
Open: http://localhost:3010
- Test chat interface
- Try product search
- Generate test quotation

---

## 📋 **Summary Checklist**

Before starting:
- [ ] Switch to mobile hotspot
- [ ] Verify Docker is running
- [ ] Ensure database is accessible
- [ ] Have ~2-3 hours available

During extraction:
- [ ] Monitor progress
- [ ] Check for errors
- [ ] Verify checkpoint saves

After completion:
- [ ] Verify price coverage (should be 60-80%)
- [ ] Generate embeddings
- [ ] Test AI chat
- [ ] Test frontend

---

## 🎉 **Expected Final State**

### Database:
✅ 19,143 products total
✅ 60-80% with accurate ERP prices
✅ 100% with AI embeddings
✅ Full semantic search capability

### Applications:
✅ AI Chat fully functional
✅ Product recommendations with real prices
✅ Quotation generation operational
✅ Multi-language support ready

### Performance:
✅ Semantic search <50ms
✅ Chat responses ~2-3 seconds
✅ Real-time price accuracy

---

**Ready to start? Switch to mobile hotspot and run:**
```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\scripts
python extract_all_erp_prices.py
```

**Good luck! 🚀**
