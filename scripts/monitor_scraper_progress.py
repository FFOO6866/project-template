"""
Monitor Scraper Progress
Quick script to check how many products have been scraped
"""
import csv
import json
from pathlib import Path
import time

CSV_FILE = 'scraped_products_all_categories.csv'
CHECKPOINT_FILE = 'comprehensive_scraping_checkpoint.json'
STATS_FILE = 'scraping_stats.json'

def main():
    print("="*80)
    print("SCRAPER PROGRESS MONITOR")
    print("="*80)
    print()

    # Check CSV
    csv_path = Path(CSV_FILE)
    if csv_path.exists():
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            products = list(reader)

        # Filter out empty rows
        valid_products = [p for p in products if p.get('name') and p.get('price')]

        print(f"Products Scraped: {len(valid_products)}")
        print(f"CSV File Size: {csv_path.stat().st_size:,} bytes")

        if valid_products:
            # Show sample products
            print(f"\nLast 5 Products Scraped:")
            for i, product in enumerate(valid_products[-5:], 1):
                print(f"{i}. {product['name'][:60]}")
                print(f"   Price: ${product['price']} | Category: {product['category']}")

            # Count by category
            categories = {}
            for p in valid_products:
                cat = p['category'] or 'Unknown'
                categories[cat] = categories.get(cat, 0) + 1

            print(f"\nProducts by Category:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"  {cat}: {count}")

    else:
        print("CSV file not found yet")

    # Check checkpoint
    print()
    checkpoint_path = Path(CHECKPOINT_FILE)
    if checkpoint_path.exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            checkpoint = json.load(f)

        print(f"Checkpoint Status:")
        print(f"  Last Category Index: {checkpoint.get('last_category_index', 0)}")
        print(f"  Products Scraped: {checkpoint.get('products_scraped', 0)}")
        print(f"  Last Updated: {time.ctime(checkpoint.get('timestamp', 0))}")
    else:
        print("No checkpoint file yet (scraper still starting)")

    # Check stats
    print()
    stats_path = Path(STATS_FILE)
    if stats_path.exists():
        with open(STATS_FILE, 'r') as f:
            stats = json.load(f)

        print(f"Final Stats:")
        print(f"  Categories Completed: {stats.get('categories_completed', 0)}/5")
        print(f"  Subcategories Completed: {stats.get('subcategories_completed', 0)}")
        print(f"  Duration: {stats.get('duration_minutes', 0):.1f} minutes")
    else:
        print("Scraper still in progress (no final stats yet)")

    print()
    print("="*80)


if __name__ == '__main__':
    main()
