"""
Production-Ready MCP Server for DataFlow AI Agent Support
=======================================================

A comprehensive MCP server implementation that provides production-grade AI agent support
with dynamic tool discovery, authentication, performance optimization, and comprehensive
monitoring. Built on the Kailash MCP SDK with enterprise-grade features.

Key Features:
- Dynamic registration of all 117 DataFlow nodes as MCP tools
- JWT authentication with role-based access control
- Concurrent request handling with connection pooling
- Real-time performance monitoring and metrics
- Circuit breaker and rate limiting patterns
- Tool discovery with capability-based filtering
- WebSocket and HTTP transport support
- Comprehensive error handling and logging
- Agent session Management
- Tool usage analytics

Usage:
    python production_mcp_server.py --port 3001 --auth jwt
    
    Or as a service:
    from production_mcp_server import ProductionMCPServer
    server = ProductionMCPServer(port=3001, enable_auth=True)
    server.start()
"""

import os
import sys
import time
import json
import asyncio
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
import threading
from contextlib import asynccontextmanager

# Apply Windows compatibility patches
try:
except ImportError:
    pass

# Core Kailash and DataFlow imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash.mcp_server import (
    MCPServer, APIKeyAuth, JWTAuth, BearerTokenAuth,
    ServiceRegistry, discover_mcp_servers, get_mcp_client,
    structured_tool, create_progress_reporter, create_cancellation_context,
    MCPError, AuthenticationError, AuthorizationError, RateLimitError,
    ToolError, TransportError, RetryableOperation
)

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
    print("WARNING: DataFlow models not available, creating mock configuration")
    DATAFLOW_AVAILABLE = False
    
    # Create minimal mock for development
    class MockDB:
        def __init__(self):
            self.connection_pool = None
            
    db = MockDB()
    
    # Mock model classes
    class Company: pass
    class User: pass
    class Customer: pass
    class Quote: pass
    class ProductClassification: pass
    class ClassificationHistory: pass
    class ClassificationCache: pass
    class ETIMAttribute: pass
    class ClassificationRule: pass
    class ClassificationFeedback: pass
    class ClassificationMetrics: pass
    class Document: pass
    class DocumentProcessingQueue: pass

# FastAPI for HTTP transport (optional)
try:
    from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("WARNING: FastAPI not available, HTTP transport disabled")

# JWT handling
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("WARNING: PyJWT not available, JWT auth disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_server.log')
    ]
)
logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURATION AND METRICS
# ==============================================================================

@dataclass
class ServerConfig:
    """Production MCP server configuration"""
    port: int = 3001
    host: str = "0.0.0.0"
    enable_auth: bool = True
    auth_type: str = "jwt"  # jwt, api_key, bearer
    jwt_secret: str = "mcp-server-secret-key"
    jwt_expiration_hours: int = 24
    
    # Performance settings
    max_concurrent_requests: int = 500
    request_timeout_seconds: int = 60
    rate_limit_per_minute: int = 1000
    
    # Connection pool settings
    connection_pool_size: int = 20
    connection_pool_max_overflow: int = 40
    connection_recycle_seconds: int = 1800
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 10
    circuit_breaker_recovery_timeout: int = 60
    circuit_breaker_expected_exception: tuple = (Exception,)
    
    # Cache settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 1800
    cache_max_size_mb: int = 256
    
    # Monitoring settings
    enable_metrics: bool = True
    metrics_collection_interval: int = 30
    enable_performance_tracking: bool = True
    enable_agent_analytics: bool = True
    
    # Transport settings
    enable_http_transport: bool = True
    enable_websocket_transport: bool = True
    enable_stdio_transport: bool = True
    
    # Agent coordination settings
    max_agents_per_session: int = 10
    agent_session_timeout_minutes: int = 30
    enable_agent_collaboration: bool = True
    
    # Tool discovery settings
    enable_dynamic_tool_discovery: bool = True
    tool_discovery_cache_ttl: int = 300
    auto_register_dataflow_nodes: bool = True

class ServerMetrics:
    """Comprehensive server metrics collection"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.tool_usage_count = defaultdict(int)
        self.agent_sessions = {}
        self.performance_samples = []
        self.concurrent_requests = 0
        self.rate_limit_violations = 0
        self.circuit_breaker_trips = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.memory_usage_mb = 0
        
        # Agent-specific metrics
        self.agent_request_count = defaultdict(int)
        self.agent_error_count = defaultdict(int)
        self.agent_tool_usage = defaultdict(lambda: defaultdict(int))
        self.agent_session_duration = defaultdict(float)
        
        # Tool-specific metrics
        self.tool_response_times = defaultdict(list)
        self.tool_success_rates = defaultdict(lambda: {'success': 0, 'failure': 0})
        self.tool_complexity_scores = defaultdict(float)
        
        self._lock = threading.Lock()
    
    def record_request(self, agent_id: Optional[str] = None, execution_time: float = 0.0,
                      success: bool = True, tool_name: Optional[str] = None):
        """Record request metrics"""
        with self._lock:
            self.request_count += 1
            self.total_response_time += execution_time
            
            if not success:
                self.error_count += 1
            
            if agent_id:
                self.agent_request_count[agent_id] += 1
                if not success:
                    self.agent_error_count[agent_id] += 1
            
            if tool_name:
                self.tool_usage_count[tool_name] += 1
                self.tool_response_times[tool_name].append(execution_time)
                
                # Keep only last 100 samples
                if len(self.tool_response_times[tool_name]) > 100:
                    self.tool_response_times[tool_name] = self.tool_response_times[tool_name][-100:]
                
                if success:
                    self.tool_success_rates[tool_name]['success'] += 1
                else:
                    self.tool_success_rates[tool_name]['failure'] += 1
                
                if agent_id:
                    self.agent_tool_usage[agent_id][tool_name] += 1
    
    def start_agent_session(self, agent_id: str, agent_info: Dict[str, Any]):
        """Start tracking an agent session"""
        with self._lock:
            self.agent_sessions[agent_id] = {
                'start_time': time.time(),
                'agent_info': agent_info,
                'request_count': 0,
                'last_activity': time.time()
            }
    
    def end_agent_session(self, agent_id: str):
        """End an agent session"""
        with self._lock:
            if agent_id in self.agent_sessions:
                session = self.agent_sessions[agent_id]
                duration = time.time() - session['start_time']
                self.agent_session_duration[agent_id] = duration
                del self.agent_sessions[agent_id]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        with self._lock:
            uptime = time.time() - self.start_time
            avg_response_time = (self.total_response_time / max(self.request_count, 1)) * 1000
            error_rate = (self.error_count / max(self.request_count, 1)) * 100
            
            # Calculate tool statistics
            tool_stats = {}
            for tool, times in self.tool_response_times.items():
                if times:
                    tool_stats[tool] = {
                        'usage_count': self.tool_usage_count[tool],
                        'avg_response_time_ms': (sum(times) / len(times)) * 1000,
                        'success_rate': (
                            self.tool_success_rates[tool]['success'] /
                            max(sum(self.tool_success_rates[tool].values()), 1)
                        ) * 100
                    }
            
            # Active agent sessions
            active_agents = len(self.agent_sessions)
            
            return {
                'server_uptime_seconds': uptime,
                'total_requests': self.request_count,
                'error_count': self.error_count,
                'error_rate_percent': error_rate,
                'average_response_time_ms': avg_response_time,
                'concurrent_requests': self.concurrent_requests,
                'rate_limit_violations': self.rate_limit_violations,
                'circuit_breaker_trips': self.circuit_breaker_trips,
                'cache_hit_ratio': self.cache_hits / max(self.cache_hits + self.cache_misses, 1),
                'memory_usage_mb': self.memory_usage_mb,
                'active_agent_sessions': active_agents,
                'total_tools_registered': len(self.tool_usage_count),
                'most_used_tools': dict(Counter(self.tool_usage_count).most_common(10)),
                'tool_statistics': tool_stats,
                'agent_statistics': {
                    'total_agents_served': len(self.agent_request_count),
                    'most_active_agents': dict(Counter(self.agent_request_count).most_common(5)),
                    'agent_error_rates': {
                        agent: (errors / max(self.agent_request_count[agent], 1)) * 100
                        for agent, errors in self.agent_error_count.items()
                    }
                }
            }

# ==============================================================================
# DATAFLOW NODE DISCOVERY AND TOOL REGISTRATION
# ==============================================================================

class DataFlowToolDiscovery:
    """Advanced DataFlow node discovery and tool registration"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.discovered_tools = {}
        self.tool_schemas = {}
        self.tool_categories = defaultdict(list)
        self.runtime = LocalRuntime()
        
        # DataFlow models and their capabilities
        self.dataflow_models = [
            Company, User, Customer, Quote,
            ProductClassification, ClassificationHistory, ClassificationCache,
            ETIMAttribute, ClassificationRule, ClassificationFeedback,
            ClassificationMetrics, Document, DocumentProcessingQueue
        ]
        
    def discover_all_tools(self) -> Dict[str, Any]:
        """Discover all available DataFlow tools with enhanced metadata"""
        logger.info("🔍 Discovering DataFlow tools...")
        
        discovered = {}
        
        for model in self.dataflow_models:
            model_name = model.__name__
            model_tools = self._discover_model_tools(model_name, model)
            
            if model_tools:
                discovered[model_name.lower()] = model_tools
                
                # Categorize tools
                for operation, tool_info in model_tools.items():
                    category = self._determine_tool_category(model_name, operation)
                    self.tool_categories[category].append(tool_info['tool_name'])
        
        self.discovered_tools = discovered
        logger.info(f"✅ Discovered {sum(len(tools) for tools in discovered.values())} tools across {len(discovered)} models")
        
        return discovered
    
    def _discover_model_tools(self, model_name: str, model_class) -> Dict[str, Any]:
        """Discover tools for a specific DataFlow model"""
        
        # Standard CRUD operations + bulk operations
        operations = [
            ("create", "Create a new record", "write"),
            ("read", "Read/retrieve a record by ID", "read"),
            ("update", "Update an existing record", "write"),
            ("delete", "Delete a record by ID", "write"),
            ("list", "List records with filtering and pagination", "read"),
            ("bulk_create", "Create multiple records in batch", "bulk"),
            ("bulk_update", "Update multiple records in batch", "bulk"),
            ("bulk_delete", "Delete multiple records in batch", "bulk"),
            ("bulk_upsert", "Insert or update multiple records", "bulk")
        ]
        
        model_tools = {}
        
        for operation, description, operation_type in operations:
            tool_name = f"{model_name}_{operation}"
            
            # Create enhanced tool schema
            schema = self._create_tool_schema(model_name, operation, description, operation_type)
            
            model_tools[operation] = {
                'tool_name': tool_name,
                'description': description,
                'model': model_name,
                'operation': operation,
                'operation_type': operation_type,
                'schema': schema,
                'complexity_score': self._calculate_complexity_score(operation, operation_type),
                'estimated_time_ms': self._estimate_execution_time(operation, operation_type),
                'required_permissions': self._get_required_permissions(model_name, operation),
                'cacheable': operation in ['read', 'list'],
                'idempotent': operation in ['read', 'list', 'create', 'update']
            }
            
            self.tool_schemas[tool_name] = schema
        
        return model_tools
    
    def _create_tool_schema(self, model_name: str, operation: str, description: str, operation_type: str) -> Dict[str, Any]:
        """Create JSON schema for tool parameters"""
        
        base_schema = {
            "type": "object",
            "description": f"{description} for {model_name}",
            "properties": {},
            "required": []
        }
        
        # Common parameters based on operation
        if operation == "create":
            base_schema["properties"] = {
                "data": {
                    "type": "object",
                    "description": f"Data for creating new {model_name}",
                    "additionalProperties": True
                },
                "validate_only": {
                    "type": "boolean",
                    "description": "Only validate without creating",
                    "default": False
                }
            }
            base_schema["required"] = ["data"]
            
        elif operation == "read":
            base_schema["properties"] = {
                "id": {
                    "type": "integer",
                    "description": f"ID of the {model_name} to retrieve"
                },
                "include_relations": {
                    "type": "boolean",
                    "description": "Include related objects",
                    "default": False
                }
            }
            base_schema["required"] = ["id"]
            
        elif operation == "update":
            base_schema["properties"] = {
                "id": {
                    "type": "integer",
                    "description": f"ID of the {model_name} to update"
                },
                "data": {
                    "type": "object",
                    "description": "Updated data",
                    "additionalProperties": True
                },
                "partial": {
                    "type": "boolean",
                    "description": "Allow partial updates",
                    "default": True
                }
            }
            base_schema["required"] = ["id", "data"]
            
        elif operation == "delete":
            base_schema["properties"] = {
                "id": {
                    "type": "integer",
                    "description": f"ID of the {model_name} to delete"
                },
                "soft_delete": {
                    "type": "boolean",
                    "description": "Perform soft delete if supported",
                    "default": False
                }
            }
            base_schema["required"] = ["id"]
            
        elif operation == "list":
            base_schema["properties"] = {
                "filters": {
                    "type": "object",
                    "description": "Filter criteria",
                    "additionalProperties": True
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of records",
                    "minimum": 1,
                    "maximum": 10000,
                    "default": 100
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of records to skip",
                    "minimum": 0,
                    "default": 0
                },
                "order_by": {
                    "type": "string",
                    "description": "Field to order by"
                },
                "order_direction": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "default": "asc"
                }
            }
            
        elif operation.startswith("bulk_"):
            base_schema["properties"] = {
                "data": {
                    "type": "array",
                    "description": f"Array of {model_name} records for bulk operation",
                    "items": {"type": "object", "additionalProperties": True},
                    "minItems": 1,
                    "maxItems": 10000
                },
                "batch_size": {
                    "type": "integer",
                    "description": "Size of processing batches",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 100
                },
                "continue_on_error": {
                    "type": "boolean",
                    "description": "Continue processing if individual records fail",
                    "default": True
                }
            }
            base_schema["required"] = ["data"]
        
        return base_schema
    
    def _determine_tool_category(self, model_name: str, operation: str) -> str:
        """Determine the category for a tool"""
        
        # Business domain categories
        if model_name in ['Company', 'Customer', 'User']:
            return 'entity_management'
        elif model_name in ['Quote', 'Document']:
            return 'business_operations'
        elif 'Classification' in model_name or 'ETIM' in model_name:
            return 'ai_classification'
        elif model_name in ['ClassificationMetrics', 'ClassificationHistory']:
            return 'analytics_reporting'
        elif 'Queue' in model_name or 'Processing' in model_name:
            return 'workflow_automation'
        else:
            return 'data_management'
    
    def _calculate_complexity_score(self, operation: str, operation_type: str) -> float:
        """Calculate complexity score for performance optimization"""
        
        base_scores = {
            'read': 1.0,
            'list': 2.0,
            'create': 3.0,
            'update': 3.5,
            'delete': 2.5,
            'bulk': 8.0
        }
        
        if operation_type == 'bulk':
            return base_scores['bulk']
        else:
            return base_scores.get(operation, 3.0)
    
    def _estimate_execution_time(self, operation: str, operation_type: str) -> int:
        """Estimate execution time in milliseconds"""
        
        estimates = {
            'read': 50,
            'list': 100,
            'create': 150,
            'update': 200,
            'delete': 100,
            'bulk': 2000
        }
        
        if operation_type == 'bulk':
            return estimates['bulk']
        else:
            return estimates.get(operation, 150)
    
    def _get_required_permissions(self, model_name: str, operation: str) -> List[str]:
        """Get required permissions for operation"""
        
        base_permission = f"{model_name.lower()}:{operation}"
        
        permissions = [base_permission]
        
        # Add category-based permissions
        if operation in ['delete', 'bulk_delete']:
            permissions.append(f"{model_name.lower()}:delete")
        
        if operation.startswith('bulk_'):
            permissions.append(f"{model_name.lower()}:bulk_operations")
        
        if model_name in ['ClassificationMetrics', 'ClassificationHistory']:
            permissions.append("analytics:read")
        
        return permissions
    
    def create_dataflow_workflow(self, model_name: str, operation: str, parameters: Dict[str, Any]) -> WorkflowBuilder:
        """Create optimized workflow for DataFlow operation"""
        
        workflow = WorkflowBuilder()
        
        # Get tool information
        model_tools = self.discovered_tools.get(model_name.lower(), {})
        tool_info = model_tools.get(operation.lower())
        
        if not tool_info:
            raise ToolError(f"Unknown operation {operation} for model {model_name}")
        
        node_name = f"{model_name}{operation.title()}Node"
        
        # Add input validation
        workflow.add_node("ValidationNode", "validate_input", {
            "schema": tool_info['schema'],
            "parameters": parameters,
            "strict_validation": True
        })
        
        # Add the DataFlow operation node
        workflow.add_node(node_name, "dataflow_operation", {
            "model": model_name,
            "operation": operation,
            "parameters": parameters,
            "connection_pool": db.connection_pool if hasattr(db, 'connection_pool') else None,
            "timeout_seconds": tool_info['estimated_time_ms'] / 1000 * 2,  # 2x estimate for timeout
            "enable_caching": tool_info['cacheable'] and self.config.enable_caching,
            "cache_ttl": self.config.cache_ttl_seconds if tool_info['cacheable'] else 0
        })
        
        # Add performance monitoring
        workflow.add_node("PerformanceTrackingNode", "track_performance", {
            "operation": f"{model_name}_{operation}",
            "complexity_score": tool_info['complexity_score'],
            "expected_time_ms": tool_info['estimated_time_ms'],
            "track_memory": operation.startswith('bulk_')
        })
        
        # Add result formatting
        workflow.add_node("ResponseFormatterNode", "format_response", {
            "include_metadata": True,
            "include_performance_info": True,
            "operation_type": tool_info['operation_type']
        })
        
        # Connect workflow
        workflow.connect("validate_input", "dataflow_operation")
        workflow.connect("dataflow_operation", "track_performance")
        workflow.connect("track_performance", "format_response")
        
        return workflow

# ==============================================================================
# AUTHENTICATION AND SESSION MANAGEMENT
# ==============================================================================

class AgentSessionManager:
    """Advanced agent session management with collaboration support"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.active_sessions = {}
        self.session_history = {}
        self.agent_collaborations = defaultdict(set)
        self.session_locks = defaultdict(threading.Lock)
        self._global_lock = threading.Lock()
    
    def create_session(self, agent_id: str, agent_info: Dict[str, Any], auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent session"""
        
        with self._global_lock:
            session_id = hashlib.md5(f"{agent_id}_{time.time()}".encode()).hexdigest()
            
            session = {
                'session_id': session_id,
                'agent_id': agent_id,
                'agent_info': agent_info,
                'auth_context': auth_context,
                'created_at': datetime.utcnow(),
                'last_activity': datetime.utcnow(),
                'request_count': 0,
                'tool_usage_history': [],
                'collaboration_partners': set(),
                'performance_metrics': {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'average_response_time': 0.0
                }
            }
            
            self.active_sessions[session_id] = session
            
            # Check for existing sessions from same agent
            agent_sessions = [s for s in self.active_sessions.values() if s['agent_id'] == agent_id]
            if len(agent_sessions) > self.config.max_agents_per_session:
                # Remove oldest session
                oldest = min(agent_sessions, key=lambda x: x['created_at'])
                del self.active_sessions[oldest['session_id']]
            
            return session
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate and update session activity"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        # Check session timeout
        timeout_minutes = self.config.agent_session_timeout_minutes
        if (datetime.utcnow() - session['last_activity']).total_seconds() > timeout_minutes * 60:
            self.end_session(session_id)
            return None
        
        # Update activity
        session['last_activity'] = datetime.utcnow()
        return session
    
    def record_tool_usage(self, session_id: str, tool_name: str, parameters: Dict[str, Any], 
                         execution_time: float, success: bool):
        """Record tool usage for session"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        with self.session_locks[session_id]:
            session['request_count'] += 1
            session['tool_usage_history'].append({
                'tool_name': tool_name,
                'parameters': parameters,
                'execution_time': execution_time,
                'success': success,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Update performance metrics
            metrics = session['performance_metrics']
            metrics['total_requests'] += 1
            
            if success:
                metrics['successful_requests'] += 1
            else:
                metrics['failed_requests'] += 1
            
            # Update average response time
            current_avg = metrics['average_response_time']
            total_requests = metrics['total_requests']
            metrics['average_response_time'] = (
                (current_avg * (total_requests - 1) + execution_time) / total_requests
            )
            
            # Keep only last 100 tool usages
            if len(session['tool_usage_history']) > 100:
                session['tool_usage_history'] = session['tool_usage_history'][-100:]
    
    def enable_collaboration(self, session_id: str, partner_session_id: str) -> bool:
        """Enable collaboration between agent sessions"""
        
        if not self.config.enable_agent_collaboration:
            return False
        
        session1 = self.active_sessions.get(session_id)
        session2 = self.active_sessions.get(partner_session_id)
        
        if not session1 or not session2:
            return False
        
        # Enable bidirectional collaboration
        session1['collaboration_partners'].add(partner_session_id)
        session2['collaboration_partners'].add(session_id)
        
        self.agent_collaborations[session_id].add(partner_session_id)
        self.agent_collaborations[partner_session_id].add(session_id)
        
        return True
    
    def get_collaboration_context(self, session_id: str) -> Dict[str, Any]:
        """Get collaboration context for session"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return {}
        
        partners = session['collaboration_partners']
        collaboration_context = {
            'active_collaborations': len(partners),
            'partner_sessions': [],
            'shared_tool_usage': {}
        }
        
        for partner_id in partners:
            partner_session = self.active_sessions.get(partner_id)
            if partner_session:
                collaboration_context['partner_sessions'].append({
                    'agent_id': partner_session['agent_id'],
                    'session_id': partner_id,
                    'last_activity': partner_session['last_activity'].isoformat()
                })
        
        return collaboration_context
    
    def end_session(self, session_id: str):
        """End an agent session"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        # Remove from collaborations
        for partner_id in session['collaboration_partners']:
            if partner_id in self.active_sessions:
                self.active_sessions[partner_id]['collaboration_partners'].discard(session_id)
            self.agent_collaborations[partner_id].discard(session_id)
        
        # Move to history
        session['ended_at'] = datetime.utcnow()
        session['duration_minutes'] = (
            session['ended_at'] - session['created_at']
        ).total_seconds() / 60
        
        self.session_history[session_id] = session
        del self.active_sessions[session_id]
        
        # Cleanup locks
        if session_id in self.session_locks:
            del self.session_locks[session_id]
        
        # Keep only last 1000 session histories
        if len(self.session_history) > 1000:
            oldest_sessions = sorted(
                self.session_history.items(),
                key=lambda x: x[1]['ended_at']
            )[:100]
            for old_session_id, _ in oldest_sessions:
                del self.session_history[old_session_id]
    
    def get_session_analytics(self) -> Dict[str, Any]:
        """Get comprehensive session analytics"""
        
        active_count = len(self.active_sessions)
        total_sessions = len(self.session_history) + active_count
        
        # Calculate average session duration
        completed_sessions = [s for s in self.session_history.values() if 'duration_minutes' in s]
        avg_duration = sum(s['duration_minutes'] for s in completed_sessions) / max(len(completed_sessions), 1)
        
        # Most active agents
        agent_request_counts = defaultdict(int)
        for session in list(self.active_sessions.values()) + list(self.session_history.values()):
            agent_request_counts[session['agent_id']] += session.get('request_count', 0)
        
        # Collaboration statistics
        total_collaborations = sum(len(partners) for partners in self.agent_collaborations.values()) // 2
        
        return {
            'active_sessions': active_count,
            'total_sessions_served': total_sessions,
            'average_session_duration_minutes': avg_duration,
            'most_active_agents': dict(Counter(agent_request_counts).most_common(10)),
            'active_collaborations': total_collaborations,
            'collaboration_enabled': self.config.enable_agent_collaboration,
            'session_timeout_minutes': self.config.agent_session_timeout_minutes,
            'max_agents_per_session': self.config.max_agents_per_session
        }

# ==============================================================================
# PRODUCTION MCP SERVER
# ==============================================================================

class ProductionMCPServer:
    """Production-ready MCP server with comprehensive AI agent support"""
    
    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or ServerConfig()
        self.metrics = ServerMetrics()
        self.session_manager = AgentSessionManager(self.config)
        self.tool_discovery = DataFlowToolDiscovery(self.config)
        
        # Initialize core MCP server
        self._init_mcp_server()
        
        # Initialize transport layers
        self.http_app = None
        if self.config.enable_http_transport and FASTAPI_AVAILABLE:
            self._init_http_transport()
        
        # Service registry for discovery
        self.service_registry = ServiceRegistry()
        
        # Circuit breaker and rate limiting
        self.circuit_breaker_state = defaultdict(lambda: {
            'failure_count': 0,
            'last_failure': 0,
            'state': 'closed'  # closed, open, half_open
        })
        
        self.rate_limiter = defaultdict(lambda: {'requests': [], 'violations': 0})
        
        # Performance optimization
        self.thread_pool = ThreadPoolExecutor(max_workers=self.config.max_concurrent_requests // 4)
        
        logger.info("🚀 Production MCP Server initialized with enhanced AI agent support")
    
    def _init_mcp_server(self):
        """Initialize the core MCP server with authentication"""
        
        # Setup authentication provider
        auth_provider = None
        if self.config.enable_auth:
            if self.config.auth_type == "jwt" and JWT_AVAILABLE:
                auth_provider = JWTAuth(
                    secret_key=self.config.jwt_secret,
                    algorithm="HS256"
                )
            elif self.config.auth_type == "api_key":
                # Default API keys for development
                api_keys = {
                    "admin_key": {"permissions": ["*"], "rate_limit": 10000},
                    "agent_key": {"permissions": ["dataflow:*", "tools:*"], "rate_limit": 1000},
                    "readonly_key": {"permissions": ["*:read", "*:list"], "rate_limit": 500}
                }
                auth_provider = APIKeyAuth(api_keys)
            elif self.config.auth_type == "bearer":
                auth_provider = BearerTokenAuth({"valid_token": {"permissions": ["*"]}})
        
        # Create MCP server with production configuration
        self.mcp_server = MCPServer(
            name="production-dataflow-server",
            auth_provider=auth_provider,
            enable_metrics=self.config.enable_metrics,
            enable_cache=self.config.enable_caching,
            cache_ttl=self.config.cache_ttl_seconds,
            circuit_breaker_config={
                "failure_threshold": self.config.circuit_breaker_failure_threshold,
                "recovery_timeout": self.config.circuit_breaker_recovery_timeout,
                "expected_exception": self.config.circuit_breaker_expected_exception
            },
            rate_limit_config={
                "requests_per_minute": self.config.rate_limit_per_minute
            }
        )
        
        # Register all DataFlow tools
        self._register_dataflow_tools()
        
        # Register utility tools
        self._register_utility_tools()
        
        logger.info(f"✅ MCP server initialized with {self.config.auth_type} authentication")
    
    def _register_dataflow_tools(self):
        """Register all DataFlow tools as MCP tools"""
        
        logger.info("🔧 Registering DataFlow tools...")
        
        # Discover all available tools
        discovered_tools = self.tool_discovery.discover_all_tools()
        
        registered_count = 0
        
        for model_name, model_tools in discovered_tools.items():
            for operation, tool_info in model_tools.items():
                tool_name = tool_info['tool_name']
                
                # Create the MCP tool
                @self.mcp_server.tool(
                    name=tool_name,
                    description=tool_info['description'],
                    required_permission=tool_info['required_permissions'][0] if tool_info['required_permissions'] else None,
                    cache_key=tool_name if tool_info['cacheable'] else None,
                    cache_ttl=self.config.cache_ttl_seconds if tool_info['cacheable'] else 0
                )
                async def dataflow_tool_wrapper(parameters: Dict[str, Any], _tool_info=tool_info, _model_name=model_name, _operation=operation) -> Dict[str, Any]:
                    return await self._execute_dataflow_tool(_model_name, _operation, parameters, _tool_info)
                
                # Store tool function for later use
                setattr(self, f"_tool_{tool_name}", dataflow_tool_wrapper)
                
                registered_count += 1
        
        logger.info(f"✅ Registered {registered_count} DataFlow tools")
    
    async def _execute_dataflow_tool(self, model_name: str, operation: str, parameters: Dict[str, Any], tool_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a DataFlow tool with comprehensive error handling and monitoring"""
        
        start_time = time.time()
        agent_id = parameters.get('_agent_id')  # Extract agent ID if provided
        session_id = parameters.get('_session_id')  # Extract session ID if provided
        
        try:
            # Validate session if provided
            session = None
            if session_id:
                session = self.session_manager.validate_session(session_id)
                if not session:
                    raise AuthenticationError("Invalid or expired session")
            
            # Check circuit breaker
            tool_name = tool_info['tool_name']
            if not self._check_circuit_breaker(tool_name):
                raise TransportError(f"Circuit breaker open for tool {tool_name}")
            
            # Check rate limiting
            if not self._check_rate_limit(agent_id or 'anonymous'):
                raise RateLimitError("Rate limit exceeded")
            
            # Update concurrent request count
            self.metrics.concurrent_requests += 1
            
            try:
                # Create and execute workflow
                workflow = self.tool_discovery.create_dataflow_workflow(model_name, operation, parameters)
                
                # Execute with timeout
                timeout = min(self.config.request_timeout_seconds, tool_info['estimated_time_ms'] / 1000 * 3)
                
                runtime = LocalRuntime()
                results, run_id = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        self.thread_pool,
                        lambda: runtime.execute(workflow.build(), parameters)
                    ),
                    timeout=timeout
                )
                
                execution_time = time.time() - start_time
                
                # Record successful execution
                self._record_success(tool_name, execution_time, agent_id, session_id)
                
                # Format response
                response = {
                    "success": True,
                    "data": results,
                    "metadata": {
                        "model": model_name,
                        "operation": operation,
                        "execution_time_ms": round(execution_time * 1000, 2),
                        "run_id": run_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "tool_name": tool_name,
                        "complexity_score": tool_info['complexity_score'],
                        "agent_id": agent_id,
                        "session_id": session_id
                    }
                }
                
                return response
                
            except asyncio.TimeoutError:
                raise ToolError(f"Tool execution timeout after {timeout}s")
                
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Record failure
            self._record_failure(tool_info['tool_name'], execution_time, agent_id, session_id, str(e))
            
            # Return structured error response
            return {
                "success": False,
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "tool_name": tool_info['tool_name'],
                    "model": model_name,
                    "operation": operation,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_id": agent_id,
                    "session_id": session_id
                }
            }
        
        finally:
            self.metrics.concurrent_requests -= 1
    
    def _register_utility_tools(self):
        """Register utility tools for server management and agent coordination"""
        
        @self.mcp_server.tool(
            name="create_agent_session",
            description="Create a new agent session for coordinated tool usage"
        )
        async def create_agent_session(agent_id: str, agent_info: Dict[str, Any] = None, auth_context: Dict[str, Any] = None) -> Dict[str, Any]:
            """Create agent session tool"""
            try:
                session = self.session_manager.create_session(
                    agent_id=agent_id,
                    agent_info=agent_info or {},
                    auth_context=auth_context or {}
                )
                
                self.metrics.start_agent_session(agent_id, session)
                
                return {
                    "success": True,
                    "session_id": session['session_id'],
                    "created_at": session['created_at'].isoformat(),
                    "agent_id": agent_id,
                    "collaboration_enabled": self.config.enable_agent_collaboration
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp_server.tool(
            name="get_available_tools",
            description="Get list of all available tools with metadata"
        )
        async def get_available_tools(category: str = None, model: str = None) -> Dict[str, Any]:
            """Get available tools tool"""
            try:
                tools = []
                
                for model_name, model_tools in self.tool_discovery.discovered_tools.items():
                    if model and model.lower() != model_name:
                        continue
                        
                    for operation, tool_info in model_tools.items():
                        tool_category = None
                        for cat, tool_list in self.tool_discovery.tool_categories.items():
                            if tool_info['tool_name'] in tool_list:
                                tool_category = cat
                                break
                        
                        if category and category != tool_category:
                            continue
                        
                        tools.append({
                            "name": tool_info['tool_name'],
                            "description": tool_info['description'],
                            "model": tool_info['model'],
                            "operation": tool_info['operation'],
                            "category": tool_category,
                            "complexity_score": tool_info['complexity_score'],
                            "estimated_time_ms": tool_info['estimated_time_ms'],
                            "cacheable": tool_info['cacheable'],
                            "required_permissions": tool_info['required_permissions'],
                            "schema": tool_info['schema']
                        })
                
                return {
                    "success": True,
                    "tools": tools,
                    "total_count": len(tools),
                    "categories": list(self.tool_discovery.tool_categories.keys()),
                    "models": list(self.tool_discovery.discovered_tools.keys())
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp_server.tool(
            name="get_server_metrics",
            description="Get comprehensive server performance and usage metrics"
        )
        async def get_server_metrics() -> Dict[str, Any]:
            """Get server metrics tool"""
            try:
                metrics_summary = self.metrics.get_summary()
                session_analytics = self.session_manager.get_session_analytics()
                
                return {
                    "success": True,
                    "server_metrics": metrics_summary,
                    "session_analytics": session_analytics,
                    "server_config": {
                        "max_concurrent_requests": self.config.max_concurrent_requests,
                        "rate_limit_per_minute": self.config.rate_limit_per_minute,
                        "cache_enabled": self.config.enable_caching,
                        "auth_enabled": self.config.enable_auth,
                        "collaboration_enabled": self.config.enable_agent_collaboration
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp_server.tool(
            name="enable_agent_collaboration",
            description="Enable collaboration between two agent sessions"
        )
        async def enable_agent_collaboration(session_id: str, partner_session_id: str) -> Dict[str, Any]:
            """Enable agent collaboration tool"""
            try:
                success = self.session_manager.enable_collaboration(session_id, partner_session_id)
                
                if success:
                    collaboration_context = self.session_manager.get_collaboration_context(session_id)
                    return {
                        "success": True,
                        "message": "Collaboration enabled successfully",
                        "collaboration_context": collaboration_context
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to enable collaboration"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp_server.tool(
            name="health_check",
            description="Comprehensive server health check"
        )
        async def health_check() -> Dict[str, Any]:
            """Health check tool"""
            try:
                # Test database connectivity
                db_healthy = True
                db_error = None
                try:
                    if DATAFLOW_AVAILABLE and hasattr(db, 'connection_pool'):
                        # Test database connection
                        runtime = LocalRuntime()
                        workflow = WorkflowBuilder()
                        workflow.add_node("AsyncSQLQueryNode", "test", {
                            "query": "SELECT 1 as test",
                            "connection_pool": db.connection_pool
                        })
                        runtime.execute(workflow.build())
                except Exception as e:
                    db_healthy = False
                    db_error = str(e)
                
                # Check circuit breaker states
                circuit_breaker_issues = [
                    tool for tool, state in self.circuit_breaker_state.items()
                    if state['state'] == 'open'
                ]
                
                return {
                    "success": True,
                    "health_status": "healthy" if db_healthy and not circuit_breaker_issues else "degraded",
                    "components": {
                        "database": {
                            "status": "healthy" if db_healthy else "unhealthy",
                            "error": db_error
                        },
                        "dataflow_integration": {
                            "status": "healthy" if DATAFLOW_AVAILABLE else "unavailable",
                            "models_available": len(self.tool_discovery.discovered_tools)
                        },
                        "circuit_breakers": {
                            "status": "healthy" if not circuit_breaker_issues else "degraded",
                            "open_breakers": circuit_breaker_issues
                        },
                        "authentication": {
                            "status": "enabled" if self.config.enable_auth else "disabled",
                            "type": self.config.auth_type
                        }
                    },
                    "uptime_seconds": time.time() - self.metrics.start_time,
                    "version": "1.0.0-production",
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                return {
                    "success": False,
                    "health_status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        logger.info("✅ Utility tools registered")
    
    def _check_circuit_breaker(self, tool_name: str) -> bool:
        """Check circuit breaker state for tool"""
        state = self.circuit_breaker_state[tool_name]
        
        if state['state'] == 'open':
            # Check if recovery timeout has passed
            if time.time() - state['last_failure'] > self.config.circuit_breaker_recovery_timeout:
                state['state'] = 'half_open'
                return True
            return False
        
        return True
    
    def _check_rate_limit(self, agent_id: str) -> bool:
        """Check rate limiting for agent"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        agent_requests = self.rate_limiter[agent_id]['requests']
        agent_requests[:] = [req_time for req_time in agent_requests if req_time > minute_ago]
        
        # Check if under limit
        if len(agent_requests) >= self.config.rate_limit_per_minute:
            self.rate_limiter[agent_id]['violations'] += 1
            self.metrics.rate_limit_violations += 1
            return False
        
        # Add current request
        agent_requests.append(now)
        return True
    
    def _record_success(self, tool_name: str, execution_time: float, agent_id: Optional[str], session_id: Optional[str]):
        """Record successful tool execution"""
        self.metrics.record_request(agent_id, execution_time, True, tool_name)
        
        if session_id:
            self.session_manager.record_tool_usage(session_id, tool_name, {}, execution_time, True)
        
        # Reset circuit breaker failure count on success
        if tool_name in self.circuit_breaker_state:
            self.circuit_breaker_state[tool_name]['failure_count'] = 0
            self.circuit_breaker_state[tool_name]['state'] = 'closed'
    
    def _record_failure(self, tool_name: str, execution_time: float, agent_id: Optional[str], session_id: Optional[str], error: str):
        """Record failed tool execution"""
        self.metrics.record_request(agent_id, execution_time, False, tool_name)
        
        if session_id:
            self.session_manager.record_tool_usage(session_id, tool_name, {}, execution_time, False)
        
        # Update circuit breaker
        state = self.circuit_breaker_state[tool_name]
        state['failure_count'] += 1
        state['last_failure'] = time.time()
        
        if state['failure_count'] >= self.config.circuit_breaker_failure_threshold:
            state['state'] = 'open'
            self.metrics.circuit_breaker_trips += 1
            logger.warning(f"Circuit breaker opened for tool {tool_name} after {state['failure_count']} failures")
    
    def _init_http_transport(self):
        """Initialize HTTP transport layer with FastAPI"""
        if not FASTAPI_AVAILABLE:
            logger.warning("FastAPI not available, HTTP transport disabled")
            return
        
        self.http_app = FastAPI(
            title="Production MCP Server",
            description="Production-ready MCP server with AI agent support",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.http_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Security
        security = HTTPBearer()
        
        @self.http_app.middleware("http")
        async def add_performance_headers(request: Request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            response.headers["X-Powered-By"] = "Production-MCP-Server"
            return response
        
        # HTTP endpoints for MCP tool access
        @self.http_app.post("/tools/{tool_name}")
        async def execute_tool_http(tool_name: str, parameters: Dict[str, Any]):
            """Execute MCP tool via HTTP"""
            try:
                # Find tool in discovered tools
                for model_tools in self.tool_discovery.discovered_tools.values():
                    for tool_info in model_tools.values():
                        if tool_info['tool_name'] == tool_name:
                            result = await self._execute_dataflow_tool(
                                tool_info['model'],
                                tool_info['operation'],
                                parameters,
                                tool_info
                            )
                            return JSONResponse(content=result)
                
                return JSONResponse(
                    content={"success": False, "error": f"Tool {tool_name} not found"},
                    status_code=404
                )
            except Exception as e:
                return JSONResponse(
                    content={"success": False, "error": str(e)},
                    status_code=500
                )
        
        @self.http_app.get("/tools")
        async def list_tools_http():
            """List all available tools via HTTP"""
            tools = []
            for model_tools in self.tool_discovery.discovered_tools.values():
                for tool_info in model_tools.values():
                    tools.append({
                        "name": tool_info['tool_name'],
                        "description": tool_info['description'],
                        "model": tool_info['model'],
                        "operation": tool_info['operation']
                    })
            return {"tools": tools, "count": len(tools)}
        
        @self.http_app.get("/metrics")
        async def get_metrics_http():
            """Get server metrics via HTTP"""
            metrics_summary = self.metrics.get_summary()
            session_analytics = self.session_manager.get_session_analytics()
            
            return {
                "server_metrics": metrics_summary,
                "session_analytics": session_analytics,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.http_app.get("/health")
        async def health_check_http():
            """Health check via HTTP"""
            # Use the registered health check tool
            return await self.get_server_metrics()  # This will be defined by the tool registration
        
        logger.info("✅ HTTP transport initialized")
    
    async def start_async(self):
        """Start server asynchronously"""
        logger.info(f"🚀 Starting Production MCP Server on port {self.config.port}")
        
        # Register with service discovery if available
        try:
            await self.service_registry.register_server({
                "id": "production-dataflow-mcp-server",
                "name": "Production DataFlow MCP Server",
                "transport": "stdio",
                "capabilities": list(self.tool_discovery.tool_categories.keys()),
                "metadata": {
                    "version": "1.0.0",
                    "tools_count": sum(len(tools) for tools in self.tool_discovery.discovered_tools.values()),
                    "auth_enabled": self.config.enable_auth,
                    "collaboration_enabled": self.config.enable_agent_collaboration
                }
            })
        except Exception as e:
            logger.warning(f"Service registration failed: {e}")
        
        # Start metrics collection
        if self.config.enable_metrics:
            asyncio.create_task(self._metrics_collection_loop())
        
        # Start HTTP server if enabled
        if self.http_app and self.config.enable_http_transport:
            import uvicorn
            config = uvicorn.Config(
                self.http_app,
                host=self.config.host,
                port=self.config.port + 1,  # HTTP on port + 1
                log_level="info"
            )
            server = uvicorn.Server(config)
            asyncio.create_task(server.serve())
        
        # Start the MCP server
        await self.mcp_server.run()
    
    def start(self):
        """Start server (blocking)"""
        try:
            asyncio.run(self.start_async())
        except KeyboardInterrupt:
            logger.info("\n🛑 Server shutdown requested")
            self.shutdown()
    
    async def _metrics_collection_loop(self):
        """Background metrics collection"""
        while True:
            try:
                await asyncio.sleep(self.config.metrics_collection_interval)
                
                # Update memory usage
                import psutil
                process = psutil.Process()
                self.metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                
                # Clean up expired sessions
                expired_sessions = []
                for session_id, session in self.session_manager.active_sessions.items():
                    if (datetime.utcnow() - session['last_activity']).total_seconds() > self.config.agent_session_timeout_minutes * 60:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    self.session_manager.end_session(session_id)
                
                if expired_sessions:
                    logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
    
    def shutdown(self):
        """Graceful server shutdown"""
        logger.info("🛑 Shutting down Production MCP Server...")
        
        # End all active sessions
        for session_id in list(self.session_manager.active_sessions.keys()):
            self.session_manager.end_session(session_id)
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        # Final metrics report
        final_metrics = self.metrics.get_summary()
        logger.info(f"📊 Final metrics: {final_metrics['total_requests']} requests processed, {final_metrics['error_rate_percent']:.1f}% error rate")
        
        logger.info("✅ Server shutdown complete")

# ==============================================================================
# COMMAND LINE INTERFACE
# ==============================================================================

def main():
    """Main entry point with CLI support"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production MCP Server for AI Agents")
    parser.add_argument("--port", type=int, default=3001, help="Server port")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--auth", choices=["jwt", "api_key", "bearer", "none"], default="jwt", help="Authentication type")
    parser.add_argument("--no-http", action="store_true", help="Disable HTTP transport")
    parser.add_argument("--config-file", help="Path to configuration file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create configuration
    config = ServerConfig(
        port=args.port,
        host=args.host,
        enable_auth=args.auth != "none",
        auth_type=args.auth if args.auth != "none" else "api_key",
        enable_http_transport=not args.no_http
    )
    
    # Load config file if provided
    if args.config_file:
        try:
            import json
            with open(args.config_file, 'r') as f:
                file_config = json.load(f)
            
            # Update config with file values
            for key, value in file_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            logger.info(f"✅ Configuration loaded from {args.config_file}")
        except Exception as e:
            logger.error(f"❌ Failed to load config file: {e}")
            sys.exit(1)
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PRODUCTION MCP SERVER FOR AI AGENTS                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ 🚀 Server Configuration:                                                    ║
║    • Port: {config.port:<10} Host: {config.host:<20}                        ║
║    • Authentication: {config.auth_type:<15} Enabled: {str(config.enable_auth):<10}    ║
║    • Max Concurrent: {config.max_concurrent_requests:<10} Rate Limit: {config.rate_limit_per_minute:<10}/min        ║
║    • HTTP Transport: {str(config.enable_http_transport):<10} Caching: {str(config.enable_caching):<15}      ║
║                                                                              ║
║ 🤖 AI Agent Features:                                                       ║
║    • DataFlow Integration: {str(DATAFLOW_AVAILABLE):<10} JWT Auth: {str(JWT_AVAILABLE):<15}      ║
║    • Agent Sessions: {str(config.enable_agent_collaboration):<15} Max Agents: {config.max_agents_per_session:<10}        ║
║    • Tool Discovery: {str(config.enable_dynamic_tool_discovery):<15} Metrics: {str(config.enable_metrics):<15}        ║
║                                                                              ║
║ 📊 Performance:                                                             ║
║    • Connection Pool: {config.connection_pool_size:<10} Timeout: {config.request_timeout_seconds:<10}s            ║
║    • Circuit Breaker: {config.circuit_breaker_failure_threshold:<10} Cache TTL: {config.cache_ttl_seconds:<10}s         ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Create and start server
    server = ProductionMCPServer(config)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Server interrupted")
    except Exception as e:
        logger.error(f"❌ Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
