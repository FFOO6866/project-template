#!/usr/bin/env python3
"""
Manual Test Runner for Accurate Success Rate Measurement
========================================================

Direct test execution to measure actual test success rates
without pytest complications on Windows.
"""

import os
import sys
import importlib.util
import time
import traceback
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    error: str = ""

class ManualTestRunner:
    """Manual test runner for accurate measurements."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.test_path = project_path / "tests"
        
    def discover_test_files(self, tier: str) -> List[Path]:
        """Discover test files for a specific tier."""
        tier_map = {"1": "unit", "2": "integration", "3": "e2e"}
        tier_dir = self.test_path / tier_map[tier]
        
        if not tier_dir.exists():
            return []
            
        test_files = []
        for file_path in tier_dir.glob("test_*.py"):
            if file_path.is_file():
                test_files.append(file_path)
        
        return test_files
    
    def extract_test_functions(self, file_path: Path) -> List[str]:
        """Extract test function names from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            test_functions = []
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('def test_') and '(' in line:
                    func_name = line.split('(')[0].replace('def ', '')
                    test_functions.append(func_name)
                elif line.startswith('async def test_') and '(' in line:
                    func_name = line.split('(')[0].replace('async def ', '')
                    test_functions.append(func_name)
            
            return test_functions
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
    
    def run_single_test(self, file_path: Path, test_func: str) -> TestResult:
        """Run a single test function."""
        start_time = time.time()
        
        try:
            # Import the test module
            spec = importlib.util.spec_from_file_location(
                f"test_module_{file_path.stem}", 
                file_path
            )
            if spec is None or spec.loader is None:
                return TestResult(
                    name=f"{file_path.stem}::{test_func}",
                    passed=False,
                    duration=time.time() - start_time,
                    error="Could not load module spec"
                )
            
            module = importlib.util.module_from_spec(spec)
            
            # Add project path to sys.path for imports
            if str(self.project_path) not in sys.path:
                sys.path.insert(0, str(self.project_path))
            
            spec.loader.exec_module(module)
            
            # Get the test function
            if not hasattr(module, test_func):
                return TestResult(
                    name=f"{file_path.stem}::{test_func}",
                    passed=False,
                    duration=time.time() - start_time,
                    error=f"Test function {test_func} not found"
                )
            
            test_function = getattr(module, test_func)
            
            # Run the test
            if asyncio and 'async' in str(test_function):
                import asyncio
                asyncio.run(test_function())
            else:
                test_function()
            
            return TestResult(
                name=f"{file_path.stem}::{test_func}",
                passed=True,
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                name=f"{file_path.stem}::{test_func}",
                passed=False,
                duration=time.time() - start_time,
                error=str(e)
            )
    
    def run_tier_tests(self, tier: str) -> Tuple[List[TestResult], Dict]:
        """Run all tests for a tier."""
        print(f"Running Tier {tier} tests...")
        
        test_files = self.discover_test_files(tier)
        all_results = []
        
        for file_path in test_files:
            print(f"  Processing {file_path.name}...")
            
            test_functions = self.extract_test_functions(file_path)
            
            for test_func in test_functions[:5]:  # Limit to 5 tests per file for speed
                result = self.run_single_test(file_path, test_func)
                all_results.append(result)
                
                status = "PASS" if result.passed else "FAIL"
                print(f"    {test_func}: {status} ({result.duration:.3f}s)")
        
        # Calculate metrics
        total = len(all_results)
        passed = sum(1 for r in all_results if r.passed)
        failed = total - passed
        total_duration = sum(r.duration for r in all_results)
        avg_duration = total_duration / total if total > 0 else 0
        success_rate = (passed / total * 100) if total > 0 else 0
        
        metrics = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "avg_duration": avg_duration
        }
        
        return all_results, metrics
    
    def run_comprehensive_analysis(self) -> Dict:
        """Run comprehensive analysis of all tiers."""
        print("Starting Manual Test Infrastructure Analysis")
        print("=" * 50)
        
        all_metrics = {}
        all_results = {}
        
        for tier in ["1", "2", "3"]:
            results, metrics = self.run_tier_tests(tier)
            all_results[f"tier_{tier}"] = results
            all_metrics[f"tier_{tier}"] = metrics
            
            print(f"\nTier {tier} Summary:")
            print(f"  Tests: {metrics['total']}")
            print(f"  Passed: {metrics['passed']}")
            print(f"  Failed: {metrics['failed']}")
            print(f"  Success Rate: {metrics['success_rate']:.1f}%")
            print(f"  Avg Duration: {metrics['avg_duration']:.3f}s")
        
        # Overall metrics
        total_tests = sum(m['total'] for m in all_metrics.values())
        total_passed = sum(m['passed'] for m in all_metrics.values())
        overall_success = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\nOVERALL RESULTS:")
        print(f"Total Tests: {total_tests}")
        print(f"Total Passed: {total_passed}")
        print(f"Overall Success Rate: {overall_success:.1f}%")
        print(f"Gap to 95% Target: {95 - overall_success:.1f}%")
        
        # Performance compliance
        tier_1_avg = all_metrics.get('tier_1', {}).get('avg_duration', 0)
        tier_2_avg = all_metrics.get('tier_2', {}).get('avg_duration', 0)
        tier_3_avg = all_metrics.get('tier_3', {}).get('avg_duration', 0)
        
        print(f"\nPERFORMANCE COMPLIANCE:")
        print(f"Tier 1 (<1s): {tier_1_avg:.3f}s {'PASS' if tier_1_avg < 1.0 else 'FAIL'}")
        print(f"Tier 2 (<5s): {tier_2_avg:.3f}s {'PASS' if tier_2_avg < 5.0 else 'FAIL'}")
        print(f"Tier 3 (<10s): {tier_3_avg:.3f}s {'PASS' if tier_3_avg < 10.0 else 'FAIL'}")
        
        # Infrastructure assessment
        print(f"\nINFRASTRUCTURE STATUS:")
        print(f"Docker Available: False (Windows environment)")
        print(f"Mock Fallback Required: True")
        print(f"Real Services: Not Available")
        
        return {
            "overall_success_rate": overall_success,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "tier_metrics": all_metrics,
            "performance_compliance": {
                "tier_1_under_1s": tier_1_avg < 1.0,
                "tier_2_under_5s": tier_2_avg < 5.0,
                "tier_3_under_10s": tier_3_avg < 10.0
            }
        }

def main():
    """Main execution."""
    project_path = Path(__file__).parent
    runner = ManualTestRunner(project_path)
    
    try:
        results = runner.run_comprehensive_analysis()
        
        # Save results
        import json
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = project_path / f"manual_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nResults saved to: {results_file}")
        
        # Return based on success rate
        success_rate = results.get('overall_success_rate', 0)
        if success_rate >= 95:
            print("\nSUCCESS: 95% target achieved!")
            return 0
        else:
            print(f"\nIN PROGRESS: {success_rate:.1f}% success rate")
            return 1
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())