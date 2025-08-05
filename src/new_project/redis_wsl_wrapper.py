#!/usr/bin/env python3
"""
Redis WSL2 Wrapper
==================

This wrapper provides Redis functionality by executing commands through WSL2
when direct network connectivity is not available.
"""

import subprocess
import json
import sys
from typing import Any, Optional, Union

class RedisWSLWrapper:
    """Redis client that works through WSL2 command execution"""
    
    def __init__(self, password: str = 'testredispass'):
        self.password = password
        self._test_connection()
    
    def _execute_redis_command(self, command: str, *args) -> str:
        """Execute a Redis command through WSL2"""
        cmd_parts = ['wsl', '-e', 'redis-cli', '-a', self.password]
        cmd_parts.append(command)
        cmd_parts.extend(str(arg) for arg in args)
        
        try:
            result = subprocess.run(
                cmd_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                raise Exception(f"Redis command failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise Exception("Redis command timed out")
        except Exception as e:
            raise Exception(f"Failed to execute Redis command: {e}")
    
    def _test_connection(self):
        """Test if Redis is accessible through WSL2"""
        try:
            response = self._execute_redis_command('PING')
            if response != 'PONG':
                raise Exception(f"Unexpected PING response: {response}")
        except Exception as e:
            raise Exception(f"Redis connection test failed: {e}")
    
    def ping(self) -> bool:
        """Test Redis connectivity"""
        try:
            response = self._execute_redis_command('PING')
            return response == 'PONG'
        except:
            return False
    
    def set(self, key: str, value: str) -> bool:
        """Set a key-value pair"""
        try:
            response = self._execute_redis_command('SET', key, value)
            return response == 'OK'
        except:
            return False
    
    def get(self, key: str) -> Optional[str]:
        """Get a value by key"""
        try:
            response = self._execute_redis_command('GET', key)
            return response if response != '(nil)' else None
        except:
            return None
    
    def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        try:
            response = self._execute_redis_command('DEL', *keys)
            return int(response)
        except:
            return 0
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a key by amount"""
        try:
            if amount == 1:
                response = self._execute_redis_command('INCR', key)
            else:
                response = self._execute_redis_command('INCRBY', key, amount)
            return int(response)
        except:
            return None
    
    def lpush(self, key: str, *values: str) -> Optional[int]:
        """Push values to the left of a list"""
        try:
            response = self._execute_redis_command('LPUSH', key, *values)
            return int(response)
        except:
            return None
    
    def llen(self, key: str) -> Optional[int]:
        """Get the length of a list"""
        try:
            response = self._execute_redis_command('LLEN', key)
            return int(response)
        except:
            return None
    
    def hset(self, key: str, field: str, value: str) -> bool:
        """Set a hash field"""
        try:
            response = self._execute_redis_command('HSET', key, field, value)
            return response in ['0', '1']  # 0 = updated, 1 = created
        except:
            return False
    
    def hget(self, key: str, field: str) -> Optional[str]:
        """Get a hash field"""
        try:
            response = self._execute_redis_command('HGET', key, field)
            return response if response != '(nil)' else None
        except:
            return None
    
    def sadd(self, key: str, *members: str) -> Optional[int]:
        """Add members to a set"""
        try:
            response = self._execute_redis_command('SADD', key, *members)
            return int(response)
        except:
            return None
    
    def scard(self, key: str) -> Optional[int]:
        """Get the size of a set"""
        try:
            response = self._execute_redis_command('SCARD', key)
            return int(response)
        except:
            return None
    
    def info(self, section: str = 'server') -> dict:
        """Get Redis server information"""
        try:
            response = self._execute_redis_command('INFO', section)
            info_dict = {}
            for line in response.split('\n'):
                if ':' in line and not line.startswith('#'):
                    key, value = line.split(':', 1)
                    info_dict[key] = value
            return info_dict
        except:
            return {}

def test_redis_wsl_wrapper():
    """Test the Redis WSL wrapper"""
    print("Testing Redis WSL2 Wrapper")
    print("=" * 30)
    
    try:
        # Initialize wrapper
        print("1. Initializing Redis wrapper ... ", end="")
        redis_client = RedisWSLWrapper()
        print("PASS")
        
        # Test basic operations
        print("2. Testing PING ... ", end="")
        if redis_client.ping():
            print("PASS")
        else:
            print("FAIL")
            return False
        
        # Test string operations
        print("3. Testing SET/GET ... ", end="")
        if redis_client.set('test_key', 'test_value'):
            value = redis_client.get('test_key')
            if value == 'test_value':
                print("PASS")
                redis_client.delete('test_key')
            else:
                print(f"FAIL - got '{value}' expected 'test_value'")
                return False
        else:
            print("FAIL - SET operation failed")
            return False
        
        # Test increment
        print("4. Testing INCR ... ", end="")
        redis_client.set('counter', '0')
        new_value = redis_client.incr('counter', 5)
        if new_value == 5:
            print("PASS")
            redis_client.delete('counter')
        else:
            print(f"FAIL - got {new_value} expected 5")
            return False
        
        # Test list operations
        print("5. Testing list operations ... ", end="")
        redis_client.delete('test_list')  # Clean slate
        list_len = redis_client.lpush('test_list', 'item1', 'item2', 'item3')
        current_len = redis_client.llen('test_list')
        if list_len == 3 and current_len == 3:
            print("PASS")
            redis_client.delete('test_list')
        else:
            print(f"FAIL - lengths: push={list_len}, current={current_len}")
            return False
        
        # Test hash operations
        print("6. Testing hash operations ... ", end="")
        if redis_client.hset('test_hash', 'field1', 'value1'):
            value = redis_client.hget('test_hash', 'field1')
            if value == 'value1':
                print("PASS")
                redis_client.delete('test_hash')
            else:
                print(f"FAIL - got '{value}' expected 'value1'")
                return False
        else:
            print("FAIL - HSET operation failed")
            return False
        
        # Test set operations
        print("7. Testing set operations ... ", end="")
        members_added = redis_client.sadd('test_set', 'member1', 'member2', 'member3')
        set_size = redis_client.scard('test_set')
        if members_added == 3 and set_size == 3:
            print("PASS")
            redis_client.delete('test_set')
        else:
            print(f"FAIL - added={members_added}, size={set_size}")
            return False
        
        # Test info
        print("8. Testing server info ... ", end="")
        info = redis_client.info('server')
        if 'redis_version' in info:
            print(f"PASS (Redis {info['redis_version']})")
        else:
            print("FAIL - no version info")
            return False
        
        print("\n[SUCCESS] All Redis operations working through WSL2!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Redis wrapper test failed: {e}")
        return False

def main():
    """Main function"""
    if test_redis_wsl_wrapper():
        print("\nRedis WSL2 wrapper is ready for use!")
        print("You can use RedisWSLWrapper class in your applications")
        return 0
    else:
        print("\nRedis WSL2 wrapper test failed")
        return 1

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