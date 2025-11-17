"""
Integration Tests for Repository Pattern

Tests the repository implementations against a real PostgreSQL database.
Requires Docker containers to be running.

Run with: pytest tests/integration/test_repositories.py
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from src.job_pricing.models import (
    JobPricingRequest,
    JobPricingResult,
    MercerJobLibrary,
    MercerJobMapping,
    SSGSkillsFramework,
    SSGTSC,
    ScrapedJobListing,
    InternalEmployee,
    GradeSalaryBand,
)
from src.job_pricing.repositories import (
    JobPricingRepository,
    MercerRepository,
    SSGRepository,
    ScrapingRepository,
    HRISRepository,
)


class TestJobPricingRepository:
    """Test JobPricingRepository operations."""

    def test_create_and_get_request(self, db_session: Session):
        """Test creating and retrieving a job pricing request."""
        repo = JobPricingRepository(db_session)

        # Create a request
        request = JobPricingRequest(
            job_title="Software Engineer",
            job_description="Develop and maintain web applications",
            location="Singapore CBD",
            internal_grade="M4",
            requested_by="test@example.com",
            status="pending",
        )

        created = repo.create(request)
        repo.commit()

        assert created.id is not None
        assert created.job_title == "Software Engineer"
        assert created.status == "pending"

        # Retrieve the request
        retrieved = repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.job_title == "Software Engineer"

    def test_get_by_user(self, db_session: Session):
        """Test retrieving requests by user email."""
        repo = JobPricingRepository(db_session)
        user_email = "user@example.com"

        # Create multiple requests for the same user
        for i in range(3):
            request = JobPricingRequest(
                job_title=f"Position {i}",
                job_description="Test description",
                location="Singapore",
                internal_grade="M3",
                requested_by=user_email,
            )
            repo.create(request)

        repo.commit()

        # Retrieve requests for the user
        user_requests = repo.get_by_user(user_email)
        assert len(user_requests) >= 3
        assert all(r.requested_by == user_email for r in user_requests)

    def test_mark_as_processing(self, db_session: Session):
        """Test marking a request as processing."""
        repo = JobPricingRepository(db_session)

        # Create a pending request
        request = JobPricingRequest(
            job_title="Data Analyst",
            job_description="Analyze data",
            location="Singapore",
            internal_grade="M3",
            requested_by="test@example.com",
            status="pending",
        )
        created = repo.create(request)
        repo.commit()

        # Mark as processing
        updated = repo.mark_as_processing(created.id)
        repo.commit()

        assert updated.status == "processing"
        assert updated.processing_started_at is not None

    def test_mark_as_completed(self, db_session: Session):
        """Test marking a request as completed."""
        repo = JobPricingRepository(db_session)

        # Create a processing request
        request = JobPricingRequest(
            job_title="HR Manager",
            job_description="Manage HR operations",
            location="Singapore",
            internal_grade="M5",
            requested_by="test@example.com",
            status="processing",
            processing_started_at=datetime.now(timezone.utc),
        )
        created = repo.create(request)
        repo.commit()

        # Mark as completed
        updated = repo.mark_as_completed(created.id, duration_seconds=45)
        repo.commit()

        assert updated.status == "completed"
        assert updated.processing_completed_at is not None
        assert updated.processing_duration_seconds == 45

    def test_get_statistics(self, db_session: Session):
        """Test getting statistics about requests."""
        repo = JobPricingRepository(db_session)
        user_email = "stats_user@example.com"

        # Create requests with different statuses
        statuses = ["pending", "processing", "completed", "failed"]
        for status in statuses:
            request = JobPricingRequest(
                job_title="Test Job",
                job_description="Test",
                location="Singapore",
                internal_grade="M3",
                requested_by=user_email,
                status=status,
                processing_duration_seconds=30 if status == "completed" else None,
            )
            repo.create(request)

        repo.commit()

        # Get statistics
        stats = repo.get_statistics(user_email=user_email)

        assert stats["total"] >= 4
        assert stats["pending"] >= 1
        assert stats["processing"] >= 1
        assert stats["completed"] >= 1
        assert stats["failed"] >= 1
        assert stats["avg_processing_time"] is not None


class TestMercerRepository:
    """Test MercerRepository operations."""

    def test_create_and_get_job(self, db_session: Session):
        """Test creating and retrieving a Mercer job."""
        repo = MercerRepository(db_session)

        # Create a Mercer job
        job = MercerJobLibrary(
            job_code="TEST.01.001.M40",
            job_title="Test Engineer",
            family="Engineering",
            career_level="M4",
            job_description="Test description",
        )

        created = repo.create(job)
        repo.commit()

        assert created.id is not None
        assert created.job_code == "TEST.01.001.M40"

        # Retrieve by job code
        retrieved = repo.get_by_job_code("TEST.01.001.M40")
        assert retrieved is not None
        assert retrieved.job_title == "Test Engineer"

    def test_get_by_family(self, db_session: Session):
        """Test retrieving jobs by family."""
        repo = MercerRepository(db_session)

        # Create jobs in the same family
        for i in range(3):
            job = MercerJobLibrary(
                job_code=f"ENG.01.00{i}.M40",
                job_title=f"Engineer {i}",
                family="Engineering",
                career_level="M4",
            )
            repo.create(job)

        repo.commit()

        # Retrieve by family
        engineering_jobs = repo.get_by_family("Engineering")
        assert len(engineering_jobs) >= 3

    def test_search_by_title(self, db_session: Session):
        """Test searching jobs by title."""
        repo = MercerRepository(db_session)

        # Create a job with specific title
        job = MercerJobLibrary(
            job_code="ANALYST.01.001.M30",
            job_title="Senior Data Analyst",
            family="Analytics",
            career_level="M3",
        )
        repo.create(job)
        repo.commit()

        # Search by title
        results = repo.search_by_title("analyst")
        assert len(results) >= 1
        assert any("Analyst" in job.job_title for job in results)

    def test_create_job_mapping(self, db_session: Session):
        """Test creating a job mapping."""
        repo = MercerRepository(db_session)

        # First create a Mercer job
        mercer_job = MercerJobLibrary(
            job_code="MAP.01.001.M40",
            job_title="Mapper Job",
            family="Test",
            career_level="M4",
        )
        created_job = repo.create(mercer_job)
        repo.commit()

        # Create a request (simplified - would normally come from JobPricingRepository)
        request_id = uuid4()

        # Create a job mapping
        mapping = repo.create_job_mapping(
            request_id=request_id,
            mercer_job_id=created_job.id,
            confidence_score=0.92,
            match_method="semantic",
            semantic_similarity=0.92,
            title_similarity=0.85,
        )
        repo.commit()

        assert mapping.id is not None
        assert mapping.confidence_score == 0.92
        assert mapping.match_method == "semantic"


class TestSSGRepository:
    """Test SSGRepository operations."""

    def test_create_and_get_job_role(self, db_session: Session):
        """Test creating and retrieving an SSG job role."""
        repo = SSGRepository(db_session)

        # Create an SSG job role
        job_role = SSGSkillsFramework(
            job_role_code="TEST-ICT-001-1.0",
            job_role_title="Test Software Developer",
            sector="Information and Communications Technology",
            track="Software Development",
        )

        created = repo.create(job_role)
        repo.commit()

        assert created.id is not None
        assert created.job_role_code == "TEST-ICT-001-1.0"

        # Retrieve by code
        retrieved = repo.get_by_job_role_code("TEST-ICT-001-1.0")
        assert retrieved is not None
        assert retrieved.job_role_title == "Test Software Developer"

    def test_get_by_sector(self, db_session: Session):
        """Test retrieving job roles by sector."""
        repo = SSGRepository(db_session)

        # Create job roles in the same sector
        for i in range(3):
            job_role = SSGSkillsFramework(
                job_role_code=f"FIN-00{i}-1.0",
                job_role_title=f"Financial Role {i}",
                sector="Financial Services",
                track="Finance",
            )
            repo.create(job_role)

        repo.commit()

        # Retrieve by sector
        finance_roles = repo.get_by_sector("Financial Services")
        assert len(finance_roles) >= 3

    def test_search_by_job_role(self, db_session: Session):
        """Test searching job roles by title."""
        repo = SSGRepository(db_session)

        # Create a job role
        job_role = SSGSkillsFramework(
            job_role_code="DEV-ICT-001-1.0",
            job_role_title="Backend Developer",
            sector="Information and Communications Technology",
            track="Software Development",
        )
        repo.create(job_role)
        repo.commit()

        # Search by title
        results = repo.search_by_job_role("developer")
        assert len(results) >= 1
        assert any("Developer" in role.job_role_title for role in results)


class TestScrapingRepository:
    """Test ScrapingRepository operations."""

    def test_create_and_get_listing(self, db_session: Session):
        """Test creating and retrieving a scraped job listing."""
        repo = ScrapingRepository(db_session)

        # Create a job listing
        listing = ScrapedJobListing(
            job_title="Software Engineer",
            company_name="Tech Company",
            location="Singapore CBD",
            source="mcf",
            source_job_id="MCF-12345",
            posted_date=datetime.now(timezone.utc),
            salary_min=5000,
            salary_max=8000,
            currency="SGD",
        )

        created = repo.create(listing)
        repo.commit()

        assert created.id is not None
        assert created.job_title == "Software Engineer"

        # Retrieve by ID
        retrieved = repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.company_name == "Tech Company"

    def test_get_active_listings(self, db_session: Session):
        """Test retrieving active job listings."""
        repo = ScrapingRepository(db_session)

        # Create a recent listing
        listing = ScrapedJobListing(
            job_title="Recent Job",
            company_name="Company A",
            location="Singapore",
            source="glassdoor",
            source_job_id="GD-67890",
            posted_date=datetime.now(timezone.utc),
        )
        repo.create(listing)
        repo.commit()

        # Get active listings from last 30 days
        active = repo.get_active_listings(days=30)
        assert len(active) >= 1

    def test_search_by_title(self, db_session: Session):
        """Test searching listings by title."""
        repo = ScrapingRepository(db_session)

        # Create a listing
        listing = ScrapedJobListing(
            job_title="Data Scientist",
            company_name="AI Company",
            location="Singapore",
            source="mcf",
            source_job_id="MCF-99999",
            posted_date=datetime.now(timezone.utc),
        )
        repo.create(listing)
        repo.commit()

        # Search by title
        results = repo.search_by_title("data")
        assert len(results) >= 1
        assert any("Data" in listing.job_title for listing in results)


class TestHRISRepository:
    """Test HRISRepository operations."""

    def test_create_and_get_employee(self, db_session: Session):
        """Test creating and retrieving an employee record."""
        repo = HRISRepository(db_session)

        # Create an employee
        employee = InternalEmployee(
            employee_id="EMP001",
            anonymized_name="Employee A",
            job_title="Software Engineer",
            job_family="Engineering",
            department="IT",
            grade="M4",
            current_salary=7000.00,
            currency="SGD",
            hire_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        )

        created = repo.create(employee)
        repo.commit()

        assert created.id is not None
        assert created.employee_id == "EMP001"

        # Retrieve by ID
        retrieved = repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.job_title == "Software Engineer"

    def test_get_by_grade(self, db_session: Session):
        """Test retrieving employees by grade."""
        repo = HRISRepository(db_session)

        # Create employees at the same grade
        for i in range(5):
            employee = InternalEmployee(
                employee_id=f"EMP00{i}",
                anonymized_name=f"Employee {i}",
                job_title="Engineer",
                job_family="Engineering",
                grade="M3",
                current_salary=5000 + (i * 500),
                hire_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
            )
            repo.create(employee)

        repo.commit()

        # Retrieve by grade
        m3_employees = repo.get_by_grade("M3")
        assert len(m3_employees) >= 5

    def test_get_salary_statistics_with_anonymization(self, db_session: Session):
        """Test salary statistics with PDPA anonymization."""
        repo = HRISRepository(db_session)

        # Create only 3 employees (below threshold of 5)
        for i in range(3):
            employee = InternalEmployee(
                employee_id=f"PDPA_EMP00{i}",
                anonymized_name=f"PDPA Employee {i}",
                job_title="Analyst",
                job_family="Analytics",
                grade="M2",
                current_salary=4000 + (i * 200),
                hire_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
            )
            repo.create(employee)

        repo.commit()

        # Should return None due to PDPA (< 5 employees)
        stats = repo.get_salary_statistics(grade="M2", anonymize=True)
        assert stats is None

        # Create 3 more employees to reach threshold
        for i in range(3, 6):
            employee = InternalEmployee(
                employee_id=f"PDPA_EMP00{i}",
                anonymized_name=f"PDPA Employee {i}",
                job_title="Analyst",
                job_family="Analytics",
                grade="M2",
                current_salary=4000 + (i * 200),
                hire_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
            )
            repo.create(employee)

        repo.commit()

        # Now should return stats (>= 5 employees)
        stats = repo.get_salary_statistics(grade="M2", anonymize=True)
        assert stats is not None
        assert stats["count"] >= 5
        assert stats["avg_salary"] is not None

    def test_create_salary_band(self, db_session: Session):
        """Test creating a salary band."""
        repo = HRISRepository(db_session)

        # Create a salary band
        band = repo.create_salary_band(
            grade="M4",
            salary_min=5000,
            salary_max=8000,
            midpoint=6500,
            market_position="P50",
            currency="SGD",
        )
        repo.commit()

        assert band.id is not None
        assert band.grade == "M4"
        assert band.salary_min == 5000
        assert band.salary_max == 8000

        # Retrieve by grade
        retrieved = repo.get_salary_band_by_grade("M4")
        assert retrieved is not None
        assert retrieved.midpoint == 6500
