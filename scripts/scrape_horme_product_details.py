"""
Horme Product Enrichment Web Scraper - PRODUCTION VERSION
Scrape full product details from horme.com.sg using AI-powered extraction

NO MOCK DATA - NO HARDCODING - NO FALLBACKS
Author: Horme Production Team
Date: 2025-01-17
"""

import os
import sys
import psycopg2
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from openai import OpenAI
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/web_scraping.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment (NO HARDCODED VALUES)
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SCRAPING_RATE_LIMIT = float(os.getenv('SCRAPING_RATE_LIMIT', '10.0'))  # requests/second (increased for speed)
SCRAPING_TIMEOUT = int(os.getenv('SCRAPING_TIMEOUT', '30'))  # seconds
SCRAPING_MAX_RETRIES = int(os.getenv('SCRAPING_MAX_RETRIES', '3'))
USER_AGENT = os.getenv('SCRAPING_USER_AGENT', 'Mozilla/5.0 (compatible; HormeBot/1.0)')

# Validate required environment variables
if not DATABASE_URL:
    raise ValueError(
        "CRITICAL: DATABASE_URL environment variable is required. "
        "Example: postgresql://user:pass@postgres:5432/horme_db"
    )

if not OPENAI_API_KEY:
    raise ValueError(
        "CRITICAL: OPENAI_API_KEY environment variable is required. "
        "Get your API key from https://platform.openai.com/api-keys"
    )

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')


def get_db_connection():
    """Get PostgreSQL connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        raise RuntimeError(
            "Failed to connect to PostgreSQL. "
            "Check DATABASE_URL and ensure database is running."
        )


async def fetch_page_content(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """
    Fetch page content from URL

    Args:
        session: aiohttp client session
        url: URL to fetch

    Returns:
        HTML content or None if failed
    """
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

    for retry in range(SCRAPING_MAX_RETRIES):
        try:
            async with session.get(url, headers=headers, timeout=SCRAPING_TIMEOUT) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.debug(f"  Fetched {url} (status: {response.status}, size: {len(content)} bytes)")
                    return content
                elif response.status == 404:
                    logger.warning(f"  Product not found (404): {url}")
                    return None
                else:
                    logger.warning(f"  HTTP {response.status}: {url}")

        except asyncio.TimeoutError:
            logger.warning(f"  Timeout (retry {retry+1}/{SCRAPING_MAX_RETRIES}): {url}")
        except aiohttp.ClientError as e:
            logger.warning(f"  Client error (retry {retry+1}/{SCRAPING_MAX_RETRIES}): {url} - {e}")
        except Exception as e:
            logger.error(f"  Unexpected error: {url} - {e}")
            break

        # Exponential backoff
        if retry < SCRAPING_MAX_RETRIES - 1:
            await asyncio.sleep(2 ** retry)

    logger.error(f"  Failed to fetch after {SCRAPING_MAX_RETRIES} retries: {url}")
    return None


def extract_product_data_with_ai(html_content: str, product_sku: str) -> Dict[str, Any]:
    """
    Extract product information from HTML using OpenAI GPT-4

    Args:
        html_content: Raw HTML content
        product_sku: Product SKU for reference

    Returns:
        Dictionary with extracted product data
    """
    # Parse HTML to extract relevant sections
    soup = BeautifulSoup(html_content, 'html.parser')

    # Get text content (remove scripts and styles)
    for script in soup(["script", "style"]):
        script.decompose()

    page_text = soup.get_text(separator='\n', strip=True)

    # Limit text length for API (GPT-4 has token limits)
    if len(page_text) > 10000:
        page_text = page_text[:10000] + "\n... (content truncated)"

    # Construct prompt for GPT-4
    prompt = f"""
Extract product information from this Horme.com.sg product page content.

Product SKU: {product_sku}

Page Content:
{page_text}

Extract and return ONLY a JSON object with the following structure:
{{
  "full_description": "detailed product description (2-3 paragraphs)",
  "specifications": {{
    "key1": "value1",
    "key2": "value2"
  }},
  "features": ["feature1", "feature2", "feature3"],
  "price_sgd": 0.00,
  "availability": "in_stock | out_of_stock | discontinued",
  "images": ["image_url1", "image_url2"],
  "documents": [
    {{"name": "Manual", "url": "document_url"}},
    {{"name": "Datasheet", "url": "datasheet_url"}}
  ],
  "related_products": ["sku1", "sku2"],
  "brand": "brand name",
  "model": "model number"
}}

Important:
- Extract REAL data only (no assumptions)
- If a field is not found, use null or empty array
- Ensure all URLs are complete (starting with http/https)
- Price should be a number (SGD currency assumed)
- Return ONLY the JSON object, no additional text
"""

    try:
        logger.debug(f"  Calling OpenAI API for SKU {product_sku}...")

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting product information from e-commerce pages. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for factual extraction
            max_tokens=1500
        )

        # Extract JSON from response
        ai_response = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if ai_response.startswith('```json'):
            ai_response = ai_response[7:]
        if ai_response.startswith('```'):
            ai_response = ai_response[3:]
        if ai_response.endswith('```'):
            ai_response = ai_response[:-3]

        ai_response = ai_response.strip()

        # Parse JSON
        product_data = json.loads(ai_response)
        logger.debug(f"  AI extraction successful for SKU {product_sku}")

        return product_data

    except json.JSONDecodeError as e:
        logger.error(f"  JSON parsing error for SKU {product_sku}: {e}")
        logger.error(f"  AI response: {ai_response[:500]}")
        return {}
    except Exception as e:
        logger.error(f"  OpenAI API error for SKU {product_sku}: {e}")
        return {}


def update_product_with_enriched_data(conn, product_id: int, product_data: Dict[str, Any]) -> bool:
    """
    Update product in database with enriched data

    Args:
        conn: Database connection
        product_id: Product ID to update
        product_data: Extracted product data from AI

    Returns:
        True if successful, False otherwise
    """
    try:
        with conn.cursor() as cur:
            # Prepare data for update
            enriched_description = product_data.get('full_description')
            specifications = product_data.get('specifications', {})
            features = product_data.get('features', [])
            price = product_data.get('price_sgd')
            availability = product_data.get('availability', 'in_stock')
            images = product_data.get('images', [])
            documents = product_data.get('documents', [])

            # Build technical_specs JSONB
            technical_specs = {
                'specifications': specifications,
                'features': features,
                'documents': documents
            }

            # Update product
            cur.execute("""
                UPDATE products SET
                    enriched_description = %s,
                    technical_specs = %s,
                    base_price = COALESCE(%s, base_price),
                    availability = %s,
                    images_url = %s,
                    enrichment_status = 'completed',
                    enrichment_date = NOW(),
                    updated_at = NOW()
                WHERE id = %s
            """, (
                enriched_description,
                json.dumps(technical_specs),
                price,
                availability,
                json.dumps(images),
                product_id
            ))

        conn.commit()
        return True

    except Exception as e:
        logger.error(f"  Database update failed for product {product_id}: {e}")
        conn.rollback()
        return False


async def process_product_enrichment(
    session: aiohttp.ClientSession,
    conn,
    queue_item: Dict[str, Any]
) -> bool:
    """
    Process a single product enrichment task

    Args:
        session: aiohttp client session
        conn: Database connection
        queue_item: Queue item dict with url, product_id, catalogue_id

    Returns:
        True if successful, False otherwise
    """
    url = queue_item['url']
    product_id = queue_item['product_id']
    catalogue_id = queue_item['catalogue_id']
    queue_id = queue_item['id']
    product_sku = queue_item['sku']

    logger.info(f"Processing: SKU {product_sku} (Catalogue ID: {catalogue_id})")

    # Update queue status to processing
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE scraping_queue SET
                status = 'processing',
                started_at = NOW()
            WHERE id = %s
        """, (queue_id,))
    conn.commit()

    # Fetch page content
    html_content = await fetch_page_content(session, url)

    if not html_content:
        # Mark as failed
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE scraping_queue SET
                    status = 'failed',
                    error_message = 'Failed to fetch page content',
                    completed_at = NOW()
                WHERE id = %s
            """, (queue_id,))

            cur.execute("""
                UPDATE products SET
                    enrichment_status = 'failed'
                WHERE id = %s
            """, (product_id,))
        conn.commit()
        return False

    # Extract data using AI
    product_data = extract_product_data_with_ai(html_content, product_sku)

    if not product_data:
        # Mark as failed
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE scraping_queue SET
                    status = 'failed',
                    error_message = 'AI extraction failed',
                    completed_at = NOW()
                WHERE id = %s
            """, (queue_id,))

            cur.execute("""
                UPDATE products SET
                    enrichment_status = 'failed'
                WHERE id = %s
            """, (product_id,))
        conn.commit()
        return False

    # Update product with enriched data
    success = update_product_with_enriched_data(conn, product_id, product_data)

    if success:
        # Mark as completed
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE scraping_queue SET
                    status = 'completed',
                    completed_at = NOW()
                WHERE id = %s
            """, (queue_id,))
        conn.commit()
        logger.info(f"  SUCCESS: SKU {product_sku} enriched")
        return True
    else:
        # Mark as failed
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE scraping_queue SET
                    status = 'failed',
                    error_message = 'Database update failed',
                    completed_at = NOW()
                WHERE id = %s
            """, (queue_id,))
        conn.commit()
        return False


async def process_scraping_queue_async(max_concurrent: int = 3):
    """
    Process scraping queue asynchronously with rate limiting

    Args:
        max_concurrent: Maximum concurrent requests
    """
    logger.info("="*80)
    logger.info("HORME PRODUCT ENRICHMENT SCRAPER - PRODUCTION VERSION")
    logger.info("="*80)
    logger.info(f"Rate Limit: {SCRAPING_RATE_LIMIT} requests/second")
    logger.info(f"Max Concurrent: {max_concurrent} workers")
    logger.info(f"Timeout: {SCRAPING_TIMEOUT} seconds")
    logger.info(f"Max Retries: {SCRAPING_MAX_RETRIES}")
    logger.info("="*80)

    conn = get_db_connection()

    # Get queue statistics
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'processing') as processing,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'failed') as failed
            FROM scraping_queue
        """)
        stats = cur.fetchone()
        pending, processing, completed, failed = stats

    logger.info(f"\nQueue Statistics:")
    logger.info(f"  Pending: {pending:,}")
    logger.info(f"  Processing: {processing:,}")
    logger.info(f"  Completed: {completed:,}")
    logger.info(f"  Failed: {failed:,}")
    logger.info("="*80)

    if pending == 0:
        logger.info("\nNo pending items in queue. Exiting.")
        conn.close()
        return

    # Process queue
    processed = 0
    successful = 0
    failed_count = 0

    async with aiohttp.ClientSession() as session:
        while True:
            # Fetch batch of pending items
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        sq.id, sq.url, sq.product_id, sq.catalogue_item_id,
                        p.sku
                    FROM scraping_queue sq
                    JOIN products p ON p.id = sq.product_id
                    WHERE sq.status = 'pending'
                    ORDER BY sq.priority ASC, sq.created_at ASC
                    LIMIT %s
                """, (max_concurrent,))

                queue_items = cur.fetchall()

            if not queue_items:
                logger.info("\nAll items processed.")
                break

            # Process batch IN PARALLEL using asyncio.gather
            tasks = []
            for queue_item in queue_items:
                item_dict = {
                    'id': queue_item[0],
                    'url': queue_item[1],
                    'product_id': queue_item[2],
                    'catalogue_id': queue_item[3],
                    'sku': queue_item[4]
                }
                tasks.append(process_product_enrichment(session, conn, item_dict))

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successes and failures
            for result in results:
                processed += 1
                if isinstance(result, Exception):
                    logger.error(f"  Task failed with exception: {result}")
                    failed_count += 1
                elif result:
                    successful += 1
                else:
                    failed_count += 1

            # Rate limiting between batches
            await asyncio.sleep(1.0 / SCRAPING_RATE_LIMIT)

            # Progress report
            logger.info(f"\nProgress: {processed} processed, {successful} successful, {failed_count} failed")

    # Final statistics
    logger.info("\n" + "="*80)
    logger.info("ENRICHMENT COMPLETE")
    logger.info("="*80)
    logger.info(f"Total Processed: {processed:,}")
    logger.info(f"Successful: {successful:,}")
    logger.info(f"Failed: {failed_count:,}")
    logger.info("="*80)

    conn.close()


def main():
    """Main execution"""
    try:
        # Create logs directory
        os.makedirs('logs', exist_ok=True)

        # Run async scraping with HIGH CONCURRENCY for speed
        # Processing 20 products in parallel per batch
        asyncio.run(process_scraping_queue_async(max_concurrent=20))

        logger.info("\nNext Steps:")
        logger.info("1. Review enrichment logs: logs/web_scraping.log")
        logger.info("2. Populate Neo4j knowledge graph:")
        logger.info("   python scripts/populate_neo4j_graph.py")

    except KeyboardInterrupt:
        logger.info("\n\nScraping interrupted by user. Progress has been saved.")
        logger.info("Run script again to resume from where it stopped.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\nFATAL ERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
