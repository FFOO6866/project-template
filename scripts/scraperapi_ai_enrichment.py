"""
ScraperAPI + AI Product Enrichment System
Uses ScraperAPI to bypass network blocking + GPT-4 for intelligent product matching

This combines:
- ScraperAPI: Access Horme.com.sg search pages (bypasses blocking)
- OpenAI GPT-4: Intelligent product matching from search results
- Database: Automatic price updates

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
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# Configuration
SCRAPERAPI_KEY = os.getenv('SCRAPERAPI_KEY', '3c29b7d4798bd49564aacf76ba828d8a')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SESSION_FILE = "horme_session.json"

if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY environment variable required")
    sys.exit(1)

# Load session cookies if available
SESSION_COOKIES = {}
if os.path.exists(SESSION_FILE):
    with open(SESSION_FILE, 'r') as f:
        session_data = json.load(f)
        for cookie in session_data.get('cookies', []):
            SESSION_COOKIES[cookie['name']] = cookie['value']
    print(f"Loaded {len(SESSION_COOKIES)} session cookies from {SESSION_FILE}")
else:
    print(f"No session file found. Proceeding without authentication.")

# Database configuration
DATABASE_HOST = os.getenv('DB_HOST', 'localhost')
DATABASE_PORT = os.getenv('DB_PORT', '10620')
DATABASE_NAME = os.getenv('DB_NAME', 'horme_db')
DATABASE_USER = os.getenv('DB_USER', 'horme_user')
DATABASE_PASSWORD = os.getenv('DB_PASSWORD', 'horme_password')

# Processing configuration
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))  # Start small
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.7'))

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
TEXT_MODEL = "gpt-4-turbo-preview"

# Statistics
stats = {
    'processed': 0,
    'matched': 0,
    'not_found': 0,
    'errors': 0,
    'prices_extracted': 0,
    'scraperapi_calls': 0,
    'openai_calls': 0
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


def fetch_with_scraperapi(url: str) -> Optional[str]:
    """
    Fetch URL using ScraperAPI proxy network with authentication cookies

    Returns HTML content or None if failed
    """
    proxy_url = "http://api.scraperapi.com"
    params = {
        'api_key': SCRAPERAPI_KEY,
        'url': url,
        'render': 'false',  # Set to 'true' if JavaScript needed
        'keep_headers': 'true'  # Preserve custom headers including cookies
    }

    # Build cookie header from session cookies
    cookie_header = "; ".join([f"{name}={value}" for name, value in SESSION_COOKIES.items()])

    headers = {}
    if cookie_header:
        headers['Cookie'] = cookie_header

    try:
        response = requests.get(proxy_url, params=params, headers=headers, timeout=60)
        stats['scraperapi_calls'] += 1

        if response.status_code == 200:
            return response.text
        else:
            print(f"  ScraperAPI returned HTTP {response.status_code}")
            return None

    except Exception as e:
        print(f"  ScraperAPI error: {e}")
        return None


def create_search_query(description: str, sku: str, brand: str = None) -> str:
    """Create optimized search query from product description"""
    # Remove common noise words
    clean_desc = description.upper()
    clean_desc = re.sub(r'\b(ITEM|PRODUCT|PACK|SET|OF|THE|A|AN)\b', '', clean_desc)

    # Extract key words (first 3-4 meaningful words)
    words = clean_desc.split()
    key_words = [w for w in words if len(w) > 2][:4]

    search_query = ' '.join(key_words)

    # Add brand if available
    if brand and brand != 'Unknown':
        search_query = f"{brand} {search_query}"

    return search_query.strip()


def search_horme_products(search_query: str) -> List[Dict[str, Any]]:
    """
    Search Horme.com.sg using ScraperAPI

    Returns list of product results with title, price, url
    """
    # Construct search URL (CORRECTED - uses searchengine.aspx)
    search_url = f"https://www.horme.com.sg/searchengine.aspx?stq={search_query.replace(' ', '+')}"

    print(f"  Searching: {search_url}")

    # Fetch via ScraperAPI
    html_content = fetch_with_scraperapi(search_url)

    if not html_content:
        return []

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract search results (try multiple selectors)
    results = []

    # Common e-commerce product selectors
    product_selectors = [
        '.product-item',
        '.search-result-item',
        '[class*="product"]',
        '.item',
        'article'
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
                        if title and len(title) > 10:  # Valid title
                            break

                # Extract price
                price_text = None
                price_selectors = ['.price', '.product-price', '[class*="price"]']
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


def fetch_product_page_price(url: str) -> Optional[float]:
    """Fetch product page and extract price"""
    if not url:
        return None

    print(f"  Fetching product page: {url}")
    html_content = fetch_with_scraperapi(url)

    if not html_content:
        return None

    soup = BeautifulSoup(html_content, 'html.parser')

    # Try multiple price selectors
    price_selectors = [
        '.price',
        '.product-price',
        '[class*="price"]',
        '[data-price]',
        '.selling-price'
    ]

    for selector in price_selectors:
        elem = soup.select_one(selector)
        if elem:
            price_text = elem.get_text(strip=True)
            price = parse_price(price_text)
            if price:
                return price

    return None


def enrich_product(product: Dict) -> bool:
    """
    Enrich a single product using ScraperAPI + AI

    Returns True if successful, False otherwise
    """
    product_id = product['id']
    sku = product['sku']
    description = product['name']
    category = product.get('category_name', 'Unknown')
    brand = product.get('brand_name', 'Unknown')

    print(f"\n[{stats['processed']+1}] Processing: {sku}")
    print(f"  Description: {description[:60]}...")

    # Step 1: Create search query
    search_query = create_search_query(description, sku, brand)
    print(f"  Search query: '{search_query}'")

    # Step 2: Search Horme.com.sg
    search_results = search_horme_products(search_query)

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
        price = fetch_product_page_price(matched_product['url'])

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
    print("SCRAPERAPI + AI PRODUCT ENRICHMENT SYSTEM")
    print("="*80)
    print(f"Database: {DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
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

    # Process products
    for product in products:
        try:
            enrich_product(product)
            stats['processed'] += 1

            # Rate limiting (avoid overwhelming APIs)
            time.sleep(2)

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
    print(f"ScraperAPI calls:   {stats['scraperapi_calls']:,}")
    print(f"OpenAI calls:       {stats['openai_calls']:,}")
    print(f"\nEstimated Costs (this batch):")
    print(f"ScraperAPI:         ${stats['scraperapi_calls'] * 0.0000997:.2f}")
    print(f"OpenAI:             ${stats['openai_calls'] * 0.01:.2f}")
    print(f"Total:              ${(stats['scraperapi_calls'] * 0.0000997) + (stats['openai_calls'] * 0.01):.2f}")
    print("="*80)

    # Extrapolate costs for full dataset
    if stats['processed'] > 0:
        success_rate = stats['matched'] / stats['processed']
        total_products = 19143

        print(f"\nProjected for all {total_products:,} products:")
        print(f"Success rate:       {success_rate*100:.1f}%")
        print(f"Expected matches:   {int(total_products * success_rate):,}")
        print(f"ScraperAPI cost:    ${total_products * 2 * 0.0000997:.2f}")  # 2 calls per product avg
        print(f"OpenAI cost:        ${total_products * 0.01:.2f}")
        print(f"Total estimated:    ${(total_products * 2 * 0.0000997) + (total_products * 0.01):.2f}")
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
