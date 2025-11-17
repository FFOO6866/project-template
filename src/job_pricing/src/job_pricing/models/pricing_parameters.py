"""
Pricing Parameters Models

Database-driven pricing parameters that replace hardcoded constants.
These tables allow dynamic updates to salary calculation logic without code changes.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    Date,
    DateTime,
    Text,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import validates

from .base import Base


class SalaryBand(Base):
    """
    Salary bands by experience level.

    Replaces hardcoded BASE_SALARY_BY_EXPERIENCE dictionary.
    Allows quarterly updates based on market surveys.
    """
    __tablename__ = "salary_bands"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Experience level classification
    experience_level = Column(String(50), nullable=False, unique=True, index=True)
    min_years = Column(Integer, nullable=False)
    max_years = Column(Integer, nullable=True)

    # Salary range in SGD (annual)
    salary_min_sgd = Column(Numeric(12, 2), nullable=False)
    salary_max_sgd = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="SGD", nullable=False)

    # Effective date range
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Constraints
    __table_args__ = (
        CheckConstraint("salary_min_sgd > 0", name="ck_salary_band_min_positive"),
        CheckConstraint("salary_max_sgd > salary_min_sgd", name="ck_salary_band_max_greater"),
        CheckConstraint("min_years >= 0", name="ck_salary_band_years_positive"),
        CheckConstraint("max_years IS NULL OR max_years > min_years", name="ck_salary_band_years_range"),
    )

    @validates("experience_level")
    def validate_experience_level(self, key, value):
        """Validate experience level is one of expected values."""
        allowed = ["entry", "junior", "mid", "senior", "lead"]
        if value not in allowed:
            raise ValueError(f"experience_level must be one of: {', '.join(allowed)}")
        return value

    def __repr__(self):
        return (
            f"<SalaryBand(level='{self.experience_level}', "
            f"range={self.salary_min_sgd}-{self.salary_max_sgd} {self.currency})>"
        )


class IndustryAdjustment(Base):
    """
    Industry-specific salary adjustment factors.

    Replaces hardcoded INDUSTRY_FACTORS dictionary.
    Allows monthly updates based on market trends.
    """
    __tablename__ = "industry_adjustments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Industry information
    industry_name = Column(String(100), nullable=False, index=True)
    adjustment_factor = Column(Numeric(5, 4), nullable=False)  # 1.15 = +15%, 0.90 = -10%

    # Effective date range
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Data quality metadata
    data_source = Column(String(255), nullable=True)  # 'Market Survey 2024', 'Internal Analysis'
    sample_size = Column(Integer, nullable=True)
    confidence_level = Column(String(20), nullable=True)  # 'High', 'Medium', 'Low'

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Constraints
    __table_args__ = (
        CheckConstraint("adjustment_factor > 0", name="ck_industry_factor_positive"),
        CheckConstraint("adjustment_factor BETWEEN 0.5 AND 2.0", name="ck_industry_factor_reasonable"),
        UniqueConstraint("industry_name", "effective_from", name="uq_industry_effective_date"),
    )

    def __repr__(self):
        return (
            f"<IndustryAdjustment(industry='{self.industry_name}', "
            f"factor={self.adjustment_factor}, active={self.is_active})>"
        )


class CompanySizeFactor(Base):
    """
    Company size-based salary adjustment factors.

    Replaces hardcoded COMPANY_SIZE_FACTORS dictionary.
    Allows annual updates based on market data.
    """
    __tablename__ = "company_size_factors"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Company size classification
    size_category = Column(String(50), nullable=False, unique=True, index=True)
    employee_min = Column(Integer, nullable=False)
    employee_max = Column(Integer, nullable=True)
    adjustment_factor = Column(Numeric(5, 4), nullable=False)

    # Effective date range
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Data quality metadata
    data_source = Column(String(255), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Constraints
    __table_args__ = (
        CheckConstraint("adjustment_factor > 0", name="ck_size_factor_positive"),
        CheckConstraint("adjustment_factor BETWEEN 0.5 AND 2.0", name="ck_size_factor_reasonable"),
        CheckConstraint("employee_min > 0", name="ck_size_employee_min_positive"),
        CheckConstraint("employee_max IS NULL OR employee_max > employee_min", name="ck_size_employee_range"),
    )

    def __repr__(self):
        return (
            f"<CompanySizeFactor(category='{self.size_category}', "
            f"factor={self.adjustment_factor}, active={self.is_active})>"
        )


class SkillPremium(Base):
    """
    Market demand-based skill premiums.

    Replaces hardcoded high_value_skills set and premium calculations.
    Allows dynamic updates based on job market demand analysis.
    """
    __tablename__ = "skill_premiums"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Skill information
    skill_name = Column(String(255), nullable=False, index=True)
    skill_category = Column(String(100), nullable=True)  # 'Technical', 'Leadership', 'Domain'
    premium_percentage = Column(Numeric(5, 4), nullable=False)  # 0.02 = 2% premium
    demand_level = Column(String(20), nullable=True)  # 'Critical', 'High', 'Medium', 'Low'

    # Effective date range
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Data quality metadata
    data_source = Column(String(255), nullable=True)
    market_demand_score = Column(Numeric(5, 2), nullable=True)  # 0-100 score

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Constraints
    __table_args__ = (
        CheckConstraint("premium_percentage >= 0", name="ck_skill_premium_non_negative"),
        CheckConstraint("premium_percentage <= 0.50", name="ck_skill_premium_reasonable"),  # Max 50%
        CheckConstraint(
            "market_demand_score IS NULL OR (market_demand_score >= 0 AND market_demand_score <= 100)",
            name="ck_skill_demand_score_range"
        ),
        UniqueConstraint("skill_name", "effective_from", name="uq_skill_effective_date"),
    )

    @validates("demand_level")
    def validate_demand_level(self, key, value):
        """Validate demand level is one of expected values."""
        if value is not None:
            allowed = ["Critical", "High", "Medium", "Low"]
            if value not in allowed:
                raise ValueError(f"demand_level must be one of: {', '.join(allowed)}")
        return value

    def __repr__(self):
        return (
            f"<SkillPremium(skill='{self.skill_name}', "
            f"premium={self.premium_percentage}, demand={self.demand_level})>"
        )


class ParameterChangeHistory(Base):
    """
    Audit trail for pricing parameter changes.

    Tracks all modifications to pricing parameters for compliance and analysis.
    """
    __tablename__ = "parameter_change_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Change tracking
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(Integer, nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    # Change metadata
    changed_by = Column(String(255), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    change_reason = Column(Text, nullable=True)

    # Approval workflow (optional)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return (
            f"<ParameterChangeHistory(table='{self.table_name}', "
            f"record_id={self.record_id}, field='{self.field_name}', "
            f"changed_by='{self.changed_by}')>"
        )
