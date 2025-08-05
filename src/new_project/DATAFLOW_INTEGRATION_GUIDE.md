# DataFlow Integration Guide for Hybrid AI Architecture

## 🎯 Overview

This guide demonstrates how to integrate DataFlow's zero-config database framework with your existing hybrid AI architecture. DataFlow provides automatic node generation for seamless database operations while maintaining compatibility with your Neo4j, ChromaDB, and OpenAI services.

## 🏗️ Architecture Integration

### DataFlow Position in Your Stack

```
┌─────────────────────────────────────────────────┐
│                 User Interface                  │
├─────────────────────────────────────────────────┤
│              Nexus API Gateway                  │
├─────────────────────────────────────────────────┤
│                 Business Logic                  │
│  ┌─────────────────┐  ┌─────────────────────────┐│
│  │ DataFlow Models │  │   AI Service Layer      ││
│  │ (Auto-Generated │  │                         ││
│  │    9 Nodes)     │  │ • OpenAI Integration    ││
│  │                 │  │ • Neo4j Knowledge Graph ││
│  │ • Product       │  │ • ChromaDB Vectors      ││
│  │ • Vendor        │  │ • Hybrid Recommendations││
│  │ • Classification│  │                         ││
│  └─────┬───────────┘  └─────────────────────────┘│
├─────────┼───────────────────────────────────────────┤
│         │            Data Layer                    │
│  ┌─────▼───────────┐  ┌─────────────────────────┐│
│  │ PostgreSQL      │  │   External AI Services  ││
│  │ (DataFlow)      │  │                         ││
│  │                 │  │ • Neo4j Database        ││
│  │ • Products      │  │ • ChromaDB Collections  ││
│  │ • Vendors       │  │ • OpenAI API           ││
│  │ • Classifications│ │ • Vector Embeddings     ││
│  │ • AI Tracking   │  │                         ││
│  └─────────────────┘  └─────────────────────────┘│
└─────────────────────────────────────────────────┘
```

## 🚀 Quick Start Integration

### 1. Install DataFlow

```bash
pip install kailash[dataflow]
# or
pip install kailash-dataflow
```

### 2. Initialize DataFlow with Your Database

```python
from dataflow import DataFlow

# Zero-config initialization (detects PostgreSQL from environment)
db = DataFlow()

# Or explicit PostgreSQL configuration
db = DataFlow(
    database_url="postgresql://user:pass@localhost:5432/your_db",
    pool_size=20,
    pool_max_overflow=30,
    monitoring=True,
    auto_migrate=True
)
```

### 3. Define Your First Model

```python
@db.model
class Product:
    """Automatically generates 9 node types for zero-config operations"""
    product_code: str
    name: str
    description: str
    category: str
    brand: str
    list_price: float
    
    # AI integration fields
    embedding_status: str = "pending"
    knowledge_graph_id: Optional[str] = None
    ai_tags: Optional[list] = None
    
    __dataflow__ = {
        'multi_tenant': True,      # Automatic multi-tenancy
        'soft_delete': True,       # Soft delete capability
        'audit_log': True,         # Full audit trail
        'versioned': True          # Version control
    }
```

**Result**: Automatically generates these 9 nodes:
- `ProductCreateNode` - Single create operations
- `ProductReadNode` - Single read by ID
- `ProductUpdateNode` - Single update operations
- `ProductDeleteNode` - Single delete operations
- `ProductListNode` - Query with filters/sorting
- `ProductBulkCreateNode` - Bulk insert operations
- `ProductBulkUpdateNode` - Bulk update operations
- `ProductBulkDeleteNode` - Bulk delete operations
- `ProductBulkUpsertNode` - Bulk upsert operations

## 📊 Integration with Existing Services

### Connecting to Your OpenAI Service

```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

def integrate_openai_recommendations(product_data: dict):
    """Integrate DataFlow with your existing OpenAI service"""
    workflow = WorkflowBuilder()
    
    # 1. Create product using auto-generated node
    workflow.add_node("ProductCreateNode", "create_product", product_data)
    
    # 2. Create AI recommendation request
    workflow.add_node("AIRecommendationCreateNode", "create_ai_request", {
        "recommendation_type": "product_analysis",
        "context_data": product_data,
        "ai_model": "gpt-4",
        "status": "processing"
    })
    
    # 3. Your existing OpenAI service integration
    # (This would call your existing OpenAIIntegrationService)
    
    # Connect nodes
    workflow.add_connection("create_product", "id", "create_ai_request", "entity_id")
    
    runtime = LocalRuntime()
    return runtime.execute(workflow.build())
```

### Connecting to Your Neo4j Knowledge Graph

```python
def integrate_knowledge_graph(product_id: int):
    """Integrate DataFlow with your existing Neo4j service"""
    workflow = WorkflowBuilder()
    
    # 1. Get product data
    workflow.add_node("ProductReadNode", "get_product", {"id": product_id})
    
    # 2. Create knowledge graph tracking
    workflow.add_node("KnowledgeGraphEntityCreateNode", "create_kg_entity", {
        "entity_type": "product",
        "entity_id": product_id,
        "neo4j_labels": ["Product", "Tool"],
        "sync_status": "pending"
    })
    
    # 3. Your existing Neo4j service integration
    # (This would call your existing KnowledgeGraphService)
    
    runtime = LocalRuntime()
    return runtime.execute(workflow.build())
```

### Connecting to Your ChromaDB Vector Database

```python
def integrate_vector_embeddings(product_id: int):
    """Integrate DataFlow with your existing ChromaDB service"""
    workflow = WorkflowBuilder()
    
    # 1. Create vector embedding tracking
    workflow.add_node("VectorEmbeddingCreateNode", "create_embedding", {
        "entity_type": "product",
        "entity_id": product_id,
        "collection_name": "products",
        "embedding_model": "text-embedding-ada-002",
        "embedding_status": "pending"
    })
    
    # 2. Your existing ChromaDB service integration
    # (This would call your existing VectorDatabaseService)
    
    runtime = LocalRuntime()
    return runtime.execute(workflow.build())
```

## 🔄 Migration from Existing Models

### From Standalone Classes to DataFlow Models

**Before (Your current approach):**
```python
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price
    
    def save_to_db(self):
        # Manual database code
        pass
    
    def find_similar(self):
        # Manual similarity logic
        pass
```

**After (DataFlow integration):**
```python
@db.model
class Product:
    name: str
    price: float
    embedding_status: str = "pending"
    
    # Automatic features:
    # - 9 auto-generated nodes
    # - Multi-tenancy
    # - Audit logging
    # - Soft deletes
    # - Version control
```

**Usage:**
```python
# Create product using auto-generated node
workflow.add_node("ProductCreateNode", "create", {"name": "Tool", "price": 99.99})

# Find similar products using auto-generated node with AI integration
workflow.add_node("ProductListNode", "find_similar", {
    "filter": {"embedding_status": "completed"},
    "ai_similarity_search": True,
    "similarity_threshold": 0.8
})
```

## 🎯 Advanced Integration Patterns

### 1. Hybrid AI Recommendation Pipeline

```python
def hybrid_recommendation_pipeline(user_requirements: dict):
    """Complete AI recommendation using all services"""
    workflow = WorkflowBuilder()
    
    # DataFlow: Create recommendation request
    workflow.add_node("AIRecommendationCreateNode", "create_request", {
        "recommendation_type": "hybrid",
        "context_data": user_requirements
    })
    
    # DataFlow: Find candidate products
    workflow.add_node("ProductListNode", "find_candidates", {
        "filter": {
            "category": user_requirements.get("category"),
            "price_range": user_requirements.get("budget"),
            "is_available": True
        },
        "limit": 50
    })
    
    # DataFlow: Track AI processing
    workflow.add_node("AIProcessingQueueCreateNode", "queue_ai_processing", {
        "task_type": "hybrid_recommendation",
        "ai_service": "hybrid",
        "processing_config": {
            "use_openai": True,
            "use_neo4j": True,
            "use_chromadb": True
        }
    })
    
    # Your existing AI services would process the queue
    # Results stored back in DataFlow for tracking
    
    runtime = LocalRuntime()
    return runtime.execute(workflow.build())
```

### 2. Product Intelligence Workflow

```python
def product_intelligence_workflow(product_data: dict):
    """Complete product onboarding with AI"""
    workflow = WorkflowBuilder()
    
    # 1. Create product
    workflow.add_node("ProductCreateNode", "create", product_data)
    
    # 2. Queue for UNSPSC classification
    workflow.add_node("AIProcessingQueueCreateNode", "queue_classification", {
        "task_type": "classification",
        "ai_service": "openai",
        "processing_config": {"classification_type": "unspsc"}
    })
    
    # 3. Queue for vector embedding
    workflow.add_node("AIProcessingQueueCreateNode", "queue_embedding", {
        "task_type": "embedding",
        "ai_service": "chromadb",
        "processing_config": {"collection": "products"}
    })
    
    # 4. Queue for knowledge graph
    workflow.add_node("AIProcessingQueueCreateNode", "queue_knowledge_graph", {
        "task_type": "knowledge_graph",
        "ai_service": "neo4j",
        "processing_config": {"create_relationships": True}
    })
    
    # Connect product ID to all AI processing tasks
    workflow.add_connection("create", "id", "queue_classification", "entity_id")
    workflow.add_connection("create", "id", "queue_embedding", "entity_id")
    workflow.add_connection("create", "id", "queue_knowledge_graph", "entity_id")
    
    runtime = LocalRuntime()
    return runtime.execute(workflow.build())
```

## 📈 Performance Optimization

### Bulk Operations for High Throughput

```python
def optimize_bulk_processing(products: List[dict]):
    """High-performance bulk operations"""
    workflow = WorkflowBuilder()
    
    # Bulk create with optimal batch size
    workflow.add_node("ProductBulkCreateNode", "bulk_create", {
        "data": products,
        "batch_size": 1000,  # Optimized for PostgreSQL
        "conflict_resolution": "upsert"
    })
    
    # Bulk queue AI processing
    ai_tasks = [
        {
            "task_type": "embedding",
            "entity_type": "product",
            "ai_service": "chromadb"
        }
        for _ in products
    ]
    
    workflow.add_node("AIProcessingQueueBulkCreateNode", "bulk_queue_ai", {
        "data": ai_tasks,
        "batch_size": 100
    })
    
    runtime = LocalRuntime()
    return runtime.execute(workflow.build())
```

### Query Optimization

```python
def optimized_product_search(filters: dict):
    """Optimized search using DataFlow indexes"""
    workflow = WorkflowBuilder()
    
    # Uses automatically created indexes
    workflow.add_node("ProductListNode", "search", {
        "filter": {
            "category": filters["category"],        # Uses category index
            "brand": filters["brand"],              # Uses brand index
            "price_range": filters["price_range"], # Uses price index
            "embedding_status": "completed",       # Uses embedding index
            "is_available": True                   # Uses availability index
        },
        "order_by": ["-safety_rating", "price"],   # Uses compound index
        "limit": 20
    })
    
    runtime = LocalRuntime()
    return runtime.execute(workflow.build())
```

## 🔐 Enterprise Features

### Multi-Tenancy Integration

```python
@db.model
class Product:
    name: str
    price: float
    
    __dataflow__ = {
        'multi_tenant': True  # Automatic tenant isolation
    }

# Usage - tenant automatically handled
workflow.add_node("ProductCreateNode", "create", {
    "name": "Tool",
    "price": 99.99,
    "tenant_id": "company-123"  # Automatic isolation
})

# Queries automatically filtered by tenant
workflow.add_node("ProductListNode", "list", {
    "filter": {"category": "tools"},
    "tenant_id": "company-123"  # Only sees company-123 products
})
```

### Audit Trail Integration

```python
# Automatic audit logging for all operations
@db.model
class Product:
    name: str
    price: float
    
    __dataflow__ = {
        'audit_log': True  # Automatic audit trail
    }

# All operations automatically logged:
# - Who made the change
# - When it was made
# - What changed (old/new values)
# - IP address and session info
```

## 🚨 Error Handling & Monitoring

### AI Service Health Monitoring

```python
def monitor_ai_services():
    """Monitor all AI services health"""
    workflow = WorkflowBuilder()
    
    # Create health check records
    workflow.add_node("AIServiceHealthBulkCreateNode", "health_checks", {
        "data": [
            {"service_name": "openai", "endpoint": "api.openai.com"},
            {"service_name": "neo4j", "endpoint": "localhost:7687"},
            {"service_name": "chromadb", "endpoint": "localhost:8000"}
        ]
    })
    
    # Get recent health trends
    workflow.add_node("AIServiceHealthListNode", "recent_health", {
        "filter": {
            "check_timestamp": {"$gte": datetime.now() - timedelta(hours=1)}
        },
        "order_by": ["-check_timestamp"]
    })
    
    runtime = LocalRuntime()
    return runtime.execute(workflow.build())
```

## 🎭 Development vs Production

### Development Setup

```python
# SQLite for development (zero config)
db = DataFlow()  # Automatically uses SQLite

# Mock AI services for development
@db.model
class Product:
    name: str
    embedding_status: str = "mock"
```

### Production Setup

```python
# PostgreSQL for production
db = DataFlow(
    database_url=os.getenv("DATABASE_URL"),
    pool_size=25,
    pool_max_overflow=50,
    monitoring=True,
    auto_migrate=False  # Control migrations in production
)

# Real AI service integration
@db.model
class Product:
    name: str
    embedding_status: str = "pending"
    
    __dataflow__ = {
        'multi_tenant': True,
        'audit_log': True,
        'monitoring': True
    }
```

## 🧪 Testing Integration

### Unit Testing with DataFlow

```python
import pytest
from dataflow import DataFlow

@pytest.fixture
def test_db():
    """Test database fixture"""
    return DataFlow(":memory:")  # In-memory SQLite for tests

def test_product_creation(test_db):
    """Test product creation workflow"""
    workflow = WorkflowBuilder()
    
    workflow.add_node("ProductCreateNode", "create", {
        "name": "Test Product",
        "price": 99.99
    })
    
    runtime = LocalRuntime()
    results, run_id = runtime.execute(workflow.build())
    
    assert results["create"]["name"] == "Test Product"
    assert results["create"]["price"] == 99.99
```

## 🏆 Best Practices

### 1. Model Design
- Use type hints for automatic validation
- Include AI integration fields from the start
- Enable enterprise features in `__dataflow__`
- Design indexes for your query patterns

### 2. Workflow Patterns
- Use bulk operations for >100 records
- Connect nodes for data flow
- Handle errors gracefully
- Monitor AI service health

### 3. Performance
- Configure connection pooling appropriately
- Use compound indexes for complex queries
- Batch AI processing operations
- Monitor and optimize query performance

### 4. Security
- Enable audit logging in production
- Use multi-tenancy for SaaS applications
- Monitor AI service access
- Implement proper access controls

## 🎯 Next Steps

1. **Start Small**: Begin with one model (e.g., Product)
2. **Add AI Integration**: Gradually add AI service connections
3. **Enable Enterprise Features**: Turn on multi-tenancy, audit logs
4. **Optimize Performance**: Tune connection pools and indexes
5. **Monitor & Scale**: Use health monitoring and performance metrics

## 📞 Support & Resources

- **DataFlow Documentation**: [Link to docs]
- **AI Integration Examples**: See `dataflow_ai_workflows.py`
- **Performance Demo**: Run `dataflow_zero_config_demo.py`
- **Community**: [Discord/Slack link]

---

**Key Takeaway**: DataFlow provides zero-config database operations while maintaining full compatibility with your existing AI services. Each `@db.model` automatically generates 9 nodes, eliminating boilerplate code while providing enterprise-grade features out of the box.