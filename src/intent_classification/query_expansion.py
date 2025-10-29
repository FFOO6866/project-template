"""
Query expansion and synonym handling system for DIY intent classification.
Improves classification accuracy by expanding queries with synonyms and related terms.
"""

import json
import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExpandedQuery:
    """Expanded query with synonyms and related terms"""
    original_query: str
    expanded_query: str
    expansion_terms: List[str]
    confidence_boost: float


class DIYQueryExpander:
    """Query expansion system for DIY classification"""
    
    def __init__(self):
        self._initialize_synonym_dictionaries()
        self._initialize_contextual_expansions()
        self._initialize_singapore_specific_terms()
        
    def _initialize_synonym_dictionaries(self):
        """Initialize comprehensive synonym dictionaries"""
        
        # Action synonyms
        self.action_synonyms = {
            "fix": ["repair", "mend", "restore", "troubleshoot", "solve", "resolve"],
            "install": ["mount", "set up", "put in", "attach", "place", "position"],
            "build": ["construct", "create", "make", "assemble", "fabricate"],
            "renovate": ["remodel", "upgrade", "improve", "refurbish", "modernize"],
            "replace": ["substitute", "swap", "change", "switch", "exchange"],
            "remove": ["take out", "extract", "uninstall", "detach", "dismantle"],
            "clean": ["wash", "scrub", "sanitize", "maintain", "service"],
            "paint": ["color", "coat", "finish", "decorate", "apply paint"],
            "cut": ["slice", "trim", "saw", "chop", "divide"],
            "drill": ["bore", "pierce", "make holes", "perforate"]
        }
        
        # Tool synonyms
        self.tool_synonyms = {
            "drill": ["boring machine", "power drill", "cordless drill", "hammer drill"],
            "saw": ["cutting tool", "handsaw", "circular saw", "jigsaw", "chainsaw"],
            "hammer": ["mallet", "sledgehammer", "claw hammer", "ball peen hammer"],
            "screwdriver": ["driver", "phillips head", "flathead", "torx driver"],
            "pliers": ["grippers", "needle nose", "wire cutters", "locking pliers"],
            "wrench": ["spanner", "adjustable wrench", "socket wrench", "allen wrench"],
            "level": ["spirit level", "bubble level", "laser level"],
            "tape measure": ["measuring tape", "ruler", "measuring device"],
            "sandpaper": ["abrasive", "sanding disc", "emery paper"],
            "router": ["wood router", "trim router", "plunge router"]
        }
        
        # Material synonyms
        self.material_synonyms = {
            "wood": ["timber", "lumber", "hardwood", "softwood", "plywood", "mdf"],
            "metal": ["steel", "aluminum", "iron", "brass", "copper", "alloy"],
            "plastic": ["polymer", "pvc", "acrylic", "polycarbonate", "vinyl"],
            "concrete": ["cement", "masonry", "mortar", "grout"],
            "glass": ["glazing", "tempered glass", "safety glass", "window pane"],
            "tile": ["ceramic", "porcelain", "stone tile", "floor tile", "wall tile"],
            "fabric": ["cloth", "textile", "upholstery", "canvas"],
            "rubber": ["latex", "silicone", "elastomer"],
            "stone": ["rock", "granite", "marble", "limestone", "slate"]
        }
        
        # Problem synonyms
        self.problem_synonyms = {
            "leak": ["drip", "seepage", "water damage", "moisture", "wet"],
            "crack": ["split", "fracture", "break", "fissure", "damage"],
            "stuck": ["jammed", "frozen", "seized", "locked", "immobile"],
            "loose": ["wobbly", "unstable", "slack", "detached", "coming apart"],
            "noisy": ["squeaky", "rattling", "creaking", "grinding", "loud"],
            "broken": ["damaged", "faulty", "defective", "not working", "out of order"],
            "clogged": ["blocked", "plugged", "obstructed", "backed up"],
            "worn": ["deteriorated", "aged", "weathered", "faded", "old"]
        }
        
        # Room synonyms
        self.room_synonyms = {
            "bathroom": ["toilet", "washroom", "shower room", "powder room", "lavatory"],
            "kitchen": ["cooking area", "galley", "kitchenette", "food prep area"],
            "bedroom": ["sleeping area", "master bedroom", "guest room", "chamber"],
            "living room": ["lounge", "sitting room", "family room", "great room"],
            "dining room": ["dining area", "eating area", "breakfast nook"],
            "study": ["office", "den", "library", "work room", "home office"],
            "garage": ["car port", "workshop", "storage area"],
            "basement": ["cellar", "lower level", "underground room"],
            "attic": ["loft", "upper level", "roof space"]
        }
        
        # Skill level synonyms
        self.skill_synonyms = {
            "beginner": ["newbie", "novice", "first time", "new to", "amateur", "starter"],
            "intermediate": ["moderate", "some experience", "decent", "okay with", "fair"],
            "advanced": ["expert", "professional", "skilled", "experienced", "pro", "master"],
            "easy": ["simple", "basic", "straightforward", "uncomplicated"],
            "difficult": ["hard", "complex", "challenging", "complicated", "tough"],
            "quick": ["fast", "rapid", "speedy", "swift"],
            "slow": ["careful", "methodical", "detailed", "thorough"]
        }
        
        # Brand synonyms and variations
        self.brand_synonyms = {
            "dewalt": ["de walt", "d walt", "yellow tools"],
            "makita": ["teal tools", "blue tools"],
            "bosch": ["blue professional", "green diy"],
            "black & decker": ["black and decker", "b&d", "orange tools"],
            "milwaukee": ["red tools", "m18", "fuel"],
            "ryobi": ["green tools", "one+"],
            "festool": ["green professional", "systainer"],
            "stanley": ["yellow tape", "fatmax"],
            "craftsman": ["red tools", "versastack"]
        }
    
    def _initialize_contextual_expansions(self):
        """Initialize context-based expansions"""
        
        # Intent-specific expansions
        self.intent_expansions = {
            "project_planning": {
                "triggers": ["want to", "planning", "thinking of", "considering"],
                "expansions": ["step by step", "guide", "how to plan", "what do I need"]
            },
            "problem_solving": {
                "triggers": ["broken", "not working", "problem", "issue"],
                "expansions": ["how to fix", "repair guide", "troubleshoot", "solution"]
            },
            "tool_selection": {
                "triggers": ["best", "recommend", "which", "what tool"],
                "expansions": ["comparison", "review", "buying guide", "tool for"]
            },
            "product_comparison": {
                "triggers": ["vs", "versus", "compare", "better"],
                "expansions": ["pros and cons", "review", "which is better", "difference"]
            },
            "learning": {
                "triggers": ["how to", "learn", "tutorial", "teach me"],
                "expansions": ["step by step", "guide", "instructions", "beginner"]
            }
        }
        
        # Contextual word associations
        self.contextual_associations = {
            "bathroom": ["plumbing", "water", "tile", "ventilation", "moisture"],
            "kitchen": ["cabinet", "countertop", "appliance", "plumbing", "electrical"],
            "electrical": ["wire", "outlet", "switch", "circuit", "safety", "voltage"],
            "plumbing": ["pipe", "water", "pressure", "leak", "drain", "faucet"],
            "flooring": ["level", "subfloor", "underlayment", "transition", "threshold"],
            "painting": ["primer", "brush", "roller", "surface prep", "ventilation"],
            "insulation": ["r-value", "vapor barrier", "thermal", "energy efficiency"],
            "roofing": ["shingle", "gutter", "flashing", "leak", "weather protection"]
        }
    
    def _initialize_singapore_specific_terms(self):
        """Initialize Singapore-specific term expansions"""
        
        self.singapore_expansions = {
            "hdb": ["public housing", "government flat", "bto", "resale flat", "rental flat"],
            "condo": ["condominium", "private apartment", "high-rise", "facilities"],
            "landed": ["terrace house", "semi-detached", "bungalow", "shophouse"],
            "void deck": ["ground floor", "common area", "multi-purpose hall"],
            "aircon": ["air conditioning", "cooling", "hvac", "split unit"],
            "town council": ["estate management", "hdb management", "maintenance"],
            "tropical": ["humid", "hot weather", "monsoon", "high humidity"],
            "renovation permit": ["hdb approval", "guidelines", "regulations"],
            "contractor": ["renovation company", "handyman", "worker", "tradesman"],
            "wet area": ["bathroom", "kitchen", "balcony", "water area"]
        }
        
        # Local measurement units
        self.measurement_expansions = {
            "sqft": ["square feet", "sq ft", "square foot"],
            "sqm": ["square meter", "sq m", "square metre"],
            "psi": ["pounds per square inch", "water pressure"],
            "amp": ["ampere", "electrical current", "circuit rating"]
        }
        
        # Local regulations and standards
        self.regulation_expansions = {
            "fire safety": ["scdf", "fire department", "safety code", "sprinkler"],
            "building code": ["ura", "bca", "regulations", "compliance"],
            "electrical": ["sp services", "electrical code", "safety switch"],
            "water": ["pub", "water pressure", "pipe sizing", "conservation"]
        }
    
    def expand_query(self, query: str, intent_hint: Optional[str] = None) -> ExpandedQuery:
        """Expand a query with synonyms and related terms"""
        original_query = query.strip()
        expanded_terms = []
        confidence_boost = 0.0
        
        # Start with original query
        expanded_query = original_query.lower()
        
        # Apply synonym expansions
        expanded_query, synonym_terms = self._apply_synonyms(expanded_query)
        expanded_terms.extend(synonym_terms)
        
        # Apply contextual expansions
        if intent_hint:
            expanded_query, context_terms = self._apply_contextual_expansions(
                expanded_query, intent_hint
            )
            expanded_terms.extend(context_terms)
        
        # Apply Singapore-specific expansions
        expanded_query, sg_terms = self._apply_singapore_expansions(expanded_query)
        expanded_terms.extend(sg_terms)
        
        # Apply technical term expansions
        expanded_query, tech_terms = self._apply_technical_expansions(expanded_query)
        expanded_terms.extend(tech_terms)
        
        # Calculate confidence boost based on number of expansions
        confidence_boost = min(len(expanded_terms) * 0.05, 0.3)
        
        return ExpandedQuery(
            original_query=original_query,
            expanded_query=expanded_query,
            expansion_terms=list(set(expanded_terms)),  # Remove duplicates
            confidence_boost=confidence_boost
        )
    
    def _apply_synonyms(self, query: str) -> Tuple[str, List[str]]:
        """Apply synonym expansions to query"""
        expanded_terms = []
        expanded_query = query
        
        # Combine all synonym dictionaries
        all_synonyms = {}
        for synonym_dict in [self.action_synonyms, self.tool_synonyms, 
                           self.material_synonyms, self.problem_synonyms,
                           self.room_synonyms, self.skill_synonyms, self.brand_synonyms]:
            all_synonyms.update(synonym_dict)
        
        # Find and expand synonyms
        for base_term, synonyms in all_synonyms.items():
            # Check if base term is in query
            if base_term in query:
                # Add synonyms to expanded query
                synonym_additions = " ".join(synonyms[:3])  # Limit to top 3 synonyms
                expanded_query += f" {synonym_additions}"
                expanded_terms.extend(synonyms[:3])
            
            # Check if any synonyms are in query (reverse lookup)
            for synonym in synonyms:
                if synonym in query and base_term not in expanded_query:
                    expanded_query += f" {base_term}"
                    expanded_terms.append(base_term)
                    break
        
        return expanded_query, expanded_terms
    
    def _apply_contextual_expansions(self, query: str, intent: str) -> Tuple[str, List[str]]:
        """Apply intent-specific contextual expansions"""
        expanded_terms = []
        expanded_query = query
        
        # Apply intent-specific expansions
        if intent in self.intent_expansions:
            intent_config = self.intent_expansions[intent]
            
            # Check if any triggers are present
            for trigger in intent_config["triggers"]:
                if trigger in query:
                    # Add expansions
                    expansions = " ".join(intent_config["expansions"])
                    expanded_query += f" {expansions}"
                    expanded_terms.extend(intent_config["expansions"])
                    break
        
        # Apply contextual associations
        for context, associations in self.contextual_associations.items():
            if context in query:
                # Add related terms
                association_terms = " ".join(associations[:3])
                expanded_query += f" {association_terms}"
                expanded_terms.extend(associations[:3])
        
        return expanded_query, expanded_terms
    
    def _apply_singapore_expansions(self, query: str) -> Tuple[str, List[str]]:
        """Apply Singapore-specific expansions"""
        expanded_terms = []
        expanded_query = query
        
        # Apply Singapore-specific expansions
        for sg_term, expansions in self.singapore_expansions.items():
            if sg_term in query:
                expansion_text = " ".join(expansions[:3])
                expanded_query += f" {expansion_text}"
                expanded_terms.extend(expansions[:3])
        
        # Apply measurement expansions
        for measurement, expansions in self.measurement_expansions.items():
            if measurement in query:
                expansion_text = " ".join(expansions)
                expanded_query += f" {expansion_text}"
                expanded_terms.extend(expansions)
        
        # Apply regulation expansions
        for regulation, expansions in self.regulation_expansions.items():
            if regulation in query:
                expansion_text = " ".join(expansions[:2])
                expanded_query += f" {expansion_text}"
                expanded_terms.extend(expansions[:2])
        
        return expanded_query, expanded_terms
    
    def _apply_technical_expansions(self, query: str) -> Tuple[str, List[str]]:
        """Apply technical term expansions"""
        expanded_terms = []
        expanded_query = query
        
        # Technical abbreviations and expansions
        technical_expansions = {
            "diy": ["do it yourself", "home improvement", "self build"],
            "hvac": ["heating ventilation air conditioning", "climate control"],
            "led": ["light emitting diode", "energy efficient lighting"],
            "pvc": ["polyvinyl chloride", "plastic pipe", "vinyl"],
            "mdf": ["medium density fiberboard", "engineered wood"],
            "gfci": ["ground fault circuit interrupter", "safety outlet"],
            "rpm": ["revolutions per minute", "speed", "rotation"],
            "psi": ["pounds per square inch", "pressure"],
            "cfm": ["cubic feet per minute", "airflow", "ventilation"],
            "btu": ["british thermal unit", "heating cooling capacity"]
        }
        
        for abbreviation, expansions in technical_expansions.items():
            if abbreviation in query:
                expansion_text = " ".join(expansions)
                expanded_query += f" {expansion_text}"
                expanded_terms.extend(expansions)
        
        return expanded_query, expanded_terms
    
    def get_query_variations(self, query: str, max_variations: int = 5) -> List[str]:
        """Generate multiple variations of a query"""
        variations = [query]  # Include original
        
        # Generate synonym-based variations
        words = query.lower().split()
        
        # Combine all synonym dictionaries
        all_synonyms = {}
        for synonym_dict in [self.action_synonyms, self.tool_synonyms, 
                           self.material_synonyms, self.problem_synonyms,
                           self.room_synonyms, self.skill_synonyms]:
            all_synonyms.update(synonym_dict)
        
        # Create variations by replacing words with synonyms
        for i, word in enumerate(words):
            if word in all_synonyms:
                synonyms = all_synonyms[word][:3]  # Limit synonyms
                for synonym in synonyms:
                    if len(variations) >= max_variations:
                        break
                    
                    # Replace word with synonym
                    variation_words = words.copy()
                    variation_words[i] = synonym
                    variation = " ".join(variation_words)
                    
                    if variation not in variations:
                        variations.append(variation)
        
        # Add question format variations
        if len(variations) < max_variations:
            if not query.lower().startswith(('how', 'what', 'which', 'where')):
                question_variations = [
                    f"how to {query.lower()}",
                    f"what about {query.lower()}",
                    f"help with {query.lower()}"
                ]
                
                for var in question_variations:
                    if len(variations) >= max_variations:
                        break
                    if var not in variations:
                        variations.append(var)
        
        return variations[:max_variations]
    
    def enhance_classification_input(self, query: str, intent_hint: Optional[str] = None) -> Dict:
        """Enhance query for classification with expansions and variations"""
        
        # Get expanded query
        expanded = self.expand_query(query, intent_hint)
        
        # Get query variations
        variations = self.get_query_variations(query, max_variations=3)
        
        # Extract key terms for emphasis
        key_terms = self._extract_key_terms(query)
        
        return {
            "original_query": query,
            "expanded_query": expanded.expanded_query,
            "expansion_terms": expanded.expansion_terms,
            "confidence_boost": expanded.confidence_boost,
            "query_variations": variations,
            "key_terms": key_terms,
            "processing_hints": {
                "has_singapore_context": any(term in query.lower() 
                                           for term in self.singapore_expansions.keys()),
                "has_technical_terms": self._has_technical_terms(query),
                "query_complexity": self._assess_query_complexity(query)
            }
        }
    
    def _extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms that should be emphasized in classification"""
        key_terms = []
        query_lower = query.lower()
        
        # Extract brand names
        for brand_dict in [self.brand_synonyms]:
            for brand in brand_dict.keys():
                if brand in query_lower:
                    key_terms.append(brand)
        
        # Extract tool names
        for tool in self.tool_synonyms.keys():
            if tool in query_lower:
                key_terms.append(tool)
        
        # Extract action words
        for action in self.action_synonyms.keys():
            if action in query_lower:
                key_terms.append(action)
        
        # Extract room/location terms
        for room in self.room_synonyms.keys():
            if room in query_lower:
                key_terms.append(room)
        
        return list(set(key_terms))  # Remove duplicates
    
    def _has_technical_terms(self, query: str) -> bool:
        """Check if query contains technical terms"""
        technical_indicators = [
            "specification", "rating", "voltage", "amperage", "horsepower",
            "rpm", "torque", "psi", "cfm", "btu", "watt", "amp", "volt"
        ]
        
        query_lower = query.lower()
        return any(term in query_lower for term in technical_indicators)
    
    def _assess_query_complexity(self, query: str) -> str:
        """Assess the complexity of the query"""
        word_count = len(query.split())
        
        if word_count <= 3:
            return "simple"
        elif word_count <= 8:
            return "moderate"
        else:
            return "complex"


def test_query_expansion():
    """Test query expansion with sample queries"""
    expander = DIYQueryExpander()
    
    test_queries = [
        ("fix leak", "problem_solving"),
        ("DeWalt drill", "tool_selection"),
        ("renovate HDB bathroom", "project_planning"),
        ("how to install", "learning"),
        ("Makita vs Bosch", "product_comparison")
    ]
    
    for query, intent_hint in test_queries:
        print(f"\\nOriginal Query: {query}")
        print(f"Intent Hint: {intent_hint}")
        
        # Get expanded query
        expanded = expander.expand_query(query, intent_hint)
        print(f"Expanded Query: {expanded.expanded_query}")
        print(f"Expansion Terms: {expanded.expansion_terms}")
        print(f"Confidence Boost: {expanded.confidence_boost:.3f}")
        
        # Get variations
        variations = expander.get_query_variations(query)
        print(f"Variations: {variations}")
        
        # Get enhanced input
        enhanced = expander.enhance_classification_input(query, intent_hint)
        print(f"Key Terms: {enhanced['key_terms']}")
        print(f"Processing Hints: {enhanced['processing_hints']}")
        print("-" * 80)


if __name__ == "__main__":
    test_query_expansion()