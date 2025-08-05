"""
Integration Tests for DataFlow Models - FOUND-003: DataFlow Models

Tests for real PostgreSQL database operations and auto-generated CRUD nodes.
Validates database schema creation, relationships, and DataFlow node generation.

Tier 2 Testing: Real PostgreSQL connections, NO MOCKING, <5s timeout
Requires: ./tests/utils/test-env up && ./tests/utils/test-env status
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

# DataFlow and Kailash SDK imports
# Windows compatibility patch
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import windows_sdk_compatibility  # Apply Windows compatibility for Kailash SDK

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Import the DataFlow models and database instance
from src.new_project.core.models import (
    db, Product, ProductCategory, UNSPSCCode, ETIMClass,
    SafetyStandard, ComplianceRequirement, Vendor, ProductPricing,
    InventoryLevel, UserProfile, SkillAssessment
)


@pytest.fixture(scope="module")
async def setup_test_database():
    """Setup test database connection and create tables."""
    # Ensure test database is configured
    test_db_url = "postgresql://test_user:test_password@localhost:5432/test_horme_db"
    
    # Initialize DataFlow with test database
    db.configure(
        database_url=test_db_url,
        pool_size=5,
        pool_max_overflow=10,
        echo=True,  # Enable SQL logging for debugging
        auto_migrate=True
    )
    
    # Create all tables
    await db.create_all()
    
    yield db
    
    # Cleanup after tests
    await db.drop_all()
    await db.disconnect()


@pytest.fixture
async def clean_database(setup_test_database):
    """Clean database before each test."""
    # Truncate all tables to ensure clean state
    tables_to_clean = [
        'skill_assessments', 'user_profiles', 'inventory_levels',
        'product_pricing', 'compliance_requirements', 'safety_standards',
        'products', 'product_categories', 'unspsc_codes', 'etim_classes',
        'vendors'
    ]
    
    for table in tables_to_clean:
        try:
            await setup_test_database.execute(f"TRUNCATE TABLE {table} CASCADE")
        except Exception:
            pass  # Table might not exist yet
    
    yield setup_test_database


class TestProductModelIntegration:
    """Integration tests for Product model database operations."""
    
    @pytest.mark.asyncio
    async def test_product_model_creates_table(self, clean_database):
        """Test that Product model creates proper PostgreSQL table."""
        # Test table exists
        table_exists_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'products'
        );
        """
        
        result = await clean_database.fetch_val(table_exists_query)
        assert result is True, "Products table should be created"
    
    @pytest.mark.asyncio
    async def test_product_model_auto_generated_nodes(self, clean_database):
        """Test that Product model auto-generates 9 DataFlow nodes."""
        # Test CreateNode
        workflow = WorkflowBuilder()
        workflow.add_node("ProductCreateNode", "create_product", {
            "product_code": "TEST001",
            "name": "Test Product",
            "description": "Test product for integration testing",
            "brand": "Test Brand",
            "model_number": "TM001",
            "unspsc_code": "12345678",
            "etim_class": "EC001",
            "specifications": {"weight": "10kg", "color": "blue"},
            "safety_rating": "A"
        })
        
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "ProductCreateNode should execute successfully"
        assert "create_product" in results, "Create operation should return results"
        
        created_product = results["create_product"]
        assert created_product["product_code"] == "TEST001"
        assert created_product["name"] == "Test Product"
        
        # Store product ID for subsequent tests
        product_id = created_product["id"]
        
        # Test ReadNode
        workflow = WorkflowBuilder()
        workflow.add_node("ProductReadNode", "read_product", {
            "id": product_id
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "ProductReadNode should execute successfully"
        read_product = results["read_product"]
        assert read_product["product_code"] == "TEST001"
        assert read_product["specifications"]["weight"] == "10kg"
        
        # Test UpdateNode
        workflow = WorkflowBuilder()
        workflow.add_node("ProductUpdateNode", "update_product", {
            "id": product_id,
            "name": "Updated Test Product",
            "specifications": {"weight": "15kg", "color": "red"}
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "ProductUpdateNode should execute successfully"
        updated_product = results["update_product"]
        assert updated_product["name"] == "Updated Test Product"
        assert updated_product["specifications"]["weight"] == "15kg"
        
        # Test ListNode
        workflow = WorkflowBuilder()
        workflow.add_node("ProductListNode", "list_products", {
            "limit": 10,
            "offset": 0
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "ProductListNode should execute successfully"
        products_list = results["list_products"]
        assert len(products_list) >= 1, "Should return at least one product"
        
        # Test SearchNode
        workflow = WorkflowBuilder()
        workflow.add_node("ProductSearchNode", "search_products", {
            "query": "Test",
            "fields": ["name", "description"]
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "ProductSearchNode should execute successfully"
        search_results = results["search_products"]
        assert len(search_results) >= 1, "Should find test product"
        
        # Test CountNode
        workflow = WorkflowBuilder()
        workflow.add_node("ProductCountNode", "count_products", {
            "filters": {"brand": "Test Brand"}
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "ProductCountNode should execute successfully"
        count_result = results["count_products"]
        assert count_result >= 1, "Should count at least one product"
        
        # Test ExistsNode
        workflow = WorkflowBuilder()
        workflow.add_node("ProductExistsNode", "product_exists", {
            "product_code": "TEST001"
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "ProductExistsNode should execute successfully"
        exists_result = results["product_exists"]
        assert exists_result is True, "Product should exist"
        
        # Test ValidateNode
        workflow = WorkflowBuilder()
        workflow.add_node("ProductValidateNode", "validate_product", {
            "product_code": "INVALID_CODE_TOO_LONG_FOR_FIELD",
            "name": "",  # Invalid empty name
            "brand": "Test Brand"
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        # Validation should catch errors
        assert "validate_product" in results
        validation_result = results["validate_product"]
        assert validation_result["valid"] is False, "Validation should fail for invalid data"
        
        # Test DeleteNode (soft delete)
        workflow = WorkflowBuilder()
        workflow.add_node("ProductDeleteNode", "delete_product", {
            "id": product_id,
            "soft_delete": True
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "ProductDeleteNode should execute successfully"
        delete_result = results["delete_product"]
        assert delete_result["deleted"] is True, "Product should be soft deleted"
    
    @pytest.mark.asyncio
    async def test_product_jsonb_specifications(self, clean_database):
        """Test Product specifications JSONB field operations."""
        # Create product with complex specifications
        workflow = WorkflowBuilder()
        workflow.add_node("ProductCreateNode", "create_product", {
            "product_code": "JSONB001",
            "name": "JSONB Test Product",
            "description": "Testing JSONB specifications",
            "brand": "JSONB Brand",
            "model_number": "JB001",
            "unspsc_code": "87654321",
            "etim_class": "EC002",
            "specifications": {
                "dimensions": {
                    "length": "100cm",
                    "width": "50cm",
                    "height": "25cm"
                },
                "weight": "15kg",
                "material": "steel",
                "color_options": ["red", "blue", "green"],
                "features": {
                    "waterproof": True,
                    "temperature_range": {
                        "min": "-10°C",
                        "max": "60°C"
                    }
                }
            },
            "safety_rating": "B"
        })
        
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "JSONB product creation should succeed"
        created_product = results["create_product"]
        
        # Verify JSONB structure is preserved
        specs = created_product["specifications"]
        assert specs["dimensions"]["length"] == "100cm"
        assert specs["features"]["waterproof"] is True
        assert "red" in specs["color_options"]
        assert specs["features"]["temperature_range"]["max"] == "60°C"
        
        # Test JSONB queries (PostgreSQL specific)
        # This would use PostgreSQL's JSONB operators
        product_id = created_product["id"]
        
        # Test updating nested JSONB
        workflow = WorkflowBuilder()
        workflow.add_node("ProductUpdateNode", "update_product", {
            "id": product_id,
            "specifications": {
                "dimensions": {
                    "length": "120cm",  # Changed
                    "width": "50cm",
                    "height": "25cm"
                },
                "weight": "15kg",
                "material": "aluminum",  # Changed
                "color_options": ["red", "blue", "green", "yellow"],  # Added
                "features": {
                    "waterproof": True,
                    "temperature_range": {
                        "min": "-20°C",  # Changed
                        "max": "80°C"    # Changed
                    },
                    "uv_resistant": True  # Added
                }
            }
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "JSONB update should succeed"
        updated_product = results["update_product"]
        
        # Verify JSONB updates
        specs = updated_product["specifications"]
        assert specs["dimensions"]["length"] == "120cm"
        assert specs["material"] == "aluminum"
        assert "yellow" in specs["color_options"]
        assert specs["features"]["temperature_range"]["min"] == "-20°C"
        assert specs["features"]["uv_resistant"] is True


class TestClassificationModelIntegration:
    """Integration tests for UNSPSC and ETIM classification models."""
    
    @pytest.mark.asyncio
    async def test_unspsc_model_hierarchical_structure(self, clean_database):
        """Test UNSPSC hierarchical classification structure."""
        # Create UNSPSC hierarchy: Segment -> Family -> Class -> Commodity
        
        # Level 1: Segment (11000000 - Live Plant and Animal Material and Accessories and Supplies)
        workflow = WorkflowBuilder()
        workflow.add_node("UNSPSCCreateNode", "create_segment", {
            "code": "11000000",
            "title": "Live Plant and Animal Material and Accessories and Supplies",
            "description": "Segment level classification",
            "segment": "11",
            "family": "00",
            "class_code": "00",
            "commodity": "00",
            "level": 1
        })
        
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "UNSPSC segment creation should succeed"
        
        # Level 2: Family (11100000 - Live animals)
        workflow = WorkflowBuilder()
        workflow.add_node("UNSPSCCreateNode", "create_family", {
            "code": "11100000",
            "title": "Live animals",
            "description": "Family level classification",
            "segment": "11",
            "family": "10",
            "class_code": "00",
            "commodity": "00",
            "level": 2
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "UNSPSC family creation should succeed"
        
        # Level 3: Class (11101500 - Livestock)
        workflow = WorkflowBuilder()
        workflow.add_node("UNSPSCCreateNode", "create_class", {
            "code": "11101500",
            "title": "Livestock",
            "description": "Class level classification",
            "segment": "11",
            "family": "10",
            "class_code": "15",
            "commodity": "00",
            "level": 3
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "UNSPSC class creation should succeed"
        
        # Level 4: Commodity (11101501 - Cattle)
        workflow = WorkflowBuilder()
        workflow.add_node("UNSPSCCreateNode", "create_commodity", {
            "code": "11101501",
            "title": "Cattle",
            "description": "Commodity level classification",
            "segment": "11",
            "family": "10",
            "class_code": "15",
            "commodity": "01",
            "level": 4
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "UNSPSC commodity creation should succeed"
        
        # Test hierarchical queries
        workflow = WorkflowBuilder()
        workflow.add_node("UNSPSCListNode", "list_by_segment", {
            "filters": {"segment": "11"},
            "order_by": "level"
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "UNSPSC hierarchical query should succeed"
        hierarchy_results = results["list_by_segment"]
        assert len(hierarchy_results) == 4, "Should return all 4 hierarchy levels"
        
        # Verify hierarchy order
        levels = [item["level"] for item in hierarchy_results]
        assert levels == [1, 2, 3, 4], "Results should be ordered by hierarchy level"
    
    @pytest.mark.asyncio
    async def test_etim_model_multi_language_support(self, clean_database):
        """Test ETIM multi-language classification support."""
        # Create ETIM class with multiple languages
        workflow = WorkflowBuilder()
        workflow.add_node("ETIMCreateNode", "create_etim_class", {
            "class_id": "EC010101",
            "name_en": "Electric Motors",
            "name_de": "Elektromotoren",
            "name_fr": "Moteurs électriques",
            "description": "Electric motors for industrial applications",
            "version": "9.0"
        })
        
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "ETIM class creation should succeed"
        created_class = results["create_etim_class"]
        
        # Verify multi-language support
        assert created_class["name_en"] == "Electric Motors"
        assert created_class["name_de"] == "Elektromotoren"
        assert created_class["name_fr"] == "Moteurs électriques"
        
        # Test search in different languages
        workflow = WorkflowBuilder()
        workflow.add_node("ETIMSearchNode", "search_english", {
            "query": "Electric",
            "fields": ["name_en"]
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "English search should succeed"
        english_results = results["search_english"]
        assert len(english_results) >= 1, "Should find English results"
        
        # Test German search
        workflow = WorkflowBuilder()
        workflow.add_node("ETIMSearchNode", "search_german", {
            "query": "Elektro",
            "fields": ["name_de"]
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "German search should succeed"
        german_results = results["search_german"]
        assert len(german_results) >= 1, "Should find German results"


class TestSafetyModelIntegration:
    """Integration tests for safety compliance models."""
    
    @pytest.mark.asyncio
    async def test_safety_compliance_workflow(self, clean_database):
        """Test complete safety compliance workflow."""
        # Create Safety Standard
        workflow = WorkflowBuilder()
        workflow.add_node("SafetyStandardCreateNode", "create_standard", {
            "standard_type": "OSHA",
            "standard_code": "OSHA-1926.95",
            "title": "Personal Protective Equipment",
            "description": "Requirements for personal protective equipment in construction",
            "severity_level": "critical",
            "regulation_text": "Employees working in areas where there is a possible danger...",
            "effective_date": datetime.now()
        })
        
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "Safety standard creation should succeed"
        safety_standard = results["create_standard"]
        standard_id = safety_standard["id"]
        
        # Create Product first (needed for compliance requirement)
        workflow = WorkflowBuilder()
        workflow.add_node("ProductCreateNode", "create_product", {
            "product_code": "SAFETY001",
            "name": "Industrial Helmet",
            "description": "Safety helmet for construction work",
            "brand": "SafetyFirst",
            "model_number": "SF001",
            "unspsc_code": "46181501",
            "etim_class": "EC020301",
            "specifications": {"material": "polycarbonate", "color": "yellow"},
            "safety_rating": "A"
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "Safety product creation should succeed"
        safety_product = results["create_product"]
        product_id = safety_product["id"]
        
        # Create Compliance Requirement linking Product to Safety Standard
        workflow = WorkflowBuilder()
        workflow.add_node("ComplianceRequirementCreateNode", "create_compliance", {
            "product_id": product_id,
            "safety_standard_id": standard_id,
            "requirement_text": "Hard hats must be worn at all times in construction areas",
            "is_mandatory": True,
            "ppe_required": True
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "Compliance requirement creation should succeed"
        compliance_req = results["create_compliance"]
        
        # Verify relationships
        assert compliance_req["product_id"] == product_id
        assert compliance_req["safety_standard_id"] == standard_id
        assert compliance_req["is_mandatory"] is True
        assert compliance_req["ppe_required"] is True
        
        # Test compliance queries
        workflow = WorkflowBuilder()
        workflow.add_node("ComplianceRequirementListNode", "list_compliance", {
            "filters": {"product_id": product_id}
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "Compliance query should succeed"
        compliance_list = results["list_compliance"]
        assert len(compliance_list) >= 1, "Should return compliance requirements"


class TestVendorPricingIntegration:
    """Integration tests for vendor and pricing models."""
    
    @pytest.mark.asyncio
    async def test_multi_vendor_pricing_workflow(self, clean_database):
        """Test multi-vendor pricing and inventory management."""
        # Create Vendors
        vendors_data = [
            {
                "vendor_code": "VENDOR001",
                "company_name": "ABC Industrial Supply",
                "display_name": "ABC Supply",
                "vendor_type": "distributor",
                "contact_email": "sales@abcsupply.com",
                "contact_phone": "+1-555-0001",
                "website_url": "https://abcsupply.com",
                "address": {
                    "street": "123 Industrial Blvd",
                    "city": "Chicago",
                    "state": "IL",
                    "zip": "60601",
                    "country": "USA"
                },
                "payment_terms": "Net 30",
                "credit_rating": "A",
                "is_preferred": True,
                "is_active": True
            },
            {
                "vendor_code": "VENDOR002",
                "company_name": "XYZ Tools Direct",
                "display_name": "XYZ Tools",
                "vendor_type": "manufacturer",
                "contact_email": "orders@xyztools.com",
                "contact_phone": "+1-555-0002",
                "website_url": "https://xyztools.com",
                "address": {
                    "street": "456 Manufacturing Dr",
                    "city": "Detroit",
                    "state": "MI",
                    "zip": "48201",
                    "country": "USA"
                },
                "payment_terms": "Net 15",
                "credit_rating": "B",
                "is_preferred": False,
                "is_active": True
            }
        ]
        
        vendor_ids = []
        runtime = LocalRuntime()
        
        for vendor_data in vendors_data:
            workflow = WorkflowBuilder()
            workflow.add_node("VendorCreateNode", "create_vendor", vendor_data)
            
            results, run_id = runtime.execute(workflow.build())
            
            assert results is not None, f"Vendor {vendor_data['vendor_code']} creation should succeed"
            vendor = results["create_vendor"]
            vendor_ids.append(vendor["id"])
            
            # Verify JSONB address field
            assert vendor["address"]["city"] == vendor_data["address"]["city"]
            assert vendor["address"]["country"] == vendor_data["address"]["country"]
        
        # Create Product for pricing
        workflow = WorkflowBuilder()
        workflow.add_node("ProductCreateNode", "create_product", {
            "product_code": "DRILL001",
            "name": "Professional Drill",
            "description": "18V cordless drill for professional use",
            "brand": "ProTool",
            "model_number": "PT-D18V",
            "unspsc_code": "27112103",
            "etim_class": "EC030201",
            "specifications": {"voltage": "18V", "torque": "65Nm", "battery": "Li-ion"},
            "safety_rating": "A"
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "Product creation should succeed"
        product = results["create_product"]
        product_id = product["id"]
        
        # Create pricing for both vendors
        pricing_data = [
            {
                "product_id": product_id,
                "vendor_id": vendor_ids[0],  # ABC Supply (distributor)
                "vendor_product_code": "ABC-DRILL-001",
                "list_price": Decimal("299.99"),
                "cost_price": Decimal("225.00"),
                "discount_price": Decimal("279.99"),
                "currency": "USD",
                "price_unit": "each",
                "minimum_order_quantity": 1,
                "price_break_quantities": {
                    "5": "275.00",
                    "10": "269.99",
                    "25": "259.99"
                },
                "effective_date": datetime.now(),
                "expiry_date": datetime.now() + timedelta(days=90),
                "is_active": True,
                "last_updated": datetime.now()
            },
            {
                "product_id": product_id,
                "vendor_id": vendor_ids[1],  # XYZ Tools (manufacturer)
                "vendor_product_code": "XYZ-PT-D18V",
                "list_price": Decimal("319.99"),
                "cost_price": Decimal("180.00"),
                "discount_price": Decimal("289.99"),
                "currency": "USD",
                "price_unit": "each",
                "minimum_order_quantity": 2,
                "price_break_quantities": {
                    "10": "285.00",
                    "50": "275.00",
                    "100": "265.00"
                },
                "effective_date": datetime.now(),
                "expiry_date": datetime.now() + timedelta(days=180),
                "is_active": True,
                "last_updated": datetime.now()
            }
        ]
        
        pricing_ids = []
        
        for pricing in pricing_data:
            workflow = WorkflowBuilder()
            workflow.add_node("ProductPricingCreateNode", "create_pricing", pricing)
            
            results, run_id = runtime.execute(workflow.build())
            
            assert results is not None, "Pricing creation should succeed"
            pricing_result = results["create_pricing"]
            pricing_ids.append(pricing_result["id"])
            
            # Verify Decimal precision
            assert pricing_result["list_price"] == str(pricing["list_price"])
            
            # Verify JSONB price breaks
            price_breaks = pricing_result["price_break_quantities"]
            assert "5" in price_breaks or "10" in price_breaks
        
        # Create inventory levels for both vendors
        inventory_data = [
            {
                "product_id": product_id,
                "vendor_id": vendor_ids[0],  # ABC Supply
                "location": "CHICAGO-WH01",
                "quantity_on_hand": 150,
                "quantity_reserved": 25,
                "quantity_on_order": 100,
                "reorder_point": 50,
                "reorder_quantity": 200,
                "lead_time_days": 3,
                "availability_status": "available",
                "last_movement_date": datetime.now(),
                "last_count_date": datetime.now() - timedelta(days=7)
            },
            {
                "product_id": product_id,
                "vendor_id": vendor_ids[1],  # XYZ Tools
                "location": "DETROIT-FACTORY",
                "quantity_on_hand": 500,
                "quantity_reserved": 0,
                "quantity_on_order": 0,
                "reorder_point": 100,
                "reorder_quantity": 1000,
                "lead_time_days": 1,
                "availability_status": "available",
                "last_movement_date": datetime.now(),
                "last_count_date": datetime.now()
            }
        ]
        
        for inventory in inventory_data:
            workflow = WorkflowBuilder()
            workflow.add_node("InventoryLevelCreateNode", "create_inventory", inventory)
            
            results, run_id = runtime.execute(workflow.build())
            
            assert results is not None, "Inventory creation should succeed"
            inventory_result = results["create_inventory"]
            
            # Verify availability calculation
            available_qty = inventory_result["quantity_on_hand"] - inventory_result["quantity_reserved"]
            assert available_qty >= 0, "Available quantity should be non-negative"
        
        # Test multi-vendor queries
        workflow = WorkflowBuilder()
        workflow.add_node("ProductPricingListNode", "list_pricing", {
            "filters": {"product_id": product_id},
            "order_by": "list_price"
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "Multi-vendor pricing query should succeed"
        pricing_list = results["list_pricing"]
        assert len(pricing_list) == 2, "Should return pricing from both vendors"
        
        # Verify pricing comparison
        prices = [Decimal(p["list_price"]) for p in pricing_list]
        assert min(prices) < max(prices), "Vendors should have different pricing"


class TestUserProfileIntegration:
    """Integration tests for user profile and skill assessment models."""
    
    @pytest.mark.asyncio
    async def test_user_skill_assessment_workflow(self, clean_database):
        """Test complete user profile and skill assessment workflow."""
        # Create User Profile
        workflow = WorkflowBuilder()
        workflow.add_node("UserProfileCreateNode", "create_profile", {
            "user_id": 12345,  # External user system ID
            "skill_level": "intermediate",
            "experience_years": 5,
            "safety_certified": True,
            "preferred_brands": ["DeWalt", "Makita", "Milwaukee"],
            "project_types": ["residential_renovation", "commercial_construction", "diy_projects"]
        })
        
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "User profile creation should succeed"
        user_profile = results["create_profile"]
        profile_id = user_profile["id"]
        
        # Verify JSON arrays
        assert "DeWalt" in user_profile["preferred_brands"]
        assert "residential_renovation" in user_profile["project_types"]
        assert len(user_profile["preferred_brands"]) == 3
        
        # Create multiple skill assessments
        skill_assessments = [
            {
                "user_profile_id": profile_id,
                "skill_category": "power_tools",
                "proficiency_score": 85,
                "assessed_date": datetime.now(),
                "assessor_type": "professional",
                "assessment_notes": "Strong understanding of power tool safety and operation",
                "skill_subcategory": "cordless_drills",
                "certification_level": "advanced"
            },
            {
                "user_profile_id": profile_id,
                "skill_category": "hand_tools",
                "proficiency_score": 92,
                "assessed_date": datetime.now(),
                "assessor_type": "professional",
                "assessment_notes": "Excellent precision and technique with hand tools",
                "skill_subcategory": "measuring_tools",
                "certification_level": "expert"
            },
            {
                "user_profile_id": profile_id,
                "skill_category": "electrical",
                "proficiency_score": 65,
                "assessed_date": datetime.now(),
                "assessor_type": "self",
                "assessment_notes": "Basic electrical knowledge, needs improvement",
                "skill_subcategory": "residential_wiring",
                "certification_level": "intermediate"
            },
            {
                "user_profile_id": profile_id,
                "skill_category": "safety",
                "proficiency_score": 95,
                "assessed_date": datetime.now(),
                "assessor_type": "professional",
                "assessment_notes": "Excellent safety awareness and practices",
                "skill_subcategory": "general_safety",
                "certification_level": "expert"
            }
        ]
        
        skill_ids = []
        
        for skill_data in skill_assessments:
            workflow = WorkflowBuilder()
            workflow.add_node("SkillAssessmentCreateNode", "create_skill", skill_data)
            
            results, run_id = runtime.execute(workflow.build())
            
            assert results is not None, f"Skill assessment for {skill_data['skill_category']} should succeed"
            skill_result = results["create_skill"]
            skill_ids.append(skill_result["id"])
            
            # Verify skill assessment data
            assert skill_result["proficiency_score"] == skill_data["proficiency_score"]
            assert skill_result["skill_category"] == skill_data["skill_category"]
        
        # Test skill-based queries
        workflow = WorkflowBuilder()
        workflow.add_node("SkillAssessmentListNode", "list_skills", {
            "filters": {"user_profile_id": profile_id},
            "order_by": "proficiency_score DESC"
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "Skill listing should succeed"
        skills_list = results["list_skills"]
        assert len(skills_list) == 4, "Should return all skill assessments"
        
        # Verify ordering by proficiency score (descending)
        scores = [skill["proficiency_score"] for skill in skills_list]
        assert scores == sorted(scores, reverse=True), "Skills should be ordered by score (desc)"
        
        # Test skill category filtering
        workflow = WorkflowBuilder()
        workflow.add_node("SkillAssessmentListNode", "list_power_tools", {
            "filters": {
                "user_profile_id": profile_id,
                "skill_category": "power_tools"
            }
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "Category filtering should succeed"
        power_tools_skills = results["list_power_tools"]
        assert len(power_tools_skills) == 1, "Should return only power tools skills"
        assert power_tools_skills[0]["skill_category"] == "power_tools"
        
        # Test proficiency level queries
        workflow = WorkflowBuilder()
        workflow.add_node("SkillAssessmentListNode", "list_high_proficiency", {
            "filters": {
                "user_profile_id": profile_id,
                "proficiency_score__gte": 90  # PostgreSQL-style filter
            }
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        assert results is not None, "Proficiency filtering should succeed"
        high_prof_skills = results["list_high_proficiency"]
        assert len(high_prof_skills) == 2, "Should return 2 high proficiency skills"
        
        for skill in high_prof_skills:
            assert skill["proficiency_score"] >= 90, "All skills should have high proficiency"


class TestModelRelationshipsIntegration:
    """Integration tests for model relationships and foreign key constraints."""
    
    @pytest.mark.asyncio
    async def test_product_classification_relationships(self, clean_database):
        """Test Product relationships with UNSPSC and ETIM classifications."""
        # Create UNSPSC code first
        workflow = WorkflowBuilder()
        workflow.add_node("UNSPSCCreateNode", "create_unspsc", {
            "code": "31201501",
            "title": "Electric hand drills",
            "description": "Portable electric drills for various applications",
            "segment": "31",
            "family": "20",
            "class_code": "15",
            "commodity": "01",
            "level": 4
        })
        
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "UNSPSC creation should succeed"
        
        # Create ETIM class
        workflow = WorkflowBuilder()
        workflow.add_node("ETIMCreateNode", "create_etim", {
            "class_id": "EC020404",
            "name_en": "Drilling machines",
            "name_de": "Bohrmaschinen",
            "name_fr": "Perceuses",
            "description": "Electric drilling machines and accessories",
            "version": "9.0"
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "ETIM creation should succeed"
        
        # Create Product with classification references
        workflow = WorkflowBuilder()
        workflow.add_node("ProductCreateNode", "create_classified_product", {
            "product_code": "CLASSIFIED001",
            "name": "Professional Electric Drill",
            "description": "High-performance electric drill with advanced features",
            "brand": "ProDrill",
            "model_number": "PD-2000",
            "unspsc_code": "31201501",  # Reference to UNSPSC
            "etim_class": "EC020404",   # Reference to ETIM
            "specifications": {
                "power": "800W",
                "chuck_size": "13mm",
                "speed_range": "0-3000 RPM"
            },
            "safety_rating": "A"
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Classified product creation should succeed"
        
        classified_product = results["create_classified_product"]
        
        # Verify foreign key relationships
        assert classified_product["unspsc_code"] == "31201501"
        assert classified_product["etim_class"] == "EC020404"
        
        # Test referential integrity (should fail with invalid references)
        workflow = WorkflowBuilder()
        workflow.add_node("ProductCreateNode", "create_invalid_product", {
            "product_code": "INVALID001",
            "name": "Invalid Product",
            "description": "Product with invalid classification references",
            "brand": "InvalidBrand",
            "model_number": "INV-001",
            "unspsc_code": "99999999",  # Non-existent UNSPSC code
            "etim_class": "EC999999",   # Non-existent ETIM class
            "specifications": {},
            "safety_rating": "C"
        })
        
        # This should fail due to foreign key constraints
        try:
            results, run_id = runtime.execute(workflow.build())
            # If this succeeds, the foreign key constraints are not working
            assert False, "Product creation with invalid references should fail"
        except Exception as e:
            # Expected behavior - foreign key constraint violation
            assert "foreign key" in str(e).lower() or "constraint" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_audit_trail_functionality(self, clean_database):
        """Test audit trail functionality across all models."""
        # Create a product and track changes
        workflow = WorkflowBuilder()
        workflow.add_node("ProductCreateNode", "create_audited_product", {
            "product_code": "AUDIT001",
            "name": "Audited Product",
            "description": "Product for testing audit trails",
            "brand": "AuditBrand",
            "model_number": "A001",
            "unspsc_code": "12345678",
            "etim_class": "EC001001",
            "specifications": {"initial": "value"},
            "safety_rating": "B"
        })
        
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Audited product creation should succeed"
        
        product = results["create_audited_product"]
        product_id = product["id"]
        original_created_at = product["created_at"]
        original_updated_at = product["updated_at"]
        
        # Wait briefly to ensure timestamp difference
        await asyncio.sleep(0.1)
        
        # Update the product
        workflow = WorkflowBuilder()
        workflow.add_node("ProductUpdateNode", "update_audited_product", {
            "id": product_id,
            "name": "Updated Audited Product",
            "description": "Updated description for audit testing",
            "specifications": {"updated": "value", "new_field": "added"}
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Product update should succeed"
        
        updated_product = results["update_audited_product"]
        
        # Verify audit trail timestamps
        assert updated_product["created_at"] == original_created_at, "Created timestamp should not change"
        assert updated_product["updated_at"] != original_updated_at, "Updated timestamp should change"
        
        # Verify changes are preserved
        assert updated_product["name"] == "Updated Audited Product"
        assert updated_product["specifications"]["updated"] == "value"
        assert updated_product["specifications"]["new_field"] == "added"
        
        # Test soft delete
        workflow = WorkflowBuilder()
        workflow.add_node("ProductDeleteNode", "soft_delete_product", {
            "id": product_id,
            "soft_delete": True
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Soft delete should succeed"
        
        delete_result = results["soft_delete_product"]
        assert delete_result["deleted"] is True
        
        # Verify product is soft deleted (should have deleted_at timestamp)
        workflow = WorkflowBuilder()
        workflow.add_node("ProductReadNode", "read_deleted_product", {
            "id": product_id,
            "include_deleted": True
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        if results and "read_deleted_product" in results:
            deleted_product = results["read_deleted_product"]
            assert deleted_product["deleted_at"] is not None, "Should have deleted_at timestamp"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--timeout=300"])  # 5 minute timeout for integration tests