"""
Simple test script for supplier discovery system.
Tests with 5 different brands to validate the system.
"""

import sys
import json
from datetime import datetime
from supplier_discovery import SupplierDiscovery

def test_supplier_discovery():
    """Test supplier discovery with 5 brands."""
    print("SUPPLIER DISCOVERY SYSTEM TEST")
    print("=" * 50)
    
    # Initialize discovery system
    discovery = SupplierDiscovery()
    
    # Test with 5 different hardware brands
    test_brands = [
        "3M",        # Safety equipment and industrial supplies
        "Bosch",     # Power tools and equipment  
        "Karcher",   # Cleaning equipment
        "DeWalt",    # Professional power tools
        "Stanley"    # Hand tools and hardware
    ]
    
    print(f"\nTesting {len(test_brands)} brands:")
    for brand in test_brands:
        print(f"  - {brand}")
    
    print("\nDiscovering suppliers...")
    print("-" * 30)
    
    results = {}
    successful = 0
    
    for brand in test_brands:
        print(f"\nProcessing {brand}...")
        supplier_info = discovery.get_supplier_info(brand)
        
        if supplier_info:
            successful += 1
            results[brand] = supplier_info
            print(f"  [SUCCESS] Found {brand}")
            print(f"    Website: {supplier_info.official_website}")
            print(f"    Categories: {', '.join(supplier_info.product_categories[:3])}")
            if supplier_info.contact_info:
                print(f"    Contact: {supplier_info.contact_info}")
        else:
            results[brand] = None
            print(f"  [FAILED] Could not find {brand}")
    
    print(f"\nSUMMARY:")
    print(f"  Brands tested: {len(test_brands)}")
    print(f"  Successful discoveries: {successful}")
    print(f"  Success rate: {(successful/len(test_brands))*100:.1f}%")
    
    # Save results
    output_data = {
        "test_timestamp": datetime.now().isoformat(),
        "brands_tested": test_brands,
        "successful_discoveries": successful,
        "success_rate": (successful/len(test_brands))*100,
        "results": {
            brand: supplier.to_dict() if supplier else None
            for brand, supplier in results.items()
        }
    }
    
    output_file = f"supplier_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"  Results saved to: {output_file}")
    
    # Display detailed results
    print(f"\nDETAILED RESULTS:")
    print("-" * 20)
    
    for brand, supplier in results.items():
        print(f"\n{brand}:")
        if supplier:
            print(f"  Official Website: {supplier.official_website}")
            print(f"  Singapore Site: {supplier.singapore_distributor or 'N/A'}")
            print(f"  Product Catalog: {supplier.product_catalog_url or 'N/A'}")
            print(f"  Tech Docs: {supplier.technical_docs_section or 'N/A'}")
            print(f"  Categories: {len(supplier.product_categories)} found")
            print(f"  Contact Info: {len(supplier.contact_info)} fields")
        else:
            print(f"  Status: Not discovered")
    
    return results

def main():
    """Run the test."""
    try:
        results = test_supplier_discovery()
        
        # Count successful discoveries
        successful = sum(1 for r in results.values() if r is not None)
        
        if successful >= 3:  # At least 3 out of 5 brands found
            print(f"\nTEST PASSED: Found {successful}/5 suppliers")
            return 0
        else:
            print(f"\nTEST WARNING: Only found {successful}/5 suppliers")
            return 1
            
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    sys.exit(main())