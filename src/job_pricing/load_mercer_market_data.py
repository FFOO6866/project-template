"""Load Mercer Market Data (Salary Benchmarks) into database."""
import pandas as pd
from datetime import datetime
from src.job_pricing.models.mercer import MercerMarketData
from src.job_pricing.utils.database import get_db_context


def load_mercer_market_data():
    """Load Mercer salary benchmark data from Market Data.xlsx."""
    print("=" * 60)
    print("LOADING MERCER MARKET DATA (SALARY BENCHMARKS)")
    print("=" * 60)

    # Read Excel file
    df = pd.read_excel(
        'data/Mercer/Market Data.xlsx',
        sheet_name='Job Summary',
        header=1
    )

    print(f"\nFound {len(df)} market data records")

    # Get column names (with spaces)
    job_code_col = [c for c in df.columns if 'Job Code' in c][0]
    p25_col = [c for c in df.columns if 'Base Salary' in c and 'Perc25' in c][0]
    p50_col = [c for c in df.columns if 'Base Salary' in c and 'Median' in c][0]
    p75_col = [c for c in df.columns if 'Base Salary' in c and 'Perc75' in c][0]
    mean_col = [c for c in df.columns if 'Base Salary' in c and 'Mean' in c][0]
    currency_col = [c for c in df.columns if 'Currency' in c][0]
    date_col = [c for c in df.columns if 'Effective Date' in c][0]
    num_orgs_col = [c for c in df.columns if 'Base Salary' in c and 'NumOrgs' in c][0]

    # Filter to records with salary data
    df_with_salary = df[df[p50_col].notna()].copy()
    print(f"Records with salary data: {len(df_with_salary)}")

    with get_db_context() as session:
        # Get existing job library codes to only load matching market data
        from src.job_pricing.models.mercer import MercerJobLibrary
        lib_codes = set([j.job_code for j in session.query(MercerJobLibrary.job_code).all()])
        print(f"Job library has {len(lib_codes)} codes")

        # Filter market data to only matching codes
        df_with_salary = df_with_salary[df_with_salary[job_code_col].isin(lib_codes)].copy()
        print(f"Market data with matching job codes: {len(df_with_salary)}")

    with get_db_context() as session:
        # Check existing
        existing = session.query(MercerMarketData).count()
        print(f"Already loaded: {existing} records")

        if existing >= len(df_with_salary) * 0.7:
            print("Majority already loaded, skipping...")
            return existing, 0

        # Clear existing to reload
        session.query(MercerMarketData).delete()
        session.commit()

        loaded = 0
        errors = 0

        for idx, row in df_with_salary.iterrows():
            try:
                # Parse date
                date_str = row[date_col]
                if pd.notna(date_str):
                    # Convert to datetime if it's a string
                    if isinstance(date_str, str):
                        # Try different date formats
                        try:
                            survey_date = datetime.strptime(date_str, '%d %B %Y').date()
                        except ValueError:
                            try:
                                survey_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                            except ValueError:
                                survey_date = datetime(2024, 1, 1).date()
                    else:
                        survey_date = date_str.date() if hasattr(date_str, 'date') else date_str
                else:
                    survey_date = datetime(2024, 1, 1).date()  # Default to 2024

                market_data = MercerMarketData(
                    job_code=str(row[job_code_col]).strip(),
                    country_code='SG',
                    location='Singapore',
                    currency='SGD',
                    benchmark_cut='by_job',

                    # Salary percentiles
                    p25=float(row[p25_col]) if pd.notna(row[p25_col]) else None,
                    p50=float(row[p50_col]) if pd.notna(row[p50_col]) else None,
                    p75=float(row[p75_col]) if pd.notna(row[p75_col]) else None,

                    # Sample size
                    sample_size=int(row[num_orgs_col]) if pd.notna(row[num_orgs_col]) else None,

                    # Survey metadata
                    survey_date=survey_date,
                    survey_name='2024 Singapore Total Remuneration Survey',
                    data_quality_flag='normal',
                )

                session.add(market_data)
                session.commit()
                loaded += 1

                if (loaded) % 100 == 0:
                    print(f"Loaded {loaded}/{len(df_with_salary)} records...")

            except Exception as e:
                session.rollback()
                errors += 1
                if errors <= 3:
                    print(f"Error at row {idx}: {e}")
                continue

        print(f"\nComplete! Loaded {loaded} market data records with {errors} errors")
        print("=" * 60)
        return loaded, errors


if __name__ == '__main__':
    load_mercer_market_data()
