"""
Advanced entity extraction for DIY queries.
Extracts project types, skill levels, budget ranges, urgency, and Singapore-specific contexts.
"""

import re
import json
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import spacy
from spacy.matcher import Matcher, PhraseMatcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Types of entities to extract"""
    PROJECT_TYPE = "project_type"
    SKILL_LEVEL = "skill_level"
    BUDGET_RANGE = "budget_range"
    URGENCY = "urgency"
    ROOM_LOCATION = "room_location"
    TOOL_CATEGORY = "tool_category"
    MATERIAL_TYPE = "material_type"
    BRAND = "brand"
    PROBLEM_TYPE = "problem_type"
    SINGAPORE_CONTEXT = "singapore_context"


@dataclass
class ExtractedEntity:
    """Single extracted entity with metadata"""
    entity_type: EntityType
    value: str
    confidence: float
    start_char: int
    end_char: int
    extraction_method: str


class DIYEntityExtractor:
    """Advanced entity extraction system for DIY queries"""
    
    def __init__(self):
        # Load spaCy model (download with: python -m spacy download en_core_web_sm)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Using fallback extraction.")
            self.nlp = None
        
        self.matcher = Matcher(self.nlp.vocab) if self.nlp else None
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab) if self.nlp else None
        
        self._initialize_patterns()
        self._initialize_vocabularies()
    
    def _initialize_patterns(self):
        """Initialize spaCy patterns for entity extraction"""
        if not self.matcher:
            return
        
        # Project type patterns
        project_patterns = [
            [{"LOWER": {"IN": ["renovate", "renovation", "renovating"]}}, {"POS": "NOUN"}],
            [{"LOWER": {"IN": ["install", "installing", "installation"]}}, {"POS": "NOUN"}],
            [{"LOWER": {"IN": ["build", "building"]}}, {"POS": "NOUN"}],
            [{"LOWER": {"IN": ["fix", "repair", "fixing", "repairing"]}}, {"POS": "NOUN"}],
            [{"LOWER": {"IN": ["upgrade", "upgrading"]}}, {"POS": "NOUN"}],
        ]
        self.matcher.add("PROJECT_TYPE", project_patterns)
        
        # Skill level patterns
        skill_patterns = [
            [{"LOWER": {"IN": ["beginner", "newbie", "first", "new"]}},
             {"LOWER": {"IN": ["to", "at", "time"]}, "OP": "?"}],
            [{"LOWER": {"IN": ["advanced", "expert", "professional", "experienced"]}}],
            [{"LOWER": {"IN": ["intermediate", "moderate", "some"]}}, 
             {"LOWER": "experience", "OP": "?"}],
        ]
        self.matcher.add("SKILL_LEVEL", skill_patterns)
        
        # Budget patterns
        budget_patterns = [
            [{"LOWER": {"IN": ["cheap", "budget", "affordable", "low"]}}, 
             {"LOWER": {"IN": ["cost", "price", "budget"]}, "OP": "?"}],
            [{"LOWER": {"IN": ["expensive", "premium", "high-end", "professional"]}}],
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["dollars", "sgd", "$"]}}],
        ]
        self.matcher.add("BUDGET_RANGE", budget_patterns)
        
        # Urgency patterns
        urgency_patterns = [
            [{"LOWER": {"IN": ["urgent", "asap", "immediately", "emergency"]}}],
            [{"LOWER": {"IN": ["quick", "fast", "rapid", "soon"]}}],
            [{"LOWER": {"IN": ["later", "eventually", "someday", "planning"]}}],
        ]
        self.matcher.add("URGENCY", urgency_patterns)
    
    def _initialize_vocabularies(self):
        """Initialize entity vocabularies and taxonomies"""
        
        # Project types taxonomy
        self.project_types = {
            "renovation": ["renovate", "renovation", "remodel", "makeover", "upgrade"],
            "installation": ["install", "mount", "set up", "put in", "add"],
            "repair": ["fix", "repair", "mend", "restore", "troubleshoot"],
            "construction": ["build", "construct", "create", "make", "assemble"],
            "maintenance": ["maintain", "service", "clean", "replace", "upkeep"]
        }
        
        # Skill levels
        self.skill_levels = {
            "beginner": ["beginner", "newbie", "first time", "new to", "never done", "basic"],
            "intermediate": ["intermediate", "some experience", "moderate", "decent", "okay with"],
            "advanced": ["advanced", "expert", "professional", "experienced", "skilled", "pro"]
        }
        
        # Budget ranges (Singapore dollars)
        self.budget_ranges = {
            "under_500": ["cheap", "budget", "affordable", "low cost", "under 500", "< 500"],
            "500_2000": ["moderate", "medium", "reasonable", "500-2000", "mid-range"],
            "2000_5000": ["higher", "premium", "quality", "2000-5000", "good budget"],
            "above_5000": ["expensive", "luxury", "professional", "high-end", "> 5000", "no limit"]
        }
        
        # Room/location types
        self.room_types = {
            "bathroom": ["bathroom", "toilet", "washroom", "shower", "bath"],
            "kitchen": ["kitchen", "cooking area", "pantry", "food prep"],
            "bedroom": ["bedroom", "sleeping area", "master bedroom", "guest room"],
            "living_room": ["living room", "lounge", "sitting area", "hall"],
            "balcony": ["balcony", "patio", "terrace", "outdoor area"],
            "study": ["study", "office", "work area", "den"],
            "dining": ["dining room", "dining area", "eating area"]
        }
        
        # Singapore-specific contexts
        self.singapore_contexts = {
            "hdb": ["hdb", "public housing", "government flat", "bto", "built to order"],
            "condo": ["condo", "condominium", "private apartment", "serviced apartment"],
            "landed": ["landed property", "terrace", "semi-detached", "bungalow", "shophouse"],
            "regulations": ["town council", "hdb guidelines", "ura", "scdf", "fire safety"],
            "climate": ["humid", "tropical", "monsoon", "hot weather", "moisture"],
            "local_terms": ["void deck", "corridor", "common area", "aircon ledge"]
        }
        
        # Tool categories
        self.tool_categories = {
            "power_tools": ["drill", "saw", "grinder", "router", "sander", "impact driver"],
            "hand_tools": ["hammer", "screwdriver", "pliers", "wrench", "chisel", "file"],
            "measuring": ["tape measure", "level", "ruler", "caliper", "square"],
            "cutting": ["saw", "cutter", "knife", "blade", "scissors"],
            "fastening": ["screwdriver", "drill", "nail gun", "stapler"]
        }
        
        # Material types
        self.material_types = {
            "wood": ["wood", "timber", "plywood", "mdf", "hardwood", "softwood"],
            "metal": ["metal", "steel", "aluminum", "iron", "brass", "copper"],
            "plastic": ["plastic", "pvc", "acrylic", "polycarbonate"],
            "concrete": ["concrete", "cement", "masonry", "brick", "stone"],
            "glass": ["glass", "tempered glass", "laminated glass"],
            "tile": ["tile", "ceramic", "porcelain", "marble", "granite"]
        }
        
        # Popular brands
        self.brands = {
            "power_tools": ["dewalt", "makita", "bosch", "black & decker", "ryobi", "milwaukee", "festool"],
            "hand_tools": ["stanley", "craftsman", "klein", "channellock"],
            "measurement": ["stanley", "tajima", "stabila"],
            "local_brands": ["takagi", "toto", "grohe", "hansgrohe"]  # Popular in Singapore
        }
        
        # Problem types
        self.problem_types = {
            "plumbing": ["leak", "clog", "drip", "water pressure", "pipe", "faucet"],
            "electrical": ["outlet", "switch", "wiring", "power", "circuit breaker"],
            "structural": ["crack", "hole", "damage", "wear", "loose", "stuck"],
            "mechanical": ["squeak", "noise", "vibration", "movement", "alignment"]
        }
    
    def extract_entities(self, query: str) -> List[ExtractedEntity]:
        """Extract all entities from a query"""
        entities = []
        
        # Use spaCy if available
        if self.nlp:
            entities.extend(self._extract_with_spacy(query))
        
        # Always use rule-based extraction as backup/complement
        entities.extend(self._extract_with_rules(query))
        
        # Remove duplicates and merge overlapping entities
        entities = self._merge_entities(entities)
        
        return entities
    
    def _extract_with_spacy(self, query: str) -> List[ExtractedEntity]:
        """Extract entities using spaCy patterns"""
        entities = []
        doc = self.nlp(query)
        
        # Get pattern matches
        matches = self.matcher(doc)
        
        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            
            entity_type = self._map_spacy_label_to_entity_type(label)
            if entity_type:
                entities.append(ExtractedEntity(
                    entity_type=entity_type,
                    value=span.text.lower(),
                    confidence=0.8,  # spaCy pattern confidence
                    start_char=span.start_char,
                    end_char=span.end_char,
                    extraction_method="spacy_patterns"
                ))
        
        return entities
    
    def _extract_with_rules(self, query: str) -> List[ExtractedEntity]:
        """Extract entities using rule-based methods"""
        entities = []
        query_lower = query.lower()
        
        # Extract each entity type
        entities.extend(self._extract_project_types(query, query_lower))
        entities.extend(self._extract_skill_levels(query, query_lower))
        entities.extend(self._extract_budget_ranges(query, query_lower))
        entities.extend(self._extract_urgency(query, query_lower))
        entities.extend(self._extract_rooms(query, query_lower))
        entities.extend(self._extract_tools(query, query_lower))
        entities.extend(self._extract_materials(query, query_lower))
        entities.extend(self._extract_brands(query, query_lower))
        entities.extend(self._extract_problems(query, query_lower))
        entities.extend(self._extract_singapore_context(query, query_lower))
        
        return entities
    
    def _extract_project_types(self, query: str, query_lower: str) -> List[ExtractedEntity]:
        """Extract project type entities"""
        entities = []
        
        for project_type, keywords in self.project_types.items():
            for keyword in keywords:
                if keyword in query_lower:
                    start_pos = query_lower.find(keyword)
                    entities.append(ExtractedEntity(
                        entity_type=EntityType.PROJECT_TYPE,
                        value=project_type,
                        confidence=0.9,
                        start_char=start_pos,
                        end_char=start_pos + len(keyword),
                        extraction_method="keyword_matching"
                    ))
        
        return entities
    
    def _extract_skill_levels(self, query: str, query_lower: str) -> List[ExtractedEntity]:
        """Extract skill level entities"""
        entities = []
        
        for skill_level, keywords in self.skill_levels.items():
            for keyword in keywords:
                if keyword in query_lower:
                    start_pos = query_lower.find(keyword)
                    entities.append(ExtractedEntity(
                        entity_type=EntityType.SKILL_LEVEL,
                        value=skill_level,
                        confidence=0.85,
                        start_char=start_pos,
                        end_char=start_pos + len(keyword),
                        extraction_method="keyword_matching"
                    ))
        
        return entities
    
    def _extract_budget_ranges(self, query: str, query_lower: str) -> List[ExtractedEntity]:
        """Extract budget range entities"""
        entities = []
        
        # Keyword-based extraction
        for budget_range, keywords in self.budget_ranges.items():
            for keyword in keywords:
                if keyword in query_lower:
                    start_pos = query_lower.find(keyword)
                    entities.append(ExtractedEntity(
                        entity_type=EntityType.BUDGET_RANGE,
                        value=budget_range,
                        confidence=0.8,
                        start_char=start_pos,
                        end_char=start_pos + len(keyword),
                        extraction_method="keyword_matching"
                    ))
        
        # Numerical extraction
        price_patterns = [
            r'\\$([0-9,]+)',  # $1,000
            r'([0-9,]+)\\s*dollars?',  # 1000 dollars
            r'([0-9,]+)\\s*sgd',  # 1000 SGD
        ]
        
        for pattern in price_patterns:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = int(amount_str)
                    budget_range = self._classify_budget_amount(amount)
                    
                    entities.append(ExtractedEntity(
                        entity_type=EntityType.BUDGET_RANGE,
                        value=budget_range,
                        confidence=0.95,
                        start_char=match.start(),
                        end_char=match.end(),
                        extraction_method="numerical_extraction"
                    ))
                except ValueError:
                    continue
        
        return entities
    
    def _classify_budget_amount(self, amount: int) -> str:
        """Classify numerical budget amount into range"""
        if amount < 500:
            return "under_500"
        elif amount < 2000:
            return "500_2000"
        elif amount < 5000:
            return "2000_5000"
        else:
            return "above_5000"
    
    def _extract_urgency(self, query: str, query_lower: str) -> List[ExtractedEntity]:
        """Extract urgency level"""
        entities = []
        
        urgency_keywords = {
            "high": ["urgent", "emergency", "asap", "immediately", "right now", "critical"],
            "medium": ["soon", "quick", "fast", "fix", "repair", "broken"],
            "low": ["planning", "thinking", "considering", "future", "eventually"]
        }
        
        for urgency_level, keywords in urgency_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    start_pos = query_lower.find(keyword)
                    entities.append(ExtractedEntity(
                        entity_type=EntityType.URGENCY,
                        value=urgency_level,
                        confidence=0.8,
                        start_char=start_pos,
                        end_char=start_pos + len(keyword),
                        extraction_method="keyword_matching"
                    ))
        
        return entities
    
    def _extract_rooms(self, query: str, query_lower: str) -> List[ExtractedEntity]:
        """Extract room/location entities"""
        entities = []
        
        for room_type, keywords in self.room_types.items():
            for keyword in keywords:
                if keyword in query_lower:
                    start_pos = query_lower.find(keyword)
                    entities.append(ExtractedEntity(
                        entity_type=EntityType.ROOM_LOCATION,
                        value=room_type,
                        confidence=0.9,
                        start_char=start_pos,
                        end_char=start_pos + len(keyword),
                        extraction_method="keyword_matching"
                    ))
        
        return entities
    
    def _extract_tools(self, query: str, query_lower: str) -> List[ExtractedEntity]:
        """Extract tool category entities"""
        entities = []
        
        for tool_category, keywords in self.tool_categories.items():
            for keyword in keywords:
                if keyword in query_lower:
                    start_pos = query_lower.find(keyword)
                    entities.append(ExtractedEntity(
                        entity_type=EntityType.TOOL_CATEGORY,
                        value=tool_category,
                        confidence=0.85,
                        start_char=start_pos,
                        end_char=start_pos + len(keyword),
                        extraction_method="keyword_matching"
                    ))
        
        return entities
    
    def _extract_materials(self, query: str, query_lower: str) -> List[ExtractedEntity]:
        """Extract material type entities"""
        entities = []
        
        for material_type, keywords in self.material_types.items():
            for keyword in keywords:
                if keyword in query_lower:
                    start_pos = query_lower.find(keyword)
                    entities.append(ExtractedEntity(
                        entity_type=EntityType.MATERIAL_TYPE,
                        value=material_type,
                        confidence=0.85,
                        start_char=start_pos,
                        end_char=start_pos + len(keyword),
                        extraction_method="keyword_matching"
                    ))
        
        return entities
    
    def _extract_brands(self, query: str, query_lower: str) -> List[ExtractedEntity]:
        """Extract brand entities"""
        entities = []
        
        all_brands = []
        for category, brands in self.brands.items():
            all_brands.extend(brands)
        
        for brand in all_brands:
            if brand in query_lower:
                start_pos = query_lower.find(brand)
                entities.append(ExtractedEntity(
                    entity_type=EntityType.BRAND,
                    value=brand,
                    confidence=0.95,
                    start_char=start_pos,
                    end_char=start_pos + len(brand),
                    extraction_method="keyword_matching"
                ))
        
        return entities
    
    def _extract_problems(self, query: str, query_lower: str) -> List[ExtractedEntity]:
        """Extract problem type entities"""
        entities = []
        
        for problem_type, keywords in self.problem_types.items():
            for keyword in keywords:
                if keyword in query_lower:
                    start_pos = query_lower.find(keyword)
                    entities.append(ExtractedEntity(
                        entity_type=EntityType.PROBLEM_TYPE,
                        value=problem_type,
                        confidence=0.8,
                        start_char=start_pos,
                        end_char=start_pos + len(keyword),
                        extraction_method="keyword_matching"
                    ))
        
        return entities
    
    def _extract_singapore_context(self, query: str, query_lower: str) -> List[ExtractedEntity]:
        """Extract Singapore-specific context entities"""
        entities = []
        
        for context_type, keywords in self.singapore_contexts.items():
            for keyword in keywords:
                if keyword in query_lower:
                    start_pos = query_lower.find(keyword)
                    entities.append(ExtractedEntity(
                        entity_type=EntityType.SINGAPORE_CONTEXT,
                        value=context_type,
                        confidence=0.9,
                        start_char=start_pos,
                        end_char=start_pos + len(keyword),
                        extraction_method="keyword_matching"
                    ))
        
        return entities
    
    def _map_spacy_label_to_entity_type(self, label: str) -> Optional[EntityType]:
        """Map spaCy labels to our entity types"""
        mapping = {
            "PROJECT_TYPE": EntityType.PROJECT_TYPE,
            "SKILL_LEVEL": EntityType.SKILL_LEVEL,
            "BUDGET_RANGE": EntityType.BUDGET_RANGE,
            "URGENCY": EntityType.URGENCY
        }
        return mapping.get(label)
    
    def _merge_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Merge overlapping entities and remove duplicates"""
        if not entities:
            return entities
        
        # Sort by start position
        entities.sort(key=lambda x: x.start_char)
        
        merged = []
        current = entities[0]
        
        for next_entity in entities[1:]:
            # Check for overlap or exact duplicates
            if (current.entity_type == next_entity.entity_type and 
                current.value == next_entity.value):
                # Keep the one with higher confidence
                if next_entity.confidence > current.confidence:
                    current = next_entity
            elif (next_entity.start_char <= current.end_char and 
                  next_entity.entity_type == current.entity_type):
                # Overlapping entities of same type - merge
                current = ExtractedEntity(
                    entity_type=current.entity_type,
                    value=current.value if current.confidence >= next_entity.confidence else next_entity.value,
                    confidence=max(current.confidence, next_entity.confidence),
                    start_char=min(current.start_char, next_entity.start_char),
                    end_char=max(current.end_char, next_entity.end_char),
                    extraction_method=f"{current.extraction_method}+{next_entity.extraction_method}"
                )
            else:
                # No overlap, add current and move to next
                merged.append(current)
                current = next_entity
        
        merged.append(current)
        return merged
    
    def entities_to_dict(self, entities: List[ExtractedEntity]) -> Dict[str, Dict]:
        """Convert entities to dictionary format"""
        result = {}
        
        for entity in entities:
            entity_type_str = entity.entity_type.value
            
            if entity_type_str not in result:
                result[entity_type_str] = {
                    "values": [],
                    "confidence": 0.0
                }
            
            result[entity_type_str]["values"].append({
                "value": entity.value,
                "confidence": entity.confidence,
                "method": entity.extraction_method
            })
            
            # Update overall confidence (max confidence for this entity type)
            result[entity_type_str]["confidence"] = max(
                result[entity_type_str]["confidence"],
                entity.confidence
            )
        
        return result


def test_entity_extraction():
    """Test entity extraction with sample queries"""
    extractor = DIYEntityExtractor()
    
    test_queries = [
        "I want to renovate my HDB bathroom with a budget of $2000",
        "Need urgent help fixing leaky faucet in kitchen",
        "DeWalt vs Makita drill for wood drilling, beginner level",
        "How to install tiles in condo balcony professionally",
        "Planning expensive renovation for landed property living room"
    ]
    
    for query in test_queries:
        print(f"\\nQuery: {query}")
        entities = extractor.extract_entities(query)
        
        if entities:
            for entity in entities:
                print(f"  {entity.entity_type.value}: {entity.value} "
                      f"(confidence: {entity.confidence:.2f}, method: {entity.extraction_method})")
        else:
            print("  No entities extracted")
        
        # Convert to dictionary format
        entity_dict = extractor.entities_to_dict(entities)
        print(f"  Dictionary format: {json.dumps(entity_dict, indent=2)}")


if __name__ == "__main__":
    test_entity_extraction()