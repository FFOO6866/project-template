"""
Nexus Production API Server
Production-optimized FastAPI server for Nexus multi-channel platform
"""

import asyncio
import os
import signal
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aioredis
import jwt
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
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
api_requests = Counter('nexus_api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
api_request_duration = Histogram('nexus_api_request_duration_seconds', 'API request duration')
api_active_requests = Gauge('nexus_api_active_requests', 'Active API requests')
workflow_executions = Counter('nexus_workflow_executions_total', 'Total workflow executions', ['workflow', 'status'])
workflow_execution_duration = Histogram('nexus_workflow_execution_duration_seconds', 'Workflow execution duration')

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

class NexusProductionAPI:
    """Production-optimized Nexus API server with distributed tracing and monitoring"""
    
    def __init__(self):
        self.app = FastAPI(
            title="Nexus Production API",
            version="1.0.0",
            description="Production multi-channel Nexus platform API"
        )
        self.nexus: Optional[Nexus] = None
        self.redis: Optional[aioredis.Redis] = None
        self.runtime = LocalRuntime()
        self.security = HTTPBearer()
        
        # Configuration
        self.instance_id = os.getenv("NEXUS_INSTANCE_ID", f"api-{uuid.uuid4().hex[:8]}")
        self.jwt_secret = os.getenv("NEXUS_JWT_SECRET")
        self.api_key = os.getenv("NEXUS_API_KEY")
        self.max_request_size = int(os.getenv("MAX_REQUEST_SIZE", 10 * 1024 * 1024))  # 10MB
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", 100))
        
        # Request tracking
        self.active_requests = 0
        self.request_cache = {}
        
        self._setup_middleware()
        self._setup_routes()
        
        logger.info("Nexus Production API initialized", instance_id=self.instance_id)

    def _setup_middleware(self):
        """Configure middleware stack"""
        
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID", "X-Process-Time"],
        )
        
        # Compression
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # Request tracking middleware
        @self.app.middleware("http")
        async def track_requests(request: Request, call_next):
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
            start_time = time.time()
            
            self.active_requests += 1
            api_active_requests.set(self.active_requests)
            
            try:
                with tracer.start_as_current_span("api_request") as span:
                    span.set_attribute("request.id", request_id)
                    span.set_attribute("request.method", request.method)
                    span.set_attribute("request.url", str(request.url))
                    span.set_attribute("instance.id", self.instance_id)
                    
                    response = await call_next(request)
                    
                    duration = time.time() - start_time
                    
                    # Update metrics
                    api_requests.labels(
                        method=request.method,
                        endpoint=request.url.path,
                        status=response.status_code
                    ).inc()
                    api_request_duration.observe(duration)
                    
                    # Add response headers
                    response.headers["X-Request-ID"] = request_id
                    response.headers["X-Process-Time"] = f"{duration:.4f}"
                    response.headers["X-Instance-ID"] = self.instance_id
                    
                    span.set_attribute("response.status_code", response.status_code)
                    span.set_attribute("response.duration", duration)
                    
                    logger.info("API request completed",
                               request_id=request_id,
                               method=request.method,
                               path=request.url.path,
                               status=response.status_code,
                               duration=duration)
                    
                    return response
                    
            finally:
                self.active_requests -= 1
                api_active_requests.set(self.active_requests)

    def _setup_routes(self):
        """Configure API routes"""
        
        @self.app.on_event("startup")
        async def startup():
            await self._initialize()
        
        @self.app.on_event("shutdown")
        async def shutdown():
            await self._cleanup()
        
        # Health check
        @self.app.get("/api/health")
        async def health_check():
            """Comprehensive health check"""
            checks = {}
            overall_status = "healthy"
            
            # Database check
            try:
                # Test database connectivity (implement based on your database)
                checks["database"] = {"status": "healthy", "response_time_ms": 0}
            except Exception as e:
                checks["database"] = {"status": "unhealthy", "error": str(e)}
                overall_status = "unhealthy"
            
            # Redis check
            try:
                if self.redis:
                    start = time.time()
                    await self.redis.ping()
                    response_time = (time.time() - start) * 1000
                    checks["redis"] = {"status": "healthy", "response_time_ms": response_time}
                else:
                    checks["redis"] = {"status": "unhealthy", "error": "Not connected"}
                    overall_status = "unhealthy"
            except Exception as e:
                checks["redis"] = {"status": "unhealthy", "error": str(e)}
                overall_status = "unhealthy"
            
            # Nexus check
            if self.nexus:
                checks["nexus"] = {"status": "healthy", "workflows": len(self.nexus._workflows)}
            else:
                checks["nexus"] = {"status": "unhealthy", "error": "Not initialized"}
                overall_status = "unhealthy"
            
            return {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "instance_id": self.instance_id,
                "version": "1.0.0",
                "checks": checks,
                "metrics": {
                    "active_requests": self.active_requests,
                    "total_requests": api_requests._value.sum(),
                    "average_response_time": api_request_duration._sum.get() / max(api_request_duration._count.get(), 1)
                }
            }
        
        # Authentication endpoint
        @self.app.post("/api/auth/login")
        async def login(credentials: Dict[str, str]):
            """Authenticate user and return JWT token"""
            with tracer.start_as_current_span("auth_login") as span:
                email = credentials.get("email")
                password = credentials.get("password")
                
                span.set_attribute("auth.email", email)
                
                if not email or not password:
                    raise HTTPException(status_code=400, detail="Email and password required")
                
                # Implement your authentication logic here
                # This is a simplified example
                if email == "admin@example.com" and password == "admin":
                    token_data = {
                        "user_id": "1",
                        "email": email,
                        "role": "admin",
                        "exp": datetime.utcnow() + timedelta(hours=24),
                        "iat": datetime.utcnow(),
                        "iss": "nexus-api",
                        "aud": "nexus-platform"
                    }
                    
                    token = jwt.encode(token_data, self.jwt_secret, algorithm="HS256")
                    
                    # Cache user session in Redis
                    if self.redis:
                        await self.redis.setex(
                            f"nexus:session:{token}",
                            86400,  # 24 hours
                            json.dumps(token_data, default=str)
                        )
                    
                    span.set_attribute("auth.success", True)
                    
                    return {
                        "access_token": token,
                        "token_type": "bearer",
                        "expires_in": 86400,
                        "user": {
                            "id": "1",
                            "email": email,
                            "role": "admin"
                        }
                    }
                else:
                    span.set_attribute("auth.success", False)
                    raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Workflow execution endpoint
        @self.app.post("/api/workflows/{workflow_name}/execute")
        async def execute_workflow(
            workflow_name: str,
            parameters: Dict,
            current_user: Dict = Depends(self._get_current_user),
            background_tasks: BackgroundTasks = BackgroundTasks()
        ):
            """Execute a workflow with parameters"""
            with tracer.start_as_current_span("workflow_execution") as span:
                span.set_attribute("workflow.name", workflow_name)
                span.set_attribute("user.id", current_user.get("user_id"))
                
                if not self.nexus or workflow_name not in self.nexus._workflows:
                    raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")
                
                start_time = time.time()
                
                try:
                    # Get workflow
                    workflow = self.nexus._workflows[workflow_name]
                    
                    # Execute workflow
                    results, run_id = self.runtime.execute(workflow)
                    
                    duration = time.time() - start_time
                    
                    # Update metrics
                    workflow_executions.labels(workflow=workflow_name, status="success").inc()
                    workflow_execution_duration.observe(duration)
                    
                    span.set_attribute("workflow.run_id", run_id)
                    span.set_attribute("workflow.duration", duration)
                    span.set_attribute("workflow.success", True)
                    
                    # Log execution (background task)
                    background_tasks.add_task(
                        self._log_workflow_execution,
                        workflow_name, run_id, parameters, results, duration, current_user
                    )
                    
                    return {
                        "status": "success",
                        "workflow_name": workflow_name,
                        "run_id": run_id,
                        "results": results,
                        "execution_time": duration,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    # Update metrics
                    workflow_executions.labels(workflow=workflow_name, status="error").inc()
                    workflow_execution_duration.observe(duration)
                    
                    span.set_attribute("workflow.error", str(e))
                    span.set_attribute("workflow.success", False)
                    
                    logger.error("Workflow execution failed",
                                workflow_name=workflow_name,
                                error=str(e),
                                duration=duration)
                    
                    raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")
        
        # List workflows endpoint
        @self.app.get("/api/workflows")
        async def list_workflows(current_user: Dict = Depends(self._get_current_user)):
            """List available workflows"""
            if not self.nexus:
                return {"workflows": []}
            
            workflows = []
            for name, workflow in self.nexus._workflows.items():
                workflows.append({
                    "name": name,
                    "description": getattr(workflow, 'description', ''),
                    "nodes": len(workflow.nodes) if hasattr(workflow, 'nodes') else 0
                })
            
            return {"workflows": workflows}
        
        # Metrics endpoint
        @self.app.get("/api/metrics")
        async def get_metrics(current_user: Dict = Depends(self._get_current_user)):
            """Get API metrics"""
            return {
                "instance_id": self.instance_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "active_requests": self.active_requests,
                    "total_requests": api_requests._value.sum(),
                    "request_duration_avg": api_request_duration._sum.get() / max(api_request_duration._count.get(), 1),
                    "workflow_executions": workflow_executions._value.sum(),
                    "workflow_duration_avg": workflow_execution_duration._sum.get() / max(workflow_execution_duration._count.get(), 1)
                }
            }

    async def _get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Get current authenticated user"""
        try:
            token = credentials.credentials
            
            # Try to get from Redis cache first
            if self.redis:
                cached_user = await self.redis.get(f"nexus:session:{token}")
                if cached_user:
                    return json.loads(cached_user)
            
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            # Validate token
            if payload.get("exp", 0) < datetime.utcnow().timestamp():
                raise HTTPException(status_code=401, detail="Token expired")
            
            return payload
            
        except jwt.JWTError as e:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def _initialize(self):
        """Initialize production services"""
        try:
            # Initialize Redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis = aioredis.from_url(redis_url)
            await self.redis.ping()
            
            # Initialize Nexus
            self.nexus = Nexus(
                api_port=int(os.getenv("NEXUS_API_PORT", 8000)),
                enable_auth=True,
                enable_monitoring=True,
                rate_limit=self.rate_limit_per_minute
            )
            
            # Register sample workflows (replace with your actual workflows)
            await self._register_workflows()
            
            # Start metrics server
            metrics_port = int(os.getenv("METRICS_PORT", 9090))
            start_http_server(metrics_port)
            
            # Instrument FastAPI with OpenTelemetry
            FastAPIInstrumentor.instrument_app(self.app)
            
            logger.info("Nexus Production API initialized successfully",
                       instance_id=self.instance_id,
                       metrics_port=metrics_port)
            
        except Exception as e:
            logger.error("Failed to initialize Nexus Production API", error=str(e))
            raise

    async def _register_workflows(self):
        """Register production workflows"""
        # Sample workflow - replace with your actual workflows
        workflow = WorkflowBuilder()
        workflow.add_node("PythonCodeNode", "hello", {
            "code": "result = {'message': 'Hello from Nexus Production API'}"
        })
        
        self.nexus.register("hello_world", workflow.build())
        
        logger.info("Production workflows registered", count=len(self.nexus._workflows))

    async def _log_workflow_execution(self, workflow_name: str, run_id: str, 
                                    parameters: Dict, results: Dict, duration: float, user: Dict):
        """Log workflow execution to Redis/database"""
        try:
            execution_log = {
                "workflow_name": workflow_name,
                "run_id": run_id,
                "parameters": parameters,
                "results": results,
                "duration": duration,
                "user_id": user.get("user_id"),
                "timestamp": datetime.utcnow().isoformat(),
                "instance_id": self.instance_id
            }
            
            if self.redis:
                # Store execution log in Redis
                await self.redis.lpush(
                    "nexus:execution_logs",
                    json.dumps(execution_log, default=str)
                )
                
                # Keep only last 1000 logs
                await self.redis.ltrim("nexus:execution_logs", 0, 999)
            
        except Exception as e:
            logger.error("Failed to log workflow execution", error=str(e))

    async def _cleanup(self):
        """Cleanup resources on shutdown"""
        logger.info("Shutting down Nexus Production API", instance_id=self.instance_id)
        
        if self.redis:
            await self.redis.close()
        
        if self.nexus:
            # Add Nexus cleanup if needed
            pass

# Create global API instance
api_server = NexusProductionAPI()
app = api_server.app

# Graceful shutdown handling
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal", signal=signum)
    asyncio.create_task(api_server._cleanup())
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    import uvicorn
    import json
    
    port = int(os.getenv("NEXUS_API_PORT", 8000))
    host = os.getenv("NEXUS_API_HOST", "0.0.0.0")
    workers = int(os.getenv("NEXUS_WORKERS", 4))
    
    uvicorn.run(
        "nexus_production_api:app",
        host=host,
        port=port,
        workers=1,  # Use 1 worker for development, use Gunicorn for production
        log_config=None,  # Use structlog
        access_log=False
    )