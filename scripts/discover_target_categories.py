"""
Discover Category URLs for the 3 Target Categories
Specifically finds URLs for:
- Safety Products (21)
- Electrical Power Tools (09)
- Cleaning Products (05)
"""
import asyncio
import json
from playwright.async_api import async_playwright
import re

WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

# Target categories we need to find
TARGET_CATEGORIES = {
    'safety': {
        'code': '21',
        'name': 'Safety Products',
        'keywords': ['safety', 'ppe', 'protection', 'protective equipment'],
        'expected_count': 9129
    },
    'power_tools': {
        'code': '09',
        'name': 'Electrical Power Tools',
        'keywords': ['power tool', 'electric tool', 'drill', 'grinder', 'saw'],
        'expected_count': 4927
    },
    'cleaning': {
        'code': '05',
        'name': 'Cleaning Products',
        'keywords': ['cleaning', 'cleaner', 'vacuum', 'mop', 'detergent'],
        'expected_count': 3210
    }
}


async def find_category_urls():
    """
    Systematically discover category URLs by:
    1. Login to website
    2. Find main navigation menu
    3. Identify category links
    4. Map to our target categories
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        discovered_categories = {}

        try:
            # === STEP 1: Login ===
            print("="*80)
            print("STEP 1: LOGIN TO HORME.COM.SG")
            print("="*80)

            await page.goto(f"{WEBSITE_URL}/login.aspx", wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            await page.fill('#ctl00_pgContent_email', LOGIN_EMAIL)
            await page.fill('#ctl00_pgContent_pwd', LOGIN_PASSWORD)
            await page.click('#btnLogin')
            await asyncio.sleep(4)

            print(f"[OK] Logged in successfully")
            print(f"Current URL: {page.url}")

            # === STEP 2: Find Main Navigation ===
            print("\n" + "="*80)
            print("STEP 2: DISCOVER CATEGORY STRUCTURE")
            print("="*80)

            # Get all links on page
            all_links = await page.locator('a').all()

            category_links = []
            for link in all_links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()

                    if href and text:
                        text = text.strip()
                        # Look for category.aspx or products.aspx links
                        if 'category.aspx' in href or 'products.aspx' in href:
                            category_links.append({
                                'text': text,
                                'href': href,
                                'url': href if href.startswith('http') else f"{WEBSITE_URL}/{href}"
                            })
                except:
                    pass

            print(f"\nFound {len(category_links)} category/product links")

            # === STEP 3: Match to Target Categories ===
            print("\n" + "="*80)
            print("STEP 3: MATCHING TO TARGET CATEGORIES")
            print("="*80)

            for cat_key, cat_info in TARGET_CATEGORIES.items():
                print(f"\n[SEARCH] Looking for: {cat_info['name']} (Code: {cat_info['code']})")
                print(f"         Keywords: {', '.join(cat_info['keywords'])}")

                matches = []
                for link in category_links:
                    text_lower = link['text'].lower()

                    # Check if link text matches any keywords
                    for keyword in cat_info['keywords']:
                        if keyword.lower() in text_lower:
                            matches.append(link)
                            break

                if matches:
                    print(f"\n   Found {len(matches)} potential matches:")
                    for i, match in enumerate(matches[:5], 1):  # Show top 5
                        print(f"   {i}. {match['text']}")
                        print(f"      URL: {match['href']}")

                    # Use first match as primary
                    discovered_categories[cat_key] = {
                        'name': cat_info['name'],
                        'code': cat_info['code'],
                        'url': matches[0]['href'],
                        'full_url': matches[0]['url'],
                        'link_text': matches[0]['text'],
                        'all_matches': matches
                    }
                else:
                    print(f"   [WARN] No matches found")

            # === STEP 4: Verify by Visiting Categories ===
            print("\n" + "="*80)
            print("STEP 4: VERIFY CATEGORIES BY VISITING")
            print("="*80)

            for cat_key, cat_data in discovered_categories.items():
                print(f"\n[VISIT] Category: {cat_data['name']}")
                print(f"        URL: {cat_data['full_url']}")

                try:
                    await page.goto(cat_data['full_url'], wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(2)

                    # Try to count products
                    product_elements = await page.locator('.product, .product-item, [class*="product"]').count()

                    # Look for product count in page
                    page_text = await page.content()

                    # Extract category ID from URL
                    cat_id_match = re.search(r'[?&]c=(\d+)', cat_data['url'])
                    cat_id = cat_id_match.group(1) if cat_id_match else 'unknown'

                    print(f"        [OK] Category ID: {cat_id}")
                    print(f"        Products visible on page: {product_elements}")

                    # Save screenshot
                    screenshot_path = f"category_{cat_key}_{cat_id}.png"
                    await page.screenshot(path=screenshot_path)
                    print(f"        Screenshot saved: {screenshot_path}")

                    # Update with verification data
                    cat_data['category_id'] = cat_id
                    cat_data['products_on_page'] = product_elements
                    cat_data['verified'] = True

                except Exception as e:
                    print(f"        [ERROR] Error visiting category: {e}")
                    cat_data['verified'] = False

            # === STEP 5: Generate Final Mapping ===
            print("\n" + "="*80)
            print("STEP 5: FINAL CATEGORY MAPPING")
            print("="*80)

            final_mapping = {}
            for cat_key, cat_data in discovered_categories.items():
                if cat_data.get('verified'):
                    final_mapping[cat_key] = {
                        'name': cat_data['name'],
                        'code': cat_data['code'],
                        'category_id': cat_data['category_id'],
                        'url': cat_data['url'],
                        'expected_products': TARGET_CATEGORIES[cat_key]['expected_count'],
                        'products_on_first_page': cat_data['products_on_page']
                    }

            # Save to JSON
            output_file = 'discovered_categories.json'
            with open(output_file, 'w') as f:
                json.dump(final_mapping, f, indent=2)

            print(f"\n[OK] Category mapping saved to: {output_file}")
            print("\nFINAL MAPPING:")
            print(json.dumps(final_mapping, indent=2))

            # === STEP 6: Generate Scraper Config ===
            print("\n" + "="*80)
            print("STEP 6: SCRAPER CONFIGURATION")
            print("="*80)

            scraper_config = []
            for cat_key, cat_data in final_mapping.items():
                scraper_config.append({
                    'name': cat_data['name'],
                    'url': cat_data['url'],
                    'type': 'main',
                    'code': cat_data['code'],
                    'expected_products': cat_data['expected_products']
                })

            print("\nCopy this into your scraper:")
            print("="*80)
            print("CATEGORIES = [")
            for config in scraper_config:
                print(f"    {config},")
            print("]")

            print("\n\n[SUCCESS] DISCOVERY COMPLETE!")
            print("\nYou can now use these category URLs in the comprehensive scraper.")

            # Wait so user can see results
            print("\nWaiting 10 seconds before closing...")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

        return discovered_categories


async def main():
    print("="*80)
    print("HORME CATEGORY DISCOVERY TOOL")
    print("="*80)
    print("\nTarget Categories:")
    for cat_key, cat_info in TARGET_CATEGORIES.items():
        print(f"  - {cat_info['name']} ({cat_info['code']}) - {cat_info['expected_count']} products")
    print("\n" + "="*80)
    print()

    categories = await find_category_urls()

    return categories


if __name__ == '__main__':
    asyncio.run(main())
