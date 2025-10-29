#!/usr/bin/env python3
"""
Complete web scraping infrastructure for horme.com.sg

This is the main entry point that provides a unified interface to all
scraping functionality with comprehensive error handling, rate limiting,
and DataFlow model compatibility.

Features:
- Rate limiting (5-second delay by default, respects robots.txt)
- Product search by SKU functionality
- Comprehensive product data parsing (prices, descriptions, specs, images, availability)
- BeautifulSoup4 for HTML parsing
- Rotating user agents and headers
- Exponential backoff for errors
- JSON format compatible with DataFlow models
- Full robots.txt compliance
"""

import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Any

# Add the horme_scraper module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'horme_scraper'))

from horme_scraper.scraper import HormeScraper
from horme_scraper.models import ScrapingConfig, ProductData, ScrapingSession
from horme_scraper.utils import setup_logging, get_default_config

class HormeScrapingInfrastructure:
    """
    Main scraping infrastructure class that orchestrates all scraping operations.
    """
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        """Initialize the scraping infrastructure."""
        self.config = config or self.get_production_config()
        self.logger = setup_logging(self.config, "horme_scraper_main.log")
        self.scraper = HormeScraper(self.config)
        self.current_session: Optional[ScrapingSession] = None
        
        self.logger.info("Horme Scraping Infrastructure initialized")
        self.logger.info(f"Rate limit: {self.config.rate_limit_seconds} seconds")
        self.logger.info(f"Output directory: {self.config.output_directory}")
    
    @staticmethod
    def get_production_config() -> ScrapingConfig:
        """Get production-ready configuration."""
        return ScrapingConfig(
            # Rate limiting - respects robots.txt requirements
            rate_limit_seconds=5.0,  # 5-second delay as requested
            max_requests_per_hour=600,  # Conservative limit
            
            # Retry logic with exponential backoff
            max_retries=3,
            retry_backoff_factor=2.0,
            retry_base_delay=1.0,
            
            # Timeouts
            request_timeout=30,
            connection_timeout=10,
            
            # Headers and user agents (rotating)
            rotate_user_agents=True,
            custom_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            
            # Logging
            log_level="INFO",
            log_requests=True,
            log_responses=True,
            
            # Storage (DataFlow compatible JSON format)
            output_directory="scraped_data",
            save_json=True,
            save_csv=False,
            
            # Safety and compliance
            respect_robots_txt=True,
            check_robots_txt_interval=3600
        )
    
    def start_session(self, session_name: str = None) -> str:
        """Start a new scraping session."""
        if not session_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_name = f"horme_scraping_{timestamp}"
        
        session_id = self.scraper.start_session(session_name)
        self.current_session = self.scraper.current_session
        
        self.logger.info(f"Started scraping session: {session_id}")
        return session_id
    
    def end_session(self) -> Optional[Dict[str, Any]]:
        """End the current scraping session."""
        session_stats = self.scraper.end_session()
        self.current_session = None
        
        if session_stats:
            self.logger.info(f"Session completed: {session_stats['session_id']}")
            self.logger.info(f"Duration: {session_stats.get('duration_seconds', 0):.2f} seconds")
            self.logger.info(f"Success rate: {session_stats['success_rate']:.2%}")
            self.logger.info(f"Products scraped: {session_stats['products_scraped']}")
        
        return session_stats
    
    def search_by_sku(self, sku: str) -> Optional[str]:
        """
        Search for a product by SKU and return its URL.
        
        Args:
            sku: Product SKU to search for
            
        Returns:
            Product URL if found, None otherwise
        """
        self.logger.info(f"Searching for SKU: {sku}")
        return self.scraper.search_by_sku(sku)
    
    def search_products(self, query: str, max_results: int = 10) -> List[str]:
        """
        Search for products by query and return URLs.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of product URLs
        """
        self.logger.info(f"Searching for products: {query}")
        return self.scraper.search_products(query, max_results)
    
    def scrape_product(self, url: str) -> Optional[ProductData]:
        """
        Scrape a single product and return structured data.
        
        Args:
            url: Product page URL
            
        Returns:
            ProductData object if successful, None otherwise
        """
        return self.scraper.scrape_product(url)
    
    def scrape_products_by_skus(self, skus: List[str]) -> List[ProductData]:
        """
        Scrape multiple products by their SKUs.
        
        Args:
            skus: List of product SKUs
            
        Returns:
            List of ProductData objects
        """
        self.logger.info(f"Scraping {len(skus)} products by SKU")
        
        products = []
        found_urls = []
        
        # Find URLs for each SKU
        for i, sku in enumerate(skus, 1):
            self.logger.info(f"Searching for SKU {i}/{len(skus)}: {sku}")
            
            url = self.search_by_sku(sku)
            if url:
                found_urls.append(url)
                self.logger.info(f"Found URL for {sku}: {url}")
            else:
                self.logger.warning(f"Could not find URL for SKU: {sku}")
        
        # Scrape found products
        if found_urls:
            self.logger.info(f"Scraping {len(found_urls)} found products...")
            products = self.scraper.scrape_products(found_urls)
        
        self.logger.info(f"Successfully scraped {len(products)} products")
        return products
    
    def scrape_products_bulk(self, urls: List[str]) -> List[ProductData]:
        """
        Scrape multiple products from URLs.
        
        Args:
            urls: List of product URLs
            
        Returns:
            List of ProductData objects
        """
        self.logger.info(f"Bulk scraping {len(urls)} products")
        return self.scraper.scrape_products(urls)
    
    def save_products_dataflow_compatible(self, products: List[ProductData], 
                                        filename_base: str = None) -> Dict[str, bool]:
        """
        Save products in DataFlow-compatible JSON format.
        
        Args:
            products: List of ProductData objects
            filename_base: Base filename (without extension)
            
        Returns:
            Dictionary with save results
        """
        if not filename_base:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_base = f"horme_products_{timestamp}"
        
        # Convert to DataFlow-compatible format
        dataflow_products = []
        for product in products:
            product_dict = product.to_dict()
            
            # Ensure DataFlow compatibility
            dataflow_product = {
                "id": product.sku,
                "sku": product.sku,
                "name": product.name,
                "price": product.price,
                "description": product.description,
                "specifications": product.specifications,
                "images": product.images,
                "categories": product.categories,
                "availability": product.availability,
                "brand": product.brand,
                "url": product.url,
                "scraped_at": product.scraped_at.isoformat(),
                "metadata": {
                    "source": "horme.com.sg",
                    "scraper_version": "1.0.0",
                    "data_format": "dataflow_compatible"
                }
            }
            dataflow_products.append(dataflow_product)
        
        # Save using the scraper's save method
        results = self.scraper.save_products(products, filename_base)
        
        # Also save DataFlow-specific format
        try:
            os.makedirs(self.config.output_directory, exist_ok=True)
            dataflow_file = os.path.join(
                self.config.output_directory, 
                f"{filename_base}_dataflow.json"
            )
            
            with open(dataflow_file, 'w', encoding='utf-8') as f:
                json.dump(dataflow_products, f, indent=2, ensure_ascii=False)
            
            results['dataflow_json'] = True
            self.logger.info(f"Saved DataFlow-compatible JSON: {dataflow_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save DataFlow-compatible format: {e}")
            results['dataflow_json'] = False
        
        return results
    
    def load_skus_from_excel(self, excel_file: str, sku_column: str = "Product SKU", 
                           max_skus: int = None) -> List[str]:
        """
        Load SKUs from Excel file.
        
        Args:
            excel_file: Path to Excel file
            sku_column: Name of the SKU column
            max_skus: Maximum number of SKUs to load
            
        Returns:
            List of SKUs
        """
        try:
            df = pd.read_excel(excel_file)
            self.logger.info(f"Loaded Excel file: {excel_file}")
            self.logger.info(f"Total rows: {len(df)}")
            self.logger.info(f"Columns: {df.columns.tolist()}")
            
            if sku_column not in df.columns:
                raise ValueError(f"Column '{sku_column}' not found in Excel file")
            
            # Get SKUs and remove NaN values
            skus = df[sku_column].dropna().astype(str).tolist()
            
            if max_skus:
                skus = skus[:max_skus]
            
            self.logger.info(f"Loaded {len(skus)} SKUs from Excel file")
            return skus
            
        except Exception as e:
            self.logger.error(f"Failed to load SKUs from Excel: {e}")
            return []
    
    def run_sample_scraping_from_excel(self, excel_file: str, num_samples: int = 5) -> Dict[str, Any]:
        """
        Run sample scraping using SKUs from Excel file.
        
        Args:
            excel_file: Path to Excel file with product data
            num_samples: Number of products to scrape
            
        Returns:
            Dictionary with scraping results
        """
        self.logger.info(f"Starting sample scraping from Excel: {excel_file}")
        
        # Start session
        session_id = self.start_session("excel_sample_scraping")
        
        try:
            # Load SKUs from Excel
            skus = self.load_skus_from_excel(excel_file, max_skus=num_samples)
            
            if not skus:
                self.logger.error("No SKUs loaded from Excel file")
                return {"success": False, "error": "No SKUs loaded"}
            
            self.logger.info(f"Selected SKUs for scraping: {skus}")
            
            # Scrape products
            products = self.scrape_products_by_skus(skus)
            
            if products:
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"excel_sample_scraping_{timestamp}"
                
                save_results = self.save_products_dataflow_compatible(products, filename)
                
                # End session
                session_stats = self.end_session()
                
                return {
                    "success": True,
                    "products_scraped": len(products),
                    "skus_requested": skus,
                    "save_results": save_results,
                    "session_stats": session_stats,
                    "products": [p.to_dict() for p in products]
                }
            else:
                self.logger.warning("No products were successfully scraped")
                session_stats = self.end_session()
                
                return {
                    "success": False,
                    "error": "No products scraped",
                    "skus_requested": skus,
                    "session_stats": session_stats
                }
                
        except Exception as e:
            self.logger.error(f"Error during sample scraping: {e}")
            self.end_session()
            
            return {
                "success": False,
                "error": str(e),
                "skus_requested": skus if 'skus' in locals() else []
            }


def main():
    """Main function demonstrating the scraping infrastructure."""
    print("=" * 60)
    print("Horme.com.sg Web Scraping Infrastructure")
    print("=" * 60)
    
    # Initialize infrastructure
    infrastructure = HormeScrapingInfrastructure()
    
    # Get path to Excel file
    excel_file = os.path.join(
        os.path.dirname(__file__), 
        "..", "docs", "reference", "ProductData (Top 3 Cats).xlsx"
    )
    
    if not os.path.exists(excel_file):
        print(f"Excel file not found: {excel_file}")
        print("Using sample SKUs instead...")
        
        # Use sample SKUs
        sample_skus = ["02000401206", "0500000694", "0500000791", "0500000854", "050000101"]
        
        session_id = infrastructure.start_session("sample_sku_scraping")
        products = infrastructure.scrape_products_by_skus(sample_skus)
        
        if products:
            save_results = infrastructure.save_products_dataflow_compatible(products, "sample_sku_scraping")
            print(f"Successfully scraped {len(products)} products")
        else:
            print("No products were scraped")
        
        infrastructure.end_session()
        
    else:
        print(f"Running sample scraping from Excel file: {excel_file}")
        
        # Run sample scraping
        results = infrastructure.run_sample_scraping_from_excel(excel_file, num_samples=5)
        
        if results["success"]:
            print(f"✓ Successfully scraped {results['products_scraped']} products")
            print(f"✓ Session duration: {results['session_stats'].get('duration_seconds', 0):.2f} seconds")
            print(f"✓ Success rate: {results['session_stats']['success_rate']:.2%}")
            
            print("\nScraped Products:")
            for product in results["products"]:
                print(f"  - {product['name']} ({product['sku']})")
                print(f"    Price: {product['price']}")
                print(f"    Brand: {product['brand']}")
                print(f"    Categories: {', '.join(product['categories'])}")
                print()
        else:
            print(f"✗ Scraping failed: {results['error']}")
    
    print("\n" + "=" * 60)
    print("Scraping infrastructure demonstration completed")
    print("=" * 60)


if __name__ == "__main__":
    main()