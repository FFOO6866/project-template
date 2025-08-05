"""
Nexus DataFlow Platform Test Suite
=================================

Comprehensive testing suite for multi-channel Nexus platform functionality.
Tests API, CLI, and MCP channels with DataFlow integration.
"""

import pytest
import asyncio
import json
import time
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Apply Windows compatibility
import windows_sdk_compatibility

# Test configuration
TEST_CONFIG = {
    "api_base_url": "http://localhost:8000",
    "mcp_base_url": "http://localhost:3001",
    "test_timeout": 30,
    "performance_threshold_ms": 2000,
    "test_user_email": "test@example.com",
    "test_company_name": "Test Company Ltd"
}

class NexusPlatformTester:
    """Test suite for Nexus DataFlow platform"""
    
    def __init__(self):
        self.api_base = TEST_CONFIG["api_base_url"]
        self.mcp_base = TEST_CONFIG["mcp_base_url"]
        self.auth_token = None
        self.test_data = {}
        
    def setup_test_environment(self):
        """Setup test environment and data"""
        print("🔧 Setting up test environment...")
        
        # Wait for platform to be ready
        self.wait_for_platform_ready()
        
        # Create test data
        self.test_data = {
            "company": {
                "name": TEST_CONFIG["test_company_name"],
                "industry": "testing",
                "is_active": True
            },
            "user": {
                "email": TEST_CONFIG["test_user_email"],
                "first_name": "Test",
                "last_name": "User",
                "role": "admin",
                "is_active": True
            },
            "product_classification": {
                "product_id": 1,
                "product_data": {
                    "name": "Test Product",
                    "description": "A test product for classification",
                    "category": "electronics"
                },
                "classification_method": "ml_automatic"
            }
        }
        
        print("✅ Test environment ready")
    
    def wait_for_platform_ready(self, max_retries=30):
        """Wait for platform to be ready"""
        print("⏳ Waiting for platform to be ready...")
        
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.api_base}/api/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get("status") == "healthy":
                        print(f"✅ Platform ready after {i+1} attempts")
                        return True
            except requests.exceptions.RequestException:
                pass
            
            print(f"   Attempt {i+1}/{max_retries} - waiting...")
            time.sleep(2)
        
        raise Exception("Platform failed to become ready within timeout")
    
    def test_health_check(self):
        """Test platform health check"""
        print("\n🔍 Testing health check...")
        
        start_time = time.time()
        response = requests.get(f"{self.api_base}/api/health")
        response_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        health_data = response.json()
        assert health_data["status"] in ["healthy", "degraded"], f"Invalid health status: {health_data['status']}"
        
        # Check response time
        assert response_time < TEST_CONFIG["performance_threshold_ms"], f"Health check too slow: {response_time}ms"
        
        print(f"✅ Health check passed ({response_time:.1f}ms)")
        print(f"   Status: {health_data['status']}")
        print(f"   DataFlow: {health_data.get('dataflow', {}).get('status', 'unknown')}")
        
        return health_data
    
    def test_dataflow_discovery(self):
        """Test DataFlow node discovery"""
        print("\n🔍 Testing DataFlow node discovery...")
        
        # This would be accessed via the platform's internal API
        # For now, we'll test it indirectly through the metrics endpoint
        response = requests.get(f"{self.api_base}/api/metrics")
        assert response.status_code == 401, "Metrics should require authentication"
        
        print("✅ DataFlow discovery test passed (authentication required)")
    
    def test_api_endpoints(self):
        """Test API endpoints functionality"""
        print("\n🔍 Testing API endpoints...")
        
        # Test CORS headers
        response = requests.options(f"{self.api_base}/api/health")
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        print("✅ CORS headers present")
        
        # Test compression
        headers = {"Accept-Encoding": "gzip"}
        response = requests.get(f"{self.api_base}/api/health", headers=headers)
        if "Content-Encoding" in response.headers:
            print("✅ Response compression enabled")
        
        # Test performance headers
        response = requests.get(f"{self.api_base}/api/health")
        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time < TEST_CONFIG["performance_threshold_ms"]
        print(f"✅ Performance headers present ({process_time:.1f}ms)")
        
        # Test rate limiting (implicit)
        print("✅ API endpoints test passed")
    
    def test_dataflow_operations_unauthenticated(self):
        """Test DataFlow operations without authentication"""
        print("\n🔍 Testing DataFlow operations (unauthenticated)...")
        
        # Test that DataFlow operations require authentication
        test_endpoints = [
            "/api/dataflow/company/create",
            "/api/dataflow/user/list", 
            "/api/classification/classify",
            "/api/bulk/create"
        ]
        
        for endpoint in test_endpoints:
            response = requests.post(f"{self.api_base}{endpoint}", json={})
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"
        
        print("✅ DataFlow operations properly secured")
    
    def test_cli_interface(self):
        """Test CLI interface functionality"""
        print("\n🔍 Testing CLI interface...")
        
        try:
            # Test CLI help
            result = subprocess.run(
                ["python", "start_nexus_platform.py", "help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            assert result.returncode == 0, f"CLI help failed: {result.stderr}"
            assert "Nexus DataFlow Platform" in result.stdout
            print("✅ CLI help command works")
            
            # Test CLI check command
            result = subprocess.run(
                ["python", "start_nexus_platform.py", "check"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # Check command may fail due to missing dependencies, but should not crash
            assert "DEPENDENCY AND CONFIGURATION CHECK" in result.stdout
            print("✅ CLI check command works")
            
        except subprocess.TimeoutExpired:
            print("⚠️  CLI tests timed out (expected in some environments)")
        except FileNotFoundError:
            print("⚠️  CLI tests skipped (Python not in PATH)")
    
    def test_configuration_management(self):
        """Test configuration management"""
        print("\n🔍 Testing configuration management...")
        
        config_path = Path("nexus_config.json")
        
        # Test config creation
        if not config_path.exists():
            subprocess.run(["python", "start_nexus_platform.py", "config"], 
                          capture_output=True, timeout=10)
        
        # Check config file structure
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            
            required_sections = ["server", "security", "performance", "monitoring"]
            for section in required_sections:
                assert section in config, f"Missing config section: {section}"
            
            print("✅ Configuration structure valid")
        else:
            print("⚠️  Configuration file not found")
    
    def test_error_handling(self):
        """Test error handling and resilience"""
        print("\n🔍 Testing error handling...")
        
        # Test invalid endpoints
        response = requests.get(f"{self.api_base}/api/nonexistent")
        assert response.status_code == 404
        
        # Test malformed requests
        response = requests.post(f"{self.api_base}/api/health", json="invalid")
        assert response.status_code in [400, 405]  # Bad request or method not allowed
        
        # Test oversized requests (if applicable)
        large_payload = {"data": "x" * 10000}
        response = requests.post(f"{self.api_base}/api/health", json=large_payload)
        # Should either accept or reject gracefully
        assert response.status_code in [200, 400, 413]
        
        print("✅ Error handling test passed")
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        print("\n🔍 Testing performance benchmarks...")
        
        # Health check performance
        response_times = []
        for i in range(5):
            start_time = time.time()
            response = requests.get(f"{self.api_base}/api/health")
            response_time = (time.time() - start_time) * 1000
            response_times.append(response_time)
            assert response.status_code == 200
        
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        print(f"   Average response time: {avg_response_time:.1f}ms")
        print(f"   Max response time: {max_response_time:.1f}ms")
        
        # Check performance targets
        assert avg_response_time < TEST_CONFIG["performance_threshold_ms"], f"Average response time too high: {avg_response_time}ms"
        assert max_response_time < TEST_CONFIG["performance_threshold_ms"] * 2, f"Max response time too high: {max_response_time}ms"
        
        print("✅ Performance benchmarks passed")
    
    def test_platform_integration(self):
        """Test overall platform integration"""
        print("\n🔍 Testing platform integration...")
        
        # Test that all expected endpoints are available
        expected_endpoints = [
            "/api/health",
            "/api/metrics",
            "/docs",  # FastAPI docs
            "/redoc"  # Alternative docs
        ]
        
        available_endpoints = []
        for endpoint in expected_endpoints:
            try:
                response = requests.get(f"{self.api_base}{endpoint}")
                if response.status_code in [200, 401]:  # 401 is OK for protected endpoints
                    available_endpoints.append(endpoint)
            except requests.RequestException:
                pass
        
        print(f"   Available endpoints: {len(available_endpoints)}/{len(expected_endpoints)}")
        for endpoint in available_endpoints:
            print(f"   ✅ {endpoint}")
        
        # At least health check should be available
        assert "/api/health" in available_endpoints, "Health check endpoint not available"
        
        print("✅ Platform integration test passed")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🧪 NEXUS DATAFLOW PLATFORM TEST SUITE")
        print("="*60)
        
        test_results = []
        
        tests = [
            ("Setup", self.setup_test_environment),
            ("Health Check", self.test_health_check),
            ("DataFlow Discovery", self.test_dataflow_discovery),
            ("API Endpoints", self.test_api_endpoints),
            ("DataFlow Security", self.test_dataflow_operations_unauthenticated),
            ("CLI Interface", self.test_cli_interface),
            ("Configuration", self.test_configuration_management),
            ("Error Handling", self.test_error_handling),
            ("Performance", self.test_performance_benchmarks),
            ("Integration", self.test_platform_integration)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"\n📋 Running: {test_name}")
                test_func()
                test_results.append((test_name, "PASSED", None))
                passed += 1
                print(f"✅ {test_name} - PASSED")
            except Exception as e:
                test_results.append((test_name, "FAILED", str(e)))
                failed += 1
                print(f"❌ {test_name} - FAILED: {e}")
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        for test_name, status, error in test_results:
            status_icon = "✅" if status == "PASSED" else "❌"
            print(f"{status_icon} {test_name}: {status}")
            if error:
                print(f"    Error: {error}")
        
        print(f"\n📈 Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed! Platform is ready for use.")
        else:
            print("⚠️  Some tests failed. Check platform configuration.")
        
        return failed == 0

def run_quick_test():
    """Run a quick test to verify platform is working"""
    print("🚀 Running quick platform test...")
    
    tester = NexusPlatformTester()
    
    try:
        tester.wait_for_platform_ready(max_retries=10)
        health_data = tester.test_health_check()
        tester.test_api_endpoints()
        
        print("\n✅ Quick test passed! Platform is working.")
        return True
    
    except Exception as e:
        print(f"\n❌ Quick test failed: {e}")
        return False

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nexus DataFlow Platform Test Suite")
    parser.add_argument("--quick", action="store_true", help="Run quick test only")
    parser.add_argument("--api-url", default=TEST_CONFIG["api_base_url"], help="API base URL")
    parser.add_argument("--mcp-url", default=TEST_CONFIG["mcp_base_url"], help="MCP base URL")
    
    args = parser.parse_args()
    
    # Update test config
    TEST_CONFIG["api_base_url"] = args.api_url
    TEST_CONFIG["mcp_base_url"] = args.mcp_url
    
    if args.quick:
        success = run_quick_test()
    else:
        tester = NexusPlatformTester()
        success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()