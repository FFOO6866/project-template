"""
Job Pricing Repository

Provides data access for job pricing requests and results.
Includes domain-specific query methods for job pricing operations.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, or_

from job_pricing.models import (
    JobPricingRequest,
    JobPricingResult,
    DataSourceContribution,
)
from .base import BaseRepository


class JobPricingRepository(BaseRepository[JobPricingRequest]):
    """
    Repository for Job Pricing Request operations.

    Provides methods for querying job pricing requests, results,
    and related data source contributions.
    """

    def __init__(self, session: Session):
        """Initialize with Job Pricing Request model."""
        super().__init__(JobPricingRequest, session)

    def get_with_result(self, request_id: UUID) -> Optional[JobPricingRequest]:
        """
        Get a job pricing request with its result eagerly loaded.

        Args:
            request_id: UUID of the request

        Returns:
            JobPricingRequest with pricing_result relationship loaded,
            or None if not found

        Example:
            request = repo.get_with_result(request_id)
            if request and request.pricing_result:
                print(f"Target salary: {request.pricing_result.target_salary}")
        """
        return (
            self.session.query(JobPricingRequest)
            .options(joinedload(JobPricingRequest.pricing_results))
            .filter(JobPricingRequest.id == request_id)
            .first()
        )

    def get_with_full_details(self, request_id: UUID) -> Optional[JobPricingRequest]:
        """
        Get a job pricing request with all related data eagerly loaded.

        Loads:
        - Pricing result
        - Data source contributions
        - Mercer job mapping
        - Extracted skills

        Args:
            request_id: UUID of the request

        Returns:
            JobPricingRequest with all relationships loaded, or None if not found
        """
        return (
            self.session.query(JobPricingRequest)
            .options(
                joinedload(JobPricingRequest.pricing_results).joinedload(
                    JobPricingResult.data_source_contributions
                ),
                joinedload(JobPricingRequest.mercer_mapping),
                joinedload(JobPricingRequest.extracted_skills),
            )
            .filter(JobPricingRequest.id == request_id)
            .first()
        )

    def get_by_user(
        self,
        user_email: str,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[JobPricingRequest]:
        """
        Get all requests by a specific user with pagination.

        Args:
            user_email: Email of the user who made the requests
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            status: Optional status filter ('pending', 'processing', 'completed', 'failed')

        Returns:
            List of JobPricingRequest instances ordered by most recent first

        Example:
            recent_requests = repo.get_by_user('user@example.com', limit=10)
            completed = repo.get_by_user('user@example.com', status='completed')
        """
        query = self.session.query(JobPricingRequest).filter(
            JobPricingRequest.requested_by == user_email
        )

        if status:
            query = query.filter(JobPricingRequest.status == status)

        return query.order_by(desc(JobPricingRequest.request_date)).offset(skip).limit(limit).all()

    def get_pending_requests(self, limit: int = 100) -> List[JobPricingRequest]:
        """
        Get all pending requests that need processing.

        Args:
            limit: Maximum number of requests to return

        Returns:
            List of pending JobPricingRequest instances ordered by oldest first

        Example:
            pending = repo.get_pending_requests(limit=50)
            for request in pending:
                process_job_pricing(request)
        """
        return (
            self.session.query(JobPricingRequest)
            .filter(JobPricingRequest.status == "pending")
            .order_by(JobPricingRequest.request_date)
            .limit(limit)
            .all()
        )

    def get_recent_completed(
        self, days: int = 7, limit: int = 50
    ) -> List[JobPricingRequest]:
        """
        Get recently completed requests.

        Args:
            days: Number of days to look back
            limit: Maximum number of requests to return

        Returns:
            List of recently completed JobPricingRequest instances

        Example:
            last_week = repo.get_recent_completed(days=7)
        """
        since = datetime.now() - timedelta(days=days)
        return (
            self.session.query(JobPricingRequest)
            .filter(
                and_(
                    JobPricingRequest.status == "completed",
                    JobPricingRequest.processing_completed_at >= since,
                )
            )
            .order_by(desc(JobPricingRequest.processing_completed_at))
            .limit(limit)
            .all()
        )

    def get_by_job_family(
        self, job_family: str, skip: int = 0, limit: int = 20
    ) -> List[JobPricingRequest]:
        """
        Get all requests for a specific job family.

        Args:
            job_family: Job family name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of JobPricingRequest instances for the job family

        Example:
            hr_requests = repo.get_by_job_family('Human Resources')
        """
        return (
            self.session.query(JobPricingRequest)
            .filter(JobPricingRequest.job_family == job_family)
            .order_by(desc(JobPricingRequest.request_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_location(
        self, location: str, skip: int = 0, limit: int = 20
    ) -> List[JobPricingRequest]:
        """
        Get all requests for a specific location.

        Args:
            location: Location name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of JobPricingRequest instances for the location

        Example:
            singapore_requests = repo.get_by_location('Singapore CBD')
        """
        return (
            self.session.query(JobPricingRequest)
            .filter(JobPricingRequest.location == location)
            .order_by(desc(JobPricingRequest.request_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_title(
        self, search_term: str, skip: int = 0, limit: int = 20
    ) -> List[JobPricingRequest]:
        """
        Search requests by job title (case-insensitive partial match).

        Args:
            search_term: Term to search for in job title
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching JobPricingRequest instances

        Example:
            analyst_jobs = repo.search_by_title('analyst')
        """
        return (
            self.session.query(JobPricingRequest)
            .filter(JobPricingRequest.job_title.ilike(f"%{search_term}%"))
            .order_by(desc(JobPricingRequest.request_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_statistics(self, user_email: Optional[str] = None) -> dict:
        """
        Get statistics about job pricing requests.

        Args:
            user_email: Optional user email to filter statistics

        Returns:
            Dictionary with statistics:
            - total: Total number of requests
            - pending: Number of pending requests
            - processing: Number of requests being processed
            - completed: Number of completed requests
            - failed: Number of failed requests
            - avg_processing_time: Average processing time in seconds

        Example:
            stats = repo.get_statistics()
            print(f"Completion rate: {stats['completed'] / stats['total'] * 100}%")
        """
        query = self.session.query(JobPricingRequest)
        if user_email:
            query = query.filter(JobPricingRequest.requested_by == user_email)

        all_requests = query.all()

        total = len(all_requests)
        pending = sum(1 for r in all_requests if r.status == "pending")
        processing = sum(1 for r in all_requests if r.status == "processing")
        completed = sum(1 for r in all_requests if r.status == "completed")
        failed = sum(1 for r in all_requests if r.status == "failed")

        processing_times = [
            r.processing_duration_seconds
            for r in all_requests
            if r.processing_duration_seconds is not None
        ]
        avg_processing_time = (
            sum(processing_times) / len(processing_times) if processing_times else 0
        )

        return {
            "total": total,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "avg_processing_time": avg_processing_time,
        }

    def mark_as_processing(self, request_id: UUID) -> Optional[JobPricingRequest]:
        """
        Mark a request as being processed.

        Args:
            request_id: UUID of the request

        Returns:
            Updated JobPricingRequest or None if not found

        Example:
            request = repo.mark_as_processing(request_id)
        """
        return self.update_by_id(
            request_id, status="processing", processing_started_at=datetime.now()
        )

    def mark_as_completed(
        self, request_id: UUID, duration_seconds: int
    ) -> Optional[JobPricingRequest]:
        """
        Mark a request as completed.

        Args:
            request_id: UUID of the request
            duration_seconds: Processing duration in seconds

        Returns:
            Updated JobPricingRequest or None if not found

        Example:
            request = repo.mark_as_completed(request_id, duration_seconds=45)
        """
        return self.update_by_id(
            request_id,
            status="completed",
            processing_completed_at=datetime.now(),
            processing_duration_seconds=duration_seconds,
        )

    def mark_as_failed(self, request_id: UUID) -> Optional[JobPricingRequest]:
        """
        Mark a request as failed.

        Args:
            request_id: UUID of the request

        Returns:
            Updated JobPricingRequest or None if not found

        Example:
            request = repo.mark_as_failed(request_id)
        """
        return self.update_by_id(request_id, status="failed")
