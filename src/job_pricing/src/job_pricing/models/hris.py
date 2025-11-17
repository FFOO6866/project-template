"""
HRIS Integration Models

Stores internal employee data, salary bands, and applicant data.
Corresponds to: internal_employees, grade_salary_bands, applicants tables
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Numeric,
    Boolean,
    Date,
    DateTime,
    CheckConstraint,
    Index,
    text,
)

from .base import Base, TimestampMixin


class InternalEmployee(Base):
    """
    Internal Employee Model

    Stores relevant employee data for internal benchmarking.
    This is a simplified view - actual HRIS integration would be read-only.

    Attributes:
        id: Unique identifier (SERIAL)
        employee_id: Employee ID from HRIS (unique)
        job_title: Current job title
        department: Department name
        job_family: Job family classification
        internal_grade: Current grade
        current_salary: Current annual salary
        currency: Currency code (default: SGD)
        employment_type: Employment type (Full-time, Contract, etc.)
        location: Work location
        employment_status: Employment status (Active, Inactive, etc.)
        years_of_experience: Total years of experience
        years_in_company: Years in current company
        years_in_grade: Years in current grade
        performance_rating: Performance rating
        last_salary_review_date: Last salary review date
        data_anonymized: Flag indicating if data is anonymized
        hire_date: Hire date
        last_updated: Last update timestamp
    """

    __tablename__ = "internal_employees"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # Employee Identification
    employee_id = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Employee ID from HRIS (unique)"
    )

    # Job Information
    job_title = Column(
        String(200),
        nullable=False,
        comment="Current job title"
    )

    department = Column(
        String(100),
        nullable=True,
        comment="Department name"
    )

    job_family = Column(
        String(100),
        nullable=True,
        comment="Job family classification"
    )

    # Grade & Compensation
    internal_grade = Column(
        String(10),
        nullable=True,
        comment="Current internal grade"
    )

    current_salary = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Current annual salary"
    )

    currency = Column(
        String(3),
        nullable=False,
        server_default=text("'SGD'"),
        comment="Currency code (ISO 4217)"
    )

    # Employment Details
    employment_type = Column(
        String(50),
        nullable=True,
        comment="Employment type (Full-time, Contract, Part-time)"
    )

    location = Column(
        String(100),
        nullable=True,
        comment="Work location"
    )

    employment_status = Column(
        String(20),
        nullable=False,
        server_default=text("'Active'"),
        comment="Employment status (Active, Inactive, etc.)"
    )

    # Career Progression
    years_of_experience = Column(
        Integer,
        nullable=True,
        comment="Total years of professional experience"
    )

    years_in_company = Column(
        Integer,
        nullable=True,
        comment="Years in current company"
    )

    years_in_grade = Column(
        Integer,
        nullable=True,
        comment="Years in current grade"
    )

    # Performance
    performance_rating = Column(
        String(20),
        nullable=True,
        comment="Performance rating (e.g., 'Exceeds Expectations')"
    )

    last_salary_review_date = Column(
        Date,
        nullable=True,
        comment="Last salary review date"
    )

    # Privacy Protection
    data_anonymized = Column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
        comment="Flag indicating if data is anonymized"
    )

    # Temporal
    hire_date = Column(
        Date,
        nullable=True,
        comment="Hire date"
    )

    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Last update timestamp"
    )

    # Constraints and Indexes
    __table_args__ = (
        Index("idx_employees_job_title", "job_title"),
        Index("idx_employees_grade", "internal_grade"),
        Index("idx_employees_department", "department"),
        Index("idx_employees_status", "employment_status"),
        Index("idx_employees_salary", "current_salary"),
    )

    def __repr__(self) -> str:
        return f"<InternalEmployee(id={self.id}, employee_id='{self.employee_id}', title='{self.job_title}')>"


class GradeSalaryBand(Base, TimestampMixin):
    """
    Grade Salary Band Model

    Defines company-specific salary bands per grade.
    Used to ensure pricing recommendations align with internal policies.

    Attributes:
        id: Unique identifier (SERIAL)
        internal_grade: Internal grade (unique)
        absolute_min: Absolute minimum salary for grade
        absolute_max: Absolute maximum salary for grade
        currency: Currency code (default: SGD)
        market_position: Target market percentile (e.g., 0.50 for P50)
        effective_date: When this band becomes effective
        expiry_date: When this band expires (optional)
    """

    __tablename__ = "grade_salary_bands"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # Grade
    internal_grade = Column(
        String(10),
        unique=True,
        nullable=False,
        comment="Internal grade (unique)"
    )

    # Salary Band
    absolute_min = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Absolute minimum salary for this grade"
    )

    absolute_max = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Absolute maximum salary for this grade"
    )

    currency = Column(
        String(3),
        nullable=False,
        server_default=text("'SGD'"),
        comment="Currency code (ISO 4217)"
    )

    # Market Positioning Strategy
    market_position = Column(
        Numeric(5, 2),
        nullable=True,
        comment="Target market percentile (e.g., 0.50 for P50, 0.75 for P75)"
    )

    # Metadata
    effective_date = Column(
        Date,
        nullable=False,
        comment="Effective date for this salary band"
    )

    expiry_date = Column(
        Date,
        nullable=True,
        comment="Expiry date for this salary band (optional)"
    )

    # Constraints and Indexes
    __table_args__ = (
        Index("idx_grade_bands_grade", "internal_grade"),
        Index("idx_grade_bands_effective", "effective_date", postgresql_ops={"effective_date": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<GradeSalaryBand(id={self.id}, grade='{self.internal_grade}', range={self.absolute_min}-{self.absolute_max})>"


class Applicant(Base):
    """
    Applicant Model

    Tracks applicant salary expectations for market intelligence.
    This is a simplified view - actual ATS integration would be read-only.
    Can also store applicant data synced from SharePoint folders.

    Attributes:
        id: Unique identifier (SERIAL)
        applicant_id: Applicant ID from ATS (unique)
        name: Applicant name (nullable for privacy)
        current_organisation: Current employer organization
        current_title: Current job title at current employer
        applied_job_title: Job title applied for
        job_family: Job family
        expected_salary: Salary expectation (monthly)
        current_salary: Current salary (monthly)
        currency: Currency code (default: SGD)
        years_of_experience: Years of experience
        education_level: Education level
        location: Location
        organisation_summary: Summary of current organization
        role_scope: Scope of current role
        application_status: Application status
        application_date: Application date
        application_year: Year of application (for grouping)
        data_anonymized: Flag indicating if data is anonymized
        sharepoint_file_id: SharePoint file ID if synced from SharePoint
    """

    __tablename__ = "applicants"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # Applicant Identification
    applicant_id = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Applicant ID from ATS (unique)"
    )

    name = Column(
        String(200),
        nullable=True,
        comment="Applicant name (nullable for privacy)"
    )

    # Current Employment Details
    current_organisation = Column(
        String(200),
        nullable=True,
        comment="Current employer organization"
    )

    current_title = Column(
        String(200),
        nullable=True,
        comment="Current job title at current employer"
    )

    organisation_summary = Column(
        Text,
        nullable=True,
        comment="Summary description of current organization"
    )

    role_scope = Column(
        Text,
        nullable=True,
        comment="Scope and responsibilities of current role"
    )

    # Applied Position
    applied_job_title = Column(
        String(200),
        nullable=False,
        comment="Job title applied for"
    )

    job_family = Column(
        String(100),
        nullable=True,
        comment="Job family classification"
    )

    # Salary Expectations (monthly)
    expected_salary = Column(
        Numeric(12, 2),
        nullable=True,
        comment="Salary expectation (monthly)"
    )

    current_salary = Column(
        Numeric(12, 2),
        nullable=True,
        comment="Current salary (monthly)"
    )

    currency = Column(
        String(3),
        nullable=False,
        server_default=text("'SGD'"),
        comment="Currency code (ISO 4217)"
    )

    # Applicant Profile
    years_of_experience = Column(
        Integer,
        nullable=True,
        comment="Years of professional experience"
    )

    education_level = Column(
        String(50),
        nullable=True,
        comment="Education level (e.g., 'Bachelor', 'Master')"
    )

    location = Column(
        String(100),
        nullable=True,
        comment="Applicant location"
    )

    # Application Status
    application_status = Column(
        String(50),
        nullable=True,
        comment="Application status"
    )

    application_date = Column(
        Date,
        nullable=False,
        comment="Application date"
    )

    application_year = Column(
        String(4),
        nullable=True,
        comment="Year of application (for grouping/filtering)"
    )

    # Privacy Protection
    data_anonymized = Column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
        comment="Flag indicating if data is anonymized"
    )

    # SharePoint Integration
    sharepoint_file_id = Column(
        String(255),
        nullable=True,
        comment="SharePoint file ID if synced from SharePoint folder"
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Timestamp when record was created"
    )

    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Last update timestamp"
    )

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "application_status IN ('Applied', 'Shortlisted', 'Interview Stage 1', 'Interview Stage 2', 'Offered', 'Offer Extended', 'Rejected', 'Withdrawn', 'Declined Offer', 'Hired')",
            name="check_application_status"
        ),
        Index("idx_applicants_job_title", "applied_job_title"),
        Index("idx_applicants_status", "application_status"),
        Index("idx_applicants_date", "application_date", postgresql_ops={"application_date": "DESC"}),
        Index("idx_applicants_year", "application_year"),
        Index("idx_applicants_organisation", "current_organisation"),
    )

    def __repr__(self) -> str:
        return f"<Applicant(id={self.id}, applicant_id='{self.applicant_id}', job='{self.applied_job_title}')>"
