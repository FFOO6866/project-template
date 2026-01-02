"""
Unit Tests for Custom Exception Hierarchy

Tests all custom exceptions for:
- Correct HTTP status codes
- Correct error codes
- to_dict() API response format
- Proper inheritance
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from job_pricing.exceptions import (
    JobPricingException,
    DataSourceException,
    EmbeddingGenerationException,
    VectorSearchException,
    JobMatchingException,
    DataValidationException,
    InsufficientDataException,
    NoMarketDataError,
    DatabaseConnectionException,
    ConfigurationException,
    RateLimitException,
    ResourceNotFoundException,
    AuthenticationException,
    AuthorizationException,
    ExternalServiceException,
)


class TestJobPricingException:
    """Tests for base exception class."""

    def test_default_http_status_code(self):
        """Test default HTTP status code is 500."""
        exc = JobPricingException("Test error")
        assert exc.http_status_code == 500

    def test_default_error_code(self):
        """Test default error code is INTERNAL_ERROR."""
        exc = JobPricingException("Test error")
        assert exc.error_code == "INTERNAL_ERROR"

    def test_message_attribute(self):
        """Test message is stored as attribute."""
        exc = JobPricingException("Custom message")
        assert exc.message == "Custom message"

    def test_str_representation(self):
        """Test string representation matches message."""
        exc = JobPricingException("Error message")
        assert str(exc) == "Error message"

    def test_to_dict_format(self):
        """Test to_dict returns proper API response format."""
        exc = JobPricingException("Test error")
        result = exc.to_dict()

        assert result == {
            "success": False,
            "error": "Test error",
            "error_code": "INTERNAL_ERROR",
        }

    def test_inheritance_from_exception(self):
        """Test that JobPricingException inherits from Exception."""
        exc = JobPricingException("Test")
        assert isinstance(exc, Exception)


class TestDataSourceException:
    """Tests for DataSourceException."""

    def test_http_status_code(self):
        """Test HTTP status code is 503 Service Unavailable."""
        exc = DataSourceException("MCF", "Connection failed")
        assert exc.http_status_code == 503

    def test_error_code(self):
        """Test error code is DATA_SOURCE_ERROR."""
        exc = DataSourceException("MCF", "Connection failed")
        assert exc.error_code == "DATA_SOURCE_ERROR"

    def test_source_name_stored(self):
        """Test source name is stored."""
        exc = DataSourceException("MyCareersFuture", "Timeout")
        assert exc.source_name == "MyCareersFuture"

    def test_original_error_stored(self):
        """Test original error is preserved."""
        original = ConnectionError("Network error")
        exc = DataSourceException("MCF", "Failed", original_error=original)
        assert exc.original_error is original

    def test_message_format(self):
        """Test message includes source name."""
        exc = DataSourceException("Glassdoor", "Rate limited")
        assert "Glassdoor" in exc.message
        assert "Rate limited" in exc.message

    def test_to_dict(self):
        """Test API response format."""
        exc = DataSourceException("MCF", "Error")
        result = exc.to_dict()
        assert result["error_code"] == "DATA_SOURCE_ERROR"
        assert "MCF" in result["error"]


class TestEmbeddingGenerationException:
    """Tests for EmbeddingGenerationException."""

    def test_http_status_code(self):
        """Test HTTP status code is 503."""
        exc = EmbeddingGenerationException("API timeout")
        assert exc.http_status_code == 503

    def test_error_code(self):
        """Test error code is EMBEDDING_ERROR."""
        exc = EmbeddingGenerationException("API timeout")
        assert exc.error_code == "EMBEDDING_ERROR"

    def test_message_includes_context(self):
        """Test message includes 'Embedding generation failed'."""
        exc = EmbeddingGenerationException("Token limit exceeded")
        assert "Embedding generation failed" in exc.message
        assert "Token limit exceeded" in exc.message


class TestVectorSearchException:
    """Tests for VectorSearchException."""

    def test_http_status_code(self):
        """Test HTTP status code is 503."""
        exc = VectorSearchException("Index unavailable")
        assert exc.http_status_code == 503

    def test_error_code(self):
        """Test error code is VECTOR_SEARCH_ERROR."""
        exc = VectorSearchException("Index unavailable")
        assert exc.error_code == "VECTOR_SEARCH_ERROR"


class TestJobMatchingException:
    """Tests for JobMatchingException."""

    def test_http_status_code(self):
        """Test HTTP status code is 404 Not Found."""
        exc = JobMatchingException("No matches found")
        assert exc.http_status_code == 404

    def test_error_code(self):
        """Test error code is JOB_MATCHING_ERROR."""
        exc = JobMatchingException("No matches found")
        assert exc.error_code == "JOB_MATCHING_ERROR"

    def test_job_title_stored(self):
        """Test job title is stored."""
        exc = JobMatchingException("No matches", job_title="Software Engineer")
        assert exc.job_title == "Software Engineer"

    def test_message_with_job_title(self):
        """Test message includes job title when provided."""
        exc = JobMatchingException("No matches", job_title="HR Manager")
        assert "HR Manager" in exc.message

    def test_message_without_job_title(self):
        """Test message works without job title."""
        exc = JobMatchingException("No matches")
        assert "Job matching failed" in exc.message


class TestDataValidationException:
    """Tests for DataValidationException."""

    def test_http_status_code(self):
        """Test HTTP status code is 422 Unprocessable Entity."""
        exc = DataValidationException("job_title", "Required field")
        assert exc.http_status_code == 422

    def test_error_code(self):
        """Test error code is VALIDATION_ERROR."""
        exc = DataValidationException("job_title", "Required field")
        assert exc.error_code == "VALIDATION_ERROR"

    def test_field_stored(self):
        """Test field name is stored."""
        exc = DataValidationException("salary_min", "Must be positive")
        assert exc.field == "salary_min"

    def test_message_includes_field(self):
        """Test message includes field name."""
        exc = DataValidationException("location", "Invalid format")
        assert "location" in exc.message


class TestInsufficientDataException:
    """Tests for InsufficientDataException."""

    def test_http_status_code(self):
        """Test HTTP status code is 404."""
        exc = InsufficientDataException("Not enough data points")
        assert exc.http_status_code == 404

    def test_error_code(self):
        """Test error code is INSUFFICIENT_DATA."""
        exc = InsufficientDataException("Not enough data")
        assert exc.error_code == "INSUFFICIENT_DATA"

    def test_sources_attempted_stored(self):
        """Test sources attempted list is stored."""
        exc = InsufficientDataException(
            "No data",
            sources_attempted=["MCF", "Glassdoor"]
        )
        assert exc.sources_attempted == ["MCF", "Glassdoor"]

    def test_sources_attempted_defaults_to_empty(self):
        """Test sources attempted defaults to empty list."""
        exc = InsufficientDataException("No data")
        assert exc.sources_attempted == []


class TestNoMarketDataError:
    """Tests for NoMarketDataError - critical production exception."""

    def test_http_status_code(self):
        """Test HTTP status code is 404."""
        exc = NoMarketDataError("Software Engineer")
        assert exc.http_status_code == 404

    def test_error_code(self):
        """Test error code is NO_MARKET_DATA."""
        exc = NoMarketDataError("Software Engineer")
        assert exc.error_code == "NO_MARKET_DATA"

    def test_job_title_stored(self):
        """Test job title is stored."""
        exc = NoMarketDataError("HR Manager")
        assert exc.job_title == "HR Manager"

    def test_message_includes_job_title(self):
        """Test message includes job title."""
        exc = NoMarketDataError("Data Scientist")
        assert "Data Scientist" in exc.message

    def test_message_includes_inability_notice(self):
        """Test message indicates recommendation cannot be generated."""
        exc = NoMarketDataError("Test Job")
        assert "Unable to generate salary recommendation" in exc.message

    def test_sources_attempted_in_message(self):
        """Test attempted sources are included in message."""
        exc = NoMarketDataError(
            "Engineer",
            sources_attempted=["Mercer", "MCF", "Glassdoor"]
        )
        assert "Mercer" in exc.message
        assert "MCF" in exc.message


class TestDatabaseConnectionException:
    """Tests for DatabaseConnectionException."""

    def test_http_status_code(self):
        """Test HTTP status code is 503."""
        exc = DatabaseConnectionException("Connection pool exhausted")
        assert exc.http_status_code == 503

    def test_error_code(self):
        """Test error code is DATABASE_ERROR."""
        exc = DatabaseConnectionException("Query timeout")
        assert exc.error_code == "DATABASE_ERROR"


class TestConfigurationException:
    """Tests for ConfigurationException."""

    def test_http_status_code(self):
        """Test HTTP status code is 500."""
        exc = ConfigurationException("OPENAI_API_KEY", "Not set")
        assert exc.http_status_code == 500

    def test_error_code(self):
        """Test error code is CONFIG_ERROR."""
        exc = ConfigurationException("DATABASE_URL", "Invalid format")
        assert exc.error_code == "CONFIG_ERROR"

    def test_config_key_stored(self):
        """Test config key is stored."""
        exc = ConfigurationException("REDIS_URL", "Missing")
        assert exc.config_key == "REDIS_URL"


class TestRateLimitException:
    """Tests for RateLimitException."""

    def test_http_status_code(self):
        """Test HTTP status code is 429 Too Many Requests."""
        exc = RateLimitException("OpenAI")
        assert exc.http_status_code == 429

    def test_error_code(self):
        """Test error code is RATE_LIMIT_EXCEEDED."""
        exc = RateLimitException("OpenAI")
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"

    def test_service_stored(self):
        """Test service name is stored."""
        exc = RateLimitException("Glassdoor API")
        assert exc.service == "Glassdoor API"

    def test_retry_after_stored(self):
        """Test retry_after is stored."""
        exc = RateLimitException("OpenAI", retry_after=60)
        assert exc.retry_after == 60

    def test_message_without_retry_after(self):
        """Test message without retry information."""
        exc = RateLimitException("MCF")
        assert "MCF rate limit exceeded" in exc.message
        assert "retry" not in exc.message.lower()

    def test_message_with_retry_after(self):
        """Test message includes retry information."""
        exc = RateLimitException("OpenAI", retry_after=30)
        assert "retry after 30 seconds" in exc.message


class TestResourceNotFoundException:
    """Tests for ResourceNotFoundException."""

    def test_http_status_code(self):
        """Test HTTP status code is 404."""
        exc = ResourceNotFoundException("User", "user-123")
        assert exc.http_status_code == 404

    def test_error_code(self):
        """Test error code is NOT_FOUND."""
        exc = ResourceNotFoundException("Job", "job-456")
        assert exc.error_code == "NOT_FOUND"

    def test_resource_type_stored(self):
        """Test resource type is stored."""
        exc = ResourceNotFoundException("Document", "doc-789")
        assert exc.resource_type == "Document"

    def test_resource_id_stored(self):
        """Test resource ID is stored."""
        exc = ResourceNotFoundException("Request", "req-001")
        assert exc.resource_id == "req-001"

    def test_message_format(self):
        """Test message includes type and ID."""
        exc = ResourceNotFoundException("PricingResult", "pr-123")
        assert "PricingResult" in exc.message
        assert "pr-123" in exc.message


class TestAuthenticationException:
    """Tests for AuthenticationException."""

    def test_http_status_code(self):
        """Test HTTP status code is 401 Unauthorized."""
        exc = AuthenticationException()
        assert exc.http_status_code == 401

    def test_error_code(self):
        """Test error code is AUTH_ERROR."""
        exc = AuthenticationException()
        assert exc.error_code == "AUTH_ERROR"

    def test_default_message(self):
        """Test default message is 'Authentication required'."""
        exc = AuthenticationException()
        assert exc.message == "Authentication required"

    def test_custom_message(self):
        """Test custom message overrides default."""
        exc = AuthenticationException("Token expired")
        assert exc.message == "Token expired"


class TestAuthorizationException:
    """Tests for AuthorizationException."""

    def test_http_status_code(self):
        """Test HTTP status code is 403 Forbidden."""
        exc = AuthorizationException()
        assert exc.http_status_code == 403

    def test_error_code(self):
        """Test error code is FORBIDDEN."""
        exc = AuthorizationException()
        assert exc.error_code == "FORBIDDEN"

    def test_default_message(self):
        """Test default message is 'Insufficient permissions'."""
        exc = AuthorizationException()
        assert exc.message == "Insufficient permissions"

    def test_custom_message(self):
        """Test custom message overrides default."""
        exc = AuthorizationException("Admin access required")
        assert exc.message == "Admin access required"


class TestExternalServiceException:
    """Tests for ExternalServiceException."""

    def test_http_status_code(self):
        """Test HTTP status code is 503."""
        exc = ExternalServiceException("OpenAI", "API error")
        assert exc.http_status_code == 503

    def test_error_code(self):
        """Test error code is EXTERNAL_SERVICE_ERROR."""
        exc = ExternalServiceException("Mercer", "Timeout")
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"

    def test_service_name_stored(self):
        """Test service name is stored."""
        exc = ExternalServiceException("Glassdoor", "Rate limited")
        assert exc.service_name == "Glassdoor"

    def test_message_includes_service_name(self):
        """Test message includes service name."""
        exc = ExternalServiceException("OpenAI", "Model unavailable")
        assert "OpenAI" in exc.message
        assert "Model unavailable" in exc.message


class TestExceptionInheritance:
    """Tests to verify all exceptions inherit from JobPricingException."""

    @pytest.mark.parametrize("exception_class", [
        DataSourceException,
        EmbeddingGenerationException,
        VectorSearchException,
        JobMatchingException,
        DataValidationException,
        InsufficientDataException,
        NoMarketDataError,
        DatabaseConnectionException,
        ConfigurationException,
        RateLimitException,
        ResourceNotFoundException,
        AuthenticationException,
        AuthorizationException,
        ExternalServiceException,
    ])
    def test_inherits_from_base(self, exception_class):
        """Test all exception classes inherit from JobPricingException."""
        assert issubclass(exception_class, JobPricingException)

    @pytest.mark.parametrize("exception_class,args", [
        (DataSourceException, ("Source", "msg")),
        (EmbeddingGenerationException, ("msg",)),
        (VectorSearchException, ("msg",)),
        (JobMatchingException, ("msg",)),
        (DataValidationException, ("field", "msg")),
        (InsufficientDataException, ("msg",)),
        (NoMarketDataError, ("job_title",)),
        (DatabaseConnectionException, ("msg",)),
        (ConfigurationException, ("key", "msg")),
        (RateLimitException, ("service",)),
        (ResourceNotFoundException, ("type", "id")),
        (AuthenticationException, ()),
        (AuthorizationException, ()),
        (ExternalServiceException, ("service", "msg")),
    ])
    def test_has_to_dict_method(self, exception_class, args):
        """Test all exceptions have to_dict() method returning valid format."""
        exc = exception_class(*args)
        result = exc.to_dict()

        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is False
        assert "error" in result
        assert "error_code" in result


class TestHTTPStatusCodeMapping:
    """Tests to verify HTTP status codes map to correct semantics."""

    def test_client_error_codes(self):
        """Test 4xx status codes for client errors."""
        # 401 Unauthorized - authentication required
        assert AuthenticationException().http_status_code == 401

        # 403 Forbidden - authenticated but not authorized
        assert AuthorizationException().http_status_code == 403

        # 404 Not Found - resource doesn't exist
        assert ResourceNotFoundException("Type", "id").http_status_code == 404
        assert JobMatchingException("msg").http_status_code == 404
        assert NoMarketDataError("job").http_status_code == 404

        # 422 Unprocessable Entity - validation failed
        assert DataValidationException("field", "msg").http_status_code == 422

        # 429 Too Many Requests - rate limited
        assert RateLimitException("service").http_status_code == 429

    def test_server_error_codes(self):
        """Test 5xx status codes for server errors."""
        # 500 Internal Server Error - config/unexpected errors
        assert JobPricingException("msg").http_status_code == 500
        assert ConfigurationException("key", "msg").http_status_code == 500

        # 503 Service Unavailable - external dependency issues
        assert DataSourceException("src", "msg").http_status_code == 503
        assert EmbeddingGenerationException("msg").http_status_code == 503
        assert VectorSearchException("msg").http_status_code == 503
        assert DatabaseConnectionException("msg").http_status_code == 503
        assert ExternalServiceException("svc", "msg").http_status_code == 503
