"""
DataFlow Integration for Knowledge Graph

This module integrates the knowledge graph system with the existing
Kailash DataFlow models and provides workflow nodes for graph operations.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json
import asyncio

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash.nodes.base import BaseNode

from .database import Neo4jConnection, GraphDatabase
from .models import ProductNode, SemanticRelationship, RelationshipType
from .search import SemanticSearchEngine, SearchResult
from .inference import RelationshipInferenceEngine
from .integration import PostgreSQLIntegration

logger = logging.getLogger(__name__)


class KnowledgeGraphDataFlowNodes:
    """
    DataFlow nodes for knowledge graph operations.
    
    Provides workflow nodes that can be used in Kailash DataFlow workflows
    to interact with the product knowledge graph.
    """
    
    def __init__(self, neo4j_connection: Neo4jConnection = None):
        """Initialize with Neo4j connection"""
        self.neo4j_conn = neo4j_connection or Neo4jConnection()
        self.graph_db = GraphDatabase(self.neo4j_conn)
        self.search_engine = SemanticSearchEngine(self.neo4j_conn)
        self.inference_engine = RelationshipInferenceEngine(self.neo4j_conn)
        self.postgres_integration = PostgreSQLIntegration(neo4j_connection=self.neo4j_conn)
    
    # ===========================================
    # SEARCH NODES
    # ===========================================
    
    def semantic_search_node(
        self,
        query: str,
        limit: int = 20,
        min_similarity: float = 0.6,
        search_strategy: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        DataFlow node for semantic product search.
        
        Args:
            query: Search query
            limit: Maximum results
            min_similarity: Minimum similarity threshold
            search_strategy: Search strategy (semantic, text, graph, hybrid)
            
        Returns:
            Dictionary with search results and metadata
        """
        try:
            # Run search synchronously (DataFlow nodes should be sync)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                self.search_engine.search(
                    query=query,
                    limit=limit,
                    min_similarity=min_similarity,
                    search_strategy=search_strategy
                )
            )
            
            loop.close()
            
            # Convert SearchResult objects to dictionaries
            results_data = [
                {
                    'product_id': r.product_id,
                    'sku': r.sku,
                    'name': r.name,
                    'description': r.description,
                    'brand_name': r.brand_name,
                    'category_name': r.category_name,
                    'price': r.price,
                    'semantic_similarity': r.semantic_similarity,
                    'text_similarity': r.text_similarity,
                    'graph_similarity': r.graph_similarity,
                    'combined_score': r.combined_score,
                    'relationships': r.relationships,
                    'match_reasons': r.match_reasons,
                    'rank': r.rank
                }
                for r in results
            ]
            
            return {
                'search_query': query,
                'result_count': len(results_data),
                'results': results_data,
                'search_strategy': search_strategy,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Semantic search node failed: {e}")
            return {
                'error': str(e),
                'search_query': query,
                'result_count': 0,
                'results': [],
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def compatibility_search_node(
        self,
        product_id: int,
        compatibility_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        DataFlow node for finding compatible products.
        
        Args:
            product_id: Product to find compatibility for
            compatibility_types: Types of compatibility to search for
            limit: Maximum results
            
        Returns:
            Dictionary with compatible products
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                self.search_engine.find_compatible_products(
                    product_id=product_id,
                    compatibility_types=compatibility_types,
                    limit=limit
                )
            )
            
            loop.close()
            
            # Convert to dictionary format
            compatible_products = [
                {
                    'product_id': r.product_id,
                    'sku': r.sku,
                    'name': r.name,
                    'brand_name': r.brand_name,
                    'price': r.price,
                    'compatibility_score': r.graph_similarity,
                    'compatibility_details': r.relationships
                }
                for r in results
            ]
            
            return {
                'source_product_id': product_id,
                'compatible_count': len(compatible_products),
                'compatible_products': compatible_products,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Compatibility search node failed: {e}")
            return {
                'error': str(e),
                'source_product_id': product_id,
                'compatible_count': 0,
                'compatible_products': [],
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def project_recommendation_node(
        self,
        project_description: str,
        budget_range: Optional[str] = None,
        skill_level: Optional[str] = None,
        limit: int = 15
    ) -> Dict[str, Any]:
        """
        DataFlow node for DIY project recommendations.
        
        Args:
            project_description: Description of the project
            budget_range: Budget constraint
            skill_level: Required skill level
            limit: Maximum recommendations
            
        Returns:
            Dictionary with project recommendations
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                self.search_engine.recommend_for_project(
                    project_description=project_description,
                    budget_range=budget_range,
                    skill_level=skill_level,
                    limit=limit
                )
            )
            
            loop.close()
            
            # Group recommendations by category/type
            recommendations_by_category = {}
            total_estimated_cost = 0.0
            
            for result in results:
                category = result.category_name or 'Other'
                
                if category not in recommendations_by_category:
                    recommendations_by_category[category] = []
                
                recommendation = {
                    'product_id': result.product_id,
                    'sku': result.sku,
                    'name': result.name,
                    'brand_name': result.brand_name,
                    'price': result.price,
                    'recommendation_score': result.combined_score,
                    'match_reasons': result.match_reasons
                }
                
                recommendations_by_category[category].append(recommendation)
                
                if result.price:
                    total_estimated_cost += result.price
            
            return {
                'project_description': project_description,
                'budget_range': budget_range,
                'skill_level': skill_level,
                'recommendation_count': len(results),
                'estimated_total_cost': total_estimated_cost,
                'recommendations_by_category': recommendations_by_category,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Project recommendation node failed: {e}")
            return {
                'error': str(e),
                'project_description': project_description,
                'recommendation_count': 0,
                'recommendations_by_category': {},
                'timestamp': datetime.utcnow().isoformat()
            }
    
    # ===========================================
    # RELATIONSHIP NODES
    # ===========================================
    
    def get_product_relationships_node(
        self,
        product_id: int,
        relationship_types: Optional[List[str]] = None,
        max_distance: int = 1,
        min_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """
        DataFlow node for getting product relationships.
        
        Args:
            product_id: Product ID
            relationship_types: Filter by relationship types
            max_distance: Maximum traversal distance
            min_confidence: Minimum confidence threshold
            
        Returns:
            Dictionary with product relationships
        """
        try:
            # Convert string relationship types to enum
            rel_types = None
            if relationship_types:
                rel_types = [RelationshipType(rt) for rt in relationship_types]
            
            relationships = self.graph_db.get_product_relationships(
                product_id=product_id,
                relationship_types=rel_types,
                max_distance=max_distance,
                min_confidence=min_confidence
            )
            
            # Group relationships by type
            relationships_by_type = {}
            for rel in relationships:
                rel_type = rel['relationship_type']
                if rel_type not in relationships_by_type:
                    relationships_by_type[rel_type] = []
                
                relationships_by_type[rel_type].append({
                    'related_product_id': rel['related_product_id'],
                    'related_sku': rel['related_sku'],
                    'related_name': rel['related_name'],
                    'confidence': rel['confidence'],
                    'compatibility_type': rel.get('compatibility_type'),
                    'use_case': rel.get('use_case'),
                    'notes': rel.get('notes')
                })
            
            return {
                'product_id': product_id,
                'total_relationships': len(relationships),
                'relationships_by_type': relationships_by_type,
                'max_distance': max_distance,
                'min_confidence': min_confidence,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Get product relationships node failed: {e}")
            return {
                'error': str(e),
                'product_id': product_id,
                'total_relationships': 0,
                'relationships_by_type': {},
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def create_relationship_node(
        self,
        from_product_id: int,
        to_product_id: int,
        relationship_type: str,
        confidence: float,
        source: str = "manual",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        DataFlow node for creating product relationships.
        
        Args:
            from_product_id: Source product ID
            to_product_id: Target product ID
            relationship_type: Type of relationship
            confidence: Confidence score (0.0-1.0)
            source: Source of relationship
            notes: Optional notes
            
        Returns:
            Dictionary with creation result
        """
        try:
            from .models import ConfidenceSource
            
            # Create relationship object
            relationship = SemanticRelationship(
                from_product_id=from_product_id,
                to_product_id=to_product_id,
                relationship_type=RelationshipType(relationship_type),
                confidence=confidence,
                source=ConfidenceSource(source),
                notes=notes
            )
            
            # Create in graph database
            success = self.graph_db.create_relationship(relationship)
            
            return {
                'success': success,
                'from_product_id': from_product_id,
                'to_product_id': to_product_id,
                'relationship_type': relationship_type,
                'confidence': confidence,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Create relationship node failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'from_product_id': from_product_id,
                'to_product_id': to_product_id,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    # ===========================================
    # DATA MANAGEMENT NODES
    # ===========================================
    
    def sync_from_postgresql_node(
        self,
        entity_types: Optional[List[str]] = None,
        force_refresh: bool = False,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        DataFlow node for syncing data from PostgreSQL.
        
        Args:
            entity_types: Types of entities to sync
            force_refresh: Force full refresh
            limit: Limit number of entities
            
        Returns:
            Dictionary with sync results
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if entity_types:
                results = {}
                if "categories" in entity_types:
                    results['categories'] = loop.run_until_complete(
                        self.postgres_integration.migrate_categories(force_refresh)
                    )
                if "brands" in entity_types:
                    results['brands'] = loop.run_until_complete(
                        self.postgres_integration.migrate_brands(force_refresh)
                    )
                if "products" in entity_types:
                    results['products'] = loop.run_until_complete(
                        self.postgres_integration.migrate_products(force_refresh, limit)
                    )
            else:
                results = loop.run_until_complete(
                    self.postgres_integration.migrate_all(force_refresh)
                )
            
            loop.close()
            
            total_synced = sum(results.values())
            
            return {
                'success': True,
                'total_synced': total_synced,
                'results_by_type': results,
                'force_refresh': force_refresh,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"PostgreSQL sync node failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_synced': 0,
                'results_by_type': {},
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def run_relationship_inference_node(
        self,
        batch_size: int = 500,
        max_products: Optional[int] = None,
        min_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """
        DataFlow node for running relationship inference.
        
        Args:
            batch_size: Batch size for processing
            max_products: Maximum products to process
            min_confidence: Minimum confidence threshold
            
        Returns:
            Dictionary with inference results
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                self.inference_engine.infer_all_relationships(
                    batch_size=batch_size,
                    max_products=max_products,
                    min_confidence=min_confidence
                )
            )
            
            loop.close()
            
            total_relationships = sum(results.values())
            
            return {
                'success': True,
                'total_relationships_created': total_relationships,
                'relationships_by_type': results,
                'batch_size': batch_size,
                'max_products': max_products,
                'min_confidence': min_confidence,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Relationship inference node failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_relationships_created': 0,
                'relationships_by_type': {},
                'timestamp': datetime.utcnow().isoformat()
            }


# ===========================================
# DATAFLOW WORKFLOW EXAMPLES
# ===========================================

class KnowledgeGraphWorkflows:
    """Example workflows using knowledge graph DataFlow nodes"""
    
    def __init__(self):
        self.kg_nodes = KnowledgeGraphDataFlowNodes()
        self.runtime = LocalRuntime()
    
    def build_product_discovery_workflow(self, search_query: str) -> WorkflowBuilder:
        """
        Build a workflow for comprehensive product discovery.
        
        This workflow:
        1. Performs semantic search
        2. Finds compatible products for top results
        3. Gets project recommendations if applicable
        4. Enriches with relationship data
        """
        workflow = WorkflowBuilder()
        
        # Step 1: Semantic search
        workflow.add_node(
            "SemanticSearchNode",
            "search",
            {
                "function": self.kg_nodes.semantic_search_node,
                "query": search_query,
                "limit": 10,
                "search_strategy": "hybrid"
            }
        )
        
        # Step 2: Extract top product for compatibility search
        workflow.add_node(
            "PythonCodeNode",
            "extract_top_product",
            {
                "code": """
if search_results['result_count'] > 0:
    top_product_id = search_results['results'][0]['product_id']
    output = {'top_product_id': top_product_id}
else:
    output = {'top_product_id': None}
                """,
                "inputs": {"search_results": "search"}
            }
        )
        
        # Step 3: Find compatible products (conditional)
        workflow.add_node(
            "SwitchNode",
            "compatibility_switch",
            {
                "condition": "extract_top_product.top_product_id is not None",
                "true_path": "find_compatibility",
                "false_path": "skip_compatibility"
            }
        )
        
        workflow.add_node(
            "PythonCodeNode",
            "find_compatibility",
            {
                "function": self.kg_nodes.compatibility_search_node,
                "product_id": "extract_top_product.top_product_id",
                "limit": 5
            }
        )
        
        workflow.add_node(
            "PythonCodeNode",
            "skip_compatibility",
            {
                "code": "output = {'compatible_products': [], 'compatible_count': 0}"
            }
        )
        
        # Step 4: Check if query suggests a project
        workflow.add_node(
            "PythonCodeNode",
            "check_project_intent",
            {
                "code": """
project_keywords = ['renovation', 'build', 'project', 'diy', 'install']
query_lower = search_query.lower()
is_project = any(keyword in query_lower for keyword in project_keywords)
output = {'is_project_query': is_project}
                """,
                "inputs": {"search_query": search_query}
            }
        )
        
        # Step 5: Project recommendations (conditional)
        workflow.add_node(
            "SwitchNode",
            "project_switch",
            {
                "condition": "check_project_intent.is_project_query",
                "true_path": "get_project_recommendations",
                "false_path": "skip_project_recommendations"
            }
        )
        
        workflow.add_node(
            "PythonCodeNode",
            "get_project_recommendations",
            {
                "function": self.kg_nodes.project_recommendation_node,
                "project_description": search_query,
                "limit": 10
            }
        )
        
        workflow.add_node(
            "PythonCodeNode",
            "skip_project_recommendations",
            {
                "code": "output = {'recommendations_by_category': {}, 'recommendation_count': 0}"
            }
        )
        
        # Step 6: Combine results
        workflow.add_node(
            "PythonCodeNode",
            "combine_results",
            {
                "code": """
output = {
    'search_query': search_query,
    'search_results': search_results,
    'compatible_products': compatibility_results.get('compatible_products', []),
    'project_recommendations': project_results.get('recommendations_by_category', {}),
    'analysis': {
        'total_products_found': search_results['result_count'],
        'compatible_products_found': compatibility_results.get('compatible_count', 0),
        'project_recommendations_found': project_results.get('recommendation_count', 0),
        'is_project_related': check_project_intent['is_project_query']
    },
    'timestamp': search_results.get('timestamp')
}
                """,
                "inputs": {
                    "search_query": search_query,
                    "search_results": "search",
                    "compatibility_results": "find_compatibility",
                    "project_results": "get_project_recommendations", 
                    "check_project_intent": "check_project_intent"
                }
            }
        )
        
        return workflow
    
    def build_data_sync_workflow(self, force_refresh: bool = False) -> WorkflowBuilder:
        """
        Build a workflow for syncing data from PostgreSQL to Neo4j.
        
        This workflow:
        1. Syncs categories, brands, and products
        2. Runs relationship inference
        3. Indexes products for search
        4. Generates sync report
        """
        workflow = WorkflowBuilder()
        
        # Step 1: Sync from PostgreSQL
        workflow.add_node(
            "PythonCodeNode",
            "sync_data",
            {
                "function": self.kg_nodes.sync_from_postgresql_node,
                "entity_types": ["categories", "brands", "products"],
                "force_refresh": force_refresh
            }
        )
        
        # Step 2: Run relationship inference (conditional on successful sync)
        workflow.add_node(
            "SwitchNode",
            "sync_success_check",
            {
                "condition": "sync_data.success and sync_data.total_synced > 0",
                "true_path": "run_inference",
                "false_path": "skip_inference"
            }
        )
        
        workflow.add_node(
            "PythonCodeNode",
            "run_inference",
            {
                "function": self.kg_nodes.run_relationship_inference_node,
                "batch_size": 200,
                "min_confidence": 0.6
            }
        )
        
        workflow.add_node(
            "PythonCodeNode",
            "skip_inference",
            {
                "code": """
output = {
    'success': False,
    'reason': 'Skipped due to sync failure or no data synced',
    'total_relationships_created': 0
}
                """
            }
        )
        
        # Step 3: Generate final report
        workflow.add_node(
            "PythonCodeNode",
            "generate_report",
            {
                "code": """
output = {
    'sync_workflow_completed': True,
    'force_refresh': force_refresh,
    'sync_results': sync_data,
    'inference_results': inference_results,
    'summary': {
        'data_synced': sync_data.get('success', False),
        'total_entities_synced': sync_data.get('total_synced', 0),
        'relationships_inferred': inference_results.get('success', False),
        'total_relationships_created': inference_results.get('total_relationships_created', 0)
    },
    'timestamp': sync_data.get('timestamp')
}
                """,
                "inputs": {
                    "force_refresh": force_refresh,
                    "sync_data": "sync_data",
                    "inference_results": "run_inference"
                }
            }
        )
        
        return workflow
    
    def execute_product_discovery(self, search_query: str) -> Dict[str, Any]:
        """Execute the product discovery workflow"""
        workflow = self.build_product_discovery_workflow(search_query)
        results, run_id = self.runtime.execute(workflow.build())
        return results.get("combine_results", {})
    
    def execute_data_sync(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Execute the data sync workflow"""
        workflow = self.build_data_sync_workflow(force_refresh)
        results, run_id = self.runtime.execute(workflow.build())
        return results.get("generate_report", {})


# Export main classes
__all__ = [
    "KnowledgeGraphDataFlowNodes",
    "KnowledgeGraphWorkflows"
]