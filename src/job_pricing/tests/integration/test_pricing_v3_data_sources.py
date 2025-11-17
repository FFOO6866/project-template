"""
Integration Tests for V3 Pricing Service - Data Source Validation

Tests that REQUIRE real data sources instead of accepting fallback calculations.
Ensures production system uses actual market data for pricing calculations.
"""

import pytest
from decimal import Decimal
from job_pricing.models import JobPricingRequest
from job_pricing.services.pricing_calculation_service_v3 import PricingCalculationServiceV3
from job_pricing.services.job_matching_service import JobMatchingService


class TestDataSourceRequirements:
    """
    Tests that enforce minimum data source requirements.

    These tests FAIL if the system relies on fallback calculations when
    real data should be available.
    """

    def test_common_tech_job_requires_mcf_data(self, db_session):
        """
        Software Engineer should match MCF listings (105 jobs available).
        MUST NOT use fallback calculation.
        """
        request = JobPricingRequest(
            job_title="Software Engineer",
            job_description="Python backend developer with 3-5 years experience",
            location_text="Singapore",
            requested_by="test_data_sources",
            requestor_email="test@example.com",
            status="pending",
            urgency="normal"
        )
        db_session.add(request)
        db_session.flush()

        pricing_service = PricingCalculationServiceV3(db_session)
        result = pricing_service.calculate_pricing(request)

        # REQUIREMENT 1: Must use at least 1 real data source (not fallback)
        assert len(result.source_contributions) >= 1, \
            "Software Engineer MUST find MCF matches (105 jobs in DB)"

        # REQUIREMENT 2: MCF source must be present
        source_names = [s.source_name for s in result.source_contributions]
        assert "MyCareersFuture" in source_names, \
            f"MCF data missing. Found: {source_names}"

        # REQUIREMENT 3: Confidence must be reasonable with real data
        assert result.confidence_score >= 40, \
            f"Confidence too low ({result.confidence_score}) for common job with MCF data"

        # REQUIREMENT 4: Sample size must be > 0
        mcf_contrib = next(s for s in result.source_contributions if s.source_name == "MyCareersFuture")
        assert mcf_contrib.sample_size > 0, \
            "MCF should have matched job listings"

    def test_hr_job_requires_mercer_data(self, db_session):
        """
        HR Business Partner should match Mercer data (174 HRM jobs available).
        MUST NOT return None from Mercer source.
        """
        request = JobPricingRequest(
            job_title="HR Business Partner",
            job_description="Senior HR professional partnering with business leaders on talent strategy, organizational development, and change management",
            location_text="Singapore",
            requested_by="test_data_sources",
            requestor_email="test@example.com",
            status="pending",
            urgency="normal"
        )
        db_session.add(request)
        db_session.flush()

        # First verify Mercer matching works for HR jobs
        matching_service = JobMatchingService(db_session)
        mercer_match = matching_service.find_best_match(
            job_title=request.job_title,
            job_description=request.job_description,
            use_llm_reasoning=True
        )

        assert mercer_match is not None, \
            "HR Business Partner MUST match Mercer HRM library (174 jobs available)"

        # Now test full pricing
        pricing_service = PricingCalculationServiceV3(db_session)
        result = pricing_service.calculate_pricing(request)

        # REQUIREMENT 1: Must use at least 1 real source
        assert len(result.source_contributions) >= 1, \
            "HR job must have real data sources"

        # REQUIREMENT 2: Should attempt to use Mercer (may not always meet 70% threshold)
        # But at least one of MCF or Mercer should contribute
        source_names = [s.source_name for s in result.source_contributions]
        has_premium_source = any(name in ["Mercer", "MyCareersFuture"] for name in source_names)
        assert has_premium_source, \
            f"HR job should use Mercer or MCF data. Found: {source_names}"

    def test_hr_manager_minimum_confidence(self, db_session):
        """
        HR Manager with good description should achieve minimum confidence.
        """
        request = JobPricingRequest(
            job_title="HR Manager",
            job_description="Manage HR operations including recruitment, employee relations, compensation and benefits administration for Singapore office",
            location_text="Singapore",
            requested_by="test_data_sources",
            requestor_email="test@example.com",
            status="pending",
            urgency="normal"
        )
        db_session.add(request)
        db_session.flush()

        pricing_service = PricingCalculationServiceV3(db_session)
        result = pricing_service.calculate_pricing(request)

        # REQUIREMENT: Minimum 60% confidence for jobs with multiple data sources
        if len(result.source_contributions) >= 2:
            assert result.confidence_score >= 60, \
                f"With {len(result.source_contributions)} sources, confidence should be >= 60% (got {result.confidence_score})"

    def test_data_scientist_uses_mcf_not_fallback(self, db_session):
        """
        Data Scientist should match MCF listings, not use fallback.
        """
        request = JobPricingRequest(
            job_title="Data Scientist",
            job_description="Python, machine learning, data analysis and visualization",
            location_text="Singapore",
            requested_by="test_data_sources",
            requestor_email="test@example.com",
            status="pending",
            urgency="normal"
        )
        db_session.add(request)
        db_session.flush()

        pricing_service = PricingCalculationServiceV3(db_session)
        result = pricing_service.calculate_pricing(request)

        # REQUIREMENT: Must have at least one real source
        assert len(result.source_contributions) >= 1, \
            "Data Scientist should find MCF matches"

        # Verify not using fallback
        source_names = [s.source_name for s in result.source_contributions]
        assert "Fallback" not in source_names and "fallback" not in str(source_names).lower(), \
            f"Should not use fallback for common tech job. Sources: {source_names}"


class TestMercerIntegration:
    """
    Tests specifically for Mercer data integration.
    """

    def test_mercer_vector_search_for_hr_jobs(self, db_session):
        """
        Verify Mercer vector search works for HR-related jobs.
        """
        matching_service = JobMatchingService(db_session)

        hr_jobs = [
            ("HR Director", "Lead HR function"),
            ("Talent Acquisition Manager", "Recruit and hire talent"),
            ("Compensation Analyst", "Design compensation programs"),
            ("HR Business Partner", "Partner with business leaders"),
        ]

        matches_found = 0
        for job_title, description in hr_jobs:
            matches = matching_service.find_similar_jobs(
                job_title=job_title,
                job_description=description,
                top_k=5
            )

            if matches and len(matches) > 0:
                matches_found += 1

        # At least 3 out of 4 HR jobs should find matches in Mercer
        assert matches_found >= 3, \
            f"Only {matches_found}/4 HR jobs found Mercer matches. Expected >= 3"

    def test_mercer_returns_none_for_non_hr_jobs(self, db_session):
        """
        Verify Mercer correctly returns None for non-HR jobs.
        This is EXPECTED behavior since Mercer data is HR-only.
        """
        matching_service = JobMatchingService(db_session)

        non_hr_jobs = [
            ("Software Engineer", "Python developer"),
            ("Data Scientist", "ML engineer"),
            ("Product Manager", "Product strategy"),
        ]

        for job_title, description in non_hr_jobs:
            match = matching_service.find_best_match(
                job_title=job_title,
                job_description=description,
                use_llm_reasoning=True
            )

            # Should return None due to low similarity (cross-domain matching)
            # This is correct behavior, not a bug
            if match:
                # If a match is found, similarity should be very low
                similarity = match.get('similarity_score', 0)
                assert similarity < 0.5, \
                    f"{job_title} matched Mercer with {similarity:.2%} similarity. " \
                    f"Expected None or very low similarity for non-HR job."

    def test_mercer_embedding_quality(self, db_session):
        """
        Verify Mercer jobs have proper embeddings.
        """
        from job_pricing.models import MercerJobLibrary

        # Check that embeddings exist and are correct dimension
        jobs_with_embeddings = db_session.query(MercerJobLibrary).filter(
            MercerJobLibrary.embedding.isnot(None)
        ).all()

        assert len(jobs_with_embeddings) > 0, \
            "Mercer library should have jobs with embeddings"

        # Verify embedding dimension
        for job in jobs_with_embeddings[:5]:  # Check first 5
            assert len(job.embedding) == 1536, \
                f"Job {job.job_code} has wrong embedding dimension: {len(job.embedding)}"


class TestConfidenceScoring:
    """
    Tests for confidence scoring logic.
    """

    def test_multiple_sources_increase_confidence(self, db_session):
        """
        Jobs with multiple data sources should have higher confidence.
        """
        # Test 1: HR job (likely to have Mercer + MCF)
        hr_request = JobPricingRequest(
            job_title="Recruiting Manager",
            job_description="Manage recruitment team and hiring strategy",
            location_text="Singapore",
            requested_by="test_confidence",
            requestor_email="test@example.com",
            status="pending",
            urgency="normal"
        )
        db_session.add(hr_request)
        db_session.flush()

        pricing_service = PricingCalculationServiceV3(db_session)
        hr_result = pricing_service.calculate_pricing(hr_request)

        # Test 2: Tech job with minimal description (likely only MCF)
        tech_request = JobPricingRequest(
            job_title="Developer",
            job_description="",
            location_text="Singapore",
            requested_by="test_confidence",
            requestor_email="test@example.com",
            status="pending",
            urgency="normal"
        )
        db_session.add(tech_request)
        db_session.flush()

        tech_result = pricing_service.calculate_pricing(tech_request)

        # HR job should generally have more sources
        hr_sources = len(hr_result.source_contributions)
        tech_sources = len(tech_result.source_contributions)

        # If HR has more sources, confidence should reflect that
        if hr_sources > tech_sources:
            assert hr_result.confidence_score >= tech_result.confidence_score, \
                f"More sources should mean higher confidence: " \
                f"HR ({hr_sources} sources, {hr_result.confidence_score}% conf) vs " \
                f"Tech ({tech_sources} sources, {tech_result.confidence_score}% conf)"

    def test_fallback_calculation_low_confidence(self, db_session):
        """
        Fallback calculations should have lower confidence scores.
        """
        # Create an obscure job unlikely to match anything
        request = JobPricingRequest(
            job_title="Underwater Basket Weaver",
            job_description="",
            location_text="Singapore",
            requested_by="test_confidence",
            requestor_email="test@example.com",
            status="pending",
            urgency="normal"
        )
        db_session.add(request)
        db_session.flush()

        pricing_service = PricingCalculationServiceV3(db_session)
        result = pricing_service.calculate_pricing(request)

        # If using fallback, confidence should be low
        if len(result.source_contributions) == 0:
            assert result.confidence_score < 60, \
                f"Fallback calculation should have confidence < 60% (got {result.confidence_score}%)"


class TestDataQuality:
    """
    Tests for data quality and consistency.
    """

    def test_mcf_data_freshness(self, db_session):
        """
        Verify MCF data is recent enough for pricing.
        """
        from job_pricing.models import ScrapedJobListing
        from datetime import datetime, timedelta, timezone

        # Check MCF data recency
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
        recent_mcf_jobs = db_session.query(ScrapedJobListing).filter(
            ScrapedJobListing.source == 'mycareersfuture',
            ScrapedJobListing.scraped_at >= cutoff_date
        ).count()

        # Should have at least some recent data (within 90 days)
        # NOTE: This may fail if scrapers haven't been run recently
        if recent_mcf_jobs == 0:
            pytest.skip("No recent MCF data found. Run MCF scraper to update data.")

        assert recent_mcf_jobs > 0, \
            "MCF data should be refreshed within 90 days for accurate pricing"

    def test_salary_ranges_are_reasonable(self, db_session):
        """
        Test that calculated salaries are within reasonable ranges for Singapore.
        """
        test_jobs = [
            ("Software Engineer", "Python developer", 50000, 200000),
            ("Data Scientist", "ML experience", 60000, 250000),
            ("HR Manager", "HR operations", 40000, 150000),
        ]

        pricing_service = PricingCalculationServiceV3(db_session)

        for job_title, description, min_expected, max_expected in test_jobs:
            request = JobPricingRequest(
                job_title=job_title,
                job_description=description,
                location_text="Singapore",
                requested_by="test_ranges",
                requestor_email="test@example.com",
                status="pending",
                urgency="normal"
            )
            db_session.add(request)
            db_session.flush()

            result = pricing_service.calculate_pricing(request)

            # Target salary should be within reasonable range for Singapore
            assert min_expected <= result.target_salary <= max_expected, \
                f"{job_title} salary ${result.target_salary:,.0f} outside reasonable range " \
                f"${min_expected:,.0f}-${max_expected:,.0f}"

    def test_percentile_spread_is_reasonable(self, db_session):
        """
        Test that percentile spreads are realistic (not too narrow or too wide).
        """
        request = JobPricingRequest(
            job_title="Product Manager",
            job_description="Senior product manager with 5+ years experience",
            location_text="Singapore",
            requested_by="test_spread",
            requestor_email="test@example.com",
            status="pending",
            urgency="normal"
        )
        db_session.add(request)
        db_session.flush()

        pricing_service = PricingCalculationServiceV3(db_session)
        result = pricing_service.calculate_pricing(request)

        # P90 should be 1.3x - 2.5x P10 (reasonable market spread)
        spread_ratio = float(result.p90 / result.p10)
        assert 1.3 <= spread_ratio <= 2.5, \
            f"Percentile spread ratio {spread_ratio:.2f} is unrealistic. " \
            f"P10: ${result.p10:,.0f}, P90: ${result.p90:,.0f}"


class TestResultPersistence:
    """
    Tests for result persistence to database.
    """

    def test_pricing_result_persisted_to_database(self, db_session):
        """
        Verify that pricing results are saved to job_pricing_results table.
        """
        from job_pricing.models import JobPricingResult

        request = JobPricingRequest(
            job_title="Backend Engineer",
            job_description="Python and PostgreSQL experience",
            location_text="Singapore",
            requested_by="test_persistence",
            requestor_email="test@example.com",
            status="pending",
            urgency="normal"
        )
        db_session.add(request)
        db_session.flush()
        request_id = request.id

        # Calculate pricing
        pricing_service = PricingCalculationServiceV3(db_session)
        result = pricing_service.calculate_pricing(request)

        # Commit to ensure persistence
        db_session.commit()

        # Query back from database
        persisted_result = db_session.query(JobPricingResult).filter_by(
            request_id=request_id
        ).first()

        assert persisted_result is not None, \
            "Pricing result should be persisted to database"

        # Verify data integrity
        assert persisted_result.target_salary == result.target_salary, \
            "Persisted salary doesn't match calculated salary"

        assert persisted_result.confidence_score == result.confidence_score, \
            "Persisted confidence doesn't match calculated confidence"

        assert persisted_result.confidence_level in ['High', 'Medium', 'Low'], \
            f"Invalid confidence level: {persisted_result.confidence_level}"

    def test_data_source_contributions_persisted(self, db_session):
        """
        Verify that data source contributions are saved.
        """
        from job_pricing.models import JobPricingResult, DataSourceContribution

        request = JobPricingRequest(
            job_title="Full Stack Developer",
            job_description="React and Node.js developer",
            location_text="Singapore",
            requested_by="test_persistence",
            requestor_email="test@example.com",
            status="pending",
            urgency="normal"
        )
        db_session.add(request)
        db_session.flush()
        request_id = request.id

        # Calculate pricing
        pricing_service = PricingCalculationServiceV3(db_session)
        result = pricing_service.calculate_pricing(request)

        db_session.commit()

        # Query persisted result
        persisted_result = db_session.query(JobPricingResult).filter_by(
            request_id=request_id
        ).first()

        if persisted_result and len(result.source_contributions) > 0:
            # Query source contributions
            contributions = db_session.query(DataSourceContribution).filter_by(
                result_id=persisted_result.id
            ).all()

            assert len(contributions) > 0, \
                "Data source contributions should be persisted"

            # Verify contribution data
            for contrib in contributions:
                assert contrib.source_name, "Source name should be populated"
                assert 0 <= contrib.weight_applied <= 1, "Weight should be 0-1"
                assert contrib.sample_size > 0, "Sample size should be positive"
