"""
Integration Tests for Salary Recommendation API

Tests the complete API endpoints with real database and services.
NO MOCKING - Tests against actual PostgreSQL database with real data.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from job_pricing.api.main import app
from job_pricing.utils.database import get_db_context
from job_pricing.models.mercer import MercerJobLibrary, MercerMarketData
from job_pricing.models.supporting import LocationIndex


# Test client fixture
@pytest.fixture
def client():
    """Create test client for API."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Get database session for verification."""
    with get_db_context() as session:
        yield session


class TestSalaryRecommendationAPI:
    """Test suite for salary recommendation API endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_recommend_salary_success(self, client, db_session):
        """Test successful salary recommendation with real data."""
        # Prepare request
        request_data = {
            "job_title": "Senior HR Business Partner",
            "job_description": "Strategic HR partner supporting business units",
            "location": "Tampines",
            "job_family": "HRM"
        }

        # Make request
        response = client.post("/api/v1/salary/recommend", json=request_data)

        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["success"] is True
        assert data["job_title"] == "Senior HR Business Partner"
        assert data["location"] == "Tampines"
        assert data["currency"] == "SGD"
        assert data["period"] == "annual"

        # Verify salary range
        assert "recommended_range" in data
        assert data["recommended_range"]["min"] > 0
        assert data["recommended_range"]["target"] > 0
        assert data["recommended_range"]["max"] > 0
        assert data["recommended_range"]["min"] < data["recommended_range"]["target"]
        assert data["recommended_range"]["target"] < data["recommended_range"]["max"]

        # Verify confidence scoring
        assert "confidence" in data
        assert 0 <= data["confidence"]["score"] <= 100
        assert data["confidence"]["level"] in ["High", "Medium", "Low"]

        # Verify matched jobs
        assert "matched_jobs" in data
        assert len(data["matched_jobs"]) > 0
        for job in data["matched_jobs"]:
            assert "job_code" in job
            assert "job_title" in job
            assert "similarity" in job
            assert "confidence" in job

        # Verify data sources
        assert "data_sources" in data
        assert "mercer_market_data" in data["data_sources"]

        # Verify location adjustment
        assert "location_adjustment" in data
        assert data["location_adjustment"]["location"] == "Tampines"
        assert data["location_adjustment"]["cost_of_living_index"] > 0

    def test_recommend_salary_no_matches(self, client):
        """Test salary recommendation when no matches found."""
        request_data = {
            "job_title": "Completely Nonexistent Job Title XYZ123",
            "job_description": "This job does not exist",
            "location": "Central Business District"
        }

        response = client.post("/api/v1/salary/recommend", json=request_data)

        # Should return 404 with error
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_recommend_salary_invalid_request(self, client):
        """Test salary recommendation with invalid request data."""
        # Empty job title
        request_data = {
            "job_title": "",
            "location": "Central Business District"
        }

        response = client.post("/api/v1/salary/recommend", json=request_data)

        # Should return 422 (validation error)
        assert response.status_code == 422

    def test_match_jobs_success(self, client):
        """Test job matching endpoint."""
        request_data = {
            "job_title": "HR Business Partner",
            "job_description": "Strategic HR partner",
            "job_family": "HRM",
            "top_k": 3
        }

        response = client.post("/api/v1/salary/match", json=request_data)

        # Should return matches (or 404 if no matches)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "matched_jobs" in data
            assert len(data["matched_jobs"]) <= 3
            assert data["query"] == "HR Business Partner"

    def test_list_locations(self, client, db_session):
        """Test locations listing endpoint."""
        # Verify locations exist in database
        location_count = db_session.query(LocationIndex).count()
        assert location_count > 0, "No locations in database"

        # Make API request
        response = client.get("/api/v1/salary/locations")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == location_count
        assert len(data["locations"]) == location_count

        # Verify location structure
        for location in data["locations"]:
            assert "name" in location
            assert "cost_of_living_index" in location
            assert location["cost_of_living_index"] > 0

    def test_get_stats(self, client, db_session):
        """Test system statistics endpoint."""
        # Verify data exists in database
        total_jobs = db_session.query(MercerJobLibrary).count()
        jobs_with_embeddings = db_session.query(MercerJobLibrary).filter(
            MercerJobLibrary.embedding.isnot(None)
        ).count()
        jobs_with_salaries = db_session.query(MercerMarketData).count()
        total_locations = db_session.query(LocationIndex).count()

        assert total_jobs > 0, "No jobs in database"
        assert jobs_with_embeddings > 0, "No embeddings in database"

        # Make API request
        response = client.get("/api/v1/salary/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "statistics" in data

        # Verify stats match database
        stats = data["statistics"]
        assert stats["mercer_jobs"]["total"] == total_jobs
        assert stats["mercer_jobs"]["with_embeddings"] == jobs_with_embeddings
        assert stats["mercer_jobs"]["with_salary_data"] == jobs_with_salaries
        assert stats["locations"]["total"] == total_locations

        # Verify data freshness info
        assert "data_freshness" in stats
        if jobs_with_salaries > 0:
            assert stats["data_freshness"]["survey_name"] is not None
            assert stats["data_freshness"]["survey_date"] is not None

    def test_recommend_salary_with_career_level_filter(self, client):
        """Test salary recommendation with career level filtering."""
        request_data = {
            "job_title": "HR Director",
            "location": "Central Business District",
            "job_family": "HRM",
            "career_level": "M6"
        }

        response = client.post("/api/v1/salary/recommend", json=request_data)

        # Should return results or 404 if no matches at that level
        assert response.status_code in [200, 404]

    def test_recommend_salary_different_locations(self, client, db_session):
        """Test salary recommendations for different locations."""
        # Get two different locations
        locations = db_session.query(LocationIndex).limit(2).all()
        assert len(locations) >= 2, "Need at least 2 locations for this test"

        base_request = {
            "job_title": "HR Business Partner",
            "job_family": "HRM"
        }

        results = []
        for location in locations:
            request_data = {**base_request, "location": location.location_name}
            response = client.post("/api/v1/salary/recommend", json=request_data)

            if response.status_code == 200:
                results.append({
                    "location": location.location_name,
                    "index": float(location.cost_of_living_index),
                    "salary": response.json()["recommended_range"]["target"]
                })

        # If we got results for both locations, verify adjustment was applied
        if len(results) == 2:
            # Salaries should differ based on location index
            # (unless indices are exactly the same)
            if results[0]["index"] != results[1]["index"]:
                ratio = results[0]["salary"] / results[1]["salary"]
                index_ratio = results[0]["index"] / results[1]["index"]
                # Ratios should be similar (within 5% due to rounding)
                assert abs(ratio - index_ratio) < 0.05

    def test_api_response_time(self, client):
        """Test API response time is acceptable."""
        import time

        request_data = {
            "job_title": "Senior Software Engineer",
            "location": "Central Business District",
            "job_family": "ICT"
        }

        start = time.time()
        response = client.post("/api/v1/salary/recommend", json=request_data)
        duration = time.time() - start

        # Response should be under 5 seconds (target from algorithm spec)
        assert duration < 5.0, f"API response took {duration:.2f}s, should be <5s"

        # Ideally under 2 seconds (based on actual performance)
        if response.status_code == 200:
            assert duration < 2.0, f"API response took {duration:.2f}s, target is <2s"


class TestAPIErrorHandling:
    """Test error handling in API."""

    def test_invalid_json(self, client):
        """Test API handles invalid JSON gracefully."""
        response = client.post(
            "/api/v1/salary/recommend",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test API validates required fields."""
        # Missing job_title
        response = client.post("/api/v1/salary/recommend", json={})

        assert response.status_code == 422

    def test_invalid_field_types(self, client):
        """Test API validates field types."""
        request_data = {
            "job_title": 12345,  # Should be string
            "location": "Central Business District"
        }

        response = client.post("/api/v1/salary/recommend", json=request_data)

        assert response.status_code == 422

    def test_job_title_too_short(self, client):
        """Test job title minimum length validation."""
        request_data = {
            "job_title": "AB",  # Too short (min 3 chars)
            "location": "Central Business District"
        }

        response = client.post("/api/v1/salary/recommend", json=request_data)

        assert response.status_code == 422

    def test_invalid_top_k(self, client):
        """Test top_k validation in match endpoint."""
        # top_k too high
        request_data = {
            "job_title": "HR Director",
            "top_k": 100  # Max is 10
        }

        response = client.post("/api/v1/salary/match", json=request_data)

        assert response.status_code == 422


class TestDataIntegrity:
    """Test data integrity across the system."""

    def test_mercer_jobs_have_embeddings(self, db_session):
        """Verify all Mercer jobs have embeddings."""
        total_jobs = db_session.query(MercerJobLibrary).count()
        jobs_with_embeddings = db_session.query(MercerJobLibrary).filter(
            MercerJobLibrary.embedding.isnot(None)
        ).count()

        assert total_jobs > 0, "No jobs in database"
        assert jobs_with_embeddings == total_jobs, \
            f"Only {jobs_with_embeddings}/{total_jobs} jobs have embeddings"

    def test_market_data_references_valid_jobs(self, db_session):
        """Verify market data references valid job codes."""
        # Get all market data job codes
        market_data_codes = set(
            row[0] for row in db_session.query(MercerMarketData.job_code).distinct()
        )

        # Get all valid job library codes
        job_library_codes = set(
            row[0] for row in db_session.query(MercerJobLibrary.job_code).distinct()
        )

        # All market data codes should exist in job library
        invalid_codes = market_data_codes - job_library_codes
        assert len(invalid_codes) == 0, \
            f"Market data has {len(invalid_codes)} invalid job codes: {invalid_codes}"

    def test_salary_data_has_valid_ranges(self, db_session):
        """Verify salary data has logical P25 < P50 < P75."""
        market_data = db_session.query(MercerMarketData).filter(
            MercerMarketData.p25.isnot(None),
            MercerMarketData.p50.isnot(None),
            MercerMarketData.p75.isnot(None)
        ).all()

        assert len(market_data) > 0, "No complete salary data in database"

        for data in market_data:
            assert data.p25 < data.p50, \
                f"P25 ({data.p25}) should be < P50 ({data.p50}) for {data.job_code}"
            assert data.p50 < data.p75, \
                f"P50 ({data.p50}) should be < P75 ({data.p75}) for {data.job_code}"
            assert data.p25 > 0, f"P25 should be positive for {data.job_code}"

    def test_locations_have_valid_indices(self, db_session):
        """Verify all locations have positive cost-of-living indices."""
        locations = db_session.query(LocationIndex).all()

        assert len(locations) > 0, "No locations in database"

        for location in locations:
            assert location.cost_of_living_index > 0, \
                f"Location {location.location_name} has invalid index {location.cost_of_living_index}"
            assert location.cost_of_living_index < 2.0, \
                f"Location {location.location_name} has unusually high index {location.cost_of_living_index}"
