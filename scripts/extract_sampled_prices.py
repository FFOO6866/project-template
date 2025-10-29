"""
Sampled ERP Price Extraction - FAST
Samples pages across entire ERP range to quickly find YOUR products

Strategy: Extract every 25th page across all 2,797 pages
This covers the entire SKU range in ~15-20 minutes instead of 105 minutes

Author: Horme Production Team
Date: 2025-10-22
"""

import os
import sys
import time
import psycopg2
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
from decimal import Decimal

# Configuration
ERP_LOGIN_URL = "https://www.horme.com.sg/admin/admin_login.aspx"
ERP_USERNAME = "integrum"
ERP_PASSWORD = "@ON2AWYH4B3"
ERP_PRODUCT_PAGE = "https://www.horme.com.sg/admin/admin_product.aspx"

# Database configuration
DATABASE_HOST = os.getenv('DB_HOST', 'localhost')
DATABASE_PORT = os.getenv('DB_PORT', '5434')
DATABASE_NAME = os.getenv('DB_NAME', 'horme_db')
DATABASE_USER = os.getenv('DB_USER', 'horme_user')
DATABASE_PASSWORD = os.getenv('DB_PASSWORD', '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42')

# Sampling configuration
TOTAL_PAGES = 2797
SAMPLE_INTERVAL = 25  # Extract every 25th page
PAGES_TO_SAMPLE = list(range(1, TOTAL_PAGES + 1, SAMPLE_INTERVAL))

# Statistics
stats = {
    'pages_sampled': 0,
    'products_extracted': 0,
    'products_with_prices': 0,
    'database_updated': 0,
    'database_not_found': 0,
    'errors': 0,
    'start_time': time.time()
}


def get_db_connection():
    """Get PostgreSQL connection"""
    try:
        conn = psycopg2.connect(
            host=DATABASE_HOST,
            port=DATABASE_PORT,
            database=DATABASE_NAME,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        return None


def login_to_erp(page: Page) -> bool:
    """Log into Horme ERP"""
    print("\n" + "="*80)
    print("LOGGING INTO HORME ERP")
    print("="*80)

    try:
        print(f"Navigating to: {ERP_LOGIN_URL}")
        page.goto(ERP_LOGIN_URL, wait_until='networkidle', timeout=30000)

        page.locator('input[name*="username" i]').first.fill(ERP_USERNAME)
        page.locator('input[type="password"]').first.fill(ERP_PASSWORD)
        page.locator('input[type="submit"]').first.click()

        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=10000)

        if 'login' in page.url.lower():
            print("[FAILED] Login failed")
            return False

        print("[SUCCESS] Login successful!")
        return True

    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return False


def navigate_to_product_page(page: Page) -> bool:
    """Navigate to Product Management page"""
    try:
        print(f"\nNavigating to Product Management...")
        page.goto(ERP_PRODUCT_PAGE, wait_until='networkidle', timeout=30000)
        time.sleep(2)
        return True
    except Exception as e:
        print(f"[ERROR] Navigation failed: {e}")
        return False


def navigate_to_page(page: Page, target_page: int) -> bool:
    """Navigate to specific page number"""
    try:
        # Type page number in the input box
        page_input = page.locator('input.fg-paging-input').first
        page_input.clear()
        page_input.fill(str(target_page))
        page_input.press('Enter')

        time.sleep(2)
        page.wait_for_load_state('networkidle', timeout=10000)
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to navigate to page {target_page}: {e}")
        return False


def parse_price(price_text: str) -> Optional[Decimal]:
    """Parse price from text like '$5.0000'"""
    if not price_text:
        return None
    cleaned = price_text.replace('$', '').replace(',', '').strip()
    try:
        return Decimal(cleaned)
    except:
        return None


def extract_products_from_current_page(page: Page) -> List[Dict]:
    """Extract products from current page"""
    products = []

    try:
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')

        table = soup.find('table', {'id': 'dataTable'})
        if not table:
            return products

        tbody = table.find('tbody')
        if not tbody:
            return products

        rows = tbody.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 9:
                continue

            try:
                # Column 2: SKU
                sku_cell = cells[1]
                sku_link = sku_cell.find('a')
                sku = sku_link.get_text(strip=True) if sku_link else ''

                # Column 3: Product Name
                name_cell = cells[2]
                name_link = name_cell.find('a')
                name = name_link.get_text(strip=True) if name_link else ''

                # Column 5: Brand
                brand = cells[4].get_text(strip=True)

                # Column 9: RN Price
                price_text = cells[8].get_text(strip=True)
                price = parse_price(price_text)

                if sku and price is not None:
                    products.append({
                        'sku': sku,
                        'name': name,
                        'brand': brand,
                        'price': price,
                        'price_text': price_text
                    })
                    stats['products_with_prices'] += 1

                stats['products_extracted'] += 1

            except Exception as e:
                stats['errors'] += 1
                continue

        return products

    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        return products


def update_database_with_prices(products: List[Dict]):
    """Update database with extracted prices"""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            for product in products:
                sku = product['sku']
                price = product['price']

                cur.execute("""
                    UPDATE products SET
                        price = %s,
                        currency = 'SGD',
                        updated_at = NOW()
                    WHERE sku = %s
                """, (float(price), sku))

                if cur.rowcount > 0:
                    stats['database_updated'] += 1
                else:
                    stats['database_not_found'] += 1

        conn.commit()

    except Exception as e:
        print(f"  [ERROR] Database update failed: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    """Main execution"""
    print("="*80)
    print("HORME ERP SAMPLED PRICE EXTRACTION - FAST METHOD")
    print("="*80)
    print(f"Sampling Strategy: Every {SAMPLE_INTERVAL}th page")
    print(f"Total Pages: {TOTAL_PAGES}")
    print(f"Pages to Sample: {len(PAGES_TO_SAMPLE)}")
    print(f"Expected Time: 15-20 minutes")
    print("="*80)

    with sync_playwright() as p:
        print("\nLaunching browser...")

        browser = p.chromium.launch(
            headless=True,
            slow_mo=50
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )

        page = context.new_page()

        # Login
        if not login_to_erp(page):
            browser.close()
            return

        # Navigate to products
        if not navigate_to_product_page(page):
            browser.close()
            return

        print("\n" + "="*80)
        print("SAMPLING PAGES ACROSS ENTIRE ERP RANGE")
        print("="*80)

        # Sample pages
        for i, page_num in enumerate(PAGES_TO_SAMPLE, 1):
            print(f"\n[Sample {i}/{len(PAGES_TO_SAMPLE)}] Page {page_num}")

            # Navigate to specific page
            if not navigate_to_page(page, page_num):
                print(f"  Skipping page {page_num}")
                continue

            # Extract products
            products = extract_products_from_current_page(page)
            print(f"  Extracted {len(products)} products with prices")

            if products:
                # Update database
                update_database_with_prices(products)
                print(f"  DB Updated: {stats['database_updated']} total")

            stats['pages_sampled'] = i

            # Progress report every 10 samples
            if i % 10 == 0:
                elapsed = time.time() - stats['start_time']
                samples_per_min = i / (elapsed / 60)
                remaining = len(PAGES_TO_SAMPLE) - i
                eta_minutes = remaining / samples_per_min if samples_per_min > 0 else 0

                print(f"\n[PROGRESS]")
                print(f"  Samples: {i} / {len(PAGES_TO_SAMPLE)} ({i/len(PAGES_TO_SAMPLE)*100:.1f}%)")
                print(f"  Products Found: {stats['products_with_prices']:,}")
                print(f"  DB Updated: {stats['database_updated']:,}")
                print(f"  DB Not Found: {stats['database_not_found']:,}")
                print(f"  Speed: {samples_per_min:.1f} pages/min")
                print(f"  ETA: {eta_minutes:.1f} minutes")

        browser.close()

    # Final statistics
    elapsed = time.time() - stats['start_time']

    print("\n" + "="*80)
    print("SAMPLING COMPLETE")
    print("="*80)
    print(f"Pages Sampled:      {stats['pages_sampled']:,} / {len(PAGES_TO_SAMPLE)}")
    print(f"Products Extracted: {stats['products_extracted']:,}")
    print(f"With Prices:        {stats['products_with_prices']:,}")
    print(f"DB Updated:         {stats['database_updated']:,}")
    print(f"DB Not Found:       {stats['database_not_found']:,}")
    print(f"Errors:             {stats['errors']}")
    print(f"\nTotal Time:         {elapsed/60:.1f} minutes")
    print(f"Coverage:           ~{stats['pages_sampled']/TOTAL_PAGES*100:.1f}% of ERP pages")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Sampling stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
