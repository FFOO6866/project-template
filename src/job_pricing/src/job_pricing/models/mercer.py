"""
Mercer Integration Models

Stores Mercer Job Library, job mappings, and market data.
Corresponds to: mercer_job_library, mercer_job_mappings, mercer_market_data tables
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
    ForeignKey,
    Index,
    UniqueConstraint,
    text,
    text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class MercerJobLibrary(Base, TimestampMixin):
    """
    Mercer Job Library Model

    Stores Mercer's standardized job catalog (18,000+ jobs).
    Includes job hierarchy, IPE factors, and vector embeddings for semantic search.

    Attributes:
        id: Unique identifier (SERIAL)
        job_code: Mercer job code (e.g., "HRM.04.005.M50")
        job_title: Standardized job title
        family: Job family (e.g., "Human Resources Management")
        subfamily: Job subfamily (optional)
        career_level: Career level (M3, M4, M5, etc.)
        position_class: Position class (40-87)
        job_description: Full job description text
        typical_titles: Array of typical job titles
        specialization_notes: Additional specialization notes
        impact_min/max: IPE Impact factor point ranges
        communication_min/max: IPE Communication factor point ranges
        innovation_min/max: IPE Innovation factor point ranges
        knowledge_min/max: IPE Knowledge factor point ranges
        risk_min/max: IPE Accountability factor point ranges
        embedding: OpenAI vector embedding (1536 dimensions)
    """

    __tablename__ = "mercer_job_library"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique job library identifier"
    )

    # Job Identification
    job_code = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Mercer job code (e.g., 'HRM.04.005.M50')"
    )

    job_title = Column(
        String(255),
        nullable=False,
        comment="Standardized job title from Mercer"
    )

    # Hierarchy
    family = Column(
        String(100),
        nullable=False,
        comment="Job family classification"
    )

    subfamily = Column(
        String(100),
        nullable=True,
        comment="Job subfamily (optional)"
    )

    career_level = Column(
        String(10),
        nullable=True,
        comment="Career level (M3, M4, M5, P1, P2, etc.)"
    )

    position_class = Column(
        Integer,
        nullable=True,
        comment="Position class (40-87)"
    )

    # Job Content
    job_description = Column(
        Text,
        nullable=True,
        comment="Full job description text"
    )

    typical_titles = Column(
        ARRAY(Text),
        nullable=True,
        comment="Array of typical job titles for this role"
    )

    specialization_notes = Column(
        Text,
        nullable=True,
        comment="Additional specialization notes"
    )

    # IPE Factors (Point Ranges)
    impact_min = Column(
        Integer,
        nullable=True,
        comment="IPE Impact factor minimum points"
    )

    impact_max = Column(
        Integer,
        nullable=True,
        comment="IPE Impact factor maximum points"
    )

    communication_min = Column(
        Integer,
        nullable=True,
        comment="IPE Communication factor minimum points"
    )

    communication_max = Column(
        Integer,
        nullable=True,
        comment="IPE Communication factor maximum points"
    )

    innovation_min = Column(
        Integer,
        nullable=True,
        comment="IPE Innovation factor minimum points"
    )

    innovation_max = Column(
        Integer,
        nullable=True,
        comment="IPE Innovation factor maximum points"
    )

    knowledge_min = Column(
        Integer,
        nullable=True,
        comment="IPE Knowledge factor minimum points"
    )

    knowledge_max = Column(
        Integer,
        nullable=True,
        comment="IPE Knowledge factor maximum points"
    )

    risk_min = Column(
        Integer,
        nullable=True,
        comment="IPE Accountability/Risk factor minimum points"
    )

    risk_max = Column(
        Integer,
        nullable=True,
        comment="IPE Accountability/Risk factor maximum points"
    )

    # Vector Embedding for Semantic Search
    embedding = Column(
        Vector(1536),
        nullable=True,
        comment="OpenAI text-embedding-3-large vector (1536 dimensions)"
    )

    # Relationships
    market_data = relationship(
        "MercerMarketData",
        back_populates="job",
        cascade="all, delete-orphan"
    )

    job_mappings = relationship(
        "MercerJobMapping",
        back_populates="mercer_job"
    )

    # Constraints and Indexes
    __table_args__ = (
        Index("idx_mercer_job_code", "job_code"),
        Index("idx_mercer_family", "family"),
        Index("idx_mercer_subfamily", "subfamily"),
        Index("idx_mercer_level", "career_level"),
        Index("idx_mercer_position_class", "position_class"),
        # Vector similarity search index (IVFFlat)
        Index(
            "idx_mercer_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
        # Full-text search on job description
        Index(
            "idx_mercer_job_description_fts",
            text("to_tsvector('english', job_description)"),
            postgresql_using="gin"
        ),
    )

    def __repr__(self) -> str:
        return f"<MercerJobLibrary(id={self.id}, code='{self.job_code}', title='{self.job_title}')>"


class MercerJobMapping(Base):
    """
    Mercer Job Mapping Model

    Stores AI-powered mappings from user job requests to Mercer library.
    One-to-one relationship with JobPricingRequest.

    Attributes:
        id: Unique identifier (SERIAL)
        request_id: Foreign key to job_pricing_requests
        mercer_job_id: Foreign key to mercer_job_library
        confidence_score: Overall match confidence (0.00-1.00)
        match_method: How the match was made (semantic, rule_based, hybrid, manual)
        semantic_similarity: Semantic similarity score
        title_similarity: Title similarity score
        skills_overlap: Skills overlap score
        grade_alignment_score: Internal grade alignment score
        explanation: Human-readable explanation
        key_similarities: Array of key similarities
        key_differences: Array of key differences
        alternative_matches: JSONB of top 5 alternative matches
        requires_manual_review: Flag for manual review needed
        manually_reviewed: Flag if manually reviewed
        reviewed_by: User who reviewed
        reviewed_at: Timestamp of review
    """

    __tablename__ = "mercer_job_mappings"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique mapping identifier"
    )

    # Foreign Keys
    request_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("job_pricing_requests.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to job pricing request"
    )

    mercer_job_id = Column(
        Integer,
        ForeignKey("mercer_job_library.id"),
        nullable=False,
        comment="Reference to Mercer job library entry"
    )

    # Match Quality
    confidence_score = Column(
        Numeric(5, 2),
        nullable=False,
        comment="Overall match confidence (0.00-1.00)"
    )

    match_method = Column(
        String(50),
        nullable=True,
        comment="Match method: semantic, rule_based, hybrid, manual"
    )

    # Similarity Scores
    semantic_similarity = Column(
        Numeric(5, 4),
        nullable=True,
        comment="Semantic similarity score (0.0000-1.0000)"
    )

    title_similarity = Column(
        Numeric(5, 4),
        nullable=True,
        comment="Title similarity score (0.0000-1.0000)"
    )

    skills_overlap = Column(
        Numeric(5, 4),
        nullable=True,
        comment="Skills overlap score (0.0000-1.0000)"
    )

    grade_alignment_score = Column(
        Numeric(5, 4),
        nullable=True,
        comment="Internal grade alignment score (0.0000-1.0000)"
    )

    # Explanation
    explanation = Column(
        Text,
        nullable=True,
        comment="Human-readable explanation of the match"
    )

    key_similarities = Column(
        ARRAY(Text),
        nullable=True,
        comment="Key similarities between user job and Mercer job"
    )

    key_differences = Column(
        ARRAY(Text),
        nullable=True,
        comment="Key differences between user job and Mercer job"
    )

    # Alternative Matches (JSONB)
    # Structure: [{"job_code": "HRM.04.005.M50", "score": 0.85, "reason": "..."}]
    from sqlalchemy.dialects.postgresql import JSONB
    alternative_matches = Column(
        JSONB,
        nullable=True,
        comment="Top 5 alternative Mercer job matches"
    )

    # Manual Review
    requires_manual_review = Column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
        comment="Flag indicating manual review needed"
    )

    manually_reviewed = Column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
        comment="Flag indicating if manually reviewed"
    )

    reviewed_by = Column(
        String(100),
        nullable=True,
        comment="User who performed manual review"
    )

    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of manual review"
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Timestamp when mapping was created"
    )

    # Relationships
    request = relationship(
        "JobPricingRequest",
        back_populates="mercer_mapping"
    )

    mercer_job = relationship(
        "MercerJobLibrary",
        back_populates="job_mappings"
    )

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("request_id", name="uq_mapping_request"),
        Index("idx_mercer_mapping_request", "request_id"),
        Index("idx_mercer_mapping_job", "mercer_job_id"),
        Index("idx_mercer_mapping_confidence", "confidence_score", postgresql_ops={"confidence_score": "DESC"}),
        Index(
            "idx_mercer_mapping_review",
            "requires_manual_review",
            postgresql_where=text("requires_manual_review = TRUE")
        ),
    )

    def __repr__(self) -> str:
        return f"<MercerJobMapping(id={self.id}, confidence={self.confidence_score}, method='{self.match_method}')>"


class MercerMarketData(Base):
    """
    Mercer Market Data Model

    Stores Mercer compensation survey data for specific jobs and locations.

    Attributes:
        id: Unique identifier (SERIAL)
        job_code: Mercer job code
        country_code: Country code (ISO 3166-1 alpha-2)
        location: Specific location within country
        currency: Currency code (default: SGD)
        industry: Industry classification
        benchmark_cut: Type of benchmark (by_job, by_family_level, etc.)
        p10-p90: Percentile compensation data
        sample_size: Number of survey participants
        survey_date: Date of the survey
        survey_name: Name of the survey
        participant_count: Total participants in survey
        data_quality_flag: Quality flag (high, normal, low, outlier)
        data_retrieved_at: Timestamp when data was retrieved
    """

    __tablename__ = "mercer_market_data"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique market data identifier"
    )

    # Job Reference
    job_code = Column(
        String(50),
        ForeignKey("mercer_job_library.job_code"),
        nullable=False,
        comment="Mercer job code reference"
    )

    # Geography
    country_code = Column(
        String(2),
        nullable=False,
        comment="Country code (ISO 3166-1 alpha-2, e.g., 'SG')"
    )

    location = Column(
        String(100),
        nullable=True,
        comment="Specific location (e.g., 'Singapore CBD')"
    )

    # Survey Details
    currency = Column(
        String(3),
        nullable=False,
        server_default=text("'SGD'"),
        comment="Currency code (ISO 4217)"
    )

    industry = Column(
        String(100),
        nullable=True,
        comment="Industry classification"
    )

    benchmark_cut = Column(
        String(50),
        nullable=False,
        comment="Benchmark type (by_job, by_family_level, by_family_position_class)"
    )

    # Compensation Data (Annual)
    p10 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="10th percentile compensation"
    )

    p25 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="25th percentile compensation"
    )

    p50 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="50th percentile (median) compensation"
    )

    p75 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="75th percentile compensation"
    )

    p90 = Column(
        Numeric(12, 2),
        nullable=True,
        comment="90th percentile compensation"
    )

    sample_size = Column(
        Integer,
        nullable=True,
        comment="Number of data points in this benchmark"
    )

    # Survey Metadata
    survey_date = Column(
        Date,
        nullable=False,
        comment="Date of the survey"
    )

    survey_name = Column(
        String(255),
        nullable=True,
        comment="Name of the Mercer survey"
    )

    participant_count = Column(
        Integer,
        nullable=True,
        comment="Total number of survey participants"
    )

    # Data Quality
    data_quality_flag = Column(
        String(20),
        nullable=False,
        server_default=text("'normal'"),
        comment="Data quality flag"
    )

    data_retrieved_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Timestamp when data was retrieved"
    )

    # Relationships
    job = relationship(
        "MercerJobLibrary",
        back_populates="market_data"
    )

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "data_quality_flag IN ('high', 'normal', 'low', 'outlier')",
            name="check_data_quality_flag"
        ),
        UniqueConstraint(
            "job_code", "country_code", "benchmark_cut", "survey_date",
            name="uq_market_data"
        ),
        Index("idx_mercer_market_job", "job_code"),
        Index("idx_mercer_market_country", "country_code"),
        Index("idx_mercer_market_date", "survey_date", postgresql_ops={"survey_date": "DESC"}),
        Index("idx_mercer_market_benchmark", "benchmark_cut"),
    )

    def __repr__(self) -> str:
        return (
            f"<MercerMarketData(id={self.id}, job_code='{self.job_code}', "
            f"country='{self.country_code}', p50={self.p50} {self.currency})>"
        )
