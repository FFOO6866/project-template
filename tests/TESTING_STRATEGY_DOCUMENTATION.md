# Horme POV - 3-Tier Testing Strategy with Real Infrastructure

## Overview

This document outlines the comprehensive 3-tier testing strategy implemented for the Horme POV project, following SDK-compliant patterns with **NO MOCKING** in Tiers 2 and 3. All tests use real infrastructure to ensure production readiness.

## 🎯 Testing Philosophy

### Core Principles
1. **NO MOCKING in Integration/E2E Tests**: Tiers 2 and 3 use REAL services only
2. **Performance SLA Compliance**: Strict timing requirements for each tier
3. **Real Infrastructure Validation**: All tests run against actual Docker services
4. **SDK Compliance**: All workflows follow Kailash SDK patterns with `runtime.execute(workflow.build())`

### SLA Targets

| Tier | Max Execution Time | Infrastructure | Mocking Policy |
|------|-------------------|----------------|----------------|
| Tier 1: Unit | <1 second | None required | Allowed (minimal) |
| Tier 2: Integration | <5 seconds | Docker services | **NO MOCKING** |
| Tier 3: End-to-End | <10 seconds | Full stack | **NO MOCKING** |
| Performance | <60 seconds | Full stack | **NO MOCKING** |

## 🏗️ Infrastructure Requirements

### Required Docker Services

The testing strategy requires the following real services running via Docker:

```yaml
# From tests/utils/docker-compose.test.yml
services:
  postgres:    # Port 5434 - PostgreSQL with pgvector
  redis:       # Port 6380 - Redis cache
  minio:       # Port 9001 - Object storage
  mysql:       # Port 3307 - MySQL database
  mongodb:     # Port 27017 - MongoDB
  ollama:      # Port 11435 - AI services
```

### Infrastructure Setup Commands

```bash
# Start test infrastructure
cd tests/utils
./test-env setup

# Check service status
./test-env status

# Run specific tier tests
./test-env test tier1    # Unit tests
./test-env test tier2    # Integration tests  
./test-env test tier3    # End-to-end tests

# Stop infrastructure
./test-env stop
```

## 📋 Tier 1: Unit Tests

### Characteristics
- **Target**: <1 second execution per test
- **Scope**: Individual node and function testing
- **Infrastructure**: None required
- **Mocking**: Limited mocking allowed for external services only
- **Focus**: SDK workflow node functionality

### Test Structure
```python
@test_timeout
def test_query_processor_node_basic_functionality(self, runtime):
    """Test query processor node with valid inputs"""
    workflow = WorkflowBuilder()
    
    workflow.add_node("PythonCodeNode", "query_processor", {
        "code": """
        # Real implementation code - NO MOCKING
        def process_search_query(query, category, limit):
            # Actual processing logic
            return {'processed': True}
        """
    })
    
    results, run_id = runtime.execute(workflow.build(), {
        "query_processor": {"query": "test", "category": "electronics", "limit": 10}
    })
    
    assert results['query_processor']['processed'] is True
```

### Test Files
- `tests/unit/test_sdk_compliant_search_workflow.py`
- `tests/unit/test_sdk_compliant_background_processing.py`

### Performance Requirements
- Each test must complete in <1 second
- No external service dependencies
- Real implementation logic (no shortcuts)
- Memory efficient processing

## 📋 Tier 2: Integration Tests

### Characteristics  
- **Target**: <5 seconds execution per test
- **Scope**: Component interaction testing
- **Infrastructure**: **REAL Docker services required**
- **Mocking**: **ABSOLUTELY FORBIDDEN**
- **Focus**: Multi-service workflows with real data

### NO MOCKING Policy

Integration tests **MUST NOT** use:
- Mock database connections
- Fake Redis responses  
- Stubbed API calls
- Mock file operations

Instead, they **MUST** use:
- Real PostgreSQL database (Port 5434)
- Real Redis cache (Port 6380)
- Real file system operations
- Actual network calls between services

### Test Structure
```python
@test_timeout
def test_database_product_search_workflow(self, postgres_connection, runtime):
    """Test complete product search workflow with REAL database"""
    workflow = WorkflowBuilder()
    
    workflow.add_node("PythonCodeNode", "database_search", {
        "code": """
        import psycopg2
        def search_products_database(search_query, conn_params):
            # REAL database connection - NO MOCKING
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM horme.products WHERE name LIKE %s", [f"%{search_query}%"])
            results = cursor.fetchall()
            
            conn.close()
            return {'results': results}
        """
    })
    
    # Uses REAL database connection parameters
    results, run_id = runtime.execute(workflow.build(), {
        "database_search": {
            "search_query": "laptop",
            "conn_params": {
                "host": "localhost", "port": 5434,
                "database": "horme_test", "user": "test_user"
            }
        }
    })
```

### Test Files
- `tests/integration/test_real_database_integration.py`
- `tests/integration/test_document_upload_integration.py`
- `tests/integration/test_product_search_filtering.py`

### Service Integration Patterns

#### PostgreSQL Integration
```python
# ✅ CORRECT - Real database operations
conn = psycopg2.connect(host='localhost', port=5434, database='horme_test')
cursor.execute("INSERT INTO products (name) VALUES (%s)", ['Test Product'])
results = cursor.fetchall()

# ❌ WRONG - Mocking forbidden
@patch('psycopg2.connect')
def test_database(mock_conn): # FORBIDDEN in Tier 2
```

#### Redis Integration  
```python
# ✅ CORRECT - Real Redis operations
r = redis.Redis(host='localhost', port=6380)
r.set('key', 'value')
result = r.get('key')

# ❌ WRONG - Mocking forbidden
@patch('redis.Redis')
def test_cache(mock_redis): # FORBIDDEN in Tier 2
```

## 📋 Tier 3: End-to-End Tests

### Characteristics
- **Target**: <10 seconds execution per test  
- **Scope**: Complete business process validation
- **Infrastructure**: **Full Docker stack required**
- **Mocking**: **ABSOLUTELY FORBIDDEN**
- **Focus**: Real user workflows from start to finish

### Business Process Testing

E2E tests validate complete business workflows:

1. **Document Upload → Processing → Product Matching → Quotation**
2. **Search → Cache → Analytics → Reporting**  
3. **User Registration → Profile → Quotation Management**
4. **Real-time Updates → Notifications → Status Tracking**

### Test Structure
```python
@test_timeout
def test_complete_document_processing_pipeline(self, full_infrastructure, runtime):
    """Test complete upload-to-quotation business workflow"""
    workflow = WorkflowBuilder()
    
    # Step 1: Real file upload
    workflow.add_node("PythonCodeNode", "document_upload", {
        "code": """
        import os
        def process_document_upload(documents, upload_dir):
            # REAL file operations - NO MOCKING
            for doc in documents:
                file_path = os.path.join(upload_dir, doc['name'])
                with open(file_path, 'w') as f:
                    f.write(doc['content'])
            return {'uploaded': True}
        """
    })
    
    # Step 2: Real content analysis
    workflow.add_node("PythonCodeNode", "content_analysis", {
        "code": """
        def analyze_document_content(upload_result):
            # REAL content processing - NO MOCKING
            # Extract items from uploaded files
            return {'items_extracted': items}
        """
    })
    
    # Step 3: Real database product matching
    workflow.add_node("PythonCodeNode", "product_matching", {
        "code": """
        import psycopg2
        def match_items_to_products(analysis_result, postgres_params):
            # REAL database operations - NO MOCKING
            conn = psycopg2.connect(**postgres_params)
            # Match extracted items to products
            return {'matched_products': matches}
        """
    })
    
    # Step 4: Real quotation generation
    workflow.add_node("PythonCodeNode", "quotation_generation", {
        "code": """
        def generate_quotation(matching_result, postgres_params):
            # REAL quotation creation - NO MOCKING
            conn = psycopg2.connect(**postgres_params)
            # Create actual quotation in database
            return {'quotation': quotation_data}
        """
    })
```

### Test Files
- `tests/e2e/test_complete_business_workflows.py`
- `tests/e2e/test_complete_upload_workflow.py`

### Performance Requirements
- Complete business process in <10 seconds
- Real file operations with actual documents
- Real database transactions with ACID compliance
- Real-time data consistency validation

## 🚀 Performance Testing

### SLA Validation

Performance tests validate specific SLA targets:

```python
SLA_TARGETS = {
    'file_upload_processing': {
        'max_response_time_ms': 5000,  # 5 seconds
        'percentile_95_ms': 3000,      # 95% under 3 seconds
        'max_concurrent_users': 10     # Support 10 concurrent uploads
    },
    'product_search': {
        'max_response_time_ms': 500,   # 0.5 seconds
        'percentile_95_ms': 200,       # 95% under 200ms
        'max_concurrent_searches': 50  # Support 50 concurrent searches
    }
}
```

### Load Testing Patterns

```python
@test_timeout
def test_concurrent_file_upload_performance(self, runtime_pool):
    """Test concurrent file upload performance"""
    metrics = PerformanceMetrics()
    
    # Execute concurrent uploads with real infrastructure
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        
        for upload in test_uploads:
            future = executor.submit(self._execute_real_upload, upload)
            futures.append(future)
        
        for future in concurrent.futures.as_completed(futures):
            response_time_ms, success, error = future.result()
            metrics.record_response(response_time_ms, success, error)
    
    # Validate against SLA targets
    sla_validation = metrics.validate_sla(SLA_TARGETS['file_upload_processing'])
    assert sla_validation['sla_compliant']
```

### Test Files
- `tests/performance/test_sla_validation.py`

## 🔧 Test Execution

### Automated Test Runner

The complete test suite can be executed using:

```bash
# Run all tiers
python tests/run_all_tests.py

# Run specific tiers
python tests/run_all_tests.py --tiers tier1 tier2

# Skip infrastructure setup (if already running)
python tests/run_all_tests.py --skip-infrastructure

# Generate detailed report
python tests/run_all_tests.py --output-report test_results.json
```

### Manual Tier Execution

```bash
# Tier 1: Unit Tests
pytest tests/unit/ -v --timeout=1

# Tier 2: Integration Tests (requires Docker)
./tests/utils/test-env setup
pytest tests/integration/ -v --timeout=5

# Tier 3: End-to-End Tests (requires full stack)
pytest tests/e2e/ -v --timeout=10

# Performance Tests
pytest tests/performance/ -v --timeout=60
```

### CI/CD Integration

```yaml
# GitHub Actions example
name: 3-Tier Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: horme_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5434:5432
      redis:
        image: redis:7
        ports:
          - 6380:6379
    
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r tests/requirements-test.txt
      
      - name: Run 3-Tier Test Suite
        run: |
          python tests/run_all_tests.py --output-report ci_results.json
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: ci_results.json
```

## 📊 Test Reporting

### Test Execution Report

The test runner generates comprehensive reports including:

```json
{
  "execution_summary": {
    "total_duration_seconds": 45.32,
    "overall_success": true,
    "tiers_executed": 4,
    "total_failures": 0,
    "total_warnings": 1
  },
  "tier_results": {
    "tier1": {
      "success": true,
      "duration_seconds": 3.21,
      "tests_collected": 25,
      "tests_passed": 25,
      "max_test_duration": 0.85
    }
  },
  "infrastructure_status": {
    "postgres": {"status": "healthy", "port": 5434},
    "redis": {"status": "healthy", "port": 6380}
  },
  "sla_compliance": {
    "tier1_speed_compliant": true,
    "tier2_speed_compliant": true, 
    "infrastructure_healthy": true,
    "overall_compliant": true
  }
}
```

### Performance Metrics

Performance tests generate detailed metrics:

- Response time percentiles (50th, 95th, 99th)
- Throughput measurements (requests/second)
- Concurrent load handling
- Resource utilization
- SLA compliance validation

## 🚨 Troubleshooting

### Common Issues

#### Infrastructure Not Available
```bash
# Check Docker services
docker-compose -f tests/utils/docker-compose.test.yml ps

# Check service logs
docker-compose -f tests/utils/docker-compose.test.yml logs postgres

# Restart services
./tests/utils/test-env reset
```

#### Port Conflicts
```bash
# Check for port conflicts
netstat -tulpn | grep -E ':(5434|6380|9001)'

# Stop conflicting services
sudo lsof -ti:5434 | xargs sudo kill -9
```

#### Test Timeout Issues
```bash
# Run with increased timeouts for debugging
pytest tests/integration/ --timeout=30 -v -s

# Check infrastructure performance
./tests/utils/test-env status
```

### Performance Debugging

```bash
# Run performance tests with detailed output
pytest tests/performance/ -v -s --tb=long

# Profile test execution
python -m cProfile tests/run_all_tests.py --tiers tier1

# Monitor resource usage
docker stats
```

## 📈 Continuous Improvement

### Metrics Tracking

The testing strategy tracks key metrics:

- Test execution speed trends
- Infrastructure reliability
- SLA compliance rates  
- Failure patterns and root causes

### Regular Reviews

- **Weekly**: Review test execution times and SLA compliance
- **Monthly**: Assess infrastructure stability and performance trends
- **Quarterly**: Update SLA targets based on system evolution

### Future Enhancements

- Automated performance regression detection
- Dynamic test data generation
- Cross-platform testing (Windows, macOS, Linux)
- Integration with monitoring systems

## ✅ Success Criteria

A successful test suite execution requires:

1. **All tiers pass**: No test failures across any tier
2. **SLA compliance**: All timing requirements met
3. **Infrastructure health**: All Docker services operational  
4. **NO MOCKING violations**: Confirmed real infrastructure usage
5. **Performance targets**: All SLA metrics within acceptable ranges

The 3-tier testing strategy ensures that the Horme POV system is production-ready with validated performance, reliability, and business process integrity.