"""
Product Classification System using REAL UNSPSC and ETIM data

IMPORTANT: This module uses ONLY real classification data from PostgreSQL.
- NO mock data
- NO hardcoded translations
- NO fallbacks
- FAILS if classification data is not loaded

Data must be loaded using: python scripts/load_classification_data.py

Data Sources:
- UNSPSC: Purchase from https://www.unspsc.org/purchase-unspsc (~$500 USD)
- ETIM: Membership at https://www.etim-international.com/
"""

import os
import logging
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of product classification"""
    product_id: int
    product_sku: str
    product_name: str
    unspsc_code: Optional[str] = None
    unspsc_title: Optional[str] = None
    unspsc_confidence: float = 0.0
    etim_class: Optional[str] = None
    etim_description: Optional[str] = None
    etim_confidence: float = 0.0
    classification_method: str = "rule_based"
    classified_at: datetime = None

    def __post_init__(self):
        if self.classified_at is None:
            self.classified_at = datetime.now()


class ProductClassifier:
    """
    Product classifier using real UNSPSC and ETIM data from PostgreSQL.

    IMPORTANT: This class REQUIRES classification data to be loaded.
    If data is not found, classification will FAIL (no fallbacks).

    Usage:
        1. Load data first: python scripts/load_classification_data.py --unspsc-csv ...
        2. Initialize classifier: classifier = ProductClassifier()
        3. Classify products: result = classifier.classify_product(product_data)
    """

    def __init__(self, database_url: Optional[str] = None):
        """Initialize product classifier.

        Args:
            database_url: PostgreSQL connection string (or use DATABASE_URL env var)

        Raises:
            ValueError: If DATABASE_URL not configured
            RuntimeError: If database connection fails
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL not configured. "
                "Set DATABASE_URL environment variable. "
                "Example: postgresql://user:pass@localhost:5432/horme_db"
            )

        self.conn = None
        self._connect()
        self._verify_classification_data()

    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(self.database_url)
            logger.info("Connected to database for product classification")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise RuntimeError(
                f"Failed to connect to database. "
                f"Ensure PostgreSQL is running and DATABASE_URL is correct."
            )

    def _verify_classification_data(self):
        """Verify that classification data is loaded.

        Raises:
            RuntimeError: If classification data is not found
        """
        try:
            with self.conn.cursor() as cursor:
                # Check UNSPSC codes
                cursor.execute("SELECT COUNT(*) FROM unspsc_codes")
                unspsc_count = cursor.fetchone()[0]

                # Check ETIM classes
                cursor.execute("SELECT COUNT(*) FROM etim_classes")
                etim_count = cursor.fetchone()[0]

                logger.info(f"Found {unspsc_count} UNSPSC codes in database")
                logger.info(f"Found {etim_count} ETIM classes in database")

                if unspsc_count == 0 and etim_count == 0:
                    raise RuntimeError(
                        "CRITICAL: No classification data found in database.\n"
                        "Please load data using:\n"
                        "  python scripts/load_classification_data.py --unspsc-csv UNSPSC_v24.csv\n"
                        "\n"
                        "Data Sources:\n"
                        "  UNSPSC: https://www.unspsc.org/purchase-unspsc (~$500 USD)\n"
                        "  ETIM: https://portal.etim-international.com/ (membership required)"
                    )

        except psycopg2.errors.UndefinedTable as e:
            logger.error(f"Classification tables not found: {e}")
            raise RuntimeError(
                "Classification tables not found. "
                "Run database migrations first: "
                "init-scripts/unified-postgresql-schema.sql"
            )

    def classify_product(
        self,
        product_id: int,
        product_name: str,
        product_sku: str,
        product_description: Optional[str] = None,
        category: Optional[str] = None
    ) -> ClassificationResult:
        """Classify a product using UNSPSC and ETIM codes.

        This is a simple rule-based classification. For production, consider using
        AI/ML models for better accuracy.

        Args:
            product_id: Product ID
            product_name: Product name
            product_sku: Product SKU
            product_description: Product description (optional)
            category: Product category (optional)

        Returns:
            ClassificationResult with UNSPSC and ETIM classifications

        Raises:
            RuntimeError: If classification fails due to missing data
        """
        # Combine search text
        search_text = product_name
        if product_description:
            search_text = f"{product_name} {product_description}"
        if category:
            search_text = f"{search_text} {category}"

        search_text = search_text.lower()

        result = ClassificationResult(
            product_id=product_id,
            product_sku=product_sku,
            product_name=product_name
        )

        # Search UNSPSC codes
        unspsc_code, unspsc_title, unspsc_confidence = self._search_unspsc(search_text)
        if unspsc_code:
            result.unspsc_code = unspsc_code
            result.unspsc_title = unspsc_title
            result.unspsc_confidence = unspsc_confidence

        # Search ETIM classes
        etim_class, etim_description, etim_confidence = self._search_etim(search_text)
        if etim_class:
            result.etim_class = etim_class
            result.etim_description = etim_description
            result.etim_confidence = etim_confidence

        return result

    def _search_unspsc(self, search_text: str) -> Tuple[Optional[str], Optional[str], float]:
        """Search UNSPSC codes by text.

        Args:
            search_text: Text to search (product name + description)

        Returns:
            Tuple of (code, title, confidence)
        """
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # Use PostgreSQL full-text search
                query = """
                SELECT code, title,
                       ts_rank(to_tsvector('english', title), plainto_tsquery('english', %s)) AS rank
                FROM unspsc_codes
                WHERE to_tsvector('english', title) @@ plainto_tsquery('english', %s)
                ORDER BY rank DESC, level DESC
                LIMIT 1
                """
                cursor.execute(query, (search_text, search_text))
                row = cursor.fetchone()

                if row:
                    # Confidence based on rank (normalized to 0-1 range)
                    # ts_rank typically returns values between 0 and 1, but can be higher
                    confidence = min(row['rank'] / 0.1, 1.0)  # Normalize
                    return row['code'], row['title'], confidence

                return None, None, 0.0

        except Exception as e:
            logger.error(f"UNSPSC search failed: {e}")
            raise

    def _search_etim(self, search_text: str) -> Tuple[Optional[str], Optional[str], float]:
        """Search ETIM classes by text.

        Args:
            search_text: Text to search (product name + description)

        Returns:
            Tuple of (class_code, description, confidence)
        """
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # Use PostgreSQL full-text search on English description
                query = """
                SELECT class_code, description_en,
                       ts_rank(to_tsvector('english', description_en), plainto_tsquery('english', %s)) AS rank
                FROM etim_classes
                WHERE to_tsvector('english', description_en) @@ plainto_tsquery('english', %s)
                ORDER BY rank DESC
                LIMIT 1
                """
                cursor.execute(query, (search_text, search_text))
                row = cursor.fetchone()

                if row:
                    confidence = min(row['rank'] / 0.1, 1.0)  # Normalize
                    return row['class_code'], row['description_en'], confidence

                return None, None, 0.0

        except Exception as e:
            logger.error(f"ETIM search failed: {e}")
            raise

    def save_classification(self, result: ClassificationResult):
        """Save classification result to database.

        Args:
            result: Classification result to save
        """
        try:
            with self.conn.cursor() as cursor:
                insert_query = """
                INSERT INTO product_classifications (
                    product_id, unspsc_code, etim_class, confidence,
                    classification_method, classified_at, classified_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_id) DO UPDATE SET
                    unspsc_code = EXCLUDED.unspsc_code,
                    etim_class = EXCLUDED.etim_class,
                    confidence = EXCLUDED.confidence,
                    classification_method = EXCLUDED.classification_method,
                    classified_at = EXCLUDED.classified_at,
                    classified_by = EXCLUDED.classified_by
                """

                # Use average confidence if both classifications exist
                confidence = 0.0
                if result.unspsc_code and result.etim_class:
                    confidence = (result.unspsc_confidence + result.etim_confidence) / 2
                elif result.unspsc_code:
                    confidence = result.unspsc_confidence
                elif result.etim_class:
                    confidence = result.etim_confidence

                cursor.execute(
                    insert_query,
                    (
                        result.product_id,
                        result.unspsc_code,
                        result.etim_class,
                        confidence,
                        result.classification_method,
                        result.classified_at,
                        'ProductClassifier'
                    )
                )
                self.conn.commit()
                logger.info(f"Saved classification for product {result.product_id}")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to save classification: {e}")
            raise

    def get_unspsc_hierarchy(self, code: str) -> Dict[str, str]:
        """Get UNSPSC hierarchy for a given code.

        Args:
            code: UNSPSC code (8 digits)

        Returns:
            Dictionary with segment, family, class, commodity
        """
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                query = """
                SELECT segment, family, class, commodity, title
                FROM unspsc_codes
                WHERE code = %s
                """
                cursor.execute(query, (code,))
                row = cursor.fetchone()

                if row:
                    return {
                        'segment': row['segment'],
                        'family': row['family'],
                        'class': row['class'],
                        'commodity': row['commodity'],
                        'title': row['title']
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get UNSPSC hierarchy: {e}")
            raise

    def get_etim_features(self, class_code: str) -> Dict[str, any]:
        """Get ETIM features for a given class code.

        Args:
            class_code: ETIM class code (e.g., 'EC000001')

        Returns:
            Dictionary with ETIM features
        """
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                query = """
                SELECT class_code, version, description_en, features, parent_class
                FROM etim_classes
                WHERE class_code = %s
                """
                cursor.execute(query, (class_code,))
                row = cursor.fetchone()

                if row:
                    return {
                        'class_code': row['class_code'],
                        'version': row['version'],
                        'description': row['description_en'],
                        'features': row['features'],
                        'parent_class': row['parent_class']
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get ETIM features: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def get_product_classifier() -> ProductClassifier:
    """Factory function to get configured product classifier.

    Returns:
        Configured ProductClassifier instance

    Raises:
        ValueError: If DATABASE_URL not configured
        RuntimeError: If classification data not loaded
    """
    return ProductClassifier()


# Example usage
if __name__ == "__main__":
    print("""
Product Classifier Usage
========================

IMPORTANT: Classification data must be loaded first!

Step 1: Load Classification Data
--------------------------------
python scripts/load_classification_data.py --unspsc-csv UNSPSC_v24.csv

Data Sources:
  UNSPSC: https://www.unspsc.org/purchase-unspsc (~$500 USD)
  ETIM: https://portal.etim-international.com/ (membership required)

Step 2: Classify Products
-------------------------
from src.core.product_classifier import ProductClassifier

with ProductClassifier() as classifier:
    result = classifier.classify_product(
        product_id=1,
        product_name="Safety Glasses",
        product_sku="SG-001",
        product_description="ANSI Z87.1 certified safety glasses",
        category="PPE"
    )

    print(f"UNSPSC: {result.unspsc_code} - {result.unspsc_title}")
    print(f"ETIM: {result.etim_class} - {result.etim_description}")

    # Save classification to database
    classifier.save_classification(result)

For more information:
- UNSPSC: https://www.unspsc.org/
- ETIM: https://www.etim-international.com/
""")
