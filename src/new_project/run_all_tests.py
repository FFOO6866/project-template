#!/usr/bin/env python3
"""
Testing Infrastructure - 3-Tier Strategy Test Runner
==================================================

Comprehensive test runner for local development and CI/CD validation.
Executes all three tiers of testing with proper reporting and validation.

Usage:
    python run_all_tests.py [--tier=unit|integration|e2e|performance|compliance|all]
    python run_all_tests.py --help
"""

import subprocess
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import tempfile
import os


class TestRunner:
    """Comprehensive test runner for 3-tier testing strategy"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results = {}
        self.start_time = datetime.now()
        self.project_root = Path(__file__).parent
        
        # Test configuration
        self.test_config = {
            'unit': {
                'path': 'tests/unit/',
                'markers': 'unit',
                'timeout': 1,
                'max_duration': timedelta(minutes=5),
                'description': 'Fast isolated tests with mocking allowed'
            },
            'integration': {
                'path': 'tests/integration/',
                'markers': 'integration and requires_docker',
                'timeout': 5,
                'max_duration': timedelta(minutes=15),
                'description': 'Real database connections, NO MOCKING'
            },
            'e2e': {
                'path': 'tests/e2e/',
                'markers': 'e2e and requires_docker',
                'timeout': 10,
                'max_duration': timedelta(minutes=25),
                'description': 'Complete system workflows with performance validation'
            },
            'performance': {
                'path': 'tests/performance/',
                'markers': 'performance',
                'timeout': 30,
                'max_duration': timedelta(minutes=20),
                'description': 'Performance benchmarks and SLA validation'
            },
            'compliance': {
                'path': 'tests/compliance/',
                'markers': 'compliance',
                'timeout': 15,
                'max_duration': timedelta(minutes=10),
                'description': 'Safety compliance and legal accuracy validation'
            }
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def run_pytest(self, tier: str, extra_args: List[str] = None) -> Dict[str, Any]:
        """Run pytest for a specific tier"""
        config = self.test_config[tier]
        test_start = datetime.now()
        
        self.log(f"Running {tier.upper()} tests: {config['description']}")
        
        # Build pytest command
        cmd = [
            sys.executable, '-m', 'pytest',
            config['path'],
            '-v',
            '--tb=short',
            f'--timeout={config["timeout"]}',
            f'--junit-xml=test-results-{tier}.xml',
            '-m', config['markers']
        ]
        
        # Add coverage for unit tests
        if tier == 'unit':
            cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=xml'])
        
        # Add extra arguments
        if extra_args:
            cmd.extend(extra_args)
        
        self.log(f"Command: {' '.join(cmd)}")
        
        # Run tests
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=config['max_duration'].total_seconds()
            )
            
            test_duration = datetime.now() - test_start
            
            return {
                'tier': tier,
                'success': result.returncode == 0,
                'return_code': result.returncode,
                'duration': test_duration.total_seconds(),
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(cmd),
                'timeout_limit': config['timeout'],
                'max_duration': config['max_duration'].total_seconds()
            }
            
        except subprocess.TimeoutExpired as e:
            test_duration = datetime.now() - test_start
            return {
                'tier': tier,
                'success': False,
                'return_code': -1,
                'duration': test_duration.total_seconds(),
                'stdout': '',
                'stderr': f'Test tier timed out after {config["max_duration"]}',
                'command': ' '.join(cmd),
                'timeout_limit': config['timeout'],
                'max_duration': config['max_duration'].total_seconds(),
                'timed_out': True
            }
        
        except Exception as e:
            test_duration = datetime.now() - test_start
            return {
                'tier': tier,
                'success': False,
                'return_code': -2,
                'duration': test_duration.total_seconds(),
                'stdout': '',
                'stderr': f'Unexpected error: {str(e)}',
                'command': ' '.join(cmd),
                'timeout_limit': config['timeout'],
                'max_duration': config['max_duration'].total_seconds(),
                'error': str(e)
            }
    
    def check_docker_services(self) -> Dict[str, bool]:
        """Check if Docker services are available"""
        self.log("Checking Docker services availability...")
        
        services = {
            'docker': False,
            'postgres': False,
            'neo4j': False,
            'chromadb': False,
            'redis': False
        }
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
            services['docker'] = result.returncode == 0
        except:
            pass
        
        if not services['docker']:
            self.log("Docker not available - integration and E2E tests will be skipped", "WARNING")
            return services
        
        # Check Docker services (if docker-compose is running)
        docker_compose_file = self.project_root / 'docker-compose.test.yml'
        if docker_compose_file.exists():
            try:
                # Check if services are running
                result = subprocess.run(
                    ['docker', 'compose', '-f', str(docker_compose_file), 'ps'],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    output = result.stdout.lower()
                    services['postgres'] = 'postgres' in output and 'running' in output
                    services['neo4j'] = 'neo4j' in output and 'running' in output
                    services['chromadb'] = 'chromadb' in output and 'running' in output
                    services['redis'] = 'redis' in output and 'running' in output
            except:
                pass
        
        # Log service status
        for service, available in services.items():
            status = "[Available]" if available else "[Not available]"
            self.log(f"  {service}: {status}")
        
        return services
    
    def run_tier(self, tier: str, services: Dict[str, bool]) -> Dict[str, Any]:
        """Run a specific test tier"""
        if tier not in self.test_config:
            raise ValueError(f"Unknown test tier: {tier}")
        
        # Check if tier requires Docker services
        if tier in ['integration', 'e2e'] and not services['docker']:
            self.log(f"Skipping {tier} tests - Docker not available", "WARNING")
            return {
                'tier': tier,
                'success': False,
                'skipped': True,
                'reason': 'Docker services not available',
                'duration': 0
            }
        
        # Run the tests
        result = self.run_pytest(tier)
        self.results[tier] = result
        
        # Log result
        status = "[PASSED]" if result['success'] else "[FAILED]"
        duration = f"{result['duration']:.2f}s"
        self.log(f"{tier.upper()} tests: {status} ({duration})")
        
        if not result['success'] and self.verbose:
            self.log(f"STDERR: {result['stderr']}", "ERROR")
        
        return result
    
    def run_all_tiers(self, selected_tiers: List[str] = None) -> Dict[str, Any]:
        """Run all or selected test tiers"""
        if selected_tiers is None:
            selected_tiers = list(self.test_config.keys())
        
        self.log("Starting 3-Tier Testing Strategy validation...")
        
        # Check Docker services
        services = self.check_docker_services()
        
        # Run tests in order
        tier_order = ['unit', 'integration', 'e2e', 'performance', 'compliance']
        failed_tiers = []
        
        for tier in tier_order:
            if tier not in selected_tiers:
                continue
                
            result = self.run_tier(tier, services)
            
            if not result.get('success', False) and not result.get('skipped', False):
                failed_tiers.append(tier)
                
                # Stop on critical failures for integration pipeline
                if tier in ['unit', 'integration'] and not result.get('skipped', False):
                    self.log(f"Critical failure in {tier} tier - stopping execution", "ERROR")
                    break
        
        # Generate summary
        total_duration = datetime.now() - self.start_time
        
        summary = {
            'start_time': self.start_time.isoformat(),
            'total_duration': total_duration.total_seconds(),
            'tiers_run': len([r for r in self.results.values() if not r.get('skipped', False)]),
            'tiers_passed': len([r for r in self.results.values() if r.get('success', False)]),
            'tiers_failed': len(failed_tiers),
            'tiers_skipped': len([r for r in self.results.values() if r.get('skipped', False)]),
            'failed_tiers': failed_tiers,
            'docker_services': services,
            'overall_success': len(failed_tiers) == 0,
            'results': self.results
        }
        
        return summary
    
    def generate_report(self, summary: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        report_lines = [
            "=" * 70,
            "TESTING INFRASTRUCTURE - 3-TIER STRATEGY RESULTS",
            "=" * 70,
            f"Start Time: {summary['start_time']}",
            f"Total Duration: {summary['total_duration']:.2f}s",
            f"Overall Status: {'[SUCCESS]' if summary['overall_success'] else '[FAILURE]'}",
            "",
            "TIER RESULTS:",
            "-" * 40
        ]
        
        # Add tier results
        for tier, config in self.test_config.items():
            if tier not in summary['results']:
                continue
                
            result = summary['results'][tier]
            
            if result.get('skipped', False):
                status = "[SKIPPED]"
                reason = f" ({result.get('reason', 'Unknown')})"
            elif result.get('success', False):
                status = "[PASSED]"
                reason = f" ({result['duration']:.2f}s)"
            else:
                status = "[FAILED]"
                reason = f" ({result['duration']:.2f}s, timeout: {result['timeout_limit']}s)"
            
            report_lines.extend([
                f"Tier {tier.upper()}: {status}{reason}",
                f"  Description: {config['description']}",
                f"  Path: {config['path']}",
                ""
            ])
        
        # Add Docker services status
        report_lines.extend([
            "DOCKER SERVICES:",
            "-" * 40
        ])
        
        for service, available in summary['docker_services'].items():
            status = "[Available]" if available else "[Not available]"
            report_lines.append(f"  {service}: {status}")
        
        report_lines.extend([
            "",
            "SUMMARY:",
            "-" * 40,
            f"  Tiers Run: {summary['tiers_run']}",
            f"  Tiers Passed: {summary['tiers_passed']}",
            f"  Tiers Failed: {summary['tiers_failed']}",
            f"  Tiers Skipped: {summary['tiers_skipped']}",
            ""
        ])
        
        if summary['failed_tiers']:
            report_lines.extend([
                "FAILED TIERS:",
                "-" * 40
            ])
            for tier in summary['failed_tiers']:
                result = summary['results'][tier]
                report_lines.extend([
                    f"  {tier.upper()}:",
                    f"    Return Code: {result['return_code']}",
                    f"    Duration: {result['duration']:.2f}s",
                    f"    Error: {result.get('stderr', 'No error message')[:200]}...",
                    ""
                ])
        
        report_lines.extend([
            "=" * 70,
            ""
        ])
        
        return "\n".join(report_lines)
    
    def save_report(self, summary: Dict[str, Any], filename: str = None) -> str:
        """Save detailed report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"
        
        report_path = self.project_root / filename
        
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.log(f"Detailed report saved to: {report_path}")
        return str(report_path)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Testing Infrastructure - 3-Tier Strategy Test Runner"
    )
    parser.add_argument(
        '--tier',
        choices=['unit', 'integration', 'e2e', 'performance', 'compliance', 'all'],
        default='all',
        help='Test tier to run (default: all)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--report',
        help='Save detailed report to specified file'
    )
    parser.add_argument(
        '--no-docker-check',
        action='store_true',
        help='Skip Docker service availability check'
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner(verbose=args.verbose)
    
    # Determine tiers to run
    if args.tier == 'all':
        selected_tiers = list(runner.test_config.keys())
    else:
        selected_tiers = [args.tier]
    
    try:
        # Run tests
        summary = runner.run_all_tiers(selected_tiers)
        
        # Generate and display report
        report = runner.generate_report(summary)
        print(report)
        
        # Save detailed report
        report_file = args.report or f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        runner.save_report(summary, report_file)
        
        # Exit with appropriate code
        sys.exit(0 if summary['overall_success'] else 1)
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Test execution interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        sys.exit(3)


if __name__ == "__main__":
    main()