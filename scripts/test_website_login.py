"""
Test Website Login and Price Extraction
Quick test to verify login works and we can extract prices
"""

import asyncio
from playwright.async_api import async_playwright
import psycopg2

# Database config
DATABASE_HOST = 'localhost'
DATABASE_PORT = '5432'
DATABASE_NAME = 'horme_db'
DATABASE_USER = 'horme_user'
DATABASE_PASSWORD = '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42'

# Website credentials
WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"


async def test_login_and_scrape():
    """Test login and price extraction"""

    print("\n" + "="*80)
    print("TESTING WEBSITE LOGIN AND PRICE EXTRACTION")
    print("="*80)

    # Connect to database
    conn = psycopg2.connect(
        host=DATABASE_HOST,
        port=DATABASE_PORT,
        database=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD
    )

    # Get a few products to test
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, sku, name
            FROM products
            WHERE sku IS NOT NULL AND price IS NULL
            LIMIT 3
        """)
        test_products = cur.fetchall()

    print(f"\n[INFO] Testing with {len(test_products)} products:")
    for p in test_products:
        print(f"  - {p[1]}: {p[2][:50]}")

    # Launch browser
    async with async_playwright() as p:
        print("\n[INFO] Launching browser...")
        browser = await p.chromium.launch(headless=False)  # Visible browser
        context = await browser.new_context()
        page = await context.new_page()

        # Go to website
        print(f"\n[INFO] Navigating to {WEBSITE_URL}...")
        await page.goto(WEBSITE_URL, wait_until='domcontentloaded')
        await page.wait_for_timeout(2000)

        print(f"[INFO] Current URL: {page.url}")
        print(f"[INFO] Page title: {await page.title()}")

        # Take screenshot
        await page.screenshot(path='test_homepage.png')
        print("[INFO] Screenshot saved: test_homepage.png")

        # Look for login
        page_content = await page.content()
        print(f"\n[INFO] Page has 'login' keyword: {'login' in page_content.lower()}")
        print(f"[INFO] Page has 'account' keyword: {'account' in page_content.lower()}")
        print(f"[INFO] Page has 'sign in' keyword: {'sign in' in page_content.lower()}")

        # Try to find and click login
        try:
            # Try multiple login selectors
            login_found = False
            for selector in ['a:has-text("Login")', 'a:has-text("Sign In")', 'a[href*="login"]', 'a[href*="account"]']:
                try:
                    login_link = await page.wait_for_selector(selector, timeout=3000)
                    if login_link:
                        print(f"[SUCCESS] Found login link: {selector}")
                        await login_link.click()
                        await page.wait_for_timeout(2000)
                        login_found = True
                        break
                except:
                    continue

            if not login_found:
                print("[WARNING] No login link found, might already be on login page or logged in")
        except Exception as e:
            print(f"[ERROR] Finding login: {e}")

        # Take screenshot of login page
        await page.screenshot(path='test_login_page.png')
        print("[INFO] Screenshot saved: test_login_page.png")

        print("\n[INFO] Keeping browser open for 60 seconds...")
        print("[INFO] Please manually check the browser window")
        print("[INFO] You can manually try to login and navigate to a product page")

        # Wait 60 seconds
        await page.wait_for_timeout(60000)

        await browser.close()

    conn.close()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("Check the screenshots:")
    print("  - test_homepage.png")
    print("  - test_login_page.png")


if __name__ == '__main__':
    asyncio.run(test_login_and_scrape())
