"""
Diagnostic script for login.aspx page
"""
import asyncio
from playwright.async_api import async_playwright

WEBSITE_URL = "https://www.horme.com.sg"
LOGIN_URL = f"{WEBSITE_URL}/login.aspx"

async def diagnose_login_aspx():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            print(f"Navigating to {LOGIN_URL}...")
            await page.goto(LOGIN_URL, wait_until='networkidle', timeout=30000)

            # Wait for any dynamic content to load
            print("Waiting 5 seconds for dynamic content...")
            await asyncio.sleep(5)

            # Save screenshot
            await page.screenshot(path='login_aspx_page.png')
            print("  Saved login_aspx_page.png")

            # Get page content
            content = await page.content()

            # Save full HTML
            with open('login_aspx_page.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("  Saved login_aspx_page.html")

            # Check for forms
            print("\n" + "="*80)
            print("FORM ELEMENTS FOUND:")
            print("="*80)

            forms = await page.locator('form').all()
            print(f"\nForms found: {len(forms)}")
            if len(forms) > 0:
                for i, form in enumerate(forms):
                    form_id = await form.get_attribute('id')
                    form_name = await form.get_attribute('name')
                    form_action = await form.get_attribute('action')
                    print(f"\nForm {i+1}:")
                    print(f"  ID: {form_id}")
                    print(f"  Name: {form_name}")
                    print(f"  Action: {form_action}")

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
                inp_value = await inp.get_attribute('value')

                # Only show text, email, password fields (not hidden fields)
                if inp_type in ['text', 'email', 'password', 'submit', None]:
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

            buttons = await page.locator('button, input[type="submit"]').all()
            print(f"\nTotal buttons: {len(buttons)}")
            for i, btn in enumerate(buttons):
                btn_type = await btn.get_attribute('type')
                btn_name = await btn.get_attribute('name')
                btn_id = await btn.get_attribute('id')
                try:
                    btn_text = await btn.inner_text()
                except:
                    btn_text = await btn.get_attribute('value')

                print(f"\nButton {i+1}:")
                print(f"  Type: {btn_type}")
                print(f"  Name: {btn_name}")
                print(f"  ID: {btn_id}")
                print(f"  Text/Value: {btn_text}")

            print("\n" + "="*80)
            print(f"Current URL: {page.url}")
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
    asyncio.run(diagnose_login_aspx())
