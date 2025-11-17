"""
Custom exceptions for Job Pricing Engine.

Provides specific exception types for better error handling and debugging.
"""


class JobPricingException(Exception):
    """Base exception for all job pricing errors."""
    pass


class DataSourceException(JobPricingException):
    """Raised when a data source is unavailable or returns invalid data."""

    def __init__(self, source_name: str, message: str, original_error: Exception = None):
        self.source_name = source_name
        self.original_error = original_error
        super().__init__(f"{source_name} error: {message}")


class EmbeddingGenerationException(JobPricingException):
    """Raised when OpenAI embedding generation fails."""

    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(f"Embedding generation failed: {message}")


class VectorSearchException(JobPricingException):
    """Raised when vector similarity search fails."""

    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(f"Vector search failed: {message}")


class JobMatchingException(JobPricingException):
    """Raised when job matching fails."""

    def __init__(self, message: str, job_title: str = None, original_error: Exception = None):
        self.job_title = job_title
        self.original_error = original_error
        super().__init__(f"Job matching failed{f' for {job_title}' if job_title else ''}: {message}")


class DataValidationException(JobPricingException):
    """Raised when input data fails validation."""

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Validation error for {field}: {message}")


class InsufficientDataException(JobPricingException):
    """Raised when there is insufficient data to generate pricing."""

    def __init__(self, message: str, sources_attempted: list = None):
        self.sources_attempted = sources_attempted or []
        super().__init__(f"Insufficient data: {message}")


class DatabaseConnectionException(JobPricingException):
    """Raised when database connection or query fails."""

    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(f"Database error: {message}")


class ConfigurationException(JobPricingException):
    """Raised when configuration is missing or invalid."""

    def __init__(self, config_key: str, message: str):
        self.config_key = config_key
        super().__init__(f"Configuration error for {config_key}: {message}")


class RateLimitException(JobPricingException):
    """Raised when an API rate limit is exceeded."""

    def __init__(self, service: str, retry_after: int = None):
        self.service = service
        self.retry_after = retry_after
        message = f"{service} rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(message)
