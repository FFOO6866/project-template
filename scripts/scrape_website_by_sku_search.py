"""
Website Price Scraper Using SKU Search
Login to horme.com.sg and search for products by SKU to extract prices
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
CHECKPOINT_FILE = 'website_sku_scraping_checkpoint.json'
BATCH_SIZE = 50
MAX_RETRIES = 3
REQUEST_DELAY = 2  # seconds between requests


def load_checkpoint():
    """Load checkpoint from file"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_product_id': 0,
        'timestamp': time.time(),
        'stats': {
            'products_processed': 0,
            'prices_found': 0,
            'products_updated': 0,
            'not_found': 0,
            'errors': 0,
            'start_time': time.time()
        }
    }


def save_checkpoint(checkpoint):
    """Save checkpoint to file"""
    checkpoint['timestamp'] = time.time()
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def get_products_needing_prices(last_product_id=0, limit=BATCH_SIZE):
    """Get products that need prices from database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, sku, name
        FROM products
        WHERE id > %s
          AND (price IS NULL OR price = 0)
          AND sku IS NOT NULL
        ORDER BY id
        LIMIT %s
    """, (last_product_id, limit))

    products = []
    for row in cursor.fetchall():
        products.append({
            'id': row[0],
            'sku': row[1],
            'name': row[2]
        })

    cursor.close()
    conn.close()

    return products


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


async def login_to_website(page):
    """Login to horme.com.sg website"""
    print("\n[LOGIN] Attempting to login to horme.com.sg...")

    try:
        # Navigate directly to login.aspx (ASP.NET site)
        print("  [INFO] Navigating to login.aspx...")
        await page.goto(f"{WEBSITE_URL}/login.aspx", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)

        # Fill login form
        print("  [INFO] Filling login form...")

        # Email field - ASP.NET specific selectors
        email_filled = False
        email_selectors = [
            '#ctl00_pgContent_email',                  # ASP.NET ID
            'input[name="ctl00$pgContent$email"]',     # ASP.NET name
            'input[type="email"]',                     # Generic email field
            '#email'
        ]

        for selector in email_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, LOGIN_EMAIL, timeout=5000)
                    email_filled = True
                    print(f"  [OK] Filled email using: {selector}")
                    break
            except:
                continue

        if not email_filled:
            raise Exception("Could not find email input field")

        # Password field - ASP.NET specific selectors
        password_filled = False
        password_selectors = [
            '#ctl00_pgContent_pwd',                    # ASP.NET ID
            'input[name="ctl00$pgContent$pwd"]',       # ASP.NET name
            'input[type="password"]',                  # Generic password field
            '#pass'
        ]

        for selector in password_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, LOGIN_PASSWORD, timeout=5000)
                    password_filled = True
                    print(f"  [OK] Filled password using: {selector}")
                    break
            except:
                continue

        if not password_filled:
            raise Exception("Could not find password input field")

        # Click login button
        print("  [INFO] Submitting login...")

        # The visible login button is an <a> tag with id="btnLogin"
        # This triggers the hidden submit button via JavaScript
        login_button_selectors = [
            '#btnLogin',                               # Visible login button (link)
            'a[title*="login"]',                       # Backup: any link with "login" in title
            '#ctl00_pgContent_main_loginButton'        # Hidden submit button (fallback)
        ]

        button_clicked = False
        for selector in login_button_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.click(selector, timeout=5000)
                    button_clicked = True
                    print(f"  [OK] Clicked login button using: {selector}")
                    break
            except:
                continue

        if not button_clicked:
            raise Exception("Could not find login button")

        # Wait for navigation
        await asyncio.sleep(4)

        # Verify login success
        current_url = page.url
        page_content = await page.content()

        # Check for successful login indicators
        if ('default.aspx' in current_url.lower() or
            'welcome' in page_content.lower() or
            'logout' in page_content.lower() or
            'my account' in page_content.lower()):
            print("  [OK] Login successful!")
            return True
        else:
            print("  [WARNING] Login may have failed - will try to continue anyway")
            return True

    except Exception as e:
        print(f"  [ERROR] Login failed: {e}")
        return False


async def search_product_by_sku(page, search_term):
    """Search for product by name/description and extract price"""
    try:
        # Clean up search term - take first few meaningful words
        # Remove extra spaces and special characters
        clean_term = ' '.join(search_term.split())[:80]  # Limit to 80 chars

        # Find search box - prioritize visible search boxes after login
        search_selectors = [
            '.autocompleteKeyword',                    # Visible search box (header)
            '.autocompleteKeyword2',                   # Alternative search box
            'input[placeholder*="help you find"]',     # By placeholder text
            '#search',
            'input[name="q"]',
            'input[type="search"]',
            'input[placeholder*="Search"]'
        ]

        search_box = None
        for selector in search_selectors:
            try:
                locator = page.locator(selector)
                if await locator.count() > 0:
                    # Check if visible (for cases where multiple exist)
                    first_element = locator.first
                    if await first_element.is_visible():
                        search_box = first_element
                        break
                    elif search_box is None:
                        # Keep first found even if not visible
                        search_box = first_element
            except:
                continue

        if not search_box:
            return None, "Search box not found"

        # Clear and enter search term
        await search_box.clear()
        await search_box.fill(clean_term)
        await asyncio.sleep(1)

        # Submit search
        await search_box.press('Enter')
        await asyncio.sleep(REQUEST_DELAY)

        # Wait for results
        await page.wait_for_load_state('networkidle', timeout=10000)

        # Try to extract price from search results or product page
        price = await extract_price_from_page(page)

        if price:
            return price, "Success"
        else:
            return None, "Price not found on page"

    except Exception as e:
        return None, f"Error: {str(e)}"


async def extract_price_from_page(page):
    """Extract price from current page using multiple strategies"""

    # Strategy 1: JSON-LD structured data
    try:
        json_ld_scripts = await page.locator('script[type="application/ld+json"]').all()
        for script in json_ld_scripts:
            content = await script.inner_text()
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    # Check for price in offers
                    if 'offers' in data:
                        offers = data['offers']
                        if isinstance(offers, dict) and 'price' in offers:
                            price_str = str(offers['price']).replace(',', '')
                            price = float(price_str)
                            if price > 0:
                                return price
                        elif isinstance(offers, list):
                            for offer in offers:
                                if isinstance(offer, dict) and 'price' in offer:
                                    price_str = str(offer['price']).replace(',', '')
                                    price = float(price_str)
                                    if price > 0:
                                        return price
            except:
                continue
    except:
        pass

    # Strategy 2: Meta tags
    try:
        meta_price = await page.locator('meta[property="product:price:amount"]').get_attribute('content')
        if meta_price:
            price = float(meta_price)
            if price > 0:
                return price
    except:
        pass

    # Strategy 3: Common price CSS selectors
    price_selectors = [
        '.price',
        '.product-price',
        '[class*="price"]',
        '[data-price-amount]',
        '.special-price .price',
        '.regular-price .price'
    ]

    for selector in price_selectors:
        try:
            elements = await page.locator(selector).all()
            for element in elements:
                text = await element.inner_text()
                # Extract numeric price from text
                price_match = re.search(r'[\$S]?\s*([0-9,]+\.?\d*)', text)
                if price_match:
                    price_str = price_match.group(1).replace(',', '')
                    price = float(price_str)
                    if price > 0:
                        return price
        except:
            continue

    # Strategy 4: Check data attributes
    try:
        price_elements = await page.locator('[data-price-amount]').all()
        for element in price_elements:
            price_attr = await element.get_attribute('data-price-amount')
            if price_attr:
                price = float(price_attr)
                if price > 0:
                    return price
    except:
        pass

    return None


async def scrape_products_batch(products, checkpoint, headless=False):
    """Scrape a batch of products"""

    async with async_playwright() as p:
        # Launch browser (headless=True for background running)
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            # Login to website
            login_success = await login_to_website(page)

            if not login_success:
                print("[ERROR] Login failed, aborting...")
                await browser.close()
                return checkpoint

            print(f"\n[SCRAPING] Processing {len(products)} products...\n")

            for i, product in enumerate(products, 1):
                product_id = product['id']
                sku = product['sku']
                name = product['name']

                print(f"[{i}/{len(products)}] Name: {name[:60]}...")

                # Search for product by name/description
                price, status = await search_product_by_sku(page, name)

                if price:
                    # Update database
                    update_product_price(product_id, price)
                    checkpoint['stats']['prices_found'] += 1
                    checkpoint['stats']['products_updated'] += 1
                    print(f"  [OK] Price found: S${price:.2f}")

                elif "not found" in status.lower():
                    checkpoint['stats']['not_found'] += 1
                    print(f"  [NOT FOUND] {status}")

                else:
                    checkpoint['stats']['errors'] += 1
                    print(f"  [ERROR] {status}")

                checkpoint['stats']['products_processed'] += 1
                checkpoint['last_product_id'] = product_id

                # Save checkpoint every 10 products
                if i % 10 == 0:
                    save_checkpoint(checkpoint)
                    print(f"\n[CHECKPOINT] Saved at product {product_id}")
                    print(f"  Progress: {checkpoint['stats']['products_processed']} processed, "
                          f"{checkpoint['stats']['prices_found']} prices found\n")

                # Small delay between products
                await asyncio.sleep(1)

        finally:
            await browser.close()

    return checkpoint


async def main(headless=False):
    """Main scraping function"""
    print("=" * 80)
    print("HORME WEBSITE PRICE SCRAPER (SKU-BASED SEARCH)")
    print("=" * 80)
    print(f"Website: {WEBSITE_URL}")
    print(f"Login Email: {LOGIN_EMAIL}")
    print(f"Batch Size: {BATCH_SIZE} products")
    print(f"Browser Mode: {'Headless (background)' if headless else 'Visible'}")
    print("=" * 80)
    print()

    # Load checkpoint
    checkpoint = load_checkpoint()
    last_id = checkpoint['last_product_id']

    print(f"[INFO] Resuming from product ID: {last_id}")
    print(f"[INFO] Stats so far: {checkpoint['stats']}")
    print()

    # Main scraping loop
    while True:
        # Get next batch of products
        products = get_products_needing_prices(last_id, BATCH_SIZE)

        if not products:
            print("\n[COMPLETE] No more products to process!")
            break

        print(f"\n[BATCH] Loaded {len(products)} products (IDs: {products[0]['id']} to {products[-1]['id']})")

        # Scrape batch
        checkpoint = await scrape_products_batch(products, checkpoint, headless=headless)

        # Save checkpoint after batch
        save_checkpoint(checkpoint)

        last_id = checkpoint['last_product_id']

        # Show progress
        elapsed = time.time() - checkpoint['stats']['start_time']
        processed = checkpoint['stats']['products_processed']
        success_rate = (checkpoint['stats']['prices_found']/processed*100) if processed > 0 else 0

        # Calculate ETA
        if processed > 0:
            avg_time_per_product = elapsed / processed
            remaining_products = 15509 - processed  # Approximate total
            eta_seconds = avg_time_per_product * remaining_products
            eta_hours = eta_seconds / 3600

            print(f"\n[PROGRESS] Total processed: {processed:,}")
            print(f"           Prices found: {checkpoint['stats']['prices_found']:,}")
            print(f"           Success rate: {success_rate:.1f}%")
            print(f"           Time elapsed: {elapsed/60:.1f} minutes")
            print(f"           Est. completion: {eta_hours:.1f} hours ({eta_seconds/60:.0f} minutes)")
        else:
            print(f"\n[PROGRESS] Total processed: {processed:,}")
            print(f"           Prices found: {checkpoint['stats']['prices_found']:,}")
        print()

        # Small delay between batches
        print("[INFO] Waiting 5 seconds before next batch...")
        time.sleep(5)

    # Final stats
    print("\n" + "=" * 80)
    print("SCRAPING SESSION COMPLETE")
    print("=" * 80)
    print(f"Products Processed: {checkpoint['stats']['products_processed']}")
    print(f"Prices Found: {checkpoint['stats']['prices_found']}")
    print(f"Not Found: {checkpoint['stats']['not_found']}")
    print(f"Errors: {checkpoint['stats']['errors']}")
    print(f"Total Time: {(time.time() - checkpoint['stats']['start_time'])/60:.1f} minutes")
    print("=" * 80)


if __name__ == '__main__':
    import sys

    # Check for headless flag
    headless_mode = '--headless' in sys.argv

    if headless_mode:
        print("\n[INFO] Running in HEADLESS mode (browser invisible)")
        print("[INFO] Perfect for overnight/background scraping")
        print()

    asyncio.run(main(headless=headless_mode))
