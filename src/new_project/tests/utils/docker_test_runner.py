"""
Docker Testing Automation Runner

Coordinates comprehensive Docker testing across all tiers:
- Tier 1: Unit tests (Docker validation, security)
- Tier 2: Integration tests (service communication)
- Tier 3: E2E tests (complete workflows, production readiness)
- Performance tests (startup, resource usage, network)
- Chaos tests (failure scenarios, recovery)

Usage:
    python tests/utils/docker_test_runner.py --tier all
    python tests/utils/docker_test_runner.py --tier unit
    python tests/utils/docker_test_runner.py --performance
    python tests/utils/docker_test_runner.py --chaos
    python tests/utils/docker_test_runner.py --production-readiness
"""

import argparse
import subprocess
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DockerTestRunner:
    """Coordinates Docker testing execution."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_tier_1_tests(self) -> Dict[str, Any]:
        """Run Tier 1 Unit Tests for Docker components."""
        logger.info("Running Tier 1 Unit Tests: Docker Validation")
        
        test_files = [
            "tests/unit/test_docker_validation.py"
        ]
        
        results = self._run_pytest_tests(
            test_files,
            "tier1_docker_unit",
            timeout_per_test=1,
            markers="not integration and not e2e"
        )
        
        return results
    
    def run_tier_2_tests(self) -> Dict[str, Any]:
        """Run Tier 2 Integration Tests with real Docker services."""
        logger.info("Running Tier 2 Integration Tests: Docker Services")
        
        # Ensure Docker test infrastructure is running
        if not self._ensure_docker_infrastructure():
            logger.error("Failed to start Docker test infrastructure")
            return {"status": "failed", "error": "Infrastructure setup failed"}
        
        test_files = [
            "tests/integration/test_docker_services_integration.py"
        ]
        
        results = self._run_pytest_tests(
            test_files,
            "tier2_docker_integration",
            timeout_per_test=5,
            markers="integration"
        )
        
        return results
    
    def run_tier_3_tests(self) -> Dict[str, Any]:
        """Run Tier 3 E2E Tests for complete Docker workflows."""
        logger.info("Running Tier 3 E2E Tests: Complete Docker Workflows")
        
        # Ensure full Docker stack is running
        if not self._ensure_full_docker_stack():
            logger.error("Failed to start full Docker stack")
            return {"status": "failed", "error": "Full stack setup failed"}
        
        test_files = [
            "tests/e2e/test_docker_complete_workflows_e2e.py",
            "tests/e2e/test_docker_production_readiness_e2e.py"
        ]
        
        results = self._run_pytest_tests(
            test_files,
            "tier3_docker_e2e",
            timeout_per_test=10,
            markers="e2e"
        )
        
        return results
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run Docker performance tests."""
        logger.info("Running Docker Performance Tests")
        
        # Ensure Docker services are running
        if not self._ensure_docker_infrastructure():
            logger.error("Failed to start Docker infrastructure for performance tests")
            return {"status": "failed", "error": "Infrastructure setup failed"}
        
        test_files = [
            "tests/performance/test_docker_performance.py"
        ]
        
        results = self._run_pytest_tests(
            test_files,
            "docker_performance",
            timeout_per_test=30,
            additional_args=["--durations=10"]
        )
        
        return results
    
    def run_chaos_tests(self) -> Dict[str, Any]:
        """Run Docker chaos tests."""
        logger.info("Running Docker Chaos Tests")
        logger.warning("Chaos tests will intentionally break services - ensure this is a test environment!")
        
        # Ensure Docker services are running
        if not self._ensure_docker_infrastructure():
            logger.error("Failed to start Docker infrastructure for chaos tests")
            return {"status": "failed", "error": "Infrastructure setup failed"}
        
        test_files = [
            "tests/performance/test_docker_chaos.py"
        ]
        
        results = self._run_pytest_tests(
            test_files,
            "docker_chaos",
            timeout_per_test=60,
            markers="chaos",
            additional_args=["--tb=short"]
        )
        
        return results
    
    def run_production_readiness_tests(self) -> Dict[str, Any]:
        """Run production readiness validation tests."""
        logger.info("Running Docker Production Readiness Tests")
        
        # Ensure full Docker stack is running
        if not self._ensure_full_docker_stack():
            logger.error("Failed to start full Docker stack")
            return {"status": "failed", "error": "Full stack setup failed"}
        
        test_files = [
            "tests/e2e/test_docker_production_readiness_e2e.py"
        ]
        
        results = self._run_pytest_tests(
            test_files,
            "docker_production_readiness",
            timeout_per_test=30,
            additional_args=["--durations=10"]
        )
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Docker tests in sequence."""
        logger.info("Running Complete Docker Test Suite")
        self.start_time = datetime.now()
        
        all_results = {}
        
        # Run tests in order of increasing complexity
        test_suites = [
            ("tier1", self.run_tier_1_tests),
            ("tier2", self.run_tier_2_tests), 
            ("tier3", self.run_tier_3_tests),
            ("performance", self.run_performance_tests),
            ("production_readiness", self.run_production_readiness_tests)
        ]
        
        for suite_name, test_function in test_suites:
            logger.info(f"Starting {suite_name} tests...")
            try:
                results = test_function()
                all_results[suite_name] = results
                
                if results.get("status") == "failed":
                    logger.error(f"{suite_name} tests failed")
                    if results.get("exit_code", 0) > 0:
                        logger.warning(f"Continuing with remaining test suites despite {suite_name} failures")
                else:
                    logger.info(f"{suite_name} tests completed successfully")
                    
            except Exception as e:
                logger.error(f"Exception in {suite_name} tests: {e}")
                all_results[suite_name] = {"status": "error", "error": str(e)}
        
        self.end_time = datetime.now()
        
        # Generate summary report
        summary = self._generate_summary_report(all_results)
        all_results["summary"] = summary
        
        return all_results
    
    def _run_pytest_tests(
        self,
        test_files: List[str],
        test_suite_name: str,
        timeout_per_test: int = 10,
        markers: Optional[str] = None,
        additional_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run pytest tests with specified configuration."""
        
        cmd = ["python", "-m", "pytest"]
        
        # Add test files
        for test_file in test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                cmd.append(str(test_path))
            else:
                logger.warning(f"Test file not found: {test_path}")
        
        # Add timeout
        cmd.extend(["--timeout", str(timeout_per_test)])
        
        # Add markers
        if markers:
            cmd.extend(["-m", markers])
        
        # Add verbose output
        cmd.append("-v")
        
        # Add additional arguments
        if additional_args:
            cmd.extend(additional_args)
        
        # Add JSON report output
        report_file = self.project_root / f"test_report_{test_suite_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        cmd.extend(["--json-report", f"--json-report-file={report_file}"])
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=len(test_files) * timeout_per_test * 10  # Overall timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            test_results = {
                "status": "passed" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "report_file": str(report_file) if report_file.exists() else None
            }
            
            # Try to parse JSON report if available
            if report_file.exists():
                try:
                    with open(report_file, 'r') as f:
                        json_report = json.load(f)
                        test_results["json_report"] = json_report
                except Exception as e:
                    logger.warning(f"Could not parse JSON report: {e}")
            
            # Log results
            if result.returncode == 0:
                logger.info(f"{test_suite_name} tests passed in {duration:.2f}s")
            else:
                logger.error(f"{test_suite_name} tests failed with exit code {result.returncode}")
                if result.stderr:
                    logger.error(f"STDERR: {result.stderr}")
            
            return test_results
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"{test_suite_name} tests timed out after {e.timeout}s")
            return {
                "status": "timeout",
                "error": f"Tests timed out after {e.timeout}s",
                "duration": e.timeout
            }
        except Exception as e:
            logger.error(f"Error running {test_suite_name} tests: {e}")
            return {
                "status": "error",
                "error": str(e),
                "duration": 0
            }
    
    def _ensure_docker_infrastructure(self) -> bool:
        """Ensure Docker test infrastructure is running."""
        logger.info("Ensuring Docker test infrastructure is running...")
        
        test_env_script = self.project_root / "tests" / "utils" / "test-env"
        
        if not test_env_script.exists():
            logger.warning("test-env script not found, assuming Docker services are manually managed")
            return True
        
        try:
            # Check status first
            result = subprocess.run(
                [str(test_env_script), "status"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and "ALL SERVICES HEALTHY" in result.stdout:
                logger.info("Docker test infrastructure already running")
                return True
            
            # Start services
            logger.info("Starting Docker test infrastructure...")
            result = subprocess.run(
                [str(test_env_script), "up"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                logger.info("Docker test infrastructure started successfully")
                return True
            else:
                logger.error(f"Failed to start Docker test infrastructure: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout starting Docker test infrastructure")
            return False
        except Exception as e:
            logger.error(f"Error starting Docker test infrastructure: {e}")
            return False
    
    def _ensure_full_docker_stack(self) -> bool:
        """Ensure full Docker stack is running for E2E tests."""
        logger.info("Ensuring full Docker stack is running...")
        
        compose_file = self.project_root / "docker-compose.yml"
        
        if not compose_file.exists():
            logger.warning("docker-compose.yml not found, assuming services are manually managed")
            return True
        
        try:
            # Check running services
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "ps", "--services", "--filter", "status=running"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            running_services = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            if len(running_services) >= 3:  # At least postgres, redis, and one app service
                logger.info(f"Full Docker stack running with {len(running_services)} services")
                return True
            
            # Start full stack
            logger.info("Starting full Docker stack...")
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "up", "-d"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )
            
            if result.returncode == 0:
                logger.info("Full Docker stack started successfully")
                # Give services time to be ready
                time.sleep(30)
                return True
            else:
                logger.error(f"Failed to start full Docker stack: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout starting full Docker stack")
            return False
        except Exception as e:
            logger.error(f"Error starting full Docker stack: {e}")
            return False
    
    def _generate_summary_report(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary report of all test results."""
        
        summary = {
            "total_duration": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "test_suites": {},
            "overall_status": "passed"
        }
        
        for suite_name, results in all_results.items():
            if suite_name == "summary":
                continue
                
            suite_summary = {
                "status": results.get("status", "unknown"),
                "duration": results.get("duration", 0),
                "exit_code": results.get("exit_code")
            }
            
            # Extract test counts from JSON report if available
            if "json_report" in results:
                json_report = results["json_report"]
                suite_summary.update({
                    "total_tests": json_report.get("summary", {}).get("total", 0),
                    "passed_tests": json_report.get("summary", {}).get("passed", 0),
                    "failed_tests": json_report.get("summary", {}).get("failed", 0),
                    "skipped_tests": json_report.get("summary", {}).get("skipped", 0)
                })
            
            summary["test_suites"][suite_name] = suite_summary
            
            # Update overall status
            if results.get("status") not in ["passed", "skipped"]:
                summary["overall_status"] = "failed"
        
        # Calculate totals
        total_tests = sum(suite.get("total_tests", 0) for suite in summary["test_suites"].values())
        passed_tests = sum(suite.get("passed_tests", 0) for suite in summary["test_suites"].values())
        failed_tests = sum(suite.get("failed_tests", 0) for suite in summary["test_suites"].values())
        skipped_tests = sum(suite.get("skipped_tests", 0) for suite in summary["test_suites"].values())
        
        summary["totals"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        return summary
    
    def save_results(self, results: Dict[str, Any], output_file: Optional[Path] = None) -> Path:
        """Save test results to file."""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.project_root / f"docker_test_results_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Test results saved to: {output_file}")
        return output_file


def main():
    """Main entry point for Docker test runner."""
    parser = argparse.ArgumentParser(description="Docker Testing Automation Runner")
    
    parser.add_argument(
        "--tier",
        choices=["1", "2", "3", "all"],
        help="Run specific tier tests (1=unit, 2=integration, 3=e2e, all=all tiers)"
    )
    
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests"
    )
    
    parser.add_argument(
        "--chaos",
        action="store_true", 
        help="Run chaos tests (WARNING: will break services)"
    )
    
    parser.add_argument(
        "--production-readiness",
        action="store_true",
        help="Run production readiness tests"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for results (default: auto-generated)"
    )
    
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Project root directory (default: auto-detected)"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = DockerTestRunner(project_root=args.project_root)
    
    # Determine what to run
    results = {}
    
    if args.tier == "1":
        results = runner.run_tier_1_tests()
    elif args.tier == "2":
        results = runner.run_tier_2_tests() 
    elif args.tier == "3":
        results = runner.run_tier_3_tests()
    elif args.tier == "all":
        results = runner.run_all_tests()
    elif args.performance:
        results = runner.run_performance_tests()
    elif args.chaos:
        results = runner.run_chaos_tests()
    elif args.production_readiness:
        results = runner.run_production_readiness_tests()
    else:
        # Default: run all tests
        results = runner.run_all_tests()
    
    # Save results
    output_file = runner.save_results(results, args.output)
    
    # Print summary
    if "summary" in results:
        summary = results["summary"]
        print(f"\n{'='*60}")
        print("DOCKER TEST RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        
        if "totals" in summary:
            totals = summary["totals"]
            print(f"Total Tests: {totals['total_tests']}")
            print(f"Passed: {totals['passed_tests']}")
            print(f"Failed: {totals['failed_tests']}")
            print(f"Skipped: {totals['skipped_tests']}")
            print(f"Pass Rate: {totals['pass_rate']:.1f}%")
        
        print(f"\nDetailed results saved to: {output_file}")
        print(f"{'='*60}")
    
    # Exit with appropriate code
    if results.get("summary", {}).get("overall_status") == "passed":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()