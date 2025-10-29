"""
Diagnostic script to examine category/product listing page structure
"""
import asyncio
from playwright.async_api import async_playwright

WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

# Test category: Safety Shoes & Safety Boots
TEST_CATEGORY_URL = f"{WEBSITE_URL}/products.aspx?c=70"

async def diagnose_category_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            # Login first
            print("Logging in...")
            await page.goto(f"{WEBSITE_URL}/login.aspx", wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            await page.fill('#ctl00_pgContent_email', LOGIN_EMAIL)
            await page.fill('#ctl00_pgContent_pwd', LOGIN_PASSWORD)
            await page.click('#btnLogin')
            await asyncio.sleep(4)

            print(f"Login complete. Now navigating to category page...")

            # Navigate to category page
            await page.goto(TEST_CATEGORY_URL, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)

            print(f"Current URL: {page.url}")

            # Save screenshot
            await page.screenshot(path='category_page.png', full_page=True)
            print("  Saved category_page.png (full page)")

            # Save HTML
            content = await page.content()
            with open('category_page.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("  Saved category_page.html")

            # Look for product listings
            print("\n" + "="*80)
            print("LOOKING FOR PRODUCT LISTINGS")
            print("="*80)

            # Common product listing selectors
            product_selectors = [
                '.product',
                '.product-item',
                '.product-card',
                '[class*="product"]',
                '.item',
                'article',
                '[itemtype*="Product"]'
            ]

            products_found = []
            for selector in product_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        products_found.append({'selector': selector, 'count': count})
                        print(f"\nFound {count} elements with selector: {selector}")
                except:
                    pass

            # Try to find product names
            print("\n" + "="*80)
            print("LOOKING FOR PRODUCT NAMES")
            print("="*80)

            name_selectors = [
                '.product-name',
                '.product-title',
                'h2 a',
                'h3 a',
                '[class*="name"] a',
                '[class*="title"] a'
            ]

            for selector in name_selectors:
                try:
                    elements = await page.locator(selector).all()
                    if len(elements) > 0:
                        print(f"\nFound {len(elements)} product names with: {selector}")
                        # Show first 3
                        for i, elem in enumerate(elements[:3]):
                            text = await elem.inner_text()
                            href = await elem.get_attribute('href')
                            print(f"  {i+1}. {text[:60]}")
                            print(f"     URL: {href}")
                except Exception as e:
                    pass

            # Try to find prices
            print("\n" + "="*80)
            print("LOOKING FOR PRICES")
            print("="*80)

            price_selectors = [
                '.price',
                '.product-price',
                '[class*="price"]',
                '.amount',
                '[data-price]'
            ]

            for selector in price_selectors:
                try:
                    elements = await page.locator(selector).all()
                    if len(elements) > 0:
                        print(f"\nFound {len(elements)} price elements with: {selector}")
                        # Show first 3
                        for i, elem in enumerate(elements[:3]):
                            text = await elem.inner_text()
                            print(f"  {i+1}. {text}")
                except Exception as e:
                    pass

            # Check for pagination
            print("\n" + "="*80)
            print("LOOKING FOR PAGINATION")
            print("="*80)

            pagination_selectors = [
                '.pagination',
                '.pager',
                '[class*="pagination"]',
                '[class*="pager"]',
                'nav[aria-label*="pagination"]'
            ]

            for selector in pagination_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        print(f"\nFound pagination with: {selector}")
                        # Try to extract page numbers
                        links = await page.locator(f"{selector} a").all()
                        print(f"  Total pagination links: {len(links)}")
                        for i, link in enumerate(links[:5]):
                            text = await link.inner_text()
                            href = await link.get_attribute('href')
                            print(f"    {i+1}. {text} -> {href}")
                except Exception as e:
                    pass

            print("\n" + "="*80)
            print("Analysis complete. Files saved:")
            print("  - category_page.png")
            print("  - category_page.html")
            print("="*80)

            print("\nWaiting 30 seconds so you can inspect the browser...")
            await asyncio.sleep(30)

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(diagnose_category_page())
