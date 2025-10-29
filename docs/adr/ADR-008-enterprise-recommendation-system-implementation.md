# ADR-008: Enterprise AI Recommendation System Implementation

**Status**: PROPOSED
**Date**: 2025-01-16
**Decision Makers**: Technical Lead, Product Owner
**Scope**: Complete upgrade from basic keyword search to enterprise-grade recommendation system

---

## Executive Summary

This ADR proposes a comprehensive implementation plan to upgrade the Horme POV from basic keyword search to an enterprise-grade AI recommendation system following Home Depot and Lowe's best practices. The implementation addresses 7 critical gaps identified in PRD alignment analysis.

**Investment Required**: 12-16 weeks development time
**Expected ROI**: 25-40% improvement in product matching accuracy (industry benchmarks)
**Business Impact**: Enables sophisticated DIY/professional tool recommendations with safety compliance

---

## Context

### Current State
- **Product Search**: Basic SQLite keyword matching (~15% accuracy)
- **Classification**: None (no UNSPSC/ETIM)
- **Knowledge Graph**: None
- **Safety Rules**: None
- **Multi-lingual**: None
- **Frontend**: Not production-deployed
- **Real-time Chat**: Not deployed

### Target State (Industry Best Practices)
- **Hybrid Recommendation System**: Collaborative + Content-based + Knowledge Graph + Context-aware
- **Product Classification**: UNSPSC/ETIM with <500ms classification time
- **Neo4j Knowledge Graph**: Tool-to-task relationships, compatibility rules
- **Safety Compliance**: OSHA/ANSI rules integration
- **Multi-lingual LLM**: 13+ languages via ETIM + LLM translation
- **Production Frontend**: Next.js deployed with WebSocket chat

---

## Decision

Implement a **6-phase roadmap** to upgrade to enterprise-grade recommendation system:

1. **Phase 1**: Neo4j Knowledge Graph Foundation (3 weeks)
2. **Phase 2**: UNSPSC/ETIM Classification System (2 weeks)
3. **Phase 3**: Hybrid AI Recommendation Engine (4 weeks)
4. **Phase 4**: Safety Compliance Integration (2 weeks)
5. **Phase 5**: Multi-lingual LLM Support (2 weeks)
6. **Phase 6**: Frontend + WebSocket Production Deployment (2 weeks)

**Total Timeline**: 15 weeks (with 1-week buffer)

---

## Phase 1: Neo4j Knowledge Graph Foundation (3 weeks)

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Neo4j Knowledge Graph                         │
│                                                                  │
│  [Product] ──used_for──> [Task] ──requires──> [Skill]          │
│     │                       │                      │            │
│     │                       │                      │            │
│  compatible_with      part_of_project      has_difficulty       │
│     │                       │                      │            │
│     ▼                       ▼                      ▼            │
│  [Product]            [Project]            [SkillLevel]         │
│                                                                  │
│  [Product] ──requires_safety──> [SafetyEquipment]               │
│     │                                                            │
│  categorized_as                                                  │
│     │                                                            │
│     ▼                                                            │
│  [UNSPSC_Category] / [ETIM_Class]                               │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

#### 1.1 Add Neo4j to Docker Stack

**File**: `docker-compose.production.yml`

```yaml
  # Neo4j Knowledge Graph
  neo4j:
    image: neo4j:5.15-enterprise
    container_name: horme-neo4j
    environment:
      - NEO4J_AUTH=${NEO4J_USER:-neo4j}/${NEO4J_PASSWORD}
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
      - NEO4J_server_memory_pagecache_size=512M
      - NEO4J_server_memory_heap_max__size=1G
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*,gds.*
      - NEO4J_dbms_security_procedures_allowlist=apoc.*,gds.*
      - NEO4JLABS_PLUGINS=["apoc", "graph-data-science"]
    ports:
      - "${NEO4J_HTTP_PORT:-7474}:7474"
      - "${NEO4J_BOLT_PORT:-7687}:7687"
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/import
      - neo4j_plugins:/plugins
      - ./init-scripts/neo4j-schema.cypher:/docker-entrypoint-initdb.d/01-schema.cypher:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD}", "RETURN 1"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - horme_network
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

volumes:
  neo4j_data:
    driver: local
    name: horme_neo4j_data
  neo4j_logs:
    driver: local
    name: horme_neo4j_logs
  neo4j_import:
    driver: local
    name: horme_neo4j_import
  neo4j_plugins:
    driver: local
    name: horme_neo4j_plugins
```

#### 1.2 Create Neo4j Schema

**File**: `init-scripts/neo4j-schema.cypher`

```cypher
// ============================================================================
// HORME HARDWARE KNOWLEDGE GRAPH SCHEMA
// Industry-standard tool-to-task relationships
// ============================================================================

// Create Constraints for Data Integrity
CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT task_id IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT skill_id IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT safety_id IF NOT EXISTS FOR (s:SafetyEquipment) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT unspsc_code IF NOT EXISTS FOR (u:UNSPSC) REQUIRE u.code IS UNIQUE;
CREATE CONSTRAINT etim_code IF NOT EXISTS FOR (e:ETIM) REQUIRE e.code IS UNIQUE;

// Create Indexes for Performance (<500ms requirement)
CREATE INDEX product_name IF NOT EXISTS FOR (p:Product) ON (p.name);
CREATE INDEX task_name IF NOT EXISTS FOR (t:Task) ON (t.name);
CREATE INDEX project_type IF NOT EXISTS FOR (p:Project) ON (p.type);
CREATE INDEX skill_level IF NOT EXISTS FOR (s:Skill) ON (s.level);
CREATE FULLTEXT INDEX product_search IF NOT EXISTS FOR (p:Product) ON EACH [p.name, p.description, p.keywords];
CREATE FULLTEXT INDEX task_search IF NOT EXISTS FOR (t:Task) ON EACH [t.name, t.description];

// ============================================================================
// NODE SCHEMAS (with required properties)
// ============================================================================

// Product Node
// CALL apoc.meta.nodeTypeProperties() // Validate schema
MERGE (template:Product {
  id: 'TEMPLATE',
  name: 'Product Template',
  description: 'Template for product nodes',
  sku: 'TEMPLATE-001',
  price: 0.0,
  currency: 'SGD',
  category: 'hardware',
  brand: 'Generic',
  keywords: ['template'],
  specifications: {},
  stock_status: 'available',
  is_professional: false,
  difficulty_level: 'beginner',
  created_at: datetime(),
  updated_at: datetime()
});

// Task Node
MERGE (template_task:Task {
  id: 'TEMPLATE_TASK',
  name: 'Task Template',
  description: 'Template for task nodes',
  difficulty: 'easy',
  estimated_time_minutes: 60,
  keywords: ['template'],
  safety_level: 'low',
  created_at: datetime()
});

// Project Node
MERGE (template_project:Project {
  id: 'TEMPLATE_PROJECT',
  name: 'Project Template',
  description: 'Template for project nodes',
  type: 'home_improvement',
  difficulty: 'intermediate',
  estimated_duration_days: 1,
  budget_range: 'medium',
  space_type: 'indoor',
  created_at: datetime()
});

// Skill Node
MERGE (template_skill:Skill {
  id: 'TEMPLATE_SKILL',
  name: 'Skill Template',
  description: 'Template for skill nodes',
  level: 'beginner', // beginner, intermediate, advanced, professional
  category: 'general',
  certification_required: false
});

// Safety Equipment Node
MERGE (template_safety:SafetyEquipment {
  id: 'TEMPLATE_SAFETY',
  name: 'Safety Equipment Template',
  description: 'Template for safety equipment nodes',
  osha_standard: 'OSHA-TEMPLATE',
  ansi_standard: 'ANSI-TEMPLATE',
  mandatory: false,
  for_task_types: ['general']
});

// UNSPSC Classification Node
MERGE (template_unspsc:UNSPSC {
  code: '00000000',
  segment: '00',
  family: '00',
  class: '00',
  commodity: '00',
  segment_name: 'Template Segment',
  family_name: 'Template Family',
  class_name: 'Template Class',
  commodity_name: 'Template Commodity'
});

// ETIM Classification Node
MERGE (template_etim:ETIM {
  code: 'EC000000',
  version: '9.0',
  class_name: 'Template Class',
  class_name_en: 'Template Class',
  group: 'EG000000',
  sector: 'ES00',
  features: {},
  translations: {}
});

// ============================================================================
// RELATIONSHIP SCHEMAS
// ============================================================================

// Product -> Task Relationships
MERGE (template)-[:USED_FOR {
  confidence: 1.0,
  usage_frequency: 'high',
  is_primary_tool: true,
  alternative_exists: false
}]->(template_task);

// Task -> Skill Requirements
MERGE (template_task)-[:REQUIRES_SKILL {
  proficiency_level: 'basic',
  is_mandatory: true,
  learning_time_hours: 2
}]->(template_skill);

// Product -> Product Compatibility
MERGE (template)-[:COMPATIBLE_WITH {
  compatibility_type: 'accessory',
  recommended: true,
  required: false
}]->(template);

// Product -> Safety Requirements
MERGE (template)-[:REQUIRES_SAFETY {
  mandatory: true,
  osha_compliant: true,
  risk_level: 'medium'
}]->(template_safety);

// Task -> Project Relationships
MERGE (template_task)-[:PART_OF_PROJECT {
  sequence_order: 1,
  is_critical_path: true,
  parallel_execution_allowed: false
}]->(template_project);

// Product -> Classification
MERGE (template)-[:CATEGORIZED_AS {
  confidence: 1.0,
  classification_date: datetime()
}]->(template_unspsc);

MERGE (template)-[:CLASSIFIED_BY {
  confidence: 1.0,
  classification_date: datetime()
}]->(template_etim);

// ============================================================================
// SAMPLE DATA POPULATION (DIY Hardware Examples)
// ============================================================================

// Example: Power Drill and Related Knowledge
CREATE (drill:Product {
  id: 'DRILL-001',
  name: 'Cordless Power Drill 20V',
  description: '20V lithium-ion cordless drill with variable speed and LED light',
  sku: 'DRILL-20V-001',
  price: 189.99,
  currency: 'SGD',
  category: 'power_tools',
  brand: 'Professional Series',
  keywords: ['drill', 'cordless', '20v', 'power tool', 'battery'],
  specifications: {
    voltage: '20V',
    battery_type: 'Lithium-Ion',
    max_torque: '500 in-lbs',
    chuck_size: '1/2 inch',
    speed_range: '0-1800 RPM'
  },
  stock_status: 'in_stock',
  is_professional: true,
  difficulty_level: 'intermediate',
  created_at: datetime(),
  updated_at: datetime()
});

CREATE (drill_task:Task {
  id: 'TASK_DRILLING_HOLES',
  name: 'Drilling Holes in Wood/Metal',
  description: 'Create precise holes for screws, bolts, or cable routing',
  difficulty: 'easy',
  estimated_time_minutes: 15,
  keywords: ['drilling', 'holes', 'woodwork', 'metalwork'],
  safety_level: 'medium',
  created_at: datetime()
});

CREATE (drilling_skill:Skill {
  id: 'SKILL_POWER_DRILL_OPERATION',
  name: 'Power Drill Operation',
  description: 'Safe operation of corded and cordless drills',
  level: 'beginner',
  category: 'power_tools',
  certification_required: false
});

CREATE (safety_glasses:SafetyEquipment {
  id: 'SAFETY_GLASSES_001',
  name: 'Safety Glasses with Side Shields',
  description: 'ANSI Z87.1 compliant safety glasses',
  osha_standard: '29 CFR 1926.102',
  ansi_standard: 'ANSI Z87.1',
  mandatory: true,
  for_task_types: ['drilling', 'cutting', 'grinding']
});

CREATE (shelf_project:Project {
  id: 'PROJECT_WALL_SHELF',
  name: 'Install Wall Shelving',
  description: 'Install wooden shelves on wall using brackets',
  type: 'home_improvement',
  difficulty: 'beginner',
  estimated_duration_days: 0.5,
  budget_range: 'low',
  space_type: 'indoor',
  created_at: datetime()
});

// Create Relationships
MERGE (drill)-[:USED_FOR {confidence: 0.95, usage_frequency: 'very_high', is_primary_tool: true}]->(drill_task);
MERGE (drill_task)-[:REQUIRES_SKILL {proficiency_level: 'basic', is_mandatory: true, learning_time_hours: 1}]->(drilling_skill);
MERGE (drill)-[:REQUIRES_SAFETY {mandatory: true, osha_compliant: true, risk_level: 'medium'}]->(safety_glasses);
MERGE (drill_task)-[:PART_OF_PROJECT {sequence_order: 2, is_critical_path: true}]->(shelf_project);

// Example: Drill Bits (Compatibility)
CREATE (drill_bits:Product {
  id: 'BITS-001',
  name: 'HSS Drill Bit Set (29 pieces)',
  description: 'High-speed steel drill bits for metal, wood, and plastic',
  sku: 'BITS-HSS-029',
  price: 45.00,
  currency: 'SGD',
  category: 'drill_accessories',
  brand: 'Professional Series',
  keywords: ['drill bits', 'hss', 'metal', 'wood'],
  specifications: {
    material: 'HSS',
    sizes: '1/16" to 1/2"',
    piece_count: 29
  },
  stock_status: 'in_stock',
  is_professional: false,
  difficulty_level: 'beginner',
  created_at: datetime(),
  updated_at: datetime()
});

MERGE (drill)-[:COMPATIBLE_WITH {
  compatibility_type: 'consumable_accessory',
  recommended: true,
  required: true
}]->(drill_bits);

// Classification Examples
CREATE (unspsc_power_tools:UNSPSC {
  code: '27112000',
  segment: '27',
  family: '11',
  class: '20',
  commodity: '00',
  segment_name: 'Tools and General Machinery',
  family_name: 'Hand tools',
  class_name: 'Powered hand tools',
  commodity_name: 'Drills'
});

CREATE (etim_drills:ETIM {
  code: 'EC001489',
  version: '9.0',
  class_name: 'Drill/screwdriver',
  class_name_en: 'Drill/screwdriver',
  group: 'EG000031',
  sector: 'ES01',
  features: {
    voltage: '20V',
    battery_technology: 'Li-Ion',
    chuck_type: 'keyless'
  },
  translations: {
    'zh': '电钻/螺丝刀',
    'ms': 'Gerudi/pemutar skru',
    'ta': 'துளையிடும் கருவி/திருகு விடுபவர்'
  }
});

MERGE (drill)-[:CATEGORIZED_AS {confidence: 1.0}]->(unspsc_power_tools);
MERGE (drill)-[:CLASSIFIED_BY {confidence: 1.0}]->(etim_drills);

// ============================================================================
// USEFUL QUERIES FOR RECOMMENDATION ENGINE
// ============================================================================

// Clean up templates (only keep as reference)
MATCH (n) WHERE n.id CONTAINS 'TEMPLATE' DETACH DELETE n;

// Query: Find tools for a specific task
// MATCH (p:Product)-[r:USED_FOR]->(t:Task {name: 'Drilling Holes in Wood/Metal'})
// RETURN p.name, p.price, r.confidence
// ORDER BY r.confidence DESC, p.price ASC;

// Query: Find compatible accessories for a product
// MATCH (p:Product {id: 'DRILL-001'})-[r:COMPATIBLE_WITH]->(accessory:Product)
// RETURN accessory.name, accessory.price, r.compatibility_type, r.recommended
// ORDER BY r.recommended DESC;

// Query: Find required safety equipment for a task
// MATCH (t:Task {name: 'Drilling Holes in Wood/Metal'})<-[:USED_FOR]-(p:Product)-[:REQUIRES_SAFETY]->(s:SafetyEquipment)
// WHERE s.mandatory = true
// RETURN DISTINCT s.name, s.osha_standard, s.ansi_standard;

// Query: Find all tasks in a project
// MATCH (t:Task)-[r:PART_OF_PROJECT]->(proj:Project {name: 'Install Wall Shelving'})
// RETURN t.name, r.sequence_order, t.difficulty, t.estimated_time_minutes
// ORDER BY r.sequence_order;

// Query: Find products by UNSPSC classification
// MATCH (p:Product)-[:CATEGORIZED_AS]->(u:UNSPSC {class: '20'})
// RETURN p.name, p.description, u.class_name;

// Query: Multi-lingual product search (ETIM)
// MATCH (p:Product)-[:CLASSIFIED_BY]->(e:ETIM)
// WHERE e.translations.zh CONTAINS '电钻'
// RETURN p.name, e.class_name_en, e.translations.zh;
```

#### 1.3 Create Knowledge Graph Service

**File**: `src/services/knowledge_graph_service.py`

```python
"""
Neo4j Knowledge Graph Service
Provides graph-based product recommendations with tool-to-task relationships
"""

from neo4j import GraphDatabase
from typing import List, Dict, Optional, Any
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ProductRecommendation:
    """Product recommendation with graph context."""
    product_id: str
    name: str
    description: str
    price: float
    currency: str
    confidence_score: float
    reasoning: str
    compatible_products: List[str]
    required_safety: List[str]
    required_skills: List[str]
    unspsc_code: Optional[str] = None
    etim_code: Optional[str] = None


class KnowledgeGraphService:
    """
    Neo4j-based knowledge graph for intelligent product recommendations.
    Implements industry best practices from Home Depot research.
    """

    def __init__(self, uri: str, user: str, password: str):
        """Initialize Neo4j connection."""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Connected to Neo4j at {uri}")

    def close(self):
        """Close Neo4j connection."""
        self.driver.close()

    def recommend_products_for_task(
        self,
        task_name: str,
        user_skill_level: str = 'beginner',
        max_results: int = 10
    ) -> List[ProductRecommendation]:
        """
        Recommend products for a specific task using graph traversal.

        Args:
            task_name: Name of the task (e.g., "Drilling Holes in Wood/Metal")
            user_skill_level: User's skill level (beginner/intermediate/advanced/professional)
            max_results: Maximum number of recommendations

        Returns:
            List of ProductRecommendation objects with confidence scores
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._query_products_for_task,
                task_name,
                user_skill_level,
                max_results
            )
            return result

    @staticmethod
    def _query_products_for_task(tx, task_name: str, skill_level: str, max_results: int):
        """Graph traversal query for task-based recommendations."""
        query = """
        MATCH (p:Product)-[r:USED_FOR]->(t:Task)
        WHERE toLower(t.name) CONTAINS toLower($task_name)
          OR toLower(t.description) CONTAINS toLower($task_name)

        // Filter by user skill level
        WHERE p.difficulty_level IN ['beginner']
           OR ($skill_level IN ['intermediate', 'advanced', 'professional'] AND p.difficulty_level IN ['beginner', 'intermediate'])
           OR ($skill_level IN ['advanced', 'professional'] AND p.difficulty_level IN ['beginner', 'intermediate', 'advanced'])
           OR ($skill_level = 'professional')

        // Get compatible products (accessories)
        OPTIONAL MATCH (p)-[comp:COMPATIBLE_WITH]->(accessory:Product)
        WHERE comp.recommended = true

        // Get required safety equipment
        OPTIONAL MATCH (p)-[safety:REQUIRES_SAFETY]->(safetyEquip:SafetyEquipment)
        WHERE safety.mandatory = true

        // Get required skills
        OPTIONAL MATCH (t)-[skill_rel:REQUIRES_SKILL]->(skill:Skill)
        WHERE skill_rel.is_mandatory = true

        // Get UNSPSC classification
        OPTIONAL MATCH (p)-[:CATEGORIZED_AS]->(unspsc:UNSPSC)

        // Get ETIM classification
        OPTIONAL MATCH (p)-[:CLASSIFIED_BY]->(etim:ETIM)

        RETURN
          p.id AS product_id,
          p.name AS name,
          p.description AS description,
          p.price AS price,
          p.currency AS currency,
          r.confidence AS confidence_score,
          r.usage_frequency AS usage_frequency,
          collect(DISTINCT accessory.name) AS compatible_products,
          collect(DISTINCT safetyEquip.name) AS required_safety,
          collect(DISTINCT skill.name) AS required_skills,
          unspsc.code AS unspsc_code,
          etim.code AS etim_code
        ORDER BY r.confidence DESC, p.price ASC
        LIMIT $max_results
        """

        result = tx.run(query, task_name=task_name, skill_level=skill_level, max_results=max_results)

        recommendations = []
        for record in result:
            recommendations.append(ProductRecommendation(
                product_id=record["product_id"],
                name=record["name"],
                description=record["description"],
                price=float(record["price"]),
                currency=record["currency"],
                confidence_score=float(record["confidence_score"]),
                reasoning=f"Recommended for task: {task_name} (confidence: {record['confidence_score']:.0%}, usage: {record['usage_frequency']})",
                compatible_products=[p for p in record["compatible_products"] if p],
                required_safety=[s for s in record["required_safety"] if s],
                required_skills=[sk for sk in record["required_skills"] if sk],
                unspsc_code=record.get("unspsc_code"),
                etim_code=record.get("etim_code")
            ))

        return recommendations

    def recommend_products_for_project(
        self,
        project_type: str,
        user_skill_level: str = 'beginner',
        budget_max: Optional[float] = None
    ) -> Dict[str, List[ProductRecommendation]]:
        """
        Recommend complete tool set for a project.
        Returns products grouped by task.

        Args:
            project_type: Type of project (e.g., "home_improvement", "plumbing")
            user_skill_level: User's skill level
            budget_max: Maximum budget constraint

        Returns:
            Dict mapping task names to product recommendations
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._query_products_for_project,
                project_type,
                user_skill_level,
                budget_max
            )
            return result

    @staticmethod
    def _query_products_for_project(tx, project_type: str, skill_level: str, budget_max: Optional[float]):
        """Graph traversal for project-based recommendations."""
        query = """
        MATCH (proj:Project)-[:HAS_TASK]->(t:Task)<-[r:USED_FOR]-(p:Product)
        WHERE toLower(proj.type) = toLower($project_type)
          OR toLower(proj.name) CONTAINS toLower($project_type)

        // Filter by skill level
        WHERE p.difficulty_level IN ['beginner']
           OR ($skill_level IN ['intermediate', 'advanced', 'professional'] AND p.difficulty_level IN ['beginner', 'intermediate'])
           OR ($skill_level IN ['advanced', 'professional'])

        // Budget constraint if provided
        WHERE $budget_max IS NULL OR p.price <= $budget_max

        // Get accessories
        OPTIONAL MATCH (p)-[comp:COMPATIBLE_WITH]->(accessory:Product)
        WHERE comp.recommended = true AND comp.required = true

        RETURN
          t.name AS task_name,
          collect(DISTINCT {
            product_id: p.id,
            name: p.name,
            description: p.description,
            price: p.price,
            currency: p.currency,
            confidence: r.confidence,
            is_primary: r.is_primary_tool,
            accessories: collect(DISTINCT accessory.name)
          }) AS products
        ORDER BY t.sequence_order
        """

        result = tx.run(query, project_type=project_type, skill_level=skill_level, budget_max=budget_max)

        project_recommendations = {}
        for record in result:
            task_name = record["task_name"]
            products = record["products"]

            product_recs = []
            for prod in products:
                product_recs.append(ProductRecommendation(
                    product_id=prod["product_id"],
                    name=prod["name"],
                    description=prod["description"],
                    price=float(prod["price"]),
                    currency=prod["currency"],
                    confidence_score=float(prod["confidence"]),
                    reasoning=f"Primary tool for {task_name}" if prod["is_primary"] else f"Alternative for {task_name}",
                    compatible_products=prod["accessories"],
                    required_safety=[],
                    required_skills=[]
                ))

            project_recommendations[task_name] = product_recs

        return project_recommendations

    def find_compatible_products(
        self,
        product_id: str,
        compatibility_type: Optional[str] = None
    ) -> List[ProductRecommendation]:
        """
        Find products compatible with a given product.
        Useful for "Customers who bought X also bought Y" recommendations.

        Args:
            product_id: Product ID to find compatible products for
            compatibility_type: Filter by type (accessory, consumable, complementary)

        Returns:
            List of compatible products with confidence scores
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._query_compatible_products,
                product_id,
                compatibility_type
            )
            return result

    @staticmethod
    def _query_compatible_products(tx, product_id: str, compatibility_type: Optional[str]):
        """Query for product compatibility graph traversal."""
        query = """
        MATCH (source:Product {id: $product_id})-[r:COMPATIBLE_WITH]->(compatible:Product)
        WHERE $compatibility_type IS NULL OR r.compatibility_type = $compatibility_type

        // Get classification for compatible products
        OPTIONAL MATCH (compatible)-[:CATEGORIZED_AS]->(unspsc:UNSPSC)
        OPTIONAL MATCH (compatible)-[:CLASSIFIED_BY]->(etim:ETIM)

        RETURN
          compatible.id AS product_id,
          compatible.name AS name,
          compatible.description AS description,
          compatible.price AS price,
          compatible.currency AS currency,
          r.compatibility_type AS compatibility_type,
          r.recommended AS recommended,
          r.required AS required,
          unspsc.code AS unspsc_code,
          etim.code AS etim_code
        ORDER BY r.recommended DESC, r.required DESC, compatible.price ASC
        """

        result = tx.run(query, product_id=product_id, compatibility_type=compatibility_type)

        compatible_products = []
        for record in result:
            confidence = 1.0 if record["required"] else (0.8 if record["recommended"] else 0.5)
            reasoning_parts = []
            if record["required"]:
                reasoning_parts.append("Required accessory")
            if record["recommended"]:
                reasoning_parts.append("Recommended companion")
            reasoning = " - ".join(reasoning_parts) or "Compatible product"

            compatible_products.append(ProductRecommendation(
                product_id=record["product_id"],
                name=record["name"],
                description=record["description"],
                price=float(record["price"]),
                currency=record["currency"],
                confidence_score=confidence,
                reasoning=f"{reasoning} ({record['compatibility_type']})",
                compatible_products=[],
                required_safety=[],
                required_skills=[],
                unspsc_code=record.get("unspsc_code"),
                etim_code=record.get("etim_code")
            ))

        return compatible_products

    def get_safety_requirements(
        self,
        task_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get mandatory safety equipment for a task.
        Critical for OSHA/ANSI compliance.

        Args:
            task_name: Name of the task

        Returns:
            List of safety equipment with standards
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._query_safety_requirements,
                task_name
            )
            return result

    @staticmethod
    def _query_safety_requirements(tx, task_name: str):
        """Query for safety equipment requirements."""
        query = """
        MATCH (t:Task)<-[:USED_FOR]-(p:Product)-[r:REQUIRES_SAFETY]->(safety:SafetyEquipment)
        WHERE toLower(t.name) CONTAINS toLower($task_name)
          AND safety.mandatory = true

        RETURN DISTINCT
          safety.name AS name,
          safety.description AS description,
          safety.osha_standard AS osha_standard,
          safety.ansi_standard AS ansi_standard,
          safety.mandatory AS mandatory,
          collect(DISTINCT t.name) AS for_tasks
        ORDER BY safety.mandatory DESC
        """

        result = tx.run(query, task_name=task_name)

        safety_requirements = []
        for record in result:
            safety_requirements.append({
                "name": record["name"],
                "description": record["description"],
                "osha_standard": record["osha_standard"],
                "ansi_standard": record["ansi_standard"],
                "mandatory": record["mandatory"],
                "for_tasks": record["for_tasks"]
            })

        return safety_requirements

    def fulltext_search(
        self,
        search_query: str,
        language: str = 'en',
        max_results: int = 20
    ) -> List[ProductRecommendation]:
        """
        Multi-lingual fulltext search using Neo4j fulltext indexes.
        Supports ETIM translations for 13+ languages.

        Args:
            search_query: Search query (product name, description, keywords)
            language: Language code (en, zh, ms, ta, etc.)
            max_results: Maximum results to return

        Returns:
            List of products matching search query
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._query_fulltext_search,
                search_query,
                language,
                max_results
            )
            return result

    @staticmethod
    def _query_fulltext_search(tx, search_query: str, language: str, max_results: int):
        """Fulltext search with ETIM multi-lingual support."""

        if language == 'en':
            # English: Use standard fulltext index
            query = """
            CALL db.index.fulltext.queryNodes("product_search", $search_query)
            YIELD node AS p, score

            OPTIONAL MATCH (p)-[:CATEGORIZED_AS]->(unspsc:UNSPSC)
            OPTIONAL MATCH (p)-[:CLASSIFIED_BY]->(etim:ETIM)

            RETURN
              p.id AS product_id,
              p.name AS name,
              p.description AS description,
              p.price AS price,
              p.currency AS currency,
              score AS confidence_score,
              unspsc.code AS unspsc_code,
              etim.code AS etim_code
            ORDER BY score DESC
            LIMIT $max_results
            """
        else:
            # Other languages: Search ETIM translations
            query = f"""
            MATCH (p:Product)-[:CLASSIFIED_BY]->(etim:ETIM)
            WHERE toLower(etim.translations.{language}) CONTAINS toLower($search_query)
               OR toLower(etim.class_name) CONTAINS toLower($search_query)

            OPTIONAL MATCH (p)-[:CATEGORIZED_AS]->(unspsc:UNSPSC)

            RETURN
              p.id AS product_id,
              p.name AS name,
              p.description AS description,
              p.price AS price,
              p.currency AS currency,
              0.8 AS confidence_score,
              unspsc.code AS unspsc_code,
              etim.code AS etim_code,
              etim.translations.{language} AS translated_name
            LIMIT $max_results
            """

        result = tx.run(query, search_query=search_query, max_results=max_results)

        search_results = []
        for record in result:
            search_results.append(ProductRecommendation(
                product_id=record["product_id"],
                name=record["name"],
                description=record.get("translated_name") or record["description"],
                price=float(record["price"]),
                currency=record["currency"],
                confidence_score=float(record["confidence_score"]),
                reasoning=f"Fulltext search match (score: {record['confidence_score']:.2f})",
                compatible_products=[],
                required_safety=[],
                required_skills=[],
                unspsc_code=record.get("unspsc_code"),
                etim_code=record.get("etim_code")
            ))

        return search_results

    def add_product_with_relationships(
        self,
        product_data: Dict[str, Any],
        tasks: List[str],
        compatible_products: List[str],
        safety_equipment: List[str],
        unspsc_code: Optional[str] = None,
        etim_code: Optional[str] = None
    ) -> bool:
        """
        Add a new product to the knowledge graph with all relationships.
        Admin function for product catalog management.

        Args:
            product_data: Product properties (id, name, description, price, etc.)
            tasks: List of task IDs this product is used for
            compatible_products: List of compatible product IDs
            safety_equipment: List of required safety equipment IDs
            unspsc_code: UNSPSC classification code
            etim_code: ETIM classification code

        Returns:
            True if successful, False otherwise
        """
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_product_with_relationships,
                product_data,
                tasks,
                compatible_products,
                safety_equipment,
                unspsc_code,
                etim_code
            )
            return result

    @staticmethod
    def _create_product_with_relationships(
        tx,
        product_data: Dict,
        tasks: List[str],
        compatible_products: List[str],
        safety_equipment: List[str],
        unspsc_code: Optional[str],
        etim_code: Optional[str]
    ):
        """Transaction to create product node and all relationships."""
        try:
            # Create product node
            create_query = """
            CREATE (p:Product {
              id: $id,
              name: $name,
              description: $description,
              sku: $sku,
              price: $price,
              currency: $currency,
              category: $category,
              brand: $brand,
              keywords: $keywords,
              specifications: $specifications,
              stock_status: $stock_status,
              is_professional: $is_professional,
              difficulty_level: $difficulty_level,
              created_at: datetime(),
              updated_at: datetime()
            })
            RETURN p.id AS product_id
            """

            tx.run(create_query, **product_data)

            # Create relationships to tasks
            for task_id in tasks:
                task_rel_query = """
                MATCH (p:Product {id: $product_id}), (t:Task {id: $task_id})
                MERGE (p)-[:USED_FOR {
                  confidence: 0.9,
                  usage_frequency: 'high',
                  is_primary_tool: true
                }]->(t)
                """
                tx.run(task_rel_query, product_id=product_data['id'], task_id=task_id)

            # Create compatibility relationships
            for compat_id in compatible_products:
                compat_rel_query = """
                MATCH (p:Product {id: $product_id}), (c:Product {id: $compat_id})
                MERGE (p)-[:COMPATIBLE_WITH {
                  compatibility_type: 'accessory',
                  recommended: true,
                  required: false
                }]->(c)
                """
                tx.run(compat_rel_query, product_id=product_data['id'], compat_id=compat_id)

            # Create safety relationships
            for safety_id in safety_equipment:
                safety_rel_query = """
                MATCH (p:Product {id: $product_id}), (s:SafetyEquipment {id: $safety_id})
                MERGE (p)-[:REQUIRES_SAFETY {
                  mandatory: true,
                  osha_compliant: true
                }]->(s)
                """
                tx.run(safety_rel_query, product_id=product_data['id'], safety_id=safety_id)

            # Create classification relationships
            if unspsc_code:
                unspsc_rel_query = """
                MATCH (p:Product {id: $product_id}), (u:UNSPSC {code: $unspsc_code})
                MERGE (p)-[:CATEGORIZED_AS {confidence: 1.0}]->(u)
                """
                tx.run(unspsc_rel_query, product_id=product_data['id'], unspsc_code=unspsc_code)

            if etim_code:
                etim_rel_query = """
                MATCH (p:Product {id: $product_id}), (e:ETIM {code: $etim_code})
                MERGE (p)-[:CLASSIFIED_BY {confidence: 1.0}]->(e)
                """
                tx.run(etim_rel_query, product_id=product_data['id'], etim_code=etim_code)

            logger.info(f"Successfully created product {product_data['id']} with relationships")
            return True

        except Exception as e:
            logger.error(f"Failed to create product with relationships: {e}")
            return False

    def get_learning_path(
        self,
        target_skill: str,
        current_skill_level: str = 'beginner'
    ) -> List[Dict[str, Any]]:
        """
        Generate a learning path for acquiring a skill.
        Returns ordered list of tasks to practice, from easy to advanced.

        Args:
            target_skill: Skill to learn (e.g., "Power Drill Operation")
            current_skill_level: User's current skill level

        Returns:
            List of tasks ordered by difficulty
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._query_learning_path,
                target_skill,
                current_skill_level
            )
            return result

    @staticmethod
    def _query_learning_path(tx, target_skill: str, current_level: str):
        """Query for skill learning path."""
        query = """
        MATCH (skill:Skill)<-[r:REQUIRES_SKILL]-(t:Task)
        WHERE toLower(skill.name) CONTAINS toLower($target_skill)

        // Filter tasks appropriate for current skill level
        WHERE t.difficulty IN
          CASE $current_level
            WHEN 'beginner' THEN ['easy']
            WHEN 'intermediate' THEN ['easy', 'medium']
            WHEN 'advanced' THEN ['easy', 'medium', 'hard']
            ELSE ['easy', 'medium', 'hard']
          END

        // Get tools needed for each task
        OPTIONAL MATCH (p:Product)-[:USED_FOR]->(t)

        RETURN
          t.name AS task_name,
          t.description AS task_description,
          t.difficulty AS difficulty,
          t.estimated_time_minutes AS estimated_time,
          r.learning_time_hours AS learning_time_hours,
          collect(DISTINCT p.name) AS tools_needed
        ORDER BY
          CASE t.difficulty
            WHEN 'easy' THEN 1
            WHEN 'medium' THEN 2
            WHEN 'hard' THEN 3
            ELSE 4
          END,
          t.estimated_time_minutes ASC
        """

        result = tx.run(query, target_skill=target_skill, current_level=current_level)

        learning_path = []
        for idx, record in enumerate(result, 1):
            learning_path.append({
                "step": idx,
                "task_name": record["task_name"],
                "task_description": record["task_description"],
                "difficulty": record["difficulty"],
                "estimated_time_minutes": record["estimated_time"],
                "learning_time_hours": record["learning_time_hours"],
                "tools_needed": record["tools_needed"]
            })

        return learning_path


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    import os

    # Initialize knowledge graph service
    kg = KnowledgeGraphService(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password")
    )

    try:
        # Example 1: Recommend products for a task
        print("\n=== Task-based Recommendations ===")
        recommendations = kg.recommend_products_for_task(
            task_name="drilling holes",
            user_skill_level="beginner",
            max_results=5
        )

        for rec in recommendations:
            print(f"\nProduct: {rec.name}")
            print(f"Price: {rec.currency} {rec.price:.2f}")
            print(f"Confidence: {rec.confidence_score:.0%}")
            print(f"Reasoning: {rec.reasoning}")
            if rec.compatible_products:
                print(f"Accessories: {', '.join(rec.compatible_products)}")
            if rec.required_safety:
                print(f"Safety Required: {', '.join(rec.required_safety)}")

        # Example 2: Get safety requirements
        print("\n\n=== Safety Requirements ===")
        safety = kg.get_safety_requirements("drilling")
        for item in safety:
            print(f"\n{item['name']}")
            print(f"  OSHA: {item['osha_standard']}")
            print(f"  ANSI: {item['ansi_standard']}")
            print(f"  Mandatory: {item['mandatory']}")

        # Example 3: Multi-lingual search
        print("\n\n=== Multi-lingual Search ===")
        results = kg.fulltext_search("电钻", language="zh", max_results=5)
        for result in results:
            print(f"\n{result.name}: {result.description}")
            print(f"  ETIM: {result.etim_code}")

        # Example 4: Learning path
        print("\n\n=== Learning Path ===")
        path = kg.get_learning_path("Power Drill Operation", "beginner")
        for step in path:
            print(f"\nStep {step['step']}: {step['task_name']}")
            print(f"  Difficulty: {step['difficulty']}")
            print(f"  Time: {step['estimated_time_minutes']} minutes")
            print(f"  Tools: {', '.join(step['tools_needed'])}")

    finally:
        kg.close()
```

#### 1.4 Update API Requirements

**File**: `requirements-api.txt`

```txt
# Existing dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
asyncpg==0.29.0
redis==5.0.1
httpx==0.25.1
structlog==23.2.0

# NEW: Neo4j driver for knowledge graph
neo4j==5.15.0

# NEW: Classification and NLP
sentence-transformers==2.2.2  # For ETIM/UNSPSC semantic classification
openai==1.6.1                 # For LLM-powered recommendations

# NEW: Graph algorithms
networkx==3.2.1               # For graph analysis
```

---

### Implementation Checklist - Phase 1

- [ ] Add Neo4j container to `docker-compose.production.yml`
- [ ] Create `init-scripts/neo4j-schema.cypher` with complete schema
- [ ] Create `src/services/knowledge_graph_service.py`
- [ ] Update `requirements-api.txt` with Neo4j driver
- [ ] Create integration tests for knowledge graph service
- [ ] Load sample product data (drill example) into Neo4j
- [ ] Create admin API endpoints for product management
- [ ] Document Neo4j query patterns for developers

**Estimated Time**: 3 weeks
**Dependencies**: None
**Risk Level**: Low (additive, doesn't break existing functionality)

---

## Phase 2: UNSPSC/ETIM Classification System (2 weeks)

**Continuing in next section due to length...**

Would you like me to continue with the remaining 5 phases in the same detail?
