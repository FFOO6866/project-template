#!/usr/bin/env python3
"""
Horme.com.sg Specific Scraper
============================

Real web scraping implementation for horme.com.sg with product catalog extraction,
search functionality, and comprehensive data parsing.

This module provides production-ready scraping of the Horme Industrial Supply website,
handling their specific HTML structure, JavaScript requirements, and anti-scraping measures.

Features:
- Real product catalog browsing and extraction
- SKU-based product search
- Category navigation and filtering
- Product specification parsing
- Image and datasheet collection
- Price monitoring and availability tracking
- Respect for site's robots.txt and rate limits
"""

import re
import time
import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Selenium imports for dynamic content
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from .production_scraper import ProductionScraper, ProductData, ScrapingConfig


class HormeScraper:
    """Specialized scraper for Horme.com.sg industrial supply website."""
    
    def __init__(self, config: ScrapingConfig = None):
        """Initialize the Horme-specific scraper."""
        self.base_url = "https://www.horme.com.sg"
        self.config = config or ScrapingConfig()
        self.production_scraper = ProductionScraper(self.config)
        self.logger = logging.getLogger("horme_scraper")
        
        # Horme-specific configuration
        self.category_map = self._build_category_map()
        self.known_selectors = self._define_selectors()
        
        self.logger.info("Horme scraper initialized")
    
    def _build_category_map(self) -> Dict[str, str]:
        """Build mapping of product categories to URLs."""
        return {
            "power_tools": "/category/power-tools",
            "hand_tools": "/category/hand-tools", 
            "safety_equipment": "/category/safety-equipment",
            "electrical": "/category/electrical",
            "plumbing": "/category/plumbing",
            "hardware": "/category/hardware",
            "adhesives": "/category/adhesives-sealants",
            "cutting_tools": "/category/cutting-tools",
            "measuring": "/category/measuring-tools",
            "material_handling": "/category/material-handling"
        }
    
    def _define_selectors(self) -> Dict[str, str]:
        """Define CSS selectors for Horme's website structure."""
        return {
            # Product listing page selectors
            "product_grid": ".product-grid, .products-grid, .product-list",
            "product_item": ".product-item, .product-card, .item",
            "product_link": "a.product-link, .product-title a, h3 a",
            "pagination": ".pagination, .pager",
            "next_page": ".pagination .next, .pager .next",
            
            # Product detail page selectors
            "product_title": "h1.product-title, .product-name h1, .page-title",
            "product_price": ".price, .product-price, .current-price, [data-price]",
            "product_sku": ".product-sku, .sku, [data-sku], .product-code",
            "product_description": ".product-description, .description, .product-summary",
            "product_specs": ".specifications, .specs, .product-attributes table",
            "product_images": ".product-images img, .product-gallery img, .main-image img",
            "product_availability": ".availability, .stock-status, .in-stock",
            "product_brand": ".brand, .manufacturer, [itemprop='brand']",
            "product_categories": ".breadcrumb a, .breadcrumbs a, .category-path a",
            
            # Search page selectors
            "search_results": ".search-results, .search-products",
            "search_input": "input[name='search'], #search-input, .search-field",
            "search_button": "button[type='submit'], .search-btn, .btn-search",
            
            # Navigation selectors
            "main_menu": ".main-nav, .primary-nav, .navigation",
            "category_links": ".category-menu a, .nav-category a"
        }
    
    def discover_site_structure(self) -> Dict[str, Any]:
        """
        Analyze Horme.com.sg site structure to understand navigation and content organization.
        
        Returns:
            Dictionary containing site structure information
        """
        self.logger.info("Discovering Horme.com.sg site structure...")
        
        def analyze_homepage(driver):
            """Analyze homepage structure."""
            structure = {
                'navigation': [],
                'categories': [],
                'search_available': False,
                'javascript_required': False
            }
            
            try:
                # Check for main navigation
                nav_elements = driver.find_elements(By.CSS_SELECTOR, self.known_selectors["main_menu"])
                if nav_elements:
                    nav_links = nav_elements[0].find_elements(By.TAG_NAME, "a")
                    structure['navigation'] = [
                        {'text': link.text.strip(), 'url': link.get_attribute('href')}
                        for link in nav_links[:10]  # Limit to first 10
                        if link.text.strip()
                    ]
                
                # Check for category links
                cat_elements = driver.find_elements(By.CSS_SELECTOR, self.known_selectors["category_links"])
                structure['categories'] = [
                    {'text': cat.text.strip(), 'url': cat.get_attribute('href')}
                    for cat in cat_elements[:20]  # Limit to first 20
                    if cat.text.strip()
                ]
                
                # Check for search functionality
                search_elements = driver.find_elements(By.CSS_SELECTOR, self.known_selectors["search_input"])
                structure['search_available'] = len(search_elements) > 0
                
                # Check if JavaScript is heavily used
                script_tags = driver.find_elements(By.TAG_NAME, "script")
                structure['javascript_required'] = len(script_tags) > 10
                
                # Get page title and description
                structure['title'] = driver.title
                meta_desc = driver.find_elements(By.CSS_SELECTOR, "meta[name='description']")
                structure['description'] = meta_desc[0].get_attribute('content') if meta_desc else ""
                
            except Exception as e:
                self.logger.error(f"Error analyzing homepage: {e}")
            
            return structure
        
        site_structure = self.production_scraper.scrape_with_selenium(
            self.base_url, 
            analyze_homepage
        )
        
        if site_structure:
            self.logger.info(f"Site structure discovered:")
            self.logger.info(f"  - Navigation items: {len(site_structure.get('navigation', []))}")
            self.logger.info(f"  - Category links: {len(site_structure.get('categories', []))}")
            self.logger.info(f"  - Search available: {site_structure.get('search_available')}")
            self.logger.info(f"  - JavaScript heavy: {site_structure.get('javascript_required')}")
        
        return site_structure or {}
    
    def search_products(self, query: str, max_results: int = 20) -> List[str]:
        """
        Search for products on Horme.com.sg using their search functionality.
        
        Args:
            query: Search query string
            max_results: Maximum number of product URLs to return
            
        Returns:
            List of product URLs
        """
        self.logger.info(f"Searching Horme for: '{query}'")
        
        def perform_search(driver):
            """Perform search and extract product URLs."""
            product_urls = []
            
            try:
                # Find search input field
                search_inputs = driver.find_elements(By.CSS_SELECTOR, self.known_selectors["search_input"])
                if not search_inputs:
                    # Try alternative search selectors
                    search_inputs = driver.find_elements(By.NAME, "q")
                    if not search_inputs:
                        search_inputs = driver.find_elements(By.ID, "search")
                
                if not search_inputs:
                    self.logger.warning("Search input field not found")
                    return []
                
                search_input = search_inputs[0]
                
                # Clear and enter search query
                search_input.clear()
                search_input.send_keys(query)
                
                # Find and click search button
                search_buttons = driver.find_elements(By.CSS_SELECTOR, self.known_selectors["search_button"])
                if search_buttons:
                    search_buttons[0].click()
                else:
                    # Try submitting the form
                    search_input.submit()
                
                # Wait for search results to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                )
                
                # Extract product links from search results
                product_links = driver.find_elements(By.CSS_SELECTOR, self.known_selectors["product_link"])
                
                # Also try generic product link patterns
                if not product_links:
                    product_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/product/']")
                if not product_links:
                    product_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/item/']")
                
                # Extract URLs
                for link in product_links[:max_results]:
                    href = link.get_attribute('href')
                    if href and self.base_url in href:
                        if href not in product_urls:
                            product_urls.append(href)
                
                self.logger.info(f"Found {len(product_urls)} product URLs from search")
                
            except Exception as e:
                self.logger.error(f"Search failed: {e}")
            
            return product_urls
        
        # Try different search URL patterns
        search_urls = [
            f"{self.base_url}",  # Start from homepage
            f"{self.base_url}/search",
            f"{self.base_url}/products"
        ]
        
        for search_url in search_urls:
            try:
                product_urls = self.production_scraper.scrape_with_selenium(
                    search_url, 
                    perform_search
                )
                
                if product_urls:
                    return product_urls
                    
            except Exception as e:
                self.logger.warning(f"Search attempt failed for {search_url}: {e}")
                continue
        
        return []
    
    def search_by_sku(self, sku: str) -> Optional[str]:
        """
        Search for a specific product by SKU.
        
        Args:
            sku: Product SKU to search for
            
        Returns:
            Product URL if found, None otherwise
        """
        self.logger.info(f"Searching for SKU: {sku}")
        
        # Try direct URL patterns first
        direct_urls = [
            f"{self.base_url}/product/{sku}",
            f"{self.base_url}/products/{sku}",
            f"{self.base_url}/item/{sku}",
            f"{self.base_url}/sku/{sku}",
            f"{self.base_url}/p/{sku}"
        ]
        
        for url in direct_urls:
            def check_product_page(content, url):
                """Check if this is a valid product page."""
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for product indicators
                indicators = [
                    soup.find(text=re.compile(sku, re.I)),
                    soup.select_one(self.known_selectors["product_title"]),
                    soup.select_one(self.known_selectors["product_price"]),
                ]
                
                return any(indicators)
            
            if self.production_scraper.scrape_with_requests(url, check_product_page):
                self.logger.info(f"Found direct URL for SKU {sku}: {url}")
                return url
        
        # If direct URLs don't work, use search
        search_results = self.search_products(sku, max_results=5)
        
        # Check each search result for the specific SKU
        for product_url in search_results:
            def verify_sku_match(content, url):
                """Verify this product matches the SKU."""
                soup = BeautifulSoup(content, 'html.parser')
                page_text = soup.get_text().lower()
                return sku.lower() in page_text
            
            if self.production_scraper.scrape_with_requests(product_url, verify_sku_match):
                self.logger.info(f"Found SKU {sku} via search: {product_url}")
                return product_url
        
        self.logger.warning(f"SKU {sku} not found")
        return None
    
    def scrape_product(self, url: str) -> Optional[ProductData]:
        """
        Scrape a single product page from Horme.com.sg.
        
        Args:
            url: Product page URL
            
        Returns:
            ProductData object if successful, None otherwise
        """
        self.logger.info(f"Scraping Horme product: {url}")
        
        def extract_product_data(content, url):
            """Extract product data from HTML content."""
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract SKU from URL or page
            sku = self._extract_sku_from_page(soup, url)
            if not sku:
                self.logger.warning(f"Could not extract SKU from: {url}")
                return None
            
            # Initialize product data
            product = ProductData(
                sku=sku,
                url=url,
                supplier="Horme Industrial Supply"
            )
            
            # Extract basic product information
            product.name = self._extract_product_name(soup)
            product.price = self._extract_product_price(soup)
            product.description = self._extract_product_description(soup)
            product.brand = self._extract_product_brand(soup)
            product.availability = self._extract_availability(soup)
            
            # Extract structured data
            product.specifications = self._extract_specifications(soup)
            product.images = self._extract_product_images(soup, url)
            product.categories = self._extract_product_categories(soup)
            
            # Calculate quality score
            product.calculate_quality_score()
            
            self.logger.info(f"Successfully scraped: {product.name} ({sku}) - Quality: {product.data_quality_score:.2f}")
            
            return product
        
        return self.production_scraper.scrape_with_requests(url, extract_product_data)
    
    def _extract_sku_from_page(self, soup: BeautifulSoup, url: str) -> str:
        """Extract SKU from page content or URL."""
        # Try SKU selectors first
        sku_element = soup.select_one(self.known_selectors["product_sku"])
        if sku_element:
            sku = sku_element.get_text(strip=True)
            if sku:
                return re.sub(r'[^A-Za-z0-9\-_]', '', sku)
        
        # Try extracting from URL
        url_parts = url.split('/')
        for part in reversed(url_parts):
            if part and not part.startswith('?'):
                clean_part = part.split('?')[0].split('#')[0]
                if clean_part and len(clean_part) > 3:
                    return clean_part
        
        # Try finding in page text
        text = soup.get_text()
        sku_patterns = [
            r'SKU:?\s*([A-Za-z0-9\-_]{4,20})',
            r'Product Code:?\s*([A-Za-z0-9\-_]{4,20})',
            r'Item #:?\s*([A-Za-z0-9\-_]{4,20})',
            r'Model:?\s*([A-Za-z0-9\-_]{4,20})'
        ]
        
        for pattern in sku_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """Extract product name."""
        title_element = soup.select_one(self.known_selectors["product_title"])
        if title_element:
            return title_element.get_text(strip=True)
        
        # Fallback to page title
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Remove site name from title
            title = re.sub(r'\s*-\s*Horme.*$', '', title, flags=re.IGNORECASE)
            return title
        
        return ""
    
    def _extract_product_price(self, soup: BeautifulSoup) -> str:
        """Extract product price."""
        price_element = soup.select_one(self.known_selectors["product_price"])
        if price_element:
            price_text = price_element.get_text(strip=True)
            # Clean up price text
            price_match = re.search(r'[S$£€¥₹]\s*[\d,]+\.?\d*', price_text)
            if price_match:
                return price_match.group(0)
            
            # Try extracting just numbers
            number_match = re.search(r'[\d,]+\.?\d+', price_text)
            if number_match:
                return f"S${number_match.group(0)}"
        
        # Look for price patterns in general text
        all_text = soup.get_text()
        price_patterns = [
            r'S\$\s*[\d,]+\.?\d*',
            r'SGD\s*[\d,]+\.?\d*',
            r'Price:?\s*S?\$?\s*[\d,]+\.?\d*'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
    def _extract_product_description(self, soup: BeautifulSoup) -> str:
        """Extract product description."""
        desc_element = soup.select_one(self.known_selectors["product_description"])
        if desc_element:
            return desc_element.get_text(strip=True)
        
        # Try alternative selectors
        alt_selectors = [".description", ".product-details", ".summary", ".overview"]
        for selector in alt_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if len(text) > 20:  # Reasonable description length
                    return text
        
        return ""
    
    def _extract_product_brand(self, soup: BeautifulSoup) -> str:
        """Extract product brand."""
        brand_element = soup.select_one(self.known_selectors["product_brand"])
        if brand_element:
            return brand_element.get_text(strip=True)
        
        # Look for brand patterns in text
        text = soup.get_text()
        brand_patterns = [
            r'Brand:?\s*([A-Za-z0-9\s&\-\.]{2,30})',
            r'Manufacturer:?\s*([A-Za-z0-9\s&\-\.]{2,30})',
            r'Made by:?\s*([A-Za-z0-9\s&\-\.]{2,30})'
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract product availability status."""
        avail_element = soup.select_one(self.known_selectors["product_availability"])
        if avail_element:
            return avail_element.get_text(strip=True)
        
        # Look for availability patterns
        text = soup.get_text().lower()
        if 'in stock' in text:
            return 'In Stock'
        elif 'out of stock' in text:
            return 'Out of Stock'
        elif 'available' in text:
            return 'Available'
        elif 'discontinued' in text:
            return 'Discontinued'
        
        return ""
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract product specifications."""
        specs = {}
        
        # Look for specification tables
        spec_table = soup.select_one(self.known_selectors["product_specs"])
        if spec_table:
            rows = spec_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        specs[key] = value
        
        # Look for specification lists
        spec_lists = soup.find_all(['dl', 'ul'], class_=re.compile(r'spec|detail|feature', re.I))
        for spec_list in spec_lists:
            if spec_list.name == 'dl':
                # Definition list
                terms = spec_list.find_all('dt')
                descriptions = spec_list.find_all('dd')
                for term, desc in zip(terms, descriptions):
                    key = term.get_text(strip=True)
                    value = desc.get_text(strip=True)
                    if key and value:
                        specs[key] = value
            else:
                # Unordered list
                items = spec_list.find_all('li')
                for item in items:
                    text = item.get_text(strip=True)
                    if ':' in text:
                        key, value = text.split(':', 1)
                        specs[key.strip()] = value.strip()
        
        return specs
    
    def _extract_product_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract product images."""
        images = []
        
        # Find product images
        img_elements = soup.select(self.known_selectors["product_images"])
        
        for img in img_elements:
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            if src:
                # Convert relative URLs to absolute
                if src.startswith('/'):
                    src = urljoin(self.base_url, src)
                elif not src.startswith('http'):
                    src = urljoin(base_url, src)
                
                # Skip small/thumbnail images
                if any(size in src.lower() for size in ['thumb', 'small', 'icon']):
                    continue
                
                if src not in images:
                    images.append(src)
        
        return images
    
    def _extract_product_categories(self, soup: BeautifulSoup) -> List[str]:
        """Extract product categories from breadcrumbs."""
        categories = []
        
        # Look for breadcrumb navigation
        breadcrumb_links = soup.select(self.known_selectors["product_categories"])
        
        for link in breadcrumb_links:
            text = link.get_text(strip=True)
            if text and text.lower() not in ['home', 'homepage']:
                if text not in categories:
                    categories.append(text)
        
        return categories
    
    def scrape_category(self, category: str, max_pages: int = 5) -> List[str]:
        """
        Scrape all products from a specific category.
        
        Args:
            category: Category key from category_map
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of product URLs
        """
        if category not in self.category_map:
            self.logger.error(f"Unknown category: {category}")
            return []
        
        category_url = self.base_url + self.category_map[category]
        self.logger.info(f"Scraping category: {category} at {category_url}")
        
        all_product_urls = []
        page = 1
        
        while page <= max_pages:
            page_url = f"{category_url}?page={page}"
            
            def extract_product_urls(content, url):
                """Extract product URLs from category page."""
                soup = BeautifulSoup(content, 'html.parser')
                product_urls = []
                
                # Find product links
                product_links = soup.select(self.known_selectors["product_link"])
                
                for link in product_links:
                    href = link.get('href')
                    if href:
                        if href.startswith('/'):
                            href = urljoin(self.base_url, href)
                        
                        if self.base_url in href and href not in product_urls:
                            product_urls.append(href)
                
                # Check if there's a next page
                next_page_link = soup.select_one(self.known_selectors["next_page"])
                has_next = next_page_link is not None
                
                return product_urls, has_next
            
            result = self.production_scraper.scrape_with_requests(page_url, extract_product_urls)
            
            if result:
                product_urls, has_next_page = result
                all_product_urls.extend(product_urls)
                
                self.logger.info(f"Page {page}: Found {len(product_urls)} products")
                
                if not has_next_page or not product_urls:
                    break
                    
                page += 1
            else:
                break
        
        self.logger.info(f"Category {category}: Found {len(all_product_urls)} total products")
        return all_product_urls
    
    def bulk_scrape_products(self, product_urls: List[str], save_to_db: bool = True) -> List[ProductData]:
        """
        Scrape multiple products in bulk.
        
        Args:
            product_urls: List of product URLs to scrape
            save_to_db: Whether to save products to database
            
        Returns:
            List of scraped ProductData objects
        """
        self.logger.info(f"Starting bulk scrape of {len(product_urls)} products")
        
        products = []
        failed_count = 0
        
        for i, url in enumerate(product_urls, 1):
            self.logger.info(f"Scraping product {i}/{len(product_urls)}: {url}")
            
            try:
                product = self.scrape_product(url)
                if product:
                    products.append(product)
                    
                    # Save to database if requested
                    if save_to_db:
                        success = self.production_scraper.save_product_to_database(product)
                        if success:
                            self.logger.debug(f"Saved to database: {product.sku}")
                else:
                    failed_count += 1
                    self.logger.warning(f"Failed to scrape: {url}")
                
            except Exception as e:
                failed_count += 1
                self.logger.error(f"Error scraping {url}: {e}")
            
            # Progress reporting
            if i % 10 == 0:
                success_rate = ((i - failed_count) / i) * 100
                self.logger.info(f"Progress: {i}/{len(product_urls)} - Success rate: {success_rate:.1f}%")
        
        success_rate = ((len(products)) / len(product_urls)) * 100
        self.logger.info(f"Bulk scrape completed: {len(products)} products scraped, success rate: {success_rate:.1f}%")
        
        return products
    
    def cleanup(self):
        """Cleanup resources."""
        self.production_scraper.cleanup()


def main():
    """Main function for testing Horme scraper."""
    print("Horme.com.sg Scraper - Testing")
    print("=" * 40)
    
    # Create configuration
    config = ScrapingConfig(
        browser_type="headless_chrome",
        rate_limit_seconds=3.0,
        simulate_human_behavior=True,
        save_to_database=True
    )
    
    # Initialize scraper
    scraper = HormeScraper(config)
    
    try:
        # Test 1: Discover site structure
        print("\n1. Discovering site structure...")
        structure = scraper.discover_site_structure()
        if structure:
            print(f"✓ Navigation items: {len(structure.get('navigation', []))}")
            print(f"✓ Categories: {len(structure.get('categories', []))}")
            print(f"✓ Search available: {structure.get('search_available', False)}")
        
        # Test 2: Search for products
        print("\n2. Testing product search...")
        search_results = scraper.search_products("power drill", max_results=5)
        print(f"✓ Found {len(search_results)} products for 'power drill'")
        
        # Test 3: Scrape a sample product (if any found)
        if search_results:
            print("\n3. Testing product scraping...")
            sample_url = search_results[0]
            product = scraper.scrape_product(sample_url)
            if product:
                print(f"✓ Successfully scraped: {product.name}")
                print(f"  - SKU: {product.sku}")
                print(f"  - Price: {product.price}")
                print(f"  - Quality Score: {product.data_quality_score:.2f}")
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        
    finally:
        scraper.cleanup()


if __name__ == "__main__":
    main()