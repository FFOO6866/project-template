"""
Utility functions for the Horme web scraper.
"""

import logging
import random
import time
import os
from typing import List, Dict, Any
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin
import requests

from .models import ScrapingConfig


def get_default_config() -> ScrapingConfig:
    """Get default scraping configuration."""
    return ScrapingConfig()


def setup_logging(config: ScrapingConfig, log_file: str = "horme_scraper.log") -> logging.Logger:
    """Set up logging for the scraper."""
    logger = logging.getLogger("horme_scraper")
    logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_user_agents() -> List[str]:
    """Get a list of realistic user agents for rotation."""
    return [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
        
        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]


def get_random_headers(user_agent: str = None) -> Dict[str, str]:
    """Get randomized headers for requests."""
    if not user_agent:
        user_agent = random.choice(get_user_agents())
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }
    
    # Randomly add some optional headers
    if random.random() < 0.5:
        headers["Sec-CH-UA"] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        headers["Sec-CH-UA-Mobile"] = "?0"
        headers["Sec-CH-UA-Platform"] = '"Windows"'
    
    return headers


def check_robots_txt(base_url: str, user_agent: str = "*") -> Dict[str, Any]:
    """Check robots.txt compliance."""
    try:
        robots_url = urljoin(base_url, "/robots.txt")
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        
        # Check common paths
        test_paths = ["/", "/search", "/product", "/products", "/catalog"]
        allowed_paths = []
        disallowed_paths = []
        
        for path in test_paths:
            if rp.can_fetch(user_agent, path):
                allowed_paths.append(path)
            else:
                disallowed_paths.append(path)
        
        # Get crawl delay
        crawl_delay = rp.crawl_delay(user_agent)
        
        return {
            "robots_txt_url": robots_url,
            "crawl_delay": crawl_delay,
            "allowed_paths": allowed_paths,
            "disallowed_paths": disallowed_paths,
            "can_fetch_root": rp.can_fetch(user_agent, "/"),
            "success": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "crawl_delay": 5.0  # Default to 5 seconds as specified
        }


def exponential_backoff(attempt: int, base_delay: float = 1.0, factor: float = 2.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff delay."""
    delay = base_delay * (factor ** attempt)
    # Add jitter
    jitter = random.uniform(0.1, 0.5) * delay
    return min(delay + jitter, max_delay)


def rate_limit_wait(last_request_time: float, rate_limit_seconds: float) -> None:
    """Wait for rate limiting if necessary."""
    current_time = time.time()
    time_since_last = current_time - last_request_time
    
    if time_since_last < rate_limit_seconds:
        wait_time = rate_limit_seconds - time_since_last
        time.sleep(wait_time)


def clean_text(text: str) -> str:
    """Clean and normalize text data."""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = " ".join(text.split())
    
    # Remove common unwanted characters
    text = text.replace("\u00a0", " ")  # Non-breaking space
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")
    
    return text.strip()


def extract_price(text: str) -> str:
    """Extract price from text."""
    import re
    
    if not text:
        return ""
    
    # Common price patterns for Singapore
    price_patterns = [
        r'S\$\s*[\d,]+\.?\d*',  # S$123.45 or S$123
        r'\$\s*[\d,]+\.?\d*',   # $123.45 or $123
        r'SGD\s*[\d,]+\.?\d*',  # SGD123.45
        r'[\d,]+\.?\d*\s*SGD',  # 123.45 SGD
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return clean_text(match.group())
    
    return clean_text(text)


def ensure_directory_exists(directory: str) -> None:
    """Ensure a directory exists, create if it doesn't."""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def save_json_data(data: List[Dict[str, Any]], filename: str) -> bool:
    """Save data to JSON file."""
    try:
        import json
        ensure_directory_exists(os.path.dirname(filename))
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        logging.getLogger("horme_scraper").error(f"Error saving JSON data: {e}")
        return False


def save_csv_data(data: List[Dict[str, Any]], filename: str) -> bool:
    """Save data to CSV file."""
    try:
        import pandas as pd
        ensure_directory_exists(os.path.dirname(filename))
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
        
        return True
    except Exception as e:
        logging.getLogger("horme_scraper").error(f"Error saving CSV data: {e}")
        return False


def validate_url(url: str) -> bool:
    """Validate if a URL is properly formatted."""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None


def parse_specifications(spec_text: str) -> Dict[str, str]:
    """Parse product specifications from text."""
    if not spec_text:
        return {}
    
    specs = {}
    lines = spec_text.split('\n')
    
    for line in lines:
        line = clean_text(line)
        if ':' in line:
            key, value = line.split(':', 1)
            key = clean_text(key)
            value = clean_text(value)
            if key and value:
                specs[key] = value
        elif line.strip():
            # If no colon, use the line as both key and value
            specs[line] = line
    
    return specs