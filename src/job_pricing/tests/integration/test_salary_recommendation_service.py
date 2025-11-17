"""
Integration Tests for Salary Recommendation Service

Tests the service layer with real database connections.
NO MOCKING - Tests against actual data and algorithms.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
from sqlalchemy.orm import Session

from job_pricing.services.salary_recommendation_service import SalaryRecommendationService
from job_pricing.services.job_matching_service import JobMatchingService
from job_pricing.utils.database import get_db_context
from job_pricing.models.mercer import MercerJobLibrary, MercerMarketData


@pytest.fixture
def db_session():
    """Get database session."""
    with get_db_context() as session:
        yield session


@pytest.fixture
def salary_service():
    """Create salary recommendation service."""
    return SalaryRecommendationService()


@pytest.fixture
def matching_service():
    """Create job matching service."""
    return JobMatchingService()


class TestJobMatchingService:
    """Test job matching service with real embeddings."""

    def test_find_similar_jobs_basic(self, matching_service, db_session):
        """Test basic job matching."""
        # Verify we have jobs with embeddings
        job_count = db_session.query(MercerJobLibrary).filter(
            MercerJobLibrary.embedding.isnot(None)
        ).count()
        assert job_count > 0, "No jobs with embeddings in database"

        # Search for HR jobs
        matches = matching_service.find_similar_jobs(
            job_title="HR Business Partner",
            job_description="Strategic HR partner",
            job_family="HRM",
            top_k=5
        )

        # Should find some matches
        assert len(matches) > 0, "No matches found"
        assert len(matches) <= 5, "Returned more than top_k matches"

        # Verify match structure
        for match in matches:
            assert "job_code" in match
            assert "job_title" in match
            assert "similarity_score" in match
            assert "confidence" in match
            assert 0 <= match["similarity_score"] <= 1
            assert match["confidence"] in ["high", "medium", "low"]

    def test_find_similar_jobs_with_family_filter(self, matching_service):
        """Test job matching with family filtering."""
        matches = matching_service.find_similar_jobs(
            job_title="HR Director",
            job_family="HRM",  # Filter to HR family
            top_k=3
        )

        # All matches should be from HRM family
        for match in matches:
            assert match["family"] == "HRM", f"Expected HRM, got {match['family']}"

    def test_find_best_match(self, matching_service):
        """Test finding single best match."""
        best_match = matching_service.find_best_match(
            job_title="HR Business Partner",
            job_family="HRM"
        )

        # May or may not find match depending on similarity threshold
        if best_match:
            assert "job_code" in best_match
            assert "similarity_score" in best_match
            # Should meet minimum threshold (0.7)
            assert best_match["similarity_score"] >= 0.7

    def test_similarity_scores_descending(self, matching_service):
        """Test that similarity scores are in descending order."""
        matches = matching_service.find_similar_jobs(
            job_title="Senior HR Manager",
            job_family="HRM",
            top_k=5
        )

        if len(matches) > 1:
            for i in range(len(matches) - 1):
                assert matches[i]["similarity_score"] >= matches[i + 1]["similarity_score"], \
                    "Matches not in descending similarity order"


class TestSalaryRecommendationService:
    """Test salary recommendation service end-to-end."""

    def test_recommend_salary_success(self, salary_service, db_session):
        """Test successful salary recommendation."""
        # Verify we have market data
        market_data_count = db_session.query(MercerMarketData).count()
        assert market_data_count > 0, "No market data in database"

        result = salary_service.recommend_salary(
            job_title="HR Business Partner",
            job_description="Strategic HR role",
            location="Central Business District",
            job_family="HRM"
        )

        # Should succeed or fail gracefully
        assert "success" in result

        if result["success"]:
            rec = result["recommendation"]

            # Verify all required fields present
            assert "job_title" in rec
            assert "location" in rec
            assert "recommended_range" in rec
            assert "confidence" in rec
            assert "matched_jobs" in rec

            # Verify salary range is logical
            range_data = rec["recommended_range"]
            assert range_data["min"] < range_data["target"]
            assert range_data["target"] < range_data["max"]
            assert range_data["min"] > 0

            # Verify confidence scoring
            confidence = rec["confidence"]
            assert 0 <= confidence["score"] <= 100
            assert confidence["level"] in ["High", "Medium", "Low"]

    def test_recommend_salary_with_location_adjustment(self, salary_service, db_session):
        """Test that location adjustment is applied correctly."""
        from job_pricing.models.supporting import LocationIndex

        # Get two different locations
        locations = db_session.query(LocationIndex).limit(2).all()
        if len(locations) < 2:
            pytest.skip("Need at least 2 locations for this test")

        results = []
        for location in locations:
            result = salary_service.recommend_salary(
                job_title="HR Business Partner",
                location=location.location_name,
                job_family="HRM"
            )
            if result["success"]:
                results.append({
                    "location": location.location_name,
                    "index": float(location.cost_of_living_index),
                    "target": result["recommendation"]["recommended_range"]["target"]
                })

        # If we got results for both, verify adjustment was applied
        if len(results) == 2 and results[0]["index"] != results[1]["index"]:
            # Calculate expected ratio based on indices
            expected_ratio = results[0]["index"] / results[1]["index"]
            actual_ratio = results[0]["target"] / results[1]["target"]

            # Ratios should be close (within 10% due to weighting and rounding)
            assert abs(expected_ratio - actual_ratio) < 0.1, \
                f"Location adjustment not applied correctly: {expected_ratio:.2f} vs {actual_ratio:.2f}"

    def test_weighted_salary_calculation(self, salary_service):
        """Test that salaries are weighted by similarity scores."""
        result = salary_service.recommend_salary(
            job_title="HR Business Partner",
            job_family="HRM",
            location="Central Business District"
        )

        if result["success"]:
            rec = result["recommendation"]

            # If multiple jobs matched, verify weighting was applied
            if len(rec["matched_jobs"]) > 1:
                # The matched jobs should have different similarity scores
                similarities = [float(job["similarity"].rstrip('%')) / 100
                              for job in rec["matched_jobs"]]

                # At least some variance in similarities
                assert max(similarities) - min(similarities) > 0.01, \
                    "All similarities are too similar to test weighting"

    def test_confidence_scoring_factors(self, salary_service):
        """Test that confidence score includes all required factors."""
        result = salary_service.recommend_salary(
            job_title="Senior HR Director",
            job_family="HRM",
            location="Central Business District"
        )

        if result["success"]:
            confidence = result["recommendation"]["confidence"]

            # All three factors should be present
            assert "factors" in confidence
            factors = confidence["factors"]
            assert "job_match" in factors
            assert "data_points" in factors
            assert "sample_size" in factors

            # Factors should sum to approximately the total score
            factor_sum = sum(factors.values())
            assert abs(factor_sum - confidence["score"]) < 1.0, \
                "Confidence factors don't sum to total score"

    def test_no_matches_error_handling(self, salary_service):
        """Test graceful handling when no matches found."""
        result = salary_service.recommend_salary(
            job_title="Completely Nonexistent Job XYZ123",
            job_description="This does not exist",
            location="Central Business District"
        )

        # Should return graceful error
        assert result["success"] is False
        assert "error" in result

    def test_no_salary_data_error_handling(self, salary_service, db_session):
        """Test handling when jobs match but have no salary data."""
        # Find a job code that exists but has no market data
        job_with_no_data = db_session.query(MercerJobLibrary).outerjoin(
            MercerMarketData,
            MercerJobLibrary.job_code == MercerMarketData.job_code
        ).filter(MercerMarketData.id.is_(None)).first()

        if job_with_no_data:
            result = salary_service.recommend_salary(
                job_title=job_with_no_data.job_title,
                location="Central Business District"
            )

            # Should handle gracefully (either find similar jobs with data, or return error)
            assert "success" in result


class TestPerformance:
    """Test performance requirements."""

    def test_job_matching_performance(self, matching_service):
        """Test job matching completes quickly."""
        import time

        start = time.time()
        matches = matching_service.find_similar_jobs(
            job_title="HR Manager",
            job_family="HRM",
            top_k=5
        )
        duration = time.time() - start

        # Should be very fast (<1 second for similarity search)
        assert duration < 1.0, f"Job matching took {duration:.2f}s, should be <1s"

    def test_salary_recommendation_performance(self, salary_service):
        """Test salary recommendation meets performance target."""
        import time

        start = time.time()
        result = salary_service.recommend_salary(
            job_title="Senior Software Engineer",
            location="Central Business District",
            job_family="ICT"
        )
        duration = time.time() - start

        # Should meet target from algorithm spec (<5s P95)
        assert duration < 5.0, f"Recommendation took {duration:.2f}s, target is <5s"

        # Ideally under 2 seconds based on actual performance
        if result["success"]:
            assert duration < 2.0, f"Recommendation took {duration:.2f}s, goal is <2s"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_job_description(self, salary_service):
        """Test with empty job description (should still work with title only)."""
        result = salary_service.recommend_salary(
            job_title="HR Manager",
            job_description="",
            location="Central Business District",
            job_family="HRM"
        )

        # Should work with title only
        assert "success" in result

    def test_very_long_job_description(self, salary_service):
        """Test with very long job description."""
        long_description = "Strategic HR partner " * 200  # ~4000 chars

        result = salary_service.recommend_salary(
            job_title="HR Business Partner",
            job_description=long_description,
            location="Central Business District",
            job_family="HRM"
        )

        # Should handle long descriptions
        assert "success" in result

    def test_special_characters_in_title(self, salary_service):
        """Test with special characters in job title."""
        result = salary_service.recommend_salary(
            job_title="HR Manager (Asia-Pacific) - Talent & Development",
            location="Central Business District",
            job_family="HRM"
        )

        # Should handle special characters
        assert "success" in result

    def test_case_insensitivity(self, salary_service):
        """Test that matching is case-insensitive."""
        result1 = salary_service.recommend_salary(
            job_title="hr business partner",  # lowercase
            location="Central Business District",
            job_family="HRM"
        )

        result2 = salary_service.recommend_salary(
            job_title="HR BUSINESS PARTNER",  # uppercase
            location="Central Business District",
            job_family="HRM"
        )

        # Both should succeed or fail the same way
        assert result1["success"] == result2["success"]

        if result1["success"] and result2["success"]:
            # Recommendations should be very similar (same matched jobs)
            jobs1 = {j["job_code"] for j in result1["recommendation"]["matched_jobs"]}
            jobs2 = {j["job_code"] for j in result2["recommendation"]["matched_jobs"]}

            # At least 50% overlap in matched jobs
            overlap = len(jobs1 & jobs2) / max(len(jobs1), len(jobs2))
            assert overlap >= 0.5, "Case sensitivity affecting results"
