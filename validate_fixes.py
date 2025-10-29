#!/usr/bin/env python3
"""
Brutal Production Readiness Validation - Post-Fix Assessment
Validates fixes to hybrid_recommendation_engine.py and docker-compose.production.yml
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Production code files (exclude tests, examples, demos)
PRODUCTION_PATTERNS = [
    'src/core/',
    'src/api/',
    'src/ai/',
    'src/nexus_production',
    'src/production_',
]

EXCLUDE_PATTERNS = [
    '/test_',
    '/tests/',
    '/demo_',
    '/simple_',
    '/knowledge_graph/examples/',
    '/knowledge_graph/tests/',
    '/new_project/',  # Test infrastructure
]

def is_production_file(path: Path) -> bool:
    """Determine if a file is production code vs test/demo"""
    path_str = str(path)

    # Exclude test/demo files
    for exclude in EXCLUDE_PATTERNS:
        if exclude in path_str:
            return False

    # Check if it's in production areas
    for pattern in PRODUCTION_PATTERNS:
        if pattern in path_str:
            return True

    # Check root-level production files
    if path.parent.name == 'src' and (
        'nexus_production' in path.name or
        'production_' in path.name
    ):
        return True

    return False

def scan_for_violations() -> Dict[str, List[str]]:
    """Scan production code for critical violations"""
    violations = {
        'localhost_redis_fallback': [],
        'localhost_postgres_fallback': [],
        'localhost_neo4j_fallback': [],
        'hardcoded_business_logic': [],
        'dict_get_defaults': []
    }

    for py_file in Path('src').rglob('*.py'):
        if not is_production_file(py_file):
            continue

        try:
            content = py_file.read_text(encoding='utf-8')
            rel_path = str(py_file.relative_to('src'))

            # Check for redis://localhost with .get() default
            if re.search(r'\.get\s*\(\s*["\']REDIS_URL["\']\s*,\s*["\']redis://localhost', content):
                violations['localhost_redis_fallback'].append(rel_path)

            # Check for localhost PostgreSQL fallback
            if re.search(r'\.get\s*\(\s*["\']DATABASE_URL["\']\s*,\s*["\'].*localhost.*postgres', content):
                violations['localhost_postgres_fallback'].append(rel_path)

            # Check for localhost Neo4j fallback
            if re.search(r'\.get\s*\(\s*["\']NEO4J_URI["\']\s*,\s*["\'].*localhost', content):
                violations['localhost_neo4j_fallback'].append(rel_path)

            # Check for large hardcoded dictionaries (business logic)
            if re.search(r'(category_keywords|task_keywords)\s*=\s*\{[^}]{500,}\}', content, re.DOTALL):
                violations['hardcoded_business_logic'].append(rel_path)

            # Check for dict .get() with defaults (potential fallback violations)
            get_matches = re.findall(r'\.get\s*\(\s*["\'](\w+)["\']\s*,\s*([^)]+)\)', content)
            if get_matches:
                # Filter for configuration keys only
                config_keys = ['REDIS_URL', 'DATABASE_URL', 'NEO4J_URI', 'CORS_ORIGINS',
                              'NEXT_PUBLIC_API_URL', 'NEXT_PUBLIC_WEBSOCKET_URL']
                for key, default in get_matches:
                    if key in config_keys and 'localhost' in default.lower():
                        violations['dict_get_defaults'].append(f"{rel_path}:{key}={default}")

        except Exception as e:
            print(f"Error scanning {py_file}: {e}")

    return violations

def check_docker_compose_fixes() -> Dict[str, bool]:
    """Verify docker-compose.production.yml fixes"""
    checks = {
        'no_cors_localhost_fallback': False,
        'no_api_url_localhost_fallback': False,
        'no_websocket_url_localhost_fallback': False
    }

    try:
        content = Path('docker-compose.production.yml').read_text(encoding='utf-8')

        # Check for removed fallbacks
        checks['no_cors_localhost_fallback'] = not bool(
            re.search(r'CORS_ORIGINS.*:-.*localhost', content)
        )
        checks['no_api_url_localhost_fallback'] = not bool(
            re.search(r'NEXT_PUBLIC_API_URL.*:-.*localhost', content)
        )
        checks['no_websocket_url_localhost_fallback'] = not bool(
            re.search(r'NEXT_PUBLIC_WEBSOCKET_URL.*:-.*localhost', content)
        )

    except Exception as e:
        print(f"Error checking docker-compose: {e}")

    return checks

def check_hybrid_engine_fixes() -> Dict[str, bool]:
    """Verify hybrid_recommendation_engine.py fixes"""
    checks = {
        'no_redis_localhost_fallback': False,
        'no_hardcoded_category_keywords': False,
        'no_hardcoded_task_keywords': False,
        'has_db_loading_methods': False
    }

    try:
        content = Path('src/ai/hybrid_recommendation_engine.py').read_text(encoding='utf-8')

        # Check for removed localhost fallback
        checks['no_redis_localhost_fallback'] = 'redis://localhost' not in content

        # Check for removed hardcoded dictionaries
        checks['no_hardcoded_category_keywords'] = not bool(
            re.search(r'category_keywords\s*=\s*\{["\'].*?["\']:', content)
        )
        checks['no_hardcoded_task_keywords'] = not bool(
            re.search(r'task_keywords\s*=\s*\{["\'].*?["\']:', content)
        )

        # Check for database loading methods
        checks['has_db_loading_methods'] = (
            '_load_category_keywords_from_db' in content and
            '_load_task_keywords_from_db' in content
        )

    except Exception as e:
        print(f"Error checking hybrid_recommendation_engine.py: {e}")

    return checks

def calculate_compliance_score(
    violations: Dict[str, List[str]],
    docker_checks: Dict[str, bool],
    hybrid_checks: Dict[str, bool]
) -> Tuple[int, str]:
    """Calculate production readiness compliance score"""

    # Scoring criteria (0-100 for each dimension)
    scores = {}

    # 1. No Hardcoding (0-100)
    hardcoding_violations = (
        len(violations['hardcoded_business_logic'])
    )
    scores['no_hardcoding'] = max(0, 100 - (hardcoding_violations * 50))

    # 2. No Mock/Fallback (0-100)
    fallback_violations = (
        len(violations['localhost_redis_fallback']) +
        len(violations['localhost_postgres_fallback']) +
        len(violations['localhost_neo4j_fallback']) +
        len(violations['dict_get_defaults'])
    )
    scores['no_fallback'] = max(0, 100 - (fallback_violations * 20))

    # 3. No Localhost (0-100)
    localhost_violations = (
        len(violations['localhost_redis_fallback']) +
        len(violations['localhost_postgres_fallback']) +
        len(violations['localhost_neo4j_fallback'])
    )
    scores['no_localhost'] = max(0, 100 - (localhost_violations * 25))

    # 4. Docker Compliance (0-100)
    docker_passed = sum(1 for v in docker_checks.values() if v)
    docker_total = len(docker_checks)
    scores['docker_compliance'] = int((docker_passed / docker_total) * 100) if docker_total > 0 else 0

    # 5. Fail-Fast (0-100)
    hybrid_passed = sum(1 for v in hybrid_checks.values() if v)
    hybrid_total = len(hybrid_checks)
    scores['fail_fast'] = int((hybrid_passed / hybrid_total) * 100) if hybrid_total > 0 else 0

    # 6. Config Management (0-100)
    # Perfect if no fallbacks exist
    scores['config_management'] = 100 if fallback_violations == 0 else max(0, 100 - (fallback_violations * 15))

    # Total score (average)
    total_score = int(sum(scores.values()) / len(scores))

    # Determination
    if total_score < 90:
        determination = "FAIL"
    elif total_score < 95:
        determination = "CONDITIONAL PASS"
    else:
        determination = "PASS"

    return total_score, determination, scores

def main():
    """Run validation and generate report"""
    print("=" * 80)
    print("BRUTAL PRODUCTION READINESS VALIDATION - POST-FIX ASSESSMENT")
    print("=" * 80)
    print()

    # Scan for violations
    print("Scanning production code for violations...")
    violations = scan_for_violations()

    print("Checking docker-compose.production.yml fixes...")
    docker_checks = check_docker_compose_fixes()

    print("Checking hybrid_recommendation_engine.py fixes...")
    hybrid_checks = check_hybrid_engine_fixes()

    print()
    print("=" * 80)
    print("FIX VERIFICATION RESULTS")
    print("=" * 80)
    print()

    # Docker Compose Fixes
    print("Docker-Compose Production Fixes:")
    for check, passed in docker_checks.items():
        status = "[FIXED]" if passed else "[NOT FIXED]"
        print(f"  {status}: {check}")
    print()

    # Hybrid Engine Fixes
    print("Hybrid Recommendation Engine Fixes:")
    for check, passed in hybrid_checks.items():
        status = "[FIXED]" if passed else "[NOT FIXED]"
        print(f"  {status}: {check}")
    print()

    # Remaining Violations
    print("=" * 80)
    print("REMAINING PRODUCTION CODE VIOLATIONS")
    print("=" * 80)
    print()

    total_violations = sum(len(v) if isinstance(v, list) else 0 for v in violations.values())

    if total_violations == 0:
        print("[OK] NO CRITICAL VIOLATIONS FOUND IN PRODUCTION CODE")
    else:
        for category, items in violations.items():
            if items:
                print(f"{category.upper()}:")
                for item in items[:10]:  # Show first 10
                    print(f"  - {item}")
                if len(items) > 10:
                    print(f"  ... and {len(items) - 10} more")
                print()

    # Calculate Compliance Score
    total_score, determination, dimension_scores = calculate_compliance_score(
        violations, docker_checks, hybrid_checks
    )

    print("=" * 80)
    print("COMPLIANCE SCORE BREAKDOWN")
    print("=" * 80)
    print()

    for dimension, score in dimension_scores.items():
        bar_length = int(score / 5)
        bar = "#" * bar_length + "-" * (20 - bar_length)
        print(f"{dimension:25s}: {score:3d}/100 [{bar}]")

    print()
    print(f"{'TOTAL SCORE':25s}: {total_score:3d}/100")
    print()

    # Determination
    print("=" * 80)
    print("PRODUCTION READINESS DETERMINATION")
    print("=" * 80)
    print()

    if determination == "PASS":
        print(f"[PASS] {determination} - Production Ready (Score: {total_score}/100)")
        print()
        print("All critical violations resolved. System meets production standards.")
    elif determination == "CONDITIONAL PASS":
        print(f"[WARN] {determination} - Acceptable with Documentation (Score: {total_score}/100)")
        print()
        print("Minor violations remain but do not block deployment.")
        print("Document all remaining issues in production runbook.")
    else:
        print(f"[FAIL] {determination} - NOT Production Ready (Score: {total_score}/100)")
        print()
        print("Critical violations must be resolved before deployment.")

    print()

    # Recommendations
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()

    if total_violations > 0:
        print("Remaining violations to address:")
        if violations['localhost_redis_fallback']:
            print("  1. Remove localhost Redis fallbacks from production code")
        if violations['localhost_postgres_fallback']:
            print("  2. Remove localhost PostgreSQL fallbacks from production code")
        if violations['hardcoded_business_logic']:
            print("  3. Move hardcoded business logic to database")
        if violations['dict_get_defaults']:
            print("  4. Remove .get() defaults for critical configuration")
    else:
        print("  [OK] All known violations have been resolved!")
        print("  [OK] System is production-ready from a configuration standpoint")

    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
