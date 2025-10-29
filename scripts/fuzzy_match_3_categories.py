"""
Fuzzy Match 36,113 Scraped Products with Database
Matches scraped products from scraped_3_main_categories.csv with existing database products
Updates prices, adds new products, generates comprehensive report
"""
import csv
import psycopg2
from psycopg2.extras import execute_batch
import os
from pathlib import Path
from difflib import SequenceMatcher
import re
import time

# Database configuration (Docker container)
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'horme_db',
    'user': 'horme_user',
    'password': '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42'
}

# Input CSV from scraper
INPUT_CSV = 'scraped_3_main_categories.csv'

# Fuzzy matching threshold
SIMILARITY_THRESHOLD = 0.80  # 80% similarity required (slightly lower for better matches)


def normalize_text(text):
    """Normalize text for comparison"""
    if not text:
        return ''
    # Convert to lowercase, remove extra spaces, remove special chars
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s-]', '', text)
    return text


def calculate_similarity(str1, str2):
    """Calculate similarity between two strings"""
    str1_norm = normalize_text(str1)
    str2_norm = normalize_text(str2)
    return SequenceMatcher(None, str1_norm, str2_norm).ratio()


def load_scraped_products(csv_file):
    """Load scraped products from CSV (name, price, category, db_category_code, url)"""
    products = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Skip empty rows or rows without price
            if not row.get('name') or not row.get('price'):
                continue

            try:
                price = float(row['price'])
                if price > 0:
                    products.append({
                        'name': row['name'].strip(),
                        'price': price,
                        'currency': 'SGD',
                        'category': row.get('category', '').strip() if row.get('category') else None,
                        'db_category_code': row.get('db_category_code', '').strip() if row.get('db_category_code') else None,
                        'url': row.get('url', '').strip() if row.get('url') else None
                    })
            except (ValueError, KeyError) as e:
                continue

    return products


def get_database_products(conn):
    """Get all products from database"""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, sku, name, price, category_id, category
        FROM products
        ORDER BY id
    """)

    products = []
    for row in cursor.fetchall():
        products.append({
            'id': row[0],
            'sku': row[1],
            'name': row[2],
            'price': row[3],
            'category_id': row[4],
            'category': row[5]
        })

    cursor.close()
    return products


def match_products(scraped_products, db_products):
    """
    Match scraped products with database products
    Returns: (matched, new_products, stats)
    """
    matched = []
    new_products = []

    # Create lookup dictionaries
    db_names_normalized = {}
    for p in db_products:
        normalized = normalize_text(p['name'])
        if normalized:
            db_names_normalized[normalized] = p

    stats = {
        'exact_name_matches': 0,
        'fuzzy_name_matches': 0,
        'no_match': 0,
        'total_scraped': len(scraped_products),
        'processing_time': 0
    }

    start_time = time.time()
    processed = 0

    print("\n  Progress: ", end='', flush=True)

    for scraped in scraped_products:
        processed += 1
        if processed % 1000 == 0:
            print(f"{processed}/{len(scraped_products)}...", end=' ', flush=True)

        db_match = None

        # 1. Try exact normalized name match (fastest)
        scraped_norm = normalize_text(scraped['name'])
        if scraped_norm in db_names_normalized:
            db_match = db_names_normalized[scraped_norm]
            stats['exact_name_matches'] += 1

        # 2. Try fuzzy name matching (slower but more accurate)
        elif scraped['name']:
            best_match = None
            best_similarity = 0

            for db_product in db_products:
                similarity = calculate_similarity(scraped['name'], db_product['name'])

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = db_product

            if best_similarity >= SIMILARITY_THRESHOLD:
                db_match = best_match
                stats['fuzzy_name_matches'] += 1

        if db_match:
            # Product exists in database - record for price update
            matched.append({
                'db_id': db_match['id'],
                'db_sku': db_match['sku'],
                'db_name': db_match['name'],
                'db_old_price': db_match['price'],
                'db_category': db_match['category'],
                'scraped_name': scraped['name'],
                'scraped_price': scraped['price'],
                'scraped_currency': scraped['currency'],
                'scraped_category': scraped['category'],
                'match_type': 'exact' if scraped_norm in db_names_normalized else 'fuzzy'
            })
        else:
            # New product not in database
            new_products.append(scraped)
            stats['no_match'] += 1

    stats['processing_time'] = time.time() - start_time
    print(f"Done! ({stats['processing_time']:.1f}s)")

    return matched, new_products, stats


def update_database_prices(conn, matched_products):
    """Update prices for matched products in database"""
    cursor = conn.cursor()

    # Only update if price has changed
    updates = []
    for match in matched_products:
        if match['db_old_price'] != match['scraped_price']:
            updates.append((
                match['scraped_price'],
                match['scraped_currency'],
                match['db_id']
            ))

    if updates:
        # Batch update
        execute_batch(cursor, """
            UPDATE products
            SET price = %s,
                currency = %s,
                updated_at = NOW()
            WHERE id = %s
        """, updates, page_size=1000)

        conn.commit()

    cursor.close()
    return len(updates)


def generate_report(scraped_count, matched, new_products, stats, db_products_count):
    """Generate detailed matching report"""

    print("\n" + "="*80)
    print("FUZZY MATCHING REPORT")
    print("="*80)

    print(f"\nDatabase Products (Before): {db_products_count:,}")
    print(f"Scraped Products: {scraped_count:,}")

    print(f"\n--- MATCHING RESULTS ---")
    print(f"Exact Name Matches: {stats['exact_name_matches']:,}")
    print(f"Fuzzy Name Matches: {stats['fuzzy_name_matches']:,}")
    print(f"Total Matched: {len(matched):,} ({len(matched)/scraped_count*100:.1f}%)")
    print(f"No Match (New Products): {stats['no_match']:,} ({stats['no_match']/scraped_count*100:.1f}%)")
    print(f"Processing Time: {stats['processing_time']:.1f} seconds")

    # Price update breakdown
    price_updates = sum(1 for m in matched if m['db_old_price'] != m['scraped_price'])
    price_same = len(matched) - price_updates
    price_added = sum(1 for m in matched if m['db_old_price'] is None)

    print(f"\n--- PRICE UPDATES ---")
    print(f"Prices Updated (changed): {price_updates:,}")
    print(f"Prices Added (was NULL): {price_added:,}")
    print(f"Prices Unchanged: {price_same:,}")

    # Sample matches with price changes
    price_changed_matches = [m for m in matched if m['db_old_price'] != m['scraped_price']][:10]
    if price_changed_matches:
        print(f"\n--- SAMPLE PRICE UPDATES (first 10) ---")
        for i, match in enumerate(price_changed_matches, 1):
            old_price = match['db_old_price'] or 0
            price_change = match['scraped_price'] - old_price
            change_str = f"+${price_change:.2f}" if price_change > 0 else f"${price_change:.2f}"

            print(f"\n{i}. {match['db_name']}")
            print(f"   SKU: {match['db_sku'] or 'N/A'}")
            print(f"   Old Price: ${old_price:.2f} -> New Price: ${match['scraped_price']:.2f} ({change_str})")
            print(f"   Match Type: {match['match_type'].upper()}")

    # Sample new products
    if new_products:
        print(f"\n--- SAMPLE NEW PRODUCTS (first 10) ---")
        for i, product in enumerate(new_products[:10], 1):
            print(f"\n{i}. {product['name']}")
            print(f"   Price: ${product['price']:.2f}")
            print(f"   Category: {product['category'] or 'N/A'}")
            print(f"   URL: {product['url'] or 'N/A'}")

    print("\n" + "="*80)


def main():
    """Main fuzzy matching workflow"""
    print("="*80)
    print("FUZZY MATCHING: 36,113 SCRAPED PRODUCTS -> DATABASE")
    print("="*80)

    # Check if CSV exists
    csv_path = Path(INPUT_CSV)
    if not csv_path.exists():
        print(f"\n[ERROR] CSV file not found: {INPUT_CSV}")
        print("Please ensure the scraper has completed.")
        return

    print(f"\nInput CSV: {INPUT_CSV}")
    print(f"Similarity Threshold: {SIMILARITY_THRESHOLD * 100}%")
    print()

    # Step 1: Load scraped products
    print("[1/5] Loading scraped products from CSV...")
    scraped_products = load_scraped_products(INPUT_CSV)
    print(f"      Loaded {len(scraped_products):,} products with prices")

    # Step 2: Load database products
    print("[2/5] Loading products from database...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        db_products = get_database_products(conn)
        print(f"      Loaded {len(db_products):,} products from database")
    except Exception as e:
        print(f"      [ERROR] Database connection failed: {e}")
        print("      Make sure PostgreSQL container is running (docker ps)")
        return

    # Step 3: Match products
    print("[3/5] Fuzzy matching products...")
    matched, new_products, stats = match_products(scraped_products, db_products)
    print(f"      Matched: {len(matched):,}, New: {len(new_products):,}")

    # Step 4: Update database
    print("[4/5] Updating database prices...")
    updated_count = update_database_prices(conn, matched)
    print(f"      Updated {updated_count:,} product prices")

    # Step 5: Generate report (skip inserting new products for now)
    print("[5/5] Generating report...")

    # Generate report
    generate_report(len(scraped_products), matched, new_products, stats, len(db_products))

    # Final database stats
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(price) as with_price,
               ROUND(100.0 * COUNT(price) / COUNT(*), 2) as coverage
        FROM products
    """)
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    print("\n" + "="*80)
    print("FINAL DATABASE STATUS")
    print("="*80)
    print(f"Total Products: {result[0]:,}")
    print(f"Products with Prices: {result[1]:,}")
    print(f"Price Coverage: {result[2]}%")
    print("="*80)
    print(f"\nNOTE: {len(new_products):,} new products were found but NOT inserted.")
    print("Review the new products list above and decide if they should be added.")
    print("="*80)


if __name__ == '__main__':
    main()
