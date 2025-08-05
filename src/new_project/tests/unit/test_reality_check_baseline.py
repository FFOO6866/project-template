"""
Reality Check Test Suite - Validate Current State vs Claims

This test suite implements test-first validation of the actual technical baseline
to address intermediate-reviewer concerns about discrepancies between claims and reality.

CRITICAL CONCERNS BEING VALIDATED:
1. Claims "SDK imports 100%" vs actual `ModuleNotFoundError: No module named 'resource'`
2. Claims "95%+ tests passing" vs actual test collection failures
3. Timeline disconnect: "24-48 hours" vs "4-6 weeks minimum"
4. Infrastructure claims vs actual execution state

Test Strategy:
- Tier 1: Validate SDK import status and resource module compatibility
- Test infrastructure baseline: Measure test discovery and success rates  
- Document actual state vs claimed state for honest assessment
"""

import pytest
import sys
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import json
import time


class RealityCheckBaseline:
    """Reality check validator for current technical state"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.results = {}
        
    def validate_sdk_imports(self) -> Dict[str, bool]:
        """Test actual SDK import success vs claimed 100%"""
        sdk_modules = [
            'kailash',
            'kailash.workflow',
            'kailash.workflow.builder',
            'kailash.runtime',
            'kailash.runtime.local',
            'kailash.nodes',
            'kailash.utils',
            'resource'  # Specifically test the failing module
        ]
        
        import_results = {}
        for module in sdk_modules:
            try:
                importlib.import_module(module)
                import_results[module] = True
            except (ImportError, ModuleNotFoundError) as e:
                import_results[module] = False
                print(f"IMPORT FAILURE: {module} - {e}")
                
        return import_results
    
    def measure_test_discovery_baseline(self) -> Dict[str, any]:
        """Measure actual test discovery and collection vs claimed success rates"""
        test_results = {}
        
        # Test discovery only (don't run tests yet)
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                str(self.project_root / 'tests'),
                '--collect-only', '--quiet'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            test_results['discovery_success'] = result.returncode == 0
            test_results['discovery_output'] = result.stdout
            test_results['discovery_errors'] = result.stderr
            
            # Count discovered tests
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                test_count = len([line for line in lines if '<Function' in line or '<Method' in line])
                test_results['discovered_test_count'] = test_count
            else:
                test_results['discovered_test_count'] = 0
                
        except Exception as e:
            test_results['discovery_success'] = False
            test_results['discovery_errors'] = str(e)
            test_results['discovered_test_count'] = 0
            
        return test_results
    
    def validate_windows_compatibility(self) -> Dict[str, bool]:
        """Test Windows-specific compatibility issues"""
        compatibility_results = {}
        
        # Test resource module specifically
        try:
            import resource
            compatibility_results['resource_module'] = True
        except ImportError:
            compatibility_results['resource_module'] = False
            
        # Test path handling
        try:
            from pathlib import Path
            test_path = Path("test/path/with/spaces and symbols")
            compatibility_results['path_handling'] = True
        except Exception:
            compatibility_results['path_handling'] = False
            
        # Test subprocess execution
        try:
            result = subprocess.run(['python', '--version'], capture_output=True, text=True)
            compatibility_results['subprocess_execution'] = result.returncode == 0
        except Exception:
            compatibility_results['subprocess_execution'] = False
            
        return compatibility_results
    
    def run_baseline_validation(self) -> Dict[str, any]:
        """Run complete baseline validation and return honest assessment"""
        print("=== REALITY CHECK: Current Technical Baseline ===")
        
        # 1. Validate SDK imports
        print("\n1. Testing SDK Import Claims vs Reality...")
        import_results = self.validate_sdk_imports()
        import_success_rate = sum(import_results.values()) / len(import_results) * 100
        
        # 2. Test discovery baseline
        print("\n2. Measuring Test Infrastructure Baseline...")
        test_results = self.measure_test_discovery_baseline()
        
        # 3. Windows compatibility
        print("\n3. Validating Windows Compatibility...")
        compatibility_results = self.validate_windows_compatibility()
        
        # Compile results
        baseline_results = {
            'timestamp': time.time(),
            'sdk_imports': {
                'results': import_results,
                'success_rate': import_success_rate,
                'claimed_rate': 100.0,
                'reality_gap': 100.0 - import_success_rate
            },
            'test_infrastructure': test_results,
            'windows_compatibility': compatibility_results,
            'assessment': self._generate_honest_assessment(import_success_rate, test_results, compatibility_results)
        }
        
        return baseline_results
    
    def _generate_honest_assessment(self, import_rate: float, test_results: Dict, compat_results: Dict) -> Dict[str, any]:
        """Generate honest technical assessment vs claims"""
        
        # Calculate actual timeline based on discovered gaps
        critical_issues = []
        if import_rate < 100:
            critical_issues.append(f"SDK imports at {import_rate:.1f}% (not 100%)")
        if not test_results.get('discovery_success', False):
            critical_issues.append("Test discovery failing")
        if not compat_results.get('resource_module', False):
            critical_issues.append("Resource module compatibility issue")
            
        # Realistic timeline assessment
        if len(critical_issues) == 0:
            estimated_timeline = "24-48 hours"
            readiness_level = "Production Ready"
        elif len(critical_issues) <= 2:
            estimated_timeline = "1-2 weeks"
            readiness_level = "Near Production"
        else:
            estimated_timeline = "4-6 weeks"
            readiness_level = "Development Phase"
            
        return {
            'critical_issues': critical_issues,
            'estimated_timeline': estimated_timeline,
            'readiness_level': readiness_level,
            'claimed_vs_actual': {
                'sdk_imports': f"Claimed 100%, Actual {import_rate:.1f}%",
                'test_success': f"Claimed 95%+, Actual {test_results.get('discovery_success', False)}",
                'timeline': f"Claimed 24-48h, Actual {estimated_timeline}"
            }
        }


class TestRealityCheckBaseline:
    """Test-first validation of current technical state"""
    
    @pytest.fixture
    def reality_checker(self):
        """Fixture to provide reality check validator"""
        return RealityCheckBaseline()
    
    def test_sdk_import_reality_vs_claims(self, reality_checker):
        """
        TEST: Validate actual SDK import success vs claimed 100%
        
        EXPECTATION: This test SHOULD FAIL initially to expose the reality gap
        between claims (100% SDK imports) and actual state (ModuleNotFoundError)
        """
        import_results = reality_checker.validate_sdk_imports()
        
        # Document the reality
        failed_imports = [module for module, success in import_results.items() if not success]
        success_rate = sum(import_results.values()) / len(import_results) * 100
        
        print(f"\n=== SDK IMPORT REALITY CHECK ===")
        print(f"Claimed: 100% SDK imports working")
        print(f"Actual: {success_rate:.1f}% SDK imports working")
        print(f"Failed imports: {failed_imports}")
        
        # This assertion should fail initially - that's the point
        assert success_rate == 100.0, (
            f"SDK import reality check FAILED: "
            f"Claimed 100% but actual is {success_rate:.1f}%. "
            f"Failed modules: {failed_imports}"
        )
    
    def test_test_infrastructure_baseline_vs_claims(self, reality_checker):
        """
        TEST: Measure actual test discovery/success vs claimed 95%+
        
        EXPECTATION: This test SHOULD FAIL initially to expose test infrastructure gaps
        """
        test_results = reality_checker.measure_test_discovery_baseline()
        
        print(f"\n=== TEST INFRASTRUCTURE REALITY CHECK ===")
        print(f"Claimed: 95%+ tests passing")
        print(f"Discovery Success: {test_results.get('discovery_success', False)}")
        print(f"Discovered Tests: {test_results.get('discovered_test_count', 0)}")
        
        if test_results.get('discovery_errors'):
            print(f"Discovery Errors: {test_results['discovery_errors']}")
        
        # This assertion should fail initially
        assert test_results.get('discovery_success', False), (
            f"Test infrastructure reality check FAILED: "
            f"Claimed 95%+ tests passing but test discovery is failing. "
            f"Errors: {test_results.get('discovery_errors', 'Unknown')}"
        )
        
        # Must have discovered at least some tests
        assert test_results.get('discovered_test_count', 0) > 0, (
            f"No tests discovered - infrastructure not functional"
        )
    
    def test_windows_compatibility_reality_check(self, reality_checker):
        """
        TEST: Validate Windows compatibility vs claims
        
        FOCUS: Specifically test the 'resource' module issue mentioned in concerns
        """
        compat_results = reality_checker.validate_windows_compatibility()
        
        print(f"\n=== WINDOWS COMPATIBILITY REALITY CHECK ===")
        print(f"Resource module: {compat_results.get('resource_module', False)}")
        print(f"Path handling: {compat_results.get('path_handling', False)}")
        print(f"Subprocess: {compat_results.get('subprocess_execution', False)}")
        
        # Test the specific issue mentioned in concerns
        assert compat_results.get('resource_module', False), (
            f"Windows compatibility FAILED: "
            f"ModuleNotFoundError: No module named 'resource' - "
            f"This contradicts claims of working SDK imports"
        )
    
    def test_generate_honest_technical_assessment(self, reality_checker):
        """
        TEST: Generate honest assessment of current state vs claims
        
        This test documents the actual timeline and readiness vs claimed timeline
        """
        baseline_results = reality_checker.run_baseline_validation()
        
        print(f"\n=== HONEST TECHNICAL ASSESSMENT ===")
        print(f"Timestamp: {baseline_results['timestamp']}")
        print(f"SDK Import Rate: {baseline_results['sdk_imports']['success_rate']:.1f}% (claimed 100%)")
        print(f"Reality Gap: {baseline_results['sdk_imports']['reality_gap']:.1f}%")
        
        assessment = baseline_results['assessment']
        print(f"\nCritical Issues: {len(assessment['critical_issues'])}")
        for issue in assessment['critical_issues']:
            print(f"  - {issue}")
            
        print(f"\nReadiness Level: {assessment['readiness_level']}")
        print(f"Estimated Timeline: {assessment['estimated_timeline']}")
        
        # Document the discrepancies
        claimed_vs_actual = assessment['claimed_vs_actual']
        print(f"\nClaims vs Reality:")
        for claim, reality in claimed_vs_actual.items():
            print(f"  {claim}: {reality}")
        
        # Store results for further analysis
        results_file = Path(__file__).parent.parent.parent / "reality_check_results.json"
        with open(results_file, 'w') as f:
            json.dump(baseline_results, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
        
        # This documents the state - no assertion needed, just measurement
        return baseline_results


if __name__ == "__main__":
    # Run reality check directly
    checker = RealityCheckBaseline()
    results = checker.run_baseline_validation()
    
    print("\n" + "="*60)
    print("REALITY CHECK COMPLETE")
    print("="*60)
    
    assessment = results['assessment']
    print(f"Current State: {assessment['readiness_level']}")
    print(f"Realistic Timeline: {assessment['estimated_timeline']}")
    print(f"Critical Issues: {len(assessment['critical_issues'])}")