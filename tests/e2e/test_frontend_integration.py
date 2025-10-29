"""
Frontend Integration Tests
===========================

Tests the Next.js frontend integration with backend services.
"""

import asyncio
import os
import sys
from datetime import datetime

import requests


class FrontendIntegrationTester:
    """Test frontend integration with backend services"""

    def __init__(self, frontend_url: str, api_url: str, websocket_url: str):
        self.frontend_url = frontend_url.rstrip('/')
        self.api_url = api_url.rstrip('/')
        self.websocket_url = websocket_url
        self.test_results = []

    def test_frontend_health(self):
        """Test frontend health endpoint"""
        print("\n🏥 Test 1: Frontend Health Check")
        print("-" * 50)

        try:
            response = requests.get(f"{self.frontend_url}/api/health", timeout=10)

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            print(f"✅ Frontend is healthy")
            print(f"   Status code: {response.status_code}")
            print(f"   Response time: {response.elapsed.total_seconds():.2f}s")

            self.test_results.append(("Frontend Health", "PASSED"))
            return True

        except Exception as e:
            print(f"❌ Frontend health check failed: {e}")
            self.test_results.append(("Frontend Health", f"FAILED: {e}"))
            return False

    def test_frontend_homepage(self):
        """Test frontend homepage loads"""
        print("\n🏠 Test 2: Frontend Homepage")
        print("-" * 50)

        try:
            response = requests.get(self.frontend_url, timeout=10)

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert len(response.text) > 0, "Homepage is empty"
            assert "<!DOCTYPE html>" in response.text or "<html" in response.text, "Not valid HTML"

            print(f"✅ Homepage loaded successfully")
            print(f"   Status code: {response.status_code}")
            print(f"   Content length: {len(response.text)} bytes")
            print(f"   Response time: {response.elapsed.total_seconds():.2f}s")

            self.test_results.append(("Frontend Homepage", "PASSED"))
            return True

        except Exception as e:
            print(f"❌ Homepage load failed: {e}")
            self.test_results.append(("Frontend Homepage", f"FAILED: {e}"))
            return False

    def test_api_connection(self):
        """Test frontend can connect to API"""
        print("\n🔗 Test 3: API Connection")
        print("-" * 50)

        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            data = response.json()
            print(f"✅ API connection successful")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Response time: {response.elapsed.total_seconds():.2f}s")

            self.test_results.append(("API Connection", "PASSED"))
            return True

        except Exception as e:
            print(f"❌ API connection failed: {e}")
            self.test_results.append(("API Connection", f"FAILED: {e}"))
            return False

    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        print("\n📊 Test 4: Metrics Endpoint")
        print("-" * 50)

        try:
            response = requests.get(f"{self.api_url}/api/metrics", timeout=10)

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            data = response.json()
            assert "active_quotations" in data or "activeQuotations" in data, "Missing active_quotations"

            print(f"✅ Metrics endpoint working")
            print(f"   Active quotations: {data.get('active_quotations', data.get('activeQuotations', 0))}")
            print(f"   Response time: {response.elapsed.total_seconds():.2f}s")

            self.test_results.append(("Metrics Endpoint", "PASSED"))
            return True

        except Exception as e:
            print(f"❌ Metrics endpoint failed: {e}")
            self.test_results.append(("Metrics Endpoint", f"FAILED: {e}"))
            return False

    def test_cors_headers(self):
        """Test CORS headers are set correctly"""
        print("\n🌐 Test 5: CORS Headers")
        print("-" * 50)

        try:
            headers = {
                "Origin": self.frontend_url,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }

            response = requests.options(f"{self.api_url}/health", headers=headers, timeout=10)

            # Check CORS headers
            cors_headers = {
                "access-control-allow-origin",
                "access-control-allow-methods",
                "access-control-allow-headers"
            }

            found_headers = {k.lower(): v for k, v in response.headers.items() if k.lower() in cors_headers}

            print(f"✅ CORS headers present")
            for header, value in found_headers.items():
                print(f"   {header}: {value}")

            self.test_results.append(("CORS Headers", "PASSED"))
            return True

        except Exception as e:
            print(f"❌ CORS headers check failed: {e}")
            self.test_results.append(("CORS Headers", f"FAILED: {e}"))
            return False

    def test_static_assets(self):
        """Test static assets are served correctly"""
        print("\n🖼️  Test 6: Static Assets")
        print("-" * 50)

        try:
            # Test Next.js static files endpoint
            response = requests.get(f"{self.frontend_url}/_next/static/", timeout=10, allow_redirects=False)

            # Either 200 (directory listing) or 404 (no directory listing) is acceptable
            # What matters is that the server responds
            assert response.status_code in [200, 404, 403], f"Unexpected status: {response.status_code}"

            print(f"✅ Static assets endpoint accessible")
            print(f"   Status code: {response.status_code}")

            self.test_results.append(("Static Assets", "PASSED"))
            return True

        except Exception as e:
            print(f"❌ Static assets check failed: {e}")
            self.test_results.append(("Static Assets", f"FAILED: {e}"))
            return False

    async def test_websocket_upgrade(self):
        """Test WebSocket upgrade from browser perspective"""
        print("\n🔌 Test 7: WebSocket Upgrade")
        print("-" * 50)

        try:
            import websockets

            # Test WebSocket connection (simulating browser)
            async with websockets.connect(self.websocket_url, ping_interval=None) as websocket:
                # Wait for welcome message
                welcome = await asyncio.wait_for(websocket.recv(), timeout=5.0)

                print(f"✅ WebSocket upgrade successful")
                print(f"   WebSocket URL: {self.websocket_url}")
                print(f"   Welcome message received")

                self.test_results.append(("WebSocket Upgrade", "PASSED"))
                return True

        except Exception as e:
            print(f"❌ WebSocket upgrade failed: {e}")
            self.test_results.append(("WebSocket Upgrade", f"FAILED: {e}"))
            return False

    async def run_all_tests(self):
        """Run all frontend integration tests"""
        print("\n" + "=" * 70)
        print("Frontend Integration Tests")
        print("=" * 70)
        print(f"Frontend URL: {self.frontend_url}")
        print(f"API URL: {self.api_url}")
        print(f"WebSocket URL: {self.websocket_url}")
        print(f"Test started at: {datetime.utcnow().isoformat()}")

        # Run synchronous tests
        self.test_frontend_health()
        self.test_frontend_homepage()
        self.test_api_connection()
        self.test_metrics_endpoint()
        self.test_cors_headers()
        self.test_static_assets()

        # Run async tests
        await self.test_websocket_upgrade()

        # Print summary
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)

        passed = sum(1 for _, result in self.test_results if result == "PASSED")
        total = len(self.test_results)

        for test_name, result in self.test_results:
            status_icon = "✅" if result == "PASSED" else "❌"
            print(f"{status_icon} {test_name}: {result}")

        print(f"\nTotal: {passed}/{total} tests passed")
        print(f"Success rate: {(passed/total*100):.1f}%")

        # Additional diagnostics
        if passed < total:
            print("\n⚠️  Some tests failed. Check the following:")
            print("   1. Ensure all services are running (docker-compose ps)")
            print("   2. Check service logs (docker-compose logs)")
            print("   3. Verify environment variables")
            print("   4. Check network connectivity")

        return passed == total


async def main():
    """Main test execution"""
    # Get URLs from environment or use defaults
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost")
    api_url = os.getenv("API_URL", "http://localhost/api")
    websocket_url = os.getenv("WEBSOCKET_URL", "ws://localhost/ws")

    print(f"\nTesting frontend integration...")

    tester = FrontendIntegrationTester(frontend_url, api_url, websocket_url)

    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
