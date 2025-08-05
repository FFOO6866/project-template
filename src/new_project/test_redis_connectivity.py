#!/usr/bin/env python3
"""
Redis Connectivity Diagnostic Script
====================================

This script performs detailed diagnostics for Redis connectivity issues.
"""

import socket
import sys
import time

def test_port_connectivity(host, port, timeout=5):
    """Test raw TCP connectivity to a port"""
    try:
        sock = socket.create_connection((host, port), timeout)
        sock.close()
        return True, "Port is open and accepting connections"
    except socket.timeout:
        return False, f"Connection to {host}:{port} timed out"
    except ConnectionRefusedError:
        return False, f"Connection to {host}:{port} was refused"
    except Exception as e:
        return False, f"Error connecting to {host}:{port}: {str(e)}"

def main():
    """Main diagnostic function"""
    print("Redis Connectivity Diagnostic")
    print("=" * 35)
    
    # Test hosts to check
    hosts_to_test = [
        ('localhost', 6379),
        ('127.0.0.1', 6379),
        ('172.18.66.241', 6379)  # WSL2 IP
    ]
    
    print("Testing raw TCP connectivity...")
    working_host = None
    
    for host, port in hosts_to_test:
        print(f"Testing {host}:{port} ... ", end="")
        success, message = test_port_connectivity(host, port)
        print("PASS" if success else "FAIL")
        if not success:
            print(f"  Reason: {message}")
        else:
            working_host = (host, port)
            print(f"  Status: {message}")
    
    if not working_host:
        print("\n[FAIL] No Redis ports are accessible from Windows")
        print("\nDiagnostic steps:")
        print("1. Check if WSL2 is running:")
        print("   wsl --list --running")
        print("2. Check Redis status in WSL2:")
        print("   wsl -e sudo systemctl status redis-server")
        print("3. Check Redis is listening:")
        print("   wsl -e sudo ss -tlnp | grep :6379")
        print("4. Test from within WSL2:")
        print("   wsl -e redis-cli -a testredispass ping")
        print("5. Try Windows firewall settings or WSL2 port forwarding")
        return 1
    
    print(f"\n[SUCCESS] Found working connection: {working_host[0]}:{working_host[1]}")
    
    # Now test Redis protocol
    print("\nTesting Redis protocol...")
    try:
        import redis
        
        r = redis.Redis(
            host=working_host[0],
            port=working_host[1],
            password='testredispass',
            socket_connect_timeout=10,
            decode_responses=True
        )
        
        # Test basic operations
        print("Testing PING ... ", end="")
        response = r.ping()
        if response:
            print("PASS")
        else:
            print("FAIL")
            return 1
        
        print("Testing SET/GET ... ", end="")
        r.set('diagnostic_test', 'success')
        value = r.get('diagnostic_test')
        if value == 'success':
            print("PASS")
            r.delete('diagnostic_test')  # cleanup
        else:
            print("FAIL")
            return 1
        
        print("\n[COMPLETE] Redis is fully functional!")
        print(f"Use these connection details:")
        print(f"- Host: {working_host[0]}")
        print(f"- Port: {working_host[1]}")
        print(f"- Password: testredispass")
        return 0
        
    except ImportError:
        print("[ERROR] Redis Python package not installed: pip install redis")
        return 1
    except Exception as e:
        print(f"[ERROR] Redis protocol test failed: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nDiagnostic cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)