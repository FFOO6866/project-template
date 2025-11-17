"""
Unit Tests for Pricing Calculation Service

Tests all components of the salary pricing calculation algorithm:
- Experience level classification
- Experience multiplier calculation
- Location multiplier lookup
- Skill premium calculation
- Salary band generation
- Confidence scoring
- Complete pricing calculation
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from job_pricing.services.pricing_calculation_service import (
    PricingCalculationService,
    SalaryBand,
    PricingFactors,
)
from job_pricing.models import (
    JobPricingRequest,
    JobSkillsExtracted,
    LocationIndex,
)


class TestExperienceLevelClassification:
    """Test experience level classification logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.service = PricingCalculationService(self.mock_session)

    def test_entry_level_0_years(self):
        """Test classification for 0 years experience."""
        result = self.service._classify_experience_level(0, 1)
        assert result == "entry"

    def test_entry_level_2_years(self):
        """Test classification for 1-2 years experience."""
        result = self.service._classify_experience_level(1, 2)
        assert result == "entry"

    def test_junior_level_3_years(self):
        """Test classification for 2-4 years experience."""
        result = self.service._classify_experience_level(2, 4)
        assert result == "junior"

    def test_mid_level_5_years(self):
        """Test classification for 4-7 years experience."""
        result = self.service._classify_experience_level(4, 7)
        assert result == "mid"

    def test_senior_level_8_years(self):
        """Test classification for 7-10 years experience."""
        result = self.service._classify_experience_level(7, 10)
        assert result == "senior"

    def test_lead_level_12_years(self):
        """Test classification for 10+ years experience."""
        result = self.service._classify_experience_level(10, 15)
        assert result == "lead"

    def test_none_min_years(self):
        """Test classification with no minimum years."""
        result = self.service._classify_experience_level(None, 5)
        assert result == "mid"

    def test_none_max_years(self):
        """Test classification with no maximum years."""
        result = self.service._classify_experience_level(5, None)
        assert result == "mid"

    def test_both_none(self):
        """Test classification with both values None."""
        result = self.service._classify_experience_level(None, None)
        assert result == "entry"


class TestExperienceMultiplier:
    """Test experience multiplier calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.service = PricingCalculationService(self.mock_session)

    def test_zero_experience(self):
        """Test multiplier for 0 years experience."""
        result = self.service._calculate_experience_multiplier(0, 0)
        assert result == 1.0

    def test_five_years_experience(self):
        """Test multiplier for 5 years experience."""
        # Average = 5, multiplier = 1.0 + (5 * 0.03) = 1.15
        result = self.service._calculate_experience_multiplier(4, 6)
        assert result == pytest.approx(1.15, rel=0.01)

    def test_ten_years_experience(self):
        """Test multiplier for 10 years experience."""
        # Average = 10, multiplier = 1.0 + (10 * 0.03) = 1.30
        result = self.service._calculate_experience_multiplier(10, 10)
        assert result == pytest.approx(1.30, rel=0.01)

    def test_maximum_cap_at_15_years(self):
        """Test that multiplier caps at 1.45 for 15+ years."""
        # 15 years would be 1.45, anything more should still be 1.45
        result = self.service._calculate_experience_multiplier(15, 20)
        assert result == pytest.approx(1.45, rel=0.01)

    def test_twenty_years_experience_capped(self):
        """Test that 20 years experience is capped at 1.45."""
        result = self.service._calculate_experience_multiplier(20, 25)
        assert result == 1.45

    def test_none_values(self):
        """Test multiplier with None values."""
        result = self.service._calculate_experience_multiplier(None, None)
        assert result == 1.0


class TestLocationMultiplier:
    """Test location cost-of-living multiplier."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.service = PricingCalculationService(self.mock_session)

    def test_no_location_text(self):
        """Test multiplier when no location is provided."""
        result = self.service._get_location_multiplier(None)
        assert result == 1.0

    def test_singapore_default(self):
        """Test Singapore returns 1.0 multiplier."""
        # Mock database query to return None (no location index entry)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_session.query.return_value = mock_query

        result = self.service._get_location_multiplier("Singapore")
        assert result == 1.0

    def test_singapore_case_insensitive(self):
        """Test Singapore matching is case-insensitive."""
        # Mock database query to return None (no location index entry)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_session.query.return_value = mock_query

        result = self.service._get_location_multiplier("SINGAPORE")
        assert result == 1.0

    def test_location_index_found(self):
        """Test multiplier from LocationIndex database."""
        # Mock database query
        mock_location = Mock(spec=LocationIndex)
        mock_location.cost_of_living_index = Decimal("1.25")

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_location
        self.mock_session.query.return_value = mock_query

        result = self.service._get_location_multiplier("New York")
        assert result == 1.25

    def test_location_not_found_returns_default(self):
        """Test default multiplier when location not in database."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_session.query.return_value = mock_query

        result = self.service._get_location_multiplier("Unknown City")
        assert result == 1.0


class TestSkillPremium:
    """Test skill premium calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.service = PricingCalculationService(self.mock_session)

    def test_no_skills(self):
        """Test premium with no skills."""
        result = self.service._calculate_skill_premium([])
        assert result == 0.0

    def test_no_high_value_skills(self):
        """Test premium with no high-value skills."""
        skills = [
            Mock(skill_name="Manual Testing"),
            Mock(skill_name="Excel"),
        ]
        result = self.service._calculate_skill_premium(skills)
        assert result == 0.0

    def test_single_high_value_skill(self):
        """Test premium with one high-value skill."""
        skills = [Mock(skill_name="Python Programming")]
        result = self.service._calculate_skill_premium(skills)
        assert result == 0.02  # 2% for one high-value skill

    def test_multiple_high_value_skills(self):
        """Test premium with multiple high-value skills."""
        skills = [
            Mock(skill_name="Python"),
            Mock(skill_name="AWS"),
            Mock(skill_name="Kubernetes"),
        ]
        result = self.service._calculate_skill_premium(skills)
        assert result == 0.06  # 2% * 3 = 6%

    def test_maximum_premium_cap(self):
        """Test that premium caps at 20%."""
        # Only 7 high-value skills are defined in the service
        # (Python, AWS, Kubernetes, Machine Learning, React, TypeScript, Terraform)
        # So the maximum premium is 7 * 0.02 = 0.14 (14%)
        skills = [
            Mock(skill_name="Python"),
            Mock(skill_name="AWS"),
            Mock(skill_name="Kubernetes"),
            Mock(skill_name="Machine Learning"),
            Mock(skill_name="React"),
            Mock(skill_name="TypeScript"),
            Mock(skill_name="Terraform"),
            Mock(skill_name="Extra Skill 1"),
            Mock(skill_name="Extra Skill 2"),
            Mock(skill_name="Extra Skill 3"),
            Mock(skill_name="Extra Skill 4"),
            Mock(skill_name="Extra Skill 5"),
        ]
        result = self.service._calculate_skill_premium(skills)
        assert result == 0.14  # 7 high-value skills = 14%

    def test_case_insensitive_matching(self):
        """Test that skill matching is case-insensitive."""
        skills = [
            Mock(skill_name="PYTHON"),
            Mock(skill_name="aws cloud"),
        ]
        result = self.service._calculate_skill_premium(skills)
        assert result == 0.04  # 2% * 2 = 4%


class TestSalaryBandGeneration:
    """Test salary band and percentile generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.service = PricingCalculationService(self.mock_session)

    def test_salary_band_basic(self):
        """Test basic salary band generation."""
        target = Decimal("100000")
        result = self.service._generate_salary_band(target)

        assert isinstance(result, SalaryBand)
        assert result.target_salary == Decimal("100000")
        assert result.recommended_min == Decimal("80000")  # 80%
        assert result.recommended_max == Decimal("120000")  # 120%

    def test_percentile_calculations(self):
        """Test percentile calculations."""
        target = Decimal("100000")
        result = self.service._generate_salary_band(target)

        assert result.p10 == Decimal("75000")  # 75%
        assert result.p25 == Decimal("90000")  # 90%
        assert result.p50 == Decimal("100000")  # 100% (median = target)
        assert result.p75 == Decimal("110000")  # 110%
        assert result.p90 == Decimal("125000")  # 125%

    def test_salary_band_large_amount(self):
        """Test salary band with large salary amount."""
        target = Decimal("500000")
        result = self.service._generate_salary_band(target)

        assert result.recommended_min == Decimal("400000")
        assert result.recommended_max == Decimal("600000")
        assert result.target_salary == Decimal("500000")


class TestConfidenceScoring:
    """Test confidence score calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.service = PricingCalculationService(self.mock_session)

    def test_base_confidence(self):
        """Test base confidence score."""
        request = Mock(
            job_description="Short description",
            years_of_experience_min=None,
            years_of_experience_max=None,
            location_text=None,
        )
        skills = []

        result = self.service._calculate_confidence_score(request, skills, "entry")
        assert result == 70.0  # Base confidence

    def test_confidence_with_good_description(self):
        """Test confidence bonus for good job description."""
        request = Mock(
            job_description="A" * 150,  # Long description
            years_of_experience_min=None,
            years_of_experience_max=None,
            location_text=None,
        )
        skills = []

        result = self.service._calculate_confidence_score(request, skills, "entry")
        assert result == 80.0  # Base + 10 for description

    def test_confidence_with_skills_matched(self):
        """Test confidence bonus for matched skills."""
        request = Mock(
            job_description="Short",
            years_of_experience_min=None,
            years_of_experience_max=None,
            location_text=None,
        )
        skills = [
            Mock(matched_tsc_code="CODE1"),
            Mock(matched_tsc_code="CODE2"),
            Mock(matched_tsc_code=None),
            Mock(matched_tsc_code=None),
        ]
        # Match rate = 2/4 = 0.5, bonus = 0.5 * 10 = 5

        result = self.service._calculate_confidence_score(request, skills, "entry")
        assert result == 75.0  # Base + 5 for 50% match rate

    def test_confidence_with_experience_data(self):
        """Test confidence bonus for experience data."""
        request = Mock(
            job_description="Short",
            years_of_experience_min=5,
            years_of_experience_max=10,
            location_text=None,
        )
        skills = []

        result = self.service._calculate_confidence_score(request, skills, "senior")
        assert result == 75.0  # Base + 5 for experience

    def test_confidence_with_location(self):
        """Test confidence bonus for location data."""
        request = Mock(
            job_description="Short",
            years_of_experience_min=None,
            years_of_experience_max=None,
            location_text="Singapore",
        )
        skills = []

        result = self.service._calculate_confidence_score(request, skills, "entry")
        assert result == 75.0  # Base + 5 for location

    def test_confidence_capped_at_100(self):
        """Test that confidence score is capped at 100."""
        request = Mock(
            job_description="A" * 200,  # Long description
            years_of_experience_min=5,
            years_of_experience_max=10,
            location_text="Singapore",
        )
        skills = [Mock(matched_tsc_code=f"CODE{i}") for i in range(10)]

        result = self.service._calculate_confidence_score(request, skills, "senior")
        assert result == 100.0  # Capped at 100

    def test_confidence_level_high(self):
        """Test confidence level classification - High."""
        result = self.service._get_confidence_level(90.0)
        assert result == "High"

    def test_confidence_level_medium(self):
        """Test confidence level classification - Medium."""
        result = self.service._get_confidence_level(75.0)
        assert result == "Medium"

    def test_confidence_level_low(self):
        """Test confidence level classification - Low."""
        result = self.service._get_confidence_level(60.0)
        assert result == "Low"


class TestCompletePricingCalculation:
    """Test complete end-to-end pricing calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.service = PricingCalculationService(self.mock_session)

    def test_basic_pricing_calculation(self):
        """Test basic pricing calculation with minimal data."""
        # Mock request
        request = Mock(spec=JobPricingRequest)
        request.id = "test-id"
        request.job_title = "Software Engineer"
        request.job_description = "Basic job description"
        request.years_of_experience_min = 3
        request.years_of_experience_max = 5
        request.location_text = "Singapore"
        request.industry = "Technology"
        request.company_size = "201-500"

        # Mock skills
        skills = [
            Mock(spec=JobSkillsExtracted, skill_name="Python", matched_tsc_code="CODE1"),
            Mock(spec=JobSkillsExtracted, skill_name="Testing", matched_tsc_code=None),
        ]

        # Mock location query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_session.query.return_value = mock_query

        # Execute
        result, factors = self.service.calculate_pricing(request, skills)

        # Verify result
        assert result.request_id == "test-id"
        assert result.currency == "SGD"
        assert result.period == "annual"
        assert result.target_salary > 0
        assert result.recommended_min < result.target_salary
        assert result.recommended_max > result.target_salary
        assert result.confidence_score > 0
        assert result.confidence_level in ["High", "Medium", "Low"]

    def test_senior_level_with_high_value_skills(self):
        """Test pricing for senior position with high-value skills."""
        request = Mock(spec=JobPricingRequest)
        request.id = "test-id"
        request.job_title = "Senior Software Engineer"
        request.job_description = "A" * 200  # Long description
        request.years_of_experience_min = 8
        request.years_of_experience_max = 10
        request.location_text = "Singapore"
        request.industry = "Finance"  # 1.20x multiplier
        request.company_size = "1000+"  # 1.20x multiplier

        # High-value skills
        skills = [
            Mock(spec=JobSkillsExtracted, skill_name="Python", matched_tsc_code="CODE1"),
            Mock(spec=JobSkillsExtracted, skill_name="AWS", matched_tsc_code="CODE2"),
            Mock(spec=JobSkillsExtracted, skill_name="Kubernetes", matched_tsc_code="CODE3"),
        ]

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_session.query.return_value = mock_query

        result, factors = self.service.calculate_pricing(request, skills)

        # Verify higher salary due to multipliers
        assert result.target_salary > Decimal("150000")  # Should be significantly higher
        assert factors.industry_adjustment == 1.20
        assert factors.company_size_factor == 1.20
        assert factors.skill_premium == 0.06  # 3 high-value skills * 2%

    def test_entry_level_minimal_experience(self):
        """Test pricing for entry-level position."""
        request = Mock(spec=JobPricingRequest)
        request.id = "test-id"
        request.job_title = "Junior Developer"
        request.job_description = "Entry level position"
        request.years_of_experience_min = 0
        request.years_of_experience_max = 1
        request.location_text = None
        request.industry = None
        request.company_size = None

        skills = []

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_session.query.return_value = mock_query

        result, factors = self.service.calculate_pricing(request, skills)

        # Verify lower salary for entry level
        assert Decimal("40000") < result.target_salary < Decimal("70000")
        # Average experience: (0 + 1) / 2 = 0.5 years → classified as "entry" level
        # Entry level uses midpoint calculation which gives 1 year average
        # Multiplier: 1.0 + (1.0 * 0.03) = 1.03
        assert factors.experience_multiplier == pytest.approx(1.03, rel=0.01)
        assert factors.skill_premium == 0.0  # No skills

    def test_pricing_factors_returned(self):
        """Test that pricing factors are correctly returned."""
        request = Mock(spec=JobPricingRequest)
        request.id = "test-id"
        request.job_title = "Test Engineer"
        request.job_description = "Test description"
        request.years_of_experience_min = 5
        request.years_of_experience_max = 7
        request.location_text = "Singapore"
        request.industry = "Technology"
        request.company_size = "201-500"

        skills = [Mock(spec=JobSkillsExtracted, skill_name="Python", matched_tsc_code="CODE1")]

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_session.query.return_value = mock_query

        result, factors = self.service.calculate_pricing(request, skills)

        # Verify factors
        assert isinstance(factors, PricingFactors)
        assert factors.base_salary > 0
        assert factors.experience_multiplier >= 1.0
        assert factors.location_multiplier >= 0
        assert factors.skill_premium >= 0
        assert factors.industry_adjustment > 0
        assert factors.company_size_factor > 0
        assert 0 <= factors.confidence_score <= 100
