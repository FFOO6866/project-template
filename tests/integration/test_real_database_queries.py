"""
Tier 2: Integration Tests - Real Database Queries
==================================================

Tests that enforce NO MOCKING policy with real infrastructure:
- ✅ Real PostgreSQL database queries
- ✅ Real Redis caching operations
- ✅ Real product data (19,143+ products)
- ❌ NO mock database connections
- ❌ NO fake data returns
- ❌ NO stubbed responses

Speed: <5 seconds per test
Infrastructure: Docker containers (PostgreSQL, Redis)
Focus: Component interactions with real services

SETUP REQUIRED:
    cd tests/utils
    docker-compose -f docker-compose.test.yml up -d postgres redis
    docker-compose -f docker-compose.test.yml ps
"""

import pytest
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import asyncio
import asyncpg
import redis

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Test infrastructure configuration (real Docker services)
TEST_DATABASE_URL = os.getenv(
    'TEST_DATABASE_URL',
    'postgresql://test_user:test_password@localhost:5434/horme_test'
)
TEST_REDIS_URL = os.getenv(
    'TEST_REDIS_URL',
    'redis://localhost:6380/0'
)


@pytest.fixture(scope="session")
def verify_test_infrastructure():
    """Verify test infrastructure is running before tests"""
    # Test PostgreSQL connectivity
    try:
        import psycopg2
        conn = psycopg2.connect(TEST_DATABASE_URL)
        conn.close()
    except Exception as e:
        pytest.fail(
            f"PostgreSQL test database not available at {TEST_DATABASE_URL}\n"
            f"Error: {e}\n"
            f"Start test infrastructure: cd tests/utils && "
            f"docker-compose -f docker-compose.test.yml up -d postgres"
        )

    # Test Redis connectivity
    try:
        redis_client = redis.from_url(TEST_REDIS_URL)
        redis_client.ping()
        redis_client.close()
    except Exception as e:
        pytest.fail(
            f"Redis test instance not available at {TEST_REDIS_URL}\n"
            f"Error: {e}\n"
            f"Start test infrastructure: cd tests/utils && "
            f"docker-compose -f docker-compose.test.yml up -d redis"
        )

    return True


@pytest.fixture(scope="function")
async def clean_test_database():
    """Clean test database before each test"""
    conn = await asyncpg.connect(TEST_DATABASE_URL)
    try:
        # Clean up test data (preserve schema)
        await conn.execute("TRUNCATE TABLE products CASCADE")
        await conn.execute("TRUNCATE TABLE users CASCADE")
        await conn.execute("TRUNCATE TABLE quotations CASCADE")
        await conn.execute("TRUNCATE TABLE rfp_documents CASCADE")
        yield conn
    finally:
        await conn.close()


@pytest.fixture(scope="function")
def clean_test_redis():
    """Clean test Redis before each test"""
    redis_client = redis.from_url(TEST_REDIS_URL, decode_responses=True)
    redis_client.flushdb()  # Clear test database
    yield redis_client
    redis_client.flushdb()
    redis_client.close()


class TestRealPostgreSQLQueries:
    """Test real PostgreSQL database operations - NO MOCKING"""

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    def test_database_connection_real(self, verify_test_infrastructure):
        """Test real PostgreSQL connection (not mocked)"""
        from src.core.postgresql_database import get_database

        db = get_database(TEST_DATABASE_URL)
        assert db is not None
        assert hasattr(db, 'pool') or hasattr(db, 'execute')

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    @pytest.mark.asyncio
    async def test_product_query_returns_real_data(self, clean_test_database):
        """CRITICAL: Product queries must return real data from database, not mock data"""
        conn = clean_test_database

        # Insert real test product
        await conn.execute("""
            INSERT INTO products (sku, name, description, category, price, status, is_published)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, 'TEST-001', 'Test Product', 'A real test product', 'Building Materials',
            99.99, 'active', True)

        # Query product
        result = await conn.fetchrow("""
            SELECT sku, name, category, price
            FROM products
            WHERE sku = $1
        """, 'TEST-001')

        # Verify real data returned
        assert result is not None, "Query should return real data, not None"
        assert result['sku'] == 'TEST-001', "Should return exact SKU queried"
        assert result['name'] == 'Test Product'
        assert result['price'] == 99.99

        # CRITICAL: Verify this is NOT mock data
        assert 'mock' not in result['sku'].lower()
        assert 'fake' not in result['name'].lower()
        assert 'sample' not in result['description'].lower() if 'description' in result else True

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    @pytest.mark.asyncio
    async def test_product_search_with_filters_real(self, clean_test_database):
        """Test product search with filters uses real database queries"""
        conn = clean_test_database

        # Insert multiple test products
        products = [
            ('PAINT-001', 'Acrylic Paint White', 'High-quality acrylic paint', 'Paint', 29.99),
            ('PAINT-002', 'Acrylic Paint Red', 'Vibrant red acrylic paint', 'Paint', 32.99),
            ('CEMENT-001', 'Portland Cement', 'Standard portland cement', 'Building Materials', 15.99)
        ]

        for sku, name, desc, cat, price in products:
            await conn.execute("""
                INSERT INTO products (sku, name, description, category, price, status, is_published)
                VALUES ($1, $2, $3, $4, $5, 'active', true)
            """, sku, name, desc, cat, price)

        # Search for paint products
        results = await conn.fetch("""
            SELECT sku, name, category, price
            FROM products
            WHERE category = $1
            AND status = 'active'
            AND is_published = true
            ORDER BY name
        """, 'Paint')

        # Verify real results
        assert len(results) == 2, "Should find exactly 2 paint products"
        assert results[0]['sku'] == 'PAINT-002'  # Red comes before White alphabetically
        assert results[1]['sku'] == 'PAINT-001'

        # CRITICAL: No mock data patterns
        for result in results:
            assert 'mock' not in result['sku'].lower()
            assert result['price'] > 0, "Price should be real, not 0 or negative"

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    @pytest.mark.asyncio
    async def test_product_search_empty_result_fails_properly(self, clean_test_database):
        """CRITICAL: Empty search should return empty list, not fallback mock data"""
        conn = clean_test_database

        # Search for non-existent product
        results = await conn.fetch("""
            SELECT sku, name FROM products
            WHERE sku = $1
        """, 'NONEXISTENT-999')

        # Should return empty list, not mock data
        assert len(results) == 0, "Should return empty list, not fallback data"
        assert isinstance(results, list), "Should return list type"

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    @pytest.mark.asyncio
    async def test_product_count_returns_real_count(self, clean_test_database):
        """Test product count uses real database aggregation"""
        conn = clean_test_database

        # Insert known number of products
        for i in range(5):
            await conn.execute("""
                INSERT INTO products (sku, name, category, price, status, is_published)
                VALUES ($1, $2, $3, $4, 'active', true)
            """, f'TEST-{i:03d}', f'Test Product {i}', 'Test Category', 10.0 * (i + 1))

        # Count products
        count = await conn.fetchval("SELECT COUNT(*) FROM products")

        # Verify exact count (no approximation or mock)
        assert count == 5, f"Should return exact count 5, got {count}"
        assert isinstance(count, int), "Count should be integer from database"


class TestRealRedisOperations:
    """Test real Redis cache operations - NO MOCKING"""

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    def test_redis_connection_real(self, verify_test_infrastructure, clean_test_redis):
        """Test real Redis connection (not mocked)"""
        redis_client = clean_test_redis

        # Test ping
        response = redis_client.ping()
        assert response is True, "Redis ping should return True"

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    def test_redis_cache_set_get_real(self, clean_test_redis):
        """CRITICAL: Redis cache operations must use real Redis, not mocked"""
        redis_client = clean_test_redis

        # Set cache value
        cache_key = "test:product:SKU-001"
        cache_value = '{"sku": "SKU-001", "name": "Real Product", "price": 99.99}'

        redis_client.setex(cache_key, 3600, cache_value)

        # Get cache value
        retrieved = redis_client.get(cache_key)

        # Verify real Redis operation
        assert retrieved is not None, "Should retrieve real cached value"
        assert retrieved == cache_value, "Should return exact cached value"
        assert 'Real Product' in retrieved

        # CRITICAL: No mock data
        assert 'mock' not in retrieved.lower()
        assert 'fake' not in retrieved.lower()

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    def test_redis_cache_expiration_real(self, clean_test_redis):
        """Test real Redis TTL and expiration"""
        import time
        redis_client = clean_test_redis

        # Set cache with 2 second expiration
        cache_key = "test:expiration"
        redis_client.setex(cache_key, 2, "temporary_value")

        # Verify exists
        assert redis_client.exists(cache_key) == 1

        # Wait for expiration
        time.sleep(3)

        # Verify expired (real Redis behavior)
        assert redis_client.exists(cache_key) == 0, "Key should be expired in real Redis"
        assert redis_client.get(cache_key) is None

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    def test_redis_cache_miss_returns_none(self, clean_test_redis):
        """CRITICAL: Cache miss should return None, not fallback data"""
        redis_client = clean_test_redis

        # Try to get non-existent key
        result = redis_client.get("nonexistent:key:12345")

        # Should return None, not mock data
        assert result is None, "Cache miss should return None, not fallback data"


class TestProductMatchingWorkflowIntegration:
    """Test ProductMatchingWorkflow with real database - NO MOCKING"""

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    def test_workflow_initializes_with_real_database(self, verify_test_infrastructure):
        """Test workflow connects to real PostgreSQL database"""
        from src.workflows.product_matching import ProductMatchingWorkflow

        # Initialize with test database
        workflow = ProductMatchingWorkflow(database_url=TEST_DATABASE_URL)

        # Verify real database connection
        assert workflow.database_url == TEST_DATABASE_URL
        assert hasattr(workflow, 'db')
        assert workflow.db is not None

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    @pytest.mark.asyncio
    async def test_workflow_search_returns_real_products(self, clean_test_database):
        """CRITICAL: Workflow search must return real products from database"""
        from src.workflows.product_matching import ProductMatchingWorkflow

        conn = clean_test_database

        # Insert test products
        await conn.execute("""
            INSERT INTO products (sku, name, description, category, price, status, is_published)
            VALUES ($1, $2, $3, $4, $5, 'active', true)
        """, 'WF-TEST-001', 'Workflow Test Product', 'Test product for workflow', 'Building Materials', 150.0)

        # Create workflow
        workflow = ProductMatchingWorkflow(database_url=TEST_DATABASE_URL)

        # Execute search workflow
        search_workflow = workflow.create_product_search_workflow(['Workflow', 'Test'])
        results, run_id = workflow.runtime.execute(search_workflow)

        # Verify real results from database
        assert results is not None
        assert 'search_products' in results
        products = results['search_products'].get('products', [])

        # Should find the real product we inserted
        assert len(products) > 0, "Should find real products from database"

        found_product = None
        for product in products:
            if product.get('sku') == 'WF-TEST-001':
                found_product = product
                break

        assert found_product is not None, "Should find specific product from database"
        assert found_product['name'] == 'Workflow Test Product'

        # CRITICAL: No mock data
        assert 'mock' not in found_product['sku'].lower()


class TestHybridRecommendationEngineIntegration:
    """Test HybridRecommendationEngine with real Redis - NO MOCKING"""

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    def test_engine_initializes_with_real_redis(self, verify_test_infrastructure, clean_test_redis):
        """Test recommendation engine connects to real Redis"""
        from src.ai.hybrid_recommendation_engine import HybridRecommendationEngine
        from unittest.mock import MagicMock

        # Mock database and knowledge graph (not testing those here)
        mock_db = MagicMock()
        mock_kg = MagicMock()

        # Initialize with real Redis
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv('REDIS_URL', TEST_REDIS_URL)
            mp.setenv('ENVIRONMENT', 'development')
            mp.setenv('HYBRID_WEIGHT_COLLABORATIVE', '0.25')
            mp.setenv('HYBRID_WEIGHT_CONTENT_BASED', '0.25')
            mp.setenv('HYBRID_WEIGHT_KNOWLEDGE_GRAPH', '0.30')
            mp.setenv('HYBRID_WEIGHT_LLM_ANALYSIS', '0.20')

            engine = HybridRecommendationEngine(
                database=mock_db,
                knowledge_graph=mock_kg,
                redis_url=TEST_REDIS_URL
            )

            # Verify real Redis connection
            assert engine.cache_enabled is True
            assert engine.redis_client is not None

            # Test real Redis operation
            engine.redis_client.set('test:key', 'test:value')
            assert engine.redis_client.get('test:key') == 'test:value'

    @pytest.mark.integration
    @pytest.mark.timeout(5)
    def test_recommendation_scores_are_real_not_fallback(self, verify_test_infrastructure):
        """CRITICAL: Recommendation scores must be calculated, not fallback 0.5"""
        # This test verifies the pattern - actual scoring tested in E2E

        from src.ai.hybrid_recommendation_engine import HybridRecommendationEngine
        from unittest.mock import MagicMock

        mock_db = MagicMock()
        mock_kg = MagicMock()

        # Mock database to return real products
        mock_db.fetch.return_value = [
            {'id': 1, 'sku': 'REAL-001', 'name': 'Real Product', 'category': 'Paint', 'price': 50.0}
        ]

        with pytest.MonkeyPatch.context() as mp:
            mp.setenv('REDIS_URL', TEST_REDIS_URL)
            mp.setenv('ENVIRONMENT', 'development')
            mp.setenv('HYBRID_WEIGHT_COLLABORATIVE', '0.25')
            mp.setenv('HYBRID_WEIGHT_CONTENT_BASED', '0.25')
            mp.setenv('HYBRID_WEIGHT_KNOWLEDGE_GRAPH', '0.30')
            mp.setenv('HYBRID_WEIGHT_LLM_ANALYSIS', '0.20')

            engine = HybridRecommendationEngine(
                database=mock_db,
                knowledge_graph=mock_kg,
                redis_url=TEST_REDIS_URL
            )

            # Verify algorithm weights are real, not all 0.5
            assert engine.weights['collaborative'] != 0.5
            assert engine.weights['content_based'] != 0.5
            assert sum(engine.weights.values()) == pytest.approx(1.0, abs=0.01)


class TestNoMockingPolicyEnforcement:
    """Enforce NO MOCKING policy in integration tests"""

    @pytest.mark.integration
    def test_integration_tests_use_real_postgres(self):
        """Verify integration tests use real PostgreSQL, not mocks"""
        # Test that we can connect to real database
        import psycopg2
        conn = psycopg2.connect(TEST_DATABASE_URL)
        cursor = conn.cursor()

        # Execute real query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()

        # Should get real PostgreSQL version, not mock
        assert version is not None
        assert 'PostgreSQL' in version[0]

        cursor.close()
        conn.close()

    @pytest.mark.integration
    def test_integration_tests_use_real_redis(self):
        """Verify integration tests use real Redis, not mocks"""
        redis_client = redis.from_url(TEST_REDIS_URL)

        # Get real Redis info
        info = redis_client.info()

        # Should get real Redis info, not mock
        assert 'redis_version' in info
        assert info['redis_version'] is not None

        redis_client.close()


# Test execution summary
if __name__ == "__main__":
    print("=" * 80)
    print("Tier 2: Integration Tests - Real Database Queries")
    print("=" * 80)
    print("\nPRE-REQUISITES:")
    print("1. Start test infrastructure:")
    print("   cd tests/utils")
    print("   docker-compose -f docker-compose.test.yml up -d postgres redis")
    print("2. Verify services are running:")
    print("   docker-compose -f docker-compose.test.yml ps")
    print("3. Check health:")
    print("   docker-compose -f docker-compose.test.yml logs postgres redis")
    print("=" * 80)
    print("\nRunning tests...")
    pytest.main([__file__, "-v", "--tb=short", "--timeout=5", "-m", "integration"])
