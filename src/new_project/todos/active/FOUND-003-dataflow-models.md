# FOUND-003: DataFlow Models - Horme Product Ecosystem

**Created:** 2025-08-01  
**Assigned:** DataFlow Specialist  
**Priority:** 🔥 High  
**Status:** Not Started  
**Estimated Effort:** 12 hours  
**Due Date:** 2025-08-05

## Description

Create comprehensive DataFlow models for the Horme product ecosystem, including product catalogs, vendor relationships, UNSPSC/ETIM classifications, safety compliance data, and user profiles. These models will auto-generate 9 nodes per model for seamless database operations.

## Acceptance Criteria

- [ ] @db.model decorators properly implemented for all entity types
- [ ] Auto-generated CRUD nodes available for each model (9 nodes per model)
- [ ] PostgreSQL schema supports UNSPSC and ETIM classification hierarchies
- [ ] Safety compliance data models include OSHA/ANSI standards
- [ ] Vendor and product relationship models support complex pricing and availability
- [ ] User profile models include skill assessment and safety certifications
- [ ] All models support soft deletion and audit trails
- [ ] Database migrations created and tested

## Subtasks

- [ ] Core Product Models (Est: 3h)
  - Verification: Product, ProductCategory, ProductSpecification models with auto-generated nodes
  - Output: Complete product catalog structure with UNSPSC/ETIM support
- [ ] Classification System Models (Est: 2h)
  - Verification: UNSPSCCode, ETIMClass models with hierarchical relationships
  - Output: Full classification hierarchy with 5-level UNSPSC and ETIM structure
- [ ] Safety Compliance Models (Est: 2h)
  - Verification: SafetyStandard, ComplianceRequirement, PPERequirement models
  - Output: OSHA/ANSI compliance data with product safety mappings
- [ ] Vendor and Pricing Models (Est: 2h)
  - Verification: Vendor, ProductPricing, InventoryLevel models
  - Output: Multi-vendor pricing and availability tracking
- [ ] User and Profile Models (Est: 2h)
  - Verification: UserProfile, SkillAssessment, SafetyCertification models
  - Output: User profiling for skill-based recommendations
- [ ] Database Migrations (Est: 1h)
  - Verification: All models create proper PostgreSQL tables with indexes

## Dependencies

- FOUND-001: SDK Compliance Foundation (must complete first)
- Requires PostgreSQL database connection
- Integration with existing dataflow_models.py structure

## Risk Assessment

- **HIGH**: Model relationships must support complex queries for recommendations
- **MEDIUM**: UNSPSC/ETIM data hierarchy may require specialized indexing
- **MEDIUM**: Safety compliance models must be legally accurate
- **LOW**: DataFlow auto-generation may need customization for specific use cases

## Model Specifications

### Core Product Models

```python
@db.model
class Product:
    id: int = Field(primary_key=True)
    product_code: str = Field(unique=True, index=True)
    name: str = Field(max_length=255)
    description: str
    brand: str = Field(index=True)
    model_number: str
    unspsc_code: str = Field(foreign_key="UNSPSCCode.code")
    etim_class: str = Field(foreign_key="ETIMClass.class_id")
    specifications: dict  # JSONB field
    safety_rating: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime = Field(null=True)

@db.model
class ProductCategory:
    id: int = Field(primary_key=True)
    name: str = Field(max_length=100)
    parent_id: int = Field(foreign_key="ProductCategory.id", null=True)
    unspsc_segment: str
    unspsc_family: str
    level: int  # Hierarchy level (1-5)
```

### Classification System Models

```python
@db.model
class UNSPSCCode:
    code: str = Field(primary_key=True, max_length=8)  # 8-digit code
    title: str = Field(max_length=255)
    description: str
    segment: str = Field(max_length=2)  # First 2 digits
    family: str = Field(max_length=2)   # Next 2 digits
    class_code: str = Field(max_length=2)  # Next 2 digits
    commodity: str = Field(max_length=2)   # Last 2 digits
    level: int  # 1-5 hierarchy level

@db.model
class ETIMClass:
    class_id: str = Field(primary_key=True)
    name_en: str = Field(max_length=255)
    name_de: str = Field(max_length=255, null=True)
    name_fr: str = Field(max_length=255, null=True)
    description: str
    version: str = Field(default="9.0")
    parent_class: str = Field(foreign_key="ETIMClass.class_id", null=True)
```

### Safety Compliance Models

```python
@db.model
class SafetyStandard:
    id: int = Field(primary_key=True)
    standard_type: str  # OSHA, ANSI, etc.
    standard_code: str = Field(unique=True)
    title: str = Field(max_length=255)
    description: str
    severity_level: str  # critical, high, medium, low
    regulation_text: str
    effective_date: datetime

@db.model
class ComplianceRequirement:
    id: int = Field(primary_key=True)
    product_id: int = Field(foreign_key="Product.id")
    safety_standard_id: int = Field(foreign_key="SafetyStandard.id")
    requirement_text: str
    is_mandatory: bool = Field(default=True)
    ppe_required: bool = Field(default=False)
```

### User Profile Models

```python
@db.model
class UserProfile:
    id: int = Field(primary_key=True)
    user_id: int  # Link to existing user system
    skill_level: str  # beginner, intermediate, advanced, professional
    experience_years: int
    safety_certified: bool = Field(default=False)
    preferred_brands: list = Field(default_factory=list)  # JSON array
    project_types: list = Field(default_factory=list)    # JSON array
    created_at: datetime = Field(default_factory=datetime.now)

@db.model
class SkillAssessment:
    id: int = Field(primary_key=True)
    user_profile_id: int = Field(foreign_key="UserProfile.id")
    skill_category: str  # power_tools, hand_tools, electrical, plumbing
    proficiency_score: int  # 1-100
    assessed_date: datetime = Field(default_factory=datetime.now)
    assessor_type: str  # self, system, professional
```

## Testing Requirements

- [ ] Unit tests: All models create correct database tables
- [ ] Integration tests: Auto-generated nodes function correctly
- [ ] Migration tests: Schema updates work correctly
- [ ] Performance tests: Complex queries on classification hierarchies

## DataFlow Integration Benefits

Each model will automatically generate:
1. CreateNode - Insert new records
2. ReadNode - Query single records
3. UpdateNode - Modify existing records
4. DeleteNode - Soft delete records
5. ListNode - Query multiple records with pagination
6. SearchNode - Full-text search capabilities
7. CountNode - Aggregate counting
8. ExistsNode - Existence checking
9. ValidateNode - Data validation

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All models tested with PostgreSQL database
- [ ] Auto-generated nodes verified and functional
- [ ] Database migrations successfully applied
- [ ] Performance benchmarks established for complex queries
- [ ] Documentation completed for all models and relationships

## Implementation Files

- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\core\models.py`
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\dataflow_models.py` (extend existing)
- Migration files in appropriate migration directory
- Test files in `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\tests\unit\`

## Notes

- Follow existing dataflow_models.py patterns for consistency
- Ensure UNSPSC 5-level hierarchy (Segment > Family > Class > Commodity) is properly modeled
- ETIM class relationships must support multi-language requirements
- Safety compliance models must be legally defensible and auditable
- Consider indexing strategies for performance on large product catalogs

## Progress Log

**2025-08-01:** Task created with comprehensive model specifications for Horme product ecosystem