"""
Mercer Market Data Loader

Loads salary data from 'data/Mercer/Market Data.xlsx' into mercer_market_data table.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import pandas as pd
from datetime import datetime, date
from job_pricing.core.database import get_session
from job_pricing.models import MercerMarketData, MercerJobLibrary

def normalize_currency(currency_name):
    """Convert currency name to 3-letter code."""
    if pd.isna(currency_name):
        return 'SGD'

    currency_str = str(currency_name).strip()

    # Currency mapping
    currency_map = {
        'Singapore Dollar': 'SGD',
        'US Dollar': 'USD',
        'United States Dollar': 'USD',
        'Euro': 'EUR',
        'British Pound': 'GBP',
        'Japanese Yen': 'JPY',
        'Australian Dollar': 'AUD',
        'Canadian Dollar': 'CAD',
        'Hong Kong Dollar': 'HKD',
        'Malaysian Ringgit': 'MYR',
        'Thai Baht': 'THB',
    }

    # Check map first
    if currency_str in currency_map:
        return currency_map[currency_str]

    # If already 3 letters, use as-is
    if len(currency_str) == 3 and currency_str.isupper():
        return currency_str

    # Default to first 3 letters uppercase
    return currency_str[:3].upper()

def load_market_data():
    """Load Mercer market data from Excel file."""

    session = get_session()

    try:
        # Read Excel file
        excel_path = Path(__file__).parent.parent / 'Mercer' / 'Market Data.xlsx'
        print(f"Loading market data from: {excel_path}")

        df = pd.read_excel(excel_path)
        print(f"Loaded {len(df)} rows from Excel")

        # Skip header row (row 0 has column descriptions)
        df = df[1:]
        print(f"After skipping header: {len(df)} rows")

        # Clean up: remove rows with no job code
        df = df[df['MjlCode'].notna()]
        print(f"After filtering for valid job codes: {len(df)} rows")

        # Process each row
        loaded_count = 0
        skipped_count = 0
        skipped_no_job = 0
        skipped_no_p50 = 0

        for idx, row in df.iterrows():
            try:
                job_code = str(row['MjlCode']).strip()

                # Check if job code exists in library (foreign key constraint)
                job_exists = session.query(MercerJobLibrary).filter(
                    MercerJobLibrary.job_code == job_code
                ).first()

                if not job_exists:
                    skipped_no_job += 1
                    continue

                # Extract salary percentiles (using BaseAnnual for base salary)
                p10 = pd.to_numeric(row.get('BaseAnnual_Perc10_IW'), errors='coerce')
                p25 = pd.to_numeric(row.get('BaseAnnual_Perc25_IW'), errors='coerce')
                p50 = pd.to_numeric(row.get('BaseAnnual_Median_IW'), errors='coerce')
                p75 = pd.to_numeric(row.get('BaseAnnual_Perc75_IW'), errors='coerce')
                p90 = pd.to_numeric(row.get('BaseAnnual_Perc90_IW'), errors='coerce')

                # Skip if no salary data
                if pd.isna(p50):
                    skipped_no_p50 += 1
                    continue

                # DATA VALIDATION: Ensure percentiles are in correct order
                percentiles = [
                    ('P10', p10), ('P25', p25), ('P50', p50), ('P75', p75), ('P90', p90)
                ]
                valid_percentiles = [(name, val) for name, val in percentiles if not pd.isna(val)]

                if len(valid_percentiles) >= 2:
                    # Check if percentiles are monotonically increasing
                    for i in range(len(valid_percentiles) - 1):
                        if valid_percentiles[i][1] > valid_percentiles[i+1][1]:
                            print(f"WARNING: Invalid percentile order for {job_code}: {valid_percentiles[i][0]}={valid_percentiles[i][1]} > {valid_percentiles[i+1][0]}={valid_percentiles[i+1][1]}")
                            # Still load but log the warning
                            break

                # Get survey date - REQUIRED, no default
                survey_date = row.get('DataEffectiveDate')
                if isinstance(survey_date, str):
                    try:
                        survey_date = datetime.strptime(survey_date, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"SKIPPING {job_code}: Invalid date format '{survey_date}'")
                        skipped_count += 1
                        continue
                elif isinstance(survey_date, datetime):
                    survey_date = survey_date.date()
                elif pd.isna(survey_date):
                    print(f"SKIPPING {job_code}: Missing survey date (DataEffectiveDate is required)")
                    skipped_count += 1
                    continue
                else:
                    print(f"SKIPPING {job_code}: Invalid survey date type {type(survey_date)}")
                    skipped_count += 1
                    continue

                # Get sample size - REQUIRED, no default
                sample_size = pd.to_numeric(row.get('BaseAnnual_NumObs'), errors='coerce')
                if pd.isna(sample_size):
                    print(f"SKIPPING {job_code}: Missing sample size (BaseAnnual_NumObs is required)")
                    skipped_count += 1
                    continue
                sample_size = int(sample_size)

                # Create or update market data record
                # Match on unique constraint: job_code + country_code + benchmark_cut + survey_date
                existing = session.query(MercerMarketData).filter(
                    MercerMarketData.job_code == job_code,
                    MercerMarketData.country_code == 'SG',
                    MercerMarketData.benchmark_cut == 'by_job',
                    MercerMarketData.survey_date == survey_date
                ).first()

                if existing:
                    # Update existing record
                    existing.p10 = p10 if not pd.isna(p10) else None
                    existing.p25 = p25 if not pd.isna(p25) else None
                    existing.p50 = p50 if not pd.isna(p50) else None
                    existing.p75 = p75 if not pd.isna(p75) else None
                    existing.p90 = p90 if not pd.isna(p90) else None
                    existing.survey_date = survey_date
                    existing.sample_size = sample_size
                    existing.currency = normalize_currency(row.get('CurrencyName', 'SGD'))
                    existing.benchmark_cut = 'by_job'
                else:
                    # Create new record
                    market_data = MercerMarketData(
                        job_code=job_code,
                        country_code='SG',
                        benchmark_cut='by_job',
                        p10=p10 if not pd.isna(p10) else None,
                        p25=p25 if not pd.isna(p25) else None,
                        p50=p50 if not pd.isna(p50) else None,
                        p75=p75 if not pd.isna(p75) else None,
                        p90=p90 if not pd.isna(p90) else None,
                        survey_date=survey_date,
                        sample_size=sample_size,
                        currency=normalize_currency(row.get('CurrencyName', 'SGD')),
                        survey_name='2024 Singapore Total Remuneration Survey'
                    )
                    session.add(market_data)

                loaded_count += 1

                if loaded_count % 50 == 0:
                    print(f"Processed {loaded_count} records...")
                    session.flush()

            except Exception as e:
                print(f"Error processing row {idx}: {e}")
                continue

        # Commit all changes
        session.commit()

        print()
        print("=" * 80)
        print("MARKET DATA LOAD COMPLETE")
        print("=" * 80)
        print(f"Successfully loaded: {loaded_count} records")
        print(f"Skipped (job not in library): {skipped_no_job} records")
        print(f"Skipped (no P50 data): {skipped_no_p50} records")
        print(f"Total skipped: {skipped_no_job + skipped_no_p50} records")
        print(f"Total in database: {session.query(MercerMarketData).count()} records")
        print("=" * 80)

        return loaded_count

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return 0
    finally:
        session.close()

if __name__ == '__main__':
    load_market_data()
