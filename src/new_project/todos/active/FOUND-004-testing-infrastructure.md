# FOUND-004: Testing Infrastructure - 3-Tier Strategy

**Created:** 2025-08-01  
**Assigned:** Testing Specialist  
**Priority:** 🔥 High  
**Status:** Not Started  
**Estimated Effort:** 8 hours  
**Due Date:** 2025-08-03

## Description

Establish comprehensive 3-tier testing strategy with real infrastructure for the AI knowledge-based assistance system. This includes unit tests, integration tests with real databases, and end-to-end performance validation with realistic data volumes.

## Acceptance Criteria

- [ ] Tier 1 (Unit): All algorithms and components tested in isolation
- [ ] Tier 2 (Integration): Real PostgreSQL, Neo4j, and ChromaDB connections tested
- [ ] Tier 3 (E2E): Full system performance validated with realistic data loads
- [ ] Docker test environment configured for consistent testing
- [ ] CI/CD pipeline integration prepared
- [ ] Performance benchmarks established for <2s response requirement
- [ ] Test data generation utilities created
- [ ] Safety compliance testing framework established

## Subtasks

- [ ] Docker Test Environment Setup (Est: 2h)
  - Verification: PostgreSQL, Neo4j, ChromaDB containers with test data
  - Output: docker-compose.test.yml with all required services
- [ ] Unit Test Framework (Est: 2h)
  - Verification: Pytest configuration with coverage reporting
  - Output: Test structure for nodes, models, and algorithms
- [ ] Integration Test Infrastructure (Est: 2h)
  - Verification: Real database connections and data flow validation
  - Output: Integration tests for DataFlow, Neo4j, and vector operations
- [ ] Performance Test Framework (Est: 1.5h)
  - Verification: Load testing with realistic data volumes
  - Output: Performance benchmarks and monitoring tools
- [ ] Test Data Generation (Est: 0.5h)
  - Verification: Utilities to generate realistic product, user, and safety data
  - Output: Data factories and fixtures for all test tiers

## Dependencies

- Docker environment for containerized testing
- Access to test databases (PostgreSQL, Neo4j, ChromaDB)
- Integration with existing test structure in tests/ directory

## Risk Assessment

- **MEDIUM**: Real database testing may be slower than mocked tests
- **MEDIUM**: Performance testing requires significant test data generation
- **LOW**: Docker environment setup may have platform-specific issues
- **LOW**: CI/CD integration may require additional configuration

## Testing Architecture

### Tier 1: Unit Tests (Isolated)
```python
# Test individual components without external dependencies
tests/unit/
├── test_recommendation_engine.py
├── test_safety_compliance.py
├── test_classification_system.py
├── test_dataflow_models.py
└── test_embedding_pipeline.py
```

### Tier 2: Integration Tests (Real Services)
```python
# Test with real database connections
tests/integration/
├── test_postgresql_operations.py
├── test_neo4j_knowledge_graph.py
├── test_chromadb_vector_search.py
├── test_openai_integration.py
└── test_multi_database_workflows.py
```

### Tier 3: End-to-End Tests (Full System)
```python
# Test complete recommendation workflows
tests/e2e/
├── test_recommendation_pipeline.py
├── test_performance_benchmarks.py
├── test_safety_compliance_workflows.py
└── test_multi_channel_deployment.py
```

## Docker Test Environment

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  postgres-test:
    image: postgres:15
    environment:
      POSTGRES_DB: horme_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5433:5432"
    volumes:
      - ./test-data/postgres:/docker-entrypoint-initdb.d

  neo4j-test:
    image: neo4j:5.3
    environment:
      NEO4J_AUTH: neo4j/test_password
      NEO4J_PLUGINS: '["apoc"]'
    ports:
      - "7475:7474"
      - "7688:7687"
    volumes:
      - ./test-data/neo4j:/var/lib/neo4j/import

  chromadb-test:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - ./test-data/chromadb:/chroma/chroma
```

## Performance Benchmarks

### Response Time Requirements
- Product search: < 500ms
- Recommendation generation: < 2s
- Safety compliance check: < 1s
- Knowledge graph queries: < 800ms
- Vector similarity search: < 300ms

### Load Testing Targets
- Concurrent users: 100
- Requests per second: 50
- Database records: 100k products, 10k users, 1M safety rules
- Vector embeddings: 100k product embeddings

## Test Data Generation

### Product Data Factory
```python
class ProductDataFactory:
    @staticmethod
    def create_products(count: int) -> List[Product]:
        """Generate realistic product data with UNSPSC codes"""
        
    @staticmethod
    def create_safety_standards(count: int) -> List[SafetyStandard]:
        """Generate OSHA/ANSI safety standards"""
        
    @staticmethod
    def create_user_profiles(count: int) -> List[UserProfile]:
        """Generate user profiles with skill assessments"""
```

### Knowledge Graph Test Data
```cypher
// Generate tool-to-task relationships
CREATE (drill:Tool {name: 'Cordless Drill', category: 'Power Tools'})
CREATE (hole:Task {name: 'Drill Hole', complexity: 'beginner'})
CREATE (drill)-[:USED_FOR]->(hole)
```

## Testing Requirements

### Unit Tests (Tier 1)
- [ ] Recommendation algorithm accuracy (precision/recall)
- [ ] Safety rule engine correctness
- [ ] Classification system hierarchy traversal
- [ ] DataFlow model validation
- [ ] Embedding generation quality

### Integration Tests (Tier 2)
- [ ] PostgreSQL CRUD operations with DataFlow
- [ ] Neo4j knowledge graph queries and updates
- [ ] ChromaDB vector search and indexing
- [ ] OpenAI API integration and error handling
- [ ] Multi-database transaction consistency

### E2E Tests (Tier 3)
- [ ] Complete recommendation workflow performance
- [ ] Safety compliance validation workflow
- [ ] User skill assessment and personalization
- [ ] Multi-channel deployment (API/CLI/MCP)
- [ ] Stress testing with production-like load

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: AI System Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/ --cov=src/ --cov-report=xml
```

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Docker test environment running successfully
- [ ] All three test tiers implemented and passing
- [ ] Performance benchmarks established and documented
- [ ] Test data generation utilities created and validated
- [ ] CI/CD pipeline configured and tested
- [ ] Test documentation completed

## Implementation Files

- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\tests\` (extend existing structure)
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\docker-compose.test.yml`
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\test-data\` (test data fixtures)
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\tests\` (project-specific tests)

## Notes

- Follow existing test patterns in the codebase
- Use real infrastructure for Tier 2/3 tests (NO MOCKING for databases)
- Ensure test isolation and cleanup between test runs
- Performance tests should simulate realistic user behavior
- Safety compliance tests must validate legal accuracy

## Progress Log

**2025-08-01:** Task created with comprehensive 3-tier testing strategy aligned with Kailash SDK best practices