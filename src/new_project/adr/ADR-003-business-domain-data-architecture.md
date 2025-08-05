# ADR-003: Business Domain Data Architecture for UNSPSC/ETIM Classification System

## Status
**Proposed**

## Context

The Horme AI Knowledge-Based Assistance System requires a comprehensive data architecture to support dual product classification (UNSPSC/ETIM), safety compliance (OSHA/ANSI), and multi-vendor pricing integration. Based on requirements analysis, the system must handle:

### Business Domain Complexity
- **Dual Classification Standards**: UNSPSC (31,000+ categories) + ETIM (4,000+ classes, 4,500+ features)
- **Safety Compliance**: OSHA/ANSI rule integration with 10,000+ safety requirements
- **Multi-Vendor Integration**: Support for 50+ vendor catalogs with different data formats
- **Knowledge Graph Relationships**: Tool-to-task mappings with 100,000+ relationships
- **Performance Requirements**: <500ms classification, <2s recommendation workflows

### Current DataFlow Model Analysis
The system currently defines 13 DataFlow models that auto-generate 117 nodes (9 per model). However, the business domain requirements need systematic breakdown to ensure these models properly support:

1. **Product Classification Workflows**
2. **Safety Compliance Validation**
3. **Multi-Vendor Price Comparison**
4. **Skill-Based Recommendations**
5. **Project Planning Optimization**

### Data Architecture Challenges
- **Classification Hierarchy Traversal**: Efficient navigation of deep classification trees
- **Cross-Standard Mapping**: UNSPSC ↔ ETIM bidirectional mapping
- **Real-Time Safety Validation**: OSHA/ANSI rule engine integration
- **Vector Similarity Search**: Product embedding similarity with 99%+ accuracy
- **Multi-Tenant Data Isolation**: Vendor-specific pricing and availability

## Decision

We will implement a **Hybrid Multi-Store Data Architecture** combining relational, graph, and vector databases optimized for business domain requirements.

### Core Data Architecture Components

#### 1. **Classification Data Layer** (PostgreSQL + pgvector)
```sql
-- UNSPSC Classification Hierarchy
CREATE TABLE unspsc_segments (
    segment_code CHAR(2) PRIMARY KEY,
    segment_title VARCHAR(255) NOT NULL,
    description TEXT
);

CREATE TABLE unspsc_families (
    family_code CHAR(4) PRIMARY KEY,
    segment_code CHAR(2) REFERENCES unspsc_segments(segment_code),
    family_title VARCHAR(255) NOT NULL,
    description TEXT
);

CREATE TABLE unspsc_classes (
    class_code CHAR(6) PRIMARY KEY,
    family_code CHAR(4) REFERENCES unspsc_families(family_code),
    class_title VARCHAR(255) NOT NULL,
    description TEXT
);

CREATE TABLE unspsc_commodities (
    commodity_code CHAR(8) PRIMARY KEY,
    class_code CHAR(6) REFERENCES unspsc_classes(class_code),
    commodity_title VARCHAR(255) NOT NULL,
    description TEXT,
    embedding vector(1536) -- OpenAI embedding
);

-- ETIM Classification Structure
CREATE TABLE etim_groups (
    group_code VARCHAR(10) PRIMARY KEY,
    group_name_en VARCHAR(255),
    group_name_de VARCHAR(255),
    description TEXT
);

CREATE TABLE etim_classes (
    class_code VARCHAR(10) PRIMARY KEY,
    group_code VARCHAR(10) REFERENCES etim_groups(group_code),
    class_name_en VARCHAR(255),
    class_name_de VARCHAR(255),
    description TEXT
);

-- Cross-Standard Mapping
CREATE TABLE unspsc_etim_mapping (
    id SERIAL PRIMARY KEY,
    unspsc_code CHAR(8) REFERENCES unspsc_commodities(commodity_code),
    etim_code VARCHAR(10) REFERENCES etim_classes(class_code),
    confidence_score DECIMAL(3,2), -- 0.00-1.00
    mapping_type VARCHAR(20) -- 'exact', 'partial', 'related'
);
```

#### 2. **Product Data Layer** (DataFlow Models)
```python
from kailash_dataflow import db

@db.model
class Product(db.Model):
    """Core product information with dual classification"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text)
    manufacturer = db.Column(db.String(100), index=True)
    model_number = db.Column(db.String(100), index=True)
    
    # Classification codes
    unspsc_code = db.Column(db.String(8), index=True)
    etim_code = db.Column(db.String(10), index=True)
    
    # Safety and compliance
    safety_rating = db.Column(db.String(20))
    osha_compliant = db.Column(db.Boolean, default=False)
    ansi_standards = db.Column(db.JSON)  # Array of ANSI standard codes
    
    # Pricing and availability
    base_price = db.Column(db.Decimal(10, 2))
    currency = db.Column(db.String(3), default='USD')
    availability_status = db.Column(db.String(20))
    
    # Vector embeddings
    description_embedding = db.Column(db.Vector(1536))
    feature_embedding = db.Column(db.Vector(1536))

@db.model
class SafetyRequirement(db.Model):
    """OSHA/ANSI safety requirements and rules"""
    id = db.Column(db.Integer, primary_key=True)
    regulation_type = db.Column(db.String(20))  # 'OSHA', 'ANSI', 'ISO'
    regulation_code = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    severity_level = db.Column(db.String(20))  # 'critical', 'warning', 'info'
    
    # Applicability rules
    applicable_products = db.Column(db.JSON)  # UNSPSC codes array
    applicable_tasks = db.Column(db.JSON)     # Task type array
    applicable_environments = db.Column(db.JSON)  # Environment codes

@db.model
class Vendor(db.Model):
    """Multi-vendor catalog integration"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    api_endpoint = db.Column(db.String(255))
    api_key_encrypted = db.Column(db.Text)
    catalog_format = db.Column(db.String(20))  # 'json', 'xml', 'csv'
    
    # Business terms
    discount_tier = db.Column(db.String(20))
    payment_terms = db.Column(db.String(50))
    shipping_zones = db.Column(db.JSON)
    
    # Integration status
    last_sync = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20))
    error_count = db.Column(db.Integer, default=0)

@db.model
class VendorPricing(db.Model):
    """Vendor-specific pricing and availability"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    
    # Pricing information
    vendor_sku = db.Column(db.String(100), index=True)
    unit_price = db.Column(db.Decimal(10, 2))
    bulk_pricing = db.Column(db.JSON)  # Tier pricing structure
    
    # Availability
    stock_quantity = db.Column(db.Integer)
    lead_time_days = db.Column(db.Integer)
    minimum_order_qty = db.Column(db.Integer, default=1)
    
    # Last updated
    price_updated = db.Column(db.DateTime)
    stock_updated = db.Column(db.DateTime)

@db.model
class UserProfile(db.Model):
    """User skill profiles for personalized recommendations"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    
    # Skill assessment
    skill_level = db.Column(db.String(20))  # 'beginner', 'intermediate', 'expert'
    experience_years = db.Column(db.Integer)
    specializations = db.Column(db.JSON)  # Array of specialization codes
    
    # Safety certifications
    safety_certifications = db.Column(db.JSON)
    certification_expiry = db.Column(db.JSON)
    
    # Preferences
    preferred_brands = db.Column(db.JSON)
    budget_range = db.Column(db.JSON)  # {'min': 0, 'max': 1000}
    tool_preferences = db.Column(db.JSON)
```

#### 3. **Knowledge Graph Layer** (Neo4j)
```cypher
// Tool-to-Task Relationship Model
CREATE (p:Product {
    id: $product_id,
    name: $name,
    unspsc_code: $unspsc_code,
    etim_code: $etim_code
});

CREATE (t:Task {
    id: $task_id,
    name: $task_name,
    difficulty_level: $difficulty,
    safety_risk: $risk_level
});

CREATE (s:Skill {
    code: $skill_code,
    name: $skill_name,
    category: $category
});

// Relationships
CREATE (p)-[:SUITABLE_FOR {
    effectiveness_score: $effectiveness,
    safety_rating: $safety,
    user_skill_required: $skill_level
}]->(t);

CREATE (t)-[:REQUIRES_SKILL {
    proficiency_level: $level,
    critical: $is_critical
}]->(s);

CREATE (p)-[:COMPLIES_WITH {
    regulation_type: $reg_type,
    compliance_score: $score
}]->(safety:SafetyRegulation);
```

#### 4. **Vector Search Layer** (ChromaDB)
```python
# Product Embedding Collections
product_descriptions = {
    "collection_name": "product_descriptions",
    "embedding_dimension": 1536,
    "metadata_schema": {
        "unspsc_code": "string",
        "etim_code": "string", 
        "manufacturer": "string",
        "price_range": "string",
        "safety_rating": "string"
    }
}

product_features = {
    "collection_name": "product_features",
    "embedding_dimension": 1536,
    "metadata_schema": {
        "feature_type": "string",
        "measurement_unit": "string",
        "value_range": "string"
    }
}

safety_regulations = {
    "collection_name": "safety_requirements",
    "embedding_dimension": 1536,
    "metadata_schema": {
        "regulation_type": "string",
        "severity": "string",
        "applicable_tasks": "list"
    }
}
```

## Business Domain Requirements Matrix

### Functional Requirements

| REQ-ID | Business Requirement | Implementation | Performance Target | Validation Criteria |
|--------|---------------------|----------------|-------------------|-------------------|
| **BUS-001** | Dual Product Classification | UNSPSC + ETIM lookup with cross-mapping | <500ms per product | 95%+ accuracy on test dataset |
| **BUS-002** | Safety Compliance Validation | OSHA/ANSI rule engine with Neo4j relationships | <1s per validation | 100% regulatory coverage |
| **BUS-003** | Multi-Vendor Price Comparison | Vendor API integration with pricing aggregation | <2s for 10+ vendors | Real-time pricing accuracy |
| **BUS-004** | Skill-Based Recommendations | User profile matching with knowledge graph | <2s per recommendation | 25%+ relevance improvement |
| **BUS-005** | Project Planning Optimization | Task decomposition with tool-to-task mapping | <3s per project plan | 90%+ task coverage |

### Data Quality Requirements

| REQ-ID | Data Quality Requirement | Implementation | Monitoring | Acceptance Criteria |
|--------|--------------------------|----------------|------------|-------------------|
| **DQ-001** | Classification Accuracy | Automated validation against reference datasets | Daily accuracy reports | >95% classification accuracy |
| **DQ-002** | Pricing Data Freshness | Vendor API sync with staleness detection | Real-time sync monitoring | <24h price staleness |
| **DQ-003** | Safety Regulation Currency | Regulatory database updates with change tracking | Monthly compliance audits | 100% current regulations |
| **DQ-004** | Cross-Standard Mapping Quality | UNSPSC↔ETIM mapping validation and confidence scoring | Mapping quality metrics | >90% high-confidence mappings |

### Integration Requirements

| REQ-ID | Integration Requirement | Components | SLA Target | Validation Method |
|--------|------------------------|------------|------------|------------------|
| **INT-001** | Real-Time Classification | PostgreSQL + ChromaDB + OpenAI | <500ms end-to-end | Performance testing |
| **INT-002** | Knowledge Graph Queries | Neo4j + DataFlow models | <800ms graph traversal | Load testing |
| **INT-003** | Vector Similarity Search | ChromaDB + OpenAI embeddings | <300ms similarity search | Benchmark testing |
| **INT-004** | Vendor API Orchestration | Multiple vendor APIs + rate limiting | <2s aggregated results | Integration testing |

## Implementation Strategy

### Phase 1: Core Data Models (Week 1-2)
1. **DataFlow Model Implementation**
   - Implement 13 DataFlow models with @db.model decorators
   - Validate auto-generation of 117 nodes (9 per model)
   - Ensure SDK compliance for all generated nodes

2. **Database Schema Deployment**  
   - PostgreSQL schema with pgvector extension
   - UNSPSC/ETIM classification tables
   - Cross-mapping relationship tables

3. **Basic CRUD Operations**
   - Test all 117 auto-generated DataFlow nodes
   - Validate parameter patterns and node registration
   - Performance baseline establishment

### Phase 2: Business Logic Implementation (Week 3-4)
1. **Classification Engine**
   - Dual UNSPSC/ETIM classification workflows
   - Cross-standard mapping with confidence scoring
   - Vector similarity search integration

2. **Safety Compliance Engine**
   - OSHA/ANSI rule engine implementation
   - Neo4j relationship modeling
   - Real-time compliance validation

3. **Multi-Vendor Integration**
   - Vendor API integration framework
   - Pricing aggregation and comparison
   - Real-time inventory status

### Phase 3: Advanced Features (Week 5-6)
1. **Knowledge Graph Intelligence**
   - Tool-to-task relationship modeling
   - Skill-based recommendation engine
   - Project planning optimization

2. **Performance Optimization**
   - Database query optimization
   - Vector search performance tuning
   - Caching strategy implementation

## Technical Specifications

### Database Performance Requirements
```sql
-- Index Strategy for Classification Performance
CREATE INDEX idx_products_unspsc ON products(unspsc_code);
CREATE INDEX idx_products_etim ON products(etim_code);
CREATE INDEX idx_products_embedding_similarity ON products USING ivfflat (description_embedding vector_cosine_ops);

-- Query Performance Targets
-- Product lookup by UNSPSC: <50ms
-- Cross-standard mapping: <100ms
-- Vector similarity search: <200ms
-- Safety compliance check: <300ms
```

### API Response Schema
```typescript
interface ClassificationResponse {
  product_id: number;
  unspsc: {
    code: string;
    title: string;
    confidence: number;
  };
  etim: {
    code: string;
    title: string;
    confidence: number;
  };
  safety_compliance: {
    osha_compliant: boolean;
    ansi_standards: string[];
    risk_level: 'low' | 'medium' | 'high';
  };
  recommendations: Product[];
  response_time_ms: number;
}
```

### Performance Monitoring
```yaml
# SLA Monitoring Configuration
classification_sla:
  target_response_time: 500ms
  success_rate_threshold: 99.5%
  error_rate_threshold: 0.5%

safety_validation_sla:
  target_response_time: 1000ms
  compliance_accuracy: 100%
  regulation_coverage: 100%

recommendation_sla:
  target_response_time: 2000ms
  relevance_improvement: 25%
  user_satisfaction: 85%
```

## Consequences

### Positive Outcomes

#### Business Value Delivery
- **Accurate Classification**: Dual UNSPSC/ETIM coverage provides global product categorization
- **Safety Assurance**: Comprehensive OSHA/ANSI compliance reduces liability risk
- **Cost Optimization**: Multi-vendor pricing comparison drives purchasing efficiency
- **Personalization**: Skill-based recommendations improve user experience and task success
- **Scalability**: Architecture supports 100,000+ products with sub-second response times

#### Technical Benefits
- **Data Consistency**: Single source of truth for product classification and safety data
- **Performance Optimization**: Hybrid storage strategy optimized for different query patterns
- **Vendor Flexibility**: Pluggable vendor integration supports diverse catalog formats
- **Real-Time Updates**: Event-driven architecture ensures data freshness
- **Compliance Automation**: Automated safety validation reduces manual oversight

### Negative Consequences

#### Complexity Overhead
- **Multi-Store Complexity**: Three different database technologies require specialized expertise
- **Data Synchronization**: Cross-system consistency requires sophisticated event handling
- **Integration Maintenance**: 50+ vendor integrations create ongoing maintenance burden
- **Performance Tuning**: Query optimization across multiple systems requires deep technical knowledge

#### Business Risk
- **Data Quality Dependencies**: Inaccurate vendor data impacts recommendation quality
- **Regulatory Change Management**: Safety regulations change frequently requiring rapid updates
- **Vendor Relationship Management**: API changes from vendors can break integrations
- **Classification Accuracy**: Incorrect classifications could lead to safety incidents

### Technical Debt
- **Cross-System Query Optimization**: Complex queries spanning multiple data stores
- **Data Migration Complexity**: Schema changes impact multiple interconnected systems
- **Monitoring and Observability**: Comprehensive monitoring across hybrid architecture
- **Backup and Recovery**: Point-in-time recovery across multiple data stores

## Alternatives Considered

### Option 1: Single PostgreSQL Database
- **Pros**: Simpler architecture, ACID compliance, mature tooling
- **Cons**: Poor performance for vector similarity search, limited graph query capabilities
- **Rejection Reason**: Cannot meet <300ms vector search SLA requirements

### Option 2: MongoDB-Only Architecture  
- **Pros**: Flexible schema, good performance, single technology stack
- **Cons**: Limited vector search capabilities, poor graph relationship modeling
- **Rejection Reason**: Insufficient support for complex classification hierarchies

### Option 3: Pure Graph Database (Neo4j Only)
- **Pros**: Excellent relationship modeling, powerful graph queries
- **Cons**: Poor performance for large-scale vector operations, complex pricing queries
- **Rejection Reason**: Vector similarity search performance inadequate for business requirements

## Implementation Plan

### Dependencies
- PostgreSQL 15 with pgvector extension
- Neo4j 5.3 with APOC procedures
- ChromaDB for vector operations
- OpenAI API for embedding generation
- DataFlow framework for model-to-node generation

### Testing Strategy
- **Unit Tests**: DataFlow model validation, classification accuracy
- **Integration Tests**: Cross-system query performance, vendor API integration
- **Performance Tests**: SLA validation under realistic load
- **Business Tests**: End-to-end workflow validation with real data

### Success Criteria
- **Classification Accuracy**: >95% on standardized test datasets
- **Performance Compliance**: All SLA targets met under load
- **Data Quality**: >99% data freshness and accuracy metrics
- **Business Value**: 25%+ improvement in recommendation relevance
- **System Reliability**: 99.9% uptime with automated failover

---

*This ADR establishes the business domain data architecture foundation that enables the Horme AI system to deliver accurate, safe, and cost-effective tool recommendations while maintaining high performance and regulatory compliance.*