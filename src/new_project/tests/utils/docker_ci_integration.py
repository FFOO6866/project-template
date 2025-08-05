"""
Docker CI/CD Integration Script

Provides CI/CD integration for Docker testing pipeline:
- GitHub Actions integration
- Jenkins pipeline support
- GitLab CI integration
- Test result reporting
- Failure notifications
- Performance regression detection

Usage in CI/CD:
    python tests/utils/docker_ci_integration.py --ci-mode github-actions
    python tests/utils/docker_ci_integration.py --ci-mode jenkins
    python tests/utils/docker_ci_integration.py --ci-mode gitlab-ci
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DockerCIIntegration:
    """Docker CI/CD integration coordinator."""
    
    def __init__(self, ci_mode: str = "generic", project_root: Optional[Path] = None):
        self.ci_mode = ci_mode
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.ci_config = self._detect_ci_environment()
        
    def _detect_ci_environment(self) -> Dict[str, Any]:
        """Detect CI environment and configuration."""
        config = {
            "is_ci": False,
            "provider": "unknown",
            "branch": None,
            "commit": None,
            "pr_number": None,
            "build_number": None
        }
        
        # GitHub Actions
        if os.getenv("GITHUB_ACTIONS"):
            config.update({
                "is_ci": True,
                "provider": "github-actions",
                "branch": os.getenv("GITHUB_REF_NAME"),
                "commit": os.getenv("GITHUB_SHA"),
                "pr_number": os.getenv("GITHUB_EVENT_NUMBER"),
                "build_number": os.getenv("GITHUB_RUN_NUMBER"),
                "actor": os.getenv("GITHUB_ACTOR"),
                "repo": os.getenv("GITHUB_REPOSITORY")
            })
        
        # Jenkins
        elif os.getenv("JENKINS_URL"):
            config.update({
                "is_ci": True,
                "provider": "jenkins",
                "branch": os.getenv("GIT_BRANCH"),
                "commit": os.getenv("GIT_COMMIT"),
                "build_number": os.getenv("BUILD_NUMBER"),
                "job_name": os.getenv("JOB_NAME"),
                "build_url": os.getenv("BUILD_URL")
            })
        
        # GitLab CI
        elif os.getenv("GITLAB_CI"):
            config.update({
                "is_ci": True,
                "provider": "gitlab-ci",
                "branch": os.getenv("CI_COMMIT_REF_NAME"),
                "commit": os.getenv("CI_COMMIT_SHA"),
                "pr_number": os.getenv("CI_MERGE_REQUEST_IID"),
                "build_number": os.getenv("CI_PIPELINE_ID"),
                "project": os.getenv("CI_PROJECT_PATH"),
                "pipeline_url": os.getenv("CI_PIPELINE_URL")
            })
        
        # Azure DevOps
        elif os.getenv("AZURE_HTTP_USER_AGENT"):
            config.update({
                "is_ci": True,
                "provider": "azure-devops",
                "branch": os.getenv("BUILD_SOURCEBRANCH"),
                "commit": os.getenv("BUILD_SOURCEVERSION"),
                "build_number": os.getenv("BUILD_BUILDNUMBER"),
                "project": os.getenv("SYSTEM_TEAMPROJECT")
            })
        
        # CircleCI
        elif os.getenv("CIRCLECI"):
            config.update({
                "is_ci": True,
                "provider": "circleci",
                "branch": os.getenv("CIRCLE_BRANCH"),
                "commit": os.getenv("CIRCLE_SHA1"),
                "pr_number": os.getenv("CIRCLE_PR_NUMBER"),
                "build_number": os.getenv("CIRCLE_BUILD_NUM"),
                "project": os.getenv("CIRCLE_PROJECT_REPONAME")
            })
        
        return config
    
    def run_docker_tests_for_ci(self, test_types: List[str] = None) -> Dict[str, Any]:
        """Run Docker tests optimized for CI environment."""
        logger.info(f"Running Docker tests in CI mode: {self.ci_mode}")
        logger.info(f"CI Provider: {self.ci_config['provider']}")
        
        if test_types is None:
            # Default test types for CI
            test_types = ["unit", "integration", "e2e", "performance"]
        
        # Import the test runner
        sys.path.append(str(self.project_root / "tests" / "utils"))
        from docker_test_runner import DockerTestRunner
        
        runner = DockerTestRunner(self.project_root)
        
        # Customize test execution for CI
        test_results = {}
        
        for test_type in test_types:
            logger.info(f"Running {test_type} tests...")
            
            try:
                if test_type == "unit":
                    results = runner.run_tier_1_tests()
                elif test_type == "integration":
                    results = runner.run_tier_2_tests()
                elif test_type == "e2e":
                    results = runner.run_tier_3_tests()
                elif test_type == "performance":
                    results = runner.run_performance_tests()
                elif test_type == "chaos":
                    results = runner.run_chaos_tests()
                elif test_type == "production-readiness":
                    results = runner.run_production_readiness_tests()
                else:
                    logger.warning(f"Unknown test type: {test_type}")
                    continue
                
                test_results[test_type] = results
                
                # Early exit on critical failures
                if test_type in ["unit", "integration"] and results.get("status") == "failed":
                    logger.error(f"Critical test failure in {test_type} tests - stopping pipeline")
                    break
                    
            except Exception as e:
                logger.error(f"Exception in {test_type} tests: {e}")
                test_results[test_type] = {"status": "error", "error": str(e)}
        
        # Generate CI-specific report
        ci_report = self._generate_ci_report(test_results)
        
        # Save results with CI metadata
        self._save_ci_results(ci_report)
        
        return ci_report
    
    def _generate_ci_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate CI-specific test report."""
        
        report = {
            "ci_metadata": self.ci_config,
            "timestamp": datetime.now().isoformat(),
            "test_results": test_results,
            "summary": {
                "overall_status": "passed",
                "total_suites": len(test_results),
                "passed_suites": 0,
                "failed_suites": 0,
                "error_suites": 0,
                "total_duration": 0
            }
        }
        
        # Calculate summary
        for suite_name, results in test_results.items():
            status = results.get("status", "unknown")
            duration = results.get("duration", 0)
            
            report["summary"]["total_duration"] += duration
            
            if status == "passed":
                report["summary"]["passed_suites"] += 1
            elif status == "failed":
                report["summary"]["failed_suites"] += 1
                report["summary"]["overall_status"] = "failed"
            else:
                report["summary"]["error_suites"] += 1
                report["summary"]["overall_status"] = "failed"
        
        # Add CI-specific metrics
        report["ci_metrics"] = self._calculate_ci_metrics(test_results)
        
        return report
    
    def _calculate_ci_metrics(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate CI-specific metrics."""
        
        metrics = {
            "build_health": "healthy",
            "performance_regression": False,
            "critical_failures": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check for critical failures
        critical_test_types = ["unit", "integration"]
        for test_type in critical_test_types:
            if test_type in test_results:
                results = test_results[test_type]
                if results.get("status") == "failed":
                    metrics["critical_failures"].append(f"{test_type} tests failed")
                    metrics["build_health"] = "critical"
        
        # Check performance regressions
        if "performance" in test_results:
            perf_results = test_results["performance"]
            if perf_results.get("status") == "failed":
                metrics["performance_regression"] = True
                metrics["warnings"].append("Performance tests failed - possible regression")
        
        # Check test duration
        total_duration = sum(results.get("duration", 0) for results in test_results.values())
        if total_duration > 600:  # 10 minutes
            metrics["warnings"].append(f"Total test duration {total_duration:.1f}s is high")
            metrics["recommendations"].append("Consider parallelizing tests or optimizing slow tests")
        
        # Check for chaos test results
        if "chaos" in test_results:
            chaos_results = test_results["chaos"]
            if chaos_results.get("status") == "failed":
                metrics["warnings"].append("Chaos tests failed - system may not be resilient")
                metrics["recommendations"].append("Review chaos test failures for resilience improvements")
        
        return metrics
    
    def _save_ci_results(self, report: Dict[str, Any]) -> Path:
        """Save CI results with appropriate formatting."""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON report
        json_file = self.project_root / f"ci_docker_test_report_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Generate CI-specific outputs
        if self.ci_config["provider"] == "github-actions":
            self._generate_github_actions_output(report)
        elif self.ci_config["provider"] == "jenkins":
            self._generate_jenkins_output(report)
        elif self.ci_config["provider"] == "gitlab-ci":
            self._generate_gitlab_ci_output(report)
        
        logger.info(f"CI results saved to: {json_file}")
        return json_file
    
    def _generate_github_actions_output(self, report: Dict[str, Any]):
        """Generate GitHub Actions specific output."""
        
        # Set GitHub Actions outputs
        if os.getenv("GITHUB_OUTPUT"):
            with open(os.getenv("GITHUB_OUTPUT"), 'a') as f:
                f.write(f"test_status={report['summary']['overall_status']}\n")
                f.write(f"passed_suites={report['summary']['passed_suites']}\n")
                f.write(f"failed_suites={report['summary']['failed_suites']}\n")
                f.write(f"total_duration={report['summary']['total_duration']:.2f}\n")
        
        # Generate job summary
        if os.getenv("GITHUB_STEP_SUMMARY"):
            summary_content = self._generate_markdown_summary(report)
            with open(os.getenv("GITHUB_STEP_SUMMARY"), 'w') as f:
                f.write(summary_content)
        
        # Set annotations for failures
        for suite_name, results in report["test_results"].items():
            if results.get("status") == "failed":
                error_msg = f":x: {suite_name} tests failed"
                print(f"::error title=Test Failure::{error_msg}")
        
        # Set warnings
        for warning in report.get("ci_metrics", {}).get("warnings", []):
            print(f"::warning title=Test Warning::{warning}")
    
    def _generate_jenkins_output(self, report: Dict[str, Any]):
        """Generate Jenkins specific output."""
        
        # Generate Jenkins-compatible test results
        junit_file = self.project_root / "docker_test_results.xml"
        self._generate_junit_xml(report, junit_file)
        
        # Generate HTML report
        html_file = self.project_root / "docker_test_report.html"
        self._generate_html_report(report, html_file)
        
        logger.info(f"Jenkins JUnit results: {junit_file}")
        logger.info(f"Jenkins HTML report: {html_file}")
    
    def _generate_gitlab_ci_output(self, report: Dict[str, Any]):
        """Generate GitLab CI specific output."""
        
        # Generate GitLab CI artifacts
        artifacts_dir = self.project_root / "test-artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        # Generate JUnit report for GitLab
        junit_file = artifacts_dir / "docker_test_results.xml"
        self._generate_junit_xml(report, junit_file)
        
        # Generate coverage report if available
        coverage_file = artifacts_dir / "coverage.xml"
        # Coverage generation would be implemented based on test results
        
        logger.info(f"GitLab CI artifacts in: {artifacts_dir}")
    
    def _generate_markdown_summary(self, report: Dict[str, Any]) -> str:
        """Generate markdown summary for GitHub Actions."""
        
        summary = report["summary"]
        ci_metrics = report.get("ci_metrics", {})
        
        status_emoji = "✅" if summary["overall_status"] == "passed" else "❌"
        
        markdown = f"""# Docker Test Results {status_emoji}

## Summary
- **Overall Status**: {summary['overall_status'].upper()}
- **Total Test Suites**: {summary['total_suites']}
- **Passed**: {summary['passed_suites']} ✅
- **Failed**: {summary['failed_suites']} ❌
- **Errors**: {summary['error_suites']} ⚠️
- **Total Duration**: {summary['total_duration']:.2f}s

## Test Suite Results
| Suite | Status | Duration |
|-------|--------|----------|
"""
        
        for suite_name, results in report["test_results"].items():
            status = results.get("status", "unknown")
            duration = results.get("duration", 0)
            status_icon = "✅" if status == "passed" else "❌" if status == "failed" else "⚠️"
            
            markdown += f"| {suite_name} | {status_icon} {status} | {duration:.2f}s |\n"
        
        # Add CI metrics
        if ci_metrics.get("critical_failures"):
            markdown += "\n## Critical Failures ❌\n"
            for failure in ci_metrics["critical_failures"]:
                markdown += f"- {failure}\n"
        
        if ci_metrics.get("warnings"):
            markdown += "\n## Warnings ⚠️\n"
            for warning in ci_metrics["warnings"]:
                markdown += f"- {warning}\n"
        
        if ci_metrics.get("recommendations"):
            markdown += "\n## Recommendations 💡\n"
            for rec in ci_metrics["recommendations"]:
                markdown += f"- {rec}\n"
        
        return markdown
    
    def _generate_junit_xml(self, report: Dict[str, Any], output_file: Path):
        """Generate JUnit XML for CI systems."""
        
        # This is a simplified JUnit XML generator
        # In production, you'd use a proper XML library
        
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<testsuites>\n'
        
        for suite_name, results in report["test_results"].items():
            status = results.get("status", "unknown")
            duration = results.get("duration", 0)
            
            xml_content += f'  <testsuite name="{suite_name}" tests="1" failures="{"1" if status == "failed" else "0"}" time="{duration}">\n'
            
            if status == "failed":
                error_msg = results.get("error", "Test suite failed")
                xml_content += f'    <testcase name="{suite_name}_test" classname="{suite_name}">\n'
                xml_content += f'      <failure message="{error_msg}"></failure>\n'
                xml_content += '    </testcase>\n'
            else:
                xml_content += f'    <testcase name="{suite_name}_test" classname="{suite_name}"></testcase>\n'
            
            xml_content += '  </testsuite>\n'
        
        xml_content += '</testsuites>\n'
        
        with open(output_file, 'w') as f:
            f.write(xml_content)
    
    def _generate_html_report(self, report: Dict[str, Any], output_file: Path):
        """Generate HTML report for CI systems."""
        
        summary = report["summary"]
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Docker Test Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .status-passed {{ color: green; }}
        .status-failed {{ color: red; }}
        .status-error {{ color: orange; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Docker Test Results</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Overall Status:</strong> <span class="status-{summary['overall_status']}">{summary['overall_status'].upper()}</span></p>
        <p><strong>Total Duration:</strong> {summary['total_duration']:.2f}s</p>
        <p><strong>Passed Suites:</strong> {summary['passed_suites']}</p>
        <p><strong>Failed Suites:</strong> {summary['failed_suites']}</p>
        <p><strong>Error Suites:</strong> {summary['error_suites']}</p>
    </div>
    
    <div class="results">
        <h2>Test Suite Results</h2>
        <table>
            <tr>
                <th>Suite</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Details</th>
            </tr>
"""
        
        for suite_name, results in report["test_results"].items():
            status = results.get("status", "unknown")
            duration = results.get("duration", 0)
            error = results.get("error", "")
            
            html_content += f"""
            <tr>
                <td>{suite_name}</td>
                <td class="status-{status}">{status.upper()}</td>
                <td>{duration:.2f}s</td>
                <td>{error}</td>
            </tr>
"""
        
        html_content += """
        </table>
    </div>
    
    <div class="metadata">
        <h2>CI Metadata</h2>
        <p><strong>Provider:</strong> {provider}</p>
        <p><strong>Branch:</strong> {branch}</p>
        <p><strong>Commit:</strong> {commit}</p>
        <p><strong>Build:</strong> {build_number}</p>
        <p><strong>Timestamp:</strong> {timestamp}</p>
    </div>
    
</body>
</html>
""".format(
            provider=report["ci_metadata"]["provider"],
            branch=report["ci_metadata"]["branch"] or "unknown",
            commit=report["ci_metadata"]["commit"] or "unknown",
            build_number=report["ci_metadata"]["build_number"] or "unknown",
            timestamp=report["timestamp"]
        )
        
        with open(output_file, 'w') as f:
            f.write(html_content)


def main():
    """Main entry point for CI integration."""
    
    parser = argparse.ArgumentParser(description="Docker CI/CD Integration")
    
    parser.add_argument(
        "--ci-mode",
        choices=["github-actions", "jenkins", "gitlab-ci", "azure-devops", "circleci", "generic"],
        default="generic",
        help="CI/CD provider mode"
    )
    
    parser.add_argument(
        "--test-types",
        nargs="+",
        choices=["unit", "integration", "e2e", "performance", "chaos", "production-readiness"],
        default=["unit", "integration", "e2e"],
        help="Types of tests to run"
    )
    
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Project root directory"
    )
    
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first critical test failure"
    )
    
    args = parser.parse_args()
    
    # Initialize CI integration
    ci_integration = DockerCIIntegration(args.ci_mode, args.project_root)
    
    logger.info(f"Starting Docker CI integration - Mode: {args.ci_mode}")
    logger.info(f"Test types: {args.test_types}")
    
    # Run tests
    try:
        results = ci_integration.run_docker_tests_for_ci(args.test_types)
        
        # Print summary
        summary = results["summary"]
        print(f"\n{'='*60}")
        print("DOCKER CI TEST RESULTS")
        print(f"{'='*60}")
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"Passed Suites: {summary['passed_suites']}")
        print(f"Failed Suites: {summary['failed_suites']}")
        print(f"Error Suites: {summary['error_suites']}")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        print(f"{'='*60}")
        
        # Exit with appropriate code
        if summary["overall_status"] == "passed":
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"CI integration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()