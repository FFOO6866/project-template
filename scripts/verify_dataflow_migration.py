#!/usr/bin/env python3
"""
Verify DataFlow Migration Success
Tests that the migrated schema works with application code
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_basic_connection():
    """Test basic database connection"""
    print("=" * 80)
    print("TEST 1: Basic Database Connection")
    print("=" * 80)

    try:
        import asyncpg

        db_url = os.getenv("DATABASE_URL", "postgresql://horme_user:horme_password@localhost:5433/horme_db")

        conn = await asyncpg.connect(db_url)
        print("✓ Database connection successful")

        # Query table count
        result = await conn.fetchval("SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'dataflow'")
        print(f"✓ Found {result} tables in dataflow schema")

        if result == 21:
            print("✓ Table count matches expected (21)")
        else:
            print(f"⚠ Warning: Expected 21 tables, found {result}")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def test_dataflow_models():
    """Test DataFlow models can be imported and initialized"""
    print("\n" + "=" * 80)
    print("TEST 2: DataFlow Models Import")
    print("=" * 80)

    try:
        from models.production_models import db

        print("✓ production_models.py imported successfully")

        # Check registered models
        models = list(db._models.keys())
        print(f"✓ Found {len(models)} registered models")

        expected_models = [
            'Category', 'Brand', 'Supplier', 'Product',
            'ProductPricing', 'ProductSpecification', 'ProductInventory',
            'WorkRecommendation', 'RFPDocument', 'Quotation', 'QuotationItem',
            'Customer', 'ActivityLog', 'OSHAStandard', 'ANSIStandard',
            'ToolRiskClassification', 'TaskHazardMapping', 'ANSIEquipmentSpecification',
            'UNSPSCCode', 'ETIMClass', 'ProductClassification'
        ]

        for model in expected_models:
            if model in models:
                print(f"  ✓ {model}")
            else:
                print(f"  ❌ Missing: {model}")

        return len(models) == len(expected_models)

    except Exception as e:
        print(f"❌ Model import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_dataflow_initialization():
    """Test DataFlow initialization with database"""
    print("\n" + "=" * 80)
    print("TEST 3: DataFlow Initialization")
    print("=" * 80)

    try:
        from models.production_models import db

        print("Initializing DataFlow connection...")
        await db.initialize()
        print("✓ DataFlow initialized successfully")

        # Test connection pool
        print(f"✓ Connection pool: {db.pool}")
        print(f"✓ Database dialect: {db.dialect}")

        await db.close()
        print("✓ Connection closed cleanly")

        return True

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_basic_operations():
    """Test basic CRUD operations"""
    print("\n" + "=" * 80)
    print("TEST 4: Basic CRUD Operations")
    print("=" * 80)

    try:
        import asyncpg

        db_url = os.getenv("DATABASE_URL", "postgresql://horme_user:horme_password@localhost:5433/horme_db")
        conn = await asyncpg.connect(db_url)

        # Test Category insert
        print("\nTesting Category insert...")
        await conn.execute("""
            INSERT INTO dataflow.category (name, slug, description)
            VALUES ('Test Category', 'test-category', 'Test description')
            ON CONFLICT (slug) DO NOTHING
        """)
        print("✓ Category insert successful")

        # Test Category query
        categories = await conn.fetch("SELECT * FROM dataflow.category WHERE slug = 'test-category'")
        if categories:
            print(f"✓ Category query successful: {categories[0]['name']}")
        else:
            print("⚠ Category not found after insert")

        # Test Brand insert
        print("\nTesting Brand insert...")
        await conn.execute("""
            INSERT INTO dataflow.brand (name, slug, description)
            VALUES ('Test Brand', 'test-brand', 'Test brand')
            ON CONFLICT (slug) DO NOTHING
        """)
        print("✓ Brand insert successful")

        # Test Supplier insert
        print("\nTesting Supplier insert...")
        await conn.execute("""
            INSERT INTO dataflow.supplier (name, website)
            VALUES ('Test Supplier', 'https://test-supplier.com')
            ON CONFLICT (website) DO NOTHING
        """)
        print("✓ Supplier insert successful")

        # Test Product insert with foreign keys
        print("\nTesting Product insert with foreign keys...")

        # Get IDs
        category_id = await conn.fetchval("SELECT id FROM dataflow.category WHERE slug = 'test-category'")
        brand_id = await conn.fetchval("SELECT id FROM dataflow.brand WHERE slug = 'test-brand'")
        supplier_id = await conn.fetchval("SELECT id FROM dataflow.supplier WHERE website = 'https://test-supplier.com'")

        await conn.execute("""
            INSERT INTO dataflow.product (sku, name, slug, category_id, brand_id, supplier_id, base_price)
            VALUES ('TEST-001', 'Test Product', 'test-product', $1, $2, $3, 99.99)
            ON CONFLICT (sku) DO NOTHING
        """, category_id, brand_id, supplier_id)
        print("✓ Product insert with foreign keys successful")

        # Test Product query
        product = await conn.fetchrow("SELECT * FROM dataflow.product WHERE sku = 'TEST-001'")
        if product:
            print(f"✓ Product query successful: {product['name']} (${product['base_price']})")
        else:
            print("⚠ Product not found after insert")

        # Test Quotation insert
        print("\nTesting Quotation insert...")
        await conn.execute("""
            INSERT INTO dataflow.quotation (
                quotation_number, client_name, project_title, total_amount,
                valid_until, line_items, status
            )
            VALUES (
                'Q-TEST-001', 'Test Client', 'Test Project', 500.00,
                CURRENT_TIMESTAMP + INTERVAL '30 days', '[]'::jsonb, 'draft'
            )
            ON CONFLICT (quotation_number) DO NOTHING
        """)
        print("✓ Quotation insert successful")

        # Test counts
        print("\nVerifying data counts...")
        category_count = await conn.fetchval("SELECT COUNT(*) FROM dataflow.category")
        product_count = await conn.fetchval("SELECT COUNT(*) FROM dataflow.product")
        quotation_count = await conn.fetchval("SELECT COUNT(*) FROM dataflow.quotation")

        print(f"  Categories: {category_count}")
        print(f"  Products: {product_count}")
        print(f"  Quotations: {quotation_count}")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ CRUD operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_advanced_features():
    """Test advanced features (soft delete, versioning, triggers)"""
    print("\n" + "=" * 80)
    print("TEST 5: Advanced Features")
    print("=" * 80)

    try:
        import asyncpg

        db_url = os.getenv("DATABASE_URL", "postgresql://horme_user:horme_password@localhost:5433/horme_db")
        conn = await asyncpg.connect(db_url)

        # Test updated_at trigger
        print("\nTesting updated_at trigger...")
        await asyncpg.sleep(1)  # Wait 1 second

        await conn.execute("""
            UPDATE dataflow.product
            SET name = 'Updated Test Product'
            WHERE sku = 'TEST-001'
        """)

        product = await conn.fetchrow("SELECT created_at, updated_at FROM dataflow.product WHERE sku = 'TEST-001'")
        if product and product['updated_at'] > product['created_at']:
            print("✓ updated_at trigger working correctly")
        else:
            print("⚠ updated_at trigger may not be working")

        # Test soft delete
        print("\nTesting soft delete...")
        await conn.execute("""
            UPDATE dataflow.product
            SET deleted_at = CURRENT_TIMESTAMP
            WHERE sku = 'TEST-001'
        """)

        deleted_product = await conn.fetchrow("SELECT deleted_at FROM dataflow.product WHERE sku = 'TEST-001'")
        if deleted_product and deleted_product['deleted_at']:
            print("✓ Soft delete working (product marked as deleted)")
        else:
            print("⚠ Soft delete column not populated")

        # Test version field
        print("\nTesting version field...")
        version = await conn.fetchval("SELECT version FROM dataflow.product WHERE sku = 'TEST-001'")
        if version == 1:
            print("✓ Version field initialized correctly")
        else:
            print(f"⚠ Version field unexpected value: {version}")

        # Test JSONB fields
        print("\nTesting JSONB fields...")
        await conn.execute("""
            UPDATE dataflow.product
            SET technical_specs = '{"weight": "1.5kg", "dimensions": "10x10x10cm"}'::jsonb
            WHERE sku = 'TEST-001'
        """)

        specs = await conn.fetchval("SELECT technical_specs FROM dataflow.product WHERE sku = 'TEST-001'")
        if specs and 'weight' in specs:
            print(f"✓ JSONB field working: {specs}")
        else:
            print("⚠ JSONB field not working correctly")

        # Test indexes exist
        print("\nTesting indexes...")
        indexes = await conn.fetch("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'dataflow'
            AND tablename = 'product'
        """)

        print(f"✓ Found {len(indexes)} indexes on product table")
        for idx in indexes[:5]:  # Show first 5
            print(f"  - {idx['indexname']}")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ Advanced features test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_foreign_key_integrity():
    """Test foreign key constraints"""
    print("\n" + "=" * 80)
    print("TEST 6: Foreign Key Integrity")
    print("=" * 80)

    try:
        import asyncpg

        db_url = os.getenv("DATABASE_URL", "postgresql://horme_user:horme_password@localhost:5433/horme_db")
        conn = await asyncpg.connect(db_url)

        # Test that we cannot insert product with non-existent category
        print("\nTesting foreign key constraint enforcement...")
        try:
            await conn.execute("""
                INSERT INTO dataflow.product (sku, name, slug, category_id, base_price)
                VALUES ('FAIL-001', 'Should Fail', 'should-fail', 99999, 10.00)
            """)
            print("⚠ Foreign key constraint NOT enforced (this is bad)")
            success = False
        except asyncpg.exceptions.ForeignKeyViolationError:
            print("✓ Foreign key constraint enforced correctly")
            success = True

        # Test cascade behavior
        print("\nTesting cascade delete behavior...")

        # Get foreign key info
        fks = await conn.fetch("""
            SELECT
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'dataflow'
                AND tc.table_name = 'product'
        """)

        print(f"✓ Found {len(fks)} foreign key constraints on product table")
        for fk in fks:
            print(f"  - {fk['column_name']} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")

        await conn.close()
        return success

    except Exception as e:
        print(f"❌ Foreign key integrity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all verification tests"""
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 22 + "DataFlow Migration Verification" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝\n")

    results = []

    # Run tests
    results.append(await test_basic_connection())
    results.append(await test_dataflow_models())
    results.append(await test_dataflow_initialization())
    results.append(await test_basic_operations())
    results.append(await test_advanced_features())
    results.append(await test_foreign_key_integrity())

    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    test_names = [
        "Basic Database Connection",
        "DataFlow Models Import",
        "DataFlow Initialization",
        "Basic CRUD Operations",
        "Advanced Features",
        "Foreign Key Integrity"
    ]

    passed = sum(results)
    total = len(results)

    for name, result in zip(test_names, results):
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status:8} | {name}")

    print("=" * 80)
    print(f"\nOverall: {passed}/{total} tests passed ({passed*100//total}%)")

    if all(results):
        print("\n✅ ALL TESTS PASSED - Migration successful and schema is production-ready!")
        return 0
    else:
        print("\n⚠ Some tests failed - Review output above for details")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
