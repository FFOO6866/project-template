"""
Test script to process a job pricing request end-to-end
"""

import sys
from uuid import UUID

from src.job_pricing.core.database import get_session
from src.job_pricing.services import JobProcessingService

# Request ID from the API call
request_id = "b15ebfa4-06d2-48cb-b910-29fd6ad7a564"

print("=" * 70)
print("JOB PRICING REQUEST PROCESSING TEST")
print("=" * 70)
print(f"Request ID: {request_id}")
print()

# Get database session
session = get_session()

try:
    # Create processing service
    print("Initializing processing service...")
    service = JobProcessingService(session)

    # Process the request
    print(f"\nProcessing request {request_id}...\n")
    result = service.process_request(UUID(request_id))

    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Status: {result.status}")
    print(f"Job Title: {result.job_title}")
    print(f"Job Description: {result.job_description[:100]}..." if len(result.job_description) > 100 else result.job_description)
    print()

    # Show extracted skills
    if hasattr(result, 'extracted_skills') and result.extracted_skills:
        print(f"Extracted Skills ({len(result.extracted_skills)}):")
        for skill in result.extracted_skills[:10]:  # Show first 10
            matched = f"→ {skill.matched_tsc_code}" if skill.matched_tsc_code else "✗ No match"
            confidence = f"({skill.match_confidence:.0%})" if skill.match_confidence else ""
            print(f"  • {skill.skill_name} {matched} {confidence}")
        if len(result.extracted_skills) > 10:
            print(f"  ... and {len(result.extracted_skills) - 10} more")
    else:
        print("No skills extracted yet")

    print("\n" + "=" * 70)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    session.close()
