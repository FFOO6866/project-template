"""
Fuzzy Match Scraped Products with Database
Matches scraped products from CSV with existing 19k database products
Updates prices, adds new products, marks discontinued ones
"""
import csv
import psycopg2
from psycopg2.extras import execute_batch
import os
from pathlib import Path
from difflib import SequenceMatcher
import re

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'horme_db'),
    'user': os.getenv('DB_USER', 'horme_user'),
    'password': os.getenv('DB_PASSWORD', '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42')
}

# Input CSV from scraper
INPUT_CSV = 'scraped_products_ultra_simple.csv'

# Fuzzy matching threshold
SIMILARITY_THRESHOLD = 0.85  # 85% similarity required


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
    """Load scraped products from CSV"""
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
                        'sku': row.get('sku', '').strip() if row.get('sku') else None,
                        'name': row['name'].strip(),
                        'price': price,
                        'currency': row.get('currency', 'SGD') or 'SGD',
                        'brand': row.get('brand', '').strip() if row.get('brand') else None,
                        'category': row.get('category', '').strip() if row.get('category') else None,
                        'url': row.get('url', '').strip() if row.get('url') else None
                    })
            except (ValueError, KeyError):
                continue

    return products


def get_database_products(conn):
    """Get all products from database"""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, sku, name, price, brand
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
            'brand': row[4]
        })

    cursor.close()
    return products


def match_products(scraped_products, db_products):
    """
    Match scraped products with database products
    Returns: (matched, new_products)
    """
    matched = []
    new_products = []
    db_skus = {p['sku']: p for p in db_products if p['sku']}
    db_names = {normalize_text(p['name']): p for p in db_products}

    stats = {
        'exact_sku_matches': 0,
        'fuzzy_name_matches': 0,
        'no_match': 0,
        'total_scraped': len(scraped_products)
    }

    for scraped in scraped_products:
        db_match = None

        # 1. Try exact SKU match (highest priority)
        if scraped['sku'] and scraped['sku'] in db_skus:
            db_match = db_skus[scraped['sku']]
            stats['exact_sku_matches'] += 1

        # 2. Try fuzzy name matching
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
            # Product exists in database - update price
            matched.append({
                'db_id': db_match['id'],
                'db_sku': db_match['sku'],
                'db_name': db_match['name'],
                'db_old_price': db_match['price'],
                'scraped_name': scraped['name'],
                'scraped_price': scraped['price'],
                'scraped_currency': scraped['currency'],
                'match_type': 'sku' if db_match['sku'] == scraped['sku'] else 'name'
            })
        else:
            # New product not in database
            new_products.append(scraped)
            stats['no_match'] += 1

    return matched, new_products, stats


def update_database_prices(conn, matched_products):
    """Update prices for matched products in database"""
    cursor = conn.cursor()

    updates = []
    for match in matched_products:
        updates.append((
            match['scraped_price'],
            match['scraped_currency'],
            match['db_id']
        ))

    # Batch update
    execute_batch(cursor, """
        UPDATE products
        SET price = %s,
            currency = %s,
            updated_at = NOW()
        WHERE id = %s
    """, updates)

    conn.commit()
    cursor.close()

    return len(updates)


def insert_new_products(conn, new_products):
    """Insert new products found on website but not in database"""
    if not new_products:
        return 0

    cursor = conn.cursor()

    inserts = []
    for product in new_products:
        inserts.append((
            product['sku'],
            product['name'],
            product['price'],
            product['currency'],
            product['brand'],
            product['category']
        ))

    # Batch insert
    execute_batch(cursor, """
        INSERT INTO products (sku, name, price, currency, brand, category_name, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (sku) DO NOTHING
    """, inserts)

    conn.commit()
    cursor.close()

    return len(inserts)


def generate_report(scraped_count, matched, new_products, stats, db_products_count):
    """Generate detailed matching report"""

    print("\n" + "="*80)
    print("FUZZY MATCHING REPORT")
    print("="*80)

    print(f"\nDatabase Products (Before): {db_products_count}")
    print(f"Scraped Products: {scraped_count}")

    print(f"\n--- MATCHING RESULTS ---")
    print(f"Exact SKU Matches: {stats['exact_sku_matches']}")
    print(f"Fuzzy Name Matches: {stats['fuzzy_name_matches']}")
    print(f"Total Matched: {len(matched)}")
    print(f"No Match (New Products): {stats['no_match']}")

    # Price update breakdown
    price_updates = sum(1 for m in matched if m['db_old_price'] != m['scraped_price'])
    price_same = len(matched) - price_updates

    print(f"\n--- PRICE UPDATES ---")
    print(f"Prices Updated: {price_updates}")
    print(f"Prices Unchanged: {price_same}")

    # Sample matches
    print(f"\n--- SAMPLE MATCHES (first 10) ---")
    for i, match in enumerate(matched[:10], 1):
        price_change = match['scraped_price'] - (match['db_old_price'] or 0)
        change_str = f"+${price_change:.2f}" if price_change > 0 else f"${price_change:.2f}"

        print(f"\n{i}. {match['db_name']}")
        print(f"   SKU: {match['db_sku']}")
        print(f"   Old Price: ${match['db_old_price'] or 0:.2f} -> New Price: ${match['scraped_price']:.2f} ({change_str})")
        print(f"   Match Type: {match['match_type'].upper()}")

    # Sample new products
    if new_products:
        print(f"\n--- SAMPLE NEW PRODUCTS (first 10) ---")
        for i, product in enumerate(new_products[:10], 1):
            print(f"\n{i}. {product['name']}")
            print(f"   SKU: {product['sku'] or 'N/A'}")
            print(f"   Price: ${product['price']:.2f}")
            print(f"   Category: {product['category'] or 'N/A'}")

    print("\n" + "="*80)


def main():
    """Main fuzzy matching workflow"""
    print("="*80)
    print("FUZZY MATCHING: SCRAPED PRODUCTS -> DATABASE")
    print("="*80)

    # Check if CSV exists
    csv_path = Path(INPUT_CSV)
    if not csv_path.exists():
        print(f"\n[ERROR] CSV file not found: {INPUT_CSV}")
        print("Please run the scraper first to generate the CSV file.")
        return

    print(f"\nInput CSV: {INPUT_CSV}")
    print(f"Similarity Threshold: {SIMILARITY_THRESHOLD * 100}%")
    print()

    # Step 1: Load scraped products
    print("[1/5] Loading scraped products from CSV...")
    scraped_products = load_scraped_products(INPUT_CSV)
    print(f"      Loaded {len(scraped_products)} products with prices")

    # Step 2: Load database products
    print("[2/5] Loading products from database...")
    conn = psycopg2.connect(**DB_CONFIG)
    db_products = get_database_products(conn)
    print(f"      Loaded {len(db_products)} products from database")

    # Step 3: Match products
    print("[3/5] Fuzzy matching products...")
    matched, new_products, stats = match_products(scraped_products, db_products)
    print(f"      Matched: {len(matched)}, New: {len(new_products)}")

    # Step 4: Update database
    print("[4/5] Updating database prices...")
    updated_count = update_database_prices(conn, matched)
    print(f"      Updated {updated_count} product prices")

    # Step 5: Insert new products
    print("[5/5] Inserting new products...")
    inserted_count = insert_new_products(conn, new_products)
    print(f"      Inserted {inserted_count} new products")

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
    print(f"Total Products: {result[0]}")
    print(f"Products with Prices: {result[1]}")
    print(f"Price Coverage: {result[2]}%")
    print("="*80)


if __name__ == '__main__':
    main()
