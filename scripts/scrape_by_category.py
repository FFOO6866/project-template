"""
Category-Based Website Price Scraper
Systematically scrape all product categories and extract prices
"""

import asyncio
import os
import json
import time
import psycopg2
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from decimal import Decimal
import re

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'horme_db'),
    'user': os.getenv('DB_USER', 'horme_user'),
    'password': os.getenv('DB_PASSWORD', '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42')
}

# Website credentials
WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

# Scraping configuration
CHECKPOINT_FILE = 'category_scraping_checkpoint.json'
REQUEST_DELAY = 1  # seconds between requests

# Hardcoded category list (from explore_categories.py results)
CATEGORIES = [
    {'name': 'PPE Safety Equipment', 'url': 'category.aspx?c=18', 'type': 'main'},
    {'name': 'Safety Shoes & Safety Boots', 'url': 'products.aspx?c=70', 'type': 'products'},
    {'name': 'Hand & Arm Protection', 'url': 'products.aspx?c=71', 'type': 'products'},
    {'name': 'Eye Protection', 'url': 'products.aspx?c=111', 'type': 'products'},
    {'name': 'Hearing Protection', 'url': 'products.aspx?c=207', 'type': 'products'},
    {'name': 'Face Masks & Respirators', 'url': 'products.aspx?c=78', 'type': 'products'},
    {'name': 'Head & Face Protection', 'url': 'products.aspx?c=206', 'type': 'products'},
    {'name': 'Protective Apparel', 'url': 'products.aspx?c=157', 'type': 'products'},
    {'name': 'Ladders, Trolleys & Storage', 'url': 'category.aspx?c=17', 'type': 'main'},
    {'name': 'Ladders, Step Stools & Work Platforms', 'url': 'products.aspx?c=91', 'type': 'products'},
    {'name': 'Trolley & Carts', 'url': 'products.aspx?c=125', 'type': 'products'},
    {'name': 'Storage Boxes & Plastic Containers', 'url': 'products.aspx?c=134', 'type': 'products'},
    {'name': 'Shelves, Cabinets, Drawers & Racks', 'url': 'products.aspx?c=186', 'type': 'products'},
    {'name': 'Toolboxes, Tool Bags & Work Benches', 'url': 'products.aspx?c=92', 'type': 'products'},
    {'name': 'Castors & Wheels', 'url': 'products.aspx?c=5', 'type': 'products'},
    {'name': 'Waterproof Hard Cases', 'url': 'products.aspx?c=184', 'type': 'products'},
    {'name': 'Cleaning Products', 'url': 'category.aspx?c=7', 'type': 'main'},
    {'name': 'Trash & Recycling Bins', 'url': 'products.aspx?c=149', 'type': 'products'},
    {'name': 'Trash Bags & Accessories', 'url': 'products.aspx?c=212', 'type': 'products'},
    {'name': 'Cleaning Tools', 'url': 'products.aspx?c=29', 'type': 'products'},
    {'name': 'Cleaning Trolleys', 'url': 'products.aspx?c=214', 'type': 'products'},
    {'name': 'Pressure Washers & Steam Cleaners', 'url': 'products.aspx?c=28', 'type': 'products'},
    {'name': 'Vacuum Cleaners & Carpet Cleaners', 'url': 'products.aspx?c=27', 'type': 'products'},
]


def load_checkpoint():
    """Load checkpoint from file"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_category_index': 0,
        'scraped_products': {},  # product_id -> price
        'timestamp': time.time(),
        'stats': {
            'categories_processed': 0,
            'products_found': 0,
            'prices_extracted': 0,
            'products_updated': 0,
            'errors': 0,
            'start_time': time.time()
        }
    }


def save_checkpoint(checkpoint):
    """Save checkpoint to file"""
    checkpoint['timestamp'] = time.time()
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def update_product_price(product_id, price):
    """Update product price in database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE products
        SET price = %s,
            currency = 'SGD',
            updated_at = NOW()
        WHERE id = %s
    """, (price, product_id))

    conn.commit()
    cursor.close()
    conn.close()


def find_matching_product_in_db(product_name):
    """Find product in database by fuzzy name matching"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Try exact name match first
    cursor.execute("""
        SELECT id, name, sku
        FROM products
        WHERE LOWER(name) = LOWER(%s)
        LIMIT 1
    """, (product_name,))

    result = cursor.fetchone()

    # If no exact match, try similarity search
    if not result:
        cursor.execute("""
            SELECT id, name, sku,
                   similarity(name, %s) as sim
            FROM products
            WHERE similarity(name, %s) > 0.5
            ORDER BY sim DESC
            LIMIT 1
        """, (product_name, product_name))
        result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        return {'id': result[0], 'name': result[1], 'sku': result[2]}
    return None


async def login_to_website(page):
    """Login to horme.com.sg website"""
    print("\n[LOGIN] Logging in to horme.com.sg...")

    try:
        await page.goto(f"{WEBSITE_URL}/login.aspx", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)

        await page.fill('#ctl00_pgContent_email', LOGIN_EMAIL)
        await page.fill('#ctl00_pgContent_pwd', LOGIN_PASSWORD)
        await page.click('#btnLogin')
        await asyncio.sleep(4)

        print("  [OK] Login successful!")
        return True

    except Exception as e:
        print(f"  [ERROR] Login failed: {e}")
        return False


async def scrape_category_page(page, category_url, page_num=1):
    """Scrape products from a single category page"""
    try:
        # Navigate to category page (with page number if specified)
        full_url = f"{WEBSITE_URL}/{category_url}"
        if page_num > 1:
            full_url += f"#page-{page_num}"

        await page.goto(full_url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(REQUEST_DELAY)

        products = []

        # Find all product containers
        product_elements = await page.locator('.product').all()

        for product_elem in product_elements:
            try:
                # Extract product name and URL
                name_link = product_elem.locator('h2 a')
                product_name = await name_link.inner_text()
                product_url = await name_link.get_attribute('href')

                # Extract product ID from URL (product.aspx?id=XXXX)
                product_id = None
                if product_url:
                    match = re.search(r'id=(\d+)', product_url)
                    if match:
                        product_id = match.group(1)

                # Extract price
                price_elem = product_elem.locator('.popular__pro__price')
                price_text = await price_elem.inner_text()

                # Parse price (e.g., "S$33.50" -> 33.50)
                price = None
                if price_text:
                    price_match = re.search(r'[\$S]?\s*([0-9,]+\.?\d*)', price_text)
                    if price_match:
                        price_str = price_match.group(1).replace(',', '')
                        price = float(price_str)

                if product_name and price and price > 0:
                    products.append({
                        'id': product_id,
                        'name': product_name.strip(),
                        'price': price,
                        'url': product_url
                    })

            except Exception as e:
                # Skip individual product errors
                continue

        return products

    except Exception as e:
        print(f"    [ERROR] Failed to scrape page: {e}")
        return []


async def get_pagination_info(page):
    """Get total number of pages for current category"""
    try:
        pagination_links = await page.locator('.pagination a').all()
        max_page = 1

        for link in pagination_links:
            text = await link.inner_text()
            # Try to parse page number
            try:
                page_num = int(text.strip())
                if page_num > max_page:
                    max_page = page_num
            except ValueError:
                continue

        return max_page

    except Exception as e:
        return 1


async def scrape_categories(headless=False):
    """Main scraping function for all categories"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        # Load checkpoint
        checkpoint = load_checkpoint()

        try:
            # Login
            login_success = await login_to_website(page)
            if not login_success:
                print("[ERROR] Login failed, aborting...")
                return checkpoint

            # Process categories starting from checkpoint
            start_idx = checkpoint['last_category_index']

            for i in range(start_idx, len(CATEGORIES)):
                category = CATEGORIES[i]

                # Skip main categories (they just contain subcategories)
                if category['type'] == 'main':
                    print(f"\n[SKIP] {category['name']} (main category)")
                    checkpoint['last_category_index'] = i
                    save_checkpoint(checkpoint)
                    continue

                print(f"\n[{i+1}/{len(CATEGORIES)}] Scraping: {category['name']}")
                print(f"  URL: {category['url']}")

                # Navigate to first page
                await page.goto(f"{WEBSITE_URL}/{category['url']}",
                              wait_until='networkidle', timeout=30000)
                await asyncio.sleep(2)

                # Get total pages
                total_pages = await get_pagination_info(page)
                print(f"  Total pages: {total_pages}")

                # Scrape all pages in this category
                category_products = []
                for page_num in range(1, total_pages + 1):
                    print(f"    Page {page_num}/{total_pages}...", end=' ')

                    products = await scrape_category_page(page, category['url'], page_num)
                    category_products.extend(products)

                    print(f"Found {len(products)} products")

                    # Small delay between pages
                    await asyncio.sleep(1)

                print(f"\n  Total products in category: {len(category_products)}")

                # Update database with scraped prices
                updated_count = 0
                for product in category_products:
                    product_id = product['id']

                    # Check if already scraped
                    if product_id not in checkpoint['scraped_products']:
                        # Find matching product in database
                        db_product = find_matching_product_in_db(product['name'])

                        if db_product:
                            # Update price in database
                            update_product_price(db_product['id'], product['price'])
                            checkpoint['scraped_products'][product_id] = product['price']
                            checkpoint['stats']['products_updated'] += 1
                            updated_count += 1

                checkpoint['stats']['products_found'] += len(category_products)
                checkpoint['stats']['prices_extracted'] += len(category_products)
                checkpoint['stats']['categories_processed'] += 1
                checkpoint['last_category_index'] = i

                print(f"  Updated {updated_count} products in database")

                # Save checkpoint after each category
                save_checkpoint(checkpoint)

                # Delay between categories
                await asyncio.sleep(2)

        finally:
            await browser.close()

        return checkpoint


async def main(headless=False):
    """Main entry point"""
    print("=" * 80)
    print("HORME CATEGORY-BASED PRICE SCRAPER")
    print("=" * 80)
    print(f"Website: {WEBSITE_URL}")
    print(f"Total Categories: {len(CATEGORIES)}")
    print(f"Browser Mode: {'Headless (background)' if headless else 'Visible'}")
    print("=" * 80)
    print()

    checkpoint = await scrape_categories(headless=headless)

    # Final stats
    print("\n" + "=" * 80)
    print("SCRAPING COMPLETE")
    print("=" * 80)
    print(f"Categories Processed: {checkpoint['stats']['categories_processed']}")
    print(f"Products Found: {checkpoint['stats']['products_found']}")
    print(f"Prices Extracted: {checkpoint['stats']['prices_extracted']}")
    print(f"Products Updated in DB: {checkpoint['stats']['products_updated']}")
    print(f"Total Time: {(time.time() - checkpoint['stats']['start_time'])/60:.1f} minutes")
    print("=" * 80)


if __name__ == '__main__':
    import sys

    headless_mode = '--headless' in sys.argv

    if headless_mode:
        print("\n[INFO] Running in HEADLESS mode")
    else:
        print("\n[INFO] Running in VISIBLE mode (you can watch the browser)")

    asyncio.run(main(headless=headless_mode))
