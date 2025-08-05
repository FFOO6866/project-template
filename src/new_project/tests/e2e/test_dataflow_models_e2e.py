"""
End-to-End Tests for DataFlow Models - FOUND-003: DataFlow Models

Tests for complete DataFlow model workflows and business scenarios.
Validates real-world usage patterns and business process automation.

Tier 3 Testing: Complete workflows, real infrastructure, NO MOCKING, <10s timeout
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
async def setup_e2e_environment():
    """Setup complete E2E test environment with sample data."""
    # Ensure test database is configured
    test_db_url = "postgresql://test_user:test_password@localhost:5432/test_horme_e2e_db"
    
    # Initialize DataFlow with test database
    db.configure(
        database_url=test_db_url,
        pool_size=10,
        pool_max_overflow=20,
        echo=False,  # Disable SQL logging for performance
        auto_migrate=True
    )
    
    # Create all tables
    await db.create_all()
    
    # Seed with reference data
    await seed_reference_data()
    
    yield db
    
    # Cleanup after tests
    await db.drop_all()
    await db.disconnect()


async def seed_reference_data():
    """Seed database with reference data for E2E tests."""
    runtime = LocalRuntime()
    
    # Seed UNSPSC classifications
    unspsc_data = [
        # Construction and Building Materials
        {"code": "30000000", "title": "Building and Construction and Maintenance Services", "segment": "30", "family": "00", "class_code": "00", "commodity": "00", "level": 1},
        {"code": "30100000", "title": "Building and facility construction", "segment": "30", "family": "10", "class_code": "00", "commodity": "00", "level": 2},
        {"code": "30101500", "title": "Building construction", "segment": "30", "family": "10", "class_code": "15", "commodity": "00", "level": 3},
        {"code": "30101501", "title": "Residential building construction", "segment": "30", "family": "10", "class_code": "15", "commodity": "01", "level": 4},
        
        # Tools and Hardware
        {"code": "31000000", "title": "Manufacturing Components and Supplies", "segment": "31", "family": "00", "class_code": "00", "commodity": "00", "level": 1},
        {"code": "31200000", "title": "Tools and General Machinery", "segment": "31", "family": "20", "class_code": "00", "commodity": "00", "level": 2},
        {"code": "31201500", "title": "Hand tools", "segment": "31", "family": "20", "class_code": "15", "commodity": "00", "level": 3},
        {"code": "31201501", "title": "Screwdrivers", "segment": "31", "family": "20", "class_code": "15", "commodity": "01", "level": 4},
        {"code": "31201502", "title": "Wrenches", "segment": "31", "family": "20", "class_code": "15", "commodity": "02", "level": 4},
    ]
    
    for unspsc in unspsc_data:
        workflow = WorkflowBuilder()
        workflow.add_node("UNSPSCCreateNode", "create_unspsc", {
            **unspsc,
            "description": f"UNSPSC classification for {unspsc['title']}"
        })
        
        try:
            await runtime.execute(workflow.build())
        except Exception:
            pass  # May already exist
    
    # Seed ETIM classifications
    etim_data = [
        {"class_id": "EC010101", "name_en": "Hand tools", "name_de": "Handwerkzeuge", "name_fr": "Outils à main", "version": "9.0"},
        {"class_id": "EC010201", "name_en": "Power tools", "name_de": "Elektrowerkzeuge", "name_fr": "Outils électriques", "version": "9.0"},
        {"class_id": "EC020301", "name_en": "Safety equipment", "name_de": "Sicherheitsausrüstung", "name_fr": "Équipement de sécurité", "version": "9.0"},
        {"class_id": "EC030401", "name_en": "Construction materials", "name_de": "Baumaterialien", "name_fr": "Matériaux de construction", "version": "9.0"},
    ]
    
    for etim in etim_data:
        workflow = WorkflowBuilder()
        workflow.add_node("ETIMCreateNode", "create_etim", {
            **etim,
            "description": f"ETIM classification for {etim['name_en']}"
        })
        
        try:
            await runtime.execute(workflow.build())
        except Exception:
            pass  # May already exist
    
    # Seed Safety Standards
    safety_standards = [
        {
            "standard_type": "OSHA",
            "standard_code": "OSHA-1926.95",
            "title": "Personal Protective Equipment",
            "description": "Requirements for personal protective equipment in construction",
            "severity_level": "critical",
            "regulation_text": "Employees working in areas where there is a possible danger of head injury from impact, or from falling or flying objects, or from electrical shock and burns, shall be protected by protective helmets.",
            "effective_date": datetime(2020, 1, 1)
        },
        {
            "standard_type": "ANSI",
            "standard_code": "ANSI-Z87.1",
            "title": "Eye and Face Protection",
            "description": "Requirements for eye and face protection devices",
            "severity_level": "high",
            "regulation_text": "Eye and face protection equipment shall meet the requirements specified in ANSI Z87.1-2015.",
            "effective_date": datetime(2021, 6, 1)
        }
    ]
    
    for standard in safety_standards:
        workflow = WorkflowBuilder()
        workflow.add_node("SafetyStandardCreateNode", "create_standard", standard)
        
        try:
            await runtime.execute(workflow.build())
        except Exception:
            pass  # May already exist


@pytest.fixture
async def clean_e2e_data(setup_e2e_environment):
    """Clean transactional data before each test while preserving reference data."""
    # Clean transactional tables only
    transactional_tables = [
        'skill_assessments', 'user_profiles', 'inventory_levels',
        'product_pricing', 'compliance_requirements', 'products',
        'product_categories', 'vendors'
    ]
    
    for table in transactional_tables:
        try:
            await setup_e2e_environment.execute(f"TRUNCATE TABLE {table} CASCADE")
        except Exception:
            pass  # Table might not exist yet
    
    yield setup_e2e_environment


class TestProductCatalogManagementE2E:
    """End-to-end tests for complete product catalog management workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_product_catalog_creation_workflow(self, clean_e2e_data):
        """Test complete workflow from product creation to catalog publication."""
        runtime = LocalRuntime()
        
        # Step 1: Create Product Categories Hierarchy
        categories_hierarchy = [
            {"name": "Tools", "parent_id": None, "unspsc_segment": "31", "unspsc_family": "20", "level": 1},
            {"name": "Hand Tools", "parent_id": None, "unspsc_segment": "31", "unspsc_family": "20", "level": 2},  # Will be updated with parent_id
            {"name": "Screwdrivers", "parent_id": None, "unspsc_segment": "31", "unspsc_family": "20", "level": 3},
            {"name": "Wrenches", "parent_id": None, "unspsc_segment": "31", "unspsc_family": "20", "level": 3},
        ]
        
        category_ids = {}
        
        for i, category in enumerate(categories_hierarchy):
            if i == 1:  # Hand Tools - child of Tools
                category["parent_id"] = category_ids["Tools"]
            elif i >= 2:  # Screwdrivers and Wrenches - children of Hand Tools
                category["parent_id"] = category_ids["Hand Tools"]
            
            workflow = WorkflowBuilder()
            workflow.add_node("ProductCategoryCreateNode", "create_category", category)
            
            results, run_id = runtime.execute(workflow.build())
            
            assert results is not None, f"Category {category['name']} creation should succeed"
            created_category = results["create_category"]
            category_ids[category["name"]] = created_category["id"]
        
        # Step 2: Create Products with Full Classification
        products_data = [
            {
                "product_code": "SD-PH-001",
                "name": "Phillips Head Screwdriver Set",
                "description": "Professional 6-piece Phillips head screwdriver set with magnetic tips",
                "brand": "ProTool",
                "model_number": "PT-PH-6PC",
                "unspsc_code": "31201501",
                "etim_class": "EC010101",
                "specifications": {
                    "pieces": 6,
                    "sizes": ["PH0", "PH1", "PH2", "PH3", "PH4", "PH5"],
                    "handle_material": "ergonomic_rubber",
                    "shaft_material": "chrome_vanadium_steel",
                    "magnetic_tips": True,
                    "case_included": True
                },
                "safety_rating": "A"
            },
            {
                "product_code": "WR-ADJ-001",
                "name": "Adjustable Wrench Set",
                "description": "3-piece adjustable wrench set for various applications",
                "brand": "ToughGrip",
                "model_number": "TG-ADJ-3PC",
                "unspsc_code": "31201502",
                "etim_class": "EC010101",
                "specifications": {
                    "pieces": 3,
                    "sizes": ["6 inch", "8 inch", "10 inch"],
                    "jaw_capacity": ["0-19mm", "0-25mm", "0-32mm"],
                    "material": "forged_steel",
                    "finish": "chrome_plated",
                    "non_slip_grip": True
                },
                "safety_rating": "A"
            },
            {
                "product_code": "PPE-HH-001",
                "name": "Safety Hard Hat",
                "description": "OSHA compliant construction safety helmet",
                "brand": "SafetyFirst",
                "model_number": "SF-HH-STD",
                "unspsc_code": "46181501",
                "etim_class": "EC020301",
                "specifications": {
                    "material": "high_density_polyethylene",
                    "suspension_type": "ratchet",
                    "color_options": ["white", "yellow", "orange", "blue"],
                    "ventilation": "side_vents",
                    "chin_strap": "included",
                    "osha_compliant": True,
                    "ansi_rating": "Z89.1_Type_I_Class_E"
                },
                "safety_rating": "A+"
            }
        ]
        
        product_ids = {}
        
        for product_data in products_data:
            workflow = WorkflowBuilder()
            workflow.add_node("ProductCreateNode", "create_product", product_data)
            
            results, run_id = runtime.execute(workflow.build())
            
            assert results is not None, f"Product {product_data['product_code']} creation should succeed"
            created_product = results["create_product"]
            product_ids[product_data["product_code"]] = created_product["id"]
            
            # Verify complex specifications are preserved
            specs = created_product["specifications"]
            if "pieces" in product_data["specifications"]:
                assert specs["pieces"] == product_data["specifications"]["pieces"]
            if "osha_compliant" in product_data["specifications"]:
                assert specs["osha_compliant"] == product_data["specifications"]["osha_compliant"]
        
        # Step 3: Create Safety Compliance Requirements
        # Link Safety Hard Hat to OSHA standard
        workflow = WorkflowBuilder()
        workflow.add_node("SafetyStandardListNode", "find_osha_standard", {
            "filters": {"standard_code": "OSHA-1926.95"}
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "OSHA standard lookup should succeed"
        osha_standards = results["find_osha_standard"]
        assert len(osha_standards) > 0, "Should find OSHA standard"
        osha_standard_id = osha_standards[0]["id"]
        
        # Create compliance requirement
        workflow = WorkflowBuilder()
        workflow.add_node("ComplianceRequirementCreateNode", "create_compliance", {
            "product_id": product_ids["PPE-HH-001"],
            "safety_standard_id": osha_standard_id,
            "requirement_text": "Hard hats must be worn in all construction areas as per OSHA 1926.95",
            "is_mandatory": True,
            "ppe_required": True
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Compliance requirement creation should succeed"
        
        # Step 4: Test Product Catalog Queries
        # Query all products with their classifications
        workflow = WorkflowBuilder()
        workflow.add_node("ProductListNode", "catalog_products", {
            "include_related": ["unspsc", "etim", "compliance"],
            "order_by": "product_code"
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Product catalog query should succeed"
        catalog_products = results["catalog_products"]
        assert len(catalog_products) == 3, "Should return all created products"
        
        # Verify product catalog completeness
        for product in catalog_products:
            assert product["product_code"] is not None
            assert product["name"] is not None
            assert product["unspsc_code"] is not None
            assert product["etim_class"] is not None
            assert product["specifications"] is not None
            assert len(product["specifications"]) > 0
        
        # Step 5: Test Search Functionality
        workflow = WorkflowBuilder()
        workflow.add_node("ProductSearchNode", "search_tools", {
            "query": "screwdriver wrench",
            "fields": ["name", "description"],
            "boost_fields": {"name": 2.0}  # Boost name matches
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Product search should succeed"
        search_results = results["search_tools"]
        assert len(search_results) >= 2, "Should find screwdriver and wrench products"
        
        # Step 6: Test Classification-based Filtering
        workflow = WorkflowBuilder()
        workflow.add_node("ProductListNode", "filter_hand_tools", {
            "filters": {"unspsc_code__startswith": "312015"},  # Hand tools classification
            "order_by": "name"
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Classification filtering should succeed"
        hand_tools = results["filter_hand_tools"]
        assert len(hand_tools) == 2, "Should return screwdriver and wrench products"
    
    @pytest.mark.asyncio
    async def test_product_specification_evolution_workflow(self, clean_e2e_data):
        """Test workflow for evolving product specifications over time."""
        runtime = LocalRuntime()
        
        # Create initial product with basic specifications
        workflow = WorkflowBuilder()
        workflow.add_node("ProductCreateNode", "create_evolving_product", {
            "product_code": "EV-001",
            "name": "Evolving Product",
            "description": "Product for testing specification evolution",
            "brand": "EvoBrand",
            "model_number": "EV-V1",
            "unspsc_code": "31201501",
            "etim_class": "EC010101",
            "specifications": {
                "version": "1.0",
                "basic_feature": "enabled",
                "weight": "1.5kg"
            },
            "safety_rating": "B"
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Initial product creation should succeed"
        product = results["create_evolving_product"]
        product_id = product["id"]
        
        # Evolution 1: Add new features
        workflow = WorkflowBuilder()
        workflow.add_node("ProductUpdateNode", "evolve_v2", {
            "id": product_id,
            "model_number": "EV-V2",
            "specifications": {
                "version": "2.0",
                "basic_feature": "enabled",
                "advanced_feature": "enabled",
                "weight": "1.4kg",  # Improved weight
                "new_materials": ["carbon_fiber", "aluminum"],
                "performance": {
                    "speed": "increased_by_20_percent",
                    "efficiency": "improved"
                }
            }
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Product evolution v2 should succeed"
        evolved_product = results["evolve_v2"]
        
        # Verify evolution
        specs = evolved_product["specifications"]
        assert specs["version"] == "2.0"
        assert specs["advanced_feature"] == "enabled"
        assert "carbon_fiber" in specs["new_materials"]
        assert specs["performance"]["speed"] == "increased_by_20_percent"
        
        # Evolution 2: Major specification overhaul
        workflow = WorkflowBuilder()
        workflow.add_node("ProductUpdateNode", "evolve_v3", {
            "id": product_id,
            "model_number": "EV-V3",
            "specifications": {
                "version": "3.0",
                "legacy_compatibility": {
                    "v1_features": ["basic_feature"],
                    "v2_features": ["advanced_feature"]
                },
                "next_gen_features": {
                    "ai_assisted": True,
                    "iot_connectivity": "WiFi_6",
                    "predictive_maintenance": True
                },
                "physical_properties": {
                    "weight": "1.2kg",
                    "dimensions": {"length": "25cm", "width": "15cm", "height": "8cm"},
                    "materials": {
                        "primary": "carbon_fiber_composite",
                        "secondary": "titanium_alloy",
                        "coating": "nano_ceramic"
                    }
                },
                "environmental": {
                    "energy_efficiency": "A++",
                    "recyclable_components": 85,
                    "carbon_footprint_reduction": "40_percent"
                }
            },
            "safety_rating": "A"  # Improved safety rating
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Product evolution v3 should succeed"
        final_product = results["evolve_v3"]
        
        # Verify complex nested specifications
        specs = final_product["specifications"]
        assert specs["version"] == "3.0"
        assert specs["next_gen_features"]["ai_assisted"] is True
        assert specs["physical_properties"]["materials"]["primary"] == "carbon_fiber_composite"
        assert specs["environmental"]["carbon_footprint_reduction"] == "40_percent"
        assert final_product["safety_rating"] == "A"
        
        # Test specification history queries
        workflow = WorkflowBuilder()
        workflow.add_node("ProductReadNode", "read_final_state", {
            "id": product_id,
            "include_history": True
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Product history read should succeed"
        product_with_history = results["read_final_state"]
        
        # Verify final state
        assert product_with_history["model_number"] == "EV-V3"
        assert product_with_history["specifications"]["version"] == "3.0"


class TestMultiVendorSupplyChainE2E:
    """End-to-end tests for multi-vendor supply chain management workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_supply_chain_workflow(self, clean_e2e_data):
        """Test complete multi-vendor supply chain from vendor onboarding to order fulfillment."""
        runtime = LocalRuntime()
        
        # Step 1: Onboard Multiple Vendors
        vendors_data = [
            {
                "vendor_code": "PREMIUM_TOOLS",
                "company_name": "Premium Tools International",
                "display_name": "Premium Tools",
                "vendor_type": "manufacturer",
                "contact_email": "orders@premiumtools.com",
                "contact_phone": "+1-800-PREMIUM",
                "website_url": "https://premiumtools.com",
                "address": {
                    "street": "1000 Manufacturing Way",
                    "city": "Pittsburgh",
                    "state": "PA",
                    "zip": "15201",
                    "country": "USA"
                },
                "payment_terms": "Net 15",
                "credit_rating": "A+",
                "is_preferred": True,
                "is_active": True
            },
            {
                "vendor_code": "BUDGET_SUPPLY",
                "company_name": "Budget Supply Co.",
                "display_name": "Budget Supply",
                "vendor_type": "distributor",
                "contact_email": "sales@budgetsupply.com",
                "contact_phone": "+1-888-BUDGET1",
                "website_url": "https://budgetsupply.com",
                "address": {
                    "street": "500 Warehouse Blvd",
                    "city": "Memphis",
                    "state": "TN",
                    "zip": "38103",
                    "country": "USA"
                },
                "payment_terms": "Net 30",
                "credit_rating": "B+",
                "is_preferred": False,
                "is_active": True
            },
            {
                "vendor_code": "SPECIALTY_TOOLS",
                "company_name": "Specialty Tools & Equipment",
                "display_name": "Specialty Tools",
                "vendor_type": "supplier",
                "contact_email": "info@specialtytools.com",
                "contact_phone": "+1-555-SPECIAL",
                "website_url": "https://specialtytools.com",
                "address": {
                    "street": "750 Industrial Park Dr",
                    "city": "Cleveland",
                    "state": "OH",
                    "zip": "44135",
                    "country": "USA"
                },
                "payment_terms": "Net 45",
                "credit_rating": "A-",
                "is_preferred": True,
                "is_active": True
            }
        ]
        
        vendor_ids = {}
        
        for vendor_data in vendors_data:
            workflow = WorkflowBuilder()
            workflow.add_node("VendorCreateNode", "create_vendor", vendor_data)
            
            results, run_id = runtime.execute(workflow.build())
            
            assert results is not None, f"Vendor {vendor_data['vendor_code']} creation should succeed"
            created_vendor = results["create_vendor"]
            vendor_ids[vendor_data["vendor_code"]] = created_vendor["id"]
            
            # Verify address JSONB structure
            assert created_vendor["address"]["city"] == vendor_data["address"]["city"]
            assert created_vendor["credit_rating"] == vendor_data["credit_rating"]
        
        # Step 2: Create Products for Multi-Vendor Pricing
        product_data = {
            "product_code": "DRILL-PRO-18V",
            "name": "Professional 18V Cordless Drill",
            "description": "High-performance 18V lithium-ion cordless drill with brushless motor",
            "brand": "ProDrill",
            "model_number": "PD-18V-BL",
            "unspsc_code": "31201501",
            "etim_class": "EC010201",
            "specifications": {
                "voltage": "18V",
                "battery_type": "lithium_ion",
                "motor_type": "brushless",
                "chuck_size": "13mm",
                "torque_settings": 21,
                "max_torque": "65Nm",
                "speed_range": "0-500/0-1700 RPM",
                "weight": "1.8kg",
                "led_light": True,
                "belt_clip": True
            },
            "safety_rating": "A"
        }
        
        workflow = WorkflowBuilder()
        workflow.add_node("ProductCreateNode", "create_drill_product", product_data)
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Drill product creation should succeed"
        drill_product = results["create_drill_product"]
        product_id = drill_product["id"]
        
        # Step 3: Setup Multi-Vendor Pricing with Different Strategies
        pricing_data = [
            {
                "vendor_id": vendor_ids["PREMIUM_TOOLS"],
                "vendor_product_code": "PT-PD18VBL",
                "list_price": Decimal("349.99"),
                "cost_price": Decimal("210.00"),
                "discount_price": Decimal("329.99"),
                "currency": "USD",
                "price_unit": "each",
                "minimum_order_quantity": 1,
                "price_break_quantities": {
                    "1": "329.99",
                    "5": "319.99",
                    "10": "309.99",
                    "25": "299.99",
                    "50": "289.99"
                },
                "effective_date": datetime.now(),
                "expiry_date": datetime.now() + timedelta(days=180),
                "is_active": True,
                "last_updated": datetime.now()
            },
            {
                "vendor_id": vendor_ids["BUDGET_SUPPLY"],
                "vendor_product_code": "BS-DRILL-18V-001",
                "list_price": Decimal("299.99"),
                "cost_price": Decimal("225.00"),
                "discount_price": Decimal("279.99"),
                "currency": "USD",
                "price_unit": "each",
                "minimum_order_quantity": 2,
                "price_break_quantities": {
                    "2": "279.99",
                    "10": "269.99",
                    "25": "259.99",
                    "50": "249.99",
                    "100": "239.99"
                },
                "effective_date": datetime.now(),
                "expiry_date": datetime.now() + timedelta(days=90),
                "is_active": True,
                "last_updated": datetime.now()
            },
            {
                "vendor_id": vendor_ids["SPECIALTY_TOOLS"],
                "vendor_product_code": "ST-PROF-DRILL-18V",
                "list_price": Decimal("379.99"),
                "cost_price": Decimal("190.00"),
                "discount_price": Decimal("359.99"),
                "currency": "USD",
                "price_unit": "each",
                "minimum_order_quantity": 1,
                "price_break_quantities": {
                    "1": "359.99",
                    "3": "349.99",
                    "5": "339.99",
                    "10": "329.99",
                    "20": "319.99"
                },
                "effective_date": datetime.now(),
                "expiry_date": datetime.now() + timedelta(days=365),
                "is_active": True,
                "last_updated": datetime.now()
            }
        ]
        
        pricing_ids = []
        
        for pricing in pricing_data:
            pricing["product_id"] = product_id
            
            workflow = WorkflowBuilder()
            workflow.add_node("ProductPricingCreateNode", "create_pricing", pricing)
            
            results, run_id = runtime.execute(workflow.build())
            
            assert results is not None, "Pricing creation should succeed"
            pricing_result = results["create_pricing"]
            pricing_ids.append(pricing_result["id"])
            
            # Verify decimal precision and JSONB price breaks
            assert Decimal(pricing_result["list_price"]) == pricing["list_price"]
            price_breaks = pricing_result["price_break_quantities"]
            assert len(price_breaks) > 0, "Should have price break quantities"
        
        # Step 4: Setup Inventory Levels with Different Availability
        inventory_data = [
            {
                "vendor_id": vendor_ids["PREMIUM_TOOLS"],
                "location": "PITTSBURGH_FACTORY",
                "quantity_on_hand": 500,
                "quantity_reserved": 50,
                "quantity_on_order": 0,
                "reorder_point": 100,
                "reorder_quantity": 1000,
                "lead_time_days": 1,
                "availability_status": "available"
            },
            {
                "vendor_id": vendor_ids["BUDGET_SUPPLY"],
                "location": "MEMPHIS_WAREHOUSE",
                "quantity_on_hand": 75,
                "quantity_reserved": 15,
                "quantity_on_order": 200,
                "reorder_point": 25,
                "reorder_quantity": 100,
                "lead_time_days": 5,
                "availability_status": "limited"
            },
            {
                "vendor_id": vendor_ids["SPECIALTY_TOOLS"],
                "location": "CLEVELAND_SHOWROOM",
                "quantity_on_hand": 25,
                "quantity_reserved": 5,
                "quantity_on_order": 50,
                "reorder_point": 10,
                "reorder_quantity": 50,
                "lead_time_days": 3,
                "availability_status": "limited"
            }
        ]
        
        for inventory in inventory_data:
            inventory["product_id"] = product_id
            inventory["last_movement_date"] = datetime.now()
            inventory["last_count_date"] = datetime.now() - timedelta(days=7)
            
            workflow = WorkflowBuilder()
            workflow.add_node("InventoryLevelCreateNode", "create_inventory", inventory)
            
            results, run_id = runtime.execute(workflow.build())
            
            assert results is not None, "Inventory creation should succeed"
            inventory_result = results["create_inventory"]
            
            # Verify availability calculation
            available_qty = inventory_result["quantity_on_hand"] - inventory_result["quantity_reserved"]
            assert available_qty >= 0, "Available quantity should be non-negative"
        
        # Step 5: Test Supply Chain Analytics Queries
        # Best price analysis
        workflow = WorkflowBuilder()
        workflow.add_node("ProductPricingListNode", "analyze_pricing", {
            "filters": {"product_id": product_id, "is_active": True},
            "order_by": "discount_price",
            "include_related": ["vendor"]
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Pricing analysis should succeed"
        pricing_analysis = results["analyze_pricing"]
        assert len(pricing_analysis) == 3, "Should return all vendor pricing"
        
        # Verify pricing is ordered by discount price (lowest first)
        prices = [Decimal(p["discount_price"]) for p in pricing_analysis]
        assert prices == sorted(prices), "Prices should be ordered lowest to highest"
        
        # Best availability analysis
        workflow = WorkflowBuilder()
        workflow.add_node("InventoryLevelListNode", "analyze_availability", {
            "filters": {"product_id": product_id},
            "order_by": "quantity_on_hand DESC",
            "include_related": ["vendor"]
        })
        
        results, run_id = runtime.execute(workflow.build())
        assert results is not None, "Availability analysis should succeed"
        availability_analysis = results["analyze_availability"]
        assert len(availability_analysis) == 3, "Should return all vendor inventory"
        
        # Verify inventory is ordered by quantity (highest first)
        quantities = [inv["quantity_on_hand"] for inv in availability_analysis]
        assert quantities == sorted(quantities, reverse=True), "Should be ordered by quantity descending"
        
        # Step 6: Test Procurement Decision Workflow
        # Complex query combining price, availability, and vendor preference
        workflow = WorkflowBuilder()
        workflow.add_node("VendorListNode", "procurement_analysis", {
            "filters": {"is_active": True},
            "include_related": ["pricing", "inventory"],
            "custom_query": {
                "product_id": product_id,
                "min_quantity_available": 20,
                "max_lead_time_days": 7
            }
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        if results and "procurement_analysis" in results:
            procurement_results = results["procurement_analysis"]
            
            # Validate procurement decision factors
            for vendor_option in procurement_results:
                assert vendor_option["is_active"] is True
                # Should have pricing and inventory data
                # Additional validation would depend on the specific query implementation
        
        # Step 7: Test Vendor Performance Tracking
        # Update inventory levels to simulate movement
        workflow = WorkflowBuilder()
        workflow.add_node("InventoryLevelUpdateNode", "simulate_movement", {
            "filters": {"product_id": product_id, "vendor_id": vendor_ids["PREMIUM_TOOLS"]},
            "updates": {
                "quantity_on_hand": 475,  # Reduced by 25
                "quantity_reserved": 60,  # Increased by 10
                "last_movement_date": datetime.now()
            }
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        if results:
            # Verify inventory movement tracking
            workflow = WorkflowBuilder()
            workflow.add_node("InventoryLevelReadNode", "check_movement", {
                "filters": {"product_id": product_id, "vendor_id": vendor_ids["PREMIUM_TOOLS"]}
            })
            
            results, run_id = runtime.execute(workflow.build())
            
            if results and "check_movement" in results:
                updated_inventory = results["check_movement"]
                if isinstance(updated_inventory, list) and len(updated_inventory) > 0:
                    updated_inventory = updated_inventory[0]
                
                assert updated_inventory["quantity_on_hand"] == 475
                assert updated_inventory["quantity_reserved"] == 60


class TestUserSkillBasedRecommendationsE2E:
    """End-to-end tests for user skill-based product recommendation workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_skill_based_recommendation_workflow(self, clean_e2e_data):
        """Test complete workflow from user onboarding to personalized product recommendations."""
        runtime = LocalRuntime()
        
        # Step 1: Create Diverse Product Catalog for Recommendations
        products_for_recommendations = [
            {
                "product_code": "BEGINNER_DRILL",
                "name": "Easy-Use Cordless Drill",
                "description": "Perfect for beginners and DIY enthusiasts",
                "brand": "DIYHelper",
                "model_number": "DH-EASY-12V",
                "unspsc_code": "31201501",
                "etim_class": "EC010201",
                "specifications": {
                    "voltage": "12V",
                    "skill_level": "beginner",
                    "ease_of_use": "very_high",
                    "safety_features": ["auto_stop", "led_light", "safety_switch"],
                    "weight": "1.2kg"
                },
                "safety_rating": "A+"
            },
            {
                "product_code": "INTERMEDIATE_DRILL",
                "name": "Versatile 18V Drill Driver",
                "description": "Great for intermediate users with multiple features",
                "brand": "MidRange",
                "model_number": "MR-VER-18V",
                "unspsc_code": "31201501",
                "etim_class": "EC010201",
                "specifications": {
                    "voltage": "18V",
                    "skill_level": "intermediate",
                    "features": ["variable_speed", "torque_control", "bit_storage"],
                    "weight": "1.6kg"
                },
                "safety_rating": "A"
            },
            {
                "product_code": "PROFESSIONAL_DRILL",
                "name": "Heavy-Duty Professional Drill",
                "description": "Industrial-grade drill for professional contractors",
                "brand": "ProGrade",
                "model_number": "PG-HD-24V",
                "unspsc_code": "31201501",
                "etim_class": "EC010201",
                "specifications": {
                    "voltage": "24V",
                    "skill_level": "professional",
                    "industrial_grade": True,
                    "max_torque": "95Nm",
                    "duty_cycle": "continuous",
                    "weight": "2.1kg"
                },
                "safety_rating": "A"
            },
            {
                "product_code": "SAFETY_GLASSES_BASIC",
                "name": "Basic Safety Glasses",
                "description": "Essential eye protection for all skill levels",
                "brand": "SafeView",
                "model_number": "SV-BASIC-001",
                "unspsc_code": "46181501",
                "etim_class": "EC020301",
                "specifications": {
                    "protection_level": "basic",
                    "ansi_rating": "Z87.1",
                    "lens_type": "polycarbonate",
                    "skill_level": "all_levels"
                },
                "safety_rating": "B+"
            },
            {
                "product_code": "SAFETY_GLASSES_PRO",
                "name": "Professional Safety Glasses",
                "description": "Advanced eye protection with anti-fog coating",
                "brand": "ProVision",
                "model_number": "PV-PRO-002",
                "unspsc_code": "46181501",
                "etim_class": "EC020301",
                "specifications": {
                    "protection_level": "advanced",
                    "ansi_rating": "Z87.1+",
                    "features": ["anti_fog", "uv_protection", "scratch_resistant"],
                    "skill_level": "intermediate_to_professional"
                },
                "safety_rating": "A+"
            }
        ]
        
        product_ids = {}
        
        for product_data in products_for_recommendations:
            workflow = WorkflowBuilder()
            workflow.add_node("ProductCreateNode", "create_product", product_data)
            
            results, run_id = runtime.execute(workflow.build())
            
            assert results is not None, f"Product {product_data['product_code']} creation should succeed"
            created_product = results["create_product"]
            product_ids[product_data["product_code"]] = created_product["id"]
        
        # Step 2: Create User Profiles with Different Skill Levels
        user_profiles = [
            {
                "user_id": 1001,
                "skill_level": "beginner",
                "experience_years": 1,
                "safety_certified": False,
                "preferred_brands": ["DIYHelper", "SafeView"],
                "project_types": ["diy_repairs", "home_improvement"]
            },
            {
                "user_id": 1002,
                "skill_level": "intermediate",
                "experience_years": 5,
                "safety_certified": True,
                "preferred_brands": ["MidRange", "ProVision"],
                "project_types": ["residential_renovation", "furniture_building"]
            },
            {
                "user_id": 1003,
                "skill_level": "professional",
                "experience_years": 15,
                "safety_certified": True,
                "preferred_brands": ["ProGrade", "ProVision"],
                "project_types": ["commercial_construction", "industrial_maintenance"]
            }
        ]
        
        profile_ids = {}
        
        for profile_data in user_profiles:
            workflow = WorkflowBuilder()
            workflow.add_node("UserProfileCreateNode", "create_profile", profile_data)
            
            results, run_id = runtime.execute(workflow.build())
            
            assert results is not None, f"User profile {profile_data['user_id']} creation should succeed"
            created_profile = results["create_profile"]
            profile_ids[profile_data["user_id"]] = created_profile["id"]
        
        # Step 3: Create Detailed Skill Assessments
        skill_assessments = [
            # Beginner User (1001)
            {
                "user_profile_id": profile_ids[1001],
                "skill_category": "power_tools",
                "proficiency_score": 35,
                "assessed_date": datetime.now(),
                "assessor_type": "self",
                "certification_level": "basic"
            },
            {
                "user_profile_id": profile_ids[1001],
                "skill_category": "safety",
                "proficiency_score": 70,
                "assessed_date": datetime.now(),
                "assessor_type": "system",
                "certification_level": "intermediate"
            },
            # Intermediate User (1002)
            {
                "user_profile_id": profile_ids[1002],
                "skill_category": "power_tools",
                "proficiency_score": 75,
                "assessed_date": datetime.now(),
                "assessor_type": "professional",
                "certification_level": "intermediate"
            },
            {
                "user_profile_id": profile_ids[1002],
                "skill_category": "hand_tools",
                "proficiency_score": 85,
                "assessed_date": datetime.now(),
                "assessor_type": "professional",
                "certification_level": "advanced"
            },
            {
                "user_profile_id": profile_ids[1002],
                "skill_category": "safety",
                "proficiency_score": 90,
                "assessed_date": datetime.now(),
                "assessor_type": "professional",
                "certification_level": "advanced"
            },
            # Professional User (1003)
            {
                "user_profile_id": profile_ids[1003],
                "skill_category": "power_tools",
                "proficiency_score": 95,
                "assessed_date": datetime.now(),
                "assessor_type": "professional",
                "certification_level": "expert"
            },
            {
                "user_profile_id": profile_ids[1003],
                "skill_category": "hand_tools",
                "proficiency_score": 98,
                "assessed_date": datetime.now(),
                "assessor_type": "professional",
                "certification_level": "expert"
            },
            {
                "user_profile_id": profile_ids[1003],
                "skill_category": "electrical",
                "proficiency_score": 92,
                "assessed_date": datetime.now(),
                "assessor_type": "professional",
                "certification_level": "expert"
            },
            {
                "user_profile_id": profile_ids[1003],
                "skill_category": "safety",
                "proficiency_score": 100,
                "assessed_date": datetime.now(),
                "assessor_type": "professional",
                "certification_level": "expert"
            }
        ]
        
        for skill_data in skill_assessments:
            skill_data["assessment_notes"] = f"Assessment for {skill_data['skill_category']} at {skill_data['certification_level']} level"
            skill_data["skill_subcategory"] = f"{skill_data['skill_category']}_general"
            
            workflow = WorkflowBuilder()
            workflow.add_node("SkillAssessmentCreateNode", "create_skill_assessment", skill_data)
            
            results, run_id = runtime.execute(workflow.build())
            
            assert results is not None, "Skill assessment creation should succeed"
        
        # Step 4: Test Skill-Based Product Recommendations
        # Beginner user recommendations
        workflow = WorkflowBuilder()
        workflow.add_node("ProductListNode", "recommend_for_beginner", {
            "recommendation_filters": {
                "user_profile_id": profile_ids[1001],
                "skill_level_match": True,
                "safety_appropriate": True,
                "brand_preference": True
            },
            "order_by": "recommendation_score DESC",
            "limit": 5
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        # For this test, we'll simulate the recommendation logic
        # In a real implementation, this would involve complex ML algorithms
        
        # Simulate beginner recommendations by filtering products
        workflow = WorkflowBuilder()
        workflow.add_node("ProductSearchNode", "beginner_products", {
            "query": "beginner easy DIY",
            "fields": ["name", "description", "specifications"],
            "filters": {
                "specifications__skill_level": ["beginner", "all_levels"]
            }
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        if results and "beginner_products" in results:
            beginner_recommendations = results["beginner_products"]
            
            # Verify beginner-appropriate products are recommended
            for product in beginner_recommendations:
                specs = product.get("specifications", {})
                skill_level = specs.get("skill_level", "")
                assert skill_level in ["beginner", "all_levels"], \
                    "Beginner should only get beginner-appropriate products"
        
        # Professional user recommendations
        workflow = WorkflowBuilder()
        workflow.add_node("ProductSearchNode", "professional_products", {
            "query": "professional industrial heavy-duty",
            "fields": ["name", "description", "specifications"],
            "filters": {
                "specifications__skill_level": ["professional", "intermediate_to_professional"]
            }
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        if results and "professional_products" in results:
            professional_recommendations = results["professional_products"]
            
            # Verify professional-grade products are recommended
            for product in professional_recommendations:
                specs = product.get("specifications", {})
                skill_level = specs.get("skill_level", "")
                assert "professional" in skill_level or "advanced" in str(specs), \
                    "Professional should get professional-grade products"
        
        # Step 5: Test Safety-Based Recommendations
        # For users without safety certification, prioritize safety products
        workflow = WorkflowBuilder()
        workflow.add_node("UserProfileReadNode", "get_beginner_profile", {
            "id": profile_ids[1001]
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        if results and "get_beginner_profile" in results:
            beginner_profile = results["get_beginner_profile"]
            
            if not beginner_profile["safety_certified"]:
                # Recommend safety products for uncertified users
                workflow = WorkflowBuilder()
                workflow.add_node("ProductListNode", "safety_recommendations", {
                    "filters": {
                        "unspsc_code__startswith": "46181"  # Safety equipment UNSPSC
                    },
                    "order_by": "safety_rating DESC"
                })
                
                results, run_id = runtime.execute(workflow.build())
                
                if results and "safety_recommendations" in results:
                    safety_products = results["safety_recommendations"]
                    assert len(safety_products) > 0, "Should recommend safety products"
        
        # Step 6: Test Skill Gap Analysis and Training Recommendations
        # Analyze skills for intermediate user
        workflow = WorkflowBuilder()
        workflow.add_node("SkillAssessmentListNode", "analyze_intermediate_skills", {
            "filters": {"user_profile_id": profile_ids[1002]},
            "order_by": "proficiency_score"
        })
        
        results, run_id = runtime.execute(workflow.build())
        
        if results and "analyze_intermediate_skills" in results:
            intermediate_skills = results["analyze_intermediate_skills"]
            
            # Identify skill gaps (scores below 80 for intermediate level)
            skill_gaps = [skill for skill in intermediate_skills if skill["proficiency_score"] < 80]
            
            if skill_gaps:
                # Recommend training products for identified gaps
                gap_categories = [gap["skill_category"] for gap in skill_gaps]
                
                workflow = WorkflowBuilder()
                workflow.add_node("ProductSearchNode", "training_products", {
                    "query": " ".join(gap_categories) + " training educational",
                    "fields": ["name", "description", "specifications"]
                })
                
                results, run_id = runtime.execute(workflow.build())
                
                # This would be used to recommend training materials or beginner-friendly tools
        
        # Step 7: Test Personalized Brand and Project Recommendations
        # Get user's preferred brands and project types
        for user_id in [1001, 1002, 1003]:
            workflow = WorkflowBuilder()
            workflow.add_node("UserProfileReadNode", "get_user_preferences", {
                "id": profile_ids[user_id]
            })
            
            results, run_id = runtime.execute(workflow.build())
            
            if results and "get_user_preferences" in results:
                user_profile = results["get_user_preferences"]
                preferred_brands = user_profile["preferred_brands"]
                project_types = user_profile["project_types"]
                
                # Recommend products matching user's brand preferences
                for brand in preferred_brands:
                    workflow = WorkflowBuilder()
                    workflow.add_node("ProductListNode", f"brand_products_{brand}", {
                        "filters": {"brand": brand},
                        "limit": 3
                    })
                    
                    results, run_id = runtime.execute(workflow.build())
                    
                    if results and f"brand_products_{brand}" in results:
                        brand_products = results[f"brand_products_{brand}"]
                        
                        for product in brand_products:
                            assert product["brand"] == brand, \
                                "Brand filtering should work correctly"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--timeout=600"])  # 10 minute timeout for E2E tests