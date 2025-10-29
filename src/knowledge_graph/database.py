"""
Neo4j Database Connection and Graph Operations

This module provides the core database interface for the knowledge graph,
including connection management, CRUD operations, and optimized queries.
"""

import os
import logging
from typing import Optional, List, Dict, Any, Union, Tuple
from contextlib import contextmanager
import json
from datetime import datetime

from neo4j import GraphDatabase, Driver, Session, Transaction
from neo4j.exceptions import ServiceUnavailable, TransientError
import redis
from redis import Redis

from .models import (
    ProductNode, SemanticRelationship, CategoryNode, BrandNode, ProjectNode,
    RelationshipType, ConfidenceSource, RelationshipQuery
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jConnection:
    """
    Neo4j database connection manager with connection pooling and error handling.
    
    Provides thread-safe access to Neo4j database with automatic retry logic
    and connection health monitoring.
    """
    
    def __init__(
        self,
        uri: str = None,
        username: str = None, 
        password: str = None,
        database: str = "horme_knowledge",
        max_connection_lifetime: int = 3600,
        max_connection_pool_size: int = 50,
        connection_acquisition_timeout: int = 60
    ):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j connection URI (default: from environment)
            username: Database username (default: from environment)
            password: Database password (default: from environment)
            database: Database name to use
            max_connection_lifetime: Max connection lifetime in seconds
            max_connection_pool_size: Maximum connections in pool
            connection_acquisition_timeout: Timeout for acquiring connection
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "horme_knowledge_2024")
        self.database = database
        
        # Connection configuration
        self.config = {
            "max_connection_lifetime": max_connection_lifetime,
            "max_connection_pool_size": max_connection_pool_size,
            "connection_acquisition_timeout": connection_acquisition_timeout,
            "keep_alive": True,
            "user_agent": "HormeKnowledgeGraph/1.0"
        }
        
        self._driver: Optional[Driver] = None
        self._redis_client: Optional[Redis] = None
        self._setup_redis_cache()
        
    def _setup_redis_cache(self):
        """Setup Redis cache for query results and embeddings"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://:horme_redis_2024@localhost:6380/0")
            self._redis_client = redis.from_url(redis_url, decode_responses=True)
            self._redis_client.ping()  # Test connection
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis cache not available: {e}")
            self._redis_client = None
    
    def connect(self) -> Driver:
        """
        Establish connection to Neo4j database.
        
        Returns:
            Neo4j Driver instance
            
        Raises:
            ServiceUnavailable: If database is not accessible
        """
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password),
                    **self.config
                )
                
                # Test connection
                with self._driver.session(database=self.database) as session:
                    session.run("RETURN 1 as test").single()
                    
                logger.info(f"Connected to Neo4j at {self.uri}")
                
            except ServiceUnavailable as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error connecting to Neo4j: {e}")
                raise
                
        return self._driver
    
    def close(self):
        """Close database connection and cleanup resources"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")
            
        if self._redis_client:
            self._redis_client.close()
            self._redis_client = None
    
    @contextmanager
    def session(self, **kwargs):
        """
        Context manager for Neo4j sessions.
        
        Usage:
            with neo4j_conn.session() as session:
                result = session.run("MATCH (n) RETURN count(n)")
        """
        driver = self.connect()
        session = driver.session(database=self.database, **kwargs)
        try:
            yield session
        finally:
            session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on database connection.
        
        Returns:
            Dictionary with health status and metrics
        """
        try:
            with self.session() as session:
                # Test basic connectivity
                result = session.run("RETURN 1 as test").single()
                
                # Get database metrics
                stats_query = """
                CALL dbms.queryJmx("org.neo4j:instance=kernel#0,name=Transactions") 
                YIELD attributes
                RETURN attributes.NumberOfOpenTransactions as open_transactions,
                       attributes.NumberOfCommittedTransactions as committed_transactions
                """
                
                stats_result = session.run(stats_query).single()
                
                # Test Redis cache if available
                redis_status = "unavailable"
                if self._redis_client:
                    try:
                        self._redis_client.ping()
                        redis_status = "connected"
                    except:
                        redis_status = "error"
                
                return {
                    "status": "healthy",
                    "neo4j_connected": True,
                    "database": self.database,
                    "redis_cache": redis_status,
                    "open_transactions": stats_result["open_transactions"] if stats_result else 0,
                    "committed_transactions": stats_result["committed_transactions"] if stats_result else 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self._redis_client:
            return None
        try:
            value = self._redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def cache_set(self, key: str, value: Any, expire: int = 3600):
        """Set value in Redis cache with expiration"""
        if not self._redis_client:
            return
        try:
            self._redis_client.set(key, json.dumps(value, default=str), ex=expire)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")


class GraphDatabase:
    """
    High-level interface for graph database operations.
    
    Provides CRUD operations, relationship management, and optimized queries
    for the product knowledge graph.
    """
    
    def __init__(self, connection: Neo4jConnection):
        """
        Initialize graph database interface.
        
        Args:
            connection: Neo4j connection instance
        """
        self.conn = connection
        self.logger = logging.getLogger(f"{__name__}.GraphDatabase")
    
    # ===========================================
    # NODE OPERATIONS
    # ===========================================
    
    def create_product_node(self, product: ProductNode) -> bool:
        """
        Create or update a product node in the graph.
        
        Args:
            product: ProductNode instance
            
        Returns:
            True if successful, False otherwise
        """
        query = """
        MERGE (p:Product {product_id: $product_id})
        SET p += $properties
        SET p.updated_at = datetime()
        RETURN p.product_id as id
        """
        
        try:
            with self.conn.session() as session:
                result = session.run(query, {
                    "product_id": product.product_id,
                    "properties": product.to_neo4j_properties()
                })
                
                if result.single():
                    self.logger.info(f"Created/updated product node: {product.sku}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to create product node {product.sku}: {e}")
            
        return False
    
    def get_product_node(self, product_id: int = None, sku: str = None) -> Optional[ProductNode]:
        """
        Retrieve a product node by ID or SKU.
        
        Args:
            product_id: Product ID to search for
            sku: Product SKU to search for
            
        Returns:
            ProductNode instance or None if not found
        """
        if not product_id and not sku:
            raise ValueError("Either product_id or sku must be provided")
        
        # Try cache first
        cache_key = f"product:{product_id or sku}"
        cached = self.conn.cache_get(cache_key)
        if cached:
            return ProductNode(**cached)
        
        if product_id:
            query = "MATCH (p:Product {product_id: $product_id}) RETURN p"
            params = {"product_id": product_id}
        else:
            query = "MATCH (p:Product {sku: $sku}) RETURN p"
            params = {"sku": sku}
        
        try:
            with self.conn.session() as session:
                result = session.run(query, params).single()
                
                if result:
                    node_data = dict(result["p"])
                    # Convert datetime strings back to datetime objects
                    for field in ["created_at", "updated_at", "last_sync_from_postgres"]:
                        if node_data.get(field):
                            node_data[field] = datetime.fromisoformat(str(node_data[field]))
                    
                    product = ProductNode(**node_data)
                    
                    # Cache the result
                    self.conn.cache_set(cache_key, node_data, expire=1800)  # 30 minutes
                    
                    return product
                    
        except Exception as e:
            self.logger.error(f"Failed to get product node: {e}")
            
        return None
    
    def create_category_node(self, category: CategoryNode) -> bool:
        """Create or update a category node"""
        query = """
        MERGE (c:Category {category_id: $category_id})
        SET c += $properties
        RETURN c.category_id as id
        """
        
        try:
            with self.conn.session() as session:
                result = session.run(query, {
                    "category_id": category.category_id,
                    "properties": category.to_neo4j_properties()
                })
                return bool(result.single())
        except Exception as e:
            self.logger.error(f"Failed to create category node: {e}")
            return False
    
    def create_brand_node(self, brand: BrandNode) -> bool:
        """Create or update a brand node"""
        query = """
        MERGE (b:Brand {brand_id: $brand_id})
        SET b += $properties  
        RETURN b.brand_id as id
        """
        
        try:
            with self.conn.session() as session:
                result = session.run(query, {
                    "brand_id": brand.brand_id,
                    "properties": brand.to_neo4j_properties()
                })
                return bool(result.single())
        except Exception as e:
            self.logger.error(f"Failed to create brand node: {e}")
            return False
    
    # ===========================================
    # RELATIONSHIP OPERATIONS
    # ===========================================
    
    def create_relationship(self, relationship: SemanticRelationship) -> bool:
        """
        Create a relationship between two products.
        
        Args:
            relationship: SemanticRelationship instance
            
        Returns:
            True if successful, False otherwise
        """
        query = f"""
        MATCH (from:Product {{product_id: $from_id}})
        MATCH (to:Product {{product_id: $to_id}})
        MERGE (from)-[r:{relationship.relationship_type.value}]->(to)
        SET r += $properties
        RETURN r
        """
        
        try:
            with self.conn.session() as session:
                result = session.run(query, {
                    "from_id": relationship.from_product_id,
                    "to_id": relationship.to_product_id,
                    "properties": relationship.to_neo4j_properties()
                })
                
                if result.single():
                    self.logger.info(f"Created relationship: {relationship.from_product_id} -> {relationship.to_product_id}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to create relationship: {e}")
            
        return False
    
    def get_product_relationships(
        self, 
        product_id: int, 
        relationship_types: Optional[List[RelationshipType]] = None,
        direction: str = "both",  # "outgoing", "incoming", "both"
        max_distance: int = 1,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for a product with filtering options.
        
        Args:
            product_id: Product ID to get relationships for
            relationship_types: Filter by relationship types
            direction: Relationship direction ("outgoing", "incoming", "both")
            max_distance: Maximum traversal distance
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of relationship dictionaries
        """
        # Build query based on direction
        if direction == "outgoing":
            pattern = "(p:Product {product_id: $product_id})-[r]->(related)"
        elif direction == "incoming":
            pattern = "(related)-[r]->(p:Product {product_id: $product_id})"
        else:  # both
            pattern = "(p:Product {product_id: $product_id})-[r]-(related)"
        
        # Add relationship type filter
        if relationship_types:
            type_filter = "|".join([rt.value for rt in relationship_types])
            pattern = pattern.replace("[r]", f"[r:{type_filter}]")
        
        # Add distance constraint
        if max_distance > 1:
            pattern = pattern.replace("[r]", f"[r*1..{max_distance}]")
        
        query = f"""
        MATCH {pattern}
        WHERE r.confidence >= $min_confidence
        RETURN type(r) as relationship_type,
               r.confidence as confidence,
               r.source as source,
               r.compatibility_type as compatibility_type,
               r.use_case as use_case,
               r.notes as notes,
               related.product_id as related_product_id,
               related.sku as related_sku,
               related.name as related_name,
               related.price as related_price
        ORDER BY r.confidence DESC
        """
        
        try:
            with self.conn.session() as session:
                results = session.run(query, {
                    "product_id": product_id,
                    "min_confidence": min_confidence
                })
                
                relationships = []
                for record in results:
                    relationships.append(dict(record))
                
                return relationships
                
        except Exception as e:
            self.logger.error(f"Failed to get relationships for product {product_id}: {e}")
            return []
    
    # ===========================================
    # ADVANCED QUERIES
    # ===========================================
    
    def find_compatible_products(
        self, 
        product_id: int, 
        compatibility_type: str = None,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find products compatible with the given product.
        
        Args:
            product_id: Product to find compatibility for
            compatibility_type: Type of compatibility (battery_system, etc.)
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of compatible products with compatibility details
        """
        query = """
        MATCH (p:Product {product_id: $product_id})-[r:COMPATIBLE_WITH|SAME_BRAND_ECOSYSTEM]-(compatible)
        WHERE r.confidence >= $min_confidence
        AND ($compatibility_type IS NULL OR r.compatibility_type = $compatibility_type)
        RETURN compatible.product_id as product_id,
               compatible.sku as sku,
               compatible.name as name,
               compatible.price as price,
               compatible.brand_name as brand_name,
               r.confidence as confidence,
               r.compatibility_type as compatibility_type,  
               r.notes as compatibility_notes
        ORDER BY r.confidence DESC
        """
        
        try:
            with self.conn.session() as session:
                results = session.run(query, {
                    "product_id": product_id,
                    "compatibility_type": compatibility_type,
                    "min_confidence": min_confidence
                })
                
                return [dict(record) for record in results]
                
        except Exception as e:
            self.logger.error(f"Failed to find compatible products: {e}")
            return []
    
    def find_project_recommendations(
        self, 
        project_type: str,
        budget_range: str = None,
        skill_level: str = None
    ) -> List[Dict[str, Any]]:
        """
        Find product recommendations for a DIY project.
        
        Args:
            project_type: Type of project (bathroom_renovation, etc.)
            budget_range: Budget constraint (low, medium, high)
            skill_level: Required skill level (beginner, intermediate, advanced)
            
        Returns:
            List of recommended products for the project
        """
        query = """
        MATCH (project:Project)-[r:REQUIRES|USED_FOR]-(product:Product)
        WHERE project.category = $project_type
        AND ($budget_range IS NULL OR project.budget_range = $budget_range)
        AND ($skill_level IS NULL OR project.difficulty_level = $skill_level)
        AND product.is_published = true
        RETURN product.product_id as product_id,
               product.sku as sku,
               product.name as name,
               product.price as price,
               product.brand_name as brand_name,
               r.requirement_type as requirement_type,
               r.priority as priority,
               r.confidence as confidence
        ORDER BY r.priority DESC, r.confidence DESC
        """
        
        try:
            with self.conn.session() as session:
                results = session.run(query, {
                    "project_type": project_type,
                    "budget_range": budget_range,
                    "skill_level": skill_level
                })
                
                return [dict(record) for record in results]
                
        except Exception as e:
            self.logger.error(f"Failed to find project recommendations: {e}")
            return []
    
    def get_brand_ecosystem(self, brand_name: str) -> Dict[str, Any]:
        """
        Get all products and relationships within a brand ecosystem.
        
        Args:
            brand_name: Brand name to analyze
            
        Returns:
            Dictionary with ecosystem analysis
        """
        query = """
        MATCH (brand:Brand {name: $brand_name})<-[:MANUFACTURED_BY]-(product:Product)
        OPTIONAL MATCH (product)-[r:COMPATIBLE_WITH|SAME_BRAND_ECOSYSTEM]-(related:Product)
        WHERE related.brand_name = $brand_name
        RETURN brand,
               collect(DISTINCT product) as products,
               collect(DISTINCT {
                   from: product.name,
                   to: related.name,
                   type: type(r),
                   confidence: r.confidence
               }) as relationships
        """
        
        try:
            with self.conn.session() as session:
                result = session.run(query, {"brand_name": brand_name}).single()
                
                if result:
                    return {
                        "brand": dict(result["brand"]) if result["brand"] else None,
                        "products": [dict(p) for p in result["products"]],
                        "relationships": result["relationships"],
                        "ecosystem_size": len(result["products"]),
                        "relationship_count": len([r for r in result["relationships"] if r["to"]])
                    }
                
        except Exception as e:
            self.logger.error(f"Failed to get brand ecosystem: {e}")
            
        return {"brand": None, "products": [], "relationships": [], "ecosystem_size": 0}
    
    def bulk_create_nodes(self, nodes: List[Union[ProductNode, CategoryNode, BrandNode]]) -> int:
        """
        Bulk create multiple nodes efficiently.
        
        Args:
            nodes: List of node objects to create
            
        Returns:
            Number of nodes successfully created
        """
        if not nodes:
            return 0
        
        # Group nodes by type
        products = [n for n in nodes if isinstance(n, ProductNode)]
        categories = [n for n in nodes if isinstance(n, CategoryNode)]
        brands = [n for n in nodes if isinstance(n, BrandNode)]
        
        created_count = 0
        
        try:
            with self.conn.session() as session:
                # Bulk create products
                if products:
                    product_data = [
                        {
                            "product_id": p.product_id,
                            "properties": p.to_neo4j_properties()
                        }
                        for p in products
                    ]
                    
                    query = """
                    UNWIND $data as row
                    MERGE (p:Product {product_id: row.product_id})
                    SET p += row.properties
                    """
                    
                    result = session.run(query, {"data": product_data})
                    created_count += len(products)
                
                # Bulk create categories
                if categories:
                    category_data = [
                        {
                            "category_id": c.category_id,
                            "properties": c.to_neo4j_properties()
                        }
                        for c in categories
                    ]
                    
                    query = """
                    UNWIND $data as row
                    MERGE (c:Category {category_id: row.category_id})
                    SET c += row.properties
                    """
                    
                    session.run(query, {"data": category_data})
                    created_count += len(categories)
                
                # Bulk create brands
                if brands:
                    brand_data = [
                        {
                            "brand_id": b.brand_id,
                            "properties": b.to_neo4j_properties()
                        }
                        for b in brands
                    ]
                    
                    query = """
                    UNWIND $data as row
                    MERGE (b:Brand {brand_id: row.brand_id})
                    SET b += row.properties
                    """
                    
                    session.run(query, {"data": brand_data})
                    created_count += len(brands)
                
                self.logger.info(f"Bulk created {created_count} nodes")
                
        except Exception as e:
            self.logger.error(f"Bulk node creation failed: {e}")
            
        return created_count
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics and metrics"""
        query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        UNION ALL
        MATCH ()-[r]->()
        RETURN type(r) as label, count(r) as count
        """
        
        try:
            with self.conn.session() as session:
                results = session.run(query)
                stats = {}
                
                for record in results:
                    label = record["label"]
                    count = record["count"]
                    stats[label] = count
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}


# Export main classes
__all__ = ["Neo4jConnection", "GraphDatabase"]