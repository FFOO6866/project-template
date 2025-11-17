"""
Data Ingestion Error Model

Tracks errors that occur during data ingestion operations.
Used for debugging, monitoring, and data quality reporting.
"""

from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid
import enum

from .base import Base


class ErrorSource(str, enum.Enum):
    """Enumeration of data ingestion sources."""
    MERCER_JOB_LIBRARY = "mercer_job_library"
    MERCER_MARKET_DATA = "mercer_market_data"
    SSG_JOB_ROLES = "ssg_job_roles"
    SSG_TSC = "ssg_tsc"
    SSG_MAPPINGS = "ssg_mappings"
    SCRAPED_LISTINGS = "scraped_listings"
    INTERNAL_EMPLOYEES = "internal_employees"
    APPLICANTS = "applicants"
    OTHER = "other"


class ErrorType(str, enum.Enum):
    """Enumeration of error types."""
    VALIDATION_ERROR = "validation_error"
    DUPLICATE = "duplicate"
    FK_VIOLATION = "fk_violation"
    TYPE_ERROR = "type_error"
    INTEGRITY_ERROR = "integrity_error"
    TRANSFORMATION_ERROR = "transformation_error"
    UNKNOWN_ERROR = "unknown_error"


class DataIngestionError(Base):
    """
    Tracks errors during data ingestion.

    Used for:
    - Debugging data quality issues
    - Monitoring ingestion health
    - Generating error reports
    - Re-processing failed records

    Example:
        >>> error = DataIngestionError(
        ...     source=ErrorSource.MERCER_JOB_LIBRARY,
        ...     record_identifier="ICT.01.001.M40",
        ...     error_type=ErrorType.VALIDATION_ERROR,
        ...     error_message="Job title is required but missing",
        ...     record_data={"job_code": "ICT.01.001.M40", "job_title": None}
        ... )
        >>> session.add(error)
        >>> session.commit()
    """

    __tablename__ = "data_ingestion_errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source information
    source = Column(
        SQLEnum(ErrorSource),
        nullable=False,
        index=True,
        comment="Source of the data (e.g., 'mercer_job_library', 'ssg_tsc')"
    )

    # Record identification
    record_identifier = Column(
        String(200),
        nullable=True,
        index=True,
        comment="Unique identifier for the failed record (e.g., job_code, tsc_code)"
    )

    # Error details
    error_type = Column(
        SQLEnum(ErrorType),
        nullable=False,
        index=True,
        comment="Type of error (e.g., 'validation_error', 'duplicate')"
    )

    error_message = Column(
        Text,
        nullable=False,
        comment="Human-readable error message"
    )

    # Original record data (for debugging and retry)
    record_data = Column(
        JSONB,
        nullable=True,
        comment="Original record data that failed to load"
    )

    # Error context
    stack_trace = Column(
        Text,
        nullable=True,
        comment="Full stack trace if exception occurred"
    )

    batch_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Batch identifier if part of batch load"
    )

    # Resolution tracking
    resolved = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="True if error has been resolved/addressed"
    )

    resolution_notes = Column(
        Text,
        nullable=True,
        comment="Notes on how error was resolved"
    )

    resolved_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When error was marked as resolved"
    )

    resolved_by = Column(
        String(100),
        nullable=True,
        comment="User who resolved the error"
    )

    # Timestamps
    created_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When error was logged"
    )

    def __repr__(self):
        return (
            f"<DataIngestionError("
            f"source={self.source.value}, "
            f"record={self.record_identifier}, "
            f"type={self.error_type.value}, "
            f"resolved={self.resolved}"
            f")>"
        )

    def mark_resolved(self, resolved_by: str, notes: str):
        """
        Mark error as resolved.

        Args:
            resolved_by: Username or identifier of person resolving
            notes: Resolution notes
        """
        self.resolved = True
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = resolved_by
        self.resolution_notes = notes

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "source": self.source.value,
            "record_identifier": self.record_identifier,
            "error_type": self.error_type.value,
            "error_message": self.error_message,
            "record_data": self.record_data,
            "batch_id": self.batch_id,
            "resolved": self.resolved,
            "resolution_notes": self.resolution_notes,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Add indexes for common queries
"""
CREATE INDEX idx_ingestion_errors_source_resolved ON data_ingestion_errors(source, resolved);
CREATE INDEX idx_ingestion_errors_error_type ON data_ingestion_errors(error_type);
CREATE INDEX idx_ingestion_errors_created_at ON data_ingestion_errors(created_at DESC);
CREATE INDEX idx_ingestion_errors_batch_id ON data_ingestion_errors(batch_id) WHERE batch_id IS NOT NULL;
"""
