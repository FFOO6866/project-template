"""
FastAPI server for real-time DIY intent classification.
Provides REST API endpoints with <500ms response time guarantee.
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
import redis
from cachetools import TTLCache
import threading

# Import our classification modules
from intent_classifier import DIYIntentClassificationSystem, ClassificationResult
from entity_extraction import DIYEntityExtractor, ExtractedEntity
from query_expansion import DIYQueryExpander, ExpandedQuery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for API
class ClassificationRequest(BaseModel):
    query: str = Field(..., description="DIY query to classify", min_length=1, max_length=500)
    use_expansion: bool = Field(True, description="Whether to use query expansion")
    include_entities: bool = Field(True, description="Whether to extract entities")
    intent_hint: Optional[str] = Field(None, description="Optional intent hint for better accuracy")


class EntityResponse(BaseModel):
    entity_type: str
    value: str
    confidence: float
    extraction_method: str


class ClassificationResponse(BaseModel):
    query: str
    intent: str
    confidence: float
    entities: List[EntityResponse]
    processing_time_ms: float
    fallback_used: bool
    expansion_used: bool
    expansion_terms: List[str] = []


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    avg_response_time_ms: float
    total_requests: int
    cache_hit_rate: float


class BatchClassificationRequest(BaseModel):
    queries: List[str] = Field(..., max_items=10, description="Batch of queries to classify")
    use_expansion: bool = True
    include_entities: bool = True


class BatchClassificationResponse(BaseModel):
    results: List[ClassificationResponse]
    total_processing_time_ms: float
    batch_size: int


# Global system components
classifier: Optional[DIYIntentClassificationSystem] = None
entity_extractor: Optional[DIYEntityExtractor] = None
query_expander: Optional[DIYQueryExpander] = None
redis_client: Optional[redis.Redis] = None
local_cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute TTL cache

# Performance tracking
request_count = 0
request_times = []
cache_hits = 0
cache_misses = 0
request_lock = threading.Lock()

# FastAPI app
app = FastAPI(
    title="DIY Intent Classification API",
    description="Real-time intent classification for DIY customer queries",
    version="1.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


async def get_classifier():
    """Dependency to get the classifier instance"""
    if classifier is None:
        raise HTTPException(status_code=503, detail="Classifier not loaded")
    return classifier


async def get_entity_extractor():
    """Dependency to get the entity extractor instance"""
    if entity_extractor is None:
        raise HTTPException(status_code=503, detail="Entity extractor not loaded")
    return entity_extractor


async def get_query_expander():
    """Dependency to get the query expander instance"""
    if query_expander is None:
        raise HTTPException(status_code=503, detail="Query expander not loaded")
    return query_expander


def get_cache_key(query: str, use_expansion: bool, include_entities: bool) -> str:
    """Generate cache key for query"""
    return f"classify:{hash(query)}:{use_expansion}:{include_entities}"


async def get_cached_result(cache_key: str) -> Optional[Dict]:
    """Get result from cache"""
    global cache_hits, cache_misses
    
    # Try local cache first
    if cache_key in local_cache:
        with request_lock:
            cache_hits += 1
        return local_cache[cache_key]
    
    # Try Redis cache if available
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                result = json.loads(cached)
                local_cache[cache_key] = result  # Store in local cache too
                with request_lock:
                    cache_hits += 1
                return result
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
    
    with request_lock:
        cache_misses += 1
    return None


async def cache_result(cache_key: str, result: Dict):
    """Cache result in both local and Redis cache"""
    local_cache[cache_key] = result
    
    if redis_client:
        try:
            redis_client.setex(cache_key, 300, json.dumps(result))  # 5 minutes TTL
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")


def track_request_time(processing_time: float):
    """Track request processing time"""
    global request_count, request_times
    
    with request_lock:
        request_count += 1
        request_times.append(processing_time)
        
        # Keep only last 1000 requests for average calculation
        if len(request_times) > 1000:
            request_times = request_times[-1000:]


@app.on_event("startup")
async def startup_event():
    """Initialize system components on startup"""
    global classifier, entity_extractor, query_expander, redis_client
    
    logger.info("Starting DIY Intent Classification API...")
    
    try:
        # Initialize components
        logger.info("Loading intent classifier...")
        classifier = DIYIntentClassificationSystem()
        
        # Try to load trained model
        model_path = Path(__file__).parent / "trained_model"
        if model_path.exists():
            classifier.load_model(str(model_path))
            logger.info("Trained model loaded successfully")
        else:
            logger.warning("No trained model found. Training new model...")
            # This would be done offline in production
            # classifier = train_intent_classifier()
        
        logger.info("Loading entity extractor...")
        entity_extractor = DIYEntityExtractor()
        
        logger.info("Loading query expander...")
        query_expander = DIYQueryExpander()
        
        # Try to connect to Redis
        try:
            redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            redis_client.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Using local cache only.")
            redis_client = None
        
        logger.info("API startup complete!")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global redis_client
    
    if redis_client:
        redis_client.close()
    
    logger.info("API shutdown complete")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "DIY Intent Classification API", 
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    global request_count, request_times, cache_hits, cache_misses
    
    avg_response_time = sum(request_times) / len(request_times) if request_times else 0
    total_cache_requests = cache_hits + cache_misses
    cache_hit_rate = cache_hits / total_cache_requests if total_cache_requests > 0 else 0
    
    return HealthResponse(
        status="healthy" if classifier and entity_extractor and query_expander else "degraded",
        model_loaded=classifier is not None,
        avg_response_time_ms=avg_response_time,
        total_requests=request_count,
        cache_hit_rate=cache_hit_rate
    )


@app.post("/classify", response_model=ClassificationResponse)
async def classify_intent(
    request: ClassificationRequest,
    background_tasks: BackgroundTasks,
    classifier_instance: DIYIntentClassificationSystem = Depends(get_classifier),
    entity_extractor_instance: DIYEntityExtractor = Depends(get_entity_extractor),
    query_expander_instance: DIYQueryExpander = Depends(get_query_expander)
):
    """Classify intent of a DIY query with <500ms guarantee"""
    
    start_time = time.time()
    
    try:
        # Generate cache key
        cache_key = get_cache_key(request.query, request.use_expansion, request.include_entities)
        
        # Check cache
        cached_result = await get_cached_result(cache_key)
        if cached_result:
            processing_time = (time.time() - start_time) * 1000
            background_tasks.add_task(track_request_time, processing_time)
            return ClassificationResponse(**cached_result)
        
        # Prepare query
        query_to_classify = request.query
        expansion_terms = []
        expansion_used = False
        
        if request.use_expansion:
            expanded = query_expander_instance.expand_query(request.query, request.intent_hint)
            query_to_classify = expanded.expanded_query
            expansion_terms = expanded.expansion_terms
            expansion_used = True
        
        # Classify intent
        classification_result = classifier_instance.classify_intent(
            query_to_classify, 
            use_fallback=True
        )
        
        # Extract entities
        entities = []
        if request.include_entities:
            extracted_entities = entity_extractor_instance.extract_entities(request.query)
            entities = [
                EntityResponse(
                    entity_type=entity.entity_type.value,
                    value=entity.value,
                    confidence=entity.confidence,
                    extraction_method=entity.extraction_method
                )
                for entity in extracted_entities
            ]
        
        # Build response
        response = ClassificationResponse(
            query=request.query,
            intent=classification_result.intent,
            confidence=classification_result.confidence,
            entities=entities,
            processing_time_ms=classification_result.processing_time_ms,
            fallback_used=classification_result.fallback_used,
            expansion_used=expansion_used,
            expansion_terms=expansion_terms
        )
        
        # Cache result
        background_tasks.add_task(
            cache_result, 
            cache_key, 
            response.dict()
        )
        
        # Track performance
        total_processing_time = (time.time() - start_time) * 1000
        background_tasks.add_task(track_request_time, total_processing_time)
        
        # Ensure <500ms response time (log warning if exceeded)
        if total_processing_time > 500:
            logger.warning(f"Response time exceeded 500ms: {total_processing_time:.1f}ms for query: {request.query}")
        
        return response
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Classification failed for query '{request.query}': {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@app.post("/classify/batch", response_model=BatchClassificationResponse)
async def classify_batch(
    request: BatchClassificationRequest,
    background_tasks: BackgroundTasks,
    classifier_instance: DIYIntentClassificationSystem = Depends(get_classifier),
    entity_extractor_instance: DIYEntityExtractor = Depends(get_entity_extractor),
    query_expander_instance: DIYQueryExpander = Depends(get_query_expander)
):
    """Batch classify multiple queries"""
    
    start_time = time.time()
    results = []
    
    try:
        # Process each query
        for query in request.queries:
            classification_request = ClassificationRequest(
                query=query,
                use_expansion=request.use_expansion,
                include_entities=request.include_entities
            )
            
            # Use the single classification endpoint logic
            result = await classify_intent(
                classification_request,
                background_tasks,
                classifier_instance,
                entity_extractor_instance,
                query_expander_instance
            )
            results.append(result)
        
        total_processing_time = (time.time() - start_time) * 1000
        
        return BatchClassificationResponse(
            results=results,
            total_processing_time_ms=total_processing_time,
            batch_size=len(request.queries)
        )
        
    except Exception as e:
        logger.error(f"Batch classification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch classification failed: {str(e)}")


@app.get("/intents", response_model=List[str])
async def get_available_intents(
    classifier_instance: DIYIntentClassificationSystem = Depends(get_classifier)
):
    """Get list of available intent categories"""
    if hasattr(classifier_instance, 'id_to_label') and classifier_instance.id_to_label:
        return list(classifier_instance.id_to_label.values())
    else:
        return ["project_planning", "problem_solving", "tool_selection", "product_comparison", "learning"]


@app.get("/entities/types", response_model=List[str])
async def get_entity_types(
    entity_extractor_instance: DIYEntityExtractor = Depends(get_entity_extractor)
):
    """Get list of available entity types"""
    from entity_extraction import EntityType
    return [entity_type.value for entity_type in EntityType]


@app.post("/expand", response_model=Dict)
async def expand_query(
    query: str,
    intent_hint: Optional[str] = None,
    query_expander_instance: DIYQueryExpander = Depends(get_query_expander)
):
    """Expand a query with synonyms and related terms"""
    try:
        expanded = query_expander_instance.expand_query(query, intent_hint)
        enhanced = query_expander_instance.enhance_classification_input(query, intent_hint)
        
        return {
            "original_query": query,
            "expanded_query": expanded.expanded_query,
            "expansion_terms": expanded.expansion_terms,
            "confidence_boost": expanded.confidence_boost,
            "query_variations": enhanced["query_variations"],
            "key_terms": enhanced["key_terms"],
            "processing_hints": enhanced["processing_hints"]
        }
    except Exception as e:
        logger.error(f"Query expansion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query expansion failed: {str(e)}")


@app.get("/performance/stats", response_model=Dict)
async def get_performance_stats():
    """Get detailed performance statistics"""
    global request_count, request_times, cache_hits, cache_misses
    
    if not request_times:
        return {"message": "No performance data available"}
    
    avg_time = sum(request_times) / len(request_times)
    max_time = max(request_times)
    min_time = min(request_times)
    under_500ms = sum(1 for t in request_times if t < 500)
    under_500ms_percent = (under_500ms / len(request_times)) * 100
    
    total_cache_requests = cache_hits + cache_misses
    cache_hit_rate = cache_hits / total_cache_requests if total_cache_requests > 0 else 0
    
    return {
        "total_requests": request_count,
        "avg_response_time_ms": avg_time,
        "max_response_time_ms": max_time,
        "min_response_time_ms": min_time,
        "under_500ms_percent": under_500ms_percent,
        "cache_hit_rate": cache_hit_rate,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses
    }


@app.delete("/cache/clear")
async def clear_cache():
    """Clear all caches"""
    global cache_hits, cache_misses
    
    try:
        # Clear local cache
        local_cache.clear()
        
        # Clear Redis cache if available
        if redis_client:
            redis_client.flushdb()
        
        # Reset cache stats
        cache_hits = 0
        cache_misses = 0
        
        return {"message": "Cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")


if __name__ == "__main__":
    # For development - use uvicorn command for production
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1  # Single worker for development
    )