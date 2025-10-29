#!/usr/bin/env python3
"""
Enhanced RFP Analysis System with Real Product Database Integration
Connects to the actual products.db with 17,266 products for realistic RFP processing.
"""

import os
import sys
import json
import sqlite3
import re
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import traceback

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import optional dependencies for enhanced matching
try:
    from fuzzywuzzy import fuzz, process
    HAS_FUZZYWUZZY = True
    logger.info("FuzzyWuzzy available for enhanced matching")
except ImportError:
    HAS_FUZZYWUZZY = False
    logger.warning("FuzzyWuzzy not available, using basic string matching")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

@dataclass
class RequirementItem:
    """Represents a single requirement extracted from an RFP."""
    category: str
    description: str
    quantity: int
    specifications: Dict[str, str]
    keywords: List[str]
    priority: int = 1  # 1=high, 2=medium, 3=low

@dataclass
class ProductMatch:
    """Represents a product match for a requirement."""
    product_id: int
    sku: str
    product_name: str
    description: str
    brand: str
    category: str
    availability: str
    currency: str
    estimated_price: float  # Generated price since not stored
    match_score: float
    matching_keywords: List[str]
    match_reasons: List[str]

@dataclass
class PricingRule:
    """Represents a pricing rule for markup calculations."""
    category: str
    base_markup: float
    volume_discount: float
    minimum_margin: float
    brand_premium: float = 0.0

class RealProductCatalog:
    """Product catalog that connects to the real products.db database."""
    
    def __init__(self, db_path: str = "products.db"):
        self.db_path = db_path
        self.connection = None
        self.categories = {}
        self.brands = {}
        self.product_count = 0
        self._load_metadata()
    
    def _load_metadata(self):
        """Load categories, brands, and product count from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load categories
            cursor.execute("SELECT id, name FROM categories")
            self.categories = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Load brands
            cursor.execute("SELECT id, name FROM brands")
            self.brands = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get product count
            cursor.execute("SELECT COUNT(*) FROM products WHERE is_published = 1")
            self.product_count = cursor.fetchone()[0]
            
            conn.close()
            logger.info(f"Loaded metadata: {len(self.categories)} categories, {len(self.brands)} brands, {self.product_count} products")
            
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            self.categories = {}
            self.brands = {}
            self.product_count = 0
    
    def _generate_estimated_price(self, product_name: str, category: str, brand: str) -> float:
        """Generate estimated pricing based on product characteristics."""
        base_price = 50.0  # Default base price
        
        # Category-based pricing
        category_multipliers = {
            'cleaning': 0.8,
            'electrical': 2.5,
            'power tools': 3.0,
            'safety': 1.8,
            'hardware': 1.2,
            'automotive': 2.0,
            'industrial': 2.8
        }
        
        # Brand premiums
        premium_brands = ['3M', '3M SCOTCH', 'ABB', 'AEG', 'MAKITA', 'DEWALT', 'BOSCH']
        
        # Apply category multiplier
        for cat_key, multiplier in category_multipliers.items():
            if cat_key.lower() in category.lower() or cat_key.lower() in product_name.lower():
                base_price *= multiplier
                break
        
        # Apply brand premium
        if brand.upper() in [b.upper() for b in premium_brands]:
            base_price *= 1.4
        elif brand.upper() != 'NO BRAND':
            base_price *= 1.1
        
        # Product-specific adjustments based on keywords
        name_lower = product_name.lower()
        if any(word in name_lower for word in ['spray', 'cleaner', 'detergent']):
            base_price *= 0.6
        elif any(word in name_lower for word in ['tool', 'drill', 'saw', 'grinder']):
            base_price *= 4.0
        elif any(word in name_lower for word in ['cable', 'wire', 'connector']):
            base_price *= 1.5
        elif any(word in name_lower for word in ['safety', 'protection', 'helmet']):
            base_price *= 2.0
        
        # Add some randomization based on SKU for consistency
        sku_hash = abs(hash(product_name)) % 100
        price_variation = 0.8 + (sku_hash / 100.0) * 0.4  # 0.8 to 1.2 multiplier
        base_price *= price_variation
        
        return round(base_price, 2)
    
    def search_products(self, keywords: List[str], category_filter: str = None, 
                       fuzzy_threshold: int = 60, limit: int = 10) -> List[ProductMatch]:
        """Search products using advanced keyword matching."""
        if not keywords:
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build search query
            search_terms = []
            params = []
            
            # Create search conditions for each keyword
            for keyword in keywords:
                search_terms.append("""
                    (p.name LIKE ? OR p.description LIKE ? OR p.sku LIKE ? OR 
                     c.name LIKE ? OR b.name LIKE ?)
                """)
                keyword_param = f"%{keyword}%"
                params.extend([keyword_param] * 5)
            
            where_clause = " AND ".join(search_terms)
            
            # Add category filter if specified
            if category_filter:
                where_clause += " AND c.name LIKE ?"
                params.append(f"%{category_filter}%")
            
            # Main search query
            query = f"""
            SELECT DISTINCT p.id, p.sku, p.name, p.description, p.availability, p.currency,
                   c.name as category_name, b.name as brand_name
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            LEFT JOIN brands b ON p.brand_id = b.id 
            WHERE p.is_published = 1 AND ({where_clause})
            ORDER BY 
                CASE WHEN p.name LIKE ? THEN 1 ELSE 2 END,
                LENGTH(p.name)
            LIMIT ?
            """
            
            # Add primary keyword for ordering and limit
            primary_keyword = f"%{keywords[0]}%" if keywords else "%"
            params.extend([primary_keyword, limit * 2])  # Get more results for scoring
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            conn.close()
            
            # Score and rank results
            matches = []
            for result in results:
                match_score, matching_keywords, match_reasons = self._calculate_match_score(
                    keywords, result, fuzzy_threshold
                )
                
                if match_score >= (fuzzy_threshold / 100.0) * 50:  # Minimum score threshold
                    estimated_price = self._generate_estimated_price(
                        result[2], result[6] or "General", result[7] or "NO BRAND"
                    )
                    
                    match = ProductMatch(
                        product_id=result[0],
                        sku=result[1],
                        product_name=result[2],
                        description=result[3] or "",
                        brand=result[7] or "NO BRAND",
                        category=result[6] or "General",
                        availability=result[4] or "unknown",
                        currency=result[5] or "USD",
                        estimated_price=estimated_price,
                        match_score=match_score,
                        matching_keywords=matching_keywords,
                        match_reasons=match_reasons
                    )
                    matches.append(match)
            
            # Sort by match score and return top results
            matches.sort(key=lambda x: x.match_score, reverse=True)
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    def _calculate_match_score(self, search_keywords: List[str], 
                              product_result: tuple, fuzzy_threshold: int) -> Tuple[float, List[str], List[str]]:
        """Calculate comprehensive match score for a product."""
        product_id, sku, name, description, availability, currency, category, brand = product_result
        
        # Combine all searchable text
        searchable_text = f"{name} {description or ''} {sku} {category or ''} {brand or ''}".lower()
        
        total_score = 0.0
        matching_keywords = []
        match_reasons = []
        
        for keyword in search_keywords:
            keyword_lower = keyword.lower()
            keyword_score = 0
            
            # Exact match in product name (highest weight)
            if keyword_lower in name.lower():
                keyword_score += 100
                match_reasons.append(f"Exact match in name: '{keyword}'")
            
            # Exact match in SKU (high weight)
            elif keyword_lower in sku.lower():
                keyword_score += 90
                match_reasons.append(f"Match in SKU: '{keyword}'")
            
            # Exact match in category (high weight)
            elif category and keyword_lower in category.lower():
                keyword_score += 85
                match_reasons.append(f"Match in category: '{keyword}'")
            
            # Exact match in brand (medium-high weight)
            elif brand and keyword_lower in brand.lower():
                keyword_score += 75
                match_reasons.append(f"Match in brand: '{keyword}'")
            
            # Exact match in description (medium weight)
            elif description and keyword_lower in description.lower():
                keyword_score += 60
                match_reasons.append(f"Match in description: '{keyword}'")
            
            # Fuzzy matching if available
            elif HAS_FUZZYWUZZY:
                # Fuzzy match against name
                name_ratio = fuzz.partial_ratio(keyword_lower, name.lower())
                if name_ratio >= fuzzy_threshold:
                    keyword_score += name_ratio * 0.8
                    match_reasons.append(f"Fuzzy match in name: '{keyword}' ({name_ratio}%)")
                
                # Fuzzy match against description
                elif description:
                    desc_ratio = fuzz.partial_ratio(keyword_lower, description.lower())
                    if desc_ratio >= fuzzy_threshold:
                        keyword_score += desc_ratio * 0.5
                        match_reasons.append(f"Fuzzy match in description: '{keyword}' ({desc_ratio}%)")
            
            # Basic substring matching fallback
            elif keyword_lower in searchable_text:
                keyword_score += 40
                match_reasons.append(f"Substring match: '{keyword}'")
            
            if keyword_score > 0:
                total_score += keyword_score
                matching_keywords.append(keyword)
        
        # Calculate final score (0-100 scale)
        if search_keywords:
            # Average score weighted by keyword coverage
            coverage_ratio = len(matching_keywords) / len(search_keywords)
            average_score = total_score / len(search_keywords)
            final_score = average_score * coverage_ratio
            
            # Bonus for availability
            if availability == 'in_stock':
                final_score *= 1.1
                match_reasons.append("Product in stock bonus")
            
            return min(final_score, 100.0), matching_keywords, match_reasons
        
        return 0.0, [], []
    
    def get_product_by_id(self, product_id: int) -> Optional[ProductMatch]:
        """Get a specific product by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT p.id, p.sku, p.name, p.description, p.availability, p.currency,
                   c.name as category_name, b.name as brand_name
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            LEFT JOIN brands b ON p.brand_id = b.id 
            WHERE p.id = ? AND p.is_published = 1
            """, (product_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                estimated_price = self._generate_estimated_price(
                    result[2], result[6] or "General", result[7] or "NO BRAND"
                )
                
                return ProductMatch(
                    product_id=result[0],
                    sku=result[1],
                    product_name=result[2],
                    description=result[3] or "",
                    brand=result[7] or "NO BRAND",
                    category=result[6] or "General",
                    availability=result[4] or "unknown",
                    currency=result[5] or "USD",
                    estimated_price=estimated_price,
                    match_score=100.0,
                    matching_keywords=[],
                    match_reasons=["Direct product lookup"]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting product by ID: {e}")
            return None
    
    def get_categories(self) -> Dict[int, str]:
        """Get all available categories."""
        return self.categories.copy()
    
    def get_brands(self) -> Dict[int, str]:
        """Get all available brands."""
        return self.brands.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get catalog statistics."""
        return {
            'total_products': self.product_count,
            'total_categories': len(self.categories),
            'total_brands': len(self.brands),
            'database_path': self.db_path
        }

class EnhancedRFPParser:
    """Enhanced RFP document parser with better pattern recognition."""
    
    def __init__(self):
        # Enhanced patterns for better requirement extraction
        self.requirement_patterns = [
            # Quantity first patterns
            r'(\d+)\s*(?:units?|pcs?|pieces?|qty|quantity)\s+(?:of\s+)?(.+?)(?=\n|\.|;|$)',
            r'(\d+)\s*x\s+(.+?)(?=\n|\.|;|$)',
            r'(\d+)\s+(.+?)(?:\s+(?:units?|pcs?|pieces?))(?=\n|\.|;|$)',
            
            # Description first patterns
            r'(.+?):\s*(\d+)\s*(?:units?|pcs?|pieces?|qty)',
            r'(.+?)\s*[-–]\s*(\d+)\s*(?:units?|pcs?|pieces?)',
            
            # Action-based patterns
            r'(?:require|need|want|request)\s+(\d+)\s+(.+?)(?=\n|\.|;|$)',
            r'(?:purchase|buy|order)\s+(\d+)\s+(.+?)(?=\n|\.|;|$)',
            
            # List-based patterns
            r'^\s*\d+\.\s*(\d+)\s*(?:units?|pcs?)?\s+(.+?)(?=\n|$)',
            r'^\s*[-•]\s*(\d+)\s*(?:units?|pcs?)?\s+(.+?)(?=\n|$)',
        ]
        
        # Enhanced specification patterns
        self.spec_patterns = [
            (r'(\d+(?:\.\d+)?)\s*(?:volt|v)s?(?:\s+(?:ac|dc))?', 'voltage'),
            (r'(\d+(?:\.\d+)?)\s*(?:amp|a)s?', 'current'),
            (r'(\d+(?:\.\d+)?)\s*(?:watt|w)s?', 'power'),
            (r'(\d+(?:\.\d+)?)\s*(?:mm|millimeter)s?', 'dimension_mm'),
            (r'(\d+(?:\.\d+)?)\s*(?:cm|centimeter)s?', 'dimension_cm'),
            (r'(\d+(?:\.\d+)?)\s*(?:m|meter)s?(?:\s+(?:long|length))?', 'length_m'),
            (r'(\d+(?:\.\d+)?)\s*(?:ft|feet|foot)', 'length_ft'),
            (r'(\d+(?:\.\d+)?)\s*(?:inch|in|")s?', 'dimension_inch'),
            (r'ip\s*(\d+)', 'ip_rating'),
            (r'(\d+)\s*k(?:\s+color)?', 'color_temperature'),
            (r'(\d+)\s*p(?:\s+resolution)?', 'resolution'),
            (r'(\d+(?:\.\d+)?)\s*(?:kg|kilogram)s?', 'weight_kg'),
            (r'(\d+(?:\.\d+)?)\s*(?:lb|pound)s?', 'weight_lb'),
            (r'(\d+(?:\.\d+)?)\s*(?:hz|hertz)', 'frequency'),
        ]
    
    def parse_text(self, text: str) -> List[RequirementItem]:
        """Parse RFP text with enhanced pattern recognition."""
        requirements = []
        
        # Preprocess text
        text = self._preprocess_text(text)
        
        # Split into lines and sections
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Try to extract requirements from this line
            req = self._extract_requirement_from_line(line, line_num)
            if req:
                requirements.append(req)
        
        # If no structured requirements found, try paragraph extraction
        if not requirements:
            requirements = self._extract_from_paragraphs(text)
        
        # Post-process and enhance requirements
        requirements = self._enhance_requirements(requirements)
        
        logger.info(f"Extracted {len(requirements)} requirements from RFP text")
        return requirements
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize the input text."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common formatting issues
        text = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', text)  # Fix decimal numbers
        text = re.sub(r'(\d+)\s*,\s*(\d+)', r'\1,\2', text)   # Fix thousands separators
        
        # Ensure line breaks are preserved for list items
        text = re.sub(r'(\n\s*\d+\.)|\n\s*[-•]', r'\n\1', text)
        
        return text
    
    def _extract_requirement_from_line(self, line: str, line_num: int) -> Optional[RequirementItem]:
        """Extract a requirement from a single line."""
        for pattern in self.requirement_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    groups = match.groups()
                    if len(groups) != 2:
                        continue
                    
                    # Try to parse quantity and description
                    try:
                        quantity = int(groups[0])
                        description = groups[1].strip()
                    except ValueError:
                        try:
                            quantity = int(groups[1])
                            description = groups[0].strip()
                        except ValueError:
                            continue
                    
                    if quantity <= 0 or not description or len(description) < 3:
                        continue
                    
                    # Clean up description
                    description = self._clean_description(description)
                    
                    # Extract details
                    keywords = self._extract_keywords(description)
                    category = self._infer_category(description, keywords)
                    specifications = self._extract_specifications(description)
                    priority = self._determine_priority(description, line_num)
                    
                    return RequirementItem(
                        category=category,
                        description=description,
                        quantity=quantity,
                        specifications=specifications,
                        keywords=keywords,
                        priority=priority
                    )
                    
                except Exception as e:
                    logger.debug(f"Error parsing line '{line}': {e}")
                    continue
        
        return None
    
    def _extract_from_paragraphs(self, text: str) -> List[RequirementItem]:
        """Extract requirements from paragraph text when line-by-line fails."""
        requirements = []
        
        # Split into sentences
        sentences = re.split(r'[.!?\n]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            # Look for quantity indicators
            quantity_matches = re.findall(r'\b(\d+)\b', sentence)
            if not quantity_matches:
                continue
            
            quantity = int(quantity_matches[0])
            if quantity <= 0:
                continue
            
            # Extract meaningful keywords
            keywords = self._extract_keywords(sentence)
            if len(keywords) < 2:
                continue
            
            category = self._infer_category(sentence, keywords)
            specifications = self._extract_specifications(sentence)
            
            requirements.append(RequirementItem(
                category=category,
                description=sentence,
                quantity=quantity,
                specifications=specifications,
                keywords=keywords,
                priority=2  # Medium priority for paragraph extractions
            ))
        
        return requirements
    
    def _clean_description(self, description: str) -> str:
        """Clean and normalize requirement descriptions."""
        # Remove extra whitespace
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Remove common prefixes/suffixes
        description = re.sub(r'^(?:of\s+|for\s+)', '', description, flags=re.IGNORECASE)
        description = re.sub(r'(?:\s+each|\s+ea\.?)$', '', description, flags=re.IGNORECASE)
        
        # Capitalize first letter
        if description:
            description = description[0].upper() + description[1:]
        
        return description
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        # Remove quantity-related words and common noise
        clean_text = re.sub(r'\d+\s*(?:units?|pcs?|pieces?|qty|quantity)', '', text, flags=re.IGNORECASE)
        clean_text = re.sub(r'\b(?:require|need|want|request|purchase|buy|order)\b', '', clean_text, flags=re.IGNORECASE)
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z0-9]+\b', clean_text.lower())
        
        # Filter stop words and short words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall',
            'this', 'that', 'these', 'those', 'from', 'up', 'down', 'out', 'off', 'over',
            'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
            'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'just', 'now'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:10]  # Limit to top 10 keywords
    
    def _infer_category(self, description: str, keywords: List[str]) -> str:
        """Infer product category from description and keywords."""
        category_mappings = {
            'Lighting': ['light', 'led', 'lamp', 'fixture', 'bulb', 'illumination', 'lighting', 'strip', 'spotlight'],
            'Electrical': ['electrical', 'electric', 'wire', 'cable', 'connector', 'switch', 'outlet', 'voltage', 'current', 'power'],
            'Power Tools': ['drill', 'saw', 'grinder', 'tool', 'motor', 'power tool', 'electric tool', 'cordless'],
            'Safety Products': ['safety', 'protection', 'helmet', 'gloves', 'vest', 'goggles', 'mask', 'harness', 'ppe'],
            'Cleaning Products': ['clean', 'cleaner', 'detergent', 'soap', 'spray', 'degreaser', 'disinfectant', 'sanitizer'],
            'Hardware': ['bolt', 'screw', 'nut', 'washer', 'fastener', 'mounting', 'bracket', 'clamp', 'fitting'],
            'Automotive': ['car', 'vehicle', 'automotive', 'engine', 'brake', 'tire', 'oil', 'filter', 'battery'],
            'Industrial': ['industrial', 'machinery', 'equipment', 'bearing', 'valve', 'pump', 'compressor', 'hydraulic'],
            'Electronics': ['electronic', 'circuit', 'board', 'component', 'resistor', 'capacitor', 'sensor', 'display'],
            'Networking': ['network', 'ethernet', 'cable', 'router', 'switch', 'wifi', 'wireless', 'internet'],
            'HVAC': ['heating', 'cooling', 'ventilation', 'hvac', 'air', 'fan', 'filter', 'duct', 'thermostat'],
            'Plumbing': ['plumbing', 'pipe', 'fitting', 'valve', 'faucet', 'drain', 'water', 'sewer', 'toilet']
        }
        
        description_lower = description.lower()
        combined_text = description_lower + ' ' + ' '.join(keywords)
        
        # Score each category
        category_scores = {}
        for category, category_keywords in category_mappings.items():
            score = 0
            for keyword in category_keywords:
                if keyword.lower() in combined_text:
                    # Higher weight for exact keyword matches
                    if keyword.lower() in keywords:
                        score += 3
                    else:
                        score += 1
            category_scores[category] = score
        
        # Return category with highest score, or 'General' if no matches
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:
                return best_category[0]
        
        return 'General'
    
    def _extract_specifications(self, description: str) -> Dict[str, str]:
        """Extract technical specifications from description."""
        specs = {}
        description_lower = description.lower()
        
        for pattern, spec_name in self.spec_patterns:
            matches = re.findall(pattern, description_lower)
            if matches:
                specs[spec_name] = matches[0]
        
        return specs
    
    def _determine_priority(self, description: str, line_number: int) -> int:
        """Determine requirement priority based on context clues."""
        description_lower = description.lower()
        
        # High priority indicators
        high_priority_words = ['critical', 'essential', 'required', 'must', 'urgent', 'priority', 'important']
        if any(word in description_lower for word in high_priority_words):
            return 1
        
        # Low priority indicators
        low_priority_words = ['optional', 'nice to have', 'preferred', 'if available', 'consider']
        if any(word in description_lower for word in low_priority_words):
            return 3
        
        # Medium priority for items later in the list (assuming importance decreases)
        if line_number > 10:
            return 2
        
        return 1  # Default to high priority
    
    def _enhance_requirements(self, requirements: List[RequirementItem]) -> List[RequirementItem]:
        """Post-process and enhance extracted requirements."""
        enhanced = []
        
        for req in requirements:
            # Skip duplicates
            if any(self._are_requirements_similar(req, existing) for existing in enhanced):
                continue
            
            # Enhance keywords with synonyms/variations
            enhanced_keywords = self._expand_keywords(req.keywords)
            req.keywords = enhanced_keywords
            
            enhanced.append(req)
        
        return enhanced
    
    def _are_requirements_similar(self, req1: RequirementItem, req2: RequirementItem) -> bool:
        """Check if two requirements are similar (to avoid duplicates)."""
        # Simple similarity check based on description overlap
        desc1_words = set(req1.description.lower().split())
        desc2_words = set(req2.description.lower().split())
        
        if len(desc1_words) == 0 or len(desc2_words) == 0:
            return False
        
        overlap = len(desc1_words.intersection(desc2_words))
        similarity = overlap / min(len(desc1_words), len(desc2_words))
        
        return similarity > 0.7
    
    def _expand_keywords(self, keywords: List[str]) -> List[str]:
        """Expand keywords with common synonyms and variations."""
        synonym_map = {
            'light': ['lighting', 'lamp', 'bulb', 'led'],
            'cable': ['wire', 'cord', 'lead'],
            'tool': ['equipment', 'device', 'instrument'],
            'safety': ['protection', 'security', 'protective'],
            'clean': ['cleaning', 'cleaner', 'detergent'],
            'power': ['electrical', 'electric', 'energy'],
            'sensor': ['detector', 'monitor', 'gauge'],
            'camera': ['surveillance', 'cctv', 'monitoring'],
            'battery': ['power', 'backup', 'ups'],
            'network': ['networking', 'ethernet', 'internet']
        }
        
        expanded = keywords.copy()
        for keyword in keywords[:]:  # Copy to avoid modification during iteration
            if keyword.lower() in synonym_map:
                for synonym in synonym_map[keyword.lower()]:
                    if synonym not in expanded and len(expanded) < 15:
                        expanded.append(synonym)
        
        return expanded

class EnhancedPricingCalculator:
    """Enhanced pricing calculator with realistic industry pricing rules."""
    
    def __init__(self):
        # Enhanced pricing rules based on real industry categories
        self.pricing_rules = {
            'Cleaning Products': PricingRule('Cleaning Products', 0.30, 0.15, 0.20, 0.05),
            'Electrical': PricingRule('Electrical', 0.35, 0.12, 0.25, 0.10),
            'Power Tools': PricingRule('Power Tools', 0.40, 0.10, 0.30, 0.15),
            'Safety Products': PricingRule('Safety Products', 0.45, 0.08, 0.35, 0.12),
            'Hardware': PricingRule('Hardware', 0.25, 0.18, 0.15, 0.03),
            'Automotive': PricingRule('Automotive', 0.32, 0.14, 0.22, 0.08),
            'Industrial': PricingRule('Industrial', 0.38, 0.11, 0.28, 0.12),
            'Electronics': PricingRule('Electronics', 0.42, 0.09, 0.32, 0.18),
            'Networking': PricingRule('Networking', 0.35, 0.13, 0.25, 0.10),
            'HVAC': PricingRule('HVAC', 0.33, 0.12, 0.23, 0.08),
            'Plumbing': PricingRule('Plumbing', 0.28, 0.16, 0.18, 0.05),
            'Lighting': PricingRule('Lighting', 0.36, 0.11, 0.26, 0.08),
            'General': PricingRule('General', 0.30, 0.15, 0.20, 0.05)
        }
        
        # Brand premium multipliers
        self.brand_premiums = {
            '3M': 1.5, '3M SCOTCH': 1.4, 'ABB': 1.3, 'AEG': 1.3, 'MAKITA': 1.4,
            'DEWALT': 1.4, 'BOSCH': 1.3, 'MILWAUKEE': 1.3, 'FESTOOL': 1.6,
            'SNAP-ON': 1.7, 'FLUKE': 1.5, 'KLEIN': 1.2, 'STANLEY': 1.1,
            'NO BRAND': 0.9, 'GENERIC': 0.8
        }
    
    def calculate_price(self, base_price: float, quantity: int, category: str = 'General', 
                       brand: str = 'NO BRAND', priority: int = 1) -> Dict[str, Any]:
        """Calculate enhanced pricing with multiple factors."""
        rule = self.pricing_rules.get(category, self.pricing_rules['General'])
        
        # Apply base markup
        marked_up_price = base_price * (1 + rule.base_markup)
        
        # Apply brand premium
        brand_multiplier = self.brand_premiums.get(brand.upper(), 1.0)
        if brand_multiplier != 1.0:
            marked_up_price *= brand_multiplier
        
        # Apply volume discount based on quantity
        volume_discount = 0
        if quantity >= 500:
            volume_discount = rule.volume_discount * 1.5
        elif quantity >= 200:
            volume_discount = rule.volume_discount * 1.2
        elif quantity >= 100:
            volume_discount = rule.volume_discount
        elif quantity >= 50:
            volume_discount = rule.volume_discount * 0.7
        elif quantity >= 20:
            volume_discount = rule.volume_discount * 0.4
        elif quantity >= 10:
            volume_discount = rule.volume_discount * 0.2
        
        discounted_price = marked_up_price * (1 - volume_discount)
        
        # Priority adjustment (urgent orders may have higher pricing)
        priority_multiplier = 1.0
        if priority == 1:  # High priority
            priority_multiplier = 1.05
        elif priority == 3:  # Low priority
            priority_multiplier = 0.98
        
        adjusted_price = discounted_price * priority_multiplier
        
        # Ensure minimum margin
        minimum_price = base_price * (1 + rule.minimum_margin)
        final_unit_price = max(adjusted_price, minimum_price)
        
        total_price = final_unit_price * quantity
        
        # Calculate savings and margins
        original_total = base_price * quantity
        total_markup = (final_unit_price - base_price) * quantity
        
        return {
            'base_price': round(base_price, 2),
            'markup_percentage': round(rule.base_markup * 100, 1),
            'brand_premium': round((brand_multiplier - 1) * 100, 1),
            'volume_discount_percentage': round(volume_discount * 100, 1),
            'priority_adjustment': round((priority_multiplier - 1) * 100, 1),
            'unit_price': round(final_unit_price, 2),
            'total_price': round(total_price, 2),
            'quantity': quantity,
            'total_markup': round(total_markup, 2),
            'margin_percentage': round(((final_unit_price - base_price) / final_unit_price) * 100, 1),
            'savings_amount': round(max(0, original_total * volume_discount), 2),
            'category': category,
            'brand': brand,
            'priority': priority
        }

class EnhancedQuotationGenerator:
    """Enhanced quotation generator with professional formatting and database integration."""
    
    def __init__(self, db_path: str = "quotations.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize enhanced quotations database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enhanced quotations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quote_number TEXT UNIQUE NOT NULL,
                    customer_name TEXT NOT NULL,
                    customer_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    subtotal REAL NOT NULL,
                    tax_amount REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    status TEXT DEFAULT 'draft',
                    priority INTEGER DEFAULT 2,
                    valid_until DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'Enhanced RFP System',
                    probability INTEGER DEFAULT 50,
                    notes TEXT,
                    rfp_hash TEXT
                )
            ''')
            
            # Enhanced quotation items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quotation_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quotation_id INTEGER NOT NULL,
                    line_number INTEGER NOT NULL,
                    product_id INTEGER,
                    sku TEXT,
                    item_name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    brand TEXT,
                    quantity INTEGER NOT NULL,
                    base_price REAL NOT NULL,
                    unit_price REAL NOT NULL,
                    total_price REAL NOT NULL,
                    discount_percentage REAL DEFAULT 0,
                    match_score REAL,
                    specifications TEXT,
                    availability TEXT,
                    lead_time_days INTEGER,
                    FOREIGN KEY (quotation_id) REFERENCES quotations (id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quotations_number ON quotations(quote_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quotations_customer ON quotations(customer_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quotation_items_quotation ON quotation_items(quotation_id)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing enhanced database: {e}")
    
    def generate_quotation(self, requirements: List[RequirementItem], matches: Dict[str, List[ProductMatch]], 
                         pricing: Dict[str, Dict], customer_name: str = "Valued Customer",
                         rfp_text: str = "") -> Dict[str, Any]:
        """Generate enhanced professional quotation."""
        
        # Generate unique quote number with better format
        timestamp = datetime.now()
        quote_number = f"RFP-{timestamp.strftime('%Y%m%d')}-{timestamp.strftime('%H%M%S')}"
        
        # Create RFP hash for duplicate detection
        rfp_hash = hashlib.md5(rfp_text.encode()).hexdigest()[:16] if rfp_text else ""
        
        # Calculate totals and prepare items
        subtotal = 0
        quotation_items = []
        line_number = 1
        
        for req in requirements:
            req_key = f"{req.category}_{hash(req.description) % 10000}"
            if req_key in matches and matches[req_key]:
                best_match = matches[req_key][0]  # Best match
                pricing_info = pricing.get(req_key, {})
                
                # Calculate estimated lead time based on category and availability
                lead_time = self._estimate_lead_time(best_match.category, best_match.availability)
                
                item = {
                    'line_number': line_number,
                    'product_id': best_match.product_id,
                    'sku': best_match.sku,
                    'item_name': best_match.product_name,
                    'description': f"{req.description}",
                    'category': best_match.category,
                    'brand': best_match.brand,
                    'quantity': req.quantity,
                    'base_price': best_match.estimated_price,
                    'unit_price': pricing_info.get('unit_price', best_match.estimated_price),
                    'total_price': pricing_info.get('total_price', best_match.estimated_price * req.quantity),
                    'discount_percentage': pricing_info.get('volume_discount_percentage', 0),
                    'match_score': best_match.match_score,
                    'specifications': json.dumps(req.specifications) if req.specifications else None,
                    'availability': best_match.availability,
                    'lead_time_days': lead_time
                }
                quotation_items.append(item)
                subtotal += item['total_price']
                line_number += 1
        
        # Calculate tax and total
        tax_rate = 0.08  # 8% tax rate
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        # Determine priority based on requirements
        avg_priority = sum(req.priority for req in requirements) / len(requirements) if requirements else 2
        quotation_priority = round(avg_priority)
        
        # Prepare enhanced quotation data
        quotation_data = {
            'quote_number': quote_number,
            'customer_name': customer_name,
            'title': f"RFP Response - {len(requirements)} Items",
            'description': f"Professional quotation for {len(requirements)} requirement items with {len([i for i in quotation_items if i['match_score'] > 80])} high-confidence matches",
            'items': quotation_items,
            'subtotal': round(subtotal, 2),
            'tax_amount': round(tax_amount, 2),
            'total_amount': round(total_amount, 2),
            'currency': 'USD',
            'valid_until': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'created_at': timestamp.isoformat(),
            'status': 'draft',
            'priority': quotation_priority,
            'notes': self._generate_quotation_notes(requirements, matches, quotation_items),
            'rfp_hash': rfp_hash,
            'statistics': {
                'total_items': len(quotation_items),
                'high_confidence_matches': len([i for i in quotation_items if i['match_score'] > 80]),
                'medium_confidence_matches': len([i for i in quotation_items if 60 <= i['match_score'] <= 80]),
                'low_confidence_matches': len([i for i in quotation_items if i['match_score'] < 60]),
                'average_match_score': round(sum(i['match_score'] for i in quotation_items) / len(quotation_items), 1) if quotation_items else 0,
                'total_discount': round(sum(i['total_price'] * i['discount_percentage'] / 100 for i in quotation_items), 2),
                'categories_covered': len(set(i['category'] for i in quotation_items)),
                'brands_included': len(set(i['brand'] for i in quotation_items)),
                'estimated_lead_time': max([i['lead_time_days'] for i in quotation_items]) if quotation_items else 0
            }
        }
        
        # Save to database
        quotation_id = self._save_quotation(quotation_data)
        quotation_data['id'] = quotation_id
        
        return quotation_data
    
    def _estimate_lead_time(self, category: str, availability: str) -> int:
        """Estimate lead time based on category and availability."""
        base_lead_times = {
            'Cleaning Products': 3,
            'Hardware': 5,
            'Electrical': 7,
            'Safety Products': 10,
            'Power Tools': 14,
            'Industrial': 21,
            'Electronics': 14,
            'Networking': 10,
            'HVAC': 15,
            'Automotive': 12
        }
        
        base_time = base_lead_times.get(category, 10)
        
        if availability == 'in_stock':
            return base_time
        elif availability == 'low_stock':
            return base_time + 3
        elif availability == 'out_of_stock':
            return base_time + 10
        else:
            return base_time + 5  # Unknown availability
    
    def _generate_quotation_notes(self, requirements: List[RequirementItem], 
                                 matches: Dict[str, List[ProductMatch]], 
                                 items: List[Dict]) -> str:
        """Generate intelligent notes for the quotation."""
        notes = []
        
        # Matching quality notes
        high_confidence = len([i for i in items if i['match_score'] > 80])
        if high_confidence == len(items):
            notes.append("All items matched with high confidence (>80% match score)")
        elif high_confidence > len(items) * 0.7:
            notes.append(f"Most items ({high_confidence}/{len(items)}) matched with high confidence")
        else:
            notes.append(f"Some items have lower match confidence - recommend review")
        
        # Volume discount notes
        total_discount = sum(i['total_price'] * i['discount_percentage'] / 100 for i in items)
        if total_discount > 0:
            notes.append(f"Volume discounts applied: ${total_discount:.2f} savings")
        
        # Category diversity notes
        categories = set(i['category'] for i in items)
        if len(categories) > 5:
            notes.append(f"Multi-category order spanning {len(categories)} product categories")
        
        # Availability concerns
        out_of_stock = [i for i in items if i['availability'] == 'out_of_stock']
        if out_of_stock:
            notes.append(f"Note: {len(out_of_stock)} items currently out of stock")
        
        # Lead time notes
        max_lead_time = max([i['lead_time_days'] for i in items]) if items else 0
        if max_lead_time > 14:
            notes.append(f"Extended lead time: up to {max_lead_time} days for some items")
        
        return "; ".join(notes)
    
    def _save_quotation(self, quotation_data: Dict[str, Any]) -> int:
        """Save enhanced quotation to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert quotation
            cursor.execute('''
                INSERT INTO quotations 
                (quote_number, customer_name, title, description, subtotal, tax_amount, total_amount, 
                 currency, valid_until, created_by, priority, notes, rfp_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                quotation_data['quote_number'],
                quotation_data['customer_name'],
                quotation_data['title'],
                quotation_data['description'],
                quotation_data['subtotal'],
                quotation_data['tax_amount'],
                quotation_data['total_amount'],
                quotation_data['currency'],
                quotation_data['valid_until'],
                'Enhanced RFP System',
                quotation_data['priority'],
                quotation_data['notes'],
                quotation_data['rfp_hash']
            ))
            
            quotation_id = cursor.lastrowid
            
            # Insert items
            for item in quotation_data['items']:
                cursor.execute('''
                    INSERT INTO quotation_items 
                    (quotation_id, line_number, product_id, sku, item_name, description, category, brand,
                     quantity, base_price, unit_price, total_price, discount_percentage, match_score,
                     specifications, availability, lead_time_days)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    quotation_id,
                    item['line_number'],
                    item['product_id'],
                    item['sku'],
                    item['item_name'],
                    item['description'],
                    item['category'],
                    item['brand'],
                    item['quantity'],
                    item['base_price'],
                    item['unit_price'],
                    item['total_price'],
                    item['discount_percentage'],
                    item['match_score'],
                    item['specifications'],
                    item['availability'],
                    item['lead_time_days']
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved enhanced quotation {quotation_data['quote_number']} to database")
            return quotation_id
            
        except Exception as e:
            logger.error(f"Error saving enhanced quotation: {e}")
            return 0
    
    def format_quotation_text(self, quotation_data: Dict[str, Any]) -> str:
        """Format enhanced quotation as professional text."""
        stats = quotation_data.get('statistics', {})
        
        header = f"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                              PROFESSIONAL QUOTATION                                  ║
║                              Quote #{quotation_data['quote_number']}                 ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

CUSTOMER INFORMATION:
────────────────────────────────────────────────────────────────────────────────────────
Customer:           {quotation_data['customer_name']}
Quote Date:         {quotation_data['created_at'][:10]}
Valid Until:        {quotation_data['valid_until']}
Priority Level:     {'High' if quotation_data.get('priority', 2) == 1 else 'Medium' if quotation_data.get('priority', 2) == 2 else 'Low'}

QUOTATION SUMMARY:
────────────────────────────────────────────────────────────────────────────────────────
Total Items:        {stats.get('total_items', 0)}
Categories:         {stats.get('categories_covered', 0)}
Brands:            {stats.get('brands_included', 0)}
Avg Match Score:    {stats.get('average_match_score', 0)}%
Est. Lead Time:     {stats.get('estimated_lead_time', 0)} days
Total Savings:      ${stats.get('total_discount', 0):.2f}

DETAILED LINE ITEMS:
════════════════════════════════════════════════════════════════════════════════════════
"""
        
        items_text = ""
        for item in quotation_data['items']:
            confidence_indicator = "🟢" if item['match_score'] > 80 else "🟡" if item['match_score'] > 60 else "🔴"
            availability_indicator = "✅" if item['availability'] == 'in_stock' else "⚠️" if item['availability'] == 'low_stock' else "❌"
            
            items_text += f"""
{item['line_number']:2d}. {item['item_name']} {confidence_indicator} {availability_indicator}
    SKU:            {item['sku']}
    Brand:          {item['brand']}
    Category:       {item['category']}
    Description:    {item['description']}
    Quantity:       {item['quantity']:,}
    Unit Price:     ${item['unit_price']:,.2f}
    Line Total:     ${item['total_price']:,.2f}
    Match Score:    {item['match_score']:.1f}%
    Lead Time:      {item['lead_time_days']} days
    {'Discount:      ' + str(item['discount_percentage']) + '%' if item['discount_percentage'] > 0 else ''}
    
"""
        
        footer = f"""
════════════════════════════════════════════════════════════════════════════════════════
PRICING SUMMARY:
────────────────────────────────────────────────────────────────────────────────────────
Subtotal:           ${quotation_data['subtotal']:,.2f}
Tax (8%):           ${quotation_data['tax_amount']:,.2f}
────────────────────────────────────────────────────────────────────────────────────────
TOTAL:              ${quotation_data['total_amount']:,.2f} {quotation_data['currency']}
════════════════════════════════════════════════════════════════════════════════════════

TERMS & CONDITIONS:
────────────────────────────────────────────────────────────────────────────────────────
• Payment Terms:     Net 30 days from invoice date
• Validity Period:   This quotation is valid until {quotation_data['valid_until']}
• Delivery:          Ex-works, shipping and handling charges additional
• Lead Times:        As indicated per line item, subject to stock availability
• Currency:          All prices in {quotation_data['currency']}
• Warranty:          As per manufacturer's standard warranty terms

MATCH CONFIDENCE LEGEND:
🟢 High Confidence (>80%)  🟡 Medium Confidence (60-80%)  🔴 Review Required (<60%)

AVAILABILITY STATUS:
✅ In Stock  ⚠️ Low Stock  ❌ Out of Stock

NOTES:
{quotation_data.get('notes', 'No additional notes')}

────────────────────────────────────────────────────────────────────────────────────────
Generated by Enhanced RFP Analysis System
Connected to live product database with {stats.get('total_items', 0)} matched items
Database contains 17,266+ products across multiple categories
────────────────────────────────────────────────────────────────────────────────────────

Thank you for your business opportunity!
"""
        
        return header + items_text + footer

class EnhancedRFPAnalysisSystem:
    """Main enhanced RFP Analysis system with real database integration."""
    
    def __init__(self, products_db_path: str = "products.db", quotations_db_path: str = "quotations.db"):
        self.catalog = RealProductCatalog(products_db_path)
        self.parser = EnhancedRFPParser()
        self.pricing_calculator = EnhancedPricingCalculator()
        self.quotation_generator = EnhancedQuotationGenerator(quotations_db_path)
        
        logger.info("Enhanced RFP Analysis System initialized")
        logger.info(f"Connected to product database: {self.catalog.get_statistics()}")
    
    def process_rfp(self, rfp_text: str, customer_name: str = "Valued Customer", 
                   fuzzy_threshold: int = 60, max_matches_per_requirement: int = 5) -> Dict[str, Any]:
        """Complete enhanced RFP processing workflow."""
        logger.info(f"Starting enhanced RFP processing for customer: {customer_name}")
        
        try:
            # Step 1: Parse RFP document with enhanced parser
            requirements = self.parser.parse_text(rfp_text)
            logger.info(f"Extracted {len(requirements)} requirements")
            
            if not requirements:
                return self._create_error_response("No requirements could be extracted from the RFP text")
            
            # Step 2: Find product matches using real database
            all_matches = {}
            all_pricing = {}
            match_summary = {'total_searches': 0, 'successful_matches': 0, 'high_confidence': 0}
            
            for req in requirements:
                req_key = f"{req.category}_{hash(req.description) % 10000}"
                match_summary['total_searches'] += 1
                
                # Search for products with enhanced matching
                matches = self.catalog.search_products(
                    keywords=req.keywords,
                    category_filter=req.category if req.category != 'General' else None,
                    fuzzy_threshold=fuzzy_threshold,
                    limit=max_matches_per_requirement
                )
                
                if matches:
                    all_matches[req_key] = matches
                    match_summary['successful_matches'] += 1
                    
                    if matches[0].match_score > 80:
                        match_summary['high_confidence'] += 1
                    
                    # Calculate enhanced pricing for best match
                    best_match = matches[0]
                    pricing_info = self.pricing_calculator.calculate_price(
                        base_price=best_match.estimated_price,
                        quantity=req.quantity,
                        category=req.category,
                        brand=best_match.brand,
                        priority=req.priority
                    )
                    all_pricing[req_key] = pricing_info
                else:
                    logger.warning(f"No matches found for requirement: {req.description}")
            
            # Step 3: Generate enhanced quotation
            quotation = self.quotation_generator.generate_quotation(
                requirements=requirements,
                matches=all_matches,
                pricing=all_pricing,
                customer_name=customer_name,
                rfp_text=rfp_text
            )
            
            # Step 4: Prepare comprehensive response
            response = {
                'success': True,
                'requirements': [
                    {
                        'category': req.category,
                        'description': req.description,
                        'quantity': req.quantity,
                        'keywords': req.keywords,
                        'specifications': req.specifications,
                        'priority': req.priority
                    }
                    for req in requirements
                ],
                'matches': {
                    key: [
                        {
                            'product_id': match.product_id,
                            'sku': match.sku,
                            'product_name': match.product_name,
                            'description': match.description[:200] + "..." if len(match.description) > 200 else match.description,
                            'brand': match.brand,
                            'category': match.category,
                            'availability': match.availability,
                            'estimated_price': match.estimated_price,
                            'match_score': match.match_score,
                            'matching_keywords': match.matching_keywords,
                            'match_reasons': match.match_reasons
                        }
                        for match in matches
                    ]
                    for key, matches in all_matches.items()
                },
                'pricing': all_pricing,
                'quotation': quotation,
                'quotation_text': self.quotation_generator.format_quotation_text(quotation),
                'summary': {
                    'total_requirements': len(requirements),
                    'matched_requirements': match_summary['successful_matches'],
                    'high_confidence_matches': match_summary['high_confidence'],
                    'match_rate_percentage': round((match_summary['successful_matches'] / len(requirements)) * 100, 1),
                    'total_amount': quotation['total_amount'],
                    'currency': quotation['currency'],
                    'average_match_score': quotation['statistics']['average_match_score'],
                    'categories_covered': quotation['statistics']['categories_covered'],
                    'brands_included': quotation['statistics']['brands_included'],
                    'estimated_lead_time': quotation['statistics']['estimated_lead_time']
                },
                'processing_metadata': {
                    'processed_at': datetime.now().isoformat(),
                    'fuzzy_threshold': fuzzy_threshold,
                    'customer_name': customer_name,
                    'system_version': 'Enhanced RFP Analysis v2.0',
                    'database_products': self.catalog.product_count,
                    'processing_time_ms': 0  # Would be calculated in real implementation
                }
            }
            
            logger.info(f"Enhanced RFP processing completed successfully. Total: ${quotation['total_amount']:.2f}")
            return response
            
        except Exception as e:
            logger.error(f"Error in enhanced RFP processing: {e}")
            logger.error(traceback.format_exc())
            return self._create_error_response(f"Processing error: {str(e)}")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            'success': False,
            'error': error_message,
            'requirements': [],
            'matches': {},
            'pricing': {},
            'quotation': None,
            'quotation_text': '',
            'summary': {
                'total_requirements': 0,
                'matched_requirements': 0,
                'high_confidence_matches': 0,
                'match_rate_percentage': 0,
                'total_amount': 0.0,
                'currency': 'USD'
            },
            'processing_metadata': {
                'processed_at': datetime.now().isoformat(),
                'error': True
            }
        }
    
    def search_products_direct(self, keywords: List[str], category: str = None, 
                              limit: int = 20) -> List[Dict[str, Any]]:
        """Direct product search interface."""
        matches = self.catalog.search_products(keywords, category, limit=limit)
        return [
            {
                'product_id': match.product_id,
                'sku': match.sku,
                'name': match.product_name,
                'description': match.description,
                'brand': match.brand,
                'category': match.category,
                'availability': match.availability,
                'estimated_price': match.estimated_price,
                'match_score': match.match_score
            }
            for match in matches
        ]
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        catalog_stats = self.catalog.get_statistics()
        return {
            'system_name': 'Enhanced RFP Analysis System',
            'version': '2.0',
            'database_connection': True,
            'product_catalog': catalog_stats,
            'categories': list(self.catalog.get_categories().values()),
            'top_brands': list(self.catalog.get_brands().values())[:20],
            'features': [
                'Real product database integration (17,266+ products)',
                'Advanced fuzzy matching with confidence scoring',
                'Enhanced requirement parsing with priority detection',
                'Dynamic pricing with brand premiums and volume discounts',
                'Professional quotation generation with lead times',
                'Multi-category support with intelligent categorization',
                'Comprehensive match reasoning and quality indicators'
            ]
        }

# Demo and testing functionality
def demo_enhanced_system():
    """Demonstrate the enhanced RFP system with real database."""
    print("Enhanced RFP Analysis System Demo")
    print("=" * 80)
    
    # Initialize system
    system = EnhancedRFPAnalysisSystem()
    
    # Get system info
    info = system.get_system_info()
    print(f"System: {info['system_name']} v{info['version']}")
    print(f"Database: {info['product_catalog']['total_products']} products, {info['product_catalog']['total_categories']} categories")
    print()
    
    # Sample comprehensive RFP
    sample_rfp = """
    REQUEST FOR PROPOSAL - FACILITY UPGRADE PROJECT
    
    Dear Suppliers,
    
    We are seeking competitive quotations for the following critical items required 
    for our comprehensive facility upgrade and modernization project:
    
    ELECTRICAL & LIGHTING REQUIREMENTS:
    1. 45 units high-efficiency LED light fixtures for warehouse areas (minimum 100W equivalent, IP65 rated)
    2. 20 pieces smart motion sensors for automatic lighting control in corridors and storage areas
    3. 150 meters heavy-duty electrical cable Cat6 for network backbone infrastructure
    4. 8 units industrial power supply units 24V DC for control systems and automation equipment
    
    SECURITY & SAFETY SYSTEMS:
    5. 12 units weatherproof security cameras for perimeter monitoring (minimum 1080p, night vision capability)
    6. 6 pieces access control keypads for restricted area entry management
    7. 25 units safety helmets with adjustable suspension for site personnel protection
    8. 40 pairs safety gloves cut-resistant Level 3 for handling operations
    
    INDUSTRIAL EQUIPMENT:
    9. 4 units cordless drill sets with multiple bit attachments for maintenance operations
    10. 2 pieces angle grinders 7-inch for metal cutting and surface preparation
    11. 15 units heavy-duty extension cords 50ft for temporary power distribution
    12. 6 pieces digital multimeters for electrical testing and troubleshooting
    
    CLEANING & MAINTENANCE:
    13. 30 units industrial degreaser spray 750ml for equipment cleaning
    14. 20 liters all-purpose cleaner concentrate for facility maintenance
    15. 50 pieces microfiber cleaning cloths for delicate surface care
    
    DELIVERY & QUALITY REQUIREMENTS:
    - All items must be delivered within 21 days of purchase order confirmation
    - Products must meet or exceed specified technical requirements
    - Installation support preferred for electrical and security items
    - Minimum 2-year warranty required for all electronic components
    - Documentation and certification must accompany safety equipment
    
    Please provide detailed specifications, unit pricing, total costs, estimated delivery 
    timelines, and warranty information for each item. Volume discounts and package 
    deals are welcomed and should be clearly identified.
    
    This is a high-priority project with potential for additional follow-up orders.
    
    Best regards,
    Procurement Department
    Industrial Solutions Corp.
    """
    
    # Process the RFP
    print("Processing comprehensive RFP...")
    result = system.process_rfp(sample_rfp, "Industrial Solutions Corp.", fuzzy_threshold=65)
    
    if result['success']:
        print(f"\nPROCESSING RESULTS:")
        print(f"{'='*50}")
        print(f"Requirements Found:      {result['summary']['total_requirements']}")
        print(f"Successfully Matched:    {result['summary']['matched_requirements']}")
        print(f"High Confidence Matches: {result['summary']['high_confidence_matches']}")
        print(f"Match Rate:             {result['summary']['match_rate_percentage']}%")
        print(f"Categories Covered:      {result['summary']['categories_covered']}")
        print(f"Brands Included:         {result['summary']['brands_included']}")
        print(f"Estimated Lead Time:     {result['summary']['estimated_lead_time']} days")
        print(f"Total Quotation Value:   ${result['summary']['total_amount']:,.2f}")
        
        print(f"\nSAMPLE REQUIREMENTS EXTRACTED:")
        print(f"{'-'*50}")
        for i, req in enumerate(result['requirements'][:5], 1):
            print(f"{i}. {req['description']}")
            print(f"   Category: {req['category']} | Qty: {req['quantity']} | Priority: {req['priority']}")
            print(f"   Keywords: {', '.join(req['keywords'][:5])}")
            print()
        
        print(f"SAMPLE PRODUCT MATCHES:")
        print(f"{'-'*50}")
        for req_key, matches in list(result['matches'].items())[:3]:
            if matches:
                best = matches[0]
                print(f"Requirement: {req_key}")
                print(f"  Best Match: {best['product_name']} (SKU: {best['sku']})")
                print(f"  Brand: {best['brand']} | Category: {best['category']}")
                print(f"  Price: ${best['estimated_price']:.2f} | Match: {best['match_score']:.1f}%")
                print(f"  Availability: {best['availability']}")
                print(f"  Reasons: {', '.join(best['match_reasons'][:2])}")
                print()
        
        print(f"PROFESSIONAL QUOTATION GENERATED:")
        print(result['quotation_text'])
        
    else:
        print(f"ERROR: {result['error']}")

if __name__ == "__main__":
    demo_enhanced_system()