"""
Test Database-Loaded Category and Task Keywords

This script tests that the hybrid recommendation engine correctly loads
category and task keywords from PostgreSQL and fails fast when data is missing.

Usage:
    # Test with data loaded
    python scripts/test_database_keyword_loading.py

    # Test fail-fast behavior (requires manual database clearing)
    python scripts/test_database_keyword_loading.py --test-fail-fast

Requirements:
    - PostgreSQL database running with unified schema
    - Category and task mappings loaded (run load_category_task_mappings.py first)
"""

import os
import sys
import logging
import argparse

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.postgresql_database import get_database
from src.ai.hybrid_recommendation_engine import HybridRecommendationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Test Functions
# =============================================================================

def test_category_keyword_loading():
    """Test that category keywords load from database correctly"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Category Keyword Loading from Database")
    logger.info("="*80)

    try:
        database = get_database()
        engine = HybridRecommendationEngine(database=database)

        # Access category keywords (triggers lazy loading)
        categories = engine._extract_categories_from_requirements([
            "Need LED lighting for warehouse",
            "Safety equipment for construction",
            "Power tools and drills required"
        ])

        logger.info(f"✅ Successfully extracted categories: {categories}")

        # Verify category keywords were loaded
        if engine._category_keywords is None:
            logger.error("❌ Category keywords were not loaded")
            return False

        logger.info(f"Loaded category mappings: {list(engine._category_keywords.keys())}")

        # Verify expected categories were extracted
        expected_categories = {'lighting', 'safety', 'tools', 'power'}
        if not expected_categories.issubset(set(categories)):
            logger.warning(f"Expected categories {expected_categories}, got {set(categories)}")

        logger.info("✅ TEST 1 PASSED: Category keywords loaded from database\n")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {e}\n", exc_info=True)
        return False


def test_task_keyword_loading():
    """Test that task keywords load from database correctly"""
    logger.info("="*80)
    logger.info("TEST 2: Task Keyword Loading from Database")
    logger.info("="*80)

    try:
        database = get_database()
        engine = HybridRecommendationEngine(database=database)

        # Access task keywords (triggers lazy loading)
        tasks = engine._extract_tasks_from_requirements([
            "Need to drill holes in concrete",
            "Paint the walls",
            "Install lighting fixtures",
            "Measure dimensions accurately"
        ])

        logger.info(f"✅ Successfully extracted tasks: {tasks}")

        # Verify task keywords were loaded
        if engine._task_keywords is None:
            logger.error("❌ Task keywords were not loaded")
            return False

        logger.info(f"Loaded task mappings: {list(engine._task_keywords.keys())}")

        # Verify expected tasks were extracted
        expected_tasks = {'task_drill_hole', 'task_paint_surface', 'task_install_lighting', 'task_measure_dimension'}
        if not expected_tasks.issubset(set(tasks)):
            logger.warning(f"Expected tasks {expected_tasks}, got {set(tasks)}")

        logger.info("✅ TEST 2 PASSED: Task keywords loaded from database\n")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {e}\n", exc_info=True)
        return False


def test_fail_fast_behavior():
    """Test that engine fails fast when database tables are empty"""
    logger.info("="*80)
    logger.info("TEST 3: Fail-Fast Behavior (Empty Database)")
    logger.info("="*80)

    database = get_database()

    # Check if tables are already empty
    with database.connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM category_keyword_mappings")
        category_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM task_keyword_mappings")
        task_count = cursor.fetchone()[0]

    if category_count > 0 or task_count > 0:
        logger.warning(
            "⚠️ TEST 3 SKIPPED: Tables contain data. "
            "To test fail-fast behavior, manually clear the tables and re-run."
        )
        logger.info("Commands to clear tables (CAUTION - USE ONLY IN TEST ENVIRONMENT):")
        logger.info("  DELETE FROM category_keyword_mappings;")
        logger.info("  DELETE FROM task_keyword_mappings;")
        return None

    # Test category keywords fail-fast
    try:
        engine = HybridRecommendationEngine(database=database)
        engine._extract_categories_from_requirements(["test requirement"])
        logger.error("❌ TEST 3 FAILED: Should have raised error for empty category_keyword_mappings")
        return False
    except (ValueError, RuntimeError) as e:
        if "category keyword mappings" in str(e).lower():
            logger.info(f"✅ Correctly failed fast for empty category mappings: {e}")
        else:
            logger.error(f"❌ Wrong error message: {e}")
            return False

    # Test task keywords fail-fast
    try:
        engine = HybridRecommendationEngine(database=database)
        engine._extract_tasks_from_requirements(["test requirement"])
        logger.error("❌ TEST 3 FAILED: Should have raised error for empty task_keyword_mappings")
        return False
    except (ValueError, RuntimeError) as e:
        if "task keyword mappings" in str(e).lower():
            logger.info(f"✅ Correctly failed fast for empty task mappings: {e}")
        else:
            logger.error(f"❌ Wrong error message: {e}")
            return False

    logger.info("✅ TEST 3 PASSED: Fail-fast behavior works correctly\n")
    return True


def test_database_data_integrity():
    """Verify database contains expected data"""
    logger.info("="*80)
    logger.info("TEST 4: Database Data Integrity")
    logger.info("="*80)

    try:
        database = get_database()

        # Check category mappings
        with database.connection.cursor() as cursor:
            cursor.execute("""
                SELECT category, COUNT(*) as keyword_count
                FROM category_keyword_mappings
                GROUP BY category
                ORDER BY category
            """)
            category_stats = cursor.fetchall()

            logger.info("Category keyword counts:")
            for category, count in category_stats:
                logger.info(f"  {category}: {count} keywords")

            # Check task mappings
            cursor.execute("""
                SELECT COUNT(*) as total_tasks,
                       COUNT(DISTINCT keyword) as unique_keywords,
                       COUNT(DISTINCT task_id) as unique_task_ids
                FROM task_keyword_mappings
            """)
            task_stats = cursor.fetchone()
            logger.info(f"\nTask keyword statistics:")
            logger.info(f"  Total mappings: {task_stats[0]}")
            logger.info(f"  Unique keywords: {task_stats[1]}")
            logger.info(f"  Unique task IDs: {task_stats[2]}")

            # Verify minimum data requirements
            if len(category_stats) < 3:
                logger.warning("⚠️ Less than 3 categories found")

            if task_stats[0] < 5:
                logger.warning("⚠️ Less than 5 task mappings found")

        logger.info("✅ TEST 4 PASSED: Database data integrity verified\n")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 4 FAILED: {e}\n", exc_info=True)
        return False


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main test execution"""
    parser = argparse.ArgumentParser(description='Test database-loaded keyword mappings')
    parser.add_argument(
        '--test-fail-fast',
        action='store_true',
        help='Test fail-fast behavior (requires empty database tables)'
    )
    args = parser.parse_args()

    logger.info("="*80)
    logger.info("Database Keyword Loading Test Suite")
    logger.info("="*80)

    # Check required environment variables
    required_vars = ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    # Run tests
    results = {}

    # Test 1: Category keyword loading
    results['category_loading'] = test_category_keyword_loading()

    # Test 2: Task keyword loading
    results['task_loading'] = test_task_keyword_loading()

    # Test 3: Fail-fast behavior (only if requested)
    if args.test_fail_fast:
        results['fail_fast'] = test_fail_fast_behavior()
    else:
        logger.info("="*80)
        logger.info("TEST 3: Fail-Fast Behavior - SKIPPED")
        logger.info("Run with --test-fail-fast to test fail-fast behavior")
        logger.info("="*80 + "\n")

    # Test 4: Database data integrity
    results['data_integrity'] = test_database_data_integrity()

    # Summary
    logger.info("="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)

    passed = sum(1 for result in results.values() if result is True)
    failed = sum(1 for result in results.values() if result is False)
    skipped = sum(1 for result in results.values() if result is None)

    for test_name, result in results.items():
        status = "✅ PASSED" if result is True else "❌ FAILED" if result is False else "⚠️ SKIPPED"
        logger.info(f"{test_name}: {status}")

    logger.info("="*80)
    logger.info(f"Total: {passed} passed, {failed} failed, {skipped} skipped")

    if failed > 0:
        logger.error("❌ SOME TESTS FAILED")
        sys.exit(1)
    else:
        logger.info("✅ ALL TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
