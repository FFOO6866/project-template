"""
Seed script to populate applicants table with sample data

This script seeds the database with the 6 sample applicants that were
previously hardcoded in the frontend.
"""

from datetime import date
from src.job_pricing.core.database import SessionLocal
from src.job_pricing.repositories.hris_repository import HRISRepository


def seed_applicants():
    """Seed the applicants table with sample data."""
    session = SessionLocal()
    repo = HRISRepository(session)

    applicants_data = [
        {
            "applicant_id": "APP-2024-001",
            "name": "Lim Jia Wei",
            "current_organisation": "CapitaLand Group",
            "current_title": "Global Rewards Director",
            "applied_job_title": "Assistant Director, Total Rewards",
            "years_of_experience": 15,
            "current_salary": 12500,
            "expected_salary": 15000,
            "organisation_summary": "Leading property development and investment company in Asia",
            "role_scope": "Strategic rewards design across global property development portfolio",
            "application_status": "Interview Stage 2",
            "application_date": date(2024, 11, 1),
            "application_year": "2024",
            "job_family": "HR",
            "currency": "SGD",
            "data_anonymized": False,
        },
        {
            "applicant_id": "APP-2024-002",
            "name": "Chan Mei Fang",
            "current_organisation": "City Developments Ltd",
            "current_title": "Head Performance and Rewards",
            "applied_job_title": "Assistant Director, Total Rewards",
            "years_of_experience": 12,
            "current_salary": 11800,
            "expected_salary": 14500,
            "organisation_summary": "Diversified real estate company with hospitality and residential focus",
            "role_scope": "End-to-end performance management and rewards strategy",
            "application_status": "Offer Extended",
            "application_date": date(2024, 10, 15),
            "application_year": "2024",
            "job_family": "HR",
            "currency": "SGD",
            "data_anonymized": False,
        },
        {
            "applicant_id": "APP-2024-003",
            "name": "Tan Keng Hua",
            "current_organisation": "Shangri-La Group",
            "current_title": "Head of Rewards",
            "applied_job_title": "Assistant Director, Total Rewards",
            "years_of_experience": 10,
            "current_salary": 14200,
            "expected_salary": 16000,
            "organisation_summary": "Luxury hospitality group with global presence",
            "role_scope": "Global rewards strategy for hospitality operations",
            "application_status": "Declined Offer",
            "application_date": date(2024, 9, 20),
            "application_year": "2024",
            "job_family": "HR",
            "currency": "SGD",
            "data_anonymized": False,
        },
        {
            "applicant_id": "APP-2023-001",
            "name": "Wong Siew Ling",
            "current_organisation": "Frasers Property",
            "current_title": "Total Rewards Manager",
            "applied_job_title": "Assistant Director, Total Rewards",
            "years_of_experience": 8,
            "current_salary": 10500,
            "expected_salary": 13000,
            "organisation_summary": "Integrated real estate company with diversified portfolio",
            "role_scope": "Total rewards optimization and market benchmarking",
            "application_status": "Hired",
            "application_date": date(2023, 12, 5),
            "application_year": "2023",
            "job_family": "HR",
            "currency": "SGD",
            "data_anonymized": False,
        },
        {
            "applicant_id": "APP-2024-004",
            "name": "Kumar Raj",
            "current_organisation": "Marina Bay Sands",
            "current_title": "Compensation Manager",
            "applied_job_title": "Director, Total Rewards",
            "years_of_experience": 14,
            "current_salary": 13500,
            "expected_salary": 16500,
            "organisation_summary": "Integrated resort with retail, hospitality and entertainment",
            "role_scope": "Compensation strategy and market positioning",
            "application_status": "Interview Stage 1",
            "application_date": date(2024, 11, 10),
            "application_year": "2024",
            "job_family": "HR",
            "currency": "SGD",
            "data_anonymized": False,
        },
        {
            "applicant_id": "APP-2024-005",
            "name": "Lee Xiu Ying",
            "current_organisation": "Keppel Corporation",
            "current_title": "Senior Rewards Analyst",
            "applied_job_title": "Manager, Total Rewards",
            "years_of_experience": 6,
            "current_salary": 8500,
            "expected_salary": 10500,
            "organisation_summary": "Global asset manager and operator in various sectors",
            "role_scope": "Rewards analysis and benchmarking",
            "application_status": "Shortlisted",
            "application_date": date(2024, 10, 25),
            "application_year": "2024",
            "job_family": "HR",
            "currency": "SGD",
            "data_anonymized": False,
        },
    ]

    try:
        for app_data in applicants_data:
            repo.create_applicant(**app_data)

        session.commit()
        print(f"[SUCCESS] Successfully seeded {len(applicants_data)} applicants")

        # Display summary
        print("\n[SUMMARY] Seeded Data Summary:")
        print(f"   - Application Years: {set(app['application_year'] for app in applicants_data)}")
        print(f"   - Statuses: {set(app['application_status'] for app in applicants_data)}")
        print(f"   - Avg Experience: {sum(app['years_of_experience'] for app in applicants_data) / len(applicants_data):.1f} years")
        print(f"   - Salary Range: SGD {min(app['current_salary'] for app in applicants_data):,.0f} - {max(app['expected_salary'] for app in applicants_data):,.0f}")

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Error seeding applicants: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("[INFO] Seeding external applicants data...")
    seed_applicants()
