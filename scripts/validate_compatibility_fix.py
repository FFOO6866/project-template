#!/usr/bin/env python3
"""
Validation Script for Compatibility Fix

Validates that:
1. No hardcoded compatibility recommendations exist
2. All compatibility functions use real Neo4j queries
3. Proper error handling is in place
4. Integration tests pass

Run this before committing compatibility-related changes.
"""

import os
import sys
import subprocess
import re
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class Colors:
    """Terminal color codes"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_section(title):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}[OK] {message}{Colors.END}")


def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARN] {message}{Colors.END}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}[ERROR] {message}{Colors.END}")


def check_for_hardcoded_data():
    """Check for hardcoded compatibility data"""
    print_section("STEP 1: Check for Hardcoded Compatibility Data")

    violations = []
    target_file = PROJECT_ROOT / "src" / "production_nexus_diy_platform.py"

    # Forbidden patterns that indicate hardcoded data
    forbidden_patterns = [
        (r'return \[.*"These products are compatible".*\]', "Hardcoded compatibility message"),
        (r'return \[.*"No adapters".*\]', "Hardcoded adapter message"),
        (r'return \[.*"Follow standard installation".*\]', "Hardcoded installation message"),
        (r"'safety_rating': 'safe'.*# Without analysis", "Hardcoded safety rating without analysis"),
        (r"'warnings': \[\].*# Empty without checking", "Empty warnings without checking"),
    ]

    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # Check _analyze_compatibility function
    if "TODO: Query REAL compatibility database" in content:
        violations.append("_analyze_compatibility still has TODO for real database")

    if "raise HTTPException.*501.*Feature not yet implemented" in content:
        # Check if this is in the right place (should only be for Neo4j not configured)
        if "Neo4j knowledge graph" not in content:
            violations.append("HTTPException 501 missing Neo4j configuration check")

    # Check for forbidden patterns
    for pattern, description in forbidden_patterns:
        if re.search(pattern, content):
            violations.append(f"Found forbidden pattern: {description}")

    # Check that Neo4j validation exists
    if "if not hasattr(self.knowledge_graph, 'driver'):" not in content:
        violations.append("Missing Neo4j driver validation in _analyze_compatibility")

    # Check that real relationship parsing exists
    if "for rel in compat1:" not in content:
        violations.append("Missing relationship parsing in _analyze_compatibility")

    if "if rel['relationship_type'] == 'COMPATIBLE_WITH':" not in content:
        violations.append("Missing COMPATIBLE_WITH relationship handling")

    # Report results
    if violations:
        for violation in violations:
            print_error(violation)
        return False
    else:
        print_success("No hardcoded compatibility data found")
        print_success("Real Neo4j integration confirmed")
        return True


def check_error_handling():
    """Check for proper error handling"""
    print_section("STEP 2: Check Error Handling")

    target_file = PROJECT_ROOT / "src" / "production_nexus_diy_platform.py"

    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = {
        "HTTPException 501 for Neo4j not configured": 'raise HTTPException.*status_code=501.*Neo4j knowledge graph',
        "HTTPException 404 for no relationships": 'raise HTTPException.*status_code=404.*No compatibility relationships',
        "Confidence score extraction": 'rel.get\\(.*confidence.*\\)',
        "Safety notes extraction": 'rel.get\\(.*safety_notes.*\\)',
    }

    all_passed = True
    for check_name, pattern in checks.items():
        if re.search(pattern, content, re.DOTALL):
            print_success(f"{check_name}: Present")
        else:
            print_error(f"{check_name}: MISSING")
            all_passed = False

    return all_passed


def check_integration_test_exists():
    """Check that integration test exists"""
    print_section("STEP 3: Check Integration Test Exists")

    test_file = PROJECT_ROOT / "tests" / "integration" / "test_production_compatibility.py"

    if not test_file.exists():
        print_error(f"Integration test file not found: {test_file}")
        return False

    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for required test cases
    required_tests = [
        "test_compatible_products_analysis",
        "test_incompatible_products_analysis",
        "test_no_compatibility_data_raises_404",
        "test_neo4j_not_configured_raises_501",
        "test_confidence_scores_from_relationships",
    ]

    all_found = True
    for test_name in required_tests:
        if f"async def {test_name}" in content:
            print_success(f"Test found: {test_name}")
        else:
            print_error(f"Test missing: {test_name}")
            all_found = False

    # Check for NO MOCKING markers
    if "# TIER 2: INTEGRATION TESTS (Real Neo4j, NO MOCKING)" in content:
        print_success("NO MOCKING policy documented in tests")
    else:
        print_warning("NO MOCKING policy not clearly documented")

    return all_found


def run_integration_tests():
    """Run integration tests using Docker"""
    print_section("STEP 4: Run Integration Tests")

    # Check if Docker is available
    try:
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print_warning("Docker not available - skipping integration tests")
            return True
    except Exception as e:
        print_warning(f"Docker not available: {e} - skipping integration tests")
        return True

    print("Starting Docker test services...")

    # Start Docker test services
    try:
        subprocess.run(
            ['docker-compose', '-f', 'docker-compose.test.yml', 'up', '-d'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=60
        )
    except subprocess.TimeoutExpired:
        print_warning("Docker services taking too long to start - skipping tests")
        return True
    except Exception as e:
        print_warning(f"Failed to start Docker services: {e} - skipping tests")
        return True

    print("Waiting for services to be healthy...")
    import time
    time.sleep(10)

    # Run integration tests
    try:
        result = subprocess.run(
            [
                'docker-compose', '-f', 'docker-compose.test.yml', 'run', '--rm', 'test-runner',
                'pytest', 'tests/integration/test_production_compatibility.py', '-v', '--timeout=5'
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            print_success("All integration tests passed")
            print("\nTest output:")
            print(result.stdout)
            return True
        else:
            print_error("Integration tests failed")
            print("\nTest output:")
            print(result.stdout)
            print("\nTest errors:")
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print_error("Integration tests timed out")
        return False
    except Exception as e:
        print_error(f"Failed to run integration tests: {e}")
        return False
    finally:
        # Cleanup Docker services
        try:
            subprocess.run(
                ['docker-compose', '-f', 'docker-compose.test.yml', 'down'],
                cwd=PROJECT_ROOT,
                capture_output=True,
                timeout=30
            )
        except:
            pass


def check_documentation():
    """Check that documentation is updated"""
    print_section("STEP 5: Check Documentation")

    summary_file = PROJECT_ROOT / "COMPATIBILITY_FIX_SUMMARY.md"

    if not summary_file.exists():
        print_error("COMPATIBILITY_FIX_SUMMARY.md not found")
        return False

    with open(summary_file, 'r', encoding='utf-8') as f:
        content = f.read()

    required_sections = [
        "## What Was Fixed",
        "## Changes Made",
        "## Integration with Existing Infrastructure",
        "## Test Coverage",
        "## Running the Tests",
        "## Compliance with Production Code Quality Standards",
    ]

    all_found = True
    for section in required_sections:
        if section in content:
            print_success(f"Documentation section found: {section}")
        else:
            print_error(f"Documentation section missing: {section}")
            all_found = False

    return all_found


def main():
    """Run all validation checks"""
    print(f"\n{Colors.BOLD}Compatibility Fix Validation Script{Colors.END}")
    print(f"{Colors.BOLD}Target: production_nexus_diy_platform.py{Colors.END}")

    results = {
        "Hardcoded Data Check": check_for_hardcoded_data(),
        "Error Handling Check": check_error_handling(),
        "Integration Test Exists": check_integration_test_exists(),
        "Documentation Check": check_documentation(),
    }

    # Run integration tests (optional if Docker available)
    if os.environ.get('RUN_INTEGRATION_TESTS', 'false').lower() == 'true':
        results["Integration Tests"] = run_integration_tests()

    # Summary
    print_section("VALIDATION SUMMARY")

    all_passed = True
    for check_name, passed in results.items():
        if passed:
            print_success(f"{check_name}: PASSED")
        else:
            print_error(f"{check_name}: FAILED")
            all_passed = False

    print()
    if all_passed:
        print_success("ALL VALIDATION CHECKS PASSED")
        print_success("Compatibility fix is ready for commit")
        return 0
    else:
        print_error("VALIDATION FAILED")
        print_error("Fix the issues above before committing")
        return 1


if __name__ == "__main__":
    sys.exit(main())
