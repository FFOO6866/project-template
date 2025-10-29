"""
Integration Tests for Production MCP Server Safety Analysis
============================================================

Tests the integration of OSHA/ANSI compliance engines with MCP server.

CRITICAL REQUIREMENTS:
- Uses REAL PostgreSQL database with safety standards
- NO mocking of compliance engines or database
- Tests fail fast if database is not populated
- Validates real OSHA/ANSI data integration

Test Coverage:
- Tier 2 (Integration): Real database queries, compliance engine integration
- Safety analysis with real OSHA standards
- ANSI equipment recommendations
- Location-specific considerations from database
- Emergency procedures from OSHA standards
- Training recommendations based on hazards

Prerequisites:
- PostgreSQL database must be running
- Safety standards must be loaded: python scripts/load_safety_standards.py
- OSHA and ANSI tables must be populated
"""

import pytest
import asyncio
from typing import Dict, Any, List
from datetime import datetime

# Import MCP server components
from src.production_mcp_server import (
    MCPServerState,
    _perform_comprehensive_safety_analysis,
    _get_location_considerations_from_db,
    _get_emergency_procedures_from_db,
    _get_training_recommendations_from_db,
    server_state
)

# Import compliance engines for validation
from src.safety.osha_compliance import OSHAComplianceEngine
from src.safety.ansi_compliance import ANSIComplianceEngine

# Import request models
from src.production_nexus_diy_platform import SafetyRequirementsRequest, SkillLevel


@pytest.fixture(scope="module")
async def initialized_server_state():
    """
    Initialize MCP server state with real database connections.

    This fixture ensures the server state is properly initialized
    before running tests. It validates that:
    - PostgreSQL database is accessible
    - Safety standards are loaded
    - OSHA and ANSI engines are initialized
    """
    # Initialize server state
    await server_state.initialize()

    # Validate engines are initialized
    assert server_state.osha_engine is not None, \
        "OSHA engine not initialized - database may be empty"
    assert server_state.ansi_engine is not None, \
        "ANSI engine not initialized - database may be empty"

    # Validate database has data
    osha_stats = server_state.osha_engine.get_database_statistics()
    assert osha_stats['osha_standards_count'] > 0, \
        "No OSHA standards in database - run: python scripts/load_safety_standards.py"
    assert osha_stats['tool_classifications_count'] > 0, \
        "No tool classifications in database - run: python scripts/load_safety_standards.py"

    ansi_stats = server_state.ansi_engine.get_database_statistics()
    assert ansi_stats['ansi_standards_count'] > 0, \
        "No ANSI standards in database - run: python scripts/load_safety_standards.py"

    yield server_state

    # Cleanup
    await server_state.cleanup()


class TestSafetyAnalysisIntegration:
    """Test comprehensive safety analysis with real database integration."""

    @pytest.mark.asyncio
    async def test_electrical_work_safety_analysis(self, initialized_server_state):
        """Test safety analysis for electrical work using real OSHA standards."""
        # Create safety request for electrical work
        request = SafetyRequirementsRequest(
            task_description="Install new electrical outlet in kitchen",
            tools_involved=["voltage tester", "wire stripper", "screwdriver"],
            materials_involved=["electrical wire", "outlet box", "wire nuts"],
            location_type="indoor",
            user_experience=SkillLevel.INTERMEDIATE
        )

        # Perform safety analysis
        analysis = await _perform_comprehensive_safety_analysis(request)

        # Validate analysis structure
        assert analysis is not None, "Safety analysis returned None"
        assert 'risk_level' in analysis, "Missing risk_level in analysis"
        assert 'hazards' in analysis, "Missing hazards in analysis"
        assert 'osha_standards' in analysis, "Missing osha_standards in analysis"
        assert 'mandatory_ppe' in analysis, "Missing mandatory_ppe in analysis"

        # Validate data source is database
        assert analysis['data_source'] == 'postgresql_database', \
            "Analysis should use PostgreSQL database, not hardcoded data"

        # Validate OSHA standards are from database
        assert len(analysis['osha_standards']) > 0, \
            "No OSHA standards found - database should have electrical safety standards"

        # Validate PPE requirements are present
        assert len(analysis['mandatory_ppe']) > 0, \
            "No mandatory PPE found - electrical work requires PPE"

        # Validate hazards are identified
        assert len(analysis['hazards']) > 0, \
            "No hazards identified - electrical work has known hazards"

        # Validate risk level is appropriate
        assert analysis['risk_level'] in ['medium', 'high', 'critical'], \
            f"Electrical work should be medium-high risk, got: {analysis['risk_level']}"

        # Validate location considerations
        assert 'location_considerations' in analysis
        assert len(analysis['location_considerations']) > 0

        # Validate emergency procedures
        assert 'emergency_procedures' in analysis
        assert len(analysis['emergency_procedures']) > 0

        # Validate training recommendations
        assert 'training_recommendations' in analysis
        assert len(analysis['training_recommendations']) > 0

        # Validate metadata
        assert 'standards_count' in analysis
        assert analysis['standards_count'] > 0

    @pytest.mark.asyncio
    async def test_power_tool_safety_analysis(self, initialized_server_state):
        """Test safety analysis for power tool work using real database."""
        request = SafetyRequirementsRequest(
            task_description="Cut lumber with circular saw for deck construction",
            tools_involved=["circular saw", "measuring tape", "safety glasses"],
            materials_involved=["pressure-treated lumber"],
            location_type="outdoor",
            user_experience=SkillLevel.BEGINNER
        )

        analysis = await _perform_comprehensive_safety_analysis(request)

        # Validate basic structure
        assert analysis is not None
        assert analysis['data_source'] == 'postgresql_database'

        # Validate ANSI equipment recommendations for power tools
        assert 'ansi_equipment_recommendations' in analysis
        # Power tools should trigger hearing protection requirements
        if analysis['ansi_equipment_recommendations']:
            hearing_protection = analysis['ansi_equipment_recommendations'][0]
            assert 'hearing_protection_required' in hearing_protection
            assert 'ansi_standard' in hearing_protection

        # Validate beginner-specific training recommendations
        assert 'training_recommendations' in analysis
        training = analysis['training_recommendations']
        # Beginners should have specific training requirements
        assert any('OSHA' in rec or 'training' in rec.lower() for rec in training), \
            "Beginner should have OSHA training recommendations"

    @pytest.mark.asyncio
    async def test_no_hardcoded_safety_categories(self, initialized_server_state):
        """Verify that analysis does NOT use hardcoded safety categories."""
        request = SafetyRequirementsRequest(
            task_description="Paint interior walls",
            tools_involved=["paint roller", "paint brush"],
            materials_involved=["latex paint"],
            location_type="indoor",
            user_experience=SkillLevel.INTERMEDIATE
        )

        analysis = await _perform_comprehensive_safety_analysis(request)

        # The analysis should come from database, not hardcoded dictionaries
        assert analysis['data_source'] == 'postgresql_database'
        assert 'osha_data_source' in analysis
        assert analysis['osha_data_source'] == 'osha_compliance_engine'

        # Should have OSHA standards from database
        assert isinstance(analysis['osha_standards'], list)

        # Should have hazards from database assessment
        assert isinstance(analysis['hazards'], list)

    @pytest.mark.asyncio
    async def test_database_unavailable_fails_fast(self):
        """Test that system fails fast when database is not populated."""
        # Create a new state without initializing engines
        test_state = MCPServerState()

        request = SafetyRequirementsRequest(
            task_description="Test task",
            tools_involved=[],
            materials_involved=[],
            location_type="indoor",
            user_experience=SkillLevel.INTERMEDIATE
        )

        # Temporarily set server_state to test_state
        import src.production_mcp_server as production_mcp_server
        original_state = production_mcp_server.server_state
        production_mcp_server.server_state = test_state

        try:
            # Should raise ValueError about uninitialized engines
            with pytest.raises(ValueError, match="Safety compliance engines not initialized"):
                await _perform_comprehensive_safety_analysis(request)
        finally:
            # Restore original state
            production_mcp_server.server_state = original_state


class TestLocationConsiderations:
    """Test location-specific safety considerations from database."""

    @pytest.mark.asyncio
    async def test_indoor_location_considerations(self, initialized_server_state):
        """Test indoor location safety considerations from database."""
        considerations = await _get_location_considerations_from_db("indoor")

        assert considerations is not None
        assert len(considerations) > 0
        assert isinstance(considerations, list)

        # Should have real considerations, not just generic fallback
        assert not all('General workspace safety' in c for c in considerations), \
            "Should have specific indoor considerations, not just generic"

    @pytest.mark.asyncio
    async def test_outdoor_location_considerations(self, initialized_server_state):
        """Test outdoor location safety considerations from database."""
        considerations = await _get_location_considerations_from_db("outdoor")

        assert considerations is not None
        assert len(considerations) > 0

        # Outdoor should have different considerations than indoor
        indoor_considerations = await _get_location_considerations_from_db("indoor")
        assert considerations != indoor_considerations, \
            "Indoor and outdoor should have different safety considerations"


class TestEmergencyProcedures:
    """Test emergency procedures extraction from OSHA standards."""

    @pytest.mark.asyncio
    async def test_electrical_emergency_procedures(self, initialized_server_state):
        """Test emergency procedures for electrical work from database."""
        # Use real OSHA electrical standards
        osha_standards = ["29 CFR 1926.416", "29 CFR 1926.417"]

        procedures = await _get_emergency_procedures_from_db(osha_standards)

        assert procedures is not None
        assert len(procedures) > 0
        assert isinstance(procedures, list)

        # Should have universal emergency procedures
        assert any('emergency contact' in p.lower() or 'first aid' in p.lower()
                   for p in procedures), \
            "Should include universal emergency procedures"

    @pytest.mark.asyncio
    async def test_empty_standards_provides_fallback(self, initialized_server_state):
        """Test that empty standards list provides fallback procedures."""
        procedures = await _get_emergency_procedures_from_db([])

        assert procedures is not None
        assert len(procedures) > 0
        # Should at least have universal procedures
        assert any('emergency' in p.lower() for p in procedures)


class TestTrainingRecommendations:
    """Test training recommendations based on hazards and skill level."""

    @pytest.mark.asyncio
    async def test_beginner_training_recommendations(self, initialized_server_state):
        """Test that beginners get comprehensive training recommendations."""
        hazards = ["electrical", "power_tools"]

        recommendations = await _get_training_recommendations_from_db(
            SkillLevel.BEGINNER,
            hazards
        )

        assert recommendations is not None
        assert len(recommendations) > 0

        # Beginners should get OSHA 10-hour recommendation
        assert any('OSHA' in rec for rec in recommendations), \
            "Beginners should have OSHA training recommendation"

        # Should have specific recommendations for hazards
        assert len(recommendations) > 1, \
            "Should have multiple training recommendations for beginners"

    @pytest.mark.asyncio
    async def test_electrical_certification_for_intermediate(self, initialized_server_state):
        """Test electrical certification requirement for intermediate users."""
        hazards = ["electrical"]

        recommendations = await _get_training_recommendations_from_db(
            SkillLevel.INTERMEDIATE,
            hazards
        )

        assert recommendations is not None
        # Intermediate users doing electrical work should get certification recommendation
        assert any('electrical' in rec.lower() and 'certification' in rec.lower()
                   for rec in recommendations), \
            "Intermediate users should get electrical certification recommendation"


class TestOSHAComplianceIntegration:
    """Test OSHA compliance engine integration with MCP server."""

    @pytest.mark.asyncio
    async def test_osha_engine_statistics(self, initialized_server_state):
        """Validate OSHA engine has loaded data from database."""
        stats = server_state.osha_engine.get_database_statistics()

        assert stats['osha_standards_count'] > 0
        assert stats['tool_classifications_count'] > 0
        assert stats['task_hazard_mappings_count'] > 0
        assert stats['total_safety_records'] > 0

    @pytest.mark.asyncio
    async def test_osha_task_assessment_integration(self, initialized_server_state):
        """Test OSHA engine task assessment through MCP server."""
        # Directly test OSHA engine integration
        assessment = server_state.osha_engine.assess_task_risk(
            task_description="Drilling holes in concrete wall",
            tools_used=["hammer drill", "safety glasses"]
        )

        assert assessment is not None
        assert assessment['data_source'] == 'postgresql_database'
        assert 'risk_level' in assessment
        assert 'mandatory_ppe' in assessment
        assert 'osha_standards' in assessment


class TestANSIComplianceIntegration:
    """Test ANSI compliance engine integration with MCP server."""

    @pytest.mark.asyncio
    async def test_ansi_engine_statistics(self, initialized_server_state):
        """Validate ANSI engine has loaded data from database."""
        stats = server_state.ansi_engine.get_database_statistics()

        assert stats['ansi_standards_count'] > 0
        assert stats['equipment_specifications_count'] > 0
        assert stats['total_ansi_records'] > 0

    @pytest.mark.asyncio
    async def test_ansi_hearing_protection_recommendation(self, initialized_server_state):
        """Test ANSI hearing protection recommendations through MCP server."""
        # Test NRR requirement for power tool work
        hearing_req = server_state.ansi_engine.get_nrr_requirement(noise_level_dba=95)

        assert hearing_req is not None
        assert hearing_req['hearing_protection_required'] is True
        assert 'ansi_standard' in hearing_req
        assert hearing_req['ansi_standard'] == "ANSI S3.19-1974"
        assert 'minimum_nrr_labeled' in hearing_req


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
