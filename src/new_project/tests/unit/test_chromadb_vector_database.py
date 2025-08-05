"""
Unit Tests for ChromaDB Vector Database Operations
================================================

Tests the ChromaDB vector database service with mocking for fast unit tests.
Validates embedding operations, collection management, and similarity search.

Test Coverage:
- Vector database collection management
- Embedding creation and storage
- Similarity search operations
- Metadata filtering and querying
- Error handling and edge cases
- Performance constraints (<1s per test)
"""

import pytest
import time
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional, Tuple

# Test framework imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import windows_patch  # Apply Windows compatibility for Kailash SDK

# Import the service under test (will be implemented)
from src.new_project.core.services.vector_database import VectorDatabaseService, ChromaDBCollections
from src.new_project.core.models.vector_database import ProductEmbedding, ManualEmbedding, SafetyEmbedding, ProjectEmbedding


class TestChromaDBCollections:
    """Test ChromaDB collection configuration and management"""
    
    def test_collection_types_defined(self):
        """Test that all required collection types are defined"""
        collections = ChromaDBCollections()
        
        expected_collections = [
            "products", "manuals", "safety_guidelines", "project_patterns"
        ]
        actual_collections = collections.get_collection_names()
        
        assert set(expected_collections) == set(actual_collections), \
            f"Expected collections {expected_collections}, got {actual_collections}"
    
    def test_product_collection_config(self):
        """Test product collection configuration"""
        collections = ChromaDBCollections()
        
        config = collections.get_collection_config("products")
        
        assert config["name"] == "products"
        assert config["embedding_dimension"] == 1536  # OpenAI ada-002 dimension
        assert "metadata_schema" in config
        assert "description" in config
        
        # Validate metadata schema
        metadata_schema = config["metadata_schema"]
        expected_fields = ["product_code", "category", "brand", "price", "specifications"]
        for field in expected_fields:
            assert field in metadata_schema
    
    def test_manual_collection_config(self):
        """Test manual collection configuration"""
        collections = ChromaDBCollections()
        
        config = collections.get_collection_config("manuals")
        
        assert config["name"] == "manuals"
        assert config["embedding_dimension"] == 1536
        assert "metadata_schema" in config
        
        # Validate metadata schema
        metadata_schema = config["metadata_schema"]
        expected_fields = ["manual_id", "product_code", "section", "page_number", "content_type"]
        for field in expected_fields:
            assert field in metadata_schema
    
    def test_safety_collection_config(self):
        """Test safety guidelines collection configuration"""
        collections = ChromaDBCollections()
        
        config = collections.get_collection_config("safety_guidelines")
        
        assert config["name"] == "safety_guidelines"
        assert config["embedding_dimension"] == 1536
        assert "metadata_schema" in config
        
        # Validate metadata schema
        metadata_schema = config["metadata_schema"]
        expected_fields = ["guideline_id", "osha_code", "ansi_standard", "severity", "category"]
        for field in expected_fields:
            assert field in metadata_schema
    
    def test_project_collection_config(self):
        """Test project patterns collection configuration"""
        collections = ChromaDBCollections()
        
        config = collections.get_collection_config("project_patterns")
        
        assert config["name"] == "project_patterns"
        assert config["embedding_dimension"] == 1536
        assert "metadata_schema" in config
        
        # Validate metadata schema
        metadata_schema = config["metadata_schema"]
        expected_fields = ["pattern_id", "project_type", "difficulty", "tools_required", "estimated_time"]
        for field in expected_fields:
            assert field in metadata_schema


class TestVectorDatabaseService:
    """Test VectorDatabaseService operations with mocking"""
    
    @pytest.fixture
    def mock_chromadb_client(self):
        """Mock ChromaDB client for unit tests"""
        with patch('core.services.vector_database.chromadb.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            
            # Mock client methods
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_client.list_collections.return_value = []
            mock_client_class.return_value = mock_client
            
            yield mock_client, mock_collection
    
    @pytest.fixture
    def vector_database_service(self, mock_chromadb_client):
        """Create VectorDatabaseService with mocked ChromaDB client"""
        mock_client, mock_collection = mock_chromadb_client
        
        service = VectorDatabaseService(
            persist_directory="./test_chroma_db",
            client_settings={"allow_reset": True}
        )
        return service, mock_client, mock_collection
    
    def test_service_initialization(self, vector_database_service):
        """Test service initializes with proper configuration"""
        service, mock_client, mock_collection = vector_database_service
        
        assert service is not None
        assert service.persist_directory == "./test_chroma_db"
        assert hasattr(service, 'client')
        assert hasattr(service, 'collections')
    
    def test_create_collection(self, vector_database_service):
        """Test creating a new collection"""
        service, mock_client, mock_collection = vector_database_service
        
        collection_name = "test_collection"
        embedding_dimension = 1536
        
        # Mock successful collection creation
        mock_client.get_or_create_collection.return_value = mock_collection
        
        result = service.create_collection(collection_name, embedding_dimension)
        
        # Verify collection was created
        mock_client.get_or_create_collection.assert_called_once()
        args, kwargs = mock_client.get_or_create_collection.call_args
        assert args[0] == collection_name
        
        assert result == mock_collection
    
    def test_add_product_embedding(self, vector_database_service):
        """Test adding a product embedding to the collection"""
        service, mock_client, mock_collection = vector_database_service
        
        product_data = {
            "product_code": "TOOL-001",
            "name": "Circular Saw",
            "description": "15-amp circular saw with 7.25-inch blade",
            "category": "cutting_tools",
            "brand": "DeWalt",
            "price": 199.99,
            "specifications": {"power": "15-amp", "blade_diameter": "7.25-inch"}
        }
        
        # Mock embedding generation
        mock_embedding = np.random.rand(1536).astype(np.float32).tolist()
        with patch.object(service, '_generate_embedding', return_value=mock_embedding):
            service.add_product_embedding(product_data)
        
        # Verify embedding was added to collection
        mock_collection.add.assert_called_once()
        args, kwargs = mock_collection.add.call_args
        
        assert "embeddings" in kwargs
        assert "documents" in kwargs
        assert "metadatas" in kwargs
        assert "ids" in kwargs
        
        # Verify metadata structure
        metadata = kwargs["metadatas"][0]
        assert metadata["product_code"] == "TOOL-001"
        assert metadata["category"] == "cutting_tools"
        assert metadata["brand"] == "DeWalt"
        assert metadata["price"] == 199.99
    
    def test_add_manual_embedding(self, vector_database_service):
        """Test adding a manual embedding to the collection"""
        service, mock_client, mock_collection = vector_database_service
        
        manual_data = {
            "manual_id": "MAN-001",
            "product_code": "TOOL-001",
            "section": "Safety Instructions",
            "page_number": 5,
            "content": "Always wear safety glasses when operating this tool...",
            "content_type": "safety"
        }
        
        # Mock embedding generation
        mock_embedding = np.random.rand(1536).astype(np.float32).tolist()
        with patch.object(service, '_generate_embedding', return_value=mock_embedding):
            service.add_manual_embedding(manual_data)
        
        # Verify embedding was added to collection
        mock_collection.add.assert_called_once()
        args, kwargs = mock_collection.add.call_args
        
        # Verify metadata structure
        metadata = kwargs["metadatas"][0]
        assert metadata["manual_id"] == "MAN-001"
        assert metadata["product_code"] == "TOOL-001"
        assert metadata["section"] == "Safety Instructions"
        assert metadata["content_type"] == "safety"
    
    def test_add_safety_embedding(self, vector_database_service):
        """Test adding a safety guideline embedding to the collection"""
        service, mock_client, mock_collection = vector_database_service
        
        safety_data = {
            "guideline_id": "SAFE-001",
            "osha_code": "1926.95",
            "ansi_standard": "Z87.1",
            "title": "Eye Protection Requirements",
            "content": "Eye protection is required when operating power tools that may produce flying debris...",
            "severity": "high",
            "category": "personal_protective_equipment"
        }
        
        # Mock embedding generation
        mock_embedding = np.random.rand(1536).astype(np.float32).tolist()
        with patch.object(service, '_generate_embedding', return_value=mock_embedding):
            service.add_safety_embedding(safety_data)
        
        # Verify embedding was added to collection
        mock_collection.add.assert_called_once()
        args, kwargs = mock_collection.add.call_args
        
        # Verify metadata structure
        metadata = kwargs["metadatas"][0]
        assert metadata["guideline_id"] == "SAFE-001"
        assert metadata["osha_code"] == "1926.95"
        assert metadata["severity"] == "high"
        assert metadata["category"] == "personal_protective_equipment"
    
    def test_add_project_pattern_embedding(self, vector_database_service):
        """Test adding a project pattern embedding to the collection"""
        service, mock_client, mock_collection = vector_database_service
        
        project_data = {
            "pattern_id": "PROJ-001",
            "project_type": "deck_building",
            "title": "Basic Deck Construction",
            "description": "Step-by-step guide for building a simple rectangular deck...",
            "difficulty": "intermediate",
            "tools_required": ["circular_saw", "drill", "level", "measuring_tape"],
            "estimated_time": 480,  # minutes
            "materials": ["pressure_treated_lumber", "deck_screws", "concrete_blocks"]
        }
        
        # Mock embedding generation
        mock_embedding = np.random.rand(1536).astype(np.float32).tolist()
        with patch.object(service, '_generate_embedding', return_value=mock_embedding):
            service.add_project_pattern_embedding(project_data)
        
        # Verify embedding was added to collection
        mock_collection.add.assert_called_once()
        args, kwargs = mock_collection.add.call_args
        
        # Verify metadata structure
        metadata = kwargs["metadatas"][0]
        assert metadata["pattern_id"] == "PROJ-001"
        assert metadata["project_type"] == "deck_building"
        assert metadata["difficulty"] == "intermediate"
        assert metadata["estimated_time"] == 480
    
    def test_similarity_search_products(self, vector_database_service):
        """Test similarity search for products"""
        service, mock_client, mock_collection = vector_database_service
        
        query_text = "circular saw for cutting wood"
        n_results = 5
        
        # Mock search results
        mock_results = {
            "ids": [["TOOL-001", "TOOL-002", "TOOL-003"]],
            "distances": [[0.1, 0.2, 0.3]],
            "metadatas": [[
                {"product_code": "TOOL-001", "name": "Circular Saw", "category": "cutting_tools"},
                {"product_code": "TOOL-002", "name": "Jigsaw", "category": "cutting_tools"},
                {"product_code": "TOOL-003", "name": "Hand Saw", "category": "hand_tools"}
            ]],
            "documents": [["Circular saw description", "Jigsaw description", "Hand saw description"]]
        }
        
        # Mock embedding generation and collection query
        mock_embedding = np.random.rand(1536).astype(np.float32).tolist()
        with patch.object(service, '_generate_embedding', return_value=mock_embedding):
            mock_collection.query.return_value = mock_results
            
            results = service.similarity_search_products(query_text, n_results)
        
        # Verify query was called
        mock_collection.query.assert_called_once()
        args, kwargs = mock_collection.query.call_args
        assert kwargs["n_results"] == n_results
        assert "query_embeddings" in kwargs
        
        # Verify results structure
        assert len(results) == 3
        assert results[0]["product_code"] == "TOOL-001"
        assert results[0]["similarity_score"] == 0.9  # 1 - 0.1 distance
        assert results[1]["similarity_score"] == 0.8  # 1 - 0.2 distance
    
    def test_similarity_search_with_filters(self, vector_database_service):
        """Test similarity search with metadata filters"""
        service, mock_client, mock_collection = vector_database_service
        
        query_text = "safety equipment"
        filters = {"category": "safety", "price": {"$lt": 100}}
        n_results = 3
        
        # Mock search results
        mock_results = {
            "ids": [["SAFE-001", "SAFE-002"]],
            "distances": [[0.15, 0.25]],
            "metadatas": [[
                {"product_code": "SAFE-001", "name": "Safety Glasses", "category": "safety", "price": 25.99},
                {"product_code": "SAFE-002", "name": "Hard Hat", "category": "safety", "price": 45.00}
            ]],
            "documents": [["Safety glasses description", "Hard hat description"]]
        }
        
        # Mock embedding generation and collection query
        mock_embedding = np.random.rand(1536).astype(np.float32).tolist()
        with patch.object(service, '_generate_embedding', return_value=mock_embedding):
            mock_collection.query.return_value = mock_results
            
            results = service.similarity_search_products(query_text, n_results, filters)
        
        # Verify query was called with filters
        mock_collection.query.assert_called_once()
        args, kwargs = mock_collection.query.call_args
        assert kwargs["where"] == filters
        
        # Verify results
        assert len(results) == 2
        assert all(result["category"] == "safety" for result in results)
        assert all(result["price"] < 100 for result in results)
    
    def test_batch_add_embeddings(self, vector_database_service):
        """Test batch adding multiple embeddings"""
        service, mock_client, mock_collection = vector_database_service
        
        products_batch = [
            {
                "product_code": "TOOL-001",
                "name": "Circular Saw",
                "description": "15-amp circular saw",
                "category": "cutting_tools"
            },
            {
                "product_code": "TOOL-002", 
                "name": "Drill",
                "description": "Cordless drill with battery",
                "category": "drilling_tools"
            }
        ]
        
        # Mock embedding generation
        mock_embeddings = [
            np.random.rand(1536).astype(np.float32).tolist(),
            np.random.rand(1536).astype(np.float32).tolist()
        ]
        with patch.object(service, '_generate_embedding', side_effect=mock_embeddings):
            service.batch_add_product_embeddings(products_batch)
        
        # Verify batch add was called
        mock_collection.add.assert_called_once()
        args, kwargs = mock_collection.add.call_args
        
        assert len(kwargs["embeddings"]) == 2
        assert len(kwargs["documents"]) == 2
        assert len(kwargs["metadatas"]) == 2
        assert len(kwargs["ids"]) == 2
    
    def test_delete_embedding(self, vector_database_service):
        """Test deleting an embedding from collection"""
        service, mock_client, mock_collection = vector_database_service
        
        product_id = "TOOL-001"
        
        service.delete_product_embedding(product_id)
        
        # Verify delete was called
        mock_collection.delete.assert_called_once()
        args, kwargs = mock_collection.delete.call_args
        assert kwargs["ids"] == [product_id]
    
    def test_update_embedding(self, vector_database_service):
        """Test updating an existing embedding"""
        service, mock_client, mock_collection = vector_database_service
        
        updated_product_data = {
            "product_code": "TOOL-001",
            "name": "Updated Circular Saw",
            "description": "Updated 15-amp circular saw with new features",
            "category": "cutting_tools",
            "price": 249.99
        }
        
        # Mock embedding generation
        mock_embedding = np.random.rand(1536).astype(np.float32).tolist()
        with patch.object(service, '_generate_embedding', return_value=mock_embedding):
            service.update_product_embedding(updated_product_data)
        
        # Verify update was called (delete + add)
        mock_collection.delete.assert_called_once()
        mock_collection.add.assert_called_once()
    
    def test_get_collection_stats(self, vector_database_service):
        """Test getting collection statistics"""
        service, mock_client, mock_collection = vector_database_service
        
        # Mock collection count
        mock_collection.count.return_value = 150
        
        stats = service.get_collection_stats("products")
        
        assert stats["collection_name"] == "products"
        assert stats["total_embeddings"] == 150
        assert "created_at" in stats
    
    def test_error_handling_invalid_embedding_dimension(self, vector_database_service):
        """Test error handling for invalid embedding dimensions"""
        service, mock_client, mock_collection = vector_database_service
        
        # Mock embedding with wrong dimension
        wrong_dimension_embedding = np.random.rand(512).astype(np.float32).tolist()  # Should be 1536
        
        product_data = {
            "product_code": "TOOL-001",
            "name": "Test Tool",
            "description": "Test description",
            "category": "test"
        }
        
        with patch.object(service, '_generate_embedding', return_value=wrong_dimension_embedding):
            with pytest.raises(ValueError) as exc_info:
                service.add_product_embedding(product_data)
            
            assert "embedding dimension" in str(exc_info.value).lower()
    
    def test_error_handling_missing_required_fields(self, vector_database_service):
        """Test error handling for missing required fields"""
        service, mock_client, mock_collection = vector_database_service
        
        # Product data missing required fields
        incomplete_product_data = {
            "name": "Incomplete Product"
            # Missing: product_code, description, category
        }
        
        with pytest.raises(ValueError) as exc_info:
            service.add_product_embedding(incomplete_product_data)
        
        assert "required field" in str(exc_info.value).lower()
    
    def test_error_handling_collection_not_found(self, vector_database_service):
        """Test error handling when collection doesn't exist"""
        service, mock_client, mock_collection = vector_database_service
        
        # Mock collection not found
        mock_client.get_or_create_collection.side_effect = Exception("Collection not found")
        
        with pytest.raises(Exception) as exc_info:
            service.similarity_search_products("test query", 5)
        
        assert "Collection not found" in str(exc_info.value)


class TestVectorDatabasePerformance:
    """Test performance requirements for vector database operations"""
    
    @pytest.fixture
    def vector_database_service(self):
        """Create VectorDatabaseService with mocked fast responses"""
        with patch('core.services.vector_database.chromadb.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            
            # Mock fast responses
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_collection.add.return_value = None
            mock_collection.query.return_value = {
                "ids": [["TOOL-001"]],
                "distances": [[0.1]],
                "metadatas": [[{"product_code": "TOOL-001"}]],
                "documents": [["test"]]
            }
            
            mock_client_class.return_value = mock_client
            
            service = VectorDatabaseService()
            return service, mock_client, mock_collection
    
    def test_embedding_creation_performance(self, vector_database_service, performance_monitor):
        """Test that embedding creation completes within performance threshold"""
        service, mock_client, mock_collection = vector_database_service
        
        product_data = {
            "product_code": "PERF-001",
            "name": "Performance Test Tool",
            "description": "Tool for performance testing",
            "category": "test"
        }
        
        # Mock fast embedding generation
        mock_embedding = np.random.rand(1536).astype(np.float32).tolist()
        with patch.object(service, '_generate_embedding', return_value=mock_embedding):
            # Measure performance
            performance_monitor.start("embedding_creation")
            service.add_product_embedding(product_data)
            duration = performance_monitor.stop("embedding_creation")
        
        # Assert performance requirement
        performance_monitor.assert_within_threshold(1.0, "embedding_creation")
    
    def test_similarity_search_performance(self, vector_database_service, performance_monitor):
        """Test that similarity search completes within performance threshold"""
        service, mock_client, mock_collection = vector_database_service
        
        # Mock fast embedding generation
        mock_embedding = np.random.rand(1536).astype(np.float32).tolist()
        with patch.object(service, '_generate_embedding', return_value=mock_embedding):
            # Measure performance
            performance_monitor.start("similarity_search")
            results = service.similarity_search_products("test query", 5)
            duration = performance_monitor.stop("similarity_search")
        
        # Assert performance requirement
        performance_monitor.assert_within_threshold(1.0, "similarity_search")
        assert len(results) > 0
    
    def test_batch_operations_performance(self, vector_database_service, performance_monitor):
        """Test that batch operations complete within performance threshold"""
        service, mock_client, mock_collection = vector_database_service
        
        # Create batch of 10 products
        products_batch = [
            {
                "product_code": f"BATCH-{i:03d}",
                "name": f"Batch Tool {i}",
                "description": f"Tool {i} for batch testing",
                "category": "test"
            }
            for i in range(10)
        ]
        
        # Mock fast embedding generation
        mock_embeddings = [np.random.rand(1536).astype(np.float32).tolist() for _ in range(10)]
        with patch.object(service, '_generate_embedding', side_effect=mock_embeddings):
            # Measure performance
            performance_monitor.start("batch_operations")
            service.batch_add_product_embeddings(products_batch)
            duration = performance_monitor.stop("batch_operations")
        
        # Assert performance requirement - batch operations can be slightly slower
        performance_monitor.assert_within_threshold(1.0, "batch_operations")


class TestVectorDatabaseModels:
    """Test data models for vector database entities"""
    
    def test_product_embedding_model(self):
        """Test ProductEmbedding model validation and serialization"""
        product_embedding = ProductEmbedding(
            product_code="TOOL-001",
            name="Circular Saw",
            description="15-amp circular saw with 7.25-inch blade",
            category="cutting_tools", 
            brand="DeWalt",
            price=199.99,
            specifications={"power": "15-amp", "blade_diameter": "7.25-inch"},
            embedding_vector=np.random.rand(1536).tolist()
        )
        
        assert product_embedding.product_code == "TOOL-001"
        assert product_embedding.category == "cutting_tools"
        assert len(product_embedding.embedding_vector) == 1536
        
        # Test serialization for ChromaDB
        metadata = product_embedding.to_metadata()
        assert metadata["product_code"] == "TOOL-001"
        assert metadata["brand"] == "DeWalt"
        assert metadata["price"] == 199.99
    
    def test_manual_embedding_model(self):
        """Test ManualEmbedding model validation and serialization"""
        manual_embedding = ManualEmbedding(
            manual_id="MAN-001",
            product_code="TOOL-001",
            section="Safety Instructions",
            page_number=5,
            content="Always wear safety glasses when operating this tool...",
            content_type="safety",
            embedding_vector=np.random.rand(1536).tolist()
        )
        
        assert manual_embedding.manual_id == "MAN-001"
        assert manual_embedding.section == "Safety Instructions"
        assert manual_embedding.content_type == "safety"
        
        # Test serialization for ChromaDB
        metadata = manual_embedding.to_metadata()
        assert metadata["manual_id"] == "MAN-001"
        assert metadata["page_number"] == 5
    
    def test_safety_embedding_model(self):
        """Test SafetyEmbedding model validation and serialization"""
        safety_embedding = SafetyEmbedding(
            guideline_id="SAFE-001",
            osha_code="1926.95",
            ansi_standard="Z87.1",
            title="Eye Protection Requirements",
            content="Eye protection is required...",
            severity="high",
            category="personal_protective_equipment",
            embedding_vector=np.random.rand(1536).tolist()
        )
        
        assert safety_embedding.guideline_id == "SAFE-001"
        assert safety_embedding.osha_code == "1926.95"
        assert safety_embedding.severity == "high"
        
        # Test serialization for ChromaDB
        metadata = safety_embedding.to_metadata()
        assert metadata["guideline_id"] == "SAFE-001"
        assert metadata["severity"] == "high"
    
    def test_project_embedding_model(self):
        """Test ProjectEmbedding model validation and serialization"""
        project_embedding = ProjectEmbedding(
            pattern_id="PROJ-001",
            project_type="deck_building",
            title="Basic Deck Construction",
            description="Step-by-step guide for building a deck...",
            difficulty="intermediate",
            tools_required=["circular_saw", "drill", "level"],
            estimated_time=480,
            materials=["lumber", "screws", "concrete_blocks"],
            embedding_vector=np.random.rand(1536).tolist()
        )
        
        assert project_embedding.pattern_id == "PROJ-001"
        assert project_embedding.project_type == "deck_building"
        assert project_embedding.difficulty == "intermediate"
        assert len(project_embedding.tools_required) == 3
        
        # Test serialization for ChromaDB
        metadata = project_embedding.to_metadata()
        assert metadata["pattern_id"] == "PROJ-001"
        assert metadata["estimated_time"] == 480
    
    def test_invalid_embedding_vector_dimension(self):
        """Test validation of embedding vector dimensions"""
        with pytest.raises(ValueError):
            ProductEmbedding(
                product_code="TOOL-001",
                name="Test Tool",
                description="Test description",
                category="test",
                embedding_vector=np.random.rand(512).tolist()  # Wrong dimension
            )
    
    def test_invalid_severity_level(self):
        """Test validation of safety severity levels"""
        with pytest.raises(ValueError):
            SafetyEmbedding(
                guideline_id="SAFE-001",
                osha_code="1926.95",
                ansi_standard="Z87.1",
                title="Test Safety Rule",
                content="Test content",
                severity="invalid",  # Should be low, medium, high, critical
                category="test",
                embedding_vector=np.random.rand(1536).tolist()
            )


if __name__ == "__main__":
    # Run unit tests with performance monitoring
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--durations=10",
        "-m", "unit"
    ])