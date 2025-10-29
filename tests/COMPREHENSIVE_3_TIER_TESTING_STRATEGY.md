# Comprehensive 3-Tier Testing Strategy: 15% to 100% Production Readiness

## Executive Summary

This strategy transforms the Horme POV system from a 15% mockup to 100% production-ready validation through rigorous real-world testing. The approach eliminates mock dependencies in favor of actual infrastructure, real data, and genuine business scenarios.

## Current Testing Gaps Analysis

### Identified Problems
- **Mock Data Everywhere**: 85% of current tests use fake/mock data
- **No Real Infrastructure Testing**: Database, Redis, WebSocket connections untested
- **Missing Business Logic Validation**: Core calculations and workflows unverified
- **No Load/Performance Testing**: System behavior under realistic loads unknown
- **Security Vulnerabilities**: No security validation or compliance testing
- **Integration Failures**: Components never tested together with real services

### Critical Impact Areas
1. **RFP Processing**: Pricing calculations, supplier matching, document analysis
2. **Quotation Generation**: Business logic, data transformations, PDF generation
3. **Supplier Scraping**: Real website interaction, anti-bot evasion, data quality
4. **Work Recommendations**: AI model integration, scoring algorithms, database performance
5. **Multi-Channel Platform**: API, CLI, MCP server coordination and session management

## 3-Tier Testing Strategy Overview

### NO MOCKING Policy (Tiers 2-3)
- **Tier 2 & 3 tests MUST use real infrastructure**
- **NO mock objects, stubbed responses, or fake implementations**
- **Use Docker containers for all external dependencies**
- **Validate actual business functionality, not mocked responses**

## Tier 1: Unit Tests (<1 Second)

### Purpose: Business Logic Validation
Test individual components in isolation with focus on business calculations, data transformations, and utility functions.

### Scope and Requirements
```python
# Speed: <1 second per test
# Isolation: No external dependencies
# Mocking: ONLY allowed in Tier 1
# Location: tests/unit/
```

### Business Logic Test Categories

#### 1. Pricing Calculations
```python
# tests/unit/test_pricing_calculations.py
import pytest
from src.rfp_analysis_system import PricingCalculator
from decimal import Decimal

def test_supplier_markup_calculation():
    """Test markup calculation with various scenarios."""
    calc = PricingCalculator()
    
    # Standard markup
    result = calc.calculate_markup(
        base_price=Decimal("100.00"),
        markup_percentage=Decimal("15.0")
    )
    assert result == Decimal("115.00")
    
    # Volume discount
    result = calc.calculate_volume_discount(
        unit_price=Decimal("50.00"),
        quantity=1000,
        tier_thresholds=[100, 500, 1000],
        tier_discounts=[5, 10, 15]
    )
    assert result == Decimal("42.50")  # 15% discount

def test_complex_pricing_scenarios():
    """Test edge cases in pricing calculations."""
    calc = PricingCalculator()
    
    # Zero quantity handling
    result = calc.calculate_total_cost(
        unit_price=Decimal("10.00"),
        quantity=0
    )
    assert result == Decimal("0.00")
    
    # Negative quantity (error case)
    with pytest.raises(ValueError, match="Quantity cannot be negative"):
        calc.calculate_total_cost(
            unit_price=Decimal("10.00"),
            quantity=-5
        )
```

#### 2. Data Transformation Logic
```python
# tests/unit/test_data_transformations.py
import pytest
from src.data_enrichment_pipeline import ProductEnricher

def test_product_category_normalization():
    """Test product category standardization."""
    enricher = ProductEnricher()
    
    # Test various input formats
    test_cases = [
        ("Networking Equipment", "networking_equipment"),
        ("SERVERS & STORAGE", "servers_storage"),
        ("Software/Licenses", "software_licenses"),
        ("Unknown Category", "other")
    ]
    
    for input_cat, expected in test_cases:
        result = enricher.normalize_category(input_cat)
        assert result == expected

def test_supplier_data_cleaning():
    """Test supplier data cleaning and validation."""
    enricher = ProductEnricher()
    
    dirty_data = {
        "company_name": "  ACME Corp, Inc.  ",
        "email": "SALES@ACME.COM",
        "phone": "(555) 123-4567 ext 100",
        "website": "www.acme.com/"
    }
    
    cleaned = enricher.clean_supplier_data(dirty_data)
    
    assert cleaned["company_name"] == "ACME Corp, Inc."
    assert cleaned["email"] == "sales@acme.com"
    assert cleaned["phone"] == "555-123-4567"
    assert cleaned["website"] == "https://www.acme.com"
```

#### 3. Scoring Algorithms
```python
# tests/unit/test_scoring_algorithms.py
import pytest
from src.intelligent_work_recommendation_engine import RecommendationScorer

def test_supplier_confidence_scoring():
    """Test supplier confidence scoring algorithm."""
    scorer = RecommendationScorer()
    
    # High confidence supplier
    supplier_data = {
        "years_in_business": 15,
        "certifications": ["ISO9001", "Microsoft Gold"],
        "customer_reviews": 4.8,
        "past_performance": 0.95,
        "response_time_hours": 2.5
    }
    
    score = scorer.calculate_supplier_confidence(supplier_data)
    assert score >= 0.85  # Should be high confidence
    
    # Low confidence supplier
    low_quality_supplier = {
        "years_in_business": 1,
        "certifications": [],
        "customer_reviews": 2.1,
        "past_performance": 0.60,
        "response_time_hours": 48.0
    }
    
    score = scorer.calculate_supplier_confidence(low_quality_supplier)
    assert score <= 0.40  # Should be low confidence

def test_project_recommendation_ranking():
    """Test project recommendation ranking algorithm."""
    scorer = RecommendationScorer()
    
    projects = [
        {
            "urgency": "high",
            "budget": 50000,
            "complexity": "medium",
            "client_tier": "enterprise"
        },
        {
            "urgency": "low",
            "budget": 5000,
            "complexity": "low",
            "client_tier": "small_business"
        }
    ]
    
    ranked = scorer.rank_projects(projects)
    assert ranked[0]["urgency"] == "high"  # High urgency should rank first
```

#### 4. Validation Logic
```python
# tests/unit/test_validation_logic.py
import pytest
from src.rfp_document_processing import RFPValidator

def test_rfp_document_validation():
    """Test RFP document structure validation."""
    validator = RFPValidator()
    
    # Valid RFP
    valid_rfp = {
        "title": "Network Infrastructure Upgrade",
        "budget_range": {"min": 10000, "max": 50000},
        "timeline": {"start": "2024-03-01", "end": "2024-06-01"},
        "requirements": ["Cisco equipment", "24/7 support"],
        "contact": {
            "name": "John Smith",
            "email": "john@company.com",
            "phone": "555-1234"
        }
    }
    
    result = validator.validate_rfp_structure(valid_rfp)
    assert result.is_valid is True
    assert len(result.errors) == 0
    
    # Invalid RFP - missing required fields
    invalid_rfp = {
        "title": "Incomplete RFP",
        "budget_range": {"min": 10000}  # Missing max
        # Missing timeline, requirements, contact
    }
    
    result = validator.validate_rfp_structure(invalid_rfp)
    assert result.is_valid is False
    assert "budget_range.max" in result.errors
    assert "timeline" in result.errors
```

### Unit Test Performance Targets
- **Individual test**: <1 second
- **Test suite**: <30 seconds total
- **Coverage**: >90% for business logic functions
- **Reliability**: 100% pass rate on clean builds

## Tier 2: Integration Tests (<5 Seconds)

### Purpose: Real Infrastructure Integration
Test component interactions using actual Docker services. **NO MOCKING ALLOWED**.

### Infrastructure Requirements
```bash
# Must run before integration tests
./tests/utils/test-env setup
./tests/utils/test-env status

# Expected services
✅ PostgreSQL: Ready (port 5432)
✅ Redis: Ready (port 6379) 
✅ MinIO: Ready (port 9000)
✅ Elasticsearch: Ready (port 9200)
✅ Ollama: Ready (port 11434)
```

### Integration Test Categories

#### 1. Database Operations with Real PostgreSQL
```python
# tests/integration/test_real_database_operations.py
import pytest
from src.production_api_endpoints import DatabaseManager
from tests.utils.docker_config import get_test_db_config

@pytest.mark.integration
def test_rfp_lifecycle_database_operations():
    """Test complete RFP lifecycle with real database."""
    db_config = get_test_db_config()
    db_manager = DatabaseManager(db_config)
    
    # Create RFP record
    rfp_data = {
        "title": "Integration Test RFP",
        "description": "Testing real database operations",
        "budget_min": 10000,
        "budget_max": 50000,
        "deadline": "2024-06-01",
        "client_id": "test-client-123"
    }
    
    rfp_id = db_manager.create_rfp(rfp_data)
    assert rfp_id is not None
    
    # Retrieve and verify
    retrieved_rfp = db_manager.get_rfp(rfp_id)
    assert retrieved_rfp["title"] == "Integration Test RFP"
    assert retrieved_rfp["budget_min"] == 10000
    
    # Update RFP status
    db_manager.update_rfp_status(rfp_id, "in_progress")
    updated_rfp = db_manager.get_rfp(rfp_id)
    assert updated_rfp["status"] == "in_progress"
    
    # Add quotations
    quotation_data = {
        "rfp_id": rfp_id,
        "supplier_id": "supplier-456",
        "total_price": 35000,
        "delivery_timeline": "8 weeks",
        "items": [
            {"description": "Router", "quantity": 2, "unit_price": 5000},
            {"description": "Switches", "quantity": 10, "unit_price": 2500}
        ]
    }
    
    quotation_id = db_manager.create_quotation(quotation_data)
    assert quotation_id is not None
    
    # Verify quotation relationships
    rfp_quotations = db_manager.get_quotations_for_rfp(rfp_id)
    assert len(rfp_quotations) == 1
    assert rfp_quotations[0]["total_price"] == 35000

@pytest.mark.integration
def test_concurrent_database_operations():
    """Test database operations under concurrent access."""
    import threading
    import time
    
    db_config = get_test_db_config()
    results = []
    errors = []
    
    def create_rfp_worker(worker_id):
        try:
            db_manager = DatabaseManager(db_config)
            rfp_data = {
                "title": f"Concurrent Test RFP {worker_id}",
                "description": f"Worker {worker_id} test",
                "budget_min": 1000,
                "budget_max": 5000,
                "deadline": "2024-06-01",
                "client_id": f"client-{worker_id}"
            }
            rfp_id = db_manager.create_rfp(rfp_data)
            results.append((worker_id, rfp_id))
        except Exception as e:
            errors.append((worker_id, str(e)))
    
    # Create 5 concurrent database operations
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_rfp_worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # Verify all operations succeeded
    assert len(errors) == 0, f"Database errors: {errors}"
    assert len(results) == 5, f"Expected 5 results, got {len(results)}"
    
    # Verify all RFPs were created with unique IDs
    rfp_ids = [result[1] for result in results]
    assert len(set(rfp_ids)) == 5  # All unique IDs
```

#### 2. Real API Integration Tests
```python
# tests/integration/test_real_api_integration.py
import pytest
import requests
from tests.utils.docker_config import get_api_base_url

@pytest.mark.integration
def test_rfp_processing_api_integration():
    """Test complete RFP processing through real API."""
    base_url = get_api_base_url()
    
    # Upload RFP document
    test_rfp_file = "tests/fixtures/real_rfp_document.pdf"
    with open(test_rfp_file, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{base_url}/api/rfp/upload", files=files)
    
    assert response.status_code == 200
    upload_result = response.json()
    document_id = upload_result["document_id"]
    
    # Process RFP document
    process_response = requests.post(
        f"{base_url}/api/rfp/process/{document_id}",
        json={"extract_requirements": True, "match_suppliers": True}
    )
    
    assert process_response.status_code == 200
    process_result = process_response.json()
    
    # Verify extracted requirements
    assert "requirements" in process_result
    assert len(process_result["requirements"]) > 0
    assert "budget_range" in process_result
    assert "timeline" in process_result
    
    # Verify supplier matching
    assert "matched_suppliers" in process_result
    assert len(process_result["matched_suppliers"]) > 0
    
    # Each matched supplier should have confidence score
    for supplier in process_result["matched_suppliers"]:
        assert "confidence_score" in supplier
        assert 0.0 <= supplier["confidence_score"] <= 1.0
        assert "company_name" in supplier
        assert "contact_info" in supplier

@pytest.mark.integration  
def test_quotation_generation_api_integration():
    """Test quotation generation with real supplier data."""
    base_url = get_api_base_url()
    
    # Create quotation request
    quotation_request = {
        "rfp_id": "test-rfp-123",
        "supplier_id": "real-supplier-456",
        "items": [
            {
                "description": "Enterprise Router",
                "specification": "Cisco ISR 4331",
                "quantity": 2,
                "required_delivery": "2024-04-15"
            },
            {
                "description": "Managed Switch",
                "specification": "Cisco Catalyst 9300-24T",
                "quantity": 4,
                "required_delivery": "2024-04-15"
            }
        ],
        "service_requirements": [
            "Installation and configuration",
            "2-year warranty support",
            "Training for 4 staff members"
        ]
    }
    
    response = requests.post(
        f"{base_url}/api/quotations/generate",
        json=quotation_request
    )
    
    assert response.status_code == 200
    quotation = response.json()
    
    # Verify quotation structure
    assert "quotation_id" in quotation
    assert "line_items" in quotation
    assert "total_amount" in quotation
    assert "delivery_timeline" in quotation
    
    # Verify line items match request
    assert len(quotation["line_items"]) == 2  # Hardware items
    
    # Verify pricing calculations
    total_calculated = sum(
        item["quantity"] * item["unit_price"] 
        for item in quotation["line_items"]
    )
    assert abs(quotation["total_amount"] - total_calculated) < 0.01
    
    # Verify PDF generation
    pdf_response = requests.get(
        f"{base_url}/api/quotations/{quotation['quotation_id']}/pdf"
    )
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert len(pdf_response.content) > 1000  # Reasonable PDF size
```

#### 3. Real WebSocket Communication Tests
```python
# tests/integration/test_real_websocket_integration.py
import pytest
import asyncio
import websockets
import json
from tests.utils.docker_config import get_websocket_url

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_server_real_communication():
    """Test MCP server communication with real WebSocket."""
    ws_url = get_websocket_url()
    
    async with websockets.connect(ws_url) as websocket:
        # Send initialization message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        await websocket.send(json.dumps(init_message))
        response = await websocket.recv()
        init_response = json.loads(response)
        
        assert "result" in init_response
        assert "capabilities" in init_response["result"]
        
        # Test tool listing
        tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        await websocket.send(json.dumps(tools_message))
        tools_response = await websocket.recv()
        tools_result = json.loads(tools_response)
        
        assert "result" in tools_result
        assert "tools" in tools_result["result"]
        assert len(tools_result["result"]["tools"]) > 0
        
        # Test actual tool execution
        search_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_products",
                "arguments": {
                    "query": "cisco router",
                    "category": "networking",
                    "max_results": 5
                }
            }
        }
        
        await websocket.send(json.dumps(search_message))
        search_response = await websocket.recv()
        search_result = json.loads(search_response)
        
        assert "result" in search_result
        assert "content" in search_result["result"]
        
        # Verify search results structure
        content = search_result["result"]["content"]
        if isinstance(content, list) and len(content) > 0:
            result_data = content[0]
            if "text" in result_data:
                # Parse search results
                import json
                results = json.loads(result_data["text"])
                assert "products" in results
                assert len(results["products"]) > 0
                
                # Verify product structure
                for product in results["products"]:
                    assert "name" in product
                    assert "category" in product
                    assert "price" in product
```

#### 4. Real File I/O and Document Processing
```python
# tests/integration/test_real_document_processing.py
import pytest
import os
import tempfile
from src.rfp_document_processing import DocumentProcessor
from tests.fixtures import get_test_documents_path

@pytest.mark.integration
def test_real_pdf_document_processing():
    """Test PDF document processing with real files."""
    processor = DocumentProcessor()
    test_pdf = os.path.join(get_test_documents_path(), "sample_rfp.pdf")
    
    # Process real PDF document
    result = processor.process_document(test_pdf)
    
    assert result.success is True
    assert len(result.extracted_text) > 100  # Reasonable text length
    assert result.document_type == "rfp"
    
    # Verify extracted metadata
    assert "title" in result.metadata
    assert "page_count" in result.metadata
    assert result.metadata["page_count"] > 0
    
    # Verify requirement extraction
    assert len(result.requirements) > 0
    for requirement in result.requirements:
        assert "description" in requirement
        assert "priority" in requirement
        assert requirement["priority"] in ["high", "medium", "low"]
    
    # Verify budget extraction
    if result.budget_info:
        assert "min_budget" in result.budget_info or "max_budget" in result.budget_info
        if "min_budget" in result.budget_info:
            assert result.budget_info["min_budget"] > 0

@pytest.mark.integration
def test_real_excel_data_import():
    """Test Excel data processing with real files."""
    processor = DocumentProcessor()
    test_excel = os.path.join(get_test_documents_path(), "product_catalog.xlsx")
    
    # Import real Excel data
    result = processor.import_excel_data(test_excel)
    
    assert result.success is True
    assert len(result.imported_records) > 0
    
    # Verify data structure
    for record in result.imported_records:
        assert "product_name" in record
        assert "category" in record
        assert "price" in record
        
        # Verify data types
        assert isinstance(record["product_name"], str)
        assert len(record["product_name"]) > 0
        assert isinstance(record["price"], (int, float))
        assert record["price"] > 0
    
    # Verify data quality
    product_names = [r["product_name"] for r in result.imported_records]
    assert len(set(product_names)) == len(product_names)  # No duplicates

@pytest.mark.integration
def test_real_document_storage_retrieval():
    """Test document storage and retrieval with real file system."""
    processor = DocumentProcessor()
    
    # Create test document
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        test_content = "This is a test document for integration testing."
        f.write(test_content)
        test_file_path = f.name
    
    try:
        # Store document
        storage_result = processor.store_document(
            file_path=test_file_path,
            document_type="test",
            metadata={"test": True, "integration": "real_storage"}
        )
        
        assert storage_result.success is True
        document_id = storage_result.document_id
        assert document_id is not None
        
        # Retrieve document
        retrieved = processor.retrieve_document(document_id)
        assert retrieved.success is True
        assert retrieved.content == test_content
        assert retrieved.metadata["test"] is True
        
        # Search documents
        search_results = processor.search_documents(
            query="integration testing",
            document_types=["test"]
        )
        
        assert len(search_results) >= 1
        found_doc = next((d for d in search_results if d.id == document_id), None)
        assert found_doc is not None
        
    finally:
        os.unlink(test_file_path)
```

### Integration Test Performance Targets
- **Individual test**: <5 seconds
- **Test suite**: <5 minutes total
- **Infrastructure startup**: <30 seconds
- **Reliability**: >95% pass rate with real services

## Tier 3: End-to-End Tests (<10 Seconds)

### Purpose: Complete Business Workflow Validation
Test complete user workflows from start to finish using full infrastructure stack.

### E2E Test Categories

#### 1. Complete RFP Processing Workflow
```python
# tests/e2e/test_complete_rfp_workflow.py
import pytest
import requests
import time
from tests.utils.docker_config import get_full_stack_config

@pytest.mark.e2e
def test_complete_rfp_processing_workflow():
    """Test complete RFP workflow from document upload to quotation generation."""
    config = get_full_stack_config()
    api_base = config["api_url"]
    
    # Step 1: Upload RFP document
    test_rfp = "tests/fixtures/complete_rfp_example.pdf"
    with open(test_rfp, "rb") as f:
        upload_response = requests.post(
            f"{api_base}/api/documents/upload",
            files={"document": f},
            data={"document_type": "rfp", "client_id": "e2e-test-client"}
        )
    
    assert upload_response.status_code == 200
    upload_result = upload_response.json()
    document_id = upload_result["document_id"]
    
    # Step 2: Process RFP document
    processing_response = requests.post(
        f"{api_base}/api/rfp/analyze",
        json={
            "document_id": document_id,
            "options": {
                "extract_requirements": True,
                "estimate_budget": True,
                "match_suppliers": True,
                "generate_preliminary_timeline": True
            }
        }
    )
    
    assert processing_response.status_code == 200
    analysis_result = processing_response.json()
    rfp_id = analysis_result["rfp_id"]
    
    # Verify analysis results
    assert len(analysis_result["requirements"]) >= 3
    assert "budget_estimate" in analysis_result
    assert len(analysis_result["matched_suppliers"]) >= 2
    
    # Step 3: Generate quotations from matched suppliers
    quotation_ids = []
    for supplier in analysis_result["matched_suppliers"][:3]:  # Top 3 suppliers
        quotation_response = requests.post(
            f"{api_base}/api/quotations/generate",
            json={
                "rfp_id": rfp_id,
                "supplier_id": supplier["id"],
                "auto_price": True,
                "include_services": True
            }
        )
        
        assert quotation_response.status_code == 200
        quotation_result = quotation_response.json()
        quotation_ids.append(quotation_result["quotation_id"])
    
    assert len(quotation_ids) == 3
    
    # Step 4: Compare quotations
    comparison_response = requests.post(
        f"{api_base}/api/quotations/compare",
        json={
            "rfp_id": rfp_id,
            "quotation_ids": quotation_ids,
            "comparison_criteria": [
                "total_price", "delivery_time", "supplier_rating", "warranty_terms"
            ]
        }
    )
    
    assert comparison_response.status_code == 200
    comparison_result = comparison_response.json()
    
    # Verify comparison results
    assert "recommendations" in comparison_result
    assert len(comparison_result["quotations"]) == 3
    
    best_quotation = comparison_result["recommendations"]["best_value"]
    assert "quotation_id" in best_quotation
    assert "reasoning" in best_quotation
    
    # Step 5: Generate final report
    report_response = requests.post(
        f"{api_base}/api/reports/rfp-summary",
        json={
            "rfp_id": rfp_id,
            "include_quotations": True,
            "include_analysis": True,
            "format": "pdf"
        }
    )
    
    assert report_response.status_code == 200
    assert report_response.headers["content-type"] == "application/pdf"
    
    # Verify PDF content size
    pdf_content = report_response.content
    assert len(pdf_content) > 10000  # Reasonable PDF size
    
    # Step 6: Verify data persistence
    rfp_status_response = requests.get(f"{api_base}/api/rfp/{rfp_id}")
    assert rfp_status_response.status_code == 200
    
    rfp_status = rfp_status_response.json()
    assert rfp_status["status"] == "analyzed"
    assert len(rfp_status["quotations"]) == 3
```

#### 2. Complete Supplier Scraping and Enrichment Workflow
```python
# tests/e2e/test_complete_supplier_workflow.py
import pytest
import asyncio
from src.horme_scraper.scraper import SupplierScraper
from src.data_enrichment_pipeline import DataEnrichmentPipeline
from tests.utils.docker_config import get_full_stack_config

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_supplier_scraping_workflow():
    """Test complete supplier discovery, scraping, and enrichment."""
    config = get_full_stack_config()
    
    # Step 1: Initialize scraper with real configuration
    scraper = SupplierScraper(
        database_url=config["database_url"],
        redis_url=config["redis_url"],
        enable_proxy_rotation=True,
        max_concurrent_requests=5
    )
    
    # Step 2: Scrape real supplier data (limited scope for testing)
    target_suppliers = [
        "https://www.cdw.com",
        "https://www.insight.com", 
        "https://www.shi.com"
    ]
    
    scraping_results = []
    for supplier_url in target_suppliers:
        try:
            result = await scraper.scrape_supplier_catalog(
                supplier_url=supplier_url,
                max_products=50,  # Limited for testing
                categories=["networking", "servers", "storage"]
            )
            scraping_results.append(result)
        except Exception as e:
            pytest.skip(f"Supplier {supplier_url} unreachable: {e}")
    
    # Verify scraping results
    assert len(scraping_results) >= 1  # At least one supplier scraped
    
    total_products = sum(len(result.products) for result in scraping_results)
    assert total_products >= 20  # Reasonable product count
    
    # Verify product data quality
    for result in scraping_results:
        for product in result.products:
            assert product.name is not None
            assert len(product.name) > 0
            assert product.category is not None
            assert product.price > 0 or product.price_range is not None
    
    # Step 3: Enrich scraped data
    enrichment_pipeline = DataEnrichmentPipeline(
        database_url=config["database_url"],
        ai_model_url=config["ollama_url"]
    )
    
    enrichment_jobs = []
    for result in scraping_results:
        job = await enrichment_pipeline.enrich_product_batch(
            products=result.products,
            enrichment_options={
                "categorize": True,
                "extract_specifications": True,
                "normalize_pricing": True,
                "generate_descriptions": True,
                "match_existing": True
            }
        )
        enrichment_jobs.append(job)
    
    # Wait for enrichment completion
    for job in enrichment_jobs:
        enrichment_result = await enrichment_pipeline.get_job_result(job.job_id)
        while enrichment_result.status == "processing":
            await asyncio.sleep(2)
            enrichment_result = await enrichment_pipeline.get_job_result(job.job_id)
        
        assert enrichment_result.status == "completed"
        assert enrichment_result.success_rate > 0.8  # 80% success rate
        
        # Verify enriched data quality
        for enriched_product in enrichment_result.enriched_products:
            assert enriched_product.normalized_category is not None
            assert enriched_product.confidence_score > 0.5
            
            if enriched_product.specifications:
                assert len(enriched_product.specifications) > 0
    
    # Step 4: Verify data persistence and searchability
    from src.production_api_endpoints import ProductSearch
    
    search_engine = ProductSearch(database_url=config["database_url"])
    
    # Test search functionality
    search_results = await search_engine.search_products(
        query="cisco router",
        filters={"category": "networking"},
        max_results=10
    )
    
    assert len(search_results) > 0
    
    # Verify search result quality
    for product in search_results:
        assert "cisco" in product.name.lower() or "router" in product.name.lower()
        assert product.category == "networking"
        assert product.supplier_info is not None
```

#### 3. Complete Multi-Channel Platform Workflow
```python
# tests/e2e/test_complete_platform_workflow.py
import pytest
import requests
import subprocess
import json
from tests.utils.docker_config import get_full_stack_config

@pytest.mark.e2e
def test_complete_multi_channel_platform_workflow():
    """Test complete workflow across API, CLI, and MCP channels."""
    config = get_full_stack_config()
    
    # Step 1: Create project via API
    api_response = requests.post(
        f"{config['api_url']}/api/projects/create",
        json={
            "name": "E2E Test Project",
            "description": "Multi-channel testing project",
            "budget": 25000,
            "priority": "high",
            "requirements": [
                "Network infrastructure upgrade",
                "Server consolidation",
                "Security implementation"
            ]
        }
    )
    
    assert api_response.status_code == 200
    project_data = api_response.json()
    project_id = project_data["project_id"]
    
    # Step 2: Generate recommendations via CLI
    cli_command = [
        "docker", "exec", "horme-nexus",
        "python", "-m", "src.nexus_cli",
        "generate-recommendations",
        "--project-id", project_id,
        "--output", "json"
    ]
    
    cli_result = subprocess.run(
        cli_command, 
        capture_output=True, 
        text=True, 
        timeout=30
    )
    
    assert cli_result.returncode == 0
    recommendations_output = json.loads(cli_result.stdout)
    
    assert "recommendations" in recommendations_output
    assert len(recommendations_output["recommendations"]) > 0
    
    # Step 3: Process recommendations via MCP
    import websockets
    import asyncio
    
    async def test_mcp_processing():
        ws_url = config["mcp_websocket_url"]
        
        async with websockets.connect(ws_url) as websocket:
            # Initialize MCP session
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "e2e-test", "version": "1.0"}
                }
            }
            
            await websocket.send(json.dumps(init_message))
            await websocket.recv()  # Consume init response
            
            # Process project recommendations
            process_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "process_project_recommendations",
                    "arguments": {
                        "project_id": project_id,
                        "recommendations": recommendations_output["recommendations"],
                        "auto_prioritize": True,
                        "generate_timeline": True
                    }
                }
            }
            
            await websocket.send(json.dumps(process_message))
            mcp_response = await websocket.recv()
            mcp_result = json.loads(mcp_response)
            
            assert "result" in mcp_result
            return mcp_result["result"]
    
    mcp_processing_result = asyncio.run(test_mcp_processing())
    
    # Step 4: Verify cross-channel data consistency
    # Check that all channels see the same updated project state
    
    # API verification
    api_project_check = requests.get(
        f"{config['api_url']}/api/projects/{project_id}"
    )
    assert api_project_check.status_code == 200
    api_project_state = api_project_check.json()
    
    # CLI verification
    cli_status_command = [
        "docker", "exec", "horme-nexus",
        "python", "-m", "src.nexus_cli",
        "project-status",
        "--project-id", project_id,
        "--output", "json"
    ]
    
    cli_status_result = subprocess.run(
        cli_status_command,
        capture_output=True,
        text=True,
        timeout=15
    )
    
    assert cli_status_result.returncode == 0
    cli_project_state = json.loads(cli_status_result.stdout)
    
    # Verify consistency
    assert api_project_state["project_id"] == cli_project_state["project_id"]
    assert api_project_state["status"] == cli_project_state["status"]
    assert len(api_project_state["recommendations"]) == len(cli_project_state["recommendations"])
    
    # Step 5: Generate final deliverables
    deliverables_response = requests.post(
        f"{config['api_url']}/api/projects/{project_id}/deliverables",
        json={
            "include_recommendations": True,
            "include_timeline": True,
            "include_budget_breakdown": True,
            "include_risk_analysis": True,
            "format": ["pdf", "excel"]
        }
    )
    
    assert deliverables_response.status_code == 200
    deliverables_result = deliverables_response.json()
    
    assert "pdf_url" in deliverables_result
    assert "excel_url" in deliverables_result
    
    # Verify deliverable files
    pdf_response = requests.get(deliverables_result["pdf_url"])
    assert pdf_response.status_code == 200
    assert len(pdf_response.content) > 5000  # Reasonable PDF size
    
    excel_response = requests.get(deliverables_result["excel_url"])
    assert excel_response.status_code == 200
    assert len(excel_response.content) > 2000  # Reasonable Excel size
```

### E2E Test Performance Targets
- **Individual test**: <10 seconds
- **Test suite**: <15 minutes total
- **Full stack startup**: <60 seconds
- **Reliability**: >90% pass rate with full infrastructure

## Test Data Management Strategy

### Real Data Approach (NO MOCK DATA)
Replace mock data with curated real-world test datasets that represent actual business scenarios.

### Test Data Categories

#### 1. Document Test Data
```python
# tests/fixtures/test_documents.py
class RealTestDocuments:
    """Curated collection of real test documents."""
    
    @classmethod
    def get_rfp_documents(cls):
        """Return paths to real RFP documents for testing."""
        return [
            "tests/fixtures/documents/networking_rfp_example.pdf",
            "tests/fixtures/documents/server_infrastructure_rfp.pdf",
            "tests/fixtures/documents/security_implementation_rfp.pdf"
        ]
    
    @classmethod
    def get_supplier_catalogs(cls):
        """Return real supplier catalog data."""
        return [
            "tests/fixtures/catalogs/cisco_catalog_sample.xlsx",
            "tests/fixtures/catalogs/dell_server_catalog.csv",
            "tests/fixtures/catalogs/fortinet_security_products.json"
        ]
    
    @classmethod
    def get_quotation_examples(cls):
        """Return real quotation examples."""
        return [
            "tests/fixtures/quotations/enterprise_network_quote.pdf",
            "tests/fixtures/quotations/server_consolidation_quote.xlsx"
        ]
```

#### 2. Database Test Data
```python
# tests/fixtures/test_database_data.py
class RealTestData:
    """Real business data for database testing."""
    
    REAL_SUPPLIERS = [
        {
            "company_name": "CDW Corporation",
            "website": "https://www.cdw.com",
            "categories": ["networking", "servers", "software"],
            "certifications": ["Microsoft Gold", "Cisco Gold"],
            "rating": 4.6,
            "years_in_business": 35
        },
        {
            "company_name": "Insight Enterprises",
            "website": "https://www.insight.com",
            "categories": ["cloud", "datacenter", "networking"],
            "certifications": ["AWS Premier", "Microsoft Gold"],
            "rating": 4.4,
            "years_in_business": 32
        }
    ]
    
    REAL_PRODUCTS = [
        {
            "name": "Cisco ISR 4331 Integrated Services Router",
            "category": "networking",
            "manufacturer": "Cisco",
            "model": "ISR4331/K9",
            "specifications": {
                "throughput": "100 Mbps",
                "wan_ports": 3,
                "lan_ports": 2,
                "form_factor": "1RU"
            },
            "price_range": {"min": 1200, "max": 1800}
        },
        {
            "name": "Dell PowerEdge R740 Server",
            "category": "servers",
            "manufacturer": "Dell",
            "model": "R740",
            "specifications": {
                "processor": "Intel Xeon Scalable",
                "memory_max": "768GB",
                "storage_bays": 16,
                "form_factor": "2U"
            },
            "price_range": {"min": 3500, "max": 15000}
        }
    ]
    
    REAL_RFPS = [
        {
            "title": "Enterprise Network Infrastructure Modernization",
            "description": "Upgrade aging network infrastructure for 500-person organization",
            "budget_range": {"min": 50000, "max": 150000},
            "timeline_weeks": 12,
            "requirements": [
                "Replace core switches and routers",
                "Implement redundancy and failover",
                "Upgrade to Wi-Fi 6",
                "Network monitoring and management tools"
            ],
            "compliance_requirements": ["SOC 2", "HIPAA"]
        }
    ]
```

#### 3. Performance Test Data
```python
# tests/fixtures/performance_test_data.py
class PerformanceTestData:
    """Realistic data volumes for performance testing."""
    
    @classmethod
    def generate_bulk_products(cls, count=10000):
        """Generate realistic bulk product data."""
        base_products = RealTestData.REAL_PRODUCTS
        
        products = []
        for i in range(count):
            base_product = base_products[i % len(base_products)]
            product = base_product.copy()
            product["name"] = f"{product['name']} - Model {i:05d}"
            product["model"] = f"{product['model']}-{i:05d}"
            products.append(product)
        
        return products
    
    @classmethod
    def generate_concurrent_requests(cls, count=100):
        """Generate concurrent API request scenarios."""
        return [
            {
                "endpoint": "/api/products/search",
                "method": "POST",
                "payload": {"query": f"router model {i}", "max_results": 10}
            }
            for i in range(count)
        ]
```

### Test Data Lifecycle Management
```python
# tests/utils/test_data_manager.py
class TestDataManager:
    """Manage test data lifecycle and cleanup."""
    
    def __init__(self, database_url):
        self.database_url = database_url
        self.created_records = {}
    
    def setup_test_data(self, test_name):
        """Set up fresh test data for a specific test."""
        # Load appropriate test dataset
        if "supplier" in test_name:
            return self._load_supplier_test_data()
        elif "product" in test_name:
            return self._load_product_test_data()
        elif "rfp" in test_name:
            return self._load_rfp_test_data()
    
    def cleanup_test_data(self, test_name):
        """Clean up test data after test completion."""
        if test_name in self.created_records:
            for table, record_ids in self.created_records[test_name].items():
                self._delete_records(table, record_ids)
    
    def _load_supplier_test_data(self):
        """Load real supplier test data."""
        suppliers = RealTestData.REAL_SUPPLIERS
        created_ids = []
        
        for supplier_data in suppliers:
            supplier_id = self._insert_supplier(supplier_data)
            created_ids.append(supplier_id)
        
        return created_ids
```

## Performance Benchmarks and Load Testing

### Performance Targets

#### Response Time SLAs
```python
# tests/performance/test_sla_validation.py
import pytest
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import requests

class PerformanceSLAs:
    """Define performance SLA targets for validation."""
    
    API_RESPONSE_TIMES = {
        "product_search": {"target": 200, "max": 500},  # milliseconds
        "quotation_generation": {"target": 2000, "max": 5000},
        "document_upload": {"target": 1000, "max": 3000},
        "rfp_analysis": {"target": 5000, "max": 10000}
    }
    
    THROUGHPUT_TARGETS = {
        "concurrent_searches": 50,  # requests per second
        "document_processing": 5,   # documents per minute
        "quotation_generation": 10  # quotations per minute
    }
    
    RESOURCE_LIMITS = {
        "memory_usage_mb": 2048,
        "cpu_usage_percent": 80,
        "disk_usage_mb": 10240
    }

@pytest.mark.performance
def test_api_response_time_slas():
    """Validate API response times meet SLA requirements."""
    api_base = get_test_api_url()
    slas = PerformanceSLAs.API_RESPONSE_TIMES
    
    test_cases = [
        {
            "name": "product_search",
            "url": f"{api_base}/api/products/search",
            "method": "POST",
            "payload": {"query": "cisco router", "max_results": 20}
        },
        {
            "name": "quotation_generation", 
            "url": f"{api_base}/api/quotations/generate",
            "method": "POST",
            "payload": {
                "rfp_id": "test-rfp-123",
                "supplier_id": "test-supplier-456",
                "items": [{"name": "Router", "quantity": 2, "specs": "Basic"}]
            }
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        response_times = []
        
        # Run 10 iterations to get statistical data
        for _ in range(10):
            start_time = time.time()
            
            if test_case["method"] == "POST":
                response = requests.post(test_case["url"], json=test_case["payload"])
            else:
                response = requests.get(test_case["url"])
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            response_times.append(response_time_ms)
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        max_response_time = max(response_times)
        
        results[test_case["name"]] = {
            "average": avg_response_time,
            "p95": p95_response_time,
            "max": max_response_time
        }
        
        # Validate against SLAs
        sla = slas[test_case["name"]]
        assert avg_response_time <= sla["target"], f"Average response time {avg_response_time:.2f}ms exceeds target {sla['target']}ms"
        assert max_response_time <= sla["max"], f"Max response time {max_response_time:.2f}ms exceeds limit {sla['max']}ms"
    
    print("Performance SLA Results:", results)

@pytest.mark.performance
def test_concurrent_load_handling():
    """Test system behavior under concurrent load."""
    api_base = get_test_api_url()
    concurrent_requests = 25
    
    def make_search_request(query_id):
        """Make a single search request."""
        start_time = time.time()
        response = requests.post(
            f"{api_base}/api/products/search",
            json={"query": f"test product {query_id}", "max_results": 10}
        )
        end_time = time.time()
        
        return {
            "query_id": query_id,
            "status_code": response.status_code,
            "response_time": (end_time - start_time) * 1000,
            "success": response.status_code == 200
        }
    
    # Execute concurrent requests
    with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        futures = [
            executor.submit(make_search_request, i) 
            for i in range(concurrent_requests)
        ]
        
        results = [future.result() for future in futures]
    
    # Analyze results
    successful_requests = [r for r in results if r["success"]]
    failed_requests = [r for r in results if not r["success"]]
    
    success_rate = len(successful_requests) / len(results)
    avg_response_time = statistics.mean([r["response_time"] for r in successful_requests])
    
    # Validate performance under load
    assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95% threshold"
    assert avg_response_time <= 1000, f"Average response time {avg_response_time:.2f}ms exceeds 1000ms under load"
    assert len(failed_requests) <= 1, f"Too many failed requests: {len(failed_requests)}"

@pytest.mark.performance
def test_memory_usage_monitoring():
    """Monitor memory usage during intensive operations."""
    import psutil
    import os
    
    # Get baseline memory usage
    process = psutil.Process()
    baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Perform intensive operation
    api_base = get_test_api_url()
    
    # Process large document batch
    for i in range(50):
        response = requests.post(
            f"{api_base}/api/products/search",
            json={"query": f"intensive search {i}", "max_results": 100}
        )
        assert response.status_code == 200
        
        # Check memory every 10 iterations
        if i % 10 == 0:
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - baseline_memory
            
            assert memory_increase <= PerformanceSLAs.RESOURCE_LIMITS["memory_usage_mb"], \
                f"Memory usage increased by {memory_increase:.2f}MB, exceeding limit"
    
    # Final memory check
    final_memory = process.memory_info().rss / 1024 / 1024
    total_increase = final_memory - baseline_memory
    
    print(f"Memory usage: Baseline: {baseline_memory:.2f}MB, Final: {final_memory:.2f}MB, Increase: {total_increase:.2f}MB")
    
    assert total_increase <= PerformanceSLAs.RESOURCE_LIMITS["memory_usage_mb"], \
        f"Total memory increase {total_increase:.2f}MB exceeds limit"
```

### Load Testing Scenarios
```python
# tests/performance/test_load_scenarios.py
@pytest.mark.load_test
def test_peak_usage_simulation():
    """Simulate peak usage patterns."""
    import threading
    import queue
    import random
    
    api_base = get_test_api_url()
    results_queue = queue.Queue()
    
    # Define realistic usage patterns
    usage_patterns = [
        {
            "name": "morning_peak",
            "duration_seconds": 300,  # 5 minutes
            "requests_per_second": 30,
            "operations": [
                {"weight": 40, "operation": "product_search"},
                {"weight": 30, "operation": "quotation_view"},
                {"weight": 20, "operation": "rfp_upload"},
                {"weight": 10, "operation": "report_generation"}
            ]
        }
    ]
    
    def simulate_user_session(session_id, pattern):
        """Simulate realistic user session."""
        session_results = []
        start_time = time.time()
        
        while time.time() - start_time < pattern["duration_seconds"]:
            # Choose operation based on weighted probability
            operation = random.choices(
                [op["operation"] for op in pattern["operations"]],
                weights=[op["weight"] for op in pattern["operations"]]
            )[0]
            
            # Execute operation
            request_start = time.time()
            try:
                if operation == "product_search":
                    response = requests.post(
                        f"{api_base}/api/products/search",
                        json={"query": f"user_{session_id}_query", "max_results": 20}
                    )
                elif operation == "quotation_view":
                    response = requests.get(f"{api_base}/api/quotations/recent")
                elif operation == "rfp_upload":
                    # Simulate file upload
                    files = {"file": ("test.pdf", b"fake pdf content")}
                    response = requests.post(f"{api_base}/api/rfp/upload", files=files)
                elif operation == "report_generation":
                    response = requests.post(
                        f"{api_base}/api/reports/generate",
                        json={"type": "supplier_summary", "format": "pdf"}
                    )
                
                request_end = time.time()
                
                session_results.append({
                    "operation": operation,
                    "status_code": response.status_code,
                    "response_time": (request_end - request_start) * 1000,
                    "success": response.status_code < 400
                })
                
            except Exception as e:
                session_results.append({
                    "operation": operation,
                    "status_code": 0,
                    "response_time": 0,
                    "success": False,
                    "error": str(e)
                })
            
            # Realistic user think time
            time.sleep(random.uniform(1, 5))
        
        results_queue.put(session_results)
    
    # Execute load test
    pattern = usage_patterns[0]
    concurrent_users = 20
    
    threads = []
    for user_id in range(concurrent_users):
        thread = threading.Thread(
            target=simulate_user_session,
            args=(user_id, pattern)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    # Collect and analyze results
    all_results = []
    while not results_queue.empty():
        all_results.extend(results_queue.get())
    
    # Calculate metrics
    total_requests = len(all_results)
    successful_requests = len([r for r in all_results if r["success"]])
    failed_requests = total_requests - successful_requests
    
    success_rate = successful_requests / total_requests if total_requests > 0 else 0
    avg_response_time = statistics.mean([r["response_time"] for r in all_results if r["success"]])
    
    # Performance assertions
    assert success_rate >= 0.90, f"Success rate {success_rate:.2%} below 90% threshold during peak load"
    assert avg_response_time <= 2000, f"Average response time {avg_response_time:.2f}ms exceeds 2000ms during peak load"
    assert failed_requests <= total_requests * 0.05, f"Failed requests {failed_requests} exceed 5% threshold"
    
    print(f"Load Test Results: {total_requests} requests, {success_rate:.2%} success rate, {avg_response_time:.2f}ms avg response time")
```

## Security and Compliance Validation

### Security Test Categories

#### 1. Authentication and Authorization
```python
# tests/security/test_authentication_security.py
import pytest
import requests
import jwt
import time

@pytest.mark.security
def test_api_authentication_requirements():
    """Test API authentication and authorization."""
    api_base = get_test_api_url()
    
    # Test 1: Unauthenticated access should be denied
    protected_endpoints = [
        "/api/rfp/upload",
        "/api/quotations/generate", 
        "/api/suppliers/create",
        "/api/reports/generate"
    ]
    
    for endpoint in protected_endpoints:
        response = requests.post(f"{api_base}{endpoint}")
        assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"
    
    # Test 2: Invalid token should be rejected
    invalid_token = "invalid.jwt.token"
    headers = {"Authorization": f"Bearer {invalid_token}"}
    
    for endpoint in protected_endpoints:
        response = requests.post(f"{api_base}{endpoint}", headers=headers)
        assert response.status_code == 401, f"Invalid token should be rejected for {endpoint}"
    
    # Test 3: Expired token should be rejected
    # Generate expired token
    expired_payload = {
        "user_id": "test-user",
        "exp": int(time.time()) - 3600,  # Expired 1 hour ago
        "iat": int(time.time()) - 7200   # Issued 2 hours ago
    }
    expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
    headers = {"Authorization": f"Bearer {expired_token}"}
    
    response = requests.post(f"{api_base}/api/rfp/upload", headers=headers)
    assert response.status_code == 401, "Expired token should be rejected"
    
    # Test 4: Valid token should be accepted
    valid_payload = {
        "user_id": "test-user",
        "exp": int(time.time()) + 3600,  # Expires in 1 hour
        "iat": int(time.time()),
        "scope": ["rfp:write", "quotation:read"]
    }
    valid_token = jwt.encode(valid_payload, "secret", algorithm="HS256")
    headers = {"Authorization": f"Bearer {valid_token}"}
    
    # This should now pass authentication (may fail on other validation)
    response = requests.get(f"{api_base}/api/quotations/recent", headers=headers)
    assert response.status_code != 401, "Valid token should pass authentication"

@pytest.mark.security
def test_role_based_access_control():
    """Test role-based access control (RBAC)."""
    api_base = get_test_api_url()
    
    # Create tokens for different roles
    roles = {
        "viewer": {
            "permissions": ["quotation:read", "supplier:read"],
            "restricted_endpoints": ["/api/rfp/upload", "/api/suppliers/create"]
        },
        "editor": {
            "permissions": ["quotation:read", "quotation:write", "supplier:read"],
            "restricted_endpoints": ["/api/suppliers/create", "/api/admin/settings"]
        },
        "admin": {
            "permissions": ["*"],
            "restricted_endpoints": []
        }
    }
    
    for role_name, role_config in roles.items():
        # Generate token for role
        token_payload = {
            "user_id": f"test-{role_name}",
            "role": role_name,
            "permissions": role_config["permissions"],
            "exp": int(time.time()) + 3600
        }
        role_token = jwt.encode(token_payload, "secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {role_token}"}
        
        # Test restricted endpoints
        for endpoint in role_config["restricted_endpoints"]:
            response = requests.post(f"{api_base}{endpoint}", headers=headers)
            assert response.status_code == 403, f"Role {role_name} should be forbidden from {endpoint}"
```

#### 2. Input Validation and Injection Prevention
```python
# tests/security/test_input_validation.py
@pytest.mark.security
def test_sql_injection_prevention():
    """Test protection against SQL injection attacks."""
    api_base = get_test_api_url()
    valid_token = generate_test_token(permissions=["supplier:read"])
    headers = {"Authorization": f"Bearer {valid_token}"}
    
    # SQL injection payloads
    injection_payloads = [
        "'; DROP TABLE suppliers; --",
        "1' OR '1'='1",
        "admin'--",
        "1'; INSERT INTO users (username) VALUES ('hacker'); --",
        "' UNION SELECT * FROM sensitive_data --"
    ]
    
    for payload in injection_payloads:
        # Test in search query
        response = requests.post(
            f"{api_base}/api/suppliers/search",
            headers=headers,
            json={"query": payload, "max_results": 10}
        )
        
        # Should not return 500 error (which might indicate SQL error)
        assert response.status_code != 500, f"SQL injection payload may have caused server error: {payload}"
        
        # Response should be sanitized/empty rather than containing injection results
        if response.status_code == 200:
            result = response.json()
            # Should not return suspicious data patterns
            assert "DROP" not in str(result).upper()
            assert "UNION" not in str(result).upper()
            assert "INSERT" not in str(result).upper()

@pytest.mark.security
def test_xss_prevention():
    """Test protection against Cross-Site Scripting (XSS) attacks."""
    api_base = get_test_api_url()
    valid_token = generate_test_token(permissions=["rfp:write"])
    headers = {"Authorization": f"Bearer {valid_token}"}
    
    # XSS payloads
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "';alert('XSS');//"
    ]
    
    for payload in xss_payloads:
        # Test in RFP creation
        response = requests.post(
            f"{api_base}/api/rfp/create",
            headers=headers,
            json={
                "title": payload,
                "description": f"Test RFP with payload: {payload}",
                "requirements": [payload]
            }
        )
        
        if response.status_code == 200:
            rfp_result = response.json()
            rfp_id = rfp_result.get("rfp_id")
            
            if rfp_id:
                # Retrieve RFP and check if payload is sanitized
                get_response = requests.get(f"{api_base}/api/rfp/{rfp_id}", headers=headers)
                
                if get_response.status_code == 200:
                    retrieved_rfp = get_response.json()
                    
                    # XSS payloads should be sanitized
                    assert "<script>" not in retrieved_rfp.get("title", "")
                    assert "javascript:" not in retrieved_rfp.get("title", "")
                    assert "onerror=" not in retrieved_rfp.get("title", "")

@pytest.mark.security
def test_file_upload_security():
    """Test file upload security and validation."""
    api_base = get_test_api_url()
    valid_token = generate_test_token(permissions=["rfp:write"])
    headers = {"Authorization": f"Bearer {valid_token}"}
    
    # Test 1: Malicious file types should be rejected
    malicious_files = [
        ("malware.exe", b"MZ\x90\x00", "application/octet-stream"),
        ("script.bat", b"@echo off\necho malicious", "text/plain"),
        ("shell.php", b"<?php system($_GET['cmd']); ?>", "application/php"),
        ("exploit.js", b"eval(atob('malicious_code'))", "application/javascript")
    ]
    
    for filename, content, mimetype in malicious_files:
        files = {"file": (filename, content, mimetype)}
        response = requests.post(
            f"{api_base}/api/rfp/upload",
            headers=headers,
            files=files
        )
        
        # Should reject malicious file types
        assert response.status_code in [400, 415], f"Malicious file {filename} should be rejected"
    
    # Test 2: Oversized files should be rejected
    large_content = b"A" * (50 * 1024 * 1024)  # 50MB
    files = {"file": ("large.pdf", large_content, "application/pdf")}
    response = requests.post(
        f"{api_base}/api/rfp/upload",
        headers=headers,
        files=files
    )
    assert response.status_code == 413, "Oversized file should be rejected"
    
    # Test 3: Valid file should be accepted
    valid_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
    files = {"file": ("valid.pdf", valid_content, "application/pdf")}
    response = requests.post(
        f"{api_base}/api/rfp/upload",
        headers=headers,
        files=files
    )
    assert response.status_code == 200, "Valid PDF file should be accepted"
```

#### 3. Data Privacy and Compliance
```python
# tests/security/test_data_privacy_compliance.py
@pytest.mark.security
@pytest.mark.compliance
def test_data_encryption_at_rest():
    """Test that sensitive data is encrypted in the database."""
    from tests.utils.docker_config import get_test_db_connection
    
    db_conn = get_test_db_connection()
    cursor = db_conn.cursor()
    
    # Create test data with sensitive information
    sensitive_data = {
        "company_name": "Test Company Inc",
        "email": "sensitive@testcompany.com",
        "phone": "+1-555-123-4567",
        "tax_id": "12-3456789",
        "contact_notes": "Confidential supplier relationship details"
    }
    
    # Insert data through API
    api_base = get_test_api_url()
    token = generate_test_token(permissions=["supplier:write"])
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{api_base}/api/suppliers/create",
        headers=headers,
        json=sensitive_data
    )
    
    assert response.status_code == 200
    supplier_id = response.json()["supplier_id"]
    
    # Check database storage - sensitive fields should be encrypted
    cursor.execute(
        "SELECT email, phone, tax_id, contact_notes FROM suppliers WHERE id = %s",
        (supplier_id,)
    )
    stored_data = cursor.fetchone()
    
    # Verify that sensitive fields are not stored in plain text
    assert stored_data[0] != sensitive_data["email"]  # Email should be encrypted
    assert stored_data[1] != sensitive_data["phone"]  # Phone should be encrypted  
    assert stored_data[2] != sensitive_data["tax_id"]  # Tax ID should be encrypted
    assert stored_data[3] != sensitive_data["contact_notes"]  # Notes should be encrypted
    
    # Verify that data can be retrieved correctly through API
    get_response = requests.get(f"{api_base}/api/suppliers/{supplier_id}", headers=headers)
    assert get_response.status_code == 200
    
    retrieved_data = get_response.json()
    assert retrieved_data["email"] == sensitive_data["email"]  # Should be decrypted
    assert retrieved_data["phone"] == sensitive_data["phone"]
    
    cursor.close()
    db_conn.close()

@pytest.mark.compliance
def test_gdpr_data_deletion():
    """Test GDPR-compliant data deletion."""
    api_base = get_test_api_url()
    token = generate_test_token(permissions=["supplier:write", "supplier:delete"])
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create supplier with personal data
    supplier_data = {
        "company_name": "GDPR Test Company",
        "contact_person": "John Doe",
        "email": "john.doe@gdprtest.com",
        "phone": "+1-555-987-6543",
        "address": "123 Privacy Street, EU"
    }
    
    create_response = requests.post(
        f"{api_base}/api/suppliers/create",
        headers=headers,
        json=supplier_data
    )
    assert create_response.status_code == 200
    supplier_id = create_response.json()["supplier_id"]
    
    # Create related data (quotations, RFPs, etc.)
    quotation_response = requests.post(
        f"{api_base}/api/quotations/create",
        headers=headers,
        json={
            "supplier_id": supplier_id,
            "rfp_id": "test-rfp-123",
            "items": [{"name": "Test Item", "price": 100}]
        }
    )
    assert quotation_response.status_code == 200
    
    # Request GDPR data deletion
    deletion_response = requests.delete(
        f"{api_base}/api/suppliers/{supplier_id}/gdpr-delete",
        headers=headers
    )
    assert deletion_response.status_code == 200
    
    # Verify supplier data is completely removed
    get_response = requests.get(f"{api_base}/api/suppliers/{supplier_id}", headers=headers)
    assert get_response.status_code == 404
    
    # Verify related data is anonymized or removed
    from tests.utils.docker_config import get_test_db_connection
    db_conn = get_test_db_connection()
    cursor = db_conn.cursor()
    
    # Check quotations table - should be anonymized
    cursor.execute("SELECT supplier_info FROM quotations WHERE supplier_id = %s", (supplier_id,))
    quotation_data = cursor.fetchone()
    
    if quotation_data:
        # Supplier info should be anonymized
        assert "john.doe@gdprtest.com" not in str(quotation_data[0])
        assert "John Doe" not in str(quotation_data[0])
    
    cursor.close()
    db_conn.close()

@pytest.mark.compliance
def test_audit_logging():
    """Test comprehensive audit logging for compliance."""
    api_base = get_test_api_url()
    token = generate_test_token(permissions=["supplier:write"], user_id="audit-test-user")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Perform auditable actions
    actions = [
        {
            "action": "CREATE",
            "endpoint": "/api/suppliers/create",
            "method": "POST",
            "data": {"company_name": "Audit Test Company"}
        },
        {
            "action": "READ", 
            "endpoint": "/api/suppliers/search",
            "method": "POST",
            "data": {"query": "audit test"}
        }
    ]
    
    for action_info in actions:
        if action_info["method"] == "POST":
            response = requests.post(
                f"{api_base}{action_info['endpoint']}", 
                headers=headers,
                json=action_info["data"]
            )
        else:
            response = requests.get(f"{api_base}{action_info['endpoint']}", headers=headers)
        
        assert response.status_code in [200, 201]
    
    # Verify audit logs
    from tests.utils.docker_config import get_test_db_connection
    db_conn = get_test_db_connection()
    cursor = db_conn.cursor()
    
    cursor.execute("""
        SELECT action_type, user_id, resource_type, timestamp, ip_address
        FROM audit_logs 
        WHERE user_id = %s 
        ORDER BY timestamp DESC
    """, ("audit-test-user",))
    
    audit_records = cursor.fetchall()
    assert len(audit_records) >= len(actions)
    
    # Verify audit record structure
    for record in audit_records:
        assert record[0] is not None  # action_type
        assert record[1] == "audit-test-user"  # user_id
        assert record[2] is not None  # resource_type
        assert record[3] is not None  # timestamp
        # IP address may be None in test environment
    
    cursor.close()
    db_conn.close()
```

## Docker Test Infrastructure Setup

### Test Infrastructure Architecture
```yaml
# tests/utils/docker-compose.test.yml
version: '3.8'

services:
  # Core Database Services
  postgres_test:
    image: postgres:15
    environment:
      POSTGRES_DB: horme_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "${TEST_POSTGRES_PORT:-5433}:5432"
    volumes:
      - ./init-scripts:/docker-entrypoint-initdb.d
      - postgres_test_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d horme_test"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis_test:
    image: redis:7-alpine
    ports:
      - "${TEST_REDIS_PORT:-6380}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Object Storage
  minio_test:
    image: minio/minio:latest
    environment:
      MINIO_ACCESS_KEY: testuser
      MINIO_SECRET_KEY: testpass123
    ports:
      - "${TEST_MINIO_PORT:-9001}:9000"
    command: server /data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # Search Engine
  elasticsearch_test:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "${TEST_ELASTICSEARCH_PORT:-9201}:9200"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # AI/ML Services
  ollama_test:
    image: ollama/ollama:latest
    ports:
      - "${TEST_OLLAMA_PORT:-11435}:11434"
    volumes:
      - ollama_test_data:/root/.ollama
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Application Services
  api_test:
    build:
      context: ../../
      dockerfile: Dockerfile.api
    environment:
      DATABASE_URL: postgresql://test_user:test_pass@postgres_test:5432/horme_test
      REDIS_URL: redis://redis_test:6379/0
      MINIO_ENDPOINT: minio_test:9000
      ELASTICSEARCH_URL: http://elasticsearch_test:9200
      OLLAMA_URL: http://ollama_test:11434
      ENVIRONMENT: test
    ports:
      - "${TEST_API_PORT:-8001}:8000"
    depends_on:
      postgres_test:
        condition: service_healthy
      redis_test:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  mcp_test:
    build:
      context: ../../
      dockerfile: Dockerfile.mcp-lightweight
    environment:
      DATABASE_URL: postgresql://test_user:test_pass@postgres_test:5432/horme_test
      REDIS_URL: redis://redis_test:6379/0
      MCP_PORT: 3002
      ENVIRONMENT: test
    ports:
      - "${TEST_MCP_PORT:-3003}:3002"
    depends_on:
      postgres_test:
        condition: service_healthy
      redis_test:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3002/health"]
      interval: 30s
      timeout: 10s
      retries: 5

volumes:
  postgres_test_data:
  ollama_test_data:

networks:
  default:
    name: horme_test_network
```

### Automated Test Environment Setup
```python
# tests/utils/setup_test_infrastructure.py
import docker
import time
import psycopg2
import redis
import requests
import subprocess
import os
from typing import Dict, List, Optional

class TestInfrastructureManager:
    """Manage Docker-based test infrastructure."""
    
    def __init__(self, project_name: str = "horme_test"):
        self.project_name = project_name
        self.docker_client = docker.from_env()
        self.services_config = self._load_services_config()
    
    def setup_complete_infrastructure(self) -> Dict[str, str]:
        """Set up complete test infrastructure and return connection details."""
        print("🚀 Setting up test infrastructure...")
        
        # Step 1: Clean up any existing test containers
        self._cleanup_existing_containers()
        
        # Step 2: Start infrastructure services
        self._start_infrastructure_services()
        
        # Step 3: Wait for all services to be healthy
        self._wait_for_services_healthy()
        
        # Step 4: Initialize services with test data
        self._initialize_services()
        
        # Step 5: Return connection details
        connection_details = self._get_connection_details()
        
        print("✅ Test infrastructure ready!")
        return connection_details
    
    def _start_infrastructure_services(self):
        """Start all required infrastructure services."""
        compose_file = "tests/utils/docker-compose.test.yml"
        
        # Start services in dependency order
        service_groups = [
            ["postgres_test", "redis_test"],  # Core services
            ["minio_test", "elasticsearch_test"],  # Storage services
            ["ollama_test"],  # AI services
            ["api_test", "mcp_test"]  # Application services
        ]
        
        for group in service_groups:
            print(f"Starting services: {', '.join(group)}")
            
            cmd = ["docker-compose", "-f", compose_file, "up", "-d"] + group
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to start services {group}: {result.stderr}")
            
            # Wait between groups to ensure proper startup order
            time.sleep(10)
    
    def _wait_for_services_healthy(self, timeout: int = 300):
        """Wait for all services to be healthy."""
        services = [
            "postgres_test", "redis_test", "minio_test", 
            "elasticsearch_test", "ollama_test", "api_test", "mcp_test"
        ]
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            healthy_services = []
            
            for service in services:
                if self._is_service_healthy(service):
                    healthy_services.append(service)
            
            print(f"Healthy services: {len(healthy_services)}/{len(services)}")
            
            if len(healthy_services) == len(services):
                print("All services are healthy!")
                return
            
            time.sleep(10)
        
        raise TimeoutError("Services did not become healthy within timeout")
    
    def _is_service_healthy(self, service_name: str) -> bool:
        """Check if a specific service is healthy."""
        try:
            containers = self.docker_client.containers.list(
                filters={"name": f"{self.project_name}_{service_name}"}
            )
            
            if not containers:
                return False
            
            container = containers[0]
            health = container.attrs.get("State", {}).get("Health", {})
            
            if health:
                return health.get("Status") == "healthy"
            else:
                # If no health check defined, assume healthy if running
                return container.status == "running"
                
        except Exception as e:
            print(f"Error checking health of {service_name}: {e}")
            return False
    
    def _initialize_services(self):
        """Initialize services with test data and configurations."""
        # Initialize PostgreSQL with test schema and data
        self._initialize_postgresql()
        
        # Initialize Elasticsearch with test indices
        self._initialize_elasticsearch()
        
        # Pull required Ollama models
        self._initialize_ollama()
        
        # Initialize MinIO with test buckets
        self._initialize_minio()
    
    def _initialize_postgresql(self):
        """Initialize PostgreSQL with test schema and data."""
        conn_details = self._get_postgres_connection_details()
        
        try:
            conn = psycopg2.connect(**conn_details)
            cursor = conn.cursor()
            
            # Run initialization scripts
            init_scripts = [
                "tests/utils/init-scripts/01-create-test-database.sql",
                "tests/utils/init-scripts/02-seed-test-data.sql"
            ]
            
            for script_path in init_scripts:
                if os.path.exists(script_path):
                    with open(script_path, 'r') as script_file:
                        cursor.execute(script_file.read())
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ PostgreSQL initialized with test data")
            
        except Exception as e:
            print(f"❌ PostgreSQL initialization failed: {e}")
            raise
    
    def _initialize_elasticsearch(self):
        """Initialize Elasticsearch with test indices."""
        es_url = f"http://localhost:{self._get_port('elasticsearch_test')}"
        
        try:
            # Create test indices
            indices = ["products", "suppliers", "rfps", "quotations"]
            
            for index in indices:
                response = requests.put(f"{es_url}/{index}", json={
                    "mappings": {
                        "properties": {
                            "name": {"type": "text"},
                            "description": {"type": "text"},
                            "category": {"type": "keyword"},
                            "created_at": {"type": "date"}
                        }
                    }
                })
                response.raise_for_status()
            
            print("✅ Elasticsearch initialized with test indices")
            
        except Exception as e:
            print(f"❌ Elasticsearch initialization failed: {e}")
            raise
    
    def _initialize_ollama(self):
        """Pull required Ollama models for testing."""
        ollama_url = f"http://localhost:{self._get_port('ollama_test')}"
        
        try:
            # Pull required models (lightweight versions for testing)
            models = ["llama3.2:1b", "nomic-embed-text"]
            
            for model in models:
                print(f"Pulling Ollama model: {model}")
                response = requests.post(f"{ollama_url}/api/pull", json={"name": model})
                
                if response.status_code == 200:
                    # Wait for pull completion (simplified)
                    time.sleep(30)
                
            print("✅ Ollama models ready")
            
        except Exception as e:
            print(f"❌ Ollama initialization failed: {e}")
            # Don't raise - Ollama failures shouldn't block other tests
    
    def _initialize_minio(self):
        """Initialize MinIO with test buckets."""
        try:
            from minio import Minio
            
            client = Minio(
                f"localhost:{self._get_port('minio_test')}",
                access_key="testuser",
                secret_key="testpass123",
                secure=False
            )
            
            # Create test buckets
            buckets = ["documents", "reports", "uploads"]
            
            for bucket in buckets:
                if not client.bucket_exists(bucket):
                    client.make_bucket(bucket)
            
            print("✅ MinIO initialized with test buckets")
            
        except Exception as e:
            print(f"❌ MinIO initialization failed: {e}")
            raise
    
    def _get_connection_details(self) -> Dict[str, str]:
        """Get connection details for all services."""
        return {
            "database_url": f"postgresql://test_user:test_pass@localhost:{self._get_port('postgres_test')}/horme_test",
            "redis_url": f"redis://localhost:{self._get_port('redis_test')}/0",
            "api_url": f"http://localhost:{self._get_port('api_test')}",
            "mcp_websocket_url": f"ws://localhost:{self._get_port('mcp_test')}/ws",
            "elasticsearch_url": f"http://localhost:{self._get_port('elasticsearch_test')}",
            "minio_endpoint": f"localhost:{self._get_port('minio_test')}",
            "ollama_url": f"http://localhost:{self._get_port('ollama_test')}"
        }
    
    def cleanup_infrastructure(self):
        """Clean up all test infrastructure."""
        print("🧹 Cleaning up test infrastructure...")
        
        compose_file = "tests/utils/docker-compose.test.yml"
        
        # Stop and remove containers
        subprocess.run([
            "docker-compose", "-f", compose_file, "down", "-v", "--remove-orphans"
        ], capture_output=True)
        
        print("✅ Test infrastructure cleaned up")

# Test execution script
def main():
    """Main test infrastructure setup script."""
    import sys
    
    manager = TestInfrastructureManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        manager.cleanup_infrastructure()
    else:
        try:
            connection_details = manager.setup_complete_infrastructure()
            
            # Save connection details for tests
            import json
            with open("tests/.test-connections.json", "w") as f:
                json.dump(connection_details, f, indent=2)
            
            print("\n🎯 Test infrastructure is ready!")
            print("Connection details saved to tests/.test-connections.json")
            
        except Exception as e:
            print(f"❌ Infrastructure setup failed: {e}")
            manager.cleanup_infrastructure()
            sys.exit(1)

if __name__ == "__main__":
    main()
```

## Test Execution Framework and CI Integration

### Test Execution Script
```python
# tests/run_comprehensive_tests.py
import subprocess
import sys
import json
import time
import os
from typing import List, Dict, Optional
from tests.utils.setup_test_infrastructure import TestInfrastructureManager

class ComprehensiveTestRunner:
    """Run complete 3-tier test suite with infrastructure management."""
    
    def __init__(self, enable_infrastructure: bool = True):
        self.enable_infrastructure = enable_infrastructure
        self.infrastructure_manager = TestInfrastructureManager() if enable_infrastructure else None
        self.test_results = {}
    
    def run_complete_test_suite(self) -> Dict[str, any]:
        """Run the complete 3-tier test suite."""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 60)
        
        try:
            # Step 1: Setup infrastructure if required
            if self.enable_infrastructure:
                print("\n📋 Phase 1: Infrastructure Setup")
                self._setup_test_infrastructure()
            
            # Step 2: Run Tier 1 - Unit Tests
            print("\n🔬 Phase 2: Tier 1 - Unit Tests")
            tier1_results = self._run_tier1_tests()
            
            # Step 3: Run Tier 2 - Integration Tests (requires infrastructure)
            if self.enable_infrastructure:
                print("\n🔧 Phase 3: Tier 2 - Integration Tests")
                tier2_results = self._run_tier2_tests()
            else:
                tier2_results = {"skipped": "Infrastructure not enabled"}
            
            # Step 4: Run Tier 3 - E2E Tests (requires infrastructure)
            if self.enable_infrastructure:
                print("\n🎯 Phase 4: Tier 3 - End-to-End Tests")
                tier3_results = self._run_tier3_tests()
            else:
                tier3_results = {"skipped": "Infrastructure not enabled"}
            
            # Step 5: Run Performance Tests
            if self.enable_infrastructure:
                print("\n⚡ Phase 5: Performance Tests")
                performance_results = self._run_performance_tests()
            else:
                performance_results = {"skipped": "Infrastructure not enabled"}
            
            # Step 6: Run Security Tests
            if self.enable_infrastructure:
                print("\n🔒 Phase 6: Security Tests")
                security_results = self._run_security_tests()
            else:
                security_results = {"skipped": "Infrastructure not enabled"}
            
            # Compile final results
            final_results = {
                "tier1_unit": tier1_results,
                "tier2_integration": tier2_results,
                "tier3_e2e": tier3_results,
                "performance": performance_results,
                "security": security_results,
                "overall_success": self._calculate_overall_success([
                    tier1_results, tier2_results, tier3_results,
                    performance_results, security_results
                ])
            }
            
            # Generate comprehensive report
            self._generate_test_report(final_results)
            
            return final_results
            
        finally:
            # Cleanup infrastructure
            if self.enable_infrastructure and self.infrastructure_manager:
                print("\n🧹 Cleanup: Removing Test Infrastructure")
                self.infrastructure_manager.cleanup_infrastructure()
    
    def _setup_test_infrastructure(self):
        """Set up complete test infrastructure."""
        try:
            connection_details = self.infrastructure_manager.setup_complete_infrastructure()
            
            # Verify all services are accessible
            self._verify_infrastructure_connectivity(connection_details)
            
            print("✅ Test infrastructure ready and verified")
            
        except Exception as e:
            print(f"❌ Infrastructure setup failed: {e}")
            raise
    
    def _verify_infrastructure_connectivity(self, connections: Dict[str, str]):
        """Verify that all infrastructure services are accessible."""
        import requests
        import psycopg2
        import redis
        
        # Test database connectivity
        try:
            conn = psycopg2.connect(connections["database_url"])
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            print("  ✅ PostgreSQL connection verified")
        except Exception as e:
            raise RuntimeError(f"PostgreSQL connection failed: {e}")
        
        # Test Redis connectivity
        try:
            r = redis.from_url(connections["redis_url"])
            r.ping()
            print("  ✅ Redis connection verified")
        except Exception as e:
            raise RuntimeError(f"Redis connection failed: {e}")
        
        # Test API connectivity
        try:
            response = requests.get(f"{connections['api_url']}/health", timeout=10)
            response.raise_for_status()
            print("  ✅ API service verified")
        except Exception as e:
            raise RuntimeError(f"API service connection failed: {e}")
    
    def _run_tier1_tests(self) -> Dict[str, any]:
        """Run Tier 1 unit tests."""
        print("Running unit tests (no external dependencies)...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/unit/",
            "-v",
            "--timeout=1",  # 1 second timeout per test
            "--tb=short",
            "--json-report",
            "--json-report-file=tests/reports/tier1_results.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": "< 30 seconds target"
        }
    
    def _run_tier2_tests(self) -> Dict[str, any]:
        """Run Tier 2 integration tests with real infrastructure."""
        print("Running integration tests (real Docker services, NO MOCKING)...")
        
        cmd = [
            "python", "-m", "pytest", 
            "tests/integration/",
            "-v",
            "--timeout=5",  # 5 second timeout per test
            "-m", "integration",
            "--tb=short",
            "--json-report",
            "--json-report-file=tests/reports/tier2_results.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": "< 5 minutes target"
        }
    
    def _run_tier3_tests(self) -> Dict[str, any]:
        """Run Tier 3 end-to-end tests with complete workflows."""
        print("Running end-to-end tests (complete business workflows)...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/e2e/",
            "-v", 
            "--timeout=10",  # 10 second timeout per test
            "-m", "e2e",
            "--tb=short",
            "--json-report",
            "--json-report-file=tests/reports/tier3_results.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout, 
            "stderr": result.stderr,
            "duration": "< 15 minutes target"
        }
    
    def _run_performance_tests(self) -> Dict[str, any]:
        """Run performance and load tests."""
        print("Running performance tests (SLA validation, load testing)...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/performance/",
            "-v",
            "-m", "performance or load_test",
            "--tb=short",
            "--json-report", 
            "--json-report-file=tests/reports/performance_results.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "performance_targets_met": result.returncode == 0
        }
    
    def _run_security_tests(self) -> Dict[str, any]:
        """Run security and compliance tests."""
        print("Running security tests (authentication, input validation, compliance)...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/security/",
            "-v",
            "-m", "security or compliance", 
            "--tb=short",
            "--json-report",
            "--json-report-file=tests/reports/security_results.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "security_validated": result.returncode == 0
        }
    
    def _calculate_overall_success(self, results: List[Dict[str, any]]) -> bool:
        """Calculate overall test success."""
        for result in results:
            if isinstance(result, dict) and "passed" in result:
                if not result["passed"]:
                    return False
        return True
    
    def _generate_test_report(self, results: Dict[str, any]):
        """Generate comprehensive test report."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"tests/reports/comprehensive_test_report_{timestamp}.json"
        
        # Ensure reports directory exists
        os.makedirs("tests/reports", exist_ok=True)
        
        # Add metadata
        report_data = {
            "timestamp": timestamp,
            "test_strategy": "3-Tier Testing Strategy",
            "infrastructure_used": self.enable_infrastructure,
            "results": results
        }
        
        # Save JSON report
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate human-readable summary
        self._generate_summary_report(report_data, timestamp)
        
        print(f"\n📊 Comprehensive test report saved: {report_file}")
    
    def _generate_summary_report(self, data: Dict[str, any], timestamp: str):
        """Generate human-readable summary report."""
        summary_file = f"tests/reports/test_summary_{timestamp}.txt"
        
        with open(summary_file, 'w') as f:
            f.write("COMPREHENSIVE 3-TIER TEST RESULTS SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Test Execution Time: {timestamp}\n")
            f.write(f"Infrastructure Used: {'Yes' if self.enable_infrastructure else 'No'}\n\n")
            
            results = data["results"]
            
            # Tier 1 Results
            f.write("TIER 1 - UNIT TESTS\n")
            f.write("-" * 20 + "\n")
            tier1 = results.get("tier1_unit", {})
            f.write(f"Status: {'PASSED' if tier1.get('passed') else 'FAILED'}\n")
            f.write(f"Target: <1 second per test, <30 seconds total\n\n")
            
            # Tier 2 Results
            f.write("TIER 2 - INTEGRATION TESTS (NO MOCKING)\n")
            f.write("-" * 40 + "\n")
            tier2 = results.get("tier2_integration", {})
            if "skipped" in tier2:
                f.write("Status: SKIPPED (no infrastructure)\n\n")
            else:
                f.write(f"Status: {'PASSED' if tier2.get('passed') else 'FAILED'}\n")
                f.write(f"Target: <5 seconds per test, <5 minutes total\n\n")
            
            # Tier 3 Results
            f.write("TIER 3 - END-TO-END TESTS (COMPLETE WORKFLOWS)\n") 
            f.write("-" * 50 + "\n")
            tier3 = results.get("tier3_e2e", {})
            if "skipped" in tier3:
                f.write("Status: SKIPPED (no infrastructure)\n\n")
            else:
                f.write(f"Status: {'PASSED' if tier3.get('passed') else 'FAILED'}\n")
                f.write(f"Target: <10 seconds per test, <15 minutes total\n\n")
            
            # Performance Results
            f.write("PERFORMANCE VALIDATION\n")
            f.write("-" * 22 + "\n")
            perf = results.get("performance", {})
            if "skipped" in perf:
                f.write("Status: SKIPPED (no infrastructure)\n\n")
            else:
                f.write(f"Status: {'PASSED' if perf.get('performance_targets_met') else 'FAILED'}\n")
                f.write("SLA Targets: API <500ms, Throughput >50 RPS\n\n")
            
            # Security Results
            f.write("SECURITY & COMPLIANCE\n")
            f.write("-" * 21 + "\n")
            sec = results.get("security", {})
            if "skipped" in sec:
                f.write("Status: SKIPPED (no infrastructure)\n\n")
            else:
                f.write(f"Status: {'PASSED' if sec.get('security_validated') else 'FAILED'}\n")
                f.write("Validates: Authentication, Input validation, GDPR compliance\n\n")
            
            # Overall Result
            f.write("OVERALL RESULT\n")
            f.write("-" * 14 + "\n")
            overall_success = results.get("overall_success", False)
            f.write(f"Production Ready: {'YES ✅' if overall_success else 'NO ❌'}\n")
            
            if overall_success:
                f.write("\n🎉 SYSTEM VALIDATED FOR PRODUCTION DEPLOYMENT\n")
                f.write("All tiers passed with real infrastructure and data.\n")
            else:
                f.write("\n⚠️  SYSTEM REQUIRES FIXES BEFORE PRODUCTION\n")
                f.write("Check individual test results for failure details.\n")
        
        print(f"📋 Test summary saved: {summary_file}")

# CLI interface
def main():
    """Main CLI interface for test execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive 3-tier test suite")
    parser.add_argument("--no-infrastructure", action="store_true", 
                       help="Skip infrastructure setup (unit tests only)")
    parser.add_argument("--tier", choices=["1", "2", "3", "all"], default="all",
                       help="Run specific tier only")
    
    args = parser.parse_args()
    
    if args.tier != "all" and args.no_infrastructure and args.tier in ["2", "3"]:
        print("❌ Error: Tier 2 and 3 tests require infrastructure")
        sys.exit(1)
    
    runner = ComprehensiveTestRunner(enable_infrastructure=not args.no_infrastructure)
    
    try:
        if args.tier == "1":
            results = {"tier1_unit": runner._run_tier1_tests()}
        elif args.tier == "2":
            runner._setup_test_infrastructure()
            results = {"tier2_integration": runner._run_tier2_tests()}
        elif args.tier == "3":
            runner._setup_test_infrastructure() 
            results = {"tier3_e2e": runner._run_tier3_tests()}
        else:
            results = runner.run_complete_test_suite()
        
        # Exit with proper code
        overall_success = results.get("overall_success", False)
        if args.tier != "all":
            # For individual tiers, check the specific result
            tier_result = list(results.values())[0]
            overall_success = tier_result.get("passed", False)
        
        sys.exit(0 if overall_success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### CI/CD Integration
```yaml
# .github/workflows/comprehensive-testing.yml
name: Comprehensive 3-Tier Testing

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  # Tier 1: Unit Tests (fastest, no infrastructure)
  tier1-unit-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
    
    - name: Run Tier 1 Unit Tests
      run: |
        python tests/run_comprehensive_tests.py --tier 1 --no-infrastructure
    
    - name: Upload Unit Test Results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: tier1-test-results
        path: tests/reports/

  # Tier 2: Integration Tests (Docker infrastructure required)
  tier2-integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    needs: tier1-unit-tests
    
    services:
      docker:
        image: docker:dind
        options: --privileged
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
        pip install docker-compose
    
    - name: Start Docker daemon
      run: |
        sudo systemctl start docker
        sudo usermod -aG docker $USER
    
    - name: Run Tier 2 Integration Tests
      run: |
        python tests/run_comprehensive_tests.py --tier 2
    
    - name: Upload Integration Test Results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: tier2-test-results
        path: tests/reports/
    
    - name: Cleanup Docker Resources
      if: always()
      run: |
        docker system prune -af

  # Tier 3: End-to-End Tests (complete infrastructure)
  tier3-e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    needs: [tier1-unit-tests, tier2-integration-tests]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
        pip install docker-compose
    
    - name: Free up disk space
      run: |
        docker system prune -af
        sudo apt-get clean
        df -h
    
    - name: Run Tier 3 E2E Tests
      run: |
        python tests/run_comprehensive_tests.py --tier 3
    
    - name: Upload E2E Test Results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: tier3-test-results
        path: tests/reports/

  # Complete Test Suite (all tiers + performance + security)
  complete-test-suite:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    needs: [tier1-unit-tests, tier2-integration-tests, tier3-e2e-tests]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
        pip install docker-compose
    
    - name: Run Complete Test Suite
      run: |
        python tests/run_comprehensive_tests.py --tier all
    
    - name: Upload Complete Test Results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: complete-test-results
        path: tests/reports/
    
    - name: Generate Production Readiness Report
      if: always()
      run: |
        python tests/generate_production_readiness_report.py
    
    - name: Comment PR with Results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          
          // Read test summary
          const summaryPath = 'tests/reports/test_summary_latest.txt';
          if (fs.existsSync(summaryPath)) {
            const summary = fs.readFileSync(summaryPath, 'utf8');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🧪 Comprehensive Test Results\n\n\`\`\`\n${summary}\n\`\`\``
            });
          }

  # Production Deployment Gate
  production-readiness-gate:
    runs-on: ubuntu-latest
    needs: complete-test-suite
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Download Test Results
      uses: actions/download-artifact@v3
      with:
        name: complete-test-results
        path: test-results/
    
    - name: Validate Production Readiness
      run: |
        # Check if all tests passed
        if [ -f "test-results/comprehensive_test_report_latest.json" ]; then
          OVERALL_SUCCESS=$(jq -r '.results.overall_success' test-results/comprehensive_test_report_latest.json)
          
          if [ "$OVERALL_SUCCESS" = "true" ]; then
            echo "✅ System validated for production deployment"
            echo "production_ready=true" >> $GITHUB_OUTPUT
          else
            echo "❌ System not ready for production"
            echo "production_ready=false" >> $GITHUB_OUTPUT
            exit 1
          fi
        else
          echo "❌ Test results not found"
          exit 1
        fi
    
    - name: Create Production Release
      if: steps.validate.outputs.production_ready == 'true'
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: production-ready-${{ github.sha }}
        release_name: Production Ready Build
        body: |
          🎉 This build has passed all 3-tier tests and is validated for production deployment.
          
          **Test Results:**
          - ✅ Tier 1: Unit tests with business logic validation
          - ✅ Tier 2: Integration tests with real infrastructure (NO MOCKING)
          - ✅ Tier 3: End-to-end tests with complete workflows
          - ✅ Performance: SLA validation and load testing
          - ✅ Security: Authentication, input validation, compliance
          
          **Infrastructure Validated:**
          - Real PostgreSQL database operations
          - Real Redis caching and sessions
          - Real file I/O and document processing
          - Real API communication and WebSocket connections
          - Real AI/ML model integration
        draft: false
        prerelease: false
```

## Summary and Implementation Roadmap

### Key Success Metrics

#### Production Readiness Indicators
- **Tier 1**: >95% pass rate, <30 seconds total execution
- **Tier 2**: >95% pass rate, <5 minutes total execution  
- **Tier 3**: >90% pass rate, <15 minutes total execution
- **Performance**: All SLA targets met under realistic load
- **Security**: 100% pass rate on authentication, validation, compliance

#### Real-World Validation Proof Points
- **NO MOCK DATA**: All tests use real business data and scenarios
- **NO MOCKING**: Tiers 2-3 use actual Docker infrastructure
- **Complete Workflows**: E2E tests validate entire business processes
- **Production Parity**: Test environment mirrors production architecture
- **Compliance Verified**: GDPR, security, audit requirements validated

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Analyze current testing gaps and requirements", "status": "completed", "activeForm": "Analyzed current testing gaps and requirements"}, {"content": "Design Tier 1 unit testing strategy for business logic", "status": "completed", "activeForm": "Designed Tier 1 unit testing strategy for business logic"}, {"content": "Design Tier 2 integration testing strategy with real infrastructure", "status": "completed", "activeForm": "Designed Tier 2 integration testing strategy with real infrastructure"}, {"content": "Design Tier 3 E2E testing strategy for complete workflows", "status": "completed", "activeForm": "Designed Tier 3 E2E testing strategy for complete workflows"}, {"content": "Create test data management strategy with real data", "status": "completed", "activeForm": "Created test data management strategy with real data"}, {"content": "Define performance benchmarks and load testing approach", "status": "completed", "activeForm": "Defined performance benchmarks and load testing approach"}, {"content": "Design security and compliance validation tests", "status": "completed", "activeForm": "Designed security and compliance validation tests"}, {"content": "Create Docker test infrastructure setup", "status": "completed", "activeForm": "Created Docker test infrastructure setup"}, {"content": "Implement test execution framework and CI integration", "status": "completed", "activeForm": "Implemented test execution framework and CI integration"}]