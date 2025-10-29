"""
Debug script to inspect actual page structure
Find the correct selectors for products and prices
"""
import asyncio
from playwright.async_api import async_playwright

WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            # Login
            print("Logging in...")
            await page.goto(f"{WEBSITE_URL}/login.aspx", wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            await page.fill('#ctl00_pgContent_email', LOGIN_EMAIL)
            await page.fill('#ctl00_pgContent_pwd', LOGIN_PASSWORD)
            await page.click('#btnLogin')
            await asyncio.sleep(4)
            print("Logged in\n")

            # Go to a product category page
            test_url = f"{WEBSITE_URL}/products.aspx?c=70"  # Safety Shoes
            print(f"Navigating to: {test_url}")
            await page.goto(test_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # Save page HTML for inspection
            html_content = await page.content()
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("Saved page HTML to: debug_page.html\n")

            # Try different selectors
            selectors_to_try = [
                '.product',
                '.product-item',
                '[class*="product"]',
                '.popular__pro',
                '[class*="popular"]',
                '.item',
                '[class*="item"]',
                'article',
                '[data-product]',
                '.grid-item',
                '[class*="grid"]'
            ]

            print("Testing product selectors:")
            print("="*80)

            for selector in selectors_to_try:
                try:
                    count = await page.locator(selector).count()
                    print(f"{selector:30} -> {count} elements")

                    if count > 0 and count < 50:  # Reasonable product count
                        # Get first element's HTML
                        first_elem = page.locator(selector).first
                        html = await first_elem.inner_html()
                        print(f"  Sample HTML (first 200 chars): {html[:200]}...")
                except Exception as e:
                    print(f"{selector:30} -> Error: {e}")

            # Try price selectors
            print("\n" + "="*80)
            print("Testing price selectors:")
            print("="*80)

            price_selectors = [
                '.price',
                '[class*="price"]',
                '.popular__pro__price',
                '[data-price]',
                '.product-price',
                '.amount'
            ]

            for selector in price_selectors:
                try:
                    count = await page.locator(selector).count()
                    print(f"{selector:30} -> {count} elements")

                    if count > 0:
                        first_elem = page.locator(selector).first
                        text = await first_elem.inner_text()
                        print(f"  Sample text: {text}")
                except Exception as e:
                    print(f"{selector:30} -> Error: {e}")

            # Screenshot
            await page.screenshot(path='debug_products_page.png', full_page=True)
            print("\nScreenshot saved: debug_products_page.png")

            print("\nWaiting 20 seconds for manual inspection...")
            await asyncio.sleep(20)

        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
