#!/usr/bin/env python3
"""Load UNSPSC and ETIM classification data into PostgreSQL database.

This script loads real classification data from official sources:
- UNSPSC codes from purchased CSV files (unspsc.org - $500 USD)
- ETIM classes from member CSV/API (etim-international.com)

IMPORTANT: NO mock data. This script FAILS if data sources are not available.

Usage:
    # Load UNSPSC data (requires purchased CSV):
    python scripts/load_classification_data.py --unspsc-csv /path/to/UNSPSC_v24.csv

    # Load ETIM data (requires member CSV):
    python scripts/load_classification_data.py --etim-csv /path/to/etim_classes_9.0.csv

    # Load both:
    python scripts/load_classification_data.py \\
        --unspsc-csv /path/to/UNSPSC_v24.csv \\
        --etim-csv /path/to/etim_classes_9.0.csv

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
    UNSPSC_CSV_PATH: Default path to UNSPSC CSV
    ETIM_CSV_PATH: Default path to ETIM CSV
    ETIM_API_KEY: ETIM API key (alternative to CSV)

Data Source Acquisition:
    UNSPSC:
    - Purchase: https://www.unspsc.org/purchase-unspsc
    - Cost: ~$500 USD for commercial license
    - Format: Excel/CSV with full code hierarchy

    ETIM:
    - Membership: https://www.etim-international.com/become-a-member/
    - Portal: https://portal.etim-international.com/
    - Format: CSV/XML exports or API access
"""

import os
import sys
import argparse
import logging
from typing import List, Optional
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import psycopg2
from psycopg2.extras import execute_batch

from src.integrations.unspsc_client import UNSPSCClient, UNSPSCCode
from src.integrations.etim_client import ETIMClient, ETIMClass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClassificationDataLoader:
    """Loads classification data into PostgreSQL database."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize data loader.

        Args:
            database_url: PostgreSQL connection string (or use DATABASE_URL env var)
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError(
                "Database URL not provided. "
                "Set DATABASE_URL environment variable or pass database_url parameter."
            )

        self.conn = None
        self.unspsc_client = UNSPSCClient()
        self.etim_client = ETIMClient()

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(self.database_url)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def create_tables(self):
        """Create classification tables if they don't exist.

        IMPORTANT: This should match the schema in init-scripts/unified-postgresql-schema.sql
        """
        create_sql = """
        -- UNSPSC Codes Table
        CREATE TABLE IF NOT EXISTS unspsc_codes (
            id SERIAL PRIMARY KEY,
            code VARCHAR(8) UNIQUE NOT NULL,
            segment VARCHAR(255),
            family VARCHAR(255),
            class VARCHAR(255),
            commodity VARCHAR(255),
            title VARCHAR(500) NOT NULL,
            definition TEXT,
            level INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_unspsc_code ON unspsc_codes(code);
        CREATE INDEX IF NOT EXISTS idx_unspsc_level ON unspsc_codes(level);
        CREATE INDEX IF NOT EXISTS idx_unspsc_title ON unspsc_codes USING gin(to_tsvector('english', title));

        -- ETIM Classes Table
        CREATE TABLE IF NOT EXISTS etim_classes (
            id SERIAL PRIMARY KEY,
            class_code VARCHAR(8) UNIQUE NOT NULL,
            version VARCHAR(10) NOT NULL,
            description_en VARCHAR(500) NOT NULL,
            description_de VARCHAR(500),
            description_fr VARCHAR(500),
            description_nl VARCHAR(500),
            parent_class VARCHAR(8),
            features JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_class) REFERENCES etim_classes(class_code) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_etim_class_code ON etim_classes(class_code);
        CREATE INDEX IF NOT EXISTS idx_etim_version ON etim_classes(version);
        CREATE INDEX IF NOT EXISTS idx_etim_parent ON etim_classes(parent_class);
        CREATE INDEX IF NOT EXISTS idx_etim_description ON etim_classes USING gin(to_tsvector('english', description_en));

        -- Product Classifications Table
        CREATE TABLE IF NOT EXISTS product_classifications (
            id SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL,
            unspsc_code VARCHAR(8),
            etim_class VARCHAR(8),
            confidence DECIMAL(3, 2),
            classification_method VARCHAR(50),
            classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            classified_by VARCHAR(100),
            FOREIGN KEY (unspsc_code) REFERENCES unspsc_codes(code) ON DELETE SET NULL,
            FOREIGN KEY (etim_class) REFERENCES etim_classes(class_code) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_product_classifications_product ON product_classifications(product_id);
        CREATE INDEX IF NOT EXISTS idx_product_classifications_unspsc ON product_classifications(unspsc_code);
        CREATE INDEX IF NOT EXISTS idx_product_classifications_etim ON product_classifications(etim_class);
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(create_sql)
                self.conn.commit()
                logger.info("Classification tables created successfully")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create tables: {e}")
            raise

    def load_unspsc_data(self, csv_path: str) -> int:
        """Load UNSPSC codes from CSV file.

        Args:
            csv_path: Path to UNSPSC CSV file (purchased from unspsc.org)

        Returns:
            Number of codes loaded

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        logger.info(f"Loading UNSPSC data from {csv_path}...")

        # Import codes from CSV
        codes = self.unspsc_client.import_from_csv(csv_path)

        if not codes:
            raise ValueError(f"No UNSPSC codes found in {csv_path}")

        # Prepare batch insert
        insert_sql = """
        INSERT INTO unspsc_codes (code, segment, family, class, commodity, title, definition, level)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (code) DO UPDATE SET
            segment = EXCLUDED.segment,
            family = EXCLUDED.family,
            class = EXCLUDED.class,
            commodity = EXCLUDED.commodity,
            title = EXCLUDED.title,
            definition = EXCLUDED.definition,
            level = EXCLUDED.level,
            updated_at = CURRENT_TIMESTAMP
        """

        # Convert to tuples for batch insert
        data = [
            (
                code.code,
                code.segment,
                code.family,
                code.class_code,
                code.commodity,
                code.title,
                code.definition,
                code.level
            )
            for code in codes
        ]

        try:
            with self.conn.cursor() as cursor:
                execute_batch(cursor, insert_sql, data, page_size=1000)
                self.conn.commit()
                logger.info(f"Successfully loaded {len(codes)} UNSPSC codes")
                return len(codes)
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to load UNSPSC data: {e}")
            raise

    def load_etim_data(self, csv_path: Optional[str] = None, use_api: bool = False) -> int:
        """Load ETIM classes from CSV file or API.

        Args:
            csv_path: Path to ETIM CSV file (member export)
            use_api: Use ETIM API instead of CSV (requires API key)

        Returns:
            Number of classes loaded

        Raises:
            ValueError: If neither CSV nor API is available
        """
        if use_api:
            logger.info("Loading ETIM data from API...")
            if not self.etim_client.check_authentication():
                raise ValueError(
                    "ETIM API key not configured. "
                    "Set ETIM_API_KEY environment variable or provide CSV file."
                )
            classes = self.etim_client.get_classes(version="9.0")
        elif csv_path:
            logger.info(f"Loading ETIM data from {csv_path}...")
            classes = self.etim_client.import_from_csv(csv_path)
        else:
            raise ValueError(
                "No ETIM data source provided. "
                "Provide --etim-csv path or set ETIM_API_KEY for API access."
            )

        if not classes:
            raise ValueError("No ETIM classes found")

        # Prepare batch insert
        insert_sql = """
        INSERT INTO etim_classes (
            class_code, version, description_en, description_de,
            description_fr, description_nl, parent_class, features
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (class_code) DO UPDATE SET
            version = EXCLUDED.version,
            description_en = EXCLUDED.description_en,
            description_de = EXCLUDED.description_de,
            description_fr = EXCLUDED.description_fr,
            description_nl = EXCLUDED.description_nl,
            parent_class = EXCLUDED.parent_class,
            features = EXCLUDED.features,
            updated_at = CURRENT_TIMESTAMP
        """

        # Convert to tuples for batch insert
        import json
        data = [
            (
                cls.class_code,
                cls.version,
                cls.description_en,
                cls.description_de,
                cls.description_fr,
                cls.description_nl,
                cls.parent_class,
                json.dumps(cls.features) if cls.features else None
            )
            for cls in classes
        ]

        try:
            with self.conn.cursor() as cursor:
                execute_batch(cursor, insert_sql, data, page_size=1000)
                self.conn.commit()
                logger.info(f"Successfully loaded {len(classes)} ETIM classes")
                return len(classes)
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to load ETIM data: {e}")
            raise

    def validate_data(self) -> dict:
        """Validate loaded classification data.

        Returns:
            Dictionary with validation statistics
        """
        stats = {
            'unspsc_count': 0,
            'etim_count': 0,
            'unspsc_segments': 0,
            'unspsc_families': 0,
            'unspsc_classes': 0,
            'unspsc_commodities': 0,
            'etim_top_level': 0,
            'etim_with_parent': 0
        }

        try:
            with self.conn.cursor() as cursor:
                # Count UNSPSC codes
                cursor.execute("SELECT COUNT(*) FROM unspsc_codes")
                stats['unspsc_count'] = cursor.fetchone()[0]

                # Count by level
                cursor.execute("SELECT COUNT(*) FROM unspsc_codes WHERE level = 1")
                stats['unspsc_segments'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM unspsc_codes WHERE level = 2")
                stats['unspsc_families'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM unspsc_codes WHERE level = 3")
                stats['unspsc_classes'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM unspsc_codes WHERE level = 4")
                stats['unspsc_commodities'] = cursor.fetchone()[0]

                # Count ETIM classes
                cursor.execute("SELECT COUNT(*) FROM etim_classes")
                stats['etim_count'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM etim_classes WHERE parent_class IS NULL")
                stats['etim_top_level'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM etim_classes WHERE parent_class IS NOT NULL")
                stats['etim_with_parent'] = cursor.fetchone()[0]

            logger.info("Validation Statistics:")
            logger.info(f"  UNSPSC Codes: {stats['unspsc_count']}")
            logger.info(f"    - Segments: {stats['unspsc_segments']}")
            logger.info(f"    - Families: {stats['unspsc_families']}")
            logger.info(f"    - Classes: {stats['unspsc_classes']}")
            logger.info(f"    - Commodities: {stats['unspsc_commodities']}")
            logger.info(f"  ETIM Classes: {stats['etim_count']}")
            logger.info(f"    - Top Level: {stats['etim_top_level']}")
            logger.info(f"    - With Parent: {stats['etim_with_parent']}")

            return stats

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise


def main():
    """Main entry point for classification data loading."""
    parser = argparse.ArgumentParser(
        description='Load UNSPSC and ETIM classification data into PostgreSQL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Data Source Information:
  UNSPSC: Purchase from https://www.unspsc.org/purchase-unspsc (~$500 USD)
  ETIM:   Membership required at https://www.etim-international.com/

Examples:
  # Load UNSPSC data only:
  python scripts/load_classification_data.py --unspsc-csv UNSPSC_v24.csv

  # Load ETIM data only:
  python scripts/load_classification_data.py --etim-csv etim_classes_9.0.csv

  # Load both:
  python scripts/load_classification_data.py \\
      --unspsc-csv UNSPSC_v24.csv \\
      --etim-csv etim_classes_9.0.csv

  # Use ETIM API instead of CSV:
  export ETIM_API_KEY="your_api_key"
  python scripts/load_classification_data.py --etim-api
        """
    )

    parser.add_argument(
        '--database-url',
        help='PostgreSQL connection string (or use DATABASE_URL env var)'
    )
    parser.add_argument(
        '--unspsc-csv',
        help='Path to UNSPSC CSV file (purchased from unspsc.org)'
    )
    parser.add_argument(
        '--etim-csv',
        help='Path to ETIM CSV file (member export)'
    )
    parser.add_argument(
        '--etim-api',
        action='store_true',
        help='Use ETIM API instead of CSV (requires ETIM_API_KEY)'
    )
    parser.add_argument(
        '--create-tables',
        action='store_true',
        default=True,
        help='Create tables if they don\'t exist (default: True)'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        default=True,
        help='Validate data after loading (default: True)'
    )

    args = parser.parse_args()

    # Check if any data source is provided
    if not args.unspsc_csv and not args.etim_csv and not args.etim_api:
        parser.error(
            "No data source provided. Specify --unspsc-csv, --etim-csv, or --etim-api.\n"
            "See --help for examples and data acquisition information."
        )

    try:
        # Initialize loader
        loader = ClassificationDataLoader(database_url=args.database_url)
        loader.connect()

        # Create tables
        if args.create_tables:
            loader.create_tables()

        # Load UNSPSC data
        if args.unspsc_csv:
            unspsc_count = loader.load_unspsc_data(args.unspsc_csv)
            logger.info(f"✓ Loaded {unspsc_count} UNSPSC codes")

        # Load ETIM data
        if args.etim_csv or args.etim_api:
            etim_count = loader.load_etim_data(
                csv_path=args.etim_csv,
                use_api=args.etim_api
            )
            logger.info(f"✓ Loaded {etim_count} ETIM classes")

        # Validate data
        if args.validate:
            stats = loader.validate_data()
            logger.info("✓ Data validation completed")

        logger.info("Classification data loading completed successfully!")

    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        logger.error("Please ensure you have purchased/downloaded the required data files:")
        logger.error("  UNSPSC: https://www.unspsc.org/purchase-unspsc")
        logger.error("  ETIM: https://portal.etim-international.com/")
        sys.exit(1)

    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        if 'loader' in locals():
            loader.close()


if __name__ == '__main__':
    main()
