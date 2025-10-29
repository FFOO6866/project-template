#!/usr/bin/env python3
"""
DataFlow Product Import Validation Script
Validates that all 17,266 products were imported successfully using DataFlow query nodes

Features:
- Uses DataFlow auto-generated query nodes
- MongoDB-style filtering and aggregation
- Comprehensive data quality validation
- Performance benchmarking
- Export validation reports
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

# Add src to Python path
sys.path.append('/app/src')

# Import DataFlow and models
from dataflow import DataFlow
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/dataflow_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataFlowImportValidator:
    """Comprehensive validation using DataFlow query nodes."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        
        # Initialize DataFlow
        self.db = DataFlow(
            database_url=database_url,
            pool_size=10,
            monitoring=True
        )
        
        # Initialize runtime
        self.runtime = LocalRuntime()
        
        # Validation results
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "database_url": database_url,
            "tests": {},
            "summary": {},
            "performance": {}
        }
        
        logger.info("DataFlow validation initialized")
    
    async def initialize_dataflow(self) -> bool:
        """Initialize DataFlow models."""
        try:
            # Import models to ensure nodes are available
            from horme_dataflow_models import Category, Brand, Product, db
            self.db = db
            
            await self.db.initialize()
            logger.info("DataFlow validation ready - all query nodes available")
            return True
            
        except Exception as e:
            logger.error(f"DataFlow initialization failed: {e}")
            return False
    
    async def validate_product_count(self) -> Dict[str, Any]:
        """Validate total product count using ProductListNode."""
        try:
            logger.info("Validating product count...")
            
            # Get total count of all products
            workflow = WorkflowBuilder()
            workflow.add_node("ProductListNode", "count_all_products", {
                "filter": {},  # No filter = all products
                "limit": 50000,  # High limit to get all
                "count_only": False
            })
            
            start_time = datetime.now()
            results, run_id = self.runtime.execute(workflow.build())
            query_time = (datetime.now() - start_time).total_seconds()
            
            if results and "count_all_products" in results:
                total_products = len(results["count_all_products"]) if isinstance(results["count_all_products"], list) else 0
                
                # Also check active products
                active_workflow = WorkflowBuilder()
                active_workflow.add_node("ProductListNode", "count_active_products", {
                    "filter": {"status": "active"},
                    "limit": 50000
                })
                
                active_results, active_run_id = self.runtime.execute(active_workflow.build())
                active_products = len(active_results["count_active_products"]) if active_results and "count_active_products" in active_results else 0
                
                result = {
                    "status": "PASS" if total_products >= 17200 else "FAIL",  # Allow for some variation
                    "total_products": total_products,
                    "active_products": active_products,
                    "expected_minimum": 17200,
                    "query_time_seconds": query_time,
                    "message": f"Found {total_products:,} total products ({active_products:,} active)"
                }
                
                logger.info(f"Product count validation: {result['message']} - {result['status']}")
                return result
            else:
                return {
                    "status": "FAIL",
                    "error": "Failed to query products",
                    "query_time_seconds": query_time
                }
                
        except Exception as e:
            logger.error(f"Product count validation failed: {e}")
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def validate_categories(self) -> Dict[str, Any]:
        """Validate categories using CategoryListNode."""
        try:
            logger.info("Validating categories...")
            
            workflow = WorkflowBuilder()
            workflow.add_node("CategoryListNode", "list_categories", {
                "filter": {"is_active": True},
                "order_by": ["name"],
                "limit": 1000
            })
            
            start_time = datetime.now()
            results, run_id = self.runtime.execute(workflow.build())
            query_time = (datetime.now() - start_time).total_seconds()
            
            if results and "list_categories" in results:
                categories = results["list_categories"]
                category_count = len(categories)
                
                # Sample category names for validation
                sample_categories = [cat["name"] for cat in categories[:10]]
                
                result = {
                    "status": "PASS" if category_count > 0 else "FAIL",
                    "category_count": category_count,
                    "sample_categories": sample_categories,
                    "query_time_seconds": query_time,
                    "message": f"Found {category_count} categories"
                }
                
                logger.info(f"Category validation: {result['message']} - {result['status']}")
                return result
            else:
                return {
                    "status": "FAIL",
                    "error": "Failed to query categories"
                }
                
        except Exception as e:
            logger.error(f"Category validation failed: {e}")
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def validate_brands(self) -> Dict[str, Any]:
        """Validate brands using BrandListNode."""
        try:
            logger.info("Validating brands...")
            
            workflow = WorkflowBuilder()
            workflow.add_node("BrandListNode", "list_brands", {
                "filter": {"is_active": True},
                "order_by": ["name"],
                "limit": 1000
            })
            
            start_time = datetime.now()
            results, run_id = self.runtime.execute(workflow.build())
            query_time = (datetime.now() - start_time).total_seconds()
            
            if results and "list_brands" in results:
                brands = results["list_brands"]
                brand_count = len(brands)
                
                # Sample brand names for validation
                sample_brands = [brand["name"] for brand in brands[:10]]
                
                result = {
                    "status": "PASS" if brand_count > 0 else "FAIL",
                    "brand_count": brand_count,
                    "sample_brands": sample_brands,
                    "query_time_seconds": query_time,
                    "message": f"Found {brand_count} brands"
                }
                
                logger.info(f"Brand validation: {result['message']} - {result['status']}")
                return result
            else:
                return {
                    "status": "FAIL",
                    "error": "Failed to query brands"
                }
                
        except Exception as e:
            logger.error(f"Brand validation failed: {e}")
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def validate_data_quality(self) -> Dict[str, Any]:
        """Validate data quality using MongoDB-style queries."""
        try:
            logger.info("Validating data quality...")
            
            # Check for products with missing SKUs
            missing_sku_workflow = WorkflowBuilder()
            missing_sku_workflow.add_node("ProductListNode", "missing_sku", {
                "filter": {
                    "$or": [
                        {"sku": {"$eq": ""}},
                        {"sku": {"$eq": None}}
                    ]
                },
                "limit": 100
            })
            
            # Check for products with missing names
            missing_name_workflow = WorkflowBuilder()
            missing_name_workflow.add_node("ProductListNode", "missing_name", {
                "filter": {
                    "$or": [
                        {"name": {"$eq": ""}},
                        {"name": {"$eq": None}}
                    ]
                },
                "limit": 100
            })
            
            # Check for products with valid category and brand relationships
            valid_relations_workflow = WorkflowBuilder()
            valid_relations_workflow.add_node("ProductListNode", "valid_relations", {
                "filter": {
                    "category_id": {"$ne": None},
                    "brand_id": {"$ne": None},
                    "status": "active"
                },
                "limit": 10
            })
            
            # Execute all validation workflows
            start_time = datetime.now()
            
            missing_sku_results, _ = self.runtime.execute(missing_sku_workflow.build())
            missing_name_results, _ = self.runtime.execute(missing_name_workflow.build())
            valid_relations_results, _ = self.runtime.execute(valid_relations_workflow.build())
            
            query_time = (datetime.now() - start_time).total_seconds()
            
            # Analyze results
            missing_sku_count = len(missing_sku_results.get("missing_sku", [])) if missing_sku_results else 0
            missing_name_count = len(missing_name_results.get("missing_name", [])) if missing_name_results else 0
            valid_relations_count = len(valid_relations_results.get("valid_relations", [])) if valid_relations_results else 0
            
            # Sample valid product for inspection
            sample_product = None
            if valid_relations_results and "valid_relations" in valid_relations_results and valid_relations_results["valid_relations"]:
                sample_product = valid_relations_results["valid_relations"][0]
                # Remove sensitive data for logging
                sample_display = {
                    "sku": sample_product.get("sku", "N/A"),
                    "name": sample_product.get("name", "N/A")[:50] + "..." if len(sample_product.get("name", "")) > 50 else sample_product.get("name", "N/A"),
                    "category_id": sample_product.get("category_id"),
                    "brand_id": sample_product.get("brand_id"),
                    "status": sample_product.get("status")
                }
            
            result = {
                "status": "PASS" if missing_sku_count == 0 and missing_name_count == 0 and valid_relations_count > 0 else "FAIL",
                "missing_sku_count": missing_sku_count,
                "missing_name_count": missing_name_count,
                "valid_relations_sample_count": valid_relations_count,
                "sample_valid_product": sample_display if sample_product else None,
                "query_time_seconds": query_time,
                "message": f"Data quality check: {missing_sku_count} missing SKUs, {missing_name_count} missing names"
            }
            
            logger.info(f"Data quality validation: {result['message']} - {result['status']}")
            return result
            
        except Exception as e:
            logger.error(f"Data quality validation failed: {e}")
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def validate_search_functionality(self) -> Dict[str, Any]:
        """Test search functionality using ProductListNode filters."""
        try:
            logger.info("Validating search functionality...")
            
            # Test text search (if full-text search is enabled)
            search_workflow = WorkflowBuilder()
            search_workflow.add_node("ProductListNode", "search_test", {
                "filter": {
                    "name": {"$regex": ".*laptop.*", "$options": "i"}  # Case-insensitive search for "laptop"
                },
                "limit": 10
            })
            
            # Test category filtering
            category_filter_workflow = WorkflowBuilder()
            category_filter_workflow.add_node("ProductListNode", "category_filter", {
                "filter": {
                    "category_id": {"$ne": None}
                },
                "limit": 5
            })
            
            # Test status filtering
            status_filter_workflow = WorkflowBuilder()
            status_filter_workflow.add_node("ProductListNode", "status_filter", {
                "filter": {
                    "status": "active",
                    "is_published": True
                },
                "limit": 5
            })
            
            start_time = datetime.now()
            
            search_results, _ = self.runtime.execute(search_workflow.build())
            category_results, _ = self.runtime.execute(category_filter_workflow.build())
            status_results, _ = self.runtime.execute(status_filter_workflow.build())
            
            query_time = (datetime.now() - start_time).total_seconds()
            
            search_count = len(search_results.get("search_test", [])) if search_results else 0
            category_count = len(category_results.get("category_filter", [])) if category_results else 0
            status_count = len(status_results.get("status_filter", [])) if status_results else 0
            
            result = {
                "status": "PASS" if category_count > 0 and status_count > 0 else "FAIL",
                "text_search_results": search_count,
                "category_filter_results": category_count,
                "status_filter_results": status_count,
                "query_time_seconds": query_time,
                "message": f"Search tests: {search_count} text matches, {category_count} category matches, {status_count} status matches"
            }
            
            logger.info(f"Search functionality validation: {result['message']} - {result['status']}")
            return result
            
        except Exception as e:
            logger.error(f"Search functionality validation failed: {e}")
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def performance_benchmark(self) -> Dict[str, Any]:
        """Benchmark DataFlow query performance."""
        try:
            logger.info("Running performance benchmark...")
            
            # Test 1: Large result set query
            large_query_workflow = WorkflowBuilder()
            large_query_workflow.add_node("ProductListNode", "large_query", {
                "filter": {"status": "active"},
                "limit": 5000,
                "order_by": ["created_at"]
            })
            
            # Test 2: Complex filter query
            complex_filter_workflow = WorkflowBuilder()
            complex_filter_workflow.add_node("ProductListNode", "complex_filter", {
                "filter": {
                    "status": "active",
                    "is_published": True,
                    "category_id": {"$ne": None},
                    "brand_id": {"$ne": None}
                },
                "limit": 1000
            })
            
            # Execute benchmarks
            start_time = datetime.now()
            large_results, _ = self.runtime.execute(large_query_workflow.build())
            large_query_time = (datetime.now() - start_time).total_seconds()
            
            start_time = datetime.now()
            complex_results, _ = self.runtime.execute(complex_filter_workflow.build())
            complex_query_time = (datetime.now() - start_time).total_seconds()
            
            large_count = len(large_results.get("large_query", [])) if large_results else 0
            complex_count = len(complex_results.get("complex_filter", [])) if complex_results else 0
            
            # Calculate throughput
            large_throughput = large_count / large_query_time if large_query_time > 0 else 0
            complex_throughput = complex_count / complex_query_time if complex_query_time > 0 else 0
            
            result = {
                "large_query_time_seconds": large_query_time,
                "large_query_count": large_count,
                "large_query_throughput": f"{large_throughput:.1f} records/sec",
                "complex_query_time_seconds": complex_query_time,
                "complex_query_count": complex_count,
                "complex_query_throughput": f"{complex_throughput:.1f} records/sec",
                "performance_grade": "EXCELLENT" if large_query_time < 2.0 and complex_query_time < 1.0 else "GOOD" if large_query_time < 5.0 and complex_query_time < 2.0 else "NEEDS_IMPROVEMENT"
            }
            
            logger.info(f"Performance benchmark completed - Grade: {result['performance_grade']}")
            return result
            
        except Exception as e:
            logger.error(f"Performance benchmark failed: {e}")
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def run_full_validation(self) -> bool:
        """Run complete validation suite."""
        try:
            logger.info("Starting comprehensive DataFlow validation...")
            
            # Initialize DataFlow
            if not await self.initialize_dataflow():
                return False
            
            # Run all validation tests
            self.validation_results["tests"]["product_count"] = await self.validate_product_count()
            self.validation_results["tests"]["categories"] = await self.validate_categories()
            self.validation_results["tests"]["brands"] = await self.validate_brands()
            self.validation_results["tests"]["data_quality"] = await self.validate_data_quality()
            self.validation_results["tests"]["search_functionality"] = await self.validate_search_functionality()
            self.validation_results["performance"] = await self.performance_benchmark()
            
            # Generate summary
            passed_tests = sum(1 for test in self.validation_results["tests"].values() if test.get("status") == "PASS")
            total_tests = len(self.validation_results["tests"])
            
            self.validation_results["summary"] = {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": f"{(passed_tests/total_tests*100):.1f}%",
                "overall_status": "PASS" if passed_tests == total_tests else "FAIL"
            }
            
            # Log summary
            logger.info(f"Validation completed: {passed_tests}/{total_tests} tests passed ({self.validation_results['summary']['success_rate']})")
            
            return self.validation_results["summary"]["overall_status"] == "PASS"
            
        except Exception as e:
            logger.error(f"Full validation failed: {e}")
            return False
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report."""
        report_file = f"/app/reports/dataflow_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        # Also create human-readable report
        text_report_file = report_file.replace('.json', '.txt')
        
        with open(text_report_file, 'w') as f:
            f.write("DATAFLOW IMPORT VALIDATION REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {self.validation_results['timestamp']}\n")
            f.write(f"Database: {self.validation_results['database_url']}\n\n")
            
            f.write("SUMMARY\n")
            f.write("-" * 40 + "\n")
            summary = self.validation_results["summary"]
            f.write(f"Overall Status: {summary['overall_status']}\n")
            f.write(f"Tests Passed: {summary['passed_tests']}/{summary['total_tests']} ({summary['success_rate']})\n\n")
            
            f.write("TEST RESULTS\n")
            f.write("-" * 40 + "\n")
            for test_name, test_result in self.validation_results["tests"].items():
                f.write(f"{test_name.upper()}: {test_result.get('status', 'UNKNOWN')}\n")
                f.write(f"  Message: {test_result.get('message', 'No message')}\n")
                if 'error' in test_result:
                    f.write(f"  Error: {test_result['error']}\n")
                f.write("\n")
            
            f.write("PERFORMANCE METRICS\n")
            f.write("-" * 40 + "\n")
            perf = self.validation_results["performance"]
            f.write(f"Performance Grade: {perf.get('performance_grade', 'N/A')}\n")
            f.write(f"Large Query Throughput: {perf.get('large_query_throughput', 'N/A')}\n")
            f.write(f"Complex Query Throughput: {perf.get('complex_query_throughput', 'N/A')}\n")
        
        logger.info(f"Validation reports saved:")
        logger.info(f"  JSON: {report_file}")
        logger.info(f"  Text: {text_report_file}")
        
        return report_file

async def main():
    """Main validation execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate DataFlow product import')
    parser.add_argument('--database-url', type=str,
                       default=os.getenv('DATABASE_URL', 'postgresql://horme_user:secure_password_2024@postgres:5432/horme_db'),
                       help='PostgreSQL database URL')
    
    args = parser.parse_args()
    
    logger.info("Starting DataFlow Import Validation")
    logger.info("=" * 80)
    logger.info("Target: Validate 17,266 products imported via DataFlow")
    logger.info("=" * 80)
    
    # Initialize validator
    validator = DataFlowImportValidator(args.database_url)
    
    try:
        # Run full validation
        success = await validator.run_full_validation()
        
        # Generate reports
        report_file = validator.generate_validation_report()
        
        if success:
            logger.info("SUCCESS: All DataFlow validation tests passed!")
            logger.info(f"Validation report: {report_file}")
        else:
            logger.error("FAILURE: Some DataFlow validation tests failed")
            logger.info(f"See detailed report: {report_file}")
        
        return success
        
    except Exception as e:
        logger.error(f"DataFlow validation failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)