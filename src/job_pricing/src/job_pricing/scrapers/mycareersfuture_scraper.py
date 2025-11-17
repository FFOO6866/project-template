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
from job_pricing.core.database import get_session

logger = logging.getLogger(__name__)

class MyCareersFutureScraper:
    """MCF scraper using requests (Selenium-free for speed)."""

    BASE_URL = "https://api.mycareersfuture.gov.sg/v2/jobs"
    
    def scrape_jobs(self, max_jobs: int = 100) -> List[Dict]:
        """Scrape MCF jobs via API."""
        import requests
        
        jobs = []
        page = 0
        
        logger.info(f"Scraping MCF jobs (max={max_jobs})...")
        
        while len(jobs) < max_jobs and page < 10:
            try:
                # MCF has a public API
                response = requests.get(
                    self.BASE_URL,
                    params={"page": page, "limit": 20, "search": ""},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10
                )
                
                if response.status_code != 200:
                    break
                    
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    break
                
                for job in results:
                    if len(jobs) >= max_jobs:
                        break

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
                            "source": "my_careers_future",  # Must match check constraint
                            "job_id": job.get("uuid", ""),
                            "job_url": f"https://www.mycareersfuture.gov.sg/job/{job.get('uuid', '')}",
                            "scraped_at": datetime.now(),
                        })
                
                page += 1
                time.sleep(1)  # Rate limit
                
            except Exception as e:
                logger.error(f"Error scraping page {page}: {e}")
                break
        
        logger.info(f"Scraped {len(jobs)} MCF jobs")
        return jobs
    
    def save_to_database(self, jobs: List[Dict]) -> int:
        """Save to database."""
        session = get_session()
        saved = 0

        try:
            for job_data in jobs:
                listing = ScrapedJobListing(**job_data)
                session.add(listing)
                saved += 1

            session.commit()
            logger.info(f"Saved {saved} jobs to database")
        except Exception as e:
            logger.error(f"DB error: {e}")
            session.rollback()
            raise
        finally:
            session.close()

        return saved


def main():
    logging.basicConfig(level=logging.INFO)
    scraper = MyCareersFutureScraper()
    jobs = scraper.scrape_jobs(max_jobs=100)
    if jobs:
        scraper.save_to_database(jobs)
    return jobs


if __name__ == "__main__":
    main()
