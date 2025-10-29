# CRITICAL: Catalogue ID Data Quality Issue
## Date: 2025-10-23

## Executive Summary

**The scraper is working correctly**. The problem is **data quality** - the `catalogue_id` column contains a mix of:
1. ✅ **Valid product page IDs** (unique, 1 product per ID) - ~5-10%
2. ❌ **Category/listing page IDs** (shared, 6-18 products per ID) - ~90-95%

## Evidence

### Database Analysis

```sql
-- Catalogue IDs shared by many products (CATEGORY PAGES)
catalogue_id | product_count
-------------|---------------
2097         | 18 products
17063        | 16 products
8738         | 12 products
... (most IDs have 6-18 products)

-- Catalogue IDs with single products (PRODUCT PAGES - THESE WORK!)
16853        | 1 product  → Price found: S$6.06 ✅
16952        | 1 product  → Price found: S$151.25 ✅
```

### Website Verification

| Catalogue ID | URL Result | Has Price? | Shared By |
|--------------|------------|------------|-----------|
| 16853 | Product page | ✅ S$6.06 | 1 product |
| 16952 | Product page | ✅ S$151.25 | 1 product |
| 13404 | Category/listing page | ❌ No price | 6 products |
| 2280 | Category/listing page | ❌ No price | Multiple |
| 10734 | Category/listing page | ❌ No price | 4 products |

### Scraper Performance

- **Products processed**: 40
- **Prices found**: 0
- **Reason**: First 40 products all had category page IDs

## Current Database State

```sql
Total products: 19,143
With catalogue_id: 9,764 (51%)
Without prices: 15,509 (81%)

Unique catalogue_ids: ~800 (estimated)
Products per catalogue_id: Average 12 products
```

## Why This Happened

The original data import likely captured:
- **Category page IDs** for products browsed via category pages
- **Product page IDs** for products accessed directly

This created inconsistent `catalogue_id` values where most point to category listings instead of individual product pages.

## Impact on Price Scraping

### Scraping Success by ID Type

| ID Type | Count (Est) | Success Rate | Prices Obtainable |
|---------|-------------|--------------|-------------------|
| Unique product IDs | ~500-800 | ~80% | ~400-640 |
| Shared category IDs | ~9,000 | 0% | 0 |
| **TOTAL** | ~9,764 | ~5-7% | ~400-640 |

**Realistic outcome**: 400-640 prices maximum (2-3% of total database)

## Solutions

### Option 1: Scrape Only Unique Catalogue IDs ⭐ RECOMMENDED
**Impact**: 400-640 new prices
**Time**: ~30 minutes
**Success rate**: 70-80%

```sql
-- Find products with unique catalogue IDs
SELECT DISTINCT p.catalogue_id
FROM products p
WHERE p.catalogue_id IS NOT NULL
  AND p.price IS NULL
  AND (
    SELECT COUNT(*)
    FROM products p2
    WHERE p2.catalogue_id = p.catalogue_id
  ) = 1
ORDER BY p.catalogue_id;
```

### Option 2: Manual Product ID Discovery
**Impact**: Potentially all 9,764 products
**Time**: Unknown - depends on how to find correct product IDs
**Requires**: User input on how to map products to correct page IDs

Questions for user:
- Is there another source for individual product page IDs?
- Can we derive product page IDs from SKU or product_code?
- Does the website have a product search API?

### Option 3: Use Current Prices + Manual Entry
**Impact**: Keep 3,634 existing prices, manually add critical products
**Time**: Immediate for existing, variable for manual
**Best for**: Getting system working quickly

### Option 4: Alternative Price Source
- Check if Horme has an API
- Check if ERP can be mapped differently
- Check if there's a product catalog file/export

## Recommended Action Plan

### Immediate (Next 30 mins)
1. **Stop current scraper** (it's processing category pages)
2. **Run Option 1**: Scrape only unique catalogue IDs
3. **Expected result**: 400-640 new prices → Total: ~4,000-4,300 (21-22% coverage)

### Next Steps (Requires User Input)
1. **Ask user**: How were catalogue IDs originally obtained?
2. **Ask user**: Is there a way to get individual product page IDs?
3. **Evaluate**: Is 21-22% price coverage acceptable for MVP?

## Files Created During Investigation

### Working Scripts
- `scrape_by_catalogue_id.py` - Main scraper (JSON-LD extraction)
- `find_price_location.py` - Price discovery tool
- `debug_single_product.py` - Single product debugger

### Analysis Reports
- `ERP_DATABASE_MISMATCH_CRITICAL_REPORT.md`
- `WEBSITE_SCRAPING_STATUS.md`
- `FINAL_SESSION_SUMMARY_2025-10-23.md`
- `CRITICAL_CATALOGUE_ID_DATA_ISSUE.md` (this file)

## Technical Details

### Scraper Capabilities ✅
- ✅ Extracts prices from JSON-LD structured data
- ✅ Falls back to HTML element extraction
- ✅ Falls back to regex in page source
- ✅ Handles discontinued/out-of-stock products
- ✅ Checkpoint system for resume capability
- ✅ Rate limiting to respect website

### Scraper Limitations ⚠️
- ⚠️ Cannot extract prices from category/listing pages (not a scraper issue - pages don't have prices)
- ⚠️ Depends on correct catalogue_id in database

## Immediate Next Step

**DECISION REQUIRED**:

Choose option and I will execute immediately:

1. **Option 1**: Scrape ~600-800 products with unique catalogue IDs (30 mins, ~400-640 prices)
2. **Option 2**: Investigate how to get correct product IDs (requires your input)
3. **Option 3**: Stop price scraping, work with existing 3,634 prices (19% coverage)
4. **Option 4**: Explore alternative price sources

---

**Status**: ⏸️ **SCRAPER PAUSED** - Waiting for decision
**Current Coverage**: 18.98% (3,634 products)
**Maximum Achievable**: ~22-23% (4,000-4,300 products) with Option 1

**Last Updated**: 2025-10-23T23:30:00+08:00
