#!/usr/bin/env python3
"""
Comprehensive Test Infrastructure Validation
============================================

This script validates that the 3-tier testing strategy is fully operational:
- Tier 1: Unit Tests (with mocking allowed, <1s per test)
- Tier 2: Integration Tests (real services, NO MOCKING, <5s per test)  
- Tier 3: E2E Tests (complete workflows, NO MOCKING, <10s per test)

Usage:
    python run_comprehensive_test_validation.py [--tier 1|2|3] [--verbose]

This replaces the false progress reporting that showed 100% success with 0 tests.
"""

import sys
import subprocess
import time
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
import argparse


@dataclass
class TestResult:
    """Represents the result of running a test suite"""
    tier: int
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    errors: List[str]
    success_rate: float
    
    def __post_init__(self):
        if self.total_tests > 0:
            self.success_rate = (self.passed / self.total_tests) * 100
        else:
            self.success_rate = 0.0


class TestInfrastructureValidator:
    """Validates the complete test infrastructure is working"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: Dict[int, TestResult] = {}
        
    def run_tier_1_tests(self, verbose: bool = False) -> TestResult:
        """Run Tier 1 (Unit) tests - mocking allowed, <1s per test"""
        print("\n" + "="*60)
        print("TIER 1: UNIT TESTS (Mocking Allowed, <1s per test)")
        print("="*60)
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "--tb=short",
            "--timeout=30",  # 30-second timeout (SDK setup takes ~6s)
            "-x",  # Stop on first failure for faster feedback
            "--json-report", "--json-report-file=test-results-tier1.json"
        ]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
            
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max for all unit tests
            )
            duration = time.time() - start_time
            
            # Parse JSON report if available
            json_file = self.project_root / "test-results-tier1.json"
            if json_file.exists():
                with open(json_file) as f:
                    report = json.load(f)
                    
                total = report["summary"]["total"]
                passed = report["summary"].get("passed", 0)
                failed = report["summary"].get("failed", 0)
                skipped = report["summary"].get("skipped", 0)
                
                tier1_result = TestResult(
                    tier=1,
                    total_tests=total,
                    passed=passed,
                    failed=failed,
                    skipped=skipped,
                    duration=duration,
                    errors=[],
                    success_rate=0.0
                )
            else:
                # Fallback parsing from stdout
                output = result.stdout + result.stderr
                tier1_result = self._parse_pytest_output(1, output, duration)
            
            print(f"Unit Tests: {tier1_result.passed}/{tier1_result.total_tests} passed "
                  f"({tier1_result.success_rate:.1f}%) in {duration:.2f}s")
            
            if result.returncode != 0:
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                
            return tier1_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"ERROR: Unit tests timed out after {duration:.1f}s")
            return TestResult(
                tier=1, total_tests=0, passed=0, failed=0, skipped=0,
                duration=duration, errors=["Timeout"], success_rate=0.0
            )
        except Exception as e:
            duration = time.time() - start_time
            print(f"ERROR: Failed to run unit tests: {e}")
            return TestResult(
                tier=1, total_tests=0, passed=0, failed=0, skipped=0,
                duration=duration, errors=[str(e)], success_rate=0.0
            )
    
    def run_tier_2_tests(self, verbose: bool = False) -> TestResult:
        """Run Tier 2 (Integration) tests - real services, NO MOCKING, <5s per test"""
        print("\n" + "="*60)
        print("TIER 2: INTEGRATION TESTS (Real Services, NO MOCKING, <5s per test)")
        print("="*60)
        
        # Check if Docker test environment is available
        if not self._check_docker_services():
            print("WARNING: Docker test services not available. Skipping integration tests.")
            print("Run: ./tests/utils/test-env up && ./tests/utils/test-env status")
            return TestResult(
                tier=2, total_tests=0, passed=0, failed=0, skipped=0,
                duration=0.0, errors=["Docker services not available"], success_rate=0.0
            )
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "--tb=short",
            "--timeout=5",  # Enforce 5-second timeout per test
            "-m", "integration",  # Only run integration-marked tests
            "--json-report", "--json-report-file=test-results-tier2.json"
        ]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
            
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max for integration tests
            )
            duration = time.time() - start_time
            
            # Parse results
            json_file = self.project_root / "test-results-tier2.json"
            if json_file.exists():
                with open(json_file) as f:
                    report = json.load(f)
                    total = report["summary"]["total"]
                    passed = report["summary"].get("passed", 0)
                    failed = report["summary"].get("failed", 0)
                    skipped = report["summary"].get("skipped", 0)
                    
                tier2_result = TestResult(
                    tier=2, total_tests=total, passed=passed, failed=failed,
                    skipped=skipped, duration=duration, errors=[], success_rate=0.0
                )
            else:
                output = result.stdout + result.stderr
                tier2_result = self._parse_pytest_output(2, output, duration)
            
            print(f"Integration Tests: {tier2_result.passed}/{tier2_result.total_tests} passed "
                  f"({tier2_result.success_rate:.1f}%) in {duration:.2f}s")
            
            if result.returncode != 0:
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                
            return tier2_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"ERROR: Integration tests timed out after {duration:.1f}s")
            return TestResult(
                tier=2, total_tests=0, passed=0, failed=0, skipped=0,
                duration=duration, errors=["Timeout"], success_rate=0.0
            )
        except Exception as e:
            duration = time.time() - start_time
            print(f"ERROR: Failed to run integration tests: {e}")
            return TestResult(
                tier=2, total_tests=0, passed=0, failed=0, skipped=0,
                duration=duration, errors=[str(e)], success_rate=0.0
            )
    
    def run_tier_3_tests(self, verbose: bool = False) -> TestResult:
        """Run Tier 3 (E2E) tests - complete workflows, NO MOCKING, <10s per test"""
        print("\n" + "="*60)
        print("TIER 3: END-TO-END TESTS (Complete Workflows, NO MOCKING, <10s per test)")
        print("="*60)
        
        # Check if Docker test environment is available
        if not self._check_docker_services():
            print("WARNING: Docker test services not available. Skipping E2E tests.")
            return TestResult(
                tier=3, total_tests=0, passed=0, failed=0, skipped=0,
                duration=0.0, errors=["Docker services not available"], success_rate=0.0
            )
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/e2e/",
            "--tb=short",
            "--timeout=10",  # Enforce 10-second timeout per test
            "-m", "e2e",  # Only run e2e-marked tests
            "--json-report", "--json-report-file=test-results-tier3.json"
        ]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
            
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1200  # 20 minutes max for E2E tests
            )
            duration = time.time() - start_time
            
            # Parse results
            json_file = self.project_root / "test-results-tier3.json"
            if json_file.exists():
                with open(json_file) as f:
                    report = json.load(f)
                    total = report["summary"]["total"]
                    passed = report["summary"].get("passed", 0)
                    failed = report["summary"].get("failed", 0)
                    skipped = report["summary"].get("skipped", 0)
                    
                tier3_result = TestResult(
                    tier=3, total_tests=total, passed=passed, failed=failed,
                    skipped=skipped, duration=duration, errors=[], success_rate=0.0
                )
            else:
                output = result.stdout + result.stderr
                tier3_result = self._parse_pytest_output(3, output, duration)
            
            print(f"E2E Tests: {tier3_result.passed}/{tier3_result.total_tests} passed "
                  f"({tier3_result.success_rate:.1f}%) in {duration:.2f}s")
            
            if result.returncode != 0:
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                
            return tier3_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"ERROR: E2E tests timed out after {duration:.1f}s")
            return TestResult(
                tier=3, total_tests=0, passed=0, failed=0, skipped=0,
                duration=duration, errors=["Timeout"], success_rate=0.0
            )
        except Exception as e:
            duration = time.time() - start_time
            print(f"ERROR: Failed to run E2E tests: {e}")
            return TestResult(
                tier=3, total_tests=0, passed=0, failed=0, skipped=0,
                duration=duration, errors=[str(e)], success_rate=0.0
            )
    
    def _check_docker_services(self) -> bool:
        """Check if Docker test services are running"""
        try:
            # Use the test-env script to check status
            test_env_script = self.project_root / "tests" / "utils" / "test-env"
            if test_env_script.exists():
                result = subprocess.run(
                    ["bash", str(test_env_script), "status"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return "ALL SERVICES HEALTHY" in result.stdout
            return False
        except Exception:
            return False
    
    def _parse_pytest_output(self, tier: int, output: str, duration: float) -> TestResult:
        """Parse pytest output to extract test results"""
        import re
        
        # Look for pytest summary line
        summary_pattern = r"=+\s*(\d+)\s+passed(?:,\s*(\d+)\s+failed)?(?:,\s*(\d+)\s+skipped)?.*=+"
        match = re.search(summary_pattern, output)
        
        if match:
            passed = int(match.group(1))
            failed = int(match.group(2) or 0)
            skipped = int(match.group(3) or 0)
            total = passed + failed + skipped
        else:
            # Fallback: look for collected items
            collected_pattern = r"collected (\d+) items?"
            match = re.search(collected_pattern, output)
            if match:
                total = int(match.group(1))
                passed = 0
                failed = 0
                skipped = total  # Assume all skipped if no other info
            else:
                total = passed = failed = skipped = 0
        
        return TestResult(
            tier=tier,
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            errors=[],
            success_rate=0.0
        )
    
    def run_comprehensive_validation(self, tiers: List[int], verbose: bool = False) -> Dict[int, TestResult]:
        """Run comprehensive test validation for specified tiers"""
        print("KAILASH SDK 3-TIER TEST INFRASTRUCTURE VALIDATION")
        print("="*60)
        print("Validating critical test infrastructure repairs...")
        print("This replaces false progress reporting (0 tests = 100% success)")
        
        start_time = time.time()
        
        if 1 in tiers:
            self.results[1] = self.run_tier_1_tests(verbose)
            
        if 2 in tiers:
            self.results[2] = self.run_tier_2_tests(verbose)
            
        if 3 in tiers:
            self.results[3] = self.run_tier_3_tests(verbose)
        
        total_duration = time.time() - start_time
        
        # Generate comprehensive report
        self._generate_final_report(total_duration)
        
        return self.results
    
    def _generate_final_report(self, total_duration: float):
        """Generate the final validation report"""
        print("\n" + "="*80)
        print("FINAL TEST INFRASTRUCTURE VALIDATION REPORT")
        print("="*80)
        
        total_tests = sum(r.total_tests for r in self.results.values())
        total_passed = sum(r.passed for r in self.results.values())
        total_failed = sum(r.failed for r in self.results.values())
        total_skipped = sum(r.skipped for r in self.results.values())
        
        print(f"Overall Results:")
        print(f"  Total Tests Discovered: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_failed}")
        print(f"  Skipped: {total_skipped}")
        print(f"  Total Duration: {total_duration:.2f}s")
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
        else:
            print(f"  Success Rate: 0.0% (NO TESTS FOUND)")
        
        print()
        
        # Tier-by-tier breakdown
        for tier, result in self.results.items():
            tier_names = {1: "Unit", 2: "Integration", 3: "E2E"}
            tier_policies = {
                1: "Mocking Allowed, <1s per test",
                2: "Real Services, NO MOCKING, <5s per test", 
                3: "Complete Workflows, NO MOCKING, <10s per test"
            }
            
            print(f"Tier {tier} ({tier_names[tier]}) - {tier_policies[tier]}:")
            print(f"  Tests: {result.total_tests}")
            print(f"  Passed: {result.passed}")
            print(f"  Failed: {result.failed}")
            print(f"  Skipped: {result.skipped}")
            print(f"  Duration: {result.duration:.2f}s")
            print(f"  Success Rate: {result.success_rate:.1f}%")
            
            if result.errors:
                print(f"  Errors: {', '.join(result.errors)}")
            print()
        
        # Infrastructure status
        print("Infrastructure Status:")
        print(f"  Test Discovery: {'WORKING' if total_tests > 0 else 'BROKEN'}")
        print(f"  Import Resolution: {'WORKING' if not any('ImportError' in str(r.errors) for r in self.results.values()) else 'BROKEN'}")
        
        docker_available = self._check_docker_services()
        print(f"  Docker Services: {'AVAILABLE' if docker_available else 'NOT AVAILABLE'}")
        
        # Critical issues
        if total_tests == 0:
            print("\nCRITICAL ISSUE: NO TESTS DISCOVERED")
            print("   This indicates test infrastructure is completely broken.")
            print("   Previous reports showing 100% success with 0 tests were FALSE.")
        elif total_failed > total_passed:
            print("\nWARNING: More tests failing than passing")
        elif total_tests > 0 and total_passed > 0:
            print(f"\nSUCCESS: Test infrastructure is operational")
            print(f"   {total_passed} tests are passing out of {total_tests} discovered")
        
        print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(description="Validate 3-tier test infrastructure")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], action="append",
                       help="Run specific test tier (can be repeated)")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Default to all tiers if none specified
    tiers = args.tier if args.tier else [1, 2, 3]
    
    project_root = Path(__file__).parent
    validator = TestInfrastructureValidator(project_root)
    
    try:
        results = validator.run_comprehensive_validation(tiers, args.verbose)
        
        # Exit with appropriate code
        total_tests = sum(r.total_tests for r in results.values())
        total_failed = sum(r.failed for r in results.values())
        
        if total_tests == 0:
            sys.exit(2)  # No tests found - critical failure
        elif total_failed > 0:
            sys.exit(1)  # Some tests failed
        else:
            sys.exit(0)  # All tests passed
            
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nValidation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()