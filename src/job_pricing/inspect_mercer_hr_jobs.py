"""Inspect what HR jobs exist in Mercer library."""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

os.environ['DATABASE_URL'] = 'postgresql://job_pricing_user:change_this_secure_password_123@localhost:5432/job_pricing_db'

from job_pricing.core.database import get_session
from job_pricing.models import MercerJobLibrary, MercerMarketData

session = get_session()

print("=" * 80)
print("MERCER HR JOBS INVENTORY")
print("=" * 80)
print()

# Get all HR jobs (HRM code prefix = Human Resources Management)
hr_jobs = session.query(MercerJobLibrary).filter(
    MercerJobLibrary.job_code.like('HRM%')
).all()

print(f"Total HR Jobs in Library: {len(hr_jobs)}")
print()

# Show first 20 HR jobs
print("HR Jobs (first 20):")
print("=" * 80)
for i, job in enumerate(hr_jobs[:20], 1):
    # Check if this job has market data
    has_data = session.query(MercerMarketData).filter(
        MercerMarketData.job_code == job.job_code,
        MercerMarketData.country_code == 'SG',
        MercerMarketData.p50.isnot(None)
    ).first() is not None

    data_marker = "[HAS DATA]" if has_data else "[NO DATA]"

    print(f"{i}. {job.job_code}: {job.job_title}")
    print(f"   Subfamily: {job.subfamily if hasattr(job, 'subfamily') else 'N/A'}")
    print(f"   Level: {job.career_level if hasattr(job, 'career_level') else 'N/A'}")
    print(f"   {data_marker}")
    print()

print("=" * 80)

# Count jobs with data
hr_with_data = 0
hr_codes = [j.job_code for j in hr_jobs]
for code in hr_codes:
    has_data = session.query(MercerMarketData).filter(
        MercerMarketData.job_code == code,
        MercerMarketData.country_code == 'SG',
        MercerMarketData.p50.isnot(None)
    ).first()
    if has_data:
        hr_with_data += 1

print(f"HR Jobs with SG Market Data: {hr_with_data}/{len(hr_jobs)} ({hr_with_data/len(hr_jobs)*100:.1f}%)")
print()

# Show jobs with data
print("=" * 80)
print("HR JOBS WITH MARKET DATA:")
print("=" * 80)
jobs_with_data = []
for job in hr_jobs:
    market_data = session.query(MercerMarketData).filter(
        MercerMarketData.job_code == job.job_code,
        MercerMarketData.country_code == 'SG',
        MercerMarketData.p50.isnot(None)
    ).first()
    if market_data:
        jobs_with_data.append((job, market_data))

for job, market_data in jobs_with_data[:10]:
    print(f"{job.job_code}: {job.job_title}")
    print(f"  Level: {job.career_level}")
    print(f"  P50: SGD ${market_data.p50:,.0f}")
    print()

session.close()
