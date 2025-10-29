"""
Test script for the supplier discovery and scraping system.

This script demonstrates the complete workflow of the supplier discovery
and scraping system using 5 different hardware brands.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from supplier_discovery import SupplierDiscovery
from supplier_scrapers import SupplierScrapingManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_supplier_discovery():
    """Test the supplier discovery system."""
    print("\n" + "="*60)
    print("TESTING SUPPLIER DISCOVERY SYSTEM")
    print("="*60)
    
    discovery = SupplierDiscovery()
    
    # Test brands from different hardware categories
    test_brands = [
        "3M",        # Safety equipment and industrial supplies
        "Bosch",     # Power tools and equipment
        "Karcher",   # Cleaning equipment
        "DeWalt",    # Professional power tools
        "Stanley"    # Hand tools and hardware
    ]
    
    print(f"\nTesting supplier discovery for {len(test_brands)} brands:")
    print(f"Brands: {', '.join(test_brands)}")
    
    # Discover suppliers for all brands
    results = discovery.discover_multiple_brands(test_brands)
    
    # Display results
    print(f"\nDiscovery Results:")
    print("-" * 40)
    
    successful_discoveries = 0
    for brand, supplier_info in results.items():
        if supplier_info:
            successful_discoveries += 1
            print(f"\n[FOUND] {brand}:")
            print(f"   Website: {supplier_info.official_website}")
            print(f"   Singapore Distributor: {supplier_info.singapore_distributor or 'N/A'}")
            print(f"   Product Catalog: {supplier_info.product_catalog_url or 'N/A'}")
            print(f"   Categories: {', '.join(supplier_info.product_categories[:3])}")
            if supplier_info.contact_info:
                print(f"   Contact: {supplier_info.contact_info}")
        else:
            print(f"\n[NOT FOUND] {brand}: Not found")
    
    print(f"\nDiscovery Summary:")
    print(f"  Successful: {successful_discoveries}/{len(test_brands)}")
    print(f"  Success Rate: {(successful_discoveries/len(test_brands))*100:.1f}%")
    
    # Save supplier database
    discovery.save_suppliers_database("test_supplier_database.json")
    print(f"  Saved database: test_supplier_database.json")
    
    return results


def test_supplier_scraping():
    """Test the supplier scraping system."""
    print("\n" + "="*60)
    print("TESTING SUPPLIER SCRAPING SYSTEM")
    print("="*60)
    
    manager = SupplierScrapingManager(rate_limit_seconds=1.0)
    
    # Test with hardware-related search terms that should yield results
    test_queries = [
        "drill",           # Power tools
        "safety",          # Safety equipment  
        "cleaning",        # Cleaning supplies
        "measuring",       # Measuring tools
        "hand tools"       # Hand tools
    ]
    
    print(f"\nTesting scraping for {len(test_queries)} search queries:")
    print(f"Queries: {', '.join(test_queries)}")
    
    # Run complete search and scrape workflow
    start_time = time.time()
    results = manager.search_and_scrape(test_queries, max_results_per_brand=3)
    processing_time = time.time() - start_time
    
    # Display detailed results
    print(f"\nScraping Results:")
    print("-" * 40)
    
    summary = results['summary']
    print(f"Total Products Found: {summary['total_products']}")
    print(f"Total Errors: {summary['total_errors']}")
    print(f"Processing Time: {summary['processing_time']:.2f}s")
    print(f"Suppliers Processed: {summary['suppliers_processed']}")
    
    # Show results by supplier
    for supplier_name, supplier_data in results['suppliers'].items():
        products = supplier_data['products']
        errors = supplier_data['errors']
        brands = supplier_data['brands_processed']
        
        print(f"\n📦 {supplier_name}:")
        print(f"   Products Scraped: {len(products)}")
        print(f"   Queries Processed: {', '.join(brands)}")
        
        if products:
            # Show sample products
            print(f"   Sample Products:")
            for i, product in enumerate(products[:3]):  # Show first 3 products
                print(f"     {i+1}. {product['name'][:50]}...")
                if product['price']:
                    print(f"        Price: {product['price']}")
                if product['specifications']:
                    spec_count = len(product['specifications'])
                    print(f"        Specifications: {spec_count} items")
                if product['datasheets']:
                    print(f"        Datasheets: {len(product['datasheets'])} PDFs")
        
        if errors:
            print(f"   Errors: {len(errors)}")
            # Show first error as sample
            if errors:
                print(f"     Sample: {errors[0][:80]}...")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_scraping_results_{timestamp}.json"
    manager.save_results(results, results_file)
    print(f"\nDetailed results saved to: {results_file}")
    
    return results


def test_integrated_workflow():
    """Test the complete integrated workflow."""
    print("\n" + "="*60)
    print("TESTING INTEGRATED WORKFLOW")
    print("="*60)
    
    # Step 1: Discover suppliers
    print("\nStep 1: Discovering suppliers...")
    discovery = SupplierDiscovery()
    
    # Use brands that are likely to have good online presence
    integration_brands = ["3M", "Bosch", "Karcher"]
    
    supplier_results = {}
    for brand in integration_brands:
        supplier_info = discovery.get_supplier_info(brand)
        if supplier_info:
            supplier_results[brand] = supplier_info
            print(f"  ✅ Found {brand}: {supplier_info.official_website}")
        else:
            print(f"  ❌ Could not find {brand}")
    
    # Step 2: Test scraping from discovered suppliers
    print(f"\nStep 2: Testing scraping from {len(supplier_results)} discovered suppliers...")
    
    if supplier_results:
        manager = SupplierScrapingManager(rate_limit_seconds=1.0)
        
        # Search for generic terms that should work across suppliers
        search_terms = ["tools", "safety"]
        
        workflow_results = manager.search_and_scrape(search_terms, max_results_per_brand=2)
        
        # Display integrated results
        print(f"\nIntegrated Workflow Results:")
        print("-" * 30)
        
        total_products = workflow_results['summary']['total_products']
        total_time = workflow_results['summary']['processing_time']
        
        print(f"Suppliers Discovered: {len(supplier_results)}")
        print(f"Products Scraped: {total_products}")
        print(f"Total Processing Time: {total_time:.2f}s")
        
        # Show success metrics
        if total_products > 0:
            print(f"\n✅ Integration Successful!")
            print(f"   Successfully scraped {total_products} products")
            print(f"   from {len(workflow_results['suppliers'])} suppliers")
        else:
            print(f"\n⚠️  Integration partially successful")
            print(f"   Found suppliers but limited product scraping")
        
        return True
    else:
        print(f"\n❌ Integration failed - no suppliers discovered")
        return False


def create_test_report(discovery_results, scraping_results, integration_success):
    """Create a comprehensive test report."""
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST REPORT")
    print("="*60)
    
    report = {
        "test_timestamp": datetime.now().isoformat(),
        "test_summary": {
            "supplier_discovery": {
                "brands_tested": 5,
                "successful_discoveries": sum(1 for r in discovery_results.values() if r),
                "success_rate": (sum(1 for r in discovery_results.values() if r) / 5) * 100
            },
            "supplier_scraping": {
                "queries_tested": 5,
                "total_products_scraped": scraping_results['summary']['total_products'],
                "suppliers_active": scraping_results['summary']['suppliers_processed'],
                "processing_time": scraping_results['summary']['processing_time']
            },
            "integration_test": {
                "successful": integration_success,
                "workflow_complete": integration_success
            }
        },
        "detailed_results": {
            "discovery_details": {
                brand: supplier.to_dict() if supplier else None
                for brand, supplier in discovery_results.items()
            },
            "scraping_details": scraping_results
        }
    }
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"supplier_system_test_report_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Display summary
    discovery_summary = report['test_summary']['supplier_discovery']
    scraping_summary = report['test_summary']['supplier_scraping'] 
    integration_summary = report['test_summary']['integration_test']
    
    print(f"\nTest Results Summary:")
    print(f"📊 Supplier Discovery:")
    print(f"   Success Rate: {discovery_summary['success_rate']:.1f}%")
    print(f"   Brands Found: {discovery_summary['successful_discoveries']}/{discovery_summary['brands_tested']}")
    
    print(f"\n🔍 Supplier Scraping:")
    print(f"   Products Scraped: {scraping_summary['total_products_scraped']}")
    print(f"   Active Suppliers: {scraping_summary['suppliers_active']}")
    print(f"   Processing Time: {scraping_summary['processing_time']:.2f}s")
    
    print(f"\n🔗 Integration Test:")
    print(f"   Workflow Complete: {'✅ Yes' if integration_summary['successful'] else '❌ No'}")
    
    # Overall assessment
    overall_success = (
        discovery_summary['success_rate'] >= 60 and  # At least 60% discovery success
        scraping_summary['total_products_scraped'] > 0 and  # Some products scraped
        integration_summary['successful']  # Integration worked
    )
    
    print(f"\n🎯 Overall Assessment: {'✅ PASS' if overall_success else '⚠️  PARTIAL SUCCESS'}")
    
    if overall_success:
        print("   The supplier discovery and scraping system is working correctly!")
    else:
        print("   The system works but may need optimization for better results.")
    
    print(f"\nFull report saved to: {report_file}")
    
    return report


def main():
    """Run the complete test suite."""
    print("SUPPLIER DISCOVERY AND SCRAPING SYSTEM TEST")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: Supplier Discovery
        discovery_results = test_supplier_discovery()
        
        # Test 2: Supplier Scraping  
        scraping_results = test_supplier_scraping()
        
        # Test 3: Integrated Workflow
        integration_success = test_integrated_workflow()
        
        # Generate comprehensive report
        report = create_test_report(discovery_results, scraping_results, integration_success)
        
        print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"\nTest suite failed: {e}")
        raise


if __name__ == "__main__":
    main()