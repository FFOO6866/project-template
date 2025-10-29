"""
Authenticated ScraperAPI + AI Product Enrichment System
Uses saved session cookies for authenticated access to Horme.com.sg

This combines:
- Session cookies from manual login (extract_horme_session.py)
- Playwright for authenticated browsing (primary method)
- ScraperAPI as fallback (with cookie support)
- OpenAI GPT-4 for intelligent product matching
- Database automatic price updates

PREREQUISITES:
1. Run extract_horme_session.py to get horme_session.json
2. Ensure session is still valid
3. Set OPENAI_API_KEY environment variable

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
from bs4 import BeautifulSoup
from openai import OpenAI
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

# Configuration
SCRAPERAPI_KEY = os.getenv('SCRAPERAPI_KEY', '3c29b7d4798bd49564aacf76ba828d8a')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SESSION_FILE = "horme_session.json"

if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY environment variable required")
    sys.exit(1)

if not os.path.exists(SESSION_FILE):
    print(f"ERROR: Session file not found: {SESSION_FILE}")
    print("\nPlease run first: python scripts/extract_horme_session.py")
    sys.exit(1)

# Database configuration
DATABASE_HOST = os.getenv('DB_HOST', 'localhost')
DATABASE_PORT = os.getenv('DB_PORT', '5434')
DATABASE_NAME = os.getenv('DB_NAME', 'horme_db')
DATABASE_USER = os.getenv('DB_USER', 'horme_user')
DATABASE_PASSWORD = os.getenv('DB_PASSWORD', '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42')

# Processing configuration
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.7'))
USE_PLAYWRIGHT = True  # Primary method
USE_SCRAPERAPI = False  # Fallback only

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
TEXT_MODEL = "gpt-4-turbo-preview"

# Load session
with open(SESSION_FILE, 'r') as f:
    SESSION_DATA = json.load(f)

# Statistics
stats = {
    'processed': 0,
    'matched': 0,
    'not_found': 0,
    'errors': 0,
    'prices_extracted': 0,
    'playwright_calls': 0,
    'scraperapi_calls': 0,
    'openai_calls': 0,
    'session_valid': True
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


class AuthenticatedBrowser:
    """Manages authenticated Playwright browser session"""

    def __init__(self, session_data: Dict):
        self.session_data = session_data
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        """Start browser session"""
        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=True,  # Run in background
            args=['--disable-blink-features=AutomationControlled']
        )

        # Create context with realistic settings
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        # Restore cookies
        self.context.add_cookies(self.session_data['cookies'])

        self.page = self.context.new_page()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close browser session"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch page with authenticated session"""
        try:
            self.page.goto(url, wait_until='networkidle', timeout=30000)
            stats['playwright_calls'] += 1

            # Check if redirected to login page
            current_url = self.page.url
            if 'login' in current_url.lower():
                print(f"  [SESSION EXPIRED] Redirected to login page")
                stats['session_valid'] = False
                return None

            return self.page.content()

        except Exception as e:
            print(f"  Playwright error: {e}")
            return None


def create_search_query(description: str, sku: str, brand: str = None) -> str:
    """Create optimized search query from product description"""
    clean_desc = description.upper()
    clean_desc = re.sub(r'\b(ITEM|PRODUCT|PACK|SET|OF|THE|A|AN)\b', '', clean_desc)

    words = clean_desc.split()
    key_words = [w for w in words if len(w) > 2][:4]

    search_query = ' '.join(key_words)

    if brand and brand != 'Unknown':
        search_query = f"{brand} {search_query}"

    return search_query.strip()


def search_horme_products_authenticated(browser: AuthenticatedBrowser, search_query: str) -> List[Dict[str, Any]]:
    """
    Search Horme.com.sg using authenticated browser session

    Returns list of product results with title, price, url
    """
    search_url = f"https://www.horme.com.sg/searchengine.aspx?stq={search_query.replace(' ', '+')}"

    print(f"  Searching: {search_url}")

    # Fetch via authenticated Playwright
    html_content = browser.fetch_page(search_url)

    if not html_content:
        return []

    # Check for authentication failure indicators
    if "login" in html_content.lower() and "password" in html_content.lower():
        print(f"  [AUTH FAILED] Login page detected - session expired")
        stats['session_valid'] = False
        return []

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract search results
    results = []

    # Common e-commerce product selectors
    product_selectors = [
        '.product-item',
        '.search-result-item',
        '[class*="product"]',
        '.item',
        'article',
        'div[data-product]',
        'li.product'
    ]

    for selector in product_selectors:
        items = soup.select(selector)
        if items and len(items) > 0:
            print(f"  Found {len(items)} results using selector: {selector}")

            for item in items[:10]:  # Limit to top 10 results
                # Extract title
                title = None
                title_selectors = ['h3', 'h4', '.product-title', '.product-name', 'a']
                for ts in title_selectors:
                    elem = item.select_one(ts)
                    if elem:
                        title = elem.get_text(strip=True)
                        if title and len(title) > 10:
                            break

                # Extract price
                price_text = None
                price_selectors = ['.price', '.product-price', '[class*="price"]', 'span.price', 'div.price']
                for ps in price_selectors:
                    elem = item.select_one(ps)
                    if elem:
                        price_text = elem.get_text(strip=True)
                        break

                # Extract URL
                url = None
                link = item.select_one('a')
                if link and link.get('href'):
                    url = link['href']
                    if not url.startswith('http'):
                        url = 'https://www.horme.com.sg' + url

                if title:  # Only add if we found a title
                    results.append({
                        'title': title,
                        'price_text': price_text,
                        'url': url
                    })

            break  # Stop after first successful selector

    print(f"  Extracted {len(results)} product results")

    # Check if results look authentic (not login/member-only messages)
    if results:
        # Check first result for auth indicators
        first_title = results[0]['title'].lower()
        if 'member only' in first_title or 'login' in first_title or 'sign in' in first_title:
            print(f"  [AUTH ISSUE] Results appear to be login/member messages")
            return []

    return results


def ai_match_product(
    target_description: str,
    target_sku: str,
    target_category: str,
    target_brand: str,
    search_results: List[Dict]
) -> Optional[Dict[str, Any]]:
    """
    Use GPT-4 to match the correct product from search results

    Returns match info with confidence score, index, reasoning
    """
    if not search_results:
        return None

    # Format search results for AI
    results_text = "\n".join([
        f"{i}. {r['title']} - {r.get('price_text', 'Price not shown')}"
        for i, r in enumerate(search_results)
    ])

    prompt = f"""You are an expert product matcher for an industrial hardware supplier.

TARGET PRODUCT:
- SKU: {target_sku}
- Description: {target_description}
- Category: {target_category}
- Brand: {target_brand}

SEARCH RESULTS:
{results_text}

Task: Determine which search result (if any) matches the target product.

Respond in JSON format:
{{
    "matched": true/false,
    "match_index": <index 0-{len(search_results)-1}, or null if no match>,
    "confidence": <0.0 to 1.0>,
    "reasoning": "<brief explanation>"
}}

Rules:
- Only return matched=true if confidence >= {CONFIDENCE_THRESHOLD}
- Match based on product type, brand, and key specifications
- Ignore minor differences in wording
- Be strict - better to say no match than wrong match
- If results say "member only" or "login required", return matched=false
"""

    try:
        response = openai_client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert product matcher. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500
        )

        stats['openai_calls'] += 1

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        print(f"  AI matching error: {e}")
        return None


def parse_price(price_text: str) -> Optional[float]:
    """Parse price from text like 'SGD 189.00' or '$189.00'"""
    if not price_text:
        return None

    # Remove currency symbols and commas
    cleaned = price_text.replace('SGD', '').replace('$', '').replace(',', '').strip()

    # Extract number
    match = re.search(r'[\d.]+', cleaned)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None

    return None


def fetch_product_page_price_authenticated(browser: AuthenticatedBrowser, url: str) -> Optional[float]:
    """Fetch product page and extract price using authenticated session"""
    if not url:
        return None

    print(f"  Fetching product page: {url}")
    html_content = browser.fetch_page(url)

    if not html_content:
        return None

    soup = BeautifulSoup(html_content, 'html.parser')

    # Try multiple price selectors
    price_selectors = [
        '.price',
        '.product-price',
        '[class*="price"]',
        '[data-price]',
        '.selling-price',
        'span.price',
        'div.price'
    ]

    for selector in price_selectors:
        elem = soup.select_one(selector)
        if elem:
            price_text = elem.get_text(strip=True)
            price = parse_price(price_text)
            if price:
                return price

    return None


def enrich_product(browser: AuthenticatedBrowser, product: Dict) -> bool:
    """
    Enrich a single product using authenticated session + AI

    Returns True if successful, False otherwise
    """
    product_id = product['id']
    sku = product['sku']
    description = product['name']
    category = product.get('category_name', 'Unknown')
    brand = product.get('brand_name', 'Unknown')

    print(f"\n[{stats['processed']+1}] Processing: {sku}")
    print(f"  Description: {description[:60]}...")

    # Check session validity
    if not stats['session_valid']:
        print(f"  [SESSION EXPIRED] Cannot continue - re-run extract_horme_session.py")
        return False

    # Step 1: Create search query
    search_query = create_search_query(description, sku, brand)
    print(f"  Search query: '{search_query}'")

    # Step 2: Search Horme.com.sg with authenticated session
    search_results = search_horme_products_authenticated(browser, search_query)

    if not search_results:
        print(f"  [NOT FOUND] No search results")
        return False

    # Step 3: AI matching
    print(f"  Analyzing {len(search_results)} results with AI...")
    match_result = ai_match_product(description, sku, category, brand, search_results)

    if not match_result or not match_result.get('matched'):
        confidence = match_result.get('confidence', 0.0) if match_result else 0.0
        print(f"  [NOT MATCHED] Confidence too low: {confidence:.2f}")
        print(f"  Reasoning: {match_result.get('reasoning', 'N/A') if match_result else 'AI error'}")
        return False

    # Step 4: Extract price
    match_index = match_result['match_index']
    matched_product = search_results[match_index]
    confidence = match_result['confidence']

    print(f"  [MATCHED] {matched_product['title'][:50]}...")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  Reasoning: {match_result['reasoning']}")

    # Try to get price from search results first
    price = parse_price(matched_product.get('price_text'))

    # If no price in search results, fetch product page
    if not price and matched_product.get('url'):
        price = fetch_product_page_price_authenticated(browser, matched_product['url'])

    if price:
        print(f"  [PRICE FOUND] SGD {price:.2f}")
        stats['prices_extracted'] += 1
    else:
        print(f"  [PRICE NOT FOUND] Product matched but price missing")

    # Step 5: Update database
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE products SET
                    price = %s,
                    currency = 'SGD',
                    enrichment_status = 'completed',
                    enrichment_date = NOW(),
                    updated_at = NOW()
                WHERE id = %s
            """, (price, product_id))

        conn.commit()
        conn.close()

        stats['matched'] += 1
        return True

    except Exception as e:
        print(f"  [DATABASE ERROR] {e}")
        conn.rollback()
        conn.close()
        return False


def main():
    """Main execution"""
    print("="*80)
    print("AUTHENTICATED SCRAPERAPI + AI PRODUCT ENRICHMENT SYSTEM")
    print("="*80)
    print(f"Database: {DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
    print(f"Session file: {SESSION_FILE}")
    print(f"Session extracted: {SESSION_DATA['extracted_at']}")
    print(f"Cookies: {len(SESSION_DATA['cookies'])}")
    print("="*80)

    # Get products needing enrichment
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT p.id, p.sku, p.name, p.category_id, p.brand_id,
                   c.name as category_name, b.name as brand_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE (p.enrichment_status IN ('pending', 'not_found')
               OR p.price IS NULL)
            ORDER BY p.id
            LIMIT %s
        """, (BATCH_SIZE,))

        products = cur.fetchall()

    conn.close()

    if not products:
        print("\nNo products need enrichment.")
        return

    print(f"\nFound {len(products)} products to enrich")
    print("="*80)

    # Process products with authenticated browser
    with AuthenticatedBrowser(SESSION_DATA) as browser:
        for product in products:
            try:
                enrich_product(browser, product)
                stats['processed'] += 1

                # Rate limiting
                time.sleep(2)

                # Check session validity
                if not stats['session_valid']:
                    print("\n" + "="*80)
                    print("SESSION EXPIRED - STOPPING")
                    print("="*80)
                    print("\nPlease re-run: python scripts/extract_horme_session.py")
                    print("Then restart this script.")
                    break

            except Exception as e:
                print(f"  [ERROR] {e}")
                stats['errors'] += 1
                stats['processed'] += 1

    # Print statistics
    print("\n" + "="*80)
    print("ENRICHMENT COMPLETE")
    print("="*80)
    print(f"Processed:          {stats['processed']:,}")
    print(f"Matched:            {stats['matched']:,}")
    print(f"Prices Extracted:   {stats['prices_extracted']:,}")
    print(f"Not Found:          {stats['processed'] - stats['matched']:,}")
    print(f"Errors:             {stats['errors']:,}")
    print(f"\nAPI Usage:")
    print(f"Playwright calls:   {stats['playwright_calls']:,}")
    print(f"ScraperAPI calls:   {stats['scraperapi_calls']:,}")
    print(f"OpenAI calls:       {stats['openai_calls']:,}")
    print(f"Session valid:      {'YES' if stats['session_valid'] else 'NO (EXPIRED)'}")

    if not stats['session_valid']:
        print(f"\n[WARNING] Session expired during processing!")
        print(f"Re-run: python scripts/extract_horme_session.py")

    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nEnrichment interrupted. Progress has been saved.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
