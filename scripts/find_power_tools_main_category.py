"""
Find the main Electrical Power Tools category by exploring the website navigation
"""
import asyncio
import json
from playwright.async_api import async_playwright

WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"


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
            print("EXPLORING WEBSITE NAVIGATION")
            print("="*80)

            await page.goto(f"{WEBSITE_URL}/login.aspx", wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            await page.fill('#ctl00_pgContent_email', LOGIN_EMAIL)
            await page.fill('#ctl00_pgContent_pwd', LOGIN_PASSWORD)
            await page.click('#btnLogin')
            await asyncio.sleep(4)

            print("[OK] Logged in\n")

            # Go to homepage
            await page.goto(WEBSITE_URL, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # Look for main navigation menu
            print("Looking for main navigation menu...")

            # Try to find menu button and click it
            try:
                menu_button = page.locator('button:has-text("Menu"), .menu-button, [class*="menu"]').first
                await menu_button.click()
                await asyncio.sleep(2)
                print("[OK] Opened menu")
            except:
                print("[INFO] Menu might already be open or doesn't need clicking")

            # Extract all navigation links
            all_links = await page.locator('nav a, .navigation a, .menu a, a[href*="category"]').all()

            print(f"\nFound {len(all_links)} navigation links")

            # Look for power tools related links
            power_tools_links = []
            for link in all_links:
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute('href')

                    if text and href:
                        text = text.strip().lower()
                        # Look for power tools keywords
                        if any(kw in text for kw in ['power', 'tool', 'drill', 'grind', 'saw', 'electric']):
                            power_tools_links.append({
                                'text': text,
                                'href': href
                            })
                except:
                    pass

            print("\n" + "="*80)
            print("POWER TOOLS RELATED LINKS FOUND:")
            print("="*80)

            for i, link in enumerate(power_tools_links, 1):
                print(f"\n{i}. {link['text']}")
                print(f"   URL: {link['href']}")

            # Save screenshot of homepage/menu
            await page.screenshot(path='navigation_menu.png', full_page=True)
            print("\n[OK] Screenshot saved: navigation_menu.png")

            # Save results to JSON
            output = {
                'power_tools_links': power_tools_links,
                'total_links_found': len(all_links)
            }

            with open('power_tools_navigation.json', 'w') as f:
                json.dump(output, f, indent=2)

            print("[OK] Results saved to: power_tools_navigation.json")

            print("\n" + "="*80)
            print("MANUAL INSPECTION")
            print("="*80)
            print("\nThe browser will stay open for 30 seconds.")
            print("Please manually:")
            print("1. Look at the navigation menu")
            print("2. Find 'Electrical Power Tools' or similar")
            print("3. Note the URL when you click on it")
            print("="*80)

            await asyncio.sleep(30)

        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
