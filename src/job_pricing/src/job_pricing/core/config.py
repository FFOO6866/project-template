"""
Configuration Management - Loads ALL settings from .env file.

CRITICAL: NO HARDCODED VALUES. Everything must come from environment variables.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from .env file.

    All values are read from environment variables.
    NO DEFAULTS for sensitive data (will fail if not set).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --------------------------------------------------------------------------
    # Environment
    # --------------------------------------------------------------------------
    ENVIRONMENT: str = Field(..., description="Environment: development, staging, production")
    DEBUG: bool = Field(default=False, description="Debug mode")
    APP_NAME: str = Field(default="job-pricing-engine")
    APP_VERSION: str = Field(default="1.0.0")

    # --------------------------------------------------------------------------
    # API Configuration
    # --------------------------------------------------------------------------
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_BASE_URL: str = Field(default="http://localhost:8000")

    # --------------------------------------------------------------------------
    # Database
    # --------------------------------------------------------------------------
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    DB_POOL_SIZE: int = Field(default=20)
    DB_MAX_OVERFLOW: int = Field(default=10)
    SQL_ECHO: bool = Field(default=False)

    # --------------------------------------------------------------------------
    # Redis
    # --------------------------------------------------------------------------
    REDIS_URL: str = Field(..., description="Redis connection string")
    CACHE_TTL_SHORT: int = Field(default=300)  # 5 minutes
    CACHE_TTL_MEDIUM: int = Field(default=1800)  # 30 minutes
    CACHE_TTL_LONG: int = Field(default=86400)  # 24 hours

    # --------------------------------------------------------------------------
    # OpenAI - CRITICAL
    # --------------------------------------------------------------------------
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key - REQUIRED")
    OPENAI_MODEL_DEFAULT: str = Field(default="gpt-4")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-large")
    OPENAI_MAX_TOKENS: int = Field(default=2000)
    OPENAI_TEMPERATURE: float = Field(default=0.1)
    OPENAI_MAX_REQUESTS_PER_MINUTE: int = Field(default=60)

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OpenAI API key format"""
        if not v.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        if len(v) < 20:
            raise ValueError("OpenAI API key is too short")
        return v

    # --------------------------------------------------------------------------
    # JWT Authentication
    # --------------------------------------------------------------------------
    JWT_SECRET_KEY: str = Field(..., description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # --------------------------------------------------------------------------
    # API Keys
    # --------------------------------------------------------------------------
    API_KEY_SALT: str = Field(..., description="Salt for API key hashing")

    # --------------------------------------------------------------------------
    # CORS
    # --------------------------------------------------------------------------
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:8000")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # --------------------------------------------------------------------------
    # External Integrations
    # --------------------------------------------------------------------------
    # Mercer
    MERCER_API_KEY: str = Field(default="")
    MERCER_API_BASE_URL: str = Field(default="https://api.mercer.com/v1")
    MERCER_API_TIMEOUT: int = Field(default=30)

    # Glassdoor
    GLASSDOOR_EMAIL: str = Field(default="")
    GLASSDOOR_PASSWORD: str = Field(default="")

    # BIPO HRIS
    BIPO_API_BASE_URL: str = Field(default="https://ap9.bipocloud.com/IMC")
    BIPO_USERNAME: str = Field(default="")
    BIPO_PASSWORD: str = Field(default="")
    BIPO_CLIENT_ID: str = Field(default="")
    BIPO_CLIENT_SECRET: str = Field(default="")
    BIPO_ENABLED: bool = Field(default=False)

    # Proxy
    PROXY_ENABLED: bool = Field(default=False)
    PROXY_URL: str = Field(default="")

    # --------------------------------------------------------------------------
    # Celery
    # --------------------------------------------------------------------------
    CELERY_BROKER_URL: str = Field(..., description="Celery broker URL (Redis)")
    CELERY_RESULT_BACKEND: str = Field(..., description="Celery result backend (Redis)")

    # Scraping Schedule
    SCRAPING_SCHEDULE_WEEKLY: str = Field(default="0 2 * * 0")  # Sunday 2AM
    SCRAPING_SCHEDULE_DAILY: str = Field(default="0 6 * * *")  # Daily 6AM

    # --------------------------------------------------------------------------
    # File Storage
    # --------------------------------------------------------------------------
    UPLOAD_DIR: str = Field(default="/app/data/uploads")
    EXPORT_DIR: str = Field(default="/app/data/exports")
    DATA_DIR: str = Field(default="/app/data")
    MAX_UPLOAD_SIZE: int = Field(default=10485760)  # 10 MB

    # --------------------------------------------------------------------------
    # Logging
    # --------------------------------------------------------------------------
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")
    LOG_FILE: str = Field(default="/app/logs/app.log")

    # Sentry
    SENTRY_DSN: str = Field(default="")
    SENTRY_ENVIRONMENT: str = Field(default="")

    @property
    def sentry_enabled(self) -> bool:
        """Check if Sentry is configured"""
        return bool(self.SENTRY_DSN)

    # --------------------------------------------------------------------------
    # Monitoring
    # --------------------------------------------------------------------------
    PROMETHEUS_ENABLED: bool = Field(default=True)
    PROMETHEUS_PORT: int = Field(default=9090)
    HEALTH_CHECK_ENABLED: bool = Field(default=True)

    # --------------------------------------------------------------------------
    # Email
    # --------------------------------------------------------------------------
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM_EMAIL: str = Field(default="noreply@company.com")
    SMTP_USE_TLS: bool = Field(default=True)

    @property
    def smtp_enabled(self) -> bool:
        """Check if SMTP is configured"""
        return bool(self.SMTP_USER and self.SMTP_PASSWORD)

    # --------------------------------------------------------------------------
    # Rate Limiting
    # --------------------------------------------------------------------------
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_FREE_TIER: int = Field(default=100)
    RATE_LIMIT_STANDARD_TIER: int = Field(default=1000)

    # --------------------------------------------------------------------------
    # Feature Flags
    # --------------------------------------------------------------------------
    FEATURE_WEB_SCRAPING: bool = Field(default=True)
    FEATURE_MERCER_INTEGRATION: bool = Field(default=True)
    FEATURE_SSG_INTEGRATION: bool = Field(default=True)
    FEATURE_INTERNAL_HRIS: bool = Field(default=False)
    FEATURE_APPLICANT_DATA: bool = Field(default=False)

    # --------------------------------------------------------------------------
    # Development Settings
    # --------------------------------------------------------------------------
    AUTO_RELOAD: bool = Field(default=True)
    DEBUG_TOOLBAR_ENABLED: bool = Field(default=False)

    # --------------------------------------------------------------------------
    # Backup & Maintenance
    # --------------------------------------------------------------------------
    BACKUP_ENABLED: bool = Field(default=True)
    BACKUP_RETENTION_DAYS: int = Field(default=30)
    BACKUP_SCHEDULE: str = Field(default="0 3 * * *")  # Daily 3AM

    # --------------------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------------------
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of: {', '.join(allowed)}")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(allowed)}")
        return v_upper

    # --------------------------------------------------------------------------
    # Computed Properties
    # --------------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.ENVIRONMENT == "testing"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are loaded only once.
    All subsequent calls return the same instance.

    Returns:
        Settings: Application settings

    Raises:
        ValidationError: If required environment variables are missing
        ValueError: If any setting value is invalid
    """
    return Settings()  # type: ignore


# Convenience function to reload settings (useful for testing)
def reload_settings() -> Settings:
    """
    Reload settings by clearing cache.

    Use this in tests when you need to reload environment variables.

    Returns:
        Settings: Fresh settings instance
    """
    get_settings.cache_clear()
    return get_settings()
