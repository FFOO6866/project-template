"""
Comprehensive All-Category Scraper
Scrapes ALL product categories from Horme website for maximum coverage
"""
import asyncio
from playwright.async_api import async_playwright
import re
import csv
import time

WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

# ALL product category URLs discovered (products.aspx pages have direct products)
ALL_CATEGORIES = [
    # Safety Products (21)
    ('Safety Shoes', 'products.aspx?c=70'),
    ('Hand Protection', 'products.aspx?c=71'),
    ('Eye Protection', 'products.aspx?c=111'),
    ('Hearing Protection', 'products.aspx?c=207'),
    ('Face Masks', 'products.aspx?c=78'),
    ('Head Protection', 'products.aspx?c=206'),
    ('Protective Apparel', 'products.aspx?c=157'),

    # Ladders, Trolleys & Storage (17)
    ('Ladders & Work Platforms', 'products.aspx?c=91'),
    ('Trolley & Carts', 'products.aspx?c=125'),
    ('Storage Boxes', 'products.aspx?c=134'),
    ('Shelves & Cabinets', 'products.aspx?c=186'),
    ('Toolboxes & Work Benches', 'products.aspx?c=92'),
    ('Castors & Wheels', 'products.aspx?c=5'),
    ('Waterproof Cases', 'products.aspx?c=184'),

    # Cleaning Products (05)
    ('Trash Bins', 'products.aspx?c=149'),
    ('Trash Bags', 'products.aspx?c=212'),
    ('Cleaning Tools', 'products.aspx?c=29'),
    ('Cleaning Trolleys', 'products.aspx?c=214'),
    ('Pressure Washers', 'products.aspx?c=28'),
    ('Vacuum Cleaners', 'products.aspx?c=27'),

    # Power Tools - Corded (09)
    ('Corded Drills', 'products.aspx?c=40'),
    ('Corded Cutters & Saws', 'products.aspx?c=42'),
    ('Corded Grinders', 'products.aspx?c=41'),
    ('Corded Oscillating Tools', 'products.aspx?c=166'),
    ('Corded 110V Tools', 'products.aspx?c=178'),
    ('Other Corded Tools', 'products.aspx?c=45'),

    # Power Tools - Cordless (09)
    ('Cordless Drills', 'products.aspx?c=51'),
    ('Cordless Cutters & Saws', 'products.aspx?c=53'),
    ('Cordless Grinders', 'products.aspx?c=77'),
    ('Other Cordless Tools', 'products.aspx?c=56'),

    # Power Tools - Accessories (09)
    ('Powertool Batteries', 'products.aspx?c=80'),
    ('Multitool Accessories', 'products.aspx?c=187'),
    ('Drilling Accessories', 'products.aspx?c=79'),
    ('Cutting Accessories', 'products.aspx?c=81'),
    ('Other Tool Accessories', 'products.aspx?c=84'),

    # Hand Tools
    ('Hand Tool Sets', 'products.aspx?c=151'),
    ('Automotive Tools', 'products.aspx?c=179'),
    ('Construction Tools', 'products.aspx?c=128'),
    ('Cutting & Sawing Tools', 'products.aspx?c=86'),
    ('Electrician Tools', 'products.aspx?c=87'),
    ('Hex Tools', 'products.aspx?c=176'),
    ('Measuring Tools', 'products.aspx?c=89'),
    ('Multitools & Knives', 'products.aspx?c=123'),
    ('Non Sparking Tools', 'products.aspx?c=167'),
    ('Plumbing Tools', 'products.aspx?c=152'),
    ('Other Hand Tools', 'products.aspx?c=90'),

    # Garden & Outdoor
    ('Lawn Mowers', 'products.aspx?c=114'),
    ('Garden Tools', 'products.aspx?c=93'),
    ('Painting Tools', 'products.aspx?c=95'),

    # Machines & Equipment
    ('Cutting Machines', 'products.aspx?c=101'),
    ('Drilling Machines', 'products.aspx?c=99'),
    ('Sanding Machines', 'products.aspx?c=100'),

    # Pneumatic
    ('Air Tools', 'products.aspx?c=94'),

    # Electrical
    ('Batteries & Power Stations', 'products.aspx?c=96'),
    ('Electrical Accessories', 'products.aspx?c=48'),
    ('Electrical Testers', 'products.aspx?c=173'),
]

OUTPUT_CSV = 'all_products_scraped.csv'


async def scrape_all():
    """Main scraping function for ALL categories"""
    print("="*80)
    print("COMPREHENSIVE ALL-CATEGORY SCRAPER")
    print("="*80)
    print(f"Categories to scrape: {len(ALL_CATEGORIES)}")
    print(f"Output: {OUTPUT_CSV}")
    print(f"Expected time: 2-4 hours")
    print("="*80)
    print()

    # Initialize CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'price', 'category', 'url'])
        writer.writeheader()

    total_products = 0
    start_time = time.time()

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
            for i, (cat_name, cat_url) in enumerate(ALL_CATEGORIES, 1):
                print(f"[{i}/{len(ALL_CATEGORIES)}] {cat_name}")
                category_products = 0

                # Try multiple pages (max 30 per category for safety)
                for page_num in range(1, 31):
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
                            print("End")
                            break

                        products = []
                        for product_elem in product_elements:
                            try:
                                name_link = product_elem.locator('.product__details h2 a').first
                                product_name = await name_link.inner_text()
                                product_url = await name_link.get_attribute('href')

                                price_elem = product_elem.locator('.popular__pro__price').first
                                price_text = await price_elem.inner_text()

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

                        category_products += len(products)
                        total_products += len(products)
                        print(f"{len(products)} products (total: {total_products})")

                    except Exception as e:
                        if 'Timeout' in str(e):
                            print(f"Timeout - skipping")
                            break
                        else:
                            print(f"Error - skipping")
                            break

                elapsed = (time.time() - start_time) / 60
                print(f"  Category total: {category_products} products | Time: {elapsed:.1f}min\n")

            # Final stats
            elapsed = (time.time() - start_time) / 60
            print("="*80)
            print("SCRAPING COMPLETE")
            print("="*80)
            print(f"Total products scraped: {total_products}")
            print(f"Categories processed: {len(ALL_CATEGORIES)}")
            print(f"Time elapsed: {elapsed:.1f} minutes ({elapsed/60:.1f} hours)")
            print(f"Output file: {OUTPUT_CSV}")
            print("="*80)

        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(scrape_all())
