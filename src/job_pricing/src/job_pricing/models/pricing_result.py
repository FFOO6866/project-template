"""
Job Pricing Result Model

Stores algorithm output and salary recommendations.
Corresponds to: job_pricing_results table
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Integer,
    Numeric,
    CheckConstraint,
    ForeignKey,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from .base import Base


class JobPricingResult(Base):
    """
    Job Pricing Result Model

    Stores the algorithm's salary recommendations and analysis.
    One-to-one relationship with JobPricingRequest.

    Attributes:
        id: Unique UUID identifier
        request_id: Foreign key to job_pricing_requests
        currency: Currency code (default: SGD)
        period: Salary period (default: annual)
        recommended_min: Recommended minimum salary
        recommended_max: Recommended maximum salary
        target_salary: Target/mid-point salary
        p10-p90: Percentile distribution values
        market_position: Market position description
        confidence_score: Overall confidence (0-100)
        confidence_level: High, Medium, or Low
        confidence_factors: JSONB breakdown of confidence components
        summary_text: Human-readable summary
        key_factors: Array of key factors influencing result
        considerations: Array of considerations/caveats
        alternative_scenarios: JSONB array of alternative scenarios
        total_data_points: Total number of data points used
        data_sources_used: Number of data sources used
        data_consistency_score: Data consistency score (0-100)
    """

    __tablename__ = "job_pricing_results"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="Unique result identifier"
    )

    # Foreign Key
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_pricing_requests.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the job pricing request"
    )

    # Currency and Period
    currency = Column(
        String(3),
        nullable=False,
        server_default=text("'SGD'"),
        comment="Currency code (ISO 4217)"
    )

    period = Column(
        String(20),
        nullable=False,
        server_default=text("'annual'"),
        comment="Salary period (annual, monthly)"
    )

    # Salary Recommendations
    recommended_min = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Recommended minimum salary"
    )

    recommended_max = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Recommended maximum salary"
    )

    target_salary = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Target/mid-point salary"
    )

    # Percentile Distribution
    p10 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="10th percentile salary"
    )

    p25 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="25th percentile salary"
    )

    p50 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="50th percentile (median) salary"
    )

    p75 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="75th percentile salary"
    )

    p90 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="90th percentile salary"
    )

    market_position = Column(
        String(50),
        nullable=True,
        comment="Market position description (e.g., '55th percentile')"
    )

    # Confidence Metrics
    confidence_score = Column(
        Numeric(5, 2),
        nullable=False,
        comment="Overall confidence score (0.00-100.00)"
    )

    confidence_level = Column(
        String(20),
        nullable=False,
        comment="Confidence level: High, Medium, or Low"
    )

    confidence_factors = Column(
        JSONB,
        nullable=True,
        comment="Breakdown of confidence components"
    )

    # Explanation
    summary_text = Column(
        Text,
        nullable=True,
        comment="Human-readable summary of the result"
    )

    key_factors = Column(
        ARRAY(Text),
        nullable=True,
        comment="Key factors influencing the result"
    )

    considerations = Column(
        ARRAY(Text),
        nullable=True,
        comment="Important considerations and caveats"
    )

    # Alternative Scenarios
    alternative_scenarios = Column(
        JSONB,
        nullable=True,
        comment="Array of alternative scenario objects"
    )

    # Data Quality Metadata
    total_data_points = Column(
        Integer,
        nullable=True,
        comment="Total number of data points used in analysis"
    )

    data_sources_used = Column(
        Integer,
        nullable=True,
        comment="Number of data sources used"
    )

    data_consistency_score = Column(
        Numeric(5, 2),
        nullable=True,
        comment="Data consistency score (0.00-100.00)"
    )

    # Audit Fields
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Timestamp when result was created"
    )

    # Relationships
    request = relationship(
        "JobPricingRequest",
        back_populates="pricing_result"
    )

    data_source_contributions = relationship(
        "DataSourceContribution",
        back_populates="result",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "confidence_level IN ('High', 'Medium', 'Low')",
            name="check_confidence_level"
        ),
        UniqueConstraint("request_id", name="uq_result_request"),
        # Indexes
        Index("idx_pricing_results_request", "request_id"),
        Index("idx_pricing_results_confidence", "confidence_level"),
        Index("idx_pricing_results_created", "created_at", postgresql_ops={"created_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return (
            f"<JobPricingResult(id={self.id}, "
            f"target_salary={self.target_salary} {self.currency}, "
            f"confidence={self.confidence_level})>"
        )
