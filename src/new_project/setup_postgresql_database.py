#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script
================================

This script helps set up the PostgreSQL database with test users and databases
after PostgreSQL has been successfully installed.
"""

import os
import sys
import subprocess
import getpass
from pathlib import Path

def find_postgres_bin():
    """Find PostgreSQL bin directory"""
    common_paths = [
        r"C:\Program Files\PostgreSQL\17\bin",
        r"C:\Program Files\PostgreSQL\16\bin", 
        r"C:\Program Files\PostgreSQL\15\bin",
        r"C:\Program Files\PostgreSQL\14\bin",
        r"C:\Program Files (x86)\PostgreSQL\17\bin",
        r"C:\Program Files (x86)\PostgreSQL\16\bin"
    ]
    
    for path in common_paths:
        if Path(path).exists() and Path(path, "psql.exe").exists():
            return Path(path)
    
    # Check if psql is in PATH
    try:
        result = subprocess.run(['where', 'psql'], capture_output=True, text=True)
        if result.returncode == 0:
            psql_path = Path(result.stdout.strip())
            return psql_path.parent
    except:
        pass
    
    return None

def run_psql_command(bin_path, host, port, username, database, command, password=None):
    """Run a psql command"""
    psql_exe = bin_path / "psql.exe"
    
    env = os.environ.copy()
    if password:
        env['PGPASSWORD'] = password
    
    cmd = [
        str(psql_exe),
        '-h', host,
        '-p', str(port),
        '-U', username,
        '-d', database,
        '-c', command
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def test_connection(bin_path, host, port, username, database, password=None):
    """Test database connection"""
    success, stdout, stderr = run_psql_command(
        bin_path, host, port, username, database, 
        "SELECT version();", password
    )
    return success, stdout if success else stderr

def create_test_database_setup(bin_path, admin_password):
    """Create test database and user"""
    print("Creating test database and user...")
    
    # Commands to create test user and database
    commands = [
        "CREATE USER test_user WITH PASSWORD 'test_password';",
        "CREATE DATABASE test_horme_db OWNER test_user;",
        "GRANT ALL PRIVILEGES ON DATABASE test_horme_db TO test_user;"
    ]
    
    success_count = 0
    for command in commands:
        print(f"Executing: {command}")
        success, stdout, stderr = run_psql_command(
            bin_path, 'localhost', 5432, 'postgres', 'postgres', 
            command, admin_password
        )
        
        if success:
            print(f"[SUCCESS] Success: {command}")
            success_count += 1
        else:
            print(f"[FAIL] Failed: {command}")
            print(f"Error: {stderr}")
            
            # If user/database already exists, that's okay
            if "already exists" in stderr.lower():
                print("  (Already exists - continuing)")
                success_count += 1
    
    return success_count == len(commands)

def main():
    """Main setup function"""
    print("PostgreSQL Database Setup")
    print("=" * 30)
    
    # Find PostgreSQL binaries
    print("1. Finding PostgreSQL installation...")
    bin_path = find_postgres_bin()
    
    if not bin_path:
        print("[FAIL] PostgreSQL binaries not found!")
        print("Make sure PostgreSQL is installed and either:")
        print("- Added to PATH, or")
        print("- Installed in a standard location")
        return 1
    
    print(f"[SUCCESS] Found PostgreSQL at: {bin_path}")
    
    # Test admin connection
    print("\n2. Testing PostgreSQL connection...")
    print("You'll need the PostgreSQL admin password (set during installation)")
    
    max_attempts = 3
    admin_password = None
    
    for attempt in range(max_attempts):
        admin_password = getpass.getpass("Enter PostgreSQL admin (postgres) password: ")
        
        success, result = test_connection(bin_path, 'localhost', 5432, 'postgres', 'postgres', admin_password)
        
        if success:
            print("[SUCCESS] Successfully connected to PostgreSQL!")
            break
        else:
            print(f"[FAIL] Connection failed: {result}")
            if attempt < max_attempts - 1:
                print(f"Try again ({attempt + 2}/{max_attempts})...")
            else:
                print("Maximum attempts reached. Check your password and PostgreSQL service status.")
                return 1
    
    # Create test database and user
    print("\n3. Setting up test database...")
    if create_test_database_setup(bin_path, admin_password):
        print("[SUCCESS] Test database setup completed successfully!")
    else:
        print("[FAIL] Some database setup operations failed")
        return 1
    
    # Test the new user connection
    print("\n4. Testing test user connection...")
    success, result = test_connection(bin_path, 'localhost', 5432, 'test_user', 'test_horme_db', 'test_password')
    
    if success:
        print("[SUCCESS] Test user can connect successfully!")
        print("\nDatabase setup complete! Connection details:")
        print("- Host: localhost")
        print("- Port: 5432") 
        print("- Database: test_horme_db")
        print("- Username: test_user")
        print("- Password: test_password")
        return 0
    else:
        print(f"[FAIL] Test user connection failed: {result}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)