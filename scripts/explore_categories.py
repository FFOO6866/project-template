"""
Explore category structure on horme.com.sg
Find all category links and their product counts
"""
import asyncio
from playwright.async_api import async_playwright

WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

async def explore_categories():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            # Login
            print("Logging in...")
            await page.goto(f"{WEBSITE_URL}/login.aspx", wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            await page.fill('#ctl00_pgContent_email', LOGIN_EMAIL)
            await page.fill('#ctl00_pgContent_pwd', LOGIN_PASSWORD)
            await page.click('#btnLogin')
            await asyncio.sleep(4)

            print(f"Current URL: {page.url}")

            # Save homepage screenshot
            await page.screenshot(path='homepage_after_login.png')
            print("Saved homepage_after_login.png")

            # Look for category/navigation links
            print("\n" + "="*80)
            print("LOOKING FOR CATEGORY LINKS")
            print("="*80)

            # Common category selectors
            category_selectors = [
                'nav a',
                '.menu a',
                '.nav-item a',
                '.category a',
                '[class*="category"] a',
                '[class*="menu"] a',
                'a[href*="category"]',
                'a[href*="shop"]',
                'a[href*="products"]'
            ]

            all_links = []
            for selector in category_selectors:
                try:
                    links = await page.locator(selector).all()
                    for link in links:
                        try:
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            if href and text:
                                text = text.strip()
                                if text and len(text) < 100:  # Reasonable link text
                                    all_links.append({
                                        'text': text,
                                        'href': href,
                                        'selector': selector
                                    })
                        except:
                            pass
                except:
                    pass

            # Remove duplicates
            unique_links = {}
            for link in all_links:
                key = f"{link['text']}|{link['href']}"
                if key not in unique_links:
                    unique_links[key] = link

            print(f"\nFound {len(unique_links)} unique links")

            # Filter for likely category links
            category_keywords = ['category', 'shop', 'products', 'tools', 'hardware',
                               'safety', 'equipment', 'supplies', 'materials']

            likely_categories = []
            for link in unique_links.values():
                href_lower = link['href'].lower()
                text_lower = link['text'].lower()

                # Check if it's a category link
                if any(keyword in href_lower or keyword in text_lower for keyword in category_keywords):
                    likely_categories.append(link)

            print(f"\n{len(likely_categories)} likely category links:")
            for i, cat in enumerate(likely_categories[:30], 1):  # Show first 30
                print(f"\n{i}. {cat['text']}")
                print(f"   URL: {cat['href']}")

            # Save page HTML for further analysis
            content = await page.content()
            with open('homepage_structure.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("\n\nSaved homepage_structure.html")

            print("\nWaiting 30 seconds so you can inspect the browser...")
            await asyncio.sleep(30)

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(explore_categories())
