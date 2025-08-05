"""
Neo4j Knowledge Graph Service
=============================

Service for managing Neo4j knowledge graph operations including schema management,
node creation, relationship management, and complex graph queries.
"""

from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, field

try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    # Mock classes for development/testing
    class GraphDatabase:
        @staticmethod
        def driver(uri: str, auth: tuple = None, **kwargs):
            return MockDriver()
    
    class Driver:
        pass
    
    class MockDriver:
        def __init__(self):
            pass
        
        def session(self):
            return MockSession()
        
        def close(self):
            pass
    
    class MockSession:
        def run(self, query: str, **parameters):
            return MockResult()
        
        def close(self):
            pass
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    
    class MockResult:
        def single(self):
            return {"t": {"name": "mock_result", "id": "mock_id"}}
        
        def values(self):
            return [("mock_result", 4.0, ["mock_category"])]

from ..models.knowledge_graph import Tool, Task, Project, User, SafetyRule

logger = logging.getLogger(__name__)


@dataclass
class Neo4jSchema:
    """Neo4j schema definition and management"""
    
    def __init__(self):
        self.node_types = {
            "Tool": {
                "name": {"type": "string", "required": True, "indexed": True},
                "category": {"type": "string", "required": True, "indexed": True},
                "brand": {"type": "string", "required": True, "indexed": True},
                "specifications": {"type": "object", "required": True},
                "safety_rating": {"type": "float", "required": True, "indexed": True}
            },
            "Task": {
                "name": {"type": "string", "required": True, "indexed": True},
                "complexity": {"type": "integer", "required": True, "indexed": True},
                "required_skills": {"type": "array", "required": True},
                "estimated_time": {"type": "integer", "required": True}
            },
            "Project": {
                "name": {"type": "string", "required": True, "indexed": True},
                "project_type": {"type": "string", "required": True, "indexed": True},
                "difficulty_level": {"type": "string", "required": True, "indexed": True},
                "estimated_duration": {"type": "integer", "required": True}
            },
            "User": {
                "username": {"type": "string", "required": True, "indexed": True},
                "skill_level": {"type": "string", "required": True, "indexed": True},
                "experience": {"type": "array", "required": True},
                "preferences": {"type": "object", "required": True},
                "safety_certification": {"type": "array", "required": False}
            },
            "SafetyRule": {
                "osha_code": {"type": "string", "required": True, "indexed": True},
                "ansi_standard": {"type": "string", "required": True, "indexed": True}, 
                "description": {"type": "string", "required": True},
                "severity": {"type": "string", "required": True, "indexed": True}
            }
        }
        
        self.relationship_types = [
            "USED_FOR",      # Tool -> Task
            "COMPATIBLE_WITH", # Tool -> Tool
            "REQUIRES_SAFETY", # Tool -> SafetyRule
            "PART_OF",       # Task -> Project
            "CAN_PERFORM"    # User -> Task
        ]
    
    def get_node_types(self) -> List[str]:
        """Get list of all node types"""
        return list(self.node_types.keys())
    
    def get_relationship_types(self) -> List[str]:
        """Get list of all relationship types"""
        return self.relationship_types
    
    def get_node_properties(self, node_type: str) -> Dict[str, Any]:
        """Get properties for a specific node type"""
        if node_type not in self.node_types:
            raise ValueError(f"Unknown node type: {node_type}")
        return self.node_types[node_type]
    
    def validate_node_data(self, node_type: str, data: Dict[str, Any]) -> bool:
        """Validate node data against schema"""
        if node_type not in self.node_types:
            raise ValueError(f"Unknown node type: {node_type}")
        
        schema = self.node_types[node_type]
        
        # Check required fields
        for field_name, field_config in schema.items():
            if field_config.get("required", False) and field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")
        
        return True


class KnowledgeGraphService:
    """Service for Neo4j knowledge graph operations"""
    
    def __init__(self, uri: str, username: str, password: str, **kwargs):
        """Initialize Neo4j connection"""
        self.uri = uri
        self.username = username
        self.password = password
        
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available, using mock implementation")
        
        try:
            self.driver = GraphDatabase.driver(
                uri, 
                auth=(username, password),
                **kwargs
            )
            self.schema = Neo4jSchema()
            logger.info(f"Connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if Neo4j connection is healthy"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as health")
                return result.single()["health"] == 1
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False
    
    def close(self):
        """Close Neo4j connection"""
        if hasattr(self, 'driver'):
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def create_schema(self):
        """Create Neo4j schema with constraints and indexes"""
        with self.driver.session() as session:
            # Create uniqueness constraints
            constraints = [
                "CREATE CONSTRAINT tool_name_unique IF NOT EXISTS FOR (t:Tool) REQUIRE t.name IS UNIQUE",
                "CREATE CONSTRAINT task_name_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.name IS UNIQUE", 
                "CREATE CONSTRAINT project_name_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.name IS UNIQUE",
                "CREATE CONSTRAINT user_username_unique IF NOT EXISTS FOR (u:User) REQUIRE u.username IS UNIQUE",
                "CREATE CONSTRAINT safety_osha_unique IF NOT EXISTS FOR (s:SafetyRule) REQUIRE s.osha_code IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.debug(f"Created constraint: {constraint}")
                except Exception as e:
                    logger.warning(f"Failed to create constraint: {e}")
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX tool_category_index IF NOT EXISTS FOR (t:Tool) ON (t.category)",
                "CREATE INDEX tool_brand_index IF NOT EXISTS FOR (t:Tool) ON (t.brand)",
                "CREATE INDEX tool_safety_rating_index IF NOT EXISTS FOR (t:Tool) ON (t.safety_rating)",
                "CREATE INDEX task_complexity_index IF NOT EXISTS FOR (t:Task) ON (t.complexity)",
                "CREATE INDEX user_skill_level_index IF NOT EXISTS FOR (u:User) ON (u.skill_level)",
                "CREATE INDEX safety_severity_index IF NOT EXISTS FOR (s:SafetyRule) ON (s.severity)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                    logger.debug(f"Created index: {index}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")
    
    def create_tool_node(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a tool node in the knowledge graph"""
        # Validate required fields
        required_fields = ["name", "category", "brand", "specifications", "safety_rating"]
        for field in required_fields:
            if field not in tool_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate using schema
        self.schema.validate_node_data("Tool", tool_data)
        
        # Create tool model for validation
        tool = Tool(
            name=tool_data["name"],
            category=tool_data["category"],
            brand=tool_data["brand"],
            specifications=tool_data["specifications"],
            safety_rating=tool_data["safety_rating"]
        )
        
        with self.driver.session() as session:
            query = """
            CREATE (t:Tool {
                id: $id,
                name: $name,
                category: $category,
                brand: $brand,
                specifications: $specifications,
                safety_rating: $safety_rating
            })
            RETURN t
            """
            
            result = session.run(query, **tool.to_dict())
            node = result.single()
            return dict(node["t"])
    
    def create_task_node(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task node in the knowledge graph"""
        # Validate required fields
        required_fields = ["name", "complexity", "required_skills", "estimated_time"]
        for field in required_fields:
            if field not in task_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Create task model for validation
        task = Task(
            name=task_data["name"],
            complexity=task_data["complexity"],
            required_skills=task_data["required_skills"],
            estimated_time=task_data["estimated_time"]
        )
        
        with self.driver.session() as session:
            query = """
            CREATE (t:Task {
                id: $id,
                name: $name,
                complexity: $complexity,
                required_skills: $required_skills,
                estimated_time: $estimated_time
            })
            RETURN t
            """
            
            result = session.run(query, **task.to_dict())
            node = result.single()
            return dict(node["t"])
    
    def create_safety_rule_node(self, safety_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a safety rule node in the knowledge graph"""
        # Validate required fields
        required_fields = ["osha_code", "ansi_standard", "description", "severity"]
        for field in required_fields:
            if field not in safety_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Create safety rule model for validation
        safety_rule = SafetyRule(
            osha_code=safety_data["osha_code"],
            ansi_standard=safety_data["ansi_standard"],
            description=safety_data["description"],
            severity=safety_data["severity"]
        )
        
        with self.driver.session() as session:
            query = """
            CREATE (s:SafetyRule {
                id: $id,
                osha_code: $osha_code,
                ansi_standard: $ansi_standard,
                description: $description,
                severity: $severity
            })
            RETURN s
            """
            
            result = session.run(query, **safety_rule.to_dict())
            node = result.single()
            return dict(node["s"])
    
    def create_used_for_relationship(self, tool_id: str, task_id: str) -> Dict[str, Any]:
        """Create USED_FOR relationship between tool and task"""
        with self.driver.session() as session:
            query = """
            MATCH (tool:Tool {id: $tool_id}), (task:Task {id: $task_id})
            CREATE (tool)-[r:USED_FOR]->(task)
            RETURN r
            """
            
            result = session.run(query, tool_id=tool_id, task_id=task_id)
            relationship = result.single()
            return {"type": "USED_FOR"}
    
    def create_requires_safety_relationship(self, tool_id: str, safety_rule_id: str) -> Dict[str, Any]:
        """Create REQUIRES_SAFETY relationship between tool and safety rule"""
        with self.driver.session() as session:
            query = """
            MATCH (tool:Tool {id: $tool_id}), (safety:SafetyRule {id: $safety_rule_id})
            CREATE (tool)-[r:REQUIRES_SAFETY]->(safety)
            RETURN r
            """
            
            result = session.run(query, tool_id=tool_id, safety_rule_id=safety_rule_id)
            relationship = result.single()
            return {"type": "REQUIRES_SAFETY"}
    
    def create_compatible_with_relationship(self, tool1_id: str, tool2_id: str) -> Dict[str, Any]:
        """Create COMPATIBLE_WITH relationship between tools"""
        with self.driver.session() as session:
            query = """
            MATCH (tool1:Tool {id: $tool1_id}), (tool2:Tool {id: $tool2_id})
            CREATE (tool1)-[r:COMPATIBLE_WITH]->(tool2)
            RETURN r
            """
            
            result = session.run(query, tool1_id=tool1_id, tool2_id=tool2_id)
            relationship = result.single()
            return {"type": "COMPATIBLE_WITH"}
    
    def find_tools_for_task(self, task_name: str) -> List[Dict[str, Any]]:
        """Find tools suitable for a specific task"""
        with self.driver.session() as session:
            query = """
            MATCH (tool:Tool)-[:USED_FOR]->(task:Task {name: $task_name})
            RETURN tool.name as name, tool.safety_rating as safety_rating, 
                   tool.category as category, tool.brand as brand
            ORDER BY tool.safety_rating DESC
            """
            
            result = session.run(query, task_name=task_name)
            tools = []
            for record in result:
                tools.append({
                    "name": record["name"],
                    "safety_rating": record["safety_rating"],
                    "category": record["category"],
                    "brand": record["brand"]
                })
            return tools
    
    def find_safety_requirements_for_tool(self, tool_name: str) -> List[Dict[str, Any]]:
        """Find safety requirements for a specific tool"""
        with self.driver.session() as session:
            query = """
            MATCH (tool:Tool {name: $tool_name})-[:REQUIRES_SAFETY]->(safety:SafetyRule)
            RETURN safety.osha_code as osha_code, safety.ansi_standard as ansi_standard,
                   safety.description as description, safety.severity as severity
            ORDER BY safety.severity DESC
            """
            
            result = session.run(query, tool_name=tool_name)
            requirements = []
            for record in result:
                requirements.append({
                    "osha_code": record["osha_code"],
                    "ansi_standard": record["ansi_standard"],
                    "description": record["description"],
                    "severity": record["severity"]
                })
            return requirements
    
    def get_compatible_tools(self, tool_name: str) -> List[Dict[str, Any]]:
        """Find tools compatible with a given tool"""
        with self.driver.session() as session:
            query = """
            MATCH (tool1:Tool {name: $tool_name})-[:COMPATIBLE_WITH]->(tool2:Tool)
            RETURN tool2.name as name, tool2.safety_rating as safety_rating,
                   tool2.category as category, tool2.brand as brand
            ORDER BY tool2.safety_rating DESC
            """
            
            result = session.run(query, tool_name=tool_name)
            compatible_tools = []
            for record in result:
                compatible_tools.append({
                    "name": record["name"],
                    "safety_rating": record["safety_rating"],
                    "category": record["category"],
                    "brand": record["brand"]
                })
            return compatible_tools
    
    def find_tools_for_skill_level(self, skill_level: str, max_complexity: int = 10) -> List[Dict[str, Any]]:
        """Find tools appropriate for a user's skill level"""
        with self.driver.session() as session:
            query = """
            MATCH (tool:Tool)-[:USED_FOR]->(task:Task)
            WHERE task.complexity <= $max_complexity
            RETURN DISTINCT tool.name as name, tool.safety_rating as safety_rating,
                   tool.category as category, tool.brand as brand,
                   collect(task.complexity) as task_complexities
            ORDER BY tool.safety_rating DESC
            """
            
            result = session.run(query, max_complexity=max_complexity)
            tools = []
            for record in result:
                tools.append({
                    "name": record["name"],
                    "safety_rating": record["safety_rating"],
                    "category": record["category"],
                    "brand": record["brand"],
                    "max_task_complexity": max(record["task_complexities"]) if record["task_complexities"] else 0
                })
            return tools
    
    def find_safety_rules_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Find safety rules by severity level"""
        with self.driver.session() as session:
            query = """
            MATCH (s:SafetyRule {severity: $severity})
            RETURN s.osha_code as osha_code, s.ansi_standard as ansi_standard,
                   s.description as description, s.severity as severity
            ORDER BY s.osha_code
            """
            
            result = session.run(query, severity=severity)
            rules = []
            for record in result:
                rules.append({
                    "osha_code": record["osha_code"],
                    "ansi_standard": record["ansi_standard"],
                    "description": record["description"],
                    "severity": record["severity"]
                })
            return rules
    
    def get_tool_by_id(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get tool by ID"""
        with self.driver.session() as session:
            query = "MATCH (t:Tool {id: $tool_id}) RETURN t"
            result = session.run(query, tool_id=tool_id)
            record = result.single()
            return dict(record["t"]) if record else None
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        with self.driver.session() as session:
            query = "MATCH (t:Task {id: $task_id}) RETURN t"
            result = session.run(query, task_id=task_id)
            record = result.single()
            return dict(record["t"]) if record else None
    
    def get_task_by_name(self, task_name: str) -> Optional[Dict[str, Any]]:
        """Get task by name"""
        with self.driver.session() as session:
            query = "MATCH (t:Task {name: $task_name}) RETURN t"
            result = session.run(query, task_name=task_name)
            record = result.single()
            return dict(record["t"]) if record else None
    
    def update_tool_node(self, tool_id: str, updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update tool node properties"""
        with self.driver.session() as session:
            # Create SET clause for provided fields
            set_clauses = []
            for key, value in updated_data.items():
                set_clauses.append(f"t.{key} = ${key}")
            
            set_clause = ", ".join(set_clauses)
            
            query = f"""
            MATCH (t:Tool {{id: $tool_id}})
            SET {set_clause}
            RETURN t
            """
            
            params = {"tool_id": tool_id, **updated_data}
            result = session.run(query, **params)
            record = result.single()
            return dict(record["t"]) if record else None
    
    def delete_tool_node(self, tool_id: str) -> bool:
        """Delete tool node and all its relationships"""
        with self.driver.session() as session:
            query = """
            MATCH (t:Tool {id: $tool_id})
            DETACH DELETE t
            RETURN count(t) as deleted_count
            """
            
            result = session.run(query, tool_id=tool_id)
            record = result.single()
            return record["deleted_count"] > 0 if record else False
    
    def bulk_create_tool_nodes(self, tools_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple tool nodes in batch"""
        created_tools = []
        
        with self.driver.session() as session:
            tx = session.begin_transaction()
            try:
                for tool_data in tools_data:
                    # Validate and create tool
                    tool = Tool(
                        name=tool_data["name"],
                        category=tool_data["category"],
                        brand=tool_data["brand"],
                        specifications=tool_data["specifications"],
                        safety_rating=tool_data["safety_rating"]
                    )
                    
                    query = """
                    CREATE (t:Tool {
                        id: $id,
                        name: $name,
                        category: $category,
                        brand: $brand,
                        specifications: $specifications,
                        safety_rating: $safety_rating
                    })
                    RETURN t
                    """
                    
                    result = tx.run(query, **tool.to_dict())
                    node = result.single()
                    created_tools.append(dict(node["t"]))
                
                tx.commit()
            except Exception as e:
                tx.rollback()
                logger.error(f"Bulk create failed: {e}")
                raise
        
        return created_tools