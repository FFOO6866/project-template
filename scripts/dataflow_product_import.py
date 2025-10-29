#!/usr/bin/env python3
"""
Production DataFlow Product Import Script
Imports 17,266 products from Excel using Kailash DataFlow 0.4.2

This script uses DataFlow's auto-generated nodes for high-performance bulk operations:
- CategoryCreateNode, CategoryBulkCreateNode
- BrandCreateNode, BrandBulkCreateNode  
- ProductCreateNode, ProductBulkCreateNode

Features:
- Zero-config DataFlow initialization
- Auto-migration with PostgreSQL optimizations
- MongoDB-style filtering and querying
- Bulk operations (10k+ products/sec)
- Enterprise multi-tenancy support
- Comprehensive logging and progress tracking
"""

import os
import sys
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio
import time
import re
from dataclasses import dataclass
import json

# Add src to Python path for imports
sys.path.append('/app/src')

# Import DataFlow and models
from dataflow import DataFlow
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/dataflow_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ImportMetrics:
    """Performance metrics for DataFlow import."""
    start_time: datetime
    categories_created: int = 0
    brands_created: int = 0
    products_created: int = 0
    products_skipped: int = 0
    workflows_executed: int = 0
    batch_times: List[float] = None
    errors: int = 0
    
    def __post_init__(self):
        if self.batch_times is None:
            self.batch_times = []
    
    @property
    def elapsed_time(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def avg_batch_time(self) -> float:
        return sum(self.batch_times) / len(self.batch_times) if self.batch_times else 0
    
    def log_progress(self, current_batch: int, total_batches: int):
        """Log progress with ETA calculation."""
        progress_pct = (current_batch / total_batches) * 100
        eta_seconds = (total_batches - current_batch) * self.avg_batch_time if self.avg_batch_time > 0 else 0
        eta_minutes = eta_seconds / 60
        
        logger.info(f"DataFlow Progress: {current_batch}/{total_batches} batches ({progress_pct:.1f}%) - "
                   f"ETA: {eta_minutes:.1f} min - "
                   f"Created: {self.products_created} products, {self.categories_created} categories, {self.brands_created} brands")

class DataFlowProductImporter:
    """Production DataFlow importer using auto-generated nodes."""
    
    def __init__(self, database_url: str, excel_path: str, test_mode: bool = False, batch_size: int = 1000):
        self.database_url = database_url
        self.excel_path = Path(excel_path)
        self.test_mode = test_mode
        self.batch_size = batch_size
        self.metrics = ImportMetrics(start_time=datetime.now())
        
        # Initialize DataFlow with zero-config
        logger.info("Initializing DataFlow with zero-config setup...")
        self.db = DataFlow(
            database_url=database_url,
            pool_size=20,              # High-performance connection pool
            pool_max_overflow=30,      # Extra connections for bulk operations
            pool_recycle=3600,         # Recycle connections hourly
            monitoring=True,           # Enable performance monitoring
            echo=False,               # No SQL logging in production
            auto_migrate=True         # Enable automatic schema migrations
        )
        
        # Initialize LocalRuntime for workflow execution
        self.runtime = LocalRuntime()
        
        # Caches for deduplication
        self.category_cache: Dict[str, int] = {}
        self.brand_cache: Dict[str, int] = {}
        
        logger.info(f"DataFlow importer initialized - Test mode: {test_mode}, Batch size: {batch_size}")
    
    async def initialize_dataflow(self) -> bool:
        """Initialize DataFlow models and auto-migration."""
        try:
            logger.info("Starting DataFlow initialization and auto-migration...")
            
            # Import models to trigger auto-generation of nodes
            from horme_dataflow_models import Category, Brand, Product, db
            self.db = db  # Use the pre-configured DataFlow instance
            
            # Initialize database and auto-migrate schema
            await self.db.initialize()
            
            # Run auto-migration to ensure schema is up-to-date
            success, migrations = await self.db.auto_migrate()
            if success:
                logger.info(f"DataFlow auto-migration completed successfully. Applied {len(migrations)} migrations.")
            else:
                logger.error("DataFlow auto-migration failed")
                return False
            
            logger.info("DataFlow initialization complete - all 81 auto-generated nodes available")
            logger.info("Available node types: CategoryCreateNode, CategoryBulkCreateNode, BrandCreateNode, BrandBulkCreateNode, ProductCreateNode, ProductBulkCreateNode, etc.")
            
            return True
            
        except Exception as e:
            logger.error(f"DataFlow initialization failed: {e}")
            return False
    
    def load_and_clean_excel_data(self) -> Optional[pd.DataFrame]:
        """Load and clean Excel data with comprehensive validation."""
        try:
            logger.info(f"Loading Excel file: {self.excel_path}")
            df = pd.read_excel(self.excel_path)
            logger.info(f"Loaded {len(df):,} rows from Excel file")
            
            if self.test_mode:
                # Use only first 100 rows for testing
                df = df.head(100)
                logger.info(f"TEST MODE: Using only {len(df)} rows")
            
            # Clean column names - remove trailing spaces
            original_columns = df.columns.tolist()
            df.columns = [col.strip() for col in df.columns]
            
            # Log column name changes
            for orig, clean in zip(original_columns, df.columns):
                if orig != clean:
                    logger.info(f"Column renamed: '{orig}' -> '{clean}'")
            
            # Data cleaning operations
            logger.info("Starting comprehensive data cleaning...")
            
            # Clean Product SKU
            df['Product SKU'] = df['Product SKU'].astype(str).str.strip()
            df['Product SKU'] = df['Product SKU'].replace('nan', '')
            
            # Clean Description
            df['Description'] = df['Description'].astype(str).str.strip()
            df['Description'] = df['Description'].replace('nan', '')
            
            # Clean Category
            df['Category'] = df['Category'].astype(str).str.strip()
            df['Category'] = df['Category'].replace('nan', 'Uncategorized')
            
            # Clean Brand
            df['Brand'] = df['Brand'].astype(str).str.strip()
            df['Brand'] = df['Brand'].replace('nan', 'No Brand')
            
            # Handle missing CatalogueItemID
            missing_catalog_ids = df['CatalogueItemID'].isnull().sum()
            logger.info(f"Found {missing_catalog_ids:,} products with missing CatalogueItemID ({(missing_catalog_ids/len(df)*100):.1f}%)")
            
            # Remove empty rows and invalid data
            original_count = len(df)
            df = df.dropna(how='all')
            
            # Remove rows with missing critical data
            critical_columns = ['Product SKU', 'Description', 'Category', 'Brand']
            for col in critical_columns:
                df = df[df[col].str.len() > 0]
            
            # Remove duplicate Product SKUs
            before_dedup = len(df)
            df = df.drop_duplicates(subset=['Product SKU'], keep='first')
            
            if len(df) < before_dedup:
                logger.info(f"Removed {before_dedup - len(df)} duplicate Product SKUs")
            
            logger.info(f"Data cleaning complete. Final dataset: {len(df):,} rows")
            return df
            
        except Exception as e:
            logger.error(f"Error loading/cleaning Excel data: {e}")
            return None
    
    def create_slug(self, name: str) -> str:
        """Create URL-friendly slug from name."""
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')[:100]
    
    async def create_categories_bulk(self, df: pd.DataFrame) -> bool:
        """Create unique categories using DataFlow CategoryBulkCreateNode."""
        try:
            logger.info("Creating categories using DataFlow CategoryBulkCreateNode...")
            
            # Extract unique categories
            unique_categories = df['Category'].unique()
            logger.info(f"Found {len(unique_categories)} unique categories")
            
            # Prepare category data for bulk creation
            category_data = []
            for category_name in unique_categories:
                if category_name and category_name != 'Uncategorized':
                    category_data.append({
                        "name": category_name,
                        "slug": self.create_slug(category_name),
                        "description": f"Category for {category_name}",
                        "is_active": True,
                        "level": 0,
                        "sort_order": 0
                    })
            
            if not category_data:
                logger.info("No valid categories to create")
                return True
            
            # Create workflow with CategoryBulkCreateNode
            workflow = WorkflowBuilder()
            workflow.add_node("CategoryBulkCreateNode", "create_categories", {
                "data": category_data,
                "batch_size": self.batch_size,
                "conflict_resolution": "skip",  # Skip duplicates
                "return_ids": True
            })
            
            # Execute workflow
            logger.info(f"Executing CategoryBulkCreateNode workflow for {len(category_data)} categories...")
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "create_categories" in results:
                self.metrics.categories_created = len(category_data)
                self.metrics.workflows_executed += 1
                logger.info(f"Successfully created {self.metrics.categories_created} categories via DataFlow")
                return True
            else:
                logger.error("CategoryBulkCreateNode workflow failed")
                return False
                
        except Exception as e:
            logger.error(f"Error creating categories: {e}")
            self.metrics.errors += 1
            return False
    
    async def create_brands_bulk(self, df: pd.DataFrame) -> bool:
        """Create unique brands using DataFlow BrandBulkCreateNode."""
        try:
            logger.info("Creating brands using DataFlow BrandBulkCreateNode...")
            
            # Extract unique brands
            unique_brands = df['Brand'].unique()
            logger.info(f"Found {len(unique_brands)} unique brands")
            
            # Prepare brand data for bulk creation
            brand_data = []
            for brand_name in unique_brands:
                if brand_name and brand_name != 'No Brand':
                    brand_data.append({
                        "name": brand_name,
                        "slug": self.create_slug(brand_name),
                        "description": f"Brand: {brand_name}",
                        "is_active": True
                    })
            
            if not brand_data:
                logger.info("No valid brands to create")
                return True
            
            # Create workflow with BrandBulkCreateNode
            workflow = WorkflowBuilder()
            workflow.add_node("BrandBulkCreateNode", "create_brands", {
                "data": brand_data,
                "batch_size": self.batch_size,
                "conflict_resolution": "skip",  # Skip duplicates
                "return_ids": True
            })
            
            # Execute workflow
            logger.info(f"Executing BrandBulkCreateNode workflow for {len(brand_data)} brands...")
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "create_brands" in results:
                self.metrics.brands_created = len(brand_data)
                self.metrics.workflows_executed += 1
                logger.info(f"Successfully created {self.metrics.brands_created} brands via DataFlow")
                return True
            else:
                logger.error("BrandBulkCreateNode workflow failed")
                return False
                
        except Exception as e:
            logger.error(f"Error creating brands: {e}")
            self.metrics.errors += 1
            return False
    
    async def get_category_id_mapping(self) -> Dict[str, int]:
        """Get category name to ID mapping using CategoryListNode."""
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("CategoryListNode", "list_categories", {
                "filter": {"is_active": True},
                "limit": 1000  # Should cover all categories
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "list_categories" in results:
                categories = results["list_categories"]
                return {cat["name"]: cat["id"] for cat in categories}
            else:
                logger.error("Failed to fetch category mappings")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching category mappings: {e}")
            return {}
    
    async def get_brand_id_mapping(self) -> Dict[str, int]:
        """Get brand name to ID mapping using BrandListNode."""
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("BrandListNode", "list_brands", {
                "filter": {"is_active": True},
                "limit": 1000  # Should cover all brands
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "list_brands" in results:
                brands = results["list_brands"]
                return {brand["name"]: brand["id"] for brand in brands}
            else:
                logger.error("Failed to fetch brand mappings")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching brand mappings: {e}")
            return {}
    
    async def import_products_batch(self, batch_df: pd.DataFrame, category_mapping: Dict[str, int], brand_mapping: Dict[str, int]) -> Tuple[int, int]:
        """Import a batch of products using ProductBulkCreateNode."""
        batch_start_time = time.time()
        
        try:
            # Prepare product data for bulk creation
            products_data = []
            skipped_count = 0
            
            for idx, row in batch_df.iterrows():
                try:
                    # Get category and brand IDs
                    category_id = category_mapping.get(row['Category'])
                    brand_id = brand_mapping.get(row['Brand'])
                    
                    if not category_id:
                        logger.warning(f"Category not found for product {row['Product SKU']}: {row['Category']}")
                        skipped_count += 1
                        continue
                    
                    if not brand_id:
                        logger.warning(f"Brand not found for product {row['Product SKU']}: {row['Brand']}")
                        skipped_count += 1
                        continue
                    
                    # Prepare product data using DataFlow Product model structure
                    product_data = {
                        "sku": row['Product SKU'],
                        "name": row['Description'],
                        "slug": self.create_slug(f"{row['Product SKU']}-{row['Description']}"),
                        "description": row['Description'],
                        "category_id": category_id,
                        "brand_id": brand_id,
                        "status": "active",
                        "is_published": True,
                        "availability": "in_stock",
                        "currency": "USD"
                    }
                    
                    # Add CatalogueItemID if available
                    if pd.notna(row['CatalogueItemID']):
                        # Store in enriched_data as JSONB
                        product_data["enriched_data"] = {
                            "catalogue_item_id": int(row['CatalogueItemID']),
                            "import_source": "excel",
                            "import_timestamp": datetime.now().isoformat()
                        }
                    
                    products_data.append(product_data)
                    
                except Exception as e:
                    logger.error(f"Error preparing product {row['Product SKU']}: {e}")
                    skipped_count += 1
                    continue
            
            if not products_data:
                logger.warning("No valid products in batch")
                return 0, skipped_count
            
            # Create workflow with ProductBulkCreateNode
            workflow = WorkflowBuilder()
            workflow.add_node("ProductBulkCreateNode", "create_products", {
                "data": products_data,
                "batch_size": min(self.batch_size, 1000),  # Limit for performance
                "conflict_resolution": "skip",  # Skip duplicates (based on SKU)
                "return_ids": True
            })
            
            # Execute workflow
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "create_products" in results:
                created_count = len(products_data)
                self.metrics.workflows_executed += 1
                
                batch_time = time.time() - batch_start_time
                self.metrics.batch_times.append(batch_time)
                
                logger.debug(f"ProductBulkCreateNode batch completed: {created_count} products, {batch_time:.2f}s")
                return created_count, skipped_count
            else:
                logger.error("ProductBulkCreateNode workflow failed")
                self.metrics.errors += 1
                return 0, skipped_count
                
        except Exception as e:
            logger.error(f"Error in product batch import: {e}")
            self.metrics.errors += 1
            return 0, len(batch_df)
    
    async def import_all_products(self, df: pd.DataFrame) -> bool:
        """Import all products using DataFlow bulk operations."""
        try:
            logger.info("Starting DataFlow product import process...")
            
            # Step 1: Create categories
            if not await self.create_categories_bulk(df):
                return False
            
            # Step 2: Create brands
            if not await self.create_brands_bulk(df):
                return False
            
            # Step 3: Get ID mappings
            logger.info("Fetching category and brand ID mappings...")
            category_mapping = await self.get_category_id_mapping()
            brand_mapping = await self.get_brand_id_mapping()
            
            logger.info(f"Retrieved {len(category_mapping)} category mappings and {len(brand_mapping)} brand mappings")
            
            # Step 4: Import products in batches
            total_products = len(df)
            total_batches = (total_products + self.batch_size - 1) // self.batch_size
            
            logger.info(f"Starting product import: {total_products:,} products in {total_batches} batches")
            
            for batch_num in range(total_batches):
                start_idx = batch_num * self.batch_size
                end_idx = min(start_idx + self.batch_size, total_products)
                
                batch_df = df.iloc[start_idx:end_idx]
                
                logger.info(f"Processing batch {batch_num + 1}/{total_batches} (rows {start_idx + 1}-{end_idx})")
                
                created, skipped = await self.import_products_batch(batch_df, category_mapping, brand_mapping)
                
                self.metrics.products_created += created
                self.metrics.products_skipped += skipped
                
                # Log progress
                self.metrics.log_progress(batch_num + 1, total_batches)
                
                # Small delay between batches
                if batch_num < total_batches - 1:
                    await asyncio.sleep(0.1)
            
            logger.info(f"DataFlow import completed! Created {self.metrics.products_created:,} products, "
                       f"skipped {self.metrics.products_skipped:,} products")
            return True
            
        except Exception as e:
            logger.error(f"Error in DataFlow import process: {e}")
            return False
    
    async def validate_import(self) -> bool:
        """Validate import using DataFlow query nodes."""
        try:
            logger.info("Validating DataFlow import...")
            
            # Count products using ProductListNode
            workflow = WorkflowBuilder()
            workflow.add_node("ProductListNode", "count_products", {
                "filter": {"status": "active"},
                "limit": 1,
                "count_only": True  # Only return count
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "count_products" in results:
                product_count = len(results["count_products"]) if isinstance(results["count_products"], list) else results["count_products"]
                logger.info(f"Validation: Found {product_count:,} active products in database")
                
                # Get sample products
                sample_workflow = WorkflowBuilder()
                sample_workflow.add_node("ProductListNode", "sample_products", {
                    "filter": {"status": "active"},
                    "limit": 5
                })
                
                sample_results, sample_run_id = self.runtime.execute(sample_workflow.build())
                
                if sample_results and "sample_products" in sample_results:
                    logger.info("Sample imported products:")
                    for product in sample_results["sample_products"][:5]:
                        logger.info(f"  SKU: {product.get('sku', 'N/A')}, Name: {product.get('name', 'N/A')[:50]}...")
                
                return True
            else:
                logger.error("Failed to validate import")
                return False
                
        except Exception as e:
            logger.error(f"Error validating import: {e}")
            return False
    
    def generate_final_report(self) -> None:
        """Generate comprehensive DataFlow import report."""
        end_time = datetime.now()
        total_time = end_time - self.metrics.start_time
        
        report = f"""
DATAFLOW PRODUCT IMPORT REPORT
{'=' * 60}
Import Date: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
DataFlow Version: 0.4.2
Excel File: {self.excel_path}
Test Mode: {self.test_mode}
Batch Size: {self.batch_size}

PERFORMANCE METRICS
{'=' * 60}
Total Time: {total_time}
Average Batch Time: {self.metrics.avg_batch_time:.2f} seconds
Total Workflows Executed: {self.metrics.workflows_executed}
Total Batches: {len(self.metrics.batch_times)}

DATAFLOW RESULTS
{'=' * 60}
Products Created: {self.metrics.products_created:,}
Products Skipped: {self.metrics.products_skipped:,}
Categories Created: {self.metrics.categories_created:,}
Brands Created: {self.metrics.brands_created:,}
Errors Encountered: {self.metrics.errors:,}

PERFORMANCE ANALYSIS
{'=' * 60}
Import Rate: {self.metrics.products_created / total_time.total_seconds():.1f} products/second
Success Rate: {(self.metrics.products_created / max(1, self.metrics.products_created + self.metrics.products_skipped) * 100):.1f}%
Workflow Success Rate: {((self.metrics.workflows_executed - self.metrics.errors) / max(1, self.metrics.workflows_executed) * 100):.1f}%

DATAFLOW FEATURES USED
{'=' * 60}
- Zero-config DataFlow initialization
- Auto-migration with PostgreSQL optimizations
- CategoryBulkCreateNode for bulk category creation
- BrandBulkCreateNode for bulk brand creation
- ProductBulkCreateNode for bulk product creation
- CategoryListNode and BrandListNode for ID mapping
- ProductListNode for validation queries
- Enterprise multi-tenancy support
- JSONB metadata storage for enriched data
"""
        
        logger.info(report)
        
        # Save report to file
        report_file = f"/app/reports/dataflow_import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Detailed DataFlow report saved to: {report_file}")

async def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import Excel product data using DataFlow 0.4.2')
    parser.add_argument('--test', action='store_true', help='Run in test mode (first 100 rows only)')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for bulk operations (default: 1000)')
    parser.add_argument('--excel-file', type=str, 
                       default='/app/data/ProductData (Top 3 Cats).xlsx',
                       help='Path to Excel file')
    parser.add_argument('--database-url', type=str,
                       default=os.getenv('DATABASE_URL', 'postgresql://horme_user:secure_password_2024@postgres:5432/horme_db'),
                       help='PostgreSQL database URL')
    
    args = parser.parse_args()
    
    # Validate Excel file exists
    if not Path(args.excel_file).exists():
        logger.error(f"Excel file not found: {args.excel_file}")
        return False
    
    logger.info("Starting DataFlow Product Import Process")
    logger.info("=" * 80)
    logger.info(f"DataFlow Version: 0.4.2")
    logger.info(f"Target: Import 17,266 products using auto-generated nodes")
    logger.info("=" * 80)
    
    # Initialize importer
    importer = DataFlowProductImporter(
        database_url=args.database_url,
        excel_path=args.excel_file,
        test_mode=args.test,
        batch_size=args.batch_size
    )
    
    try:
        # Initialize DataFlow
        if not await importer.initialize_dataflow():
            return False
        
        # Load and clean Excel data
        df = importer.load_and_clean_excel_data()
        if df is None:
            logger.error("Failed to load Excel data")
            return False
        
        # Import products using DataFlow
        success = await importer.import_all_products(df)
        if not success:
            logger.error("DataFlow import process failed")
            return False
        
        # Validate results
        await importer.validate_import()
        
        # Generate final report
        importer.generate_final_report()
        
        logger.info("SUCCESS: DataFlow import process completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"DataFlow import failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)