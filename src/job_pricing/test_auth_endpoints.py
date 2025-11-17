"""
Authentication Endpoints Validation Script

Tests authentication endpoint structure, schemas, and routing without database.
"""
import sys
from typing import List, Dict

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class EndpointTester:
    def __init__(self):
        self.results: List[Dict] = []

    def test(self, name: str, func):
        """Run a test and record results"""
        print(f"\n{BLUE}Testing:{RESET} {name}")
        try:
            func()
            self.results.append({"name": name, "status": "PASS"})
            print(f"{GREEN}[PASS]{RESET} {name}")
            return True
        except Exception as e:
            self.results.append({"name": name, "status": "FAIL", "error": str(e)})
            print(f"{RED}[FAIL]{RESET} {name}")
            print(f"  Error: {e}")
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print(f"{BLUE}AUTHENTICATION ENDPOINTS TEST SUMMARY{RESET}")
        print("=" * 80)

        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = len(self.results) - passed

        print(f"\nTotal Tests: {len(self.results)}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%")

        if failed > 0:
            print(f"\n{RED}FAILED TESTS:{RESET}")
            for r in self.results:
                if r["status"] == "FAIL":
                    print(f"  - {r['name']}")
                    if "error" in r:
                        print(f"    {r['error'][:150]}")

        print("\n" + "=" * 80)

        if failed == 0:
            print(f"{GREEN}[OK] ALL ENDPOINT TESTS PASSED{RESET}")
            return 0
        else:
            print(f"{RED}[FAIL] {failed} TEST(S) FAILED{RESET}")
            return 1


def main():
    """Run all authentication endpoint tests"""
    tester = EndpointTester()

    # Test 1: Import auth router
    def test_auth_router_import():
        from src.job_pricing.api.v1.auth import router
        assert router is not None
        assert hasattr(router, 'routes')

    tester.test("Import auth router", test_auth_router_import)

    # Test 2: Count routes
    def test_route_count():
        from src.job_pricing.api.v1.auth import router
        routes = router.routes
        assert len(routes) >= 12, f"Expected >= 12 routes, got {len(routes)}"

    tester.test("Auth router has >= 12 routes", test_route_count)

    # Test 3: Check specific routes
    def test_specific_routes():
        from src.job_pricing.api.v1.auth import router
        route_paths = [r.path for r in router.routes]

        required_routes = [
            "/register",
            "/login",
            "/refresh",
            "/logout",
            "/me",
        ]

        for route in required_routes:
            assert route in route_paths, f"Missing route: {route}"

    tester.test("Required auth routes exist", test_specific_routes)

    # Test 4: Request schemas
    def test_request_schemas():
        from src.job_pricing.api.v1.auth import (
            UserRegister,
            UpdateUserRequest,
            ChangePasswordRequest
        )

        # Test UserRegister
        user_data = UserRegister(
            email="test@example.com",
            username="testuser",
            password="SecurePass123!",
            full_name="Test User"
        )
        assert user_data.email == "test@example.com"

        # Test ChangePasswordRequest
        pwd_change = ChangePasswordRequest(
            current_password="old123",
            new_password="new456789"
        )
        assert pwd_change.current_password == "old123"

    tester.test("Request schemas validation", test_request_schemas)

    # Test 5: Response schemas
    def test_response_schemas():
        from src.job_pricing.api.v1.auth import (
            UserResponse,
            TokenResponse
        )
        from src.job_pricing.models.auth import UserRole
        from datetime import datetime

        # Test UserResponse (includes all required fields)
        user = UserResponse(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.VIEWER.value,
            is_active=True,
            is_verified=False,
            is_superuser=False,
            created_at=datetime.utcnow(),
            last_login=None,
            department=None,
            job_title=None
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"

        # Test TokenResponse
        token = TokenResponse(
            access_token="abc123",
            refresh_token="def456",
            token_type="bearer",
            expires_in=900
        )
        assert token.token_type == "bearer"

    tester.test("Response schemas validation", test_response_schemas)

    # Test 6: Dependencies import
    def test_dependencies():
        from src.job_pricing.api.dependencies.auth import (
            get_current_user,
            get_current_active_user,
            PermissionChecker,
            RoleChecker
        )
        assert get_current_user is not None
        assert PermissionChecker is not None
        assert RoleChecker is not None

    tester.test("Auth dependencies import", test_dependencies)

    # Test 7: Permission checker initialization
    def test_permission_checker():
        from src.job_pricing.api.dependencies.auth import PermissionChecker
        from src.job_pricing.models.auth import Permission

        checker = PermissionChecker([Permission.CREATE_JOB_PRICING])
        assert checker is not None
        assert checker.required_permissions == [Permission.CREATE_JOB_PRICING]

    tester.test("PermissionChecker initialization", test_permission_checker)

    # Test 8: Role checker initialization
    def test_role_checker():
        from src.job_pricing.api.dependencies.auth import RoleChecker
        from src.job_pricing.models.auth import UserRole

        checker = RoleChecker([UserRole.ADMIN.value])
        assert checker is not None
        assert UserRole.ADMIN.value in checker.allowed_roles

    tester.test("RoleChecker initialization", test_role_checker)

    # Test 9: Auth utilities
    def test_auth_utils():
        from src.job_pricing.utils.auth import (
            hash_password,
            verify_password,
            create_access_token,
            create_refresh_token
        )

        # Test password hashing
        password = "TestPassword123!"
        hashed = hash_password(password)
        assert len(hashed) > 50
        assert verify_password(password, hashed)
        assert not verify_password("wrong", hashed)

        # Test token creation
        data = {"sub": "123", "email": "test@example.com"}
        access_token = create_access_token(data)
        assert len(access_token) > 50

        refresh_token = create_refresh_token(data)
        assert len(refresh_token) > 50

    tester.test("Auth utilities (hash, verify, tokens)", test_auth_utils)

    # Test 10: Route methods
    def test_route_methods():
        from src.job_pricing.api.v1.auth import router

        # Collect all methods for each path (handle duplicate paths)
        methods_by_path = {}
        for route in router.routes:
            if route.path not in methods_by_path:
                methods_by_path[route.path] = set()
            methods_by_path[route.path].update(route.methods)

        # Check specific method requirements
        assert "POST" in methods_by_path.get("/register", set()), "POST not in /register"
        assert "POST" in methods_by_path.get("/login", set()), "POST not in /login"
        assert "POST" in methods_by_path.get("/refresh", set()), "POST not in /refresh"
        assert "GET" in methods_by_path.get("/me", set()), "GET not in /me"

    tester.test("Route HTTP methods", test_route_methods)

    # Test 11: Endpoint tags
    def test_endpoint_tags():
        from src.job_pricing.api.v1.auth import router
        assert router.tags is not None
        # Auth router should have a tag for organization

    tester.test("Router tags configuration", test_endpoint_tags)

    # Test 12: User model permissions
    def test_user_model_permissions():
        from src.job_pricing.models.auth import User, Permission, UserRole, ROLE_PERMISSIONS
        from sqlalchemy.orm import Session

        # Verify ROLE_PERMISSIONS mapping
        admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        assert len(admin_perms) >= 15
        assert Permission.MANAGE_USERS in admin_perms

        viewer_perms = ROLE_PERMISSIONS[UserRole.VIEWER]
        assert len(viewer_perms) <= 5
        assert Permission.VIEW_JOB_PRICING in viewer_perms

    tester.test("User model permission methods", test_user_model_permissions)

    # Print summary
    exit_code = tester.print_summary()

    if exit_code != 0:
        print(f"\n{YELLOW}RECOMMENDATIONS:{RESET}")
        print("1. Fix any import errors or missing dependencies")
        print("2. Verify schema definitions match requirements")
        print("3. Test with actual HTTP requests (requires running server)")
        print("4. Validate authentication flow end-to-end")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
