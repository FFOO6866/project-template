"""
SSG TSC (Technical Skills & Competencies) Loader

Loads SSG TSC data from Excel into the database.

Usage:
    python -m data.seed.load_ssg_tsc
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from sqlalchemy.exc import IntegrityError

from src.job_pricing.core.database import get_session
from src.job_pricing.models.ssg import SSGTSC


def load_tsc_from_excel(file_path: str, session) -> tuple:
    """
    Load TSC data from SSG Excel file.

    Args:
        file_path: Path to Excel file
        session: Database session

    Returns:
        Tuple of (loaded_count, skipped_count, error_count)
    """
    print(f"Reading Excel file: {file_path}")

    # Read TSC_CCS_Key sheet
    df_tsc = pd.read_excel(file_path, sheet_name="TSC_CCS_Key")

    print(f"Found {len(df_tsc)} TSC records in Excel")

    loaded = 0
    skipped = 0
    errors = 0

    for idx, row in df_tsc.iterrows():
        try:
            # Extract data
            tsc_code = row['TSC Code']
            tsc_title = row['TSC_CCS Title']
            tsc_description = row.get('TSC_CCS Description')
            skill_category = row.get('TSC_CCS Category')

            # Skip if essential fields are missing
            if pd.isna(tsc_code) or pd.isna(tsc_title):
                print(f"  ⊗ Skipped row {idx+1}: Missing tsc_code or tsc_title")
                skipped += 1
                continue

            # Check if already exists
            existing = session.query(SSGTSC).filter_by(
                tsc_code=str(tsc_code).strip()
            ).first()

            if existing:
                skipped += 1
                if skipped % 1000 == 0:
                    print(f"  ... {skipped} skipped so far (already exist)")
                continue

            # Create model instance
            tsc = SSGTSC(
                tsc_code=str(tsc_code).strip(),
                tsc_title=str(tsc_title).strip(),
                tsc_description=str(tsc_description).strip() if pd.notna(tsc_description) else None,
                skill_category=str(skill_category).strip() if pd.notna(skill_category) else None,
                proficiency_level=None  # Not available in this sheet
            )

            session.add(tsc)
            loaded += 1

            if loaded % 500 == 0:
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
    print("SSG TSC (TECHNICAL SKILLS & COMPETENCIES) LOADER")
    print("=" * 70)

    excel_file = "data/SSG/jobsandskills-skillsfuture-skills-framework-dataset.xlsx"

    session = get_session()

    try:
        print(f"\n1. Loading TSC data from Excel...")
        loaded, skipped, errors = load_tsc_from_excel(excel_file, session)

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
            print(f"\n✓ Successfully loaded {loaded} SSG TSC records")

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()
