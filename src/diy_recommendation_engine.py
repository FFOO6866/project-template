"""
Smart DIY Recommendation Engine for Horme Hardware

This module provides intelligent, context-aware recommendations for DIY projects
combining knowledge graph insights, semantic understanding, content enrichment,
and safety considerations.

Features:
- Project-based recommendations with step-by-step tool suggestions
- Skill-appropriate tool recommendations based on user experience
- Budget-aware alternatives and cost optimization
- Compatibility checking for tool combinations
- Safety equipment reminders and compliance checking
- Real-time inventory integration
- Learning from user preferences and project outcomes

Components:
- ProjectRecommendationEngine: Main recommendation orchestrator
- SkillBasedFilter: Filters recommendations by user skill level
- BudgetOptimizer: Optimizes recommendations within budget constraints
- CompatibilityChecker: Ensures tool compatibility and synergy
- SafetyAdvisor: Provides safety equipment and procedure recommendations
- PersonalizationEngine: Learns from user behavior and preferences
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, Counter
import math

# Import our other DIY system components
from .diy_knowledge_graph import DIYKnowledgeGraph, ProductNode, ProjectNode
from .semantic_product_understanding import SemanticProductUnderstanding, QueryIntent
from .diy_content_enrichment import KnowledgeIntegrator, ContentInsight

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """User profile for personalized recommendations"""
    user_id: str
    skill_levels: Dict[str, str]  # skill_area -> level (beginner/intermediate/expert)
    completed_projects: List[str]  # project_ids
    owned_tools: List[str]  # product_ids
    budget_range: Tuple[float, float]  # (min, max)
    preferences: Dict[str, Any]  # brand preferences, etc.
    safety_level: str = "standard"  # conservative, standard, relaxed
    experience_score: float = 0.0  # 0-1 based on completed projects
    learning_goals: List[str] = field(default_factory=list)

@dataclass
class ProjectRecommendation:
    """Comprehensive project recommendation"""
    project_id: str
    project_name: str
    project_description: str
    difficulty_level: str
    estimated_time: str
    confidence_score: float  # How confident we are in this recommendation
    
    # Tool recommendations
    essential_tools: List[Dict[str, Any]]
    recommended_tools: List[Dict[str, Any]]
    optional_tools: List[Dict[str, Any]]
    
    # Cost breakdown
    tool_cost_estimate: Dict[str, float]  # category -> cost
    total_estimated_cost: float
    budget_alternatives: List[Dict[str, Any]]
    
    # Safety and skill requirements
    required_skills: List[Dict[str, Any]]
    safety_equipment: List[Dict[str, Any]]
    safety_warnings: List[str]
    
    # Learning resources
    tutorials: List[Dict[str, Any]]
    guides: List[Dict[str, Any]]
    
    # Compatibility and alternatives
    tool_compatibility_matrix: Dict[str, Dict[str, float]]
    alternative_approaches: List[Dict[str, Any]]
    
    # Personalization factors
    skill_match_score: float  # How well it matches user skill level
    interest_match_score: float  # How well it matches user interests
    success_probability: float  # Likelihood of successful completion

@dataclass
class ToolRecommendation:
    """Individual tool recommendation with context"""
    product_id: str
    product_name: str
    category: str
    price: float
    importance: str  # essential, recommended, optional
    compatibility_score: float  # with other recommended tools
    skill_appropriateness: float  # how appropriate for user skill level
    alternatives: List[Dict[str, Any]]
    usage_in_project: str  # how it's used in the project
    safety_considerations: List[str]

class SkillBasedFilter:
    """Filters and adjusts recommendations based on user skill level"""
    
    def __init__(self):
        """Initialize skill-based filtering system"""
        
        # Skill progression mappings
        self.skill_hierarchy = {
            'beginner': 1,
            'intermediate': 2, 
            'expert': 3
        }
        
        # Tool complexity ratings
        self.tool_complexity = {
            'hand_tools': {
                'hammer': 1,
                'screwdriver': 1,
                'measuring_tape': 1,
                'level': 1,
                'pliers': 1,
                'wrench': 2,
                'chisel': 2,
                'hand_saw': 2
            },
            'power_tools': {
                'drill': 1,
                'jigsaw': 2,
                'circular_saw': 3,
                'router': 3,
                'table_saw': 3,
                'miter_saw': 2,
                'orbital_sander': 1,
                'belt_sander': 2
            },
            'specialized_tools': {
                'multimeter': 3,
                'pipe_threader': 3,
                'tile_wet_saw': 2,
                'compressor': 2,
                'welder': 3
            }
        }
        
    def filter_tools_by_skill(self, tools: List[Dict[str, Any]], 
                             user_skill_level: str,
                             skill_area: str = "general") -> List[Dict[str, Any]]:
        """Filter tools appropriate for user skill level"""
        
        user_level = self.skill_hierarchy.get(user_skill_level, 1)
        filtered_tools = []
        
        for tool in tools:
            tool_category = tool.get('category', 'hand_tools')
            tool_name = tool.get('name', '').lower()
            
            # Find tool complexity
            tool_complexity = self._get_tool_complexity(tool_name, tool_category)
            
            # Allow tools at or slightly above user level
            if tool_complexity <= user_level + 0.5:
                # Add skill appropriateness score
                appropriateness = max(0, 1 - (tool_complexity - user_level) * 0.3)
                tool['skill_appropriateness'] = appropriateness
                filtered_tools.append(tool)
                
        return filtered_tools
        
    def adjust_project_difficulty(self, project: Dict[str, Any], 
                                user_profile: UserProfile) -> Dict[str, Any]:
        """Adjust project recommendations based on user skill"""
        
        project_difficulty = project.get('difficulty_level', 'intermediate')
        project_level = self.skill_hierarchy.get(project_difficulty, 2)
        
        # Calculate user's overall skill level
        skill_levels = list(user_profile.skill_levels.values())
        if skill_levels:
            avg_user_level = sum(self.skill_hierarchy.get(level, 1) for level in skill_levels) / len(skill_levels)
        else:
            avg_user_level = 1
            
        # Adjust project based on skill gap
        skill_gap = project_level - avg_user_level
        
        adjusted_project = project.copy()
        
        if skill_gap > 1:  # Project too difficult
            adjusted_project['difficulty_adjustment'] = 'simplified'
            adjusted_project['recommended_modifications'] = [
                'Consider hiring professional for complex steps',
                'Break project into smaller phases',
                'Get experienced helper for difficult parts'
            ]
        elif skill_gap < -0.5:  # Project too easy
            adjusted_project['difficulty_adjustment'] = 'enhanced'
            adjusted_project['enhancement_suggestions'] = [
                'Add decorative elements',
                'Use more advanced techniques',
                'Incorporate additional features'
            ]
        else:
            adjusted_project['difficulty_adjustment'] = 'appropriate'
            
        return adjusted_project
        
    def _get_tool_complexity(self, tool_name: str, category: str) -> int:
        """Get complexity rating for a tool"""
        
        # Check specific tool mappings
        for cat, tools in self.tool_complexity.items():
            if any(tool_key in tool_name for tool_key in tools.keys()):
                for tool_key, complexity in tools.items():
                    if tool_key in tool_name:
                        return complexity
                        
        # Default complexity by category
        category_defaults = {
            'hand_tools': 1,
            'power_tools': 2,
            'specialized_tools': 3,
            'measuring_tools': 1,
            'safety_equipment': 1
        }
        
        return category_defaults.get(category, 2)

class BudgetOptimizer:
    """Optimizes recommendations within budget constraints"""
    
    def __init__(self):
        """Initialize budget optimization system"""
        self.price_tolerance = 0.15  # 15% tolerance for better alternatives
        
    def optimize_tool_selection(self, tools: List[Dict[str, Any]], 
                               budget: float,
                               priorities: Dict[str, float] = None) -> Dict[str, Any]:
        """Optimize tool selection within budget"""
        
        if not tools:
            return {'selected_tools': [], 'total_cost': 0, 'budget_used': 0}
            
        priorities = priorities or {}
        
        # Categorize tools by importance
        essential_tools = [t for t in tools if t.get('importance') == 'essential']
        recommended_tools = [t for t in tools if t.get('importance') == 'recommended']
        optional_tools = [t for t in tools if t.get('importance') == 'optional']
        
        selected_tools = []
        remaining_budget = budget
        
        # First, select essential tools
        for tool in essential_tools:
            price = tool.get('price', 0)
            if price <= remaining_budget:
                selected_tools.append(tool)
                remaining_budget -= price
            else:
                # Look for cheaper alternative
                alternative = self._find_budget_alternative(tool, remaining_budget)
                if alternative:
                    selected_tools.append(alternative)
                    remaining_budget -= alternative['price']
                    
        # Then add recommended tools if budget allows
        recommended_sorted = sorted(recommended_tools, 
                                  key=lambda x: x.get('value_score', 0), 
                                  reverse=True)
        
        for tool in recommended_sorted:
            price = tool.get('price', 0)
            if price <= remaining_budget:
                selected_tools.append(tool)
                remaining_budget -= price
                
        # Finally, add optional tools with highest value
        optional_sorted = sorted(optional_tools,
                               key=lambda x: x.get('value_score', 0),
                               reverse=True)
        
        for tool in optional_sorted:
            price = tool.get('price', 0)
            if price <= remaining_budget:
                selected_tools.append(tool)
                remaining_budget -= price
                
        total_cost = budget - remaining_budget
        
        return {
            'selected_tools': selected_tools,
            'total_cost': total_cost,
            'budget_used': total_cost / budget if budget > 0 else 0,
            'remaining_budget': remaining_budget,
            'optimization_notes': self._generate_optimization_notes(
                selected_tools, budget, total_cost
            )
        }
        
    def find_budget_alternatives(self, target_tools: List[Dict[str, Any]],
                               budget_constraint: float) -> List[Dict[str, Any]]:
        """Find budget-friendly alternatives for expensive tools"""
        
        alternatives = []
        
        for tool in target_tools:
            price = tool.get('price', 0)
            
            if price > budget_constraint * 0.3:  # If tool is >30% of budget
                # Generate alternatives
                alternative_options = [
                    {
                        'original_tool': tool['name'],
                        'alternative': 'Rent instead of buy',
                        'cost_savings': price * 0.7,  # Assume 70% savings
                        'trade_offs': ['Limited usage time', 'Need to return']
                    },
                    {
                        'original_tool': tool['name'],
                        'alternative': 'Buy used/refurbished',
                        'cost_savings': price * 0.4,  # Assume 40% savings
                        'trade_offs': ['May have wear', 'Limited warranty']
                    },
                    {
                        'original_tool': tool['name'],
                        'alternative': 'Borrow from friend/neighbor',
                        'cost_savings': price,
                        'trade_offs': ['Dependent on availability', 'Social obligation']
                    }
                ]
                
                alternatives.extend(alternative_options)
                
        return alternatives
        
    def _find_budget_alternative(self, tool: Dict[str, Any], 
                               max_price: float) -> Optional[Dict[str, Any]]:
        """Find a budget alternative for a specific tool"""
        
        # This would integrate with product database to find actual alternatives
        # For now, simulate with price reduction
        original_price = tool.get('price', 0)
        
        if original_price <= max_price:
            return tool
            
        # Simulate finding a budget version
        budget_version = tool.copy()
        budget_version['name'] += ' (Budget Version)'
        budget_version['price'] = min(original_price * 0.7, max_price)
        budget_version['trade_offs'] = ['Lower quality', 'Less features', 'Shorter warranty']
        
        return budget_version
        
    def _generate_optimization_notes(self, selected_tools: List[Dict[str, Any]],
                                   budget: float, total_cost: float) -> List[str]:
        """Generate notes about budget optimization"""
        
        notes = []
        
        budget_utilization = total_cost / budget if budget > 0 else 0
        
        if budget_utilization > 0.95:
            notes.append("Excellent budget utilization - using almost full budget efficiently")
        elif budget_utilization > 0.8:
            notes.append("Good budget utilization - consider adding optional tools")
        elif budget_utilization < 0.6:
            notes.append("Budget underutilized - consider upgrading to higher quality tools")
            
        essential_count = len([t for t in selected_tools if t.get('importance') == 'essential'])
        recommended_count = len([t for t in selected_tools if t.get('importance') == 'recommended'])
        
        if essential_count == 0:
            notes.append("WARNING: No essential tools selected - project may not be feasible")
        elif recommended_count == 0:
            notes.append("Only essential tools selected - consider increasing budget for better results")
            
        return notes

class CompatibilityChecker:
    """Ensures tool compatibility and identifies synergies"""
    
    def __init__(self):
        """Initialize compatibility checking system"""
        
        # Compatibility rules
        self.compatibility_rules = {
            'voltage_compatibility': {
                'description': 'Tools with same voltage can share batteries',
                'weight': 0.8
            },
            'brand_ecosystem': {
                'description': 'Same brand tools often work together better',
                'weight': 0.6
            },
            'complementary_function': {
                'description': 'Tools that complement each other in workflow',
                'weight': 0.7
            },
            'shared_accessories': {
                'description': 'Tools that share bits, blades, or attachments',
                'weight': 0.5
            }
        }
        
        # Known compatibility combinations
        self.known_combinations = {
            ('drill', 'driver_bits'): 0.95,
            ('circular_saw', 'saw_blades'): 0.95,
            ('router', 'router_bits'): 0.95,
            ('sander', 'sandpaper'): 0.90,
            ('measuring_tape', 'level'): 0.85,
            ('drill', 'level'): 0.80
        }
        
    def check_tool_compatibility(self, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check compatibility between selected tools"""
        
        if len(tools) < 2:
            return {'compatibility_score': 1.0, 'issues': [], 'synergies': []}
            
        compatibility_matrix = {}
        issues = []
        synergies = []
        
        # Check each pair of tools
        for i, tool1 in enumerate(tools):
            for j, tool2 in enumerate(tools[i+1:], i+1):
                compatibility_score = self._calculate_compatibility(tool1, tool2)
                compatibility_matrix[f"{tool1['name']}-{tool2['name']}"] = compatibility_score
                
                if compatibility_score < 0.3:
                    issues.append({
                        'tool1': tool1['name'],
                        'tool2': tool2['name'],
                        'issue': 'Low compatibility',
                        'score': compatibility_score
                    })
                elif compatibility_score > 0.8:
                    synergies.append({
                        'tool1': tool1['name'],
                        'tool2': tool2['name'],
                        'synergy': 'High compatibility',
                        'score': compatibility_score
                    })
                    
        # Calculate overall compatibility score
        scores = list(compatibility_matrix.values())
        overall_score = sum(scores) / len(scores) if scores else 1.0
        
        return {
            'compatibility_score': overall_score,
            'compatibility_matrix': compatibility_matrix,
            'issues': issues,
            'synergies': synergies,
            'recommendations': self._generate_compatibility_recommendations(issues, synergies)
        }
        
    def _calculate_compatibility(self, tool1: Dict[str, Any], 
                               tool2: Dict[str, Any]) -> float:
        """Calculate compatibility score between two tools"""
        
        score = 0.5  # Base compatibility
        
        # Check voltage compatibility
        if tool1.get('specifications', {}).get('voltage') == tool2.get('specifications', {}).get('voltage'):
            if tool1.get('specifications', {}).get('voltage'):  # Both have voltage
                score += 0.2
                
        # Check brand compatibility
        if tool1.get('brand') == tool2.get('brand'):
            score += 0.15
            
        # Check functional compatibility
        tool1_type = self._get_tool_type(tool1.get('name', ''))
        tool2_type = self._get_tool_type(tool2.get('name', ''))
        
        # Check known combinations
        combo_key = tuple(sorted([tool1_type, tool2_type]))
        if combo_key in self.known_combinations:
            score = max(score, self.known_combinations[combo_key])
            
        # Check for conflicting requirements
        if self._tools_conflict(tool1, tool2):
            score *= 0.5
            
        return min(max(score, 0), 1)  # Clamp between 0 and 1
        
    def _get_tool_type(self, tool_name: str) -> str:
        """Extract tool type from tool name"""
        tool_name_lower = tool_name.lower()
        
        tool_types = {
            'drill': ['drill'],
            'saw': ['saw'],
            'router': ['router'],
            'sander': ['sander'],
            'hammer': ['hammer'],
            'level': ['level'],
            'measuring_tape': ['tape', 'measure'],
            'driver_bits': ['bit', 'driver'],
            'saw_blades': ['blade']
        }
        
        for tool_type, keywords in tool_types.items():
            if any(keyword in tool_name_lower for keyword in keywords):
                return tool_type
                
        return 'unknown'
        
    def _tools_conflict(self, tool1: Dict[str, Any], tool2: Dict[str, Any]) -> bool:
        """Check if tools have conflicting requirements"""
        
        # Check for power conflicts (e.g., both need same outlet)
        if (tool1.get('category') == 'power_tools' and 
            tool2.get('category') == 'power_tools' and
            tool1.get('specifications', {}).get('power_type') == 'corded' and
            tool2.get('specifications', {}).get('power_type') == 'corded'):
            return True  # Both need power outlet
            
        # Check for space conflicts
        if (tool1.get('specifications', {}).get('size') == 'large' and
            tool2.get('specifications', {}).get('size') == 'large'):
            return True  # Both are large tools
            
        return False
        
    def _generate_compatibility_recommendations(self, issues: List[Dict[str, Any]],
                                              synergies: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on compatibility analysis"""
        
        recommendations = []
        
        if issues:
            recommendations.append(f"Found {len(issues)} compatibility issues to address")
            for issue in issues[:2]:  # Show top 2 issues
                recommendations.append(
                    f"Consider alternatives for {issue['tool1']} or {issue['tool2']}"
                )
                
        if synergies:
            recommendations.append(f"Great synergy between {len(synergies)} tool pairs")
            for synergy in synergies[:2]:  # Show top 2 synergies
                recommendations.append(
                    f"{synergy['tool1']} works excellently with {synergy['tool2']}"
                )
                
        if not issues and synergies:
            recommendations.append("Excellent tool selection with high compatibility")
        elif not issues and not synergies:
            recommendations.append("Good basic tool selection")
            
        return recommendations

class SafetyAdvisor:
    """Provides safety equipment and procedure recommendations"""
    
    def __init__(self):
        """Initialize safety advisor system"""
        
        # Safety requirements by tool category
        self.tool_safety_requirements = {
            'power_tools': {
                'required': ['safety_glasses', 'hearing_protection'],
                'recommended': ['work_gloves', 'dust_mask']
            },
            'cutting_tools': {
                'required': ['safety_glasses', 'work_gloves'],
                'recommended': ['hearing_protection']
            },
            'electrical_tools': {
                'required': ['insulated_gloves', 'voltage_tester'],
                'recommended': ['rubber_soled_shoes']
            },
            'chemical_products': {
                'required': ['respiratory_protection', 'chemical_gloves'],
                'recommended': ['eye_wash_station']
            }
        }
        
        # Safety standards compliance
        self.safety_standards = {
            'OSHA_1926': {
                'power_tools': ['1926.302', '1926.304'],
                'electrical': ['1926.95', '1926.416'],
                'ppe': ['1926.95', '1926.96']
            },
            'ANSI': {
                'eye_protection': 'Z87.1',
                'hearing_protection': 'S3.19',
                'hand_protection': 'S2.15'
            }
        }
        
    def generate_safety_recommendations(self, tools: List[Dict[str, Any]],
                                      project_type: str,
                                      user_skill_level: str) -> Dict[str, Any]:
        """Generate comprehensive safety recommendations"""
        
        required_ppe = set()
        recommended_ppe = set()
        safety_procedures = []
        compliance_standards = []
        risk_assessment = {}
        
        # Analyze each tool
        for tool in tools:
            tool_safety = self._analyze_tool_safety(tool)
            required_ppe.update(tool_safety['required_ppe'])
            recommended_ppe.update(tool_safety['recommended_ppe'])
            safety_procedures.extend(tool_safety['procedures'])
            compliance_standards.extend(tool_safety['standards'])
            
        # Project-specific safety requirements
        project_safety = self._get_project_safety_requirements(project_type)
        required_ppe.update(project_safety['required_ppe'])
        safety_procedures.extend(project_safety['procedures'])
        
        # Skill-level adjustments
        if user_skill_level == 'beginner':
            # More conservative safety requirements
            recommended_ppe.update(['first_aid_kit', 'safety_handbook'])
            safety_procedures.append("Consider having experienced person supervise")
            
        # Risk assessment
        risk_assessment = self._assess_project_risks(tools, project_type, user_skill_level)
        
        return {
            'required_safety_equipment': list(required_ppe),
            'recommended_safety_equipment': list(recommended_ppe),
            'safety_procedures': list(set(safety_procedures)),  # Remove duplicates
            'compliance_standards': list(set(compliance_standards)),
            'risk_assessment': risk_assessment,
            'safety_checklist': self._generate_safety_checklist(
                required_ppe, recommended_ppe, safety_procedures
            )
        }
        
    def _analyze_tool_safety(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze safety requirements for a specific tool"""
        
        tool_category = tool.get('category', 'hand_tools')
        tool_name = tool.get('name', '').lower()
        
        safety_info = {
            'required_ppe': [],
            'recommended_ppe': [],
            'procedures': [],
            'standards': []
        }
        
        # Get safety requirements by category
        if tool_category in self.tool_safety_requirements:
            reqs = self.tool_safety_requirements[tool_category]
            safety_info['required_ppe'] = reqs.get('required', [])
            safety_info['recommended_ppe'] = reqs.get('recommended', [])
            
        # Specific tool hazards
        if 'saw' in tool_name:
            safety_info['required_ppe'].extend(['safety_glasses', 'hearing_protection'])
            safety_info['procedures'].append('Keep blade guards in place')
            safety_info['procedures'].append('Secure workpiece before cutting')
            
        if 'drill' in tool_name:
            safety_info['required_ppe'].append('safety_glasses')
            safety_info['procedures'].append('Ensure bit is properly secured')
            
        if 'grinder' in tool_name:
            safety_info['required_ppe'].extend(['face_shield', 'hearing_protection'])
            safety_info['procedures'].append('Check for bystanders before use')
            
        # Add relevant standards
        if tool_category == 'power_tools':
            safety_info['standards'].append('OSHA_1926.302')
        if 'electrical' in tool_category:
            safety_info['standards'].append('OSHA_1926.95')
            
        return safety_info
        
    def _get_project_safety_requirements(self, project_type: str) -> Dict[str, Any]:
        """Get safety requirements specific to project type"""
        
        project_safety_map = {
            'electrical': {
                'required_ppe': ['insulated_gloves', 'voltage_tester'],
                'procedures': [
                    'Turn off power at breaker',
                    'Test wires with voltage tester',
                    'Use GFCI protection'
                ]
            },
            'plumbing': {
                'required_ppe': ['work_gloves', 'safety_glasses'],
                'procedures': [
                    'Shut off water supply',
                    'Have emergency shutoff accessible',
                    'Check for lead pipes'
                ]
            },
            'roofing': {
                'required_ppe': ['fall_protection', 'non_slip_shoes'],
                'procedures': [
                    'Use proper ladder setup',
                    'Check weather conditions',
                    'Have spotter present'
                ]
            },
            'demolition': {
                'required_ppe': ['dust_mask', 'safety_glasses', 'work_gloves'],
                'procedures': [
                    'Check for asbestos/lead',
                    'Ensure structural safety',
                    'Have debris removal plan'
                ]
            }
        }
        
        return project_safety_map.get(project_type, {
            'required_ppe': ['safety_glasses', 'work_gloves'],
            'procedures': ['Read all tool manuals', 'Keep work area clean']
        })
        
    def _assess_project_risks(self, tools: List[Dict[str, Any]], 
                            project_type: str, 
                            user_skill_level: str) -> Dict[str, Any]:
        """Assess overall project risks"""
        
        risk_factors = {
            'tool_complexity': 0,
            'electrical_hazard': 0,
            'fall_hazard': 0,
            'cut_hazard': 0,
            'chemical_hazard': 0,
            'fire_hazard': 0
        }
        
        # Analyze tools for risk factors
        for tool in tools:
            tool_name = tool.get('name', '').lower()
            tool_category = tool.get('category', '')
            
            if 'saw' in tool_name or 'cutter' in tool_name:
                risk_factors['cut_hazard'] += 1
            if 'electrical' in tool_category or 'wire' in tool_name:
                risk_factors['electrical_hazard'] += 1
            if 'ladder' in tool_name or 'scaffold' in tool_name:
                risk_factors['fall_hazard'] += 1
            if 'chemical' in tool_category or 'solvent' in tool_name:
                risk_factors['chemical_hazard'] += 1
                
        # Project-specific risks
        project_risks = {
            'electrical': {'electrical_hazard': 3, 'fire_hazard': 2},
            'roofing': {'fall_hazard': 3},
            'plumbing': {'chemical_hazard': 1},
            'welding': {'fire_hazard': 3, 'chemical_hazard': 2}
        }
        
        if project_type in project_risks:
            for risk, value in project_risks[project_type].items():
                risk_factors[risk] += value
                
        # Skill level adjustment
        skill_multiplier = {'beginner': 1.5, 'intermediate': 1.0, 'expert': 0.7}
        multiplier = skill_multiplier.get(user_skill_level, 1.0)
        
        for risk in risk_factors:
            risk_factors[risk] = min(risk_factors[risk] * multiplier, 5)  # Cap at 5
            
        # Calculate overall risk level
        total_risk = sum(risk_factors.values())
        risk_level = 'low' if total_risk < 5 else 'medium' if total_risk < 15 else 'high'
        
        return {
            'risk_factors': risk_factors,
            'overall_risk_level': risk_level,
            'total_risk_score': total_risk,
            'recommendations': self._generate_risk_recommendations(risk_factors, risk_level)
        }
        
    def _generate_risk_recommendations(self, risk_factors: Dict[str, float], 
                                     risk_level: str) -> List[str]:
        """Generate risk-based recommendations"""
        
        recommendations = []
        
        if risk_level == 'high':
            recommendations.append("HIGH RISK PROJECT - Consider professional assistance")
            recommendations.append("Ensure all safety equipment is available before starting")
            
        # Specific risk recommendations  
        if risk_factors['electrical_hazard'] > 2:
            recommendations.append("ELECTRICAL HAZARD - Turn off power and use voltage tester")
        if risk_factors['fall_hazard'] > 2:
            recommendations.append("FALL HAZARD - Use proper fall protection equipment")
        if risk_factors['cut_hazard'] > 2:
            recommendations.append("CUTTING HAZARD - Keep first aid kit readily available")
        if risk_factors['chemical_hazard'] > 1:
            recommendations.append("CHEMICAL HAZARD - Ensure proper ventilation")
            
        return recommendations
        
    def _generate_safety_checklist(self, required_ppe: set, 
                                 recommended_ppe: set, 
                                 procedures: List[str]) -> List[Dict[str, Any]]:
        """Generate safety checklist for project"""
        
        checklist = []
        
        # PPE checklist items
        for ppe in required_ppe:
            checklist.append({
                'category': 'PPE',
                'item': f"Obtain and inspect {ppe.replace('_', ' ')}",
                'required': True,
                'checked': False
            })
            
        for ppe in recommended_ppe:
            checklist.append({
                'category': 'PPE',
                'item': f"Consider using {ppe.replace('_', ' ')}",
                'required': False,
                'checked': False
            })
            
        # Procedure checklist items
        for procedure in procedures[:5]:  # Limit to top 5
            checklist.append({
                'category': 'Procedure',
                'item': procedure,
                'required': True,
                'checked': False
            })
            
        return checklist

class PersonalizationEngine:
    """Learns from user behavior and preferences to improve recommendations"""
    
    def __init__(self):
        """Initialize personalization engine"""
        self.user_feedback_weight = 0.3
        self.success_rate_weight = 0.4
        self.preference_weight = 0.3
        
    def update_user_profile(self, user_profile: UserProfile, 
                          project_outcome: Dict[str, Any]) -> UserProfile:
        """Update user profile based on project outcome"""
        
        updated_profile = user_profile
        
        # Update experience score
        if project_outcome.get('completed', False):
            success_factor = 1.0 if project_outcome.get('successful', False) else 0.5
            updated_profile.experience_score = min(
                updated_profile.experience_score + 0.1 * success_factor, 
                1.0
            )
            
            # Add to completed projects
            project_id = project_outcome.get('project_id')
            if project_id and project_id not in updated_profile.completed_projects:
                updated_profile.completed_projects.append(project_id)
                
        # Update skill levels based on tools used successfully
        tools_used = project_outcome.get('tools_used', [])
        if project_outcome.get('successful', False):
            for tool in tools_used:
                tool_category = tool.get('category', 'general')
                current_level = updated_profile.skill_levels.get(tool_category, 'beginner')
                
                # Gradual skill progression
                if current_level == 'beginner' and len(updated_profile.completed_projects) > 2:
                    updated_profile.skill_levels[tool_category] = 'intermediate'
                elif current_level == 'intermediate' and len(updated_profile.completed_projects) > 5:
                    updated_profile.skill_levels[tool_category] = 'expert'
                    
        # Update preferences based on feedback
        feedback = project_outcome.get('feedback', {})
        if feedback:
            brand_ratings = feedback.get('brand_ratings', {})
            for brand, rating in brand_ratings.items():
                if 'brand_preferences' not in updated_profile.preferences:
                    updated_profile.preferences['brand_preferences'] = {}
                    
                current_rating = updated_profile.preferences['brand_preferences'].get(brand, 3.0)
                # Weighted average with new rating
                updated_profile.preferences['brand_preferences'][brand] = (
                    current_rating * 0.7 + rating * 0.3
                )
                
        return updated_profile
        
    def calculate_personalized_scores(self, recommendations: List[ProjectRecommendation],
                                    user_profile: UserProfile) -> List[ProjectRecommendation]:
        """Calculate personalized scores for recommendations"""
        
        for recommendation in recommendations:
            # Calculate skill match score
            rec_difficulty = recommendation.difficulty_level
            user_skills = list(user_profile.skill_levels.values())
            avg_user_skill = sum(1 if s == 'beginner' else 2 if s == 'intermediate' else 3 
                               for s in user_skills) / len(user_skills) if user_skills else 1
            
            rec_difficulty_num = 1 if rec_difficulty == 'beginner' else 2 if rec_difficulty == 'intermediate' else 3
            skill_diff = abs(avg_user_skill - rec_difficulty_num)
            recommendation.skill_match_score = max(0, 1 - skill_diff * 0.3)
            
            # Calculate interest match score based on completed projects
            similar_projects = len([p for p in user_profile.completed_projects 
                                  if self._projects_similar(p, recommendation.project_id)])
            recommendation.interest_match_score = min(similar_projects * 0.2 + 0.5, 1.0)
            
            # Calculate success probability
            base_success = 0.7  # Base success rate
            skill_adjustment = recommendation.skill_match_score * 0.2
            experience_adjustment = user_profile.experience_score * 0.1
            recommendation.success_probability = min(
                base_success + skill_adjustment + experience_adjustment, 
                1.0
            )
            
            # Update overall confidence score
            recommendation.confidence_score = (
                recommendation.skill_match_score * 0.4 +
                recommendation.interest_match_score * 0.3 +
                recommendation.success_probability * 0.3
            )
            
        return recommendations
        
    def _projects_similar(self, project1_id: str, project2_id: str) -> bool:
        """Check if two projects are similar (simplified)"""
        # This would use actual project similarity logic
        # For now, simple string similarity
        return any(word in project2_id.lower() for word in project1_id.lower().split('_'))

class ProjectRecommendationEngine:
    """Main recommendation engine that orchestrates all components"""
    
    def __init__(self, knowledge_graph: DIYKnowledgeGraph = None):
        """Initialize the recommendation engine"""
        
        # Initialize all components
        self.knowledge_graph = knowledge_graph or DIYKnowledgeGraph()
        self.semantic_system = SemanticProductUnderstanding()
        self.content_integrator = KnowledgeIntegrator()
        self.skill_filter = SkillBasedFilter()
        self.budget_optimizer = BudgetOptimizer()
        self.compatibility_checker = CompatibilityChecker()
        self.safety_advisor = SafetyAdvisor()
        self.personalization_engine = PersonalizationEngine()
        
        logger.info("DIY Recommendation Engine initialized")
        
    def get_project_recommendations(self, user_query: str,
                                  user_profile: UserProfile,
                                  available_products: List[Dict[str, Any]] = None,
                                  max_recommendations: int = 5) -> List[ProjectRecommendation]:
        """Get comprehensive project recommendations"""
        
        logger.info(f"Processing recommendation request: {user_query}")
        
        # Parse user intent and requirements
        query_result = self.semantic_system.process_query(user_query, available_products)
        intent = query_result.get('intent', {})
        
        # Get relevant projects from knowledge graph
        relevant_projects = self.knowledge_graph.semantic_search_projects(
            user_query, max_results=max_recommendations * 2
        )
        
        if not relevant_projects:
            logger.warning("No relevant projects found")
            return []
            
        recommendations = []
        
        for project in relevant_projects[:max_recommendations]:
            # Get project details
            project_id = project.get('id')
            project_tools = self.knowledge_graph.find_products_for_project(project_id)
            project_skills = self.knowledge_graph.find_skills_for_project(project_id)
            
            # Filter tools by skill level
            all_tools = []
            for importance, tools in project_tools.items():
                for tool in tools:
                    tool['importance'] = importance
                    all_tools.append(tool)
                    
            filtered_tools = self.skill_filter.filter_tools_by_skill(
                all_tools, 
                user_profile.skill_levels.get('general', 'beginner')
            )
            
            # Optimize within budget
            budget_max = user_profile.budget_range[1] if user_profile.budget_range else 1000
            budget_result = self.budget_optimizer.optimize_tool_selection(
                filtered_tools, budget_max
            )
            
            # Check tool compatibility
            compatibility_result = self.compatibility_checker.check_tool_compatibility(
                budget_result['selected_tools']
            )
            
            # Generate safety recommendations
            safety_result = self.safety_advisor.generate_safety_recommendations(
                budget_result['selected_tools'],
                project.get('category', 'general'),
                user_profile.skill_levels.get('general', 'beginner')
            )
            
            # Get learning resources
            content_insights = self.content_integrator.generate_content_insights(
                f"{project.get('name')} {user_query}", max_sources=5
            )
            
            # Create comprehensive recommendation
            recommendation = ProjectRecommendation(
                project_id=project_id,
                project_name=project.get('name', 'Unknown Project'),
                project_description=project.get('description', ''),
                difficulty_level=project.get('difficulty_level', 'intermediate'),
                estimated_time=project.get('estimated_time', 'Unknown'),
                confidence_score=0.8,  # Will be updated by personalization
                
                # Tool recommendations
                essential_tools=[t for t in budget_result['selected_tools'] if t.get('importance') == 'essential'],
                recommended_tools=[t for t in budget_result['selected_tools'] if t.get('importance') == 'recommended'],
                optional_tools=[t for t in budget_result['selected_tools'] if t.get('importance') == 'optional'],
                
                # Cost information
                tool_cost_estimate=self._calculate_cost_by_category(budget_result['selected_tools']),
                total_estimated_cost=budget_result['total_cost'],
                budget_alternatives=self.budget_optimizer.find_budget_alternatives(
                    filtered_tools, budget_max * 0.7
                ),
                
                # Skills and safety
                required_skills=project_skills,
                safety_equipment=safety_result['required_safety_equipment'],
                safety_warnings=safety_result['safety_procedures'],
                
                # Learning resources
                tutorials=[insight.extracted_knowledge for insight in content_insights 
                          if insight.content_type == 'youtube'][:3],
                guides=[],  # Would be populated with project guides
                
                # Technical details
                tool_compatibility_matrix=compatibility_result['compatibility_matrix'],
                alternative_approaches=[],  # Would be populated with alternatives
                
                # Personalization scores (to be updated)
                skill_match_score=0.0,
                interest_match_score=0.0,
                success_probability=0.0
            )
            
            recommendations.append(recommendation)
            
        # Apply personalization
        personalized_recommendations = self.personalization_engine.calculate_personalized_scores(
            recommendations, user_profile
        )
        
        # Sort by confidence score
        personalized_recommendations.sort(key=lambda r: r.confidence_score, reverse=True)
        
        logger.info(f"Generated {len(personalized_recommendations)} recommendations")
        return personalized_recommendations
        
    def _calculate_cost_by_category(self, tools: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate total cost by tool category"""
        
        cost_by_category = defaultdict(float)
        
        for tool in tools:
            category = tool.get('category', 'other')
            price = tool.get('price', 0)
            cost_by_category[category] += price
            
        return dict(cost_by_category)
        
    def get_tool_recommendations(self, tool_query: str, 
                               user_profile: UserProfile,
                               context: Dict[str, Any] = None) -> List[ToolRecommendation]:
        """Get specific tool recommendations"""
        
        # This would implement tool-specific recommendations
        # For now, return empty list
        return []

# Example usage and testing
if __name__ == "__main__":
    # Initialize recommendation engine
    engine = ProjectRecommendationEngine()
    
    # Create sample user profile
    user_profile = UserProfile(
        user_id="test_user_001",
        skill_levels={"general": "beginner", "woodworking": "intermediate"},
        completed_projects=["shelf_install"],
        owned_tools=["drill_001", "hammer_001"],
        budget_range=(50, 300),
        preferences={"brand_preferences": {"DeWalt": 4.0, "Makita": 3.5}},
        safety_level="standard"
    )
    
    # Test queries
    test_queries = [
        "I want to renovate my bathroom",
        "build a wooden deck for my backyard", 
        "fix leaky faucet in kitchen sink"
    ]
    
    print("Testing DIY Recommendation Engine:")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        try:
            # Get recommendations
            recommendations = engine.get_project_recommendations(
                query, user_profile, max_recommendations=2
            )
            
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    print(f"\nRecommendation {i}: {rec.project_name}")
                    print(f"  Difficulty: {rec.difficulty_level}")
                    print(f"  Time: {rec.estimated_time}")
                    print(f"  Confidence: {rec.confidence_score:.2f}")
                    print(f"  Estimated Cost: ${rec.total_estimated_cost:.2f}")
                    print(f"  Essential Tools: {len(rec.essential_tools)}")
                    print(f"  Safety Equipment: {len(rec.safety_equipment)}")
                    print(f"  Success Probability: {rec.success_probability:.2f}")
            else:
                print("No recommendations generated")
                
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            
    print(f"\nRecommendation engine testing completed!")
    print("Note: Full functionality requires knowledge graph population and API keys")