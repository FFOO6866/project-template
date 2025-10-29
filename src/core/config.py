"""
Production Configuration Management System
==========================================

Centralized configuration management using Pydantic settings.
ALL configuration comes from environment variables - NO HARDCODING.

Adheres to CLAUDE.md standards:
- ❌ NO hardcoded values
- ❌ NO default credentials
- ❌ NO fallback data
- ✅ ALL configuration from environment
- ✅ Validation on startup
- ✅ Fail fast if misconfigured

Usage:
    from src.core.config import config

    # Use configuration
    redis_client = await aioredis.from_url(config.REDIS_URL)
    db_pool = await asyncpg.create_pool(config.DATABASE_URL)
"""

import os
import sys
from typing import Optional, List
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)


class ProductionConfig(BaseSettings):
    """
    Production configuration - ALL values from environment variables.

    NO defaults for sensitive values - deployment will fail if not configured.
    This is intentional and correct - never deploy with missing configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env.production",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra environment variables
    )

    # =========================================================================
    # ENVIRONMENT & APPLICATION
    # =========================================================================
    ENVIRONMENT: str = Field(
        ...,  # Required, no default
        description="Environment: development, staging, or production"
    )

    APP_NAME: str = Field(
        default="horme-pov",
        description="Application name"
    )

    DEBUG: bool = Field(
        default=False,
        description="Debug mode - MUST be False in production"
    )

    # =========================================================================
    # DATABASE CONFIGURATION (PostgreSQL)
    # =========================================================================
    DATABASE_URL: str = Field(
        ...,  # Required, no default
        description="PostgreSQL connection string (required)"
    )

    DATABASE_POOL_SIZE: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Database connection pool size"
    )

    DATABASE_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        le=50,
        description="Maximum overflow connections"
    )

    DATABASE_POOL_TIMEOUT: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Connection pool timeout in seconds"
    )

    # =========================================================================
    # REDIS CONFIGURATION
    # =========================================================================
    REDIS_URL: str = Field(
        ...,  # Required, no default
        description="Redis connection string (required)"
    )

    REDIS_MAX_CONNECTIONS: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum Redis connections"
    )

    REDIS_SOCKET_TIMEOUT: int = Field(
        default=5,
        ge=1,
        le=30,
        description="Redis socket timeout in seconds"
    )

    # =========================================================================
    # NEO4J KNOWLEDGE GRAPH
    # =========================================================================
    NEO4J_URI: str = Field(
        ...,  # Required, no default
        description="Neo4j connection URI (required)"
    )

    NEO4J_USER: str = Field(
        ...,  # Required, no default
        description="Neo4j username (required)"
    )

    NEO4J_PASSWORD: str = Field(
        ...,  # Required, no default
        description="Neo4j password (required)"
    )

    NEO4J_DATABASE: str = Field(
        default="neo4j",
        description="Neo4j database name"
    )

    # =========================================================================
    # OPENAI CONFIGURATION
    # =========================================================================
    OPENAI_API_KEY: str = Field(
        ...,  # Required, no default
        description="OpenAI API key (required)"
    )

    OPENAI_MODEL: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI model to use"
    )

    OPENAI_MAX_TOKENS: int = Field(
        default=2000,
        ge=100,
        le=4000,
        description="Maximum tokens per request"
    )

    OPENAI_TEMPERATURE: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Model temperature"
    )

    # =========================================================================
    # SECURITY & AUTHENTICATION
    # =========================================================================
    SECRET_KEY: str = Field(
        ...,  # Required, no default
        description="Application secret key (required)"
    )

    JWT_SECRET: str = Field(
        ...,  # Required, no default
        description="JWT signing secret (required)"
    )

    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )

    JWT_EXPIRATION_HOURS: int = Field(
        default=24,
        ge=1,
        le=168,
        description="JWT token expiration in hours"
    )

    ADMIN_PASSWORD: str = Field(
        ...,  # Required, no default
        description="Admin user password (required)"
    )

    # =========================================================================
    # API CONFIGURATION
    # =========================================================================
    API_HOST: str = Field(
        default="0.0.0.0",
        description="API host to bind to"
    )

    API_PORT: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="API port"
    )

    API_WORKERS: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of API workers"
    )

    CORS_ORIGINS: List[str] = Field(
        ...,  # Required, no default
        description="Allowed CORS origins (required)"
    )

    MAX_REQUEST_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum request size in bytes"
    )

    RATE_LIMIT_PER_MINUTE: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="API rate limit per minute"
    )

    # =========================================================================
    # MCP SERVER CONFIGURATION
    # =========================================================================
    MCP_HOST: str = Field(
        default="0.0.0.0",
        description="MCP server host"
    )

    MCP_PORT: int = Field(
        default=3002,
        ge=1024,
        le=65535,
        description="MCP server port"
    )

    MCP_TRANSPORT: str = Field(
        default="websocket",
        description="MCP transport type"
    )

    # =========================================================================
    # WEB SCRAPING CONFIGURATION
    # =========================================================================
    SCRAPING_RATE_LIMIT: float = Field(
        default=3.0,
        ge=0.1,
        le=10.0,
        description="Scraping rate limit (requests per second)"
    )

    SCRAPING_MAX_CONCURRENT: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent scraping requests"
    )

    GOOGLE_API_KEY: Optional[str] = Field(
        default=None,
        description="Google API key (optional)"
    )

    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = Field(
        default=None,
        description="Google Custom Search Engine ID (optional)"
    )

    # =========================================================================
    # MONITORING & OBSERVABILITY
    # =========================================================================
    PROMETHEUS_PORT: int = Field(
        default=9090,
        ge=1024,
        le=65535,
        description="Prometheus metrics port"
    )

    JAEGER_HOST: str = Field(
        default="jaeger",
        description="Jaeger tracing host"
    )

    JAEGER_PORT: int = Field(
        default=6831,
        description="Jaeger agent port"
    )

    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )

    ENABLE_AUDIT_LOGGING: bool = Field(
        default=True,
        description="Enable audit logging"
    )

    # =========================================================================
    # HYBRID RECOMMENDATION ENGINE CONFIGURATION
    # =========================================================================
    HYBRID_WEIGHT_COLLABORATIVE: float = Field(
        ...,  # Required, no default
        ge=0.0,
        le=1.0,
        description="Collaborative filtering weight (0.0-1.0, must sum to 1.0)"
    )

    HYBRID_WEIGHT_CONTENT_BASED: float = Field(
        ...,  # Required, no default
        ge=0.0,
        le=1.0,
        description="Content-based filtering weight (0.0-1.0, must sum to 1.0)"
    )

    HYBRID_WEIGHT_KNOWLEDGE_GRAPH: float = Field(
        ...,  # Required, no default
        ge=0.0,
        le=1.0,
        description="Knowledge graph weight (0.0-1.0, must sum to 1.0)"
    )

    HYBRID_WEIGHT_LLM_ANALYSIS: float = Field(
        ...,  # Required, no default
        ge=0.0,
        le=1.0,
        description="LLM analysis weight (0.0-1.0, must sum to 1.0)"
    )

    EMBEDDING_MODEL: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings"
    )

    RECOMMENDATION_CACHE_TTL: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Recommendation cache TTL in seconds"
    )

    # =========================================================================
    # PRODUCT CLASSIFICATION CONFIGURATION
    # =========================================================================
    CLASSIFICATION_CONFIDENCE_THRESHOLD: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Classification confidence threshold (0.0-1.0)"
    )

    CLASSIFICATION_CACHE_TTL: int = Field(
        default=86400,
        ge=60,
        le=604800,
        description="Classification cache TTL in seconds (up to 7 days)"
    )

    # =========================================================================
    # NEXUS PLATFORM CONFIGURATION
    # =========================================================================
    NEXUS_PORT: int = Field(
        default=8090,
        ge=1024,
        le=65535,
        description="Nexus platform port"
    )

    # =========================================================================
    # WEBSOCKET CHAT SERVER CONFIGURATION
    # =========================================================================
    WEBSOCKET_HOST: str = Field(
        default="0.0.0.0",
        description="WebSocket server host"
    )

    WEBSOCKET_PORT: int = Field(
        default=8001,
        ge=1024,
        le=65535,
        description="WebSocket server port"
    )

    # =========================================================================
    # FEATURE FLAGS
    # =========================================================================
    ENABLE_AI_CLASSIFICATION: bool = Field(
        default=True,
        description="Enable AI-powered intent classification"
    )

    ENABLE_IMAGE_ANALYSIS: bool = Field(
        default=True,
        description="Enable image analysis features"
    )

    ENABLE_SEMANTIC_SEARCH: bool = Field(
        default=True,
        description="Enable semantic search with embeddings"
    )

    # =========================================================================
    # VALIDATORS
    # =========================================================================

    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value"""
        allowed = ['development', 'staging', 'production']
        if v.lower() not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of: {allowed}")
        return v.lower()

    @field_validator('DEBUG')
    @classmethod
    def validate_debug(cls, v: bool, info) -> bool:
        """Ensure DEBUG is False in production"""
        # Access environment from validation info
        if hasattr(info, 'data'):
            env = info.data.get('ENVIRONMENT', '').lower()
            if env == 'production' and v is True:
                raise ValueError("DEBUG must be False in production environment")
        return v

    @field_validator('SECRET_KEY', 'JWT_SECRET', 'ADMIN_PASSWORD')
    @classmethod
    def validate_secret_strength(cls, v: str, info) -> str:
        """Validate secret strength"""
        field_name = info.field_name

        # Check minimum length
        if len(v) < 16:
            raise ValueError(f"{field_name} must be at least 16 characters long")

        # Check for common weak values
        weak_values = ['secret', 'password', 'admin', '123456', 'changeme', 'your-secret-key']
        if v.lower() in weak_values:
            raise ValueError(f"{field_name} cannot be a common/weak value. Use: openssl rand -hex 32")

        # Production requires stronger secrets
        env = os.getenv('ENVIRONMENT', '').lower()
        if env == 'production':
            if len(v) < 32:
                raise ValueError(
                    f"{field_name} must be at least 32 characters in production. "
                    f"Generate with: openssl rand -hex 32"
                )

        return v

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format"""
        # Check for localhost in production
        env = os.getenv('ENVIRONMENT', '').lower()
        if env == 'production' and 'localhost' in v.lower():
            raise ValueError(
                "DATABASE_URL cannot contain 'localhost' in production. "
                "Use Docker service name or external host."
            )

        # Must start with postgresql://
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError("DATABASE_URL must use PostgreSQL (postgresql:// or postgres://)")

        # Must include credentials
        if '@' not in v:
            raise ValueError("DATABASE_URL must include credentials (user:password@host)")

        return v

    @field_validator('REDIS_URL')
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Validate Redis URL"""
        env = os.getenv('ENVIRONMENT', '').lower()
        if env == 'production' and 'localhost' in v.lower():
            raise ValueError(
                "REDIS_URL cannot contain 'localhost' in production. "
                "Use Docker service name or external host."
            )

        if not v.startswith('redis://'):
            raise ValueError("REDIS_URL must start with redis://")

        return v

    @field_validator('NEO4J_URI')
    @classmethod
    def validate_neo4j_uri(cls, v: str) -> str:
        """Validate Neo4j URI"""
        env = os.getenv('ENVIRONMENT', '').lower()
        if env == 'production' and 'localhost' in v.lower():
            raise ValueError(
                "NEO4J_URI cannot contain 'localhost' in production. "
                "Use Docker service name or external host."
            )

        if not v.startswith(('bolt://', 'neo4j://', 'neo4j+s://')):
            raise ValueError("NEO4J_URI must use bolt:// or neo4j:// protocol")

        return v

    @field_validator('OPENAI_API_KEY')
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OpenAI API key format"""
        if not v.startswith('sk-'):
            raise ValueError("OPENAI_API_KEY must start with 'sk-'")

        if len(v) < 20:
            raise ValueError("OPENAI_API_KEY appears to be invalid (too short)")

        return v

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def validate_cors_origins(cls, v):
        """Validate CORS origins"""
        import json

        # Handle string input (parse JSON or CSV)
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except (json.JSONDecodeError, ValueError):
                v = [origin.strip() for origin in v.split(',') if origin.strip()]

        if not isinstance(v, list):
            raise ValueError(f"CORS_ORIGINS must be a list, got {type(v)}")

        env = os.getenv('ENVIRONMENT', '').lower()

        if env == 'production':
            # No wildcards in production
            if '*' in v:
                raise ValueError("CORS_ORIGINS cannot include '*' wildcard in production")

            # HTTPS required for non-localhost origins in production
            for origin in v:
                if not origin.startswith('http://localhost') and not origin.startswith('https://'):
                    raise ValueError(
                        f"CORS origin '{origin}' must use HTTPS in production (localhost HTTP allowed for testing)"
                    )

        return v

    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()

        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {allowed}")

        # Warn about DEBUG in production
        env = os.getenv('ENVIRONMENT', '').lower()
        if env == 'production' and v_upper == 'DEBUG':
            logger.warning("DEBUG log level in production - consider using INFO or WARNING")

        return v_upper

    @model_validator(mode='after')
    def validate_hybrid_weights(self):
        """Validate hybrid recommendation engine weights sum to 1.0"""
        weights = [
            self.HYBRID_WEIGHT_COLLABORATIVE,
            self.HYBRID_WEIGHT_CONTENT_BASED,
            self.HYBRID_WEIGHT_KNOWLEDGE_GRAPH,
            self.HYBRID_WEIGHT_LLM_ANALYSIS
        ]

        total_weight = sum(weights)

        # Allow small floating point error (0.99 to 1.01)
        if not (0.99 <= total_weight <= 1.01):
            raise ValueError(
                f"Hybrid recommendation engine weights must sum to 1.0, got {total_weight}. "
                f"Current weights: collaborative={self.HYBRID_WEIGHT_COLLABORATIVE}, "
                f"content_based={self.HYBRID_WEIGHT_CONTENT_BASED}, "
                f"knowledge_graph={self.HYBRID_WEIGHT_KNOWLEDGE_GRAPH}, "
                f"llm_analysis={self.HYBRID_WEIGHT_LLM_ANALYSIS}"
            )

        return self

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == 'production'

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == 'development'

    def get_database_pool_config(self) -> dict:
        """Get database pool configuration"""
        return {
            'dsn': self.DATABASE_URL,
            'min_size': self.DATABASE_POOL_SIZE,
            'max_size': self.DATABASE_POOL_SIZE + self.DATABASE_MAX_OVERFLOW,
            'timeout': self.DATABASE_POOL_TIMEOUT,
            'command_timeout': 60,
        }

    def get_redis_config(self) -> dict:
        """Get Redis configuration"""
        return {
            'url': self.REDIS_URL,
            'max_connections': self.REDIS_MAX_CONNECTIONS,
            'socket_timeout': self.REDIS_SOCKET_TIMEOUT,
            'socket_connect_timeout': 5,
            'retry_on_timeout': True,
        }

    def get_neo4j_config(self) -> dict:
        """Get Neo4j configuration"""
        return {
            'uri': self.NEO4J_URI,
            'auth': (self.NEO4J_USER, self.NEO4J_PASSWORD),
            'database': self.NEO4J_DATABASE,
            'max_connection_lifetime': 3600,
            'max_connection_pool_size': 50,
            'connection_acquisition_timeout': 60,
        }

    def validate_required_fields(self) -> None:
        """
        Validate all required fields are set.
        Raises ValueError if any required field is missing.
        """
        required_fields = [
            'ENVIRONMENT', 'DATABASE_URL', 'REDIS_URL',
            'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD',
            'OPENAI_API_KEY', 'SECRET_KEY', 'JWT_SECRET',
            'ADMIN_PASSWORD', 'CORS_ORIGINS'
        ]

        missing_fields = []
        for field_name in required_fields:
            value = getattr(self, field_name, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field_name)

        if missing_fields:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing_fields)}. "
                f"Set these in your .env.production file or as environment variables."
            )


# =========================================================================
# GLOBAL CONFIGURATION INSTANCE
# =========================================================================

def load_config() -> ProductionConfig:
    """
    Load and validate production configuration.

    This function:
    1. Loads configuration from environment variables
    2. Validates all required fields
    3. Checks for security issues
    4. Fails fast if misconfigured

    Returns:
        ProductionConfig instance

    Raises:
        ValueError: If configuration is invalid or incomplete
    """
    try:
        config = ProductionConfig()
        config.validate_required_fields()

        logger.info(f"Configuration loaded successfully for environment: {config.ENVIRONMENT}")

        # Log configuration summary (without sensitive values)
        logger.info(f"  Database: PostgreSQL (pool_size={config.DATABASE_POOL_SIZE})")
        logger.info(f"  Redis: Connected (max_connections={config.REDIS_MAX_CONNECTIONS})")
        logger.info(f"  Neo4j: {config.NEO4J_URI} (database={config.NEO4J_DATABASE})")
        logger.info(f"  OpenAI: {config.OPENAI_MODEL}")
        logger.info(f"  API: {config.API_HOST}:{config.API_PORT} (workers={config.API_WORKERS})")
        logger.info(f"  MCP: {config.MCP_HOST}:{config.MCP_PORT}")
        logger.info(f"  CORS Origins: {len(config.CORS_ORIGINS)} configured")

        return config

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        logger.error("Ensure all required environment variables are set in .env.production")
        raise


# Initialize global configuration
# This will fail at import time if configuration is invalid (intentional - fail fast)
try:
    config = load_config()
except Exception as e:
    logger.critical(f"FATAL: Cannot load configuration: {e}")
    logger.critical("Application cannot start with invalid configuration")
    # Re-raise to prevent application startup
    raise


# Export main configuration instance
__all__ = ['config', 'ProductionConfig', 'load_config']
