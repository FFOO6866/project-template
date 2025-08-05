"""
End-to-End Tests for Custom Classification Workflows - AI-001
===========================================================

Tests complete HVAC, electrical, and tool classification workflows using the Kailash SDK.
Validates the runtime.execute(workflow.build()) pattern with real workflow execution.

Test Coverage:
- Complete HVAC classification workflow from product data to recommendations
- Electrical safety analysis workflow with code compliance
- Tool suitability workflow with project matching
- Performance validation for custom workflows (<2s per workflow)
- SDK pattern compliance with real WorkflowBuilder and LocalRuntime

NO EXTERNAL DEPENDENCIES - Uses the implemented custom nodes directly
Tests the actual workflow implementations using SDK patterns
"""

import pytest
import time
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

# Kailash SDK imports
# Windows compatibility patch
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import windows_sdk_compatibility  # Apply Windows compatibility for Kailash SDK

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Import our implemented custom workflows
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from workflows.hvac_classification import (
        HVACCompatibilityNode, HVACEfficiencyNode, HVACClassificationWorkflow
    )
    from workflows.electrical_classification import (
        ElectricalSafetyNode, ElectricalClassificationWorkflow  
    )
    from workflows.tool_classification import (
        ToolSuitabilityNode, ToolClassificationWorkflow
    )
    CUSTOM_WORKFLOWS_AVAILABLE = True
except ImportError as e:
    print(f"Custom workflows not available: {e}")
    CUSTOM_WORKFLOWS_AVAILABLE = False


@pytest.fixture
def e2e_performance_timer():
    """Performance timer for E2E workflow testing"""
    class WorkflowTimer:
        def __init__(self):
            self.measurements = []
        
        def time_workflow(self, workflow_name: str):
            """Context manager for timing workflow execution"""
            return WorkflowTimerContext(self, workflow_name)
        
        def record_measurement(self, workflow_name: str, duration: float, metadata: Dict = None):
            self.measurements.append({
                "workflow": workflow_name,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            })
        
        def assert_within_sla(self, max_seconds: float):
            if not self.measurements:
                return
            
            latest = self.measurements[-1]
            assert latest["duration"] < max_seconds, \
                f"Workflow {latest['workflow']} took {latest['duration']:.3f}s, exceeds {max_seconds}s SLA"
        
        def get_summary(self):
            if not self.measurements:
                return {"total_workflows": 0}
            
            durations = [m["duration"] for m in self.measurements]
            return {
                "total_workflows": len(durations),
                "average_duration": sum(durations) / len(durations),
                "max_duration": max(durations),
                "all_within_2s": all(d < 2.0 for d in durations),
                "measurements": self.measurements
            }
    
    class WorkflowTimerContext:
        def __init__(self, timer, workflow_name):
            self.timer = timer
            self.workflow_name = workflow_name
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            self.timer.record_measurement(self.workflow_name, duration)
    
    return WorkflowTimer()


class TestHVACClassificationWorkflowE2E:
    """End-to-end tests for HVAC classification workflow"""
    
    @pytest.mark.skipif(not CUSTOM_WORKFLOWS_AVAILABLE, reason="Custom workflows not available")
    def test_hvac_compatibility_workflow_complete(self, e2e_performance_timer):
        """Test complete HVAC compatibility analysis workflow"""
        
        # Real HVAC product data
        product_data = {
            "name": "Carrier Infinity 19VS Central Air Conditioner",
            "model": "24VNA9",
            "btu_capacity": 36000,  # 3-ton unit
            "seer_rating": 19.0,
            "refrigerant_type": "R-410A",
            "energy_star": True,
            "dimensions": {"width": 29, "height": 35, "depth": 29},
            "weight": 165,
            "compressor_type": "Variable Speed",
            "warranty_years": 10
        }
        
        system_requirements = {
            "btu_requirement": 35000,
            "minimum_seer": 16.0,
            "refrigerant_type": "R-410A", 
            "space_constraints": {"max_width": 32, "max_height": 38, "max_depth": 32},
            "efficiency_requirements": {"minimum_seer": 16.0},
            "energy_star_required": True
        }
        
        with e2e_performance_timer.time_workflow("hvac_compatibility_full"):
            # Test individual node execution first
            compatibility_node = HVACCompatibilityNode()
            efficiency_node = HVACEfficiencyNode()
            
            # Execute compatibility analysis
            compatibility_result = compatibility_node.run({
                "product_data": product_data,
                "system_requirements": system_requirements,
                "efficiency_threshold": 0.8,
                "include_alternatives": True
            })
            
            # Execute efficiency analysis
            efficiency_result = efficiency_node.run({
                "product_data": product_data,
                "efficiency_requirements": system_requirements.get("efficiency_requirements", {}),
                "energy_costs": {"electricity": 0.12},
                "usage_hours": 2000
            })
        
        # Validate compatibility results
        assert isinstance(compatibility_result, dict)
        assert "compatibility_score" in compatibility_result
        assert "compatibility_issues" in compatibility_result
        assert "recommendations" in compatibility_result
        
        compatibility_score = compatibility_result["compatibility_score"]
        assert 0.0 <= compatibility_score <= 1.0
        
        # For this high-quality unit, expect good compatibility
        assert compatibility_score >= 0.8, f"Expected high compatibility for quality unit, got {compatibility_score}"
        
        # Validate efficiency results
        assert isinstance(efficiency_result, dict)
        assert "efficiency_rating" in efficiency_result
        assert "energy_savings" in efficiency_result
        
        efficiency_rating = efficiency_result["efficiency_rating"]
        assert "overall_score" in efficiency_rating
        assert "rating_level" in efficiency_rating
        
        # High SEER unit should get excellent rating
        assert efficiency_rating["overall_score"] >= 0.9
        assert efficiency_rating["rating_level"] in ["excellent", "very_good"]
        
        # Performance validation
        e2e_performance_timer.assert_within_sla(2.0)
        
        print(f"HVAC E2E Results:")
        print(f"  Compatibility Score: {compatibility_score:.3f}")
        print(f"  Efficiency Rating: {efficiency_rating['rating_level']} ({efficiency_rating['overall_score']:.3f})")
        print(f"  Recommendations: {len(compatibility_result['recommendations'])} items")
    
    @pytest.mark.skipif(not CUSTOM_WORKFLOWS_AVAILABLE, reason="Custom workflows not available")
    def test_hvac_workflow_with_sdk_pattern(self, e2e_performance_timer):
        """Test HVAC workflow using proper SDK pattern: runtime.execute(workflow.build())"""
        
        product_data = {
            "name": "Trane XR16 Heat Pump",
            "btu_capacity": 48000,  # 4-ton unit
            "seer_rating": 16.0,
            "hspf_rating": 9.0,
            "refrigerant_type": "R-410A",
            "energy_star": True
        }
        
        system_requirements = {
            "btu_requirement": 45000,
            "minimum_seer": 15.0,
            "minimum_hspf": 8.5,
            "refrigerant_type": "R-410A"
        }
        
        with e2e_performance_timer.time_workflow("hvac_sdk_pattern"):
            # Create workflow using WorkflowBuilder
            workflow = WorkflowBuilder()
            
            # Add nodes using string-based API (SDK pattern)
            workflow.add_node(
                "HVACCompatibilityNode", "hvac_compatibility",
                {
                    "product_data": product_data,
                    "system_requirements": system_requirements,
                    "efficiency_threshold": 0.8
                }
            )
            
            workflow.add_node(
                "HVACEfficiencyNode", "hvac_efficiency", 
                {
                    "product_data": product_data,
                    "efficiency_requirements": system_requirements,
                    "energy_costs": {"electricity": 0.12, "gas": 1.20},
                    "usage_hours": 2500
                }
            )
            
            # Execute using proper SDK pattern: runtime.execute(workflow.build())
            runtime = LocalRuntime()
            results, run_id = runtime.execute(workflow.build())
        
        # Validate SDK pattern execution
        assert run_id is not None
        assert isinstance(results, dict)
        assert "hvac_compatibility" in results
        assert "hvac_efficiency" in results
        
        # Validate workflow results
        compatibility_result = results["hvac_compatibility"]
        efficiency_result = results["hvac_efficiency"]
        
        assert compatibility_result["compatibility_score"] >= 0.8  # Good match
        assert efficiency_result["efficiency_rating"]["overall_score"] >= 0.8
        
        # Performance validation
        e2e_performance_timer.assert_within_sla(2.0)
        
        print(f"HVAC SDK Pattern Results:")
        print(f"  Run ID: {run_id}")
        print(f"  Compatibility: {compatibility_result['compatibility_score']:.3f}")
        print(f"  Efficiency: {efficiency_result['efficiency_rating']['rating_level']}")


class TestElectricalClassificationWorkflowE2E: 
    """End-to-end tests for electrical classification workflow"""
    
    @pytest.mark.skipif(not CUSTOM_WORKFLOWS_AVAILABLE, reason="Custom workflows not available")
    def test_electrical_safety_workflow_complete(self, e2e_performance_timer):
        """Test complete electrical safety analysis workflow"""
        
        # Real electrical component data
        product_data = {
            "name": "Square D Homeline 20A GFCI Circuit Breaker",
            "type": "circuit_breaker",
            "voltage_rating": {"min": 115, "max": 125, "nominal": 120},
            "amperage": 20,
            "ul_listed": True,
            "ul_number": "E12345",
            "nec_compliant": True,
            "gfci_protected": True,
            "afci_compatible": True,
            "grounding_compatible": True,
            "overcurrent_protection": True,
            "lockout_tagout_compatible": True
        }
        
        installation_context = {
            "supply_voltage": {"nominal": 120},
            "circuit_type": "residential",
            "installation_location": "bathroom",
            "work_environment": "residential"
        }
        
        with e2e_performance_timer.time_workflow("electrical_safety_full"):
            # Execute electrical safety analysis
            safety_node = ElectricalSafetyNode()
            
            safety_result = safety_node.run({
                "product_data": product_data,
                "installation_context": installation_context,
                "safety_standards": ["NEC", "UL", "OSHA"],
                "strict_compliance": True
            })
        
        # Validate safety analysis results
        assert isinstance(safety_result, dict)
        assert "safety_rating" in safety_result
        assert "code_compliance" in safety_result
        assert "voltage_compatibility" in safety_result
        assert "certifications" in safety_result
        assert "overall_compliant" in safety_result
        
        # For this well-certified component, expect good safety rating
        safety_rating = safety_result["safety_rating"]
        assert "safety_level" in safety_rating
        assert safety_rating["safety_level"] in ["excellent", "very_good", "good"]
        
        # Voltage should be compatible
        voltage_compatibility = safety_result["voltage_compatibility"]
        assert voltage_compatibility["status"] == "compatible"
        
        # Should be compliant with standards
        code_compliance = safety_result["code_compliance"]
        assert code_compliance["overall_compliant"] is True
        
        # Performance validation
        e2e_performance_timer.assert_within_sla(2.0)
        
        print(f"Electrical Safety E2E Results:")
        print(f"  Safety Level: {safety_rating['safety_level']}")
        print(f"  Overall Compliant: {safety_result['overall_compliant']}")
        print(f"  Safety Issues: {len(safety_result.get('safety_issues', []))}")
    
    @pytest.mark.skipif(not CUSTOM_WORKFLOWS_AVAILABLE, reason="Custom workflows not available")
    def test_electrical_workflow_with_issues(self, e2e_performance_timer):
        """Test electrical workflow with safety issues to validate error detection"""
        
        # Problematic electrical component
        problem_product_data = {
            "name": "Generic 30A Breaker",
            "type": "circuit_breaker",
            "voltage_rating": {"min": 200, "max": 250, "nominal": 240},  # Wrong voltage
            "amperage": 30,
            "ul_listed": False,  # Not certified
            "nec_compliant": False,  # Not compliant
            "gfci_protected": False,  # Missing GFCI for bathroom
            "grounding_compatible": False  # Not grounded
        }
        
        installation_context = {
            "supply_voltage": {"nominal": 120},  # Voltage mismatch
            "circuit_type": "residential",
            "installation_location": "bathroom",  # Requires GFCI
            "work_environment": "residential"
        }
        
        with e2e_performance_timer.time_workflow("electrical_safety_problems"):
            safety_node = ElectricalSafetyNode()
            
            problem_result = safety_node.run({
                "product_data": problem_product_data,
                "installation_context": installation_context,
                "safety_standards": ["NEC", "UL", "OSHA"],
                "strict_compliance": True
            })
        
        # Should detect problems
        assert problem_result["overall_compliant"] is False
        
        # Should identify voltage compatibility issues
        voltage_compatibility = problem_result["voltage_compatibility"]
        assert voltage_compatibility["status"] in ["undervoltage", "overvoltage"]
        
        # Should have safety issues
        safety_issues = problem_result.get("safety_issues", [])
        assert len(safety_issues) > 0
        
        # Should have low safety rating
        safety_rating = problem_result["safety_rating"]
        assert safety_rating["safety_level"] in ["poor", "acceptable"]
        
        # Performance validation  
        e2e_performance_timer.assert_within_sla(2.0)
        
        print(f"Electrical Problems E2E Results:")
        print(f"  Safety Issues Found: {len(safety_issues)}")
        print(f"  Voltage Status: {voltage_compatibility['status']}")
        print(f"  Safety Level: {safety_rating['safety_level']}")


class TestToolClassificationWorkflowE2E:
    """End-to-end tests for tool classification workflow"""
    
    @pytest.mark.skipif(not CUSTOM_WORKFLOWS_AVAILABLE, reason="Custom workflows not available")
    def test_tool_suitability_workflow_complete(self, e2e_performance_timer):
        """Test complete tool suitability analysis workflow"""
        
        # Real tool data
        product_data = {
            "name": "DeWalt DCD771C2 20V MAX Cordless Drill Driver Kit",
            "tool_type": "power_drill",
            "power_source": "battery",
            "voltage": 20,
            "skill_level": "intermediate", 
            "weight": 3.6,
            "safety_features": ["LED light", "belt hook", "keyless chuck", "clutch"],
            "dimensions": {"length": 8.5, "height": 10.2, "width": 3.2},
            "torque_rating": 300,
            "battery_life": "extended"
        }
        
        project_context = {
            "project_type": "home_renovation",
            "user_skill_level": "intermediate",
            "material_types": ["wood", "drywall", "composite"],
            "workspace": "indoor",
            "power_available": True,
            "user_experience_years": 5,
            "space_constraints": {"max_length": 12}
        }
        
        with e2e_performance_timer.time_workflow("tool_suitability_full"):
            # Execute tool suitability analysis
            suitability_node = ToolSuitabilityNode()
            
            suitability_result = suitability_node.run({
                "product_data": product_data,
                "project_context": project_context,
                "user_profile": {"skill_level": "intermediate", "experience_years": 5},
                "safety_priority": "high"
            })
        
        # Validate suitability results
        assert isinstance(suitability_result, dict)
        assert "project_suitability" in suitability_result
        assert "skill_level_requirements" in suitability_result
        assert "safety_considerations" in suitability_result
        assert "material_compatibility" in suitability_result
        assert "overall_suitability" in suitability_result
        
        # For this good match, expect high suitability
        overall_suitability = suitability_result["overall_suitability"]
        assert "score" in overall_suitability
        assert overall_suitability["score"] >= 0.7  # Should be suitable
        
        # Project suitability should be good (drill for home renovation)
        project_suitability = suitability_result["project_suitability"]
        assert project_suitability["score"] >= 0.8
        
        # Skill level should match
        skill_requirements = suitability_result["skill_level_requirements"]
        assert skill_requirements["match_status"] in ["appropriate", "challenging_but_manageable"]
        
        # Material compatibility should be good (wood, drywall)
        material_compatibility = suitability_result["material_compatibility"]
        assert material_compatibility["score"] >= 0.8
        
        # Performance validation
        e2e_performance_timer.assert_within_sla(2.0)
        
        print(f"Tool Suitability E2E Results:")
        print(f"  Overall Score: {overall_suitability['score']:.3f}")
        print(f"  Recommendation: {overall_suitability['recommendation']}")
        print(f"  Material Compatibility: {material_compatibility['status']}")
    
    @pytest.mark.skipif(not CUSTOM_WORKFLOWS_AVAILABLE, reason="Custom workflows not available")
    def test_tool_skill_mismatch_workflow(self, e2e_performance_timer):
        """Test tool workflow with skill level mismatch"""
        
        # Professional-grade tool
        professional_tool_data = {
            "name": "Hilti TE 30-C Max Rotary Hammer",
            "tool_type": "rotary_hammer",
            "power_source": "corded",
            "skill_level": "professional",  # Requires professional skill
            "weight": 8.6,  # Heavy tool
            "safety_features": ["vibration_control", "dust_extraction", "active_torque_control"],
            "power_watts": 1010
        }
        
        beginner_project_context = {
            "project_type": "home_improvement",
            "user_skill_level": "beginner",  # Skill mismatch
            "material_types": ["concrete"],
            "workspace": "indoor",
            "user_experience_years": 0  # No experience
        }
        
        with e2e_performance_timer.time_workflow("tool_skill_mismatch"):
            suitability_node = ToolSuitabilityNode()
            
            mismatch_result = suitability_node.run({
                "product_data": professional_tool_data,
                "project_context": beginner_project_context,
                "user_profile": {"skill_level": "beginner", "experience_years": 0},
                "safety_priority": "high"
            })
        
        # Should detect skill mismatch
        skill_requirements = mismatch_result["skill_level_requirements"]
        assert skill_requirements["match_status"] == "beyond_current_skill"
        assert skill_requirements["training_recommended"] is True
        assert skill_requirements["skill_gap"] > 0
        
        # Overall suitability should be low
        overall_suitability = mismatch_result["overall_suitability"]
        assert overall_suitability["score"] < 0.7  # Not suitable
        assert overall_suitability["recommendation"] in ["not_recommended", "acceptable_with_caution"]
        
        # Should have safety concerns
        safety_considerations = mismatch_result["safety_considerations"]
        safety_concerns = skill_requirements.get("safety_concerns", [])
        assert len(safety_concerns) > 0
        
        # Performance validation
        e2e_performance_timer.assert_within_sla(2.0)
        
        print(f"Tool Skill Mismatch E2E Results:")
        print(f"  Skill Gap: {skill_requirements['skill_gap']} levels")
        print(f"  Safety Concerns: {len(safety_concerns)}")
        print(f"  Overall Score: {overall_suitability['score']:.3f}")


class TestWorkflowPerformanceE2E:
    """End-to-end performance tests for all custom workflows"""
    
    @pytest.mark.skipif(not CUSTOM_WORKFLOWS_AVAILABLE, reason="Custom workflows not available")
    def test_all_workflows_performance_sla(self, e2e_performance_timer):
        """Test that all custom workflows meet <2s performance SLA"""
        
        # Test data for each workflow type
        test_scenarios = [
            ("hvac_performance", {
                "workflow_type": "hvac",
                "product_data": {
                    "name": "Test HVAC Unit",
                    "btu_capacity": 24000,
                    "seer_rating": 16.0,
                    "refrigerant_type": "R-410A"
                },
                "system_requirements": {"btu_requirement": 25000}
            }),
            ("electrical_performance", {
                "workflow_type": "electrical",
                "product_data": {
                    "name": "Test Circuit Breaker",
                    "type": "circuit_breaker",
                    "voltage_rating": {"nominal": 120},
                    "amperage": 20,
                    "ul_listed": True
                },
                "installation_context": {"supply_voltage": {"nominal": 120}}
            }),
            ("tool_performance", {
                "workflow_type": "tool",
                "product_data": {
                    "name": "Test Drill",
                    "tool_type": "power_drill",
                    "power_source": "battery",
                    "skill_level": "intermediate"
                },
                "project_context": {"project_type": "home_renovation", "user_skill_level": "intermediate"}
            })
        ]
        
        performance_results = []
        
        for scenario_name, scenario_data in test_scenarios:
            with e2e_performance_timer.time_workflow(scenario_name):
                if scenario_data["workflow_type"] == "hvac":
                    node = HVACCompatibilityNode()
                    result = node.run({
                        "product_data": scenario_data["product_data"],
                        "system_requirements": scenario_data["system_requirements"]
                    })
                elif scenario_data["workflow_type"] == "electrical":
                    node = ElectricalSafetyNode()
                    result = node.run({
                        "product_data": scenario_data["product_data"],
                        "installation_context": scenario_data["installation_context"]
                    })
                elif scenario_data["workflow_type"] == "tool":
                    node = ToolSuitabilityNode()
                    result = node.run({
                        "product_data": scenario_data["product_data"],
                        "project_context": scenario_data["project_context"]
                    })
                
                # Verify result is valid
                assert isinstance(result, dict)
                assert len(result) > 0
            
            # Check performance SLA for each workflow
            e2e_performance_timer.assert_within_sla(2.0)
        
        # Get performance summary
        summary = e2e_performance_timer.get_summary()
        
        # All workflows should meet business SLA
        assert summary["all_within_2s"], f"Some workflows exceeded 2s SLA: {summary}"
        
        print(f"E2E Performance Summary:")
        print(f"  Total Workflows: {summary['total_workflows']}")
        print(f"  Average Duration: {summary['average_duration']:.3f}s")
        print(f"  Max Duration: {summary['max_duration']:.3f}s")
        print(f"  All Within 2s SLA: {summary['all_within_2s']}")
        
        return summary


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])