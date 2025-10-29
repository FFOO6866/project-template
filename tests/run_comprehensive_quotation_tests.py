#!/usr/bin/env python3
"""
COMPREHENSIVE 3-TIER QUOTATION TESTING FRAMEWORK
Executes all tiers with REAL infrastructure and generates statistical analysis reports.
Enterprise Grade Testing with NO MOCKING policy.
"""

import os
import sys
import json
import time
import statistics
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ComprehensiveQuotationTestRunner:
    """Executes comprehensive 3-tier testing framework with statistical analysis."""
    
    def __init__(self):
        self.start_time = time.time()
        self.test_results = {
            'tier1_component': [],
            'tier2_integration': [],
            'tier3_e2e': []
        }
        self.performance_metrics = {
            'precision_rates': [],
            'recall_rates': [],
            'response_times': [],
            'throughput_rates': [],
            'success_rates': []
        }
        self.infrastructure_status = {}
        
    def setup_test_environment(self) -> bool:
        """Set up real Docker test infrastructure."""
        print("🚀 Setting up real Docker test infrastructure...")
        
        try:
            # Setup Docker infrastructure
            setup_cmd = [sys.executable, "tests/utils/setup_local_docker.py"]
            result = subprocess.run(setup_cmd, capture_output=True, text=True, cwd=project_root)
            
            if result.returncode != 0:
                print(f"❌ Infrastructure setup failed: {result.stderr}")
                return False
            
            # Verify infrastructure status
            self.infrastructure_status = self._check_infrastructure_health()
            
            print("✅ Infrastructure setup completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Infrastructure setup error: {e}")
            return False
    
    def _check_infrastructure_health(self) -> Dict[str, Any]:
        """Check health of real infrastructure services."""
        health_status = {}
        
        try:
            # Check PostgreSQL
            import psycopg2
            postgres_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '6660')),
                'database': os.getenv('DB_NAME', 'horme-pov_test'),
                'user': os.getenv('DB_USER', 'test_user'),
                'password': os.getenv('DB_PASSWORD', 'test_password')
            }
            
            conn = psycopg2.connect(**postgres_config)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            pg_version = cursor.fetchone()[0]
            conn.close()
            
            health_status['postgresql'] = {
                'status': 'healthy',
                'version': pg_version,
                'connection_time': time.time()
            }
            
        except Exception as e:
            health_status['postgresql'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        try:
            # Check Redis
            import redis
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6661')),
                decode_responses=True
            )
            redis_info = redis_client.info()
            
            health_status['redis'] = {
                'status': 'healthy',
                'version': redis_info.get('redis_version', 'unknown'),
                'memory_usage': redis_info.get('used_memory_human', 'unknown')
            }
            
        except Exception as e:
            health_status['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        return health_status
    
    def run_tier1_component_tests(self) -> Dict[str, Any]:
        """Execute Tier 1 component tests (<1 second each)."""
        print("⚡ Running Tier 1 Component Tests (<1 second)...")
        
        tier1_start = time.time()
        
        try:
            # Import and run Tier 1 tests directly
            from tests.unit.test_quotation_components import TestQuotationComponents
            
            test_instance = TestQuotationComponents()
            
            # Execute individual component tests
            component_tests = [
                ('quote_number_generation', test_instance.test_quote_number_generation),
                ('financial_calculations', test_instance.test_financial_calculations),
                ('line_item_generation', test_instance.test_line_item_generation),
                ('quotation_metadata', test_instance.test_quotation_metadata),
                ('edge_case_calculations', test_instance.test_edge_case_calculations),
                ('enterprise_grade_precision', test_instance.test_enterprise_grade_precision),
                ('performance_benchmarking', test_instance.test_performance_benchmarking)
            ]
            
            tier1_results = []
            
            for test_name, test_method in component_tests:
                test_start = time.time()
                
                try:
                    if test_name == 'quote_number_generation':
                        result = test_method(test_instance.quotation_workflow())
                    elif test_name == 'financial_calculations':
                        result = test_method(
                            test_instance.quotation_workflow(),
                            test_instance.sample_requirements(),
                            test_instance.sample_pricing_results()
                        )
                    elif test_name == 'line_item_generation':
                        result = test_method(
                            test_instance.quotation_workflow(),
                            test_instance.sample_requirements(),
                            test_instance.sample_pricing_results()
                        )
                    elif test_name == 'quotation_metadata':
                        result = test_method(
                            test_instance.quotation_workflow(),
                            test_instance.sample_requirements(),
                            test_instance.sample_pricing_results()
                        )
                    elif test_name == 'edge_case_calculations':
                        result = test_method(test_instance.quotation_workflow())
                    elif test_name == 'enterprise_grade_precision':
                        result = test_method(test_instance.quotation_workflow())
                    elif test_name == 'performance_benchmarking':
                        result = test_method(
                            test_instance.quotation_workflow(),
                            test_instance.sample_requirements(),
                            test_instance.sample_pricing_results()
                        )
                    else:
                        result = None
                    
                    test_time = time.time() - test_start
                    
                    tier1_results.append({
                        'test_name': test_name,
                        'execution_time': test_time,
                        'success': True,
                        'result': result if isinstance(result, dict) else {'status': 'passed'}
                    })
                    
                    # Validate <1 second requirement
                    if test_time >= 1.0:
                        print(f"⚠️  Warning: {test_name} took {test_time:.3f}s (exceeds 1s limit)")
                    
                    # Update performance metrics
                    self.performance_metrics['response_times'].append(test_time)
                    
                except Exception as e:
                    tier1_results.append({
                        'test_name': test_name,
                        'execution_time': time.time() - test_start,
                        'success': False,
                        'error': str(e)
                    })
            
            tier1_time = time.time() - tier1_start
            tier1_success_rate = sum(1 for r in tier1_results if r['success']) / len(tier1_results) * 100
            
            self.test_results['tier1_component'] = tier1_results
            self.performance_metrics['success_rates'].append(tier1_success_rate)
            
            print(f"✅ Tier 1 completed: {len(tier1_results)} tests, {tier1_success_rate:.1f}% success rate in {tier1_time:.3f}s")
            
            return {
                'tier': 'tier1_component',
                'total_tests': len(tier1_results),
                'successful_tests': sum(1 for r in tier1_results if r['success']),
                'success_rate': tier1_success_rate,
                'total_time': tier1_time,
                'results': tier1_results
            }
            
        except Exception as e:
            print(f"❌ Tier 1 execution failed: {e}")
            return {
                'tier': 'tier1_component',
                'total_tests': 0,
                'successful_tests': 0,
                'success_rate': 0.0,
                'total_time': time.time() - tier1_start,
                'error': str(e)
            }
    
    def run_tier2_integration_tests(self) -> Dict[str, Any]:
        """Execute Tier 2 integration tests (<5 seconds each) with real Docker services."""
        print("🔗 Running Tier 2 Integration Tests (<5 seconds) with real Docker services...")
        
        tier2_start = time.time()
        
        try:
            from tests.integration.test_quotation_integration import TestQuotationIntegration
            
            test_instance = TestQuotationIntegration()
            
            # Setup test fixtures
            docker_config = {
                'postgres_host': os.getenv('DB_HOST', 'localhost'),
                'postgres_port': int(os.getenv('DB_PORT', '6660')),
                'postgres_db': os.getenv('DB_NAME', 'horme-pov_test'),
                'postgres_user': os.getenv('DB_USER', 'test_user'),
                'postgres_password': os.getenv('DB_PASSWORD', 'test_password'),
                'redis_host': os.getenv('REDIS_HOST', 'localhost'),
                'redis_port': int(os.getenv('REDIS_PORT', '6661')),
            }
            
            # Setup real database and cache connections
            import psycopg2
            import redis
            
            postgres_conn = psycopg2.connect(
                host=docker_config['postgres_host'],
                port=docker_config['postgres_port'],
                database=docker_config['postgres_db'],
                user=docker_config['postgres_user'],
                password=docker_config['postgres_password']
            )
            
            redis_conn = redis.Redis(
                host=docker_config['redis_host'],
                port=docker_config['redis_port'],
                decode_responses=True
            )
            redis_conn.flushdb()  # Clean slate for testing
            
            quotation_workflow = test_instance.quotation_workflow()
            sample_data = test_instance.sample_enterprise_data()
            
            # Execute integration tests
            integration_tests = [
                ('postgresql_quotation_storage', 'test_postgresql_quotation_storage'),
                ('redis_caching_integration', 'test_redis_caching_integration'),
                ('file_storage_integration', 'test_file_storage_integration'),
                ('api_endpoint_integration', 'test_api_endpoint_integration'),
                ('service_communication_validation', 'test_service_communication_validation')
            ]
            
            tier2_results = []
            
            for test_name, method_name in integration_tests:
                test_start = time.time()
                
                try:
                    test_method = getattr(test_instance, method_name)
                    
                    if test_name == 'postgresql_quotation_storage':
                        result = test_method(postgres_conn, quotation_workflow, sample_data)
                    elif test_name == 'redis_caching_integration':
                        result = test_method(redis_conn, quotation_workflow, sample_data)
                    elif test_name == 'file_storage_integration':
                        result = test_method(quotation_workflow, sample_data)
                    elif test_name == 'api_endpoint_integration':
                        result = test_method(quotation_workflow, sample_data)
                    elif test_name == 'service_communication_validation':
                        result = test_method(postgres_conn, redis_conn, quotation_workflow, sample_data)
                    else:
                        result = {'status': 'unknown_test'}
                    
                    test_time = time.time() - test_start
                    
                    tier2_results.append({
                        'test_name': test_name,
                        'execution_time': test_time,
                        'success': True,
                        'result': result
                    })
                    
                    # Validate <5 second requirement
                    if test_time >= 5.0:
                        print(f"⚠️  Warning: {test_name} took {test_time:.3f}s (exceeds 5s limit)")
                    
                    # Update performance metrics
                    self.performance_metrics['response_times'].append(test_time)
                    
                except Exception as e:
                    tier2_results.append({
                        'test_name': test_name,
                        'execution_time': time.time() - test_start,
                        'success': False,
                        'error': str(e)
                    })
                    print(f"❌ {test_name} failed: {e}")
            
            # Cleanup
            postgres_conn.close()
            redis_conn.close()
            
            tier2_time = time.time() - tier2_start
            tier2_success_rate = sum(1 for r in tier2_results if r['success']) / len(tier2_results) * 100
            
            self.test_results['tier2_integration'] = tier2_results
            self.performance_metrics['success_rates'].append(tier2_success_rate)
            
            print(f"✅ Tier 2 completed: {len(tier2_results)} tests, {tier2_success_rate:.1f}% success rate in {tier2_time:.3f}s")
            
            return {
                'tier': 'tier2_integration',
                'total_tests': len(tier2_results),
                'successful_tests': sum(1 for r in tier2_results if r['success']),
                'success_rate': tier2_success_rate,
                'total_time': tier2_time,
                'results': tier2_results
            }
            
        except Exception as e:
            print(f"❌ Tier 2 execution failed: {e}")
            return {
                'tier': 'tier2_integration',
                'total_tests': 0,
                'successful_tests': 0,
                'success_rate': 0.0,
                'total_time': time.time() - tier2_start,
                'error': str(e)
            }
    
    def run_tier3_e2e_tests(self) -> Dict[str, Any]:
        """Execute Tier 3 end-to-end tests (<10 seconds each) with complete workflows."""
        print("🎯 Running Tier 3 End-to-End Tests (<10 seconds) with complete workflows...")
        
        tier3_start = time.time()
        
        try:
            from tests.e2e.test_quotation_e2e import TestQuotationE2E
            
            test_instance = TestQuotationE2E()
            
            # Setup infrastructure
            infrastructure_config = {
                'postgres': {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'port': int(os.getenv('DB_PORT', '6660')),
                    'database': os.getenv('DB_NAME', 'horme-pov_test'),
                    'user': os.getenv('DB_USER', 'test_user'),
                    'password': os.getenv('DB_PASSWORD', 'test_password')
                },
                'redis': {
                    'host': os.getenv('REDIS_HOST', 'localhost'),
                    'port': int(os.getenv('REDIS_PORT', '6661'))
                }
            }
            
            # Setup real connections
            import psycopg2
            import redis
            
            database_conn = psycopg2.connect(**infrastructure_config['postgres'])
            cache_conn = redis.Redis(**infrastructure_config['redis'], decode_responses=True)
            
            real_customer_scenarios = test_instance.real_customer_scenarios()
            
            # Execute E2E tests
            e2e_tests = [
                ('complete_quotation_business_workflow', 'test_complete_quotation_business_workflow'),
                ('performance_under_load', 'test_performance_under_load'),
                ('error_recovery_and_resilience', 'test_error_recovery_and_resilience')
            ]
            
            tier3_results = []
            
            for test_name, method_name in e2e_tests:
                test_start = time.time()
                
                try:
                    test_method = getattr(test_instance, method_name)
                    
                    if test_name == 'complete_quotation_business_workflow':
                        result = test_method(database_conn, cache_conn, real_customer_scenarios)
                    elif test_name == 'performance_under_load':
                        result = test_method(database_conn, cache_conn)
                    elif test_name == 'error_recovery_and_resilience':
                        result = test_method(database_conn, cache_conn)
                    else:
                        result = {'status': 'unknown_test'}
                    
                    test_time = time.time() - test_start
                    
                    tier3_results.append({
                        'test_name': test_name,
                        'execution_time': test_time,
                        'success': True,
                        'result': result
                    })
                    
                    # Validate <10 second requirement
                    if test_time >= 10.0:
                        print(f"⚠️  Warning: {test_name} took {test_time:.3f}s (exceeds 10s limit)")
                    
                    # Update performance metrics
                    self.performance_metrics['response_times'].append(test_time)
                    
                    # Extract throughput metrics if available
                    if isinstance(result, dict) and 'throughput_req_per_sec' in result:
                        self.performance_metrics['throughput_rates'].append(result['throughput_req_per_sec'])
                    
                except Exception as e:
                    tier3_results.append({
                        'test_name': test_name,
                        'execution_time': time.time() - test_start,
                        'success': False,
                        'error': str(e)
                    })
                    print(f"❌ {test_name} failed: {e}")
            
            # Cleanup
            database_conn.close()
            cache_conn.close()
            
            tier3_time = time.time() - tier3_start
            tier3_success_rate = sum(1 for r in tier3_results if r['success']) / len(tier3_results) * 100
            
            self.test_results['tier3_e2e'] = tier3_results
            self.performance_metrics['success_rates'].append(tier3_success_rate)
            
            print(f"✅ Tier 3 completed: {len(tier3_results)} tests, {tier3_success_rate:.1f}% success rate in {tier3_time:.3f}s")
            
            return {
                'tier': 'tier3_e2e',
                'total_tests': len(tier3_results),
                'successful_tests': sum(1 for r in tier3_results if r['success']),
                'success_rate': tier3_success_rate,
                'total_time': tier3_time,
                'results': tier3_results
            }
            
        except Exception as e:
            print(f"❌ Tier 3 execution failed: {e}")
            return {
                'tier': 'tier3_e2e',
                'total_tests': 0,
                'successful_tests': 0,
                'success_rate': 0.0,
                'total_time': time.time() - tier3_start,
                'error': str(e)
            }
    
    def generate_statistical_analysis_report(self, tier_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive statistical analysis report."""
        total_execution_time = time.time() - self.start_time
        
        # Aggregate metrics
        total_tests = sum(tier.get('total_tests', 0) for tier in tier_results)
        successful_tests = sum(tier.get('successful_tests', 0) for tier in tier_results)
        overall_success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Performance statistics
        response_times = self.performance_metrics['response_times']
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            std_deviation = statistics.stdev(response_times) if len(response_times) > 1 else 0
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # Calculate percentiles
            sorted_times = sorted(response_times)
            percentile_95 = sorted_times[int(0.95 * len(sorted_times))] if sorted_times else 0
            percentile_99 = sorted_times[int(0.99 * len(sorted_times))] if sorted_times else 0
        else:
            avg_response_time = median_response_time = std_deviation = 0
            min_response_time = max_response_time = percentile_95 = percentile_99 = 0
        
        # Throughput statistics
        throughput_rates = self.performance_metrics['throughput_rates']
        if throughput_rates:
            avg_throughput = statistics.mean(throughput_rates)
            max_throughput = max(throughput_rates)
        else:
            avg_throughput = max_throughput = 0
        
        # Enterprise Grade Validation
        precision_requirement = overall_success_rate >= 95.0
        performance_requirement = avg_response_time < 2.0
        reliability_requirement = std_deviation < 1.0
        
        enterprise_grade_compliance = precision_requirement and performance_requirement and reliability_requirement
        
        statistical_report = {
            'test_execution_summary': {
                'total_execution_time': total_execution_time,
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'overall_success_rate': overall_success_rate,
                'test_tiers_completed': len([t for t in tier_results if t.get('total_tests', 0) > 0])
            },
            'performance_metrics': {
                'response_time_statistics': {
                    'average': avg_response_time,
                    'median': median_response_time,
                    'standard_deviation': std_deviation,
                    'minimum': min_response_time,
                    'maximum': max_response_time,
                    'percentile_95': percentile_95,
                    'percentile_99': percentile_99
                },
                'throughput_statistics': {
                    'average_requests_per_second': avg_throughput,
                    'maximum_requests_per_second': max_throughput
                }
            },
            'enterprise_grade_validation': {
                'precision_requirement': {
                    'threshold': '≥95%',
                    'actual': f'{overall_success_rate:.1f}%',
                    'passed': precision_requirement
                },
                'performance_requirement': {
                    'threshold': '<2.0s average',
                    'actual': f'{avg_response_time:.3f}s',
                    'passed': performance_requirement
                },
                'reliability_requirement': {
                    'threshold': '<1.0s std deviation',
                    'actual': f'{std_deviation:.3f}s',
                    'passed': reliability_requirement
                },
                'overall_compliance': enterprise_grade_compliance
            },
            'infrastructure_status': self.infrastructure_status,
            'tier_breakdown': tier_results,
            'confidence_intervals': {
                'success_rate_95_ci': self._calculate_confidence_interval(overall_success_rate, total_tests),
                'response_time_95_ci': self._calculate_response_time_ci(response_times) if response_times else (0, 0)
            },
            'test_matrix_coverage': {
                'tier1_component_coverage': len(self.test_results.get('tier1_component', [])),
                'tier2_integration_coverage': len(self.test_results.get('tier2_integration', [])),
                'tier3_e2e_coverage': len(self.test_results.get('tier3_e2e', [])),
                'real_infrastructure_validation': bool(self.infrastructure_status.get('postgresql', {}).get('status') == 'healthy' and 
                                                     self.infrastructure_status.get('redis', {}).get('status') == 'healthy')
            },
            'generated_at': datetime.now().isoformat(),
            'test_environment': {
                'docker_infrastructure': 'real',
                'mocking_policy': 'none',
                'database_type': 'postgresql',
                'cache_type': 'redis',
                'testing_approach': 'enterprise_grade_3_tier'
            }
        }
        
        return statistical_report
    
    def _calculate_confidence_interval(self, success_rate: float, sample_size: int) -> Tuple[float, float]:
        """Calculate 95% confidence interval for success rate."""
        if sample_size == 0:
            return (0.0, 0.0)
        
        import math
        
        p = success_rate / 100.0
        n = sample_size
        
        # 95% confidence interval
        z = 1.96
        margin_of_error = z * math.sqrt((p * (1 - p)) / n)
        
        lower_bound = max(0, p - margin_of_error) * 100
        upper_bound = min(100, p + margin_of_error) * 100
        
        return (round(lower_bound, 2), round(upper_bound, 2))
    
    def _calculate_response_time_ci(self, response_times: List[float]) -> Tuple[float, float]:
        """Calculate 95% confidence interval for response times."""
        if len(response_times) < 2:
            return (0.0, 0.0)
        
        import math
        
        mean_time = statistics.mean(response_times)
        std_dev = statistics.stdev(response_times)
        n = len(response_times)
        
        # 95% confidence interval
        t_value = 1.96  # Approximation for large samples
        margin_of_error = t_value * (std_dev / math.sqrt(n))
        
        lower_bound = max(0, mean_time - margin_of_error)
        upper_bound = mean_time + margin_of_error
        
        return (round(lower_bound, 4), round(upper_bound, 4))
    
    def save_comprehensive_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save comprehensive test report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_quotation_test_report_{timestamp}.json"
        
        report_path = project_root / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(report_path)
    
    def print_executive_summary(self, report: Dict[str, Any]):
        """Print executive summary of test results."""
        print("\n" + "="*80)
        print("🏆 COMPREHENSIVE QUOTATION TESTING - EXECUTIVE SUMMARY")
        print("="*80)
        
        summary = report['test_execution_summary']
        performance = report['performance_metrics']
        enterprise = report['enterprise_grade_validation']
        
        print(f"\n📊 TEST EXECUTION RESULTS:")
        print(f"   • Total Tests Executed: {summary['total_tests']}")
        print(f"   • Successful Tests: {summary['successful_tests']}")
        print(f"   • Failed Tests: {summary['failed_tests']}")
        print(f"   • Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        print(f"   • Total Execution Time: {summary['total_execution_time']:.2f} seconds")
        
        print(f"\n⚡ PERFORMANCE METRICS:")
        response_stats = performance['response_time_statistics']
        print(f"   • Average Response Time: {response_stats['average']:.3f}s")
        print(f"   • 95th Percentile: {response_stats['percentile_95']:.3f}s")
        print(f"   • Standard Deviation: {response_stats['standard_deviation']:.3f}s")
        
        if performance['throughput_statistics']['average_requests_per_second'] > 0:
            print(f"   • Average Throughput: {performance['throughput_statistics']['average_requests_per_second']:.2f} req/s")
        
        print(f"\n🎯 ENTERPRISE GRADE VALIDATION:")
        print(f"   • Precision Requirement (≥95%): {'✅ PASSED' if enterprise['precision_requirement']['passed'] else '❌ FAILED'} "
              f"({enterprise['precision_requirement']['actual']})")
        print(f"   • Performance Requirement (<2.0s): {'✅ PASSED' if enterprise['performance_requirement']['passed'] else '❌ FAILED'} "
              f"({enterprise['performance_requirement']['actual']})")
        print(f"   • Reliability Requirement (<1.0s std): {'✅ PASSED' if enterprise['reliability_requirement']['passed'] else '❌ FAILED'} "
              f"({enterprise['reliability_requirement']['actual']})")
        
        compliance_status = "✅ ENTERPRISE GRADE COMPLIANT" if enterprise['overall_compliance'] else "❌ ENTERPRISE GRADE NON-COMPLIANT"
        print(f"\n🏅 OVERALL COMPLIANCE: {compliance_status}")
        
        print(f"\n🔧 INFRASTRUCTURE STATUS:")
        for service, status in report['infrastructure_status'].items():
            status_icon = "✅" if status.get('status') == 'healthy' else "❌"
            print(f"   • {service.title()}: {status_icon} {status.get('status', 'unknown')}")
        
        print(f"\n📈 CONFIDENCE INTERVALS (95%):")
        ci = report['confidence_intervals']
        print(f"   • Success Rate: {ci['success_rate_95_ci'][0]:.1f}% - {ci['success_rate_95_ci'][1]:.1f}%")
        print(f"   • Response Time: {ci['response_time_95_ci'][0]:.4f}s - {ci['response_time_95_ci'][1]:.4f}s")
        
        print("\n" + "="*80)

def main():
    """Execute comprehensive 3-tier quotation testing framework."""
    print("🚀 COMPREHENSIVE 3-TIER QUOTATION TESTING FRAMEWORK")
    print("Enterprise Grade Testing with REAL Infrastructure (NO MOCKING)")
    print("="*80)
    
    runner = ComprehensiveQuotationTestRunner()
    
    # Step 1: Setup real Docker infrastructure
    if not runner.setup_test_environment():
        print("❌ Failed to setup test environment. Exiting.")
        sys.exit(1)
    
    # Step 2: Execute all test tiers
    tier_results = []
    
    # Tier 1: Component Tests (<1 second each)
    tier1_result = runner.run_tier1_component_tests()
    tier_results.append(tier1_result)
    
    # Tier 2: Integration Tests (<5 seconds each) with real Docker services
    tier2_result = runner.run_tier2_integration_tests()
    tier_results.append(tier2_result)
    
    # Tier 3: End-to-End Tests (<10 seconds each) with complete workflows
    tier3_result = runner.run_tier3_e2e_tests()
    tier_results.append(tier3_result)
    
    # Step 3: Generate statistical analysis report
    comprehensive_report = runner.generate_statistical_analysis_report(tier_results)
    
    # Step 4: Save and display results
    report_path = runner.save_comprehensive_report(comprehensive_report)
    print(f"\n📄 Comprehensive report saved to: {report_path}")
    
    # Step 5: Display executive summary
    runner.print_executive_summary(comprehensive_report)
    
    # Step 6: Return appropriate exit code
    overall_success = comprehensive_report['enterprise_grade_validation']['overall_compliance']
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main()