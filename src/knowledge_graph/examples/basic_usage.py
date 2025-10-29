"""
Basic Usage Examples for Horme Knowledge Graph

This file demonstrates basic usage patterns for the knowledge graph system.
"""

import asyncio
import os
from datetime import datetime

# Import knowledge graph components
from knowledge_graph import Neo4jConnection, GraphDatabase
from knowledge_graph.models import ProductNode, SemanticRelationship, RelationshipType, ConfidenceSource
from knowledge_graph.search import SemanticSearchEngine
from knowledge_graph.inference import RelationshipInferenceEngine
from knowledge_graph.integration import PostgreSQLIntegration
from knowledge_graph.dataflow_integration import KnowledgeGraphWorkflows


async def basic_setup_example():
    """Example 1: Basic setup and connection"""
    print("=== Basic Setup Example ===")
    
    # Initialize Neo4j connection
    neo4j_conn = Neo4jConnection(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="horme_knowledge_2024"
    )
    
    # Create graph database interface
    graph_db = GraphDatabase(neo4j_conn)
    
    # Test connection
    health_status = neo4j_conn.health_check()
    print(f"Database Health: {health_status['status']}")
    
    # Get database statistics
    stats = graph_db.get_database_stats()
    print(f"Database Stats: {stats}")
    
    neo4j_conn.close()


async def product_management_example():
    """Example 2: Creating and managing products"""
    print("=== Product Management Example ===")
    
    neo4j_conn = Neo4jConnection()
    graph_db = GraphDatabase(neo4j_conn)
    
    # Create a sample product
    sample_product = ProductNode(
        product_id=99999,
        sku="EXAMPLE-DRILL-001",
        name="Example 18V Cordless Drill",
        slug="example-18v-cordless-drill",
        brand_name="Example Brand",
        category_name="Power Tools",
        price=129.99,
        description="High-performance 18V cordless drill with hammer function",
        specifications={
            "voltage": "18V",
            "torque": "65 Nm",
            "chuck_size": "13mm",
            "battery_type": "Li-ion"
        },
        features=["Hammer function", "LED work light", "Belt clip"],
        keywords=["drill", "cordless", "18V", "hammer", "construction"]
    )
    
    # Create product in graph
    success = graph_db.create_product_node(sample_product)
    print(f"Product created: {success}")
    
    # Retrieve the product
    retrieved_product = graph_db.get_product_node(product_id=99999)
    if retrieved_product:
        print(f"Retrieved product: {retrieved_product.name}")
    
    neo4j_conn.close()


async def relationship_management_example():
    """Example 3: Creating and querying relationships"""
    print("=== Relationship Management Example ===")
    
    neo4j_conn = Neo4jConnection()
    graph_db = GraphDatabase(neo4j_conn)
    
    # Create a relationship between two products
    relationship = SemanticRelationship(
        from_product_id=99999,
        to_product_id=99998,  # Assuming another product exists
        relationship_type=RelationshipType.COMPATIBLE_WITH,
        confidence=0.9,
        source=ConfidenceSource.MANUFACTURER_SPEC,
        compatibility_type="battery_system",
        notes="Both products use the same 18V battery system"
    )
    
    # Create relationship in graph
    success = graph_db.create_relationship(relationship)
    print(f"Relationship created: {success}")
    
    # Query relationships for a product
    relationships = graph_db.get_product_relationships(
        product_id=99999,
        min_confidence=0.5
    )
    print(f"Found {len(relationships)} relationships")
    
    for rel in relationships[:3]:  # Show first 3
        print(f"  - {rel['relationship_type']}: {rel['related_name']} (confidence: {rel['confidence']})")
    
    neo4j_conn.close()


async def semantic_search_example():
    """Example 4: Semantic search capabilities"""
    print("=== Semantic Search Example ===")
    
    neo4j_conn = Neo4jConnection()
    search_engine = SemanticSearchEngine(
        neo4j_connection=neo4j_conn,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Basic product search
    print("Searching for: 'cordless drill for home projects'")
    results = await search_engine.search(
        query="cordless drill for home projects",
        limit=5,
        search_strategy="hybrid"
    )
    
    print(f"Found {len(results)} products:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.name}")
        print(f"     Brand: {result.brand_name}")
        print(f"     Score: {result.combined_score:.3f}")
        print(f"     Reasons: {', '.join(result.match_reasons)}")
        print()
    
    # Compatibility search
    if results:
        first_product_id = results[0].product_id
        print(f"Finding products compatible with: {results[0].name}")
        
        compatible = await search_engine.find_compatible_products(
            product_id=first_product_id,
            limit=3
        )
        
        print(f"Found {len(compatible)} compatible products:")
        for comp in compatible:
            print(f"  - {comp.name} (compatibility: {comp.graph_similarity:.3f})")
    
    neo4j_conn.close()


async def project_recommendation_example():
    """Example 5: DIY project recommendations"""
    print("=== Project Recommendation Example ===")
    
    neo4j_conn = Neo4jConnection()
    search_engine = SemanticSearchEngine(neo4j_connection=neo4j_conn)
    
    # Get recommendations for a bathroom renovation project
    recommendations = await search_engine.recommend_for_project(
        project_description="bathroom renovation with tile installation",
        budget_range="medium",
        skill_level="intermediate",
        limit=10
    )
    
    print("Recommendations for bathroom renovation:")
    for result in recommendations[:5]:  # Show top 5
        print(f"  - {result.name}")
        print(f"    Price: ${result.price:.2f}" if result.price else "    Price: N/A")
        print(f"    Relevance: {result.combined_score:.3f}")
        print()
    
    neo4j_conn.close()


async def relationship_inference_example():
    """Example 6: AI-powered relationship inference"""
    print("=== Relationship Inference Example ===")
    
    neo4j_conn = Neo4jConnection()
    inference_engine = RelationshipInferenceEngine(
        neo4j_connection=neo4j_conn,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Infer relationships for a specific product
    relationships = await inference_engine.infer_product_relationships(
        product_id=99999,  # Our example product
        relationship_types=[
            RelationshipType.COMPATIBLE_WITH,
            RelationshipType.ALTERNATIVE_TO
        ]
    )
    
    print(f"Inferred {len(relationships)} relationships:")
    for rel in relationships:
        print(f"  - {rel.relationship_type.value}: Product {rel.to_product_id}")
        print(f"    Confidence: {rel.confidence:.3f}")
        print(f"    Source: {rel.source.value}")
        if rel.notes:
            print(f"    Notes: {rel.notes}")
        print()
    
    neo4j_conn.close()


async def data_migration_example():
    """Example 7: Data migration from PostgreSQL"""
    print("=== Data Migration Example ===")
    
    neo4j_conn = Neo4jConnection()
    postgres_integration = PostgreSQLIntegration(neo4j_connection=neo4j_conn)
    
    try:
        # Get sync status
        status = await postgres_integration.get_sync_status()
        print("Current sync status:")
        for entity_type, details in status.items():
            if isinstance(details, dict) and 'synced' in details:
                print(f"  {entity_type}: {details['synced']}/{details['total']} ({details['sync_percentage']}%)")
        
        # Migrate a small batch of products (for demo)
        print("\nMigrating 10 products...")
        migrated_count = await postgres_integration.migrate_products(
            force_refresh=False,
            limit=10
        )
        print(f"Migrated {migrated_count} products")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        print("Make sure PostgreSQL is running and accessible")
    
    await postgres_integration.close()


async def dataflow_workflow_example():
    """Example 8: DataFlow workflow integration"""
    print("=== DataFlow Workflow Example ===")
    
    # Initialize workflow system
    workflows = KnowledgeGraphWorkflows()
    
    # Execute product discovery workflow
    print("Running product discovery workflow...")
    results = workflows.execute_product_discovery(
        search_query="tools for deck building project"
    )
    
    print("Workflow Results:")
    print(f"  Query: {results.get('search_query')}")
    
    analysis = results.get('analysis', {})
    print(f"  Products found: {analysis.get('total_products_found', 0)}")
    print(f"  Compatible products: {analysis.get('compatible_products_found', 0)}")
    print(f"  Project recommendations: {analysis.get('project_recommendations_found', 0)}")
    print(f"  Is project-related: {analysis.get('is_project_related', False)}")
    
    # Show some search results
    search_results = results.get('search_results', {}).get('results', [])
    if search_results:
        print("\n  Top search results:")
        for result in search_results[:3]:
            print(f"    - {result['name']} (Score: {result['combined_score']:.3f})")


async def brand_ecosystem_example():
    """Example 9: Brand ecosystem analysis"""
    print("=== Brand Ecosystem Example ===")
    
    neo4j_conn = Neo4jConnection()
    graph_db = GraphDatabase(neo4j_conn)
    
    # Analyze a brand ecosystem (if data exists)
    ecosystem = graph_db.get_brand_ecosystem("Makita")
    
    if ecosystem.get("brand"):
        print(f"Brand: {ecosystem['brand']['name']}")
        print(f"Ecosystem size: {ecosystem['ecosystem_size']} products")
        print(f"Internal relationships: {ecosystem['relationship_count']}")
        
        # Show some products in the ecosystem
        products = ecosystem.get('products', [])
        if products:
            print("\nProducts in ecosystem:")
            for product in products[:5]:  # Show first 5
                print(f"  - {product.get('name', 'Unknown')}")
    else:
        print("No brand ecosystem data found (run data migration first)")
    
    neo4j_conn.close()


async def performance_monitoring_example():
    """Example 10: Performance monitoring and optimization"""
    print("=== Performance Monitoring Example ===")
    
    neo4j_conn = Neo4jConnection()
    
    # Check system health
    health = neo4j_conn.health_check()
    print(f"System Status: {health['status']}")
    print(f"Neo4j Connected: {health.get('neo4j_connected', False)}")
    print(f"Redis Cache: {health.get('redis_cache', 'unavailable')}")
    
    # Performance timing example
    start_time = datetime.utcnow()
    
    graph_db = GraphDatabase(neo4j_conn)
    stats = graph_db.get_database_stats()
    
    end_time = datetime.utcnow()
    query_time = (end_time - start_time).total_seconds()
    
    print(f"\nDatabase Statistics (retrieved in {query_time:.3f}s):")
    for label, count in stats.items():
        print(f"  {label}: {count}")
    
    neo4j_conn.close()


async def main():
    """Run all examples"""
    print("🚀 Horme Knowledge Graph - Basic Usage Examples")
    print("=" * 60)
    
    try:
        await basic_setup_example()
        print()
        
        await product_management_example()
        print()
        
        await relationship_management_example()
        print()
        
        await semantic_search_example()
        print()
        
        await project_recommendation_example()
        print()
        
        await relationship_inference_example()
        print()
        
        await data_migration_example()
        print()
        
        await dataflow_workflow_example()
        print()
        
        await brand_ecosystem_example()
        print()
        
        await performance_monitoring_example()
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Neo4j is running (docker-compose -f docker-compose.neo4j.yml up -d)")
        print("2. Check environment variables (NEO4J_URI, POSTGRES_URL, etc.)")
        print("3. Ensure required Python packages are installed (pip install -r requirements.txt)")
        print("4. For AI features, set OPENAI_API_KEY environment variable")
    
    print("\n✅ Examples completed!")


if __name__ == "__main__":
    # Set up basic environment variables if not set
    if not os.getenv("NEO4J_URI"):
        os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    if not os.getenv("NEO4J_USER"):
        os.environ["NEO4J_USER"] = "neo4j"
    if not os.getenv("NEO4J_PASSWORD"):
        os.environ["NEO4J_PASSWORD"] = "horme_knowledge_2024"
    
    # Run examples
    asyncio.run(main())