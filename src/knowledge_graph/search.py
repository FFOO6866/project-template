"""
Semantic Search Engine

This module implements semantic search capabilities using vector embeddings,
natural language query processing, and graph-based relationship exploration.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import asyncio
import re
from dataclasses import dataclass, asdict

import numpy as np
import openai
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .database import Neo4jConnection, GraphDatabase
from .models import SemanticSearchQuery, RelationshipType

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Individual search result with similarity scores and metadata"""
    product_id: int
    sku: str
    name: str
    description: Optional[str]
    brand_name: Optional[str]
    category_name: Optional[str]
    price: Optional[float]
    
    # Similarity scores
    semantic_similarity: float
    text_similarity: float
    graph_similarity: float
    combined_score: float
    
    # Relationships and context
    relationships: List[Dict[str, Any]]
    match_reasons: List[str]
    
    # Metadata
    rank: int
    search_time: datetime


@dataclass 
class SearchContext:
    """Context for search query processing"""
    original_query: str
    processed_query: str
    intent: str  # product_search, compatibility_check, project_recommendation
    entities: List[str]  # Extracted entities (brands, categories, etc.)
    keywords: List[str]
    filters: Dict[str, Any]


class SemanticSearchEngine:
    """
    Advanced semantic search engine for product discovery and recommendations.
    
    Combines multiple search strategies:
    - Vector similarity using embeddings
    - Traditional text search (TF-IDF)
    - Graph-based relationship traversal
    - Natural language query understanding
    """
    
    def __init__(
        self,
        neo4j_connection: Neo4jConnection,
        chromadb_host: str = "localhost",
        chromadb_port: int = 8000,
        openai_api_key: str = None,
        use_sentence_transformers: bool = True
    ):
        """
        Initialize the semantic search engine.
        
        Args:
            neo4j_connection: Neo4j database connection
            chromadb_host: ChromaDB host address
            chromadb_port: ChromaDB port
            openai_api_key: OpenAI API key for embeddings
            use_sentence_transformers: Whether to use local sentence transformers
        """
        self.graph_db = GraphDatabase(neo4j_connection)
        self.neo4j_conn = neo4j_connection
        
        # Vector database setup
        self.chromadb_client = chromadb.HttpClient(
            host=chromadb_host,
            port=chromadb_port,
            settings=Settings(allow_reset=True)
        )
        
        # Initialize embedding models
        self.openai_api_key = openai_api_key
        if openai_api_key:
            openai.api_key = openai_api_key
        
        self.sentence_transformer = None
        if use_sentence_transformers:
            try:
                self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence transformer model")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}")
        
        # Text search vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.95
        )
        
        # Collections for different search types
        self.collections = {}
        self._initialize_collections()
        
        # Query processing patterns
        self.intent_patterns = {
            'compatibility': [
                r'compatible with',
                r'works with',
                r'fits',
                r'battery for',
                r'charger for'
            ],
            'project': [
                r'for (.+?) project',
                r'(.+?) renovation',
                r'build a (.+)',
                r'diy (.+)',
                r'tools for (.+)'
            ],
            'alternative': [
                r'alternative to',
                r'similar to',
                r'instead of',
                r'replacement for'
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            'brand': r'\b(makita|dewalt|milwaukee|ryobi|bosch|black\+?decker|craftsman|porter[- ]cable)\b',
            'voltage': r'\b(\d+(?:\.\d+)?)\s*v(?:olt)?s?\b',
            'category': r'\b(drill|saw|hammer|battery|charger|impact|grinder|sander|router)\b',
            'measurement': r'\b(\d+(?:\.\d+)?)\s*(inch|inches|mm|cm|ft|feet|amp|ah)\b'
        }
    
    def _initialize_collections(self):
        """Initialize ChromaDB collections for different search types"""
        try:
            # Product embeddings collection
            self.collections['products'] = self.chromadb_client.get_or_create_collection(
                name="horme_products",
                metadata={"description": "Product embeddings for semantic search"}
            )
            
            # Project/use-case embeddings
            self.collections['projects'] = self.chromadb_client.get_or_create_collection(
                name="horme_projects", 
                metadata={"description": "DIY project and use-case embeddings"}
            )
            
            logger.info("ChromaDB collections initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB collections: {e}")
            self.collections = {}
    
    # ===========================================
    # MAIN SEARCH METHODS
    # ===========================================
    
    async def search(
        self,
        query: str,
        limit: int = 20,
        min_similarity: float = 0.6,
        include_relationships: bool = True,
        filters: Optional[Dict[str, Any]] = None,
        search_strategy: str = "hybrid"  # semantic, text, graph, hybrid
    ) -> List[SearchResult]:
        """
        Perform semantic search for products.
        
        Args:
            query: Natural language search query
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            include_relationships: Whether to include related products
            filters: Additional filters (brand, category, price range, etc.)
            search_strategy: Search strategy to use
            
        Returns:
            List of SearchResult objects ranked by relevance
        """
        start_time = datetime.utcnow()
        
        # Process and understand the query
        context = await self._process_query(query, filters or {})
        logger.info(f"Query intent: {context.intent}, entities: {context.entities}")
        
        # Route to appropriate search strategy
        if search_strategy == "hybrid":
            results = await self._hybrid_search(context, limit, min_similarity)
        elif search_strategy == "semantic":
            results = await self._semantic_search(context, limit, min_similarity)
        elif search_strategy == "text":
            results = await self._text_search(context, limit, min_similarity)
        elif search_strategy == "graph":
            results = await self._graph_search(context, limit, min_similarity)
        else:
            raise ValueError(f"Unknown search strategy: {search_strategy}")
        
        # Include relationships if requested
        if include_relationships:
            results = await self._enrich_with_relationships(results, context)
        
        # Set search metadata
        search_time = datetime.utcnow()
        for i, result in enumerate(results):
            result.rank = i + 1
            result.search_time = search_time
        
        logger.info(f"Search completed in {(search_time - start_time).total_seconds():.2f}s, {len(results)} results")
        return results
    
    async def find_compatible_products(
        self,
        product_id: int,
        compatibility_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Find products compatible with a specific product.
        
        Args:
            product_id: Product to find compatibility for
            compatibility_types: Types of compatibility to search for
            limit: Maximum number of results
            
        Returns:
            List of compatible products with compatibility details
        """
        # Get the source product
        product = self.graph_db.get_product_node(product_id=product_id)
        if not product:
            logger.error(f"Product {product_id} not found")
            return []
        
        # Get compatible products from graph
        compatible_products = self.graph_db.find_compatible_products(
            product_id=product_id,
            min_confidence=0.6
        )
        
        # Convert to SearchResult objects
        results = []
        for comp_data in compatible_products[:limit]:
            result = SearchResult(
                product_id=comp_data['product_id'],
                sku=comp_data['sku'],
                name=comp_data['name'],
                description=None,
                brand_name=comp_data.get('brand_name'),
                category_name=None,
                price=comp_data.get('price'),
                semantic_similarity=0.0,
                text_similarity=0.0,
                graph_similarity=comp_data['confidence'],
                combined_score=comp_data['confidence'],
                relationships=[{
                    'type': 'COMPATIBLE_WITH',
                    'confidence': comp_data['confidence'],
                    'compatibility_type': comp_data.get('compatibility_type'),
                    'notes': comp_data.get('compatibility_notes')
                }],
                match_reasons=[f"Compatible via {comp_data.get('compatibility_type', 'general compatibility')}"],
                rank=0,
                search_time=datetime.utcnow()
            )
            results.append(result)
        
        return results
    
    async def recommend_for_project(
        self,
        project_description: str,
        budget_range: Optional[str] = None,
        skill_level: Optional[str] = None,
        limit: int = 15
    ) -> List[SearchResult]:
        """
        Recommend products for a DIY project.
        
        Args:
            project_description: Description of the project
            budget_range: Budget constraint (low, medium, high)
            skill_level: Required skill level
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended products for the project
        """
        # Create search context for project
        context = await self._process_query(
            f"tools and materials for {project_description}",
            {"budget_range": budget_range, "skill_level": skill_level}
        )
        
        # Combine semantic search with project knowledge
        semantic_results = await self._semantic_search(context, limit * 2, 0.5)
        
        # Get project-specific recommendations from graph
        project_type = self._classify_project_type(project_description)
        if project_type:
            graph_results = self.graph_db.find_project_recommendations(
                project_type=project_type,
                budget_range=budget_range,
                skill_level=skill_level
            )
            
            # Merge and rank results
            merged_results = self._merge_project_results(semantic_results, graph_results)
            return merged_results[:limit]
        
        return semantic_results[:limit]
    
    # ===========================================
    # SEARCH STRATEGY IMPLEMENTATIONS
    # ===========================================
    
    async def _hybrid_search(
        self,
        context: SearchContext,
        limit: int,
        min_similarity: float
    ) -> List[SearchResult]:
        """Combine multiple search strategies for best results"""
        
        # Run different search strategies in parallel
        semantic_task = self._semantic_search(context, limit, min_similarity * 0.8)
        text_task = self._text_search(context, limit, min_similarity * 0.7)
        graph_task = self._graph_search(context, limit, min_similarity * 0.6)
        
        semantic_results, text_results, graph_results = await asyncio.gather(
            semantic_task, text_task, graph_task
        )
        
        # Merge and re-rank results
        merged_results = self._merge_search_results([
            (semantic_results, 0.4),  # 40% weight for semantic
            (text_results, 0.3),      # 30% weight for text  
            (graph_results, 0.3)      # 30% weight for graph
        ])
        
        return merged_results[:limit]
    
    async def _semantic_search(
        self,
        context: SearchContext,
        limit: int,
        min_similarity: float
    ) -> List[SearchResult]:
        """Search using vector embeddings and semantic similarity"""
        
        if 'products' not in self.collections:
            logger.warning("Product embeddings collection not available")
            return []
        
        try:
            # Get query embedding
            query_embedding = await self._get_embedding(context.processed_query)
            if not query_embedding:
                return []
            
            # Search in ChromaDB
            results = self.collections['products'].query(
                query_embeddings=[query_embedding],
                n_results=limit * 2,
                where=self._build_chromadb_filters(context.filters)
            )
            
            # Convert to SearchResult objects
            search_results = []
            
            if results['ids'] and results['ids'][0]:
                for i, (doc_id, distance, metadata) in enumerate(zip(
                    results['ids'][0],
                    results['distances'][0], 
                    results['metadatas'][0]
                )):
                    similarity = 1 - distance  # Convert distance to similarity
                    
                    if similarity < min_similarity:
                        continue
                    
                    result = SearchResult(
                        product_id=int(doc_id),
                        sku=metadata.get('sku', ''),
                        name=metadata.get('name', ''),
                        description=metadata.get('description'),
                        brand_name=metadata.get('brand_name'),
                        category_name=metadata.get('category_name'),
                        price=metadata.get('price'),
                        semantic_similarity=similarity,
                        text_similarity=0.0,
                        graph_similarity=0.0,
                        combined_score=similarity,
                        relationships=[],
                        match_reasons=[f"Semantic similarity: {similarity:.2f}"],
                        rank=0,
                        search_time=datetime.utcnow()
                    )
                    
                    search_results.append(result)
            
            return search_results[:limit]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def _text_search(
        self,
        context: SearchContext,
        limit: int,
        min_similarity: float
    ) -> List[SearchResult]:
        """Traditional text-based search using TF-IDF"""
        
        # Build Neo4j fulltext search query
        search_terms = ' '.join(context.keywords)
        
        query = """
        CALL db.index.fulltext.queryNodes("product_fulltext_index", $search_terms)
        YIELD node, score
        WHERE score >= $min_score
        RETURN node.product_id as product_id,
               node.sku as sku,
               node.name as name,
               node.description as description,
               node.brand_name as brand_name,
               node.category_name as category_name,
               node.price as price,
               score
        ORDER BY score DESC
        LIMIT $limit
        """
        
        try:
            with self.neo4j_conn.session() as session:
                results = session.run(query, {
                    'search_terms': search_terms,
                    'min_score': min_similarity,
                    'limit': limit
                })
                
                search_results = []
                for record in results:
                    score = float(record['score'])
                    
                    result = SearchResult(
                        product_id=record['product_id'],
                        sku=record['sku'],
                        name=record['name'],
                        description=record['description'],
                        brand_name=record['brand_name'],
                        category_name=record['category_name'],
                        price=record['price'],
                        semantic_similarity=0.0,
                        text_similarity=score,
                        graph_similarity=0.0,
                        combined_score=score,
                        relationships=[],
                        match_reasons=[f"Text match score: {score:.2f}"],
                        rank=0,
                        search_time=datetime.utcnow()
                    )
                    
                    search_results.append(result)
                
                return search_results
                
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []
    
    async def _graph_search(
        self,
        context: SearchContext,
        limit: int,
        min_similarity: float
    ) -> List[SearchResult]:
        """Search using graph relationships and traversal"""
        
        # Find seed products based on entities
        seed_products = await self._find_seed_products(context)
        
        if not seed_products:
            return []
        
        # Traverse graph from seed products
        search_results = []
        
        for seed_product_id in seed_products[:5]:  # Limit seeds to avoid explosion
            # Get related products through relationships
            related = self.graph_db.get_product_relationships(
                product_id=seed_product_id,
                max_distance=2,
                min_confidence=min_similarity
            )
            
            for rel in related:
                # Calculate graph-based similarity score
                graph_score = rel['confidence']
                
                result = SearchResult(
                    product_id=rel['related_product_id'],
                    sku=rel['related_sku'],
                    name=rel['related_name'],
                    description=None,
                    brand_name=None,
                    category_name=None,
                    price=rel.get('related_price'),
                    semantic_similarity=0.0,
                    text_similarity=0.0,
                    graph_similarity=graph_score,
                    combined_score=graph_score,
                    relationships=[{
                        'type': rel['relationship_type'],
                        'confidence': rel['confidence'],
                        'source': rel.get('source')
                    }],
                    match_reasons=[f"Graph relationship: {rel['relationship_type']}"],
                    rank=0,
                    search_time=datetime.utcnow()
                )
                
                search_results.append(result)
        
        # Remove duplicates and sort by score
        unique_results = {r.product_id: r for r in search_results}
        sorted_results = sorted(
            unique_results.values(),
            key=lambda x: x.combined_score,
            reverse=True
        )
        
        return sorted_results[:limit]
    
    # ===========================================
    # QUERY PROCESSING
    # ===========================================
    
    async def _process_query(self, query: str, filters: Dict[str, Any]) -> SearchContext:
        """Process and understand the natural language query"""
        
        # Clean and normalize query
        processed_query = self._normalize_query(query)
        
        # Detect intent
        intent = self._detect_intent(processed_query)
        
        # Extract entities
        entities = self._extract_entities(processed_query)
        
        # Extract keywords
        keywords = self._extract_keywords(processed_query)
        
        return SearchContext(
            original_query=query,
            processed_query=processed_query,
            intent=intent,
            entities=entities,
            keywords=keywords,
            filters=filters
        )
    
    def _normalize_query(self, query: str) -> str:
        """Normalize and clean the search query"""
        # Convert to lowercase
        query = query.lower().strip()
        
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query)
        
        # Expand common abbreviations
        abbreviations = {
            'mfg': 'manufacturer',
            'mfr': 'manufacturer',
            'w/': 'with',
            'wo/': 'without',
            'inc': 'including',
            'excl': 'excluding'
        }
        
        for abbr, expansion in abbreviations.items():
            query = re.sub(r'\b' + re.escape(abbr) + r'\b', expansion, query)
        
        return query
    
    def _detect_intent(self, query: str) -> str:
        """Detect the intent of the search query"""
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return intent
        
        # Default intent
        return 'product_search'
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities from the query"""
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                entities.append(f"{entity_type}:{match}")
        
        return entities
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from the query"""
        # Remove stop words and extract meaningful terms
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'what', 'where', 'when', 'how', 'i',
            'need', 'want', 'looking', 'find', 'search', 'get', 'buy'
        }
        
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    # ===========================================
    # UTILITY METHODS
    # ===========================================
    
    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get text embedding using available models"""
        
        # Try sentence transformer first (faster, local)
        if self.sentence_transformer:
            try:
                embedding = self.sentence_transformer.encode(text)
                return embedding.tolist()
            except Exception as e:
                logger.warning(f"Sentence transformer failed: {e}")
        
        # Fallback to OpenAI embeddings
        if self.openai_api_key:
            try:
                response = await openai.Embedding.acreate(
                    model="text-embedding-ada-002",
                    input=text
                )
                return response['data'][0]['embedding']
            except Exception as e:
                logger.warning(f"OpenAI embedding failed: {e}")
        
        return None
    
    def _build_chromadb_filters(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build ChromaDB where filters from search filters"""
        if not filters:
            return None
        
        where_clause = {}
        
        if 'brand_name' in filters:
            where_clause['brand_name'] = filters['brand_name']
        
        if 'category_name' in filters:
            where_clause['category_name'] = filters['category_name']
        
        if 'price_min' in filters or 'price_max' in filters:
            price_filter = {}
            if 'price_min' in filters:
                price_filter['$gte'] = filters['price_min']
            if 'price_max' in filters:
                price_filter['$lte'] = filters['price_max']
            where_clause['price'] = price_filter
        
        return where_clause if where_clause else None
    
    def _merge_search_results(
        self,
        result_sets: List[Tuple[List[SearchResult], float]]
    ) -> List[SearchResult]:
        """Merge multiple result sets with weighted scoring"""
        
        # Collect all unique products
        product_scores = {}
        
        for results, weight in result_sets:
            for result in results:
                product_id = result.product_id
                
                if product_id not in product_scores:
                    product_scores[product_id] = {
                        'result': result,
                        'scores': [],
                        'total_weight': 0.0
                    }
                
                # Add weighted score
                combined_score = (
                    result.semantic_similarity * 0.4 +
                    result.text_similarity * 0.35 +
                    result.graph_similarity * 0.25
                )
                
                product_scores[product_id]['scores'].append(combined_score * weight)
                product_scores[product_id]['total_weight'] += weight
        
        # Calculate final scores and create merged results
        merged_results = []
        
        for product_id, data in product_scores.items():
            if data['total_weight'] > 0:
                final_score = sum(data['scores']) / data['total_weight']
                
                result = data['result']
                result.combined_score = final_score
                
                merged_results.append(result)
        
        # Sort by combined score
        merged_results.sort(key=lambda x: x.combined_score, reverse=True)
        
        return merged_results
    
    async def _find_seed_products(self, context: SearchContext) -> List[int]:
        """Find seed products for graph traversal based on entities"""
        
        seed_products = []
        
        # Extract brand and category entities
        brands = [e.split(':')[1] for e in context.entities if e.startswith('brand:')]
        categories = [e.split(':')[1] for e in context.entities if e.startswith('category:')]
        
        query_parts = []
        params = {}
        
        if brands:
            query_parts.append("p.brand_name IN $brands")
            params['brands'] = brands
        
        if categories:
            query_parts.append("p.category_name CONTAINS $category_term")
            params['category_term'] = categories[0]  # Use first category
        
        if query_parts:
            query = f"""
            MATCH (p:Product)
            WHERE {' OR '.join(query_parts)}
            AND p.is_published = true
            RETURN p.product_id
            LIMIT 10
            """
            
            try:
                with self.neo4j_conn.session() as session:
                    results = session.run(query, params)
                    seed_products = [record['p.product_id'] for record in results]
            except Exception as e:
                logger.error(f"Failed to find seed products: {e}")
        
        return seed_products
    
    def _classify_project_type(self, description: str) -> Optional[str]:
        """Classify project type from description"""
        project_keywords = {
            'bathroom_renovation': ['bathroom', 'shower', 'toilet', 'sink', 'tile', 'bath'],
            'kitchen_renovation': ['kitchen', 'cabinet', 'countertop', 'sink', 'stove'],
            'deck_building': ['deck', 'patio', 'outdoor', 'wood', 'lumber', 'railing'],
            'electrical': ['electrical', 'wire', 'outlet', 'switch', 'circuit', 'voltage']
        }
        
        description_lower = description.lower()
        
        for project_type, keywords in project_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return project_type
        
        return None
    
    async def _enrich_with_relationships(
        self,
        results: List[SearchResult],
        context: SearchContext
    ) -> List[SearchResult]:
        """Enrich search results with relationship information"""
        
        for result in results:
            try:
                # Get relationships for this product
                relationships = self.graph_db.get_product_relationships(
                    product_id=result.product_id,
                    max_distance=1,
                    min_confidence=0.6
                )
                
                # Convert to result format
                result.relationships = [
                    {
                        'type': rel['relationship_type'],
                        'confidence': rel['confidence'],
                        'related_product': {
                            'id': rel['related_product_id'],
                            'name': rel['related_name'],
                            'sku': rel['related_sku']
                        }
                    }
                    for rel in relationships[:5]  # Limit to top 5 relationships
                ]
                
            except Exception as e:
                logger.warning(f"Failed to enrich product {result.product_id} with relationships: {e}")
        
        return results
    
    # ===========================================
    # INDEXING AND MAINTENANCE
    # ===========================================
    
    async def index_products(self, batch_size: int = 100) -> int:
        """Index products for semantic search"""
        logger.info("Starting product indexing for semantic search...")
        
        if 'products' not in self.collections:
            logger.error("Products collection not available")
            return 0
        
        # Get all products from Neo4j
        query = """
        MATCH (p:Product)
        WHERE p.is_published = true
        RETURN p.product_id as product_id,
               p.sku as sku,
               p.name as name,
               p.description as description,
               p.long_description as long_description,
               p.brand_name as brand_name,
               p.category_name as category_name,
               p.price as price,
               p.keywords as keywords,
               p.features as features
        """
        
        try:
            with self.neo4j_conn.session() as session:
                results = session.run(query)
                products = [dict(record) for record in results]
            
            logger.info(f"Indexing {len(products)} products...")
            
            # Process in batches
            indexed_count = 0
            
            for i in range(0, len(products), batch_size):
                batch = products[i:i + batch_size]
                
                # Prepare data for ChromaDB
                ids = []
                documents = []
                embeddings = []
                metadatas = []
                
                for product in batch:
                    # Create searchable text
                    text_parts = [
                        product.get('name', ''),
                        product.get('description', ''),
                        product.get('long_description', ''),
                        product.get('brand_name', ''),
                        product.get('category_name', ''),
                        ' '.join(product.get('keywords', []) or []),
                        ' '.join(product.get('features', []) or [])
                    ]
                    
                    document_text = ' '.join(filter(None, text_parts))
                    
                    if not document_text.strip():
                        continue
                    
                    # Get embedding
                    embedding = await self._get_embedding(document_text)
                    if not embedding:
                        continue
                    
                    ids.append(str(product['product_id']))
                    documents.append(document_text)
                    embeddings.append(embedding)
                    metadatas.append({
                        'sku': product.get('sku', ''),
                        'name': product.get('name', ''),
                        'description': product.get('description'),
                        'brand_name': product.get('brand_name'),
                        'category_name': product.get('category_name'),
                        'price': product.get('price')
                    })
                
                # Add to ChromaDB
                if ids:
                    self.collections['products'].add(
                        ids=ids,
                        documents=documents,
                        embeddings=embeddings,
                        metadatas=metadatas
                    )
                    
                    indexed_count += len(ids)
                    logger.info(f"Indexed batch: {indexed_count}/{len(products)} products")
            
            logger.info(f"Product indexing completed: {indexed_count} products indexed")
            return indexed_count
            
        except Exception as e:
            logger.error(f"Product indexing failed: {e}")
            return 0


# Export main classes
__all__ = ["SemanticSearchEngine", "SearchResult", "SearchContext"]