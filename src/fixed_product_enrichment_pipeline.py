#!/usr/bin/env python3
"""
Fixed Product Enrichment Pipeline for Horme POV

This is a production-ready enrichment pipeline that:
1. Processes all 17,266 products from Excel master data
2. Enriches them with real data from multiple sources
3. Implements proper rate limiting and error handling
4. Stores enriched data in database-compatible format
5. Generates comprehensive quality reports

Key Features:
- Real web scraping integration with horme.com.sg
- Supplier data integration
- Quality scoring and improvement tracking
- Rate limiting and respectful scraping
- Database storage preparation
- Comprehensive reporting
"""

import os
import sys
import json
import logging
import time
import asyncio
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field, asdict
import random
import hashlib
from urllib.parse import urljoin, quote
import traceback
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
# Optional imports - will fallback if not available
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

try:
    from fuzzywuzzy import fuzz, process
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False

# Note: horme_scraper module integration removed for simplified standalone operation

@dataclass
class EnrichmentConfig:
    """Configuration for the enrichment pipeline."""
    
    # Source file paths
    excel_file_path: str = "docs/reference/ProductData (Top 3 Cats).xlsx"
    scraped_data_directory: str = "sample_output"
    supplier_data_directory: str = "supplier_data"
    
    # Scraping configuration
    base_url: str = "https://horme.com.sg"
    rate_limit_seconds: float = 5.0  # Respectful scraping
    max_retries: int = 3
    timeout: int = 30
    batch_size: int = 50
    
    # Matching thresholds
    sku_exact_match_threshold: float = 100.0
    name_fuzzy_match_threshold: float = 85.0
    brand_fuzzy_match_threshold: float = 80.0
    
    # Quality scoring weights
    quality_weights: Dict[str, float] = field(default_factory=lambda: {
        "sku_completeness": 0.20,
        "name_completeness": 0.15,
        "description_completeness": 0.10,
        "price_completeness": 0.15,
        "specifications_completeness": 0.15,
        "images_completeness": 0.10,
        "brand_completeness": 0.05,
        "category_completeness": 0.05,
        "availability_completeness": 0.05
    })
    
    # Output settings
    output_directory: str = "enrichment_output"
    database_file: str = "enriched_products.db"
    enable_scraping: bool = True
    max_products_to_scrape: int = 100  # Limit for testing

@dataclass
class EnrichmentMetrics:
    """Track pipeline metrics."""
    
    pipeline_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Input statistics
    excel_products_loaded: int = 0
    scraped_products_loaded: int = 0
    supplier_products_loaded: int = 0
    
    # Processing statistics
    products_processed: int = 0
    products_enriched: int = 0
    successful_scrapes: int = 0
    failed_scrapes: int = 0
    
    # Quality statistics
    avg_quality_before: float = 0.0
    avg_quality_after: float = 0.0
    high_quality_products: int = 0  # >=80%
    medium_quality_products: int = 0  # 60-79%
    low_quality_products: int = 0  # <60%
    
    # Enrichment details
    pricing_found: int = 0
    specifications_found: int = 0
    images_found: int = 0
    availability_found: int = 0
    descriptions_enhanced: int = 0
    
    # Errors and warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        self.errors.append(f"{datetime.now().isoformat()}: {error}")
    
    def add_warning(self, warning: str) -> None:
        self.warnings.append(f"{datetime.now().isoformat()}: {warning}")
    
    def finish(self) -> None:
        self.end_time = datetime.now()
    
    def get_duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

class FixedProductEnrichmentPipeline:
    """
    Fixed and production-ready product enrichment pipeline.
    
    This pipeline:
    1. Loads 17,266 products from Excel master data
    2. Enriches them with web scraping and supplier data
    3. Implements quality scoring and improvement tracking
    4. Stores results in database-compatible format
    5. Generates comprehensive reports
    """
    
    def __init__(self, config: EnrichmentConfig):
        """Initialize the enrichment pipeline."""
        self.config = config
        self.metrics = EnrichmentMetrics(pipeline_id=f"enrichment_{int(time.time())}")
        
        # Create output directory first
        os.makedirs(self.config.output_directory, exist_ok=True)
        
        # Ensure absolute path for output directory
        self.config.output_directory = os.path.abspath(self.config.output_directory)
        
        # Setup logging after directory creation
        self.logger = self._setup_logging()
        
        # Initialize web session
        self.session = None
        
        # Data storage
        self.excel_products: List[Dict[str, Any]] = []
        self.scraped_products: List[Dict[str, Any]] = []
        self.supplier_products: List[Dict[str, Any]] = []
        self.enriched_products: List[Dict[str, Any]] = []
        
        self.logger.info(f"Fixed Product Enrichment Pipeline initialized")
        self.logger.info(f"Pipeline ID: {self.metrics.pipeline_id}")
        self.logger.info(f"Output directory: {self.config.output_directory}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging."""
        logger = logging.getLogger(f"enrichment_pipeline_{self.metrics.pipeline_id}")
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create log file
        log_file = os.path.join(self.config.output_directory, f"enrichment_{self.metrics.pipeline_id}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _simple_string_similarity(self, str1: str, str2: str) -> float:
        """Simple string similarity calculation without external dependencies."""
        if not str1 or not str2:
            return 0.0
        
        str1_lower = str1.lower()
        str2_lower = str2.lower()
        
        # Exact match
        if str1_lower == str2_lower:
            return 100.0
        
        # Contains match
        if str1_lower in str2_lower or str2_lower in str1_lower:
            shorter = min(len(str1_lower), len(str2_lower))
            longer = max(len(str1_lower), len(str2_lower))
            return (shorter / longer) * 90.0
        
        # Word overlap
        words1 = set(str1_lower.split())
        words2 = set(str2_lower.split())
        
        if words1 and words2:
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            if union > 0:
                return (intersection / union) * 80.0
        
        return 0.0
    
    def setup_web_session(self) -> requests.Session:
        """Setup robust web scraping session."""
        try:
            # Use cloudscraper if available, otherwise regular requests
            if CLOUDSCRAPER_AVAILABLE:
                self.logger.info("Using cloudscraper for enhanced anti-bot protection")
                session = cloudscraper.create_scraper(
                    browser={
                        'browser': 'chrome',
                        'platform': 'windows',
                        'mobile': False
                    }
                )
            else:
                self.logger.info("Using standard requests session")
                session = requests.Session()
            
            # Configure retry strategy
            retry_strategy = Retry(
                total=self.config.max_retries,
                backoff_factor=2,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"]
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Set realistic headers
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            })
            
            self.session = session
            self.logger.info("Web scraping session configured successfully")
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to setup web session: {e}")
            # Fallback to regular requests session
            session = requests.Session()
            session.timeout = self.config.timeout
            self.session = session
            return session
    
    def load_excel_products(self) -> bool:
        """Load products from Excel master data."""
        try:
            excel_path = Path(self.config.excel_file_path)
            if not excel_path.exists():
                self.metrics.add_error(f"Excel file not found: {excel_path}")
                return False
            
            self.logger.info(f"Loading Excel data from: {excel_path}")
            df = pd.read_excel(excel_path)
            
            # Clean and standardize data
            df = df.dropna(subset=['Product SKU'])
            df['Product SKU'] = df['Product SKU'].astype(str).str.strip()
            df['Description'] = df['Description'].fillna('').astype(str).str.strip()
            df['Category '] = df['Category '].fillna('').astype(str).str.strip()
            df['Brand '] = df['Brand '].fillna('NO BRAND').astype(str).str.strip()
            
            # Convert to standardized format
            for _, row in df.iterrows():
                product = {
                    'source': 'excel',
                    'sku': row['Product SKU'].strip(),
                    'name': row['Description'].strip(),
                    'description': row['Description'].strip(),
                    'category': row['Category '].strip(),
                    'brand': row['Brand '].strip(),
                    'catalogue_id': row.get('CatalogueItemID'),
                    'price': None,
                    'specifications': {},
                    'images': [],
                    'availability': None,
                    'source_url': None,
                    'quality_before_enrichment': self._calculate_base_quality({
                        'sku': row['Product SKU'].strip(),
                        'name': row['Description'].strip(),
                        'brand': row['Brand '].strip(),
                        'category': row['Category '].strip()
                    }),
                    'enrichment_metadata': {
                        'loaded_at': datetime.now().isoformat(),
                        'source': 'excel_master_data'
                    }
                }
                self.excel_products.append(product)
            
            self.metrics.excel_products_loaded = len(self.excel_products)
            self.logger.info(f" Loaded {len(self.excel_products):,} products from Excel")
            return True
            
        except Exception as e:
            self.metrics.add_error(f"Excel loading failed: {str(e)}")
            self.logger.error(f" Excel loading failed: {str(e)}")
            return False
    
    def load_existing_scraped_data(self) -> bool:
        """Load existing scraped data from sample_output directory."""
        try:
            scraped_dir = Path(self.config.scraped_data_directory)
            if not scraped_dir.exists():
                self.logger.warning(f"Scraped data directory not found: {scraped_dir}")
                return True  # Not an error, just no existing data
            
            json_files = list(scraped_dir.glob("*.json"))
            self.logger.info(f"Loading existing scraped data from {len(json_files)} files")
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Handle different JSON structures
                    if isinstance(data, list):
                        products = data
                    elif isinstance(data, dict) and 'products' in data:
                        products = data['products']
                    elif isinstance(data, dict) and 'sku' in data:
                        products = [data]
                    else:
                        continue
                    
                    # Standardize each product
                    for product in products:
                        if isinstance(product, dict) and product.get('sku'):
                            standardized = {
                                'source': 'scraped',
                                'sku': str(product.get('sku', '')).strip(),
                                'name': str(product.get('name', '')).strip(),
                                'description': str(product.get('description', '')).strip(),
                                'price': product.get('price'),
                                'brand': str(product.get('brand', '')).strip(),
                                'category': self._extract_category(product),
                                'specifications': product.get('specifications', {}),
                                'images': product.get('images', []),
                                'availability': product.get('availability', ''),
                                'source_url': product.get('url', ''),
                                'scraped_at': product.get('scraped_at'),
                                'enrichment_metadata': {
                                    'loaded_from_file': json_file.name,
                                    'loaded_at': datetime.now().isoformat()
                                }
                            }
                            self.scraped_products.append(standardized)
                            
                except Exception as e:
                    self.metrics.add_warning(f"Error loading {json_file}: {str(e)}")
            
            self.metrics.scraped_products_loaded = len(self.scraped_products)
            self.logger.info(f" Loaded {len(self.scraped_products):,} existing scraped products")
            return True
            
        except Exception as e:
            self.metrics.add_error(f"Scraped data loading failed: {str(e)}")
            self.logger.error(f" Scraped data loading failed: {str(e)}")
            return False
    
    def load_supplier_data(self) -> bool:
        """Load supplier data if available."""
        try:
            supplier_dir = Path(self.config.supplier_data_directory)
            if not supplier_dir.exists():
                self.logger.info("No supplier data directory found - continuing without supplier data")
                return True
            
            json_files = list(supplier_dir.glob("*.json"))
            self.logger.info(f"Loading supplier data from {len(json_files)} files")
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Handle different JSON structures
                    if isinstance(data, list):
                        products = data
                    elif isinstance(data, dict) and 'products' in data:
                        products = data['products']
                    else:
                        products = [data]
                    
                    # Extract supplier name from filename
                    supplier_name = json_file.stem
                    
                    # Standardize each product
                    for product in products:
                        if isinstance(product, dict):
                            standardized = {
                                'source': 'supplier',
                                'supplier_name': supplier_name,
                                'sku': str(product.get('sku', product.get('supplier_sku', ''))).strip(),
                                'name': str(product.get('name', product.get('product_name', ''))).strip(),
                                'description': str(product.get('description', '')).strip(),
                                'price': product.get('price', product.get('supplier_price')),
                                'brand': str(product.get('brand', '')).strip(),
                                'category': str(product.get('category', '')).strip(),
                                'specifications': product.get('specifications', {}),
                                'availability': product.get('availability', product.get('stock_status', '')),
                                'lead_time': product.get('lead_time', product.get('lead_time_days')),
                                'minimum_order_qty': product.get('minimum_order_qty', product.get('moq')),
                                'supplier_sku': product.get('supplier_sku', ''),
                                'enrichment_metadata': {
                                    'supplier': supplier_name,
                                    'loaded_from_file': json_file.name,
                                    'loaded_at': datetime.now().isoformat()
                                }
                            }
                            self.supplier_products.append(standardized)
                            
                except Exception as e:
                    self.metrics.add_warning(f"Error loading supplier file {json_file}: {str(e)}")
            
            self.metrics.supplier_products_loaded = len(self.supplier_products)
            self.logger.info(f" Loaded {len(self.supplier_products):,} supplier products")
            return True
            
        except Exception as e:
            self.metrics.add_error(f"Supplier data loading failed: {str(e)}")
            self.logger.error(f" Supplier data loading failed: {str(e)}")
            return False
    
    def _extract_category(self, product: Dict) -> str:
        """Extract category from various product formats."""
        categories = product.get('categories', [])
        if isinstance(categories, list) and categories:
            return str(categories[0]).strip()
        elif isinstance(categories, str):
            return categories.strip()
        else:
            return str(product.get('category', '')).strip()
    
    def scrape_products_intelligently(self, max_products: int = None) -> bool:
        """Intelligently scrape products that need enrichment."""
        if not self.config.enable_scraping:
            self.logger.info("Scraping disabled - skipping scraping phase")
            return True
        
        try:
            self.logger.info(" Starting intelligent product scraping...")
            
            # Setup web session
            self.setup_web_session()
            
            # Determine which products need scraping
            products_to_scrape = self._identify_products_for_scraping(max_products or self.config.max_products_to_scrape)
            
            if not products_to_scrape:
                self.logger.info("No products identified for scraping")
                return True
            
            self.logger.info(f" Identified {len(products_to_scrape)} products for scraping")
            
            # Scrape products in batches
            scraped_count = 0
            failed_count = 0
            
            for i, product in enumerate(products_to_scrape, 1):
                try:
                    self.logger.info(f" Scraping {i}/{len(products_to_scrape)}: {product['sku']} - {product['name'][:50]}...")
                    
                    # Generate potential URLs for this product
                    urls = self._generate_product_urls(product['sku'], product['name'])
                    
                    # Try to scrape from each URL
                    scraped_data = None
                    for url in urls:
                        scraped_data = self._scrape_product_page(url, product['sku'])
                        if scraped_data and scraped_data.get('found'):
                            break
                    
                    if scraped_data and scraped_data.get('found'):
                        # Enhance original product with scraped data
                        enriched_product = self._merge_scraped_data(product, scraped_data)
                        self.scraped_products.append(enriched_product)
                        scraped_count += 1
                        self.logger.info(f" Successfully scraped: {product['sku']}")
                    else:
                        failed_count += 1
                        self.logger.warning(f" Failed to scrape: {product['sku']}")
                    
                    # Rate limiting
                    time.sleep(self.config.rate_limit_seconds)
                    
                    # Progress update
                    if i % 10 == 0:
                        self.logger.info(f" Progress: {i}/{len(products_to_scrape)} processed, {scraped_count} successful, {failed_count} failed")
                    
                except Exception as e:
                    failed_count += 1
                    self.metrics.add_error(f"Error scraping {product.get('sku', 'unknown')}: {str(e)}")
                    self.logger.error(f" Error scraping {product.get('sku', 'unknown')}: {str(e)}")
            
            self.metrics.successful_scrapes = scraped_count
            self.metrics.failed_scrapes = failed_count
            
            self.logger.info(f" Scraping completed: {scraped_count} successful, {failed_count} failed")
            return True
            
        except Exception as e:
            self.metrics.add_error(f"Scraping phase failed: {str(e)}")
            self.logger.error(f" Scraping phase failed: {str(e)}")
            return False
    
    def _identify_products_for_scraping(self, max_products: int) -> List[Dict[str, Any]]:
        """Identify products that would benefit most from scraping."""
        # Get existing scraped SKUs to avoid duplicates
        existing_scraped_skus = {p.get('sku', '').strip().upper() for p in self.scraped_products}
        
        # Priority scoring for products that need enrichment
        candidates = []
        for product in self.excel_products:
            sku = product.get('sku', '').strip().upper()
            
            # Skip if already scraped
            if sku in existing_scraped_skus:
                continue
            
            # Calculate priority score
            priority_score = 0
            
            # Higher priority for products with brand (likely to have web presence)
            if product.get('brand') and product.get('brand') != 'NO BRAND':
                priority_score += 10
            
            # Higher priority for certain categories
            category = product.get('category', '').lower()
            if any(keyword in category for keyword in ['tools', 'hardware', 'safety']):
                priority_score += 5
            
            # Higher priority for SKUs that look like they might have web presence
            sku_lower = sku.lower()
            if any(pattern in sku_lower for pattern in ['tool', 'drill', 'hammer', 'bolt', 'screw']):
                priority_score += 3
            
            candidates.append({
                'product': product,
                'priority_score': priority_score,
                'sku': sku
            })
        
        # Sort by priority and take top candidates
        candidates.sort(key=lambda x: x['priority_score'], reverse=True)
        selected = [c['product'] for c in candidates[:max_products]]
        
        self.logger.info(f" Selected top {len(selected)} products for scraping based on priority scoring")
        return selected
    
    def _generate_product_urls(self, sku: str, name: str) -> List[str]:
        """Generate potential URLs for a product."""
        urls = []
        base_url = self.config.base_url
        
        # Direct SKU-based URLs
        sku_clean = sku.replace(' ', '').replace('-', '').replace('/', '')
        urls.extend([
            f"{base_url}/product/{sku}",
            f"{base_url}/products/{sku}",
            f"{base_url}/item/{sku}",
            f"{base_url}/p/{sku}",
            f"{base_url}/product/{sku_clean}",
            f"{base_url}/products/{sku_clean}",
        ])
        
        # Name-based URLs
        if name:
            name_slug = name.lower().replace(' ', '-').replace('/', '-')[:50]
            name_slug = ''.join(c for c in name_slug if c.isalnum() or c == '-')
            if name_slug:
                urls.extend([
                    f"{base_url}/product/{name_slug}",
                    f"{base_url}/products/{name_slug}",
                ])
        
        # Search URLs as fallback
        urls.extend([
            f"{base_url}/search?q={quote(sku)}",
            f"{base_url}/search?query={quote(sku)}",
            f"{base_url}/catalogsearch/result/?q={quote(sku)}",
        ])
        
        return urls
    
    def _scrape_product_page(self, url: str, sku: str) -> Dict[str, Any]:
        """Scrape a single product page."""
        scraped_data = {
            'url': url,
            'sku': sku,
            'found': False,
            'price': None,
            'availability': None,
            'specifications': {},
            'images': [],
            'description': None,
            'enhanced_name': None,
            'brand': None,
            'error': None
        }
        
        try:
            response = self.session.get(url, timeout=self.config.timeout)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check if this is actually a product page
                if self._is_product_page(soup, sku):
                    scraped_data['found'] = True
                    
                    # Extract enhanced product information
                    scraped_data['enhanced_name'] = self._extract_product_name(soup)
                    scraped_data['price'] = self._extract_price(soup)
                    scraped_data['availability'] = self._extract_availability(soup)
                    scraped_data['specifications'] = self._extract_specifications(soup)
                    scraped_data['images'] = self._extract_images(soup, url)
                    scraped_data['description'] = self._extract_description(soup)
                    scraped_data['brand'] = self._extract_brand(soup)
                    
                    self.logger.debug(f"Successfully scraped product data for: {sku}")
                
            else:
                scraped_data['error'] = f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            scraped_data['error'] = "Request timeout"
        except requests.exceptions.RequestException as e:
            scraped_data['error'] = f"Request error: {str(e)}"
        except Exception as e:
            scraped_data['error'] = f"Parsing error: {str(e)}"
            
        return scraped_data
    
    def _is_product_page(self, soup: BeautifulSoup, sku: str) -> bool:
        """Determine if the page contains actual product information."""
        # Look for product page indicators
        indicators = [
            soup.find(attrs={'itemprop': 'name'}),
            soup.find(attrs={'itemprop': 'price'}),
            soup.find(attrs={'itemprop': 'sku'}),
            soup.select_one('.product-name'),
            soup.select_one('.product-price'),
            soup.select_one('.product-title'),
            soup.select_one('[data-product-id]'),
            soup.select_one('.add-to-cart'),
            soup.select_one('.buy-now'),
            soup.select_one('.price'),
            soup.select_one('.product-details')
        ]
        
        # Also check if SKU appears in page text
        page_text = soup.get_text().lower()
        sku_in_text = sku.lower() in page_text
        
        return any(indicator for indicator in indicators) or sku_in_text
    
    def _extract_product_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract enhanced product name."""
        selectors = [
            '[itemprop="name"]',
            '.product-name',
            '.product-title',
            'h1.title',
            'h1',
            '.main-title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text().strip()
                if name and len(name) > 5:  # Meaningful name
                    return name
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract price information."""
        price_selectors = [
            '[itemprop="price"]',
            '.product-price',
            '.price',
            '.current-price',
            '.sale-price',
            '.regular-price',
            '[data-price]',
            '.price-current',
            '.price-now'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get_text() or element.get('content', '')
                price = self._clean_price(price_text)
                if price:
                    return price
        
        # Look for price patterns in text
        import re
        text = soup.get_text()
        price_patterns = [
            r'\$\s*(\d+\.?\d*)',
            r'SGD\s*(\d+\.?\d*)',
            r'S\$\s*(\d+\.?\d*)',
            r'Price:?\s*\$?(\d+\.?\d*)',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    price_val = float(matches[0])
                    if 0.1 <= price_val <= 10000:  # Reasonable price range
                        return f"S${price_val:.2f}"
                except ValueError:
                    continue
        
        return None
    
    def _clean_price(self, price_text: str) -> Optional[str]:
        """Clean and standardize price text."""
        if not price_text:
            return None
            
        import re
        # Remove extra whitespace and normalize
        price_text = re.sub(r'\\s+', ' ', price_text.strip())
        
        # Extract numeric value
        price_match = re.search(r'(\d+\.?\d*)', price_text)
        if price_match:
            try:
                price_val = float(price_match.group(1))
                if 0.1 <= price_val <= 10000:  # Reasonable range
                    return f"S${price_val:.2f}"
            except ValueError:
                pass
        
        return None
    
    def _extract_availability(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract availability status."""
        availability_selectors = [
            '.availability',
            '.stock-status',
            '.in-stock',
            '.out-of-stock',
            '[itemprop="availability"]',
            '.product-availability',
            '.stock-info'
        ]
        
        for selector in availability_selectors:
            element = soup.select_one(selector)
            if element:
                availability = element.get_text().strip()
                if availability:
                    return self._standardize_availability(availability)
        
        # Look for availability patterns in text
        text = soup.get_text().lower()
        if 'in stock' in text:
            return 'In Stock'
        elif 'out of stock' in text:
            return 'Out of Stock'
        elif 'available' in text:
            return 'Available'
        elif 'contact' in text and 'price' in text:
            return 'Contact for Price'
        
        return None
    
    def _standardize_availability(self, availability: str) -> str:
        """Standardize availability status."""
        availability = availability.lower().strip()
        
        if any(word in availability for word in ['in stock', 'available', 'ready']):
            return 'In Stock'
        elif any(word in availability for word in ['out of stock', 'unavailable', 'sold out']):
            return 'Out of Stock'
        elif any(word in availability for word in ['contact', 'call', 'inquiry']):
            return 'Contact for Price'
        elif any(word in availability for word in ['preorder', 'pre-order', 'coming soon']):
            return 'Pre-order'
        else:
            return availability.title()
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract product specifications."""
        specs = {}
        
        # Look for specification tables
        spec_tables = soup.find_all('table', class_=lambda x: x and any(word in x.lower() for word in ['spec', 'detail', 'feature']))
        
        for table in spec_tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) == 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    if key and value and len(key) < 100 and len(value) < 500:
                        specs[key] = value
        
        # Look for specification lists
        spec_lists = soup.find_all(['ul', 'ol'], class_=lambda x: x and 'spec' in x.lower())
        
        for spec_list in spec_lists:
            items = spec_list.find_all('li')
            for item in items:
                text = item.get_text().strip()
                if ':' in text:
                    parts = text.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        if key and value and len(key) < 100 and len(value) < 500:
                            specs[key] = value
        
        return specs
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract product images."""
        images = []
        
        img_selectors = [
            '.product-image img',
            '.product-gallery img',
            '.product-photos img',
            '[itemprop="image"]',
            '.main-image img',
            '.hero-image img',
            '.product-thumb img',
            '.zoom-image'
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
                    
                    if src not in images and 'http' in src and not any(skip in src for skip in ['logo', 'icon', 'banner']):
                        images.append(src)
        
        return images[:5]  # Limit to 5 images
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract enhanced product description."""
        desc_selectors = [
            '[itemprop="description"]',
            '.product-description',
            '.description',
            '.product-summary',
            '.summary',
            '.product-details',
            '.product-info'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                desc = element.get_text().strip()
                if desc and len(desc) > 20:  # Meaningful description
                    return desc[:1000]  # Limit length
        
        return None
    
    def _extract_brand(self, soup: BeautifulSoup) -> Optional[str]:
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
                brand = element.get_text().strip()
                if brand and len(brand) > 1:
                    return brand
        
        return None
    
    def _merge_scraped_data(self, original_product: Dict[str, Any], scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge scraped data with original product."""
        enriched = original_product.copy()
        enriched['source'] = 'scraped'
        
        # Update with scraped data
        if scraped_data.get('enhanced_name'):
            enriched['name'] = scraped_data['enhanced_name']
        if scraped_data.get('price'):
            enriched['price'] = scraped_data['price']
        if scraped_data.get('availability'):
            enriched['availability'] = scraped_data['availability']
        if scraped_data.get('specifications'):
            enriched['specifications'] = scraped_data['specifications']
        if scraped_data.get('images'):
            enriched['images'] = scraped_data['images']
        if scraped_data.get('description'):
            enriched['description'] = scraped_data['description']
        if scraped_data.get('brand') and scraped_data['brand'] != 'NO BRAND':
            enriched['brand'] = scraped_data['brand']
        
        # Update enrichment metadata
        enriched['enrichment_metadata'].update({
            'scraped_at': datetime.now().isoformat(),
            'scraped_from_url': scraped_data.get('url'),
            'scraping_successful': scraped_data.get('found', False),
            'scraping_error': scraped_data.get('error')
        })
        
        return enriched
    
    def enrich_all_products(self) -> bool:
        """Enrich all products by merging data from different sources."""
        try:
            self.logger.info(" Starting comprehensive product enrichment...")
            
            # Create lookup for scraped and supplier data
            scraped_lookup = {p.get('sku', '').strip().upper(): p for p in self.scraped_products}
            supplier_lookup = {p.get('sku', '').strip().upper(): p for p in self.supplier_products}
            
            # Enrich each Excel product
            for product in self.excel_products:
                sku = product.get('sku', '').strip().upper()
                
                enriched_product = product.copy()
                enrichments_applied = []
                
                # Check for scraped data
                if sku in scraped_lookup:
                    scraped_product = scraped_lookup[sku]
                    enriched_product = self._merge_data_sources(enriched_product, scraped_product, 'scraped')
                    enrichments_applied.append('scraped_data')
                
                # Check for supplier data
                if sku in supplier_lookup:
                    supplier_product = supplier_lookup[sku]
                    enriched_product = self._merge_data_sources(enriched_product, supplier_product, 'supplier')
                    enrichments_applied.append('supplier_data')
                
                # Calculate quality scores
                quality_before = enriched_product.get('quality_before_enrichment', 0)
                quality_after = self._calculate_quality_score(enriched_product)
                
                enriched_product['quality_score'] = quality_after
                enriched_product['quality_improvement'] = quality_after - quality_before
                enriched_product['enrichments_applied'] = enrichments_applied
                
                # Update enrichment metadata
                enriched_product['enrichment_metadata'].update({
                    'enriched_at': datetime.now().isoformat(),
                    'enrichments_applied': enrichments_applied,
                    'quality_before': quality_before,
                    'quality_after': quality_after,
                    'quality_improvement': quality_after - quality_before
                })
                
                self.enriched_products.append(enriched_product)
                
                # Update metrics
                self._update_enrichment_metrics(enriched_product, enrichments_applied)
            
            self.metrics.products_processed = len(self.enriched_products)
            self.logger.info(f" Enriched {len(self.enriched_products):,} products")
            
            # Calculate final quality statistics
            self._calculate_final_quality_statistics()
            
            return True
            
        except Exception as e:
            self.metrics.add_error(f"Product enrichment failed: {str(e)}")
            self.logger.error(f" Product enrichment failed: {str(e)}")
            return False
    
    def _merge_data_sources(self, base_product: Dict[str, Any], source_product: Dict[str, Any], source_type: str) -> Dict[str, Any]:
        """Merge data from different sources with intelligent conflict resolution."""
        merged = base_product.copy()
        
        # Merge based on data quality and source priority
        fields_to_merge = {
            'price': source_product.get('price'),
            'availability': source_product.get('availability'),
            'specifications': source_product.get('specifications', {}),
            'images': source_product.get('images', []),
            'source_url': source_product.get('source_url')
        }
        
        # Enhanced description if available
        if source_product.get('description') and len(source_product['description']) > len(merged.get('description', '')):
            merged['description'] = source_product['description']
        
        # Enhanced name if available
        if source_product.get('name') and len(source_product['name']) > len(merged.get('name', '')):
            merged['name'] = source_product['name']
        
        # Brand enhancement (prefer non-'NO BRAND' values)
        if source_product.get('brand') and source_product['brand'] != 'NO BRAND':
            merged['brand'] = source_product['brand']
        
        # Merge fields that add value
        for field, value in fields_to_merge.items():
            if value:
                if field == 'specifications' and isinstance(value, dict):
                    # Merge specifications
                    existing_specs = merged.get('specifications', {})
                    if isinstance(existing_specs, dict):
                        existing_specs.update(value)
                        merged['specifications'] = existing_specs
                    else:
                        merged['specifications'] = value
                elif field == 'images' and isinstance(value, list):
                    # Merge images
                    existing_images = merged.get('images', [])
                    if isinstance(existing_images, list):
                        for img in value:
                            if img not in existing_images:
                                existing_images.append(img)
                        merged['images'] = existing_images
                    else:
                        merged['images'] = value
                else:
                    # Direct assignment for other fields
                    merged[field] = value
        
        # Add source-specific data for supplier
        if source_type == 'supplier':
            supplier_fields = ['supplier_name', 'lead_time', 'minimum_order_qty', 'supplier_sku']
            for field in supplier_fields:
                if source_product.get(field):
                    merged[field] = source_product[field]
        
        return merged
    
    def _update_enrichment_metrics(self, product: Dict[str, Any], enrichments: List[str]) -> None:
        """Update enrichment metrics based on product data."""
        if enrichments:
            self.metrics.products_enriched += 1
        
        if product.get('price'):
            self.metrics.pricing_found += 1
        if product.get('specifications') and isinstance(product['specifications'], dict) and product['specifications']:
            self.metrics.specifications_found += 1
        if product.get('images') and isinstance(product['images'], list) and product['images']:
            self.metrics.images_found += 1
        if product.get('availability'):
            self.metrics.availability_found += 1
        if len(product.get('description', '')) > len(product.get('name', '')):
            self.metrics.descriptions_enhanced += 1
    
    def _calculate_base_quality(self, basic_product: Dict) -> float:
        """Calculate base quality score for comparison."""
        weights = self.config.quality_weights
        score = 0
        max_possible = sum(weights.values())
        
        if basic_product.get('sku'):
            score += weights['sku_completeness']
        if basic_product.get('name'):
            score += weights['name_completeness']
        if basic_product.get('brand'):
            score += weights['brand_completeness']
        if basic_product.get('category'):
            score += weights['category_completeness']
        
        return (score / max_possible) * 100 if max_possible > 0 else 0
    
    def _calculate_quality_score(self, product: Dict[str, Any]) -> float:
        """Calculate comprehensive quality score for a product."""
        weights = self.config.quality_weights
        score = 0
        
        # Completeness scoring
        if product.get('sku'):
            score += weights['sku_completeness']
        if product.get('name'):
            score += weights['name_completeness']
        if product.get('description'):
            score += weights['description_completeness']
        if product.get('price'):
            score += weights['price_completeness']
        if product.get('specifications') and isinstance(product['specifications'], dict) and product['specifications']:
            score += weights['specifications_completeness']
        if product.get('images') and isinstance(product['images'], list) and product['images']:
            score += weights['images_completeness']
        if product.get('brand'):
            score += weights['brand_completeness']
        if product.get('category'):
            score += weights['category_completeness']
        if product.get('availability'):
            score += weights['availability_completeness']
        
        max_possible = sum(weights.values())
        return (score / max_possible) * 100 if max_possible > 0 else 0
    
    def _calculate_final_quality_statistics(self) -> None:
        """Calculate final quality statistics for all products."""
        if not self.enriched_products:
            return
        
        total_quality_before = 0
        total_quality_after = 0
        high_quality = 0
        medium_quality = 0
        low_quality = 0
        
        for product in self.enriched_products:
            quality_before = product.get('quality_before_enrichment', 0)
            quality_after = product.get('quality_score', 0)
            
            total_quality_before += quality_before
            total_quality_after += quality_after
            
            if quality_after >= 80:
                high_quality += 1
            elif quality_after >= 60:
                medium_quality += 1
            else:
                low_quality += 1
        
        self.metrics.avg_quality_before = total_quality_before / len(self.enriched_products)
        self.metrics.avg_quality_after = total_quality_after / len(self.enriched_products)
        self.metrics.high_quality_products = high_quality
        self.metrics.medium_quality_products = medium_quality
        self.metrics.low_quality_products = low_quality
    
    def save_enriched_products_to_database(self) -> bool:
        """Save enriched products to SQLite database."""
        try:
            db_path = os.path.join(self.config.output_directory, self.config.database_file)
            self.logger.info(f" Saving enriched products to database: {db_path}")
            
            # Create database connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enriched_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE NOT NULL,
                    name TEXT,
                    description TEXT,
                    category TEXT,
                    brand TEXT,
                    price TEXT,
                    availability TEXT,
                    specifications TEXT,  -- JSON
                    images TEXT,  -- JSON
                    source_url TEXT,
                    quality_score REAL,
                    quality_improvement REAL,
                    enrichments_applied TEXT,  -- JSON
                    enrichment_metadata TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert products
            inserted_count = 0
            for product in self.enriched_products:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO enriched_products 
                        (sku, name, description, category, brand, price, availability, 
                         specifications, images, source_url, quality_score, quality_improvement,
                         enrichments_applied, enrichment_metadata, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        product.get('sku', ''),
                        product.get('name', ''),
                        product.get('description', ''),
                        product.get('category', ''),
                        product.get('brand', ''),
                        product.get('price', ''),
                        product.get('availability', ''),
                        json.dumps(product.get('specifications', {})),
                        json.dumps(product.get('images', [])),
                        product.get('source_url', ''),
                        product.get('quality_score', 0),
                        product.get('quality_improvement', 0),
                        json.dumps(product.get('enrichments_applied', [])),
                        json.dumps(product.get('enrichment_metadata', {}))
                    ))
                    inserted_count += 1
                except Exception as e:
                    self.metrics.add_warning(f"Failed to insert product {product.get('sku', 'unknown')}: {str(e)}")
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sku ON enriched_products(sku)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quality ON enriched_products(quality_score)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON enriched_products(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_brand ON enriched_products(brand)')
            
            conn.commit()
            conn.close()
            
            self.logger.info(f" Saved {inserted_count:,} products to database")
            return True
            
        except Exception as e:
            self.metrics.add_error(f"Database save failed: {str(e)}")
            self.logger.error(f" Database save failed: {str(e)}")
            return False
    
    def generate_comprehensive_report(self) -> bool:
        """Generate comprehensive enrichment report."""
        try:
            self.logger.info(" Generating comprehensive enrichment report...")
            
            # Calculate final statistics
            self.metrics.finish()
            
            # Generate report data
            report_data = {
                "pipeline_execution": {
                    "pipeline_id": self.metrics.pipeline_id,
                    "start_time": self.metrics.start_time.isoformat(),
                    "end_time": self.metrics.end_time.isoformat() if self.metrics.end_time else None,
                    "duration_seconds": self.metrics.get_duration(),
                    "duration_formatted": str(timedelta(seconds=int(self.metrics.get_duration())))
                },
                "data_sources": {
                    "excel_master_products": self.metrics.excel_products_loaded,
                    "existing_scraped_products": self.metrics.scraped_products_loaded,
                    "supplier_products": self.metrics.supplier_products_loaded,
                    "total_input_products": (self.metrics.excel_products_loaded + 
                                           self.metrics.scraped_products_loaded + 
                                           self.metrics.supplier_products_loaded)
                },
                "scraping_results": {
                    "scraping_enabled": self.config.enable_scraping,
                    "successful_scrapes": self.metrics.successful_scrapes,
                    "failed_scrapes": self.metrics.failed_scrapes,
                    "scraping_success_rate": (self.metrics.successful_scrapes / 
                                            max(self.metrics.successful_scrapes + self.metrics.failed_scrapes, 1)) * 100
                },
                "enrichment_results": {
                    "total_products_processed": self.metrics.products_processed,
                    "products_enriched": self.metrics.products_enriched,
                    "enrichment_rate": (self.metrics.products_enriched / max(self.metrics.products_processed, 1)) * 100,
                    "pricing_found": self.metrics.pricing_found,
                    "specifications_found": self.metrics.specifications_found,
                    "images_found": self.metrics.images_found,
                    "availability_found": self.metrics.availability_found,
                    "descriptions_enhanced": self.metrics.descriptions_enhanced
                },
                "quality_analysis": {
                    "average_quality_before": self.metrics.avg_quality_before,
                    "average_quality_after": self.metrics.avg_quality_after,
                    "average_improvement": self.metrics.avg_quality_after - self.metrics.avg_quality_before,
                    "high_quality_products": self.metrics.high_quality_products,
                    "medium_quality_products": self.metrics.medium_quality_products,
                    "low_quality_products": self.metrics.low_quality_products,
                    "quality_distribution": {
                        "high_quality_percentage": (self.metrics.high_quality_products / max(self.metrics.products_processed, 1)) * 100,
                        "medium_quality_percentage": (self.metrics.medium_quality_products / max(self.metrics.products_processed, 1)) * 100,
                        "low_quality_percentage": (self.metrics.low_quality_products / max(self.metrics.products_processed, 1)) * 100
                    }
                },
                "coverage_analysis": {
                    "pricing_coverage": (self.metrics.pricing_found / max(self.metrics.products_processed, 1)) * 100,
                    "specifications_coverage": (self.metrics.specifications_found / max(self.metrics.products_processed, 1)) * 100,
                    "images_coverage": (self.metrics.images_found / max(self.metrics.products_processed, 1)) * 100,
                    "availability_coverage": (self.metrics.availability_found / max(self.metrics.products_processed, 1)) * 100
                },
                "recommendations": self._generate_recommendations(),
                "configuration_used": asdict(self.config),
                "errors_and_warnings": {
                    "error_count": len(self.metrics.errors),
                    "warning_count": len(self.metrics.warnings),
                    "recent_errors": self.metrics.errors[-5:] if self.metrics.errors else [],
                    "recent_warnings": self.metrics.warnings[-5:] if self.metrics.warnings else []
                }
            }
            
            # Save comprehensive JSON report
            report_file = os.path.join(self.config.output_directory, f"enrichment_report_{self.metrics.pipeline_id}.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            # Save CSV summary
            self._generate_csv_summary(report_data)
            
            # Generate HTML report
            self._generate_html_report(report_data)
            
            self.logger.info(f" Comprehensive report generated: {report_file}")
            return True
            
        except Exception as e:
            self.metrics.add_error(f"Report generation failed: {str(e)}")
            self.logger.error(f" Report generation failed: {str(e)}")
            return False
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on results."""
        recommendations = []
        
        # Quality recommendations
        high_quality_pct = (self.metrics.high_quality_products / max(self.metrics.products_processed, 1)) * 100
        if high_quality_pct >= 80:
            recommendations.append("Excellent data quality achieved! Consider this pipeline ready for production.")
        elif high_quality_pct >= 60:
            recommendations.append("Good data quality achieved. Focus on improving low-quality products for better results.")
        else:
            recommendations.append("Data quality needs improvement. Consider expanding scraping coverage and supplier data sources.")
        
        # Coverage recommendations
        pricing_coverage = (self.metrics.pricing_found / max(self.metrics.products_processed, 1)) * 100
        if pricing_coverage < 30:
            recommendations.append("Low pricing coverage. Implement alternative pricing strategies or supplier integrations.")
        
        specs_coverage = (self.metrics.specifications_found / max(self.metrics.products_processed, 1)) * 100
        if specs_coverage < 40:
            recommendations.append("Limited specification data. Consider manufacturer data integration or manual specification entry.")
        
        # Scraping recommendations
        if self.config.enable_scraping:
            scraping_success = (self.metrics.successful_scrapes / max(self.metrics.successful_scrapes + self.metrics.failed_scrapes, 1)) * 100
            if scraping_success < 30:
                recommendations.append("Low scraping success rate. Review website structure changes and implement additional scraping strategies.")
        
        # Performance recommendations
        processing_rate = self.metrics.products_processed / max(self.metrics.get_duration(), 1)
        if processing_rate < 10:
            recommendations.append("Consider optimizing processing performance or implementing parallel processing for large datasets.")
        
        # Coverage target achievement
        total_coverage = (self.metrics.products_enriched / max(self.metrics.products_processed, 1)) * 100
        if total_coverage >= 80:
            recommendations.append(" Target of 80%+ product enrichment achieved! Pipeline is ready for production deployment.")
        else:
            recommendations.append(f"Current enrichment coverage: {total_coverage:.1f}%. Work towards 80%+ target by expanding data sources.")
        
        return recommendations
    
    def _generate_csv_summary(self, report_data: Dict[str, Any]) -> None:
        """Generate CSV summary for easy analysis."""
        try:
            summary_data = [
                ["Metric", "Value", "Description"],
                ["Pipeline ID", self.metrics.pipeline_id, "Unique pipeline execution identifier"],
                ["Duration (seconds)", report_data["pipeline_execution"]["duration_seconds"], "Total execution time"],
                ["Products Processed", self.metrics.products_processed, "Total products processed"],
                ["Products Enriched", self.metrics.products_enriched, "Products successfully enriched"],
                ["Enrichment Rate (%)", f"{(self.metrics.products_enriched / max(self.metrics.products_processed, 1)) * 100:.1f}", "Percentage of products enriched"],
                ["Average Quality Before (%)", f"{self.metrics.avg_quality_before:.1f}", "Average quality score before enrichment"],
                ["Average Quality After (%)", f"{self.metrics.avg_quality_after:.1f}", "Average quality score after enrichment"],
                ["Quality Improvement (%)", f"{self.metrics.avg_quality_after - self.metrics.avg_quality_before:.1f}", "Average quality improvement"],
                ["High Quality Products", self.metrics.high_quality_products, "Products with quality score ≥80%"],
                ["Medium Quality Products", self.metrics.medium_quality_products, "Products with quality score 60-79%"],
                ["Low Quality Products", self.metrics.low_quality_products, "Products with quality score <60%"],
                ["Pricing Coverage (%)", f"{(self.metrics.pricing_found / max(self.metrics.products_processed, 1)) * 100:.1f}", "Percentage of products with pricing"],
                ["Specifications Coverage (%)", f"{(self.metrics.specifications_found / max(self.metrics.products_processed, 1)) * 100:.1f}", "Percentage of products with specifications"],
                ["Images Coverage (%)", f"{(self.metrics.images_found / max(self.metrics.products_processed, 1)) * 100:.1f}", "Percentage of products with images"],
                ["Availability Coverage (%)", f"{(self.metrics.availability_found / max(self.metrics.products_processed, 1)) * 100:.1f}", "Percentage of products with availability info"],
                ["Successful Scrapes", self.metrics.successful_scrapes, "Number of successful web scraping operations"],
                ["Failed Scrapes", self.metrics.failed_scrapes, "Number of failed web scraping operations"],
                ["Errors", len(self.metrics.errors), "Total number of errors encountered"],
                ["Warnings", len(self.metrics.warnings), "Total number of warnings encountered"]
            ]
            
            csv_file = os.path.join(self.config.output_directory, f"enrichment_summary_{self.metrics.pipeline_id}.csv")
            df = pd.DataFrame(summary_data, columns=["Metric", "Value", "Description"])
            df.to_csv(csv_file, index=False)
            
            self.logger.info(f" CSV summary saved: {csv_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate CSV summary: {str(e)}")
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> None:
        """Generate executive HTML report."""
        try:
            enrichment_rate = (self.metrics.products_enriched / max(self.metrics.products_processed, 1)) * 100
            quality_improvement = self.metrics.avg_quality_after - self.metrics.avg_quality_before
            target_achievement = " ACHIEVED" if enrichment_rate >= 80 else " IN PROGRESS"
            
            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>HORME POV - Product Enrichment Report</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
                    .container {{ max-width: 1200px; margin: 0 auto; background: white; min-height: 100vh; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                    .header h1 {{ font-size: 2.5em; margin: 0; }}
                    .header p {{ font-size: 1.2em; margin: 10px 0 0 0; opacity: 0.9; }}
                    .content {{ padding: 30px; }}
                    .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                    .summary-card {{ background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                    .summary-number {{ font-size: 2.5em; font-weight: bold; color: #667eea; margin-bottom: 5px; }}
                    .summary-label {{ color: #6c757d; font-weight: 600; }}
                    .section {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 10px; border-left: 4px solid #667eea; }}
                    .achievement {{ background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); border-left-color: #28a745; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                    .progress-bar {{ width: 100%; height: 20px; background-color: #e9ecef; border-radius: 10px; overflow: hidden; }}
                    .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); transition: width 1s ease; }}
                    .recommendations {{ background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); border-left: 4px solid #ffc107; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                    .table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                    .table th {{ background: #667eea; color: white; padding: 12px; text-align: left; }}
                    .table td {{ padding: 12px; border-bottom: 1px solid #e9ecef; }}
                    .success {{ color: #28a745; font-weight: bold; }}
                    .warning {{ color: #ffc107; font-weight: bold; }}
                    .info {{ color: #17a2b8; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1> HORME POV Product Enrichment</h1>
                        <p>Fixed Pipeline Execution Report</p>
                        <p>Pipeline ID: {self.metrics.pipeline_id} | {self.metrics.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <div class="content">
                        <div class="achievement">
                            <h2> Target Achievement Status: {target_achievement}</h2>
                            <p><strong>Enrichment Rate: {enrichment_rate:.1f}%</strong> (Target: 80%+)</p>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {min(enrichment_rate, 100)}%"></div>
                            </div>
                            <p>Successfully processed <strong>{self.metrics.products_processed:,}</strong> products with an average quality improvement of <strong>{quality_improvement:.1f}%</strong></p>
                        </div>
                        
                        <div class="summary-grid">
                            <div class="summary-card">
                                <div class="summary-number">{self.metrics.products_processed:,}</div>
                                <div class="summary-label">Products Processed</div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-number">{enrichment_rate:.1f}%</div>
                                <div class="summary-label">Enrichment Rate</div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-number">{self.metrics.avg_quality_after:.1f}%</div>
                                <div class="summary-label">Final Quality Score</div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-number">+{quality_improvement:.1f}%</div>
                                <div class="summary-label">Quality Improvement</div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-number">{self.metrics.get_duration():.0f}s</div>
                                <div class="summary-label">Execution Time</div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-number">{self.metrics.high_quality_products:,}</div>
                                <div class="summary-label">High Quality Products</div>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2> Data Sources Integration</h2>
                            <table class="table">
                                <tr><th>Source</th><th>Products Loaded</th><th>Status</th></tr>
                                <tr><td>Excel Master Data</td><td class="success">{self.metrics.excel_products_loaded:,}</td><td class="success"> Complete</td></tr>
                                <tr><td>Scraped Web Data</td><td class="info">{self.metrics.scraped_products_loaded:,}</td><td class="info">ℹ Available</td></tr>
                                <tr><td>Supplier Data</td><td class="warning">{self.metrics.supplier_products_loaded:,}</td><td class="warning"> Limited</td></tr>
                            </table>
                        </div>
                        
                        <div class="section">
                            <h2> Quality Distribution</h2>
                            <table class="table">
                                <tr><th>Quality Level</th><th>Count</th><th>Percentage</th><th>Target</th></tr>
                                <tr><td>High Quality (≥80%)</td><td class="success">{self.metrics.high_quality_products:,}</td><td>{(self.metrics.high_quality_products/max(self.metrics.products_processed,1)*100):.1f}%</td><td class="success">Excellent</td></tr>
                                <tr><td>Medium Quality (60-79%)</td><td class="warning">{self.metrics.medium_quality_products:,}</td><td>{(self.metrics.medium_quality_products/max(self.metrics.products_processed,1)*100):.1f}%</td><td class="warning">Good</td></tr>
                                <tr><td>Low Quality (<60%)</td><td style="color: #dc3545;">{self.metrics.low_quality_products:,}</td><td>{(self.metrics.low_quality_products/max(self.metrics.products_processed,1)*100):.1f}%</td><td style="color: #dc3545;">Needs Improvement</td></tr>
                            </table>
                        </div>
                        
                        <div class="section">
                            <h2> Enrichment Coverage Analysis</h2>
                            <table class="table">
                                <tr><th>Data Type</th><th>Products Found</th><th>Coverage</th><th>Status</th></tr>
                                <tr><td>Pricing Information</td><td>{self.metrics.pricing_found:,}</td><td>{(self.metrics.pricing_found/max(self.metrics.products_processed,1)*100):.1f}%</td><td class="{'success' if self.metrics.pricing_found/max(self.metrics.products_processed,1)*100 >= 50 else 'warning'}">{' Good' if self.metrics.pricing_found/max(self.metrics.products_processed,1)*100 >= 50 else ' Limited'}</td></tr>
                                <tr><td>Specifications</td><td>{self.metrics.specifications_found:,}</td><td>{(self.metrics.specifications_found/max(self.metrics.products_processed,1)*100):.1f}%</td><td class="{'success' if self.metrics.specifications_found/max(self.metrics.products_processed,1)*100 >= 40 else 'warning'}">{' Good' if self.metrics.specifications_found/max(self.metrics.products_processed,1)*100 >= 40 else ' Limited'}</td></tr>
                                <tr><td>Product Images</td><td>{self.metrics.images_found:,}</td><td>{(self.metrics.images_found/max(self.metrics.products_processed,1)*100):.1f}%</td><td class="{'success' if self.metrics.images_found/max(self.metrics.products_processed,1)*100 >= 30 else 'warning'}">{' Good' if self.metrics.images_found/max(self.metrics.products_processed,1)*100 >= 30 else ' Limited'}</td></tr>
                                <tr><td>Availability Status</td><td>{self.metrics.availability_found:,}</td><td>{(self.metrics.availability_found/max(self.metrics.products_processed,1)*100):.1f}%</td><td class="{'success' if self.metrics.availability_found/max(self.metrics.products_processed,1)*100 >= 30 else 'warning'}">{' Good' if self.metrics.availability_found/max(self.metrics.products_processed,1)*100 >= 30 else ' Limited'}</td></tr>
                            </table>
                        </div>
                        
                        <div class="recommendations">
                            <h2> Key Recommendations</h2>
                            <ul>
                                {''.join([f'<li>{rec}</li>' for rec in report_data.get('recommendations', [])])}
                            </ul>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            '''
            
            html_file = os.path.join(self.config.output_directory, f"enrichment_report_{self.metrics.pipeline_id}.html")
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f" HTML report generated: {html_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {str(e)}")
    
    def run_complete_pipeline(self) -> bool:
        """Execute the complete fixed enrichment pipeline."""
        try:
            self.logger.info(" Starting Fixed Product Enrichment Pipeline")
            self.logger.info(f"Target: Enrich {self.config.max_products_to_scrape} products with 80%+ coverage")
            
            # Stage 1: Load all data sources
            self.logger.info(" Stage 1: Loading data sources...")
            if not self.load_excel_products():
                return False
            
            self.load_existing_scraped_data()
            self.load_supplier_data()
            
            # Stage 2: Intelligent scraping (if enabled)
            if self.config.enable_scraping:
                self.logger.info(" Stage 2: Intelligent product scraping...")
                self.scrape_products_intelligently()
            else:
                self.logger.info("⏭ Stage 2: Scraping disabled - using existing data only")
            
            # Stage 3: Comprehensive enrichment
            self.logger.info(" Stage 3: Comprehensive product enrichment...")
            if not self.enrich_all_products():
                return False
            
            # Stage 4: Database storage
            self.logger.info(" Stage 4: Database storage...")
            self.save_enriched_products_to_database()
            
            # Stage 5: Comprehensive reporting
            self.logger.info(" Stage 5: Comprehensive reporting...")
            self.generate_comprehensive_report()
            
            # Success summary
            enrichment_rate = (self.metrics.products_enriched / max(self.metrics.products_processed, 1)) * 100
            quality_improvement = self.metrics.avg_quality_after - self.metrics.avg_quality_before
            
            self.logger.info(" PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
            self.logger.info(f" Results Summary:")
            self.logger.info(f"   • Products Processed: {self.metrics.products_processed:,}")
            self.logger.info(f"   • Enrichment Rate: {enrichment_rate:.1f}% (Target: 80%+)")
            self.logger.info(f"   • Quality Improvement: +{quality_improvement:.1f}%")
            self.logger.info(f"   • High Quality Products: {self.metrics.high_quality_products:,}")
            self.logger.info(f"   • Execution Time: {self.metrics.get_duration():.2f} seconds")
            
            if enrichment_rate >= 80:
                self.logger.info(" TARGET ACHIEVED: 80%+ enrichment coverage reached!")
            else:
                self.logger.info(f" Progress: {enrichment_rate:.1f}% towards 80% target")
            
            return True
            
        except Exception as e:
            self.metrics.add_error(f"Pipeline execution failed: {str(e)}")
            self.logger.error(f" Pipeline execution failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

def main():
    """Main execution function."""
    print("=" * 80)
    print("HORME POV - Fixed Product Enrichment Pipeline")
    print("=" * 80)
    print()
    print("This pipeline will:")
    print("1. Load 17,266 products from Excel master data")
    print("2. Enrich them with web scraping and existing data")
    print("3. Implement quality scoring and improvement tracking")
    print("4. Store results in database-compatible format")
    print("5. Generate comprehensive reports")
    print("6. Target: 80%+ products with enriched data")
    print()
    
    # Create configuration
    config = EnrichmentConfig()
    
    # Adjust for testing/production
    config.enable_scraping = True  # Set to False to disable scraping
    config.max_products_to_scrape = 50  # Increase for production
    
    print(f"Configuration:")
    print(f"  • Scraping enabled: {config.enable_scraping}")
    print(f"  • Max products to scrape: {config.max_products_to_scrape}")
    print(f"  • Rate limit: {config.rate_limit_seconds} seconds")
    print(f"  • Output directory: {config.output_directory}")
    print()
    
    # Create and run pipeline
    pipeline = FixedProductEnrichmentPipeline(config)
    
    success = pipeline.run_complete_pipeline()
    
    print("\n" + "=" * 80)
    if success:
        print(" PIPELINE COMPLETED SUCCESSFULLY")
        
        # Display final metrics
        enrichment_rate = (pipeline.metrics.products_enriched / max(pipeline.metrics.products_processed, 1)) * 100
        quality_improvement = pipeline.metrics.avg_quality_after - pipeline.metrics.avg_quality_before
        
        print(f"\n FINAL RESULTS:")
        print(f"   • Products Processed: {pipeline.metrics.products_processed:,}")
        print(f"   • Products Enriched: {pipeline.metrics.products_enriched:,}")
        print(f"   • Enrichment Rate: {enrichment_rate:.1f}%")
        print(f"   • Average Quality Improvement: +{quality_improvement:.1f}%")
        print(f"   • High Quality Products (≥80%): {pipeline.metrics.high_quality_products:,}")
        print(f"   • Medium Quality Products (60-79%): {pipeline.metrics.medium_quality_products:,}")
        print(f"   • Low Quality Products (<60%): {pipeline.metrics.low_quality_products:,}")
        print(f"   • Execution Time: {pipeline.metrics.get_duration():.2f} seconds")
        
        print(f"\n OUTPUT FILES:")
        if os.path.exists(config.output_directory):
            output_files = [f for f in os.listdir(config.output_directory) 
                          if f.endswith(('.json', '.html', '.csv', '.db', '.log'))]
            for file in sorted(output_files):
                print(f"   • {file}")
        
        if enrichment_rate >= 80:
            print(f"\n TARGET ACHIEVED! {enrichment_rate:.1f}% enrichment coverage reached!")
            print(" Pipeline is ready for production deployment.")
        else:
            print(f"\n Progress: {enrichment_rate:.1f}% towards 80% target")
            print(" Consider expanding data sources or scraping coverage.")
        
    else:
        print(" PIPELINE FAILED")
        print("Check the log files for detailed error information.")
    
    print("=" * 80)

if __name__ == "__main__":
    main()