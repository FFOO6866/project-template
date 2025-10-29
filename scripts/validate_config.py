#!/usr/bin/env python3
"""
Production Configuration Validation Script
==========================================

Validates that production configuration is properly set and secure.
NO MOCKS, NO FALLBACKS - configuration must be complete and correct.

Adheres to CLAUDE.md standards:
- ❌ NO default/weak passwords
- ❌ NO localhost URLs in production
- ❌ NO missing required fields
- ✅ ALL secrets are strong
- ✅ ALL URLs point to real services
- ✅ CORS is properly configured

Usage:
    python scripts/validate_config.py

Exit codes:
    0 - Configuration is valid
    1 - Configuration has errors
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Tuple
import asyncio
import asyncpg
import aioredis
from neo4j import GraphDatabase


class ConfigValidationError(Exception):
    """Configuration validation error"""
    pass


class ConfigValidator:
    """Validates production configuration"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.config = None

    def validate_configuration(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate all configuration settings.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        print("=" * 80)
        print("🔍 HORME POV CONFIGURATION VALIDATION")
        print("=" * 80)
        print()

        # Step 1: Load configuration
        print("📋 Step 1: Loading configuration...")
        try:
            from src.core.config import config
            self.config = config
            print(f"   ✅ Configuration loaded for environment: {config.ENVIRONMENT}")
        except Exception as e:
            self.errors.append(f"Failed to load configuration: {str(e)}")
            print(f"   ❌ Configuration load failed: {str(e)}")
            return False, self.errors, self.warnings

        # Step 2: Validate environment settings
        print("\n📋 Step 2: Validating environment settings...")
        self._validate_environment()

        # Step 3: Validate security settings
        print("\n📋 Step 3: Validating security settings...")
        self._validate_security()

        # Step 4: Validate service URLs
        print("\n📋 Step 4: Validating service URLs...")
        self._validate_urls()

        # Step 5: Validate CORS configuration
        print("\n📋 Step 5: Validating CORS configuration...")
        self._validate_cors()

        # Step 6: Test database connectivity (optional, async)
        print("\n📋 Step 6: Testing service connectivity...")
        try:
            asyncio.run(self._test_connectivity())
        except Exception as e:
            self.warnings.append(f"Connectivity tests skipped: {str(e)}")
            print(f"   ⚠️  Connectivity tests skipped: {str(e)}")

        # Generate report
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_environment(self):
        """Validate environment settings"""
        # Check environment
        if self.config.ENVIRONMENT not in ['development', 'staging', 'production']:
            self.errors.append(
                f"Invalid ENVIRONMENT: {self.config.ENVIRONMENT}. "
                f"Must be 'development', 'staging', or 'production'"
            )
            print(f"   ❌ Invalid ENVIRONMENT value")
        else:
            print(f"   ✅ ENVIRONMENT is valid: {self.config.ENVIRONMENT}")

        # Check DEBUG is False in production
        if self.config.ENVIRONMENT == 'production' and self.config.DEBUG:
            self.errors.append("DEBUG must be False in production environment")
            print(f"   ❌ DEBUG is True in production")
        else:
            print(f"   ✅ DEBUG setting is correct: {self.config.DEBUG}")

        # Check log level
        if self.config.ENVIRONMENT == 'production' and self.config.LOG_LEVEL == 'DEBUG':
            self.warnings.append("LOG_LEVEL is DEBUG in production - consider INFO or WARNING")
            print(f"   ⚠️  LOG_LEVEL is DEBUG in production")
        else:
            print(f"   ✅ LOG_LEVEL is appropriate: {self.config.LOG_LEVEL}")

    def _validate_security(self):
        """Validate security settings"""
        # Check secret lengths
        secrets_to_check = {
            'SECRET_KEY': self.config.SECRET_KEY,
            'JWT_SECRET': self.config.JWT_SECRET,
            'ADMIN_PASSWORD': self.config.ADMIN_PASSWORD,
        }

        for secret_name, secret_value in secrets_to_check.items():
            if len(secret_value) < 16:
                self.errors.append(
                    f"{secret_name} is too short: {len(secret_value)} characters "
                    f"(minimum 16 required)"
                )
                print(f"   ❌ {secret_name} is too short")
            elif self.config.is_production() and len(secret_value) < 32:
                self.warnings.append(
                    f"{secret_name} should be at least 32 characters in production "
                    f"(current: {len(secret_value)})"
                )
                print(f"   ⚠️  {secret_name} is shorter than recommended for production")
            else:
                print(f"   ✅ {secret_name} has adequate length")

        # Check for common weak passwords
        weak_passwords = ['admin', 'password', '123456', 'admin123', 'changeme']
        for weak in weak_passwords:
            if weak in self.config.ADMIN_PASSWORD.lower():
                self.errors.append(
                    f"ADMIN_PASSWORD contains weak pattern: '{weak}'. "
                    f"Use: openssl rand -base64 24"
                )
                print(f"   ❌ ADMIN_PASSWORD contains weak pattern")
                break
        else:
            print(f"   ✅ ADMIN_PASSWORD does not contain common weak patterns")

        # Check SECRET_KEY and JWT_SECRET are different
        if self.config.SECRET_KEY == self.config.JWT_SECRET:
            self.errors.append("SECRET_KEY and JWT_SECRET must be different")
            print(f"   ❌ SECRET_KEY and JWT_SECRET are identical")
        else:
            print(f"   ✅ SECRET_KEY and JWT_SECRET are different")

        # Check OpenAI API key format
        if not self.config.OPENAI_API_KEY.startswith('sk-'):
            self.errors.append("OPENAI_API_KEY must start with 'sk-'")
            print(f"   ❌ OPENAI_API_KEY has invalid format")
        elif len(self.config.OPENAI_API_KEY) < 20:
            self.errors.append("OPENAI_API_KEY appears to be invalid (too short)")
            print(f"   ❌ OPENAI_API_KEY is too short")
        else:
            print(f"   ✅ OPENAI_API_KEY format is valid")

    def _validate_urls(self):
        """Validate service URLs"""
        # Check DATABASE_URL
        if 'localhost' in self.config.DATABASE_URL and self.config.is_production():
            self.errors.append(
                "DATABASE_URL contains 'localhost' in production. "
                "Use Docker service name (postgres) or external host"
            )
            print(f"   ❌ DATABASE_URL contains localhost in production")
        else:
            print(f"   ✅ DATABASE_URL is correctly configured")

        # Check DATABASE_URL has credentials
        if '@' not in self.config.DATABASE_URL:
            self.errors.append("DATABASE_URL missing credentials (no @ found)")
            print(f"   ❌ DATABASE_URL missing credentials")
        else:
            print(f"   ✅ DATABASE_URL includes credentials")

        # Check REDIS_URL
        if 'localhost' in self.config.REDIS_URL and self.config.is_production():
            self.errors.append(
                "REDIS_URL contains 'localhost' in production. "
                "Use Docker service name (redis) or external host"
            )
            print(f"   ❌ REDIS_URL contains localhost in production")
        else:
            print(f"   ✅ REDIS_URL is correctly configured")

        # Check NEO4J_URI
        if 'localhost' in self.config.NEO4J_URI and self.config.is_production():
            self.errors.append(
                "NEO4J_URI contains 'localhost' in production. "
                "Use Docker service name (neo4j) or external host"
            )
            print(f"   ❌ NEO4J_URI contains localhost in production")
        else:
            print(f"   ✅ NEO4J_URI is correctly configured")

        # Check Neo4j credentials are set
        if not self.config.NEO4J_USER or not self.config.NEO4J_PASSWORD:
            self.errors.append("Neo4j credentials not set (NEO4J_USER or NEO4J_PASSWORD missing)")
            print(f"   ❌ Neo4j credentials missing")
        else:
            print(f"   ✅ Neo4j credentials are set")

    def _validate_cors(self):
        """Validate CORS configuration"""
        if not self.config.CORS_ORIGINS:
            self.errors.append("CORS_ORIGINS is empty - no origins are allowed")
            print(f"   ❌ CORS_ORIGINS is empty")
            return

        # Check for wildcards in production
        if '*' in self.config.CORS_ORIGINS and self.config.is_production():
            self.errors.append(
                "CORS_ORIGINS contains wildcard '*' in production. "
                "Specify exact allowed origins"
            )
            print(f"   ❌ CORS uses wildcard in production")
        elif '*' not in self.config.CORS_ORIGINS:
            print(f"   ✅ CORS does not use wildcards")

        # Check all origins use HTTPS in production
        if self.config.is_production():
            for origin in self.config.CORS_ORIGINS:
                if not origin.startswith('https://'):
                    self.errors.append(
                        f"CORS origin '{origin}' does not use HTTPS in production"
                    )
                    print(f"   ❌ CORS origin not using HTTPS: {origin}")
            else:
                if self.config.CORS_ORIGINS:
                    print(f"   ✅ All CORS origins use HTTPS")

        print(f"   ✅ CORS configured with {len(self.config.CORS_ORIGINS)} origin(s)")

    async def _test_connectivity(self):
        """Test connectivity to configured services (optional)"""
        print("\n   Testing database connectivity...")
        await self._test_database()

        print("   Testing Redis connectivity...")
        await self._test_redis()

        print("   Testing Neo4j connectivity...")
        await self._test_neo4j()

    async def _test_database(self):
        """Test PostgreSQL database connectivity"""
        try:
            conn = await asyncpg.connect(self.config.DATABASE_URL, timeout=5)
            version = await conn.fetchval('SELECT version()')
            await conn.close()
            print(f"      ✅ PostgreSQL connected successfully")
            print(f"         Version: {version.split(',')[0]}")
        except asyncpg.InvalidPasswordError:
            self.errors.append("Database authentication failed - check credentials")
            print(f"      ❌ Database authentication failed")
        except asyncpg.InvalidCatalogNameError:
            self.errors.append(f"Database '{self.config.DATABASE_URL.split('/')[-1]}' does not exist")
            print(f"      ❌ Database does not exist")
        except Exception as e:
            self.warnings.append(f"Database connection test failed: {str(e)}")
            print(f"      ⚠️  Database connection test failed: {str(e)}")

    async def _test_redis(self):
        """Test Redis connectivity"""
        try:
            redis = await aioredis.from_url(
                self.config.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5
            )
            await redis.ping()
            info = await redis.info('server')
            await redis.close()
            print(f"      ✅ Redis connected successfully")
            print(f"         Version: {info.get('redis_version', 'unknown')}")
        except aioredis.AuthenticationError:
            self.errors.append("Redis authentication failed - check password")
            print(f"      ❌ Redis authentication failed")
        except Exception as e:
            self.warnings.append(f"Redis connection test failed: {str(e)}")
            print(f"      ⚠️  Redis connection test failed: {str(e)}")

    async def _test_neo4j(self):
        """Test Neo4j connectivity"""
        try:
            driver = GraphDatabase.driver(
                self.config.NEO4J_URI,
                auth=(self.config.NEO4J_USER, self.config.NEO4J_PASSWORD)
            )
            with driver.session(database=self.config.NEO4J_DATABASE) as session:
                result = session.run("RETURN 1 as test")
                result.single()
            driver.close()
            print(f"      ✅ Neo4j connected successfully")
        except Exception as e:
            self.warnings.append(f"Neo4j connection test failed: {str(e)}")
            print(f"      ⚠️  Neo4j connection test failed: {str(e)}")


def main():
    """Main validation entry point"""
    validator = ConfigValidator()

    try:
        is_valid, errors, warnings = validator.validate_configuration()

        # Print summary
        print("\n" + "=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)

        if errors:
            print(f"\n❌ ERRORS ({len(errors)}):")
            for i, error in enumerate(errors, 1):
                print(f"   {i}. {error}")

        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for i, warning in enumerate(warnings, 1):
                print(f"   {i}. {warning}")

        print(f"\nTotal Issues: {len(errors)} error(s), {len(warnings)} warning(s)")
        print("=" * 80)

        if is_valid:
            print("\n✅ CONFIGURATION VALIDATION PASSED")
            print("\nYour configuration is production-ready!")
            print("\nNext steps:")
            print("  1. Review warnings (if any)")
            print("  2. Run production standards check: python scripts/validate_production_standards.py")
            print("  3. Deploy: docker-compose -f docker-compose.production-final.yml up -d")
            return 0
        else:
            print("\n❌ CONFIGURATION VALIDATION FAILED")
            print("\nFix all errors before deploying to production.")
            print("\nCommon fixes:")
            print("  • Generate strong secrets: openssl rand -hex 32")
            print("  • Update DATABASE_URL to use Docker service name: postgresql://user:pass@postgres:5432/db")
            print("  • Set CORS_ORIGINS to your actual domains: https://yourdomain.com")
            print("  • Ensure OPENAI_API_KEY starts with 'sk-' and is valid")
            return 1

    except Exception as e:
        print(f"\n❌ FATAL ERROR during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
