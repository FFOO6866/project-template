"""
Tool Classification Workflow - AI-001 Custom Classification
=========================================================

Custom classification workflow for tools and equipment:
- Project suitability and skill level matching
- Safety feature analysis and PPE requirements
- Tool type compatibility and usage recommendations
- Professional vs DIY appropriateness assessment

Follows Kailash SDK patterns with string-based nodes and runtime.execute(workflow.build())
"""

import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# Kailash SDK imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash.nodes.base import register_node, NodeParameter, Node

# Import our SDK compliance framework
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.new_project.nodes.sdk_compliance import SecureGovernedNode

# Import classification nodes to register them
from src.new_project.nodes.classification_nodes import UNSPSCClassificationNode, ETIMClassificationNode, SafetyComplianceNode


@register_node()
class ToolSuitabilityNode(SecureGovernedNode):
    """
    Custom node for tool project suitability and user skill level analysis.
    
    Analyzes tool appropriateness for specific projects, user skill levels,
    material compatibility, and workspace requirements.
    """
    
    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Define parameters for tool suitability analysis."""
        return {
            "product_data": NodeParameter(
                name="product_data",
                type=dict,
                required=True,
                description="Tool specifications including type, power, features, skill level requirements"
            ),
            "project_context": NodeParameter(
                name="project_context",
                type=dict,
                required=False,
                default={},
                description="Project details including type, materials, user skill level, workspace"
            ),
            "user_profile": NodeParameter(
                name="user_profile",
                type=dict,
                required=False,
                default={},
                description="User skill profile, experience level, and preferences"
            ),
            "safety_priority": NodeParameter(
                name="safety_priority",
                type=str,
                required=False,
                default="high",
                description="Safety priority level: low, medium, high, critical"
            )
        }
    
    def _run_implementation(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool suitability analysis."""
        product_data = inputs["product_data"]
        project_context = inputs.get("project_context", {})
        user_profile = inputs.get("user_profile", {})
        safety_priority = inputs.get("safety_priority", "high")
        
        # Analyze project suitability
        project_suitability = self._analyze_project_suitability(product_data, project_context)
        
        # Check skill level requirements
        skill_level_analysis = self._analyze_skill_level_requirements(
            product_data, project_context, user_profile
        )
        
        # Evaluate safety considerations
        safety_analysis = self._evaluate_safety_considerations(
            product_data, project_context, safety_priority
        )
        
        # Check material compatibility
        material_compatibility = self._check_material_compatibility(product_data, project_context)
        
        # Analyze workspace requirements
        workspace_analysis = self._analyze_workspace_requirements(product_data, project_context)
        
        # Calculate overall suitability score
        suitability_score = self._calculate_suitability_score([
            project_suitability, skill_level_analysis, safety_analysis, 
            material_compatibility, workspace_analysis
        ])
        
        # Generate recommendations
        recommendations = self._generate_tool_recommendations(
            product_data, project_context, user_profile, project_suitability,
            skill_level_analysis, safety_analysis, material_compatibility, workspace_analysis
        )
        
        return {
            "project_suitability": project_suitability,
            "skill_level_requirements": skill_level_analysis,
            "safety_considerations": safety_analysis,
            "material_compatibility": material_compatibility,
            "workspace_requirements": workspace_analysis,
            "overall_suitability": suitability_score,
            "recommended": suitability_score.get("score", 0) >= 0.7,
            "recommendations": recommendations,
            "usage_tips": self._generate_usage_tips(product_data, project_context),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _analyze_project_suitability(self, product_data: Dict, project_context: Dict) -> Dict:
        """Analyze how suitable the tool is for the specific project."""
        tool_type = product_data.get("tool_type", "").lower()
        project_type = project_context.get("project_type", "").lower()
        
        # Define tool-project compatibility matrix
        compatibility_matrix = {
            "power_drill": {
                "home_renovation": 0.9,
                "deck_construction": 0.8, 
                "furniture_assembly": 0.9,
                "electrical_work": 0.6,
                "plumbing": 0.4,
                "automotive": 0.5
            },
            "impact_driver": {
                "deck_construction": 0.95,
                "home_renovation": 0.8,
                "furniture_assembly": 0.7,
                "automotive": 0.9,
                "electrical_work": 0.3
            },
            "circular_saw": {
                "deck_construction": 0.95,
                "home_renovation": 0.9,
                "furniture_making": 0.8,
                "flooring": 0.9,
                "electrical_work": 0.2
            },
            "angle_grinder": {
                "metalworking": 0.95,
                "tile_work": 0.8,
                "automotive": 0.9,
                "deck_construction": 0.3,
                "furniture_assembly": 0.1
            },
            "reciprocating_saw": {
                "demolition": 0.95,
                "home_renovation": 0.8,
                "plumbing": 0.7,
                "electrical_work": 0.6,
                "furniture_assembly": 0.2
            }
        }
        
        # Get compatibility score
        tool_compatibility = compatibility_matrix.get(tool_type, {})
        base_score = tool_compatibility.get(project_type, 0.5)  # Default neutral score
        
        # Adjust score based on power requirements
        power_source = product_data.get("power_source", "").lower()
        workspace = project_context.get("workspace", "").lower()
        
        if power_source == "battery" and workspace in ["outdoor", "remote", "mobile"]:
            base_score += 0.1  # Bonus for battery tools in remote locations
        elif power_source == "corded" and workspace == "indoor" and project_context.get("power_available", True):
            base_score += 0.05  # Small bonus for corded tools with power access
        
        # Determine suitability level
        if base_score >= 0.9:
            suitability_level = "excellent"
        elif base_score >= 0.8:
            suitability_level = "very_good"
        elif base_score >= 0.7:
            suitability_level = "good"
        elif base_score >= 0.6:
            suitability_level = "acceptable"
        else:
            suitability_level = "poor"
        
        return {
            "score": min(1.0, base_score),
            "suitability_level": suitability_level,
            "tool_type": tool_type,
            "project_type": project_type,
            "power_compatibility": power_source,
            "workspace_match": workspace,
            "details": f"{tool_type.replace('_', ' ').title()} is {suitability_level} for {project_type.replace('_', ' ')}"
        }
    
    def _analyze_skill_level_requirements(self, product_data: Dict, project_context: Dict, 
                                        user_profile: Dict) -> Dict:
        """Analyze skill level requirements and user compatibility."""
        tool_skill_level = product_data.get("skill_level", "intermediate").lower()
        user_skill_level = user_profile.get("skill_level", project_context.get("user_skill_level", "beginner")).lower()
        user_experience = user_profile.get("experience_years", project_context.get("user_experience_years", 0))
        
        # Define skill level hierarchy
        skill_levels = {
            "beginner": 1,
            "intermediate": 2, 
            "advanced": 3,
            "professional": 4,
            "expert": 5
        }
        
        tool_skill_num = skill_levels.get(tool_skill_level, 2)
        user_skill_num = skill_levels.get(user_skill_level, 1)
        
        # Calculate skill match
        if user_skill_num >= tool_skill_num:
            skill_match = 1.0  # User skill meets or exceeds requirement
            match_status = "appropriate"
        elif user_skill_num == tool_skill_num - 1:
            skill_match = 0.7  # One level below - manageable with care
            match_status = "challenging_but_manageable"
        else:
            skill_match = 0.3  # Significant skill gap
            match_status = "beyond_current_skill"
        
        # Experience factor
        if user_experience >= 5:
            experience_bonus = 0.1
        elif user_experience >= 2:
            experience_bonus = 0.05
        else:
            experience_bonus = 0.0
        
        final_score = min(1.0, skill_match + experience_bonus)
        
        # Safety considerations for skill mismatch
        safety_concerns = []
        if user_skill_num < tool_skill_num:
            safety_concerns.append(f"Tool requires {tool_skill_level} skill level, user is {user_skill_level}")
            if tool_skill_level in ["advanced", "professional", "expert"]:
                safety_concerns.append("Consider professional training or supervision")
        
        return {
            "score": final_score,
            "match_status": match_status,
            "tool_skill_required": tool_skill_level,
            "user_skill_level": user_skill_level,
            "user_experience_years": user_experience,
            "skill_gap": max(0, tool_skill_num - user_skill_num),
            "safety_concerns": safety_concerns,
            "training_recommended": len(safety_concerns) > 0,
            "details": f"Tool requires {tool_skill_level} skill, user is {user_skill_level} with {user_experience} years experience"
        }
    
    def _evaluate_safety_considerations(self, product_data: Dict, project_context: Dict, 
                                      safety_priority: str) -> Dict:
        """Evaluate safety features and requirements for the tool."""
        safety_features = product_data.get("safety_features", [])
        tool_type = product_data.get("tool_type", "").lower()
        project_type = project_context.get("project_type", "").lower()
        
        # Define required safety features by tool type
        required_safety_features = {
            "circular_saw": ["blade_guard", "safety_switch", "anti_kickback"],
            "angle_grinder": ["guard", "safety_switch", "vibration_control"],
            "power_drill": ["clutch", "led_light", "belt_hook"],
            "reciprocating_saw": ["blade_guard", "anti-vibration", "variable_speed"],
            "impact_driver": ["led_light", "belt_hook", "electronic_clutch"]
        }
        
        # High-risk project types requiring extra safety
        high_risk_projects = ["demolition", "roofing", "electrical_work", "metalworking"]
        
        required_features = required_safety_features.get(tool_type, [])
        present_features = [f for f in required_features if f.replace("_", " ") in " ".join(safety_features).lower()]
        
        safety_coverage = len(present_features) / len(required_features) if required_features else 1.0
        
        # Additional safety considerations
        safety_score = safety_coverage
        safety_issues = []
        
        # High-risk project adjustments
        if project_type in high_risk_projects:
            if safety_coverage < 0.8:
                safety_issues.append(f"High-risk project ({project_type}) requires better safety features")
                safety_score *= 0.7
            
            # Check for specific high-risk safety features
            if tool_type == "angle_grinder" and "guard" not in " ".join(safety_features).lower():
                safety_issues.append("Angle grinder must have guard for safe operation")
                safety_score *= 0.5
        
        # PPE requirements
        ppe_requirements = self._determine_ppe_requirements(tool_type, project_type, safety_features)
        
        # Overall safety rating
        if safety_score >= 0.9 and not safety_issues:
            safety_rating = "excellent"
        elif safety_score >= 0.8:
            safety_rating = "very_good"
        elif safety_score >= 0.7:
            safety_rating = "good"
        elif safety_score >= 0.6:
            safety_rating = "acceptable"
        else:
            safety_rating = "poor"
        
        return {
            "safety_rating": safety_rating,
            "safety_score": safety_score,
            "safety_features_present": safety_features,
            "required_features": required_features,
            "missing_features": [f for f in required_features if f not in present_features],
            "safety_coverage": safety_coverage,
            "safety_issues": safety_issues,
            "ppe_requirements": ppe_requirements,
            "high_risk_project": project_type in high_risk_projects,
            "details": f"Safety rating: {safety_rating} ({len(present_features)}/{len(required_features)} required features present)"
        }
    
    def _check_material_compatibility(self, product_data: Dict, project_context: Dict) -> Dict:
        """Check tool compatibility with project materials."""
        tool_type = product_data.get("tool_type", "").lower()
        material_types = project_context.get("material_types", [])
        
        if not material_types:
            return {
                "status": "no_materials_specified",
                "score": 0.8,
                "details": "No specific materials specified for compatibility check"
            }
        
        # Define tool-material compatibility
        tool_material_compatibility = {
            "power_drill": {
                "wood": 0.95,
                "drywall": 0.9,
                "metal": 0.7,
                "concrete": 0.4,
                "plastic": 0.9,
                "composite": 0.8
            },
            "circular_saw": {
                "wood": 0.95,
                "plywood": 0.95,
                "composite": 0.9,
                "metal": 0.3,  # Requires special blade
                "plastic": 0.8,
                "drywall": 0.4
            },
            "angle_grinder": {
                "metal": 0.95,
                "stone": 0.9,
                "concrete": 0.9,
                "tile": 0.85,
                "wood": 0.2,  # Not recommended
                "plastic": 0.1
            },
            "reciprocating_saw": {
                "wood": 0.9,
                "metal": 0.8,
                "plastic": 0.85,
                "drywall": 0.9,
                "composite": 0.8,
                "demolition_materials": 0.95
            }
        }
        
        compatibility_scores = []
        material_analysis = {}
        
        tool_compatibility = tool_material_compatibility.get(tool_type, {})
        
        for material in material_types:
            material_lower = material.lower()
            compatibility = tool_compatibility.get(material_lower, 0.5)  # Default neutral
            compatibility_scores.append(compatibility)
            
            material_analysis[material] = {
                "compatibility": compatibility,
                "suitable": compatibility >= 0.7,
                "requires_special_setup": compatibility < 0.7 and compatibility >= 0.4
            }
        
        # Overall compatibility score
        if compatibility_scores:
            avg_compatibility = sum(compatibility_scores) / len(compatibility_scores)
            min_compatibility = min(compatibility_scores)
            
            # Use weighted average favoring the minimum (weakest link)
            overall_score = (avg_compatibility * 0.6) + (min_compatibility * 0.4)
        else:
            overall_score = 0.8  # Default when no materials specified
        
        # Determine compatibility status
        if overall_score >= 0.9:
            status = "excellent_compatibility"
        elif overall_score >= 0.8:
            status = "very_compatible"
        elif overall_score >= 0.7:
            status = "compatible"
        elif overall_score >= 0.5:
            status = "limited_compatibility"
        else:
            status = "poor_compatibility"
        
        # Identify problematic materials
        problematic_materials = [
            material for material, analysis in material_analysis.items()
            if not analysis["suitable"] and not analysis["requires_special_setup"]
        ]
        
        return {
            "status": status,
            "score": overall_score,
            "material_analysis": material_analysis,
            "compatible_materials": [m for m, a in material_analysis.items() if a["suitable"]],
            "problematic_materials": problematic_materials,
            "requires_special_setup": [m for m, a in material_analysis.items() if a["requires_special_setup"]],
            "details": f"Tool compatibility: {status} for specified materials"
        }
    
    def _analyze_workspace_requirements(self, product_data: Dict, project_context: Dict) -> Dict:
        """Analyze workspace requirements and constraints."""
        tool_size = product_data.get("dimensions", {})
        workspace = project_context.get("workspace", "").lower()
        space_constraints = project_context.get("space_constraints", {})
        
        # Tool portability analysis
        weight = product_data.get("weight", 0)  # in pounds
        power_source = product_data.get("power_source", "").lower()
        
        portability_score = 1.0
        workspace_issues = []
        
        # Weight considerations
        if weight > 15:
            portability_score -= 0.2
            workspace_issues.append("Heavy tool - may require breaks during extended use")
        elif weight > 10:
            portability_score -= 0.1
        
        # Power source considerations
        if power_source == "corded":
            if workspace in ["outdoor", "remote", "mobile"]:
                portability_score -= 0.3
                workspace_issues.append("Corded tool requires power access - may need extension cord or generator")
            elif not project_context.get("power_available", True):
                portability_score -= 0.5
                workspace_issues.append("No power available for corded tool")
        
        # Space constraints
        if space_constraints:
            if tool_size.get("length", 0) > space_constraints.get("max_length", float('inf')):
                portability_score -= 0.2
                workspace_issues.append("Tool length exceeds workspace constraints")
        
        # Workspace type suitability
        workspace_suitability = {
            "indoor": {"corded": 0.9, "battery": 0.8},
            "outdoor": {"battery": 0.9, "corded": 0.6},
            "garage": {"corded": 0.9, "battery": 0.9},
            "basement": {"corded": 0.8, "battery": 0.9},
            "remote": {"battery": 0.95, "corded": 0.1}
        }
        
        workspace_match = workspace_suitability.get(workspace, {}).get(power_source, 0.7)
        
        # Overall workspace score
        overall_score = (portability_score * 0.6) + (workspace_match * 0.4)
        
        return {
            "score": overall_score,
            "portability_score": portability_score,
            "workspace_match": workspace_match,
            "workspace_type": workspace,
            "power_source": power_source,
            "weight": weight,
            "workspace_issues": workspace_issues,
            "power_requirements": {
                "type": power_source,
                "access_needed": power_source == "corded",
                "extension_cord_needed": power_source == "corded" and workspace in ["outdoor", "remote"]
            },
            "details": f"Workspace compatibility: {overall_score:.2f} for {workspace} environment"
        }
    
    def _calculate_suitability_score(self, analyses: List[Dict]) -> Dict:
        """Calculate overall tool suitability score."""
        project_suitability, skill_level_analysis, safety_analysis, material_compatibility, workspace_analysis = analyses
        
        # Weighted scoring based on importance
        weights = {
            "project": 0.25,
            "skill": 0.2,
            "safety": 0.25,
            "material": 0.2,
            "workspace": 0.1
        }
        
        scores = {
            "project": project_suitability.get("score", 0.0),
            "skill": skill_level_analysis.get("score", 0.0),
            "safety": safety_analysis.get("safety_score", 0.0), 
            "material": material_compatibility.get("score", 0.0),
            "workspace": workspace_analysis.get("score", 0.0)
        }
        
        overall_score = sum(scores[key] * weights[key] for key in scores)
        
        # Determine recommendation level
        if overall_score >= 0.9:
            recommendation = "highly_recommended"
        elif overall_score >= 0.8:
            recommendation = "recommended"
        elif overall_score >= 0.7:
            recommendation = "suitable"
        elif overall_score >= 0.6:
            recommendation = "acceptable_with_caution"
        else:
            recommendation = "not_recommended"
        
        # Identify limiting factors
        limiting_factors = [
            key for key, score in scores.items() if score < 0.6
        ]
        
        return {
            "score": round(overall_score, 3),
            "recommendation": recommendation,
            "component_scores": scores,
            "weights": weights,
            "limiting_factors": limiting_factors,
            "grade": "A" if overall_score >= 0.9 else \
                    "B" if overall_score >= 0.8 else \
                    "C" if overall_score >= 0.7 else \
                    "D" if overall_score >= 0.6 else "F"
        }
    
    def _determine_ppe_requirements(self, tool_type: str, project_type: str, safety_features: List[str]) -> Dict:
        """Determine Personal Protective Equipment requirements."""
        base_ppe = {
            "safety_glasses": True,
            "hearing_protection": False,
            "dust_mask": False,
            "work_gloves": True,
            "steel_toe_boots": False
        }
        
        # High-noise tools
        high_noise_tools = ["circular_saw", "angle_grinder", "reciprocating_saw", "impact_driver"]
        if tool_type in high_noise_tools:
            base_ppe["hearing_protection"] = True
        
        # Dust-generating tools/projects
        dust_projects = ["sanding", "demolition", "drywall", "concrete_work"]
        dust_tools = ["angle_grinder", "circular_saw"]
        if tool_type in dust_tools or project_type in dust_projects:
            base_ppe["dust_mask"] = True
        
        # Heavy-duty projects
        heavy_projects = ["construction", "demolition", "metalworking"]
        if project_type in heavy_projects:
            base_ppe["steel_toe_boots"] = True
        
        ppe_list = [ppe for ppe, required in base_ppe.items() if required]
        
        return {
            "required_ppe": ppe_list,
            "detailed_requirements": base_ppe,
            "ppe_count": len(ppe_list),
            "high_ppe_requirement": len(ppe_list) >= 4
        }
    
    def _generate_tool_recommendations(self, product_data: Dict, project_context: Dict,
                                     user_profile: Dict, *analyses) -> List[str]:
        """Generate tool usage recommendations."""
        recommendations = []
        
        project_suitability, skill_level_analysis, safety_analysis, material_compatibility, workspace_analysis = analyses
        
        # Overall recommendation
        overall_score = self._calculate_suitability_score(analyses).get("score", 0)
        
        if overall_score >= 0.8:
            recommendations.append("Excellent tool choice for this project and user profile")
        elif overall_score >= 0.7:
            recommendations.append("Good tool choice - suitable for this project")
        elif overall_score >= 0.6:
            recommendations.append("Acceptable choice - review considerations below")
        else:
            recommendations.append("Consider alternative tools - significant limitations identified")
        
        # Skill level recommendations
        if skill_level_analysis.get("training_recommended", False):
            recommendations.append("Consider professional training or supervision before use")
        
        # Safety recommendations
        missing_features = safety_analysis.get("missing_features", [])
        if missing_features:
            recommendations.append(f"Consider tool with these safety features: {', '.join(missing_features)}")
        
        ppe_requirements = safety_analysis.get("ppe_requirements", {})
        if ppe_requirements.get("required_ppe"):
            ppe_list = ", ".join(ppe_requirements["required_ppe"])
            recommendations.append(f"Required PPE: {ppe_list}")
        
        # Material compatibility recommendations
        problematic_materials = material_compatibility.get("problematic_materials", [])
        if problematic_materials:
            recommendations.append(f"Not suitable for: {', '.join(problematic_materials)}")
        
        special_setup = material_compatibility.get("requires_special_setup", [])
        if special_setup:
            recommendations.append(f"Requires special setup/blades for: {', '.join(special_setup)}")
        
        # Workspace recommendations
        workspace_issues = workspace_analysis.get("workspace_issues", [])
        recommendations.extend(workspace_issues)
        
        return recommendations
    
    def _generate_usage_tips(self, product_data: Dict, project_context: Dict) -> List[str]:
        """Generate helpful usage tips for the tool."""
        tips = []
        
        tool_type = product_data.get("tool_type", "").lower()
        power_source = product_data.get("power_source", "").lower()
        
        # General tips by tool type
        tool_tips = {
            "power_drill": [
                "Use pilot holes for hardwood to prevent splitting",
                "Adjust clutch setting based on material and screw size",
                "Keep spare batteries charged for cordless models"
            ],
            "circular_saw": [
                "Support both sides of cut to prevent binding",
                "Use appropriate blade for material being cut",
                "Check blade depth - should extend 1/4 inch below material"
            ],
            "angle_grinder": [
                "Never remove the guard - it's essential for safety",
                "Let the tool reach full speed before contacting material",
                "Apply light pressure - let the tool do the work"
            ],
            "reciprocating_saw": [
                "Use longer blades for thicker materials",
                "Apply forward pressure to reduce blade wandering",
                "Change blades frequently for clean cuts"
            ]
        }
        
        tips.extend(tool_tips.get(tool_type, []))
        
        # Power source specific tips
        if power_source == "battery":
            tips.append("Monitor battery level - performance decreases as battery drains")
            tips.append("Keep batteries at room temperature for optimal performance")
        elif power_source == "corded":
            tips.append("Use proper gauge extension cord for tool's amperage requirements")
            tips.append("Protect cord from damage - route away from cutting area")
        
        # Project-specific tips
        project_type = project_context.get("project_type", "").lower()
        if "outdoor" in project_type or project_context.get("workspace") == "outdoor":
            tips.append("Protect tool from moisture and dust when working outdoors")
            tips.append("Use GFCI-protected outlets for outdoor electrical tools")
        
        return tips[:5]  # Limit to top 5 tips


class ToolClassificationWorkflow:
    """
    Complete tool classification workflow combining suitability analysis with standard classification.
    
    Uses Kailash SDK patterns with string-based nodes and WorkflowBuilder.
    Follows runtime.execute(workflow.build()) pattern for execution.
    """
    
    def __init__(self):
        self.workflow = WorkflowBuilder()
        self._setup_workflow()
    
    def _setup_workflow(self):
        """Setup tool classification workflow with string-based nodes."""
        
        # Standard UNSPSC classification
        self.workflow.add_node(
            "UNSPSCClassificationNode", "unspsc_classify",
            {
                "product_data": "${product_data}",
                "classification_system": "UNSPSC", 
                "domain": "tools",
                "confidence_threshold": 0.8
            }
        )
        
        # ETIM classification
        self.workflow.add_node(
            "ETIMClassificationNode", "etim_classify", 
            {
                "product_data": "${product_data}",
                "classification_system": "ETIM", 
                "domain": "tools",
                "language": "en"
            }
        )
        
        # Custom tool suitability analysis
        self.workflow.add_node(
            "ToolSuitabilityNode", "tool_suitability",
            {
                "product_data": "${product_data}",
                "project_context": "${project_context}",
                "user_profile": "${user_profile}"
            }
        )
        
        # Safety compliance checking
        self.workflow.add_node(
            "SafetyComplianceNode", "safety_compliance",
            {
                "product_data": "${product_data}",
                "standards": ["OSHA", "ANSI", "UL"], 
                "domain": "tools"
            }
        )
        
        # Results aggregation
        self.workflow.add_node(
            "PythonCodeNode", "aggregate_results",
            {
                "code": '''
# Aggregate tool classification results
result = {
    "classification_result": {
        "unspsc": unspsc_classify,
        "etim": etim_classify,
        "tool_suitability": tool_suitability,
        "safety_compliance": safety_compliance
    },
    "overall_score": (
        tool_suitability.get("overall_suitability", {}).get("score", 0) * 0.6 +
        (1.0 if safety_compliance.get("compliant", False) else 0.0) * 0.4
    ),
    "recommendations": []
}

# Combine recommendations
for component in [tool_suitability, safety_compliance]:
    if isinstance(component, dict) and "recommendations" in component:
        result["recommendations"].extend(component["recommendations"])

result["workflow_type"] = "tool_classification"
result["analysis_complete"] = True
                ''',
                "input_mapping": {
                    "unspsc_classify": "unspsc_classify.result",
                    "etim_classify": "etim_classify.result", 
                    "tool_suitability": "tool_suitability.result",
                    "safety_compliance": "safety_compliance.result"
                }
            }
        )
    
    def classify_tool(self, product_data: Dict[str, Any], 
                     project_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute tool classification workflow using SDK patterns.
        
        Args:
            product_data: Tool specifications and features
            project_context: Project details and user requirements
            
        Returns:
            Complete tool classification results with suitability analysis
        """
        from kailash.runtime.local import LocalRuntime
        
        runtime = LocalRuntime()
        
        # Prepare workflow inputs
        workflow_input = {
            "product_data": product_data,
            "project_context": project_context or {},
            "user_profile": project_context.get("user_profile", {}) if project_context else {}
        }
        
        # Execute workflow using SDK pattern: runtime.execute(workflow.build())
        results, run_id = runtime.execute(self.workflow.build(), workflow_input)
        
        return {
            "run_id": run_id,
            "classification_results": results,
            "workflow_type": "tool_classification",
            "execution_timestamp": datetime.now().isoformat()
        }


# Workflow creation helper functions
def create_tool_classification_workflow(product_data: Dict[str, Any], **kwargs) -> WorkflowBuilder:
    """
    Create tool classification workflow using string-based node API.
    
    Returns WorkflowBuilder configured for tool classification.
    Must call .build() before execution with LocalRuntime.
    """
    workflow = WorkflowBuilder()
    
    # Add tool workflow nodes using string-based API
    workflow.add_node(
        "ToolSuitabilityNode", "tool_suitability",
        {
            "product_data": product_data,
            "project_context": kwargs.get("project_context", {}),
            "user_profile": kwargs.get("user_profile", {}),
            "safety_priority": kwargs.get("safety_priority", "high")
        }
    )
    
    return workflow


def execute_tool_classification_example():
    """Example of proper SDK workflow execution pattern for tools."""
    # Test tool data
    product_data = {
        "name": "DeWalt 20V MAX Cordless Drill",
        "tool_type": "power_drill",
        "power_source": "battery",
        "voltage": 20,
        "skill_level": "intermediate",
        "weight": 3.5,
        "safety_features": ["LED light", "belt hook", "clutch", "keyless chuck"],
        "dimensions": {"length": 8.5, "height": 10, "width": 3}
    }
    
    project_context = {
        "project_type": "home_renovation",
        "user_skill_level": "intermediate",
        "material_types": ["wood", "drywall"],
        "workspace": "indoor",
        "power_available": True,
        "user_experience_years": 3
    }
    
    # Create and execute workflow
    workflow = ToolClassificationWorkflow()
    result = workflow.classify_tool(product_data, project_context)
    
    return result