"""Test script for Salary Recommendation Service."""
import sys
sys.path.insert(0, '/app')

from src.job_pricing.services.salary_recommendation_service import SalaryRecommendationService


def test_salary_recommendation():
    """Test end-to-end salary recommendation."""
    print("=" * 70)
    print("TESTING SALARY RECOMMENDATION SERVICE")
    print("=" * 70)

    service = SalaryRecommendationService()

    # Test Case 1: HR Director role
    print("\n1. Testing: 'HR Director, Total Rewards'")
    print("-" * 70)

    result = service.recommend_salary(
        job_title="HR Director, Total Rewards",
        job_description="Responsible for designing total rewards strategy and compensation programs",
        location="Central Business District",
        job_family="HRM"
    )

    if result["success"]:
        rec = result["recommendation"]
        print(f"\n✓ SUCCESS")
        print(f"\nJob: {rec['job_title']}")
        print(f"Location: {rec['location']}")
        print(f"\nRecommended Salary Range:")
        print(f"  Minimum (P25):  SGD {rec['recommended_range']['min']:>10,.2f}")
        print(f"  Target (P50):   SGD {rec['recommended_range']['target']:>10,.2f}")
        print(f"  Maximum (P75):  SGD {rec['recommended_range']['max']:>10,.2f}")

        print(f"\nConfidence Score: {rec['confidence']['score']:.1f}/100 ({rec['confidence']['level']})")
        print(f"  - Job Match:     {rec['confidence']['factors']['job_match']:.1f} points")
        print(f"  - Data Points:   {rec['confidence']['factors']['data_points']:.1f} points")
        print(f"  - Sample Size:   {rec['confidence']['factors']['sample_size']:.1f} points")

        print(f"\nMatched Mercer Jobs (Top 3):")
        for i, job in enumerate(rec['matched_jobs'], 1):
            print(f"  {i}. {job['job_title']}")
            print(f"     Code: {job['job_code']} | Similarity: {job['similarity']} | Confidence: {job['confidence']}")

        print(f"\nData Source:")
        print(f"  Survey: {rec['data_sources']['mercer_market_data']['survey']}")
        print(f"  Jobs Matched: {rec['data_sources']['mercer_market_data']['jobs_matched']}")
        print(f"  Total Sample: {rec['data_sources']['mercer_market_data']['total_sample_size']} organizations")

        print(f"\nLocation Adjustment:")
        print(f"  {rec['location_adjustment']['note']}")

        print(f"\nSummary:")
        print(f"  {rec['summary']}")
    else:
        print(f"\n✗ FAILED: {result.get('error')}")
        if 'matched_jobs' in result:
            print(f"\nMatched jobs found but no salary data available:")
            for job in result['matched_jobs']:
                print(f"  - {job['job_title']} ({job['job_code']})")

    # Test Case 2: HR Business Partner
    print("\n\n2. Testing: 'Senior HR Business Partner'")
    print("-" * 70)

    result2 = service.recommend_salary(
        job_title="Senior HR Business Partner",
        job_description="Strategic HR partner supporting business units",
        location="Tampines",
        job_family="HRM"
    )

    if result2["success"]:
        rec2 = result2["recommendation"]
        print(f"\n✓ SUCCESS")
        print(f"\nRecommended Range: SGD {rec2['recommended_range']['min']:,.0f} - {rec2['recommended_range']['max']:,.0f}")
        print(f"Target: SGD {rec2['recommended_range']['target']:,.0f}")
        print(f"Confidence: {rec2['confidence']['level']} ({rec2['confidence']['score']:.0f}/100)")
        print(f"Best Match: {rec2['matched_jobs'][0]['job_title']} ({rec2['matched_jobs'][0]['similarity']})")
    else:
        print(f"\n✗ FAILED: {result2.get('error')}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_salary_recommendation()
