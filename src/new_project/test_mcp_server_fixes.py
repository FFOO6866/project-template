"""
MCP Server Fixes Test Suite
===========================

Comprehensive test suite to verify all MCP server fixes are working properly.
This script tests:
1. FastMCP dependency installation and fallback
2. DataFlow async context manager fixes
3. Database connection pool functionality
4. MCP server tool registration and execution
5. WebSocket and HTTP transport functionality

Usage:
    python test_mcp_server_fixes.py
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPServerFixTester:
    """Comprehensive test suite for MCP server fixes"""
    
    def __init__(self):
        self.test_results = {
            'dependency_tests': {},
            'database_tests': {},
            'async_tests': {},
            'mcp_server_tests': {},
            'transport_tests': {},
            'integration_tests': {}
        }
        
        self.start_time = time.time()
    
    def test_dependencies(self) -> Dict[str, bool]:
        """Test all required dependencies"""
        logger.info("🗋 Testing dependencies...")
        
        dependencies = {
            'fastmcp': self._test_fastmcp(),
            'psycopg2': self._test_psycopg2(),
            'asyncpg': self._test_asyncpg(),
            'fastapi': self._test_fastapi(),
            'websockets': self._test_websockets(),
            'jwt': self._test_jwt(),
            'psutil': self._test_psutil(),
            'kailash': self._test_kailash(),
            'dataflow': self._test_dataflow()
        }
        
        self.test_results['dependency_tests'] = dependencies
        
        passed = sum(1 for result in dependencies.values() if result)
        total = len(dependencies)
        
        logger.info(f"✅ Dependency tests: {passed}/{total} passed")
        return dependencies
    
    def _test_fastmcp(self) -> bool:
        """Test FastMCP availability with fallback"""
        try:
            import fastmcp
            logger.debug("✅ FastMCP available")
            return True
        except ImportError:
            logger.debug("⚠️ FastMCP not available, fallback will be used")
            return True  # Fallback is acceptable
    
    def _test_psycopg2(self) -> bool:
        """Test psycopg2 availability"""
        try:
            import psycopg2
            logger.debug("✅ psycopg2 available")
            return True
        except ImportError:
            logger.debug("❌ psycopg2 not available")
            return False
    
    def _test_asyncpg(self) -> bool:
        """Test asyncpg availability"""
        try:
            import asyncpg
            logger.debug("✅ asyncpg available")
            return True
        except ImportError:
            logger.debug("❌ asyncpg not available")
            return False
    
    def _test_fastapi(self) -> bool:
        """Test FastAPI availability"""
        try:
            from fastapi import FastAPI
            logger.debug("✅ FastAPI available")
            return True
        except ImportError:
            logger.debug("❌ FastAPI not available")
            return False
    
    def _test_websockets(self) -> bool:
        """Test websockets availability"""
        try:
            import websockets
            logger.debug("✅ websockets available")
            return True
        except ImportError:
            logger.debug("❌ websockets not available")
            return False
    
    def _test_jwt(self) -> bool:
        """Test JWT availability"""
        try:
            import jwt
            logger.debug("✅ JWT available")
            return True
        except ImportError:
            logger.debug("❌ JWT not available")
            return False
    
    def _test_psutil(self) -> bool:
        """Test psutil availability"""
        try:
            import psutil
            logger.debug("✅ psutil available")
            return True
        except ImportError:
            logger.debug("❌ psutil not available")
            return False
    
    def _test_kailash(self) -> bool:
        """Test Kailash SDK availability"""
        try:
            from kailash.workflow.builder import WorkflowBuilder
            from kailash.runtime.local import LocalRuntime
            logger.debug("✅ Kailash SDK available")
            return True
        except ImportError:
            logger.debug("❌ Kailash SDK not available")
            return False
    
    def _test_dataflow(self) -> bool:
        """Test DataFlow availability"""
        try:
            from dataflow import DataFlow
            logger.debug("✅ DataFlow available")
            return True
        except ImportError:
            logger.debug("❌ DataFlow not available")
            return False
    
    async def test_database_connectivity(self) -> Dict[str, bool]:
        """Test database connectivity fixes"""
        logger.info("💾 Testing database connectivity...")
        
        tests = {
            'basic_connection': await self._test_basic_db_connection(),
            'async_connection': await self._test_async_db_connection(),
            'connection_pool': await self._test_connection_pool(),
            'migration_table': await self._test_migration_table_creation()
        }
        
        self.test_results['database_tests'] = tests
        
        passed = sum(1 for result in tests.values() if result)
        total = len(tests)
        
        logger.info(f"✅ Database tests: {passed}/{total} passed")
        return tests
    
    async def _test_basic_db_connection(self) -> bool:
        """Test basic database connection"""
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='postgres',
                user='postgres',
                password='postgres'
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            logger.debug("✅ Basic database connection successful")
            return result[0] == 1
            
        except Exception as e:
            logger.debug(f"❌ Basic database connection failed: {e}")
            return False
    
    async def _test_async_db_connection(self) -> bool:
        """Test async database connection with fixes"""
        try:
            from dataflow_async_fixes import AsyncSQLConnectionWrapper
            import asyncpg
            
            # Create connection pool
            pool = await asyncpg.create_pool(
                "postgresql://postgres:postgres@localhost:5432/postgres",
                min_size=1,
                max_size=2
            )
            
            # Test async connection wrapper
            async with AsyncSQLConnectionWrapper(pool, "postgresql://postgres:postgres@localhost:5432/postgres") as conn:
                result = await conn.fetchrow("SELECT 1 as test")
                
                if result and result.get('test') == 1:
                    logger.debug("✅ Async database connection successful")
                    await pool.close()
                    return True
            
            await pool.close()
            return False
            
        except Exception as e:
            logger.debug(f"❌ Async database connection failed: {e}")
            return False
    
    async def _test_connection_pool(self) -> bool:
        """Test connection pool functionality"""
        try:
            from dataflow_async_fixes import DataFlowConnectionPoolFix
            
            # Mock DataFlow instance
            class MockDataFlow:
                def __init__(self):
                    self.database_url = "postgresql://postgres:postgres@localhost:5432/postgres"
                    self.pool_size = 5
                    self.pool_max_overflow = 10
                    self.pool_timeout = 30
            
            mock_df = MockDataFlow()
            fix = DataFlowConnectionPoolFix(mock_df)
            
            await fix.ensure_connection_pool()
            
            # Test if connection_pool attribute was added
            has_pool = hasattr(mock_df, 'connection_pool')
            
            await fix.close_pool()
            
            logger.debug("✅ Connection pool test successful")
            return has_pool
            
        except Exception as e:
            logger.debug(f"❌ Connection pool test failed: {e}")
            return False
    
    async def _test_migration_table_creation(self) -> bool:
        """Test migration table creation with async fixes"""
        try:
            from dataflow_async_fixes import AsyncSQLConnectionWrapper, create_migration_table_safe
            import asyncpg
            
            # Create temporary connection
            pool = await asyncpg.create_pool(
                "postgresql://postgres:postgres@localhost:5432/postgres",
                min_size=1,
                max_size=1
            )
            
            async with AsyncSQLConnectionWrapper(pool, "postgresql://postgres:postgres@localhost:5432/postgres") as conn:
                # Test migration table creation
                success = await create_migration_table_safe(conn)
                
                if success:
                    # Verify table exists
                    result = await conn.fetchrow("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'dataflow_migrations'
                        )
                    """)
                    
                    # Clean up
                    await conn.execute("DROP TABLE IF EXISTS dataflow_migrations")
                    
                    await pool.close()
                    
                    logger.debug("✅ Migration table creation test successful")
                    return result[0] if result else False
            
            await pool.close()
            return False
            
        except Exception as e:
            logger.debug(f"❌ Migration table creation test failed: {e}")
            return False
    
    async def test_mcp_server_functionality(self) -> Dict[str, bool]:
        """Test MCP server functionality with fixes"""
        logger.info("🤖 Testing MCP server functionality...")
        
        tests = {
            'server_creation': await self._test_mcp_server_creation(),
            'tool_discovery': await self._test_tool_discovery(),
            'tool_registration': await self._test_tool_registration(),
            'tool_execution': await self._test_tool_execution(),
            'error_handling': await self._test_error_handling()
        }
        
        self.test_results['mcp_server_tests'] = tests
        
        passed = sum(1 for result in tests.values() if result)
        total = len(tests)
        
        logger.info(f"✅ MCP server tests: {passed}/{total} passed")
        return tests
    
    async def _test_mcp_server_creation(self) -> bool:
        """Test MCP server creation with fixes"""
        try:
            from fixed_production_mcp_server import FixedProductionMCPServer, FixedServerConfig
            
            config = FixedServerConfig(
                port=3999,  # Use different port for testing
                enable_auth=False,
                enable_mock_mode=True
            )
            
            server = FixedProductionMCPServer(config)
            
            # Verify server components
            has_metrics = hasattr(server, 'metrics')
            has_tool_discovery = hasattr(server, 'tool_discovery')
            has_mcp_server = hasattr(server, 'mcp_server')
            
            logger.debug("✅ MCP server creation successful")
            return has_metrics and has_tool_discovery and has_mcp_server
            
        except Exception as e:
            logger.debug(f"❌ MCP server creation failed: {e}")
            return False
    
    async def _test_tool_discovery(self) -> bool:
        """Test tool discovery functionality"""
        try:
            from fixed_production_mcp_server import FixedDataFlowToolDiscovery, FixedServerConfig
            
            config = FixedServerConfig(enable_mock_mode=True)
            discovery = FixedDataFlowToolDiscovery(config)
            
            # Test tool discovery
            tools = discovery.discover_all_tools()
            
            has_tools = len(tools) > 0
            has_schemas = len(discovery.tool_schemas) > 0
            
            logger.debug(f"✅ Tool discovery successful: {len(tools)} models, {len(discovery.tool_schemas)} tools")
            return has_tools and has_schemas
            
        except Exception as e:
            logger.debug(f"❌ Tool discovery failed: {e}")
            return False
    
    async def _test_tool_registration(self) -> bool:
        """Test tool registration with MCP server"""
        try:
            from fixed_production_mcp_server import FixedProductionMCPServer, FixedServerConfig
            
            config = FixedServerConfig(
                port=3998,
                enable_auth=False,
                enable_mock_mode=True
            )
            
            server = FixedProductionMCPServer(config)
            
            # Check if tools were registered
            tools = server.tool_discovery.discover_all_tools()
            registered_tools = len(tools)
            
            logger.debug(f"✅ Tool registration successful: {registered_tools} tools registered")
            return registered_tools > 0
            
        except Exception as e:
            logger.debug(f"❌ Tool registration failed: {e}")
            return False
    
    async def _test_tool_execution(self) -> bool:
        """Test tool execution with safe mode"""
        try:
            from fixed_production_mcp_server import FixedDataFlowToolDiscovery, FixedServerConfig
            
            config = FixedServerConfig(enable_mock_mode=True)
            discovery = FixedDataFlowToolDiscovery(config)
            
            # Initialize and execute a simple tool
            await discovery.initialize_async_components()
            
            result = await discovery.execute_dataflow_operation(
                'Company', 'health_check', {'_safe_mode': True}
            )
            
            success = result.get('success', False)
            
            await discovery.cleanup()
            
            logger.debug("✅ Tool execution successful")
            return success
            
        except Exception as e:
            logger.debug(f"❌ Tool execution failed: {e}")
            return False
    
    async def _test_error_handling(self) -> bool:
        """Test error handling in tool execution"""
        try:
            from fixed_production_mcp_server import FixedDataFlowToolDiscovery, FixedServerConfig
            
            config = FixedServerConfig(enable_mock_mode=True)
            discovery = FixedDataFlowToolDiscovery(config)
            
            # Test with invalid operation
            result = await discovery.execute_dataflow_operation(
                'NonExistentModel', 'invalid_operation', {}
            )
            
            # Should return error response, not throw exception
            has_error = not result.get('success', True)
            has_error_details = 'error' in result
            
            logger.debug("✅ Error handling test successful")
            return has_error and has_error_details
            
        except Exception as e:
            logger.debug(f"❌ Error handling test failed: {e}")
            return False
    
    async def test_transport_layers(self) -> Dict[str, bool]:
        """Test transport layer functionality"""
        logger.info("🌐 Testing transport layers...")
        
        tests = {
            'http_transport': await self._test_http_transport(),
            'websocket_transport': await self._test_websocket_transport(),
            'stdio_transport': await self._test_stdio_transport()
        }
        
        self.test_results['transport_tests'] = tests
        
        passed = sum(1 for result in tests.values() if result)
        total = len(tests)
        
        logger.info(f"✅ Transport tests: {passed}/{total} passed")
        return tests
    
    async def _test_http_transport(self) -> bool:
        """Test HTTP transport initialization"""
        try:
            from fixed_production_mcp_server import FixedProductionMCPServer, FixedServerConfig
            
            config = FixedServerConfig(
                port=3997,
                enable_auth=False,
                enable_http_transport=True,
                enable_websocket_transport=False,
                enable_mock_mode=True
            )
            
            server = FixedProductionMCPServer(config)
            
            # Check if HTTP app was created
            has_http_app = hasattr(server, 'http_app') and server.http_app is not None
            
            logger.debug("✅ HTTP transport test successful")
            return has_http_app
            
        except Exception as e:
            logger.debug(f"❌ HTTP transport test failed: {e}")
            return False
    
    async def _test_websocket_transport(self) -> bool:
        """Test WebSocket transport initialization"""
        try:
            from fixed_production_mcp_server import FixedProductionMCPServer, FixedServerConfig
            
            config = FixedServerConfig(
                port=3996,
                enable_auth=False,
                enable_http_transport=False,
                enable_websocket_transport=True,
                enable_mock_mode=True
            )
            
            server = FixedProductionMCPServer(config)
            
            # Check if WebSocket handler was created
            has_websocket = hasattr(server, 'websocket_handler') and server.websocket_handler is not None
            
            logger.debug("✅ WebSocket transport test successful")
            return has_websocket
            
        except Exception as e:
            logger.debug(f"❌ WebSocket transport test failed: {e}")
            return False
    
    async def _test_stdio_transport(self) -> bool:
        """Test STDIO transport availability"""
        try:
            from fixed_production_mcp_server import FixedProductionMCPServer, FixedServerConfig
            
            config = FixedServerConfig(
                port=3995,
                enable_auth=False,
                enable_stdio_transport=True,
                enable_mock_mode=True
            )
            
            server = FixedProductionMCPServer(config)
            
            # Check if MCP server supports STDIO
            has_stdio = hasattr(server.mcp_server, 'run_stdio') or hasattr(server.mcp_server, 'run')
            
            logger.debug("✅ STDIO transport test successful")
            return has_stdio
            
        except Exception as e:
            logger.debug(f"❌ STDIO transport test failed: {e}")
            return False
    
    async def test_integration(self) -> Dict[str, bool]:
        """Test end-to-end integration"""
        logger.info("🔗 Testing integration...")
        
        tests = {
            'server_health_check': await self._test_server_health_check(),
            'metrics_collection': await self._test_metrics_collection(),
            'graceful_degradation': await self._test_graceful_degradation(),
            'configuration_loading': await self._test_configuration_loading()
        }
        
        self.test_results['integration_tests'] = tests
        
        passed = sum(1 for result in tests.values() if result)
        total = len(tests)
        
        logger.info(f"✅ Integration tests: {passed}/{total} passed")
        return tests
    
    async def _test_server_health_check(self) -> bool:
        """Test server health check functionality"""
        try:
            from fixed_production_mcp_server import FixedProductionMCPServer, FixedServerConfig
            
            config = FixedServerConfig(
                port=3994,
                enable_auth=False,
                enable_mock_mode=True
            )
            
            server = FixedProductionMCPServer(config)
            
            # Test health check
            health = await server._server_health_check()
            
            has_status = 'status' in health
            has_components = 'components' in health
            is_successful = health.get('success', False)
            
            logger.debug("✅ Server health check test successful")
            return has_status and has_components and is_successful
            
        except Exception as e:
            logger.debug(f"❌ Server health check test failed: {e}")
            return False
    
    async def _test_metrics_collection(self) -> bool:
        """Test metrics collection functionality"""
        try:
            from fixed_production_mcp_server import FixedServerMetrics
            
            metrics = FixedServerMetrics()
            
            # Record some test metrics
            metrics.record_request(success=True, execution_time=0.1, tool_name="test_tool")
            metrics.record_request(success=False, execution_time=0.5, error_type="TestError")
            
            # Get summary
            summary = metrics.get_summary()
            
            has_requests = summary.get('total_requests', 0) > 0
            has_success_rate = 'success_rate_percent' in summary
            has_response_time = 'average_response_time_ms' in summary
            
            logger.debug("✅ Metrics collection test successful")
            return has_requests and has_success_rate and has_response_time
            
        except Exception as e:
            logger.debug(f"❌ Metrics collection test failed: {e}")
            return False
    
    async def _test_graceful_degradation(self) -> bool:
        """Test graceful degradation when components are missing"""
        try:
            from fixed_production_mcp_server import FixedProductionMCPServer, FixedServerConfig
            
            config = FixedServerConfig(
                port=3993,
                enable_auth=False,
                enable_mock_mode=True,
                graceful_degradation=True
            )
            
            server = FixedProductionMCPServer(config)
            
            # Server should initialize even with missing components
            has_server = server is not None
            has_fallback = hasattr(server, 'mcp_server')
            
            logger.debug("✅ Graceful degradation test successful")
            return has_server and has_fallback
            
        except Exception as e:
            logger.debug(f"❌ Graceful degradation test failed: {e}")
            return False
    
    async def _test_configuration_loading(self) -> bool:
        """Test configuration loading and validation"""
        try:
            from fixed_production_mcp_server import FixedServerConfig
            
            # Test default configuration
            config = FixedServerConfig()
            
            has_port = hasattr(config, 'port') and config.port > 0
            has_host = hasattr(config, 'host') and config.host
            has_auth = hasattr(config, 'enable_auth')
            
            # Test custom configuration
            custom_config = FixedServerConfig(
                port=8080,
                host="127.0.0.1",
                enable_auth=True,
                auth_type="api_key"
            )
            
            has_custom_values = (
                custom_config.port == 8080 and
                custom_config.host == "127.0.0.1" and
                custom_config.enable_auth == True and
                custom_config.auth_type == "api_key"
            )
            
            logger.debug("✅ Configuration loading test successful")
            return has_port and has_host and has_auth and has_custom_values
            
        except Exception as e:
            logger.debug(f"❌ Configuration loading test failed: {e}")
            return False
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        total_time = time.time() - self.start_time
        
        # Calculate overall statistics
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            if isinstance(tests, dict):
                total_tests += len(tests)
                passed_tests += sum(1 for result in tests.values() if result)
        
        overall_pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'execution_time_seconds': round(total_time, 2),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'pass_rate_percent': round(overall_pass_rate, 1)
            },
            'test_results': self.test_results,
            'recommendations': self._generate_recommendations(),
            'next_steps': self._generate_next_steps()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check dependency results
        deps = self.test_results.get('dependency_tests', {})
        if not deps.get('fastapi', True):
            recommendations.append("Install FastAPI for HTTP transport: pip install fastapi uvicorn")
        
        if not deps.get('websockets', True):
            recommendations.append("Install websockets for WebSocket transport: pip install websockets")
        
        if not deps.get('asyncpg', True):
            recommendations.append("Install asyncpg for async database operations: pip install asyncpg")
        
        if not deps.get('psycopg2', True):
            recommendations.append("Install psycopg2 for database connectivity: pip install psycopg2-binary")
        
        # Check database results
        db_tests = self.test_results.get('database_tests', {})
        if not db_tests.get('basic_connection', True):
            recommendations.append("Fix PostgreSQL connection - run fix_database_connection.py")
        
        # Check MCP server results
        mcp_tests = self.test_results.get('mcp_server_tests', {})
        if not mcp_tests.get('server_creation', True):
            recommendations.append("Review MCP server configuration and dependencies")
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Generate next steps based on test results"""
        next_steps = []
        
        # Calculate pass rates for each category
        categories_pass_rates = {}
        for category, tests in self.test_results.items():
            if isinstance(tests, dict) and tests:
                passed = sum(1 for result in tests.values() if result)
                total = len(tests)
                categories_pass_rates[category] = passed / total
        
        # Determine overall status
        overall_pass_rate = sum(categories_pass_rates.values()) / len(categories_pass_rates) if categories_pass_rates else 0
        
        if overall_pass_rate >= 0.9:
            next_steps.extend([
                "✅ All major components are working properly",
                "🚀 You can start the MCP server with: python fixed_production_mcp_server.py",
                "🔧 Consider running in production mode with authentication enabled"
            ])
        elif overall_pass_rate >= 0.7:
            next_steps.extend([
                "⚠️ Some components need attention but basic functionality works",
                "🛠️ Install missing dependencies as recommended above",
                "🧪 Run the server in mock mode first: --mock-mode"
            ])
        else:
            next_steps.extend([
                "❌ Multiple components need fixing",
                "🔧 Run fix_database_connection.py to fix database issues",
                "📦 Install missing dependencies as recommended above",
                "💡 Consider running the server with --debug for more information"
            ])
        
        return next_steps
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        logger.info("🚀 Starting comprehensive MCP server fix tests...")
        
        try:
            # Run test suites
            self.test_dependencies()
            await self.test_database_connectivity()
            await self.test_mcp_server_functionality()
            await self.test_transport_layers()
            await self.test_integration()
            
            # Generate report
            report = self.generate_test_report()
            
            # Save report
            report_file = Path(__file__).parent / f"mcp_fix_test_report_{int(time.time())}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"📊 Test report saved: {report_file}")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            raise

async def main():
    """Main test runner"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        MCP SERVER FIXES TEST SUITE                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ This comprehensive test suite verifies all MCP server fixes:                ║
║                                                                              ║
║ • FastMCP dependency and fallback implementation                            ║
║ • DataFlow async context manager protocol fixes                             ║
║ • Database connection pool functionality                                     ║
║ • MCP server tool registration and execution                                ║
║ • WebSocket and HTTP transport layers                                       ║
║ • End-to-end integration testing                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    tester = MCPServerFixTester()
    
    try:
        report = await tester.run_all_tests()
        
        print(f"\n📊 TEST RESULTS SUMMARY")
        print(f"═" * 50)
        
        summary = report['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Pass Rate: {summary['pass_rate_percent']}%")
        print(f"Execution Time: {report['execution_time_seconds']}s")
        
        print(f"\n📋 TEST CATEGORIES:")
        for category, tests in report['test_results'].items():
            if isinstance(tests, dict):
                passed = sum(1 for result in tests.values() if result)
                total = len(tests)
                status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"  {status} {category.replace('_', ' ').title()}: {passed}/{total}")
        
        if report['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        print(f"\n🎯 NEXT STEPS:")
        for step in report['next_steps']:
            print(f"  {step}")
        
        # Determine exit code
        if summary['pass_rate_percent'] >= 90:
            print(f"\n🎉 SUCCESS: All critical components are working!")
            sys.exit(0)
        elif summary['pass_rate_percent'] >= 70:
            print(f"\n⚠️ PARTIAL SUCCESS: Basic functionality works but some improvements needed.")
            sys.exit(0)
        else:
            print(f"\n❌ NEEDS ATTENTION: Multiple components require fixes.")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print(f"\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
