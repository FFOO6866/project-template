#!/usr/bin/env python3
"""
Truth Baseline Validator

Independent validation framework that addresses the systematic validation methodology failure
identified by ultrathink-analyst. This validator provides objective measurement of actual
vs claimed capabilities with zero tolerance for validation gaps.

Key Principles:
1. No advancement without objective verification
2. No partial credit for incomplete implementations  
3. No claims without executable proof
4. No mocking in production readiness validation
5. Independent verification required for all critical requirements

Usage:
    python truth_baseline_validator.py --validate-all
    python truth_baseline_validator.py --validate-infrastructure
    python truth_baseline_validator.py --validate-services
    python truth_baseline_validator.py --generate-report
"""

import json
import subprocess
import sys
import time
import platform
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Standard validation result structure."""
    requirement_id: str
    description: str
    claimed_status: str
    actual_status: str
    verified: bool
    measurement_method: str
    validation_timestamp: datetime
    evidence: Dict[str, Any]
    error_message: Optional[str] = None


class TruthBaselineValidator:
    """
    Independent validation framework for production readiness.
    
    Addresses ultrathink-analyst findings:
    - Root cause: Measurement misalignment using mock/simulation vs actual production functionality
    - Truth baseline: 0-15% actual production readiness due to Windows SDK import failures
    - Claims vs reality gap: 75% claimed vs 0% actual infrastructure deployment
    """
    
    def __init__(self):
        self.validation_results: List[ValidationResult] = []
        self.start_time = datetime.now()
        
        # Service validation configurations
        self.service_configs = {
            "postgresql": {
                "port": 5432,
                "health_check": "pg_isready -h localhost -p 5432",
                "connection_test": self._test_postgresql_connection
            },
            "neo4j": {
                "port": 7474,
                "health_check": "curl -f http://localhost:7474",
                "connection_test": self._test_neo4j_connection
            },
            "chromadb": {
                "port": 8000,
                "health_check": "curl -f http://localhost:8000/api/v1/heartbeat",
                "connection_test": self._test_chromadb_connection
            },
            "redis": {
                "port": 6379,
                "health_check": "redis-cli ping",
                "connection_test": self._test_redis_connection
            }
        }
        
        # Claims extracted from documentation (ADR-006)
        self.documented_claims = {
            "production_readiness": "75%",
            "infrastructure_operational": "100%",
            "services_deployed": "All services operational",
            "test_success_rate": "95%+",
            "timeline_to_production": "14 days"
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Execute complete validation suite.
        
        Returns comprehensive validation report with actual vs claimed measurements.
        """
        logger.info("Starting complete validation suite")
        
        # Execute all validation categories
        self.validate_infrastructure_deployment()
        self.validate_service_integration()
        self.validate_test_infrastructure()
        self.validate_windows_compatibility()
        self.validate_performance_baseline()
        
        return self.generate_truth_baseline_report()
    
    def validate_infrastructure_deployment(self) -> List[ValidationResult]:
        """
        REQ-INFRA-001, REQ-INFRA-002, REQ-INFRA-003: Infrastructure validation.
        
        Validates:
        1. Service accessibility from Windows host
        2. Data persistence across container restarts
        3. Cross-platform Windows integration
        """
        logger.info("Validating infrastructure deployment")
        
        # REQ-INFRA-001: Service Accessibility Validation
        accessibility_result = self._validate_service_accessibility()
        self.validation_results.append(accessibility_result)
        
        # REQ-INFRA-002: Data Persistence Validation
        persistence_result = self._validate_data_persistence()
        self.validation_results.append(persistence_result)
        
        # REQ-INFRA-003: Cross-Platform Windows Integration
        integration_result = self._validate_windows_integration()
        self.validation_results.append(integration_result)
        
        return self.validation_results[-3:]
    
    def validate_service_integration(self) -> List[ValidationResult]:
        """
        REQ-VALIDATE-001, REQ-VALIDATE-002: Real service integration validation.
        
        Validates:
        1. All services use real connections (NO MOCKING)
        2. Data consistency across services
        3. Service interoperability
        """
        logger.info("Validating service integration")
        
        # REQ-VALIDATE-001: Real Service Integration Testing
        real_service_result = self._validate_real_service_integration()
        self.validation_results.append(real_service_result)
        
        # REQ-VALIDATE-002: Data Consistency and Integrity
        consistency_result = self._validate_data_consistency()
        self.validation_results.append(consistency_result)
        
        return self.validation_results[-2:]
    
    def validate_test_infrastructure(self) -> ValidationResult:
        """
        Validate test infrastructure reality vs claims.
        
        Compares documented test success claims against actual test execution results.
        """
        logger.info("Validating test infrastructure")
        
        try:
            # Run pytest with collection only to count discoverable tests
            discover_result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=Path(__file__).parent
            )
            
            # Run actual tests to get execution results
            test_result = subprocess.run(
                [sys.executable, "-m", "pytest", "--tb=no", "-q", "-x"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=Path(__file__).parent
            )
            
            # Parse results
            discovered_tests = len([line for line in discover_result.stdout.split('\n') if 'test_' in line])
            
            # Extract test results from output
            test_output = test_result.stdout
            passed_tests = test_output.count(" PASSED")
            failed_tests = test_output.count(" FAILED")
            error_tests = test_output.count(" ERROR")
            
            total_executable = passed_tests + failed_tests + error_tests
            
            if total_executable > 0:
                actual_success_rate = (passed_tests / total_executable) * 100
            else:
                actual_success_rate = 0
            
            # Compare against claims
            claimed_success_rate = 95  # From documented claims
            verified = actual_success_rate >= claimed_success_rate
            
            evidence = {
                "discovered_tests": discovered_tests,
                "executable_tests": total_executable,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests,
                "actual_success_rate": f"{actual_success_rate:.1f}%",
                "claimed_success_rate": f"{claimed_success_rate}%",
                "discovery_output": discover_result.stdout[:1000],  # First 1KB
                "test_output": test_output[:1000]  # First 1KB
            }
            
            result = ValidationResult(
                requirement_id="REQ-TEST-001",
                description="Test Infrastructure Success Rate Validation",
                claimed_status=f"{claimed_success_rate}% test success rate",
                actual_status=f"{actual_success_rate:.1f}% test success rate",
                verified=verified,
                measurement_method="pytest_execution",
                validation_timestamp=datetime.now(),
                evidence=evidence
            )
            
        except Exception as e:
            result = ValidationResult(
                requirement_id="REQ-TEST-001",
                description="Test Infrastructure Success Rate Validation",
                claimed_status="95% test success rate",
                actual_status="Test execution failed",
                verified=False,
                measurement_method="pytest_execution",
                validation_timestamp=datetime.now(),
                evidence={},
                error_message=str(e)
            )
        
        self.validation_results.append(result)
        return result
    
    def validate_windows_compatibility(self) -> ValidationResult:
        """
        REQ-WIN-001, REQ-WIN-002: Windows compatibility validation.
        
        Validates SDK functionality and development environment consistency on Windows.
        """
        logger.info("Validating Windows compatibility")
        
        try:
            # Test basic SDK imports
            sdk_import_test = """
import sys
try:
    from kailash.workflow.builder import WorkflowBuilder
    from kailash.runtime.local import LocalRuntime
    print("SDK_IMPORT_SUCCESS")
except Exception as e:
    print(f"SDK_IMPORT_FAILED: {e}")
"""
            
            result = subprocess.run(
                [sys.executable, "-c", sdk_import_test],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            sdk_imports_working = "SDK_IMPORT_SUCCESS" in result.stdout
            
            # Test Windows-specific functionality
            windows_features = {
                "platform_detection": platform.system() == "Windows",
                "resource_module_available": self._test_resource_module(),
                "path_handling": self._test_path_handling(),
                "subprocess_execution": result.returncode == 0
            }
            
            # Calculate overall Windows compatibility
            working_features = sum(1 for working in windows_features.values() if working)
            total_features = len(windows_features)
            compatibility_percentage = (working_features / total_features) * 100
            
            verified = compatibility_percentage >= 95  # 95% compatibility required
            
            evidence = {
                "sdk_imports_working": sdk_imports_working,
                "windows_features": windows_features,
                "compatibility_percentage": f"{compatibility_percentage:.1f}%",
                "platform": platform.system(),
                "python_version": sys.version,
                "import_output": result.stdout,
                "import_errors": result.stderr
            }
            
            result = ValidationResult(
                requirement_id="REQ-WIN-001",
                description="Windows SDK Compatibility Validation",
                claimed_status="100% Windows compatibility",
                actual_status=f"{compatibility_percentage:.1f}% Windows compatibility",
                verified=verified,
                measurement_method="windows_feature_testing",
                validation_timestamp=datetime.now(),
                evidence=evidence
            )
            
        except Exception as e:
            result = ValidationResult(
                requirement_id="REQ-WIN-001",
                description="Windows SDK Compatibility Validation",
                claimed_status="100% Windows compatibility",
                actual_status="Windows compatibility test failed",
                verified=False,
                measurement_method="windows_feature_testing",
                validation_timestamp=datetime.now(),
                evidence={},
                error_message=str(e)
            )
        
        self.validation_results.append(result)
        return result
    
    def validate_performance_baseline(self) -> ValidationResult:
        """
        REQ-PERF-001: Performance measurement validation.
        
        Validates actual performance against claimed SLA targets.
        """
        logger.info("Validating performance baseline")
        
        try:
            # Measure system resource availability
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Test basic operation performance
            start_time = time.time()
            
            # Simulate basic operations
            for i in range(100):
                _ = {"test": f"data_{i}", "timestamp": time.time()}
            
            operation_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Performance thresholds (from requirements)
            performance_metrics = {
                "cpu_utilization": {"actual": cpu_percent, "threshold": 70, "unit": "%"},
                "memory_utilization": {"actual": memory.percent, "threshold": 80, "unit": "%"},
                "disk_utilization": {"actual": disk.percent, "threshold": 80, "unit": "%"},
                "basic_operation_time": {"actual": operation_time, "threshold": 100, "unit": "ms"}
            }
            
            # Calculate performance compliance
            compliant_metrics = 0
            for metric, values in performance_metrics.items():
                if metric == "basic_operation_time":
                    # Lower is better for time
                    if values["actual"] <= values["threshold"]:
                        compliant_metrics += 1
                else:
                    # Lower is better for utilization
                    if values["actual"] <= values["threshold"]:
                        compliant_metrics += 1
            
            performance_compliance = (compliant_metrics / len(performance_metrics)) * 100
            verified = performance_compliance >= 80  # 80% compliance required
            
            evidence = {
                "performance_metrics": performance_metrics,
                "performance_compliance": f"{performance_compliance:.1f}%",
                "system_info": {
                    "cpu_count": psutil.cpu_count(),
                    "total_memory_gb": round(memory.total / (1024**3), 2),
                    "available_memory_gb": round(memory.available / (1024**3), 2)
                }
            }
            
            result = ValidationResult(
                requirement_id="REQ-PERF-001",
                description="Performance Baseline Validation",
                claimed_status="All SLA targets met",
                actual_status=f"{performance_compliance:.1f}% SLA compliance",
                verified=verified,
                measurement_method="system_performance_measurement",
                validation_timestamp=datetime.now(),
                evidence=evidence
            )
            
        except Exception as e:
            result = ValidationResult(
                requirement_id="REQ-PERF-001",
                description="Performance Baseline Validation",
                claimed_status="All SLA targets met",
                actual_status="Performance measurement failed",
                verified=False,
                measurement_method="system_performance_measurement",
                validation_timestamp=datetime.now(),
                evidence={},
                error_message=str(e)
            )
        
        self.validation_results.append(result)
        return result
    
    def generate_truth_baseline_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive truth baseline report.
        
        Provides objective measurement of actual vs claimed capabilities.
        """
        logger.info("Generating truth baseline report")
        
        total_requirements = len(self.validation_results)
        verified_requirements = sum(1 for r in self.validation_results if r.verified)
        
        if total_requirements > 0:
            actual_production_readiness = (verified_requirements / total_requirements) * 100
        else:
            actual_production_readiness = 0
        
        # Extract claimed production readiness from documentation
        claimed_production_readiness = 75  # From ADR-006
        
        # Calculate claims vs reality gap
        claims_vs_reality_gap = abs(claimed_production_readiness - actual_production_readiness)
        
        # Categorize validation results
        categorized_results = {
            "infrastructure": [],
            "services": [],
            "testing": [],
            "performance": [],
            "compatibility": []
        }
        
        for result in self.validation_results:
            if "INFRA" in result.requirement_id:
                categorized_results["infrastructure"].append(asdict(result))
            elif "VALIDATE" in result.requirement_id:
                categorized_results["services"].append(asdict(result))
            elif "TEST" in result.requirement_id:
                categorized_results["testing"].append(asdict(result))
            elif "PERF" in result.requirement_id:
                categorized_results["performance"].append(asdict(result))
            elif "WIN" in result.requirement_id:
                categorized_results["compatibility"].append(asdict(result))
        
        # Generate final report
        report = {
            "validation_summary": {
                "timestamp": datetime.now().isoformat(),
                "validation_duration_minutes": (datetime.now() - self.start_time).total_seconds() / 60,
                "total_requirements_validated": total_requirements,
                "requirements_verified": verified_requirements,
                "requirements_failed": total_requirements - verified_requirements
            },
            "production_readiness_analysis": {
                "claimed_production_readiness": f"{claimed_production_readiness}%",
                "actual_production_readiness": f"{actual_production_readiness:.1f}%",
                "claims_vs_reality_gap": f"{claims_vs_reality_gap:.1f}%",
                "validation_methodology": "independent_objective_measurement",
                "measurement_standards": "no_mocking_real_services_only"
            },
            "validation_results_by_category": categorized_results,
            "critical_findings": self._generate_critical_findings(),
            "recommendations": self._generate_recommendations(),
            "next_steps": self._generate_next_steps()
        }
        
        return report
    
    # Private helper methods
    
    def _validate_service_accessibility(self) -> ValidationResult:
        """Validate all services are accessible from Windows host."""
        try:
            service_results = {}
            
            for service_name, config in self.service_configs.items():
                try:
                    # Test external health check
                    result = subprocess.run(
                        config["health_check"],
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    service_results[service_name] = {
                        "accessible": result.returncode == 0,
                        "response_time": "< 10s",
                        "health_check_output": result.stdout[:200],
                        "health_check_error": result.stderr[:200] if result.stderr else None
                    }
                    
                except subprocess.TimeoutExpired:
                    service_results[service_name] = {
                        "accessible": False,
                        "response_time": "> 10s (timeout)",
                        "error": "Health check timeout"
                    }
                except Exception as e:
                    service_results[service_name] = {
                        "accessible": False,
                        "error": str(e)
                    }
            
            # Calculate accessibility percentage
            accessible_services = sum(1 for r in service_results.values() if r.get("accessible", False))
            total_services = len(self.service_configs)
            accessibility_percentage = (accessible_services / total_services) * 100
            
            verified = accessibility_percentage == 100  # 100% required
            
            return ValidationResult(
                requirement_id="REQ-INFRA-001",
                description="Service Accessibility Validation",
                claimed_status="All services operational",
                actual_status=f"{accessible_services}/{total_services} services accessible ({accessibility_percentage:.1f}%)",
                verified=verified,
                measurement_method="external_health_checks",
                validation_timestamp=datetime.now(),
                evidence={"service_results": service_results}
            )
            
        except Exception as e:
            return ValidationResult(
                requirement_id="REQ-INFRA-001",
                description="Service Accessibility Validation",
                claimed_status="All services operational",
                actual_status="Service accessibility check failed",
                verified=False,
                measurement_method="external_health_checks",
                validation_timestamp=datetime.now(),
                evidence={},
                error_message=str(e)
            )
    
    def _validate_data_persistence(self) -> ValidationResult:
        """Validate data persists across container restarts."""
        # For now, return a placeholder result since this requires Docker operations
        return ValidationResult(
            requirement_id="REQ-INFRA-002",
            description="Data Persistence Validation",
            claimed_status="Data persists across restarts",
            actual_status="Docker services not operational - cannot test persistence",
            verified=False,
            measurement_method="restart_cycle_validation",
            validation_timestamp=datetime.now(),
            evidence={"note": "Requires operational Docker services for validation"}
        )
    
    def _validate_windows_integration(self) -> ValidationResult:
        """Validate Windows integration functionality."""
        try:
            integration_tests = {
                "platform_detection": platform.system() == "Windows",
                "python_executable": sys.executable is not None,
                "subprocess_support": True,  # We're running subprocesses successfully
                "file_system_access": Path(__file__).exists()
            }
            
            working_integrations = sum(1 for working in integration_tests.values() if working)
            total_integrations = len(integration_tests)
            integration_percentage = (working_integrations / total_integrations) * 100
            
            verified = integration_percentage == 100
            
            return ValidationResult(
                requirement_id="REQ-INFRA-003",
                description="Cross-Platform Windows Integration",
                claimed_status="100% Windows integration",
                actual_status=f"{integration_percentage:.1f}% Windows integration",
                verified=verified,
                measurement_method="windows_integration_testing",
                validation_timestamp=datetime.now(),
                evidence={"integration_tests": integration_tests}
            )
            
        except Exception as e:
            return ValidationResult(
                requirement_id="REQ-INFRA-003", 
                description="Cross-Platform Windows Integration",
                claimed_status="100% Windows integration",
                actual_status="Windows integration test failed",
                verified=False,
                measurement_method="windows_integration_testing",
                validation_timestamp=datetime.now(),
                evidence={},
                error_message=str(e)
            )
    
    def _validate_real_service_integration(self) -> ValidationResult:
        """Validate real service integration (NO MOCKING)."""
        try:
            # Check if mocking is being used in test files
            test_files = list(Path(__file__).parent.glob("tests/**/*.py"))
            mocking_violations = []
            
            for test_file in test_files:
                try:
                    content = test_file.read_text(encoding='utf-8')
                    if any(mock_pattern in content for mock_pattern in ["@mock.", "@patch", "Mock(", "MagicMock"]):
                        mocking_violations.append(str(test_file))
                except Exception:
                    continue  # Skip files that can't be read
            
            # Test actual service connections
            connection_tests = {}
            for service_name, config in self.service_configs.items():
                try:
                    connection_result = config["connection_test"]()
                    connection_tests[service_name] = {
                        "connection_successful": connection_result,
                        "connection_type": "real_service"
                    }
                except Exception as e:
                    connection_tests[service_name] = {
                        "connection_successful": False,
                        "connection_type": "real_service",
                        "error": str(e)
                    }
            
            # Calculate verification status
            has_mocking_violations = len(mocking_violations) > 0
            successful_connections = sum(1 for r in connection_tests.values() if r.get("connection_successful", False))
            total_services = len(connection_tests)
            
            verified = not has_mocking_violations and successful_connections == total_services
            
            return ValidationResult(
                requirement_id="REQ-VALIDATE-001",
                description="Real Service Integration Testing (NO MOCKING)",
                claimed_status="All tests use real services",
                actual_status=f"Mocking violations: {len(mocking_violations)}, Real connections: {successful_connections}/{total_services}",
                verified=verified,
                measurement_method="mocking_detection_and_connection_testing",
                validation_timestamp=datetime.now(),
                evidence={
                    "mocking_violations": mocking_violations,
                    "connection_tests": connection_tests,
                    "test_files_scanned": len(test_files)
                }
            )
            
        except Exception as e:
            return ValidationResult(
                requirement_id="REQ-VALIDATE-001",
                description="Real Service Integration Testing (NO MOCKING)",
                claimed_status="All tests use real services",
                actual_status="Real service integration validation failed",
                verified=False,
                measurement_method="mocking_detection_and_connection_testing",
                validation_timestamp=datetime.now(),
                evidence={},
                error_message=str(e)
            )
    
    def _validate_data_consistency(self) -> ValidationResult:
        """Validate data consistency across services."""
        # Placeholder for data consistency validation
        return ValidationResult(
            requirement_id="REQ-VALIDATE-002",
            description="Data Consistency and Integrity Validation",
            claimed_status="Data consistency maintained across services",
            actual_status="Services not operational - cannot test consistency",
            verified=False,
            measurement_method="cross_service_data_validation",
            validation_timestamp=datetime.now(),
            evidence={"note": "Requires operational services for cross-service consistency testing"}
        )
    
    def _test_postgresql_connection(self) -> bool:
        """Test PostgreSQL connection."""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="horme_test_db",
                user="test_user",
                password="test_password",
                connect_timeout=5
            )
            conn.close()
            return True
        except Exception:
            return False
    
    def _test_neo4j_connection(self) -> bool:
        """Test Neo4j connection."""
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(
                "bolt://localhost:7687",
                auth=("neo4j", "testpassword")
            )
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
            driver.close()
            return record["test"] == 1
        except Exception:
            return False
    
    def _test_chromadb_connection(self) -> bool:
        """Test ChromaDB connection."""
        try:
            import chromadb
            client = chromadb.HttpClient(host="localhost", port=8000)
            client.heartbeat()
            return True
        except Exception:
            return False
    
    def _test_redis_connection(self) -> bool:
        """Test Redis connection."""
        try:
            import redis
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            return r.ping()
        except Exception:
            return False
    
    def _test_resource_module(self) -> bool:
        """Test resource module availability."""
        try:
            import resource
            return hasattr(resource, 'getrlimit') and hasattr(resource, 'setrlimit')
        except ImportError:
            return False
    
    def _test_path_handling(self) -> bool:
        """Test cross-platform path handling."""
        try:
            test_path = Path(__file__).parent / "test_file.tmp"
            test_path.touch()
            exists = test_path.exists()
            test_path.unlink()
            return exists
        except Exception:
            return False
    
    def _generate_critical_findings(self) -> List[str]:
        """Generate list of critical findings."""
        findings = []
        
        failed_requirements = [r for r in self.validation_results if not r.verified]
        
        if failed_requirements:
            findings.append(f"{len(failed_requirements)} critical requirements failed validation")
        
        # Check for specific critical issues
        infra_failures = [r for r in failed_requirements if "INFRA" in r.requirement_id]
        if infra_failures:
            findings.append("Infrastructure deployment failures detected")
        
        service_failures = [r for r in failed_requirements if "VALIDATE" in r.requirement_id]
        if service_failures:
            findings.append("Service integration failures detected")
        
        if not any(r.verified for r in self.validation_results if "INFRA" in r.requirement_id):
            findings.append("CRITICAL: Zero infrastructure services operational")
        
        return findings
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        verified_count = sum(1 for r in self.validation_results if r.verified)
        total_count = len(self.validation_results)
        
        if verified_count == 0:
            recommendations.append("IMMEDIATE: Emergency infrastructure deployment required")
            recommendations.append("Follow WSL2 + Docker deployment procedure from ADR-007")
            recommendations.append("Implement truth baseline validation framework")
        elif verified_count < total_count * 0.5:
            recommendations.append("URGENT: Address failing validation requirements before proceeding")
            recommendations.append("Focus on infrastructure and service deployment")
        elif verified_count < total_count * 0.8:
            recommendations.append("Address remaining validation gaps before production deployment")
            recommendations.append("Implement performance and security hardening measures")
        else:
            recommendations.append("Continue with production readiness certification process")
            recommendations.append("Implement continuous validation monitoring")
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Generate specific next steps based on current state."""
        next_steps = []
        
        # Check infrastructure status
        infra_verified = any(r.verified for r in self.validation_results if "INFRA" in r.requirement_id)
        if not infra_verified:
            next_steps.extend([
                "1. Deploy WSL2 Ubuntu 22.04 environment",
                "2. Install and configure Docker Desktop with WSL2 backend",
                "3. Deploy service stack using docker-compose",
                "4. Validate service accessibility from Windows host"
            ])
        
        # Check service integration
        service_verified = any(r.verified for r in self.validation_results if "VALIDATE" in r.requirement_id)
        if not service_verified:
            next_steps.extend([
                "5. Remove all mocking from integration tests",
                "6. Implement real service connection patterns",
                "7. Validate data consistency across services"
            ])
        
        # Always include monitoring setup
        next_steps.append("8. Implement continuous validation monitoring")
        next_steps.append("9. Schedule daily truth baseline validation reports")
        
        return next_steps


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Truth Baseline Validator for Production Readiness")
    parser.add_argument("--validate-all", action="store_true", help="Run complete validation suite")
    parser.add_argument("--validate-infrastructure", action="store_true", help="Validate infrastructure only")
    parser.add_argument("--validate-services", action="store_true", help="Validate services only")
    parser.add_argument("--generate-report", action="store_true", help="Generate truth baseline report")
    parser.add_argument("--output", type=str, default=None, help="Output file for results")
    
    args = parser.parse_args()
    
    validator = TruthBaselineValidator()
    
    try:
        if args.validate_all or (not any([args.validate_infrastructure, args.validate_services, args.generate_report])):
            logger.info("Running complete validation suite")
            report = validator.validate_all()
        elif args.validate_infrastructure:
            logger.info("Running infrastructure validation")
            validator.validate_infrastructure_deployment()
            report = validator.generate_truth_baseline_report()
        elif args.validate_services:
            logger.info("Running service validation")
            validator.validate_service_integration()
            report = validator.generate_truth_baseline_report()
        elif args.generate_report:
            logger.info("Generating report from existing results")
            report = validator.generate_truth_baseline_report()
        
        # Output results
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(json.dumps(report, indent=2, default=str))
            logger.info(f"Report written to {output_path}")
        else:
            print(json.dumps(report, indent=2, default=str))
        
        # Exit with appropriate code
        verified_count = sum(1 for r in validator.validation_results if r.verified)
        total_count = len(validator.validation_results)
        
        if verified_count == total_count:
            logger.info("All validations passed")
            sys.exit(0)
        else:
            logger.warning(f"Validation failures: {total_count - verified_count}/{total_count}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation execution failed: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()