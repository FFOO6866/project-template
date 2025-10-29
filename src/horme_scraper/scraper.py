"""
Main scraper class for horme.com.sg
"""

import time
import requests
import logging
import uuid
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

from .models import ProductData, ScrapingConfig, ScrapingSession
from .utils import (
    get_random_headers, check_robots_txt, exponential_backoff,
    rate_limit_wait, clean_text, extract_price, save_json_data,
    save_csv_data, ensure_directory_exists, validate_url,
    parse_specifications
)


class HormeScraper:
    """
    Respectful web scraper for horme.com.sg
    
    Features:
    - Rate limiting based on robots.txt
    - Rotating user agents and headers
    - Retry logic with exponential backoff
    - Graceful error handling
    - Request/response logging
    - JSON data export
    """
    
    def __init__(self, config: ScrapingConfig = None):
        """Initialize the scraper with configuration."""
        self.config = config or ScrapingConfig()
        self.base_url = "https://horme.com.sg"
        self.session = requests.Session()
        self.logger = logging.getLogger("horme_scraper")
        
        # Rate limiting
        self.last_request_time = 0.0
        self.request_count = 0
        self.hourly_requests = {}
        
        # Robots.txt compliance
        self.robots_info = None
        self.robots_last_checked = 0
        
        # Session tracking
        self.current_session: Optional[ScrapingSession] = None
        
        # Initialize
        self._setup_session()
        self._check_robots_txt()
    
    def _setup_session(self) -> None:
        """Set up the requests session with default headers."""
        headers = get_random_headers()
        if self.config.custom_headers:
            headers.update(self.config.custom_headers)
        
        self.session.headers.update(headers)
        self.session.timeout = (self.config.connection_timeout, self.config.request_timeout)
    
    def _check_robots_txt(self) -> None:
        """Check robots.txt for compliance."""
        current_time = time.time()
        
        if (self.robots_info is None or 
            current_time - self.robots_last_checked > self.config.check_robots_txt_interval):
            
            self.logger.info("Checking robots.txt compliance...")
            self.robots_info = check_robots_txt(self.base_url)
            self.robots_last_checked = current_time
            
            if self.robots_info.get("success"):
                crawl_delay = self.robots_info.get("crawl_delay")
                if crawl_delay and crawl_delay > self.config.rate_limit_seconds:
                    self.config.rate_limit_seconds = crawl_delay
                    self.logger.info(f"Updated rate limit to {crawl_delay} seconds based on robots.txt")
                
                self.logger.info(f"Robots.txt check complete. Crawl delay: {self.config.rate_limit_seconds}s")
            else:
                self.logger.warning(f"Could not check robots.txt: {self.robots_info.get('error')}")
    
    def _wait_for_rate_limit(self) -> None:
        """Wait for rate limiting if necessary."""
        rate_limit_wait(self.last_request_time, self.config.rate_limit_seconds)
        
        # Check hourly rate limit
        current_hour = int(time.time() // 3600)
        if current_hour not in self.hourly_requests:
            self.hourly_requests = {current_hour: 0}  # Reset counter
        
        if self.hourly_requests[current_hour] >= self.config.max_requests_per_hour:
            wait_time = 3600 - (time.time() % 3600)
            self.logger.warning(f"Hourly rate limit reached. Waiting {wait_time:.0f} seconds...")
            time.sleep(wait_time)
            self.hourly_requests = {}
    
    def _update_headers(self) -> None:
        """Update headers with rotation if enabled."""
        if self.config.rotate_user_agents:
            headers = get_random_headers()
            if self.config.custom_headers:
                headers.update(self.config.custom_headers)
            self.session.headers.update(headers)
    
    def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """Make a web request with retry logic and rate limiting."""
        if not validate_url(url):
            self.logger.error(f"Invalid URL: {url}")
            return None
        
        # Check robots.txt compliance
        if self.config.respect_robots_txt and self.robots_info:
            if not self.robots_info.get("can_fetch_root", True):
                self.logger.warning(f"Robots.txt disallows fetching: {url}")
                return None
        
        self._check_robots_txt()  # Periodic robots.txt check
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Rate limiting
                self._wait_for_rate_limit()
                self.last_request_time = time.time()
                
                # Update headers for rotation
                self._update_headers()
                
                # Log request
                if self.config.log_requests:
                    self.logger.info(f"Making {method} request to: {url} (attempt {attempt + 1})")
                
                # Make request
                response = self.session.request(method, url, **kwargs)
                
                # Update counters
                self.request_count += 1
                current_hour = int(time.time() // 3600)
                self.hourly_requests[current_hour] = self.hourly_requests.get(current_hour, 0) + 1
                
                if self.current_session:
                    self.current_session.requests_made += 1
                
                # Check response
                response.raise_for_status()
                
                # Log successful response
                if self.config.log_responses:
                    self.logger.info(f"Successful response: {response.status_code} - {len(response.content)} bytes")
                
                if self.current_session:
                    self.current_session.successful_requests += 1
                
                return response
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Request failed (attempt {attempt + 1}): {e}"
                self.logger.warning(error_msg)
                
                if self.current_session:
                    self.current_session.failed_requests += 1
                    self.current_session.add_error(error_msg)
                
                if attempt < self.config.max_retries:
                    delay = exponential_backoff(
                        attempt, 
                        self.config.retry_base_delay,
                        self.config.retry_backoff_factor
                    )
                    self.logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    self.logger.error(f"All retry attempts failed for: {url}")
                    return None
        
        return None
    
    def start_session(self, session_id: str = None) -> str:
        """Start a new scraping session."""
        if not session_id:
            session_id = f"horme_scraping_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        self.current_session = ScrapingSession(session_id=session_id)
        self.logger.info(f"Started scraping session: {session_id}")
        return session_id
    
    def end_session(self) -> Optional[Dict[str, Any]]:
        """End the current scraping session and return statistics."""
        if not self.current_session:
            return None
        
        self.current_session.finish_session()
        session_data = self.current_session.to_dict()
        
        self.logger.info(f"Session {self.current_session.session_id} completed:")
        self.logger.info(f"  Duration: {session_data.get('duration_seconds', 0):.2f} seconds")
        self.logger.info(f"  Requests: {session_data['requests_made']}")
        self.logger.info(f"  Success rate: {session_data['success_rate']:.2%}")
        self.logger.info(f"  Products scraped: {session_data['products_scraped']}")
        
        # Save session data
        session_file = os.path.join(
            self.config.output_directory,
            f"session_{self.current_session.session_id}.json"
        )
        ensure_directory_exists(os.path.dirname(session_file))
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Session data saved to: {session_file}")
        except Exception as e:
            self.logger.error(f"Failed to save session data: {e}")
        
        self.current_session = None
        return session_data
    
    def search_products(self, query: str, max_results: int = 10) -> List[str]:
        """
        Search for products and return URLs.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of product URLs
        """
        self.logger.info(f"Searching for products: {query}")
        
        # Try different search URL patterns
        search_urls = [
            f"{self.base_url}/search?q={query}",
            f"{self.base_url}/search?query={query}",
            f"{self.base_url}/products/search?q={query}",
            f"{self.base_url}/catalog/search?query={query}"
        ]
        
        product_urls = []
        
        for search_url in search_urls:
            if len(product_urls) >= max_results:
                break
                
            response = self._make_request(search_url)
            if not response:
                continue
            
            try:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Common selectors for product links
                product_selectors = [
                    'a[href*="/product/"]',
                    'a[href*="/products/"]',
                    'a[href*="/item/"]',
                    '.product-item a',
                    '.product-link',
                    '.product a',
                    '[data-product-url]'
                ]
                
                for selector in product_selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href') or link.get('data-product-url')
                        if href:
                            if href.startswith('/'):
                                href = urljoin(self.base_url, href)
                            
                            if href not in product_urls and self.base_url in href:
                                product_urls.append(href)
                                
                                if len(product_urls) >= max_results:
                                    break
                    
                    if len(product_urls) >= max_results:
                        break
                
                if product_urls:
                    self.logger.info(f"Found {len(product_urls)} product URLs from {search_url}")
                    break
                    
            except Exception as e:
                self.logger.error(f"Error parsing search results from {search_url}: {e}")
                continue
        
        if not product_urls:
            self.logger.warning(f"No products found for query: {query}")
        
        return product_urls[:max_results]
    
    def search_by_sku(self, sku: str) -> Optional[str]:
        """
        Search for a product by SKU and return its URL.
        
        Args:
            sku: Product SKU to search for
            
        Returns:
            Product URL if found, None otherwise
        """
        self.logger.info(f"Searching for SKU: {sku}")
        
        # Try direct SKU search patterns
        search_patterns = [
            f"{self.base_url}/product/{sku}",
            f"{self.base_url}/products/{sku}",
            f"{self.base_url}/item/{sku}",
            f"{self.base_url}/sku/{sku}",
        ]
        
        # Try direct access first
        for url in search_patterns:
            response = self._make_request(url)
            if response and response.status_code == 200:
                # Verify it's actually a product page
                if self._is_product_page(response):
                    self.logger.info(f"Found product page for SKU {sku}: {url}")
                    return url
        
        # Try search query
        search_results = self.search_products(sku, max_results=5)
        
        # Check each result for the SKU
        for product_url in search_results:
            response = self._make_request(product_url)
            if response:
                try:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_text = soup.get_text().lower()
                    
                    if sku.lower() in page_text:
                        self.logger.info(f"Found SKU {sku} in product page: {product_url}")
                        return product_url
                        
                except Exception as e:
                    self.logger.error(f"Error checking product page for SKU: {e}")
                    continue
        
        self.logger.warning(f"Could not find product page for SKU: {sku}")
        return None
    
    def _is_product_page(self, response: requests.Response) -> bool:
        """Check if a response contains a product page."""
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for common product page indicators
            indicators = [
                soup.find(attrs={'itemprop': 'name'}),
                soup.find(attrs={'itemprop': 'price'}),
                soup.find(attrs={'itemprop': 'sku'}),
                soup.select_one('.product-name'),
                soup.select_one('.product-price'),
                soup.select_one('.product-title'),
                soup.select_one('[data-product-id]'),
                soup.select_one('.add-to-cart'),
                soup.select_one('.buy-now')
            ]
            
            return any(indicator for indicator in indicators)
            
        except Exception:
            return False
    
    def scrape_product(self, url: str) -> Optional[ProductData]:
        """
        Scrape product data from a product page.
        
        Args:
            url: Product page URL
            
        Returns:
            ProductData object if successful, None otherwise
        """
        self.logger.info(f"Scraping product: {url}")
        
        response = self._make_request(url)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract SKU from URL or page
            sku = self._extract_sku(url, soup)
            if not sku:
                self.logger.warning(f"Could not extract SKU from: {url}")
                return None
            
            # Initialize product data
            product = ProductData(sku=sku, url=url)
            
            # Extract product name
            product.name = self._extract_product_name(soup)
            
            # Extract price
            product.price = self._extract_price(soup)
            
            # Extract description
            product.description = self._extract_description(soup)
            
            # Extract specifications
            product.specifications = self._extract_specifications(soup)
            
            # Extract images
            product.images = self._extract_images(soup, url)
            
            # Extract categories
            product.categories = self._extract_categories(soup)
            
            # Extract availability
            product.availability = self._extract_availability(soup)
            
            # Extract brand
            product.brand = self._extract_brand(soup)
            
            self.logger.info(f"Successfully scraped product: {product.name} ({sku})")
            
            if self.current_session:
                self.current_session.products_scraped += 1
            
            return product
            
        except Exception as e:
            error_msg = f"Error scraping product {url}: {e}"
            self.logger.error(error_msg)
            if self.current_session:
                self.current_session.add_error(error_msg)
            return None
    
    def _extract_sku(self, url: str, soup: BeautifulSoup) -> str:
        """Extract SKU from URL or page content."""
        # Try to extract from URL
        url_parts = url.split('/')
        for part in reversed(url_parts):
            if part and not part.startswith('?'):
                # Remove query parameters
                clean_part = part.split('?')[0]
                if clean_part:
                    return clean_part
        
        # Try to extract from page content
        sku_selectors = [
            '[itemprop="sku"]',
            '.product-sku',
            '.sku',
            '[data-sku]',
            '.product-code',
            '.item-code'
        ]
        
        for selector in sku_selectors:
            element = soup.select_one(selector)
            if element:
                sku = clean_text(element.get_text() or element.get('content', ''))
                if sku:
                    return sku
        
        # Try to find SKU in text patterns
        import re
        text = soup.get_text()
        sku_patterns = [
            r'SKU:?\s*([A-Z0-9\-_]+)',
            r'Product Code:?\s*([A-Z0-9\-_]+)',
            r'Item Code:?\s*([A-Z0-9\-_]+)',
            r'Model:?\s*([A-Z0-9\-_]+)'
        ]
        
        for pattern in sku_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """Extract product name."""
        name_selectors = [
            '[itemprop="name"]',
            '.product-name',
            '.product-title',
            'h1.title',
            'h1',
            '.page-title',
            'title'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = clean_text(element.get_text() or element.get('content', ''))
                if name and len(name) > 3:  # Reasonable name length
                    return name
        
        return ""
    
    def _extract_price(self, soup: BeautifulSoup) -> str:
        """Extract product price."""
        price_selectors = [
            '[itemprop="price"]',
            '.product-price',
            '.price',
            '.current-price',
            '.sale-price',
            '[data-price]'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text() or element.get('content', '')
                price = extract_price(price_text)
                if price:
                    return price
        
        # Look for price patterns in general text
        price_areas = soup.find_all(['div', 'span', 'p'], 
                                   class_=lambda x: x and 'price' in x.lower())
        
        for area in price_areas:
            price_text = area.get_text()
            price = extract_price(price_text)
            if price:
                return price
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description."""
        desc_selectors = [
            '[itemprop="description"]',
            '.product-description',
            '.description',
            '.product-summary',
            '.summary',
            '.product-details'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                desc = clean_text(element.get_text())
                if desc and len(desc) > 10:  # Reasonable description length
                    return desc
        
        return ""
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract product specifications."""
        specs = {}
        
        # Look for specification tables
        spec_tables = soup.find_all('table', class_=lambda x: x and 'spec' in x.lower())
        
        for table in spec_tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) == 2:
                    key = clean_text(cells[0].get_text())
                    value = clean_text(cells[1].get_text())
                    if key and value:
                        specs[key] = value
        
        # Look for specification lists
        spec_lists = soup.find_all(['ul', 'ol'], 
                                  class_=lambda x: x and 'spec' in x.lower())
        
        for spec_list in spec_lists:
            items = spec_list.find_all('li')
            for item in items:
                text = clean_text(item.get_text())
                if ':' in text:
                    key, value = text.split(':', 1)
                    key = clean_text(key)
                    value = clean_text(value)
                    if key and value:
                        specs[key] = value
        
        # Look for specification divs
        spec_divs = soup.find_all('div', 
                                 class_=lambda x: x and ('spec' in x.lower() or 'detail' in x.lower()))
        
        for div in spec_divs:
            text = clean_text(div.get_text())
            parsed_specs = parse_specifications(text)
            specs.update(parsed_specs)
        
        return specs
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract product images."""
        images = []
        
        # Look for product images
        img_selectors = [
            '.product-image img',
            '.product-gallery img',
            '.product-photos img',
            '[itemprop="image"]',
            '.main-image img',
            '.hero-image img'
        ]
        
        for selector in img_selectors:
            img_elements = soup.select(selector)
            for img in img_elements:
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    if src.startswith('/'):
                        src = urljoin(base_url, src)
                    elif not src.startswith('http'):
                        src = urljoin(base_url, src)
                    
                    if src not in images and 'http' in src:
                        images.append(src)
        
        return images
    
    def _extract_categories(self, soup: BeautifulSoup) -> List[str]:
        """Extract product categories."""
        categories = []
        
        # Look for breadcrumbs
        breadcrumb_selectors = [
            '.breadcrumb a',
            '.breadcrumbs a',
            '[aria-label="breadcrumb"] a',
            '.navigation a'
        ]
        
        for selector in breadcrumb_selectors:
            links = soup.select(selector)
            for link in links:
                text = clean_text(link.get_text())
                if text and text.lower() not in ['home', 'homepage']:
                    categories.append(text)
        
        # Look for category tags
        category_selectors = [
            '.product-category',
            '.category',
            '.tags a',
            '.product-tags a'
        ]
        
        for selector in category_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = clean_text(element.get_text())
                if text and text not in categories:
                    categories.append(text)
        
        return categories
    
    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract product availability."""
        availability_selectors = [
            '.availability',
            '.stock-status',
            '.in-stock',
            '.out-of-stock',
            '[itemprop="availability"]'
        ]
        
        for selector in availability_selectors:
            element = soup.select_one(selector)
            if element:
                availability = clean_text(element.get_text() or element.get('content', ''))
                if availability:
                    return availability
        
        # Look for common availability patterns
        text = soup.get_text().lower()
        if 'in stock' in text:
            return 'In Stock'
        elif 'out of stock' in text:
            return 'Out of Stock'
        elif 'available' in text:
            return 'Available'
        
        return ""
    
    def _extract_brand(self, soup: BeautifulSoup) -> str:
        """Extract product brand."""
        brand_selectors = [
            '[itemprop="brand"]',
            '.product-brand',
            '.brand',
            '.manufacturer'
        ]
        
        for selector in brand_selectors:
            element = soup.select_one(selector)
            if element:
                brand = clean_text(element.get_text() or element.get('content', ''))
                if brand:
                    return brand
        
        return ""
    
    def scrape_products(self, product_urls: List[str]) -> List[ProductData]:
        """
        Scrape multiple products.
        
        Args:
            product_urls: List of product URLs to scrape
            
        Returns:
            List of ProductData objects
        """
        self.logger.info(f"Starting to scrape {len(product_urls)} products")
        
        products = []
        
        for i, url in enumerate(product_urls, 1):
            self.logger.info(f"Scraping product {i}/{len(product_urls)}: {url}")
            
            product = self.scrape_product(url)
            if product:
                products.append(product)
            
            # Progress update
            if i % 10 == 0:
                self.logger.info(f"Progress: {i}/{len(product_urls)} products scraped")
        
        self.logger.info(f"Completed scraping. Successfully scraped {len(products)} products")
        return products
    
    def save_products(self, products: List[ProductData], filename_base: str = None) -> Dict[str, bool]:
        """
        Save scraped products to files.
        
        Args:
            products: List of ProductData objects
            filename_base: Base filename (without extension)
            
        Returns:
            Dictionary with save results
        """
        if not filename_base:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_base = f"horme_products_{timestamp}"
        
        ensure_directory_exists(self.config.output_directory)
        
        # Convert products to dictionaries
        products_data = [product.to_dict() for product in products]
        
        results = {}
        
        # Save JSON
        if self.config.save_json:
            json_file = os.path.join(self.config.output_directory, f"{filename_base}.json")
            results['json'] = save_json_data(products_data, json_file)
            if results['json']:
                self.logger.info(f"Products saved to JSON: {json_file}")
        
        # Save CSV
        if self.config.save_csv:
            csv_file = os.path.join(self.config.output_directory, f"{filename_base}.csv")
            results['csv'] = save_csv_data(products_data, csv_file)
            if results['csv']:
                self.logger.info(f"Products saved to CSV: {csv_file}")
        
        return results