"""
Core Business Logic - No SDK Dependencies
Implements product search, RFP analysis, and work-based recommendations
Optimized for Windows compatibility and real-world business scenarios
"""
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import math

from .database import get_database, ProductDatabase

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Product search result with relevance score"""
    product: Dict
    relevance_score: float
    match_reasons: List[str]

@dataclass
class RFPAnalysis:
    """RFP document analysis result"""
    document_id: str
    work_type: str
    required_products: List[str]
    recommended_products: List[SearchResult]
    confidence_score: float
    analysis_summary: str
    created_at: datetime

@dataclass
class WorkRecommendation:
    """Work-based product recommendation"""
    work_type: str
    products: List[SearchResult]
    total_score: float
    reasoning: str

class ProductSearchEngine:
    """Advanced product search with relevance scoring"""
    
    def __init__(self, database: ProductDatabase = None):
        self.db = database or get_database()
        
    def search(self, query: str, filters: Dict = None, limit: int = 100) -> List[SearchResult]:
        """Search products with relevance scoring"""
        try:
            # Get raw results from database
            raw_results = self.db.search_products(query, filters, limit * 2)  # Get more for scoring
            
            # Score and rank results
            scored_results = []
            for product in raw_results:
                score, reasons = self._calculate_relevance_score(query, product)
                if score > 0:
                    scored_results.append(SearchResult(
                        product=product,
                        relevance_score=score,
                        match_reasons=reasons
                    ))
            
            # Sort by relevance score
            scored_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return scored_results[:limit]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _calculate_relevance_score(self, query: str, product: Dict) -> Tuple[float, List[str]]:
        """Calculate relevance score for a product"""
        score = 0.0
        reasons = []
        
        query_lower = query.lower()
        description = product.get('description', '').lower()
        brand = product.get('brand', '').lower()
        category = product.get('category', '').lower()
        
        # Exact SKU match
        if query_lower == product.get('product_sku', '').lower():
            score += 100
            reasons.append("Exact SKU match")
        
        # Exact phrase in description
        if query_lower in description:
            score += 50
            reasons.append("Exact phrase in description")
        
        # Brand match
        if query_lower in brand:
            score += 30
            reasons.append("Brand match")
        
        # Category match
        if query_lower in category:
            score += 20
            reasons.append("Category match")
        
        # Word matches in description
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        description_words = set(re.findall(r'\b\w+\b', description))
        
        matching_words = query_words.intersection(description_words)
        if matching_words:
            word_score = len(matching_words) / len(query_words) * 10
            score += word_score
            reasons.append(f"Word matches: {', '.join(matching_words)}")
        
        return score, reasons

class RFPAnalyzer:
    """RFP document analysis and product matching"""
    
    def __init__(self, database: ProductDatabase = None):
        self.db = database or get_database()
        self.search_engine = ProductSearchEngine(self.db)
        
        # Work type patterns
        self.work_patterns = {
            'cleaning': [
                r'\b(clean|cleaning|sanitiz|disinfect|wash|wipe|mop|vacuum)\b',
                r'\b(detergent|soap|bleach|solvent|degreaser)\b'
            ],
            'safety': [
                r'\b(safety|protection|protective|ppe|helmet|glove|goggle)\b',
                r'\b(harness|vest|boot|mask|respirator)\b'
            ],
            'tools': [
                r'\b(tool|drill|hammer|saw|wrench|screwdriver|plier)\b',
                r'\b(equipment|machinery|device|instrument)\b'
            ],
            'construction': [
                r'\b(construction|building|concrete|cement|mortar|brick)\b',
                r'\b(foundation|structure|framework|scaffold)\b'
            ],
            'maintenance': [
                r'\b(maintenance|repair|fix|service|upkeep|replace)\b',
                r'\b(lubricant|oil|grease|sealant|adhesive)\b'
            ],
            'electrical': [
                r'\b(electrical|electric|wire|cable|circuit|voltage)\b',
                r'\b(switch|outlet|breaker|conduit|junction)\b'
            ]
        }
    
    def analyze_rfp(self, document_text: str, document_id: str = None) -> RFPAnalysis:
        """Analyze RFP document and recommend products"""
        try:
            document_id = document_id or f"rfp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Detect work types
            work_types = self._detect_work_types(document_text)
            primary_work_type = work_types[0] if work_types else 'general'
            
            # Extract product requirements
            required_products = self._extract_product_requirements(document_text)
            
            # Find recommended products
            recommended_products = []
            
            # Search for explicitly mentioned products
            for requirement in required_products:
                results = self.search_engine.search(requirement, limit=5)
                recommended_products.extend(results)
            
            # Add work-type based recommendations
            work_results = self._get_work_based_recommendations(primary_work_type)
            recommended_products.extend(work_results.products[:10])
            
            # Remove duplicates and sort by relevance
            seen_products = set()
            unique_recommendations = []
            for result in recommended_products:
                product_id = result.product.get('id')
                if product_id not in seen_products:
                    seen_products.add(product_id)
                    unique_recommendations.append(result)
            
            unique_recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(
                work_types, required_products, unique_recommendations
            )
            
            # Generate analysis summary
            summary = self._generate_analysis_summary(
                primary_work_type, required_products, unique_recommendations
            )
            
            return RFPAnalysis(
                document_id=document_id,
                work_type=primary_work_type,
                required_products=required_products,
                recommended_products=unique_recommendations[:20],
                confidence_score=confidence,
                analysis_summary=summary,
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"RFP analysis failed: {e}")
            return RFPAnalysis(
                document_id=document_id or 'error',
                work_type='unknown',
                required_products=[],
                recommended_products=[],
                confidence_score=0.0,
                analysis_summary=f"Analysis failed: {str(e)}",
                created_at=datetime.now()
            )
    
    def _detect_work_types(self, text: str) -> List[str]:
        """Detect work types from document text"""
        detected = []
        text_lower = text.lower()
        
        for work_type, patterns in self.work_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            
            if score > 0:
                detected.append((work_type, score))
        
        # Sort by score and return work types
        detected.sort(key=lambda x: x[1], reverse=True)
        return [work_type for work_type, _ in detected]
    
    def _extract_product_requirements(self, text: str) -> List[str]:
        """Extract specific product requirements from text"""
        requirements = []
        
        # Look for product-like terms
        product_patterns = [
            r'\b([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Title Case Products
            r'\b(\w+\s+(?:tool|equipment|device|machine|system))\b',
            r'\b(PPE|personal protective equipment)\b',
            r'\b(\d+\s*(?:mm|cm|inch|ft)\s+\w+)\b'  # Measurements
        ]
        
        for pattern in product_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if len(match) > 3 and match not in requirements:
                    requirements.append(match.strip())
        
        return requirements[:10]  # Limit to prevent overflow
    
    def _get_work_based_recommendations(self, work_type: str) -> WorkRecommendation:
        """Get products recommended for specific work type"""
        try:
            products = self.db.get_products_by_work_type(work_type, limit=20)
            
            search_results = []
            for product in products:
                # Create mock search result for work-based recommendations
                search_results.append(SearchResult(
                    product=product,
                    relevance_score=10.0,  # Base score for work type match
                    match_reasons=[f"Recommended for {work_type} work"]
                ))
            
            return WorkRecommendation(
                work_type=work_type,
                products=search_results,
                total_score=len(search_results) * 10.0,
                reasoning=f"Products commonly used for {work_type} work"
            )
            
        except Exception as e:
            logger.error(f"Work-based recommendation failed: {e}")
            return WorkRecommendation(
                work_type=work_type,
                products=[],
                total_score=0.0,
                reasoning=f"No recommendations available for {work_type}"
            )
    
    def _calculate_confidence(self, work_types: List[str], requirements: List[str], 
                            recommendations: List[SearchResult]) -> float:
        """Calculate analysis confidence score"""
        confidence = 0.0
        
        # Work type detection confidence
        if work_types:
            confidence += 30.0
        
        # Requirements extraction confidence
        if requirements:
            confidence += min(len(requirements) * 5, 30.0)
        
        # Recommendations quality confidence
        if recommendations:
            avg_relevance = sum(r.relevance_score for r in recommendations) / len(recommendations)
            confidence += min(avg_relevance, 40.0)
        
        return min(confidence, 100.0)
    
    def _generate_analysis_summary(self, work_type: str, requirements: List[str], 
                                 recommendations: List[SearchResult]) -> str:
        """Generate human-readable analysis summary"""
        summary_parts = []
        
        summary_parts.append(f"Primary work type identified: {work_type}")
        
        if requirements:
            summary_parts.append(f"Extracted {len(requirements)} specific requirements:")
            for req in requirements[:5]:  # Show top 5
                summary_parts.append(f"  - {req}")
        
        if recommendations:
            summary_parts.append(f"Found {len(recommendations)} matching products:")
            for rec in recommendations[:3]:  # Show top 3
                product = rec.product
                summary_parts.append(
                    f"  - {product.get('brand', 'Unknown')} {product.get('description', 'Unknown')[:50]}..."
                )
        
        return "\n".join(summary_parts)

class WorkRecommendationEngine:
    """Work-based product recommendation system"""
    
    def __init__(self, database: ProductDatabase = None):
        self.db = database or get_database()
        
        # Enhanced work type mappings with specific keywords
        self.work_mappings = {
            'cement work': {
                'categories': ['18 - Tools'],
                'keywords': ['cement', 'concrete', 'mortar', 'trowel', 'float', 'mixer', 'vibrator'],
                'brands': ['Makita', 'DeWalt', 'Bosch']
            },
            'cleaning': {
                'categories': ['05 - Cleaning Products'],
                'keywords': ['clean', 'detergent', 'disinfectant', 'sanitizer', 'soap', 'bleach'],
                'brands': ['Diversey', 'Ecolab', 'Kimberly-Clark']
            },
            'safety': {
                'categories': ['21 - Safety Products'],
                'keywords': ['helmet', 'gloves', 'goggles', 'harness', 'vest', 'boots', 'mask'],
                'brands': ['3M', 'Honeywell', 'MSA']
            },
            'tools': {
                'categories': ['18 - Tools'],
                'keywords': ['drill', 'saw', 'hammer', 'wrench', 'screwdriver', 'pliers'],
                'brands': ['Stanley', 'Klein Tools', 'Ridgid']
            }
        }
    
    def get_recommendations(self, work_type: str, context: str = None) -> WorkRecommendation:
        """Get product recommendations for specific work type"""
        try:
            work_key = work_type.lower()
            
            # Get work configuration
            if work_key not in self.work_mappings:
                # Fallback to fuzzy matching
                work_key = self._find_similar_work_type(work_key)
            
            if work_key not in self.work_mappings:
                return self._fallback_recommendation(work_type)
            
            config = self.work_mappings[work_key]
            
            # Get products by category
            category_products = []
            for category in config['categories']:
                products = self.db.search_products('', {'category': category}, limit=50)
                category_products.extend(products)
            
            # Score products based on keywords and context
            scored_products = []
            for product in category_products:
                score, reasons = self._score_product_for_work(product, config, context)
                if score > 0:
                    scored_products.append(SearchResult(
                        product=product,
                        relevance_score=score,
                        match_reasons=reasons
                    ))
            
            # Sort by relevance
            scored_products.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Generate reasoning
            reasoning = self._generate_recommendation_reasoning(work_type, config, scored_products)
            
            return WorkRecommendation(
                work_type=work_type,
                products=scored_products[:20],
                total_score=sum(p.relevance_score for p in scored_products[:20]),
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Work recommendation failed: {e}")
            return WorkRecommendation(
                work_type=work_type,
                products=[],
                total_score=0.0,
                reasoning=f"Failed to generate recommendations: {str(e)}"
            )
    
    def _score_product_for_work(self, product: Dict, config: Dict, context: str = None) -> Tuple[float, List[str]]:
        """Score product relevance for specific work type"""
        score = 10.0  # Base score for category match
        reasons = ["Category match"]
        
        description = product.get('description', '').lower()
        brand = product.get('brand', '').lower()
        
        # Keyword matching
        matching_keywords = []
        for keyword in config['keywords']:
            if keyword.lower() in description:
                score += 5.0
                matching_keywords.append(keyword)
        
        if matching_keywords:
            reasons.append(f"Keywords: {', '.join(matching_keywords)}")
        
        # Brand preference
        for preferred_brand in config['brands']:
            if preferred_brand.lower() in brand:
                score += 10.0
                reasons.append(f"Preferred brand: {preferred_brand}")
                break
        
        # Context matching
        if context:
            context_lower = context.lower()
            context_words = set(re.findall(r'\b\w+\b', context_lower))
            description_words = set(re.findall(r'\b\w+\b', description))
            
            matching_context = context_words.intersection(description_words)
            if matching_context:
                score += len(matching_context) * 2
                reasons.append(f"Context match: {', '.join(list(matching_context)[:3])}")
        
        return score, reasons
    
    def _find_similar_work_type(self, work_type: str) -> Optional[str]:
        """Find similar work type using fuzzy matching"""
        work_lower = work_type.lower()
        
        # Simple keyword matching
        for key, config in self.work_mappings.items():
            if any(keyword in work_lower for keyword in config['keywords'][:3]):
                return key
                
        return None
    
    def _fallback_recommendation(self, work_type: str) -> WorkRecommendation:
        """Fallback recommendation when work type is not recognized"""
        # Search for products matching the work type text
        search_results = []
        raw_products = get_database().search_products(work_type, limit=10)
        
        for product in raw_products:
            search_results.append(SearchResult(
                product=product,
                relevance_score=5.0,
                match_reasons=["Text match with work type"]
            ))
        
        return WorkRecommendation(
            work_type=work_type,
            products=search_results,
            total_score=len(search_results) * 5.0,
            reasoning=f"General products matching '{work_type}' - work type not specifically recognized"
        )
    
    def _generate_recommendation_reasoning(self, work_type: str, config: Dict, 
                                        products: List[SearchResult]) -> str:
        """Generate explanation for recommendations"""
        reasoning_parts = [
            f"Recommendations for {work_type} based on:",
            f"• Product categories: {', '.join(config['categories'])}",
            f"• Key requirements: {', '.join(config['keywords'][:5])}",
            f"• Preferred brands: {', '.join(config['brands'])}"
        ]
        
        if products:
            reasoning_parts.append(f"• Found {len(products)} matching products")
            
            # Show top scoring reasons
            top_reasons = set()
            for product in products[:5]:
                top_reasons.update(product.match_reasons)
            
            if top_reasons:
                reasoning_parts.append(f"• Match criteria: {', '.join(list(top_reasons)[:3])}")
        
        return "\n".join(reasoning_parts)

# Global instances
_search_engine = None
_rfp_analyzer = None
_recommendation_engine = None

def get_search_engine() -> ProductSearchEngine:
    """Get global search engine instance"""
    global _search_engine
    if _search_engine is None:
        _search_engine = ProductSearchEngine()
    return _search_engine

def get_rfp_analyzer() -> RFPAnalyzer:
    """Get global RFP analyzer instance"""
    global _rfp_analyzer
    if _rfp_analyzer is None:
        _rfp_analyzer = RFPAnalyzer()
    return _rfp_analyzer

def get_recommendation_engine() -> WorkRecommendationEngine:
    """Get global recommendation engine instance"""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = WorkRecommendationEngine()
    return _recommendation_engine