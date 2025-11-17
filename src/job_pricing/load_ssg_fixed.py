"""Fixed script to load SSG Skills Framework data."""
import pandas as pd
import hashlib
from src.job_pricing.models.ssg import SSGSkillsFramework, SSGTSC
from src.job_pricing.utils.database import get_db_context

def clean_string(value):
    """Clean string values from Excel."""
    if pd.isna(value):
        return None
    return str(value).strip() if value else None

def generate_short_code(sector, track, idx):
    """Generate a short unique code from sector, track, and index."""
    # Use first 3 letters of sector + first 3 of track + index
    sector_short = sector[:3].upper() if sector else "UNK"
    track_short = track[:3].upper() if track else "UNK"
    return f"{sector_short}-{track_short}-{idx:04d}"

def load_ssg_job_roles():
    """Load SSG job roles."""
    print("\n=== Loading SSG Job Roles ===")

    df = pd.read_excel('data/SSG/jobsandskills-skillsfuture-skills-framework-dataset.xlsx',
                       sheet_name='Job Role_Description')

    print(f"Found {len(df)} job roles")

    with get_db_context() as session:
        # Check how many already loaded
        existing = session.query(SSGSkillsFramework).count()
        print(f"Already loaded: {existing} job roles")

        if existing >= len(df) * 0.7:  # If 70%+ already loaded
            print("Majority already loaded, skipping...")
            return existing, 0

        # Clear existing to reload all
        session.query(SSGSkillsFramework).delete()
        session.commit()

        loaded = 0
        errors = 0

        for idx, row in df.iterrows():
            try:
                code = generate_short_code(
                    clean_string(row['Sector']),
                    clean_string(row['Track']),
                    idx
                )

                job_role = SSGSkillsFramework(
                    sector=clean_string(row['Sector']),
                    track=clean_string(row['Track']),
                    job_role_code=code,
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
                if errors <= 3:
                    print(f"Error at row {idx}: {e}")
                continue

        print(f"Complete! Loaded {loaded} job roles with {errors} errors\n")
        return loaded, errors

def load_ssg_tsc():
    """Load SSG TSC."""
    print("\n=== Loading SSG TSC ===")

    df = pd.read_excel('data/SSG/jobsandskills-skillsfuture-skills-framework-dataset.xlsx',
                       sheet_name='TSC_CCS_Key')

    print(f"Found {len(df)} TSC records")

    with get_db_context() as session:
        # Check existing
        existing = session.query(SSGTSC).count()
        print(f"Already loaded: {existing} TSC records")

        if existing >= len(df) * 0.7:
            print("Majority already loaded, skipping...")
            return existing, 0

        # Clear to reload
        session.query(SSGTSC).delete()
        session.commit()

        loaded = 0
        errors = 0

        for idx, row in df.iterrows():
            try:
                tsc = SSGTSC(
                    tsc_code=clean_string(row['TSC Code']),
                    tsc_title=clean_string(row['TSC_CCS Title']),
                    tsc_description=clean_string(row['TSC_CCS Description']),
                    skill_category=clean_string(row['TSC_CCS Category']),
                )

                session.add(tsc)
                session.commit()
                loaded += 1

                if (idx + 1) % 2000 == 0:
                    print(f"Loaded {idx + 1}/{len(df)} TSC records...")

            except Exception as e:
                session.rollback()
                errors += 1
                if errors <= 3:
                    print(f"Error at row {idx}: {e}")
                continue

        print(f"Complete! Loaded {loaded} TSC records with {errors} errors\n")
        return loaded, errors

def main():
    """Load all SSG data."""
    print("=" * 60)
    print("LOADING SSG SKILLS FRAMEWORK DATA (FIXED)")
    print("=" * 60)

    roles_loaded, roles_errors = load_ssg_job_roles()
    tsc_loaded, tsc_errors = load_ssg_tsc()

    print("=" * 60)
    print("SSG DATA LOADING COMPLETE")
    print("=" * 60)
    print(f"Job Roles: {roles_loaded} loaded, {roles_errors} errors")
    print(f"TSC: {tsc_loaded} loaded, {tsc_errors} errors")
    print(f"Total: {roles_loaded + tsc_loaded} records loaded")
    print("=" * 60)

if __name__ == '__main__':
    main()
