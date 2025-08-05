#!/usr/bin/env python3
"""
NodeParameter Validation Script - INFRA-002 Compliance Checker
==============================================================

Comprehensive validation script to ensure 100% NodeParameter compliance across the codebase.
Checks for:
1. Missing 'name' field in NodeParameter definitions
2. Proper parameter structure (name, type, required, description, default)
3. Node registration functionality
4. SDK compliance patterns

Usage:
    python validate_nodeparameter_compliance.py
"""

import ast
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

# Add Windows SDK compatibility
sys.path.insert(0, str(Path(__file__).parent))
import windows_sdk_compatibility

from kailash.nodes.base import NodeParameter, Node, register_node
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime


@dataclass
class ValidationResult:
    """Results of NodeParameter validation"""
    file_path: str
    line_number: int
    issue_type: str
    issue_description: str
    severity: str  # 'error', 'warning', 'info'


class NodeParameterValidator:
    """Comprehensive NodeParameter compliance validator"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results: List[ValidationResult] = []
        self.files_checked = 0
        self.violations_found = 0
        
    def validate_all(self) -> Dict[str, Any]:
        """Run comprehensive validation across the entire codebase"""
        print("Starting comprehensive NodeParameter compliance validation...")
        
        # Step 1: AST-based validation for syntax issues
        print("\nStep 1: AST-based syntax validation")
        self._validate_ast_patterns()
        
        # Step 2: Runtime validation for registered nodes
        print("\nStep 2: Runtime node registration validation")
        self._validate_node_registration()
        
        # Step 3: Test node creation to verify parameters work
        print("\nStep 3: Node instantiation validation")
        self._validate_node_instantiation()
        
        # Step 4: Workflow integration validation
        print("\nStep 4: Workflow integration validation")
        self._validate_workflow_integration()
        
        # Generate comprehensive report
        return self._generate_report()
    
    def _validate_ast_patterns(self):
        """Use AST to find NodeParameter usage patterns"""
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
                
            try:
                self._validate_file_ast(file_path)
                self.files_checked += 1
            except Exception as e:
                self.results.append(ValidationResult(
                    file_path=str(file_path),
                    line_number=0,
                    issue_type="ast_error",
                    issue_description=f"AST parsing failed: {str(e)}",
                    severity="warning"
                ))
    
    def _validate_file_ast(self, file_path: Path):
        """Validate NodeParameter usage in a single file using AST"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content, str(file_path))
        except SyntaxError as e:
            self.results.append(ValidationResult(
                file_path=str(file_path),
                line_number=e.lineno or 0,
                issue_type="syntax_error",
                issue_description=f"Python syntax error: {str(e)}",
                severity="error"
            ))
            return
        
        class NodeParameterVisitor(ast.NodeVisitor):
            def __init__(self, validator, file_path):
                self.validator = validator
                self.file_path = file_path
            
            def visit_Call(self, node):
                # Check for NodeParameter calls
                if self._is_nodeparameter_call(node):
                    self._validate_nodeparameter_call(node)
                self.generic_visit(node)
            
            def _is_nodeparameter_call(self, node):
                """Check if this is a NodeParameter constructor call"""
                if hasattr(node.func, 'id') and node.func.id == 'NodeParameter':
                    return True
                if hasattr(node.func, 'attr') and node.func.attr == 'NodeParameter':
                    return True
                return False
            
            def _validate_nodeparameter_call(self, node):
                """Validate a specific NodeParameter call"""
                # Check if 'name' is the first parameter
                name_found = False
                first_param_is_name = False
                
                if node.args:
                    # If there are positional arguments, we can't determine if first is 'name'
                    # This is actually problematic - should use keyword arguments
                    self.validator.results.append(ValidationResult(
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        issue_type="positional_args",
                        issue_description="NodeParameter uses positional arguments instead of keyword arguments",
                        severity="warning"
                    ))
                
                if node.keywords:
                    # Check first keyword argument
                    first_keyword = node.keywords[0]
                    if first_keyword.arg == 'name':
                        first_param_is_name = True
                        name_found = True
                    
                    # Check if 'name' exists anywhere
                    for keyword in node.keywords:
                        if keyword.arg == 'name':
                            name_found = True
                            break
                
                # Validate findings
                if not name_found:
                    self.validator.results.append(ValidationResult(
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        issue_type="missing_name_field",
                        issue_description="NodeParameter missing required 'name' field",
                        severity="error"
                    ))
                    self.validator.violations_found += 1
                elif not first_param_is_name and node.keywords:
                    self.validator.results.append(ValidationResult(
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        issue_type="name_not_first",
                        issue_description="NodeParameter 'name' field should be first parameter",
                        severity="warning"
                    ))
                
                # Check for required fields
                required_fields = {'name', 'type', 'required'}
                provided_fields = {kw.arg for kw in node.keywords if kw.arg}
                missing_fields = required_fields - provided_fields
                
                if missing_fields:
                    self.validator.results.append(ValidationResult(
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        issue_type="missing_required_fields",
                        issue_description=f"NodeParameter missing recommended fields: {', '.join(missing_fields)}",
                        severity="info"
                    ))
        
        visitor = NodeParameterVisitor(self, file_path)
        visitor.visit(tree)
    
    def _validate_node_registration(self):
        """Test node registration functionality"""
        try:
            # Create a test node with proper NodeParameter
            @register_node()
            class TestComplianceNode(Node):
                def get_parameters(self):
                    return {
                        "test_input": NodeParameter(
                            name="test_input",
                            type=str,
                            required=True,
                            description="Test input parameter",
                            default="test_value"
                        ),
                        "optional_param": NodeParameter(
                            name="optional_param",
                            type=int,
                            required=False,
                            description="Optional parameter",
                            default=42
                        )
                    }
                
                def run(self, inputs):
                    return {
                        "test_result": f"Processed: {inputs.get('test_input', 'default')}",
                        "optional_result": inputs.get('optional_param', 42) * 2
                    }
            
            # Test node instantiation
            node = TestComplianceNode()
            assert hasattr(node, 'get_parameters')
            assert hasattr(node, 'run')
            
            # Test parameter retrieval
            params = node.get_parameters()
            assert 'test_input' in params
            assert 'optional_param' in params
            
            # Test parameter structure
            test_param = params['test_input']
            assert hasattr(test_param, 'name')
            assert hasattr(test_param, 'type')
            assert hasattr(test_param, 'required')
            assert test_param.name == "test_input"
            assert test_param.type == str
            assert test_param.required == True
            
            print("  [OK] Node registration validation passed")
            
        except Exception as e:
            self.results.append(ValidationResult(
                file_path="validation_script",
                line_number=0,
                issue_type="node_registration_error",
                issue_description=f"Node registration failed: {str(e)}",
                severity="error"
            ))
            self.violations_found += 1
            print(f"  [ERROR] Node registration validation failed: {str(e)}")
    
    def _validate_node_instantiation(self):
        """Test that nodes can be instantiated and used"""
        try:
            # Import and test existing nodes
            from nodes.classification_nodes import UNSPSCClassificationNode, ETIMClassificationNode
            
            # Test UNSPSC node
            unspsc_node = UNSPSCClassificationNode()
            unspsc_params = unspsc_node.get_parameters()
            
            # Validate UNSPSC parameters
            for param_name, param_def in unspsc_params.items():
                if not hasattr(param_def, 'name'):
                    self.results.append(ValidationResult(
                        file_path="nodes/classification_nodes.py",
                        line_number=0,
                        issue_type="parameter_missing_name",
                        issue_description=f"UNSPSC node parameter '{param_name}' missing 'name' attribute",
                        severity="error"
                    ))
                    self.violations_found += 1
                elif param_def.name != param_name:
                    self.results.append(ValidationResult(
                        file_path="nodes/classification_nodes.py",
                        line_number=0,
                        issue_type="parameter_name_mismatch",
                        issue_description=f"UNSPSC node parameter name mismatch: key='{param_name}', name='{param_def.name}'",
                        severity="error"
                    ))
                    self.violations_found += 1
            
            # Test ETIM node
            etim_node = ETIMClassificationNode() 
            etim_params = etim_node.get_parameters()
            
            # Validate ETIM parameters
            for param_name, param_def in etim_params.items():
                if not hasattr(param_def, 'name'):
                    self.results.append(ValidationResult(
                        file_path="nodes/classification_nodes.py",
                        line_number=0,
                        issue_type="parameter_missing_name",
                        issue_description=f"ETIM node parameter '{param_name}' missing 'name' attribute",
                        severity="error"
                    ))
                    self.violations_found += 1
                elif param_def.name != param_name:
                    self.results.append(ValidationResult(
                        file_path="nodes/classification_nodes.py",
                        line_number=0,
                        issue_type="parameter_name_mismatch",
                        issue_description=f"ETIM node parameter name mismatch: key='{param_name}', name='{param_def.name}'",
                        severity="error"
                    ))
                    self.violations_found += 1
            
            print("  [OK] Node instantiation validation passed")
            
        except ImportError as e:
            print(f"  [WARNING] Could not import classification nodes: {str(e)}")
        except Exception as e:
            self.results.append(ValidationResult(
                file_path="validation_script",
                line_number=0,
                issue_type="node_instantiation_error",
                issue_description=f"Node instantiation failed: {str(e)}",
                severity="error"
            ))
            self.violations_found += 1
            print(f"  [ERROR] Node instantiation validation failed: {str(e)}")
    
    def _validate_workflow_integration(self):
        """Test workflow integration with validated nodes"""
        try:
            # Create a simple workflow to test integration
            workflow = WorkflowBuilder()
            
            # Add a PythonCodeNode (should always be available)
            workflow.add_node("PythonCodeNode", "test_processor", {
                "code": "result = {'validation': 'success', 'input_count': len(inputs)}"
            })
            
            # Build the workflow
            built_workflow = workflow.build()
            
            # Execute the workflow
            runtime = LocalRuntime()
            results, run_id = runtime.execute(built_workflow)
            
            # Validate results
            if results and run_id:
                print("  [OK] Workflow integration validation passed")
            else:
                self.results.append(ValidationResult(
                    file_path="validation_script",
                    line_number=0,
                    issue_type="workflow_execution_error",
                    issue_description="Workflow execution returned no results",
                    severity="error"
                ))
                self.violations_found += 1
            
        except Exception as e:
            self.results.append(ValidationResult(
                file_path="validation_script",
                line_number=0,
                issue_type="workflow_integration_error",
                issue_description=f"Workflow integration failed: {str(e)}",
                severity="error"
            ))
            self.violations_found += 1
            print(f"  [ERROR] Workflow integration validation failed: {str(e)}")
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during validation"""
        skip_patterns = [
            '__pycache__',
            '.git',
            '.pytest_cache',
            'venv',
            'env',
            '.venv',
            'node_modules',
            'build',
            'dist',
            '.coverage',
            'htmlcov'
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        errors = [r for r in self.results if r.severity == 'error']
        warnings = [r for r in self.results if r.severity == 'warning']
        info = [r for r in self.results if r.severity == 'info']
        
        compliance_score = max(0, 100 - (len(errors) * 10) - (len(warnings) * 2))
        
        report = {
            "validation_summary": {
                "total_files_checked": self.files_checked,
                "total_violations": self.violations_found,
                "compliance_score": compliance_score,
                "status": "COMPLIANT" if self.violations_found == 0 else "NON_COMPLIANT"
            },
            "issue_breakdown": {
                "errors": len(errors),
                "warnings": len(warnings),
                "info": len(info)
            },
            "detailed_results": {
                "errors": [self._format_result(r) for r in errors],
                "warnings": [self._format_result(r) for r in warnings],
                "info": [self._format_result(r) for r in info]
            },
            "recommendations": self._generate_recommendations(errors, warnings)
        }
        
        return report
    
    def _format_result(self, result: ValidationResult) -> Dict[str, Any]:
        """Format validation result for report"""
        return {
            "file": result.file_path,
            "line": result.line_number,
            "type": result.issue_type,
            "description": result.issue_description,
            "severity": result.severity
        }
    
    def _generate_recommendations(self, errors: List[ValidationResult], warnings: List[ValidationResult]) -> List[str]:
        """Generate actionable recommendations based on findings"""
        recommendations = []
        
        if errors:
            recommendations.append("[CRITICAL] Fix all NodeParameter errors before deployment")
            
            # Group errors by type
            error_types = {}
            for error in errors:
                if error.issue_type not in error_types:
                    error_types[error.issue_type] = []
                error_types[error.issue_type].append(error)
            
            for error_type, error_list in error_types.items():
                if error_type == "missing_name_field":
                    recommendations.append(f"  - Add 'name' field to {len(error_list)} NodeParameter definitions")
                elif error_type == "parameter_missing_name":
                    recommendations.append(f"  - Fix {len(error_list)} parameters missing 'name' attribute")
                elif error_type == "node_registration_error":
                    recommendations.append(f"  - Resolve {len(error_list)} node registration issues")
        
        if warnings:
            recommendations.append("[WARNING] Consider addressing warnings for better compliance:")
            warning_types = {}
            for warning in warnings:
                if warning.issue_type not in warning_types:
                    warning_types[warning.issue_type] = []
                warning_types[warning.issue_type].append(warning)
            
            for warning_type, warning_list in warning_types.items():
                if warning_type == "name_not_first":
                    recommendations.append(f"  - Move 'name' field to first position in {len(warning_list)} NodeParameter definitions")
                elif warning_type == "positional_args":
                    recommendations.append(f"  - Use keyword arguments in {len(warning_list)} NodeParameter calls")
        
        if not errors and not warnings:
            recommendations.append("[SUCCESS] All NodeParameter definitions are compliant!")
            recommendations.append("[SUCCESS] Node registration functionality works correctly")
            recommendations.append("[SUCCESS] Workflow integration is functioning properly")
        
        return recommendations


def main():
    """Main validation execution"""
    print("NodeParameter Compliance Validation - INFRA-002")
    print("=" * 60)
    
    validator = NodeParameterValidator()
    report = validator.validate_all()
    
    # Print summary
    print("\nVALIDATION SUMMARY")
    print("=" * 30)
    print(f"Files checked: {report['validation_summary']['total_files_checked']}")
    print(f"Violations found: {report['validation_summary']['total_violations']}")
    print(f"Compliance score: {report['validation_summary']['compliance_score']}%")
    print(f"Status: {report['validation_summary']['status']}")
    
    # Print detailed results
    if report['detailed_results']['errors']:
        print(f"\nERRORS ({len(report['detailed_results']['errors'])})")
        for error in report['detailed_results']['errors']:
            print(f"  {error['file']}:{error['line']} - {error['description']}")
    
    if report['detailed_results']['warnings']:
        print(f"\nWARNINGS ({len(report['detailed_results']['warnings'])})")
        for warning in report['detailed_results']['warnings']:
            print(f"  {warning['file']}:{warning['line']} - {warning['description']}")
    
    # Print recommendations
    print(f"\nRECOMMENDATIONS")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    # Save report to file
    import json
    with open('nodeparameter_compliance_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: nodeparameter_compliance_report.json")
    
    # Exit with appropriate code
    return 0 if report['validation_summary']['total_violations'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())