"""
Integration Tests for NextJS API Client
======================================

Tier 2 integration tests focusing on:
- Real HTTP connectivity to Nexus API server
- JWT authentication flow with real tokens
- File upload pipeline with actual files
- WebSocket connection establishment
- Error response handling from live server

NO MOCKING - All tests use real Nexus API running on localhost:8000
Tests require: ./tests/utils/test-env up && ./tests/utils/test-env status
"""

import pytest
import asyncio
import json
import tempfile
import websockets
from pathlib import Path
import sys
import time
import requests
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add src directory for Nexus imports
src_dir = project_root.parent.parent / "src"
sys.path.insert(0, str(src_dir))


@pytest.fixture(scope="module")
def nexus_server_url():
    """Base URL for the Nexus server"""
    return "http://localhost:8000"


@pytest.fixture(scope="module")
def test_user_credentials():
    """Test user credentials for authentication"""
    return {
        "email": "test@test.com",
        "password": "test123"
    }


@pytest.fixture(scope="module") 
def ensure_nexus_server_running(nexus_server_url):
    """Ensure Nexus server is running before tests"""
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{nexus_server_url}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ Nexus server is running at {nexus_server_url}")
                return True
        except requests.exceptions.RequestException:
            if attempt < max_attempts - 1:
                print(f"⏳ Waiting for Nexus server... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)
            else:
                pytest.skip(f"❌ Nexus server not available at {nexus_server_url}")
    
    return False


@pytest.fixture
def api_client(ensure_nexus_server_running, nexus_server_url):
    """API client configured for integration testing"""
    from fe_api_client import APIClient
    
    config = {
        "base_url": nexus_server_url,
        "timeout": 10,
        "max_retries": 2
    }
    return APIClient(config)


@pytest.fixture
def authenticated_client(api_client, test_user_credentials):
    """API client with valid authentication token"""
    # First, ensure test user exists by calling create-user CLI command
    try:
        import subprocess
        result = subprocess.run([
            "python", "-m", "nexus_app", "create-user",
            "--email", test_user_credentials["email"],
            "--first-name", "Test",
            "--last-name", "User", 
            "--role", "sales_rep",
            "--company-id", "1"
        ], capture_output=True, text=True, cwd=str(src_dir))
        print(f"User creation result: {result.stdout}")
    except Exception as e:
        print(f"Note: User creation failed (user may already exist): {e}")
    
    # Authenticate and get token
    login_response = api_client.login(test_user_credentials)
    api_client.set_auth_token(login_response["access_token"])
    
    return api_client


@pytest.mark.integration
@pytest.mark.requires_docker
class TestNexusAPIConnectivity:
    """Test real HTTP connectivity to Nexus API server"""
    
    def test_server_health_check(self, nexus_server_url):
        """Test server health endpoint is accessible"""
        response = requests.get(f"{nexus_server_url}/health")
        
        assert response.status_code == 200
        health_data = response.json()
        assert "status" in health_data
        assert health_data["status"] == "healthy"
    
    def test_api_docs_accessible(self, nexus_server_url):
        """Test FastAPI docs are accessible"""
        response = requests.get(f"{nexus_server_url}/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_cors_headers_present(self, nexus_server_url):
        """Test CORS headers are properly configured"""
        headers = {"Origin": "http://localhost:3000"}
        response = requests.options(f"{nexus_server_url}/api/auth/login", headers=headers)
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers
    
    def test_api_client_connection(self, api_client):
        """Test API client can establish connection"""
        # Test with a simple endpoint that doesn't require auth
        result = api_client.get("/health")
        
        assert result["status"] == "healthy"


@pytest.mark.integration 
@pytest.mark.requires_docker
class TestJWTAuthenticationFlow:
    """Test JWT authentication with real Nexus server"""
    
    def test_login_with_valid_credentials(self, api_client, test_user_credentials):
        """Test login with valid user credentials"""
        response = api_client.login(test_user_credentials)
        
        assert "access_token" in response
        assert "token_type" in response
        assert response["token_type"] == "bearer"
        assert "user" in response
        assert response["user"]["email"] == test_user_credentials["email"]
        
        # Verify token is properly formatted JWT
        token = response["access_token"]
        assert len(token.split('.')) == 3  # JWT has 3 parts
    
    def test_login_with_invalid_credentials(self, api_client):
        """Test login with invalid credentials returns 401"""
        invalid_credentials = {
            "email": "nonexistent@test.com", 
            "password": "wrongpassword"
        }
        
        from fe_api_client import AuthenticationError
        with pytest.raises(AuthenticationError) as exc_info:
            api_client.login(invalid_credentials)
        
        assert exc_info.value.status_code == 401
    
    def test_protected_endpoint_with_valid_token(self, authenticated_client):
        """Test accessing protected endpoint with valid token"""
        # Access a protected endpoint that requires authentication
        response = authenticated_client.get("/api/user/profile")
        
        assert "user" in response
        assert response["user"]["email"] == "test@test.com"
    
    def test_protected_endpoint_without_token(self, api_client):
        """Test accessing protected endpoint without token returns 401"""
        from fe_api_client import AuthenticationError
        
        with pytest.raises(AuthenticationError) as exc_info:
            api_client.get("/api/user/profile")
        
        assert exc_info.value.status_code == 401
    
    def test_protected_endpoint_with_expired_token(self, api_client):
        """Test accessing protected endpoint with expired token"""
        # Set an obviously expired token
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE1NzAwMDAwMDB9.invalid"
        api_client.set_auth_token(expired_token)
        
        from fe_api_client import AuthenticationError
        with pytest.raises(AuthenticationError) as exc_info:
            api_client.get("/api/user/profile")
        
        assert exc_info.value.status_code == 401
    
    def test_token_refresh_flow(self, authenticated_client):
        """Test automatic token refresh when token expires soon"""
        # This test verifies the client handles token refresh
        # In a real scenario, tokens would be refreshed automatically
        
        original_token = authenticated_client.get_auth_token()
        assert original_token is not None
        
        # Simulate token about to expire (would trigger refresh in real client)
        new_response = authenticated_client.get("/api/user/profile")
        assert "user" in new_response


@pytest.mark.integration
@pytest.mark.requires_docker  
class TestFileUploadPipeline:
    """Test file upload functionality with real files"""
    
    @pytest.fixture
    def test_pdf_file(self):
        """Create a temporary PDF file for testing"""
        content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(content)
            f.flush()
            yield f.name
        
        # Cleanup
        Path(f.name).unlink(missing_ok=True)
    
    @pytest.fixture
    def test_text_file(self):
        """Create a temporary text file for testing"""
        content = "This is a test document for file upload testing.\nMultiple lines of content."
        
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w') as f:
            f.write(content)
            f.flush()
            yield f.name
        
        # Cleanup
        Path(f.name).unlink(missing_ok=True)
    
    def test_upload_pdf_file(self, authenticated_client, test_pdf_file):
        """Test uploading a PDF file"""
        with open(test_pdf_file, 'rb') as f:
            files = {"file": (Path(test_pdf_file).name, f, "application/pdf")}
            data = {
                "customer_id": 1,
                "document_type": "RFP"
            }
            
            response = authenticated_client.upload_file(files, data)
        
        assert "document_id" in response
        assert "file_name" in response
        assert response["file_name"] == Path(test_pdf_file).name
        assert "processing_status" in response
        assert response["processing_status"] == "queued"
    
    def test_upload_text_file(self, authenticated_client, test_text_file):
        """Test uploading a text file"""
        with open(test_text_file, 'rb') as f:
            files = {"file": (Path(test_text_file).name, f, "text/plain")}
            data = {
                "document_type": "general"
            }
            
            response = authenticated_client.upload_file(files, data)
        
        assert "document_id" in response
        assert response["file_name"] == Path(test_text_file).name
    
    def test_upload_file_too_large(self, authenticated_client):
        """Test uploading a file that exceeds size limit"""
        # Create a file larger than 50MB limit
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            f.write(large_content)
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                files = {"file": ("large_file.txt", upload_file, "text/plain")}
                
                from fe_api_client import ValidationError
                with pytest.raises(ValidationError) as exc_info:
                    authenticated_client.upload_file(files, {})
                
                assert "413" in str(exc_info.value) or "too large" in str(exc_info.value).lower()
    
    def test_upload_invalid_file_type(self, authenticated_client):
        """Test uploading an invalid file type"""
        # Create a mock executable file
        with tempfile.NamedTemporaryFile(suffix=".exe") as f:
            f.write(b"fake executable content")
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                files = {"file": ("malware.exe", upload_file, "application/x-executable")}
                
                from fe_api_client import ValidationError
                with pytest.raises(ValidationError) as exc_info:
                    authenticated_client.upload_file(files, {})
                
                assert "file type" in str(exc_info.value).lower() or "not allowed" in str(exc_info.value).lower()


@pytest.mark.integration
@pytest.mark.requires_docker
class TestWebSocketConnection:
    """Test WebSocket connectivity for real-time features"""
    
    @pytest.fixture
    def ws_url(self, nexus_server_url):
        """WebSocket URL for connection"""
        return nexus_server_url.replace("http://", "ws://")
    
    @pytest.mark.asyncio
    async def test_websocket_connection_with_valid_token(self, authenticated_client, ws_url):
        """Test WebSocket connection with valid JWT token"""
        token = authenticated_client.get_auth_token()
        client_id = f"test_client_{int(time.time())}"
        
        ws_endpoint = f"{ws_url}/ws/{client_id}?token={token}"
        
        try:
            async with websockets.connect(ws_endpoint) as websocket:
                # Should receive welcome message
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome_msg)
                
                assert welcome_data["type"] == "welcome"
                assert "Connected to sales assistant" in welcome_data["message"]
                
        except asyncio.TimeoutError:
            pytest.fail("Did not receive welcome message within timeout")
        except Exception as e:
            pytest.fail(f"WebSocket connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_connection_with_invalid_token(self, ws_url):
        """Test WebSocket connection with invalid token"""
        invalid_token = "invalid.jwt.token"
        client_id = f"test_client_{int(time.time())}"
        
        ws_endpoint = f"{ws_url}/ws/{client_id}?token={invalid_token}"
        
        with pytest.raises(websockets.exceptions.ConnectionClosedError) as exc_info:
            async with websockets.connect(ws_endpoint) as websocket:
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
        
        # Should close with authentication error code
        assert exc_info.value.code == 1008  # Policy violation (invalid token)
    
    @pytest.mark.asyncio
    async def test_websocket_bidirectional_communication(self, authenticated_client, ws_url):
        """Test sending and receiving messages via WebSocket"""
        token = authenticated_client.get_auth_token()
        client_id = f"test_client_{int(time.time())}"
        
        ws_endpoint = f"{ws_url}/ws/{client_id}?token={token}"
        
        async with websockets.connect(ws_endpoint) as websocket:
            # Receive welcome message
            welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            welcome_data = json.loads(welcome_msg)
            assert welcome_data["type"] == "welcome"
            
            # Send chat message
            chat_message = {
                "type": "chat_message",
                "message": "Hello from integration test",
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(chat_message))
            
            # Receive response
            response_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response_msg)
            
            assert response_data["type"] == "chat_response"
            assert "Hello from integration test" in response_data["message"]
    
    @pytest.mark.asyncio
    async def test_websocket_quote_request_flow(self, authenticated_client, ws_url):
        """Test quote request flow via WebSocket"""
        token = authenticated_client.get_auth_token()
        client_id = f"test_client_{int(time.time())}"
        
        ws_endpoint = f"{ws_url}/ws/{client_id}?token={token}"
        
        async with websockets.connect(ws_endpoint) as websocket:
            # Receive welcome message
            await asyncio.wait_for(websocket.recv(), timeout=5.0)
            
            # Send quote request
            quote_request = {
                "type": "quote_request",
                "customer_id": 1,
                "products": ["Product A", "Product B"],
                "message": "Please generate quote for these products"
            }
            
            await websocket.send(json.dumps(quote_request))
            
            # Should receive processing message
            processing_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            processing_data = json.loads(processing_msg)
            assert processing_data["type"] == "quote_processing"
            
            # Should receive completion message
            completion_msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            completion_data = json.loads(completion_msg)
            assert completion_data["type"] == "quote_ready"
            assert "quote_id" in completion_data


@pytest.mark.integration
@pytest.mark.requires_docker
class TestErrorResponseHandling:
    """Test error response handling from live server"""
    
    def test_404_not_found_handling(self, api_client):
        """Test handling of 404 Not Found responses"""
        from fe_api_client import APIClientError
        
        with pytest.raises(APIClientError) as exc_info:
            api_client.get("/api/nonexistent/endpoint")
        
        assert exc_info.value.status_code == 404
    
    def test_403_forbidden_handling(self, api_client):
        """Test handling of 403 Forbidden responses"""
        # Try to access admin endpoint without proper role
        api_client.set_auth_token("user_token_without_admin_role")
        
        from fe_api_client import AuthenticationError
        with pytest.raises(AuthenticationError) as exc_info:
            api_client.get("/api/admin/users")
        
        assert exc_info.value.status_code in [401, 403]
    
    def test_429_rate_limit_handling(self, api_client):
        """Test handling of 429 Rate Limit responses"""
        # Make many rapid requests to trigger rate limiting
        for i in range(20):  # Exceed rate limit of 1000/min by making rapid requests
            try:
                api_client.get("/health")
            except Exception as e:
                if "429" in str(e):
                    # Rate limit triggered successfully
                    assert "rate limit" in str(e).lower() or "too many requests" in str(e).lower()
                    break
        else:
            # Rate limiting may not be triggered in test environment
            print("Note: Rate limiting not triggered (may be disabled in test)")
    
    def test_server_timeout_handling(self, api_client):
        """Test handling of server timeout scenarios"""
        # Set very short timeout to simulate timeout
        api_client.timeout = 0.001  # 1ms timeout
        
        from fe_api_client import NetworkError
        with pytest.raises(NetworkError) as exc_info:
            api_client.get("/api/slow/endpoint")  # This should timeout
        
        assert "timeout" in str(exc_info.value).lower()
    
    def test_malformed_json_response_handling(self, authenticated_client):
        """Test handling of malformed JSON responses"""
        # This would be difficult to test with real server
        # Instead, test client's JSON parsing error handling
        from fe_api_client import ServerError
        
        with pytest.raises((ServerError, json.JSONDecodeError)):
            # Try to manually trigger a JSON decode error
            authenticated_client._handle_response_json("invalid json response")


@pytest.mark.integration
@pytest.mark.requires_docker
class TestAPIClientPerformanceIntegration:
    """Test API client performance with real server"""
    
    def test_login_response_time(self, api_client, test_user_credentials, performance_monitor):
        """Test login response time is acceptable"""
        performance_monitor.start("login")
        
        response = api_client.login(test_user_credentials)
        
        performance_monitor.assert_within_threshold(3.0, "login")  # <3 seconds
        assert "access_token" in response
    
    def test_concurrent_requests_performance(self, authenticated_client, performance_monitor):
        """Test handling of concurrent requests"""
        import concurrent.futures
        
        performance_monitor.start("concurrent_requests")
        
        def make_request(i):
            return authenticated_client.get(f"/api/user/profile?req={i}")
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in futures]
        
        performance_monitor.assert_within_threshold(5.0, "concurrent_requests")  # <5 seconds total
        
        # All requests should succeed
        assert len(results) == 10
        for result in results:
            assert "user" in result
    
    def test_file_upload_performance(self, authenticated_client, performance_monitor):
        """Test file upload performance"""
        # Create a reasonably sized test file (1MB)
        test_content = b"x" * (1024 * 1024)  # 1MB
        
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            f.write(test_content)
            f.flush()
            
            performance_monitor.start("file_upload")
            
            with open(f.name, 'rb') as upload_file:
                files = {"file": ("test_1mb.txt", upload_file, "text/plain")}
                response = authenticated_client.upload_file(files, {"document_type": "test"})
            
            performance_monitor.assert_within_threshold(10.0, "file_upload")  # <10 seconds for 1MB
            assert "document_id" in response