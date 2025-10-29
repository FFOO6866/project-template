"""
Verify the correct main Power Tools category
Check multiple category IDs to find the one with ALL power tools subcategories
"""
import asyncio
from playwright.async_api import async_playwright

WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

# Candidate category IDs to check
CANDIDATE_CATEGORIES = [
    {'id': '9', 'name': 'Power Tools - Accessories (from discovery)'},
    {'id': '08', 'name': 'Power Tools (guessing from category 05/21)'},
    {'id': '8', 'name': 'Power Tools (single digit)'},
    {'id': '09', 'name': 'Power Tools (with leading zero)'},
    {'id': '86', 'name': 'Cutting & Sawing Tools (subcategory)'},
]


async def check_category(page, cat_id, cat_name):
    """Check a single category and report what it contains"""
    print(f"\n[CHECK] Category ID: {cat_id} - {cat_name}")

    # Try both category.aspx and products.aspx
    for page_type in ['category.aspx', 'products.aspx']:
        url = f"{WEBSITE_URL}/{page_type}?c={cat_id}"
        print(f"  Trying: {url}")

        try:
            await page.goto(url, wait_until='networkidle', timeout=15000)
            await asyncio.sleep(1)

            # Check if page loaded successfully (not 404)
            page_title = await page.title()

            # Get breadcrumb or page heading
            try:
                heading = await page.locator('h1, .page-title, .category-title').first.inner_text()
                print(f"  [OK] Page title: {heading}")
            except:
                heading = page_title
                print(f"  [OK] Found page: {page_title}")

            # Count products or subcategories
            product_count = await page.locator('.product, .product-item, [class*="product"]').count()
            subcategory_count = await page.locator('a[href*="products.aspx"], a[href*="category.aspx"]').count()

            print(f"       Products visible: {product_count}")
            print(f"       Subcategory links: {subcategory_count}")

            # Take screenshot
            screenshot_path = f"verify_{page_type.split('.')[0]}_{cat_id}.png"
            await page.screenshot(path=screenshot_path)
            print(f"       Screenshot: {screenshot_path}")

            # Get all category links to see subcategories
            if page_type == 'category.aspx' and subcategory_count > 0:
                print(f"  [INFO] This looks like a MAIN category with subcategories")
                try:
                    subcat_links = await page.locator('a[href*="products.aspx"]').all()
                    print(f"  Subcategories found:")
                    for i, link in enumerate(subcat_links[:10], 1):
                        try:
                            text = await link.inner_text()
                            href = await link.get_attribute('href')
                            if text and 'product' in href.lower():
                                print(f"    {i}. {text.strip()}")
                        except:
                            pass
                except:
                    pass

            return True

        except Exception as e:
            print(f"  [ERROR] {e}")

    return False


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            # Login
            print("="*80)
            print("LOGGING IN...")
            print("="*80)

            await page.goto(f"{WEBSITE_URL}/login.aspx", wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            await page.fill('#ctl00_pgContent_email', LOGIN_EMAIL)
            await page.fill('#ctl00_pgContent_pwd', LOGIN_PASSWORD)
            await page.click('#btnLogin')
            await asyncio.sleep(4)

            print("[OK] Logged in")

            # Check each candidate category
            print("\n" + "="*80)
            print("CHECKING CANDIDATE CATEGORIES")
            print("="*80)

            for cat in CANDIDATE_CATEGORIES:
                await check_category(page, cat['id'], cat['name'])
                await asyncio.sleep(1)

            print("\n" + "="*80)
            print("VERIFICATION COMPLETE")
            print("="*80)
            print("\nReview the screenshots to determine which is the main Power Tools category")
            print("Look for a category page that shows subcategories, not direct products")

            print("\nWaiting 10 seconds...")
            await asyncio.sleep(10)

        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
