"""
OSHA Compliance Engine - Database-Driven Implementation
Phase 4: Safety Compliance System
Real OSHA Standards from PostgreSQL Database

CRITICAL: NO HARDCODED DATA
All standards, classifications, and mappings must be loaded from PostgreSQL.
If database is empty, system FAILS with explicit error message.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """OSHA Risk Classification Levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OSHAComplianceEngine:
    """
    OSHA Compliance Rules Engine - Database-Driven

    ZERO HARDCODED DATA: All OSHA standards loaded from PostgreSQL
    using Kailash SDK WorkflowBuilder pattern.

    Implements real OSHA standards for workplace safety in construction and DIY.
    Based on 29 CFR (Code of Federal Regulations) Part 1926 - Safety and Health
    Regulations for Construction.

    Features:
    - Risk assessment based on tool/task classification
    - Mandatory PPE enforcement
    - Legal compliance validation
    - Hazard exposure calculation

    Data Sources:
    - osha_standards table (OSHA CFR standards from osha.gov)
    - tool_risk_classifications table (Tool hazard assessments)
    - task_hazard_mappings table (Task-to-hazard mappings)
    """

    def __init__(self, database_url: str = None):
        """
        Initialize OSHA compliance engine

        Args:
            database_url: PostgreSQL connection URL (uses env var if None)

        Raises:
            ValueError: If database is empty or required data is missing
        """
        self.runtime = LocalRuntime()
        self.database_url = database_url

        # Load data from database
        self.standards = self._load_osha_standards()
        self.tool_classifications = self._load_tool_risk_classifications()
        self.task_hazards = self._load_task_hazard_mapping()

        # Validate required data
        self._validate_required_data()

    def _load_osha_standards(self) -> Dict[str, Dict]:
        """
        Load real OSHA standards from PostgreSQL database

        Returns:
            Dictionary of OSHA standards with requirements

        Raises:
            ValueError: If no standards found in database
        """
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("OSHAStandardListNode", "get_standards", {
                "filter": {},
                "limit": 1000,
                "order_by": ["cfr"]
            })

            results, run_id = self.runtime.execute(workflow.build())
            standards_list = results.get("get_standards", [])

            if not standards_list:
                raise ValueError(
                    "CRITICAL: No OSHA standards found in database. "
                    "Run scripts/load_safety_standards.py to populate data from osha.gov"
                )

            # Convert list to dictionary keyed by standard type
            standards_dict = {}
            for standard in standards_list:
                # Derive key from CFR number (e.g., "29 CFR 1926.102" -> "eye_protection")
                key = self._derive_standard_key(standard['cfr'], standard['title'])
                standards_dict[key] = {
                    'cfr': standard['cfr'],
                    'title': standard['title'],
                    'requirement': standard['requirements'],
                    'applies_to': standard.get('applies_to', []),
                    'required_ppe': standard.get('required_ppe', []),
                    'mandatory': standard.get('mandatory', True),
                    'risk_level': standard.get('risk_level', 'medium'),
                    'legal_reference': standard.get('legal_reference_url', ''),
                    'penalties': standard.get('penalties', '')
                }

            logger.info(f"Loaded {len(standards_dict)} OSHA standards from database")
            return standards_dict

        except Exception as e:
            logger.error(f"Failed to load OSHA standards from database: {e}")
            raise ValueError(
                f"OSHA standards database load failed: {e}. "
                "Ensure PostgreSQL is running and data is loaded."
            )

    def _derive_standard_key(self, cfr: str, title: str) -> str:
        """Derive dictionary key from CFR number and title"""
        # Map CFR numbers to standard keys
        cfr_mapping = {
            "29 CFR 1926.102": "eye_protection",
            "29 CFR 1926.138": "hand_protection",
            "29 CFR 1926.96": "foot_protection",
            "29 CFR 1926.100": "head_protection",
            "29 CFR 1926.101": "hearing_protection",
            "29 CFR 1926.103": "respiratory_protection",
            "29 CFR 1926.302": "power_tool_safety",
            "29 CFR 1926.95": "general_ppe"
        }

        return cfr_mapping.get(cfr, title.lower().replace(" ", "_").replace("-", "_"))

    def _load_tool_risk_classifications(self) -> Dict[str, Dict]:
        """
        Load tool risk classifications from PostgreSQL database

        Returns:
            Dictionary of tools with risk levels and required PPE

        Raises:
            ValueError: If no tool classifications found in database
        """
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("ToolRiskClassificationListNode", "get_tools", {
                "filter": {},
                "limit": 1000,
                "order_by": ["tool_name"]
            })

            results, run_id = self.runtime.execute(workflow.build())
            tools_list = results.get("get_tools", [])

            if not tools_list:
                raise ValueError(
                    "CRITICAL: No tool risk classifications found in database. "
                    "Run scripts/load_safety_standards.py to populate tool safety data"
                )

            # Convert list to dictionary keyed by tool name
            tools_dict = {}
            for tool in tools_list:
                tool_key = tool['tool_name'].lower().replace(' ', '_')
                tools_dict[tool_key] = {
                    'category': tool['category'],
                    'risk_level': tool['risk_level'],
                    'hazards': tool.get('hazards', []),
                    'osha_standards': tool.get('osha_standards', []),
                    'mandatory_ppe': tool.get('mandatory_ppe', []),
                    'recommended_ppe': tool.get('recommended_ppe', []),
                    'training_required': tool.get('training_required', False),
                    'certification_required': tool.get('certification_required', False)
                }

            logger.info(f"Loaded {len(tools_dict)} tool risk classifications from database")
            return tools_dict

        except Exception as e:
            logger.error(f"Failed to load tool risk classifications from database: {e}")
            raise ValueError(
                f"Tool risk classifications database load failed: {e}. "
                "Ensure PostgreSQL is running and data is loaded."
            )

    def _load_task_hazard_mapping(self) -> Dict[str, Dict]:
        """
        Load task-to-hazard mappings from PostgreSQL database

        Returns:
            Dictionary of tasks with associated hazards and PPE

        Raises:
            ValueError: If no task hazard mappings found in database
        """
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("TaskHazardMappingListNode", "get_tasks", {
                "filter": {},
                "limit": 1000,
                "order_by": ["task_id"]
            })

            results, run_id = self.runtime.execute(workflow.build())
            tasks_list = results.get("get_tasks", [])

            if not tasks_list:
                raise ValueError(
                    "CRITICAL: No task hazard mappings found in database. "
                    "Run scripts/load_safety_standards.py to populate task safety data"
                )

            # Convert list to dictionary keyed by task_id
            tasks_dict = {}
            for task in tasks_list:
                tasks_dict[task['task_id']] = {
                    'task_name': task['task_name'],
                    'hazards': task.get('hazards', []),
                    'risk_level': task['risk_level'],
                    'osha_standards': task.get('osha_standards', []),
                    'mandatory_ppe': task.get('mandatory_ppe', []),
                    'recommended_ppe': task.get('recommended_ppe', []),
                    'safety_notes': task.get('safety_notes', '')
                }

            logger.info(f"Loaded {len(tasks_dict)} task hazard mappings from database")
            return tasks_dict

        except Exception as e:
            logger.error(f"Failed to load task hazard mappings from database: {e}")
            raise ValueError(
                f"Task hazard mappings database load failed: {e}. "
                "Ensure PostgreSQL is running and data is loaded."
            )

    def _validate_required_data(self):
        """
        Validate that required safety data is present

        Raises:
            ValueError: If critical data is missing
        """
        if not self.standards:
            raise ValueError(
                "VALIDATION FAILED: No OSHA standards loaded. "
                "Database must contain OSHA CFR standards from osha.gov"
            )

        if not self.tool_classifications:
            raise ValueError(
                "VALIDATION FAILED: No tool risk classifications loaded. "
                "Database must contain tool safety assessments"
            )

        if not self.task_hazards:
            raise ValueError(
                "VALIDATION FAILED: No task hazard mappings loaded. "
                "Database must contain task-to-hazard safety mappings"
            )

        logger.info("✅ OSHA compliance data validation successful")
        logger.info(f"   {len(self.standards)} OSHA standards loaded")
        logger.info(f"   {len(self.tool_classifications)} tool classifications loaded")
        logger.info(f"   {len(self.task_hazards)} task hazard mappings loaded")

    def assess_task_risk(self, task_description: str, tools_used: List[str] = None) -> Dict[str, Any]:
        """
        Assess risk level for a task based on OSHA standards from database

        Args:
            task_description: Description of the task to perform
            tools_used: List of tools/products to be used

        Returns:
            Risk assessment with required PPE and OSHA compliance info
        """
        task_lower = task_description.lower()
        tools_used = tools_used or []

        # Initialize assessment
        assessment = {
            "task": task_description,
            "tools": tools_used,
            "risk_level": RiskLevel.LOW.value,
            "hazards": set(),
            "osha_standards": set(),
            "mandatory_ppe": set(),
            "recommended_ppe": set(),
            "compliance_notes": [],
            "data_source": "postgresql_database"
        }

        # Check task hazards from database
        for task_key, task_data in self.task_hazards.items():
            if task_key.replace('_', ' ') in task_lower:
                assessment["risk_level"] = self._escalate_risk(
                    assessment["risk_level"],
                    task_data["risk_level"]
                )
                assessment["hazards"].update(task_data["hazards"])
                assessment["osha_standards"].update(task_data["osha_standards"])
                assessment["mandatory_ppe"].update(task_data["mandatory_ppe"])
                if task_data.get("recommended_ppe"):
                    assessment["recommended_ppe"].update(task_data["recommended_ppe"])

        # Check tool risks from database
        for tool in tools_used:
            tool_key = tool.lower().replace(' ', '_')
            if tool_key in self.tool_classifications:
                tool_data = self.tool_classifications[tool_key]
                assessment["risk_level"] = self._escalate_risk(
                    assessment["risk_level"],
                    tool_data["risk_level"]
                )
                assessment["hazards"].update(tool_data["hazards"])
                assessment["osha_standards"].update(tool_data["osha_standards"])
                assessment["mandatory_ppe"].update(tool_data["mandatory_ppe"])
                assessment["recommended_ppe"].update(tool_data.get("recommended_ppe", []))

        # Add compliance notes based on risk level
        if assessment["risk_level"] in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]:
            assessment["compliance_notes"].append(
                f"HIGH RISK TASK: OSHA mandates strict compliance with PPE requirements"
            )

        if "dust_generation" in assessment["hazards"]:
            assessment["compliance_notes"].append(
                "Respiratory protection required per 29 CFR 1926.103"
            )

        if "noise" in assessment["hazards"]:
            assessment["compliance_notes"].append(
                "Hearing protection required if noise exceeds 85 dBA (29 CFR 1926.101)"
            )

        # Convert sets to lists for JSON serialization
        assessment["hazards"] = list(assessment["hazards"])
        assessment["osha_standards"] = list(assessment["osha_standards"])
        assessment["mandatory_ppe"] = list(assessment["mandatory_ppe"])
        assessment["recommended_ppe"] = list(assessment["recommended_ppe"])

        return assessment

    def _escalate_risk(self, current_risk: str, new_risk: str) -> str:
        """
        Escalate risk level to highest identified risk

        Args:
            current_risk: Current risk level
            new_risk: New risk level to compare

        Returns:
            Highest risk level
        """
        risk_hierarchy = {
            RiskLevel.LOW.value: 1,
            RiskLevel.MEDIUM.value: 2,
            RiskLevel.HIGH.value: 3,
            RiskLevel.CRITICAL.value: 4
        }

        if risk_hierarchy.get(new_risk, 0) > risk_hierarchy.get(current_risk, 0):
            return new_risk
        return current_risk

    def validate_ppe_compliance(
        self,
        task_assessment: Dict[str, Any],
        available_ppe: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that available PPE meets OSHA requirements

        Args:
            task_assessment: Risk assessment from assess_task_risk()
            available_ppe: List of PPE items available/worn

        Returns:
            Tuple of (is_compliant, missing_ppe_list)
        """
        mandatory_ppe = set(task_assessment.get("mandatory_ppe", []))
        available_ppe_set = set([ppe.lower().replace(' ', '_') for ppe in available_ppe])

        missing_ppe = mandatory_ppe - available_ppe_set

        is_compliant = len(missing_ppe) == 0

        return is_compliant, list(missing_ppe)

    def get_standard_details(self, cfr_number: str) -> Optional[Dict]:
        """
        Get detailed information about specific OSHA standard from database

        Args:
            cfr_number: CFR number (e.g., "29 CFR 1926.102")

        Returns:
            Standard details or None if not found
        """
        for standard_data in self.standards.values():
            if standard_data["cfr"] == cfr_number:
                return standard_data
        return None

    def get_all_standards(self) -> Dict[str, Dict]:
        """
        Get all OSHA standards loaded from database

        Returns:
            Dictionary of all loaded OSHA standards
        """
        return self.standards

    def get_database_statistics(self) -> Dict[str, int]:
        """
        Get statistics about loaded safety data

        Returns:
            Dictionary with counts of loaded data
        """
        return {
            "osha_standards_count": len(self.standards),
            "tool_classifications_count": len(self.tool_classifications),
            "task_hazard_mappings_count": len(self.task_hazards),
            "total_safety_records": (
                len(self.standards) +
                len(self.tool_classifications) +
                len(self.task_hazards)
            )
        }


# Global compliance engine instance
_compliance_engine = None


def get_osha_compliance_engine(database_url: str = None) -> OSHAComplianceEngine:
    """
    Get global OSHA compliance engine instance

    Args:
        database_url: PostgreSQL connection URL (optional)

    Returns:
        OSHAComplianceEngine instance

    Raises:
        ValueError: If database is empty or data load fails
    """
    global _compliance_engine
    if _compliance_engine is None:
        _compliance_engine = OSHAComplianceEngine(database_url)
    return _compliance_engine
