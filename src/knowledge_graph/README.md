# Horme Knowledge Graph System

A comprehensive semantic knowledge graph implementation for product relationships, intelligent search, and AI-powered recommendations.

## 🏗️ Architecture Overview

The knowledge graph system consists of multiple integrated components:

### Core Components

1. **Neo4j Graph Database** - Stores product nodes and semantic relationships
2. **ChromaDB Vector Store** - Handles embeddings for semantic search  
3. **PostgreSQL Integration** - Syncs with existing DataFlow models
4. **AI Inference Engine** - Generates relationships using ML algorithms
5. **Semantic Search Engine** - Multi-strategy search with embeddings
6. **FastAPI REST API** - Provides HTTP endpoints for all operations
7. **DataFlow Integration** - Workflow nodes for Kailash DataFlow

### Data Flow

```
PostgreSQL (DataFlow) → Migration Scripts → Neo4j Knowledge Graph
                                              ↓
ChromaDB Vector Embeddings ← Semantic Search Engine → FastAPI API
                                              ↓
AI Inference Engine → Product Relationships → Recommendations
```

## 🚀 Quick Start

### 1. Start the Infrastructure

```bash
# Start Neo4j, ChromaDB, and Redis
cd src/knowledge_graph
docker-compose -f docker-compose.neo4j.yml up -d
```

### 2. Set Environment Variables

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j" 
export NEO4J_PASSWORD="horme_knowledge_2024"
export POSTGRES_URL="postgresql://horme_user:horme_password_2024@localhost:5432/horme_database"
export OPENAI_API_KEY="your-openai-api-key"
export REDIS_URL="redis://:horme_redis_2024@localhost:6380/0"
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize the Knowledge Graph

```python
from knowledge_graph import Neo4jConnection, GraphDatabase
from knowledge_graph.integration import PostgreSQLIntegration

# Initialize connections
neo4j_conn = Neo4jConnection()
graph_db = GraphDatabase(neo4j_conn)

# Run initial data migration
postgres_integration = PostgreSQLIntegration(neo4j_connection=neo4j_conn)
await postgres_integration.migrate_all()

print("Knowledge graph initialized!")
```

### 5. Start the API Server

```bash
# Start the FastAPI server
python -m uvicorn knowledge_graph.api:app --reload --port 8001
```

Visit `http://localhost:8001/docs` for the interactive API documentation.

## 📊 Data Models

### Product Node
```python
@dataclass
class ProductNode:
    product_id: int
    sku: str
    name: str
    brand_name: str
    category_name: str
    price: float
    specifications: Dict[str, Any]
    features: List[str]
    keywords: List[str]
    # ... additional fields
```

### Relationship Types
```python
class RelationshipType(Enum):
    COMPATIBLE_WITH = "COMPATIBLE_WITH"           # Battery/tool compatibility
    REQUIRES = "REQUIRES"                         # Hard dependencies  
    ALTERNATIVE_TO = "ALTERNATIVE_TO"             # Substitute products
    USED_FOR = "USED_FOR"                        # Usage contexts
    SAME_BRAND_ECOSYSTEM = "SAME_BRAND_ECOSYSTEM" # Brand system compatibility
    NEEDED_FOR_PROJECT = "NEEDED_FOR_PROJECT"     # DIY project requirements
    UPGRADED_BY = "UPGRADED_BY"                   # Product upgrades
    ACCESSORY_FOR = "ACCESSORY_FOR"              # Accessories and add-ons
```

### Semantic Relationship
```python
@dataclass
class SemanticRelationship:
    from_product_id: int
    to_product_id: int
    relationship_type: RelationshipType
    confidence: float                    # 0.0 to 1.0
    source: ConfidenceSource            # AI, manual, manufacturer, etc.
    compatibility_type: str             # battery_system, voltage, etc.
    notes: str
    evidence: List[str]                 # Supporting evidence
    created_at: datetime
```

## 🔍 Search Capabilities

### 1. Semantic Search
```python
from knowledge_graph.search import SemanticSearchEngine

search_engine = SemanticSearchEngine(neo4j_conn)

# Natural language search
results = await search_engine.search(
    query="18V cordless drill with hammer function",
    limit=20,
    search_strategy="hybrid"  # semantic + text + graph
)

for result in results:
    print(f"{result.name} - Score: {result.combined_score:.2f}")
```

### 2. Compatibility Search
```python
# Find products compatible with a specific item
compatible = await search_engine.find_compatible_products(
    product_id=12345,
    compatibility_types=["battery_system", "voltage_compatibility"]
)

print(f"Found {len(compatible)} compatible products")
```

### 3. Project Recommendations
```python
# Get recommendations for DIY projects
recommendations = await search_engine.recommend_for_project(
    project_description="bathroom renovation with tile work",
    budget_range="medium",
    skill_level="intermediate"
)

for category, products in recommendations.items():
    print(f"{category}: {len(products)} recommended products")
```

## 🤖 AI-Powered Relationship Inference

### Inference Rules
The system uses multiple algorithms to infer product relationships:

1. **Brand Ecosystem Analysis** - Same brand, compatible battery systems
2. **Specification Matching** - Voltage, size, technical compatibility  
3. **Semantic Similarity** - NLP analysis of descriptions and features
4. **Usage Pattern Analysis** - Project requirements and tool combinations
5. **Alternative Detection** - Similar function, different brands

### Running Inference
```python
from knowledge_graph.inference import RelationshipInferenceEngine

inference_engine = RelationshipInferenceEngine(neo4j_conn, openai_api_key="...")

# Run comprehensive relationship inference
results = await inference_engine.infer_all_relationships(
    batch_size=500,
    min_confidence=0.6
)

print(f"Created relationships: {results}")
# Output: {'COMPATIBLE_WITH': 1250, 'ALTERNATIVE_TO': 890, ...}
```

### Confidence Scoring
Each relationship includes a confidence score (0.0-1.0) based on:
- **Source reliability** (manufacturer spec = 1.0, AI inference = 0.7)
- **Evidence strength** (multiple supporting factors increase confidence)
- **User validation** (feedback adjusts confidence over time)

## 🌐 REST API Usage

### Product Search
```bash
curl -X POST "http://localhost:8001/search/products" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tools for bathroom renovation",
    "limit": 10,
    "search_strategy": "hybrid",
    "min_similarity": 0.6
  }'
```

### Compatibility Check
```bash
curl -X POST "http://localhost:8001/search/compatibility" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 12345,
    "compatibility_types": ["battery_system"],
    "limit": 5
  }'
```

### Project Recommendations
```bash
curl -X POST "http://localhost:8001/search/project-recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "project_description": "build a deck",
    "budget_range": "medium",
    "skill_level": "intermediate",
    "limit": 15
  }'
```

### Data Management
```bash
# Migrate data from PostgreSQL
curl -X POST "http://localhost:8001/data/migrate" \
  -H "Content-Type: application/json" \
  -d '{
    "force_refresh": false,
    "entity_types": ["products", "categories", "brands"]
  }'

# Run relationship inference
curl -X POST "http://localhost:8001/inference/relationships" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_size": 500,
    "min_confidence": 0.6
  }'
```

## 🔧 DataFlow Integration

### Using Knowledge Graph Nodes in Workflows

```python
from knowledge_graph.dataflow_integration import KnowledgeGraphWorkflows

workflows = KnowledgeGraphWorkflows()

# Execute product discovery workflow
results = workflows.execute_product_discovery(
    search_query="cordless drill for deck building"
)

print("Search Results:", results['search_results'])
print("Compatible Products:", results['compatible_products'])
print("Project Recommendations:", results['project_recommendations'])
```

### Custom Workflow Example
```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from knowledge_graph.dataflow_integration import KnowledgeGraphDataFlowNodes

# Initialize DataFlow nodes
kg_nodes = KnowledgeGraphDataFlowNodes()
workflow = WorkflowBuilder()

# Add semantic search node
workflow.add_node(
    "SemanticSearchNode",
    "search_products", 
    {
        "function": kg_nodes.semantic_search_node,
        "query": "power tools for construction",
        "limit": 20,
        "search_strategy": "hybrid"
    }
)

# Add compatibility analysis
workflow.add_node(
    "CompatibilityNode",
    "find_compatibility",
    {
        "function": kg_nodes.compatibility_search_node,
        "product_id": 12345,
        "limit": 10
    }
)

# Execute workflow
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())
```

## 📈 Performance and Scaling

### Query Optimization
- **Indexed Properties**: SKU, product_id, brand_name, category_name
- **Full-text Search**: Product names, descriptions, features
- **Graph Algorithms**: Shortest path, centrality analysis
- **Caching**: Redis cache for frequent queries and embeddings

### Batch Processing
- **Data Migration**: Processes 1000+ products per batch
- **Relationship Inference**: Configurable batch sizes (500-2000 products)
- **Vector Indexing**: Parallel embedding generation and storage

### Monitoring
```python
# Health check
response = requests.get("http://localhost:8001/health")
print(response.json())

# Graph statistics  
response = requests.get("http://localhost:8001/stats")
stats = response.json()
print(f"Products: {stats['node_counts']['Product']}")
print(f"Relationships: {stats['relationship_counts']['COMPATIBLE_WITH']}")
```

## 🔄 Data Synchronization

### Automatic Sync
```python
from knowledge_graph.integration import PostgreSQLIntegration

# Set up continuous sync (checks for updates every hour)
integration = PostgreSQLIntegration()

# Sync only recently updated entities
results = await integration.migrate_all(force_refresh=False)
print(f"Synced: {results}")
```

### Manual Sync Operations
```python
# Force full refresh of all data
await integration.migrate_categories(force_refresh=True)
await integration.migrate_brands(force_refresh=True) 
await integration.migrate_products(force_refresh=True)

# Check sync status
status = await integration.get_sync_status()
print("Sync Status:", status)
```

## 🧪 Testing and Validation

### Unit Tests
```bash
# Run knowledge graph tests
python -m pytest src/knowledge_graph/tests/ -v
```

### Integration Tests
```bash
# Test with real Neo4j instance
python -m pytest src/knowledge_graph/tests/integration/ -v

# Test API endpoints
python -m pytest src/knowledge_graph/tests/api/ -v
```

### Manual Testing
```python
# Test semantic search
search_engine = SemanticSearchEngine(neo4j_conn)
results = await search_engine.search("drill bits for masonry")
assert len(results) > 0
assert results[0].combined_score > 0.7

# Test relationship inference
inference_engine = RelationshipInferenceEngine(neo4j_conn)
relationships = await inference_engine.infer_product_relationships(product_id=123)
assert len(relationships) > 0
```

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build and deploy the full stack
docker-compose -f docker-compose.neo4j.yml up -d

# Scale the API service
docker-compose up --scale knowledge-api=3
```

### Environment Configuration
```bash
# Production settings
export NEO4J_URI="bolt://neo4j-cluster:7687"
export POSTGRES_URL="postgresql://readonly_user:password@postgres-replica:5432/horme_db"
export CHROMADB_HOST="chromadb-cluster"
export REDIS_URL="redis://redis-cluster:6379/0"
export OPENAI_API_KEY="prod-openai-key"
```

### Monitoring and Alerts
- **Health Checks**: Automated endpoint monitoring
- **Performance Metrics**: Query latency, cache hit rates
- **Data Quality**: Relationship confidence distributions
- **System Resources**: Memory usage, connection pools

## 🔐 Security Considerations

### Authentication
- Neo4j authentication with strong passwords
- API key authentication for OpenAI services
- Redis authentication for cache access

### Data Privacy
- No PII stored in knowledge graph
- Product data only (names, specs, relationships)
- Audit logging for relationship modifications

### Network Security
- Internal network communication only
- HTTPS/TLS for external API access
- Container network isolation

## 📚 Additional Resources

### Documentation
- [Neo4j Cypher Query Language](https://neo4j.com/docs/cypher-manual/)
- [ChromaDB Vector Database](https://docs.trychroma.com/)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [Kailash DataFlow Documentation](../../sdk-users/)

### Examples
- [Complete workflow examples](./examples/)
- [API usage examples](./examples/api_examples.py)
- [Custom inference rules](./examples/custom_inference.py)

### Support
- Check the [troubleshooting guide](./TROUBLESHOOTING.md)
- Review [performance tuning tips](./PERFORMANCE.md)
- Submit issues on the project repository

---

## 🎯 Key Features Summary

✅ **Semantic Product Search** - Natural language queries with AI-powered understanding  
✅ **Intelligent Compatibility Detection** - Brand ecosystems and technical compatibility  
✅ **DIY Project Recommendations** - Context-aware tool and material suggestions  
✅ **Real-time Data Sync** - Automatic PostgreSQL to Neo4j synchronization  
✅ **AI Relationship Inference** - Machine learning-powered relationship discovery  
✅ **Multi-strategy Search** - Hybrid semantic, text, and graph-based search  
✅ **DataFlow Integration** - Native Kailash workflow node support  
✅ **REST API** - Complete HTTP API with OpenAPI documentation  
✅ **Production Ready** - Docker deployment, monitoring, and scaling support

The knowledge graph system transforms static product catalogs into intelligent, interconnected networks that understand product relationships and user intent, enabling next-generation e-commerce experiences.