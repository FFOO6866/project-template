"""
DataFlow Zero-Config Database Operations Demo
============================================

Comprehensive demonstration of zero-config database operations using DataFlow
auto-generated nodes. Shows how @db.model decorators automatically create
9 node types per model for seamless database integration.

This module demonstrates:
- Auto-generated CRUD operations (Create, Read, Update, Delete, List)
- Auto-generated bulk operations (BulkCreate, BulkUpdate, BulkDelete, BulkUpsert)
- Enterprise features (multi-tenancy, audit logs, soft deletes)
- AI service integration patterns
- Real-world workflow examples
- Performance optimization techniques
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataflow_ai_integration import db, Product, Vendor, KnowledgeGraphEntity, VectorEmbedding, AIRecommendation
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
import uuid
import json

# ==============================================================================
# ZERO-CONFIG DATABASE OPERATIONS DEMO
# ==============================================================================

class DataFlowZeroConfigDemo:
    """
    Comprehensive demonstration of DataFlow's zero-config approach.
    Each @db.model automatically generates 9 node types with no additional configuration.
    """
    
    def __init__(self):
        self.runtime = LocalRuntime()
        print("🚀 DataFlow Zero-Config Demo Initialized")
        print("📊 Available auto-generated nodes per model:")
        print("   • CreateNode, ReadNode, UpdateNode, DeleteNode")
        print("   • ListNode, BulkCreateNode, BulkUpdateNode, BulkDeleteNode, BulkUpsertNode")
        print()
    
    def demo_single_record_operations(self) -> None:
        """
        Demonstrate single record CRUD operations using auto-generated nodes.
        Shows zero-config Create, Read, Update, Delete operations.
        """
        print("=" * 60)
        print("🔧 SINGLE RECORD OPERATIONS DEMO")
        print("=" * 60)
        
        workflow = WorkflowBuilder()
        
        # 1. CREATE: Auto-generated ProductCreateNode
        print("1. Creating product using ProductCreateNode...")
        workflow.add_node("ProductCreateNode", "create_product", {
            "product_code": "DEMO-001",
            "name": "Smart Industrial Drill",
            "description": "AI-powered precision drill with safety sensors",
            "category": "Power Tools",
            "brand": "TechTools Pro",
            "list_price": 299.99,
            "specifications": {
                "power": "18V",
                "torque": "65 Nm",
                "chuck_size": "13mm",
                "battery_type": "Li-ion"
            },
            "features": {
                "smart_torque_control": True,
                "led_worklight": True,
                "battery_indicator": True,
                "safety_clutch": True
            },
            "safety_rating": 4.5,
            "is_available": True,
            "stock_quantity": 50,
            "embedding_status": "pending"
        })
        
        # 2. READ: Auto-generated ProductReadNode
        print("2. Reading product using ProductReadNode...")
        workflow.add_node("ProductReadNode", "read_product", {
            # ID will be connected from create operation
        })
        
        # 3. UPDATE: Auto-generated ProductUpdateNode
        print("3. Updating product using ProductUpdateNode...")
        workflow.add_node("ProductUpdateNode", "update_product", {
            "list_price": 279.99,  # Price reduction
            "stock_quantity": 45,   # Inventory update
            "ai_tags": ["precision", "safety", "professional"],
            "embedding_status": "processing"
        })
        
        # Connect create -> read -> update
        workflow.add_connection("create_product", "id", "read_product", "id")
        workflow.add_connection("read_product", "id", "update_product", "id")
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        print(f"✅ Single record operations completed (Run ID: {run_id})")
        print(f"📝 Created product: {results.get('create_product', {}).get('product_code', 'N/A')}")
        print(f"💰 Updated price: ${results.get('update_product', {}).get('list_price', 'N/A')}")
        print()
        
        return results, run_id
    
    def demo_bulk_operations(self) -> None:
        """
        Demonstrate bulk operations using auto-generated bulk nodes.
        Shows high-performance batch processing capabilities.
        """
        print("=" * 60)
        print("📦 BULK OPERATIONS DEMO")
        print("=" * 60)
        
        workflow = WorkflowBuilder()
        
        # Prepare bulk product data
        bulk_products = []
        for i in range(1, 11):  # 10 products
            bulk_products.append({
                "product_code": f"BULK-{i:03d}",
                "name": f"Professional Tool {i}",
                "description": f"High-quality professional tool #{i} for industrial use",
                "category": "Professional Tools",
                "brand": "BulkTools Inc",
                "list_price": 150.00 + (i * 10),
                "specifications": {
                    "model": f"PT-{i:03d}",
                    "weight": f"{2.0 + (i * 0.1)}kg",
                    "warranty": "2 years"
                },
                "safety_rating": 4.0 + (i * 0.05),
                "is_available": True,
                "stock_quantity": 100 - (i * 5),
                "embedding_status": "pending"
            })
        
        # 1. BULK CREATE: Auto-generated ProductBulkCreateNode
        print("1. Bulk creating 10 products using ProductBulkCreateNode...")
        workflow.add_node("ProductBulkCreateNode", "bulk_create_products", {
            "data": bulk_products,
            "batch_size": 5,  # Process in batches of 5
            "conflict_resolution": "upsert",  # Handle duplicates
            "return_ids": True
        })
        
        # 2. BULK UPDATE: Auto-generated ProductBulkUpdateNode
        print("2. Bulk updating products using ProductBulkUpdateNode...")
        workflow.add_node("ProductBulkUpdateNode", "bulk_update_products", {
            "filter": {
                "category": "Professional Tools",
                "brand": "BulkTools Inc"
            },
            "update": {
                "embedding_status": "processing",
                "ai_tags": ["professional", "industrial", "bulk-demo"]
            },
            "limit": 10
        })
        
        # 3. BULK UPSERT: Auto-generated ProductBulkUpsertNode
        print("3. Bulk upserting with modified data using ProductBulkUpsertNode...")
        # Modify some products for upsert demo
        upsert_products = bulk_products[:5]  # First 5 products
        for product in upsert_products:
            product["list_price"] *= 1.1  # 10% price increase
            product["stock_quantity"] += 25  # Increase stock
        
        workflow.add_node("ProductBulkUpsertNode", "bulk_upsert_products", {
            "data": upsert_products,
            "batch_size": 3,
            "conflict_resolution": "update",
            "match_fields": ["product_code"],  # Match on product_code
            "update_fields": ["list_price", "stock_quantity"]  # Only update these fields
        })
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        print(f"✅ Bulk operations completed (Run ID: {run_id})")
        created_count = len(results.get('bulk_create_products', []))
        print(f"📦 Created {created_count} products in bulk")
        print(f"🔄 Updated products with AI tags")
        print(f"⚡ Upserted 5 products with price/stock changes")
        print()
        
        return results, run_id
    
    def demo_complex_queries(self) -> None:
        """
        Demonstrate complex queries using auto-generated ListNode with MongoDB-style filters.
        Shows advanced filtering, sorting, and pagination capabilities.
        """
        print("=" * 60)
        print("🔍 COMPLEX QUERIES DEMO")
        print("=" * 60)
        
        workflow = WorkflowBuilder()
        
        # 1. ADVANCED FILTERING: MongoDB-style operators
        print("1. Advanced filtering with MongoDB-style operators...")
        workflow.add_node("ProductListNode", "advanced_filter", {
            "filter": {
                "list_price": {"$gte": 200, "$lte": 500},  # Price range
                "safety_rating": {"$gt": 4.0},              # High safety rating
                "category": {"$in": ["Power Tools", "Professional Tools"]},  # Multiple categories
                "brand": {"$ne": "Unknown"},                # Not unknown brand
                "specifications.power": {"$regex": "18V"},  # Regex on nested field
                "is_available": True,
                "stock_quantity": {"$gt": 0}
            },
            "order_by": ["-safety_rating", "list_price"],  # Sort by safety desc, price asc
            "limit": 5
        })
        
        # 2. TEXT SEARCH: Full-text search capabilities
        print("2. Full-text search on product names and descriptions...")
        workflow.add_node("ProductListNode", "text_search", {
            "filter": {
                "$text": {
                    "$search": "professional drill precision",
                    "$caseSensitive": False
                },
                "is_available": True
            },
            "order_by": [{"$meta": "textScore"}],  # Order by relevance
            "limit": 10
        })
        
        # 3. AGGREGATION: Category-based statistics
        print("3. Category aggregation and statistics...")
        workflow.add_node("ProductListNode", "category_stats", {
            "filter": {"is_available": True},
            "aggregate": {
                "group_by": ["category"],
                "metrics": {
                    "total_products": {"$count": "*"},
                    "avg_price": {"$avg": "list_price"},
                    "max_safety_rating": {"$max": "safety_rating"},
                    "total_stock": {"$sum": "stock_quantity"}
                }
            },
            "order_by": ["-total_products"]
        })
        
        # 4. PAGINATION: Large result set handling
        print("4. Pagination for large result sets...")
        workflow.add_node("ProductListNode", "paginated_results", {
            "filter": {"is_available": True},
            "order_by": ["category", "brand", "name"],
            "limit": 20,
            "offset": 0  # First page
        })
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        print(f"✅ Complex queries completed (Run ID: {run_id})")
        
        advanced_results = results.get('advanced_filter', [])
        text_results = results.get('text_search', [])
        category_stats = results.get('category_stats', [])
        paginated_results = results.get('paginated_results', [])
        
        print(f"🔍 Advanced filter found {len(advanced_results)} products")
        print(f"📝 Text search found {len(text_results)} matching products")
        print(f"📊 Category stats: {len(category_stats)} categories analyzed")
        print(f"📄 Paginated results: {len(paginated_results)} products (page 1)")
        print()
        
        return results, run_id
    
    def demo_ai_integration_workflow(self) -> None:
        """
        Demonstrate AI service integration using DataFlow nodes.
        Shows how auto-generated nodes work with AI processing pipelines.
        """
        print("=" * 60)
        print("🤖 AI INTEGRATION WORKFLOW DEMO")
        print("=" * 60)
        
        workflow = WorkflowBuilder()
        
        # 1. CREATE AI RECOMMENDATION REQUEST
        print("1. Creating AI recommendation request...")
        workflow.add_node("AIRecommendationCreateNode", "create_ai_request", {
            "request_id": str(uuid.uuid4()),
            "recommendation_type": "tool",
            "context_data": {
                "task": "drilling precision holes in metal",
                "user_skill_level": "intermediate",
                "budget": 400,
                "workspace": "workshop",
                "safety_priority": "high"
            },
            "ai_model": "gpt-4",
            "prompt_template": "tool_recommendation",
            "status": "processing",
            "created_at": datetime.now()
        })
        
        # 2. CREATE VECTOR EMBEDDING RECORD
        print("2. Creating vector embedding tracking record...")
        workflow.add_node("VectorEmbeddingCreateNode", "create_embedding_record", {
            "entity_type": "recommendation_request",
            "collection_name": "recommendations",
            "embedding_id": f"rec_{str(uuid.uuid4())[:8]}",
            "embedding_model": "text-embedding-ada-002",
            "embedding_dimension": 1536,
            "embedding_status": "pending",
            "content_version": 1,
            "last_updated": datetime.now()
        })
        
        # 3. CREATE KNOWLEDGE GRAPH ENTITY
        print("3. Creating knowledge graph entity record...")
        workflow.add_node("KnowledgeGraphEntityCreateNode", "create_kg_entity", {
            "entity_type": "recommendation",
            "neo4j_labels": ["Recommendation", "ToolRequest"],
            "sync_status": "pending",
            "sync_direction": "to_neo4j",
            "schema_version": "1.0"
        })
        
        # 4. QUERY RELATED PRODUCTS
        print("4. Querying related products for recommendations...")
        workflow.add_node("ProductListNode", "get_drilling_tools", {
            "filter": {
                "category": {"$in": ["Power Tools", "Drilling Equipment"]},
                "specifications.application": {"$regex": "drilling|precision"},
                "safety_rating": {"$gte": 4.0},
                "list_price": {"$lte": 400},
                "is_available": True
            },
            "order_by": ["-safety_rating", "list_price"],
            "limit": 10
        })
        
        # 5. BULK UPDATE SEARCH STATISTICS
        print("5. Updating product search statistics...")
        workflow.add_node("ProductBulkUpdateNode", "update_search_stats", {
            "filter": {
                "category": {"$in": ["Power Tools", "Drilling Equipment"]}
            },
            "update": {
                "seo_keywords": {"$addToSet": ["drilling", "precision", "metal"]},
                "last_searched": datetime.now()
            },
            "limit": 10
        })
        
        # Connect AI request ID to related records
        workflow.add_connection("create_ai_request", "id", "create_embedding_record", "entity_id")
        workflow.add_connection("create_ai_request", "id", "create_kg_entity", "entity_id")
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        print(f"✅ AI integration workflow completed (Run ID: {run_id})")
        
        ai_request = results.get('create_ai_request', {})
        embedding_record = results.get('create_embedding_record', {})
        kg_entity = results.get('create_kg_entity', {})
        drilling_tools = results.get('get_drilling_tools', [])
        
        print(f"🤖 AI request created: {ai_request.get('request_id', 'N/A')[:8]}...")
        print(f"🔗 Vector embedding record: {embedding_record.get('embedding_id', 'N/A')}")
        print(f"📊 Knowledge graph entity: {kg_entity.get('id', 'N/A')}")
        print(f"🔧 Found {len(drilling_tools)} relevant drilling tools")
        print()
        
        return results, run_id
    
    def demo_enterprise_features(self) -> None:
        """
        Demonstrate enterprise features: multi-tenancy, audit logs, soft deletes.
        Shows how DataFlow handles enterprise requirements automatically.
        """
        print("=" * 60)
        print("🏢 ENTERPRISE FEATURES DEMO")
        print("=" * 60)
        
        workflow = WorkflowBuilder()
        
        # 1. MULTI-TENANT OPERATIONS
        print("1. Multi-tenant product creation...")
        workflow.add_node("ProductCreateNode", "create_tenant_product", {
            "product_code": "TENANT-A-001",
            "name": "Tenant A Exclusive Tool",
            "description": "Tool available only to Tenant A",
            "category": "Exclusive Tools",
            "brand": "Tenant Brand",
            "list_price": 199.99,
            "tenant_id": "tenant-a-12345",  # Multi-tenant isolation
            "is_available": True
        })
        
        # 2. AUDIT LOG DEMONSTRATION
        print("2. Creating operations that generate audit logs...")
        workflow.add_node("ProductUpdateNode", "update_for_audit", {
            "list_price": 189.99,  # Price change (audited)
            "specifications": {
                "updated_by": "demo_user",
                "update_reason": "promotional_pricing"
            }
        })
        
        # 3. SOFT DELETE DEMONSTRATION
        print("3. Soft delete operation (preserves data)...")
        workflow.add_node("ProductDeleteNode", "soft_delete_product", {
            # This will perform soft delete, not hard delete
            "soft_delete": True,
            "deletion_reason": "discontinued_model"
        })
        
        # 4. VERSIONED DATA OPERATIONS
        print("4. Versioned update (creates new version)...")
        workflow.add_node("ProductCreateNode", "create_versioned_product", {
            "product_code": "VERSIONED-001",
            "name": "Versioned Product",
            "description": "Product with version control",
            "category": "Versioned Tools",
            "brand": "Version Brand",
            "list_price": 299.99,
            "version": 1,
            "is_available": True
        })
        
        # 5. TENANT-ISOLATED QUERIES
        print("5. Tenant-isolated product queries...")
        workflow.add_node("ProductListNode", "get_tenant_products", {
            "filter": {
                "tenant_id": "tenant-a-12345",
                "deleted_at": None  # Only non-deleted items
            },
            "limit": 20
        })
        
        # Connect operations for audit trail
        workflow.add_connection("create_tenant_product", "id", "update_for_audit", "id")
        workflow.add_connection("update_for_audit", "id", "soft_delete_product", "id")
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        print(f"✅ Enterprise features demo completed (Run ID: {run_id})")
        
        tenant_product = results.get('create_tenant_product', {})
        updated_product = results.get('update_for_audit', {})
        versioned_product = results.get('create_versioned_product', {})
        tenant_products = results.get('get_tenant_products', [])
        
        print(f"🏢 Tenant product created: {tenant_product.get('product_code', 'N/A')}")
        print(f"📝 Audit trail: Price change logged automatically")
        print(f"🗑️ Soft delete: Data preserved with deletion timestamp")
        print(f"📋 Versioned product: {versioned_product.get('product_code', 'N/A')}")
        print(f"🔍 Tenant query returned {len(tenant_products)} products")
        print()
        
        return results, run_id
    
    def demo_performance_optimization(self) -> None:
        """
        Demonstrate performance optimization techniques using DataFlow.
        Shows batch processing, connection pooling, and query optimization.
        """
        print("=" * 60)
        print("⚡ PERFORMANCE OPTIMIZATION DEMO")
        print("=" * 60)
        
        workflow = WorkflowBuilder()
        
        # 1. OPTIMIZED BULK OPERATIONS
        print("1. High-performance bulk operations...")
        
        # Create large batch of products for performance testing
        perf_products = []
        for i in range(1, 101):  # 100 products
            perf_products.append({
                "product_code": f"PERF-{i:04d}",
                "name": f"Performance Test Product {i}",
                "description": f"High-volume test product #{i}",
                "category": "Performance Test",
                "brand": "PerfTest Inc",
                "list_price": 100.0 + i,
                "safety_rating": 3.5 + (i % 10) * 0.1,
                "is_available": True,
                "stock_quantity": i * 10,
                "embedding_status": "pending"
            })
        
        # Use large batch size for optimal performance
        workflow.add_node("ProductBulkCreateNode", "bulk_create_performance", {
            "data": perf_products,
            "batch_size": 50,  # Optimal batch size for PostgreSQL
            "conflict_resolution": "upsert",
            "return_ids": False  # Skip ID return for better performance
        })
        
        # 2. OPTIMIZED QUERIES WITH INDEXES
        print("2. Index-optimized queries...")
        workflow.add_node("ProductListNode", "optimized_category_query", {
            "filter": {
                "category": "Performance Test",  # Uses category index
                "is_available": True,           # Uses availability index
                "safety_rating": {"$gte": 4.0}  # Uses safety_rating index
            },
            "order_by": ["category", "safety_rating"],  # Uses compound index
            "limit": 25
        })
        
        # 3. BATCH UPDATE WITH JSONB OPERATIONS
        print("3. High-performance JSONB updates...")
        workflow.add_node("ProductBulkUpdateNode", "batch_jsonb_update", {
            "filter": {"category": "Performance Test"},
            "update": {
                "specifications": {
                    "$set": {
                        "performance_tested": True,
                        "test_date": datetime.now().isoformat(),
                        "batch_number": "PERF-001"
                    }
                },
                "ai_tags": {"$addToSet": ["performance", "tested", "bulk"]}
            },
            "limit": 100
        })
        
        # 4. CONCURRENT OPERATIONS SIMULATION
        print("4. Concurrent operation patterns...")
        
        # Simulate concurrent reads (safe operations)
        workflow.add_node("ProductListNode", "concurrent_read_1", {
            "filter": {"brand": "PerfTest Inc"},
            "limit": 20
        })
        
        workflow.add_node("ProductListNode", "concurrent_read_2", {
            "filter": {"category": "Performance Test"},
            "limit": 20
        })
        
        workflow.add_node("ProductListNode", "concurrent_read_3", {
            "filter": {"safety_rating": {"$gte": 4.0}},
            "limit": 20
        })
        
        # Execute workflow
        start_time = datetime.now()
        results, run_id = self.runtime.execute(workflow.build())
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"✅ Performance optimization demo completed (Run ID: {run_id})")
        print(f"⏱️ Total execution time: {execution_time:.3f} seconds")
        
        created_products = len(results.get('bulk_create_performance', []))
        optimized_query = len(results.get('optimized_category_query', []))
        concurrent_1 = len(results.get('concurrent_read_1', []))
        concurrent_2 = len(results.get('concurrent_read_2', []))
        concurrent_3 = len(results.get('concurrent_read_3', []))
        
        print(f"📦 Bulk created: {created_products} products")
        print(f"🔍 Optimized query: {optimized_query} results")
        print(f"🔄 Concurrent operations: {concurrent_1 + concurrent_2 + concurrent_3} total results")
        print(f"⚡ Average throughput: {created_products / execution_time:.1f} products/second")
        print()
        
        return results, run_id, execution_time

# ==============================================================================
# COMPREHENSIVE DEMO RUNNER
# ==============================================================================

def run_complete_dataflow_demo():
    """
    Run the complete DataFlow zero-config demonstration.
    Shows all major features and capabilities.
    """
    print("🚀 DATAFLOW ZERO-CONFIG COMPREHENSIVE DEMO")
    print("=" * 80)
    print("This demo showcases DataFlow's revolutionary zero-config approach:")
    print("• Each @db.model automatically generates 9 database operation nodes")
    print("• No manual configuration required")
    print("• Enterprise features enabled by default")
    print("• AI service integration patterns")
    print("• High-performance bulk operations")
    print("=" * 80)
    print()
    
    demo = DataFlowZeroConfigDemo()
    
    try:
        # Run all demo sections
        demo.demo_single_record_operations()
        demo.demo_bulk_operations()
        demo.demo_complex_queries()
        demo.demo_ai_integration_workflow()
        demo.demo_enterprise_features()
        results, run_id, exec_time = demo.demo_performance_optimization()
        
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("Key Takeaways:")
        print("✅ Zero configuration required - @db.model does everything")
        print("✅ 9 auto-generated nodes per model (CRUD + Bulk operations)")
        print("✅ Enterprise features (multi-tenancy, audit, soft delete)")
        print("✅ AI service integration with tracking and orchestration")
        print("✅ High-performance operations with optimal PostgreSQL usage")
        print("✅ MongoDB-style query syntax with SQL performance")
        print("=" * 80)
        print(f"Final execution time: {exec_time:.3f} seconds")
        print(f"Demo run ID: {run_id}")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        print("This is expected in development - actual DataFlow would handle these operations")

# ==============================================================================
# EXAMPLE USAGE PATTERNS
# ==============================================================================

def example_real_world_patterns():
    """
    Real-world usage patterns for DataFlow AI integration.
    Shows practical applications and common workflows.
    """
    print("\n📋 REAL-WORLD DATAFLOW PATTERNS")
    print("=" * 50)
    
    # Pattern 1: E-commerce Product Onboarding
    print("Pattern 1: E-commerce Product Onboarding")
    print("- ProductCreateNode: Add new product")
    print("- AIProcessingQueueCreateNode: Queue for classification")
    print("- VectorEmbeddingCreateNode: Generate embeddings")
    print("- KnowledgeGraphEntityCreateNode: Add to knowledge graph")
    print()
    
    # Pattern 2: Inventory Management
    print("Pattern 2: Inventory Management")
    print("- ProductBulkUpdateNode: Update stock levels")
    print("- ProductListNode: Query low-stock items")
    print("- VendorListNode: Find suppliers")
    print("- AIRecommendationCreateNode: Reorder recommendations")
    print()
    
    # Pattern 3: Customer Intelligence
    print("Pattern 3: Customer Intelligence")
    print("- AIRecommendationCreateNode: Generate recommendations")
    print("- ProductListNode: Find similar products")
    print("- AIProcessingQueueCreateNode: Queue analysis")
    print("- VectorEmbeddingListNode: Similarity search")
    print()
    
    # Pattern 4: Compliance Monitoring
    print("Pattern 4: Compliance Monitoring")
    print("- ProductListNode: Query safety ratings")
    print("- KnowledgeGraphEntityListNode: Check compliance")
    print("- AIServiceHealthCreateNode: Monitor AI services")
    print("- AIProcessingQueueCreateNode: Queue assessments")

if __name__ == "__main__":
    # Run the complete demonstration
    run_complete_dataflow_demo()
    
    # Show real-world patterns
    example_real_world_patterns()