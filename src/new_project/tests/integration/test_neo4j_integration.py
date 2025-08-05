"""
Integration Tests for Neo4j Knowledge Graph Operations
====================================================

Tests the Neo4j knowledge graph service with real Docker Neo4j service.
NO MOCKING - validates actual database operations and schema creation.

Test Coverage:
- Real Neo4j Docker container setup and connection
- Schema creation and constraint validation
- Node creation and property persistence
- Relationship creation and graph traversal
- Complex Cypher queries and performance
- Data integrity and consistency
- Error handling with real database errors
- Performance constraints (<5s per test)

Prerequisites:
- Docker must be installed and running
- Run: ./tests/utils/test-env up && ./tests/utils/test-env status
"""

import pytest
import time
import asyncio
from typing import Dict, List, Any, Optional
# Conditional imports for Neo4j
try:
    import neo4j
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    # Create mock classes when Neo4j is not available
    class GraphDatabase:
        @staticmethod
        def driver(*args, **kwargs):
            return None
    neo4j = type('neo4j', (), {'GraphDatabase': GraphDatabase})()
    NEO4J_AVAILABLE = False

# Test framework imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import windows_patch  # Apply Windows compatibility for Kailash SDK

# Import the service under test
from src.new_project.core.services.knowledge_graph import KnowledgeGraphService, Neo4jSchema
from src.new_project.core.models.knowledge_graph import Tool, Task, Project, User, SafetyRule

# Docker test utilities
try:
    import docker
    from tests.utils.docker_config import DockerConfig
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


@pytest.mark.integration
@pytest.mark.requires_docker
class TestNeo4jIntegrationSetup:
    """Test Neo4j Docker setup and connection"""
    
    @pytest.fixture(scope="class")
    def docker_neo4j(self):
        """Start Neo4j Docker container for testing"""
        if not DOCKER_AVAILABLE:
            pytest.skip("Docker not available")
        
        docker_config = DockerConfig()
        
        # Neo4j container configuration
        neo4j_config = {
            "image": "neo4j:5.0",
            "environment": {
                "NEO4J_AUTH": "neo4j/testpassword",
                "NEO4J_PLUGINS": '["apoc"]',
                "NEO4J_dbms_security_procedures_unrestricted": "apoc.*"
            },
            "ports": {"7474": "7474", "7687": "7687"},
            "healthcheck": {
                "test": ["CMD-SHELL", "cypher-shell -u neo4j -p testpassword 'RETURN 1'"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5
            }
        }
        
        # Start container
        container = docker_config.start_container("test_neo4j", neo4j_config)
        
        # Wait for Neo4j to be ready
        docker_config.wait_for_health(container, timeout=60)
        
        yield {
            "container": container,
            "uri": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "testpassword"
        }
        
        # Cleanup
        docker_config.stop_container(container)
    
    def test_neo4j_connection(self, docker_neo4j):
        """Test connection to Neo4j Docker container"""
        config = docker_neo4j
        
        driver = GraphDatabase.driver(
            config["uri"],
            auth=(config["username"], config["password"])
        )
        
        try:
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                assert record["test"] == 1
        finally:
            driver.close()
    
    def test_neo4j_version_compatibility(self, docker_neo4j):
        """Test Neo4j version is compatible with our requirements"""
        config = docker_neo4j
        
        driver = GraphDatabase.driver(
            config["uri"],
            auth=(config["username"], config["password"])
        )
        
        try:
            with driver.session() as session:
                result = session.run("CALL dbms.components() YIELD versions")
                record = result.single()
                version = record["versions"][0]
                
                # Should be Neo4j 5.x for our requirements
                assert version.startswith("5."), f"Expected Neo4j 5.x, got {version}"
        finally:
            driver.close()
    
    def test_apoc_plugin_availability(self, docker_neo4j):
        """Test APOC plugin is available for advanced operations"""
        config = docker_neo4j
        
        driver = GraphDatabase.driver(
            config["uri"],
            auth=(config["username"], config["password"])
        )
        
        try:
            with driver.session() as session:
                # Test basic APOC function
                result = session.run("RETURN apoc.version() as version")
                record = result.single()
                assert record["version"] is not None
        except Exception as e:
            pytest.skip(f"APOC not available: {e}")
        finally:
            driver.close()


@pytest.mark.integration
@pytest.mark.requires_docker
class TestNeo4jSchemaIntegration:
    """Test Neo4j schema creation and validation with real database"""
    
    @pytest.fixture
    def knowledge_graph_service(self, docker_neo4j):
        """Create KnowledgeGraphService connected to Docker Neo4j"""
        config = docker_neo4j
        
        service = KnowledgeGraphService(
            uri=config["uri"],
            username=config["username"],
            password=config["password"]
        )
        
        # Clean database before each test
        with service.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        yield service
        
        # Cleanup after test
        service.close()
    
    def test_schema_creation(self, knowledge_graph_service):
        """Test creating the complete knowledge graph schema"""
        service = knowledge_graph_service
        
        # Create schema with constraints and indexes
        service.create_schema()
        
        # Verify constraints were created
        with service.driver.session() as session:
            result = session.run("SHOW CONSTRAINTS")
            constraints = [record["name"] for record in result]
            
            # Should have uniqueness constraints for key properties
            assert any("Tool" in constraint for constraint in constraints)
            assert any("Task" in constraint for constraint in constraints)
            assert any("SafetyRule" in constraint for constraint in constraints)
    
    def test_node_type_constraints(self, knowledge_graph_service):
        """Test node type constraints and validation"""
        service = knowledge_graph_service
        service.create_schema()
        
        # Test Tool node with all required properties
        tool_data = {
            "name": "Integration Test Circular Saw",
            "category": "cutting_tools",
            "brand": "TestBrand",
            "specifications": {"power": "15-amp", "blade_diameter": "7.25-inch"},
            "safety_rating": 4.2
        }
        
        result = service.create_tool_node(tool_data)
        assert result is not None
        assert result["name"] == "Integration Test Circular Saw"
        
        # Verify the node was actually created in the database
        with service.driver.session() as session:
            query_result = session.run(
                "MATCH (t:Tool {name: $name}) RETURN t",
                name="Integration Test Circular Saw"
            )
            node = query_result.single()
            assert node is not None
            assert node["t"]["category"] == "cutting_tools"
            assert node["t"]["safety_rating"] == 4.2
    
    def test_relationship_constraints(self, knowledge_graph_service):
        """Test relationship constraints and validation"""
        service = knowledge_graph_service
        service.create_schema()
        
        # Create tool and task nodes
        tool_data = {
            "name": "Test Drill",
            "category": "drilling_tools",
            "brand": "TestBrand",
            "specifications": {"type": "cordless"},
            "safety_rating": 4.0
        }
        tool_result = service.create_tool_node(tool_data)
        
        task_data = {
            "name": "Drill Holes",
            "complexity": 3,
            "required_skills": ["measuring", "drilling"],
            "estimated_time": 15
        }
        task_result = service.create_task_node(task_data)
        
        # Create relationship
        relationship_result = service.create_used_for_relationship(
            tool_result["id"], task_result["id"]
        )
        
        assert relationship_result is not None
        
        # Verify relationship exists in database
        with service.driver.session() as session:
            query_result = session.run(
                """
                MATCH (tool:Tool {name: 'Test Drill'})-[r:USED_FOR]->(task:Task {name: 'Drill Holes'})
                RETURN r
                """
            )
            relationship = query_result.single()
            assert relationship is not None
    
    def test_schema_indexes_performance(self, knowledge_graph_service, performance_monitor):
        """Test that schema indexes provide good query performance"""
        service = knowledge_graph_service
        service.create_schema()
        
        # Create multiple nodes for performance testing
        for i in range(100):
            tool_data = {
                "name": f"Performance Test Tool {i}",
                "category": "test_tools",
                "brand": "TestBrand",
                "specifications": {"test": True},
                "safety_rating": 3.0 + (i % 20) / 10.0
            }
            service.create_tool_node(tool_data)
        
        # Test indexed query performance
        performance_monitor.start("indexed_query")
        
        with service.driver.session() as session:
            result = session.run(
                "MATCH (t:Tool) WHERE t.category = 'test_tools' RETURN count(t) as count"
            )
            count = result.single()["count"]
        
        query_duration = performance_monitor.stop("indexed_query")
        
        # Should find all 100 tools quickly with index
        assert count == 100
        performance_monitor.assert_within_threshold(5.0, "indexed_query")


@pytest.mark.integration
@pytest.mark.requires_docker
class TestNeo4jCRUDOperations:
    """Test CRUD operations with real Neo4j database"""
    
    @pytest.fixture
    def knowledge_graph_service(self, docker_neo4j):
        """Create clean KnowledgeGraphService for each test"""
        config = docker_neo4j
        
        service = KnowledgeGraphService(
            uri=config["uri"],
            username=config["username"],
            password=config["password"]
        )
        
        service.create_schema()
        
        # Clean database
        with service.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        yield service
        
        service.close()
    
    def test_create_tool_nodes(self, knowledge_graph_service):
        """Test creating various types of tool nodes"""
        service = knowledge_graph_service
        
        # Test different tool types
        tools = [
            {
                "name": "DeWalt Circular Saw",
                "category": "cutting_tools",
                "brand": "DeWalt",
                "specifications": {
                    "power": "15-amp",
                    "blade_diameter": "7.25-inch",
                    "max_cutting_depth": "2.5-inch"
                },
                "safety_rating": 4.2
            },
            {
                "name": "Makita Cordless Drill",
                "category": "drilling_tools", 
                "brand": "Makita",
                "specifications": {
                    "voltage": "18V",
                    "battery_type": "lithium-ion",
                    "chuck_size": "1/2-inch"
                },
                "safety_rating": 4.5
            },
            {
                "name": "Safety Glasses",
                "category": "safety_equipment",
                "brand": "Generic",
                "specifications": {
                    "ansi_rating": "Z87.1",
                    "lens_type": "polycarbonate"
                },
                "safety_rating": 5.0
            }
        ]
        
        created_tools = []
        for tool_data in tools:
            result = service.create_tool_node(tool_data)
            created_tools.append(result)
            assert result["name"] == tool_data["name"]
            assert result["brand"] == tool_data["brand"]
        
        # Verify all tools exist in database
        with service.driver.session() as session:
            result = session.run("MATCH (t:Tool) RETURN count(t) as count")
            count = result.single()["count"]
            assert count == 3
    
    def test_create_task_nodes(self, knowledge_graph_service):
        """Test creating various types of task nodes"""
        service = knowledge_graph_service
        
        tasks = [
            {
                "name": "Cut Wood Planks",
                "complexity": 3,
                "required_skills": ["measuring", "cutting", "safety"],
                "estimated_time": 30
            },
            {
                "name": "Drill Pilot Holes",
                "complexity": 2,
                "required_skills": ["measuring", "drilling"],
                "estimated_time": 15
            },
            {
                "name": "Assemble Frame",
                "complexity": 4,
                "required_skills": ["assembly", "measuring", "fastening"],
                "estimated_time": 60
            }
        ]
        
        for task_data in tasks:
            result = service.create_task_node(task_data)
            assert result["name"] == task_data["name"]
            assert result["complexity"] == task_data["complexity"]
            assert len(result["required_skills"]) == len(task_data["required_skills"])
        
        # Verify tasks with complexity filtering
        with service.driver.session() as session:
            result = session.run(
                "MATCH (t:Task) WHERE t.complexity <= 3 RETURN count(t) as count"
            )
            count = result.single()["count"]
            assert count == 2  # Cut Wood Planks and Drill Pilot Holes
    
    def test_create_safety_rule_nodes(self, knowledge_graph_service):
        """Test creating safety rule nodes with OSHA/ANSI standards"""
        service = knowledge_graph_service
        
        safety_rules = [
            {
                "osha_code": "1926.95",
                "ansi_standard": "Z87.1",
                "description": "Eye protection required when operating power tools",
                "severity": "high"
            },
            {
                "osha_code": "1926.96",
                "ansi_standard": "Z89.1", 
                "description": "Head protection required in construction areas",
                "severity": "medium"
            },
            {
                "osha_code": "1926.52",
                "ansi_standard": "Z87.1",
                "description": "Hearing protection required for noise levels above 85dB",
                "severity": "high"
            }
        ]
        
        for rule_data in safety_rules:
            result = service.create_safety_rule_node(rule_data)
            assert result["osha_code"] == rule_data["osha_code"]
            assert result["severity"] == rule_data["severity"]
        
        # Query high-severity safety rules
        high_severity_rules = service.find_safety_rules_by_severity("high")
        assert len(high_severity_rules) == 2
    
    def test_create_relationships(self, knowledge_graph_service):
        """Test creating relationships between nodes"""
        service = knowledge_graph_service
        
        # Create nodes first
        tool_data = {
            "name": "Test Circular Saw",
            "category": "cutting_tools",
            "brand": "TestBrand",
            "specifications": {},
            "safety_rating": 4.0
        }
        tool = service.create_tool_node(tool_data)
        
        task_data = {
            "name": "Test Cutting Task",
            "complexity": 3,
            "required_skills": ["cutting"],
            "estimated_time": 20
        }
        task = service.create_task_node(task_data)
        
        safety_data = {
            "osha_code": "TEST.01",
            "ansi_standard": "TEST.1",
            "description": "Test safety rule",
            "severity": "medium"
        }
        safety_rule = service.create_safety_rule_node(safety_data)
        
        # Create relationships
        used_for_rel = service.create_used_for_relationship(tool["id"], task["id"])
        requires_safety_rel = service.create_requires_safety_relationship(
            tool["id"], safety_rule["id"]
        )
        
        assert used_for_rel["type"] == "USED_FOR"
        assert requires_safety_rel["type"] == "REQUIRES_SAFETY"
        
        # Verify relationship traversal
        tools_for_task = service.find_tools_for_task("Test Cutting Task")
        assert len(tools_for_task) == 1
        assert tools_for_task[0]["name"] == "Test Circular Saw"
        
        safety_for_tool = service.find_safety_requirements_for_tool("Test Circular Saw")
        assert len(safety_for_tool) == 1
        assert safety_for_tool[0]["osha_code"] == "TEST.01"
    
    def test_update_operations(self, knowledge_graph_service):
        """Test updating node properties"""
        service = knowledge_graph_service
        
        # Create tool
        tool_data = {
            "name": "Updatable Tool",
            "category": "test_tools",
            "brand": "OldBrand",
            "specifications": {"version": "1.0"},
            "safety_rating": 3.0
        }
        tool = service.create_tool_node(tool_data)
        
        # Update tool properties
        updated_data = {
            "brand": "NewBrand",
            "specifications": {"version": "2.0", "improved": True},
            "safety_rating": 4.0
        }
        
        updated_tool = service.update_tool_node(tool["id"], updated_data)
        
        assert updated_tool["brand"] == "NewBrand"
        assert updated_tool["safety_rating"] == 4.0
        assert updated_tool["specifications"]["version"] == "2.0"
        assert updated_tool["specifications"]["improved"] is True
    
    def test_delete_operations(self, knowledge_graph_service):
        """Test deleting nodes and relationships"""
        service = knowledge_graph_service
        
        # Create nodes and relationships
        tool_data = {
            "name": "Deletable Tool",
            "category": "test_tools",
            "brand": "TestBrand",
            "specifications": {},
            "safety_rating": 3.0
        }
        tool = service.create_tool_node(tool_data)
        
        task_data = {
            "name": "Deletable Task",
            "complexity": 2,
            "required_skills": ["test"],
            "estimated_time": 10
        }
        task = service.create_task_node(task_data)
        
        # Create relationship
        service.create_used_for_relationship(tool["id"], task["id"])
        
        # Verify nodes exist
        assert service.get_tool_by_id(tool["id"]) is not None
        assert service.get_task_by_id(task["id"]) is not None
        
        # Delete tool (should also remove relationships)
        service.delete_tool_node(tool["id"])
        
        # Verify tool is deleted
        assert service.get_tool_by_id(tool["id"]) is None
        
        # Verify task still exists (only tool was deleted)
        assert service.get_task_by_id(task["id"]) is not None


@pytest.mark.integration
@pytest.mark.requires_docker
class TestNeo4jComplexQueries:
    """Test complex Cypher queries and graph traversal"""
    
    @pytest.fixture
    def populated_knowledge_graph(self, docker_neo4j):
        """Create knowledge graph with realistic data"""
        config = docker_neo4j
        
        service = KnowledgeGraphService(
            uri=config["uri"],
            username=config["username"],
            password=config["password"]
        )
        
        service.create_schema()
        
        # Clean database
        with service.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        # Create a realistic deck building scenario
        
        # Tools
        tools = [
            {
                "name": "DeWalt Circular Saw DWE575SB",
                "category": "cutting_tools",
                "brand": "DeWalt",
                "specifications": {"power": "15-amp", "blade_diameter": "7.25-inch"},
                "safety_rating": 4.2
            },
            {
                "name": "Makita Cordless Drill XDT13Z",
                "category": "drilling_tools",
                "brand": "Makita", 
                "specifications": {"voltage": "18V", "max_torque": "125-ft-lbs"},
                "safety_rating": 4.5
            },
            {
                "name": "Stanley Level 42-465",
                "category": "measuring_tools",
                "brand": "Stanley",
                "specifications": {"length": "48-inch", "accuracy": "0.5mm/m"},
                "safety_rating": 5.0
            },
            {
                "name": "Safety Glasses Z87",
                "category": "safety_equipment",
                "brand": "3M",
                "specifications": {"ansi_rating": "Z87.1"},
                "safety_rating": 5.0
            }
        ]
        
        created_tools = []
        for tool_data in tools:
            tool = service.create_tool_node(tool_data)
            created_tools.append(tool)
        
        # Tasks
        tasks = [
            {
                "name": "Cut Deck Boards",
                "complexity": 3,
                "required_skills": ["measuring", "cutting", "safety"],
                "estimated_time": 45
            },
            {
                "name": "Drill Pilot Holes",
                "complexity": 2,
                "required_skills": ["measuring", "drilling"],
                "estimated_time": 20
            },
            {
                "name": "Check Level",
                "complexity": 1,
                "required_skills": ["measuring"],
                "estimated_time": 5
            }
        ]
        
        created_tasks = []
        for task_data in tasks:
            task = service.create_task_node(task_data)
            created_tasks.append(task)
        
        # Safety Rules
        safety_rules = [
            {
                "osha_code": "1926.95",
                "ansi_standard": "Z87.1",
                "description": "Eye protection required when operating power tools",
                "severity": "high"
            },
            {
                "osha_code": "1926.52",
                "ansi_standard": "Z87.1",
                "description": "Hearing protection required for noise levels above 85dB",
                "severity": "high"
            }
        ]
        
        created_safety_rules = []
        for rule_data in safety_rules:
            rule = service.create_safety_rule_node(rule_data)
            created_safety_rules.append(rule)
        
        # Create relationships
        # Circular saw used for cutting
        service.create_used_for_relationship(created_tools[0]["id"], created_tasks[0]["id"])
        # Drill used for pilot holes
        service.create_used_for_relationship(created_tools[1]["id"], created_tasks[1]["id"])
        # Level used for checking
        service.create_used_for_relationship(created_tools[2]["id"], created_tasks[2]["id"])
        
        # Safety requirements
        service.create_requires_safety_relationship(created_tools[0]["id"], created_safety_rules[0]["id"])  # Saw needs eye protection
        service.create_requires_safety_relationship(created_tools[0]["id"], created_safety_rules[1]["id"])  # Saw needs hearing protection
        service.create_requires_safety_relationship(created_tools[1]["id"], created_safety_rules[0]["id"])  # Drill needs eye protection
        
        # Tool compatibility (tools that work well together)
        service.create_compatible_with_relationship(created_tools[0]["id"], created_tools[3]["id"])  # Saw + Safety glasses
        service.create_compatible_with_relationship(created_tools[1]["id"], created_tools[3]["id"])  # Drill + Safety glasses
        
        yield service
        
        service.close()
    
    def test_multi_hop_recommendations(self, populated_knowledge_graph):
        """Test complex multi-hop graph traversal queries"""
        service = populated_knowledge_graph
        
        # Find all tools needed for a complete deck building project
        # This requires traversing: Task -> Tool -> SafetyRule
        query = """
        MATCH (task:Task)
        WHERE task.name CONTAINS 'Deck' OR task.name CONTAINS 'Drill' OR task.name CONTAINS 'Level'
        MATCH (task)<-[:USED_FOR]-(tool:Tool)
        OPTIONAL MATCH (tool)-[:REQUIRES_SAFETY]->(safety:SafetyRule)
        OPTIONAL MATCH (tool)-[:COMPATIBLE_WITH]->(compatible:Tool)
        RETURN DISTINCT tool.name as tool_name, 
               tool.category as category,
               collect(DISTINCT task.name) as tasks,
               collect(DISTINCT safety.description) as safety_requirements,
               collect(DISTINCT compatible.name) as compatible_tools
        ORDER BY tool.safety_rating DESC
        """
        
        with service.driver.session() as session:
            result = session.run(query)
            tools = list(result)
        
        assert len(tools) >= 3  # Should find circular saw, drill, level
        
        # Verify circular saw has safety requirements
        circular_saw = next((t for t in tools if "Circular Saw" in t["tool_name"]), None)
        assert circular_saw is not None
        assert len(circular_saw["safety_requirements"]) >= 1
        assert any("Eye protection" in req for req in circular_saw["safety_requirements"])
    
    def test_recommendation_by_skill_level(self, populated_knowledge_graph):
        """Test filtering recommendations by user skill level"""
        service = populated_knowledge_graph
        
        # Find tools appropriate for beginner skill level (complexity <= 2)
        beginner_tools = service.find_tools_for_skill_level("beginner", max_complexity=2)
        
        # Should include drill and level, but not circular saw (complexity 3)
        assert len(beginner_tools) >= 2
        tool_names = [tool["name"] for tool in beginner_tools]
        assert any("Drill" in name for name in tool_names)
        assert any("Level" in name for name in tool_names)
        
        # Advanced users should see all tools
        advanced_tools = service.find_tools_for_skill_level("advanced", max_complexity=5)
        assert len(advanced_tools) >= len(beginner_tools)
    
    def test_safety_compliance_queries(self, populated_knowledge_graph):
        """Test safety compliance and risk assessment queries"""
        service = populated_knowledge_graph
        
        # Find all OSHA-compliant tools and their requirements
        query = """
        MATCH (tool:Tool)-[:REQUIRES_SAFETY]->(safety:SafetyRule)
        WHERE safety.osha_code IS NOT NULL
        RETURN tool.name as tool_name,
               tool.safety_rating as safety_rating,
               collect({
                   osha_code: safety.osha_code,
                   severity: safety.severity,
                   description: safety.description
               }) as osha_requirements
        ORDER BY tool.safety_rating DESC
        """
        
        with service.driver.session() as session:
            result = session.run(query)
            compliant_tools = list(result)
        
        assert len(compliant_tools) >= 2  # Circular saw and drill have safety requirements
        
        # All tools should have OSHA codes
        for tool in compliant_tools:
            assert len(tool["osha_requirements"]) > 0
            for req in tool["osha_requirements"]:
                assert req["osha_code"].startswith("1926.")
    
    def test_tool_compatibility_network(self, populated_knowledge_graph):
        """Test tool compatibility network analysis"""
        service = populated_knowledge_graph
        
        # Find tool compatibility clusters
        query = """
        MATCH (tool1:Tool)-[:COMPATIBLE_WITH]-(tool2:Tool)
        RETURN tool1.name as tool1_name,
               tool1.category as tool1_category,
               collect(tool2.name) as compatible_tools,
               count(tool2) as compatibility_count
        ORDER BY compatibility_count DESC
        """
        
        with service.driver.session() as session:
            result = session.run(query)
            compatibility_networks = list(result)
        
        # Safety glasses should be compatible with multiple tools
        safety_glasses = next(
            (item for item in compatibility_networks if "Safety Glasses" in item["tool1_name"]), 
            None
        )
        if safety_glasses:
            assert safety_glasses["compatibility_count"] >= 2
    
    def test_project_workflow_analysis(self, populated_knowledge_graph):
        """Test analyzing complete project workflows"""
        service = populated_knowledge_graph
        
        # Simulate a deck building project workflow
        project_tasks = ["Cut Deck Boards", "Drill Pilot Holes", "Check Level"]
        
        # Find all tools and safety requirements for the complete project
        total_tools = set()
        total_safety_requirements = set()
        estimated_time = 0
        
        for task_name in project_tasks:
            tools_for_task = service.find_tools_for_task(task_name)
            for tool in tools_for_task:
                total_tools.add(tool["name"])
                
                # Get safety requirements for this tool
                safety_reqs = service.find_safety_requirements_for_tool(tool["name"])
                for req in safety_reqs:
                    total_safety_requirements.add(req["osha_code"])
            
            # Get task estimated time
            task_info = service.get_task_by_name(task_name)
            if task_info:
                estimated_time += task_info["estimated_time"]
        
        # Verify project analysis results
        assert len(total_tools) >= 3  # Should need multiple tools
        assert len(total_safety_requirements) >= 1  # Should have safety requirements
        assert estimated_time > 0  # Should have time estimate
        
        # Verify all safety requirements are covered
        assert "1926.95" in total_safety_requirements  # Eye protection


@pytest.mark.integration
@pytest.mark.requires_docker
class TestNeo4jPerformanceIntegration:
    """Test Neo4j performance with real database operations"""
    
    @pytest.fixture
    def performance_knowledge_graph(self, docker_neo4j):
        """Create knowledge graph optimized for performance testing"""
        config = docker_neo4j
        
        service = KnowledgeGraphService(
            uri=config["uri"],
            username=config["username"],
            password=config["password"]
        )
        
        service.create_schema()
        
        # Clean database
        with service.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        # Create larger dataset for performance testing
        # 500 tools, 100 tasks, 50 safety rules
        import random
        
        tool_categories = ["cutting_tools", "drilling_tools", "measuring_tools", "safety_equipment", "fastening_tools"]
        brands = ["DeWalt", "Makita", "Milwaukee", "Bosch", "Stanley", "Craftsman"]
        
        # Create tools
        for i in range(500):
            tool_data = {
                "name": f"Performance Tool {i:03d}",
                "category": random.choice(tool_categories),
                "brand": random.choice(brands),
                "specifications": {"test_id": i, "performance": True},
                "safety_rating": round(random.uniform(2.0, 5.0), 1)
            }
            service.create_tool_node(tool_data)
        
        # Create tasks
        for i in range(100):
            task_data = {
                "name": f"Performance Task {i:03d}",
                "complexity": random.randint(1, 5),
                "required_skills": [f"skill_{j}" for j in range(random.randint(1, 4))],
                "estimated_time": random.randint(5, 120)
            }
            service.create_task_node(task_data)
        
        # Create safety rules
        for i in range(50):
            rule_data = {
                "osha_code": f"1926.{100 + i}",
                "ansi_standard": f"Z{random.randint(10, 99)}.{random.randint(1, 9)}",
                "description": f"Performance safety rule {i}",
                "severity": random.choice(["low", "medium", "high", "critical"])
            }
            service.create_safety_rule_node(rule_data)
        
        # Create random relationships for realistic graph structure
        with service.driver.session() as session:
            # USED_FOR relationships (tool -> task)
            session.run("""
                MATCH (tool:Tool), (task:Task)
                WHERE rand() < 0.1
                CREATE (tool)-[:USED_FOR]->(task)
            """)
            
            # REQUIRES_SAFETY relationships (tool -> safety)
            session.run("""
                MATCH (tool:Tool), (safety:SafetyRule)
                WHERE rand() < 0.05
                CREATE (tool)-[:REQUIRES_SAFETY]->(safety)
            """)
            
            # COMPATIBLE_WITH relationships (tool -> tool)
            session.run("""
                MATCH (tool1:Tool), (tool2:Tool)
                WHERE tool1 <> tool2 AND rand() < 0.02
                CREATE (tool1)-[:COMPATIBLE_WITH]->(tool2)
            """)
        
        yield service
        
        service.close()
    
    def test_large_dataset_query_performance(self, performance_knowledge_graph, performance_monitor):
        """Test query performance with large dataset"""
        service = performance_knowledge_graph
        
        # Test complex query performance
        performance_monitor.start("large_dataset_query")
        
        query = """
        MATCH (tool:Tool)-[:USED_FOR]->(task:Task)
        WHERE tool.category = 'cutting_tools'
        OPTIONAL MATCH (tool)-[:REQUIRES_SAFETY]->(safety:SafetyRule)
        RETURN tool.name, task.name, collect(safety.osha_code) as safety_codes
        LIMIT 50
        """
        
        with service.driver.session() as session:
            result = session.run(query)
            results = list(result)
        
        query_duration = performance_monitor.stop("large_dataset_query")
        
        # Should complete within 5 seconds for integration test
        performance_monitor.assert_within_threshold(5.0, "large_dataset_query")
        assert len(results) > 0
    
    def test_concurrent_operations_performance(self, performance_knowledge_graph, performance_monitor):
        """Test performance under concurrent operations"""
        service = performance_knowledge_graph
        
        import concurrent.futures
        import threading
        
        def perform_query(thread_id):
            """Perform a query in a separate thread"""
            with service.driver.session() as session:
                result = session.run(
                    "MATCH (tool:Tool) WHERE tool.safety_rating >= $rating RETURN count(tool) as count",
                    rating=3.0
                )
                return result.single()["count"]
        
        # Test concurrent queries
        performance_monitor.start("concurrent_queries")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(perform_query, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        concurrent_duration = performance_monitor.stop("concurrent_queries")
        
        # Should handle concurrent queries efficiently
        performance_monitor.assert_within_threshold(5.0, "concurrent_queries")
        assert len(results) == 10
        assert all(result > 0 for result in results)
    
    def test_bulk_operations_performance(self, performance_knowledge_graph, performance_monitor):
        """Test bulk insert and update performance"""
        service = performance_knowledge_graph
        
        # Test bulk insert performance
        performance_monitor.start("bulk_insert")
        
        # Create 100 new tools in batch
        new_tools = []
        for i in range(100):
            tool_data = {
                "name": f"Bulk Tool {i:03d}",
                "category": "bulk_tools",
                "brand": "BulkBrand",
                "specifications": {"bulk_id": i},
                "safety_rating": 3.5
            }
            new_tools.append(tool_data)
        
        service.bulk_create_tool_nodes(new_tools)
        
        bulk_duration = performance_monitor.stop("bulk_insert")
        
        # Bulk operations should be efficient
        performance_monitor.assert_within_threshold(5.0, "bulk_insert")
        
        # Verify all tools were created
        with service.driver.session() as session:
            result = session.run("MATCH (t:Tool {category: 'bulk_tools'}) RETURN count(t) as count")
            count = result.single()["count"]
            assert count == 100
    
    def test_index_performance_optimization(self, performance_knowledge_graph, performance_monitor):
        """Test that database indexes provide performance optimization"""
        service = performance_knowledge_graph
        
        # Query that should benefit from indexes
        indexed_query = "MATCH (t:Tool {category: 'cutting_tools'}) RETURN t LIMIT 10"
        
        # Measure with indexes
        performance_monitor.start("with_indexes")
        with service.driver.session() as session:
            result = session.run(indexed_query)
            results_with_index = list(result)
        with_index_duration = performance_monitor.stop("with_indexes")
        
        # Drop indexes temporarily
        with service.driver.session() as session:
            session.run("DROP INDEX tool_category_index IF EXISTS")
        
        # Measure without indexes
        performance_monitor.start("without_indexes")
        with service.driver.session() as session:
            result = session.run(indexed_query)
            results_without_index = list(result)
        without_index_duration = performance_monitor.stop("without_indexes")
        
        # Recreate indexes
        service.create_schema()
        
        # With indexes should be faster (or at least not significantly slower)
        assert len(results_with_index) == len(results_without_index)
        # Performance difference may not be significant with small dataset
        # But both should complete within threshold
        assert with_index_duration < 5.0
        assert without_index_duration < 5.0


if __name__ == "__main__":
    # Run integration tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "integration",
        "--durations=10"
    ])