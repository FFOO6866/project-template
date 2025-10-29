# VM Testing Strategy Documentation

## Overview

This document outlines the comprehensive testing strategy for the Horme POV platform in Virtual Machine (VM) environments, covering unit testing, integration testing, system testing, security testing, performance testing, and operational testing.

## Testing Philosophy

### Core Principles
1. **Real Infrastructure Testing**: No mocking in Tiers 2-3 tests - use actual containers and services
2. **Environment Parity**: Test in environments that mirror production as closely as possible
3. **Security-First Testing**: Security validation integrated into all test phases
4. **Automated Validation**: Comprehensive automated test suites with CI/CD integration
5. **Performance Baseline**: Establish and validate performance benchmarks
6. **Operational Testing**: Validate deployment, backup, recovery, and maintenance procedures

### Test Environment Types

#### Tier 1: Unit Tests
- **Scope**: Individual functions, methods, and components
- **Environment**: Isolated test containers with mocked external dependencies
- **Duration**: <5 minutes total execution time
- **Frequency**: Every commit

#### Tier 2: Integration Tests
- **Scope**: Service-to-service communication and data flow
- **Environment**: Full stack with real containers (database, redis, services)
- **Duration**: 5-15 minutes total execution time
- **Frequency**: Every pull request

#### Tier 3: System Tests
- **Scope**: Complete system functionality and user workflows
- **Environment**: Production-like VM environment with full security hardening
- **Duration**: 15-60 minutes total execution time
- **Frequency**: Daily builds and pre-deployment

## Test Infrastructure

### Test Environment Setup

#### VM Test Environment Specifications
```yaml
# docker-compose.test-vm.yml
version: '3.8'

services:
  # Test Database
  postgres-test:
    image: postgres:15-alpine
    container_name: test-postgres
    environment:
      - POSTGRES_DB=horme_test
      - POSTGRES_USER=horme_test
      - POSTGRES_PASSWORD=test_password
    volumes:
      - postgres_test_data:/var/lib/postgresql/data
    networks:
      - test_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U horme_test -d horme_test"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Test Redis
  redis-test:
    image: redis:7-alpine
    container_name: test-redis
    networks:
      - test_network
    healthcheck:
      test: ["CMD-SHELL", "redis-cli ping || exit 1"]
      interval: 5s
      timeout: 3s
      retries: 3

  # Test API Service
  api-test:
    build:
      context: .
      dockerfile: Dockerfile.api
      target: test
    container_name: test-api
    environment:
      - NODE_ENV=test
      - DATABASE_URL=postgresql://horme_test:test_password@postgres-test:5432/horme_test
      - REDIS_URL=redis://redis-test:6379
      - JWT_SECRET=test_jwt_secret
      - LOG_LEVEL=debug
    networks:
      - test_network
    depends_on:
      postgres-test:
        condition: service_healthy
      redis-test:
        condition: service_healthy
    volumes:
      - ./tests:/app/tests:ro
      - test_logs:/app/logs

  # Test MCP Service
  mcp-test:
    build:
      context: .
      dockerfile: Dockerfile.mcp-lightweight
      target: test
    container_name: test-mcp
    environment:
      - NODE_ENV=test
      - DATABASE_URL=postgresql://horme_test:test_password@postgres-test:5432/horme_test
      - WS_PORT=3002
    networks:
      - test_network
    depends_on:
      postgres-test:
        condition: service_healthy
    volumes:
      - ./tests:/app/tests:ro
      - test_logs:/app/logs

  # Test Frontend
  frontend-test:
    build:
      context: ./fe-reference
      dockerfile: Dockerfile
      target: test
    container_name: test-frontend
    environment:
      - NODE_ENV=test
      - API_URL=http://api-test:8000
      - WS_URL=ws://mcp-test:3002
    networks:
      - test_network
    volumes:
      - ./fe-reference/tests:/app/tests:ro

networks:
  test_network:
    driver: bridge

volumes:
  postgres_test_data:
  test_logs:
```

### Test Data Management

#### Test Data Setup Script
```bash
#!/bin/bash
# scripts/setup-test-data.sh

set -e

echo "🔧 Setting up test data..."

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Create test database schema
docker-compose -f docker-compose.test-vm.yml exec postgres-test \
  psql -U horme_test -d horme_test -c "
    CREATE TABLE IF NOT EXISTS test_products (
      id SERIAL PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      description TEXT,
      price DECIMAL(10,2),
      category VARCHAR(100),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS test_quotations (
      id SERIAL PRIMARY KEY,
      product_id INTEGER REFERENCES test_products(id),
      quantity INTEGER NOT NULL,
      unit_price DECIMAL(10,2),
      total_amount DECIMAL(10,2),
      status VARCHAR(50) DEFAULT 'pending',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS test_documents (
      id SERIAL PRIMARY KEY,
      title VARCHAR(255) NOT NULL,
      content TEXT,
      document_type VARCHAR(50),
      uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
  "

# Insert test data
docker-compose -f docker-compose.test-vm.yml exec postgres-test \
  psql -U horme_test -d horme_test -c "
    INSERT INTO test_products (name, description, price, category) VALUES
    ('Test Product 1', 'Description for test product 1', 99.99, 'Category A'),
    ('Test Product 2', 'Description for test product 2', 149.99, 'Category B'),
    ('Test Product 3', 'Description for test product 3', 199.99, 'Category A');

    INSERT INTO test_quotations (product_id, quantity, unit_price, total_amount) VALUES
    (1, 10, 99.99, 999.90),
    (2, 5, 149.99, 749.95),
    (3, 2, 199.99, 399.98);

    INSERT INTO test_documents (title, content, document_type) VALUES
    ('Test Document 1', 'Sample content for testing', 'pdf'),
    ('Test Document 2', 'Another test document content', 'docx'),
    ('Test RFP Document', 'Request for Proposal test content', 'pdf');
  "

echo "✅ Test data setup complete!"
```

## Test Suites

### 1. Unit Tests (Tier 1)

#### API Unit Tests
```python
# tests/unit/test_api_endpoints.py
import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import Mock, patch
from src.api.main import app
from src.api.models import Product, Quotation

class TestAPIEndpoints:
    """Unit tests for API endpoints with mocked dependencies."""
    
    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @patch('src.api.services.ProductService.get_all')
    async def test_get_products_success(self, mock_get_all, client):
        """Test successful product retrieval."""
        # Arrange
        mock_products = [
            {"id": 1, "name": "Test Product", "price": 99.99},
            {"id": 2, "name": "Another Product", "price": 149.99}
        ]
        mock_get_all.return_value = mock_products
        
        # Act
        response = await client.get("/api/products")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_products
        mock_get_all.assert_called_once()
    
    @patch('src.api.services.QuotationService.create')
    async def test_create_quotation_success(self, mock_create, client):
        """Test successful quotation creation."""
        # Arrange
        quotation_data = {
            "product_id": 1,
            "quantity": 10,
            "unit_price": 99.99
        }
        mock_quotation = {"id": 1, **quotation_data, "total_amount": 999.90}
        mock_create.return_value = mock_quotation
        
        # Act
        response = await client.post("/api/quotations", json=quotation_data)
        
        # Assert
        assert response.status_code == 201
        assert response.json() == mock_quotation
        mock_create.assert_called_once_with(quotation_data)
    
    @patch('src.api.services.DocumentService.upload')
    async def test_document_upload_validation(self, mock_upload, client):
        """Test document upload with validation."""
        # Arrange
        mock_upload.side_effect = ValueError("Invalid file format")
        
        # Act
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", b"test content", "text/plain")}
        )
        
        # Assert
        assert response.status_code == 400
        assert "Invalid file format" in response.json()["detail"]

    async def test_health_check(self, client):
        """Test health check endpoint."""
        # Act
        response = await client.get("/health")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

#### MCP Server Unit Tests
```python
# tests/unit/test_mcp_server.py
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from src.mcp.server import MCPServer
from src.mcp.handlers import ProductHandler, QuotationHandler

class TestMCPServer:
    """Unit tests for MCP server functionality."""
    
    @pytest.fixture
    def server(self):
        return MCPServer()
    
    @pytest.fixture
    def mock_websocket(self):
        mock_ws = Mock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock()
        return mock_ws
    
    @patch('src.mcp.handlers.ProductHandler.get_products')
    async def test_handle_get_products(self, mock_get_products, server, mock_websocket):
        """Test MCP product retrieval handler."""
        # Arrange
        mock_products = [{"id": 1, "name": "Test Product"}]
        mock_get_products.return_value = mock_products
        
        message = {
            "id": "test-123",
            "method": "products/list",
            "params": {}
        }
        
        # Act
        await server.handle_message(mock_websocket, json.dumps(message))
        
        # Assert
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["id"] == "test-123"
        assert sent_message["result"] == mock_products
    
    async def test_handle_invalid_message(self, server, mock_websocket):
        """Test handling of invalid JSON message."""
        # Arrange
        invalid_json = "{ invalid json }"
        
        # Act
        await server.handle_message(mock_websocket, invalid_json)
        
        # Assert
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["error"]["code"] == -32700  # Parse error
    
    @patch('src.mcp.handlers.QuotationHandler.create_quotation')
    async def test_handle_create_quotation(self, mock_create, server, mock_websocket):
        """Test MCP quotation creation handler."""
        # Arrange
        quotation_data = {"product_id": 1, "quantity": 5}
        mock_quotation = {"id": 1, **quotation_data, "total_amount": 499.95}
        mock_create.return_value = mock_quotation
        
        message = {
            "id": "test-456",
            "method": "quotations/create",
            "params": quotation_data
        }
        
        # Act
        await server.handle_message(mock_websocket, json.dumps(message))
        
        # Assert
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["result"] == mock_quotation
```

### 2. Integration Tests (Tier 2)

#### Service Integration Tests
```python
# tests/integration/test_service_integration.py
import pytest
import asyncio
from httpx import AsyncClient
import docker
from testcontainers.postgres import PostgreSQLContainer
from testcontainers.redis import RedisContainer

class TestServiceIntegration:
    """Integration tests with real database and redis containers."""
    
    @pytest.fixture(scope="class")
    def postgres_container(self):
        with PostgreSQLContainer("postgres:15") as postgres:
            yield postgres
    
    @pytest.fixture(scope="class")
    def redis_container(self):
        with RedisContainer("redis:7") as redis:
            yield redis
    
    @pytest.fixture
    async def app_client(self, postgres_container, redis_container):
        # Set environment variables for test containers
        import os
        os.environ["DATABASE_URL"] = postgres_container.get_connection_url()
        os.environ["REDIS_URL"] = f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}"
        
        # Import app after setting environment variables
        from src.api.main import app
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    async def test_full_product_workflow(self, app_client):
        """Test complete product management workflow."""
        # Create product
        product_data = {
            "name": "Integration Test Product",
            "description": "Product for integration testing",
            "price": 299.99,
            "category": "Test Category"
        }
        
        response = await app_client.post("/api/products", json=product_data)
        assert response.status_code == 201
        product = response.json()
        product_id = product["id"]
        
        # Retrieve product
        response = await app_client.get(f"/api/products/{product_id}")
        assert response.status_code == 200
        retrieved_product = response.json()
        assert retrieved_product["name"] == product_data["name"]
        
        # Update product
        update_data = {"price": 249.99}
        response = await app_client.put(f"/api/products/{product_id}", json=update_data)
        assert response.status_code == 200
        updated_product = response.json()
        assert updated_product["price"] == 249.99
        
        # Delete product
        response = await app_client.delete(f"/api/products/{product_id}")
        assert response.status_code == 204
        
        # Verify deletion
        response = await app_client.get(f"/api/products/{product_id}")
        assert response.status_code == 404
    
    async def test_quotation_calculation_accuracy(self, app_client):
        """Test quotation calculation with database persistence."""
        # Create test product
        product_data = {
            "name": "Calculation Test Product",
            "price": 99.99,
            "category": "Test"
        }
        response = await app_client.post("/api/products", json=product_data)
        product_id = response.json()["id"]
        
        # Create quotation
        quotation_data = {
            "product_id": product_id,
            "quantity": 15,
            "unit_price": 99.99
        }
        
        response = await app_client.post("/api/quotations", json=quotation_data)
        assert response.status_code == 201
        quotation = response.json()
        
        # Verify calculation accuracy
        expected_total = 15 * 99.99  # 1499.85
        assert quotation["total_amount"] == expected_total
        assert quotation["quantity"] == 15
        assert quotation["unit_price"] == 99.99
    
    async def test_database_transaction_rollback(self, app_client):
        """Test database transaction rollback on error."""
        # This test should trigger a database constraint violation
        # and verify that partial changes are rolled back
        
        # Create valid product first
        product_data = {"name": "Valid Product", "price": 99.99}
        response = await app_client.post("/api/products", json=product_data)
        product_id = response.json()["id"]
        
        # Attempt batch operation that should fail partway through
        batch_data = {
            "quotations": [
                {"product_id": product_id, "quantity": 10, "unit_price": 99.99},
                {"product_id": 999999, "quantity": 5, "unit_price": 149.99},  # Invalid product_id
                {"product_id": product_id, "quantity": 3, "unit_price": 199.99}
            ]
        }
        
        response = await app_client.post("/api/quotations/batch", json=batch_data)
        assert response.status_code == 400  # Should fail due to invalid product_id
        
        # Verify no quotations were created (rollback occurred)
        response = await app_client.get("/api/quotations")
        quotations = response.json()
        # Filter quotations for this product to avoid interference from other tests
        product_quotations = [q for q in quotations if q["product_id"] == product_id]
        assert len(product_quotations) == 0
```

#### API-MCP Integration Tests
```python
# tests/integration/test_api_mcp_integration.py
import pytest
import asyncio
import websockets
import json
from httpx import AsyncClient

class TestAPIMCPIntegration:
    """Integration tests between API and MCP services."""
    
    @pytest.fixture
    async def api_client(self):
        # Assumes test environment is running
        async with AsyncClient(base_url="http://localhost:8000") as ac:
            yield ac
    
    @pytest.fixture
    async def mcp_client(self):
        uri = "ws://localhost:3002"
        async with websockets.connect(uri) as websocket:
            yield websocket
    
    async def test_product_sync_between_services(self, api_client, mcp_client):
        """Test that products created via API are accessible via MCP."""
        # Create product via API
        product_data = {
            "name": "Sync Test Product",
            "price": 199.99,
            "category": "Sync Test"
        }
        
        response = await api_client.post("/api/products", json=product_data)
        assert response.status_code == 201
        created_product = response.json()
        product_id = created_product["id"]
        
        # Retrieve product via MCP
        mcp_request = {
            "id": "sync-test-1",
            "method": "products/get",
            "params": {"id": product_id}
        }
        
        await mcp_client.send(json.dumps(mcp_request))
        response_str = await mcp_client.recv()
        mcp_response = json.loads(response_str)
        
        assert mcp_response["id"] == "sync-test-1"
        assert mcp_response["result"]["id"] == product_id
        assert mcp_response["result"]["name"] == product_data["name"]
    
    async def test_real_time_quotation_updates(self, api_client, mcp_client):
        """Test real-time quotation updates via WebSocket."""
        # Subscribe to quotation updates via MCP
        subscribe_request = {
            "id": "subscribe-1",
            "method": "quotations/subscribe",
            "params": {}
        }
        
        await mcp_client.send(json.dumps(subscribe_request))
        subscribe_response = await mcp_client.recv()
        assert json.loads(subscribe_response)["result"]["subscribed"] is True
        
        # Create product first
        product_data = {"name": "Real-time Test Product", "price": 99.99}
        response = await api_client.post("/api/products", json=product_data)
        product_id = response.json()["id"]
        
        # Create quotation via API
        quotation_data = {
            "product_id": product_id,
            "quantity": 5,
            "unit_price": 99.99
        }
        
        response = await api_client.post("/api/quotations", json=quotation_data)
        assert response.status_code == 201
        
        # Wait for real-time update via MCP
        try:
            update_str = await asyncio.wait_for(mcp_client.recv(), timeout=5.0)
            update = json.loads(update_str)
            assert update["method"] == "quotations/updated"
            assert update["params"]["quotation"]["product_id"] == product_id
        except asyncio.TimeoutError:
            pytest.fail("Real-time update not received within 5 seconds")
```

### 3. System Tests (Tier 3)

#### End-to-End Workflow Tests
```python
# tests/system/test_e2e_workflows.py
import pytest
import time
import requests
import websockets
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestEndToEndWorkflows:
    """End-to-end system tests with real user workflows."""
    
    @pytest.fixture
    def chrome_driver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:3000"  # Assumes test environment running
    
    def test_complete_rfp_processing_workflow(self, chrome_driver, base_url):
        """Test complete RFP processing workflow."""
        driver = chrome_driver
        
        # 1. Navigate to application
        driver.get(base_url)
        assert "Horme POV" in driver.title
        
        # 2. Upload RFP document
        driver.find_element(By.ID, "upload-button").click()
        file_input = driver.find_element(By.ID, "file-input")
        file_input.send_keys("/app/tests/data/sample_rfp.pdf")
        
        driver.find_element(By.ID, "submit-upload").click()
        
        # 3. Wait for processing completion
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "processing-complete"))
        )
        
        # 4. Verify extracted information
        extracted_text = driver.find_element(By.ID, "extracted-content").text
        assert "Request for Proposal" in extracted_text
        
        # 5. Generate quotation
        driver.find_element(By.ID, "generate-quotation").click()
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "quotation-result"))
        )
        
        # 6. Verify quotation generation
        quotation_section = driver.find_element(By.ID, "quotation-result")
        assert quotation_section.is_displayed()
        
        # 7. Export quotation
        driver.find_element(By.ID, "export-pdf").click()
        
        # Wait for download to complete (simplified check)
        time.sleep(3)
    
    def test_supplier_discovery_workflow(self, chrome_driver, base_url):
        """Test supplier discovery and matching workflow."""
        driver = chrome_driver
        
        # 1. Navigate to supplier discovery
        driver.get(f"{base_url}/suppliers")
        
        # 2. Enter product search criteria
        search_input = driver.find_element(By.ID, "product-search")
        search_input.send_keys("Industrial Pump")
        
        driver.find_element(By.ID, "search-suppliers").click()
        
        # 3. Wait for search results
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "supplier-result"))
        )
        
        # 4. Verify supplier results
        supplier_results = driver.find_elements(By.CLASS_NAME, "supplier-result")
        assert len(supplier_results) > 0
        
        # 5. Select supplier and view details
        supplier_results[0].click()
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "supplier-details"))
        )
        
        # 6. Verify supplier information display
        supplier_details = driver.find_element(By.ID, "supplier-details")
        assert supplier_details.is_displayed()
        
        # 7. Request quote from supplier
        driver.find_element(By.ID, "request-quote").click()
        
        # 8. Fill quote request form
        quantity_input = driver.find_element(By.ID, "quantity")
        quantity_input.send_keys("100")
        
        specifications = driver.find_element(By.ID, "specifications")
        specifications.send_keys("Industrial grade pump for water treatment")
        
        driver.find_element(By.ID, "submit-quote-request").click()
        
        # 9. Verify quote request submission
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "quote-request-success"))
        )
    
    async def test_real_time_collaboration_workflow(self):
        """Test real-time collaboration features."""
        # This test requires multiple WebSocket connections
        
        # Connection 1: User A
        uri = "ws://localhost:3002"
        async with websockets.connect(uri) as user_a:
            # Connection 2: User B
            async with websockets.connect(uri) as user_b:
                
                # User A joins collaboration session
                join_request_a = {
                    "id": "join-a",
                    "method": "collaboration/join",
                    "params": {"session_id": "test-session", "user_id": "user_a"}
                }
                await user_a.send(json.dumps(join_request_a))
                response_a = await user_a.recv()
                assert json.loads(response_a)["result"]["joined"] is True
                
                # User B joins same session
                join_request_b = {
                    "id": "join-b",
                    "method": "collaboration/join",
                    "params": {"session_id": "test-session", "user_id": "user_b"}
                }
                await user_b.send(json.dumps(join_request_b))
                response_b = await user_b.recv()
                assert json.loads(response_b)["result"]["joined"] is True
                
                # User A should receive notification of User B joining
                notification = await user_a.recv()
                notification_data = json.loads(notification)
                assert notification_data["method"] == "collaboration/user_joined"
                assert notification_data["params"]["user_id"] == "user_b"
                
                # User A shares document
                share_request = {
                    "id": "share-doc",
                    "method": "collaboration/share_document",
                    "params": {
                        "session_id": "test-session",
                        "document_id": "doc-123",
                        "action": "share"
                    }
                }
                await user_a.send(json.dumps(share_request))
                
                # User B should receive document share notification
                share_notification = await user_b.recv()
                share_data = json.loads(share_notification)
                assert share_data["method"] == "collaboration/document_shared"
                assert share_data["params"]["document_id"] == "doc-123"
```

### 4. Security Tests

#### Security Validation Tests
```python
# tests/security/test_security_validation.py
import pytest
import requests
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class TestSecurityValidation:
    """Security-focused tests for VM deployment."""
    
    @pytest.fixture
    def base_url(self):
        return "https://localhost"  # Assumes SSL-enabled test environment
    
    def test_ssl_certificate_validation(self, base_url):
        """Test SSL certificate configuration."""
        response = requests.get(base_url, verify=True)
        assert response.status_code == 200
        
        # Verify SSL headers
        assert response.headers.get('Strict-Transport-Security') is not None
        assert 'max-age=' in response.headers.get('Strict-Transport-Security', '')
    
    def test_security_headers_validation(self, base_url):
        """Test security headers are properly set."""
        response = requests.get(base_url)
        
        # Required security headers
        security_headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': 'default-src'
        }
        
        for header, expected_value in security_headers.items():
            actual_value = response.headers.get(header, '')
            assert expected_value in actual_value, f"Missing or incorrect {header}"
    
    def test_rate_limiting(self, base_url):
        """Test rate limiting is properly configured."""
        # Make rapid requests to trigger rate limiting
        responses = []
        for i in range(20):
            try:
                response = requests.get(f"{base_url}/api/health", timeout=1)
                responses.append(response.status_code)
            except requests.exceptions.RequestException:
                responses.append(None)
            time.sleep(0.1)  # 100ms between requests
        
        # Should eventually get rate limited (429 status)
        assert 429 in responses, "Rate limiting not working properly"
    
    def test_sql_injection_protection(self, base_url):
        """Test SQL injection protection."""
        # Attempt SQL injection on various endpoints
        injection_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE products; --",
            "1' UNION SELECT * FROM products --",
            "admin'--",
            "' OR 1=1 --"
        ]
        
        for payload in injection_payloads:
            # Test product search endpoint
            response = requests.get(
                f"{base_url}/api/products/search",
                params={"q": payload}
            )
            # Should not return server error or suspicious results
            assert response.status_code != 500
            
            # Test quotation creation
            response = requests.post(
                f"{base_url}/api/quotations",
                json={"product_id": payload, "quantity": 1}
            )
            # Should return validation error, not server error
            assert response.status_code in [400, 422]  # Client error, not server error
    
    def test_xss_protection(self):
        """Test XSS protection in frontend."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=options)
        
        try:
            driver.get("https://localhost:3000")
            
            # Attempt XSS injection in form fields
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "<svg onload=alert('XSS')>"
            ]
            
            for payload in xss_payloads:
                # Find search input (if exists)
                search_inputs = driver.find_elements_by_css_selector("input[type='text']")
                if search_inputs:
                    search_inputs[0].clear()
                    search_inputs[0].send_keys(payload)
                    
                    # Submit form
                    submit_buttons = driver.find_elements_by_css_selector("button[type='submit']")
                    if submit_buttons:
                        submit_buttons[0].click()
                        
                    # Check that script didn't execute (no alert)
                    # In a real test, you might check for absence of alert dialogs
                    time.sleep(1)
                    
                    # Verify payload is properly escaped in output
                    page_source = driver.page_source
                    assert payload not in page_source or "&lt;" in page_source
        finally:
            driver.quit()
    
    def test_container_security_configuration(self):
        """Test container security configurations."""
        # Check container user (should not be root)
        result = subprocess.run([
            "docker", "exec", "horme-api", "whoami"
        ], capture_output=True, text=True)
        assert result.stdout.strip() != "root"
        
        # Check container capabilities
        result = subprocess.run([
            "docker", "inspect", "horme-api", "--format", "{{.HostConfig.CapDrop}}"
        ], capture_output=True, text=True)
        assert "ALL" in result.stdout
        
        # Check read-only filesystem
        result = subprocess.run([
            "docker", "inspect", "horme-api", "--format", "{{.HostConfig.ReadonlyRootfs}}"
        ], capture_output=True, text=True)
        assert result.stdout.strip() == "true"
    
    def test_network_isolation(self):
        """Test network isolation between containers."""
        # Test that database is not accessible from outside the network
        result = subprocess.run([
            "docker", "exec", "horme-api", "nc", "-z", "postgres", "5432"
        ], capture_output=True)
        assert result.returncode == 0  # Should be accessible from API container
        
        # Test that direct access to database port is blocked
        try:
            response = requests.get("http://localhost:5432", timeout=5)
            pytest.fail("Database should not be directly accessible")
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass  # Expected - database should not be directly accessible
```

### 5. Performance Tests

#### Performance Baseline Tests
```python
# tests/performance/test_performance_baseline.py
import pytest
import time
import asyncio
import aiohttp
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

class TestPerformanceBaseline:
    """Performance tests to establish and validate baselines."""
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"
    
    async def test_api_response_time_baseline(self, base_url):
        """Test API response time meets baseline requirements."""
        response_times = []
        
        async with aiohttp.ClientSession() as session:
            # Warm up
            for _ in range(5):
                async with session.get(f"{base_url}/api/health") as response:
                    await response.read()
            
            # Measure response times
            for _ in range(50):
                start_time = time.time()
                async with session.get(f"{base_url}/api/health") as response:
                    await response.read()
                    assert response.status == 200
                end_time = time.time()
                response_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        # Validate baseline requirements
        avg_response_time = statistics.mean(response_times)
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]
        
        assert avg_response_time < 100, f"Average response time {avg_response_time:.2f}ms exceeds 100ms"
        assert p95_response_time < 200, f"95th percentile {p95_response_time:.2f}ms exceeds 200ms"
    
    async def test_concurrent_request_handling(self, base_url):
        """Test system handles concurrent requests within performance limits."""
        concurrent_users = 10
        requests_per_user = 20
        
        async def user_session(session_id):
            response_times = []
            async with aiohttp.ClientSession() as session:
                for _ in range(requests_per_user):
                    start_time = time.time()
                    async with session.get(f"{base_url}/api/products") as response:
                        await response.read()
                        assert response.status == 200
                    end_time = time.time()
                    response_times.append((end_time - start_time) * 1000)
            return response_times
        
        # Execute concurrent sessions
        tasks = [user_session(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks)
        
        # Analyze performance under load
        all_response_times = [rt for session_times in results for rt in session_times]
        avg_response_time = statistics.mean(all_response_times)
        p95_response_time = sorted(all_response_times)[int(0.95 * len(all_response_times))]
        
        # Performance should degrade gracefully under load
        assert avg_response_time < 500, f"Average response time under load {avg_response_time:.2f}ms too high"
        assert p95_response_time < 1000, f"95th percentile under load {p95_response_time:.2f}ms too high"
    
    def test_resource_usage_baseline(self):
        """Test resource usage stays within acceptable limits."""
        # Monitor system resources during normal operation
        initial_memory = psutil.virtual_memory().percent
        initial_cpu = psutil.cpu_percent(interval=1)
        
        # Generate some load
        import requests
        for _ in range(100):
            requests.get("http://localhost:8000/api/health")
        
        # Check resource usage after load
        final_memory = psutil.virtual_memory().percent
        final_cpu = psutil.cpu_percent(interval=1)
        
        # Memory usage should not increase dramatically
        memory_increase = final_memory - initial_memory
        assert memory_increase < 20, f"Memory usage increased by {memory_increase:.1f}%"
        
        # CPU usage should return to reasonable levels
        assert final_cpu < 80, f"CPU usage {final_cpu:.1f}% too high after load"
    
    def test_database_query_performance(self, base_url):
        """Test database query performance meets requirements."""
        import requests
        
        # Test product search performance (complex query)
        search_times = []
        for i in range(20):
            start_time = time.time()
            response = requests.get(f"{base_url}/api/products/search?q=test+product")
            end_time = time.time()
            
            assert response.status_code == 200
            search_times.append((end_time - start_time) * 1000)
        
        avg_search_time = statistics.mean(search_times)
        assert avg_search_time < 300, f"Average search time {avg_search_time:.2f}ms too slow"
        
        # Test quotation creation performance (write operation)
        creation_times = []
        for i in range(10):
            start_time = time.time()
            response = requests.post(f"{base_url}/api/quotations", json={
                "product_id": 1,
                "quantity": 5,
                "unit_price": 99.99
            })
            end_time = time.time()
            
            if response.status_code == 201:  # Only count successful creations
                creation_times.append((end_time - start_time) * 1000)
        
        if creation_times:  # Only test if we had successful creations
            avg_creation_time = statistics.mean(creation_times)
            assert avg_creation_time < 500, f"Average creation time {avg_creation_time:.2f}ms too slow"
```

### 6. Operational Tests

#### Deployment and Recovery Tests
```python
# tests/operational/test_deployment_recovery.py
import pytest
import subprocess
import time
import requests
import docker

class TestDeploymentRecovery:
    """Tests for deployment procedures and disaster recovery."""
    
    @pytest.fixture
    def docker_client(self):
        return docker.from_env()
    
    def test_health_check_validation(self):
        """Test comprehensive health check script."""
        result = subprocess.run([
            "./scripts/validate-vm-deployment.sh"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Health check failed: {result.stderr}"
        assert "All services healthy" in result.stdout
    
    def test_database_backup_procedure(self):
        """Test database backup creation and validation."""
        # Run backup script
        result = subprocess.run([
            "./scripts/backup-database.sh"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Backup failed: {result.stderr}"
        
        # Verify backup file was created
        backup_list = subprocess.run([
            "find", "/opt/horme-pov/backups", "-name", "*.sql.gz", "-mtime", "-1"
        ], capture_output=True, text=True)
        
        assert backup_list.stdout.strip(), "No recent backup file found"
    
    def test_service_restart_recovery(self, docker_client):
        """Test service recovery after restart."""
        # Stop API service
        api_container = docker_client.containers.get("horme-api")
        api_container.stop()
        
        # Verify service is down
        time.sleep(5)
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            pytest.fail("Service should be down")
        except requests.exceptions.RequestException:
            pass  # Expected
        
        # Restart service
        api_container.start()
        
        # Wait for service to be ready
        for _ in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        else:
            pytest.fail("Service did not recover within 30 seconds")
        
        # Verify service functionality
        response = requests.get("http://localhost:8000/api/products")
        assert response.status_code == 200
    
    def test_database_connection_recovery(self, docker_client):
        """Test application recovery after database restart."""
        # Stop database
        db_container = docker_client.containers.get("horme-postgres")
        db_container.stop()
        
        # Verify API handles database unavailability gracefully
        time.sleep(5)
        response = requests.get("http://localhost:8000/api/products")
        assert response.status_code in [503, 500]  # Service unavailable or server error
        
        # Restart database
        db_container.start()
        
        # Wait for database to be ready
        for _ in range(60):  # Wait up to 60 seconds for database
            try:
                result = subprocess.run([
                    "docker", "exec", "horme-postgres", "pg_isready",
                    "-U", "horme_user", "-d", "horme_db"
                ], capture_output=True, timeout=5)
                if result.returncode == 0:
                    break
            except subprocess.TimeoutExpired:
                pass
            time.sleep(1)
        else:
            pytest.fail("Database did not recover within 60 seconds")
        
        # Verify application recovers
        for _ in range(30):  # Wait up to 30 seconds for app recovery
            try:
                response = requests.get("http://localhost:8000/api/products")
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        else:
            pytest.fail("Application did not recover database connection")
    
    def test_disaster_recovery_procedure(self):
        """Test complete disaster recovery procedure."""
        # Create test data first
        test_product = {
            "name": "Disaster Recovery Test Product",
            "price": 999.99,
            "category": "Test"
        }
        response = requests.post("http://localhost:8000/api/products", json=test_product)
        assert response.status_code == 201
        test_product_id = response.json()["id"]
        
        # Create backup
        backup_result = subprocess.run([
            "./scripts/backup-database.sh"
        ], capture_output=True, text=True)
        assert backup_result.returncode == 0
        
        # Simulate disaster by deleting test data
        response = requests.delete(f"http://localhost:8000/api/products/{test_product_id}")
        assert response.status_code == 204
        
        # Verify data is gone
        response = requests.get(f"http://localhost:8000/api/products/{test_product_id}")
        assert response.status_code == 404
        
        # Run disaster recovery
        recovery_result = subprocess.run([
            "./scripts/disaster-recovery.sh"
        ], capture_output=True, text=True)
        assert recovery_result.returncode == 0
        
        # Verify data is restored
        time.sleep(10)  # Allow time for services to fully restart
        response = requests.get(f"http://localhost:8000/api/products/{test_product_id}")
        assert response.status_code == 200
        restored_product = response.json()
        assert restored_product["name"] == test_product["name"]
```

## Test Execution Procedures

### Continuous Integration Pipeline

```yaml
# .github/workflows/vm-testing.yml
name: VM Testing Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Build test environment
        run: |
          docker-compose -f docker-compose.test-vm.yml build
      - name: Run integration tests
        run: |
          docker-compose -f docker-compose.test-vm.yml up -d
          sleep 30
          pytest tests/integration/ -v
      - name: Cleanup
        run: |
          docker-compose -f docker-compose.test-vm.yml down -v

  system-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up VM-like environment
        run: |
          sudo apt-get update
          sudo apt-get install -y docker-compose
      - name: Deploy full stack
        run: |
          ./deploy-vm-production.sh
          sleep 60
      - name: Run system tests
        run: |
          pytest tests/system/ -v --maxfail=5
      - name: Run security tests
        run: |
          pytest tests/security/ -v
      - name: Run performance tests
        run: |
          pytest tests/performance/ -v
      - name: Cleanup
        run: |
          docker-compose -f docker-compose.vm-production.yml down -v
```

### Local Test Execution

```bash
#!/bin/bash
# scripts/run-all-tests.sh

set -e

echo "🧪 Running comprehensive test suite..."

# Setup test environment
echo "Setting up test environment..."
docker-compose -f docker-compose.test-vm.yml up -d
sleep 30

# Run tests by tier
echo "Running Tier 1: Unit Tests..."
pytest tests/unit/ -v --cov=src --cov-report=term-missing

echo "Running Tier 2: Integration Tests..."
pytest tests/integration/ -v

echo "Running Tier 3: System Tests..."
# Deploy production-like environment for system tests
./deploy-vm-production.sh
sleep 60

pytest tests/system/ -v
pytest tests/security/ -v
pytest tests/performance/ -v --benchmark-only
pytest tests/operational/ -v

# Cleanup
echo "Cleaning up test environment..."
docker-compose -f docker-compose.test-vm.yml down -v
docker-compose -f docker-compose.vm-production.yml down -v

echo "✅ All tests completed!"
```

### Test Reporting

```python
# tests/conftest.py
import pytest
import json
import time
from datetime import datetime

@pytest.fixture(scope="session", autouse=True)
def test_report():
    """Generate comprehensive test report."""
    start_time = time.time()
    
    yield
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Generate test report
    report = {
        "test_run": {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "environment": "VM Test Environment"
        },
        "coverage": "Generated by pytest-cov",
        "performance_metrics": "Generated by pytest-benchmark"
    }
    
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=2)
```

## Conclusion

This comprehensive testing strategy ensures the Horme POV platform maintains high quality, security, and performance standards in VM production environments. The multi-tier approach provides confidence in system reliability while the automated execution enables continuous validation throughout the development lifecycle.

Regular execution of this test suite, combined with proper monitoring and alerting, provides a robust foundation for maintaining production system health and performance.