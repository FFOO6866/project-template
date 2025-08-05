"""
Enhanced Nexus-MCP Integration with Production Server
===================================================

Integrates the production MCP server with the existing Nexus DataFlow platform,
providing comprehensive AI agent support with all 117 DataFlow nodes available
as MCP tools.

Features:
- Seamless integration with existing nexus_dataflow_platform.py
- Production MCP server with full DataFlow node registration
- Enhanced agent coordination and session management
- Real-time performance monitoring and analytics
- Multi-transport support (STDIO, HTTP, WebSocket)
- Advanced authentication and authorization
- Circuit breaker and rate limiting patterns

Usage:
    # Replace the basic MCP server in nexus_dataflow_platform.py
    from enhanced_nexus_mcp_integration import EnhancedNexusMCPIntegration
    
    integration = EnhancedNexusMCPIntegration(nexus_app)
    integration.initialize_production_mcp_server()
    integration.start()
"""

import os
import sys
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Apply Windows compatibility
try:
    import windows_sdk_compatibility
except ImportError:
    pass

# Core Kailash imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Production MCP server
from production_mcp_server import ProductionMCPServer, ServerConfig, ServerMetrics

# DataFlow integration
try:
    from dataflow_classification_models import (
        db, Company, User, Customer, Quote,
        ProductClassification, ClassificationHistory, ClassificationCache,
        ETIMAttribute, ClassificationRule, ClassificationFeedback,
        ClassificationMetrics, Document, DocumentProcessingQueue
    )
    DATAFLOW_AVAILABLE = True
except ImportError:
    DATAFLOW_AVAILABLE = False
    print("WARNING: DataFlow models not available")

# FastAPI for enhanced endpoints
try:
    from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, WebSocket
    from fastapi.responses import JSONResponse, StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = logging.getLogger(__name__)

class EnhancedNexusMCPIntegration:
    """
    Enhanced integration layer between Nexus platform and production MCP server.
    
    This class provides a bridge between the existing Nexus DataFlow platform
    and the new production MCP server, enabling advanced AI agent support
    while maintaining compatibility with existing workflows.
    """
    
    def __init__(self, nexus_app=None, config: Optional[ServerConfig] = None):
        self.nexus_app = nexus_app
        self.config = config or ServerConfig(
            port=3001,
            enable_auth=True,
            auth_type="jwt",
            max_concurrent_requests=500,
            enable_agent_collaboration=True,
            enable_performance_tracking=True
        )
        
        # Production MCP server instance
        self.mcp_server = None
        self.server_thread = None
        self.integration_metrics = {
            'nexus_mcp_requests': 0,
            'agent_sessions_created': 0,
            'dataflow_operations_via_mcp': 0,
            'integration_errors': 0
        }
        
        # Agent coordination
        self.active_agent_workflows = {}
        self.agent_performance_cache = {}
        
        logger.info("🔗 Enhanced Nexus-MCP Integration initialized")
    
    def initialize_production_mcp_server(self) -> ProductionMCPServer:
        """
        Initialize the production MCP server with DataFlow integration.
        
        Returns:
            ProductionMCPServer: Configured and ready production server
        """
        
        logger.info("🚀 Initializing Production MCP Server...")
        
        # Create production MCP server
        self.mcp_server = ProductionMCPServer(self.config)
        
        # Add custom Nexus integration tools
        self._register_nexus_integration_tools()
        
        # Add advanced workflow orchestration tools
        self._register_workflow_orchestration_tools()
        
        # Add real-time monitoring tools
        self._register_monitoring_tools()
        
        logger.info("✅ Production MCP Server initialized with Nexus integration")
        return self.mcp_server
    
    def _register_nexus_integration_tools(self):
        """Register Nexus-specific integration tools"""
        
        @self.mcp_server.mcp_server.tool(
            name="execute_nexus_workflow",
            description="Execute a registered Nexus workflow through MCP"
        )
        async def execute_nexus_workflow(
            workflow_name: str,
            context: Dict[str, Any] = None,
            agent_id: str = None,
            session_id: str = None
        ) -> Dict[str, Any]:
            """Execute Nexus workflow tool"""
            try:
                if not self.nexus_app:
                    return {
                        "success": False,
                        "error": "Nexus app not available"
                    }
                
                # Get the workflow from Nexus app
                try:
                    workflow = self.nexus_app.get_workflow(workflow_name)
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Workflow '{workflow_name}' not found: {str(e)}"
                    }
                
                # Execute workflow
                runtime = LocalRuntime()
                start_time = time.time()
                
                results, run_id = runtime.execute(workflow, context or {})
                execution_time = time.time() - start_time
                
                # Update metrics
                self.integration_metrics['nexus_mcp_requests'] += 1
                
                # Track agent performance
                if agent_id:
                    if agent_id not in self.agent_performance_cache:
                        self.agent_performance_cache[agent_id] = {
                            'workflow_executions': 0,
                            'total_execution_time': 0,
                            'successful_executions': 0,
                            'failed_executions': 0
                        }
                    
                    cache = self.agent_performance_cache[agent_id]
                    cache['workflow_executions'] += 1
                    cache['total_execution_time'] += execution_time
                    cache['successful_executions'] += 1
                
                return {
                    "success": True,
                    "results": results,
                    "metadata": {
                        "workflow_name": workflow_name,
                        "run_id": run_id,
                        "execution_time_ms": round(execution_time * 1000, 2),
                        "agent_id": agent_id,
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                self.integration_metrics['integration_errors'] += 1
                
                # Update agent error stats
                if agent_id and agent_id in self.agent_performance_cache:
                    self.agent_performance_cache[agent_id]['failed_executions'] += 1
                
                return {
                    "success": False,
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e),
                        "workflow_name": workflow_name,
                        "agent_id": agent_id,
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
        
        @self.mcp_server.mcp_server.tool(
            name="get_nexus_workflows",
            description="Get list of available Nexus workflows"
        )
        async def get_nexus_workflows() -> Dict[str, Any]:
            """Get Nexus workflows tool"""
            try:
                if not self.nexus_app:
                    return {
                        "success": False,
                        "error": "Nexus app not available"
                    }
                
                # Get available workflows (this would need to be implemented in the Nexus app)
                available_workflows = [
                    "dataflow_operations",
                    "classification_pipeline", 
                    "bulk_operations",
                    "dashboard_analytics",
                    "user_session"
                ]
                
                workflow_info = []
                for workflow_name in available_workflows:
                    try:
                        workflow = self.nexus_app.get_workflow(workflow_name)
                        workflow_info.append({
                            "name": workflow_name,
                            "description": f"Nexus workflow: {workflow_name}",
                            "available": True
                        })
                    except Exception:
                        workflow_info.append({
                            "name": workflow_name,
                            "description": f"Nexus workflow: {workflow_name}",
                            "available": False
                        })
                
                return {
                    "success": True,
                    "workflows": workflow_info,
                    "total_count": len(workflow_info)
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp_server.mcp_server.tool(
            name="get_dataflow_models_info",
            description="Get detailed information about available DataFlow models"
        )
        async def get_dataflow_models_info() -> Dict[str, Any]:
            """Get DataFlow models info tool"""
            try:
                if not DATAFLOW_AVAILABLE:
                    return {
                        "success": False,
                        "error": "DataFlow not available"
                    }
                
                models_info = []
                
                dataflow_models = [
                    (Company, "Business entity management"),
                    (User, "User account management"),
                    (Customer, "Customer relationship management"),
                    (Quote, "Sales quote management"),
                    (ProductClassification, "AI-powered product classification"),
                    (ClassificationHistory, "Classification audit trail"),
                    (ClassificationCache, "Classification performance cache"),
                    (ETIMAttribute, "ETIM standard attributes"),
                    (ClassificationRule, "Business classification rules"),
                    (ClassificationFeedback, "ML model feedback loop"),
                    (ClassificationMetrics, "Performance analytics"),
                    (Document, "Document management"),
                    (DocumentProcessingQueue, "Document processing pipeline")
                ]
                
                for model_class, description in dataflow_models:
                    model_name = model_class.__name__
                    
                    # Get available operations for this model
                    operations = [
                        "create", "read", "update", "delete", "list",
                        "bulk_create", "bulk_update", "bulk_delete", "bulk_upsert"
                    ]
                    
                    models_info.append({
                        "model_name": model_name,
                        "description": description,
                        "available_operations": operations,
                        "total_operations": len(operations),
                        "mcp_tools": [f"{model_name}_{op}" for op in operations]
                    })
                
                return {
                    "success": True,
                    "models": models_info,
                    "total_models": len(models_info),
                    "total_operations": sum(len(model["available_operations"]) for model in models_info),
                    "dataflow_available": DATAFLOW_AVAILABLE
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        logger.info("✅ Nexus integration tools registered")
    
    def _register_workflow_orchestration_tools(self):
        """Register advanced workflow orchestration tools"""
        
        @self.mcp_server.mcp_server.tool(
            name="create_agent_workflow_session",
            description="Create a persistent workflow session for complex multi-step operations"
        )
        async def create_agent_workflow_session(
            agent_id: str,
            workflow_type: str,
            session_config: Dict[str, Any] = None
        ) -> Dict[str, Any]:
            """Create agent workflow session"""
            try:
                import uuid
                import time
                
                session_id = str(uuid.uuid4())
                
                workflow_session = {
                    'session_id': session_id,
                    'agent_id': agent_id,
                    'workflow_type': workflow_type,
                    'created_at': datetime.utcnow(),
                    'last_activity': datetime.utcnow(),
                    'config': session_config or {},
                    'workflow_steps': [],
                    'current_step': 0,
                    'status': 'active',
                    'results_cache': {},
                    'performance_metrics': {
                        'total_steps': 0,
                        'successful_steps': 0,
                        'failed_steps': 0,
                        'total_execution_time': 0
                    }
                }
                
                self.active_agent_workflows[session_id] = workflow_session
                
                return {
                    "success": True,
                    "workflow_session_id": session_id,
                    "agent_id": agent_id,
                    "workflow_type": workflow_type,
                    "created_at": workflow_session['created_at'].isoformat(),
                    "status": "active"
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp_server.mcp_server.tool(
            name="execute_workflow_step",
            description="Execute a single step in a workflow session"
        )
        async def execute_workflow_step(
            workflow_session_id: str,
            step_name: str,
            step_config: Dict[str, Any],
            use_cached_results: bool = True
        ) -> Dict[str, Any]:
            """Execute workflow step"""
            try:
                if workflow_session_id not in self.active_agent_workflows:
                    return {
                        "success": False,
                        "error": "Workflow session not found"
                    }
                
                session = self.active_agent_workflows[workflow_session_id]
                
                # Check cache if enabled
                cache_key = f"{step_name}_{hash(str(step_config))}"
                if use_cached_results and cache_key in session['results_cache']:
                    cached_result = session['results_cache'][cache_key]
                    
                    return {
                        "success": True,
                        "results": cached_result['results'],
                        "step_name": step_name,
                        "cached": True,
                        "cached_at": cached_result['timestamp'],
                        "execution_time_ms": 0
                    }
                
                # Execute step
                start_time = time.time()
                
                # Determine step type and execute accordingly
                if step_config.get('type') == 'nexus_workflow':
                    # Execute Nexus workflow
                    workflow_name = step_config.get('workflow_name')
                    context = step_config.get('context', {})
                    
                    if self.nexus_app:
                        workflow = self.nexus_app.get_workflow(workflow_name)
                        runtime = LocalRuntime()
                        results, run_id = runtime.execute(workflow, context)
                        
                        step_result = {
                            "type": "nexus_workflow",
                            "workflow_name": workflow_name,
                            "results": results,
                            "run_id": run_id
                        }
                    else:
                        raise Exception("Nexus app not available")
                
                elif step_config.get('type') == 'dataflow_operation':
                    # Execute DataFlow operation via MCP tool
                    model_name = step_config.get('model')
                    operation = step_config.get('operation')
                    parameters = step_config.get('parameters', {})
                    
                    # Use the DataFlow tool discovery from the MCP server
                    tool_discovery = self.mcp_server.tool_discovery
                    workflow = tool_discovery.create_dataflow_workflow(model_name, operation, parameters)
                    
                    runtime = LocalRuntime()
                    results, run_id = runtime.execute(workflow.build())
                    
                    step_result = {
                        "type": "dataflow_operation", 
                        "model": model_name,
                        "operation": operation,
                        "results": results,
                        "run_id": run_id
                    }
                
                else:
                    raise Exception(f"Unknown step type: {step_config.get('type')}")
                
                execution_time = time.time() - start_time
                
                # Update session
                session['last_activity'] = datetime.utcnow()
                session['workflow_steps'].append({
                    'step_name': step_name,
                    'config': step_config,
                    'results': step_result,
                    'execution_time': execution_time,
                    'timestamp': datetime.utcnow().isoformat()
                })
                session['current_step'] += 1
                
                # Update metrics
                metrics = session['performance_metrics']
                metrics['total_steps'] += 1
                metrics['successful_steps'] += 1
                metrics['total_execution_time'] += execution_time
                
                # Cache result
                session['results_cache'][cache_key] = {
                    'results': step_result,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Clean cache if too large
                if len(session['results_cache']) > 50:
                    # Remove oldest entries
                    oldest_keys = sorted(
                        session['results_cache'].keys(),
                        key=lambda k: session['results_cache'][k]['timestamp']
                    )[:10]
                    for key in oldest_keys:
                        del session['results_cache'][key]
                
                return {
                    "success": True,
                    "results": step_result,
                    "step_name": step_name,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "workflow_session_id": workflow_session_id,
                    "current_step": session['current_step'],
                    "cached": False
                }
                
            except Exception as e:
                # Update error metrics
                if workflow_session_id in self.active_agent_workflows:
                    session = self.active_agent_workflows[workflow_session_id]
                    session['performance_metrics']['failed_steps'] += 1
                
                return {
                    "success": False,
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e),
                        "step_name": step_name,
                        "workflow_session_id": workflow_session_id
                    }
                }
        
        @self.mcp_server.mcp_server.tool(
            name="get_workflow_session_status",
            description="Get status and progress of a workflow session"
        )
        async def get_workflow_session_status(workflow_session_id: str) -> Dict[str, Any]:
            """Get workflow session status"""
            try:
                if workflow_session_id not in self.active_agent_workflows:
                    return {
                        "success": False,
                        "error": "Workflow session not found"
                    }
                
                session = self.active_agent_workflows[workflow_session_id]
                
                return {
                    "success": True,
                    "session_info": {
                        "session_id": workflow_session_id,
                        "agent_id": session['agent_id'],
                        "workflow_type": session['workflow_type'],
                        "status": session['status'],
                        "created_at": session['created_at'].isoformat(),
                        "last_activity": session['last_activity'].isoformat(),
                        "current_step": session['current_step'],
                        "total_steps_executed": len(session['workflow_steps']),
                        "performance_metrics": session['performance_metrics'],
                        "cache_size": len(session['results_cache'])
                    },
                    "recent_steps": [
                        {
                            "step_name": step['step_name'],
                            "execution_time_ms": round(step['execution_time'] * 1000, 2),
                            "timestamp": step['timestamp']
                        }
                        for step in session['workflow_steps'][-5:]  # Last 5 steps
                    ]
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        logger.info("✅ Workflow orchestration tools registered")
    
    def _register_monitoring_tools(self):
        """Register real-time monitoring and analytics tools"""
        
        @self.mcp_server.mcp_server.tool(
            name="get_integration_metrics",
            description="Get comprehensive Nexus-MCP integration metrics"
        )
        async def get_integration_metrics() -> Dict[str, Any]:
            """Get integration metrics"""
            try:
                # Get MCP server metrics
                mcp_metrics = self.mcp_server.metrics.get_summary()
                
                # Get session analytics
                session_analytics = self.mcp_server.session_manager.get_session_analytics()
                
                # Active workflow sessions
                active_workflows = len(self.active_agent_workflows)
                workflow_types = {}
                total_workflow_steps = 0
                
                for session in self.active_agent_workflows.values():
                    workflow_type = session['workflow_type']
                    workflow_types[workflow_type] = workflow_types.get(workflow_type, 0) + 1
                    total_workflow_steps += len(session['workflow_steps'])
                
                # Agent performance summary
                agent_performance = {}
                for agent_id, cache in self.agent_performance_cache.items():
                    if cache['workflow_executions'] > 0:
                        avg_execution_time = cache['total_execution_time'] / cache['workflow_executions']
                        success_rate = cache['successful_executions'] / cache['workflow_executions']
                        
                        agent_performance[agent_id] = {
                            "workflow_executions": cache['workflow_executions'],
                            "average_execution_time_ms": round(avg_execution_time * 1000, 2),
                            "success_rate_percent": round(success_rate * 100, 1),
                            "total_failures": cache['failed_executions']
                        }
                
                return {
                    "success": True,
                    "integration_metrics": self.integration_metrics,
                    "mcp_server_metrics": mcp_metrics,
                    "session_analytics": session_analytics,
                    "workflow_sessions": {
                        "active_sessions": active_workflows,
                        "workflow_types": workflow_types,
                        "total_steps_executed": total_workflow_steps
                    },
                    "agent_performance": agent_performance,
                    "dataflow_integration": {
                        "available": DATAFLOW_AVAILABLE,
                        "models_registered": len(self.mcp_server.tool_discovery.discovered_tools) if self.mcp_server else 0
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp_server.mcp_server.tool(
            name="cleanup_workflow_sessions",
            description="Clean up inactive workflow sessions"
        )
        async def cleanup_workflow_sessions(max_age_hours: int = 24) -> Dict[str, Any]:
            """Cleanup workflow sessions"""
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
                sessions_to_remove = []
                
                for session_id, session in self.active_agent_workflows.items():
                    if session['last_activity'] < cutoff_time:
                        sessions_to_remove.append(session_id)
                
                for session_id in sessions_to_remove:
                    del self.active_agent_workflows[session_id]
                
                return {
                    "success": True,
                    "cleaned_sessions": len(sessions_to_remove),
                    "active_sessions_remaining": len(self.active_agent_workflows),
                    "cutoff_time": cutoff_time.isoformat()
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        logger.info("✅ Monitoring tools registered")
    
    def start_mcp_server_async(self):
        """Start MCP server in background thread"""
        
        def run_server():
            try:
                asyncio.run(self.mcp_server.start_async())
            except Exception as e:
                logger.error(f"MCP server failed: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        logger.info("🚀 Production MCP server started in background")
    
    def add_nexus_mcp_endpoints(self, app: FastAPI):
        """Add MCP integration endpoints to Nexus FastAPI app"""
        
        if not FASTAPI_AVAILABLE:
            logger.warning("FastAPI not available, skipping endpoint registration")
            return
        
        @app.get("/api/mcp/status")
        async def mcp_status():
            """Get MCP server status"""
            try:
                if not self.mcp_server:
                    return JSONResponse(
                        content={"status": "not_initialized", "error": "MCP server not initialized"},
                        status_code=503
                    )
                
                # Get comprehensive status
                metrics = self.mcp_server.metrics.get_summary()
                session_analytics = self.mcp_server.session_manager.get_session_analytics()
                
                return {
                    "status": "running",
                    "mcp_server_metrics": metrics,
                    "session_analytics": session_analytics,
                    "integration_metrics": self.integration_metrics,
                    "dataflow_available": DATAFLOW_AVAILABLE,
                    "config": {
                        "port": self.config.port,
                        "auth_enabled": self.config.enable_auth,
                        "collaboration_enabled": self.config.enable_agent_collaboration
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                return JSONResponse(
                    content={"status": "error", "error": str(e)},
                    status_code=500
                )
        
        @app.post("/api/mcp/execute-tool")
        async def execute_mcp_tool(request: Dict[str, Any]):
            """Execute MCP tool via HTTP"""
            try:
                tool_name = request.get("tool_name")
                parameters = request.get("parameters", {})
                agent_id = request.get("agent_id")
                session_id = request.get("session_id")
                
                if not tool_name:
                    raise HTTPException(status_code=400, detail="tool_name required")
                
                # Add agent/session context to parameters
                if agent_id:
                    parameters["_agent_id"] = agent_id
                if session_id:
                    parameters["_session_id"] = session_id
                
                # Find and execute tool
                for model_tools in self.mcp_server.tool_discovery.discovered_tools.values():
                    for tool_info in model_tools.values():
                        if tool_info['tool_name'] == tool_name:
                            result = await self.mcp_server._execute_dataflow_tool(
                                tool_info['model'],
                                tool_info['operation'],
                                parameters,
                                tool_info
                            )
                            
                            self.integration_metrics['dataflow_operations_via_mcp'] += 1
                            return result
                
                # Check utility tools
                utility_tools = [
                    "create_agent_session", "get_available_tools", "get_server_metrics",
                    "enable_agent_collaboration", "health_check", "execute_nexus_workflow",
                    "get_nexus_workflows", "get_dataflow_models_info"
                ]
                
                if tool_name in utility_tools:
                    # This would need access to the registered tool functions
                    return {"success": False, "error": "Utility tool execution via HTTP not yet implemented"}
                
                return JSONResponse(
                    content={"success": False, "error": f"Tool {tool_name} not found"},
                    status_code=404
                )
                
            except Exception as e:
                self.integration_metrics['integration_errors'] += 1
                return JSONResponse(
                    content={"success": False, "error": str(e)},
                    status_code=500
                )
        
        @app.get("/api/mcp/tools")
        async def list_mcp_tools():
            """List all available MCP tools"""
            try:
                tools = []
                
                # DataFlow tools
                for model_tools in self.mcp_server.tool_discovery.discovered_tools.values():
                    for tool_info in model_tools.values():
                        tools.append({
                            "name": tool_info['tool_name'],
                            "description": tool_info['description'],
                            "model": tool_info['model'],
                            "operation": tool_info['operation'],
                            "category": "dataflow",
                            "complexity_score": tool_info['complexity_score'],
                            "estimated_time_ms": tool_info['estimated_time_ms']
                        })
                
                # Utility tools
                utility_tools = [
                    {"name": "create_agent_session", "description": "Create agent session", "category": "session_management"},
                    {"name": "get_available_tools", "description": "Get available tools", "category": "discovery"},
                    {"name": "get_server_metrics", "description": "Get server metrics", "category": "monitoring"},
                    {"name": "health_check", "description": "Server health check", "category": "monitoring"},
                    {"name": "execute_nexus_workflow", "description": "Execute Nexus workflow", "category": "nexus_integration"},
                    {"name": "get_nexus_workflows", "description": "Get Nexus workflows", "category": "nexus_integration"},
                    {"name": "create_agent_workflow_session", "description": "Create workflow session", "category": "workflow_orchestration"}
                ]
                
                tools.extend(utility_tools)
                
                return {
                    "tools": tools,
                    "total_count": len(tools),
                    "categories": list(set(tool.get("category", "unknown") for tool in tools))
                }
                
            except Exception as e:
                return JSONResponse(
                    content={"error": str(e)},
                    status_code=500
                )
        
        logger.info("✅ Nexus-MCP integration endpoints added")
    
    def start(self, start_mcp_server: bool = True):
        """Start the enhanced integration"""
        
        logger.info("🚀 Starting Enhanced Nexus-MCP Integration...")
        
        if not self.mcp_server:
            self.initialize_production_mcp_server()
        
        if start_mcp_server:
            self.start_mcp_server_async()
        
        # Add endpoints to Nexus app if available
        if self.nexus_app and hasattr(self.nexus_app, 'api_app'):
            self.add_nexus_mcp_endpoints(self.nexus_app.api_app)
        
        logger.info("✅ Enhanced Nexus-MCP Integration started successfully")
        
        # Print integration summary
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ENHANCED NEXUS-MCP INTEGRATION ACTIVE                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ 🚀 Production MCP Server: Running on port {self.config.port:<10}                        ║
║ 🔗 DataFlow Integration: {str(DATAFLOW_AVAILABLE):<10}                                    ║
║ 🔐 Authentication: {self.config.auth_type:<15} Enabled: {str(self.config.enable_auth):<10}          ║
║ 🤝 Agent Collaboration: {str(self.config.enable_agent_collaboration):<10}                               ║
║ 📊 Performance Tracking: {str(self.config.enable_performance_tracking):<10}                              ║
║                                                                              ║
║ 🛠️  Available Features:                                                      ║
║   • {len(self.mcp_server.tool_discovery.discovered_tools) * 9 if self.mcp_server else 0:<3} DataFlow operations as MCP tools                           ║
║   • Advanced agent session management                                       ║
║   • Multi-step workflow orchestration                                       ║
║   • Real-time performance monitoring                                        ║
║   • Nexus workflow integration                                              ║
║   • HTTP API endpoints for tool execution                                   ║
║                                                                              ║
║ 🌐 Access Methods:                                                          ║
║   • MCP Protocol: STDIO transport                                           ║
║   • HTTP API: /api/mcp/* endpoints                                          ║
║   • Nexus Integration: execute_nexus_workflow tool                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)
    
    def shutdown(self):
        """Shutdown the integration"""
        
        logger.info("🛑 Shutting down Enhanced Nexus-MCP Integration...")
        
        # Cleanup workflow sessions
        for session_id in list(self.active_agent_workflows.keys()):
            del self.active_agent_workflows[session_id]
        
        # Shutdown MCP server
        if self.mcp_server:
            self.mcp_server.shutdown()
        
        # Wait for server thread
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5)
        
        logger.info("✅ Enhanced Nexus-MCP Integration shutdown complete")

# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def enhance_nexus_with_mcp(nexus_app, config: Optional[ServerConfig] = None) -> EnhancedNexusMCPIntegration:
    """
    Convenience function to enhance an existing Nexus app with production MCP capabilities.
    
    Args:
        nexus_app: Existing Nexus application instance
        config: Optional MCP server configuration
    
    Returns:
        EnhancedNexusMCPIntegration: Configured integration instance
    """
    
    integration = EnhancedNexusMCPIntegration(nexus_app, config)
    integration.start()
    return integration

def create_production_mcp_config(
    port: int = 3001,
    enable_auth: bool = True,
    auth_type: str = "jwt",
    max_concurrent_requests: int = 500,
    enable_collaboration: bool = True
) -> ServerConfig:
    """
    Create production MCP server configuration.
    
    Args:
        port: MCP server port
        enable_auth: Enable authentication
        auth_type: Authentication type (jwt, api_key, bearer)
        max_concurrent_requests: Maximum concurrent requests
        enable_collaboration: Enable agent collaboration
    
    Returns:
        ServerConfig: Production configuration
    """
    
    return ServerConfig(
        port=port,
        enable_auth=enable_auth,
        auth_type=auth_type,
        max_concurrent_requests=max_concurrent_requests,
        enable_agent_collaboration=enable_collaboration,
        enable_performance_tracking=True,
        enable_metrics=True,
        enable_caching=True,
        cache_ttl_seconds=1800,
        enable_http_transport=True,
        enable_dynamic_tool_discovery=True,
        auto_register_dataflow_nodes=True
    )

if __name__ == "__main__":
    # Standalone usage
    print("🚀 Starting Enhanced Nexus-MCP Integration in standalone mode...")
    
    config = create_production_mcp_config()
    integration = EnhancedNexusMCPIntegration(config=config)
    
    try:
        integration.start()
        print("Press Ctrl+C to shutdown...")
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
        integration.shutdown()
