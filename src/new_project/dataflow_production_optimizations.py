"""
DataFlow Production Performance Optimizations
==============================================

Production-ready optimizations for DataFlow operations focusing on:
- 10,000+ records/sec bulk throughput
- Model-specific caching strategies  
- Connection pooling optimization
- Query performance tuning
- Memory-efficient operations

Optimized for the identified high-traffic models:
- Company, Customer, ProductClassification (high-traffic)
- ClassificationCache (ML predictions)
- Quote, Document (bulk imports)
"""

import asyncio
import time
import hashlib
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# DataFlow and SDK imports
from dataflow import DataFlow
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Import our optimized models
from dataflow_classification_models import (
    db, Company, User, Customer, Quote, ProductClassification, 
    ClassificationCache, Document, DocumentProcessingQueue
)


@dataclass
class BulkOperationConfig:
    """Configuration for bulk operations optimization"""
    batch_size: int = 5000
    parallel_workers: int = 4
    memory_limit_mb: int = 512
    timeout_seconds: int = 300
    retry_attempts: int = 3
    use_copy_method: bool = True
    enable_upsert: bool = True
    commit_frequency: int = 1000


@dataclass
class CacheConfig:
    """Model-specific cache configuration"""
    model_name: str
    ttl_seconds: int
    cache_strategy: str  # write_through, write_behind, cache_aside
    warming_enabled: bool = False
    warming_query: Optional[str] = None
    compression_enabled: bool = False
    max_size_mb: int = 100


class ProductionOptimizations:
    """Production optimizations for DataFlow operations"""
    
    def __init__(self, dataflow_db: DataFlow):
        self.db = dataflow_db
        self.runtime = LocalRuntime()
        
        # Model-specific cache configurations
        self.cache_configs = {
            'Company': CacheConfig(
                model_name='Company',
                ttl_seconds=2700,  # 45 minutes
                cache_strategy='write_through',
                warming_enabled=True,
                warming_query="SELECT * FROM companies WHERE is_active = true ORDER BY employee_count DESC LIMIT 1000",
                compression_enabled=True,
                max_size_mb=50
            ),
            'Customer': CacheConfig(
                model_name='Customer',
                ttl_seconds=1800,  # 30 minutes
                cache_strategy='write_through',
                warming_enabled=True,
                warming_query="SELECT * FROM customers WHERE customer_status = 'active' AND total_revenue > 10000 ORDER BY total_revenue DESC LIMIT 2000",
                compression_enabled=True,
                max_size_mb=75
            ),
            'ProductClassification': CacheConfig(
                model_name='ProductClassification',
                ttl_seconds=7200,  # 2 hours
                cache_strategy='write_behind',  # Async for performance
                warming_enabled=True,
                warming_query="SELECT * FROM product_classifications WHERE confidence_level IN ('high', 'very_high') ORDER BY classified_at DESC LIMIT 5000",
                compression_enabled=True,
                max_size_mb=200  # Larger cache for ML data
            ),
            'ClassificationCache': CacheConfig(
                model_name='ClassificationCache',
                ttl_seconds=5400,  # 1.5 hours
                cache_strategy='write_through',
                warming_enabled=True,
                warming_query="SELECT * FROM classification_caches WHERE is_popular = true ORDER BY hit_count DESC LIMIT 3000",
                compression_enabled=True,
                max_size_mb=300  # Largest cache for ML predictions
            ),
            'Quote': CacheConfig(
                model_name='Quote',
                ttl_seconds=900,   # 15 minutes (dynamic pricing)
                cache_strategy='cache_aside',  # Manual control for quotes
                warming_enabled=False,  # Quotes change frequently
                compression_enabled=False,
                max_size_mb=25
            ),
            'Document': CacheConfig(
                model_name='Document',
                ttl_seconds=3600,  # 1 hour
                cache_strategy='write_through',
                warming_enabled=True,
                warming_query="SELECT * FROM documents WHERE ai_status = 'completed' AND upload_date > CURRENT_DATE - INTERVAL '30 days' LIMIT 1000",
                compression_enabled=True,
                max_size_mb=100
            )
        }
        
        # Bulk operation configurations
        self.bulk_configs = {
            'Company': BulkOperationConfig(batch_size=3000, memory_limit_mb=256),
            'Customer': BulkOperationConfig(batch_size=4000, memory_limit_mb=384),
            'ProductClassification': BulkOperationConfig(batch_size=8000, memory_limit_mb=512, parallel_workers=6),
            'Quote': BulkOperationConfig(batch_size=2000, memory_limit_mb=256),
            'Document': BulkOperationConfig(batch_size=1000, memory_limit_mb=768, parallel_workers=2),  # Larger files
            'User': BulkOperationConfig(batch_size=5000, memory_limit_mb=128)
        }
    
    async def execute_optimized_bulk_operation(
        self, 
        model_name: str, 
        operation: str, 
        data: List[Dict[str, Any]],
        config_override: Optional[BulkOperationConfig] = None
    ) -> Dict[str, Any]:
        """Execute bulk operation with production optimizations"""
        
        config = config_override or self.bulk_configs.get(model_name, BulkOperationConfig())
        
        start_time = time.time()
        total_records = len(data)
        processed_records = 0
        errors = []
        
        print(f"🚀 Starting optimized bulk {operation} for {model_name}: {total_records:,} records")
        print(f"   • Batch size: {config.batch_size:,}")
        print(f"   • Parallel workers: {config.parallel_workers}")
        print(f"   • Memory limit: {config.memory_limit_mb}MB")
        
        # Split data into batches
        batches = [
            data[i:i + config.batch_size] 
            for i in range(0, len(data), config.batch_size)
        ]
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=config.parallel_workers) as executor:
            # Submit batch jobs
            future_to_batch = {
                executor.submit(
                    self._process_batch,
                    model_name, operation, batch, batch_idx, config
                ): batch_idx
                for batch_idx, batch in enumerate(batches)
            }
            
            # Collect results
            batch_results = []
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                try:
                    result = future.result(timeout=config.timeout_seconds)
                    batch_results.append(result)
                    processed_records += result['processed_count']
                    
                    if result['errors']:
                        errors.extend(result['errors'])
                    
                    # Progress reporting
                    progress = (processed_records / total_records) * 100
                    print(f"   📊 Batch {batch_idx + 1}/{len(batches)} completed - {progress:.1f}% ({processed_records:,}/{total_records:,})")
                    
                except Exception as e:
                    errors.append({
                        'batch_idx': batch_idx,
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    print(f"   ❌ Batch {batch_idx + 1} failed: {e}")
        
        execution_time = time.time() - start_time
        throughput = processed_records / execution_time if execution_time > 0 else 0
        
        result = {
            'success': processed_records > 0,
            'model': model_name,
            'operation': operation,
            'total_records': total_records,
            'processed_records': processed_records,
            'failed_records': total_records - processed_records,
            'execution_time_seconds': execution_time,
            'throughput_records_per_second': throughput,
            'batches_processed': len(batch_results),
            'errors': errors,
            'performance_metrics': {
                'avg_batch_time': sum(r['execution_time'] for r in batch_results) / len(batch_results) if batch_results else 0,
                'max_batch_time': max((r['execution_time'] for r in batch_results), default=0),
                'min_batch_time': min((r['execution_time'] for r in batch_results), default=0),
                'memory_usage_mb': config.memory_limit_mb,
                'parallel_workers': config.parallel_workers
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        print(f"✅ Bulk operation completed:")
        print(f"   • Processed: {processed_records:,}/{total_records:,} records")
        print(f"   • Throughput: {throughput:,.0f} records/second")
        print(f"   • Total time: {execution_time:.2f}s")
        print(f"   • Errors: {len(errors)}")
        
        return result
    
    def _process_batch(
        self, 
        model_name: str, 
        operation: str, 
        batch_data: List[Dict[str, Any]], 
        batch_idx: int,
        config: BulkOperationConfig
    ) -> Dict[str, Any]:
        """Process a single batch with retries"""
        
        for attempt in range(config.retry_attempts):
            try:
                start_time = time.time()
                
                # Create workflow for batch operation
                workflow = WorkflowBuilder()
                
                node_name = f"{model_name}Bulk{operation.title()}Node"
                
                # Add bulk operation node with optimizations
                workflow.add_node(node_name, f"batch_{batch_idx}", {
                    "data": batch_data,
                    "batch_size": len(batch_data),
                    "use_copy_method": config.use_copy_method,
                    "enable_upsert": config.enable_upsert,
                    "commit_frequency": config.commit_frequency,
                    "timeout_seconds": config.timeout_seconds
                })
                
                # Execute workflow
                results, run_id = self.runtime.execute(workflow.build())
                
                execution_time = time.time() - start_time
                
                return {
                    'batch_idx': batch_idx,
                    'processed_count': len(batch_data),
                    'execution_time': execution_time,
                    'throughput': len(batch_data) / execution_time if execution_time > 0 else 0,
                    'run_id': run_id,
                    'attempt': attempt + 1,
                    'errors': []
                }
                
            except Exception as e:
                if attempt == config.retry_attempts - 1:
                    # Final attempt failed
                    return {
                        'batch_idx': batch_idx,
                        'processed_count': 0,
                        'execution_time': 0,
                        'throughput': 0,
                        'run_id': None,
                        'attempt': attempt + 1,
                        'errors': [str(e)]
                    }
                else:
                    # Retry with exponential backoff
                    time.sleep(2 ** attempt)
                    continue
    
    async def warm_model_cache(self, model_name: str) -> Dict[str, Any]:
        """Warm cache for specific model"""
        
        config = self.cache_configs.get(model_name)
        if not config or not config.warming_enabled:
            return {
                'success': False,
                'message': f"Cache warming not configured for {model_name}"
            }
        
        start_time = time.time()
        
        print(f"🔥 Warming cache for {model_name}...")
        
        try:
            # Create workflow for cache warming
            workflow = WorkflowBuilder()
            
            # Use List operation to fetch warming data
            workflow.add_node(f"{model_name}ListNode", "warm_cache", {
                "limit": 5000,  # Configurable limit
                "include_metadata": True,
                "cache_results": True,
                "cache_ttl": config.ttl_seconds
            })
            
            # Execute warming workflow
            results, run_id = self.runtime.execute(workflow.build())
            
            execution_time = time.time() - start_time
            
            warmed_count = len(results.get("warm_cache", []))
            
            print(f"✅ Cache warming completed for {model_name}:")
            print(f"   • Records warmed: {warmed_count:,}")
            print(f"   • Time taken: {execution_time:.2f}s")
            print(f"   • Cache TTL: {config.ttl_seconds}s")
            
            return {
                'success': True,
                'model': model_name,
                'warmed_count': warmed_count,
                'execution_time': execution_time,
                'cache_ttl': config.ttl_seconds,
                'run_id': run_id
            }
            
        except Exception as e:
            print(f"❌ Cache warming failed for {model_name}: {e}")
            return {
                'success': False,
                'model': model_name,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    async def warm_all_caches(self) -> Dict[str, Any]:
        """Warm caches for all configured models"""
        
        print(f"🔥 Starting cache warming for {len(self.cache_configs)} models...")
        
        start_time = time.time()
        results = {}
        
        # Warm caches in parallel
        warming_tasks = [
            self.warm_model_cache(model_name)
            for model_name, config in self.cache_configs.items()
            if config.warming_enabled
        ]
        
        warming_results = await asyncio.gather(*warming_tasks, return_exceptions=True)
        
        # Process results
        total_warmed = 0
        successful_models = 0
        
        for i, result in enumerate(warming_results):
            model_name = list(self.cache_configs.keys())[i]
            
            if isinstance(result, Exception):
                results[model_name] = {
                    'success': False,
                    'error': str(result)
                }
            else:
                results[model_name] = result
                if result['success']:
                    total_warmed += result.get('warmed_count', 0)
                    successful_models += 1
        
        total_time = time.time() - start_time
        
        print(f"✅ Cache warming completed:")
        print(f"   • Models warmed: {successful_models}/{len(warming_tasks)}")
        print(f"   • Total records: {total_warmed:,}")
        print(f"   • Total time: {total_time:.2f}s")
        
        return {
            'success': successful_models > 0,
            'total_models': len(warming_tasks),
            'successful_models': successful_models,
            'total_warmed_records': total_warmed,
            'total_execution_time': total_time,
            'model_results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def create_performance_monitoring_workflow(self) -> WorkflowBuilder:
        """Create workflow for performance monitoring"""
        
        workflow = WorkflowBuilder()
        
        # Connection pool monitoring
        workflow.add_node("ConnectionPoolMonitorNode", "monitor_pool", {
            "track_active_connections": True,
            "track_pool_overflow": True,
            "alert_threshold": 0.8  # Alert at 80% capacity
        })
        
        # Cache performance monitoring
        workflow.add_node("CachePerformanceNode", "monitor_cache", {
            "track_hit_ratio": True,
            "track_memory_usage": True,
            "track_eviction_rate": True,
            "models": list(self.cache_configs.keys())
        })
        
        # Query performance monitoring
        workflow.add_node("QueryPerformanceNode", "monitor_queries", {
            "slow_query_threshold": 1000,  # 1 second
            "track_execution_plans": True,
            "track_lock_waits": True
        })
        
        # Bulk operation monitoring
        workflow.add_node("BulkOperationMonitorNode", "monitor_bulk", {
            "track_throughput": True,
            "track_error_rates": True,
            "track_memory_usage": True
        })
        
        # Connect monitoring nodes
        workflow.connect("monitor_pool", "monitor_cache")
        workflow.connect("monitor_cache", "monitor_queries")
        workflow.connect("monitor_queries", "monitor_bulk")
        
        return workflow
    
    def get_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Get performance optimization recommendations"""
        
        recommendations = []
        
        # Connection pool recommendations
        recommendations.append({
            'category': 'Connection Pool',
            'priority': 'high',
            'recommendation': 'Monitor connection pool usage and adjust pool_size/max_overflow based on peak load',
            'current_config': {
                'pool_size': 75,
                'pool_max_overflow': 150,
                'pool_recycle': 1200
            },
            'suggested_monitoring': 'Track active connections, pool overflow events, and connection wait times'
        })
        
        # Caching recommendations
        recommendations.append({
            'category': 'Caching',
            'priority': 'high',
            'recommendation': 'Implement model-specific cache warming and TTL optimization',
            'models': {
                'ProductClassification': '2 hours TTL (stable ML predictions)',
                'ClassificationCache': '1.5 hours TTL (ML cache optimization)',
                'Company': '45 minutes TTL (moderate update frequency)',
                'Customer': '30 minutes TTL (dynamic business data)'
            },
            'suggested_monitoring': 'Track cache hit ratios, memory usage, and warming effectiveness'
        })
        
        # Bulk operation recommendations
        recommendations.append({
            'category': 'Bulk Operations',
            'priority': 'medium',
            'recommendation': 'Use model-specific batch sizes and parallel processing',
            'optimal_batch_sizes': {
                'ProductClassification': '8,000 records (ML data)',
                'Customer': '4,000 records (business data)',
                'Company': '3,000 records (complex relationships)',
                'Document': '1,000 records (large files)'
            },
            'suggested_monitoring': 'Track throughput, memory usage, and error rates'
        })
        
        # Index optimization recommendations
        recommendations.append({
            'category': 'Indexing',
            'priority': 'medium',
            'recommendation': 'Implement covering indexes and partial indexes for common queries',
            'key_optimizations': [
                'GIN indexes for JSONB fields with path operators',
                'Partial indexes with WHERE conditions for active records',
                'Covering indexes to avoid table lookups',
                'Trigram indexes for fuzzy text search'
            ],
            'suggested_monitoring': 'Track index usage, query execution plans, and table scan ratios'
        })
        
        return recommendations


# Initialize production optimizations
production_optimizer = ProductionOptimizations(db)


async def run_performance_benchmark():
    """Run comprehensive performance benchmark"""
    
    print("\n" + "="*80)
    print("🎯 DATAFLOW PRODUCTION PERFORMANCE BENCHMARK")
    print("="*80)
    
    # Test data generation
    def generate_test_companies(count: int) -> List[Dict[str, Any]]:
        return [
            {
                "name": f"Test Company {i}",
                "industry": "technology" if i % 2 == 0 else "manufacturing",
                "employee_count": (i % 1000) + 10,
                "is_active": True,
                "founded_year": 2000 + (i % 24)
            }
            for i in range(count)
        ]
    
    def generate_test_classifications(count: int) -> List[Dict[str, Any]]:
        return [
            {
                "product_id": i + 1,
                "unspsc_code": f"1234567{i % 10}",
                "unspsc_confidence": 0.8 + (i % 20) / 100,
                "etim_class_id": f"EC{i:06d}",
                "etim_confidence": 0.7 + (i % 30) / 100,
                "classification_method": "ml_automatic",
                "confidence_level": "high" if i % 3 == 0 else "medium",
                "classification_text": f"Product classification text {i}"
            }
            for i in range(count)
        ]
    
    # Benchmark configurations
    benchmarks = [
        {
            'name': 'Company Bulk Insert',
            'model': 'Company',
            'operation': 'create',
            'data_generator': generate_test_companies,
            'record_counts': [1000, 5000, 10000, 25000],
            'target_throughput': 3000  # records/second
        },
        {
            'name': 'ProductClassification Bulk Insert',
            'model': 'ProductClassification', 
            'operation': 'create',
            'data_generator': generate_test_classifications,
            'record_counts': [5000, 10000, 25000, 50000],
            'target_throughput': 8000  # records/second
        }
    ]
    
    benchmark_results = []
    
    for benchmark in benchmarks:
        print(f"\n📊 Running benchmark: {benchmark['name']}")
        print("-" * 50)
        
        for record_count in benchmark['record_counts']:
            print(f"\n🔄 Testing {record_count:,} records...")
            
            # Generate test data
            test_data = benchmark['data_generator'](record_count)
            
            # Run bulk operation
            result = await production_optimizer.execute_optimized_bulk_operation(
                benchmark['model'],
                benchmark['operation'],
                test_data
            )
            
            # Analyze performance
            throughput = result['throughput_records_per_second']
            target = benchmark['target_throughput']
            performance_ratio = throughput / target if target > 0 else 0
            
            benchmark_result = {
                'benchmark': benchmark['name'],
                'model': benchmark['model'],
                'record_count': record_count,
                'throughput': throughput,
                'target_throughput': target,
                'performance_ratio': performance_ratio,
                'execution_time': result['execution_time_seconds'],
                'success_rate': result['processed_records'] / result['total_records'],
                'meets_target': performance_ratio >= 1.0
            }
            
            benchmark_results.append(benchmark_result)
            
            # Performance status
            status = "✅ PASS" if performance_ratio >= 1.0 else "⚠️  BELOW TARGET"
            print(f"   {status}: {throughput:,.0f} records/sec (target: {target:,})")
    
    # Cache warming benchmark
    print(f"\n🔥 Testing cache warming performance...")
    cache_result = await production_optimizer.warm_all_caches()
    print(f"✅ Cache warming: {cache_result['total_warmed_records']:,} records in {cache_result['total_execution_time']:.2f}s")
    
    # Summary report
    print(f"\n" + "="*80)
    print("📈 PERFORMANCE BENCHMARK SUMMARY")
    print("="*80)
    
    for result in benchmark_results:
        status = "✅ PASS" if result['meets_target'] else "❌ FAIL"
        print(f"{status} {result['benchmark']} - {result['record_count']:,} records: {result['throughput']:,.0f} rec/sec")
    
    # Performance recommendations
    print(f"\n💡 PERFORMANCE RECOMMENDATIONS:")
    recommendations = production_optimizer.get_performance_recommendations()
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['category']} ({rec['priority']} priority): {rec['recommendation']}")
    
    return benchmark_results


# CLI interface for production optimizations
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "benchmark":
            asyncio.run(run_performance_benchmark())
        elif command == "warm-cache":
            model = sys.argv[2] if len(sys.argv) > 2 else None
            if model:
                result = asyncio.run(production_optimizer.warm_model_cache(model))
                print(json.dumps(result, indent=2))
            else:
                result = asyncio.run(production_optimizer.warm_all_caches())
                print(json.dumps(result, indent=2))
        elif command == "recommendations":
            recommendations = production_optimizer.get_performance_recommendations()
            print(json.dumps(recommendations, indent=2))
        else:
            print("Available commands: benchmark, warm-cache [model], recommendations")
    else:
        print("DataFlow Production Optimizations")
        print("Available commands:")
        print("  python dataflow_production_optimizations.py benchmark")
        print("  python dataflow_production_optimizations.py warm-cache [model_name]")
        print("  python dataflow_production_optimizations.py recommendations")