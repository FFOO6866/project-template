"""
SSG Skill Matching Service

Matches extracted skills from job descriptions to SSG TSC (Technical Skills & Competencies).

Uses multiple matching strategies:
1. Exact matching (normalized lowercase comparison)
2. Fuzzy matching (trigram similarity using PostgreSQL pg_trgm)
3. Semantic matching (future: using embeddings)
"""

import logging
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from job_pricing.repositories.ssg_repository import SSGRepository
from job_pricing.models import SSGTSC, JobSkillsExtracted

logger = logging.getLogger(__name__)


@dataclass
class SkillMatch:
    """
    Represents a matched skill with confidence score.

    Attributes:
        skill_name: Original skill name from extraction
        matched_tsc: Matched SSG TSC record (None if no match found)
        confidence: Match confidence score (0.0-1.0)
        match_method: Method used for matching (exact, fuzzy, semantic, manual)
        skill_category: Category of the skill
        is_core_skill: Whether this is a core skill for the job
    """

    skill_name: str
    matched_tsc: Optional[SSGTSC]
    confidence: float
    match_method: str
    skill_category: Optional[str] = None
    is_core_skill: bool = False

    @property
    def matched_tsc_code(self) -> Optional[str]:
        """Get TSC code of matched skill."""
        return self.matched_tsc.tsc_code if self.matched_tsc else None

    @property
    def matched_tsc_title(self) -> Optional[str]:
        """Get title of matched skill."""
        return self.matched_tsc.tsc_title if self.matched_tsc else None


class SkillMatchingService:
    """
    Service for matching extracted skills to SSG TSC taxonomy.

    Provides multiple matching strategies with configurable thresholds.
    Supports batch matching and automatic database persistence.
    """

    def __init__(
        self,
        session: Session,
        exact_match_threshold: float = 0.95,
        fuzzy_match_threshold: float = 0.3,
    ):
        """
        Initialize skill matching service.

        Args:
            session: SQLAlchemy database session
            exact_match_threshold: Minimum similarity for exact matches (default: 0.95)
            fuzzy_match_threshold: Minimum similarity for fuzzy matches (default: 0.3)
        """
        self.session = session
        self.repository = SSGRepository(session)
        self.exact_match_threshold = exact_match_threshold
        self.fuzzy_match_threshold = fuzzy_match_threshold

    def match_skill(
        self, skill_name: str, skill_category: Optional[str] = None
    ) -> SkillMatch:
        """
        Match a single skill to SSG TSC taxonomy.

        Tries multiple matching strategies in order:
        1. Exact match (normalized comparison)
        2. Fuzzy match (trigram similarity)
        3. No match (returns unmatched result)

        Args:
            skill_name: Skill name to match
            skill_category: Optional skill category hint

        Returns:
            SkillMatch with matched TSC or None if no match found

        Example:
            >>> service = SkillMatchingService(session)
            >>> match = service.match_skill("Python Programming")
            >>> print(f"{match.matched_tsc_title}: {match.confidence:.2%} confidence")
        """
        # Normalize skill name
        normalized_skill = skill_name.strip().lower()

        # Strategy 1: Try exact match with TSC title
        exact_match = self._exact_match(normalized_skill)
        if exact_match:
            return exact_match

        # Strategy 2: Try fuzzy match
        fuzzy_match = self._fuzzy_match(normalized_skill)
        if fuzzy_match:
            return fuzzy_match

        # No match found
        return SkillMatch(
            skill_name=skill_name,
            matched_tsc=None,
            confidence=0.0,
            match_method="none",
            skill_category=skill_category,
        )

    def match_skills_batch(
        self, skills: List[Tuple[str, Optional[str]]]
    ) -> List[SkillMatch]:
        """
        Match multiple skills to SSG TSC taxonomy.

        Args:
            skills: List of tuples (skill_name, skill_category)

        Returns:
            List of SkillMatch results

        Example:
            >>> skills = [("Python", "Programming"), ("SQL", "Database"), ("Leadership", "Soft Skills")]
            >>> matches = service.match_skills_batch(skills)
            >>> for match in matches:
            ...     print(f"{match.skill_name} -> {match.matched_tsc_title}")
        """
        matches = []
        for skill_name, skill_category in skills:
            match = self.match_skill(skill_name, skill_category)
            matches.append(match)
        return matches

    def save_matched_skills(
        self, request_id: UUID, matches: List[SkillMatch]
    ) -> List[JobSkillsExtracted]:
        """
        Save matched skills to database.

        Creates JobSkillsExtracted records for each matched skill.

        Args:
            request_id: UUID of the job pricing request
            matches: List of SkillMatch results

        Returns:
            List of created JobSkillsExtracted instances

        Example:
            >>> matches = service.match_skills_batch(skills)
            >>> saved = service.save_matched_skills(request_id, matches)
            >>> print(f"Saved {len(saved)} skills to database")
        """
        saved_skills = []

        for match in matches:
            extracted_skill = self.repository.create_extracted_skill(
                request_id=request_id,
                skill_name=match.skill_name,
                skill_category=match.skill_category,
                matched_tsc_code=match.matched_tsc_code,
                match_confidence=match.confidence,
                match_method=match.match_method,
                is_core_skill=match.is_core_skill,
            )
            saved_skills.append(extracted_skill)

        # Commit all at once
        self.session.commit()
        return saved_skills

    def get_matched_skills(self, request_id: UUID) -> List[JobSkillsExtracted]:
        """
        Retrieve all matched skills for a job pricing request.

        Args:
            request_id: UUID of the job pricing request

        Returns:
            List of JobSkillsExtracted instances ordered by confidence

        Example:
            >>> skills = service.get_matched_skills(request_id)
            >>> for skill in skills:
            ...     print(f"{skill.skill_name}: {skill.match_confidence:.2%}")
        """
        return self.repository.get_extracted_skills_by_request(request_id)

    def _exact_match(self, normalized_skill: str) -> Optional[SkillMatch]:
        """
        Try to find an exact match for a skill.

        Compares normalized lowercase strings.

        Args:
            normalized_skill: Lowercased, stripped skill name

        Returns:
            SkillMatch if found, None otherwise
        """
        # Search for skills with similar title
        candidates = self.repository.search_tsc_by_title(normalized_skill, limit=5)

        for candidate in candidates:
            normalized_candidate = candidate.tsc_title.strip().lower()

            # Check for exact match
            if normalized_candidate == normalized_skill:
                return SkillMatch(
                    skill_name=normalized_skill,
                    matched_tsc=candidate,
                    confidence=1.0,
                    match_method="exact",
                    skill_category=candidate.skill_category,
                )

            # Check for very close match (>95% similarity after normalization)
            if self._string_similarity(normalized_skill, normalized_candidate) >= self.exact_match_threshold:
                return SkillMatch(
                    skill_name=normalized_skill,
                    matched_tsc=candidate,
                    confidence=0.95,
                    match_method="exact",
                    skill_category=candidate.skill_category,
                )

        return None

    def _fuzzy_match(self, normalized_skill: str) -> Optional[SkillMatch]:
        """
        Try to find a fuzzy match using trigram similarity.

        Uses PostgreSQL pg_trgm extension for similarity search.

        Args:
            normalized_skill: Lowercased, stripped skill name

        Returns:
            SkillMatch if found with sufficient confidence, None otherwise
        """
        try:
            # Use repository's fuzzy search (trigram similarity)
            fuzzy_matches = self.repository.search_skills_fuzzy(
                normalized_skill,
                threshold=self.fuzzy_match_threshold,
                limit=5,
            )

            if not fuzzy_matches:
                return None

            # Take best match
            best_match, similarity = fuzzy_matches[0]

            # Adjust confidence score (trigram similarity is already 0-1)
            confidence = similarity

            return SkillMatch(
                skill_name=normalized_skill,
                matched_tsc=best_match,
                confidence=confidence,
                match_method="fuzzy",
                skill_category=best_match.skill_category,
            )

        except Exception as e:
            # If fuzzy search fails (e.g., pg_trgm not installed), fall back gracefully
            logger.warning(f"Fuzzy matching failed: {e}")
            return None

    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate simple string similarity (Levenshtein-based).

        Fallback method when trigram similarity is not available.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score (0.0-1.0)
        """
        # Simple implementation: ratio of common characters
        # In production, use python-Levenshtein or similar
        if s1 == s2:
            return 1.0

        longer = s1 if len(s1) > len(s2) else s2
        shorter = s2 if len(s1) > len(s2) else s1

        if len(longer) == 0:
            return 1.0

        # Count common characters (very simple approximation)
        common = sum(1 for c in shorter if c in longer)
        return common / len(longer)

    def get_statistics(self) -> Dict[str, any]:
        """
        Get statistics about skill matching.

        Returns:
            Dictionary with:
            - total_tsc_count: Total number of TSC skills in database
            - sectors: List of all sectors
            - categories: List of all skill categories
            - most_common_categories: Top skill categories

        Example:
            >>> stats = service.get_statistics()
            >>> print(f"Total skills in database: {stats['total_tsc_count']}")
        """
        # Count total TSC skills
        total_tsc = self.session.query(SSGTSC).count()

        # Get all sectors
        sectors = self.repository.get_all_sectors()

        # Get all skill categories
        categories_query = (
            self.session.query(SSGTSC.skill_category)
            .distinct()
            .order_by(SSGTSC.skill_category)
            .all()
        )
        categories = [c[0] for c in categories_query if c[0]]

        # Get most common categories
        most_common_query = (
            self.session.query(SSGTSC.skill_category, SSGTSC.skill_category)
            .group_by(SSGTSC.skill_category)
            .order_by(SSGTSC.skill_category.desc())
            .limit(10)
            .all()
        )
        most_common_categories = [c[0] for c in most_common_query if c[0]]

        return {
            "total_tsc_count": total_tsc,
            "sectors": sectors,
            "skill_categories": categories,
            "most_common_categories": most_common_categories,
        }
