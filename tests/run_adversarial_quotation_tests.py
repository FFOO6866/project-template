#!/usr/bin/env python3
"""
Enterprise Adversarial Quotation Testing - Complete Execution Script

This script orchestrates the complete adversarial testing suite for the quotation module,
including infrastructure setup, test execution, and comprehensive reporting.

CRITICAL REQUIREMENTS:
- NO MOCK DATA - All tests run against real infrastructure
- Enterprise metrics: Precision ≥95%, Recall ≥90%, F1-Score ≥92.5%
- Financial accuracy: 100% (zero tolerance for calculation errors)
- Performance: <10 seconds end-to-end processing
- Statistical validation: 95% confidence intervals

Usage:
    python run_adversarial_quotation_tests.py [options]
    
Options:
    --full-suite          Run complete 2,500+ test suite (default: 500 tests)
    --parallel-workers N  Number of parallel test workers (default: 8)  
    --skip-infrastructure Skip Docker infrastructure setup
    --report-format       Report formats: json,csv,html (default: all)
    --output-dir DIR      Output directory for results (default: ./test_results/)
"""

import argparse
import asyncio
import logging
import sys
import time
import json
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Setup project path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import adversarial testing components
from tests.integration.test_adversarial_quotation_generator import (
    AdversarialRFQGenerator, 
    QuotationSystemValidator,
    AdversarialTestCase,
    ValidationResult
)
from tests.utils.adversarial_test_runner import (
    AdversarialTestExecutor,
    TestInfrastructureConfig
)
from tests.utils.adversarial_payload_generator import (
    EnterpriseAdversarialPayloadGenerator,
    generate_comprehensive_adversarial_dataset
)
from tests.utils.enterprise_validation_framework import (
    EnterpriseValidationFramework,
    ValidationMetrics,
    TestCaseResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'adversarial_testing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class AdversarialTestOrchestrator:
    """Orchestrates complete adversarial testing execution."""
    
    def __init__(self, args):
        self.args = args
        self.start_time = None
        self.end_time = None
        self.infrastructure_ready = False
        self.test_results = []
        
        # Create output directory
        self.output_dir = Path(args.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.test_executor = None
        self.generator = None
        self.validator = None
        self.validation_framework = None
        
        # Setup signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.warning("🛑 Received shutdown signal, cleaning up...")
        self._cleanup()
        sys.exit(0)
    
    def _cleanup(self):
        """Cleanup resources."""
        if self.test_executor and hasattr(self.test_executor, 'infrastructure'):
            self.test_executor.infrastructure.cleanup_infrastructure()
    
    def setup_infrastructure(self) -> bool:
        """Setup complete test infrastructure."""
        if self.args.skip_infrastructure:
            logger.info("⏩ Skipping infrastructure setup as requested")
            return True
        
        logger.info("🔄 Setting up adversarial test infrastructure...")
        
        try:
            self.test_executor = AdversarialTestExecutor()
            
            if not self.test_executor.setup_test_environment():
                logger.error("❌ Failed to setup test infrastructure")
                return False
            
            self.infrastructure_ready = True
            logger.info("✅ Test infrastructure ready")
            return True
            
        except Exception as e:
            logger.error(f"❌ Infrastructure setup failed: {e}")
            return False
    
    def initialize_components(self):
        """Initialize all testing components."""
        logger.info("🔄 Initializing adversarial testing components...")
        
        # Test case generator
        self.generator = AdversarialRFQGenerator(seed=42)
        logger.info("✅ Adversarial RFQ generator initialized")
        
        # System validator
        self.validator = QuotationSystemValidator()
        logger.info("✅ Quotation system validator initialized")
        
        # Validation framework
        self.validation_framework = EnterpriseValidationFramework({
            'export_formats': self.args.report_format.split(','),
            'generate_visualizations': True,
            'save_detailed_results': True
        })
        logger.info("✅ Enterprise validation framework initialized")
    
    def generate_test_cases(self) -> List[AdversarialTestCase]:
        """Generate comprehensive adversarial test cases."""
        logger.info("🔄 Generating adversarial test cases...")
        
        if self.args.full_suite:
            logger.info("📊 Generating FULL SUITE: 2,500+ adversarial test cases")
            test_cases = self.generator.generate_all_test_cases()
        else:
            logger.info("📊 Generating SUBSET: 500 adversarial test cases for validation")
            test_cases = []
            test_cases.extend(self.generator.generate_basic_rfq_variations(200))
            test_cases.extend(self.generator.generate_format_attack_cases(100))
            test_cases.extend(self.generator.generate_semantic_confusion_cases(100))
            test_cases.extend(self.generator.generate_business_logic_exploits(50))
            test_cases.extend(self.generator.generate_injection_attack_cases(30))
            test_cases.extend(self.generator.generate_real_world_scenario_cases(20))
        
        logger.info(f"✅ Generated {len(test_cases)} adversarial test cases")
        
        # Save test cases for reference
        test_cases_file = self.output_dir / f"adversarial_test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(test_cases_file, 'w') as f:
            test_cases_data = [
                {
                    'test_id': tc.test_id,
                    'category': tc.category,
                    'attack_type': tc.attack_type,
                    'severity': tc.severity,
                    'expected_behavior': tc.expected_behavior,
                    'validation_criteria': tc.validation_criteria
                } for tc in test_cases
            ]
            json.dump(test_cases_data, f, indent=2)
        
        logger.info(f"💾 Test cases saved to: {test_cases_file}")
        return test_cases
    
    def execute_adversarial_tests(self, test_cases: List[AdversarialTestCase]) -> List[ValidationResult]:
        """Execute adversarial tests with performance monitoring."""
        logger.info(f"🚀 Starting adversarial test execution with {self.args.parallel_workers} workers...")
        
        start_time = time.time()
        
        # Execute tests using validator
        validation_results = self.validator.validate_test_suite(
            test_cases, 
            parallel_workers=self.args.parallel_workers
        )
        
        execution_time = time.time() - start_time
        
        # Extract individual results
        individual_results = validation_results['individual_results']
        
        logger.info(f"✅ Adversarial test execution completed in {execution_time:.2f} seconds")
        logger.info(f"📊 Executed {len(individual_results)} test cases")
        logger.info(f"⚡ Throughput: {len(individual_results)/execution_time:.2f} tests/second")
        
        return individual_results
    
    def convert_to_framework_results(self, validation_results: List[ValidationResult], 
                                   test_cases: List[AdversarialTestCase]) -> List[TestCaseResult]:
        """Convert validation results to framework format."""
        framework_results = []
        
        # Create lookup for test cases
        test_case_lookup = {tc.test_id: tc for tc in test_cases}
        
        for val_result in validation_results:
            test_case = test_case_lookup.get(val_result.test_id)
            
            framework_result = TestCaseResult(
                test_id=val_result.test_id,
                category=test_case.category if test_case else 'unknown',
                attack_type=test_case.attack_type if test_case else 'unknown',
                severity=test_case.severity if test_case else 'unknown',
                success=val_result.success,
                processing_time=val_result.performance_time,
                financial_accuracy=val_result.financial_accuracy,
                detected_vulnerabilities=val_result.detected_vulnerabilities,
                business_failures=val_result.business_logic_failures,
                error_message=val_result.error_message
            )
            
            framework_results.append(framework_result)
            self.validation_framework.add_test_result(framework_result)
        
        return framework_results
    
    def generate_comprehensive_reports(self) -> ValidationMetrics:
        """Generate comprehensive validation reports."""
        logger.info("📊 Generating comprehensive validation reports...")
        
        # Generate enterprise validation report
        metrics = self.validation_framework.generate_comprehensive_validation_report()
        
        # Log key metrics
        logger.info("=" * 60)
        logger.info("🏆 ENTERPRISE ADVERSARIAL TESTING RESULTS")
        logger.info("=" * 60)
        logger.info(f"📊 Precision: {metrics.precision:.4f} ({'✅ PASS' if metrics.precision >= 0.95 else '❌ FAIL'}) (≥0.95)")
        logger.info(f"📊 Recall: {metrics.recall:.4f} ({'✅ PASS' if metrics.recall >= 0.90 else '❌ FAIL'}) (≥0.90)")
        logger.info(f"📊 F1-Score: {metrics.f1_score:.4f} ({'✅ PASS' if metrics.f1_score >= 0.925 else '❌ FAIL'}) (≥0.925)")
        logger.info(f"💰 Financial Accuracy: {metrics.financial_accuracy:.4f} ({'✅ PASS' if metrics.zero_tolerance_failures == 0 else '❌ FAIL'}) (100%)")
        logger.info(f"⚡ Avg Processing Time: {metrics.avg_processing_time:.3f}s ({'✅ PASS' if metrics.avg_processing_time < 10.0 else '❌ FAIL'}) (<10s)")
        logger.info(f"📈 Sample Size: {metrics.sample_size} ({'✅ PASS' if metrics.sample_size >= 30 else '❌ FAIL'}) (≥30)")
        logger.info(f"🔒 Vulnerabilities Detected: {metrics.vulnerabilities_detected}")
        logger.info(f"🛡️ Input Sanitization Rate: {metrics.input_sanitization_rate:.2f}")
        logger.info("=" * 60)
        logger.info(f"🏆 ENTERPRISE COMPLIANCE: {'✅ ACHIEVED' if metrics.enterprise_compliance_met else '❌ NOT MET'}")
        logger.info("=" * 60)
        
        return metrics
    
    def save_execution_summary(self, metrics: ValidationMetrics, test_cases_count: int):
        """Save execution summary."""
        execution_summary = {
            'execution_metadata': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'total_duration': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None,
                'test_cases_executed': test_cases_count,
                'parallel_workers': self.args.parallel_workers,
                'full_suite': self.args.full_suite,
                'infrastructure_used': not self.args.skip_infrastructure
            },
            'enterprise_results': {
                'precision': metrics.precision,
                'recall': metrics.recall,
                'f1_score': metrics.f1_score,
                'financial_accuracy': metrics.financial_accuracy,
                'avg_processing_time': metrics.avg_processing_time,
                'zero_tolerance_failures': metrics.zero_tolerance_failures,
                'enterprise_compliance_achieved': metrics.enterprise_compliance_met
            },
            'security_analysis': {
                'vulnerabilities_detected': metrics.vulnerabilities_detected,
                'injection_attacks_blocked': metrics.injection_attacks_blocked,
                'business_logic_failures': metrics.business_logic_failures,
                'input_sanitization_rate': metrics.input_sanitization_rate
            },
            'compliance_details': metrics.compliance_details
        }
        
        summary_file = self.output_dir / f"adversarial_execution_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(execution_summary, f, indent=2, default=str)
        
        logger.info(f"📄 Execution summary saved: {summary_file}")
    
    def run_complete_adversarial_testing(self) -> bool:
        """Run complete adversarial testing suite."""
        try:
            self.start_time = datetime.now()
            logger.info("🔴 ENTERPRISE ADVERSARIAL QUOTATION TESTING")
            logger.info("=" * 70)
            logger.info("⚠️  CRITICAL: NO MOCK DATA - Testing against REAL infrastructure")
            logger.info("🎯 Enterprise Requirements: Precision ≥95%, Recall ≥90%, F1 ≥92.5%")
            logger.info("💰 Financial: 100% accuracy (zero tolerance for errors)")
            logger.info("⚡ Performance: <10 seconds end-to-end processing")
            logger.info("📈 Statistical: 95% confidence intervals")
            logger.info("=" * 70)
            
            # Step 1: Setup infrastructure
            if not self.setup_infrastructure():
                return False
            
            # Step 2: Initialize components
            self.initialize_components()
            
            # Step 3: Generate test cases
            test_cases = self.generate_test_cases()
            
            # Step 4: Execute adversarial tests
            validation_results = self.execute_adversarial_tests(test_cases)
            
            # Step 5: Convert results for framework
            framework_results = self.convert_to_framework_results(validation_results, test_cases)
            
            # Step 6: Generate comprehensive reports
            metrics = self.generate_comprehensive_reports()
            
            # Step 7: Save execution summary
            self.end_time = datetime.now()
            self.save_execution_summary(metrics, len(test_cases))
            
            # Final status
            success = metrics.enterprise_compliance_met
            
            if success:
                logger.info("🎉 ADVERSARIAL TESTING COMPLETED SUCCESSFULLY")
                logger.info("✅ All enterprise requirements met")
            else:
                logger.error("❌ ADVERSARIAL TESTING COMPLETED WITH FAILURES")
                logger.error("⚠️ Enterprise requirements NOT met - review reports")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Adversarial testing failed: {e}")
            return False
            
        finally:
            self._cleanup()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Enterprise Adversarial Quotation Testing Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_adversarial_quotation_tests.py --full-suite
  python run_adversarial_quotation_tests.py --parallel-workers 12
  python run_adversarial_quotation_tests.py --skip-infrastructure --output-dir ./results/
        """
    )
    
    parser.add_argument(
        '--full-suite',
        action='store_true',
        help='Run complete 2,500+ test suite (default: 500 test subset)'
    )
    
    parser.add_argument(
        '--parallel-workers',
        type=int,
        default=8,
        help='Number of parallel test workers (default: 8)'
    )
    
    parser.add_argument(
        '--skip-infrastructure',
        action='store_true',
        help='Skip Docker infrastructure setup (assumes infrastructure running)'
    )
    
    parser.add_argument(
        '--report-format',
        default='json,csv,html',
        help='Report formats: json,csv,html (default: all)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='./test_results/',
        help='Output directory for results (default: ./test_results/)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()

def main():
    """Main execution function."""
    args = parse_arguments()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create orchestrator and run tests
    orchestrator = AdversarialTestOrchestrator(args)
    
    success = orchestrator.run_complete_adversarial_testing()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()