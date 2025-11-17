"""
Script to run MyCareersFuture scraper and save results to database

Run with: python run_scraper_to_db.py
"""

import logging
from datetime import datetime

from src.job_pricing.scrapers.mycareersfuture_scraper import MyCareersFutureScraper
from src.job_pricing.repositories.scraping_repository import ScrapingRepository
from src.job_pricing.core.database import get_session

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run scraper and save to database."""

    logger.info("=" * 80)
    logger.info("Starting MyCareersFuture Scraper -> Database Pipeline")
    logger.info("=" * 80)

    # Initialize scraper
    scraper = MyCareersFutureScraper(
        headless=True,
        page_load_timeout=30,
        implicit_wait=10
    )

    # Test parameters - scrape Software Engineer jobs
    test_params = {
        "job_title": "Software Engineer",
        "location": None,
        "max_pages": 2,  # Scrape 2 pages (~40 jobs)
        "delay": 2.0
    }

    logger.info(f"Scraping parameters: {test_params}")

    # Run scraper
    logger.info("Running scraper...")
    result = scraper.run(**test_params)

    # Check if scraping was successful
    if not result['success']:
        logger.error(f"Scraping failed! Errors: {result['errors']}")
        return False

    logger.info(f"Scraped {result['count']} jobs successfully in {result['execution_time_seconds']:.2f}s")

    if not result['data']:
        logger.warning("No jobs found to save")
        return True

    # Save to database
    logger.info("Saving to database...")

    session = get_session()
    repository = ScrapingRepository(session)

    try:
        saved_count = 0
        duplicate_count = 0
        error_count = 0

        for job_data in result['data']:
            try:
                # Check if job already exists (by URL)
                existing = repository.find_by_url(job_data['job_url'])

                if existing:
                    duplicate_count += 1
                    logger.debug(f"Job already exists: {job_data['job_title']} at {job_data['company_name']}")
                    continue

                # Save new job
                job_listing = repository.create(job_data)
                saved_count += 1
                logger.debug(f"Saved: {job_listing.job_title} at {job_listing.company_name}")

            except Exception as e:
                error_count += 1
                logger.error(f"Failed to save job: {e}")

        # Commit all changes
        session.commit()

        # Print summary
        logger.info("=" * 80)
        logger.info("PIPELINE COMPLETED")
        logger.info("=" * 80)
        logger.info(f"Total scraped: {result['count']}")
        logger.info(f"Saved to DB: {saved_count}")
        logger.info(f"Duplicates skipped: {duplicate_count}")
        logger.info(f"Errors: {error_count}")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        session.rollback()
        return False

    finally:
        session.close()


if __name__ == "__main__":
    success = main()

    if success:
        logger.info("✅ Pipeline completed successfully")
    else:
        logger.error("❌ Pipeline failed")
