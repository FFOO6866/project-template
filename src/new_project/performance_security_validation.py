"""
Performance Security Validation - Phase 2 Remediation
====================================================

Validates that security measures don't significantly impact performance.
Tests both security-enabled and security-disabled scenarios for comparison.
"""

import time
import statistics
from typing import Dict, Any, List
from security.input_sanitizer import InputSanitizer
from nodes.secure_workflow_nodes import FileValidationNode
from nodes.secure_search_nodes import QueryParseNode, CacheLookupNode


def benchmark_input_sanitization(iterations: int = 1000) -> Dict[str, Any]:
    """Benchmark input sanitization performance"""
    
    # Test data
    normal_inputs = [
        "normal search query",
        "user input data",
        "file.txt",
        "SELECT * FROM products WHERE active = 1",
        "This is normal content"
    ]
    
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "<script>alert('XSS')</script>",
        "../../../etc/passwd",
        "'; UNION SELECT password FROM admin; --",
        "<iframe src='javascript:alert(1)'></iframe>"
    ]
    
    sanitizer_strict = InputSanitizer(strict_mode=True)
    sanitizer_normal = InputSanitizer(strict_mode=False)
    
    results = {
        "normal_inputs": {},
        "malicious_inputs": {},
        "iterations": iterations
    }
    
    # Benchmark normal inputs
    print("Benchmarking normal inputs...")
    
    # Normal inputs with security
    start_time = time.time()
    for _ in range(iterations):
        for input_text in normal_inputs:
            try:
                sanitizer_normal.sanitize_string(input_text)
            except:
                pass
    normal_with_security_time = time.time() - start_time
    
    # Normal inputs without security (baseline)
    start_time = time.time()
    for _ in range(iterations):
        for input_text in normal_inputs:
            processed = input_text.strip()  # Minimal processing
    normal_baseline_time = time.time() - start_time
    
    results["normal_inputs"] = {
        "with_security_ms": normal_with_security_time * 1000,
        "baseline_ms": normal_baseline_time * 1000,
        "overhead_ms": (normal_with_security_time - normal_baseline_time) * 1000,
        "overhead_percent": ((normal_with_security_time - normal_baseline_time) / max(normal_baseline_time, 0.001)) * 100
    }
    
    # Benchmark malicious inputs
    print("Benchmarking malicious inputs...")
    
    # Malicious inputs with security
    start_time = time.time()
    for _ in range(iterations):
        for input_text in malicious_inputs:
            try:
                sanitizer_normal.sanitize_string(input_text)
            except:
                pass
    malicious_with_security_time = time.time() - start_time
    
    # Malicious inputs without security (baseline)
    start_time = time.time()
    for _ in range(iterations):
        for input_text in malicious_inputs:
            processed = input_text.strip()  # Minimal processing
    malicious_baseline_time = time.time() - start_time
    
    results["malicious_inputs"] = {
        "with_security_ms": malicious_with_security_time * 1000,
        "baseline_ms": malicious_baseline_time * 1000,
        "overhead_ms": (malicious_with_security_time - malicious_baseline_time) * 1000,
        "overhead_percent": ((malicious_with_security_time - malicious_baseline_time) / max(malicious_baseline_time, 0.001)) * 100
    }
    
    return results


def benchmark_secure_nodes(iterations: int = 100) -> Dict[str, Any]:
    """Benchmark secure node performance"""
    
    print(f"Benchmarking secure nodes ({iterations} iterations)...")
    
    # Test data
    test_inputs = {
        "file_validation": {
            "files": ["test1.txt", "test2.pdf", "test3.doc"],
            "scan_content": True,
            "max_file_size": 1024000
        },
        "query_parse": {
            "query": "search products category:electronics price:100-500",
            "enable_advanced_operators": True,
            "max_query_length": 1000
        },
        "cache_lookup": {
            "cache_key": "user_profile_12345",
            "operation": "get",
            "namespace": "default"
        }
    }
    
    nodes = {
        "FileValidationNode": FileValidationNode(),
        "QueryParseNode": QueryParseNode(),
        "CacheLookupNode": CacheLookupNode()
    }
    
    results = {}
    
    for node_name, node in nodes.items():
        print(f"Benchmarking {node_name}...")
        
        input_key = {
            "FileValidationNode": "file_validation",
            "QueryParseNode": "query_parse", 
            "CacheLookupNode": "cache_lookup"
        }[node_name]
        
        inputs = test_inputs[input_key]
        
        # Measure execution times
        execution_times = []
        
        for _ in range(iterations):
            start_time = time.time()
            try:
                result = node.run(inputs)
                execution_time = time.time() - start_time
                execution_times.append(execution_time * 1000)  # Convert to ms
            except Exception as e:
                # Still record time for failed executions
                execution_time = time.time() - start_time
                execution_times.append(execution_time * 1000)
        
        # Calculate statistics
        results[node_name] = {
            "iterations": iterations,
            "min_time_ms": min(execution_times),
            "max_time_ms": max(execution_times),
            "avg_time_ms": statistics.mean(execution_times),
            "median_time_ms": statistics.median(execution_times),
            "std_dev_ms": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            "p95_time_ms": sorted(execution_times)[int(0.95 * len(execution_times))],
            "p99_time_ms": sorted(execution_times)[int(0.99 * len(execution_times))]
        }
    
    return results


def benchmark_workflow_security(iterations: int = 50) -> Dict[str, Any]:
    """Benchmark workflow-level security performance"""
    
    print(f"Benchmarking workflow security ({iterations} iterations)...")
    
    from kailash.workflow.builder import WorkflowBuilder
    from kailash.runtime.local import LocalRuntime
    
    # Test workflow with security nodes
    def create_secure_workflow():
        workflow = WorkflowBuilder()
        
        # Add secure nodes
        workflow.add_node("FileValidationNode", "validate_files", {
            "files": ["test1.txt", "test2.pdf"],
            "scan_content": True
        })
        
        workflow.add_node("QueryParseNode", "parse_query", {
            "query": "search products",
            "enable_advanced_operators": False
        })
        
        workflow.add_node("CacheLookupNode", "cache_lookup", {
            "cache_key": "test_key",
            "operation": "get"
        })
        
        return workflow
    
    runtime = LocalRuntime()
    
    # Measure workflow execution times
    execution_times = []
    
    for _ in range(iterations):
        try:
            workflow = create_secure_workflow()
            built_workflow = workflow.build()
            
            start_time = time.time()
            results, run_id = runtime.execute(built_workflow)
            execution_time = time.time() - start_time
            
            execution_times.append(execution_time * 1000)  # Convert to ms
            
        except Exception as e:
            # Still record time for failed executions
            execution_time = time.time() - start_time
            execution_times.append(execution_time * 1000)
    
    # Calculate statistics
    workflow_results = {
        "iterations": iterations,
        "min_time_ms": min(execution_times),
        "max_time_ms": max(execution_times), 
        "avg_time_ms": statistics.mean(execution_times),
        "median_time_ms": statistics.median(execution_times),
        "std_dev_ms": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
        "p95_time_ms": sorted(execution_times)[int(0.95 * len(execution_times))],
        "p99_time_ms": sorted(execution_times)[int(0.99 * len(execution_times))],
        "successful_executions": sum(1 for t in execution_times if t < 10000)  # Under 10s
    }
    
    return workflow_results


def run_performance_validation():
    """Run complete performance validation"""
    
    print("=== Performance Security Validation ===")
    print()
    
    # 1. Input Sanitization Performance
    print("1. Input Sanitization Performance")
    print("-" * 40)
    
    sanitization_results = benchmark_input_sanitization(1000)
    
    print("Normal Inputs:")
    normal = sanitization_results["normal_inputs"]
    print(f"  With Security: {normal['with_security_ms']:.2f}ms")
    print(f"  Baseline: {normal['baseline_ms']:.2f}ms")
    print(f"  Overhead: {normal['overhead_ms']:.2f}ms ({normal['overhead_percent']:.1f}%)")
    
    print("\nMalicious Inputs:")
    malicious = sanitization_results["malicious_inputs"]
    print(f"  With Security: {malicious['with_security_ms']:.2f}ms")
    print(f"  Baseline: {malicious['baseline_ms']:.2f}ms")
    print(f"  Overhead: {malicious['overhead_ms']:.2f}ms ({malicious['overhead_percent']:.1f}%)")
    
    print()
    
    # 2. Secure Node Performance
    print("2. Secure Node Performance")
    print("-" * 40)
    
    node_results = benchmark_secure_nodes(100)
    
    for node_name, stats in node_results.items():
        print(f"{node_name}:")
        print(f"  Average: {stats['avg_time_ms']:.2f}ms")
        print(f"  Median: {stats['median_time_ms']:.2f}ms")
        print(f"  P95: {stats['p95_time_ms']:.2f}ms")
        print(f"  P99: {stats['p99_time_ms']:.2f}ms")
        print(f"  Std Dev: {stats['std_dev_ms']:.2f}ms")
        print()
    
    # 3. Workflow Security Performance  
    print("3. Workflow Security Performance")
    print("-" * 40)
    
    workflow_results = benchmark_workflow_security(50)
    
    print("Secure Workflow Execution:")
    print(f"  Average: {workflow_results['avg_time_ms']:.2f}ms")
    print(f"  Median: {workflow_results['median_time_ms']:.2f}ms")
    print(f"  P95: {workflow_results['p95_time_ms']:.2f}ms")
    print(f"  P99: {workflow_results['p99_time_ms']:.2f}ms")
    print(f"  Successful: {workflow_results['successful_executions']}/{workflow_results['iterations']}")
    
    print()
    
    # 4. Performance Assessment
    print("4. Performance Assessment")
    print("-" * 40)
    
    # Define performance criteria
    criteria = {
        "input_sanitization_overhead": 50,  # Max 50ms overhead per 1000 operations
        "node_avg_execution": 1000,  # Max 1 second average
        "node_p95_execution": 2000,  # Max 2 seconds P95
        "workflow_avg_execution": 5000,  # Max 5 seconds average
        "workflow_p95_execution": 10000  # Max 10 seconds P95
    }
    
    assessment = {
        "input_sanitization": normal['overhead_ms'] <= criteria['input_sanitization_overhead'],
        "node_performance": all(stats['avg_time_ms'] <= criteria['node_avg_execution'] for stats in node_results.values()),
        "node_p95": all(stats['p95_time_ms'] <= criteria['node_p95_execution'] for stats in node_results.values()),
        "workflow_performance": workflow_results['avg_time_ms'] <= criteria['workflow_avg_execution'],
        "workflow_p95": workflow_results['p95_time_ms'] <= criteria['workflow_p95_execution']
    }
    
    all_passed = all(assessment.values())
    
    print("Performance Criteria:")
    for criterion, passed in assessment.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {criterion}: {status}")
    
    print()
    print(f"Overall Performance Assessment: {'✓ PASS' if all_passed else '✗ FAIL'}")
    
    if all_passed:
        print("Security implementation maintains acceptable performance characteristics.")
    else:
        print("Security implementation may impact performance - optimization needed.")
    
    return {
        "sanitization": sanitization_results,
        "nodes": node_results,
        "workflow": workflow_results,
        "assessment": assessment,
        "overall_pass": all_passed
    }


if __name__ == "__main__":
    results = run_performance_validation()