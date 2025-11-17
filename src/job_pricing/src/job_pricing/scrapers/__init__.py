"""
Web Scrapers for Job Pricing Engine

This package contains scrapers for external job boards:
- MyCareersFuture (Singapore government job portal)
- Glassdoor (salary insights and company ratings)

All scrapers inherit from BaseScraper and use Selenium for JavaScript-rendered sites.
"""

from .base_scraper import BaseScraper
from .mycareersfuture_scraper import MyCareersFutureScraper
from .glassdoor_scraper import GlassdoorScraper

__all__ = [
    "BaseScraper",
    "MyCareersFutureScraper",
    "GlassdoorScraper",
]
