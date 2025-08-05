"""
Tier 2 (Integration) Tests for Testing Infrastructure
===================================================

Integration tests with real database connections and services.
Tests component interactions with real infrastructure - NO MOCKING.
Maximum execution time: <5 seconds per test.

Prerequisites:
- Docker test environment must be running
- PostgreSQL, Neo4j, ChromaDB, Redis services must be healthy

Coverage:
- Real database connections and operations
- Data persistence and retrieval
- Service integration and communication
- Performance with real data loads
- Cross-service data consistency
"""

import pytest
import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Database and service clients with conditional imports
import asyncpg
import redis
import httpx

# Conditional imports for optional services
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    # Create mock chromadb when not available
    class MockChromaDB:
        @staticmethod
        def Client(*args, **kwargs):
            return None
    chromadb = MockChromaDB()
    CHROMADB_AVAILABLE = False

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    # Create mock GraphDatabase when Neo4j not available
    class GraphDatabase:
        @staticmethod
        def driver(*args, **kwargs):
            return None
    NEO4J_AVAILABLE = False

# Import test data factories
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "test-data"))

from test_data_factory import (
    ProductDataFactory,
    KnowledgeGraphDataFactory,
    PerformanceTestDataFactory,
    generate_all_test_data
)


# Test configuration for real services
TEST_CONFIG = {
    'postgres': {
        'host': 'localhost',
        'port': 5433,
        'database': 'horme_test',
        'user': 'test_user',
        'password': 'test_pass'
    },
    'neo4j': {
        'uri': 'bolt://localhost:7688',
        'user': 'neo4j',
        'password': 'test_password'
    },
    'chromadb': {
        'host': 'localhost',
        'port': 8001,
        'token': 'test-token'
    },
    'redis': {
        'host': 'localhost',
        'port': 6381,
        'db': 0
    },
    'openai_mock': {
        'base_url': 'http://localhost:8002',
        'api_key': 'test-key'
    }
}


def get_postgres_url():
    """Get PostgreSQL connection URL"""
    cfg = TEST_CONFIG['postgres']
    return f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"


@pytest.fixture(scope="session")
async def postgres_connection():
    """Provide PostgreSQL connection for integration tests"""
    conn = None
    try:
        conn = await asyncpg.connect(get_postgres_url())
        yield conn
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")
    finally:
        if conn:
            await conn.close()


@pytest.fixture(scope="session")
def neo4j_driver():
    """Provide Neo4j driver for integration tests"""
    driver = None
    try:
        cfg = TEST_CONFIG['neo4j']
        driver = GraphDatabase.driver(cfg['uri'], auth=(cfg['user'], cfg['password']))
        
        # Test connection
        with driver.session() as session:
            session.run("RETURN 1")
        
        yield driver
    except Exception as e:
        pytest.skip(f"Neo4j not available: {e}")
    finally:
        if driver:
            driver.close()


@pytest.fixture(scope="session")
def chromadb_client():
    """Provide ChromaDB client for integration tests"""
    try:
        cfg = TEST_CONFIG['chromadb']
        client = chromadb.HttpClient(
            host=cfg['host'],
            port=cfg['port'],
            settings={
                "chroma_client_auth_provider": "token",
                "chroma_client_auth_credentials": cfg['token']
            }
        )
        
        # Test connection
        client.heartbeat()
        yield client
    except Exception as e:
        pytest.skip(f"ChromaDB not available: {e}")


@pytest.fixture(scope="session")
def redis_client():
    """Provide Redis client for integration tests"""
    client = None
    try:
        cfg = TEST_CONFIG['redis']
        client = redis.Redis(host=cfg['host'], port=cfg['port'], db=cfg['db'])
        
        # Test connection
        client.ping()
        yield client
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
    finally:
        if client:
            client.close()


@pytest.fixture
async def clean_test_data(postgres_connection, neo4j_driver, chromadb_client, redis_client):
    """Clean test data before and after tests"""
    # Cleanup before test
    await cleanup_postgres(postgres_connection)
    cleanup_neo4j(neo4j_driver)
    cleanup_chromadb(chromadb_client)
    cleanup_redis(redis_client)
    
    yield
    
    # Cleanup after test
    await cleanup_postgres(postgres_connection)
    cleanup_neo4j(neo4j_driver)
    cleanup_chromadb(chromadb_client)
    cleanup_redis(redis_client)


async def cleanup_postgres(conn):
    """Clean PostgreSQL test data"""
    try:
        await conn.execute("DELETE FROM test_search_queries WHERE user_id IS NOT NULL")
        await conn.execute("DELETE FROM test_user_sessions WHERE user_id IS NOT NULL")
        await conn.execute("DELETE FROM test_products WHERE product_code LIKE 'TEST-%'")
        await conn.execute("DELETE FROM test_users WHERE username LIKE 'test_%'")
        await conn.execute("DELETE FROM test_safety_standards WHERE standard_id LIKE 'TEST-%'")
    except Exception:
        pass  # Ignore cleanup errors


def cleanup_neo4j(driver):
    """Clean Neo4j test data"""
    try:
        with driver.session() as session:
            session.run("MATCH (n) WHERE n.test_data = true DELETE n")
            session.run("MATCH ()-[r {test_data: true}]-() DELETE r")
    except Exception:
        pass  # Ignore cleanup errors


def cleanup_chromadb(client):
    """Clean ChromaDB test collections"""
    try:
        for collection in client.list_collections():
            if collection.name.startswith('test_'):
                client.delete_collection(collection.name)
    except Exception:
        pass  # Ignore cleanup errors


def cleanup_redis(client):
    """Clean Redis test data"""
    try:
        for key in client.scan_iter(match="test:*"):
            client.delete(key)
    except Exception:
        pass  # Ignore cleanup errors


@pytest.mark.integration
@pytest.mark.requires_docker
class TestPostgreSQLIntegration:
    """Test PostgreSQL database integration with real connections"""
    
    async def test_database_connection(self, postgres_connection):
        """Test that PostgreSQL connection is working"""
        result = await postgres_connection.fetchval("SELECT 1")
        assert result == 1, "PostgreSQL connection test failed"
    
    async def test_product_data_persistence(self, postgres_connection, clean_test_data, performance_monitor):
        """Test inserting and retrieving product data"""
        monitor = performance_monitor.start("product_data_persistence")
        
        # Generate test products
        products = ProductDataFactory.create_products(10)
        
        # Insert products
        for product in products:
            await postgres_connection.execute("""
                INSERT INTO test_products (
                    product_code, name, category, subcategory, unspsc_code,
                    etim_class, price, description, safety_standards, vendor_id,
                    skill_level_required, complexity_score, embedding_vector
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """, 
                product.product_code, product.name, product.category, product.subcategory,
                product.unspsc_code, product.etim_class, product.price, product.description,
                product.safety_standards, product.vendor_id, product.skill_level_required,
                product.complexity_score, product.embedding_vector
            )
        
        # Retrieve and verify products
        rows = await postgres_connection.fetch("SELECT * FROM test_products WHERE product_code LIKE 'PRD-%'")
        
        duration = monitor.stop("product_data_persistence")
        
        assert len(rows) == 10, f"Expected 10 products, found {len(rows)}"
        
        # Verify data integrity
        for row in rows:
            assert row['product_code'].startswith('PRD-'), "Invalid product code format"
            assert row['price'] > 0, "Price should be positive"
            assert len(row['embedding_vector']) == 384, "Embedding vector should have 384 dimensions"
        
        # Performance validation - should complete in <5s
        assert duration < 5.0, f"Product persistence took {duration:.3f}s, exceeds 5s limit"
    
    async def test_user_profile_operations(self, postgres_connection, clean_test_data, performance_monitor):
        """Test user profile CRUD operations"""
        monitor = performance_monitor.start("user_profile_operations")
        
        # Generate test users
        users = ProductDataFactory.create_user_profiles(5)
        
        # Insert users
        for user in users:
            await postgres_connection.execute("""
                INSERT INTO test_users (
                    user_id, username, email, role, skill_level, experience_years,
                    certifications, safety_training, preferred_categories, location
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                user.user_id, user.username, user.email, user.role, user.skill_level,
                user.experience_years, user.certifications, user.safety_training,
                user.preferred_categories, user.location
            )
        
        # Test user retrieval
        user_count = await postgres_connection.fetchval("SELECT COUNT(*) FROM test_users")
        assert user_count >= 5, f"Expected at least 5 users, found {user_count}"
        
        # Test user search by skill level
        intermediate_users = await postgres_connection.fetch(
            "SELECT * FROM test_users WHERE skill_level = 'intermediate'"
        )
        
        # Test user update
        test_user = users[0]
        await postgres_connection.execute(
            "UPDATE test_users SET experience_years = $1 WHERE user_id = $2",
            99, test_user.user_id
        )
        
        updated_user = await postgres_connection.fetchrow(
            "SELECT * FROM test_users WHERE user_id = $1", test_user.user_id
        )
        assert updated_user['experience_years'] == 99, "User update failed"
        
        duration = monitor.stop("user_profile_operations")
        assert duration < 5.0, f"User operations took {duration:.3f}s, exceeds 5s limit"
    
    async def test_vector_similarity_search(self, postgres_connection, clean_test_data, performance_monitor):
        """Test PostgreSQL vector similarity search with pgvector"""
        monitor = performance_monitor.start("vector_similarity_search")
        
        # Insert products with embeddings
        products = ProductDataFactory.create_products(20)
        
        for product in products:
            await postgres_connection.execute("""
                INSERT INTO test_products (
                    product_code, name, category, price, embedding_vector
                ) VALUES ($1, $2, $3, $4, $5)
            """, product.product_code, product.name, product.category, product.price, product.embedding_vector)
        
        # Test similarity search function
        query_vector = products[0].embedding_vector
        similar_products = await postgres_connection.fetch("""
            SELECT * FROM find_similar_products($1::vector(384), 0.5, 5)
        """, query_vector)
        
        duration = monitor.stop("vector_similarity_search")
        
        assert len(similar_products) > 0, "Should find at least one similar product"
        assert similar_products[0]['product_code'] == products[0].product_code, "Should find exact match first"
        
        # Performance validation
        assert duration < 2.0, f"Vector search took {duration:.3f}s, exceeds 2s limit for integration test"
    
    async def test_performance_logging(self, postgres_connection, clean_test_data):
        """Test performance logging functionality"""
        # Create a test user first
        test_user_id = str(uuid.uuid4())
        await postgres_connection.execute("""
            INSERT INTO test_users (user_id, username, email, role) 
            VALUES ($1, $2, $3, $4)
        """, test_user_id, "perf_test_user", "perf@test.com", "user")
        
        # Log some performance data
        query_id = await postgres_connection.fetchval("""
            SELECT log_search_performance($1, $2, $3, $4, $5, $6)
        """, 
            test_user_id, "search", "test query", 
            json.dumps({"category": "tools"}), 250, 15
        )
        
        assert query_id is not None, "Performance logging should return query ID"
        
        # Verify performance data was logged
        logged_query = await postgres_connection.fetchrow(
            "SELECT * FROM test_search_queries WHERE query_id = $1", query_id
        )
        
        assert logged_query is not None, "Query should be logged"
        assert logged_query['response_time_ms'] == 250, "Response time should match"
        assert logged_query['results_count'] == 15, "Results count should match"


@pytest.mark.integration  
@pytest.mark.requires_docker
class TestNeo4jIntegration:
    """Test Neo4j knowledge graph integration with real connections"""
    
    def test_neo4j_connection(self, neo4j_driver):
        """Test that Neo4j connection is working"""
        with neo4j_driver.session() as session:
            result = session.run("RETURN 1 as test").single()
            assert result['test'] == 1, "Neo4j connection test failed"
    
    def test_knowledge_graph_data_operations(self, neo4j_driver, clean_test_data, performance_monitor):
        """Test knowledge graph data insertion and querying"""
        monitor = performance_monitor.start("knowledge_graph_operations")
        
        with neo4j_driver.session() as session:
            # Create test nodes
            session.run("""
                CREATE (t:Tool {
                    tool_id: 'TEST_TOOL_001',
                    name: 'Test Drill',
                    category: 'Power Tools',
                    test_data: true
                })
            """)
            
            session.run("""
                CREATE (task:Task {
                    task_id: 'TEST_TASK_001',
                    name: 'Test Drilling',
                    complexity: 'beginner',
                    test_data: true
                })
            """)
            
            # Create relationship
            session.run("""
                MATCH (t:Tool {tool_id: 'TEST_TOOL_001'})
                MATCH (task:Task {task_id: 'TEST_TASK_001'})
                CREATE (t)-[:USED_FOR {confidence: 0.95, test_data: true}]->(task)
            """)
            
            # Query tools for task
            result = session.run("""
                MATCH (task:Task {task_id: 'TEST_TASK_001'})<-[:USED_FOR]-(tool:Tool)
                RETURN tool.name as tool_name, tool.category as category
            """).single()
            
            duration = monitor.stop("knowledge_graph_operations")
            
            assert result is not None, "Should find tool for task"
            assert result['tool_name'] == 'Test Drill', "Should return correct tool name"
            assert result['category'] == 'Power Tools', "Should return correct category"
            
            # Performance validation
            assert duration < 5.0, f"Knowledge graph operations took {duration:.3f}s, exceeds 5s limit"
    
    def test_recommendation_queries(self, neo4j_driver, clean_test_data, performance_monitor):
        """Test recommendation queries on knowledge graph"""
        monitor = performance_monitor.start("recommendation_queries")
        
        with neo4j_driver.session() as session:
            # Create test data for recommendations
            session.run("""
                CREATE (t1:Tool {tool_id: 'REC_TOOL_001', name: 'Drill A', category: 'Power Tools', test_data: true})
                CREATE (t2:Tool {tool_id: 'REC_TOOL_002', name: 'Drill B', category: 'Power Tools', test_data: true})
                CREATE (t3:Tool {tool_id: 'REC_TOOL_003', name: 'Saw A', category: 'Power Tools', test_data: true})
                CREATE (t1)-[:SIMILAR_TO {similarity: 0.8, test_data: true}]->(t2)
                CREATE (t2)-[:SIMILAR_TO {similarity: 0.7, test_data: true}]->(t3)
            """)
            
            # Query for similar tools
            results = session.run("""
                MATCH (t:Tool {tool_id: 'REC_TOOL_001'})-[:SIMILAR_TO]-(similar:Tool)
                RETURN similar.name as tool_name, similar.category as category
                LIMIT 5
            """).data()
            
            duration = monitor.stop("recommendation_queries")
            
            assert len(results) > 0, "Should find similar tools"
            assert results[0]['tool_name'] == 'Drill B', "Should find most similar tool"
            
            # Performance validation
            assert duration < 3.0, f"Recommendation queries took {duration:.3f}s, exceeds 3s limit"
    
    def test_graph_algorithm_performance(self, neo4j_driver, clean_test_data, performance_monitor):
        """Test graph algorithm performance with larger dataset"""
        monitor = performance_monitor.start("graph_algorithm_performance")
        
        with neo4j_driver.session() as session:
            # Create a larger test graph
            session.run("""
                UNWIND range(1, 50) AS i
                CREATE (t:Tool {
                    tool_id: 'PERF_TOOL_' + toString(i),
                    name: 'Performance Tool ' + toString(i),
                    category: ['Power Tools', 'Hand Tools', 'Measuring Tools'][i % 3],
                    test_data: true
                })
            """)
            
            # Create random relationships
            session.run("""
                MATCH (t1:Tool), (t2:Tool)
                WHERE t1.tool_id STARTS WITH 'PERF_TOOL_' 
                  AND t2.tool_id STARTS WITH 'PERF_TOOL_'
                  AND t1 <> t2
                  AND rand() < 0.1
                CREATE (t1)-[:SIMILAR_TO {similarity: rand(), test_data: true}]->(t2)
            """)
            
            # Run complex query (shortest path)
            result = session.run("""
                MATCH (start:Tool {tool_id: 'PERF_TOOL_1'}),
                      (end:Tool {tool_id: 'PERF_TOOL_25'})
                MATCH path = shortestPath((start)-[*..5]-(end))
                RETURN length(path) as path_length
            """).single()
            
            duration = monitor.stop("graph_algorithm_performance")
            
            # Performance validation for complex queries
            assert duration < 5.0, f"Graph algorithm took {duration:.3f}s, exceeds 5s limit"


@pytest.mark.integration
@pytest.mark.requires_docker  
class TestChromaDBIntegration:
    """Test ChromaDB vector database integration with real connections"""
    
    def test_chromadb_connection(self, chromadb_client):
        """Test that ChromaDB connection is working"""
        heartbeat = chromadb_client.heartbeat()
        assert heartbeat > 0, "ChromaDB connection test failed"
    
    def test_collection_operations(self, chromadb_client, clean_test_data, performance_monitor):
        """Test ChromaDB collection creation and management"""
        monitor = performance_monitor.start("chromadb_collection_operations")
        
        # Create test collection
        collection_name = "test_products_integration"
        collection = chromadb_client.create_collection(
            name=collection_name,
            metadata={"description": "Integration test collection"}
        )
        
        # Add some embeddings
        products = ProductDataFactory.create_products(10)
        
        ids = [p.product_code for p in products]
        embeddings = [p.embedding_vector for p in products]
        documents = [f"{p.name}: {p.description}" for p in products]
        metadatas = [{"category": p.category, "price": p.price} for p in products]
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        # Verify data was added
        count = collection.count()
        assert count == 10, f"Expected 10 embeddings, found {count}"
        
        duration = monitor.stop("chromadb_collection_operations")
        assert duration < 5.0, f"ChromaDB collection operations took {duration:.3f}s, exceeds 5s limit"
    
    def test_vector_search_operations(self, chromadb_client, clean_test_data, performance_monitor):
        """Test ChromaDB vector similarity search"""
        monitor = performance_monitor.start("chromadb_vector_search")
        
        # Create collection with test data
        collection_name = "test_search_integration"
        collection = chromadb_client.create_collection(name=collection_name)
        
        products = ProductDataFactory.create_products(50)
        
        collection.add(
            ids=[p.product_code for p in products],
            embeddings=[p.embedding_vector for p in products],
            documents=[f"{p.name}: {p.description}" for p in products],
            metadatas=[{"category": p.category} for p in products]
        )
        
        # Perform similarity search
        query_embedding = products[0].embedding_vector
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        
        duration = monitor.stop("chromadb_vector_search")
        
        assert len(results['ids'][0]) == 5, "Should return 5 results"
        assert results['ids'][0][0] == products[0].product_code, "Should find exact match first"
        
        # Performance validation
        assert duration < 3.0, f"Vector search took {duration:.3f}s, exceeds 3s limit"
    
    def test_filtered_search(self, chromadb_client, clean_test_data, performance_monitor):
        """Test ChromaDB search with metadata filtering"""
        monitor = performance_monitor.start("chromadb_filtered_search")
        
        collection_name = "test_filtered_search"
        collection = chromadb_client.create_collection(name=collection_name)
        
        products = ProductDataFactory.create_products(30)
        
        collection.add(
            ids=[p.product_code for p in products],
            embeddings=[p.embedding_vector for p in products],
            documents=[f"{p.name}: {p.description}" for p in products],
            metadatas=[{
                "category": p.category,
                "price": p.price,
                "skill_level": p.skill_level_required
            } for p in products]
        )
        
        # Search with category filter
        query_embedding = products[0].embedding_vector
        results = collection.query(
            query_embeddings=[query_embedding],
            where={"category": "Power Tools"},
            n_results=3
        )
        
        duration = monitor.stop("chromadb_filtered_search")
        
        assert len(results['ids'][0]) <= 3, "Should return at most 3 results"
        
        # Verify all results match filter
        for metadata in results['metadatas'][0]:
            assert metadata['category'] == 'Power Tools', "All results should match filter"
        
        # Performance validation
        assert duration < 4.0, f"Filtered search took {duration:.3f}s, exceeds 4s limit"


@pytest.mark.integration
@pytest.mark.requires_docker
class TestRedisIntegration:
    """Test Redis cache integration with real connections"""
    
    def test_redis_connection(self, redis_client):
        """Test that Redis connection is working"""
        result = redis_client.ping()
        assert result is True, "Redis connection test failed"
    
    def test_cache_operations(self, redis_client, clean_test_data, performance_monitor):
        """Test Redis cache set/get operations"""
        monitor = performance_monitor.start("redis_cache_operations")
        
        # Test basic cache operations
        test_key = "test:cache:product:123"
        test_value = {"name": "Test Product", "price": 99.99, "category": "Tools"}
        
        # Set cache entry
        redis_client.setex(test_key, 3600, json.dumps(test_value))
        
        # Get cache entry
        cached_value = redis_client.get(test_key)
        assert cached_value is not None, "Cache entry should exist"
        
        cached_data = json.loads(cached_value)
        assert cached_data['name'] == test_value['name'], "Cached data should match"
        assert cached_data['price'] == test_value['price'], "Cached price should match"
        
        duration = monitor.stop("redis_cache_operations")
        assert duration < 1.0, f"Cache operations took {duration:.3f}s, exceeds 1s limit"
    
    def test_session_management(self, redis_client, clean_test_data, performance_monitor):
        """Test Redis session management operations"""
        monitor = performance_monitor.start("redis_session_management")
        
        # Create test session
        session_id = str(uuid.uuid4())
        session_data = {
            "user_id": "test_user_123",
            "login_time": datetime.now().isoformat(),
            "preferences": {"theme": "dark", "language": "en"}
        }
        
        session_key = f"test:session:{session_id}"
        redis_client.setex(session_key, 1800, json.dumps(session_data))  # 30 min TTL
        
        # Retrieve session
        retrieved_session = redis_client.get(session_key)
        assert retrieved_session is not None, "Session should exist"
        
        session_obj = json.loads(retrieved_session)
        assert session_obj['user_id'] == session_data['user_id'], "Session user ID should match"
        
        # Test session expiry
        ttl = redis_client.ttl(session_key)
        assert ttl > 0, "Session should have TTL set"
        assert ttl <= 1800, "Session TTL should be within expected range"
        
        duration = monitor.stop("redis_session_management")
        assert duration < 2.0, f"Session management took {duration:.3f}s, exceeds 2s limit"
    
    def test_performance_counters(self, redis_client, clean_test_data, performance_monitor):
        """Test Redis performance counters and metrics"""
        monitor = performance_monitor.start("redis_performance_counters")
        
        # Test atomic counters
        counter_key = "test:counter:api_requests"
        
        # Increment counter multiple times
        for i in range(10):
            redis_client.incr(counter_key)
        
        counter_value = redis_client.get(counter_key)
        assert int(counter_value) == 10, "Counter should equal 10"
        
        # Test hash-based metrics
        metrics_key = "test:metrics:response_times"
        redis_client.hset(metrics_key, "avg_response_time", "250")
        redis_client.hset(metrics_key, "max_response_time", "500")
        redis_client.hset(metrics_key, "request_count", "100")
        
        metrics = redis_client.hgetall(metrics_key)
        assert len(metrics) == 3, "Should have 3 metrics"
        assert metrics[b'avg_response_time'] == b'250', "Average response time should match"
        
        duration = monitor.stop("redis_performance_counters")
        assert duration < 1.5, f"Performance counters took {duration:.3f}s, exceeds 1.5s limit"


@pytest.mark.integration
@pytest.mark.requires_docker
class TestOpenAIMockIntegration:
    """Test OpenAI API mock server integration"""
    
    async def test_openai_mock_connection(self, performance_monitor):
        """Test that OpenAI mock server is responding"""
        monitor = performance_monitor.start("openai_mock_connection")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{TEST_CONFIG['openai_mock']['base_url']}/__admin/health",
                    timeout=5.0
                )
                
                duration = monitor.stop("openai_mock_connection")
                
                assert response.status_code == 200, "OpenAI mock should be healthy"
                assert duration < 2.0, f"Mock health check took {duration:.3f}s, exceeds 2s limit"
                
            except httpx.ConnectError:
                pytest.skip("OpenAI mock server not available")
    
    async def test_chat_completion_mock(self, performance_monitor):
        """Test OpenAI chat completions API mock"""
        monitor = performance_monitor.start("openai_chat_completion")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{TEST_CONFIG['openai_mock']['base_url']}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {TEST_CONFIG['openai_mock']['api_key']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {"role": "user", "content": "What tools do I need for drilling?"}
                        ]
                    },
                    timeout=5.0
                )
                
                duration = monitor.stop("openai_chat_completion")
                
                assert response.status_code == 200, "Chat completion should succeed"
                
                data = response.json()
                assert "choices" in data, "Response should contain choices"
                assert len(data["choices"]) > 0, "Should have at least one choice"
                assert data["choices"][0]["message"]["role"] == "assistant", "Should have assistant response"
                
                assert duration < 3.0, f"Chat completion took {duration:.3f}s, exceeds 3s limit"
                
            except httpx.ConnectError:
                pytest.skip("OpenAI mock server not available")
    
    async def test_embeddings_mock(self, performance_monitor):
        """Test OpenAI embeddings API mock"""
        monitor = performance_monitor.start("openai_embeddings")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{TEST_CONFIG['openai_mock']['base_url']}/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {TEST_CONFIG['openai_mock']['api_key']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "text-embedding-ada-002",
                        "input": "cordless drill for home improvement"
                    },
                    timeout=5.0
                )
                
                duration = monitor.stop("openai_embeddings")
                
                assert response.status_code == 200, "Embeddings should succeed"
                
                data = response.json()
                assert "data" in data, "Response should contain data"
                assert len(data["data"]) > 0, "Should have at least one embedding"
                assert "embedding" in data["data"][0], "Should contain embedding vector"
                
                embedding = data["data"][0]["embedding"]
                assert len(embedding) == 384, "Mock should return 384-dimensional embeddings"
                
                assert duration < 2.0, f"Embeddings took {duration:.3f}s, exceeds 2s limit"
                
            except httpx.ConnectError:
                pytest.skip("OpenAI mock server not available")


@pytest.mark.integration
@pytest.mark.requires_docker
class TestCrossServiceIntegration:
    """Test integration across multiple services"""
    
    async def test_full_data_pipeline(self, postgres_connection, neo4j_driver, chromadb_client, 
                                    redis_client, clean_test_data, performance_monitor):
        """Test complete data pipeline across all services"""
        monitor = performance_monitor.start("full_data_pipeline")
        
        # Generate test data
        products = ProductDataFactory.create_products(5)
        users = ProductDataFactory.create_user_profiles(2)
        
        # 1. Store products in PostgreSQL
        for product in products:
            await postgres_connection.execute("""
                INSERT INTO test_products (
                    product_code, name, category, price, embedding_vector
                ) VALUES ($1, $2, $3, $4, $5)
            """, product.product_code, product.name, product.category, 
                product.price, product.embedding_vector)
        
        # 2. Create knowledge graph relationships in Neo4j
        with neo4j_driver.session() as session:
            for product in products[:3]:  # Use first 3 products
                session.run("""
                    CREATE (p:Product {
                        product_id: $product_id,
                        name: $name,
                        category: $category,
                        test_data: true
                    })
                """, product_id=product.product_code, name=product.name, category=product.category)
        
        # 3. Store embeddings in ChromaDB
        collection_name = "test_pipeline_products"
        collection = chromadb_client.create_collection(name=collection_name)
        
        collection.add(
            ids=[p.product_code for p in products],
            embeddings=[p.embedding_vector for p in products],
            documents=[f"{p.name}: {p.description}" for p in products],
            metadatas=[{"category": p.category} for p in products]
        )
        
        # 4. Cache popular products in Redis
        popular_products = [p.product_code for p in products[:2]]
        redis_client.setex(
            "test:popular:products", 
            3600, 
            json.dumps(popular_products)
        )
        
        # 5. Verify data consistency across services
        
        # Check PostgreSQL
        pg_count = await postgres_connection.fetchval(
            "SELECT COUNT(*) FROM test_products WHERE product_code LIKE 'PRD-%'"
        )
        assert pg_count == 5, f"PostgreSQL should have 5 products, found {pg_count}"
        
        # Check Neo4j
        with neo4j_driver.session() as session:
            neo4j_count = session.run(
                "MATCH (p:Product {test_data: true}) RETURN count(p) as count"
            ).single()['count']
            assert neo4j_count == 3, f"Neo4j should have 3 products, found {neo4j_count}"
        
        # Check ChromaDB
        chroma_count = collection.count()
        assert chroma_count == 5, f"ChromaDB should have 5 embeddings, found {chroma_count}"
        
        # Check Redis
        cached_products = redis_client.get("test:popular:products")
        assert cached_products is not None, "Popular products should be cached"
        cached_list = json.loads(cached_products)
        assert len(cached_list) == 2, f"Should have 2 cached products, found {len(cached_list)}"
        
        duration = monitor.stop("full_data_pipeline")
        assert duration < 5.0, f"Full pipeline took {duration:.3f}s, exceeds 5s limit"
    
    async def test_search_recommendation_pipeline(self, postgres_connection, chromadb_client, 
                                                redis_client, clean_test_data, performance_monitor):
        """Test search and recommendation pipeline across services"""
        monitor = performance_monitor.start("search_recommendation_pipeline")
        
        # Setup test data
        products = ProductDataFactory.create_products(20)
        
        # Store in PostgreSQL and ChromaDB
        for product in products:
            await postgres_connection.execute("""
                INSERT INTO test_products (
                    product_code, name, category, price, embedding_vector
                ) VALUES ($1, $2, $3, $4, $5)
            """, product.product_code, product.name, product.category, 
                product.price, product.embedding_vector)
        
        collection_name = "test_search_products"
        collection = chromadb_client.create_collection(name=collection_name)
        collection.add(
            ids=[p.product_code for p in products],
            embeddings=[p.embedding_vector for p in products],
            documents=[f"{p.name}: {p.description}" for p in products],
            metadatas=[{"category": p.category, "price": p.price} for p in products]
        )
        
        # Simulate search workflow
        query_product = products[0]
        
        # 1. Vector similarity search in ChromaDB
        similar_results = collection.query(
            query_embeddings=[query_product.embedding_vector],
            n_results=5
        )
        
        similar_ids = similar_results['ids'][0]
        assert len(similar_ids) == 5, "Should find 5 similar products"
        
        # 2. Get detailed product info from PostgreSQL
        placeholders = ','.join(['$' + str(i+1) for i in range(len(similar_ids))])
        detailed_products = await postgres_connection.fetch(f"""
            SELECT product_code, name, category, price 
            FROM test_products 
            WHERE product_code IN ({placeholders})
            ORDER BY price ASC
        """, *similar_ids)
        
        assert len(detailed_products) == 5, "Should get detailed info for all similar products"
        
        # 3. Cache search results in Redis
        search_cache_key = f"test:search:{query_product.product_code}"
        search_results = [dict(row) for row in detailed_products]
        
        redis_client.setex(
            search_cache_key,
            1800,  # 30 minutes
            json.dumps(search_results, default=str)
        )
        
        # 4. Verify cached results
        cached_results = redis_client.get(search_cache_key)
        assert cached_results is not None, "Search results should be cached"
        
        cached_data = json.loads(cached_results)
        assert len(cached_data) == 5, "Cached results should have 5 products"
        
        duration = monitor.stop("search_recommendation_pipeline")
        assert duration < 4.0, f"Search pipeline took {duration:.3f}s, exceeds 4s limit"


if __name__ == "__main__":
    # Run integration tests directly for debugging
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])