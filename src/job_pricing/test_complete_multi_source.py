"""
Complete Multi-Source Pricing Test with Hybrid LLM Matching
Tests the full workflow: Hybrid matching → Mercer + MCF data → V3 pricing
"""
import logging
from src.job_pricing.core.database import get_session
from src.job_pricing.models import JobPricingRequest
from src.job_pricing.services.pricing_calculation_service_v3 import PricingCalculationServiceV3

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

session = get_session()

print("=" * 80)
print("COMPLETE MULTI-SOURCE PRICING TEST")
print("Hybrid LLM Matching -> Mercer Market Data -> V3 Pricing")
print("=" * 80)

# Test with a job that should have Mercer market data
request = JobPricingRequest(
    job_title='Head of Human Resources',
    job_description='Senior executive leading all HR functions including talent acquisition, development, compensation, and employee relations for a mid-sized company',
    location_text='Singapore',
    requested_by='test_user',
    requestor_email='test@example.com',
    status='pending',
    urgency='normal'
)
session.add(request)
session.flush()

print(f"\nJOB REQUEST:")
print(f"  Title: {request.job_title}")
print(f"  Description: {request.job_description[:80]}...")
print(f"  Location: {request.location_text}")

print(f"\n[STAGE 1] Hybrid LLM Job Matching...")
pricing_service = PricingCalculationServiceV3(session)
result = pricing_service.calculate_pricing(request)

print("\n" + "=" * 80)
print("PRICING RESULTS")
print("=" * 80)

print(f"\nSALARY RECOMMENDATION:")
print(f"  Target Salary:     SGD ${result.target_salary:,.0f}")
print(f"  Recommended Range: SGD ${result.recommended_min:,.0f} - ${result.recommended_max:,.0f}")
print(f"  Confidence Score:  {result.confidence_score:.0f}/100 ({result.confidence_score/100:.0%})")

print(f"\nPERCENTILES:")
print(f"  P10 (Low Market):   ${result.p10:,.0f}")
print(f"  P25 (Budget):       ${result.p25:,.0f}")
print(f"  P50 (Market/Target):${result.p50:,.0f}")
print(f"  P75 (Competitive):  ${result.p75:,.0f}")
print(f"  P90 (High Market):  ${result.p90:,.0f}")

print(f"\nDATA SOURCES ({len(result.source_contributions)}):")
total_weight = 0
for contrib in result.source_contributions:
    total_weight += contrib.weight
    print(f"\n  {contrib.source_name.upper()}:")
    print(f"    Weight:        {contrib.weight * 100:.0f}%")
    print(f"    Sample Size:   {contrib.sample_size}")
    print(f"    Data Age:      {contrib.recency_days} days")
    print(f"    Match Quality: {contrib.match_quality * 100:.0f}%")
    if contrib.p50:
        print(f"    P50 from source: ${contrib.p50:,.0f}")

print(f"\n  TOTAL DATA COVERAGE: {total_weight * 100:.0f}%")

print(f"\nALTERNATIVE SCENARIOS:")
for name, scenario in result.alternative_scenarios.items():
    print(f"  {name.upper():15s}: ${scenario['min']:,.0f} - ${scenario['max']:,.0f}")
    if 'use_case' in scenario:
        print(f"                   ({scenario['use_case']})")

print(f"\nEXPLANATION:")
print(f"  {result.explanation}")

# Analyze results
print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

sources_found = {c.source_name for c in result.source_contributions}

if 'mercer' in sources_found:
    print("\n✅ MERCER DATA: Successfully integrated!")
    mercer = [c for c in result.source_contributions if c.source_name == 'mercer'][0]
    print(f"   - Mercer provides 40% weight in pricing")
    print(f"   - Survey data from {mercer.recency_days} days ago")
    print(f"   - Match quality: {mercer.match_quality:.0%}")
else:
    print("\n⚠️  MERCER DATA: Not found")
    print("   - Job may not have Singapore market data")
    print("   - Or LLM selected job without market data")

if 'my_careers_future' in sources_found:
    print("\n✅ MCF DATA: Successfully integrated!")
    mcf = [c for c in result.source_contributions if c.source_name == 'my_careers_future'][0]
    print(f"   - MCF provides 25% weight in pricing")
    print(f"   - {mcf.sample_size} jobs found")
    print(f"   - Data from {mcf.recency_days} days ago")
else:
    print("\n⚠️  MCF DATA: Not found")
    print("   - No matching jobs in MCF database")

# Success criteria
print("\n" + "=" * 80)
if len(result.source_contributions) >= 2:
    print("🎉 MULTI-SOURCE PRICING SUCCESS!")
    print("=" * 80)
    print(f"\n✅ Used {len(result.source_contributions)} data sources")
    print(f"✅ Total coverage: {total_weight:.0%}")
    print(f"✅ Confidence: {result.confidence_score:.0f}/100")
    if total_weight >= 0.65:
        print("✅ Excellent data coverage (65%+)")
    print("\nHybrid LLM approach is working perfectly!")
elif len(result.source_contributions) == 1:
    print("PARTIAL SUCCESS - Single Source Pricing")
    print("=" * 80)
    print(f"\n✅ Used 1 data source: {result.source_contributions[0].source_name}")
    print(f"⚠️  Could benefit from additional data sources")
else:
    print("NO DATA SOURCES FOUND")
    print("=" * 80)
    print("\n⚠️  Using fallback calculation")

session.close()
