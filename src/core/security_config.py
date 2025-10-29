#!/usr/bin/env python3
"""
Security Configuration Validator for Horme POV Production Environment
=====================================================================

This module provides comprehensive security configuration validation and enforcement
for production deployments. It validates environment variables, secrets, and
configuration settings against security best practices.

Key Features:
- Environment variable validation with security requirements
- Secret strength validation using entropy calculations
- CORS configuration validation and enforcement
- Database connection security validation
- Production readiness assessment
- Security policy enforcement
- Automated security hardening recommendations

Usage:
    from src.core.security_config import SecurityValidator
    
    validator = SecurityValidator()
    is_valid, issues = validator.validate_production_config()
    
    if not is_valid:
        for issue in issues:
            print(f"SECURITY ISSUE: {issue}")
"""

import os
import re
import sys
import json
import base64
import logging
import hashlib
import secrets
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import urllib.parse

class SecurityLevel(Enum):
    """Security levels for different environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    HIGH_SECURITY = "high_security"

class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    CRITICAL = "critical"      # Blocks production deployment
    HIGH = "high"             # Strong recommendation to fix
    MEDIUM = "medium"         # Should be addressed
    LOW = "low"              # Optional improvement
    INFO = "info"            # Information only

@dataclass
class ValidationIssue:
    """Security validation issue"""
    severity: ValidationSeverity
    category: str
    message: str
    variable: Optional[str] = None
    recommendation: Optional[str] = None
    documentation: Optional[str] = None

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    min_password_length: int = 16
    min_jwt_secret_entropy: int = 256
    min_api_key_entropy: int = 128
    require_https: bool = True
    allow_cors_wildcards: bool = False
    require_rate_limiting: bool = True
    require_audit_logging: bool = True
    max_token_expiry_minutes: int = 60
    require_mfa: bool = False

class SecurityValidator:
    """
    Comprehensive security configuration validator
    """
    
    # Critical environment variables that must be set
    REQUIRED_PRODUCTION_VARS = {
        'JWT_SECRET_KEY': 'JWT signing secret key',
        'DATABASE_URL': 'Database connection string',
        'ADMIN_PASSWORD': 'Admin user password',
        'ENVIRONMENT': 'Environment identifier',
    }
    
    # Variables that should never have default/weak values
    FORBIDDEN_DEFAULT_VALUES = {
        'JWT_SECRET_KEY': ['secret', 'change-me', 'jwt-secret', 'your-secret-key'],
        'ADMIN_PASSWORD': ['admin', 'password', 'admin123', '123456', 'changeme'],
        'POSTGRES_PASSWORD': ['postgres', 'password', '123456'],
        'REDIS_PASSWORD': ['redis', 'password', ''],
    }
    
    # Patterns for different secret types
    SECRET_PATTERNS = {
        'jwt_secret': r'^[A-Za-z0-9+/=-]{32,}$',  # Base64-like, minimum 32 chars
        'api_key': r'^[a-zA-Z0-9_-]+_[A-Za-z0-9+/=-]{20,}$',  # Prefixed format
        'database_password': r'^[A-Za-z0-9!@#$%^&*()_+=-]{16,}$',  # Mixed chars, 16+ length
        'hex_key': r'^[a-fA-F0-9]{32,}$',  # Hex encoding, minimum 32 chars
    }
    
    # Secure CORS origins patterns (no wildcards in production)
    SECURE_CORS_PATTERNS = [
        r'^https://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # HTTPS domains
        r'^https://localhost:\d+$',  # HTTPS localhost for development
    ]
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.PRODUCTION):
        self.security_level = security_level
        self.logger = logging.getLogger(__name__)
        self.validation_issues: List[ValidationIssue] = []
        
        # Set security policy based on level
        self.policy = self._get_security_policy(security_level)
        
    def _get_security_policy(self, level: SecurityLevel) -> SecurityPolicy:
        """Get security policy for the specified level"""
        if level == SecurityLevel.DEVELOPMENT:
            return SecurityPolicy(
                min_password_length=8,
                min_jwt_secret_entropy=128,
                allow_cors_wildcards=True,
                require_https=False,
                require_rate_limiting=False,
                require_audit_logging=False,
                max_token_expiry_minutes=480,  # 8 hours for development
            )
        elif level == SecurityLevel.STAGING:
            return SecurityPolicy(
                min_password_length=12,
                min_jwt_secret_entropy=192,
                allow_cors_wildcards=False,
                require_https=True,
                require_rate_limiting=True,
                require_audit_logging=True,
                max_token_expiry_minutes=120,
            )
        elif level == SecurityLevel.HIGH_SECURITY:
            return SecurityPolicy(
                min_password_length=20,
                min_jwt_secret_entropy=384,
                allow_cors_wildcards=False,
                require_https=True,
                require_rate_limiting=True,
                require_audit_logging=True,
                max_token_expiry_minutes=30,
                require_mfa=True,
            )
        else:  # PRODUCTION
            return SecurityPolicy()
    
    def calculate_entropy(self, value: str) -> float:
        """
        Calculate approximate entropy of a string in bits
        
        Args:
            value: String to calculate entropy for
            
        Returns:
            Approximate entropy in bits
        """
        if not value:
            return 0.0
            
        # Determine character set size
        charset_size = 0
        if re.search(r'[a-z]', value):
            charset_size += 26
        if re.search(r'[A-Z]', value):
            charset_size += 26
        if re.search(r'[0-9]', value):
            charset_size += 10
        if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', value):
            charset_size += 32
        if re.search(r'[ ]', value):
            charset_size += 1
            
        if charset_size == 0:
            return 0.0
            
        # Calculate entropy: length * log2(charset_size)
        import math
        entropy = len(value) * math.log2(charset_size)
        
        # Adjust for patterns and repetition
        unique_chars = len(set(value))
        repetition_penalty = unique_chars / len(value) if len(value) > 0 else 1.0
        
        return entropy * repetition_penalty
    
    def validate_secret_strength(self, key: str, value: str) -> List[ValidationIssue]:
        """
        Validate the strength of a secret value
        
        Args:
            key: Environment variable name
            value: Secret value to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if not value:
            issues.append(ValidationIssue(
                ValidationSeverity.CRITICAL,
                "secrets",
                f"Secret '{key}' is empty or not set",
                key,
                f"Set a strong value for {key}",
                "https://docs.horme.com/security/secrets"
            ))
            return issues
        
        # Check for forbidden default values
        if key in self.FORBIDDEN_DEFAULT_VALUES:
            if value.lower() in [v.lower() for v in self.FORBIDDEN_DEFAULT_VALUES[key]]:
                issues.append(ValidationIssue(
                    ValidationSeverity.CRITICAL,
                    "secrets",
                    f"Secret '{key}' uses a default/weak value: {value}",
                    key,
                    "Generate a cryptographically secure random value",
                    "Use generate_secure_secrets.py to generate secure secrets"
                ))
        
        # Calculate entropy
        entropy = self.calculate_entropy(value)
        
        # Determine minimum entropy based on secret type
        if 'JWT' in key.upper():
            min_entropy = self.policy.min_jwt_secret_entropy
        elif 'API_KEY' in key.upper():
            min_entropy = self.policy.min_api_key_entropy
        elif 'PASSWORD' in key.upper():
            min_entropy = 64  # Minimum for passwords
        else:
            min_entropy = 32  # General minimum
            
        if entropy < min_entropy:
            severity = ValidationSeverity.CRITICAL if min_entropy >= 128 else ValidationSeverity.HIGH
            issues.append(ValidationIssue(
                severity,
                "secrets",
                f"Secret '{key}' has insufficient entropy: {entropy:.1f} bits (minimum: {min_entropy})",
                key,
                f"Use a secret with at least {min_entropy} bits of entropy",
                "Run generate_secure_secrets.py to generate secure secrets"
            ))
        
        # Check for patterns that indicate weak secrets
        if len(value) < 16 and 'PASSWORD' in key.upper():
            issues.append(ValidationIssue(
                ValidationSeverity.HIGH,
                "secrets",
                f"Password '{key}' is too short: {len(value)} characters (minimum: {self.policy.min_password_length})",
                key,
                f"Use a password with at least {self.policy.min_password_length} characters"
            ))
        
        # Check for common patterns
        if re.search(r'^(admin|user|test|demo)', value.lower()):
            issues.append(ValidationIssue(
                ValidationSeverity.HIGH,
                "secrets",
                f"Secret '{key}' starts with a common prefix",
                key,
                "Use a completely random value"
            ))
        
        return issues
    
    def validate_cors_configuration(self, cors_origins: str) -> List[ValidationIssue]:
        """
        Validate CORS configuration for security issues
        
        Args:
            cors_origins: Comma-separated list of CORS origins
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if not cors_origins:
            if self.security_level == SecurityLevel.PRODUCTION:
                issues.append(ValidationIssue(
                    ValidationSeverity.HIGH,
                    "cors",
                    "CORS_ORIGINS not configured for production",
                    "CORS_ORIGINS",
                    "Configure specific allowed origins for production"
                ))
            return issues
        
        origins = [origin.strip() for origin in cors_origins.split(',')]
        
        for origin in origins:
            # Check for wildcard usage
            if origin == '*':
                severity = ValidationSeverity.CRITICAL if not self.policy.allow_cors_wildcards else ValidationSeverity.INFO
                issues.append(ValidationIssue(
                    severity,
                    "cors",
                    "CORS wildcard (*) allows requests from any origin",
                    "CORS_ORIGINS",
                    "Specify exact allowed origins instead of using wildcards",
                    "https://docs.horme.com/security/cors"
                ))
                continue
            
            # Check for insecure HTTP origins in production
            if origin.startswith('http://') and self.policy.require_https:
                issues.append(ValidationIssue(
                    ValidationSeverity.HIGH,
                    "cors",
                    f"Insecure HTTP origin in CORS configuration: {origin}",
                    "CORS_ORIGINS",
                    "Use HTTPS origins in production",
                    "Configure SSL/TLS for all frontend domains"
                ))
            
            # Validate origin format
            if not any(re.match(pattern, origin) for pattern in self.SECURE_CORS_PATTERNS):
                if origin not in ['http://localhost:3000', 'http://localhost:8080']:  # Allow dev origins
                    issues.append(ValidationIssue(
                        ValidationSeverity.MEDIUM,
                        "cors",
                        f"CORS origin has unexpected format: {origin}",
                        "CORS_ORIGINS",
                        "Ensure all origins follow expected patterns"
                    ))
        
        return issues
    
    def validate_database_security(self, database_url: str) -> List[ValidationIssue]:
        """
        Validate database connection security
        
        Args:
            database_url: Database connection URL
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if not database_url:
            issues.append(ValidationIssue(
                ValidationSeverity.CRITICAL,
                "database",
                "DATABASE_URL is not configured",
                "DATABASE_URL",
                "Configure secure database connection"
            ))
            return issues
        
        try:
            parsed = urllib.parse.urlparse(database_url)
            
            # Check for missing credentials
            if not parsed.username:
                issues.append(ValidationIssue(
                    ValidationSeverity.HIGH,
                    "database",
                    "Database connection missing username",
                    "DATABASE_URL",
                    "Include database username in connection string"
                ))
            
            if not parsed.password:
                issues.append(ValidationIssue(
                    ValidationSeverity.CRITICAL,
                    "database",
                    "Database connection missing password",
                    "DATABASE_URL",
                    "Include strong database password in connection string"
                ))
            elif parsed.password:
                # Validate password strength
                password_issues = self.validate_secret_strength("DATABASE_PASSWORD", parsed.password)
                issues.extend(password_issues)
            
            # Check for insecure connections
            if parsed.scheme not in ['postgresql', 'postgres'] and 'sqlite' not in parsed.scheme:
                issues.append(ValidationIssue(
                    ValidationSeverity.MEDIUM,
                    "database",
                    f"Database scheme may not be secure: {parsed.scheme}",
                    "DATABASE_URL",
                    "Use PostgreSQL for production deployments"
                ))
            
            # Check for default database names
            if parsed.path and parsed.path.lower() in ['/postgres', '/test', '/development']:
                issues.append(ValidationIssue(
                    ValidationSeverity.MEDIUM,
                    "database",
                    f"Database uses default name: {parsed.path}",
                    "DATABASE_URL",
                    "Use a specific database name for the application"
                ))
            
        except Exception as e:
            issues.append(ValidationIssue(
                ValidationSeverity.HIGH,
                "database",
                f"Database URL format is invalid: {e}",
                "DATABASE_URL",
                "Fix database connection string format"
            ))
        
        return issues
    
    def validate_token_configuration(self) -> List[ValidationIssue]:
        """Validate JWT token configuration"""
        issues = []
        
        # Check token expiration times
        access_expire = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '60')
        try:
            expire_minutes = int(access_expire)
            if expire_minutes > self.policy.max_token_expiry_minutes:
                issues.append(ValidationIssue(
                    ValidationSeverity.MEDIUM,
                    "tokens",
                    f"Access token expiry is too long: {expire_minutes} minutes (max: {self.policy.max_token_expiry_minutes})",
                    "ACCESS_TOKEN_EXPIRE_MINUTES",
                    f"Set token expiry to {self.policy.max_token_expiry_minutes} minutes or less"
                ))
        except ValueError:
            issues.append(ValidationIssue(
                ValidationSeverity.HIGH,
                "tokens",
                f"Invalid token expiry value: {access_expire}",
                "ACCESS_TOKEN_EXPIRE_MINUTES",
                "Set a valid number for token expiry minutes"
            ))
        
        return issues
    
    def validate_rate_limiting(self) -> List[ValidationIssue]:
        """Validate rate limiting configuration"""
        issues = []
        
        if self.policy.require_rate_limiting:
            rate_limit = os.getenv('RATE_LIMIT_REQUESTS')
            if not rate_limit:
                issues.append(ValidationIssue(
                    ValidationSeverity.HIGH,
                    "rate_limiting",
                    "Rate limiting not configured",
                    "RATE_LIMIT_REQUESTS",
                    "Configure rate limiting for production",
                    "Set RATE_LIMIT_REQUESTS and RATE_LIMIT_WINDOW"
                ))
        
        return issues
    
    def validate_logging_configuration(self) -> List[ValidationIssue]:
        """Validate logging and audit configuration"""
        issues = []
        
        if self.policy.require_audit_logging:
            audit_logging = os.getenv('ENABLE_AUDIT_LOGGING', '').lower()
            if audit_logging not in ['true', '1', 'yes']:
                issues.append(ValidationIssue(
                    ValidationSeverity.MEDIUM,
                    "logging",
                    "Audit logging not enabled",
                    "ENABLE_AUDIT_LOGGING",
                    "Enable audit logging for production: ENABLE_AUDIT_LOGGING=true"
                ))
        
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        if log_level in ['DEBUG', 'TRACE'] and self.security_level == SecurityLevel.PRODUCTION:
            issues.append(ValidationIssue(
                ValidationSeverity.MEDIUM,
                "logging",
                f"Log level too verbose for production: {log_level}",
                "LOG_LEVEL",
                "Use INFO or WARNING log level for production"
            ))
        
        return issues
    
    def validate_environment_variables(self) -> List[ValidationIssue]:
        """Validate all environment variables"""
        issues = []
        
        # Check required variables
        for var_name, description in self.REQUIRED_PRODUCTION_VARS.items():
            value = os.getenv(var_name)
            if not value:
                issues.append(ValidationIssue(
                    ValidationSeverity.CRITICAL,
                    "environment",
                    f"Required variable '{var_name}' is not set ({description})",
                    var_name,
                    f"Set {var_name} in your environment configuration"
                ))
            else:
                # Validate secret strength for sensitive variables
                if any(keyword in var_name.upper() for keyword in ['SECRET', 'PASSWORD', 'KEY', 'TOKEN']):
                    secret_issues = self.validate_secret_strength(var_name, value)
                    issues.extend(secret_issues)
        
        # Check environment consistency
        environment = os.getenv('ENVIRONMENT', '').lower()
        if self.security_level == SecurityLevel.PRODUCTION and environment != 'production':
            issues.append(ValidationIssue(
                ValidationSeverity.HIGH,
                "environment",
                f"Environment mismatch: ENVIRONMENT={environment} but validating for production",
                "ENVIRONMENT",
                "Set ENVIRONMENT=production for production deployments"
            ))
        
        return issues
    
    def validate_https_configuration(self) -> List[ValidationIssue]:
        """Validate HTTPS and TLS configuration"""
        issues = []
        
        if self.policy.require_https:
            require_https = os.getenv('REQUIRE_HTTPS', '').lower()
            if require_https not in ['true', '1', 'yes']:
                issues.append(ValidationIssue(
                    ValidationSeverity.HIGH,
                    "https",
                    "HTTPS not enforced",
                    "REQUIRE_HTTPS",
                    "Enable HTTPS enforcement: REQUIRE_HTTPS=true",
                    "Configure SSL/TLS certificates and reverse proxy"
                ))
        
        return issues
    
    def validate_production_config(self) -> Tuple[bool, List[ValidationIssue]]:
        """
        Comprehensive production configuration validation
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        self.validation_issues = []
        
        # Run all validation checks
        self.validation_issues.extend(self.validate_environment_variables())
        
        # Validate specific configurations
        cors_origins = os.getenv('CORS_ORIGINS', '')
        self.validation_issues.extend(self.validate_cors_configuration(cors_origins))
        
        database_url = os.getenv('DATABASE_URL', '')
        self.validation_issues.extend(self.validate_database_security(database_url))
        
        self.validation_issues.extend(self.validate_token_configuration())
        self.validation_issues.extend(self.validate_rate_limiting())
        self.validation_issues.extend(self.validate_logging_configuration())
        self.validation_issues.extend(self.validate_https_configuration())
        
        # Determine if configuration is valid (no critical issues)
        critical_issues = [issue for issue in self.validation_issues if issue.severity == ValidationSeverity.CRITICAL]
        is_valid = len(critical_issues) == 0
        
        return is_valid, self.validation_issues
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security validation report"""
        is_valid, issues = self.validate_production_config()
        
        # Group issues by severity
        issues_by_severity = {}
        for severity in ValidationSeverity:
            issues_by_severity[severity.value] = [
                issue for issue in issues if issue.severity == severity
            ]
        
        # Group issues by category
        issues_by_category = {}
        for issue in issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue)
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'security_level': self.security_level.value,
            'is_valid_for_production': is_valid,
            'summary': {
                'total_issues': len(issues),
                'critical_issues': len(issues_by_severity['critical']),
                'high_issues': len(issues_by_severity['high']),
                'medium_issues': len(issues_by_severity['medium']),
                'low_issues': len(issues_by_severity['low']),
                'info_issues': len(issues_by_severity['info']),
            },
            'issues_by_severity': {
                severity: [
                    {
                        'category': issue.category,
                        'message': issue.message,
                        'variable': issue.variable,
                        'recommendation': issue.recommendation,
                        'documentation': issue.documentation
                    }
                    for issue in issue_list
                ]
                for severity, issue_list in issues_by_severity.items()
            },
            'issues_by_category': {
                category: len(issue_list)
                for category, issue_list in issues_by_category.items()
            },
            'security_policy': {
                'min_password_length': self.policy.min_password_length,
                'min_jwt_secret_entropy': self.policy.min_jwt_secret_entropy,
                'require_https': self.policy.require_https,
                'allow_cors_wildcards': self.policy.allow_cors_wildcards,
                'require_rate_limiting': self.policy.require_rate_limiting,
                'require_audit_logging': self.policy.require_audit_logging,
                'max_token_expiry_minutes': self.policy.max_token_expiry_minutes,
            },
            'recommendations': [
                "Run 'python generate_secure_secrets.py' to generate secure secrets",
                "Use environment-specific configuration files",
                "Enable all security headers in production",
                "Configure rate limiting and DDoS protection",
                "Set up comprehensive audit logging",
                "Regularly rotate secrets and credentials",
                "Monitor for security vulnerabilities and updates"
            ]
        }
        
        return report
    
    def enforce_security_policy(self) -> bool:
        """
        Enforce security policy by raising exceptions for critical issues
        
        Returns:
            True if all critical issues are resolved
            
        Raises:
            SecurityError: If critical security issues are found
        """
        is_valid, issues = self.validate_production_config()
        
        critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
        
        if critical_issues:
            error_messages = []
            for issue in critical_issues:
                error_messages.append(f"CRITICAL: {issue.message}")
                if issue.recommendation:
                    error_messages.append(f"  → {issue.recommendation}")
            
            raise SecurityError(
                f"Critical security issues prevent production deployment:\n" +
                "\n".join(error_messages)
            )
        
        return True

class SecurityError(Exception):
    """Security validation error"""
    pass

# Convenience functions for common validation tasks
def validate_production_readiness() -> Tuple[bool, List[ValidationIssue]]:
    """Quick production readiness check"""
    validator = SecurityValidator(SecurityLevel.PRODUCTION)
    return validator.validate_production_config()

def enforce_production_security():
    """Enforce production security policy (raises exception on critical issues)"""
    validator = SecurityValidator(SecurityLevel.PRODUCTION)
    validator.enforce_security_policy()

def generate_security_assessment() -> Dict[str, Any]:
    """Generate comprehensive security assessment report"""
    validator = SecurityValidator(SecurityLevel.PRODUCTION)
    return validator.generate_security_report()

# Export main components
__all__ = [
    'SecurityValidator', 'SecurityLevel', 'ValidationSeverity', 'ValidationIssue', 
    'SecurityPolicy', 'SecurityError',
    'validate_production_readiness', 'enforce_production_security', 'generate_security_assessment'
]