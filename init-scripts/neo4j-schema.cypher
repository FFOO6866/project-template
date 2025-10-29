// ============================================================================
// Neo4j Knowledge Graph Schema Initialization
// Horme POV - Enterprise AI Recommendation System
// Phase 1: Knowledge Graph Foundation
// ============================================================================
//
// This script initializes the Neo4j knowledge graph schema with:
// - Node constraints and indexes for performance
// - Core node types: Product, Task, Project, Skill, SafetyEquipment, UNSPSC, ETIM
// - Relationship types for tool-to-task, compatibility, safety requirements
// - Full-text search indexes for semantic queries
//
// IMPORTANT: This is production-ready schema with no mock data
// Data will be loaded separately from existing PostgreSQL database
// ============================================================================

// Drop existing constraints and indexes (for clean setup)
DROP CONSTRAINT product_id IF EXISTS;
DROP CONSTRAINT task_id IF EXISTS;
DROP CONSTRAINT project_id IF EXISTS;
DROP CONSTRAINT skill_id IF EXISTS;
DROP CONSTRAINT safety_equipment_id IF EXISTS;
DROP CONSTRAINT unspsc_code IF EXISTS;
DROP CONSTRAINT etim_code IF EXISTS;

DROP INDEX product_name IF EXISTS;
DROP INDEX task_name IF EXISTS;
DROP INDEX product_category IF EXISTS;
DROP INDEX product_brand IF EXISTS;
DROP FULLTEXT INDEX product_search IF EXISTS;
DROP FULLTEXT INDEX task_search IF EXISTS;

// ============================================================================
// Node Constraints (Unique IDs)
// ============================================================================

// Product nodes - Hardware items, tools, materials
CREATE CONSTRAINT product_id IF NOT EXISTS
FOR (p:Product) REQUIRE p.id IS UNIQUE;

// Task nodes - DIY tasks like "drill hole", "paint wall", "install shelf"
CREATE CONSTRAINT task_id IF NOT EXISTS
FOR (t:Task) REQUIRE t.id IS UNIQUE;

// Project nodes - Complete DIY projects like "kitchen renovation", "build deck"
CREATE CONSTRAINT project_id IF NOT EXISTS
FOR (pr:Project) REQUIRE pr.id IS UNIQUE;

// Skill nodes - Required skill levels (beginner, intermediate, expert)
CREATE CONSTRAINT skill_id IF NOT EXISTS
FOR (s:Skill) REQUIRE s.id IS UNIQUE;

// SafetyEquipment nodes - PPE requirements (safety glasses, gloves, masks)
CREATE CONSTRAINT safety_equipment_id IF NOT EXISTS
FOR (se:SafetyEquipment) REQUIRE se.id IS UNIQUE;

// UNSPSC nodes - Industry-standard product classification (5-level hierarchy)
CREATE CONSTRAINT unspsc_code IF NOT EXISTS
FOR (u:UNSPSC) REQUIRE u.code IS UNIQUE;

// ETIM nodes - Multi-lingual product classification (13+ languages)
CREATE CONSTRAINT etim_code IF NOT EXISTS
FOR (e:ETIM) REQUIRE e.code IS UNIQUE;

// ============================================================================
// Performance Indexes
// ============================================================================

// Product indexes for fast lookups
CREATE INDEX product_name IF NOT EXISTS
FOR (p:Product) ON (p.name);

CREATE INDEX product_category IF NOT EXISTS
FOR (p:Product) ON (p.category);

CREATE INDEX product_brand IF NOT EXISTS
FOR (p:Product) ON (p.brand);

CREATE INDEX product_sku IF NOT EXISTS
FOR (p:Product) ON (p.sku);

// Task indexes for task-based search
CREATE INDEX task_name IF NOT EXISTS
FOR (t:Task) ON (t.name);

CREATE INDEX task_category IF NOT EXISTS
FOR (t:Task) ON (t.category);

// Project indexes for project recommendations
CREATE INDEX project_name IF NOT EXISTS
FOR (pr:Project) ON (pr.name);

CREATE INDEX project_category IF NOT EXISTS
FOR (pr:Project) ON (pr.category);

// UNSPSC indexes for classification performance (<500ms requirement)
CREATE INDEX unspsc_segment IF NOT EXISTS
FOR (u:UNSPSC) ON (u.segment);

CREATE INDEX unspsc_family IF NOT EXISTS
FOR (u:UNSPSC) ON (u.family);

CREATE INDEX unspsc_class IF NOT EXISTS
FOR (u:UNSPSC) ON (u.class);

// ============================================================================
// Full-Text Search Indexes (for semantic queries)
// ============================================================================

// Product full-text search - name, description, keywords
CREATE FULLTEXT INDEX product_search IF NOT EXISTS
FOR (p:Product) ON EACH [p.name, p.description, p.keywords];

// Task full-text search - name, description, requirements
CREATE FULLTEXT INDEX task_search IF NOT EXISTS
FOR (t:Task) ON EACH [t.name, t.description, t.requirements];

// Project full-text search - name, description, goals
CREATE FULLTEXT INDEX project_search IF NOT EXISTS
FOR (pr:Project) ON EACH [pr.name, pr.description, pr.goals];

// ============================================================================
// Sample Skill Levels (Production-ready reference data)
// ============================================================================

// Create standard skill level nodes
MERGE (s1:Skill {id: 'skill_beginner', name: 'Beginner', level: 1, description: 'No prior experience required'})
MERGE (s2:Skill {id: 'skill_intermediate', name: 'Intermediate', level: 2, description: 'Basic DIY experience recommended'})
MERGE (s3:Skill {id: 'skill_advanced', name: 'Advanced', level: 3, description: 'Significant DIY experience required'})
MERGE (s4:Skill {id: 'skill_expert', name: 'Expert', level: 4, description: 'Professional-level expertise required'});

// ============================================================================
// Sample Safety Equipment Categories (OSHA/ANSI reference data)
// ============================================================================

// Create standard safety equipment nodes
MERGE (se1:SafetyEquipment {
  id: 'ppe_safety_glasses',
  name: 'Safety Glasses',
  category: 'Eye Protection',
  standard: 'ANSI Z87.1',
  mandatory: true,
  description: 'Impact-resistant safety glasses meeting ANSI Z87.1 standard'
})

MERGE (se2:SafetyEquipment {
  id: 'ppe_work_gloves',
  name: 'Work Gloves',
  category: 'Hand Protection',
  standard: 'ANSI/ISEA 105',
  mandatory: true,
  description: 'Cut-resistant work gloves with appropriate grip'
})

MERGE (se3:SafetyEquipment {
  id: 'ppe_dust_mask',
  name: 'Dust Mask/Respirator',
  category: 'Respiratory Protection',
  standard: 'NIOSH N95',
  mandatory: false,
  description: 'Dust mask or N95 respirator for dust-generating tasks'
})

MERGE (se4:SafetyEquipment {
  id: 'ppe_hearing_protection',
  name: 'Hearing Protection',
  category: 'Hearing Protection',
  standard: 'ANSI S3.19',
  mandatory: false,
  description: 'Earplugs or earmuffs for high-noise tasks'
})

MERGE (se5:SafetyEquipment {
  id: 'ppe_steel_toe_boots',
  name: 'Steel-Toe Boots',
  category: 'Foot Protection',
  standard: 'ASTM F2413',
  mandatory: false,
  description: 'Steel-toe safety boots for heavy object handling'
});

// ============================================================================
// Relationship Type Documentation
// ============================================================================
//
// The following relationship types will be created dynamically as data is loaded:
//
// Product Relationships:
// - (Product)-[:USED_FOR]->(Task)           # Which tasks use this product
// - (Product)-[:REQUIRED_BY]->(Project)     # Which projects need this product
// - (Product)-[:COMPATIBLE_WITH]->(Product) # Compatible products
// - (Product)-[:ALTERNATIVE_TO]->(Product)  # Alternative/substitute products
// - (Product)-[:REQUIRES_SKILL]->(Skill)    # Skill level required to use
// - (Product)-[:REQUIRES_SAFETY]->(SafetyEquipment) # Required PPE
// - (Product)-[:CLASSIFIED_AS]->(UNSPSC)    # UNSPSC classification
// - (Product)-[:CLASSIFIED_AS]->(ETIM)      # ETIM classification
//
// Task Relationships:
// - (Task)-[:PART_OF]->(Project)            # Task is part of project
// - (Task)-[:REQUIRES_SKILL]->(Skill)       # Skill level required
// - (Task)-[:REQUIRES_SAFETY]->(SafetyEquipment) # Required PPE
// - (Task)-[:PREREQUISITE_FOR]->(Task)      # Task must be completed first
//
// Project Relationships:
// - (Project)-[:REQUIRES_SKILL]->(Skill)    # Overall skill level required
//
// Safety Relationships:
// - (Task)-[:HAS_RISK {level: 'high'}]->(SafetyEquipment) # Risk assessment
//
// ============================================================================

// ============================================================================
// Schema Validation Query
// ============================================================================

// Verify schema creation (this will be logged)
CALL db.constraints();
CALL db.indexes();

// Return summary statistics
MATCH (n)
RETURN labels(n)[0] as NodeType, count(n) as Count
ORDER BY Count DESC;

// ============================================================================
// Schema Initialization Complete
// ============================================================================
//
// Next Steps:
// 1. Load product data from PostgreSQL using data migration script
// 2. Create task and project nodes based on Horme business logic
// 3. Establish relationships between products, tasks, and projects
// 4. Load UNSPSC and ETIM classification data
// 5. Test performance with <500ms query requirement
//
// Schema Version: 1.0
// Last Updated: 2025-01-16
// ============================================================================
