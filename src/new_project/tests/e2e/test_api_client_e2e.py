"""
E2E Tests for NextJS API Client
==============================

Tier 3 end-to-end tests focusing on:
- Complete user workflows from login to business operations
- Real frontend-backend integration scenarios
- Authentication persistence across multiple operations
- Real-time features and notifications
- Complete business processes

NO MOCKING - Tests complete scenarios with full infrastructure stack
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
import concurrent.futures

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
def test_company_data():
    """Test company for E2E scenarios"""
    return {
        "name": "E2E Test Company",
        "industry": "Technology",
        "address": "123 Test Street, Test City, TC 12345"
    }


@pytest.fixture(scope="module")
def test_user_data():
    """Test user for E2E scenarios"""
    return {
        "email": "e2e_test@test.com",
        "password": "e2e_test123",
        "first_name": "E2E",
        "last_name": "TestUser",
        "role": "sales_rep"
    }


@pytest.fixture(scope="module")
def ensure_full_infrastructure(nexus_server_url):
    """Ensure complete infrastructure is running"""
    services_to_check = [
        ("Nexus API", f"{nexus_server_url}/health"),
        ("Database", f"{nexus_server_url}/api/health/database"),
        ("WebSocket", f"{nexus_server_url.replace('http', 'ws')}/ws/health?token=test")
    ]
    
    for service_name, url in services_to_check:
        max_attempts = 15
        for attempt in range(max_attempts):
            try:
                if service_name == "WebSocket":
                    # Special handling for WebSocket health check
                    continue  # Skip WebSocket health check for now
                else:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        print(f"✅ {service_name} is running")
                        break
            except requests.exceptions.RequestException:
                if attempt < max_attempts - 1:
                    print(f"⏳ Waiting for {service_name}... (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(3)
                else:
                    pytest.skip(f"❌ {service_name} not available")
    
    return True


@pytest.fixture
def api_client(ensure_full_infrastructure, nexus_server_url):
    """API client configured for E2E testing"""
    from fe_api_client import APIClient
    
    config = {
        "base_url": nexus_server_url,
        "timeout": 30,  # Longer timeout for E2E tests
        "max_retries": 3
    }
    return APIClient(config)


@pytest.fixture
def e2e_test_session(api_client, test_user_data, test_company_data):
    """Complete test session with authenticated user"""
    # Create company first
    try:
        company_response = api_client.post("/api/admin/companies", test_company_data)
        company_id = company_response["id"]
    except Exception:
        # Company might already exist, get it
        companies = api_client.get("/api/companies")
        company_id = companies[0]["id"] if companies else 1
    
    # Create test user
    try:
        import subprocess
        result = subprocess.run([
            "python", "-m", "nexus_app", "create-user",
            "--email", test_user_data["email"],
            "--first-name", test_user_data["first_name"],
            "--last-name", test_user_data["last_name"],
            "--role", test_user_data["role"],
            "--company-id", str(company_id)
        ], capture_output=True, text=True, cwd=str(src_dir))
    except Exception as e:
        print(f"Note: User creation failed (user may already exist): {e}")
    
    # Authenticate user
    login_response = api_client.login({
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    
    api_client.set_auth_token(login_response["access_token"])
    
    return {
        "api_client": api_client,
        "user": login_response["user"],
        "company_id": company_id,
        "token": login_response["access_token"]
    }


@pytest.mark.e2e
@pytest.mark.requires_docker
class TestCompleteUserWorkflows:
    """Test complete user workflows from start to finish"""
    
    def test_complete_login_to_dashboard_workflow(self, e2e_test_session):
        """Test complete workflow: Login → Dashboard → Profile → Settings"""
        session = e2e_test_session
        client = session["api_client"]
        
        # Step 1: Verify authentication worked
        assert session["user"]["email"] == "e2e_test@test.com"
        assert session["token"] is not None
        
        # Step 2: Access dashboard data
        dashboard_response = client.get("/api/dashboard")
        assert "metrics" in dashboard_response
        assert "recent_activity" in dashboard_response
        
        # Step 3: Get user profile
        profile_response = client.get("/api/user/profile")
        assert profile_response["user"]["email"] == session["user"]["email"]
        
        # Step 4: Update user preferences
        preferences = {
            "notifications": True,
            "theme": "dark",
            "language": "en"
        }
        
        update_response = client.put("/api/user/preferences", preferences)
        assert update_response["preferences"]["theme"] == "dark"
        
        # Step 5: Verify preferences persisted
        updated_profile = client.get("/api/user/profile")
        assert updated_profile["preferences"]["theme"] == "dark"
    
    def test_complete_customer_management_workflow(self, e2e_test_session):
        """Test complete workflow: Create Customer → Update → Quote → Invoice"""
        client = e2e_test_session["api_client"]
        
        # Step 1: Create new customer
        customer_data = {
            "name": "E2E Test Customer Inc.",
            "type": "enterprise",
            "industry": "Manufacturing",
            "primary_contact": "John E2E TestContact",
            "email": "contact@e2etestcustomer.com",
            "phone": "+1-555-0123",
            "billing_address": "456 Customer Ave, Customer City, CC 67890"
        }
        
        create_response = client.post("/api/customers", customer_data)
        customer_id = create_response["customer_id"]
        assert customer_id is not None
        
        # Step 2: Retrieve customer details
        customer_details = client.get(f"/api/customers/{customer_id}")
        assert customer_details["name"] == customer_data["name"]
        assert customer_details["email"] == customer_data["email"]
        
        # Step 3: Update customer information
        update_data = {
            "phone": "+1-555-9999",
            "industry": "Technology"
        }
        
        update_response = client.put(f"/api/customers/{customer_id}", update_data)
        assert update_response["success"] is True
        
        # Step 4: Create quote for customer
        quote_data = {
            "customer_id": customer_id,
            "title": "E2E Test Quote",
            "description": "Complete E2E testing quote",
            "line_items": [
                {
                    "product_name": "Test Product A",
                    "quantity": 5,
                    "unit_price": 100.00,
                    "discount_percent": 10
                },
                {
                    "product_name": "Test Product B", 
                    "quantity": 2,
                    "unit_price": 250.00,
                    "discount_percent": 5
                }
            ]
        }
        
        quote_response = client.post("/api/quotes", quote_data)
        quote_id = quote_response["quote_id"]
        assert quote_id is not None
        assert "quote_number" in quote_response
        
        # Step 5: Retrieve quote details
        quote_details = client.get(f"/api/quotes/{quote_id}")
        assert quote_details["customer_id"] == customer_id
        assert quote_details["title"] == quote_data["title"]
        assert len(quote_details["line_items"]) == 2
        
        # Step 6: List customer's quotes
        customer_quotes = client.get(f"/api/customers/{customer_id}/quotes")
        assert len(customer_quotes) >= 1
        assert any(q["id"] == quote_id for q in customer_quotes)
    
    def test_complete_document_processing_workflow(self, e2e_test_session):
        """Test complete workflow: Upload Document → AI Processing → Results → Download"""
        client = e2e_test_session["api_client"]
        
        # Step 1: Create a test RFP document
        rfp_content = """
        REQUEST FOR PROPOSAL
        
        Company: E2E Test Customer Inc.
        Project: Enterprise Software Solution
        
        Requirements:
        - Customer relationship management system
        - Integration with existing ERP
        - Multi-user support with role-based access
        - Real-time reporting and analytics
        - Mobile application support
        
        Budget Range: $100,000 - $250,000
        Timeline: 6 months
        Contact: procurement@e2etestcustomer.com
        """
        
        with tempfile.NamedTemporaryFile(suffix=".txt", mode='w', delete=False) as f:
            f.write(rfp_content)
            f.flush()
            
            # Step 2: Upload document
            with open(f.name, 'rb') as upload_file:
                files = {"file": ("test_rfp.txt", upload_file, "text/plain")}
                upload_data = {
                    "document_type": "RFP",
                    "category": "inbound"
                }
                
                upload_response = client.upload_file(files, upload_data)
                document_id = upload_response["document_id"]
                assert document_id is not None
        
        # Cleanup temp file
        Path(f.name).unlink(missing_ok=True)
        
        # Step 3: Wait for AI processing to complete
        max_wait = 30  # 30 seconds
        processing_complete = False
        
        for _ in range(max_wait):
            doc_status = client.get(f"/api/documents/{document_id}")
            if doc_status["ai_status"] == "completed":
                processing_complete = True
                break
            elif doc_status["ai_status"] == "failed":
                pytest.fail("Document processing failed")
            time.sleep(1)
        
        assert processing_complete, "Document processing did not complete within timeout"
        
        # Step 4: Retrieve AI extraction results
        document_details = client.get(f"/api/documents/{document_id}")
        assert document_details["ai_status"] == "completed"
        assert document_details["ai_extracted_data"] is not None
        
        extracted_data = json.loads(document_details["ai_extracted_data"])
        assert "document_type" in extracted_data
        assert extracted_data["document_type"] == "RFP"
        assert "budget_range" in extracted_data
        assert "timeline" in extracted_data
        
        # Step 5: Download processed document
        download_response = client.get(f"/api/documents/{document_id}/download")
        assert download_response is not None
        
        # Step 6: List all documents
        documents_list = client.get("/api/documents")
        assert len(documents_list) >= 1
        assert any(doc["id"] == document_id for doc in documents_list)


@pytest.mark.e2e
@pytest.mark.requires_docker
class TestRealTimeIntegration:
    """Test real-time features and WebSocket integration"""
    
    @pytest.mark.asyncio
    async def test_complete_realtime_notification_workflow(self, e2e_test_session):
        """Test complete real-time notification workflow"""
        session = e2e_test_session
        token = session["token"]
        client_id = f"e2e_test_{int(time.time())}"
        
        ws_url = "ws://localhost:8000"
        ws_endpoint = f"{ws_url}/ws/{client_id}?token={token}"
        
        async with websockets.connect(ws_endpoint) as websocket:
            # Step 1: Receive welcome message
            welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            welcome_data = json.loads(welcome_msg)
            assert welcome_data["type"] == "welcome"
            
            # Step 2: Simulate document upload that triggers notification
            # This would be done via HTTP API while WebSocket is connected
            upload_task = asyncio.create_task(self._simulate_document_upload(session))
            
            # Step 3: Wait for real-time notification about upload
            notification_received = False
            for _ in range(15):  # Wait up to 15 seconds
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(msg)
                    
                    if data.get("type") == "document_uploaded":
                        notification_received = True
                        assert "document_id" in data
                        assert "message" in data
                        break
                except asyncio.TimeoutError:
                    continue
            
            # Wait for upload task to complete
            await upload_task
            
            assert notification_received, "Did not receive real-time notification"
    
    async def _simulate_document_upload(self, session):
        """Helper to simulate document upload during WebSocket test"""
        await asyncio.sleep(2)  # Wait a bit before uploading
        
        client = session["api_client"]
        
        # Create and upload a simple document
        with tempfile.NamedTemporaryFile(suffix=".txt", mode='w') as f:
            f.write("Real-time notification test document")
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                files = {"file": ("notification_test.txt", upload_file, "text/plain")}
                upload_data = {"document_type": "test"}
                
                return client.upload_file(files, upload_data)
    
    @pytest.mark.asyncio
    async def test_complete_realtime_chat_workflow(self, e2e_test_session):
        """Test complete real-time chat interaction workflow"""
        session = e2e_test_session
        token = session["token"]
        client_id = f"e2e_chat_{int(time.time())}"
        
        ws_url = "ws://localhost:8000"
        ws_endpoint = f"{ws_url}/ws/{client_id}?token={token}"
        
        async with websockets.connect(ws_endpoint) as websocket:
            # Step 1: Receive welcome message
            await asyncio.wait_for(websocket.recv(), timeout=10.0)
            
            # Step 2: Send multiple chat messages
            chat_messages = [
                "Hello, I need help with a quote",
                "Can you find products for manufacturing automation?",
                "What's the status of quote Q20240802001?"
            ]
            
            responses = []
            
            for message in chat_messages:
                # Send message
                chat_msg = {
                    "type": "chat_message",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(chat_msg))
                
                # Receive response
                response_msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response_msg)
                
                assert response_data["type"] == "chat_response"
                assert message in response_data["message"]
                responses.append(response_data)
            
            assert len(responses) == len(chat_messages)
            
            # Step 3: Send quote request via chat
            quote_request = {
                "type": "quote_request",
                "customer_id": 1,
                "products": ["Industrial Robot", "Control System"],
                "message": "Generate quote for automation equipment"
            }
            
            await websocket.send(json.dumps(quote_request))
            
            # Should receive processing message
            processing_msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            processing_data = json.loads(processing_msg)
            assert processing_data["type"] == "quote_processing"
            
            # Should receive completion message
            completion_msg = await asyncio.wait_for(websocket.recv(), timeout=15.0)
            completion_data = json.loads(completion_msg)
            assert completion_data["type"] == "quote_ready"
            assert "quote_id" in completion_data


@pytest.mark.e2e
@pytest.mark.requires_docker
class TestAuthenticationPersistence:
    """Test authentication persistence across multiple operations"""
    
    def test_token_persistence_across_page_refreshes(self, e2e_test_session):
        """Test token persistence simulating page refreshes"""
        session = e2e_test_session
        original_token = session["token"]
        
        # Simulate page refresh by creating new client instance
        from fe_api_client import APIClient
        
        new_client = APIClient({"base_url": "http://localhost:8000"})
        
        # Simulate loading token from localStorage/sessionStorage
        new_client.set_auth_token(original_token)
        
        # Should be able to access protected resources
        profile = new_client.get("/api/user/profile")
        assert profile["user"]["email"] == session["user"]["email"]
        
        # Should be able to perform authenticated operations
        dashboard = new_client.get("/api/dashboard")
        assert "metrics" in dashboard
    
    def test_token_refresh_during_long_session(self, e2e_test_session):
        """Test token refresh during extended usage session"""
        client = e2e_test_session["api_client"]
        original_token = client.get_auth_token()
        
        # Simulate extended session with multiple operations
        operations = [
            lambda: client.get("/api/dashboard"),
            lambda: client.get("/api/customers"),
            lambda: client.get("/api/user/profile"),
            lambda: client.get("/api/documents"),
            lambda: client.get("/api/quotes")
        ]
        
        # Perform operations with delays to simulate real usage
        for i, operation in enumerate(operations):
            result = operation()
            assert result is not None
            
            # Check if token was refreshed during operations
            current_token = client.get_auth_token()
            if current_token != original_token:
                print(f"Token was refreshed during operation {i}")
                original_token = current_token
            
            time.sleep(1)  # Simulate user thinking time
        
        # Final verification that we're still authenticated
        final_profile = client.get("/api/user/profile")
        assert final_profile["user"]["email"] == e2e_test_session["user"]["email"]
    
    def test_concurrent_authenticated_requests(self, e2e_test_session):
        """Test handling concurrent requests with shared authentication"""
        client = e2e_test_session["api_client"]
        
        def make_authenticated_request(endpoint):
            return client.get(f"/api/{endpoint}")
        
        endpoints = [
            "dashboard", "user/profile", "customers", 
            "documents", "quotes", "dashboard"
        ]
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(make_authenticated_request, endpoint)
                for endpoint in endpoints
            ]
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=10)
                    results.append(result)
                except Exception as e:
                    pytest.fail(f"Concurrent request failed: {e}")
        
        # All requests should succeed
        assert len(results) == len(endpoints)
        
        # Token should still be valid after concurrent usage
        final_check = client.get("/api/user/profile")
        assert final_check["user"]["email"] == e2e_test_session["user"]["email"]


@pytest.mark.e2e
@pytest.mark.requires_docker  
class TestCompleteBusinessProcesses:
    """Test complete business processes end-to-end"""
    
    def test_complete_sales_process_end_to_end(self, e2e_test_session):
        """Test complete sales process: Lead → Customer → Quote → Order → Invoice"""
        client = e2e_test_session["api_client"]
        
        # Step 1: Create lead from RFP document
        rfp_content = """
        RFP: Manufacturing Automation System
        
        Company: Advanced Manufacturing Corp
        Budget: $150,000 - $200,000
        Timeline: 4 months
        Requirements: 
        - Robotic assembly line
        - Quality control systems
        - Production planning software
        Contact: procurement@advancedmfg.com
        """
        
        with tempfile.NamedTemporaryFile(suffix=".txt", mode='w', delete=False) as f:
            f.write(rfp_content)
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                files = {"file": ("advanced_mfg_rfp.txt", upload_file, "text/plain")}
                upload_data = {"document_type": "RFP"}
                
                document_response = client.upload_file(files, upload_data)
                document_id = document_response["document_id"]
        
        Path(f.name).unlink(missing_ok=True)
        
        # Step 2: Wait for AI processing and extract lead information
        for _ in range(30):
            doc_status = client.get(f"/api/documents/{document_id}")
            if doc_status["ai_status"] == "completed":
                break
            time.sleep(1)
        
        extracted_data = json.loads(doc_status["ai_extracted_data"])
        
        # Step 3: Convert lead to customer
        customer_data = {
            "name": "Advanced Manufacturing Corp",
            "type": "enterprise",
            "industry": "Manufacturing",
            "primary_contact": "Procurement Manager",
            "email": "procurement@advancedmfg.com",
            "phone": "+1-555-0199",
            "billing_address": "789 Manufacturing Blvd, Industrial City, IC 12345"
        }
        
        customer_response = client.post("/api/customers", customer_data)
        customer_id = customer_response["customer_id"]
        
        # Step 4: Create detailed quote based on requirements
        quote_data = {
            "customer_id": customer_id,
            "title": "Manufacturing Automation System Proposal",
            "description": "Complete automation solution for manufacturing operations",
            "line_items": [
                {
                    "product_name": "Robotic Assembly Line System",
                    "quantity": 1,
                    "unit_price": 85000.00,
                    "discount_percent": 5
                },
                {
                    "product_name": "Quality Control Vision System",
                    "quantity": 2,
                    "unit_price": 25000.00,
                    "discount_percent": 0
                },
                {
                    "product_name": "Production Planning Software Suite",
                    "quantity": 1,
                    "unit_price": 35000.00,
                    "discount_percent": 10
                },
                {
                    "product_name": "Installation and Training Services",
                    "quantity": 1,
                    "unit_price": 15000.00,
                    "discount_percent": 0
                }
            ]
        }
        
        quote_response = client.post("/api/quotes", quote_data)
        quote_id = quote_response["quote_id"]
        quote_number = quote_response["quote_number"]
        
        # Step 5: Retrieve complete quote details
        quote_details = client.get(f"/api/quotes/{quote_id}")
        
        # Verify quote totals
        expected_subtotal = (85000 * 0.95) + (25000 * 2) + (35000 * 0.90) + 15000
        assert abs(quote_details["total_amount"] - expected_subtotal) < 1.0
        
        # Step 6: Update quote status (simulate customer acceptance)
        status_update = {"status": "accepted", "notes": "Customer approved proposal"}
        client.put(f"/api/quotes/{quote_id}/status", status_update)
        
        # Step 7: Verify complete sales pipeline
        customer_summary = client.get(f"/api/customers/{customer_id}/summary")
        assert customer_summary["total_quotes"] >= 1
        assert customer_summary["total_quote_value"] >= expected_subtotal
        
        # Step 8: Generate sales report
        report_data = client.post("/api/reports/sales", {
            "start_date": datetime.now().strftime("%Y-%m-01"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "include_customers": [customer_id]
        })
        
        assert "total_revenue" in report_data
        assert "quotes_generated" in report_data
        assert report_data["quotes_generated"] >= 1
    
    def test_complete_support_process_integration(self, e2e_test_session):
        """Test complete customer support process integration"""
        client = e2e_test_session["api_client"]
        
        # Step 1: Create customer with existing quote
        customer_data = {
            "name": "Support Test Customer",
            "type": "small_business",
            "industry": "Retail",
            "primary_contact": "Support Manager",
            "email": "support@supporttest.com",
            "phone": "+1-555-0188"
        }
        
        customer_response = client.post("/api/customers", customer_data)
        customer_id = customer_response["customer_id"]
        
        # Step 2: Create support ticket via document upload
        support_content = """
        SUPPORT REQUEST
        
        Issue: Integration problems with ERP system
        Severity: High
        Description: Unable to sync product data between CRM and ERP
        Error Messages: Connection timeout, authentication failures
        Environment: Production
        Affected Users: All sales team (25 users)
        Business Impact: Cannot generate quotes or process orders
        """
        
        with tempfile.NamedTemporaryFile(suffix=".txt", mode='w', delete=False) as f:
            f.write(support_content)
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                files = {"file": ("support_request.txt", upload_file, "text/plain")}
                upload_data = {
                    "document_type": "support_request",
                    "customer_id": customer_id
                }
                
                ticket_response = client.upload_file(files, upload_data)
        
        Path(f.name).unlink(missing_ok=True)
        
        # Step 3: Process support ticket
        document_id = ticket_response["document_id"]
        
        # Wait for AI processing
        for _ in range(20):
            doc_status = client.get(f"/api/documents/{document_id}")
            if doc_status["ai_status"] == "completed":
                break
            time.sleep(1)
        
        # Step 4: Create follow-up quote for support services
        support_quote_data = {
            "customer_id": customer_id,
            "title": "ERP Integration Support Services",
            "description": "Emergency support for ERP system integration issues",
            "line_items": [
                {
                    "product_name": "Emergency Technical Support (8 hours)",
                    "quantity": 1,
                    "unit_price": 2000.00,
                    "discount_percent": 0
                },
                {
                    "product_name": "System Integration Audit",
                    "quantity": 1,
                    "unit_price": 1500.00,
                    "discount_percent": 0
                }
            ]
        }
        
        support_quote_response = client.post("/api/quotes", support_quote_data)
        support_quote_id = support_quote_response["quote_id"]
        
        # Step 5: Verify integrated support workflow
        customer_details = client.get(f"/api/customers/{customer_id}")
        customer_documents = client.get(f"/api/customers/{customer_id}/documents")
        customer_quotes = client.get(f"/api/customers/{customer_id}/quotes")
        
        assert len(customer_documents) >= 1
        assert len(customer_quotes) >= 1
        assert any(doc["type"] == "support_request" for doc in customer_documents)
        assert any(quote["title"].startswith("ERP Integration") for quote in customer_quotes)


@pytest.mark.e2e
@pytest.mark.requires_docker
class TestPerformanceAndScalability:
    """Test performance and scalability of complete system"""
    
    def test_high_volume_operations_performance(self, e2e_test_session, performance_monitor):
        """Test system performance under high volume operations"""
        client = e2e_test_session["api_client"]
        
        performance_monitor.start("high_volume_test")
        
        # Create multiple customers, quotes, and documents rapidly
        operations_completed = 0
        
        try:
            # Create 10 customers
            for i in range(10):
                customer_data = {
                    "name": f"Performance Test Customer {i}",
                    "type": "small_business",
                    "industry": "Technology",
                    "email": f"perf_test_{i}@test.com"
                }
                client.post("/api/customers", customer_data)
                operations_completed += 1
            
            # Create quotes for first 5 customers
            customers = client.get("/api/customers")[-5:]  # Get last 5 customers
            
            for customer in customers:
                quote_data = {
                    "customer_id": customer["id"],
                    "title": f"Performance Test Quote for {customer['name']}",
                    "description": "High volume testing quote",
                    "line_items": [
                        {
                            "product_name": "Test Product",
                            "quantity": 1,
                            "unit_price": 1000.00,
                            "discount_percent": 0
                        }
                    ]
                }
                client.post("/api/quotes", quote_data)
                operations_completed += 1
            
        except Exception as e:
            pytest.fail(f"High volume operations failed after {operations_completed} operations: {e}")
        
        performance_monitor.assert_within_threshold(30.0, "high_volume_test")  # <30 seconds
        assert operations_completed >= 15  # Should complete at least 15 operations
    
    def test_concurrent_user_simulation(self, api_client, performance_monitor):
        """Test system under concurrent user load"""
        performance_monitor.start("concurrent_users")
        
        def simulate_user_session(user_id):
            """Simulate a complete user session"""
            try:
                # Create user-specific client
                from fe_api_client import APIClient
                user_client = APIClient({"base_url": "http://localhost:8000"})
                
                # Login (using shared test credentials)
                login_response = user_client.login({
                    "email": "e2e_test@test.com",
                    "password": "e2e_test123"
                })
                user_client.set_auth_token(login_response["access_token"])
                
                # Perform typical user operations
                user_client.get("/api/dashboard")
                user_client.get("/api/customers")
                user_client.get("/api/user/profile")
                
                return f"User {user_id} completed successfully"
                
            except Exception as e:
                return f"User {user_id} failed: {str(e)}"
        
        # Simulate 5 concurrent users
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            user_futures = [
                executor.submit(simulate_user_session, user_id)
                for user_id in range(5)
            ]
            
            results = []
            for future in concurrent.futures.as_completed(user_futures, timeout=30):
                result = future.result()
                results.append(result)
        
        performance_monitor.assert_within_threshold(25.0, "concurrent_users")  # <25 seconds
        
        # All users should complete successfully
        successful_users = [r for r in results if "completed successfully" in r]
        assert len(successful_users) >= 4  # At least 4 out of 5 should succeed