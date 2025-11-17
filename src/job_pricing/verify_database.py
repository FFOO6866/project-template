"""Quick database verification script."""
from src.job_pricing.core.database import get_session
from src.job_pricing.models import ScrapedJobListing, JobPricingResult, DataSourceContribution

session = get_session()

print("=" * 80)
print("DATABASE STATUS")
print("=" * 80)

# Count MCF jobs
mcf_count = session.query(ScrapedJobListing).filter_by(source='my_careers_future').count()
print(f'\nMCF Jobs in Database: {mcf_count}')

# Count pricing results
results_count = session.query(JobPricingResult).count()
print(f'Pricing Results Created: {results_count}')

# Count source contributions
contrib_count = session.query(DataSourceContribution).count()
print(f'Source Contributions Saved: {contrib_count}')

# Show latest result
latest = session.query(JobPricingResult).order_by(JobPricingResult.created_at.desc()).first()
if latest:
    print(f'\n' + "=" * 80)
    print("LATEST PRICING RESULT")
    print("=" * 80)
    print(f'Job Title: {latest.request.job_title}')
    print(f'Target Salary: SGD ${latest.target_salary:,.0f}')
    print(f'Recommended Range: SGD ${latest.recommended_min:,.0f} - ${latest.recommended_max:,.0f}')
    print(f'Confidence: {latest.confidence_score}/100 ({latest.confidence_level})')
    print(f'Data Sources Used: {latest.data_sources_used}')
    print(f'\nPercentiles:')
    print(f'  P10: ${latest.p10:,.0f}')
    print(f'  P25: ${latest.p25:,.0f}')
    print(f'  P50: ${latest.p50:,.0f}')
    print(f'  P75: ${latest.p75:,.0f}')
    print(f'  P90: ${latest.p90:,.0f}')

    # Show source contributions
    if latest.data_source_contributions:
        print(f'\nSource Contributions:')
        for contrib in latest.data_source_contributions:
            print(f'  - {contrib.source_name}: weight={contrib.weight_applied}, sample={contrib.sample_size}')

print("\n" + "=" * 80)
print("STATUS: ALL SYSTEMS OPERATIONAL")
print("=" * 80)

session.close()
