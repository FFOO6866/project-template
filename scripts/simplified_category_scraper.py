"""
Simplified Category Scraper - Direct & Reliable
Scrapes 5 main category URLs directly without complex subcategory logic
Based on proven working selectors
"""
import asyncio
import csv
import json
import time
from playwright.async_api import async_playwright
import re
from pathlib import Path
import sys

# Website configuration
WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

# Direct category URLs (no subcategory discovery needed)
CATEGORIES = [
    {'name': 'Safety Products', 'code': '21', 'url': 'category.aspx?c=18'},
    {'name': 'Power Tools - Corded', 'code': '09', 'url': 'category.aspx?c=1'},
    {'name': 'Power Tools - Cordless', 'code': '09', 'url': 'category.aspx?c=50'},
    {'name': 'Power Tools - Accessories', 'code': '09', 'url': 'category.aspx?c=9'},
    {'name': 'Cleaning Products', 'code': '05', 'url': 'category.aspx?c=7'},
]

# Output files
OUTPUT_CSV = 'scraped_products_simple.csv'
CHECKPOINT_FILE = 'simple_scraper_checkpoint.json'

# Configuration
REQUEST_DELAY = 2  # seconds between page requests
MAX_PAGES_PER_CATEGORY = 50  # safety limit


def log(msg):
    """Print with flush"""
    print(msg, flush=True)
    sys.stdout.flush()


def load_checkpoint():
    """Load checkpoint"""
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_category_idx': 0,
        'last_page': 0,
        'products_scraped': 0,
        'timestamp': time.time()
    }


def save_checkpoint(checkpoint):
    """Save checkpoint"""
    checkpoint['timestamp'] = time.time()
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def init_csv():
    """Initialize CSV with headers"""
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['sku', 'name', 'price', 'currency', 'brand', 'category', 'url'])
        writer.writeheader()


def save_product(product):
    """Append product to CSV"""
    with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['sku', 'name', 'price', 'currency', 'brand', 'category', 'url'])
        writer.writerow(product)


async def login(page):
    """Login to website"""
    log("\n[LOGIN] Logging in...")

    try:
        await page.goto(f"{WEBSITE_URL}/login.aspx", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)

        await page.fill('#ctl00_pgContent_email', LOGIN_EMAIL)
        await page.fill('#ctl00_pgContent_pwd', LOGIN_PASSWORD)
        await page.click('#btnLogin')
        await asyncio.sleep(4)

        log("  [OK] Login successful")
        return True

    except Exception as e:
        log(f"  [ERROR] Login failed: {e}")
        return False


async def scrape_page(page, category_url, category_name, page_num):
    """Scrape a single page and return products"""
    products = []

    try:
        # Build URL with page number
        url = f"{WEBSITE_URL}/{category_url}"
        if page_num > 1:
            # Check URL structure - some use ?page=, some use &page=
            separator = '&' if '?' in category_url else '?'
            url = f"{url}{separator}page={page_num}"

        log(f"    Page {page_num}: {url}")

        await page.goto(url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(REQUEST_DELAY)

        # Get all product elements
        product_elements = await page.locator('.product').all()

        if len(product_elements) == 0:
            log(f"      No products found (end of category)")
            return []

        log(f"      Found {len(product_elements)} products")

        # Extract each product
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
                    product = {
                        'sku': '',  # SKU not easily visible
                        'name': product_name.strip(),
                        'price': price,
                        'currency': 'SGD',
                        'brand': '',  # Brand not easily visible
                        'category': category_name,
                        'url': product_url or ''
                    }
                    products.append(product)

            except Exception as e:
                # Skip individual product errors
                continue

        log(f"      Extracted {len(products)} valid products")
        return products

    except Exception as e:
        log(f"      [ERROR] Page scraping failed: {e}")
        return []


async def scrape_category(page, category, checkpoint):
    """Scrape all pages of a category"""
    log(f"\n{'='*80}")
    log(f"CATEGORY: {category['name']} (Code: {category['code']})")
    log(f"{'='*80}")

    start_page = 1
    if checkpoint.get('last_category_idx') == CATEGORIES.index(category):
        start_page = checkpoint.get('last_page', 1) + 1
        log(f"  Resuming from page {start_page}")

    category_products = 0

    for page_num in range(start_page, MAX_PAGES_PER_CATEGORY + 1):
        products = await scrape_page(page, category['url'], category['name'], page_num)

        if not products:
            log(f"  No more products - category complete")
            break

        # Save products to CSV
        for product in products:
            save_product(product)
            category_products += 1
            checkpoint['products_scraped'] += 1

        # Update checkpoint
        checkpoint['last_category_idx'] = CATEGORIES.index(category)
        checkpoint['last_page'] = page_num
        save_checkpoint(checkpoint)

        log(f"  Total in category so far: {category_products}")

    log(f"\n  Category complete: {category_products} products")
    return category_products


async def main():
    """Main scraping function"""
    log("="*80)
    log("SIMPLIFIED HORME CATEGORY SCRAPER")
    log("="*80)
    log(f"\nCategories: {len(CATEGORIES)}")
    for cat in CATEGORIES:
        log(f"  - {cat['name']} ({cat['code']})")
    log(f"\nOutput: {OUTPUT_CSV}")
    log(f"Headless: True")
    log("="*80)

    # Initialize
    checkpoint = load_checkpoint()

    if checkpoint.get('last_category_idx', 0) == 0 and checkpoint.get('last_page', 0) == 0:
        # Fresh start - initialize CSV
        init_csv()

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
            if not await login(page):
                log("[ERROR] Login failed, aborting")
                return

            # Scrape each category
            start_idx = checkpoint.get('last_category_idx', 0)

            for i in range(start_idx, len(CATEGORIES)):
                category = CATEGORIES[i]

                category_count = await scrape_category(page, category, checkpoint)

                # Reset page counter for next category
                checkpoint['last_page'] = 0
                save_checkpoint(checkpoint)

            # Final stats
            elapsed = time.time() - start_time
            log(f"\n{'='*80}")
            log("SCRAPING COMPLETE")
            log(f"{'='*80}")
            log(f"Total products scraped: {checkpoint['products_scraped']}")
            log(f"Time elapsed: {elapsed/60:.1f} minutes")
            log(f"Output file: {OUTPUT_CSV}")
            log(f"{'='*80}")

        except Exception as e:
            log(f"\n[ERROR] Scraping failed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
