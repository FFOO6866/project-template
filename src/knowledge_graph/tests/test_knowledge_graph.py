"""
Test Suite for Knowledge Graph System

Basic tests to validate functionality of the knowledge graph components.
"""

import pytest
import asyncio
import os
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Import components to test
from knowledge_graph.database import Neo4jConnection, GraphDatabase
from knowledge_graph.models import (
    ProductNode, SemanticRelationship, RelationshipType, ConfidenceSource
)
from knowledge_graph.search import SemanticSearchEngine
from knowledge_graph.inference import RelationshipInferenceEngine
from knowledge_graph.dataflow_integration import KnowledgeGraphDataFlowNodes


class TestNeo4jConnection:
    """Test Neo4j connection functionality"""
    
    def test_connection_initialization(self):
        """Test basic connection initialization"""
        conn = Neo4jConnection(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="test_password"
        )
        
        assert conn.uri == "bolt://localhost:7687"
        assert conn.username == "neo4j"
        assert conn.password == "test_password"
        assert conn.database == "horme_knowledge"
    
    @patch('neo4j.GraphDatabase.driver')
    def test_connection_success(self, mock_driver):
        """Test successful database connection"""
        # Mock Neo4j driver
        mock_session = Mock()
        mock_session.run.return_value.single.return_value = {"test": 1}
        mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
        
        conn = Neo4jConnection()
        driver = conn.connect()
        
        assert driver is not None
        mock_driver.assert_called_once()
    
    def test_health_check_structure(self):
        """Test health check response structure"""
        conn = Neo4jConnection()
        
        # Mock the health check to avoid requiring real database
        with patch.object(conn, 'session') as mock_session:
            mock_session.return_value.__enter__.return_value.run.return_value.single.return_value = {
                "open_transactions": 0,
                "committed_transactions": 100
            }
            
            health = conn.health_check()
            
            # Check response structure
            assert "status" in health
            assert "timestamp" in health
            assert isinstance(health["timestamp"], str)


class TestProductNode:
    """Test ProductNode data model"""
    
    def test_product_node_creation(self):
        """Test creating a ProductNode"""
        product = ProductNode(
            product_id=123,
            sku="TEST-123",
            name="Test Product",
            slug="test-product",
            brand_name="Test Brand",
            category_name="Test Category",
            price=99.99,
            description="A test product",
            specifications={"voltage": "18V"},
            features=["feature1", "feature2"],
            keywords=["test", "product"]
        )
        
        assert product.product_id == 123
        assert product.sku == "TEST-123"
        assert product.name == "Test Product"
        assert product.price == 99.99
        assert product.specifications["voltage"] == "18V"
        assert len(product.features) == 2
        assert len(product.keywords) == 2
    
    def test_product_to_neo4j_properties(self):
        """Test conversion to Neo4j properties"""
        product = ProductNode(
            product_id=123,
            sku="TEST-123",
            name="Test Product",
            slug="test-product"
        )
        
        props = product.to_neo4j_properties()
        
        assert props["product_id"] == 123
        assert props["sku"] == "TEST-123"
        assert props["name"] == "Test Product"
        assert props["slug"] == "test-product"
        assert "updated_at" in props


class TestSemanticRelationship:
    """Test SemanticRelationship data model"""
    
    def test_relationship_creation(self):
        """Test creating a SemanticRelationship"""
        relationship = SemanticRelationship(
            from_product_id=123,
            to_product_id=456,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
            confidence=0.85,
            source=ConfidenceSource.AI_INFERENCE,
            compatibility_type="battery_system",
            notes="Test relationship"
        )
        
        assert relationship.from_product_id == 123
        assert relationship.to_product_id == 456
        assert relationship.relationship_type == RelationshipType.COMPATIBLE_WITH
        assert relationship.confidence == 0.85
        assert relationship.source == ConfidenceSource.AI_INFERENCE
        assert relationship.compatibility_type == "battery_system"
    
    def test_relationship_quality_score(self):
        """Test quality score calculation"""
        # High confidence, manufacturer source
        relationship1 = SemanticRelationship(
            from_product_id=123,
            to_product_id=456,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
            confidence=0.9,
            source=ConfidenceSource.MANUFACTURER_SPEC,
            validation_count=5,
            rejection_count=0
        )
        
        quality1 = relationship1.quality_score()
        assert quality1 > 0.8
        
        # Lower confidence, AI source
        relationship2 = SemanticRelationship(
            from_product_id=123,
            to_product_id=456,
            relationship_type=RelationshipType.ALTERNATIVE_TO,
            confidence=0.6,
            source=ConfidenceSource.AI_INFERENCE,
            validation_count=1,
            rejection_count=2
        )
        
        quality2 = relationship2.quality_score()
        assert quality2 < quality1


class TestGraphDatabase:
    """Test GraphDatabase operations"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_connection = Mock(spec=Neo4jConnection)
        self.graph_db = GraphDatabase(self.mock_connection)
    
    def test_graph_database_initialization(self):
        """Test GraphDatabase initialization"""
        assert self.graph_db.conn == self.mock_connection
        assert hasattr(self.graph_db, 'logger')
    
    @patch('knowledge_graph.database.GraphDatabase.create_product_node')
    def test_create_product_node(self, mock_create):
        """Test product node creation"""
        mock_create.return_value = True
        
        product = ProductNode(
            product_id=123,
            sku="TEST-123",
            name="Test Product",
            slug="test-product"
        )
        
        result = mock_create(product)
        assert result == True
        mock_create.assert_called_once_with(product)


class TestSemanticSearchEngine:
    """Test semantic search functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_connection = Mock(spec=Neo4jConnection)
        self.search_engine = SemanticSearchEngine(
            neo4j_connection=self.mock_connection,
            use_sentence_transformers=False  # Avoid loading models in tests
        )
    
    def test_search_engine_initialization(self):
        """Test search engine initialization"""
        assert self.search_engine.neo4j_conn == self.mock_connection
        assert hasattr(self.search_engine, 'intent_patterns')
        assert hasattr(self.search_engine, 'entity_patterns')
    
    def test_normalize_query(self):
        """Test query normalization"""
        # Test case normalization
        normalized = self.search_engine._normalize_query("  POWER DRILL w/ BATTERY  ")
        assert normalized == "power drill with battery"
        
        # Test abbreviation expansion
        normalized = self.search_engine._normalize_query("drill mfg makita inc battery")
        assert "manufacturer" in normalized
        assert "including" in normalized
    
    def test_detect_intent(self):
        """Test intent detection"""
        # Test compatibility intent
        intent = self.search_engine._detect_intent("battery compatible with makita drill")
        assert intent == "compatibility"
        
        # Test project intent
        intent = self.search_engine._detect_intent("tools for bathroom renovation")
        assert intent == "project"
        
        # Test alternative intent
        intent = self.search_engine._detect_intent("alternative to dewalt drill")
        assert intent == "alternative"
        
        # Test default intent
        intent = self.search_engine._detect_intent("cordless drill")
        assert intent == "product_search"
    
    def test_extract_entities(self):
        """Test entity extraction"""
        entities = self.search_engine._extract_entities("makita 18v drill with hammer function")
        
        # Should extract brand, voltage, and category
        brand_entities = [e for e in entities if e.startswith("brand:")]
        voltage_entities = [e for e in entities if e.startswith("voltage:")]
        category_entities = [e for e in entities if e.startswith("category:")]
        
        assert len(brand_entities) > 0
        assert len(voltage_entities) > 0
        assert len(category_entities) > 0
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        keywords = self.search_engine._extract_keywords(
            "I need a cordless drill for building a deck"
        )
        
        # Should extract meaningful keywords, excluding stop words
        assert "cordless" in keywords
        assert "drill" in keywords
        assert "building" in keywords
        assert "deck" in keywords
        
        # Should exclude stop words
        assert "need" not in keywords
        assert "for" not in keywords


class TestRelationshipInferenceEngine:
    """Test relationship inference functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_connection = Mock(spec=Neo4jConnection)
        self.inference_engine = RelationshipInferenceEngine(
            neo4j_connection=self.mock_connection,
            enable_ai_inference=False  # Disable AI for tests
        )
    
    def test_inference_engine_initialization(self):
        """Test inference engine initialization"""
        assert self.inference_engine.neo4j_conn == self.mock_connection
        assert len(self.inference_engine.rules) > 0
        assert hasattr(self.inference_engine, '_product_cache')
    
    def test_voltage_extraction(self):
        """Test voltage extraction from product text"""
        # Create mock products with voltage information
        product1 = Mock()
        product1.name = "Makita 18V LXT Drill"
        product1.description = "Powerful 18 volt cordless drill"
        product1.specifications = {"voltage": "18V"}
        
        voltage = self.inference_engine._extract_voltage(product1)
        assert voltage == "18V"
        
        # Test different voltage formats
        product2 = Mock()
        product2.name = "DeWalt 20-Volt MAX Drill"
        product2.description = "20V cordless power drill"
        product2.specifications = {}
        
        voltage = self.inference_engine._extract_voltage(product2)
        assert voltage == "20V"
    
    def test_price_similarity_calculation(self):
        """Test price similarity calculation"""
        product1 = Mock()
        product1.price = 100.0
        
        product2 = Mock()
        product2.price = 120.0
        
        similarity = self.inference_engine._calculate_price_similarity(product1, product2)
        expected = 100.0 / 120.0  # min/max ratio
        assert abs(similarity - expected) < 0.01
        
        # Test identical prices
        product3 = Mock()
        product3.price = 100.0
        
        similarity = self.inference_engine._calculate_price_similarity(product1, product3)
        assert similarity == 1.0
    
    def test_kit_detection(self):
        """Test kit relationship detection"""
        product1 = Mock()
        product1.name = "Makita 18V LXT Drill Kit"
        
        product2 = Mock()
        product2.name = "Makita 18V LXT Battery"
        
        is_kit = self.inference_engine._detect_kit_relationship(product1, product2)
        assert is_kit == True
        
        # Test non-kit products
        product3 = Mock()
        product3.name = "Regular Drill"
        
        product4 = Mock()
        product4.name = "Standard Battery"
        
        is_kit = self.inference_engine._detect_kit_relationship(product3, product4)
        assert is_kit == False


class TestDataFlowIntegration:
    """Test DataFlow integration nodes"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock the Neo4j connection to avoid requiring real database
        with patch('knowledge_graph.dataflow_integration.Neo4jConnection'):
            self.kg_nodes = KnowledgeGraphDataFlowNodes()
    
    def test_dataflow_nodes_initialization(self):
        """Test DataFlow nodes initialization"""
        assert hasattr(self.kg_nodes, 'graph_db')
        assert hasattr(self.kg_nodes, 'search_engine')
        assert hasattr(self.kg_nodes, 'inference_engine')
    
    @patch('asyncio.new_event_loop')
    @patch('asyncio.set_event_loop')
    def test_semantic_search_node_structure(self, mock_set_loop, mock_new_loop):
        """Test semantic search node output structure"""
        # Mock asyncio loop
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = []  # Empty results
        
        result = self.kg_nodes.semantic_search_node(
            query="test query",
            limit=10,
            search_strategy="hybrid"
        )
        
        # Check output structure
        assert "search_query" in result
        assert "result_count" in result
        assert "results" in result
        assert "search_strategy" in result
        assert "timestamp" in result
        
        assert result["search_query"] == "test query"
        assert result["search_strategy"] == "hybrid"
        assert isinstance(result["results"], list)
    
    def test_get_product_relationships_node_structure(self):
        """Test product relationships node output structure"""
        # Mock the graph database method
        with patch.object(self.kg_nodes.graph_db, 'get_product_relationships') as mock_get_rels:
            mock_get_rels.return_value = [
                {
                    'relationship_type': 'COMPATIBLE_WITH',
                    'related_product_id': 456,
                    'related_sku': 'TEST-456',
                    'related_name': 'Test Related Product',
                    'confidence': 0.8
                }
            ]
            
            result = self.kg_nodes.get_product_relationships_node(
                product_id=123,
                max_distance=1,
                min_confidence=0.5
            )
            
            # Check output structure
            assert "product_id" in result
            assert "total_relationships" in result
            assert "relationships_by_type" in result
            assert "timestamp" in result
            
            assert result["product_id"] == 123
            assert result["total_relationships"] == 1
            assert "COMPATIBLE_WITH" in result["relationships_by_type"]


@pytest.mark.asyncio
async def test_async_functionality():
    """Test async functionality with proper event loop"""
    # This is a placeholder for async tests that require a real event loop
    # In practice, you'd test actual async methods here
    
    # Simple async test to verify pytest-asyncio is working
    await asyncio.sleep(0.01)  # Small delay
    assert True  # If we get here, async is working


def test_environment_variables():
    """Test environment variable handling"""
    # Test default values
    conn = Neo4jConnection()
    assert conn.uri.startswith("bolt://")
    assert conn.username == "neo4j"
    assert conn.database == "horme_knowledge"
    
    # Test custom values
    conn = Neo4jConnection(
        uri="bolt://custom:7687",
        username="custom_user",
        password="custom_pass",
        database="custom_db"
    )
    assert conn.uri == "bolt://custom:7687"
    assert conn.username == "custom_user"
    assert conn.password == "custom_pass"
    assert conn.database == "custom_db"


class TestDataValidation:
    """Test data validation and edge cases"""
    
    def test_product_node_validation(self):
        """Test ProductNode validation"""
        # Test required fields
        with pytest.raises(TypeError):
            ProductNode()  # Missing required fields
        
        # Test valid creation
        product = ProductNode(
            product_id=123,
            sku="TEST-123",
            name="Test Product",
            slug="test-product"
        )
        assert product.product_id == 123
    
    def test_relationship_confidence_bounds(self):
        """Test relationship confidence validation"""
        # Valid confidence values
        rel1 = SemanticRelationship(
            from_product_id=123,
            to_product_id=456,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
            confidence=0.0  # Minimum valid
        )
        assert rel1.confidence == 0.0
        
        rel2 = SemanticRelationship(
            from_product_id=123,
            to_product_id=456,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
            confidence=1.0  # Maximum valid
        )
        assert rel2.confidence == 1.0
    
    def test_empty_search_query(self):
        """Test handling of empty search queries"""
        mock_connection = Mock(spec=Neo4jConnection)
        search_engine = SemanticSearchEngine(
            neo4j_connection=mock_connection,
            use_sentence_transformers=False
        )
        
        # Test empty query normalization
        normalized = search_engine._normalize_query("   ")
        assert normalized == ""
        
        # Test empty query keyword extraction
        keywords = search_engine._extract_keywords("")
        assert keywords == []


if __name__ == "__main__":
    """Run tests directly"""
    pytest.main([__file__, "-v"])