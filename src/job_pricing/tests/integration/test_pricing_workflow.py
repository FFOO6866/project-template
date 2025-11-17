"""
Integration Tests for Complete Pricing Workflow

Tests the end-to-end workflow from request creation through pricing calculation.
Uses real database (no mocking) to ensure all components work together.
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from src.job_pricing.models import (
    JobPricingRequest,
    JobSkillsExtracted,
    JobPricingResult,
)
from src.job_pricing.repositories.job_pricing_repository import JobPricingRepository
from src.job_pricing.services.job_processing_service import JobProcessingService
from src.job_pricing.services.pricing_calculation_service import PricingCalculationService


class TestCompletePricingWorkflow:
    """
    Test complete end-to-end pricing workflow.

    Workflow:
    1. Create job pricing request
    2. Process request (extract skills, match to SSG, calculate pricing)
    3. Verify results are stored correctly
    """

    def test_basic_pricing_workflow(self, db_session):
        """Test basic end-to-end pricing workflow."""
        # Step 1: Create job pricing request
        request = JobPricingRequest(
            job_title="Software Engineer",
            job_description="Build scalable web applications using Python, React, and AWS. "
                          "Experience with Docker and Kubernetes required.",
            location_text="Singapore",
            years_of_experience_min=3,
            years_of_experience_max=5,
            industry="Technology",
            company_size="51-200",
            urgency="normal",
            requested_by="test@example.com",
            requestor_email="test@example.com",
            status="pending",
        )

        db_session.add(request)
        db_session.commit()
        db_session.refresh(request)

        assert request.id is not None
        assert request.status == "pending"

        # Step 2: Process the request
        service = JobProcessingService(db_session)
        processed_request = service.process_request(request.id)

        # Step 3: Verify processing completed
        assert processed_request.status == "completed"
        assert processed_request.error_message is None

        # Step 4: Verify skills were extracted
        extracted_skills = (
            db_session.query(JobSkillsExtracted)
            .filter_by(request_id=request.id)
            .all()
        )

        assert len(extracted_skills) > 0
        skill_names = [s.skill_name.lower() for s in extracted_skills]

        # Should have extracted some of the mentioned skills
        assert any(skill in skill_names for skill in ["python", "react", "aws", "docker", "kubernetes"])

        # Step 5: Verify pricing result was calculated
        pricing_result = (
            db_session.query(JobPricingResult)
            .filter_by(request_id=request.id)
            .first()
        )

        assert pricing_result is not None
        assert pricing_result.target_salary is not None
        assert pricing_result.target_salary > 0
        assert pricing_result.recommended_min is not None
        assert pricing_result.recommended_max is not None
        assert pricing_result.recommended_min < pricing_result.target_salary < pricing_result.recommended_max

        # Verify percentiles
        assert pricing_result.p10 is not None
        assert pricing_result.p25 is not None
        assert pricing_result.p50 is not None
        assert pricing_result.p75 is not None
        assert pricing_result.p90 is not None

        # Verify percentiles are in order
        assert pricing_result.p10 < pricing_result.p25 < pricing_result.p50 < pricing_result.p75 < pricing_result.p90

        # Verify confidence score
        assert pricing_result.confidence_score is not None
        assert 0 <= pricing_result.confidence_score <= 100
        assert pricing_result.confidence_level in ["High", "Medium", "Low"]

        # Verify currency and period
        assert pricing_result.currency == "SGD"
        assert pricing_result.period == "annual"

    def test_senior_level_high_salary_workflow(self, db_session):
        """Test pricing workflow for senior-level position with high salary expectations."""
        # Create senior-level request
        request = JobPricingRequest(
            job_title="Senior Data Scientist",
            job_description="Lead data science initiatives. Expertise in Python, Machine Learning, "
                          "AWS, TensorFlow, and data pipeline architecture. PhD preferred.",
            location_text="Singapore",
            years_of_experience_min=8,
            years_of_experience_max=12,
            industry="Finance",  # Higher multiplier
            company_size="1000+",  # Larger company
            urgency="high",
            requested_by="test@example.com",
            requestor_email="test@example.com",
            status="pending",
        )

        db_session.add(request)
        db_session.commit()

        # Process the request
        service = JobProcessingService(db_session)
        processed_request = service.process_request(request.id)

        assert processed_request.status == "completed"

        # Verify pricing reflects senior level
        pricing_result = (
            db_session.query(JobPricingResult)
            .filter_by(request_id=request.id)
            .first()
        )

        # Senior level in Finance with large company should have high salary
        assert pricing_result.target_salary > Decimal("150000")

        # Verify high-value skills were detected
        extracted_skills = (
            db_session.query(JobSkillsExtracted)
            .filter_by(request_id=request.id)
            .all()
        )

        skill_names = [s.skill_name.lower() for s in extracted_skills]
        high_value_skills_found = sum(
            1 for skill in ["python", "machine learning", "aws"]
            if skill in skill_names
        )

        assert high_value_skills_found >= 2, "Should detect high-value skills"

    def test_entry_level_workflow(self, db_session):
        """Test pricing workflow for entry-level position."""
        request = JobPricingRequest(
            job_title="Junior Web Developer",
            job_description="Entry-level position for fresh graduates. Learn HTML, CSS, JavaScript, "
                          "and basic web development practices.",
            location_text="Singapore",
            years_of_experience_min=0,
            years_of_experience_max=2,
            industry="Technology",
            company_size="11-50",  # Small startup
            urgency="normal",
            requested_by="test@example.com",
            requestor_email="test@example.com",
            status="pending",
        )

        db_session.add(request)
        db_session.commit()

        # Process the request
        service = JobProcessingService(db_session)
        processed_request = service.process_request(request.id)

        assert processed_request.status == "completed"

        # Verify pricing reflects entry level
        pricing_result = (
            db_session.query(JobPricingResult)
            .filter_by(request_id=request.id)
            .first()
        )

        # Entry level should have lower salary
        assert Decimal("40000") < pricing_result.target_salary < Decimal("80000")

    def test_workflow_with_no_skills(self, db_session):
        """Test pricing workflow when no skills are mentioned in description."""
        request = JobPricingRequest(
            job_title="Project Manager",
            job_description="Manage projects and coordinate team activities.",
            location_text="Singapore",
            years_of_experience_min=5,
            years_of_experience_max=7,
            industry="General",
            company_size="51-200",
            urgency="normal",
            requested_by="test@example.com",
            requestor_email="test@example.com",
            status="pending",
        )

        db_session.add(request)
        db_session.commit()

        # Process the request
        service = JobProcessingService(db_session)
        processed_request = service.process_request(request.id)

        # Should still complete successfully even without detected skills
        assert processed_request.status == "completed"

        # Should still generate pricing
        pricing_result = (
            db_session.query(JobPricingResult)
            .filter_by(request_id=request.id)
            .first()
        )

        assert pricing_result is not None
        assert pricing_result.target_salary > 0

    def test_workflow_with_minimal_data(self, db_session):
        """Test pricing workflow with only required fields."""
        request = JobPricingRequest(
            job_title="Analyst",
            job_description="",
            status="pending",
            requested_by="test@example.com",
            requestor_email="test@example.com",
        )

        db_session.add(request)
        db_session.commit()

        # Process the request
        service = JobProcessingService(db_session)
        processed_request = service.process_request(request.id)

        # Should complete but with lower confidence
        assert processed_request.status == "completed"

        pricing_result = (
            db_session.query(JobPricingResult)
            .filter_by(request_id=request.id)
            .first()
        )

        assert pricing_result is not None
        # Confidence should be lower due to missing data
        assert pricing_result.confidence_score < 85


class TestPricingCalculationIntegration:
    """
    Test pricing calculation service with real database.
    """

    def test_pricing_with_real_skills(self, db_session):
        """Test pricing calculation with actual extracted skills in database."""
        # Create request
        request = JobPricingRequest(
            job_title="Backend Engineer",
            job_description="Python backend development",
            location_text="Singapore",
            years_of_experience_min=4,
            years_of_experience_max=6,
            industry="Technology",
            company_size="201-500",
            status="processing",
            requested_by="test@example.com",
            requestor_email="test@example.com",
        )

        db_session.add(request)
        db_session.commit()
        db_session.refresh(request)

        # Add extracted skills
        skills = [
            JobSkillsExtracted(
                request_id=request.id,
                skill_name="Python",
                skill_category="Programming",
                matched_tsc_code="TSC-PRG-001",
                match_confidence=0.95,
                is_core_skill=True,
            ),
            JobSkillsExtracted(
                request_id=request.id,
                skill_name="AWS",
                skill_category="Cloud",
                matched_tsc_code="TSC-CLD-001",
                match_confidence=0.90,
                is_core_skill=True,
            ),
            JobSkillsExtracted(
                request_id=request.id,
                skill_name="Docker",
                skill_category="DevOps",
                matched_tsc_code="TSC-DEV-001",
                match_confidence=0.85,
                is_core_skill=False,
            ),
        ]

        for skill in skills:
            db_session.add(skill)
        db_session.commit()

        # Calculate pricing
        pricing_service = PricingCalculationService(db_session)
        extracted_skills = (
            db_session.query(JobSkillsExtracted)
            .filter_by(request_id=request.id)
            .all()
        )

        pricing_result, pricing_factors = pricing_service.calculate_pricing(
            request, extracted_skills
        )

        # Verify pricing factors
        assert pricing_factors.base_salary > 0
        assert pricing_factors.experience_multiplier >= 1.0
        assert pricing_factors.location_multiplier == 1.0  # Singapore
        assert pricing_factors.skill_premium > 0  # Should have Python and AWS premium
        assert pricing_factors.industry_adjustment == 1.15  # Technology
        assert pricing_factors.company_size_factor == 1.10  # 201-500

        # Verify pricing result
        assert pricing_result.target_salary > 0
        assert pricing_result.currency == "SGD"
        assert pricing_result.period == "annual"

    def test_confidence_scoring_integration(self, db_session):
        """Test confidence scoring with complete data vs minimal data."""
        # Request with complete data
        complete_request = JobPricingRequest(
            job_title="Full Stack Developer",
            job_description="Build modern web applications using React, Node.js, and PostgreSQL. "
                          "Experience with cloud deployment and CI/CD pipelines required. "
                          "Work in an agile team environment.",  # >100 chars
            location_text="Singapore",
            years_of_experience_min=3,
            years_of_experience_max=5,
            industry="Technology",
            company_size="51-200",
            status="processing",
            requested_by="test@example.com",
            requestor_email="test@example.com",
        )

        db_session.add(complete_request)
        db_session.commit()
        db_session.refresh(complete_request)

        # Add some matched skills
        skill = JobSkillsExtracted(
            request_id=complete_request.id,
            skill_name="React",
            skill_category="Frontend",
            matched_tsc_code="TSC-FE-001",
            match_confidence=0.95,
            is_core_skill=True,
        )
        db_session.add(skill)
        db_session.commit()

        # Calculate pricing
        pricing_service = PricingCalculationService(db_session)
        extracted_skills = [skill]

        pricing_result, _ = pricing_service.calculate_pricing(
            complete_request, extracted_skills
        )

        # Confidence should be high (good description, experience data, location, skills)
        assert pricing_result.confidence_score >= 80
        assert pricing_result.confidence_level in ["High", "Medium"]


class TestRepositoryIntegration:
    """
    Test JobPricingRepository with real database operations.
    """

    def test_create_and_retrieve_request(self, db_session):
        """Test creating and retrieving job pricing requests."""
        repository = JobPricingRepository(db_session)

        # Create request
        request = JobPricingRequest(
            job_title="DevOps Engineer",
            job_description="Manage infrastructure and deployment pipelines",
            status="pending",
            requested_by="test@example.com",
            requestor_email="test@example.com",
        )

        created_request = repository.create(request)
        db_session.commit()

        # Retrieve by ID
        retrieved_request = repository.get_by_id(created_request.id)

        assert retrieved_request is not None
        assert retrieved_request.id == created_request.id
        assert retrieved_request.job_title == "DevOps Engineer"
        assert retrieved_request.status == "pending"

    def test_mark_as_processing(self, db_session):
        """Test marking request as processing."""
        repository = JobPricingRepository(db_session)

        # Create request
        request = JobPricingRequest(
            job_title="Data Analyst",
            job_description="Analyze data and create reports",
            status="pending",
            requested_by="test@example.com",
            requestor_email="test@example.com",
        )

        created_request = repository.create(request)
        db_session.commit()

        # Mark as processing
        repository.mark_as_processing(created_request.id)
        db_session.commit()

        # Verify status changed
        updated_request = repository.get_by_id(created_request.id)
        assert updated_request.status == "processing"
        assert updated_request.processing_started_at is not None

    def test_mark_as_completed(self, db_session):
        """Test marking request as completed."""
        repository = JobPricingRepository(db_session)

        # Create and start processing request
        request = JobPricingRequest(
            job_title="UX Designer",
            job_description="Design user interfaces",
            status="processing",
            requested_by="test@example.com",
            requestor_email="test@example.com",
        )

        created_request = repository.create(request)
        db_session.commit()

        # Mark as completed
        repository.mark_as_completed(created_request.id, duration_seconds=10)
        db_session.commit()

        # Verify status changed
        updated_request = repository.get_by_id(created_request.id)
        assert updated_request.status == "completed"
        assert updated_request.processing_completed_at is not None

    def test_get_with_full_details(self, db_session):
        """Test retrieving request with all related data."""
        repository = JobPricingRepository(db_session)

        # Create request
        request = JobPricingRequest(
            job_title="Mobile Developer",
            job_description="Build iOS and Android applications",
            status="completed",
            requested_by="test@example.com",
            requestor_email="test@example.com",
        )

        created_request = repository.create(request)
        db_session.commit()
        db_session.refresh(created_request)

        # Add skills
        skill = JobSkillsExtracted(
            request_id=created_request.id,
            skill_name="Swift",
            skill_category="Programming",
            is_core_skill=True,
        )
        db_session.add(skill)

        # Add pricing result
        pricing = JobPricingResult(
            request_id=created_request.id,
            currency="SGD",
            period="annual",
            target_salary=Decimal("100000"),
            recommended_min=Decimal("80000"),
            recommended_max=Decimal("120000"),
            confidence_score=Decimal("85.0"),
            confidence_level="High",
        )
        db_session.add(pricing)
        db_session.commit()

        # Retrieve with full details
        full_request = repository.get_with_full_details(created_request.id)

        assert full_request is not None
        assert len(full_request.extracted_skills) == 1
        assert full_request.extracted_skills[0].skill_name == "Swift"
        assert full_request.pricing_result is not None
        assert full_request.pricing_result.target_salary == Decimal("100000")
