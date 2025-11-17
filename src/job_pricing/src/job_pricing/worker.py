"""
Celery Worker - Background Task Processing for Job Pricing Engine

This module configures Celery for handling asynchronous tasks:
- Data scraping from job boards
- Market data processing
- Price calculations
- Scheduled data refreshes
"""

from celery import Celery
from celery.schedules import crontab

from job_pricing.core.config import get_settings

settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "job_pricing_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=86400,  # Results expire after 24 hours
)

# Task autodiscovery configuration
celery_app.autodiscover_tasks(
    [
        "src.job_pricing.workflows",
        "src.job_pricing.services",
        "src.job_pricing.tasks",  # NEW: Job processing tasks
    ]
)

# Celery Beat Schedule (Periodic Tasks)
celery_app.conf.beat_schedule = {
    # Daily market data refresh (6 AM UTC)
    "daily-market-data-refresh": {
        "task": "src.job_pricing.workflows.refresh_market_data",
        "schedule": crontab(hour=6, minute=0),
        "options": {"expires": 3600},
    },
    # Weekly full data scrape (Sunday 2 AM UTC)
    "weekly-full-scrape": {
        "task": "src.job_pricing.workflows.full_data_scrape",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),
        "options": {"expires": 7200},
    },
}


# Task implementations
@celery_app.task(name="src.job_pricing.workflows.refresh_market_data")
def refresh_market_data():
    """
    Refresh market data from external sources.

    This task runs daily to update:
    - Mercer IPE Job Library data
    - SSG SkillsFuture job roles data
    - Pricing parameters

    Returns:
        dict: Results with statistics for each data source
    """
    import logging
    from pathlib import Path
    from datetime import datetime
    from job_pricing.core.database import get_db
    from data.ingestion.mercer_job_library_loader import MercerJobLibraryLoader
    from data.ingestion.ssg_job_roles_loader import SSGJobRolesLoader

    logger = logging.getLogger(__name__)
    logger.info("Starting daily market data refresh")

    start_time = datetime.now()
    results = {
        "success": False,
        "mercer_updated": 0,
        "ssg_updated": 0,
        "errors": [],
        "execution_time_seconds": 0,
    }

    db_session = None

    try:
        # Get database session
        db_session = next(get_db())

        # Define data file paths
        data_dir = Path(settings.DATA_DIR) / "raw"
        mercer_file = data_dir / "mercer" / "mercer_job_library.xlsx"
        ssg_file = data_dir / "ssg" / "ssg_job_roles.xlsx"

        # Refresh Mercer data if file exists and feature is enabled
        if settings.FEATURE_MERCER_INTEGRATION and mercer_file.exists():
            try:
                logger.info(f"Loading Mercer data from {mercer_file}")
                mercer_loader = MercerJobLibraryLoader(
                    session=db_session,
                    batch_size=100,
                    continue_on_error=True,
                    show_progress=False
                )
                mercer_result = mercer_loader.load_from_excel(str(mercer_file))

                results["mercer_updated"] = mercer_result.statistics.successful
                logger.info(
                    f"Mercer data refresh complete: "
                    f"{mercer_result.statistics.successful}/{mercer_result.statistics.total_records} records"
                )
            except Exception as e:
                error_msg = f"Mercer data refresh failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                results["errors"].append(error_msg)
        else:
            logger.info("Skipping Mercer data refresh (file not found or feature disabled)")

        # Refresh SSG data if file exists and feature is enabled
        if settings.FEATURE_SSG_INTEGRATION and ssg_file.exists():
            try:
                logger.info(f"Loading SSG data from {ssg_file}")
                ssg_loader = SSGJobRolesLoader(
                    session=db_session,
                    batch_size=100,
                    continue_on_error=True,
                    show_progress=False
                )
                ssg_result = ssg_loader.load_from_excel(str(ssg_file))

                results["ssg_updated"] = ssg_result.statistics.successful
                logger.info(
                    f"SSG data refresh complete: "
                    f"{ssg_result.statistics.successful}/{ssg_result.statistics.total_records} records"
                )
            except Exception as e:
                error_msg = f"SSG data refresh failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                results["errors"].append(error_msg)
        else:
            logger.info("Skipping SSG data refresh (file not found or feature disabled)")

        # Mark as successful if at least one source was updated
        results["success"] = results["mercer_updated"] > 0 or results["ssg_updated"] > 0

        execution_time = (datetime.now() - start_time).total_seconds()
        results["execution_time_seconds"] = execution_time

        logger.info(f"Market data refresh completed in {execution_time:.2f}s: {results}")

        return results

    except Exception as e:
        logger.error(f"Fatal error in refresh_market_data: {e}", exc_info=True)
        results["success"] = False
        results["errors"].append(str(e))
        return results

    finally:
        if db_session:
            db_session.close()


@celery_app.task(name="src.job_pricing.workflows.full_data_scrape")
def full_data_scrape(
    job_titles: list = None,
    sources: list = None,
    max_results_per_source: int = 50
):
    """
    Perform full data scrape from all configured sources.

    Args:
        job_titles: List of job titles to scrape (default: common HR/business roles)
        sources: List of sources to scrape (default: ['mcf', 'glassdoor'])
        max_results_per_source: Maximum results per source (default: 50)

    Returns:
        Dictionary with scraping results and statistics
    """
    import logging
    from datetime import datetime
    from job_pricing.scrapers import MyCareersFutureScraper, GlassdoorScraper
    from job_pricing.core.database import get_db
    from job_pricing.repositories.scraping_repository import ScrapingRepository
    from job_pricing.models import ScrapedJobListing, ScrapingAuditLog

    logger = logging.getLogger(__name__)
    logger.info("Starting full data scrape task")

    # Default job titles if none provided
    if job_titles is None:
        job_titles = [
            "Software Engineer",
            "Data Analyst",
            "HR Manager",
            "Marketing Manager",
            "Sales Manager",
        ]

    # Default sources if none provided
    if sources is None:
        sources = ["mcf", "glassdoor"]

    # Initialize results tracking
    start_time = datetime.now()
    results = {
        "success": False,
        "mcf_count": 0,
        "glassdoor_count": 0,
        "total_scraped": 0,
        "total_stored": 0,
        "errors": [],
        "execution_time_seconds": 0,
    }

    db_session = None

    try:
        # Get database session
        db_session = next(get_db())
        repo = ScrapingRepository(db_session)

        all_jobs = []

        # Scrape MyCareersFuture
        if "mcf" in sources:
            logger.info("Scraping MyCareersFuture...")
            try:
                mcf_scraper = MyCareersFutureScraper(headless=True)

                for job_title in job_titles:
                    logger.info(f"MCF: Scraping '{job_title}'")

                    scrape_result = mcf_scraper.run(
                        job_title=job_title,
                        max_pages=2,  # 2 pages per job title
                        delay=2.5
                    )

                    if scrape_result["success"]:
                        jobs = scrape_result["data"]
                        all_jobs.extend(jobs)
                        results["mcf_count"] += len(jobs)
                        logger.info(f"MCF: Found {len(jobs)} jobs for '{job_title}'")
                    else:
                        error_msg = f"MCF scrape failed for '{job_title}': {scrape_result.get('errors', [])}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)

            except Exception as e:
                error_msg = f"MCF scraping error: {str(e)}"
                logger.error(error_msg, exc_info=True)
                results["errors"].append(error_msg)

        # Scrape Glassdoor
        if "glassdoor" in sources:
            logger.info("Scraping Glassdoor...")
            try:
                gd_scraper = GlassdoorScraper(headless=True)

                for job_title in job_titles:
                    logger.info(f"Glassdoor: Scraping '{job_title}'")

                    scrape_result = gd_scraper.run(
                        job_title=job_title,
                        location="Singapore",
                        max_results=10,  # Limit per job title (Glassdoor rate limits)
                        delay=3.5
                    )

                    if scrape_result["success"]:
                        jobs = scrape_result["data"]
                        all_jobs.extend(jobs)
                        results["glassdoor_count"] += len(jobs)
                        logger.info(f"Glassdoor: Found {len(jobs)} jobs for '{job_title}'")
                    else:
                        error_msg = f"Glassdoor scrape failed for '{job_title}': {scrape_result.get('errors', [])}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)

            except Exception as e:
                error_msg = f"Glassdoor scraping error: {str(e)}"
                logger.error(error_msg, exc_info=True)
                results["errors"].append(error_msg)

        results["total_scraped"] = len(all_jobs)

        # Save to database
        if all_jobs:
            logger.info(f"Saving {len(all_jobs)} jobs to database...")

            stored_count = 0
            for job_data in all_jobs:
                try:
                    # Create ScrapedJobListing instance
                    job = ScrapedJobListing(**job_data)

                    # Use repository to create or update
                    # Check if job already exists (by source + job_id)
                    existing = db_session.query(ScrapedJobListing).filter(
                        ScrapedJobListing.source == job.source,
                        ScrapedJobListing.job_id == job.job_id
                    ).first()

                    if existing:
                        # Update last_seen_at
                        existing.last_seen_at = datetime.now()
                        existing.is_active = True
                        logger.debug(f"Updated existing job: {job.job_id}")
                    else:
                        # Add new job
                        db_session.add(job)
                        stored_count += 1
                        logger.debug(f"Added new job: {job.job_id}")

                except Exception as e:
                    logger.warning(f"Error saving job {job_data.get('job_id')}: {e}")
                    results["errors"].append(f"Save error: {str(e)}")
                    continue

            # Commit all changes
            db_session.commit()
            results["total_stored"] = stored_count
            logger.info(f"Stored {stored_count} new jobs, updated {len(all_jobs) - stored_count} existing")

        # Create audit log entry
        execution_time = (datetime.now() - start_time).total_seconds()
        results["execution_time_seconds"] = execution_time

        audit_log = ScrapingAuditLog(
            run_date=start_time,
            run_type="weekly",
            source=None,  # NULL for combined run
            mcf_count=results["mcf_count"],
            glassdoor_count=results["glassdoor_count"],
            validated_count=results["total_scraped"],  # All scraped jobs pass validation
            deduplicated_count=results["total_scraped"] - results["total_stored"],
            stored_count=results["total_stored"],
            error_count=len(results["errors"]),
            status="completed" if results["total_scraped"] > 0 else "failed",
            error_message="; ".join(results["errors"]) if results["errors"] else None,
            execution_time_seconds=int(execution_time)
        )

        db_session.add(audit_log)
        db_session.commit()

        logger.info(f"Audit log created: {audit_log.id}")

        results["success"] = True
        logger.info(f"Full data scrape completed: {results}")

        return results

    except Exception as e:
        logger.error(f"Fatal error in full_data_scrape: {e}", exc_info=True)

        if db_session:
            db_session.rollback()

        # Try to create error audit log
        try:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_log = ScrapingAuditLog(
                run_date=start_time,
                run_type="weekly",
                source=None,
                mcf_count=results.get("mcf_count", 0),
                glassdoor_count=results.get("glassdoor_count", 0),
                validated_count=0,
                deduplicated_count=0,
                stored_count=0,
                error_count=1,
                status="failed",
                error_message=str(e),
                execution_time_seconds=int(execution_time)
            )
            db_session.add(error_log)
            db_session.commit()
        except Exception as log_error:
            logger.error(f"Could not create error audit log: {log_error}")

        results["success"] = False
        results["errors"].append(str(e))
        return results

    finally:
        if db_session:
            db_session.close()


if __name__ == "__main__":
    celery_app.start()
