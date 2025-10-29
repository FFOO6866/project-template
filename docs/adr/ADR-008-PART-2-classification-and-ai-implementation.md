# ADR-008 PART 2: Classification, AI, Safety & Multi-lingual Implementation

**Continuation of**: ADR-008-enterprise-recommendation-system-implementation.md
**Status**: PROPOSED
**Date**: 2025-01-16

---

## Phase 2: UNSPSC/ETIM Classification System (2 weeks)

### Overview

Implement industry-standard product classification using UNSPSC (United Nations Standard Products and Services Code) and ETIM (Electrotechnical Information Model) for:
- Accurate product categorization (<500ms classification time requirement)
- Multi-lingual support (13+ languages via ETIM)
- Industry-standard compliance for procurement
- Better search and filtering capabilities

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                Classification Service                         │
│                                                               │
│  ┌────────────┐         ┌────────────┐                      │
│  │  UNSPSC    │         │   ETIM     │                      │
│  │ Classifier │         │ Classifier │                      │
│  │            │         │            │                      │
│  │ - 5-level  │         │ - Classes  │                      │
│  │   hierarchy│         │ - Features │                      │
│  │ - Rules    │         │ - 13+ langs│                      │
│  └─────┬──────┘         └─────┬──────┘                      │
│        │                      │                              │
│        └──────────┬───────────┘                              │
│                   │                                          │
│                   ▼                                          │
│       ┌─────────────────────┐                                │
│       │  Semantic Matcher   │                                │
│       │  (Sentence-BERT)    │                                │
│       └─────────────────────┘                                │
│                   │                                          │
│                   ▼                                          │
│       ┌─────────────────────┐                                │
│       │  Neo4j Integration  │                                │
│       │  (Store in graph)   │                                │
│       └─────────────────────┘                                │
└──────────────────────────────────────────────────────────────┘
```

### Implementation

#### 2.1 UNSPSC Classification Data

**File**: `data/classification/unspsc_codes.json`

```json
{
  "version": "24.0901",
  "last_updated": "2024-09-01",
  "categories": [
    {
      "segment": "27",
      "segment_name": "Tools and General Machinery",
      "families": [
        {
          "family": "11",
          "family_name": "Hand tools",
          "classes": [
            {
              "class": "15",
              "class_name": "Non powered hand tools",
              "commodities": [
                {"commodity": "00", "commodity_name": "Hammers"},
                {"commodity": "01", "commodity_name": "Screwdrivers"},
                {"commodity": "02", "commodity_name": "Pliers"},
                {"commodity": "03", "commodity_name": "Wrenches"}
              ]
            },
            {
              "class": "20",
              "class_name": "Powered hand tools",
              "commodities": [
                {"commodity": "00", "commodity_name": "Drills"},
                {"commodity": "01", "commodity_name": "Sanders"},
                {"commodity": "02", "commodity_name": "Saws"},
                {"commodity": "03", "commodity_name": "Grinders"}
              ]
            }
          ]
        },
        {
          "family": "12",
          "family_name": "Tool Accessories",
          "classes": [
            {
              "class": "10",
              "class_name": "Drill accessories",
              "commodities": [
                {"commodity": "00", "commodity_name": "Drill bits"},
                {"commodity": "01", "commodity_name": "Drill chucks"},
                {"commodity": "02", "commodity_name": "Drill depth stops"}
              ]
            }
          ]
        }
      ]
    },
    {
      "segment": "46",
      "segment_name": "Defense and Law Enforcement and Security and Safety Equipment and Supplies",
      "families": [
        {
          "family": "18",
          "family_name": "Safety and protection equipment",
          "classes": [
            {
              "class": "10",
              "class_name": "Personal safety and protection",
              "commodities": [
                {"commodity": "01", "commodity_name": "Safety glasses or goggles"},
                {"commodity": "02", "commodity_name": "Hearing protection"},
                {"commodity": "03", "commodity_name": "Respiratory protection"},
                {"commodity": "04", "commodity_name": "Protective gloves"}
              ]
            }
          ]
        }
      ]
    }
  ],
  "classification_rules": [
    {
      "pattern": "drill.*cordless|cordless.*drill",
      "code": "27112000",
      "confidence": 0.95
    },
    {
      "pattern": "safety.*glasses|protective.*eyewear",
      "code": "46181001",
      "confidence": 0.98
    },
    {
      "pattern": "drill.*bits|hss.*bits",
      "code": "27121000",
      "confidence": 0.92
    }
  ]
}
```

#### 2.2 ETIM Classification Data

**File**: `data/classification/etim_classes.json`

```json
{
  "version": "9.0",
  "last_updated": "2024-01-01",
  "classes": [
    {
      "code": "EC001489",
      "group": "EG000031",
      "sector": "ES01",
      "class_name_en": "Drill/screwdriver",
      "translations": {
        "de": "Bohrschrauber",
        "fr": "Perceuse-visseuse",
        "es": "Taladro atornillador",
        "it": "Trapano avvitatore",
        "nl": "Boor-/schroefmachine",
        "pt": "Berbequim/aparafusadora",
        "zh": "电钻/螺丝刀",
        "ja": "ドリル/ドライバー",
        "ko": "드릴/드라이버",
        "ms": "Gerudi/pemutar skru",
        "ta": "துளையிடும் கருவி/திருகு விடுபவர்",
        "th": "สว่าน/ไขควง",
        "vi": "Máy khoan/vặn vít"
      },
      "features": [
        {
          "code": "EF000110",
          "name": "Supply voltage",
          "unit": "V",
          "type": "numeric",
          "translations": {
            "de": "Versorgungsspannung",
            "zh": "电源电压",
            "ms": "Voltan bekalan"
          }
        },
        {
          "code": "EF000112",
          "name": "Battery technology",
          "type": "enum",
          "values": ["Li-Ion", "Ni-Cd", "Ni-MH"],
          "translations": {
            "de": "Batterietechnologie",
            "zh": "电池技术",
            "ms": "Teknologi bateri"
          }
        },
        {
          "code": "EF000245",
          "name": "Max. torque",
          "unit": "Nm",
          "type": "numeric",
          "translations": {
            "de": "Max. Drehmoment",
            "zh": "最大扭矩",
            "ms": "Tork maksimum"
          }
        }
      ]
    },
    {
      "code": "EC000123",
      "group": "EG000010",
      "sector": "ES01",
      "class_name_en": "Safety glasses",
      "translations": {
        "de": "Schutzbrille",
        "fr": "Lunettes de protection",
        "es": "Gafas de seguridad",
        "zh": "安全眼镜",
        "ms": "Cermin mata keselamatan",
        "ta": "பாதுகாப்பு கண்ணாடிகள்"
      },
      "features": [
        {
          "code": "EF000301",
          "name": "Protection class",
          "type": "enum",
          "values": ["Basic", "Enhanced", "High Performance"],
          "translations": {
            "de": "Schutzklasse",
            "zh": "防护等级"
          }
        },
        {
          "code": "EF000302",
          "name": "Lens material",
          "type": "enum",
          "values": ["Polycarbonate", "Glass", "Acrylic"]
        }
      ]
    }
  ],
  "classification_rules": [
    {
      "keywords": ["drill", "cordless", "battery", "lithium"],
      "etim_code": "EC001489",
      "confidence": 0.9
    },
    {
      "keywords": ["safety", "glasses", "protective", "eyewear", "goggles"],
      "etim_code": "EC000123",
      "confidence": 0.95
    }
  ]
}
```

#### 2.3 Classification Service Implementation

**File**: `src/services/classification_service.py`

```python
"""
UNSPSC/ETIM Classification Service
Provides industry-standard product classification with <500ms performance
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer, util
import torch

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Classification result with confidence score."""
    unspsc_code: str
    unspsc_name: str
    etim_code: str
    etim_name: str
    etim_translations: Dict[str, str]
    confidence_score: float
    classification_method: str  # 'rule', 'semantic', 'hybrid'


class ProductClassifier:
    """
    Fast product classification using UNSPSC and ETIM standards.
    Performance target: <500ms per classification.
    """

    def __init__(self, data_dir: str = "data/classification"):
        """
        Initialize classifier with UNSPSC and ETIM data.

        Args:
            data_dir: Directory containing classification data files
        """
        self.data_dir = Path(data_dir)

        # Load classification data
        self.unspsc_data = self._load_json("unspsc_codes.json")
        self.etim_data = self._load_json("etim_classes.json")

        # Build lookup indices for fast retrieval
        self.unspsc_index = self._build_unspsc_index()
        self.etim_index = self._build_etim_index()

        # Load semantic model for similarity matching
        logger.info("Loading sentence-transformers model for semantic classification...")
        self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast model, 80MB
        logger.info("Sentence-transformers model loaded")

        # Pre-compute embeddings for ETIM class names (performance optimization)
        self.etim_embeddings = self._precompute_etim_embeddings()

        logger.info(f"Classifier initialized with {len(self.unspsc_index)} UNSPSC codes and {len(self.etim_index)} ETIM classes")

    def _load_json(self, filename: str) -> Dict:
        """Load JSON classification data."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            logger.warning(f"Classification file not found: {filepath}, using empty data")
            return {}

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _build_unspsc_index(self) -> Dict[str, Dict]:
        """Build fast lookup index for UNSPSC codes."""
        index = {}

        if not self.unspsc_data:
            return index

        for segment in self.unspsc_data.get('categories', []):
            for family in segment.get('families', []):
                for cls in family.get('classes', []):
                    for commodity in cls.get('commodities', []):
                        code = f"{segment['segment']}{family['family']}{cls['class']}{commodity['commodity']}"
                        index[code] = {
                            'code': code,
                            'segment': segment['segment'],
                            'segment_name': segment['segment_name'],
                            'family': family['family'],
                            'family_name': family['family_name'],
                            'class': cls['class'],
                            'class_name': cls['class_name'],
                            'commodity': commodity['commodity'],
                            'commodity_name': commodity['commodity_name'],
                            'full_name': f"{segment['segment_name']} > {family['family_name']} > {cls['class_name']} > {commodity['commodity_name']}"
                        }

        return index

    def _build_etim_index(self) -> Dict[str, Dict]:
        """Build fast lookup index for ETIM classes."""
        index = {}

        if not self.etim_data:
            return index

        for etim_class in self.etim_data.get('classes', []):
            code = etim_class['code']
            index[code] = etim_class

        return index

    def _precompute_etim_embeddings(self) -> Dict[str, torch.Tensor]:
        """Pre-compute embeddings for all ETIM class names for fast semantic search."""
        embeddings = {}

        if not self.etim_index:
            return embeddings

        # Collect all class names
        class_names = []
        class_codes = []

        for code, etim_class in self.etim_index.items():
            class_names.append(etim_class['class_name_en'])
            class_codes.append(code)

            # Also include translations for multi-lingual support
            for lang, translation in etim_class.get('translations', {}).items():
                class_names.append(translation)
                class_codes.append(f"{code}_{lang}")

        # Compute embeddings in batch (much faster)
        logger.info(f"Pre-computing embeddings for {len(class_names)} ETIM class names...")
        embeddings_tensor = self.semantic_model.encode(class_names, convert_to_tensor=True, show_progress_bar=False)

        # Store in dictionary
        for code, embedding in zip(class_codes, embeddings_tensor):
            embeddings[code] = embedding

        logger.info(f"Pre-computed {len(embeddings)} ETIM embeddings")
        return embeddings

    def classify_product(
        self,
        product_name: str,
        product_description: str,
        product_keywords: List[str] = None,
        language: str = 'en'
    ) -> ClassificationResult:
        """
        Classify a product using UNSPSC and ETIM standards.
        Uses hybrid approach: rule-based + semantic matching.

        Args:
            product_name: Product name
            product_description: Product description
            product_keywords: Optional list of keywords
            language: Language code for ETIM translations

        Returns:
            ClassificationResult with UNSPSC and ETIM codes

        Performance: <500ms target
        """
        # Step 1: Try rule-based classification (fastest)
        unspsc_result = self._classify_unspsc_rules(product_name, product_description)
        etim_result = self._classify_etim_rules(product_name, product_description, product_keywords)

        if unspsc_result and etim_result:
            # Both classifications successful via rules
            return ClassificationResult(
                unspsc_code=unspsc_result['code'],
                unspsc_name=unspsc_result['full_name'],
                etim_code=etim_result['code'],
                etim_name=etim_result['class_name_en'],
                etim_translations=etim_result.get('translations', {}),
                confidence_score=min(unspsc_result['confidence'], etim_result['confidence']),
                classification_method='rule'
            )

        # Step 2: Semantic matching (slower but more accurate)
        if not etim_result:
            etim_result = self._classify_etim_semantic(product_name, product_description, language)

        if not unspsc_result:
            # Use ETIM to infer UNSPSC (fallback mapping)
            unspsc_result = self._infer_unspsc_from_etim(etim_result) if etim_result else None

        # Step 3: Return best available classification
        if unspsc_result and etim_result:
            return ClassificationResult(
                unspsc_code=unspsc_result['code'],
                unspsc_name=unspsc_result.get('full_name', 'Unknown'),
                etim_code=etim_result['code'],
                etim_name=etim_result['class_name_en'],
                etim_translations=etim_result.get('translations', {}),
                confidence_score=etim_result['confidence'],
                classification_method='semantic'
            )

        # Fallback: Return generic classification
        logger.warning(f"Could not classify product: {product_name}")
        return ClassificationResult(
            unspsc_code='00000000',
            unspsc_name='Unclassified',
            etim_code='EC000000',
            etim_name='Unclassified',
            etim_translations={},
            confidence_score=0.0,
            classification_method='fallback'
        )

    def _classify_unspsc_rules(
        self,
        product_name: str,
        product_description: str
    ) -> Optional[Dict]:
        """Rule-based UNSPSC classification using regex patterns."""
        text = f"{product_name} {product_description}".lower()

        # Try pattern matching from classification rules
        for rule in self.unspsc_data.get('classification_rules', []):
            pattern = rule['pattern']
            if re.search(pattern, text, re.IGNORECASE):
                code = rule['code']
                if code in self.unspsc_index:
                    result = self.unspsc_index[code].copy()
                    result['confidence'] = rule['confidence']
                    return result

        return None

    def _classify_etim_rules(
        self,
        product_name: str,
        product_description: str,
        product_keywords: List[str] = None
    ) -> Optional[Dict]:
        """Rule-based ETIM classification using keyword matching."""
        text = f"{product_name} {product_description}".lower()
        keywords = [kw.lower() for kw in (product_keywords or [])]

        # Try keyword matching from classification rules
        for rule in self.etim_data.get('classification_rules', []):
            rule_keywords = rule['keywords']
            matches = sum(1 for kw in rule_keywords if kw in text or kw in keywords)

            if matches >= len(rule_keywords) * 0.6:  # 60% keyword match threshold
                code = rule['etim_code']
                if code in self.etim_index:
                    result = self.etim_index[code].copy()
                    result['confidence'] = rule['confidence'] * (matches / len(rule_keywords))
                    return result

        return None

    def _classify_etim_semantic(
        self,
        product_name: str,
        product_description: str,
        language: str
    ) -> Optional[Dict]:
        """Semantic classification using sentence embeddings."""
        # Create query text
        query_text = f"{product_name} {product_description}"

        # Encode query
        query_embedding = self.semantic_model.encode(query_text, convert_to_tensor=True)

        # Find most similar ETIM class
        best_score = 0.0
        best_code = None

        for code, embedding in self.etim_embeddings.items():
            # Skip language-specific embeddings if looking for base code
            if '_' in code:
                continue

            similarity = util.cos_sim(query_embedding, embedding).item()

            if similarity > best_score:
                best_score = similarity
                best_code = code

        # Return if confidence threshold met (0.5 = 50% similarity)
        if best_code and best_score >= 0.5:
            result = self.etim_index[best_code].copy()
            result['confidence'] = best_score
            return result

        return None

    def _infer_unspsc_from_etim(self, etim_result: Dict) -> Optional[Dict]:
        """Infer UNSPSC code from ETIM classification using mapping table."""
        # Simplified mapping (in production, use comprehensive mapping table)
        etim_to_unspsc_map = {
            'EC001489': '27112000',  # Drill/screwdriver -> Drills
            'EC000123': '46181001',  # Safety glasses -> Safety glasses or goggles
        }

        etim_code = etim_result['code']
        if etim_code in etim_to_unspsc_map:
            unspsc_code = etim_to_unspsc_map[etim_code]
            if unspsc_code in self.unspsc_index:
                result = self.unspsc_index[unspsc_code].copy()
                result['confidence'] = etim_result.get('confidence', 0.8) * 0.9  # Slightly lower confidence
                return result

        return None

    def get_etim_features_schema(self, etim_code: str) -> List[Dict]:
        """
        Get ETIM feature schema for a product class.
        Useful for structured product data collection.

        Args:
            etim_code: ETIM classification code

        Returns:
            List of feature definitions with types and units
        """
        if etim_code in self.etim_index:
            return self.etim_index[etim_code].get('features', [])
        return []

    def translate_etim_class(self, etim_code: str, target_language: str) -> str:
        """
        Get translated ETIM class name.

        Args:
            etim_code: ETIM classification code
            target_language: Target language code (zh, ms, ta, etc.)

        Returns:
            Translated class name, or English name if translation not available
        """
        if etim_code in self.etim_index:
            etim_class = self.etim_index[etim_code]
            translations = etim_class.get('translations', {})
            return translations.get(target_language, etim_class['class_name_en'])

        return "Unknown"

    def batch_classify(
        self,
        products: List[Dict[str, str]],
        batch_size: int = 32
    ) -> List[ClassificationResult]:
        """
        Classify multiple products in batches for better performance.

        Args:
            products: List of product dicts with 'name', 'description', 'keywords'
            batch_size: Number of products to classify in parallel

        Returns:
            List of ClassificationResult objects
        """
        results = []

        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]

            for product in batch:
                result = self.classify_product(
                    product_name=product.get('name', ''),
                    product_description=product.get('description', ''),
                    product_keywords=product.get('keywords', [])
                )
                results.append(result)

        return results


# ============================================================================
# INTEGRATION WITH NEO4J KNOWLEDGE GRAPH
# ============================================================================

def update_product_classifications(
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    classifier: ProductClassifier
):
    """
    Classify all products in Neo4j and update their classifications.
    Run this as a batch job to classify entire product catalog.
    """
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    with driver.session() as session:
        # Get all products without classification
        result = session.run("""
            MATCH (p:Product)
            WHERE NOT (p)-[:CATEGORIZED_AS]->(:UNSPSC)
               OR NOT (p)-[:CLASSIFIED_BY]->(:ETIM)
            RETURN p.id AS id, p.name AS name, p.description AS description, p.keywords AS keywords
            LIMIT 1000
        """)

        products_to_classify = []
        for record in result:
            products_to_classify.append({
                'id': record['id'],
                'name': record['name'],
                'description': record['description'] or '',
                'keywords': record['keywords'] or []
            })

        logger.info(f"Classifying {len(products_to_classify)} products...")

        # Classify in batches
        classifications = classifier.batch_classify(products_to_classify)

        # Update Neo4j with classifications
        for product, classification in zip(products_to_classify, classifications):
            if classification.confidence_score >= 0.5:  # Only update if confident
                session.run("""
                    MATCH (p:Product {id: $product_id})

                    // Create or match UNSPSC node
                    MERGE (unspsc:UNSPSC {code: $unspsc_code})
                    ON CREATE SET unspsc.name = $unspsc_name

                    // Create or match ETIM node
                    MERGE (etim:ETIM {code: $etim_code})
                    ON CREATE SET
                      etim.class_name_en = $etim_name,
                      etim.translations = $etim_translations

                    // Create relationships
                    MERGE (p)-[:CATEGORIZED_AS {
                      confidence: $confidence,
                      classification_date: datetime(),
                      method: $method
                    }]->(unspsc)

                    MERGE (p)-[:CLASSIFIED_BY {
                      confidence: $confidence,
                      classification_date: datetime(),
                      method: $method
                    }]->(etim)
                """,
                    product_id=product['id'],
                    unspsc_code=classification.unspsc_code,
                    unspsc_name=classification.unspsc_name,
                    etim_code=classification.etim_code,
                    etim_name=classification.etim_name,
                    etim_translations=classification.etim_translations,
                    confidence=classification.confidence_score,
                    method=classification.classification_method
                )

        logger.info(f"Updated classifications for {len(products_to_classify)} products")

    driver.close()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    import time

    # Initialize classifier
    classifier = ProductClassifier(data_dir="data/classification")

    # Example 1: Classify a single product
    print("\n=== Single Product Classification ===")
    start_time = time.time()

    result = classifier.classify_product(
        product_name="Cordless Power Drill 20V",
        product_description="20V lithium-ion cordless drill with variable speed and LED light",
        product_keywords=["drill", "cordless", "20v", "power tool"]
    )

    elapsed_ms = (time.time() - start_time) * 1000

    print(f"\nProduct: Cordless Power Drill 20V")
    print(f"UNSPSC: {result.unspsc_code} - {result.unspsc_name}")
    print(f"ETIM: {result.etim_code} - {result.etim_name}")
    print(f"Confidence: {result.confidence_score:.2%}")
    print(f"Method: {result.classification_method}")
    print(f"Classification time: {elapsed_ms:.2f}ms {'✓' if elapsed_ms < 500 else '✗ (>500ms)'}")

    # Example 2: Multi-lingual translation
    print("\n=== Multi-lingual Translations ===")
    for lang in ['zh', 'ms', 'ta']:
        translation = classifier.translate_etim_class(result.etim_code, lang)
        print(f"{lang}: {translation}")

    # Example 3: Get ETIM features for structured data
    print("\n=== ETIM Feature Schema ===")
    features = classifier.get_etim_features_schema(result.etim_code)
    for feature in features:
        unit = f" ({feature['unit']})" if 'unit' in feature else ""
        print(f"- {feature['name']}{unit}: {feature['type']}")

    # Example 4: Batch classification performance test
    print("\n=== Batch Classification Performance ===")
    test_products = [
        {"name": "Safety Glasses with Side Shields", "description": "ANSI Z87.1 compliant safety glasses", "keywords": ["safety", "glasses"]},
        {"name": "HSS Drill Bit Set", "description": "High-speed steel drill bits for metal and wood", "keywords": ["drill bits", "hss"]},
        {"name": "Cordless Screwdriver", "description": "12V cordless screwdriver with LED light", "keywords": ["screwdriver", "cordless"]},
    ]

    start_time = time.time()
    batch_results = classifier.batch_classify(test_products)
    elapsed_ms = (time.time() - start_time) * 1000

    print(f"\nClassified {len(test_products)} products in {elapsed_ms:.2f}ms")
    print(f"Average: {elapsed_ms / len(test_products):.2f}ms per product")

    for product, classification in zip(test_products, batch_results):
        print(f"\n{product['name']}:")
        print(f"  UNSPSC: {classification.unspsc_code}")
        print(f"  ETIM: {classification.etim_code} ({classification.confidence_score:.0%})")
```

### Implementation Checklist - Phase 2

- [ ] Create `data/classification/` directory structure
- [ ] Download UNSPSC codes from official source (https://www.unspsc.org/)
- [ ] Download ETIM classification data (https://www.etim-international.com/)
- [ ] Create `data/classification/unspsc_codes.json` with complete hierarchy
- [ ] Create `data/classification/etim_classes.json` with 13+ language support
- [ ] Implement `src/services/classification_service.py`
- [ ] Update `requirements-api.txt` with sentence-transformers
- [ ] Create batch classification script for existing products
- [ ] Integrate with Neo4j knowledge graph service
- [ ] Create API endpoints for product classification
- [ ] Performance testing to ensure <500ms classification time
- [ ] Create admin UI for managing classification rules

**Estimated Time**: 2 weeks
**Dependencies**: Phase 1 (Neo4j must be operational)
**Risk Level**: Medium (external data dependencies, performance critical)

---

## Phase 3: Hybrid AI Recommendation Engine (4 weeks)

### Overview

Implement a sophisticated hybrid recommendation system combining multiple algorithms:
1. **Collaborative Filtering**: "Customers who bought X also bought Y"
2. **Content-Based Filtering**: Product similarity based on specifications
3. **Knowledge Graph**: Neo4j relationship-based recommendations
4. **Context-Aware**: Project type, user skill level, budget constraints
5. **LLM-Powered**: Natural language understanding for RFP processing

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│            Hybrid Recommendation Engine                           │
│                                                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │Collaborative│  │  Content   │  │  Knowledge │  │   LLM     │ │
│  │  Filtering │  │   Based    │  │   Graph    │  │  Context  │ │
│  │            │  │            │  │            │  │  Analysis │ │
│  │ (User-Item)│  │ (TF-IDF +  │  │ (Neo4j     │  │ (OpenAI)  │ │
│  │  Matrix    │  │  Cosine)   │  │  Cypher)   │  │           │ │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬─────┘ │
│        │               │               │               │        │
│        └───────────────┴───────────────┴───────────────┘        │
│                            │                                    │
│                            ▼                                    │
│                  ┌──────────────────┐                           │
│                  │ Score Aggregator │                           │
│                  │ (Weighted Fusion)│                           │
│                  └─────────┬────────┘                           │
│                            │                                    │
│                            ▼                                    │
│                  ┌──────────────────┐                           │
│                  │ Ranking & Filter │                           │
│                  │ (Business Rules) │                           │
│                  └─────────┬────────┘                           │
│                            │                                    │
│                            ▼                                    │
│                     [Recommendations]                           │
└──────────────────────────────────────────────────────────────────┘
```

### Implementation

**File**: `src/services/hybrid_recommendation_engine.py`

```python
"""
Hybrid Recommendation Engine
Combines collaborative filtering, content-based, knowledge graph, and LLM approaches
Following Home Depot and Lowe's industry best practices
"""

from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from dataclasses import dataclass
import logging
from datetime import datetime
import openai
import os

from src.services.knowledge_graph_service import KnowledgeGraphService, ProductRecommendation
from src.services.classification_service import ProductClassifier

logger = logging.getLogger(__name__)


@dataclass
class HybridRecommendation:
    """Enhanced recommendation with multiple scoring factors."""
    product_id: str
    name: str
    description: str
    price: float
    currency: str

    # Scoring breakdown
    collaborative_score: float  # 0-1
    content_score: float        # 0-1
    graph_score: float          # 0-1
    llm_score: float            # 0-1
    final_score: float          # Weighted combination

    # Context
    reasoning: str
    match_type: str  # 'exact', 'compatible', 'alternative', 'complementary'
    confidence: float

    # Additional metadata
    compatible_products: List[str]
    required_safety: List[str]
    user_skill_match: bool
    budget_fit: bool

    # Classification
    unspsc_code: Optional[str] = None
    etim_code: Optional[str] = None


class HybridRecommendationEngine:
    """
    Advanced hybrid recommendation engine combining multiple algorithms.
    Industry best practices from Home Depot, Lowe's, and research.
    """

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        openai_api_key: str,
        classification_data_dir: str = "data/classification"
    ):
        """Initialize hybrid recommendation engine."""

        # Initialize component services
        self.kg_service = KnowledgeGraphService(neo4j_uri, neo4j_user, neo4j_password)
        self.classifier = ProductClassifier(data_dir=classification_data_dir)

        # Initialize OpenAI for LLM-powered recommendations
        openai.api_key = openai_api_key

        # Scoring weights for hybrid fusion (tunable)
        self.weights = {
            'collaborative': 0.25,
            'content': 0.20,
            'graph': 0.35,  # Highest weight - knowledge graph is most reliable
            'llm': 0.20
        }

        logger.info("Hybrid Recommendation Engine initialized")

    def recommend_for_rfp(
        self,
        rfp_text: str,
        customer_context: Optional[Dict] = None,
        user_skill_level: str = 'beginner',
        budget_max: Optional[float] = None,
        max_results: int = 20
    ) -> List[HybridRecommendation]:
        """
        Recommend products for an RFP using hybrid approach.

        This is the main entry point that combines all recommendation strategies.

        Args:
            rfp_text: RFP document text
            customer_context: Optional customer history/preferences
            user_skill_level: User's skill level (beginner/intermediate/advanced/professional)
            budget_max: Maximum budget constraint
            max_results: Maximum number of recommendations

        Returns:
            List of HybridRecommendation objects, ranked by final score
        """
        logger.info(f"Generating hybrid recommendations for RFP (skill: {user_skill_level}, budget: {budget_max})")

        # Step 1: Extract requirements from RFP using LLM
        requirements = self._extract_requirements_with_llm(rfp_text)
        logger.info(f"Extracted {len(requirements)} requirements from RFP")

        # Step 2: Get recommendations from each algorithm
        all_recommendations = {}

        # 2a. Knowledge Graph recommendations (primary)
        for requirement in requirements:
            graph_recs = self.kg_service.recommend_products_for_task(
                task_name=requirement['task'],
                user_skill_level=user_skill_level,
                max_results=max_results
            )

            for rec in graph_recs:
                if rec.product_id not in all_recommendations:
                    all_recommendations[rec.product_id] = {
                        'product': rec,
                        'graph_score': rec.confidence_score,
                        'collaborative_score': 0.0,
                        'content_score': 0.0,
                        'llm_score': 0.0,
                        'requirements_matched': []
                    }

                all_recommendations[rec.product_id]['requirements_matched'].append(requirement)

        # 2b. Content-based recommendations
        for requirement in requirements:
            content_recs = self._content_based_search(
                keywords=requirement['keywords'],
                max_results=max_results
            )

            for product_id, score in content_recs:
                if product_id in all_recommendations:
                    all_recommendations[product_id]['content_score'] = max(
                        all_recommendations[product_id]['content_score'],
                        score
                    )

        # 2c. Collaborative filtering (if customer context available)
        if customer_context and 'purchase_history' in customer_context:
            collab_recs = self._collaborative_filtering(
                customer_context['purchase_history'],
                max_results=max_results
            )

            for product_id, score in collab_recs:
                if product_id in all_recommendations:
                    all_recommendations[product_id]['collaborative_score'] = score

        # 2d. LLM semantic matching
        llm_recs = self._llm_semantic_matching(
            rfp_text=rfp_text,
            requirements=requirements,
            candidate_products=list(all_recommendations.keys())
        )

        for product_id, score in llm_recs.items():
            if product_id in all_recommendations:
                all_recommendations[product_id]['llm_score'] = score

        # Step 3: Fuse scores using weighted combination
        final_recommendations = []

        for product_id, rec_data in all_recommendations.items():
            # Calculate weighted final score
            final_score = (
                self.weights['collaborative'] * rec_data['collaborative_score'] +
                self.weights['content'] * rec_data['content_score'] +
                self.weights['graph'] * rec_data['graph_score'] +
                self.weights['llm'] * rec_data['llm_score']
            )

            # Apply business rules and filters
            product = rec_data['product']

            # Budget filter
            budget_fit = True if budget_max is None else product.price <= budget_max

            # Skill level match (already filtered in graph query, but double-check)
            user_skill_match = self._check_skill_match(product, user_skill_level)

            # Create hybrid recommendation
            hybrid_rec = HybridRecommendation(
                product_id=product.product_id,
                name=product.name,
                description=product.description,
                price=product.price,
                currency=product.currency,
                collaborative_score=rec_data['collaborative_score'],
                content_score=rec_data['content_score'],
                graph_score=rec_data['graph_score'],
                llm_score=rec_data['llm_score'],
                final_score=final_score,
                reasoning=self._generate_reasoning(rec_data),
                match_type=self._determine_match_type(rec_data),
                confidence=final_score,
                compatible_products=product.compatible_products,
                required_safety=product.required_safety,
                user_skill_match=user_skill_match,
                budget_fit=budget_fit,
                unspsc_code=product.unspsc_code,
                etim_code=product.etim_code
            )

            final_recommendations.append(hybrid_rec)

        # Step 4: Rank and filter
        final_recommendations.sort(key=lambda x: x.final_score, reverse=True)

        # Filter out products that don't meet constraints
        filtered_recs = [
            rec for rec in final_recommendations
            if rec.budget_fit and rec.user_skill_match and rec.final_score >= 0.3  # Minimum confidence threshold
        ]

        logger.info(f"Generated {len(filtered_recs)} hybrid recommendations (filtered from {len(final_recommendations)})")

        return filtered_recs[:max_results]

    def _extract_requirements_with_llm(self, rfp_text: str) -> List[Dict[str, Any]]:
        """
        Extract structured requirements from RFP using GPT-4.

        Returns list of requirements with:
        - task: Task description
        - keywords: Extracted keywords
        - quantity: Estimated quantity
        - specifications: Technical specifications
        """
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are an expert at analyzing RFPs for hardware/DIY projects.
Extract structured requirements from the RFP text.

For each requirement, identify:
1. Task description (what needs to be done)
2. Keywords (product types mentioned)
3. Quantity (how many units)
4. Specifications (technical requirements)

Return as JSON array."""},
                    {"role": "user", "content": f"Analyze this RFP and extract requirements:\n\n{rfp_text}"}
                ],
                temperature=0.3,  # Lower temperature for more consistent extraction
                response_format={"type": "json_object"}
            )

            requirements = response.choices[0].message.content
            import json
            return json.loads(requirements).get('requirements', [])

        except Exception as e:
            logger.error(f"LLM requirement extraction failed: {e}")
            # Fallback to simple keyword extraction
            return self._fallback_keyword_extraction(rfp_text)

    def _fallback_keyword_extraction(self, rfp_text: str) -> List[Dict[str, Any]]:
        """Simple keyword extraction fallback if LLM fails."""
        import re

        # Extract quantity patterns
        quantity_patterns = [
            r'(\d+)\s*(?:units?|pcs?|pieces?)\s+(.+)',
            r'(.+):\s*(\d+)',
        ]

        requirements = []
        for pattern in quantity_patterns:
            matches = re.findall(pattern, rfp_text, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    try:
                        qty = int(match[0]) if match[0].isdigit() else int(match[1])
                        item = match[1] if match[0].isdigit() else match[0]

                        requirements.append({
                            'task': f"Purchase {item}",
                            'keywords': item.split()[:5],  # First 5 words as keywords
                            'quantity': qty,
                            'specifications': {}
                        })
                    except:
                        continue

        return requirements

    def _content_based_search(
        self,
        keywords: List[str],
        max_results: int
    ) -> List[Tuple[str, float]]:
        """
        Content-based product search using TF-IDF and cosine similarity.

        Returns:
            List of (product_id, similarity_score) tuples
        """
        # In production, use proper TF-IDF vectorization
        # For now, use Neo4j fulltext search as approximation

        results = self.kg_service.fulltext_search(
            search_query=' '.join(keywords),
            language='en',
            max_results=max_results
        )

        return [(rec.product_id, rec.confidence_score) for rec in results]

    def _collaborative_filtering(
        self,
        purchase_history: List[str],
        max_results: int
    ) -> List[Tuple[str, float]]:
        """
        Collaborative filtering: "Customers who bought X also bought Y"

        Args:
            purchase_history: List of product IDs user has purchased
            max_results: Max recommendations

        Returns:
            List of (product_id, confidence_score) tuples
        """
        # Simplified collaborative filtering using Neo4j graph patterns
        # In production, use matrix factorization (ALS, SVD) or neural collaborative filtering

        recommendations = []

        for purchased_product_id in purchase_history:
            # Find compatible products
            compatible = self.kg_service.find_compatible_products(
                product_id=purchased_product_id
            )

            for rec in compatible:
                recommendations.append((rec.product_id, rec.confidence_score))

        # Aggregate and deduplicate
        aggregated = {}
        for product_id, score in recommendations:
            if product_id not in aggregated:
                aggregated[product_id] = 0.0
            aggregated[product_id] += score

        # Normalize scores
        max_score = max(aggregated.values()) if aggregated else 1.0
        normalized = [(pid, score / max_score) for pid, score in aggregated.items()]

        # Sort and limit
        normalized.sort(key=lambda x: x[1], reverse=True)
        return normalized[:max_results]

    def _llm_semantic_matching(
        self,
        rfp_text: str,
        requirements: List[Dict],
        candidate_products: List[str]
    ) -> Dict[str, float]:
        """
        Use LLM to semantically match products to RFP requirements.
        Provides explainable recommendations.

        Returns:
            Dict mapping product_id to semantic match score (0-1)
        """
        # Get product details from Neo4j
        # (In production, batch this query for efficiency)

        # Simplified: Use GPT to score top candidates
        # In production, use batch processing and caching

        scores = {}

        # For demo purposes, return uniform scores
        # Real implementation would call GPT-4 for semantic matching
        for product_id in candidate_products[:10]:  # Limit to top 10 for cost
            scores[product_id] = 0.7  # Placeholder score

        return scores

    def _check_skill_match(self, product: ProductRecommendation, user_skill_level: str) -> bool:
        """Check if product difficulty matches user skill level."""
        # Simplified skill matching
        skill_hierarchy = {
            'beginner': ['beginner'],
            'intermediate': ['beginner', 'intermediate'],
            'advanced': ['beginner', 'intermediate', 'advanced'],
            'professional': ['beginner', 'intermediate', 'advanced', 'professional']
        }

        # Would need to query Neo4j for product difficulty
        # For now, assume match
        return True

    def _generate_reasoning(self, rec_data: Dict) -> str:
        """Generate human-readable reasoning for recommendation."""
        reasons = []

        if rec_data['graph_score'] > 0.8:
            reasons.append("Strongly matches task requirements based on knowledge graph")
        elif rec_data['graph_score'] > 0.5:
            reasons.append("Matches task requirements")

        if rec_data['content_score'] > 0.7:
            reasons.append("High content similarity to requirements")

        if rec_data['collaborative_score'] > 0.6:
            reasons.append("Frequently purchased together with similar items")

        if rec_data['llm_score'] > 0.7:
            reasons.append("Semantic match to RFP requirements")

        if len(rec_data['requirements_matched']) > 1:
            reasons.append(f"Matches {len(rec_data['requirements_matched'])} requirements")

        return "; ".join(reasons) if reasons else "Recommended based on analysis"

    def _determine_match_type(self, rec_data: Dict) -> str:
        """Determine the type of match (exact, compatible, alternative, complementary)."""
        if rec_data['graph_score'] > 0.9:
            return 'exact'
        elif rec_data['collaborative_score'] > 0.7:
            return 'complementary'
        elif rec_data['content_score'] > 0.7:
            return 'alternative'
        else:
            return 'compatible'

    def close(self):
        """Close all service connections."""
        self.kg_service.close()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    import os

    # Initialize engine
    engine = HybridRecommendationEngine(
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        classification_data_dir="data/classification"
    )

    try:
        # Example RFP
        sample_rfp = """
        Request for Proposal - Office Security Upgrade

        We need the following items:
        - 25 units LED lights for office areas (high efficiency, 5000K color temperature)
        - 8 pieces motion sensors for automatic hallway lighting
        - 4 units IP security cameras with night vision for monitoring
        - 100 meters Cat6 ethernet cable for network infrastructure
        - 2 units 24V power supply systems for access control

        All items must be delivered within 3 weeks.
        Installation will be performed by our in-house team (intermediate skill level).
        Budget: SGD 5,000 maximum.
        """

        # Get hybrid recommendations
        recommendations = engine.recommend_for_rfp(
            rfp_text=sample_rfp,
            user_skill_level='intermediate',
            budget_max=5000.0,
            max_results=15
        )

        # Display results
        print("\n=== HYBRID RECOMMENDATION RESULTS ===\n")

        total_cost = 0.0
        for idx, rec in enumerate(recommendations, 1):
            print(f"{idx}. {rec.name}")
            print(f"   Price: {rec.currency} {rec.price:.2f}")
            print(f"   Final Score: {rec.final_score:.2%}")
            print(f"   Match Type: {rec.match_type}")
            print(f"   Reasoning: {rec.reasoning}")
            print(f"   Score Breakdown:")
            print(f"     - Graph: {rec.graph_score:.2%}")
            print(f"     - Content: {rec.content_score:.2%}")
            print(f"     - Collaborative: {rec.collaborative_score:.2%}")
            print(f"     - LLM: {rec.llm_score:.2%}")

            if rec.compatible_products:
                print(f"   Compatible with: {', '.join(rec.compatible_products[:3])}")

            if rec.required_safety:
                print(f"   Safety required: {', '.join(rec.required_safety)}")

            print()
            total_cost += rec.price

        print(f"Estimated Total Cost: SGD {total_cost:.2f}")
        print(f"Budget: SGD 5,000.00")
        print(f"Budget Status: {'✓ Within Budget' if total_cost <= 5000 else '✗ Over Budget'}")

    finally:
        engine.close()
```

### Implementation Checklist - Phase 3

- [ ] Implement `src/services/hybrid_recommendation_engine.py`
- [ ] Add OpenAI integration for LLM-powered requirements extraction
- [ ] Implement collaborative filtering algorithm
- [ ] Implement content-based filtering with TF-IDF
- [ ] Create scoring fusion logic with tunable weights
- [ ] Add business rules for filtering (budget, skill level, etc.)
- [ ] Create API endpoints for hybrid recommendations
- [ ] Integrate with existing RFP processing endpoint
- [ ] Performance optimization (caching, batch processing)
- [ ] Create A/B testing framework for tuning weights
- [ ] Add recommendation explainability (why this product?)
- [ ] Create admin UI for monitoring recommendation quality

**Estimated Time**: 4 weeks
**Dependencies**: Phase 1 (Neo4j), Phase 2 (Classification)
**Risk Level**: High (complex algorithms, performance critical, OpenAI dependency)

---

**Due to length constraints, I'll continue with Phases 4-6 (Safety, Multi-lingual, Frontend/WebSocket) in the next response. Would you like me to continue?**
