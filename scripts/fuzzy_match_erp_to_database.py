"""
Fuzzy Name Matching: ERP CSV to Database Products
Attempts to match ERP products to database products by name/description similarity
"""

import csv
import os
import psycopg2
from rapidfuzz import fuzz, process
from typing import List, Dict, Tuple
import json

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'horme_db'),
    'user': os.getenv('DB_USER', 'horme_user'),
    'password': os.getenv('DB_PASSWORD', '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42')
}

ERP_CSV_FILE = 'erp_product_prices.csv'

def normalize_name(name: str) -> str:
    """Normalize product name for better matching"""
    if not name:
        return ""

    # Convert to uppercase
    normalized = name.upper()

    # Remove common noise words
    noise_words = ['THE', 'A', 'AN', 'FOR', 'WITH', 'AND', '&']
    words = normalized.split()
    words = [w for w in words if w not in noise_words]

    # Remove extra spaces
    normalized = ' '.join(words)

    # Remove special characters but keep alphanumeric and spaces
    normalized = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in normalized)

    # Collapse multiple spaces
    normalized = ' '.join(normalized.split())

    return normalized


def load_database_products(conn) -> Dict[int, Dict]:
    """Load all products from database that need prices"""
    print("Loading database products without prices...")

    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sku, name, description, category, brand
        FROM products
        WHERE price IS NULL OR price = 0
        ORDER BY id
    """)

    products = {}
    for row in cursor.fetchall():
        product_id, sku, name, description, category, brand = row

        # Combine name and description for better matching
        search_text = name or ""
        if description:
            search_text += " " + description

        products[product_id] = {
            'id': product_id,
            'sku': sku,
            'name': name,
            'description': description,
            'category': category,
            'brand': brand,
            'search_text': normalize_name(search_text)
        }

    cursor.close()
    print(f"  Loaded {len(products):,} products needing prices")
    return products


def load_erp_csv() -> List[Dict]:
    """Load ERP products from CSV"""
    print(f"\nLoading ERP CSV: {ERP_CSV_FILE}...")

    erp_products = []
    with open(ERP_CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            erp_products.append({
                'sku': row['sku'],
                'name': row['name'],
                'brand': row.get('brand', ''),
                'price': float(row['price']),
                'search_text': normalize_name(row['name'])
            })

    print(f"  Loaded {len(erp_products):,} ERP products")
    return erp_products


def find_fuzzy_matches(db_products: Dict, erp_products: List[Dict],
                       threshold: int = 80) -> List[Dict]:
    """
    Find fuzzy matches between database and ERP products

    Args:
        db_products: Database products dictionary
        erp_products: ERP products list
        threshold: Minimum similarity score (0-100)

    Returns:
        List of matches with similarity scores
    """
    print(f"\nPerforming fuzzy matching (threshold: {threshold})...")
    print("This may take a few minutes...\n")

    matches = []

    # Create lookup dictionary for faster searching
    erp_lookup = {p['search_text']: p for p in erp_products}
    erp_names = list(erp_lookup.keys())

    processed = 0
    for db_id, db_product in db_products.items():
        processed += 1

        if processed % 1000 == 0:
            print(f"  Processed {processed:,}/{len(db_products):,} products... ({len(matches)} matches found)")

        # Find best match using fuzzy string matching
        result = process.extractOne(
            db_product['search_text'],
            erp_names,
            scorer=fuzz.token_sort_ratio
        )

        if result:
            matched_name, score, _ = result

            if score >= threshold:
                erp_product = erp_lookup[matched_name]

                matches.append({
                    'db_id': db_id,
                    'db_sku': db_product['sku'],
                    'db_name': db_product['name'],
                    'db_category': db_product['category'],
                    'erp_sku': erp_product['sku'],
                    'erp_name': erp_product['name'],
                    'erp_price': erp_product['price'],
                    'similarity_score': score,
                    'db_search_text': db_product['search_text'],
                    'erp_search_text': erp_product['search_text']
                })

    print(f"\n  Total matches found: {len(matches):,}")
    return matches


def analyze_matches(matches: List[Dict]) -> None:
    """Analyze and display match statistics"""
    if not matches:
        print("\n[ERROR] No matches found!")
        return

    print("\n" + "=" * 80)
    print("FUZZY MATCHING ANALYSIS")
    print("=" * 80)

    # Score distribution
    score_ranges = {
        '95-100 (Excellent)': 0,
        '90-94 (Very Good)': 0,
        '85-89 (Good)': 0,
        '80-84 (Fair)': 0
    }

    for match in matches:
        score = match['similarity_score']
        if score >= 95:
            score_ranges['95-100 (Excellent)'] += 1
        elif score >= 90:
            score_ranges['90-94 (Very Good)'] += 1
        elif score >= 85:
            score_ranges['85-89 (Good)'] += 1
        else:
            score_ranges['80-84 (Fair)'] += 1

    print("\nMatch Quality Distribution:")
    for range_name, count in score_ranges.items():
        percentage = (count / len(matches)) * 100 if matches else 0
        print(f"  {range_name}: {count:,} matches ({percentage:.1f}%)")

    # Top 10 best matches
    print("\nTop 10 Best Matches (Highest Similarity):")
    print("-" * 80)
    sorted_matches = sorted(matches, key=lambda x: x['similarity_score'], reverse=True)

    for i, match in enumerate(sorted_matches[:10], 1):
        print(f"\n{i}. Similarity: {match['similarity_score']:.0f}%")
        print(f"   DB:  {match['db_name']}")
        print(f"   ERP: {match['erp_name']}")
        print(f"   Price: ${match['erp_price']:.2f}")

    # Price statistics
    prices = [m['erp_price'] for m in matches]
    avg_price = sum(prices) / len(prices) if prices else 0
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0

    print("\n" + "=" * 80)
    print("PRICE STATISTICS")
    print("=" * 80)
    print(f"Total Matches: {len(matches):,}")
    print(f"Average Price: ${avg_price:.2f}")
    print(f"Price Range: ${min_price:.2f} - ${max_price:.2f}")
    print(f"Total Value: ${sum(prices):,.2f}")


def save_matches(matches: List[Dict], filename: str = 'fuzzy_match_results.json') -> None:
    """Save matches to JSON file for review"""
    print(f"\nSaving matches to {filename}...")

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)

    print(f"  [OK] Saved {len(matches):,} matches")


def save_high_confidence_matches(matches: List[Dict], threshold: int = 90) -> str:
    """Save high-confidence matches to CSV for easy import"""
    high_confidence = [m for m in matches if m['similarity_score'] >= threshold]

    if not high_confidence:
        print(f"\n[WARNING] No matches with confidence >= {threshold}%")
        return None

    filename = f'high_confidence_matches_{threshold}plus.csv'
    print(f"\nSaving {len(high_confidence):,} high-confidence matches to {filename}...")

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'db_id', 'db_sku', 'db_name', 'erp_sku', 'erp_name',
            'erp_price', 'similarity_score'
        ])
        writer.writeheader()
        writer.writerows(high_confidence)

    print(f"  [OK] Saved high-confidence matches")
    return filename


def update_database_with_matches(conn, matches: List[Dict],
                                 min_confidence: int = 90,
                                 dry_run: bool = True) -> int:
    """
    Update database with matched prices

    Args:
        conn: Database connection
        matches: List of matches
        min_confidence: Minimum similarity score to update (0-100)
        dry_run: If True, don't actually update, just report what would happen

    Returns:
        Number of products updated
    """
    high_confidence = [m for m in matches if m['similarity_score'] >= min_confidence]

    if not high_confidence:
        print(f"\n[WARNING] No matches with confidence >= {min_confidence}%")
        return 0

    print("\n" + "=" * 80)
    if dry_run:
        print(f"DRY RUN: Would update {len(high_confidence):,} products")
    else:
        print(f"UPDATING {len(high_confidence):,} products in database...")
    print("=" * 80)

    if dry_run:
        print("\nSample updates that would be performed:")
        for i, match in enumerate(high_confidence[:5], 1):
            print(f"\n{i}. Product ID {match['db_id']}: {match['db_name']}")
            print(f"   Would set price: ${match['erp_price']:.2f}")
            print(f"   Based on ERP: {match['erp_name']} ({match['similarity_score']:.0f}% match)")

        print(f"\n... and {len(high_confidence) - 5} more")
        print("\n[WARNING] This was a DRY RUN - no changes made to database")
        return 0

    # Actual update
    cursor = conn.cursor()
    updated_count = 0

    for match in high_confidence:
        try:
            cursor.execute("""
                UPDATE products
                SET price = %s,
                    currency = 'SGD',
                    updated_at = NOW()
                WHERE id = %s
            """, (match['erp_price'], match['db_id']))

            updated_count += cursor.rowcount

        except Exception as e:
            print(f"  [WARNING] Error updating product {match['db_id']}: {e}")

    conn.commit()
    cursor.close()

    print(f"\n[OK] Updated {updated_count:,} products in database")
    return updated_count


def main():
    """Main execution function"""
    print("=" * 80)
    print("FUZZY MATCHING: ERP CSV TO DATABASE PRODUCTS")
    print("=" * 80)
    print("\nThis script will attempt to match ERP products to database products")
    print("by comparing product names and descriptions using fuzzy string matching.")
    print()

    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("  [OK] Connected")

    try:
        # Load data
        db_products = load_database_products(conn)
        erp_products = load_erp_csv()

        # Perform fuzzy matching with different thresholds
        print("\n" + "=" * 80)
        print("TESTING DIFFERENT SIMILARITY THRESHOLDS")
        print("=" * 80)

        for threshold in [90, 85, 80, 75]:
            matches = find_fuzzy_matches(db_products, erp_products, threshold=threshold)
            print(f"\nThreshold {threshold}%: Found {len(matches):,} matches")

        # Use 80% threshold for detailed analysis
        print("\n" + "=" * 80)
        print("DETAILED ANALYSIS WITH 80% THRESHOLD")
        print("=" * 80)

        matches = find_fuzzy_matches(db_products, erp_products, threshold=80)

        if matches:
            # Analyze matches
            analyze_matches(matches)

            # Save results
            save_matches(matches)
            save_high_confidence_matches(matches, threshold=90)

            # Ask about updating database
            print("\n" + "=" * 80)
            print("DATABASE UPDATE OPTIONS")
            print("=" * 80)

            # Dry run first
            print("\nPerforming dry run with 90% confidence threshold...")
            update_database_with_matches(conn, matches, min_confidence=90, dry_run=True)

            print("\n" + "=" * 80)
            print("To actually update the database, run this script with --apply flag:")
            print("  python fuzzy_match_erp_to_database.py --apply")
            print("=" * 80)

        else:
            print("\n[ERROR] No fuzzy matches found between ERP and database products")
            print("   This suggests the product catalogs are truly different.")

    finally:
        conn.close()
        print("\n[OK] Database connection closed")


if __name__ == '__main__':
    import sys

    # Check for --apply flag
    if '--apply' in sys.argv:
        print("\n[WARNING] RUNNING IN APPLY MODE - WILL UPDATE DATABASE")
        input("Press Enter to continue or Ctrl+C to cancel...")

        conn = psycopg2.connect(**DB_CONFIG)
        try:
            db_products = load_database_products(conn)
            erp_products = load_erp_csv()
            matches = find_fuzzy_matches(db_products, erp_products, threshold=80)

            if matches:
                update_database_with_matches(conn, matches, min_confidence=90, dry_run=False)
        finally:
            conn.close()
    else:
        main()
