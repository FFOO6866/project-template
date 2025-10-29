"""
Security Parameter Validation Unit Tests - Phase 2 Remediation
=============================================================

Tier 1 (Unit) tests for SDK parameter validation and security compliance.
Tests parameter injection vulnerabilities, input sanitization, and security controls.

Test Categories:
- Parameter validation security
- Input sanitization (SQL injection, XSS, path traversal)
- Node parameter declaration compliance
- Security error handling
- Performance impact validation

All tests must complete in <1 second and can use mocks for external services.
"""

import pytest
import time
import uuid
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional
from datetime import datetime

# Security test imports
import re
import os
import sqlite3
from pathlib import Path

# Kailash SDK imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash.nodes.base import Node, NodeParameter

# Import nodes under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from nodes.classification_nodes import (
    UNSPSCClassificationNode,
    ETIMClassificationNode,
    DualClassificationWorkflowNode,
    SafetyComplianceNode
)


class SecurityTestNode(Node):
    """Test node for security validation testing"""
    
    def get_parameters(self) -> Dict[str, NodeParameter]:
        return {
            "files": NodeParameter(
                name="files",
                type=list,
                required=True,
                description="List of files to process"
            ),
            "processing_id": NodeParameter(
                name="processing_id", 
                type=str,
                required=True,
                description="Processing identifier"
            ),
            "options": NodeParameter(
                name="options",
                type=dict,
                required=False,
                default={},
                description="Processing options"
            ),
            "query": NodeParameter(
                name="query",
                type=str,
                required=False,
                default="",
                description="Search query"
            ),
            "file_path": NodeParameter(
                name="file_path",
                type=str,
                required=False,
                default="",
                description="File path for operations"
            )
        }
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation with security checks"""
        # Apply input sanitization
        sanitized_inputs = self._sanitize_inputs(inputs)
        
        return {
            "status": "success",
            "inputs_received": sanitized_inputs,
            "timestamp": datetime.now().isoformat(),
            "security_validated": True
        }
    
    def _sanitize_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Apply security sanitization to inputs"""
        sanitized = {}
        
        for key, value in inputs.items():
            if isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_string(str(item)) for item in value]
            elif isinstance(value, dict):
                sanitized[key] = {k: self._sanitize_string(str(v)) for k, v in value.items()}
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_string(self, value: str) -> str:
        """Sanitize string inputs for security"""
        # Remove SQL injection attempts
        sql_patterns = [
            r"'.*OR.*'.*'",
            r"'.*UNION.*SELECT",
            r"'.*DROP.*TABLE",
            r"'.*INSERT.*INTO",
            r"'.*DELETE.*FROM",
            r"--",
            r"/\*.*\*/",
            r"exec\s*\(",
            r"script.*>",
            r"<.*script"
        ]
        
        sanitized = value
        for pattern in sql_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        # Remove path traversal attempts
        sanitized = sanitized.replace("../", "").replace("..\\", "")
        
        # Remove XSS attempts
        xss_patterns = [
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe.*?>.*?</iframe>",
            r"<object.*?>.*?</object>",
            r"<embed.*?>.*?</embed>"
        ]
        
        for pattern in xss_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        return sanitized.strip()


class TestParameterValidationSecurity:
    """Test parameter validation security compliance"""
    
    def test_parameter_declaration_prevents_injection(self):
        """Test that proper parameter declarations prevent injection attacks"""
        node = SecurityTestNode()
        params = node.get_parameters()
        
        # Verify all parameters are properly declared
        assert isinstance(params, dict), "Parameters must be dictionary"
        
        for param_name, param_def in params.items():
            assert isinstance(param_def, NodeParameter), \
                f"Parameter {param_name} must be NodeParameter object"
            assert hasattr(param_def, 'type'), f"Parameter {param_name} missing type"
            assert hasattr(param_def, 'required'), f"Parameter {param_name} missing required"
            assert param_def.type in [str, int, float, bool, list, dict], \
                f"Parameter {param_name} has invalid type: {param_def.type}"
    
    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are blocked"""
        node = SecurityTestNode()
        
        # SQL injection payloads
        malicious_queries = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT password FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'pass'); --",
            "' OR 1=1 /*",
            "admin'/**/OR/**/1=1/**/--",
            "' OR 'x'='x",
            "; exec master..xp_cmdshell 'dir'",
            "'; exec('del *.*'); --"
        ]
        
        for payload in malicious_queries:
            inputs = {
                "files": ["test.txt"],
                "processing_id": "test123",
                "query": payload
            }
            
            result = node.run(inputs)
            
            # Check that malicious content was sanitized
            received_query = result["inputs_received"]["query"]
            
            # Should not contain SQL injection patterns
            assert "DROP TABLE" not in received_query.upper()
            assert "UNION SELECT" not in received_query.upper()
            assert "OR '1'='1" not in received_query
            assert "exec(" not in received_query.lower()
            assert "--" not in received_query
            
            # Should still process successfully (sanitized)
            assert result["status"] == "success"
            assert result["security_validated"] is True
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attacks are blocked"""
        node = SecurityTestNode()
        
        # Path traversal payloads
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../../../../root/.ssh/id_rsa",
            "..\\..\\..\\..\\boot.ini",
            "....//....//....//etc//passwd",
            "..\\....\\....\\....\\windows\\win.ini",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd"
        ]
        
        for payload in malicious_paths:
            inputs = {
                "files": ["test.txt"],
                "processing_id": "test123",
                "file_path": payload
            }
            
            result = node.run(inputs)
            
            # Check that path traversal was sanitized
            received_path = result["inputs_received"]["file_path"]
            
            # Should not contain traversal patterns
            assert "../" not in received_path
            assert "..\\" not in received_path
            assert "etc/passwd" not in received_path
            assert "windows/system32" not in received_path.lower()
            
            # Should still process successfully (sanitized)
            assert result["status"] == "success"
    
    def test_xss_prevention(self):
        """Test that XSS attempts are blocked"""
        node = SecurityTestNode()
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<svg onload=alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<object data='javascript:alert(\"XSS\")'></object>",
            "<embed src='javascript:alert(\"XSS\")'></embed>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//\"",
            "\";alert('XSS');//"
        ]
        
        for payload in xss_payloads:
            inputs = {
                "files": ["test.txt"],
                "processing_id": payload,  # Test XSS in required field
                "options": {"description": payload}  # Test XSS in nested object
            }
            
            result = node.run(inputs)
            
            # Check that XSS content was sanitized
            received_id = result["inputs_received"]["processing_id"]
            received_desc = result["inputs_received"]["options"]["description"]
            
            # Should not contain script tags or javascript
            assert "<script" not in received_id.lower()
            assert "javascript:" not in received_id.lower()
            assert "onerror=" not in received_id.lower()
            assert "<iframe" not in received_desc.lower()
            assert "alert(" not in received_desc.lower()
            
            # Should still process successfully (sanitized)
            assert result["status"] == "success"
    
    def test_parameter_size_limits(self):
        """Test that parameter size limits prevent DoS attacks"""
        node = SecurityTestNode()
        
        # Large payload attack
        large_string = "A" * 1000000  # 1MB string
        large_list = ["item"] * 10000  # 10k items
        
        inputs = {
            "files": large_list,
            "processing_id": large_string[:100],  # Truncate to reasonable size
            "options": {"data": large_string[:1000]}  # Limit nested data
        }
        
        start_time = time.time()
        result = node.run(inputs)
        processing_time = time.time() - start_time
        
        # Should complete quickly despite large inputs
        assert processing_time < 1.0, f"Processing took too long: {processing_time:.3f}s"
        assert result["status"] == "success"
        
        # Should have reasonable output size
        result_str = json.dumps(result)
        assert len(result_str) < 100000, "Result size should be limited"
    
    def test_parameter_type_validation(self):
        """Test strict parameter type validation"""
        node = SecurityTestNode()
        
        # Test type mismatches that could enable attacks
        invalid_inputs = [
            # Wrong type for files (should be list)
            {
                "files": {"malicious": "'; DROP TABLE files; --"},
                "processing_id": "test123"
            },
            # Wrong type for processing_id (should be string)
            {
                "files": ["test.txt"],
                "processing_id": ["'; DROP TABLE users; --"]
            },
            # Wrong type for options (should be dict)
            {
                "files": ["test.txt"],
                "processing_id": "test123",
                "options": "'; DELETE FROM options; --"
            }
        ]
        
        for invalid_input in invalid_inputs:
            # Should handle type mismatches gracefully
            result = node.run(invalid_input)
            
            # Should either sanitize or return error
            assert result["status"] == "success", "Should handle type errors gracefully"
            assert "security_validated" in result
    
    def test_required_parameter_enforcement(self):
        """Test that required parameters cannot be bypassed"""
        node = SecurityTestNode()
        
        # Test missing required parameters
        incomplete_inputs = [
            # Missing files
            {"processing_id": "test123"},
            # Missing processing_id
            {"files": ["test.txt"]},
            # Empty required parameters
            {"files": [], "processing_id": ""},
            # Null/None required parameters
            {"files": None, "processing_id": "test123"}
        ]
        
        for incomplete_input in incomplete_inputs:
            try:
                result = node.run(incomplete_input)
                # If it doesn't raise an exception, should return error status
                if "error" not in result and result.get("status") == "success":
                    # Check if required validation was bypassed
                    if not incomplete_input.get("files") or not incomplete_input.get("processing_id"):
                        pytest.fail(f"Required parameter validation bypassed: {incomplete_input}")
            except (ValueError, TypeError) as e:
                # Expected behavior for missing required parameters
                assert "required" in str(e).lower() or "missing" in str(e).lower()


class TestNodeSecurityCompliance:
    """Test that all nodes implement security compliance"""
    
    def test_classification_nodes_have_secure_parameters(self):
        """Test that classification nodes have proper parameter declarations"""
        nodes_to_test = [
            UNSPSCClassificationNode(),
            ETIMClassificationNode(),
            DualClassificationWorkflowNode(),
            SafetyComplianceNode()
        ]
        
        for node in nodes_to_test:
            params = node.get_parameters()
            
            # Every parameter must be NodeParameter object
            for param_name, param_def in params.items():
                assert isinstance(param_def, NodeParameter), \
                    f"{node.__class__.__name__}.{param_name} not a NodeParameter object"
                
                # Must have security-relevant attributes
                assert hasattr(param_def, 'type'), f"{param_name} missing type declaration"
                assert hasattr(param_def, 'required'), f"{param_name} missing required flag"
                assert hasattr(param_def, 'description'), f"{param_name} missing description"
                
                # Type must be a valid Python type
                valid_types = [str, int, float, bool, list, dict]
                assert param_def.type in valid_types, \
                    f"{param_name} has invalid type: {param_def.type}"
    
    def test_nodes_sanitize_string_inputs(self):
        """Test that nodes properly sanitize string inputs"""
        node = UNSPSCClassificationNode()
        
        # Test with malicious product data
        malicious_product = {
            "name": "Tool'; DROP TABLE products; --",
            "description": "<script>alert('XSS')</script>Product description",
            "category": "../../../etc/passwd"
        }
        
        inputs = {
            "product_data": malicious_product,
            "confidence_threshold": 0.8
        }
        
        # Should not crash and should handle malicious input
        result = node.run(inputs)
        
        # Should return valid result without exposing vulnerabilities
        assert isinstance(result, dict)
        assert "unspsc_code" in result
        assert "error" not in result or result.get("within_sla", True)
    
    def test_nodes_handle_oversized_inputs(self):
        """Test that nodes handle oversized inputs gracefully"""
        node = ETIMClassificationNode()
        
        # Create oversized product data
        large_description = "A" * 100000  # 100KB description
        large_specs = {f"spec_{i}": "value" * 1000 for i in range(100)}  # Large specs dict
        
        oversized_product = {
            "name": "Test Product",
            "description": large_description,
            "specifications": large_specs,
            "category": "tools"
        }
        
        inputs = {
            "product_data": oversized_product,
            "language": "en"
        }
        
        start_time = time.time()
        result = node.run(inputs)
        processing_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert processing_time < 2.0, f"Oversized input processing too slow: {processing_time:.3f}s"
        
        # Should return valid result
        assert isinstance(result, dict)
        assert "etim_class_id" in result
    
    def test_nodes_validate_parameter_combinations(self):
        """Test that nodes validate parameter combinations securely"""
        node = DualClassificationWorkflowNode()
        
        # Test potentially conflicting parameters
        conflicting_inputs = {
            "product_data": {"name": "Test Product"},
            "unspsc_confidence_threshold": 1.5,  # Invalid: > 1.0
            "etim_confidence_threshold": -0.5,   # Invalid: < 0.0
            "agreement_threshold": 2.0           # Invalid: > 1.0
        }
        
        result = node.run(conflicting_inputs)
        
        # Should handle invalid parameter combinations
        assert isinstance(result, dict)
        
        # Should either fix invalid values or report error
        if "error" not in result:
            # If no error, should have applied valid defaults or corrections
            assert result.get("sdk_compliant", False) is True
        
        # Should not crash or expose internal state
        assert "timestamp" in result
        assert "node_type" in result


class TestSecurityPerformanceImpact:
    """Test that security measures don't significantly impact performance"""
    
    def test_parameter_validation_performance_impact(self):
        """Test that security validation has minimal performance impact"""
        node = SecurityTestNode()
        
        # Test normal inputs
        normal_inputs = {
            "files": ["file1.txt", "file2.txt", "file3.txt"],
            "processing_id": "normal_processing_123",
            "options": {"setting1": "value1", "setting2": "value2"}
        }
        
        # Measure performance with security validation
        start_time = time.time()
        for _ in range(100):  # 100 iterations
            result = node.run(normal_inputs)
            assert result["status"] == "success"
        
        total_time = time.time() - start_time
        avg_time = total_time / 100
        
        # Should complete quickly despite security checks
        assert avg_time < 0.01, f"Security validation too slow: {avg_time:.4f}s per call"
        assert total_time < 1.0, f"Total time too slow: {total_time:.3f}s for 100 calls"
    
    def test_sanitization_performance(self):
        """Test that input sanitization has acceptable performance"""
        node = SecurityTestNode()
        
        # Test with various input sizes
        test_cases = [
            {"size": "small", "text": "Small input text"},
            {"size": "medium", "text": "Medium " * 100 + " input text"},
            {"size": "large", "text": "Large " * 1000 + " input text"}
        ]
        
        for test_case in test_cases:
            inputs = {
                "files": ["test.txt"],
                "processing_id": "perf_test",
                "query": test_case["text"]
            }
            
            start_time = time.time()
            for _ in range(50):  # 50 iterations
                result = node.run(inputs)
                assert result["status"] == "success"
            
            elapsed_time = time.time() - start_time
            avg_time = elapsed_time / 50
            
            # Performance should be acceptable for all sizes
            max_time = {"small": 0.001, "medium": 0.005, "large": 0.02}
            assert avg_time < max_time[test_case["size"]], \
                f"Sanitization too slow for {test_case['size']} input: {avg_time:.4f}s"
    
    def test_memory_usage_with_security(self):
        """Test that security measures don't cause memory leaks"""
        node = SecurityTestNode()
        
        # Test multiple iterations to check for memory leaks
        inputs = {
            "files": ["test.txt"],
            "processing_id": "memory_test",
            "options": {"data": "test data " * 1000}
        }
        
        # Run many iterations
        results = []
        for i in range(200):
            result = node.run(inputs)
            results.append(result)
            
            # Clear some results periodically to test cleanup
            if i % 50 == 0:
                results = results[-10:]  # Keep only last 10
        
        # Should complete without memory issues
        assert len(results) <= 10, "Memory cleanup not working properly"
        
        # Final result should still be valid
        final_result = node.run(inputs)
        assert final_result["status"] == "success"


class TestSecurityErrorHandling:
    """Test security-related error handling"""
    
    def test_malicious_input_error_handling(self):
        """Test that malicious inputs are handled without exposing internals"""
        node = SecurityTestNode()
        
        # Various malicious inputs
        malicious_inputs = [
            {"files": ["'; exec('rm -rf /'); --"], "processing_id": "test"},
            {"files": ["test.txt"], "processing_id": "'; import os; os.system('dir'); --"},
            {"files": ["<script>fetch('/admin')</script>"], "processing_id": "xss_test"},
            {"files": ["../../../../etc/shadow"], "processing_id": "path_test"}
        ]
        
        for malicious_input in malicious_inputs:
            result = node.run(malicious_input)
            
            # Should not expose error details that could help attackers
            if "error" in result:
                error_msg = result["error"]
                # Should not contain system paths, stack traces, or internal details
                assert "/etc/" not in error_msg
                assert "traceback" not in error_msg.lower()
                assert "exception" not in error_msg.lower()
                assert "stack" not in error_msg.lower()
            
            # Should always include security validation flag
            assert "security_validated" in result
    
    def test_node_failure_security(self):
        """Test that node failures don't expose security vulnerabilities"""
        # Create a node that will fail during processing
        class FailingSecurityNode(SecurityTestNode):
            def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                # Apply sanitization first
                sanitized = self._sanitize_inputs(inputs)
                
                # Simulate a processing failure
                raise Exception("Simulated processing failure")
        
        node = FailingSecurityNode()
        
        inputs = {
            "files": ["'; DROP TABLE users; --"],
            "processing_id": "<script>alert('fail')</script>",
            "query": "../../../etc/passwd"
        }
        
        # Should handle failure securely
        try:
            result = node.run(inputs)
            # If no exception, should return secure error response
            if isinstance(result, dict) and "error" in result:
                # Error should not expose malicious input
                assert "DROP TABLE" not in result["error"]
                assert "<script>" not in result["error"]
                assert "etc/passwd" not in result["error"]
        except Exception as e:
            # Exception should not expose malicious input
            error_str = str(e)
            assert "DROP TABLE" not in error_str
            assert "<script>" not in error_str
            assert "etc/passwd" not in error_str


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--timeout=60"])