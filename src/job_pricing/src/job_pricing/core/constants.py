"""
Application Constants

Centralized constants to ensure consistency across the application.
"""

# Data Source Identifiers
class DataSource:
    """Data source identifiers for scraped job listings."""
    MY_CAREERS_FUTURE = "my_careers_future"
    GLASSDOOR = "glassdoor"

    @classmethod
    def all(cls):
        """Get all valid data sources."""
        return [cls.MY_CAREERS_FUTURE, cls.GLASSDOOR]


# API Configuration
class APIConfig:
    """API configuration constants."""
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    CACHE_TTL_SECONDS = 1800  # 30 minutes

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = 60
    RATE_LIMIT_PER_HOUR = 1000


# Error Messages
class ErrorMessages:
    """Standard error messages."""
    DATABASE_ERROR = "Database temporarily unavailable"
    INVALID_REQUEST = "Invalid request parameters"
    RATE_LIMIT_EXCEEDED = "Rate limit exceeded. Please try again later."
    INTERNAL_ERROR = "Internal server error"
    NO_DATA_FOUND = "No data found for the specified criteria"
