"""
Batch Processor

Advanced batch processing utilities for data ingestion.
Provides parallel processing, chunking, and progress tracking.
"""

from typing import List, Dict, Any, Callable, Optional, TypeVar, Generic
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class BatchConfig:
    """
    Configuration for batch processing.

    Attributes:
        batch_size: Number of items per batch
        max_workers: Maximum number of parallel workers
        use_processes: If True, use ProcessPool (CPU-bound); else ThreadPool (I/O-bound)
        show_progress: If True, display progress bar
        fail_fast: If True, stop on first error; else continue
    """
    batch_size: int = 100
    max_workers: int = 4
    use_processes: bool = False
    show_progress: bool = True
    fail_fast: bool = False


class BatchProcessor(Generic[T, R]):
    """
    Generic batch processor with parallel execution support.

    Processes large datasets in batches with configurable parallelism.
    Supports both thread-based (I/O-bound) and process-based (CPU-bound) execution.

    Example:
        >>> def process_record(record):
        ...     # Heavy processing
        ...     return transformed_record
        ...
        >>> processor = BatchProcessor(
        ...     config=BatchConfig(batch_size=100, max_workers=4)
        ... )
        >>> results = processor.process(
        ...     data=records,
        ...     process_func=process_record
        ... )
    """

    def __init__(self, config: Optional[BatchConfig] = None):
        """
        Initialize batch processor.

        Args:
            config: Batch processing configuration
        """
        self.config = config or BatchConfig()

    def process(
        self,
        data: List[T],
        process_func: Callable[[T], R],
        error_handler: Optional[Callable[[T, Exception], None]] = None
    ) -> List[R]:
        """
        Process data in batches with optional parallelism.

        Args:
            data: List of items to process
            process_func: Function to apply to each item
            error_handler: Optional function to call on errors (item, exception)

        Returns:
            List of processed results

        Example:
            >>> results = processor.process(
            ...     data=jobs,
            ...     process_func=lambda job: transform_job(job),
            ...     error_handler=lambda job, e: log_error(job, e)
            ... )
        """
        if not data:
            logger.warning("Empty data list provided to process()")
            return []

        logger.info(f"Processing {len(data)} items with config: {self.config}")

        results = []

        if self.config.max_workers == 1:
            # Serial processing (no parallelism)
            results = self._process_serial(data, process_func, error_handler)
        else:
            # Parallel processing
            results = self._process_parallel(data, process_func, error_handler)

        logger.info(f"Processed {len(results)} items successfully")

        return results

    def _process_serial(
        self,
        data: List[T],
        process_func: Callable[[T], R],
        error_handler: Optional[Callable[[T, Exception], None]]
    ) -> List[R]:
        """
        Process data serially (no parallelism).

        Args:
            data: List of items to process
            process_func: Function to apply to each item
            error_handler: Optional error handling function

        Returns:
            List of processed results
        """
        results = []

        for item in tqdm(data, disable=not self.config.show_progress):
            try:
                result = process_func(item)
                results.append(result)

            except Exception as e:
                logger.error(f"Error processing item: {e}")

                if error_handler:
                    error_handler(item, e)

                if self.config.fail_fast:
                    raise

        return results

    def _process_parallel(
        self,
        data: List[T],
        process_func: Callable[[T], R],
        error_handler: Optional[Callable[[T, Exception], None]]
    ) -> List[R]:
        """
        Process data in parallel using thread or process pool.

        Args:
            data: List of items to process
            process_func: Function to apply to each item
            error_handler: Optional error handling function

        Returns:
            List of processed results
        """
        results = []

        # Choose executor type
        ExecutorClass = ProcessPoolExecutor if self.config.use_processes else ThreadPoolExecutor

        with ExecutorClass(max_workers=self.config.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(process_func, item): item
                for item in data
            }

            # Process completed tasks with progress bar
            progress = tqdm(
                total=len(data),
                disable=not self.config.show_progress
            )

            for future in as_completed(future_to_item):
                item = future_to_item[future]

                try:
                    result = future.result()
                    results.append(result)

                except Exception as e:
                    logger.error(f"Error processing item: {e}")

                    if error_handler:
                        error_handler(item, e)

                    if self.config.fail_fast:
                        # Cancel remaining tasks
                        for f in future_to_item:
                            f.cancel()
                        raise

                finally:
                    progress.update(1)

            progress.close()

        return results

    def process_in_batches(
        self,
        data: List[T],
        batch_func: Callable[[List[T]], List[R]],
        error_handler: Optional[Callable[[List[T], Exception], None]] = None
    ) -> List[R]:
        """
        Process data in batches (each batch processed as a unit).

        Useful when batch processing is more efficient than individual item processing
        (e.g., bulk database inserts, batch API calls).

        Args:
            data: List of items to process
            batch_func: Function to apply to each batch
            error_handler: Optional function to call on batch errors

        Returns:
            Flattened list of processed results

        Example:
            >>> def process_batch(batch):
            ...     # Bulk insert
            ...     return repository.bulk_insert(batch)
            ...
            >>> results = processor.process_in_batches(
            ...     data=jobs,
            ...     batch_func=process_batch
            ... )
        """
        if not data:
            return []

        results = []
        batches = self._create_batches(data)

        logger.info(f"Processing {len(batches)} batches of size {self.config.batch_size}")

        for batch in tqdm(batches, disable=not self.config.show_progress):
            try:
                batch_results = batch_func(batch)

                if batch_results:
                    results.extend(batch_results)

            except Exception as e:
                logger.error(f"Error processing batch: {e}")

                if error_handler:
                    error_handler(batch, e)

                if self.config.fail_fast:
                    raise

        return results

    def _create_batches(self, data: List[T]) -> List[List[T]]:
        """
        Split data into batches.

        Args:
            data: List of items to batch

        Returns:
            List of batches
        """
        batch_size = self.config.batch_size
        return [
            data[i:i + batch_size]
            for i in range(0, len(data), batch_size)
        ]

    @staticmethod
    def chunk_data(data: List[T], chunk_size: int) -> List[List[T]]:
        """
        Split data into chunks of specified size.

        Args:
            data: List of items to chunk
            chunk_size: Size of each chunk

        Returns:
            List of chunks

        Example:
            >>> chunks = BatchProcessor.chunk_data([1, 2, 3, 4, 5], chunk_size=2)
            >>> # Returns: [[1, 2], [3, 4], [5]]
        """
        return [
            data[i:i + chunk_size]
            for i in range(0, len(data), chunk_size)
        ]

    @staticmethod
    def flatten(nested_list: List[List[T]]) -> List[T]:
        """
        Flatten a list of lists into a single list.

        Args:
            nested_list: List of lists

        Returns:
            Flattened list

        Example:
            >>> flattened = BatchProcessor.flatten([[1, 2], [3, 4], [5]])
            >>> # Returns: [1, 2, 3, 4, 5]
        """
        return [item for sublist in nested_list for item in sublist]


def parallel_map(
    func: Callable[[T], R],
    data: List[T],
    max_workers: int = 4,
    use_processes: bool = False,
    show_progress: bool = True
) -> List[R]:
    """
    Convenience function for parallel mapping.

    Args:
        func: Function to apply to each item
        data: List of items to process
        max_workers: Maximum number of parallel workers
        use_processes: If True, use processes; else threads
        show_progress: If True, show progress bar

    Returns:
        List of results

    Example:
        >>> results = parallel_map(
        ...     func=lambda x: x * 2,
        ...     data=[1, 2, 3, 4, 5],
        ...     max_workers=2
        ... )
        >>> # Returns: [2, 4, 6, 8, 10]
    """
    config = BatchConfig(
        batch_size=1,  # Process one item at a time
        max_workers=max_workers,
        use_processes=use_processes,
        show_progress=show_progress
    )

    processor = BatchProcessor(config=config)

    return processor.process(data, func)


def batch_map(
    batch_func: Callable[[List[T]], List[R]],
    data: List[T],
    batch_size: int = 100,
    show_progress: bool = True
) -> List[R]:
    """
    Convenience function for batch processing.

    Args:
        batch_func: Function to apply to each batch
        data: List of items to process
        batch_size: Size of each batch
        show_progress: If True, show progress bar

    Returns:
        Flattened list of results

    Example:
        >>> def bulk_insert(batch):
        ...     return database.insert_many(batch)
        ...
        >>> results = batch_map(
        ...     batch_func=bulk_insert,
        ...     data=records,
        ...     batch_size=100
        ... )
    """
    config = BatchConfig(
        batch_size=batch_size,
        max_workers=1,  # Serial batch processing
        show_progress=show_progress
    )

    processor = BatchProcessor(config=config)

    return processor.process_in_batches(data, batch_func)
