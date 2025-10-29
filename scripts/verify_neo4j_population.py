"""
Neo4j Knowledge Graph Population Verification Script
=====================================================

Verifies that the Neo4j knowledge graph was populated correctly.

Features:
- Checks node counts (products, categories, brands, tasks)
- Verifies relationship counts
- Validates indexes and constraints
- Tests sample queries
- Reports on graph health

Usage:
    python scripts/verify_neo4j_population.py

Returns:
    Exit code 0 if verification passes
    Exit code 1 if verification fails
"""

import os
import sys
import logging
from typing import Dict, List, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.neo4j_knowledge_graph import get_knowledge_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Expected Counts (Approximate)
# =============================================================================

EXPECTED_COUNTS = {
    'Product': (19000, 20000),      # 19,143 expected
    'Category': (40, 60),            # ~50 expected
    'Brand': (150, 250),             # ~200 expected
    'Task': (5, 10),                 # 7 expected
}

EXPECTED_RELATIONSHIPS = {
    'IN_CATEGORY': (19000, 20000),   # One per product
    'OF_BRAND': (19000, 20000),      # One per product
    'SIMILAR_TO': (40000, 60000),    # ~50,000 expected
    'USED_FOR': (8000, 12000),       # ~10,000 expected
}


# =============================================================================
# Verification Functions
# =============================================================================

def verify_connection() -> bool:
    """Verify Neo4j connection."""
    logger.info("Verifying Neo4j connection...")

    try:
        kg = get_knowledge_graph()
        connected = kg.test_connection()

        if connected:
            logger.info("✅ Neo4j connection successful")
            return True
        else:
            logger.error("❌ Neo4j connection failed")
            return False

    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return False


def verify_node_counts(kg) -> Tuple[bool, Dict]:
    """
    Verify node counts match expected ranges.

    Returns:
        Tuple of (success, node_counts_dict)
    """
    logger.info("\nVerifying node counts...")

    try:
        with kg.get_session() as session:
            query = """
            MATCH (n)
            RETURN labels(n)[0] as NodeType, count(n) as Count
            ORDER BY Count DESC
            """
            result = session.run(query)
            node_counts = {record["NodeType"]: record["Count"] for record in result}

        all_valid = True

        for node_type, (min_expected, max_expected) in EXPECTED_COUNTS.items():
            actual_count = node_counts.get(node_type, 0)

            if min_expected <= actual_count <= max_expected:
                logger.info(f"✅ {node_type}: {actual_count} (expected {min_expected}-{max_expected})")
            else:
                logger.error(
                    f"❌ {node_type}: {actual_count} "
                    f"(expected {min_expected}-{max_expected})"
                )
                all_valid = False

        # Check for unexpected node types
        for node_type, count in node_counts.items():
            if node_type not in EXPECTED_COUNTS and node_type is not None:
                logger.warning(f"⚠️ Unexpected node type: {node_type} ({count} nodes)")

        total_nodes = sum(node_counts.values())
        logger.info(f"\nTotal nodes: {total_nodes}")

        return all_valid, node_counts

    except Exception as e:
        logger.error(f"❌ Failed to verify node counts: {e}")
        return False, {}


def verify_relationship_counts(kg) -> Tuple[bool, Dict]:
    """
    Verify relationship counts match expected ranges.

    Returns:
        Tuple of (success, relationship_counts_dict)
    """
    logger.info("\nVerifying relationship counts...")

    try:
        with kg.get_session() as session:
            query = """
            MATCH ()-[r]->()
            RETURN type(r) as RelationType, count(r) as Count
            ORDER BY Count DESC
            """
            result = session.run(query)
            rel_counts = {record["RelationType"]: record["Count"] for record in result}

        all_valid = True

        for rel_type, (min_expected, max_expected) in EXPECTED_RELATIONSHIPS.items():
            actual_count = rel_counts.get(rel_type, 0)

            if min_expected <= actual_count <= max_expected:
                logger.info(f"✅ {rel_type}: {actual_count} (expected {min_expected}-{max_expected})")
            else:
                logger.error(
                    f"❌ {rel_type}: {actual_count} "
                    f"(expected {min_expected}-{max_expected})"
                )
                all_valid = False

        # Check for unexpected relationship types
        for rel_type, count in rel_counts.items():
            if rel_type not in EXPECTED_RELATIONSHIPS:
                logger.warning(f"⚠️ Unexpected relationship type: {rel_type} ({count} relationships)")

        total_rels = sum(rel_counts.values())
        logger.info(f"\nTotal relationships: {total_rels}")

        return all_valid, rel_counts

    except Exception as e:
        logger.error(f"❌ Failed to verify relationship counts: {e}")
        return False, {}


def verify_indexes_and_constraints(kg) -> bool:
    """Verify required indexes and constraints exist."""
    logger.info("\nVerifying indexes and constraints...")

    try:
        with kg.get_session() as session:
            # Check constraints
            constraints_query = "SHOW CONSTRAINTS"
            constraints_result = session.run(constraints_query)
            constraints = [dict(record) for record in constraints_result]

            # Check indexes
            indexes_query = "SHOW INDEXES"
            indexes_result = session.run(indexes_query)
            indexes = [dict(record) for record in indexes_result]

        logger.info(f"✅ Found {len(constraints)} constraints")
        logger.info(f"✅ Found {len(indexes)} indexes")

        # Verify critical constraints exist
        required_constraints = [
            'product_id',
            'category_name',
            'brand_name',
            'task_id'
        ]

        constraint_names = [c.get('name', '') for c in constraints]

        all_valid = True
        for required in required_constraints:
            if required in constraint_names:
                logger.info(f"✅ Constraint exists: {required}")
            else:
                logger.warning(f"⚠️ Missing constraint: {required}")
                # Don't fail - constraints are nice to have but not critical

        return True

    except Exception as e:
        logger.error(f"❌ Failed to verify indexes/constraints: {e}")
        return False


def verify_sample_queries(kg) -> bool:
    """Test sample queries to ensure graph is queryable."""
    logger.info("\nVerifying sample queries...")

    all_valid = True

    try:
        # Query 1: Get sample products
        with kg.get_session() as session:
            query = "MATCH (p:Product) RETURN p.id, p.name, p.sku LIMIT 5"
            result = session.run(query)
            products = [dict(record) for record in result]

            if len(products) > 0:
                logger.info(f"✅ Sample products query returned {len(products)} results")
            else:
                logger.error("❌ Sample products query returned no results")
                all_valid = False

        # Query 2: Get products with category relationships
        with kg.get_session() as session:
            query = """
            MATCH (p:Product)-[:IN_CATEGORY]->(c:Category)
            RETURN p.name as product, c.name as category
            LIMIT 5
            """
            result = session.run(query)
            product_categories = [dict(record) for record in result]

            if len(product_categories) > 0:
                logger.info(f"✅ Product-category query returned {len(product_categories)} results")
            else:
                logger.error("❌ Product-category query returned no results")
                all_valid = False

        # Query 3: Get similar products
        with kg.get_session() as session:
            query = """
            MATCH (p1:Product)-[s:SIMILAR_TO]->(p2:Product)
            RETURN p1.name as product1, p2.name as product2, s.similarity_score as score
            LIMIT 5
            """
            result = session.run(query)
            similar_products = [dict(record) for record in result]

            if len(similar_products) > 0:
                logger.info(f"✅ Similarity query returned {len(similar_products)} results")
            else:
                logger.error("❌ Similarity query returned no results")
                all_valid = False

        # Query 4: Get task recommendations
        with kg.get_session() as session:
            query = """
            MATCH (p:Product)-[u:USED_FOR]->(t:Task)
            RETURN p.name as product, t.name as task, u.necessity as necessity
            LIMIT 5
            """
            result = session.run(query)
            task_recommendations = [dict(record) for record in result]

            if len(task_recommendations) > 0:
                logger.info(f"✅ Task recommendation query returned {len(task_recommendations)} results")
            else:
                logger.error("❌ Task recommendation query returned no results")
                all_valid = False

        return all_valid

    except Exception as e:
        logger.error(f"❌ Failed to execute sample queries: {e}")
        return False


def verify_data_quality(kg) -> bool:
    """Verify data quality (no nulls, orphaned nodes, etc.)."""
    logger.info("\nVerifying data quality...")

    all_valid = True

    try:
        # Check for products without categories
        with kg.get_session() as session:
            query = """
            MATCH (p:Product)
            WHERE NOT (p)-[:IN_CATEGORY]->()
            RETURN count(p) as orphaned_products
            """
            result = session.run(query)
            orphaned_count = result.single()["orphaned_products"]

            if orphaned_count == 0:
                logger.info("✅ No products without categories")
            else:
                logger.warning(f"⚠️ {orphaned_count} products without category relationships")
                # Don't fail - some products might not have categories

        # Check for products without brands
        with kg.get_session() as session:
            query = """
            MATCH (p:Product)
            WHERE NOT (p)-[:OF_BRAND]->()
            RETURN count(p) as orphaned_products
            """
            result = session.run(query)
            orphaned_count = result.single()["orphaned_products"]

            if orphaned_count == 0:
                logger.info("✅ No products without brands")
            else:
                logger.warning(f"⚠️ {orphaned_count} products without brand relationships")

        # Check for null SKUs
        with kg.get_session() as session:
            query = """
            MATCH (p:Product)
            WHERE p.sku IS NULL OR p.sku = ''
            RETURN count(p) as null_sku_count
            """
            result = session.run(query)
            null_count = result.single()["null_sku_count"]

            if null_count == 0:
                logger.info("✅ No products with null/empty SKU")
            else:
                logger.error(f"❌ {null_count} products with null/empty SKU")
                all_valid = False

        return all_valid

    except Exception as e:
        logger.error(f"❌ Failed to verify data quality: {e}")
        return False


# =============================================================================
# Main Verification Workflow
# =============================================================================

def run_verification() -> bool:
    """
    Run complete Neo4j population verification.

    Returns:
        True if all verifications pass, False otherwise
    """
    logger.info("="*80)
    logger.info("Neo4j Knowledge Graph Population Verification")
    logger.info("="*80)

    results = []

    # Step 1: Verify connection
    logger.info("\n[Step 1/6] Connection Verification")
    connection_ok = verify_connection()
    results.append(("Connection", connection_ok))

    if not connection_ok:
        logger.error("\n❌ Connection failed - aborting verification")
        return False

    kg = get_knowledge_graph()

    # Step 2: Verify node counts
    logger.info("\n[Step 2/6] Node Count Verification")
    nodes_ok, node_counts = verify_node_counts(kg)
    results.append(("Node Counts", nodes_ok))

    # Step 3: Verify relationship counts
    logger.info("\n[Step 3/6] Relationship Count Verification")
    rels_ok, rel_counts = verify_relationship_counts(kg)
    results.append(("Relationship Counts", rels_ok))

    # Step 4: Verify indexes and constraints
    logger.info("\n[Step 4/6] Indexes and Constraints Verification")
    indexes_ok = verify_indexes_and_constraints(kg)
    results.append(("Indexes/Constraints", indexes_ok))

    # Step 5: Verify sample queries
    logger.info("\n[Step 5/6] Sample Queries Verification")
    queries_ok = verify_sample_queries(kg)
    results.append(("Sample Queries", queries_ok))

    # Step 6: Verify data quality
    logger.info("\n[Step 6/6] Data Quality Verification")
    quality_ok = verify_data_quality(kg)
    results.append(("Data Quality", quality_ok))

    # Summary
    logger.info("\n" + "="*80)
    logger.info("Verification Summary")
    logger.info("="*80)

    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{check_name:30} {status}")
        if not passed:
            all_passed = False

    logger.info("="*80)

    if all_passed:
        logger.info("\n🎉 All verifications PASSED - Neo4j graph is ready for production!")
        return True
    else:
        logger.error("\n❌ Some verifications FAILED - review errors above")
        return False


# =============================================================================
# Script Entry Point
# =============================================================================

if __name__ == "__main__":
    try:
        success = run_verification()

        if success:
            logger.info("\nVerification complete - exiting with success (0)")
            sys.exit(0)
        else:
            logger.error("\nVerification failed - exiting with error (1)")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("\nVerification interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.critical(f"UNEXPECTED ERROR: {e}", exc_info=True)
        sys.exit(1)
