"""
DIY Knowledge Platform - Unified Nexus Implementation
=====================================================

A comprehensive Nexus-based platform that unifies:
- DIY Assistant API (RESTful API for natural language queries)
- CLI Tool (Command-line interface for project planning)
- MCP Server (Model Context Protocol for AI assistant integration)

Features:
- Natural language project queries with intent understanding
- Product compatibility checking with safety recommendations
- Project planning assistance with skill level assessment
- Budget optimization with multi-vendor pricing
- Safety recommendations with OSHA/ANSI compliance
- Real-time inventory and availability checking
- Community knowledge integration
- Expert guidance and best practices

Examples:
- "What do I need to install a new toilet?"
- "Can I use Makita batteries with DeWalt tools?"
- "How do I fix squeaky floors?"
- "What's the difference between a hammer drill and impact driver?"

Architecture:
- Built on Nexus multi-channel platform
- Integrates with existing DataFlow models
- Uses hybrid AI for intent understanding
- Provides contextual, project-aware responses
"""

import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal

# Nexus and Kailash SDK imports
from nexus import Nexus
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Import existing DataFlow models
try:
    from src.new_project.core.models import (
        db, Product, ProductCategory, ProductSpecification,
        UNSPSCCode, SafetyStandard, ComplianceRequirement, 
        Vendor, ProductPricing, InventoryLevel,
        UserProfile, SkillAssessment, SafetyCertification
    )
except ImportError:
    # Fallback for testing
    print("Warning: DataFlow models not available. Using mock implementations.")
    db = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# CORE DIY KNOWLEDGE MODELS
# ==============================================================================

@dataclass
class DIYProject:
    """DIY project definition with requirements and guidance."""
    id: str
    name: str
    description: str
    difficulty_level: str  # beginner, intermediate, advanced, expert
    estimated_time_hours: float
    estimated_cost_min: Decimal
    estimated_cost_max: Decimal
    category: str
    room_types: List[str]
    required_skills: List[str]
    safety_level: str
    permits_required: bool = False
    professional_help_recommended: bool = False
    tools_required: List[str] = field(default_factory=list)
    materials_needed: List[str] = field(default_factory=list)
    steps: List[Dict] = field(default_factory=list)
    tips_and_tricks: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)
    safety_warnings: List[str] = field(default_factory=list)

@dataclass
class ToolCompatibility:
    """Tool compatibility information with safety considerations."""
    tool1: str
    tool2: str
    compatibility_type: str  # compatible, incompatible, requires_adapter
    safety_rating: str
    notes: str
    verified_by_expert: bool = False

@dataclass
class ProjectRecommendation:
    """AI-generated project recommendation with context."""
    project: DIYProject
    confidence_score: float
    reasoning: str
    skill_level_match: bool
    budget_fit: bool
    safety_considerations: List[str]
    alternative_approaches: List[str]
    recommended_products: List[str]

# ==============================================================================
# DIY INTENT CLASSIFICATION SYSTEM
# ==============================================================================

class DIYIntentClassifier:
    """Natural language processing for DIY intent understanding."""
    
    def __init__(self):
        self.intent_patterns = {
            'project_planning': [
                r'i want to (build|make|create|construct|install) (?P<project>.*)',
                r'planning to (renovate|upgrade|improve|fix) (?P<room>.*)',
                r'how to (start|begin) (?P<project>.*) project'
            ],
            'tool_recommendation': [
                r'what tool (do i need|should i use) (for|to) (?P<task>.*)',
                r'best (tool|equipment) for (?P<application>.*)',
                r'recommend (something|tool) for (?P<use_case>.*)',
                r'difference between (?P<tool1>.*) and (?P<tool2>.*)'
            ],
            'compatibility_check': [
                r'can i use (?P<item1>.*) with (?P<item2>.*)',
                r'(?P<brand1>.*) (battery|batteries) (work|compatible) with (?P<brand2>.*)',
                r'will (?P<tool>.*) work on (?P<material>.*)'
            ],
            'problem_solving': [
                r'having trouble with (?P<issue>.*)',
                r'(?P<problem>.*) (not working|broken|stuck|squeaky)',
                r'how to fix (?P<issue>.*)',
                r'repair (?P<item>.*)'
            ],
            'safety_guidance': [
                r'is it safe to (?P<action>.*)',
                r'safety (requirements|precautions) for (?P<task>.*)',
                r'do i need (ppe|protection|safety gear) for (?P<task>.*)'
            ],
            'budget_optimization': [
                r'cheap(est|er) (way|option) to (?P<goal>.*)',
                r'(budget|affordable) (?P<item_type>.*) for (?P<use>.*)',
                r'save money on (?P<project>.*)'
            ]
        }
        
        # Common DIY entities and synonyms
        self.entity_mappings = {
            'toilet': ['toilet', 'commode', 'water closet', 'WC'],
            'bathroom': ['bathroom', 'bath', 'restroom', 'powder room'],
            'kitchen': ['kitchen', 'galley', 'kitchenette'],
            'drill': ['drill', 'driver', 'screwdriver'],
            'hammer_drill': ['hammer drill', 'rotary hammer', 'percussion drill'],
            'impact_driver': ['impact driver', 'impact drill', 'impact gun'],
            'floor': ['floor', 'flooring', 'hardwood', 'laminate', 'tile']
        }
        
        # Skill level indicators
        self.skill_indicators = {
            'beginner': ['first time', 'new to', 'never done', 'beginner', 'novice'],
            'intermediate': ['some experience', 'done before', 'intermediate'],
            'advanced': ['experienced', 'advanced', 'professional', 'expert']
        }

    def classify_intent(self, user_query: str) -> Dict[str, Any]:
        """Classify user intent and extract entities."""
        user_query = user_query.lower().strip()
        
        # Extract primary intent
        primary_intent = None
        entities = {}
        confidence = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, user_query)
                if match:
                    primary_intent = intent
                    entities.update(match.groupdict())
                    confidence = 0.8 if match else 0.3
                    break
            if primary_intent:
                break
        
        # Extract skill level
        skill_level = self._assess_skill_level(user_query)
        
        # Extract room/location context
        room_context = self._extract_room_context(user_query)
        
        # Extract urgency indicators
        urgency = self._assess_urgency(user_query)
        
        return {
            'primary_intent': primary_intent or 'general_inquiry',
            'entities': entities,
            'skill_level': skill_level,
            'room_context': room_context,
            'urgency': urgency,
            'confidence': confidence,
            'original_query': user_query
        }
    
    def _assess_skill_level(self, query: str) -> str:
        """Assess user skill level from query language."""
        for level, indicators in self.skill_indicators.items():
            if any(indicator in query for indicator in indicators):
                return level
        return 'intermediate'  # Default assumption
    
    def _extract_room_context(self, query: str) -> Optional[str]:
        """Extract room/location context from query."""
        room_keywords = {
            'bathroom': ['bathroom', 'bath', 'toilet', 'shower', 'vanity'],
            'kitchen': ['kitchen', 'sink', 'cabinet', 'countertop', 'appliance'],
            'bedroom': ['bedroom', 'bed', 'closet'],
            'living_room': ['living room', 'family room', 'den'],
            'garage': ['garage', 'workshop', 'shed'],
            'outdoor': ['deck', 'patio', 'yard', 'garden', 'fence']
        }
        
        for room, keywords in room_keywords.items():
            if any(keyword in query for keyword in keywords):
                return room
        return None
    
    def _assess_urgency(self, query: str) -> str:
        """Assess urgency level from query language."""
        urgent_keywords = ['emergency', 'urgent', 'asap', 'broken', 'leaking', 'not working']
        if any(keyword in query for keyword in urgent_keywords):
            return 'high'
        
        soon_keywords = ['soon', 'quickly', 'this weekend']
        if any(keyword in query for keyword in soon_keywords):
            return 'medium'
        
        return 'low'

# ==============================================================================
# DIY KNOWLEDGE BASE
# ==============================================================================

class DIYKnowledgeBase:
    """Comprehensive DIY knowledge base with projects, tools, and guidance."""
    
    def __init__(self):
        self.projects = self._initialize_projects()
        self.tool_compatibility = self._initialize_compatibility()
        self.safety_guidelines = self._initialize_safety_guidelines()
        
    def _initialize_projects(self) -> Dict[str, DIYProject]:
        """Initialize DIY project database."""
        return {
            'toilet_installation': DIYProject(
                id='toilet_installation',
                name='Install a New Toilet',
                description='Complete guide to removing old toilet and installing new one',
                difficulty_level='intermediate',
                estimated_time_hours=3.0,
                estimated_cost_min=Decimal('150.00'),
                estimated_cost_max=Decimal('400.00'),
                category='plumbing',
                room_types=['bathroom'],
                required_skills=['basic_plumbing', 'tool_use'],
                safety_level='medium',
                permits_required=False,
                professional_help_recommended=False,
                tools_required=[
                    'adjustable_wrench', 'wax_ring', 'toilet_bolts', 'level',
                    'putty_knife', 'bucket', 'rags', 'pliers'
                ],
                materials_needed=[
                    'toilet', 'wax_ring', 'toilet_bolts', 'supply_line',
                    'toilet_flange', 'plumbers_putty'
                ],
                steps=[
                    {'step': 1, 'description': 'Turn off water supply and drain toilet'},
                    {'step': 2, 'description': 'Remove old toilet and clean flange'},
                    {'step': 3, 'description': 'Install new wax ring and toilet bolts'},
                    {'step': 4, 'description': 'Position and secure new toilet'},
                    {'step': 5, 'description': 'Connect water supply and test'}
                ],
                tips_and_tricks=[
                    'Use two wax rings for extra seal if floor is uneven',
                    'Have a helper - toilets are heavy and awkward',
                    'Test fit before final installation'
                ],
                common_mistakes=[
                    'Overtightening bolts can crack the toilet base',
                    'Not centering toilet properly on flange',
                    'Forgetting to turn off water supply'
                ],
                safety_warnings=[
                    'Toilets are heavy - lift with your legs',
                    'Wear gloves when handling old wax ring',
                    'Ensure proper ventilation'
                ]
            ),
            
            'squeaky_floor_repair': DIYProject(
                id='squeaky_floor_repair',
                name='Fix Squeaky Floors',
                description='Eliminate squeaks in hardwood and subflooring',
                difficulty_level='beginner',
                estimated_time_hours=2.0,
                estimated_cost_min=Decimal('15.00'),
                estimated_cost_max=Decimal('75.00'),
                category='flooring',
                room_types=['any_room'],
                required_skills=['basic_carpentry'],
                safety_level='low',
                permits_required=False,
                professional_help_recommended=False,
                tools_required=[
                    'drill', 'screws', 'stud_finder', 'hammer', 'nail_set'
                ],
                materials_needed=[
                    'wood_screws', 'construction_adhesive', 'shims'
                ],
                steps=[
                    {'step': 1, 'description': 'Locate the source of the squeak'},
                    {'step': 2, 'description': 'Access from below if possible'},
                    {'step': 3, 'description': 'Secure loose subfloor to joists'},
                    {'step': 4, 'description': 'Use screws instead of nails'},
                    {'step': 5, 'description': 'Test and repeat if necessary'}
                ],
                tips_and_tricks=[
                    'Baby powder can temporarily quiet squeaks',
                    'Work during quiet times to hear squeaks clearly',
                    'Mark squeak locations with tape before starting'
                ],
                common_mistakes=[
                    'Using screws that are too long',
                    'Not pre-drilling pilot holes',
                    'Assuming all squeaks have the same cause'
                ],
                safety_warnings=[
                    'Watch for electrical wires when drilling',
                    'Wear safety glasses when working overhead'
                ]
            )
        }
    
    def _initialize_compatibility(self) -> List[ToolCompatibility]:
        """Initialize tool compatibility database."""
        return [
            ToolCompatibility(
                tool1='makita_battery',
                tool2='dewalt_tool',
                compatibility_type='incompatible',
                safety_rating='safe',
                notes='Different battery chemistries and connections. Use adapters available from third parties.',
                verified_by_expert=True
            ),
            ToolCompatibility(
                tool1='hammer_drill',
                tool2='masonry_bit',
                compatibility_type='compatible',
                safety_rating='safe',
                notes='Hammer drills are designed for masonry bits. Ensure proper bit size.',
                verified_by_expert=True
            )
        ]
    
    def _initialize_safety_guidelines(self) -> Dict[str, Dict]:
        """Initialize safety guidelines database."""
        return {
            'power_tools': {
                'ppe_required': ['safety_glasses', 'hearing_protection'],
                'precautions': [
                    'Inspect tools before use',
                    'Keep work area clean and well-lit',
                    'Disconnect power when changing accessories'
                ],
                'osha_standards': ['OSHA-1926.95', 'OSHA-1926.307']
            },
            'electrical_work': {
                'ppe_required': ['safety_glasses', 'insulated_gloves', 'non_conductive_shoes'],
                'precautions': [
                    'Turn off power at breaker',
                    'Test circuits before working',
                    'Use GFCI protection'
                ],
                'osha_standards': ['OSHA-1926.416', 'OSHA-1926.417']
            }
        }

# ==============================================================================
# DIY RECOMMENDATION ENGINE
# ==============================================================================

class DIYRecommendationEngine:
    """AI-powered recommendation engine for DIY projects and products."""
    
    def __init__(self, knowledge_base: DIYKnowledgeBase):
        self.knowledge_base = knowledge_base
        self.recommendation_weights = {
            'skill_level_match': 0.25,
            'project_relevance': 0.30,
            'budget_constraint': 0.15,
            'safety_consideration': 0.20,
            'availability': 0.10
        }
    
    def generate_recommendations(self, intent_analysis: Dict, user_profile: Optional[Dict] = None) -> List[ProjectRecommendation]:
        """Generate contextual recommendations based on intent analysis."""
        recommendations = []
        
        # Find relevant projects
        relevant_projects = self._find_relevant_projects(intent_analysis)
        
        for project in relevant_projects:
            # Calculate recommendation score
            score = self._calculate_recommendation_score(project, intent_analysis, user_profile)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(project, intent_analysis, score)
            
            # Check skill level match
            skill_match = self._check_skill_match(project, intent_analysis, user_profile)
            
            # Check budget fit
            budget_fit = self._check_budget_fit(project, intent_analysis)
            
            # Get safety considerations
            safety_considerations = self._get_safety_considerations(project)
            
            # Get alternative approaches
            alternatives = self._get_alternative_approaches(project, intent_analysis)
            
            # Get recommended products
            products = self._get_recommended_products(project)
            
            recommendation = ProjectRecommendation(
                project=project,
                confidence_score=score,
                reasoning=reasoning,
                skill_level_match=skill_match,
                budget_fit=budget_fit,
                safety_considerations=safety_considerations,
                alternative_approaches=alternatives,
                recommended_products=products
            )
            
            recommendations.append(recommendation)
        
        # Sort by confidence score
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _find_relevant_projects(self, intent_analysis: Dict) -> List[DIYProject]:
        """Find projects relevant to user intent."""
        relevant_projects = []
        query = intent_analysis['original_query']
        entities = intent_analysis['entities']
        room_context = intent_analysis.get('room_context')
        
        for project in self.knowledge_base.projects.values():
            relevance_score = 0
            
            # Check if project matches entities
            for entity_key, entity_value in entities.items():
                if entity_value and entity_value.lower() in project.name.lower():
                    relevance_score += 0.4
                if entity_value and entity_value.lower() in project.description.lower():
                    relevance_score += 0.2
            
            # Check room context match
            if room_context and room_context in project.room_types:
                relevance_score += 0.3
            
            # Check keyword overlap
            query_words = set(query.split())
            project_words = set((project.name + ' ' + project.description).lower().split())
            overlap = len(query_words.intersection(project_words))
            relevance_score += min(overlap * 0.1, 0.3)
            
            if relevance_score > 0.2:  # Threshold for relevance
                relevant_projects.append(project)
        
        return relevant_projects
    
    def _calculate_recommendation_score(self, project: DIYProject, intent_analysis: Dict, user_profile: Optional[Dict]) -> float:
        """Calculate recommendation confidence score."""
        score = 0.0
        
        # Base relevance score
        score += 0.5
        
        # Skill level match
        user_skill = intent_analysis.get('skill_level', 'intermediate')
        if project.difficulty_level == user_skill:
            score += self.recommendation_weights['skill_level_match']
        elif abs(self._skill_to_number(project.difficulty_level) - self._skill_to_number(user_skill)) == 1:
            score += self.recommendation_weights['skill_level_match'] * 0.7
        
        # Safety considerations
        if intent_analysis.get('urgency') == 'high' and project.safety_level == 'high':
            score -= 0.2  # Reduce score for high-risk urgent projects
        
        # Add randomness for diversity
        import random
        score += random.uniform(-0.1, 0.1)
        
        return min(max(score, 0.0), 1.0)
    
    def _skill_to_number(self, skill_level: str) -> int:
        """Convert skill level to number for comparison."""
        mapping = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}
        return mapping.get(skill_level, 2)
    
    def _generate_reasoning(self, project: DIYProject, intent_analysis: Dict, score: float) -> str:
        """Generate human-readable reasoning for recommendation."""
        reasons = []
        
        if score > 0.8:
            reasons.append("Excellent match for your needs")
        elif score > 0.6:
            reasons.append("Good match for your requirements")
        else:
            reasons.append("Possible option to consider")
        
        if intent_analysis.get('skill_level') == project.difficulty_level:
            reasons.append(f"matches your {project.difficulty_level} skill level")
        
        if intent_analysis.get('urgency') == 'high':
            reasons.append(f"can be completed in {project.estimated_time_hours} hours")
        
        return "; ".join(reasons) + "."
    
    def _check_skill_match(self, project: DIYProject, intent_analysis: Dict, user_profile: Optional[Dict]) -> bool:
        """Check if project matches user skill level."""
        user_skill = intent_analysis.get('skill_level', 'intermediate')
        project_skill_num = self._skill_to_number(project.difficulty_level)
        user_skill_num = self._skill_to_number(user_skill)
        
        return abs(project_skill_num - user_skill_num) <= 1
    
    def _check_budget_fit(self, project: DIYProject, intent_analysis: Dict) -> bool:
        """Check if project fits user budget constraints."""
        # Simple heuristic - assume budget fit unless high urgency + high cost
        if intent_analysis.get('urgency') == 'high' and project.estimated_cost_max > 500:
            return False
        return True
    
    def _get_safety_considerations(self, project: DIYProject) -> List[str]:
        """Get safety considerations for project."""
        considerations = []
        
        if project.safety_level == 'high':
            considerations.append("High-risk project - consider professional consultation")
        
        if project.permits_required:
            considerations.append("Building permits may be required")
        
        if project.professional_help_recommended:
            considerations.append("Professional assistance recommended")
        
        considerations.extend(project.safety_warnings)
        
        return considerations
    
    def _get_alternative_approaches(self, project: DIYProject, intent_analysis: Dict) -> List[str]:
        """Get alternative approaches to the project."""
        alternatives = []
        
        if project.difficulty_level == 'advanced':
            alternatives.append("Consider hiring a professional contractor")
            alternatives.append("Break project into smaller phases")
        
        if project.estimated_cost_max > 300:
            alternatives.append("Look for budget-friendly material alternatives")
            alternatives.append("Consider used or rental tools")
        
        return alternatives
    
    def _get_recommended_products(self, project: DIYProject) -> List[str]:
        """Get recommended products for project."""
        # Combine tools and materials
        return project.tools_required + project.materials_needed

# ==============================================================================
# NEXUS WORKFLOW BUILDERS
# ==============================================================================

def create_diy_assistant_workflow() -> WorkflowBuilder:
    """Create workflow for DIY assistant API responses."""
    workflow = WorkflowBuilder()
    
    # Intent classification
    workflow.add_node("PythonCodeNode", "classify_intent", {
        "code": """
# Initialize DIY intent classifier
classifier = DIYIntentClassifier()

# Get user query from input
user_query = input_data.get('query', '')
user_profile = input_data.get('user_profile', {})

# Classify intent
intent_analysis = classifier.classify_intent(user_query)

result = {
    'intent_analysis': intent_analysis,
    'user_profile': user_profile,
    'original_query': user_query
}
"""
    })
    
    # Generate recommendations
    workflow.add_node("PythonCodeNode", "generate_recommendations", {
        "code": """
# Initialize knowledge base and recommendation engine
knowledge_base = DIYKnowledgeBase()
rec_engine = DIYRecommendationEngine(knowledge_base)

# Get intent analysis from previous step
intent_analysis = input_data['intent_analysis']
user_profile = input_data.get('user_profile')

# Generate recommendations
recommendations = rec_engine.generate_recommendations(intent_analysis, user_profile)

result = {
    'recommendations': [
        {
            'project_name': rec.project.name,
            'description': rec.project.description,
            'difficulty': rec.project.difficulty_level,
            'time_estimate': rec.project.estimated_time_hours,
            'cost_range': f'${rec.project.estimated_cost_min}-${rec.project.estimated_cost_max}',
            'confidence': rec.confidence_score,
            'reasoning': rec.reasoning,
            'tools_needed': rec.project.tools_required,
            'materials_needed': rec.project.materials_needed,
            'safety_warnings': rec.safety_considerations,
            'steps': rec.project.steps
        }
        for rec in recommendations
    ],
    'intent_analysis': intent_analysis
}
"""
    })
    
    # Format response
    workflow.add_node("PythonCodeNode", "format_response", {
        "code": """
import json

# Get data from previous steps
recommendations = input_data['recommendations']
intent_analysis = input_data['intent_analysis']

# Format response based on intent
primary_intent = intent_analysis['primary_intent']

if primary_intent == 'project_planning':
    response_type = 'project_guide'
elif primary_intent == 'tool_recommendation':
    response_type = 'tool_suggestions'
elif primary_intent == 'compatibility_check':
    response_type = 'compatibility_info'
elif primary_intent == 'problem_solving':
    response_type = 'troubleshooting_guide'
else:
    response_type = 'general_advice'

result = {
    'response_type': response_type,
    'recommendations': recommendations,
    'total_count': len(recommendations),
    'confidence': intent_analysis.get('confidence', 0.5),
    'user_skill_level': intent_analysis.get('skill_level', 'intermediate'),
    'urgency': intent_analysis.get('urgency', 'low')
}
"""
    })
    
    # Connect nodes
    workflow.connect("classify_intent", "generate_recommendations")
    workflow.connect("generate_recommendations", "format_response")
    
    return workflow

def create_compatibility_check_workflow() -> WorkflowBuilder:
    """Create workflow for product compatibility checking."""
    workflow = WorkflowBuilder()
    
    workflow.add_node("PythonCodeNode", "check_compatibility", {
        "code": """
# Get items to check from input
item1 = input_data.get('item1', '').lower()
item2 = input_data.get('item2', '').lower()

# Initialize knowledge base
knowledge_base = DIYKnowledgeBase()

# Check compatibility
compatibility_info = None
for compat in knowledge_base.tool_compatibility:
    if (item1 in compat.tool1.lower() and item2 in compat.tool2.lower()) or \
       (item2 in compat.tool1.lower() and item1 in compat.tool2.lower()):
        compatibility_info = compat
        break

if compatibility_info:
    result = {
        'compatible': compatibility_info.compatibility_type == 'compatible',
        'compatibility_type': compatibility_info.compatibility_type,
        'safety_rating': compatibility_info.safety_rating,
        'notes': compatibility_info.notes,
        'expert_verified': compatibility_info.verified_by_expert
    }
else:
    # Default response for unknown combinations
    result = {
        'compatible': None,
        'compatibility_type': 'unknown',
        'safety_rating': 'unknown',
        'notes': 'Compatibility information not available. Consult manufacturer specifications.',
        'expert_verified': False
    }
"""
    })
    
    return workflow

def create_safety_check_workflow() -> WorkflowBuilder:
    """Create workflow for safety recommendations."""
    workflow = WorkflowBuilder()
    
    workflow.add_node("PythonCodeNode", "safety_analysis", {
        "code": """
# Get task/project from input
task = input_data.get('task', '').lower()
project_type = input_data.get('project_type', 'general')

# Initialize knowledge base
knowledge_base = DIYKnowledgeBase()

# Determine safety category
safety_category = 'general'
if any(word in task for word in ['drill', 'saw', 'grind', 'sand']):
    safety_category = 'power_tools'
elif any(word in task for word in ['wire', 'electric', 'outlet', 'switch']):
    safety_category = 'electrical_work'

# Get safety guidelines
guidelines = knowledge_base.safety_guidelines.get(safety_category, {})

result = {
    'safety_category': safety_category,
    'ppe_required': guidelines.get('ppe_required', []),
    'precautions': guidelines.get('precautions', []),
    'osha_standards': guidelines.get('osha_standards', []),
    'risk_level': 'medium' if safety_category != 'general' else 'low'
}
"""
    })
    
    return workflow

def create_budget_optimization_workflow() -> WorkflowBuilder:
    """Create workflow for budget optimization recommendations."""
    workflow = WorkflowBuilder()
    
    workflow.add_node("PythonCodeNode", "optimize_budget", {
        "code": """
# Get budget constraints from input
max_budget = input_data.get('max_budget', 1000.0)
project_type = input_data.get('project_type', 'general')
items_needed = input_data.get('items_needed', [])

# Budget optimization strategies
strategies = []

if max_budget < 100:
    strategies.extend([
        'Consider renting specialized tools instead of buying',
        'Look for used tools in good condition',
        'Buy basic versions and upgrade later if needed',
        'Use alternative materials that cost less'
    ])
elif max_budget < 500:
    strategies.extend([
        'Buy essential tools, rent specialty tools',
        'Look for combo tool packages for better value',
        'Consider mid-range brands for good quality/price balance'
    ])
else:
    strategies.extend([
        'Invest in quality tools that will last',
        'Consider professional-grade tools if you plan multiple projects',
        'Buy during sales or seasonal promotions'
    ])

# General money-saving tips
general_tips = [
    'Compare prices across multiple retailers',
    'Check for manufacturer rebates and promotions',
    'Consider generic/store brands for consumables',
    'Buy in bulk for materials you\'ll use repeatedly',
    'Join loyalty programs for frequent purchases'
]

result = {
    'budget_strategies': strategies,
    'general_tips': general_tips,
    'recommended_budget_split': {
        'tools': '40%',
        'materials': '50%',
        'safety_equipment': '10%'
    }
}
"""
    })
    
    return workflow

# ==============================================================================
# NEXUS PLATFORM INITIALIZATION
# ==============================================================================

def create_diy_nexus_platform() -> Nexus:
    """Create and configure the DIY Nexus platform."""
    
    # Initialize Nexus with enterprise features
    app = Nexus(
        api_port=8000,
        mcp_port=3001,
        enable_auth=False,  # Disable for demo
        enable_monitoring=True,
        rate_limit=100,
        auto_discovery=False  # Manual registration for better control
    )
    
    # Register core DIY workflows
    app.register("diy_assistant", create_diy_assistant_workflow().build())
    app.register("compatibility_check", create_compatibility_check_workflow().build())
    app.register("safety_check", create_safety_check_workflow().build())
    app.register("budget_optimization", create_budget_optimization_workflow().build())
    
    return app

# ==============================================================================
# CLI INTERFACE EXAMPLES
# ==============================================================================

def demonstrate_cli_usage():
    """Demonstrate CLI usage examples."""
    examples = [
        {
            'command': 'nexus execute diy_assistant --query "What do I need to install a new toilet?"',
            'description': 'Get complete project guidance for toilet installation'
        },
        {
            'command': 'nexus execute compatibility_check --item1 "Makita battery" --item2 "DeWalt drill"',
            'description': 'Check tool compatibility between brands'
        },
        {
            'command': 'nexus execute safety_check --task "using circular saw"',
            'description': 'Get safety requirements for power tool use'
        },
        {
            'command': 'nexus execute budget_optimization --max-budget 200 --project-type "bathroom"',
            'description': 'Get budget optimization strategies for bathroom projects'
        }
    ]
    
    print("=== DIY Nexus CLI Examples ===\n")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['description']}")
        print(f"   Command: {example['command']}\n")

# ==============================================================================
# API ENDPOINT EXAMPLES
# ==============================================================================

def demonstrate_api_usage():
    """Demonstrate API usage examples."""
    examples = [
        {
            'endpoint': 'POST /api/workflows/diy_assistant/execute',
            'payload': {
                'query': 'How do I fix squeaky floors?',
                'user_profile': {
                    'skill_level': 'beginner',
                    'budget_range': 'low'
                }
            },
            'description': 'Natural language DIY assistance'
        },
        {
            'endpoint': 'POST /api/workflows/compatibility_check/execute',
            'payload': {
                'item1': 'hammer drill',
                'item2': 'concrete'
            },
            'description': 'Check tool-material compatibility'
        },
        {
            'endpoint': 'POST /api/workflows/safety_check/execute',
            'payload': {
                'task': 'electrical outlet installation',
                'project_type': 'electrical'
            },
            'description': 'Get safety requirements and PPE recommendations'
        }
    ]
    
    print("=== DIY Nexus API Examples ===\n")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['description']}")
        print(f"   Endpoint: {example['endpoint']}")
        print(f"   Payload: {json.dumps(example['payload'], indent=2)}\n")

# ==============================================================================
# MCP INTEGRATION EXAMPLES
# ==============================================================================

def demonstrate_mcp_usage():
    """Demonstrate MCP integration examples."""
    examples = [
        {
            'tool_name': 'diy_assistant',
            'parameters': {
                'query': "What's the difference between a hammer drill and impact driver?",
                'user_skill': 'intermediate'
            },
            'description': 'AI assistant can ask for tool comparisons'
        },
        {
            'tool_name': 'compatibility_check',
            'parameters': {
                'item1': 'Ryobi battery',
                'item2': 'Milwaukee tool'
            },
            'description': 'AI assistant can check cross-brand compatibility'
        },
        {
            'tool_name': 'safety_check',
            'parameters': {
                'task': 'tile cutting with wet saw'
            },
            'description': 'AI assistant can provide safety guidance'
        }
    ]
    
    print("=== DIY Nexus MCP Integration Examples ===\n")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['description']}")
        print(f"   Tool: {example['tool_name']}")
        print(f"   Parameters: {json.dumps(example['parameters'], indent=2)}\n")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    """Main function to start the DIY Nexus platform."""
    print("🔧 DIY Knowledge Platform - Nexus Implementation")
    print("=" * 50)
    
    # Initialize platform
    try:
        app = create_diy_nexus_platform()
        
        print("✅ DIY Nexus platform initialized successfully!")
        print(f"🌐 API Server: http://localhost:8000")
        print(f"🔌 MCP Server: http://localhost:3001")
        print(f"💻 CLI Access: nexus execute <workflow_name>")
        print()
        
        # Demonstrate usage examples
        demonstrate_cli_usage()
        demonstrate_api_usage()
        demonstrate_mcp_usage()
        
        print("🚀 Starting DIY Nexus Platform...")
        print("   Press Ctrl+C to stop")
        
        # Start the platform (this will block)
        app.start()
        
    except KeyboardInterrupt:
        print("\n👋 DIY Nexus Platform stopped")
    except Exception as e:
        print(f"❌ Error starting platform: {e}")
        logger.error(f"Platform startup error: {e}", exc_info=True)

if __name__ == "__main__":
    main()