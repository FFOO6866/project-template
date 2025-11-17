"""
Test script for MyCareersFuture scraper

Run with: python test_mcf_scraper.py
"""

import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_mcf_scraper():
    """Test MCF scraper with a simple search."""

    try:
        from job_pricing.scrapers.mycareersfuture_scraper import MyCareersFutureScraper

        logger.info("=" * 80)
        logger.info("Testing MyCareersFuture Scraper")
        logger.info("=" * 80)

        # Initialize scraper (headless mode for Docker)
        scraper = MyCareersFutureScraper(
            headless=True,
            page_load_timeout=30,
            implicit_wait=10
        )

        # Test parameters
        test_params = {
            "job_title": "Software Engineer",
            "location": None,
            "max_pages": 1,  # Just test 1 page
            "delay": 2.0
        }

        logger.info(f"Test parameters: {test_params}")

        # Run scraper
        result = scraper.run(**test_params)

        # Print results
        logger.info("=" * 80)
        logger.info("SCRAPING RESULTS")
        logger.info("=" * 80)
        logger.info(f"Success: {result['success']}")
        logger.info(f"Jobs found: {result['count']}")
        logger.info(f"Errors: {len(result['errors'])}")
        logger.info(f"Execution time: {result['execution_time_seconds']:.2f}s")

        if result['errors']:
            logger.warning(f"Errors encountered: {result['errors']}")

        # Print sample jobs
        if result['data']:
            logger.info("\n" + "=" * 80)
            logger.info("SAMPLE JOBS (first 3)")
            logger.info("=" * 80)

            for i, job in enumerate(result['data'][:3], 1):
                logger.info(f"\nJob {i}:")
                logger.info(f"  Title: {job['job_title']}")
                logger.info(f"  Company: {job['company_name']}")
                logger.info(f"  Location: {job['location']}")

                if job['salary_min'] and job['salary_max']:
                    logger.info(f"  Salary: ${job['salary_min']:,.0f} - ${job['salary_max']:,.0f}")
                else:
                    logger.info(f"  Salary: Not disclosed")

                logger.info(f"  Employment Type: {job['employment_type']}")
                logger.info(f"  Seniority: {job['seniority_level']}")
                logger.info(f"  URL: {job['job_url']}")

        logger.info("\n" + "=" * 80)
        logger.info("TEST COMPLETED")
        logger.info("=" * 80)

        return result

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    result = test_mcf_scraper()

    if result and result['success']:
        logger.info("✅ Test PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Test FAILED")
        sys.exit(1)
