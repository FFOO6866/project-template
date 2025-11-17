"""Test that result persistence works with fixed constraint."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from job_pricing.core.database import get_session
from job_pricing.models import JobPricingRequest, JobPricingResult
from job_pricing.services.pricing_calculation_service_v3 import PricingCalculationServiceV3

session = get_session()

request = JobPricingRequest(
    job_title='Software Engineer',
    job_description='Python backend developer',
    location_text='Singapore',
    requested_by='test_persistence',
    requestor_email='test@example.com',
    status='pending',
    urgency='normal'
)
session.add(request)
session.flush()
req_id = request.id

print(f"Created request: {req_id}")

pricing_service = PricingCalculationServiceV3(session)
result = pricing_service.calculate_pricing(request)

print(f"Calculated pricing: ${result.target_salary:,.0f}")

session.commit()

# Query back
saved = session.query(JobPricingResult).filter_by(request_id=req_id).first()

if saved:
    print("\nSUCCESS! Result persistence working!")
    print(f"  Result ID: {saved.id}")
    print(f"  Target: SGD ${saved.target_salary:,.0f}")
    print(f"  Confidence: {saved.confidence_score:.0f}/100 ({saved.confidence_level})")
    print(f"  Sources: {saved.data_sources_used}")
    print(f"  Data points: {saved.total_data_points}")
else:
    print("\nFAILED - not persisted")

session.close()
