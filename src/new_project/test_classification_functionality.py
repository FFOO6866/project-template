#!/usr/bin/env python3
"""
Functionality Test for Fixed Classification Nodes
===============================================

Test that our SDK compliance fixes don't break existing functionality.
This verifies the business logic still works correctly.
"""

import sys
import os
import time
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Apply Windows compatibility patch
import platform
if platform.system() == 'Windows':
    import windows_patch

def test_unspsc_classification():
    """Test UNSPSC classification functionality"""
    print("Testing UNSPSC Classification...")
    
    try:
        from nodes.classification_nodes import UNSPSCClassificationNode
        
        node = UNSPSCClassificationNode()
        
        # Test with cordless drill
        test_input = {
            "product_data": {
                "name": "DeWalt 20V MAX Cordless Drill", 
                "description": "Professional cordless drill with brushless motor",
                "category": "power tools"
            },
            "include_hierarchy": True,
            "confidence_threshold": 0.8
        }
        
        result = node.run(test_input)
        
        print(f"  UNSPSC Result: {result.get('unspsc_code')} - {result.get('unspsc_title')}")
        print(f"  Confidence: {result.get('confidence')}")
        print(f"  Within SLA: {result.get('within_sla')}")
        
        assert "unspsc_code" in result, "Missing UNSPSC code"
        assert "confidence" in result, "Missing confidence score"
        assert isinstance(result.get("confidence"), (int, float)), "Confidence should be numeric"
        
        return True
        
    except Exception as e:
        print(f"  FAILED: {e}")
        return False

def test_etim_classification():
    """Test ETIM classification functionality"""
    print("Testing ETIM Classification...")
    
    try:
        from nodes.classification_nodes import ETIMClassificationNode
        
        node = ETIMClassificationNode()
        
        # Test with cordless drill in German
        test_input = {
            "product_data": {
                "name": "Cordless Drill",
                "description": "Professional drilling tool"
            },
            "language": "de",
            "include_attributes": True,
            "confidence_threshold": 0.8
        }
        
        result = node.run(test_input)
        
        print(f"  ETIM Result: {result.get('etim_class_id')} - {result.get('etim_name')}")
        print(f"  Confidence: {result.get('confidence')}")
        print(f"  Language: {result.get('language')}")
        
        assert "etim_class_id" in result, "Missing ETIM class ID"
        assert "confidence" in result, "Missing confidence score"
        assert result.get("language") == "de", "Language not preserved"
        
        return True
        
    except Exception as e:
        print(f"  FAILED: {e}")
        return False

def test_dual_classification():
    """Test dual classification functionality"""
    print("Testing Dual Classification...")
    
    try:
        from nodes.classification_nodes import DualClassificationWorkflowNode
        
        node = DualClassificationWorkflowNode()
        
        # Test with safety helmet
        test_input = {
            "product_data": {
                "name": "Safety Helmet Hard Hat",
                "description": "Industrial safety helmet ANSI compliant",
                "category": "safety equipment"
            },
            "unspsc_confidence_threshold": 0.8,
            "etim_confidence_threshold": 0.8,
            "language": "en"
        }
        
        result = node.run(test_input)
        
        print(f"  Classification Result Available: {'classification_result' in result}")
        if "classification_result" in result:
            cr = result["classification_result"]
            print(f"  UNSPSC: {cr.get('unspsc', {}).get('code', 'N/A')}")
            print(f"  ETIM: {cr.get('etim', {}).get('class_id', 'N/A')}")
            print(f"  Dual Confidence: {cr.get('dual_confidence', 'N/A')}")
        
        assert "classification_result" in result, "Missing classification result"
        assert "performance_metrics" in result, "Missing performance metrics"
        
        return True
        
    except Exception as e:
        print(f"  FAILED: {e}")
        return False

def test_workflow_creation():
    """Test workflow creation with fixed nodes"""
    print("Testing Workflow Creation...")
    
    try:
        from nodes.classification_nodes import create_unspsc_classification_workflow
        
        product_data = {
            "name": "Test Product",
            "description": "Test product for workflow validation"
        }
        
        workflow = create_unspsc_classification_workflow(product_data)
        built_workflow = workflow.build()
        
        print(f"  Workflow created successfully")
        print(f"  Nodes in workflow: {len(built_workflow.nodes) if hasattr(built_workflow, 'nodes') else 'N/A'}")
        
        assert workflow is not None, "Workflow creation failed"
        assert built_workflow is not None, "Workflow build failed"
        
        return True
        
    except Exception as e:
        print(f"  FAILED: {e}")
        return False

def main():
    """Main functionality test"""
    print("Classification Nodes Functionality Test")
    print("=" * 50)
    
    tests = [
        test_unspsc_classification,
        test_etim_classification,
        test_dual_classification,
        test_workflow_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
            print("  PASSED\n")
        else:
            print("  FAILED\n")
    
    print("=" * 50)
    print(f"Functionality Test Summary: {passed}/{total} tests passed")
    print(f"Success rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("All functionality tests passed! SDK compliance fixes successful.")
        return 0
    else:
        print("Some functionality tests failed. Review implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())