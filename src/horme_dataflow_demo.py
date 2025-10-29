"""
Horme Product Knowledge Base - DataFlow Usage Demonstration

This script demonstrates how to use the auto-generated DataFlow nodes for the Horme
product knowledge base. Shows practical examples of CRUD operations, complex queries,
and bulk operations using the 81 auto-generated nodes.

Key Features Demonstrated:
- Auto-generated CRUD nodes (9 per model × 9 models = 81 nodes)
- MongoDB-style queries on PostgreSQL
- Bulk operations for high performance
- Complex filtering and aggregation
- Product search and specification queries
- Web scraping data management
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

# Import the DataFlow models and workflow components
from horme_dataflow_models import db
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

class HormeDataFlowDemo:
    """
    Demonstration of Horme product knowledge base operations using DataFlow.
    """
    
    def __init__(self):
        self.runtime = LocalRuntime()
    
    def create_workflow(self) -> WorkflowBuilder:
        """Create a new workflow builder."""
        return WorkflowBuilder()
    
    async def demo_basic_crud_operations(self):
        """
        Demonstrate basic CRUD operations using auto-generated nodes.
        Each model automatically provides: Create, Read, Update, Delete, List nodes.
        """
        print("🔧 Demo: Basic CRUD Operations")
        print("=" * 50)
        
        workflow = self.create_workflow()
        
        # 1. Create a new category (CategoryCreateNode)
        workflow.add_node("CategoryCreateNode", "create_category", {
            "name": "Gaming Laptops",
            "slug": "gaming-laptops",
            "description": "High-performance laptops for gaming",
            "level": 2,
            "path": "Electronics/Computers/Gaming Laptops",
            "metadata": {
                "target_audience": "gamers",
                "performance_tier": "high",
                "price_range": "premium"
            }
        })
        
        # 2. Create a brand (BrandCreateNode)  
        workflow.add_node("BrandCreateNode", "create_brand", {
            "name": "NVIDIA",
            "slug": "nvidia",
            "description": "Graphics processing and AI computing",
            "website_url": "https://www.nvidia.com",
            "country": "USA",
            "founded_year": 1993
        })
        
        # 3. Create a product (ProductCreateNode) with rich specifications
        workflow.add_node("ProductCreateNode", "create_product", {
            "sku": "ASUS-ROG-STRIX-G15",
            "name": "ASUS ROG Strix G15 Gaming Laptop",
            "slug": "asus-rog-strix-g15",
            "model_number": "G513QM-HN063T",
            "description": "15.6-inch gaming laptop with RTX 3060",
            "long_description": "Powerful gaming laptop with AMD Ryzen 7, NVIDIA RTX 3060, 144Hz display, and RGB keyboard for immersive gaming experience.",
            "price": 1299.99,
            "msrp": 1399.99,
            "specifications": {
                "processor": "AMD Ryzen 7 5800H",
                "graphics": "NVIDIA GeForce RTX 3060 6GB",
                "memory": "16GB DDR4",
                "storage": "1TB PCIe NVMe SSD",
                "display": "15.6-inch FHD 144Hz IPS",
                "keyboard": "RGB Backlit",
                "ports": ["USB 3.2", "USB-C", "HDMI 2.0", "RJ45"],
                "battery": "90Wh 4-cell",
                "weight": "2.3kg"
            },
            "features": [
                "144Hz high refresh rate display",
                "RGB per-key keyboard",
                "Intelligent cooling system",
                "DTS:X Ultra audio",
                "WiFi 6 support"
            ],
            "keywords": ["gaming", "laptop", "asus", "rog", "rtx", "amd", "ryzen"]
        })
        
        # Connect category and brand to product
        workflow.add_connection("create_category", "id", "create_product", "category_id")
        workflow.add_connection("create_brand", "id", "create_product", "brand_id")
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        print(f"✅ Created category: {results['create_category']['result']['name']}")
        print(f"✅ Created brand: {results['create_brand']['result']['name']}")
        print(f"✅ Created product: {results['create_product']['result']['name']}")
        print(f"   SKU: {results['create_product']['result']['sku']}")
        print(f"   Price: ${results['create_product']['result']['price']}")
        print()
        
        return results
    
    async def demo_advanced_queries(self):
        """
        Demonstrate advanced MongoDB-style queries on PostgreSQL using DataFlow.
        """
        print("🔍 Demo: Advanced Query Operations")
        print("=" * 50)
        
        workflow = self.create_workflow()
        
        # 1. Complex product search with multiple filters (ProductListNode)
        workflow.add_node("ProductListNode", "search_gaming_laptops", {
            "filter": {
                # JSONB queries on specifications
                "specifications.graphics": {"$regex": "RTX|GeForce"},
                "specifications.memory": {"$regex": "16GB|32GB"},
                # Price range filtering
                "price": {"$gte": 1000, "$lte": 2000},
                # Status filtering
                "status": "active",
                "is_published": True,
                # Feature matching
                "features": {"$contains": "gaming"}
            },
            "order_by": ["-price", "name"],  # Sort by price desc, then name asc
            "limit": 10
        })
        
        # 2. Category hierarchy search (CategoryListNode)
        workflow.add_node("CategoryListNode", "search_categories", {
            "filter": {
                "path": {"$regex": "Electronics"},
                "level": {"$gte": 1},
                "is_active": True
            },
            "order_by": ["level", "sort_order"]
        })
        
        # 3. Brand search with country filtering (BrandListNode)
        workflow.add_node("BrandListNode", "search_brands", {
            "filter": {
                "country": {"$in": ["USA", "Taiwan", "China"]},
                "founded_year": {"$gte": 1980},
                "is_active": True
            },
            "order_by": ["name"]
        })
        
        # Execute queries
        results, run_id = self.runtime.execute(workflow.build())
        
        print(f"🎮 Found {len(results['search_gaming_laptops']['result'])} gaming laptops")
        for product in results['search_gaming_laptops']['result'][:3]:
            print(f"   • {product['name']} - ${product['price']}")
            print(f"     GPU: {product['specifications'].get('graphics', 'N/A')}")
        
        print(f"\n📁 Found {len(results['search_categories']['result'])} categories")
        for category in results['search_categories']['result'][:5]:
            print(f"   • {category['path']}")
        
        print(f"\n🏷️ Found {len(results['search_brands']['result'])} brands")
        for brand in results['search_brands']['result'][:5]:
            print(f"   • {brand['name']} ({brand['country']}, {brand['founded_year']})")
        
        print()
        return results
    
    async def demo_bulk_operations(self):
        """
        Demonstrate high-performance bulk operations using DataFlow.
        Each model provides: BulkCreate, BulkUpdate, BulkDelete, BulkUpsert nodes.
        """
        print("⚡ Demo: Bulk Operations (High Performance)")
        print("=" * 50)
        
        workflow = self.create_workflow()
        
        # 1. Bulk create product specifications (ProductSpecificationBulkCreateNode)
        bulk_specs = []
        product_id = 1  # Assume we have a product with ID 1
        
        # Generate multiple specifications for a product
        spec_data = [
            ("Performance", "CPU Cores", "8", "number", 8),
            ("Performance", "CPU Threads", "16", "number", 16),
            ("Performance", "Base Clock", "3.2GHz", "text", None),
            ("Performance", "Boost Clock", "4.4GHz", "text", None),
            ("Graphics", "GPU Model", "RTX 3060", "text", None),
            ("Graphics", "VRAM", "6GB", "number", 6),
            ("Memory", "RAM Type", "DDR4", "text", None),
            ("Memory", "RAM Speed", "3200MHz", "text", None),
            ("Storage", "Type", "NVMe SSD", "text", None),
            ("Storage", "Interface", "PCIe 3.0", "text", None),
            ("Display", "Panel Type", "IPS", "text", None),
            ("Display", "Response Time", "3ms", "number", 3),
        ]
        
        for i, (group, name, value, data_type, numeric_val) in enumerate(spec_data):
            spec = {
                "product_id": product_id,
                "spec_group": group,
                "spec_name": name,
                "spec_value": value,
                "data_type": data_type,
                "numeric_value": numeric_val,
                "display_order": i,
                "is_key_spec": i < 6,  # First 6 are key specs
                "is_searchable": True,
                "source": "manual"
            }
            bulk_specs.append(spec)
        
        workflow.add_node("ProductSpecificationBulkCreateNode", "bulk_create_specs", {
            "data": bulk_specs,
            "batch_size": 50,
            "conflict_resolution": "skip"  # Skip duplicates
        })
        
        # 2. Bulk create product images (ProductImageBulkCreateNode)
        bulk_images = [
            {
                "product_id": product_id,
                "url": "/images/asus-rog-g15-front.jpg",
                "alt_text": "ASUS ROG Strix G15 front view",
                "image_type": "photo",
                "position": 0,
                "is_primary": True,
                "width": 1920,
                "height": 1080
            },
            {
                "product_id": product_id,
                "url": "/images/asus-rog-g15-keyboard.jpg",
                "alt_text": "RGB keyboard detail",
                "image_type": "photo", 
                "position": 1,
                "width": 1920,
                "height": 1080
            },
            {
                "product_id": product_id,
                "url": "/images/asus-rog-g15-ports.jpg",
                "alt_text": "Port connectivity options",
                "image_type": "photo",
                "position": 2,
                "width": 1920,
                "height": 1080
            }
        ]
        
        workflow.add_node("ProductImageBulkCreateNode", "bulk_create_images", {
            "data": bulk_images,
            "batch_size": 20
        })
        
        # 3. Bulk price update for multiple products (ProductBulkUpdateNode)
        workflow.add_node("ProductBulkUpdateNode", "bulk_price_update", {
            "filter": {
                "specifications.graphics": {"$regex": "RTX 30"},
                "status": "active"
            },
            "update": {
                # Apply 5% discount using MongoDB-style operators
                "price": {"$multiply": 0.95},
                # Update metadata
                "$set": {
                    "metadata.promotion": "RTX 30 series sale",
                    "metadata.discount_applied": datetime.now().isoformat()
                }
            },
            "limit": 100
        })
        
        # Execute bulk operations
        results, run_id = self.runtime.execute(workflow.build())
        
        print(f"📋 Created {len(bulk_specs)} product specifications in bulk")
        print(f"🖼️ Created {len(bulk_images)} product images in bulk")
        
        if 'bulk_price_update' in results:
            updated_count = results['bulk_price_update']['result'].get('updated_count', 0)
            print(f"💰 Updated prices for {updated_count} products with RTX 30 series GPUs")
        
        print()
        return results
    
    async def demo_web_scraping_operations(self):
        """
        Demonstrate web scraping job tracking and enriched data management.
        """
        print("🕷️ Demo: Web Scraping Operations")  
        print("=" * 50)
        
        workflow = self.create_workflow()
        
        # 1. Create scraping job (ScrapingJobCreateNode)
        workflow.add_node("ScrapingJobCreateNode", "create_scraping_job", {
            "job_name": "Gaming Laptop Price Monitor",
            "job_type": "price_update",
            "target_url": "https://example-retailer.com/gaming-laptops",
            "target_domain": "example-retailer.com",
            "status": "running",
            "started_at": datetime.now(),
            "scraping_config": {
                "selectors": {
                    "product_name": ".product-title",
                    "price": ".price-current",
                    "specs": ".spec-list li"
                },
                "rate_limit": 1.0,  # 1 request per second
                "user_agent": "Horme Product Scraper 1.0"
            },
            "is_recurring": True,
            "cron_schedule": "0 */6 * * *"  # Every 6 hours
        })
        
        # 2. Update products with scraped data (ProductBulkUpsertNode)
        scraped_products = [
            {
                "sku": "SCRAPED-GAMING-001",
                "name": "Gaming Laptop Pro X1",
                "price": 1599.99,
                "source_urls": ["https://example-retailer.com/gaming-laptop-x1"],
                "scraping_metadata": {
                    "scraped_at": datetime.now().isoformat(),
                    "source": "example-retailer.com",
                    "confidence": 0.95,
                    "data_quality": "high"
                },
                "enriched_data": {
                    "sentiment_score": 0.8,
                    "review_summary": "High performance, great value",
                    "competitor_price_avg": 1649.99,
                    "market_position": "competitive"
                },
                "last_scraped_at": datetime.now()
            },
            {
                "sku": "SCRAPED-GAMING-002", 
                "name": "Gaming Laptop Ultra Z2",
                "price": 1899.99,
                "source_urls": ["https://example-retailer.com/gaming-laptop-z2"],
                "scraping_metadata": {
                    "scraped_at": datetime.now().isoformat(),
                    "source": "example-retailer.com", 
                    "confidence": 0.92,
                    "data_quality": "high"
                },
                "enriched_data": {
                    "sentiment_score": 0.85,
                    "review_summary": "Premium build, excellent performance",
                    "competitor_price_avg": 1999.99,
                    "market_position": "premium"
                },
                "last_scraped_at": datetime.now()
            }
        ]
        
        workflow.add_node("ProductBulkUpsertNode", "upsert_scraped_products", {
            "data": scraped_products,
            "match_fields": ["sku"],
            "conflict_resolution": "upsert",
            "batch_size": 50
        })
        
        # 3. Query products by scraping metadata (ProductListNode)
        workflow.add_node("ProductListNode", "search_scraped_products", {
            "filter": {
                "scraping_metadata.confidence": {"$gte": 0.9},
                "last_scraped_at": {"$gte": datetime.now().replace(hour=0, minute=0, second=0)},
                "enriched_data.market_position": {"$in": ["competitive", "premium"]}
            },
            "order_by": ["-scraping_metadata.confidence", "-price"],
            "limit": 20
        })
        
        # Execute scraping workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        job_result = results['create_scraping_job']['result']
        print(f"🕷️ Created scraping job: {job_result['job_name']}")
        print(f"   Target: {job_result['target_domain']}")
        print(f"   Schedule: {job_result['cron_schedule']}")
        
        upsert_result = results['upsert_scraped_products']['result']
        print(f"📦 Upserted {len(scraped_products)} scraped products")
        print(f"   Created: {upsert_result.get('created_count', 0)}")
        print(f"   Updated: {upsert_result.get('updated_count', 0)}")
        
        scraped_products_found = results['search_scraped_products']['result']
        print(f"🔍 Found {len(scraped_products_found)} high-confidence scraped products")
        
        print()
        return results
    
    async def demo_analytics_operations(self):
        """
        Demonstrate product analytics tracking and reporting.
        """
        print("📊 Demo: Analytics Operations")
        print("=" * 50)
        
        workflow = self.create_workflow()
        
        # 1. Create analytics data (ProductAnalyticsBulkCreateNode)
        analytics_data = []
        product_ids = [1, 2, 3]  # Assume we have products with these IDs
        
        # Generate daily analytics for the past week
        for days_ago in range(7):
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            date = date.replace(day=date.day - days_ago)
            
            for product_id in product_ids:
                analytics = {
                    "product_id": product_id,
                    "date": date,
                    "page_views": 150 + (days_ago * 10) + (product_id * 25),
                    "unique_visitors": 80 + (days_ago * 5) + (product_id * 15),
                    "add_to_cart": 12 + (product_id * 3),
                    "add_to_wishlist": 8 + (product_id * 2),
                    "search_impressions": 500 + (product_id * 100),
                    "search_clicks": 45 + (product_id * 10),
                    "search_ctr": 0.09 + (product_id * 0.01),
                    "popularity_score": 75.0 + (product_id * 5),
                    "trending_score": 60.0 + (days_ago * 2),
                    "data_sources": ["web_analytics", "search_console"],
                    "last_updated": datetime.now()
                }
                analytics_data.append(analytics)
        
        workflow.add_node("ProductAnalyticsBulkCreateNode", "create_analytics", {
            "data": analytics_data,
            "batch_size": 50,
            "conflict_resolution": "upsert"
        })
        
        # 2. Query top performing products (ProductAnalyticsListNode)
        workflow.add_node("ProductAnalyticsListNode", "top_performers", {
            "filter": {
                "date": {"$gte": datetime.now().replace(day=datetime.now().day - 7)},
                "popularity_score": {"$gte": 70}
            },
            "aggregate": [
                {
                    "$group": {
                        "_id": "$product_id",
                        "total_views": {"$sum": "$page_views"},
                        "total_visitors": {"$sum": "$unique_visitors"},
                        "avg_ctr": {"$avg": "$search_ctr"},
                        "max_popularity": {"$max": "$popularity_score"}
                    }
                },
                {"$sort": {"total_views": -1}},
                {"$limit": 10}
            ]
        })
        
        # 3. Trending products analysis (ProductAnalyticsListNode)
        workflow.add_node("ProductAnalyticsListNode", "trending_analysis", {
            "filter": {
                "date": {"$gte": datetime.now().replace(day=datetime.now().day - 3)},
                "trending_score": {"$gte": 60}
            },
            "order_by": ["-trending_score", "-date"],
            "limit": 15
        })
        
        # Execute analytics workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        print(f"📈 Created {len(analytics_data)} analytics records")
        
        top_performers = results['top_performers']['result']
        print(f"🏆 Top {len(top_performers)} performing products by views:")
        for performer in top_performers[:5]:
            print(f"   Product ID {performer['_id']}: {performer['total_views']} views, {performer['total_visitors']} visitors")
        
        trending = results['trending_analysis']['result']
        print(f"🔥 Found {len(trending)} trending product analytics entries")
        
        print()
        return results
    
    async def demo_complex_relationships(self):
        """
        Demonstrate complex relationships and cross-model queries.
        """
        print("🔗 Demo: Complex Relationships")
        print("=" * 50)
        
        workflow = self.create_workflow()
        
        # 1. Product-supplier relationship operations (ProductSupplierBulkCreateNode)
        supplier_relationships = [
            {
                "product_id": 1,
                "supplier_id": 1,
                "supplier_sku": "SUPPLIER1-GAMING-001",
                "supplier_name": "ASUS ROG Strix G15 - Supplier 1",
                "supplier_price": 1199.99,
                "minimum_order_qty": 1,
                "lead_time_days": 3,
                "is_preferred": True,
                "reliability_score": 96.5,
                "quality_score": 98.0
            },
            {
                "product_id": 1,
                "supplier_id": 2,
                "supplier_sku": "SUPPLIER2-GAMING-001",
                "supplier_name": "ASUS ROG Strix G15 - Supplier 2",
                "supplier_price": 1249.99,
                "minimum_order_qty": 5,
                "lead_time_days": 7,
                "is_preferred": False,
                "reliability_score": 92.0,
                "quality_score": 95.0
            }
        ]
        
        workflow.add_node("ProductSupplierBulkCreateNode", "create_relationships", {
            "data": supplier_relationships,
            "batch_size": 10
        })
        
        # 2. Find best suppliers for products (ProductSupplierListNode)
        workflow.add_node("ProductSupplierListNode", "best_suppliers", {
            "filter": {
                "is_available": True,
                "reliability_score": {"$gte": 90},
                "quality_score": {"$gte": 95}
            },
            "order_by": ["-reliability_score", "supplier_price"],
            "limit": 20
        })
        
        # 3. Category hierarchy analysis (CategoryListNode)
        workflow.add_node("CategoryListNode", "category_hierarchy", {
            "filter": {
                "is_active": True,
                "level": {"$lte": 2}
            },
            "order_by": ["level", "path", "sort_order"]
        })
        
        # Execute relationship workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        print(f"🤝 Created {len(supplier_relationships)} supplier relationships")
        
        best_suppliers = results['best_suppliers']['result']
        print(f"⭐ Found {len(best_suppliers)} high-quality suppliers")
        for supplier in best_suppliers[:3]:
            print(f"   Product {supplier['product_id']}: {supplier['supplier_name']}")
            print(f"      Price: ${supplier['supplier_price']}, Reliability: {supplier['reliability_score']}%")
        
        categories = results['category_hierarchy']['result']
        print(f"📁 Category hierarchy ({len(categories)} categories):")
        for category in categories[:5]:
            indent = "  " * category['level']
            print(f"   {indent}{category['name']} (Level {category['level']})")
        
        print()
        return results
    
    async def run_complete_demo(self):
        """
        Run the complete demonstration of all DataFlow capabilities.
        """
        print("🚀 Horme Product Knowledge Base - DataFlow Demo")
        print("=" * 70)
        print("Demonstrating 81 auto-generated nodes (9 nodes × 9 models)")
        print("=" * 70)
        print()
        
        try:
            # Run all demonstration modules
            await self.demo_basic_crud_operations()
            await self.demo_advanced_queries()  
            await self.demo_bulk_operations()
            await self.demo_web_scraping_operations()
            await self.demo_analytics_operations()
            await self.demo_complex_relationships()
            
            print("🎉 Demo completed successfully!")
            print("=" * 70)
            print("Key DataFlow Benefits Demonstrated:")
            print("✅ 81 auto-generated database operation nodes")
            print("✅ MongoDB-style queries on PostgreSQL")
            print("✅ High-performance bulk operations")
            print("✅ Enterprise features (multi-tenancy, audit logs)")  
            print("✅ Web scraping data management")
            print("✅ Advanced analytics and reporting")
            print("✅ Complex relationship management")
            print("=" * 70)
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            raise

async def main():
    """Run the DataFlow demonstration."""
    demo = HormeDataFlowDemo()
    await demo.run_complete_demo()

if __name__ == "__main__":
    asyncio.run(main())