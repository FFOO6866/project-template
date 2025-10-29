"""
Supplier Scrapers - Modular Web Scrapers for Hardware Suppliers

This module provides specialized scraper classes for different hardware supplier
websites, with adaptive parsing and parallel processing capabilities.
"""

import asyncio
import aiohttp
import logging
import re
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import requests
import concurrent.futures
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProductInfo:
    """Comprehensive product information extracted from supplier websites."""
    sku: str
    name: str = ""
    brand: str = ""
    price: str = ""
    description: str = ""
    specifications: Dict[str, Any] = field(default_factory=dict)
    technical_specs: Dict[str, Any] = field(default_factory=dict)
    images: List[str] = field(default_factory=list)
    datasheets: List[str] = field(default_factory=list)
    manuals: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    compatibility: List[str] = field(default_factory=list)
    availability: str = ""
    supplier_url: str = ""
    scraped_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "sku": self.sku,
            "name": self.name,
            "brand": self.brand,
            "price": self.price,
            "description": self.description,
            "specifications": self.specifications,
            "technical_specs": self.technical_specs,
            "images": self.images,
            "datasheets": self.datasheets,
            "manuals": self.manuals,
            "categories": self.categories,
            "compatibility": self.compatibility,
            "availability": self.availability,
            "supplier_url": self.supplier_url,
            "scraped_at": self.scraped_at.isoformat()
        }


@dataclass
class ScrapingResult:
    """Results from a scraping operation."""
    success: bool
    products: List[ProductInfo] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    pages_scraped: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "products": [p.to_dict() for p in self.products],
            "errors": self.errors,
            "processing_time": self.processing_time,
            "pages_scraped": self.pages_scraped,
            "total_products": len(self.products)
        }


class BaseSupplierScraper(ABC):
    """
    Abstract base class for supplier-specific scrapers.
    
    Provides common functionality and enforces interface for all scrapers.
    """
    
    def __init__(self, rate_limit_seconds: float = 1.0, max_retries: int = 3):
        """
        Initialize base scraper.
        
        Args:
            rate_limit_seconds: Delay between requests per domain
            max_retries: Maximum retry attempts for failed requests
        """
        self.rate_limit_seconds = rate_limit_seconds
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.last_request_time = {}
        
    @abstractmethod
    def get_supplier_name(self) -> str:
        """Return the supplier name this scraper handles."""
        pass
    
    @abstractmethod
    def get_base_url(self) -> str:
        """Return the base URL for this supplier."""
        pass
    
    @abstractmethod
    def search_products(self, query: str, max_results: int = 50) -> List[str]:
        """
        Search for products and return product URLs.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of product URLs
        """
        pass
    
    @abstractmethod
    def scrape_product(self, product_url: str) -> Optional[ProductInfo]:
        """
        Scrape detailed product information from a product page.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            ProductInfo object or None if scraping failed
        """
        pass
    
    def _rate_limit(self, domain: str):
        """Apply rate limiting per domain."""
        current_time = time.time()
        last_time = self.last_request_time.get(domain, 0)
        time_diff = current_time - last_time
        
        if time_diff < self.rate_limit_seconds:
            sleep_time = self.rate_limit_seconds - time_diff
            time.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()
    
    def _make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with rate limiting and retry logic."""
        domain = urlparse(url).netloc
        self._rate_limit(domain)
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=15, **kwargs)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def _extract_pdf_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract PDF links from page (datasheets, manuals)."""
        pdf_links = []
        
        # Find all links that might be PDFs
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            link_text = link.get_text(strip=True).lower()
            
            # Check if it's a PDF link
            if (href.lower().endswith('.pdf') or 
                'pdf' in link_text or 
                'datasheet' in link_text or 
                'manual' in link_text or
                'specification' in link_text):
                
                full_url = urljoin(base_url, href)
                pdf_links.append(full_url)
        
        return pdf_links
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        return text
    
    def scrape_multiple_products(self, product_urls: List[str]) -> ScrapingResult:
        """
        Scrape multiple products with parallel processing.
        
        Args:
            product_urls: List of product URLs to scrape
            
        Returns:
            ScrapingResult with all scraped products and statistics
        """
        start_time = time.time()
        products = []
        errors = []
        
        # Use ThreadPoolExecutor for parallel scraping
        max_workers = min(5, len(product_urls))  # Limit concurrent requests
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit scraping tasks
            future_to_url = {
                executor.submit(self.scrape_product, url): url 
                for url in product_urls
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    product = future.result()
                    if product:
                        products.append(product)
                        logger.info(f"Successfully scraped: {product.name}")
                    else:
                        errors.append(f"Failed to scrape product at {url}")
                        
                except Exception as e:
                    error_msg = f"Error scraping {url}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
        
        processing_time = time.time() - start_time
        success = len(products) > 0
        
        result = ScrapingResult(
            success=success,
            products=products,
            errors=errors,
            processing_time=processing_time,
            pages_scraped=len(product_urls)
        )
        
        logger.info(f"Scraping completed: {len(products)} products, {len(errors)} errors, {processing_time:.2f}s")
        
        return result


class BoschScraper(BaseSupplierScraper):
    """Specialized scraper for Bosch Singapore website."""
    
    def get_supplier_name(self) -> str:
        return "Bosch"
    
    def get_base_url(self) -> str:
        return "https://www.bosch.com.sg"
    
    def search_products(self, query: str, max_results: int = 50) -> List[str]:
        """Search Bosch products."""
        search_url = f"{self.get_base_url()}/search"
        
        response = self._make_request(search_url, params={'q': query})
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        product_urls = []
        
        # Look for product links in search results
        product_links = soup.find_all('a', href=True)
        for link in product_links:
            href = link['href']
            if '/products/' in href or '/product/' in href:
                full_url = urljoin(self.get_base_url(), href)
                product_urls.append(full_url)
                
                if len(product_urls) >= max_results:
                    break
        
        return product_urls[:max_results]
    
    def scrape_product(self, product_url: str) -> Optional[ProductInfo]:
        """Scrape Bosch product details."""
        response = self._make_request(product_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic product information
        name = self._extract_product_name(soup)
        if not name:
            return None
        
        # Generate SKU from URL or find it in page
        sku = self._extract_sku(soup, product_url)
        
        # Extract other details
        price = self._extract_price(soup)
        description = self._extract_description(soup)
        specifications = self._extract_specifications(soup)
        images = self._extract_images(soup, product_url)
        categories = self._extract_categories(soup)
        
        # Extract PDF documents
        pdf_links = self._extract_pdf_links(soup, product_url)
        datasheets = [link for link in pdf_links if 'datasheet' in link.lower()]
        manuals = [link for link in pdf_links if 'manual' in link.lower()]
        
        product = ProductInfo(
            sku=sku,
            name=name,
            brand="Bosch",
            price=price,
            description=description,
            specifications=specifications,
            images=images,
            datasheets=datasheets,
            manuals=manuals,
            categories=categories,
            supplier_url=product_url
        )
        
        return product
    
    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """Extract product name from page."""
        selectors = [
            'h1.product-title',
            'h1.pdp-title', 
            '.product-name h1',
            'h1.product-header',
            '.product-header h1',
            'h1.page-title',
            '.product-info h1',
            'h1',
            '.title h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = self._clean_text(element.get_text())
                if text and len(text) > 3:  # Ensure meaningful product name
                    return text
        
        return ""
    
    def _extract_sku(self, soup: BeautifulSoup, url: str) -> str:
        """Extract or generate SKU."""
        # Try to find SKU in page
        sku_selectors = [
            '.product-number',
            '.part-number', 
            '.model-number',
            '[data-sku]'
        ]
        
        for selector in sku_selectors:
            element = soup.select_one(selector)
            if element:
                sku = element.get_text(strip=True)
                if sku:
                    return sku
        
        # Generate from URL
        url_parts = url.split('/')
        if url_parts:
            return url_parts[-1][:20]  # Use last part of URL as SKU
        
        return hashlib.md5(url.encode()).hexdigest()[:10]
    
    def _extract_price(self, soup: BeautifulSoup) -> str:
        """Extract price information."""
        price_selectors = [
            '.price',
            '.product-price',
            '.pdp-price',
            '[class*="price"]'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                if '$' in price_text or 'S$' in price_text:
                    return price_text
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description."""
        desc_selectors = [
            '.product-description',
            '.pdp-description',
            '.product-details',
            '.description',
            'meta[name="description"]'
        ]
        
        for selector in desc_selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element:
                    return element.get('content', '')
            else:
                element = soup.select_one(selector)
                if element:
                    return self._clean_text(element.get_text())
        
        return ""
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract technical specifications."""
        specs = {}
        
        # Look for specification tables or lists
        spec_sections = soup.find_all(['table', 'dl', 'div'], class_=re.compile(r'spec|technical|feature', re.I))
        
        for section in spec_sections:
            if section.name == 'table':
                rows = section.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = self._clean_text(cells[0].get_text())
                        value = self._clean_text(cells[1].get_text())
                        if key and value:
                            specs[key] = value
            
            elif section.name == 'dl':
                dts = section.find_all('dt')
                dds = section.find_all('dd')
                for dt, dd in zip(dts, dds):
                    key = self._clean_text(dt.get_text())
                    value = self._clean_text(dd.get_text())
                    if key and value:
                        specs[key] = value
        
        return specs
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract product images."""
        images = []
        
        # Find product images
        img_selectors = [
            '.product-image img',
            '.pdp-gallery img',
            '.product-gallery img',
            'img[class*="product"]'
        ]
        
        for selector in img_selectors:
            elements = soup.select(selector)
            for img in elements:
                src = img.get('src') or img.get('data-src')
                if src:
                    full_url = urljoin(base_url, src)
                    if full_url not in images:
                        images.append(full_url)
        
        return images[:5]  # Limit to 5 images
    
    def _extract_categories(self, soup: BeautifulSoup) -> List[str]:
        """Extract product categories from breadcrumbs."""
        categories = []
        
        # Look for breadcrumb navigation
        breadcrumb_selectors = [
            '.breadcrumb',
            '.breadcrumbs',
            'nav[aria-label="breadcrumb"]',
            '.navigation-path'
        ]
        
        for selector in breadcrumb_selectors:
            element = soup.select_one(selector)
            if element:
                links = element.find_all('a')
                for link in links:
                    category = self._clean_text(link.get_text())
                    if category and category.lower() not in ['home', 'products']:
                        categories.append(category)
        
        return categories


class KarcherScraper(BaseSupplierScraper):
    """Specialized scraper for Karcher Singapore website."""
    
    def get_supplier_name(self) -> str:
        return "Karcher"
    
    def get_base_url(self) -> str:
        return "https://www.karcher.com.sg"
    
    def search_products(self, query: str, max_results: int = 50) -> List[str]:
        """Search Karcher products."""
        search_url = f"{self.get_base_url()}/products"
        
        response = self._make_request(search_url, params={'search': query})
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        product_urls = []
        
        # Look for product links
        product_links = soup.find_all('a', href=True)
        for link in product_links:
            href = link['href']
            if '/product/' in href or '/products/' in href:
                full_url = urljoin(self.get_base_url(), href)
                product_urls.append(full_url)
                
                if len(product_urls) >= max_results:
                    break
        
        return product_urls[:max_results]
    
    def scrape_product(self, product_url: str) -> Optional[ProductInfo]:
        """Scrape Karcher product details."""
        response = self._make_request(product_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic information
        name = self._extract_product_name(soup)
        if not name:
            return None
        
        sku = self._extract_sku(soup, product_url)
        price = self._extract_price(soup)
        description = self._extract_description(soup)
        specifications = self._extract_specifications(soup)
        images = self._extract_images(soup, product_url)
        categories = self._extract_categories(soup)
        
        # Extract documents
        pdf_links = self._extract_pdf_links(soup, product_url)
        datasheets = [link for link in pdf_links if any(keyword in link.lower() for keyword in ['datasheet', 'spec', 'technical'])]
        manuals = [link for link in pdf_links if 'manual' in link.lower()]
        
        product = ProductInfo(
            sku=sku,
            name=name,
            brand="Karcher",
            price=price,
            description=description,
            specifications=specifications,
            images=images,
            datasheets=datasheets,
            manuals=manuals,
            categories=categories,
            supplier_url=product_url
        )
        
        return product


class ThreeMScraper(BaseSupplierScraper):
    """Specialized scraper for 3M Singapore website."""
    
    def get_supplier_name(self) -> str:
        return "3M"
    
    def get_base_url(self) -> str:
        return "https://www.3m.com.sg"
    
    def search_products(self, query: str, max_results: int = 50) -> List[str]:
        """Search 3M products."""
        search_url = f"{self.get_base_url()}/3M/en_SG/search/"
        
        response = self._make_request(search_url, params={'q': query})
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        product_urls = []
        
        # 3M specific product link patterns
        product_links = soup.find_all('a', href=True)
        for link in product_links:
            href = link['href']
            if '/product/' in href or '/p/' in href:
                full_url = urljoin(self.get_base_url(), href)
                product_urls.append(full_url)
                
                if len(product_urls) >= max_results:
                    break
        
        return product_urls[:max_results]
    
    def scrape_product(self, product_url: str) -> Optional[ProductInfo]:
        """Scrape 3M product details."""
        response = self._make_request(product_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        name = self._extract_product_name(soup)
        if not name:
            return None
        
        sku = self._extract_sku(soup, product_url)
        description = self._extract_description(soup)
        specifications = self._extract_specifications(soup)
        images = self._extract_images(soup, product_url)
        categories = self._extract_categories(soup)
        
        # 3M specific document extraction
        pdf_links = self._extract_pdf_links(soup, product_url)
        datasheets = [link for link in pdf_links if any(keyword in link.lower() for keyword in ['datasheet', 'technical', 'spec'])]
        manuals = [link for link in pdf_links if 'manual' in link.lower()]
        
        product = ProductInfo(
            sku=sku,
            name=name,
            brand="3M",
            description=description,
            specifications=specifications,
            images=images,
            datasheets=datasheets,
            manuals=manuals,
            categories=categories,
            supplier_url=product_url
        )
        
        return product


class DeWaltScraper(BaseSupplierScraper):
    """Specialized scraper for DeWalt Singapore website."""
    
    def get_supplier_name(self) -> str:
        return "DeWalt"
    
    def get_base_url(self) -> str:
        return "https://www.dewalt.com.sg"
    
    def search_products(self, query: str, max_results: int = 50) -> List[str]:
        """Search DeWalt products."""
        search_url = f"{self.get_base_url()}/products"
        
        response = self._make_request(search_url, params={'search': query})
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        product_urls = []
        
        # Look for product links
        product_links = soup.find_all('a', href=True)
        for link in product_links:
            href = link['href']
            if '/product/' in href or '/tools/' in href:
                full_url = urljoin(self.get_base_url(), href)
                product_urls.append(full_url)
                
                if len(product_urls) >= max_results:
                    break
        
        return product_urls[:max_results]
    
    def scrape_product(self, product_url: str) -> Optional[ProductInfo]:
        """Scrape DeWalt product details."""
        response = self._make_request(product_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        name = self._extract_product_name(soup)
        if not name:
            return None
        
        sku = self._extract_sku(soup, product_url)
        price = self._extract_price(soup)
        description = self._extract_description(soup)
        specifications = self._extract_specifications(soup)
        images = self._extract_images(soup, product_url)
        categories = self._extract_categories(soup)
        
        # Extract documents
        pdf_links = self._extract_pdf_links(soup, product_url)
        datasheets = [link for link in pdf_links if any(keyword in link.lower() for keyword in ['datasheet', 'spec', 'technical'])]
        manuals = [link for link in pdf_links if 'manual' in link.lower()]
        
        product = ProductInfo(
            sku=sku,
            name=name,
            brand="DeWalt",
            price=price,
            description=description,
            specifications=specifications,
            images=images,
            datasheets=datasheets,
            manuals=manuals,
            categories=categories,
            supplier_url=product_url
        )
        
        return product


class MilwaukeeScraper(BaseSupplierScraper):
    """Specialized scraper for Milwaukee Singapore website."""
    
    def get_supplier_name(self) -> str:
        return "Milwaukee"
    
    def get_base_url(self) -> str:
        return "https://www.milwaukeetool.com.sg"
    
    def search_products(self, query: str, max_results: int = 50) -> List[str]:
        """Search Milwaukee products."""
        search_url = f"{self.get_base_url()}/products"
        
        response = self._make_request(search_url, params={'q': query})
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        product_urls = []
        
        # Look for product links
        product_links = soup.find_all('a', href=True)
        for link in product_links:
            href = link['href']
            if '/product/' in href or '/tool/' in href:
                full_url = urljoin(self.get_base_url(), href)
                product_urls.append(full_url)
                
                if len(product_urls) >= max_results:
                    break
        
        return product_urls[:max_results]
    
    def scrape_product(self, product_url: str) -> Optional[ProductInfo]:
        """Scrape Milwaukee product details."""
        response = self._make_request(product_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        name = self._extract_product_name(soup)
        if not name:
            return None
        
        sku = self._extract_sku(soup, product_url)
        price = self._extract_price(soup)
        description = self._extract_description(soup)
        specifications = self._extract_specifications(soup)
        images = self._extract_images(soup, product_url)
        categories = self._extract_categories(soup)
        
        # Extract documents
        pdf_links = self._extract_pdf_links(soup, product_url)
        datasheets = [link for link in pdf_links if any(keyword in link.lower() for keyword in ['datasheet', 'spec', 'technical'])]
        manuals = [link for link in pdf_links if 'manual' in link.lower()]
        
        product = ProductInfo(
            sku=sku,
            name=name,
            brand="Milwaukee",
            price=price,
            description=description,
            specifications=specifications,
            images=images,
            datasheets=datasheets,
            manuals=manuals,
            categories=categories,
            supplier_url=product_url
        )
        
        return product


class MakitaScraper(BaseSupplierScraper):
    """Specialized scraper for Makita Singapore website."""
    
    def get_supplier_name(self) -> str:
        return "Makita"
    
    def get_base_url(self) -> str:
        return "https://www.makita.com.sg"
    
    def search_products(self, query: str, max_results: int = 50) -> List[str]:
        """Search Makita products."""
        search_url = f"{self.get_base_url()}/products"
        
        response = self._make_request(search_url, params={'search': query})
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        product_urls = []
        
        # Look for product links
        product_links = soup.find_all('a', href=True)
        for link in product_links:
            href = link['href']
            if '/product/' in href or '/tools/' in href:
                full_url = urljoin(self.get_base_url(), href)
                product_urls.append(full_url)
                
                if len(product_urls) >= max_results:
                    break
        
        return product_urls[:max_results]
    
    def scrape_product(self, product_url: str) -> Optional[ProductInfo]:
        """Scrape Makita product details."""
        response = self._make_request(product_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        name = self._extract_product_name(soup)
        if not name:
            return None
        
        sku = self._extract_sku(soup, product_url)
        price = self._extract_price(soup)
        description = self._extract_description(soup)
        specifications = self._extract_specifications(soup)
        images = self._extract_images(soup, product_url)
        categories = self._extract_categories(soup)
        
        # Extract documents
        pdf_links = self._extract_pdf_links(soup, product_url)
        datasheets = [link for link in pdf_links if any(keyword in link.lower() for keyword in ['datasheet', 'spec', 'technical'])]
        manuals = [link for link in pdf_links if 'manual' in link.lower()]
        
        product = ProductInfo(
            sku=sku,
            name=name,
            brand="Makita",
            price=price,
            description=description,
            specifications=specifications,
            images=images,
            datasheets=datasheets,
            manuals=manuals,
            categories=categories,
            supplier_url=product_url
        )
        
        return product


class StanleyScraper(BaseSupplierScraper):
    """Specialized scraper for Stanley Singapore website."""
    
    def get_supplier_name(self) -> str:
        return "Stanley"
    
    def get_base_url(self) -> str:
        return "https://www.stanleytools.com.sg"
    
    def search_products(self, query: str, max_results: int = 50) -> List[str]:
        """Search Stanley products."""
        search_url = f"{self.get_base_url()}/products"
        
        response = self._make_request(search_url, params={'q': query})
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        product_urls = []
        
        # Look for product links
        product_links = soup.find_all('a', href=True)
        for link in product_links:
            href = link['href']
            if '/product/' in href or '/tools/' in href:
                full_url = urljoin(self.get_base_url(), href)
                product_urls.append(full_url)
                
                if len(product_urls) >= max_results:
                    break
        
        return product_urls[:max_results]
    
    def scrape_product(self, product_url: str) -> Optional[ProductInfo]:
        """Scrape Stanley product details."""
        response = self._make_request(product_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        name = self._extract_product_name(soup)
        if not name:
            return None
        
        sku = self._extract_sku(soup, product_url)
        price = self._extract_price(soup)
        description = self._extract_description(soup)
        specifications = self._extract_specifications(soup)
        images = self._extract_images(soup, product_url)
        categories = self._extract_categories(soup)
        
        # Extract documents
        pdf_links = self._extract_pdf_links(soup, product_url)
        datasheets = [link for link in pdf_links if any(keyword in link.lower() for keyword in ['datasheet', 'spec', 'technical'])]
        manuals = [link for link in pdf_links if 'manual' in link.lower()]
        
        product = ProductInfo(
            sku=sku,
            name=name,
            brand="Stanley",
            price=price,
            description=description,
            specifications=specifications,
            images=images,
            datasheets=datasheets,
            manuals=manuals,
            categories=categories,
            supplier_url=product_url
        )
        
        return product


class SupplierScrapingManager:
    """
    Manages multiple supplier scrapers with parallel processing.
    
    Coordinates scraping across different suppliers while respecting
    rate limits and providing unified results.
    """
    
    def __init__(self, rate_limit_seconds: float = 1.0):
        """
        Initialize scraping manager.
        
        Args:
            rate_limit_seconds: Default rate limit for all scrapers
        """
        self.rate_limit_seconds = rate_limit_seconds
        self.scrapers = {
            'Bosch': BoschScraper(rate_limit_seconds),
            'Karcher': KarcherScraper(rate_limit_seconds),
            '3M': ThreeMScraper(rate_limit_seconds),
            'DeWalt': DeWaltScraper(rate_limit_seconds),
            'Milwaukee': MilwaukeeScraper(rate_limit_seconds),
            'Makita': MakitaScraper(rate_limit_seconds),
            'Stanley': StanleyScraper(rate_limit_seconds)
        }
        
    def add_scraper(self, scraper: BaseSupplierScraper):
        """Add a custom scraper to the manager."""
        self.scrapers[scraper.get_supplier_name()] = scraper
    
    def search_all_suppliers(self, query: str, max_results_per_supplier: int = 20) -> Dict[str, List[str]]:
        """
        Search for products across all suppliers.
        
        Args:
            query: Search query
            max_results_per_supplier: Maximum results per supplier
            
        Returns:
            Dictionary mapping supplier names to product URLs
        """
        all_results = {}
        
        for supplier_name, scraper in self.scrapers.items():
            try:
                logger.info(f"Searching {supplier_name} for '{query}'...")
                results = scraper.search_products(query, max_results_per_supplier)
                all_results[supplier_name] = results
                logger.info(f"Found {len(results)} products from {supplier_name}")
                
            except Exception as e:
                logger.error(f"Error searching {supplier_name}: {e}")
                all_results[supplier_name] = []
        
        return all_results
    
    def scrape_products_from_suppliers(self, supplier_products: Dict[str, List[str]]) -> Dict[str, ScrapingResult]:
        """
        Scrape products from multiple suppliers in parallel.
        
        Args:
            supplier_products: Dict mapping supplier names to product URL lists
            
        Returns:
            Dict mapping supplier names to ScrapingResult objects
        """
        results = {}
        
        # Use ThreadPoolExecutor for parallel supplier processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.scrapers)) as executor:
            # Submit scraping tasks for each supplier
            future_to_supplier = {}
            
            for supplier_name, product_urls in supplier_products.items():
                if product_urls and supplier_name in self.scrapers:
                    scraper = self.scrapers[supplier_name]
                    future = executor.submit(scraper.scrape_multiple_products, product_urls)
                    future_to_supplier[future] = supplier_name
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_supplier):
                supplier_name = future_to_supplier[future]
                try:
                    result = future.result()
                    results[supplier_name] = result
                    logger.info(f"Completed scraping {supplier_name}: {len(result.products)} products")
                    
                except Exception as e:
                    logger.error(f"Error scraping {supplier_name}: {e}")
                    results[supplier_name] = ScrapingResult(
                        success=False,
                        errors=[str(e)]
                    )
        
        return results
    
    def search_and_scrape(self, brands: List[str], max_results_per_brand: int = 10) -> Dict[str, Any]:
        """
        Complete workflow: search for brands across suppliers and scrape results.
        
        Args:
            brands: List of brand names to search for
            max_results_per_brand: Maximum results per brand per supplier
            
        Returns:
            Complete results dictionary with all scraped data
        """
        start_time = time.time()
        all_results = {
            'brands_searched': brands,
            'suppliers': {},
            'summary': {
                'total_products': 0,
                'total_errors': 0,
                'processing_time': 0.0,
                'suppliers_processed': 0
            }
        }
        
        for brand in brands:
            logger.info(f"Processing brand: {brand}")
            
            # Search across all suppliers
            search_results = self.search_all_suppliers(brand, max_results_per_brand)
            
            # Scrape found products
            scraping_results = self.scrape_products_from_suppliers(search_results)
            
            # Aggregate results
            for supplier_name, result in scraping_results.items():
                if supplier_name not in all_results['suppliers']:
                    all_results['suppliers'][supplier_name] = {
                        'products': [],
                        'errors': [],
                        'brands_processed': []
                    }
                
                all_results['suppliers'][supplier_name]['products'].extend(
                    [p.to_dict() for p in result.products]
                )
                all_results['suppliers'][supplier_name]['errors'].extend(result.errors)
                all_results['suppliers'][supplier_name]['brands_processed'].append(brand)
        
        # Calculate summary
        processing_time = time.time() - start_time
        total_products = sum(len(supplier['products']) for supplier in all_results['suppliers'].values())
        total_errors = sum(len(supplier['errors']) for supplier in all_results['suppliers'].values())
        
        all_results['summary'] = {
            'total_products': total_products,
            'total_errors': total_errors,
            'processing_time': processing_time,
            'suppliers_processed': len(all_results['suppliers'])
        }
        
        logger.info(f"Scraping completed: {total_products} products, {total_errors} errors, {processing_time:.2f}s")
        
        return all_results
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save scraping results to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"supplier_scraping_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {filename}")


def main():
    """Example usage of supplier scraping system."""
    manager = SupplierScrapingManager(rate_limit_seconds=1.0)
    
    # Test brands from common hardware categories
    test_brands = ["drill", "safety gloves", "cleaning", "measuring tape", "power tools"]
    
    print("Supplier Scraping System Demo")
    print("=" * 50)
    
    # Run complete search and scrape workflow
    results = manager.search_and_scrape(test_brands, max_results_per_brand=5)
    
    # Display summary
    summary = results['summary']
    print(f"\nScraping Summary:")
    print(f"  Total Products: {summary['total_products']}")
    print(f"  Total Errors: {summary['total_errors']}")
    print(f"  Processing Time: {summary['processing_time']:.2f}s")
    print(f"  Suppliers Processed: {summary['suppliers_processed']}")
    
    # Display results by supplier
    for supplier_name, supplier_data in results['suppliers'].items():
        print(f"\n{supplier_name}:")
        print(f"  Products: {len(supplier_data['products'])}")
        print(f"  Errors: {len(supplier_data['errors'])}")
        print(f"  Brands: {', '.join(supplier_data['brands_processed'])}")
    
    # Save results
    manager.save_results(results, "demo_supplier_scraping.json")


if __name__ == "__main__":
    main()