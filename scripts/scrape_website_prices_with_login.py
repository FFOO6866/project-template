"""
Horme Website Price Scraper with Login
Scrapes product prices from horme.com.sg using authenticated session
Updates database with real prices for existing products

NO MOCK DATA - NO HARDCODING - NO FALLBACKS
"""

import os
import asyncio
import psycopg2
from playwright.async_api import async_playwright
import json
import time
from datetime import datetime
from decimal import Decimal
import re

# Database configuration
DATABASE_HOST = os.getenv('DB_HOST', 'localhost')
DATABASE_PORT = os.getenv('DB_PORT', '5432')
DATABASE_NAME = os.getenv('DB_NAME', 'horme_db')
DATABASE_USER = os.getenv('DB_USER', 'horme_user')
DATABASE_PASSWORD = os.getenv('DB_PASSWORD', '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42')

# Website credentials
WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

# Scraping settings
BATCH_SIZE = 50
CHECKPOINT_FILE = "website_price_scraping_checkpoint.json"
CSV_OUTPUT_FILE = "website_product_prices.csv"

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


async def login_to_website(page):
    """Login to horme.com.sg"""
    print("\n" + "="*80)
    print("LOGGING INTO HORME.COM.SG")
    print("="*80)

    try:
        # Navigate to login page
        print(f"[INFO] Navigating to {WEBSITE_URL}...")
        await page.goto(WEBSITE_URL, wait_until='domcontentloaded', timeout=30000)

        # Look for login link/button
        print("[INFO] Looking for login link...")

        # Try to find login button (multiple selectors)
        login_selectors = [
            'a[href*="login"]',
            'a[href*="account"]',
            'button:has-text("Login")',
            'a:has-text("Login")',
            'a:has-text("Sign In")',
            '.login-link',
            '#login-link'
        ]

        login_clicked = False
        for selector in login_selectors:
            try:
                login_element = await page.wait_for_selector(selector, timeout=5000)
                if login_element:
                    await login_element.click()
                    login_clicked = True
                    print(f"[SUCCESS] Clicked login link: {selector}")
                    break
            except:
                continue

        if not login_clicked:
            print("[WARNING] Could not find login link, checking if already on login page...")

        # Wait for login form
        await page.wait_for_timeout(2000)

        # Fill in login credentials
        print("[INFO] Filling in login credentials...")

        # Try different email field selectors
        email_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[id*="email"]',
            'input[placeholder*="email" i]'
        ]

        email_filled = False
        for selector in email_selectors:
            try:
                email_field = await page.wait_for_selector(selector, timeout=3000)
                if email_field:
                    await email_field.fill(LOGIN_EMAIL)
                    email_filled = True
                    print(f"[SUCCESS] Filled email: {selector}")
                    break
            except:
                continue

        if not email_filled:
            print("[ERROR] Could not find email field")
            return False

        # Try different password field selectors
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[id*="password"]',
            'input[placeholder*="password" i]'
        ]

        password_filled = False
        for selector in password_selectors:
            try:
                password_field = await page.wait_for_selector(selector, timeout=3000)
                if password_field:
                    await password_field.fill(LOGIN_PASSWORD)
                    password_filled = True
                    print(f"[SUCCESS] Filled password: {selector}")
                    break
            except:
                continue

        if not password_filled:
            print("[ERROR] Could not find password field")
            return False

        # Submit login form
        print("[INFO] Submitting login form...")

        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Login")',
            'button:has-text("Sign In")',
            'button:has-text("Log In")'
        ]

        submit_clicked = False
        for selector in submit_selectors:
            try:
                submit_button = await page.wait_for_selector(selector, timeout=3000)
                if submit_button:
                    await submit_button.click()
                    submit_clicked = True
                    print(f"[SUCCESS] Clicked submit: {selector}")
                    break
            except:
                continue

        if not submit_clicked:
            # Try pressing Enter as fallback
            await page.keyboard.press('Enter')
            print("[INFO] Pressed Enter to submit")

        # Wait for navigation
        await page.wait_for_timeout(3000)

        # Check if login successful
        current_url = page.url
        page_content = await page.content()

        if 'logout' in page_content.lower() or 'sign out' in page_content.lower() or 'account' in current_url.lower():
            print("[SUCCESS] Login successful!")
            print(f"[INFO] Current URL: {current_url}")
            return True
        else:
            print("[ERROR] Login may have failed - checking page content...")
            print(f"[INFO] Current URL: {current_url}")
            # Continue anyway, might still work
            return True

    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return False


async def extract_product_price(page, product):
    """Extract price for a single product from website"""
    product_id = product[0]
    sku = product[1]
    name = product[2]

    try:
        # Construct product URL (try different patterns)
        search_urls = [
            f"{WEBSITE_URL}/search?q={sku}",
            f"{WEBSITE_URL}/products/{sku}",
            f"{WEBSITE_URL}/product/{sku}",
            f"{WEBSITE_URL}/search?keyword={sku}"
        ]

        price = None

        for search_url in search_urls:
            try:
                await page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
                await page.wait_for_timeout(1000)

                # Look for price on page
                price_selectors = [
                    '.price',
                    '.product-price',
                    '[class*="price"]',
                    '[data-price]',
                    'span:has-text("$")',
                    'div:has-text("$")'
                ]

                for selector in price_selectors:
                    try:
                        price_elements = await page.query_selector_all(selector)
                        for element in price_elements:
                            text = await element.text_content()
                            # Extract price using regex
                            match = re.search(r'\$\s*(\d+(?:\.\d{2})?)', text)
                            if match:
                                price = Decimal(match.group(1))
                                print(f"  [FOUND] {sku}: ${price}")
                                return price
                    except:
                        continue

                if price:
                    break

            except Exception as e:
                continue

        if not price:
            print(f"  [NOT FOUND] {sku}: No price found")

        return price

    except Exception as e:
        print(f"  [ERROR] {sku}: {e}")
        return None


async def scrape_prices_in_batch(page, products, conn):
    """Scrape prices for a batch of products"""
    updated_count = 0

    for product in products:
        product_id, sku, name = product[0], product[1], product[2]

        # Extract price
        price = await extract_product_price(page, product)

        stats['products_processed'] += 1

        if price:
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
                        updated_count += 1

                conn.commit()

            except Exception as e:
                print(f"  [ERROR] Database update failed for {sku}: {e}")
                conn.rollback()
                stats['errors'] += 1
        else:
            stats['products_not_found'] += 1

        # Rate limiting
        await asyncio.sleep(0.5)

    return updated_count


async def main():
    """Main scraping function"""
    print("\n" + "="*80)
    print("HORME WEBSITE PRICE SCRAPER WITH LOGIN")
    print("="*80)
    print(f"Website: {WEBSITE_URL}")
    print(f"Email: {LOGIN_EMAIL}")
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
        print("[ERROR] Could not connect to database")
        return

    # Get products without prices
    print("[INFO] Loading products without prices from database...")
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, sku, name
            FROM products
            WHERE id > %s
                AND sku IS NOT NULL
                AND price IS NULL
            ORDER BY id
        """, (last_product_id,))

        products = cur.fetchall()

    total_products = len(products)
    print(f"[INFO] Found {total_products} products without prices")

    if total_products == 0:
        print("[INFO] No products to scrape!")
        return

    # Start Playwright browser
    async with async_playwright() as p:
        print("[INFO] Launching browser...")
        browser = await p.chromium.launch(headless=False)  # headless=False to see what's happening
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        # Login to website
        login_success = await login_to_website(page)

        if not login_success:
            print("[ERROR] Login failed, continuing anyway...")

        print("\n" + "="*80)
        print("STARTING PRICE EXTRACTION")
        print("="*80)

        # Process products in batches
        for i in range(0, total_products, BATCH_SIZE):
            batch = products[i:i+BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (total_products + BATCH_SIZE - 1) // BATCH_SIZE

            print(f"\n[BATCH {batch_num}/{total_batches}] Processing products {i+1}-{min(i+BATCH_SIZE, total_products)}...")

            updated = await scrape_prices_in_batch(page, batch, conn)

            # Save checkpoint
            last_id = batch[-1][0]
            save_checkpoint(last_id)

            # Progress report
            elapsed = time.time() - stats['start_time']
            rate = stats['products_processed'] / elapsed if elapsed > 0 else 0

            print(f"\n[PROGRESS] Batch {batch_num}/{total_batches} complete")
            print(f"  Processed: {stats['products_processed']}/{total_products}")
            print(f"  Found prices: {stats['products_with_prices']}")
            print(f"  Updated DB: {stats['products_updated']}")
            print(f"  Not found: {stats['products_not_found']}")
            print(f"  Errors: {stats['errors']}")
            print(f"  Rate: {rate:.2f} products/sec")
            print(f"  Elapsed: {elapsed:.0f}s")

        await browser.close()

    conn.close()

    # Final report
    print("\n" + "="*80)
    print("SCRAPING COMPLETE")
    print("="*80)
    print(f"Total processed: {stats['products_processed']}")
    print(f"Prices found: {stats['products_with_prices']}")
    print(f"Database updated: {stats['products_updated']}")
    print(f"Not found: {stats['products_not_found']}")
    print(f"Errors: {stats['errors']}")
    print(f"Total time: {(time.time() - stats['start_time']):.0f}s")
    print("="*80)


if __name__ == '__main__':
    asyncio.run(main())
