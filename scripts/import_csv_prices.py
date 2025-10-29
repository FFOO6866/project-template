"""
Import ERP Prices from CSV to Database
Updates existing products in database with prices from erp_product_prices.csv
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

CSV_FILE = 'erp_product_prices.csv'

def import_prices_from_csv():
    """Import prices from CSV and update database"""

    print("=" * 80)
    print("IMPORTING ERP PRICES FROM CSV")
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
    print(f"  Total products: {before_stats[0]:,}")
    print(f"  With prices:    {before_stats[1]:,} ({100*before_stats[1]/before_stats[0]:.1f}%)")
    print(f"  Without prices: {before_stats[2]:,} ({100*before_stats[2]/before_stats[0]:.1f}%)")
    print()

    # Read CSV file
    print(f"Reading {CSV_FILE}...")
    updates = []

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row['sku']
            price = row['price']

            if sku and price:
                try:
                    price_decimal = Decimal(price)
                    if price_decimal > 0:
                        updates.append((price_decimal, sku))
                except:
                    pass

    print(f"Found {len(updates):,} products with valid prices in CSV")
    print()

    # Update database in batches
    print("Updating database...")
    batch_size = 1000
    updated_count = 0

    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]

        execute_batch(cursor, """
            UPDATE products
            SET price = %s,
                updated_at = NOW()
            WHERE sku = %s
        """, batch)

        updated_count += cursor.rowcount

        if (i + batch_size) % 5000 == 0:
            print(f"  Processed {i + batch_size:,} / {len(updates):,} products...")
            conn.commit()

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
    print(f"  Total products: {after_stats[0]:,}")
    print(f"  With prices:    {after_stats[1]:,} ({100*after_stats[1]/after_stats[0]:.1f}%)")
    print(f"  Without prices: {after_stats[2]:,} ({100*after_stats[2]/after_stats[0]:.1f}%)")
    print()
    print(f"Improvement:")
    print(f"  Price coverage: {before_stats[1]:,} → {after_stats[1]:,} (+{after_stats[1]-before_stats[1]:,})")
    print(f"  Coverage %:     {100*before_stats[1]/before_stats[0]:.1f}% → {100*after_stats[1]/after_stats[0]:.1f}%")
    print("=" * 80)

    cursor.close()
    conn.close()

if __name__ == '__main__':
    import_prices_from_csv()
