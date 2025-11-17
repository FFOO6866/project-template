"""
SSG TSC (Technical Skills & Competencies) Data Loader

Loads SSG Technical Skills & Competencies data from Excel files into the database.
Includes validation, batch processing, and error logging.

Usage:
    from data.ingestion.ssg_tsc_loader import SSGTSCLoader

    loader = SSGTSCLoader(session)
    result = loader.load_from_excel("data/raw/ssg/ssg_tsc.xlsx")
    print(f"Loaded {result.statistics.successful}/{result.statistics.total_records} skills")

    # Or from command line:
    python -m data.ingestion.ssg_tsc_loader data/raw/ssg/ssg_tsc.xlsx
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.job_pricing.models.ssg import SSGTSC
from src.job_pricing.repositories.ssg_repository import SSGTSCRepository
from data.ingestion.base_loader import BaseDataLoader, LoadResult
from data.ingestion.excel_loader import ExcelLoader
from data.validation.ssg_validator import SSGTSCValidator
from src.job_pricing.core.database import get_session

logger = logging.getLogger(__name__)


class SSGTSCLoader(BaseDataLoader[SSGTSC], ExcelLoader):
    """
    Loader for SSG Technical Skills & Competencies data from Excel files.

    Expected Excel columns:
    - tsc_code (required): TSC code (e.g., "ICT-DIS-4010-1.1-A")
    - tsc_title (required): Skill title
    - skill_category (required): Skill category (e.g., "Data Management", "Programming")
    - proficiency_level (required): Proficiency level (1-6 or Basic/Intermediate/Advanced)
    - tsc_description (optional): Skill description

    Example:
        >>> loader = SSGTSCLoader(session)
        >>> result = loader.load_from_excel("ssg_tsc.xlsx")
        >>> print(f"Success rate: {result.statistics.success_rate:.1f}%")
    """

    def __init__(
        self,
        session: Session,
        batch_size: int = 100,
        continue_on_error: bool = True,
        show_progress: bool = True
    ):
        """
        Initialize SSG TSC loader.

        Args:
            session: SQLAlchemy database session
            batch_size: Number of records per batch (default: 100)
            continue_on_error: Continue loading on errors (default: True)
            show_progress: Show progress bar (default: True)
        """
        # Initialize repository
        repository = SSGTSCRepository(session)

        # Get existing TSC codes for duplicate detection
        existing_tsc = repository.get_all()
        existing_tsc_codes = {tsc.tsc_code for tsc in existing_tsc}

        # Initialize validator
        validator = SSGTSCValidator(existing_tsc_codes=existing_tsc_codes)

        # Initialize base loader
        super().__init__(
            session=session,
            repository=repository,
            validator=validator,
            batch_size=batch_size,
            continue_on_error=continue_on_error,
            show_progress=show_progress
        )

    def transform_record(self, raw_data: Dict[str, Any]) -> SSGTSC:
        """
        Transform Excel row data into SSGTSC model instance.

        Args:
            raw_data: Dictionary from Excel row

        Returns:
            SSGTSC model instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Handle proficiency_level: normalize to string
        proficiency_level = raw_data.get("proficiency_level")
        if proficiency_level is not None:
            proficiency_level = str(proficiency_level)

        tsc = SSGTSC(
            tsc_code=raw_data.get("tsc_code"),
            tsc_title=raw_data.get("tsc_title"),
            skill_category=raw_data.get("skill_category"),
            proficiency_level=proficiency_level,
            tsc_description=raw_data.get("tsc_description"),
        )

        return tsc

    def get_record_id(self, raw_data: Dict[str, Any]) -> str:
        """
        Extract record identifier from raw data.

        Args:
            raw_data: Dictionary from Excel row

        Returns:
            Record identifier (tsc_code)
        """
        return raw_data.get("tsc_code", "UNKNOWN")

    def load_from_excel(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        dry_run: bool = False
    ) -> LoadResult:
        """
        Load SSG TSC from Excel file.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name (default: first sheet)
            dry_run: If True, validate only without database writes

        Returns:
            LoadResult with statistics and error information

        Example:
            >>> loader = SSGTSCLoader(session)
            >>> result = loader.load_from_excel("ssg_tsc.xlsx")
            >>> if result.statistics.success_rate < 95:
            ...     print(f"Warning: Low success rate {result.statistics.success_rate:.1f}%")
        """
        logger.info(f"Loading SSG TSC from: {file_path}")

        # Read Excel file
        try:
            data = self.read_excel(file_path, sheet_name=sheet_name, clean_data=True)
            logger.info(f"Read {len(data)} records from Excel")
        except Exception as e:
            logger.error(f"Failed to read Excel file: {e}")
            raise

        # Validate required columns
        if data:
            required_columns = ["tsc_code", "tsc_title", "skill_category", "proficiency_level"]
            missing_columns = self.validate_columns(data[0], required_columns)

            if missing_columns:
                raise ValueError(
                    f"Missing required columns: {', '.join(missing_columns)}\n"
                    f"Expected columns: {', '.join(required_columns)}"
                )

        # Load data
        if dry_run:
            result = self.dry_run(data)
            logger.info(f"Dry run complete: {result.statistics.successful}/{result.statistics.total_records} valid")
        else:
            result = self.load_data(data)
            logger.info(
                f"Load complete: {result.statistics.successful}/{result.statistics.total_records} "
                f"successful ({result.statistics.success_rate:.1f}%)"
            )

        return result

    @staticmethod
    def validate_columns(sample_record: Dict[str, Any], required_columns: List[str]) -> List[str]:
        """
        Validate that sample record contains required columns.

        Args:
            sample_record: Sample record to check
            required_columns: List of required column names

        Returns:
            List of missing column names (empty if all present)
        """
        record_columns = set(sample_record.keys())
        missing = [col for col in required_columns if col not in record_columns]
        return missing


def main():
    """
    Command-line entry point for loading SSG TSC data.

    Usage:
        python -m data.ingestion.ssg_tsc_loader <excel_file> [--dry-run] [--batch-size 100]

    Examples:
        python -m data.ingestion.ssg_tsc_loader data/raw/ssg/ssg_tsc.xlsx
        python -m data.ingestion.ssg_tsc_loader data/raw/ssg/ssg_tsc.xlsx --dry-run
        python -m data.ingestion.ssg_tsc_loader data/raw/ssg/ssg_tsc.xlsx --batch-size 50
    """
    import argparse

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Load SSG TSC data from Excel file"
    )
    parser.add_argument(
        "excel_file",
        help="Path to Excel file containing SSG TSC data"
    )
    parser.add_argument(
        "--sheet",
        default=None,
        help="Sheet name (default: first sheet)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only, do not write to database"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of records per batch (default: 100)"
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Hide progress bar"
    )

    args = parser.parse_args()

    # Check file exists
    file_path = Path(args.excel_file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    # Get database session
    session = get_session()

    try:
        # Create loader
        loader = SSGTSCLoader(
            session=session,
            batch_size=args.batch_size,
            show_progress=not args.no_progress
        )

        # Load data
        result = loader.load_from_excel(
            file_path=str(file_path),
            sheet_name=args.sheet,
            dry_run=args.dry_run
        )

        # Print summary
        print("\n" + "=" * 70)
        print("SSG TSC LOAD SUMMARY")
        print("=" * 70)
        print(f"Total Records:    {result.statistics.total_records:,}")
        print(f"Successful:       {result.statistics.successful:,}")
        print(f"Failed:           {result.statistics.failed:,}")
        print(f"Skipped:          {result.statistics.skipped:,}")
        print(f"Duplicates:       {result.statistics.duplicates:,}")
        print(f"Success Rate:     {result.statistics.success_rate:.1f}%")
        print(f"Duration:         {result.statistics.duration_seconds:.1f}s")
        print(f"Speed:            {result.statistics.records_per_second:.1f} records/sec")
        print("=" * 70)

        # Print error summary if any
        if result.statistics.failed > 0:
            print("\nERROR SUMMARY:")
            print(f"Validation Errors:  {result.statistics.validation_errors}")
            print(f"Database Errors:    {result.statistics.database_errors}")
            print(f"\nError details logged to data_ingestion_errors table")

        # Commit if not dry run
        if not args.dry_run:
            session.commit()
            print("\nChanges committed to database.")
        else:
            print("\nDry run complete. No changes made to database.")

        # Exit code based on success
        if result.statistics.success_rate < 100:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error during load: {e}", exc_info=True)
        session.rollback()
        print(f"\nFatal error: {e}")
        sys.exit(1)

    finally:
        session.close()


if __name__ == "__main__":
    main()
