"""
Diagnostic script to check page structure after login
"""
import asyncio
from playwright.async_api import async_playwright

WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_URL = f"{WEBSITE_URL}/login.aspx"
LOGIN_EMAIL = "fuji.foo@outlook.com"
LOGIN_PASSWORD = "integrum2@25"

async def diagnose_after_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            # Login
            print(f"Logging in to {LOGIN_URL}...")
            await page.goto(LOGIN_URL, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)

            await page.fill('#ctl00_pgContent_email', LOGIN_EMAIL)
            await page.fill('#ctl00_pgContent_pwd', LOGIN_PASSWORD)
            await page.click('#btnLogin')
            await asyncio.sleep(5)

            print(f"Current URL after login: {page.url}")

            # Save screenshot
            await page.screenshot(path='after_login.png')
            print("  Saved after_login.png")

            # Check for search boxes
            print("\n" + "="*80)
            print("SEARCH BOXES:")
            print("="*80)

            search_selectors = [
                '#search',
                'input[name="q"]',
                'input[type="search"]',
                'input[placeholder*="Search"]',
                'input[placeholder*="search"]',
                '.autocompleteKeyword',
                '.autocompleteKeyword2'
            ]

            for selector in search_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        print(f"\nFound {count} element(s) with selector: {selector}")
                        for i in range(min(count, 3)):  # Show first 3
                            element = page.locator(selector).nth(i)
                            visible = await element.is_visible()
                            name = await element.get_attribute('name')
                            id_attr = await element.get_attribute('id')
                            placeholder = await element.get_attribute('placeholder')
                            print(f"  Element {i+1}:")
                            print(f"    Visible: {visible}")
                            print(f"    Name: {name}")
                            print(f"    ID: {id_attr}")
                            print(f"    Placeholder: {placeholder}")
                except Exception as e:
                    pass

            print("\n" + "="*80)
            print("ALL INPUT FIELDS:")
            print("="*80)

            inputs = await page.locator('input').all()
            search_inputs = []
            for i, inp in enumerate(inputs):
                try:
                    inp_type = await inp.get_attribute('type')
                    inp_name = await inp.get_attribute('name')
                    inp_id = await inp.get_attribute('id')
                    inp_placeholder = await inp.get_attribute('placeholder')
                    visible = await inp.is_visible()

                    # Check if it might be a search box
                    if (inp_placeholder and 'search' in inp_placeholder.lower()) or \
                       (inp_type and inp_type == 'search') or \
                       (inp_name and 'search' in inp_name.lower()):
                        search_inputs.append({
                            'index': i,
                            'type': inp_type,
                            'name': inp_name,
                            'id': inp_id,
                            'placeholder': inp_placeholder,
                            'visible': visible
                        })
                except:
                    pass

            print(f"\nFound {len(search_inputs)} potential search inputs:")
            for inp_info in search_inputs:
                print(f"\nInput {inp_info['index']}:")
                print(f"  Type: {inp_info['type']}")
                print(f"  Name: {inp_info['name']}")
                print(f"  ID: {inp_info['id']}")
                print(f"  Placeholder: {inp_info['placeholder']}")
                print(f"  Visible: {inp_info['visible']}")

            print("\nWaiting 30 seconds so you can inspect the browser window...")
            await asyncio.sleep(30)

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(diagnose_after_login())
