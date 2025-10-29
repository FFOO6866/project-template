#!/usr/bin/env python3
"""
DataFlow Schema Migration Script
Migrates existing PostgreSQL schema to match production_models.py using DataFlow auto-migration

Strategy: Use DataFlow auto-migration to create all 21+ tables with proper structure
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.production_models import db
from dataflow.migrations import AutoMigrationSystem


async def check_current_schema():
    """Check current database schema"""
    print("=" * 80)
    print("STEP 1: Current Database Schema Analysis")
    print("=" * 80)

    # Initialize DataFlow connection
    await db.initialize()

    # Get connection details
    print(f"\nDatabase URL: {db.database_url}")
    print(f"Database Type: {db.dialect}")

    # Check existing tables
    async with db.pool.acquire() as conn:
        result = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'dataflow'
            ORDER BY tablename
        """)

        existing_tables = [r['tablename'] for r in result]
        print(f"\nExisting Tables ({len(existing_tables)}):")
        for table in existing_tables:
            print(f"  - {table}")

        # Check table structures
        print("\nExisting Table Structures:")
        for table in existing_tables:
            columns = await conn.fetch(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'dataflow' AND table_name = '{table}'
                ORDER BY ordinal_position
            """)
            print(f"\n  {table}:")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"    - {col['column_name']}: {col['data_type']} {nullable}")

    return existing_tables


async def generate_target_schema():
    """Generate target schema from production_models.py"""
    print("\n" + "=" * 80)
    print("STEP 2: Target Schema from production_models.py")
    print("=" * 80)

    # Get all registered models
    models = db._models
    print(f"\nRegistered Models ({len(models)}):")
    for model_name in sorted(models.keys()):
        print(f"  - {model_name}")

    # Get expected table names
    expected_tables = []
    for model_name, model_class in models.items():
        table_name = getattr(model_class, '__dataflow__', {}).get('table_name', model_name.lower())
        expected_tables.append(table_name)

    print(f"\nExpected Tables ({len(expected_tables)}):")
    for table in sorted(expected_tables):
        print(f"  - {table}")

    return expected_tables


async def analyze_migration_needs(existing_tables, expected_tables):
    """Analyze what migration operations are needed"""
    print("\n" + "=" * 80)
    print("STEP 3: Migration Analysis")
    print("=" * 80)

    existing_set = set(existing_tables)
    expected_set = set(expected_tables)

    # Tables to create
    to_create = expected_set - existing_set
    print(f"\nTables to CREATE ({len(to_create)}):")
    for table in sorted(to_create):
        print(f"  + {table}")

    # Tables to drop (old schema)
    to_drop = existing_set - expected_set
    print(f"\nTables to DROP ({len(to_drop)}):")
    for table in sorted(to_drop):
        print(f"  - {table}")

    # Tables that exist but may need modification
    to_modify = existing_set & expected_set
    print(f"\nTables to potentially MODIFY ({len(to_modify)}):")
    for table in sorted(to_modify):
        print(f"  ~ {table}")

    return {
        'to_create': to_create,
        'to_drop': to_drop,
        'to_modify': to_modify
    }


async def backup_existing_data():
    """Backup existing data before migration"""
    print("\n" + "=" * 80)
    print("STEP 4: Data Backup")
    print("=" * 80)

    backup_dir = Path(__file__).parent.parent / "backups" / "dataflow"
    backup_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"dataflow_backup_{timestamp}.sql"

    print(f"\nCreating backup: {backup_file}")

    # Use pg_dump to backup dataflow schema
    import subprocess
    db_url = os.getenv("DATABASE_URL", "postgresql://horme_user:horme_password@localhost:5433/horme_db")

    # Parse connection string
    from urllib.parse import urlparse
    parsed = urlparse(db_url)

    dump_cmd = [
        "docker", "exec", "horme-postgres",
        "pg_dump",
        "-U", parsed.username,
        "-d", parsed.path.lstrip("/"),
        "-n", "dataflow",  # Only dataflow schema
        "-f", f"/tmp/backup_{timestamp}.sql"
    ]

    try:
        result = subprocess.run(dump_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✓ Backup created successfully")

            # Copy from container to host
            copy_cmd = [
                "docker", "cp",
                f"horme-postgres:/tmp/backup_{timestamp}.sql",
                str(backup_file)
            ]
            subprocess.run(copy_cmd, check=True)
            print(f"✓ Backup saved to: {backup_file}")
        else:
            print(f"⚠ Backup warning: {result.stderr}")
    except Exception as e:
        print(f"⚠ Backup failed: {e}")
        print("  Continuing with migration (development environment)")


async def run_auto_migration(dry_run=True):
    """Run DataFlow auto-migration"""
    print("\n" + "=" * 80)
    print(f"STEP 5: DataFlow Auto-Migration (DRY_RUN={dry_run})")
    print("=" * 80)

    try:
        # Initialize auto-migration system
        migration_system = AutoMigrationSystem(
            connection=db.pool,
            dialect="postgresql",
            migrations_dir="migrations/dataflow"
        )

        # Get target schema from models
        target_schema = {}
        for model_name, model_class in db._models.items():
            # DataFlow internally converts models to TableDefinition
            # We'll let auto_migrate detect the schema from the models
            pass

        print("\nRunning auto-migration analysis...")
        print(f"  Dry Run: {dry_run}")
        print(f"  Interactive: False")

        # Run auto-migration
        success, migrations = await migration_system.auto_migrate(
            target_schema=target_schema,
            dry_run=dry_run,
            interactive=False,
            auto_confirm=not dry_run,
            max_risk_level="MEDIUM" if not dry_run else None
        )

        print(f"\nAuto-migration completed: {success}")
        print(f"Migrations generated: {len(migrations)}")

        if migrations:
            for migration in migrations:
                print(f"\n  Migration: {migration.name}")
                print(f"  Version: {migration.version}")
                print(f"  Operations: {len(migration.operations)}")
                print(f"  Status: {migration.status}")

                for op in migration.operations:
                    print(f"    - {op.operation_type}: {op.description}")

        return success, migrations

    except Exception as e:
        print(f"\n❌ Auto-migration error: {e}")
        import traceback
        traceback.print_exc()
        return False, []


async def manual_migration_fallback():
    """Manual migration if auto-migration not available"""
    print("\n" + "=" * 80)
    print("STEP 5: Manual Migration (Auto-migration not available)")
    print("=" * 80)

    print("\nDataFlow auto-migration requires full DataFlow SDK")
    print("Falling back to manual schema creation...")

    async with db.pool.acquire() as conn:
        # Drop old tables first
        print("\nDropping old tables...")
        await conn.execute("DROP TABLE IF EXISTS dataflow.product_enrichment CASCADE")
        await conn.execute("DROP TABLE IF EXISTS dataflow.product_suppliers CASCADE")
        await conn.execute("DROP TABLE IF EXISTS dataflow.quotations CASCADE")
        await conn.execute("DROP TABLE IF EXISTS dataflow.products CASCADE")
        await conn.execute("DROP TABLE IF EXISTS dataflow.suppliers CASCADE")
        print("✓ Old tables dropped")

        # Initialize DataFlow models - this will create tables
        print("\nInitializing DataFlow models...")
        await db.initialize()
        print("✓ DataFlow initialized")

        # DataFlow should auto-create tables from models
        print("\nWaiting for table creation...")
        await asyncio.sleep(2)

        # Verify tables created
        result = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'dataflow'
            ORDER BY tablename
        """)

        new_tables = [r['tablename'] for r in result]
        print(f"\nTables created ({len(new_tables)}):")
        for table in new_tables:
            print(f"  + {table}")

        return len(new_tables) > 0


async def verify_migration():
    """Verify migration succeeded"""
    print("\n" + "=" * 80)
    print("STEP 6: Migration Verification")
    print("=" * 80)

    async with db.pool.acquire() as conn:
        # Count tables
        result = await conn.fetch("""
            SELECT COUNT(*) as count
            FROM pg_tables
            WHERE schemaname = 'dataflow'
        """)
        table_count = result[0]['count']

        # List all tables
        result = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'dataflow'
            ORDER BY tablename
        """)
        tables = [r['tablename'] for r in result]

        print(f"\nTotal Tables: {table_count}")
        print("\nAll Tables:")
        for table in tables:
            # Get column count
            col_result = await conn.fetch(f"""
                SELECT COUNT(*) as count
                FROM information_schema.columns
                WHERE table_schema = 'dataflow' AND table_name = '{table}'
            """)
            col_count = col_result[0]['count']
            print(f"  ✓ {table} ({col_count} columns)")

        # Check for expected models
        expected_models = [
            'category', 'brand', 'supplier', 'product',
            'productpricing', 'productspecification', 'productinventory',
            'workrecommendation', 'rfpdocument', 'quotation', 'quotationitem',
            'customer', 'activitylog', 'oshastandard', 'ansistandard',
            'toolriskclassification', 'taskhazardmapping', 'ansiequipmentspecification',
            'unspsccode', 'etimclass', 'productclassification'
        ]

        missing_models = []
        for model in expected_models:
            if model not in tables:
                missing_models.append(model)

        if missing_models:
            print(f"\n⚠ Missing Models ({len(missing_models)}):")
            for model in missing_models:
                print(f"  - {model}")
        else:
            print("\n✓ All expected models present!")

        return table_count >= 21 and not missing_models


async def main():
    """Main migration orchestration"""
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "DataFlow Schema Migration" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")

    try:
        # Step 1: Check current schema
        existing_tables = await check_current_schema()

        # Step 2: Generate target schema
        expected_tables = await generate_target_schema()

        # Step 3: Analyze migration needs
        migration_analysis = await analyze_migration_needs(existing_tables, expected_tables)

        # Step 4: Backup existing data
        await backup_existing_data()

        # Step 5: Run migration (try auto-migration first)
        try:
            success, migrations = await run_auto_migration(dry_run=True)

            if success and migrations:
                print("\n" + "=" * 80)
                print("Review migration plan above. Apply migration? [y/N]: ", end="")
                response = input().strip().lower()

                if response == 'y':
                    success, migrations = await run_auto_migration(dry_run=False)
                else:
                    print("Migration cancelled by user")
                    return 1
            else:
                # Fallback to manual migration
                success = await manual_migration_fallback()

        except (ImportError, AttributeError) as e:
            print(f"\nAuto-migration not available: {e}")
            success = await manual_migration_fallback()

        # Step 6: Verify migration
        if success:
            verified = await verify_migration()

            if verified:
                print("\n" + "=" * 80)
                print("✓ MIGRATION SUCCESSFUL")
                print("=" * 80)
                print("\nNext steps:")
                print("  1. Test application connectivity")
                print("  2. Load initial data if needed")
                print("  3. Run application tests")
                return 0
            else:
                print("\n" + "=" * 80)
                print("⚠ MIGRATION INCOMPLETE")
                print("=" * 80)
                return 1
        else:
            print("\n" + "=" * 80)
            print("❌ MIGRATION FAILED")
            print("=" * 80)
            return 1

    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        await db.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
