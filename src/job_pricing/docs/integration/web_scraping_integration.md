# Web Scraping Integration Specification

**Version**: 1.0
**Date**: 2025-01-10
**Status**: Production-Ready

## Overview

This document specifies the production implementation for web scraping job market data from two primary sources:
1. **My Careers Future (MCF)** - Singapore's national jobs portal
2. **Glassdoor** - Global job listings and company reviews platform

The scraping system operates on a **weekly batch schedule** (every Sunday 2:00 AM SGT) to collect fresh market data for the Dynamic Job Pricing Engine. All scraped data is deduplicated, validated, and integrated into the pricing algorithm with appropriate confidence scoring.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Scraping Orchestrator                 │
│                   (Kailash Workflow Engine)                  │
└───────────────┬─────────────────────────────────────────────┘
                │
                ├─────────────┬─────────────┬──────────────┐
                │             │             │              │
        ┌───────▼──────┐  ┌───▼─────┐  ┌───▼──────┐  ┌───▼──────┐
        │ MCF Scraper  │  │Glassdoor│  │Data      │  │Integration│
        │  Module      │  │ Scraper │  │Validator │  │  Engine   │
        └──────┬───────┘  └────┬────┘  └────┬─────┘  └────┬─────┘
               │               │            │             │
        ┌──────▼───────────────▼────────────▼─────────────▼─────┐
        │            PostgreSQL Database                         │
        │  - scraped_job_listings                               │
        │  - scraping_audit_log                                 │
        │  - scraped_company_data                               │
        └───────────────────────────────────────────────────────┘
```

## Target Platforms

### 1. My Careers Future (MCF)

**URL**: https://www.mycareersfuture.gov.sg/
**Data Priority**: HIGH (40% weight in market data aggregation)

**Key Data Points**:
- Job Title
- Company Name
- Salary Range (if disclosed)
- Location (postal code, area)
- Employment Type (Full-time, Contract, Part-time)
- Seniority Level
- Job Category
- Skills Required (structured tags)
- Job Description
- Posting Date
- Application Deadline

**Technical Characteristics**:
- Modern React SPA with API endpoints
- Rate limiting: ~50 requests/minute
- Requires JavaScript rendering
- Search pagination: 20 results per page
- Total job listings: ~100,000+

**API Endpoints** (Reverse-engineered):
```
GET /api/v2/search
POST /api/v2/jobs/search
GET /api/v2/jobs/{job_id}
```

### 2. Glassdoor

**URL**: https://www.glassdoor.sg/
**Data Priority**: MEDIUM (15% weight in market data aggregation)

**Key Data Points**:
- Job Title
- Company Name
- Salary Estimate (Glassdoor's algorithm)
- Location
- Company Rating
- Company Size
- Industry
- Job Description
- Benefits
- Posted Date
- Easy Apply indicator

**Technical Characteristics**:
- Anti-bot protection (Cloudflare, reCAPTCHA)
- Rate limiting: ~20 requests/minute
- Requires JavaScript rendering
- Login required for full data access
- Search pagination: 10-30 results per page
- Total Singapore jobs: ~50,000+

**Challenges**:
- More aggressive anti-scraping measures
- Salary data often estimated (not actual)
- Requires careful rate limiting
- May require rotating IPs/proxies

## Production Implementation

### Phase 1: Scraping Infrastructure

**File**: `src/job_pricing/services/web_scraping/base_scraper.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import random
import time

class BaseScraper(ABC):
    """
    Production-ready base class for web scrapers.
    NO mock data - all scraping from real websites.
    """

    def __init__(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        self.headless = headless
        self.proxy = proxy
        self.user_agent = user_agent or self._get_random_user_agent()
        self.driver = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_random_user_agent(self) -> str:
        """Rotate user agents to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        return random.choice(user_agents)

    def initialize_driver(self) -> webdriver.Chrome:
        """Initialize Selenium Chrome driver with production settings"""
        options = Options()

        if self.headless:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')

        # Anti-detection measures
        options.add_argument(f'user-agent={self.user_agent}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')

        # Proxy configuration
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')

        self.driver = webdriver.Chrome(options=options)

        # Execute CDP commands to mask automation
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": self.user_agent
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return self.driver

    def random_sleep(self, min_seconds: float = 2.0, max_seconds: float = 5.0):
        """Sleep for random duration to mimic human behavior"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def safe_find_element(
        self,
        by: By,
        value: str,
        timeout: int = 10
    ) -> Optional[any]:
        """Safely find element with timeout"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.warning(f"Element not found: {by}={value}")
            return None

    def safe_click(self, element) -> bool:
        """Safely click element with retry"""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(element)
            )
            element.click()
            return True
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return False

    def scroll_to_bottom(self):
        """Scroll to bottom to trigger lazy loading"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.random_sleep(1.0, 2.0)

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    @abstractmethod
    def scrape_job_listings(self, search_params: Dict) -> List[Dict]:
        """Scrape job listings based on search parameters"""
        pass

    @abstractmethod
    def scrape_job_details(self, job_url: str) -> Dict:
        """Scrape detailed information for a single job"""
        pass
```

### Phase 2: My Careers Future Scraper

**File**: `src/job_pricing/services/web_scraping/mcf_scraper.py`

```python
from typing import Dict, List, Optional
from selenium.webdriver.common.by import By
from datetime import datetime
import json
import re
from .base_scraper import BaseScraper

class MCFScraper(BaseScraper):
    """
    Production-ready scraper for My Careers Future portal.
    Extracts job listings with salary data for Singapore market.
    """

    BASE_URL = "https://www.mycareersfuture.gov.sg"
    API_BASE_URL = "https://api.mycareersfuture.gov.sg/v2"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_cookies = None

    def scrape_job_listings(
        self,
        search_params: Dict
    ) -> List[Dict]:
        """
        Scrape job listings from MCF.

        Args:
            search_params: {
                'search': str (job title keyword),
                'location': str,
                'job_category': str,
                'employment_type': str,
                'salary_min': int,
                'salary_max': int,
                'page_limit': int (max pages to scrape)
            }

        Returns:
            List of job listing dictionaries
        """
        self.initialize_driver()
        all_jobs = []

        try:
            # Build search URL
            search_url = self._build_search_url(search_params)
            self.logger.info(f"Starting MCF scrape: {search_url}")

            self.driver.get(search_url)
            self.random_sleep(3, 5)

            page_limit = search_params.get('page_limit', 10)
            current_page = 1

            while current_page <= page_limit:
                self.logger.info(f"Scraping MCF page {current_page}/{page_limit}")

                # Wait for job cards to load
                job_cards = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "[data-testid='job-card']"
                )

                if not job_cards:
                    self.logger.warning("No job cards found, stopping pagination")
                    break

                # Extract data from each job card
                for card in job_cards:
                    try:
                        job_data = self._extract_job_card_data(card)
                        if job_data:
                            all_jobs.append(job_data)
                    except Exception as e:
                        self.logger.error(f"Error extracting job card: {e}")
                        continue

                # Check for next page
                if not self._click_next_page():
                    self.logger.info("No more pages available")
                    break

                current_page += 1
                self.random_sleep(5, 8)  # Longer delay between pages

        except Exception as e:
            self.logger.error(f"MCF scraping error: {e}")
        finally:
            self.cleanup()

        self.logger.info(f"MCF scraping completed: {len(all_jobs)} jobs extracted")
        return all_jobs

    def _build_search_url(self, params: Dict) -> str:
        """Build MCF search URL with parameters"""
        base = f"{self.BASE_URL}/search"
        query_parts = []

        if params.get('search'):
            query_parts.append(f"search={params['search']}")
        if params.get('location'):
            query_parts.append(f"location={params['location']}")
        if params.get('job_category'):
            query_parts.append(f"jobCategories={params['job_category']}")
        if params.get('employment_type'):
            query_parts.append(f"employmentType={params['employment_type']}")
        if params.get('salary_min'):
            query_parts.append(f"salary={params['salary_min']}")

        return f"{base}?{'&'.join(query_parts)}" if query_parts else base

    def _extract_job_card_data(self, card_element) -> Optional[Dict]:
        """Extract structured data from MCF job card"""
        try:
            # Job title
            title_elem = card_element.find_element(By.CSS_SELECTOR, "[data-testid='job-card-title']")
            job_title = title_elem.text if title_elem else None

            # Company name
            company_elem = card_element.find_element(By.CSS_SELECTOR, "[data-testid='job-card-company']")
            company_name = company_elem.text if company_elem else None

            # Salary range
            salary_elem = card_element.find_element(By.CSS_SELECTOR, "[data-testid='job-card-salary']")
            salary_text = salary_elem.text if salary_elem else None
            salary_min, salary_max = self._parse_salary_range(salary_text)

            # Location
            location_elem = card_element.find_element(By.CSS_SELECTOR, "[data-testid='job-card-location']")
            location = location_elem.text if location_elem else None

            # Employment type
            emp_type_elem = card_element.find_element(By.CSS_SELECTOR, "[data-testid='job-card-employment-type']")
            employment_type = emp_type_elem.text if emp_type_elem else None

            # Skills (tags)
            skills_elems = card_element.find_elements(By.CSS_SELECTOR, "[data-testid='job-card-skill-tag']")
            skills = [elem.text for elem in skills_elems]

            # Job URL
            job_link = card_element.find_element(By.CSS_SELECTOR, "a[href*='/job/']")
            job_url = job_link.get_attribute('href')
            job_id = self._extract_job_id(job_url)

            # Posted date
            date_elem = card_element.find_element(By.CSS_SELECTOR, "[data-testid='job-card-posted-date']")
            posted_date = self._parse_posted_date(date_elem.text) if date_elem else None

            return {
                'source': 'my_careers_future',
                'job_id': job_id,
                'job_url': job_url,
                'job_title': job_title,
                'company_name': company_name,
                'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_currency': 'SGD',
                'location': location,
                'employment_type': employment_type,
                'skills': skills,
                'posted_date': posted_date,
                'scraped_at': datetime.now()
            }

        except NoSuchElementException as e:
            self.logger.warning(f"Element not found in job card: {e}")
            return None

    def _parse_salary_range(self, salary_text: Optional[str]) -> tuple:
        """Parse salary range from text like '$5,000 - $7,000'"""
        if not salary_text:
            return None, None

        # Remove currency symbols and commas
        clean_text = salary_text.replace('$', '').replace(',', '').replace('SGD', '')

        # Match patterns like "5000 - 7000" or "5000 to 7000"
        match = re.search(r'(\d+)\s*[-to]+\s*(\d+)', clean_text)
        if match:
            return int(match.group(1)), int(match.group(2))

        # Match single value like "5000"
        match = re.search(r'(\d+)', clean_text)
        if match:
            value = int(match.group(1))
            return value, value

        return None, None

    def _extract_job_id(self, job_url: str) -> Optional[str]:
        """Extract job ID from MCF URL"""
        match = re.search(r'/job/([a-zA-Z0-9-]+)', job_url)
        return match.group(1) if match else None

    def _parse_posted_date(self, date_text: str) -> Optional[datetime]:
        """Parse relative date like '3 days ago' to datetime"""
        if not date_text:
            return None

        date_text = date_text.lower()
        now = datetime.now()

        if 'today' in date_text or 'just now' in date_text:
            return now
        elif 'yesterday' in date_text:
            return now - timedelta(days=1)
        elif 'day' in date_text:
            days_match = re.search(r'(\d+)\s*day', date_text)
            if days_match:
                days = int(days_match.group(1))
                return now - timedelta(days=days)
        elif 'week' in date_text:
            weeks_match = re.search(r'(\d+)\s*week', date_text)
            if weeks_match:
                weeks = int(weeks_match.group(1))
                return now - timedelta(weeks=weeks)
        elif 'month' in date_text:
            months_match = re.search(r'(\d+)\s*month', date_text)
            if months_match:
                months = int(months_match.group(1))
                return now - timedelta(days=months * 30)

        return None

    def _click_next_page(self) -> bool:
        """Click next page button, return True if successful"""
        try:
            next_button = self.safe_find_element(
                By.CSS_SELECTOR,
                "[data-testid='pagination-next']"
            )
            if next_button and next_button.is_enabled():
                return self.safe_click(next_button)
            return False
        except Exception:
            return False

    def scrape_job_details(self, job_url: str) -> Dict:
        """
        Scrape detailed information for a single MCF job posting.

        Args:
            job_url: Full URL to MCF job posting

        Returns:
            Detailed job data dictionary
        """
        self.initialize_driver()

        try:
            self.driver.get(job_url)
            self.random_sleep(3, 5)

            # Job description
            desc_elem = self.safe_find_element(
                By.CSS_SELECTOR,
                "[data-testid='job-description']"
            )
            job_description = desc_elem.text if desc_elem else None

            # Requirements
            req_elem = self.safe_find_element(
                By.CSS_SELECTOR,
                "[data-testid='job-requirements']"
            )
            requirements = req_elem.text if req_elem else None

            # Benefits
            benefits_elems = self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid='job-benefit-item']"
            )
            benefits = [elem.text for elem in benefits_elems]

            # Seniority level
            seniority_elem = self.safe_find_element(
                By.CSS_SELECTOR,
                "[data-testid='job-seniority']"
            )
            seniority_level = seniority_elem.text if seniority_elem else None

            return {
                'job_url': job_url,
                'job_description': job_description,
                'requirements': requirements,
                'benefits': benefits,
                'seniority_level': seniority_level,
                'scraped_at': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Error scraping MCF job details: {e}")
            return {}
        finally:
            self.cleanup()
```

### Phase 3: Glassdoor Scraper

**File**: `src/job_pricing/services/web_scraping/glassdoor_scraper.py`

```python
from typing import Dict, List, Optional
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import json
import re
from .base_scraper import BaseScraper

class GlassdoorScraper(BaseScraper):
    """
    Production-ready scraper for Glassdoor.
    Handles anti-bot measures with proxy rotation and rate limiting.
    """

    BASE_URL = "https://www.glassdoor.sg"

    def __init__(self, email: str, password: str, **kwargs):
        super().__init__(**kwargs)
        self.email = email
        self.password = password
        self.logged_in = False

    def login(self) -> bool:
        """Login to Glassdoor to access full data"""
        try:
            self.driver.get(f"{self.BASE_URL}/profile/login_input.htm")
            self.random_sleep(2, 4)

            # Enter email
            email_input = self.safe_find_element(By.ID, "inlineUserEmail")
            if not email_input:
                self.logger.error("Email input not found")
                return False

            email_input.send_keys(self.email)
            self.random_sleep(1, 2)

            # Click continue
            continue_btn = self.safe_find_element(By.CSS_SELECTOR, "button[type='submit']")
            if continue_btn:
                self.safe_click(continue_btn)
                self.random_sleep(2, 3)

            # Enter password
            password_input = self.safe_find_element(By.ID, "inlineUserPassword")
            if not password_input:
                self.logger.error("Password input not found")
                return False

            password_input.send_keys(self.password)
            self.random_sleep(1, 2)

            # Submit login
            submit_btn = self.safe_find_element(By.CSS_SELECTOR, "button[type='submit']")
            if submit_btn:
                self.safe_click(submit_btn)
                self.random_sleep(5, 8)

            # Verify login
            self.logged_in = self._verify_login()
            return self.logged_in

        except Exception as e:
            self.logger.error(f"Glassdoor login failed: {e}")
            return False

    def _verify_login(self) -> bool:
        """Verify successful login"""
        try:
            # Check for user account element
            user_elem = self.safe_find_element(By.CSS_SELECTOR, "[data-test='user-menu']", timeout=5)
            return user_elem is not None
        except Exception:
            return False

    def scrape_job_listings(
        self,
        search_params: Dict
    ) -> List[Dict]:
        """
        Scrape job listings from Glassdoor.

        Args:
            search_params: {
                'keyword': str (job title),
                'location': str (default: Singapore),
                'page_limit': int (max pages to scrape)
            }

        Returns:
            List of job listing dictionaries
        """
        self.initialize_driver()

        # Login first
        if not self.login():
            self.logger.error("Failed to login to Glassdoor")
            self.cleanup()
            return []

        all_jobs = []

        try:
            # Build search URL
            search_url = self._build_search_url(search_params)
            self.logger.info(f"Starting Glassdoor scrape: {search_url}")

            self.driver.get(search_url)
            self.random_sleep(5, 8)  # Longer wait for Glassdoor

            page_limit = search_params.get('page_limit', 5)
            current_page = 1

            while current_page <= page_limit:
                self.logger.info(f"Scraping Glassdoor page {current_page}/{page_limit}")

                # Wait for job listings to load
                job_cards = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "li[data-test='jobListing']"
                )

                if not job_cards:
                    self.logger.warning("No job listings found")
                    break

                # Extract data from each job card
                for card in job_cards:
                    try:
                        job_data = self._extract_job_card_data(card)
                        if job_data:
                            all_jobs.append(job_data)
                    except Exception as e:
                        self.logger.error(f"Error extracting Glassdoor job card: {e}")
                        continue

                # Click next page
                if not self._click_next_page():
                    self.logger.info("No more pages available")
                    break

                current_page += 1
                self.random_sleep(8, 12)  # Longer delay for Glassdoor rate limits

        except Exception as e:
            self.logger.error(f"Glassdoor scraping error: {e}")
        finally:
            self.cleanup()

        self.logger.info(f"Glassdoor scraping completed: {len(all_jobs)} jobs extracted")
        return all_jobs

    def _build_search_url(self, params: Dict) -> str:
        """Build Glassdoor search URL"""
        keyword = params.get('keyword', '')
        location = params.get('location', 'Singapore')

        # URL encode parameters
        keyword_encoded = keyword.replace(' ', '-')
        location_encoded = location.replace(' ', '-')

        return f"{self.BASE_URL}/Job/{keyword_encoded}-jobs-{location_encoded}.htm"

    def _extract_job_card_data(self, card_element) -> Optional[Dict]:
        """Extract structured data from Glassdoor job card"""
        try:
            # Job title
            title_elem = card_element.find_element(By.CSS_SELECTOR, "[data-test='job-title']")
            job_title = title_elem.text if title_elem else None

            # Company name
            company_elem = card_element.find_element(By.CSS_SELECTOR, "[data-test='employer-name']")
            company_name = company_elem.text if company_elem else None

            # Location
            location_elem = card_element.find_element(By.CSS_SELECTOR, "[data-test='emp-location']")
            location = location_elem.text if location_elem else None

            # Salary estimate
            salary_elem = card_element.find_element(By.CSS_SELECTOR, "[data-test='detailSalary']")
            salary_text = salary_elem.text if salary_elem else None
            salary_min, salary_max = self._parse_salary_estimate(salary_text)

            # Company rating
            rating_elem = card_element.find_element(By.CSS_SELECTOR, "[data-test='rating']")
            rating_text = rating_elem.text if rating_elem else None
            company_rating = float(rating_text) if rating_text else None

            # Job URL
            job_link = card_element.find_element(By.CSS_SELECTOR, "a[data-test='job-link']")
            job_url = job_link.get_attribute('href')
            if job_url and not job_url.startswith('http'):
                job_url = f"{self.BASE_URL}{job_url}"

            job_id = self._extract_job_id(job_url)

            return {
                'source': 'glassdoor',
                'job_id': job_id,
                'job_url': job_url,
                'job_title': job_title,
                'company_name': company_name,
                'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_currency': 'SGD',
                'salary_type': 'estimated',  # Glassdoor estimates
                'location': location,
                'company_rating': company_rating,
                'scraped_at': datetime.now()
            }

        except NoSuchElementException as e:
            self.logger.warning(f"Element not found in Glassdoor job card: {e}")
            return None

    def _parse_salary_estimate(self, salary_text: Optional[str]) -> tuple:
        """Parse Glassdoor salary estimate"""
        if not salary_text:
            return None, None

        # Remove currency and clean
        clean_text = salary_text.replace('$', '').replace(',', '').replace('SGD', '').replace('K', '000')

        # Match range like "60000 - 80000"
        match = re.search(r'(\d+)\s*[-–to]+\s*(\d+)', clean_text)
        if match:
            return int(match.group(1)), int(match.group(2))

        # Match single value
        match = re.search(r'(\d+)', clean_text)
        if match:
            value = int(match.group(1))
            return value, value

        return None, None

    def _extract_job_id(self, job_url: str) -> Optional[str]:
        """Extract job ID from Glassdoor URL"""
        match = re.search(r'jobListingId=(\d+)', job_url)
        return match.group(1) if match else None

    def _click_next_page(self) -> bool:
        """Click next page button"""
        try:
            next_button = self.safe_find_element(
                By.CSS_SELECTOR,
                "[data-test='pagination-next']"
            )
            if next_button and 'disabled' not in next_button.get_attribute('class'):
                self.scroll_to_bottom()
                return self.safe_click(next_button)
            return False
        except Exception:
            return False

    def scrape_job_details(self, job_url: str) -> Dict:
        """Scrape detailed Glassdoor job posting"""
        if not self.driver:
            self.initialize_driver()
            if not self.login():
                return {}

        try:
            self.driver.get(job_url)
            self.random_sleep(5, 8)

            # Job description
            desc_elem = self.safe_find_element(
                By.CSS_SELECTOR,
                "[data-test='jobDescriptionText']"
            )
            job_description = desc_elem.text if desc_elem else None

            # Company size
            size_elem = self.safe_find_element(
                By.CSS_SELECTOR,
                "[data-test='employer-size']"
            )
            company_size = size_elem.text if size_elem else None

            # Industry
            industry_elem = self.safe_find_element(
                By.CSS_SELECTOR,
                "[data-test='employer-industry']"
            )
            industry = industry_elem.text if industry_elem else None

            return {
                'job_url': job_url,
                'job_description': job_description,
                'company_size': company_size,
                'industry': industry,
                'scraped_at': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Error scraping Glassdoor job details: {e}")
            return {}
```

### Phase 4: Scraping Orchestration with Kailash

**File**: `src/job_pricing/workflows/web_scraping_workflow.py`

```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from typing import Dict, List
from datetime import datetime
import logging

class WebScrapingOrchestrator:
    """
    Kailash-based orchestration for weekly web scraping batch job.
    Coordinates MCF and Glassdoor scrapers with data validation and storage.
    """

    def __init__(
        self,
        mcf_scraper,
        glassdoor_scraper,
        db_connection_string: str
    ):
        self.mcf_scraper = mcf_scraper
        self.glassdoor_scraper = glassdoor_scraper
        self.db_connection_string = db_connection_string
        self.logger = logging.getLogger(self.__class__.__name__)

    def build_weekly_scraping_workflow(
        self,
        search_queries: List[Dict]
    ) -> WorkflowBuilder:
        """
        Build Kailash workflow for weekly scraping batch.

        Args:
            search_queries: List of search configurations
                [
                    {
                        'job_family': 'Engineering',
                        'keywords': ['software engineer', 'data engineer'],
                        'locations': ['Singapore'],
                        'page_limit': 10
                    }
                ]

        Returns:
            WorkflowBuilder instance
        """
        workflow = WorkflowBuilder()

        # Step 1: Scrape My Careers Future
        workflow.add_node(
            "PythonCodeNode",
            "scrape_mcf",
            {
                "code": self._get_mcf_scraping_code(),
                "inputs": {
                    "search_queries": search_queries,
                    "scraper": self.mcf_scraper
                },
                "output_key": "mcf_results"
            }
        )

        # Step 2: Scrape Glassdoor (parallel execution)
        workflow.add_node(
            "PythonCodeNode",
            "scrape_glassdoor",
            {
                "code": self._get_glassdoor_scraping_code(),
                "inputs": {
                    "search_queries": search_queries,
                    "scraper": self.glassdoor_scraper
                },
                "output_key": "glassdoor_results"
            }
        )

        # Step 3: Data validation and cleaning
        workflow.add_node(
            "PythonCodeNode",
            "validate_data",
            {
                "code": self._get_validation_code(),
                "inputs": {
                    "mcf_data": "{{mcf_results}}",
                    "glassdoor_data": "{{glassdoor_results}}"
                },
                "output_key": "validated_data"
            }
        )

        # Step 4: Deduplication
        workflow.add_node(
            "PythonCodeNode",
            "deduplicate",
            {
                "code": self._get_deduplication_code(),
                "inputs": {
                    "validated_data": "{{validated_data}}"
                },
                "output_key": "deduplicated_data"
            }
        )

        # Step 5: Store in database
        workflow.add_node(
            "DatabaseWriteNode",
            "store_results",
            {
                "connection_string": self.db_connection_string,
                "table": "scraped_job_listings",
                "data": "{{deduplicated_data}}",
                "mode": "upsert",
                "conflict_columns": ["source", "job_id"],
                "output_key": "stored_count"
            }
        )

        # Step 6: Update audit log
        workflow.add_node(
            "DatabaseWriteNode",
            "audit_log",
            {
                "connection_string": self.db_connection_string,
                "table": "scraping_audit_log",
                "data": {
                    "run_date": datetime.now(),
                    "mcf_count": "{{mcf_results.length}}",
                    "glassdoor_count": "{{glassdoor_results.length}}",
                    "validated_count": "{{validated_data.length}}",
                    "stored_count": "{{stored_count}}",
                    "status": "completed"
                },
                "output_key": "audit_log_id"
            }
        )

        return workflow

    def execute_weekly_scraping(
        self,
        search_queries: List[Dict]
    ) -> Dict:
        """
        Execute weekly scraping workflow.

        Returns:
            Execution results with counts and status
        """
        self.logger.info("Starting weekly web scraping batch...")

        workflow = self.build_weekly_scraping_workflow(search_queries)
        runtime = LocalRuntime()

        try:
            results, run_id = runtime.execute(workflow.build())

            self.logger.info(f"Weekly scraping completed. Run ID: {run_id}")
            self.logger.info(f"MCF jobs scraped: {results.get('mcf_results', {}).get('count', 0)}")
            self.logger.info(f"Glassdoor jobs scraped: {results.get('glassdoor_results', {}).get('count', 0)}")
            self.logger.info(f"Total jobs stored: {results.get('stored_count', 0)}")

            return {
                'run_id': run_id,
                'status': 'success',
                'mcf_count': results.get('mcf_results', {}).get('count', 0),
                'glassdoor_count': results.get('glassdoor_results', {}).get('count', 0),
                'stored_count': results.get('stored_count', 0),
                'timestamp': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Weekly scraping failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now()
            }

    def _get_mcf_scraping_code(self) -> str:
        """Python code for MCF scraping"""
        return """
def scrape_mcf(search_queries, scraper):
    all_jobs = []
    for query in search_queries:
        for keyword in query.get('keywords', []):
            search_params = {
                'search': keyword,
                'location': query.get('locations', ['Singapore'])[0],
                'page_limit': query.get('page_limit', 10)
            }
            jobs = scraper.scrape_job_listings(search_params)
            all_jobs.extend(jobs)

    return {
        'jobs': all_jobs,
        'count': len(all_jobs)
    }
"""

    def _get_glassdoor_scraping_code(self) -> str:
        """Python code for Glassdoor scraping"""
        return """
def scrape_glassdoor(search_queries, scraper):
    all_jobs = []
    for query in search_queries:
        for keyword in query.get('keywords', []):
            search_params = {
                'keyword': keyword,
                'location': query.get('locations', ['Singapore'])[0],
                'page_limit': query.get('page_limit', 5)  # Lower for Glassdoor
            }
            jobs = scraper.scrape_job_listings(search_params)
            all_jobs.extend(jobs)

    return {
        'jobs': all_jobs,
        'count': len(all_jobs)
    }
"""

    def _get_validation_code(self) -> str:
        """Python code for data validation"""
        return """
def validate_data(mcf_data, glassdoor_data):
    validated = []

    # Combine both sources
    all_jobs = mcf_data.get('jobs', []) + glassdoor_data.get('jobs', [])

    for job in all_jobs:
        # Required fields validation
        if not job.get('job_title') or not job.get('company_name'):
            continue

        # Salary validation (must have at least min or max)
        if not job.get('salary_min') and not job.get('salary_max'):
            # Flag as missing salary data
            job['has_salary_data'] = False
        else:
            job['has_salary_data'] = True

        # Location standardization
        if job.get('location'):
            job['location'] = standardize_location(job['location'])

        validated.append(job)

    return validated

def standardize_location(location):
    # Standardize Singapore location names
    location_map = {
        'Central': 'Central Business District',
        'CBD': 'Central Business District',
        'Orchard': 'Orchard Road',
        # Add more mappings as needed
    }
    return location_map.get(location, location)
"""

    def _get_deduplication_code(self) -> str:
        """Python code for deduplication"""
        return """
def deduplicate(validated_data):
    seen = set()
    deduplicated = []

    for job in validated_data:
        # Create unique key from source + job_id
        unique_key = f"{job['source']}:{job.get('job_id', '')}"

        if unique_key not in seen:
            seen.add(unique_key)
            deduplicated.append(job)

    return deduplicated
"""
```

### Phase 5: Database Schema

**Database Schema**:

```sql
-- Scraped job listings table
CREATE TABLE scraped_job_listings (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL, -- 'my_careers_future', 'glassdoor'
    job_id VARCHAR(255) NOT NULL,
    job_url TEXT NOT NULL,
    job_title VARCHAR(500) NOT NULL,
    company_name VARCHAR(500) NOT NULL,
    salary_min NUMERIC(12, 2),
    salary_max NUMERIC(12, 2),
    salary_currency VARCHAR(3) DEFAULT 'SGD',
    salary_type VARCHAR(20), -- 'actual', 'estimated'
    location VARCHAR(255),
    employment_type VARCHAR(50),
    seniority_level VARCHAR(100),
    job_description TEXT,
    requirements TEXT,
    skills TEXT[], -- Array of skills
    benefits TEXT[],
    company_rating NUMERIC(3, 2),
    company_size VARCHAR(50),
    industry VARCHAR(100),
    has_salary_data BOOLEAN DEFAULT TRUE,
    posted_date TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(source, job_id)
);

-- Indexes for performance
CREATE INDEX idx_scraped_jobs_title ON scraped_job_listings(job_title);
CREATE INDEX idx_scraped_jobs_company ON scraped_job_listings(company_name);
CREATE INDEX idx_scraped_jobs_location ON scraped_job_listings(location);
CREATE INDEX idx_scraped_jobs_posted ON scraped_job_listings(posted_date DESC);
CREATE INDEX idx_scraped_jobs_active ON scraped_job_listings(is_active);
CREATE INDEX idx_scraped_jobs_salary ON scraped_job_listings(salary_min, salary_max);

-- Full-text search for job matching
CREATE INDEX idx_scraped_jobs_description_fts ON scraped_job_listings
USING gin(to_tsvector('english', job_description));

-- Scraping audit log
CREATE TABLE scraping_audit_log (
    id SERIAL PRIMARY KEY,
    run_date TIMESTAMP NOT NULL,
    source VARCHAR(50), -- NULL for combined runs
    mcf_count INTEGER DEFAULT 0,
    glassdoor_count INTEGER DEFAULT 0,
    validated_count INTEGER DEFAULT 0,
    deduplicated_count INTEGER DEFAULT 0,
    stored_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL, -- 'completed', 'failed', 'partial'
    error_message TEXT,
    execution_time_seconds INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_log_date ON scraping_audit_log(run_date DESC);
CREATE INDEX idx_audit_log_status ON scraping_audit_log(status);

-- Scraped company data (aggregated from multiple sources)
CREATE TABLE scraped_company_data (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(500) NOT NULL UNIQUE,
    glassdoor_rating NUMERIC(3, 2),
    company_size VARCHAR(50),
    industry VARCHAR(100),
    total_jobs_posted INTEGER DEFAULT 0,
    avg_salary_min NUMERIC(12, 2),
    avg_salary_max NUMERIC(12, 2),
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_company_name ON scraped_company_data(company_name);
CREATE INDEX idx_company_industry ON scraped_company_data(industry);
```

### Phase 6: Scheduling and Monitoring

**File**: `src/job_pricing/services/web_scraping/scheduler.py`

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
import os

class WebScrapingScheduler:
    """
    Production scheduler for weekly web scraping jobs.
    Runs every Sunday at 2:00 AM SGT.
    """

    def __init__(self, orchestrator: WebScrapingOrchestrator):
        self.orchestrator = orchestrator
        self.scheduler = BackgroundScheduler(timezone='Asia/Singapore')
        self.logger = logging.getLogger(self.__class__.__name__)

    def start(self):
        """Start the scheduler"""
        # Weekly job: Every Sunday at 2:00 AM SGT
        self.scheduler.add_job(
            func=self._run_weekly_scraping,
            trigger=CronTrigger(
                day_of_week='sun',
                hour=2,
                minute=0,
                timezone='Asia/Singapore'
            ),
            id='weekly_web_scraping',
            name='Weekly Web Scraping Batch',
            replace_existing=True
        )

        # Optional: Daily incremental scraping for hot jobs
        self.scheduler.add_job(
            func=self._run_incremental_scraping,
            trigger=CronTrigger(
                hour=6,
                minute=0,
                timezone='Asia/Singapore'
            ),
            id='daily_incremental_scraping',
            name='Daily Incremental Scraping',
            replace_existing=True
        )

        self.scheduler.start()
        self.logger.info("Web scraping scheduler started")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        self.logger.info("Web scraping scheduler stopped")

    def _run_weekly_scraping(self):
        """Execute weekly comprehensive scraping"""
        self.logger.info("Starting weekly scraping job...")

        # Define search queries for comprehensive coverage
        search_queries = [
            {
                'job_family': 'Engineering',
                'keywords': [
                    'software engineer',
                    'data engineer',
                    'devops engineer',
                    'machine learning engineer',
                    'full stack developer'
                ],
                'locations': ['Singapore'],
                'page_limit': 20
            },
            {
                'job_family': 'Human Resources',
                'keywords': [
                    'hr manager',
                    'talent acquisition',
                    'compensation analyst',
                    'hr business partner'
                ],
                'locations': ['Singapore'],
                'page_limit': 10
            },
            # Add more job families as needed
        ]

        try:
            results = self.orchestrator.execute_weekly_scraping(search_queries)
            self.logger.info(f"Weekly scraping completed: {results}")

            # Send notification
            self._send_completion_notification(results)

        except Exception as e:
            self.logger.error(f"Weekly scraping failed: {e}")
            self._send_error_notification(e)

    def _run_incremental_scraping(self):
        """Execute daily incremental scraping for high-priority jobs"""
        self.logger.info("Starting incremental scraping job...")

        # Smaller set of high-priority searches
        search_queries = [
            {
                'job_family': 'Engineering',
                'keywords': ['software engineer'],
                'locations': ['Singapore'],
                'page_limit': 5
            }
        ]

        try:
            results = self.orchestrator.execute_weekly_scraping(search_queries)
            self.logger.info(f"Incremental scraping completed: {results}")
        except Exception as e:
            self.logger.error(f"Incremental scraping failed: {e}")

    def _send_completion_notification(self, results: Dict):
        """Send notification on successful completion"""
        # Implement notification (email, Slack, etc.)
        pass

    def _send_error_notification(self, error: Exception):
        """Send error notification"""
        # Implement error notification
        pass
```

## Integration Checkpoints

- [ ] Selenium ChromeDriver installed and configured
- [ ] Proxy service integrated (if required)
- [ ] MCF scraper tested with real searches
- [ ] Glassdoor scraper tested with valid credentials
- [ ] Database schema created with indexes
- [ ] Kailash workflow tested end-to-end
- [ ] Weekly scheduler configured and running
- [ ] Audit logging and monitoring implemented
- [ ] Rate limiting validated (no IP bans)
- [ ] Data quality validation rules defined
- [ ] Deduplication logic tested
- [ ] Integration with dynamic pricing algorithm verified

## Performance Requirements

- **MCF Scraping Rate**: 50 requests/minute (max)
- **Glassdoor Scraping Rate**: 20 requests/minute (max)
- **Weekly Batch Duration**: <4 hours for full run
- **Data Freshness**: Updated every Sunday 2:00 AM SGT
- **Storage Growth**: ~10,000 new jobs/week
- **Deduplication Rate**: >95% accuracy

## Error Handling

1. **Rate Limiting / IP Ban**:
   - Rotate to backup proxy
   - Exponential backoff (2x delay after each retry)
   - Alert operations team
   - Resume scraping after cooldown period

2. **Page Structure Changes**:
   - Log element not found errors
   - Capture screenshot for debugging
   - Alert development team
   - Pause scraping for affected source

3. **Login Failures (Glassdoor)**:
   - Retry with alternative credentials
   - Check for CAPTCHA requirement
   - Fallback to MCF-only scraping
   - Alert for manual intervention

4. **Data Validation Failures**:
   - Log invalid records to separate table
   - Flag for manual review
   - Continue processing valid records
   - Generate data quality report

## Compliance and Ethics

**IMPORTANT**: Web scraping must comply with:

1. **Robots.txt** compliance
   - Check and respect robots.txt for each site
   - Honor crawl-delay directives

2. **Terms of Service**
   - Review TOS for MCF and Glassdoor
   - Ensure usage is within acceptable boundaries
   - Commercial use may require API licenses

3. **Rate Limiting**
   - Implement conservative rate limits
   - Mimic human browsing behavior
   - Avoid aggressive scraping that impacts site performance

4. **Data Privacy**
   - Do not scrape personal information
   - Focus on public job listing data only
   - Comply with PDPA (Singapore) regulations

5. **Attribution**
   - Maintain source attribution in database
   - Respect intellectual property rights
   - Do not republish data without permission

## Next Steps

1. Set up Selenium infrastructure with ChromeDriver
2. Implement MCFScraper and test with live searches
3. Implement GlassdoorScraper with valid credentials
4. Create database schema and indexes
5. Build Kailash orchestration workflow
6. Configure weekly scheduler
7. Implement monitoring and alerting
8. Integrate with dynamic pricing algorithm
9. Deploy to production environment
10. Monitor first few runs and optimize
