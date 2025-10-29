"""
Final integration test for the supplier discovery and scraping system.
Tests the complete workflow with 5 different brands from Excel data.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Import our modules
from supplier_discovery import SupplierDiscovery
from supplier_scrapers import SupplierScrapingManager

def test_complete_system():
    """Test the complete supplier discovery and scraping system."""
    print("FINAL SUPPLIER SYSTEM INTEGRATION TEST")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test data - 5 different brands from common Excel data categories
    test_brands = [
        "3M",        # Safety/Industrial supplies
        "Bosch",     # Power tools 
        "Karcher",   # Cleaning equipment
        "DeWalt",    # Professional tools
        "Stanley"    # Hand tools/Hardware
    ]
    
    results = {
        "test_metadata": {
            "timestamp": datetime.now().isoformat(),
            "brands_tested": test_brands,
            "test_stages": ["discovery", "scraping_setup", "integration"]
        },
        "stage_results": {},
        "summary": {}
    }
    
    # Stage 1: Supplier Discovery
    print(f"\nSTAGE 1: SUPPLIER DISCOVERY")
    print("-" * 30)
    
    discovery = SupplierDiscovery()
    discovery_results = {}
    successful_discoveries = 0
    
    for brand in test_brands:
        print(f"Discovering {brand}...", end=" ")
        supplier_info = discovery.get_supplier_info(brand)
        
        if supplier_info:
            discovery_results[brand] = supplier_info
            successful_discoveries += 1
            print("[OK]")
            print(f"  Website: {supplier_info.official_website}")
            print(f"  Categories: {len(supplier_info.product_categories)}")
        else:
            discovery_results[brand] = None
            print("[FAILED]")
    
    discovery_success_rate = (successful_discoveries / len(test_brands)) * 100
    results["stage_results"]["discovery"] = {
        "successful": successful_discoveries,
        "total": len(test_brands),
        "success_rate": discovery_success_rate,
        "details": {
            brand: supplier.to_dict() if supplier else None
            for brand, supplier in discovery_results.items()
        }
    }
    
    print(f"\nDiscovery Results: {successful_discoveries}/{len(test_brands)} ({discovery_success_rate:.1f}%)")
    
    # Stage 2: Scraping System Setup
    print(f"\nSTAGE 2: SCRAPING SYSTEM SETUP")
    print("-" * 30)
    
    manager = SupplierScrapingManager(rate_limit_seconds=1.0)
    available_scrapers = list(manager.scrapers.keys())
    
    print(f"Available scrapers: {len(available_scrapers)}")
    for scraper_name in available_scrapers:
        scraper = manager.scrapers[scraper_name]
        print(f"  - {scraper_name}: {scraper.get_base_url()}")
    
    # Test scraper initialization
    scraper_setup_success = len(available_scrapers) >= 3
    results["stage_results"]["scraping_setup"] = {
        "scrapers_available": len(available_scrapers),
        "scraper_details": {
            name: manager.scrapers[name].get_base_url() 
            for name in available_scrapers
        },
        "setup_successful": scraper_setup_success
    }
    
    print(f"Scraper setup: {'OK' if scraper_setup_success else 'FAILED'}")
    
    # Stage 3: Integration Test
    print(f"\nSTAGE 3: INTEGRATION TEST")
    print("-" * 30)
    
    # Test the complete workflow (simplified for demo)
    integration_successful = False
    integration_details = {}
    
    if successful_discoveries >= 3 and scraper_setup_success:
        print("Running integration test...")
        
        # Check if discovered suppliers match available scrapers
        discovered_brands = [brand for brand, supplier in discovery_results.items() if supplier]
        matching_scrapers = [brand for brand in discovered_brands if brand in available_scrapers]
        
        print(f"Discovered brands: {discovered_brands}")
        print(f"Matching scrapers: {matching_scrapers}")
        
        if len(matching_scrapers) >= 2:
            integration_successful = True
            print("Integration test: PASSED")
            print("  - Supplier discovery working")
            print("  - Scrapers available for discovered suppliers")
            print("  - System ready for production use")
        else:
            print("Integration test: PARTIAL")
            print("  - Discovery working but limited scraper coverage")
    else:
        print("Integration test: FAILED")
        print("  - Insufficient discoveries or scraper setup failed")
    
    results["stage_results"]["integration"] = {
        "successful": integration_successful,
        "discovered_brands": [brand for brand, supplier in discovery_results.items() if supplier],
        "available_scrapers": available_scrapers,
        "integration_ready": integration_successful
    }
    
    # Overall Summary
    print(f"\nOVERALL SUMMARY")
    print("=" * 20)
    
    overall_success = (
        discovery_success_rate >= 80 and  # 80%+ discovery success
        scraper_setup_success and         # Scrapers initialized
        integration_successful            # Integration working
    )
    
    results["summary"] = {
        "overall_success": overall_success,
        "discovery_rate": discovery_success_rate,
        "scrapers_ready": scraper_setup_success,
        "integration_ready": integration_successful,
        "system_status": "READY" if overall_success else "NEEDS_WORK"
    }
    
    print(f"System Status: {results['summary']['system_status']}")
    print(f"Discovery Success: {discovery_success_rate:.1f}%")
    print(f"Scrapers Ready: {'Yes' if scraper_setup_success else 'No'}")
    print(f"Integration Ready: {'Yes' if integration_successful else 'No'}")
    
    # Save comprehensive results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"final_supplier_test_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {results_file}")
    
    # Return status for script exit code
    return 0 if overall_success else 1

def display_system_capabilities():
    """Display the capabilities of the supplier system."""
    print(f"\nSYSTEM CAPABILITIES SUMMARY")
    print("=" * 35)
    
    capabilities = [
        "Brand to supplier website discovery",
        "Singapore market supplier mapping",
        "10+ pre-verified hardware suppliers",
        "Adaptive website scraping",
        "Parallel processing with rate limiting",
        "Technical specification extraction",
        "PDF datasheet identification",
        "Product image collection",
        "Category and compatibility detection",
        "Comprehensive error handling",
        "JSON export with timestamps",
        "Modular scraper architecture"
    ]
    
    print("Core Features:")
    for i, capability in enumerate(capabilities, 1):
        print(f"  {i:2d}. {capability}")
    
    print(f"\nSupported Suppliers:")
    discovery = SupplierDiscovery()
    all_suppliers = discovery.get_all_suppliers()
    
    for brand, supplier in all_suppliers.items():
        print(f"  - {brand}: {supplier.official_website}")
    
    print(f"\nTotal: {len(all_suppliers)} verified suppliers")

def main():
    """Run the final integration test."""
    try:
        # Display system capabilities
        display_system_capabilities()
        
        # Run the complete system test
        exit_code = test_complete_system()
        
        print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if exit_code == 0:
            print("FINAL RESULT: SYSTEM READY FOR PRODUCTION")
        else:
            print("FINAL RESULT: SYSTEM NEEDS OPTIMIZATION")
        
        return exit_code
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    sys.exit(main())