"""Simple script to load Mercer Job Library data into database."""
import pandas as pd
import re
from sqlalchemy.orm import Session
from src.job_pricing.models.mercer import MercerJobLibrary
from src.job_pricing.utils.database import get_db_context

def extract_career_level_code(level_title):
    """Extract short code from career level title like 'Executive Tier 3 (ET3)' -> 'ET3'."""
    if pd.isna(level_title):
        return None
    # Try to extract code from parentheses
    match = re.search(r'\(([^)]+)\)', level_title)
    if match:
        return match.group(1)
    # If no parentheses, return as is (might already be short code)
    return level_title

def load_mercer_jobs():
    """Load Mercer jobs from Excel into database."""
    print("Loading Mercer Job Library...")

    # Read Excel with correct sheet and header
    df = pd.read_excel('data/Mercer/Mercer Job Library.xlsx',
                       sheet_name='Mercer Combined Jobs and Jobs',
                       header=10)

    print(f"Found {len(df)} jobs in Excel file")

    # Map column names to model fields
    column_mapping = {
        'Job Code': 'job_code',
        'Job Title': 'job_title',
        'Job Description': 'job_description',
        'Family Code': 'family',
        'Family Title': 'family_title',
        'Sub-family Code': 'subfamily',
        'Sub-family Title': 'subfamily_title',
        'Career Level Title': 'career_level',
        'Specialization Code': 'specialization_code',
        'Specialization Title': 'specialization_title',
        'Career Stream Title': 'career_stream',
    }

    with get_db_context() as session:
        loaded = 0
        errors = 0

        for idx, row in df.iterrows():
            try:
                # Create job object
                job = MercerJobLibrary(
                    job_code=row['Job Code'],
                    job_title=row['Job Title'],
                    job_description=row['Job Description'] if pd.notna(row['Job Description']) else None,
                    family=row['Family Code'] if pd.notna(row['Family Code']) else None,
                    subfamily=str(int(row['Sub-family Code'])) if pd.notna(row['Sub-family Code']) else None,
                    career_level=extract_career_level_code(row['Career Level Title']),
                )

                session.add(job)
                session.commit()  # Commit immediately

                # Progress message every 50 jobs
                if (idx + 1) % 50 == 0:
                    print(f"Loaded {idx + 1}/{len(df)} jobs...")

            except Exception as e:
                session.rollback()
                errors += 1
                print(f"Error loading job {row.get('Job Code', 'unknown')}: {e}")
                continue

        loaded = len(df) - errors

    print(f"\nComplete! Loaded {loaded} jobs with {errors} errors")
    return loaded, errors

if __name__ == '__main__':
    load_mercer_jobs()
