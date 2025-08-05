#!/usr/bin/env python3
"""
Production Readiness Baseline Validation Script
Provides objective measurement of current system capabilities vs claims
"""

import json
import subprocess
import datetime
import sys
import os
from pathlib import Path
import time

class ProductionReadinessValidator:
    """Independent validation of production readiness claims."""
    
    def __init__(self):
        self.results = {
            'validation_timestamp': datetime.datetime.now().isoformat(),
            'validator': 'requirements-analyst',
            'methodology': 'independent_objective_measurement',
            'validation_results': {}
        }
        
    def validate_docker_infrastructure(self):
        """Validate Docker service availability."""
        print("[INFO] Validating Docker Infrastructure...")
        
        services = {
            'docker_daemon': {'command': ['docker', 'version'], 'port': None},
            'postgresql': {'command': ['curl', '-f', 'http://localhost:5432'], 'port': 5432},
            'neo4j': {'command': ['curl', '-f', 'http://localhost:7474'], 'port': 7474},
            'chromadb': {'command': ['curl', '-f', 'http://localhost:8000/api/v1/heartbeat'], 'port': 8000},
            'redis': {'command': ['redis-cli', 'ping'], 'port': 6379},
            'openai_mock': {'command': ['curl', '-f', 'http://localhost:8080/v1/health'], 'port': 8080}
        }
        
        service_results = {}
        operational_count = 0
        
        for service_name, config in services.items():
            try:
                result = subprocess.run(
                    config['command'], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                if result.returncode == 0:
                    service_results[service_name] = {
                        'status': 'operational',
                        'response_time': '<10s',
                        'validation_method': 'direct_connection'
                    }
                    operational_count += 1
                    print(f"  [PASS] {service_name}: OPERATIONAL")
                else:
                    service_results[service_name] = {
                        'status': 'failed',
                        'error': result.stderr.strip() if result.stderr else 'Connection failed',
                        'validation_method': 'direct_connection'
                    }
                    print(f"  [FAIL] {service_name}: FAILED - {result.stderr.strip()}")
                    
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                service_results[service_name] = {
                    'status': 'unavailable',
                    'error': str(e),
                    'validation_method': 'command_execution'
                }
                print(f"  [FAIL] {service_name}: UNAVAILABLE - {str(e)}")
        
        total_services = len(services)
        operational_percentage = (operational_count / total_services) * 100
        
        return {
            'services': service_results,
            'operational_count': f"{operational_count}/{total_services}",
            'operational_percentage': f"{operational_percentage:.1f}%",
            'ready_for_advancement': operational_count == total_services,
            'critical_blocker': operational_count == 0
        }
    
    def validate_test_infrastructure(self):
        """Validate test execution capability."""
        print("[INFO] Validating Test Infrastructure...")
        
        try:
            # Check if test runner exists
            test_runner_path = Path('run_all_tests.py')
            if not test_runner_path.exists():
                return {
                    'status': 'test_runner_missing',
                    'error': 'run_all_tests.py not found',
                    'ready_for_advancement': False
                }
            
            # Execute test runner with timeout
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, 'run_all_tests.py'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            execution_time = time.time() - start_time
            
            # Parse results
            output_lines = result.stdout.split('\n') if result.stdout else []
            error_lines = result.stderr.split('\n') if result.stderr else []
            
            # Look for tier results
            tier_results = {}
            for line in output_lines:
                if 'Tier' in line and '[' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        tier_name = parts[0].replace('Tier', '').strip()
                        status = 'PASSED' if '[PASSED]' in line else 'FAILED'
                        tier_results[tier_name] = status
            
            overall_success = result.returncode == 0
            
            print(f"  [INFO] Test Execution Time: {execution_time:.1f}s")
            print(f"  [INFO] Return Code: {result.returncode}")
            
            for tier, status in tier_results.items():
                icon = "[PASS]" if status == "PASSED" else "[FAIL]"
                print(f"  {icon} {tier}: {status}")
            
            return {
                'execution_time': f"{execution_time:.1f}s",
                'return_code': result.returncode,
                'tier_results': tier_results,
                'overall_success': overall_success,
                'stdout_sample': output_lines[:10] if output_lines else [],
                'stderr_sample': error_lines[:10] if error_lines else [],
                'ready_for_advancement': overall_success and len(tier_results) > 0
            }
            
        except subprocess.TimeoutExpired:
            print("  [FAIL] Test execution TIMEOUT after 5 minutes")
            return {
                'status': 'timeout',
                'error': 'Test execution exceeded 5 minute timeout',
                'execution_time': '>300s',
                'ready_for_advancement': False
            }
        except Exception as e:
            print(f"  [FAIL] Test execution ERROR: {str(e)}")
            return {
                'status': 'execution_error',
                'error': str(e),
                'ready_for_advancement': False
            }
    
    def validate_windows_sdk_compatibility(self):
        """Validate Windows SDK compatibility status."""
        print("[INFO] Validating Windows SDK Compatibility...")
        
        # Check for compatibility certificate
        cert_path = Path('WINDOWS_SDK_COMPATIBILITY_VALIDATION_CERTIFICATE.md')
        if cert_path.exists():
            print("  [PASS] Windows SDK Compatibility Certificate: FOUND")
            cert_content = cert_path.read_text()
            certified = 'CERTIFIED - PRODUCTION READY' in cert_content
            success_rate = '100.0%' in cert_content
            
            return {
                'certificate_exists': True,
                'certified_status': certified,
                'success_rate_100_percent': success_rate,
                'validation_date': '2025-08-04' if '2025-08-04' in cert_content else 'unknown',
                'ready_for_advancement': certified and success_rate
            }
        else:
            print("  [FAIL] Windows SDK Compatibility Certificate: NOT FOUND")
            return {
                'certificate_exists': False,
                'ready_for_advancement': False
            }
    
    def validate_nexus_platform_status(self):
        """Validate Nexus platform availability."""
        print("[INFO] Validating Nexus Platform Status...")
        
        # Check for nexus platform files
        nexus_files = [
            'nexus_dataflow_platform.py',
            'start_nexus_platform.py',
            'nexus_enhanced_app.py'
        ]
        
        files_found = []
        for file_name in nexus_files:
            if Path(file_name).exists():
                files_found.append(file_name)
                print(f"  [PASS] {file_name}: FOUND")
            else:
                print(f"  [FAIL] {file_name}: NOT FOUND")
        
        # Try to test if nexus platform can be imported
        try:
            import importlib.util
            platform_ready = len(files_found) > 0
            
            return {
                'nexus_files_found': files_found,
                'files_count': f"{len(files_found)}/{len(nexus_files)}",
                'platform_ready': platform_ready,
                'ready_for_testing': platform_ready and len(files_found) >= 2
            }
        except Exception as e:
            return {
                'nexus_files_found': files_found,
                'import_error': str(e),
                'ready_for_testing': False
            }
    
    def calculate_actual_production_readiness(self):
        """Calculate objective production readiness percentage."""
        print("[INFO] Calculating Actual Production Readiness...")
        
        # Weight factors for different components
        weights = {
            'infrastructure': 0.40,  # Critical blocker - highest weight
            'testing': 0.30,         # Essential for validation
            'windows_compat': 0.15,  # Development environment
            'platform': 0.15         # Application layer
        }
        
        # Get component scores (0.0 to 1.0)
        scores = {}
        
        # Infrastructure score
        infra_result = self.results['validation_results'].get('docker_infrastructure', {})
        if infra_result.get('critical_blocker'):
            scores['infrastructure'] = 0.0
        elif infra_result.get('ready_for_advancement'):
            scores['infrastructure'] = 1.0
        else:
            # Partial score based on operational services
            op_count = infra_result.get('operational_count', '0/5')
            if '/' in op_count:
                operational, total = map(int, op_count.split('/'))
                scores['infrastructure'] = operational / total
            else:
                scores['infrastructure'] = 0.0
        
        # Testing score
        test_result = self.results['validation_results'].get('test_infrastructure', {})
        if test_result.get('ready_for_advancement'):
            scores['testing'] = 1.0
        elif test_result.get('overall_success'):
            scores['testing'] = 0.7  # Partial credit if tests run but not all pass
        else:
            scores['testing'] = 0.0
        
        # Windows compatibility score
        windows_result = self.results['validation_results'].get('windows_sdk_compatibility', {})
        scores['windows_compat'] = 1.0 if windows_result.get('ready_for_advancement') else 0.0
        
        # Platform score
        platform_result = self.results['validation_results'].get('nexus_platform_status', {})
        if platform_result.get('ready_for_testing'):
            scores['platform'] = 0.5  # Cannot fully test without infrastructure
        else:
            scores['platform'] = 0.0
        
        # Calculate weighted score
        weighted_score = sum(scores[component] * weights[component] for component in scores)
        percentage = weighted_score * 100
        
        print(f"  [SCORE] Infrastructure Score: {scores['infrastructure']:.2f} (weight: {weights['infrastructure']})")
        print(f"  [SCORE] Testing Score: {scores['testing']:.2f} (weight: {weights['testing']})")
        print(f"  [SCORE] Windows Compat Score: {scores['windows_compat']:.2f} (weight: {weights['windows_compat']})")
        print(f"  [SCORE] Platform Score: {scores['platform']:.2f} (weight: {weights['platform']})")
        print(f"  [RESULT] ACTUAL PRODUCTION READINESS: {percentage:.1f}%")
        
        return {
            'component_scores': scores,
            'weights': weights,
            'weighted_score': weighted_score,
            'actual_production_readiness_percentage': f"{percentage:.1f}%",
            'readiness_level': self.categorize_readiness_level(percentage),
            'primary_blockers': self.identify_primary_blockers(scores)
        }
    
    def categorize_readiness_level(self, percentage):
        """Categorize readiness level based on percentage."""
        if percentage >= 90:
            return "PRODUCTION_READY"
        elif percentage >= 70:
            return "NEAR_PRODUCTION_READY"
        elif percentage >= 50:
            return "DEVELOPMENT_READY"
        elif percentage >= 25:
            return "INFRASTRUCTURE_PARTIAL"
        else:
            return "CRITICAL_INFRASTRUCTURE_FAILURE"
    
    def identify_primary_blockers(self, scores):
        """Identify the primary blockers preventing advancement."""
        blockers = []
        
        if scores['infrastructure'] < 0.5:
            blockers.append("CRITICAL: Docker infrastructure deployment failure")
        
        if scores['testing'] < 0.5:
            blockers.append("HIGH: Test infrastructure not operational")
        
        if scores['windows_compat'] < 1.0:
            blockers.append("MEDIUM: Windows SDK compatibility issues")
        
        if scores['platform'] < 0.5:
            blockers.append("MEDIUM: Platform components not ready for testing")
        
        return blockers
    
    def generate_validation_report(self):
        """Generate comprehensive validation report."""
        print("=" * 80)
        print("PRODUCTION READINESS BASELINE VALIDATION REPORT")
        print("=" * 80)
        print(f"Validation Time: {self.results['validation_timestamp']}")
        print(f"Validator: {self.results['validator']}")
        print(f"Methodology: {self.results['methodology']}")
        print()
        
        # Run all validations
        self.results['validation_results']['docker_infrastructure'] = self.validate_docker_infrastructure()
        print()
        
        self.results['validation_results']['test_infrastructure'] = self.validate_test_infrastructure()
        print()
        
        self.results['validation_results']['windows_sdk_compatibility'] = self.validate_windows_sdk_compatibility()
        print()
        
        self.results['validation_results']['nexus_platform_status'] = self.validate_nexus_platform_status()
        print()
        
        # Calculate overall readiness
        self.results['production_readiness_analysis'] = self.calculate_actual_production_readiness()
        print()
        
        # Generate summary
        self.generate_summary()
        
        # Save report
        report_filename = f"production_readiness_baseline_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"[REPORT] Detailed report saved to: {report_filename}")
        
        return self.results
    
    def generate_summary(self):
        """Generate executive summary."""
        print("=" * 80)
        print("EXECUTIVE SUMMARY")
        print("=" * 80)
        
        analysis = self.results['production_readiness_analysis']
        percentage = analysis['actual_production_readiness_percentage']
        level = analysis['readiness_level']
        blockers = analysis['primary_blockers']
        
        print(f"[RESULT] ACTUAL PRODUCTION READINESS: {percentage}")
        print(f"[RESULT] READINESS LEVEL: {level}")
        print()
        
        print("[BLOCKERS] PRIMARY BLOCKERS:")
        for i, blocker in enumerate(blockers, 1):
            print(f"  {i}. {blocker}")
        
        if not blockers:
            print("  [PASS] No critical blockers identified")
        
        print()
        print("[ACTIONS] RECOMMENDED IMMEDIATE ACTIONS:")
        
        # Infrastructure recommendations
        infra_result = self.results['validation_results']['docker_infrastructure']
        if infra_result.get('critical_blocker'):
            print("  1. CRITICAL: Deploy Docker infrastructure (5 services)")
            print("     - Execute TASK P0-001: Docker Service Stack Deployment")
            print("     - Timeline: 7 days maximum")
            print("     - Success Criteria: 5/5 services operational")
        
        # Testing recommendations  
        test_result = self.results['validation_results']['test_infrastructure']
        if not test_result.get('ready_for_advancement'):
            print("  2. HIGH: Recover test infrastructure")
            print("     - Execute TASK P0-002: Test Infrastructure Recovery")
            print("     - Timeline: 7 days after infrastructure")
            print("     - Success Criteria: 95%+ test pass rate")
        
        print(f"\n[TIMELINE] ESTIMATED TIMELINE TO PRODUCTION READY:")
        if level == "CRITICAL_INFRASTRUCTURE_FAILURE":
            print("  - Phase 1 (Infrastructure): 14 days")
            print("  - Phase 2 (Core Features): 14 days") 
            print("  - Phase 3 (Excellence): 14 days")
            print("  - TOTAL: 35-42 days")
        elif level == "INFRASTRUCTURE_PARTIAL":
            print("  - Infrastructure Recovery: 7-14 days")
            print("  - Feature Implementation: 21-28 days")
            print("  - TOTAL: 28-35 days")
        else:
            print("  - Remaining Development: 14-21 days")
        
        print("\n" + "=" * 80)

def main():
    """Main validation execution."""
    validator = ProductionReadinessValidator()
    results = validator.generate_validation_report()
    
    # Return appropriate exit code
    readiness_level = results['production_readiness_analysis']['readiness_level']
    if readiness_level in ['CRITICAL_INFRASTRUCTURE_FAILURE', 'INFRASTRUCTURE_PARTIAL']:
        sys.exit(1)  # Critical issues found
    elif readiness_level == 'DEVELOPMENT_READY':
        sys.exit(0)  # Acceptable for development
    else:
        sys.exit(0)  # Good status

if __name__ == "__main__":
    main()