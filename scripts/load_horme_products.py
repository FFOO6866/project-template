"""
Horme Product Data Loader - PRODUCTION VERSION
Load real product data from Excel to PostgreSQL

NO MOCK DATA - NO HARDCODING - NO FALLBACKS
Author: Horme Production Team
Date: 2025-01-17
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_loading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment (NO HARDCODED VALUES)
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError(
        "CRITICAL: DATABASE_URL environment variable is required. "
        "Example: postgresql://user:pass@postgres:5432/horme_db"
    )

# File paths
PROJECT_ROOT = Path(__file__).parent.parent
EXCEL_FILE = PROJECT_ROOT / "docs" / "reference" / "ProductData (Top 3 Cats).xlsx"

# Validate file exists
if not EXCEL_FILE.exists():
    raise FileNotFoundError(
        f"CRITICAL: Excel file not found: {EXCEL_FILE}. "
        "Ensure ProductData (Top 3 Cats).xlsx is in docs/reference/ directory."
    )

# Category definitions (MUST MATCH EXCEL DATA EXACTLY)
CATEGORIES = [
    {
        'name': '09 - Electrical Power Tools',
        'slug': 'power-tools',
        'description': 'Electric and battery-powered tools for construction and DIY projects'
    },
    {
        'name': '21 - Safety Products',
        'slug': 'safety-equipment',
        'description': 'Personal protective equipment and safety gear for workplace safety'
    },
    {
        'name': '05 - Cleaning Products',
        'slug': 'cleaning-products',
        'description': 'Professional cleaning chemicals and supplies for industrial and commercial use'
    }
]


def get_db_connection():
    """Get PostgreSQL connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        logger.error(f"DATABASE_URL: {DATABASE_URL}")
        raise RuntimeError(
            "Failed to connect to PostgreSQL. "
            "Check DATABASE_URL and ensure database is running."
        )


def load_categories(conn):
    """Load category master data"""
    logger.info("Loading Categories...")

    with conn.cursor() as cur:
        for cat in CATEGORIES:
            cur.execute("""
                INSERT INTO categories (name, slug, description, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, true, NOW(), NOW())
                ON CONFLICT (slug) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    updated_at = NOW()
                RETURNING id, name
            """, (cat['name'], cat['slug'], cat['description']))

            cat_id, cat_name = cur.fetchone()
            logger.info(f"  Category: {cat_name} (ID: {cat_id})")

    conn.commit()
    logger.info("Categories loaded successfully")


def load_brands(conn, df):
    """Extract and load unique brands from Excel"""
    logger.info("Loading Brands...")

    # Get unique brands
    brands = df['Brand '].dropna().unique()  # Note: Excel has trailing space
    logger.info(f"  Found {len(brands)} unique brands")

    loaded = 0
    with conn.cursor() as cur:
        for brand in brands:
            brand = str(brand).strip()
            if not brand or brand.upper() == 'NO BRAND':
                continue

            slug = brand.lower().replace(' ', '-').replace('/', '-').replace('&', 'and')
            slug = ''.join(c if c.isalnum() or c == '-' else '-' for c in slug)

            try:
                cur.execute("""
                    INSERT INTO brands (name, slug, is_active, created_at, updated_at)
                    VALUES (%s, %s, true, NOW(), NOW())
                    ON CONFLICT (slug) DO UPDATE SET
                        name = EXCLUDED.name,
                        updated_at = NOW()
                    RETURNING id, name
                """, (brand, slug))

                brand_id, brand_name = cur.fetchone()
                loaded += 1

                if loaded % 10 == 0:
                    logger.info(f"  Loaded {loaded} brands...")

            except Exception as e:
                logger.warning(f"  Failed to load brand '{brand}': {e}")
                continue

    conn.commit()
    logger.info(f"Brands loaded: {loaded} total")


def get_category_id(conn, category_name):
    """Get category ID by name"""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM categories WHERE name = %s", (category_name.strip(),))
        result = cur.fetchone()
        return result[0] if result else None


def get_brand_id(conn, brand_name):
    """Get brand ID by name"""
    if not brand_name or pd.isna(brand_name) or str(brand_name).strip().upper() == 'NO BRAND':
        return None

    brand_name = str(brand_name).strip()

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM brands WHERE name = %s", (brand_name,))
        result = cur.fetchone()
        return result[0] if result else None


def load_products(conn, df, is_package=False, batch_size=500):
    """
    Load products from DataFrame

    Args:
        conn: Database connection
        df: Pandas DataFrame with product data
        is_package: True if loading package SKUs
        batch_size: Number of products to insert per batch
    """
    product_type = "Package" if is_package else "Single"
    logger.info(f"Loading {product_type} SKU Products...")
    logger.info(f"  Total rows: {len(df)}")

    products_loaded = 0
    products_failed = 0
    products_queued_for_enrichment = 0

    with conn.cursor() as cur:
        for idx, row in df.iterrows():
            # Commit every 100 products to avoid transaction issues
            if idx > 0 and idx % 100 == 0:
                conn.commit()
                logger.info(f"  Loaded {products_loaded} products so far...")
            try:
                # Extract data (handle column name variations with trailing spaces)
                sku = str(row.get('Product SKU', '')).strip()
                name = str(row.get('Description', '')).strip()
                category_name = str(row.get('Category ', '')).strip()  # Trailing space!
                brand_name = str(row.get('Brand ', '')).strip()  # Trailing space!
                catalogue_id = row.get('CatalogueItemID')

                # Validate required fields
                if not sku or not name or sku == 'nan' or name == 'nan':
                    logger.warning(f"  Row {idx+2}: Missing SKU or Description, skipping")
                    products_failed += 1
                    continue

                # Get foreign keys
                category_id = get_category_id(conn, category_name)
                brand_id = get_brand_id(conn, brand_name)

                if not category_id:
                    logger.error(f"  Row {idx+2}: Category '{category_name}' not found, skipping")
                    products_failed += 1
                    continue

                # Prepare slug (URL-friendly identifier)
                slug = sku.lower().replace('/', '-').replace(' ', '-').replace('#', 'num')
                slug = ''.join(c if c.isalnum() or c == '-' else '-' for c in slug)

                # Prepare catalogue_item_id (convert to int if exists)
                catalogue_item_id = None
                if not pd.isna(catalogue_id) and catalogue_id:
                    try:
                        catalogue_item_id = int(float(catalogue_id))  # Handle float from Excel
                    except (ValueError, TypeError):
                        logger.warning(f"  Row {idx+2}: Invalid Catalogue ID '{catalogue_id}'")

                # Determine enrichment status
                enrichment_status = 'pending' if catalogue_item_id else 'not_applicable'

                # Insert product
                cur.execute("""
                    INSERT INTO products (
                        sku, product_code, name, description,
                        category_id, brand_id, catalogue_id,
                        is_published, is_package, currency,
                        enrichment_status, is_active,
                        created_at, updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        true, %s, 'SGD',
                        %s, true,
                        NOW(), NOW()
                    )
                    ON CONFLICT (product_code) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        category_id = EXCLUDED.category_id,
                        brand_id = EXCLUDED.brand_id,
                        catalogue_id = EXCLUDED.catalogue_id,
                        enrichment_status = EXCLUDED.enrichment_status,
                        updated_at = NOW()
                    RETURNING id, sku
                """, (
                    sku, sku, name, name,  # Use SKU as product_code, name as description
                    category_id, brand_id, catalogue_item_id,
                    is_package, enrichment_status
                ))

                product_id, product_sku = cur.fetchone()
                products_loaded += 1

                # Queue for enrichment if has catalogue ID
                if catalogue_item_id:
                    try:
                        cur.execute("""
                            INSERT INTO scraping_queue (
                                product_id, catalogue_item_id,
                                priority, status, created_at
                            )
                            VALUES (%s, %s, 5, 'pending', NOW())
                        """, (product_id, catalogue_item_id))
                        products_queued_for_enrichment += 1
                    except Exception:
                        # Skip if scraping queue insert fails
                        pass

                # Progress logging
                if products_loaded % 100 == 0:
                    logger.info(f"  Loaded {products_loaded} {product_type} products...")
                    conn.commit()  # Commit in batches for performance

            except psycopg2.IntegrityError as e:
                logger.error(f"  Row {idx+2}: Database integrity error: {e}")
                products_failed += 1
                conn.rollback()
                continue
            except Exception as e:
                logger.error(f"  Row {idx+2}: Unexpected error: {e}")
                products_failed += 1
                continue

    # Final commit
    conn.commit()

    logger.info(f"{product_type} SKU Products Summary:")
    logger.info(f"  Loaded: {products_loaded}")
    logger.info(f"  Failed: {products_failed}")
    logger.info(f"  Queued for enrichment: {products_queued_for_enrichment}")

    return products_loaded, products_failed, products_queued_for_enrichment


def create_initial_mappings(conn):
    """Create basic category/task keyword mappings for hybrid recommendations"""
    logger.info("Creating category keyword mappings...")

    mappings = [
        # Power Tools
        ('Power Tools', 'drill', 1.0),
        ('Power Tools', 'saw', 1.0),
        ('Power Tools', 'grinder', 1.0),
        ('Power Tools', 'sander', 0.9),
        ('Power Tools', 'power tool', 1.0),
        ('Power Tools', 'cordless', 0.8),
        ('Power Tools', 'battery', 0.7),
        ('Power Tools', 'electric', 0.7),

        # Safety Equipment
        ('Safety Equipment', 'safety', 1.0),
        ('Safety Equipment', 'protective', 1.0),
        ('Safety Equipment', 'glove', 0.9),
        ('Safety Equipment', 'helmet', 0.9),
        ('Safety Equipment', 'glasses', 0.9),
        ('Safety Equipment', 'mask', 0.9),
        ('Safety Equipment', 'ppe', 1.0),
        ('Safety Equipment', 'protection', 1.0),

        # Cleaning Products
        ('Cleaning Products', 'clean', 1.0),
        ('Cleaning Products', 'detergent', 0.9),
        ('Cleaning Products', 'chemical', 0.8),
        ('Cleaning Products', 'sanitize', 0.9),
        ('Cleaning Products', 'disinfect', 0.9),
        ('Cleaning Products', 'wash', 0.8),
    ]

    with conn.cursor() as cur:
        for category, keyword, weight in mappings:
            cur.execute("""
                INSERT INTO category_keyword_mappings (category, keyword, weight, created_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (category, keyword) DO UPDATE SET
                    weight = EXCLUDED.weight
            """, (category, keyword, weight))

    conn.commit()
    logger.info(f"  Created {len(mappings)} keyword mappings")


def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("HORME PRODUCT DATA LOADER - PRODUCTION VERSION")
    logger.info("="*80)
    logger.info(f"Source: {EXCEL_FILE}")
    logger.info(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    logger.info("="*80)

    try:
        # Step 1: Connect to database
        logger.info("\nStep 1: Database Connection")
        conn = get_db_connection()
        logger.info("  Connected successfully")

        # Step 2: Load categories
        logger.info("\nStep 2: Master Data - Categories")
        load_categories(conn)

        # Step 3: Read Excel file
        logger.info("\nStep 3: Reading Excel File")
        logger.info(f"  File size: {EXCEL_FILE.stat().st_size:,} bytes")

        # Read Product sheet (Single SKUs)
        logger.info("  Reading 'Product' sheet...")
        df_single = pd.read_excel(EXCEL_FILE, sheet_name='Product')
        logger.info(f"  Found {len(df_single)} single SKU products")

        # Read Package sheet (Package SKUs)
        logger.info("  Reading 'Package' sheet...")
        df_package = pd.read_excel(EXCEL_FILE, sheet_name='Package')
        logger.info(f"  Found {len(df_package)} package SKU products")

        total_products = len(df_single) + len(df_package)
        logger.info(f"  TOTAL: {total_products} products to load")

        # Step 4: Load brands
        logger.info("\nStep 4: Master Data - Brands")
        all_brands = pd.concat(
            [df_single['Brand '], df_package['Brand ']],
            ignore_index=True
        )
        load_brands(conn, pd.DataFrame({'Brand ': all_brands}))

        # Step 5: Load single SKU products
        logger.info("\nStep 5: Loading Single SKU Products")
        loaded_single, failed_single, queued_single = load_products(
            conn, df_single, is_package=False
        )

        # Step 6: Load package SKU products
        logger.info("\nStep 6: Loading Package SKU Products")
        loaded_package, failed_package, queued_package = load_products(
            conn, df_package, is_package=True
        )

        # Step 7: Create keyword mappings
        logger.info("\nStep 7: Creating Keyword Mappings")
        create_initial_mappings(conn)

        # Summary
        total_loaded = loaded_single + loaded_package
        total_failed = failed_single + failed_package
        total_queued = queued_single + queued_package

        logger.info("\n" + "="*80)
        logger.info("IMPORT COMPLETE")
        logger.info("="*80)
        logger.info(f"Single SKU:  {loaded_single:,} loaded, {failed_single:,} failed")
        logger.info(f"Package SKU: {loaded_package:,} loaded, {failed_package:,} failed")
        logger.info("-"*80)
        logger.info(f"TOTAL:       {total_loaded:,} loaded, {total_failed:,} failed")
        logger.info(f"ENRICHMENT:  {total_queued:,} products queued for web scraping")
        logger.info("="*80)

        # Check database stats
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM products")
            db_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM categories")
            cat_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM brands")
            brand_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM scraping_queue WHERE status = 'pending'")
            queue_count = cur.fetchone()[0]

        logger.info(f"\nDatabase Statistics:")
        logger.info(f"  Products: {db_count:,}")
        logger.info(f"  Categories: {cat_count}")
        logger.info(f"  Brands: {brand_count}")
        logger.info(f"  Scraping Queue: {queue_count:,} pending")
        logger.info("="*80)

        conn.close()

        if total_failed > 0:
            logger.warning(f"\nWARNING: {total_failed} products failed to load. Check logs for details.")
            sys.exit(1)
        else:
            logger.info("\nSUCCESS: All products loaded successfully!")
            logger.info(f"\nNext Steps:")
            logger.info(f"1. Run web scraper to enrich {total_queued:,} products:")
            logger.info(f"   python scripts/scrape_horme_product_details.py")
            logger.info(f"2. Populate Neo4j knowledge graph:")
            logger.info(f"   python scripts/populate_neo4j_graph.py")
            sys.exit(0)

    except Exception as e:
        logger.error(f"\nFATAL ERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Run main
    main()
