"""
Performance Benchmark Suite for Job Pricing Engine
Tests response times, throughput, and resource utilization under various loads.
"""
import time
import statistics
import logging
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.job_pricing.core.database import get_session
from src.job_pricing.models import JobPricingRequest
from src.job_pricing.services.pricing_calculation_service_v3 import PricingCalculationServiceV3
from src.job_pricing.services.job_matching_service import JobMatchingService

logging.basicConfig(level=logging.WARNING)  # Reduce noise during benchmarks
logger = logging.getLogger(__name__)

class PerformanceBenchmark:
    """Performance benchmarking suite."""

    def __init__(self):
        self.results = {}

    def measure_time(self, func, *args, **kwargs) -> float:
        """Measure execution time of a function in seconds."""
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return elapsed, result

    def benchmark_single_request(self, job_data: Dict[str, str]) -> Dict[str, Any]:
        """Benchmark a single pricing request end-to-end."""
        session = get_session()

        # Create request
        request = JobPricingRequest(
            job_title=job_data['job_title'],
            job_description=job_data.get('job_description', ''),
            location_text=job_data.get('location_text', 'Singapore'),
            requested_by='benchmark_test',
            requestor_email='benchmark@test.com',
            status='pending',
            urgency='normal'
        )
        session.add(request)
        session.flush()

        # Measure total pricing calculation time
        pricing_service = PricingCalculationServiceV3(session)
        total_time, result = self.measure_time(
            pricing_service.calculate_pricing,
            request
        )

        session.close()

        return {
            'total_time': total_time,
            'confidence_score': result.confidence_score,
            'sources_used': len(result.source_contributions),
            'target_salary': float(result.target_salary)
        }

    def benchmark_embedding_generation(self, job_title: str) -> Dict[str, float]:
        """Benchmark embedding generation performance."""
        from src.job_pricing.services.job_matching_service import JobMatchingService
        import openai

        session = get_session()
        matching_service = JobMatchingService(session)

        # Test embedding generation
        elapsed, embedding = self.measure_time(
            matching_service.generate_query_embedding,
            job_title,
            ""
        )

        session.close()

        return {
            'embedding_generation_time': elapsed,
            'embedding_dimensions': len(embedding) if embedding else 0
        }

    def benchmark_vector_search(self, job_title: str) -> Dict[str, float]:
        """Benchmark pgvector similarity search performance."""
        session = get_session()
        matching_service = JobMatchingService(session)

        elapsed, candidates = self.measure_time(
            matching_service.find_similar_jobs,
            job_title=job_title,
            top_k=5
        )

        session.close()

        return {
            'vector_search_time': elapsed,
            'candidates_found': len(candidates) if candidates else 0
        }

    def benchmark_llm_matching(self, job_title: str, job_description: str) -> Dict[str, float]:
        """Benchmark LLM-based job matching performance."""
        session = get_session()
        matching_service = JobMatchingService(session)

        # First get embedding candidates
        candidates = matching_service.find_similar_jobs(
            job_title=job_title,
            job_description=job_description,
            top_k=5
        )

        if not candidates:
            session.close()
            return {'llm_matching_time': 0, 'match_found': False}

        # Measure LLM selection time
        elapsed, match = self.measure_time(
            matching_service._llm_select_best_match,
            job_title=job_title,
            job_description=job_description,
            candidates=candidates
        )

        session.close()

        return {
            'llm_matching_time': elapsed,
            'match_found': match is not None,
            'llm_confidence': match.get('match_score', 0) if match else 0
        }

    def benchmark_database_queries(self) -> Dict[str, float]:
        """Benchmark common database query patterns."""
        session = get_session()
        timings = {}

        try:
            # Test 1: Query Mercer job library
            from src.job_pricing.models import MercerJobLibrary
            start = time.time()
            jobs = session.query(MercerJobLibrary).limit(100).all()
            timings['query_mercer_jobs_100'] = time.time() - start
            timings['mercer_jobs_found'] = len(jobs)
        except Exception as e:
            logger.warning(f"Mercer query failed: {e}")
            timings['query_mercer_jobs_100'] = 0

        try:
            # Test 2: Query scraped jobs
            from src.job_pricing.models import ScrapedJobListing
            start = time.time()
            scraped_jobs = session.query(ScrapedJobListing).limit(100).all()
            timings['query_scraped_jobs_100'] = time.time() - start
            timings['scraped_jobs_found'] = len(scraped_jobs)
        except Exception as e:
            logger.warning(f"Scraped jobs query failed: {e}")
            timings['query_scraped_jobs_100'] = 0

        try:
            # Test 3: Query market data
            from src.job_pricing.models import MercerMarketData
            start = time.time()
            market_data = session.query(MercerMarketData).filter(
                MercerMarketData.country_code == 'SG'
            ).all()
            timings['query_market_data_sg'] = time.time() - start
            timings['market_data_records'] = len(market_data)
        except Exception as e:
            logger.warning(f"Market data query failed: {e}")
            timings['query_market_data_sg'] = 0

        try:
            # Test 4: Query pricing requests
            start = time.time()
            pricing_requests = session.query(JobPricingRequest).limit(100).all()
            timings['query_pricing_requests_100'] = time.time() - start
            timings['pricing_requests_found'] = len(pricing_requests)
        except Exception as e:
            logger.warning(f"Pricing requests query failed: {e}")
            timings['query_pricing_requests_100'] = 0

        session.close()
        return timings

    def benchmark_concurrent_requests(self, num_requests: int = 10) -> Dict[str, Any]:
        """Benchmark concurrent request processing."""
        test_jobs = [
            {
                'job_title': 'Software Engineer',
                'job_description': 'Python developer with 3-5 years experience',
                'location_text': 'Singapore'
            },
            {
                'job_title': 'Data Scientist',
                'job_description': 'ML engineer with Python and TensorFlow',
                'location_text': 'Singapore'
            },
            {
                'job_title': 'Product Manager',
                'job_description': 'Senior PM with 5+ years in tech',
                'location_text': 'Singapore'
            },
            {
                'job_title': 'HR Business Partner',
                'job_description': 'HR professional with talent management experience',
                'location_text': 'Singapore'
            },
            {
                'job_title': 'Financial Analyst',
                'job_description': 'Finance professional with Excel and SQL',
                'location_text': 'Singapore'
            }
        ]

        times = []
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(num_requests):
                job_data = test_jobs[i % len(test_jobs)]
                future = executor.submit(self.benchmark_single_request, job_data)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    result = future.result()
                    times.append(result['total_time'])
                except Exception as e:
                    logger.error(f"Concurrent request failed: {e}")

        total_time = time.time() - start_time

        if times:
            return {
                'total_time': total_time,
                'requests_completed': len(times),
                'requests_per_second': len(times) / total_time if total_time > 0 else 0,
                'avg_response_time': statistics.mean(times),
                'min_response_time': min(times),
                'max_response_time': max(times),
                'p50_response_time': statistics.median(times),
                'p95_response_time': sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0]
            }
        else:
            return {'error': 'No requests completed successfully'}

    def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark suite."""
        print("=" * 80)
        print("PERFORMANCE BENCHMARK SUITE")
        print("Dynamic Job Pricing Engine V3")
        print("=" * 80)
        print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        results = {}

        # Test 1: Single request end-to-end
        print("[1/7] Benchmarking single request (Software Engineer)...")
        results['single_request'] = self.benchmark_single_request({
            'job_title': 'Software Engineer',
            'job_description': 'Python developer with 3-5 years experience in backend development',
            'location_text': 'Singapore'
        })
        print(f"      Completed in {results['single_request']['total_time']:.2f}s")

        # Test 2: Embedding generation
        print("[2/7] Benchmarking embedding generation...")
        results['embedding_generation'] = self.benchmark_embedding_generation('Software Engineer')
        print(f"      Completed in {results['embedding_generation']['embedding_generation_time']:.3f}s")

        # Test 3: Vector search
        print("[3/7] Benchmarking vector similarity search...")
        results['vector_search'] = self.benchmark_vector_search('Software Engineer')
        print(f"      Completed in {results['vector_search']['vector_search_time']:.3f}s")

        # Test 4: LLM matching
        print("[4/7] Benchmarking LLM-based matching...")
        results['llm_matching'] = self.benchmark_llm_matching(
            'Software Engineer',
            'Python developer with backend experience'
        )
        print(f"      Completed in {results['llm_matching']['llm_matching_time']:.2f}s")

        # Test 5: Database queries
        print("[5/7] Benchmarking database queries...")
        results['database_queries'] = self.benchmark_database_queries()
        db_results = results['database_queries']
        if 'query_mercer_jobs_100' in db_results and db_results['query_mercer_jobs_100'] > 0:
            print(f"      Mercer query: {db_results['query_mercer_jobs_100']:.3f}s")
        if 'query_scraped_jobs_100' in db_results and db_results['query_scraped_jobs_100'] > 0:
            print(f"      Scraped jobs query: {db_results['query_scraped_jobs_100']:.3f}s")

        # Test 6: Concurrent requests (5 parallel)
        print("[6/7] Benchmarking concurrent requests (5 parallel)...")
        results['concurrent_5'] = self.benchmark_concurrent_requests(5)
        if 'error' not in results['concurrent_5']:
            print(f"      Throughput: {results['concurrent_5']['requests_per_second']:.1f} req/s")
            print(f"      Avg response: {results['concurrent_5']['avg_response_time']:.2f}s")

        # Test 7: Concurrent requests (10 parallel)
        print("[7/7] Benchmarking concurrent requests (10 parallel)...")
        results['concurrent_10'] = self.benchmark_concurrent_requests(10)
        if 'error' not in results['concurrent_10']:
            print(f"      Throughput: {results['concurrent_10']['requests_per_second']:.1f} req/s")
            print(f"      Avg response: {results['concurrent_10']['avg_response_time']:.2f}s")

        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return results

    def print_report(self, results: Dict[str, Any]):
        """Print formatted benchmark report."""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)

        # Component Performance
        print("\nCOMPONENT PERFORMANCE:")
        print("-" * 80)

        if 'embedding_generation' in results:
            print(f"  Embedding Generation:        {results['embedding_generation']['embedding_generation_time']*1000:.0f}ms")

        if 'vector_search' in results:
            print(f"  Vector Search (top 5):       {results['vector_search']['vector_search_time']*1000:.0f}ms")

        if 'llm_matching' in results:
            print(f"  LLM Analysis:                {results['llm_matching']['llm_matching_time']*1000:.0f}ms")

        if 'single_request' in results:
            print(f"  End-to-End Request:          {results['single_request']['total_time']*1000:.0f}ms")

        # Database Performance
        print("\nDATABASE PERFORMANCE:")
        print("-" * 80)
        if 'database_queries' in results:
            db = results['database_queries']
            if 'query_mercer_jobs_100' in db and db['query_mercer_jobs_100'] > 0:
                print(f"  Query Mercer Jobs (100):     {db['query_mercer_jobs_100']*1000:.0f}ms ({db.get('mercer_jobs_found', 0)} records)")
            if 'query_scraped_jobs_100' in db and db['query_scraped_jobs_100'] > 0:
                print(f"  Query Scraped Jobs (100):    {db['query_scraped_jobs_100']*1000:.0f}ms ({db.get('scraped_jobs_found', 0)} records)")
            if 'query_market_data_sg' in db and db['query_market_data_sg'] > 0:
                print(f"  Query Market Data (SG):      {db['query_market_data_sg']*1000:.0f}ms ({db.get('market_data_records', 0)} records)")
            if 'query_pricing_requests_100' in db and db['query_pricing_requests_100'] > 0:
                print(f"  Query Pricing Requests:      {db['query_pricing_requests_100']*1000:.0f}ms ({db.get('pricing_requests_found', 0)} records)")

        # Concurrent Performance
        print("\nCONCURRENT REQUEST PERFORMANCE:")
        print("-" * 80)

        for test_name in ['concurrent_5', 'concurrent_10']:
            if test_name in results and 'error' not in results[test_name]:
                r = results[test_name]
                num_requests = test_name.split('_')[1]
                print(f"\n  {num_requests} Parallel Requests:")
                print(f"    Throughput:                {r['requests_per_second']:.1f} req/s")
                print(f"    Avg Response Time:         {r['avg_response_time']*1000:.0f}ms")
                print(f"    Min Response Time:         {r['min_response_time']*1000:.0f}ms")
                print(f"    Max Response Time:         {r['max_response_time']*1000:.0f}ms")
                print(f"    P50 (Median):              {r['p50_response_time']*1000:.0f}ms")
                print(f"    P95:                       {r['p95_response_time']*1000:.0f}ms")

        # Quality Metrics
        print("\nQUALITY METRICS:")
        print("-" * 80)
        if 'single_request' in results:
            sr = results['single_request']
            print(f"  Confidence Score:            {sr['confidence_score']:.0f}/100")
            print(f"  Data Sources Used:           {sr['sources_used']}")
            print(f"  Target Salary:               SGD ${sr['target_salary']:,.0f}")

        # Performance Targets
        print("\nPERFORMANCE TARGETS:")
        print("-" * 80)

        targets = {
            'End-to-End Request (p95)': (3000, results.get('concurrent_10', {}).get('p95_response_time', 0) * 1000),
            'Embedding Generation': (500, results.get('embedding_generation', {}).get('embedding_generation_time', 0) * 1000),
            'Vector Search': (500, results.get('vector_search', {}).get('vector_search_time', 0) * 1000),
            'LLM Analysis': (2000, results.get('llm_matching', {}).get('llm_matching_time', 0) * 1000),
            'Throughput (req/min)': (50, results.get('concurrent_10', {}).get('requests_per_second', 0) * 60)
        }

        for metric, (target, actual) in targets.items():
            if actual > 0:
                status = "PASS" if actual <= target else "FAIL"
                print(f"  {metric:30s}: {actual:>7.0f}ms  (Target: <{target:.0f}ms)  [{status}]")

        print("\n" + "=" * 80)
        print("BENCHMARK COMPLETE")
        print("=" * 80)


if __name__ == '__main__':
    benchmark = PerformanceBenchmark()

    try:
        results = benchmark.run_full_benchmark()
        benchmark.print_report(results)

        # Save results to file
        import json
        output_file = f'benchmark_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w') as f:
            # Convert to serializable format
            serializable_results = {
                k: {k2: float(v2) if isinstance(v2, (int, float)) else v2
                    for k2, v2 in v.items()}
                for k, v in results.items()
            }
            json.dump(serializable_results, f, indent=2)

        print(f"\nResults saved to: {output_file}")

    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        print(f"\nERROR: Benchmark failed - {e}")
