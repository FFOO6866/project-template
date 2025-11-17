"""
Base Scraper Class

Provides common functionality for all web scrapers:
- Selenium browser initialization
- Error handling and retries
- Rate limiting
- Logging and monitoring
"""

import time
import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from job_pricing.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseScraper(ABC):
    """
    Base class for all web scrapers.

    Provides common browser initialization, error handling, and retry logic.
    Subclasses must implement the scrape() method.
    """

    def __init__(
        self,
        headless: bool = True,
        page_load_timeout: int = 30,
        implicit_wait: int = 10,
    ):
        """
        Initialize base scraper.

        Args:
            headless: Run browser in headless mode (no GUI)
            page_load_timeout: Maximum time to wait for page load (seconds)
            implicit_wait: Implicit wait time for elements (seconds)
        """
        self.headless = headless
        self.page_load_timeout = page_load_timeout
        self.implicit_wait = implicit_wait
        self.driver: Optional[webdriver.Chrome] = None
        self.results: List[Dict[str, Any]] = []
        self.errors: List[str] = []

    def init_browser(self) -> webdriver.Chrome:
        """
        Initialize Chrome browser with optimal settings.

        Returns:
            Configured Chrome WebDriver instance
        """
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")

        # Performance and anti-detection options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        # User agent rotation (reduce bot detection)
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        # Experimental options
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Initialize driver
        # Try to use system chromium-driver (Docker) or download Chrome driver (local)
        try:
            # Docker environment: use system chromium-driver
            chrome_options.binary_location = "/usr/bin/chromium"
            service = Service("/usr/bin/chromium-driver")
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Using system Chromium driver")
        except Exception as e:
            # Local environment: download Chrome driver
            logger.info(f"System driver not found ({e}), downloading Chrome driver...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Using downloaded Chrome driver")

        # Set timeouts
        driver.set_page_load_timeout(self.page_load_timeout)
        driver.implicitly_wait(self.implicit_wait)

        # Remove webdriver flag (anti-detection)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        logger.info(f"Initialized Chrome browser (headless={self.headless})")
        return driver

    def wait_for_element(
        self,
        by: By,
        value: str,
        timeout: int = 10,
        condition: str = "presence",
    ) -> Optional[Any]:
        """
        Wait for element to appear with specified condition.

        Args:
            by: Selenium By locator type
            value: Locator value
            timeout: Maximum wait time (seconds)
            condition: Condition type ('presence', 'visible', 'clickable')

        Returns:
            Element if found, None otherwise
        """
        try:
            wait = WebDriverWait(self.driver, timeout)

            conditions = {
                "presence": EC.presence_of_element_located,
                "visible": EC.visibility_of_element_located,
                "clickable": EC.element_to_be_clickable,
            }

            condition_func = conditions.get(condition, EC.presence_of_element_located)
            element = wait.until(condition_func((by, value)))

            return element

        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {by}='{value}'")
            return None

    def safe_get_text(self, element, default: str = "") -> str:
        """Safely extract text from element."""
        try:
            return element.text.strip() if element else default
        except Exception as e:
            logger.debug(f"Error extracting text: {e}")
            return default

    def safe_get_attribute(self, element, attribute: str, default: str = "") -> str:
        """Safely extract attribute from element."""
        try:
            return element.get_attribute(attribute) or default
        except Exception as e:
            logger.debug(f"Error extracting attribute '{attribute}': {e}")
            return default

    def scroll_page(self, pause_time: float = 0.5):
        """Scroll page to load lazy-loaded content."""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            while True:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(pause_time)

                # Calculate new height
                new_height = self.driver.execute_script("return document.body.scrollHeight")

                if new_height == last_height:
                    break

                last_height = new_height

        except Exception as e:
            logger.warning(f"Error during page scroll: {e}")

    def retry_on_failure(self, func, max_retries: int = 3, delay: int = 2):
        """
        Retry function on failure with exponential backoff.

        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            delay: Initial delay between retries (doubles each retry)

        Returns:
            Function result or None on failure
        """
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed after {max_retries} attempts: {e}")
                    self.errors.append(str(e))
                    return None

                wait_time = delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)

    @abstractmethod
    def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape data from target website.

        Must be implemented by subclasses.

        Args:
            **kwargs: Scraper-specific parameters

        Returns:
            List of scraped job records
        """
        pass

    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute scraping workflow with browser lifecycle management.

        Args:
            **kwargs: Scraper-specific parameters

        Returns:
            Results dictionary with data, count, errors
        """
        start_time = datetime.now()

        try:
            # Initialize browser
            self.driver = self.init_browser()
            logger.info(f"Starting scrape with params: {kwargs}")

            # Execute scrape
            self.results = self.scrape(**kwargs)

            # Calculate stats
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Scrape completed: {len(self.results)} results, "
                f"{len(self.errors)} errors, {execution_time:.2f}s"
            )

            return {
                "success": True,
                "data": self.results,
                "count": len(self.results),
                "errors": self.errors,
                "execution_time_seconds": execution_time,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Fatal scraping error: {e}", exc_info=True)
            return {
                "success": False,
                "data": [],
                "count": 0,
                "errors": self.errors + [str(e)],
                "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat(),
            }

        finally:
            # Cleanup browser
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Browser closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.driver = self.init_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing browser in context manager: {e}")
