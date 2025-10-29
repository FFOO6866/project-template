#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation script for E2E RFP PostgreSQL migration.

Checks that the migrated tests can connect to PostgreSQL and validates schema.
"""

import os
import sys
from pathlib import Path

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_postgresql_connection():
    """Verify PostgreSQL test database is accessible."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        host = os.environ.get('POSTGRES_HOST', 'localhost')
        port = os.environ.get('POSTGRES_PORT', '5434')
        database = os.environ.get('POSTGRES_DB', 'horme_test')
        user = os.environ.get('POSTGRES_USER', 'test_user')
        password = os.environ.get('POSTGRES_PASSWORD', 'test_password')

        print(f"Connecting to PostgreSQL at {host}:{port}/{database}...")

        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            cursor_factory=RealDictCursor,
            connect_timeout=5
        )

        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()

        print(f"✅ PostgreSQL connected successfully!")
        print(f"   Version: {version['version']}")

        cursor.close()
        conn.close()

        return True

    except ImportError:
        print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL test container is running:")
        print("   cd tests/utils && python setup_local_docker.py")
        print("2. Check container status:")
        print("   docker ps | grep horme_pov_test_postgres")
        print("3. Check container logs:")
        print("   docker logs horme_pov_test_postgres")
        return False


def validate_rfp_schema():
    """Validate that RFP-specific tables can be created."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        host = os.environ.get('POSTGRES_HOST', 'localhost')
        port = os.environ.get('POSTGRES_PORT', '5434')
        database = os.environ.get('POSTGRES_DB', 'horme_test')
        user = os.environ.get('POSTGRES_USER', 'test_user')
        password = os.environ.get('POSTGRES_PASSWORD', 'test_password')

        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            cursor_factory=RealDictCursor
        )
        conn.autocommit = False

        cursor = conn.cursor()

        # Try to create RFP tables (same as in test fixture)
        print("\nValidating RFP schema creation...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_validation_companies (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                industry TEXT,
                size_category TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_validation_rfp_documents (
                id SERIAL PRIMARY KEY,
                company_id INTEGER REFERENCES test_validation_companies(id) ON DELETE SET NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                document_type TEXT,
                complexity_score INTEGER,
                estimated_budget DECIMAL(12,2),
                deadline_date DATE,
                status TEXT DEFAULT 'received',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Test JSONB support
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_validation_quotations (
                id SERIAL PRIMARY KEY,
                rfp_document_id INTEGER REFERENCES test_validation_rfp_documents(id) ON DELETE CASCADE,
                line_items JSONB,
                total_value DECIMAL(12,2),
                confidence_score DECIMAL(3,2)
            )
        """)

        conn.commit()

        print("✅ RFP schema validated successfully!")
        print("   - SERIAL PRIMARY KEY supported")
        print("   - FOREIGN KEY constraints supported")
        print("   - DECIMAL data type supported")
        print("   - JSONB data type supported")
        print("   - TIMESTAMP WITH TIME ZONE supported")

        # Cleanup test tables
        cursor.execute("DROP TABLE IF EXISTS test_validation_quotations CASCADE")
        cursor.execute("DROP TABLE IF EXISTS test_validation_rfp_documents CASCADE")
        cursor.execute("DROP TABLE IF EXISTS test_validation_companies CASCADE")
        conn.commit()

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False


def validate_test_dependencies():
    """Check that all required Python dependencies are installed."""
    print("\nChecking Python dependencies...")

    dependencies = {
        'pytest': 'pytest',
        'psycopg2': 'psycopg2-binary',
    }

    all_installed = True

    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {module} installed")
        except ImportError:
            print(f"❌ {module} NOT installed (install with: pip install {package})")
            all_installed = False

    return all_installed


def check_docker_container():
    """Check if PostgreSQL Docker container is running."""
    try:
        import subprocess

        print("\nChecking Docker container status...")

        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=horme_pov_test_postgres', '--format', '{{.Names}}\t{{.Status}}'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            container_info = result.stdout.strip()
            print(f"✅ PostgreSQL container running: {container_info}")
            return True
        else:
            print("❌ PostgreSQL container NOT running")
            print("\nTo start the container:")
            print("   cd tests/utils")
            print("   python setup_local_docker.py")
            return False

    except FileNotFoundError:
        print("⚠️  Docker not found. Ensure Docker Desktop is installed and running.")
        return False
    except subprocess.TimeoutExpired:
        print("⚠️  Docker command timeout. Check Docker Desktop status.")
        return False
    except Exception as e:
        print(f"⚠️  Could not check Docker status: {e}")
        return False


def main():
    """Run all validation checks."""
    print("=" * 70)
    print("E2E RFP PostgreSQL Migration Validation")
    print("=" * 70)

    checks = [
        ("Python Dependencies", validate_test_dependencies),
        ("Docker Container", check_docker_container),
        ("PostgreSQL Connection", check_postgresql_connection),
        ("RFP Schema", validate_rfp_schema),
    ]

    results = {}

    for check_name, check_func in checks:
        print(f"\n{'=' * 70}")
        print(f"Check: {check_name}")
        print("=" * 70)
        results[check_name] = check_func()

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    all_passed = all(results.values())

    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")

    print("=" * 70)

    if all_passed:
        print("\n🎉 All validation checks passed!")
        print("\nYou can now run the E2E RFP tests:")
        print("   pytest tests/e2e/test_rfp_analysis_workflow.py -v")
        return 0
    else:
        print("\n⚠️  Some validation checks failed. Please fix the issues above.")
        print("\nQuick troubleshooting:")
        print("1. Install dependencies: pip install -r requirements-test.txt")
        print("2. Start test infrastructure: cd tests/utils && python setup_local_docker.py")
        print("3. Verify PostgreSQL is ready: docker logs horme_pov_test_postgres")
        return 1


if __name__ == '__main__':
    sys.exit(main())
