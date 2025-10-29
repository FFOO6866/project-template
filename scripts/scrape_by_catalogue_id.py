"""
Direct Product Scraping Using Catalogue ID
Uses direct product URLs: https://www.horme.com.sg/product.aspx?id=XXXX
No login required - public product pages
"""

import asyncio
import psycopg2
from playwright.async_api import async_playwright
import json
import time
from decimal import Decimal
import re
import os

# Database configuration
DATABASE_HOST = 'localhost'
DATABASE_PORT = '5432'
DATABASE_NAME = 'horme_db'
DATABASE_USER = 'horme_user'
DATABASE_PASSWORD = '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42'

# Website base URL
WEBSITE_BASE_URL = "https://www.horme.com.sg/product.aspx?id="

# Scraping settings
BATCH_SIZE = 20
CHECKPOINT_FILE = "unique_catalogue_id_scraping_checkpoint.json"

# Statistics
stats = {
    'products_processed': 0,
    'products_with_prices': 0,
    'products_updated': 0,
    'products_not_found': 0,
    'errors': 0,
    'start_time': time.time()
}


def get_db_connection():
    """Connect to PostgreSQL database"""
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
        print(f"[ERROR] Database connection failed: {e}")
        return None


def load_checkpoint():
    """Load last checkpoint"""
    try:
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {'last_product_id': 0, 'stats': stats}


def save_checkpoint(last_product_id: int):
    """Save progress checkpoint"""
    checkpoint = {
        'last_product_id': last_product_id,
        'timestamp': time.time(),
        'stats': stats
    }
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)
    print(f"  [CHECKPOINT] Saved at product ID {last_product_id}")


async def extract_price_from_page(page, catalogue_id):
    """Extract price from product page using Catalogue ID - from JSON-LD structured data"""

    url = f"{WEBSITE_BASE_URL}{catalogue_id}"

    try:
        # Navigate to product page
        await page.goto(url, wait_until='domcontentloaded', timeout=15000)
        await page.wait_for_timeout(2000)  # Wait for page to fully load

        # Check if page loaded successfully
        page_content = await page.content()

        if 'product not found' in page_content.lower() or 'error' in page_content.lower():
            return None

        # PRIMARY METHOD: Extract price from JSON-LD structured data
        # This is more reliable than scraping visual elements
        try:
            json_ld_elements = await page.query_selector_all('script[type="application/ld+json"]')
            for element in json_ld_elements:
                content = await element.text_content()
                if not content:
                    continue

                try:
                    import json
                    data = json.loads(content)

                    # Look for price in offers
                    if 'offers' in data:
                        offers = data['offers']
                        if isinstance(offers, dict) and 'price' in offers:
                            price_value = offers['price']
                            if price_value and str(price_value).strip():
                                try:
                                    price = Decimal(str(price_value))
                                    if price > 0:
                                        print(f"    [JSON-LD] Found price in offers: {price}")
                                        return price
                                except:
                                    pass

                    # Look for price at top level
                    if 'price' in data:
                        price_value = data['price']
                        if price_value and str(price_value).strip():
                            try:
                                price = Decimal(str(price_value))
                                if price > 0:
                                    print(f"    [JSON-LD] Found price at top level: {price}")
                                    return price
                            except:
                                pass
                except Exception as e:
                    # Debug: print JSON parsing errors
                    continue
        except Exception as e:
            print(f"    [DEBUG] JSON-LD extraction error: {e}")
            pass

        # FALLBACK 1: Try HTML price selectors (less reliable)
        price_selectors = [
            '#ctl00_pgContent_price',
            '#ctl00_pgContent_original_price',
            '[id*="pgContent_price"]'
        ]

        for selector in price_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.text_content()
                    if text and text.strip() != 'N.A.':
                        match = re.search(r'(?:S\$|SGD|$)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', text.replace(',', ''))
                        if match:
                            price_str = match.group(1).replace(',', '')
                            try:
                                price = Decimal(price_str)
                                if price > 0:
                                    return price
                            except:
                                continue
            except:
                continue

        # FALLBACK 2: Search HTML source for price in JSON
        try:
            matches = re.findall(r'"price"\s*:\s*"?(\d+\.?\d*)"?', page_content)
            if matches:
                # Get the first reasonable price
                for match in matches:
                    try:
                        price = Decimal(match)
                        if 0.01 < price < 100000:  # Reasonable range
                            return price
                    except:
                        continue
        except:
            pass

        return None

    except Exception as e:
        print(f"    [ERROR] Failed to extract from catalogue ID {catalogue_id}: {e}")
        return None


async def scrape_batch(page, products, conn):
    """Scrape prices for a batch of products"""

    for product in products:
        product_id, catalogue_id, name = product[0], product[1], product[2]

        # Handle Unicode characters in product names
        try:
            name_display = name[:60] if len(name) > 60 else name
        except:
            name_display = name.encode('ascii', 'replace').decode('ascii')[:60]

        print(f"\n[{stats['products_processed']+1}] Catalogue ID: {catalogue_id}")
        print(f"    Product: {name_display}...")

        try:
            price = await extract_price_from_page(page, catalogue_id)

            stats['products_processed'] += 1

            if price:
                print(f"    [FOUND] Price: ${price}")
                stats['products_with_prices'] += 1

                # Update database
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE products
                            SET price = %s,
                                currency = 'SGD',
                                updated_at = NOW()
                            WHERE id = %s
                        """, (float(price), product_id))

                        if cur.rowcount > 0:
                            stats['products_updated'] += 1
                            print(f"    [UPDATED] Database updated successfully")

                    conn.commit()
                except Exception as e:
                    print(f"    [ERROR] Database update failed: {e}")
                    conn.rollback()
                    stats['errors'] += 1
            else:
                print(f"    [NOT FOUND] No price found on page")
                stats['products_not_found'] += 1

        except Exception as e:
            print(f"    [ERROR] {e}")
            stats['errors'] += 1

        # Rate limiting - be respectful
        await asyncio.sleep(0.5)


async def main():
    """Main scraping function"""
    print("\n" + "="*80)
    print("UNIQUE CATALOGUE ID SCRAPING (OPTIMIZED)")
    print("="*80)
    print(f"Base URL: {WEBSITE_BASE_URL}XXXX")
    print(f"Database: {DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")
    print()

    # Load checkpoint
    checkpoint = load_checkpoint()
    last_product_id = checkpoint.get('last_product_id', 0)

    if last_product_id > 0:
        print(f"[INFO] Resuming from product ID: {last_product_id}")

    # Connect to database
    conn = get_db_connection()
    if not conn:
        return

    # Get products with UNIQUE catalogue_id but no price
    print("[INFO] Loading products with UNIQUE Catalogue IDs but no prices...")
    with conn.cursor() as cur:
        cur.execute("""
            SELECT p.id, p.catalogue_id, p.name
            FROM products p
            WHERE p.id > %s
                AND p.catalogue_id IS NOT NULL
                AND p.price IS NULL
                AND p.catalogue_id IN (
                    SELECT catalogue_id
                    FROM products
                    WHERE catalogue_id IS NOT NULL
                    GROUP BY catalogue_id
                    HAVING COUNT(*) = 1
                )
            ORDER BY p.id
        """, (last_product_id,))

        products = cur.fetchall()

    total_products = len(products)
    print(f"[INFO] Found {total_products} products to process")

    if total_products == 0:
        print("[INFO] No products to scrape!")
        conn.close()
        return

    # Launch browser
    async with async_playwright() as p:
        print("\n[INFO] Launching browser (visible mode for compatibility)...")
        browser = await p.chromium.launch(headless=False)  # Visible mode - website blocks headless
        context = await browser.new_context()
        page = await context.new_page()

        print("\n" + "="*80)
        print("STARTING PRICE EXTRACTION")
        print("="*80)

        # Process products in batches
        for i in range(0, total_products, BATCH_SIZE):
            batch = products[i:i+BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (total_products + BATCH_SIZE - 1) // BATCH_SIZE

            print(f"\n{'='*80}")
            print(f"BATCH {batch_num}/{total_batches} - Products {i+1} to {min(i+BATCH_SIZE, total_products)}")
            print(f"{'='*80}")

            await scrape_batch(page, batch, conn)

            # Save checkpoint after each batch
            last_id = batch[-1][0]
            save_checkpoint(last_id)

            # Progress report
            elapsed = time.time() - stats['start_time']
            rate = stats['products_processed'] / elapsed if elapsed > 0 else 0
            success_rate = (stats['products_with_prices'] / stats['products_processed'] * 100) if stats['products_processed'] > 0 else 0

            print(f"\n{'-'*80}")
            print(f"PROGRESS REPORT - Batch {batch_num}/{total_batches}")
            print(f"{'-'*80}")
            print(f"  Processed:      {stats['products_processed']:,}/{total_products:,} ({stats['products_processed']/total_products*100:.1f}%)")
            print(f"  Prices found:   {stats['products_with_prices']:,} ({success_rate:.1f}%)")
            print(f"  DB updated:     {stats['products_updated']:,}")
            print(f"  Not found:      {stats['products_not_found']:,}")
            print(f"  Errors:         {stats['errors']:,}")
            print(f"  Rate:           {rate:.2f} products/sec")
            print(f"  Elapsed:        {elapsed:.0f}s ({elapsed/60:.1f} min)")

            if stats['products_processed'] < total_products:
                remaining = total_products - stats['products_processed']
                est_time = remaining / rate if rate > 0 else 0
                print(f"  Est. remaining: {est_time:.0f}s ({est_time/60:.1f} min)")
            print(f"{'-'*80}")

        await browser.close()

    conn.close()

    # Final report
    print("\n" + "="*80)
    print("SCRAPING COMPLETE!")
    print("="*80)
    print(f"Total processed:    {stats['products_processed']:,}")
    print(f"Prices found:       {stats['products_with_prices']:,} ({stats['products_with_prices']/stats['products_processed']*100:.1f}%)")
    print(f"Database updated:   {stats['products_updated']:,}")
    print(f"Not found:          {stats['products_not_found']:,}")
    print(f"Errors:             {stats['errors']:,}")
    print(f"Total time:         {(time.time() - stats['start_time']):.0f}s ({(time.time() - stats['start_time'])/60:.1f} min)")
    print("="*80)


if __name__ == '__main__':
    asyncio.run(main())
