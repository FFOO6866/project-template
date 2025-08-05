"""
Unit Tests for NextJS API Client
===============================

Tier 1 unit tests focusing on:
- API client configuration and setup
- Authentication token management
- Request/response interceptors  
- Parameter validation
- Error handling without external dependencies

All external HTTP requests are mocked to ensure fast, isolated testing.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestAPIClientConfiguration:
    """Test API client configuration and initialization"""
    
    def test_api_client_initialization_default_config(self):
        """Test API client initializes with default configuration"""
        from fe_api_client import APIClient
        
        client = APIClient()
        
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30
        assert client.max_retries == 3
        assert "Content-Type" in client.default_headers
        assert client.default_headers["Content-Type"] == "application/json"
    
    def test_api_client_initialization_custom_config(self):
        """Test API client initializes with custom configuration"""
        from fe_api_client import APIClient
        
        config = {
            "base_url": "https://api.production.com",
            "timeout": 60,
            "max_retries": 5,
            "headers": {"Custom-Header": "value"}
        }
        
        client = APIClient(config)
        
        assert client.base_url == "https://api.production.com"
        assert client.timeout == 60
        assert client.max_retries == 5
        assert "Custom-Header" in client.default_headers
        assert client.default_headers["Custom-Header"] == "value"
    
    def test_api_client_environment_detection(self):
        """Test API client detects development vs production environment"""
        from fe_api_client import APIClient
        
        with patch.dict('os.environ', {'NODE_ENV': 'development'}):
            dev_client = APIClient()
            assert dev_client.base_url == "http://localhost:8000"
        
        with patch.dict('os.environ', {'NODE_ENV': 'production'}):
            prod_client = APIClient()
            assert prod_client.base_url.startswith("https://")


class TestAuthenticationTokenManagement:
    """Test JWT token storage, validation, and refresh logic"""
    
    @pytest.fixture
    def mock_token_data(self):
        """Mock JWT token data"""
        return {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJyb2xlIjoic2FsZXNfcmVwIiwiY29tcGFueV9pZCI6MSwiZXhwIjoxNzI1MzY3MjAwLCJpYXQiOjE3MjUyODA4MDB9.signature",
            "token_type": "bearer",
            "expires_in": 86400,
            "user": {
                "id": 1,
                "email": "test@test.com",
                "first_name": "Test",
                "last_name": "User",
                "role": "sales_rep",
                "company_name": "Test Company"
            }
        }
    
    def test_token_storage_and_retrieval(self, mock_token_data):
        """Test token is properly stored and retrieved"""
        from fe_api_client import APIClient
        
        client = APIClient()
        client.set_auth_token(mock_token_data["access_token"])
        
        assert client.get_auth_token() == mock_token_data["access_token"]
        assert "Authorization" in client.auth_headers
        assert client.auth_headers["Authorization"] == f"Bearer {mock_token_data['access_token']}"
    
    def test_token_expiration_detection(self):
        """Test token expiration detection"""
        from fe_api_client import APIClient
        
        client = APIClient()
        
        # Create expired token (expired 1 hour ago)
        expired_time = datetime.utcnow() - timedelta(hours=1)
        expired_token = client._create_mock_jwt({
            "exp": int(expired_time.timestamp()),
            "user_id": 1
        })
        
        client.set_auth_token(expired_token)
        assert client.is_token_expired() == True
        
        # Create valid token (expires in 1 hour)
        valid_time = datetime.utcnow() + timedelta(hours=1)
        valid_token = client._create_mock_jwt({
            "exp": int(valid_time.timestamp()),
            "user_id": 1
        })
        
        client.set_auth_token(valid_token)
        assert client.is_token_expired() == False
    
    def test_token_refresh_logic(self, mock_token_data):
        """Test automatic token refresh logic"""
        from fe_api_client import APIClient
        
        client = APIClient()
        
        with patch.object(client, '_refresh_token') as mock_refresh:
            mock_refresh.return_value = mock_token_data["access_token"]
            
            # Simulate expired token scenario
            client.set_auth_token("expired_token")
            with patch.object(client, 'is_token_expired', return_value=True):
                new_token = client.ensure_valid_token()
                
                mock_refresh.assert_called_once()
                assert new_token == mock_token_data["access_token"]
    
    def test_token_removal_on_logout(self):
        """Test token is properly removed on logout"""
        from fe_api_client import APIClient
        
        client = APIClient()
        client.set_auth_token("test_token")
        
        assert client.get_auth_token() == "test_token"
        
        client.logout()
        
        assert client.get_auth_token() is None
        assert "Authorization" not in client.auth_headers


class TestRequestResponseInterceptors:
    """Test request and response interceptors for error handling and retry logic"""
    
    def test_request_interceptor_adds_auth_headers(self):
        """Test request interceptor automatically adds authentication headers"""
        from fe_api_client import APIClient
        
        client = APIClient()
        client.set_auth_token("test_token")
        
        mock_request = {"url": "/api/test", "headers": {}}
        intercepted_request = client._request_interceptor(mock_request)
        
        assert "Authorization" in intercepted_request["headers"]
        assert intercepted_request["headers"]["Authorization"] == "Bearer test_token"
    
    def test_request_interceptor_adds_common_headers(self):
        """Test request interceptor adds common headers"""
        from fe_api_client import APIClient
        
        client = APIClient()
        
        mock_request = {"url": "/api/test", "headers": {}}
        intercepted_request = client._request_interceptor(mock_request)
        
        assert "Content-Type" in intercepted_request["headers"]
        assert "X-Requested-With" in intercepted_request["headers"]
        assert intercepted_request["headers"]["X-Requested-With"] == "XMLHttpRequest"
    
    def test_response_interceptor_handles_success(self):
        """Test response interceptor properly handles successful responses"""
        from fe_api_client import APIClient
        
        client = APIClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": "test"}
        
        result = client._response_interceptor(mock_response)
        
        assert result["success"] == True
        assert result["data"] == "test"
    
    def test_response_interceptor_handles_authentication_errors(self):
        """Test response interceptor handles 401 authentication errors"""
        from fe_api_client import APIClient, AuthenticationError
        
        client = APIClient()
        client.set_auth_token("test_token")
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Token expired"}
        
        with pytest.raises(AuthenticationError) as exc_info:
            client._response_interceptor(mock_response)
        
        assert "Token expired" in str(exc_info.value)
        # Token should be cleared on authentication error
        assert client.get_auth_token() is None
    
    def test_response_interceptor_handles_server_errors(self):
        """Test response interceptor handles 5xx server errors"""
        from fe_api_client import APIClient, ServerError
        
        client = APIClient()
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        
        with pytest.raises(ServerError) as exc_info:
            client._response_interceptor(mock_response)
        
        assert "Internal server error" in str(exc_info.value)
    
    def test_retry_logic_on_network_errors(self):
        """Test retry logic is invoked on network errors"""
        from fe_api_client import APIClient
        import requests
        
        client = APIClient()
        
        with patch.object(client.session, 'request') as mock_request:
            # Simulate network error then success
            mock_request.side_effect = [
                requests.exceptions.ConnectionError("Network error"),
                Mock(status_code=200, json=lambda: {"success": True})
            ]
            
            result = client._make_request_with_retry("POST", "/api/test", {})
            
            assert mock_request.call_count == 2
            assert result["success"] == True


class TestParameterValidation:
    """Test parameter validation for API requests"""
    
    def test_login_parameter_validation(self):
        """Test login request parameter validation"""
        from fe_api_client import APIClient, ValidationError
        
        client = APIClient()
        
        # Test missing email
        with pytest.raises(ValidationError) as exc_info:
            client.validate_login_params({"password": "test123"})
        assert "email" in str(exc_info.value).lower()
        
        # Test missing password
        with pytest.raises(ValidationError) as exc_info:
            client.validate_login_params({"email": "test@test.com"})
        assert "password" in str(exc_info.value).lower()
        
        # Test invalid email format
        with pytest.raises(ValidationError) as exc_info:
            client.validate_login_params({"email": "invalid-email", "password": "test123"})
        assert "email" in str(exc_info.value).lower()
        
        # Test valid parameters
        valid_params = {"email": "test@test.com", "password": "test123"}
        result = client.validate_login_params(valid_params)
        assert result == valid_params
    
    def test_file_upload_parameter_validation(self):
        """Test file upload parameter validation"""
        from fe_api_client import APIClient, ValidationError
        
        client = APIClient()
        
        # Test missing file
        with pytest.raises(ValidationError) as exc_info:
            client.validate_file_upload_params({})
        assert "file" in str(exc_info.value).lower()
        
        # Test invalid file size
        large_file_mock = Mock()
        large_file_mock.size = 100 * 1024 * 1024  # 100MB
        
        with pytest.raises(ValidationError) as exc_info:
            client.validate_file_upload_params({"file": large_file_mock})
        assert "size" in str(exc_info.value).lower()
        
        # Test invalid file type
        invalid_file_mock = Mock()
        invalid_file_mock.size = 1024  # 1KB
        invalid_file_mock.type = "application/x-executable"
        
        with pytest.raises(ValidationError) as exc_info:
            client.validate_file_upload_params({"file": invalid_file_mock})
        assert "type" in str(exc_info.value).lower()
        
        # Test valid file
        valid_file_mock = Mock()
        valid_file_mock.size = 1024  # 1KB
        valid_file_mock.type = "application/pdf"
        valid_file_mock.name = "test.pdf"
        
        result = client.validate_file_upload_params({
            "file": valid_file_mock,
            "customer_id": 1,
            "document_type": "RFP"
        })
        assert result["file"] == valid_file_mock
        assert result["customer_id"] == 1
        assert result["document_type"] == "RFP"


class TestErrorHandling:
    """Test error handling without external dependencies"""
    
    def test_custom_error_classes(self):
        """Test custom error classes are properly defined"""
        from fe_api_client import (
            APIClientError, AuthenticationError, ValidationError, 
            ServerError, NetworkError
        )
        
        # Test base error class
        base_error = APIClientError("Base error")
        assert str(base_error) == "Base error"
        assert isinstance(base_error, Exception)
        
        # Test authentication error
        auth_error = AuthenticationError("Invalid token")
        assert str(auth_error) == "Invalid token"
        assert isinstance(auth_error, APIClientError)
        
        # Test validation error
        validation_error = ValidationError("Invalid parameters")
        assert str(validation_error) == "Invalid parameters"
        assert isinstance(validation_error, APIClientError)
        
        # Test server error
        server_error = ServerError("Internal server error")
        assert str(server_error) == "Internal server error"
        assert isinstance(server_error, APIClientError)
        
        # Test network error
        network_error = NetworkError("Connection timeout")
        assert str(network_error) == "Connection timeout"
        assert isinstance(network_error, APIClientError)
    
    def test_error_context_preservation(self):
        """Test error context is preserved through the client"""
        from fe_api_client import APIClient, AuthenticationError
        
        client = APIClient()
        
        # Test error context includes request details
        try:
            client._handle_error(401, {"detail": "Token expired"}, "/api/protected")
        except AuthenticationError as e:
            assert "Token expired" in str(e)
            assert hasattr(e, 'status_code')
            assert hasattr(e, 'endpoint')
            assert e.status_code == 401
            assert e.endpoint == "/api/protected"


@pytest.mark.unit
class TestAPIClientPerformance:
    """Test API client performance characteristics for unit testing"""
    
    def test_initialization_performance(self, performance_monitor):
        """Test API client initialization is fast"""
        from fe_api_client import APIClient
        
        performance_monitor.start("initialization")
        client = APIClient()
        performance_monitor.assert_within_threshold(0.1, "initialization")  # <100ms
        
        assert client is not None
    
    def test_token_operations_performance(self, performance_monitor):
        """Test token operations are fast"""
        from fe_api_client import APIClient
        
        client = APIClient()
        
        performance_monitor.start("token_operations")
        
        # Multiple token operations
        for i in range(100):
            client.set_auth_token(f"token_{i}")
            token = client.get_auth_token()
            client.is_token_expired()
        
        performance_monitor.assert_within_threshold(0.5, "token_operations")  # <500ms for 100 operations
    
    def test_parameter_validation_performance(self, performance_monitor):
        """Test parameter validation is fast"""
        from fe_api_client import APIClient
        
        client = APIClient()
        
        performance_monitor.start("validation")
        
        # Multiple validation operations
        for i in range(50):
            valid_params = {"email": f"test{i}@test.com", "password": "test123"}
            client.validate_login_params(valid_params)
        
        performance_monitor.assert_within_threshold(0.2, "validation")  # <200ms for 50 validations