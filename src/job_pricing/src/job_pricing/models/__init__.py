"""
Database Models Package

This package contains all SQLAlchemy ORM models for the Job Pricing Engine.

Models are organized by functional area:
- base.py: Base model and mixins
- job_request.py: Core job pricing request models
- pricing_result.py: Pricing calculation results
- pricing_parameters.py: Database-driven pricing parameters (replaces hardcoded constants)
- mercer.py: Mercer IPE integration models
- ssg.py: SSG Skills Framework models
- scraping.py: Web scraping data models
- hris.py: Internal HRIS models
- supporting.py: Supporting tables (locations, currencies, audit)
"""

from .base import Base, TimestampMixin
from .job_request import JobPricingRequest
from .pricing_result import JobPricingResult
from .data_source_contribution import DataSourceContribution
from .pricing_parameters import (
    SalaryBand,
    IndustryAdjustment,
    CompanySizeFactor,
    SkillPremium,
    ParameterChangeHistory,
)
from .mercer import MercerJobLibrary, MercerJobMapping, MercerMarketData
from .ssg import SSGSkillsFramework, SSGTSC, SSGJobRoleTSCMapping, JobSkillsExtracted
from .scraping import ScrapedJobListing, ScrapedCompanyData, ScrapingAuditLog
from .hris import InternalEmployee, GradeSalaryBand, Applicant
from .supporting import Location, LocationIndex, CurrencyExchangeRate, AuditLog

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # Core Models
    "JobPricingRequest",
    "JobPricingResult",
    "DataSourceContribution",
    # Pricing Parameters
    "SalaryBand",
    "IndustryAdjustment",
    "CompanySizeFactor",
    "SkillPremium",
    "ParameterChangeHistory",
    # Mercer Integration
    "MercerJobLibrary",
    "MercerJobMapping",
    "MercerMarketData",
    # SSG SkillsFuture
    "SSGSkillsFramework",
    "SSGTSC",
    "SSGJobRoleTSCMapping",
    "JobSkillsExtracted",
    # Web Scraping
    "ScrapedJobListing",
    "ScrapedCompanyData",
    "ScrapingAuditLog",
    # HRIS
    "InternalEmployee",
    "GradeSalaryBand",
    "Applicant",
    # Supporting
    "Location",
    "LocationIndex",
    "CurrencyExchangeRate",
    "AuditLog",
]
