# 🌐 Web Scraping Services Analysis - Alternative Solution

**Date**: 2025-10-22
**Status**: ✅ VIABLE ALTERNATIVE to network blocking issue
**Purpose**: Evaluate third-party scraping services to bypass network restrictions

---

## 🎯 The Problem They Solve

**Current Issue**: Horme.com.sg is blocked at network level
- ❌ Docker container cannot access
- ❌ Host machine cannot access
- ✅ Third-party services use residential IPs + rotating proxies = can access

**How They Work**:
```
Your Code → Scraping Service API → Their Proxy Network → horme.com.sg
            (localhost)              (residential IPs)      (accessible)
```

---

## 📊 Service Comparison

| Service | Cost per Call | Free Credits | Python SDK | JS Rendering | Best For |
|---------|--------------|--------------|------------|--------------|----------|
| **ScrapingDog** | $0.000067 | 1,000 | ✅ | ✅ | General + specialized APIs |
| **ScraperAPI** | $0.0000997 | 5,000 | ✅ | ✅ | Most free credits |
| **ScrapingBee** | $0.000083 | 1,000 | ✅ | ✅ | Simple HTML extraction |
| **ZenRows** | $0.00008 | $1 credit | ✅ | ✅ | Proxy specialists |
| **Scrape.do** | $0.000071 | 1,000 | ✅ | ✅ | General purpose |

### Recommended: **ScraperAPI** ⭐

**Why**:
- ✅ 5,000 free trial credits (most generous)
- ✅ Explicit JavaScript rendering support
- ✅ Production-ready Python SDK
- ✅ Good documentation
- ✅ Can test 5,000 products for FREE

---

## 💰 Cost Analysis

### Scenario 1: Catalogue ID URLs (Optimistic)

**Assumption**: Catalogue ID URLs work (404s were due to network blocking, not invalid IDs)

**Products to scrape**: 9,764 (those with catalogue IDs)

| Service | Cost | With OpenAI AI Matching |
|---------|------|------------------------|
| ScrapingDog | $654 | $844 - $1,229 |
| ScraperAPI | $973 | $1,163 - $1,548 |
| ScrapingBee | $811 | $1,001 - $1,386 |
| ZenRows | $781 | $971 - $1,356 |
| Scrape.do | $693 | $883 - $1,268 |

**Free tier test**:
- ScraperAPI: 5,000 products FREE ✅
- Others: 1,000 products FREE

### Scenario 2: Search-Based (Realistic)

**Assumption**: Catalogue URLs still return 404s, need to search each product

**API calls needed**:
- Search page: 19,143 calls
- Product page: ~15,000 calls (estimated matches)
- Total: ~34,000 calls

| Service | Cost | With OpenAI |
|---------|------|-------------|
| ScrapingDog | $2,278 | $2,468 - $2,853 |
| ScraperAPI | $3,389 | $3,579 - $3,964 |
| ScrapingBee | $2,822 | $3,012 - $3,397 |
| ZenRows | $2,720 | $2,910 - $3,295 |
| Scrape.do | $2,414 | $2,604 - $2,989 |

---

## ⚖️ Solution Comparison

| Solution | Cost | Time | Success Rate | Accuracy | Pros | Cons |
|----------|------|------|--------------|----------|------|------|
| **Price List** | FREE | 30 min | 95% | 100% | Fast, accurate, free | Requires Horme cooperation |
| **ScraperAPI (Catalogue)** | $973 | 5 hrs | 60% | 85% | Bypasses blocking, free trial | Expensive, uncertain if URLs work |
| **ScraperAPI (Search)** | $3,389 | 50 hrs | 75% | 75% | Bypasses blocking | Very expensive, slow |
| **VPN + AI** | $20/mo + $190 | 50 hrs | 50% | 75% | Full control | Complex setup |
| **Category Defaults** | FREE | 5 min | 100% | 0% | Testing only | Not production-ready |

---

## 🧪 Proof of Concept Strategy

### Phase 1: Test ScraperAPI Free Tier

**Step 1: Sign up for ScraperAPI**
```
https://www.scraperapi.com/signup
- Get 5,000 free credits
- No credit card required
```

**Step 2: Test Catalogue ID URLs**
```python
import requests

api_key = "YOUR_SCRAPERAPI_KEY"
url = "https://www.horme.com.sg/Product/Detail/16853"
proxy_url = f"http://api.scraperapi.com?api_key={api_key}&url={url}"

response = requests.get(proxy_url)
print(response.status_code)  # If 200, catalogue IDs work!
```

**Step 3: Determine Path Forward**

**IF catalogue URLs return 200 (success)**:
✅ Use catalogue ID approach (cheaper, faster)
- 9,764 products
- ~$973 cost (or 5,000 free with trial)
- 5-10 hours total time

**IF catalogue URLs return 404 (failure)**:
⚠️ Must use search-based approach
- 19,143 products
- ~$3,389 cost
- 50+ hours total time
- Consider if price list is better option

---

## 🔧 Implementation Options

### Option A: ScraperAPI + Catalogue IDs (Best Case)

**Code Integration**:
```python
import requests
from typing import Optional

SCRAPERAPI_KEY = os.getenv('SCRAPERAPI_KEY')

def fetch_with_scraperapi(url: str) -> Optional[str]:
    """Fetch URL using ScraperAPI proxy"""
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={url}"
    response = requests.get(proxy_url, timeout=60)
    if response.status_code == 200:
        return response.text
    return None

# Use in existing scraper
async def fetch_page_content(session, url):
    # Replace aiohttp with ScraperAPI
    html = fetch_with_scraperapi(url)
    return html
```

**Modifications needed**:
- ✅ Minimal - just replace HTTP client
- ✅ Keep existing AI extraction logic
- ✅ ~1 hour of development

**Cost**: ~$973 for 9,764 products (or FREE for first 5,000)

### Option B: ScraperAPI + AI Search (Worst Case)

**Approach**:
1. Use ScraperAPI to fetch search pages
2. Use GPT-4 to match products
3. Use ScraperAPI to fetch product pages
4. Extract prices

**Modifications needed**:
- Combine existing AI enrichment script with ScraperAPI
- ~2-3 hours of development

**Cost**: ~$3,389 scraping + $190-575 OpenAI = $3,579-3,964

### Option C: Hybrid Approach (Recommended)

**Strategy**:
1. **Test with ScraperAPI free tier (5,000 credits)**
   - Test catalogue ID approach on first 5,000 products
   - Measure success rate

2. **Evaluate results**:
   - If >80% success → Purchase more credits, continue
   - If <50% success → Stop, get price list instead

3. **Decision point**:
   - If working well → Complete remaining 4,764 products ($318)
   - If not working → Don't spend money, pursue price list

**Total risk**: $0 (free tier only)
**Best case**: 5,000 products enriched for FREE
**Worst case**: Proves approach doesn't work, no money wasted

---

## 🎯 Recommended Action Plan

### Immediate (Next 30 minutes)

1. **Sign up for ScraperAPI** (5 minutes)
   ```
   https://www.scraperapi.com/signup
   Get API key
   ```

2. **Test single product** (10 minutes)
   ```python
   # Test script
   import requests

   api_key = "YOUR_KEY"
   test_url = "https://www.horme.com.sg/Product/Detail/16853"
   proxy = f"http://api.scraperapi.com?api_key={api_key}&url={test_url}"

   response = requests.get(proxy)
   print(f"Status: {response.status_code}")
   print(f"Content length: {len(response.text)}")

   if response.status_code == 200:
       print("✅ SUCCESS - Catalogue IDs work!")
   else:
       print("❌ FAIL - Catalogue IDs invalid")
   ```

3. **Make decision** (5 minutes)
   - If test succeeds → Proceed to Phase 2
   - If test fails → Abandon, get price list

### Short Term (If test succeeds)

4. **Integrate ScraperAPI** (1 hour)
   - Modify `scripts/scrape_horme_product_details.py`
   - Replace direct HTTP calls with ScraperAPI
   - Test on 10 products

5. **Run free tier batch** (5-10 hours)
   - Process 5,000 products using free credits
   - Monitor success rate
   - Review extracted data quality

6. **Evaluate economics** (Decision point)
   - Success rate: _____%
   - Data quality: Good / Fair / Poor
   - Continue? Yes / No

### Long Term (If continuing)

7. **Purchase credits** (if economical)
   - Remaining products: 4,764
   - Cost: ~$318
   - Time: ~3-5 hours

8. **Complete enrichment**
   - Total enriched: 9,764 products
   - Total cost: $318 (saved $655 with free tier)
   - Products without catalogue IDs: 9,379 (still need price list)

---

## ✅ Success Criteria

**Proceed with ScraperAPI if**:
- ✅ Test product returns HTTP 200
- ✅ HTML contains product information
- ✅ Prices are extractable
- ✅ Success rate >80% in free tier test
- ✅ Data quality is good

**Stop and get price list if**:
- ❌ Test product returns 404
- ❌ HTML is blocked/CAPTCHA
- ❌ Success rate <50% in free tier test
- ❌ Data quality is poor
- ❌ Too expensive vs. price list value

---

## 🔬 Technical Integration

### Quick Test Script

**File**: `scripts/test_scraperapi.py`

```python
"""
Quick test of ScraperAPI to access Horme.com.sg
Run this FIRST to validate approach before full integration
"""

import os
import requests
from bs4 import BeautifulSoup

SCRAPERAPI_KEY = os.getenv('SCRAPERAPI_KEY')

def test_catalogue_url(catalogue_id: str):
    """Test if catalogue ID URL works via ScraperAPI"""
    url = f"https://www.horme.com.sg/Product/Detail/{catalogue_id}"
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={url}"

    print(f"Testing: {url}")
    print(f"Via ScraperAPI...")

    try:
        response = requests.get(proxy_url, timeout=60)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)} bytes")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Try to find product title
            title = soup.find('h1') or soup.find(class_='product-title')
            price = soup.find(class_='price') or soup.find(class_='product-price')

            print(f"\nExtracted Data:")
            print(f"  Title: {title.get_text(strip=True) if title else 'NOT FOUND'}")
            print(f"  Price: {price.get_text(strip=True) if price else 'NOT FOUND'}")

            return True
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    # Test 5 different catalogue IDs
    test_ids = ["16853", "16854", "16855", "3911", "6667"]

    results = []
    for cat_id in test_ids:
        success = test_catalogue_url(cat_id)
        results.append(success)
        print("\n" + "="*80 + "\n")

    print(f"Summary: {sum(results)}/{len(results)} successful")

    if sum(results) >= 4:
        print("✅ RECOMMENDATION: Proceed with ScraperAPI approach")
    elif sum(results) >= 2:
        print("⚠️ RECOMMENDATION: Mixed results - evaluate cost/benefit")
    else:
        print("❌ RECOMMENDATION: Get price list instead - catalogue IDs don't work")
```

### Full Integration (if test succeeds)

**File**: `scripts/scrape_with_scraperapi.py`

```python
"""
Modified scraper using ScraperAPI to bypass network blocking
"""

import os
import requests
from typing import Optional
# ... existing imports ...

SCRAPERAPI_KEY = os.getenv('SCRAPERAPI_KEY')
SCRAPERAPI_PREMIUM = os.getenv('SCRAPERAPI_PREMIUM', 'false').lower() == 'true'

def fetch_via_scraperapi(url: str) -> Optional[str]:
    """Fetch URL using ScraperAPI proxy"""
    params = {
        'api_key': SCRAPERAPI_KEY,
        'url': url
    }

    # Premium features (if enabled)
    if SCRAPERAPI_PREMIUM:
        params['render'] = 'true'  # JavaScript rendering
        params['premium'] = 'true'  # Residential proxies

    proxy_url = "http://api.scraperapi.com"

    try:
        response = requests.get(proxy_url, params=params, timeout=60)
        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        print(f"ScraperAPI error: {e}")
        return None

# Integrate into existing scraper
# Replace: async with session.get(url, ...) as response:
# With: html_content = fetch_via_scraperapi(url)
```

---

## 📊 Expected Outcomes

### Best Case Scenario
- ✅ Catalogue URLs work via ScraperAPI
- ✅ 5,000 products enriched FREE (trial credits)
- ✅ Remaining 4,764 products: $318
- ✅ Total cost: $318 for 9,764 products
- ✅ Timeline: 1 day setup + 5-10 hours scraping

### Realistic Scenario
- ⚠️ Mixed results (60-70% success rate)
- ⚠️ 3,000-3,500 products enriched with free tier
- ⚠️ Decision: Continue paying or get price list for remainder
- ⚠️ Hybrid approach: ScraperAPI + price list

### Worst Case Scenario
- ❌ Catalogue URLs still return 404 even via ScraperAPI
- ❌ Need search-based approach ($3,389)
- ❌ OR need to get price list anyway
- ✅ Only lost time (no money on failed approach)

---

## 🎯 Bottom Line

### Why This is Worth Trying

1. **Free tier is risk-free**
   - 5,000 free credits = test at no cost
   - Proves viability before spending money

2. **Solves network blocking**
   - Residential IPs bypass restrictions
   - Professional proxy rotation

3. **Quick to test**
   - 30 minutes to validate approach
   - Immediate decision on feasibility

4. **Integrates with existing code**
   - Minimal modifications needed
   - Keep AI extraction logic

5. **Complements price list strategy**
   - Can enrich ~9,764 products with catalogue IDs
   - Still need price list for remaining 9,379
   - Hybrid approach is viable

### When to Abandon This Approach

- ❌ If test returns 404s (catalogue IDs invalid)
- ❌ If success rate <50% in free tier
- ❌ If cost >$1,000 (better to just get price list)
- ❌ If Horme provides price list (free > paid)

---

**Next Step**: Sign up for ScraperAPI and run test script (30 minutes)

**Decision Point**: After test, choose:
- Path A: Proceed with ScraperAPI (if test succeeds)
- Path B: Get price list from Horme (if test fails or too expensive)
- Path C: Hybrid (ScraperAPI for some, price list for remainder)

**Report Generated**: 2025-10-22
**Status**: READY FOR TESTING
**Recommendation**: Test ScraperAPI free tier immediately to validate approach
