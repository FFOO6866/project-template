#!/usr/bin/env python3
"""
Simple Work-Based Recommendation Engine
A practical keyword-matching system for construction/DIY recommendations.
No AI/ML - just reliable keyword matching that actually works.
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class WorkCategory(Enum):
    """Common work categories for construction/DIY projects."""
    CEMENT_WORK = "cement_work"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    PAINTING = "painting"
    TILING = "tiling"
    CARPENTRY = "carpentry"
    FLOORING = "flooring"
    ROOFING = "roofing"
    INSULATION = "insulation"
    DEMOLITION = "demolition"
    PLASTERING = "plastering"
    WATERPROOFING = "waterproofing"


@dataclass
class Product:
    """Simple product representation."""
    sku: str
    name: str
    brand: str
    price: float
    description: str
    categories: List[str]
    work_categories: List[str]  # Mapped work categories
    keywords: List[str]  # Extracted keywords


@dataclass
class ToolSet:
    """Pre-defined tool set for a work category."""
    work_category: WorkCategory
    name: str
    essential_tools: List[str]
    optional_tools: List[str]
    safety_equipment: List[str]
    estimated_cost: float


@dataclass
class ProjectQuantity:
    """Quantity suggestions for common projects."""
    work_category: WorkCategory
    project_type: str
    unit: str  # e.g., "per room", "per m²", "per meter"
    quantities: Dict[str, float]  # product_type -> quantity


@dataclass
class WorkRecommendation:
    """Work-based recommendation result."""
    work_category: WorkCategory
    recommended_products: List[Product]
    tool_set: ToolSet
    quantity_guide: List[ProjectQuantity]
    total_estimated_cost: float
    confidence_score: float  # 0-1 based on keyword matching


class SimpleWorkRecommendationEngine:
    """Simple keyword-based recommendation engine for construction work."""
    
    def __init__(self):
        self.work_keywords = self._init_work_keywords()
        self.product_keywords = self._init_product_keywords()
        self.tool_sets = self._init_tool_sets()
        self.quantity_guides = self._init_quantity_guides()
        self.products: List[Product] = []
    
    def _init_work_keywords(self) -> Dict[WorkCategory, List[str]]:
        """Initialize keyword mappings for each work category."""
        return {
            WorkCategory.CEMENT_WORK: [
                "cement", "concrete", "mortar", "screed", "foundation", "slab",
                "render", "rendering", "block", "brick", "masonry", "aggregate", "sand",
                "grout", "repair", "crack", "waterproof", "seal", "driveway", "foundation",
                "structural", "mix", "ready", "portland", "exterior", "wall"
            ],
            WorkCategory.ELECTRICAL: [
                "electrical", "wire", "wiring", "rewiring", "cable", "switch", "socket", "outlet",
                "circuit", "breaker", "fuse", "conduit", "junction", "light", "lighting",
                "fan", "ceiling", "power", "voltage", "amp", "installation", "repair",
                "appliance", "kitchen", "bedroom", "house", "outlets"
            ],
            WorkCategory.PLUMBING: [
                "plumbing", "pipe", "fitting", "tap", "faucet", "toilet",
                "basin", "sink", "drain", "water", "sewage", "valve",
                "joint", "leak", "repair", "installation", "bathroom", "kitchen",
                "heater", "supply", "waste", "connecting", "connector"
            ],
            WorkCategory.PAINTING: [
                "paint", "painting", "primer", "brush", "roller", "spray",
                "wall", "ceiling", "color", "coating", "finish", "emulsion",
                "gloss", "matt", "exterior", "interior", "touch", "preparation",
                "living", "room", "house", "home", "walls"
            ],
            WorkCategory.TILING: [
                "tile", "tiling", "ceramic", "porcelain", "marble", "granite",
                "adhesive", "grout", "spacer", "cutter", "trim", "sealant",
                "floor", "flooring", "wall", "bathroom", "kitchen", "waterproof",
                "backsplash", "installation", "retile"
            ],
            WorkCategory.CARPENTRY: [
                "wood", "timber", "carpenter", "saw", "drill", "screw",
                "nail", "joint", "cabinet", "furniture", "door", "window",
                "frame", "shelf", "repair", "installation", "cutting", "sanding"
            ],
            WorkCategory.FLOORING: [
                "flooring", "floor", "laminate", "vinyl", "carpet", "parquet",
                "underlay", "installation", "repair", "skirting", "transition",
                "adhesive", "planks", "tiles", "boards", "new", "install", "makeover"
            ],
            WorkCategory.ROOFING: [
                "roof", "roofing", "tile", "sheet", "gutter", "downpipe",
                "flashing", "waterproof", "repair", "leak", "installation",
                "membrane", "insulation", "ventilation"
            ],
            WorkCategory.INSULATION: [
                "insulation", "insulate", "thermal", "sound", "foam",
                "fiberglass", "rockwool", "cavity", "loft", "wall",
                "ceiling", "energy", "saving", "installation"
            ],
            WorkCategory.DEMOLITION: [
                "demolition", "demolish", "break", "hammer", "chisel",
                "removal", "strip", "tear", "knock", "wall", "ceiling",
                "floor", "disposal", "debris"
            ],
            WorkCategory.PLASTERING: [
                "plaster", "plastering", "render", "rendering", "skim", "smooth",
                "wall", "ceiling", "repair", "crack", "hole", "finish",
                "compound", "filler", "preparation", "exterior", "concrete"
            ],
            WorkCategory.WATERPROOFING: [
                "waterproof", "waterproofing", "seal", "membrane", "coating",
                "damp", "moisture", "leak", "protection", "barrier",
                "roof", "basement", "bathroom", "balcony", "before", "installing"
            ]
        }
    
    def _init_product_keywords(self) -> Dict[str, List[str]]:
        """Initialize product type keywords for categorization."""
        return {
            "tools_power": [
                "drill", "saw", "grinder", "sander", "router", "planer",
                "impact", "cordless", "electric", "battery", "motor"
            ],
            "tools_hand": [
                "hammer", "screwdriver", "pliers", "wrench", "chisel",
                "file", "plane", "square", "level", "tape", "ruler"
            ],
            "materials_cement": [
                "cement", "concrete", "mortar", "aggregate", "sand",
                "gravel", "admixture", "accelerator", "retardant"
            ],
            "materials_electrical": [
                "cable", "wire", "conduit", "switch", "socket", "breaker",
                "fuse", "junction", "connector", "terminal"
            ],
            "materials_plumbing": [
                "pipe", "fitting", "valve", "joint", "elbow", "tee",
                "reducer", "coupling", "adapter", "seal"
            ],
            "materials_paint": [
                "paint", "primer", "undercoat", "emulsion", "gloss",
                "matt", "satin", "thinner", "solvent"
            ],
            "materials_tile": [
                "tile", "ceramic", "porcelain", "marble", "granite",
                "adhesive", "grout", "spacer", "trim", "edge"
            ],
            "safety_equipment": [
                "helmet", "goggles", "gloves", "mask", "respirator",
                "harness", "boots", "vest", "protection", "safety"
            ]
        }
    
    def _init_tool_sets(self) -> Dict[WorkCategory, ToolSet]:
        """Initialize pre-defined tool sets for each work category."""
        return {
            WorkCategory.CEMENT_WORK: ToolSet(
                work_category=WorkCategory.CEMENT_WORK,
                name="Cement Work Tool Set",
                essential_tools=[
                    "mixing_paddle", "bucket", "trowel", "float", "level",
                    "measuring_tape", "shovel", "wheelbarrow"
                ],
                optional_tools=[
                    "concrete_mixer", "vibrator", "screed_board", "jointer"
                ],
                safety_equipment=[
                    "safety_goggles", "dust_mask", "gloves", "steel_toe_boots"
                ],
                estimated_cost=450.0
            ),
            WorkCategory.ELECTRICAL: ToolSet(
                work_category=WorkCategory.ELECTRICAL,
                name="Electrical Work Tool Set",
                essential_tools=[
                    "wire_stripper", "electrical_tester", "screwdriver_set",
                    "pliers", "cable_cutter", "multimeter"
                ],
                optional_tools=[
                    "fish_tape", "conduit_bender", "cable_puller", "junction_box"
                ],
                safety_equipment=[
                    "insulated_gloves", "safety_goggles", "non_conductive_shoes"
                ],
                estimated_cost=320.0
            ),
            WorkCategory.PLUMBING: ToolSet(
                work_category=WorkCategory.PLUMBING,
                name="Plumbing Tool Set",
                essential_tools=[
                    "pipe_wrench", "adjustable_wrench", "pipe_cutter",
                    "plunger", "snake", "level", "measuring_tape"
                ],
                optional_tools=[
                    "pipe_threading_machine", "soldering_iron", "pressure_tester"
                ],
                safety_equipment=[
                    "safety_goggles", "gloves", "knee_pads"
                ],
                estimated_cost=280.0
            ),
            WorkCategory.PAINTING: ToolSet(
                work_category=WorkCategory.PAINTING,
                name="Painting Tool Set",
                essential_tools=[
                    "brushes", "rollers", "paint_tray", "ladder", "drop_cloths",
                    "sandpaper", "scraper", "tape"
                ],
                optional_tools=[
                    "spray_gun", "airless_sprayer", "texture_roller"
                ],
                safety_equipment=[
                    "dust_mask", "safety_goggles", "gloves"
                ],
                estimated_cost=180.0
            ),
            WorkCategory.TILING: ToolSet(
                work_category=WorkCategory.TILING,
                name="Tiling Tool Set",
                essential_tools=[
                    "tile_cutter", "notched_trowel", "rubber_float",
                    "sponge", "level", "spacers", "measuring_tape"
                ],
                optional_tools=[
                    "wet_saw", "angle_grinder", "hole_saw", "trim_cutter"
                ],
                safety_equipment=[
                    "safety_goggles", "dust_mask", "knee_pads", "gloves"
                ],
                estimated_cost=380.0
            ),
            WorkCategory.CARPENTRY: ToolSet(
                work_category=WorkCategory.CARPENTRY,
                name="Carpentry Tool Set",
                essential_tools=[
                    "circular_saw", "drill", "hammer", "chisels", "square",
                    "level", "measuring_tape", "clamps"
                ],
                optional_tools=[
                    "router", "planer", "biscuit_joiner", "miter_saw"
                ],
                safety_equipment=[
                    "safety_goggles", "hearing_protection", "dust_mask", "gloves"
                ],
                estimated_cost=520.0
            ),
            WorkCategory.FLOORING: ToolSet(
                work_category=WorkCategory.FLOORING,
                name="Flooring Tool Set",
                essential_tools=[
                    "saw", "drill", "hammer", "tapping_block", "spacers",
                    "level", "measuring_tape", "knee_pads"
                ],
                optional_tools=[
                    "floor_nailer", "miter_saw", "router", "moisture_meter"
                ],
                safety_equipment=[
                    "safety_goggles", "dust_mask", "knee_pads", "gloves"
                ],
                estimated_cost=420.0
            ),
            WorkCategory.ROOFING: ToolSet(
                work_category=WorkCategory.ROOFING,
                name="Roofing Tool Set",
                essential_tools=[
                    "hammer", "nail_gun", "ladder", "measuring_tape", "chalk_line",
                    "utility_knife", "roofing_nailer", "safety_harness"
                ],
                optional_tools=[
                    "power_saw", "angle_grinder", "roofing_hatchet", "ridge_vent_tool"
                ],
                safety_equipment=[
                    "safety_harness", "helmet", "non_slip_boots", "gloves"
                ],
                estimated_cost=650.0
            ),
            WorkCategory.INSULATION: ToolSet(
                work_category=WorkCategory.INSULATION,
                name="Insulation Tool Set",
                essential_tools=[
                    "utility_knife", "measuring_tape", "staple_gun", "protective_clothing",
                    "ladder", "dust_mask", "goggles"
                ],
                optional_tools=[
                    "insulation_blower", "vapor_barrier_tool", "thermal_imager"
                ],
                safety_equipment=[
                    "dust_mask", "goggles", "protective_clothing", "gloves"
                ],
                estimated_cost=280.0
            ),
            WorkCategory.DEMOLITION: ToolSet(
                work_category=WorkCategory.DEMOLITION,
                name="Demolition Tool Set",
                essential_tools=[
                    "sledge_hammer", "crowbar", "reciprocating_saw", "dust_mask",
                    "safety_goggles", "debris_bags", "shovel"
                ],
                optional_tools=[
                    "jackhammer", "angle_grinder", "concrete_breaker", "dumpster"
                ],
                safety_equipment=[
                    "hard_hat", "safety_goggles", "dust_mask", "steel_toe_boots", "gloves"
                ],
                estimated_cost=480.0
            ),
            WorkCategory.PLASTERING: ToolSet(
                work_category=WorkCategory.PLASTERING,
                name="Plastering Tool Set",
                essential_tools=[
                    "hawk", "trowel", "float", "mixing_paddle", "bucket",
                    "spray_bottle", "sanding_block"
                ],
                optional_tools=[
                    "plastering_machine", "corner_bead_tool", "texture_roller"
                ],
                safety_equipment=[
                    "dust_mask", "safety_goggles", "gloves"
                ],
                estimated_cost=320.0
            ),
            WorkCategory.WATERPROOFING: ToolSet(
                work_category=WorkCategory.WATERPROOFING,
                name="Waterproofing Tool Set",
                essential_tools=[
                    "brush", "roller", "trowel", "mixing_paddle", "bucket",
                    "sealing_gun", "measuring_tape"
                ],
                optional_tools=[
                    "pressure_washer", "moisture_meter", "infrared_thermometer"
                ],
                safety_equipment=[
                    "gloves", "safety_goggles", "respirator", "protective_clothing"
                ],
                estimated_cost=380.0
            )
        }
    
    def _init_quantity_guides(self) -> Dict[WorkCategory, List[ProjectQuantity]]:
        """Initialize quantity guides for common projects."""
        return {
            WorkCategory.CEMENT_WORK: [
                ProjectQuantity(
                    work_category=WorkCategory.CEMENT_WORK,
                    project_type="concrete_slab",
                    unit="per m²",
                    quantities={
                        "cement_bags": 0.4,
                        "sand_bags": 1.2,
                        "aggregate_bags": 2.0,
                        "reinforcement_mesh": 1.1
                    }
                ),
                ProjectQuantity(
                    work_category=WorkCategory.CEMENT_WORK,
                    project_type="wall_render",
                    unit="per m²",
                    quantities={
                        "cement_bags": 0.2,
                        "sand_bags": 0.6,
                        "water": 15.0  # liters
                    }
                )
            ],
            WorkCategory.ELECTRICAL: [
                ProjectQuantity(
                    work_category=WorkCategory.ELECTRICAL,
                    project_type="room_wiring",
                    unit="per room",
                    quantities={
                        "cable_2.5mm": 50.0,  # meters
                        "cable_1.5mm": 30.0,  # meters
                        "sockets": 6.0,
                        "switches": 3.0,
                        "junction_boxes": 4.0
                    }
                )
            ],
            WorkCategory.PLUMBING: [
                ProjectQuantity(
                    work_category=WorkCategory.PLUMBING,
                    project_type="bathroom_plumbing",
                    unit="per bathroom",
                    quantities={
                        "pipe_15mm": 10.0,  # meters
                        "pipe_22mm": 5.0,   # meters
                        "elbows": 8.0,
                        "tees": 4.0,
                        "valves": 3.0
                    }
                )
            ],
            WorkCategory.PAINTING: [
                ProjectQuantity(
                    work_category=WorkCategory.PAINTING,
                    project_type="room_painting",
                    unit="per room",
                    quantities={
                        "primer_liters": 2.0,
                        "paint_liters": 4.0,
                        "brushes": 2.0,
                        "rollers": 3.0,
                        "sandpaper_sheets": 10.0
                    }
                )
            ],
            WorkCategory.TILING: [
                ProjectQuantity(
                    work_category=WorkCategory.TILING,
                    project_type="floor_tiling",
                    unit="per m²",
                    quantities={
                        "tiles": 1.1,  # 10% extra
                        "adhesive_kg": 3.0,
                        "grout_kg": 0.5,
                        "spacers": 20.0
                    }
                )
            ]
        }
    
    def load_products_from_json(self, file_path: str) -> None:
        """Load products from JSON file and categorize them."""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    # Single product JSON
                    data = json.load(f)
                    if isinstance(data, dict):
                        product = self._parse_product(data)
                        if product:
                            self.products.append(product)
                    elif isinstance(data, list):
                        for item in data:
                            product = self._parse_product(item)
                            if product:
                                self.products.append(product)
        except Exception as e:
            print(f"Error loading products from {file_path}: {e}")
    
    def _parse_product(self, data: Dict) -> Optional[Product]:
        """Parse product data and categorize it."""
        try:
            # Extract basic info
            sku = data.get('sku', '')
            name = data.get('name', '')
            brand = data.get('brand', '')
            
            # Parse price
            price_str = data.get('price', '0')
            if isinstance(price_str, str):
                price = float(re.sub(r'[^\d.]', '', price_str))
            else:
                price = float(price_str)
            
            description = data.get('description', '')
            categories = data.get('categories', [])
            
            # Extract keywords from name, description, and categories
            keywords = self._extract_keywords(name, description, categories)
            
            # Map to work categories
            work_categories = self._map_to_work_categories(keywords)
            
            return Product(
                sku=sku,
                name=name,
                brand=brand,
                price=price,
                description=description,
                categories=categories,
                work_categories=work_categories,
                keywords=keywords
            )
        except Exception as e:
            print(f"Error parsing product: {e}")
            return None
    
    def _extract_keywords(self, name: str, description: str, categories: List[str]) -> List[str]:
        """Extract keywords from product information."""
        text = f"{name} {description} {' '.join(categories)}".lower()
        
        # Clean and split text
        words = re.findall(r'\b[a-z]{3,}\b', text)
        
        # Remove common stop words
        stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'are', 'you', 'can', 'use'}
        keywords = [word for word in words if word not in stop_words]
        
        return list(set(keywords))  # Remove duplicates
    
    def _map_to_work_categories(self, keywords: List[str]) -> List[str]:
        """Map product keywords to work categories."""
        work_categories = []
        
        for work_category, work_keywords in self.work_keywords.items():
            # Calculate match score
            matches = sum(1 for keyword in keywords if keyword in work_keywords)
            
            # If we have multiple keyword matches, include this work category
            if matches >= 2:
                work_categories.append(work_category.value)
            # Single strong match for very specific keywords
            elif matches >= 1 and any(keyword in ['cement', 'electrical', 'plumbing', 'paint', 'tile'] 
                                    for keyword in keywords):
                work_categories.append(work_category.value)
        
        return work_categories
    
    def classify_work_query(self, query: str) -> Tuple[Optional[WorkCategory], float]:
        """Classify user query into work category with confidence score."""
        query_lower = query.lower()
        query_keywords = re.findall(r'\b[a-z]{2,}\b', query_lower)  # Include 2-letter words
        
        category_scores = {}
        
        for work_category, work_keywords in self.work_keywords.items():
            score = 0.0
            matches = 0
            
            # Direct keyword matches (highest weight)
            for keyword in query_keywords:
                if keyword in work_keywords:
                    score += 3.0
                    matches += 1
            
            # Partial matches (medium weight)
            for keyword in query_keywords:
                for work_keyword in work_keywords:
                    if len(keyword) >= 4 and len(work_keyword) >= 4:
                        if work_keyword in keyword or keyword in work_keyword:
                            score += 1.5
                            matches += 0.5
            
            # Multi-word phrase matching (special cases)
            query_text = ' ' + query_lower + ' '
            for work_keyword in work_keywords:
                if len(work_keyword) >= 4 and work_keyword in query_text:
                    score += 2.0
                    matches += 1
            
            # Normalize score by category keyword count but boost absolute matches
            if matches > 0:
                normalized_score = (score / len(work_keywords)) + (matches * 0.1)
                category_scores[work_category] = (normalized_score, matches)
        
        if not category_scores:
            return None, 0.0
        
        # Find best category with highest score, then by most matches
        best_category = max(category_scores.keys(), 
                          key=lambda cat: (category_scores[cat][0], category_scores[cat][1]))
        best_score = category_scores[best_category][0]
        
        return best_category, min(best_score, 1.0)  # Cap at 1.0
    
    def get_work_recommendations(self, work_category: WorkCategory, limit: int = 20) -> WorkRecommendation:
        """Get recommendations for a specific work category."""
        # Find relevant products
        relevant_products = [
            product for product in self.products
            if work_category.value in product.work_categories
        ]
        
        # Sort by relevance (number of matching keywords)
        def relevance_score(product):
            work_keywords = self.work_keywords[work_category]
            return sum(1 for keyword in product.keywords if keyword in work_keywords)
        
        relevant_products.sort(key=relevance_score, reverse=True)
        recommended_products = relevant_products[:limit]
        
        # Get tool set
        tool_set = self.tool_sets.get(work_category, ToolSet(
            work_category=work_category,
            name=f"{work_category.value.title()} Tools",
            essential_tools=[],
            optional_tools=[],
            safety_equipment=[],
            estimated_cost=0.0
        ))
        
        # Get quantity guides
        quantity_guides = self.quantity_guides.get(work_category, [])
        
        # Calculate total estimated cost
        product_cost = sum(product.price for product in recommended_products[:10])  # Top 10
        total_cost = product_cost + tool_set.estimated_cost
        
        # Calculate confidence based on number of relevant products found
        confidence = min(len(recommended_products) / 10.0, 1.0)
        
        return WorkRecommendation(
            work_category=work_category,
            recommended_products=recommended_products,
            tool_set=tool_set,
            quantity_guide=quantity_guides,
            total_estimated_cost=total_cost,
            confidence_score=confidence
        )
    
    def get_recommendations_by_query(self, query: str) -> Optional[WorkRecommendation]:
        """Get recommendations based on user query."""
        work_category, confidence = self.classify_work_query(query)
        
        if work_category and confidence > 0.1:  # Minimum confidence threshold
            recommendation = self.get_work_recommendations(work_category)
            # Adjust confidence based on query classification confidence
            recommendation.confidence_score *= confidence
            return recommendation
        
        return None
    
    def get_available_work_categories(self) -> List[str]:
        """Get list of available work categories."""
        return [category.value for category in WorkCategory]
    
    def get_products_by_work_category(self, work_category: str) -> List[Product]:
        """Get all products for a specific work category."""
        return [
            product for product in self.products
            if work_category in product.work_categories
        ]


def create_sample_products() -> List[Dict]:
    """Create sample product data for testing."""
    return [
        {
            "sku": "CEMENT-001",
            "name": "Portland Cement 40kg",
            "brand": "Universal",
            "price": "S$12.50",
            "description": "High quality Portland cement for concrete and mortar mixing",
            "categories": ["Building Materials", "Cement", "Concrete"]
        },
        {
            "sku": "DRILL-001", 
            "name": "Cordless Drill 18V",
            "brand": "Bosch",
            "price": "S$189.99",
            "description": "Professional cordless drill for electrical and carpentry work",
            "categories": ["Power Tools", "Drills", "Electrical Tools"]
        },
        {
            "sku": "PIPE-001",
            "name": "PVC Pipe 22mm x 3m",
            "brand": "Wavin",
            "price": "S$8.90",
            "description": "PVC pipe for plumbing water supply systems",
            "categories": ["Plumbing", "Pipes", "Water Systems"]
        },
        {
            "sku": "PAINT-001",
            "name": "Interior Wall Paint 5L White",
            "brand": "Nippon",
            "price": "S$45.00",
            "description": "Premium interior emulsion paint for walls and ceilings",
            "categories": ["Paint", "Interior", "Wall Paint"]
        },
        {
            "sku": "TILE-001",
            "name": "Ceramic Floor Tile 600x600mm",
            "brand": "Johnson",
            "price": "S$15.50",
            "description": "Ceramic floor tiles for bathroom and kitchen flooring",
            "categories": ["Tiles", "Flooring", "Ceramic"]
        },
        {
            "sku": "WIRE-001",
            "name": "Electrical Cable 2.5mm² 100m",
            "brand": "Prysmian",
            "price": "S$85.00",
            "description": "Electrical cable for house wiring and electrical installations",
            "categories": ["Electrical", "Cables", "Wiring"]
        }
    ]


if __name__ == "__main__":
    # Test the recommendation engine
    engine = SimpleWorkRecommendationEngine()
    
    # Create sample products
    sample_products = create_sample_products()
    
    # Add sample products to engine
    for product_data in sample_products:
        product = engine._parse_product(product_data)
        if product:
            engine.products.append(product)
    
    print("Simple Work Recommendation Engine Test")
    print("=" * 50)
    
    # Test work category classification
    test_queries = [
        "I need to do cement work for my driveway",
        "Electrical wiring for new room",
        "Plumbing repair for kitchen sink",
        "Paint the living room walls",
        "Install ceramic tiles in bathroom"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        recommendation = engine.get_recommendations_by_query(query)
        
        if recommendation:
            print(f"Work Category: {recommendation.work_category.value}")
            print(f"Confidence: {recommendation.confidence_score:.2f}")
            print(f"Products Found: {len(recommendation.recommended_products)}")
            print(f"Tool Set: {recommendation.tool_set.name}")
            print(f"Essential Tools: {len(recommendation.tool_set.essential_tools)}")
            print(f"Total Cost Estimate: S${recommendation.total_estimated_cost:.2f}")
            
            # Show top 3 products
            if recommendation.recommended_products:
                print("Top Products:")
                for i, product in enumerate(recommendation.recommended_products[:3], 1):
                    print(f"  {i}. {product.name} - S${product.price:.2f}")
        else:
            print("No recommendations found")
    
    print(f"\nAvailable Work Categories: {len(engine.get_available_work_categories())}")
    print(f"Total Products Loaded: {len(engine.products)}")