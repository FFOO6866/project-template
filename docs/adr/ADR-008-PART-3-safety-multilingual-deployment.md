# ADR-008 PART 3: Safety Compliance, Multi-lingual & Production Deployment

**Continuation of**: ADR-008-PART-2-classification-and-ai-implementation.md
**Status**: PROPOSED
**Date**: 2025-01-16

---

## Phase 4: Safety Compliance Integration (OSHA/ANSI) - 2 weeks

### Overview

Integrate safety compliance rules following OSHA and ANSI standards to ensure:
- Mandatory safety equipment recommendations
- Compliance with regulations (29 CFR 1926.302, ANSI Z87.1, etc.)
- Risk-based filtering for user skill levels
- Legal liability protection through proper documentation
- Safety training recommendations

### Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                 Safety Compliance System                       │
│                                                                │
│  ┌──────────────┐       ┌──────────────┐                     │
│  │ OSHA Rules   │       │ ANSI Rules   │                     │
│  │  Database    │       │  Database    │                     │
│  └──────┬───────┘       └──────┬───────┘                     │
│         │                      │                              │
│         └──────────┬───────────┘                              │
│                    │                                          │
│                    ▼                                          │
│         ┌──────────────────────┐                              │
│         │  Safety Rule Engine  │                              │
│         │  (Constraint-based)  │                              │
│         └──────────┬───────────┘                              │
│                    │                                          │
│         ┌──────────┴───────────┐                              │
│         │                      │                              │
│         ▼                      ▼                              │
│  ┌─────────────┐        ┌─────────────┐                      │
│  │   Mandate   │        │    Risk     │                      │
│  │ Enforcement │        │ Assessment  │                      │
│  └─────────────┘        └─────────────┘                      │
│         │                      │                              │
│         └──────────┬───────────┘                              │
│                    │                                          │
│                    ▼                                          │
│         ┌──────────────────────┐                              │
│         │ Neo4j Integration    │                              │
│         │ (Safety Relationships│                              │
│         └──────────────────────┘                              │
└───────────────────────────────────────────────────────────────┘
```

### Implementation

#### 4.1 OSHA/ANSI Safety Rules Database

**File**: `data/safety/osha_standards.json`

```json
{
  "version": "2024.1",
  "last_updated": "2024-01-01",
  "standards": [
    {
      "standard_id": "29 CFR 1926.102",
      "title": "Eye and Face Protection",
      "description": "Requirements for eye and face protection in construction",
      "mandatory_for": ["drilling", "grinding", "cutting", "welding", "chipping"],
      "equipment_required": [
        {
          "type": "safety_glasses",
          "ansi_standard": "ANSI Z87.1",
          "specifications": {
            "impact_resistance": "required",
            "side_shields": "required_for_impact_hazards",
            "lens_material": ["polycarbonate", "glass", "plastic"]
          }
        }
      ],
      "penalty_for_violation": "Up to $15,625 per violation",
      "reference_url": "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.102"
    },
    {
      "standard_id": "29 CFR 1926.302",
      "title": "Power-Operated Hand Tools",
      "description": "Safety requirements for powered hand tools",
      "mandatory_for": ["power_drill", "angle_grinder", "circular_saw", "power_sander"],
      "requirements": [
        {
          "requirement": "Guards must be in place",
          "applies_to": ["grinders", "saws"],
          "violation_severity": "serious"
        },
        {
          "requirement": "Tool must be unplugged during blade/bit changes",
          "applies_to": ["all_power_tools"],
          "violation_severity": "serious"
        },
        {
          "requirement": "Electric tools must be grounded or double-insulated",
          "applies_to": ["corded_tools"],
          "violation_severity": "serious"
        }
      ],
      "safety_equipment": [
        "safety_glasses",
        "hearing_protection",
        "work_gloves",
        "dust_mask"
      ],
      "reference_url": "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.302"
    },
    {
      "standard_id": "29 CFR 1910.242",
      "title": "Hand and Portable Powered Tools and Equipment, General",
      "description": "General requirements for hand and portable powered tools",
      "mandatory_for": ["all_power_tools", "pneumatic_tools", "hydraulic_tools"],
      "requirements": [
        {
          "requirement": "Appropriate PPE must be worn",
          "risk_assessment_required": true
        },
        {
          "requirement": "Tools must be inspected before use",
          "frequency": "daily"
        },
        {
          "requirement": "Damaged tools must be removed from service",
          "violation_severity": "serious"
        }
      ],
      "reference_url": "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.242"
    }
  ],
  "task_safety_mappings": [
    {
      "task": "drilling_holes_wood_metal",
      "risk_level": "medium",
      "osha_standards": ["29 CFR 1926.102", "29 CFR 1926.302"],
      "mandatory_ppe": [
        {"type": "safety_glasses", "ansi": "ANSI Z87.1"},
        {"type": "hearing_protection", "ansi": "ANSI S3.19", "optional_if": "indoor_low_rpm"}
      ],
      "recommended_ppe": [
        {"type": "work_gloves", "ansi": "ANSI/ISEA 105"},
        {"type": "dust_mask", "ansi": "NIOSH N95", "required_if": "concrete_drilling"}
      ],
      "prohibited_for_untrained": false,
      "certification_required": false
    },
    {
      "task": "angle_grinding",
      "risk_level": "high",
      "osha_standards": ["29 CFR 1926.102", "29 CFR 1926.300", "29 CFR 1926.302"],
      "mandatory_ppe": [
        {"type": "face_shield", "ansi": "ANSI Z87.1"},
        {"type": "hearing_protection", "ansi": "ANSI S3.19"},
        {"type": "cut_resistant_gloves", "ansi": "ANSI/ISEA 105 Level A4+"},
        {"type": "respiratory_protection", "ansi": "NIOSH approved"}
      ],
      "recommended_ppe": [
        {"type": "leather_apron", "reason": "spark_protection"},
        {"type": "safety_boots", "ansi": "ASTM F2413"}
      ],
      "prohibited_for_untrained": true,
      "certification_required": false,
      "training_hours_required": 4
    },
    {
      "task": "electrical_wiring",
      "risk_level": "very_high",
      "osha_standards": ["29 CFR 1926.416", "29 CFR 1910.333", "NFPA 70E"],
      "mandatory_ppe": [
        {"type": "insulated_gloves", "ansi": "ASTM D120 Class 00+"},
        {"type": "safety_glasses", "ansi": "ANSI Z87.1"},
        {"type": "arc_flash_suit", "ansi": "NFPA 70E", "required_if": "live_work"}
      ],
      "prohibited_for_untrained": true,
      "certification_required": true,
      "required_certifications": ["Licensed Electrician", "OSHA 10-Hour"],
      "training_hours_required": 40
    }
  ]
}
```

**File**: `data/safety/ansi_standards.json`

```json
{
  "version": "2024.1",
  "standards": [
    {
      "standard_id": "ANSI Z87.1",
      "title": "Occupational and Educational Personal Eye and Face Protection Devices",
      "description": "Performance requirements for eye and face protection",
      "current_version": "2020",
      "test_requirements": {
        "impact_resistance": {
          "basic_impact": "1 inch steel ball at 50 ft/s",
          "high_impact": "0.25 inch steel ball at 150 ft/s"
        },
        "optical_quality": "Class 1 or Class 2",
        "coverage": "Minimum coverage area specified"
      },
      "marking_requirements": {
        "manufacturer_mark": "required",
        "standard_mark": "Z87 or Z87+",
        "shade_number": "required_for_welding"
      },
      "product_types": [
        "safety_glasses",
        "safety_goggles",
        "face_shields",
        "welding_helmets"
      ]
    },
    {
      "standard_id": "ANSI S3.19",
      "title": "Hearing Protection Devices - Labeling",
      "description": "Requirements for hearing protection device labeling",
      "current_version": "2021",
      "nrr_ratings": {
        "low": "NRR 20-24 dB",
        "medium": "NRR 25-29 dB",
        "high": "NRR 30+ dB"
      },
      "product_types": [
        "earplugs_foam",
        "earplugs_reusable",
        "earmuffs",
        "custom_molded"
      ],
      "selection_criteria": {
        "noise_level_85_90dB": "NRR 20+",
        "noise_level_90_100dB": "NRR 25+",
        "noise_level_100plus_dB": "NRR 30+ or dual protection"
      }
    },
    {
      "standard_id": "ANSI/ISEA 105",
      "title": "Hand Protection Classification",
      "description": "Performance classification for hand protection",
      "current_version": "2016",
      "cut_resistance_levels": {
        "A1": "200-499 grams",
        "A2": "500-999 grams",
        "A3": "1000-1499 grams",
        "A4": "1500-2199 grams",
        "A5": "2200-2999 grams",
        "A6": "3000-3999 grams",
        "A7": "4000-4999 grams",
        "A8": "5000-5999 grams",
        "A9": "6000+ grams"
      },
      "task_recommendations": {
        "general_handling": "A1-A2",
        "sharp_edges": "A3-A4",
        "metal_cutting": "A5-A6",
        "glass_handling": "A7-A9"
      }
    }
  ]
}
```

#### 4.2 Safety Compliance Service

**File**: `src/services/safety_compliance_service.py`

```python
"""
Safety Compliance Service
OSHA/ANSI standards enforcement for product recommendations
Ensures legal compliance and user safety
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class SkillLevel(Enum):
    """User skill level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    PROFESSIONAL = "professional"


@dataclass
class SafetyRequirement:
    """Safety requirement for a task."""
    equipment_type: str
    ansi_standard: Optional[str]
    osha_standard: Optional[str]
    mandatory: bool
    reason: str
    risk_if_missing: str
    product_recommendations: List[str]  # Product IDs


@dataclass
class SafetyAssessment:
    """Comprehensive safety assessment for a task."""
    task_name: str
    risk_level: RiskLevel
    user_skill_level: SkillLevel

    # Requirements
    mandatory_ppe: List[SafetyRequirement]
    recommended_ppe: List[SafetyRequirement]

    # Restrictions
    prohibited_for_skill_level: bool
    certification_required: bool
    required_certifications: List[str]
    training_hours_required: int

    # Compliance
    osha_standards_applicable: List[str]
    ansi_standards_applicable: List[str]

    # Warnings
    warnings: List[str]
    legal_disclaimers: List[str]


class SafetyComplianceService:
    """
    Enforce OSHA/ANSI safety standards in product recommendations.
    Critical for legal liability protection.
    """

    def __init__(self, safety_data_dir: str = "data/safety"):
        """Initialize safety compliance service."""
        self.data_dir = Path(safety_data_dir)

        # Load safety standards
        self.osha_standards = self._load_json("osha_standards.json")
        self.ansi_standards = self._load_json("ansi_standards.json")

        # Build lookup indexes
        self.task_safety_map = self._build_task_safety_map()
        self.equipment_standards_map = self._build_equipment_standards_map()

        logger.info(f"Safety Compliance Service initialized with {len(self.task_safety_map)} task mappings")

    def _load_json(self, filename: str) -> Dict:
        """Load JSON safety data."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            logger.warning(f"Safety file not found: {filepath}, using empty data")
            return {}

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _build_task_safety_map(self) -> Dict[str, Dict]:
        """Build fast lookup for task safety requirements."""
        task_map = {}

        for mapping in self.osha_standards.get('task_safety_mappings', []):
            task_map[mapping['task']] = mapping

        return task_map

    def _build_equipment_standards_map(self) -> Dict[str, List[str]]:
        """Build lookup for equipment to applicable standards."""
        equipment_map = {}

        # From OSHA standards
        for standard in self.osha_standards.get('standards', []):
            for equipment in standard.get('equipment_required', []):
                equip_type = equipment['type']
                if equip_type not in equipment_map:
                    equipment_map[equip_type] = []
                equipment_map[equip_type].append(standard['standard_id'])

        return equipment_map

    def assess_task_safety(
        self,
        task_name: str,
        user_skill_level: SkillLevel = SkillLevel.BEGINNER,
        user_certifications: List[str] = None
    ) -> SafetyAssessment:
        """
        Perform comprehensive safety assessment for a task.

        Args:
            task_name: Name of the task
            user_skill_level: User's skill level
            user_certifications: List of certifications user holds

        Returns:
            SafetyAssessment with all requirements and restrictions
        """
        user_certifications = user_certifications or []

        # Find task safety mapping
        task_mapping = self._find_task_mapping(task_name)

        if not task_mapping:
            logger.warning(f"No safety mapping found for task: {task_name}")
            return self._default_safety_assessment(task_name, user_skill_level)

        # Parse risk level
        risk_level = RiskLevel(task_mapping['risk_level'])

        # Build mandatory PPE requirements
        mandatory_ppe = []
        for ppe in task_mapping.get('mandatory_ppe', []):
            requirement = SafetyRequirement(
                equipment_type=ppe['type'],
                ansi_standard=ppe.get('ansi'),
                osha_standard=None,  # Would link from standards
                mandatory=True,
                reason=f"Required by OSHA for {risk_level.value} risk tasks",
                risk_if_missing="Serious injury risk - eye damage, hearing loss, etc.",
                product_recommendations=[]  # Populated from product catalog
            )
            mandatory_ppe.append(requirement)

        # Build recommended PPE requirements
        recommended_ppe = []
        for ppe in task_mapping.get('recommended_ppe', []):
            requirement = SafetyRequirement(
                equipment_type=ppe['type'],
                ansi_standard=ppe.get('ansi'),
                osha_standard=None,
                mandatory=False,
                reason=ppe.get('reason', 'Additional protection recommended'),
                risk_if_missing="Moderate injury risk",
                product_recommendations=[]
            )
            recommended_ppe.append(requirement)

        # Check skill level restrictions
        prohibited_for_skill_level = False
        if task_mapping.get('prohibited_for_untrained', False):
            if user_skill_level in [SkillLevel.BEGINNER]:
                prohibited_for_skill_level = True

        # Check certification requirements
        certification_required = task_mapping.get('certification_required', False)
        required_certs = task_mapping.get('required_certifications', [])

        missing_certs = [cert for cert in required_certs if cert not in user_certifications]

        # Generate warnings
        warnings = []
        if prohibited_for_skill_level:
            warnings.append(f"⚠️ This task requires {SkillLevel.INTERMEDIATE.value}+ skill level")

        if missing_certs:
            warnings.append(f"⚠️ Certifications required: {', '.join(missing_certs)}")

        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            warnings.append(f"⚠️ HIGH RISK TASK - Ensure all safety equipment is worn")

        # Legal disclaimers
        disclaimers = [
            "User assumes all responsibility for safe tool operation",
            "Follow manufacturer instructions and safety guidelines",
            "Ensure proper training before using power tools",
            "Wear all required Personal Protective Equipment (PPE)"
        ]

        return SafetyAssessment(
            task_name=task_name,
            risk_level=risk_level,
            user_skill_level=user_skill_level,
            mandatory_ppe=mandatory_ppe,
            recommended_ppe=recommended_ppe,
            prohibited_for_skill_level=prohibited_for_skill_level,
            certification_required=certification_required,
            required_certifications=required_certs,
            training_hours_required=task_mapping.get('training_hours_required', 0),
            osha_standards_applicable=task_mapping.get('osha_standards', []),
            ansi_standards_applicable=[ppe.get('ansi') for ppe in task_mapping.get('mandatory_ppe', []) if ppe.get('ansi')],
            warnings=warnings,
            legal_disclaimers=disclaimers
        )

    def _find_task_mapping(self, task_name: str) -> Optional[Dict]:
        """Find safety mapping for a task (fuzzy match)."""
        task_lower = task_name.lower().replace(' ', '_')

        # Try exact match first
        if task_lower in self.task_safety_map:
            return self.task_safety_map[task_lower]

        # Try fuzzy match
        for task_key, mapping in self.task_safety_map.items():
            if task_key in task_lower or task_lower in task_key:
                return mapping

        return None

    def _default_safety_assessment(
        self,
        task_name: str,
        user_skill_level: SkillLevel
    ) -> SafetyAssessment:
        """Default safety assessment when no specific mapping found."""
        return SafetyAssessment(
            task_name=task_name,
            risk_level=RiskLevel.MEDIUM,
            user_skill_level=user_skill_level,
            mandatory_ppe=[
                SafetyRequirement(
                    equipment_type="safety_glasses",
                    ansi_standard="ANSI Z87.1",
                    osha_standard="29 CFR 1926.102",
                    mandatory=True,
                    reason="General eye protection for DIY tasks",
                    risk_if_missing="Eye injury risk",
                    product_recommendations=[]
                )
            ],
            recommended_ppe=[],
            prohibited_for_skill_level=False,
            certification_required=False,
            required_certifications=[],
            training_hours_required=0,
            osha_standards_applicable=["29 CFR 1926.102"],
            ansi_standards_applicable=["ANSI Z87.1"],
            warnings=["⚠️ Safety data not available for this task - use general PPE"],
            legal_disclaimers=[
                "User assumes all responsibility for safe tool operation",
                "Follow manufacturer instructions and safety guidelines"
            ]
        )

    def filter_recommendations_by_safety(
        self,
        recommendations: List[Dict],
        task_name: str,
        user_skill_level: SkillLevel,
        enforce_restrictions: bool = True
    ) -> List[Dict]:
        """
        Filter product recommendations based on safety requirements.
        Remove products that are unsafe for user's skill level.

        Args:
            recommendations: List of product recommendations
            task_name: Task being performed
            user_skill_level: User's skill level
            enforce_restrictions: Whether to enforce skill level restrictions

        Returns:
            Filtered list of recommendations (may be empty if task prohibited)
        """
        # Get safety assessment
        assessment = self.assess_task_safety(task_name, user_skill_level)

        # If task is prohibited for skill level, return empty list
        if enforce_restrictions and assessment.prohibited_for_skill_level:
            logger.warning(f"Task {task_name} prohibited for skill level {user_skill_level.value}")
            return []

        # Otherwise, return recommendations with safety warnings attached
        filtered_recs = []
        for rec in recommendations:
            # Add safety assessment to recommendation
            rec['safety_assessment'] = {
                'risk_level': assessment.risk_level.value,
                'mandatory_ppe': [
                    {
                        'type': ppe.equipment_type,
                        'standard': ppe.ansi_standard or ppe.osha_standard,
                        'reason': ppe.reason
                    }
                    for ppe in assessment.mandatory_ppe
                ],
                'warnings': assessment.warnings,
                'disclaimers': assessment.legal_disclaimers
            }
            filtered_recs.append(rec)

        return filtered_recs

    def get_safety_equipment_recommendations(
        self,
        task_name: str,
        user_skill_level: SkillLevel = SkillLevel.BEGINNER
    ) -> List[SafetyRequirement]:
        """
        Get list of required safety equipment for a task.
        To be displayed prominently in UI.

        Args:
            task_name: Task being performed
            user_skill_level: User's skill level

        Returns:
            List of SafetyRequirement objects
        """
        assessment = self.assess_task_safety(task_name, user_skill_level)

        # Combine mandatory and recommended
        all_ppe = assessment.mandatory_ppe + assessment.recommended_ppe

        return all_ppe

    def generate_safety_checklist(
        self,
        task_name: str,
        user_skill_level: SkillLevel
    ) -> Dict[str, Any]:
        """
        Generate comprehensive safety checklist for a task.
        Suitable for display in UI before user starts task.

        Returns:
            Dict with checklist items, warnings, and resources
        """
        assessment = self.assess_task_safety(task_name, user_skill_level)

        checklist = {
            'task': task_name,
            'risk_level': assessment.risk_level.value,
            'pre_task_checklist': [
                {
                    'item': f"✓ Obtain {ppe.equipment_type.replace('_', ' ').title()}",
                    'standard': ppe.ansi_standard or ppe.osha_standard,
                    'mandatory': ppe.mandatory
                }
                for ppe in (assessment.mandatory_ppe + assessment.recommended_ppe)
            ],
            'during_task_checklist': [
                "✓ Wear all required PPE",
                "✓ Inspect tools before use",
                "✓ Ensure adequate lighting",
                "✓ Keep work area clean",
                "✓ Follow manufacturer instructions"
            ],
            'post_task_checklist': [
                "✓ Clean and store tools properly",
                "✓ Dispose of waste materials safely",
                "✓ Inspect PPE for damage"
            ],
            'warnings': assessment.warnings,
            'legal_disclaimers': assessment.legal_disclaimers,
            'osha_standards': assessment.osha_standards_applicable,
            'training_required': assessment.training_hours_required > 0,
            'training_hours': assessment.training_hours_required,
            'certification_required': assessment.certification_required,
            'certifications': assessment.required_certifications
        }

        return checklist


# ============================================================================
# INTEGRATION WITH KNOWLEDGE GRAPH
# ============================================================================

def sync_safety_data_to_neo4j(
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    safety_service: SafetyComplianceService
):
    """
    Sync safety requirements to Neo4j knowledge graph.
    Creates SafetyEquipment nodes and relationships.
    """
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    with driver.session() as session:
        # Get all unique tasks
        result = session.run("MATCH (t:Task) RETURN t.name AS task_name, t.id AS task_id")

        tasks = [(record['task_name'], record['task_id']) for record in result]

        logger.info(f"Syncing safety data for {len(tasks)} tasks...")

        for task_name, task_id in tasks:
            # Get safety requirements
            assessment = safety_service.assess_task_safety(task_name)

            # Create/update SafetyEquipment nodes and relationships
            for ppe in assessment.mandatory_ppe:
                session.run("""
                    MERGE (safety:SafetyEquipment {id: $safety_id})
                    ON CREATE SET
                      safety.name = $name,
                      safety.ansi_standard = $ansi_standard,
                      safety.osha_standard = $osha_standard,
                      safety.mandatory = $mandatory

                    WITH safety
                    MATCH (t:Task {id: $task_id})
                    MERGE (t)-[:REQUIRES_SAFETY {
                      mandatory: $mandatory,
                      risk_if_missing: $risk,
                      reason: $reason
                    }]->(safety)
                """,
                    safety_id=f"SAFETY_{ppe.equipment_type.upper()}",
                    name=ppe.equipment_type.replace('_', ' ').title(),
                    ansi_standard=ppe.ansi_standard,
                    osha_standard=ppe.osha_standard,
                    mandatory=ppe.mandatory,
                    task_id=task_id,
                    risk=ppe.risk_if_missing,
                    reason=ppe.reason
                )

        logger.info("Safety data sync complete")

    driver.close()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Initialize safety service
    safety_service = SafetyComplianceService(safety_data_dir="data/safety")

    # Example 1: Assess task safety
    print("\n=== Safety Assessment ===")
    assessment = safety_service.assess_task_safety(
        task_name="drilling_holes_wood_metal",
        user_skill_level=SkillLevel.BEGINNER
    )

    print(f"\nTask: {assessment.task_name}")
    print(f"Risk Level: {assessment.risk_level.value}")
    print(f"User Skill: {assessment.user_skill_level.value}")

    print(f"\nMandatory PPE:")
    for ppe in assessment.mandatory_ppe:
        print(f"  - {ppe.equipment_type.replace('_', ' ').title()}")
        print(f"    Standard: {ppe.ansi_standard or ppe.osha_standard}")
        print(f"    Reason: {ppe.reason}")

    print(f"\nWarnings:")
    for warning in assessment.warnings:
        print(f"  {warning}")

    # Example 2: Generate safety checklist
    print("\n\n=== Safety Checklist ===")
    checklist = safety_service.generate_safety_checklist(
        task_name="angle_grinding",
        user_skill_level=SkillLevel.INTERMEDIATE
    )

    print(f"\nTask: {checklist['task']}")
    print(f"Risk Level: {checklist['risk_level'].upper()}")

    print(f"\nPre-Task Checklist:")
    for item in checklist['pre_task_checklist']:
        mandatory_mark = "[MANDATORY]" if item['mandatory'] else "[RECOMMENDED]"
        print(f"  {item['item']} {mandatory_mark}")
        if item['standard']:
            print(f"    Compliance: {item['standard']}")

    print(f"\nDuring Task:")
    for item in checklist['during_task_checklist']:
        print(f"  {item}")

    if checklist['warnings']:
        print(f"\n⚠️  WARNINGS:")
        for warning in checklist['warnings']:
            print(f"  {warning}")
```

### Implementation Checklist - Phase 4

- [ ] Create `data/safety/` directory structure
- [ ] Create `data/safety/osha_standards.json` with complete OSHA standards
- [ ] Create `data/safety/ansi_standards.json` with ANSI standards
- [ ] Implement `src/services/safety_compliance_service.py`
- [ ] Integrate with Neo4j knowledge graph (sync safety relationships)
- [ ] Update hybrid recommendation engine to enforce safety rules
- [ ] Create API endpoints for safety assessment
- [ ] Create UI components for safety warnings and checklists
- [ ] Add safety disclaimers to quotation generation
- [ ] Legal review of safety disclaimers (consult legal counsel)
- [ ] Create admin UI for managing safety rules
- [ ] Generate compliance reports for audit purposes

**Estimated Time**: 2 weeks
**Dependencies**: Phase 1 (Neo4j), Phase 3 (Hybrid Engine)
**Risk Level**: High (legal liability, critical for user safety)

---

**Continuing with Phase 5 (Multi-lingual) and Phase 6 (Frontend/WebSocket) in next section...**
