"""
HVAC Classification Workflow - AI-001 Custom Classification
=========================================================

Custom classification workflow for HVAC systems with domain-specific logic:
- Compatibility matrices and sizing requirements
- Efficiency ratings and energy calculations  
- Safety compliance and code requirements
- BTU analysis and refrigerant compatibility

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
class HVACCompatibilityNode(SecureGovernedNode):
    """
    Custom node for HVAC system compatibility analysis.
    
    Analyzes BTU capacity, refrigerant compatibility, dimensional constraints,
    and system integration requirements for HVAC equipment.
    """
    
    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Define parameters for HVAC compatibility analysis."""
        return {
            "product_data": NodeParameter(
                name="product_data",
                type=dict,
                required=True,
                description="HVAC product specifications including BTU capacity, refrigerant type, dimensions"
            ),
            "system_requirements": NodeParameter(
                name="system_requirements", 
                type=dict,
                required=False,
                default={},
                description="System requirements including BTU needs, space constraints, refrigerant preferences"
            ),
            "efficiency_threshold": NodeParameter(
                name="efficiency_threshold",
                type=float,
                required=False,
                default=0.8,
                description="Minimum efficiency compatibility score (0.0-1.0)"
            ),
            "include_alternatives": NodeParameter(
                name="include_alternatives",
                type=bool,
                required=False,
                default=True,
                description="Include alternative compatible systems in analysis"
            )
        }
    
    def _run_implementation(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HVAC compatibility analysis."""
        product_data = inputs["product_data"]
        system_requirements = inputs.get("system_requirements", {})
        efficiency_threshold = inputs.get("efficiency_threshold", 0.8)
        include_alternatives = inputs.get("include_alternatives", True)
        
        # Analyze BTU capacity compatibility
        btu_analysis = self._analyze_btu_compatibility(product_data, system_requirements)
        
        # Check refrigerant compatibility
        refrigerant_analysis = self._check_refrigerant_compatibility(product_data, system_requirements)
        
        # Evaluate efficiency ratings
        efficiency_analysis = self._evaluate_efficiency_ratings(product_data, system_requirements)
        
        # Check dimensional constraints
        dimensional_analysis = self._check_dimensional_constraints(product_data, system_requirements)
        
        # Calculate overall compatibility score
        compatibility_score = self._calculate_compatibility_score([
            btu_analysis, refrigerant_analysis, efficiency_analysis, dimensional_analysis
        ])
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            product_data, system_requirements, compatibility_score, btu_analysis, 
            refrigerant_analysis, efficiency_analysis, dimensional_analysis
        )
        
        # Identify issues
        compatibility_issues = self._identify_compatibility_issues([
            btu_analysis, refrigerant_analysis, efficiency_analysis, dimensional_analysis
        ])
        
        result = {
            "compatibility_score": compatibility_score,
            "compatibility_issues": compatibility_issues,
            "recommendations": recommendations,
            "detailed_analysis": {
                "btu_compatibility": btu_analysis,
                "refrigerant_compatibility": refrigerant_analysis,
                "efficiency_analysis": efficiency_analysis,
                "dimensional_analysis": dimensional_analysis
            },
            "meets_threshold": compatibility_score >= efficiency_threshold,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # Include alternatives if requested
        if include_alternatives and compatibility_score < efficiency_threshold:
            result["alternatives"] = self._suggest_alternatives(product_data, system_requirements)
        
        return result
    
    def _analyze_btu_compatibility(self, product_data: Dict, requirements: Dict) -> Dict:
        """Analyze BTU capacity requirements and compatibility."""
        product_btu = product_data.get("btu_capacity", 0)
        required_btu = requirements.get("btu_requirement", 0)
        
        if required_btu == 0:
            return {"status": "no_requirement", "score": 0.5, "details": "No BTU requirement specified"}
        
        ratio = product_btu / required_btu if required_btu > 0 else 0
        
        if 0.95 <= ratio <= 1.15:  # Within 15% is excellent
            return {
                "status": "excellent", 
                "score": 1.0, 
                "ratio": ratio,
                "details": f"BTU capacity {product_btu} is optimal for requirement {required_btu}"
            }
        elif 0.85 <= ratio <= 1.25:  # Within 25% is acceptable
            return {
                "status": "acceptable", 
                "score": 0.7, 
                "ratio": ratio,
                "details": f"BTU capacity {product_btu} is within acceptable range for requirement {required_btu}"
            }
        elif ratio < 0.85:
            return {
                "status": "undersized", 
                "score": 0.2, 
                "ratio": ratio,
                "details": f"BTU capacity {product_btu} is insufficient for requirement {required_btu}"
            }
        else:  # ratio > 1.25
            return {
                "status": "oversized", 
                "score": 0.4, 
                "ratio": ratio,
                "details": f"BTU capacity {product_btu} is excessive for requirement {required_btu}"
            }
    
    def _check_refrigerant_compatibility(self, product_data: Dict, requirements: Dict) -> Dict:
        """Check refrigerant type compatibility with system requirements."""
        product_refrigerant = product_data.get("refrigerant_type", "").upper()
        required_refrigerant = requirements.get("refrigerant_type", "").upper()
        
        if not required_refrigerant:
            return {
                "status": "no_requirement", 
                "score": 0.5, 
                "details": "No refrigerant requirement specified"
            }
        
        if product_refrigerant == required_refrigerant:
            return {
                "status": "compatible", 
                "score": 1.0, 
                "details": f"Refrigerant {product_refrigerant} matches requirement exactly"
            }
        
        # Check for compatible alternatives
        compatible_alternatives = {
            "R-410A": ["R-32", "R-454B"],
            "R-22": ["R-407C", "R-422D"],  
            "R-134A": ["R-1234YF", "R-513A"]
        }
        
        if product_refrigerant in compatible_alternatives.get(required_refrigerant, []):
            return {
                "status": "alternative_compatible", 
                "score": 0.8,
                "details": f"Refrigerant {product_refrigerant} is compatible alternative to {required_refrigerant}"
            }
        
        # Check reverse compatibility
        for main_ref, alternatives in compatible_alternatives.items():
            if required_refrigerant == main_ref and product_refrigerant in alternatives:
                return {
                    "status": "reverse_compatible", 
                    "score": 0.7,
                    "details": f"Refrigerant {product_refrigerant} can work with {required_refrigerant} system"
                }
        
        return {
            "status": "incompatible", 
            "score": 0.0,
            "details": f"Refrigerant {product_refrigerant} is not compatible with {required_refrigerant}"
        }
    
    def _evaluate_efficiency_ratings(self, product_data: Dict, requirements: Dict) -> Dict:
        """Evaluate HVAC efficiency ratings and compliance."""
        seer_rating = product_data.get("seer_rating", 0)
        hspf_rating = product_data.get("hspf_rating", 0)
        
        min_seer = requirements.get("minimum_seer", 13.0)  # Minimum federal standard
        min_hspf = requirements.get("minimum_hspf", 7.7)   # Minimum federal standard
        
        seer_score = min(1.0, seer_rating / min_seer) if min_seer > 0 else 0.5
        hspf_score = min(1.0, hspf_rating / min_hspf) if min_hspf > 0 and hspf_rating > 0 else 0.5
        
        overall_score = (seer_score + hspf_score) / 2
        
        efficiency_level = "excellent" if overall_score >= 0.9 else \
                          "good" if overall_score >= 0.8 else \
                          "acceptable" if overall_score >= 0.7 else "poor"
        
        return {
            "score": overall_score,
            "efficiency_level": efficiency_level,
            "seer_analysis": {
                "rating": seer_rating,
                "minimum": min_seer,
                "score": seer_score,
                "meets_requirement": seer_rating >= min_seer
            },
            "hspf_analysis": {
                "rating": hspf_rating,
                "minimum": min_hspf,
                "score": hspf_score,
                "meets_requirement": hspf_rating >= min_hspf
            } if hspf_rating > 0 else None,
            "details": f"SEER {seer_rating} vs min {min_seer}, HSPF {hspf_rating} vs min {min_hspf}"
        }
    
    def _check_dimensional_constraints(self, product_data: Dict, requirements: Dict) -> Dict:
        """Check dimensional fit within space constraints."""
        dimensions = product_data.get("dimensions", {})
        constraints = requirements.get("space_constraints", {})
        
        if not constraints:
            return {
                "status": "no_constraints", 
                "score": 0.8, 
                "details": "No space constraints specified"
            }
        
        fit_issues = []
        dimension_scores = []
        
        for dimension in ["width", "height", "depth"]:
            product_dim = dimensions.get(dimension, 0)
            max_constraint = constraints.get(f"max_{dimension}", float('inf'))
            
            if product_dim > max_constraint:
                fit_issues.append(f"{dimension}: {product_dim} exceeds maximum {max_constraint}")
                dimension_scores.append(0.0)
            else:
                clearance_ratio = (max_constraint - product_dim) / max_constraint if max_constraint > 0 else 1.0
                dimension_scores.append(min(1.0, clearance_ratio + 0.5))  # Give credit for fitting
        
        overall_score = sum(dimension_scores) / len(dimension_scores) if dimension_scores else 0.8
        
        return {
            "score": overall_score,
            "status": "fits" if not fit_issues else "dimensional_issues",
            "fit_issues": fit_issues,
            "clearance_analysis": {
                dim: {
                    "product": dimensions.get(dim, 0),
                    "constraint": constraints.get(f"max_{dim}", "no limit"),
                    "fits": dimensions.get(dim, 0) <= constraints.get(f"max_{dim}", float('inf'))
                }
                for dim in ["width", "height", "depth"]
            },
            "details": f"Dimensional fit analysis: {len(fit_issues)} issues found"
        }
    
    def _calculate_compatibility_score(self, analyses: List[Dict]) -> float:
        """Calculate overall compatibility score from individual analyses."""
        total_score = 0.0
        weights = [0.3, 0.25, 0.25, 0.2]  # BTU, refrigerant, efficiency, dimensions
        
        for i, analysis in enumerate(analyses):
            weight = weights[i] if i < len(weights) else 0.25
            score = analysis.get("score", 0.0)
            total_score += score * weight
        
        return round(total_score, 3)
    
    def _identify_compatibility_issues(self, analyses: List[Dict]) -> List[str]:
        """Identify specific compatibility issues from analyses."""
        issues = []
        
        for analysis in analyses:
            if analysis.get("score", 1.0) < 0.7:  # Below acceptable threshold
                status = analysis.get("status", "unknown")
                details = analysis.get("details", "")
                
                if status in ["undersized", "oversized", "incompatible", "dimensional_issues"]:
                    issues.append(f"{status.replace('_', ' ').title()}: {details}")
                elif analysis.get("fit_issues"):
                    issues.extend(analysis["fit_issues"])
        
        return issues
    
    def _generate_recommendations(self, product_data: Dict, requirements: Dict, 
                                compatibility_score: float, *analyses) -> List[str]:
        """Generate recommendations based on compatibility analysis."""
        recommendations = []
        
        if compatibility_score >= 0.9:
            recommendations.append("Excellent compatibility - proceed with confidence")
        elif compatibility_score >= 0.8:
            recommendations.append("Good compatibility - suitable for installation")
        elif compatibility_score >= 0.7:
            recommendations.append("Acceptable compatibility - consider minor adjustments")
        else:
            recommendations.append("Poor compatibility - review requirements or consider alternatives")
        
        # Specific recommendations based on analyses
        btu_analysis, refrigerant_analysis, efficiency_analysis, dimensional_analysis = analyses
        
        if btu_analysis.get("status") == "undersized":
            recommendations.append("Consider higher BTU capacity unit for better performance")
        elif btu_analysis.get("status") == "oversized":
            recommendations.append("Unit may be oversized - could lead to short cycling and inefficiency")
        
        if refrigerant_analysis.get("status") == "incompatible":
            recommendations.append("Refrigerant incompatibility requires system modification or different unit")
        
        if efficiency_analysis.get("efficiency_level") == "poor":
            recommendations.append("Consider higher efficiency unit for better energy savings")
        
        if dimensional_analysis.get("fit_issues"):
            recommendations.append("Address dimensional constraints before installation")
        
        return recommendations
    
    def _suggest_alternatives(self, product_data: Dict, requirements: Dict) -> List[Dict]:
        """Suggest alternative HVAC systems that might be more compatible."""
        alternatives = []
        
        current_btu = product_data.get("btu_capacity", 0)
        required_btu = requirements.get("btu_requirement", current_btu)
        
        if current_btu < required_btu * 0.85:  # Undersized
            alternatives.append({
                "type": "higher_capacity",
                "suggestion": f"Consider {int(required_btu * 1.05)} BTU unit",
                "reason": "Better match for cooling/heating requirements"
            })
        
        if product_data.get("refrigerant_type") != requirements.get("refrigerant_type"):
            alternatives.append({
                "type": "refrigerant_compatible", 
                "suggestion": f"Look for {requirements.get('refrigerant_type', 'R-410A')} compatible unit",
                "reason": "Matches existing system refrigerant"
            })
        
        return alternatives


@register_node()
class HVACEfficiencyNode(SecureGovernedNode):
    """
    Custom node for HVAC efficiency analysis and energy calculations.
    
    Analyzes SEER ratings, HSPF ratings, Energy Star compliance,
    and calculates potential energy savings and operational costs.
    """
    
    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Define parameters for HVAC efficiency analysis."""
        return {
            "product_data": NodeParameter(
                name="product_data",
                type=dict,
                required=True,
                description="HVAC product with efficiency ratings (SEER, HSPF, Energy Star status)"
            ),
            "efficiency_requirements": NodeParameter(
                name="efficiency_requirements",
                type=dict,
                required=False,
                default={},
                description="Efficiency requirements and baseline for comparison"
            ),
            "energy_costs": NodeParameter(
                name="energy_costs",
                type=dict,
                required=False,
                default={"electricity": 0.12, "gas": 1.20},  # $/kWh, $/therm
                description="Local energy costs for savings calculations"
            ),
            "usage_hours": NodeParameter(
                name="usage_hours",
                type=int,
                required=False,
                default=2000,
                description="Annual usage hours for energy calculations"
            )
        }
    
    def _run_implementation(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HVAC efficiency analysis."""
        product_data = inputs["product_data"]
        requirements = inputs.get("efficiency_requirements", {})
        energy_costs = inputs.get("energy_costs", {"electricity": 0.12, "gas": 1.20})
        usage_hours = inputs.get("usage_hours", 2000)
        
        # Analyze SEER rating
        seer_analysis = self._analyze_seer_rating(product_data, requirements)
        
        # Analyze HSPF rating (for heat pumps)
        hspf_analysis = self._analyze_hspf_rating(product_data, requirements)
        
        # Calculate energy savings
        energy_savings = self._calculate_energy_savings(
            product_data, requirements, energy_costs, usage_hours
        )
        
        # Check Energy Star compliance
        energy_star_analysis = self._check_energy_star_compliance(product_data)
        
        # Overall efficiency rating
        efficiency_rating = self._calculate_efficiency_rating(
            seer_analysis, hspf_analysis, energy_star_analysis
        )
        
        return {
            "efficiency_rating": efficiency_rating,
            "energy_savings": energy_savings,
            "compliance_status": {
                "energy_star": energy_star_analysis,
                "federal_standards": self._check_federal_standards(product_data),
                "regional_standards": self._check_regional_standards(product_data, requirements)
            },
            "detailed_analysis": {
                "seer_analysis": seer_analysis,
                "hspf_analysis": hspf_analysis,
                "annual_cost_analysis": energy_savings.get("annual_costs", {}),
                "payback_analysis": energy_savings.get("payback_period", {})
            },
            "recommendations": self._generate_efficiency_recommendations(
                efficiency_rating, energy_savings, product_data
            )
        }
    
    def _analyze_seer_rating(self, product_data: Dict, requirements: Dict) -> Dict:
        """Analyze SEER (Seasonal Energy Efficiency Ratio) rating."""
        seer_rating = product_data.get("seer_rating", 0)
        min_seer = requirements.get("minimum_seer", 13.0)  # Federal minimum
        target_seer = requirements.get("target_seer", 16.0)  # Good efficiency target
        
        if seer_rating == 0:
            return {"status": "missing", "score": 0.0, "details": "SEER rating not provided"}
        
        efficiency_level = "excellent" if seer_rating >= 18 else \
                          "very_good" if seer_rating >= 16 else \
                          "good" if seer_rating >= 14 else \
                          "minimum" if seer_rating >= 13 else "below_standard"
        
        score = min(1.0, seer_rating / target_seer)
        
        return {
            "rating": seer_rating,
            "minimum_required": min_seer,
            "target": target_seer,
            "efficiency_level": efficiency_level,
            "score": score,
            "meets_minimum": seer_rating >= min_seer,
            "meets_target": seer_rating >= target_seer,
            "details": f"SEER {seer_rating} - {efficiency_level} efficiency level"
        }
    
    def _analyze_hspf_rating(self, product_data: Dict, requirements: Dict) -> Optional[Dict]:
        """Analyze HSPF (Heating Seasonal Performance Factor) rating for heat pumps."""
        hspf_rating = product_data.get("hspf_rating", 0)
        
        if hspf_rating == 0:
            return None  # Not a heat pump or rating not provided
        
        min_hspf = requirements.get("minimum_hspf", 7.7)  # Federal minimum
        target_hspf = requirements.get("target_hspf", 9.0)  # Good efficiency target
        
        efficiency_level = "excellent" if hspf_rating >= 10 else \
                          "very_good" if hspf_rating >= 9 else \
                          "good" if hspf_rating >= 8.5 else \
                          "minimum" if hspf_rating >= 7.7 else "below_standard"
        
        score = min(1.0, hspf_rating / target_hspf)
        
        return {
            "rating": hspf_rating,
            "minimum_required": min_hspf,
            "target": target_hspf,
            "efficiency_level": efficiency_level,
            "score": score,
            "meets_minimum": hspf_rating >= min_hspf,
            "meets_target": hspf_rating >= target_hspf,
            "details": f"HSPF {hspf_rating} - {efficiency_level} heating efficiency"
        }
    
    def _calculate_energy_savings(self, product_data: Dict, requirements: Dict, 
                                energy_costs: Dict, usage_hours: int) -> Dict:
        """Calculate energy savings compared to baseline or minimum standards."""
        current_seer = product_data.get("seer_rating", 13.0)
        baseline_seer = requirements.get("baseline_seer", 10.0)  # Old system comparison
        btu_capacity = product_data.get("btu_capacity", 24000)  # Default 2-ton unit
        
        # Calculate annual energy consumption (kWh)
        current_kwh = (btu_capacity * usage_hours) / (current_seer * 1000)  # Convert BTU to kWh
        baseline_kwh = (btu_capacity * usage_hours) / (baseline_seer * 1000)
        
        # Calculate costs
        electricity_cost = energy_costs.get("electricity", 0.12)
        current_annual_cost = current_kwh * electricity_cost
        baseline_annual_cost = baseline_kwh * electricity_cost
        
        annual_savings = baseline_annual_cost - current_annual_cost
        lifetime_savings = annual_savings * 15  # 15-year equipment life
        
        # Calculate payback period (assuming premium for high efficiency)
        efficiency_premium = requirements.get("efficiency_premium", 1000)  # Extra cost for efficiency
        payback_years = efficiency_premium / annual_savings if annual_savings > 0 else float('inf')
        
        return {
            "annual_savings": round(annual_savings, 2),
            "lifetime_savings": round(lifetime_savings, 2),
            "annual_costs": {
                "current_system": round(current_annual_cost, 2),
                "baseline_system": round(baseline_annual_cost, 2),
                "savings": round(annual_savings, 2)
            },
            "energy_consumption": {
                "current_kwh": round(current_kwh, 0),
                "baseline_kwh": round(baseline_kwh, 0),
                "savings_kwh": round(baseline_kwh - current_kwh, 0)
            },
            "payback_period": {
                "years": round(payback_years, 1) if payback_years != float('inf') else "N/A",
                "efficiency_premium": efficiency_premium,
                "is_cost_effective": payback_years <= 10
            }
        }
    
    def _check_energy_star_compliance(self, product_data: Dict) -> Dict:
        """Check Energy Star compliance and certification."""
        is_energy_star = product_data.get("energy_star", False)
        seer_rating = product_data.get("seer_rating", 0)
        hspf_rating = product_data.get("hspf_rating", 0)
        
        # Energy Star requirements vary by region and type
        energy_star_seer_min = 15.0  # Typical Energy Star requirement
        energy_star_hspf_min = 8.5   # Typical Energy Star requirement for heat pumps
        
        qualifies_by_rating = seer_rating >= energy_star_seer_min
        if hspf_rating > 0:
            qualifies_by_rating = qualifies_by_rating and hspf_rating >= energy_star_hspf_min
        
        return {
            "certified": is_energy_star,
            "qualifies_by_rating": qualifies_by_rating,
            "requirements": {
                "seer_minimum": energy_star_seer_min,
                "hspf_minimum": energy_star_hspf_min if hspf_rating > 0 else None
            },
            "status": "certified" if is_energy_star else 
                     "eligible" if qualifies_by_rating else "not_eligible"
        }
    
    def _check_federal_standards(self, product_data: Dict) -> Dict:
        """Check compliance with federal efficiency standards."""
        seer_rating = product_data.get("seer_rating", 0)
        hspf_rating = product_data.get("hspf_rating", 0)
        
        federal_seer_min = 13.0  # Federal minimum SEER
        federal_hspf_min = 7.7   # Federal minimum HSPF
        
        return {
            "seer_compliant": seer_rating >= federal_seer_min,
            "hspf_compliant": hspf_rating >= federal_hspf_min if hspf_rating > 0 else True,
            "overall_compliant": seer_rating >= federal_seer_min and 
                               (hspf_rating >= federal_hspf_min if hspf_rating > 0 else True),
            "requirements": {
                "seer_minimum": federal_seer_min,
                "hspf_minimum": federal_hspf_min
            }
        }
    
    def _check_regional_standards(self, product_data: Dict, requirements: Dict) -> Dict:
        """Check compliance with regional efficiency standards."""
        region = requirements.get("region", "national")
        seer_rating = product_data.get("seer_rating", 0)
        
        # Regional standards (simplified)
        regional_requirements = {
            "california": {"seer": 14.0, "name": "California Title 24"},
            "florida": {"seer": 14.0, "name": "Florida Energy Code"}, 
            "texas": {"seer": 14.0, "name": "Texas Energy Code"},
            "national": {"seer": 13.0, "name": "Federal Standard"}
        }
        
        regional_req = regional_requirements.get(region.lower(), regional_requirements["national"])
        
        return {
            "region": region,
            "standard_name": regional_req["name"],
            "seer_requirement": regional_req["seer"],
            "compliant": seer_rating >= regional_req["seer"],
            "details": f"{regional_req['name']} requires SEER {regional_req['seer']}, unit has {seer_rating}"
        }
    
    def _calculate_efficiency_rating(self, seer_analysis: Dict, hspf_analysis: Optional[Dict], 
                                   energy_star_analysis: Dict) -> Dict:
        """Calculate overall efficiency rating."""
        seer_score = seer_analysis.get("score", 0.0)
        hspf_score = hspf_analysis.get("score", 0.8) if hspf_analysis else 0.8  # Default for AC-only
        energy_star_bonus = 0.1 if energy_star_analysis.get("certified") else 0.0
        
        overall_score = (seer_score * 0.6 + hspf_score * 0.4) + energy_star_bonus
        overall_score = min(1.0, overall_score)  # Cap at 1.0
        
        rating_level = "excellent" if overall_score >= 0.9 else \
                      "very_good" if overall_score >= 0.8 else \
                      "good" if overall_score >= 0.7 else \
                      "acceptable" if overall_score >= 0.6 else "poor"
        
        return {
            "overall_score": round(overall_score, 3),
            "rating_level": rating_level,
            "components": {
                "seer_contribution": round(seer_score * 0.6, 3),
                "hspf_contribution": round(hspf_score * 0.4, 3),
                "energy_star_bonus": energy_star_bonus
            },
            "grade": "A+" if overall_score >= 0.95 else \
                    "A" if overall_score >= 0.9 else \
                    "B+" if overall_score >= 0.85 else \
                    "B" if overall_score >= 0.8 else \
                    "C+" if overall_score >= 0.75 else \
                    "C" if overall_score >= 0.7 else "D"
        }
    
    def _generate_efficiency_recommendations(self, efficiency_rating: Dict, 
                                           energy_savings: Dict, product_data: Dict) -> List[str]:
        """Generate efficiency-based recommendations."""
        recommendations = []
        
        rating_level = efficiency_rating.get("rating_level", "unknown")
        
        if rating_level == "excellent":
            recommendations.append("Outstanding efficiency choice - maximum energy savings")
        elif rating_level == "very_good":
            recommendations.append("Very good efficiency - excellent long-term value")
        elif rating_level == "good":  
            recommendations.append("Good efficiency choice - solid energy savings")
        elif rating_level == "acceptable":
            recommendations.append("Meets minimum standards - consider higher efficiency for better savings")
        else:
            recommendations.append("Below optimal efficiency - recommend upgrading to higher SEER/HSPF unit")
        
        # Payback analysis recommendations
        payback_years = energy_savings.get("payback_period", {}).get("years", "N/A")
        if isinstance(payback_years, (int, float)) and payback_years <= 5:
            recommendations.append("Excellent payback period - efficiency premium pays for itself quickly")
        elif isinstance(payback_years, (int, float)) and payback_years <= 10:
            recommendations.append("Good payback period - efficiency investment is cost-effective")
        
        # Energy Star recommendation
        if not product_data.get("energy_star", False):
            recommendations.append("Consider Energy Star certified unit for maximum efficiency and rebates")
        
        return recommendations


class HVACClassificationWorkflow:
    """
    Complete HVAC classification workflow combining compatibility and efficiency analysis.
    
    Uses Kailash SDK patterns with string-based nodes and WorkflowBuilder.
    Follows runtime.execute(workflow.build()) pattern for execution.
    """
    
    def __init__(self):
        self.workflow = WorkflowBuilder()
        self._setup_workflow()
    
    def _setup_workflow(self):
        """Setup HVAC classification workflow with string-based nodes."""
        
        # Standard UNSPSC classification
        self.workflow.add_node(
            "UNSPSCClassificationNode", "unspsc_classify",
            {
                "product_data": "${product_data}",
                "classification_system": "UNSPSC", 
                "domain": "HVAC",
                "confidence_threshold": 0.8
            }
        )
        
        # ETIM classification
        self.workflow.add_node(
            "ETIMClassificationNode", "etim_classify", 
            {
                "product_data": "${product_data}",
                "classification_system": "ETIM", 
                "domain": "HVAC",
                "language": "en"
            }
        )
        
        # Custom HVAC compatibility analysis
        self.workflow.add_node(
            "HVACCompatibilityNode", "hvac_compatibility",
            {
                "product_data": "${product_data}",
                "system_requirements": "${system_requirements}"
            }
        )
        
        # HVAC efficiency analysis
        self.workflow.add_node(
            "HVACEfficiencyNode", "hvac_efficiency",
            {
                "product_data": "${product_data}",
                "efficiency_requirements": "${efficiency_requirements}"
            }
        )
        
        # Safety compliance checking
        self.workflow.add_node(
            "SafetyComplianceNode", "safety_check",
            {
                "product_data": "${product_data}",
                "standards": ["OSHA", "NFPA", "UL"], 
                "domain": "HVAC"
            }
        )
        
        # Results aggregation
        self.workflow.add_node(
            "PythonCodeNode", "aggregate_results",
            {
                "code": '''
# Aggregate HVAC classification results
result = {
    "classification_result": {
        "unspsc": unspsc_classify,
        "etim": etim_classify,
        "hvac_compatibility": hvac_compatibility,
        "hvac_efficiency": hvac_efficiency,
        "safety_compliance": safety_check
    },
    "overall_score": (
        hvac_compatibility.get("compatibility_score", 0) * 0.4 +
        hvac_efficiency.get("efficiency_rating", {}).get("overall_score", 0) * 0.4 +
        (1.0 if safety_check.get("compliant", False) else 0.0) * 0.2
    ),
    "recommendations": []
}

# Combine recommendations
for component in [hvac_compatibility, hvac_efficiency, safety_check]:
    if isinstance(component, dict) and "recommendations" in component:
        result["recommendations"].extend(component["recommendations"])

result["workflow_type"] = "hvac_classification"
result["analysis_complete"] = True
                ''',
                "input_mapping": {
                    "unspsc_classify": "unspsc_classify.result",
                    "etim_classify": "etim_classify.result", 
                    "hvac_compatibility": "hvac_compatibility.result",
                    "hvac_efficiency": "hvac_efficiency.result",
                    "safety_check": "safety_check.result"
                }
            }
        )
    
    def classify_hvac_product(self, product_data: Dict[str, Any], 
                            system_requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute HVAC classification workflow using SDK patterns.
        
        Args:
            product_data: HVAC product specifications
            system_requirements: System installation and performance requirements
            
        Returns:
            Complete HVAC classification results with compatibility and efficiency analysis
        """
        from kailash.runtime.local import LocalRuntime
        
        runtime = LocalRuntime()
        
        # Prepare workflow inputs
        workflow_input = {
            "product_data": product_data,
            "system_requirements": system_requirements or {},
            "efficiency_requirements": system_requirements.get("efficiency_requirements", {}) if system_requirements else {}
        }
        
        # Execute workflow using SDK pattern: runtime.execute(workflow.build())
        results, run_id = runtime.execute(self.workflow.build(), workflow_input)
        
        return {
            "run_id": run_id,
            "classification_results": results,
            "workflow_type": "hvac_classification",
            "execution_timestamp": datetime.now().isoformat()
        }


# Workflow creation helper functions for easy usage
def create_hvac_classification_workflow(product_data: Dict[str, Any], **kwargs) -> WorkflowBuilder:
    """
    Create HVAC classification workflow using string-based node API.
    
    Returns WorkflowBuilder configured for HVAC classification.
    Must call .build() before execution with LocalRuntime.
    """
    workflow = WorkflowBuilder()
    
    # Add HVAC workflow nodes using string-based API
    workflow.add_node(
        "HVACCompatibilityNode", "hvac_compatibility",
        {
            "product_data": product_data,
            "system_requirements": kwargs.get("system_requirements", {}),
            "efficiency_threshold": kwargs.get("efficiency_threshold", 0.8)
        }
    )
    
    workflow.add_node(
        "HVACEfficiencyNode", "hvac_efficiency",
        {
            "product_data": product_data,
            "efficiency_requirements": kwargs.get("efficiency_requirements", {}),
            "energy_costs": kwargs.get("energy_costs", {"electricity": 0.12})
        }
    )
    
    return workflow


def execute_hvac_classification_example():
    """Example of proper SDK workflow execution pattern for HVAC."""
    # Test HVAC product data
    product_data = {
        "name": "Carrier 3-Ton Central Air Conditioner",
        "btu_capacity": 36000,
        "seer_rating": 16.0, 
        "refrigerant_type": "R-410A",
        "energy_star": True,
        "dimensions": {"width": 30, "height": 36, "depth": 24}
    }
    
    system_requirements = {
        "btu_requirement": 35000,
        "refrigerant_type": "R-410A",
        "minimum_seer": 15.0,
        "space_constraints": {"max_width": 32, "max_height": 38}
    }
    
    # Create and execute workflow
    workflow = HVACClassificationWorkflow()
    result = workflow.classify_hvac_product(product_data, system_requirements)
    
    return result