# Authenticated AI Product Enrichment - Quick Start Guide

## Overview

This solution uses **AI-powered authenticated web scraping** to extract product pricing from Horme.com.sg:

1. **Manual Login** (one-time): You log in to Horme.com.sg using your credentials
2. **Session Extraction**: Playwright captures your session cookies
3. **Automated Scraping**: AI-powered system uses your session to enrich products
4. **Price Extraction**: GPT-4 matches products and extracts pricing

## Prerequisites

- Valid Horme.com.sg account (B2B wholesale customer)
- Python 3.8+ installed
- OpenAI API key (already configured)
- Internet connection

## Step-by-Step Instructions

### Step 1: Install Playwright (Automated)

Simply run the extraction script - it will auto-install Playwright if needed:

```bash
extract_session.bat
```

**OR** install manually:

```bash
pip install playwright
playwright install chromium
```

### Step 2: Extract Session Cookies

**Method 1: Using Batch File (Easiest)**
```bash
extract_session.bat
```

**Method 2: Using Python Directly**
```bash
python scripts/extract_horme_session.py
```

**What Happens**:
1. Browser window opens automatically
2. You manually log in to Horme.com.sg
3. Navigate around to ensure you're logged in
4. Return to terminal and press Enter
5. Script extracts and saves cookies to `horme_session.json`
6. Session validated automatically

**Expected Output**:
```
================================================================================
HORME.COM.SG SESSION COOKIE EXTRACTOR
================================================================================

Launching browser...
Navigating to: https://www.horme.com.sg

================================================================================
INSTRUCTIONS:
================================================================================

1. A browser window has opened
2. Please LOG IN to your Horme.com.sg account
3. After logging in, navigate around to ensure you're authenticated
4. Return to this terminal and press Enter when done

Press Enter AFTER you have logged in successfully...

Extracting session cookies...
  Found 12 cookies
Extracting localStorage...
  Found 3 localStorage items

================================================================================
VALIDATING SESSION...
================================================================================

Testing access to: https://www.horme.com.sg/searchengine.aspx?stq=drill

[SUCCESS] Session appears to be authenticated!

Saving session to: horme_session.json
  [SAVED] Session data written to horme_session.json

================================================================================
SESSION SUMMARY
================================================================================

Cookies: 12
localStorage: 3 items
Extracted: 2025-10-22T15:30:45.123456
Validated: YES

[SUCCESS] Session is ready for automated scraping!

Next steps:
1. Run: python scripts/scraperapi_ai_enrichment_authenticated.py
2. Script will automatically use saved session
3. Monitor for session expiration
```

### Step 3: Run Authenticated Enrichment

**Method 1: Using Batch File (Easiest)**
```bash
run_authenticated_enrichment.bat
```

**Method 2: Using Python Directly**
```bash
set OPENAI_API_KEY=sk-proj-...
set BATCH_SIZE=10
python scripts/scraperapi_ai_enrichment_authenticated.py
```

**What Happens**:
1. Loads `horme_session.json`
2. Creates authenticated browser session
3. Fetches 10 products needing enrichment
4. For each product:
   - Creates fuzzy search query
   - Searches Horme.com.sg (authenticated)
   - Extracts product results
   - Uses GPT-4 to match correct product
   - Extracts price
   - Updates database
5. Prints statistics

**Expected Output**:
```
================================================================================
AUTHENTICATED SCRAPERAPI + AI PRODUCT ENRICHMENT SYSTEM
================================================================================
Database: localhost:5434/horme_db
Batch size: 10
Confidence threshold: 0.7
Session file: horme_session.json
Session extracted: 2025-10-22T15:30:45.123456
Cookies: 12
================================================================================

Found 10 products to enrich
================================================================================

[1] Processing: SKU-001
  Description: SAFETY HELMET WHITE STANDARD...
  Search query: 'SAFETY HELMET WHITE'
  Searching: https://www.horme.com.sg/searchengine.aspx?stq=SAFETY+HELMET+WHITE
  Found 7 results using selector: .product-item
  Extracted 7 product results
  Analyzing 7 results with AI...
  [MATCHED] Safety Helmet - White - Standard Size - CE Certified
  Confidence: 0.95
  Reasoning: Exact match on product type, color, and standard designation
  [PRICE FOUND] SGD 12.50

[2] Processing: SKU-002
  Description: POWER DRILL CORDLESS 18V BATTERY...
  Search query: 'POWER DRILL CORDLESS 18V'
  Searching: https://www.horme.com.sg/searchengine.aspx?stq=POWER+DRILL+CORDLESS+18V
  Found 6 results using selector: .product-item
  Extracted 6 product results
  Analyzing 6 results with AI...
  [MATCHED] Cordless Power Drill 18V with Battery Pack
  Confidence: 0.89
  Reasoning: Matches voltage specification and cordless feature
  [PRICE FOUND] SGD 189.00

...

================================================================================
ENRICHMENT COMPLETE
================================================================================
Processed:          10
Matched:            8
Prices Extracted:   8
Not Found:          2
Errors:             0

API Usage:
Playwright calls:   18
ScraperAPI calls:   0
OpenAI calls:       10
Session valid:      YES
================================================================================
```

## Troubleshooting

### Issue: Session File Not Found
```
ERROR: Session file not found: horme_session.json
```

**Solution**: Run `extract_session.bat` first

### Issue: Session Expired
```
[SESSION EXPIRED] Redirected to login page
```

**Solution**:
```bash
extract_session.bat  # Extract new session
run_authenticated_enrichment.bat  # Try again
```

### Issue: Playwright Not Installed
```
ERROR: No module named 'playwright'
```

**Solution**:
```bash
pip install playwright
playwright install chromium
```

### Issue: Authentication Failed
```
[AUTH FAILED] Login page detected - session expired
```

**Solution**:
1. Ensure you fully logged in during extraction
2. Try logging in again with `extract_session.bat`
3. Check if Horme.com.sg has CAPTCHA requirements
4. Verify your account is active

### Issue: No Products Found
```
[NOT FOUND] No search results
```

**Possible Causes**:
- Search query too specific
- Product not in Horme catalog
- Authentication issue

**Solution**: Check script output for search URL and test manually in browser

### Issue: Price Not Found
```
[PRICE NOT FOUND] Product matched but price missing
```

**Possible Causes**:
- Price only shown to logged-in members
- Price requires "Request Quote"
- HTML structure changed

**Solution**: Manually check product page to verify price visibility

## Cost Analysis

### Scenario: 10 Products (Test)
```
Playwright:         FREE (open source)
OpenAI GPT-4:       10 calls × $0.01 = $0.10
Total:              $0.10
```

### Scenario: 19,143 Products (Full Run)
```
Playwright:         FREE
OpenAI GPT-4:       19,143 × $0.01 = $191.43
Total:              $191.43
```

**Time Estimate**: ~10 hours (2 seconds per product)

## Production Deployment

### One-Time Setup (10 minutes)
```bash
# 1. Install dependencies
pip install playwright psycopg2-binary openai beautifulsoup4
playwright install chromium

# 2. Extract session
extract_session.bat

# 3. Test with 10 products
set BATCH_SIZE=10
run_authenticated_enrichment.bat
```

### Full Production Run (10 hours)
```bash
# 1. Validate session
python scripts/extract_horme_session.py

# 2. Run full enrichment
set BATCH_SIZE=19143
python scripts/scraperapi_ai_enrichment_authenticated.py
```

### Monitoring
```bash
# Check progress (separate terminal)
docker exec horme-postgres psql -U horme_user -d horme_db -c "
  SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN price IS NOT NULL THEN 1 END) as with_prices,
    COUNT(CASE WHEN enrichment_status = 'completed' THEN 1 END) as completed
  FROM products;
"
```

## Session Maintenance

### Session Lifespan
- Typical: 1-7 days (depends on Horme.com.sg)
- Check validity: Run extraction script (it tests existing session)

### Re-Authentication
If session expires during enrichment:
1. Script detects and stops automatically
2. Extract new session: `extract_session.bat`
3. Resume enrichment: `run_authenticated_enrichment.bat`

**Progress is saved**: Database updates are committed per-product, so you never lose progress

## Security & Compliance

### Legal & Ethical Considerations

**Acceptable**:
- ✅ Using your own legitimate Horme.com.sg account
- ✅ Extracting data you're authorized to view
- ✅ Reasonable request rate (2 seconds between products)
- ✅ Internal business use (quotation system)

**Not Acceptable**:
- ❌ Using stolen/fake credentials
- ❌ Creating multiple accounts to bypass limits
- ❌ Excessive request rate (DDoS)
- ❌ Selling/distributing scraped data

### Our Implementation
- Uses YOUR credentials (you manually log in)
- Respects rate limits (2-second delays)
- Uses authenticated session (not bypassing security)
- Business use case (B2B wholesale pricing)

## Alternative: Contact Horme Directly

**Consider This First**:

Instead of scraping, you could:
1. Contact: sales@horme.com.sg
2. Request: Product price list (Excel/CSV)
3. Result: 100% accurate, complete, FREE
4. Time: 1-2 business days

**Comparison**:
| Method | Cost | Time | Accuracy | Maintenance |
|--------|------|------|----------|-------------|
| AI Scraping | $191 | 10 hours | 85-95% | Medium (sessions expire) |
| Price List | $0 | 1-2 days | 100% | None |

**Use scraping IF**:
- Horme won't provide price list
- Need real-time updates
- Want to demonstrate AI capabilities

## Files Created

1. **scripts/extract_horme_session.py** - Session cookie extractor
2. **scripts/scraperapi_ai_enrichment_authenticated.py** - Authenticated enrichment
3. **extract_session.bat** - Windows batch file for extraction
4. **run_authenticated_enrichment.bat** - Windows batch file for enrichment
5. **horme_session.json** - Saved session cookies (created after extraction)
6. **AI_AUTHENTICATION_BYPASS_RESEARCH.md** - Technical research document

## Support

### Common Questions

**Q: How long does session last?**
A: Typically 1-7 days. Script checks validity and warns if expired.

**Q: Can I run on multiple machines?**
A: Yes, copy `horme_session.json` to other machines.

**Q: What if AI matches wrong product?**
A: Adjust `CONFIDENCE_THRESHOLD` (default 0.7). Higher = stricter matching.

**Q: Can I use ScraperAPI instead of Playwright?**
A: Yes, edit script and set `USE_PLAYWRIGHT = False` and `USE_SCRAPERAPI = True`

**Q: How to speed up processing?**
A: Reduce `time.sleep(2)` delay, but risk being blocked for excessive requests.

### Getting Help

1. Check this guide first
2. Review error messages in script output
3. Test manually in browser to verify expected behavior
4. Check `horme_session.json` exists and is valid

## Next Steps

1. ✅ Run `extract_session.bat` to get authenticated session
2. ✅ Run `run_authenticated_enrichment.bat` to test 10 products
3. ✅ Check results in database
4. ✅ If success rate >80%, run full batch (19,143 products)
5. ✅ Monitor progress and handle session expiration if needed

**Ready to start?** Run `extract_session.bat` now!
