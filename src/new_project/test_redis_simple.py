#!/usr/bin/env python3
"""
Simple Redis Connection Test
============================

This script tests Redis connection through WSL2.
"""

import sys
import redis
from redis.exceptions import ConnectionError, AuthenticationError

def test_redis_connection():
    """Test Redis connection"""
    print("Testing Redis connection (via WSL2)...")
    
    # Connection configurations to try
    configs = [
        # WSL2 Redis IP (most likely to work)
        {'host': '172.18.66.241', 'port': 6379, 'password': 'testredispass', 'db': 0},
        # Standard localhost attempts
        {'host': 'localhost', 'port': 6379, 'password': 'testredispass', 'db': 0},
        {'host': '127.0.0.1', 'port': 6379, 'password': 'testredispass', 'db': 0},
        # Try without password in case config didn't work
        {'host': '172.18.66.241', 'port': 6379, 'password': None, 'db': 0},
        {'host': 'localhost', 'port': 6379, 'password': None, 'db': 0},
        {'host': '127.0.0.1', 'port': 6379, 'password': None, 'db': 0},
    ]
    
    for i, config in enumerate(configs, 1):
        try:
            print(f"Config {i}: {config['host']}:{config['port']} with {'password' if config['password'] else 'no password'} ... ", end="")
            
            r = redis.Redis(
                host=config['host'],
                port=config['port'],
                password=config['password'],
                db=config['db'],
                socket_connect_timeout=5,
                decode_responses=True
            )
            
            # Test basic operations
            r.ping()
            
            # Test set/get operations
            test_key = 'test_connection_key'
            test_value = 'test_connection_value'
            
            r.set(test_key, test_value)
            retrieved_value = r.get(test_key)
            
            if retrieved_value == test_value:
                # Clean up test key
                r.delete(test_key)
                
                # Get server info
                info = r.info('server')
                redis_version = info.get('redis_version', 'unknown')
                
                print("SUCCESS!")
                print(f"Redis connection successful!")
                print(f"Redis version: {redis_version}")
                print(f"Connection details: {config['host']}:{config['port']}")
                
                return True, config
            else:
                print("FAIL - Set/Get test failed")
                continue
                
        except ConnectionError as e:
            print(f"Connection failed: {str(e)}")
            continue
        except AuthenticationError as e:
            print(f"Authentication failed: {str(e)}")
            continue
        except Exception as e:
            print(f"Error: {str(e)}")
            continue
    
    return False, None

def test_redis_operations(config):
    """Test various Redis operations"""
    print("\nTesting Redis operations...")
    
    try:
        r = redis.Redis(
            host=config['host'],
            port=config['port'],
            password=config['password'],
            db=config['db'],
            decode_responses=True
        )
        
        # Test 1: String operations
        print("1. String operations ... ", end="")
        r.set('test_string', 'Hello Redis!')
        value = r.get('test_string')
        if value == 'Hello Redis!':
            print("PASS")
        else:
            print("FAIL")
            return False
        
        # Test 2: Number operations
        print("2. Number operations ... ", end="")
        r.set('test_counter', 0)
        r.incr('test_counter', 5)
        counter = int(r.get('test_counter'))
        if counter == 5:
            print("PASS")
        else:
            print("FAIL")
            return False
        
        # Test 3: List operations
        print("3. List operations ... ", end="")
        list_key = 'test_list'
        r.delete(list_key)  # Clean slate
        r.lpush(list_key, 'item1', 'item2', 'item3')
        list_length = r.llen(list_key)
        if list_length == 3:
            print("PASS")
        else:
            print("FAIL")
            return False
        
        # Test 4: Hash operations
        print("4. Hash operations ... ", end="")
        hash_key = 'test_hash'
        r.hset(hash_key, mapping={'field1': 'value1', 'field2': 'value2'})
        hash_value = r.hget(hash_key, 'field1')
        if hash_value == 'value1':
            print("PASS")
        else:
            print("FAIL")
            return False
        
        # Test 5: Set operations
        print("5. Set operations ... ", end="")
        set_key = 'test_set'
        r.sadd(set_key, 'member1', 'member2', 'member3')
        set_size = r.scard(set_key)
        if set_size == 3:
            print("PASS")
        else:
            print("FAIL")
            return False
        
        # Clean up test keys
        test_keys = ['test_string', 'test_counter', 'test_list', 'test_hash', 'test_set']
        r.delete(*test_keys)
        
        print("\n[SUCCESS] All Redis operations completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Redis operations test failed: {e}")
        return False

def main():
    """Main function"""
    print("Simple Redis Connection Test")
    print("=" * 35)
    
    # Test basic connection
    connected, config = test_redis_connection()
    
    if not connected:
        print("\n[FAIL] Could not connect to Redis")
        print("\nTroubleshooting:")
        print("1. Make sure WSL2 is running: wsl --list --running")
        print("2. Start Redis in WSL2: wsl -e sudo systemctl start redis-server")
        print("3. Check Redis status: wsl -e sudo systemctl status redis-server")
        print("4. Test from WSL2: wsl -e redis-cli -a testredispass ping")
        return 1
    
    # Test operations
    if test_redis_operations(config):
        print("\n[COMPLETE] Redis setup is fully functional!")
        print("\nConnection details for your application:")
        print(f"- Host: {config['host']}")
        print(f"- Port: {config['port']}")
        print(f"- Password: {config['password'] if config['password'] else '(none)'}")
        print(f"- Database: {config['db']}")
        return 0
    else:
        print("\n[PARTIAL] Redis connected but some operations failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nScript cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)