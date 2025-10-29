"""
AI-Powered Product Enrichment - HOST VERSION
Runs on host machine to bypass Docker network restrictions

This script:
1. Runs Playwright on the host machine (has normal web access)
2. Connects to PostgreSQL in Docker container
3. Uses GPT-4 Vision for intelligent product matching
4. Extracts pricing data from Horme website

Author: Horme Production Team
Date: 2025-10-22
"""

import os
import sys
import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Third-party imports
import psycopg2
from psycopg2.extras import RealDictCursor
from playwright.async_api import async_playwright, Browser, Page
from openai import AsyncOpenAI
from bs4 import BeautifulSoup

# Configuration
DATABASE_HOST = os.getenv('DB_HOST', 'localhost')
DATABASE_PORT = os.getenv('DB_PORT', '10620')  # Mapped port from Docker
DATABASE_NAME = os.getenv('DB_NAME', 'horme_db')
DATABASE_USER = os.getenv('DB_USER', 'horme_user')
DATABASE_PASSWORD = os.getenv('DB_PASSWORD', 'horme_password')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY environment variable is required")
    sys.exit(1)

# OpenAI client
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
TEXT_MODEL = "gpt-4-turbo-preview"
VISION_MODEL = "gpt-4-vision-preview"

# Processing configuration
MAX_CONCURRENT = int(os.getenv('MAX_CONCURRENT', '5'))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.7'))

# Base URL
HORME_BASE_URL = "https://www.horme.com.sg"

# Statistics
stats = {
    'processed': 0,
    'matched': 0,
    'not_found': 0,
    'errors': 0,
    'prices_extracted': 0
}


def get_db_connection():
    """Get PostgreSQL connection to Docker container"""
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
        print(f"Connection string: postgresql://{DATABASE_USER}:***@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")
        sys.exit(1)


class AIProductEnricher:
    """AI-powered product enrichment using GPT-4 Vision"""

    def __init__(self, browser: Browser):
        self.browser = browser
        self.context = None
        self.page = None

    async def initialize(self):
        """Initialize browser context and page"""
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()

    async def close(self):
        """Close browser context"""
        if self.context:
            await self.context.close()

    def _create_search_query(self, description: str, sku: str, brand: str = None) -> str:
        """Create optimized search query"""
        # Remove SKU prefix and common noise words
        clean_desc = description.upper()
        clean_desc = re.sub(r'\b(ITEM|PRODUCT|PACK|SET|OF|THE|A|AN)\b', '', clean_desc)

        # Extract key product identifiers
        words = clean_desc.split()
        key_words = [w for w in words if len(w) > 2][:5]  # First 5 meaningful words

        search_query = ' '.join(key_words)

        # Add brand if available
        if brand and brand != 'Unknown':
            search_query = f"{brand} {search_query}"

        return search_query.strip()

    async def search_and_match_product(
        self,
        product_id: int,
        sku: str,
        description: str,
        category: str,
        brand: str
    ) -> Optional[Dict[str, Any]]:
        """
        Search for product and extract pricing using AI

        Returns dict with:
        - matched: bool
        - confidence: float
        - price: float or None
        - product_url: str or None
        - reasoning: str
        """
        try:
            # Create search query
            search_query = self._create_search_query(description, sku, brand)
            print(f"  Search query: '{search_query}'")

            # Navigate to search page
            search_url = f"{HORME_BASE_URL}/Search?q={search_query.replace(' ', '+')}"
            await self.page.goto(search_url, wait_until='networkidle', timeout=30000)

            # Wait for results to load
            await asyncio.sleep(2)

            # Take screenshot for AI analysis
            screenshot_bytes = await self.page.screenshot(full_page=False)

            # Get page HTML for text analysis
            html_content = await self.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract search result items
            results = []
            for item in soup.select('.product-item, .search-result-item, [class*="product"]')[:10]:
                title = item.select_one('.product-title, .product-name, h3, h4')
                price_elem = item.select_one('.price, .product-price, [class*="price"]')
                link = item.select_one('a')

                if title:
                    result = {
                        'title': title.get_text(strip=True),
                        'price': price_elem.get_text(strip=True) if price_elem else None,
                        'url': link['href'] if link and link.get('href') else None
                    }
                    results.append(result)

            if not results:
                print("  No search results found")
                return {
                    'matched': False,
                    'confidence': 0.0,
                    'price': None,
                    'product_url': None,
                    'reasoning': 'No search results found'
                }

            # Use GPT-4 to match the correct product
            match_result = await self._ai_match_product(
                description, sku, category, brand, results
            )

            if not match_result['matched'] or match_result['confidence'] < CONFIDENCE_THRESHOLD:
                print(f"  No confident match (confidence: {match_result['confidence']:.2f})")
                return match_result

            # Extract detailed product info
            matched_result = results[match_result['match_index']]
            product_url = matched_result['url']

            if product_url and not product_url.startswith('http'):
                product_url = HORME_BASE_URL + product_url

            # Navigate to product page if URL available
            if product_url:
                await self.page.goto(product_url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(1)

                # Extract price from product page
                price = await self._extract_price_from_page()

                return {
                    'matched': True,
                    'confidence': match_result['confidence'],
                    'price': price,
                    'product_url': product_url,
                    'reasoning': match_result['reasoning']
                }
            else:
                # Try to extract price from search results
                price_text = matched_result['price']
                price = self._parse_price_text(price_text) if price_text else None

                return {
                    'matched': True,
                    'confidence': match_result['confidence'],
                    'price': price,
                    'product_url': None,
                    'reasoning': match_result['reasoning']
                }

        except Exception as e:
            print(f"  ERROR: {e}")
            return {
                'matched': False,
                'confidence': 0.0,
                'price': None,
                'product_url': None,
                'reasoning': f'Error: {str(e)}'
            }

    async def _ai_match_product(
        self,
        target_description: str,
        target_sku: str,
        target_category: str,
        target_brand: str,
        search_results: List[Dict]
    ) -> Dict[str, Any]:
        """Use GPT-4 to match the correct product from search results"""

        results_text = "\n".join([
            f"{i}. {r['title']} - {r.get('price', 'N/A')}"
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

Analyze these search results and determine which one (if any) matches the target product.

Respond in JSON format:
{{
    "matched": true/false,
    "match_index": <index of matching product, or null if no match>,
    "confidence": <0.0 to 1.0>,
    "reasoning": "<explanation of match or why no match>"
}}

Important:
- Only return matched=true if confidence >= {CONFIDENCE_THRESHOLD}
- Consider product name, brand, and specifications
- Ignore minor differences in formatting
- Be strict about matching the correct product type
"""

        try:
            response = await openai_client.chat.completions.create(
                model=TEXT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert product matcher. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=500
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"  AI matching error: {e}")
            return {
                'matched': False,
                'match_index': None,
                'confidence': 0.0,
                'reasoning': f'AI error: {str(e)}'
            }

    async def _extract_price_from_page(self) -> Optional[float]:
        """Extract price from current product page"""
        try:
            # Common price selectors
            price_selectors = [
                '.price',
                '.product-price',
                '[class*="price"]',
                '[data-price]',
                '.selling-price'
            ]

            for selector in price_selectors:
                elem = await self.page.query_selector(selector)
                if elem:
                    price_text = await elem.inner_text()
                    price = self._parse_price_text(price_text)
                    if price:
                        return price

            return None

        except Exception as e:
            print(f"  Price extraction error: {e}")
            return None

    def _parse_price_text(self, price_text: str) -> Optional[float]:
        """Parse price from text (handles SGD, $, etc.)"""
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


async def process_batch(products: List[Dict], browser: Browser):
    """Process a batch of products"""
    enricher = AIProductEnricher(browser)
    await enricher.initialize()

    conn = get_db_connection()

    try:
        for product in products:
            product_id = product['id']
            sku = product['sku']
            description = product['name']
            category = product.get('category_name', 'Unknown')
            brand = product.get('brand_name', 'Unknown')

            print(f"\n[{stats['processed']+1}] Processing: {sku} - {description[:50]}...")

            # Search and match product
            result = await enricher.search_and_match_product(
                product_id, sku, description, category, brand
            )

            # Update database
            with conn.cursor() as cur:
                if result['matched']:
                    # Update with price if found
                    cur.execute("""
                        UPDATE products SET
                            price = %s,
                            currency = 'SGD',
                            enrichment_status = 'completed',
                            enrichment_date = NOW(),
                            updated_at = NOW()
                        WHERE id = %s
                    """, (result['price'], product_id))

                    stats['matched'] += 1
                    if result['price']:
                        stats['prices_extracted'] += 1
                        print(f"  ✓ MATCHED - Price: SGD {result['price']:.2f} (confidence: {result['confidence']:.2f})")
                    else:
                        print(f"  ✓ MATCHED - No price found (confidence: {result['confidence']:.2f})")
                else:
                    # Mark as not found
                    cur.execute("""
                        UPDATE products SET
                            enrichment_status = 'not_found',
                            enrichment_date = NOW(),
                            updated_at = NOW()
                        WHERE id = %s
                    """, (product_id,))

                    stats['not_found'] += 1
                    print(f"  ✗ NOT FOUND - {result['reasoning']}")

            conn.commit()
            stats['processed'] += 1

            # Rate limiting
            await asyncio.sleep(2)

    finally:
        await enricher.close()
        conn.close()


async def main():
    """Main execution"""
    print("="*80)
    print("AI-POWERED PRODUCT ENRICHMENT - HOST VERSION")
    print("="*80)
    print(f"Database: {DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Max concurrent: {MAX_CONCURRENT}")
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

    # Initialize Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        try:
            # Process in batches
            await process_batch(products, browser)

        finally:
            await browser.close()

    # Print statistics
    print("\n" + "="*80)
    print("ENRICHMENT COMPLETE")
    print("="*80)
    print(f"Processed:        {stats['processed']:,}")
    print(f"Matched:          {stats['matched']:,}")
    print(f"Prices Extracted: {stats['prices_extracted']:,}")
    print(f"Not Found:        {stats['not_found']:,}")
    print(f"Errors:           {stats['errors']:,}")
    print("="*80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nEnrichment interrupted. Progress has been saved.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
