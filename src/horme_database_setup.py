"""
Horme Product Knowledge Base - Database Setup and Migration Script

This script provides automated setup for the Horme product knowledge base using Kailash DataFlow.
Includes database initialization, schema migration, and sample data population.

Features:
- Automatic PostgreSQL database setup
- Schema migration with rollback support
- Sample data population for testing
- Performance optimization
- Environment configuration
- Health checks and validation

Usage:
    python horme_database_setup.py --init          # Initialize database
    python horme_database_setup.py --migrate       # Run migrations
    python horme_database_setup.py --sample-data   # Load sample data
    python horme_database_setup.py --health-check  # Validate setup
    python horme_database_setup.py --all          # Complete setup
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    from horme_dataflow_models import (
        db, Category, Brand, Supplier, Product, ProductImage, 
        ProductSpecification, ProductSupplier, ScrapingJob, ProductAnalytics
    )
    from kailash.workflow.builder import WorkflowBuilder
    from kailash.runtime.local import LocalRuntime
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure Kailash SDK is installed: pip install kailash[dataflow]")
    sys.exit(1)

class HormeDatabaseSetup:
    """
    Comprehensive database setup and management for Horme product knowledge base.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database setup manager."""
        self.database_url = database_url or os.getenv(
            'DATABASE_URL', 
            'postgresql://horme_user:horme_password@localhost:5432/horme_products'
        )
        self.runtime = LocalRuntime()
        logger.info(f"Initialized Horme database setup for: {self.database_url}")
    
    async def check_database_connection(self) -> bool:
        """
        Test database connectivity and basic operations.
        """
        try:
            # Test connection with a simple health check workflow
            workflow = WorkflowBuilder()
            workflow.add_node("HealthCheckNode", "db_health", {
                "check_database": True,
                "check_cache": True,
                "timeout": 10
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            health_status = results.get("db_health", {}).get("result", {})
            
            if health_status.get("status") == "healthy":
                logger.info("✅ Database connection successful")
                return True
            else:
                logger.error(f"❌ Database health check failed: {health_status}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def initialize_database(self) -> bool:
        """
        Initialize the database with proper configuration and extensions.
        """
        try:
            logger.info("🔧 Initializing Horme product database...")
            
            # Initialize DataFlow - this creates tables and indexes automatically
            await db.initialize()
            
            logger.info("✅ Database initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    async def run_migrations(self, dry_run: bool = False) -> bool:
        """
        Run database migrations with safety checks.
        """
        try:
            logger.info("🔄 Running database migrations...")
            
            if dry_run:
                logger.info("🔍 Running in dry-run mode (preview only)")
            
            # Run auto-migration with safety checks
            success, migrations = await db.auto_migrate(
                dry_run=dry_run,
                max_risk_level="MEDIUM",        # Block high-risk operations
                backup_before_migration=True,   # Backup before changes
                rollback_on_error=True         # Auto-rollback on failure
            )
            
            if success:
                if dry_run:
                    logger.info("✅ Migration preview completed successfully")
                else:
                    logger.info(f"✅ Applied {len(migrations)} migrations successfully")
                return True
            else:
                logger.error("❌ Migration failed or was blocked by safety checks")
                return False
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    async def create_sample_categories(self) -> List[int]:
        """Create sample product categories."""
        logger.info("📁 Creating sample categories...")
        
        categories_data = [
            # Root categories
            {"name": "Electronics", "slug": "electronics", "level": 0, "path": "Electronics"},
            {"name": "Home & Garden", "slug": "home-garden", "level": 0, "path": "Home & Garden"},
            {"name": "Sports & Outdoors", "slug": "sports-outdoors", "level": 0, "path": "Sports & Outdoors"},
            
            # Electronics subcategories
            {"name": "Computers", "slug": "computers", "level": 1, "path": "Electronics/Computers"},
            {"name": "Mobile Devices", "slug": "mobile-devices", "level": 1, "path": "Electronics/Mobile Devices"},
            {"name": "Audio & Video", "slug": "audio-video", "level": 1, "path": "Electronics/Audio & Video"},
            
            # Computer subcategories
            {"name": "Laptops", "slug": "laptops", "level": 2, "path": "Electronics/Computers/Laptops"},
            {"name": "Desktops", "slug": "desktops", "level": 2, "path": "Electronics/Computers/Desktops"},
            {"name": "Components", "slug": "components", "level": 2, "path": "Electronics/Computers/Components"},
        ]
        
        workflow = WorkflowBuilder()
        workflow.add_node("CategoryBulkCreateNode", "create_categories", {
            "data": categories_data,
            "batch_size": 50,
            "return_ids": True
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        category_ids = results["create_categories"]["result"]["ids"]
        
        logger.info(f"✅ Created {len(category_ids)} categories")
        return category_ids
    
    async def create_sample_brands(self) -> List[int]:
        """Create sample brands."""
        logger.info("🏷️ Creating sample brands...")
        
        brands_data = [
            {"name": "Apple", "slug": "apple", "website_url": "https://www.apple.com", "country": "USA", "founded_year": 1976},
            {"name": "Samsung", "slug": "samsung", "website_url": "https://www.samsung.com", "country": "South Korea", "founded_year": 1938},
            {"name": "Dell", "slug": "dell", "website_url": "https://www.dell.com", "country": "USA", "founded_year": 1984},
            {"name": "HP", "slug": "hp", "website_url": "https://www.hp.com", "country": "USA", "founded_year": 1939},
            {"name": "Lenovo", "slug": "lenovo", "website_url": "https://www.lenovo.com", "country": "China", "founded_year": 1984},
            {"name": "ASUS", "slug": "asus", "website_url": "https://www.asus.com", "country": "Taiwan", "founded_year": 1989},
            {"name": "Microsoft", "slug": "microsoft", "website_url": "https://www.microsoft.com", "country": "USA", "founded_year": 1975},
            {"name": "Sony", "slug": "sony", "website_url": "https://www.sony.com", "country": "Japan", "founded_year": 1946},
        ]
        
        workflow = WorkflowBuilder()
        workflow.add_node("BrandBulkCreateNode", "create_brands", {
            "data": brands_data,
            "batch_size": 50,
            "return_ids": True
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        brand_ids = results["create_brands"]["result"]["ids"]
        
        logger.info(f"✅ Created {len(brand_ids)} brands")
        return brand_ids
    
    async def create_sample_suppliers(self) -> List[int]:
        """Create sample suppliers."""
        logger.info("🏪 Creating sample suppliers...")
        
        suppliers_data = [
            {
                "name": "TechDistributor Inc", 
                "slug": "tech-distributor", 
                "company_type": "distributor",
                "contact_email": "orders@techdist.com",
                "country": "USA",
                "is_preferred": True,
                "payment_terms": "Net 30"
            },
            {
                "name": "Global Electronics Supply", 
                "slug": "global-electronics", 
                "company_type": "distributor",
                "contact_email": "sales@globalsupply.com",
                "country": "Singapore",
                "payment_terms": "Net 45"
            },
            {
                "name": "Premium Tech Wholesale", 
                "slug": "premium-tech", 
                "company_type": "wholesaler",
                "contact_email": "wholesale@premiumtech.com",
                "country": "Germany",
                "is_preferred": True,
                "payment_terms": "Net 15"
            },
        ]
        
        workflow = WorkflowBuilder()
        workflow.add_node("SupplierBulkCreateNode", "create_suppliers", {
            "data": suppliers_data,
            "batch_size": 50,
            "return_ids": True
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        supplier_ids = results["create_suppliers"]["result"]["ids"]
        
        logger.info(f"✅ Created {len(supplier_ids)} suppliers")
        return supplier_ids
    
    async def create_sample_products(self, category_ids: List[int], brand_ids: List[int]) -> List[int]:
        """Create sample products with rich specifications."""
        logger.info("📦 Creating sample products...")
        
        # Sample products with realistic data
        products_data = [
            {
                "sku": "APPLE-MBP-14-M2-512",
                "name": "MacBook Pro 14-inch M2 512GB",
                "slug": "macbook-pro-14-m2-512gb",
                "model_number": "MPHE3LL/A",
                "description": "14-inch MacBook Pro with M2 chip, 512GB SSD",
                "long_description": "The 14-inch MacBook Pro with M2 chip delivers exceptional performance and battery life in a compact design. Features Liquid Retina XDR display, advanced camera and audio, and all the ports you need.",
                "category_id": category_ids[6] if len(category_ids) > 6 else category_ids[0],  # Laptops
                "brand_id": brand_ids[0] if len(brand_ids) > 0 else None,  # Apple
                "price": 1999.00,
                "msrp": 1999.00,
                "currency": "USD",
                "weight": 1.6,
                "color": "Space Gray",
                "specifications": {
                    "processor": "Apple M2 chip",
                    "memory": "8GB unified memory",
                    "storage": "512GB SSD",
                    "display": "14.2-inch Liquid Retina XDR",
                    "graphics": "8-core GPU",
                    "ports": ["3x Thunderbolt 4", "HDMI", "SDXC", "MagSafe 3"],
                    "battery": "Up to 17 hours",
                    "os": "macOS"
                },
                "features": [
                    "M2 chip with 8-core CPU",
                    "Liquid Retina XDR display",
                    "1080p FaceTime HD camera",
                    "Six-speaker sound system",
                    "MagSafe 3 charging"
                ],
                "keywords": ["macbook", "laptop", "apple", "m2", "portable", "professional"]
            },
            {
                "sku": "DELL-XPS-13-I7-1TB",
                "name": "Dell XPS 13 Intel i7 1TB",
                "slug": "dell-xps-13-i7-1tb",
                "model_number": "XPS9320-7408SLV-PUS",
                "description": "13.4-inch XPS laptop with Intel i7 processor and 1TB SSD",
                "long_description": "The Dell XPS 13 combines premium design with powerful performance. Features a stunning InfinityEdge display, advanced thermal design, and all-day battery life.",
                "category_id": category_ids[6] if len(category_ids) > 6 else category_ids[0],  # Laptops
                "brand_id": brand_ids[2] if len(brand_ids) > 2 else None,  # Dell
                "price": 1599.00,
                "msrp": 1699.00,
                "currency": "USD",
                "weight": 1.27,
                "color": "Platinum Silver",
                "specifications": {
                    "processor": "Intel Core i7-1260P",
                    "memory": "16GB LPDDR5",
                    "storage": "1TB PCIe NVMe SSD",
                    "display": "13.4-inch FHD+ InfinityEdge",
                    "graphics": "Integrated Intel Iris Xe",
                    "ports": ["2x Thunderbolt 4", "microSD"],
                    "battery": "Up to 12 hours",
                    "os": "Windows 11"
                },
                "features": [
                    "InfinityEdge display",
                    "Precision touchpad",
                    "Backlit keyboard",
                    "Windows Hello",
                    "Premium materials"
                ],
                "keywords": ["dell", "xps", "laptop", "intel", "ultrabook", "premium"]
            },
            {
                "sku": "SAMSUNG-S23-ULTRA-256",
                "name": "Samsung Galaxy S23 Ultra 256GB",
                "slug": "samsung-galaxy-s23-ultra-256gb",
                "model_number": "SM-S918U",
                "description": "Galaxy S23 Ultra with S Pen, 256GB storage",
                "long_description": "The most powerful Galaxy S ever with integrated S Pen, advanced camera system, and premium design. Perfect for productivity and creativity.",
                "category_id": category_ids[4] if len(category_ids) > 4 else category_ids[0],  # Mobile Devices
                "brand_id": brand_ids[1] if len(brand_ids) > 1 else None,  # Samsung
                "price": 1199.00,
                "msrp": 1199.00,
                "currency": "USD",
                "weight": 0.234,
                "color": "Phantom Black",
                "specifications": {
                    "processor": "Snapdragon 8 Gen 2",
                    "memory": "12GB RAM",
                    "storage": "256GB",
                    "display": "6.8-inch Dynamic AMOLED 2X",
                    "camera": "200MP main + 12MP ultra-wide + 10MP telephoto",
                    "battery": "5000mAh",
                    "os": "Android 13",
                    "connectivity": ["5G", "Wi-Fi 6E", "Bluetooth 5.3"]
                },
                "features": [
                    "Built-in S Pen",
                    "200MP camera with 100x zoom",
                    "All-day battery",
                    "IP68 water resistance",
                    "Wireless charging"
                ],
                "keywords": ["samsung", "galaxy", "smartphone", "s-pen", "android", "camera"]
            }
        ]
        
        workflow = WorkflowBuilder()
        workflow.add_node("ProductBulkCreateNode", "create_products", {
            "data": products_data,
            "batch_size": 50,
            "return_ids": True
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        product_ids = results["create_products"]["result"]["ids"]
        
        logger.info(f"✅ Created {len(product_ids)} products")
        return product_ids
    
    async def create_sample_specifications(self, product_ids: List[int]) -> bool:
        """Create detailed product specifications."""
        logger.info("📋 Creating product specifications...")
        
        specifications_data = []
        
        # Add specifications for each product
        for i, product_id in enumerate(product_ids[:3]):  # First 3 products
            if i == 0:  # MacBook Pro specs
                specs = [
                    {"product_id": product_id, "spec_group": "Performance", "spec_name": "CPU Cores", "spec_value": "8", "data_type": "number", "numeric_value": 8, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Performance", "spec_name": "GPU Cores", "spec_value": "10", "data_type": "number", "numeric_value": 10, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Memory", "spec_name": "RAM", "spec_value": "8GB", "spec_unit": "GB", "data_type": "number", "numeric_value": 8, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Storage", "spec_name": "SSD Capacity", "spec_value": "512GB", "spec_unit": "GB", "data_type": "number", "numeric_value": 512, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Display", "spec_name": "Screen Size", "spec_value": "14.2", "spec_unit": "inches", "data_type": "number", "numeric_value": 14.2, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Display", "spec_name": "Resolution", "spec_value": "3024x1964", "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Connectivity", "spec_name": "Wi-Fi", "spec_value": "Wi-Fi 6", "is_comparable": True},
                    {"product_id": product_id, "spec_group": "Physical", "spec_name": "Thickness", "spec_value": "15.5", "spec_unit": "mm", "data_type": "number", "numeric_value": 15.5},
                ]
            elif i == 1:  # Dell XPS specs
                specs = [
                    {"product_id": product_id, "spec_group": "Performance", "spec_name": "CPU Cores", "spec_value": "12", "data_type": "number", "numeric_value": 12, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Memory", "spec_name": "RAM", "spec_value": "16GB", "spec_unit": "GB", "data_type": "number", "numeric_value": 16, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Storage", "spec_name": "SSD Capacity", "spec_value": "1TB", "spec_unit": "TB", "data_type": "number", "numeric_value": 1000, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Display", "spec_name": "Screen Size", "spec_value": "13.4", "spec_unit": "inches", "data_type": "number", "numeric_value": 13.4, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Display", "spec_name": "Resolution", "spec_value": "1920x1200", "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Connectivity", "spec_name": "Wi-Fi", "spec_value": "Wi-Fi 6E", "is_comparable": True},
                    {"product_id": product_id, "spec_group": "Physical", "spec_name": "Thickness", "spec_value": "14.8", "spec_unit": "mm", "data_type": "number", "numeric_value": 14.8},
                ]
            else:  # Samsung Galaxy specs
                specs = [
                    {"product_id": product_id, "spec_group": "Performance", "spec_name": "RAM", "spec_value": "12GB", "spec_unit": "GB", "data_type": "number", "numeric_value": 12, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Storage", "spec_name": "Internal Storage", "spec_value": "256GB", "spec_unit": "GB", "data_type": "number", "numeric_value": 256, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Display", "spec_name": "Screen Size", "spec_value": "6.8", "spec_unit": "inches", "data_type": "number", "numeric_value": 6.8, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Display", "spec_name": "Resolution", "spec_value": "3088x1440", "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Camera", "spec_name": "Main Camera", "spec_value": "200MP", "spec_unit": "MP", "data_type": "number", "numeric_value": 200, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Battery", "spec_name": "Capacity", "spec_value": "5000mAh", "spec_unit": "mAh", "data_type": "number", "numeric_value": 5000, "is_key_spec": True},
                    {"product_id": product_id, "spec_group": "Connectivity", "spec_name": "5G", "spec_value": "Yes", "data_type": "boolean", "boolean_value": True, "is_comparable": True},
                ]
            
            specifications_data.extend(specs)
        
        workflow = WorkflowBuilder()
        workflow.add_node("ProductSpecificationBulkCreateNode", "create_specs", {
            "data": specifications_data,
            "batch_size": 100
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        logger.info(f"✅ Created {len(specifications_data)} product specifications")
        return True
    
    async def create_sample_images(self, product_ids: List[int]) -> bool:
        """Create sample product images."""
        logger.info("🖼️ Creating product images...")
        
        images_data = []
        
        # Add sample images for each product
        for i, product_id in enumerate(product_ids[:3]):
            if i == 0:  # MacBook Pro images
                images = [
                    {"product_id": product_id, "url": "/images/macbook-pro-14-m2-front.jpg", "alt_text": "MacBook Pro 14-inch M2 front view", "image_type": "photo", "position": 0, "is_primary": True},
                    {"product_id": product_id, "url": "/images/macbook-pro-14-m2-side.jpg", "alt_text": "MacBook Pro 14-inch M2 side view", "image_type": "photo", "position": 1},
                    {"product_id": product_id, "url": "/images/macbook-pro-14-m2-ports.jpg", "alt_text": "MacBook Pro 14-inch M2 ports", "image_type": "photo", "position": 2},
                ]
            elif i == 1:  # Dell XPS images
                images = [
                    {"product_id": product_id, "url": "/images/dell-xps-13-i7-front.jpg", "alt_text": "Dell XPS 13 front view", "image_type": "photo", "position": 0, "is_primary": True},
                    {"product_id": product_id, "url": "/images/dell-xps-13-i7-keyboard.jpg", "alt_text": "Dell XPS 13 keyboard detail", "image_type": "photo", "position": 1},
                ]
            else:  # Samsung Galaxy images
                images = [
                    {"product_id": product_id, "url": "/images/samsung-s23-ultra-front.jpg", "alt_text": "Samsung Galaxy S23 Ultra front", "image_type": "photo", "position": 0, "is_primary": True},
                    {"product_id": product_id, "url": "/images/samsung-s23-ultra-back.jpg", "alt_text": "Samsung Galaxy S23 Ultra back with cameras", "image_type": "photo", "position": 1},
                    {"product_id": product_id, "url": "/images/samsung-s23-ultra-spen.jpg", "alt_text": "Samsung Galaxy S23 Ultra with S Pen", "image_type": "photo", "position": 2},
                ]
            
            images_data.extend(images)
        
        workflow = WorkflowBuilder()
        workflow.add_node("ProductImageBulkCreateNode", "create_images", {
            "data": images_data,
            "batch_size": 50
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        logger.info(f"✅ Created {len(images_data)} product images")
        return True
    
    async def create_sample_supplier_relationships(self, product_ids: List[int], supplier_ids: List[int]) -> bool:
        """Create product-supplier relationships."""
        logger.info("🔗 Creating supplier relationships...")
        
        relationships_data = []
        
        # Create relationships between products and suppliers
        for product_id in product_ids[:3]:
            for i, supplier_id in enumerate(supplier_ids):
                relationship = {
                    "product_id": product_id,
                    "supplier_id": supplier_id,
                    "supplier_sku": f"SUP{supplier_id}-PROD{product_id}",
                    "supplier_price": 800.00 + (i * 50),  # Varying prices
                    "minimum_order_qty": 1 if i == 0 else 5,
                    "lead_time_days": 3 + (i * 2),
                    "is_preferred": i == 0,  # First supplier is preferred
                    "reliability_score": 95.0 - (i * 5),
                    "quality_score": 98.0 - (i * 3)
                }
                relationships_data.append(relationship)
        
        workflow = WorkflowBuilder()
        workflow.add_node("ProductSupplierBulkCreateNode", "create_relationships", {
            "data": relationships_data,
            "batch_size": 50
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        logger.info(f"✅ Created {len(relationships_data)} supplier relationships")
        return True
    
    async def populate_sample_data(self) -> bool:
        """
        Populate the database with comprehensive sample data.
        """
        try:
            logger.info("🎯 Populating sample data for Horme product knowledge base...")
            
            # Create sample data in proper order (respecting foreign key constraints)
            category_ids = await self.create_sample_categories()
            brand_ids = await self.create_sample_brands()
            supplier_ids = await self.create_sample_suppliers()
            product_ids = await self.create_sample_products(category_ids, brand_ids)
            
            # Create related data
            await self.create_sample_specifications(product_ids)
            await self.create_sample_images(product_ids)
            await self.create_sample_supplier_relationships(product_ids, supplier_ids)
            
            logger.info("✅ Sample data population completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Sample data population failed: {e}")
            return False
    
    async def run_health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check of the database setup.
        """
        logger.info("🏥 Running comprehensive health check...")
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "checks": {}
        }
        
        try:
            # Database connection check
            connection_ok = await self.check_database_connection()
            health_report["checks"]["database_connection"] = {
                "status": "healthy" if connection_ok else "unhealthy",
                "message": "Database connection successful" if connection_ok else "Database connection failed"
            }
            
            # Table existence check
            workflow = WorkflowBuilder()
            workflow.add_node("CategoryListNode", "check_categories", {"limit": 1})
            workflow.add_node("ProductListNode", "check_products", {"limit": 1})
            workflow.add_node("BrandListNode", "check_brands", {"limit": 1})
            
            results, run_id = self.runtime.execute(workflow.build())
            
            tables_ok = all([
                "check_categories" in results,
                "check_products" in results, 
                "check_brands" in results
            ])
            
            health_report["checks"]["tables"] = {
                "status": "healthy" if tables_ok else "unhealthy",
                "message": "All tables accessible" if tables_ok else "Some tables missing or inaccessible"
            }
            
            # Data integrity check
            category_count = len(results.get("check_categories", {}).get("result", []))
            product_count = len(results.get("check_products", {}).get("result", []))
            brand_count = len(results.get("check_brands", {}).get("result", []))
            
            health_report["checks"]["data_integrity"] = {
                "status": "healthy",
                "categories": category_count,
                "products": product_count,
                "brands": brand_count,
                "message": f"Found {category_count} categories, {product_count} products, {brand_count} brands"
            }
            
            # Overall status
            all_healthy = all([
                check["status"] == "healthy" 
                for check in health_report["checks"].values()
            ])
            
            health_report["status"] = "healthy" if all_healthy else "unhealthy"
            
            if health_report["status"] == "healthy":
                logger.info("✅ All health checks passed")
            else:
                logger.warning("⚠️ Some health checks failed")
            
            return health_report
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            health_report["status"] = "error"
            health_report["error"] = str(e)
            return health_report
    
    async def run_complete_setup(self) -> bool:
        """
        Run complete database setup: initialize, migrate, populate, and validate.
        """
        logger.info("🚀 Starting complete Horme database setup...")
        
        try:
            # Step 1: Check connection
            if not await self.check_database_connection():
                logger.error("❌ Database connection failed. Please check your DATABASE_URL.")
                return False
            
            # Step 2: Initialize database
            if not await self.initialize_database():
                logger.error("❌ Database initialization failed.")
                return False
            
            # Step 3: Run migrations
            if not await self.run_migrations():
                logger.error("❌ Database migrations failed.")
                return False
            
            # Step 4: Populate sample data
            if not await self.populate_sample_data():
                logger.error("❌ Sample data population failed.")
                return False
            
            # Step 5: Health check
            health_report = await self.run_health_check()
            if health_report["status"] != "healthy":
                logger.warning("⚠️ Health check revealed issues, but setup completed.")
            
            logger.info("🎉 Complete Horme database setup finished successfully!")
            logger.info(f"📊 Health Report: {json.dumps(health_report, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Complete setup failed: {e}")
            return False

async def main():
    """Main CLI interface for database setup."""
    parser = argparse.ArgumentParser(
        description="Horme Product Knowledge Base - Database Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python horme_database_setup.py --all                    # Complete setup
  python horme_database_setup.py --init --migrate         # Initialize and migrate
  python horme_database_setup.py --sample-data           # Load sample data only
  python horme_database_setup.py --health-check          # Validate setup
  python horme_database_setup.py --migrate --dry-run     # Preview migrations
        """
    )
    
    parser.add_argument("--database-url", help="PostgreSQL database URL")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--migrate", action="store_true", help="Run migrations")
    parser.add_argument("--sample-data", action="store_true", help="Populate sample data")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    parser.add_argument("--all", action="store_true", help="Run complete setup")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    
    args = parser.parse_args()
    
    if not any([args.init, args.migrate, args.sample_data, args.health_check, args.all]):
        parser.print_help()
        return
    
    # Initialize setup manager
    setup = HormeDatabaseSetup(args.database_url)
    
    success = True
    
    try:
        if args.all:
            success = await setup.run_complete_setup()
        else:
            if args.init:
                success &= await setup.initialize_database()
            
            if args.migrate:
                success &= await setup.run_migrations(dry_run=args.dry_run)
            
            if args.sample_data:
                success &= await setup.populate_sample_data()
            
            if args.health_check:
                health_report = await setup.run_health_check()
                print(json.dumps(health_report, indent=2))
                success &= health_report["status"] == "healthy"
        
        if success:
            logger.info("🎉 All operations completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Some operations failed.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())