"""
SSG Job Role → TSC Mappings Data Loader

Loads SSG job role to technical skills & competencies mappings from Excel files.
Includes validation, batch processing, and error logging.

IMPORTANT: Must load Job Roles and TSC data BEFORE loading mappings!

Usage:
    from data.ingestion.ssg_mappings_loader import SSGMappingsLoader

    loader = SSGMappingsLoader(session)
    result = loader.load_from_excel("data/raw/ssg/ssg_mappings.xlsx")
    print(f"Loaded {result.statistics.successful}/{result.statistics.total_records} mappings")

    # Or from command line:
    python -m data.ingestion.ssg_mappings_loader data/raw/ssg/ssg_mappings.xlsx
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.job_pricing.models.ssg import SSGJobRoleTSCMapping
from src.job_pricing.repositories.ssg_repository import (
    SSGJobRolesRepository,
    SSGTSCRepository,
    SSGMappingRepository
)
from data.ingestion.base_loader import BaseDataLoader, LoadResult
from data.ingestion.excel_loader import ExcelLoader
from data.validation.ssg_validator import SSGMappingValidator
from src.job_pricing.core.database import get_session

logger = logging.getLogger(__name__)


class SSGMappingsLoader(BaseDataLoader[SSGJobRoleTSCMapping], ExcelLoader):
    """
    Loader for SSG job role → TSC mapping data from Excel files.

    Expected Excel columns:
    - job_role_code (required): SSG job role code (e.g., "ICT-DIS-4010-1.1")
    - tsc_code (required): TSC code (e.g., "ICT-DIS-4010-1.1-A")
    - proficiency_level (required): Required proficiency level (1-6 or Basic/Intermediate/Advanced)
    - is_core_skill (optional): Whether this is a core skill (true/false/yes/no/1/0)

    PREREQUISITES:
    - SSG Job Roles must be loaded first
    - SSG TSC must be loaded first

    Example:
        >>> loader = SSGMappingsLoader(session)
        >>> result = loader.load_from_excel("ssg_mappings.xlsx")
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
        Initialize SSG Mappings loader.

        Args:
            session: SQLAlchemy database session
            batch_size: Number of records per batch (default: 100)
            continue_on_error: Continue loading on errors (default: True)
            show_progress: Show progress bar (default: True)
        """
        # Initialize repositories
        job_roles_repo = SSGJobRolesRepository(session)
        tsc_repo = SSGTSCRepository(session)
        mappings_repo = SSGMappingRepository(session)

        # Get valid foreign keys
        valid_role_codes = {role.job_role_code for role in job_roles_repo.get_all()}
        valid_tsc_codes = {tsc.tsc_code for tsc in tsc_repo.get_all()}

        # Verify we have data to reference
        if not valid_role_codes:
            raise ValueError(
                "No SSG Job Roles found in database. Load job roles before mappings."
            )

        if not valid_tsc_codes:
            raise ValueError(
                "No SSG TSC found in database. Load TSC before mappings."
            )

        logger.info(f"Found {len(valid_role_codes)} job roles and {len(valid_tsc_codes)} TSC for validation")

        # Initialize validator
        validator = SSGMappingValidator(
            valid_role_codes=valid_role_codes,
            valid_tsc_codes=valid_tsc_codes
        )

        # Initialize base loader
        super().__init__(
            session=session,
            repository=mappings_repo,
            validator=validator,
            batch_size=batch_size,
            continue_on_error=continue_on_error,
            show_progress=show_progress
        )

    def transform_record(self, raw_data: Dict[str, Any]) -> SSGJobRoleTSCMapping:
        """
        Transform Excel row data into SSGJobRoleTSCMapping model instance.

        Args:
            raw_data: Dictionary from Excel row

        Returns:
            SSGJobRoleTSCMapping model instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Handle proficiency_level: normalize to string
        proficiency_level = raw_data.get("proficiency_level")
        if proficiency_level is not None:
            proficiency_level = str(proficiency_level)

        # Handle is_core_skill: normalize to boolean
        is_core_skill = self._parse_boolean(raw_data.get("is_core_skill"), default=False)

        mapping = SSGJobRoleTSCMapping(
            job_role_code=raw_data.get("job_role_code"),
            tsc_code=raw_data.get("tsc_code"),
            proficiency_level=proficiency_level,
            is_core_skill=is_core_skill,
        )

        return mapping

    def get_record_id(self, raw_data: Dict[str, Any]) -> str:
        """
        Extract record identifier from raw data.

        Args:
            raw_data: Dictionary from Excel row

        Returns:
            Record identifier (composite key: job_role_code + tsc_code)
        """
        job_role = raw_data.get("job_role_code", "UNKNOWN")
        tsc = raw_data.get("tsc_code", "UNKNOWN")
        return f"{job_role}:{tsc}"

    @staticmethod
    def _parse_boolean(value: Any, default: bool = False) -> bool:
        """
        Parse boolean value from various formats.

        Args:
            value: Value to parse (can be bool, str, int, None)
            default: Default value if None

        Returns:
            Boolean value

        Examples:
            >>> _parse_boolean(True)  # True
            >>> _parse_boolean("yes")  # True
            >>> _parse_boolean("1")    # True
            >>> _parse_boolean(0)      # False
            >>> _parse_boolean(None)   # False (default)
        """
        if value is None:
            return default

        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return bool(value)

        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ("true", "yes", "y", "1"):
                return True
            elif value_lower in ("false", "no", "n", "0"):
                return False

        return default

    def load_from_excel(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        dry_run: bool = False
    ) -> LoadResult:
        """
        Load SSG Mappings from Excel file.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name (default: first sheet)
            dry_run: If True, validate only without database writes

        Returns:
            LoadResult with statistics and error information

        Example:
            >>> loader = SSGMappingsLoader(session)
            >>> result = loader.load_from_excel("ssg_mappings.xlsx")
            >>> if result.statistics.success_rate < 95:
            ...     print(f"Warning: Low success rate {result.statistics.success_rate:.1f}%")
        """
        logger.info(f"Loading SSG Mappings from: {file_path}")

        # Read Excel file
        try:
            data = self.read_excel(file_path, sheet_name=sheet_name, clean_data=True)
            logger.info(f"Read {len(data)} records from Excel")
        except Exception as e:
            logger.error(f"Failed to read Excel file: {e}")
            raise

        # Validate required columns
        if data:
            required_columns = ["job_role_code", "tsc_code", "proficiency_level"]
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
    Command-line entry point for loading SSG Mappings data.

    Usage:
        python -m data.ingestion.ssg_mappings_loader <excel_file> [--dry-run] [--batch-size 100]

    Examples:
        python -m data.ingestion.ssg_mappings_loader data/raw/ssg/ssg_mappings.xlsx
        python -m data.ingestion.ssg_mappings_loader data/raw/ssg/ssg_mappings.xlsx --dry-run
        python -m data.ingestion.ssg_mappings_loader data/raw/ssg/ssg_mappings.xlsx --batch-size 50
    """
    import argparse

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Load SSG Mappings data from Excel file"
    )
    parser.add_argument(
        "excel_file",
        help="Path to Excel file containing SSG Mappings data"
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
        loader = SSGMappingsLoader(
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
        print("SSG MAPPINGS LOAD SUMMARY")
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
