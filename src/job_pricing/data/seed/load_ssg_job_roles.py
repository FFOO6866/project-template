"""
Simple SSG Job Roles Loader

Loads SSG Skills Framework data from Excel directly into the database.
Generates job_role_codes from sector/track/job role names.

Usage:
    python -m data.seed.load_ssg_job_roles
"""

import sys
import hashlib
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from sqlalchemy.exc import IntegrityError

from src.job_pricing.core.database import get_session
from src.job_pricing.models.ssg import SSGSkillsFramework


def generate_job_role_code(sector: str, track: str, job_role: str) -> str:
    """
    Generate a unique job role code from sector, track, and job role.

    Args:
        sector: Sector name
        track: Track name
        job_role: Job role title

    Returns:
        Unique job role code (e.g., "ACC-ASS-AUDIT-ASSOC-1a2b3c")
    """
    # Create a short hash of the full combination
    combined = f"{sector}_{track}_{job_role}".lower().replace(" ", "_")
    hash_suffix = hashlib.md5(combined.encode()).hexdigest()[:6]

    # Create acronym from first letters
    sector_code = "".join([word[0].upper() for word in sector.split()[:3]])
    track_code = "".join([word[0].upper() for word in track.split()[:3]])
    role_code = "".join([word[0].upper() for word in job_role.split()[:3]])

    # Combine: SECTOR-TRACK-ROLE-HASH
    return f"{sector_code}-{track_code}-{role_code}-{hash_suffix}"


def load_job_roles_from_excel(file_path: str, session) -> tuple:
    """
    Load job roles from SSG Excel file.

    Args:
        file_path: Path to Excel file
        session: Database session

    Returns:
        Tuple of (loaded_count, skipped_count, error_count)
    """
    print(f"Reading Excel file: {file_path}")

    # Read Job Role_Description sheet
    df_descriptions = pd.read_excel(file_path, sheet_name="Job Role_Description")

    # Read Job Role_CWF_KT sheet for critical work functions
    df_cwf = pd.read_excel(file_path, sheet_name="Job Role_CWF_KT")

    # Group CWF by job role to get all critical work functions
    cwf_by_role = {}
    for _, row in df_cwf.iterrows():
        key = (row['Sector'], row['Track'], row['Job Role'])
        if key not in cwf_by_role:
            cwf_by_role[key] = []
        if pd.notna(row['Critical Work Function']):
            cwf = row['Critical Work Function']
            if cwf not in cwf_by_role[key]:
                cwf_by_role[key].append(cwf)

    print(f"Found {len(df_descriptions)} job roles in Excel")

    loaded = 0
    skipped = 0
    errors = 0

    for idx, row in df_descriptions.iterrows():
        try:
            # Extract data
            sector = row['Sector']
            track = row['Track']
            job_role_title = row['Job Role']
            job_role_description = row.get('Job Role Description')

            # Skip if essential fields are missing
            if pd.isna(sector) or pd.isna(track) or pd.isna(job_role_title):
                print(f"  ⊗ Skipped row {idx+1}: Missing essential fields")
                skipped += 1
                continue

            # Generate job role code
            job_role_code = generate_job_role_code(sector, track, job_role_title)

            # Get critical work functions
            key = (sector, track, job_role_title)
            cwf_list = cwf_by_role.get(key, [])
            critical_work_function = "; ".join(cwf_list) if cwf_list else None

            # Check if already exists
            existing = session.query(SSGSkillsFramework).filter_by(
                job_role_code=job_role_code
            ).first()

            if existing:
                print(f"  ⊗ Skipped: {job_role_title} (code: {job_role_code}) - already exists")
                skipped += 1
                continue

            # Create model instance
            job_role = SSGSkillsFramework(
                sector=str(sector).strip(),
                track=str(track).strip(),
                job_role_code=job_role_code,
                job_role_title=str(job_role_title).strip(),
                job_role_description=str(job_role_description).strip() if pd.notna(job_role_description) else None,
                critical_work_function=critical_work_function,
                career_level=None  # Not available in this dataset
            )

            session.add(job_role)

            print(f"  + Added: {job_role_title} (code: {job_role_code})")
            loaded += 1

            # Commit in batches of 50
            if loaded % 50 == 0:
                session.commit()
                print(f"  → Committed batch ({loaded} records so far)")

        except IntegrityError as e:
            session.rollback()
            print(f"  ✗ Integrity error on row {idx+1}: {e}")
            errors += 1

        except Exception as e:
            session.rollback()
            print(f"  ✗ Error on row {idx+1}: {e}")
            errors += 1

    # Final commit
    session.commit()

    return loaded, skipped, errors


def main():
    """Main entry point"""
    print("=" * 70)
    print("SSG JOB ROLES LOADER")
    print("=" * 70)

    excel_file = "data/SSG/jobsandskills-skillsfuture-skills-framework-dataset.xlsx"

    session = get_session()

    try:
        print(f"\n1. Loading Job Roles from Excel...")
        loaded, skipped, errors = load_job_roles_from_excel(excel_file, session)

        print("\n" + "=" * 70)
        print("LOAD SUMMARY")
        print("=" * 70)
        print(f"Loaded:   {loaded}")
        print(f"Skipped:  {skipped}")
        print(f"Errors:   {errors}")
        print(f"Total:    {loaded + skipped + errors}")
        print("=" * 70)

        if errors > 0:
            print(f"\n⚠ Warning: {errors} errors occurred during loading")

        if loaded > 0:
            print(f"\n✓ Successfully loaded {loaded} SSG job roles")

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()
