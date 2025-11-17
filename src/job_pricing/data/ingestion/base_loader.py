"""
Base Data Loader

Foundational class for all data ingestion operations.
Provides common functionality: batch processing, error handling, progress tracking.
"""

from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
from tqdm import tqdm

from src.job_pricing.repositories.base import BaseRepository
from ..validation.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")


@dataclass
class LoadStatistics:
    """
    Statistics from a data load operation.

    Tracks success/failure counts and timing information.
    """
    total_records: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    duplicates: int = 0
    validation_errors: int = 0
    database_errors: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_records == 0:
            return 0.0
        return (self.successful / self.total_records) * 100

    @property
    def records_per_second(self) -> float:
        """Calculate processing speed."""
        duration = self.duration_seconds
        if duration == 0:
            return 0.0
        return self.total_records / duration

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "total_records": self.total_records,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "duplicates": self.duplicates,
            "validation_errors": self.validation_errors,
            "database_errors": self.database_errors,
            "success_rate": f"{self.success_rate:.2f}%",
            "duration_seconds": f"{self.duration_seconds:.2f}",
            "records_per_second": f"{self.records_per_second:.2f}",
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }

    def __str__(self) -> str:
        """Human-readable summary."""
        return (
            f"Load Statistics:\n"
            f"  Total: {self.total_records}\n"
            f"  ✓ Successful: {self.successful}\n"
            f"  ✗ Failed: {self.failed}\n"
            f"  ⊘ Skipped: {self.skipped}\n"
            f"  ⚠ Validation Errors: {self.validation_errors}\n"
            f"  ⚠ Database Errors: {self.database_errors}\n"
            f"  Success Rate: {self.success_rate:.2f}%\n"
            f"  Duration: {self.duration_seconds:.2f}s\n"
            f"  Speed: {self.records_per_second:.2f} records/sec"
        )


@dataclass
class LoadResult:
    """
    Result from a data load operation.

    Contains statistics, errors, and any loaded models.
    """
    statistics: LoadStatistics
    validation_results: List[ValidationResult] = field(default_factory=list)
    error_log_ids: List[str] = field(default_factory=list)
    loaded_models: List[Any] = field(default_factory=list)

    def get_failed_records(self) -> List[str]:
        """Get list of failed record IDs."""
        return [
            vr.record_id
            for vr in self.validation_results
            if not vr.is_valid and vr.record_id
        ]


class BaseDataLoader(Generic[ModelType]):
    """
    Base class for data loaders.

    Provides common functionality:
    - Batch processing with progress bars
    - Validation integration
    - Error handling and logging
    - Transaction management
    - Statistics tracking

    Subclasses should override:
    - transform_record() - Convert raw data to model instance
    - get_record_id() - Extract unique identifier from raw data
    """

    def __init__(
        self,
        session: Session,
        repository: BaseRepository[ModelType],
        validator: Optional[BaseValidator] = None,
        batch_size: int = 100,
        continue_on_error: bool = True,
        show_progress: bool = True
    ):
        """
        Initialize data loader.

        Args:
            session: SQLAlchemy database session
            repository: Repository for database operations
            validator: Optional validator for data validation
            batch_size: Number of records to process per batch
            continue_on_error: If True, continue processing after errors
            show_progress: If True, show progress bar during loading
        """
        self.session = session
        self.repository = repository
        self.validator = validator
        self.batch_size = batch_size
        self.continue_on_error = continue_on_error
        self.show_progress = show_progress
        self.statistics = LoadStatistics()

    def load_data(
        self,
        data: List[Dict[str, Any]],
        pre_transform_hook: Optional[Callable] = None,
        post_transform_hook: Optional[Callable] = None
    ) -> LoadResult:
        """
        Load data into database with validation and error handling.

        Args:
            data: List of raw data dictionaries
            pre_transform_hook: Optional function to call before transforming each record
            post_transform_hook: Optional function to call after transforming each record

        Returns:
            LoadResult with statistics and errors
        """
        self.statistics = LoadStatistics()
        self.statistics.total_records = len(data)
        validation_results = []
        loaded_models = []

        logger.info(f"Starting data load: {len(data)} records")

        # Create progress bar
        progress = tqdm(total=len(data), disable=not self.show_progress)

        try:
            # Process in batches
            for i in range(0, len(data), self.batch_size):
                batch = data[i:i + self.batch_size]
                batch_result = self._process_batch(
                    batch,
                    pre_transform_hook,
                    post_transform_hook
                )

                validation_results.extend(batch_result["validation_results"])
                loaded_models.extend(batch_result["loaded_models"])

                # Update progress
                progress.update(len(batch))

        finally:
            progress.close()
            self.statistics.end_time = datetime.now()

        logger.info(f"Data load complete:\n{self.statistics}")

        return LoadResult(
            statistics=self.statistics,
            validation_results=validation_results,
            loaded_models=loaded_models
        )

    def _process_batch(
        self,
        batch: List[Dict[str, Any]],
        pre_transform_hook: Optional[Callable],
        post_transform_hook: Optional[Callable]
    ) -> Dict[str, List]:
        """
        Process a single batch of records.

        Args:
            batch: List of raw records to process
            pre_transform_hook: Optional pre-processing function
            post_transform_hook: Optional post-processing function

        Returns:
            Dictionary with validation_results and loaded_models
        """
        validation_results = []
        loaded_models = []

        for raw_record in batch:
            try:
                # Pre-transform hook
                if pre_transform_hook:
                    raw_record = pre_transform_hook(raw_record)

                # Get record identifier
                record_id = self.get_record_id(raw_record)

                # Validate if validator provided
                if self.validator:
                    validation_result = self.validator.validate(raw_record, record_id)
                    validation_results.append(validation_result)

                    if not validation_result.is_valid:
                        self.statistics.validation_errors += 1
                        self.statistics.failed += 1
                        self._log_validation_errors(validation_result)

                        if not self.continue_on_error:
                            raise ValueError(f"Validation failed for record {record_id}")

                        continue  # Skip this record

                # Transform raw data to model
                model_instance = self.transform_record(raw_record)

                # Post-transform hook
                if post_transform_hook:
                    model_instance = post_transform_hook(model_instance)

                # Insert into database
                try:
                    created_model = self.repository.create(model_instance)
                    loaded_models.append(created_model)
                    self.statistics.successful += 1

                except IntegrityError as e:
                    self.session.rollback()
                    self.statistics.database_errors += 1
                    self.statistics.failed += 1

                    # Check if duplicate
                    if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                        self.statistics.duplicates += 1
                        logger.warning(f"Duplicate record skipped: {record_id}")
                    else:
                        logger.error(f"Database error for record {record_id}: {e}")
                        self._log_database_error(record_id, raw_record, e)

                    if not self.continue_on_error:
                        raise

                except Exception as e:
                    self.session.rollback()
                    self.statistics.database_errors += 1
                    self.statistics.failed += 1
                    logger.error(f"Unexpected database error for record {record_id}: {e}")
                    self._log_database_error(record_id, raw_record, e)

                    if not self.continue_on_error:
                        raise

            except Exception as e:
                self.statistics.failed += 1
                record_id = self.get_record_id(raw_record) if raw_record else "unknown"
                logger.error(f"Error processing record {record_id}: {e}")

                if not self.continue_on_error:
                    raise

        # Commit batch
        try:
            self.repository.commit()
        except Exception as e:
            logger.error(f"Failed to commit batch: {e}")
            self.session.rollback()
            raise

        return {
            "validation_results": validation_results,
            "loaded_models": loaded_models
        }

    def transform_record(self, raw_data: Dict[str, Any]) -> ModelType:
        """
        Transform raw data dictionary to model instance.

        Subclasses MUST override this method.

        Args:
            raw_data: Raw data dictionary from source

        Returns:
            Model instance ready for database insertion

        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError("Subclasses must implement transform_record()")

    def get_record_id(self, raw_data: Dict[str, Any]) -> str:
        """
        Extract unique identifier from raw data.

        Subclasses SHOULD override this method.

        Args:
            raw_data: Raw data dictionary

        Returns:
            Unique identifier string

        Default implementation returns "Record {index}" which is not ideal.
        """
        return f"Record {id(raw_data)}"

    def _log_validation_errors(self, validation_result: ValidationResult):
        """
        Log validation errors to error table.

        Args:
            validation_result: Validation result with errors
        """
        # TODO: Implement error logging to database
        # Will be implemented when DataIngestionError model is created
        for error in validation_result.errors:
            logger.warning(
                f"Validation error - Record: {validation_result.record_id}, "
                f"Field: {error.field}, Type: {error.error_type}, "
                f"Message: {error.message}"
            )

    def _log_database_error(
        self,
        record_id: str,
        raw_data: Dict[str, Any],
        exception: Exception
    ):
        """
        Log database errors to error table.

        Args:
            record_id: Record identifier
            raw_data: Original raw data
            exception: Exception that occurred
        """
        # TODO: Implement error logging to database
        # Will be implemented when DataIngestionError model is created
        logger.error(
            f"Database error - Record: {record_id}, "
            f"Exception: {type(exception).__name__}, "
            f"Message: {str(exception)}"
        )

    def dry_run(self, data: List[Dict[str, Any]]) -> LoadResult:
        """
        Perform validation-only run without database writes.

        Args:
            data: List of raw data dictionaries

        Returns:
            LoadResult with validation results but no loaded models
        """
        logger.info(f"Starting DRY RUN: {len(data)} records")

        validation_results = []
        self.statistics = LoadStatistics()
        self.statistics.total_records = len(data)

        for raw_record in tqdm(data, disable=not self.show_progress):
            record_id = self.get_record_id(raw_record)

            # Validate
            if self.validator:
                validation_result = self.validator.validate(raw_record, record_id)
                validation_results.append(validation_result)

                if validation_result.is_valid:
                    self.statistics.successful += 1
                else:
                    self.statistics.validation_errors += 1
                    self.statistics.failed += 1

            # Try to transform (to catch transformation errors)
            try:
                self.transform_record(raw_record)
            except Exception as e:
                logger.error(f"Transformation error for {record_id}: {e}")
                self.statistics.failed += 1

        self.statistics.end_time = datetime.now()

        logger.info(f"DRY RUN complete:\n{self.statistics}")

        return LoadResult(
            statistics=self.statistics,
            validation_results=validation_results,
            loaded_models=[]
        )
