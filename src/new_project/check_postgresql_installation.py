#!/usr/bin/env python3
"""
PostgreSQL Installation Checker
===============================

This script checks if PostgreSQL has been successfully installed and is ready for use.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_postgres_process():
    """Check if PostgreSQL installer is still running"""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq postgresql*'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if 'postgresql' in result.stdout.lower():
            return True, "PostgreSQL installer is still running"
        else:
            return False, "No PostgreSQL installer process found"
    except Exception as e:
        return False, f"Error checking process: {str(e)}"

def check_postgres_service():
    """Check if PostgreSQL service is installed and running"""
    try:
        # Check for common PostgreSQL service names
        service_names = [
            'postgresql-x64-17',
            'postgresql-x64-16', 
            'postgresql-x64-15',
            'postgresql-x64-14',
            'PostgreSQL'
        ]
        
        for service_name in service_names:
            result = subprocess.run(
                ['sc', 'query', service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                if 'RUNNING' in result.stdout:
                    return True, f"PostgreSQL service '{service_name}' is running"
                else:
                    return True, f"PostgreSQL service '{service_name}' is installed but not running"
        
        return False, "No PostgreSQL service found"
        
    except Exception as e:
        return False, f"Error checking service: {str(e)}"

def check_postgres_executable():
    """Check if PostgreSQL executables are available"""
    try:
        # Check common installation paths
        common_paths = [
            r"C:\Program Files\PostgreSQL\17\bin",
            r"C:\Program Files\PostgreSQL\16\bin",
            r"C:\Program Files\PostgreSQL\15\bin",
            r"C:\Program Files\PostgreSQL\14\bin",
            r"C:\Program Files (x86)\PostgreSQL\17\bin",
            r"C:\Program Files (x86)\PostgreSQL\16\bin"
        ]
        
        for path in common_paths:
            psql_path = Path(path) / "psql.exe"
            if psql_path.exists():
                # Try to run psql --version
                result = subprocess.run(
                    [str(psql_path), '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return True, f"PostgreSQL found at {path}: {result.stdout.strip()}"
        
        # Check if psql is in PATH
        try:
            result = subprocess.run(
                ['psql', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, f"PostgreSQL in PATH: {result.stdout.strip()}"
        except FileNotFoundError:
            pass
        
        return False, "PostgreSQL executables not found"
        
    except Exception as e:
        return False, f"Error checking executables: {str(e)}"

def wait_for_installation_complete(max_wait_minutes=10):
    """Wait for PostgreSQL installation to complete"""
    print(f"Waiting for PostgreSQL installation to complete (max {max_wait_minutes} minutes)...")
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while time.time() - start_time < max_wait_seconds:
        # Check if installer is still running
        process_running, process_msg = check_postgres_process()
        
        if not process_running:
            print(f"[COMPLETE] Installation process completed: {process_msg}")
            time.sleep(5)  # Give it a few more seconds
            break
        else:
            print(f"[WAITING] Still installing: {process_msg}")
            time.sleep(30)  # Check every 30 seconds
    else:
        print(f"[WARNING] Installation took longer than {max_wait_minutes} minutes")
        return False
    
    return True

def main():
    """Main function to check PostgreSQL installation status"""
    print("PostgreSQL Installation Checker")
    print("=" * 40)
    
    # First check if installation is still in progress
    process_running, process_msg = check_postgres_process()
    if process_running:
        print(f"[INSTALLING] {process_msg}")
        if not wait_for_installation_complete():
            print("[ERROR] Installation appears to be taking too long. Please check manually.")
            return 1
    
    print("\nChecking PostgreSQL installation...")
    
    # Check service
    service_ok, service_msg = check_postgres_service()
    print(f"Service: {'[PASS]' if service_ok else '[FAIL]'} {service_msg}")
    
    # Check executables
    exec_ok, exec_msg = check_postgres_executable()
    print(f"Executables: {'[PASS]' if exec_ok else '[FAIL]'} {exec_msg}")
    
    # Overall status
    if service_ok and exec_ok:
        print("\n[SUCCESS] PostgreSQL appears to be successfully installed!")
        print("\nNext steps:")
        print("1. Configure the database with:")
        print("   - Open SQL Shell (psql) as Administrator")
        print("   - Create test user and database")
        print("2. Install Python driver: pip install psycopg2-binary")
        print("3. Run validation script again")
        return 0
    else:
        print("\n[FAIL] PostgreSQL installation incomplete or failed")
        print("\nTroubleshooting:")
        if not service_ok:
            print("- Try starting PostgreSQL service manually")
            print("- Check Windows Services for PostgreSQL")
        if not exec_ok:
            print("- Verify installation path")
            print("- Add PostgreSQL bin directory to PATH")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)