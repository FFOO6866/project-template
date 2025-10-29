"""
Production Validation Test Runner
==================================

Runs comprehensive 3-tier testing strategy with NO MOCKING policy enforcement.

Usage:
    python tests/run_production_validation_tests.py [tier]

    tier: unit, integration, e2e, or all (default: all)

Examples:
    python tests/run_production_validation_tests.py unit           # Fast unit tests only
    python tests/run_production_validation_tests.py integration    # Integration tests with Docker
    python tests/run_production_validation_tests.py e2e            # Full E2E tests
    python tests/run_production_validation_tests.py all            # Complete test suite
"""

import sys
import os
import subprocess
from pathlib import Path
import time
import json

project_root = Path(__file__).parent.parent
os.chdir(project_root)


class Colors:
    """Terminal colors for output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(message: str):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")


def check_docker_infrastructure() -> bool:
    """Check if Docker test infrastructure is running"""
    print_info("Checking Docker test infrastructure...")

    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=horme_pov_test', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print_error("Docker not running or not accessible")
            return False

        containers = result.stdout.strip().split('\n')
        containers = [c for c in containers if c]  # Filter empty lines

        required_containers = ['postgres', 'redis']
        running_containers = []

        for container in containers:
            for required in required_containers:
                if required in container.lower():
                    running_containers.append(required)

        if len(running_containers) >= len(required_containers):
            print_success(f"Docker infrastructure running: {', '.join(running_containers)}")
            return True
        else:
            print_warning(
                f"Some containers missing. Found: {running_containers}, "
                f"Required: {required_containers}"
            )
            return False

    except Exception as e:
        print_error(f"Failed to check Docker infrastructure: {e}")
        return False


def start_docker_infrastructure() -> bool:
    """Start Docker test infrastructure"""
    print_info("Starting Docker test infrastructure...")

    try:
        # Navigate to tests/utils and start infrastructure
        result = subprocess.run(
            ['docker-compose', '-f', 'tests/utils/docker-compose.test.yml', 'up', '-d',
             'postgres', 'redis'],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            print_error(f"Failed to start infrastructure: {result.stderr}")
            return False

        print_success("Docker infrastructure started")

        # Wait for services to be healthy
        print_info("Waiting for services to be healthy...")
        time.sleep(10)

        return check_docker_infrastructure()

    except Exception as e:
        print_error(f"Failed to start Docker infrastructure: {e}")
        return False


def run_tier1_unit_tests() -> dict:
    """Run Tier 1 Unit Tests (NO infrastructure required)"""
    print_header("TIER 1: Unit Tests - Production Compliance")

    print_info("Speed: <1 second per test")
    print_info("Isolation: No external dependencies")
    print_info("Focus: Fail-fast validation, no mock data detection")
    print()

    start_time = time.time()

    cmd = [
        'pytest',
        'tests/unit/test_production_compliance.py',
        '-v',
        '--tb=short',
        '--timeout=1',
        '-m', 'not integration',
        '-m', 'not e2e',
        '--color=yes'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_time

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode == 0:
        print_success(f"Tier 1 tests PASSED in {elapsed:.2f}s")
        return {'tier': 1, 'passed': True, 'time': elapsed, 'output': result.stdout}
    else:
        print_error(f"Tier 1 tests FAILED in {elapsed:.2f}s")
        return {'tier': 1, 'passed': False, 'time': elapsed, 'output': result.stdout}


def run_tier2_integration_tests() -> dict:
    """Run Tier 2 Integration Tests (Docker infrastructure required)"""
    print_header("TIER 2: Integration Tests - Real Database Queries")

    print_info("Speed: <5 seconds per test")
    print_info("Infrastructure: Docker PostgreSQL + Redis")
    print_info("Focus: Real database operations, NO MOCKING")
    print()

    # Check infrastructure
    if not check_docker_infrastructure():
        print_warning("Docker infrastructure not running. Attempting to start...")
        if not start_docker_infrastructure():
            print_error("Failed to start infrastructure. Skipping Tier 2 tests.")
            return {'tier': 2, 'passed': False, 'time': 0, 'output': 'Infrastructure unavailable'}

    start_time = time.time()

    cmd = [
        'pytest',
        'tests/integration/test_real_database_queries.py',
        '-v',
        '--tb=short',
        '--timeout=5',
        '-m', 'integration',
        '--color=yes'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_time

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode == 0:
        print_success(f"Tier 2 tests PASSED in {elapsed:.2f}s")
        return {'tier': 2, 'passed': True, 'time': elapsed, 'output': result.stdout}
    else:
        print_error(f"Tier 2 tests FAILED in {elapsed:.2f}s")
        return {'tier': 2, 'passed': False, 'time': elapsed, 'output': result.stdout}


def run_tier3_e2e_tests() -> dict:
    """Run Tier 3 End-to-End Tests (Complete infrastructure required)"""
    print_header("TIER 3: End-to-End Tests - Production Workflows")

    print_info("Speed: <10 seconds per test")
    print_info("Infrastructure: Complete Docker stack")
    print_info("Focus: Complete user workflows, real data")
    print()

    # Check infrastructure
    if not check_docker_infrastructure():
        print_warning("Docker infrastructure not running. Attempting to start...")
        if not start_docker_infrastructure():
            print_error("Failed to start infrastructure. Skipping Tier 3 tests.")
            return {'tier': 3, 'passed': False, 'time': 0, 'output': 'Infrastructure unavailable'}

    start_time = time.time()

    cmd = [
        'pytest',
        'tests/e2e/test_production_workflows.py',
        '-v',
        '--tb=short',
        '--timeout=10',
        '-m', 'e2e',
        '--color=yes'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_time

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode == 0:
        print_success(f"Tier 3 tests PASSED in {elapsed:.2f}s")
        return {'tier': 3, 'passed': True, 'time': elapsed, 'output': result.stdout}
    else:
        print_error(f"Tier 3 tests FAILED in {elapsed:.2f}s")
        return {'tier': 3, 'passed': False, 'time': elapsed, 'output': result.stdout}


def generate_test_report(results: list):
    """Generate test execution report"""
    print_header("TEST EXECUTION SUMMARY")

    total_time = sum(r['time'] for r in results)
    passed_count = sum(1 for r in results if r['passed'])
    failed_count = len(results) - passed_count

    print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
    for result in results:
        tier_name = f"Tier {result['tier']}"
        status = f"{Colors.OKGREEN}PASSED{Colors.ENDC}" if result['passed'] else f"{Colors.FAIL}FAILED{Colors.ENDC}"
        print(f"  {tier_name}: {status} ({result['time']:.2f}s)")

    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print(f"  Total Tests: {len(results)} tiers")
    print(f"  Passed: {Colors.OKGREEN}{passed_count}{Colors.ENDC}")
    print(f"  Failed: {Colors.FAIL}{failed_count}{Colors.ENDC}")
    print(f"  Total Time: {total_time:.2f}s")

    if failed_count == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ ALL TESTS PASSED - PRODUCTION READY{Colors.ENDC}")
        return 0
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ TESTS FAILED - PRODUCTION NOT READY{Colors.ENDC}")
        return 1


def main():
    """Main test runner"""
    tier = sys.argv[1] if len(sys.argv) > 1 else 'all'

    print_header("PRODUCTION VALIDATION TEST SUITE")
    print_info("3-Tier Testing Strategy with NO MOCKING Policy")
    print_info("Testing: Horme POV Product Recommendation System")
    print()

    results = []

    if tier in ['unit', 'all']:
        results.append(run_tier1_unit_tests())

    if tier in ['integration', 'all']:
        results.append(run_tier2_integration_tests())

    if tier in ['e2e', 'all']:
        results.append(run_tier3_e2e_tests())

    if not results:
        print_error(f"Invalid tier: {tier}")
        print_info("Valid options: unit, integration, e2e, all")
        return 1

    return generate_test_report(results)


if __name__ == '__main__':
    sys.exit(main())
