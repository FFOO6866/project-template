"""
Unit tests for configuration management.

Tests that settings are loaded correctly from .env file.
"""

import pytest
from pydantic import ValidationError

from job_pricing.core.config import Settings, get_settings, reload_settings


def test_settings_loads_from_env():
    """Test that settings loads from .env file"""
    settings = get_settings()

    # Check critical settings are loaded
    assert settings.OPENAI_API_KEY is not None
    assert len(settings.OPENAI_API_KEY) > 0
    assert settings.OPENAI_API_KEY.startswith("sk-")


def test_settings_validates_openai_key():
    """Test that OpenAI API key validation works"""
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="development",
            DATABASE_URL="postgresql://test",
            REDIS_URL="redis://test",
            OPENAI_API_KEY="invalid_key",  # Doesn't start with sk-
            JWT_SECRET_KEY="test",
            CELERY_BROKER_URL="redis://test",
            CELERY_RESULT_BACKEND="redis://test",
            API_KEY_SALT="test",
        )


def test_settings_validates_environment():
    """Test that ENVIRONMENT is validated"""
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="invalid",  # Not in allowed list
            DATABASE_URL="postgresql://test",
            REDIS_URL="redis://test",
            OPENAI_API_KEY="sk-test123456789012345678",
            JWT_SECRET_KEY="test",
            CELERY_BROKER_URL="redis://test",
            CELERY_RESULT_BACKEND="redis://test",
            API_KEY_SALT="test",
        )


def test_environment_checks():
    """Test environment helper properties"""
    settings = get_settings()

    if settings.ENVIRONMENT == "development":
        assert settings.is_development is True
        assert settings.is_production is False
    elif settings.ENVIRONMENT == "production":
        assert settings.is_development is False
        assert settings.is_production is True


def test_cors_origins_parsing():
    """Test CORS origins are parsed correctly"""
    settings = get_settings()

    origins = settings.cors_origins_list
    assert isinstance(origins, list)
    assert len(origins) > 0


def test_required_settings_present():
    """Test that all required settings are present"""
    settings = get_settings()

    # Critical settings
    assert settings.ENVIRONMENT is not None
    assert settings.DATABASE_URL is not None
    assert settings.REDIS_URL is not None
    assert settings.OPENAI_API_KEY is not None
    assert settings.JWT_SECRET_KEY is not None
    assert settings.API_KEY_SALT is not None


def test_settings_singleton():
    """Test that get_settings returns same instance"""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2


def test_reload_settings():
    """Test that reload_settings creates new instance"""
    settings1 = get_settings()
    settings2 = reload_settings()

    # After reload, should have new instance
    assert settings1 is not settings2
