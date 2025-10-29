#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: Safety Compliance System Test Suite
Comprehensive testing for OSHA and ANSI compliance engines

Tests:
1. OSHA Compliance Engine
2. ANSI Compliance Engine
3. Risk Assessment
4. PPE Compliance Validation
5. Equipment Certification
6. NRR Calculations
7. Cut Resistance Recommendations
"""

import sys
import os
import logging
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.safety.osha_compliance import get_osha_compliance_engine, RiskLevel
from src.safety.ansi_compliance import get_ansi_compliance_engine

logging.basicConfig(level=logging.INFO, encoding='utf-8' if sys.version_info >= (3, 9) else None)
logger = logging.getLogger(__name__)


def test_osha_compliance_engine():
    """Test OSHA compliance engine basic functionality"""
    print("\n" + "="*80)
    print("TEST 1: OSHA Compliance Engine")
    print("="*80)

    osha_engine = get_osha_compliance_engine()

    # Test 1: Get all OSHA standards
    standards = osha_engine.get_all_standards()
    print(f"\n[OK] Loaded {len(standards)} OSHA standards:")
    for key, standard in list(standards.items())[:3]:
        print(f"   - {standard['cfr']}: {standard['title']}")

    # Test 2: Get specific standard details
    cfr_number = "29 CFR 1926.102"
    standard = osha_engine.get_standard_details(cfr_number)
    print(f"\n[OK] Retrieved standard {cfr_number}")
    print(f"   Title: {standard['title']}")
    print(f"   Risk Level: {standard['risk_level']}")
    print(f"   Mandatory: {standard['mandatory']}")
    print(f"   Applies to: {', '.join(standard['applies_to'][:3])}")

    # Test 3: Tool risk classification
    tool_classifications = osha_engine._load_tool_risk_classifications()
    print(f"\n[OK] Loaded {len(tool_classifications)} tool risk classifications")
    angle_grinder = tool_classifications["angle_grinder"]
    print(f"   Angle Grinder Risk Level: {angle_grinder['risk_level']}")
    print(f"   Mandatory PPE: {', '.join(angle_grinder['mandatory_ppe'])}")

    return True


def test_task_risk_assessment():
    """Test comprehensive task risk assessment"""
    print("\n" + "="*80)
    print("TEST 2: Task Risk Assessment")
    print("="*80)

    osha_engine = get_osha_compliance_engine()

    # Test scenario 1: Drilling concrete
    task_1 = "Drilling holes in concrete wall"
    tools_1 = ["drill", "hammer"]

    assessment_1 = osha_engine.assess_task_risk(task_1, tools_1)

    print(f"\n[OK] Task: {task_1}")
    print(f"   Tools: {tools_1}")
    print(f"   Risk Level: {assessment_1['risk_level']}")
    print(f"   Hazards: {', '.join(assessment_1['hazards'])}")
    print(f"   OSHA Standards: {', '.join(assessment_1['osha_standards'][:2])}")
    print(f"   Mandatory PPE: {', '.join(assessment_1['mandatory_ppe'])}")
    print(f"   Compliance Notes: {len(assessment_1['compliance_notes'])} notes")

    # Test scenario 2: Cutting metal with angle grinder
    task_2 = "Cutting metal pipes with angle grinder"
    tools_2 = ["angle_grinder"]

    assessment_2 = osha_engine.assess_task_risk(task_2, tools_2)

    print(f"\n[OK] Task: {task_2}")
    print(f"   Tools: {tools_2}")
    print(f"   Risk Level: {assessment_2['risk_level']}")
    print(f"   Hazards: {', '.join(assessment_2['hazards'])}")
    print(f"   OSHA Standards: {', '.join(assessment_2['osha_standards'][:2])}")
    print(f"   Mandatory PPE: {', '.join(assessment_2['mandatory_ppe'])}")

    # Validate critical risk level
    assert assessment_2['risk_level'] == RiskLevel.CRITICAL.value, \
        "Angle grinder should be classified as CRITICAL risk"

    return True


def test_ppe_compliance_validation():
    """Test PPE compliance validation"""
    print("\n" + "="*80)
    print("TEST 3: PPE Compliance Validation")
    print("="*80)

    osha_engine = get_osha_compliance_engine()

    # Task assessment
    task = "Cutting metal with angle grinder"
    tools = ["angle_grinder"]
    assessment = osha_engine.assess_task_risk(task, tools)

    # Test 1: Full compliance
    available_ppe_full = [
        "safety_glasses",
        "face_shield",
        "work_gloves",
        "hearing_protection",
        "dust_mask"
    ]

    is_compliant, missing = osha_engine.validate_ppe_compliance(
        assessment,
        available_ppe_full
    )

    print(f"\n[OK] Test 1: Full PPE Compliance")
    print(f"   Available PPE: {', '.join(available_ppe_full)}")
    print(f"   Compliant: {is_compliant}")
    print(f"   Missing: {', '.join(missing) if missing else 'None'}")

    assert is_compliant == True, "Full PPE should be compliant"

    # Test 2: Partial compliance (missing mandatory items)
    available_ppe_partial = [
        "safety_glasses",
        "work_gloves"
    ]

    is_compliant, missing = osha_engine.validate_ppe_compliance(
        assessment,
        available_ppe_partial
    )

    print(f"\n[OK] Test 2: Partial PPE Compliance")
    print(f"   Available PPE: {', '.join(available_ppe_partial)}")
    print(f"   Compliant: {is_compliant}")
    print(f"   Missing: {', '.join(missing)}")

    assert is_compliant == False, "Partial PPE should not be compliant"
    assert len(missing) > 0, "Should have missing PPE items"

    return True


def test_ansi_compliance_engine():
    """Test ANSI compliance engine"""
    print("\n" + "="*80)
    print("TEST 4: ANSI Compliance Engine")
    print("="*80)

    ansi_engine = get_ansi_compliance_engine()

    # Test 1: Get all ANSI standards
    standards = ansi_engine.get_all_standards()
    print(f"\n[OK] Loaded {len(standards)} ANSI standards:")
    for key, standard in list(standards.items())[:3]:
        print(f"   - {standard['standard']}: {standard['title']}")

    # Test 2: Equipment certification validation
    equipment_type = "impact_rated_safety_glasses"
    marking = "Z87+"

    validation = ansi_engine.validate_equipment_certification(
        equipment_type,
        marking
    )

    print(f"\n[OK] Equipment Certification Validation")
    print(f"   Equipment: {equipment_type}")
    print(f"   Marking: {marking}")
    print(f"   Valid: {validation['valid']}")
    print(f"   ANSI Standard: {validation['ansi_standard']}")
    print(f"   Protection Level: {validation['protection_level']}")
    print(f"   Marking Valid: {validation['marking_valid']}")

    assert validation['valid'] == True, "Z87+ marking should be valid"
    assert validation['marking_valid'] == True, "Marking should match requirement"

    return True


def test_nrr_calculations():
    """Test NRR (Noise Reduction Rating) calculations"""
    print("\n" + "="*80)
    print("TEST 5: NRR Calculations (ANSI S3.19)")
    print("="*80)

    ansi_engine = get_ansi_compliance_engine()

    # Test various noise levels
    noise_levels = [85, 90, 95, 100, 110, 115]

    for noise_level in noise_levels:
        nrr_req = ansi_engine.get_nrr_requirement(noise_level)

        print(f"\n[OK] Noise Level: {noise_level} dBA")
        print(f"   Protection Required: {nrr_req.get('hearing_protection_required', False)}")

        if nrr_req.get('hearing_protection_required'):
            print(f"   Max Exposure: {nrr_req['max_exposure_hours']} hours")
            print(f"   Required NRR (labeled): {nrr_req['minimum_nrr_labeled']} dB")
            print(f"   Recommended Products: {', '.join(nrr_req['recommended_products'])}")

            # Validate calculation
            assert nrr_req['target_level_dba'] == 85, "Target should be 85 dBA"
            assert nrr_req['minimum_nrr_labeled'] > 0, "NRR should be positive"

    return True


def test_cut_resistance_recommendations():
    """Test cut resistance recommendations (ANSI/ISEA 105)"""
    print("\n" + "="*80)
    print("TEST 6: Cut Resistance Recommendations (ANSI/ISEA 105)")
    print("="*80)

    ansi_engine = get_ansi_compliance_engine()

    # Test various hazard scenarios
    hazards = [
        "Handling sharp metal edges",
        "Working with glass sheets",
        "Light assembly with cardboard boxes",
        "Cutting with razor sharp tools"
    ]

    for hazard in hazards:
        recommendation = ansi_engine.get_cut_resistance_recommendation(hazard)

        print(f"\n[OK] Hazard: {hazard}")
        print(f"   Recommended Cut Level: {recommendation['recommended_cut_level']}")
        print(f"   Cut Resistance: {recommendation['cut_resistance_grams']} grams")
        print(f"   Protection Rating: {recommendation['protection_rating']}")
        print(f"   ANSI Standard: {recommendation['ansi_standard']}")

        # Validate recommendation
        assert recommendation['recommended_cut_level'] in [
            'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9'
        ], "Cut level should be valid ANSI level"

    return True


def test_ansi_standard_details():
    """Test retrieving ANSI standard details"""
    print("\n" + "="*80)
    print("TEST 7: ANSI Standard Details")
    print("="*80)

    ansi_engine = get_ansi_compliance_engine()

    # Test eye protection standard
    standard_name = "ANSI Z87.1-2020"
    standard = ansi_engine.get_standard_details(standard_name)

    print(f"\n[OK] Standard: {standard_name}")
    print(f"   Title: {standard['title']}")
    print(f"   Category: {standard['category']}")
    print(f"   Description: {standard['description'][:100]}...")
    print(f"   Product Types: {', '.join(standard['product_types'])}")
    print(f"   Markings:")
    for key, value in list(standard['markings'].items())[:3]:
        print(f"      - {key}: {value}")

    # Test foot protection standard
    standard_name = "ASTM F2413-18"
    standard = ansi_engine.get_standard_details(standard_name)

    print(f"\n[OK] Standard: {standard_name}")
    print(f"   Title: {standard['title']}")
    print(f"   Category: {standard['category']}")
    print(f"   Product Types: {', '.join(standard['product_types'])}")
    print(f"   Protection Types:")
    for key, value in list(standard['protection_types'].items())[:3]:
        print(f"      - {key}: {value}")

    return True


def test_real_world_scenario():
    """Test complete real-world scenario"""
    print("\n" + "="*80)
    print("TEST 8: Real-World Scenario - Construction Site Safety")
    print("="*80)

    osha_engine = get_osha_compliance_engine()
    ansi_engine = get_ansi_compliance_engine()

    # Scenario: Worker using angle grinder on construction site
    task_description = """
    Worker needs to cut metal rebar and concrete for foundation work.
    Will be using angle grinder for extended period (4+ hours).
    Environment: Construction site with overhead hazards.
    """

    tools = ["angle_grinder", "hammer", "chisel"]

    print(f"\n[INFO] Scenario:")
    print(f"   {task_description.strip()}")
    print(f"   Tools: {', '.join(tools)}")

    # Step 1: Assess task risk
    assessment = osha_engine.assess_task_risk(task_description, tools)

    print(f"\n[OK] Step 1: Risk Assessment")
    print(f"   Overall Risk Level: {assessment['risk_level']}")
    print(f"   Identified Hazards: {', '.join(assessment['hazards'])}")
    print(f"   Applicable OSHA Standards:")
    for standard in assessment['osha_standards']:
        print(f"      - {standard}")

    # Step 2: Determine mandatory PPE
    print(f"\n[OK] Step 2: Mandatory PPE Requirements")
    for ppe in assessment['mandatory_ppe']:
        print(f"      - {ppe}")

    # Step 3: ANSI compliance for each PPE item
    print(f"\n[OK] Step 3: ANSI Certification Requirements")

    # Eye protection
    eye_cert = ansi_engine.validate_equipment_certification(
        "impact_rated_safety_glasses",
        "Z87+"
    )
    print(f"   Eye Protection: {eye_cert['required_marking']} - {eye_cert['ansi_standard']}")

    # Hearing protection (calculate NRR for angle grinder ~110 dBA)
    nrr_req = ansi_engine.get_nrr_requirement(110)
    print(f"   Hearing Protection: NRR {nrr_req['minimum_nrr_labeled']}+ dB - {nrr_req['ansi_standard']}")

    # Hand protection
    cut_rec = ansi_engine.get_cut_resistance_recommendation("sharp metal edges")
    print(f"   Hand Protection: Cut Level {cut_rec['recommended_cut_level']} - {cut_rec['ansi_standard']}")

    # Step 4: Validate worker's available PPE
    print(f"\n[OK] Step 4: PPE Compliance Validation")

    worker_ppe = [
        "safety_glasses",  # Z87+
        "face_shield",
        "work_gloves",  # A4 cut resistant
        "hearing_protection",  # NRR 30
        "hard_hat",  # Construction site
        "steel_toe_boots"
    ]

    is_compliant, missing = osha_engine.validate_ppe_compliance(
        assessment,
        worker_ppe
    )

    print(f"   Worker PPE: {', '.join(worker_ppe)}")
    print(f"   Compliance Status: {'[OK] COMPLIANT' if is_compliant else '[FAIL] NON-COMPLIANT'}")

    if missing:
        print(f"   Missing Mandatory PPE: {', '.join(missing)}")
    else:
        print(f"   [OK] All mandatory PPE requirements met")

    # Step 5: Additional recommendations
    print(f"\n[OK] Step 5: Additional Safety Recommendations")
    for note in assessment['compliance_notes']:
        print(f"   - {note}")

    return True


def run_all_tests():
    """Run all safety compliance tests"""
    print("\n" + "="*80)
    print("PHASE 4: SAFETY COMPLIANCE SYSTEM TEST SUITE")
    print("Testing OSHA and ANSI Compliance Engines")
    print("="*80)

    tests = [
        ("OSHA Compliance Engine", test_osha_compliance_engine),
        ("Task Risk Assessment", test_task_risk_assessment),
        ("PPE Compliance Validation", test_ppe_compliance_validation),
        ("ANSI Compliance Engine", test_ansi_compliance_engine),
        ("NRR Calculations", test_nrr_calculations),
        ("Cut Resistance Recommendations", test_cut_resistance_recommendations),
        ("ANSI Standard Details", test_ansi_standard_details),
        ("Real-World Scenario", test_real_world_scenario)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            logger.info(f"Running test: {test_name}")
            result = test_func()
            if result:
                passed += 1
                print(f"\n[OK] {test_name}: PASSED")
            else:
                failed += 1
                print(f"\n[FAIL] {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"\n[FAIL] {test_name}: FAILED")
            print(f"   Error: {e}")
            logger.error(f"Test failed: {test_name}", exc_info=True)

    # Final summary
    print("\n" + "="*80)
    print("TEST SUITE SUMMARY")
    print("="*80)
    print(f"Total Tests: {passed + failed}")
    print(f"[OK] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    print("="*80)

    if failed == 0:
        print("\n[SUCCESS] ALL TESTS PASSED - Safety Compliance System is Production Ready!")
    else:
        print(f"\n[WARN]  {failed} test(s) failed - Review errors above")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
