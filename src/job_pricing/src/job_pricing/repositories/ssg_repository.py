"""
SSG Repository

Provides data access for SSG Skills Framework, TSC (Technical Skills & Competencies),
and job role-skill mappings. Includes fuzzy matching for skill discovery.
"""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func, text

from job_pricing.models import (
    SSGSkillsFramework,
    SSGTSC,
    SSGJobRoleTSCMapping,
    JobSkillsExtracted,
)
from .base import BaseRepository


class SSGRepository(BaseRepository[SSGSkillsFramework]):
    """
    Repository for SSG Skills Framework operations.

    Provides methods for querying Singapore's SkillsFuture Framework,
    including job roles, technical skills, and fuzzy skill matching.
    """

    def __init__(self, session: Session):
        """Initialize with SSG Skills Framework model."""
        super().__init__(SSGSkillsFramework, session)

    def get_by_job_role_code(self, job_role_code: str) -> Optional[SSGSkillsFramework]:
        """
        Get a job role by its unique code.

        Args:
            job_role_code: SSG job role code (e.g., "ICT-DIS-5016-1.1")

        Returns:
            SSGSkillsFramework instance or None if not found

        Example:
            job_role = repo.get_by_job_role_code("ICT-DIS-5016-1.1")
        """
        return self.get_one_by_filters(job_role_code=job_role_code)

    def get_by_sector(
        self, sector: str, skip: int = 0, limit: int = 100
    ) -> List[SSGSkillsFramework]:
        """
        Get all job roles in a specific sector.

        Args:
            sector: Sector name (e.g., "Information and Communications Technology")
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of SSGSkillsFramework instances

        Example:
            ict_roles = repo.get_by_sector("Information and Communications Technology")
        """
        return (
            self.session.query(SSGSkillsFramework)
            .filter(SSGSkillsFramework.sector == sector)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_track(
        self, track: str, skip: int = 0, limit: int = 100
    ) -> List[SSGSkillsFramework]:
        """
        Get all job roles in a specific track.

        Args:
            track: Track name (e.g., "Data & AI", "Software Development")
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of SSGSkillsFramework instances

        Example:
            data_roles = repo.get_by_track("Data & AI")
        """
        return (
            self.session.query(SSGSkillsFramework)
            .filter(SSGSkillsFramework.track == track)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_job_role(
        self, search_term: str, skip: int = 0, limit: int = 20
    ) -> List[SSGSkillsFramework]:
        """
        Search job roles by title (case-insensitive partial match).

        Args:
            search_term: Term to search for in job role title
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching SSGSkillsFramework instances

        Example:
            analyst_roles = repo.search_by_job_role("analyst")
        """
        return (
            self.session.query(SSGSkillsFramework)
            .filter(SSGSkillsFramework.job_role_title.ilike(f"%{search_term}%"))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_skills_for_job_role(
        self, job_role_code: str
    ) -> List[Tuple[SSGTSC, SSGJobRoleTSCMapping]]:
        """
        Get all skills (TSC) required for a specific job role.

        Args:
            job_role_code: SSG job role code

        Returns:
            List of tuples (SSGTSC, SSGJobRoleTSCMapping) with skill and proficiency info

        Example:
            skills = repo.get_skills_for_job_role("ICT-DIS-5016-1.1")
            for skill, mapping in skills:
                print(f"{skill.skill_title}: {mapping.proficiency_level}")
        """
        results = (
            self.session.query(SSGTSC, SSGJobRoleTSCMapping)
            .join(
                SSGJobRoleTSCMapping,
                SSGTSC.tsc_code == SSGJobRoleTSCMapping.tsc_code,
            )
            .filter(SSGJobRoleTSCMapping.job_role_code == job_role_code)
            .all()
        )
        return results

    def search_skills_fuzzy(
        self, skill_text: str, threshold: float = 0.2, limit: int = 20
    ) -> List[Tuple[SSGTSC, float]]:
        """
        Fuzzy search for skills using trigram similarity.

        Uses PostgreSQL pg_trgm extension for fuzzy text matching.
        Useful for matching user-provided skills to SSG taxonomy.

        Args:
            skill_text: Skill description to search for
            threshold: Minimum similarity score (0-1, default 0.2)
            limit: Maximum number of results

        Returns:
            List of tuples (SSGTSC, similarity_score) ordered by similarity

        Example:
            matches = repo.search_skills_fuzzy("python programming", threshold=0.3)
            for skill, score in matches:
                print(f"{skill.skill_title}: {score:.2%} match")

        Note:
            Requires pg_trgm extension to be installed in PostgreSQL.
        """
        query = text("""
            SELECT
                *,
                similarity(tsc_title, :skill_text) as sim_score
            FROM ssg_tsc
            WHERE similarity(tsc_title, :skill_text) >= :threshold
            ORDER BY sim_score DESC
            LIMIT :limit
        """)

        results = self.session.execute(
            query,
            {"skill_text": skill_text, "threshold": threshold, "limit": limit},
        ).fetchall()

        # Convert results to (SSGTSC, similarity) tuples
        fuzzy_matches = []
        for row in results:
            skill = (
                self.session.query(SSGTSC)
                .filter(SSGTSC.tsc_code == row.tsc_code)
                .first()
            )
            similarity = float(row.sim_score)
            fuzzy_matches.append((skill, similarity))

        return fuzzy_matches

    def get_job_roles_by_skill(
        self, tsc_code: str, skip: int = 0, limit: int = 100
    ) -> List[Tuple[SSGSkillsFramework, SSGJobRoleTSCMapping]]:
        """
        Get all job roles that require a specific skill.

        Args:
            tsc_code: SSG TSC code
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of tuples (SSGSkillsFramework, SSGJobRoleTSCMapping)

        Example:
            roles = repo.get_job_roles_by_skill("ICT-DIS-5016-1")
            for job_role, mapping in roles:
                print(f"{job_role.job_role_title} requires {mapping.proficiency_level}")
        """
        return (
            self.session.query(SSGSkillsFramework, SSGJobRoleTSCMapping)
            .join(
                SSGJobRoleTSCMapping,
                SSGSkillsFramework.job_role_code
                == SSGJobRoleTSCMapping.job_role_code,
            )
            .filter(SSGJobRoleTSCMapping.tsc_code == tsc_code)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_extracted_skills_by_request(
        self, request_id: UUID
    ) -> List[JobSkillsExtracted]:
        """
        Get all skills extracted from a job pricing request.

        Args:
            request_id: UUID of the job pricing request

        Returns:
            List of JobSkillsExtracted instances

        Example:
            skills = repo.get_extracted_skills_by_request(request_id)
            for skill in skills:
                print(f"{skill.skill_name}: {skill.confidence_score}")
        """
        return (
            self.session.query(JobSkillsExtracted)
            .filter(JobSkillsExtracted.request_id == request_id)
            .order_by(desc(JobSkillsExtracted.confidence_score))
            .all()
        )

    def create_extracted_skill(
        self,
        request_id: UUID,
        skill_name: str,
        matched_tsc_code: Optional[str] = None,
        match_confidence: float = 1.0,
        **kwargs,
    ) -> JobSkillsExtracted:
        """
        Create a new extracted skill record.

        Args:
            request_id: UUID of the job pricing request
            skill_name: Name of the extracted skill
            matched_tsc_code: Optional SSG TSC code if mapped
            match_confidence: Match confidence (0.00-1.00)
            **kwargs: Additional fields (match_method, skill_category, etc.)

        Returns:
            Created JobSkillsExtracted instance

        Example:
            skill = repo.create_extracted_skill(
                request_id=request_id,
                skill_name="Python",
                matched_tsc_code="ICT-DIS-5016-1",
                match_confidence=0.95,
                match_method='exact',
                skill_category='Programming Language'
            )
        """
        extracted_skill = JobSkillsExtracted(
            request_id=request_id,
            skill_name=skill_name,
            matched_tsc_code=matched_tsc_code,
            match_confidence=match_confidence,
            **kwargs,
        )
        return self.create(extracted_skill)

    def get_all_sectors(self) -> List[str]:
        """
        Get a list of all unique sectors in the SSG framework.

        Returns:
            List of unique sector names

        Example:
            sectors = repo.get_all_sectors()
            # ['Information and Communications Technology', 'Financial Services', ...]
        """
        results = (
            self.session.query(SSGSkillsFramework.sector)
            .distinct()
            .order_by(SSGSkillsFramework.sector)
            .all()
        )
        return [r[0] for r in results if r[0]]

    def get_all_tracks(self, sector: Optional[str] = None) -> List[str]:
        """
        Get a list of all unique tracks, optionally filtered by sector.

        Args:
            sector: Optional sector name to filter by

        Returns:
            List of unique track names

        Example:
            all_tracks = repo.get_all_tracks()
            ict_tracks = repo.get_all_tracks(sector="Information and Communications Technology")
        """
        query = self.session.query(SSGSkillsFramework.track).distinct()

        if sector:
            query = query.filter(SSGSkillsFramework.sector == sector)

        results = query.order_by(SSGSkillsFramework.track).all()
        return [r[0] for r in results if r[0]]

    def get_tsc_by_code(self, tsc_code: str) -> Optional[SSGTSC]:
        """
        Get a TSC (Technical Skill & Competency) by its code.

        Args:
            tsc_code: SSG TSC code

        Returns:
            SSGTSC instance or None if not found

        Example:
            skill = repo.get_tsc_by_code("ICT-DIS-5016-1")
        """
        return (
            self.session.query(SSGTSC).filter(SSGTSC.tsc_code == tsc_code).first()
        )

    def search_tsc_by_title(
        self, search_term: str, skip: int = 0, limit: int = 20
    ) -> List[SSGTSC]:
        """
        Search TSC by skill title (case-insensitive partial match).

        Args:
            search_term: Term to search for in skill title
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching SSGTSC instances

        Example:
            python_skills = repo.search_tsc_by_title("python")
        """
        return (
            self.session.query(SSGTSC)
            .filter(SSGTSC.tsc_title.ilike(f"%{search_term}%"))
            .offset(skip)
            .limit(limit)
            .all()
        )
