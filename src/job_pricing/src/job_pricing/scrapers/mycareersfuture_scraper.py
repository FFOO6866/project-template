"""
MyCareersFuture (MCF) Job Scraper - Production Ready

Scrapes real MCF job listings with Selenium.
Extracts: job title, salary, company, location
Stores in: scraped_job_listings table

NO MOCK DATA.
"""

import logging
import time
from typing import List, Dict
from datetime import datetime
from decimal import Decimal
import re

from sqlalchemy.orm import Session
from job_pricing.models import ScrapedJobListing
from job_pricing.core.database import SessionLocal
from job_pricing.core.config import get_settings

logger = logging.getLogger(__name__)

class MyCareersFutureScraper:
    """MCF scraper using requests (Selenium-free for speed)."""

    BASE_URL = "https://api.mycareersfuture.gov.sg/v2/jobs"

    def __init__(self):
        """Initialize scraper with configuration settings."""
        self.settings = get_settings()

    def scrape_jobs(
        self,
        max_jobs: int = 1000,
        from_date: str = "2025-01-01",
        search_query: str = "",
    ) -> List[Dict]:
        """
        Scrape MCF jobs via API with date filtering.

        Args:
            max_jobs: Maximum number of jobs to scrape (default: 1000 for full year)
            from_date: Only include jobs posted on or after this date (ISO format)
            search_query: Optional search term to filter jobs

        Returns:
            List of job dictionaries with salary information
        """
        import requests
        from datetime import datetime as dt

        jobs = []
        page = 0
        duplicates = 0
        seen_job_ids = set()

        # Parse from_date
        cutoff_date = dt.fromisoformat(from_date).date() if from_date else None

        logger.info(f"Scraping MCF jobs (max={max_jobs}, from_date={from_date})...")

        while len(jobs) < max_jobs and page < 100:  # Increased page limit for historical data
            try:
                # MCF has a public API
                params = {
                    "page": page,
                    "limit": 100,  # Increased from 20 to 100 for faster scraping
                    "search": search_query,
                }

                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    headers={
                        "User-Agent": self.settings.SCRAPER_USER_AGENT
                    },
                    timeout=self.settings.SCRAPER_REQUEST_TIMEOUT
                )

                if response.status_code != 200:
                    logger.warning(f"API returned status {response.status_code}, stopping")
                    break

                data = response.json()
                results = data.get("results", [])

                if not results:
                    logger.info(f"No more results at page {page}, stopping")
                    break

                for job in results:
                    if len(jobs) >= max_jobs:
                        break

                    job_id = job.get("uuid", "")

                    # Skip duplicates
                    if job_id in seen_job_ids:
                        duplicates += 1
                        continue

                    seen_job_ids.add(job_id)

                    # Check posted date
                    posted_date_str = job.get("postedDate") or job.get("createdAt")
                    if cutoff_date and posted_date_str:
                        try:
                            # Parse date (MCF uses ISO format)
                            posted_date = dt.fromisoformat(posted_date_str.replace('Z', '+00:00')).date()
                            if posted_date < cutoff_date:
                                logger.debug(f"Job {job_id} too old ({posted_date}), skipping")
                                continue
                        except Exception as e:
                            logger.warning(f"Could not parse date '{posted_date_str}': {e}")

                    salary = job.get("salary", {})
                    if salary and salary.get("minimum"):
                        # Get company name from postedCompany or hiringCompany
                        company_name = "Unknown"
                        if job.get("postedCompany", {}).get("name"):
                            company_name = job["postedCompany"]["name"]
                        elif job.get("hiringCompany", {}).get("name"):
                            company_name = job["hiringCompany"]["name"]

                        jobs.append({
                            "job_title": job.get("title", "Unknown"),
                            "company_name": company_name,
                            "location": "Singapore",
                            "salary_min": Decimal(str(salary["minimum"])),
                            "salary_max": Decimal(str(salary.get("maximum", salary["minimum"]))),
                            "salary_currency": "SGD",
                            "salary_type": salary.get("type", {}).get("salaryType", "Monthly"),
                            "employment_type": job.get("employmentType", {}).get("name", "Full-time"),
                            "source": "my_careers_future",  # Must match check constraint
                            "job_id": job_id,
                            "job_url": f"https://www.mycareersfuture.gov.sg/job/{job_id}",
                            "posted_date": dt.fromisoformat(posted_date_str.replace('Z', '+00:00')) if posted_date_str else None,
                            "scraped_at": datetime.now(),
                        })

                page += 1

                # Progress logging
                if page % 5 == 0:
                    logger.info(f"Progress: Page {page}, Jobs collected: {len(jobs)}, Duplicates skipped: {duplicates}")

                time.sleep(1.5)  # Rate limit - be respectful

            except Exception as e:
                logger.error(f"Error scraping page {page}: {e}", exc_info=True)
                break

        logger.info(f"Scraping complete: {len(jobs)} jobs collected, {duplicates} duplicates skipped")
        return jobs
    
    def save_to_database(self, jobs: List[Dict]) -> int:
        """Save to database with upsert (update if exists, insert if new)."""
        session = SessionLocal()  # Create session directly
        saved = 0
        updated = 0

        try:
            for job_data in jobs:
                # Check if job already exists
                existing = session.query(ScrapedJobListing).filter(
                    ScrapedJobListing.source == job_data['source'],
                    ScrapedJobListing.job_id == job_data['job_id']
                ).first()

                if existing:
                    # Update existing record
                    for key, value in job_data.items():
                        setattr(existing, key, value)
                    updated += 1
                else:
                    # Insert new record
                    listing = ScrapedJobListing(**job_data)
                    session.add(listing)
                    saved += 1

            session.commit()
            logger.info(f"Saved {saved} new jobs, updated {updated} existing jobs to database")
        except Exception as e:
            logger.error(f"DB error: {e}")
            session.rollback()
            raise
        finally:
            session.close()

        return saved + updated


def main():
    logging.basicConfig(level=logging.INFO)
    scraper = MyCareersFutureScraper()
    jobs = scraper.scrape_jobs(max_jobs=100)
    if jobs:
        scraper.save_to_database(jobs)
    return jobs


if __name__ == "__main__":
    main()
