"""
Targeted ERP Price Extraction
Extracts prices ONLY for products already in database (19,143 products)

This is much faster than extracting all 69,926 products!
Uses ERP search function to find specific SKUs.

Author: Horme Production Team
Date: 2025-10-22
"""

import os
import sys
import time
import json
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

# Statistics
stats = {
    'skus_processed': 0,
    'prices_found': 0,
    'prices_not_found': 0,
    'database_updated': 0,
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


def get_target_skus() -> List[str]:
    """Get list of SKUs from database"""
    print("\n" + "="*80)
    print("LOADING TARGET SKUs FROM DATABASE")
    print("="*80)

    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT sku FROM products WHERE sku IS NOT NULL ORDER BY sku")
            skus = [row[0] for row in cur.fetchall()]
        conn.close()

        print(f"Loaded {len(skus)} SKUs from database")
        return skus
    except Exception as e:
        print(f"ERROR: Failed to load SKUs: {e}")
        conn.close()
        return []


def login_to_erp(page: Page) -> bool:
    """Log into Horme ERP"""
    print("\n" + "="*80)
    print("LOGGING INTO HORME ERP")
    print("="*80)

    try:
        print(f"Navigating to: {ERP_LOGIN_URL}")
        page.goto(ERP_LOGIN_URL, wait_until='networkidle', timeout=30000)

        # Fill login form
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
        time.sleep(2)  # Let DataTables load
        return True
    except Exception as e:
        print(f"[ERROR] Navigation failed: {e}")
        return False


def parse_price(price_text: str) -> Optional[Decimal]:
    """Parse price from text like '$5.0000'"""
    if not price_text:
        return None

    # Remove $ and parse
    cleaned = price_text.replace('$', '').replace(',', '').strip()
    try:
        return Decimal(cleaned)
    except:
        return None


def search_and_extract_price(page: Page, sku: str) -> Optional[Decimal]:
    """Search for SKU in ERP and extract price"""
    try:
        # Use DataTables search box
        search_input = page.locator('input[type="search"]').first

        # Clear search box
        search_input.clear()

        # Type SKU
        search_input.fill(sku)

        # Wait for DataTables to filter
        time.sleep(1)
        page.wait_for_load_state('networkidle', timeout=5000)

        # Get page HTML
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')

        # Find the product table tbody
        table = soup.find('table', {'id': 'dataTable'})
        if not table:
            return None

        tbody = table.find('tbody')
        if not tbody:
            return None

        rows = tbody.find_all('tr')

        # Check if "No matching records found"
        if len(rows) == 1:
            first_row = rows[0]
            if 'No matching records found' in first_row.get_text():
                return None

        # Look for exact SKU match
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 9:
                continue

            # Column 2: SKU
            sku_cell = cells[1]
            sku_link = sku_cell.find('a')
            row_sku = sku_link.get_text(strip=True) if sku_link else ''

            # Exact match
            if row_sku == sku:
                # Column 9: RN Price
                price_text = cells[8].get_text(strip=True)
                return parse_price(price_text)

        return None

    except Exception as e:
        print(f"  [ERROR] Search failed for {sku}: {e}")
        stats['errors'] += 1
        return None


def update_price_in_database(sku: str, price: Decimal) -> bool:
    """Update price in database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE products SET
                    price = %s,
                    currency = 'SGD',
                    updated_at = NOW()
                WHERE sku = %s
            """, (float(price), sku))

            conn.commit()

            if cur.rowcount > 0:
                stats['database_updated'] += 1
                return True
            else:
                return False
    except Exception as e:
        print(f"  [ERROR] Database update failed for {sku}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Main execution"""
    print("="*80)
    print("HORME ERP TARGETED PRICE EXTRACTION")
    print("="*80)
    print(f"Extracting prices for products already in database")
    print("="*80)

    # Get target SKUs
    target_skus = get_target_skus()
    if not target_skus:
        print("ERROR: No SKUs found in database")
        return

    total_skus = len(target_skus)
    print(f"\nTarget: {total_skus} products")

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

        # Step 1: Login
        if not login_to_erp(page):
            browser.close()
            return

        # Step 2: Navigate to products
        if not navigate_to_product_page(page):
            browser.close()
            return

        print("\n" + "="*80)
        print("EXTRACTING PRICES")
        print("="*80)

        # Process each SKU
        for i, sku in enumerate(target_skus, 1):
            stats['skus_processed'] = i

            # Search and extract
            price = search_and_extract_price(page, sku)

            if price is not None:
                stats['prices_found'] += 1

                # Update database
                if update_price_in_database(sku, price):
                    print(f"[{i}/{total_skus}] {sku}: ${price} ✓")
                else:
                    print(f"[{i}/{total_skus}] {sku}: ${price} (DB update failed)")
            else:
                stats['prices_not_found'] += 1
                print(f"[{i}/{total_skus}] {sku}: NOT FOUND")

            # Progress report every 100 SKUs
            if i % 100 == 0:
                elapsed = time.time() - stats['start_time']
                skus_per_sec = i / elapsed
                remaining = total_skus - i
                eta_seconds = remaining / skus_per_sec if skus_per_sec > 0 else 0

                print(f"\n[PROGRESS]")
                print(f"  Processed: {i:,} / {total_skus:,} ({i/total_skus*100:.1f}%)")
                print(f"  Found: {stats['prices_found']:,}")
                print(f"  Not Found: {stats['prices_not_found']:,}")
                print(f"  DB Updated: {stats['database_updated']:,}")
                print(f"  Speed: {skus_per_sec:.1f} SKUs/sec")
                print(f"  ETA: {eta_seconds/60:.1f} minutes")
                print()

        browser.close()

    # Final statistics
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    print(f"SKUs Processed:     {stats['skus_processed']:,}")
    print(f"Prices Found:       {stats['prices_found']:,}")
    print(f"Prices Not Found:   {stats['prices_not_found']:,}")
    print(f"Database Updated:   {stats['database_updated']:,}")
    print(f"Errors:             {stats['errors']}")
    print(f"\nSuccess Rate:       {stats['prices_found']/stats['skus_processed']*100:.1f}%")
    print(f"Total Time:         {(time.time() - stats['start_time'])/60:.1f} minutes")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Extraction stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
