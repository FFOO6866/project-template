#!/usr/bin/env python3
"""
Production Security Validation Script
Validates that all critical security fixes have been applied
"""

import os
import sys
import re
from pathlib import Path

class SecurityValidator:
    """Validates production security fixes"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
        self.passed = []

    def validate_all(self):
        """Run all validation checks"""
        print("=" * 80)
        print("HORME POV PRODUCTION SECURITY VALIDATION")
        print("=" * 80)
        print()

        # Check 1: Hardcoded JWT secret
        self.check_hardcoded_jwt_secret()

        # Check 2: Hardcoded admin password hash
        self.check_hardcoded_admin_password()

        # Check 3: Hardcoded database credentials
        self.check_hardcoded_database_credentials()

        # Check 4: CORS localhost fallback
        self.check_cors_localhost_fallback()

        # Check 5: Environment variable validation code
        self.check_env_validation_code()

        # Check 6: .env.production security
        self.check_env_production_file()

        # Check 7: .gitignore protection
        self.check_gitignore_protection()

        # Print results
        self.print_results()

        return len(self.errors) == 0

    def check_hardcoded_jwt_secret(self):
        """Check for hardcoded JWT secret fallback"""
        print("[1/7] Checking for hardcoded JWT secret...")

        nexus_api_file = self.project_root / "src" / "nexus_backend_api.py"
        if not nexus_api_file.exists():
            self.errors.append("nexus_backend_api.py not found")
            return

        content = nexus_api_file.read_text(encoding='utf-8')

        # Check for the old hardcoded secret
        if "nexus-production-secret-change-in-production" in content:
            self.errors.append("CRITICAL: Hardcoded JWT secret 'nexus-production-secret-change-in-production' found")
        else:
            self.passed.append("No hardcoded JWT secret found")

        # Check for proper validation
        if "if not self.jwt_secret:" in content and "raise ValueError" in content:
            self.passed.append("JWT secret validation code present")
        else:
            self.warnings.append("JWT secret validation code may be missing")

    def check_hardcoded_admin_password(self):
        """Check for hardcoded admin password hash"""
        print("[2/7] Checking for hardcoded admin password...")

        nexus_api_file = self.project_root / "src" / "nexus_backend_api.py"
        content = nexus_api_file.read_text(encoding='utf-8')

        # Check for the old hardcoded password hash
        if "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8" in content:
            self.errors.append("CRITICAL: Hardcoded admin password hash found")
        else:
            self.passed.append("No hardcoded admin password hash found")

        # Check for environment variable usage
        if "ADMIN_EMAIL" in content and "ADMIN_PASSWORD_HASH" in content:
            self.passed.append("Admin credentials use environment variables")
        else:
            self.warnings.append("Admin credential environment variable usage unclear")

    def check_hardcoded_database_credentials(self):
        """Check for hardcoded database credentials"""
        print("[3/7] Checking for hardcoded database credentials...")

        nexus_api_file = self.project_root / "src" / "nexus_backend_api.py"
        content = nexus_api_file.read_text(encoding='utf-8')

        # Check for hardcoded credentials
        if "nexus_user:nexus_password" in content:
            self.errors.append("CRITICAL: Hardcoded database credentials 'nexus_user:nexus_password' found")
        else:
            self.passed.append("No hardcoded database credentials found")

        # Check for proper validation
        if "if not self.database_url:" in content:
            self.passed.append("Database URL validation code present")
        else:
            self.warnings.append("Database URL validation code may be missing")

    def check_cors_localhost_fallback(self):
        """Check for unsafe CORS localhost fallback"""
        print("[4/7] Checking CORS configuration...")

        nexus_api_file = self.project_root / "src" / "nexus_backend_api.py"
        content = nexus_api_file.read_text(encoding='utf-8')

        # Check for environment-aware CORS
        if 'environment == "production"' in content and 'CORS_ORIGINS' in content:
            self.passed.append("Environment-aware CORS configuration present")
        else:
            self.warnings.append("Environment-aware CORS configuration unclear")

        # Check for direct localhost in allow_origins
        if re.search(r'allow_origins\s*=\s*os\.getenv\([^)]+,\s*"http://localhost', content):
            self.errors.append("CRITICAL: CORS has hardcoded localhost fallback without environment check")
        else:
            self.passed.append("No unsafe CORS localhost fallback found")

    def check_env_validation_code(self):
        """Check for environment variable validation"""
        print("[5/7] Checking environment variable validation...")

        nexus_api_file = self.project_root / "src" / "nexus_backend_api.py"
        content = nexus_api_file.read_text(encoding='utf-8')

        validation_checks = 0

        if "raise ValueError" in content and "JWT" in content:
            validation_checks += 1

        if "raise ValueError" in content and "DATABASE_URL" in content:
            validation_checks += 1

        if "raise ValueError" in content and "REDIS_URL" in content:
            validation_checks += 1

        if validation_checks >= 3:
            self.passed.append(f"Found {validation_checks} environment validation checks")
        else:
            self.warnings.append(f"Only found {validation_checks} environment validation checks (expected 3+)")

    def check_env_production_file(self):
        """Check .env.production file security"""
        print("[6/7] Checking .env.production file...")

        env_file = self.project_root / ".env.production"
        if not env_file.exists():
            self.warnings.append(".env.production file not found (expected for production)")
            return

        content = env_file.read_text(encoding='utf-8')

        # Check for secure JWT secret (should be 64 hex chars)
        jwt_match = re.search(r'JWT_SECRET=([a-f0-9]{64})', content)
        if jwt_match:
            self.passed.append("JWT_SECRET appears to be securely generated (64 hex chars)")
        else:
            self.warnings.append("JWT_SECRET format unclear or may not be secure")

        # Check for secure DB password (should be 48 hex chars)
        db_match = re.search(r'POSTGRES_PASSWORD=([a-f0-9]{48})', content)
        if db_match:
            self.passed.append("POSTGRES_PASSWORD appears to be securely generated")
        else:
            self.warnings.append("POSTGRES_PASSWORD format unclear or may not be secure")

        # Check for localhost in CORS (warning for production)
        if "localhost" in content and "CORS_ORIGINS" in content:
            self.warnings.append(".env.production contains localhost in CORS_ORIGINS (update before production deployment)")
        else:
            self.passed.append("No localhost in CORS_ORIGINS")

    def check_gitignore_protection(self):
        """Check .gitignore protection for sensitive files"""
        print("[7/7] Checking .gitignore protection...")

        gitignore_file = self.project_root / ".gitignore"
        if not gitignore_file.exists():
            self.errors.append("CRITICAL: .gitignore file not found")
            return

        content = gitignore_file.read_text(encoding='utf-8')

        if ".env.production" in content:
            self.passed.append(".env.production is protected by .gitignore")
        else:
            self.errors.append("CRITICAL: .env.production is NOT in .gitignore")

        if ".credentials" in content or ".env" in content:
            self.passed.append("Credentials files are protected by .gitignore")
        else:
            self.warnings.append("Credentials file protection in .gitignore unclear")

    def print_results(self):
        """Print validation results"""
        print()
        print("=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        print()

        if self.passed:
            print(f"PASSED ({len(self.passed)}):")
            for i, msg in enumerate(self.passed, 1):
                print(f"  {i}. {msg}")
            print()

        if self.warnings:
            print(f"WARNINGS ({len(self.warnings)}):")
            for i, msg in enumerate(self.warnings, 1):
                print(f"  {i}. {msg}")
            print()

        if self.errors:
            print(f"ERRORS ({len(self.errors)}):")
            for i, msg in enumerate(self.errors, 1):
                print(f"  {i}. {msg}")
            print()

        print("=" * 80)

        total_checks = len(self.passed) + len(self.warnings) + len(self.errors)
        pass_rate = (len(self.passed) / total_checks * 100) if total_checks > 0 else 0

        print(f"SUMMARY: {len(self.passed)}/{total_checks} checks passed ({pass_rate:.1f}%)")
        print("=" * 80)
        print()

        if self.errors:
            print("STATUS: FAILED - CRITICAL SECURITY ISSUES FOUND")
            print()
            print("ACTION REQUIRED:")
            print("  1. Review and fix all ERRORS listed above")
            print("  2. Re-run this validation script")
            print("  3. Do NOT deploy to production until all errors are resolved")
            return False
        elif self.warnings:
            print("STATUS: PASSED WITH WARNINGS")
            print()
            print("RECOMMENDATIONS:")
            print("  1. Review and address warnings before production deployment")
            print("  2. Update .env.production with production domains for CORS_ORIGINS")
            print("  3. Set ENVIRONMENT=production before deployment")
            return True
        else:
            print("STATUS: ALL CHECKS PASSED")
            print()
            print("NEXT STEPS:")
            print("  1. Update ADMIN_EMAIL in .env.production")
            print("  2. Update CORS_ORIGINS with production domains")
            print("  3. Set ENVIRONMENT=production")
            print("  4. Test application startup: python -m uvicorn src.nexus_backend_api:app")
            return True

if __name__ == "__main__":
    validator = SecurityValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)
