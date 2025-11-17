"""
Data Source Contribution Model

Tracks individual data source contributions to pricing results.
Corresponds to: data_source_contributions table
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Date,
    DateTime,
    CheckConstraint,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class DataSourceContribution(Base):
    """
    Data Source Contribution Model

    Tracks individual data source contributions to each pricing result.
    Shows how each data source (Mercer, MCF, Glassdoor, etc.) contributed
    to the final salary recommendation.

    Attributes:
        id: Unique identifier (SERIAL)
        result_id: Foreign key to job_pricing_results
        source_name: Data source name (mercer, my_careers_future, glassdoor, internal_hris, applicant_data)
        weight_applied: Weight applied to this source (0.0000-1.0000)
        p10-p90: Percentile values from this source
        sample_size: Number of data points from this source
        data_date: Date of the source data
        quality_score: Quality score for this source (0.00-1.00)
        recency_weight: Recency weight applied (0.00-1.00)
    """

    __tablename__ = "data_source_contributions"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique contribution identifier"
    )

    # Foreign Key
    result_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_pricing_results.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the pricing result"
    )

    # Source Information
    source_name = Column(
        String(50),
        nullable=False,
        comment="Data source name"
    )

    # Weight Applied
    weight_applied = Column(
        Numeric(5, 4),
        nullable=True,
        comment="Weight applied to this source (0.0000-1.0000)"
    )

    # Source Data - Percentiles
    p10 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="10th percentile from this source"
    )

    p25 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="25th percentile from this source"
    )

    p50 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="50th percentile (median) from this source"
    )

    p75 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="75th percentile from this source"
    )

    p90 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="90th percentile from this source"
    )

    # Metadata
    sample_size = Column(
        Integer,
        nullable=True,
        comment="Number of data points from this source"
    )

    data_date = Column(
        Date,
        nullable=True,
        comment="Date of the source data"
    )

    quality_score = Column(
        Numeric(5, 2),
        nullable=True,
        comment="Quality score for this source (0.00-1.00)"
    )

    recency_weight = Column(
        Numeric(5, 2),
        nullable=True,
        comment="Recency weight applied (0.00-1.00)"
    )

    # Audit Fields
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Timestamp when contribution was recorded"
    )

    # Relationships
    result = relationship(
        "JobPricingResult",
        back_populates="data_source_contributions"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "source_name IN ('mercer', 'my_careers_future', 'glassdoor', 'internal_hris', 'applicant_data')",
            name="check_source_name"
        ),
        # Indexes
        Index("idx_data_contrib_result", "result_id"),
        Index("idx_data_contrib_source", "source_name"),
    )

    def __repr__(self) -> str:
        return (
            f"<DataSourceContribution(id={self.id}, "
            f"source='{self.source_name}', "
            f"weight={self.weight_applied})>"
        )
