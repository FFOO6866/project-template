"""Simple test for job matching service."""
import sys
sys.path.insert(0, '/app')

from src.job_pricing.services.job_matching_service import JobMatchingService

def test_job_matching():
    """Test semantic job matching."""
    service = JobMatchingService()

    print("=" * 60)
    print("TESTING JOB MATCHING SERVICE")
    print("=" * 60)

    # Test case 1: Assistant Director, Total Rewards
    print("\n1. Testing: 'Assistant Director, Total Rewards'")
    matches = service.find_similar_jobs(
        job_title="Assistant Director, Total Rewards",
        job_description="Responsible for designing total rewards strategy",
        job_family="HRM",
        top_k=3
    )

    if matches:
        for i, match in enumerate(matches, 1):
            print(f"\n   Match #{i}:")
            print(f"   - Job: {match['job_title']}")
            print(f"   - Code: {match['job_code']}")
            print(f"   - Similarity: {match['similarity_score']:.1%}")
            print(f"   - Confidence: {match['confidence']}")
    else:
        print("   No matches found")

    # Test case 2: Senior HR Director
    print("\n\n2. Testing: 'Senior HR Director'")
    best_match = service.find_best_match(
        job_title="Senior HR Director",
        job_family="HRM"
    )

    if best_match:
        print(f"\n   Best Match:")
        print(f"   - Job: {best_match['job_title']}")
        print(f"   - Code: {best_match['job_code']}")
        print(f"   - Similarity: {best_match['similarity_score']:.1%}")
        print(f"   - Confidence: {best_match['confidence']}")
    else:
        print("   No match found above threshold")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_job_matching()
