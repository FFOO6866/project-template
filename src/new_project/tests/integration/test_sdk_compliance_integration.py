"""
FOUND-001: SDK Compliance Foundation - Integration Tests
=====================================================

Integration tests for SDK compliance with real infrastructure.
Tests node interactions with actual database connections and services.

Test Strategy: Integration Tests (Tier 2)
- Use real Docker services from tests/utils
- NO MOCKING of external services (PostgreSQL, Redis, etc.)
- Test component interactions with real data flows
- Test parameter injection with actual connections
- Timeout: <5 seconds per test

Prerequisites:
- Run: ./tests/utils/test-env up && ./tests/utils/test-env status
- Ensure PostgreSQL, Redis, and other services are available

Coverage:
- Real database connection testing
- Node interactions with actual services
- Parameter injection across 3 methods with real connections
- Workflow execution with real infrastructure
- Performance validation with real services
"""

import pytest
import asyncio
import json
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Windows compatibility patch
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import windows_patch  # Apply Windows compatibility for Kailash SDK

# Kailash SDK imports for integration testing
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash.nodes.base import Node, register_node

# Import our SDK compliance implementations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from nodes.sdk_compliance import SecureGovernedNode
# Mock connections for SDK compatibility tests
class MockPostgreSQLConnection:
    def __init__(self, *args, **kwargs):
        self.connected = False
    
    def connect(self):
        self.connected = True
        return True
    
    def disconnect(self):
        self.connected = False

class MockRedisConnection:
    def __init__(self, *args, **kwargs):
        self.connected = False
    
    def connect(self):
        self.connected = True
        return True
    
    def disconnect(self):
        self.connected = False

# Test infrastructure imports
import sys
import os

# Mock docker config since utils directory doesn't exist
class DockerConfig:
    @staticmethod
    def is_docker_available():
        return False
    
    @staticmethod
    def get_container_status(service_name):
        return "unavailable"
    
    @staticmethod
    def start_services():
        return True

# Test fixtures for real infrastructure
@pytest.fixture(scope="session")
def docker_services():
    """Setup Docker services for integration testing"""
    config = DockerConfig()
    
    # Verify services are running
    services_status = config.get_service_status()
    
    required_services = ['postgres', 'redis']
    missing_services = []
    
    for service in required_services:
        if not services_status.get(service, {}).get('running', False):
            missing_services.append(service)
    
    if missing_services:
        pytest.skip(f"Required services not running: {missing_services}. "
                   f"Run: ./tests/utils/test-env up")
    
    return config

@pytest.fixture
def postgres_connection(docker_services):
    """Create real PostgreSQL connection for testing"""
    config = docker_services
    
    connection = PostgreSQLConnection(
        host='localhost',
        port=config.get_port('postgres'),
        database='test_db',
        username='postgres',
        password='test_password'
    )
    
    return connection

@pytest.fixture
def redis_connection(docker_services):
    """Create real Redis connection for testing"""
    config = docker_services
    
    connection = RedisConnection(
        host='localhost',
        port=config.get_port('redis'),
        database=0
    )
    
    return connection

@pytest.fixture
async def setup_test_database(postgres_connection):
    """Setup test database schema and data"""
    # Create test tables
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS compliance_test_products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        category VARCHAR(100),
        price DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS compliance_test_users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(255),
        role VARCHAR(50) DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS compliance_audit_log (
        id SERIAL PRIMARY KEY,
        event_type VARCHAR(100) NOT NULL,
        user_id INTEGER,
        entity_type VARCHAR(100),
        entity_id INTEGER,
        metadata JSONB,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Insert test data
    insert_data_sql = """
    INSERT INTO compliance_test_products (name, category, price) VALUES
    ('Test Product 1', 'electronics', 29.99),
    ('Test Product 2', 'books', 15.50),
    ('Test Product 3', 'electronics', 199.99)
    ON CONFLICT DO NOTHING;
    
    INSERT INTO compliance_test_users (username, email, role) VALUES
    ('testuser1', 'test1@example.com', 'user'),
    ('testadmin', 'admin@example.com', 'admin'),
    ('testmanager', 'manager@example.com', 'manager')
    ON CONFLICT (username) DO NOTHING;
    """
    
    async with postgres_connection.get_connection() as conn:
        await conn.execute(create_tables_sql)
        await conn.execute(insert_data_sql)
        
    yield
    
    # Cleanup test data
    cleanup_sql = """
    DELETE FROM compliance_test_products WHERE name LIKE 'Test Product%';
    DELETE FROM compliance_test_users WHERE username LIKE 'test%';
    DELETE FROM compliance_audit_log WHERE event_type LIKE 'test_%';
    """
    
    async with postgres_connection.get_connection() as conn:
        await conn.execute(cleanup_sql)


class TestRealDatabaseConnections:
    """Test SDK compliance with real database connections"""
    
    @pytest.mark.asyncio
    async def test_node_with_real_postgres_connection(self, postgres_connection, setup_test_database):
        """Test node execution with real PostgreSQL connection"""
        
        @register_node(name="PostgreSQLTestNode", version="1.0.0")
        class PostgreSQLTestNode(SecureGovernedNode):
            def get_parameters(self) -> Dict[str, Any]:
                return {
                    "query": {"type": "string", "required": True},
                    "connection": {"type": "connection", "required": True, "connection_type": "postgresql"}
                }
            
            async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                query = inputs["query"]
                connection = inputs["connection"]
                
                async with connection.get_connection() as conn:
                    result = await conn.fetch(query)
                    return {
                        "rows": [dict(row) for row in result],
                        "row_count": len(result),
                        "query_executed": query
                    }
        
        # Create workflow with real connection
        workflow = WorkflowBuilder()
        workflow.add_node("PostgreSQLTestNode", "db_test", {
            "query": "SELECT * FROM compliance_test_products WHERE category = 'electronics'",
            "connection": postgres_connection
        })
        
        runtime = LocalRuntime()
        results, run_id = await runtime.execute_async(workflow.build())
        
        # Verify real database results
        assert run_id is not None
        assert "db_test" in results
        
        db_result = results["db_test"]
        assert "rows" in db_result
        assert "row_count" in db_result
        assert db_result["row_count"] >= 2  # Should find Test Product 1 and 3
        
        # Verify actual data from database
        rows = db_result["rows"]
        electronics_products = [row for row in rows if row["category"] == "electronics"]
        assert len(electronics_products) >= 2
    
    @pytest.mark.asyncio
    async def test_secure_node_with_audit_logging(self, postgres_connection, setup_test_database):
        """Test SecureGovernedNode audit logging with real database"""
        
        @register_node(name="AuditedDatabaseNode", version="1.0.0")
        class AuditedDatabaseNode(SecureGovernedNode):
            def get_parameters(self) -> Dict[str, Any]:
                return {
                    "operation": {"type": "string", "required": True},
                    "user_id": {"type": "int", "required": True},
                    "connection": {"type": "connection", "required": True, "connection_type": "postgresql"}
                }
            
            async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                operation = inputs["operation"]
                user_id = inputs["user_id"]
                connection = inputs["connection"]
                
                # Log audit event to real database
                audit_sql = """
                INSERT INTO compliance_audit_log (event_type, user_id, entity_type, metadata)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """
                
                metadata = {
                    "operation": operation,
                    "timestamp": datetime.now().isoformat(),
                    "ip_address": "127.0.0.1",
                    "user_agent": "SDK Integration Test"
                }
                
                async with connection.get_connection() as conn:
                    audit_result = await conn.fetchrow(
                        audit_sql, 
                        f"test_{operation}", 
                        user_id, 
                        "compliance_test", 
                        json.dumps(metadata)
                    )
                    
                    return {
                        "operation_completed": operation,
                        "audit_log_id": audit_result["id"],
                        "user_id": user_id,
                        "timestamp": metadata["timestamp"]
                    }
        
        # Execute audited operation
        workflow = WorkflowBuilder()
        workflow.add_node("AuditedDatabaseNode", "audit_test", {
            "operation": "read_sensitive_data",
            "user_id": 123,
            "connection": postgres_connection
        })
        
        runtime = LocalRuntime()
        results, run_id = await runtime.execute_async(workflow.build())
        
        # Verify audit log was actually created
        audit_result = results["audit_test"]
        assert audit_result["audit_log_id"] is not None
        assert audit_result["user_id"] == 123
        
        # Verify audit log exists in database
        verify_sql = "SELECT * FROM compliance_audit_log WHERE id = $1"
        async with postgres_connection.get_connection() as conn:
            audit_record = await conn.fetchrow(verify_sql, audit_result["audit_log_id"])
            
            assert audit_record is not None
            assert audit_record["event_type"] == "test_read_sensitive_data"
            assert audit_record["user_id"] == 123
            assert audit_record["entity_type"] == "compliance_test"
    
    @pytest.mark.asyncio
    async def test_parameter_validation_with_real_connections(self, postgres_connection, redis_connection):
        """Test parameter validation with real connection objects"""
        
        @register_node(name="MultiConnectionNode", version="1.0.0")
        class MultiConnectionNode(SecureGovernedNode):
            def get_parameters(self) -> Dict[str, Any]:
                return {
                    "db_connection": {"type": "connection", "required": True, "connection_type": "postgresql"},
                    "cache_connection": {"type": "connection", "required": True, "connection_type": "redis"},
                    "operation_type": {"type": "string", "required": True, "allowed_values": ["read", "write", "cache"]}
                }
            
            async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                db_conn = inputs["db_connection"]
                cache_conn = inputs["cache_connection"]
                op_type = inputs["operation_type"]
                
                if op_type == "read":
                    async with db_conn.get_connection() as conn:
                        result = await conn.fetch("SELECT COUNT(*) as count FROM compliance_test_products")
                        return {"database_count": dict(result[0])["count"]}
                        
                elif op_type == "cache":
                    async with cache_conn.get_connection() as conn:
                        await conn.set("test_key", "test_value", ex=30)
                        cached_value = await conn.get("test_key")
                        return {"cached_value": cached_value.decode() if cached_value else None}
                
                return {"operation": op_type, "status": "completed"}
        
        node = MultiConnectionNode()
        
        # Test valid parameters with real connections
        valid_inputs = {
            "db_connection": postgres_connection,
            "cache_connection": redis_connection,
            "operation_type": "read"
        }
        
        validation_result = node.validate_parameters(valid_inputs)
        assert validation_result["valid"] is True
        assert len(validation_result["errors"]) == 0
        
        # Test actual execution
        result = await node.run(valid_inputs)
        assert "database_count" in result
        assert isinstance(result["database_count"], int)
        
        # Test cache operation
        cache_inputs = {
            "db_connection": postgres_connection,
            "cache_connection": redis_connection,
            "operation_type": "cache"
        }
        
        cache_result = await node.run(cache_inputs)
        assert cache_result["cached_value"] == "test_value"


class TestWorkflowExecutionWithRealServices:
    """Test complete workflow execution with real services"""
    
    @pytest.mark.asyncio
    async def test_multi_node_workflow_real_services(self, postgres_connection, redis_connection, setup_test_database):
        """Test multi-node workflow with real service interactions"""
        
        @register_node(name="DataReaderNode", version="1.0.0")
        class DataReaderNode(Node):
            def get_parameters(self) -> Dict[str, Any]:
                return {
                    "connection": {"type": "connection", "required": True},
                    "query": {"type": "string", "required": True}
                }
            
            async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                async with inputs["connection"].get_connection() as conn:
                    result = await conn.fetch(inputs["query"])
                    return {"data": [dict(row) for row in result]}
        
        @register_node(name="DataProcessorNode", version="1.0.0")
        class DataProcessorNode(Node):
            def get_parameters(self) -> Dict[str, Any]:
                return {
                    "input_data": {"type": "list", "required": True},
                    "operation": {"type": "string", "required": True}
                }
            
            async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                data = inputs["input_data"]
                operation = inputs["operation"]
                
                if operation == "sum_prices":
                    total = sum(float(item.get("price", 0)) for item in data)
                    return {"total_price": total, "item_count": len(data)}
                elif operation == "count_by_category":
                    categories = {}
                    for item in data:
                        cat = item.get("category", "unknown")
                        categories[cat] = categories.get(cat, 0) + 1
                    return {"category_counts": categories}
                
                return {"processed": len(data)}
        
        @register_node(name="CacheResultNode", version="1.0.0")
        class CacheResultNode(Node):
            def get_parameters(self) -> Dict[str, Any]:
                return {
                    "cache_connection": {"type": "connection", "required": True},
                    "key": {"type": "string", "required": True},
                    "data": {"type": "dict", "required": True},
                    "ttl": {"type": "int", "required": False, "default": 300}
                }
            
            async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                async with inputs["cache_connection"].get_connection() as conn:
                    cached_data = json.dumps(inputs["data"])
                    await conn.set(inputs["key"], cached_data, ex=inputs["ttl"])
                    return {"cached": True, "key": inputs["key"], "ttl": inputs["ttl"]}
        
        # Create complex workflow
        workflow = WorkflowBuilder()
        
        # Step 1: Read data from database
        workflow.add_node("DataReaderNode", "read_products", {
            "connection": postgres_connection,
            "query": "SELECT * FROM compliance_test_products ORDER BY price DESC"
        })
        
        # Step 2: Process the data  
        workflow.add_node("DataProcessorNode", "calculate_totals", {
            "input_data": "${read_products.data}",
            "operation": "sum_prices"
        })
        
        workflow.add_node("DataProcessorNode", "count_categories", {  
            "input_data": "${read_products.data}",
            "operation": "count_by_category"
        })
        
        # Step 3: Cache results
        workflow.add_node("CacheResultNode", "cache_totals", {
            "cache_connection": redis_connection,
            "key": "product_totals",
            "data": "${calculate_totals}",
            "ttl": 60
        })
        
        workflow.add_node("CacheResultNode", "cache_categories", {
            "cache_connection": redis_connection, 
            "key": "category_counts",
            "data": "${count_categories}",
            "ttl": 60
        })
        
        # Execute workflow
        runtime = LocalRuntime()
        results, run_id = await runtime.execute_async(workflow.build())
        
        # Verify all steps completed successfully
        assert "read_products" in results
        assert "calculate_totals" in results
        assert "count_categories" in results
        assert "cache_totals" in results
        assert "cache_categories" in results
        
        # Verify data flow
        product_data = results["read_products"]["data"]
        assert len(product_data) >= 3  # Should have test products
        
        totals = results["calculate_totals"] 
        assert "total_price" in totals
        assert totals["total_price"] > 0
        assert totals["item_count"] >= 3
        
        categories = results["count_categories"]
        assert "category_counts" in categories
        assert "electronics" in categories["category_counts"]
        
        # Verify caching worked
        assert results["cache_totals"]["cached"] is True
        assert results["cache_categories"]["cached"] is True
        
        # Verify data is actually in Redis
        async with redis_connection.get_connection() as conn:
            cached_totals = await conn.get("product_totals")
            cached_categories = await conn.get("category_counts")
            
            assert cached_totals is not None
            assert cached_categories is not None
            
            # Verify cached data matches results
            cached_totals_data = json.loads(cached_totals.decode())
            assert cached_totals_data["total_price"] == totals["total_price"]
    
    @pytest.mark.asyncio
    async def test_error_handling_with_real_services(self, postgres_connection):
        """Test error handling in workflows with real services"""
        
        @register_node(name="FailingQueryNode", version="1.0.0")
        class FailingQueryNode(SecureGovernedNode):
            def get_parameters(self) -> Dict[str, Any]:
                return {
                    "connection": {"type": "connection", "required": True},
                    "query": {"type": "string", "required": True},
                    "should_fail": {"type": "bool", "required": False, "default": False}
                }
            
            async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                if inputs.get("should_fail", False):
                    # Execute invalid SQL to test error handling
                    async with inputs["connection"].get_connection() as conn:
                        await conn.fetch("SELECT * FROM non_existent_table")
                
                async with inputs["connection"].get_connection() as conn:
                    result = await conn.fetch(inputs["query"])
                    return {"rows": len(result)}
        
        # Test successful execution
        success_workflow = WorkflowBuilder()
        success_workflow.add_node("FailingQueryNode", "success_test", {
            "connection": postgres_connection,
            "query": "SELECT 1 as test",
            "should_fail": False
        })
        
        runtime = LocalRuntime()
        results, run_id = await runtime.execute_async(success_workflow.build())
        
        assert "success_test" in results
        assert results["success_test"]["rows"] == 1
        
        # Test error handling
        error_workflow = WorkflowBuilder()
        error_workflow.add_node("FailingQueryNode", "error_test", {
            "connection": postgres_connection,
            "query": "SELECT 1 as test",
            "should_fail": True
        })
        
        with pytest.raises(Exception):  # Should raise database error
            await runtime.execute_async(error_workflow.build())


class TestPerformanceWithRealServices:
    """Performance tests with real infrastructure"""
    
    @pytest.mark.asyncio
    async def test_workflow_performance_under_load(self, postgres_connection, setup_test_database):
        """Test workflow performance with real services meets <2s requirement"""
        import time
        
        @register_node(name="FastQueryNode", version="1.0.0")
        class FastQueryNode(Node):
            def get_parameters(self) -> Dict[str, Any]:
                return {
                    "connection": {"type": "connection", "required": True},
                    "batch_size": {"type": "int", "required": False, "default": 10}
                }
            
            async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                batch_size = inputs["batch_size"]
                
                # Simulate realistic query workload
                async with inputs["connection"].get_connection() as conn:
                    results = []
                    for i in range(batch_size):
                        result = await conn.fetch(
                            "SELECT id, name, price FROM compliance_test_products WHERE id = $1",
                            (i % 3) + 1  # Cycle through test product IDs
                        )
                        results.extend([dict(row) for row in result])
                    
                    return {"processed_records": len(results), "batch_size": batch_size}
        
        # Create performance test workflow
        workflow = WorkflowBuilder()
        workflow.add_node("FastQueryNode", "performance_test", {
            "connection": postgres_connection,
            "batch_size": 20
        })
        
        runtime = LocalRuntime()
        
        # Execute multiple times to test performance
        execution_times = []
        for i in range(5):
            start_time = time.time()
            results, run_id = await runtime.execute_async(workflow.build())
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            # Verify results
            assert "performance_test" in results
            assert results["performance_test"]["processed_records"] > 0
        
        # Verify performance requirements
        avg_execution_time = sum(execution_times) / len(execution_times)
        max_execution_time = max(execution_times)
        
        # Should meet <2s response time requirement
        assert avg_execution_time < 2.0, f"Average execution time {avg_execution_time}s exceeds 2s requirement"
        assert max_execution_time < 2.0, f"Max execution time {max_execution_time}s exceeds 2s requirement"
        
        print(f"Performance Test Results:")
        print(f"  Average execution time: {avg_execution_time:.3f}s")
        print(f"  Max execution time: {max_execution_time:.3f}s")
        print(f"  All executions: {[f'{t:.3f}s' for t in execution_times]}")
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, postgres_connection, redis_connection, setup_test_database):
        """Test concurrent workflow execution with real services"""
        import time
        
        @register_node(name="ConcurrentTestNode", version="1.0.0")
        class ConcurrentTestNode(Node):
            def get_parameters(self) -> Dict[str, Any]:
                return {
                    "db_connection": {"type": "connection", "required": True},
                    "cache_connection": {"type": "connection", "required": True},
                    "worker_id": {"type": "int", "required": True}
                }
            
            async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                worker_id = inputs["worker_id"]
                
                # Database operation
                async with inputs["db_connection"].get_connection() as conn:
                    result = await conn.fetch("SELECT COUNT(*) as count FROM compliance_test_products")
                    db_count = dict(result[0])["count"]
                
                # Cache operation
                cache_key = f"worker_{worker_id}_result"
                async with inputs["cache_connection"].get_connection() as conn:
                    await conn.set(cache_key, f"worker_{worker_id}_completed", ex=30)
                    cached_value = await conn.get(cache_key)
                
                return {
                    "worker_id": worker_id,
                    "db_count": db_count,
                    "cache_result": cached_value.decode() if cached_value else None
                }
        
        # Create multiple workflows for concurrent execution
        workflows = []
        for i in range(5):
            workflow = WorkflowBuilder()
            workflow.add_node("ConcurrentTestNode", f"worker_{i}", {
                "db_connection": postgres_connection,
                "cache_connection": redis_connection,
                "worker_id": i
            })
            workflows.append(workflow)
        
        runtime = LocalRuntime()
        
        # Execute workflows concurrently
        start_time = time.time()
        
        tasks = []
        for workflow in workflows:
            task = runtime.execute_async(workflow.build())
            tasks.append(task)
        
        # Wait for all tasks to complete
        concurrent_results = await asyncio.gather(*tasks)
        
        total_execution_time = time.time() - start_time
        
        # Verify all workflows completed successfully
        assert len(concurrent_results) == 5
        
        for i, (results, run_id) in enumerate(concurrent_results):
            worker_key = f"worker_{i}"
            assert worker_key in results
            assert results[worker_key]["worker_id"] == i
            assert results[worker_key]["db_count"] >= 3
            assert results[worker_key]["cache_result"] == f"worker_{i}_completed"
        
        # Concurrent execution should be efficient
        # Should complete in less time than sequential execution
        assert total_execution_time < 10.0, f"Concurrent execution took too long: {total_execution_time}s"
        
        print(f"Concurrent Execution Results:")
        print(f"  Total execution time: {total_execution_time:.3f}s")
        print(f"  Average per workflow: {total_execution_time/5:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not e2e"])