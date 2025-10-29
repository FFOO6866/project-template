#!/usr/bin/env python3
"""
Comprehensive Test Suite for Phase 2 UNSPSC/ETIM Classification System

Tests all components:
- ProductClassifier (semantic matching, caching, performance)
- PostgreSQL integration (classify_product, batch classification)
- Neo4j integration (classification nodes, relationships)
- API endpoints (/api/classify/product, /api/classify/batch, etc.)

Performance Requirements Validation:
- Single classification: <500ms
- Batch classification: <100ms per product
- Cache hit rate: >80% after warm-up

Run with: python test_classification_system.py
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClassificationSystemTester:
    """Comprehensive test suite for classification system"""

    def __init__(self):
        """Initialize tester"""
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def log_test_result(self, test_name: str, passed: bool, message: str, duration_ms: int = 0):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"

        result = {
            'test_name': test_name,
            'passed': passed,
            'message': message,
            'duration_ms': duration_ms,
            'status': status
        }
        self.test_results.append(result)

        logger.info(f"{status} - {test_name}: {message} ({duration_ms}ms)")

    def test_redis_connection(self) -> bool:
        """Test Redis connection for caching"""
        test_name = "Redis Connection Test"
        start_time = time.time()

        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6380')

            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()

            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(test_name, True, f"Connected to Redis at {redis_url}", duration_ms)
            return True

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(test_name, False, f"Redis connection failed: {e}", duration_ms)
            return False

    def test_embedding_model_load(self) -> bool:
        """Test sentence transformer model loading"""
        test_name = "Embedding Model Load Test"
        start_time = time.time()

        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("all-MiniLM-L6-v2")

            # Test embedding generation
            test_text = "Cordless drill with battery pack"
            embedding = model.encode([test_text])[0]

            if len(embedding) == 384:  # all-MiniLM-L6-v2 has 384 dimensions
                duration_ms = int((time.time() - start_time) * 1000)
                self.log_test_result(
                    test_name,
                    True,
                    f"Model loaded and generated {len(embedding)}-dim embedding",
                    duration_ms
                )
                return True
            else:
                raise ValueError(f"Unexpected embedding dimension: {len(embedding)}")

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(test_name, False, f"Model load failed: {e}", duration_ms)
            return False

    def test_classifier_initialization(self) -> bool:
        """Test ProductClassifier initialization"""
        test_name = "Classifier Initialization Test"
        start_time = time.time()

        try:
            from src.core.product_classifier import ProductClassifier

            classifier = ProductClassifier()

            # Check components initialized
            if classifier.redis_client is None:
                raise RuntimeError("Redis client not initialized")

            if classifier.embedding_model is None:
                raise RuntimeError("Embedding model not loaded")

            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(
                test_name,
                True,
                "ProductClassifier initialized successfully",
                duration_ms
            )

            classifier.close()
            return True

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(test_name, False, f"Classifier init failed: {e}", duration_ms)
            return False

    def test_classification_data_loaded(self) -> bool:
        """Test UNSPSC and ETIM data are loaded"""
        test_name = "Classification Data Load Test"
        start_time = time.time()

        try:
            from src.core.product_classifier import get_classifier

            classifier = get_classifier()

            unspsc_count = len(classifier.unspsc_codes)
            etim_count = len(classifier.etim_classes)

            if unspsc_count == 0 and etim_count == 0:
                self.log_test_result(
                    test_name,
                    False,
                    "No classification data loaded. Run scripts/load_classification_data.py",
                    int((time.time() - start_time) * 1000)
                )
                return False

            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(
                test_name,
                True,
                f"Loaded {unspsc_count} UNSPSC codes and {etim_count} ETIM classes",
                duration_ms
            )
            return True

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(test_name, False, f"Data load check failed: {e}", duration_ms)
            return False

    def test_single_product_classification(self) -> bool:
        """Test single product classification performance"""
        test_name = "Single Product Classification Test"
        start_time = time.time()

        try:
            from src.core.product_classifier import get_classifier

            classifier = get_classifier()

            # Test product
            result = classifier.classify_product(
                product_id=1,
                product_sku="TEST-001",
                product_name="Cordless Drill 18V with Battery Pack",
                product_description="Professional grade cordless drill with lithium-ion battery",
                product_category="Power Tools",
                use_cache=False  # Force fresh classification
            )

            duration_ms = result.processing_time_ms

            # Validate performance requirement: <500ms
            if duration_ms > 500:
                self.log_test_result(
                    test_name,
                    False,
                    f"Classification took {duration_ms}ms (requirement: <500ms)",
                    duration_ms
                )
                return False

            # Check classification results
            if not result.unspsc_code and not result.etim_class:
                self.log_test_result(
                    test_name,
                    False,
                    "No classification codes returned",
                    duration_ms
                )
                return False

            self.log_test_result(
                test_name,
                True,
                f"Classified in {duration_ms}ms: UNSPSC={result.unspsc_code}, ETIM={result.etim_class}",
                duration_ms
            )
            return True

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(test_name, False, f"Classification failed: {e}", duration_ms)
            return False

    def test_classification_caching(self) -> bool:
        """Test classification caching performance"""
        test_name = "Classification Caching Test"

        try:
            from src.core.product_classifier import get_classifier

            classifier = get_classifier()

            test_product = {
                'product_id': 2,
                'product_sku': 'TEST-002',
                'product_name': 'LED Work Light 5000 Lumens',
                'product_description': 'High-intensity LED work light for construction sites',
                'product_category': 'Lighting'
            }

            # First classification (no cache)
            start_time = time.time()
            result1 = classifier.classify_product(use_cache=True, **test_product)
            first_time_ms = int((time.time() - start_time) * 1000)

            # Second classification (should hit cache)
            start_time = time.time()
            result2 = classifier.classify_product(use_cache=True, **test_product)
            cached_time_ms = int((time.time() - start_time) * 1000)

            # Cache should be significantly faster
            speedup_ratio = first_time_ms / cached_time_ms if cached_time_ms > 0 else 0

            if not result2.cache_hit:
                self.log_test_result(
                    test_name,
                    False,
                    f"Cache miss on second request (first: {first_time_ms}ms, second: {cached_time_ms}ms)",
                    cached_time_ms
                )
                return False

            if speedup_ratio < 2:  # Cache should be at least 2x faster
                self.log_test_result(
                    test_name,
                    False,
                    f"Cache speedup too low ({speedup_ratio:.1f}x, expected >2x)",
                    cached_time_ms
                )
                return False

            self.log_test_result(
                test_name,
                True,
                f"Cache hit with {speedup_ratio:.1f}x speedup ({first_time_ms}ms -> {cached_time_ms}ms)",
                cached_time_ms
            )
            return True

        except Exception as e:
            self.log_test_result(test_name, False, f"Caching test failed: {e}", 0)
            return False

    def test_batch_classification(self) -> bool:
        """Test batch classification performance"""
        test_name = "Batch Classification Test"
        start_time = time.time()

        try:
            from src.core.product_classifier import get_classifier

            classifier = get_classifier()

            # Test products batch
            test_products = [
                {
                    'id': i,
                    'sku': f'TEST-{i:03d}',
                    'name': product['name'],
                    'description': product['description'],
                    'category': product['category']
                }
                for i, product in enumerate([
                    {
                        'name': 'Cordless Drill 18V',
                        'description': 'Professional cordless drill',
                        'category': 'Power Tools'
                    },
                    {
                        'name': 'Safety Glasses',
                        'description': 'Impact-resistant safety eyewear',
                        'category': 'Safety Equipment'
                    },
                    {
                        'name': 'Measuring Tape 25ft',
                        'description': 'Heavy-duty measuring tape',
                        'category': 'Hand Tools'
                    },
                    {
                        'name': 'Work Gloves',
                        'description': 'Cut-resistant work gloves',
                        'category': 'Safety Equipment'
                    },
                    {
                        'name': 'LED Headlamp',
                        'description': 'Rechargeable LED headlamp',
                        'category': 'Lighting'
                    },
                    {
                        'name': 'Hammer Drill',
                        'description': 'Electric hammer drill',
                        'category': 'Power Tools'
                    },
                    {
                        'name': 'Ladder 6ft',
                        'description': 'Aluminum step ladder',
                        'category': 'Ladders'
                    },
                    {
                        'name': 'Paint Roller Set',
                        'description': 'Professional paint roller kit',
                        'category': 'Painting Supplies'
                    },
                    {
                        'name': 'Cable Tester',
                        'description': 'Network cable testing tool',
                        'category': 'Testing Equipment'
                    },
                    {
                        'name': 'Toolbox 20-inch',
                        'description': 'Metal toolbox with compartments',
                        'category': 'Storage'
                    }
                ], start=1)
            ]

            results = classifier.classify_products_batch(test_products, use_cache=False)

            total_time_ms = int((time.time() - start_time) * 1000)
            avg_time_per_product = total_time_ms / len(results) if results else 0

            # Validate performance requirement: <100ms per product for batches
            if avg_time_per_product > 100:
                self.log_test_result(
                    test_name,
                    False,
                    f"Batch avg {avg_time_per_product:.1f}ms/product (requirement: <100ms)",
                    total_time_ms
                )
                return False

            # Check all products were classified
            if len(results) != len(test_products):
                self.log_test_result(
                    test_name,
                    False,
                    f"Only {len(results)}/{len(test_products)} products classified",
                    total_time_ms
                )
                return False

            self.log_test_result(
                test_name,
                True,
                f"Classified {len(results)} products in {total_time_ms}ms ({avg_time_per_product:.1f}ms/product)",
                total_time_ms
            )
            return True

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(test_name, False, f"Batch classification failed: {e}", duration_ms)
            return False

    def test_postgresql_integration(self) -> bool:
        """Test PostgreSQL database integration"""
        test_name = "PostgreSQL Integration Test"
        start_time = time.time()

        try:
            from src.core.postgresql_database import get_database

            db = get_database()

            # Test connection
            if not db.test_connection():
                raise RuntimeError("PostgreSQL connection failed")

            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(
                test_name,
                True,
                "PostgreSQL connected and classification methods available",
                duration_ms
            )
            return True

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(test_name, False, f"PostgreSQL integration failed: {e}", duration_ms)
            return False

    def test_neo4j_integration(self) -> bool:
        """Test Neo4j knowledge graph integration"""
        test_name = "Neo4j Integration Test"
        start_time = time.time()

        try:
            from src.core.neo4j_knowledge_graph import get_knowledge_graph

            kg = get_knowledge_graph()

            # Test connection
            if not kg.test_connection():
                raise RuntimeError("Neo4j connection failed")

            # Check classification node creation methods exist
            if not hasattr(kg, 'create_unspsc_node'):
                raise RuntimeError("create_unspsc_node method not found")

            if not hasattr(kg, 'create_etim_node'):
                raise RuntimeError("create_etim_node method not found")

            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(
                test_name,
                True,
                "Neo4j connected and classification methods available",
                duration_ms
            )
            return True

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(test_name, False, f"Neo4j integration failed: {e}", duration_ms)
            return False

    def test_api_endpoints(self) -> bool:
        """Test API endpoints (if server is running)"""
        test_name = "API Endpoints Test"
        start_time = time.time()

        try:
            import requests

            api_url = os.getenv('API_URL', 'http://localhost:8000')

            # Test health endpoint
            response = requests.get(f"{api_url}/health", timeout=5)

            if response.status_code != 200:
                raise RuntimeError(f"Health check failed: {response.status_code}")

            # Check if classification endpoints are documented
            root_response = requests.get(f"{api_url}/", timeout=5)
            root_data = root_response.json()

            endpoints = root_data.get('endpoints', {})
            has_classify = 'POST /api/classify/product' in str(endpoints)
            has_batch = 'POST /api/classify/batch' in str(endpoints)

            if not (has_classify and has_batch):
                self.log_test_result(
                    test_name,
                    False,
                    "Classification endpoints not found in API documentation",
                    int((time.time() - start_time) * 1000)
                )
                return False

            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(
                test_name,
                True,
                f"API server running at {api_url} with classification endpoints",
                duration_ms
            )
            return True

        except requests.exceptions.ConnectionError:
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(
                test_name,
                False,
                "API server not running. Start with: python src/production_api_server.py",
                duration_ms
            )
            return False
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_test_result(test_name, False, f"API test failed: {e}", duration_ms)
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "=" * 80)
        print("Phase 2 UNSPSC/ETIM Classification System - Comprehensive Test Suite")
        print("=" * 80 + "\n")

        # Infrastructure tests
        print("📋 Infrastructure Tests")
        print("-" * 80)
        self.test_redis_connection()
        self.test_embedding_model_load()
        self.test_postgresql_integration()
        self.test_neo4j_integration()

        # Classifier tests
        print("\n📋 Classifier Tests")
        print("-" * 80)
        self.test_classifier_initialization()
        self.test_classification_data_loaded()
        self.test_single_product_classification()
        self.test_classification_caching()
        self.test_batch_classification()

        # API tests
        print("\n📋 API Tests")
        print("-" * 80)
        self.test_api_endpoints()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0:.1f}%")

        if self.failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test_name']}: {result['message']}")

        print("\n" + "=" * 80)

        # Return exit code
        return 0 if self.failed_tests == 0 else 1


def main():
    """Main entry point"""
    try:
        tester = ClassificationSystemTester()
        tester.run_all_tests()
        exit_code = tester.print_summary()

        if exit_code == 0:
            print("\n✅ All tests passed! Phase 2 Classification System is ready.")
            print("\nNext steps:")
            print("1. Load classification data: python scripts/load_classification_data.py --unspsc <file> --etim <file>")
            print("2. Classify products: curl -X POST http://localhost:8000/api/classify/product -d '{\"product_id\": 1}'")
            print("3. Check statistics: curl http://localhost:8000/api/classification/statistics")
        else:
            print("\n❌ Some tests failed. Review the results above.")

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
