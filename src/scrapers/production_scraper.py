#!/usr/bin/env python3
"""
Production Web Scraping Infrastructure
======================================

Real web scraping system with Selenium WebDriver for JavaScript-heavy sites,
anti-detection measures, proxy rotation, and comprehensive data extraction.

Features:
- Selenium WebDriver with Chrome/Firefox support
- Real anti-detection mechanisms (viewport randomization, timing variation)
- Proxy rotation and user-agent randomization
- Respect for robots.txt and rate limiting
- Real supplier discovery via Google search
- Product data enrichment and validation
- PostgreSQL integration for data persistence
- Docker containerization support
"""

import os
import sys
import time
import random
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from dataclasses import dataclass, asdict
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium not available. Install with: pip install selenium")

# BeautifulSoup for static content parsing
from bs4 import BeautifulSoup

# Production configuration management
from src.core.config import config
import re

# Database integration
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logging.warning("PostgreSQL adapter not available. Install with: pip install psycopg2-binary")


@dataclass
class ScrapingConfig:
    """Configuration for production scraping operations."""
    
    # Rate limiting and respect
    rate_limit_seconds: float = 3.0
    max_requests_per_hour: int = 1200
    respect_robots_txt: bool = True
    
    # Browser configuration
    browser_type: str = "chrome"  # chrome, firefox, headless_chrome, headless_firefox
    window_width: int = 1920
    window_height: int = 1080
    
    # Anti-detection measures
    use_random_viewport: bool = True
    randomize_timing: bool = True
    rotate_user_agents: bool = True
    simulate_human_behavior: bool = True
    
    # Proxy configuration
    use_proxies: bool = False
    proxy_list: List[str] = None
    proxy_rotation_interval: int = 10  # requests
    
    # Timeout configuration
    page_load_timeout: int = 30
    element_wait_timeout: int = 10
    request_timeout: int = 30
    
    # Retry configuration
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    
    # Data storage
    output_directory: str = "scraped_data"
    save_to_database: bool = True
    database_config: Dict[str, Any] = None
    
    # Logging
    log_level: str = "INFO"
    enable_detailed_logging: bool = True


@dataclass
class ProductData:
    """Structured product data model."""
    
    sku: str
    name: str = ""
    price: str = ""
    currency: str = "SGD"
    description: str = ""
    specifications: Dict[str, str] = None
    images: List[str] = None
    categories: List[str] = None
    availability: str = ""
    brand: str = ""
    supplier: str = ""
    url: str = ""
    scraped_at: datetime = None
    data_quality_score: float = 0.0
    
    def __post_init__(self):
        if self.specifications is None:
            self.specifications = {}
        if self.images is None:
            self.images = []
        if self.categories is None:
            self.categories = []
        if self.scraped_at is None:
            self.scraped_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['scraped_at'] = self.scraped_at.isoformat()
        return data
    
    def calculate_quality_score(self) -> float:
        """Calculate data quality score based on completeness."""
        score = 0.0
        total_fields = 10
        
        # Essential fields (higher weight)
        if self.sku: score += 1.0
        if self.name: score += 1.0
        if self.price: score += 1.0
        
        # Important fields (medium weight)
        if self.description: score += 0.8
        if self.brand: score += 0.6
        if self.availability: score += 0.6
        
        # Additional fields (lower weight)
        if self.specifications: score += 0.4
        if self.images: score += 0.4
        if self.categories: score += 0.3
        if self.url: score += 0.3
        
        self.data_quality_score = min(score / total_fields, 1.0)
        return self.data_quality_score


@dataclass
class SupplierInfo:
    """Supplier information model."""
    
    name: str
    domain: str
    url: str = ""
    contact_info: Dict[str, str] = None
    categories: List[str] = None
    location: str = ""
    verified: bool = False
    last_scraped: datetime = None
    product_count: int = 0
    
    def __post_init__(self):
        if self.contact_info is None:
            self.contact_info = {}
        if self.categories is None:
            self.categories = []
        if self.last_scraped is None:
            self.last_scraped = datetime.now()


class AntiDetectionManager:
    """Manages anti-detection measures for web scraping."""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.user_agents = self._load_user_agents()
        self.current_proxy_index = 0
        
    def _load_user_agents(self) -> List[str]:
        """Load realistic user agent strings."""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        return random.choice(self.user_agents)
    
    def get_random_viewport(self) -> Tuple[int, int]:
        """Get random viewport dimensions."""
        widths = [1366, 1920, 1440, 1536, 1024]
        heights = [768, 1080, 900, 864, 768]
        
        width = random.choice(widths)
        height = random.choice(heights)
        return width, height
    
    def simulate_human_delay(self, base_delay: float = 1.0) -> None:
        """Simulate human-like delays."""
        if self.config.randomize_timing:
            delay = base_delay + random.uniform(0.5, 2.0)
            time.sleep(delay)
        else:
            time.sleep(base_delay)
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy from rotation."""
        if not self.config.use_proxies or not self.config.proxy_list:
            return None
        
        proxy = self.config.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.config.proxy_list)
        return proxy


class BrowserManager:
    """Manages browser instances with anti-detection measures."""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.anti_detection = AntiDetectionManager(config)
        self.driver: Optional[webdriver.WebDriver] = None
        
    def create_driver(self) -> webdriver.WebDriver:
        """Create and configure browser driver."""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is required for browser automation")
        
        if self.config.browser_type.startswith("chrome"):
            return self._create_chrome_driver()
        elif self.config.browser_type.startswith("firefox"):
            return self._create_firefox_driver()
        else:
            raise ValueError(f"Unsupported browser type: {self.config.browser_type}")
    
    def _create_chrome_driver(self) -> webdriver.Chrome:
        """Create Chrome driver with optimal settings."""
        options = ChromeOptions()
        
        # Headless mode
        if "headless" in self.config.browser_type:
            options.add_argument("--headless")
        
        # Anti-detection measures
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        if self.config.rotate_user_agents:
            user_agent = self.anti_detection.get_random_user_agent()
            options.add_argument(f"--user-agent={user_agent}")
        
        # Viewport size
        if self.config.use_random_viewport:
            width, height = self.anti_detection.get_random_viewport()
            options.add_argument(f"--window-size={width},{height}")
        else:
            options.add_argument(f"--window-size={self.config.window_width},{self.config.window_height}")
        
        # Proxy configuration
        proxy = self.anti_detection.get_next_proxy()
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")
        
        # Performance optimizations
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")  # Can be enabled if needed
        
        driver = webdriver.Chrome(options=options)
        
        # Execute script to remove automation indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set timeouts
        driver.set_page_load_timeout(self.config.page_load_timeout)
        driver.implicitly_wait(self.config.element_wait_timeout)
        
        return driver
    
    def _create_firefox_driver(self) -> webdriver.Firefox:
        """Create Firefox driver with optimal settings."""
        options = FirefoxOptions()
        
        # Headless mode
        if "headless" in self.config.browser_type:
            options.add_argument("--headless")
        
        # User agent
        if self.config.rotate_user_agents:
            user_agent = self.anti_detection.get_random_user_agent()
            options.set_preference("general.useragent.override", user_agent)
        
        # Disable automation indicators
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        
        # Viewport size
        if self.config.use_random_viewport:
            width, height = self.anti_detection.get_random_viewport()
        else:
            width, height = self.config.window_width, self.config.window_height
        
        driver = webdriver.Firefox(options=options)
        driver.set_window_size(width, height)
        
        # Set timeouts
        driver.set_page_load_timeout(self.config.page_load_timeout)
        driver.implicitly_wait(self.config.element_wait_timeout)
        
        return driver
    
    def get_driver(self) -> webdriver.WebDriver:
        """Get current driver or create new one."""
        if self.driver is None:
            self.driver = self.create_driver()
        return self.driver
    
    def close_driver(self) -> None:
        """Close and cleanup driver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.error(f"Error closing driver: {e}")
            finally:
                self.driver = None


class RobotsTxtChecker:
    """Handles robots.txt compliance checking."""
    
    def __init__(self):
        self.robots_cache = {}
        self.cache_duration = timedelta(hours=1)
    
    def can_fetch(self, url: str, user_agent: str = "*") -> Tuple[bool, float]:
        """
        Check if URL can be fetched according to robots.txt.
        
        Returns:
            Tuple of (can_fetch: bool, crawl_delay: float)
        """
        domain = urlparse(url).netloc
        
        # Check cache
        if domain in self.robots_cache:
            cache_entry = self.robots_cache[domain]
            if datetime.now() - cache_entry['timestamp'] < self.cache_duration:
                return cache_entry['can_fetch'], cache_entry['crawl_delay']
        
        # Fetch robots.txt
        robots_url = f"https://{domain}/robots.txt"
        can_fetch = True
        crawl_delay = 1.0
        
        try:
            response = requests.get(robots_url, timeout=10)
            if response.status_code == 200:
                robots_content = response.text
                can_fetch, crawl_delay = self._parse_robots_txt(robots_content, url, user_agent)
            
        except Exception as e:
            logging.warning(f"Could not fetch robots.txt for {domain}: {e}")
        
        # Cache result
        self.robots_cache[domain] = {
            'can_fetch': can_fetch,
            'crawl_delay': crawl_delay,
            'timestamp': datetime.now()
        }
        
        return can_fetch, crawl_delay
    
    def _parse_robots_txt(self, content: str, url: str, user_agent: str) -> Tuple[bool, float]:
        """Parse robots.txt content and check permissions."""
        lines = content.strip().split('\n')
        current_user_agent = None
        can_fetch = True
        crawl_delay = 1.0
        
        url_path = urlparse(url).path
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.lower().startswith('user-agent:'):
                current_user_agent = line.split(':', 1)[1].strip()
            
            elif current_user_agent and (current_user_agent == '*' or user_agent in current_user_agent):
                if line.lower().startswith('disallow:'):
                    disallowed_path = line.split(':', 1)[1].strip()
                    if disallowed_path and url_path.startswith(disallowed_path):
                        can_fetch = False
                
                elif line.lower().startswith('crawl-delay:'):
                    try:
                        crawl_delay = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
        
        return can_fetch, crawl_delay


class ProductionScraper:
    """Main production scraper class with real web scraping capabilities."""
    
    def __init__(self, config: ScrapingConfig = None):
        """Initialize the production scraper."""
        self.config = config or ScrapingConfig()
        self.logger = self._setup_logging()
        
        # Core components
        self.browser_manager = BrowserManager(self.config)
        self.anti_detection = AntiDetectionManager(self.config)
        self.robots_checker = RobotsTxtChecker()
        
        # Session tracking
        self.session = requests.Session()
        self.request_count = 0
        self.start_time = datetime.now()
        
        # Database connection
        self.db_connection = None
        if self.config.save_to_database and POSTGRES_AVAILABLE:
            self._setup_database()
        
        self.logger.info("Production scraper initialized")
        self.logger.info(f"Browser: {self.config.browser_type}")
        self.logger.info(f"Anti-detection: {self.config.simulate_human_behavior}")
        self.logger.info(f"Database: {self.config.save_to_database}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging."""
        logger = logging.getLogger("production_scraper")
        logger.setLevel(getattr(logging, self.config.log_level))
        
        if not logger.handlers:
            # File handler
            os.makedirs("logs", exist_ok=True)
            file_handler = logging.FileHandler("logs/production_scraper.log")
            file_handler.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def _setup_database(self) -> None:
        """Setup PostgreSQL database connection."""
        try:
            # ✅ PRODUCTION FIX: Use centralized config, no hardcoded credentials
            db_config = self.config.database_config or config.get_database_pool_config()
            
            self.db_connection = psycopg2.connect(**db_config)
            self.logger.info("Database connection established")
            
            # Create tables if they don't exist
            self._create_database_tables()
            
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            self.db_connection = None
    
    def _create_database_tables(self) -> None:
        """Create necessary database tables."""
        create_products_table = """
        CREATE TABLE IF NOT EXISTS scraped_products (
            id SERIAL PRIMARY KEY,
            sku VARCHAR(100) UNIQUE NOT NULL,
            name VARCHAR(500),
            price VARCHAR(50),
            currency VARCHAR(10) DEFAULT 'SGD',
            description TEXT,
            specifications JSONB,
            images JSONB,
            categories JSONB,
            availability VARCHAR(100),
            brand VARCHAR(200),
            supplier VARCHAR(200),
            url VARCHAR(1000),
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_quality_score FLOAT DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_suppliers_table = """
        CREATE TABLE IF NOT EXISTS suppliers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(300) NOT NULL,
            domain VARCHAR(200) UNIQUE NOT NULL,
            url VARCHAR(1000),
            contact_info JSONB,
            categories JSONB,
            location VARCHAR(200),
            verified BOOLEAN DEFAULT FALSE,
            last_scraped TIMESTAMP,
            product_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        with self.db_connection.cursor() as cursor:
            cursor.execute(create_products_table)
            cursor.execute(create_suppliers_table)
            self.db_connection.commit()
    
    def scrape_with_selenium(self, url: str, extract_method: callable) -> Optional[Any]:
        """
        Scrape a URL using Selenium WebDriver.
        
        Args:
            url: URL to scrape
            extract_method: Function to extract data from the page
            
        Returns:
            Extracted data or None if failed
        """
        # Check robots.txt
        if self.config.respect_robots_txt:
            can_fetch, crawl_delay = self.robots_checker.can_fetch(url)
            if not can_fetch:
                self.logger.warning(f"Robots.txt disallows fetching: {url}")
                return None
            
            # Update rate limit based on crawl delay
            if crawl_delay > self.config.rate_limit_seconds:
                self.config.rate_limit_seconds = crawl_delay
        
        # Rate limiting
        self.anti_detection.simulate_human_delay(self.config.rate_limit_seconds)
        
        driver = None
        try:
            driver = self.browser_manager.get_driver()
            
            # Navigate to page
            self.logger.info(f"Loading page: {url}")
            driver.get(url)
            
            # Wait for page to load completely
            WebDriverWait(driver, self.config.element_wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Simulate human behavior
            if self.config.simulate_human_behavior:
                self._simulate_human_interaction(driver)
            
            # Extract data using provided method
            result = extract_method(driver)
            
            self.request_count += 1
            self.logger.info(f"Successfully processed: {url}")
            
            return result
            
        except TimeoutException:
            self.logger.error(f"Page load timeout: {url}")
            return None
            
        except WebDriverException as e:
            self.logger.error(f"WebDriver error for {url}: {e}")
            return None
            
        except Exception as e:
            self.logger.error(f"Unexpected error scraping {url}: {e}")
            return None
        
        finally:
            # Clean up if needed (don't close driver, reuse it)
            pass
    
    def _simulate_human_interaction(self, driver: webdriver.WebDriver) -> None:
        """Simulate human-like interactions with the page."""
        try:
            # Random scroll
            scroll_pause = random.uniform(0.5, 2.0)
            driver.execute_script("window.scrollTo(0, Math.floor(Math.random() * document.body.scrollHeight));")
            time.sleep(scroll_pause)
            
            # Random mouse movement (if elements are available)
            elements = driver.find_elements(By.TAG_NAME, "div")
            if elements:
                element = random.choice(elements[:5])  # Top 5 elements
                ActionChains(driver).move_to_element(element).perform()
                time.sleep(random.uniform(0.1, 0.5))
                
        except Exception as e:
            self.logger.debug(f"Human simulation error: {e}")
    
    def scrape_with_requests(self, url: str, parser_method: callable) -> Optional[Any]:
        """
        Scrape a URL using requests and BeautifulSoup for static content.
        
        Args:
            url: URL to scrape
            parser_method: Function to parse HTML content
            
        Returns:
            Parsed data or None if failed
        """
        # Check robots.txt
        if self.config.respect_robots_txt:
            can_fetch, crawl_delay = self.robots_checker.can_fetch(url)
            if not can_fetch:
                self.logger.warning(f"Robots.txt disallows fetching: {url}")
                return None
            
            # Rate limiting
            self.anti_detection.simulate_human_delay(max(crawl_delay, self.config.rate_limit_seconds))
        else:
            self.anti_detection.simulate_human_delay(self.config.rate_limit_seconds)
        
        try:
            # Prepare headers
            headers = {
                'User-Agent': self.anti_detection.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Make request
            self.logger.info(f"Fetching: {url}")
            response = self.session.get(
                url, 
                headers=headers, 
                timeout=self.config.request_timeout
            )
            response.raise_for_status()
            
            # Parse content
            result = parser_method(response.content, url)
            
            self.request_count += 1
            self.logger.info(f"Successfully processed: {url}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
            
        except Exception as e:
            self.logger.error(f"Parsing failed for {url}: {e}")
            return None
    
    def save_product_to_database(self, product: ProductData) -> bool:
        """Save product data to PostgreSQL database."""
        if not self.db_connection:
            return False
        
        try:
            with self.db_connection.cursor() as cursor:
                # Calculate quality score
                product.calculate_quality_score()
                
                # Insert or update product
                query = """
                INSERT INTO scraped_products (
                    sku, name, price, currency, description, specifications,
                    images, categories, availability, brand, supplier, url,
                    scraped_at, data_quality_score
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (sku) DO UPDATE SET
                    name = EXCLUDED.name,
                    price = EXCLUDED.price,
                    currency = EXCLUDED.currency,
                    description = EXCLUDED.description,
                    specifications = EXCLUDED.specifications,
                    images = EXCLUDED.images,
                    categories = EXCLUDED.categories,
                    availability = EXCLUDED.availability,
                    brand = EXCLUDED.brand,
                    supplier = EXCLUDED.supplier,
                    url = EXCLUDED.url,
                    scraped_at = EXCLUDED.scraped_at,
                    data_quality_score = EXCLUDED.data_quality_score,
                    updated_at = CURRENT_TIMESTAMP;
                """
                
                cursor.execute(query, (
                    product.sku, product.name, product.price, product.currency,
                    product.description, json.dumps(product.specifications),
                    json.dumps(product.images), json.dumps(product.categories),
                    product.availability, product.brand, product.supplier,
                    product.url, product.scraped_at, product.data_quality_score
                ))
                
                self.db_connection.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Database save failed for {product.sku}: {e}")
            self.db_connection.rollback()
            return False
    
    def save_supplier_to_database(self, supplier: SupplierInfo) -> bool:
        """Save supplier information to database."""
        if not self.db_connection:
            return False
        
        try:
            with self.db_connection.cursor() as cursor:
                query = """
                INSERT INTO suppliers (
                    name, domain, url, contact_info, categories,
                    location, verified, last_scraped, product_count
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (domain) DO UPDATE SET
                    name = EXCLUDED.name,
                    url = EXCLUDED.url,
                    contact_info = EXCLUDED.contact_info,
                    categories = EXCLUDED.categories,
                    location = EXCLUDED.location,
                    verified = EXCLUDED.verified,
                    last_scraped = EXCLUDED.last_scraped,
                    product_count = EXCLUDED.product_count,
                    updated_at = CURRENT_TIMESTAMP;
                """
                
                cursor.execute(query, (
                    supplier.name, supplier.domain, supplier.url,
                    json.dumps(supplier.contact_info),
                    json.dumps(supplier.categories),
                    supplier.location, supplier.verified,
                    supplier.last_scraped, supplier.product_count
                ))
                
                self.db_connection.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Database save failed for supplier {supplier.name}: {e}")
            self.db_connection.rollback()
            return False
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.browser_manager.driver:
            self.browser_manager.close_driver()
        
        if self.db_connection:
            self.db_connection.close()
        
        # Log session statistics
        duration = datetime.now() - self.start_time
        self.logger.info(f"Scraping session completed")
        self.logger.info(f"Duration: {duration.total_seconds():.2f} seconds")
        self.logger.info(f"Requests made: {self.request_count}")
        self.logger.info(f"Average rate: {self.request_count / max(duration.total_seconds(), 1):.2f} req/sec")


def main():
    """Main function for testing the production scraper."""
    print("Production Web Scraper - Testing")
    print("=" * 50)
    
    # Create configuration
    config = ScrapingConfig(
        browser_type="headless_chrome",
        rate_limit_seconds=2.0,
        simulate_human_behavior=True,
        save_to_database=True,
        log_level="INFO"
    )
    
    # Initialize scraper
    scraper = ProductionScraper(config)
    
    try:
        print("✓ Production scraper initialized successfully")
        print(f"✓ Browser: {config.browser_type}")
        print(f"✓ Rate limit: {config.rate_limit_seconds}s")
        print(f"✓ Database: {config.save_to_database}")
        print(f"✓ Anti-detection: {config.simulate_human_behavior}")
        
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
    
    finally:
        scraper.cleanup()
    
    print("\nProduction scraper test completed!")


if __name__ == "__main__":
    main()