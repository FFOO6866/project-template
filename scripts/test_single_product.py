"""
Test single product extraction
"""

import asyncio
from playwright.async_api import async_playwright
import re
from decimal import Decimal

WEBSITE_BASE_URL = "https://www.horme.com.sg/product.aspx?id="

async def test_product(catalogue_id):
    """Test extracting price from a single product"""

    url = f"{WEBSITE_BASE_URL}{catalogue_id}"
    print(f"\nTesting: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(url, wait_until='domcontentloaded', timeout=15000)
        await page.wait_for_timeout(2000)

        # Try specific selector
        print("\nTrying #ctl00_pgContent_price...")
        try:
            element = await page.query_selector('#ctl00_pgContent_price')
            if element:
                text = await element.text_content()
                print(f"Found element, text: {text}")

                # Extract price
                match = re.search(r'(?:S\$|SGD|$)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', text.replace(',', ''))
                if match:
                    price = Decimal(match.group(1))
                    print(f"Extracted price: ${price}")
                else:
                    print(f"No price match in text: {text}")
            else:
                print("Element not found!")
        except Exception as e:
            print(f"Error: {e}")

        # Try getting all text
        print("\nGetting all page text...")
        body_text = await page.text_content('body')
        if 'S$' in body_text:
            prices = re.findall(r'S\$\s*(\d+\.\d{2})', body_text)
            print(f"Found S$ prices in body: {prices[:5]}")

        print("\nKeeping browser open for 30 seconds...")
        await page.wait_for_timeout(30000)

        await browser.close()

# Test with known good catalogue ID
asyncio.run(test_product(16853))
