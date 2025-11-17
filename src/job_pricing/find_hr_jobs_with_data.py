"""Find HR Manager jobs with market data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from job_pricing.core.database import get_session
from job_pricing.models import MercerJobLibrary, MercerMarketData

session = get_session()

# Find all HRM jobs with market data
jobs_with_data = session.query(MercerJobLibrary, MercerMarketData).join(
    MercerMarketData, MercerJobLibrary.job_code == MercerMarketData.job_code
).filter(
    MercerJobLibrary.family == 'HRM',
    MercerMarketData.country_code == 'SG'
).all()

print(f'Found {len(jobs_with_data)} HRM jobs with SG market data:')
print()
for job, market in jobs_with_data:
    print(f'Code: {job.job_code}')
    print(f'Title: {job.job_title}')
    print(f'Level: {job.career_level}')
    print(f'P50: SGD ${market.p50:,.0f}' if market.p50 else 'P50: N/A')
    print('-' * 60)

session.close()
