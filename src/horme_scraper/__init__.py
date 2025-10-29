"""
Horme Web Scraper Package

A respectful web scraping framework for horme.com.sg that:
- Implements rate limiting based on robots.txt
- Uses rotating user agents and headers
- Includes retry logic with exponential backoff
- Handles errors gracefully
- Logs all requests
- Stores data in JSON format
"""

__version__ = "1.0.0"
__author__ = "Integrum Development Team"

from .scraper import HormeScraper
from .models import ProductData, ScrapingConfig
from .utils import get_default_config, setup_logging

__all__ = ["HormeScraper", "ProductData", "ScrapingConfig", "get_default_config", "setup_logging"]