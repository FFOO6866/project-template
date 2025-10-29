"""
Import ERP prices from CSV to database
"""
import csv
import psycopg2
from decimal import Decimal

# Database configuration
DATABASE_HOST = 'localhost'
DATABASE_PORT = '5434'
DATABASE_NAME = 'horme_db'
DATABASE_USER = 'horme_user'
DATABASE_PASSWORD = '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42'

# Statistics
stats = {
    'total_rows': 0,
    'updated': 0,
    'not_found': 0,
    'errors': 0
}

# Connect to database
conn = psycopg2.connect(
    host=DATABASE_HOST,
    port=DATABASE_PORT,
    database=DATABASE_NAME,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD
)

# Read CSV and update database
with open('erp_product_prices.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)

    with conn.cursor() as cur:
        for row in reader:
            stats['total_rows'] += 1

            try:
                sku = row['sku']
                price = Decimal(row['price'])

                # Update with CORRECTED schema (no enrichment_date)
                cur.execute("""
                    UPDATE products
                    SET price = %s,
                        currency = 'SGD',
                        updated_at = NOW()
                    WHERE sku = %s
                """, (float(price), sku))

                if cur.rowcount > 0:
                    stats['updated'] += 1
                else:
                    stats['not_found'] += 1

            except Exception as e:
                stats['errors'] += 1
                print(f"Error on row {stats['total_rows']}: {e}")

            # Progress update every 1000 rows
            if stats['total_rows'] % 1000 == 0:
                print(f"Processed {stats['total_rows']:,} rows...")
                conn.commit()  # Commit in batches

# Final commit
conn.commit()
conn.close()

# Final statistics
print("\n" + "="*60)
print("IMPORT COMPLETE")
print("="*60)
print(f"Total Rows:      {stats['total_rows']:,}")
print(f"Updated:         {stats['updated']:,}")
print(f"Not Found:       {stats['not_found']:,}")
print(f"Errors:          {stats['errors']}")
print("="*60)
