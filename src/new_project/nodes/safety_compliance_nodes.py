"""
Safety Compliance Validation Nodes for Kailash SDK
=================================================

Implements safety compliance validation using proper Kailash SDK patterns.
Uses ValidationNode patterns for real compliance checking with no mocking.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash.nodes.base import Node, register_node, NodeParameter


class ComplianceLevel(Enum):
    """Safety compliance levels"""
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    ADVISORY = "advisory"
    INFORMATIONAL = "informational"


class RiskLevel(Enum):
    """Safety risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class SafetyRequirement:
    """Single safety requirement specification"""
    requirement_id: str
    standard_id: str
    title: str
    description: str
    compliance_level: ComplianceLevel
    risk_level: RiskLevel
    applicable_environments: List[str]
    applicable_skill_levels: List[str]
    verification_method: str
    legal_reference: str
    enforcement_authority: str


@dataclass
class ComplianceValidationResult:
    """Result of safety compliance validation"""
    product_code: str
    user_skill_level: str
    environment: str
    compliance_status: str
    applicable_requirements: List[SafetyRequirement]
    violations: List[Dict[str, Any]]
    warnings: List[str]
    recommendations: List[str]
    risk_assessment: Dict[str, Any]
    legal_notes: List[str]
    validation_timestamp: datetime
    validator_version: str


@register_node()
class SafetyRequirementFilterNode(Node):
    """Node for filtering safety requirements based on context"""
    
    def get_parameters(self) -> Dict[str, NodeParameter]:
        return {
            "product_category": NodeParameter(
                name="product_category",
                type=str,
                required=True,
                description="Category of the product being evaluated"
            ),
            "user_skill_level": NodeParameter(
                name="user_skill_level",
                type=str,
                required=True,
                description="Skill level of the user (novice, intermediate, advanced, expert)"
            ),
            "environment": NodeParameter(
                name="environment",
                type=str,
                required=True,
                description="Environment where the product will be used"
            ),
            "safety_requirements": NodeParameter(
                name="safety_requirements",
                type=list,
                required=True,
                description="List of safety requirements to filter"
            )
        }
    
    def run(self, inputs: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Filter safety requirements based on context"""
        
        # Handle both calling patterns: inputs dict or individual kwargs
        if inputs is not None:
            # Dictionary pattern
            product_category = inputs["product_category"]
            user_skill_level = inputs["user_skill_level"]
            environment = inputs["environment"]
            safety_requirements = inputs["safety_requirements"]
        else:
            # Keyword arguments pattern
            product_category = kwargs["product_category"]
            user_skill_level = kwargs["user_skill_level"]
            environment = kwargs["environment"]
            safety_requirements = kwargs["safety_requirements"]
        
        # Convert dict requirements back to SafetyRequirement objects
        requirements = []
        for req_dict in safety_requirements:
            req = SafetyRequirement(
                requirement_id=req_dict["requirement_id"],
                standard_id=req_dict["standard_id"],
                title=req_dict["title"],
                description=req_dict["description"],
                compliance_level=ComplianceLevel(req_dict["compliance_level"]),
                risk_level=RiskLevel(req_dict["risk_level"]),
                applicable_environments=req_dict["applicable_environments"],
                applicable_skill_levels=req_dict["applicable_skill_levels"],
                verification_method=req_dict["verification_method"],
                legal_reference=req_dict["legal_reference"],
                enforcement_authority=req_dict["enforcement_authority"]
            )
            requirements.append(req)
        
        applicable = []
        
        for requirement in requirements:
            # Check environment applicability
            if (environment in requirement.applicable_environments or 
                "all" in requirement.applicable_environments):
                
                # Check skill level applicability
                if (user_skill_level in requirement.applicable_skill_levels or 
                    "all" in requirement.applicable_skill_levels):
                    
                    applicable.append(requirement)
        
        # Sort by compliance level and risk level
        def sort_key(req):
            compliance_priority = {
                ComplianceLevel.MANDATORY: 0,
                ComplianceLevel.RECOMMENDED: 1,
                ComplianceLevel.ADVISORY: 2,
                ComplianceLevel.INFORMATIONAL: 3
            }
            risk_priority = {
                RiskLevel.CRITICAL: 0,
                RiskLevel.HIGH: 1,
                RiskLevel.MEDIUM: 2,
                RiskLevel.LOW: 3,
                RiskLevel.MINIMAL: 4
            }
            return (compliance_priority[req.compliance_level], risk_priority[req.risk_level])
        
        applicable.sort(key=sort_key)
        
        # Convert requirements to JSON-serializable dictionaries
        def req_to_dict(req):
            return {
                "requirement_id": req.requirement_id,
                "standard_id": req.standard_id,
                "title": req.title,
                "description": req.description,
                "compliance_level": req.compliance_level.value,  # Convert Enum to string
                "risk_level": req.risk_level.value,  # Convert Enum to string
                "applicable_environments": req.applicable_environments,
                "applicable_skill_levels": req.applicable_skill_levels,
                "verification_method": req.verification_method,
                "legal_reference": req.legal_reference,
                "enforcement_authority": req.enforcement_authority
            }
        
        return {
            "applicable_requirements": [req_to_dict(req) for req in applicable],
            "filtered_count": len(applicable),
            "total_count": len(requirements)
        }


@register_node()
class LockoutTagoutValidationNode(Node):
    """Specialized validation for lockout/tagout requirements"""
    
    def get_parameters(self) -> Dict[str, NodeParameter]:
        return {
            "product_category": NodeParameter(
                name="product_category",
                type=str,
                required=True,
                description="Category of the product being evaluated"
            ),
            "user_skill_level": NodeParameter(
                name="user_skill_level",
                type=str,
                required=True,
                description="Skill level of the user"
            ),
            "environment": NodeParameter(
                name="environment",
                type=str,
                required=True,
                description="Environment where the product will be used"
            ),
            "applicable_requirements": NodeParameter(
                name="applicable_requirements",
                type=list,
                required=True,
                description="List of applicable safety requirements"
            )
        }
    
    def run(self, inputs: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Validate lockout/tagout requirements"""
        
        # Handle both calling patterns: inputs dict or individual kwargs
        if inputs is not None:
            # Dictionary pattern
            product_category = inputs["product_category"]
            user_skill_level = inputs["user_skill_level"]
            environment = inputs["environment"]
            applicable_requirements = inputs["applicable_requirements"]
        else:
            # Keyword arguments pattern
            product_category = kwargs["product_category"]
            user_skill_level = kwargs["user_skill_level"]
            environment = kwargs["environment"]
            applicable_requirements = kwargs["applicable_requirements"]
        
        # Check if LOTO is required for this scenario
        loto_environments = ["industrial", "manufacturing", "electrical"]
        loto_skill_levels = ["intermediate", "advanced", "expert"]  # More experienced users work with equipment requiring LOTO
        
        should_have_loto = (environment in loto_environments and 
                           user_skill_level in loto_skill_levels and
                           product_category == "Power Tools")
        
        # Find existing LOTO requirements
        loto_requirements = []
        for req_dict in applicable_requirements:
            desc_lower = req_dict["description"].lower()
            title_lower = req_dict["title"].lower()
            if ("lockout" in desc_lower or "tagout" in desc_lower or 
                "lockout" in title_lower or "tagout" in title_lower or
                "energy isolation" in desc_lower):
                loto_requirements.append(req_dict)
        
        violations = []
        warnings = []
        recommendations = []
        
        if should_have_loto and not loto_requirements:
            # Add missing LOTO requirement
            missing_loto = {
                "requirement_id": "OSHA-1910-147-001",
                "standard_id": "OSHA-1910.147",
                "title": "Lockout/Tagout Required",
                "description": "Energy isolation required before equipment maintenance",
                "compliance_level": "mandatory",
                "risk_level": "critical",
                "applicable_environments": ["industrial", "manufacturing", "electrical"],
                "applicable_skill_levels": ["intermediate", "advanced", "expert"],
                "verification_method": "Energy isolation verification",
                "legal_reference": "29 CFR 1910.147",
                "enforcement_authority": "OSHA"
            }
            loto_requirements.append(missing_loto)
            warnings.append("Lockout/Tagout procedures required for maintenance work in industrial environments")
            recommendations.append("Implement OSHA 1910.147 lockout/tagout procedures")
        
        return {
            "validation_passed": len(loto_requirements) > 0 if should_have_loto else True,
            "loto_requirements": loto_requirements,
            "should_have_loto": should_have_loto,
            "violations": violations,
            "warnings": warnings,
            "recommendations": recommendations
        }


@register_node()
class NoviceUserSafetyValidationNode(Node):
    """Specialized validation for novice user safety restrictions"""
    
    def get_parameters(self) -> Dict[str, NodeParameter]:
        return {
            "product_category": NodeParameter(
                name="product_category",
                type=str,
                required=True,
                description="Category of the product being evaluated"
            ),
            "user_skill_level": NodeParameter(
                name="user_skill_level",
                type=str,
                required=True,
                description="Skill level of the user"
            ),
            "environment": NodeParameter(
                name="environment",
                type=str,
                required=True,
                description="Environment where the product will be used"
            ),
            "applicable_requirements": NodeParameter(
                name="applicable_requirements",
                type=list,
                required=True,
                description="List of applicable safety requirements"
            )
        }
    
    def run(self, inputs: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Validate novice user safety restrictions"""
        
        # Handle both calling patterns: inputs dict or individual kwargs
        if inputs is not None:
            # Dictionary pattern
            product_category = inputs["product_category"]
            user_skill_level = inputs["user_skill_level"]
            environment = inputs["environment"]
            applicable_requirements = inputs["applicable_requirements"]
        else:
            # Keyword arguments pattern
            product_category = kwargs["product_category"]
            user_skill_level = kwargs["user_skill_level"]
            environment = kwargs["environment"]
            applicable_requirements = kwargs["applicable_requirements"]
        
        violations = []
        warnings = []
        recommendations = []
        
        # Novice users need additional safety measures
        if user_skill_level == "novice":
            # High-risk scenarios for novice users
            high_risk_tools = ["Power Tools"]
            high_risk_environments = ["workshop", "industrial", "construction", "electrical"]
            
            if product_category in high_risk_tools:
                warnings.append("Novice users require supervision when using power tools")
                warnings.append("Additional safety training required before operation")
                recommendations.append("Complete basic safety certification before using power tools")
                recommendations.append("Ensure qualified supervision is available during operation")
                
            if environment in high_risk_environments:
                warnings.append("Heightened safety awareness required for novice users in this environment")
                recommendations.append("Review environment-specific safety procedures")
                recommendations.append("Identify emergency exits and safety equipment locations")
            
            # Add specific novice restrictions
            if product_category == "Power Tools" and environment == "workshop":
                warnings.append("Power tool operation restricted without supervision for novice users")
                warnings.append("Mandatory PPE verification required before operation")
                recommendations.append("Verify proper safety glasses and hearing protection")
                recommendations.append("Review tool-specific operating procedures")
        
        return {
            "validation_passed": True,  # Warnings don't fail validation
            "is_novice": user_skill_level == "novice",
            "warnings_generated": len(warnings),
            "violations": violations,
            "warnings": warnings,
            "recommendations": recommendations
        }


@register_node()
class CriticalWarningIdentificationNode(Node):
    """Node for identifying critical safety warnings"""
    
    def get_parameters(self) -> Dict[str, NodeParameter]:
        return {
            "product_category": NodeParameter(
                name="product_category",
                type=str,
                required=True,
                description="Category of the product being evaluated"
            ),
            "user_skill_level": NodeParameter(
                name="user_skill_level",
                type=str,
                required=True,
                description="Skill level of the user"
            ),
            "environment": NodeParameter(
                name="environment",
                type=str,
                required=True,
                description="Environment where the product will be used"
            ),
            "applicable_requirements": NodeParameter(
                name="applicable_requirements",
                type=list,
                required=True,
                description="List of applicable safety requirements"
            )
        }
    
    def run(self, inputs: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Identify critical safety warnings"""
        
        # Handle both calling patterns: inputs dict or individual kwargs
        if inputs is not None:
            # Dictionary pattern
            product_category = inputs["product_category"]
            user_skill_level = inputs["user_skill_level"]
            environment = inputs["environment"]
            applicable_requirements = inputs["applicable_requirements"]
        else:
            # Keyword arguments pattern
            product_category = kwargs["product_category"]
            user_skill_level = kwargs["user_skill_level"]
            environment = kwargs["environment"]
            applicable_requirements = kwargs["applicable_requirements"]
        
        high_risk_requirements = []
        critical_scenarios = []
        
        # Check for high-risk combinations
        risk_combinations = [
            ("Power Tools", "novice", "electrical"),
            ("Power Tools", "novice", "industrial"),
            ("Safety Equipment", "intermediate", "construction"),
            ("Power Tools", "advanced", "industrial")
        ]
        
        current_combination = (product_category, user_skill_level, environment)
        
        # Add critical requirements for high-risk scenarios
        if current_combination in risk_combinations:
            # Always add electrical safety for electrical environments
            if environment == "electrical":
                electrical_req = {
                    "requirement_id": "NFPA-70E-001",
                    "standard_id": "NFPA-70E",
                    "title": "Arc Flash Protection",
                    "description": "Arc-rated PPE required for electrical work",
                    "compliance_level": "mandatory",
                    "risk_level": "critical",
                    "applicable_environments": ["electrical", "industrial"],
                    "applicable_skill_levels": ["intermediate", "advanced", "expert"],
                    "verification_method": "Arc flash analysis",
                    "legal_reference": "NFPA 70E-2021",
                    "enforcement_authority": "NFPA"
                }
                high_risk_requirements.append(electrical_req)
                critical_scenarios.append("Electrical work requires arc flash protection")
            
            # Add novice-specific critical requirements
            if user_skill_level == "novice":
                novice_critical_req = {
                    "requirement_id": "OSHA-NOVICE-001",
                    "standard_id": "OSHA-SUPERVISION",
                    "title": "Novice User Supervision Required",
                    "description": "Continuous supervision required for novice users with power tools",
                    "compliance_level": "mandatory",
                    "risk_level": "high",
                    "applicable_environments": ["all"],
                    "applicable_skill_levels": ["novice"],
                    "verification_method": "Supervisor presence verification",
                    "legal_reference": "OSHA General Duty Clause",
                    "enforcement_authority": "OSHA"
                }
                high_risk_requirements.append(novice_critical_req)
                critical_scenarios.append("Novice users require supervision with power tools")
        
        # Filter existing requirements for high/critical risk
        for req_dict in applicable_requirements:
            if req_dict["risk_level"] in ["critical", "high"]:
                high_risk_requirements.append(req_dict)
        
        return {
            "validation_passed": len(high_risk_requirements) > 0,
            "high_risk_count": len(high_risk_requirements),
            "critical_scenarios": critical_scenarios,
            "high_risk_requirements": high_risk_requirements
        }


@register_node()
class SafetyComplianceWorkflowNode(Node):
    """Main workflow node that orchestrates safety compliance validation"""
    
    def get_parameters(self) -> Dict[str, NodeParameter]:
        return {
            "product_code": NodeParameter(
                name="product_code",
                type=str,
                required=True,
                description="Product code or identifier"
            ),
            "product_category": NodeParameter(
                name="product_category",
                type=str,
                required=True,
                description="Category of the product being evaluated"
            ),
            "user_skill_level": NodeParameter(
                name="user_skill_level",
                type=str,
                required=True,
                description="Skill level of the user"
            ),
            "environment": NodeParameter(
                name="environment",
                type=str,
                required=True,
                description="Environment where the product will be used"
            )
        }
    
    def run(self, inputs: Dict[str, Any] = None, **kwargs) -> ComplianceValidationResult:
        """Run complete safety compliance validation workflow"""
        
        # Handle both calling patterns: inputs dict or individual kwargs
        if inputs is not None:
            # Dictionary pattern
            product_code = inputs["product_code"]
            product_category = inputs["product_category"]
            user_skill_level = inputs["user_skill_level"]
            environment = inputs["environment"]
        else:
            # Keyword arguments pattern
            product_code = kwargs["product_code"]
            product_category = kwargs["product_category"]
            user_skill_level = kwargs["user_skill_level"]
            environment = kwargs["environment"]
        """Run complete safety compliance validation workflow"""
        
        # Create safety requirements database
        safety_requirements = self._get_safety_requirements()
        
        # Build validation workflow using Kailash SDK patterns
        workflow = WorkflowBuilder()
        
        # Add requirement filtering node
        workflow.add_node("SafetyRequirementFilterNode", "filter", {
            "product_category": product_category,
            "user_skill_level": user_skill_level,
            "environment": environment,
            "safety_requirements": [asdict(req) for req in safety_requirements]
        })
        
        # Add specialized validation nodes
        workflow.add_node("LockoutTagoutValidationNode", "loto_validator", {
            "product_category": product_category,
            "user_skill_level": user_skill_level,
            "environment": environment
        })
        
        workflow.add_node("NoviceUserSafetyValidationNode", "novice_validator", {
            "product_category": product_category,
            "user_skill_level": user_skill_level,
            "environment": environment
        })
        
        workflow.add_node("CriticalWarningIdentificationNode", "critical_validator", {
            "product_category": product_category,
            "user_skill_level": user_skill_level,
            "environment": environment
        })
        
        # Connect the workflow - CRITICAL: Use 4-parameter connections
        workflow.add_connection("filter", "applicable_requirements", "loto_validator", "applicable_requirements")
        workflow.add_connection("filter", "applicable_requirements", "novice_validator", "applicable_requirements")
        workflow.add_connection("filter", "applicable_requirements", "critical_validator", "applicable_requirements")
        
        # Execute workflow using proper Kailash pattern
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        
        # Aggregate results
        filter_result = results["filter"]
        loto_result = results["loto_validator"]
        novice_result = results["novice_validator"]
        critical_result = results["critical_validator"]
        
        # Combine all requirements (including added ones)
        all_requirements = []
        all_requirements.extend(filter_result["applicable_requirements"])
        
        # Add requirements from validators
        if loto_result["loto_requirements"]:
            for req in loto_result["loto_requirements"]:
                if req not in all_requirements:
                    all_requirements.append(req)
        
        if critical_result["high_risk_requirements"]:
            for req in critical_result["high_risk_requirements"]:
                if req not in all_requirements:
                    all_requirements.append(req)
        
        # Convert back to SafetyRequirement objects
        requirement_objects = []
        for req_dict in all_requirements:
            req = SafetyRequirement(
                requirement_id=req_dict["requirement_id"],
                standard_id=req_dict["standard_id"],
                title=req_dict["title"],
                description=req_dict["description"],
                compliance_level=ComplianceLevel(req_dict["compliance_level"]),
                risk_level=RiskLevel(req_dict["risk_level"]),
                applicable_environments=req_dict["applicable_environments"],
                applicable_skill_levels=req_dict["applicable_skill_levels"],
                verification_method=req_dict["verification_method"],
                legal_reference=req_dict["legal_reference"],
                enforcement_authority=req_dict["enforcement_authority"]
            )
            requirement_objects.append(req)
        
        # Aggregate warnings and recommendations
        all_warnings = []
        all_warnings.extend(loto_result.get("warnings", []))
        all_warnings.extend(novice_result.get("warnings", []))
        
        all_recommendations = []
        all_recommendations.extend(loto_result.get("recommendations", []))
        all_recommendations.extend(novice_result.get("recommendations", []))
        
        # Aggregate violations
        all_violations = []
        all_violations.extend(loto_result.get("violations", []))
        all_violations.extend(novice_result.get("violations", []))
        all_violations.extend(critical_result.get("violations", []))
        
        # Determine compliance status
        compliance_status = "compliant"
        if all_violations:
            compliance_status = "non_compliant"
        elif len(all_warnings) > 2:
            compliance_status = "conditional"
        
        # Generate legal notes
        legal_notes = []
        for req in requirement_objects[:3]:  # Top 3 most relevant
            legal_notes.append(f"{req.standard_id}: {req.legal_reference} - {req.enforcement_authority}")
        
        # Create risk assessment
        risk_assessment = {
            "product_category": product_category,
            "user_skill": user_skill_level,
            "environment": environment,
            "base_risk_level": "medium",
            "applicable_standards": len(requirement_objects),
            "high_risk_count": critical_result.get("high_risk_count", 0),
            "loto_required": loto_result.get("should_have_loto", False),
            "novice_restrictions": novice_result.get("is_novice", False)
        }
        
        return ComplianceValidationResult(
            product_code=product_code,
            user_skill_level=user_skill_level,
            environment=environment,
            compliance_status=compliance_status,
            applicable_requirements=requirement_objects,
            violations=all_violations,
            warnings=all_warnings,
            recommendations=all_recommendations,
            risk_assessment=risk_assessment,
            legal_notes=legal_notes,
            validation_timestamp=datetime.now(),
            validator_version="2.0.0"
        )
    
    def _get_safety_requirements(self) -> List[SafetyRequirement]:
        """Get comprehensive safety requirements database"""
        return [
            SafetyRequirement(
                requirement_id="OSHA-1910-95-001",
                standard_id="OSHA-1910.95",
                title="Hearing Protection Required",
                description="Hearing protection required when noise levels exceed 85 dBA TWA",
                compliance_level=ComplianceLevel.MANDATORY,
                risk_level=RiskLevel.HIGH,
                applicable_environments=["industrial", "construction", "manufacturing"],
                applicable_skill_levels=["all"],
                verification_method="Noise level measurement",
                legal_reference="29 CFR 1910.95",
                enforcement_authority="OSHA"
            ),
            SafetyRequirement(
                requirement_id="ANSI-Z87-1-001",
                standard_id="ANSI-Z87.1",
                title="Eye Protection Required",
                description="Safety glasses or goggles required for impact hazards",
                compliance_level=ComplianceLevel.MANDATORY,
                risk_level=RiskLevel.HIGH,
                applicable_environments=["workshop", "construction", "manufacturing", "laboratory"],
                applicable_skill_levels=["all"],
                verification_method="Impact resistance testing",
                legal_reference="ANSI Z87.1-2020",
                enforcement_authority="ANSI"
            ),
            SafetyRequirement(
                requirement_id="OSHA-1926-501-001",
                standard_id="OSHA-1926.501",
                title="Fall Protection Required",
                description="Fall protection required for work at heights above 6 feet",
                compliance_level=ComplianceLevel.MANDATORY,
                risk_level=RiskLevel.CRITICAL,
                applicable_environments=["construction", "outdoor", "roofing"],
                applicable_skill_levels=["all"],
                verification_method="Height measurement and harness inspection",
                legal_reference="29 CFR 1926.501",
                enforcement_authority="OSHA"
            ),
            SafetyRequirement(
                requirement_id="OSHA-1910-147-001",
                standard_id="OSHA-1910.147",
                title="Lockout/Tagout Required",
                description="Energy isolation required before equipment maintenance",
                compliance_level=ComplianceLevel.MANDATORY,
                risk_level=RiskLevel.CRITICAL,
                applicable_environments=["industrial", "manufacturing", "electrical"],
                applicable_skill_levels=["intermediate", "advanced", "expert"],
                verification_method="Energy isolation verification",
                legal_reference="29 CFR 1910.147",
                enforcement_authority="OSHA"
            ),
            SafetyRequirement(
                requirement_id="NFPA-70E-001",
                standard_id="NFPA-70E",
                title="Arc Flash Protection",
                description="Arc-rated PPE required for electrical work",
                compliance_level=ComplianceLevel.MANDATORY,
                risk_level=RiskLevel.CRITICAL,
                applicable_environments=["electrical", "industrial"],
                applicable_skill_levels=["intermediate", "advanced", "expert"],
                verification_method="Arc flash analysis",
                legal_reference="NFPA 70E-2021",
                enforcement_authority="NFPA"
            ),
            SafetyRequirement(
                requirement_id="ISO-45001-001",
                standard_id="ISO-45001",
                title="Occupational Health Management",
                description="Systematic approach to managing occupational health and safety",
                compliance_level=ComplianceLevel.RECOMMENDED,
                risk_level=RiskLevel.MEDIUM,
                applicable_environments=["all"],
                applicable_skill_levels=["all"],
                verification_method="Management system audit",
                legal_reference="ISO 45001:2018",
                enforcement_authority="ISO"
            ),
            SafetyRequirement(
                requirement_id="ANSI-B11-1-001",
                standard_id="ANSI-B11.1",
                title="Machine Guarding Required",
                description="Guards required for rotating machinery and cutting tools",
                compliance_level=ComplianceLevel.MANDATORY,
                risk_level=RiskLevel.HIGH,
                applicable_environments=["manufacturing", "workshop"],
                applicable_skill_levels=["all"],
                verification_method="Guard inspection and interlock testing",
                legal_reference="ANSI B11.1-2009",
                enforcement_authority="ANSI"
            ),
            SafetyRequirement(
                requirement_id="OSHA-1910-132-001",
                standard_id="OSHA-1910.132",
                title="Personal Protective Equipment",
                description="PPE required when engineering controls are insufficient",
                compliance_level=ComplianceLevel.MANDATORY,
                risk_level=RiskLevel.MEDIUM,
                applicable_environments=["all"],
                applicable_skill_levels=["all"],
                verification_method="Hazard assessment and PPE evaluation",
                legal_reference="29 CFR 1910.132",
                enforcement_authority="OSHA"
            )
        ]