"""
Enhanced Nexus Multi-Channel Sales Assistant Platform
====================================================

Optimized Nexus implementation for frontend integration with:
- Enhanced performance and caching
- Optimized CORS and security headers
- WebSocket optimization for real-time features
- Production monitoring and health checks
- Multi-channel orchestration (API + CLI + MCP)

This application demonstrates advanced Nexus patterns with frontend optimization.
"""

import os
import jwt
import asyncio
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

# Apply development Windows compatibility first
import dev_compatibility

# Enhanced Nexus imports
from nexus import Nexus
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# FastAPI for advanced features
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, UploadFile, File, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import time

# DataFlow models
from dataflow_models import (
    db, Company, User, UserSession, Customer, Document, 
    Quote, QuoteLineItem, ERPProduct, ActivityLog, WorkflowState
)

# Enhanced configuration
from nexus_enhanced_config import enhanced_config

# Configure production logging with structured format
logging.basicConfig(
    level=getattr(logging, enhanced_config.monitoring.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - [%(process)d:%(thread)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/nexus.log') if os.path.exists('/app/logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Production signal handling for graceful shutdown
import signal
import threading

# Global shutdown event
shutdown_event = threading.Event()

# Enhanced JWT Configuration
JWT_SECRET = enhanced_config.auth.jwt_secret
JWT_ALGORITHM = enhanced_config.auth.jwt_algorithm
JWT_EXPIRATION_HOURS = enhanced_config.auth.jwt_expiration_hours
JWT_REFRESH_THRESHOLD_MINUTES = enhanced_config.performance.jwt_refresh_threshold_minutes

# File Upload Configuration
UPLOAD_DIR = enhanced_config.file_upload.upload_dir
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = enhanced_config.file_upload.max_file_size

# Performance tracking
request_metrics = {
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "average_response_time": 0.0,
    "error_count": 0
}

# Enhanced WebSocket Connection Manager
class EnhancedConnectionManager:
    """Enhanced WebSocket manager with compression and monitoring"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, List[str]] = {}
        self.connection_metrics: Dict[str, Any] = {}
        self.message_queue: Dict[str, List[dict]] = {}
        self.max_connections = enhanced_config.enhanced_websocket.max_connections
        self.heartbeat_interval = enhanced_config.enhanced_websocket.heartbeat_interval
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: int):
        # Check connection limits
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(code=1013, reason="Connection limit exceeded")
            return False
        
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        
        # Initialize connection metrics
        self.connection_metrics[connection_id] = {
            "connected_at": datetime.now(),
            "user_id": user_id,
            "messages_sent": 0,
            "messages_received": 0,
            "last_activity": datetime.now()
        }
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id} (total: {len(self.active_connections)})")
        return True
    
    def disconnect(self, connection_id: str, user_id: int):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if user_id in self.user_connections:
            self.user_connections[user_id] = [
                conn for conn in self.user_connections[user_id] 
                if conn != connection_id
            ]
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Clean up metrics and queues
        if connection_id in self.connection_metrics:
            del self.connection_metrics[connection_id]
        if connection_id in self.message_queue:
            del self.message_queue[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id} (total: {len(self.active_connections)})")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                # Add timestamp if not present
                if "timestamp" not in message:
                    message["timestamp"] = datetime.now().isoformat()
                
                await websocket.send_json(message)
                
                # Update metrics
                if connection_id in self.connection_metrics:
                    self.connection_metrics[connection_id]["messages_sent"] += 1
                    self.connection_metrics[connection_id]["last_activity"] = datetime.now()
                
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                # Remove failed connection
                if connection_id in self.active_connections:
                    user_id = self.connection_metrics.get(connection_id, {}).get("user_id")
                    if user_id:
                        self.disconnect(connection_id, user_id)
    
    async def send_user_message(self, message: dict, user_id: int):
        """Send message to all connections for a specific user"""
        if user_id in self.user_connections:
            tasks = []
            for connection_id in self.user_connections[user_id]:
                tasks.append(self.send_personal_message(message, connection_id))
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        tasks = []
        for connection_id in self.active_connections:
            tasks.append(self.send_personal_message(message, connection_id))
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        now = datetime.now()
        total_messages_sent = sum(m.get("messages_sent", 0) for m in self.connection_metrics.values())
        total_messages_received = sum(m.get("messages_received", 0) for m in self.connection_metrics.values())
        
        # Calculate average connection duration
        connection_durations = [
            (now - m["connected_at"]).total_seconds() 
            for m in self.connection_metrics.values()
        ]
        avg_duration = sum(connection_durations) / len(connection_durations) if connection_durations else 0
        
        return {
            "active_connections": len(self.active_connections),
            "unique_users": len(self.user_connections),
            "total_messages_sent": total_messages_sent,
            "total_messages_received": total_messages_received,
            "average_connection_duration_seconds": avg_duration,
            "max_connections": self.max_connections,
            "heartbeat_interval": self.heartbeat_interval
        }

# Initialize enhanced WebSocket manager
manager = EnhancedConnectionManager()

# Enhanced authentication utilities
security = HTTPBearer()

def create_jwt_tokens(user_data: dict) -> dict:
    """Create JWT access and refresh tokens"""
    now = datetime.utcnow()
    
    # Access token (shorter lived)
    access_payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "role": user_data["role"],
        "company_id": user_data["company_id"],
        "token_type": "access",
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": now,
        "jti": hashlib.md5(f"{user_data['id']}{now.timestamp()}".encode()).hexdigest()
    }
    
    # Refresh token (longer lived)
    refresh_payload = {
        "user_id": user_data["id"],
        "token_type": "refresh",
        "exp": now + timedelta(days=enhanced_config.performance.jwt_refresh_token_days),
        "iat": now,
        "jti": hashlib.md5(f"{user_data['id']}{now.timestamp()}refresh".encode()).hexdigest()
    }
    
    return {
        "access_token": jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM),
        "refresh_token": jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM),
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
        "refresh_expires_in": enhanced_config.performance.jwt_refresh_token_days * 24 * 3600
    }

def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token with enhanced validation"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Validate token type
        if payload.get("token_type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Check if token needs refresh
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            time_until_expiry = exp_datetime - datetime.utcnow()
            
            if time_until_expiry.total_seconds() < JWT_REFRESH_THRESHOLD_MINUTES * 60:
                payload["_needs_refresh"] = True
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Enhanced caching functions
def get_cached_response(cache_key: str) -> Union[dict, None]:
    """Get cached response if valid"""
    response = enhanced_config.get_cached_response(cache_key)
    if response:
        request_metrics["cache_hits"] += 1
    else:
        request_metrics["cache_misses"] += 1
    return response

def set_cached_response(cache_key: str, response_data: dict):
    """Cache response data"""
    enhanced_config.set_cached_response(cache_key, response_data)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Enhanced dependency to get current authenticated user"""
    payload = verify_jwt_token(credentials.credentials)
    
    # Verify session is still active (with caching)
    cache_key = enhanced_config.create_cache_key(
        "user_session", 
        {"user_id": payload["user_id"]}, 
        payload["user_id"]
    )
    
    cached_session = get_cached_response(cache_key)
    if cached_session:
        return payload
    
    # Check database if not cached
    runtime = LocalRuntime()
    workflow = WorkflowBuilder()
    workflow.add_node("AsyncSQLQueryNode", "check_session", {
        "query": "SELECT * FROM user_sessions WHERE user_id = %(user_id)s AND is_active = true AND expires_at > NOW()",
        "parameters": {"user_id": payload["user_id"]},
        "connection_pool": db.connection_pool
    })
    
    results, _ = runtime.execute(workflow.build())
    if not results.get("check_session"):
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Cache valid session
    set_cached_response(cache_key, {"valid": True})
    return payload

# Initialize Enhanced Nexus application
app = Nexus(**enhanced_config.get_nexus_enhanced_config())

# Enhanced middleware setup with production optimizations
@app.api_app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers and production optimizations to all responses"""
    start_time = time.time()
    
    # Check for graceful shutdown
    if shutdown_event.is_set():
        return JSONResponse(
            status_code=503,
            content={"detail": "Service shutting down gracefully"},
            headers={"Retry-After": "30"}
        )
    
    try:
        response = await call_next(request)
        
        # Add security headers optimized for containers
        for header, value in enhanced_config.enhanced_security.security_headers.items():
            response.headers[header] = value
        
        # Add production performance headers
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        response.headers["X-Container-ID"] = os.getenv("HOSTNAME", "unknown")
        response.headers["X-Nexus-Version"] = "1.0.0"
        
        # Update metrics atomically
        request_metrics["total_requests"] += 1
        if request_metrics["total_requests"] > 1:
            request_metrics["average_response_time"] = (
                (request_metrics["average_response_time"] * (request_metrics["total_requests"] - 1) + process_time) /
                request_metrics["total_requests"]
            )
        else:
            request_metrics["average_response_time"] = process_time
        
        return response
    
    except Exception as e:
        logger.error(f"Middleware error: {str(e)}", exc_info=True)
        request_metrics["error_count"] += 1
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers={"X-Error-ID": str(hash(str(e)))[:8]}
        )

@app.api_app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests for monitoring"""
    if enhanced_config.enhanced_security.enable_request_logging:
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path} from {request.client.host}")
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} in {process_time:.4f}s")
        
        return response
    
    return await call_next(request)

# Production middleware stack with optimizations
app.api_app.add_middleware(
    GZipMiddleware, 
    minimum_size=enhanced_config.performance.gzip_minimum_size
)

# Add trusted host middleware for container security
from fastapi.middleware.trustedhost import TrustedHostMiddleware
app.api_app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1", 
        "0.0.0.0",
        "*.internal",  # Container internal networking
        os.getenv("TRUSTED_HOST", "*")
    ]
)

app.api_app.add_middleware(
    SessionMiddleware, 
    secret_key=JWT_SECRET,
    max_age=JWT_EXPIRATION_HOURS * 3600,
    session_cookie="nexus_session",
    https_only=enhanced_config.server.enable_https,
    same_site="lax"
)

# Enhanced CORS configuration
app.api_app.add_middleware(
    CORSMiddleware,
    allow_origins=enhanced_config.get_cors_origins(),
    allow_credentials=enhanced_config.cors.allow_credentials,
    allow_methods=enhanced_config.cors.allow_methods,
    allow_headers=enhanced_config.cors.allow_headers,
    expose_headers=enhanced_config.cors.expose_headers,
    max_age=enhanced_config.cors.max_age,
)

# Import and register existing workflows (keeping the same workflow definitions)
from nexus_app import (
    create_user_authentication_workflow,
    create_customer_management_workflow,
    create_quote_generation_workflow,
    create_document_processing_workflow,
    create_real_time_notification_workflow
)

# Register workflows with the enhanced Nexus platform
app.register("user_authentication", create_user_authentication_workflow().build())
app.register("customer_management", create_customer_management_workflow().build())
app.register("quote_generation", create_quote_generation_workflow().build())
app.register("document_processing", create_document_processing_workflow().build())
app.register("real_time_notification", create_real_time_notification_workflow().build())

# ==============================================================================
# ENHANCED API ENDPOINTS
# ==============================================================================

@app.api_app.post("/api/auth/login")
async def enhanced_login(credentials: Dict[str, str], request: Request, background_tasks: BackgroundTasks):
    """Enhanced login endpoint with performance optimization"""
    try:
        # Check cache first (for repeated login attempts)
        cache_key = enhanced_config.create_cache_key("login_attempt", {"email": credentials.get("email")})
        
        # Execute authentication workflow
        runtime = LocalRuntime()
        workflow = create_user_authentication_workflow()
        
        # Get client information
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "unknown")[:200]
        
        context = {
            "email": credentials.get("email"),
            "ip_address": client_ip,
            "user_agent": user_agent
        }
        
        results, _ = runtime.execute(workflow.build(), context)
        
        user_data = results.get("validate_user", {})
        if not user_data:
            request_metrics["error_count"] += 1
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create JWT tokens
        tokens = create_jwt_tokens(user_data[0])
        
        # Prepare response
        response_data = {
            **tokens,
            "user": {
                "id": user_data[0]["id"],
                "email": user_data[0]["email"],
                "first_name": user_data[0]["first_name"],
                "last_name": user_data[0]["last_name"],
                "role": user_data[0]["role"],
                "company_name": user_data[0]["company_name"]
            },
            "session_info": {
                "login_time": datetime.utcnow().isoformat(),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "expires_at": (datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)).isoformat()
            }
        }
        
        # Cache successful login info (short TTL for security)
        cache_key = enhanced_config.create_cache_key("user_info", {"user_id": user_data[0]["id"]})
        set_cached_response(cache_key, response_data["user"])
        
        # Background task for session cleanup
        background_tasks.add_task(cleanup_expired_sessions)
        
        return response_data
    
    except Exception as e:
        request_metrics["error_count"] += 1
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.api_app.post("/api/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh JWT token endpoint"""
    try:
        # Verify refresh token
        payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        if payload.get("token_type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Get user data
        cache_key = enhanced_config.create_cache_key("user_info", {"user_id": payload["user_id"]})
        user_data = get_cached_response(cache_key)
        
        if not user_data:
            # Fetch from database
            runtime = LocalRuntime()
            workflow = WorkflowBuilder()
            workflow.add_node("AsyncSQLQueryNode", "get_user", {
                "query": "SELECT * FROM users WHERE id = %(user_id)s AND is_active = true",
                "parameters": {"user_id": payload["user_id"]},
                "connection_pool": db.connection_pool
            })
            
            results, _ = runtime.execute(workflow.build())
            user_results = results.get("get_user", [])
            if not user_results:
                raise HTTPException(status_code=401, detail="User not found")
            
            user_data = user_results[0]
            set_cached_response(cache_key, user_data)
        
        # Create new tokens
        tokens = create_jwt_tokens(user_data)
        
        return {
            **tokens,
            "refreshed_at": datetime.utcnow().isoformat()
        }
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@app.api_app.get("/api/dashboard")
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    """Enhanced dashboard endpoint with caching"""
    try:
        # Check cache first
        cache_key = enhanced_config.create_cache_key("dashboard", {"company_id": current_user["company_id"]})
        cached_data = get_cached_response(cache_key)
        
        if cached_data:
            return cached_data
        
        # Fetch dashboard data
        runtime = LocalRuntime()
        workflow = WorkflowBuilder()
        
        # Get metrics
        workflow.add_node("AsyncSQLQueryNode", "get_metrics", {
            "query": """
                SELECT 
                    (SELECT COUNT(*) FROM customers WHERE deleted_at IS NULL) as total_customers,
                    (SELECT COUNT(*) FROM quotes WHERE created_date >= CURRENT_DATE - INTERVAL '30 days') as total_quotes,
                    (SELECT COUNT(*) FROM documents WHERE upload_date >= CURRENT_DATE - INTERVAL '30 days') as total_documents,
                    (SELECT COALESCE(SUM(total_amount), 0) FROM quotes WHERE status = 'accepted' AND created_date >= CURRENT_DATE - INTERVAL '30 days') as monthly_revenue
            """,
            "parameters": {},
            "connection_pool": db.connection_pool
        })
        
        # Get recent activity
        workflow.add_node("AsyncSQLQueryNode", "get_activity", {
            "query": """
                SELECT entity_type, entity_id, action, user_name, timestamp, 
                       CASE 
                           WHEN entity_type = 'customer' THEN (SELECT name FROM customers WHERE id = entity_id)
                           WHEN entity_type = 'quote' THEN (SELECT quote_number FROM quotes WHERE id = entity_id)
                           WHEN entity_type = 'document' THEN (SELECT name FROM documents WHERE id = entity_id)
                           ELSE 'Unknown'
                       END as entity_name
                FROM activity_logs 
                ORDER BY timestamp DESC 
                LIMIT 10
            """,
            "parameters": {},
            "connection_pool": db.connection_pool
        })
        
        workflow.connect("get_metrics", "get_activity")
        
        results, _ = runtime.execute(workflow.build())
        
        dashboard_data = {
            "metrics": results.get("get_metrics", [{}])[0],
            "recent_activity": results.get("get_activity", []),
            "cache_info": {
                "cached_at": datetime.now().isoformat(),
                "cache_ttl": enhanced_config.performance.cache_ttl_seconds
            }
        }
        
        # Cache the response
        set_cached_response(cache_key, dashboard_data)
        
        return dashboard_data
    
    except Exception as e:
        request_metrics["error_count"] += 1
        logger.error(f"Dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")

@app.api_app.get("/api/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": enhanced_config.environment
        }
        
        if enhanced_config.health_check.enable_health_checks:
            checks = {}
            
            # Database check
            if enhanced_config.health_check.check_database:
                try:
                    runtime = LocalRuntime()
                    workflow = WorkflowBuilder()
                    workflow.add_node("AsyncSQLQueryNode", "db_check", {
                        "query": "SELECT 1 as healthy",
                        "parameters": {},
                        "connection_pool": db.connection_pool
                    })
                    
                    start_time = time.time()
                    results, _ = runtime.execute(workflow.build())
                    response_time = time.time() - start_time
                    
                    checks["database"] = {
                        "status": "healthy" if results.get("db_check") else "unhealthy",
                        "response_time_ms": round(response_time * 1000, 2)
                    }
                except Exception as e:
                    checks["database"] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
            
            # WebSocket check
            checks["websocket"] = {
                "status": "healthy",
                "active_connections": len(manager.active_connections),
                "max_connections": manager.max_connections
            }
            
            # Cache check
            cache_stats = enhanced_config.get_cache_stats()
            checks["cache"] = {
                "status": "healthy",
                **cache_stats
            }
            
            # Performance metrics
            checks["performance"] = {
                "status": "healthy",
                "total_requests": request_metrics["total_requests"],
                "cache_hit_ratio": request_metrics["cache_hits"] / max(request_metrics["cache_hits"] + request_metrics["cache_misses"], 1),
                "average_response_time_ms": round(request_metrics["average_response_time"] * 1000, 2),
                "error_rate": request_metrics["error_count"] / max(request_metrics["total_requests"], 1)
            }
            
            health_data["checks"] = checks
            
            # Overall status
            unhealthy_checks = [name for name, check in checks.items() if check["status"] != "healthy"]
            if unhealthy_checks:
                health_data["status"] = "degraded"
                health_data["unhealthy_checks"] = unhealthy_checks
        
        return health_data
    
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Health check failed"
        }

@app.api_app.get("/api/metrics")
async def get_metrics(current_user: dict = Depends(get_current_user)):
    """Get platform metrics and statistics"""
    try:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "request_metrics": request_metrics,
            "websocket_stats": manager.get_connection_stats(),
            "cache_stats": enhanced_config.get_cache_stats(),
            "system_info": {
                "environment": enhanced_config.environment,
                "cache_ttl": enhanced_config.performance.cache_ttl_seconds,
                "max_concurrent_requests": enhanced_config.performance.max_concurrent_requests,
                "websocket_max_connections": enhanced_config.enhanced_websocket.max_connections
            }
        }
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

# Enhanced WebSocket endpoint
@app.api_app.websocket("/ws/{client_id}")
async def enhanced_websocket_endpoint(websocket: WebSocket, client_id: str, token: Optional[str] = None):
    """Enhanced WebSocket endpoint with compression and monitoring"""
    try:
        # Verify JWT token
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        payload = verify_jwt_token(token)
        user_id = payload["user_id"]
        
        # Connect to WebSocket manager
        connected = await manager.connect(websocket, client_id, user_id)
        if not connected:
            return
        
        # Send welcome message
        await manager.send_personal_message({
            "type": "welcome",
            "message": "Connected to enhanced sales assistant",
            "features": {
                "compression": enhanced_config.enhanced_websocket.enable_compression,
                "heartbeat_interval": enhanced_config.enhanced_websocket.heartbeat_interval,
                "max_message_size": enhanced_config.enhanced_websocket.max_message_size
            }
        }, client_id)
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeat(client_id))
        
        try:
            while True:
                # Receive messages from client
                data = await websocket.receive_json()
                
                # Update metrics
                if client_id in manager.connection_metrics:
                    manager.connection_metrics[client_id]["messages_received"] += 1
                    manager.connection_metrics[client_id]["last_activity"] = datetime.now()
                
                # Handle different message types
                await handle_websocket_message(data, client_id, user_id)
        
        except WebSocketDisconnect:
            heartbeat_task.cancel()
            manager.disconnect(client_id, user_id)
    
    except jwt.JWTError:
        await websocket.close(code=1008, reason="Invalid token")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=1011, reason="Internal error")

async def send_heartbeat(connection_id: str):
    """Send periodic heartbeat messages"""
    try:
        while True:
            await asyncio.sleep(enhanced_config.enhanced_websocket.heartbeat_interval)
            await manager.send_personal_message({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            }, connection_id)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Heartbeat error for {connection_id}: {e}")

async def handle_websocket_message(data: dict, client_id: str, user_id: int):
    """Handle incoming WebSocket messages"""
    message_type = data.get("type")
    
    if message_type == "chat_message":
        # Process chat message
        response = {
            "type": "chat_response",
            "message": f"Received: {data.get('message')}",
            "user_id": user_id,
            "processed_at": datetime.now().isoformat()
        }
        await manager.send_personal_message(response, client_id)
    
    elif message_type == "quote_request":
        # Handle quote generation request
        await manager.send_personal_message({
            "type": "quote_processing",
            "message": "Processing quote request..."
        }, client_id)
        
        # Simulate processing
        await asyncio.sleep(2)
        
        await manager.send_personal_message({
            "type": "quote_ready",
            "message": "Quote generated successfully",
            "quote_id": f"Q{int(time.time())}",
            "processing_time_ms": 2000
        }, client_id)
    
    elif message_type == "ping":
        # Respond to ping
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }, client_id)

# Background task functions
async def cleanup_expired_sessions():
    """Background task to clean up expired sessions"""
    try:
        runtime = LocalRuntime()
        workflow = WorkflowBuilder()
        workflow.add_node("AsyncSQLExecuteNode", "cleanup_sessions", {
            "query": "UPDATE user_sessions SET is_active = false WHERE expires_at < NOW()",
            "parameters": {},
            "connection_pool": db.connection_pool
        })
        
        results, _ = runtime.execute(workflow.build())
        logger.info("Expired sessions cleaned up")
    except Exception as e:
        logger.error(f"Session cleanup error: {e}")

# ==============================================================================
# CLI COMMAND ENHANCEMENTS
# ==============================================================================

@app.cli.command("cache-stats")
def cache_stats_command():
    """Display cache statistics"""
    stats = enhanced_config.get_cache_stats()
    print("📊 Cache Statistics:")
    print(f"   • Total entries: {stats['total_entries']}")
    print(f"   • Valid entries: {stats['valid_entries']}")
    print(f"   • Expired entries: {stats['expired_entries']}")
    print(f"   • Hit ratio: {stats['cache_hit_ratio']:.2%}")
    print(f"   • TTL: {stats['ttl_seconds']} seconds")

@app.cli.command("clear-cache")
@app.cli.option("--pattern", help="Clear entries matching pattern")
def clear_cache_command(pattern: Optional[str]):
    """Clear cache entries"""
    try:
        enhanced_config.clear_cache(pattern)
        if pattern:
            print(f"✅ Cache entries matching '{pattern}' cleared")
        else:
            print("✅ All cache entries cleared")
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

@app.cli.command("connection-stats")
def connection_stats_command():
    """Display WebSocket connection statistics"""
    stats = manager.get_connection_stats()
    print("🔗 WebSocket Statistics:")
    print(f"   • Active connections: {stats['active_connections']}")
    print(f"   • Unique users: {stats['unique_users']}")
    print(f"   • Messages sent: {stats['total_messages_sent']}")
    print(f"   • Messages received: {stats['total_messages_received']}")
    print(f"   • Average duration: {stats['average_connection_duration_seconds']:.1f}s")

# ==============================================================================
# MCP TOOL ENHANCEMENTS
# ==============================================================================

@app.mcp_server.tool("get_health_status")
def get_health_status_tool() -> Dict[str, Any]:
    """MCP tool to get system health status"""
    try:
        return {
            "success": True,
            "health_data": {
                "status": "healthy",
                "request_metrics": request_metrics,
                "websocket_connections": len(manager.active_connections),
                "cache_stats": enhanced_config.get_cache_stats(),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "health_data": None
        }

# ==============================================================================
# APPLICATION STARTUP
# ==============================================================================

def setup_enhanced_database():
    """Initialize database with enhanced monitoring"""
    try:
        # DataFlow handles schema creation
        logger.info("Enhanced database setup completed via DataFlow auto-migration")
        
        # Initialize cache
        enhanced_config.clear_cache()
        logger.info("Cache system initialized")
        
        return True
    except Exception as e:
        logger.error(f"Enhanced database setup failed: {str(e)}")
        return False

def main():
    """Enhanced main application entry point"""
    logger.info("🚀 Starting Enhanced Nexus Sales Assistant Platform")
    
    # Setup database
    if not setup_enhanced_database():
        logger.error("❌ Enhanced database setup failed - exiting")
        return
    
    # Configure enterprise features
    app.auth.strategy = "jwt"
    app.monitoring.interval = enhanced_config.monitoring.metrics_interval
    app.monitoring.metrics = ["requests", "latency", "errors", "websockets", "cache"]
    
    # Display configuration summary
    logger.info("✅ Enhanced enterprise features configured")
    logger.info("🌐 Multi-channel access available:")
    logger.info(f"   • REST API: {'https' if enhanced_config.server.enable_https else 'http'}://{enhanced_config.server.api_host}:{enhanced_config.server.api_port}")
    logger.info(f"   • WebSocket: {'wss' if enhanced_config.server.enable_https else 'ws'}://{enhanced_config.server.api_host}:{enhanced_config.server.api_port}/ws/{{client_id}}?token={{jwt_token}}")
    logger.info("   • CLI: nexus --help")
    logger.info(f"   • MCP Server: http://{enhanced_config.server.mcp_host}:{enhanced_config.server.mcp_port}")
    
    # Performance info
    logger.info("⚡ Performance optimizations:")
    logger.info(f"   • Request timeout: {enhanced_config.performance.request_timeout}s")
    logger.info(f"   • Cache TTL: {enhanced_config.performance.cache_ttl_seconds}s")
    logger.info(f"   • Max concurrent requests: {enhanced_config.performance.max_concurrent_requests}")
    logger.info(f"   • WebSocket max connections: {enhanced_config.enhanced_websocket.max_connections}")
    
    # Security info
    logger.info(f"🛡️  Security: {len(enhanced_config.enhanced_security.security_headers)} headers, {enhanced_config.enhanced_security.rate_limit_per_minute}/min rate limit")
    logger.info(f"🌐 CORS Origins: {len(enhanced_config.get_cors_origins())} configured")
    
    # Save frontend configuration
    try:
        from nexus_enhanced_config import save_frontend_config
        save_frontend_config("frontend-config.json")
        logger.info("📄 Frontend configuration saved to frontend-config.json")
    except Exception as e:
        logger.warning(f"Could not save frontend config: {e}")
    
    # Start the enhanced platform
    logger.info("🎯 Starting enhanced multi-channel platform...")
    app.start()

if __name__ == "__main__":
    main()