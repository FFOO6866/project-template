#!/usr/bin/env python3
"""
Test-First Development Runner for SDK Compliance Foundation
========================================================

Comprehensive test runner for the 3-tier testing strategy implementation.
This script validates the test-first development approach for FOUND-001.

Usage:
    python run_tests.py [tier] [options]

Tiers:
    unit        - Run Tier 1 unit tests (fast, mocked dependencies)
    integration - Run Tier 2 integration tests (real Docker services)
    e2e         - Run Tier 3 end-to-end tests (complete workflows)
    all         - Run all test tiers sequentially

Options:
    --performance   - Include performance validation tests
    --compliance    - Run SDK compliance validation
    --setup         - Setup test environment first
    --cleanup       - Cleanup test data after execution
    --verbose       - Verbose output with detailed results
    --parallel      - Run tests in parallel (where supported)

Examples:
    python run_tests.py unit --compliance
    python run_tests.py integration --setup --verbose
    python run_tests.py e2e --performance --cleanup
    python run_tests.py all --setup --cleanup --verbose
"""

import sys
import os
import argparse
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Apply Windows compatibility patch for Kailash SDK
import platform
if platform.system() == 'Windows':
    sys.path.insert(0, str(Path(__file__).parent))
    import windows_patch

# Add project paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root / "tests" / "utils"))
sys.path.append(str(project_root / "src"))

class TestRunner:
    """Test-first development runner for SDK compliance validation"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {}
        self.start_time = None
        self.total_tests_run = 0
        self.total_tests_passed = 0
        self.total_tests_failed = 0
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if self.verbose or level in ["ERROR", "WARNING"]:
            print(f"[{timestamp}] {level}: {message}")
    
    def check_environment(self) -> Dict[str, Any]:
        """Check test environment requirements"""
        self.log("Checking test environment...")
        
        env_status = {
            "python_available": True,
            "pytest_available": False,
            "docker_available": False,
            "kailash_sdk_available": False,
            "test_dependencies": [],
            "missing_dependencies": [],
            "docker_services": {}
        }
        
        # Check Python
        try:
            python_version = sys.version
            self.log(f"Python version: {python_version}")
        except Exception as e:
            env_status["python_available"] = False
            self.log(f"Python check failed: {e}", "ERROR")
        
        # Check pytest
        try:
            import pytest
            env_status["pytest_available"] = True
            self.log(f"pytest version: {pytest.__version__}")
        except ImportError:
            env_status["missing_dependencies"].append("pytest")
            self.log("pytest not available", "WARNING")
        
        # Check Kailash SDK
        try:
            from kailash.workflow.builder import WorkflowBuilder
            env_status["kailash_sdk_available"] = True
            self.log("Kailash SDK available")
        except ImportError:
            env_status["missing_dependencies"].append("kailash")
            self.log("Kailash SDK not available", "WARNING")
        
        # Check Docker utilities
        try:
            from docker_config import DockerConfig
            config = DockerConfig()
            env_status["docker_available"] = True
            env_status["docker_services"] = config.get_service_status()
            self.log("Docker utilities available")
        except ImportError:
            env_status["missing_dependencies"].append("docker")
            self.log("Docker utilities not available", "WARNING")
        
        return env_status
    
    def setup_test_environment(self) -> bool:
        """Setup Docker test environment"""
        self.log("Setting up test environment...")
        
        try:
            # Check if Docker setup script exists
            docker_setup_script = project_root / "tests" / "utils" / "setup_local_docker.py"
            if not docker_setup_script.exists():
                self.log(f"Docker setup script not found: {docker_setup_script}", "WARNING")
                return False
            
            # Run Docker setup
            result = subprocess.run([
                sys.executable, str(docker_setup_script)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("Docker test environment setup completed")
                return True
            else:
                self.log(f"Docker setup failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error setting up test environment: {e}", "ERROR")
            return False
    
    def run_tier_tests(self, tier: str, extra_args: List[str] = None) -> Dict[str, Any]:
        """Run tests for specific tier"""
        self.log(f"Running {tier} tests...")
        
        if extra_args is None:
            extra_args = []
        
        # Determine test path and markers
        test_configs = {
            "unit": {
                "path": "tests/unit/",
                "markers": ["-m", "unit", "--timeout=10"],
                "description": "Unit tests (Tier 1)"
            },
            "integration": {
                "path": "tests/integration/",
                "markers": ["-m", "integration", "--timeout=30"],
                "description": "Integration tests (Tier 2)"
            },
            "e2e": {
                "path": "tests/e2e/",
                "markers": ["-m", "e2e", "--timeout=60"],
                "description": "End-to-end tests (Tier 3)"
            }
        }
        
        if tier not in test_configs:
            raise ValueError(f"Unknown test tier: {tier}")
        
        config = test_configs[tier]
        test_dir = Path(__file__).parent / config["path"]
        
        if not test_dir.exists():
            self.log(f"Test directory not found: {test_dir}", "WARNING")
            return {"status": "skipped", "reason": "Test directory not found"}
        
        # Build pytest command
        pytest_cmd = [
            sys.executable, "-m", "pytest",
            str(test_dir),
            "-v",
            "--tb=short",
            "--color=yes"
        ] + config["markers"] + extra_args
        
        self.log(f"Running: {' '.join(pytest_cmd)}")
        
        try:
            start_time = time.time()
            result = subprocess.run(pytest_cmd, capture_output=True, text=True)
            execution_time = time.time() - start_time
            
            # Parse pytest output for test counts
            output_lines = result.stdout.split('\n')
            
            test_summary = {
                "tier": tier,
                "description": config["description"],
                "status": "passed" if result.returncode == 0 else "failed",
                "return_code": result.returncode,
                "execution_time": execution_time,
                "output": result.stdout,
                "errors": result.stderr,
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_skipped": 0
            }
            
            # Extract test counts from pytest output
            for line in output_lines:
                if "passed" in line and "failed" in line:
                    # Parse line like "2 passed, 1 failed in 0.23s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed," and i > 0:
                            test_summary["tests_passed"] = int(parts[i-1])
                        elif part == "failed" and i > 0:
                            test_summary["tests_failed"] = int(parts[i-1])
                        elif part == "skipped" and i > 0:
                            test_summary["tests_skipped"] = int(parts[i-1])
                elif "passed in" in line:
                    # Parse line like "5 passed in 0.23s"
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "passed":
                        test_summary["tests_passed"] = int(parts[0])
            
            test_summary["tests_run"] = (test_summary["tests_passed"] + 
                                       test_summary["tests_failed"] + 
                                       test_summary["tests_skipped"])
            
            # Update totals
            self.total_tests_run += test_summary["tests_run"]
            self.total_tests_passed += test_summary["tests_passed"]
            self.total_tests_failed += test_summary["tests_failed"]
            
            self.log(f"{tier} tests completed: "
                    f"{test_summary['tests_passed']} passed, "
                    f"{test_summary['tests_failed']} failed, "
                    f"{test_summary['tests_skipped']} skipped "
                    f"in {execution_time:.2f}s")
            
            return test_summary
            
        except Exception as e:
            self.log(f"Error running {tier} tests: {e}", "ERROR")
            return {
                "tier": tier,
                "status": "error",
                "error": str(e),
                "execution_time": 0
            }
    
    def run_compliance_validation(self) -> Dict[str, Any]:
        """Run SDK compliance validation tests"""
        self.log("Running SDK compliance validation...")
        
        compliance_results = {
            "status": "passed",
            "checks_performed": [],
            "violations_found": [],
            "compliance_score": 100
        }
        
        # Check test files exist
        test_files = [
            "tests/unit/test_sdk_compliance_foundation.py",
            "tests/integration/test_sdk_compliance_integration.py", 
            "tests/e2e/test_sdk_compliance_e2e.py"
        ]
        
        for test_file in test_files:
            test_path = Path(__file__).parent / test_file
            if test_path.exists():
                compliance_results["checks_performed"].append(f"Test file exists: {test_file}")
            else:
                compliance_results["violations_found"].append(f"Missing test file: {test_file}")
                compliance_results["compliance_score"] -= 20
        
        # Check test configuration
        config_files = ["pytest.ini", "conftest.py"]
        for config_file in config_files:
            config_path = Path(__file__).parent / config_file
            if config_path.exists():
                compliance_results["checks_performed"].append(f"Config file exists: {config_file}")
            else:
                compliance_results["violations_found"].append(f"Missing config file: {config_file}")
                compliance_results["compliance_score"] -= 10
        
        # Validate test structure
        try:
            # Check unit test structure
            unit_test_file = Path(__file__).parent / "tests/unit/test_sdk_compliance_foundation.py"
            if unit_test_file.exists():
                content = unit_test_file.read_text()
                required_classes = [
                    "TestRegisterNodeDecorator",
                    "TestSecureGovernedNode", 
                    "TestNodeExecutionPatterns",
                    "TestStringBasedNodeConfigurations"
                ]
                
                for test_class in required_classes:
                    if test_class in content:
                        compliance_results["checks_performed"].append(f"Test class found: {test_class}")
                    else:
                        compliance_results["violations_found"].append(f"Missing test class: {test_class}")
                        compliance_results["compliance_score"] -= 5
        
        except Exception as e:
            compliance_results["violations_found"].append(f"Error validating test structure: {e}")
            compliance_results["compliance_score"] -= 10
        
        if compliance_results["violations_found"]:
            compliance_results["status"] = "failed"
        
        self.log(f"Compliance validation completed: "
                f"Score {compliance_results['compliance_score']}/100, "
                f"{len(compliance_results['violations_found'])} violations found")
        
        return compliance_results
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance validation tests"""
        self.log("Running performance validation tests...")
        
        # Run tests with performance markers
        perf_result = self.run_tier_tests("unit", ["-m", "performance"])
        
        performance_summary = {
            "status": perf_result.get("status", "unknown"),
            "execution_time": perf_result.get("execution_time", 0),
            "performance_requirements": {
                "unit_tests_max": 1.0,
                "integration_tests_max": 5.0,
                "e2e_tests_max": 10.0,
                "workflow_response_max": 2.0
            },
            "sla_compliance": {},
            "recommendations": []
        }
        
        # Check SLA compliance
        if perf_result.get("execution_time", 0) > 1.0:
            performance_summary["sla_compliance"]["unit_tests"] = "FAILED"
            performance_summary["recommendations"].append(
                "Unit tests taking too long - optimize test setup and mocking"
            )
        else:
            performance_summary["sla_compliance"]["unit_tests"] = "PASSED"
        
        return performance_summary
    
    def cleanup_test_data(self) -> bool:
        """Cleanup test data and temporary files"""
        self.log("Cleaning up test data...")
        
        try:
            # Remove temporary test files
            temp_files = [
                "/tmp/test_document.txt",
                Path(__file__).parent / "test_output.log"
            ]
            
            for temp_file in temp_files:
                temp_path = Path(temp_file)
                if temp_path.exists():
                    temp_path.unlink()
                    self.log(f"Removed temporary file: {temp_path}")
            
            return True
            
        except Exception as e:
            self.log(f"Error during cleanup: {e}", "ERROR")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test execution report"""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        report = {
            "execution_summary": {
                "start_time": self.start_time,
                "total_execution_time": total_time,
                "total_tests_run": self.total_tests_run,
                "total_tests_passed": self.total_tests_passed,
                "total_tests_failed": self.total_tests_failed,
                "success_rate": (self.total_tests_passed / max(1, self.total_tests_run)) * 100
            },
            "test_results": self.results,
            "environment_info": {
                "python_version": sys.version,
                "working_directory": str(Path.cwd()),
                "test_directory": str(Path(__file__).parent)
            }
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save test report to file"""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"
        
        report_path = Path(__file__).parent / filename
        
        try:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.log(f"Test report saved to: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.log(f"Error saving report: {e}", "ERROR")
            return None

def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(
        description="Test-First Development Runner for SDK Compliance Foundation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "tier",
        choices=["unit", "integration", "e2e", "all"],
        help="Test tier to run"
    )
    
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Include performance validation tests"
    )
    
    parser.add_argument(
        "--compliance", 
        action="store_true",
        help="Run SDK compliance validation"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true", 
        help="Setup test environment first"
    )
    
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Cleanup test data after execution"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output with detailed results"
    )
    
    parser.add_argument(
        "--parallel", 
        action="store_true",
        help="Run tests in parallel (where supported)"
    )
    
    parser.add_argument(
        "--report",
        help="Save detailed report to specified file"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner(verbose=args.verbose)
    runner.start_time = time.time()
    
    try:
        # Check environment
        env_status = runner.check_environment()
        runner.results["environment"] = env_status
        
        if env_status["missing_dependencies"]:
            runner.log(f"Missing dependencies: {env_status['missing_dependencies']}", "WARNING")
            print("\nTo install missing dependencies:")
            print("pip install pytest pytest-asyncio pytest-timeout")
            print("pip install kailash  # When available")
            print("pip install docker  # For Docker utilities")
        
        # Setup environment if requested
        if args.setup:
            setup_success = runner.setup_test_environment()
            runner.results["setup"] = {"success": setup_success}
            
            if not setup_success:
                runner.log("Environment setup failed, continuing with available services", "WARNING")
        
        # Run compliance validation if requested
        if args.compliance:
            compliance_result = runner.run_compliance_validation()
            runner.results["compliance"] = compliance_result
            
            if compliance_result["status"] == "failed":
                runner.log("Compliance validation failed!", "ERROR")
                for violation in compliance_result["violations_found"]:
                    runner.log(f"  - {violation}", "ERROR")
        
        # Run tests based on tier
        extra_args = []
        if args.parallel:
            extra_args.extend(["-n", "auto"])  # pytest-xdist
        
        if args.tier == "all":
            # Run all tiers sequentially
            for tier in ["unit", "integration", "e2e"]:
                try:
                    result = runner.run_tier_tests(tier, extra_args)
                    runner.results[tier] = result
                except Exception as e:
                    runner.log(f"Error running {tier} tests: {e}", "ERROR")
                    runner.results[tier] = {"status": "error", "error": str(e)}
        else:
            # Run specific tier
            result = runner.run_tier_tests(args.tier, extra_args)
            runner.results[args.tier] = result
        
        # Run performance tests if requested
        if args.performance:
            perf_result = runner.run_performance_tests()
            runner.results["performance"] = perf_result
        
        # Cleanup if requested
        if args.cleanup:
            cleanup_success = runner.cleanup_test_data()
            runner.results["cleanup"] = {"success": cleanup_success}
        
        # Generate and save report
        report = runner.generate_report()
        
        if args.report:
            runner.save_report(report, args.report)
        else:
            # Save with timestamp
            runner.save_report(report)
        
        # Print summary
        print("\n" + "="*60)
        print("TEST EXECUTION SUMMARY")
        print("="*60)
        
        summary = report["execution_summary"]
        print(f"Total execution time: {summary['total_execution_time']:.2f}s")
        print(f"Tests run: {summary['total_tests_run']}")
        print(f"Tests passed: {summary['total_tests_passed']}")
        print(f"Tests failed: {summary['total_tests_failed']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        
        if args.compliance and "compliance" in runner.results:
            comp_result = runner.results["compliance"]
            print(f"Compliance score: {comp_result['compliance_score']}/100")
        
        print("="*60)
        
        # Exit with appropriate code
        if summary["total_tests_failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        runner.log("Test execution interrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        runner.log(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()