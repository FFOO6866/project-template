"""
Tier 1 (Unit) Tests for Testing Infrastructure
===========================================

Fast, isolated unit tests for testing infrastructure components.
Tests individual components without external dependencies.
Maximum execution time: <1 second per test.

Coverage:
- Docker configuration validation
- Test data factory validation  
- Performance monitoring utilities
- Compliance checking utilities
- Test environment configuration
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import test infrastructure components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "test-data"))

from test_data_factory import (
    ProductDataFactory,
    KnowledgeGraphDataFactory,
    PerformanceTestDataFactory,
    Product,
    UserProfile,
    SafetyStandard,
    KnowledgeGraphNode,
    KnowledgeGraphRelationship
)


class TestDockerConfigurationValidation:
    """Test Docker test environment configuration"""
    
    def test_docker_compose_file_exists(self):
        """Test that docker-compose.test.yml exists and is readable"""
        docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.test.yml"
        
        assert docker_compose_path.exists(), "docker-compose.test.yml file not found"
        assert docker_compose_path.is_file(), "docker-compose.test.yml is not a file"
        
        # Test file is readable
        with open(docker_compose_path, 'r') as f:
            content = f.read()
            assert len(content) > 0, "docker-compose.test.yml is empty"
    
    def test_docker_compose_yaml_structure(self):
        """Test that docker-compose.test.yml has valid YAML structure"""
        import yaml
        
        docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.test.yml"
        
        with open(docker_compose_path, 'r') as f:
            try:
                config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in docker-compose.test.yml: {e}")
        
        # Test required sections exist
        assert 'services' in config, "services section missing from docker-compose.test.yml"
        assert 'volumes' in config, "volumes section missing from docker-compose.test.yml"
        assert 'networks' in config, "networks section missing from docker-compose.test.yml"
    
    def test_required_services_defined(self):
        """Test that all required services are defined in docker-compose"""
        import yaml
        
        docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.test.yml"
        
        with open(docker_compose_path, 'r') as f:
            config = yaml.safe_load(f)
        
        required_services = [
            'postgres-test',
            'neo4j-test', 
            'chromadb-test',
            'redis-test',
            'openai-mock'
        ]
        
        services = config.get('services', {})
        
        for service in required_services:
            assert service in services, f"Required service '{service}' not found in docker-compose.test.yml"
    
    def test_service_port_configuration(self):
        """Test that services have correct port configurations"""
        import yaml
        
        docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.test.yml"
        
        with open(docker_compose_path, 'r') as f:
            config = yaml.safe_load(f)
        
        expected_ports = {
            'postgres-test': ['5433:5432'],
            'neo4j-test': ['7475:7474', '7688:7687'],
            'chromadb-test': ['8001:8000'],
            'redis-test': ['6381:6379'],
            'openai-mock': ['8002:8080']
        }
        
        services = config.get('services', {})
        
        for service_name, expected_port_mappings in expected_ports.items():
            service_config = services.get(service_name, {})
            service_ports = service_config.get('ports', [])
            
            for expected_port in expected_port_mappings:
                assert expected_port in service_ports, \
                    f"Service '{service_name}' missing port mapping '{expected_port}'"
    
    def test_service_health_checks(self):
        """Test that critical services have health checks defined"""
        import yaml
        
        docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.test.yml"
        
        with open(docker_compose_path, 'r') as f:
            config = yaml.safe_load(f)
        
        services_requiring_healthcheck = [
            'postgres-test',
            'neo4j-test',
            'chromadb-test',
            'redis-test'
        ]
        
        services = config.get('services', {})
        
        for service_name in services_requiring_healthcheck:
            service_config = services.get(service_name, {})
            assert 'healthcheck' in service_config, \
                f"Service '{service_name}' missing health check configuration"
            
            healthcheck = service_config['healthcheck']
            assert 'test' in healthcheck, f"Service '{service_name}' healthcheck missing 'test' command"
            assert 'interval' in healthcheck, f"Service '{service_name}' healthcheck missing 'interval'"
            assert 'timeout' in healthcheck, f"Service '{service_name}' healthcheck missing 'timeout'"
            assert 'retries' in healthcheck, f"Service '{service_name}' healthcheck missing 'retries'"


class TestProductDataFactory:
    """Test product data generation factory"""
    
    def test_create_products_returns_list(self):
        """Test that create_products returns a list of Product objects"""
        products = ProductDataFactory.create_products(5)
        
        assert isinstance(products, list), "create_products should return a list"
        assert len(products) == 5, "Should return exactly 5 products"
        
        for product in products:
            assert isinstance(product, Product), "Each item should be a Product instance"
    
    def test_product_data_structure(self):
        """Test that generated products have required fields"""
        products = ProductDataFactory.create_products(1)
        product = products[0]
        
        # Test required fields exist and have correct types
        assert hasattr(product, 'product_code'), "Product missing product_code"
        assert hasattr(product, 'name'), "Product missing name"
        assert hasattr(product, 'category'), "Product missing category"
        assert hasattr(product, 'price'), "Product missing price"
        assert hasattr(product, 'unspsc_code'), "Product missing unspsc_code"
        assert hasattr(product, 'safety_standards'), "Product missing safety_standards"
        assert hasattr(product, 'embedding_vector'), "Product missing embedding_vector"
        
        # Test field types
        assert isinstance(product.product_code, str), "product_code should be string"
        assert isinstance(product.price, float), "price should be float"
        assert isinstance(product.safety_standards, list), "safety_standards should be list"
        assert isinstance(product.embedding_vector, list), "embedding_vector should be list"
        assert len(product.embedding_vector) == 384, "embedding_vector should have 384 dimensions"
    
    def test_product_code_uniqueness(self):
        """Test that product codes are unique"""
        products = ProductDataFactory.create_products(100)
        product_codes = [p.product_code for p in products]
        
        assert len(product_codes) == len(set(product_codes)), "Product codes should be unique"
    
    def test_price_range_validation(self):
        """Test that product prices are within expected range"""
        products = ProductDataFactory.create_products(50)
        
        for product in products:
            assert 10 <= product.price <= 3000, f"Price {product.price} outside expected range (10-3000)"
            assert product.price == round(product.price, 2), "Price should have at most 2 decimal places"
    
    def test_safety_standards_validation(self):
        """Test that safety standards are from predefined list"""
        products = ProductDataFactory.create_products(20)
        valid_standards = set(ProductDataFactory.SAFETY_STANDARDS)
        
        for product in products:
            for standard in product.safety_standards:
                assert standard in valid_standards, f"Invalid safety standard: {standard}"
    
    def test_skill_level_validation(self):
        """Test that skill levels are from predefined list"""
        products = ProductDataFactory.create_products(20)
        valid_levels = set(ProductDataFactory.SKILL_LEVELS)
        
        for product in products:
            assert product.skill_level_required in valid_levels, \
                f"Invalid skill level: {product.skill_level_required}"
    
    def test_complexity_score_range(self):
        """Test that complexity scores are within valid range"""
        products = ProductDataFactory.create_products(30)
        
        for product in products:
            assert 1 <= product.complexity_score <= 10, \
                f"Complexity score {product.complexity_score} outside range (1-10)"
    
    def test_embedding_vector_properties(self):
        """Test that embedding vectors have correct properties"""
        products = ProductDataFactory.create_products(5)
        
        for product in products:
            vector = product.embedding_vector
            assert len(vector) == 384, "Embedding vector should have 384 dimensions"
            assert all(isinstance(v, float) for v in vector), "All vector elements should be floats"
            
            # Test vector is normalized-ish (values between -3 and 3 for normal distribution)
            assert all(-5 <= v <= 5 for v in vector), "Vector values outside expected range"


class TestUserProfileFactory:
    """Test user profile data generation"""
    
    def test_create_user_profiles_returns_list(self):
        """Test that create_user_profiles returns list of UserProfile objects"""
        users = ProductDataFactory.create_user_profiles(3)
        
        assert isinstance(users, list), "create_user_profiles should return a list"
        assert len(users) == 3, "Should return exactly 3 users"
        
        for user in users:
            assert isinstance(user, UserProfile), "Each item should be a UserProfile instance"
    
    def test_user_profile_data_structure(self):
        """Test that generated user profiles have required fields"""
        users = ProductDataFactory.create_user_profiles(1)
        user = users[0]
        
        # Test required fields exist
        required_fields = [
            'user_id', 'username', 'email', 'role', 'skill_level',
            'experience_years', 'certifications', 'safety_training',
            'preferred_categories', 'location', 'created_at'
        ]
        
        for field in required_fields:
            assert hasattr(user, field), f"UserProfile missing field: {field}"
    
    def test_user_email_format(self):
        """Test that user emails have valid format"""
        users = ProductDataFactory.create_user_profiles(10)
        
        for user in users:
            email = user.email
            assert '@' in email, f"Invalid email format: {email}"
            assert '.' in email.split('@')[1], f"Invalid email domain: {email}"
    
    def test_experience_years_range(self):
        """Test that experience years are within reasonable range"""
        users = ProductDataFactory.create_user_profiles(20)
        
        for user in users:
            assert 0 <= user.experience_years <= 30, \
                f"Experience years {user.experience_years} outside range (0-30)"
    
    def test_user_id_uniqueness(self):
        """Test that user IDs are unique"""
        users = ProductDataFactory.create_user_profiles(50)
        user_ids = [u.user_id for u in users]
        
        assert len(user_ids) == len(set(user_ids)), "User IDs should be unique"


class TestSafetyStandardFactory:
    """Test safety standard data generation"""
    
    def test_create_safety_standards_returns_list(self):
        """Test that create_safety_standards returns list of SafetyStandard objects"""
        standards = ProductDataFactory.create_safety_standards(5)
        
        assert isinstance(standards, list), "create_safety_standards should return a list"
        assert len(standards) == 5, "Should return exactly 5 standards"
        
        for standard in standards:
            assert isinstance(standard, SafetyStandard), "Each item should be a SafetyStandard instance"
    
    def test_safety_standard_structure(self):
        """Test that safety standards have required fields"""
        standards = ProductDataFactory.create_safety_standards(1)
        standard = standards[0]
        
        required_fields = [
            'standard_id', 'name', 'organization', 'category',
            'description', 'requirements', 'applicable_products',
            'compliance_level', 'last_updated'
        ]
        
        for field in required_fields:
            assert hasattr(standard, field), f"SafetyStandard missing field: {field}"
    
    def test_safety_organization_values(self):
        """Test that safety organizations are from expected values"""
        standards = ProductDataFactory.create_safety_standards(20)
        valid_orgs = {"OSHA", "ANSI", "ISO", "NFPA", "ASTM"}
        
        for standard in standards:
            assert standard.organization in valid_orgs, \
                f"Invalid organization: {standard.organization}"
    
    def test_compliance_level_values(self):
        """Test that compliance levels are from expected values"""
        standards = ProductDataFactory.create_safety_standards(15)
        valid_levels = {"mandatory", "recommended", "advisory"}
        
        for standard in standards:
            assert standard.compliance_level in valid_levels, \
                f"Invalid compliance level: {standard.compliance_level}"


class TestKnowledgeGraphDataFactory:
    """Test knowledge graph data generation"""
    
    def test_create_nodes_returns_list(self):
        """Test that create_nodes returns list of KnowledgeGraphNode objects"""
        nodes = KnowledgeGraphDataFactory.create_nodes(5)
        
        assert isinstance(nodes, list), "create_nodes should return a list"
        assert len(nodes) == 5, "Should return exactly 5 nodes"
        
        for node in nodes:
            assert isinstance(node, KnowledgeGraphNode), "Each item should be a KnowledgeGraphNode instance"
    
    def test_node_structure(self):
        """Test that knowledge graph nodes have required fields"""
        nodes = KnowledgeGraphDataFactory.create_nodes(1)
        node = nodes[0]
        
        assert hasattr(node, 'node_id'), "Node missing node_id"
        assert hasattr(node, 'node_type'), "Node missing node_type"
        assert hasattr(node, 'name'), "Node missing name"
        assert hasattr(node, 'properties'), "Node missing properties"
        
        assert isinstance(node.properties, dict), "Node properties should be dict"
    
    def test_node_types_validation(self):
        """Test that node types are from predefined list"""
        nodes = KnowledgeGraphDataFactory.create_nodes(30)
        valid_types = set(KnowledgeGraphDataFactory.NODE_TYPES)
        
        for node in nodes:
            assert node.node_type in valid_types, f"Invalid node type: {node.node_type}"
    
    def test_create_relationships_returns_list(self):
        """Test that create_relationships returns list of KnowledgeGraphRelationship objects"""
        nodes = KnowledgeGraphDataFactory.create_nodes(10)
        relationships = KnowledgeGraphDataFactory.create_relationships(nodes, 5)
        
        assert isinstance(relationships, list), "create_relationships should return a list"
        assert len(relationships) == 5, "Should return exactly 5 relationships"
        
        for rel in relationships:
            assert isinstance(rel, KnowledgeGraphRelationship), \
                "Each item should be a KnowledgeGraphRelationship instance"
    
    def test_relationship_structure(self):
        """Test that relationships have required fields"""
        nodes = KnowledgeGraphDataFactory.create_nodes(10)
        relationships = KnowledgeGraphDataFactory.create_relationships(nodes, 1)
        rel = relationships[0]
        
        assert hasattr(rel, 'source_id'), "Relationship missing source_id"
        assert hasattr(rel, 'target_id'), "Relationship missing target_id"
        assert hasattr(rel, 'relationship_type'), "Relationship missing relationship_type"
        assert hasattr(rel, 'properties'), "Relationship missing properties"
        
        assert isinstance(rel.properties, dict), "Relationship properties should be dict"
    
    def test_relationship_types_validation(self):
        """Test that relationship types are from predefined list"""
        nodes = KnowledgeGraphDataFactory.create_nodes(20)
        relationships = KnowledgeGraphDataFactory.create_relationships(nodes, 10)
        valid_types = set(KnowledgeGraphDataFactory.RELATIONSHIP_TYPES)
        
        for rel in relationships:
            assert rel.relationship_type in valid_types, \
                f"Invalid relationship type: {rel.relationship_type}"
    
    def test_no_self_relationships(self):
        """Test that relationships don't create self-loops"""
        nodes = KnowledgeGraphDataFactory.create_nodes(10)
        relationships = KnowledgeGraphDataFactory.create_relationships(nodes, 20)
        
        for rel in relationships:
            assert rel.source_id != rel.target_id, \
                f"Self-relationship found: {rel.source_id} -> {rel.target_id}"


class TestPerformanceTestDataFactory:
    """Test performance testing data generation"""
    
    def test_create_load_test_data_structure(self):
        """Test that load test data has correct structure"""
        data = PerformanceTestDataFactory.create_load_test_data(10, 50)
        
        required_keys = [
            'users', 'products', 'search_queries', 'concurrent_users',
            'total_requests', 'target_rps', 'duration_seconds'
        ]
        
        for key in required_keys:
            assert key in data, f"Load test data missing key: {key}"
    
    def test_load_test_data_counts(self):
        """Test that load test data has correct counts"""
        user_count, request_count = 20, 100
        data = PerformanceTestDataFactory.create_load_test_data(user_count, request_count)
        
        assert len(data['users']) == user_count, f"Expected {user_count} users"
        assert len(data['products']) == request_count, f"Expected {request_count} products"
        assert len(data['search_queries']) == request_count, f"Expected {request_count} queries"
        assert data['concurrent_users'] == user_count, "Concurrent users count mismatch"
        assert data['total_requests'] == request_count, "Total requests count mismatch"
    
    def test_search_query_types(self):
        """Test that search queries have valid types"""
        data = PerformanceTestDataFactory.create_load_test_data(5, 30)
        valid_query_types = {"search", "recommendation", "safety_check"}
        
        for query in data['search_queries']:
            assert 'type' in query, "Query missing type field"
            assert query['type'] in valid_query_types, f"Invalid query type: {query['type']}"


class TestPerformanceMonitoring:
    """Test performance monitoring utilities from conftest.py"""
    
    @pytest.fixture
    def mock_performance_monitor(self):
        """Create a mock performance monitor for testing"""
        class MockPerformanceMonitor:
            def __init__(self):
                self.measurements = []
                self.start_time = None
                self.end_time = None
            
            def start(self, operation_name="test"):
                import time
                self.start_time = time.time()
                return self
            
            def stop(self, operation_name="test"):
                import time
                self.end_time = time.time()
                duration = self.end_time - self.start_time
                self.measurements.append({
                    "operation": operation_name,
                    "duration": duration,
                    "timestamp": self.end_time
                })
                return duration
            
            def assert_within_threshold(self, threshold, operation_name="test"):
                if not self.measurements:
                    raise ValueError("No measurements recorded")
                latest = self.measurements[-1]
                assert latest["duration"] < threshold, \
                    f"{operation_name} took {latest['duration']:.3f}s, exceeds {threshold}s threshold"
        
        return MockPerformanceMonitor()
    
    def test_performance_monitor_start_stop(self, mock_performance_monitor):
        """Test that performance monitor can start and stop timing"""
        monitor = mock_performance_monitor
        
        monitor.start("test_operation")
        import time
        time.sleep(0.01)  # Sleep for 10ms
        duration = monitor.stop("test_operation")
        
        assert duration > 0, "Duration should be positive"
        assert duration < 1.0, "Duration should be less than 1 second for this test"
        assert len(monitor.measurements) == 1, "Should have one measurement"
    
    def test_performance_monitor_threshold_validation(self, mock_performance_monitor):
        """Test that performance monitor correctly validates thresholds"""
        monitor = mock_performance_monitor
        
        # Simulate a fast operation
        monitor.start("fast_operation")
        import time
        time.sleep(0.001)  # 1ms
        monitor.stop("fast_operation")
        
        # Should pass threshold check
        monitor.assert_within_threshold(0.1, "fast_operation")  # 100ms threshold
        
        # Should fail threshold check
        with pytest.raises(AssertionError):
            monitor.assert_within_threshold(0.0001, "fast_operation")  # 0.1ms threshold


class TestComplianceValidation:
    """Test compliance validation utilities from conftest.py"""
    
    @pytest.fixture
    def mock_compliance_validator(self):
        """Create a mock compliance validator for testing"""
        class MockComplianceValidator:
            def __init__(self):
                self.violations = []
                self.checks_performed = []
            
            def check_node_registration(self, node_class):
                check_name = f"node_registration_{node_class.__name__}"
                self.checks_performed.append(check_name)
                
                if not hasattr(node_class, '_node_metadata'):
                    self.violations.append({
                        "type": "missing_registration",
                        "message": f"Node {node_class.__name__} missing @register_node decorator",
                        "severity": "high"
                    })
                    return False
                return True
            
            def assert_compliant(self):
                if self.violations:
                    violation_summary = "\n".join([
                        f"  - {v['type']}: {v['message']}" for v in self.violations
                    ])
                    raise AssertionError(f"SDK Compliance violations found:\n{violation_summary}")
        
        return MockComplianceValidator()
    
    def test_compliance_validator_node_registration_pass(self, mock_compliance_validator):
        """Test compliance validator passes for properly registered nodes"""
        validator = mock_compliance_validator
        
        # Mock a properly registered node
        class TestNode:
            _node_metadata = {"name": "TestNode", "version": "1.0"}
        
        result = validator.check_node_registration(TestNode)
        
        assert result is True, "Should pass compliance check for registered node"
        assert len(validator.violations) == 0, "Should have no violations"
        assert len(validator.checks_performed) == 1, "Should have performed one check"
    
    def test_compliance_validator_node_registration_fail(self, mock_compliance_validator):
        """Test compliance validator fails for unregistered nodes"""
        validator = mock_compliance_validator
        
        # Mock an unregistered node
        class UnregisteredNode:
            pass
        
        result = validator.check_node_registration(UnregisteredNode)
        
        assert result is False, "Should fail compliance check for unregistered node"
        assert len(validator.violations) == 1, "Should have one violation"
        assert validator.violations[0]["type"] == "missing_registration"
    
    def test_compliance_validator_assert_compliant_pass(self, mock_compliance_validator):
        """Test assert_compliant passes when no violations"""
        validator = mock_compliance_validator
        
        # No violations added
        validator.assert_compliant()  # Should not raise
    
    def test_compliance_validator_assert_compliant_fail(self, mock_compliance_validator):
        """Test assert_compliant fails when violations exist"""
        validator = mock_compliance_validator
        
        # Add a violation
        validator.violations.append({
            "type": "test_violation",
            "message": "Test violation message"
        })
        
        with pytest.raises(AssertionError) as exc_info:
            validator.assert_compliant()
        
        assert "SDK Compliance violations found" in str(exc_info.value)


class TestTestEnvironmentConfiguration:
    """Test test environment configuration utilities"""
    
    def test_test_data_directory_structure(self):
        """Test that test data directory has expected structure"""
        test_data_dir = Path(__file__).parent.parent.parent / "test-data"
        
        assert test_data_dir.exists(), "test-data directory should exist"
        assert test_data_dir.is_dir(), "test-data should be a directory"
        
        # Check for required subdirectories
        required_dirs = ["postgres", "neo4j", "wiremock"]
        for dir_name in required_dirs:
            dir_path = test_data_dir / dir_name
            assert dir_path.exists(), f"Required directory '{dir_name}' not found in test-data"
    
    def test_postgres_init_script_exists(self):
        """Test that PostgreSQL initialization script exists"""
        postgres_dir = Path(__file__).parent.parent.parent / "test-data" / "postgres"
        init_script = postgres_dir / "01-init-schema.sql"
        
        assert init_script.exists(), "PostgreSQL init script not found"
        assert init_script.is_file(), "PostgreSQL init script should be a file"
        
        # Test script has content
        with open(init_script, 'r') as f:
            content = f.read()
            assert len(content) > 0, "PostgreSQL init script is empty"
            assert "CREATE TABLE" in content, "Init script should contain table creation"
    
    def test_neo4j_init_script_exists(self):
        """Test that Neo4j initialization script exists"""
        neo4j_dir = Path(__file__).parent.parent.parent / "test-data" / "neo4j"
        init_script = neo4j_dir / "init-knowledge-graph.cypher"
        
        assert init_script.exists(), "Neo4j init script not found"
        assert init_script.is_file(), "Neo4j init script should be a file"
        
        # Test script has content
        with open(init_script, 'r') as f:
            content = f.read()
            assert len(content) > 0, "Neo4j init script is empty"
            assert "CREATE" in content, "Init script should contain Cypher CREATE statements"
    
    def test_wiremock_mappings_exist(self):
        """Test that WireMock API mappings exist"""
        wiremock_dir = Path(__file__).parent.parent.parent / "test-data" / "wiremock" / "mappings"
        
        required_mappings = [
            "openai-chat-completion.json",
            "openai-embeddings.json"
        ]
        
        for mapping_file in required_mappings:
            mapping_path = wiremock_dir / mapping_file
            assert mapping_path.exists(), f"WireMock mapping '{mapping_file}' not found"
            
            # Test mapping has valid JSON
            with open(mapping_path, 'r') as f:
                try:
                    mapping_config = json.load(f)
                    assert 'request' in mapping_config, f"Mapping '{mapping_file}' missing request config"
                    assert 'response' in mapping_config, f"Mapping '{mapping_file}' missing response config"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in mapping '{mapping_file}': {e}")


@pytest.mark.unit
@pytest.mark.performance
class TestPerformanceRequirements:
    """Test that unit tests meet performance requirements"""
    
    def test_unit_test_execution_time(self, performance_monitor):
        """Test that unit tests execute within time limits"""
        # This test validates that our test infrastructure tests are fast enough
        
        monitor = performance_monitor.start("unit_test_simulation")
        
        # Simulate unit test work
        products = ProductDataFactory.create_products(10)
        users = ProductDataFactory.create_user_profiles(5)
        
        duration = monitor.stop("unit_test_simulation")
        
        # Unit tests should complete in <1 second
        assert duration < 1.0, f"Unit test took {duration:.3f}s, exceeds 1s limit"
    
    def test_data_generation_performance(self, performance_monitor):
        """Test that test data generation is performant"""
        monitor = performance_monitor.start("data_generation")
        
        # Generate reasonable amount of test data
        ProductDataFactory.create_products(100)
        ProductDataFactory.create_user_profiles(50)
        ProductDataFactory.create_safety_standards(25)
        
        duration = monitor.stop("data_generation")
        
        # Data generation should be fast for unit tests
        assert duration < 0.5, f"Data generation took {duration:.3f}s, exceeds 0.5s limit"


if __name__ == "__main__":
    # Run tests directly for debugging
    pytest.main([__file__, "-v", "--tb=short"])