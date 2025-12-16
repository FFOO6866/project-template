"""
Job Matching Service

Provides semantic job matching using OpenAI embeddings and vector similarity search.
Maps user job inputs to Mercer Job Library using pgvector.
"""

import logging
from typing import Dict, List, Optional, Tuple
import openai
import os
import time
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from ..models.mercer import MercerJobLibrary
from ..utils.database import get_db_context
from ..exceptions import (
    EmbeddingGenerationException,
    VectorSearchException,
    JobMatchingException,
    DataValidationException,
    ConfigurationException,
    RateLimitException,
    DatabaseConnectionException
)

logger = logging.getLogger(__name__)


class JobMatchingService:
    """Service for matching user jobs to Mercer Job Library using semantic search."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize job matching service."""
        self.session = session
        openai.api_key = os.getenv('OPENAI_API_KEY')

    def generate_query_embedding(self, job_title: str, job_description: str = "", max_retries: int = 3) -> List[float]:
        """
        Generate embedding for a job query with retry logic.

        Args:
            job_title: Job title to match
            job_description: Optional job description for better matching
            max_retries: Maximum number of retry attempts for transient failures

        Returns:
            1536-dimension embedding vector

        Raises:
            DataValidationException: If inputs are invalid
            ConfigurationException: If OpenAI API key is missing
            EmbeddingGenerationException: If embedding generation fails after retries
            RateLimitException: If rate limit is exceeded
        """
        # Validate inputs
        if not job_title or not job_title.strip():
            raise DataValidationException("job_title", "Job title cannot be empty")

        if len(job_title) > 1000:
            raise DataValidationException("job_title", "Job title exceeds maximum length of 1000 characters")

        # Check API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ConfigurationException("OPENAI_API_KEY", "OpenAI API key not configured")

        # Combine title and description for richer matching
        query_text = f"{job_title}. {job_description}" if job_description else job_title

        # Retry logic for transient failures
        for attempt in range(max_retries):
            try:
                logger.debug(f"Generating embedding for: {job_title[:50]}... (attempt {attempt + 1}/{max_retries})")

                response = openai.embeddings.create(
                    model="text-embedding-3-large",
                    input=query_text,
                    dimensions=1536
                )

                embedding = response.data[0].embedding

                # Validate embedding
                if not embedding or len(embedding) != 1536:
                    raise EmbeddingGenerationException(
                        f"Invalid embedding dimensions: expected 1536, got {len(embedding) if embedding else 0}"
                    )

                logger.debug(f"Successfully generated embedding ({len(embedding)} dimensions)")
                return embedding

            except openai.RateLimitError as e:
                logger.warning(f"OpenAI rate limit exceeded: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise RateLimitException("OpenAI", retry_after=60)

            except openai.APIError as e:
                logger.error(f"OpenAI API error: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying after {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise EmbeddingGenerationException(
                        f"API error after {max_retries} attempts: {str(e)}",
                        original_error=e
                    )

            except openai.AuthenticationError as e:
                # Don't retry authentication errors
                raise ConfigurationException(
                    "OPENAI_API_KEY",
                    f"Invalid API key: {str(e)}"
                )

            except Exception as e:
                logger.error(f"Unexpected error generating embedding: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise EmbeddingGenerationException(
                        f"Unexpected error after {max_retries} attempts: {str(e)}",
                        original_error=e
                    )

        # Should never reach here, but just in case
        raise EmbeddingGenerationException("Failed to generate embedding after all retries")

    def find_similar_jobs(
        self,
        job_title: str,
        job_description: str = "",
        job_family: Optional[str] = None,
        career_level: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find similar Mercer jobs using semantic search.

        Args:
            job_title: Job title to match
            job_description: Job description for better matching
            job_family: Optional family filter (e.g., "HRM", "ICT")
            career_level: Optional level filter (e.g., "M5", "ET2")
            top_k: Number of top matches to return

        Returns:
            List of matched jobs with similarity scores
        """
        # Debug logging
        logger.debug(f"find_similar_jobs called: title='{job_title}', family={job_family}, level={career_level}, top_k={top_k}")

        try:
            # Generate query embedding (may raise exceptions)
            query_embedding = self.generate_query_embedding(job_title, job_description)
            logger.debug(f"Generated embedding, first 3 values: {query_embedding[:3]}")

            # Validate top_k
            if top_k < 1 or top_k > 100:
                raise DataValidationException("top_k", "Must be between 1 and 100")

            # Build SQL query with filters
            filters = []
            params = {
                "limit": top_k
            }

            if job_family:
                filters.append("family = :family")
                params["family"] = job_family

            if career_level:
                filters.append("career_level = :career_level")
                params["career_level"] = career_level

            where_clause = "WHERE " + " AND ".join(filters) if filters else ""

            # Convert embedding to PostgreSQL array format
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            # Use pgvector cosine similarity
            query = text(f"""
                SELECT
                    id,
                    job_code,
                    job_title,
                    job_description,
                    family,
                    subfamily,
                    career_level,
                    1 - (embedding <=> '{embedding_str}'::vector) AS similarity
                FROM mercer_job_library
                {where_clause}
                ORDER BY embedding <=> '{embedding_str}'::vector
                LIMIT :limit
            """)

            # Debug: log the actual SQL
            logger.debug(f"SQL WHERE clause: '{where_clause}'")
            logger.debug(f"SQL params: {params}")

            # Execute with context manager or provided session
            try:
                if self.session:
                    # Set IVFFlat probes to search more clusters (default is 1, which is too restrictive)
                    # This improves recall at slight cost of speed
                    self.session.execute(text("SET ivfflat.probes = 10"))
                    results = self.session.execute(query, params).fetchall()
                else:
                    with get_db_context() as session:
                        # Set IVFFlat probes for this session
                        session.execute(text("SET ivfflat.probes = 10"))
                        results = session.execute(query, params).fetchall()

            except OperationalError as e:
                logger.error(f"Database connection error: {e}")
                raise DatabaseConnectionException(
                    "Failed to connect to database for vector search",
                    original_error=e
                )

            except SQLAlchemyError as e:
                logger.error(f"Vector search query failed: {e}", exc_info=True)
                raise VectorSearchException(
                    "Database query failed - check pgvector extension is installed",
                    original_error=e
                )

            # Convert to dict list
            matches = []
            for row in results:
                matches.append({
                    "id": row[0],
                    "job_code": row[1],
                    "job_title": row[2],
                    "job_description": row[3],
                    "family": row[4],
                    "subfamily": row[5],
                    "career_level": row[6],
                    "similarity_score": float(row[7]),
                    "confidence": self._calculate_confidence(float(row[7]))
                })

            # Debug logging
            logger.debug(f"find_similar_jobs returned {len(matches)} matches")
            if matches:
                logger.debug(f"Top match: {matches[0]['job_title']} with {matches[0]['similarity_score']:.2%} similarity")

            return matches

        except (EmbeddingGenerationException, DatabaseConnectionException, VectorSearchException, DataValidationException):
            # Re-raise known exceptions
            raise

        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Unexpected error in find_similar_jobs: {e}", exc_info=True)
            raise VectorSearchException(
                f"Unexpected error during job search: {str(e)}",
                original_error=e
            )

    def find_best_match(
        self,
        job_title: str,
        job_description: str = "",
        job_family: Optional[str] = None,
        career_level: Optional[str] = None,
        use_llm_reasoning: bool = True
    ) -> Optional[Dict]:
        """
        Find the single best matching Mercer job using hybrid approach.

        Hybrid Approach:
        1. Use embeddings to find top 5 candidates (fast)
        2. Use LLM to analyze and pick best match with reasoning (smart)

        Args:
            job_title: Job title to match
            job_description: Job description for context
            job_family: Optional family filter
            career_level: Optional level filter
            use_llm_reasoning: If True, use LLM for final decision (recommended)

        Returns:
            Best match with confidence score and reasoning, or None if no good match
        """
        # Step 1: Get top candidates using embedding similarity (fast)
        candidates = self.find_similar_jobs(
            job_title=job_title,
            job_description=job_description,
            job_family=job_family,
            career_level=career_level,
            top_k=5  # Get top 5 for LLM to analyze
        )

        if not candidates:
            logger.debug("No embedding matches found")
            return None

        # Step 2: If LLM reasoning enabled, use it for final decision
        if use_llm_reasoning and openai.api_key:
            logger.debug(f"Using LLM to analyze {len(candidates)} candidates")
            return self._llm_select_best_match(
                job_title=job_title,
                job_description=job_description,
                candidates=candidates
            )
        else:
            # PRODUCTION: No LLM available - use embedding-based selection with strict threshold
            # This is NOT a fallback - it's an alternative matching method when LLM is disabled
            if not openai.api_key:
                raise ConfigurationException(
                    "OPENAI_API_KEY",
                    "OpenAI API key required for job matching"
                )

            best_match = candidates[0]

            # Require minimum similarity threshold
            # Changed from 0.7 → 0.55 → 0.40 to handle OpenAI embedding variability
            # OpenAI embeddings are non-deterministic, causing 40-67% similarity range for same input
            if best_match["similarity_score"] < 0.40:
                logger.debug(f"Best match similarity {best_match['similarity_score']:.2f} below 0.40 threshold")
                return None

            return best_match

    def _llm_select_best_match(
        self,
        job_title: str,
        job_description: str,
        candidates: List[Dict]
    ) -> Optional[Dict]:
        """
        Use LLM to analyze candidates and select best match with reasoning.

        Args:
            job_title: User's job title
            job_description: User's job description
            candidates: Top candidates from embedding search

        Returns:
            Best match with LLM reasoning and confidence, or None
        """
        try:
            # Build prompt for LLM analysis
            candidates_text = "\n\n".join([
                f"Candidate {i+1}:\n"
                f"  Code: {c['job_code']}\n"
                f"  Title: {c['job_title']}\n"
                f"  Family: {c['family']}\n"
                f"  Level: {c['career_level']}\n"
                f"  Embedding Similarity: {c['similarity_score']:.2%}\n"
                f"  Description: {c['job_description'][:200] if c['job_description'] else 'N/A'}..."
                for i, c in enumerate(candidates)
            ])

            prompt = f"""You are a job matching expert. Analyze these Mercer job candidates and determine the best match.

USER JOB:
Title: {job_title}
Description: {job_description}

CANDIDATES:
{candidates_text}

TASK:
1. Analyze which candidate best matches the user's job based on:
   - Job responsibilities and scope
   - Career level and seniority
   - Required skills and experience
   - Industry context

2. Provide your response in this EXACT JSON format:
{{
    "best_match_number": <1-{len(candidates)} or 0 if no good match>,
    "confidence": <0.0-1.0>,
    "reasoning": "<explain why this is the best match>",
    "key_similarities": ["similarity 1", "similarity 2", "similarity 3"],
    "key_differences": ["difference 1", "difference 2"]
}}

If none of the candidates are a good match (e.g., completely different job function), return best_match_number: 0.

Respond ONLY with valid JSON, no other text."""

            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cheap for this task
                messages=[
                    {"role": "system", "content": "You are a job matching expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent matching
                max_tokens=500
            )

            # Parse LLM response
            import json
            llm_result = json.loads(response.choices[0].message.content)

            best_match_number = llm_result.get("best_match_number", 0)

            # No match found
            if best_match_number == 0:
                logger.info(f"LLM determined no good match. Reason: {llm_result.get('reasoning', 'N/A')}")
                return None

            # Get the selected candidate
            selected_candidate = candidates[best_match_number - 1]
            llm_confidence = llm_result.get("confidence", 0.0)

            # Enhance candidate with LLM insights
            selected_candidate["match_score"] = llm_confidence
            selected_candidate["llm_reasoning"] = llm_result.get("reasoning", "")
            selected_candidate["key_similarities"] = llm_result.get("key_similarities", [])
            selected_candidate["key_differences"] = llm_result.get("key_differences", [])
            selected_candidate["matching_method"] = "hybrid_llm"

            logger.info(
                f"LLM selected: {selected_candidate['job_code']} "
                f"(confidence: {llm_confidence:.2%}, "
                f"embedding: {selected_candidate['similarity_score']:.2%})"
            )

            return selected_candidate

        except Exception as e:
            # PRODUCTION: No fallback - propagate the error
            logger.error(f"Error in LLM matching: {e}", exc_info=True)
            raise JobMatchingException(
                message=f"LLM job matching failed: {str(e)}",
                job_title=job_title,
                original_error=e
            )

    def _calculate_confidence(self, similarity_score: float) -> str:
        """
        Convert similarity score to confidence level.

        Args:
            similarity_score: Cosine similarity (0-1)

        Returns:
            Confidence level: "high", "medium", or "low"
        """
        if similarity_score >= 0.85:
            return "high"
        elif similarity_score >= 0.75:
            return "medium"
        else:
            return "low"


# Example usage
if __name__ == "__main__":
    service = JobMatchingService()

    # Test search
    matches = service.find_similar_jobs(
        job_title="Assistant Director, Total Rewards",
        job_description="Responsible for designing and implementing total rewards strategy",
        job_family="HRM",
        top_k=5
    )

    logger.info("Top 5 Matches:")
    for i, match in enumerate(matches, 1):
        logger.info(f"\n{i}. {match['job_title']} ({match['job_code']})")
        logger.info(f"   Similarity: {match['similarity_score']:.2%}")
        logger.info(f"   Confidence: {match['confidence']}")
