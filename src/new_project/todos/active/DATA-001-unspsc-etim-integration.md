# DATA-001: UNSPSC/ETIM Integration - Global Classification System

**Created:** 2025-08-01  
**Assigned:** Data Integration Team  
**Priority:** 🔥 High  
**Status:** Not Started  
**Estimated Effort:** 20 hours  
**Due Date:** 2025-08-08

## Description

Implement comprehensive UNSPSC and ETIM classification systems for global product categorization. This system will provide hierarchical product classification, multi-language support, and semantic understanding for the AI recommendation engine.

## Acceptance Criteria

- [ ] UNSPSC 5-level hierarchy implemented (Segment > Family > Class > Commodity)
- [ ] ETIM 9.0 classification system with 5,554 classes integrated
- [ ] Multi-language support for ETIM (13+ languages including EN, DE, FR, ES, IT, JA, KO)
- [ ] Hierarchical traversal and search capabilities
- [ ] Product mapping to both UNSPSC and ETIM codes
- [ ] Classification validation and recommendation system
- [ ] Performance optimization for large-scale classification queries
- [ ] Integration with knowledge graph for semantic relationships

## Subtasks

- [ ] UNSPSC Data Integration (Est: 6h)
  - Verification: Complete UNSPSC taxonomy loaded with 50,000+ codes
  - Output: Hierarchical structure from segments to specific commodities
- [ ] ETIM System Implementation (Est: 6h)
  - Verification: ETIM 9.0 with 5,554 classes and multi-language support
  - Output: Complete ETIM taxonomy with technical attributes
- [ ] Classification Mapping Engine (Est: 4h)
  - Verification: Products automatically classified using both systems
  - Output: Dual classification with confidence scoring
- [ ] Search and Traversal APIs (Est: 2h)
  - Verification: Efficient hierarchy navigation and search capabilities
  - Output: Fast classification lookup and parent/child relationships
- [ ] Knowledge Graph Integration (Est: 2h)
  - Verification: Classification codes linked to tools and tasks in Neo4j
  - Output: Semantic relationships between classifications and recommendations

## Dependencies

- FOUND-003: DataFlow Models (models must exist first)
- Access to official UNSPSC and ETIM data sources
- Neo4j knowledge graph for semantic integration

## Risk Assessment

- **HIGH**: Official classification data licensing and access requirements
- **HIGH**: Multi-language support complexity for international deployment
- **MEDIUM**: Performance optimization for hierarchical queries at scale
- **MEDIUM**: Data quality and completeness of classification mappings
- **LOW**: Classification standards evolution requiring updates

## UNSPSC Implementation

### Hierarchy Structure
```python
# UNSPSC 8-digit code structure: SSFFCCCC
# SS = Segment (2 digits)
# FF = Family (2 digits) 
# CC = Class (2 digits)
# CC = Commodity (2 digits)

class UNSPSCHierarchy:
    segments = {
        "10": "Live Plant and Animal Material and Accessories and Supplies",
        "11": "Mineral and Textile and Inedible Plant and Animal Materials", 
        "12": "Chemicals including Bio Chemicals and Gas Materials",
        "13": "Resin and Rosin and Rubber and Foam and Film and Elastomeric Materials",
        "14": "Paper Materials and Products",
        "15": "Fuels and Fuel Additives and Lubricants and Anti corrosive Materials",
        # ... 50+ segments total
    }
```

### Key Tool Categories in UNSPSC
- **23**: Manufacturing Components and Supplies
- **24**: Industrial Manufacturing and Processing Machinery and Accessories  
- **25**: Tools and General Machinery
- **26**: Material Handling and Conditioning and Storage Machinery and their Accessories and Supplies
- **27**: Distribution and Conditioning Systems and Equipment and Components

## ETIM Implementation

### Classification Structure
```python
# ETIM hierarchical structure
class ETIMHierarchy:
    major_groups = {
        "EC": "Electrical Installation",
        "EG": "Building Technology", 
        "EH": "Tools, Hardware and Site Supplies",  # Primary focus
        "EI": "Information and Communication Technology",
        "EL": "Lighting",
        "EM": "Measurement and Control Technology"
    }
    
    # EH group breakdown for tools
    eh_classes = {
        "EH001": "Hand tools",
        "EH002": "Power tools", 
        "EH003": "Cutting tools",
        "EH004": "Measuring tools",
        "EH005": "Safety equipment",
        # ... 1000+ tool-related classes
    }
```

### Multi-Language Support
```python
class ETIMMultiLanguage:
    supported_languages = [
        "en",  # English
        "de",  # German  
        "fr",  # French
        "es",  # Spanish
        "it",  # Italian
        "ja",  # Japanese
        "ko",  # Korean
        "nl",  # Dutch
        "zh",  # Chinese (Mandarin)
        "pt",  # Portuguese
        "ru",  # Russian
        "tr",  # Turkish
        "pl"   # Polish
    ]
```

## Classification Mapping Engine

### Dual Classification Strategy
```python
class ProductClassificationEngine:
    def classify_product(self, product_data: dict) -> dict:
        """
        Classify product using both UNSPSC and ETIM systems
        Returns classification with confidence scores
        """
        unspsc_match = self.classify_unspsc(product_data)
        etim_match = self.classify_etim(product_data)
        
        return {
            "unspsc": {
                "code": unspsc_match.code,
                "title": unspsc_match.title,
                "confidence": unspsc_match.confidence,
                "hierarchy": unspsc_match.get_hierarchy()
            },
            "etim": {
                "class_id": etim_match.class_id, 
                "name": etim_match.name,
                "confidence": etim_match.confidence,
                "attributes": etim_match.technical_attributes
            }
        }
```

### Machine Learning Classification
```python
class MLClassificationEngine:
    def __init__(self):
        self.text_classifier = pipeline(
            "text-classification",
            model="microsoft/DialoGPT-medium"
        )
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def smart_classify(self, product_description: str) -> dict:
        """Use ML to suggest classifications when manual mapping unavailable"""
        embedding = self.embedding_model.encode(product_description)
        
        # Find most similar classified products
        similar_products = await self.vector_search(embedding, limit=5)
        
        # Aggregate classification suggestions
        return self.aggregate_classifications(similar_products)
```

## Performance Optimization

### Database Indexing Strategy
```sql
-- UNSPSC performance indexes
CREATE INDEX idx_unspsc_segment ON unspsc_codes(segment);
CREATE INDEX idx_unspsc_family ON unspsc_codes(family); 
CREATE INDEX idx_unspsc_class ON unspsc_codes(class_code);
CREATE INDEX idx_unspsc_full_code ON unspsc_codes(code);

-- ETIM performance indexes  
CREATE INDEX idx_etim_parent ON etim_classes(parent_class);
CREATE INDEX idx_etim_name_en ON etim_classes(name_en);
CREATE INDEX idx_etim_search ON etim_classes USING gin(to_tsvector('english', name_en || ' ' || description));

-- Product classification mapping
CREATE INDEX idx_product_unspsc ON products(unspsc_code);
CREATE INDEX idx_product_etim ON products(etim_class);
```

### Caching Strategy
```python
class ClassificationCache:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.cache_ttl = 3600  # 1 hour
    
    async def get_classification_hierarchy(self, code: str) -> dict:
        """Cache hierarchical lookups for performance"""
        cache_key = f"classification:hierarchy:{code}"
        cached = await self.redis_client.get(cache_key)
        
        if cached:
            return json.loads(cached)
            
        hierarchy = await self.build_hierarchy(code)
        await self.redis_client.setex(
            cache_key, 
            self.cache_ttl, 
            json.dumps(hierarchy)
        )
        return hierarchy
```

## Testing Requirements

- [ ] Unit tests: Classification engine accuracy with known products
- [ ] Integration tests: Database performance with 100k+ classifications  
- [ ] Performance tests: Sub-second classification lookup times
- [ ] Multi-language tests: ETIM translations accuracy
- [ ] Hierarchy tests: Parent-child relationship integrity

## API Endpoints

```python
@app.get("/api/v1/classify/{product_id}")
async def classify_product(product_id: int) -> dict:
    """Get UNSPSC and ETIM classifications for product"""

@app.get("/api/v1/unspsc/{code}/hierarchy")  
async def get_unspsc_hierarchy(code: str) -> dict:
    """Get full hierarchy path for UNSPSC code"""

@app.get("/api/v1/etim/{class_id}/attributes")
async def get_etim_attributes(class_id: str) -> dict:
    """Get technical attributes for ETIM class"""

@app.post("/api/v1/classify/suggest")
async def suggest_classification(product_data: dict) -> dict:
    """ML-powered classification suggestion"""
```

## Knowledge Graph Integration

```cypher
// Link classifications to tools and tasks
MATCH (tool:Tool), (task:Task)
WHERE tool.unspsc_code = "25171500" // Power drills
CREATE (unspsc:UNSPSCCode {code: "25171500", title: "Power Drills"})
CREATE (tool)-[:CLASSIFIED_AS]->(unspsc)
CREATE (unspsc)-[:USED_FOR_TASKS]->(task)

// Multi-language ETIM support
CREATE (etim:ETIMClass {
    class_id: "EH001234",
    name_en: "Cordless Drill",
    name_de: "Akku-Bohrmaschine", 
    name_fr: "Perceuse sans fil"
})
```

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Both UNSPSC and ETIM systems fully implemented
- [ ] Multi-language support validated for key markets
- [ ] Performance benchmarks met (<500ms classification lookup)
- [ ] Integration with knowledge graph completed
- [ ] API endpoints documented and tested
- [ ] Data quality validation passed (>95% accuracy)

## Implementation Files

- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\core\classification.py`
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\nodes\classification_nodes.py`
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\services\etim_service.py`
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\services\unspsc_service.py`

## Notes

- ETIM licensing requires membership in ETIM International organization
- UNSPSC data available from GS1 US with licensing requirements  
- Consider using OpenMaterialData Project for open-source alternatives
- Multi-language support critical for international Horme expansion
- Classification accuracy directly impacts recommendation quality

## Progress Log

**2025-08-01:** Task created with comprehensive UNSPSC/ETIM integration requirements based on global standards