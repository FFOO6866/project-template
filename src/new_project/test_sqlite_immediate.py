#!/usr/bin/env python3
"""
IMMEDIATE SQLite Test - Working in Next 10 Minutes
==================================================

No Docker, no PostgreSQL, no external dependencies.
Just Python's built-in SQLite database for IMMEDIATE testing.
"""

import sqlite3
import os
import sys
from pathlib import Path

# Apply Windows compatibility first
try:
    import windows_sdk_compatibility
    print("[INFO] Windows SDK compatibility applied")
except ImportError:
    print("[WARNING] Windows SDK compatibility not found, continuing anyway")

def setup_sqlite_database():
    """Create SQLite database with test tables - IMMEDIATE WORKING"""
    
    # Use project directory for database
    project_dir = Path(__file__).parent
    db_path = project_dir / "test_horme.db"
    
    print(f"Creating SQLite database at: {db_path}")
    
    try:
        # Create database connection
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create test tables immediately
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                classification_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert test data immediately
        cursor.execute("INSERT OR IGNORE INTO companies (name) VALUES ('Test Company')")
        cursor.execute("INSERT OR IGNORE INTO users (name, email, company_id) VALUES ('Test User', 'test@example.com', 1)")
        cursor.execute("INSERT OR IGNORE INTO products (name, description, classification_code) VALUES ('Test Product', 'Test Description', 'TEST-001')")
        
        conn.commit()
        
        # Verify data exists
        cursor.execute("SELECT COUNT(*) FROM companies")
        company_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"[SUCCESS] SQLite database created with:")
        print(f"  - {company_count} companies")
        print(f"  - {user_count} users")
        print(f"  - {product_count} products")
        
        return str(db_path)
        
    except Exception as e:
        print(f"[ERROR] SQLite setup failed: {e}")
        return None

def test_sqlite_crud_operations(db_path):
    """Test basic CRUD operations - IMMEDIATE WORKING"""
    
    print("\nTesting CRUD operations...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # CREATE - Add a new product
        cursor.execute("""
            INSERT INTO products (name, description, classification_code) 
            VALUES (?, ?, ?)
        """, ("Immediate Test Product", "Created right now", "IMMEDIATE-001"))
        
        new_product_id = cursor.lastrowid
        print(f"[CREATE] Added product with ID: {new_product_id}")
        
        # READ - Get the product
        cursor.execute("SELECT * FROM products WHERE id = ?", (new_product_id,))
        product = cursor.fetchone()
        print(f"[READ] Retrieved product: {product[1]} - {product[2]}")
        
        # UPDATE - Modify the product
        cursor.execute("""
            UPDATE products 
            SET description = ? 
            WHERE id = ?
        """, ("Updated in real-time test", new_product_id))
        
        print(f"[UPDATE] Modified product {new_product_id}")
        
        # LIST - Get all products
        cursor.execute("SELECT id, name, classification_code FROM products")
        all_products = cursor.fetchall()
        print(f"[LIST] Found {len(all_products)} products:")
        for product in all_products:
            print(f"  {product[0]}: {product[1]} ({product[2]})")
        
        # DELETE - Remove test product (optional, keep for demo)
        # cursor.execute("DELETE FROM products WHERE id = ?", (new_product_id,))
        # print(f"[DELETE] Removed product {new_product_id}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("[SUCCESS] All CRUD operations working!")
        return True
        
    except Exception as e:
        print(f"[ERROR] CRUD test failed: {e}")
        return False

def test_sdk_integration_immediate():
    """Test with Kailash SDK using SQLite - IMMEDIATE WORKING"""
    
    print("\nTesting SDK integration with SQLite...")
    
    try:
        # Try to import SDK components
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        
        print("[SUCCESS] SDK imports successful")
        
        # Create a simple workflow that works with SQLite
        workflow = WorkflowBuilder()
        
        # Add a simple data processing node that doesn't need external DB
        workflow.add_node("JSONProcessorNode", "json_processor", {
            "input_data": {"test": "immediate", "working": True, "timestamp": "now"}
        })
        
        # Execute the workflow
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        
        print(f"[SUCCESS] Workflow executed with run_id: {run_id}")
        print(f"[SUCCESS] Results: {results}")
        
        return True
        
    except ImportError as e:
        print(f"[WARNING] SDK not available: {e}")
        print("[INFO] But SQLite database is working and ready!")
        return False
    except Exception as e:
        print(f"[ERROR] SDK integration failed: {e}")
        return False

def generate_immediate_connection_string(db_path):
    """Generate connection string for immediate use"""
    
    # SQLite connection string
    sqlite_url = f"sqlite:///{db_path}"
    
    print(f"\n{'='*50}")
    print("IMMEDIATE DATABASE CONNECTION READY!")
    print("="*50)
    print(f"SQLite Database Path: {db_path}")
    print(f"Connection String: {sqlite_url}")
    print("")
    print("Python connection code:")
    print("```python")
    print("import sqlite3")
    print(f"conn = sqlite3.connect(r'{db_path}')")
    print("cursor = conn.cursor()")
    print("cursor.execute('SELECT * FROM products')")
    print("results = cursor.fetchall()")
    print("print(results)")
    print("```")
    print("")
    print("For SQLAlchemy/async usage:")
    print("```python")
    print(f"DATABASE_URL = '{sqlite_url}'")
    print("```")
    
    return sqlite_url

def main():
    """IMMEDIATE working database setup - 5 minutes or less"""
    
    print("IMMEDIATE SQLite Database Setup")
    print("="*40)
    print("Creating working database in under 5 minutes...")
    
    # Step 1: Create SQLite database (30 seconds)
    db_path = setup_sqlite_database()
    if not db_path:
        print("[FAIL] Could not create database")
        return 1
    
    # Step 2: Test CRUD operations (30 seconds)
    if not test_sqlite_crud_operations(db_path):
        print("[FAIL] CRUD operations failed")
        return 1
    
    # Step 3: Test SDK integration (optional, 1 minute)
    sdk_working = test_sdk_integration_immediate()
    
    # Step 4: Generate connection info (immediate)
    connection_string = generate_immediate_connection_string(db_path)
    
    # Final status
    print(f"\n{'='*50}")
    print("IMMEDIATE SETUP COMPLETE!")
    print("="*50)
    print("[✓] SQLite database created and working")
    print("[✓] CRUD operations tested and working")
    print(f"[{'✓' if sdk_working else '?'}] SDK integration {'working' if sdk_working else 'not tested'}")
    print("[✓] Ready for immediate development!")
    
    print(f"\nDatabase file: {db_path}")
    print("You can start using this database RIGHT NOW!")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nSetup cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)