#!/usr/bin/env python3
"""
Simple PostgreSQL Test Script
=============================

This script attempts to connect to PostgreSQL with common default passwords
and provides guidance for manual setup if needed.
"""

import sys
import psycopg2
from psycopg2 import OperationalError

def test_postgresql_connection():
    """Test PostgreSQL connection with common passwords"""
    
    # Common default passwords to try
    common_passwords = [
        'postgres',    # Most common default
        'password',    # Another common default
        'admin',       # Sometimes used
        '',            # No password
        '123456',      # Simple password
        'root'         # Alternative
    ]
    
    print("Testing PostgreSQL connection...")
    print("Trying common default passwords...")
    
    for password in common_passwords:
        try:
            print(f"Trying password: '{password if password else '(empty)'}' ... ", end="")
            
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                user='postgres',
                password=password,
                database='postgres',
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print("SUCCESS!")
            print(f"Connected with password: '{password if password else '(empty)'}'")
            print(f"PostgreSQL version: {version[:50]}...")
            
            return True, password
            
        except OperationalError as e:
            if "authentication failed" in str(e).lower():
                print("Authentication failed")
                continue
            elif "connection refused" in str(e).lower():
                print("ERROR - Connection refused")
                print("PostgreSQL service may not be running!")
                return False, None
            else:
                print(f"ERROR - {str(e)}")
                continue
        except Exception as e:
            print(f"ERROR - {str(e)}")
            continue
    
    print("\nNone of the common passwords worked.")
    return False, None

def setup_test_database(admin_password):
    """Try to set up test database using SQL commands"""
    print(f"\nAttempting to create test database with admin password...")
    
    try:
        # Connect to PostgreSQL as admin
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password=admin_password,
            database='postgres',
            connect_timeout=10
        )
        
        conn.autocommit = True  # Need this for CREATE DATABASE
        cursor = conn.cursor()
        
        # Create test user
        try:
            cursor.execute("CREATE USER test_user WITH PASSWORD 'test_password';")
            print("[SUCCESS] Created user 'test_user'")
        except psycopg2.Error as e:
            if "already exists" in str(e):
                print("[INFO] User 'test_user' already exists")
            else:
                print(f"[WARNING] Error creating user: {e}")
        
        # Create test database
        try:
            cursor.execute("CREATE DATABASE test_horme_db OWNER test_user;")
            print("[SUCCESS] Created database 'test_horme_db'")
        except psycopg2.Error as e:
            if "already exists" in str(e):
                print("[INFO] Database 'test_horme_db' already exists")
            else:
                print(f"[WARNING] Error creating database: {e}")
        
        # Grant privileges
        try:
            cursor.execute("GRANT ALL PRIVILEGES ON DATABASE test_horme_db TO test_user;")
            print("[SUCCESS] Granted privileges to test_user")
        except psycopg2.Error as e:
            print(f"[WARNING] Error granting privileges: {e}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")
        return False

def test_user_connection():
    """Test connection as test user"""
    print("\nTesting test user connection...")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='test_user',
            password='test_password',
            database='test_horme_db',
            connect_timeout=5
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT current_database(), current_user;')
        db_name, user_name = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print(f"[SUCCESS] Test user connected to database '{db_name}' as user '{user_name}'")
        return True
        
    except Exception as e:
        print(f"[FAIL] Test user connection failed: {e}")
        return False

def main():
    """Main function"""
    print("Simple PostgreSQL Connection Test")
    print("=" * 40)
    
    # Test basic connection
    connected, admin_password = test_postgresql_connection()
    
    if not connected:
        print("\n[FAIL] Could not connect to PostgreSQL")
        print("\nManual setup required:")
        print("1. Open SQL Shell (psql) from Start Menu")
        print("2. Note the password you set during installation")
        print("3. Run this script again, or manually create:")
        print("   CREATE USER test_user WITH PASSWORD 'test_password';")
        print("   CREATE DATABASE test_horme_db OWNER test_user;")
        print("   GRANT ALL PRIVILEGES ON DATABASE test_horme_db TO test_user;")
        return 1
    
    # Set up test database
    if setup_test_database(admin_password):
        print("[SUCCESS] Database setup completed")
        
        # Test user connection
        if test_user_connection():
            print("\n[COMPLETE] PostgreSQL setup is fully functional!")
            print("\nConnection details for your application:")
            print("- Host: localhost")
            print("- Port: 5432")
            print("- Database: test_horme_db")
            print("- Username: test_user")
            print("- Password: test_password")
            return 0
        else:
            print("\n[PARTIAL] Database created but test user connection failed")
            return 1
    else:
        print("\n[FAIL] Database setup failed")
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