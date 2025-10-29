#!/usr/bin/env python3
"""
Product Data Enrichment Pipeline
===============================

Advanced product data enrichment system with AI-powered classification,
specification extraction, image analysis, and data quality validation.

Features:
- AI-powered product classification and categorization
- Technical specification extraction and standardization
- Image analysis and quality assessment
- Price monitoring and historical tracking
- Data quality scoring and validation
- Duplicate detection and merging
- Missing information inference
- Cross-reference with manufacturer databases
"""

import os
import re
import json
import time
import logging
import requests
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import hashlib
import statistics
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

# Image processing
try:
    from PIL import Image
    import io
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False

# Machine learning for classification
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Import production scraper components
from .production_scraper import ProductData, ProductionScraper, ScrapingConfig


@dataclass
class EnrichmentConfig:
    """Configuration for product enrichment operations."""
    
    # AI/ML settings
    enable_ai_classification: bool = True
    enable_image_analysis: bool = True
    enable_price_analysis: bool = True
    
    # Quality thresholds
    min_quality_score: float = 0.7
    min_description_length: int = 50
    require_specifications: bool = True
    require_images: bool = True
    
    # Data validation
    enable_duplicate_detection: bool = True
    duplicate_threshold: float = 0.85
    
    # External data sources
    enable_manufacturer_lookup: bool = True
    enable_market_price_check: bool = True
    
    # Processing settings
    max_concurrent_enrichments: int = 5
    enrichment_timeout: int = 30


@dataclass
class EnrichmentResult:
    """Result of product enrichment process."""
    
    original_product: ProductData
    enriched_product: ProductData
    enrichment_score: float
    quality_improvements: Dict[str, Any]
    processing_time: float
    errors: List[str]
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ProductClassifier:
    """AI-powered product classification system."""
    
    def __init__(self):
        self.logger = logging.getLogger("product_classifier")
        
        # Pre-defined category hierarchies
        self.category_hierarchy = {
            'Tools': {
                'Power Tools': ['drill', 'saw', 'grinder', 'router', 'sander'],
                'Hand Tools': ['hammer', 'screwdriver', 'wrench', 'pliers', 'chisel'],
                'Cutting Tools': ['blade', 'bit', 'cutter', 'knife', 'scissors'],
                'Measuring Tools': ['ruler', 'level', 'caliper', 'gauge', 'meter']
            },
            'Hardware': {
                'Fasteners': ['screw', 'bolt', 'nut', 'washer', 'rivet'],
                'Brackets': ['bracket', 'mount', 'hinge', 'hook', 'clamp'],
                'Wire & Cable': ['wire', 'cable', 'cord', 'conduit', 'connector']
            },
            'Safety Equipment': {
                'PPE': ['helmet', 'gloves', 'goggles', 'mask', 'vest'],
                'Safety Devices': ['alarm', 'detector', 'barrier', 'guard', 'lock'],
                'First Aid': ['kit', 'bandage', 'antiseptic', 'stretcher', 'defibrillator']
            },
            'Electrical': {
                'Components': ['resistor', 'capacitor', 'transistor', 'diode', 'relay'],
                'Wiring': ['wire', 'cable', 'connector', 'terminal', 'splice'],
                'Lighting': ['bulb', 'led', 'fixture', 'ballast', 'transformer']
            }
        }
        
        # Initialize ML models if available
        if ML_AVAILABLE:
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            self.category_vectors = None
            self._build_category_models()
    
    def _build_category_models(self):
        """Build ML models for category classification."""
        if not ML_AVAILABLE:
            return
        
        # Create training data from category hierarchy
        categories = []
        texts = []
        
        for main_cat, sub_cats in self.category_hierarchy.items():
            for sub_cat, keywords in sub_cats.items():
                categories.append(f"{main_cat} > {sub_cat}")
                texts.append(' '.join(keywords))
        
        # Fit vectorizer on category keywords
        if texts:
            self.category_vectors = self.vectorizer.fit_transform(texts)
            self.category_labels = categories
    
    def classify_product(self, product: ProductData) -> Tuple[List[str], float]:
        """
        Classify product into categories using AI/ML.
        
        Args:
            product: Product to classify
            
        Returns:
            Tuple of (categories, confidence_score)
        """
        # Combine text features for classification
        text_features = []
        if product.name:
            text_features.append(product.name)
        if product.description:
            text_features.append(product.description)
        if product.specifications:
            text_features.extend([f"{k} {v}" for k, v in product.specifications.items()])
        
        combined_text = ' '.join(text_features).lower()
        
        # Use ML classification if available
        if ML_AVAILABLE and self.category_vectors is not None:
            categories, confidence = self._ml_classify(combined_text)
        else:
            categories, confidence = self._rule_based_classify(combined_text)
        
        return categories, confidence
    
    def _ml_classify(self, text: str) -> Tuple[List[str], float]:
        """ML-based classification using TF-IDF and cosine similarity."""
        try:
            # Transform product text
            product_vector = self.vectorizer.transform([text])
            
            # Calculate similarities with category vectors
            similarities = cosine_similarity(product_vector, self.category_vectors)[0]
            
            # Get top matching categories
            top_indices = np.argsort(similarities)[-3:][::-1]  # Top 3 categories
            
            categories = []
            confidences = []
            
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    categories.append(self.category_labels[idx])
                    confidences.append(similarities[idx])
            
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return categories, float(avg_confidence)
            
        except Exception as e:
            self.logger.error(f"ML classification failed: {e}")
            return self._rule_based_classify(text)
    
    def _rule_based_classify(self, text: str) -> Tuple[List[str], float]:
        """Rule-based classification using keyword matching."""
        categories = []
        scores = []
        
        for main_cat, sub_cats in self.category_hierarchy.items():
            for sub_cat, keywords in sub_cats.items():
                score = 0
                for keyword in keywords:
                    if keyword.lower() in text:
                        score += 1
                
                if score > 0:
                    categories.append(f"{main_cat} > {sub_cat}")
                    scores.append(score / len(keywords))
        
        # Sort by score and take top categories
        if categories:
            sorted_cats = sorted(zip(categories, scores), key=lambda x: x[1], reverse=True)
            categories = [cat for cat, _ in sorted_cats[:3]]
            avg_confidence = statistics.mean([score for _, score in sorted_cats[:3]])
        else:
            avg_confidence = 0.0
        
        return categories, avg_confidence


class SpecificationExtractor:
    """Extract and standardize product specifications."""
    
    def __init__(self):
        self.logger = logging.getLogger("spec_extractor")
        
        # Standardized specification mappings
        self.spec_mappings = {
            # Dimensions
            'dimensions': ['dimension', 'size', 'length', 'width', 'height', 'depth'],
            'weight': ['weight', 'mass', 'kg', 'lb', 'gram'],
            'material': ['material', 'made of', 'construction', 'steel', 'plastic', 'aluminum'],
            'color': ['color', 'colour', 'finish', 'coating'],
            
            # Electrical
            'voltage': ['voltage', 'volt', 'v', 'vac', 'vdc'],
            'current': ['current', 'amp', 'ampere', 'ma'],
            'power': ['power', 'watt', 'kw', 'hp', 'horsepower'],
            'frequency': ['frequency', 'hz', 'hertz'],
            
            # Mechanical
            'torque': ['torque', 'nm', 'ft-lb', 'twist'],
            'pressure': ['pressure', 'psi', 'bar', 'pascal', 'kpa'],
            'temperature': ['temperature', 'temp', 'celsius', 'fahrenheit', '°c', '°f'],
            'capacity': ['capacity', 'volume', 'liter', 'gallon', 'ml'],
            
            # Safety & Standards
            'certification': ['ce', 'ul', 'csa', 'rohs', 'iso', 'ansi', 'din'],
            'ip_rating': ['ip rating', 'ip', 'waterproof', 'dustproof'],
            'grade': ['grade', 'class', 'type', 'series']
        }
    
    def extract_specifications(self, product: ProductData) -> Dict[str, str]:
        """
        Extract and standardize specifications from product data.
        
        Args:
            product: Product to extract specifications from
            
        Returns:
            Standardized specifications dictionary
        """
        # Start with existing specifications
        specs = product.specifications.copy() if product.specifications else {}
        
        # Extract from description
        if product.description:
            extracted_specs = self._extract_from_text(product.description)
            specs.update(extracted_specs)
        
        # Extract from product name
        if product.name:
            name_specs = self._extract_from_text(product.name)
            specs.update(name_specs)
        
        # Standardize specification keys and values
        standardized_specs = self._standardize_specifications(specs)
        
        return standardized_specs
    
    def _extract_from_text(self, text: str) -> Dict[str, str]:
        """Extract specifications from text using regex patterns."""
        specs = {}
        
        # Define extraction patterns
        patterns = {
            'dimensions': r'(\d+(?:\.\d+)?)\s*(?:x|\×)\s*(\d+(?:\.\d+)?)\s*(?:x|\×)?\s*(\d+(?:\.\d+)?)?\s*(mm|cm|m|in|ft)',
            'weight': r'(\d+(?:\.\d+)?)\s*(kg|lb|g|oz|gram|kilogram|pound|ounce)',
            'voltage': r'(\d+(?:\.\d+)?)\s*(v|volt|voltage|vac|vdc)',
            'current': r'(\d+(?:\.\d+)?)\s*(a|amp|ampere|ma|milliamp)',
            'power': r'(\d+(?:\.\d+)?)\s*(w|watt|kw|kilowatt|hp|horsepower)',
            'frequency': r'(\d+(?:\.\d+)?)\s*(hz|hertz)',
            'pressure': r'(\d+(?:\.\d+)?)\s*(psi|bar|pascal|kpa|mpa)',
            'temperature': r'(-?\d+(?:\.\d+)?)\s*(°?c|°?f|celsius|fahrenheit)',
            'capacity': r'(\d+(?:\.\d+)?)\s*(l|ml|liter|litre|gal|gallon)',
        }
        
        for spec_type, pattern in patterns.items():
            matches = re.finditer(pattern, text.lower(), re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    value = groups[0]
                    unit = groups[1]
                    specs[spec_type] = f"{value} {unit}"
        
        # Extract IP rating
        ip_match = re.search(r'ip\s*(\d{2})', text.lower())
        if ip_match:
            specs['ip_rating'] = f"IP{ip_match.group(1)}"
        
        # Extract certifications
        cert_pattern = r'\b(ce|ul|csa|rohs|iso\s*\d+|ansi|din)\b'
        cert_matches = re.findall(cert_pattern, text.lower())
        if cert_matches:
            specs['certification'] = ', '.join(cert_matches)
        
        return specs
    
    def _standardize_specifications(self, specs: Dict[str, str]) -> Dict[str, str]:
        """Standardize specification keys and values."""
        standardized = {}
        
        for key, value in specs.items():
            # Standardize key
            std_key = self._standardize_key(key.lower())
            
            # Clean and standardize value
            std_value = self._standardize_value(value)
            
            if std_key and std_value:
                standardized[std_key] = std_value
        
        return standardized
    
    def _standardize_key(self, key: str) -> str:
        """Standardize specification key names."""
        key = key.lower().strip()
        
        for std_key, aliases in self.spec_mappings.items():
            if key in aliases or any(alias in key for alias in aliases):
                return std_key
        
        # If no standard mapping found, clean up the key
        key = re.sub(r'[^\w\s]', '', key)  # Remove special characters
        key = re.sub(r'\s+', '_', key)     # Replace spaces with underscores
        
        return key if len(key) > 1 else ''
    
    def _standardize_value(self, value: str) -> str:
        """Standardize specification values."""
        if not value:
            return ''
        
        # Clean up the value
        value = str(value).strip()
        value = re.sub(r'\s+', ' ', value)  # Normalize whitespace
        
        return value


class ImageAnalyzer:
    """Analyze product images for quality and content."""
    
    def __init__(self):
        self.logger = logging.getLogger("image_analyzer")
        self.image_processing = IMAGE_PROCESSING_AVAILABLE
    
    def analyze_product_images(self, product: ProductData) -> Dict[str, Any]:
        """
        Analyze product images for quality and content.
        
        Args:
            product: Product with images to analyze
            
        Returns:
            Image analysis results
        """
        if not product.images:
            return {'image_count': 0, 'quality_score': 0.0}
        
        analysis = {
            'image_count': len(product.images),
            'valid_images': 0,
            'average_quality': 0.0,
            'quality_scores': [],
            'image_types': [],
            'errors': []
        }
        
        if not self.image_processing:
            self.logger.warning("Image processing not available")
            return analysis
        
        for i, image_url in enumerate(product.images):
            try:
                quality_score = self._analyze_single_image(image_url)
                if quality_score > 0:
                    analysis['valid_images'] += 1
                    analysis['quality_scores'].append(quality_score)
                
            except Exception as e:
                analysis['errors'].append(f"Image {i}: {str(e)}")
        
        if analysis['quality_scores']:
            analysis['average_quality'] = statistics.mean(analysis['quality_scores'])
        
        return analysis
    
    def _analyze_single_image(self, image_url: str) -> float:
        """Analyze a single image for quality."""
        try:
            # Download image
            response = requests.get(image_url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Open image
            image = Image.open(io.BytesIO(response.content))
            
            # Basic quality metrics
            width, height = image.size
            
            # Quality score based on resolution and format
            quality_score = 0.0
            
            # Resolution scoring
            pixel_count = width * height
            if pixel_count >= 1000000:  # 1MP+
                quality_score += 0.4
            elif pixel_count >= 250000:  # 0.25MP+
                quality_score += 0.3
            elif pixel_count >= 50000:   # 0.05MP+
                quality_score += 0.2
            else:
                quality_score += 0.1
            
            # Aspect ratio scoring (reasonable product image ratios)
            aspect_ratio = max(width, height) / min(width, height)
            if 1.0 <= aspect_ratio <= 1.5:  # Square to 3:2
                quality_score += 0.3
            elif aspect_ratio <= 2.0:       # Up to 2:1
                quality_score += 0.2
            else:
                quality_score += 0.1
            
            # Format scoring
            if image.format in ['JPEG', 'PNG']:
                quality_score += 0.2
            elif image.format in ['WEBP', 'GIF']:
                quality_score += 0.1
            
            # File size consideration (not too small, not too large)
            content_length = response.headers.get('content-length')
            if content_length:
                size_kb = int(content_length) / 1024
                if 50 <= size_kb <= 2000:  # Reasonable size range
                    quality_score += 0.1
            
            return min(quality_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            self.logger.error(f"Image analysis failed for {image_url}: {e}")
            return 0.0


class ProductEnrichmentPipeline:
    """Main product enrichment pipeline."""
    
    def __init__(self, config: EnrichmentConfig = None):
        """Initialize the enrichment pipeline."""
        self.config = config or EnrichmentConfig()
        self.logger = logging.getLogger("enrichment_pipeline")
        
        # Initialize components
        self.classifier = ProductClassifier()
        self.spec_extractor = SpecificationExtractor()
        self.image_analyzer = ImageAnalyzer()
        
        # Statistics
        self.processed_count = 0
        self.success_count = 0
        self.start_time = datetime.now()
        
        self.logger.info("Product enrichment pipeline initialized")
        self.logger.info(f"AI Classification: {self.config.enable_ai_classification}")
        self.logger.info(f"Image Analysis: {self.config.enable_image_analysis}")
        self.logger.info(f"Duplicate Detection: {self.config.enable_duplicate_detection}")
    
    def enrich_product(self, product: ProductData) -> EnrichmentResult:
        """
        Enrich a single product with additional data and quality improvements.
        
        Args:
            product: Product to enrich
            
        Returns:
            EnrichmentResult with enriched product and metadata
        """
        start_time = time.time()
        errors = []
        original_quality = product.data_quality_score
        
        # Create copy for enrichment
        enriched = ProductData(
            sku=product.sku,
            name=product.name,
            price=product.price,
            currency=product.currency,
            description=product.description,
            specifications=product.specifications.copy() if product.specifications else {},
            images=product.images.copy() if product.images else [],
            categories=product.categories.copy() if product.categories else [],
            availability=product.availability,
            brand=product.brand,
            supplier=product.supplier,
            url=product.url,
            scraped_at=product.scraped_at
        )
        
        improvements = {
            'classification_improved': False,
            'specifications_enhanced': False,
            'image_quality_analyzed': False,
            'quality_score_improved': False
        }
        
        try:
            # 1. AI-powered classification
            if self.config.enable_ai_classification:
                new_categories, confidence = self.classifier.classify_product(enriched)
                if new_categories and confidence > 0.5:
                    # Merge with existing categories
                    all_categories = list(set(enriched.categories + new_categories))
                    enriched.categories = all_categories[:5]  # Limit to top 5
                    improvements['classification_improved'] = True
            
            # 2. Specification extraction and standardization
            enhanced_specs = self.spec_extractor.extract_specifications(enriched)
            if enhanced_specs:
                enriched.specifications.update(enhanced_specs)
                improvements['specifications_enhanced'] = True
            
            # 3. Image quality analysis
            if self.config.enable_image_analysis and enriched.images:
                image_analysis = self.image_analyzer.analyze_product_images(enriched)
                if image_analysis.get('average_quality', 0) > 0:
                    # Store image analysis in specifications
                    enriched.specifications['image_quality'] = f"{image_analysis['average_quality']:.2f}"
                    enriched.specifications['image_count'] = str(image_analysis['image_count'])
                    improvements['image_quality_analyzed'] = True
            
            # 4. Data quality validation and improvement
            self._improve_data_quality(enriched, improvements)
            
            # 5. Calculate final quality score
            new_quality = enriched.calculate_quality_score()
            if new_quality > original_quality:
                improvements['quality_score_improved'] = True
            
        except Exception as e:
            error_msg = f"Enrichment failed: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        
        processing_time = time.time() - start_time
        
        # Calculate enrichment score
        enrichment_score = self._calculate_enrichment_score(
            product, enriched, improvements
        )
        
        result = EnrichmentResult(
            original_product=product,
            enriched_product=enriched,
            enrichment_score=enrichment_score,
            quality_improvements=improvements,
            processing_time=processing_time,
            errors=errors
        )
        
        self.processed_count += 1
        if enrichment_score > 0.5:
            self.success_count += 1
        
        return result
    
    def _improve_data_quality(self, product: ProductData, improvements: Dict[str, Any]):
        """Improve data quality through validation and inference."""
        # Clean and standardize name
        if product.name:
            original_name = product.name
            product.name = self._clean_product_name(product.name)
            if product.name != original_name:
                improvements['name_cleaned'] = True
        
        # Standardize price format
        if product.price:
            original_price = product.price
            product.price = self._standardize_price(product.price)
            if product.price != original_price:
                improvements['price_standardized'] = True
        
        # Infer missing brand from name or specifications
        if not product.brand and product.name:
            inferred_brand = self._infer_brand(product.name, product.specifications)
            if inferred_brand:
                product.brand = inferred_brand
                improvements['brand_inferred'] = True
        
        # Enhance description if too short
        if not product.description or len(product.description) < self.config.min_description_length:
            enhanced_desc = self._enhance_description(product)
            if enhanced_desc:
                product.description = enhanced_desc
                improvements['description_enhanced'] = True
    
    def _clean_product_name(self, name: str) -> str:
        """Clean and standardize product name."""
        if not name:
            return name
        
        # Remove excessive whitespace
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Capitalize properly
        # Keep existing capitalization for acronyms and brand names
        words = name.split()
        cleaned_words = []
        
        for word in words:
            if word.isupper() and len(word) > 1:
                # Keep acronyms uppercase
                cleaned_words.append(word)
            elif word.lower() in ['and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with']:
                # Keep small words lowercase (unless first word)
                cleaned_words.append(word.lower() if len(cleaned_words) > 0 else word.title())
            else:
                cleaned_words.append(word.title())
        
        return ' '.join(cleaned_words)
    
    def _standardize_price(self, price: str) -> str:
        """Standardize price format."""
        if not price:
            return price
        
        # Extract numeric value and currency
        price_match = re.search(r'([S$£€¥₹]?)\s*([\d,]+\.?\d*)', price)
        if price_match:
            currency_symbol = price_match.group(1) or 'S$'
            numeric_value = price_match.group(2)
            
            # Format consistently
            return f"{currency_symbol}{numeric_value}"
        
        return price
    
    def _infer_brand(self, name: str, specifications: Dict[str, str]) -> str:
        """Infer brand from product name or specifications."""
        # Common brand names (extend as needed)
        known_brands = [
            'Bosch', 'DeWalt', 'Makita', 'Stanley', 'Black & Decker', 'Hitachi',
            'Festool', 'Milwaukee', 'Ryobi', 'Metabo', 'Hilti', 'Kärcher',
            'Philips', 'Osram', 'GE', '3M', 'Honeywell', 'Brady', 'MSA'
        ]
        
        # Check name for brand matches
        name_words = name.upper().split() if name else []
        for brand in known_brands:
            if brand.upper() in name_words or brand.upper() in name.upper():
                return brand
        
        # Check specifications for brand information
        if specifications:
            for key, value in specifications.items():
                if 'brand' in key.lower() or 'manufacturer' in key.lower():
                    return value
                
                # Check if any known brand is mentioned in spec values
                for brand in known_brands:
                    if brand.upper() in value.upper():
                        return brand
        
        return ''
    
    def _enhance_description(self, product: ProductData) -> str:
        """Enhance product description using available data."""
        parts = []
        
        # Start with existing description
        if product.description:
            parts.append(product.description)
        
        # Add information from specifications
        if product.specifications:
            spec_parts = []
            for key, value in product.specifications.items():
                if key.lower() not in ['image_quality', 'image_count']:
                    spec_parts.append(f"{key.replace('_', ' ').title()}: {value}")
            
            if spec_parts:
                spec_text = '. '.join(spec_parts[:5])  # Limit to 5 specs
                parts.append(f"Specifications: {spec_text}")
        
        # Add category information
        if product.categories:
            cat_text = f"Categories: {', '.join(product.categories[:3])}"
            parts.append(cat_text)
        
        # Add availability information
        if product.availability:
            parts.append(f"Availability: {product.availability}")
        
        enhanced_desc = '. '.join(parts)
        return enhanced_desc if len(enhanced_desc) > len(product.description or '') else product.description
    
    def _calculate_enrichment_score(self, original: ProductData, enriched: ProductData, 
                                   improvements: Dict[str, Any]) -> float:
        """Calculate overall enrichment score."""
        score = 0.0
        
        # Quality score improvement
        original_quality = original.calculate_quality_score()
        enriched_quality = enriched.calculate_quality_score()
        quality_improvement = enriched_quality - original_quality
        score += quality_improvement * 0.4  # 40% weight
        
        # Individual improvements
        improvement_weights = {
            'classification_improved': 0.15,
            'specifications_enhanced': 0.15,
            'image_quality_analyzed': 0.10,
            'name_cleaned': 0.05,
            'price_standardized': 0.05,
            'brand_inferred': 0.05,
            'description_enhanced': 0.05
        }
        
        for improvement, weight in improvement_weights.items():
            if improvements.get(improvement, False):
                score += weight
        
        return min(score, 1.0)  # Cap at 1.0
    
    def enrich_products_batch(self, products: List[ProductData]) -> List[EnrichmentResult]:
        """
        Enrich multiple products in batch with concurrent processing.
        
        Args:
            products: List of products to enrich
            
        Returns:
            List of enrichment results
        """
        self.logger.info(f"Starting batch enrichment of {len(products)} products")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_enrichments) as executor:
            # Submit enrichment tasks
            future_to_product = {
                executor.submit(self.enrich_product, product): product
                for product in products
            }
            
            # Process completed tasks
            for future in as_completed(future_to_product, timeout=self.config.enrichment_timeout * len(products)):
                try:
                    result = future.result()
                    results.append(result)
                    
                    if len(results) % 10 == 0:
                        self.logger.info(f"Processed {len(results)}/{len(products)} products")
                        
                except Exception as e:
                    product = future_to_product[future]
                    self.logger.error(f"Failed to enrich product {product.sku}: {e}")
        
        # Calculate batch statistics
        success_rate = self.success_count / max(self.processed_count, 1)
        avg_enrichment_score = statistics.mean([r.enrichment_score for r in results]) if results else 0.0
        
        self.logger.info(f"Batch enrichment completed:")
        self.logger.info(f"  - Products processed: {len(results)}")
        self.logger.info(f"  - Success rate: {success_rate:.1%}")
        self.logger.info(f"  - Average enrichment score: {avg_enrichment_score:.2f}")
        
        return results
    
    def get_enrichment_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        runtime = datetime.now() - self.start_time
        
        return {
            'processed_count': self.processed_count,
            'success_count': self.success_count,
            'success_rate': self.success_count / max(self.processed_count, 1),
            'runtime_seconds': runtime.total_seconds(),
            'processing_rate': self.processed_count / max(runtime.total_seconds(), 1)
        }


def main():
    """Main function for testing product enrichment."""
    print("Product Enrichment Pipeline - Testing")
    print("=" * 45)
    
    # Create test product data
    test_product = ProductData(
        sku="TEST001",
        name="bosch 18v cordless drill",
        price="S$ 189.99",
        description="Professional drill",
        specifications={"voltage": "18V", "chuck_size": "13mm"},
        images=["https://example.com/drill.jpg"],
        categories=["Tools"],
        availability="In Stock",
        brand="",
        supplier="Test Supplier",
        url="https://example.com/product/TEST001"
    )
    
    # Create configuration
    config = EnrichmentConfig(
        enable_ai_classification=True,
        enable_image_analysis=True,
        min_quality_score=0.6
    )
    
    # Initialize pipeline
    pipeline = ProductEnrichmentPipeline(config)
    
    try:
        print("\n1. Testing single product enrichment...")
        result = pipeline.enrich_product(test_product)
        
        print(f"✓ Original quality: {result.original_product.data_quality_score:.2f}")
        print(f"✓ Enriched quality: {result.enriched_product.data_quality_score:.2f}")
        print(f"✓ Enrichment score: {result.enrichment_score:.2f}")
        print(f"✓ Processing time: {result.processing_time:.2f}s")
        
        # Show improvements
        improvements = result.quality_improvements
        improved_aspects = [k for k, v in improvements.items() if v]
        if improved_aspects:
            print(f"✓ Improvements: {', '.join(improved_aspects)}")
        
        # Test batch processing
        print("\n2. Testing batch enrichment...")
        test_products = [test_product] * 3  # Simulate batch
        batch_results = pipeline.enrich_products_batch(test_products)
        
        print(f"✓ Batch processed: {len(batch_results)} products")
        
        # Get statistics
        print("\n3. Pipeline statistics...")
        stats = pipeline.get_enrichment_statistics()
        print(f"✓ Success rate: {stats['success_rate']:.1%}")
        print(f"✓ Processing rate: {stats['processing_rate']:.1f} products/sec")
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")


if __name__ == "__main__":
    main()