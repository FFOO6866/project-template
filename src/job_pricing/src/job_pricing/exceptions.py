"""
Custom exceptions for Job Pricing Engine.

Provides specific exception types for better error handling and debugging.
Each exception includes HTTP status code for proper API responses.
"""

from typing import Optional


class JobPricingException(Exception):
    """
    Base exception for all job pricing errors.

    Attributes:
        http_status_code: HTTP status code for API responses (default 500)
        error_code: Machine-readable error code for clients
        message: Human-readable error message
    """
    http_status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert exception to API response format."""
        return {
            "success": False,
            "error": self.message,
            "error_code": self.error_code,
        }


__all__ = [
    "JobPricingException",
    "DataSourceException",
    "EmbeddingGenerationException",
    "VectorSearchException",
    "JobMatchingException",
    "DataValidationException",
    "InsufficientDataException",
    "NoMarketDataError",
    "DatabaseConnectionException",
    "ConfigurationException",
    "RateLimitException",
    "ResourceNotFoundException",
    "AuthenticationException",
    "AuthorizationException",
    "ExternalServiceException",
]


class DataSourceException(JobPricingException):
    """Raised when a data source is unavailable or returns invalid data."""
    http_status_code = 503  # Service Unavailable
    error_code = "DATA_SOURCE_ERROR"

    def __init__(self, source_name: str, message: str, original_error: Exception = None):
        self.source_name = source_name
        self.original_error = original_error
        super().__init__(f"{source_name} error: {message}")


class EmbeddingGenerationException(JobPricingException):
    """Raised when OpenAI embedding generation fails."""
    http_status_code = 503  # Service Unavailable
    error_code = "EMBEDDING_ERROR"

    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(f"Embedding generation failed: {message}")


class VectorSearchException(JobPricingException):
    """Raised when vector similarity search fails."""
    http_status_code = 503  # Service Unavailable
    error_code = "VECTOR_SEARCH_ERROR"

    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(f"Vector search failed: {message}")


class JobMatchingException(JobPricingException):
    """Raised when job matching fails."""
    http_status_code = 404  # Not Found
    error_code = "JOB_MATCHING_ERROR"

    def __init__(self, message: str, job_title: str = None, original_error: Exception = None):
        self.job_title = job_title
        self.original_error = original_error
        super().__init__(f"Job matching failed{f' for {job_title}' if job_title else ''}: {message}")


class DataValidationException(JobPricingException):
    """Raised when input data fails validation."""
    http_status_code = 422  # Unprocessable Entity
    error_code = "VALIDATION_ERROR"

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Validation error for {field}: {message}")


class InsufficientDataException(JobPricingException):
    """Raised when there is insufficient data to generate pricing."""
    http_status_code = 404  # Not Found
    error_code = "INSUFFICIENT_DATA"

    def __init__(self, message: str, sources_attempted: list = None):
        self.sources_attempted = sources_attempted or []
        super().__init__(f"Insufficient data: {message}")


class NoMarketDataError(JobPricingException):
    """
    Raised when NO market data sources are available for pricing calculation.

    This is a HARD FAILURE - no fallback/mock data should be used.
    The API layer must return a proper error to the client.

    NO MOCK DATA - This indicates we cannot provide a recommendation.
    """
    http_status_code = 404  # Not Found
    error_code = "NO_MARKET_DATA"

    def __init__(self, job_title: str, sources_attempted: list = None):
        self.job_title = job_title
        self.sources_attempted = sources_attempted or []
        message = (
            f"No market data available for job: '{job_title}'. "
            f"Unable to generate salary recommendation. "
            f"Attempted sources: {', '.join(sources_attempted) if sources_attempted else 'all sources'}."
        )
        super().__init__(message)


class DatabaseConnectionException(JobPricingException):
    """Raised when database connection or query fails."""
    http_status_code = 503  # Service Unavailable
    error_code = "DATABASE_ERROR"

    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(f"Database error: {message}")


class ConfigurationException(JobPricingException):
    """Raised when configuration is missing or invalid."""
    http_status_code = 500  # Internal Server Error
    error_code = "CONFIG_ERROR"

    def __init__(self, config_key: str, message: str):
        self.config_key = config_key
        super().__init__(f"Configuration error for {config_key}: {message}")


class RateLimitException(JobPricingException):
    """Raised when an API rate limit is exceeded."""
    http_status_code = 429  # Too Many Requests
    error_code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, service: str, retry_after: int = None):
        self.service = service
        self.retry_after = retry_after
        message = f"{service} rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(message)


class ResourceNotFoundException(JobPricingException):
    """Raised when a requested resource is not found."""
    http_status_code = 404  # Not Found
    error_code = "NOT_FOUND"

    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} not found: {resource_id}")


class AuthenticationException(JobPricingException):
    """Raised when authentication fails."""
    http_status_code = 401  # Unauthorized
    error_code = "AUTH_ERROR"

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message)


class AuthorizationException(JobPricingException):
    """Raised when user lacks permission."""
    http_status_code = 403  # Forbidden
    error_code = "FORBIDDEN"

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message)


class ExternalServiceException(JobPricingException):
    """Raised when an external service (OpenAI, Mercer, etc.) fails."""
    http_status_code = 503  # Service Unavailable
    error_code = "EXTERNAL_SERVICE_ERROR"

    def __init__(self, service_name: str, message: str, original_error: Exception = None):
        self.service_name = service_name
        self.original_error = original_error
        super().__init__(f"{service_name} service error: {message}")
