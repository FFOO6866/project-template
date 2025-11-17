"""
Pytest Configuration for Integration Tests

Provides fixtures for database testing with real PostgreSQL.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from job_pricing.models import Base
from job_pricing.core.config import get_settings


@pytest.fixture(scope="session")
def db_engine():
    """
    Create a database engine for the test session.

    Uses the DATABASE_URL from environment or falls back to test database.
    """
    settings = get_settings()

    # Create engine
    engine = create_engine(
        settings.DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Teardown: drop all tables
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create a new database session for each test function.

    Uses a transaction that is rolled back after the test to ensure isolation.
    """
    connection = db_engine.connect()
    transaction = connection.begin()

    # Create session bound to the connection
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    # Rollback transaction to clean up
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def sample_job_request_data():
    """
    Provide sample data for creating job pricing requests.
    """
    return {
        "job_title": "Software Engineer",
        "job_description": "Develop and maintain web applications using Python and React",
        "location": "Singapore CBD",
        "internal_grade": "M4",
        "job_family": "Engineering",
        "department": "Product Development",
        "employment_type": "full_time",
        "years_experience_required": 3,
        "education_level": "bachelor",
        "requested_by": "hr@example.com",
    }


@pytest.fixture(scope="function")
def sample_mercer_job_data():
    """
    Provide sample data for creating Mercer jobs.
    """
    return {
        "job_code": "ICT.02.003.M40",
        "job_title": "Software Engineer - Applications",
        "family": "Information & Communication Technology",
        "sub_family": "Applications Development",
        "career_level": "M4",
        "job_description": "Designs, develops, and maintains software applications",
        "ipe_minimum": 300,
        "ipe_midpoint": 400,
        "ipe_maximum": 500,
    }


@pytest.fixture(scope="function")
def sample_ssg_job_role_data():
    """
    Provide sample data for creating SSG job roles.
    """
    return {
        "job_role_code": "ICT-DIS-4010-1.1",
        "job_role_title": "Software Developer",
        "sector": "Information and Communications Technology",
        "sub_sector": "Infocomm",
        "track": "Data & Insights",
        "career_level": "Senior/Lead",
    }


@pytest.fixture(scope="function")
def sample_scraped_listing_data():
    """
    Provide sample data for creating scraped job listings.
    """
    return {
        "job_title": "Backend Developer",
        "company_name": "Tech Startup Pte Ltd",
        "location": "Singapore - City Area",
        "source": "mcf",
        "source_job_id": "MCF-2025-001",
        "salary_min": 5000,
        "salary_max": 8000,
        "currency": "SGD",
        "job_description": "We are looking for an experienced backend developer",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    }


@pytest.fixture(scope="function")
def sample_employee_data():
    """
    Provide sample data for creating internal employees.
    """
    return {
        "employee_id": "EMP9999",
        "anonymized_name": "Employee 9999",
        "job_title": "Senior Software Engineer",
        "job_family": "Engineering",
        "department": "Product Development",
        "grade": "M5",
        "current_salary": 8500.00,
        "currency": "SGD",
    }
