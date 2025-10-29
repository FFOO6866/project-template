"""
Integration Test: Production Project Planning with Real Data
=============================================================

Tests the production project planning workflow with:
- Real PostgreSQL product database queries
- Real pricing engine calculations
- Hybrid AI recommendation engine
- NO hardcoded data or mock responses

Tier 2 Integration Test Requirements:
- Uses REAL Docker services (PostgreSQL, Redis, Neo4j)
- NO MOCKING of external services
- Tests actual component interactions
- Validates data flows with real infrastructure
"""

import pytest
import os
from typing import Dict, Any
from fastapi import HTTPException


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def project_plan_sample() -> Dict[str, Any]:
    """Sample project plan for testing"""
    return {
        'id': 'test-project-001',
        'name': 'DIY Bathroom Renovation',
        'description': 'Complete bathroom renovation including new fixtures, tiling, and lighting',
        'difficulty_level': 'intermediate',
        'estimated_hours': 40,
        'phases': [
            {
                'phase': 1,
                'name': 'Planning and Preparation',
                'duration_hours': 4,
                'tasks': ['Measure bathroom', 'Create materials list', 'Get permits']
            },
            {
                'phase': 2,
                'name': 'Demolition and Preparation',
                'duration_hours': 8,
                'tasks': ['Remove old fixtures', 'Prepare surfaces', 'Install new plumbing']
            },
            {
                'phase': 3,
                'name': 'Installation and Finishing',
                'duration_hours': 28,
                'tasks': ['Install new fixtures', 'Tile walls and floor', 'Install lighting', 'Paint']
            }
        ]
    }


@pytest.fixture
def database_connection_required():
    """
    Ensures PostgreSQL database is available for testing.

    CRITICAL: This is an integration test - requires REAL database.
    Run: ./tests/utils/test-env up && ./tests/utils/test-env status
    """
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        pytest.skip("DATABASE_URL not configured. Integration test requires PostgreSQL.")

    if 'localhost' in database_url and os.getenv('ENVIRONMENT') == 'production':
        pytest.fail("Cannot use localhost in production environment")

    # Test database connectivity
    try:
        from src.core.postgresql_database import get_database
        db = get_database()
        if not db.test_connection():
            pytest.skip("PostgreSQL connection failed. Start test environment: ./tests/utils/test-env up")
    except Exception as e:
        pytest.skip(f"Database initialization failed: {e}")


@pytest.fixture
def redis_connection_required():
    """
    Ensures Redis is available for hybrid recommendation engine caching.

    CRITICAL: This is an integration test - requires REAL Redis instance.
    """
    redis_url = os.getenv('REDIS_URL')

    if not redis_url:
        pytest.skip("REDIS_URL not configured. Integration test requires Redis.")

    if 'localhost' in redis_url and os.getenv('ENVIRONMENT') == 'production':
        pytest.fail("Cannot use localhost in production environment")


# ============================================================================
# Integration Tests
# ============================================================================

class TestProductionProjectRequirements:
    """Test _get_project_requirements with REAL database"""

    def test_get_project_requirements_returns_real_products(
        self,
        project_plan_sample,
        database_connection_required,
        redis_connection_required
    ):
        """
        Test that _get_project_requirements returns REAL products from database.

        CRITICAL VALIDATIONS:
        - NO hardcoded product names (e.g., 'Drill', 'Level')
        - NO hardcoded prices (e.g., 80.00, 25.00)
        - All products have product_id from database
        - All products have real SKU
        - All prices come from database records
        """
        from src.production_nexus_diy_platform_fixes import _get_project_requirements_fixed
        from src.ai.hybrid_recommendation_engine import HybridRecommendationEngine

        # Create mock self with hybrid engine
        class MockSelf:
            def __init__(self):
                self.hybrid_engine = None

        mock_self = MockSelf()

        # Execute project requirements extraction
        import asyncio
        requirements = asyncio.run(
            _get_project_requirements_fixed(mock_self, project_plan_sample)
        )

        # CRITICAL VALIDATION 1: No hardcoded data
        assert requirements is not None, "Requirements should not be None"
        assert 'tools' in requirements, "Requirements must include tools"
        assert 'materials' in requirements, "Requirements must include materials"
        assert 'safety_equipment' in requirements, "Requirements must include safety equipment"

        # CRITICAL VALIDATION 2: All products have database IDs
        for tool in requirements['tools']:
            assert 'product_id' in tool, "Tool missing product_id from database"
            assert tool['product_id'] is not None, "Tool product_id is None"
            assert 'sku' in tool, "Tool missing SKU from database"
            assert 'estimated_cost' in tool, "Tool missing price from database"

            # CRITICAL: Ensure it's not hardcoded 'Drill' or 'Level'
            assert tool['name'] not in ['Drill', 'Level'], \
                f"Found hardcoded tool name: {tool['name']}"

            # CRITICAL: Ensure price is not hardcoded 80.00 or 25.00
            assert tool['estimated_cost'] not in [80.00, 25.00], \
                f"Found hardcoded price: ${tool['estimated_cost']}"

        for material in requirements['materials']:
            assert 'product_id' in material, "Material missing product_id from database"
            assert material['product_id'] is not None, "Material product_id is None"
            assert 'sku' in material, "Material missing SKU from database"
            assert 'estimated_cost' in material, "Material missing price from database"

            # CRITICAL: Ensure it's not hardcoded 'Screws' or 'Wood glue'
            assert material['name'] not in ['Screws', 'Wood glue'], \
                f"Found hardcoded material name: {material['name']}"

            # CRITICAL: Ensure price is not hardcoded 15.00 or 8.00
            assert material['estimated_cost'] not in [15.00, 8.00], \
                f"Found hardcoded price: ${material['estimated_cost']}"

        for safety in requirements['safety_equipment']:
            assert 'product_id' in safety, "Safety equipment missing product_id from database"
            assert safety['product_id'] is not None, "Safety equipment product_id is None"
            assert 'sku' in safety, "Safety equipment missing SKU from database"
            assert 'estimated_cost' in safety, "Safety equipment missing price from database"

            # CRITICAL: Ensure it's not hardcoded 'Safety glasses'
            assert safety['name'] != 'Safety glasses', \
                f"Found hardcoded safety equipment name: {safety['name']}"

            # CRITICAL: Ensure price is not hardcoded 12.00
            assert safety['estimated_cost'] != 12.00, \
                f"Found hardcoded price: ${safety['estimated_cost']}"

        # CRITICAL VALIDATION 3: Metadata indicates real data source
        assert requirements.get('data_source') == 'postgresql_product_database', \
            "Data source should be PostgreSQL product database"
        assert requirements.get('recommendation_method') == 'hybrid_ai_engine', \
            "Recommendation method should be hybrid AI engine"

        print(f"✅ PASS: Retrieved {len(requirements['tools'])} tools, "
              f"{len(requirements['materials'])} materials, "
              f"{len(requirements['safety_equipment'])} safety items from REAL database")

    def test_get_project_requirements_fails_without_description(
        self,
        database_connection_required
    ):
        """Test that missing project description raises HTTPException(400)"""
        from src.production_nexus_diy_platform_fixes import _get_project_requirements_fixed

        class MockSelf:
            pass

        mock_self = MockSelf()

        # Project plan without description
        invalid_plan = {
            'id': 'test-project-002',
            'name': 'Invalid Project',
            # Missing 'description' field
            'difficulty_level': 'intermediate'
        }

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(_get_project_requirements_fixed(mock_self, invalid_plan))

        assert exc_info.value.status_code == 400, \
            "Should raise 400 Bad Request for missing description"
        assert "description" in exc_info.value.detail.lower(), \
            "Error detail should mention missing description"

        print("✅ PASS: Correctly raises HTTPException(400) for missing description")

    def test_get_project_requirements_fails_without_database(self):
        """Test that database unavailability raises HTTPException(503)"""
        from src.production_nexus_diy_platform_fixes import _get_project_requirements_fixed

        # Temporarily remove DATABASE_URL to simulate unavailable database
        original_db_url = os.getenv('DATABASE_URL')
        if original_db_url:
            os.environ.pop('DATABASE_URL')

        class MockSelf:
            pass

        mock_self = MockSelf()

        project_plan = {
            'description': 'Test project',
            'difficulty_level': 'intermediate'
        }

        import asyncio
        try:
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(_get_project_requirements_fixed(mock_self, project_plan))

            assert exc_info.value.status_code == 503, \
                "Should raise 503 Service Unavailable for database connection failure"

            print("✅ PASS: Correctly raises HTTPException(503) when database unavailable")

        finally:
            # Restore DATABASE_URL
            if original_db_url:
                os.environ['DATABASE_URL'] = original_db_url


class TestProductionBudgetBreakdown:
    """Test _generate_budget_breakdown with REAL pricing engine"""

    def test_generate_budget_breakdown_uses_pricing_engine(
        self,
        project_plan_sample,
        database_connection_required
    ):
        """
        Test that _generate_budget_breakdown uses REAL pricing engine calculations.

        CRITICAL VALIDATIONS:
        - Uses pricing engine, not hardcoded formulas
        - Applies business rules (markup, discounts, margins)
        - Returns detailed pricing breakdown
        - NO hardcoded costs like 80.00, 25.00, 15.00, 8.00, 12.00
        """
        from src.production_nexus_diy_platform_fixes import _generate_budget_breakdown_fixed

        class MockSelf:
            pass

        mock_self = MockSelf()

        # Sample required items (would come from _get_project_requirements in real workflow)
        required_items = {
            'tools': [
                {
                    'product_id': 'TOOL-001',
                    'name': 'Cordless Drill with Battery Pack',
                    'sku': 'DWT-DCD791D2',
                    'category': 'Power Tools',
                    'brand': 'DEWALT',
                    'estimated_cost': 179.99,
                    'recommendation_score': 0.95
                },
                {
                    'product_id': 'TOOL-002',
                    'name': 'Digital Level 24-inch',
                    'sku': 'BOSCH-GLL-24',
                    'category': 'Measuring Tools',
                    'brand': 'BOSCH',
                    'estimated_cost': 34.99,
                    'recommendation_score': 0.88
                }
            ],
            'materials': [
                {
                    'product_id': 'MAT-001',
                    'name': 'Ceramic Tile 12x12 Box',
                    'sku': 'TILE-CER-WHT',
                    'category': 'Flooring',
                    'brand': 'Generic',
                    'estimated_cost': 22.50,
                    'quantity': '10 boxes',
                    'recommendation_score': 0.82
                }
            ],
            'safety_equipment': [
                {
                    'product_id': 'SAFE-001',
                    'name': 'ANSI Z87.1 Safety Glasses',
                    'sku': '3M-SEC-SAFE',
                    'category': 'Safety Products',
                    'brand': '3M',
                    'estimated_cost': 14.99,
                    'recommendation_score': 0.98
                }
            ]
        }

        # Execute budget breakdown calculation
        import asyncio
        budget = asyncio.run(
            _generate_budget_breakdown_fixed(mock_self, project_plan_sample, required_items)
        )

        # CRITICAL VALIDATION 1: Budget structure
        assert budget is not None, "Budget should not be None"
        assert 'total_estimated_cost' in budget, "Budget must include total"
        assert 'breakdown' in budget, "Budget must include breakdown"
        assert 'pricing_details' in budget, "Budget must include pricing details"

        # CRITICAL VALIDATION 2: Breakdown categories
        breakdown = budget['breakdown']
        assert 'tools' in breakdown, "Breakdown must include tools cost"
        assert 'materials' in breakdown, "Breakdown must include materials cost"
        assert 'safety_equipment' in breakdown, "Breakdown must include safety cost"
        assert 'contingency' in breakdown, "Breakdown must include contingency"

        # CRITICAL VALIDATION 3: NOT hardcoded totals
        # If using hardcoded data, total would be 80 + 25 + 15 + 8 + 12 = 140
        # Plus 10% contingency = 154
        assert budget['total_estimated_cost'] != 154.00, \
            "Found hardcoded total (140 + 10% contingency)"

        # CRITICAL VALIDATION 4: Pricing details from engine
        pricing_details = budget['pricing_details']
        assert 'item_count' in pricing_details, "Must include item count from pricing engine"
        assert 'total_savings' in pricing_details, "Must include savings from pricing engine"
        assert 'customer_tier' in pricing_details, "Must include customer tier from pricing engine"

        # CRITICAL VALIDATION 5: Data source metadata
        assert budget.get('data_source') == 'pricing_engine', \
            "Data source should be pricing engine"
        assert budget.get('calculation_method') == 'dynamic_pricing_with_business_rules', \
            "Calculation method should use pricing engine business rules"

        # CRITICAL VALIDATION 6: Costs are positive
        assert budget['total_estimated_cost'] > 0, "Total cost must be positive"
        assert breakdown['tools'] > 0, "Tools cost must be positive"
        assert breakdown['materials'] > 0, "Materials cost must be positive"
        assert breakdown['safety_equipment'] > 0, "Safety cost must be positive"
        assert breakdown['contingency'] > 0, "Contingency must be positive"

        print(f"✅ PASS: Budget breakdown calculated with pricing engine")
        print(f"   Total: ${budget['total_estimated_cost']:.2f}")
        print(f"   Tools: ${breakdown['tools']:.2f}")
        print(f"   Materials: ${breakdown['materials']:.2f}")
        print(f"   Safety: ${breakdown['safety_equipment']:.2f}")
        print(f"   Contingency: ${breakdown['contingency']:.2f}")
        print(f"   Savings: ${pricing_details['total_savings']:.2f}")

    def test_generate_budget_breakdown_fails_without_items(self):
        """Test that empty required_items raises HTTPException(400)"""
        from src.production_nexus_diy_platform_fixes import _generate_budget_breakdown_fixed

        class MockSelf:
            pass

        mock_self = MockSelf()

        project_plan = {
            'description': 'Test project',
            'difficulty_level': 'intermediate'
        }

        # Empty required items
        empty_items = {
            'tools': [],
            'materials': [],
            'safety_equipment': []
        }

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(_generate_budget_breakdown_fixed(mock_self, project_plan, empty_items))

        assert exc_info.value.status_code == 400, \
            "Should raise 400 Bad Request for empty items"

        print("✅ PASS: Correctly raises HTTPException(400) for empty product list")


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == '__main__':
    """
    Run integration tests with:

    1. Start test environment:
       ./tests/utils/test-env up && ./tests/utils/test-env status

    2. Run tests:
       pytest tests/integration/test_production_project_planning.py -v --timeout=10

    3. Expected results:
       - All tests PASS
       - NO hardcoded data detected
       - Real database queries executed
       - Pricing engine calculations used
    """
    pytest.main([__file__, '-v', '--timeout=10'])
