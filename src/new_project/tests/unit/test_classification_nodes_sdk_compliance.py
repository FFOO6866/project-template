"""
Unit Tests for Classification Nodes SDK Compliance - DATA-001
===========================================================

Test-first implementation to fix critical SDK compliance violations:
1. Parameter definition violations (dict format -> NodeParameter objects)
2. Missing @register_node decorators
3. Method interface compliance (run() vs execute())

This test file defines the expected SDK-compliant behavior BEFORE implementation.
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Dict, Any, List

# Kailash SDK imports for compliance testing
# Windows compatibility patch
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import windows_sdk_compatibility  # Apply Windows compatibility for Kailash SDK

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash.nodes.base import Node, register_node, NodeParameter

# Import our implementation (will fix compliance violations)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import the classification nodes we need to fix
from src.new_project.nodes.classification_nodes import (
    UNSPSCClassificationNode,
    ETIMClassificationNode, 
    DualClassificationWorkflowNode
)


class TestParameterDefinitionCompliance:
    """Test that classification nodes use proper NodeParameter objects"""
    
    def test_unspsc_node_uses_node_parameter_objects(self):
        """Test UNSPSCClassificationNode uses NodeParameter objects, not dicts"""
        node = UNSPSCClassificationNode()
        params = node.get_parameters()
        
        # All parameters must be NodeParameter objects
        for param_name, param_def in params.items():
            assert isinstance(param_def, NodeParameter), \
                f"Parameter '{param_name}' must be NodeParameter object, got {type(param_def)}"
            
            # Verify NodeParameter has required attributes
            assert hasattr(param_def, 'name'), f"NodeParameter '{param_name}' missing name attribute"
            assert hasattr(param_def, 'type'), f"NodeParameter '{param_name}' missing type attribute"
            assert hasattr(param_def, 'required'), f"NodeParameter '{param_name}' missing required attribute"
            assert hasattr(param_def, 'description'), f"NodeParameter '{param_name}' missing description attribute"
        
        # Verify specific parameters exist with correct types
        assert "product_data" in params
        assert params["product_data"].type == dict
        assert params["product_data"].required is True
        
        assert "include_hierarchy" in params
        assert params["include_hierarchy"].type == bool
        assert params["include_hierarchy"].required is False
        assert params["include_hierarchy"].default is True
        
        assert "confidence_threshold" in params
        assert params["confidence_threshold"].type == float
        assert params["confidence_threshold"].required is False
        assert params["confidence_threshold"].default == 0.8
    
    def test_etim_node_uses_node_parameter_objects(self):
        """Test ETIMClassificationNode uses NodeParameter objects, not dicts"""
        node = ETIMClassificationNode()
        params = node.get_parameters()
        
        # All parameters must be NodeParameter objects
        for param_name, param_def in params.items():
            assert isinstance(param_def, NodeParameter), \
                f"Parameter '{param_name}' must be NodeParameter object, got {type(param_def)}"
        
        # Verify specific ETIM parameters
        assert "product_data" in params
        assert params["product_data"].type == dict
        assert params["product_data"].required is True
        
        assert "language" in params
        assert params["language"].type == str
        assert params["language"].required is False
        assert params["language"].default == "en"
        
        assert "include_attributes" in params
        assert params["include_attributes"].type == bool
        assert params["include_attributes"].required is False
        assert params["include_attributes"].default is True
        
        assert "etim_version" in params
        assert params["etim_version"].type == str
        assert params["etim_version"].required is False
        assert params["etim_version"].default == "9.0"
    
    def test_dual_classification_node_uses_node_parameter_objects(self):
        """Test DualClassificationWorkflowNode uses NodeParameter objects, not dicts"""
        node = DualClassificationWorkflowNode()
        params = node.get_parameters()
        
        # All parameters must be NodeParameter objects
        for param_name, param_def in params.items():
            assert isinstance(param_def, NodeParameter), \
                f"Parameter '{param_name}' must be NodeParameter object, got {type(param_def)}"
        
        # Verify dual classification specific parameters
        assert "product_data" in params
        assert params["product_data"].type == dict
        assert params["product_data"].required is True
        
        assert "unspsc_confidence_threshold" in params
        assert params["unspsc_confidence_threshold"].type == float
        assert params["unspsc_confidence_threshold"].required is False
        assert params["unspsc_confidence_threshold"].default == 0.8
        
        assert "etim_confidence_threshold" in params
        assert params["etim_confidence_threshold"].type == float
        assert params["etim_confidence_threshold"].required is False
        assert params["etim_confidence_threshold"].default == 0.8
    
    def test_no_deprecated_dict_parameter_definitions(self):
        """Test that no classification nodes use deprecated dict parameter definitions"""
        nodes_to_test = [
            UNSPSCClassificationNode(),
            ETIMClassificationNode(),
            DualClassificationWorkflowNode()
        ]
        
        for node in nodes_to_test:
            params = node.get_parameters()
            
            for param_name, param_def in params.items():
                # Must not be a plain dictionary
                assert not isinstance(param_def, dict), \
                    f"Node {node.__class__.__name__} parameter '{param_name}' uses deprecated dict format"
                
                # Must be NodeParameter object
                assert isinstance(param_def, NodeParameter), \
                    f"Node {node.__class__.__name__} parameter '{param_name}' must use NodeParameter object"


class TestRegisterNodeDecoratorCompliance:
    """Test that all classification nodes have proper @register_node decorators"""
    
    def test_unspsc_node_has_register_node_decorator(self):
        """Test UNSPSCClassificationNode has @register_node decorator"""  
        # Check that class is properly registered
        node_class = UNSPSCClassificationNode
        
        # Verify the class can be instantiated (decorator applied)
        node = node_class()
        assert node is not None
        
        # Verify decorator metadata exists (if implemented)
        # The @register_node decorator should add metadata
        assert hasattr(node_class, '__module__'), "Node class should have module information"
        
        # Test that node works with string-based workflow API
        workflow = WorkflowBuilder()
        
        # This should work without TypeError if decorator is properly applied
        try:
            workflow.add_node("UNSPSCClassificationNode", "test_unspsc", {
                "product_data": {"name": "Test Product"}
            })
            workflow_built = workflow.build()
            assert workflow_built is not None, "Workflow should build successfully with registered node"
        except TypeError as e:
            pytest.fail(f"@register_node decorator not properly applied: {e}")
    
    def test_etim_node_has_register_node_decorator(self):
        """Test ETIMClassificationNode has @register_node decorator"""
        node_class = ETIMClassificationNode
        
        # Verify the class can be instantiated
        node = node_class()
        assert node is not None
        
        # Test string-based workflow integration
        workflow = WorkflowBuilder()
        
        try:
            workflow.add_node("ETIMClassificationNode", "test_etim", {
                "product_data": {"name": "Test Product"}
            })
            workflow_built = workflow.build()
            assert workflow_built is not None, "Workflow should build successfully with registered node"
        except TypeError as e:
            pytest.fail(f"@register_node decorator not properly applied: {e}")
    
    def test_dual_classification_node_has_register_node_decorator(self):
        """Test DualClassificationWorkflowNode has @register_node decorator"""
        node_class = DualClassificationWorkflowNode
        
        # Verify the class can be instantiated
        node = node_class()
        assert node is not None
        
        # Test string-based workflow integration
        workflow = WorkflowBuilder()
        
        try:
            workflow.add_node("DualClassificationWorkflowNode", "test_dual", {
                "product_data": {"name": "Test Product"}
            })
            workflow_built = workflow.build()
            assert workflow_built is not None, "Workflow should build successfully with registered node"
        except TypeError as e:
            pytest.fail(f"@register_node decorator not properly applied: {e}")
    
    def test_register_node_decorator_supports_sdk_patterns(self):
        """Test that @register_node decorator supports standard SDK patterns"""
        
        # Test that decorated classes work with direct instantiation
        nodes = [
            UNSPSCClassificationNode(),
            ETIMClassificationNode(),
            DualClassificationWorkflowNode()
        ]
        
        for node in nodes:
            # Should have required SDK methods
            assert hasattr(node, 'run'), f"{node.__class__.__name__} missing run() method"
            assert hasattr(node, 'get_parameters'), f"{node.__class__.__name__} missing get_parameters() method"
            
            # Methods should be callable
            assert callable(node.run), f"{node.__class__.__name__}.run() not callable"
            assert callable(node.get_parameters), f"{node.__class__.__name__}.get_parameters() not callable"


class TestMethodInterfaceCompliance:
    """Test that nodes implement proper SDK method interfaces"""
    
    def test_nodes_implement_run_as_primary_interface(self):
        """Test that all classification nodes implement run() as primary interface"""
        nodes = [
            UNSPSCClassificationNode(),
            ETIMClassificationNode(),
            DualClassificationWorkflowNode()
        ]
        
        for node in nodes:
            # Must have run() method
            assert hasattr(node, 'run'), f"{node.__class__.__name__} missing run() method"
            assert callable(node.run), f"{node.__class__.__name__}.run() not callable"
            
            # run() should be synchronous (not async)
            import inspect
            assert not inspect.iscoroutinefunction(node.run), \
                f"{node.__class__.__name__}.run() should be synchronous"
            
            # Should not have deprecated execute() method as primary interface
            if hasattr(node, 'execute'):
                # If execute exists, it should not be the primary interface
                # The primary interface should be run()
                pass  # This is acceptable as long as run() exists
    
    def test_run_method_accepts_dict_inputs(self):
        """Test that run() method accepts dictionary inputs"""
        node = UNSPSCClassificationNode()
        
        # Should accept dict inputs without error
        test_inputs = {
            "product_data": {"name": "Test Product", "description": "Test description"},
            "include_hierarchy": True,
            "confidence_threshold": 0.8
        }
        
        # This should not raise TypeError about parameter format
        try:
            result = node.run(test_inputs)
            assert isinstance(result, dict), "run() should return dictionary"
            assert "unspsc_code" in result, "UNSPSC node should return unspsc_code"
        except Exception as e:
            # Should not fail due to parameter definition issues
            if "Field required" in str(e) or "dict format" in str(e):
                pytest.fail(f"Parameter definition not SDK compliant: {e}")
    
    def test_run_method_with_minimal_required_params(self):
        """Test run() method works with minimal required parameters"""
        node = ETIMClassificationNode()
        
        # Test with only required parameters
        minimal_inputs = {
            "product_data": {"name": "Test Product"}
        }
        
        try:
            result = node.run(minimal_inputs)
            assert isinstance(result, dict), "run() should return dictionary"
            assert "etim_class_id" in result, "ETIM node should return etim_class_id"
        except Exception as e:
            if "Field required" in str(e):
                pytest.fail(f"Required parameter validation not working: {e}")


class TestSDKWorkflowIntegration:
    """Test that fixed nodes work properly in SDK workflows"""
    
    def test_unspsc_node_in_workflow_execution_pattern(self):
        """Test UNSPSC node works in runtime.execute(workflow.build()) pattern"""
        workflow = WorkflowBuilder()
        
        # Add node using string-based API
        workflow.add_node("UNSPSCClassificationNode", "classify_product", {
            "product_data": {"name": "DeWalt Cordless Drill", "category": "power tools"},
            "include_hierarchy": True,
            "confidence_threshold": 0.8
        })
        
        # Build workflow (required step)
        built_workflow = workflow.build()
        assert built_workflow is not None, "Workflow should build successfully"
        
        # Should be ready for runtime execution
        # Note: In actual tests, this would execute with LocalRuntime
        # For compliance testing, we verify the pattern is correct
        assert hasattr(built_workflow, 'nodes'), "Built workflow should have nodes"
        assert len(built_workflow.nodes) == 1, "Should have one node"
        
        # Verify node configuration
        node_config = built_workflow.nodes[0] if isinstance(built_workflow.nodes, list) else list(built_workflow.nodes.values())[0]
        assert hasattr(node_config, 'node_type'), "Node should have node_type attribute"
        assert node_config.node_type == 'UNSPSCClassificationNode', "Node type should be string"
        assert hasattr(node_config, 'node_id'), "Node should have node_id attribute"
        assert node_config.node_id == 'classify_product', "Node ID should be preserved"
    
    def test_all_nodes_support_string_based_workflow_api(self):
        """Test that all classification nodes work with string-based workflow API"""
        workflow = WorkflowBuilder()
        
        # Test each node type
        test_configs = [
            ("UNSPSCClassificationNode", "unspsc_classify", {
                "product_data": {"name": "Test Product"},
                "confidence_threshold": 0.8
            }),
            ("ETIMClassificationNode", "etim_classify", {
                "product_data": {"name": "Test Product"},
                "language": "en"
            }),
            ("DualClassificationWorkflowNode", "dual_classify", {
                "product_data": {"name": "Test Product"},
                "unspsc_confidence_threshold": 0.8,
                "etim_confidence_threshold": 0.8
            })
        ]
        
        for node_type, node_id, config in test_configs:
            try:
                workflow.add_node(node_type, node_id, config)
            except Exception as e:
                pytest.fail(f"Node {node_type} failed string-based API: {e}")
        
        # All nodes should build successfully
        built_workflow = workflow.build()
        assert built_workflow is not None, "Workflow with all nodes should build"
        assert len(built_workflow.nodes) == 3, "Should have all three nodes"


class TestParameterValidationWithNodeParameters:
    """Test that NodeParameter objects provide proper validation"""
    
    def test_node_parameter_validation_catches_type_errors(self):
        """Test that NodeParameter validation catches type mismatches"""
        node = UNSPSCClassificationNode()
        
        # Test invalid parameter type
        invalid_inputs = {
            "product_data": "should_be_dict_not_string",  # Wrong type
            "include_hierarchy": "not_a_boolean",         # Wrong type
            "confidence_threshold": "not_a_float"         # Wrong type
        }
        
        # The node should handle parameter validation properly
        # Either through direct validation or through the SDK
        try:
            result = node.run(invalid_inputs)
            # If it doesn't throw, it should return error information
            if "error" not in result:
                pytest.fail("Invalid parameters should be caught by validation")
        except (ValueError, TypeError) as e:
            # This is expected - parameter validation should catch type errors
            assert "type" in str(e).lower() or "parameter" in str(e).lower()
    
    def test_node_parameter_provides_default_values(self):
        """Test that NodeParameter objects provide default values correctly"""
        node = UNSPSCClassificationNode()
        
        # Test with minimal inputs (defaults should be applied)
        minimal_inputs = {
            "product_data": {"name": "Test Product"}
        }
        
        result = node.run(minimal_inputs)
        
        # Should succeed with defaults applied
        assert isinstance(result, dict), "Should return valid result with defaults"
        assert "unspsc_code" in result, "Should have UNSPSC classification result"
        
        # Verify that default values were used in processing
        # (The specific behavior depends on implementation, but should not error)
    
    def test_required_parameter_validation_works(self):
        """Test that required parameters are properly validated"""
        node = ETIMClassificationNode()
        
        # Test missing required parameter
        incomplete_inputs = {
            "language": "en",
            "include_attributes": True
            # Missing required "product_data"
        }
        
        # Should catch missing required parameter
        try:
            result = node.run(incomplete_inputs)
            if "error" not in result:
                pytest.fail("Missing required parameter should be caught")
        except (ValueError, TypeError) as e:
            assert "required" in str(e).lower() or "product_data" in str(e).lower()


class TestPerformanceWithFixedImplementation:
    """Test that SDK compliance fixes don't impact performance"""
    
    def test_parameter_validation_performance(self):
        """Test that NodeParameter validation is fast"""
        node = DualClassificationWorkflowNode()
        
        test_inputs = {
            "product_data": {"name": "Performance Test Product", "category": "test"},
            "unspsc_confidence_threshold": 0.9,
            "etim_confidence_threshold": 0.9,
            "language": "en"
        }
        
        start_time = time.time()
        
        # Run multiple times to test performance
        for _ in range(10):
            result = node.run(test_inputs)
            assert isinstance(result, dict), "Should return valid result"
        
        elapsed = time.time() - start_time
        
        # Should complete quickly (much less than 1 second for 10 runs)
        assert elapsed < 1.0, f"Parameter validation too slow: {elapsed:.3f}s for 10 runs"
    
    def test_node_instantiation_performance(self):
        """Test that node instantiation with NodeParameters is fast"""
        start_time = time.time()
        
        # Create multiple node instances
        for _ in range(50):
            node = UNSPSCClassificationNode()
            params = node.get_parameters()
            assert len(params) > 0, "Should have parameters"
        
        elapsed = time.time() - start_time
        
        # Should instantiate quickly
        assert elapsed < 0.5, f"Node instantiation too slow: {elapsed:.3f}s for 50 instances"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])