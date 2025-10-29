#!/usr/bin/env python3
"""
SDK-compliant search optimization workflow (FIXED VERSION)
Converts TypeScript search implementation to proper Kailash SDK patterns
"""

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
import json
import time
import sqlite3
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

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
        self.runtime = LocalRuntime()
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
        
        # Node 3: FTS5 search execution (primary method)
        workflow.add_node("PythonCodeNode", "fts5_search", {
            "code": """
import sqlite3
import json
import time
import os
from typing import List, Dict, Any

def execute_fts5_search(processed_query: Dict[str, Any], cache_lookup_result: Dict[str, Any], db_path: str) -> Dict[str, Any]:
    '''Execute high-performance FTS5 search'''
    
    # Skip if cache hit or FTS5 not requested
    if cache_lookup_result.get('cache_hit', False):
        return {
            'fts5_executed': False,
            'results': cache_lookup_result['cached_results'],
            'skip_reason': 'cache_hit'
        }
    
    if processed_query['search_strategy'] != 'fts5_primary':
        return {
            'fts5_executed': False,
            'results': [],
            'skip_reason': 'strategy_not_fts5'
        }
    
    start_time = time.time()
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Verify FTS5 table exists
        fts_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_fts'").fetchone()
        
        if not fts_check:
            conn.close()
            return {
                'fts5_executed': False,
                'results': [],
                'error': 'FTS5 table products_fts not found',
                'fallback_required': True
            }
        
        # Build FTS5 query
        clean_query = processed_query['clean_query']
        clean_category = processed_query['clean_category']
        limit = processed_query['validated_limit']
        include_specs = processed_query['include_specs']
        
        # Base SQL with FTS5 integration
        select_fields = [
            'p.id', 'p.sku', 'p.name', 'p.description',
            'p.enriched_description', 'p.currency', 'p.availability',
            'pp.list_price as price',
            'b.name as brand', 'c.name as category',
            'fts.rank'
        ]
        
        if include_specs:
            select_fields.append('p.technical_specs')
        
        # Add FTS5 snippet for highlighting
        select_fields.append("snippet(products_fts, 0, '<mark>', '</mark>', '...', 64) as snippet")
        
        sql = f"SELECT {', '.join(select_fields)} FROM products_fts fts JOIN products p ON p.id = fts.rowid LEFT JOIN product_pricing pp ON p.id = pp.product_id LEFT JOIN brands b ON p.brand_id = b.id LEFT JOIN categories c ON p.category_id = c.id WHERE p.is_published = 1"
        
        params = []
        
        # Add FTS5 query condition
        if clean_query:
            # Simple term escaping for FTS5
            fts_terms = []
            for term in clean_query.split():
                if term and len(term) > 1:
                    escaped_term = f'"{term}"'
                    fts_terms.append(escaped_term)
            
            if fts_terms:
                fts_query = ' '.join(fts_terms)
                sql += " AND products_fts MATCH ?"
                params.append(fts_query)
        
        # Add category filter
        if clean_category:
            sql += " AND LOWER(c.name) LIKE LOWER(?)"
            params.append(f"%{clean_category}%")
        
        # Order by FTS5 rank and limit results
        sql += " ORDER BY fts.rank LIMIT ?"
        params.append(limit)
        
        # Execute search
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        
        # Convert results to dictionaries
        results = []
        for i, row in enumerate(rows):
            result_dict = {
                'id': row['id'],
                'sku': row['sku'],
                'name': row['name'],
                'description': row['description'],
                'enriched_description': row['enriched_description'] or '',
                'technical_specs': row.get('technical_specs', '') if include_specs else '',
                'price': row['price'],
                'currency': row['currency'] or 'USD',
                'brand': row['brand'] or '',
                'category': row['category'] or '',
                'availability': row['availability'] or '',
                'rank': row['rank'] if row['rank'] else i,
                'snippet': row['snippet'] or '',
                'match_score': 0  # Will be calculated in ranking node
            }
            results.append(result_dict)
        
        conn.close()
        execution_time_ms = (time.time() - start_time) * 1000
        
        return {
            'fts5_executed': True,
            'results': results,
            'result_count': len(results),
            'execution_time_ms': execution_time_ms
        }
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        
        return {
            'fts5_executed': False,
            'results': [],
            'error': f'FTS5 search failed: {str(e)}',
            'execution_time_ms': (time.time() - start_time) * 1000,
            'fallback_required': True
        }

result = execute_fts5_search(processed_query, cache_lookup_result, db_path)
"""
        })
        
        # Connect workflow nodes using 4-parameter connections (ESSENTIAL PATTERN)
        workflow.add_connection("query_processor", "result", "cache_lookup", "processed_query")
        workflow.add_connection("cache_lookup", "result", "fts5_search", "cache_lookup_result")
        workflow.add_connection("query_processor", "result", "fts5_search", "processed_query")
        
        return workflow
    
    async def execute_search(self, options: SearchOptions) -> Dict[str, Any]:
        """Execute search optimization workflow with essential SDK pattern"""
        
        start_time = time.time()
        
        try:
            # Create workflow with proper SDK patterns
            workflow = self.create_search_optimization_workflow(options)
            
            # ESSENTIAL PATTERN: runtime.execute(workflow.build()) 
            results, run_id = self.runtime.execute(workflow.build(), {
                "query_processor": {
                    "query": options.query,
                    "category": options.category,
                    "limit": options.limit,
                    "include_specs": options.include_specs,
                    "use_cache": options.use_cache,
                    "enable_fts": options.enable_fts
                },
                "cache_lookup": {
                    "search_cache": self._search_cache
                },
                "fts5_search": {
                    "db_path": self.db_path
                }
            })
            
            total_execution_time = (time.time() - start_time) * 1000
            
            # Extract results from workflow execution
            fts5_result = results.get('fts5_search', {})
            query_processing = results.get('query_processor', {})
            cache_lookup = results.get('cache_lookup', {})
            
            final_results = fts5_result.get('results', [])
            
            return {
                'results': final_results,
                'performance_metrics': {
                    'fts5_enabled': fts5_result.get('fts5_executed', False),
                    'cache_hit': cache_lookup.get('cache_hit', False),
                    'execution_time_ms': total_execution_time,
                    'total_results': len(final_results),
                    'query_complexity': query_processing.get('complexity_score', 0),
                    'search_method': 'fts5' if fts5_result.get('fts5_executed', False) else 'none'
                },
                'workflow_metadata': {
                    'run_id': run_id,
                    'nodes_executed': list(results.keys()),
                    'cache_status': cache_lookup.get('cache_status', 'unknown')
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
    
    asyncio.run(demo())