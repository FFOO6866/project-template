"""
Smart CSV Import - Updates Matching Products Only
Focuses on the ~4,000 overlapping products (SKU "05" series)
"""

import csv
import os
import psycopg2
from psycopg2.extras import execute_batch
from decimal import Decimal

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'horme_db'),
    'user': os.getenv('DB_USER', 'horme_user'),
    'password': os.getenv('DB_PASSWORD', '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42')
}

CSV_FILE = '../erp_product_prices.csv'

def import_matching_prices():
    """Import prices for products that exist in both CSV and database"""

    print("=" * 80)
    print("SMART CSV PRICE IMPORT - Matching Products Only")
    print("=" * 80)
    print(f"CSV File: {CSV_FILE}")
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print()

    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Get current database stats
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(price) as with_price,
            COUNT(*) - COUNT(price) as without_price
        FROM products
    """)
    before_stats = cursor.fetchone()

    print(f"Database before import:")
    print(f"  Total products:     {before_stats[0]:,}")
    print(f"  With prices:        {before_stats[1]:,} ({100*before_stats[1]/before_stats[0]:.1f}%)")
    print(f"  Without prices:     {before_stats[2]:,} ({100*before_stats[2]/before_stats[0]:.1f}%)")
    print()

    # Get all database SKUs
    print("Loading database SKUs...")
    cursor.execute("SELECT DISTINCT sku FROM products WHERE sku IS NOT NULL")
    db_skus = set(row[0] for row in cursor.fetchall())
    print(f"  Found {len(db_skus):,} unique SKUs in database")
    print()

    # Read CSV and find matches
    print(f"Reading {CSV_FILE} and finding matches...")
    matches = []
    csv_skus = set()

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row['sku']
            price = row['price']
            csv_skus.add(sku)

            if sku in db_skus and price:
                try:
                    price_decimal = Decimal(price)
                    if price_decimal > 0:
                        matches.append((price_decimal, sku))
                except:
                    pass

    print(f"  CSV has {len(csv_skus):,} unique SKUs")
    print(f"  Found {len(matches):,} matching products with prices")
    print()

    # Show SKU prefix analysis
    print("SKU Prefix Analysis:")
    for prefix in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10']:
        db_count = len([s for s in db_skus if s.startswith(prefix)])
        csv_count = len([s for s in csv_skus if s.startswith(prefix)])
        match_count = len([m for m in matches if m[1].startswith(prefix)])
        if db_count > 0 or csv_count > 0:
            print(f"  {prefix}xx: DB={db_count:,} | CSV={csv_count:,} | Matches={match_count:,}")
    print()

    if not matches:
        print("❌ No matching products found!")
        print("   This means database and CSV have completely different product sets.")
        return

    # Update database
    print(f"Updating {len(matches):,} products in database...")
    execute_batch(cursor, """
        UPDATE products
        SET price = %s,
            updated_at = NOW()
        WHERE sku = %s
    """, matches, page_size=1000)

    updated_count = cursor.rowcount
    conn.commit()

    # Get updated stats
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(price) as with_price,
            COUNT(*) - COUNT(price) as without_price
        FROM products
    """)
    after_stats = cursor.fetchone()

    print()
    print("=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    print(f"Products updated: {updated_count:,}")
    print()
    print(f"Database after import:")
    print(f"  Total products:     {after_stats[0]:,}")
    print(f"  With prices:        {after_stats[1]:,} ({100*after_stats[1]/after_stats[0]:.1f}%)")
    print(f"  Without prices:     {after_stats[2]:,} ({100*after_stats[2]/after_stats[0]:.1f}%)")
    print()
    print(f"Improvement:")
    print(f"  Price coverage:     {before_stats[1]:,} -> {after_stats[1]:,} (+{after_stats[1]-before_stats[1]:,})")
    print(f"  Coverage %:         {100*before_stats[1]/before_stats[0]:.1f}% -> {100*after_stats[1]/after_stats[0]:.1f}%")
    print("=" * 80)

    cursor.close()
    conn.close()

if __name__ == '__main__':
    import_matching_prices()
