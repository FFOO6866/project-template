"""
Web Scraping Data Models

Stores job data scraped from MyCareersFuture and Glassdoor.
Corresponds to: scraped_job_listings, scraped_company_data, scraping_audit_log tables
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    CheckConstraint,
    Index,
    UniqueConstraint,
    text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from .base import Base


class ScrapedJobListing(Base):
    """
    Scraped Job Listing Model

    Stores job data scraped from MyCareersFuture (MCF) and Glassdoor.
    Includes job details, salary data, location, and company information.

    Attributes:
        id: Unique identifier (SERIAL)
        source: Data source (my_careers_future, glassdoor)
        job_id: Source-specific job ID
        job_url: URL to the job listing
        job_title: Job title
        company_name: Company name
        salary_min: Minimum salary
        salary_max: Maximum salary
        salary_currency: Currency code (default: SGD)
        salary_type: Salary type (actual, estimated)
        location: Job location
        employment_type: Employment type (Full-time, Contract, etc.)
        seniority_level: Seniority level
        job_description: Full job description
        requirements: Job requirements
        skills: Array of required skills
        benefits: Array of benefits
        company_rating: Company rating (Glassdoor)
        company_size: Company size
        industry: Industry
        has_salary_data: Flag indicating if salary data is present
        posted_date: When job was posted
        scraped_at: When job was scraped
        last_seen_at: Last time job was seen (for tracking active/inactive)
        is_active: Whether job listing is still active
    """

    __tablename__ = "scraped_job_listings"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # Source Identification
    source = Column(
        String(50),
        nullable=False,
        comment="Data source (my_careers_future, glassdoor)"
    )

    job_id = Column(
        String(255),
        nullable=False,
        comment="Source-specific job ID"
    )

    job_url = Column(
        Text,
        nullable=False,
        comment="URL to the job listing"
    )

    # Job Details
    job_title = Column(
        String(500),
        nullable=False,
        comment="Job title"
    )

    company_name = Column(
        String(500),
        nullable=False,
        comment="Company name"
    )

    # Salary Data
    salary_min = Column(
        Numeric(12, 2),
        nullable=True,
        comment="Minimum salary"
    )

    salary_max = Column(
        Numeric(12, 2),
        nullable=True,
        comment="Maximum salary"
    )

    salary_currency = Column(
        String(3),
        nullable=False,
        server_default=text("'SGD'"),
        comment="Currency code (ISO 4217)"
    )

    salary_type = Column(
        String(20),
        nullable=True,
        comment="Salary type (actual, estimated)"
    )

    # Location
    location = Column(
        String(255),
        nullable=True,
        comment="Job location"
    )

    # Job Characteristics
    employment_type = Column(
        String(50),
        nullable=True,
        comment="Employment type (Full-time, Contract, Part-time)"
    )

    seniority_level = Column(
        String(100),
        nullable=True,
        comment="Seniority level (Entry, Mid, Senior, etc.)"
    )

    job_description = Column(
        Text,
        nullable=True,
        comment="Full job description text"
    )

    requirements = Column(
        Text,
        nullable=True,
        comment="Job requirements"
    )

    skills = Column(
        ARRAY(Text),
        nullable=True,
        comment="Array of required skills"
    )

    benefits = Column(
        ARRAY(Text),
        nullable=True,
        comment="Array of benefits offered"
    )

    # Company Data (from Glassdoor)
    company_rating = Column(
        Numeric(3, 2),
        nullable=True,
        comment="Company rating (1.00-5.00)"
    )

    company_size = Column(
        String(50),
        nullable=True,
        comment="Company size (e.g., '50-200', '1000+')"
    )

    industry = Column(
        String(100),
        nullable=True,
        comment="Industry classification"
    )

    # Data Quality
    has_salary_data = Column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
        comment="Flag indicating if salary data is present"
    )

    # Temporal Tracking
    posted_date = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When job was posted"
    )

    scraped_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="When job was first scraped"
    )

    last_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Last time job was seen (for active tracking)"
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
        comment="Whether job listing is still active"
    )

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "source IN ('my_careers_future', 'glassdoor')",
            name="check_source"
        ),
        UniqueConstraint("source", "job_id", name="uq_scraped_job"),
        Index("idx_scraped_jobs_source", "source"),
        Index("idx_scraped_jobs_title", "job_title"),
        Index("idx_scraped_jobs_company", "company_name"),
        Index("idx_scraped_jobs_location", "location"),
        Index("idx_scraped_jobs_posted", "posted_date", postgresql_ops={"posted_date": "DESC"}),
        Index("idx_scraped_jobs_active", "is_active"),
        Index("idx_scraped_jobs_salary", "salary_min", "salary_max"),
        Index(
            "idx_scraped_jobs_salary_data",
            "has_salary_data",
            postgresql_where=text("has_salary_data = TRUE")
        ),
        # Full-text search on job description
        Index(
            "idx_scraped_jobs_description_fts",
            text("to_tsvector('english', job_description)"),
            postgresql_using="gin"
        ),
        # Trigram index for fuzzy title matching
        Index(
            "idx_scraped_jobs_title_trgm",
            "job_title",
            postgresql_using="gin",
            postgresql_ops={"job_title": "gin_trgm_ops"}
        ),
    )

    def __repr__(self) -> str:
        return f"<ScrapedJobListing(id={self.id}, source='{self.source}', title='{self.job_title}')>"


class ScrapedCompanyData(Base):
    """
    Scraped Company Data Model

    Aggregates company information from multiple job listings.
    Provides company-level insights for pricing analysis.

    Attributes:
        id: Unique identifier (SERIAL)
        company_name: Company name (unique)
        glassdoor_rating: Company rating from Glassdoor
        company_size: Company size range
        industry: Industry classification
        headquarters_location: HQ location
        total_jobs_posted: Total jobs posted (all time)
        active_jobs_count: Current active jobs count
        avg_salary_min: Average minimum salary across all jobs
        avg_salary_max: Average maximum salary across all jobs
        last_updated: Last update timestamp
    """

    __tablename__ = "scraped_company_data"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # Company Identification
    company_name = Column(
        String(500),
        unique=True,
        nullable=False,
        comment="Company name (unique)"
    )

    # Company Profile
    glassdoor_rating = Column(
        Numeric(3, 2),
        nullable=True,
        comment="Company rating from Glassdoor (1.00-5.00)"
    )

    company_size = Column(
        String(50),
        nullable=True,
        comment="Company size (e.g., '50-200', '1000+')"
    )

    industry = Column(
        String(100),
        nullable=True,
        comment="Industry classification"
    )

    headquarters_location = Column(
        String(255),
        nullable=True,
        comment="Headquarters location"
    )

    # Hiring Activity
    total_jobs_posted = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Total jobs posted (all time)"
    )

    active_jobs_count = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Current active jobs count"
    )

    # Compensation Insights
    avg_salary_min = Column(
        Numeric(12, 2),
        nullable=True,
        comment="Average minimum salary across all jobs"
    )

    avg_salary_max = Column(
        Numeric(12, 2),
        nullable=True,
        comment="Average maximum salary across all jobs"
    )

    # Temporal
    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Last update timestamp"
    )

    # Constraints and Indexes
    __table_args__ = (
        Index("idx_company_name", "company_name"),
        Index("idx_company_industry", "industry"),
        Index("idx_company_rating", "glassdoor_rating", postgresql_ops={"glassdoor_rating": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<ScrapedCompanyData(id={self.id}, company='{self.company_name}', rating={self.glassdoor_rating})>"


class ScrapingAuditLog(Base):
    """
    Scraping Audit Log Model

    Tracks web scraping batch jobs for monitoring and debugging.
    Records success/failure metrics for each scraping run.

    Attributes:
        id: Unique identifier (SERIAL)
        run_date: When the scraping run occurred
        run_type: Type of run (weekly, daily, manual)
        source: Data source (my_careers_future, glassdoor, or NULL for combined)
        mcf_count: Number of jobs scraped from MCF
        glassdoor_count: Number of jobs scraped from Glassdoor
        validated_count: Number of jobs that passed validation
        deduplicated_count: Number of duplicate jobs removed
        stored_count: Number of jobs successfully stored
        error_count: Number of errors encountered
        status: Run status (completed, failed, partial)
        error_message: Error message (if failed)
        execution_time_seconds: Total execution time in seconds
    """

    __tablename__ = "scraping_audit_log"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # Run Details
    run_date = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the scraping run occurred"
    )

    run_type = Column(
        String(20),
        nullable=False,
        server_default=text("'weekly'"),
        comment="Type of run (weekly, daily, manual)"
    )

    # Source Breakdown
    source = Column(
        String(50),
        nullable=True,
        comment="Data source (my_careers_future, glassdoor, or NULL for combined)"
    )

    mcf_count = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Number of jobs scraped from MyCareersFuture"
    )

    glassdoor_count = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Number of jobs scraped from Glassdoor"
    )

    # Processing Metrics
    validated_count = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Number of jobs that passed validation"
    )

    deduplicated_count = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Number of duplicate jobs removed"
    )

    stored_count = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Number of jobs successfully stored"
    )

    error_count = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Number of errors encountered"
    )

    # Execution
    status = Column(
        String(20),
        nullable=False,
        comment="Run status (completed, failed, partial)"
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="Error message (if failed)"
    )

    execution_time_seconds = Column(
        Integer,
        nullable=True,
        comment="Total execution time in seconds"
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Timestamp when log entry was created"
    )

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "run_type IN ('weekly', 'daily', 'manual')",
            name="check_run_type"
        ),
        CheckConstraint(
            "status IN ('completed', 'failed', 'partial')",
            name="check_status"
        ),
        Index("idx_audit_log_date", "run_date", postgresql_ops={"run_date": "DESC"}),
        Index("idx_audit_log_status", "status"),
        Index("idx_audit_log_source", "source"),
    )

    def __repr__(self) -> str:
        return f"<ScrapingAuditLog(id={self.id}, run_date='{self.run_date}', status='{self.status}')>"
