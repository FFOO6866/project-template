"""
Complete Horme ERP Price Extraction
Extracts ALL 69,926 products with prices from ERP

This script will:
1. Log into the ERP admin panel
2. Navigate through all ~2,797 pages
3. Extract SKU and Price from each product
4. Save to CSV for database import
5. Update database with extracted prices

Author: Horme Production Team
Date: 2025-10-22
"""

import os
import sys
import time
import json
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import csv
from decimal import Decimal

# Configuration
ERP_LOGIN_URL = "https://www.horme.com.sg/admin/admin_login.aspx"
ERP_USERNAME = "integrum"
ERP_PASSWORD = "@ON2AWYH4B3"
ERP_PRODUCT_PAGE = "https://www.horme.com.sg/admin/admin_product.aspx"

# Database configuration
DATABASE_HOST = os.getenv('DB_HOST', 'localhost')
DATABASE_PORT = os.getenv('DB_PORT', '5432')
DATABASE_NAME = os.getenv('DB_NAME', 'horme_db')
DATABASE_USER = os.getenv('DB_USER', 'horme_user')
DATABASE_PASSWORD = os.getenv('DB_PASSWORD', '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42')

# Extraction settings
SAVE_TO_CSV = True
UPDATE_DATABASE = True
CSV_OUTPUT_FILE = "erp_product_prices.csv"
CHECKPOINT_FILE = "erp_extraction_checkpoint.json"

# Statistics
stats = {
    'pages_processed': 0,
    'products_extracted': 0,
    'products_with_prices': 0,
    'products_updated_in_db': 0,
    'products_not_in_db': 0,
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


def extract_products_from_current_page(page: Page) -> List[Dict]:
    """Extract products from current page"""
    products = []

    try:
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')

        # Find the product table tbody
        table = soup.find('table', {'id': 'dataTable'})
        if not table:
            print("  [WARNING] Product table not found")
            return products

        tbody = table.find('tbody')
        if not tbody:
            print("  [WARNING] Table body not found")
            return products

        rows = tbody.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 9:
                continue

            try:
                # Extract data from cells
                # Column 2: SKU (inside <a> tag)
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
                print(f"  [ERROR] Failed to parse row: {e}")
                stats['errors'] += 1
                continue

        return products

    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        return products


def click_next_page(page: Page) -> bool:
    """Click the Next button to go to next page"""
    try:
        # Find Next button
        next_button = page.locator('a.next.fg-button.ui-button').first

        # Check if disabled
        classes = next_button.get_attribute('class')
        if 'ui-state-disabled' in classes:
            return False  # No more pages

        # Click next
        next_button.click()
        time.sleep(2)  # Wait for page to load
        page.wait_for_load_state('networkidle', timeout=10000)

        return True

    except Exception as e:
        print(f"  [ERROR] Failed to click next: {e}")
        return False


def save_to_csv_file(products: List[Dict]):
    """Save products to CSV file"""
    try:
        file_exists = os.path.exists(CSV_OUTPUT_FILE)

        with open(CSV_OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['sku', 'name', 'brand', 'price', 'price_text'])

            if not file_exists:
                writer.writeheader()

            for product in products:
                writer.writerow(product)

    except Exception as e:
        print(f"  [ERROR] Failed to save to CSV: {e}")


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

                # Update product by SKU
                cur.execute("""
                    UPDATE products
                    SET price = %s,
                        currency = 'SGD',
                        updated_at = NOW()
                    WHERE sku = %s
                """, (float(price), sku))

                if cur.rowcount > 0:
                    stats['products_updated_in_db'] += 1
                else:
                    stats['products_not_in_db'] += 1

        conn.commit()

    except Exception as e:
        print(f"  [ERROR] Database update failed: {e}")
        conn.rollback()
    finally:
        conn.close()


def save_checkpoint(page_number: int):
    """Save progress checkpoint"""
    checkpoint = {
        'page_number': page_number,
        'timestamp': time.time(),
        'stats': stats
    }

    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def load_checkpoint() -> Optional[int]:
    """Load progress checkpoint"""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                checkpoint = json.load(f)
                return checkpoint.get('page_number', 1)
        except:
            pass
    return None


def main():
    """Main execution"""
    print("="*80)
    print("HORME ERP COMPLETE PRICE EXTRACTION")
    print("="*80)
    print(f"Target: 69,926 products across ~2,797 pages")
    print(f"Save to CSV: {SAVE_TO_CSV}")
    print(f"Update Database: {UPDATE_DATABASE}")
    print("="*80)

    # Check for checkpoint - auto-resume
    start_page = load_checkpoint()
    if start_page and start_page > 1:
        print(f"\n[CHECKPOINT] Auto-resuming from page {start_page}")
    else:
        start_page = 1

    with sync_playwright() as p:
        print("\nLaunching browser...")

        browser = p.chromium.launch(
            headless=True,  # Run in background
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
        print("EXTRACTING PRODUCTS")
        print("="*80)

        page_number = 1
        has_more_pages = True

        # Navigate to start page if resuming
        if start_page > 1:
            print(f"\nNavigating to page {start_page}...")
            for i in range(1, start_page):
                if not click_next_page(page):
                    print(f"  [WARNING] Could not navigate to page {start_page}")
                    start_page = i
                    break
            page_number = start_page

        # Extract all pages
        while has_more_pages:
            print(f"\n[Page {page_number}] Extracting products...")

            # Extract products from current page
            products = extract_products_from_current_page(page)
            print(f"  Extracted {len(products)} products with prices")

            if products:
                # Save to CSV
                if SAVE_TO_CSV:
                    save_to_csv_file(products)

                # Update database
                if UPDATE_DATABASE:
                    update_database_with_prices(products)
                    print(f"  Updated {stats['products_updated_in_db']} in database")

            stats['pages_processed'] = page_number

            # Save checkpoint every 10 pages
            if page_number % 10 == 0:
                save_checkpoint(page_number)
                print(f"\n[CHECKPOINT] Progress saved at page {page_number}")

            # Print progress every 50 pages
            if page_number % 50 == 0:
                elapsed = time.time() - stats['start_time']
                products_per_sec = stats['products_extracted'] / elapsed
                eta_seconds = (69926 - stats['products_extracted']) / products_per_sec if products_per_sec > 0 else 0

                print(f"\n[PROGRESS]")
                print(f"  Pages: {page_number} / ~2,797")
                print(f"  Products: {stats['products_extracted']:,} / 69,926")
                print(f"  With Prices: {stats['products_with_prices']:,}")
                print(f"  DB Updates: {stats['products_updated_in_db']:,}")
                print(f"  Speed: {products_per_sec:.1f} products/sec")
                print(f"  ETA: {eta_seconds/60:.1f} minutes")

            # Try to go to next page
            has_more_pages = click_next_page(page)
            page_number += 1

            # Safety limit (remove in production)
            if page_number > 3000:  # Slightly more than expected 2,797
                print("\n[LIMIT] Reached maximum pages")
                break

        browser.close()

    # Final statistics
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    print(f"Pages Processed:        {stats['pages_processed']:,}")
    print(f"Products Extracted:     {stats['products_extracted']:,}")
    print(f"Products with Prices:   {stats['products_with_prices']:,}")
    print(f"Database Updates:       {stats['products_updated_in_db']:,}")
    print(f"Not in Database:        {stats['products_not_in_db']:,}")
    print(f"Errors:                 {stats['errors']}")
    print(f"\nTotal Time:             {(time.time() - stats['start_time'])/60:.1f} minutes")

    if SAVE_TO_CSV:
        print(f"\nCSV File: {CSV_OUTPUT_FILE}")

    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Saving checkpoint...")
        save_checkpoint(stats.get('pages_processed', 1))
        print("Progress saved. Run script again to resume.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        save_checkpoint(stats.get('pages_processed', 1))
        sys.exit(1)
