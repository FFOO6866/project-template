"""
Scrape ALL Products from the 3 Main Database Categories
Target: Safety Products (21), Power Tools (09), Cleaning Products (05)
Expected: ~17,000 products total
"""
import asyncio
from playwright.async_api import async_playwright
import re
import csv
import time

WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

# ALL product subcategories for the 3 MAIN categories
# NOTE: Safety Products ALREADY SCRAPED (9,016 products in CSV)
# Resuming from Power Tools onwards
CATEGORIES = [
    # === POWER TOOLS (09) - Expected: 4,927 products ===
    # Corded Power Tools
    ('Corded Drills & Impact Drivers', 'products.aspx?c=40', '09'),
    ('Corded Cutters & Saws', 'products.aspx?c=42', '09'),
    ('Corded Grinders', 'products.aspx?c=41', '09'),
    ('Corded Oscillating Tools', 'products.aspx?c=166', '09'),
    ('Corded 110V Tools', 'products.aspx?c=178', '09'),
    ('Other Corded Power Tools', 'products.aspx?c=45', '09'),

    # Cordless Power Tools
    ('Cordless Drills & Impact Drivers', 'products.aspx?c=51', '09'),
    ('Cordless Cutters & Saws', 'products.aspx?c=53', '09'),
    ('Cordless Grinders', 'products.aspx?c=77', '09'),
    ('Other Cordless Power Tools', 'products.aspx?c=56', '09'),

    # Power Tool Accessories
    ('Powertool Batteries & Chargers', 'products.aspx?c=80', '09'),
    ('Multitool Accessories', 'products.aspx?c=187', '09'),
    ('Drilling & Fastening Accessories', 'products.aspx?c=79', '09'),
    ('Cutting & Sawing Accessories', 'products.aspx?c=81', '09'),
    ('Other Power Tools Accessories', 'products.aspx?c=84', '09'),

    # === CLEANING PRODUCTS (05) - Expected: 3,210 products ===
    ('Trash & Recycling Bins', 'products.aspx?c=149', '05'),
    ('Trash Bags & Accessories', 'products.aspx?c=212', '05'),
    ('Cleaning Tools', 'products.aspx?c=29', '05'),
    ('Cleaning Trolleys', 'products.aspx?c=214', '05'),
    ('Pressure Washers & Steam Cleaners', 'products.aspx?c=28', '05'),
    ('Vacuum Cleaners & Carpet Cleaners', 'products.aspx?c=27', '05'),
]

OUTPUT_CSV = 'scraped_3_main_categories.csv'


async def scrape_all():
    """Main scraping function"""
    print("="*80)
    print("RESUMING SCRAPER - POWER TOOLS & CLEANING CATEGORIES")
    print("="*80)
    print("Already Scraped:")
    print("  [OK] Safety Products (21) - 9,016 products COMPLETE")
    print("\nResuming with:")
    print("  2. Power Tools (09) - Expected: ~4,927 products")
    print("  3. Cleaning Products (05) - Expected: ~3,210 products")
    print(f"\nSubcategories remaining: {len(CATEGORIES)}")
    print(f"Appending to: {OUTPUT_CSV}")
    print(f"Estimated time: 1.5-2 hours")
    print("="*80)
    print()

    # Note: CSV already exists with Safety Products, we'll append to it
    # No need to recreate the CSV file or headers

    total_products = 0
    category_totals = {'21': 9016, '09': 0, '05': 0}  # Safety already complete
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

            # Scrape each subcategory
            for i, (cat_name, cat_url, db_code) in enumerate(CATEGORIES, 1):
                print(f"[{i}/{len(CATEGORIES)}] {cat_name} (DB Code: {db_code})")
                subcat_products = 0

                # Scrape all pages in this subcategory
                for page_num in range(1, 50):  # Max 50 pages per subcategory
                    try:
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
                                        'db_category_code': db_code,
                                        'url': product_url or ''
                                    })

                            except:
                                continue

                        # Save to CSV
                        if products:
                            with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.DictWriter(f, fieldnames=['name', 'price', 'category', 'db_category_code', 'url'])
                                for product in products:
                                    writer.writerow(product)

                        subcat_products += len(products)
                        total_products += len(products)
                        category_totals[db_code] += len(products)
                        print(f"{len(products)} products")

                    except Exception as e:
                        if 'Timeout' in str(e):
                            print(f"Timeout")
                            break
                        else:
                            print(f"Error")
                            break

                elapsed = (time.time() - start_time) / 60
                print(f"  Subcategory: {subcat_products} | Total: {total_products} | Time: {elapsed:.1f}min")
                print(f"  Progress: Safety={category_totals['21']}, Tools={category_totals['09']}, Cleaning={category_totals['05']}\n")

            # Final stats
            elapsed = (time.time() - start_time) / 60
            print("="*80)
            print("SCRAPING COMPLETE")
            print("="*80)
            print(f"Safety Products (21):    {category_totals['21']:,} products (Expected: 9,129)")
            print(f"Power Tools (09):        {category_totals['09']:,} products (Expected: 4,927)")
            print(f"Cleaning Products (05):  {category_totals['05']:,} products (Expected: 3,210)")
            print(f"\nTotal Scraped:           {total_products:,} products")
            print(f"Time elapsed:            {elapsed:.1f} minutes ({elapsed/60:.1f} hours)")
            print(f"Output file:             {OUTPUT_CSV}")
            print("="*80)

        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(scrape_all())
