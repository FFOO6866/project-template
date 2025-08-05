"""
ETIM Service Implementation - DATA-001
=====================================

Service implementation for ETIM (European Technical Information Model) 
classification with Redis caching and Neo4j knowledge graph integration.

Features:
- ETIM 9.0 classification with 5,554+ classes
- Multi-language support (13+ languages)
- Redis caching for sub-500ms performance
- Neo4j knowledge graph relationships
- Technical attribute management
- Hierarchical parent-child relationships

Performance Requirements:
- Cache hit: <100ms
- Database lookup: <500ms
- Multi-language query: <300ms
- Knowledge graph traversal: <1000ms
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# External service imports
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import asyncpg
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    from neo4j import GraphDatabase, AsyncGraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

# Core classification imports
try:
    from core.classification import ETIMClass
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False

@dataclass
class ETIMServiceConfig:
    """Configuration for ETIM service"""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "etim_db"
    postgres_user: str = "etim_user"
    postgres_password: str = "etim_pass"
    
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    cache_ttl: int = 3600  # 1 hour
    performance_sla_ms: int = 500
    
    supported_languages: List[str] = None
    
    def __post_init__(self):
        if self.supported_languages is None:
            self.supported_languages = [
                "en", "de", "fr", "es", "it", "ja", "ko", 
                "nl", "zh", "pt", "ru", "tr", "pl"
            ]

class ETIMService:
    """
    Service for ETIM classification with caching and knowledge graph integration.
    
    Provides high-performance ETIM classification lookup with multi-language
    support, Redis caching, and Neo4j knowledge graph relationships.
    """
    
    def __init__(self, config: ETIMServiceConfig = None):
        self.config = config or ETIMServiceConfig()
        self.redis_client: Optional[redis.Redis] = None
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.neo4j_driver = None
        
        # Performance tracking
        self.cache_hits = 0
        self.cache_misses = 0
        self.query_count = 0
        self.performance_metrics = []
        
        # ETIM metadata
        self.major_groups = {
            "EC": "Electrical Installation",
            "EG": "Building Technology", 
            "EH": "Tools, Hardware and Site Supplies",
            "EI": "Information and Communication Technology",
            "EL": "Lighting",
            "EM": "Measurement and Control Technology"
        }
    
    async def initialize(self) -> bool:
        """Initialize all service connections"""
        try:
            # Initialize Redis
            if REDIS_AVAILABLE:
                self.redis_client = redis.Redis(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    db=self.config.redis_db,
                    password=self.config.redis_password,
                    decode_responses=True
                )
                await self.redis_client.ping()
            
            # Initialize PostgreSQL
            if POSTGRES_AVAILABLE:
                self.postgres_pool = await asyncpg.create_pool(
                    host=self.config.postgres_host,
                    port=self.config.postgres_port,
                    database=self.config.postgres_db,
                    user=self.config.postgres_user,
                    password=self.config.postgres_password,
                    min_size=2,
                    max_size=10
                )
            
            # Initialize Neo4j
            if NEO4J_AVAILABLE:
                self.neo4j_driver = AsyncGraphDatabase.driver(
                    self.config.neo4j_uri,
                    auth=(self.config.neo4j_user, self.config.neo4j_password)
                )
                await self.neo4j_driver.verify_connectivity()
            
            return True
            
        except Exception as e:
            print(f"ETIM Service initialization error: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup service connections"""
        if self.redis_client:
            await self.redis_client.close()
        
        if self.postgres_pool:
            await self.postgres_pool.close()
        
        if self.neo4j_driver:
            await self.neo4j_driver.close()
    
    async def get_etim_class(self, class_id: str, language: str = "en") -> Optional[Dict[str, Any]]:
        """
        Get ETIM class information with caching.
        
        Args:
            class_id: ETIM class identifier (e.g., "EH001234")
            language: Language code for localized name
            
        Returns:
            ETIM class data or None if not found
        """
        start_time = time.time()
        
        try:
            # Try cache first
            cached_result = await self._get_from_cache(f"etim_class:{class_id}:{language}")
            if cached_result:
                self.cache_hits += 1
                self._record_performance("cache_hit", start_time)
                return cached_result
            
            self.cache_misses += 1
            
            # Query database
            etim_data = await self._query_etim_class_from_db(class_id, language)
            
            if etim_data:
                # Cache the result
                await self._set_cache(f"etim_class:{class_id}:{language}", etim_data)
                self._record_performance("db_query", start_time)
                return etim_data
            
            return None
            
        except Exception as e:
            self._record_performance("error", start_time)
            print(f"Error getting ETIM class {class_id}: {e}")
            return None
    
    async def search_etim_classes(self, 
                                 search_term: str, 
                                 language: str = "en",
                                 limit: int = 10,
                                 major_group: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search ETIM classes by name or description.
        
        Args:
            search_term: Search query
            language: Language for search and results
            limit: Maximum number of results
            major_group: Optional major group filter (e.g., "EH")
            
        Returns:
            List of matching ETIM classes
        """
        start_time = time.time()
        
        try:
            # Create cache key
            cache_key = f"etim_search:{hash(search_term)}:{language}:{limit}:{major_group or 'all'}"
            
            # Try cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.cache_hits += 1
                self._record_performance("search_cache_hit", start_time)
                return cached_result
            
            self.cache_misses += 1
            
            # Query database
            search_results = await self._search_etim_classes_in_db(
                search_term, language, limit, major_group
            )
            
            # Cache results for shorter time (search results change more frequently)
            await self._set_cache(cache_key, search_results, ttl=300)  # 5 minutes
            
            self._record_performance("search_db_query", start_time)
            return search_results
            
        except Exception as e:
            self._record_performance("search_error", start_time)
            print(f"Error searching ETIM classes: {e}")
            return []
    
    async def get_etim_hierarchy(self, class_id: str) -> Dict[str, Any]:
        """
        Get complete hierarchy for ETIM class including parent-child relationships.
        
        Args:
            class_id: ETIM class identifier
            
        Returns:
            Hierarchy information with parents and children
        """
        start_time = time.time()
        
        try:
            cache_key = f"etim_hierarchy:{class_id}"
            
            # Try cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.cache_hits += 1
                self._record_performance("hierarchy_cache_hit", start_time)
                return cached_result
            
            self.cache_misses += 1
            
            # Build hierarchy from database and knowledge graph
            hierarchy = await self._build_etim_hierarchy(class_id)
            
            # Cache hierarchy (changes infrequently)
            await self._set_cache(cache_key, hierarchy, ttl=self.config.cache_ttl * 2)
            
            self._record_performance("hierarchy_build", start_time)
            return hierarchy
            
        except Exception as e:
            self._record_performance("hierarchy_error", start_time)
            print(f"Error building ETIM hierarchy for {class_id}: {e}")
            return {"class_id": class_id, "parents": [], "children": [], "error": str(e)}
    
    async def get_technical_attributes(self, class_id: str) -> Dict[str, Any]:
        """
        Get technical attributes for ETIM class.
        
        Args:
            class_id: ETIM class identifier
            
        Returns:
            Technical attributes with definitions and value options
        """
        start_time = time.time()
        
        try:
            cache_key = f"etim_attributes:{class_id}"
            
            # Try cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.cache_hits += 1
                self._record_performance("attributes_cache_hit", start_time)
                return cached_result
            
            self.cache_misses += 1
            
            # Query technical attributes
            attributes = await self._query_technical_attributes(class_id)
            
            # Cache attributes (stable data)
            await self._set_cache(cache_key, attributes, ttl=self.config.cache_ttl * 4)
            
            self._record_performance("attributes_query", start_time)
            return attributes
            
        except Exception as e:
            self._record_performance("attributes_error", start_time)
            print(f"Error getting technical attributes for {class_id}: {e}")
            return {"class_id": class_id, "attributes": {}, "error": str(e)}
    
    async def get_multilingual_names(self, class_id: str) -> Dict[str, str]:
        """
        Get ETIM class names in all available languages.
        
        Args:
            class_id: ETIM class identifier
            
        Returns:
            Dictionary mapping language codes to localized names
        """
        start_time = time.time()
        
        try:
            cache_key = f"etim_multilang:{class_id}"
            
            # Try cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.cache_hits += 1
                self._record_performance("multilang_cache_hit", start_time)
                return cached_result
            
            self.cache_misses += 1
            
            # Query all language names
            multilang_names = await self._query_multilingual_names(class_id)
            
            # Cache multilingual data (very stable)
            await self._set_cache(cache_key, multilang_names, ttl=self.config.cache_ttl * 6)
            
            self._record_performance("multilang_query", start_time)
            return multilang_names
            
        except Exception as e:
            self._record_performance("multilang_error", start_time)
            print(f"Error getting multilingual names for {class_id}: {e}")
            return {"en": "Unknown"}
    
    async def update_knowledge_graph_relationships(self, class_id: str, relationships: List[Dict[str, Any]]) -> bool:
        """
        Update Neo4j knowledge graph with ETIM relationships.
        
        Args:
            class_id: ETIM class identifier
            relationships: List of relationship definitions
            
        Returns:
            Success status
        """
        start_time = time.time()
        
        try:
            if not self.neo4j_driver:
                return False
            
            async with self.neo4j_driver.session() as session:
                # Create or update ETIM class node
                await session.run("""
                    MERGE (etim:ETIMClass {class_id: $class_id})
                    SET etim.updated_at = datetime()
                """, class_id=class_id)
                
                # Process relationships
                for relationship in relationships:
                    rel_type = relationship.get("type")
                    target_id = relationship.get("target_id")
                    target_type = relationship.get("target_type", "Product")
                    properties = relationship.get("properties", {})
                    
                    if rel_type and target_id:
                        await session.run(f"""
                            MATCH (etim:ETIMClass {{class_id: $class_id}})
                            MERGE (target:{target_type} {{id: $target_id}})
                            MERGE (etim)-[r:{rel_type}]->(target)
                            SET r += $properties
                            SET r.updated_at = datetime()
                        """, class_id=class_id, target_id=target_id, properties=properties)
            
            # Invalidate related cache entries
            await self._invalidate_cache_pattern(f"etim_hierarchy:{class_id}*")
            
            self._record_performance("graph_update", start_time)
            return True
            
        except Exception as e:
            self._record_performance("graph_update_error", start_time)
            print(f"Error updating knowledge graph for {class_id}: {e}")
            return False
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics"""
        total_queries = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_queries) if total_queries > 0 else 0
        
        # Calculate average response times by operation type
        avg_times = {}
        for metric in self.performance_metrics:
            op_type = metric["operation"]
            if op_type not in avg_times:
                avg_times[op_type] = []
            avg_times[op_type].append(metric["duration_ms"])
        
        avg_response_times = {
            op: sum(times) / len(times) for op, times in avg_times.items()
        }
        
        return {
            "cache_performance": {
                "hit_rate": cache_hit_rate,
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "total_queries": total_queries
            },
            "response_times": avg_response_times,
            "sla_compliance": {
                "within_500ms_rate": len([m for m in self.performance_metrics if m["duration_ms"] <= 500]) / len(self.performance_metrics) if self.performance_metrics else 0,
                "average_response_ms": sum(m["duration_ms"] for m in self.performance_metrics) / len(self.performance_metrics) if self.performance_metrics else 0
            },
            "service_health": {
                "redis_available": self.redis_client is not None,
                "postgres_available": self.postgres_pool is not None,
                "neo4j_available": self.neo4j_driver is not None
            }
        }
    
    # Private helper methods
    
    async def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    async def _set_cache(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set data in Redis cache"""
        if not self.redis_client:
            return False
        
        try:
            cache_ttl = ttl or self.config.cache_ttl
            await self.redis_client.setex(key, cache_ttl, json.dumps(data))
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def _invalidate_cache_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        if not self.redis_client:
            return
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Cache invalidation error: {e}")
    
    async def _query_etim_class_from_db(self, class_id: str, language: str) -> Optional[Dict[str, Any]]:
        """Query ETIM class from PostgreSQL database"""
        if not self.postgres_pool:
            return self._mock_etim_class(class_id, language)
        
        try:
            async with self.postgres_pool.acquire() as conn:
                # Query with language-specific name
                name_column = f"name_{language}" if language != "en" else "name_en"
                
                result = await conn.fetchrow(f"""
                    SELECT 
                        class_id,
                        name_en,
                        name_de,
                        name_fr,
                        name_es,
                        name_it,
                        name_ja,
                        name_ko,
                        description,
                        version,
                        parent_class,
                        major_group,
                        created_at,
                        updated_at
                    FROM etim_classes 
                    WHERE class_id = $1
                """, class_id)
                
                if result:
                    return dict(result)
                
        except Exception as e:
            print(f"Database query error: {e}")
        
        return None
    
    async def _search_etim_classes_in_db(self, search_term: str, language: str, limit: int, major_group: Optional[str]) -> List[Dict[str, Any]]:
        """Search ETIM classes in database"""
        if not self.postgres_pool:
            return self._mock_search_results(search_term, language, limit)
        
        try:
            async with self.postgres_pool.acquire() as conn:
                # Build query with optional major group filter
                where_clause = "WHERE (LOWER(name_en) LIKE LOWER($1) OR LOWER(description) LIKE LOWER($1))"
                params = [f"%{search_term}%"]
                
                if major_group:
                    where_clause += " AND major_group = $2"
                    params.append(major_group)
                
                query = f"""
                    SELECT class_id, name_en, name_de, name_fr, description, major_group
                    FROM etim_classes 
                    {where_clause}
                    ORDER BY 
                        CASE WHEN LOWER(name_en) = LOWER($1) THEN 1 ELSE 2 END,
                        name_en
                    LIMIT ${len(params) + 1}
                """
                params.append(limit)
                
                results = await conn.fetch(query, *params)
                return [dict(row) for row in results]
                
        except Exception as e:
            print(f"Search query error: {e}")
            return []
    
    async def _build_etim_hierarchy(self, class_id: str) -> Dict[str, Any]:
        """Build ETIM hierarchy from database and knowledge graph"""
        hierarchy = {
            "class_id": class_id,
            "parents": [],
            "children": [],
            "related_tools": [],
            "related_tasks": []
        }
        
        try:
            # Get database hierarchy
            if self.postgres_pool:
                async with self.postgres_pool.acquire() as conn:
                    # Get parent classes
                    parents = await conn.fetch("""
                        WITH RECURSIVE parent_hierarchy AS (
                            SELECT class_id, parent_class, name_en, 1 as level
                            FROM etim_classes WHERE class_id = $1
                            UNION ALL
                            SELECT e.class_id, e.parent_class, e.name_en, ph.level + 1
                            FROM etim_classes e
                            JOIN parent_hierarchy ph ON e.class_id = ph.parent_class
                            WHERE ph.level < 5
                        )
                        SELECT class_id, name_en FROM parent_hierarchy WHERE class_id != $1
                    """, class_id)
                    
                    hierarchy["parents"] = [dict(row) for row in parents]
                    
                    # Get child classes
                    children = await conn.fetch("""
                        SELECT class_id, name_en FROM etim_classes 
                        WHERE parent_class = $1
                        ORDER BY name_en
                    """, class_id)
                    
                    hierarchy["children"] = [dict(row) for row in children]
            
            # Get knowledge graph relationships
            if self.neo4j_driver:
                async with self.neo4j_driver.session() as session:
                    # Get related tools
                    tools_result = await session.run("""
                        MATCH (etim:ETIMClass {class_id: $class_id})<-[:CLASSIFIED_AS]-(tool:Tool)
                        RETURN tool.id, tool.name, tool.category
                        LIMIT 10
                    """, class_id=class_id)
                    
                    hierarchy["related_tools"] = [record.data() async for record in tools_result]
                    
                    # Get related tasks
                    tasks_result = await session.run("""
                        MATCH (etim:ETIMClass {class_id: $class_id})<-[:REQUIRES_CLASSIFICATION]-(task:Task)
                        RETURN task.id, task.name, task.complexity
                        LIMIT 10
                    """, class_id=class_id)
                    
                    hierarchy["related_tasks"] = [record.data() async for record in tasks_result]
            
        except Exception as e:
            hierarchy["error"] = str(e)
        
        return hierarchy
    
    async def _query_technical_attributes(self, class_id: str) -> Dict[str, Any]:
        """Query technical attributes for ETIM class"""
        # Mock implementation for now
        mock_attributes = {
            "EH001234": {
                "EF000001": {
                    "name": "Voltage",
                    "unit": "V",
                    "type": "numeric",
                    "values": ["12", "18", "20", "24"],
                    "required": True
                },
                "EF000002": {
                    "name": "Chuck Size", 
                    "unit": "mm",
                    "type": "numeric",
                    "values": ["10", "13", "16"],
                    "required": False
                }
            },
            "EH005123": {
                "EF000020": {
                    "name": "Material",
                    "unit": "-",
                    "type": "text",
                    "values": ["HDPE", "ABS", "PC"],
                    "required": True
                }
            }
        }
        
        return {
            "class_id": class_id,
            "attributes": mock_attributes.get(class_id, {}),
            "attribute_count": len(mock_attributes.get(class_id, {}))
        }
    
    async def _query_multilingual_names(self, class_id: str) -> Dict[str, str]:
        """Query multilingual names for ETIM class"""
        # Mock implementation with comprehensive language support
        mock_translations = {
            "EH001234": {
                "en": "Cordless Drill",
                "de": "Akku-Bohrmaschine",
                "fr": "Perceuse sans fil",
                "es": "Taladro inalámbrico",
                "it": "Trapano a batteria",
                "ja": "コードレスドリル",
                "ko": "무선 드릴",
                "nl": "Draadloze boor",
                "zh": "无线钻头",
                "pt": "Furadeira sem fio",
                "ru": "Аккумуляторная дрель",
                "tr": "Kablosuz matkap",
                "pl": "Wiertarka bezprzewodowa"
            },
            "EH005123": {
                "en": "Safety Helmet",  
                "de": "Schutzhelm",
                "fr": "Casque de sécurité",
                "es": "Casco de seguridad",
                "it": "Casco di sicurezza",
                "ja": "安全ヘルメット",
                "ko": "안전 헬멧"
            }
        }
        
        return mock_translations.get(class_id, {"en": "Unknown Class"})
    
    def _mock_etim_class(self, class_id: str, language: str) -> Dict[str, Any]:
        """Mock ETIM class data for testing"""
        mock_data = {
            "EH001234": {
                "class_id": "EH001234",
                "name_en": "Cordless Drill",
                "name_de": "Akku-Bohrmaschine",
                "name_fr": "Perceuse sans fil",
                "description": "Portable drilling tool with rechargeable battery",
                "version": "9.0",
                "parent_class": None,
                "major_group": "EH"
            },
            "EH005123": {
                "class_id": "EH005123",
                "name_en": "Safety Helmet",
                "name_de": "Schutzhelm", 
                "name_fr": "Casque de sécurité",
                "description": "Protective headgear for industrial use",
                "version": "9.0",
                "parent_class": None,
                "major_group": "EH"
            }
        }
        
        return mock_data.get(class_id)
    
    def _mock_search_results(self, search_term: str, language: str, limit: int) -> List[Dict[str, Any]]:
        """Mock search results for testing"""
        all_results = [
            {
                "class_id": "EH001234",
                "name_en": "Cordless Drill",
                "description": "Portable drilling tool",
                "major_group": "EH"
            },
            {
                "class_id": "EH001235", 
                "name_en": "Hammer Drill",
                "description": "Percussion drilling tool",
                "major_group": "EH"
            }
        ]
        
        # Filter by search term
        filtered = [
            result for result in all_results
            if search_term.lower() in result["name_en"].lower() or 
               search_term.lower() in result["description"].lower()
        ]
        
        return filtered[:limit]
    
    def _record_performance(self, operation: str, start_time: float):
        """Record performance metric"""
        duration_ms = (time.time() - start_time) * 1000
        self.performance_metrics.append({
            "operation": operation,
            "duration_ms": duration_ms,
            "timestamp": time.time(),
            "within_sla": duration_ms <= self.config.performance_sla_ms
        })
        
        # Keep only recent metrics (last 1000)
        if len(self.performance_metrics) > 1000:
            self.performance_metrics = self.performance_metrics[-1000:]

# Factory function for easy service creation
async def create_etim_service(config: Dict[str, Any] = None) -> ETIMService:
    """
    Create and initialize ETIM service with configuration.
    
    Args:
        config: Service configuration dictionary
        
    Returns:
        Initialized ETIM service instance
    """
    # Convert dict config to dataclass if provided
    if config:
        service_config = ETIMServiceConfig(**config)
    else:
        service_config = ETIMServiceConfig()
    
    service = ETIMService(service_config)
    await service.initialize()
    
    return service