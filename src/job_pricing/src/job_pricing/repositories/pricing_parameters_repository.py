"""
Pricing Parameters Repository

Repository for accessing database-driven pricing parameters.
Replaces hardcoded constants with configurable database values.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..models.pricing_parameters import (
    SalaryBand,
    IndustryAdjustment,
    CompanySizeFactor,
    SkillPremium,
    ParameterChangeHistory,
)
from .base import BaseRepository


class SalaryBandRepository(BaseRepository[SalaryBand]):
    """Repository for salary bands (experience-based salary ranges)."""

    def __init__(self, session: Session):
        super().__init__(session, SalaryBand)

    def get_active_bands(self, as_of_date: Optional[date] = None) -> List[SalaryBand]:
        """
        Get all active salary bands as of a specific date.

        Args:
            as_of_date: Date to check active status (defaults to today)

        Returns:
            List of active SalaryBand records
        """
        if as_of_date is None:
            as_of_date = date.today()

        query = self.session.query(SalaryBand).filter(
            and_(
                SalaryBand.is_active == True,
                SalaryBand.effective_from <= as_of_date,
                or_(
                    SalaryBand.effective_to.is_(None),
                    SalaryBand.effective_to >= as_of_date
                )
            )
        ).order_by(SalaryBand.min_years)

        return query.all()

    def get_by_experience_level(
        self,
        experience_level: str,
        as_of_date: Optional[date] = None
    ) -> Optional[SalaryBand]:
        """
        Get salary band for a specific experience level.

        Args:
            experience_level: Experience level ('entry', 'junior', 'mid', 'senior', 'lead')
            as_of_date: Date to check active status (defaults to today)

        Returns:
            SalaryBand record or None if not found
        """
        if as_of_date is None:
            as_of_date = date.today()

        return self.session.query(SalaryBand).filter(
            and_(
                SalaryBand.experience_level == experience_level,
                SalaryBand.is_active == True,
                SalaryBand.effective_from <= as_of_date,
                or_(
                    SalaryBand.effective_to.is_(None),
                    SalaryBand.effective_to >= as_of_date
                )
            )
        ).first()

    def get_by_years_of_experience(
        self,
        years: int,
        as_of_date: Optional[date] = None
    ) -> Optional[SalaryBand]:
        """
        Get salary band for a specific number of years of experience.

        Args:
            years: Years of experience
            as_of_date: Date to check active status (defaults to today)

        Returns:
            SalaryBand record or None if not found
        """
        if as_of_date is None:
            as_of_date = date.today()

        return self.session.query(SalaryBand).filter(
            and_(
                SalaryBand.is_active == True,
                SalaryBand.min_years <= years,
                or_(
                    SalaryBand.max_years.is_(None),
                    SalaryBand.max_years >= years
                ),
                SalaryBand.effective_from <= as_of_date,
                or_(
                    SalaryBand.effective_to.is_(None),
                    SalaryBand.effective_to >= as_of_date
                )
            )
        ).first()


class IndustryAdjustmentRepository(BaseRepository[IndustryAdjustment]):
    """Repository for industry adjustment factors."""

    def __init__(self, session: Session):
        super().__init__(session, IndustryAdjustment)

    def get_active_adjustments(self, as_of_date: Optional[date] = None) -> List[IndustryAdjustment]:
        """
        Get all active industry adjustments.

        Args:
            as_of_date: Date to check active status (defaults to today)

        Returns:
            List of active IndustryAdjustment records
        """
        if as_of_date is None:
            as_of_date = date.today()

        query = self.session.query(IndustryAdjustment).filter(
            and_(
                IndustryAdjustment.is_active == True,
                IndustryAdjustment.effective_from <= as_of_date,
                or_(
                    IndustryAdjustment.effective_to.is_(None),
                    IndustryAdjustment.effective_to >= as_of_date
                )
            )
        ).order_by(IndustryAdjustment.industry_name)

        return query.all()

    def get_by_industry(
        self,
        industry_name: str,
        as_of_date: Optional[date] = None
    ) -> Optional[IndustryAdjustment]:
        """
        Get adjustment factor for a specific industry.

        Args:
            industry_name: Industry name
            as_of_date: Date to check active status (defaults to today)

        Returns:
            IndustryAdjustment record or None if not found
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Try exact match first
        result = self.session.query(IndustryAdjustment).filter(
            and_(
                IndustryAdjustment.industry_name == industry_name,
                IndustryAdjustment.is_active == True,
                IndustryAdjustment.effective_from <= as_of_date,
                or_(
                    IndustryAdjustment.effective_to.is_(None),
                    IndustryAdjustment.effective_to >= as_of_date
                )
            )
        ).first()

        # If not found, try to get 'default'
        if not result:
            result = self.session.query(IndustryAdjustment).filter(
                and_(
                    IndustryAdjustment.industry_name == 'default',
                    IndustryAdjustment.is_active == True,
                    IndustryAdjustment.effective_from <= as_of_date,
                    or_(
                        IndustryAdjustment.effective_to.is_(None),
                        IndustryAdjustment.effective_to >= as_of_date
                    )
                )
            ).first()

        return result

    def get_adjustment_factor(
        self,
        industry_name: Optional[str],
        as_of_date: Optional[date] = None
    ) -> Decimal:
        """
        Get adjustment factor for an industry (returns 1.0 if not found).

        Args:
            industry_name: Industry name (None returns default factor)
            as_of_date: Date to check active status (defaults to today)

        Returns:
            Adjustment factor as Decimal (1.0 if not found)
        """
        if not industry_name:
            industry_name = 'default'

        adjustment = self.get_by_industry(industry_name, as_of_date)
        return adjustment.adjustment_factor if adjustment else Decimal('1.0')


class CompanySizeFactorRepository(BaseRepository[CompanySizeFactor]):
    """Repository for company size adjustment factors."""

    def __init__(self, session: Session):
        super().__init__(session, CompanySizeFactor)

    def get_active_factors(self, as_of_date: Optional[date] = None) -> List[CompanySizeFactor]:
        """
        Get all active company size factors.

        Args:
            as_of_date: Date to check active status (defaults to today)

        Returns:
            List of active CompanySizeFactor records
        """
        if as_of_date is None:
            as_of_date = date.today()

        query = self.session.query(CompanySizeFactor).filter(
            and_(
                CompanySizeFactor.is_active == True,
                CompanySizeFactor.effective_from <= as_of_date,
                or_(
                    CompanySizeFactor.effective_to.is_(None),
                    CompanySizeFactor.effective_to >= as_of_date
                )
            )
        ).order_by(CompanySizeFactor.employee_min)

        return query.all()

    def get_by_size_category(
        self,
        size_category: str,
        as_of_date: Optional[date] = None
    ) -> Optional[CompanySizeFactor]:
        """
        Get adjustment factor for a specific size category.

        Args:
            size_category: Size category ('1-10', '11-50', etc.)
            as_of_date: Date to check active status (defaults to today)

        Returns:
            CompanySizeFactor record or None if not found
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Try exact match first
        result = self.session.query(CompanySizeFactor).filter(
            and_(
                CompanySizeFactor.size_category == size_category,
                CompanySizeFactor.is_active == True,
                CompanySizeFactor.effective_from <= as_of_date,
                or_(
                    CompanySizeFactor.effective_to.is_(None),
                    CompanySizeFactor.effective_to >= as_of_date
                )
            )
        ).first()

        # If not found, try to get 'default'
        if not result:
            result = self.session.query(CompanySizeFactor).filter(
                and_(
                    CompanySizeFactor.size_category == 'default',
                    CompanySizeFactor.is_active == True,
                    CompanySizeFactor.effective_from <= as_of_date,
                    or_(
                        CompanySizeFactor.effective_to.is_(None),
                        CompanySizeFactor.effective_to >= as_of_date
                    )
                )
            ).first()

        return result

    def get_adjustment_factor(
        self,
        size_category: Optional[str],
        as_of_date: Optional[date] = None
    ) -> Decimal:
        """
        Get adjustment factor for a company size (returns 1.0 if not found).

        Args:
            size_category: Size category (None returns default factor)
            as_of_date: Date to check active status (defaults to today)

        Returns:
            Adjustment factor as Decimal (1.0 if not found)
        """
        if not size_category:
            size_category = 'default'

        factor = self.get_by_size_category(size_category, as_of_date)
        return factor.adjustment_factor if factor else Decimal('1.0')


class SkillPremiumRepository(BaseRepository[SkillPremium]):
    """Repository for skill-based premium adjustments."""

    def __init__(self, session: Session):
        super().__init__(session, SkillPremium)

    def get_active_premiums(self, as_of_date: Optional[date] = None) -> List[SkillPremium]:
        """
        Get all active skill premiums.

        Args:
            as_of_date: Date to check active status (defaults to today)

        Returns:
            List of active SkillPremium records
        """
        if as_of_date is None:
            as_of_date = date.today()

        query = self.session.query(SkillPremium).filter(
            and_(
                SkillPremium.is_active == True,
                SkillPremium.effective_from <= as_of_date,
                or_(
                    SkillPremium.effective_to.is_(None),
                    SkillPremium.effective_to >= as_of_date
                )
            )
        ).order_by(SkillPremium.premium_percentage.desc())

        return query.all()

    def get_by_skill_name(
        self,
        skill_name: str,
        as_of_date: Optional[date] = None
    ) -> Optional[SkillPremium]:
        """
        Get premium for a specific skill.

        Args:
            skill_name: Skill name (case-insensitive)
            as_of_date: Date to check active status (defaults to today)

        Returns:
            SkillPremium record or None if not found
        """
        if as_of_date is None:
            as_of_date = date.today()

        return self.session.query(SkillPremium).filter(
            and_(
                SkillPremium.skill_name.ilike(skill_name),
                SkillPremium.is_active == True,
                SkillPremium.effective_from <= as_of_date,
                or_(
                    SkillPremium.effective_to.is_(None),
                    SkillPremium.effective_to >= as_of_date
                )
            )
        ).first()

    def get_premiums_for_skills(
        self,
        skill_names: List[str],
        as_of_date: Optional[date] = None
    ) -> Dict[str, Decimal]:
        """
        Get premiums for multiple skills.

        Args:
            skill_names: List of skill names
            as_of_date: Date to check active status (defaults to today)

        Returns:
            Dictionary mapping skill_name -> premium_percentage
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Normalize skill names to lowercase for matching
        skill_names_lower = [s.lower() for s in skill_names]

        premiums = self.session.query(SkillPremium).filter(
            and_(
                SkillPremium.skill_name.in_(skill_names_lower),
                SkillPremium.is_active == True,
                SkillPremium.effective_from <= as_of_date,
                or_(
                    SkillPremium.effective_to.is_(None),
                    SkillPremium.effective_to >= as_of_date
                )
            )
        ).all()

        return {p.skill_name: p.premium_percentage for p in premiums}

    def calculate_total_premium(
        self,
        skill_names: List[str],
        max_premium: Decimal = Decimal('0.50'),
        as_of_date: Optional[date] = None
    ) -> Decimal:
        """
        Calculate total skill premium (capped at max_premium).

        Args:
            skill_names: List of skill names
            max_premium: Maximum total premium (default 50%)
            as_of_date: Date to check active status (defaults to today)

        Returns:
            Total premium percentage (capped at max_premium)
        """
        premiums = self.get_premiums_for_skills(skill_names, as_of_date)
        total = sum(premiums.values())
        return min(total, max_premium)


class ParameterChangeHistoryRepository(BaseRepository[ParameterChangeHistory]):
    """Repository for parameter change audit trail."""

    def __init__(self, session: Session):
        super().__init__(session, ParameterChangeHistory)

    def log_change(
        self,
        table_name: str,
        record_id: int,
        field_name: str,
        old_value: Any,
        new_value: Any,
        changed_by: str,
        change_reason: Optional[str] = None
    ) -> ParameterChangeHistory:
        """
        Log a parameter change.

        Args:
            table_name: Name of the table being changed
            record_id: ID of the record being changed
            field_name: Name of the field being changed
            old_value: Previous value
            new_value: New value
            changed_by: User making the change
            change_reason: Optional reason for change

        Returns:
            Created ParameterChangeHistory record
        """
        history = ParameterChangeHistory(
            table_name=table_name,
            record_id=record_id,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            changed_by=changed_by,
            change_reason=change_reason
        )

        return self.create(history)

    def get_history_for_record(
        self,
        table_name: str,
        record_id: int
    ) -> List[ParameterChangeHistory]:
        """
        Get change history for a specific record.

        Args:
            table_name: Name of the table
            record_id: ID of the record

        Returns:
            List of ParameterChangeHistory records ordered by date (newest first)
        """
        return self.session.query(ParameterChangeHistory).filter(
            and_(
                ParameterChangeHistory.table_name == table_name,
                ParameterChangeHistory.record_id == record_id
            )
        ).order_by(ParameterChangeHistory.changed_at.desc()).all()

    def get_history_for_table(
        self,
        table_name: str,
        limit: int = 100
    ) -> List[ParameterChangeHistory]:
        """
        Get recent change history for a table.

        Args:
            table_name: Name of the table
            limit: Maximum number of records to return

        Returns:
            List of ParameterChangeHistory records ordered by date (newest first)
        """
        return self.session.query(ParameterChangeHistory).filter(
            ParameterChangeHistory.table_name == table_name
        ).order_by(ParameterChangeHistory.changed_at.desc()).limit(limit).all()

    def get_recent_changes(
        self,
        limit: int = 100
    ) -> List[ParameterChangeHistory]:
        """
        Get recent changes across all parameter tables.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of ParameterChangeHistory records ordered by date (newest first)
        """
        return self.session.query(ParameterChangeHistory).order_by(
            ParameterChangeHistory.changed_at.desc()
        ).limit(limit).all()
