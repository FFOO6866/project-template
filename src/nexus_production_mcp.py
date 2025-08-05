"""
Nexus Production MCP Server
Production-optimized MCP server for AI agent integration
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import aioredis
from anthropic_mcp import MCPServer, Tool, Resource
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from nexus import Nexus
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
    agent_port=int(os.getenv("JAEGER_PORT", 14268)),
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Metrics
mcp_tool_calls = Counter('nexus_mcp_tool_calls_total', 'Total MCP tool calls', ['tool', 'status'])
mcp_tool_duration = Histogram('nexus_mcp_tool_duration_seconds', 'MCP tool execution duration')
mcp_active_connections = Gauge('nexus_mcp_active_connections', 'Active MCP connections')
mcp_workflow_executions = Counter('nexus_mcp_workflow_executions_total', 'Workflow executions via MCP', ['workflow', 'status'])

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class NexusProductionMCP:
    """Production MCP server for Nexus platform integration"""
    
    def __init__(self):
        self.server = MCPServer("nexus-production")
        self.nexus: Optional[Nexus] = None
        self.redis: Optional[aioredis.Redis] = None
        self.runtime = LocalRuntime()
        
        # Configuration
        self.instance_id = os.getenv("NEXUS_INSTANCE_ID", f"mcp-{uuid.uuid4().hex[:8]}")
        self.max_concurrent_tools = int(os.getenv("MCP_MAX_CONCURRENT_TOOLS", 10))
        self.tool_timeout = int(os.getenv("MCP_TOOL_TIMEOUT", 300))
        
        # Connection tracking
        self.active_connections = 0
        self.tool_execution_semaphore = asyncio.Semaphore(self.max_concurrent_tools)
        
        self._setup_tools()
        self._setup_resources()
        
        logger.info("Nexus Production MCP server initialized", instance_id=self.instance_id)

    def _setup_tools(self):
        """Register MCP tools for AI agent integration"""
        
        @self.server.tool("execute_workflow")
        async def execute_workflow(workflow_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
            """Execute a Nexus workflow with parameters"""
            with tracer.start_as_current_span("mcp_execute_workflow") as span:
                span.set_attribute("workflow.name", workflow_name)
                span.set_attribute("instance.id", self.instance_id)
                
                start_time = time.time()
                
                async with self.tool_execution_semaphore:
                    try:
                        if not self.nexus or workflow_name not in self.nexus._workflows:
                            mcp_tool_calls.labels(tool="execute_workflow", status="error").inc()
                            return {
                                "success": False,
                                "error": f"Workflow '{workflow_name}' not found",
                                "available_workflows": list(self.nexus._workflows.keys()) if self.nexus else []
                            }
                        
                        # Get workflow
                        workflow = self.nexus._workflows[workflow_name]
                        
                        # Execute with timeout
                        try:
                            results, run_id = await asyncio.wait_for(
                                self._execute_workflow_async(workflow, parameters or {}),
                                timeout=self.tool_timeout
                            )
                        except asyncio.TimeoutError:
                            mcp_tool_calls.labels(tool="execute_workflow", status="timeout").inc()
                            return {
                                "success": False,
                                "error": f"Workflow execution timed out after {self.tool_timeout} seconds"
                            }
                        
                        duration = time.time() - start_time
                        
                        # Update metrics
                        mcp_tool_calls.labels(tool="execute_workflow", status="success").inc()
                        mcp_tool_duration.observe(duration)
                        mcp_workflow_executions.labels(workflow=workflow_name, status="success").inc()
                        
                        span.set_attribute("workflow.run_id", run_id)
                        span.set_attribute("workflow.duration", duration)
                        span.set_attribute("workflow.success", True)
                        
                        # Log execution
                        await self._log_mcp_execution(workflow_name, run_id, parameters, results, duration)
                        
                        return {
                            "success": True,
                            "workflow_name": workflow_name,
                            "run_id": run_id,
                            "results": results,
                            "execution_time": duration,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                    except Exception as e:
                        duration = time.time() - start_time
                        
                        mcp_tool_calls.labels(tool="execute_workflow", status="error").inc()
                        mcp_workflow_executions.labels(workflow=workflow_name, status="error").inc()
                        
                        span.set_attribute("workflow.error", str(e))
                        span.set_attribute("workflow.success", False)
                        
                        logger.error("MCP workflow execution failed",
                                    workflow_name=workflow_name,
                                    error=str(e),
                                    duration=duration)
                        
                        return {
                            "success": False,
                            "error": str(e),
                            "workflow_name": workflow_name,
                            "execution_time": duration
                        }

        @self.server.tool("list_workflows")
        async def list_workflows() -> Dict[str, Any]:
            """List available workflows"""
            with tracer.start_as_current_span("mcp_list_workflows"):
                try:
                    if not self.nexus:
                        return {"success": False, "error": "Nexus not initialized"}
                    
                    workflows = []
                    for name, workflow in self.nexus._workflows.items():
                        workflows.append({
                            "name": name,
                            "description": getattr(workflow, 'description', ''),
                            "nodes": len(workflow.nodes) if hasattr(workflow, 'nodes') else 0
                        })
                    
                    mcp_tool_calls.labels(tool="list_workflows", status="success").inc()
                    
                    return {
                        "success": True,
                        "workflows": workflows,
                        "count": len(workflows)
                    }
                    
                except Exception as e:
                    mcp_tool_calls.labels(tool="list_workflows", status="error").inc()
                    logger.error("Failed to list workflows", error=str(e))
                    return {"success": False, "error": str(e)}

        @self.server.tool("get_workflow_status")
        async def get_workflow_status(run_id: str) -> Dict[str, Any]:
            """Get status of a workflow execution"""
            with tracer.start_as_current_span("mcp_get_workflow_status") as span:
                span.set_attribute("run_id", run_id)
                
                try:
                    if not self.redis:
                        return {"success": False, "error": "Redis not available"}
                    
                    # Get execution log from Redis
                    logs = await self.redis.lrange("nexus:mcp_executions", 0, -1)
                    
                    for log_entry in logs:
                        try:
                            execution = json.loads(log_entry)
                            if execution.get("run_id") == run_id:
                                mcp_tool_calls.labels(tool="get_workflow_status", status="success").inc()
                                return {
                                    "success": True,
                                    "status": "completed",
                                    "execution": execution
                                }
                        except json.JSONDecodeError:
                            continue
                    
                    return {
                        "success": False,
                        "error": f"Workflow execution '{run_id}' not found"
                    }
                    
                except Exception as e:
                    mcp_tool_calls.labels(tool="get_workflow_status", status="error").inc()
                    logger.error("Failed to get workflow status", run_id=run_id, error=str(e))
                    return {"success": False, "error": str(e)}

        @self.server.tool("get_platform_health")
        async def get_platform_health() -> Dict[str, Any]:
            """Get Nexus platform health status"""
            with tracer.start_as_current_span("mcp_get_platform_health"):
                try:
                    health_data = {
                        "status": "healthy",
                        "instance_id": self.instance_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "version": "1.0.0"
                    }
                    
                    checks = {}
                    
                    # Check Nexus
                    if self.nexus:
                        checks["nexus"] = {
                            "status": "healthy",
                            "workflows": len(self.nexus._workflows)
                        }
                    else:
                        checks["nexus"] = {"status": "unhealthy", "error": "Not initialized"}
                        health_data["status"] = "unhealthy"
                    
                    # Check Redis
                    if self.redis:
                        try:
                            await self.redis.ping()
                            checks["redis"] = {"status": "healthy"}
                        except Exception as e:
                            checks["redis"] = {"status": "unhealthy", "error": str(e)}
                            health_data["status"] = "unhealthy"
                    else:
                        checks["redis"] = {"status": "unhealthy", "error": "Not connected"}
                        health_data["status"] = "unhealthy"
                    
                    # Add metrics
                    checks["metrics"] = {
                        "active_connections": self.active_connections,
                        "total_tool_calls": mcp_tool_calls._value.sum(),
                        "workflow_executions": mcp_workflow_executions._value.sum()
                    }
                    
                    health_data["checks"] = checks
                    
                    mcp_tool_calls.labels(tool="get_platform_health", status="success").inc()
                    
                    return {
                        "success": True,
                        "health": health_data
                    }
                    
                except Exception as e:
                    mcp_tool_calls.labels(tool="get_platform_health", status="error").inc()
                    logger.error("Failed to get platform health", error=str(e))
                    return {"success": False, "error": str(e)}

        @self.server.tool("create_workflow")
        async def create_workflow(name: str, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
            """Create a new workflow from definition"""
            with tracer.start_as_current_span("mcp_create_workflow") as span:
                span.set_attribute("workflow.name", name)
                
                try:
                    if not self.nexus:
                        return {"success": False, "error": "Nexus not initialized"}
                    
                    # Create workflow from definition
                    workflow = WorkflowBuilder()
                    
                    # Parse workflow definition
                    nodes = workflow_definition.get("nodes", [])
                    for node in nodes:
                        node_type = node.get("type")
                        node_id = node.get("id")
                        parameters = node.get("parameters", {})
                        
                        workflow.add_node(node_type, node_id, parameters)
                    
                    # Parse connections
                    connections = workflow_definition.get("connections", [])
                    for connection in connections:
                        from_node = connection.get("from")
                        to_node = connection.get("to")
                        if from_node and to_node:
                            workflow.connect(from_node, to_node)
                    
                    # Register workflow
                    built_workflow = workflow.build()
                    self.nexus.register(name, built_workflow)
                    
                    mcp_tool_calls.labels(tool="create_workflow", status="success").inc()
                    
                    logger.info("Workflow created via MCP", workflow_name=name)
                    
                    return {
                        "success": True,
                        "workflow_name": name,
                        "message": f"Workflow '{name}' created successfully"
                    }
                    
                except Exception as e:
                    mcp_tool_calls.labels(tool="create_workflow", status="error").inc()
                    logger.error("Failed to create workflow", workflow_name=name, error=str(e))
                    return {"success": False, "error": str(e)}

    def _setup_resources(self):
        """Register MCP resources"""
        
        @self.server.resource("nexus://workflows")
        async def workflows_resource() -> str:
            """Get workflows as JSON resource"""
            if not self.nexus:
                return json.dumps({"error": "Nexus not initialized"})
            
            workflows = {}
            for name, workflow in self.nexus._workflows.items():
                workflows[name] = {
                    "name": name,
                    "description": getattr(workflow, 'description', ''),
                    "nodes": len(workflow.nodes) if hasattr(workflow, 'nodes') else 0
                }
            
            return json.dumps(workflows, indent=2)

        @self.server.resource("nexus://health")
        async def health_resource() -> str:
            """Get platform health as JSON resource"""
            health_tool = await self.server.tools["get_platform_health"]()
            return json.dumps(health_tool, indent=2)

        @self.server.resource("nexus://metrics")
        async def metrics_resource() -> str:
            """Get platform metrics as JSON resource"""
            metrics = {
                "instance_id": self.instance_id,
                "timestamp": datetime.utcnow().isoformat(),
                "tool_calls": {
                    "total": mcp_tool_calls._value.sum(),
                    "success_rate": 0.0  # Calculate from metrics
                },
                "workflow_executions": {
                    "total": mcp_workflow_executions._value.sum()
                },
                "active_connections": self.active_connections
            }
            
            return json.dumps(metrics, indent=2)

    async def _execute_workflow_async(self, workflow, parameters: Dict) -> tuple:
        """Execute workflow asynchronously"""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.runtime.execute(workflow, parameters)
        )

    async def _log_mcp_execution(self, workflow_name: str, run_id: str, 
                                parameters: Dict, results: Dict, duration: float):
        """Log MCP workflow execution"""
        try:
            execution_log = {
                "workflow_name": workflow_name,
                "run_id": run_id,
                "parameters": parameters,
                "results": results,
                "duration": duration,
                "source": "mcp",
                "instance_id": self.instance_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if self.redis:
                await self.redis.lpush(
                    "nexus:mcp_executions",
                    json.dumps(execution_log, default=str)
                )
                
                # Keep only last 1000 executions
                await self.redis.ltrim("nexus:mcp_executions", 0, 999)
            
        except Exception as e:
            logger.error("Failed to log MCP execution", error=str(e))

    async def initialize(self):
        """Initialize MCP server and dependencies"""
        try:
            # Initialize Redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis = aioredis.from_url(redis_url)
            await self.redis.ping()
            
            # Initialize Nexus
            self.nexus = Nexus(
                enable_auth=True,
                enable_monitoring=True
            )
            
            # Register sample workflows
            await self._register_sample_workflows()
            
            # Start metrics server
            metrics_port = int(os.getenv("MCP_METRICS_PORT", 9091))
            start_http_server(metrics_port)
            
            logger.info("Nexus Production MCP server initialized successfully",
                       instance_id=self.instance_id,
                       metrics_port=metrics_port)
            
        except Exception as e:
            logger.error("Failed to initialize MCP server", error=str(e))
            raise

    async def _register_sample_workflows(self):
        """Register sample workflows for demonstration"""
        # Text processing workflow
        text_workflow = WorkflowBuilder()
        text_workflow.add_node("PythonCodeNode", "process_text", {
            "code": """
import re
text = parameters.get('text', '')
operation = parameters.get('operation', 'uppercase')

if operation == 'uppercase':
    result = {'processed_text': text.upper()}
elif operation == 'lowercase':
    result = {'processed_text': text.lower()}
elif operation == 'word_count':
    words = len(text.split())
    result = {'word_count': words, 'character_count': len(text)}
elif operation == 'clean':
    cleaned = re.sub(r'[^a-zA-Z0-9\\s]', '', text)
    result = {'cleaned_text': cleaned}
else:
    result = {'error': f'Unknown operation: {operation}'}
            """
        })
        
        self.nexus.register("text_processor", text_workflow.build())
        
        # Data analysis workflow
        analysis_workflow = WorkflowBuilder()
        analysis_workflow.add_node("PythonCodeNode", "analyze_data", {
            "code": """
import statistics
import json

data = parameters.get('data', [])
if not data:
    result = {'error': 'No data provided'}
else:
    try:
        numbers = [float(x) for x in data]
        result = {
            'count': len(numbers),
            'sum': sum(numbers),
            'mean': statistics.mean(numbers),
            'median': statistics.median(numbers),
            'min': min(numbers),
            'max': max(numbers),
            'range': max(numbers) - min(numbers)
        }
        if len(numbers) > 1:
            result['stdev'] = statistics.stdev(numbers)
    except (ValueError, TypeError) as e:
        result = {'error': f'Invalid data format: {str(e)}'}
            """
        })
        
        self.nexus.register("data_analyzer", analysis_workflow.build())
        
        logger.info("Sample workflows registered for MCP", count=len(self.nexus._workflows))

    async def start(self, host: str = "0.0.0.0", port: int = 3001):
        """Start the MCP server"""
        await self.initialize()
        
        logger.info("Starting Nexus Production MCP server", 
                   host=host, port=port, instance_id=self.instance_id)
        
        # Set up connection tracking
        original_connect = self.server.connect
        
        async def tracked_connect(*args, **kwargs):
            self.active_connections += 1
            mcp_active_connections.set(self.active_connections)
            try:
                return await original_connect(*args, **kwargs)
            finally:
                self.active_connections -= 1
                mcp_active_connections.set(self.active_connections)
        
        self.server.connect = tracked_connect
        
        # Start server
        await self.server.start(host=host, port=port)

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Shutting down Nexus Production MCP server", instance_id=self.instance_id)
        
        if self.redis:
            await self.redis.close()
        
        # Add any additional cleanup here

# Global MCP server instance
mcp_server = NexusProductionMCP()

# Graceful shutdown handling
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal", signal=signum)
    asyncio.create_task(mcp_server.cleanup())
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

async def main():
    """Main entry point"""
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("NEXUS_MCP_PORT", 3001))
    
    try:
        await mcp_server.start(host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("MCP server error", error=str(e))
    finally:
        await mcp_server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())