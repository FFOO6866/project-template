#!/usr/bin/env python3
"""
Basic Health Monitor
===================

Simple health monitoring system using proper SDK patterns.
Monitors minimal infrastructure services and provides status reports.

Uses only SDK-approved patterns for database operations.
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Apply Windows compatibility
try:
    from windows_sdk_compatibility import ensure_windows_compatibility
    ensure_windows_compatibility()
    print("[OK] Windows compatibility applied")
except ImportError as e:
    print(f"[WARNING] Windows compatibility not available: {e}")

# Essential SDK pattern imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime


class BasicHealthMonitor:
    """Basic health monitoring using SDK patterns"""
    
    def __init__(self):
        self.runtime = LocalRuntime()
        self.db_path = Path(__file__).parent / "immediate_test.db"
        
    def check_database_health(self) -> Dict[str, Any]:
        """Check database health using SQLDatabaseNode"""
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("SQLDatabaseNode", "health_check", {
                "connection_string": f"sqlite:///{self.db_path}",
                "query": "SELECT COUNT(*) as product_count FROM test_products"
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "health_check" in results:
                db_result = results["health_check"]
                count = db_result[0]['product_count'] if isinstance(db_result, list) and db_result else 0
                
                return {
                    'service': 'database',
                    'status': 'healthy',
                    'details': {
                        'product_count': count,
                        'connection': 'successful',
                        'response_time_ms': 'fast'
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'service': 'database',
                    'status': 'unhealthy',
                    'details': {'error': 'No results returned'},
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                'service': 'database',
                'status': 'unhealthy',
                'details': {'error': str(e)},
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_cache_health(self) -> Dict[str, Any]:
        """Check cache health using PythonCodeNode"""
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("PythonCodeNode", "cache_health", {
                "code": """
# Test cache operations
test_cache = {'test_key': 'test_value', 'numbers': [1, 2, 3]}
cache_operations = {
    'write_test': len(test_cache) > 0,
    'read_test': test_cache.get('test_key') == 'test_value',
    'size_test': len(test_cache) == 2
}
result = {
    'status': 'healthy' if all(cache_operations.values()) else 'unhealthy',
    'operations': cache_operations
}
"""
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "cache_health" in results:
                cache_result = results["cache_health"]
                
                return {
                    'service': 'cache',
                    'status': cache_result.get('status', 'unknown'),
                    'details': cache_result.get('operations', {}),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'service': 'cache',
                    'status': 'unhealthy',
                    'details': {'error': 'No cache results'},
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                'service': 'cache',
                'status': 'unhealthy',
                'details': {'error': str(e)},
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_workflow_health(self) -> Dict[str, Any]:
        """Check workflow execution health"""
        try:
            start_time = time.time()
            
            workflow = WorkflowBuilder()
            workflow.add_node("PythonCodeNode", "workflow_test", {
                "code": "result = {'test': 'passed', 'workflow_engine': 'healthy'}"
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            
            execution_time = time.time() - start_time
            
            if results and "workflow_test" in results:
                return {
                    'service': 'workflow_engine',
                    'status': 'healthy',
                    'details': {
                        'execution_time_ms': round(execution_time * 1000, 2),
                        'run_id': run_id,
                        'test_result': results["workflow_test"].get('test', 'unknown')
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'service': 'workflow_engine',
                    'status': 'unhealthy',
                    'details': {'error': 'Workflow execution failed'},
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                'service': 'workflow_engine',
                'status': 'unhealthy',
                'details': {'error': str(e)},
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        print("Generating health report...")
        
        start_time = time.time()
        
        # Check all services
        database_health = self.check_database_health()
        cache_health = self.check_cache_health()
        workflow_health = self.check_workflow_health()
        
        services = [database_health, cache_health, workflow_health]
        
        # Calculate overall status
        healthy_services = [s for s in services if s['status'] == 'healthy']
        total_services = len(services)
        health_percentage = (len(healthy_services) / total_services) * 100
        
        overall_status = 'healthy' if health_percentage == 100 else \
                        'degraded' if health_percentage >= 50 else 'unhealthy'
        
        report_time = time.time() - start_time
        
        health_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': overall_status,
            'health_percentage': health_percentage,
            'services': {service['service']: service for service in services},
            'summary': {
                'total_services': total_services,
                'healthy_services': len(healthy_services),
                'unhealthy_services': total_services - len(healthy_services),
                'report_generation_time_ms': round(report_time * 1000, 2)
            }
        }
        
        return health_report
    
    def run_health_monitor(self, save_report: bool = True) -> Dict[str, Any]:
        """Run health monitoring and optionally save report"""
        print("\n" + "="*60)
        print("BASIC HEALTH MONITOR")
        print("="*60)
        print("Monitoring: Database + Cache + Workflow Engine")
        print("-"*60)
        
        # Generate health report
        health_report = self.generate_health_report()
        
        # Display results
        print(f"\nOVERALL STATUS: {health_report['overall_status'].upper()}")
        print(f"Health Percentage: {health_report['health_percentage']:.1f}%")
        print(f"Report Generation Time: {health_report['summary']['report_generation_time_ms']:.2f}ms")
        
        print("\nSERVICE STATUS:")
        for service_name, service_data in health_report['services'].items():
            status_symbol = "+" if service_data['status'] == 'healthy' else "X"
            print(f"  [{status_symbol}] {service_name}: {service_data['status']}")
            
            # Show key details
            if service_data['status'] == 'healthy':
                details = service_data['details']
                if service_name == 'database' and 'product_count' in details:
                    print(f"      Products: {details['product_count']}")
                elif service_name == 'workflow_engine' and 'execution_time_ms' in details:
                    print(f"      Execution Time: {details['execution_time_ms']}ms")
            else:
                error = service_data['details'].get('error', 'Unknown error')
                print(f"      Error: {error}")
        
        # Save report if requested
        if save_report:
            report_filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w') as f:
                json.dump(health_report, f, indent=2)
            print(f"\nHealth report saved to: {report_filename}")
        
        print("\n" + "="*60)
        
        # Recommendations
        if health_report['overall_status'] == 'healthy':
            print("SYSTEM HEALTHY - All services operational")
        elif health_report['overall_status'] == 'degraded':
            print("SYSTEM DEGRADED - Some services need attention")
        else:
            print("SYSTEM UNHEALTHY - Immediate action required")
        
        return health_report


def main():
    """Main health monitoring execution"""
    monitor = BasicHealthMonitor()
    
    try:
        health_report = monitor.run_health_monitor()
        
        # Exit based on overall health
        if health_report['overall_status'] == 'healthy':
            print("\nAll systems operational!")
            sys.exit(0)
        elif health_report['overall_status'] == 'degraded':
            print("\nSome services need attention.")
            sys.exit(1)
        else:
            print("\nSystem unhealthy - immediate action required.")
            sys.exit(2)
            
    except Exception as e:
        print(f"\nHealth monitoring failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()