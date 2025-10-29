"""
Load Category and Task Keyword Mappings to PostgreSQL

This script loads hardcoded category and task keyword dictionaries from
hybrid_recommendation_engine.py into PostgreSQL tables for production use.

Usage:
    python scripts/load_category_task_mappings.py

Requirements:
    - PostgreSQL database running with unified schema
    - POSTGRES_* environment variables configured
"""

import os
import sys
import logging
from typing import Dict, List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.postgresql_database import get_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# REFERENCE DATA - Extracted from hybrid_recommendation_engine.py
# =============================================================================

# Category keyword mappings (from lines 949-955)
CATEGORY_KEYWORDS = {
    'lighting': ['light', 'led', 'lamp', 'fixture'],
    'safety': ['safety', 'ppe', 'protection', 'helmet'],
    'tools': ['drill', 'saw', 'hammer', 'tool'],
    'power': ['power', 'supply', 'battery', 'electrical'],
    'networking': ['network', 'ethernet', 'cable', 'wifi']
}

# Task keyword mappings (from lines 687-696)
TASK_KEYWORDS = {
    'drill': 'task_drill_hole',
    'paint': 'task_paint_surface',
    'install': 'task_install_fixture',
    'cut': 'task_cut_material',
    'measure': 'task_measure_dimension',
    'secure': 'task_secure_fastener',
    'lighting': 'task_install_lighting',
    'safety': 'task_safety_compliance'
}


# =============================================================================
# Data Loading Functions
# =============================================================================

def load_category_keywords(database) -> int:
    """
    Load category keyword mappings to PostgreSQL

    Returns:
        Number of records inserted
    """
    logger.info("Loading category keyword mappings...")

    # Clear existing data
    with database.connection.cursor() as cursor:
        cursor.execute("DELETE FROM category_keyword_mappings")
        database.connection.commit()
        logger.info("Cleared existing category keyword mappings")

    # Insert new data
    insert_query = """
        INSERT INTO category_keyword_mappings (category, keyword, priority)
        VALUES (%s, %s, %s)
        ON CONFLICT (category, keyword) DO NOTHING
    """

    records = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            # Priority 1 is default (all equal weight for now)
            records.append((category, keyword, 1))

    with database.connection.cursor() as cursor:
        cursor.executemany(insert_query, records)
        database.connection.commit()
        inserted_count = cursor.rowcount

    logger.info(f"✅ Inserted {inserted_count} category keyword mappings")
    return inserted_count


def load_task_keywords(database) -> int:
    """
    Load task keyword mappings to PostgreSQL

    Returns:
        Number of records inserted
    """
    logger.info("Loading task keyword mappings...")

    # Clear existing data
    with database.connection.cursor() as cursor:
        cursor.execute("DELETE FROM task_keyword_mappings")
        database.connection.commit()
        logger.info("Cleared existing task keyword mappings")

    # Insert new data
    insert_query = """
        INSERT INTO task_keyword_mappings (keyword, task_id, priority)
        VALUES (%s, %s, %s)
        ON CONFLICT (keyword, task_id) DO NOTHING
    """

    records = []
    for keyword, task_id in TASK_KEYWORDS.items():
        # Priority 1 is default (all equal weight for now)
        records.append((keyword, task_id, 1))

    with database.connection.cursor() as cursor:
        cursor.executemany(insert_query, records)
        database.connection.commit()
        inserted_count = cursor.rowcount

    logger.info(f"✅ Inserted {inserted_count} task keyword mappings")
    return inserted_count


def verify_data_loaded(database) -> bool:
    """
    Verify that data was loaded correctly

    Returns:
        True if verification passed, False otherwise
    """
    logger.info("Verifying loaded data...")

    with database.connection.cursor() as cursor:
        # Check category keywords count
        cursor.execute("SELECT COUNT(*) FROM category_keyword_mappings")
        category_count = cursor.fetchone()[0]

        # Check task keywords count
        cursor.execute("SELECT COUNT(*) FROM task_keyword_mappings")
        task_count = cursor.fetchone()[0]

        logger.info(f"Category keyword mappings: {category_count}")
        logger.info(f"Task keyword mappings: {task_count}")

        # Verify expected counts
        expected_category_count = sum(len(keywords) for keywords in CATEGORY_KEYWORDS.values())
        expected_task_count = len(TASK_KEYWORDS)

        if category_count != expected_category_count:
            logger.error(
                f"Category count mismatch: expected {expected_category_count}, got {category_count}"
            )
            return False

        if task_count != expected_task_count:
            logger.error(
                f"Task count mismatch: expected {expected_task_count}, got {task_count}"
            )
            return False

    logger.info("✅ Data verification passed")
    return True


def display_loaded_data(database):
    """Display loaded data for review"""
    logger.info("\n" + "="*80)
    logger.info("LOADED CATEGORY KEYWORD MAPPINGS")
    logger.info("="*80)

    with database.connection.cursor() as cursor:
        cursor.execute("""
            SELECT category, ARRAY_AGG(keyword ORDER BY keyword) as keywords
            FROM category_keyword_mappings
            GROUP BY category
            ORDER BY category
        """)

        for category, keywords in cursor.fetchall():
            logger.info(f"{category:15} -> {', '.join(keywords)}")

    logger.info("\n" + "="*80)
    logger.info("LOADED TASK KEYWORD MAPPINGS")
    logger.info("="*80)

    with database.connection.cursor() as cursor:
        cursor.execute("""
            SELECT keyword, task_id
            FROM task_keyword_mappings
            ORDER BY keyword
        """)

        for keyword, task_id in cursor.fetchall():
            logger.info(f"{keyword:15} -> {task_id}")

    logger.info("="*80 + "\n")


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main execution function"""
    logger.info("="*80)
    logger.info("Category and Task Keyword Mappings Loader")
    logger.info("="*80)

    # Check required environment variables
    required_vars = ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Set these variables in .env.production or environment")
        sys.exit(1)

    try:
        # Connect to database
        logger.info("Connecting to PostgreSQL database...")
        database = get_database()
        logger.info("✅ Connected to database")

        # Verify tables exist
        with database.connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_name IN ('category_keyword_mappings', 'task_keyword_mappings')
            """)
            table_count = cursor.fetchone()[0]

            if table_count != 2:
                logger.error(
                    "Required tables not found in database. "
                    "Run unified-postgresql-schema.sql first."
                )
                sys.exit(1)

        # Load data
        category_count = load_category_keywords(database)
        task_count = load_task_keywords(database)

        # Verify data
        if not verify_data_loaded(database):
            logger.error("Data verification failed")
            sys.exit(1)

        # Display loaded data
        display_loaded_data(database)

        # Success summary
        logger.info("="*80)
        logger.info("✅ DATA LOADING COMPLETE")
        logger.info("="*80)
        logger.info(f"Category keyword mappings loaded: {category_count}")
        logger.info(f"Task keyword mappings loaded: {task_count}")
        logger.info("\nNext steps:")
        logger.info("1. Verify the loaded data above is correct")
        logger.info("2. Update hybrid_recommendation_engine.py to use database loading")
        logger.info("3. Test the recommendation engine with database-loaded mappings")
        logger.info("="*80)

    except Exception as e:
        logger.error(f"❌ Failed to load mappings: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
