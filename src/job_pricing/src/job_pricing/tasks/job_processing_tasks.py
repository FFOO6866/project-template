"""
Job Processing Celery Tasks

Background tasks for processing job pricing requests.
"""

import logging
from uuid import UUID
from datetime import datetime

from job_pricing.core.celery_app import celery_app
from job_pricing.core.database import get_session
from job_pricing.services import JobProcessingService

logger = logging.getLogger(__name__)


@celery_app.task(
    name="process_job_pricing_request",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_job_pricing_request(self, request_id: str):
    """
    Process a job pricing request asynchronously.

    This task:
    1. Extracts skills from job description using OpenAI
    2. Matches skills to SSG TSC taxonomy
    3. Calculates salary pricing using V3 multi-source aggregation
    4. Saves results to database

    Args:
        self: Celery task instance (for retries)
        request_id: UUID of the job pricing request as string

    Returns:
        dict: Processing result with status and statistics

    Raises:
        Exception: If processing fails after all retries

    Example:
        >>> from job_pricing.tasks import process_job_pricing_request
        >>> task = process_job_pricing_request.delay("8bd79f97-efb3-4b5a-bf43-639b345a1a34")
        >>> task.wait()  # Wait for completion
    """
    logger.info(f"[CELERY] Starting job pricing request processing: {request_id}")

    session = next(get_session())

    try:
        # Convert string to UUID
        request_uuid = UUID(request_id)

        # Create processing service
        service = JobProcessingService(session)

        # Process the request
        start_time = datetime.now()
        result = service.process_request(request_uuid)
        duration = (datetime.now() - start_time).total_seconds()

        # Get statistics
        extracted_count = (
            len(result.extracted_skills)
            if hasattr(result, "extracted_skills")
            else 0
        )
        matched_count = (
            sum(1 for s in result.extracted_skills if s.matched_tsc_code)
            if hasattr(result, "extracted_skills")
            else 0
        )

        logger.info(
            f"[CELERY] Completed request {request_id} in {duration:.1f}s: "
            f"{extracted_count} skills extracted, {matched_count} matched"
        )

        return {
            "status": "completed",
            "request_id": request_id,
            "job_title": result.job_title,
            "duration_seconds": duration,
            "skills_extracted": extracted_count,
            "skills_matched": matched_count,
            "match_rate": (
                (matched_count / extracted_count * 100) if extracted_count > 0 else 0
            ),
        }

    except Exception as e:
        logger.error(f"[CELERY] Error processing request {request_id}: {e}")

        # Retry on transient errors
        if self.request.retries < self.max_retries:
            logger.warning(
                f"[CELERY] Retrying request {request_id} (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)

        # Mark as permanently failed
        logger.error(f"[CELERY] Request {request_id} failed after all retries")

        return {
            "status": "failed",
            "request_id": request_id,
            "error": str(e),
            "retries": self.request.retries,
        }

    finally:
        session.close()


@celery_app.task(name="process_pending_requests")
def process_pending_requests():
    """
    Periodic task to process any pending requests.

    Scans for requests that are stuck in 'pending' state
    and queues them for processing.

    This task should be run periodically (e.g., every 5 minutes)
    using Celery Beat.

    Returns:
        dict: Number of requests queued

    Example:
        # In celerybeat-schedule.py:
        celery_app.conf.beat_schedule = {
            'process-pending-requests': {
                'task': 'process_pending_requests',
                'schedule': 300.0,  # Every 5 minutes
            },
        }
    """
    from job_pricing.repositories.job_pricing_repository import (
        JobPricingRepository,
    )

    logger.info("[CELERY] Checking for pending requests")

    session = next(get_session())

    try:
        repository = JobPricingRepository(session)
        pending_requests = repository.get_pending_requests(limit=50)

        queued = 0
        for request in pending_requests:
            # Check if request is truly pending (not already processing)
            if request.status == "pending":
                # Queue for processing
                process_job_pricing_request.delay(str(request.id))
                queued += 1

        if queued > 0:
            logger.info(f"[CELERY] Queued {queued} pending requests for processing")

        return {"queued": queued, "total_pending": len(pending_requests)}

    except Exception as e:
        logger.error(f"[CELERY] Error processing pending requests: {e}")
        return {"error": str(e)}

    finally:
        session.close()
