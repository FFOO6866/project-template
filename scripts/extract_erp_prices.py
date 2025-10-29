"""
Horme ERP Automated Price Extraction
Uses Playwright to log into admin panel and extract product pricing

CREDENTIALS:
- URL: http://www.horme.com.sg/admin/admin_login.aspx
- Username: integrum
- Password: @ON2AWYH4B3

Author: Horme Production Team
Date: 2025-10-22
"""

import os
import sys
import time
import json
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup
import base64

# Configuration
ERP_LOGIN_URL = "https://www.horme.com.sg/admin/admin_login.aspx"
ERP_USERNAME = "integrum"
ERP_PASSWORD = "@ON2AWYH4B3"

# Database configuration
DATABASE_HOST = os.getenv('DB_HOST', 'localhost')
DATABASE_PORT = os.getenv('DB_PORT', '5434')
DATABASE_NAME = os.getenv('DB_NAME', 'horme_db')
DATABASE_USER = os.getenv('DB_USER', 'horme_user')
DATABASE_PASSWORD = os.getenv('DB_PASSWORD', '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42')

BATCH_SIZE = int(os.getenv('BATCH_SIZE', '50'))

# Statistics
stats = {
    'processed': 0,
    'prices_found': 0,
    'not_found': 0,
    'errors': 0
}


def get_db_connection():
    """Get PostgreSQL connection"""
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
        print(f"ERROR: Database connection failed: {e}")
        sys.exit(1)


def login_to_erp(page: Page) -> bool:
    """
    Log into Horme ERP admin panel

    Returns True if login successful
    """
    print("\n" + "="*80)
    print("LOGGING INTO HORME ERP")
    print("="*80)

    try:
        # Navigate to login page
        print(f"\nNavigating to: {ERP_LOGIN_URL}")
        page.goto(ERP_LOGIN_URL, wait_until='networkidle', timeout=30000)

        print(f"Current URL: {page.url}")
        print(f"Page title: {page.title()}")

        # Take screenshot for debugging
        page.screenshot(path='erp_login_page.png')
        print("Screenshot saved: erp_login_page.png")

        # Find login form elements
        # Try common ASP.NET login field IDs
        username_selectors = [
            'input[name*="username" i]',
            'input[name*="user" i]',
            'input[name*="login" i]',
            'input[id*="username" i]',
            'input[id*="user" i]',
            'input[id*="txtUsername"]',
            'input[id*="txtUser"]',
            'input[type="text"]'
        ]

        password_selectors = [
            'input[name*="password" i]',
            'input[name*="pass" i]',
            'input[id*="password" i]',
            'input[id*="pass" i]',
            'input[id*="txtPassword"]',
            'input[id*="txtPass"]',
            'input[type="password"]'
        ]

        button_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Login")',
            'button:has-text("Sign In")',
            'input[value*="Login" i]',
            'input[value*="Sign" i]',
            'a:has-text("Login")'
        ]

        # Find username field
        username_field = None
        for selector in username_selectors:
            try:
                username_field = page.locator(selector).first
                if username_field.is_visible(timeout=1000):
                    print(f"Found username field: {selector}")
                    break
            except:
                continue

        if not username_field:
            print("[ERROR] Could not find username field")
            print("\nAvailable input fields:")
            inputs = page.locator('input').all()
            for inp in inputs[:10]:
                try:
                    print(f"  - {inp.get_attribute('name')} / {inp.get_attribute('id')} / {inp.get_attribute('type')}")
                except:
                    pass
            return False

        # Find password field
        password_field = None
        for selector in password_selectors:
            try:
                password_field = page.locator(selector).first
                if password_field.is_visible(timeout=1000):
                    print(f"Found password field: {selector}")
                    break
            except:
                continue

        if not password_field:
            print("[ERROR] Could not find password field")
            return False

        # Find login button
        login_button = None
        for selector in button_selectors:
            try:
                login_button = page.locator(selector).first
                if login_button.is_visible(timeout=1000):
                    print(f"Found login button: {selector}")
                    break
            except:
                continue

        if not login_button:
            print("[ERROR] Could not find login button")
            return False

        # Fill in credentials
        print(f"\nFilling username: {ERP_USERNAME}")
        username_field.fill(ERP_USERNAME)

        print(f"Filling password: {'*' * len(ERP_PASSWORD)}")
        password_field.fill(ERP_PASSWORD)

        # Take screenshot before clicking
        page.screenshot(path='erp_before_login.png')
        print("Screenshot saved: erp_before_login.png")

        # Click login button
        print("Clicking login button...")
        login_button.click()

        # Wait for navigation
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=10000)

        # Take screenshot after login
        page.screenshot(path='erp_after_login.png')
        print("Screenshot saved: erp_after_login.png")

        print(f"\nPost-login URL: {page.url}")
        print(f"Post-login title: {page.title()}")

        # Check if login was successful
        # Look for signs of successful login (not on login page, no error messages)
        if 'login' in page.url.lower():
            # Check for error messages
            error_selectors = [
                '.error',
                '.alert-danger',
                '[class*="error"]',
                '[id*="error"]',
                'span[style*="red"]'
            ]

            for selector in error_selectors:
                try:
                    error_msg = page.locator(selector).first
                    if error_msg.is_visible(timeout=1000):
                        error_text = error_msg.text_content()
                        print(f"[LOGIN ERROR] {error_text}")
                        return False
                except:
                    continue

            print("[WARNING] Still on login page after submit")
            print("This might indicate login failure or additional steps required")
            return False

        print("\n[SUCCESS] Login appears successful!")
        print(f"Redirected to: {page.url}")
        return True

    except Exception as e:
        print(f"\n[ERROR] Login failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def explore_erp_for_products(page: Page) -> Dict[str, Any]:
    """
    Explore ERP interface to find product management area

    Returns information about product pages found
    """
    print("\n" + "="*80)
    print("EXPLORING ERP FOR PRODUCT DATA")
    print("="*80)

    exploration_results = {
        'product_pages': [],
        'menu_items': [],
        'current_url': page.url
    }

    try:
        # Look for common admin menu items related to products
        product_keywords = [
            'product',
            'inventory',
            'catalog',
            'item',
            'sku',
            'price',
            'pricing',
            'stock'
        ]

        print("\nSearching for navigation menu...")

        # Get all links
        links = page.locator('a').all()
        print(f"Found {len(links)} total links")

        for link in links[:50]:  # Check first 50 links
            try:
                text = link.text_content().lower()
                href = link.get_attribute('href')

                # Check if link text contains product keywords
                for keyword in product_keywords:
                    if keyword in text:
                        exploration_results['menu_items'].append({
                            'text': link.text_content(),
                            'href': href,
                            'keyword': keyword
                        })
                        print(f"  Found: {link.text_content()} -> {href}")
                        break

            except:
                continue

        # Save page HTML for manual inspection
        html_content = page.content()
        with open('erp_home_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\nERP home page saved to: erp_home_page.html")
        print(f"Found {len(exploration_results['menu_items'])} product-related menu items")

        return exploration_results

    except Exception as e:
        print(f"\n[ERROR] Exploration failed: {e}")
        import traceback
        traceback.print_exc()
        return exploration_results


def search_product_in_erp(page: Page, product_name: str, sku: str) -> Optional[Dict]:
    """
    Search for a specific product in the ERP

    Returns product data if found
    """
    try:
        # Look for search box
        search_selectors = [
            'input[name*="search" i]',
            'input[id*="search" i]',
            'input[placeholder*="search" i]',
            'input[type="search"]',
            'input[type="text"]'
        ]

        search_box = None
        for selector in search_selectors:
            try:
                search_box = page.locator(selector).first
                if search_box.is_visible(timeout=1000):
                    break
            except:
                continue

        if not search_box:
            return None

        # Search by SKU first (more specific)
        search_box.fill(sku)
        search_box.press('Enter')

        time.sleep(2)
        page.wait_for_load_state('networkidle', timeout=5000)

        # Extract product data from results
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')

        # Look for price in the page
        price_patterns = [
            r'SGD\s*(\d+\.?\d*)',
            r'\$\s*(\d+\.?\d*)',
            r'Price[:\s]*(\d+\.?\d*)',
            r'(\d+\.?\d+)\s*SGD'
        ]

        for pattern in price_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                try:
                    price = float(matches[0])
                    return {
                        'sku': sku,
                        'price': price,
                        'currency': 'SGD',
                        'found': True
                    }
                except:
                    continue

        return None

    except Exception as e:
        print(f"  Search error: {e}")
        return None


def extract_all_products_from_erp(page: Page) -> List[Dict]:
    """
    Extract all products from ERP product listing page

    Returns list of products with prices
    """
    print("\n" + "="*80)
    print("EXTRACTING ALL PRODUCTS FROM ERP")
    print("="*80)

    products = []

    try:
        # This function would navigate to the product listing
        # and extract all products at once
        # Implementation depends on ERP structure

        # For now, save the current page for manual inspection
        html_content = page.content()
        with open('erp_current_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

        print("Current page saved to: erp_current_page.html")
        print("Please inspect this file to understand ERP structure")

        return products

    except Exception as e:
        print(f"\n[ERROR] Extraction failed: {e}")
        return products


def main():
    """Main execution"""
    print("="*80)
    print("HORME ERP AUTOMATED PRICE EXTRACTION")
    print("="*80)
    print(f"ERP URL: {ERP_LOGIN_URL}")
    print(f"Username: {ERP_USERNAME}")
    print(f"Database: {DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")
    print("="*80)

    with sync_playwright() as p:
        print("\nLaunching browser...")

        # Launch browser (visible for first run to debug)
        browser = p.chromium.launch(
            headless=False,  # Visible to see what's happening
            slow_mo=500  # Slow down for visibility
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )

        page = context.new_page()

        # Step 1: Login to ERP
        login_success = login_to_erp(page)

        if not login_success:
            print("\n" + "="*80)
            print("[FAILED] Could not log in to ERP")
            print("="*80)
            print("\nPlease check:")
            print("1. Screenshots: erp_login_page.png, erp_before_login.png, erp_after_login.png")
            print("2. Verify credentials are correct")
            print("3. Check if ERP requires additional authentication (2FA, CAPTCHA)")
            browser.close()
            return

        # Step 2: Explore ERP interface
        exploration = explore_erp_for_products(page)

        print("\n" + "="*80)
        print("EXPLORATION RESULTS")
        print("="*80)
        print(f"\nFound {len(exploration['menu_items'])} product-related menu items:")
        for item in exploration['menu_items']:
            print(f"  - {item['text']}: {item['href']}")

        # Step 3: Manual inspection point
        print("\n" + "="*80)
        print("MANUAL INSPECTION REQUIRED")
        print("="*80)
        print("\nThe browser window is still open.")
        print("Please navigate to the product listing page manually.")
        print("\nOnce you're on the product listing page:")
        print("1. Press Enter in this terminal")
        print("2. The script will analyze the page structure")
        print("3. We can then automate the extraction")

        input("\nPress Enter when you're on the product listing page...")

        # Save current page after manual navigation
        page.screenshot(path='erp_product_listing.png')
        print("\nScreenshot saved: erp_product_listing.png")

        html_content = page.content()
        with open('erp_product_listing.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("HTML saved: erp_product_listing.html")

        print(f"\nCurrent URL: {page.url}")
        print(f"Current title: {page.title()}")

        # Keep browser open for inspection
        print("\n" + "="*80)
        print("Browser will remain open for inspection")
        print("Press Enter to close...")
        input()

        browser.close()

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Review the saved files:")
    print("   - erp_login_page.png")
    print("   - erp_after_login.png")
    print("   - erp_product_listing.png")
    print("   - erp_product_listing.html")
    print("\n2. Share the structure of the product listing page")
    print("3. I'll create an automated extraction script")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
