"""
ChromaDB Vector Database Service
================================

Service for managing ChromaDB vector database operations including collection
management, embedding operations, and similarity search.
"""

from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
import time

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    # Mock classes for development/testing
    class chromadb:
        @staticmethod
        def Client(**kwargs):
            return MockChromaClient()
    
    class Settings:
        pass
    
    class MockChromaClient:
        def get_or_create_collection(self, name: str, **kwargs):
            return MockCollection(name)
        
        def list_collections(self):
            return []
    
    class MockCollection:
        def __init__(self, name):
            self.name = name
        
        def add(self, **kwargs):
            pass
        
        def query(self, **kwargs):
            return {
                "ids": [["mock_id"]],
                "distances": [[0.1]],
                "metadatas": [[{"name": "mock_item"}]],
                "documents": [["mock_document"]]
            }
        
        def delete(self, **kwargs):
            pass
        
        def count(self):
            return 0

from ..models.vector_database import ProductEmbedding, ManualEmbedding, SafetyEmbedding, ProjectEmbedding

logger = logging.getLogger(__name__)


@dataclass
class ChromaDBCollections:
    """ChromaDB collections configuration and management"""
    
    def __init__(self):
        self.collections_config = {
            "products": {
                "name": "products",
                "description": "Product embeddings for tool recommendations",
                "embedding_dimension": 1536,
                "metadata_schema": {
                    "product_code": "string",
                    "category": "string",
                    "brand": "string",
                    "price": "float",
                    "specifications": "string"
                }
            },
            "manuals": {
                "name": "manuals",
                "description": "Manual and documentation embeddings",
                "embedding_dimension": 1536,
                "metadata_schema": {
                    "manual_id": "string",
                    "product_code": "string",
                    "section": "string",
                    "page_number": "integer",
                    "content_type": "string"
                }
            },
            "safety_guidelines": {
                "name": "safety_guidelines",
                "description": "Safety guideline and compliance embeddings",
                "embedding_dimension": 1536,
                "metadata_schema": {
                    "guideline_id": "string",
                    "osha_code": "string",
                    "ansi_standard": "string",
                    "severity": "string",
                    "category": "string"
                }
            },
            "project_patterns": {
                "name": "project_patterns",
                "description": "Project pattern and template embeddings",
                "embedding_dimension": 1536,
                "metadata_schema": {
                    "pattern_id": "string",
                    "project_type": "string",
                    "difficulty": "string",
                    "tools_required": "array",
                    "estimated_time": "integer"
                }
            }
        }
    
    def get_collection_names(self) -> List[str]:
        """Get list of all collection names"""
        return list(self.collections_config.keys())
    
    def get_collection_config(self, collection_name: str) -> Dict[str, Any]:
        """Get configuration for a specific collection"""
        if collection_name not in self.collections_config:
            raise ValueError(f"Unknown collection: {collection_name}")
        return self.collections_config[collection_name]
    
    def validate_collection_exists(self, collection_name: str) -> bool:
        """Validate that collection exists in configuration"""
        return collection_name in self.collections_config


class VectorDatabaseService:
    """Service for ChromaDB vector database operations"""
    
    def __init__(self, persist_directory: str = "./chroma_db", client_settings: Optional[Dict] = None):
        """Initialize ChromaDB connection"""
        self.persist_directory = persist_directory
        self.client_settings = client_settings or {}
        
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, using mock implementation")
        
        try:
            if CHROMADB_AVAILABLE:
                settings = Settings(
                    persist_directory=persist_directory,
                    **self.client_settings
                )
                self.client = chromadb.Client(settings)
            else:
                self.client = chromadb.Client()
            
            self.collections = ChromaDBCollections()
            logger.info(f"Connected to ChromaDB at {persist_directory}")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if ChromaDB connection is healthy"""
        try:
            collections = self.client.list_collections()
            return True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False
    
    def create_collection(self, collection_name: str, embedding_dimension: int = 1536) -> Any:
        """Create or get a ChromaDB collection"""
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"embedding_dimension": embedding_dimension}
            )
            logger.info(f"Created/accessed collection: {collection_name}")
            return collection
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (mock implementation for now)"""
        # This would normally use OpenAI embeddings or another embedding model
        # For now, return a mock embedding vector
        import random
        return [random.random() for _ in range(1536)]
    
    def add_product_embedding(self, product_data: Dict[str, Any]) -> None:
        """Add a product embedding to the products collection"""
        # Validate required fields
        required_fields = ["product_code", "name", "description", "category"]
        for field in required_fields:
            if field not in product_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Get or create products collection
        collection = self.create_collection("products")
        
        # Generate embedding
        document_text = f"{product_data['name']} {product_data['description']}"
        embedding = self._generate_embedding(document_text)
        
        # Validate embedding dimension
        if len(embedding) != 1536:
            raise ValueError(f"Invalid embedding dimension: {len(embedding)}, expected 1536")
        
        # Create product embedding model for validation
        product_embedding = ProductEmbedding(
            product_code=product_data["product_code"],
            name=product_data["name"],
            description=product_data["description"],
            category=product_data["category"],
            brand=product_data.get("brand"),
            price=product_data.get("price"),
            specifications=product_data.get("specifications", {}),
            embedding_vector=embedding
        )
        
        # Add to collection
        collection.add(
            embeddings=[embedding],
            documents=[product_embedding.to_document()],
            metadatas=[product_embedding.to_metadata()],
            ids=[product_data["product_code"]]
        )
        
        logger.info(f"Added product embedding: {product_data['product_code']}")
    
    def add_manual_embedding(self, manual_data: Dict[str, Any]) -> None:
        """Add a manual embedding to the manuals collection"""
        # Validate required fields
        required_fields = ["manual_id", "product_code", "section", "page_number", "content", "content_type"]
        for field in required_fields:
            if field not in manual_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Get or create manuals collection
        collection = self.create_collection("manuals")
        
        # Generate embedding
        embedding = self._generate_embedding(manual_data["content"])
        
        # Create manual embedding model for validation
        manual_embedding = ManualEmbedding(
            manual_id=manual_data["manual_id"],
            product_code=manual_data["product_code"],
            section=manual_data["section"],
            page_number=manual_data["page_number"],
            content=manual_data["content"],
            content_type=manual_data["content_type"],
            embedding_vector=embedding
        )
        
        # Add to collection
        collection.add(
            embeddings=[embedding],
            documents=[manual_embedding.to_document()],
            metadatas=[manual_embedding.to_metadata()],
            ids=[manual_data["manual_id"]]
        )
        
        logger.info(f"Added manual embedding: {manual_data['manual_id']}")
    
    def add_safety_embedding(self, safety_data: Dict[str, Any]) -> None:
        """Add a safety guideline embedding to the safety_guidelines collection"""
        # Validate required fields
        required_fields = ["guideline_id", "osha_code", "ansi_standard", "title", "content", "severity", "category"]
        for field in required_fields:
            if field not in safety_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Get or create safety_guidelines collection
        collection = self.create_collection("safety_guidelines")
        
        # Generate embedding
        embedding_text = f"{safety_data['title']} {safety_data['content']}"
        embedding = self._generate_embedding(embedding_text)
        
        # Create safety embedding model for validation
        safety_embedding = SafetyEmbedding(
            guideline_id=safety_data["guideline_id"],
            osha_code=safety_data["osha_code"],
            ansi_standard=safety_data["ansi_standard"],
            title=safety_data["title"],
            content=safety_data["content"],
            severity=safety_data["severity"],
            category=safety_data["category"],
            embedding_vector=embedding
        )
        
        # Add to collection
        collection.add(
            embeddings=[embedding],
            documents=[safety_embedding.to_document()],
            metadatas=[safety_embedding.to_metadata()],
            ids=[safety_data["guideline_id"]]
        )
        
        logger.info(f"Added safety embedding: {safety_data['guideline_id']}")
    
    def add_project_pattern_embedding(self, project_data: Dict[str, Any]) -> None:
        """Add a project pattern embedding to the project_patterns collection"""
        # Validate required fields
        required_fields = ["pattern_id", "project_type", "title", "description", "difficulty", "tools_required", "estimated_time", "materials"]
        for field in required_fields:
            if field not in project_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Get or create project_patterns collection
        collection = self.create_collection("project_patterns")
        
        # Generate embedding
        embedding_text = f"{project_data['title']} {project_data['description']}"
        embedding = self._generate_embedding(embedding_text)
        
        # Create project embedding model for validation
        project_embedding = ProjectEmbedding(
            pattern_id=project_data["pattern_id"],
            project_type=project_data["project_type"],
            title=project_data["title"],
            description=project_data["description"],
            difficulty=project_data["difficulty"],
            tools_required=project_data["tools_required"],
            estimated_time=project_data["estimated_time"],
            materials=project_data["materials"],
            embedding_vector=embedding
        )
        
        # Add to collection
        collection.add(
            embeddings=[embedding],
            documents=[project_embedding.to_document()],
            metadatas=[project_embedding.to_metadata()],
            ids=[project_data["pattern_id"]]
        )
        
        logger.info(f"Added project pattern embedding: {project_data['pattern_id']}")
    
    def similarity_search_products(self, query_text: str, n_results: int = 5, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Perform similarity search on products collection"""
        # Get products collection
        collection = self.create_collection("products")
        
        # Generate query embedding
        query_embedding = self._generate_embedding(query_text)
        
        # Perform search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters
        )
        
        # Process results
        search_results = []
        if results["ids"] and len(results["ids"]) > 0:
            for i, product_id in enumerate(results["ids"][0]):
                similarity_score = 1.0 - results["distances"][0][i]  # Convert distance to similarity
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                
                search_results.append({
                    "product_code": product_id,
                    "name": metadata.get("name", ""),
                    "category": metadata.get("category", ""),
                    "brand": metadata.get("brand", ""),
                    "price": metadata.get("price"),
                    "similarity_score": similarity_score
                })
        
        return search_results
    
    def batch_add_product_embeddings(self, products_batch: List[Dict[str, Any]]) -> None:
        """Add multiple product embeddings in batch"""
        if not products_batch:
            return
        
        # Get or create products collection
        collection = self.create_collection("products")
        
        embeddings = []
        documents = []
        metadatas = []
        ids = []
        
        for product_data in products_batch:
            # Validate required fields
            required_fields = ["product_code", "name", "description", "category"]
            for field in required_fields:
                if field not in product_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Generate embedding
            document_text = f"{product_data['name']} {product_data['description']}"
            embedding = self._generate_embedding(document_text)
            
            # Create product embedding model
            product_embedding = ProductEmbedding(
                product_code=product_data["product_code"],
                name=product_data["name"],
                description=product_data["description"],
                category=product_data["category"],
                brand=product_data.get("brand"),
                price=product_data.get("price"),
                specifications=product_data.get("specifications", {}),
                embedding_vector=embedding
            )
            
            embeddings.append(embedding)
            documents.append(product_embedding.to_document())
            metadatas.append(product_embedding.to_metadata())
            ids.append(product_data["product_code"])
        
        # Add batch to collection
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(products_batch)} product embeddings in batch")
    
    def delete_product_embedding(self, product_id: str) -> None:
        """Delete a product embedding from the collection"""
        collection = self.create_collection("products")
        collection.delete(ids=[product_id])
        logger.info(f"Deleted product embedding: {product_id}")
    
    def update_product_embedding(self, updated_product_data: Dict[str, Any]) -> None:
        """Update an existing product embedding"""
        product_code = updated_product_data.get("product_code")
        if not product_code:
            raise ValueError("Product code required for update")
        
        # Delete existing
        self.delete_product_embedding(product_code)
        
        # Add updated version
        self.add_product_embedding(updated_product_data)
        
        logger.info(f"Updated product embedding: {product_code}")
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection"""
        collection = self.create_collection(collection_name)
        
        try:
            count = collection.count()
        except:
            count = 0
        
        return {
            "collection_name": collection_name,
            "total_embeddings": count,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }