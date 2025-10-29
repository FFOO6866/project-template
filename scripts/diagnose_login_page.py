"""
Diagnostic script to investigate horme.com.sg login page structure
"""
import asyncio
from playwright.async_api import async_playwright

WEBSITE_URL = "https://www.horme.com.sg"

async def diagnose_login_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            print("Navigating to homepage...")
            await page.goto(WEBSITE_URL, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # Save homepage screenshot
            await page.screenshot(path='homepage.png')
            print("  Saved homepage.png")

            # Try to find and click login link
            print("\nLooking for login link...")
            login_selectors = [
                'a:has-text("Account")',
                'a:has-text("Login")',
                'a:has-text("Sign In")',
                '[href*="login"]',
                '[href*="account"]'
            ]

            login_clicked = False
            for selector in login_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        print(f"  Found login link: {selector}")
                        await element.click(timeout=5000)
                        login_clicked = True
                        break
                except Exception as e:
                    print(f"  Failed {selector}: {e}")
                    continue

            if not login_clicked:
                print("\n  No login link found, trying direct URL...")
                await page.goto(f"{WEBSITE_URL}/customer/account/login/", wait_until='networkidle')

            await asyncio.sleep(3)

            # Save login page screenshot
            await page.screenshot(path='login_page.png')
            print("\n  Saved login_page.png")

            # Get page content
            content = await page.content()

            # Save full HTML
            with open('login_page.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("  Saved login_page.html")

            # Check for various form elements
            print("\n" + "="*80)
            print("FORM ELEMENTS FOUND:")
            print("="*80)

            # Check for forms
            forms = await page.locator('form').all()
            print(f"\nForms found: {len(forms)}")
            for i, form in enumerate(forms):
                form_html = await form.inner_html()
                print(f"\nForm {i+1}:")
                print(form_html[:500] + "..." if len(form_html) > 500 else form_html)

            # Check for input fields
            print("\n" + "="*80)
            print("INPUT FIELDS:")
            print("="*80)

            inputs = await page.locator('input').all()
            print(f"\nTotal input fields: {len(inputs)}")
            for i, inp in enumerate(inputs):
                inp_type = await inp.get_attribute('type')
                inp_name = await inp.get_attribute('name')
                inp_id = await inp.get_attribute('id')
                inp_class = await inp.get_attribute('class')
                inp_placeholder = await inp.get_attribute('placeholder')

                print(f"\nInput {i+1}:")
                print(f"  Type: {inp_type}")
                print(f"  Name: {inp_name}")
                print(f"  ID: {inp_id}")
                print(f"  Class: {inp_class}")
                print(f"  Placeholder: {inp_placeholder}")

            # Check for buttons
            print("\n" + "="*80)
            print("BUTTONS:")
            print("="*80)

            buttons = await page.locator('button').all()
            print(f"\nTotal buttons: {len(buttons)}")
            for i, btn in enumerate(buttons):
                btn_type = await btn.get_attribute('type')
                btn_text = await btn.inner_text()
                btn_class = await btn.get_attribute('class')

                print(f"\nButton {i+1}:")
                print(f"  Type: {btn_type}")
                print(f"  Text: {btn_text}")
                print(f"  Class: {btn_class}")

            print("\n" + "="*80)
            print("Current URL: " + page.url)
            print("="*80)

            print("\nWaiting 30 seconds so you can inspect the browser window...")
            await asyncio.sleep(30)

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(diagnose_login_page())
