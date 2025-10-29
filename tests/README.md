# Horme POV - Docker-Based Test Infrastructure

## CRITICAL POLICY: Docker-Only Test Execution

**ALL TESTS MUST RUN IN DOCKER CONTAINERS - NO LOCAL PYTHON EXECUTION ALLOWED**

This project uses a comprehensive 3-tier testing strategy with real Docker services.

---

## Quick Start

### 1. Start Test Infrastructure

```bash
# Start all test services (PostgreSQL, Redis, Neo4j, etc.)
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be healthy
docker-compose -f docker-compose.test.yml logs -f
```

### 2. Run Tests in Docker

```bash
# Run ALL tests
docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/ -v

# Run specific test tiers
docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/unit/ -v
docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/integration/ -v
docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/e2e/ -v
```

### 3. Cleanup

```bash
# Stop all test services
docker-compose -f docker-compose.test.yml down

# Remove volumes (deletes test data)
docker-compose -f docker-compose.test.yml down -v
```

---

## 3-Tier Testing Strategy

### Tier 1: Unit Tests (`tests/unit/`)
- **Fast** (<1s per test), mocks allowed
- **No Docker required**
- Run: `docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/unit/ -v --timeout=1`

### Tier 2: Integration Tests (`tests/integration/`)
- **Real Docker services**, **NO MOCKING**
- **Timeout:** <5s per test
- Run: `docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/integration/ -v --timeout=5`

### Tier 3: E2E Tests (`tests/e2e/`)
- **Complete workflows**, real infrastructure
- **Timeout:** <10s per test
- Run: `docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/e2e/ -v --timeout=10`

---

## Docker Service URLs

When running inside the test-runner container:

| Service    | Internal URL       | External (Host) URL   |
|------------|--------------------|-----------------------|
| PostgreSQL | `postgres:5432`    | `localhost:5434`      |
| Redis      | `redis:6379`       | `localhost:6380`      |
| Neo4j      | `neo4j:7687`       | `localhost:7687`      |
| Ollama     | `ollama:11434`     | `localhost:11435`     |
| MySQL      | `mysql:3306`       | `localhost:3307`      |

---

## Available Fixtures (from conftest.py)

- `postgres_connection` - PostgreSQL with auto-rollback
- `redis_client` - Redis with auto-cleanup
- `neo4j_connection` - Neo4j with test data cleanup
- `sample_product_data` - Test product data
- `docker_services_available` - Health check for all services

---

## Test Markers

Tests are auto-marked based on directory:

- `@pytest.mark.tier1` - Unit tests (`tests/unit/`)
- `@pytest.mark.tier2` - Integration tests (`tests/integration/`)
- `@pytest.mark.tier3` - E2E tests (`tests/e2e/`)
- `@pytest.mark.requires_docker` - Auto-added to tier2/tier3

Run by marker:
```bash
docker-compose -f docker-compose.test.yml run --rm test-runner pytest -m tier1 -v
docker-compose -f docker-compose.test.yml run --rm test-runner pytest -m tier2 -v
```

---

## Migrated Test Files

Files moved from project root to proper test directories:

### Integration Tests (`tests/integration/`)
- `test_neo4j_integration.py`
- `test_classification_system.py`
- `test_hybrid_recommendations.py`
- `test_safety_compliance.py`
- `test_multilingual_support.py`
- `test_translation_accuracy.py`
- `test_websocket_chat.py`

### E2E Tests (`tests/e2e/`)
- `test_frontend_integration.py`

---

## Troubleshooting

### Services Not Starting
```bash
docker-compose -f docker-compose.test.yml logs postgres
docker-compose -f docker-compose.test.yml restart postgres
```

### Tests Failing with Connection Errors
Ensure you run tests INSIDE Docker:
```bash
# WRONG
pytest tests/integration/

# CORRECT
docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/integration/ -v
```

### Cleanup After Failures
```bash
docker-compose -f docker-compose.test.yml down -v
```

---

## Best Practices

1. **Always use Docker for integration/E2E tests**
2. **Use fixtures** for service connections
3. **Use appropriate timeouts** (1s/5s/10s)
4. **Clean up test data** (auto-handled by fixtures)
5. **Prefix Redis keys** with `test:` for auto-cleanup
6. **Use TestNode label** in Neo4j for auto-cleanup

---

**Run all tests:** `docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/ -v`
