"""
Job Pricing Request Model

Stores user input for job pricing requests.
Corresponds to: job_pricing_requests table
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Integer,
    CheckConstraint,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class JobPricingRequest(Base, TimestampMixin):
    """
    Job Pricing Request Model

    Stores all user input data for a job pricing request.
    One request generates one pricing result.

    Attributes:
        id: Unique UUID identifier
        job_title: Job title (max 255 chars)
        job_description: Full job description text
        years_of_experience_min: Minimum years of experience
        years_of_experience_max: Maximum years of experience
        industry: Industry classification
        company_size: Company size category
        location_id: Foreign key to locations table
        location_text: Original location text from user
        internal_grade: Internal company grade
        skills_required: Array of required skills
        benefits_required: Array of required benefits
        remote_work_policy: Remote work policy
        urgency: Request urgency level
        requested_by: User who made the request
        requestor_email: Email of requestor
        status: pending, processing, completed, failed
        processing_started_at: When processing began
        processing_completed_at: When processing finished
        error_message: Error message if processing failed
    """

    __tablename__ = "job_pricing_requests"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="Unique request identifier"
    )

    # Input Data
    job_title = Column(
        String(255),
        nullable=False,
        comment="Job title provided by user"
    )

    job_description = Column(
        Text,
        nullable=False,
        comment="Full job description text"
    )

    # Experience
    years_of_experience_min = Column(
        Integer,
        nullable=True,
        comment="Minimum years of experience required"
    )

    years_of_experience_max = Column(
        Integer,
        nullable=True,
        comment="Maximum years of experience"
    )

    # Company Context
    industry = Column(
        String(100),
        nullable=True,
        comment="Industry classification"
    )

    company_size = Column(
        String(50),
        nullable=True,
        comment="Company size category"
    )

    # Location
    location_id = Column(
        Integer,
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to locations table"
    )

    location_text = Column(
        String(255),
        nullable=True,
        comment="Original location text from user input"
    )

    # Grade and Skills
    internal_grade = Column(
        String(50),
        nullable=True,
        comment="Internal company grade"
    )

    skills_required = Column(
        ARRAY(Text),
        nullable=True,
        comment="Array of required skills"
    )

    # TPC-Specific Fields (for reference UI compatibility)
    portfolio = Column(
        String(255),
        nullable=True,
        comment="Portfolio/Entity (e.g., 'TPC Group Corporate Office')"
    )

    department = Column(
        String(255),
        nullable=True,
        comment="Department (e.g., 'People & Organisation', 'Finance')"
    )

    employment_type = Column(
        String(50),
        nullable=True,
        comment="Employment type (permanent, contract, fixed-term, secondment)"
    )

    job_family = Column(
        String(255),
        nullable=True,
        comment="Job family (e.g., 'Total Rewards', 'Finance')"
    )

    alternative_titles = Column(
        ARRAY(Text),
        nullable=True,
        comment="Alternative market titles for broader matching"
    )

    mercer_job_code = Column(
        String(100),
        nullable=True,
        comment="Mercer job code (e.g., 'HRM.04.005.M50')"
    )

    mercer_job_description = Column(
        Text,
        nullable=True,
        comment="Mercer job description/mapping details"
    )

    benefits_required = Column(
        ARRAY(Text),
        nullable=True,
        comment="Array of required benefits"
    )

    # Work Policy
    remote_work_policy = Column(
        String(50),
        nullable=True,
        comment="Remote work policy"
    )

    # Request Priority
    urgency = Column(
        String(20),
        nullable=False,
        server_default=text("'normal'"),
        comment="Request urgency: low, normal, high, critical"
    )

    # Request Metadata
    requested_by = Column(
        String(100),
        nullable=False,
        comment="User who made the request"
    )

    requestor_email = Column(
        String(255),
        nullable=False,
        comment="Email of requestor"
    )

    # Processing Status
    status = Column(
        String(50),
        nullable=False,
        server_default=text("'pending'"),
        comment="Request processing status: pending, processing, completed, failed"
    )

    # Processing Tracking
    processing_started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When processing began"
    )

    processing_completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When processing finished"
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if processing failed"
    )

    # Relationships
    pricing_result = relationship(
        "JobPricingResult",
        back_populates="request",
        uselist=False,
        cascade="all, delete-orphan"
    )

    mercer_mapping = relationship(
        "MercerJobMapping",
        back_populates="request",
        uselist=False,
        cascade="all, delete-orphan"
    )

    extracted_skills = relationship(
        "JobSkillsExtracted",
        back_populates="request",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="check_request_status"
        ),
        CheckConstraint(
            "urgency IN ('low', 'normal', 'high', 'critical')",
            name="check_urgency"
        ),
        # Indexes
        Index("idx_pricing_request_status", "status"),
        Index("idx_pricing_request_created", "created_at", postgresql_ops={"created_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<JobPricingRequest(id={self.id}, title='{self.job_title}', status='{self.status}')>"
