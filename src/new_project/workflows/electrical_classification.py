"""
Electrical Classification Workflow - AI-001 Custom Classification
===============================================================

Custom classification workflow for electrical components and systems:
- Voltage compatibility and electrical safety analysis
- NEC (National Electrical Code) compliance checking
- Circuit protection and load calculations
- UL listing and certification verification

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
class ElectricalSafetyNode(SecureGovernedNode):
    """
    Custom node for electrical safety and code compliance analysis.
    
    Analyzes voltage compatibility, amperage ratings, circuit protection,
    NEC compliance, and electrical safety certifications.
    """
    
    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Define parameters for electrical safety analysis."""
        return {
            "product_data": NodeParameter(
                name="product_data",
                type=dict,
                required=True,
                description="Electrical component specifications including voltage, amperage, certifications"
            ),
            "installation_context": NodeParameter(
                name="installation_context",
                type=dict,
                required=False,
                default={},
                description="Installation context including supply voltage, circuit type, location"
            ),
            "safety_standards": NodeParameter(
                name="safety_standards",
                type=list,
                required=False,
                default=["NEC", "UL", "OSHA"],
                description="Safety standards to check compliance against"
            ),
            "strict_compliance": NodeParameter(
                name="strict_compliance",
                type=bool,
                required=False,
                default=True,
                description="Whether to require strict compliance with all safety standards"
            )
        }
    
    def _run_implementation(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute electrical safety analysis."""
        product_data = inputs["product_data"]
        installation_context = inputs.get("installation_context", {})
        safety_standards = inputs.get("safety_standards", ["NEC", "UL", "OSHA"])
        strict_compliance = inputs.get("strict_compliance", True)
        
        # Analyze voltage compatibility
        voltage_analysis = self._analyze_voltage_compatibility(product_data, installation_context)
        
        # Check code compliance
        code_compliance = self._check_code_compliance(product_data, installation_context, safety_standards)
        
        # Verify certifications
        certification_analysis = self._verify_certifications(product_data)
        
        # Analyze circuit protection requirements
        circuit_protection = self._analyze_circuit_protection(product_data, installation_context)
        
        # Calculate overall safety rating
        safety_rating = self._calculate_safety_rating([
            voltage_analysis, code_compliance, certification_analysis, circuit_protection
        ])
        
        # Generate safety recommendations
        recommendations = self._generate_safety_recommendations(
            product_data, installation_context, voltage_analysis, 
            code_compliance, certification_analysis, circuit_protection
        )
        
        return {
            "safety_rating": safety_rating,
            "code_compliance": code_compliance,
            "voltage_compatibility": voltage_analysis,
            "certifications": certification_analysis,
            "circuit_protection": circuit_protection,
            "overall_compliant": safety_rating.get("compliant", False),
            "safety_issues": self._identify_safety_issues([
                voltage_analysis, code_compliance, certification_analysis, circuit_protection
            ]),
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _analyze_voltage_compatibility(self, product_data: Dict, installation_context: Dict) -> Dict:
        """Analyze voltage compatibility between product and installation."""
        product_voltage = product_data.get("voltage_rating", {})
        supply_voltage = installation_context.get("supply_voltage", {})
        
        if not supply_voltage:
            return {
                "status": "no_supply_voltage",
                "score": 0.5,
                "details": "Supply voltage not specified for analysis"
            }
        
        # Handle different voltage specification formats
        if isinstance(product_voltage, dict):
            min_voltage = product_voltage.get("min", 0)
            max_voltage = product_voltage.get("max", 0)
            nominal_voltage = product_voltage.get("nominal", (min_voltage + max_voltage) / 2)
        else:
            nominal_voltage = product_voltage
            min_voltage = nominal_voltage * 0.9  # Typical -10% tolerance
            max_voltage = nominal_voltage * 1.1  # Typical +10% tolerance
        
        supply_nominal = supply_voltage.get("nominal", supply_voltage.get("voltage", 0))
        
        if supply_nominal == 0:
            return {
                "status": "invalid_supply_voltage",
                "score": 0.0,
                "details": "Invalid or missing supply voltage specification"
            }
        
        # Check compatibility
        if min_voltage <= supply_nominal <= max_voltage:
            voltage_margin = min(
                (supply_nominal - min_voltage) / (max_voltage - min_voltage),
                (max_voltage - supply_nominal) / (max_voltage - min_voltage)
            )
            
            return {
                "status": "compatible",
                "score": 1.0,
                "voltage_margin": round(voltage_margin, 3),
                "product_range": {"min": min_voltage, "max": max_voltage, "nominal": nominal_voltage},
                "supply_voltage": supply_nominal,
                "details": f"Supply voltage {supply_nominal}V is within product range {min_voltage}-{max_voltage}V"
            }
        elif supply_nominal < min_voltage:
            undervoltage_percent = ((min_voltage - supply_nominal) / min_voltage) * 100
            return {
                "status": "undervoltage",
                "score": 0.1,
                "undervoltage_percent": round(undervoltage_percent, 1),
                "product_range": {"min": min_voltage, "max": max_voltage},
                "supply_voltage": supply_nominal,
                "details": f"Supply voltage {supply_nominal}V is {undervoltage_percent:.1f}% below minimum {min_voltage}V"
            }
        else:  # supply_nominal > max_voltage
            overvoltage_percent = ((supply_nominal - max_voltage) / max_voltage) * 100 if max_voltage > 0 else 100
            return {
                "status": "overvoltage",
                "score": 0.1,
                "overvoltage_percent": round(overvoltage_percent, 1),
                "product_range": {"min": min_voltage, "max": max_voltage},
                "supply_voltage": supply_nominal,
                "details": f"Supply voltage {supply_nominal}V is {overvoltage_percent:.1f}% above maximum {max_voltage}V"
            }
    
    def _check_code_compliance(self, product_data: Dict, installation_context: Dict, standards: List[str]) -> Dict:
        """Check compliance with electrical codes and standards."""
        compliance_results = {}
        overall_compliant = True
        
        # NEC (National Electrical Code) compliance
        if "NEC" in standards:
            nec_compliance = self._check_nec_compliance(product_data, installation_context)
            compliance_results["NEC"] = nec_compliance
            overall_compliant = overall_compliant and nec_compliance.get("compliant", False)
        
        # UL (Underwriters Laboratories) listing
        if "UL" in standards:
            ul_compliance = self._check_ul_listing(product_data)
            compliance_results["UL"] = ul_compliance
            overall_compliant = overall_compliant and ul_compliance.get("compliant", False)
        
        # OSHA electrical safety requirements
        if "OSHA" in standards:
            osha_compliance = self._check_osha_compliance(product_data, installation_context)
            compliance_results["OSHA"] = osha_compliance
            overall_compliant = overall_compliant and osha_compliance.get("compliant", False)
        
        return {
            "overall_compliant": overall_compliant,
            "standards_checked": standards,
            "detailed_compliance": compliance_results,
            "compliance_score": sum(
                result.get("score", 0) for result in compliance_results.values()
            ) / len(compliance_results) if compliance_results else 0.0
        }
    
    def _check_nec_compliance(self, product_data: Dict, installation_context: Dict) -> Dict:
        """Check National Electrical Code compliance."""
        issues = []
        score = 1.0
        
        # Check amperage and circuit protection
        amperage = product_data.get("amperage", 0)
        circuit_type = installation_context.get("circuit_type", "")
        location = installation_context.get("installation_location", "")
        
        # NEC Article 210 - Branch Circuits
        if amperage > 0:
            if amperage > 20 and circuit_type == "residential":
                issues.append("High amperage device may require special circuit in residential installation")
                score -= 0.2
        
        # NEC Article 404 - Switches (if applicable)
        if product_data.get("type", "").lower() in ["switch", "dimmer"]:
            if not product_data.get("nec_compliant", False):
                issues.append("Switch/dimmer should be NEC Article 404 compliant")
                score -= 0.3
        
        # NEC Article 406 - Receptacles (if applicable)
        if "outlet" in product_data.get("type", "").lower() or "receptacle" in product_data.get("type", "").lower():
            if location in ["bathroom", "kitchen", "outdoor", "garage"] and not product_data.get("gfci_protected", False):
                issues.append("GFCI protection required for this location per NEC Article 406")
                score -= 0.4
        
        # NEC Article 250 - Grounding
        if not product_data.get("grounding_compatible", True):
            issues.append("Device must be compatible with grounding requirements per NEC Article 250")
            score -= 0.3
        
        return {
            "compliant": len(issues) == 0,
            "score": max(0.0, score),
            "issues": issues,
            "articles_checked": ["210", "250", "404", "406"],
            "details": f"NEC compliance check found {len(issues)} issues"
        }
    
    def _check_ul_listing(self, product_data: Dict) -> Dict:
        """Check UL (Underwriters Laboratories) listing and certification."""
        ul_listed = product_data.get("ul_listed", False)
        ul_number = product_data.get("ul_number", "")
        
        if ul_listed and ul_number:
            return {
                "compliant": True,
                "score": 1.0,
                "ul_listed": True,
                "ul_number": ul_number,
                "details": f"Product is UL listed with number {ul_number}"
            }
        elif ul_listed:
            return {
                "compliant": True,
                "score": 0.9,
                "ul_listed": True,
                "ul_number": "Not provided",
                "details": "Product claims UL listing but no UL number provided"
            }
        else:
            return {
                "compliant": False,
                "score": 0.0,
                "ul_listed": False,
                "ul_number": None,
                "details": "Product is not UL listed - may not meet safety standards"
            }
    
    def _check_osha_compliance(self, product_data: Dict, installation_context: Dict) -> Dict:
        """Check OSHA electrical safety compliance."""
        issues = []
        score = 1.0
        
        # OSHA 1926.95 - Personal Protective Equipment
        if installation_context.get("work_environment") == "construction":
            if not product_data.get("lockout_tagout_compatible", False):
                issues.append("Device should support lockout/tagout procedures per OSHA 1926.95")
                score -= 0.2
        
        # OSHA 1910.303 - General electrical requirements
        voltage_rating = product_data.get("voltage_rating", {})
        if isinstance(voltage_rating, dict):
            max_voltage = voltage_rating.get("max", 0)
        else:
            max_voltage = voltage_rating
        
        if max_voltage > 600:
            if not product_data.get("high_voltage_qualified", False):
                issues.append("High voltage equipment requires qualified personnel per OSHA 1910.303")
                score -= 0.3
        
        # OSHA 1910.304 - Wiring design and protection
        if not product_data.get("overcurrent_protection", False):
            issues.append("Equipment should have overcurrent protection per OSHA 1910.304")
            score -= 0.2
        
        return {
            "compliant": len(issues) == 0,
            "score": max(0.0, score),
            "issues": issues,
            "sections_checked": ["1926.95", "1910.303", "1910.304"],
            "details": f"OSHA compliance check found {len(issues)} issues"
        }
    
    def _verify_certifications(self, product_data: Dict) -> Dict:
        """Verify electrical certifications and listings."""
        certifications = {
            "ul_listed": product_data.get("ul_listed", False),
            "csa_certified": product_data.get("csa_certified", False),
            "etl_listed": product_data.get("etl_listed", False),
            "ce_marked": product_data.get("ce_marked", False),
            "fcc_compliant": product_data.get("fcc_compliant", False)
        }
        
        # Calculate certification score
        total_certifications = len(certifications)
        active_certifications = sum(1 for cert in certifications.values() if cert)
        certification_score = active_certifications / total_certifications if total_certifications > 0 else 0.0
        
        # Determine certification level
        if active_certifications >= 3:
            cert_level = "excellent"
        elif active_certifications >= 2:
            cert_level = "good"
        elif active_certifications >= 1:
            cert_level = "basic"
        else:
            cert_level = "none"
        
        return {
            "certification_level": cert_level,
            "certification_score": certification_score,
            "certifications": certifications,
            "active_certifications": active_certifications,
            "total_possible": total_certifications,
            "minimum_met": active_certifications >= 1,  # At least one certification
            "details": f"Product has {active_certifications} of {total_certifications} possible certifications"
        }
    
    def _analyze_circuit_protection(self, product_data: Dict, installation_context: Dict) -> Dict:
        """Analyze circuit protection requirements and compatibility."""
        amperage = product_data.get("amperage", 0)
        voltage = product_data.get("voltage_rating", {})
        circuit_type = installation_context.get("circuit_type", "")
        
        if isinstance(voltage, dict):
            nominal_voltage = voltage.get("nominal", 120)
        else:
            nominal_voltage = voltage or 120
        
        # Calculate power consumption
        power_watts = amperage * nominal_voltage if amperage > 0 else product_data.get("power_watts", 0)
        
        # Determine required circuit breaker size
        if amperage > 0:
            # NEC 80% rule - circuit breaker should be 125% of continuous load
            required_breaker = amperage * 1.25
            
            # Standard breaker sizes
            standard_breakers = [15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100]
            recommended_breaker = next((size for size in standard_breakers if size >= required_breaker), 100)
        else:
            recommended_breaker = 15  # Default for low-power devices
        
        # Check GFCI requirements
        location = installation_context.get("installation_location", "")
        gfci_locations = ["bathroom", "kitchen", "outdoor", "garage", "basement", "laundry"]
        gfci_required = any(loc in location.lower() for loc in gfci_locations)
        gfci_compatible = product_data.get("gfci_compatible", True)
        
        # Check AFCI requirements
        afci_required = circuit_type == "residential" and location in ["bedroom", "living_room", "family_room"]
        afci_compatible = product_data.get("afci_compatible", True)
        
        protection_issues = []
        if gfci_required and not gfci_compatible:
            protection_issues.append("GFCI protection required but device not compatible")
        if afci_required and not afci_compatible:
            protection_issues.append("AFCI protection required but device not compatible")
        
        protection_score = 1.0 if not protection_issues else 0.3
        
        return {
            "required_breaker_size": recommended_breaker,
            "calculated_amperage": amperage,
            "power_consumption": power_watts,
            "gfci_required": gfci_required,
            "gfci_compatible": gfci_compatible,
            "afci_required": afci_required,
            "afci_compatible": afci_compatible,
            "protection_issues": protection_issues,
            "protection_score": protection_score,
            "details": f"Requires {recommended_breaker}A breaker, GFCI: {gfci_required}, AFCI: {afci_required}"
        }
    
    def _calculate_safety_rating(self, analyses: List[Dict]) -> Dict:
        """Calculate overall safety rating from individual analyses."""
        voltage_analysis, code_compliance, certification_analysis, circuit_protection = analyses
        
        # Weighted scoring
        voltage_score = voltage_analysis.get("score", 0.0) * 0.3
        code_score = code_compliance.get("compliance_score", 0.0) * 0.4
        cert_score = certification_analysis.get("certification_score", 0.0) * 0.2
        protection_score = circuit_protection.get("protection_score", 0.0) * 0.1
        
        overall_score = voltage_score + code_score + cert_score + protection_score
        
        # Determine safety level
        if overall_score >= 0.9:
            safety_level = "excellent"
        elif overall_score >= 0.8:
            safety_level = "very_good"
        elif overall_score >= 0.7:
            safety_level = "good"
        elif overall_score >= 0.6:
            safety_level = "acceptable"
        else:
            safety_level = "poor"
        
        # Overall compliance check
        overall_compliant = (
            voltage_analysis.get("status") == "compatible" and
            code_compliance.get("overall_compliant", False) and
            certification_analysis.get("minimum_met", False) and
            not circuit_protection.get("protection_issues")
        )
        
        return {
            "overall_score": round(overall_score, 3),
            "safety_level": safety_level,
            "compliant": overall_compliant,
            "component_scores": {
                "voltage": voltage_score,
                "code_compliance": code_score, 
                "certifications": cert_score,
                "circuit_protection": protection_score
            },
            "grade": "A" if overall_score >= 0.9 else \
                    "B" if overall_score >= 0.8 else \
                    "C" if overall_score >= 0.7 else \
                    "D" if overall_score >= 0.6 else "F"
        }
    
    def _identify_safety_issues(self, analyses: List[Dict]) -> List[str]:
        """Identify all safety issues from analyses."""
        issues = []
        
        voltage_analysis, code_compliance, certification_analysis, circuit_protection = analyses
        
        # Voltage issues
        if voltage_analysis.get("status") in ["undervoltage", "overvoltage"]:
            issues.append(f"Voltage compatibility issue: {voltage_analysis.get('details')}")
        
        # Code compliance issues
        for standard, compliance in code_compliance.get("detailed_compliance", {}).items():
            if not compliance.get("compliant", False):
                issues.extend([f"{standard}: {issue}" for issue in compliance.get("issues", [])])
        
        # Certification issues
        if not certification_analysis.get("minimum_met", False):
            issues.append("No recognized electrical certifications (UL, CSA, ETL)")
        
        # Circuit protection issues
        issues.extend(circuit_protection.get("protection_issues", []))
        
        return issues
    
    def _generate_safety_recommendations(self, product_data: Dict, installation_context: Dict,
                                       voltage_analysis: Dict, code_compliance: Dict,
                                       certification_analysis: Dict,
                                       circuit_protection: Dict) -> List[str]:
        """Generate safety recommendations based on analysis."""
        recommendations = []
        
        safety_level = self._calculate_safety_rating([
            voltage_analysis, code_compliance, certification_analysis, circuit_protection
        ]).get("safety_level", "unknown")
        
        if safety_level == "excellent":
            recommendations.append("Excellent electrical safety profile - suitable for installation")
        elif safety_level in ["very_good", "good"]:
            recommendations.append("Good electrical safety profile - minor considerations noted below")
        else:
            recommendations.append("Safety concerns identified - address issues before installation")
        
        # Voltage-specific recommendations
        if voltage_analysis.get("status") == "undervoltage":
            recommendations.append("Install voltage booster or use higher voltage supply")
        elif voltage_analysis.get("status") == "overvoltage":
            recommendations.append("Install voltage regulator or use lower voltage supply")
        
        # Code compliance recommendations
        if not code_compliance.get("overall_compliant", False):
            recommendations.append("Address code compliance issues before installation")
            for standard, compliance in code_compliance.get("detailed_compliance", {}).items():
                if not compliance.get("compliant", False):
                    recommendations.append(f"Review {standard} requirements and ensure compliance")
        
        # Certification recommendations
        if not certification_analysis.get("minimum_met", False):
            recommendations.append("Use only certified electrical equipment (UL, CSA, or ETL listed)")
        
        # Circuit protection recommendations
        required_breaker = circuit_protection.get("required_breaker_size", 15)
        recommendations.append(f"Install {required_breaker}A circuit breaker for proper protection")
        
        if circuit_protection.get("gfci_required", False):
            recommendations.append("Install GFCI protection for this location")
        
        if circuit_protection.get("afci_required", False):
            recommendations.append("Install AFCI protection per NEC requirements")
        
        return recommendations


class ElectricalClassificationWorkflow:
    """
    Complete electrical classification workflow combining safety analysis with standard classification.
    
    Uses Kailash SDK patterns with string-based nodes and WorkflowBuilder.
    Follows runtime.execute(workflow.build()) pattern for execution.
    """
    
    def __init__(self):
        self.workflow = WorkflowBuilder()
        self._setup_workflow()
    
    def _setup_workflow(self):
        """Setup electrical classification workflow with string-based nodes."""
        
        # Standard UNSPSC classification
        self.workflow.add_node(
            "UNSPSCClassificationNode", "unspsc_classify",
            {
                "product_data": "${product_data}",
                "classification_system": "UNSPSC", 
                "domain": "electrical",
                "confidence_threshold": 0.8
            }
        )
        
        # ETIM classification
        self.workflow.add_node(
            "ETIMClassificationNode", "etim_classify", 
            {
                "product_data": "${product_data}",
                "classification_system": "ETIM", 
                "domain": "electrical",
                "language": "en"
            }
        )
        
        # Custom electrical safety analysis
        self.workflow.add_node(
            "ElectricalSafetyNode", "electrical_safety",
            {
                "product_data": "${product_data}",
                "installation_context": "${installation_context}",
                "safety_standards": ["NEC", "UL", "OSHA"]
            }
        )
        
        # Safety compliance checking
        self.workflow.add_node(
            "SafetyComplianceNode", "safety_compliance",
            {
                "product_data": "${product_data}",
                "standards": ["NEC", "UL", "OSHA", "IEC"], 
                "domain": "electrical"
            }
        )
        
        # Results aggregation
        self.workflow.add_node(
            "PythonCodeNode", "aggregate_results",
            {
                "code": '''
# Aggregate electrical classification results
result = {
    "classification_result": {
        "unspsc": unspsc_classify,
        "etim": etim_classify,
        "electrical_safety": electrical_safety,
        "safety_compliance": safety_compliance
    },
    "overall_score": (
        electrical_safety.get("safety_rating", {}).get("overall_score", 0) * 0.6 +
        (1.0 if safety_compliance.get("compliant", False) else 0.0) * 0.4
    ),
    "recommendations": []
}

# Combine recommendations
for component in [electrical_safety, safety_compliance]:
    if isinstance(component, dict) and "recommendations" in component:
        result["recommendations"].extend(component["recommendations"])

result["workflow_type"] = "electrical_classification"
result["analysis_complete"] = True
                ''',
                "input_mapping": {
                    "unspsc_classify": "unspsc_classify.result",
                    "etim_classify": "etim_classify.result", 
                    "electrical_safety": "electrical_safety.result",
                    "safety_compliance": "safety_compliance.result"
                }
            }
        )
    
    def classify_electrical_component(self, product_data: Dict[str, Any], 
                                    installation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute electrical classification workflow using SDK patterns.
        
        Args:
            product_data: Electrical component specifications
            installation_context: Installation environment and requirements
            
        Returns:
            Complete electrical classification results with safety analysis
        """
        from kailash.runtime.local import LocalRuntime
        
        runtime = LocalRuntime()
        
        # Prepare workflow inputs
        workflow_input = {
            "product_data": product_data,
            "installation_context": installation_context or {}
        }
        
        # Execute workflow using SDK pattern: runtime.execute(workflow.build())
        results, run_id = runtime.execute(self.workflow.build(), workflow_input)
        
        return {
            "run_id": run_id,
            "classification_results": results,
            "workflow_type": "electrical_classification",
            "execution_timestamp": datetime.now().isoformat()
        }


# Workflow creation helper functions
def create_electrical_classification_workflow(product_data: Dict[str, Any], **kwargs) -> WorkflowBuilder:
    """
    Create electrical classification workflow using string-based node API.
    
    Returns WorkflowBuilder configured for electrical classification.
    Must call .build() before execution with LocalRuntime.
    """
    workflow = WorkflowBuilder()
    
    # Add electrical workflow nodes using string-based API
    workflow.add_node(
        "ElectricalSafetyNode", "electrical_safety",
        {
            "product_data": product_data,
            "installation_context": kwargs.get("installation_context", {}),
            "safety_standards": kwargs.get("safety_standards", ["NEC", "UL", "OSHA"])
        }
    )
    
    return workflow


def execute_electrical_classification_example():
    """Example of proper SDK workflow execution pattern for electrical components."""
    # Test electrical component data
    product_data = {
        "name": "Square D 20A GFCI Circuit Breaker",
        "type": "circuit_breaker",
        "voltage_rating": {"min": 110, "max": 125, "nominal": 120},
        "amperage": 20,
        "ul_listed": True,
        "ul_number": "E12345",
        "nec_compliant": True,
        "gfci_protected": True,
        "grounding_compatible": True
    }
    
    installation_context = {
        "supply_voltage": {"nominal": 120},
        "circuit_type": "residential",
        "installation_location": "bathroom",
        "work_environment": "residential"
    }
    
    # Create and execute workflow
    workflow = ElectricalClassificationWorkflow()
    result = workflow.classify_electrical_component(product_data, installation_context)
    
    return result