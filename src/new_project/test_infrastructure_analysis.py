#!/usr/bin/env python3
"""
Test Infrastructure Analysis and Success Rate Measurement
=========================================================

Comprehensive analysis of the 3-tier testing strategy implementation
and measurement of actual test success rates toward the 95% target.

This script implements the Kailash SDK testing strategy:
- Tier 1: Unit Tests (mocking allowed, <1s per test)
- Tier 2: Integration Tests (NO MOCKING, real services, <5s per test) 
- Tier 3: E2E Tests (NO MOCKING, complete workflows, <10s per test)
"""

import subprocess
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test execution result with detailed metrics."""
    tier: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    success_rate: float
    avg_test_time: float
    slowest_tests: List[Tuple[str, float]]

@dataclass
class InfrastructureStatus:
    """Infrastructure availability assessment."""
    docker_available: bool
    postgresql_available: bool
    redis_available: bool
    neo4j_available: bool
    services_ready: bool
    mock_fallback_needed: bool

class TestInfrastructureAnalyzer:
    """Analyzes and measures test infrastructure capabilities."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.test_path = project_path / "tests"
        self.results = {}
        self.infrastructure_status = None
        
    def assess_infrastructure(self) -> InfrastructureStatus:
        """Assess current infrastructure availability."""
        logger.info("Assessing infrastructure availability...")
        
        # Check Docker availability
        docker_available = self._check_docker()
        
        # Check if test-env scripts exist
        test_env_script = self.test_path / "utils" / "test-env.bat"
        test_env_available = test_env_script.exists()
        
        # For Windows without Docker, we'll use mock fallback for integration tests
        services_ready = docker_available and test_env_available
        
        status = InfrastructureStatus(
            docker_available=docker_available,
            postgresql_available=services_ready,
            redis_available=services_ready,
            neo4j_available=services_ready,
            services_ready=services_ready,
            mock_fallback_needed=not services_ready
        )
        
        self.infrastructure_status = status
        logger.info(f"Infrastructure Status: {status}")
        return status
    
    def _check_docker(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def run_tier_tests(self, tier: str, timeout_per_test: float = None) -> TestResult:
        """Run tests for a specific tier and measure results."""
        logger.info(f"Running Tier {tier} tests...")
        
        tier_map = {
            "1": "unit",
            "2": "integration", 
            "3": "e2e"
        }
        
        test_dir = self.test_path / tier_map[tier]
        if not test_dir.exists():
            logger.warning(f"Test directory {test_dir} does not exist")
            return TestResult(tier, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, [])
        
        # Prepare pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_dir),
            "--tb=short",
            "-v",
            "--durations=10",
            f"--timeout={timeout_per_test or self._get_tier_timeout(tier)}",
            "--json-report",
            f"--json-report-file=test_report_tier_{tier}.json"
        ]
        
        # Add tier-specific markers
        if tier == "1":
            cmd.extend(["-m", "unit or not (integration or e2e)"])
        elif tier == "2":
            cmd.extend(["-m", "integration"])
        elif tier == "3":
            cmd.extend(["-m", "e2e"])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute total timeout
            )
            
            duration = time.time() - start_time
            
            # Parse JSON report if available
            report_file = self.project_path / f"test_report_tier_{tier}.json"
            if report_file.exists():
                return self._parse_json_report(report_file, tier, duration)
            else:
                # Fallback to stdout parsing
                return self._parse_stdout_results(result.stdout, tier, duration)
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"Tier {tier} tests timed out after {duration:.2f}s")
            return TestResult(tier, 0, 0, 0, 0, 1, duration, 0.0, 0.0, [])
    
    def _get_tier_timeout(self, tier: str) -> int:
        """Get timeout per test for each tier."""
        timeouts = {"1": 1, "2": 5, "3": 10}
        return timeouts.get(tier, 5)
    
    def _parse_json_report(self, report_file: Path, tier: str, duration: float) -> TestResult:
        """Parse pytest JSON report."""
        try:
            with open(report_file, 'r') as f:
                data = json.load(f)
            
            summary = data.get('summary', {})
            total = summary.get('total', 0)
            passed = summary.get('passed', 0)
            failed = summary.get('failed', 0)
            skipped = summary.get('skipped', 0)
            errors = summary.get('error', 0)
            
            success_rate = (passed / total * 100) if total > 0 else 0
            avg_test_time = duration / total if total > 0 else 0
            
            # Extract slowest tests
            slowest_tests = []
            tests = data.get('tests', [])
            for test in sorted(tests, key=lambda t: t.get('duration', 0), reverse=True)[:5]:
                test_name = test.get('nodeid', 'unknown')
                test_duration = test.get('duration', 0)
                slowest_tests.append((test_name, test_duration))
            
            return TestResult(
                tier=tier,
                total_tests=total,
                passed=passed,
                failed=failed,
                skipped=skipped,
                errors=errors,
                duration=duration,
                success_rate=success_rate,
                avg_test_time=avg_test_time,
                slowest_tests=slowest_tests
            )
            
        except Exception as e:
            logger.error(f"Failed to parse JSON report: {e}")
            return TestResult(tier, 0, 0, 0, 0, 1, duration, 0.0, 0.0, [])
    
    def _parse_stdout_results(self, stdout: str, tier: str, duration: float) -> TestResult:
        """Parse pytest stdout output as fallback."""
        lines = stdout.split('\n')
        
        # Look for summary line like "=== 5 failed, 10 passed in 2.34s ==="
        summary_line = None
        for line in reversed(lines):
            if 'passed' in line or 'failed' in line:
                summary_line = line
                break
        
        if not summary_line:
            return TestResult(tier, 0, 0, 0, 0, 1, duration, 0.0, 0.0, [])
        
        # Parse summary
        total, passed, failed, skipped, errors = 0, 0, 0, 0, 0
        
        if 'passed' in summary_line:
            passed = int(summary_line.split('passed')[0].split()[-1])
        if 'failed' in summary_line:
            failed = int(summary_line.split('failed')[0].split()[-1])
        if 'skipped' in summary_line:
            skipped = int(summary_line.split('skipped')[0].split()[-1])
        if 'error' in summary_line:
            errors = int(summary_line.split('error')[0].split()[-1])
        
        total = passed + failed + skipped + errors
        success_rate = (passed / total * 100) if total > 0 else 0
        avg_test_time = duration / total if total > 0 else 0
        
        return TestResult(
            tier=tier,
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            success_rate=success_rate,
            avg_test_time=avg_test_time,
            slowest_tests=[]
        )
    
    def analyze_all_tiers(self) -> Dict[str, TestResult]:
        """Run comprehensive analysis of all test tiers."""
        logger.info("Starting comprehensive test infrastructure analysis...")
        
        # Assess infrastructure first
        self.assess_infrastructure()
        
        results = {}
        
        # Run each tier
        for tier in ["1", "2", "3"]:
            try:
                result = self.run_tier_tests(tier)
                results[f"tier_{tier}"] = result
                logger.info(f"Tier {tier}: {result.success_rate:.1f}% success rate")
            except Exception as e:
                logger.error(f"Failed to run Tier {tier} tests: {e}")
                results[f"tier_{tier}"] = TestResult(tier, 0, 0, 0, 0, 1, 0.0, 0.0, 0.0, [])
        
        self.results = results
        return results
    
    def calculate_overall_metrics(self) -> Dict:
        """Calculate overall testing metrics."""
        if not self.results:
            return {}
        
        total_tests = sum(r.total_tests for r in self.results.values())
        total_passed = sum(r.passed for r in self.results.values())
        total_failed = sum(r.failed for r in self.results.values())
        total_duration = sum(r.duration for r in self.results.values())
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Performance compliance check
        tier_1_avg = self.results.get("tier_1", TestResult("1", 0, 0, 0, 0, 0, 0, 0, 0, [])).avg_test_time
        tier_2_avg = self.results.get("tier_2", TestResult("2", 0, 0, 0, 0, 0, 0, 0, 0, [])).avg_test_time
        tier_3_avg = self.results.get("tier_3", TestResult("3", 0, 0, 0, 0, 0, 0, 0, 0, [])).avg_test_time
        
        performance_compliance = {
            "tier_1_under_1s": tier_1_avg < 1.0,
            "tier_2_under_5s": tier_2_avg < 5.0,
            "tier_3_under_10s": tier_3_avg < 10.0
        }
        
        return {
            "overall_success_rate": overall_success_rate,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_duration": total_duration,
            "performance_compliance": performance_compliance,
            "target_95_percent_gap": 95.0 - overall_success_rate,
            "infrastructure_status": self.infrastructure_status.__dict__ if self.infrastructure_status else {}
        }
    
    def generate_report(self) -> str:
        """Generate comprehensive test infrastructure report."""
        if not self.results:
            self.analyze_all_tiers()
        
        metrics = self.calculate_overall_metrics()
        
        report = f"""
TEST INFRASTRUCTURE ANALYSIS REPORT
===================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERALL METRICS
--------------
Overall Success Rate: {metrics.get('overall_success_rate', 0):.1f}%
Target Success Rate: 95.0%
Gap to Target: {metrics.get('target_95_percent_gap', 0):.1f}%

Total Tests: {metrics.get('total_tests', 0)}
Passed: {metrics.get('total_passed', 0)}
Failed: {metrics.get('total_failed', 0)}
Total Duration: {metrics.get('total_duration', 0):.2f}s

INFRASTRUCTURE STATUS
--------------------"""
        
        if self.infrastructure_status:
            report += f"""
Docker Available: {self.infrastructure_status.docker_available}
Services Ready: {self.infrastructure_status.services_ready}
Mock Fallback Needed: {self.infrastructure_status.mock_fallback_needed}
"""
        
        report += "\nTIER-BY-TIER ANALYSIS\n" + "="*20 + "\n"
        
        for tier_name, result in self.results.items():
            tier_num = tier_name.split('_')[1]
            tier_timeout = self._get_tier_timeout(tier_num)
            
            report += f"""
Tier {tier_num} ({'Unit' if tier_num == '1' else 'Integration' if tier_num == '2' else 'E2E'}):
  Tests: {result.total_tests}
  Passed: {result.passed}
  Failed: {result.failed}
  Success Rate: {result.success_rate:.1f}%
  Duration: {result.duration:.2f}s
  Avg Test Time: {result.avg_test_time:.3f}s
  Target: <{tier_timeout}s per test
  Performance: {'PASS' if result.avg_test_time < tier_timeout else 'FAIL'}

"""
            
            if result.slowest_tests:
                report += "  Slowest Tests:\n"
                for test_name, duration in result.slowest_tests[:3]:
                    report += f"    {duration:.3f}s: {test_name}\n"
                report += "\n"
        
        # Performance compliance
        perf = metrics.get('performance_compliance', {})
        report += f"""
PERFORMANCE COMPLIANCE
---------------------
Tier 1 (<1s): {'PASS' if perf.get('tier_1_under_1s') else 'FAIL'}
Tier 2 (<5s): {'PASS' if perf.get('tier_2_under_5s') else 'FAIL'}  
Tier 3 (<10s): {'PASS' if perf.get('tier_3_under_10s') else 'FAIL'}

RECOMMENDATIONS
--------------"""
        
        # Generate recommendations
        overall_rate = metrics.get('overall_success_rate', 0)
        if overall_rate < 95:
            report += f"""
Priority Actions to Reach 95% Success Rate:
1. Fix {metrics.get('total_failed', 0)} failing tests
2. Address infrastructure dependencies
3. Implement proper test isolation
"""
        
        if not self.infrastructure_status or not self.infrastructure_status.services_ready:
            report += """
4. Set up Docker test infrastructure for Integration/E2E tests
5. Configure test-env scripts for service management
6. Implement realistic mock fallbacks for Windows development
"""
        
        for tier_name, result in self.results.items():
            tier_num = tier_name.split('_')[1]
            tier_timeout = self._get_tier_timeout(tier_num)
            if result.avg_test_time >= tier_timeout:
                report += f"7. Optimize Tier {tier_num} tests - average {result.avg_test_time:.3f}s exceeds {tier_timeout}s target\n"
        
        return report

def main():
    """Main execution function."""
    project_path = Path(__file__).parent
    analyzer = TestInfrastructureAnalyzer(project_path)
    
    print("Analyzing Test Infrastructure...")
    print("=" * 50)
    
    # Run comprehensive analysis
    results = analyzer.analyze_all_tiers()
    
    # Generate and display report
    report = analyzer.generate_report()
    print(report)
    
    # Save report to file
    report_file = project_path / f"test_infrastructure_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\nFull report saved to: {report_file}")
    
    # Return exit code based on success rate
    overall_rate = analyzer.calculate_overall_metrics().get('overall_success_rate', 0)
    if overall_rate >= 95:
        print("\nSUCCESS: 95% target achieved!")
        return 0
    else:
        print(f"\nIN PROGRESS: {overall_rate:.1f}% success rate, {95-overall_rate:.1f}% gap to target")
        return 1

if __name__ == "__main__":
    sys.exit(main())