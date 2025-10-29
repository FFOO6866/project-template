"""
Supplier Discovery System for Hardware Brands

This module identifies and maps hardware brands to their official supplier websites,
focusing on Singapore market suppliers. It provides automated discovery of supplier
websites from brand names and maintains a comprehensive mapping database.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import requests
from urllib.parse import urljoin, urlparse
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SupplierInfo:
    """Information about a hardware supplier."""
    brand: str
    official_website: str
    singapore_distributor: Optional[str] = None
    product_catalog_url: Optional[str] = None
    technical_docs_section: Optional[str] = None
    contact_info: Dict[str, str] = field(default_factory=dict)
    product_categories: List[str] = field(default_factory=list)
    last_verified: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "brand": self.brand,
            "official_website": self.official_website,
            "singapore_distributor": self.singapore_distributor,
            "product_catalog_url": self.product_catalog_url,
            "technical_docs_section": self.technical_docs_section,
            "contact_info": self.contact_info,
            "product_categories": self.product_categories,
            "last_verified": self.last_verified.isoformat()
        }


class SupplierDiscovery:
    """
    Discovers and maps hardware brands to their official supplier websites.
    
    Features:
    - Automated website discovery for brand names
    - Singapore market focus with local distributor identification  
    - Verification of official websites vs distributors
    - Product catalog and technical documentation detection
    - Maintains verified supplier database
    """
    
    def __init__(self, rate_limit_seconds: float = 1.0):
        """
        Initialize the supplier discovery system.
        
        Args:
            rate_limit_seconds: Delay between requests to avoid overwhelming servers
        """
        self.rate_limit_seconds = rate_limit_seconds
        self.verified_suppliers: Dict[str, SupplierInfo] = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Load pre-verified Singapore hardware suppliers
        self._initialize_singapore_suppliers()
    
    def _initialize_singapore_suppliers(self):
        """Initialize with known Singapore hardware suppliers."""
        singapore_suppliers = {
            "3M": SupplierInfo(
                brand="3M",
                official_website="https://www.3m.com.sg",
                singapore_distributor="https://www.3m.com.sg",
                product_catalog_url="https://www.3m.com.sg/3M/en_SG/p/",
                technical_docs_section="https://www.3m.com.sg/3M/en_SG/safety-centers/",
                product_categories=["Safety Equipment", "Industrial Tapes", "Abrasives", "Adhesives"]
            ),
            "Bosch": SupplierInfo(
                brand="Bosch",
                official_website="https://www.bosch.com.sg",
                singapore_distributor="https://www.bosch.com.sg", 
                product_catalog_url="https://www.bosch.com.sg/products/",
                technical_docs_section="https://www.bosch.com.sg/service-support/",
                product_categories=["Power Tools", "Hand Tools", "Measuring Tools", "Garden Tools"]
            ),
            "Karcher": SupplierInfo(
                brand="Karcher", 
                official_website="https://www.karcher.com.sg",
                singapore_distributor="https://www.karcher.com.sg",
                product_catalog_url="https://www.karcher.com.sg/products/",
                technical_docs_section="https://www.karcher.com.sg/service/",
                product_categories=["Cleaning Equipment", "Pressure Washers", "Vacuum Cleaners"]
            ),
            "DeWalt": SupplierInfo(
                brand="DeWalt",
                official_website="https://www.dewalt.com.sg", 
                singapore_distributor="https://www.dewalt.com.sg",
                product_catalog_url="https://www.dewalt.com.sg/products/",
                technical_docs_section="https://www.dewalt.com.sg/support/",
                product_categories=["Power Tools", "Hand Tools", "Storage", "Accessories"]
            ),
            "Stanley": SupplierInfo(
                brand="Stanley",
                official_website="https://www.stanleytools.com.sg",
                singapore_distributor="https://www.stanleytools.com.sg", 
                product_catalog_url="https://www.stanleytools.com.sg/products/",
                technical_docs_section="https://www.stanleytools.com.sg/support/",
                product_categories=["Hand Tools", "Power Tools", "Storage", "Measuring Tools"]
            ),
            "Makita": SupplierInfo(
                brand="Makita",
                official_website="https://www.makita.com.sg",
                singapore_distributor="https://www.makita.com.sg",
                product_catalog_url="https://www.makita.com.sg/products/",
                technical_docs_section="https://www.makita.com.sg/service/",
                product_categories=["Power Tools", "Outdoor Power Equipment", "Industrial Tools"]
            ),
            "Hitachi": SupplierInfo(
                brand="Hitachi",
                official_website="https://www.hitachi-koki.com.sg",
                singapore_distributor="https://www.hitachi-koki.com.sg",
                product_catalog_url="https://www.hitachi-koki.com.sg/products/",
                technical_docs_section="https://www.hitachi-koki.com.sg/support/",
                product_categories=["Power Tools", "Industrial Equipment"]
            ),
            "Milwaukee": SupplierInfo(
                brand="Milwaukee", 
                official_website="https://www.milwaukeetool.com.sg",
                singapore_distributor="https://www.milwaukeetool.com.sg",
                product_catalog_url="https://www.milwaukeetool.com.sg/products/",
                technical_docs_section="https://www.milwaukeetool.com.sg/support/",
                product_categories=["Power Tools", "Hand Tools", "Storage", "Lighting"]
            ),
            "Festool": SupplierInfo(
                brand="Festool",
                official_website="https://www.festool.com.sg", 
                singapore_distributor="https://www.festool.com.sg",
                product_catalog_url="https://www.festool.com.sg/products/",
                technical_docs_section="https://www.festool.com.sg/service/",
                product_categories=["Power Tools", "Dust Extraction", "Abrasives", "Accessories"]
            ),
            "Hilti": SupplierInfo(
                brand="Hilti",
                official_website="https://www.hilti.com.sg",
                singapore_distributor="https://www.hilti.com.sg",
                product_catalog_url="https://www.hilti.com.sg/products/",
                technical_docs_section="https://www.hilti.com.sg/service/",
                product_categories=["Construction Tools", "Fasteners", "Chemicals", "Services"]
            )
        }
        
        self.verified_suppliers.update(singapore_suppliers)
        logger.info(f"Initialized with {len(singapore_suppliers)} verified Singapore suppliers")
    
    def discover_supplier_website(self, brand_name: str) -> Optional[SupplierInfo]:
        """
        Discover official supplier website for a brand.
        
        Args:
            brand_name: Name of the hardware brand
            
        Returns:
            SupplierInfo if found, None otherwise
        """
        # Check if already verified
        if brand_name in self.verified_suppliers:
            logger.info(f"Found verified supplier for {brand_name}")
            return self.verified_suppliers[brand_name]
        
        logger.info(f"Discovering supplier website for brand: {brand_name}")
        
        # Search strategies
        search_patterns = [
            f"{brand_name}.com.sg",
            f"{brand_name}.sg", 
            f"www.{brand_name}.com.sg",
            f"www.{brand_name}.sg",
            f"{brand_name}.com",
            f"www.{brand_name}.com"
        ]
        
        for pattern in search_patterns:
            url = f"https://{pattern}"
            if self._verify_supplier_website(url, brand_name):
                supplier_info = self._extract_supplier_info(url, brand_name)
                if supplier_info:
                    self.verified_suppliers[brand_name] = supplier_info
                    logger.info(f"Successfully discovered supplier for {brand_name}: {url}")
                    return supplier_info
            
            # Rate limiting
            time.sleep(self.rate_limit_seconds)
        
        logger.warning(f"Could not discover supplier website for {brand_name}")
        return None
    
    def _verify_supplier_website(self, url: str, brand_name: str) -> bool:
        """
        Verify if a URL is the official supplier website for a brand.
        
        Args:
            url: Website URL to verify
            brand_name: Brand name to verify against
            
        Returns:
            True if verified as official supplier website
        """
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                content = response.text.lower()
                brand_lower = brand_name.lower()
                
                # Check for brand presence in various page elements
                brand_indicators = [
                    brand_lower in content,
                    f"welcome to {brand_lower}" in content,
                    f"{brand_lower} official" in content,
                    f"{brand_lower} singapore" in content,
                    brand_lower in response.url.lower()
                ]
                
                # Must have at least 2 indicators for verification
                if sum(brand_indicators) >= 2:
                    logger.debug(f"Verified {url} as official website for {brand_name}")
                    return True
                    
        except requests.RequestException as e:
            logger.debug(f"Failed to verify {url}: {e}")
            
        return False
    
    def _extract_supplier_info(self, url: str, brand_name: str) -> Optional[SupplierInfo]:
        """
        Extract comprehensive supplier information from website.
        
        Args:
            url: Verified supplier website URL
            brand_name: Brand name
            
        Returns:
            SupplierInfo with extracted details
        """
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return None
                
            content = response.text
            
            # Extract product catalog URL
            catalog_url = self._find_product_catalog_url(content, url)
            
            # Extract technical docs section
            tech_docs_url = self._find_technical_docs_url(content, url)
            
            # Extract contact information
            contact_info = self._extract_contact_info(content)
            
            # Extract product categories  
            categories = self._extract_product_categories(content)
            
            supplier_info = SupplierInfo(
                brand=brand_name,
                official_website=url,
                singapore_distributor=url if ".sg" in url else None,
                product_catalog_url=catalog_url,
                technical_docs_section=tech_docs_url,
                contact_info=contact_info,
                product_categories=categories
            )
            
            return supplier_info
            
        except requests.RequestException as e:
            logger.error(f"Failed to extract supplier info from {url}: {e}")
            return None
    
    def _find_product_catalog_url(self, content: str, base_url: str) -> Optional[str]:
        """Find product catalog URL from website content."""
        catalog_patterns = [
            r'href=["\']([^"\']*(?:product|catalog|shop)[^"\']*)["\']',
            r'href=["\']([^"\']*products[^"\']*)["\']'
        ]
        
        for pattern in catalog_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match.startswith('/'):
                    return urljoin(base_url, match)
                elif match.startswith('http'):
                    return match
                    
        return None
    
    def _find_technical_docs_url(self, content: str, base_url: str) -> Optional[str]:
        """Find technical documentation section URL."""
        docs_patterns = [
            r'href=["\']([^"\']*(?:support|service|technical|documentation|manual)[^"\']*)["\']',
            r'href=["\']([^"\']*docs[^"\']*)["\']'
        ]
        
        for pattern in docs_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match.startswith('/'):
                    return urljoin(base_url, match)
                elif match.startswith('http'):
                    return match
                    
        return None
    
    def _extract_contact_info(self, content: str) -> Dict[str, str]:
        """Extract contact information from website content."""
        contact_info = {}
        
        # Extract phone numbers (Singapore format)
        phone_pattern = r'(?:\+65\s?)?[689]\d{3}\s?\d{4}'
        phones = re.findall(phone_pattern, content)
        if phones:
            contact_info['phone'] = phones[0]
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        if emails:
            contact_info['email'] = emails[0]
        
        # Extract addresses (basic Singapore address pattern)
        address_pattern = r'(?:Singapore\s+)?\d{6}(?:\s+Singapore)?'
        addresses = re.findall(address_pattern, content, re.IGNORECASE)
        if addresses:
            contact_info['postal_code'] = addresses[0]
            
        return contact_info
    
    def _extract_product_categories(self, content: str) -> List[str]:
        """Extract product categories from website content."""
        categories = set()
        
        # Common hardware categories
        category_keywords = [
            'power tools', 'hand tools', 'safety equipment', 'measuring tools',
            'cutting tools', 'drilling', 'grinding', 'fasteners', 'adhesives',
            'abrasives', 'cleaning equipment', 'garden tools', 'storage',
            'lighting', 'electrical', 'plumbing', 'hardware', 'construction',
            'industrial equipment', 'automotive tools', 'welding', 'pneumatic tools'
        ]
        
        content_lower = content.lower()
        for keyword in category_keywords:
            if keyword in content_lower:
                categories.add(keyword.title())
        
        return list(categories)[:10]  # Limit to top 10 categories
    
    def get_supplier_info(self, brand_name: str) -> Optional[SupplierInfo]:
        """
        Get supplier information for a brand (discover if not cached).
        
        Args:
            brand_name: Brand name to look up
            
        Returns:
            SupplierInfo if found/discovered, None otherwise
        """
        if brand_name in self.verified_suppliers:
            return self.verified_suppliers[brand_name]
        
        return self.discover_supplier_website(brand_name)
    
    def get_all_suppliers(self) -> Dict[str, SupplierInfo]:
        """Get all verified suppliers."""
        return self.verified_suppliers.copy()
    
    def save_suppliers_database(self, filepath: str = "supplier_database.json"):
        """
        Save the verified suppliers database to JSON file.
        
        Args:
            filepath: Path to save the database file
        """
        data = {
            brand: supplier.to_dict() 
            for brand, supplier in self.verified_suppliers.items()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(data)} suppliers to {filepath}")
    
    def load_suppliers_database(self, filepath: str = "supplier_database.json"):
        """
        Load verified suppliers database from JSON file.
        
        Args:
            filepath: Path to load the database file from
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for brand, supplier_data in data.items():
                # Convert back to SupplierInfo object
                supplier_data['last_verified'] = datetime.fromisoformat(supplier_data['last_verified'])
                self.verified_suppliers[brand] = SupplierInfo(**supplier_data)
            
            logger.info(f"Loaded {len(data)} suppliers from {filepath}")
            
        except FileNotFoundError:
            logger.warning(f"Supplier database file {filepath} not found")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse supplier database: {e}")
    
    def discover_multiple_brands(self, brand_list: List[str]) -> Dict[str, Optional[SupplierInfo]]:
        """
        Discover supplier websites for multiple brands.
        
        Args:
            brand_list: List of brand names to discover
            
        Returns:
            Dictionary mapping brand names to SupplierInfo (None if not found)
        """
        results = {}
        
        for brand in brand_list:
            try:
                logger.info(f"Processing brand {brand}...")
                supplier_info = self.get_supplier_info(brand)
                results[brand] = supplier_info
                
                # Rate limiting between brands
                time.sleep(self.rate_limit_seconds)
                
            except Exception as e:
                logger.error(f"Error processing brand {brand}: {e}")
                results[brand] = None
        
        return results
    
    def update_supplier_verification(self, brand_name: str) -> bool:
        """
        Update verification timestamp for a supplier.
        
        Args:
            brand_name: Brand name to update
            
        Returns:
            True if updated successfully
        """
        if brand_name in self.verified_suppliers:
            self.verified_suppliers[brand_name].last_verified = datetime.now()
            logger.info(f"Updated verification timestamp for {brand_name}")
            return True
        
        logger.warning(f"Brand {brand_name} not found in verified suppliers")
        return False


def main():
    """Example usage of SupplierDiscovery system."""
    discovery = SupplierDiscovery()
    
    # Test brands
    test_brands = ["3M", "Bosch", "Karcher", "DeWalt", "Stanley"]
    
    print("Supplier Discovery System Demo")
    print("=" * 50)
    
    for brand in test_brands:
        supplier = discovery.get_supplier_info(brand)
        if supplier:
            print(f"\n{brand}:")
            print(f"  Website: {supplier.official_website}")
            print(f"  Categories: {', '.join(supplier.product_categories[:3])}")
            if supplier.contact_info:
                print(f"  Contact: {supplier.contact_info}")
        else:
            print(f"\n{brand}: Not found")
    
    # Save results
    discovery.save_suppliers_database("demo_suppliers.json")
    print(f"\nSaved supplier database with {len(discovery.get_all_suppliers())} suppliers")


if __name__ == "__main__":
    main()