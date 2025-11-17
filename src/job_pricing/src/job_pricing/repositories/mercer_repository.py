"""
Mercer Repository

Provides data access for Mercer Job Library, job mappings, and market data.
Includes vector similarity search for semantic job matching.
"""

from typing import List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from job_pricing.models import (
    MercerJobLibrary,
    MercerJobMapping,
    MercerMarketData,
)
from .base import BaseRepository
from job_pricing.exceptions import (
    VectorSearchException,
    DatabaseConnectionException,
    DataValidationException
)

logger = logging.getLogger(__name__)


class MercerRepository(BaseRepository[MercerJobLibrary]):
    """
    Repository for Mercer Job Library operations.

    Provides methods for querying Mercer jobs, performing vector similarity
    searches, and managing job mappings and market data.
    """

    def __init__(self, session: Session):
        """Initialize with Mercer Job Library model."""
        super().__init__(MercerJobLibrary, session)

    def get_by_job_code(self, job_code: str) -> Optional[MercerJobLibrary]:
        """
        Get a Mercer job by its unique job code.

        Args:
            job_code: Mercer job code (e.g., "HRM.04.005.M50")

        Returns:
            MercerJobLibrary instance or None if not found

        Example:
            job = repo.get_by_job_code("HRM.04.005.M50")
        """
        return self.get_one_by_filters(job_code=job_code)

    def get_by_family(
        self, family: str, skip: int = 0, limit: int = 100
    ) -> List[MercerJobLibrary]:
        """
        Get all jobs in a specific job family.

        Args:
            family: Job family name (e.g., "Human Resources Management")
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of MercerJobLibrary instances

        Example:
            hr_jobs = repo.get_by_family("Human Resources Management")
        """
        return (
            self.session.query(MercerJobLibrary)
            .filter(MercerJobLibrary.family == family)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_career_level(
        self, career_level: str, skip: int = 0, limit: int = 100
    ) -> List[MercerJobLibrary]:
        """
        Get all jobs at a specific career level.

        Args:
            career_level: Career level (e.g., "M3", "M4", "M5", "P1")
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of MercerJobLibrary instances

        Example:
            mid_level_jobs = repo.get_by_career_level("M4")
        """
        return (
            self.session.query(MercerJobLibrary)
            .filter(MercerJobLibrary.career_level == career_level)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_title(
        self, search_term: str, skip: int = 0, limit: int = 20
    ) -> List[MercerJobLibrary]:
        """
        Search Mercer jobs by title (case-insensitive partial match).

        Args:
            search_term: Term to search for in job title
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching MercerJobLibrary instances

        Example:
            analyst_jobs = repo.search_by_title("analyst")
        """
        return (
            self.session.query(MercerJobLibrary)
            .filter(MercerJobLibrary.job_title.ilike(f"%{search_term}%"))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def find_similar_by_embedding(
        self, embedding: List[float], limit: int = 10, threshold: float = 0.7
    ) -> List[Tuple[MercerJobLibrary, float]]:
        """
        Find similar jobs using vector similarity search (cosine similarity).

        This is the core semantic search function for matching user jobs
        to Mercer library jobs based on OpenAI embeddings.

        Args:
            embedding: OpenAI embedding vector (1536 dimensions)
            limit: Maximum number of similar jobs to return
            threshold: Minimum similarity score (0-1, where 1 is identical)

        Returns:
            List of tuples (MercerJobLibrary, similarity_score) ordered by similarity

        Raises:
            DataValidationException: If inputs are invalid
            DatabaseConnectionException: If database connection fails
            VectorSearchException: If vector search fails

        Example:
            # Get embedding from OpenAI for user's job description
            embedding = openai.embeddings.create(
                model="text-embedding-3-large",
                input=job_description
            ).data[0].embedding

            # Find similar Mercer jobs
            similar_jobs = repo.find_similar_by_embedding(embedding, limit=5)
            for job, score in similar_jobs:
                print(f"{job.job_title}: {score:.2%} match")

        Note:
            Requires pgvector extension to be installed in PostgreSQL.
            Uses cosine similarity (1 - cosine_distance).
        """
        try:
            # Validate inputs
            if not embedding or len(embedding) != 1536:
                raise DataValidationException(
                    "embedding",
                    f"Expected 1536-dimension vector, got {len(embedding) if embedding else 0}"
                )

            if threshold < 0 or threshold > 1:
                raise DataValidationException("threshold", "Must be between 0 and 1")

            if limit < 1 or limit > 1000:
                raise DataValidationException("limit", "Must be between 1 and 1000")

            logger.debug(f"Searching for similar jobs: limit={limit}, threshold={threshold}")

            # Convert Python list to PostgreSQL vector format
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

            # Use pgvector's cosine similarity operator (<=>)
            # Lower distance = more similar, so we use (1 - distance) as similarity
            query = text("""
                SELECT
                    *,
                    1 - (embedding <=> :embedding::vector) as similarity
                FROM mercer_job_library
                WHERE embedding IS NOT NULL
                    AND (1 - (embedding <=> :embedding::vector)) >= :threshold
                ORDER BY embedding <=> :embedding::vector
                LIMIT :limit
            """)

            try:
                results = self.session.execute(
                    query,
                    {"embedding": embedding_str, "threshold": threshold, "limit": limit},
                ).fetchall()

            except OperationalError as e:
                logger.error(f"Database connection error during vector search: {e}")
                raise DatabaseConnectionException(
                    "Failed to connect to database for vector similarity search",
                    original_error=e
                )

            except SQLAlchemyError as e:
                logger.error(f"Vector search query failed: {e}", exc_info=True)
                raise VectorSearchException(
                    "Vector search failed - check pgvector extension is installed",
                    original_error=e
                )

            # Convert results to (MercerJobLibrary, similarity) tuples
            similar_jobs = []
            for row in results:
                try:
                    # Reconstruct MercerJobLibrary object from row
                    job = self.session.query(MercerJobLibrary).filter(
                        MercerJobLibrary.id == row.id
                    ).first()

                    if job:  # Only add if job was found
                        similarity = float(row.similarity)
                        similar_jobs.append((job, similarity))
                    else:
                        logger.warning(f"Job with id {row.id} not found in follow-up query")

                except Exception as e:
                    logger.warning(f"Failed to process result row: {e}")
                    continue

            logger.debug(f"Found {len(similar_jobs)} similar jobs above threshold {threshold}")
            return similar_jobs

        except (DataValidationException, DatabaseConnectionException, VectorSearchException):
            # Re-raise known exceptions
            raise

        except Exception as e:
            logger.error(f"Unexpected error in find_similar_by_embedding: {e}", exc_info=True)
            raise VectorSearchException(
                f"Unexpected error during vector search: {str(e)}",
                original_error=e
            )

    def get_with_market_data(
        self, job_code: str, country_code: str = "SG"
    ) -> Optional[Tuple[MercerJobLibrary, List[MercerMarketData]]]:
        """
        Get a Mercer job with its associated market data.

        Args:
            job_code: Mercer job code
            country_code: Country code (default: Singapore)

        Returns:
            Tuple of (MercerJobLibrary, List of MercerMarketData) or None

        Example:
            job, market_data = repo.get_with_market_data("HRM.04.005.M50", "SG")
            if market_data:
                latest = market_data[0]
                print(f"P50 salary: {latest.p50} {latest.currency}")
        """
        job = self.get_by_job_code(job_code)
        if not job:
            return None

        market_data = (
            self.session.query(MercerMarketData)
            .filter(
                and_(
                    MercerMarketData.job_code == job_code,
                    MercerMarketData.country_code == country_code,
                )
            )
            .order_by(desc(MercerMarketData.survey_date))
            .all()
        )

        return (job, market_data)

    def get_job_mapping_by_request(
        self, request_id: UUID
    ) -> Optional[MercerJobMapping]:
        """
        Get the Mercer job mapping for a pricing request.

        Args:
            request_id: UUID of the job pricing request

        Returns:
            MercerJobMapping instance or None if not found

        Example:
            mapping = repo.get_job_mapping_by_request(request_id)
            if mapping:
                print(f"Matched to: {mapping.mercer_job.job_title}")
                print(f"Confidence: {mapping.confidence_score}")
        """
        return (
            self.session.query(MercerJobMapping)
            .filter(MercerJobMapping.request_id == request_id)
            .first()
        )

    def create_job_mapping(
        self,
        request_id: UUID,
        mercer_job_id: int,
        confidence_score: float,
        match_method: str = "semantic",
        **kwargs,
    ) -> MercerJobMapping:
        """
        Create a new job mapping between a user request and Mercer job.

        Args:
            request_id: UUID of the job pricing request
            mercer_job_id: ID of the Mercer job
            confidence_score: Match confidence (0.00-1.00)
            match_method: How the match was made (semantic, rule_based, hybrid, manual)
            **kwargs: Additional fields (semantic_similarity, title_similarity, etc.)

        Returns:
            Created MercerJobMapping instance

        Example:
            mapping = repo.create_job_mapping(
                request_id=request_id,
                mercer_job_id=best_match.id,
                confidence_score=0.92,
                match_method='semantic',
                semantic_similarity=0.92,
                title_similarity=0.85
            )
        """
        mapping = MercerJobMapping(
            request_id=request_id,
            mercer_job_id=mercer_job_id,
            confidence_score=confidence_score,
            match_method=match_method,
            **kwargs,
        )
        return self.create(mapping)

    def get_latest_market_data(
        self, job_code: str, country_code: str = "SG", industry: Optional[str] = None
    ) -> Optional[MercerMarketData]:
        """
        Get the most recent market data for a job.

        Args:
            job_code: Mercer job code
            country_code: Country code (default: Singapore)
            industry: Optional industry filter

        Returns:
            Latest MercerMarketData instance or None

        Example:
            latest = repo.get_latest_market_data("HRM.04.005.M50")
            if latest:
                print(f"P50: {latest.p50}, P75: {latest.p75}")
        """
        query = self.session.query(MercerMarketData).filter(
            and_(
                MercerMarketData.job_code == job_code,
                MercerMarketData.country_code == country_code,
            )
        )

        if industry:
            query = query.filter(MercerMarketData.industry == industry)

        return query.order_by(desc(MercerMarketData.survey_date)).first()

    def get_job_families(self) -> List[str]:
        """
        Get a list of all unique job families in the Mercer library.

        Returns:
            List of unique job family names

        Example:
            families = repo.get_job_families()
            # ['Human Resources Management', 'Finance & Accounting', ...]
        """
        results = (
            self.session.query(MercerJobLibrary.family)
            .distinct()
            .order_by(MercerJobLibrary.family)
            .all()
        )
        return [r[0] for r in results]

    def get_career_levels(self) -> List[str]:
        """
        Get a list of all unique career levels in the Mercer library.

        Returns:
            List of unique career level codes

        Example:
            levels = repo.get_career_levels()
            # ['M1', 'M2', 'M3', 'M4', 'M5', 'P1', 'P2', ...]
        """
        results = (
            self.session.query(MercerJobLibrary.career_level)
            .distinct()
            .filter(MercerJobLibrary.career_level.isnot(None))
            .order_by(MercerJobLibrary.career_level)
            .all()
        )
        return [r[0] for r in results]
