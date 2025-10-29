#!/usr/bin/env python3
"""
SDK-compliant search optimization workflow (standalone version for testing)
Converts TypeScript search implementation to proper Kailash SDK patterns
"""

import json
import time
import sqlite3
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Mock Kailash SDK components for testing
class WorkflowBuilder:
    def __init__(self):
        self.nodes = []
        self.connections = []
    
    def add_node(self, node_type: str, node_id: str, config: Dict[str, Any]):
        self.nodes.append({
            'type': node_type,
            'id': node_id, 
            'config': config
        })
    
    def add_connection(self, source_node: str, output_key: str, target_node: str, input_key: str):
        self.connections.append({
            'source': source_node,
            'output': output_key,
            'target': target_node,
            'input': input_key
        })
    
    def build(self):
        return MockWorkflow(self.nodes, self.connections)

class MockRuntime:
    async def execute(self, workflow, parameters=None):
        # Mock execution - would actually run workflow
        return {
            'result_ranker': {
                'final_results': [
                    {
                        'id': 1,
                        'name': 'Test Product',
                        'match_score': 0.9
                    }
                ],
                'search_method': 'fts5',
                'execution_time_ms': 25
            },
            'cache_lookup': {
                'cache_hit': False,
                'cache_status': 'miss'
            },
            'query_processor': {
                'complexity_score': 2
            },
            'cache_storage': {
                'result_count': 1
            }
        }, 'mock_run_123'

class MockWorkflow:
    def __init__(self, nodes, connections):
        self.nodes = nodes
        self.connections = connections

@dataclass
class SearchOptions:
    query: str = ""
    category: str = ""
    limit: int = 20
    include_specs: bool = False
    use_cache: bool = True
    enable_fts: bool = True

@dataclass
class SearchResult:
    id: int
    sku: str
    name: str
    description: str
    enriched_description: str
    technical_specs: str
    price: Optional[float]
    currency: str
    brand: str
    category: str
    availability: str
    rank: float
    snippet: str
    match_score: float

class SearchOptimizationWorkflow:
    """SDK-compliant search workflow using proper Kailash patterns"""
    
    def __init__(self, db_path: str = None):
        # Essential pattern: proper runtime initialization
        self.runtime = MockRuntime()
        self.db_path = db_path or os.path.join(os.getcwd(), 'products.db')
        self._search_cache = {}  # Simple in-memory cache
    
    def create_search_optimization_workflow(self, options: SearchOptions) -> WorkflowBuilder:
        """Create SDK-compliant search optimization workflow"""
        workflow = WorkflowBuilder()
        
        # Node 1: Query preprocessing and validation
        workflow.add_node("PythonCodeNode", "query_processor", {
            "code": """
import re
import json
from typing import Dict, Any

def process_search_query(query: str, category: str, limit: int, include_specs: bool, use_cache: bool, enable_fts: bool) -> Dict[str, Any]:
    '''Process and validate search query parameters'''
    
    # Clean and validate inputs
    clean_query = query.strip() if query else ''
    clean_category = category.strip() if category else ''
    validated_limit = min(max(limit, 1), 100)  # Clamp between 1-100
    
    # Calculate query complexity for optimization decisions
    query_words = len(clean_query.split()) if clean_query else 0
    has_special_chars = bool(re.search(r'[()&|*"~]', clean_query))
    complexity_score = query_words + (2 if has_special_chars else 0)
    
    # Generate cache key for consistent caching
    cache_components = [
        clean_query.lower(),
        clean_category.lower(), 
        str(validated_limit),
        str(include_specs),
        str(enable_fts)
    ]
    cache_key = ':'.join(cache_components)
    
    # Determine search strategy based on inputs
    search_strategy = 'none'
    if clean_query or clean_category:
        if enable_fts and query_words > 0:
            search_strategy = 'fts5_primary'
        else:
            search_strategy = 'like_fallback'
    
    return {
        'clean_query': clean_query,
        'clean_category': clean_category,
        'validated_limit': validated_limit,
        'include_specs': include_specs,
        'use_cache': use_cache,
        'enable_fts': enable_fts,
        'cache_key': cache_key,
        'complexity_score': complexity_score,
        'search_strategy': search_strategy,
        'has_query': len(clean_query) > 0,
        'has_category': len(clean_category) > 0
    }

result = process_search_query(query, category, limit, include_specs, use_cache, enable_fts)
"""
        })
        
        # Node 2: Cache lookup for performance optimization  
        workflow.add_node("PythonCodeNode", "cache_lookup", {
            "code": """
import json
import time
from typing import Optional, Dict, Any

# Cache configuration
CACHE_TTL_SECONDS = 300  # 5 minutes
MAX_CACHE_ENTRIES = 1000

def lookup_search_cache(processed_query: Dict[str, Any], cache_data: Dict[str, Any]) -> Dict[str, Any]:
    '''Check cache for existing search results'''
    
    if not processed_query.get('use_cache', True):
        return {
            'cache_hit': False,
            'cached_results': None,
            'cache_status': 'disabled'
        }
    
    cache_key = processed_query['cache_key']
    current_time = time.time()
    
    # Check if entry exists and is valid
    cache_entry = cache_data.get(cache_key)
    if cache_entry:
        entry_age = current_time - cache_entry['timestamp']
        
        if entry_age <= CACHE_TTL_SECONDS:
            return {
                'cache_hit': True,
                'cached_results': cache_entry['results'],
                'cache_status': 'hit',
                'cache_age_seconds': entry_age,
                'result_count': len(cache_entry['results'])
            }
        else:
            # Entry expired, will be cleaned up later
            return {
                'cache_hit': False,
                'cached_results': None,
                'cache_status': 'expired',
                'cache_age_seconds': entry_age
            }
    
    return {
        'cache_hit': False,
        'cached_results': None,
        'cache_status': 'miss'
    }

result = lookup_search_cache(processed_query, search_cache)
"""
        })
        
        # Node 3: Result ranking and scoring
        workflow.add_node("PythonCodeNode", "result_ranker", {
            "code": """
import math
from typing import List, Dict, Any

def calculate_bm25_score(query: str, text_fields: List[str]) -> float:
    '''Calculate BM25-inspired relevance score'''
    
    if not query or not text_fields:
        return 0.0
    
    query_terms = [term.lower() for term in query.split() if len(term) > 1]
    if not query_terms:
        return 0.0
    
    # Combine all text fields
    full_text = ' '.join(text_fields).lower()
    text_terms = full_text.split()
    
    if not text_terms:
        return 0.0
    
    # Simple scoring (would be more complex BM25 in production)
    score = 0.0
    for term in query_terms:
        tf = full_text.count(term)
        if tf > 0:
            score += math.log(1 + tf)
    
    return min(score, 10.0)

def rank_and_score_results(processed_query: Dict[str, Any]) -> Dict[str, Any]:
    '''Mock result ranking and scoring'''
    
    # Mock results for demonstration
    mock_results = [
        {
            'id': 1,
            'name': 'Laptop Computer',
            'description': 'High performance laptop',
            'price': 999.99,
            'match_score': 0.9
        },
        {
            'id': 2, 
            'name': 'Desktop Computer',
            'description': 'Powerful desktop system',
            'price': 799.99,
            'match_score': 0.7
        }
    ]
    
    return {
        'final_results': mock_results,
        'result_count': len(mock_results),
        'search_method': 'fts5',
        'execution_time_ms': 25,
        'ranking_applied': True,
        'query_complexity': processed_query.get('complexity_score', 0)
    }

result = rank_and_score_results(processed_query)
"""
        })
        
        # Node 4: Cache storage
        workflow.add_node("PythonCodeNode", "cache_storage", {
            "code": """
import time
from typing import Dict, Any, List

def store_results_in_cache(ranking_result: Dict[str, Any]) -> Dict[str, Any]:
    '''Mock cache storage'''
    
    return {
        'cached': True,
        'cache_size': 10,
        'result_count': ranking_result.get('result_count', 0)
    }

result = store_results_in_cache(ranking_result)
"""
        })
        
        # Connect workflow nodes using 4-parameter connections (ESSENTIAL PATTERN)
        workflow.add_connection("query_processor", "result", "cache_lookup", "processed_query")
        workflow.add_connection("cache_lookup", "result", "result_ranker", "cache_lookup_result")
        workflow.add_connection("query_processor", "result", "result_ranker", "processed_query")
        workflow.add_connection("result_ranker", "result", "cache_storage", "ranking_result")
        
        return workflow
    
    async def execute_search(self, options: SearchOptions) -> Dict[str, Any]:
        """Execute search optimization workflow with essential SDK pattern"""
        
        start_time = time.time()
        
        try:
            # Create workflow with proper SDK patterns
            workflow = self.create_search_optimization_workflow(options)
            
            # ESSENTIAL PATTERN: runtime.execute(workflow.build()) 
            results, run_id = await self.runtime.execute(workflow.build(), {
                "query_processor": {
                    "query": options.query,
                    "category": options.category,
                    "limit": options.limit,
                    "include_specs": options.include_specs,
                    "use_cache": options.use_cache,
                    "enable_fts": options.enable_fts
                }
            })
            
            total_execution_time = (time.time() - start_time) * 1000
            
            # Extract results from workflow execution
            ranking_result = results.get('result_ranker', {})
            cache_storage_result = results.get('cache_storage', {})
            query_processing = results.get('query_processor', {})
            cache_lookup = results.get('cache_lookup', {})
            
            final_results = ranking_result.get('final_results', [])
            search_method = ranking_result.get('search_method', 'unknown')
            
            return {
                'results': final_results,
                'performance_metrics': {
                    'fts5_enabled': search_method == 'fts5',
                    'cache_hit': cache_lookup.get('cache_hit', False),
                    'execution_time_ms': total_execution_time,
                    'total_results': len(final_results),
                    'query_complexity': query_processing.get('complexity_score', 0),
                    'search_method': search_method
                },
                'workflow_metadata': {
                    'run_id': run_id,
                    'nodes_executed': list(results.keys()),
                    'cache_status': cache_lookup.get('cache_status', 'unknown'),
                    'ranking_applied': ranking_result.get('ranking_applied', False)
                }
            }
            
        except Exception as e:
            return {
                'results': [],
                'performance_metrics': {
                    'fts5_enabled': False,
                    'cache_hit': False,
                    'execution_time_ms': (time.time() - start_time) * 1000,
                    'total_results': 0,
                    'query_complexity': 0,
                    'search_method': 'error'
                },
                'workflow_metadata': {
                    'run_id': '',
                    'nodes_executed': [],
                    'errors': [f'Search workflow failed: {str(e)}']
                }
            }

# Export singleton instance for compatibility
search_workflow = SearchOptimizationWorkflow()

async def execute_optimized_search(options: SearchOptions) -> Dict[str, Any]:
    """SDK-compliant search execution entry point"""
    return await search_workflow.execute_search(options)

async def execute_autocomplete_search(query: str, limit: int = 10) -> List[str]:
    """SDK-compliant autocomplete entry point"""
    # Mock autocomplete results
    return [f"{query}_suggestion_{i}" for i in range(min(limit, 3))]

if __name__ == "__main__":
    # Demo usage
    import asyncio
    
    async def demo():
        # Test search workflow
        search_options = SearchOptions(
            query="laptop computer",
            category="electronics", 
            limit=10,
            include_specs=True,
            use_cache=True,
            enable_fts=True
        )
        
        search_result = await execute_optimized_search(search_options)
        print("Search Result:", json.dumps(search_result, indent=2))
        
        # Test autocomplete
        autocomplete_results = await execute_autocomplete_search("lapt", 5)
        print("Autocomplete Results:", autocomplete_results)
    
    asyncio.run(demo())