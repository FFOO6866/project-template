"""
Mercer Job Library Data Loader

Loads Mercer Job Library data from Excel files into the database.
Includes validation, batch processing, and error logging.

Usage:
    from data.ingestion.mercer_job_library_loader import MercerJobLibraryLoader

    loader = MercerJobLibraryLoader(session)
    result = loader.load_from_excel("data/raw/mercer/mercer_job_library.xlsx")
    print(f"Loaded {result.statistics.successful}/{result.statistics.total_records} jobs")

    # Or from command line:
    python -m data.ingestion.mercer_job_library_loader data/raw/mercer/mercer_job_library.xlsx
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.job_pricing.models.mercer import MercerJobLibrary
from src.job_pricing.models.data_ingestion_error import DataIngestionError, ErrorSource, ErrorType
from src.job_pricing.repositories.mercer_repository import MercerRepository
from data.ingestion.base_loader import BaseDataLoader, LoadResult
from data.ingestion.excel_loader import ExcelLoader
from data.validation.mercer_validator import MercerJobLibraryValidator
from src.job_pricing.utils.database import get_db_context

logger = logging.getLogger(__name__)


class MercerJobLibraryLoader(BaseDataLoader[MercerJobLibrary], ExcelLoader):
    """
    Loader for Mercer Job Library data from Excel files.

    Expected Excel columns:
    - job_code (required): Mercer job code (e.g., "HRM.04.005.M50")
    - job_title (required): Standardized job title
    - family (required): Job family (e.g., "Human Resources Management")
    - subfamily (optional): Job subfamily
    - career_level (optional): Career level (M3, M4, M5, P1, P2, etc.)
    - position_class (optional): Position class (40-87)
    - job_description (optional): Full job description text
    - typical_titles (optional): Comma-separated list of typical job titles
    - specialization_notes (optional): Additional specialization notes
    - impact_min (optional): IPE Impact factor minimum points
    - impact_max (optional): IPE Impact factor maximum points
    - communication_min (optional): IPE Communication factor minimum points
    - communication_max (optional): IPE Communication factor maximum points
    - innovation_min (optional): IPE Innovation factor minimum points
    - innovation_max (optional): IPE Innovation factor maximum points
    - knowledge_min (optional): IPE Knowledge factor minimum points
    - knowledge_max (optional): IPE Knowledge factor maximum points
    - risk_min (optional): IPE Accountability/Risk factor minimum points
    - risk_max (optional): IPE Accountability/Risk factor maximum points

    Example:
        >>> loader = MercerJobLibraryLoader(session)
        >>> result = loader.load_from_excel("mercer_jobs.xlsx")
        >>> print(f"Success rate: {result.statistics.success_rate:.1f}%")
        >>> print(f"Speed: {result.statistics.records_per_second:.1f} records/sec")
    """

    def __init__(
        self,
        session: Session,
        batch_size: int = 100,
        continue_on_error: bool = True,
        show_progress: bool = True
    ):
        """
        Initialize Mercer Job Library loader.

        Args:
            session: SQLAlchemy database session
            batch_size: Number of records per batch (default: 100)
            continue_on_error: Continue loading on errors (default: True)
            show_progress: Show progress bar (default: True)
        """
        # Initialize repository
        repository = MercerRepository(session)

        # Get existing job codes for duplicate detection
        existing_jobs = repository.get_all()
        existing_job_codes = {job.job_code for job in existing_jobs}

        # Initialize validator
        validator = MercerJobLibraryValidator(existing_job_codes=existing_job_codes)

        # Initialize base loader
        super().__init__(
            session=session,
            repository=repository,
            validator=validator,
            batch_size=batch_size,
            continue_on_error=continue_on_error,
            show_progress=show_progress
        )

    def transform_record(self, raw_data: Dict[str, Any]) -> MercerJobLibrary:
        """
        Transform Excel row data into MercerJobLibrary model instance.

        Args:
            raw_data: Dictionary from Excel row

        Returns:
            MercerJobLibrary model instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Handle typical_titles: convert comma-separated string to list
        typical_titles = None
        if raw_data.get("typical_titles"):
            if isinstance(raw_data["typical_titles"], str):
                typical_titles = [
                    title.strip()
                    for title in raw_data["typical_titles"].split(",")
                    if title.strip()
                ]
            elif isinstance(raw_data["typical_titles"], list):
                typical_titles = raw_data["typical_titles"]

        # Create model instance
        job = MercerJobLibrary(
            job_code=raw_data.get("job_code"),
            job_title=raw_data.get("job_title"),
            family=raw_data.get("family"),
            subfamily=raw_data.get("subfamily"),
            career_level=raw_data.get("career_level"),
            position_class=self._safe_int(raw_data.get("position_class")),
            job_description=raw_data.get("job_description"),
            typical_titles=typical_titles,
            specialization_notes=raw_data.get("specialization_notes"),
            # IPE Impact
            impact_min=self._safe_int(raw_data.get("impact_min")),
            impact_max=self._safe_int(raw_data.get("impact_max")),
            # IPE Communication
            communication_min=self._safe_int(raw_data.get("communication_min")),
            communication_max=self._safe_int(raw_data.get("communication_max")),
            # IPE Innovation
            innovation_min=self._safe_int(raw_data.get("innovation_min")),
            innovation_max=self._safe_int(raw_data.get("innovation_max")),
            # IPE Knowledge
            knowledge_min=self._safe_int(raw_data.get("knowledge_min")),
            knowledge_max=self._safe_int(raw_data.get("knowledge_max")),
            # IPE Risk/Accountability
            risk_min=self._safe_int(raw_data.get("risk_min")),
            risk_max=self._safe_int(raw_data.get("risk_max")),
            # Embedding will be generated separately
            embedding=None
        )

        return job

    def get_record_id(self, raw_data: Dict[str, Any]) -> str:
        """
        Extract record identifier from raw data.

        Args:
            raw_data: Dictionary from Excel row

        Returns:
            Record identifier (job_code)
        """
        return raw_data.get("job_code", "UNKNOWN")

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        """
        Safely convert value to integer.

        Args:
            value: Value to convert

        Returns:
            Integer value or None
        """
        if value is None or value == "":
            return None

        try:
            return int(float(value))  # Handle "123.0" from Excel
        except (ValueError, TypeError):
            return None

    def load_from_excel(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        dry_run: bool = False
    ) -> LoadResult:
        """
        Load Mercer Job Library data from Excel file.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name (default: first sheet)
            dry_run: If True, validate only without database writes

        Returns:
            LoadResult with statistics and error information

        Example:
            >>> loader = MercerJobLibraryLoader(session)
            >>> result = loader.load_from_excel("mercer_jobs.xlsx")
            >>> if result.statistics.success_rate < 95:
            ...     print(f"Warning: Low success rate {result.statistics.success_rate:.1f}%")
        """
        logger.info(f"Loading Mercer Job Library from: {file_path}")

        # Read Excel file
        try:
            data = self.read_excel(file_path, sheet_name=sheet_name, clean_data=True)
            logger.info(f"Read {len(data)} records from Excel")
        except Exception as e:
            logger.error(f"Failed to read Excel file: {e}")
            raise

        # Validate required columns
        if data:
            required_columns = ["job_code", "job_title", "family"]
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
    Command-line entry point for loading Mercer Job Library data.

    Usage:
        python -m data.ingestion.mercer_job_library_loader <excel_file> [--dry-run] [--batch-size 100]

    Examples:
        python -m data.ingestion.mercer_job_library_loader data/raw/mercer/mercer_job_library.xlsx
        python -m data.ingestion.mercer_job_library_loader data/raw/mercer/mercer_job_library.xlsx --dry-run
        python -m data.ingestion.mercer_job_library_loader data/raw/mercer/mercer_job_library.xlsx --batch-size 50
    """
    import argparse

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Load Mercer Job Library data from Excel file"
    )
    parser.add_argument(
        "excel_file",
        help="Path to Excel file containing Mercer Job Library data"
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
        loader = MercerJobLibraryLoader(
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
        print("MERCER JOB LIBRARY LOAD SUMMARY")
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
