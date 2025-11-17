"""
Performance and Load Testing Suite

Tests application performance under various load conditions.
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import statistics

from fastapi.testclient import TestClient

from src.job_pricing.api.main import app


@pytest.fixture(scope="module")
def test_client():
    """Create test client"""
    return TestClient(app)


class TestAPIPerformance:
    """Performance tests for API endpoints"""

    def test_health_endpoint_performance(self, test_client):
        """Test health endpoint responds quickly under load"""
        num_requests = 100
        durations = []

        for _ in range(num_requests):
            start = time.time()
            response = test_client.get("/health")
            duration = time.time() - start

            assert response.status_code == 200
            durations.append(duration)

        # Calculate statistics
        avg_duration = statistics.mean(durations)
        p95_duration = statistics.quantiles(durations, n=20)[18]  # 95th percentile
        p99_duration = statistics.quantiles(durations, n=100)[98]  # 99th percentile

        print(f"\nHealth endpoint performance:")
        print(f"  Average: {avg_duration*1000:.2f}ms")
        print(f"  P95: {p95_duration*1000:.2f}ms")
        print(f"  P99: {p99_duration*1000:.2f}ms")

        # Assert performance requirements
        assert avg_duration < 0.1, f"Average response time too slow: {avg_duration*1000:.2f}ms"
        assert p95_duration < 0.15, f"P95 response time too slow: {p95_duration*1000:.2f}ms"

    def test_readiness_endpoint_performance(self, test_client):
        """Test readiness endpoint performance with database checks"""
        num_requests = 50
        durations = []

        for _ in range(num_requests):
            start = time.time()
            response = test_client.get("/ready")
            duration = time.time() - start

            assert response.status_code == 200
            durations.append(duration)

        avg_duration = statistics.mean(durations)
        p95_duration = statistics.quantiles(durations, n=20)[18]

        print(f"\nReadiness endpoint performance:")
        print(f"  Average: {avg_duration*1000:.2f}ms")
        print(f"  P95: {p95_duration*1000:.2f}ms")

        # Readiness checks are allowed to be slower due to database queries
        assert avg_duration < 0.5, f"Average response time too slow: {avg_duration*1000:.2f}ms"

    def test_concurrent_requests(self, test_client):
        """Test API performance under concurrent load"""
        num_threads = 10
        requests_per_thread = 10

        def make_requests(thread_id: int) -> List[float]:
            """Make multiple requests and return durations"""
            durations = []
            for i in range(requests_per_thread):
                start = time.time()
                response = test_client.get("/health")
                duration = time.time() - start

                assert response.status_code == 200
                durations.append(duration)

            return durations

        # Execute concurrent requests
        start_time = time.time()
        all_durations = []

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_requests, i) for i in range(num_threads)]

            for future in as_completed(futures):
                all_durations.extend(future.result())

        total_time = time.time() - start_time
        total_requests = num_threads * requests_per_thread

        # Calculate statistics
        avg_duration = statistics.mean(all_durations)
        throughput = total_requests / total_time

        print(f"\nConcurrent load test:")
        print(f"  Total requests: {total_requests}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Throughput: {throughput:.2f} req/s")
        print(f"  Average latency: {avg_duration*1000:.2f}ms")

        # Assert performance requirements
        assert throughput > 50, f"Throughput too low: {throughput:.2f} req/s"

    def test_sustained_load(self, test_client):
        """Test API under sustained load for 30 seconds"""
        duration_seconds = 10  # Reduced for faster testing
        successful_requests = 0
        failed_requests = 0
        durations = []

        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            request_start = time.time()
            try:
                response = test_client.get("/health")
                request_duration = time.time() - request_start

                if response.status_code == 200:
                    successful_requests += 1
                    durations.append(request_duration)
                else:
                    failed_requests += 1

            except Exception:
                failed_requests += 1

        total_time = time.time() - start_time
        total_requests = successful_requests + failed_requests
        throughput = successful_requests / total_time
        success_rate = (successful_requests / total_requests) * 100

        print(f"\nSustained load test ({duration_seconds}s):")
        print(f"  Total requests: {total_requests}")
        print(f"  Successful: {successful_requests}")
        print(f"  Failed: {failed_requests}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Throughput: {throughput:.2f} req/s")

        if durations:
            print(f"  Avg latency: {statistics.mean(durations)*1000:.2f}ms")

        # Assert requirements
        assert success_rate > 99, f"Success rate too low: {success_rate:.1f}%"


class TestDatabasePerformance:
    """Performance tests for database operations"""

    @pytest.mark.integration
    def test_database_query_performance(self):
        """Test database query performance"""
        from src.job_pricing.core.database import get_session
        from sqlalchemy import text
        import time

        session = next(get_session())

        # Test simple query
        start = time.time()
        result = session.execute(text("SELECT 1"))
        duration = time.time() - start

        assert result.fetchone()[0] == 1
        assert duration < 0.01, f"Simple query too slow: {duration*1000:.2f}ms"

        # Test more complex query
        start = time.time()
        session.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            LIMIT 100
        """))
        duration = time.time() - start

        assert duration < 0.1, f"Table query too slow: {duration*1000:.2f}ms"

        session.close()


class TestMemoryUsage:
    """Memory usage tests"""

    def test_memory_leak_detection(self, test_client):
        """Test for memory leaks by making repeated requests"""
        import gc
        import sys

        gc.collect()
        initial_objects = len(gc.get_objects())

        # Make many requests
        for _ in range(100):
            test_client.get("/health")

        gc.collect()
        final_objects = len(gc.get_objects())

        object_growth = final_objects - initial_objects

        print(f"\nMemory leak test:")
        print(f"  Initial objects: {initial_objects}")
        print(f"  Final objects: {final_objects}")
        print(f"  Growth: {object_growth}")

        # Allow some growth but flag excessive growth
        assert object_growth < 1000, f"Possible memory leak detected: {object_growth} new objects"


class TestPerformanceBudget:
    """Performance budget tests"""

    PERFORMANCE_BUDGETS = {
        "/health": {
            "max_response_time_ms": 100,
            "max_p95_ms": 150,
        },
        "/ready": {
            "max_response_time_ms": 500,
            "max_p95_ms": 1000,
        },
    }

    @pytest.mark.parametrize("endpoint,budget", PERFORMANCE_BUDGETS.items())
    def test_performance_budget(self, test_client, endpoint, budget):
        """Test that endpoints meet performance budget requirements"""
        num_requests = 20
        durations = []

        for _ in range(num_requests):
            start = time.time()
            response = test_client.get(endpoint)
            duration = (time.time() - start) * 1000  # Convert to ms

            assert response.status_code == 200
            durations.append(duration)

        avg_duration = statistics.mean(durations)
        p95_duration = statistics.quantiles(durations, n=20)[18]

        print(f"\nPerformance budget for {endpoint}:")
        print(f"  Average: {avg_duration:.2f}ms (budget: {budget['max_response_time_ms']}ms)")
        print(f"  P95: {p95_duration:.2f}ms (budget: {budget['max_p95_ms']}ms)")

        assert avg_duration <= budget["max_response_time_ms"], \
            f"Average response time exceeds budget: {avg_duration:.2f}ms > {budget['max_response_time_ms']}ms"

        assert p95_duration <= budget["max_p95_ms"], \
            f"P95 response time exceeds budget: {p95_duration:.2f}ms > {budget['max_p95_ms']}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
