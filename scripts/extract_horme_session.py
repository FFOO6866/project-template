"""
Horme.com.sg Session Cookie Extractor
Uses Playwright to extract authenticated session cookies for automated scraping

WORKFLOW:
1. Launch real browser (visible to user)
2. User manually logs in to Horme.com.sg
3. Script extracts and saves session cookies
4. Cookies can be used for automated authenticated scraping

USAGE:
pip install playwright
playwright install chromium
python scripts/extract_horme_session.py

Author: Horme Production Team
Date: 2025-10-22
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

# Configuration
SESSION_FILE = "horme_session.json"
LOGIN_URL = "https://www.horme.com.sg"
TEST_URL = "https://www.horme.com.sg/searchengine.aspx?stq=drill"


def launch_browser_for_login() -> Dict:
    """
    Launch browser and wait for user to log in manually

    Returns:
        dict: Session data including cookies and localStorage
    """
    print("="*80)
    print("HORME.COM.SG SESSION COOKIE EXTRACTOR")
    print("="*80)
    print("\nThis script will:")
    print("1. Open a browser window to Horme.com.sg")
    print("2. Wait for you to log in manually")
    print("3. Extract and save your session cookies")
    print("4. Validate the session works")
    print("\n" + "="*80)

    input("\nPress Enter to launch browser...")

    session_data = {
        'cookies': [],
        'localStorage': {},
        'sessionStorage': {},
        'extracted_at': datetime.now().isoformat(),
        'validated': False
    }

    with sync_playwright() as p:
        print("\nLaunching browser...")

        # Launch browser with visible UI
        browser = p.chromium.launch(
            headless=False,  # Visible browser so user can log in
            slow_mo=100  # Slow down actions for visibility
        )

        # Create context with realistic settings
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = context.new_page()

        # Navigate to homepage
        print(f"\nNavigating to: {LOGIN_URL}")
        page.goto(LOGIN_URL, wait_until='networkidle')

        print("\n" + "="*80)
        print("INSTRUCTIONS:")
        print("="*80)
        print("\n1. A browser window has opened")
        print("2. Please LOG IN to your Horme.com.sg account")
        print("3. After logging in, navigate around to ensure you're authenticated")
        print("4. Return to this terminal and press Enter when done")
        print("\n" + "="*80)

        input("\nPress Enter AFTER you have logged in successfully...")

        # Extract cookies
        print("\nExtracting session cookies...")
        cookies = context.cookies()
        session_data['cookies'] = cookies

        print(f"  Found {len(cookies)} cookies")

        # Extract localStorage
        print("\nExtracting localStorage...")
        try:
            local_storage = page.evaluate("() => Object.assign({}, window.localStorage)")
            session_data['localStorage'] = local_storage
            print(f"  Found {len(local_storage)} localStorage items")
        except Exception as e:
            print(f"  Warning: Could not extract localStorage: {e}")

        # Extract sessionStorage
        print("\nExtracting sessionStorage...")
        try:
            session_storage = page.evaluate("() => Object.assign({}, window.sessionStorage)")
            session_data['sessionStorage'] = session_storage
            print(f"  Found {len(session_storage)} sessionStorage items")
        except Exception as e:
            print(f"  Warning: Could not extract sessionStorage: {e}")

        # Validate session by testing a search page
        print("\n" + "="*80)
        print("VALIDATING SESSION...")
        print("="*80)

        print(f"\nTesting access to: {TEST_URL}")
        page.goto(TEST_URL, wait_until='networkidle')

        # Check if we can see product results (not login page)
        page_content = page.content()

        # Look for signs of successful authentication
        is_authenticated = False

        if "login" in page_content.lower() and "password" in page_content.lower():
            print("\n[FAILED] Session validation failed - appears to be login page")
            session_data['validated'] = False
        elif "member" in page_content.lower() or "account" in page_content.lower():
            print("\n[SUCCESS] Session appears to be authenticated!")
            session_data['validated'] = True
            is_authenticated = True
        else:
            # Ambiguous - let user confirm
            print("\n[UNKNOWN] Cannot automatically determine if authenticated")
            print("\nCurrent page title:", page.title())
            print("\nPlease check the browser window:")
            response = input("Can you see product results? (yes/no): ").lower().strip()

            if response in ['yes', 'y']:
                session_data['validated'] = True
                is_authenticated = True
                print("\n[SUCCESS] User confirmed authentication")
            else:
                session_data['validated'] = False
                print("\n[FAILED] User indicated not authenticated")

        # Keep browser open for user to verify
        if is_authenticated:
            print("\n" + "="*80)
            print("Cookies successfully extracted and validated!")
            print("="*80)
            input("\nPress Enter to close browser and save session...")

        browser.close()

    return session_data


def save_session(session_data: Dict) -> None:
    """Save session data to JSON file"""
    print(f"\nSaving session to: {SESSION_FILE}")

    with open(SESSION_FILE, 'w') as f:
        json.dump(session_data, f, indent=2)

    print(f"  [SAVED] Session data written to {SESSION_FILE}")

    # Print summary
    print("\n" + "="*80)
    print("SESSION SUMMARY")
    print("="*80)
    print(f"\nCookies: {len(session_data['cookies'])}")
    print(f"localStorage: {len(session_data['localStorage'])} items")
    print(f"sessionStorage: {len(session_data['sessionStorage'])} items")
    print(f"Extracted: {session_data['extracted_at']}")
    print(f"Validated: {'YES' if session_data['validated'] else 'NO'}")

    if session_data['validated']:
        print("\n[SUCCESS] Session is ready for automated scraping!")
        print("\nNext steps:")
        print("1. Run: python scripts/scraperapi_ai_enrichment_authenticated.py")
        print("2. Script will automatically use saved session")
        print("3. Monitor for session expiration")
    else:
        print("\n[WARNING] Session validation failed!")
        print("\nTroubleshooting:")
        print("1. Ensure you fully logged in before pressing Enter")
        print("2. Try logging in again")
        print("3. Check if Horme.com.sg has CAPTCHA requirements")
        print("4. Verify your account is active")


def load_and_test_session() -> bool:
    """Load saved session and test if it still works"""
    if not os.path.exists(SESSION_FILE):
        print(f"\n[ERROR] Session file not found: {SESSION_FILE}")
        return False

    print("\n" + "="*80)
    print("TESTING SAVED SESSION")
    print("="*80)

    with open(SESSION_FILE, 'r') as f:
        session_data = json.load(f)

    print(f"\nSession extracted: {session_data['extracted_at']}")
    print(f"Cookies: {len(session_data['cookies'])}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Restore cookies
        context.add_cookies(session_data['cookies'])

        page = context.new_page()

        print(f"\nTesting access to: {TEST_URL}")
        page.goto(TEST_URL, wait_until='networkidle')

        page_content = page.content()

        # Check authentication
        if "login" in page_content.lower() and "password" in page_content.lower():
            print("\n[FAILED] Session has expired - login page detected")
            browser.close()
            return False
        else:
            print("\n[SUCCESS] Session still valid!")
            browser.close()
            return True


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("HORME.COM.SG SESSION EXTRACTOR")
    print("="*80)

    # Check if session already exists
    if os.path.exists(SESSION_FILE):
        print(f"\n[INFO] Found existing session file: {SESSION_FILE}")

        # Test if still valid
        if load_and_test_session():
            print("\n" + "="*80)
            print("Existing session is still valid!")
            print("="*80)

            response = input("\nDo you want to extract a NEW session? (yes/no): ").lower().strip()

            if response not in ['yes', 'y']:
                print("\nUsing existing session. Exiting.")
                return
        else:
            print("\nExisting session has expired. Extracting new session...")

    # Extract new session
    try:
        session_data = launch_browser_for_login()
        save_session(session_data)

        if session_data['validated']:
            print("\n" + "="*80)
            print("SESSION EXTRACTION COMPLETE!")
            print("="*80)
            print("\nYou can now run authenticated scraping with:")
            print("python scripts/scraperapi_ai_enrichment_authenticated.py")
        else:
            print("\n" + "="*80)
            print("SESSION EXTRACTED BUT NOT VALIDATED")
            print("="*80)
            print("\nThe session was saved but could not be validated.")
            print("Try running the authenticated enrichment script anyway.")
            print("If it fails, re-run this script and ensure full login.")

    except Exception as e:
        print(f"\n[ERROR] Session extraction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSession extraction cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
