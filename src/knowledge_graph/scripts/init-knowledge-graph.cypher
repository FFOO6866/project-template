// Initialize Horme Knowledge Graph Schema
// This script creates the initial schema, indexes, and constraints for the product knowledge graph

// ===========================================
// CONSTRAINTS AND UNIQUE IDENTIFIERS
// ===========================================

// Product node constraints
CREATE CONSTRAINT product_sku_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.sku IS UNIQUE;
CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE;

// Category constraints
CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.category_id IS UNIQUE;
CREATE CONSTRAINT category_slug_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.slug IS UNIQUE;

// Brand constraints  
CREATE CONSTRAINT brand_id_unique IF NOT EXISTS FOR (b:Brand) REQUIRE b.brand_id IS UNIQUE;
CREATE CONSTRAINT brand_slug_unique IF NOT EXISTS FOR (b:Brand) REQUIRE b.slug IS UNIQUE;

// Supplier constraints
CREATE CONSTRAINT supplier_id_unique IF NOT EXISTS FOR (s:Supplier) REQUIRE s.supplier_id IS UNIQUE;

// Project constraints for DIY recommendations
CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (pr:Project) REQUIRE pr.project_id IS UNIQUE;

// ===========================================
// PERFORMANCE INDEXES
// ===========================================

// Product search and filtering indexes
CREATE INDEX product_name_index IF NOT EXISTS FOR (p:Product) ON (p.name);
CREATE INDEX product_category_index IF NOT EXISTS FOR (p:Product) ON (p.category_name);
CREATE INDEX product_brand_index IF NOT EXISTS FOR (p:Product) ON (p.brand_name);
CREATE INDEX product_price_index IF NOT EXISTS FOR (p:Product) ON (p.price);
CREATE INDEX product_availability_index IF NOT EXISTS FOR (p:Product) ON (p.availability);

// Category hierarchy indexes
CREATE INDEX category_parent_index IF NOT EXISTS FOR (c:Category) ON (c.parent_id);
CREATE INDEX category_level_index IF NOT EXISTS FOR (c:Category) ON (c.level);

// Brand hierarchy indexes
CREATE INDEX brand_parent_index IF NOT EXISTS FOR (b:Brand) ON (b.parent_brand_id);

// Relationship confidence indexes for AI-generated relationships
CREATE INDEX relationship_confidence_index IF NOT EXISTS FOR ()-[r]-() ON (r.confidence);
CREATE INDEX relationship_source_index IF NOT EXISTS FOR ()-[r]-() ON (r.source);

// Full-text search indexes for semantic search
CREATE FULLTEXT INDEX product_fulltext_index IF NOT EXISTS FOR (p:Product) ON EACH [p.name, p.description, p.long_description, p.keywords];
CREATE FULLTEXT INDEX category_fulltext_index IF NOT EXISTS FOR (c:Category) ON EACH [c.name, c.description];

// ===========================================
// SAMPLE PRODUCT RELATIONSHIP SCHEMA
// ===========================================

// Create sample nodes to establish schema patterns
// These will be replaced with real data during migration

// Sample categories
MERGE (root:Category {
    category_id: 0,
    name: "Root",
    slug: "root",
    level: 0,
    path: "Root",
    is_active: true
});

MERGE (tools:Category {
    category_id: 1,
    name: "Tools",
    slug: "tools", 
    level: 1,
    path: "Root/Tools",
    parent_id: 0,
    is_active: true
});

MERGE (power_tools:Category {
    category_id: 2,
    name: "Power Tools",
    slug: "power-tools",
    level: 2, 
    path: "Root/Tools/Power Tools",
    parent_id: 1,
    is_active: true
});

// Sample brands with ecosystem relationships
MERGE (makita:Brand {
    brand_id: 1,
    name: "Makita",
    slug: "makita",
    country: "Japan",
    is_active: true
});

MERGE (dewalt:Brand {
    brand_id: 2,
    name: "DeWalt", 
    slug: "dewalt",
    country: "USA",
    is_active: true
});

// Sample products
MERGE (drill:Product {
    product_id: 1,
    sku: "MAK-XPH12Z",
    name: "Makita 18V LXT Hammer Drill",
    slug: "makita-18v-lxt-hammer-drill",
    brand_name: "Makita",
    category_name: "Power Tools",
    price: 129.99,
    availability: "in_stock",
    is_published: true,
    keywords: ["drill", "hammer drill", "18V", "cordless", "construction"]
});

MERGE (battery:Product {
    product_id: 2,
    sku: "MAK-BL1850B",
    name: "Makita 18V LXT 5.0Ah Battery",
    slug: "makita-18v-lxt-battery",
    brand_name: "Makita", 
    category_name: "Batteries",
    price: 89.99,
    availability: "in_stock",
    is_published: true,
    keywords: ["battery", "18V", "lithium", "5.0Ah", "LXT"]
});

MERGE (charger:Product {
    product_id: 3,
    sku: "MAK-DC18RC",
    name: "Makita 18V LXT Rapid Charger",
    slug: "makita-18v-lxt-charger",
    brand_name: "Makita",
    category_name: "Chargers", 
    price: 59.99,
    availability: "in_stock",
    is_published: true,
    keywords: ["charger", "18V", "rapid charging", "LXT"]
});

// Sample project for DIY recommendations
MERGE (bathroom_project:Project {
    project_id: 1,
    name: "Bathroom Renovation", 
    slug: "bathroom-renovation",
    description: "Complete bathroom renovation project",
    difficulty_level: "intermediate",
    estimated_duration: "2-3 weeks",
    budget_range: "medium"
});

// ===========================================
// RELATIONSHIP TYPES AND SAMPLE RELATIONSHIPS
// ===========================================

// Product hierarchy relationships
(drill)-[:BELONGS_TO_CATEGORY]->(power_tools);
(drill)-[:MANUFACTURED_BY]->(makita);
(battery)-[:MANUFACTURED_BY]->(makita);
(charger)-[:MANUFACTURED_BY]->(makita);

// Category hierarchy
(power_tools)-[:PARENT_CATEGORY]->(tools);
(tools)-[:PARENT_CATEGORY]->(root);

// Product compatibility relationships with confidence scores
(drill)-[:COMPATIBLE_WITH {
    confidence: 0.95,
    source: "manufacturer_spec",
    compatibility_type: "battery_system",
    notes: "Same 18V LXT battery system"
}]->(battery);

(battery)-[:COMPATIBLE_WITH {
    confidence: 0.95,
    source: "manufacturer_spec", 
    compatibility_type: "charging_system",
    notes: "LXT battery system"
}]->(charger);

// Usage relationships - what products are used for
(drill)-[:USED_FOR {
    confidence: 0.90,
    source: "product_specifications",
    use_case: "drilling_holes",
    material_types: ["wood", "metal", "masonry"]
}]->(bathroom_project);

// Requirement relationships - what a project needs
(bathroom_project)-[:REQUIRES {
    confidence: 0.85,
    source: "project_analysis",
    requirement_type: "power_tool",
    priority: "high",
    quantity_needed: 1
}]->(drill);

// Alternative product relationships
// Note: This would be populated based on similar specifications and use cases

// Cross-brand compatibility (lower confidence)
// These relationships would be inferred by the AI system

// ===========================================
// RELATIONSHIP INFERENCE SETUP
// ===========================================

// Create indexes for relationship inference algorithms
CREATE INDEX product_specs_index IF NOT EXISTS FOR (p:Product) ON (p.specifications);
CREATE INDEX product_features_index IF NOT EXISTS FOR (p:Product) ON (p.features);

// Temporal indexes for tracking relationship evolution
CREATE INDEX relationship_created_index IF NOT EXISTS FOR ()-[r]-() ON (r.created_at);
CREATE INDEX relationship_updated_index IF NOT EXISTS FOR ()-[r]-() ON (r.updated_at);

// ===========================================
// GRAPH DATA SCIENCE PREPARATION
// ===========================================

// Prepare for Graph Data Science algorithms
// This enables advanced analytics like:
// - Community detection for product clusters
// - Centrality analysis for popular products  
// - Similarity algorithms for recommendations
// - Pathfinding for product relationships

// Create a graph projection for GDS algorithms (will be done via Python API)
// CALL gds.graph.project('product-similarity', ['Product'], ['COMPATIBLE_WITH', 'ALTERNATIVE_TO']);

// ===========================================
// MONITORING AND MAINTENANCE
// ===========================================

// Create constraints for data quality
CREATE CONSTRAINT relationship_confidence_range IF NOT EXISTS FOR ()-[r]-() REQUIRE r.confidence >= 0.0 AND r.confidence <= 1.0;

// Sample queries for testing the schema:

// 1. Find all products compatible with a specific product
// MATCH (p:Product {sku: "MAK-XPH12Z"})-[:COMPATIBLE_WITH*1..2]-(compatible)
// RETURN p.name, collect(compatible.name) as compatible_products;

// 2. Find tools needed for a project
// MATCH (project:Project {name: "Bathroom Renovation"})<-[:USED_FOR]-(tool)
// RETURN project.name, collect(tool.name) as required_tools;

// 3. Find brand ecosystem products
// MATCH (brand:Brand {name: "Makita"})<-[:MANUFACTURED_BY]-(product)
// RETURN brand.name, collect(product.name) as products;

// 4. Semantic search preparation (will be enhanced with vector embeddings)
// CALL db.index.fulltext.queryNodes("product_fulltext_index", "drill hammer 18V") 
// YIELD node, score RETURN node.name, score ORDER BY score DESC LIMIT 10;

RETURN "Knowledge graph schema initialized successfully" AS status;