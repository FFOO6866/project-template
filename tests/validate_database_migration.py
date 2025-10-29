"""
Database Migration Validation Script
Validates that migration 0006 can be safely applied
NO MOCK - Tests against real database schema
"""

import os
import sys
import asyncpg
import asyncio
from typing import List, Dict

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# ANSI colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


async def check_prerequisites(conn: asyncpg.Connection) -> tuple[bool, List[str]]:
    """Check if all prerequisite tables exist"""
    issues = []

    # Check required tables exist (note: actual table is 'quotes', not 'quotations')
    required_tables = ['documents', 'quotes', 'customers', 'users']

    for table in required_tables:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = $1
            )
        """, table)

        if not exists:
            issues.append(f"Required table '{table}' does not exist")

    # NOTE: update_updated_at_column() function is NOW CREATED by the migration
    # No need to check for it as a prerequisite

    return (len(issues) == 0, issues)


async def check_tables_dont_exist(conn: asyncpg.Connection) -> tuple[bool, List[str]]:
    """Check that migration tables don't already exist"""
    issues = []

    tables_to_create = ['email_quotation_requests', 'email_attachments']

    for table in tables_to_create:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = $1
            )
        """, table)

        if exists:
            issues.append(f"Table '{table}' already exists (migration may have been applied)")

    return (len(issues) == 0, issues)


async def validate_migration_syntax():
    """Basic syntax validation of migration file"""
    migration_file = "migrations/0006_add_email_quotation_tables.sql"

    if not os.path.exists(migration_file):
        print(f"{RED}✗ Migration file not found: {migration_file}{RESET}")
        return False

    # Read and check for basic SQL syntax issues
    with open(migration_file, 'r') as f:
        content = f.read()

    # Check for required sections
    required_sections = [
        'CREATE TABLE IF NOT EXISTS email_quotation_requests',
        'CREATE TABLE IF NOT EXISTS email_attachments',
        'BEGIN;',
        'COMMIT;'
    ]

    issues = []
    for section in required_sections:
        if section not in content:
            issues.append(f"Missing required section: {section}")

    if issues:
        for issue in issues:
            print(f"{RED}✗ {issue}{RESET}")
        return False

    print(f"{GREEN}✓ Migration file syntax looks correct{RESET}")
    return True


async def validate_column_types(conn: asyncpg.Connection):
    """
    Validate that column types in migration match what code expects
    This would run AFTER migration is applied
    """
    expected_columns = {
        'email_quotation_requests': {
            'id': 'integer',
            'message_id': 'character varying',
            'sender_email': 'character varying',
            'sender_name': 'character varying',
            'subject': 'character varying',
            'received_date': 'timestamp with time zone',
            'body_text': 'text',
            'body_html': 'text',
            'has_attachments': 'boolean',
            'attachment_count': 'integer',
            'status': 'character varying',
            'extracted_requirements': 'jsonb',
            'ai_confidence_score': 'numeric',
            'extracted_at': 'timestamp with time zone',
            'document_id': 'integer',
            'quotation_id': 'integer',
            'customer_id': 'integer',
            'processing_notes': 'text',
            'error_message': 'text',
            'processed_by': 'integer',
            'created_at': 'timestamp with time zone',
            'updated_at': 'timestamp with time zone'
        },
        'email_attachments': {
            'id': 'integer',
            'email_request_id': 'integer',
            'filename': 'character varying',
            'file_path': 'character varying',
            'file_size': 'integer',
            'mime_type': 'character varying',
            'processed': 'boolean',
            'processing_status': 'character varying',
            'processing_error': 'text',
            'document_id': 'integer',
            'created_at': 'timestamp with time zone'
        }
    }

    issues = []

    for table_name, expected_cols in expected_columns.items():
        # Check if table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = $1
            )
        """, table_name)

        if not table_exists:
            print(f"{YELLOW}⊘ Table '{table_name}' not created yet (skipping column validation){RESET}")
            continue

        # Get actual columns
        rows = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = $1
        """, table_name)

        actual_cols = {row['column_name']: row['data_type'] for row in rows}

        # Check each expected column
        for col_name, expected_type in expected_cols.items():
            if col_name not in actual_cols:
                issues.append(f"Table '{table_name}': Missing column '{col_name}'")
            elif not actual_cols[col_name].startswith(expected_type):
                issues.append(
                    f"Table '{table_name}': Column '{col_name}' type mismatch "
                    f"(expected '{expected_type}', got '{actual_cols[col_name]}')"
                )

    if issues:
        for issue in issues:
            print(f"{RED}✗ {issue}{RESET}")
        return False

    print(f"{GREEN}✓ All column types match expectations{RESET}")
    return True


async def main():
    """Main validation workflow"""
    print("=" * 70)
    print("DATABASE MIGRATION VALIDATION")
    print("Migration: 0006_add_email_quotation_tables.sql")
    print("=" * 70)
    print()

    # Step 1: Validate migration file syntax
    print("Step 1: Validating migration file syntax...")
    if not await validate_migration_syntax():
        print(f"\n{RED}✗ Migration validation FAILED{RESET}")
        return 1
    print()

    # Step 2: Connect to database
    print("Step 2: Connecting to database...")
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print(f"{RED}✗ DATABASE_URL environment variable not set{RESET}")
        print("  Set it to: postgresql://horme_user:password@localhost:5433/horme_db")
        return 1

    try:
        conn = await asyncpg.connect(database_url)
        print(f"{GREEN}✓ Connected to database{RESET}")
    except Exception as e:
        print(f"{RED}✗ Database connection failed: {e}{RESET}")
        return 1

    print()

    try:
        # Step 3: Check prerequisites
        print("Step 3: Checking prerequisite tables and functions...")
        prereqs_ok, issues = await check_prerequisites(conn)

        if not prereqs_ok:
            print(f"{RED}✗ Prerequisites check FAILED:{RESET}")
            for issue in issues:
                print(f"  - {issue}")
            print()
            print(f"{YELLOW}Note: These tables/functions must exist before migration can be applied{RESET}")
            return 1

        print(f"{GREEN}✓ All prerequisites exist{RESET}")
        print()

        # Step 4: Check if migration already applied
        print("Step 4: Checking if migration already applied...")
        tables_ok, issues = await check_tables_dont_exist(conn)

        if not tables_ok:
            print(f"{YELLOW}⊘ Migration may already be applied:{RESET}")
            for issue in issues:
                print(f"  - {issue}")
            print()

            # Validate column types if tables exist
            print("Step 5: Validating existing table schemas...")
            if await validate_column_types(conn):
                print()
                print(f"{GREEN}✓ Migration appears to be correctly applied{RESET}")
                print(f"{GREEN}✓ All validations PASSED{RESET}")
                return 0
            else:
                print()
                print(f"{RED}✗ Table schemas don't match expectations{RESET}")
                print(f"{YELLOW}  You may need to drop and recreate the tables{RESET}")
                return 1

        print(f"{GREEN}✓ Migration has not been applied yet{RESET}")
        print()

        # Step 5: Summary
        print("=" * 70)
        print(f"{GREEN}✓ VALIDATION PASSED{RESET}")
        print()
        print("Migration can be safely applied with:")
        print(f"  {YELLOW}docker exec horme-postgres psql -U horme_user -d horme_db \\{RESET}")
        print(f"  {YELLOW}    -f /app/migrations/0006_add_email_quotation_tables.sql{RESET}")
        print("=" * 70)

        return 0

    finally:
        await conn.close()


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
