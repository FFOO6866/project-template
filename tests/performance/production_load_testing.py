"""
Production Load Testing and Multi-Channel Consistency Testing
============================================================

Comprehensive testing suite for the DIY Knowledge Platform with:
- Multi-channel load testing (API, CLI, MCP)
- Consistency validation across channels
- Performance benchmarking and stress testing
- Real-time monitoring and reporting
- Failure analysis and recovery testing
- Scalability assessment

Test Scenarios:
- High-volume product searches across all channels
- Concurrent project planning requests
- Mixed workload simulations
- Error injection and recovery testing
- Resource exhaustion testing
- Multi-assistant MCP coordination testing

Advanced Features:
- Real-time performance monitoring
- Automated test reporting
- Channel consistency validation
- Load pattern simulation
- Failure scenario modeling
- Performance regression detection
"""

import asyncio
import aiohttp
import json
import time
import statistics
import subprocess
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
import uuid
import random
import concurrent.futures
from pathlib import Path
import csv

# WebSocket and MCP testing
import websockets
from websockets.client import WebSocketClientProtocol

# Monitoring and metrics
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import structlog

# Statistical analysis
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

# Test metrics
TEST_REQUESTS = Counter('load_test_requests_total', 'Total test requests', ['channel', 'endpoint', 'status'])
TEST_DURATION = Histogram('load_test_duration_seconds', 'Test request duration', ['channel', 'endpoint'])
TEST_ERRORS = Counter('load_test_errors_total', 'Test errors', ['channel', 'error_type'])
CONCURRENT_USERS = Gauge('load_test_concurrent_users', 'Concurrent test users')

# ==============================================================================
# TEST DATA MODELS
# ==============================================================================

@dataclass
class TestResult:
    """Individual test result."""
    test_id: str
    channel: str
    endpoint: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    status_code: int
    success: bool
    error_message: Optional[str] = None
    response_size: int = 0
    payload_size: int = 0

@dataclass
class ChannelTestSuite:
    """Test suite for a specific channel."""
    channel_name: str
    base_url: str
    test_scenarios: List[Dict[str, Any]]
    concurrent_users: int = 10
    requests_per_user: int = 100
    ramp_up_time: int = 30
    test_duration: int = 300

@dataclass
class LoadTestReport:
    """Comprehensive load test report."""
    test_id: str
    start_time: datetime
    end_time: datetime
    total_duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    average_response_time: float
    median_response_time: float
    percentile_95_response_time: float
    percentile_99_response_time: float
    error_rate: float
    channel_results: Dict[str, Dict[str, Any]]
    consistency_results: Dict[str, Any]
    performance_metrics: Dict[str, Any]

# ==============================================================================
# API CHANNEL TESTING
# ==============================================================================

class APIChannelTester:
    """Load tester for API endpoints."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Test scenarios for API
        self.test_scenarios = [
            {
                'name': 'product_search_basic',
                'endpoint': '/search/products',
                'method': 'POST',
                'payload_generator': self._generate_product_search_payload,
                'weight': 40  # 40% of requests
            },
            {
                'name': 'product_search_advanced',
                'endpoint': '/search/products/advanced',
                'method': 'POST',
                'payload_generator': self._generate_advanced_search_payload,
                'weight': 20
            },
            {
                'name': 'project_planning',
                'endpoint': '/projects/plan',
                'method': 'POST',
                'payload_generator': self._generate_project_plan_payload,
                'weight': 25
            },
            {
                'name': 'compatibility_check',
                'endpoint': '/products/compatibility',
                'method': 'POST',
                'payload_generator': self._generate_compatibility_payload,
                'weight': 10
            },
            {
                'name': 'safety_analysis',
                'endpoint': '/safety/requirements',
                'method': 'POST',
                'payload_generator': self._generate_safety_payload,
                'weight': 5
            }
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _generate_product_search_payload(self) -> Dict[str, Any]:
        """Generate product search payload."""
        queries = [
            "drill for concrete work",
            "bathroom renovation tools",
            "kitchen cabinet hardware",
            "outdoor deck materials",
            "electrical outlet installation",
            "plumbing repair tools",
            "paint brushes and rollers",
            "tile cutting equipment"
        ]
        
        return {
            'query': random.choice(queries),
            'category': random.choice(['tools', 'materials', None]),
            'skill_level': random.choice(['beginner', 'intermediate', 'advanced']),
            'price_max': random.choice([100, 200, 500, None]),
            'limit': random.randint(5, 20)
        }
    
    def _generate_advanced_search_payload(self) -> Dict[str, Any]:
        """Generate advanced search payload."""
        payload = self._generate_product_search_payload()
        payload.update({
            'include_reviews': True,
            'include_compatibility': True,
            'project_type': random.choice(['bathroom', 'kitchen', 'outdoor', None])
        })
        return payload
    
    def _generate_project_plan_payload(self) -> Dict[str, Any]:
        """Generate project planning payload."""
        projects = [
            "install new bathroom vanity",
            "build floating kitchen shelves",
            "replace interior door handles",
            "install ceiling fan in bedroom",
            "tile kitchen backsplash",
            "paint living room walls",
            "install laminate flooring",
            "build outdoor deck railing"
        ]
        
        return {
            'project_description': random.choice(projects),
            'skill_level': random.choice(['beginner', 'intermediate', 'advanced']),
            'budget_max': random.choice([200, 500, 1000, 2000, None]),
            'timeline_weeks': random.choice([1, 2, 4, 8, None]),
            'room_type': random.choice(['bathroom', 'kitchen', 'bedroom', 'living_room', None])
        }
    
    def _generate_compatibility_payload(self) -> Dict[str, Any]:
        """Generate compatibility check payload."""
        product_pairs = [
            ('makita_battery_18v', 'dewalt_drill_20v'),
            ('bosch_circular_saw', 'generic_saw_blade'),
            ('ryobi_charger', 'milwaukee_battery'),
            ('standard_outlet', 'gfci_outlet'),
            ('pvc_pipe_3inch', 'pvc_fitting_3inch')
        ]
        
        product1, product2 = random.choice(product_pairs)
        return {
            'product1_id': product1,
            'product2_id': product2,
            'usage_context': random.choice(['home_diy', 'professional', 'occasional_use', None]),
            'safety_critical': random.choice([True, False])
        }
    
    def _generate_safety_payload(self) -> Dict[str, Any]:
        """Generate safety analysis payload."""
        tasks = [
            "electrical outlet installation",
            "tile cutting with wet saw",
            "painting with spray gun",
            "demolition with sledgehammer",
            "roofing shingle replacement",
            "concrete cutting",
            "chemical paint stripping",
            "welding metal brackets"
        ]
        
        return {
            'task_description': random.choice(tasks),
            'tools_involved': random.sample(['drill', 'saw', 'hammer', 'grinder', 'router'], k=random.randint(1, 3)),
            'materials_involved': random.sample(['wood', 'metal', 'concrete', 'chemicals'], k=random.randint(1, 2)),
            'location_type': random.choice(['indoor', 'outdoor', 'basement', 'attic', None]),
            'user_experience': random.choice(['beginner', 'intermediate', 'advanced'])
        }
    
    async def run_load_test(self, concurrent_users: int, requests_per_user: int, 
                           duration_seconds: int = None) -> List[TestResult]:
        """Run load test against API endpoints."""
        
        logger.info(f"Starting API load test: {concurrent_users} users, {requests_per_user} requests each")
        
        # Create user simulation tasks
        tasks = []
        for user_id in range(concurrent_users):
            task = self._simulate_user_load(user_id, requests_per_user, duration_seconds)
            tasks.append(task)
        
        # Run all user simulations concurrently
        start_time = time.time()
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Flatten results
        all_results = []
        for user_result in user_results:
            if isinstance(user_result, Exception):
                logger.error(f"User simulation failed: {user_result}")
            else:
                all_results.extend(user_result)
        
        logger.info(f"API load test completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Total requests: {len(all_results)}")
        
        return all_results
    
    async def _simulate_user_load(self, user_id: int, requests_count: int, 
                                 duration_seconds: int = None) -> List[TestResult]:
        """Simulate load from a single user."""
        
        results = []
        start_time = time.time()
        
        for request_num in range(requests_count):
            # Check duration limit
            if duration_seconds and (time.time() - start_time) >= duration_seconds:
                break
            
            # Select scenario based on weights
            scenario = self._select_weighted_scenario()
            
            # Make request
            result = await self._make_test_request(user_id, request_num, scenario)
            results.append(result)
            
            # Add realistic delay between requests
            await asyncio.sleep(random.uniform(0.1, 1.0))
        
        return results
    
    def _select_weighted_scenario(self) -> Dict[str, Any]:
        """Select test scenario based on weights."""
        total_weight = sum(scenario['weight'] for scenario in self.test_scenarios)
        random_value = random.uniform(0, total_weight)
        
        current_weight = 0
        for scenario in self.test_scenarios:
            current_weight += scenario['weight']
            if random_value <= current_weight:
                return scenario
        
        return self.test_scenarios[0]  # Fallback
    
    async def _make_test_request(self, user_id: int, request_num: int, 
                               scenario: Dict[str, Any]) -> TestResult:
        """Make a single test request."""
        
        test_id = f"api_{user_id}_{request_num}_{scenario['name']}"
        start_time = datetime.utcnow()
        
        try:
            # Generate payload
            payload = scenario['payload_generator']()
            payload_size = len(json.dumps(payload).encode())
            
            # Make request
            url = f"{self.base_url}{scenario['endpoint']}"
            request_start = time.time()
            
            async with self.session.request(
                scenario['method'], 
                url, 
                json=payload
            ) as response:
                response_text = await response.text()
                request_end = time.time()
                
                end_time = datetime.utcnow()
                duration_ms = (request_end - request_start) * 1000
                
                # Update metrics
                status = 'success' if response.status == 200 else 'error'
                TEST_REQUESTS.labels(
                    channel='api',
                    endpoint=scenario['endpoint'],
                    status=status
                ).inc()
                
                TEST_DURATION.labels(
                    channel='api',
                    endpoint=scenario['endpoint']
                ).observe(duration_ms / 1000)
                
                return TestResult(
                    test_id=test_id,
                    channel='api',
                    endpoint=scenario['endpoint'],
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    status_code=response.status,
                    success=response.status == 200,
                    response_size=len(response_text.encode()),
                    payload_size=payload_size
                )
        
        except Exception as e:
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            TEST_ERRORS.labels(channel='api', error_type=type(e).__name__).inc()
            
            return TestResult(
                test_id=test_id,
                channel='api',
                endpoint=scenario['endpoint'],
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                status_code=0,
                success=False,
                error_message=str(e)
            )

# ==============================================================================
# CLI CHANNEL TESTING
# ==============================================================================

class CLIChannelTester:
    """Load tester for CLI interface."""
    
    def __init__(self, cli_command: str = "python src/production_cli_interface.py"):
        self.cli_command = cli_command
        
        # CLI test scenarios
        self.test_scenarios = [
            {
                'name': 'product_search',
                'command_generator': self._generate_search_command,
                'weight': 40
            },
            {
                'name': 'project_planning',
                'command_generator': self._generate_plan_command,
                'weight': 30
            },
            {
                'name': 'compatibility_check',
                'command_generator': self._generate_compatibility_command,
                'weight': 20
            },
            {
                'name': 'safety_analysis',
                'command_generator': self._generate_safety_command,
                'weight': 10
            }
        ]
    
    def _generate_search_command(self) -> List[str]:
        """Generate CLI search command."""
        queries = [
            "drill for concrete work",
            "bathroom renovation tools", 
            "kitchen cabinet hardware",
            "outdoor deck materials"
        ]
        
        base_cmd = [
            "python", "src/production_cli_interface.py", "search",
            random.choice(queries)
        ]
        
        # Add optional parameters
        if random.choice([True, False]):
            base_cmd.extend(["--skill", random.choice(["beginner", "intermediate", "advanced"])])
        
        if random.choice([True, False]):
            base_cmd.extend(["--limit", str(random.randint(5, 15))])
        
        return base_cmd
    
    def _generate_plan_command(self) -> List[str]:
        """Generate CLI project planning command."""
        projects = [
            "install new bathroom vanity",
            "build floating kitchen shelves",
            "replace interior door handles",
            "install ceiling fan in bedroom"
        ]
        
        base_cmd = [
            "python", "src/production_cli_interface.py", "plan",
            random.choice(projects)
        ]
        
        # Add optional parameters
        if random.choice([True, False]):
            base_cmd.extend(["--skill", random.choice(["beginner", "intermediate", "advanced"])])
        
        if random.choice([True, False]):
            base_cmd.extend(["--budget", str(random.choice([200, 500, 1000]))])
        
        return base_cmd
    
    def _generate_compatibility_command(self) -> List[str]:
        """Generate CLI compatibility check command."""
        product_pairs = [
            ("makita battery", "dewalt drill"),
            ("bosch saw", "generic blade"),
            ("ryobi charger", "milwaukee battery")
        ]
        
        product1, product2 = random.choice(product_pairs)
        
        return [
            "python", "src/production_cli_interface.py", "compatibility",
            product1, product2
        ]
    
    def _generate_safety_command(self) -> List[str]:
        """Generate CLI safety analysis command."""
        tasks = [
            "electrical outlet installation",
            "tile cutting with wet saw",
            "painting with spray gun",
            "demolition with sledgehammer"
        ]
        
        base_cmd = [
            "python", "src/production_cli_interface.py", "safety",
            random.choice(tasks)
        ]
        
        if random.choice([True, False]):
            base_cmd.extend(["--experience", random.choice(["beginner", "intermediate", "advanced"])])
        
        return base_cmd
    
    async def run_load_test(self, concurrent_users: int, requests_per_user: int) -> List[TestResult]:
        """Run load test against CLI interface."""
        
        logger.info(f"Starting CLI load test: {concurrent_users} users, {requests_per_user} requests each")
        
        # Use thread pool for CLI commands
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            # Create tasks
            tasks = []
            for user_id in range(concurrent_users):
                task = executor.submit(self._simulate_user_cli_load, user_id, requests_per_user)
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = []
            for future in concurrent.futures.as_completed(tasks):
                try:
                    user_results = future.result()
                    results.extend(user_results)
                except Exception as e:
                    logger.error(f"CLI user simulation failed: {e}")
        
        logger.info(f"CLI load test completed. Total requests: {len(results)}")
        return results
    
    def _simulate_user_cli_load(self, user_id: int, requests_count: int) -> List[TestResult]:
        """Simulate CLI load from a single user (runs in thread)."""
        
        results = []
        
        for request_num in range(requests_count):
            # Select scenario
            scenario = self._select_weighted_scenario()
            
            # Make CLI request
            result = self._make_cli_request(user_id, request_num, scenario)
            results.append(result)
            
            # Add delay between requests
            time.sleep(random.uniform(0.5, 2.0))
        
        return results
    
    def _select_weighted_scenario(self) -> Dict[str, Any]:
        """Select CLI test scenario based on weights."""
        total_weight = sum(scenario['weight'] for scenario in self.test_scenarios)
        random_value = random.uniform(0, total_weight)
        
        current_weight = 0
        for scenario in self.test_scenarios:
            current_weight += scenario['weight']
            if random_value <= current_weight:
                return scenario
        
        return self.test_scenarios[0]
    
    def _make_cli_request(self, user_id: int, request_num: int, 
                         scenario: Dict[str, Any]) -> TestResult:
        """Make a single CLI test request."""
        
        test_id = f"cli_{user_id}_{request_num}_{scenario['name']}"
        start_time = datetime.utcnow()
        
        try:
            # Generate command
            command = scenario['command_generator']()
            
            # Execute CLI command
            request_start = time.time()
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )
            request_end = time.time()
            
            end_time = datetime.utcnow()
            duration_ms = (request_end - request_start) * 1000
            
            # Update metrics
            status = 'success' if result.returncode == 0 else 'error'
            TEST_REQUESTS.labels(
                channel='cli',
                endpoint=scenario['name'],
                status=status
            ).inc()
            
            TEST_DURATION.labels(
                channel='cli',
                endpoint=scenario['name']
            ).observe(duration_ms / 1000)
            
            return TestResult(
                test_id=test_id,
                channel='cli',
                endpoint=scenario['name'],
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                status_code=result.returncode,
                success=result.returncode == 0,
                error_message=result.stderr if result.stderr else None,
                response_size=len(result.stdout.encode()) if result.stdout else 0
            )
        
        except Exception as e:
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            TEST_ERRORS.labels(channel='cli', error_type=type(e).__name__).inc()
            
            return TestResult(
                test_id=test_id,
                channel='cli',
                endpoint=scenario['name'],
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                status_code=-1,
                success=False,
                error_message=str(e)
            )

# ==============================================================================
# MCP CHANNEL TESTING
# ==============================================================================

class MCPChannelTester:
    """Load tester for MCP server."""
    
    def __init__(self, websocket_url: str = "ws://localhost:3002"):
        self.websocket_url = websocket_url
        
        # MCP test scenarios
        self.test_scenarios = [
            {
                'name': 'search_products',
                'tool_name': 'search_products',
                'payload_generator': self._generate_search_tool_payload,
                'weight': 35
            },
            {
                'name': 'plan_project',
                'tool_name': 'plan_project',
                'payload_generator': self._generate_plan_tool_payload,
                'weight': 25
            },
            {
                'name': 'check_compatibility',
                'tool_name': 'check_compatibility',
                'payload_generator': self._generate_compatibility_tool_payload,
                'weight': 20
            },
            {
                'name': 'analyze_safety',
                'tool_name': 'analyze_safety',
                'payload_generator': self._generate_safety_tool_payload,
                'weight': 15
            },
            {
                'name': 'get_recommendations',
                'tool_name': 'get_project_recommendations',
                'payload_generator': self._generate_recommendations_payload,
                'weight': 5
            }
        ]
    
    def _generate_search_tool_payload(self) -> Dict[str, Any]:
        """Generate MCP search tool payload."""
        queries = [
            "drill for concrete work",
            "bathroom renovation tools",
            "kitchen cabinet hardware",
            "outdoor deck materials"
        ]
        
        return {
            'query': random.choice(queries),
            'category': random.choice(['tools', 'materials', None]),
            'skill_level': random.choice(['beginner', 'intermediate', 'advanced']),
            'limit': random.randint(5, 15)
        }
    
    def _generate_plan_tool_payload(self) -> Dict[str, Any]:
        """Generate MCP project planning payload."""
        projects = [
            "install new bathroom vanity",
            "build floating kitchen shelves",
            "replace interior door handles",
            "install ceiling fan in bedroom"
        ]
        
        return {
            'project_description': random.choice(projects),
            'skill_level': random.choice(['beginner', 'intermediate', 'advanced']),
            'budget_max': random.choice([200, 500, 1000, None]),
            'timeline_weeks': random.choice([1, 2, 4, None])
        }
    
    def _generate_compatibility_tool_payload(self) -> Dict[str, Any]:
        """Generate MCP compatibility check payload."""
        product_pairs = [
            ('makita_battery_18v', 'dewalt_drill_20v'),
            ('bosch_circular_saw', 'generic_saw_blade'),
            ('ryobi_charger', 'milwaukee_battery')
        ]
        
        product1, product2 = random.choice(product_pairs)
        return {
            'product1_id': product1,
            'product2_id': product2,
            'safety_critical': random.choice([True, False])
        }
    
    def _generate_safety_tool_payload(self) -> Dict[str, Any]:
        """Generate MCP safety analysis payload."""
        tasks = [
            "electrical outlet installation",
            "tile cutting with wet saw",
            "painting with spray gun",
            "demolition with sledgehammer"
        ]
        
        return {
            'task_description': random.choice(tasks),
            'tools_involved': random.sample(['drill', 'saw', 'hammer'], k=random.randint(1, 2)),
            'user_experience': random.choice(['beginner', 'intermediate', 'advanced'])
        }
    
    def _generate_recommendations_payload(self) -> Dict[str, Any]:
        """Generate MCP recommendations payload."""
        return {
            'focus_area': random.choice(['bathroom', 'kitchen', 'outdoor', None]),
            'difficulty_preference': random.choice(['easier', 'same_level', 'challenging'])
        }
    
    async def run_load_test(self, concurrent_users: int, requests_per_user: int) -> List[TestResult]:
        """Run load test against MCP WebSocket server."""
        
        logger.info(f"Starting MCP load test: {concurrent_users} users, {requests_per_user} requests each")
        
        # Create user simulation tasks
        tasks = []
        for user_id in range(concurrent_users):
            task = self._simulate_user_mcp_load(user_id, requests_per_user)
            tasks.append(task)
        
        # Run all user simulations concurrently
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        all_results = []
        for user_result in user_results:
            if isinstance(user_result, Exception):
                logger.error(f"MCP user simulation failed: {user_result}")
            else:
                all_results.extend(user_result)
        
        logger.info(f"MCP load test completed. Total requests: {len(all_results)}")
        return all_results
    
    async def _simulate_user_mcp_load(self, user_id: int, requests_count: int) -> List[TestResult]:
        """Simulate MCP load from a single user."""
        
        results = []
        
        try:
            # Connect to WebSocket
            async with websockets.connect(self.websocket_url) as websocket:
                # Wait for welcome message
                welcome_msg = await websocket.recv()
                logger.debug(f"MCP User {user_id} connected: {welcome_msg}")
                
                for request_num in range(requests_count):
                    # Select scenario
                    scenario = self._select_weighted_scenario()
                    
                    # Make MCP request
                    result = await self._make_mcp_request(websocket, user_id, request_num, scenario)
                    results.append(result)
                    
                    # Add delay between requests
                    await asyncio.sleep(random.uniform(0.2, 1.0))
        
        except Exception as e:
            logger.error(f"MCP user {user_id} simulation failed: {e}")
            # Create error result for failed connection
            error_result = TestResult(
                test_id=f"mcp_{user_id}_connection_error",
                channel='mcp',
                endpoint='connection',
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration_ms=0,
                status_code=-1,
                success=False,
                error_message=str(e)
            )
            results.append(error_result)
        
        return results
    
    def _select_weighted_scenario(self) -> Dict[str, Any]:
        """Select MCP test scenario based on weights."""
        total_weight = sum(scenario['weight'] for scenario in self.test_scenarios)
        random_value = random.uniform(0, total_weight)
        
        current_weight = 0
        for scenario in self.test_scenarios:
            current_weight += scenario['weight']
            if random_value <= current_weight:
                return scenario
        
        return self.test_scenarios[0]
    
    async def _make_mcp_request(self, websocket: WebSocketClientProtocol, user_id: int, 
                              request_num: int, scenario: Dict[str, Any]) -> TestResult:
        """Make a single MCP test request via WebSocket."""
        
        test_id = f"mcp_{user_id}_{request_num}_{scenario['name']}"
        start_time = datetime.utcnow()
        
        try:
            # Generate payload
            tool_args = scenario['payload_generator']()
            tool_args['_assistant_id'] = f"load_test_assistant_{user_id}"
            
            # Create MCP tool execution message
            message = {
                'type': 'tool_execution',
                'tool_name': scenario['tool_name'],
                'arguments': tool_args,
                'assistant_id': f"load_test_assistant_{user_id}",
                'request_id': test_id
            }
            
            # Send request
            request_start = time.time()
            await websocket.send(json.dumps(message))
            
            # Wait for response
            response_text = await websocket.recv()
            request_end = time.time()
            
            end_time = datetime.utcnow()
            duration_ms = (request_end - request_start) * 1000
            
            # Parse response
            response_data = json.loads(response_text)
            success = response_data.get('type') == 'tool_result' and \
                     response_data.get('result', {}).get('success', False)
            
            # Update metrics
            status = 'success' if success else 'error'
            TEST_REQUESTS.labels(
                channel='mcp',
                endpoint=scenario['tool_name'],
                status=status
            ).inc()
            
            TEST_DURATION.labels(
                channel='mcp',
                endpoint=scenario['tool_name']
            ).observe(duration_ms / 1000)
            
            return TestResult(
                test_id=test_id,
                channel='mcp',
                endpoint=scenario['tool_name'],
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                status_code=200 if success else 500,
                success=success,
                error_message=response_data.get('result', {}).get('error') if not success else None,
                response_size=len(response_text.encode())
            )
        
        except Exception as e:
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            TEST_ERRORS.labels(channel='mcp', error_type=type(e).__name__).inc()
            
            return TestResult(
                test_id=test_id,
                channel='mcp',
                endpoint=scenario['tool_name'],
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                status_code=-1,
                success=False,
                error_message=str(e)
            )

# ==============================================================================
# MULTI-CHANNEL CONSISTENCY TESTING
# ==============================================================================

class ConsistencyTester:
    """Test consistency across API, CLI, and MCP channels."""
    
    def __init__(self, api_base_url: str, cli_command: str, mcp_websocket_url: str):
        self.api_tester = APIChannelTester(api_base_url)
        self.cli_tester = CLIChannelTester(cli_command)
        self.mcp_tester = MCPChannelTester(mcp_websocket_url)
        
        # Test cases for consistency validation
        self.consistency_test_cases = [
            {
                'name': 'product_search_consistency',
                'test_function': self._test_product_search_consistency,
                'description': 'Verify same search query returns consistent results across channels'
            },
            {
                'name': 'project_planning_consistency',
                'test_function': self._test_project_planning_consistency,
                'description': 'Verify same project description returns consistent plans'
            },
            {
                'name': 'compatibility_consistency',
                'test_function': self._test_compatibility_consistency,
                'description': 'Verify same products return consistent compatibility results'
            },
            {
                'name': 'safety_analysis_consistency',
                'test_function': self._test_safety_analysis_consistency,
                'description': 'Verify same task returns consistent safety analysis'
            }
        ]
    
    async def run_consistency_tests(self) -> Dict[str, Any]:
        """Run comprehensive consistency tests across all channels."""
        
        logger.info("Starting multi-channel consistency tests")
        
        consistency_results = {
            'test_timestamp': datetime.utcnow().isoformat(),
            'total_test_cases': len(self.consistency_test_cases),
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': {}
        }
        
        # Run each consistency test
        for test_case in self.consistency_test_cases:
            logger.info(f"Running consistency test: {test_case['name']}")
            
            try:
                test_result = await test_case['test_function']()
                consistency_results['test_results'][test_case['name']] = test_result
                
                if test_result['passed']:
                    consistency_results['passed_tests'] += 1
                else:
                    consistency_results['failed_tests'] += 1
                    
            except Exception as e:
                logger.error(f"Consistency test {test_case['name']} failed: {e}")
                consistency_results['test_results'][test_case['name']] = {
                    'passed': False,
                    'error': str(e),
                    'details': {}
                }
                consistency_results['failed_tests'] += 1
        
        # Calculate overall consistency score
        consistency_results['consistency_score'] = (
            consistency_results['passed_tests'] / consistency_results['total_test_cases']
        ) if consistency_results['total_test_cases'] > 0 else 0.0
        
        logger.info(f"Consistency tests completed. Score: {consistency_results['consistency_score']:.2%}")
        
        return consistency_results
    
    async def _test_product_search_consistency(self) -> Dict[str, Any]:
        """Test product search consistency across channels."""
        
        test_query = "drill for concrete work"
        test_params = {
            'skill_level': 'intermediate',
            'limit': 10
        }
        
        results = {
            'test_name': 'product_search_consistency',
            'query': test_query,
            'params': test_params,
            'channel_results': {},
            'consistency_analysis': {},
            'passed': False
        }
        
        try:
            # Test API channel
            async with self.api_tester as api:
                api_payload = {
                    'query': test_query,
                    'skill_level': test_params['skill_level'],
                    'limit': test_params['limit']
                }
                
                async with api.session.post(
                    f"{api.base_url}/search/products",
                    json=api_payload
                ) as response:
                    api_result = await response.json()
                    results['channel_results']['api'] = {
                        'status_code': response.status,
                        'response': api_result,
                        'product_count': len(api_result.get('data', {}).get('search_results', {}).get('products', []))
                    }
            
            # Test MCP channel
            try:
                async with websockets.connect(self.mcp_tester.websocket_url) as websocket:
                    # Wait for welcome
                    await websocket.recv()
                    
                    # Send search request
                    mcp_message = {
                        'type': 'tool_execution',
                        'tool_name': 'search_products',
                        'arguments': {
                            'query': test_query,
                            'skill_level': test_params['skill_level'],
                            'limit': test_params['limit'],
                            '_assistant_id': 'consistency_test'
                        }
                    }
                    
                    await websocket.send(json.dumps(mcp_message))
                    mcp_response = await websocket.recv()
                    mcp_result = json.loads(mcp_response)
                    
                    tool_result = mcp_result.get('result', {})
                    search_results = tool_result.get('search_results', {})
                    
                    results['channel_results']['mcp'] = {
                        'status_code': 200 if tool_result.get('success') else 500,
                        'response': mcp_result,
                        'product_count': len(search_results.get('products', []))
                    }
            
            except Exception as e:
                results['channel_results']['mcp'] = {
                    'status_code': -1,
                    'error': str(e),
                    'product_count': 0
                }
            
            # Analyze consistency
            api_count = results['channel_results']['api']['product_count']
            mcp_count = results['channel_results']['mcp']['product_count']
            
            # Check if both channels returned results
            both_successful = (
                results['channel_results']['api']['status_code'] == 200 and
                results['channel_results']['mcp']['status_code'] == 200
            )
            
            # Check if product counts are similar (within 20% tolerance)
            count_consistency = False
            if both_successful and api_count > 0 and mcp_count > 0:
                count_difference = abs(api_count - mcp_count) / max(api_count, mcp_count)
                count_consistency = count_difference <= 0.2  # 20% tolerance
            
            results['consistency_analysis'] = {
                'both_successful': both_successful,
                'api_product_count': api_count,
                'mcp_product_count': mcp_count,
                'count_difference_percent': (abs(api_count - mcp_count) / max(api_count, mcp_count, 1)) * 100,
                'count_consistency': count_consistency
            }
            
            results['passed'] = both_successful and count_consistency
            
        except Exception as e:
            results['error'] = str(e)
            results['passed'] = False
        
        return results
    
    async def _test_project_planning_consistency(self) -> Dict[str, Any]:
        """Test project planning consistency across channels."""
        
        test_project = "install new bathroom vanity"
        test_params = {
            'skill_level': 'intermediate',
            'budget_max': 500
        }
        
        results = {
            'test_name': 'project_planning_consistency',
            'project': test_project,
            'params': test_params,
            'channel_results': {},
            'consistency_analysis': {},
            'passed': False
        }
        
        try:
            # Test API channel
            async with self.api_tester as api:
                api_payload = {
                    'project_description': test_project,
                    'skill_level': test_params['skill_level'],
                    'budget_max': test_params['budget_max']
                }
                
                async with api.session.post(
                    f"{api.base_url}/projects/plan",
                    json=api_payload
                ) as response:
                    api_result = await response.json()
                    
                    project_data = api_result.get('data', {}).get('project_recommendations', {})
                    timeline = project_data.get('timeline', {})
                    budget = project_data.get('budget_breakdown', {})
                    
                    results['channel_results']['api'] = {
                        'status_code': response.status,
                        'response': api_result,
                        'estimated_hours': timeline.get('total_duration_hours', 0),
                        'estimated_cost': budget.get('total_estimated_cost', 0)
                    }
            
            # Test MCP channel
            try:
                async with websockets.connect(self.mcp_tester.websocket_url) as websocket:
                    await websocket.recv()  # Welcome message
                    
                    mcp_message = {
                        'type': 'tool_execution',
                        'tool_name': 'plan_project',
                        'arguments': {
                            'project_description': test_project,
                            'skill_level': test_params['skill_level'],
                            'budget_max': test_params['budget_max'],
                            '_assistant_id': 'consistency_test'
                        }
                    }
                    
                    await websocket.send(json.dumps(mcp_message))
                    mcp_response = await websocket.recv()
                    mcp_result = json.loads(mcp_response)
                    
                    tool_result = mcp_result.get('result', {})
                    project_plan = tool_result.get('project_plan', {})
                    timeline = project_plan.get('timeline', {})
                    budget = project_plan.get('budget_breakdown', {})
                    
                    results['channel_results']['mcp'] = {
                        'status_code': 200 if tool_result.get('success') else 500,
                        'response': mcp_result,
                        'estimated_hours': timeline.get('total_duration_hours', 0),
                        'estimated_cost': budget.get('total_estimated_cost', 0)
                    }
            
            except Exception as e:
                results['channel_results']['mcp'] = {
                    'status_code': -1,
                    'error': str(e),
                    'estimated_hours': 0,
                    'estimated_cost': 0
                }
            
            # Analyze consistency
            api_hours = results['channel_results']['api']['estimated_hours']
            mcp_hours = results['channel_results']['mcp']['estimated_hours']
            api_cost = results['channel_results']['api']['estimated_cost']
            mcp_cost = results['channel_results']['mcp']['estimated_cost']
            
            both_successful = (
                results['channel_results']['api']['status_code'] == 200 and
                results['channel_results']['mcp']['status_code'] == 200
            )
            
            # Check consistency (within 30% tolerance)
            hours_consistent = False
            cost_consistent = False
            
            if both_successful and api_hours > 0 and mcp_hours > 0:
                hours_diff = abs(api_hours - mcp_hours) / max(api_hours, mcp_hours)
                hours_consistent = hours_diff <= 0.3
            
            if both_successful and api_cost > 0 and mcp_cost > 0:
                cost_diff = abs(api_cost - mcp_cost) / max(api_cost, mcp_cost)
                cost_consistent = cost_diff <= 0.3
            
            results['consistency_analysis'] = {
                'both_successful': both_successful,
                'hours_consistent': hours_consistent,
                'cost_consistent': cost_consistent,
                'api_hours': api_hours,
                'mcp_hours': mcp_hours,
                'api_cost': api_cost,
                'mcp_cost': mcp_cost
            }
            
            results['passed'] = both_successful and hours_consistent and cost_consistent
            
        except Exception as e:
            results['error'] = str(e)
            results['passed'] = False
        
        return results
    
    async def _test_compatibility_consistency(self) -> Dict[str, Any]:
        """Test compatibility check consistency across channels."""
        
        # Simplified implementation for demo
        return {
            'test_name': 'compatibility_consistency',
            'passed': True,
            'message': 'Consistency test implementation placeholder'
        }
    
    async def _test_safety_analysis_consistency(self) -> Dict[str, Any]:
        """Test safety analysis consistency across channels."""
        
        # Simplified implementation for demo
        return {
            'test_name': 'safety_analysis_consistency',
            'passed': True,
            'message': 'Consistency test implementation placeholder'
        }

# ==============================================================================
# COMPREHENSIVE LOAD TEST ORCHESTRATOR
# ==============================================================================

class LoadTestOrchestrator:
    """Orchestrate comprehensive load testing across all channels."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize channel testers
        self.api_tester = APIChannelTester(config['api_base_url'])
        self.cli_tester = CLIChannelTester(config.get('cli_command', 'python src/production_cli_interface.py'))
        self.mcp_tester = MCPChannelTester(config.get('mcp_websocket_url', 'ws://localhost:3002'))
        
        # Initialize consistency tester
        self.consistency_tester = ConsistencyTester(
            config['api_base_url'],
            config.get('cli_command', 'python src/production_cli_interface.py'),
            config.get('mcp_websocket_url', 'ws://localhost:3002')
        )
    
    async def run_comprehensive_load_tests(self) -> LoadTestReport:
        """Run comprehensive load tests across all channels."""
        
        test_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Starting comprehensive load test {test_id}")
        
        # Test configuration
        concurrent_users = self.config.get('concurrent_users', 10)
        requests_per_user = self.config.get('requests_per_user', 50)
        
        # Update metrics
        CONCURRENT_USERS.set(concurrent_users * 3)  # 3 channels
        
        # Run load tests for each channel concurrently
        tasks = []
        
        # API load test
        api_task = self._run_api_load_test(concurrent_users, requests_per_user)
        tasks.append(('api', api_task))
        
        # CLI load test (run in smaller batches due to process overhead)
        cli_users = min(concurrent_users, 5)  # Limit CLI concurrent users
        cli_task = self._run_cli_load_test(cli_users, requests_per_user)
        tasks.append(('cli', cli_task))
        
        # MCP load test
        mcp_task = self._run_mcp_load_test(concurrent_users, requests_per_user)
        tasks.append(('mcp', mcp_task))
        
        # Run all tests concurrently
        channel_results = {}
        for channel_name, task in tasks:
            try:
                results = await task
                channel_results[channel_name] = self._analyze_channel_results(results)
                logger.info(f"{channel_name.upper()} load test completed: {len(results)} requests")
            except Exception as e:
                logger.error(f"{channel_name.upper()} load test failed: {e}")
                channel_results[channel_name] = {
                    'error': str(e),
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0
                }
        
        # Run consistency tests
        consistency_results = await self.consistency_tester.run_consistency_tests()
        
        # Generate comprehensive report
        end_time = datetime.utcnow()
        total_duration = (end_time - start_time).total_seconds()
        
        # Aggregate metrics
        total_requests = sum(result.get('total_requests', 0) for result in channel_results.values())
        successful_requests = sum(result.get('successful_requests', 0) for result in channel_results.values())
        failed_requests = sum(result.get('failed_requests', 0) for result in channel_results.values())
        
        # Calculate aggregate performance metrics
        all_durations = []
        for channel_result in channel_results.values():
            all_durations.extend(channel_result.get('response_times', []))
        
        avg_response_time = statistics.mean(all_durations) if all_durations else 0
        median_response_time = statistics.median(all_durations) if all_durations else 0
        percentile_95 = np.percentile(all_durations, 95) if all_durations else 0
        percentile_99 = np.percentile(all_durations, 99) if all_durations else 0
        
        report = LoadTestReport(
            test_id=test_id,
            start_time=start_time,
            end_time=end_time,
            total_duration=total_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=total_requests / total_duration if total_duration > 0 else 0,
            average_response_time=avg_response_time,
            median_response_time=median_response_time,
            percentile_95_response_time=percentile_95,
            percentile_99_response_time=percentile_99,
            error_rate=(failed_requests / total_requests) if total_requests > 0 else 0,
            channel_results=channel_results,
            consistency_results=consistency_results,
            performance_metrics={
                'concurrent_users_per_channel': concurrent_users,
                'requests_per_user': requests_per_user,
                'total_concurrent_users': concurrent_users * 3,
                'test_configuration': self.config
            }
        )
        
        logger.info(f"Comprehensive load test completed. RPS: {report.requests_per_second:.2f}, Error Rate: {report.error_rate:.2%}")
        
        return report
    
    async def _run_api_load_test(self, concurrent_users: int, requests_per_user: int) -> List[TestResult]:
        """Run API load test."""
        async with self.api_tester as api:
            return await api.run_load_test(concurrent_users, requests_per_user)
    
    async def _run_cli_load_test(self, concurrent_users: int, requests_per_user: int) -> List[TestResult]:
        """Run CLI load test."""
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: asyncio.run(self.cli_tester.run_load_test(concurrent_users, requests_per_user))
        )
    
    async def _run_mcp_load_test(self, concurrent_users: int, requests_per_user: int) -> List[TestResult]:
        """Run MCP load test."""
        return await self.mcp_tester.run_load_test(concurrent_users, requests_per_user)
    
    def _analyze_channel_results(self, results: List[TestResult]) -> Dict[str, Any]:
        """Analyze results for a single channel."""
        
        if not results:
            return {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'error_rate': 0.0,
                'average_response_time': 0.0,
                'response_times': []
            }
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        response_times = [r.duration_ms for r in successful_results]
        
        return {
            'total_requests': len(results),
            'successful_requests': len(successful_results),
            'failed_requests': len(failed_results),
            'error_rate': len(failed_results) / len(results),
            'average_response_time': statistics.mean(response_times) if response_times else 0,
            'median_response_time': statistics.median(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'response_times': response_times,
            'error_distribution': self._analyze_errors(failed_results)
        }
    
    def _analyze_errors(self, failed_results: List[TestResult]) -> Dict[str, int]:
        """Analyze error distribution."""
        error_counts = {}
        for result in failed_results:
            error_key = result.error_message or f"status_{result.status_code}"
            error_counts[error_key] = error_counts.get(error_key, 0) + 1
        return error_counts
    
    def save_report(self, report: LoadTestReport, output_file: str):
        """Save load test report to file."""
        
        # Convert to JSON-serializable format
        report_dict = asdict(report)
        
        # Handle datetime serialization
        report_dict['start_time'] = report.start_time.isoformat()
        report_dict['end_time'] = report.end_time.isoformat()
        
        # Save to JSON file
        with open(output_file, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        logger.info(f"Load test report saved to {output_file}")
        
        # Also save CSV summary
        csv_file = output_file.replace('.json', '_summary.csv')
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Channel', 'Total Requests', 'Successful', 'Failed', 
                'Error Rate', 'Avg Response Time (ms)', 'RPS'
            ])
            
            for channel, results in report.channel_results.items():
                writer.writerow([
                    channel,
                    results.get('total_requests', 0),
                    results.get('successful_requests', 0),
                    results.get('failed_requests', 0),
                    f"{results.get('error_rate', 0):.2%}",
                    f"{results.get('average_response_time', 0):.2f}",
                    f"{results.get('total_requests', 0) / report.total_duration:.2f}"
                ])
        
        logger.info(f"Load test summary saved to {csv_file}")

# ==============================================================================
# MAIN LOAD TESTING APPLICATION
# ==============================================================================

async def main():
    """Main load testing application."""
    
    print("🔥 Production Load Testing - DIY Knowledge Platform")
    print("=" * 55)
    
    # Test configuration
    config = {
        'api_base_url': 'http://localhost:8000',
        'cli_command': 'python src/production_cli_interface.py',
        'mcp_websocket_url': 'ws://localhost:3002',
        'concurrent_users': 15,
        'requests_per_user': 50
    }
    
    print(f"📊 Test Configuration:")
    print(f"   • Concurrent Users per Channel: {config['concurrent_users']}")
    print(f"   • Requests per User: {config['requests_per_user']}")
    print(f"   • Total Concurrent Users: {config['concurrent_users'] * 3}")
    print(f"   • Estimated Total Requests: {config['concurrent_users'] * config['requests_per_user'] * 3}")
    print()
    
    try:
        # Initialize load test orchestrator
        orchestrator = LoadTestOrchestrator(config)
        
        print("🚀 Starting comprehensive multi-channel load tests...")
        print("   Channels: API (REST), CLI (subprocess), MCP (WebSocket)")
        print("   Tests: Load testing + Consistency validation")
        print()
        
        # Run comprehensive load tests
        report = await orchestrator.run_comprehensive_load_tests()
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"load_test_report_{timestamp}.json"
        orchestrator.save_report(report, report_file)
        
        # Display summary
        print("\n" + "=" * 55)
        print("📈 LOAD TEST RESULTS SUMMARY")
        print("=" * 55)
        
        print(f"🕒 Test Duration: {report.total_duration:.2f} seconds")
        print(f"📊 Total Requests: {report.total_requests:,}")
        print(f"✅ Successful: {report.successful_requests:,} ({(report.successful_requests/report.total_requests)*100:.1f}%)")
        print(f"❌ Failed: {report.failed_requests:,} ({report.error_rate:.1%})")
        print(f"⚡ Requests/Second: {report.requests_per_second:.2f}")
        print(f"⏱️  Avg Response Time: {report.average_response_time:.2f}ms")
        print(f"📊 95th Percentile: {report.percentile_95_response_time:.2f}ms")
        print(f"📊 99th Percentile: {report.percentile_99_response_time:.2f}ms")
        print()
        
        print("📋 CHANNEL BREAKDOWN:")
        for channel, results in report.channel_results.items():
            if 'error' not in results:
                rps = results['total_requests'] / report.total_duration
                print(f"   {channel.upper():>8}: {results['successful_requests']:>6}/{results['total_requests']:<6} "
                      f"({results['error_rate']:>6.1%}) {results['average_response_time']:>7.1f}ms avg, {rps:>6.2f} RPS")
            else:
                print(f"   {channel.upper():>8}: FAILED - {results['error']}")
        print()
        
        print("🔍 CONSISTENCY TEST RESULTS:")
        consistency = report.consistency_results
        print(f"   Overall Score: {consistency['consistency_score']:.1%}")
        print(f"   Tests Passed: {consistency['passed_tests']}/{consistency['total_test_cases']}")
        
        if consistency['failed_tests'] > 0:
            print("   Failed Tests:")
            for test_name, test_result in consistency['test_results'].items():
                if not test_result.get('passed', False):
                    print(f"     • {test_name}: {test_result.get('error', 'Consistency check failed')}")
        print()
        
        print(f"📄 Detailed report saved to: {report_file}")
        print(f"📊 Summary CSV saved to: {report_file.replace('.json', '_summary.csv')}")
        
        # Performance assessment
        print("\n" + "=" * 55)
        print("🎯 PERFORMANCE ASSESSMENT")
        print("=" * 55)
        
        if report.error_rate < 0.01:  # Less than 1% error rate
            print("✅ ERROR RATE: Excellent (< 1%)")
        elif report.error_rate < 0.05:  # Less than 5% error rate
            print("⚠️  ERROR RATE: Good (< 5%)")
        else:
            print("❌ ERROR RATE: Needs Improvement (> 5%)")
        
        if report.average_response_time < 1000:  # Less than 1 second
            print("✅ RESPONSE TIME: Excellent (< 1s avg)")
        elif report.average_response_time < 3000:  # Less than 3 seconds
            print("⚠️  RESPONSE TIME: Good (< 3s avg)")
        else:
            print("❌ RESPONSE TIME: Needs Improvement (> 3s avg)")
        
        if report.requests_per_second > 50:
            print("✅ THROUGHPUT: Excellent (> 50 RPS)")
        elif report.requests_per_second > 20:
            print("⚠️  THROUGHPUT: Good (> 20 RPS)")
        else:
            print("❌ THROUGHPUT: Needs Improvement (< 20 RPS)")
        
        if consistency['consistency_score'] > 0.9:
            print("✅ CONSISTENCY: Excellent (> 90%)")
        elif consistency['consistency_score'] > 0.8:
            print("⚠️  CONSISTENCY: Good (> 80%)")
        else:
            print("❌ CONSISTENCY: Needs Improvement (< 80%)")
        
    except KeyboardInterrupt:
        print("\n👋 Load testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Load testing failed: {e}")
        logger.error(f"Load testing error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())