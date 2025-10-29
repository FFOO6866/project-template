"""
Relationship Inference Engine

This module implements AI-powered algorithms to infer product relationships
based on specifications, descriptions, usage patterns, and domain knowledge.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass
import json
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai

from .database import Neo4jConnection, GraphDatabase
from .models import (
    SemanticRelationship, RelationshipType, ConfidenceSource,
    BRAND_ECOSYSTEM_COMPATIBILITY, PROJECT_TOOL_REQUIREMENTS
)

logger = logging.getLogger(__name__)


@dataclass
class InferenceRule:
    """Rule for inferring product relationships"""
    name: str
    relationship_type: RelationshipType
    confidence_base: float
    conditions: Dict[str, Any]
    weight: float = 1.0
    requires_ai: bool = False


class RelationshipInferenceEngine:
    """
    AI-powered engine for inferring product relationships.
    
    Uses multiple algorithms and data sources to identify and score
    relationships between products with confidence ratings.
    """
    
    def __init__(
        self,
        neo4j_connection: Neo4jConnection,
        openai_api_key: str = None,
        enable_ai_inference: bool = True
    ):
        """
        Initialize the inference engine.
        
        Args:
            neo4j_connection: Neo4j database connection
            openai_api_key: OpenAI API key for AI-powered inference
            enable_ai_inference: Whether to use AI models for inference
        """
        self.graph_db = GraphDatabase(neo4j_connection)
        self.neo4j_conn = neo4j_connection
        self.enable_ai = enable_ai_inference
        
        if openai_api_key:
            openai.api_key = openai_api_key
        
        # Initialize inference rules
        self.rules = self._initialize_inference_rules()
        
        # Text vectorizer for semantic similarity
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2
        )
        
        # Caches for expensive operations
        self._product_cache = {}
        self._embedding_cache = {}
        
    def _initialize_inference_rules(self) -> List[InferenceRule]:
        """Initialize predefined inference rules"""
        rules = [
            # Brand ecosystem compatibility
            InferenceRule(
                name="brand_battery_compatibility",
                relationship_type=RelationshipType.COMPATIBLE_WITH,
                confidence_base=0.85,
                conditions={
                    "same_brand": True,
                    "contains_voltage": True,
                    "category_contains": ["battery", "tool", "charger"]
                }
            ),
            
            # Voltage compatibility
            InferenceRule(
                name="voltage_compatibility", 
                relationship_type=RelationshipType.COMPATIBLE_WITH,
                confidence_base=0.75,
                conditions={
                    "same_voltage": True,
                    "different_categories": True
                }
            ),
            
            # Size compatibility for accessories
            InferenceRule(
                name="size_compatibility",
                relationship_type=RelationshipType.ACCESSORY_FOR,
                confidence_base=0.70,
                conditions={
                    "size_match": True,
                    "category_relationship": ["tool", "accessory"]
                }
            ),
            
            # Project requirements
            InferenceRule(
                name="project_tool_requirements",
                relationship_type=RelationshipType.NEEDED_FOR_PROJECT,
                confidence_base=0.80,
                conditions={
                    "project_keyword_match": True,
                    "tool_category": True
                }
            ),
            
            # Alternative products (same function, different brands)
            InferenceRule(
                name="alternative_products",
                relationship_type=RelationshipType.ALTERNATIVE_TO,
                confidence_base=0.65,
                conditions={
                    "similar_function": True,
                    "different_brands": True,
                    "similar_price_range": True
                }
            ),
            
            # Upgrade relationships
            InferenceRule(
                name="product_upgrades",
                relationship_type=RelationshipType.UPGRADED_BY,
                confidence_base=0.70,
                conditions={
                    "same_brand": True,
                    "similar_category": True,
                    "higher_specs": True
                }
            ),
            
            # Kit relationships
            InferenceRule(
                name="kit_components",
                relationship_type=RelationshipType.PART_OF_KIT,
                confidence_base=0.90,
                conditions={
                    "kit_in_name": True,
                    "components_listed": True
                }
            ),
            
            # AI-powered semantic relationships
            InferenceRule(
                name="ai_semantic_relationships",
                relationship_type=RelationshipType.COMPATIBLE_WITH,
                confidence_base=0.60,
                conditions={
                    "semantic_similarity": 0.7
                },
                requires_ai=True
            )
        ]
        
        return rules
    
    # ===========================================
    # MAIN INFERENCE METHODS
    # ===========================================
    
    async def infer_all_relationships(
        self,
        batch_size: int = 500,
        max_products: int = None,
        min_confidence: float = 0.5
    ) -> Dict[str, int]:
        """
        Run comprehensive relationship inference on all products.
        
        Args:
            batch_size: Number of products to process in each batch
            max_products: Maximum number of products to process (for testing)
            min_confidence: Minimum confidence threshold for relationships
            
        Returns:
            Dictionary with counts of relationships created by type
        """
        logger.info("Starting comprehensive relationship inference...")
        
        # Get all products from Neo4j
        products = await self._get_all_products(max_products)
        if not products:
            logger.warning("No products found for inference")
            return {}
        
        logger.info(f"Running inference on {len(products)} products")
        
        results = defaultdict(int)
        
        # Process in batches to manage memory
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: products {i+1}-{min(i+batch_size, len(products))}")
            
            batch_results = await self._infer_batch_relationships(batch, min_confidence)
            
            # Accumulate results
            for rel_type, count in batch_results.items():
                results[rel_type] += count
        
        logger.info(f"Relationship inference completed: {dict(results)}")
        return dict(results)
    
    async def infer_product_relationships(
        self,
        product_id: int,
        target_products: List[int] = None,
        relationship_types: List[RelationshipType] = None
    ) -> List[SemanticRelationship]:
        """
        Infer relationships for a specific product.
        
        Args:
            product_id: Product to infer relationships for
            target_products: Specific products to check relationships with
            relationship_types: Types of relationships to infer
            
        Returns:
            List of inferred relationships
        """
        # Get product data
        product = self.graph_db.get_product_node(product_id=product_id)
        if not product:
            logger.error(f"Product {product_id} not found")
            return []
        
        # Get target products
        if target_products:
            targets = []
            for target_id in target_products:
                target = self.graph_db.get_product_node(product_id=target_id)
                if target:
                    targets.append(target)
        else:
            # Get all products in same category and related categories
            targets = await self._get_related_products(product)
        
        # Apply inference rules
        relationships = []
        rules_to_apply = relationship_types or [rule.relationship_type for rule in self.rules]
        
        for target in targets:
            if target.product_id == product.product_id:
                continue
                
            for rule in self.rules:
                if rule.relationship_type not in rules_to_apply:
                    continue
                    
                relationship = await self._apply_rule(product, target, rule)
                if relationship:
                    relationships.append(relationship)
        
        return relationships
    
    # ===========================================
    # RULE APPLICATION METHODS
    # ===========================================
    
    async def _apply_rule(
        self,
        product1: Any,
        product2: Any,
        rule: InferenceRule
    ) -> Optional[SemanticRelationship]:
        """
        Apply a specific inference rule to two products.
        
        Args:
            product1: Source product
            product2: Target product
            rule: Inference rule to apply
            
        Returns:
            SemanticRelationship if rule matches, None otherwise
        """
        try:
            # Check if rule conditions are met
            confidence = await self._evaluate_rule_conditions(product1, product2, rule)
            
            if confidence is None or confidence < 0.5:
                return None
            
            # Create relationship
            relationship = SemanticRelationship(
                from_product_id=product1.product_id,
                to_product_id=product2.product_id,
                relationship_type=rule.relationship_type,
                confidence=min(confidence, 1.0),
                source=ConfidenceSource.AI_INFERENCE,
                created_by=f"inference_rule_{rule.name}",
                notes=f"Inferred by rule: {rule.name}"
            )
            
            # Add rule-specific metadata
            relationship.compatibility_type = self._determine_compatibility_type(product1, product2, rule)
            relationship.evidence = self._collect_evidence(product1, product2, rule)
            
            return relationship
            
        except Exception as e:
            logger.error(f"Error applying rule {rule.name}: {e}")
            return None
    
    async def _evaluate_rule_conditions(
        self,
        product1: Any,
        product2: Any,
        rule: InferenceRule
    ) -> Optional[float]:
        """
        Evaluate whether rule conditions are met and return confidence score.
        
        Args:
            product1: Source product
            product2: Target product
            rule: Rule to evaluate
            
        Returns:
            Confidence score (0.0-1.0) or None if conditions not met
        """
        conditions = rule.conditions
        confidence_factors = []
        base_confidence = rule.confidence_base
        
        # Brand compatibility checks
        if conditions.get("same_brand"):
            if product1.brand_name and product2.brand_name:
                if product1.brand_name.lower() == product2.brand_name.lower():
                    confidence_factors.append(0.9)
                else:
                    return None
        
        if conditions.get("different_brands"):
            if product1.brand_name and product2.brand_name:
                if product1.brand_name.lower() != product2.brand_name.lower():
                    confidence_factors.append(0.8)
                else:
                    return None
        
        # Voltage compatibility
        if conditions.get("same_voltage"):
            voltage1 = self._extract_voltage(product1)
            voltage2 = self._extract_voltage(product2)
            
            if voltage1 and voltage2:
                if voltage1 == voltage2:
                    confidence_factors.append(0.85)
                else:
                    return None
        
        if conditions.get("contains_voltage"):
            voltage1 = self._extract_voltage(product1)
            voltage2 = self._extract_voltage(product2)
            
            if voltage1 or voltage2:
                confidence_factors.append(0.7)
        
        # Category relationships
        if conditions.get("same_category"):
            if product1.category_name and product2.category_name:
                if product1.category_name.lower() == product2.category_name.lower():
                    confidence_factors.append(0.8)
                else:
                    return None
        
        if conditions.get("different_categories"):
            if product1.category_name and product2.category_name:
                if product1.category_name.lower() != product2.category_name.lower():
                    confidence_factors.append(0.7)
        
        # Category content checks
        if conditions.get("category_contains"):
            required_terms = conditions["category_contains"]
            category_text = f"{product1.category_name} {product2.category_name}".lower()
            
            matches = sum(1 for term in required_terms if term in category_text)
            if matches > 0:
                confidence_factors.append(matches / len(required_terms))
            else:
                return None
        
        # Size compatibility
        if conditions.get("size_match"):
            size_compatibility = self._check_size_compatibility(product1, product2)
            if size_compatibility > 0:
                confidence_factors.append(size_compatibility)
            else:
                return None
        
        # Price similarity for alternatives
        if conditions.get("similar_price_range"):
            price_similarity = self._calculate_price_similarity(product1, product2)
            if price_similarity > 0.5:
                confidence_factors.append(price_similarity)
            else:
                return None
        
        # Function similarity
        if conditions.get("similar_function"):
            function_similarity = await self._calculate_function_similarity(product1, product2)
            if function_similarity > 0.6:
                confidence_factors.append(function_similarity)
            else:
                return None
        
        # Specification comparisons
        if conditions.get("higher_specs"):
            spec_comparison = self._compare_specifications(product1, product2)
            if spec_comparison > 0:
                confidence_factors.append(spec_comparison)
            else:
                return None
        
        # Kit detection
        if conditions.get("kit_in_name"):
            kit_detected = self._detect_kit_relationship(product1, product2)
            if kit_detected:
                confidence_factors.append(0.9)
            else:
                return None
        
        # Project keyword matching
        if conditions.get("project_keyword_match"):
            project_match = self._check_project_keywords(product1, product2)
            if project_match > 0:
                confidence_factors.append(project_match)
            else:
                return None
        
        # AI-powered semantic similarity
        if conditions.get("semantic_similarity") and self.enable_ai:
            threshold = conditions["semantic_similarity"]
            similarity = await self._calculate_semantic_similarity(product1, product2)
            
            if similarity >= threshold:
                confidence_factors.append(similarity)
            else:
                return None
        
        # Calculate final confidence
        if not confidence_factors:
            return None
        
        # Weight the confidence factors
        weighted_confidence = base_confidence * np.mean(confidence_factors) * rule.weight
        
        return min(weighted_confidence, 1.0)
    
    # ===========================================
    # UTILITY METHODS FOR RULE EVALUATION
    # ===========================================
    
    def _extract_voltage(self, product: Any) -> Optional[str]:
        """Extract voltage specification from product"""
        text_to_search = f"{product.name} {product.description or ''}"
        
        # Common voltage patterns
        voltage_patterns = [
            r'(\d+(?:\.\d+)?)\s*V(?:olt)?s?',
            r'(\d+(?:\.\d+)?)\s*volt',
            r'(\d+(?:\.\d+)?)\s*-?\s*volt'
        ]
        
        for pattern in voltage_patterns:
            match = re.search(pattern, text_to_search, re.IGNORECASE)
            if match:
                return f"{match.group(1)}V"
        
        # Check specifications
        if product.specifications:
            for key, value in product.specifications.items():
                if 'voltage' in key.lower() or 'volt' in key.lower():
                    if isinstance(value, str):
                        voltage_match = re.search(r'(\d+(?:\.\d+)?)', value)
                        if voltage_match:
                            return f"{voltage_match.group(1)}V"
        
        return None
    
    def _check_size_compatibility(self, product1: Any, product2: Any) -> float:
        """Check if products have compatible sizes"""
        # Simple size compatibility check
        if not (product1.dimensions and product2.dimensions):
            return 0.0
        
        try:
            # Calculate size similarity based on dimensions
            dim1 = product1.dimensions
            dim2 = product2.dimensions
            
            similarities = []
            for dim in ['length', 'width', 'height']:
                if dim1.get(dim) and dim2.get(dim):
                    ratio = min(dim1[dim], dim2[dim]) / max(dim1[dim], dim2[dim])
                    similarities.append(ratio)
            
            if similarities:
                return np.mean(similarities)
                
        except Exception:
            pass
        
        return 0.0
    
    def _calculate_price_similarity(self, product1: Any, product2: Any) -> float:
        """Calculate price similarity between products"""
        if not (product1.price and product2.price):
            return 0.0
        
        try:
            price_ratio = min(product1.price, product2.price) / max(product1.price, product2.price)
            return price_ratio
        except:
            return 0.0
    
    async def _calculate_function_similarity(self, product1: Any, product2: Any) -> float:
        """Calculate functional similarity between products"""
        # Combine text features for similarity calculation
        text1 = f"{product1.name} {product1.description or ''} {' '.join(product1.keywords or [])}"
        text2 = f"{product2.name} {product2.description or ''} {' '.join(product2.keywords or [])}"
        
        try:
            # Use TF-IDF vectorization for text similarity
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
            
        except Exception as e:
            logger.warning(f"Function similarity calculation failed: {e}")
            return 0.0
    
    def _compare_specifications(self, product1: Any, product2: Any) -> float:
        """Compare specifications to determine if product2 is an upgrade"""
        if not (product1.specifications and product2.specifications):
            return 0.0
        
        upgrade_score = 0.0
        comparisons = 0
        
        # Define numeric specification comparisons
        numeric_specs = ['power', 'torque', 'speed', 'capacity', 'runtime', 'weight']
        
        for spec in numeric_specs:
            val1 = self._extract_numeric_spec(product1.specifications, spec)
            val2 = self._extract_numeric_spec(product2.specifications, spec)
            
            if val1 and val2:
                # For weight, lower is better; for others, higher is better
                if spec == 'weight':
                    if val2 < val1:
                        upgrade_score += 1
                else:
                    if val2 > val1:
                        upgrade_score += 1
                comparisons += 1
        
        return upgrade_score / comparisons if comparisons > 0 else 0.0
    
    def _extract_numeric_spec(self, specifications: Dict, spec_name: str) -> Optional[float]:
        """Extract numeric value from specification"""
        for key, value in specifications.items():
            if spec_name in key.lower():
                if isinstance(value, (int, float)):
                    return float(value)
                elif isinstance(value, str):
                    # Extract first number from string
                    match = re.search(r'(\d+(?:\.\d+)?)', value)
                    if match:
                        return float(match.group(1))
        return None
    
    def _detect_kit_relationship(self, product1: Any, product2: Any) -> bool:
        """Detect if products are part of a kit"""
        kit_keywords = ['kit', 'combo', 'set', 'bundle', 'pack']
        
        name1 = product1.name.lower()
        name2 = product2.name.lower()
        
        # Check if either product name contains kit indicators
        for keyword in kit_keywords:
            if keyword in name1 or keyword in name2:
                return True
        
        return False
    
    def _check_project_keywords(self, product1: Any, product2: Any) -> float:
        """Check if products match project requirements"""
        project_keywords = {
            'bathroom': ['drill', 'saw', 'tile', 'grout', 'plumbing'],
            'kitchen': ['drill', 'saw', 'router', 'cabinet', 'countertop'],
            'deck': ['saw', 'drill', 'level', 'framing', 'outdoor'],
            'electrical': ['wire', 'electrical', 'circuit', 'voltage', 'amp']
        }
        
        product_text = f"{product1.name} {product2.name} {product1.description or ''} {product2.description or ''}".lower()
        
        max_score = 0.0
        for project, keywords in project_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in product_text)
            score = matches / len(keywords)
            max_score = max(max_score, score)
        
        return max_score
    
    async def _calculate_semantic_similarity(self, product1: Any, product2: Any) -> float:
        """Calculate semantic similarity using AI embeddings"""
        if not self.enable_ai:
            return 0.0
        
        try:
            # Create text representations
            text1 = f"{product1.name}. {product1.description or ''}"
            text2 = f"{product2.name}. {product2.description or ''}"
            
            # Get embeddings from OpenAI
            embedding1 = await self._get_embedding(text1)
            embedding2 = await self._get_embedding(text2)
            
            if embedding1 and embedding2:
                # Calculate cosine similarity
                similarity = np.dot(embedding1, embedding2) / (
                    np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
                )
                return float(similarity)
                
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {e}")
        
        return 0.0
    
    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get text embedding from OpenAI API with caching"""
        if text in self._embedding_cache:
            return self._embedding_cache[text]
        
        try:
            response = await openai.Embedding.acreate(
                model="text-embedding-ada-002",
                input=text
            )
            
            embedding = response['data'][0]['embedding']
            self._embedding_cache[text] = embedding
            return embedding
            
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return None
    
    # ===========================================
    # BATCH PROCESSING METHODS
    # ===========================================
    
    async def _infer_batch_relationships(
        self,
        products: List[Any],
        min_confidence: float
    ) -> Dict[str, int]:
        """Process a batch of products for relationship inference"""
        results = defaultdict(int)
        
        # Create relationships between all product pairs in batch
        for i, product1 in enumerate(products):
            for j, product2 in enumerate(products[i+1:], i+1):
                
                # Apply all inference rules
                for rule in self.rules:
                    relationship = await self._apply_rule(product1, product2, rule)
                    
                    if relationship and relationship.confidence >= min_confidence:
                        # Create relationship in Neo4j
                        success = self.graph_db.create_relationship(relationship)
                        
                        if success:
                            results[relationship.relationship_type.value] += 1
        
        return results
    
    async def _get_all_products(self, max_products: int = None) -> List[Any]:
        """Get all products for inference"""
        query = """
        MATCH (p:Product)
        WHERE p.is_published = true
        RETURN p
        """
        
        if max_products:
            query += f" LIMIT {max_products}"
        
        try:
            with self.neo4j_conn.session() as session:
                results = session.run(query)
                products = []
                
                for record in results:
                    product_data = dict(record["p"])
                    products.append(product_data)
                
                return products
                
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            return []
    
    async def _get_related_products(self, product: Any) -> List[Any]:
        """Get products related to the given product for targeted inference"""
        query = """
        MATCH (p:Product)
        WHERE p.is_published = true
        AND (p.category_name = $category_name 
             OR p.brand_name = $brand_name
             OR p.product_id IN (
                 SELECT DISTINCT related.product_id
                 FROM (p2:Product)-[:BELONGS_TO_CATEGORY]->(c:Category)<-[:BELONGS_TO_CATEGORY]-(related)
                 WHERE p2.product_id = $product_id
             ))
        AND p.product_id != $product_id
        RETURN p
        LIMIT 100
        """
        
        try:
            with self.neo4j_conn.session() as session:
                results = session.run(query, {
                    "product_id": product.product_id,
                    "category_name": product.category_name,
                    "brand_name": product.brand_name
                })
                
                products = []
                for record in results:
                    product_data = dict(record["p"])
                    products.append(product_data)
                
                return products
                
        except Exception as e:
            logger.error(f"Failed to get related products: {e}")
            return []
    
    # ===========================================
    # HELPER METHODS
    # ===========================================
    
    def _determine_compatibility_type(self, product1: Any, product2: Any, rule: InferenceRule) -> Optional[str]:
        """Determine the specific type of compatibility"""
        if rule.name == "brand_battery_compatibility":
            return "battery_system"
        elif rule.name == "voltage_compatibility":
            return "voltage_compatibility"
        elif rule.name == "size_compatibility":
            return "size_compatibility"
        elif "ecosystem" in rule.name:
            return "brand_ecosystem"
        else:
            return "general_compatibility"
    
    def _collect_evidence(self, product1: Any, product2: Any, rule: InferenceRule) -> List[str]:
        """Collect evidence supporting the inferred relationship"""
        evidence = []
        
        if product1.brand_name == product2.brand_name:
            evidence.append(f"Same brand: {product1.brand_name}")
        
        voltage1 = self._extract_voltage(product1)
        voltage2 = self._extract_voltage(product2)
        if voltage1 and voltage2 and voltage1 == voltage2:
            evidence.append(f"Same voltage: {voltage1}")
        
        if product1.category_name == product2.category_name:
            evidence.append(f"Same category: {product1.category_name}")
        
        return evidence


# Export main class
__all__ = ["RelationshipInferenceEngine", "InferenceRule"]