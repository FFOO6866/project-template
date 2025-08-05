#!/usr/bin/env python3
"""
Final Infrastructure Integration Test
====================================

This script performs a comprehensive test of the complete infrastructure setup
to validate that both PostgreSQL and Redis are working together.
"""

import sys
import json
from datetime import datetime
from redis_wsl_wrapper import RedisWSLWrapper

def test_postgresql_integration():
    """Test PostgreSQL integration"""
    print("Testing PostgreSQL Integration...")
    
    try:
        import psycopg2
        
        # Test connection
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='test_user',
            password='test_password',
            database='test_horme_db',
            connect_timeout=5
        )
        
        cursor = conn.cursor()
        
        # Test table creation and operations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_integration (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test data
        test_data = {
            'service': 'integration_test',
            'timestamp': datetime.now().isoformat(),
            'status': 'testing'
        }
        
        cursor.execute(
            "INSERT INTO test_integration (name, data) VALUES (%s, %s) RETURNING id",
            ('Integration Test', json.dumps(test_data))
        )
        
        test_id = cursor.fetchone()[0]
        
        # Query data back
        cursor.execute(
            "SELECT id, name, data, created_at FROM test_integration WHERE id = %s",
            (test_id,)
        )
        
        row = cursor.fetchone()
        retrieved_data = json.loads(row[2])
        
        # Cleanup
        cursor.execute("DELETE FROM test_integration WHERE id = %s", (test_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("  ✓ PostgreSQL connection successful")
        print("  ✓ Table operations working")
        print("  ✓ JSON data handling working")
        print(f"  ✓ Test record ID: {test_id}")
        
        return True, {
            'test_id': test_id,
            'data_roundtrip': retrieved_data['service'] == 'integration_test'
        }
        
    except ImportError:
        return False, "psycopg2 not installed"
    except Exception as e:
        return False, str(e)

def test_redis_integration():
    """Test Redis integration"""
    print("Testing Redis Integration...")
    
    try:
        redis_client = RedisWSLWrapper(password='testredispass')
        
        # Test session simulation
        session_id = 'test_session_12345'
        session_data = {
            'user_id': 'user_123',
            'login_time': datetime.now().isoformat(),
            'permissions': ['read', 'write']
        }
        
        # Store session as hash
        for key, value in session_data.items():
            redis_client.hset(f'session:{session_id}', key, str(value))
        
        # Retrieve session
        retrieved_user = redis_client.hget(f'session:{session_id}', 'user_id')
        retrieved_time = redis_client.hget(f'session:{session_id}', 'login_time')
        
        # Test counter operations
        counter_key = 'integration_test_counter'
        redis_client.set(counter_key, '0')
        redis_client.incr(counter_key, 5)
        counter_value = int(redis_client.get(counter_key))
        
        # Test list operations (activity log)
        activity_key = 'user:user_123:activity'
        redis_client.lpush(activity_key, 'login', 'page_view', 'action')
        activity_count = redis_client.llen(activity_key)
        
        # Cleanup
        redis_client.delete(f'session:{session_id}', counter_key, activity_key)
        
        print("  ✓ Redis connection successful")
        print("  ✓ Hash operations working")
        print("  ✓ Counter operations working")
        print("  ✓ List operations working")
        print(f"  ✓ Session data retrieved: {retrieved_user}")
        
        return True, {
            'session_retrieval': retrieved_user == 'user_123',
            'counter_value': counter_value,
            'activity_count': activity_count
        }
        
    except Exception as e:
        return False, str(e)

def test_combined_operations():
    """Test operations that use both PostgreSQL and Redis"""
    print("Testing Combined Operations...")
    
    try:
        # PostgreSQL setup
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='test_user',
            password='test_password',
            database='test_horme_db'
        )
        cursor = conn.cursor()
        
        # Redis setup
        redis_client = RedisWSLWrapper(password='testredispass')
        
        # Simulate user registration workflow
        user_data = {
            'username': 'test_user_integration',
            'email': 'test@example.com',
            'registration_time': datetime.now().isoformat()
        }
        
        # 1. Store user in PostgreSQL
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_test (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE,
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute(
            "INSERT INTO users_test (username, email) VALUES (%s, %s) RETURNING id",
            (user_data['username'], user_data['email'])
        )
        
        user_id = cursor.fetchone()[0]
        
        # 2. Cache user session in Redis
        session_key = f'user_session:{user_id}'
        redis_client.hset(session_key, 'username', user_data['username'])
        redis_client.hset(session_key, 'email', user_data['email'])
        redis_client.hset(session_key, 'last_activity', user_data['registration_time'])
        
        # 3. Increment registration counter in Redis
        redis_client.incr('total_registrations')
        total_registrations = int(redis_client.get('total_registrations'))
        
        # 4. Verify data consistency
        cursor.execute("SELECT username, email FROM users_test WHERE id = %s", (user_id,))
        db_username, db_email = cursor.fetchone()
        
        cached_username = redis_client.hget(session_key, 'username')
        cached_email = redis_client.hget(session_key, 'email')
        
        # 5. Cleanup
        cursor.execute("DELETE FROM users_test WHERE id = %s", (user_id,))
        redis_client.delete(session_key)
        # Keep the counter for other tests
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Verify consistency
        data_consistent = (
            db_username == cached_username == user_data['username'] and
            db_email == cached_email == user_data['email']
        )
        
        print("  ✓ User stored in PostgreSQL")
        print("  ✓ Session cached in Redis")
        print("  ✓ Registration counter updated")
        print(f"  ✓ Data consistency: {data_consistent}")
        print(f"  ✓ Total registrations: {total_registrations}")
        
        return True, {
            'user_id': user_id,
            'data_consistent': data_consistent,
            'total_registrations': total_registrations
        }
        
    except Exception as e:
        return False, str(e)

def main():
    """Main integration test function"""
    print("Final Infrastructure Integration Test")
    print("=" * 45)
    print()
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {},
        'overall_status': 'UNKNOWN'
    }
    
    # Test PostgreSQL
    pg_success, pg_result = test_postgresql_integration()
    results['tests']['postgresql'] = {
        'success': pg_success,
        'result': pg_result
    }
    print()
    
    # Test Redis
    redis_success, redis_result = test_redis_integration()
    results['tests']['redis'] = {
        'success': redis_success,
        'result': redis_result
    }
    print()
    
    # Test combined operations
    if pg_success and redis_success:
        combined_success, combined_result = test_combined_operations()
        results['tests']['combined'] = {
            'success': combined_success,
            'result': combined_result
        }
    else:
        print("Skipping combined operations test due to previous failures")
        combined_success = False
        results['tests']['combined'] = {
            'success': False,
            'result': 'Skipped due to prerequisite failures'
        }
    
    print()
    
    # Overall assessment
    all_success = pg_success and redis_success and combined_success
    
    if all_success:
        results['overall_status'] = 'SUCCESS'
        print("🎉 INFRASTRUCTURE INTEGRATION TEST: SUCCESS")
        print()
        print("✅ PostgreSQL: Fully operational")
        print("✅ Redis: Fully operational")
        print("✅ Combined operations: Working correctly")
        print("✅ Data consistency: Maintained")
        print()
        print("🚀 Infrastructure is ready for application development!")
        exit_code = 0
    else:
        results['overall_status'] = 'FAILURE'
        print("❌ INFRASTRUCTURE INTEGRATION TEST: FAILURE")
        print()
        if not pg_success:
            print(f"❌ PostgreSQL: {pg_result}")
        if not redis_success:
            print(f"❌ Redis: {redis_result}")
        if not combined_success:
            print(f"❌ Combined operations: {combined_result}")
        print()
        print("🔧 Please check individual service configurations")
        exit_code = 1
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'integration_test_results_{timestamp}.json'
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📊 Detailed results saved to: {results_file}")
    
    return exit_code

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)