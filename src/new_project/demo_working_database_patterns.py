#!/usr/bin/env python3
"""
Working Database Patterns Demo

Demonstrates functional database operations using Core SDK with SQLDatabaseNode.
This approach works with the current infrastructure and provides DataFlow-like functionality.
"""

import sys
import os
from pathlib import Path

# Windows SDK compatibility patch
if sys.platform == "win32":
    try:
        import resource
    except ImportError:
        import types
        resource = types.ModuleType('resource')
        resource.RLIMIT_CPU = 0
        resource.getrlimit = lambda x: (float('inf'), float('inf'))
        resource.setrlimit = lambda x, y: None
        sys.modules['resource'] = resource

# Test environment setup
test_dir = Path(__file__).parent
db_path = test_dir / "demo_working_patterns.db"

def cleanup_demo_db():
    """Clean up demo database"""
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            pass  # Database may still be in use

def demo_product_crud_patterns():
    """Demonstrate CRUD patterns using Core SDK"""
    print("=" * 60)
    print("WORKING DATABASE PATTERNS DEMO")
    print("=" * 60)
    
    cleanup_demo_db()
    
    try:
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        
        # Initialize runtime
        runtime = LocalRuntime()
        
        print("\n1. CREATE TABLE PATTERN")
        print("-" * 30)
        
        # Create table workflow
        create_table_workflow = WorkflowBuilder()
        create_table_workflow.add_node("SQLDatabaseNode", "create_products_table", {
            "connection_string": f"sqlite:///{db_path}",
            "query": """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    category TEXT DEFAULT 'general',
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        })
        
        results, run_id = runtime.execute(create_table_workflow.build())
        print(f"Table created: {results['create_products_table']['row_count']} rows affected")
        
        print("\n2. INSERT (CREATE) PATTERN")
        print("-" * 30)
        
        # Insert products workflow
        insert_workflow = WorkflowBuilder()
        insert_workflow.add_node("SQLDatabaseNode", "insert_product_1", {
            "connection_string": f"sqlite:///{db_path}",
            "query": """
                INSERT INTO products (name, price, category, active) 
                VALUES ('Laptop Pro', 1299.99, 'electronics', 1)
            """
        })
        insert_workflow.add_node("SQLDatabaseNode", "insert_product_2", {
            "connection_string": f"sqlite:///{db_path}",
            "query": """
                INSERT INTO products (name, price, category, active) 
                VALUES ('Wireless Mouse', 29.99, 'electronics', 1)
            """
        })
        insert_workflow.add_node("SQLDatabaseNode", "insert_product_3", {
            "connection_string": f"sqlite:///{db_path}",
            "query": """
                INSERT INTO products (name, price, category, active) 
                VALUES ('Office Chair', 199.99, 'furniture', 1)
            """
        })
        
        results, run_id = runtime.execute(insert_workflow.build())
        print(f"Products inserted: {len(results)} products created")
        for key, result in results.items():
            print(f"  {key}: {result['row_count']} rows affected")
        
        print("\n3. READ (SELECT) PATTERNS")
        print("-" * 30)
        
        # Select all products
        select_all_workflow = WorkflowBuilder()
        select_all_workflow.add_node("SQLDatabaseNode", "select_all_products", {
            "connection_string": f"sqlite:///{db_path}",
            "query": "SELECT * FROM products ORDER BY created_at DESC"
        })
        
        results, run_id = runtime.execute(select_all_workflow.build())
        all_products = results['select_all_products']['data']
        print(f"All products retrieved: {len(all_products)} products")
        for product in all_products:
            print(f"  ID: {product['id']}, Name: {product['name']}, Price: ${product['price']}, Category: {product['category']}")
        
        # Select by category (filtering pattern)
        select_filtered_workflow = WorkflowBuilder()
        select_filtered_workflow.add_node("SQLDatabaseNode", "select_electronics", {
            "connection_string": f"sqlite:///{db_path}",
            "query": "SELECT * FROM products WHERE category = 'electronics' AND active = 1"
        })
        
        results, run_id = runtime.execute(select_filtered_workflow.build())
        electronics = results['select_electronics']['data']
        print(f"\nElectronics products: {len(electronics)} found")
        for product in electronics:
            print(f"  {product['name']}: ${product['price']}")
        
        print("\n4. UPDATE PATTERN")
        print("-" * 30)
        
        # Update product price
        update_workflow = WorkflowBuilder()
        update_workflow.add_node("SQLDatabaseNode", "update_laptop_price", {
            "connection_string": f"sqlite:///{db_path}",
            "query": """
                UPDATE products 
                SET price = 1199.99 
                WHERE name = 'Laptop Pro'
            """
        })
        
        results, run_id = runtime.execute(update_workflow.build())
        print(f"Price updated: {results['update_laptop_price']['row_count']} rows affected")
        
        # Verify update
        verify_update_workflow = WorkflowBuilder()
        verify_update_workflow.add_node("SQLDatabaseNode", "verify_price_update", {
            "connection_string": f"sqlite:///{db_path}",
            "query": "SELECT name, price FROM products WHERE name = 'Laptop Pro'"
        })
        
        results, run_id = runtime.execute(verify_update_workflow.build())
        updated_product = results['verify_price_update']['data'][0]
        print(f"Updated product: {updated_product['name']} now costs ${updated_product['price']}")
        
        print("\n5. ADVANCED QUERY PATTERNS")
        print("-" * 30)
        
        # Aggregation query
        stats_workflow = WorkflowBuilder()
        stats_workflow.add_node("SQLDatabaseNode", "product_statistics", {
            "connection_string": f"sqlite:///{db_path}",
            "query": """
                SELECT 
                    category,
                    COUNT(*) as product_count,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price
                FROM products 
                WHERE active = 1
                GROUP BY category
                ORDER BY avg_price DESC
            """
        })
        
        results, run_id = runtime.execute(stats_workflow.build())
        stats = results['product_statistics']['data']
        print("Product statistics by category:")
        for stat in stats:
            category = stat['category']
            count = stat['product_count']
            avg_price = stat['avg_price']
            min_price = stat['min_price']
            max_price = stat['max_price']
            print(f"  {category.title()}: {count} products, avg ${avg_price:.2f} (${min_price:.2f}-${max_price:.2f})")
        
        print("\n6. DELETE PATTERN")
        print("-" * 30)
        
        # Soft delete (recommended for production)
        soft_delete_workflow = WorkflowBuilder()
        soft_delete_workflow.add_node("SQLDatabaseNode", "soft_delete_product", {
            "connection_string": f"sqlite:///{db_path}",
            "query": """
                UPDATE products 
                SET active = 0 
                WHERE name = 'Wireless Mouse'
            """
        })
        
        results, run_id = runtime.execute(soft_delete_workflow.build())
        print(f"Product soft deleted: {results['soft_delete_product']['row_count']} rows affected")
        
        # Verify active products
        active_count_workflow = WorkflowBuilder()
        active_count_workflow.add_node("SQLDatabaseNode", "count_active_products", {
            "connection_string": f"sqlite:///{db_path}",
            "query": "SELECT COUNT(*) FROM products WHERE active = 1"
        })
        
        results, run_id = runtime.execute(active_count_workflow.build())
        active_count = list(results['count_active_products']['data'][0].values())[0]
        print(f"Active products remaining: {active_count}")
        
        print("\n7. BULK OPERATIONS PATTERN")
        print("-" * 30)
        
        # Bulk insert using single query
        bulk_insert_workflow = WorkflowBuilder()
        bulk_insert_workflow.add_node("SQLDatabaseNode", "bulk_insert_products", {
            "connection_string": f"sqlite:///{db_path}",
            "query": """
                INSERT INTO products (name, price, category, active) VALUES
                ('Desk Lamp', 45.99, 'furniture', 1),
                ('USB Cable', 12.99, 'electronics', 1),
                ('Notebook', 8.99, 'office', 1),
                ('Pen Set', 15.99, 'office', 1),
                ('Monitor Stand', 79.99, 'furniture', 1)
            """
        })
        
        results, run_id = runtime.execute(bulk_insert_workflow.build())
        print(f"Bulk insert completed: {results['bulk_insert_products']['row_count']} rows added")
        
        # Final count
        final_count_workflow = WorkflowBuilder()
        final_count_workflow.add_node("SQLDatabaseNode", "final_product_count", {
            "connection_string": f"sqlite:///{db_path}",
            "query": "SELECT COUNT(*) FROM products WHERE active = 1"
        })
        
        results, run_id = runtime.execute(final_count_workflow.build())
        total_products = list(results['final_product_count']['data'][0].values())[0]
        print(f"Total active products: {total_products}")
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nPATTERNS DEMONSTRATED:")
        print("+ Table creation and schema management")
        print("+ CRUD operations (Create, Read, Update, Delete)")
        print("+ Filtering and conditional queries")
        print("+ Aggregation and statistics")
        print("+ Bulk operations")
        print("+ Soft delete patterns")
        print("+ Workflow-based database operations")
        
        print("\nKEY BENEFITS:")
        print("- Works with existing SQLite infrastructure")
        print("- No PostgreSQL dependency")
        print("- Full workflow integration")
        print("- Transparent SQL operations")
        print("- Production-ready patterns")
        
        print("\nNEXT STEPS:")
        print("1. Adapt these patterns for classification models")
        print("2. Create reusable workflow templates")
        print("3. Add error handling and validation")
        print("4. Implement connection pooling for production")
        print("5. Consider PostgreSQL migration for DataFlow")
        
        return True
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        cleanup_demo_db()

if __name__ == "__main__":
    success = demo_product_crud_patterns()
    
    if success:
        print("\nDatabase patterns demo completed successfully!")
        print("Ready to implement production database workflows.")
    else:
        print("\nDemo encountered issues - check error messages above.")
    
    sys.exit(0 if success else 1)