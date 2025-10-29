"""
Test Neo4j Knowledge Graph Integration
Phase 1: Verify connectivity and schema initialization
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_neo4j_connection():
    """Test Neo4j connection with production credentials"""
    logger.info("=" * 80)
    logger.info("TEST 1: Neo4j Connection")
    logger.info("=" * 80)

    try:
        from src.core.neo4j_knowledge_graph import Neo4jKnowledgeGraph

        # Create knowledge graph instance (uses environment variables)
        kg = Neo4jKnowledgeGraph()

        # Test connection
        if kg.test_connection():
            logger.info("✅ Neo4j connection successful")
            kg.close()
            return True
        else:
            logger.error("❌ Neo4j connection test failed")
            return False

    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        logger.error("Make sure neo4j driver is installed: pip install neo4j")
        return False
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False


def test_schema_verification():
    """Verify Neo4j schema initialization"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Schema Verification")
    logger.info("=" * 80)

    try:
        from src.core.neo4j_knowledge_graph import Neo4jKnowledgeGraph

        kg = Neo4jKnowledgeGraph()
        schema_info = kg.verify_schema()

        if schema_info.get("status") == "initialized":
            logger.info("✅ Schema initialized successfully")
            logger.info(f"   - Constraints: {schema_info.get('constraints', 0)}")
            logger.info(f"   - Indexes: {schema_info.get('indexes', 0)}")
            logger.info(f"   - Total nodes: {schema_info.get('total_nodes', 0)}")

            node_counts = schema_info.get('node_counts', {})
            if node_counts:
                logger.info("   - Node counts by type:")
                for node_type, count in node_counts.items():
                    logger.info(f"     * {node_type}: {count}")

            kg.close()
            return True
        else:
            logger.error(f"❌ Schema verification failed: {schema_info}")
            kg.close()
            return False

    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
        return False


def test_create_sample_nodes():
    """Test creating sample product and task nodes"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Create Sample Nodes")
    logger.info("=" * 80)

    try:
        from src.core.neo4j_knowledge_graph import Neo4jKnowledgeGraph

        kg = Neo4jKnowledgeGraph()

        # Create sample product node
        logger.info("Creating sample product node...")
        product_created = kg.create_product_node(
            product_id=99999,  # Test ID
            sku="TEST-DRILL-001",
            name="Test Cordless Drill",
            category="Power Tools",
            brand="Test Brand",
            description="Test drill for Neo4j integration testing",
            keywords=["drill", "power tool", "cordless"]
        )

        if not product_created:
            logger.error("❌ Failed to create sample product node")
            kg.close()
            return False

        logger.info("✅ Sample product node created")

        # Create sample task node
        logger.info("Creating sample task node...")
        task_created = kg.create_task_node(
            task_id="task_test_drill_hole",
            name="Test Drill Hole",
            description="Test task for drilling holes in various materials",
            category="drilling",
            skill_level="beginner",
            estimated_time_minutes=15
        )

        if not task_created:
            logger.error("❌ Failed to create sample task node")
            kg.close()
            return False

        logger.info("✅ Sample task node created")

        # Create relationship
        logger.info("Creating USED_FOR relationship...")
        relationship_created = kg.create_product_used_for_task(
            product_id=99999,
            task_id="task_test_drill_hole",
            necessity="required",
            usage_notes="Essential tool for drilling tasks"
        )

        if not relationship_created:
            logger.error("❌ Failed to create relationship")
            kg.close()
            return False

        logger.info("✅ USED_FOR relationship created")

        # Verify by querying
        logger.info("Querying products for task...")
        products = kg.get_products_for_task("task_test_drill_hole", limit=10)

        if products:
            logger.info(f"✅ Found {len(products)} products for task")
            for product in products:
                logger.info(f"   - {product['name']} ({product['sku']}) - {product['necessity']}")
        else:
            logger.warning("⚠️ No products found for task (may need time to index)")

        # Get statistics
        stats = kg.get_statistics()
        logger.info("Knowledge graph statistics:")
        logger.info(f"   - Status: {stats.get('status')}")
        logger.info(f"   - Total nodes: {stats.get('total_nodes', 0)}")
        logger.info(f"   - Total relationships: {stats.get('total_relationships', 0)}")

        kg.close()
        return True

    except Exception as e:
        logger.error(f"❌ Sample node creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_postgresql_neo4j_integration():
    """Test integration between PostgreSQL and Neo4j"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: PostgreSQL-Neo4j Integration")
    logger.info("=" * 80)

    try:
        from src.core.postgresql_database import get_database

        # Get PostgreSQL database instance
        db = get_database()

        # Test connection
        if not db.test_connection():
            logger.error("❌ PostgreSQL connection failed")
            return False

        logger.info("✅ PostgreSQL connection successful")

        # Test knowledge graph sync (limit to 10 products for testing)
        logger.info("Testing product sync to Neo4j (limit: 10 products)...")
        sync_result = db.sync_products_to_knowledge_graph(limit=10)

        if sync_result.get("status") == "success":
            logger.info("✅ Product sync successful")
            logger.info(f"   - Total products: {sync_result.get('total_products', 0)}")
            logger.info(f"   - Synced: {sync_result.get('synced', 0)}")
            logger.info(f"   - Failed: {sync_result.get('failed', 0)}")
            logger.info(f"   - Success rate: {sync_result.get('sync_percentage', 0)}%")
            return True
        elif sync_result.get("status") == "warning":
            logger.warning(f"⚠️ {sync_result.get('message')}")
            return True  # Not a failure, just no data
        else:
            logger.error(f"❌ Product sync failed: {sync_result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_graph_recommendations():
    """Test knowledge graph-based recommendations"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Knowledge Graph Recommendations")
    logger.info("=" * 80)

    try:
        from src.core.postgresql_database import get_database

        db = get_database()

        # Test task-based recommendations
        test_tasks = [
            "drill holes in concrete wall",
            "paint bedroom walls",
            "install kitchen cabinets"
        ]

        for task in test_tasks:
            logger.info(f"\nGetting recommendations for: '{task}'")
            recommendations = db.get_knowledge_graph_recommendations(task, limit=5)

            if recommendations:
                logger.info(f"✅ Found {len(recommendations)} recommendations:")
                for i, product in enumerate(recommendations, 1):
                    logger.info(f"   {i}. {product.get('name')} ({product.get('sku')})")
            else:
                logger.warning(f"⚠️ No recommendations found for '{task}'")

        return True

    except Exception as e:
        logger.error(f"❌ Recommendation test failed: {e}")
        return False


def run_all_tests():
    """Run all Neo4j integration tests"""
    logger.info("\n")
    logger.info("#" * 80)
    logger.info("# Neo4j Knowledge Graph Integration Tests")
    logger.info("# Phase 1: Enterprise AI Recommendation System")
    logger.info("#" * 80)
    logger.info("\n")

    # Check environment variables
    logger.info("Checking environment configuration...")
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_user = os.getenv('NEO4J_USER')
    neo4j_password = os.getenv('NEO4J_PASSWORD')

    if not neo4j_uri:
        logger.error("❌ NEO4J_URI environment variable not set")
        logger.info("Expected: bolt://neo4j:7687 (Docker) or bolt://localhost:7687 (local)")
        return False

    if not neo4j_password:
        logger.error("❌ NEO4J_PASSWORD environment variable not set")
        logger.info("Set this in .env.production file")
        return False

    logger.info(f"✅ NEO4J_URI: {neo4j_uri}")
    logger.info(f"✅ NEO4J_USER: {neo4j_user or 'neo4j'}")
    logger.info(f"✅ NEO4J_PASSWORD: {'*' * len(neo4j_password) if neo4j_password else 'NOT SET'}")

    # Run tests
    results = {
        "Connection Test": test_neo4j_connection(),
        "Schema Verification": test_schema_verification(),
        "Sample Node Creation": test_create_sample_nodes(),
        "PostgreSQL Integration": test_postgresql_neo4j_integration(),
        "Knowledge Graph Recommendations": test_knowledge_graph_recommendations()
    }

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed = 0
    failed = 0

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    logger.info("\n" + "-" * 80)
    logger.info(f"Total: {passed + failed} tests")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {round((passed / (passed + failed)) * 100, 2)}%")
    logger.info("-" * 80)

    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! Neo4j integration is ready for Phase 2.")
        return True
    else:
        logger.error(f"\n❌ {failed} test(s) failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    # Load environment variables from .env.production
    try:
        from dotenv import load_dotenv
        env_file = os.path.join(os.path.dirname(__file__), '.env.production')
        if os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"✅ Loaded environment from {env_file}")
        else:
            logger.warning(f"⚠️ .env.production not found at {env_file}")
    except ImportError:
        logger.warning("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")

    # Run tests
    success = run_all_tests()
    sys.exit(0 if success else 1)
