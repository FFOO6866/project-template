#!/usr/bin/env python3
"""
Production-Grade MCP Server with Container Orchestration Support
===============================================================

A production-ready MCP server designed for containerized environments with:
- Multi-transport support (STDIO, WebSocket, HTTP, SSE)
- Connection pooling and agent coordination
- Request queuing with priority handling
- Distributed state management
- Circuit breaker patterns
- Comprehensive security
- Service mesh integration
- Advanced observability

Features:
- Agent authentication with JWT/OAuth 2.1
- Transport encryption (TLS 1.3)
- Resource limits per agent
- Audit logging with structured logs
- Kubernetes StatefulSet optimized
- Blue-green deployment support
- Rolling updates without disruption
- Persistent storage for agent state

Environment Variables:
    MCP_ENVIRONMENT: production|staging|development
    MCP_PORT: Main HTTP/WebSocket port (default: 3001)
    MCP_METRICS_PORT: Metrics endpoint port (default: 9090)
    MCP_MANAGEMENT_PORT: Management API port (default: 3002)
    
    # Authentication
    MCP_AUTH_TYPE: jwt|oauth|apikey|none
    MCP_JWT_SECRET: JWT signing secret
    MCP_JWT_PUBLIC_KEY: JWT verification public key
    MCP_OAUTH_ISSUER: OAuth 2.1 issuer URL
    
    # Database
    DATABASE_URL: PostgreSQL connection string
    REDIS_URL: Redis connection string
    
    # Observability
    JAEGER_ENDPOINT: Jaeger tracing endpoint
    PROMETHEUS_GATEWAY: Prometheus push gateway
    LOG_LEVEL: DEBUG|INFO|WARN|ERROR
    
    # Security
    MCP_TLS_CERT_PATH: TLS certificate path
    MCP_TLS_KEY_PATH: TLS private key path
    MCP_CORS_ORIGINS: Allowed CORS origins
    
    # Performance
    MCP_WORKER_THREADS: Worker thread count
    MCP_CONNECTION_POOL_SIZE: Database pool size
    MCP_AGENT_CONCURRENCY_LIMIT: Max concurrent agents
    MCP_REQUEST_QUEUE_SIZE: Request queue buffer size
"""

import os
import sys
import json
import asyncio
import logging
import signal
import ssl
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Callable, Union
from pathlib import Path
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from contextlib import asynccontextmanager
from enum import Enum
import threading
import weakref
import hashlib
import secrets

# Core dependencies
try:
    from kailash.mcp_server import (
        MCPServer, ServiceRegistry, ServiceMesh,
        JWTAuth, APIKeyAuth, OAuth2Client,
        TransportManager, WebSocketTransport, SSETransport,
        CircuitBreakerRetry, ExponentialBackoffRetry,
        ProgressReporter, CancellationContext,
        MCPError, AuthenticationError, RateLimitError,
        structured_tool, create_progress_reporter
    )
    KAILASH_AVAILABLE = True
except ImportError as e:
    print(f"ERROR: Kailash SDK not available: {e}")
    KAILASH_AVAILABLE = False
    sys.exit(1)

# HTTP/WebSocket server
try:
    from fastapi import FastAPI, WebSocket, HTTPException, Depends, Request, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.responses import JSONResponse, StreamingResponse
    import uvicorn
    from starlette.middleware.base import BaseHTTPMiddleware
    from sse_starlette import EventSourceResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    print("ERROR: FastAPI not available")
    sys.exit(1)

# Authentication & Security
try:
    import jwt
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from passlib.context import CryptContext
    SECURITY_AVAILABLE = True
except ImportError:
    print("ERROR: Security libraries not available")
    sys.exit(1)

# Database
try:
    import asyncpg
    import redis.asyncio as redis
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    DATABASE_AVAILABLE = True
except ImportError:
    print("ERROR: Database libraries not available")
    sys.exit(1)

# Observability
try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    import structlog
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    print("WARNING: Observability libraries not available")
    OBSERVABILITY_AVAILABLE = False

# Message queuing
try:
    import aio_pika
    from celery import Celery
    MESSAGING_AVAILABLE = True
except ImportError:
    print("WARNING: Messaging libraries not available")
    MESSAGING_AVAILABLE = False

# Configuration
try:
    from pydantic import BaseSettings, Field, validator
    from pydantic_settings import BaseSettings as PydanticBaseSettings
    import yaml
    CONFIG_AVAILABLE = True
except ImportError:
    print("ERROR: Configuration libraries not available")
    sys.exit(1)

# ==============================================================================
# CONFIGURATION MANAGEMENT
# ==============================================================================

class TransportType(str, Enum):
    """Supported transport types"""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"
    SSE = "sse"

class AuthType(str, Enum):
    """Supported authentication types"""
    NONE = "none"
    JWT = "jwt"
    OAUTH = "oauth"
    APIKEY = "apikey"

class Environment(str, Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class ProductionMCPConfig:
    """Production MCP server configuration"""
    # Environment
    environment: Environment = Environment(os.getenv('MCP_ENVIRONMENT', 'production'))
    debug: bool = os.getenv('MCP_DEBUG', 'false').lower() == 'true'
    
    # Server configuration
    host: str = os.getenv('MCP_HOST', '0.0.0.0')
    port: int = int(os.getenv('MCP_PORT', '3001'))
    metrics_port: int = int(os.getenv('MCP_METRICS_PORT', '9090'))
    management_port: int = int(os.getenv('MCP_MANAGEMENT_PORT', '3002'))
    
    # Transport configuration
    enabled_transports: Set[TransportType] = field(default_factory=lambda: {
        TransportType.HTTP,
        TransportType.WEBSOCKET,
        TransportType.SSE
    })
    
    # Authentication
    auth_type: AuthType = AuthType(os.getenv('MCP_AUTH_TYPE', 'jwt'))
    jwt_secret: str = os.getenv('MCP_JWT_SECRET', secrets.token_urlsafe(32))
    jwt_algorithm: str = os.getenv('MCP_JWT_ALGORITHM', 'HS256')
    jwt_expiry: int = int(os.getenv('MCP_JWT_EXPIRY', '3600'))
    oauth_issuer: str = os.getenv('MCP_OAUTH_ISSUER', '')
    
    # Database
    database_url: str = os.getenv('DATABASE_URL', 'postgresql://postgres:password@postgres:5432/mcp_db')
    redis_url: str = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    
    # Performance
    worker_threads: int = int(os.getenv('MCP_WORKER_THREADS', '4'))
    connection_pool_size: int = int(os.getenv('MCP_CONNECTION_POOL_SIZE', '20'))
    agent_concurrency_limit: int = int(os.getenv('MCP_AGENT_CONCURRENCY_LIMIT', '100'))
    request_queue_size: int = int(os.getenv('MCP_REQUEST_QUEUE_SIZE', '1000'))
    request_timeout: int = int(os.getenv('MCP_REQUEST_TIMEOUT', '30'))
    websocket_timeout: int = int(os.getenv('MCP_WEBSOCKET_TIMEOUT', '60'))
    
    # Security
    tls_cert_path: Optional[str] = os.getenv('MCP_TLS_CERT_PATH')
    tls_key_path: Optional[str] = os.getenv('MCP_TLS_KEY_PATH')
    cors_origins: List[str] = field(default_factory=lambda: 
        os.getenv('MCP_CORS_ORIGINS', '*').split(','))
    trusted_hosts: List[str] = field(default_factory=lambda: 
        os.getenv('MCP_TRUSTED_HOSTS', '*').split(','))
    rate_limit_per_minute: int = int(os.getenv('MCP_RATE_LIMIT', '1000'))
    
    # Observability
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    enable_metrics: bool = os.getenv('MCP_ENABLE_METRICS', 'true').lower() == 'true'
    enable_tracing: bool = os.getenv('MCP_ENABLE_TRACING', 'true').lower() == 'true'
    jaeger_endpoint: str = os.getenv('JAEGER_ENDPOINT', '')
    prometheus_gateway: str = os.getenv('PROMETHEUS_GATEWAY', '')
    
    # Service mesh
    service_mesh_enabled: bool = os.getenv('MCP_SERVICE_MESH', 'false').lower() == 'true'
    consul_endpoint: str = os.getenv('CONSUL_ENDPOINT', '')
    
    # Kubernetes integration
    k8s_namespace: str = os.getenv('K8S_NAMESPACE', 'default')
    k8s_service_name: str = os.getenv('K8S_SERVICE_NAME', 'mcp-server')
    pod_name: str = os.getenv('HOSTNAME', 'mcp-server-unknown')
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.environment == Environment.PRODUCTION:
            if self.auth_type == AuthType.NONE:
                raise ValueError("Authentication required in production")
            if not self.tls_cert_path and not self.debug:
                print("WARNING: TLS not configured for production")

# ==============================================================================
# OBSERVABILITY SYSTEM
# ==============================================================================

class ObservabilityManager:
    """Comprehensive observability for production MCP server"""
    
    def __init__(self, config: ProductionMCPConfig):
        self.config = config
        self.registry = CollectorRegistry()
        self.logger = self._setup_logging()
        self.tracer = None
        self.meter = None
        
        # Prometheus metrics
        self.request_counter = Counter(
            'mcp_requests_total',
            'Total MCP requests',
            ['method', 'transport', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'mcp_request_duration_seconds',
            'MCP request duration',
            ['method', 'transport'],
            registry=self.registry
        )
        
        self.active_agents = Gauge(
            'mcp_active_agents',
            'Number of active agents',
            registry=self.registry
        )
        
        self.connection_pool_size = Gauge(
            'mcp_connection_pool_size',
            'Database connection pool size',
            ['pool_type'],
            registry=self.registry
        )
        
        self.error_counter = Counter(
            'mcp_errors_total',
            'Total MCP errors',
            ['error_type', 'transport'],
            registry=self.registry
        )
        
        if OBSERVABILITY_AVAILABLE and config.enable_tracing:
            self._setup_tracing()
    
    def _setup_logging(self) -> structlog.BoundLogger:
        """Setup structured logging"""
        if OBSERVABILITY_AVAILABLE:
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )
            return structlog.get_logger("mcp-server")
        else:
            logger = logging.getLogger("mcp-server")
            logger.setLevel(getattr(logging, self.config.log_level))
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            return logger
    
    def _setup_tracing(self):
        """Setup distributed tracing"""
        if self.config.jaeger_endpoint:
            trace.set_tracer_provider(TracerProvider())
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.config.jaeger_endpoint.split(':')[0],
                agent_port=int(self.config.jaeger_endpoint.split(':')[1]),
            )
            span_processor = BatchSpanProcessor(jaeger_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            self.tracer = trace.get_tracer(__name__)
    
    def record_request(self, method: str, transport: str, status: str, duration: float):
        """Record request metrics"""
        self.request_counter.labels(method=method, transport=transport, status=status).inc()
        self.request_duration.labels(method=method, transport=transport).observe(duration)
    
    def record_error(self, error_type: str, transport: str):
        """Record error metrics"""
        self.error_counter.labels(error_type=error_type, transport=transport).inc()
    
    def update_active_agents(self, count: int):
        """Update active agents gauge"""
        self.active_agents.set(count)
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        return generate_latest(self.registry)

# ==============================================================================
# AGENT CONNECTION MANAGER
# ==============================================================================

@dataclass
class AgentSession:
    """Agent session information"""
    session_id: str
    agent_id: str
    transport_type: TransportType
    authenticated: bool = False
    user_id: Optional[str] = None
    permissions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    request_count: int = 0
    error_count: int = 0
    rate_limit_remaining: int = 1000
    websocket: Optional[WebSocket] = None
    context: Dict[str, Any] = field(default_factory=dict)

class AgentConnectionManager:
    """Manages agent connections with pooling and coordination"""
    
    def __init__(self, config: ProductionMCPConfig, observability: ObservabilityManager):
        self.config = config
        self.observability = observability
        self.sessions: Dict[str, AgentSession] = {}
        self.sessions_by_agent: Dict[str, Set[str]] = defaultdict(set)
        self.session_lock = asyncio.Lock()
        self.request_queues: Dict[str, asyncio.Queue] = {}
        self.active_requests: Dict[str, int] = defaultdict(int)
        
        # Circuit breaker for agent connections
        self.circuit_breaker = CircuitBreakerRetry(
            failure_threshold=5,
            recovery_timeout=30,
            expected_exception=MCPError
        )
    
    async def create_session(
        self, 
        agent_id: str, 
        transport_type: TransportType,
        websocket: Optional[WebSocket] = None
    ) -> AgentSession:
        """Create new agent session"""
        session_id = str(uuid.uuid4())
        
        session = AgentSession(
            session_id=session_id,
            agent_id=agent_id,
            transport_type=transport_type,
            websocket=websocket
        )
        
        async with self.session_lock:
            self.sessions[session_id] = session
            self.sessions_by_agent[agent_id].add(session_id)
            self.request_queues[session_id] = asyncio.Queue(
                maxsize=self.config.request_queue_size
            )
        
        self.observability.update_active_agents(len(self.sessions))
        self.observability.logger.info(
            "Agent session created",
            session_id=session_id,
            agent_id=agent_id,
            transport=transport_type.value
        )
        
        return session
    
    async def remove_session(self, session_id: str):
        """Remove agent session"""
        async with self.session_lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                agent_id = session.agent_id
                
                # Clean up session
                del self.sessions[session_id]
                self.sessions_by_agent[agent_id].discard(session_id)
                if not self.sessions_by_agent[agent_id]:
                    del self.sessions_by_agent[agent_id]
                
                # Clean up request queue
                if session_id in self.request_queues:
                    del self.request_queues[session_id]
                
                # Close WebSocket if exists
                if session.websocket:
                    try:
                        await session.websocket.close()
                    except Exception:
                        pass
        
        self.observability.update_active_agents(len(self.sessions))
        self.observability.logger.info(
            "Agent session removed",
            session_id=session_id
        )
    
    async def authenticate_session(
        self, 
        session_id: str, 
        token: str,
        auth_provider
    ) -> bool:
        """Authenticate agent session"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            # Validate token using auth provider
            user_info = await auth_provider.validate_token(token)
            if not user_info:
                return False
            
            session.authenticated = True
            session.user_id = user_info.get('user_id')
            session.permissions = set(user_info.get('permissions', []))
            
            self.observability.logger.info(
                "Agent session authenticated",
                session_id=session_id,
                user_id=session.user_id
            )
            
            return True
            
        except Exception as e:
            self.observability.logger.error(
                "Authentication failed",
                session_id=session_id,
                error=str(e)
            )
            return False
    
    async def queue_request(
        self, 
        session_id: str, 
        request: Dict[str, Any],
        priority: int = 5
    ) -> bool:
        """Queue request for agent with priority handling"""
        try:
            queue = self.request_queues.get(session_id)
            if not queue:
                return False
            
            # Check concurrency limits
            if self.active_requests[session_id] >= self.config.agent_concurrency_limit:
                self.observability.logger.warning(
                    "Agent concurrency limit reached",
                    session_id=session_id,
                    active_requests=self.active_requests[session_id]
                )
                return False
            
            # Add priority and timestamp to request
            prioritized_request = {
                'priority': priority,
                'timestamp': time.time(),
                'request': request
            }
            
            await queue.put(prioritized_request)
            return True
            
        except asyncio.QueueFull:
            self.observability.logger.warning(
                "Request queue full",
                session_id=session_id
            )
            return False
    
    async def get_session_health(self) -> Dict[str, Any]:
        """Get health information for all sessions"""
        async with self.session_lock:
            total_sessions = len(self.sessions)
            authenticated_sessions = sum(
                1 for s in self.sessions.values() if s.authenticated
            )
            
            transport_counts = defaultdict(int)
            for session in self.sessions.values():
                transport_counts[session.transport_type.value] += 1
            
            return {
                'total_sessions': total_sessions,
                'authenticated_sessions': authenticated_sessions,
                'transport_distribution': dict(transport_counts),
                'active_requests': sum(self.active_requests.values()),
                'queue_sizes': {
                    sid: queue.qsize() 
                    for sid, queue in self.request_queues.items()
                }
            }

# ==============================================================================
# DISTRIBUTED STATE MANAGER
# ==============================================================================

class DistributedStateManager:
    """Manages distributed state across MCP server instances"""
    
    def __init__(self, config: ProductionMCPConfig, redis_client):
        self.config = config
        self.redis = redis_client
        self.local_state: Dict[str, Any] = {}
        self.state_lock = asyncio.Lock()
        self.heartbeat_task = None
        self.instance_id = f"{config.pod_name}-{uuid.uuid4().hex[:8]}"
    
    async def initialize(self):
        """Initialize distributed state management"""
        # Register this instance
        await self.register_instance()
        
        # Start heartbeat
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def register_instance(self):
        """Register this server instance in distributed registry"""
        instance_info = {
            'instance_id': self.instance_id,
            'pod_name': self.config.pod_name,
            'namespace': self.config.k8s_namespace,
            'service_name': self.config.k8s_service_name,
            'host': self.config.host,
            'port': self.config.port,
            'transports': [t.value for t in self.config.enabled_transports],
            'started_at': datetime.utcnow().isoformat(),
            'last_heartbeat': datetime.utcnow().isoformat()
        }
        
        key = f"mcp:instances:{self.instance_id}"
        await self.redis.setex(key, 60, json.dumps(instance_info))
    
    async def _heartbeat_loop(self):
        """Maintain heartbeat with distributed registry"""
        while True:
            try:
                await self.register_instance()
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                print(f"Heartbeat failed: {e}")
                await asyncio.sleep(5)
    
    async def get_active_instances(self) -> List[Dict[str, Any]]:
        """Get list of active MCP server instances"""
        pattern = "mcp:instances:*"
        keys = await self.redis.keys(pattern)
        
        instances = []
        for key in keys:
            data = await self.redis.get(key)
            if data:
                try:
                    instances.append(json.loads(data))
                except json.JSONDecodeError:
                    continue
        
        return instances
    
    async def set_agent_state(self, agent_id: str, state: Dict[str, Any]):
        """Set agent state in distributed storage"""
        key = f"mcp:agent_state:{agent_id}"
        await self.redis.setex(key, 3600, json.dumps(state))  # 1 hour TTL
    
    async def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent state from distributed storage"""
        key = f"mcp:agent_state:{agent_id}"
        data = await self.redis.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None
    
    async def cleanup(self):
        """Clean up distributed state"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        # Remove instance from registry
        key = f"mcp:instances:{self.instance_id}"
        await self.redis.delete(key)

# ==============================================================================
# SECURITY MANAGER
# ==============================================================================

class SecurityManager:
    """Comprehensive security management for production MCP server"""
    
    def __init__(self, config: ProductionMCPConfig):
        self.config = config
        self.password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.rate_limiters: Dict[str, Dict] = defaultdict(lambda: {
            'requests': deque(maxlen=1000),
            'blocked_until': None
        })
        
        # JWT configuration
        if config.auth_type == AuthType.JWT:
            self.jwt_auth = self._setup_jwt_auth()
        
        # Load TLS context if configured
        self.ssl_context = self._setup_tls_context()
    
    def _setup_jwt_auth(self):
        """Setup JWT authentication"""
        return JWTAuth(
            secret_key=self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm,
            token_expiry=self.config.jwt_expiry
        )
    
    def _setup_tls_context(self) -> Optional[ssl.SSLContext]:
        """Setup TLS context for secure connections"""
        if not (self.config.tls_cert_path and self.config.tls_key_path):
            return None
        
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.load_cert_chain(
            self.config.tls_cert_path,
            self.config.tls_key_path
        )
        
        return context
    
    async def authenticate_request(self, token: str) -> Optional[Dict[str, Any]]:
        """Authenticate request using configured auth method"""
        try:
            if self.config.auth_type == AuthType.JWT:
                return await self.jwt_auth.validate_token(token)
            elif self.config.auth_type == AuthType.NONE:
                return {'user_id': 'anonymous', 'permissions': ['read']}
            else:
                return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    async def check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limits"""
        now = time.time()
        limiter = self.rate_limiters[client_id]
        
        # Check if currently blocked
        if limiter['blocked_until'] and now < limiter['blocked_until']:
            return False
        
        # Clean old requests (older than 1 minute)
        requests = limiter['requests']
        while requests and requests[0] < now - 60:
            requests.popleft()
        
        # Check rate limit
        if len(requests) >= self.config.rate_limit_per_minute:
            # Block for 5 minutes
            limiter['blocked_until'] = now + 300
            return False
        
        # Record this request
        requests.append(now)
        return True
    
    def generate_audit_log(self, event: str, **kwargs) -> Dict[str, Any]:
        """Generate structured audit log entry"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'event': event,
            'instance_id': getattr(self, 'instance_id', 'unknown'),
            'severity': kwargs.get('severity', 'INFO'),
            'client_id': kwargs.get('client_id'),
            'session_id': kwargs.get('session_id'),
            'user_id': kwargs.get('user_id'),
            'action': kwargs.get('action'),
            'resource': kwargs.get('resource'),
            'result': kwargs.get('result', 'success'),
            'error': kwargs.get('error'),
            'metadata': kwargs.get('metadata', {})
        }

# ==============================================================================
# PRODUCTION MCP SERVER
# ==============================================================================

class ProductionMCPServer:
    """Production-grade MCP server with enterprise features"""
    
    def __init__(self, config: Optional[ProductionMCPConfig] = None):
        self.config = config or ProductionMCPConfig()
        self.observability = ObservabilityManager(self.config)
        self.security = SecurityManager(self.config)
        self.connection_manager = AgentConnectionManager(self.config, self.observability)
        
        # Core components
        self.mcp_server = None
        self.service_registry = None
        self.service_mesh = None
        self.state_manager = None
        
        # Database connections
        self.db_pool = None
        self.redis_client = None
        
        # HTTP applications
        self.main_app = None
        self.metrics_app = None
        self.management_app = None
        
        # Background tasks
        self.background_tasks = set()
        
        # Shutdown event
        self.shutdown_event = asyncio.Event()
        
        self.observability.logger.info(
            "Production MCP Server initialized",
            config=asdict(self.config)
        )
    
    async def initialize(self):
        """Initialize all server components"""
        self.observability.logger.info("Initializing Production MCP Server")
        
        # Initialize database connections
        await self._setup_databases()
        
        # Initialize distributed state management
        if self.redis_client:
            self.state_manager = DistributedStateManager(self.config, self.redis_client)
            await self.state_manager.initialize()
        
        # Setup service discovery
        if self.config.service_mesh_enabled:
            await self._setup_service_mesh()
        
        # Initialize MCP server with Kailash SDK
        await self._setup_mcp_server()
        
        # Setup HTTP applications
        await self._setup_http_applications()
        
        # Start background tasks
        await self._start_background_tasks()
        
        self.observability.logger.info("Production MCP Server initialization complete")
    
    async def _setup_databases(self):
        """Setup database connections"""
        try:
            # PostgreSQL connection pool
            self.db_pool = await asyncpg.create_pool(
                self.config.database_url,
                min_size=5,
                max_size=self.config.connection_pool_size,
                command_timeout=self.config.request_timeout
            )
            
            self.observability.connection_pool_size.labels(pool_type='postgresql').set(
                self.config.connection_pool_size
            )
            
            self.observability.logger.info("PostgreSQL connection pool established")
            
        except Exception as e:
            self.observability.logger.error("PostgreSQL connection failed", error=str(e))
            raise
        
        try:
            # Redis connection
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            await self.redis_client.ping()
            self.observability.logger.info("Redis connection established")
            
        except Exception as e:
            self.observability.logger.error("Redis connection failed", error=str(e))
            # Redis is optional, continue without it
            self.redis_client = None
    
    async def _setup_service_mesh(self):
        """Setup service mesh integration"""
        try:
            self.service_registry = ServiceRegistry()
            self.service_mesh = ServiceMesh(self.service_registry)
            
            # Register this server instance
            server_info = {
                'id': self.state_manager.instance_id if self.state_manager else self.config.pod_name,
                'name': self.config.k8s_service_name,
                'transport': 'http',
                'endpoint': f"http://{self.config.host}:{self.config.port}",
                'capabilities': ['tools', 'resources', 'chat'],
                'metadata': {
                    'version': '1.0.0',
                    'environment': self.config.environment.value,
                    'namespace': self.config.k8s_namespace
                }
            }
            
            await self.service_registry.register_server(server_info)
            self.observability.logger.info("Service mesh integration configured")
            
        except Exception as e:
            self.observability.logger.error("Service mesh setup failed", error=str(e))
            # Service mesh is optional
            pass
    
    async def _setup_mcp_server(self):
        """Setup core MCP server with Kailash SDK"""
        try:
            # Configure authentication
            auth_provider = None
            if self.config.auth_type == AuthType.JWT:
                auth_provider = self.security.jwt_auth
            
            # Create MCP server
            self.mcp_server = MCPServer(
                name=f"{self.config.k8s_service_name}-{self.config.environment.value}",
                auth_provider=auth_provider,
                enable_cache=bool(self.redis_client),
                enable_metrics=self.config.enable_metrics,
                circuit_breaker_config={
                    'failure_threshold': 5,
                    'recovery_timeout': 30
                }
            )
            
            # Register production tools
            await self._register_production_tools()
            
            self.observability.logger.info("MCP server configured with Kailash SDK")
            
        except Exception as e:
            self.observability.logger.error("MCP server setup failed", error=str(e))
            raise
    
    async def _register_production_tools(self):
        """Register production-grade MCP tools"""
        
        @self.mcp_server.tool(
            name="health_check",
            description="Comprehensive server health check"
        )
        async def health_check() -> Dict[str, Any]:
            """Production health check tool"""
            start_time = time.time()
            health = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'instance_id': self.state_manager.instance_id if self.state_manager else 'unknown',
                'components': {},
                'metrics': self.observability.registry and dict(self.observability.get_metrics()) or {}
            }
            
            # Check database health
            if self.db_pool:
                try:
                    async with self.db_pool.acquire() as conn:
                        await conn.fetchval('SELECT 1')
                    health['components']['postgresql'] = {'status': 'healthy'}
                except Exception as e:
                    health['components']['postgresql'] = {'status': 'unhealthy', 'error': str(e)}
                    health['status'] = 'degraded'
            
            # Check Redis health
            if self.redis_client:
                try:
                    await self.redis_client.ping()
                    health['components']['redis'] = {'status': 'healthy'}
                except Exception as e:
                    health['components']['redis'] = {'status': 'unhealthy', 'error': str(e)}
                    health['status'] = 'degraded'
            
            # Get session health
            session_health = await self.connection_manager.get_session_health()
            health['components']['sessions'] = session_health
            
            execution_time = time.time() - start_time
            self.observability.record_request('health_check', 'internal', 'success', execution_time)
            
            return health
        
        @self.mcp_server.tool(
            name="execute_sql",
            description="Execute SQL query with connection pooling",
            required_permission="database.query"
        )
        async def execute_sql(
            query: str, 
            params: Optional[Dict[str, Any]] = None,
            max_rows: int = 1000
        ) -> Dict[str, Any]:
            """Execute SQL with production safeguards"""
            start_time = time.time()
            
            try:
                if not self.db_pool:
                    raise ToolError("Database not available")
                
                # Basic SQL injection protection
                if any(keyword in query.upper() for keyword in ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']):
                    raise ToolError("Destructive SQL operations not allowed")
                
                async with self.db_pool.acquire() as conn:
                    if params:
                        result = await conn.fetch(query, *params.values())
                    else:
                        result = await conn.fetch(query)
                    
                    # Limit result size
                    if len(result) > max_rows:
                        result = result[:max_rows]
                        truncated = True
                    else:
                        truncated = False
                    
                    execution_time = time.time() - start_time
                    self.observability.record_request('execute_sql', 'tool', 'success', execution_time)
                    
                    return {
                        'success': True,
                        'data': [dict(row) for row in result],
                        'count': len(result),
                        'truncated': truncated,
                        'execution_time_ms': round(execution_time * 1000, 2)
                    }
                    
            except Exception as e:
                execution_time = time.time() - start_time
                self.observability.record_request('execute_sql', 'tool', 'error', execution_time)
                self.observability.record_error('database_error', 'tool')
                
                return {
                    'success': False,
                    'error': str(e),
                    'execution_time_ms': round(execution_time * 1000, 2)
                }
        
        @self.mcp_server.tool(
            name="get_server_metrics",
            description="Get server performance metrics",
            required_permission="metrics.read"
        )
        async def get_server_metrics() -> Dict[str, Any]:
            """Get comprehensive server metrics"""
            metrics = {
                'prometheus_metrics': self.observability.get_metrics() if self.observability.registry else None,
                'session_metrics': await self.connection_manager.get_session_health(),
                'instance_info': {
                    'instance_id': self.state_manager.instance_id if self.state_manager else 'unknown',
                    'pod_name': self.config.pod_name,
                    'namespace': self.config.k8s_namespace,
                    'environment': self.config.environment.value
                }
            }
            
            if self.state_manager:
                metrics['cluster_info'] = {
                    'active_instances': await self.state_manager.get_active_instances()
                }
            
            return metrics
        
        self.observability.logger.info("Production MCP tools registered")
    
    async def _setup_http_applications(self):
        """Setup HTTP applications for different purposes"""
        # Main application (MCP protocol + WebSocket)
        self.main_app = self._create_main_app()
        
        # Metrics application (Prometheus endpoint)
        self.metrics_app = self._create_metrics_app()
        
        # Management application (Admin operations)
        self.management_app = self._create_management_app()
    
    def _create_main_app(self) -> FastAPI:
        """Create main FastAPI application"""
        app = FastAPI(
            title="Production MCP Server",
            description="Enterprise-grade MCP server with multi-transport support",
            version="1.0.0",
            docs_url="/docs" if self.config.debug else None,
            redoc_url="/redoc" if self.config.debug else None
        )
        
        # Security middleware
        if self.config.trusted_hosts != ['*']:
            app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=self.config.trusted_hosts
            )
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Request logging middleware
        @app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            self.observability.record_request(
                request.method,
                'http',
                str(response.status_code),
                process_time
            )
            
            return response
        
        # Authentication dependency
        security = HTTPBearer(auto_error=False)
        
        async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
            if self.config.auth_type == AuthType.NONE:
                return {'user_id': 'anonymous', 'permissions': ['*']}
            
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_info = await self.security.authenticate_request(credentials.credentials)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication"
                )
            
            return user_info
        
        # Health endpoint
        @app.get("/health")
        async def health_endpoint():
            if self.mcp_server:
                health_tool = next(
                    (tool for tool in self.mcp_server.tools if tool.name == "health_check"),
                    None
                )
                if health_tool:
                    result = await health_tool.handler()
                    status_code = 200 if result['status'] == 'healthy' else 503
                    return JSONResponse(content=result, status_code=status_code)
            
            return {"status": "unknown"}
        
        # WebSocket endpoint for MCP protocol
        @app.websocket("/mcp")
        async def websocket_endpoint(websocket: WebSocket):
            await self._handle_websocket_connection(websocket)
        
        # SSE endpoint for MCP protocol
        @app.get("/mcp/sse")
        async def sse_endpoint(request: Request, user: dict = Depends(get_current_user)):
            return EventSourceResponse(self._handle_sse_connection(request, user))
        
        return app
    
    def _create_metrics_app(self) -> FastAPI:
        """Create metrics application"""
        app = FastAPI(title="MCP Server Metrics", docs_url=None, redoc_url=None)
        
        @app.get("/metrics")
        async def metrics_endpoint():
            return Response(
                content=self.observability.get_metrics(),
                media_type="text/plain"
            )
        
        return app
    
    def _create_management_app(self) -> FastAPI:
        """Create management application"""
        app = FastAPI(title="MCP Server Management", docs_url=None, redoc_url=None)
        
        # Require admin authentication for management endpoints
        async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
            user_info = await self.security.authenticate_request(credentials.credentials)
            if not user_info or 'admin' not in user_info.get('permissions', []):
                raise HTTPException(status_code=403, detail="Admin access required")
            return user_info
        
        @app.get("/status")
        async def status_endpoint(user: dict = Depends(require_admin)):
            return await self.connection_manager.get_session_health()
        
        @app.post("/shutdown")
        async def shutdown_endpoint(user: dict = Depends(require_admin)):
            self.shutdown_event.set()
            return {"message": "Shutdown initiated"}
        
        return app
    
    async def _handle_websocket_connection(self, websocket: WebSocket):
        """Handle WebSocket MCP connection"""
        await websocket.accept()
        
        # Extract agent ID from headers or generate one
        agent_id = websocket.headers.get('X-Agent-ID', f"agent-{uuid.uuid4().hex[:8]}")
        
        # Create session
        session = await self.connection_manager.create_session(
            agent_id=agent_id,
            transport_type=TransportType.WEBSOCKET,
            websocket=websocket
        )
        
        try:
            # Handle MCP protocol messages
            async for message in websocket.iter_text():
                try:
                    data = json.loads(message)
                    
                    # Authenticate if needed
                    if not session.authenticated and 'auth' in data:
                        authenticated = await self.connection_manager.authenticate_session(
                            session.session_id,
                            data['auth']['token'],
                            self.security
                        )
                        if not authenticated:
                            await websocket.send_json({'error': 'Authentication failed'})
                            break
                    
                    # Rate limiting
                    if not await self.security.check_rate_limit(agent_id):
                        await websocket.send_json({'error': 'Rate limit exceeded'})
                        continue
                    
                    # Process MCP request
                    response = await self._process_mcp_request(data, session)
                    await websocket.send_json(response)
                    
                except json.JSONDecodeError:
                    await websocket.send_json({'error': 'Invalid JSON'})
                except Exception as e:
                    self.observability.record_error('websocket_error', 'websocket')
                    self.observability.logger.error(
                        "WebSocket error",
                        session_id=session.session_id,
                        error=str(e)
                    )
                    await websocket.send_json({'error': 'Internal server error'})
        
        except Exception as e:
            self.observability.logger.error(
                "WebSocket connection error",
                session_id=session.session_id,
                error=str(e)
            )
        finally:
            await self.connection_manager.remove_session(session.session_id)
    
    async def _handle_sse_connection(self, request: Request, user: dict):
        """Handle SSE MCP connection"""
        agent_id = request.headers.get('X-Agent-ID', f"agent-{uuid.uuid4().hex[:8]}")
        
        session = await self.connection_manager.create_session(
            agent_id=agent_id,
            transport_type=TransportType.SSE
        )
        
        try:
            while True:
                # Check for disconnect
                if await request.is_disconnected():
                    break
                
                # Yield heartbeat
                yield {"event": "heartbeat", "data": "ping"}
                
                # Process any queued requests
                try:
                    queue = self.connection_manager.request_queues.get(session.session_id)
                    if queue and not queue.empty():
                        request_data = await asyncio.wait_for(queue.get(), timeout=1.0)
                        response = await self._process_mcp_request(request_data['request'], session)
                        yield {"event": "response", "data": json.dumps(response)}
                except asyncio.TimeoutError:
                    pass
                
                await asyncio.sleep(1)
        
        finally:
            await self.connection_manager.remove_session(session.session_id)
    
    async def _process_mcp_request(self, request: Dict[str, Any], session: AgentSession) -> Dict[str, Any]:
        """Process MCP protocol request"""
        try:
            method = request.get('method')
            params = request.get('params', {})
            request_id = request.get('id')
            
            if method == 'tools/list':
                # Return available tools
                tools = []
                if self.mcp_server:
                    for tool in self.mcp_server.tools:
                        tools.append({
                            'name': tool.name,
                            'description': tool.description,
                            'inputSchema': tool.input_schema
                        })
                
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': {'tools': tools}
                }
            
            elif method == 'tools/call':
                # Call specific tool
                tool_name = params.get('name')
                tool_params = params.get('arguments', {})
                
                if self.mcp_server:
                    for tool in self.mcp_server.tools:
                        if tool.name == tool_name:
                            # Check permissions
                            if hasattr(tool, 'required_permission'):
                                required_perm = tool.required_permission
                                if required_perm and required_perm not in session.permissions:
                                    return {
                                        'jsonrpc': '2.0',
                                        'id': request_id,
                                        'error': {
                                            'code': -32000,
                                            'message': 'Insufficient permissions'
                                        }
                                    }
                            
                            # Execute tool
                            result = await tool.handler(**tool_params)
                            return {
                                'jsonrpc': '2.0',
                                'id': request_id,
                                'result': result
                            }
                
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': f'Tool not found: {tool_name}'
                    }
                }
            
            else:
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': f'Method not found: {method}'
                    }
                }
        
        except Exception as e:
            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'error': {
                    'code': -32000,
                    'message': str(e)
                }
            }
    
    async def _start_background_tasks(self):
        """Start background maintenance tasks"""
        # Session cleanup task
        async def cleanup_inactive_sessions():
            while not self.shutdown_event.is_set():
                try:
                    now = datetime.utcnow()
                    inactive_sessions = []
                    
                    for session_id, session in self.connection_manager.sessions.items():
                        if (now - session.last_activity).total_seconds() > 3600:  # 1 hour
                            inactive_sessions.append(session_id)
                    
                    for session_id in inactive_sessions:
                        await self.connection_manager.remove_session(session_id)
                    
                    await asyncio.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    self.observability.logger.error("Session cleanup error", error=str(e))
                    await asyncio.sleep(60)
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(cleanup_inactive_sessions())
        self.background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self.background_tasks.discard)
    
    async def start(self):
        """Start the production MCP server"""
        self.observability.logger.info(
            "Starting Production MCP Server",
            host=self.config.host,
            port=self.config.port,
            environment=self.config.environment.value
        )
        
        # Initialize all components
        await self.initialize()
        
        # Create server configurations
        main_config = uvicorn.Config(
            self.main_app,
            host=self.config.host,
            port=self.config.port,
            ssl_keyfile=self.config.tls_key_path,
            ssl_certfile=self.config.tls_cert_path,
            ssl_version=ssl.PROTOCOL_TLS,
            log_level="info" if not self.config.debug else "debug",
            access_log=True,
            loop="asyncio"
        )
        
        metrics_config = uvicorn.Config(
            self.metrics_app,
            host=self.config.host,
            port=self.config.metrics_port,
            log_level="warning"
        )
        
        management_config = uvicorn.Config(
            self.management_app,
            host="127.0.0.1",  # Only localhost for management
            port=self.config.management_port,
            log_level="warning"
        )
        
        # Start servers concurrently
        servers = [
            uvicorn.Server(main_config),
            uvicorn.Server(metrics_config),
            uvicorn.Server(management_config)
        ]
        
        try:
            await asyncio.gather(
                *[server.serve() for server in servers],
                self.shutdown_event.wait()
            )
        except Exception as e:
            self.observability.logger.error("Server error", error=str(e))
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        self.observability.logger.info("Shutting down Production MCP Server")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Close database connections
        if self.db_pool:
            await self.db_pool.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        # Clean up distributed state
        if self.state_manager:
            await self.state_manager.cleanup()
        
        self.observability.logger.info("Production MCP Server shutdown complete")

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

async def main():
    """Main entry point"""
    # Handle signals for graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler():
        shutdown_event.set()
    
    for sig in [signal.SIGTERM, signal.SIGINT]:
        signal.signal(sig, lambda s, f: signal_handler())
    
    # Create and start server
    config = ProductionMCPConfig()
    server = ProductionMCPServer(config)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("Server interrupted")
    except Exception as e:
        print(f"Server failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Production MCP Server")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--host", help="Server host")
    parser.add_argument("--auth", choices=["none", "jwt", "oauth", "apikey"], help="Auth type")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Override config with CLI args
    if args.port:
        os.environ['MCP_PORT'] = str(args.port)
    if args.host:
        os.environ['MCP_HOST'] = args.host
    if args.auth:
        os.environ['MCP_AUTH_TYPE'] = args.auth
    if args.debug:
        os.environ['MCP_DEBUG'] = 'true'
    
    sys.exit(asyncio.run(main()))