"""
Test Hybrid LLM Job Matching
Demonstrates embeddings + LLM reasoning for intelligent job matching.
"""
import logging
from src.job_pricing.core.database import get_session
from src.job_pricing.services.job_matching_service import JobMatchingService

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

session = get_session()
matching_service = JobMatchingService(session)

print("=" * 80)
print("HYBRID LLM JOB MATCHING TEST")
print("=" * 80)

# Test with HR role
job_title = "HR Business Partner"
job_description = "Senior HR professional partnering with business leaders on talent strategy, organizational development, and employee relations"

print(f"\nJOB TO MATCH:")
print(f"  Title: {job_title}")
print(f"  Description: {job_description}")

print(f"\n[STEP 1] Finding embedding candidates...")
candidates = matching_service.find_similar_jobs(
    job_title=job_title,
    job_description=job_description,
    top_k=5
)

if candidates:
    print(f"\nFound {len(candidates)} embedding candidates:")
    for i, c in enumerate(candidates, 1):
        print(f"  {i}. {c['job_title']} ({c['job_code']})")
        print(f"     Embedding similarity: {c['similarity_score']:.2%}")
else:
    print("\nNo candidates found")
    session.close()
    exit()

print(f"\n[STEP 2] Using LLM to analyze and select best match...")
match = matching_service.find_best_match(
    job_title=job_title,
    job_description=job_description,
    use_llm_reasoning=True  # Enable hybrid approach
)

print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

if match:
    print(f"\nBEST MATCH FOUND:")
    print(f"  Job Code: {match['job_code']}")
    print(f"  Job Title: {match['job_title']}")
    print(f"  Career Level: {match['career_level']}")
    print(f"  Family: {match['family']}")

    print(f"\nSCORES:")
    print(f"  Embedding Similarity: {match['similarity_score']:.2%}")
    if 'match_score' in match:
        print(f"  LLM Confidence: {match['match_score']:.2%}")

    if 'llm_reasoning' in match:
        print(f"\nLLM REASONING:")
        print(f"  {match['llm_reasoning']}")

    if 'key_similarities' in match:
        print(f"\nKEY SIMILARITIES:")
        for sim in match['key_similarities']:
            print(f"  - {sim}")

    if 'key_differences' in match:
        print(f"\nKEY DIFFERENCES:")
        for diff in match['key_differences']:
            print(f"  - {diff}")

    print(f"\nMATCHING METHOD: {match.get('matching_method', 'embedding_only')}")

    print("\n" + "=" * 80)
    print("SUCCESS: Hybrid LLM matching works!")
    print("=" * 80)
else:
    print("\nNO MATCH FOUND")
    print("LLM determined that none of the candidates are a good match.")
    print("=" * 80)

session.close()
