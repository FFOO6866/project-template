#!/usr/bin/env python3
"""
Simple DataFlow Test
===================

Test what DataFlow functionality is actually available.
"""

def test_dataflow_direct():
    print("Testing DataFlow direct import...")
    
    try:
        from dataflow import DataFlow
        print("✅ DataFlow import successful")
        
        # Test creating instance
        db = DataFlow(':memory:')
        print("✅ DataFlow instance created")
        
        # Test model definition
        @db.model
        class TestProduct:
            id: int
            name: str
            price: float
        
        print("✅ Model definition successful")
        print(f"   Model: {TestProduct}")
        
        return True
        
    except Exception as e:
        print(f"❌ DataFlow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_postgresql_install_check():
    print("\nTesting PostgreSQL availability...")
    
    try:
        import psycopg2
        print("✅ psycopg2 driver available")
        
        # Try connecting to different common PostgreSQL setups
        test_configs = [
            {'host': 'localhost', 'port': 5432, 'database': 'postgres', 'user': 'postgres', 'password': 'postgres'},
            {'host': 'localhost', 'port': 5432, 'database': 'postgres', 'user': 'postgres', 'password': ''},
            {'host': 'localhost', 'port': 5432, 'database': 'postgres', 'user': 'postgres', 'password': 'password'},
        ]
        
        for i, config in enumerate(test_configs, 1):
            try:
                conn = psycopg2.connect(**config, connect_timeout=3)
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                cursor.close()
                conn.close()
                
                print(f"✅ PostgreSQL connection successful with config {i}")
                print(f"   Version: {version[0][:50]}...")
                return True, config
                
            except Exception as e:
                print(f"❌ Config {i} failed: {str(e)[:100]}...")
                continue
        
        print("❌ No PostgreSQL connection successful")
        return False, None
        
    except ImportError:
        print("❌ psycopg2 not available")
        print("   Install with: pip install psycopg2-binary")
        return False, None


if __name__ == "__main__":
    print("Simple DataFlow Functionality Test")
    print("=" * 50)
    
    # Test DataFlow
    dataflow_success = test_dataflow_direct()
    
    # Test PostgreSQL
    postgres_success, postgres_config = test_postgresql_install_check()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if dataflow_success:
        print("✅ DataFlow framework is working")
        print("   - Can create models with @db.model decorator")
        print("   - In-memory SQLite database available for testing")
    else:
        print("❌ DataFlow framework has issues")
    
    if postgres_success:
        print("✅ PostgreSQL is available and accessible")
        print(f"   - Connection config: {postgres_config}")
        print("   - Ready for production DataFlow operations")
    else:
        print("❌ PostgreSQL needs to be installed/configured")
        print("   - Install PostgreSQL from postgresql.org")
        print("   - Or use Docker: docker run --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres")
    
    print("\n" + "=" * 50)
    print("NEXT STEPS")
    print("=" * 50)
    
    if dataflow_success and not postgres_success:
        print("1. Install PostgreSQL (see instructions above)")
        print("2. Test DataFlow with PostgreSQL connection")
        print("3. Create simple model and test CRUD operations")
        
    elif dataflow_success and postgres_success:
        print("✅ Ready to test full DataFlow functionality!")
        print("1. Create DataFlow instance with PostgreSQL")  
        print("2. Define a simple model")
        print("3. Test auto-generated CRUD nodes")
        print("4. Verify data persistence")
        
    else:
        print("1. Fix DataFlow installation issues")
        print("2. Install PostgreSQL")
        print("3. Re-run this test")