"""
Generate Vector Embeddings for Mercer Jobs

Generates OpenAI embeddings for Mercer Job Library records to enable semantic search.
Uses text-embedding-3-large model (1536 dimensions) for high-quality embeddings.

Features:
- Batch processing with configurable batch size
- Rate limiting and retry logic
- Progress tracking
- Resume capability (skips jobs with existing embeddings)
- Cost estimation and tracking

Usage:
    from data.ingestion.generate_embeddings import EmbeddingGenerator

    generator = EmbeddingGenerator(session, api_key=os.getenv("OPENAI_API_KEY"))
    result = generator.generate_all(batch_size=100)
    print(f"Generated {result['generated']} embeddings")

    # Or from command line:
    python -m data.ingestion.generate_embeddings --batch-size 100
"""

import sys
import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from sqlalchemy.orm import Session
import openai
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.job_pricing.models.mercer import MercerJobLibrary
from src.job_pricing.repositories.mercer_repository import MercerJobLibraryRepository
from src.job_pricing.core.database import get_session

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingStatistics:
    """Statistics for embedding generation."""
    total_jobs: int = 0
    jobs_with_embeddings: int = 0
    jobs_without_embeddings: int = 0
    generated: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    @property
    def embeddings_per_second(self) -> float:
        """Calculate embeddings per second."""
        duration = self.duration_seconds
        return self.generated / duration if duration > 0 else 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        attempted = self.generated + self.failed
        return (self.generated / attempted * 100) if attempted > 0 else 0


class EmbeddingGenerator:
    """
    Generator for OpenAI embeddings for Mercer jobs.

    Uses OpenAI's text-embedding-3-large model to generate 1536-dimensional
    vector embeddings for semantic search.

    Pricing (as of 2024):
    - text-embedding-3-large: $0.13 per 1M tokens
    - Average job ~500 tokens
    - Cost for 18,000 jobs: ~$1.17 USD

    Example:
        >>> generator = EmbeddingGenerator(session, api_key=os.getenv("OPENAI_API_KEY"))
        >>> result = generator.generate_all(batch_size=100, skip_existing=True)
        >>> print(f"Cost: ${result['total_cost_usd']:.2f}")
    """

    # OpenAI pricing (per 1M tokens)
    EMBEDDING_MODEL = "text-embedding-3-large"
    EMBEDDING_DIMENSIONS = 1536
    COST_PER_1M_TOKENS = 0.13  # USD

    # Rate limits (tier 1)
    MAX_REQUESTS_PER_MINUTE = 500
    MAX_TOKENS_PER_MINUTE = 1_000_000

    def __init__(
        self,
        session: Session,
        api_key: Optional[str] = None,
        batch_size: int = 100,
        show_progress: bool = True
    ):
        """
        Initialize embedding generator.

        Args:
            session: SQLAlchemy database session
            api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
            batch_size: Number of jobs to process per batch
            show_progress: Show progress bar
        """
        self.session = session
        self.repository = MercerJobLibraryRepository(session)
        self.batch_size = batch_size
        self.show_progress = show_progress

        # Initialize OpenAI client
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = openai.OpenAI(api_key=api_key)

        # Rate limiting
        self.request_times: List[float] = []
        self.token_counts: List[int] = []

    def generate_all(
        self,
        skip_existing: bool = True,
        max_jobs: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate embeddings for all Mercer jobs.

        Args:
            skip_existing: Skip jobs that already have embeddings
            max_jobs: Maximum number of jobs to process (for testing)

        Returns:
            Dictionary with statistics

        Example:
            >>> result = generator.generate_all(skip_existing=True)
            >>> print(f"Generated {result['statistics'].generated} embeddings")
            >>> print(f"Total cost: ${result['statistics'].total_cost_usd:.2f}")
        """
        stats = EmbeddingStatistics()

        logger.info("Starting embedding generation for Mercer jobs")

        # Get jobs that need embeddings
        if skip_existing:
            jobs = self.repository.find_by(embedding=None)
            logger.info(f"Found {len(jobs)} jobs without embeddings")
        else:
            jobs = self.repository.get_all()
            logger.info(f"Found {len(jobs)} total jobs")

        # Apply max_jobs limit for testing
        if max_jobs:
            jobs = jobs[:max_jobs]
            logger.info(f"Limited to {max_jobs} jobs for testing")

        stats.total_jobs = len(jobs)
        stats.jobs_without_embeddings = len(jobs)

        # Process in batches
        batches = [
            jobs[i:i + self.batch_size]
            for i in range(0, len(jobs), self.batch_size)
        ]

        logger.info(f"Processing {len(batches)} batches of size {self.batch_size}")

        for batch in tqdm(batches, desc="Generating embeddings", disable=not self.show_progress):
            try:
                self._process_batch(batch, stats)

                # Commit after each batch
                self.session.commit()

            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                self.session.rollback()
                stats.failed += len(batch)

        stats.end_time = datetime.now()

        logger.info(
            f"Embedding generation complete: {stats.generated} generated, "
            f"{stats.failed} failed, {stats.skipped} skipped"
        )

        return {
            "statistics": stats,
            "total_jobs": stats.total_jobs,
            "generated": stats.generated,
            "failed": stats.failed,
            "skipped": stats.skipped,
            "total_cost_usd": stats.total_cost_usd,
            "duration_seconds": stats.duration_seconds,
        }

    def _process_batch(self, jobs: List[MercerJobLibrary], stats: EmbeddingStatistics):
        """
        Process a batch of jobs.

        Args:
            jobs: List of jobs to process
            stats: Statistics object to update
        """
        for job in jobs:
            try:
                # Skip if already has embedding (safety check)
                if job.embedding is not None:
                    stats.skipped += 1
                    continue

                # Generate embedding text
                embedding_text = self._create_embedding_text(job)

                # Estimate tokens
                estimated_tokens = len(embedding_text) // 4  # Rough estimate

                # Rate limiting
                self._rate_limit(estimated_tokens)

                # Generate embedding
                response = self.client.embeddings.create(
                    model=self.EMBEDDING_MODEL,
                    input=embedding_text,
                    dimensions=self.EMBEDDING_DIMENSIONS
                )

                # Extract embedding vector
                embedding_vector = response.data[0].embedding

                # Update job
                job.embedding = embedding_vector

                # Update statistics
                stats.generated += 1
                stats.total_tokens += response.usage.total_tokens
                stats.total_cost_usd += (response.usage.total_tokens / 1_000_000) * self.COST_PER_1M_TOKENS

                # Record request time for rate limiting
                self.request_times.append(time.time())
                self.token_counts.append(response.usage.total_tokens)

            except Exception as e:
                logger.error(f"Failed to generate embedding for job {job.job_code}: {e}")
                stats.failed += 1

    @staticmethod
    def _create_embedding_text(job: MercerJobLibrary) -> str:
        """
        Create embedding text from job data.

        Combines job title, description, family, and other relevant fields
        into a single text for embedding generation.

        Args:
            job: MercerJobLibrary instance

        Returns:
            Combined text for embedding
        """
        parts = []

        # Job title (most important)
        parts.append(f"Job Title: {job.job_title}")

        # Family and subfamily
        if job.family:
            parts.append(f"Family: {job.family}")
        if job.subfamily:
            parts.append(f"Subfamily: {job.subfamily}")

        # Career level
        if job.career_level:
            parts.append(f"Level: {job.career_level}")

        # Job description (if available)
        if job.job_description:
            # Limit description to 2000 chars to avoid token limits
            description = job.job_description[:2000]
            parts.append(f"Description: {description}")

        # Typical titles (if available)
        if job.typical_titles:
            titles_str = ", ".join(job.typical_titles[:5])  # Limit to 5 titles
            parts.append(f"Typical Titles: {titles_str}")

        # Specialization notes (if available)
        if job.specialization_notes:
            notes = job.specialization_notes[:500]  # Limit to 500 chars
            parts.append(f"Specialization: {notes}")

        return "\n".join(parts)

    def _rate_limit(self, estimated_tokens: int):
        """
        Implement rate limiting to avoid hitting OpenAI limits.

        OpenAI Tier 1 limits:
        - 500 requests per minute
        - 1,000,000 tokens per minute

        Args:
            estimated_tokens: Estimated tokens for next request
        """
        current_time = time.time()

        # Clean up old request times (older than 60 seconds)
        cutoff_time = current_time - 60
        self.request_times = [t for t in self.request_times if t > cutoff_time]
        self.token_counts = self.token_counts[-len(self.request_times):]

        # Check request rate
        if len(self.request_times) >= self.MAX_REQUESTS_PER_MINUTE - 10:  # 10 request buffer
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"Rate limit: sleeping {sleep_time:.1f}s (requests)")
                time.sleep(sleep_time)
                return

        # Check token rate
        total_tokens = sum(self.token_counts) + estimated_tokens
        if total_tokens >= self.MAX_TOKENS_PER_MINUTE - 10000:  # 10k token buffer
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"Rate limit: sleeping {sleep_time:.1f}s (tokens)")
                time.sleep(sleep_time)
                return

    def estimate_cost(self, num_jobs: Optional[int] = None) -> Dict[str, Any]:
        """
        Estimate cost for generating embeddings.

        Args:
            num_jobs: Number of jobs (default: all jobs without embeddings)

        Returns:
            Dictionary with cost estimates

        Example:
            >>> estimate = generator.estimate_cost()
            >>> print(f"Estimated cost: ${estimate['total_cost_usd']:.2f}")
        """
        if num_jobs is None:
            jobs_without_embeddings = self.repository.find_by(embedding=None)
            num_jobs = len(jobs_without_embeddings)

        # Estimate tokens per job (500 tokens average)
        estimated_tokens_per_job = 500
        total_tokens = num_jobs * estimated_tokens_per_job

        # Calculate cost
        cost_usd = (total_tokens / 1_000_000) * self.COST_PER_1M_TOKENS

        return {
            "num_jobs": num_jobs,
            "estimated_tokens_per_job": estimated_tokens_per_job,
            "total_tokens": total_tokens,
            "total_cost_usd": cost_usd,
            "model": self.EMBEDDING_MODEL,
            "dimensions": self.EMBEDDING_DIMENSIONS,
        }


def main():
    """
    Command-line entry point for generating embeddings.

    Usage:
        python -m data.ingestion.generate_embeddings [--batch-size 100] [--max-jobs 10] [--estimate]

    Examples:
        # Estimate cost
        python -m data.ingestion.generate_embeddings --estimate

        # Generate for all jobs without embeddings
        python -m data.ingestion.generate_embeddings

        # Test with 10 jobs
        python -m data.ingestion.generate_embeddings --max-jobs 10

        # Custom batch size
        python -m data.ingestion.generate_embeddings --batch-size 50
    """
    import argparse

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Generate OpenAI embeddings for Mercer jobs"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of jobs per batch (default: 100)"
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=None,
        help="Maximum number of jobs to process (for testing)"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip jobs with existing embeddings (default: True)"
    )
    parser.add_argument(
        "--estimate",
        action="store_true",
        help="Estimate cost only, do not generate embeddings"
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Hide progress bar"
    )

    args = parser.parse_args()

    # Get database session
    session = get_session()

    try:
        # Create generator
        generator = EmbeddingGenerator(
            session=session,
            batch_size=args.batch_size,
            show_progress=not args.no_progress
        )

        if args.estimate:
            # Estimate cost only
            estimate = generator.estimate_cost(num_jobs=args.max_jobs)

            print("\n" + "=" * 70)
            print("EMBEDDING GENERATION COST ESTIMATE")
            print("=" * 70)
            print(f"Model:                {estimate['model']}")
            print(f"Dimensions:           {estimate['dimensions']}")
            print(f"Jobs to Process:      {estimate['num_jobs']:,}")
            print(f"Est. Tokens/Job:      {estimate['estimated_tokens_per_job']:,}")
            print(f"Total Tokens:         {estimate['total_tokens']:,}")
            print(f"Cost per 1M Tokens:   ${generator.COST_PER_1M_TOKENS}")
            print(f"Total Cost (USD):     ${estimate['total_cost_usd']:.2f}")
            print("=" * 70)

        else:
            # Generate embeddings
            result = generator.generate_all(
                skip_existing=args.skip_existing,
                max_jobs=args.max_jobs
            )

            stats = result["statistics"]

            # Print summary
            print("\n" + "=" * 70)
            print("EMBEDDING GENERATION SUMMARY")
            print("=" * 70)
            print(f"Total Jobs:           {stats.total_jobs:,}")
            print(f"Generated:            {stats.generated:,}")
            print(f"Failed:               {stats.failed:,}")
            print(f"Skipped:              {stats.skipped:,}")
            print(f"Success Rate:         {stats.success_rate:.1f}%")
            print(f"Duration:             {stats.duration_seconds:.1f}s")
            print(f"Speed:                {stats.embeddings_per_second:.1f} embeddings/sec")
            print(f"Total Tokens:         {stats.total_tokens:,}")
            print(f"Total Cost (USD):     ${stats.total_cost_usd:.2f}")
            print("=" * 70)

            # Commit changes
            session.commit()
            print("\nEmbeddings saved to database.")

            # Exit code based on success
            if stats.failed > 0:
                sys.exit(1)
            else:
                sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        session.rollback()
        print(f"\nFatal error: {e}")
        sys.exit(1)

    finally:
        session.close()


if __name__ == "__main__":
    main()
