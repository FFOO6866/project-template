"""
Debug script to see exactly what Playwright sees
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_product(catalogue_id):
    url = f"https://www.horme.com.sg/product.aspx?id={catalogue_id}"
    print(f"\nTesting: {url}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(url, wait_until='domcontentloaded', timeout=15000)
        await page.wait_for_timeout(2000)

        # Try to find the price element
        print("=" * 80)
        print("CHECKING #ctl00_pgContent_price")
        print("=" * 80)

        element = await page.query_selector('#ctl00_pgContent_price')
        if element:
            text = await element.text_content()
            inner_html = await element.inner_html()
            print(f"[OK] Element found!")
            print(f"  text_content(): '{text}'")
            print(f"  inner_html():   '{inner_html}'")
        else:
            print("[ERROR] Element NOT found!")

        # Check all elements with 'price' in ID
        print("\n" + "=" * 80)
        print("ALL ELEMENTS WITH 'price' IN ID")
        print("=" * 80)

        elements = await page.query_selector_all('[id*="price"]')
        print(f"Found {len(elements)} elements")
        for i, el in enumerate(elements[:10]):  # First 10 only
            el_id = await el.get_attribute('id')
            el_text = await el.text_content()
            print(f"{i+1}. ID: {el_id}")
            print(f"   Text: {el_text[:100]}")

        # Check page source for "S$"
        print("\n" + "=" * 80)
        print("SEARCHING FOR 'S$' IN PAGE")
        print("=" * 80)

        body_text = await page.text_content('body')
        if 'S$' in body_text:
            print("[OK] 'S$' found in body text")
            # Find first occurrence
            idx = body_text.index('S$')
            snippet = body_text[max(0, idx-50):idx+100]
            print(f"  Context: ...{snippet}...")
        else:
            print("[ERROR] 'S$' NOT found in body text!")

        print("\n\nKeeping browser open for 30 seconds...")
        await page.wait_for_timeout(30000)

        await browser.close()

# Test with product that WebFetch confirmed has price
asyncio.run(debug_product(16952))
