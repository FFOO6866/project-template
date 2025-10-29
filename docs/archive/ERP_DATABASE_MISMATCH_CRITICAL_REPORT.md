# CRITICAL: ERP-Database Product Catalog Mismatch

**Date**: 2025-10-22
**Status**: 🚨 **EXTRACTION STOPPED - Zero Product Matches Found**

---

## 🔴 CRITICAL FINDING

The ERP system and the database contain **completely different product catalogs** with **ZERO overlap**.

### Evidence

#### Database Products (19,143 total)
**SKU Prefix Distribution**:
- `05-series`: 3,992 products (21%)
- `21-series`: 9,936 products (52%)
- `09-series`: 5,161 products (27%)
- `01-series`: **0 products (0%)**

**Example Database Products**:
```
SKU: 050001101 | Name: WINDOW WIPER 8" | Price: NULL
SKU: 050000101 | Name: MOBILE BIN WITH WHEELS-120LTR | Price: NULL
SKU: 050000102 | Name: MOBILE BIN WITH WHEELS-240LTR | Price: NULL
```

#### ERP Products (Extracted from Admin Portal)
**SKU Prefix Distribution** (from 110 pages extracted):
- `01-series`: 2,750 products (100%)
- `05-series`: **0 products (0%)**
- `21-series`: **0 products (0%)**
- `09-series`: **0 products (0%)**

**Example ERP Products**:
```
SKU: 0100000079 | Name: MITZUNO CUT OFF WHEEL 14" | Price: $5.00
SKU: 010000008 | Name: CUT OFF WHEEL 100*1.2*16 - LICON | Price: $0.56
SKU: 010000009 | Name: CUT OFF WHEEL 100*1.2*16 - LICON | Price: $0.51
```

---

## ❌ Why Extraction Failed

### Problem
After extracting **2,750 products with prices** from the ERP:
- **Products updated in database**: **0**
- **Products not found in database**: **2,750**

### Root Cause
The database and ERP contain **different product catalogs**:

| Category | Database | ERP |
|----------|----------|-----|
| Product Type | Bins, Wipers, Industrial Supplies | Cutting Wheels, Grinding Tools |
| SKU Prefix | 05, 21, 09 | 01 |
| Overlap | **0%** | **0%** |
| Source | Website Scraper | ERP Admin System |

---

## 🔍 Investigation Results

### 1. Port Issue (RESOLVED)
- ✅ Fixed database port from 5434 to 5432
- ✅ Database connection now working

### 2. SKU Matching Issue (UNRESOLVED)
- ❌ **Zero SKU matches** between ERP and database
- ❌ Different product catalogs entirely
- ❌ Cannot update prices without matching products

### 3. Data Source Mismatch
The database appears to have been populated from:
- **Public website scraping** (horme.com.sg products)
- Products visible to customers

The ERP appears to contain:
- **Internal product catalog** (different categories)
- Backend inventory management
- Possibly different business units

---

## 🎯 Options to Resolve This

### Option 1: Import ALL ERP Products into Database ⭐ RECOMMENDED
**Goal**: Add the 69,926 ERP products to the database

**Pros**:
- Complete product catalog
- All products have prices
- Full ERP integration

**Cons**:
- Increases database from 19K to 89K products
- May include inactive/discontinued products
- Takes 2-3 hours to extract

**Steps**:
1. Modify extraction script to INSERT new products (not just UPDATE)
2. Continue extraction to completion
3. Merge website + ERP products in single database

**Implementation**: Create `scripts/import_erp_products.py`

---

### Option 2: Find Matching Products by Name
**Goal**: Match products by name/description instead of SKU

**Pros**:
- Uses existing database
- Only updates current products
- Faster execution

**Cons**:
- Fuzzy matching may be inaccurate
- Many products still won't match
- Requires complex matching logic

**Success Rate**: Estimated 10-30% match rate

**Implementation**: Modify update logic to use:
```sql
UPDATE products
SET price = %s
WHERE LOWER(name) LIKE LOWER(%s)
   OR LOWER(description) LIKE LOWER(%s)
```

---

### Option 3: Extract from Different ERP Pages
**Goal**: Find pages in ERP that contain 05/21/09 series products

**Pros**:
- Targets existing database products
- No schema changes needed
- Straightforward implementation

**Cons**:
- **May not exist** - ERP might not have these SKUs
- Time-consuming to search all pages
- Uncertain success

**Steps**:
1. Search ERP for products with SKU pattern `05*`, `21*`, `09*`
2. If found, extract those pages
3. Update matching products

**Risk**: High chance of failure if ERP doesn't have these products

---

### Option 4: Re-scrape Website with Price Extraction
**Goal**: Go back to original data source (website) and extract prices

**Pros**:
- Guaranteed SKU match (same source)
- Public pricing data
- No ERP dependency

**Cons**:
- Website might not show wholesale prices
- May require login/account
- Different pricing than ERP

**Implementation**: Modify `scripts/scrape_horme_product_details.py`

---

## 📊 Current Extraction Status

### Statistics (When Stopped):
- **Pages Processed**: 110 of ~2,797
- **Products Extracted**: 2,750 with prices
- **Database Updates**: 0 (zero matches)
- **CSV File**: 2,950 products saved
- **Extraction Time**: ~12 minutes

### Files Created:
- `scripts/erp_product_prices.csv` (2,950 products, all 01-series)
- `scripts/erp_extraction_checkpoint.json` (page 110)

### Resources Used:
- ERP Connection: Active (hotspot)
- Database Connection: Active (fixed port)
- Playwright Browser: Running

---

## ✅ Recommended Action Plan

### Immediate (Next 30 minutes)
1. **Decide on Option 1, 2, 3, or 4** based on business requirements
2. **Confirm product catalog strategy**:
   - Do you want ALL ERP products in database? (Option 1)
   - Or only update existing products? (Option 2/3)
3. **Verify ERP has 05/21/09 series** (if choosing Option 3)

### Short-term (Next 2-3 hours)
If **Option 1 chosen** (Import ALL ERP products):
1. Create `import_erp_products.py` script
2. Add INSERT logic for new products
3. Resume extraction from page 1
4. Let it run to completion (~2-3 hours)
5. Final database: ~89,000 products with prices

If **Option 2 chosen** (Name matching):
1. Create fuzzy name matching function
2. Run matching algorithm on CSV
3. Update database with matches
4. Document match success rate

### Long-term (Next session)
1. **Generate embeddings** for all products (including new ones)
2. **Test AI chat** with expanded product catalog
3. **Verify frontend** displays all products correctly
4. **Set up sync** between ERP and database

---

## 🚨 Critical Questions to Answer

### Business Questions:
1. **Should the database contain ALL ERP products?**
   - Yes → Option 1 (Import all 69K ERP products)
   - No → Option 2/3 (Find matching products only)

2. **Are the "05/21/09" series products in the ERP at all?**
   - Need to search ERP admin to verify
   - If not, website scraping is only option

3. **Which is the source of truth?**
   - ERP → Import all ERP products
   - Website → Re-scrape website
   - Both → Merge catalogs

### Technical Questions:
1. **Is the ERP sorted by SKU prefix?**
   - If yes, we need to navigate to pages 500-2000+ for 05/21/09 series
   - If no, we need to search

2. **Can we search ERP by SKU?**
   - Would make targeting specific products easier

---

## 📁 Files Reference

### Scripts:
- `scripts/extract_all_erp_prices.py` - Current extraction script (stopped)
- `scripts/erp_product_prices.csv` - 2,950 extracted 01-series products
- `scripts/erp_extraction_checkpoint.json` - Stopped at page 110

### Database:
- **Host**: localhost:5432 ✅ (Fixed)
- **Database**: horme_db
- **Products**: 19,143 (05/21/09 series)
- **Price Coverage**: 18.98% (3,634 with prices)

### ERP:
- **URL**: https://www.horme.com.sg/admin/
- **Login**: Working via hotspot ✅
- **Total Pages**: ~2,797
- **Total Products**: ~69,926

---

## 📞 Next Steps

**AWAITING USER DECISION**:

Please choose one of the following options:

### A. Import ALL ERP Products (Recommended)
- Complete product catalog
- All prices available
- Takes 2-3 hours
- Database grows to ~89K products

### B. Match by Product Name
- Keep current 19K products
- Update prices where names match
- Faster (30 minutes)
- Lower success rate (10-30%)

### C. Search for 05/21/09 in ERP
- Target existing products
- Uncertain if they exist in ERP
- May waste time if not found

### D. Re-scrape Website
- Match existing SKUs
- Get public pricing
- May differ from wholesale prices

---

**Status**: 🔴 **EXTRACTION STOPPED - AWAITING DECISION**
**Timestamp**: 2025-10-22T22:30:00+08:00
