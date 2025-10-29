"""
Direct Database Implementation - No SDK Dependencies
Handles SQLite and PostgreSQL connections with pooling and error handling
Optimized for Windows compatibility and 17,266 product records
"""
import sqlite3
import threading
import queue
import os
import logging
import time
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration"""
    database_path: str = "products.db"
    pool_size: int = 10
    max_connections: int = 20
    timeout: int = 30
    enable_wal: bool = True
    enable_fts: bool = True
    
class ConnectionPool:
    """Thread-safe SQLite connection pool"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool = queue.Queue(maxsize=config.max_connections)
        self._active_connections = 0
        self._lock = threading.Lock()
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Initialize the connection pool"""
        for _ in range(self.config.pool_size):
            conn = self._create_connection()
            if conn:
                self._pool.put(conn)
                
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create a new SQLite connection with optimizations"""
        try:
            conn = sqlite3.connect(
                self.config.database_path,
                timeout=self.config.timeout,
                check_same_thread=False
            )
            
            # Enable WAL mode for better concurrency
            if self.config.enable_wal:
                conn.execute("PRAGMA journal_mode=WAL")
                
            # Performance optimizations
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")
            
            conn.row_factory = sqlite3.Row
            return conn
            
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            raise RuntimeError(f"Database connection creation failed: {str(e)}") from e
            
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        try:
            # Try to get from pool
            try:
                conn = self._pool.get_nowait()
            except queue.Empty:
                # Pool is empty, create new connection if under limit
                with self._lock:
                    if self._active_connections < self.config.max_connections:
                        conn = self._create_connection()
                        if conn:
                            self._active_connections += 1
                    else:
                        # Wait for available connection
                        conn = self._pool.get(timeout=self.config.timeout)
                        
            if not conn:
                raise Exception("Unable to get database connection")
                
            yield conn
            
        finally:
            if conn:
                try:
                    # Return connection to pool
                    self._pool.put_nowait(conn)
                except queue.Full:
                    # Pool is full, close connection
                    conn.close()
                    with self._lock:
                        self._active_connections -= 1
                        
    def close_all(self):
        """Close all connections in the pool"""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except queue.Empty:
                break
                
class ProductDatabase:
    """Direct database operations for product management"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.pool = ConnectionPool(self.config)
        self.schema_initialized = False
        self._initialize_schema()
        
    def _initialize_schema(self):
        """Initialize database schema"""
        if self.schema_initialized:
            return
            
        schema_sql = """
        -- Products table with enrichment fields
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_sku TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            brand TEXT NOT NULL,
            catalogue_item_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Enrichment fields
            source_url TEXT,  -- Where the data came from
            enriched_description TEXT,  -- Detailed product info from scraping
            technical_specs TEXT,  -- JSON field for specifications
            supplier_info TEXT,  -- JSON field for supplier name, part number, etc.
            competitor_price TEXT,  -- JSON field for competitive pricing data
            images_url TEXT,  -- JSON array of product images
            last_enriched TIMESTAMP,  -- When enrichment was last performed
            enrichment_status TEXT DEFAULT 'pending',  -- pending, success, failed
            enrichment_source TEXT  -- horme, supplier, competitor, simulated
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_products_sku ON products(product_sku);
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
        CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
        CREATE INDEX IF NOT EXISTS idx_products_catalogue_id ON products(catalogue_item_id);
        CREATE INDEX IF NOT EXISTS idx_products_enrichment_status ON products(enrichment_status);
        CREATE INDEX IF NOT EXISTS idx_products_enrichment_source ON products(enrichment_source);
        CREATE INDEX IF NOT EXISTS idx_products_last_enriched ON products(last_enriched);
        
        -- Categories lookup
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Brands lookup
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Product search cache
        CREATE TABLE IF NOT EXISTS search_cache (
            query_hash TEXT PRIMARY KEY,
            query_text TEXT NOT NULL,
            results TEXT NOT NULL,  -- JSON
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        );
        
        -- Work recommendations
        CREATE TABLE IF NOT EXISTS work_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_type TEXT NOT NULL,
            product_ids TEXT NOT NULL,  -- JSON array
            confidence_score REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Full-text search if enabled
        if self.config.enable_fts:
            fts_sql = """
            -- Full-text search virtual table
            CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
                product_sku, description, category, brand,
                content='products',
                content_rowid='id'
            );
            
            -- Triggers to keep FTS in sync
            CREATE TRIGGER IF NOT EXISTS products_fts_insert AFTER INSERT ON products BEGIN
                INSERT INTO products_fts(rowid, product_sku, description, category, brand)
                VALUES (new.id, new.product_sku, new.description, new.category, new.brand);
            END;
            
            CREATE TRIGGER IF NOT EXISTS products_fts_delete AFTER DELETE ON products BEGIN
                INSERT INTO products_fts(products_fts, rowid, product_sku, description, category, brand)
                VALUES ('delete', old.id, old.product_sku, old.description, old.category, old.brand);
            END;
            
            CREATE TRIGGER IF NOT EXISTS products_fts_update AFTER UPDATE ON products BEGIN
                INSERT INTO products_fts(products_fts, rowid, product_sku, description, category, brand)
                VALUES ('delete', old.id, old.product_sku, old.description, old.category, old.brand);
                INSERT INTO products_fts(rowid, product_sku, description, category, brand)
                VALUES (new.id, new.product_sku, new.description, new.category, new.brand);
            END;
            """
            schema_sql += fts_sql
            
        try:
            with self.pool.get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()
                logger.info("Database schema initialized successfully")
                self.schema_initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise
            
    def import_products_from_excel(self, excel_path: str) -> bool:
        """Import products from Excel file"""
        try:
            import pandas as pd
            
            logger.info(f"Loading products from {excel_path}")
            df = pd.read_excel(excel_path)
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Rename columns to match schema
            column_mapping = {
                'Product SKU': 'product_sku',
                'Description': 'description',
                'Category': 'category',
                'Brand': 'brand',
                'CatalogueItemID': 'catalogue_item_id'
            }
            df = df.rename(columns=column_mapping)
            
            # Clean data
            for col in ['product_sku', 'description', 'category', 'brand']:
                df[col] = df[col].astype(str).str.strip()
                
            # Handle NaN values
            df['catalogue_item_id'] = df['catalogue_item_id'].where(pd.notnull(df['catalogue_item_id']), None)
            
            return self._insert_products_batch(df)
            
        except ImportError:
            logger.error("pandas is required for Excel import. Install with: pip install pandas openpyxl")
            return False
        except Exception as e:
            logger.error(f"Failed to import from Excel: {e}")
            raise RuntimeError(f"Excel import failed: {str(e)}") from e
            
    def _insert_products_batch(self, df) -> bool:
        """Insert products in batches"""
        batch_size = 1000
        
        try:
            with self.pool.get_connection() as conn:
                # Insert unique brands first
                unique_brands = df['brand'].unique()
                for brand in unique_brands:
                    conn.execute(
                        "INSERT OR IGNORE INTO brands (name) VALUES (?)",
                        (brand,)
                    )
                
                # Insert unique categories
                unique_categories = df['category'].unique()
                for category in unique_categories:
                    conn.execute(
                        "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                        (category,)
                    )
                
                # Insert products in batches
                total_rows = len(df)
                for i in range(0, total_rows, batch_size):
                    batch = df.iloc[i:i + batch_size]
                    
                    products_data = []
                    for _, row in batch.iterrows():
                        products_data.append((
                            row['product_sku'],
                            row['description'],
                            row['category'],
                            row['brand'],
                            row['catalogue_item_id']
                        ))
                    
                    conn.executemany("""
                        INSERT OR REPLACE INTO products 
                        (product_sku, description, category, brand, catalogue_item_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, products_data)
                    
                    logger.info(f"Imported batch {i//batch_size + 1}/{(total_rows-1)//batch_size + 1}")
                
                conn.commit()
                
                # Verify import
                cursor = conn.execute("SELECT COUNT(*) FROM products")
                count = cursor.fetchone()[0]
                logger.info(f"Successfully imported {count} products")
                
                return count > 0
                
        except Exception as e:
            logger.error(f"Failed to insert products: {e}")
            raise RuntimeError(f"Product insertion failed: {str(e)}") from e
            
    def search_products(self, query: str, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Search products with optional filters"""
        try:
            with self.pool.get_connection() as conn:
                if self.config.enable_fts and query:
                    # Use full-text search
                    sql = """
                    SELECT p.* FROM products p
                    JOIN products_fts fts ON p.id = fts.rowid
                    WHERE products_fts MATCH ?
                    """
                    params = [query]
                else:
                    # Use LIKE search
                    sql = """
                    SELECT * FROM products 
                    WHERE description LIKE ? OR brand LIKE ? OR category LIKE ?
                    """
                    like_query = f"%{query}%"
                    params = [like_query, like_query, like_query]
                
                # Add filters
                if filters:
                    if 'category' in filters:
                        sql += " AND category = ?"
                        params.append(filters['category'])
                    if 'brand' in filters:
                        sql += " AND brand = ?"
                        params.append(filters['brand'])
                
                sql += f" ORDER BY id LIMIT {limit}"
                
                cursor = conn.execute(sql, params)
                results = []
                for row in cursor.fetchall():
                    results.append(dict(row))
                
                return results
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
            
    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        """Get single product by SKU"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM products WHERE product_sku = ?",
                    (sku,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get product {sku}: {e}")
            raise
            
    def get_products_by_work_type(self, work_type: str, limit: int = 50) -> List[Dict]:
        """Get products recommended for specific work type"""
        # Work type mapping
        work_mappings = {
            'cleaning': ['05 - Cleaning Products'],
            'safety': ['21 - Safety Products'],
            'tools': ['18 - Tools'],
            'cement work': ['18 - Tools'],
            'construction': ['18 - Tools', '21 - Safety Products'],
            'maintenance': ['05 - Cleaning Products', '18 - Tools']
        }
        
        categories = work_mappings.get(work_type.lower(), [])
        if not categories:
            # Fallback to text search
            return self.search_products(work_type, limit=limit)
            
        try:
            with self.pool.get_connection() as conn:
                placeholders = ','.join('?' * len(categories))
                cursor = conn.execute(f"""
                    SELECT * FROM products 
                    WHERE category IN ({placeholders})
                    ORDER BY brand, description
                    LIMIT {limit}
                """, categories)
                
                results = []
                for row in cursor.fetchall():
                    results.append(dict(row))
                return results
                
        except Exception as e:
            logger.error(f"Failed to get products for work type {work_type}: {e}")
            raise
            
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            with self.pool.get_connection() as conn:
                stats = {}
                
                # Total products
                cursor = conn.execute("SELECT COUNT(*) FROM products")
                stats['total_products'] = cursor.fetchone()[0]
                
                # By category
                cursor = conn.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM products 
                    GROUP BY category 
                    ORDER BY count DESC
                """)
                stats['by_category'] = dict(cursor.fetchall())
                
                # By brand (top 10)
                cursor = conn.execute("""
                    SELECT brand, COUNT(*) as count 
                    FROM products 
                    GROUP BY brand 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                stats['top_brands'] = dict(cursor.fetchall())
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise
    
    def update_product_enrichment(self, product_sku: str, enrichment_data: Dict[str, Any]) -> bool:
        """Update product with enrichment data"""
        try:
            with self.pool.get_connection() as conn:
                # Prepare update data
                update_data = {
                    'source_url': enrichment_data.get('source_url'),
                    'enriched_description': enrichment_data.get('enriched_description'),
                    'technical_specs': json.dumps(enrichment_data.get('technical_specs', {})),
                    'supplier_info': json.dumps(enrichment_data.get('supplier_info', {})),
                    'competitor_price': json.dumps(enrichment_data.get('competitor_price', {})),
                    'images_url': json.dumps(enrichment_data.get('images_url', [])),
                    'last_enriched': datetime.now().isoformat(),
                    'enrichment_status': enrichment_data.get('enrichment_status', 'success'),
                    'enrichment_source': enrichment_data.get('enrichment_source', 'unknown'),
                    'updated_at': datetime.now().isoformat()
                }
                
                conn.execute("""
                    UPDATE products SET
                        source_url = ?,
                        enriched_description = ?,
                        technical_specs = ?,
                        supplier_info = ?,
                        competitor_price = ?,
                        images_url = ?,
                        last_enriched = ?,
                        enrichment_status = ?,
                        enrichment_source = ?,
                        updated_at = ?
                    WHERE product_sku = ?
                """, (
                    update_data['source_url'],
                    update_data['enriched_description'],
                    update_data['technical_specs'],
                    update_data['supplier_info'],
                    update_data['competitor_price'],
                    update_data['images_url'],
                    update_data['last_enriched'],
                    update_data['enrichment_status'],
                    update_data['enrichment_source'],
                    update_data['updated_at'],
                    product_sku
                ))
                
                conn.commit()
                return conn.total_changes > 0
                
        except Exception as e:
            logger.error(f"Failed to update enrichment for {product_sku}: {e}")
            raise RuntimeError(f"Enrichment update failed for product {product_sku}: {str(e)}") from e
    
    def get_products_for_enrichment(self, limit: int = 100, source_priority: List[str] = None) -> List[Dict]:
        """Get products that need enrichment"""
        try:
            with self.pool.get_connection() as conn:
                sql = """
                    SELECT * FROM products 
                    WHERE enrichment_status = 'pending' OR enrichment_status IS NULL
                    ORDER BY id
                    LIMIT ?
                """
                
                cursor = conn.execute(sql, (limit,))
                results = []
                for row in cursor.fetchall():
                    results.append(dict(row))
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get products for enrichment: {e}")
            raise
    
    def get_enrichment_statistics(self) -> Dict[str, Any]:
        """Get enrichment statistics"""
        try:
            with self.pool.get_connection() as conn:
                stats = {}
                
                # Total products
                cursor = conn.execute("SELECT COUNT(*) FROM products")
                stats['total_products'] = cursor.fetchone()[0]
                
                # Enrichment status breakdown
                cursor = conn.execute("""
                    SELECT enrichment_status, COUNT(*) as count 
                    FROM products 
                    GROUP BY enrichment_status
                """)
                stats['by_status'] = dict(cursor.fetchall())
                
                # Enrichment source breakdown
                cursor = conn.execute("""
                    SELECT enrichment_source, COUNT(*) as count 
                    FROM products 
                    WHERE enrichment_source IS NOT NULL
                    GROUP BY enrichment_source
                """)
                stats['by_source'] = dict(cursor.fetchall())
                
                # Recently enriched (last 24 hours)
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM products 
                    WHERE last_enriched > datetime('now', '-1 day')
                """)
                stats['enriched_last_24h'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get enrichment statistics: {e}")
            raise
            
    def close(self):
        """Close all database connections"""
        self.pool.close_all()

# Global database instance
_db_instance = None

def get_database(config: DatabaseConfig = None) -> ProductDatabase:
    """Get global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = ProductDatabase(config)
    return _db_instance

def close_database():
    """Close global database instance"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None