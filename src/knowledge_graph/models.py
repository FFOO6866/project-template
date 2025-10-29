"""
Product Knowledge Graph Data Models

This module defines the data models for the Neo4j knowledge graph, including:
- Product nodes and relationships
- Relationship types and confidence scoring
- Semantic relationship structures
- Integration with PostgreSQL data models
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator
import uuid


class RelationshipType(str, Enum):
    """
    Enumeration of product relationship types in the knowledge graph.
    
    Each relationship type has specific semantic meaning and confidence scoring rules.
    """
    # Core compatibility relationships
    COMPATIBLE_WITH = "COMPATIBLE_WITH"           # Products that work together (batteries, tools)
    REQUIRES = "REQUIRES"                         # Hard dependency (tool requires battery)
    ALTERNATIVE_TO = "ALTERNATIVE_TO"             # Products that can substitute each other
    USED_FOR = "USED_FOR"                        # Product usage contexts and projects
    
    # Brand and ecosystem relationships  
    SAME_BRAND_ECOSYSTEM = "SAME_BRAND_ECOSYSTEM" # Products in same brand system (Makita 18V)
    CROSS_BRAND_COMPATIBLE = "CROSS_BRAND_COMPATIBLE" # Cross-brand compatibility (adapters)
    
    # Project and usage relationships
    NEEDED_FOR_PROJECT = "NEEDED_FOR_PROJECT"     # Project requires this product
    OFTEN_BOUGHT_WITH = "OFTEN_BOUGHT_WITH"       # Purchase pattern relationships
    RECOMMENDED_WITH = "RECOMMENDED_WITH"         # Expert recommendations
    
    # Technical relationships
    UPGRADED_BY = "UPGRADED_BY"                   # Product A is upgraded version of B
    ACCESSORY_FOR = "ACCESSORY_FOR"              # Accessories and add-ons  
    PART_OF_KIT = "PART_OF_KIT"                  # Products sold as kits
    
    # Category and classification
    SIMILAR_FUNCTION = "SIMILAR_FUNCTION"         # Products with similar functions
    SIMILAR_SPECS = "SIMILAR_SPECS"              # Similar technical specifications


class ConfidenceSource(str, Enum):
    """Source of relationship confidence scoring"""
    MANUFACTURER_SPEC = "manufacturer_spec"       # Official manufacturer documentation
    AI_INFERENCE = "ai_inference"                # AI-generated relationship
    USER_BEHAVIOR = "user_behavior"              # Purchase/usage patterns
    EXPERT_KNOWLEDGE = "expert_knowledge"        # Domain expert input
    WEB_SCRAPING = "web_scraping"               # Scraped from web sources
    COMMUNITY_INPUT = "community_input"          # User-generated content


@dataclass
class ProductNode:
    """
    Product node representation for Neo4j knowledge graph.
    
    Maps to PostgreSQL Product model but optimized for graph operations.
    """
    # Core identifiers (required)
    product_id: int
    sku: str
    name: str
    slug: str
    
    # Categorization
    brand_name: Optional[str] = None
    brand_id: Optional[int] = None
    category_name: Optional[str] = None
    category_id: Optional[int] = None
    
    # Basic attributes for relationship inference
    price: Optional[float] = None
    currency: str = "USD"
    availability: str = "unknown"
    is_published: bool = True
    
    # Rich content for semantic analysis
    description: Optional[str] = None
    long_description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    features: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # Physical attributes for compatibility analysis
    dimensions: Optional[Dict[str, float]] = None  # length, width, height
    weight: Optional[float] = None
    material: Optional[str] = None
    color: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_sync_from_postgres: Optional[datetime] = None
    
    # Vector embeddings (stored as binary in Neo4j)
    embedding_vector: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    embedding_updated_at: Optional[datetime] = None
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        """Convert to Neo4j node properties dictionary"""
        props = {
            "product_id": self.product_id,
            "sku": self.sku,
            "name": self.name,
            "slug": self.slug,
            "price": self.price,
            "currency": self.currency,
            "availability": self.availability,
            "is_published": self.is_published,
            "created_at": self.created_at,
            "updated_at": self.updated_at or datetime.utcnow(),
            "last_sync_from_postgres": self.last_sync_from_postgres
        }
        
        # Add optional fields if present
        if self.brand_name:
            props["brand_name"] = self.brand_name
            props["brand_id"] = self.brand_id
        if self.category_name:
            props["category_name"] = self.category_name
            props["category_id"] = self.category_id
        if self.description:
            props["description"] = self.description
        if self.long_description:
            props["long_description"] = self.long_description
        if self.specifications:
            props["specifications"] = self.specifications
        if self.features:
            props["features"] = self.features
        if self.keywords:
            props["keywords"] = self.keywords
        if self.dimensions:
            props["dimensions"] = self.dimensions
        if self.weight:
            props["weight"] = self.weight
        if self.material:
            props["material"] = self.material
        if self.color:
            props["color"] = self.color
            
        return props


@dataclass 
class SemanticRelationship:
    """
    Relationship between products in the knowledge graph.
    
    Includes confidence scoring, source tracking, and semantic metadata.
    """
    # Core relationship data
    from_product_id: int
    to_product_id: int
    relationship_type: RelationshipType
    
    # Confidence and quality metrics
    confidence: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0 confidence score
    source: ConfidenceSource = ConfidenceSource.AI_INFERENCE
    
    # Relationship metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"  # system, user_id, or algorithm name
    
    # Semantic details
    compatibility_type: Optional[str] = None      # battery_system, voltage, etc.
    use_case: Optional[str] = None               # drilling, cutting, etc.
    context: Optional[str] = None                # project_type, skill_level, etc.
    notes: Optional[str] = None                  # Human-readable explanation
    
    # Supporting evidence
    evidence: List[str] = field(default_factory=list)  # URLs, specs, etc.
    tags: List[str] = field(default_factory=list)      # Additional tags
    
    # Quality metrics
    validation_count: int = 0                    # How many times validated
    rejection_count: int = 0                     # How many times rejected
    user_feedback_score: Optional[float] = None  # User feedback rating
    
    # Expiry and maintenance
    expires_at: Optional[datetime] = None        # When relationship should be re-evaluated
    needs_review: bool = False                   # Flag for manual review
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        """Convert to Neo4j relationship properties dictionary"""
        return {
            "relationship_type": self.relationship_type.value,
            "confidence": self.confidence,
            "source": self.source.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "compatibility_type": self.compatibility_type,
            "use_case": self.use_case,
            "context": self.context,
            "notes": self.notes,
            "evidence": self.evidence,
            "tags": self.tags,
            "validation_count": self.validation_count,
            "rejection_count": self.rejection_count,
            "user_feedback_score": self.user_feedback_score,
            "expires_at": self.expires_at,
            "needs_review": self.needs_review
        }
    
    def quality_score(self) -> float:
        """Calculate overall quality score for this relationship"""
        base_score = self.confidence
        
        # Boost score based on source reliability
        source_multipliers = {
            ConfidenceSource.MANUFACTURER_SPEC: 1.0,
            ConfidenceSource.EXPERT_KNOWLEDGE: 0.95,
            ConfidenceSource.USER_BEHAVIOR: 0.85,
            ConfidenceSource.WEB_SCRAPING: 0.75,
            ConfidenceSource.AI_INFERENCE: 0.70,
            ConfidenceSource.COMMUNITY_INPUT: 0.65
        }
        
        source_score = base_score * source_multipliers.get(self.source, 0.5)
        
        # Adjust based on validation feedback
        if self.validation_count > 0:
            validation_ratio = self.validation_count / (self.validation_count + self.rejection_count)
            source_score *= (0.5 + 0.5 * validation_ratio)  # Scale between 0.5 and 1.0
        
        # Incorporate user feedback
        if self.user_feedback_score is not None:
            source_score = (source_score + self.user_feedback_score) / 2
            
        return min(1.0, source_score)


@dataclass
class CategoryNode:
    """Category node for product classification and hierarchy"""
    category_id: int
    name: str
    slug: str
    level: int = 0
    path: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True
    description: Optional[str] = None
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        return {
            "category_id": self.category_id,
            "name": self.name,
            "slug": self.slug,
            "level": self.level,
            "path": self.path,
            "parent_id": self.parent_id,
            "is_active": self.is_active,
            "description": self.description
        }


@dataclass
class BrandNode:
    """Brand node for manufacturer relationships and ecosystem analysis"""
    brand_id: int
    name: str
    slug: str
    country: Optional[str] = None
    parent_brand_id: Optional[int] = None
    is_active: bool = True
    website_url: Optional[str] = None
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        return {
            "brand_id": self.brand_id,
            "name": self.name,
            "slug": self.slug,
            "country": self.country,
            "parent_brand_id": self.parent_brand_id,
            "is_active": self.is_active,
            "website_url": self.website_url
        }


@dataclass
class ProjectNode:
    """DIY project node for use-case based recommendations"""
    project_id: int = field(default_factory=lambda: int(uuid.uuid4().int))
    name: str
    slug: str
    description: Optional[str] = None
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    estimated_duration: Optional[str] = None
    budget_range: str = "low"  # low, medium, high
    category: Optional[str] = None  # bathroom, kitchen, outdoor, etc.
    keywords: List[str] = field(default_factory=list)
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "difficulty_level": self.difficulty_level,
            "estimated_duration": self.estimated_duration,
            "budget_range": self.budget_range,
            "category": self.category,
            "keywords": self.keywords
        }


# Pydantic models for API validation
class ProductNodeCreate(BaseModel):
    """Pydantic model for creating product nodes via API"""
    product_id: int
    sku: str
    name: str
    slug: str
    brand_name: Optional[str] = None
    brand_id: Optional[int] = None
    category_name: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    features: List[str] = []
    keywords: List[str] = []


class RelationshipCreate(BaseModel):
    """Pydantic model for creating relationships via API"""
    from_product_id: int
    to_product_id: int
    relationship_type: RelationshipType
    confidence: float = Field(ge=0.0, le=1.0)
    source: ConfidenceSource = ConfidenceSource.AI_INFERENCE
    compatibility_type: Optional[str] = None
    use_case: Optional[str] = None
    notes: Optional[str] = None
    evidence: List[str] = []
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class RelationshipQuery(BaseModel):
    """Pydantic model for querying relationships"""
    product_id: Optional[int] = None
    relationship_types: Optional[List[RelationshipType]] = None
    min_confidence: float = 0.0
    max_distance: int = 2  # Maximum graph traversal distance
    limit: int = 100


class SemanticSearchQuery(BaseModel):
    """Pydantic model for semantic search queries"""
    query: str
    limit: int = 20
    min_similarity: float = 0.7
    filters: Optional[Dict[str, Any]] = None
    include_relationships: bool = True


# Relationship compatibility matrices for inference
BRAND_ECOSYSTEM_COMPATIBILITY = {
    "Makita": {
        "battery_systems": ["18V LXT", "12V CXT", "40V XGT"],
        "compatible_brands": [],  # Makita is typically proprietary
        "tool_categories": ["power_tools", "outdoor_tools", "accessories"]
    },
    "DeWalt": {
        "battery_systems": ["20V MAX", "12V MAX", "60V FLEXVOLT"],
        "compatible_brands": ["Porter-Cable"],  # Some cross-compatibility
        "tool_categories": ["power_tools", "hand_tools", "accessories"]
    },
    "Milwaukee": {
        "battery_systems": ["M18", "M12", "MX FUEL"],
        "compatible_brands": [],
        "tool_categories": ["power_tools", "lighting", "storage"]
    },
    "Ryobi": {
        "battery_systems": ["18V ONE+", "40V"],
        "compatible_brands": ["Ridgid"],  # Both owned by TTI
        "tool_categories": ["power_tools", "outdoor_tools", "accessories"]
    }
}

PROJECT_TOOL_REQUIREMENTS = {
    "bathroom_renovation": {
        "required_tools": ["drill", "saw", "level", "measuring_tape"],
        "nice_to_have": ["oscillating_tool", "wet_saw", "grout_removal_tool"],
        "skill_level": "intermediate",
        "safety_equipment": ["safety_glasses", "dust_mask", "gloves"]
    },
    "kitchen_renovation": {
        "required_tools": ["drill", "circular_saw", "jigsaw", "router"],
        "nice_to_have": ["table_saw", "miter_saw", "pocket_hole_jig"],
        "skill_level": "advanced",
        "safety_equipment": ["safety_glasses", "hearing_protection", "dust_mask"]
    },
    "deck_building": {
        "required_tools": ["circular_saw", "drill", "impact_driver", "level"],
        "nice_to_have": ["miter_saw", "framing_nailer", "chalk_line"],
        "skill_level": "intermediate",
        "safety_equipment": ["safety_glasses", "work_gloves", "knee_pads"]
    }
}

# Export all models and types
__all__ = [
    "RelationshipType",
    "ConfidenceSource", 
    "ProductNode",
    "SemanticRelationship",
    "CategoryNode",
    "BrandNode",
    "ProjectNode",
    "ProductNodeCreate",
    "RelationshipCreate",
    "RelationshipQuery",
    "SemanticSearchQuery",
    "BRAND_ECOSYSTEM_COMPATIBILITY",
    "PROJECT_TOOL_REQUIREMENTS"
]