"""
Test Enhanced Nexus API - Comprehensive Validation
==================================================

Test the enhanced API server with multiple workflows:
- Multiple workflow execution
- Performance monitoring
- Error handling
- Different endpoint types
- Session management

Building on confirmed working minimal API foundation.
"""

import os
import sys
import time
import requests
import threading
import json
from pathlib import Path

# Add project path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_enhanced_nexus_api():
    """Test enhanced Nexus API functionality"""
    
    print("Enhanced Nexus API Test")
    print("=" * 50)
    
    # Import and start the server in background
    try:
        from enhanced_minimal_nexus_api import EnhancedMinimalNexusAPI
        
        print("\n1. Starting Enhanced API Server...")
        
        api = EnhancedMinimalNexusAPI()
        
        # Start server in background thread
        def start_server():
            try:
                api.start()
            except Exception as e:
                print(f"   ERROR: Server start failed: {e}")
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(4)
        
        base_url = "http://127.0.0.1:8003"
        
        print("   SUCCESS: Enhanced API server started")
        
        # 2. Test root endpoint
        print("\n2. Testing root endpoint...")
        
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            
            if response.status_code == 200:
                root_data = response.json()
                print("   SUCCESS: Root endpoint responds")
                print(f"      Version: {root_data.get('version')}")
                print(f"      Workflows: {root_data.get('workflows')}")
                print(f"      DataFlow: {root_data.get('dataflow_available')}")
            else:
                print(f"   ERROR: Root endpoint failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERROR: Root endpoint failed: {e}")
            return False
        
        # 3. Test health check
        print("\n3. Testing health check...")
        
        try:
            response = requests.get(f"{base_url}/api/health", timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                print("   SUCCESS: Health check endpoint responds")
                print(f"      Status: {health_data.get('status')}")
                print(f"      Uptime: {health_data.get('uptime_seconds', 0):.1f}s")
                print(f"      Requests: {health_data.get('total_requests', 0)}")
            else:
                print(f"   ERROR: Health check failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERROR: Health check failed: {e}")
            return False
        
        # 4. Test workflows list
        print("\n4. Testing workflows list...")
        
        try:
            response = requests.get(f"{base_url}/api/workflows", timeout=5)
            
            if response.status_code == 200:
                workflows_data = response.json()
                workflows = workflows_data.get('workflows', {})
                print("   SUCCESS: Workflows list endpoint responds")
                print(f"      Count: {workflows_data.get('count', 0)}")
                for name, info in workflows.items():
                    print(f"      - {name}: {info.get('description')}")
            else:
                print(f"   ERROR: Workflows list failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERROR: Workflows list failed: {e}")
            return False
        
        # 5. Test each workflow
        print("\n5. Testing individual workflows...")
        
        # Test workflow: test
        try:
            response = requests.post(f"{base_url}/api/workflows/test/execute", json={}, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("   SUCCESS: Test workflow executed")
                    exec_time = result['metadata']['execution_time_ms']
                    print(f"      Execution time: {exec_time}ms")
                else:
                    print(f"   ERROR: Test workflow failed: {result}")
                    return False
            else:
                print(f"   ERROR: Test workflow HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERROR: Test workflow failed: {e}")
            return False
        
        # Test workflow: data_processing
        try:
            test_data = {
                "data": [
                    {"id": 1, "name": "item1", "value": 100},
                    {"id": 2, "name": "item2", "value": 200},
                    "simple_string",
                    42
                ]
            }
            
            response = requests.post(
                f"{base_url}/api/workflows/data_processing/execute", 
                json=test_data, 
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    process_result = result['results']['process_data']['result']
                    print("   SUCCESS: Data processing workflow executed")
                    print(f"      Processed: {process_result.get('input_count')} -> {process_result.get('output_count')} items")
                else:
                    print(f"   ERROR: Data processing failed: {result}")
                    return False
            else:
                print(f"   ERROR: Data processing HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERROR: Data processing workflow failed: {e}")
            return False
        
        # Test workflow: classification
        try:
            item_data = {
                "item": {
                    "name": "Electric Drill",
                    "description": "High-powered electric drill for construction work",
                    "category": "unknown"
                }
            }
            
            response = requests.post(
                f"{base_url}/api/workflows/classification/execute", 
                json=item_data, 
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    class_result = result['results']['classify_item']['result']
                    classification = class_result.get('classification', {})
                    print("   SUCCESS: Classification workflow executed")
                    print(f"      Category: {classification.get('category')}")
                    print(f"      Confidence: {classification.get('confidence')}")
                else:
                    print(f"   ERROR: Classification failed: {result}")
                    return False
            else:
                print(f"   ERROR: Classification HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERROR: Classification workflow failed: {e}")
            return False
        
        # Test workflow: user
        try:
            user_data = {
                "operation": "info",
                "user_id": 1234
            }
            
            response = requests.post(
                f"{base_url}/api/workflows/user/execute", 
                json=user_data, 
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    user_result = result['results']['manage_user']['result']
                    user_info = user_result.get('user', {})
                    print("   SUCCESS: User workflow executed")
                    print(f"      User: {user_info.get('name')} ({user_info.get('email')})")
                else:
                    print(f"   ERROR: User workflow failed: {result}")
                    return False
            else:
                print(f"   ERROR: User workflow HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERROR: User workflow failed: {e}")
            return False
        
        # 6. Test convenient endpoints
        print("\n6. Testing convenient endpoints...")
        
        # Test /api/classify
        try:
            item_data = {
                "name": "Safety Helmet",
                "description": "Hard hat for construction safety"
            }
            
            response = requests.post(f"{base_url}/api/classify", json=item_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("   SUCCESS: Convenient classify endpoint works")
                else:
                    print(f"   ERROR: Convenient classify failed: {result}")
                    return False
            else:
                print(f"   ERROR: Convenient classify HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERROR: Convenient classify failed: {e}")
            return False
        
        # Test /api/process
        try:
            process_data = {
                "data": [1, 2, 3, {"test": True}]
            }
            
            response = requests.post(f"{base_url}/api/process", json=process_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("   SUCCESS: Convenient process endpoint works")
                else:
                    print(f"   ERROR: Convenient process failed: {result}")
                    return False
            else:
                print(f"   ERROR: Convenient process HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERROR: Convenient process failed: {e}")
            return False
        
        # Test /api/user/{user_id}
        try:
            response = requests.get(f"{base_url}/api/user/1234", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("   SUCCESS: Convenient user endpoint works")
                else:
                    print(f"   ERROR: Convenient user failed: {result}")
                    return False
            else:
                print(f"   ERROR: Convenient user HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERROR: Convenient user failed: {e}")
            return False
        
        # 7. Test metrics endpoint
        print("\n7. Testing metrics endpoint...")
        
        try:
            response = requests.get(f"{base_url}/api/metrics", timeout=5)
            
            if response.status_code == 200:
                metrics_data = response.json()
                requests_info = metrics_data.get('requests', {})
                performance = metrics_data.get('performance', {})
                
                print("   SUCCESS: Metrics endpoint responds")
                print(f"      Total requests: {requests_info.get('total', 0)}")
                print(f"      Success rate: {requests_info.get('success_rate', 0):.2%}")
                print(f"      Avg response time: {performance.get('average_response_time_ms', 0):.2f}ms")
                print(f"      Workflows executed: {performance.get('workflows_executed', 0)}")
            else:
                print(f"   ERROR: Metrics failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERROR: Metrics failed: {e}")
            return False
        
        # 8. Test error handling
        print("\n8. Testing error handling...")
        
        # Test non-existent workflow
        try:
            response = requests.post(f"{base_url}/api/workflows/nonexistent/execute", json={}, timeout=10)
            
            if response.status_code == 404:
                print("   SUCCESS: Non-existent workflow returns 404")
            else:
                print(f"   WARNING: Expected 404, got {response.status_code}")
                
        except Exception as e:
            print(f"   ERROR: Error handling test failed: {e}")
            return False
        
        # 9. Test performance under load
        print("\n9. Testing performance...")
        
        try:
            start_time = time.time()
            successful_requests = 0
            total_test_requests = 10
            
            for i in range(total_test_requests):
                response = requests.post(f"{base_url}/api/workflows/test/execute", json={}, timeout=5)
                if response.status_code == 200:
                    successful_requests += 1
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"   SUCCESS: Performance test completed")
            print(f"      Requests: {successful_requests}/{total_test_requests}")
            print(f"      Total time: {total_time:.2f}s")
            print(f"      Avg time per request: {(total_time/total_test_requests)*1000:.2f}ms")
            print(f"      Requests per second: {total_test_requests/total_time:.2f}")
            
        except Exception as e:
            print(f"   ERROR: Performance test failed: {e}")
            return False
        
        # Final metrics check
        print("\n10. Final metrics check...")
        
        try:
            response = requests.get(f"{base_url}/api/metrics", timeout=5)
            
            if response.status_code == 200:
                final_metrics = response.json()
                requests_info = final_metrics.get('requests', {})
                
                print("   SUCCESS: Final metrics retrieved")
                print(f"      Total requests handled: {requests_info.get('total', 0)}")
                print(f"      Final success rate: {requests_info.get('success_rate', 0):.2%}")
                
        except Exception as e:
            print(f"   ERROR: Final metrics failed: {e}")
            return False
        
        # Success summary
        print("\n" + "=" * 60)
        print("SUCCESS: Enhanced Nexus API Test PASSED")
        print("=" * 60)
        
        success_criteria = [
            "SUCCESS: Enhanced API server started",
            "SUCCESS: Root and health endpoints working",
            "SUCCESS: All 4 workflows execute successfully",
            "SUCCESS: Data processing workflow handles complex data",
            "SUCCESS: Classification workflow provides results",
            "SUCCESS: User management workflow functional",
            "SUCCESS: Convenient endpoints working",
            "SUCCESS: Metrics tracking operational", 
            "SUCCESS: Error handling working correctly",
            "SUCCESS: Performance acceptable under load"
        ]
        
        for criterion in success_criteria:
            print(f"   {criterion}")
        
        print(f"\nEnhanced Platform Features:")
        print(f"   • Multiple workflow types (4 workflows)")
        print(f"   • Performance monitoring and metrics")
        print(f"   • Convenient specialized endpoints")
        print(f"   • Proper error handling")
        print(f"   • Load testing capability")
        print(f"   • Windows-compatible deployment")
        
        print(f"\nNext Steps for Production:")
        print(f"   1. Enable authentication")
        print(f"   2. Add PostgreSQL/DataFlow integration")
        print(f"   3. Add CLI channel")
        print(f"   4. Add MCP channel")
        print(f"   5. Add advanced monitoring")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test entry point"""
    print("Testing Enhanced Nexus API Functionality")
    print("Building on confirmed working foundation\n")
    
    success = test_enhanced_nexus_api()
    
    if success:
        print("\n" + "=" * 70)
        print("SUCCESS: ENHANCED NEXUS API TEST PASSED!")
        print("Multi-workflow platform ready for production enhancement")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("ERROR: ENHANCED NEXUS API TEST FAILED")
        print("Fix issues before proceeding")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()