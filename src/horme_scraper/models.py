"""
Data models for the Horme web scraper.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


@dataclass
class ProductData:
    """Data model for scraped product information."""
    
    sku: str
    name: str = ""
    price: str = ""
    description: str = ""
    specifications: Dict[str, Any] = field(default_factory=dict)
    images: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    availability: str = ""
    brand: str = ""
    url: str = ""
    scraped_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the product data to a dictionary."""
        return {
            "sku": self.sku,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "specifications": self.specifications,
            "images": self.images,
            "categories": self.categories,
            "availability": self.availability,
            "brand": self.brand,
            "url": self.url,
            "scraped_at": self.scraped_at.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert the product data to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass
class ScrapingConfig:
    """Configuration for the scraping behavior."""
    
    # Rate limiting
    rate_limit_seconds: float = 5.0  # Based on robots.txt requirement (max 1 req per 5 seconds)
    max_requests_per_hour: int = 720  # Conservative limit
    
    # Retry logic
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    retry_base_delay: float = 1.0
    
    # Timeouts
    request_timeout: int = 30
    connection_timeout: int = 10
    
    # Headers and user agents
    rotate_user_agents: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    # Logging
    log_level: str = "INFO"
    log_requests: bool = True
    log_responses: bool = True
    
    # Storage
    output_directory: str = "scraped_data"
    save_json: bool = True
    save_csv: bool = False
    
    # Safety
    respect_robots_txt: bool = True
    check_robots_txt_interval: int = 3600  # Check robots.txt every hour
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "rate_limit_seconds": self.rate_limit_seconds,
            "max_requests_per_hour": self.max_requests_per_hour,
            "max_retries": self.max_retries,
            "retry_backoff_factor": self.retry_backoff_factor,
            "retry_base_delay": self.retry_base_delay,
            "request_timeout": self.request_timeout,
            "connection_timeout": self.connection_timeout,
            "rotate_user_agents": self.rotate_user_agents,
            "custom_headers": self.custom_headers,
            "log_level": self.log_level,
            "log_requests": self.log_requests,
            "log_responses": self.log_responses,
            "output_directory": self.output_directory,
            "save_json": self.save_json,
            "save_csv": self.save_csv,
            "respect_robots_txt": self.respect_robots_txt,
            "check_robots_txt_interval": self.check_robots_txt_interval
        }


@dataclass
class ScrapingSession:
    """Track scraping session statistics."""
    
    session_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    requests_made: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    products_scraped: int = 0
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error to the session."""
        self.errors.append(f"{datetime.now().isoformat()}: {error}")
    
    def finish_session(self) -> None:
        """Mark the session as finished."""
        self.end_time = datetime.now()
    
    def get_duration(self) -> Optional[float]:
        """Get session duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.get_duration(),
            "requests_made": self.requests_made,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "products_scraped": self.products_scraped,
            "success_rate": self.successful_requests / max(self.requests_made, 1),
            "errors": self.errors
        }