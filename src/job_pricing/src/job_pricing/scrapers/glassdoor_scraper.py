"""
Glassdoor Scraper

Scrapes salary insights and company ratings from Glassdoor.

Website: https://www.glassdoor.sg/
Technology: React-based with anti-bot protection
Challenges:
- CAPTCHA protection
- Login walls
- Rate limiting
- Dynamic content loading

NOTE: Glassdoor has strict anti-scraping measures. Consider using their official API
      (requires paid license) for production use. This scraper is for educational/research purposes.
"""

import time
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import quote_plus

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class GlassdoorScraper(BaseScraper):
    """
    Scraper for Glassdoor salary data and company ratings.

    Handles anti-bot protection, login walls, and dynamic content.
    """

    BASE_URL = "https://www.glassdoor.sg"
    SEARCH_URL = f"{BASE_URL}/Job/jobs.htm"
    SALARIES_URL = f"{BASE_URL}/Salaries/index.htm"

    def __init__(self, **kwargs):
        """Initialize Glassdoor scraper with extended timeouts."""
        # Glassdoor needs longer timeouts due to anti-bot checks
        kwargs.setdefault('page_load_timeout', 45)
        kwargs.setdefault('implicit_wait', 15)
        super().__init__(**kwargs)
        self.source_name = "glassdoor"

    def scrape(
        self,
        job_title: str,
        location: Optional[str] = "Singapore",
        max_results: int = 20,
        delay: float = 3.5,
    ) -> List[Dict[str, Any]]:
        """
        Scrape salary data from Glassdoor.

        Args:
            job_title: Job title to search for
            location: Location filter (default: Singapore)
            max_results: Maximum number of results to scrape
            delay: Delay between requests (seconds, min 3.0 recommended)

        Returns:
            List of job/salary dictionaries
        """
        logger.info(
            f"Starting Glassdoor scrape: job_title='{job_title}', "
            f"location='{location}', max_results={max_results}"
        )

        jobs = []

        try:
            # Navigate to salaries search page
            search_url = self._build_search_url(job_title, location)
            logger.info(f"Navigating to: {search_url}")

            self.driver.get(search_url)
            time.sleep(delay)  # Give time for anti-bot checks

            # Check for CAPTCHA or login wall
            if self._check_for_captcha():
                logger.error("CAPTCHA detected - cannot proceed automatically")
                self.errors.append("CAPTCHA protection encountered")
                return jobs

            if self._check_for_login_wall():
                logger.warning("Login wall detected - limited data available")
                # Continue anyway, some data may be visible

            # Wait for content to load
            time.sleep(delay)

            # Try to scrape salary data
            salary_data = self._scrape_salary_data(job_title)
            if salary_data:
                jobs.extend(salary_data)

            # If we need more results, try job listings
            if len(jobs) < max_results:
                job_listings = self._scrape_job_listings(job_title, location, max_results - len(jobs))
                jobs.extend(job_listings)

        except Exception as e:
            logger.error(f"Error during Glassdoor scrape: {e}", exc_info=True)
            self.errors.append(f"Scraping error: {str(e)}")

        logger.info(f"Glassdoor scrape completed: {len(jobs)} results found")
        return jobs

    def _build_search_url(self, job_title: str, location: str) -> str:
        """Build Glassdoor search URL with encoded parameters."""
        encoded_title = quote_plus(job_title)
        encoded_location = quote_plus(location) if location else "Singapore"

        # Try salaries page first (better salary data)
        return f"{self.SALARIES_URL}?keyword={encoded_title}&location={encoded_location}"

    def _check_for_captcha(self) -> bool:
        """Check if CAPTCHA is present on page."""
        try:
            captcha_indicators = [
                "captcha",
                "recaptcha",
                "bot-detection",
                "Please verify you are a human",
            ]

            page_source = self.driver.page_source.lower()

            for indicator in captcha_indicators:
                if indicator in page_source:
                    logger.warning(f"CAPTCHA indicator found: '{indicator}'")
                    return True

            # Check for CAPTCHA iframes
            captcha_frames = self.driver.find_elements(
                By.CSS_SELECTOR,
                "iframe[src*='captcha'], iframe[src*='recaptcha']"
            )

            if captcha_frames:
                logger.warning(f"Found {len(captcha_frames)} CAPTCHA iframes")
                return True

            return False

        except Exception as e:
            logger.warning(f"Error checking for CAPTCHA: {e}")
            return False

    def _check_for_login_wall(self) -> bool:
        """Check if login wall is blocking content."""
        try:
            login_indicators = [
                "button[data-test='sign-in']",
                "a[href*='login']",
                ".modal.sign-in",
                "#LoginModal",
            ]

            for selector in login_indicators:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and any(el.is_displayed() for el in elements):
                    return True

            return False

        except Exception as e:
            logger.warning(f"Error checking for login wall: {e}")
            return False

    def _scrape_salary_data(self, job_title: str) -> List[Dict[str, Any]]:
        """
        Scrape salary estimates from Glassdoor salary pages.

        Returns:
            List of salary data dictionaries
        """
        salaries = []

        try:
            # Scroll to load content
            self.scroll_page(pause_time=1.0)

            # Parse page with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Find salary cards/rows (multiple possible structures)
            salary_elements = (
                soup.find_all(attrs={"data-test": re.compile(r"salary", re.I)})
                or soup.find_all("div", class_=re.compile(r"salary.*card", re.I))
                or soup.find_all("tr", class_=re.compile(r"salary.*row", re.I))
            )

            logger.info(f"Found {len(salary_elements)} salary elements")

            for elem in salary_elements[:10]:  # Limit to first 10
                try:
                    salary_data = self._extract_salary_from_element(elem, job_title)
                    if salary_data:
                        salaries.append(salary_data)
                except Exception as e:
                    logger.debug(f"Error extracting salary element: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping salary data: {e}")

        return salaries

    def _extract_salary_from_element(self, element, job_title: str) -> Optional[Dict[str, Any]]:
        """Extract salary data from a Glassdoor salary element."""
        try:
            # Extract company name
            company_elem = (
                element.find(attrs={"data-test": "employer-name"})
                or element.find(class_=re.compile(r"employer|company", re.I))
            )
            company_name = company_elem.get_text(strip=True) if company_elem else "Unknown"

            # Extract salary range
            salary_text = element.get_text()
            salary_min, salary_max = self._parse_salary(salary_text)

            if not salary_min and not salary_max:
                return None  # Skip if no salary data

            # Extract company rating
            rating_elem = element.find(class_=re.compile(r"rating", re.I))
            company_rating = None
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r"(\d+\.?\d*)", rating_text)
                if rating_match:
                    company_rating = float(rating_match.group(1))

            # Build salary record
            record = {
                "source": self.source_name,
                "job_id": f"gd_{abs(hash(company_name + job_title)) % 1000000}",
                "job_url": self.driver.current_url,
                "job_title": job_title,
                "company_name": company_name,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_currency": "SGD",
                "salary_type": "estimated",  # Glassdoor provides estimates
                "location": "Singapore",
                "employment_type": None,
                "seniority_level": self._infer_seniority(job_title),
                "job_description": None,
                "requirements": None,
                "skills": [],
                "benefits": [],
                "company_rating": company_rating,
                "company_size": None,
                "industry": None,
                "has_salary_data": True,
                "posted_date": None,
                "scraped_at": datetime.now(),
                "last_seen_at": datetime.now(),
                "is_active": True,
            }

            logger.debug(f"Extracted salary: {job_title} at {company_name} (${salary_min}-${salary_max})")
            return record

        except Exception as e:
            logger.warning(f"Failed to extract salary from element: {e}")
            return None

    def _scrape_job_listings(
        self,
        job_title: str,
        location: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """
        Scrape job listings as fallback if salary data not available.

        Args:
            job_title: Job title to search
            location: Location filter
            max_results: Maximum results to return

        Returns:
            List of job dictionaries
        """
        jobs = []

        try:
            # Navigate to jobs search
            job_search_url = f"{self.SEARCH_URL}?sc.keyword={quote_plus(job_title)}&locT=C&locId=2397&locKeyword={quote_plus(location)}"
            logger.info(f"Navigating to job listings: {job_search_url}")

            self.driver.get(job_search_url)
            time.sleep(3)

            # Scroll and wait for listings
            self.scroll_page(pause_time=0.75)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Find job cards
            job_cards = (
                soup.find_all("li", class_=re.compile(r"job.*card|react.*job", re.I))
                or soup.find_all("div", attrs={"data-test": re.compile(r"job.*item", re.I)})
                or soup.find_all("article")
            )

            logger.info(f"Found {len(job_cards)} job cards")

            for card in job_cards[:max_results]:
                try:
                    job = self._extract_job_from_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"Error extracting job card: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping job listings: {e}")

        return jobs

    def _extract_job_from_card(self, card) -> Optional[Dict[str, Any]]:
        """Extract job data from Glassdoor job card."""
        try:
            # Extract job title
            title_elem = (
                card.find("a", class_=re.compile(r"job.*title", re.I))
                or card.find("h2")
                or card.find("h3")
            )
            job_title = title_elem.get_text(strip=True) if title_elem else "Unknown"

            # Extract company
            company_elem = (
                card.find(attrs={"data-test": "employer-name"})
                or card.find("span", class_=re.compile(r"employer|company", re.I))
            )
            company_name = company_elem.get_text(strip=True) if company_elem else "Unknown"

            # Extract job URL
            link_elem = card.find("a", href=True)
            job_url = None
            if link_elem:
                href = link_elem["href"]
                job_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

            # Extract salary if present
            salary_text = card.get_text()
            salary_min, salary_max = self._parse_salary(salary_text)

            # Extract rating
            rating_elem = card.find(class_=re.compile(r"rating", re.I))
            company_rating = None
            if rating_elem:
                rating_match = re.search(r"(\d+\.?\d*)", rating_elem.get_text())
                if rating_match:
                    company_rating = float(rating_match.group(1))

            # Build job record
            job = {
                "source": self.source_name,
                "job_id": f"gd_{abs(hash(job_url or job_title + company_name)) % 1000000}",
                "job_url": job_url or self.driver.current_url,
                "job_title": job_title,
                "company_name": company_name,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_currency": "SGD",
                "salary_type": "estimated" if salary_min else None,
                "location": "Singapore",
                "employment_type": None,
                "seniority_level": self._infer_seniority(job_title),
                "job_description": None,
                "requirements": None,
                "skills": [],
                "benefits": [],
                "company_rating": company_rating,
                "company_size": None,
                "industry": None,
                "has_salary_data": salary_min is not None,
                "posted_date": None,
                "scraped_at": datetime.now(),
                "last_seen_at": datetime.now(),
                "is_active": True,
            }

            return job

        except Exception as e:
            logger.warning(f"Failed to extract job from card: {e}")
            return None

    def _parse_salary(self, text: str) -> tuple[Optional[float], Optional[float]]:
        """
        Parse salary from text (handles Glassdoor format).

        Glassdoor uses formats like:
        - "$80K - $120K (Employer est.)"
        - "S$5,000 - S$8,000"
        - "$100,000/yr"
        """
        if not text:
            return None, None

        # Remove commas and extra spaces
        text = re.sub(r",", "", text)

        # Try range pattern: "$80K - $120K" or "5000 - 8000"
        range_patterns = [
            r"[\$S]*\s*(\d+(?:\.\d+)?)\s*[Kk]?\s*[-–to]\s*[\$S]*\s*(\d+(?:\.\d+)?)\s*[Kk]?",
            r"SGD\s*(\d+(?:\.\d+)?)\s*[-–]\s*SGD\s*(\d+(?:\.\d+)?)",
        ]

        for pattern in range_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                min_val = float(match.group(1))
                max_val = float(match.group(2))

                # Handle 'K' suffix
                if 'k' in text.lower():
                    min_val *= 1000
                    max_val *= 1000

                return min_val, max_val

        # Try single value: "$100K" or "S$50000"
        single_patterns = [
            r"[\$S]+\s*(\d+(?:\.\d+)?)\s*[Kk]?",
            r"SGD\s*(\d+(?:\.\d+)?)",
        ]

        for pattern in single_patterns:
            match = re.search(pattern, text)
            if match:
                val = float(match.group(1))
                if 'k' in text.lower():
                    val *= 1000

                # Assume +/- 15% range
                return val * 0.85, val * 1.15

        return None, None

    def _infer_seniority(self, job_title: str) -> Optional[str]:
        """Infer seniority level from job title."""
        title_lower = job_title.lower()

        if any(word in title_lower for word in ["intern", "trainee", "graduate", "entry"]):
            return "Entry"
        elif any(word in title_lower for word in ["senior", "sr", "lead", "principal"]):
            return "Senior"
        elif any(word in title_lower for word in ["manager", "head", "director"]):
            return "Management"
        elif any(word in title_lower for word in ["executive", "vp", "c-level", "chief"]):
            return "Executive"
        elif any(word in title_lower for word in ["junior", "jr"]):
            return "Junior"
        else:
            return "Mid"
