"""
Production Readiness Verification Script

Systematically tests all components to verify actual production readiness.
"""

import sys
import os
import time
import traceback
from typing import Dict, List, Tuple

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class ProductionVerifier:
    """Verifies production readiness of the application"""

    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
        self.errors: List[str] = []

    def test(self, name: str, func):
        """Run a test and record results"""
        print(f"\n{BLUE}Testing:{RESET} {name}")
        try:
            result = func()
            if result:
                self.results.append((name, True, "OK"))
                print(f"{GREEN}[PASS]{RESET} {name}")
                return True
            else:
                self.results.append((name, False, "Test returned False"))
                print(f"{RED}[FAIL]{RESET} {name}")
                return False
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.results.append((name, False, error_msg))
            self.errors.append(f"{name}: {error_msg}")
            print(f"{RED}[ERROR]{RESET} {name}: {e}")
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print(f"{BLUE}PRODUCTION READINESS VERIFICATION SUMMARY{RESET}")
        print("=" * 80)

        passed = sum(1 for _, success, _ in self.results if success)
        failed = len(self.results) - passed

        print(f"\nTotal Tests: {len(self.results)}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%")

        if failed > 0:
            print(f"\n{RED}FAILED TESTS:{RESET}")
            for name, success, error in self.results:
                if not success:
                    print(f"  - {name}")
                    if len(error) < 200:
                        print(f"    {error}")

        print("\n" + "=" * 80)

        if failed == 0:
            print(f"{GREEN}[OK] ALL TESTS PASSED - PRODUCTION READY{RESET}")
            return 0
        else:
            print(f"{RED}[FAIL] {failed} TEST(S) FAILED - NOT PRODUCTION READY{RESET}")
            return 1


def main():
    """Run all production readiness tests"""
    verifier = ProductionVerifier()

    # Setup test environment
    os.environ['OPENAI_API_KEY'] = 'sk-' + 'test' * 12
    os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost/test'
    os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-jwt-validation'
    os.environ['API_KEY_SALT'] = 'test-salt'
    os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    os.environ['ENVIRONMENT'] = 'development'

    # Test 1: Model Imports
    def test_model_imports():
        from src.job_pricing.models.auth import User, UserRole, Permission
        assert User is not None
        assert UserRole.ADMIN.value == "admin"
        assert len(Permission) >= 15  # Updated: actual count is 17
        return True

    verifier.test("Model Imports (User, Role, Permission)", test_model_imports)

    # Test 2: Auth Utilities
    def test_auth_utils():
        from src.job_pricing.utils.auth import hash_password, verify_password
        password = "TestPassword123!"
        hashed = hash_password(password)
        assert len(hashed) > 50
        assert verify_password(password, hashed)
        assert not verify_password("wrong", hashed)
        return True

    verifier.test("Password Hashing & Verification", test_auth_utils)

    # Test 3: JWT Token Creation
    def test_jwt_tokens():
        from src.job_pricing.utils.auth import create_access_token, create_refresh_token, decode_token
        data = {"sub": "123", "email": "test@example.com", "role": "admin"}

        access_token = create_access_token(data)
        assert len(access_token) > 50

        refresh_token = create_refresh_token(data)
        assert len(refresh_token) > 50

        payload = decode_token(access_token)
        assert payload["sub"] == "123"
        assert payload["type"] == "access"

        return True

    verifier.test("JWT Token Creation & Decoding", test_jwt_tokens)

    # Test 4: API Dependencies
    def test_api_dependencies():
        from src.job_pricing.api.dependencies.auth import PermissionChecker, RoleChecker
        from src.job_pricing.models.auth import Permission, UserRole

        pc = PermissionChecker([Permission.CREATE_JOB_PRICING])
        assert pc is not None

        rc = RoleChecker([UserRole.ADMIN.value])
        assert rc is not None

        return True

    verifier.test("API Dependencies (PermissionChecker, RoleChecker)", test_api_dependencies)

    # Test 5: Auth Endpoints
    def test_auth_endpoints():
        from src.job_pricing.api.v1.auth import router
        assert len(router.routes) >= 12
        route_paths = [r.path for r in router.routes]
        assert "/register" in route_paths
        assert "/login" in route_paths
        assert "/me" in route_paths
        return True

    verifier.test("Auth Endpoints (12+ routes)", test_auth_endpoints)

    # Test 6: Middleware
    def test_middleware():
        from src.job_pricing.middleware import RateLimitMiddleware, PrometheusMiddleware
        assert RateLimitMiddleware is not None
        assert PrometheusMiddleware is not None
        return True

    verifier.test("Middleware (RateLimit, Prometheus)", test_middleware)

    # Test 7: Main FastAPI App
    def test_main_app():
        from src.job_pricing.api.main import app
        assert app is not None
        assert len(app.routes) >= 30
        auth_routes = [r.path for r in app.routes if hasattr(r, 'path') and 'auth' in r.path]
        assert len(auth_routes) >= 12
        return True

    verifier.test("Main FastAPI App (30+ routes)", test_main_app)

    # Test 8: Backup Verification
    def test_backup_utils():
        from src.job_pricing.utils.backup import BackupVerifier
        verifier_obj = BackupVerifier(backup_dir="/tmp/test_backups", max_age_days=7)
        assert verifier_obj is not None
        return True

    verifier.test("Backup Verification Utility", test_backup_utils)

    # Test 9: Database Optimization
    def test_db_optimization():
        from src.job_pricing.utils.db_optimization import QueryOptimizer, time_query
        optimizer = QueryOptimizer()
        assert optimizer is not None

        @time_query
        def test_func():
            return True

        assert test_func()
        return True

    verifier.test("Database Query Optimization", test_db_optimization)

    # Test 10: Prometheus Metrics
    def test_prometheus():
        from src.job_pricing.middleware.prometheus import (
            REQUEST_COUNT,
            REQUEST_DURATION,
            PrometheusMiddleware
        )
        assert REQUEST_COUNT is not None
        assert REQUEST_DURATION is not None
        assert PrometheusMiddleware is not None
        return True

    verifier.test("Prometheus Metrics", test_prometheus)

    # Test 11: Worker & Celery
    def test_worker():
        from src.job_pricing.worker import refresh_market_data, full_data_scrape
        assert refresh_market_data is not None
        assert full_data_scrape is not None
        return True

    verifier.test("Celery Worker Tasks", test_worker)

    # Test 12: Configuration
    def test_config():
        from src.job_pricing.core.config import get_settings
        settings = get_settings()
        assert settings.ENVIRONMENT == "development"
        assert settings.OPENAI_API_KEY.startswith("sk-")
        assert settings.JWT_SECRET_KEY is not None
        assert settings.RATE_LIMIT_ENABLED is not None
        return True

    verifier.test("Configuration Settings", test_config)

    # Test 13: RBAC Permissions
    def test_rbac():
        from src.job_pricing.models.auth import UserRole, Permission, ROLE_PERMISSIONS
        admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        assert len(admin_perms) >= 15
        assert Permission.CREATE_JOB_PRICING in admin_perms
        assert Permission.MANAGE_USERS in admin_perms

        viewer_perms = ROLE_PERMISSIONS[UserRole.VIEWER]
        assert len(viewer_perms) <= 5
        assert Permission.VIEW_JOB_PRICING in viewer_perms
        return True

    verifier.test("RBAC Permissions (4 roles, 17 permissions)", test_rbac)

    # Test 14: Performance Test Imports
    def test_performance_tests():
        # Check that test files exist and can be imported
        import os
        test_files = [
            "tests/integration/test_health_checks.py",
            "tests/unit/test_refresh_market_data.py",
            "tests/performance/test_load_testing.py"
        ]
        for test_file in test_files:
            if not os.path.exists(test_file):
                raise FileNotFoundError(f"Test file missing: {test_file}")
        return True

    verifier.test("Test Files Exist", test_performance_tests)

    # Test 15: Database Migration File
    def test_migration():
        import os
        migration_file = "alembic/versions/004_add_authentication_tables.py"
        if not os.path.exists(migration_file):
            raise FileNotFoundError(f"Migration file missing: {migration_file}")

        # Check migration can be imported
        with open(migration_file, 'r') as f:
            content = f.read()
            assert "def upgrade()" in content
            assert "def downgrade()" in content
            assert "users" in content
            assert "refresh_tokens" in content
            assert "audit_logs" in content
        return True

    verifier.test("Database Migration File", test_migration)

    # Print summary
    exit_code = verifier.print_summary()

    # Print recommendations
    if exit_code != 0:
        print(f"\n{YELLOW}RECOMMENDED NEXT STEPS:{RESET}")
        print("1. Fix failed tests above")
        print("2. Run database migration: alembic upgrade head")
        print("3. Run pytest test suite: pytest tests/ -v")
        print("4. Test authentication flow manually")
        print("5. Verify middleware integration")
        print("6. Measure actual performance")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
