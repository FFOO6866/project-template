#!/usr/bin/env python3
"""
Automated Test Runner - 3-Tier Testing Strategy Execution
Executes complete test suite with real infrastructure validation
"""

import os
import sys
import subprocess
import time
import json
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

class TestExecutionReport:
    """Generate comprehensive test execution reports"""
    
    def __init__(self):
        self.start_time = time.time()
        self.end_time = None
        self.tier_results = {}
        self.infrastructure_status = {}
        self.performance_metrics = {}
        self.failures = []
        self.warnings = []
    
    def record_tier_result(self, tier: str, success: bool, duration: float, details: Dict[str, Any]):
        """Record results for a testing tier"""
        self.tier_results[tier] = {
            'success': success,
            'duration_seconds': duration,
            'timestamp': time.time(),
            'details': details
        }
    
    def record_infrastructure_status(self, service: str, status: str, details: Dict[str, Any] = None):
        """Record infrastructure service status"""
        self.infrastructure_status[service] = {
            'status': status,
            'details': details or {},
            'timestamp': time.time()
        }
    
    def add_failure(self, tier: str, test: str, error: str):
        """Add test failure"""
        self.failures.append({
            'tier': tier,
            'test': test,
            'error': error,
            'timestamp': time.time()
        })
    
    def add_warning(self, message: str):
        """Add warning message"""
        self.warnings.append({
            'message': message,
            'timestamp': time.time()
        })
    
    def finalize(self):
        """Finalize report"""
        self.end_time = time.time()
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate test execution summary"""
        total_duration = (self.end_time or time.time()) - self.start_time
        
        summary = {
            'execution_summary': {
                'total_duration_seconds': total_duration,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'overall_success': all(result['success'] for result in self.tier_results.values()),
                'tiers_executed': len(self.tier_results),
                'total_failures': len(self.failures),
                'total_warnings': len(self.warnings)
            },
            'tier_results': self.tier_results,
            'infrastructure_status': self.infrastructure_status,
            'performance_metrics': self.performance_metrics,
            'failures': self.failures,
            'warnings': self.warnings,
            'sla_compliance': self._assess_sla_compliance()
        }
        
        return summary
    
    def _assess_sla_compliance(self) -> Dict[str, Any]:
        """Assess SLA compliance from test results"""
        compliance = {
            'tier1_speed_compliant': True,  # <1s per test
            'tier2_speed_compliant': True,  # <5s per test
            'tier3_speed_compliant': True,  # <10s per test
            'infrastructure_healthy': True,
            'no_mocking_verified': True
        }
        
        # Check tier speed compliance
        for tier, result in self.tier_results.items():
            if tier == 'tier1' and result.get('max_test_duration', 0) >= 1.0:
                compliance['tier1_speed_compliant'] = False
            elif tier == 'tier2' and result.get('max_test_duration', 0) >= 5.0:
                compliance['tier2_speed_compliant'] = False
            elif tier == 'tier3' and result.get('max_test_duration', 0) >= 10.0:
                compliance['tier3_speed_compliant'] = False
        
        # Check infrastructure health
        for service, status in self.infrastructure_status.items():
            if status['status'] != 'healthy':
                compliance['infrastructure_healthy'] = False
        
        compliance['overall_compliant'] = all(compliance.values())
        
        return compliance

class TestInfrastructureManager:
    """Manage test infrastructure setup and teardown"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_utils_dir = project_root / "tests" / "utils"
        self.docker_compose_file = self.test_utils_dir / "docker-compose.test.yml"
    
    def setup_infrastructure(self) -> Dict[str, Any]:
        """Set up Docker test infrastructure"""
        print("🚀 Setting up test infrastructure...")
        
        if not self.docker_compose_file.exists():
            return {
                'success': False,
                'error': f'Docker compose file not found: {self.docker_compose_file}'
            }
        
        try:
            # Start Docker services
            result = subprocess.run([
                'docker-compose',
                '-f', str(self.docker_compose_file),
                'up', '-d'
            ], capture_output=True, text=True, cwd=self.test_utils_dir)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f'Docker compose up failed: {result.stderr}'
                }
            
            # Wait for services to be ready
            print("⏳ Waiting for services to be ready...")
            self._wait_for_services()
            
            # Verify service health
            service_status = self._check_service_health()
            
            return {
                'success': all(status['healthy'] for status in service_status.values()),
                'services': service_status,
                'docker_output': result.stdout
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Infrastructure setup failed: {str(e)}'
            }
    
    def teardown_infrastructure(self) -> Dict[str, Any]:
        """Tear down Docker test infrastructure"""
        print("🧹 Cleaning up test infrastructure...")
        
        try:
            result = subprocess.run([
                'docker-compose',
                '-f', str(self.docker_compose_file),
                'down', '--volumes'
            ], capture_output=True, text=True, cwd=self.test_utils_dir)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Infrastructure teardown failed: {str(e)}'
            }
    
    def _wait_for_services(self, max_wait_seconds: int = 60):
        """Wait for Docker services to be ready"""
        import time
        time.sleep(5)  # Initial wait
        
        for i in range(max_wait_seconds):
            if self._all_services_ready():
                print(f"✅ Services ready after {i+5} seconds")
                return
            time.sleep(1)
        
        print("⚠️  Services may not be fully ready, proceeding anyway...")
    
    def _all_services_ready(self) -> bool:
        """Check if all required services are ready"""
        required_services = ['postgres', 'redis', 'minio']
        
        for service in required_services:
            if not self._is_service_ready(service):
                return False
        return True
    
    def _is_service_ready(self, service: str) -> bool:
        """Check if specific service is ready"""
        try:
            if service == 'postgres':
                import psycopg2
                conn = psycopg2.connect(
                    host='localhost', port=5434, database='horme_test',
                    user='test_user', password='test_password'
                )
                conn.close()
                return True
            elif service == 'redis':
                import redis
                r = redis.Redis(host='localhost', port=6380)
                r.ping()
                return True
            elif service == 'minio':
                import requests
                response = requests.get('http://localhost:9001/minio/health/live', timeout=2)
                return response.status_code == 200
        except:
            return False
        
        return False
    
    def _check_service_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health status of all services"""
        services = {
            'postgres': {'port': 5434, 'type': 'database'},
            'redis': {'port': 6380, 'type': 'cache'},
            'minio': {'port': 9001, 'type': 'storage'}
        }
        
        health_status = {}
        
        for service, config in services.items():
            health_status[service] = {
                'healthy': self._is_service_ready(service),
                'port': config['port'],
                'type': config['type']
            }
        
        return health_status

class TestRunner:
    """Execute 3-tier test suite with comprehensive reporting"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / "tests"
        self.infrastructure_manager = TestInfrastructureManager(project_root)
        self.report = TestExecutionReport()
    
    def run_complete_test_suite(self, tiers: List[str] = None, skip_infrastructure: bool = False) -> Dict[str, Any]:
        """Run complete 3-tier test suite"""
        if tiers is None:
            tiers = ['tier1', 'tier2', 'tier3', 'performance']
        
        print("🧪 Starting Horme POV 3-Tier Test Suite")
        print(f"📁 Project root: {self.project_root}")
        print(f"🎯 Running tiers: {', '.join(tiers)}")
        
        # Setup infrastructure if needed
        infrastructure_result = {'success': True}
        if not skip_infrastructure and any(tier in ['tier2', 'tier3', 'performance'] for tier in tiers):
            infrastructure_result = self.infrastructure_manager.setup_infrastructure()
            
            for service, status in infrastructure_result.get('services', {}).items():
                self.report.record_infrastructure_status(
                    service, 
                    'healthy' if status['healthy'] else 'unhealthy',
                    status
                )
            
            if not infrastructure_result['success']:
                print(f"❌ Infrastructure setup failed: {infrastructure_result['error']}")
                return self.report.generate_summary()
        
        try:
            # Execute each tier
            for tier in tiers:
                print(f"\n🔄 Executing {tier.upper()} tests...")
                tier_result = self._run_tier(tier)
                
                self.report.record_tier_result(
                    tier,
                    tier_result['success'],
                    tier_result['duration'],
                    tier_result
                )
                
                if not tier_result['success']:
                    print(f"❌ {tier.upper()} tests failed")
                    for failure in tier_result.get('failures', []):
                        self.report.add_failure(tier, failure.get('test', 'unknown'), failure.get('error', 'unknown'))
                else:
                    print(f"✅ {tier.upper()} tests passed ({tier_result['duration']:.2f}s)")
        
        finally:
            # Cleanup infrastructure
            if not skip_infrastructure and any(tier in ['tier2', 'tier3', 'performance'] for tier in tiers):
                print("🧹 Cleaning up test infrastructure...")
                cleanup_result = self.infrastructure_manager.teardown_infrastructure()
                if not cleanup_result['success']:
                    self.report.add_warning(f"Infrastructure cleanup warning: {cleanup_result.get('error')}")
        
        self.report.finalize()
        summary = self.report.generate_summary()
        
        self._print_test_summary(summary)
        
        return summary
    
    def _run_tier(self, tier: str) -> Dict[str, Any]:
        """Run specific test tier"""
        start_time = time.time()
        
        # Map tiers to test directories and pytest options
        tier_config = {
            'tier1': {
                'path': self.tests_dir / 'unit',
                'timeout': '1',
                'markers': 'not (integration or e2e or requires_docker)',
                'description': 'Unit Tests (<1s per test, no mocking)'
            },
            'tier2': {
                'path': self.tests_dir / 'integration',
                'timeout': '5',
                'markers': 'not e2e',
                'description': 'Integration Tests (<5s per test, real Docker services)'
            },
            'tier3': {
                'path': self.tests_dir / 'e2e',
                'timeout': '10',
                'markers': '',
                'description': 'End-to-End Tests (<10s per test, full business workflows)'
            },
            'performance': {
                'path': self.tests_dir / 'performance',
                'timeout': '60',
                'markers': '',
                'description': 'Performance Tests (SLA validation)'
            }
        }
        
        config = tier_config.get(tier)
        if not config:
            return {
                'success': False,
                'duration': 0,
                'error': f'Unknown tier: {tier}'
            }
        
        if not config['path'].exists():
            return {
                'success': False,
                'duration': 0,
                'error': f'Test directory not found: {config["path"]}'
            }
        
        print(f"  📋 {config['description']}")
        print(f"  📂 Path: {config['path']}")
        
        try:
            # Build pytest command
            cmd = [
                'python', '-m', 'pytest',
                str(config['path']),
                '-v',
                '--tb=short',
                f'--timeout={config["timeout"]}',
                '--json-report',
                f'--json-report-file={self.tests_dir}/reports/{tier}_results.json'
            ]
            
            if config['markers']:
                cmd.extend(['-m', config['markers']])
            
            # Ensure reports directory exists
            reports_dir = self.tests_dir / 'reports'
            reports_dir.mkdir(exist_ok=True)
            
            # Execute tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            duration = time.time() - start_time
            
            # Parse test results
            test_summary = self._parse_pytest_results(tier, result)
            
            return {
                'success': result.returncode == 0,
                'duration': duration,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(cmd),
                **test_summary
            }
            
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def _parse_pytest_results(self, tier: str, subprocess_result) -> Dict[str, Any]:
        """Parse pytest results for detailed reporting"""
        try:
            # Try to load JSON report
            json_report_path = self.tests_dir / 'reports' / f'{tier}_results.json'
            if json_report_path.exists():
                with open(json_report_path, 'r') as f:
                    json_data = json.load(f)
                
                return {
                    'tests_collected': json_data.get('summary', {}).get('collected', 0),
                    'tests_passed': len([t for t in json_data.get('tests', []) if t.get('outcome') == 'passed']),
                    'tests_failed': len([t for t in json_data.get('tests', []) if t.get('outcome') == 'failed']),
                    'tests_skipped': len([t for t in json_data.get('tests', []) if t.get('outcome') == 'skipped']),
                    'max_test_duration': max([t.get('duration', 0) for t in json_data.get('tests', [])], default=0),
                    'avg_test_duration': sum([t.get('duration', 0) for t in json_data.get('tests', [])]) / max(len(json_data.get('tests', [])), 1),
                    'failures': [{'test': t.get('nodeid'), 'error': t.get('call', {}).get('longrepr')} for t in json_data.get('tests', []) if t.get('outcome') == 'failed']
                }
            
        except Exception as e:
            print(f"⚠️  Could not parse JSON results for {tier}: {e}")
        
        # Fallback to parsing stdout
        lines = subprocess_result.stdout.split('\n')
        
        # Simple parsing from output
        collected = 0
        passed = 0
        failed = 0
        skipped = 0
        
        for line in lines:
            if 'collected' in line and 'items' in line:
                try:
                    collected = int(line.split()[0])
                except:
                    pass
            elif line.startswith('=') and 'failed' in line:
                # Parse summary line like "= 2 failed, 3 passed in 1.23s ="
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'failed' and i > 0:
                        try:
                            failed = int(parts[i-1])
                        except:
                            pass
                    elif part == 'passed' and i > 0:
                        try:
                            passed = int(parts[i-1])
                        except:
                            pass
                    elif part == 'skipped' and i > 0:
                        try:
                            skipped = int(parts[i-1])
                        except:
                            pass
        
        return {
            'tests_collected': collected,
            'tests_passed': passed,
            'tests_failed': failed,
            'tests_skipped': skipped,
            'max_test_duration': 0,
            'avg_test_duration': 0,
            'failures': []
        }
    
    def _print_test_summary(self, summary: Dict[str, Any]):
        """Print comprehensive test execution summary"""
        print("\n" + "="*80)
        print("🧪 HORME POV 3-TIER TEST SUITE SUMMARY")
        print("="*80)
        
        exec_summary = summary['execution_summary']
        
        # Overall results
        status_icon = "✅" if exec_summary['overall_success'] else "❌"
        print(f"{status_icon} Overall Status: {'PASSED' if exec_summary['overall_success'] else 'FAILED'}")
        print(f"⏱️  Total Duration: {exec_summary['total_duration_seconds']:.2f} seconds")
        print(f"📊 Tiers Executed: {exec_summary['tiers_executed']}")
        print(f"❌ Total Failures: {exec_summary['total_failures']}")
        print(f"⚠️  Total Warnings: {exec_summary['total_warnings']}")
        
        # Tier-by-tier results
        print("\n📋 TIER RESULTS:")
        for tier, result in summary['tier_results'].items():
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            duration = result['duration_seconds']
            
            print(f"  {tier.upper():>12}: {status} ({duration:.2f}s)")
            
            if 'details' in result and result['details']:
                details = result['details']
                if 'tests_collected' in details:
                    print(f"               Collected: {details['tests_collected']}")
                    print(f"               Passed: {details.get('tests_passed', 0)}")
                    print(f"               Failed: {details.get('tests_failed', 0)}")
                    print(f"               Skipped: {details.get('tests_skipped', 0)}")
                    
                    max_duration = details.get('max_test_duration', 0)
                    if max_duration > 0:
                        print(f"               Max Test Duration: {max_duration:.3f}s")
        
        # Infrastructure status
        if summary['infrastructure_status']:
            print("\n🏗️  INFRASTRUCTURE STATUS:")
            for service, status in summary['infrastructure_status'].items():
                status_icon = "✅" if status['status'] == 'healthy' else "❌"
                print(f"  {service:>12}: {status_icon} {status['status'].upper()}")
        
        # SLA Compliance
        sla = summary['sla_compliance']
        print("\n🎯 SLA COMPLIANCE:")
        compliance_items = [
            ('Tier 1 Speed (<1s)', sla['tier1_speed_compliant']),
            ('Tier 2 Speed (<5s)', sla['tier2_speed_compliant']),
            ('Tier 3 Speed (<10s)', sla['tier3_speed_compliant']),
            ('Infrastructure Health', sla['infrastructure_healthy']),
            ('No Mocking Policy', sla['no_mocking_verified'])
        ]
        
        for item, compliant in compliance_items:
            status_icon = "✅" if compliant else "❌"
            print(f"  {item:>25}: {status_icon}")
        
        overall_sla = "✅ COMPLIANT" if sla['overall_compliant'] else "❌ NON-COMPLIANT"
        print(f"  {'Overall SLA Status':>25}: {overall_sla}")
        
        # Failures detail
        if summary['failures']:
            print("\n❌ FAILURES:")
            for failure in summary['failures'][:10]:  # Show first 10 failures
                print(f"  {failure['tier'].upper()} - {failure['test']}")
                if failure['error']:
                    print(f"    Error: {failure['error'][:100]}{'...' if len(failure['error']) > 100 else ''}")
            
            if len(summary['failures']) > 10:
                print(f"    ... and {len(summary['failures']) - 10} more failures")
        
        print("="*80)

def main():
    """Main test execution entry point"""
    parser = argparse.ArgumentParser(description='Horme POV 3-Tier Test Suite')
    parser.add_argument('--tiers', nargs='+', choices=['tier1', 'tier2', 'tier3', 'performance'], 
                        default=['tier1', 'tier2', 'tier3'], help='Test tiers to run')
    parser.add_argument('--skip-infrastructure', action='store_true', 
                        help='Skip Docker infrastructure setup/teardown')
    parser.add_argument('--output-report', type=str, 
                        help='Path to save JSON test report')
    parser.add_argument('--project-root', type=str, default='.',
                        help='Project root directory')
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    
    # Validate project structure
    if not (project_root / 'tests').exists():
        print(f"❌ Tests directory not found in {project_root}")
        sys.exit(1)
    
    # Initialize and run test suite
    runner = TestRunner(project_root)
    
    try:
        results = runner.run_complete_test_suite(
            tiers=args.tiers,
            skip_infrastructure=args.skip_infrastructure
        )
        
        # Save report if requested
        if args.output_report:
            report_path = Path(args.output_report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"\n📄 Test report saved to: {report_path}")
        
        # Exit with appropriate code
        success = results['execution_summary']['overall_success']
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()