"""
SQLite to PostgreSQL Migration Script
Migrates data from multiple SQLite databases to unified PostgreSQL schema
"""

import sqlite3
import psycopg2
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional
import os
from contextlib import contextmanager

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from src.models.production_models import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteToPostgreSQLMigrator:
    """Migrates data from SQLite databases to PostgreSQL using DataFlow"""
    
    def __init__(self):
        # Use environment variable or relative paths
        project_root = Path(__file__).parent.parent.parent
        data_dir = os.getenv('SQLITE_DATA_DIR', str(project_root))

        self.sqlite_databases = {
            'products': os.path.join(data_dir, 'products.db'),
            'quotations': os.path.join(data_dir, 'quotations.db'),
            'documents': os.path.join(data_dir, 'documents.db'),
            'sales_assistant': os.path.join(data_dir, 'sales_assistant.db')
        }
        self.runtime = LocalRuntime()
        
    @contextmanager
    def get_sqlite_connection(self, db_path: str):
        """Get SQLite connection with proper error handling"""
        if not os.path.exists(db_path):
            logger.warning(f"SQLite database not found: {db_path}")
            yield None
            return
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def extract_sqlite_data(self, db_path: str, table_name: str) -> List[Dict[str, Any]]:
        """Extract data from SQLite table"""
        with self.get_sqlite_connection(db_path) as conn:
            if conn is None:
                return []
                
            try:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                # Convert sqlite3.Row to dict
                data = []
                for row in rows:
                    row_dict = {}
                    for key in row.keys():
                        value = row[key]
                        # Handle JSON fields
                        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                            try:
                                value = json.loads(value)
                            except json.JSONDecodeError:
                                pass
                        row_dict[key] = value
                    data.append(row_dict)
                
                logger.info(f"Extracted {len(data)} rows from {table_name}")
                return data
                
            except sqlite3.Error as e:
                logger.error(f"Error extracting from {table_name}: {e}")
                return []
    
    def migrate_categories(self) -> bool:
        """Migrate product categories"""
        logger.info("Migrating categories...")
        
        categories_data = self.extract_sqlite_data(
            self.sqlite_databases['products'], 'categories'
        )
        
        if not categories_data:
            return True
            
        # Process in batches
        batch_size = 100
        for i in range(0, len(categories_data), batch_size):
            batch = categories_data[i:i + batch_size]
            
            # Prepare data for DataFlow
            dataflow_records = []
            for cat in batch:
                record = {
                    'name': cat['name'],
                    'slug': cat['slug'],
                    'description': cat.get('description'),
                    'is_active': bool(cat.get('is_active', True)),
                    'created_at': self._parse_timestamp(cat.get('created_at')),
                    'updated_at': self._parse_timestamp(cat.get('updated_at'))
                }
                dataflow_records.append(record)
            
            # Use DataFlow BulkCreateNode
            workflow = WorkflowBuilder()
            workflow.add_node("CategoryBulkCreateNode", "migrate_categories", {
                "data": dataflow_records,
                "batch_size": batch_size,
                "conflict_resolution": "skip"
            })
            
            try:
                results, run_id = self.runtime.execute(workflow.build())
                logger.info(f"Migrated batch of {len(batch)} categories")
            except Exception as e:
                logger.error(f"Error migrating categories batch: {e}")
                return False
        
        return True
    
    def migrate_brands(self) -> bool:
        """Migrate product brands"""
        logger.info("Migrating brands...")
        
        brands_data = self.extract_sqlite_data(
            self.sqlite_databases['products'], 'brands'
        )
        
        if not brands_data:
            return True
            
        batch_size = 100
        for i in range(0, len(brands_data), batch_size):
            batch = brands_data[i:i + batch_size]
            
            dataflow_records = []
            for brand in batch:
                record = {
                    'name': brand['name'],
                    'slug': brand['slug'], 
                    'description': brand.get('description'),
                    'is_active': bool(brand.get('is_active', True)),
                    'created_at': self._parse_timestamp(brand.get('created_at')),
                    'updated_at': self._parse_timestamp(brand.get('updated_at'))
                }
                dataflow_records.append(record)
            
            workflow = WorkflowBuilder()
            workflow.add_node("BrandBulkCreateNode", "migrate_brands", {
                "data": dataflow_records,
                "batch_size": batch_size,
                "conflict_resolution": "skip"
            })
            
            try:
                results, run_id = self.runtime.execute(workflow.build())
                logger.info(f"Migrated batch of {len(batch)} brands")
            except Exception as e:
                logger.error(f"Error migrating brands batch: {e}")
                return False
        
        return True
    
    def migrate_products(self) -> bool:
        """Migrate products with enrichment data"""
        logger.info("Migrating products...")
        
        products_data = self.extract_sqlite_data(
            self.sqlite_databases['products'], 'products'
        )
        
        if not products_data:
            return True
        
        batch_size = 50  # Smaller batches for products (more complex data)
        for i in range(0, len(products_data), batch_size):
            batch = products_data[i:i + batch_size]
            
            dataflow_records = []
            for product in batch:
                # Parse technical specs if JSON string
                technical_specs = product.get('technical_specs')
                if isinstance(technical_specs, str):
                    try:
                        technical_specs = json.loads(technical_specs)
                    except json.JSONDecodeError:
                        technical_specs = None
                
                # Parse supplier info if JSON string
                supplier_info = product.get('supplier_info')
                if isinstance(supplier_info, str):
                    try:
                        supplier_info = json.loads(supplier_info)
                    except json.JSONDecodeError:
                        supplier_info = None
                
                # Parse import metadata
                import_metadata = product.get('import_metadata')
                if isinstance(import_metadata, str):
                    try:
                        import_metadata = json.loads(import_metadata)
                    except json.JSONDecodeError:
                        import_metadata = None
                
                record = {
                    'sku': product['sku'],
                    'name': product['name'],
                    'slug': product['slug'],
                    'description': product.get('description'),
                    'category_id': product.get('category_id'),
                    'brand_id': product.get('brand_id'),
                    'status': product.get('status', 'active'),
                    'is_published': bool(product.get('is_published', True)),
                    'availability': product.get('availability', 'in_stock'),
                    'currency': product.get('currency', 'USD'),
                    'catalogue_item_id': product.get('catalogue_item_id'),
                    'source_url': product.get('source_url'),
                    'images_url': product.get('images_url'),
                    'enriched_description': product.get('enriched_description'),
                    'technical_specs': technical_specs,
                    'supplier_info': supplier_info,
                    'competitor_data': self._parse_json_field(product.get('competitor_price')),
                    'enrichment_status': product.get('enrichment_status', 'pending'),
                    'enrichment_source': product.get('enrichment_source'),
                    'last_enriched': self._parse_timestamp(product.get('last_enriched')),
                    'import_metadata': import_metadata,
                    'created_at': self._parse_timestamp(product.get('created_at')),
                    'updated_at': self._parse_timestamp(product.get('updated_at'))
                }
                dataflow_records.append(record)
            
            workflow = WorkflowBuilder()
            workflow.add_node("ProductBulkCreateNode", "migrate_products", {
                "data": dataflow_records,
                "batch_size": batch_size,
                "conflict_resolution": "skip"
            })
            
            try:
                results, run_id = self.runtime.execute(workflow.build())
                logger.info(f"Migrated batch of {len(batch)} products")
            except Exception as e:
                logger.error(f"Error migrating products batch: {e}")
                return False
        
        return True
    
    def migrate_work_recommendations(self) -> bool:
        """Migrate work recommendations"""
        logger.info("Migrating work recommendations...")
        
        work_data = self.extract_sqlite_data(
            self.sqlite_databases['products'], 'work_recommendations'
        )
        
        if not work_data:
            return True
            
        batch_size = 100
        for i in range(0, len(work_data), batch_size):
            batch = work_data[i:i + batch_size]
            
            dataflow_records = []
            for work in batch:
                record = {
                    'title': work['title'],
                    'description': work['description'],
                    'category': work.get('category', 'general'),
                    'priority': work.get('priority', 'medium'),
                    'status': work.get('status', 'open'),
                    'estimated_hours': work.get('estimated_hours'),
                    'estimated_value': self._parse_decimal(work.get('estimated_value')),
                    'related_products': self._parse_json_field(work.get('related_products')),
                    'client_requirements': self._parse_json_field(work.get('client_requirements')),
                    'recommendation_source': work.get('recommendation_source', 'manual'),
                    'confidence_score': work.get('confidence_score'),
                    'created_at': self._parse_timestamp(work.get('created_at')),
                    'updated_at': self._parse_timestamp(work.get('updated_at'))
                }
                dataflow_records.append(record)
            
            workflow = WorkflowBuilder()
            workflow.add_node("WorkRecommendationBulkCreateNode", "migrate_work_recs", {
                "data": dataflow_records,
                "batch_size": batch_size,
                "conflict_resolution": "skip"
            })
            
            try:
                results, run_id = self.runtime.execute(workflow.build())
                logger.info(f"Migrated batch of {len(batch)} work recommendations")
            except Exception as e:
                logger.error(f"Error migrating work recommendations batch: {e}")
                return False
        
        return True
    
    def migrate_quotations(self) -> bool:
        """Migrate quotations"""
        logger.info("Migrating quotations...")
        
        quotations_data = self.extract_sqlite_data(
            self.sqlite_databases['quotations'], 'quotations'
        )
        
        if not quotations_data:
            return True
            
        batch_size = 50
        for i in range(0, len(quotations_data), batch_size):
            batch = quotations_data[i:i + batch_size]
            
            dataflow_records = []
            for quot in batch:
                record = {
                    'quotation_number': quot.get('quotation_number', f"QUO-{quot['id']}"),
                    'client_name': quot['client_name'],
                    'client_email': quot.get('client_email'),
                    'project_title': quot.get('project_title', 'Untitled Project'),
                    'total_amount': self._parse_decimal(quot['total_amount']),
                    'currency': quot.get('currency', 'USD'),
                    'status': quot.get('status', 'draft'),
                    'valid_until': self._parse_timestamp(quot.get('valid_until')),
                    'line_items': self._parse_json_field(quot.get('line_items', [])),
                    'terms_conditions': quot.get('terms_conditions'),
                    'notes': quot.get('notes'),
                    'created_at': self._parse_timestamp(quot.get('created_at')),
                    'updated_at': self._parse_timestamp(quot.get('updated_at'))
                }
                dataflow_records.append(record)
            
            workflow = WorkflowBuilder()
            workflow.add_node("QuotationBulkCreateNode", "migrate_quotations", {
                "data": dataflow_records,
                "batch_size": batch_size,
                "conflict_resolution": "skip"
            })
            
            try:
                results, run_id = self.runtime.execute(workflow.build())
                logger.info(f"Migrated batch of {len(batch)} quotations")
            except Exception as e:
                logger.error(f"Error migrating quotations batch: {e}")
                return False
        
        return True
    
    def migrate_customers(self) -> bool:
        """Migrate customer data"""
        logger.info("Migrating customers...")
        
        customers_data = self.extract_sqlite_data(
            self.sqlite_databases['sales_assistant'], 'customers'
        )
        
        if not customers_data:
            return True
            
        batch_size = 100
        for i in range(0, len(customers_data), batch_size):
            batch = customers_data[i:i + batch_size]
            
            dataflow_records = []
            for customer in batch:
                record = {
                    'name': customer['name'],
                    'company_name': customer.get('company_name'),
                    'email': customer['email'],
                    'phone': customer.get('phone'),
                    'address': customer.get('address'),
                    'industry': customer.get('industry'),
                    'customer_type': customer.get('customer_type', 'prospect'),
                    'credit_limit': self._parse_decimal(customer.get('credit_limit')),
                    'payment_terms': customer.get('payment_terms', 'net_30'),
                    'notes': customer.get('notes'),
                    'created_at': self._parse_timestamp(customer.get('created_at')),
                    'updated_at': self._parse_timestamp(customer.get('updated_at'))
                }
                dataflow_records.append(record)
            
            workflow = WorkflowBuilder()
            workflow.add_node("CustomerBulkCreateNode", "migrate_customers", {
                "data": dataflow_records,
                "batch_size": batch_size,
                "conflict_resolution": "skip"
            })
            
            try:
                results, run_id = self.runtime.execute(workflow.build())
                logger.info(f"Migrated batch of {len(batch)} customers")
            except Exception as e:
                logger.error(f"Error migrating customers batch: {e}")
                return False
        
        return True
    
    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        """Parse various timestamp formats"""
        if not value:
            return None
            
        if isinstance(value, datetime):
            return value
            
        if isinstance(value, str):
            # Try common formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        
        return None
    
    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parse decimal values safely"""
        if not value:
            return None
            
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
    
    def _parse_json_field(self, value: Any) -> Optional[Any]:
        """Parse JSON fields safely"""
        if not value:
            return None
            
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        
        return value
    
    def run_migration(self) -> bool:
        """Run complete migration process"""
        logger.info("Starting SQLite to PostgreSQL migration...")
        
        # Initialize PostgreSQL schema
        logger.info("Initializing PostgreSQL schema...")
        try:
            # This will create all tables using DataFlow auto-migration
            db.initialize()
            logger.info("PostgreSQL schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL schema: {e}")
            return False
        
        # Run migrations in order (respecting foreign key dependencies)
        migrations = [
            ("Categories", self.migrate_categories),
            ("Brands", self.migrate_brands), 
            ("Products", self.migrate_products),
            ("Work Recommendations", self.migrate_work_recommendations),
            ("Customers", self.migrate_customers),
            ("Quotations", self.migrate_quotations)
        ]
        
        for migration_name, migration_func in migrations:
            try:
                logger.info(f"Starting {migration_name} migration...")
                success = migration_func()
                if success:
                    logger.info(f"✅ {migration_name} migration completed")
                else:
                    logger.error(f"❌ {migration_name} migration failed")
                    return False
            except Exception as e:
                logger.error(f"❌ {migration_name} migration failed with error: {e}")
                return False
        
        logger.info("🎉 Migration completed successfully!")
        return True

def main():
    """Run migration"""
    migrator = SQLiteToPostgreSQLMigrator()
    success = migrator.run_migration()
    
    if success:
        print("Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update connection strings to use PostgreSQL")
        print("2. Remove SQLite database files")
        print("3. Test application functionality")
    else:
        print("Migration failed. Check logs for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())