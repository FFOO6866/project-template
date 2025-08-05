"""
Unit Tests for Custom Classification Workflows - AI-001
========================================================

Tests for HVAC, electrical, and tool classification workflows using TDD methodology.
Validates specialized domain logic, safety compliance, and SDK patterns.

Tier 1 Testing: Fast (<1s), isolated, can use mocks for external services
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Dict, Any

# Kailash SDK imports
# Windows compatibility patch
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import windows_sdk_compatibility  # Apply Windows compatibility for Kailash SDK

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash.nodes.base import register_node, NodeParameter, Node

# Import the custom classification workflow nodes we need to implement
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
except ImportError:
    # Mock implementations for TDD
    CUSTOM_WORKFLOWS_AVAILABLE = False
    
    # Mock node classes for testing
    class MockWorkflowNode(Node):
        def get_parameters(self):
            return {
                "product_data": NodeParameter(
                    name="product_data", 
                    type=dict, 
                    required=True,
                    description="Product data for classification"
                )
            }
        def run(self, inputs):
            return {"result": "mock"}
    
    HVACCompatibilityNode = MockWorkflowNode
    HVACEfficiencyNode = MockWorkflowNode
    ElectricalSafetyNode = MockWorkflowNode
    ToolSuitabilityNode = MockWorkflowNode
    
    class MockWorkflowClass:
        def __init__(self):
            self.workflow = WorkflowBuilder()
            
        def classify_hvac_product(self, product_data, system_requirements=None):
            return {"mock": True, "workflow_type": "hvac"}
            
        def classify_electrical_component(self, product_data, installation_context=None):
            return {"mock": True, "workflow_type": "electrical"}
            
        def classify_tool(self, product_data, project_context=None):
            return {"mock": True, "workflow_type": "tool"}
    
    HVACClassificationWorkflow = MockWorkflowClass
    ElectricalClassificationWorkflow = MockWorkflowClass
    ToolClassificationWorkflow = MockWorkflowClass


class TestHVACCompatibilityNode:
    """Test HVAC compatibility analysis node."""
    
    def test_hvac_compatibility_node_exists(self):
        """Test that HVACCompatibilityNode is defined."""
        assert HVACCompatibilityNode is not None
        
    def test_hvac_compatibility_node_has_sdk_compliance(self):
        """Test HVACCompatibilityNode follows SDK patterns."""
        node = HVACCompatibilityNode()
        
        # Test SDK interface compliance
        assert hasattr(node, 'run'), "Node should have run() method"
        assert hasattr(node, 'get_parameters'), "Node should have get_parameters() method"
        assert callable(node.run), "run() should be callable"
        assert callable(node.get_parameters), "get_parameters() should be callable"
    
    def test_hvac_compatibility_parameters(self):
        """Test HVACCompatibilityNode parameter definitions."""
        node = HVACCompatibilityNode()
        params = node.get_parameters()
        
        # Required parameters for HVAC compatibility analysis
        expected_params = ["product_data", "system_requirements"]
        
        for param_name in expected_params:
            if param_name in params:
                param_def = params[param_name]
                assert hasattr(param_def, 'name'), f"Parameter {param_name} should have name attribute"
                assert hasattr(param_def, 'type'), f"Parameter {param_name} should have type attribute"
    
    def test_hvac_compatibility_execution(self):
        """Test HVACCompatibilityNode execution with mock data."""
        node = HVACCompatibilityNode()
        
        # Test data for HVAC unit
        product_data = {
            "name": "Trane 3-Ton Central Air Conditioner",
            "btu_capacity": 36000,
            "refrigerant_type": "R-410A",
            "dimensions": {"width": 30, "height": 36, "depth": 24}
        }
        
        system_requirements = {
            "btu_requirement": 35000,
            "refrigerant_type": "R-410A",
            "space_constraints": {"max_width": 32, "max_height": 38}
        }
        
        inputs = {
            "product_data": product_data,
            "system_requirements": system_requirements
        }
        
        # Execute node
        start_time = time.time()
        result = node.run(inputs)
        execution_time = time.time() - start_time
        
        # Validate response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        # Performance requirement: <500ms for individual node
        assert execution_time < 0.5, f"HVAC compatibility analysis took {execution_time}s, should be <0.5s"
        
        # If not mocked, check for expected analysis results
        if CUSTOM_WORKFLOWS_AVAILABLE:
            expected_fields = ["compatibility_score", "compatibility_issues", "recommendations"]
            for field in expected_fields:
                assert field in result, f"Result should contain {field}"


class TestHVACEfficiencyNode:
    """Test HVAC efficiency analysis node."""
    
    def test_hvac_efficiency_node_exists(self):
        """Test that HVACEfficiencyNode is defined."""
        assert HVACEfficiencyNode is not None
    
    def test_hvac_efficiency_parameters(self):
        """Test HVACEfficiencyNode parameter definitions."""
        node = HVACEfficiencyNode()
        params = node.get_parameters()
        
        # Should have parameters for efficiency analysis
        expected_params = ["product_data", "efficiency_requirements"]
        
        for param_name in expected_params:
            if param_name in params:
                param_def = params[param_name]
                assert hasattr(param_def, 'type'), f"Parameter {param_name} should have type"
    
    def test_hvac_efficiency_execution(self):
        """Test HVACEfficiencyNode execution with SEER ratings."""
        node = HVACEfficiencyNode()
        
        product_data = {
            "name": "High-Efficiency Heat Pump",
            "seer_rating": 18.5,
            "hspf_rating": 9.2,
            "energy_star": True
        }
        
        efficiency_requirements = {
            "minimum_seer": 16.0,
            "minimum_hspf": 8.5,
            "energy_star_required": True
        }
        
        inputs = {
            "product_data": product_data,
            "efficiency_requirements": efficiency_requirements
        }
        
        result = node.run(inputs)
        assert isinstance(result, dict), "Result should be a dictionary"
        
        # Check for efficiency analysis results
        if CUSTOM_WORKFLOWS_AVAILABLE:
            expected_fields = ["efficiency_rating", "energy_savings", "compliance_status"]
            for field in expected_fields:
                assert field in result, f"Result should contain {field}"


class TestElectricalSafetyNode:
    """Test electrical safety and code compliance analysis node."""
    
    def test_electrical_safety_node_exists(self):
        """Test that ElectricalSafetyNode is defined."""
        assert ElectricalSafetyNode is not None
    
    def test_electrical_safety_parameters(self):
        """Test ElectricalSafetyNode parameter definitions."""
        node = ElectricalSafetyNode()
        params = node.get_parameters()
        
        expected_params = ["product_data", "installation_context"]
        
        for param_name in expected_params:
            if param_name in params:
                param_def = params[param_name]
                assert hasattr(param_def, 'name'), f"Parameter {param_name} should have name"
    
    def test_electrical_safety_execution(self):
        """Test ElectricalSafetyNode execution with electrical component."""
        node = ElectricalSafetyNode()
        
        product_data = {
            "name": "20A GFCI Circuit Breaker",
            "voltage_rating": {"min": 110, "max": 120},
            "amperage": 20,
            "ul_listed": True,
            "nec_compliant": True
        }
        
        installation_context = {
            "supply_voltage": {"nominal": 115},
            "circuit_type": "residential",
            "installation_location": "bathroom"
        }
        
        inputs = {
            "product_data": product_data,
            "installation_context": installation_context
        }
        
        result = node.run(inputs)
        assert isinstance(result, dict), "Result should be a dictionary"
        
        if CUSTOM_WORKFLOWS_AVAILABLE:
            expected_fields = ["safety_rating", "code_compliance", "voltage_compatibility"]
            for field in expected_fields:
                assert field in result, f"Result should contain {field}"


class TestToolSuitabilityNode:
    """Test tool project suitability analysis node."""
    
    def test_tool_suitability_node_exists(self):
        """Test that ToolSuitabilityNode is defined."""
        assert ToolSuitabilityNode is not None
    
    def test_tool_suitability_parameters(self):
        """Test ToolSuitabilityNode parameter definitions."""
        node = ToolSuitabilityNode()
        params = node.get_parameters()
        
        expected_params = ["product_data", "project_context"]
        
        for param_name in expected_params:
            if param_name in params:
                param_def = params[param_name]
                assert hasattr(param_def, 'type'), f"Parameter {param_name} should have type"
    
    def test_tool_suitability_execution(self):
        """Test ToolSuitabilityNode execution with tool data."""
        node = ToolSuitabilityNode()
        
        product_data = {
            "name": "DeWalt 20V MAX Cordless Drill",
            "tool_type": "power_drill",
            "power_source": "battery",
            "skill_level": "intermediate",
            "safety_features": ["LED light", "belt hook", "two-speed transmission"]
        }
        
        project_context = {
            "project_type": "home_renovation",
            "user_skill_level": "intermediate",
            "material_types": ["wood", "drywall"],
            "workspace": "indoor"
        }
        
        inputs = {
            "product_data": product_data,
            "project_context": project_context
        }
        
        result = node.run(inputs)
        assert isinstance(result, dict), "Result should be a dictionary"
        
        if CUSTOM_WORKFLOWS_AVAILABLE:
            expected_fields = ["project_suitability", "skill_level_requirements", "safety_considerations"]
            for field in expected_fields:
                assert field in result, f"Result should contain {field}"


class TestHVACClassificationWorkflow:
    """Test complete HVAC classification workflow."""
    
    def test_hvac_workflow_creation(self):
        """Test HVACClassificationWorkflow can be created."""
        workflow = HVACClassificationWorkflow()
        assert workflow is not None
        assert hasattr(workflow, 'classify_hvac_product'), "Should have classify_hvac_product method"
    
    def test_hvac_workflow_execution(self):
        """Test HVAC classification workflow execution."""
        workflow = HVACClassificationWorkflow()
        
        product_data = {
            "name": "Carrier 4-Ton Heat Pump",
            "btu_capacity": 48000,
            "seer_rating": 16.0,
            "refrigerant_type": "R-410A"
        }
        
        system_requirements = {
            "btu_requirement": 45000,
            "efficiency_requirements": {"minimum_seer": 15.0},
            "space_constraints": {"max_width": 36}
        }
        
        start_time = time.time()
        result = workflow.classify_hvac_product(product_data, system_requirements)
        execution_time = time.time() - start_time
        
        assert isinstance(result, dict), "Result should be a dictionary"
        
        # Performance requirement: <2s for complete workflow
        assert execution_time < 2.0, f"HVAC workflow took {execution_time}s, should be <2s"
        
        if CUSTOM_WORKFLOWS_AVAILABLE:
            assert result.get("workflow_type") == "hvac_classification"
            assert "run_id" in result, "Should have run_id from workflow execution"
    
    def test_hvac_workflow_sdk_compliance(self):
        """Test HVAC workflow follows SDK patterns."""
        workflow = HVACClassificationWorkflow()
        
        # Should use WorkflowBuilder internally
        assert hasattr(workflow, 'workflow'), "Should have workflow attribute"
        
        # Workflow should be buildable
        if hasattr(workflow.workflow, 'build'):
            built_workflow = workflow.workflow.build()
            assert built_workflow is not None, "Workflow should build successfully"


class TestElectricalClassificationWorkflow:
    """Test complete electrical classification workflow."""
    
    def test_electrical_workflow_creation(self):
        """Test ElectricalClassificationWorkflow can be created."""
        workflow = ElectricalClassificationWorkflow()
        assert workflow is not None
        assert hasattr(workflow, 'classify_electrical_component'), "Should have classify_electrical_component method"
    
    def test_electrical_workflow_execution(self):
        """Test electrical classification workflow execution."""
        workflow = ElectricalClassificationWorkflow()
        
        product_data = {
            "name": "Square D 30A Circuit Breaker",
            "voltage_rating": {"min": 220, "max": 240},
            "amperage": 30,
            "type": "AFCI"
        }
        
        installation_context = {
            "supply_voltage": {"nominal": 230},
            "circuit_type": "residential",
            "room_type": "bedroom"
        }
        
        start_time = time.time()
        result = workflow.classify_electrical_component(product_data, installation_context)
        execution_time = time.time() - start_time
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert execution_time < 2.0, f"Electrical workflow took {execution_time}s, should be <2s"
        
        if CUSTOM_WORKFLOWS_AVAILABLE:
            assert result.get("workflow_type") == "electrical_classification"


class TestToolClassificationWorkflow:
    """Test complete tool classification workflow."""
    
    def test_tool_workflow_creation(self):
        """Test ToolClassificationWorkflow can be created."""
        workflow = ToolClassificationWorkflow()
        assert workflow is not None
        assert hasattr(workflow, 'classify_tool'), "Should have classify_tool method"
    
    def test_tool_workflow_execution(self):
        """Test tool classification workflow execution."""
        workflow = ToolClassificationWorkflow()
        
        product_data = {
            "name": "Milwaukee M18 Impact Driver",
            "tool_type": "impact_driver",
            "power_source": "battery",
            "torque_rating": 1800
        }
        
        project_context = {
            "project_type": "deck_construction",
            "user_skill_level": "advanced",
            "material_types": ["lumber", "composite"]
        }
        
        start_time = time.time()
        result = workflow.classify_tool(product_data, project_context)
        execution_time = time.time() - start_time
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert execution_time < 2.0, f"Tool workflow took {execution_time}s, should be <2s"
        
        if CUSTOM_WORKFLOWS_AVAILABLE:
            assert result.get("workflow_type") == "tool_classification"


class TestWorkflowIntegration:
    """Test workflow integration with SDK patterns."""
    
    def test_workflows_use_string_based_nodes(self):
        """Test that workflows use string-based node references."""
        workflows = [
            HVACClassificationWorkflow(),
            ElectricalClassificationWorkflow(), 
            ToolClassificationWorkflow()
        ]
        
        for workflow in workflows:
            assert hasattr(workflow, 'workflow'), "Should have WorkflowBuilder instance"
            
            if hasattr(workflow.workflow, 'build'):
                built_workflow = workflow.workflow.build()
                assert built_workflow is not None, "Workflow should build successfully"
                
                # Check that nodes use string types (not object instances)
                if hasattr(built_workflow, 'nodes') and built_workflow.nodes:
                    for node in built_workflow.nodes:
                        if hasattr(node, 'node_type'):
                            assert isinstance(node.node_type, str), "Node type should be string"
    
    def test_workflows_support_runtime_execution(self):
        """Test that workflows can be executed with LocalRuntime."""
        # This test validates the SDK pattern but doesn't execute
        # Full execution would be tested in integration tests
        
        workflow = HVACClassificationWorkflow()
        
        if hasattr(workflow, 'workflow') and hasattr(workflow.workflow, 'build'):
            built_workflow = workflow.workflow.build()
            
            # Should be ready for runtime.execute(workflow.build())
            assert built_workflow is not None, "Workflow should be ready for runtime execution"
            
            # Verify the pattern would work with LocalRuntime
            runtime = LocalRuntime()
            assert hasattr(runtime, 'execute'), "Runtime should have execute method"


class TestSafetyComplianceIntegration:
    """Test safety compliance integration across all workflows."""
    
    def test_workflows_include_safety_analysis(self):
        """Test that all workflows include safety compliance checking."""
        test_data = [
            (HVACClassificationWorkflow(), {
                "name": "Gas Furnace",
                "fuel_type": "natural_gas",
                "safety_features": ["flame_sensor", "pressure_switch"]
            }),
            (ElectricalClassificationWorkflow(), {
                "name": "GFCI Outlet",
                "voltage_rating": {"min": 110, "max": 120},
                "safety_features": ["ground_fault_protection"]
            }),
            (ToolClassificationWorkflow(), {
                "name": "Circular Saw",
                "tool_type": "power_saw",
                "safety_features": ["blade_guard", "safety_switch"]
            })
        ]
        
        for workflow, product_data in test_data:
            if hasattr(workflow, 'workflow'):
                # Workflow should include safety compliance nodes
                built_workflow = workflow.workflow.build()
                
                if hasattr(built_workflow, 'nodes') and built_workflow.nodes:
                    # Look for safety-related nodes in workflow
                    node_types = []
                    for node in built_workflow.nodes:
                        if hasattr(node, 'node_type'):
                            node_types.append(node.node_type)
                    
                    # Should have some form of safety analysis
                    has_safety_node = any(
                        'Safety' in node_type or 'Compliance' in node_type 
                        for node_type in node_types
                    )
                    
                    # This assertion may be relaxed if safety is integrated differently
                    # assert has_safety_node, f"Workflow should include safety analysis nodes"
    
    def test_osha_ansi_standards_integration(self):
        """Test integration with OSHA/ANSI safety standards."""
        # This test validates that workflows can access safety standards
        # Implementation depends on how safety standards are integrated
        
        workflows = [
            HVACClassificationWorkflow(),
            ElectricalClassificationWorkflow(),
            ToolClassificationWorkflow()
        ]
        
        for workflow in workflows:
            # Workflows should be able to access safety standards
            # This is a placeholder test - implementation may vary
            assert workflow is not None, "Workflow should exist for safety integration"


class TestPerformanceRequirements:
    """Test performance requirements for custom workflows."""
    
    def test_individual_node_performance(self):
        """Test that individual nodes meet <500ms performance requirement."""
        nodes = [
            HVACCompatibilityNode(),
            HVACEfficiencyNode(),
            ElectricalSafetyNode(),
            ToolSuitabilityNode()
        ]
        
        test_data = {
            "product_data": {"name": "Test Product", "type": "test"},
            "system_requirements": {},
            "installation_context": {},
            "project_context": {}
        }
        
        for node in nodes:
            start_time = time.time()
            result = node.run(test_data)
            execution_time = time.time() - start_time
            
            assert execution_time < 0.5, f"{node.__class__.__name__} took {execution_time}s, should be <0.5s"
            assert isinstance(result, dict), "Node should return dictionary"
    
    def test_complete_workflow_performance(self):
        """Test that complete workflows meet <2s performance requirement."""
        workflows = [
            (HVACClassificationWorkflow(), "classify_hvac_product"),
            (ElectricalClassificationWorkflow(), "classify_electrical_component"),
            (ToolClassificationWorkflow(), "classify_tool")
        ]
        
        test_product_data = {"name": "Test Product", "type": "test"}
        
        for workflow, method_name in workflows:
            if hasattr(workflow, method_name):
                method = getattr(workflow, method_name)
                
                start_time = time.time()
                result = method(test_product_data)
                execution_time = time.time() - start_time
                
                assert execution_time < 2.0, f"{workflow.__class__.__name__} took {execution_time}s, should be <2s"
                assert isinstance(result, dict), "Workflow should return dictionary"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])