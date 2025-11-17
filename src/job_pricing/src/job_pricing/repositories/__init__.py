"""
Repository Pattern Package

Provides data access layer using the repository pattern.
Repositories encapsulate database operations and provide a clean API for data access.

Available Repositories:
- BaseRepository: Generic base repository with CRUD operations
- JobPricingRepository: Job pricing requests and results
- MercerRepository: Mercer job library and mappings
- SSGRepository: SSG Skills Framework and TSC mappings
- ScrapingRepository: Scraped job listings and company data
- HRISRepository: Internal employee data and salary bands
"""

from .base import BaseRepository
from .job_pricing_repository import JobPricingRepository
from .mercer_repository import MercerRepository
from .ssg_repository import SSGRepository
from .scraping_repository import ScrapingRepository
from .hris_repository import HRISRepository

__all__ = [
    "BaseRepository",
    "JobPricingRepository",
    "MercerRepository",
    "SSGRepository",
    "ScrapingRepository",
    "HRISRepository",
]
