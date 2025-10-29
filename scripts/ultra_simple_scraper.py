"""
Ultra Simple Scraper - Based on Proven Test Script
Synchronous, simple, reliable - exactly what worked in testing
"""
import asyncio
from playwright.async_api import async_playwright
import re
import csv
import json
import time

WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

# Category URLs to scrape (products.aspx pages have products directly)
CATEGORIES = [
    ('Safety Shoes', 'products.aspx?c=70'),
    ('Hand Protection', 'products.aspx?c=71'),
    ('Eye Protection', 'products.aspx?c=111'),
    ('Hearing Protection', 'products.aspx?c=207'),
    ('Face Masks', 'products.aspx?c=78'),
    ('Head Protection', 'products.aspx?c=206'),
    ('Protective Apparel', 'products.aspx?c=157'),
    # Add more specific product category URLs here
]

OUTPUT_CSV = 'scraped_products_ultra_simple.csv'


async def scrape_all():
    """Main scraping function"""
    print("="*80)
    print("ULTRA SIMPLE SCRAPER - PROVEN APPROACH")
    print("="*80)
    print(f"Categories to scrape: {len(CATEGORIES)}")
    print(f"Output: {OUTPUT_CSV}\n")

    # Initialize CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'price', 'category', 'url'])
        writer.writeheader()

    total_products = 0

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

            # Scrape each category
            for i, (cat_name, cat_url) in enumerate(CATEGORIES, 1):
                print(f"[{i}/{len(CATEGORIES)}] {cat_name}")

                # Try multiple pages
                for page_num in range(1, 20):  # Max 20 pages per category
                    try:
                        # Navigate to page
                        url = f"{WEBSITE_URL}/{cat_url}"
                        if page_num > 1:
                            url += f"&page={page_num}"

                        print(f"  Page {page_num}: ", end='', flush=True)

                        await page.goto(url, wait_until='networkidle', timeout=30000)
                        await asyncio.sleep(2)

                        # Extract products
                        product_elements = await page.locator('.product').all()

                        if len(product_elements) == 0:
                            print("No products (end)")
                            break

                        products = []
                        for product_elem in product_elements:
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

                                if product_name and price and price > 0:
                                    products.append({
                                        'name': product_name.strip(),
                                        'price': price,
                                        'category': cat_name,
                                        'url': product_url or ''
                                    })

                            except:
                                continue

                        # Save to CSV
                        if products:
                            with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.DictWriter(f, fieldnames=['name', 'price', 'category', 'url'])
                                for product in products:
                                    writer.writerow(product)

                        total_products += len(products)
                        print(f"{len(products)} products (total: {total_products})")

                    except Exception as e:
                        print(f"Error: {e}")
                        break

                print()

            print("="*80)
            print("SCRAPING COMPLETE")
            print(f"Total products scraped: {total_products}")
            print(f"Output file: {OUTPUT_CSV}")
            print("="*80)

        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(scrape_all())
