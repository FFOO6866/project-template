#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation script for AI model configuration fixes.
Checks that all hardcoded paths are removed and environment variables are set correctly.
"""

import os
import sys
from pathlib import Path
import subprocess

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_environment_variables():
    """Check that all required environment variables are set"""
    print("Checking environment variables...")

    required_vars = {
        'OPENAI_TIMEOUT': '120',
        'OPENAI_MAX_RETRIES': '3',
        'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
        'EMBEDDING_DIMENSION': '384',
        'INTENT_CLASSIFIER_MODEL_PATH': '/app/models/intent_classifier',
        'INTENT_TRAINING_DATA_PATH': '/app/src/intent_classification/training_data.json',
    }

    missing_vars = []
    for var, expected in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} (expected: {expected})")
        else:
            print(f"  ✓ {var}={value}")

    if missing_vars:
        print(f"\n  ✗ Missing environment variables:")
        for var in missing_vars:
            print(f"    - {var}")
        return False

    print("  ✓ All required environment variables are set")
    return True

def check_hardcoded_paths():
    """Check for hardcoded Windows paths in source files"""
    print("\nChecking for hardcoded Windows paths...")

    project_root = Path(__file__).parent.parent
    src_dir = project_root / 'src'

    problematic_files = []

    # Files to check
    files_to_check = [
        src_dir / 'intent_classification' / 'intent_classifier.py',
        src_dir / 'intent_classification' / 'training_data.py',
        src_dir / 'migrations' / 'sqlite_to_postgresql.py',
    ]

    hardcoded_pattern = 'C:/Users/fujif'

    for file_path in files_to_check:
        if not file_path.exists():
            print(f"  ⚠ File not found: {file_path}")
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if hardcoded_pattern in content:
            problematic_files.append(file_path.relative_to(project_root))

    if problematic_files:
        print(f"  ✗ Found hardcoded Windows paths in:")
        for file_path in problematic_files:
            print(f"    - {file_path}")
        return False

    print("  ✓ No hardcoded Windows paths found")
    return True

def check_dockerfile_postgres():
    """Check that Dockerfile.postgres exists and has pgvector"""
    print("\nChecking PostgreSQL Dockerfile...")

    project_root = Path(__file__).parent.parent
    dockerfile = project_root / 'Dockerfile.postgres'

    if not dockerfile.exists():
        print(f"  ✗ Dockerfile.postgres not found")
        return False

    with open(dockerfile, 'r') as f:
        content = f.read()

    if 'pgvector' not in content:
        print(f"  ✗ Dockerfile.postgres does not contain pgvector installation")
        return False

    print("  ✓ Dockerfile.postgres exists with pgvector support")
    return True

def check_init_scripts():
    """Check that vector support SQL script exists"""
    print("\nChecking database initialization scripts...")

    project_root = Path(__file__).parent.parent
    vector_script = project_root / 'init-scripts' / '02-add-vector-support.sql'

    if not vector_script.exists():
        print(f"  ✗ Vector support SQL script not found")
        return False

    with open(vector_script, 'r') as f:
        content = f.read()

    required_elements = [
        'CREATE EXTENSION IF NOT EXISTS vector',
        'vector(384)',
        'cosine_similarity',
    ]

    missing = [elem for elem in required_elements if elem not in content]

    if missing:
        print(f"  ✗ Vector support script missing required elements:")
        for elem in missing:
            print(f"    - {elem}")
        return False

    print("  ✓ Vector support SQL script is complete")
    return True

def check_docker_compose():
    """Check that docker-compose.production.yml uses custom postgres image"""
    print("\nChecking docker-compose configuration...")

    project_root = Path(__file__).parent.parent
    compose_file = project_root / 'docker-compose.production.yml'

    if not compose_file.exists():
        print(f"  ✗ docker-compose.production.yml not found")
        return False

    with open(compose_file, 'r') as f:
        content = f.read()

    required_elements = [
        'Dockerfile.postgres',
        '02-add-vector-support.sql',
    ]

    missing = [elem for elem in required_elements if elem not in content]

    if missing:
        print(f"  ✗ docker-compose.production.yml missing required elements:")
        for elem in missing:
            print(f"    - {elem}")
        return False

    print("  ✓ docker-compose.production.yml is correctly configured")
    return True

def check_model_download_script():
    """Check that model download script exists"""
    print("\nChecking model download script...")

    project_root = Path(__file__).parent.parent
    download_script = project_root / 'scripts' / 'download_models.py'

    if not download_script.exists():
        print(f"  ✗ Model download script not found")
        return False

    with open(download_script, 'r') as f:
        content = f.read()

    if 'SentenceTransformer' not in content or 'all-MiniLM-L6-v2' not in content:
        print(f"  ✗ Model download script incomplete")
        return False

    print("  ✓ Model download script exists and is complete")
    return True

def main():
    """Run all validation checks"""
    print("=" * 70)
    print("AI MODEL CONFIGURATION VALIDATION")
    print("=" * 70)

    checks = [
        check_environment_variables,
        check_hardcoded_paths,
        check_dockerfile_postgres,
        check_init_scripts,
        check_docker_compose,
        check_model_download_script,
    ]

    results = []
    for check in checks:
        try:
            results.append(check())
        except Exception as e:
            print(f"  ✗ Check failed with error: {e}")
            results.append(False)

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if all(results):
        print("\n✓ SUCCESS: All validation checks passed!")
        print("\nNext steps:")
        print("1. Rebuild PostgreSQL container: docker-compose build postgres")
        print("2. Restart containers: docker-compose up -d")
        print("3. Verify pgvector: docker exec horme-postgres psql -U horme_user -d horme_db -c 'CREATE EXTENSION vector;'")
        return 0
    else:
        print("\n✗ FAILURE: Some validation checks failed!")
        print("Review the errors above and fix the issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
