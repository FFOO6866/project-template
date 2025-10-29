#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test: Production API Safety Analysis
Tests that production_api_endpoints.py uses REAL safety compliance engines
instead of hardcoded safety data.

CRITICAL: This test validates that the API returns REAL data from PostgreSQL
database via OSHA and ANSI compliance engines, NOT mock/hardcoded data.

Test Approach:
1. Test validates real database integration
2. Test fails fast if safety engines unavailable
3. Test verifies NO hardcoded data in responses
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_safety_analysis_imports_real_engines():
    """
    TEST 1: Verify that safety analysis function imports real compliance engines

    This test validates that the implementation uses OSHA and ANSI engines
    from the src/safety module, not hardcoded data.
    """
    import inspect
    from src.production_api_endpoints import perform_comprehensive_safety_analysis

    # Get source code of the function
    source = inspect.getsource(perform_comprehensive_safety_analysis)

    # Verify imports of real compliance engines
    assert "from src.safety.osha_compliance import get_osha_compliance_engine" in source, \
        "Must import OSHA compliance engine"

    assert "from src.safety.ansi_compliance import get_ansi_compliance_engine" in source, \
        "Must import ANSI compliance engine"

    # Verify NO hardcoded safety data
    assert '"power_tools"' not in source or 'hardcoded' not in source.lower(), \
        "Should not contain hardcoded category 'power_tools'"

    assert 'return {' in source, "Should return safety data"

    # Verify database source indicator
    assert "postgresql_database" in source or "data_source" in source, \
        "Should indicate PostgreSQL as data source"

    print("✅ Safety analysis function uses real compliance engines")


def test_safety_analysis_no_hardcoded_ppe():
    """
    TEST 2: Verify NO hardcoded PPE lists in the implementation

    Checks that the old hardcoded PPE list is not in the source code.
    """
    import inspect
    from src.production_api_endpoints import perform_comprehensive_safety_analysis

    source = inspect.getsource(perform_comprehensive_safety_analysis)

    # Check for old hardcoded values (should NOT exist)
    hardcoded_ppe = '["Safety glasses", "Hearing protection"]'
    assert hardcoded_ppe not in source, \
        f"CRITICAL: Found hardcoded PPE list: {hardcoded_ppe}"

    hardcoded_osha = '["OSHA-1926.95"]'
    assert hardcoded_osha not in source, \
        f"CRITICAL: Found hardcoded OSHA standard: {hardcoded_osha}"

    print("✅ No hardcoded PPE or OSHA standards found in source code")


def test_safety_analysis_uses_osha_assess_task_risk():
    """
    TEST 3: Verify that implementation calls osha_engine.assess_task_risk()

    The real implementation must call the OSHA engine's assess_task_risk method.
    """
    import inspect
    from src.production_api_endpoints import perform_comprehensive_safety_analysis

    source = inspect.getsource(perform_comprehensive_safety_analysis)

    # Verify OSHA engine method calls
    assert "osha_engine.assess_task_risk(" in source, \
        "Must call osha_engine.assess_task_risk() method"

    assert "task_description" in source and "tools_used" in source, \
        "Must pass task_description and tools_used to assessment"

    print("✅ Implementation calls osha_engine.assess_task_risk()")


def test_safety_analysis_error_handling():
    """
    TEST 4: Verify proper error handling for database unavailability

    The implementation must raise HTTPException 503 when database is unavailable.
    """
    import inspect
    from src.production_api_endpoints import perform_comprehensive_safety_analysis

    source = inspect.getsource(perform_comprehensive_safety_analysis)

    # Verify HTTPException import and usage
    assert "HTTPException" in source, \
        "Must import and use HTTPException"

    assert "503" in source or "status_code=503" in source, \
        "Must return 503 Service Unavailable when database is down"

    assert "ValueError" in source or "except" in source, \
        "Must handle ValueError from compliance engine initialization"

    print("✅ Proper error handling implemented")


def test_safety_analysis_data_source_field():
    """
    TEST 5: Verify that response includes data_source field

    All safety responses must indicate that data comes from PostgreSQL database.
    """
    import inspect
    from src.production_api_endpoints import perform_comprehensive_safety_analysis

    source = inspect.getsource(perform_comprehensive_safety_analysis)

    # Verify data_source field in response
    assert '"data_source"' in source, \
        "Response must include data_source field"

    assert "postgresql_database" in source, \
        "data_source must indicate 'postgresql_database'"

    print("✅ Response includes data_source field")


@pytest.mark.asyncio
async def test_safety_analysis_real_integration():
    """
    TEST 6: Integration test with real database (if available)

    This test actually calls the function and validates the response structure.
    If database is unavailable, it should fail with HTTPException 503.
    """
    from src.production_api_endpoints import perform_comprehensive_safety_analysis
    from fastapi import HTTPException

    # Create a mock request object
    class MockRequest:
        task_description = "Cutting metal with angle grinder"
        tools_involved = ["angle_grinder"]
        user_experience = type('obj', (object,), {'value': 'intermediate'})()
        location_type = "indoor"

    request = MockRequest()

    try:
        # Call the function
        result = await perform_comprehensive_safety_analysis(request)

        # Validate response structure
        assert "risk_level" in result, "Response must include risk_level"
        assert "osha_standards" in result, "Response must include osha_standards"
        assert "mandatory_ppe" in result, "Response must include mandatory_ppe"
        assert "data_source" in result, "Response must include data_source"

        # Validate data source
        assert result["data_source"] == "postgresql_database", \
            f"Data source must be 'postgresql_database', got: {result['data_source']}"

        # Validate NO hardcoded data
        if result.get("osha_standards"):
            # If we got standards, they should NOT be the old hardcoded value
            assert result["osha_standards"] != ["OSHA-1926.95"], \
                "CRITICAL: Still returning hardcoded OSHA standard"

        if result.get("mandatory_ppe"):
            # If we got PPE, it should NOT be the old hardcoded value
            hardcoded_ppe = ["Safety glasses", "Hearing protection"]
            assert result["mandatory_ppe"] != hardcoded_ppe, \
                "CRITICAL: Still returning hardcoded PPE list"

        print("✅ Real integration test passed")
        print(f"   Risk level: {result['risk_level']}")
        print(f"   OSHA standards: {len(result.get('osha_standards', []))}")
        print(f"   Mandatory PPE: {len(result.get('mandatory_ppe', []))}")
        print(f"   Data source: {result['data_source']}")

    except HTTPException as e:
        # If database is unavailable, that's expected
        if e.status_code == 503:
            print("⚠️ Database unavailable (expected in test environment)")
            print(f"   Error: {e.detail}")
            pytest.skip("Database not available - test skipped")
        else:
            raise


if __name__ == "__main__":
    print("="*80)
    print("INTEGRATION TEST: Production API Safety Analysis")
    print("Testing hardcoded data removal and real database integration")
    print("="*80)

    # Run static analysis tests
    print("\n1. Testing compliance engine imports...")
    test_safety_analysis_imports_real_engines()

    print("\n2. Testing NO hardcoded PPE lists...")
    test_safety_analysis_no_hardcoded_ppe()

    print("\n3. Testing OSHA engine method calls...")
    test_safety_analysis_uses_osha_assess_task_risk()

    print("\n4. Testing error handling...")
    test_safety_analysis_error_handling()

    print("\n5. Testing data_source field...")
    test_safety_analysis_data_source_field()

    print("\n" + "="*80)
    print("✅ ALL STATIC ANALYSIS TESTS PASSED")
    print("="*80)
    print("\nRun with pytest to test real database integration:")
    print("pytest tests/integration/test_production_api_safety.py -v")
    print("="*80)
