"""
Quick Test: ScraperAPI to Access Horme.com.sg
Tests if catalogue ID URLs work when accessed via ScraperAPI proxy network

BEFORE RUNNING:
1. Sign up: https://www.scraperapi.com/signup (free 5,000 credits)
2. Get your API key
3. Set environment variable:
   - Windows: set SCRAPERAPI_KEY=your_key_here
   - Linux/Mac: export SCRAPERAPI_KEY=your_key_here

RUN:
python scripts/test_scraperapi.py

Author: Horme Production Team
Date: 2025-10-22
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, Dict, Any

SCRAPERAPI_KEY = os.getenv('SCRAPERAPI_KEY', '3c29b7d4798bd49564aacf76ba828d8a')

if not SCRAPERAPI_KEY or SCRAPERAPI_KEY == 'your_key_here':
    print("="*80)
    print("ERROR: SCRAPERAPI_KEY environment variable not set")
    print("="*80)
    print("\n1. Sign up for free: https://www.scraperapi.com/signup")
    print("2. Get your API key from dashboard")
    print("3. Set environment variable:")
    print("\n   Windows (CMD):")
    print("   set SCRAPERAPI_KEY=your_key_here")
    print("\n   Windows (PowerShell):")
    print("   $env:SCRAPERAPI_KEY=\"your_key_here\"")
    print("\n   Linux/Mac:")
    print("   export SCRAPERAPI_KEY=your_key_here")
    print("\n4. Run this script again")
    print("="*80)
    sys.exit(1)


def test_catalogue_url(catalogue_id: str) -> Dict[str, Any]:
    """
    Test if catalogue ID URL works via ScraperAPI

    Returns:
        dict with success, status_code, title, price, etc.
    """
    url = f"https://www.horme.com.sg/Product/Detail/{catalogue_id}"

    # ScraperAPI endpoint
    proxy_url = "http://api.scraperapi.com"
    params = {
        'api_key': SCRAPERAPI_KEY,
        'url': url,
        'render': 'false'  # Set to 'true' if JavaScript rendering needed
    }

    print(f"\n{'='*80}")
    print(f"Testing Catalogue ID: {catalogue_id}")
    print(f"URL: {url}")
    print(f"Via ScraperAPI proxy network...")
    print(f"{'='*80}")

    result = {
        'catalogue_id': catalogue_id,
        'url': url,
        'success': False,
        'status_code': None,
        'title': None,
        'price': None,
        'error': None,
        'html_preview': None
    }

    try:
        response = requests.get(proxy_url, params=params, timeout=60)
        result['status_code'] = response.status_code

        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text):,} bytes")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract product title (try multiple selectors)
            title = None
            title_selectors = ['h1', '.product-title', '.product-name', '[class*="title"]']
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem:
                    title = elem.get_text(strip=True)
                    break

            # Extract price (try multiple selectors)
            price_text = None
            price_selectors = ['.price', '.product-price', '[class*="price"]', '[data-price]']
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    price_text = elem.get_text(strip=True)
                    break

            # Parse price to number
            price = None
            if price_text:
                # Extract number from text like "SGD 189.00" or "$189.00"
                match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if match:
                    try:
                        price = float(match.group())
                    except ValueError:
                        pass

            result['success'] = True
            result['title'] = title
            result['price'] = price
            result['html_preview'] = response.text[:500]  # First 500 chars

            print(f"\n[SUCCESS] - Product page loaded!")
            print(f"\nExtracted Data:")
            print(f"  Title: {title if title else '[NOT FOUND]'}")
            print(f"  Price: SGD {price:.2f}" if price else "  Price: [NOT FOUND]")

            if title and price:
                print(f"\n[PERFECT] - Both title and price extracted!")
            elif title:
                print(f"\n[PARTIAL] - Title found but price missing")
            else:
                print(f"\n[POOR] - Product data not found in HTML")

        elif response.status_code == 404:
            result['error'] = "Product not found (404)"
            print(f"\n[FAILED] - Product not found (HTTP 404)")
            print(f"   This means the catalogue ID {catalogue_id} is invalid/outdated")

        else:
            result['error'] = f"HTTP {response.status_code}"
            print(f"\n[FAILED] - HTTP {response.status_code}")
            print(f"   ScraperAPI returned error status")

    except requests.exceptions.Timeout:
        result['error'] = "Request timeout"
        print(f"\n[ERROR] - Request timed out after 60 seconds")

    except Exception as e:
        result['error'] = str(e)
        print(f"\n[ERROR] - {e}")

    return result


def main():
    """Test multiple catalogue IDs to validate approach"""
    print("\n" + "="*80)
    print("SCRAPERAPI TEST - Horme.com.sg Product Pages")
    print("="*80)
    print(f"API Key: {SCRAPERAPI_KEY[:10]}...{SCRAPERAPI_KEY[-5:]}")
    print(f"Free Credits: 5,000 (for new accounts)")
    print("="*80)

    # Sample catalogue IDs from database
    # These are the IDs that were returning 404 when accessed directly
    test_catalogue_ids = [
        "16853",  # From first product in queue
        "16854",  # From second product
        "16855",  # From third product
        "3911",   # Different ID range
        "6667",   # Another ID range
    ]

    print(f"\nTesting {len(test_catalogue_ids)} catalogue IDs...")
    print("(Using 5 API credits from your free 5,000)")

    results = []
    for cat_id in test_catalogue_ids:
        result = test_catalogue_url(cat_id)
        results.append(result)

        # Pause between requests to avoid rate limiting
        import time
        time.sleep(1)

    # Summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    successful = sum(1 for r in results if r['success'])
    found_titles = sum(1 for r in results if r['title'])
    found_prices = sum(1 for r in results if r['price'])

    print(f"\nResults:")
    print(f"  Total Tested:     {len(results)}")
    print(f"  HTTP 200 (OK):    {successful}")
    print(f"  HTTP 404 (Not Found): {sum(1 for r in results if r['status_code'] == 404)}")
    print(f"  Titles Found:     {found_titles}")
    print(f"  Prices Found:     {found_prices}")

    print(f"\nDetailed Results:")
    for r in results:
        status = "✅ OK" if r['success'] else f"❌ {r['error']}"
        data_quality = ""
        if r['title'] and r['price']:
            data_quality = "🎉 Complete"
        elif r['title']:
            data_quality = "⚠️  Title Only"
        elif r['success']:
            data_quality = "❌ No Data"

        print(f"  Catalogue {r['catalogue_id']}: {status} {data_quality}")

    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)

    if found_prices >= 4:
        print(f"\n✅ EXCELLENT RESULTS ({found_prices}/5 products with prices)")
        print("\nRECOMMENDATION: Proceed with ScraperAPI approach")
        print("\nNext Steps:")
        print("1. Integrate ScraperAPI into scraping script")
        print("2. Use remaining 4,995 free credits to enrich 4,995 products")
        print("3. Evaluate results and decide if continuing is worth it")
        print("\nEstimated Cost:")
        print(f"  - Free tier: 4,995 products (FREE)")
        print(f"  - Remaining: 4,769 products (~$318)")
        print(f"  - Total: ~$318 for all 9,764 products with catalogue IDs")

    elif found_prices >= 2:
        print(f"\n⚠️  MIXED RESULTS ({found_prices}/5 products with prices)")
        print("\nRECOMMENDATION: Cautiously proceed OR get price list instead")
        print("\nOptions:")
        print("1. Try more samples to validate success rate")
        print("2. Investigate HTML structure to improve extraction")
        print("3. Consider getting price list from Horme (100% accurate, free)")

    elif successful >= 3:
        print(f"\n⚠️  PRODUCTS FOUND BUT PRICES MISSING ({successful}/5 pages loaded)")
        print("\nRECOMMENDATION: HTML parsing needs improvement")
        print("\nNext Steps:")
        print("1. Manually inspect HTML structure")
        print("2. Update price selectors in extraction logic")
        print("3. Re-test with improved selectors")

    else:
        print(f"\n❌ POOR RESULTS ({successful}/5 successful requests)")
        print("\nRECOMMENDATION: DO NOT proceed with ScraperAPI")
        print("\nReasons:")
        print("- Catalogue IDs are invalid/outdated (even via ScraperAPI)")
        print("- Would need expensive search-based approach (~$3,389)")
        print("- Getting price list from Horme is better option")
        print("\nAlternative:")
        print("Contact Horme for price list (FREE, 100% accurate, fast)")

    print("\n" + "="*80)
    print(f"API Credits Used: 5")
    print(f"API Credits Remaining: 4,995 (if free tier account)")
    print("="*80)

    # Save results to file for reference
    import json
    output_file = "scraperapi_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print("\nDone!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
