"""
Parallel ERP Price Extraction - Single Track
Extracts a specific page range from the ERP

Usage: python extract_parallel_track.py <track_id> <start_page> <end_page>
Example: python extract_parallel_track.py 1 1 700

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

# Get parameters
if len(sys.argv) != 4:
    print("Usage: python extract_parallel_track.py <track_id> <start_page> <end_page>")
    sys.exit(1)

TRACK_ID = int(sys.argv[1])
START_PAGE = int(sys.argv[2])
END_PAGE = int(sys.argv[3])

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

# Statistics
stats = {
    'pages_processed': 0,
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
        print(f"[Track {TRACK_ID}] ERROR: Database connection failed: {e}")
        return None


def login_to_erp(page: Page) -> bool:
    """Log into Horme ERP"""
    try:
        page.goto(ERP_LOGIN_URL, wait_until='networkidle', timeout=30000)
        page.locator('input[name*="username" i]').first.fill(ERP_USERNAME)
        page.locator('input[type="password"]').first.fill(ERP_PASSWORD)
        page.locator('input[type="submit"]').first.click()
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=10000)

        if 'login' in page.url.lower():
            return False
        return True
    except Exception as e:
        print(f"[Track {TRACK_ID}] ERROR: Login failed: {e}")
        return False


def navigate_to_product_page(page: Page) -> bool:
    """Navigate to Product Management page"""
    try:
        page.goto(ERP_PRODUCT_PAGE, wait_until='networkidle', timeout=30000)
        time.sleep(2)
        return True
    except Exception as e:
        return False


def navigate_to_page(page: Page, target_page: int) -> bool:
    """Navigate to specific page number"""
    try:
        page_input = page.locator('input.fg-paging-input').first
        page_input.clear()
        page_input.fill(str(target_page))
        page_input.press('Enter')
        time.sleep(1.5)
        page.wait_for_load_state('networkidle', timeout=10000)
        return True
    except Exception as e:
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
                sku_cell = cells[1]
                sku_link = sku_cell.find('a')
                sku = sku_link.get_text(strip=True) if sku_link else ''

                price_text = cells[8].get_text(strip=True)
                price = parse_price(price_text)

                if sku and price is not None:
                    products.append({'sku': sku, 'price': price})
                    stats['products_with_prices'] += 1

                stats['products_extracted'] += 1
            except Exception as e:
                stats['errors'] += 1
                continue

        return products
    except Exception as e:
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
        conn.rollback()
    finally:
        conn.close()


def main():
    """Main execution"""
    print(f"[Track {TRACK_ID}] Starting extraction: pages {START_PAGE}-{END_PAGE}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=50)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # Login
        if not login_to_erp(page):
            print(f"[Track {TRACK_ID}] Login failed")
            browser.close()
            return

        # Navigate to products
        if not navigate_to_product_page(page):
            print(f"[Track {TRACK_ID}] Navigation failed")
            browser.close()
            return

        # Navigate to start page
        if START_PAGE > 1:
            print(f"[Track {TRACK_ID}] Jumping to page {START_PAGE}...")
            if not navigate_to_page(page, START_PAGE):
                print(f"[Track {TRACK_ID}] Failed to jump to start page")
                browser.close()
                return

        # Extract pages
        current_page = START_PAGE
        while current_page <= END_PAGE:
            products = extract_products_from_current_page(page)

            if products:
                update_database_with_prices(products)

            stats['pages_processed'] += 1

            # Progress report every 50 pages
            if stats['pages_processed'] % 50 == 0:
                elapsed = time.time() - stats['start_time']
                pages_per_min = stats['pages_processed'] / (elapsed / 60) if elapsed > 0 else 0
                remaining_pages = END_PAGE - current_page
                eta_minutes = remaining_pages / pages_per_min if pages_per_min > 0 else 0

                print(f"[Track {TRACK_ID}] Page {current_page}/{END_PAGE} | "
                      f"Products: {stats['products_extracted']:,} | "
                      f"DB Updated: {stats['database_updated']:,} | "
                      f"ETA: {eta_minutes:.1f}min")

            # Go to next page
            if current_page < END_PAGE:
                next_button = page.locator('a.next.fg-button.ui-button').first
                classes = next_button.get_attribute('class')

                if 'ui-state-disabled' in classes:
                    break

                next_button.click()
                time.sleep(1.5)
                page.wait_for_load_state('networkidle', timeout=10000)

            current_page += 1

        browser.close()

    # Final statistics
    elapsed = time.time() - stats['start_time']
    print(f"\n[Track {TRACK_ID}] COMPLETE")
    print(f"  Pages: {stats['pages_processed']}")
    print(f"  Products: {stats['products_extracted']:,}")
    print(f"  DB Updated: {stats['database_updated']:,}")
    print(f"  Time: {elapsed/60:.1f} minutes")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[Track {TRACK_ID}] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
