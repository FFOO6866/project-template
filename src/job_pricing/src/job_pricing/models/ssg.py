"""
SSG SkillsFuture Framework Models

Stores Singapore's national skills taxonomy and job role mappings.
Corresponds to: ssg_skills_framework, ssg_tsc, ssg_job_role_tsc_mapping, job_skills_extracted tables
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
    ForeignKey,
    Index,
    UniqueConstraint,
    text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class SSGSkillsFramework(Base, TimestampMixin):
    """
    SSG Skills Framework Model

    Stores Singapore's national skills taxonomy from SkillsFuture.
    38 sectors, multiple tracks per sector, and job roles with career levels.

    Attributes:
        id: Unique identifier (SERIAL)
        sector: Sector name (e.g., "Infocomm Technology")
        track: Track name (e.g., "Data Analytics")
        job_role_code: Unique job role code
        job_role_title: Job role title
        job_role_description: Job role description
        career_level: Career level (Entry, Mid, Senior, Lead)
        critical_work_function: Critical work function for this role
    """

    __tablename__ = "ssg_skills_framework"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # Hierarchy
    sector = Column(
        String(100),
        nullable=False,
        comment="Sector (e.g., 'Infocomm Technology')"
    )

    track = Column(
        String(200),
        nullable=False,
        comment="Track within sector (e.g., 'Data Analytics')"
    )

    # Job Role
    job_role_code = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique SSG job role code"
    )

    job_role_title = Column(
        String(255),
        nullable=False,
        comment="Job role title from SSG"
    )

    job_role_description = Column(
        Text,
        nullable=True,
        comment="Job role description"
    )

    # Career Level
    career_level = Column(
        String(50),
        nullable=True,
        comment="Career level (Entry, Mid, Senior, Lead)"
    )

    # Critical Work Functions
    critical_work_function = Column(
        Text,
        nullable=True,
        comment="Critical work function for this role"
    )

    # Relationships
    tsc_mappings = relationship(
        "SSGJobRoleTSCMapping",
        back_populates="job_role",
        cascade="all, delete-orphan"
    )

    # Constraints and Indexes
    __table_args__ = (
        Index("idx_ssg_sector", "sector"),
        Index("idx_ssg_track", "track"),
        Index("idx_ssg_job_role_code", "job_role_code"),
        Index("idx_ssg_career_level", "career_level"),
    )

    def __repr__(self) -> str:
        return f"<SSGSkillsFramework(id={self.id}, code='{self.job_role_code}', title='{self.job_role_title}')>"


class SSGTSC(Base, TimestampMixin):
    """
    SSG Technical Skills & Competencies (TSC) Model

    Stores technical skills mapped to job roles in the SSG framework.
    Skills have categories and proficiency levels.

    Attributes:
        id: Unique identifier (SERIAL)
        tsc_code: Unique TSC code
        tsc_title: Skill title
        tsc_description: Skill description
        skill_category: Category (e.g., "Data Management", "Programming")
        proficiency_level: Proficiency level (Basic, Intermediate, Advanced)
    """

    __tablename__ = "ssg_tsc"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # TSC Identification
    tsc_code = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique TSC code from SSG"
    )

    tsc_title = Column(
        String(255),
        nullable=False,
        comment="Skill title"
    )

    tsc_description = Column(
        Text,
        nullable=True,
        comment="Skill description"
    )

    skill_category = Column(
        String(100),
        nullable=True,
        comment="Skill category (e.g., 'Data Management')"
    )

    proficiency_level = Column(
        String(50),
        nullable=True,
        comment="Proficiency level (Basic, Intermediate, Advanced)"
    )

    # Relationships
    job_role_mappings = relationship(
        "SSGJobRoleTSCMapping",
        back_populates="tsc",
        cascade="all, delete-orphan"
    )

    skills_extracted = relationship(
        "JobSkillsExtracted",
        back_populates="matched_tsc"
    )

    # Constraints and Indexes
    __table_args__ = (
        Index("idx_ssg_tsc_code", "tsc_code"),
        Index("idx_ssg_tsc_category", "skill_category"),
        # Full-text search for skill matching
        Index(
            "idx_ssg_tsc_title_fts",
            text("to_tsvector('english', tsc_title)"),
            postgresql_using="gin"
        ),
        # Trigram index for fuzzy matching
        Index(
            "idx_ssg_tsc_title_trgm",
            "tsc_title",
            postgresql_using="gin",
            postgresql_ops={"tsc_title": "gin_trgm_ops"}
        ),
    )

    def __repr__(self) -> str:
        return f"<SSGTSC(id={self.id}, code='{self.tsc_code}', title='{self.tsc_title}')>"


class SSGJobRoleTSCMapping(Base):
    """
    SSG Job Role to TSC Mapping Model

    Many-to-many relationship between SSG job roles and technical skills.
    Indicates which skills are required for each job role.

    Attributes:
        id: Unique identifier (SERIAL)
        job_role_code: Foreign key to ssg_skills_framework
        tsc_code: Foreign key to ssg_tsc
        proficiency_level: Required proficiency level for this role
        is_core_skill: Whether this is a core skill for the role
    """

    __tablename__ = "ssg_job_role_tsc_mapping"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique mapping identifier"
    )

    # Foreign Keys
    job_role_code = Column(
        String(50),
        ForeignKey("ssg_skills_framework.job_role_code"),
        nullable=False,
        comment="Reference to SSG job role"
    )

    tsc_code = Column(
        String(50),
        ForeignKey("ssg_tsc.tsc_code"),
        nullable=False,
        comment="Reference to SSG TSC"
    )

    # Mapping Details
    proficiency_level = Column(
        String(50),
        nullable=True,
        comment="Required proficiency level for this role"
    )

    is_core_skill = Column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
        comment="Whether this is a core skill for the role"
    )

    # Relationships
    job_role = relationship(
        "SSGSkillsFramework",
        back_populates="tsc_mappings"
    )

    tsc = relationship(
        "SSGTSC",
        back_populates="job_role_mappings"
    )

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("job_role_code", "tsc_code", name="uq_ssg_job_role_tsc"),
        Index("idx_ssg_mapping_job_role", "job_role_code"),
        Index("idx_ssg_mapping_tsc", "tsc_code"),
    )

    def __repr__(self) -> str:
        return f"<SSGJobRoleTSCMapping(id={self.id}, role='{self.job_role_code}', tsc='{self.tsc_code}')>"


class JobSkillsExtracted(Base):
    """
    Job Skills Extracted Model

    Stores skills extracted from user job descriptions using AI/NLP.
    Maps extracted skills to SSG TSC codes when possible.

    Attributes:
        id: Unique identifier (SERIAL)
        request_id: Foreign key to job_pricing_requests
        skill_name: Extracted skill name
        skill_category: Skill category
        matched_tsc_code: Matched SSG TSC code (if found)
        match_confidence: Match confidence (0.00-1.00)
        match_method: How the match was made (exact, fuzzy, semantic, manual)
        proficiency_required: Required proficiency level
        is_core_skill: Whether this is a core skill for the job
    """

    __tablename__ = "job_skills_extracted"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # Foreign Key
    request_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("job_pricing_requests.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to job pricing request"
    )

    # Extracted Skill
    skill_name = Column(
        String(255),
        nullable=False,
        comment="Extracted skill name from job description"
    )

    skill_category = Column(
        String(100),
        nullable=True,
        comment="Skill category (e.g., 'Technical', 'Soft Skills')"
    )

    # SSG Mapping
    matched_tsc_code = Column(
        String(50),
        ForeignKey("ssg_tsc.tsc_code"),
        nullable=True,
        comment="Matched SSG TSC code (if found)"
    )

    match_confidence = Column(
        Numeric(5, 2),
        nullable=True,
        comment="Match confidence (0.00-1.00)"
    )

    match_method = Column(
        String(50),
        nullable=True,
        comment="Match method: exact, fuzzy, semantic, manual"
    )

    # Skill Importance
    proficiency_required = Column(
        String(50),
        nullable=True,
        comment="Required proficiency level (Basic, Intermediate, Advanced)"
    )

    is_core_skill = Column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
        comment="Whether this is a core skill for the job"
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Timestamp when skill was extracted"
    )

    # Relationships
    request = relationship(
        "JobPricingRequest",
        back_populates="extracted_skills"
    )

    matched_tsc = relationship(
        "SSGTSC",
        back_populates="skills_extracted"
    )

    # Constraints and Indexes
    __table_args__ = (
        Index("idx_skills_request", "request_id"),
        Index("idx_skills_tsc", "matched_tsc_code"),
    )

    def __repr__(self) -> str:
        return f"<JobSkillsExtracted(id={self.id}, skill='{self.skill_name}', tsc='{self.matched_tsc_code}')>"
