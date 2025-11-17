"""Check market data availability for job codes."""
from src.job_pricing.core.database import get_session
from src.job_pricing.models import MercerMarketData, MercerJobLibrary

session = get_session()

job_code = 'HRM.09.002.ET3'
print(f'Checking job code: {job_code}')

# Check if job exists
job = session.query(MercerJobLibrary).filter_by(job_code=job_code).first()
if job:
    print(f'Job found: {job.job_title}')
else:
    print('Job not found in library')

# Check for market data
market_data = session.query(MercerMarketData).filter(
    MercerMarketData.job_code == job_code,
    MercerMarketData.country_code == 'SG'
).all()

if market_data:
    print(f'\nMarket data found: {len(market_data)} records')
    for md in market_data:
        print(f'  P50: ${md.p50:,.0f}')
else:
    print('\nNo Singapore market data for this job code')

# Check what job codes DO have market data
print('\nJob codes with Singapore market data:')
jobs_with_data = session.query(MercerMarketData.job_code).filter(
    MercerMarketData.country_code == 'SG'
).distinct().all()

print(f'Total: {len(jobs_with_data)} unique job codes with SG data')
print('\nSample (first 10):')
for (jc,) in jobs_with_data[:10]:
    job_info = session.query(MercerJobLibrary).filter_by(job_code=jc).first()
    if job_info:
        print(f'  {jc}: {job_info.job_title}')

session.close()
