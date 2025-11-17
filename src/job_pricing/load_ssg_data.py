"""Simple script to load SSG Skills Framework data into database."""
import pandas as pd
import re
from sqlalchemy.orm import Session
from src.job_pricing.models.ssg import SSGSkillsFramework, SSGTSC, SSGJobRoleTSCMapping
from src.job_pricing.utils.database import get_db_context

def clean_string(value):
    """Clean string values from Excel."""
    if pd.isna(value):
        return None
    return str(value).strip() if value else None

def load_ssg_job_roles():
    """Load SSG job roles from Excel."""
    print("\n=== Loading SSG Job Roles ===")

    df = pd.read_excel('data/SSG/jobsandskills-skillsfuture-skills-framework-dataset.xlsx',
                       sheet_name='Job Role_Description')

    print(f"Found {len(df)} job roles in Excel")

    with get_db_context() as session:
        loaded = 0
        errors = 0

        for idx, row in df.iterrows():
            try:
                job_role = SSGSkillsFramework(
                    sector=clean_string(row['Sector']),
                    track=clean_string(row['Track']),
                    job_role_code=f"{clean_string(row['Sector'])}-{clean_string(row['Track'])}-{idx}",  # Generate code
                    job_role_title=clean_string(row['Job Role']),
                    job_role_description=clean_string(row['Job Role Description']),
                )

                session.add(job_role)
                session.commit()
                loaded += 1

                if (idx + 1) % 500 == 0:
                    print(f"Loaded {idx + 1}/{len(df)} job roles...")

            except Exception as e:
                session.rollback()
                errors += 1
                if errors <= 5:  # Only print first 5 errors
                    print(f"Error: {e}")
                continue

        print(f"Complete! Loaded {loaded} job roles with {errors} errors\n")
        return loaded, errors

def load_ssg_tsc():
    """Load SSG TSC (Technical Skills & Competencies) from Excel."""
    print("\n=== Loading SSG TSC ===")

    df = pd.read_excel('data/SSG/jobsandskills-skillsfuture-skills-framework-dataset.xlsx',
                       sheet_name='TSC_CCS_Key')

    print(f"Found {len(df)} TSC records in Excel")

    with get_db_context() as session:
        loaded = 0
        errors = 0

        for idx, row in df.iterrows():
            try:
                tsc = SSGTSC(
                    tsc_code=clean_string(row['TSC Code']),
                    sector=clean_string(row['Sector']),
                    tsc_category=clean_string(row['TSC_CCS Category']),
                    tsc_title=clean_string(row['TSC_CCS Title']),
                    tsc_description=clean_string(row['TSC_CCS Description']),
                )

                session.add(tsc)
                session.commit()
                loaded += 1

                if (idx + 1) % 2000 == 0:
                    print(f"Loaded {idx + 1}/{len(df)} TSC records...")

            except Exception as e:
                session.rollback()
                errors += 1
                if errors <= 5:
                    print(f"Error: {e}")
                continue

        print(f"Complete! Loaded {loaded} TSC records with {errors} errors\n")
        return loaded, errors

def load_all_ssg_data():
    """Load all SSG data."""
    print("=" * 60)
    print("LOADING SSG SKILLS FRAMEWORK DATA")
    print("=" * 60)

    # Load job roles first
    roles_loaded, roles_errors = load_ssg_job_roles()

    # Load TSC
    tsc_loaded, tsc_errors = load_ssg_tsc()

    print("=" * 60)
    print("SSG DATA LOADING COMPLETE")
    print("=" * 60)
    print(f"Job Roles: {roles_loaded} loaded, {roles_errors} errors")
    print(f"TSC: {tsc_loaded} loaded, {tsc_errors} errors")
    print(f"Total: {roles_loaded + tsc_loaded} records loaded")
    print("=" * 60)

if __name__ == '__main__':
    load_all_ssg_data()
