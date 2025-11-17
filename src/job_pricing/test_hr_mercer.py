"""Test Mercer integration with HR role that has market data."""
import logging
from src.job_pricing.core.database import get_session
from src.job_pricing.models import JobPricingRequest
from src.job_pricing.services.pricing_calculation_service_v3 import PricingCalculationServiceV3

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

session = get_session()

# Test with HR role that matches Mercer data
request = JobPricingRequest(
    job_title='HR Business Partner',
    job_description='Senior HR professional partnering with business leaders on talent strategy',
    location_text='Singapore',
    requested_by='test_user',
    requestor_email='test@example.com',
    status='pending',
    urgency='normal'
)
session.add(request)
session.flush()

print('=' * 80)
print('MULTI-SOURCE PRICING TEST: HR Business Partner')
print('=' * 80)

pricing_service = PricingCalculationServiceV3(session)
result = pricing_service.calculate_pricing(request)

print(f'\nRESULTS:')
print(f'  Target: SGD ${result.target_salary:,.0f}')
print(f'  Range: SGD ${result.recommended_min:,.0f} - ${result.recommended_max:,.0f}')
print(f'  Confidence: {result.confidence_score:.0f}/100')

print(f'\nPERCENTILES:')
print(f'  P10: ${result.p10:,.0f}')
print(f'  P25: ${result.p25:,.0f}')
print(f'  P50: ${result.p50:,.0f}')
print(f'  P75: ${result.p75:,.0f}')
print(f'  P90: ${result.p90:,.0f}')

print(f'\nDATA SOURCES ({len(result.source_contributions)}):')
for c in result.source_contributions:
    print(f'  - {c.source_name:20s} | Weight: {c.weight:>6.2%} | Sample: {c.sample_size:>3d} | Age: {c.recency_days:>3d} days')
    if c.p50:
        print(f'    P50 from this source: ${c.p50:,.0f}')

total_weight = sum(c.weight for c in result.source_contributions)
print(f'\nTOTAL COVERAGE: {total_weight:.0%}')

sources_found = [c.source_name for c in result.source_contributions]
if 'mercer' in sources_found:
    print('\nSUCCESS: Mercer data integrated!')
    mercer_contrib = [c for c in result.source_contributions if c.source_name == 'mercer'][0]
    print(f'  Mercer P50: ${mercer_contrib.p50:,.0f}')
    print(f'  Sample size: {mercer_contrib.sample_size}')
    print(f'  Survey age: {mercer_contrib.recency_days} days')
else:
    print('\nINFO: No Mercer match found for this job title')

if 'my_careers_future' in sources_found:
    print('\nMCF data also found')

session.close()

print('\n' + '=' * 80)
if len(result.source_contributions) >= 2:
    print('MULTI-SOURCE PRICING SUCCESSFUL!')
else:
    print('Single source pricing (Mercer or MCF may not have data for this role)')
print('=' * 80)
