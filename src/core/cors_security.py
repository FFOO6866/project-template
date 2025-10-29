#!/usr/bin/env python3
"""
Secure CORS Configuration for Horme POV Production Environment
=============================================================

This module provides secure CORS (Cross-Origin Resource Sharing) configuration
that prevents common security vulnerabilities while maintaining functionality.

Key Security Features:
- No wildcard origins in production
- Environment-specific CORS policies
- HTTPS-only origins for production
- Specific allowed headers and methods
- Credential handling restrictions
- Security header injection

Usage:
    from src.core.cors_security import configure_secure_cors
    
    app = FastAPI()
    configure_secure_cors(app, environment="production")
"""

import os
import logging
from typing import List, Optional
from enum import Enum

class CORSSecurityLevel(Enum):
    """CORS security levels for different environments"""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"

class SecureCORSConfig:
    """
    Secure CORS configuration manager
    """
    
    # Default secure configurations by environment
    DEFAULT_CONFIGS = {
        CORSSecurityLevel.DEVELOPMENT: {
            "allow_origins": [
                "http://localhost:3000",    # React dev server
                "http://localhost:3001",    # Alternative React port
                "http://localhost:8080",    # Vue/other dev server
                "http://localhost:8000",    # FastAPI dev server
                "http://127.0.0.1:3000",    # Localhost alternative
                "http://127.0.0.1:8080",
                "http://127.0.0.1:8000",
            ],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
            "allow_headers": [
                "Accept",
                "Accept-Language", 
                "Content-Language",
                "Content-Type",
                "Authorization",
                "X-Requested-With",
                "X-API-Key",
                "X-CSRF-Token",
            ],
            "expose_headers": ["X-Total-Count", "X-Rate-Limit-Remaining"],
            "max_age": 86400,  # 24 hours cache for preflight
        },
        CORSSecurityLevel.STAGING: {
            "allow_origins": [],  # Must be explicitly configured
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
            "allow_headers": [
                "Accept",
                "Accept-Language",
                "Content-Language", 
                "Content-Type",
                "Authorization",
                "X-API-Key",
                "X-CSRF-Token",
            ],
            "expose_headers": ["X-Total-Count"],
            "max_age": 3600,  # 1 hour cache
        },
        CORSSecurityLevel.PRODUCTION: {
            "allow_origins": [],  # Must be explicitly configured
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Minimal set
            "allow_headers": [
                "Accept",
                "Content-Type",
                "Authorization", 
                "X-API-Key",
                "X-CSRF-Token",
            ],
            "expose_headers": [],  # Minimal exposure
            "max_age": 3600,
        }
    }
    
    def __init__(self, security_level: CORSSecurityLevel = CORSSecurityLevel.PRODUCTION):
        self.security_level = security_level
        self.logger = logging.getLogger(__name__)
        
    def get_secure_origins(self) -> List[str]:
        """
        Get secure origins from environment configuration
        
        Returns:
            List of allowed origins with security validation
        """
        cors_origins_env = os.getenv("CORS_ORIGINS", "")
        
        if not cors_origins_env:
            if self.security_level == CORSSecurityLevel.DEVELOPMENT:
                return self.DEFAULT_CONFIGS[self.security_level]["allow_origins"]
            else:
                self.logger.warning("CORS_ORIGINS not configured for production environment")
                return []
        
        # Parse origins from environment
        origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
        
        # Validate origins for security
        validated_origins = []
        for origin in origins:
            if self._validate_origin_security(origin):
                validated_origins.append(origin)
            else:
                self.logger.warning(f"Rejecting insecure CORS origin: {origin}")
                
        return validated_origins
    
    def _validate_origin_security(self, origin: str) -> bool:
        """
        Validate that an origin meets security requirements
        
        Args:
            origin: Origin URL to validate
            
        Returns:
            True if origin is secure, False otherwise
        """
        # Never allow wildcards in production
        if origin == "*":
            if self.security_level == CORSSecurityLevel.PRODUCTION:
                self.logger.error("Wildcard CORS origin (*) not allowed in production")
                return False
            elif self.security_level == CORSSecurityLevel.STAGING:
                self.logger.warning("Wildcard CORS origin (*) not recommended in staging")
                return False
            # Allow in development only
            return True
            
        # Check for null origin (potential security risk)
        if origin.lower() in ["null", "file://", "data:"]:
            self.logger.error(f"Dangerous CORS origin rejected: {origin}")
            return False
        
        # Production must use HTTPS
        if self.security_level == CORSSecurityLevel.PRODUCTION:
            if not origin.startswith("https://"):
                # Allow localhost HTTPS for testing
                if not origin.startswith("https://localhost:") and not origin.startswith("https://127.0.0.1:"):
                    self.logger.error(f"Production CORS origin must use HTTPS: {origin}")
                    return False
        
        # Staging should prefer HTTPS
        if self.security_level == CORSSecurityLevel.STAGING:
            if origin.startswith("http://") and "localhost" not in origin and "127.0.0.1" not in origin:
                self.logger.warning(f"Staging CORS origin should use HTTPS: {origin}")
        
        # Basic URL format validation
        if not origin.startswith(("http://", "https://")):
            self.logger.error(f"Invalid CORS origin format: {origin}")
            return False
            
        return True
    
    def get_cors_config(self) -> dict:
        """
        Get complete CORS configuration for the current security level
        
        Returns:
            Dictionary with CORS middleware configuration
        """
        base_config = self.DEFAULT_CONFIGS[self.security_level].copy()
        
        # Override origins with environment-specific configuration
        secure_origins = self.get_secure_origins()
        base_config["allow_origins"] = secure_origins
        
        # Additional security configurations
        if self.security_level == CORSSecurityLevel.PRODUCTION:
            # Production-specific hardening
            base_config["allow_credentials"] = True  # Required for auth
            base_config["max_age"] = 3600  # Shorter cache time
            
        self.logger.info(f"CORS configured for {self.security_level.value} with {len(secure_origins)} allowed origins")
        
        return base_config

def configure_secure_cors(app, environment: str = None):
    """
    Configure secure CORS middleware for FastAPI application
    
    Args:
        app: FastAPI application instance
        environment: Environment level (development, staging, production)
    """
    from fastapi.middleware.cors import CORSMiddleware
    
    # Determine security level
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "production").lower()
    
    try:
        security_level = CORSSecurityLevel(environment)
    except ValueError:
        logging.warning(f"Unknown environment '{environment}', defaulting to production")
        security_level = CORSSecurityLevel.PRODUCTION
    
    # Get secure configuration
    cors_config = SecureCORSConfig(security_level)
    config = cors_config.get_cors_config()
    
    # Log configuration for debugging
    logger = logging.getLogger(__name__)
    logger.info(f"Configuring CORS for {security_level.value} environment")
    logger.info(f"Allowed origins: {config['allow_origins']}")
    logger.info(f"Allow credentials: {config['allow_credentials']}")
    logger.info(f"Allowed methods: {config['allow_methods']}")
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config["allow_origins"],
        allow_credentials=config["allow_credentials"], 
        allow_methods=config["allow_methods"],
        allow_headers=config["allow_headers"],
        expose_headers=config.get("expose_headers", []),
        max_age=config.get("max_age", 600),
    )
    
    # Add security warning if using insecure configuration
    if "*" in config["allow_origins"]:
        logger.warning("⚠️  SECURITY WARNING: Using wildcard CORS origin - not suitable for production")
    
    if security_level == CORSSecurityLevel.PRODUCTION and not config["allow_origins"]:
        logger.error("❌ CRITICAL: No CORS origins configured for production environment")
        logger.error("   Set CORS_ORIGINS environment variable with comma-separated HTTPS URLs")
        logger.error("   Example: CORS_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com")

def validate_cors_environment():
    """
    Validate CORS environment configuration
    
    Returns:
        List of validation issues
    """
    issues = []
    environment = os.getenv("ENVIRONMENT", "production").lower()
    cors_origins = os.getenv("CORS_ORIGINS", "")
    
    if environment == "production":
        if not cors_origins:
            issues.append("CRITICAL: CORS_ORIGINS not set for production environment")
        elif "*" in cors_origins:
            issues.append("CRITICAL: Wildcard CORS origin not allowed in production")
        else:
            origins = [o.strip() for o in cors_origins.split(",")]
            for origin in origins:
                if origin.startswith("http://") and "localhost" not in origin:
                    issues.append(f"HIGH: Insecure HTTP origin in production: {origin}")
                    
    return issues

# Security headers middleware for additional protection
class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to responses
    """
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Wrap the send function to add headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    
                    # Add security headers
                    security_headers = {
                        b"X-Content-Type-Options": b"nosniff",
                        b"X-Frame-Options": b"DENY",
                        b"X-XSS-Protection": b"1; mode=block",
                        b"Referrer-Policy": b"strict-origin-when-cross-origin",
                        b"Content-Security-Policy": b"default-src 'self'",
                    }
                    
                    # Add HTTPS headers for production
                    environment = os.getenv("ENVIRONMENT", "").lower()
                    if environment == "production":
                        security_headers[b"Strict-Transport-Security"] = b"max-age=31536000; includeSubDomains; preload"
                    
                    # Merge with existing headers
                    for name, value in security_headers.items():
                        if name not in headers:
                            headers[name] = value
                    
                    message["headers"] = list(headers.items())
                
                await send(message)
                
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

def add_security_headers(app):
    """Add security headers middleware to FastAPI app"""
    app.add_middleware(SecurityHeadersMiddleware)

# Example usage patterns
CORS_CONFIG_EXAMPLES = {
    "development": """
# Development CORS configuration
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
""",
    "staging": """
# Staging CORS configuration  
ENVIRONMENT=staging
CORS_ORIGINS=https://staging-app.yourdomain.com,https://staging-admin.yourdomain.com
""",
    "production": """
# Production CORS configuration
ENVIRONMENT=production
CORS_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com
"""
}

# Export main components
__all__ = [
    "configure_secure_cors",
    "SecureCORSConfig", 
    "CORSSecurityLevel",
    "validate_cors_environment",
    "add_security_headers",
    "SecurityHeadersMiddleware",
    "CORS_CONFIG_EXAMPLES"
]