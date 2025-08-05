"""
Integration Tests for Native Service Alternatives
================================================

Tier 2 (Integration) tests using Windows native alternatives to Docker services.
These tests demonstrate that real service functionality works without Docker.

Tier 2 requirements:
- Use real services (no mocking)
- Test component interactions
- SQLite instead of PostgreSQL
- Python dict/file instead of Redis/NoSQL
- Complete data flows
"""

import sqlite3
import json
import tempfile
import os
from pathlib import Path
import pytest
import time


class TestSQLiteAsPostgreSQLAlternative:
    """Test SQLite as a drop-in alternative to PostgreSQL for development"""
    
    def test_sqlite_basic_operations(self):
        """Test basic CRUD operations with SQLite"""
        # Create in-memory database
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert data
        cursor.execute(
            "INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
            ("Test Product", "A test product", 19.99)
        )
        
        # Read data
        cursor.execute("SELECT * FROM products WHERE name = ?", ("Test Product",))
        result = cursor.fetchone()
        
        # Verify
        assert result is not None
        assert result[1] == "Test Product"  # name
        assert result[2] == "A test product"  # description
        assert result[3] == 19.99  # price
        
        # Update data
        cursor.execute(
            "UPDATE products SET price = ? WHERE name = ?",
            (24.99, "Test Product")
        )
        
        # Verify update
        cursor.execute("SELECT price FROM products WHERE name = ?", ("Test Product",))
        updated_price = cursor.fetchone()[0]
        assert updated_price == 24.99
        
        # Delete data
        cursor.execute("DELETE FROM products WHERE name = ?", ("Test Product",))
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        assert count == 0
        
        conn.close()
    
    def test_sqlite_complex_queries(self):
        """Test complex queries and joins with SQLite"""
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Create tables with relationships
        cursor.execute('''
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category_id INTEGER,
                price REAL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        
        # Insert test data
        cursor.execute("INSERT INTO categories (name) VALUES (?)", ("Electronics",))
        category_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO products (name, category_id, price) VALUES (?, ?, ?)",
            ("Laptop", category_id, 999.99)
        )
        
        cursor.execute(
            "INSERT INTO products (name, category_id, price) VALUES (?, ?, ?)",
            ("Mouse", category_id, 29.99)
        )
        
        # Test join query
        cursor.execute('''
            SELECT p.name, p.price, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.price > ?
        ''', (50.0,))
        
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == "Laptop"
        assert results[0][1] == 999.99
        assert results[0][2] == "Electronics"
        
        conn.close()


class TestPythonDictAsRedisAlternative:
    """Test Python dict/file as Redis alternative for caching"""
    
    def test_in_memory_cache_operations(self):
        """Test basic cache operations with Python dict"""
        cache = {}
        
        # SET operation
        cache['user:123'] = {'name': 'John Doe', 'email': 'john@example.com'}
        cache['session:abc'] = {'user_id': 123, 'expires': time.time() + 3600}
        
        # GET operation
        user = cache.get('user:123')
        assert user is not None
        assert user['name'] == 'John Doe'
        
        # EXISTS operation
        assert 'user:123' in cache
        assert 'user:456' not in cache
        
        # DELETE operation
        del cache['session:abc']
        assert 'session:abc' not in cache
        
        # KEYS pattern matching (simplified)
        keys = [k for k in cache.keys() if k.startswith('user:')]
        assert len(keys) == 1
        assert 'user:123' in keys
    
    def test_cache_with_expiration(self):
        """Test cache with TTL functionality"""
        import time
        
        cache = {}
        
        def set_with_ttl(key, value, ttl_seconds):
            cache[key] = {
                'value': value,
                'expires': time.time() + ttl_seconds
            }
        
        def get_with_ttl(key):
            if key not in cache:
                return None
            
            entry = cache[key]
            if time.time() > entry['expires']:
                del cache[key]
                return None
            
            return entry['value']
        
        # Test setting and getting with TTL
        set_with_ttl('temp:data', {'message': 'Hello'}, 2)
        
        # Should be available immediately
        result = get_with_ttl('temp:data')
        assert result is not None
        assert result['message'] == 'Hello'
        
        # Should still be available after 1 second
        time.sleep(1)
        result = get_with_ttl('temp:data')
        assert result is not None
        
        # Should be expired after 3 seconds total
        time.sleep(2.5)
        result = get_with_ttl('temp:data')
        assert result is None


class TestJSONFileAsDocumentStore:
    """Test JSON files as NoSQL document store alternative"""
    
    def test_json_document_operations(self):
        """Test document CRUD operations with JSON files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_file = Path(temp_dir) / "documents.json"
            
            # Initialize empty database
            database = {'documents': []}
            
            def save_db():
                with open(db_file, 'w') as f:
                    json.dump(database, f, indent=2)
            
            def load_db():
                nonlocal database
                if db_file.exists():
                    with open(db_file, 'r') as f:
                        database = json.load(f)
            
            # CREATE document
            doc1 = {
                'id': '1',
                'type': 'product',
                'data': {
                    'name': 'Test Product',
                    'price': 29.99,
                    'tags': ['test', 'product']
                }
            }
            
            database['documents'].append(doc1)
            save_db()
            
            # READ document
            load_db()
            found_doc = next(
                (doc for doc in database['documents'] if doc['id'] == '1'),
                None
            )
            assert found_doc is not None
            assert found_doc['data']['name'] == 'Test Product'
            
            # UPDATE document
            found_doc['data']['price'] = 39.99
            save_db()
            
            # Verify update
            load_db()
            updated_doc = next(
                (doc for doc in database['documents'] if doc['id'] == '1'),
                None
            )
            assert updated_doc['data']['price'] == 39.99
            
            # DELETE document
            database['documents'] = [
                doc for doc in database['documents'] if doc['id'] != '1'
            ]
            save_db()
            
            # Verify deletion
            load_db()
            deleted_doc = next(
                (doc for doc in database['documents'] if doc['id'] == '1'),
                None
            )
            assert deleted_doc is None
    
    def test_json_query_operations(self):
        """Test query operations on JSON documents"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_file = Path(temp_dir) / "products.json"
            
            # Create test data
            database = {
                'documents': [
                    {
                        'id': '1',
                        'type': 'product',
                        'data': {'name': 'Laptop', 'category': 'electronics', 'price': 999.99}
                    },
                    {
                        'id': '2', 
                        'type': 'product',
                        'data': {'name': 'Mouse', 'category': 'electronics', 'price': 29.99}
                    },
                    {
                        'id': '3',
                        'type': 'product', 
                        'data': {'name': 'Book', 'category': 'education', 'price': 19.99}
                    }
                ]
            }
            
            with open(db_file, 'w') as f:
                json.dump(database, f)
            
            # Load and query
            with open(db_file, 'r') as f:
                db = json.load(f)
            
            # Find by category
            electronics = [
                doc for doc in db['documents']
                if doc['data'].get('category') == 'electronics'
            ]
            assert len(electronics) == 2
            
            # Find by price range
            expensive = [
                doc for doc in db['documents']
                if doc['data'].get('price', 0) > 100
            ]
            assert len(expensive) == 1
            assert expensive[0]['data']['name'] == 'Laptop'
            
            # Find by name pattern
            books = [
                doc for doc in db['documents']
                if 'book' in doc['data'].get('name', '').lower()
            ]
            assert len(books) == 1
            assert books[0]['data']['category'] == 'education'


class TestIntegratedWorkflow:
    """Test integrated workflow using multiple native services"""
    
    def test_full_data_pipeline(self):
        """Test complete data pipeline using native services"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup SQLite database
            db_file = Path(temp_dir) / "pipeline.db"
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE raw_data (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value REAL,
                    processed BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Setup JSON document store
            doc_file = Path(temp_dir) / "processed.json"
            processed_docs = {'documents': []}
            
            # Setup cache
            cache = {}
            
            # Pipeline Step 1: Insert raw data
            raw_data = [
                ('Product A', 100.0),
                ('Product B', 200.0),
                ('Product C', 150.0)
            ]
            
            for name, value in raw_data:
                cursor.execute(
                    "INSERT INTO raw_data (name, value) VALUES (?, ?)",
                    (name, value)
                )
            
            conn.commit()
            
            # Pipeline Step 2: Process data with caching
            cursor.execute("SELECT * FROM raw_data WHERE processed = FALSE")
            unprocessed = cursor.fetchall()
            
            for row in unprocessed:
                row_id, name, value, processed = row
                
                # Check cache first
                cache_key = f"processed:{row_id}"
                if cache_key not in cache:
                    # Process data (simple transformation)
                    processed_value = value * 1.1  # 10% markup
                    cache[cache_key] = processed_value
                else:
                    processed_value = cache[cache_key]
                
                # Store in document store
                doc = {
                    'id': str(row_id),
                    'original_name': name,
                    'original_value': value,
                    'processed_value': processed_value,
                    'markup_percent': 10
                }
                processed_docs['documents'].append(doc)
                
                # Mark as processed in SQL
                cursor.execute(
                    "UPDATE raw_data SET processed = TRUE WHERE id = ?",
                    (row_id,)
                )
            
            conn.commit()
            
            # Save processed documents
            with open(doc_file, 'w') as f:
                json.dump(processed_docs, f, indent=2)
            
            # Pipeline Step 3: Verify results
            # Check SQL database
            cursor.execute("SELECT COUNT(*) FROM raw_data WHERE processed = TRUE")
            processed_count = cursor.fetchone()[0]
            assert processed_count == 3
            
            # Check document store
            assert len(processed_docs['documents']) == 3
            
            # Check cache
            assert len(cache) == 3
            
            # Verify data integrity
            with open(doc_file, 'r') as f:
                saved_docs = json.load(f)
            
            assert len(saved_docs['documents']) == 3
            
            # Find specific document
            product_a_doc = next(
                doc for doc in saved_docs['documents']
                if doc['original_name'] == 'Product A'
            )
            assert abs(product_a_doc['processed_value'] - 110.0) < 0.01  # 100 * 1.1 (floating point safe)
            
            conn.close()
            
            # Fix for Windows file locking
            import time
            time.sleep(0.1)  # Allow file handles to close properly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])