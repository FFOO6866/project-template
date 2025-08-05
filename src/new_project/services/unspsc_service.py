"""
UNSPSC Service Implementation - DATA-001  
========================================

Service implementation for UNSPSC (UN Standard Products and Services Code)
classification with Redis caching and Neo4j knowledge graph integration.

Features:
- UNSPSC 5-level hierarchy (Segment > Family > Class > Commodity)
- 8-digit code structure with 50,000+ codes
- Redis caching for sub-500ms performance
- Neo4j knowledge graph relationships
- Hierarchical traversal and search
- Business rule validation

Performance Requirements:
- Cache hit: <100ms
- Database lookup: <500ms
- Hierarchy traversal: <300ms
- Search operations: <500ms
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Set, Tuple
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
    from core.classification import UNSPSCCode
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False

@dataclass
class UNSPSCServiceConfig:
    """Configuration for UNSPSC service"""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 1  # Different DB from ETIM
    redis_password: Optional[str] = None
    
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "unspsc_db"
    postgres_user: str = "unspsc_user"
    postgres_password: str = "unspsc_pass"
    
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    cache_ttl: int = 3600  # 1 hour
    hierarchy_cache_ttl: int = 7200  # 2 hours (hierarchy is more stable)
    performance_sla_ms: int = 500
    
    # UNSPSC-specific settings
    max_search_results: int = 50
    enable_fuzzy_search: bool = True
    validate_business_rules: bool = True

class UNSPSCService:
    """
    Service for UNSPSC classification with caching and knowledge graph integration.
    
    Provides high-performance UNSPSC classification lookup with hierarchical
    navigation, Redis caching, and Neo4j knowledge graph relationships.
    """
    
    def __init__(self, config: UNSPSCServiceConfig = None):
        self.config = config or UNSPSCServiceConfig()
        self.redis_client: Optional[redis.Redis] = None
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.neo4j_driver = None
        
        # Performance tracking
        self.cache_hits = 0
        self.cache_misses = 0
        self.query_count = 0
        self.performance_metrics = []
        
        # UNSPSC metadata and business rules
        self.major_segments = {
            "10": "Live Plant and Animal Material and Accessories and Supplies",
            "11": "Mineral and Textile and Inedible Plant and Animal Materials",
            "12": "Chemicals including Bio Chemicals and Gas Materials",
            "13": "Resin and Rosin and Rubber and Foam and Film and Elastomeric Materials",
            "14": "Paper Materials and Products",
            "15": "Fuels and Fuel Additives and Lubricants and Anti corrosive Materials",
            "20": "Mining and Well Drilling Machinery and Accessories",
            "21": "Farming and Forestry Machinery and Accessories",
            "22": "Building and Construction Machinery and Accessories",
            "23": "Manufacturing Components and Supplies",
            "24": "Industrial Manufacturing and Processing Machinery and Accessories",
            "25": "Tools and General Machinery",
            "26": "Material Handling and Conditioning and Storage Machinery",
            "27": "Distribution and Conditioning Systems and Equipment and Components",
            "30": "Structures and Building and Construction and Manufacturing Components and Supplies",
            "40": "Service Industry Machinery and Equipment and Supplies",
            "41": "Laboratory and Measuring and Observing and Testing Equipment",
            "42": "Medical Equipment and Accessories and Supplies",
            "43": "Information Technology Broadcasting and Telecommunications",
            "44": "Office Equipment and Accessories and Supplies",
            "45": "Printing and Photographic and Audio and Visual Equipment and Supplies",
            "46": "Defense and Law Enforcement and Security and Safety Equipment and Supplies",
            "47": "Cleaning Equipment and Supplies",
            "48": "Service Industry Equipment and Supplies",
            "49": "Sports and Recreational Equipment and Supplies and Accessories",
            "50": "Food Beverage and Tobacco Products",
            "51": "Drugs and Pharmaceutical Products",
            "52": "Domestic Appliances and Supplies and Consumer Electronic Products",
            "53": "Apparel and Luggage and Personal Care Products",
            "54": "Personal and Domestic Service Products",
            "55": "Retail Trade Services",
            "56": "Financial and Insurance Services",
            "60": "Financial and Insurance Services",
            "70": "Education and Training Services",
            "72": "Building and Facility Construction and Maintenance Services",
            "73": "Industrial Production and Manufacturing Services",
            "76": "Industrial Cleaning Services",
            "77": "Environmental Services",
            "78": "Transportation and Storage and Mail Services",
            "80": "Management and Business Professionals and Administrative Services",
            "81": "Engineering and Research and Technology Based Services",
            "82": "Editorial and Design and Graphic and Fine Art Services",
            "83": "Public Utilities and Public Sector Related Services",
            "84": "Recreational Services",
            "85": "Personal and Domestic Services",
            "86": "International Organizations and Bodies",
            "90": "Travel and Food and Lodging and Entertainment Services",
            "91": "Personal and Domestic Services",
            "92": "National Defense and Public Order and Security Services",
            "93": "Politics and Civic Affairs Services",
            "94": "Organizations and Clubs"
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
                    max_size=15
                )
            
            # Initialize Neo4j
            if NEO4J_AVAILABLE:
                self.neo4j_driver = AsyncGraphDatabase.driver(
                    self.config.neo4j_uri,
                    auth=(self.config.neo4j_user, self.config.neo4j_password)
                )
                await self.neo4j_driver.verify_connectivity()
            
            # Warm up cache with frequently accessed codes
            await self._warm_up_cache()
            
            return True
            
        except Exception as e:
            print(f"UNSPSC Service initialization error: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup service connections"""
        if self.redis_client:
            await self.redis_client.close()
        
        if self.postgres_pool:
            await self.postgres_pool.close()
        
        if self.neo4j_driver:
            await self.neo4j_driver.close()
    
    async def get_unspsc_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get UNSPSC code information with caching.
        
        Args:
            code: 8-digit UNSPSC code (e.g., "25171500")
            
        Returns:
            UNSPSC code data or None if not found
        """
        start_time = time.time()
        
        try:
            # Validate code format
            if not self._is_valid_unspsc_code(code):
                self._record_performance("validation_error", start_time)
                return None
            
            # Try cache first
            cache_key = f"unspsc_code:{code}"
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.cache_hits += 1
                self._record_performance("cache_hit", start_time)
                return cached_result
            
            self.cache_misses += 1
            
            # Query database
            unspsc_data = await self._query_unspsc_code_from_db(code)
            
            if unspsc_data:
                # Enhance with computed fields
                unspsc_data = await self._enhance_unspsc_data(unspsc_data)
                
                # Cache the result
                await self._set_cache(cache_key, unspsc_data, self.config.cache_ttl)
                self._record_performance("db_query", start_time)
                return unspsc_data
            
            return None
            
        except Exception as e:
            self._record_performance("error", start_time)
            print(f"Error getting UNSPSC code {code}: {e}")
            return None
    
    async def search_unspsc_codes(self, 
                                 search_term: str,
                                 segment: Optional[str] = None,
                                 family: Optional[str] = None,
                                 limit: int = 20,
                                 include_hierarchy: bool = True) -> List[Dict[str, Any]]:
        """
        Search UNSPSC codes by title or description.
        
        Args:
            search_term: Search query
            segment: Optional segment filter (2 digits)
            family: Optional family filter (4 digits)
            limit: Maximum number of results
            include_hierarchy: Include hierarchy information
            
        Returns:
            List of matching UNSPSC codes with relevance scoring
        """
        start_time = time.time()
        
        try:
            # Create cache key
            cache_key = f"unspsc_search:{hash(search_term)}:{segment or 'all'}:{family or 'all'}:{limit}:{include_hierarchy}"
            
            # Try cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.cache_hits += 1
                self._record_performance("search_cache_hit", start_time)
                return cached_result
            
            self.cache_misses += 1
            
            # Perform search in database
            search_results = await self._search_unspsc_codes_in_db(
                search_term, segment, family, limit, include_hierarchy
            )
            
            # Apply relevance scoring
            scored_results = self._apply_relevance_scoring(search_results, search_term)
            
            # Cache results for shorter time (search results may change)
            await self._set_cache(cache_key, scored_results, ttl=600)  # 10 minutes
            
            self._record_performance("search_db_query", start_time)
            return scored_results
            
        except Exception as e:
            self._record_performance("search_error", start_time)
            print(f"Error searching UNSPSC codes: {e}")
            return []
    
    async def get_hierarchy_path(self, code: str) -> List[Dict[str, Any]]:
        """
        Get complete hierarchy path for UNSPSC code.
        
        Args:
            code: 8-digit UNSPSC commodity code
            
        Returns:
            List of hierarchy levels from segment to commodity
        """
        start_time = time.time()
        
        try:
            if not self._is_valid_unspsc_code(code):
                return []
            
            cache_key = f"unspsc_hierarchy:{code}"
            
            # Try cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.cache_hits += 1
                self._record_performance("hierarchy_cache_hit", start_time)
                return cached_result
            
            self.cache_misses += 1
            
            # Build hierarchy path
            hierarchy_path = await self._build_hierarchy_path(code)
            
            # Cache hierarchy (very stable data)
            await self._set_cache(cache_key, hierarchy_path, self.config.hierarchy_cache_ttl)
            
            self._record_performance("hierarchy_build", start_time)
            return hierarchy_path
            
        except Exception as e:
            self._record_performance("hierarchy_error", start_time)
            print(f"Error building hierarchy for {code}: {e}")
            return []
    
    async def get_children_codes(self, parent_code: str) -> List[Dict[str, Any]]:
        """
        Get child codes for a parent UNSPSC code.
        
        Args:
            parent_code: Parent UNSPSC code (segment, family, or class)
            
        Returns:
            List of child codes with their information
        """
        start_time = time.time()
        
        try:
            cache_key = f"unspsc_children:{parent_code}"
            
            # Try cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.cache_hits += 1
                self._record_performance("children_cache_hit", start_time)
                return cached_result
            
            self.cache_misses += 1
            
            # Query child codes
            children = await self._query_children_codes(parent_code)
            
            # Cache children (stable data)
            await self._set_cache(cache_key, children, self.config.hierarchy_cache_ttl)
            
            self._record_performance("children_query", start_time)
            return children
            
        except Exception as e:
            self._record_performance("children_error", start_time)
            print(f"Error getting children for {parent_code}: {e}")
            return []
    
    async def get_similar_codes(self, code: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get similar UNSPSC codes based on hierarchy and semantic similarity.
        
        Args:
            code: Reference UNSPSC code
            limit: Maximum number of similar codes
            
        Returns:
            List of similar codes with similarity scores
        """
        start_time = time.time()
        
        try:
            if not self._is_valid_unspsc_code(code):
                return []
            
            cache_key = f"unspsc_similar:{code}:{limit}"
            
            # Try cache first
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.cache_hits += 1
                self._record_performance("similar_cache_hit", start_time)
                return cached_result
            
            self.cache_misses += 1
            
            # Find similar codes using multiple strategies
            similar_codes = await self._find_similar_codes(code, limit)
            
            # Cache similar codes
            await self._set_cache(cache_key, similar_codes, ttl=1800)  # 30 minutes
            
            self._record_performance("similar_query", start_time)
            return similar_codes
            
        except Exception as e:
            self._record_performance("similar_error", start_time)
            print(f"Error finding similar codes for {code}: {e}")
            return []
    
    async def validate_business_rules(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate UNSPSC code against business rules.
        
        Args:
            code: UNSPSC code to validate
            context: Additional context for validation
            
        Returns:
            Validation result with compliance status and recommendations
        """
        start_time = time.time()
        
        try:
            if not self.config.validate_business_rules:
                return {"valid": True, "rules_checked": 0}
            
            validation_result = {
                "code": code,
                "valid": True,
                "violations": [],
                "warnings": [],
                "recommendations": [],
                "rules_checked": 0
            }
            
            # Rule 1: Code format validation
            if not self._is_valid_unspsc_code(code):
                validation_result["violations"].append({
                    "rule": "format_validation",
                    "message": "Invalid UNSPSC code format",
                    "severity": "high"
                })
                validation_result["valid"] = False
            
            validation_result["rules_checked"] += 1
            
            # Rule 2: Hierarchy consistency
            if validation_result["valid"]:
                hierarchy_valid = await self._validate_hierarchy_consistency(code)
                if not hierarchy_valid:
                    validation_result["warnings"].append({
                        "rule": "hierarchy_consistency",
                        "message": "Code may not follow standard hierarchy patterns",
                        "severity": "medium"
                    })
                
                validation_result["rules_checked"] += 1
            
            # Rule 3: Context-specific validation
            if context and validation_result["valid"]:
                context_validation = self._validate_context_rules(code, context)
                validation_result["recommendations"].extend(context_validation)
                validation_result["rules_checked"] += 1
            
            self._record_performance("business_rules_validation", start_time)
            return validation_result
            
        except Exception as e:
            self._record_performance("validation_error", start_time)
            return {
                "code": code,
                "valid": False,
                "error": str(e),
                "rules_checked": 0
            }
    
    async def update_knowledge_graph_relationships(self, code: str, relationships: List[Dict[str, Any]]) -> bool:
        """
        Update Neo4j knowledge graph with UNSPSC relationships.
        
        Args:
            code: UNSPSC code
            relationships: List of relationship definitions
            
        Returns:
            Success status
        """
        start_time = time.time()
        
        try:
            if not self.neo4j_driver:
                return False
            
            async with self.neo4j_driver.session() as session:
                # Create or update UNSPSC code node
                unspsc_data = await self.get_unspsc_code(code)
                if not unspsc_data:
                    return False
                
                await session.run("""
                    MERGE (unspsc:UNSPSCCode {code: $code})
                    SET unspsc.title = $title,
                        unspsc.segment = $segment,
                        unspsc.family = $family,
                        unspsc.level = $level,
                        unspsc.updated_at = datetime()
                """, 
                code=code,
                title=unspsc_data.get("title", ""),
                segment=unspsc_data.get("segment", ""),
                family=unspsc_data.get("family", ""),
                level=unspsc_data.get("level", 0)
                )
                
                # Process relationships
                for relationship in relationships:
                    rel_type = relationship.get("type")
                    target_id = relationship.get("target_id")
                    target_type = relationship.get("target_type", "Product")
                    properties = relationship.get("properties", {})
                    
                    if rel_type and target_id:
                        await session.run(f"""
                            MATCH (unspsc:UNSPSCCode {{code: $code}})
                            MERGE (target:{target_type} {{id: $target_id}})
                            MERGE (unspsc)-[r:{rel_type}]->(target)
                            SET r += $properties
                            SET r.updated_at = datetime()
                        """, code=code, target_id=target_id, properties=properties)
            
            # Invalidate related cache entries
            await self._invalidate_cache_pattern(f"unspsc_hierarchy:{code}*")
            await self._invalidate_cache_pattern(f"unspsc_similar:{code}*")
            
            self._record_performance("graph_update", start_time)
            return True
            
        except Exception as e:
            self._record_performance("graph_update_error", start_time)
            print(f"Error updating knowledge graph for {code}: {e}")
            return False
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service performance metrics"""
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
                "total_queries": total_queries,
                "efficiency_rating": "excellent" if cache_hit_rate > 0.8 else "good" if cache_hit_rate > 0.6 else "poor"
            },
            "response_times": avg_response_times,
            "sla_compliance": {
                "within_500ms_rate": len([m for m in self.performance_metrics if m["duration_ms"] <= 500]) / len(self.performance_metrics) if self.performance_metrics else 0,
                "average_response_ms": sum(m["duration_ms"] for m in self.performance_metrics) / len(self.performance_metrics) if self.performance_metrics else 0,
                "p95_response_ms": self._calculate_percentile([m["duration_ms"] for m in self.performance_metrics], 95) if self.performance_metrics else 0
            },
            "service_health": {
                "redis_available": self.redis_client is not None,
                "postgres_available": self.postgres_pool is not None,
                "neo4j_available": self.neo4j_driver is not None,
                "business_rules_enabled": self.config.validate_business_rules
            },
            "data_statistics": {
                "segments_count": len(self.major_segments),
                "search_enabled": True,
                "hierarchy_levels": 4
            }
        }
    
    # Private helper methods
    
    def _is_valid_unspsc_code(self, code: str) -> bool:
        """Validate UNSPSC code format"""
        if not isinstance(code, str) or len(code) != 8:
            return False
        
        if not code.isdigit():
            return False
        
        if code.startswith('00'):
            return False
        
        return True
    
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
    
    async def _warm_up_cache(self):
        """Warm up cache with frequently accessed UNSPSC codes"""
        # Pre-cache major segments and common tool codes
        common_codes = [
            "25000000",  # Tools and General Machinery segment
            "25170000",  # Power Tools family
            "25171500",  # Power drills
            "25171501",  # Cordless drills
            "46000000",  # Safety Equipment segment
            "46180000",  # Safety Equipment family
            "46181501"   # Safety helmets
        ]
        
        for code in common_codes:
            if self._is_valid_unspsc_code(code):
                await self.get_unspsc_code(code)
    
    async def _query_unspsc_code_from_db(self, code: str) -> Optional[Dict[str, Any]]:
        """Query UNSPSC code from PostgreSQL database"""
        if not self.postgres_pool:
            return self._mock_unspsc_code(code)
        
        try:
            async with self.postgres_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT 
                        code,
                        title,
                        description,
                        segment,
                        family,
                        class_code,
                        commodity,
                        level,
                        parent_code,
                        created_at,
                        updated_at
                    FROM unspsc_codes 
                    WHERE code = $1
                """, code)
                
                if result:
                    return dict(result)
                
        except Exception as e:
            print(f"Database query error: {e}")
        
        return None
    
    async def _enhance_unspsc_data(self, unspsc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance UNSPSC data with computed fields"""
        code = unspsc_data["code"]
        
        # Add segment information
        segment_code = code[:2]
        unspsc_data["segment_title"] = self.major_segments.get(segment_code, "Unknown Segment")
        
        # Add hierarchy validation
        unspsc_data["hierarchy_valid"] = self._validate_code_hierarchy(code)
        
        # Add business context
        unspsc_data["business_context"] = self._get_business_context(code)
        
        return unspsc_data
    
    async def _search_unspsc_codes_in_db(self, search_term: str, segment: Optional[str], family: Optional[str], limit: int, include_hierarchy: bool) -> List[Dict[str, Any]]:
        """Search UNSPSC codes in database"""
        if not self.postgres_pool:
            return self._mock_search_results(search_term, limit)
        
        try:
            async with self.postgres_pool.acquire() as conn:
                # Build dynamic query
                where_conditions = ["(LOWER(title) LIKE LOWER($1) OR LOWER(description) LIKE LOWER($1))"]
                params = [f"%{search_term}%"]
                param_count = 1
                
                if segment:
                    param_count += 1
                    where_conditions.append(f"segment = ${param_count}")
                    params.append(segment)
                
                if family:
                    param_count += 1
                    where_conditions.append(f"family = ${param_count}")
                    params.append(family)
                
                where_clause = " AND ".join(where_conditions)
                
                query = f"""
                    SELECT code, title, description, segment, family, level
                    FROM unspsc_codes 
                    WHERE {where_clause}
                    ORDER BY 
                        CASE WHEN LOWER(title) = LOWER($1) THEN 1 ELSE 2 END,
                        level DESC,
                        title
                    LIMIT ${param_count + 1}
                """
                params.append(limit)
                
                results = await conn.fetch(query, *params)
                return [dict(row) for row in results]
                
        except Exception as e:
            print(f"Search query error: {e}")
            return []
    
    def _apply_relevance_scoring(self, results: List[Dict[str, Any]], search_term: str) -> List[Dict[str, Any]]:
        """Apply relevance scoring to search results"""
        search_lower = search_term.lower()
        
        for result in results:
            score = 0.0
            title = result.get("title", "").lower()
            description = result.get("description", "").lower()
            
            # Exact title match
            if title == search_lower:
                score += 100
            # Title starts with search term
            elif title.startswith(search_lower):
                score += 80
            # Title contains search term
            elif search_lower in title:
                score += 60
            # Description contains search term
            elif search_lower in description:
                score += 40
            
            # Boost for more specific codes (higher level)
            score += result.get("level", 0) * 5
            
            # Boost for common segments (tools, safety)
            segment = result.get("segment", "")
            if segment in ["25", "46"]:
                score += 10
            
            result["relevance_score"] = score
        
        # Sort by relevance score
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)
    
    async def _build_hierarchy_path(self, code: str) -> List[Dict[str, Any]]:
        """Build complete hierarchy path for UNSPSC code"""
        if CORE_AVAILABLE:
            try:
                unspsc_obj = UNSPSCCode(code=code, title="Temp")
                hierarchy_codes = unspsc_obj.get_hierarchy_path()
                
                # Get details for each level
                hierarchy_path = []
                for level_code in hierarchy_codes:
                    level_data = await self.get_unspsc_code(level_code)
                    if level_data:
                        hierarchy_path.append(level_data)
                
                return hierarchy_path
                
            except Exception as e:
                print(f"Hierarchy build error: {e}")
        
        # Fallback implementation
        return self._mock_hierarchy_path(code)
    
    async def _query_children_codes(self, parent_code: str) -> List[Dict[str, Any]]:
        """Query child codes for parent UNSPSC code"""
        if not self.postgres_pool:
            return self._mock_children_codes(parent_code)
        
        try:
            async with self.postgres_pool.acquire() as conn:
                # Determine search pattern based on parent code length
                if len(parent_code) == 8:  # Commodity level - no children
                    return []
                elif len(parent_code) == 6:  # Class level - find commodities
                    pattern = parent_code + "__"
                elif len(parent_code) == 4:  # Family level - find classes
                    pattern = parent_code + "____"
                elif len(parent_code) == 2:  # Segment level - find families
                    pattern = parent_code + "______"
                else:
                    return []
                
                results = await conn.fetch("""
                    SELECT code, title, level
                    FROM unspsc_codes 
                    WHERE code LIKE $1 AND code != $2
                    ORDER BY code
                    LIMIT 50
                """, pattern.replace("_", "%"), parent_code)
                
                return [dict(row) for row in results]
                
        except Exception as e:
            print(f"Children query error: {e}")
            return []
    
    async def _find_similar_codes(self, code: str, limit: int) -> List[Dict[str, Any]]:
        """Find similar UNSPSC codes using multiple strategies"""
        similar_codes = []
        
        # Strategy 1: Same family codes
        family_code = code[:4]
        family_similar = await self._query_children_codes(family_code)
        
        for similar in family_similar[:limit//2]:
            if similar["code"] != code:
                similar["similarity_type"] = "same_family"
                similar["similarity_score"] = 0.8
                similar_codes.append(similar)
        
        # Strategy 2: Same class codes
        if len(similar_codes) < limit:
            class_code = code[:6]
            class_similar = await self._query_children_codes(class_code)
            
            for similar in class_similar:
                if similar["code"] != code and similar["code"] not in [s["code"] for s in similar_codes]:
                    similar["similarity_type"] = "same_class"
                    similar["similarity_score"] = 0.9
                    similar_codes.append(similar)
                    
                    if len(similar_codes) >= limit:
                        break
        
        return similar_codes[:limit]
    
    async def _validate_hierarchy_consistency(self, code: str) -> bool:
        """Validate that code follows proper hierarchy patterns"""
        try:
            if CORE_AVAILABLE:
                unspsc_obj = UNSPSCCode(code=code, title="Validation")
                return unspsc_obj.level > 0
            return True
        except:
            return False
    
    def _validate_context_rules(self, code: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Validate context-specific business rules"""
        recommendations = []
        
        # Industry-specific recommendations
        industry = context.get("industry")
        if industry == "construction" and not code.startswith(("25", "46")):
            recommendations.append({
                "type": "industry_alignment",
                "message": "Consider tools (25) or safety equipment (46) codes for construction industry"
            })
        
        # Product type recommendations
        product_type = context.get("product_type")
        if product_type == "power_tool" and not code.startswith("2517"):
            recommendations.append({
                "type": "product_alignment", 
                "message": "Power tools typically use 2517xxxx family codes"
            })
        
        return recommendations
    
    def _validate_code_hierarchy(self, code: str) -> bool:
        """Validate that code follows proper hierarchy structure"""
        if len(code) != 8:
            return False
        
        segment = code[:2]
        family = code[:4]
        class_code = code[:6]
        
        # Check if segment exists
        if segment not in self.major_segments:
            return False
        
        # Additional validation logic would go here
        return True
    
    def _get_business_context(self, code: str) -> Dict[str, Any]:
        """Get business context for UNSPSC code"""
        segment = code[:2]
        context = {
            "segment_name": self.major_segments.get(segment, "Unknown"),
            "is_product": int(segment) < 50,
            "is_service": int(segment) >= 50
        }
        
        # Add specific context for tool codes
        if segment == "25":
            context["category"] = "tools_machinery"
            context["typical_users"] = ["construction", "manufacturing", "maintenance"]
        elif segment == "46":
            context["category"] = "safety_security"
            context["regulatory_considerations"] = ["OSHA", "ANSI", "safety_standards"]
        
        return context
    
    def _mock_unspsc_code(self, code: str) -> Dict[str, Any]:
        """Mock UNSPSC code data for testing"""
        mock_data = {
            "25171500": {
                "code": "25171500",
                "title": "Power drills",
                "description": "Electric and pneumatic drilling tools",
                "segment": "25",
                "family": "2517",
                "class_code": "251715",
                "commodity": "25171500",
                "level": 4
            },
            "25171501": {
                "code": "25171501",
                "title": "Cordless drills",
                "description": "Battery-powered portable drilling tools",
                "segment": "25",
                "family": "2517",
                "class_code": "251715",
                "commodity": "25171501",
                "level": 4
            },
            "46181501": {
                "code": "46181501",
                "title": "Safety helmets",
                "description": "Protective headgear for industrial use",
                "segment": "46",
                "family": "4618",
                "class_code": "461815",
                "commodity": "46181501",
                "level": 4
            }
        }
        
        return mock_data.get(code)
    
    def _mock_search_results(self, search_term: str, limit: int) -> List[Dict[str, Any]]:
        """Mock search results for testing"""
        all_results = [
            {"code": "25171500", "title": "Power drills", "level": 4, "relevance_score": 90},
            {"code": "25171501", "title": "Cordless drills", "level": 4, "relevance_score": 85},
            {"code": "25171502", "title": "Hammer drills", "level": 4, "relevance_score": 80}
        ]
        
        # Filter by search term
        filtered = [
            result for result in all_results
            if search_term.lower() in result["title"].lower()
        ]
        
        return filtered[:limit]
    
    def _mock_hierarchy_path(self, code: str) -> List[Dict[str, Any]]:
        """Mock hierarchy path for testing"""
        if code == "25171501":
            return [
                {"code": "25000000", "title": "Tools and General Machinery", "level": 1},
                {"code": "25170000", "title": "Power Tools", "level": 2},
                {"code": "25171500", "title": "Portable Power Drills", "level": 3},
                {"code": "25171501", "title": "Cordless drills", "level": 4}
            ]
        return []
    
    def _mock_children_codes(self, parent_code: str) -> List[Dict[str, Any]]:
        """Mock children codes for testing"""
        if parent_code == "2517":
            return [
                {"code": "25171500", "title": "Power drills", "level": 4},
                {"code": "25171501", "title": "Cordless drills", "level": 4},
                {"code": "25171502", "title": "Hammer drills", "level": 4}
            ]
        return []
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value from list"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
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
async def create_unspsc_service(config: Dict[str, Any] = None) -> UNSPSCService:
    """
    Create and initialize UNSPSC service with configuration.
    
    Args:
        config: Service configuration dictionary
        
    Returns:
        Initialized UNSPSC service instance
    """
    # Convert dict config to dataclass if provided
    if config:
        service_config = UNSPSCServiceConfig(**config)
    else:
        service_config = UNSPSCServiceConfig()
    
    service = UNSPSCService(service_config)
    await service.initialize()
    
    return service