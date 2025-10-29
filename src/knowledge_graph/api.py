"""
Knowledge Graph API

This module provides FastAPI endpoints for interacting with the knowledge graph,
including product search, relationship queries, and recommendations.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from .database import Neo4jConnection, GraphDatabase
from .models import (
    ProductNodeCreate, RelationshipCreate, RelationshipQuery,
    SemanticSearchQuery, RelationshipType, ConfidenceSource
)
from .search import SemanticSearchEngine, SearchResult
from .inference import RelationshipInferenceEngine
from .integration import PostgreSQLIntegration

logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Horme Knowledge Graph API",
    description="Semantic product knowledge graph with AI-powered relationships and search",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (will be initialized on startup)
neo4j_conn: Optional[Neo4jConnection] = None
graph_db: Optional[GraphDatabase] = None
search_engine: Optional[SemanticSearchEngine] = None
inference_engine: Optional[RelationshipInferenceEngine] = None
postgres_integration: Optional[PostgreSQLIntegration] = None


# ===========================================
# PYDANTIC MODELS FOR API
# ===========================================

class ProductSearchRequest(BaseModel):
    """Request model for product search"""
    query: str = Field(..., description="Search query")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    min_similarity: float = Field(0.6, ge=0.0, le=1.0, description="Minimum similarity threshold")
    include_relationships: bool = Field(True, description="Include product relationships")
    search_strategy: str = Field("hybrid", description="Search strategy: semantic, text, graph, hybrid")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")


class CompatibilityRequest(BaseModel):
    """Request model for compatibility search"""
    product_id: int = Field(..., description="Product ID to find compatibility for")
    compatibility_types: Optional[List[str]] = Field(None, description="Types of compatibility")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")


class ProjectRecommendationRequest(BaseModel):
    """Request model for project recommendations"""
    project_description: str = Field(..., description="Description of the DIY project")
    budget_range: Optional[str] = Field(None, description="Budget range: low, medium, high")
    skill_level: Optional[str] = Field(None, description="Skill level: beginner, intermediate, advanced")
    limit: int = Field(15, ge=1, le=50, description="Maximum number of recommendations")


class RelationshipInferenceRequest(BaseModel):
    """Request model for relationship inference"""
    batch_size: int = Field(500, ge=100, le=2000, description="Batch size for processing")
    max_products: Optional[int] = Field(None, description="Maximum products to process (testing)")
    min_confidence: float = Field(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")


class MigrationRequest(BaseModel):
    """Request model for data migration"""
    force_refresh: bool = Field(False, description="Force full refresh regardless of sync status")
    entity_types: Optional[List[str]] = Field(None, description="Entity types to migrate: products, categories, brands")
    limit: Optional[int] = Field(None, description="Limit number of entities (testing)")


class GraphAnalyticsResponse(BaseModel):
    """Response model for graph analytics"""
    node_counts: Dict[str, int]
    relationship_counts: Dict[str, int]
    top_brands: List[Dict[str, Any]]
    top_categories: List[Dict[str, Any]]
    graph_density: float
    last_updated: datetime


# ===========================================
# DEPENDENCY INJECTION
# ===========================================

def get_graph_db() -> GraphDatabase:
    """Dependency for graph database access"""
    if graph_db is None:
        raise HTTPException(status_code=503, detail="Graph database not initialized")
    return graph_db

def get_search_engine() -> SemanticSearchEngine:
    """Dependency for search engine access"""
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    return search_engine

def get_inference_engine() -> RelationshipInferenceEngine:
    """Dependency for inference engine access"""
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Inference engine not initialized")
    return inference_engine

def get_postgres_integration() -> PostgreSQLIntegration:
    """Dependency for PostgreSQL integration access"""
    if postgres_integration is None:
        raise HTTPException(status_code=503, detail="PostgreSQL integration not initialized")
    return postgres_integration


# ===========================================
# HEALTH AND STATUS ENDPOINTS
# ===========================================

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    if neo4j_conn is None:
        raise HTTPException(status_code=503, detail="Knowledge graph services not initialized")
    
    health_status = neo4j_conn.health_check()
    
    if health_status["status"] == "healthy":
        return {"status": "healthy", "timestamp": datetime.utcnow(), "details": health_status}
    else:
        raise HTTPException(status_code=503, detail=f"Unhealthy: {health_status.get('error', 'Unknown error')}")


@app.get("/stats", response_model=GraphAnalyticsResponse, tags=["System"])
async def get_graph_statistics(db: GraphDatabase = Depends(get_graph_db)):
    """Get knowledge graph statistics and analytics"""
    try:
        # Get basic node and relationship counts
        stats = db.get_database_stats()
        
        # Separate nodes and relationships
        node_counts = {k: v for k, v in stats.items() if not k.isupper()}
        relationship_counts = {k: v for k, v in stats.items() if k.isupper()}
        
        # Get top brands and categories
        top_brands = await _get_top_entities("Brand", db)
        top_categories = await _get_top_entities("Category", db)
        
        # Calculate graph density (simplified)
        total_nodes = sum(node_counts.values())
        total_relationships = sum(relationship_counts.values())
        max_possible_edges = total_nodes * (total_nodes - 1) / 2
        graph_density = total_relationships / max_possible_edges if max_possible_edges > 0 else 0.0
        
        return GraphAnalyticsResponse(
            node_counts=node_counts,
            relationship_counts=relationship_counts,
            top_brands=top_brands,
            top_categories=top_categories,
            graph_density=graph_density,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get graph statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")


# ===========================================
# SEARCH ENDPOINTS
# ===========================================

@app.post("/search/products", response_model=List[SearchResult], tags=["Search"])
async def search_products(
    request: ProductSearchRequest,
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
):
    """
    Search for products using semantic and traditional search methods.
    
    Supports multiple search strategies:
    - **semantic**: Vector similarity using embeddings
    - **text**: Traditional text search using TF-IDF
    - **graph**: Relationship-based traversal search
    - **hybrid**: Combination of all methods (recommended)
    """
    try:
        results = await search_engine.search(
            query=request.query,
            limit=request.limit,
            min_similarity=request.min_similarity,
            include_relationships=request.include_relationships,
            filters=request.filters,
            search_strategy=request.search_strategy
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Product search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/search/compatibility", response_model=List[SearchResult], tags=["Search"])
async def find_compatible_products(
    request: CompatibilityRequest,
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
):
    """
    Find products compatible with a specific product.
    
    Returns products that are compatible based on:
    - Brand ecosystem compatibility (same battery system, etc.)
    - Technical specifications (voltage, size, etc.)
    - Usage patterns and relationships
    """
    try:
        results = await search_engine.find_compatible_products(
            product_id=request.product_id,
            compatibility_types=request.compatibility_types,
            limit=request.limit
        )
        
        if not results:
            raise HTTPException(status_code=404, detail=f"No compatible products found for product {request.product_id}")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compatibility search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Compatibility search failed: {str(e)}")


@app.post("/search/project-recommendations", response_model=List[SearchResult], tags=["Search"])
async def get_project_recommendations(
    request: ProjectRecommendationRequest,
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
):
    """
    Get product recommendations for a DIY project.
    
    Analyzes the project description and recommends appropriate tools,
    materials, and accessories based on project requirements and user constraints.
    """
    try:
        results = await search_engine.recommend_for_project(
            project_description=request.project_description,
            budget_range=request.budget_range,
            skill_level=request.skill_level,
            limit=request.limit
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Project recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Project recommendation failed: {str(e)}")


# ===========================================
# PRODUCT AND RELATIONSHIP ENDPOINTS
# ===========================================

@app.get("/products/{product_id}", tags=["Products"])
async def get_product(
    product_id: int,
    include_relationships: bool = Query(True, description="Include product relationships"),
    db: GraphDatabase = Depends(get_graph_db)
):
    """Get detailed information about a specific product"""
    try:
        product = db.get_product_node(product_id=product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        result = {
            "product": product.__dict__,
            "relationships": []
        }
        
        if include_relationships:
            relationships = db.get_product_relationships(
                product_id=product_id,
                max_distance=1,
                min_confidence=0.5
            )
            result["relationships"] = relationships
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve product: {str(e)}")


@app.get("/products/{product_id}/relationships", tags=["Products"])
async def get_product_relationships(
    product_id: int,
    relationship_types: Optional[List[RelationshipType]] = Query(None, description="Filter by relationship types"),
    direction: str = Query("both", description="Relationship direction: outgoing, incoming, both"),
    max_distance: int = Query(1, ge=1, le=3, description="Maximum traversal distance"),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    db: GraphDatabase = Depends(get_graph_db)
):
    """Get relationships for a specific product with filtering options"""
    try:
        relationships = db.get_product_relationships(
            product_id=product_id,
            relationship_types=relationship_types,
            direction=direction,
            max_distance=max_distance,
            min_confidence=min_confidence
        )
        
        return {
            "product_id": product_id,
            "relationship_count": len(relationships),
            "relationships": relationships
        }
        
    except Exception as e:
        logger.error(f"Failed to get relationships for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve relationships: {str(e)}")


@app.post("/relationships", tags=["Relationships"])
async def create_relationship(
    relationship: RelationshipCreate,
    db: GraphDatabase = Depends(get_graph_db)
):
    """Create a new relationship between products"""
    try:
        from .models import SemanticRelationship
        
        # Convert to internal model
        semantic_rel = SemanticRelationship(
            from_product_id=relationship.from_product_id,
            to_product_id=relationship.to_product_id,
            relationship_type=relationship.relationship_type,
            confidence=relationship.confidence,
            source=relationship.source,
            compatibility_type=relationship.compatibility_type,
            use_case=relationship.use_case,
            notes=relationship.notes,
            evidence=relationship.evidence
        )
        
        success = db.create_relationship(semantic_rel)
        
        if success:
            return {"message": "Relationship created successfully", "relationship": relationship.dict()}
        else:
            raise HTTPException(status_code=500, detail="Failed to create relationship")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create relationship: {e}")
        raise HTTPException(status_code=500, detail=f"Relationship creation failed: {str(e)}")


# ===========================================
# BRAND AND CATEGORY ENDPOINTS  
# ===========================================

@app.get("/brands/{brand_name}/ecosystem", tags=["Brands"])
async def get_brand_ecosystem(
    brand_name: str,
    db: GraphDatabase = Depends(get_graph_db)
):
    """
    Get comprehensive brand ecosystem analysis.
    
    Returns all products, relationships, and compatibility information
    within a specific brand ecosystem (e.g., Makita 18V LXT system).
    """
    try:
        ecosystem = db.get_brand_ecosystem(brand_name)
        
        if not ecosystem.get("brand"):
            raise HTTPException(status_code=404, detail=f"Brand '{brand_name}' not found")
        
        return ecosystem
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get brand ecosystem for {brand_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Brand ecosystem analysis failed: {str(e)}")


@app.get("/categories", tags=["Categories"])
async def list_categories(
    parent_id: Optional[int] = Query(None, description="Filter by parent category"),
    level: Optional[int] = Query(None, description="Filter by hierarchy level"),
    db: GraphDatabase = Depends(get_graph_db)
):
    """List product categories with optional filtering"""
    try:
        query = "MATCH (c:Category) WHERE c.is_active = true"
        params = {}
        
        if parent_id is not None:
            query += " AND c.parent_id = $parent_id"
            params["parent_id"] = parent_id
        
        if level is not None:
            query += " AND c.level = $level"
            params["level"] = level
        
        query += " RETURN c ORDER BY c.sort_order, c.name"
        
        with neo4j_conn.session() as session:
            results = session.run(query, params)
            categories = [dict(record["c"]) for record in results]
        
        return {"categories": categories, "count": len(categories)}
        
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(status_code=500, detail=f"Category listing failed: {str(e)}")


# ===========================================
# INFERENCE AND ANALYTICS ENDPOINTS
# ===========================================

@app.post("/inference/relationships", tags=["AI/ML"])
async def run_relationship_inference(
    request: RelationshipInferenceRequest,
    background_tasks: BackgroundTasks,
    inference_engine: RelationshipInferenceEngine = Depends(get_inference_engine)
):
    """
    Run AI-powered relationship inference on products.
    
    This is a computationally intensive operation that runs in the background.
    Use the returned task_id to check progress.
    """
    try:
        # Start inference in background
        task_id = f"inference_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        background_tasks.add_task(
            _run_inference_task,
            task_id,
            request.batch_size,
            request.max_products,
            request.min_confidence,
            inference_engine
        )
        
        return {
            "message": "Relationship inference started",
            "task_id": task_id,
            "estimated_duration": "5-30 minutes depending on dataset size"
        }
        
    except Exception as e:
        logger.error(f"Failed to start relationship inference: {e}")
        raise HTTPException(status_code=500, detail=f"Inference start failed: {str(e)}")


@app.get("/inference/progress/{task_id}", tags=["AI/ML"])
async def get_inference_progress(task_id: str):
    """Get progress of relationship inference task"""
    # This would typically check a task queue or database
    # For now, return a simple response
    return {
        "task_id": task_id,
        "status": "running",
        "message": "Progress tracking not implemented yet - check logs for updates"
    }


# ===========================================
# DATA MANAGEMENT ENDPOINTS
# ===========================================

@app.post("/data/migrate", tags=["Data Management"])
async def migrate_data(
    request: MigrationRequest,
    background_tasks: BackgroundTasks,
    integration: PostgreSQLIntegration = Depends(get_postgres_integration)
):
    """
    Migrate data from PostgreSQL to Neo4j knowledge graph.
    
    This operation can take several minutes for large datasets.
    """
    try:
        task_id = f"migration_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        background_tasks.add_task(
            _run_migration_task,
            task_id,
            request.force_refresh,
            request.entity_types,
            request.limit,
            integration
        )
        
        return {
            "message": "Data migration started",
            "task_id": task_id,
            "entity_types": request.entity_types or ["categories", "brands", "products"],
            "estimated_duration": "2-15 minutes depending on data size"
        }
        
    except Exception as e:
        logger.error(f"Failed to start data migration: {e}")
        raise HTTPException(status_code=500, detail=f"Migration start failed: {str(e)}")


@app.get("/data/sync-status", tags=["Data Management"])
async def get_sync_status(integration: PostgreSQLIntegration = Depends(get_postgres_integration)):
    """Get data synchronization status between PostgreSQL and Neo4j"""
    try:
        status = await integration.get_sync_status()
        return status
        
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail=f"Sync status check failed: {str(e)}")


@app.post("/data/index-products", tags=["Data Management"])
async def index_products_for_search(
    background_tasks: BackgroundTasks,
    batch_size: int = Query(100, ge=10, le=500, description="Batch size for indexing"),
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
):
    """
    Index products for semantic search.
    
    This creates vector embeddings for all products to enable semantic search.
    """
    try:
        task_id = f"indexing_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        background_tasks.add_task(
            _run_indexing_task,
            task_id,
            batch_size,
            search_engine
        )
        
        return {
            "message": "Product indexing started",
            "task_id": task_id,
            "estimated_duration": "5-20 minutes depending on product count"
        }
        
    except Exception as e:
        logger.error(f"Failed to start product indexing: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing start failed: {str(e)}")


# ===========================================
# BACKGROUND TASK FUNCTIONS
# ===========================================

async def _run_inference_task(
    task_id: str,
    batch_size: int,
    max_products: Optional[int],
    min_confidence: float,
    inference_engine: RelationshipInferenceEngine
):
    """Background task for relationship inference"""
    try:
        logger.info(f"Starting inference task {task_id}")
        
        results = await inference_engine.infer_all_relationships(
            batch_size=batch_size,
            max_products=max_products,
            min_confidence=min_confidence
        )
        
        logger.info(f"Inference task {task_id} completed: {results}")
        
    except Exception as e:
        logger.error(f"Inference task {task_id} failed: {e}")


async def _run_migration_task(
    task_id: str,
    force_refresh: bool,
    entity_types: Optional[List[str]],
    limit: Optional[int],
    integration: PostgreSQLIntegration
):
    """Background task for data migration"""
    try:
        logger.info(f"Starting migration task {task_id}")
        
        if entity_types:
            results = {}
            if "categories" in entity_types:
                results['categories'] = await integration.migrate_categories(force_refresh)
            if "brands" in entity_types:
                results['brands'] = await integration.migrate_brands(force_refresh)
            if "products" in entity_types:
                results['products'] = await integration.migrate_products(force_refresh, limit)
        else:
            results = await integration.migrate_all(force_refresh)
        
        logger.info(f"Migration task {task_id} completed: {results}")
        
    except Exception as e:
        logger.error(f"Migration task {task_id} failed: {e}")


async def _run_indexing_task(
    task_id: str,
    batch_size: int,
    search_engine: SemanticSearchEngine
):
    """Background task for product indexing"""
    try:
        logger.info(f"Starting indexing task {task_id}")
        
        indexed_count = await search_engine.index_products(batch_size)
        
        logger.info(f"Indexing task {task_id} completed: {indexed_count} products indexed")
        
    except Exception as e:
        logger.error(f"Indexing task {task_id} failed: {e}")


# ===========================================
# UTILITY FUNCTIONS
# ===========================================

async def _get_top_entities(entity_type: str, db: GraphDatabase, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top entities by product count"""
    try:
        query = f"""
        MATCH (e:{entity_type})<-[r]-(p:Product)
        WHERE e.is_active = true
        RETURN e.name as name,
               e.{entity_type.lower()}_id as id,
               count(p) as product_count
        ORDER BY product_count DESC
        LIMIT $limit
        """
        
        with neo4j_conn.session() as session:
            results = session.run(query, {"limit": limit})
            return [dict(record) for record in results]
            
    except Exception as e:
        logger.warning(f"Failed to get top {entity_type} entities: {e}")
        return []


# ===========================================
# APPLICATION STARTUP AND SHUTDOWN
# ===========================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global neo4j_conn, graph_db, search_engine, inference_engine, postgres_integration
    
    try:
        # Initialize Neo4j connection
        neo4j_conn = Neo4jConnection()
        graph_db = GraphDatabase(neo4j_conn)
        
        # Initialize search engine
        search_engine = SemanticSearchEngine(
            neo4j_connection=neo4j_conn,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize inference engine
        inference_engine = RelationshipInferenceEngine(
            neo4j_connection=neo4j_conn,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize PostgreSQL integration
        postgres_integration = PostgreSQLIntegration(
            neo4j_connection=neo4j_conn
        )
        
        logger.info("Knowledge Graph API initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Knowledge Graph API: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        if postgres_integration:
            await postgres_integration.close()
        
        if neo4j_conn:
            neo4j_conn.close()
            
        logger.info("Knowledge Graph API shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# ===========================================
# MAIN ENTRY POINT
# ===========================================

if __name__ == "__main__":
    uvicorn.run(
        "knowledge_graph.api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )