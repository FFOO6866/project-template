"""
Comprehensive Category Scraper for Horme Website
Scrapes all 5 main categories to get complete product data with prices

Strategy:
1. Scrape 5 main category pages (Safety, Power Tools x3, Cleaning)
2. Navigate to each subcategory automatically
3. Extract ALL products with prices, page by page
4. Save to CSV for fuzzy matching with database
"""
import asyncio
import csv
import json
import time
from playwright.async_api import async_playwright
import re
from pathlib import Path

# Website configuration
WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

# Main categories to scrape
MAIN_CATEGORIES = [
    {'code': '21', 'name': 'Safety Products', 'url': 'category.aspx?c=18'},
    {'code': '09', 'name': 'Power Tools - Corded', 'url': 'category.aspx?c=1'},
    {'code': '09', 'name': 'Power Tools - Cordless', 'url': 'category.aspx?c=50'},
    {'code': '09', 'name': 'Power Tools - Accessories', 'url': 'category.aspx?c=9'},
    {'code': '05', 'name': 'Cleaning Products', 'url': 'category.aspx?c=7'},
]

# Output files
OUTPUT_CSV = 'scraped_products_all_categories.csv'
CHECKPOINT_FILE = 'comprehensive_scraping_checkpoint.json'
STATS_FILE = 'scraping_stats.json'

# Scraping configuration
REQUEST_DELAY = 1  # seconds between requests
MAX_RETRIES = 3


def load_checkpoint():
    """Load checkpoint to resume scraping"""
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_category_index': 0,
        'last_subcategory_url': None,
        'products_scraped': 0,
        'timestamp': time.time()
    }


def save_checkpoint(checkpoint):
    """Save checkpoint"""
    checkpoint['timestamp'] = time.time()
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def save_product_to_csv(product, mode='a'):
    """Save product to CSV file"""
    fieldnames = ['sku', 'name', 'price', 'currency', 'brand', 'category', 'url']

    file_exists = Path(OUTPUT_CSV).exists()

    with open(OUTPUT_CSV, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists or mode == 'w':
            writer.writeheader()

        writer.writerow(product)


async def login(page):
    """Login to Horme website"""
    import sys
    print("\n[LOGIN] Logging in to horme.com.sg...", flush=True)
    sys.stdout.flush()

    try:
        await page.goto(f"{WEBSITE_URL}/login.aspx", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)

        await page.fill('#ctl00_pgContent_email', LOGIN_EMAIL)
        await page.fill('#ctl00_pgContent_pwd', LOGIN_PASSWORD)
        await page.click('#btnLogin')
        await asyncio.sleep(4)

        import sys
        print("  [OK] Login successful", flush=True)
        sys.stdout.flush()
        return True

    except Exception as e:
        import sys
        print(f"  [ERROR] Login failed: {e}", flush=True)
        sys.stdout.flush()
        return False


async def get_subcategory_links(page, main_category_url):
    """Get all subcategory links from a main category page"""
    print(f"\n  [INFO] Finding subcategories...")

    try:
        await page.goto(f"{WEBSITE_URL}/{main_category_url}", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)

        # Look for subcategory links (products.aspx links on category pages)
        subcategory_links = []

        # Check if this is a category page with subcategories or a direct product listing
        product_links = await page.locator('a[href*="products.aspx?c="]').all()

        if len(product_links) > 0:
            # This category has subcategories
            for link in product_links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()

                    if href and text and 'products.aspx?c=' in href:
                        text = text.strip()
                        if text and len(text) < 100:  # Reasonable category name
                            subcategory_links.append({
                                'name': text,
                                'url': href
                            })
                except:
                    pass

            # Remove duplicates
            seen = set()
            unique_subcategories = []
            for link in subcategory_links:
                if link['url'] not in seen:
                    seen.add(link['url'])
                    unique_subcategories.append(link)

            print(f"  [OK] Found {len(unique_subcategories)} subcategories")
            return unique_subcategories

        else:
            # This is already a product listing page (no subcategories)
            print(f"  [OK] This is a direct product listing (no subcategories)")
            return [{'name': 'Main Category', 'url': main_category_url}]

    except Exception as e:
        print(f"  [ERROR] Failed to get subcategories: {e}")
        return []


async def scrape_product_page(page, url, category_name, page_num=1):
    """Scrape products from a single product listing page"""
    products = []

    try:
        # Navigate to page
        full_url = f"{WEBSITE_URL}/{url}" if not url.startswith('http') else url

        await page.goto(full_url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(REQUEST_DELAY)

        # Find all product elements
        product_elements = await page.locator('.product').all()

        for product_elem in product_elements:
            try:
                # Extract product name and URL
                name_link = product_elem.locator('.product__details h2 a').first
                product_name = await name_link.inner_text()
                product_url = await name_link.get_attribute('href')

                # Extract SKU (if visible)
                sku = None
                try:
                    sku_elem = product_elem.locator('.sku, [class*="sku"]').first
                    sku = await sku_elem.inner_text()
                    sku = sku.strip()
                except:
                    pass

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

                # Extract brand (if visible)
                brand = None
                try:
                    brand_elem = product_elem.locator('.brand, [class*="brand"]')
                    brand = await brand_elem.inner_text()
                    brand = brand.strip()
                except:
                    pass

                if product_name and price and price > 0:
                    products.append({
                        'sku': sku or '',
                        'name': product_name.strip(),
                        'price': price,
                        'currency': 'SGD',
                        'brand': brand or '',
                        'category': category_name,
                        'url': product_url or ''
                    })

            except Exception as e:
                # Skip individual product errors
                continue

        return products

    except Exception as e:
        print(f"      [ERROR] Failed to scrape page {page_num}: {e}")
        return []


async def scrape_subcategory(page, subcategory, category_code, stats):
    """Scrape all pages of a subcategory"""
    print(f"\n    [SUBCATEGORY] {subcategory['name']}")

    try:
        # Go to first page
        await page.goto(f"{WEBSITE_URL}/{subcategory['url']}", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)

        # Check for pagination
        total_pages = 1
        try:
            pagination_links = await page.locator('.pagination a, [class*="pagination"] a').all()
            for link in pagination_links:
                text = await link.inner_text()
                try:
                    page_num = int(text.strip())
                    if page_num > total_pages:
                        total_pages = page_num
                except ValueError:
                    continue
        except:
            pass

        print(f"      Total pages: {total_pages}")

        # Scrape each page
        for page_num in range(1, total_pages + 1):
            print(f"      Page {page_num}/{total_pages}...", end=' ')

            products = await scrape_product_page(page, subcategory['url'], subcategory['name'], page_num)

            # Save products to CSV
            for product in products:
                save_product_to_csv(product)
                stats['products_scraped'] += 1

            print(f"{len(products)} products")

            # Navigate to next page if not last
            if page_num < total_pages:
                try:
                    next_button = page.locator(f'a:has-text("{page_num + 1}")')
                    await next_button.click()
                    await asyncio.sleep(REQUEST_DELAY)
                except:
                    print(f"      [WARN] Could not navigate to page {page_num + 1}")
                    break

        stats['subcategories_completed'] += 1

    except Exception as e:
        print(f"      [ERROR] Failed to scrape subcategory: {e}")
        stats['errors'] += 1


async def scrape_all_categories():
    """Main scraping function"""

    # Initialize CSV with headers
    save_product_to_csv({'sku': '', 'name': '', 'price': '', 'currency': '', 'brand': '', 'category': '', 'url': ''}, mode='w')

    # Load checkpoint
    checkpoint = load_checkpoint()

    # Initialize stats
    stats = {
        'start_time': time.time(),
        'products_scraped': checkpoint.get('products_scraped', 0),
        'categories_completed': 0,
        'subcategories_completed': 0,
        'errors': 0
    }

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
                print("[ERROR] Login failed, aborting...")
                return stats

            # Scrape each main category
            start_idx = checkpoint.get('last_category_index', 0)

            for i in range(start_idx, len(MAIN_CATEGORIES)):
                category = MAIN_CATEGORIES[i]

                print(f"\n{'='*80}")
                print(f"[{i+1}/{len(MAIN_CATEGORIES)}] CATEGORY: {category['name']} (Code: {category['code']})")
                print(f"{'='*80}")

                # Get subcategories
                subcategories = await get_subcategory_links(page, category['url'])

                # Scrape each subcategory
                for subcategory in subcategories:
                    await scrape_subcategory(page, subcategory, category['code'], stats)

                    # Save checkpoint after each subcategory
                    checkpoint['last_category_index'] = i
                    checkpoint['last_subcategory_url'] = subcategory['url']
                    checkpoint['products_scraped'] = stats['products_scraped']
                    save_checkpoint(checkpoint)

                stats['categories_completed'] += 1

                # Small delay between categories
                await asyncio.sleep(2)

            # Save final stats
            stats['end_time'] = time.time()
            stats['duration_seconds'] = stats['end_time'] - stats['start_time']
            stats['duration_minutes'] = stats['duration_seconds'] / 60

            with open(STATS_FILE, 'w') as f:
                json.dump(stats, f, indent=2)

            print(f"\n{'='*80}")
            print("SCRAPING COMPLETE")
            print(f"{'='*80}")
            print(f"Products scraped: {stats['products_scraped']}")
            print(f"Categories completed: {stats['categories_completed']}/{len(MAIN_CATEGORIES)}")
            print(f"Subcategories completed: {stats['subcategories_completed']}")
            print(f"Errors: {stats['errors']}")
            print(f"Duration: {stats['duration_minutes']:.1f} minutes")
            print(f"Output file: {OUTPUT_CSV}")
            print(f"{'='*80}")

        except Exception as e:
            print(f"\n[ERROR] Scraping failed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

    return stats


async def main():
    import sys
    print("="*80, flush=True)
    print("COMPREHENSIVE HORME CATEGORY SCRAPER", flush=True)
    print("="*80, flush=True)
    print("\nTarget Categories:", flush=True)
    for cat in MAIN_CATEGORIES:
        print(f"  - {cat['name']} ({cat['code']})", flush=True)
    print(f"\nOutput: {OUTPUT_CSV}", flush=True)
    print(f"Running in HEADLESS mode", flush=True)
    print("="*80, flush=True)
    print(flush=True)
    sys.stdout.flush()

    stats = await scrape_all_categories()

    return stats


if __name__ == '__main__':
    asyncio.run(main())
