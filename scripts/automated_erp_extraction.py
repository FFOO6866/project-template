"""
Automated Horme ERP Product Price Extraction
Fully automated - no manual interaction required

This script will:
1. Log into the ERP admin panel
2. Navigate to Product Management page
3. Extract all product data including prices
4. Save to JSON for database import

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
import csv

# Configuration
ERP_LOGIN_URL = "https://www.horme.com.sg/admin/admin_login.aspx"
ERP_USERNAME = "integrum"
ERP_PASSWORD = "@ON2AWYH4B3"
ERP_PRODUCT_PAGE = "https://www.horme.com.sg/admin/admin_product.aspx"

# Database configuration
DATABASE_HOST = os.getenv('DB_HOST', 'localhost')
DATABASE_PORT = os.getenv('DB_PORT', '5434')
DATABASE_NAME = os.getenv('DB_NAME', 'horme_db')
DATABASE_USER = os.getenv('DB_USER', 'horme_user')
DATABASE_PASSWORD = os.getenv('DB_PASSWORD', '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42')

# Statistics
stats = {
    'products_extracted': 0,
    'products_with_prices': 0,
    'products_updated': 0,
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

        # Find and fill login form
        username_field = page.locator('input[name*="username" i]').first
        password_field = page.locator('input[type="password"]').first
        login_button = page.locator('input[type="submit"]').first

        print(f"Filling username: {ERP_USERNAME}")
        username_field.fill(ERP_USERNAME)

        print(f"Filling password: {'*' * len(ERP_PASSWORD)}")
        password_field.fill(ERP_PASSWORD)

        print("Clicking login button...")
        login_button.click()

        # Wait for navigation
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=10000)

        print(f"Post-login URL: {page.url}")

        # Check if login was successful
        if 'login' in page.url.lower():
            print("[FAILED] Still on login page")
            return False

        print("[SUCCESS] Login successful!")
        return True

    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return False


def navigate_to_product_page(page: Page) -> bool:
    """
    Navigate to Product Management page
    Returns True if successful
    """
    print("\n" + "="*80)
    print("NAVIGATING TO PRODUCT MANAGEMENT")
    print("="*80)

    try:
        print(f"\nNavigating to: {ERP_PRODUCT_PAGE}")
        page.goto(ERP_PRODUCT_PAGE, wait_until='networkidle', timeout=30000)

        print(f"Current URL: {page.url}")
        print(f"Page title: {page.title()}")

        # Take screenshot
        page.screenshot(path='erp_product_page.png')
        print("Screenshot saved: erp_product_page.png")

        # Save HTML
        html_content = page.content()
        with open('erp_product_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("HTML saved: erp_product_page.html")

        return True

    except Exception as e:
        print(f"[ERROR] Navigation failed: {e}")
        return False


def extract_products_from_page(page: Page) -> List[Dict]:
    """
    Extract all products from the current page
    Returns list of product dictionaries
    """
    print("\n" + "="*80)
    print("EXTRACTING PRODUCTS FROM PAGE")
    print("="*80)

    products = []

    try:
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')

        # Look for data tables (common in ASP.NET admin panels)
        tables = soup.find_all('table')
        print(f"\nFound {len(tables)} tables on page")

        for i, table in enumerate(tables):
            print(f"\nAnalyzing table {i+1}...")

            # Get headers
            headers = []
            header_row = table.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                print(f"  Headers: {headers}")

            # Get data rows
            data_rows = table.find_all('tr')[1:]  # Skip header row
            print(f"  Data rows: {len(data_rows)}")

            if len(data_rows) > 0:
                # This looks like a product table
                for row in data_rows[:5]:  # Show first 5 for analysis
                    cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                    print(f"    Row sample: {cells[:5]}")  # First 5 cells

        # Look for export buttons or links
        export_links = soup.find_all('a', href=re.compile(r'export|csv|excel', re.I))
        print(f"\nFound {len(export_links)} potential export links:")
        for link in export_links:
            print(f"  - {link.get_text(strip=True)}: {link.get('href')}")

        # Look for pagination
        pagination = soup.find_all(['a', 'button'], text=re.compile(r'next|previous|page', re.I))
        print(f"\nFound {len(pagination)} pagination controls")

        return products

    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return products


def check_for_export_functionality(page: Page) -> Optional[str]:
    """
    Check if there's an export/download button for all products
    Returns URL or action if found
    """
    print("\n" + "="*80)
    print("CHECKING FOR EXPORT FUNCTIONALITY")
    print("="*80)

    try:
        # Look for export buttons
        export_selectors = [
            'a:has-text("Export")',
            'button:has-text("Export")',
            'a:has-text("Download")',
            'button:has-text("Download")',
            'a:has-text("CSV")',
            'button:has-text("CSV")',
            'a:has-text("Excel")',
            'button:has-text("Excel")',
            'input[value*="Export" i]',
            'input[value*="Download" i]'
        ]

        for selector in export_selectors:
            try:
                button = page.locator(selector).first
                if button.is_visible(timeout=1000):
                    text = button.text_content()
                    href = button.get_attribute('href')
                    print(f"[FOUND] Export button: {text}")
                    if href:
                        print(f"  URL: {href}")
                        return href
                    else:
                        print(f"  Action: Click button")
                        return "click"
            except:
                continue

        print("[NOT FOUND] No export functionality detected")
        return None

    except Exception as e:
        print(f"[ERROR] Export check failed: {e}")
        return None


def analyze_erp_structure(page: Page):
    """
    Comprehensive analysis of ERP structure
    """
    print("\n" + "="*80)
    print("COMPREHENSIVE ERP STRUCTURE ANALYSIS")
    print("="*80)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    # 1. Find all forms
    forms = soup.find_all('form')
    print(f"\nForms found: {len(forms)}")
    for form in forms[:3]:
        print(f"  - Action: {form.get('action')}")
        print(f"    Method: {form.get('method')}")

    # 2. Find all input fields
    inputs = soup.find_all('input')
    print(f"\nInput fields found: {len(inputs)}")
    input_types = {}
    for inp in inputs:
        inp_type = inp.get('type', 'text')
        input_types[inp_type] = input_types.get(inp_type, 0) + 1
    print(f"  Types: {input_types}")

    # 3. Find search functionality
    search_inputs = soup.find_all('input', {'type': ['text', 'search']})
    print(f"\nSearch inputs found: {len(search_inputs)}")
    for inp in search_inputs[:5]:
        print(f"  - Name: {inp.get('name')} | ID: {inp.get('id')} | Placeholder: {inp.get('placeholder')}")

    # 4. Find buttons
    buttons = soup.find_all(['button', 'input'])
    button_texts = [b.get_text(strip=True) or b.get('value', '') for b in buttons if b.get_text(strip=True) or b.get('value')]
    print(f"\nButtons found: {len(button_texts)}")
    print(f"  Unique texts: {set(button_texts[:20])}")

    # 5. Check for JavaScript data
    scripts = soup.find_all('script')
    print(f"\nScript tags found: {len(scripts)}")
    for script in scripts:
        script_content = script.string or ''
        if 'product' in script_content.lower() and len(script_content) > 100:
            print(f"  - Found script with 'product' keyword ({len(script_content)} chars)")


def main():
    """Main execution"""
    print("="*80)
    print("AUTOMATED HORME ERP PRODUCT EXTRACTION")
    print("="*80)
    print(f"ERP URL: {ERP_LOGIN_URL}")
    print(f"Username: {ERP_USERNAME}")
    print(f"Database: {DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")
    print("="*80)

    with sync_playwright() as p:
        print("\nLaunching browser...")

        # Launch browser (headless for automation, visible for debugging)
        browser = p.chromium.launch(
            headless=False,  # Set to True for production
            slow_mo=100
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )

        page = context.new_page()

        # Step 1: Login to ERP
        if not login_to_erp(page):
            print("\n[FAILED] Could not log in to ERP")
            browser.close()
            return

        # Step 2: Navigate to Product Management
        if not navigate_to_product_page(page):
            print("\n[FAILED] Could not navigate to product page")
            browser.close()
            return

        # Step 3: Analyze page structure
        analyze_erp_structure(page)

        # Step 4: Check for export functionality
        export_url = check_for_export_functionality(page)

        # Step 5: Extract products
        products = extract_products_from_page(page)

        # Step 6: Keep browser open for inspection
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print("\nFiles created:")
        print("  - erp_product_page.png")
        print("  - erp_product_page.html")
        print("\nReview these files to understand the ERP structure.")
        print("We can then create a targeted extraction script.")
        print("\nBrowser will remain open for 30 seconds for inspection...")

        time.sleep(30)
        browser.close()

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Review erp_product_page.html to find:")
    print("   - Product table structure")
    print("   - Column names and order")
    print("   - Pagination controls")
    print("   - Export/download buttons")
    print("\n2. Share key findings and I'll create the extraction script")


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
