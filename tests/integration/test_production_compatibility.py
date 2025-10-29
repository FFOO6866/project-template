"""
Integration Tests for Production Compatibility Analysis

Tests the real Neo4j-based compatibility checking system in production_nexus_diy_platform.py

CRITICAL REQUIREMENTS:
- Uses REAL Neo4j knowledge graph (NO MOCKING)
- Tests actual compatibility relationship queries
- Validates confidence scoring from SemanticRelationship
- Ensures proper error handling for missing data
"""

import pytest
import asyncio
from typing import Dict, List, Any
from fastapi import HTTPException

# Test infrastructure
from src.core.neo4j_knowledge_graph import Neo4jKnowledgeGraph
from src.knowledge_graph.models import (
    SemanticRelationship, RelationshipType, ConfidenceSource
)
from src.production_nexus_diy_platform import (
    ProductionRecommendationEngine,
    SemanticKnowledgeGraph,
    CompatibilityCheckRequest
)


@pytest.fixture
def neo4j_kg():
    """Real Neo4j knowledge graph instance for testing"""
    import os

    # Get Neo4j connection params from environment (set by conftest.py)
    uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD', 'test_password')

    # Use the test fixture's Neo4j connection
    kg = Neo4jKnowledgeGraph(uri=uri, user=user, password=password)
    yield kg
    kg.close()


@pytest.fixture
async def semantic_kg():
    """SemanticKnowledgeGraph instance for production code"""
    import os

    # Get Neo4j connection params from environment (set by conftest.py)
    uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD', 'test_password')

    # Initialize with test Neo4j connection
    kg = SemanticKnowledgeGraph(neo4j_uri=uri, neo4j_user=user, neo4j_password=password)
    yield kg
    await kg.close()


@pytest.fixture
async def rec_engine(semantic_kg):
    """ProductionRecommendationEngine with real Neo4j"""
    engine = ProductionRecommendationEngine(
        knowledge_graph=semantic_kg,
        redis_client=None  # Not needed for compatibility tests
    )
    return engine


@pytest.fixture
async def test_products(neo4j_kg):
    """Create test products in Neo4j for compatibility testing"""
    # Create test products
    products = []

    # Product 1: Makita 18V Drill
    product1_id = neo4j_kg.create_product_node(
        product_id=1001,
        sku="MAKITA-DDF485",
        name="Makita 18V Cordless Drill",
        category="Power Tools",
        brand="Makita",
        description="18V LXT brushless drill driver"
    )
    products.append(1001)

    # Product 2: Makita 18V Battery (Compatible)
    product2_id = neo4j_kg.create_product_node(
        product_id=1002,
        sku="MAKITA-BL1850B",
        name="Makita 18V 5.0Ah Battery",
        category="Batteries",
        brand="Makita",
        description="18V LXT lithium-ion battery"
    )
    products.append(1002)

    # Product 3: DeWalt 20V Battery (Incompatible - different brand)
    product3_id = neo4j_kg.create_product_node(
        product_id=1003,
        sku="DEWALT-DCB205",
        name="DeWalt 20V MAX Battery",
        category="Batteries",
        brand="DeWalt",
        description="20V MAX lithium-ion battery"
    )
    products.append(1003)

    # Product 4: Makita Safety Glasses (Compatible accessory)
    product4_id = neo4j_kg.create_product_node(
        product_id=1004,
        sku="MAKITA-P-66310",
        name="Makita Safety Glasses",
        category="Safety Equipment",
        brand="Makita",
        description="ANSI Z87.1 rated safety glasses"
    )
    products.append(1004)

    yield products

    # Cleanup: Delete test products
    with neo4j_kg.get_session() as session:
        session.run("""
            MATCH (p:Product)
            WHERE p.id IN $product_ids
            DETACH DELETE p
        """, product_ids=products)


@pytest.fixture
async def test_compatibility_relationships(neo4j_kg, test_products):
    """Create test compatibility relationships in Neo4j"""
    relationships = []

    async with neo4j_kg.driver.session() as session:
        # Compatible: Makita Drill + Makita Battery
        await session.run("""
            MATCH (p1:Product {id: $product1_id})
            MATCH (p2:Product {id: $product2_id})
            CREATE (p1)-[r:COMPATIBLE_WITH {
                confidence: 0.95,
                relationship_type: 'COMPATIBLE_WITH',
                safety_notes: 'Same voltage and brand ecosystem',
                created_at: datetime()
            }]->(p2)
        """, product1_id=1001, product2_id=1002)
        relationships.append((1001, 1002))

        # Incompatible: Makita Drill + DeWalt Battery
        await session.run("""
            MATCH (p1:Product {id: $product1_id})
            MATCH (p2:Product {id: $product2_id})
            CREATE (p1)-[r:INCOMPATIBLE_WITH {
                confidence: 0.98,
                relationship_type: 'INCOMPATIBLE_WITH',
                safety_notes: 'Different brand ecosystems - battery will not fit',
                created_at: datetime()
            }]->(p2)
        """, product1_id=1001, product2_id=1003)
        relationships.append((1001, 1003))

        # Compatible: Makita Drill + Makita Safety Glasses (general compatibility)
        await session.run("""
            MATCH (p1:Product {id: $product1_id})
            MATCH (p2:Product {id: $product2_id})
            CREATE (p1)-[r:COMPATIBLE_WITH {
                confidence: 0.75,
                relationship_type: 'COMPATIBLE_WITH',
                safety_notes: 'Recommended safety equipment for power tool use',
                created_at: datetime()
            }]->(p2)
        """, product1_id=1001, product2_id=1004)
        relationships.append((1001, 1004))

    yield relationships

    # Cleanup handled by test_products fixture


# ==============================================================================
# TIER 2: INTEGRATION TESTS (Real Neo4j, NO MOCKING)
# ==============================================================================

@pytest.mark.tier2
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_compatible_products_analysis(rec_engine, test_products, test_compatibility_relationships):
    """Test compatibility analysis with COMPATIBLE products (Makita drill + battery)"""
    # Create compatibility check request
    request = CompatibilityCheckRequest(
        product1_id="1001",  # Makita Drill
        product2_id="1002",  # Makita Battery
        usage_context="cordless drilling",
        safety_critical=False
    )

    # Get compatibility relationships from Neo4j
    compat1 = await rec_engine.knowledge_graph.get_compatibility_relationships("1001")
    compat2 = await rec_engine.knowledge_graph.get_compatibility_relationships("1002")

    # Analyze compatibility
    analysis = await rec_engine._analyze_compatibility("1001", "1002", compat1, compat2, request)

    # Validate analysis results
    assert analysis['status'] == 'compatible', "Should detect compatible products"
    assert analysis['confidence'] >= 0.9, "Confidence should be high (0.95 from relationship)"
    assert 'technical_details' in analysis
    assert analysis['technical_details']['relationship_count'] > 0

    # Validate safety assessment
    safety = await rec_engine._assess_compatibility_safety(analysis, request.safety_critical)
    assert safety['safety_rating'] == 'safe'
    assert len(safety['warnings']) == 0 or 'Same voltage' in str(safety['warnings'])
    assert safety['certifications_valid'] is True

    # Validate recommendations
    recommendations = await rec_engine._generate_compatibility_recommendations(analysis, safety)
    assert len(recommendations) > 0
    assert any('compatible' in rec.lower() for rec in recommendations)
    assert any('95%' in rec or '0.95' in rec for rec in recommendations), "Should show confidence score"


@pytest.mark.tier2
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_incompatible_products_analysis(rec_engine, test_products, test_compatibility_relationships):
    """Test compatibility analysis with INCOMPATIBLE products (Makita drill + DeWalt battery)"""
    request = CompatibilityCheckRequest(
        product1_id="1001",  # Makita Drill
        product2_id="1003",  # DeWalt Battery
        usage_context="cordless drilling",
        safety_critical=True
    )

    # Get compatibility relationships from Neo4j
    compat1 = await rec_engine.knowledge_graph.get_compatibility_relationships("1001")
    compat2 = await rec_engine.knowledge_graph.get_compatibility_relationships("1003")

    # Analyze compatibility
    analysis = await rec_engine._analyze_compatibility("1001", "1003", compat1, compat2, request)

    # Validate analysis results
    assert analysis['status'] == 'incompatible', "Should detect incompatible products"
    assert analysis['confidence'] >= 0.9, "Confidence should be high (0.98 from relationship)"
    assert 'incompatibility_reasons' in analysis['technical_details']
    assert len(analysis['technical_details']['incompatibility_reasons']) > 0

    # Validate safety assessment
    safety = await rec_engine._assess_compatibility_safety(analysis, request.safety_critical)
    assert safety['safety_rating'] == 'unsafe'
    assert len(safety['warnings']) > 0
    assert 'DO NOT use' in str(safety['required_precautions'])
    assert safety['certifications_valid'] is False

    # Validate recommendations
    recommendations = await rec_engine._generate_compatibility_recommendations(analysis, safety)
    assert len(recommendations) > 0
    assert any('NOT compatible' in rec for rec in recommendations)
    assert any('Different brand' in rec or 'battery will not fit' in rec for rec in recommendations)


@pytest.mark.tier2
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_no_compatibility_data_raises_404(rec_engine, test_products):
    """Test that missing compatibility data raises HTTPException 404"""
    request = CompatibilityCheckRequest(
        product1_id="1001",  # Makita Drill
        product2_id="9999",  # Non-existent product
        usage_context="testing",
        safety_critical=False
    )

    # Get compatibility relationships (will be empty for non-existent product)
    compat1 = await rec_engine.knowledge_graph.get_compatibility_relationships("1001")
    compat2 = []  # No relationships for non-existent product

    # Should raise HTTPException 404
    with pytest.raises(HTTPException) as exc_info:
        await rec_engine._analyze_compatibility("1001", "9999", compat1, compat2, request)

    assert exc_info.value.status_code == 404
    assert "No compatibility relationships found" in str(exc_info.value.detail)


@pytest.mark.tier2
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_neo4j_not_configured_raises_501(semantic_kg):
    """Test that missing Neo4j configuration raises HTTPException 501"""
    # Create engine without Neo4j driver
    class MockSemanticKG:
        pass  # No driver attribute

    engine = ProductionRecommendationEngine(
        knowledge_graph=MockSemanticKG(),
        redis_client=None
    )

    request = CompatibilityCheckRequest(
        product1_id="1001",
        product2_id="1002",
        usage_context="testing",
        safety_critical=False
    )

    # Should raise HTTPException 501
    with pytest.raises(HTTPException) as exc_info:
        await engine._analyze_compatibility("1001", "1002", [], [], request)

    assert exc_info.value.status_code == 501
    assert "Neo4j knowledge graph" in str(exc_info.value.detail)


@pytest.mark.tier2
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_confidence_scores_from_relationships(rec_engine, test_products, test_compatibility_relationships):
    """Test that confidence scores are correctly extracted from SemanticRelationship data"""
    request = CompatibilityCheckRequest(
        product1_id="1001",
        product2_id="1002",
        usage_context="testing",
        safety_critical=False
    )

    # Get compatibility relationships
    compat1 = await rec_engine.knowledge_graph.get_compatibility_relationships("1001")
    compat2 = await rec_engine.knowledge_graph.get_compatibility_relationships("1002")

    # Analyze compatibility
    analysis = await rec_engine._analyze_compatibility("1001", "1002", compat1, compat2, request)

    # Confidence should match the relationship's confidence (0.95)
    assert abs(analysis['confidence'] - 0.95) < 0.01, "Confidence should match relationship data"


@pytest.mark.tier2
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_safety_critical_flag_affects_safety_rating(rec_engine, test_products, test_compatibility_relationships):
    """Test that safety_critical flag affects safety assessment"""
    request = CompatibilityCheckRequest(
        product1_id="1001",
        product2_id="1002",
        usage_context="testing",
        safety_critical=True  # Safety-critical context
    )

    # Get compatibility relationships
    compat1 = await rec_engine.knowledge_graph.get_compatibility_relationships("1001")
    compat2 = await rec_engine.knowledge_graph.get_compatibility_relationships("1002")

    # Analyze compatibility
    analysis = await rec_engine._analyze_compatibility("1001", "1002", compat1, compat2, request)

    # Safety assessment should reflect safety-critical context
    safety = await rec_engine._assess_compatibility_safety(analysis, request.safety_critical)

    # For compatible products in safety-critical context
    assert safety['safety_rating'] == 'safe_with_precautions', "Safety-critical should require precautions"
    assert len(safety['required_precautions']) > 0


@pytest.mark.tier2
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_multiple_relationships_max_confidence(rec_engine, neo4j_kg, test_products):
    """Test that multiple relationships use maximum confidence score"""
    # Create multiple COMPATIBLE_WITH relationships with different confidence scores
    async with neo4j_kg.driver.session() as session:
        await session.run("""
            MATCH (p1:Product {id: 1001})
            MATCH (p2:Product {id: 1002})
            CREATE (p1)-[:COMPATIBLE_WITH {
                confidence: 0.70,
                relationship_type: 'COMPATIBLE_WITH',
                safety_notes: 'Lower confidence relationship',
                created_at: datetime()
            }]->(p2)
        """)

        await session.run("""
            MATCH (p1:Product {id: 1001})
            MATCH (p2:Product {id: 1002})
            CREATE (p1)-[:COMPATIBLE_WITH {
                confidence: 0.95,
                relationship_type: 'COMPATIBLE_WITH',
                safety_notes: 'Higher confidence relationship',
                created_at: datetime()
            }]->(p2)
        """)

    request = CompatibilityCheckRequest(
        product1_id="1001",
        product2_id="1002",
        usage_context="testing",
        safety_critical=False
    )

    # Get compatibility relationships
    compat1 = await rec_engine.knowledge_graph.get_compatibility_relationships("1001")
    compat2 = await rec_engine.knowledge_graph.get_compatibility_relationships("1002")

    # Analyze compatibility
    analysis = await rec_engine._analyze_compatibility("1001", "1002", compat1, compat2, request)

    # Should use maximum confidence (0.95)
    assert analysis['confidence'] >= 0.95, "Should use maximum confidence from multiple relationships"

    # Cleanup
    async with neo4j_kg.driver.session() as session:
        await session.run("""
            MATCH (p1:Product {id: 1001})-[r:COMPATIBLE_WITH]->(p2:Product {id: 1002})
            WHERE r.confidence < 0.95
            DELETE r
        """)


@pytest.mark.tier2
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_bidirectional_relationships(rec_engine, neo4j_kg, test_products):
    """Test that bidirectional relationships are handled correctly"""
    # Create bidirectional COMPATIBLE_WITH relationship
    async with neo4j_kg.driver.session() as session:
        # A -> B
        await session.run("""
            MATCH (p1:Product {id: 1001})
            MATCH (p2:Product {id: 1004})
            CREATE (p1)-[:COMPATIBLE_WITH {
                confidence: 0.80,
                relationship_type: 'COMPATIBLE_WITH',
                created_at: datetime()
            }]->(p2)
        """)

        # B -> A
        await session.run("""
            MATCH (p1:Product {id: 1004})
            MATCH (p2:Product {id: 1001})
            CREATE (p1)-[:COMPATIBLE_WITH {
                confidence: 0.85,
                relationship_type: 'COMPATIBLE_WITH',
                created_at: datetime()
            }]->(p2)
        """)

    request = CompatibilityCheckRequest(
        product1_id="1001",
        product2_id="1004",
        usage_context="testing",
        safety_critical=False
    )

    # Get compatibility relationships
    compat1 = await rec_engine.knowledge_graph.get_compatibility_relationships("1001")
    compat2 = await rec_engine.knowledge_graph.get_compatibility_relationships("1004")

    # Analyze compatibility
    analysis = await rec_engine._analyze_compatibility("1001", "1004", compat1, compat2, request)

    # Should detect compatibility from either direction
    assert analysis['status'] == 'compatible'
    assert analysis['confidence'] >= 0.80  # Max of 0.80 and 0.85

    # Cleanup
    async with neo4j_kg.driver.session() as session:
        await session.run("""
            MATCH (p1:Product {id: 1001})-[r:COMPATIBLE_WITH]-(p2:Product {id: 1004})
            DELETE r
        """)
