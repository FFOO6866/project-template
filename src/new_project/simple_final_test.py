#!/usr/bin/env python3
"""
Simple Final Infrastructure Test
===============================

Basic test to confirm both services are working.
"""

import sys

def test_postgresql():
    """Test PostgreSQL"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='test_user',
            password='test_password',
            database='test_horme_db',
            connect_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, f"PostgreSQL working: {version[:30]}..."
    except Exception as e:
        return False, f"PostgreSQL failed: {str(e)}"

def test_redis():
    """Test Redis"""
    try:
        from redis_wsl_wrapper import RedisWSLWrapper
        redis_client = RedisWSLWrapper(password='testredispass')
        redis_client.set('final_test', 'success')
        value = redis_client.get('final_test')
        redis_client.delete('final_test')
        
        if value == 'success':
            info = redis_client.info('server')
            version = info.get('redis_version', 'unknown')
            return True, f"Redis working: version {version}"
        else:
            return False, "Redis test operation failed"
    except Exception as e:
        return False, f"Redis failed: {str(e)}"

def main():
    """Main test function"""
    print("Final Infrastructure Test")
    print("=" * 30)
    
    # Test PostgreSQL
    print("Testing PostgreSQL ... ", end="")
    pg_success, pg_msg = test_postgresql()
    print("PASS" if pg_success else "FAIL")
    if not pg_success:
        print(f"  Error: {pg_msg}")
    
    # Test Redis
    print("Testing Redis ... ", end="")
    redis_success, redis_msg = test_redis()
    print("PASS" if redis_success else "FAIL")
    if not redis_success:
        print(f"  Error: {redis_msg}")
    
    # Summary
    print("\n" + "=" * 30)
    if pg_success and redis_success:
        print("OVERALL STATUS: SUCCESS")
        print("Both PostgreSQL and Redis are operational!")
        print("\nServices ready for:")
        print("- Application development")
        print("- Database operations")
        print("- Caching and session management")
        return 0
    else:
        print("OVERALL STATUS: FAILURE")
        if not pg_success:
            print(f"PostgreSQL issue: {pg_msg}")
        if not redis_success:
            print(f"Redis issue: {redis_msg}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Test error: {str(e)}")
        sys.exit(1)