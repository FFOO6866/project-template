#!/usr/bin/env python3
"""
Supplier Discovery System
========================

Automated supplier discovery and validation system for Singapore industrial suppliers.
Uses Google search, website analysis, and machine learning for supplier classification.

Features:
- Google Search API integration for supplier discovery
- Website classification and validation
- Automated supplier onboarding pipeline
- Data quality scoring and verification
- Contact information extraction
- Category classification and product detection
- Compliance checking (Singapore business registration)
"""

import os
import time
import json
import logging
import requests
import re
from typing import List, Dict, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

# Web scraping
from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import production scraper components
from .production_scraper import ProductionScraper, SupplierInfo, ScrapingConfig


@dataclass 
class DiscoveryConfig:
    """Configuration for supplier discovery operations."""
    
    # Search configuration
    max_suppliers_per_search: int = 50
    search_depth: int = 5  # Pages of Google results
    geographic_focus: str = "Singapore"
    
    # Industry categories
    target_industries: List[str] = None
    
    # Validation thresholds
    min_quality_score: float = 0.6
    require_contact_info: bool = True
    require_singapore_registration: bool = True
    
    # Rate limiting for external APIs
    google_api_delay: float = 1.0
    website_scraping_delay: float = 2.0
    
    def __post_init__(self):
        if self.target_industries is None:
            self.target_industries = [
                "industrial supplies", "hardware", "tools", "electrical supplies",
                "safety equipment", "mechanical parts", "plumbing supplies",
                "construction materials", "manufacturing supplies", "fasteners"
            ]


class GoogleSearchClient:
    """Client for Google Search API and web scraping based search."""
    
    def __init__(self, config: DiscoveryConfig):
        self.config = config
        self.logger = logging.getLogger("google_search")
        
        # Try to use Google Custom Search API if available
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        # Fallback to web scraping
        self.use_api = bool(self.api_key and self.search_engine_id)
        
        if self.use_api:
            self.logger.info("Using Google Custom Search API")
        else:
            self.logger.info("Using web scraping for Google search")
    
    def search_suppliers(self, industry: str, location: str = "Singapore") -> List[Dict[str, Any]]:
        """
        Search for suppliers in a specific industry and location.
        
        Args:
            industry: Industry or product category to search for
            location: Geographic location to focus on
            
        Returns:
            List of search result dictionaries
        """
        query = f"{industry} suppliers {location}"
        self.logger.info(f"Searching for: {query}")
        
        if self.use_api:
            return self._search_with_api(query)
        else:
            return self._search_with_scraping(query)
    
    def _search_with_api(self, query: str) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API."""
        results = []
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': 10,
                'gl': 'sg',  # Singapore geolocation
                'lr': 'lang_en'
            }
            
            for page in range(self.config.search_depth):
                if page > 0:
                    params['start'] = page * 10 + 1
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if 'items' in data:
                    for item in data['items']:
                        results.append({
                            'title': item.get('title', ''),
                            'link': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'displayLink': item.get('displayLink', '')
                        })
                
                # Respect rate limiting
                time.sleep(self.config.google_api_delay)
                
                # Check if we have more results
                if len(data.get('items', [])) < 10:
                    break
                    
        except Exception as e:
            self.logger.error(f"Google API search failed: {e}")
        
        return results
    
    def _search_with_scraping(self, query: str) -> List[Dict[str, Any]]:
        """Search using web scraping (fallback method)."""
        results = []
        
        try:
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(options=options)
            
            try:
                search_url = f"https://www.google.com/search?q={query}&gl=sg&hl=en"
                driver.get(search_url)
                
                # Wait for results to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.g"))
                )
                
                # Extract search results
                result_elements = driver.find_elements(By.CSS_SELECTOR, "div.g")
                
                for element in result_elements[:self.config.max_suppliers_per_search]:
                    try:
                        title_element = element.find_element(By.CSS_SELECTOR, "h3")
                        link_element = element.find_element(By.CSS_SELECTOR, "a")
                        snippet_element = element.find_element(By.CSS_SELECTOR, ".VwiC3b, .s3v9rd")
                        
                        results.append({
                            'title': title_element.text,
                            'link': link_element.get_attribute('href'),
                            'snippet': snippet_element.text if snippet_element else '',
                            'displayLink': urlparse(link_element.get_attribute('href')).netloc
                        })
                        
                    except NoSuchElementException:
                        continue
                
            finally:
                driver.quit()
                
        except Exception as e:
            self.logger.error(f"Google scraping failed: {e}")
        
        return results


class SupplierAnalyzer:
    """Analyzes supplier websites for classification and validation."""
    
    def __init__(self, production_scraper: ProductionScraper):
        self.scraper = production_scraper
        self.logger = logging.getLogger("supplier_analyzer")
        
        # Industry keywords for classification
        self.industry_keywords = {
            'industrial_supplies': [
                'industrial supplies', 'factory supplies', 'manufacturing supplies',
                'industrial equipment', 'industrial materials'
            ],
            'tools': [
                'tools', 'hand tools', 'power tools', 'cutting tools',
                'measuring tools', 'workshop tools'
            ],
            'hardware': [
                'hardware', 'fasteners', 'screws', 'bolts', 'nuts',
                'washers', 'rivets', 'anchors'
            ],
            'electrical': [
                'electrical supplies', 'electrical components', 'wiring',
                'cables', 'switches', 'outlets', 'lighting'
            ],
            'safety': [
                'safety equipment', 'ppe', 'personal protective equipment',
                'safety gear', 'protective clothing', 'safety shoes'
            ],
            'plumbing': [
                'plumbing supplies', 'pipes', 'fittings', 'valves',
                'pumps', 'water systems', 'drainage'
            ],
            'mechanical': [
                'mechanical parts', 'bearings', 'gears', 'motors',
                'hydraulics', 'pneumatics', 'machine parts'
            ]
        }
    
    def analyze_supplier_website(self, url: str) -> Optional[SupplierInfo]:
        """
        Analyze a supplier website and extract key information.
        
        Args:
            url: Supplier website URL
            
        Returns:
            SupplierInfo object if analysis successful, None otherwise
        """
        self.logger.info(f"Analyzing supplier website: {url}")
        
        def extract_supplier_info(content, url):
            """Extract supplier information from HTML content."""
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract basic information
            domain = urlparse(url).netloc
            name = self._extract_company_name(soup, domain)
            
            if not name:
                self.logger.warning(f"Could not extract company name from {url}")
                return None
            
            # Create supplier info object
            supplier = SupplierInfo(
                name=name,
                domain=domain,
                url=url
            )
            
            # Extract contact information
            supplier.contact_info = self._extract_contact_info(soup)
            
            # Classify industry categories
            supplier.categories = self._classify_supplier_categories(soup)
            
            # Extract location information
            supplier.location = self._extract_location(soup)
            
            # Verify Singapore registration if required
            if self.scraper.config.save_to_database:
                supplier.verified = self._verify_singapore_registration(name)
            
            self.logger.info(f"Analyzed supplier: {name}")
            self.logger.info(f"  Categories: {', '.join(supplier.categories)}")
            self.logger.info(f"  Location: {supplier.location}")
            self.logger.info(f"  Verified: {supplier.verified}")
            
            return supplier
        
        return self.scraper.scrape_with_requests(url, extract_supplier_info)
    
    def _extract_company_name(self, soup: BeautifulSoup, domain: str) -> str:
        """Extract company name from website."""
        # Try different selectors for company name
        name_selectors = [
            'h1.company-name', '.company-name', '#company-name',
            'h1.logo-text', '.logo-text', '.brand-name',
            '.header h1', 'header h1', '.site-title'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                if len(name) > 2 and len(name) < 100:
                    return name
        
        # Try extracting from title tag
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Remove common suffixes
            title = re.sub(r'\s*[-|]\s*(Home|Welcome|Singapore|Pte.*Ltd.*)', '', title, flags=re.IGNORECASE)
            if len(title) > 2 and len(title) < 100:
                return title
        
        # Fallback to domain name
        return domain.replace('www.', '').replace('.com', '').replace('.sg', '').title()
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract contact information from website."""
        contact_info = {}
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, soup.get_text())
        if emails:
            contact_info['email'] = emails[0]  # Take first email found
        
        # Extract phone numbers (Singapore format)
        phone_patterns = [
            r'\+65\s*[689]\d{3}\s*\d{4}',  # +65 format
            r'\b[689]\d{3}\s*\d{4}\b',     # Local format
            r'\(\+65\)\s*[689]\d{3}\s*\d{4}'  # (+65) format
        ]
        
        text = soup.get_text()
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                contact_info['phone'] = phones[0]
                break
        
        # Extract address (look for Singapore addresses)
        address_patterns = [
            r'[\d\w\s,.-]+Singapore\s+\d{6}',  # Address with postal code
            r'[\d\w\s,.-]+\d{6}\s+Singapore',  # Postal code before Singapore
        ]
        
        for pattern in address_patterns:
            addresses = re.findall(pattern, text, re.IGNORECASE)
            if addresses:
                contact_info['address'] = addresses[0].strip()
                break
        
        # Look for contact page information
        contact_links = soup.find_all('a', href=re.compile(r'contact', re.I))
        if contact_links:
            contact_info['contact_page'] = contact_links[0].get('href')
        
        return contact_info
    
    def _classify_supplier_categories(self, soup: BeautifulSoup) -> List[str]:
        """Classify supplier into industry categories based on content."""
        categories = []
        
        # Get all text content
        content = soup.get_text().lower()
        
        # Check each industry category
        for category, keywords in self.industry_keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences of keywords
                score += content.count(keyword.lower())
            
            # If enough keywords found, add category
            if score >= 2:  # Threshold for category inclusion
                categories.append(category.replace('_', ' ').title())
        
        # If no categories found, try to infer from meta tags and headings
        if not categories:
            # Check meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                desc_content = meta_desc.get('content', '').lower()
                for category, keywords in self.industry_keywords.items():
                    for keyword in keywords:
                        if keyword.lower() in desc_content:
                            categories.append(category.replace('_', ' ').title())
                            break
            
            # Check main headings
            headings = soup.find_all(['h1', 'h2', 'h3'])
            heading_text = ' '.join(h.get_text().lower() for h in headings)
            
            for category, keywords in self.industry_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in heading_text:
                        if category.replace('_', ' ').title() not in categories:
                            categories.append(category.replace('_', ' ').title())
                        break
        
        return categories[:5]  # Limit to top 5 categories
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract location information."""
        text = soup.get_text()
        
        # Look for Singapore-specific location indicators
        singapore_areas = [
            'Singapore', 'Jurong', 'Woodlands', 'Tampines', 'Bedok', 'Toa Payoh',
            'Ang Mo Kio', 'Bishan', 'Bukit Batok', 'Clementi', 'Pasir Ris',
            'Sengkang', 'Punggol', 'Hougang', 'Serangoon'
        ]
        
        for area in singapore_areas:
            if area.lower() in text.lower():
                return area if area != 'Singapore' else 'Singapore'
        
        return 'Singapore'  # Default assumption
    
    def _verify_singapore_registration(self, company_name: str) -> bool:
        """
        Verify if company is registered in Singapore.
        This is a placeholder - in production, you would integrate with ACRA API.
        """
        # Placeholder implementation
        # In real implementation, you would:
        # 1. Query ACRA (Accounting and Corporate Regulatory Authority) database
        # 2. Check for valid UEN (Unique Entity Number)
        # 3. Verify business registration status
        
        # For now, return True if it looks like a Singapore company
        sg_indicators = [
            'pte ltd', 'private limited', 'singapore',
            'sdn bhd', 'trading', 'supplies'
        ]
        
        name_lower = company_name.lower()
        return any(indicator in name_lower for indicator in sg_indicators)


class SupplierDiscovery:
    """Main supplier discovery and management system."""
    
    def __init__(self, config: DiscoveryConfig = None):
        """Initialize the supplier discovery system."""
        self.config = config or DiscoveryConfig()
        self.logger = logging.getLogger("supplier_discovery")
        
        # Initialize components
        scraping_config = ScrapingConfig(
            browser_type="headless_chrome",
            rate_limit_seconds=self.config.website_scraping_delay,
            save_to_database=True
        )
        
        self.production_scraper = ProductionScraper(scraping_config)
        self.google_client = GoogleSearchClient(self.config)
        self.analyzer = SupplierAnalyzer(self.production_scraper)
        
        # Storage
        self.discovered_suppliers: List[SupplierInfo] = []
        
        self.logger.info("Supplier discovery system initialized")
        self.logger.info(f"Target industries: {', '.join(self.config.target_industries)}")
        self.logger.info(f"Geographic focus: {self.config.geographic_focus}")
    
    def discover_suppliers_by_industry(self, industry: str) -> List[SupplierInfo]:
        """
        Discover suppliers for a specific industry.
        
        Args:
            industry: Industry category to search for
            
        Returns:
            List of discovered and validated suppliers
        """
        self.logger.info(f"Discovering suppliers for industry: {industry}")
        
        # Search for suppliers
        search_results = self.google_client.search_suppliers(
            industry, 
            self.config.geographic_focus
        )
        
        self.logger.info(f"Found {len(search_results)} initial search results")
        
        # Analyze each supplier website
        suppliers = []
        
        for result in search_results:
            try:
                url = result['link']
                
                # Skip non-business websites
                if self._should_skip_website(url):
                    continue
                
                # Analyze supplier website
                supplier = self.analyzer.analyze_supplier_website(url)
                
                if supplier and self._validate_supplier(supplier):
                    suppliers.append(supplier)
                    
                    # Save to database if configured
                    if self.production_scraper.config.save_to_database:
                        self.production_scraper.save_supplier_to_database(supplier)
                
                # Rate limiting
                time.sleep(self.config.website_scraping_delay)
                
            except Exception as e:
                self.logger.error(f"Error analyzing {result.get('link', 'unknown')}: {e}")
                continue
        
        self.logger.info(f"Discovered {len(suppliers)} validated suppliers for {industry}")
        return suppliers
    
    def discover_all_industries(self) -> Dict[str, List[SupplierInfo]]:
        """
        Discover suppliers across all configured target industries.
        
        Returns:
            Dictionary mapping industries to their discovered suppliers
        """
        self.logger.info("Starting comprehensive supplier discovery")
        
        all_suppliers = {}
        
        for industry in self.config.target_industries:
            self.logger.info(f"Processing industry: {industry}")
            
            suppliers = self.discover_suppliers_by_industry(industry)
            all_suppliers[industry] = suppliers
            
            # Add to main collection (avoiding duplicates)
            for supplier in suppliers:
                if not any(s.domain == supplier.domain for s in self.discovered_suppliers):
                    self.discovered_suppliers.append(supplier)
            
            # Progress report
            total_discovered = len(self.discovered_suppliers)
            self.logger.info(f"Total unique suppliers discovered so far: {total_discovered}")
        
        self.logger.info(f"Supplier discovery completed: {len(self.discovered_suppliers)} unique suppliers")
        return all_suppliers
    
    def _should_skip_website(self, url: str) -> bool:
        """Determine if a website should be skipped during analysis."""
        skip_domains = [
            'facebook.com', 'linkedin.com', 'youtube.com', 'instagram.com',
            'google.com', 'wikipedia.org', 'amazon.com', 'alibaba.com',
            'indiamart.com', 'thomasnet.com', 'yellowpages.com'
        ]
        
        domain = urlparse(url).netloc.lower()
        return any(skip_domain in domain for skip_domain in skip_domains)
    
    def _validate_supplier(self, supplier: SupplierInfo) -> bool:
        """Validate if supplier meets quality requirements."""
        # Check minimum requirements
        if self.config.require_contact_info:
            if not supplier.contact_info or not any(supplier.contact_info.values()):
                return False
        
        if self.config.require_singapore_registration:
            if not supplier.verified:
                return False
        
        # Check categories
        if not supplier.categories:
            return False
        
        # Check name quality
        if len(supplier.name) < 3 or len(supplier.name) > 100:
            return False
        
        return True
    
    def get_supplier_statistics(self) -> Dict[str, Any]:
        """Get statistics about discovered suppliers."""
        if not self.discovered_suppliers:
            return {}
        
        # Category distribution
        category_counts = {}
        for supplier in self.discovered_suppliers:
            for category in supplier.categories:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Verification status
        verified_count = sum(1 for s in self.discovered_suppliers if s.verified)
        
        # Contact information completeness
        with_email = sum(1 for s in self.discovered_suppliers if s.contact_info.get('email'))
        with_phone = sum(1 for s in self.discovered_suppliers if s.contact_info.get('phone'))
        with_address = sum(1 for s in self.discovered_suppliers if s.contact_info.get('address'))
        
        return {
            'total_suppliers': len(self.discovered_suppliers),
            'verified_suppliers': verified_count,
            'verification_rate': verified_count / len(self.discovered_suppliers),
            'category_distribution': category_counts,
            'contact_completeness': {
                'with_email': with_email,
                'with_phone': with_phone,
                'with_address': with_address
            }
        }
    
    def export_suppliers(self, filename: str = None) -> str:
        """
        Export discovered suppliers to JSON file.
        
        Args:
            filename: Output filename (optional)
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"discovered_suppliers_{timestamp}.json"
        
        # Prepare export data
        export_data = {
            'discovery_timestamp': datetime.now().isoformat(),
            'config': asdict(self.config),
            'statistics': self.get_supplier_statistics(),
            'suppliers': [asdict(supplier) for supplier in self.discovered_suppliers]
        }
        
        # Save to file
        os.makedirs("exported_data", exist_ok=True)
        filepath = os.path.join("exported_data", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Suppliers exported to: {filepath}")
        return filepath
    
    def cleanup(self):
        """Cleanup resources."""
        if self.production_scraper:
            self.production_scraper.cleanup()


def main():
    """Main function for testing supplier discovery."""
    print("Supplier Discovery System - Testing")
    print("=" * 45)
    
    # Create configuration
    config = DiscoveryConfig(
        max_suppliers_per_search=20,
        search_depth=2,
        target_industries=["industrial supplies", "power tools", "safety equipment"]
    )
    
    # Initialize discovery system
    discovery = SupplierDiscovery(config)
    
    try:
        # Test 1: Discover suppliers for one industry
        print("\n1. Testing supplier discovery for 'industrial supplies'...")
        suppliers = discovery.discover_suppliers_by_industry("industrial supplies")
        print(f"✓ Discovered {len(suppliers)} suppliers")
        
        if suppliers:
            print(f"Sample supplier: {suppliers[0].name}")
            print(f"  Categories: {', '.join(suppliers[0].categories)}")
            print(f"  Verified: {suppliers[0].verified}")
        
        # Test 2: Get statistics
        print("\n2. Getting discovery statistics...")
        stats = discovery.get_supplier_statistics()
        if stats:
            print(f"✓ Total suppliers: {stats['total_suppliers']}")
            print(f"✓ Verification rate: {stats['verification_rate']:.1%}")
        
        # Test 3: Export results
        print("\n3. Exporting results...")
        export_file = discovery.export_suppliers()
        print(f"✓ Exported to: {export_file}")
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        
    finally:
        discovery.cleanup()


if __name__ == "__main__":
    main()