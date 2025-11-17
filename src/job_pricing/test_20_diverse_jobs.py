"""
Test Mercer Integration with 20+ Diverse Job Titles

Tests semantic matching and pricing across different:
- Industries (Tech, Finance, HR, Sales, Operations, etc.)
- Levels (Entry, Mid, Senior, Executive)
- Functions (Technical, Business, Support)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import os
import uuid
from job_pricing.core.database import get_session
from job_pricing.services.pricing_calculation_service_v3 import PricingCalculationServiceV3
from job_pricing.models import JobPricingRequest


# Test suite: 25 diverse job titles
TEST_JOBS = [
    # Technology - Various Levels
    {"title": "Software Engineer", "description": "Develops and maintains web applications using Python and JavaScript"},
    {"title": "Senior Data Scientist", "description": "Leads machine learning initiatives and analytics projects"},
    {"title": "DevOps Engineer", "description": "Manages cloud infrastructure and CI/CD pipelines"},
    {"title": "Chief Technology Officer", "description": "Sets technology vision and leads engineering teams"},
    {"title": "QA Automation Tester", "description": "Creates and maintains automated test suites"},

    # Finance
    {"title": "Financial Analyst", "description": "Performs financial modeling and budget analysis"},
    {"title": "Senior Accountant", "description": "Manages month-end close and financial reporting"},
    {"title": "Chief Financial Officer", "description": "Oversees all financial operations and strategic planning"},
    {"title": "Tax Manager", "description": "Handles corporate tax compliance and planning"},

    # Human Resources
    {"title": "HR Business Partner", "description": "Partners with business units on talent strategy"},
    {"title": "Talent Acquisition Specialist", "description": "Sources and recruits top talent"},
    {"title": "Compensation & Benefits Manager", "description": "Designs and manages compensation programs"},
    {"title": "Chief People Officer", "description": "Leads all aspects of human capital management"},

    # Sales & Marketing
    {"title": "Sales Manager", "description": "Leads sales team and drives revenue growth"},
    {"title": "Digital Marketing Manager", "description": "Develops and executes digital marketing campaigns"},
    {"title": "Business Development Executive", "description": "Identifies and pursues new business opportunities"},
    {"title": "Chief Marketing Officer", "description": "Sets marketing strategy and brand direction"},

    # Operations
    {"title": "Supply Chain Manager", "description": "Optimizes supply chain operations and logistics"},
    {"title": "Operations Analyst", "description": "Analyzes processes and drives operational efficiency"},
    {"title": "Chief Operating Officer", "description": "Oversees day-to-day business operations"},

    # Customer Service
    {"title": "Customer Success Manager", "description": "Ensures customer satisfaction and retention"},
    {"title": "Support Engineer", "description": "Provides technical support to customers"},

    # Legal & Compliance
    {"title": "Legal Counsel", "description": "Provides legal advice on contracts and compliance"},
    {"title": "Compliance Officer", "description": "Ensures regulatory compliance across operations"},

    # Product Management
    {"title": "Product Manager", "description": "Defines product roadmap and prioritizes features"},
]


def test_diverse_jobs():
    """Run pricing for 25 diverse job titles and report results."""

    # Get database session and service
    session = get_session()
    service = PricingCalculationServiceV3(session)

    print("=" * 100)
    print("TESTING MERCER INTEGRATION WITH 25 DIVERSE JOB TITLES")
    print("=" * 100)
    print()

    results = {
        "total": len(TEST_JOBS),
        "successful": 0,
        "failed": 0,
        "mercer_matched": 0,
        "no_mercer": 0,
        "errors": []
    }

    for idx, job in enumerate(TEST_JOBS, 1):
        try:
            print(f"\n[{idx}/{len(TEST_JOBS)}] Testing: {job['title']}")
            print(f"Description: {job['description'][:80]}...")

            # Create request object
            request = JobPricingRequest(
                id=uuid.uuid4(),
                job_title=job['title'],
                job_description=job['description'],
                years_of_experience_min=3,
                years_of_experience_max=5,
                location_text='Singapore',
                requested_by='test_suite',
                requestor_email='test@example.com'
            )

            # Add to session (required for the service)
            session.add(request)
            session.flush()

            # Calculate pricing
            pricing = service.calculate_pricing(request)

            # Check if Mercer contributed
            mercer_contrib = None
            for contrib in pricing.source_contributions:
                if 'mercer' in contrib.source_name.lower():
                    mercer_contrib = contrib
                    break

            if mercer_contrib and mercer_contrib.weight_percentage > 0:
                results["mercer_matched"] += 1
                match_quality = mercer_contrib.data_points.get("match_quality", "N/A")
                print(f"[OK] Mercer Match: {mercer_contrib.weight_percentage:.1f}% weight, {match_quality} match quality")
                print(f"  Matched to: {mercer_contrib.data_points.get('matched_job_title', 'Unknown')}")
                print(f"  Job Code: {mercer_contrib.data_points.get('matched_job_code', 'Unknown')}")
            else:
                results["no_mercer"] += 1
                print(f"[SKIP] No Mercer data")

            # Overall pricing result
            print(f"  Target Salary: SGD ${pricing.target_salary:,.0f}")
            print(f"  Confidence: {pricing.confidence_score}/100")
            print(f"  Total Sources: {len(pricing.source_contributions)}")

            results["successful"] += 1

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "job": job['title'],
                "error": str(e)
            })
            print(f"[ERROR] {str(e)}")

    # Summary report
    print("\n")
    print("=" * 100)
    print("SUMMARY REPORT")
    print("=" * 100)
    print(f"Total jobs tested: {results['total']}")
    print(f"Successful: {results['successful']} ({results['successful']/results['total']*100:.1f}%)")
    print(f"Failed: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")
    print(f"Mercer matches: {results['mercer_matched']} ({results['mercer_matched']/results['total']*100:.1f}%)")
    print(f"No Mercer data: {results['no_mercer']} ({results['no_mercer']/results['total']*100:.1f}%)")

    if results['errors']:
        print(f"\nErrors encountered: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error['job']}: {error['error']}")

    print("=" * 100)

    # Close session
    session.close()

    # Return pass/fail
    return results['successful'] == results['total'] and results['mercer_matched'] >= results['total'] * 0.5


if __name__ == '__main__':
    success = test_diverse_jobs()
    sys.exit(0 if success else 1)
