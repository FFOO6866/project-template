"""
Scraping Repository

Provides data access for scraped job listings, company data, and scraping audit logs.
Handles data from MyCareersFuture (MCF) and Glassdoor sources.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func, text

from job_pricing.models import (
    ScrapedJobListing,
    ScrapedCompanyData,
    ScrapingAuditLog,
)
from .base import BaseRepository


class ScrapingRepository(BaseRepository[ScrapedJobListing]):
    """
    Repository for scraped job listing operations.

    Provides methods for querying job listings from MCF and Glassdoor,
    company data aggregation, and scraping audit logs.
    """

    def __init__(self, session: Session):
        """Initialize with Scraped Job Listing model."""
        super().__init__(ScrapedJobListing, session)

    def get_active_listings(
        self,
        days: int = 30,
        source: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ScrapedJobListing]:
        """
        Get active job listings (posted within specified days).

        Args:
            days: Number of days to look back (default: 30)
            source: Optional source filter ('mcf' or 'glassdoor')
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active ScrapedJobListing instances

        Example:
            recent_jobs = repo.get_active_listings(days=7)
            mcf_jobs = repo.get_active_listings(days=30, source='mcf')
        """
        since = datetime.now() - timedelta(days=days)
        query = self.session.query(ScrapedJobListing).filter(
            ScrapedJobListing.posted_date >= since
        )

        if source:
            query = query.filter(ScrapedJobListing.source == source)

        return (
            query.order_by(desc(ScrapedJobListing.posted_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_title(
        self,
        search_term: str,
        source: Optional[str] = None,
        location: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[ScrapedJobListing]:
        """
        Search job listings by title (case-insensitive partial match).

        Args:
            search_term: Term to search for in job title
            source: Optional source filter
            location: Optional location filter (case-insensitive partial match)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching ScrapedJobListing instances

        Example:
            analyst_jobs = repo.search_by_title("analyst", location="Singapore")
        """
        query = self.session.query(ScrapedJobListing).filter(
            ScrapedJobListing.job_title.ilike(f"%{search_term}%")
        )

        if source:
            query = query.filter(ScrapedJobListing.source == source)

        if location:
            query = query.filter(ScrapedJobListing.location.ilike(f"%{location}%"))

        return (
            query.order_by(desc(ScrapedJobListing.posted_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_company(
        self, company_name: str, skip: int = 0, limit: int = 100
    ) -> List[ScrapedJobListing]:
        """
        Get all job listings from a specific company.

        Args:
            company_name: Company name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ScrapedJobListing instances

        Example:
            company_jobs = repo.get_by_company("Google Singapore")
        """
        return (
            self.session.query(ScrapedJobListing)
            .filter(ScrapedJobListing.company_name.ilike(f"%{company_name}%"))
            .order_by(desc(ScrapedJobListing.posted_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_location(
        self, location: str, skip: int = 0, limit: int = 100
    ) -> List[ScrapedJobListing]:
        """
        Get all job listings in a specific location.

        Args:
            location: Location name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ScrapedJobListing instances

        Example:
            cbd_jobs = repo.get_by_location("Singapore CBD")
        """
        return (
            self.session.query(ScrapedJobListing)
            .filter(ScrapedJobListing.location.ilike(f"%{location}%"))
            .order_by(desc(ScrapedJobListing.posted_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_with_salary_data(
        self,
        min_salary: Optional[float] = None,
        max_salary: Optional[float] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ScrapedJobListing]:
        """
        Get job listings with salary data, optionally filtered by salary range.

        Args:
            min_salary: Minimum salary filter
            max_salary: Maximum salary filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ScrapedJobListing instances with salary data

        Example:
            mid_range = repo.get_with_salary_data(min_salary=4000, max_salary=8000)
        """
        query = self.session.query(ScrapedJobListing).filter(
            or_(
                ScrapedJobListing.salary_min.isnot(None),
                ScrapedJobListing.salary_max.isnot(None),
            )
        )

        if min_salary:
            query = query.filter(
                or_(
                    ScrapedJobListing.salary_min >= min_salary,
                    ScrapedJobListing.salary_max >= min_salary,
                )
            )

        if max_salary:
            query = query.filter(
                or_(
                    ScrapedJobListing.salary_min <= max_salary,
                    ScrapedJobListing.salary_max <= max_salary,
                )
            )

        return (
            query.order_by(desc(ScrapedJobListing.posted_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_skills(
        self, skills: List[str], match_all: bool = False, skip: int = 0, limit: int = 20
    ) -> List[ScrapedJobListing]:
        """
        Search job listings by required skills.

        Args:
            skills: List of skills to search for
            match_all: If True, require all skills; if False, match any skill
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching ScrapedJobListing instances

        Example:
            python_jobs = repo.search_by_skills(["Python", "SQL"])
            all_skills = repo.search_by_skills(["Python", "SQL"], match_all=True)
        """
        query = self.session.query(ScrapedJobListing)

        if match_all:
            # All skills must be present
            for skill in skills:
                query = query.filter(
                    func.lower(func.cast(ScrapedJobListing.skills, text("text"))).like(
                        f"%{skill.lower()}%"
                    )
                )
        else:
            # Any skill matches
            conditions = [
                func.lower(func.cast(ScrapedJobListing.skills, text("text"))).like(
                    f"%{skill.lower()}%"
                )
                for skill in skills
            ]
            query = query.filter(or_(*conditions))

        return (
            query.order_by(desc(ScrapedJobListing.posted_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_salary_statistics(
        self,
        job_title_pattern: Optional[str] = None,
        location: Optional[str] = None,
        days: int = 90,
    ) -> Dict[str, Any]:
        """
        Get salary statistics for job listings.

        Args:
            job_title_pattern: Optional job title filter (ILIKE pattern)
            location: Optional location filter
            days: Number of days to look back (default: 90)

        Returns:
            Dictionary with salary statistics:
            - count: Number of listings with salary data
            - avg_min: Average minimum salary
            - avg_max: Average maximum salary
            - median_min: Median minimum salary
            - median_max: Median maximum salary
            - p25_min, p75_min: 25th and 75th percentile minimum
            - p25_max, p75_max: 25th and 75th percentile maximum

        Example:
            stats = repo.get_salary_statistics(
                job_title_pattern="%analyst%",
                location="Singapore"
            )
            print(f"Average salary range: {stats['avg_min']} - {stats['avg_max']}")
        """
        since = datetime.now() - timedelta(days=days)

        query = self.session.query(ScrapedJobListing).filter(
            and_(
                ScrapedJobListing.posted_date >= since,
                or_(
                    ScrapedJobListing.salary_min.isnot(None),
                    ScrapedJobListing.salary_max.isnot(None),
                ),
            )
        )

        if job_title_pattern:
            query = query.filter(
                ScrapedJobListing.job_title.ilike(job_title_pattern)
            )

        if location:
            query = query.filter(ScrapedJobListing.location.ilike(f"%{location}%"))

        listings = query.all()

        if not listings:
            return {
                "count": 0,
                "avg_min": None,
                "avg_max": None,
                "median_min": None,
                "median_max": None,
                "p25_min": None,
                "p75_min": None,
                "p25_max": None,
                "p75_max": None,
            }

        # Extract salary values
        min_salaries = [
            listing.salary_min for listing in listings if listing.salary_min
        ]
        max_salaries = [
            listing.salary_max for listing in listings if listing.salary_max
        ]

        # Calculate statistics
        def percentile(data: List[float], p: float) -> Optional[float]:
            if not data:
                return None
            sorted_data = sorted(data)
            k = (len(sorted_data) - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < len(sorted_data):
                return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
            return sorted_data[f]

        return {
            "count": len(listings),
            "avg_min": sum(min_salaries) / len(min_salaries) if min_salaries else None,
            "avg_max": sum(max_salaries) / len(max_salaries) if max_salaries else None,
            "median_min": percentile(min_salaries, 0.5),
            "median_max": percentile(max_salaries, 0.5),
            "p25_min": percentile(min_salaries, 0.25),
            "p75_min": percentile(min_salaries, 0.75),
            "p25_max": percentile(max_salaries, 0.25),
            "p75_max": percentile(max_salaries, 0.75),
        }

    def get_company_data(self, company_name: str) -> Optional[ScrapedCompanyData]:
        """
        Get aggregated company data.

        Args:
            company_name: Company name (exact match)

        Returns:
            ScrapedCompanyData instance or None if not found

        Example:
            company = repo.get_company_data("Google Singapore")
            if company:
                print(f"Overall rating: {company.overall_rating}")
                print(f"Active jobs: {company.active_job_count}")
        """
        return (
            self.session.query(ScrapedCompanyData)
            .filter(ScrapedCompanyData.company_name == company_name)
            .first()
        )

    def search_companies(
        self, search_term: str, skip: int = 0, limit: int = 20
    ) -> List[ScrapedCompanyData]:
        """
        Search companies by name (case-insensitive partial match).

        Args:
            search_term: Term to search for in company name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching ScrapedCompanyData instances

        Example:
            tech_companies = repo.search_companies("tech")
        """
        return (
            self.session.query(ScrapedCompanyData)
            .filter(ScrapedCompanyData.company_name.ilike(f"%{search_term}%"))
            .order_by(desc(ScrapedCompanyData.active_job_count))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_audit_logs(
        self, days: int = 7, status: Optional[str] = None, skip: int = 0, limit: int = 50
    ) -> List[ScrapingAuditLog]:
        """
        Get scraping audit logs.

        Args:
            days: Number of days to look back
            status: Optional status filter ('success', 'partial_success', 'failed')
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ScrapingAuditLog instances

        Example:
            recent_logs = repo.get_audit_logs(days=1)
            failures = repo.get_audit_logs(days=7, status='failed')
        """
        since = datetime.now() - timedelta(days=days)
        query = self.session.query(ScrapingAuditLog).filter(
            ScrapingAuditLog.run_timestamp >= since
        )

        if status:
            query = query.filter(ScrapingAuditLog.status == status)

        return (
            query.order_by(desc(ScrapingAuditLog.run_timestamp))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_audit_log(
        self,
        source: str,
        status: str,
        records_scraped: int,
        records_new: int,
        records_updated: int,
        **kwargs,
    ) -> ScrapingAuditLog:
        """
        Create a new scraping audit log entry.

        Args:
            source: Source of the scrape ('mcf' or 'glassdoor')
            status: Status of the scrape run
            records_scraped: Total records scraped
            records_new: New records added
            records_updated: Existing records updated
            **kwargs: Additional fields (duration_seconds, error_count, etc.)

        Returns:
            Created ScrapingAuditLog instance

        Example:
            log = repo.create_audit_log(
                source='mcf',
                status='success',
                records_scraped=150,
                records_new=20,
                records_updated=10,
                duration_seconds=45,
                error_count=0
            )
        """
        audit_log = ScrapingAuditLog(
            source=source,
            status=status,
            records_scraped=records_scraped,
            records_new=records_new,
            records_updated=records_updated,
            **kwargs,
        )
        return self.create(audit_log)

    def get_scraping_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get scraping performance statistics.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with scraping statistics:
            - total_runs: Total number of scraping runs
            - successful_runs: Number of successful runs
            - failed_runs: Number of failed runs
            - total_records_scraped: Total records scraped
            - total_records_new: Total new records added
            - avg_duration_seconds: Average run duration
            - last_successful_run: Timestamp of last successful run

        Example:
            stats = repo.get_scraping_statistics(days=7)
            print(f"Success rate: {stats['successful_runs'] / stats['total_runs'] * 100}%")
        """
        since = datetime.now() - timedelta(days=days)

        logs = (
            self.session.query(ScrapingAuditLog)
            .filter(ScrapingAuditLog.run_timestamp >= since)
            .all()
        )

        if not logs:
            return {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "total_records_scraped": 0,
                "total_records_new": 0,
                "avg_duration_seconds": None,
                "last_successful_run": None,
            }

        successful = [log for log in logs if log.status == "success"]
        failed = [log for log in logs if log.status == "failed"]

        durations = [log.duration_seconds for log in logs if log.duration_seconds]

        last_success = (
            self.session.query(ScrapingAuditLog)
            .filter(ScrapingAuditLog.status == "success")
            .order_by(desc(ScrapingAuditLog.run_timestamp))
            .first()
        )

        return {
            "total_runs": len(logs),
            "successful_runs": len(successful),
            "failed_runs": len(failed),
            "total_records_scraped": sum(log.records_scraped for log in logs),
            "total_records_new": sum(log.records_new for log in logs),
            "avg_duration_seconds": (
                sum(durations) / len(durations) if durations else None
            ),
            "last_successful_run": (
                last_success.run_timestamp if last_success else None
            ),
        }
