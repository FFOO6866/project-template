"""
Improved Website Price Scraper - Direct Product URL Approach
Uses product SKU to construct URLs and extract prices
"""

import asyncio
import psycopg2
from playwright.async_api import async_playwright
import json
import time
from decimal import Decimal
import re

# Database configuration
DATABASE_HOST = 'localhost'
DATABASE_PORT = '5432'
DATABASE_NAME = 'horme_db'
DATABASE_USER = 'horme_user'
DATABASE_PASSWORD = '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42'

# Website credentials
WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

# Scraping settings
BATCH_SIZE = 10
CHECKPOINT_FILE = "website_price_scraping_checkpoint.json"

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
    """Login to horme.com.sg - Improved approach"""
    print("\n" + "="*80)
    print("LOGGING INTO HORME.COM.SG")
    print("="*80)

    try:
        # Navigate to homepage
        print(f"[INFO] Navigating to {WEBSITE_URL}...")
        await page.goto(WEBSITE_URL, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(2000)

        # Try clicking on user icon in top right
        print("[INFO] Looking for user account icon...")

        # Multiple strategies to find and click account/login
        account_selectors = [
            'a[href*="customer/account"]',
            'a[href*="login"]',
            'a[title*="Account"]',
            'a[title*="Login"]',
            '.header-links a:has-text("Account")',
            '.header-links a:has-text("Login")',
            '[class*="account"]',
            '[class*="login"]'
        ]

        login_clicked = False
        for selector in account_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=3000)
                if element:
                    print(f"[SUCCESS] Found account link: {selector}")
                    await element.click()
                    await page.wait_for_timeout(3000)
                    login_clicked = True
                    break
            except:
                continue

        if not login_clicked:
            print("[INFO] Trying direct login URL...")
            await page.goto(f"{WEBSITE_URL}/customer/account/login/", wait_until='domcontentloaded')
            await page.wait_for_timeout(2000)

        # Fill in email
        print("[INFO] Filling in login credentials...")
        email_selectors = [
            'input#email',
            'input[name="login[username]"]',
            'input[type="email"]',
            'input[placeholder*="email" i]'
        ]

        email_filled = False
        for selector in email_selectors:
            try:
                email_field = await page.wait_for_selector(selector, timeout=3000)
                if email_field:
                    await email_field.fill(LOGIN_EMAIL)
                    print(f"[SUCCESS] Filled email: {selector}")
                    email_filled = True
                    break
            except:
                continue

        if not email_filled:
            print("[ERROR] Could not find email field")
            return False

        # Fill in password
        password_selectors = [
            'input#pass',
            'input[name="login[password]"]',
            'input[type="password"]'
        ]

        password_filled = False
        for selector in password_selectors:
            try:
                password_field = await page.wait_for_selector(selector, timeout=3000)
                if password_field:
                    await password_field.fill(LOGIN_PASSWORD)
                    print(f"[SUCCESS] Filled password: {selector}")
                    password_filled = True
                    break
            except:
                continue

        if not password_filled:
            print("[ERROR] Could not find password field")
            return False

        # Submit form
        print("[INFO] Submitting login...")
        submit_selectors = [
            'button[type="submit"]',
            'button.action.login',
            'input[type="submit"]',
            'button:has-text("Sign In")',
            'button:has-text("Login")'
        ]

        submit_clicked = False
        for selector in submit_selectors:
            try:
                submit_button = await page.wait_for_selector(selector, timeout=3000)
                if submit_button:
                    await submit_button.click()
                    print(f"[SUCCESS] Clicked submit: {selector}")
                    submit_clicked = True
                    break
            except:
                continue

        if not submit_clicked:
            await page.keyboard.press('Enter')
            print("[INFO] Pressed Enter to submit")

        # Wait for login
        await page.wait_for_timeout(4000)

        # Check if logged in
        current_url = page.url
        page_content = await page.content()

        if 'logout' in page_content.lower() or 'my account' in page_content.lower():
            print("[SUCCESS] Login successful!")
            return True
        else:
            print("[WARNING] Login status uncertain, continuing anyway...")
            return True

    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return False


async def extract_price_from_product_page(page, sku):
    """Extract price from product page"""

    # Try different URL patterns
    url_patterns = [
        f"{WEBSITE_URL}/catalogsearch/result/?q={sku}",
        f"{WEBSITE_URL}/search?q={sku}",
        f"{WEBSITE_URL}/catalogsearch/result/index/?q={sku}"
    ]

    for url in url_patterns:
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(1500)

            # Look for price on page
            price_selectors = [
                '.price',
                '.price-box .price',
                '[data-price-type="finalPrice"]',
                '.product-info-price .price',
                'span.price',
                'div.price',
                '[itemprop="price"]'
            ]

            for selector in price_selectors:
                try:
                    price_elements = await page.query_selector_all(selector)
                    for element in price_elements:
                        text = await element.text_content()
                        if text:
                            # Extract price using regex
                            match = re.search(r'\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', text.replace(',', ''))
                            if match:
                                price_str = match.group(1).replace(',', '')
                                price = Decimal(price_str)
                                if price > 0:
                                    return price
                except:
                    continue

        except Exception as e:
            continue

    return None


async def scrape_batch(page, products, conn):
    """Scrape prices for a batch of products"""

    for product in products:
        product_id, sku, name = product[0], product[1], product[2]

        print(f"\n[{stats['products_processed']+1}] Processing: {sku}")

        try:
            price = await extract_price_from_product_page(page, sku)

            stats['products_processed'] += 1

            if price:
                print(f"  [FOUND] Price: ${price}")
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
                            print(f"  [UPDATED] Database updated")

                    conn.commit()
                except Exception as e:
                    print(f"  [ERROR] Database update failed: {e}")
                    conn.rollback()
            else:
                print(f"  [NOT FOUND] No price found")
                stats['products_not_found'] += 1

        except Exception as e:
            print(f"  [ERROR] {e}")
            stats['errors'] += 1

        # Rate limiting
        await asyncio.sleep(1)


async def main():
    """Main scraping function"""
    print("\n" + "="*80)
    print("IMPROVED WEBSITE PRICE SCRAPER")
    print("="*80)
    print(f"Website: {WEBSITE_URL}")
    print(f"Database: {DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")
    print()

    # Load checkpoint
    checkpoint = load_checkpoint()
    last_product_id = checkpoint.get('last_product_id', 0)

    # Connect to database
    conn = get_db_connection()
    if not conn:
        return

    # Get products without prices
    print("[INFO] Loading products without prices...")
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, sku, name
            FROM products
            WHERE id > %s
                AND sku IS NOT NULL
                AND price IS NULL
            ORDER BY id
            LIMIT 100
        """, (last_product_id,))

        products = cur.fetchall()

    print(f"[INFO] Found {len(products)} products to process")

    if len(products) == 0:
        print("[INFO] No products to scrape!")
        return

    # Launch browser
    async with async_playwright() as p:
        print("\n[INFO] Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Login
        login_success = await login_to_website(page)

        if not login_success:
            print("[WARNING] Login uncertain, but continuing...")

        print("\n" + "="*80)
        print("STARTING PRICE EXTRACTION")
        print("="*80)

        # Process products
        for i in range(0, len(products), BATCH_SIZE):
            batch = products[i:i+BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (len(products) + BATCH_SIZE - 1) // BATCH_SIZE

            print(f"\n[BATCH {batch_num}/{total_batches}]")

            await scrape_batch(page, batch, conn)

            # Save checkpoint
            last_id = batch[-1][0]
            save_checkpoint(last_id)

            # Progress report
            elapsed = time.time() - stats['start_time']
            rate = stats['products_processed'] / elapsed if elapsed > 0 else 0

            print(f"\n[PROGRESS]")
            print(f"  Processed: {stats['products_processed']}/{len(products)}")
            print(f"  Found prices: {stats['products_with_prices']}")
            print(f"  Updated DB: {stats['products_updated']}")
            print(f"  Not found: {stats['products_not_found']}")
            print(f"  Errors: {stats['errors']}")
            print(f"  Rate: {rate:.2f} products/sec")

        await browser.close()

    conn.close()

    print("\n" + "="*80)
    print("SCRAPING COMPLETE")
    print("="*80)
    print(f"Total processed: {stats['products_processed']}")
    print(f"Prices found: {stats['products_with_prices']}")
    print(f"Database updated: {stats['products_updated']}")


if __name__ == '__main__':
    import os
    asyncio.run(main())
