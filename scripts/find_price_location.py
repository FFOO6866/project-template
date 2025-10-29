"""
Find where the actual price is stored on the page
"""
import asyncio
import json
from playwright.async_api import async_playwright
import re

async def find_price(catalogue_id):
    url = f"https://www.horme.com.sg/product.aspx?id={catalogue_id}"
    print(f"\nAnalyzing: {url}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(url, wait_until='domcontentloaded', timeout=15000)
        await page.wait_for_timeout(3000)  # Wait 3 seconds

        # Check for JSON-LD structured data
        print("=" * 80)
        print("CHECKING FOR JSON-LD STRUCTURED DATA")
        print("=" * 80)

        json_ld_elements = await page.query_selector_all('script[type="application/ld+json"]')
        print(f"Found {len(json_ld_elements)} JSON-LD elements\n")

        for i, element in enumerate(json_ld_elements):
            content = await element.text_content()
            try:
                data = json.loads(content)
                print(f"JSON-LD #{i+1}:")
                if 'offers' in data:
                    print(f"  HAS OFFERS! {json.dumps(data['offers'], indent=2)}")
                elif 'price' in str(data).lower():
                    print(f"  Contains 'price': {json.dumps(data, indent=2)}")
                else:
                    print(f"  Type: {data.get('@type', 'unknown')}")
            except:
                print(f"  Failed to parse JSON")

        # Search HTML source for price patterns
        print("\n" + "=" * 80)
        print("SEARCHING HTML SOURCE FOR PRICE PATTERNS")
        print("=" * 80)

        html_content = await page.content()

        # Look for price in various formats
        patterns = [
            r'"price"\s*:\s*"?(\d+\.?\d*)"?',
            r'"offers"\s*:\s*{[^}]*"price"\s*:\s*"?(\d+\.?\d*)"?',
            r'S\$\s*(\d+\.?\d+)',
            r'SGD\s*(\d+\.?\d+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html_content)
            if matches:
                print(f"\nPattern: {pattern}")
                print(f"  Matches: {matches[:5]}")  # First 5 matches

        print("\n\nKeeping browser open for 20 seconds...")
        await page.wait_for_timeout(20000)

        await browser.close()

# Test with product that WebFetch confirmed has price S$151.25
asyncio.run(find_price(16952))
