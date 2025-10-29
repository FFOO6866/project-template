"""
Quick test to verify scraper extracts products correctly
"""
import asyncio
from playwright.async_api import async_playwright
import re

WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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
            print("Logged in successfully\n")

            # Test one product page
            test_url = f"{WEBSITE_URL}/products.aspx?c=70"  # Safety Shoes
            print(f"Testing: {test_url}")
            await page.goto(test_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # Extract products
            product_elements = await page.locator('.product').all()
            print(f"Found {len(product_elements)} product elements\n")

            products = []
            for i, product_elem in enumerate(product_elements[:5], 1):  # Test first 5
                try:
                    # Extract product name and URL
                    name_link = product_elem.locator('.product__details h2 a').first
                    product_name = await name_link.inner_text()
                    product_url = await name_link.get_attribute('href')

                    # Extract price
                    price_elem = product_elem.locator('.popular__pro__price').first
                    price_text = await price_elem.inner_text()

                    # Parse price
                    price = None
                    if price_text:
                        price_match = re.search(r'[\$S]?\s*([0-9,]+\.?\d*)', price_text)
                        if price_match:
                            price_str = price_match.group(1).replace(',', '')
                            price = float(price_str)

                    if product_name and price:
                        products.append({
                            'name': product_name.strip(),
                            'price': price,
                            'url': product_url or ''
                        })

                        print(f"{i}. {product_name}")
                        print(f"   Price: ${price}")
                        print(f"   URL: {product_url}\n")

                except Exception as e:
                    print(f"{i}. [ERROR] {e}\n")

            print(f"Successfully extracted {len(products)} products!")

        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
