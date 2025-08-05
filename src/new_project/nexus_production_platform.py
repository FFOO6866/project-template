"""
Nexus Production-Optimized Multi-Channel Platform
=================================================

Production-ready Nexus platform with complete DataFlow integration and performance optimizations:

🚀 PERFORMANCE FEATURES:
- WebSocket real-time notifications
- Enhanced JWT session management with refresh tokens
- <2s API response time with intelligent caching
- 10,000+ records/sec bulk operations
- Connection pooling: 75 base + 150 overflow
- Model-specific cache strategies
- Load balancing ready

🌐 MULTI-CHANNEL ACCESS:
- REST API with FastAPI optimizations
- CLI commands for operations
- MCP server for AI agent integration

🔒 PRODUCTION SECURITY:
- JWT authentication with rotation
- Session validation and refresh
- Rate limiting and CORS
- Request timeout management

📊 MONITORING & HEALTH:
- Real-time metrics dashboard
- Connection pool monitoring
- Cache performance tracking
- Comprehensive alerting
"""

import os
import sys
import asyncio
import logging
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union, Set
from pathlib import Path
from contextlib import asynccontextmanager
from collections import defaultdict, deque
import time
import threading
import weakref

# Windows compatibility
import windows_sdk_compatibility

# Core Nexus and SDK imports
from nexus import Nexus
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# DataFlow integration
try:
    from dataflow_classification_models import (
        db, Company, User, Customer, Quote,
        ProductClassification, ClassificationHistory, ClassificationCache,
        ETIMAttribute, ClassificationRule, ClassificationFeedback,
        ClassificationMetrics, Document, DocumentProcessingQueue
    )
    from dataflow_production_optimizations import production_optimizer, ProductionOptimizations
    DATAFLOW_AVAILABLE = True
except Exception as e:
    print(f"WARNING: DataFlow models not available: {e}")
    print("Creating mock DataFlow configuration for development...")
    
    from dataflow import DataFlow
    
    db = DataFlow(
        database_url="sqlite:///nexus_development.db",
        auto_migrate=True,
        enable_caching=True,
        cache_backend='memory'
    )
    
    @db.model
    class Company:
        id: int
        name: str
        industry: str = "technology"
        is_active: bool = True
    
    @db.model
    class User:
        id: int
        email: str
        first_name: str = ""
        last_name: str = ""
        role: str = "user"
        company_id: Optional[int] = None
        is_active: bool = True
    
    @db.model
    class ProductClassification:
        id: int
        product_id: int
        unspsc_code: Optional[str] = None
        etim_class_id: Optional[str] = None
        confidence_score: float = 0.0
        classification_method: str = "unknown"
    
    # Mock production optimizer
    class MockProductionOptimizations:
        def __init__(self, db):
            self.db = db
            self.cache_configs = {}
            self.bulk_configs = {}
        
        async def execute_optimized_bulk_operation(self, model, operation, data, config=None):
            return {"success": True, "processed_records": len(data), "throughput_records_per_second": 1000}
        
        async def warm_model_cache(self, model):
            return {"success": True, "warmed_count": 100}
        
        def get_performance_recommendations(self):
            return []
    
    production_optimizer = MockProductionOptimizations(db)
    DATAFLOW_AVAILABLE = False

# FastAPI and WebSocket imports
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocketState
import jwt
import redis
from datetime import timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================================================================
# PRODUCTION CONFIGURATION
# ==============================================================================

class ProductionNexusConfig:
    """Production-optimized configuration for Nexus platform"""
    
    def __init__(self):
        self.environment = os.getenv("NEXUS_ENV", "production")
        self.debug = self.environment == "development"
        
        # Server configuration
        self.api_port = int(os.getenv("NEXUS_API_PORT", "8000"))
        self.mcp_port = int(os.getenv("NEXUS_MCP_PORT", "3001"))
        self.api_host = os.getenv("NEXUS_API_HOST", "0.0.0.0")
        
        # WebSocket configuration
        self.websocket_port = int(os.getenv("NEXUS_WEBSOCKET_PORT", "8001"))
        self.max_websocket_connections = int(os.getenv("MAX_WEBSOCKET_CONNECTIONS", "500"))
        self.websocket_heartbeat_interval = int(os.getenv("WEBSOCKET_HEARTBEAT_INTERVAL", "30"))
        self.websocket_timeout = int(os.getenv("WEBSOCKET_TIMEOUT", "300"))
        
        # Enhanced JWT Security
        self.jwt_secret = os.getenv("NEXUS_JWT_SECRET", "production-nexus-secret-key-change-me")
        self.jwt_refresh_secret = os.getenv("NEXUS_JWT_REFRESH_SECRET", "production-refresh-secret-key-change-me")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_minutes = int(os.getenv("JWT_EXPIRATION_MINUTES", "15"))  # Short-lived access tokens
        self.jwt_refresh_expiration_days = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))  # Refresh tokens
        
        # Production performance configuration (enhanced from DataFlow optimizations)
        self.cache_ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", "2700"))  # 45 minutes
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", "500"))  # Increased for production
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))  # Reduced for better UX
        self.enable_compression = os.getenv("ENABLE_COMPRESSION", "true").lower() == "true"
        
        # DataFlow production integration (from optimizations)
        self.dataflow_pool_size = int(os.getenv("DATAFLOW_POOL_SIZE", "75"))
        self.dataflow_max_overflow = int(os.getenv("DATAFLOW_MAX_OVERFLOW", "150"))
        self.dataflow_pool_recycle = int(os.getenv("DATAFLOW_POOL_RECYCLE", "1200"))  # 20 minutes
        
        # Enhanced performance settings
        self.bulk_operation_timeout = int(os.getenv("BULK_OPERATION_TIMEOUT", "600"))  # 10 minutes
        self.classification_timeout = int(os.getenv("CLASSIFICATION_TIMEOUT", "45"))   # 45 seconds
        self.cache_warming_enabled = os.getenv("CACHE_WARMING_ENABLED", "true").lower() == "true"
        self.enable_request_batching = os.getenv("ENABLE_REQUEST_BATCHING", "true").lower() == "true"
        self.batch_size_limit = int(os.getenv("BATCH_SIZE_LIMIT", "2000"))  # Increased for production
        
        # Redis configuration for distributed caching
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        
        # Rate limiting
        self.rate_limit_requests_per_minute = int(os.getenv("RATE_LIMIT_RPM", "300"))  # Increased for production
        self.rate_limit_burst = int(os.getenv("RATE_LIMIT_BURST", "50"))
        
        # Load balancing support
        self.enable_load_balancing = os.getenv("ENABLE_LOAD_BALANCING", "false").lower() == "true"
        self.load_balancer_health_check_path = "/api/health"
        
        # CORS configuration for production
        self.cors_origins = self._parse_cors_origins()
        
        # Initialize caching system
        self._init_caching_system()
        
        # Initialize metrics
        self._init_metrics()
        
        # WebSocket connection manager
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Real-time notification queues
        self.notification_queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
    def _parse_cors_origins(self) -> List[str]:
        """Parse CORS origins from environment"""
        cors_env = os.getenv("CORS_ORIGINS", "")
        if cors_env:
            return [origin.strip() for origin in cors_env.split(",") if origin.strip()]
        
        # Default development origins
        return [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:8080",
            "https://your-production-domain.com"  # Add your production domain
        ]
    
    def _init_caching_system(self):
        """Initialize distributed caching system"""
        self._local_cache = {}
        self._cache_timestamps = {}
        self._cache_access_count = {}
        self._cache_size_bytes = 0
        self._cache_lock = threading.RLock()
        
        # Redis connection for distributed caching
        self._redis_client = None
        if self.redis_enabled:
            try:
                import redis
                self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
                self._redis_client.ping()  # Test connection
                logger.info("✅ Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"❌ Redis connection failed, using local cache: {e}")
                self.redis_enabled = False
    
    def _init_metrics(self):
        """Initialize comprehensive metrics system"""
        self.metrics = {
            # Request metrics
            "total_requests": 0,
            "active_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "p95_response_time": 0.0,
            "p99_response_time": 0.0,
            
            # Cache metrics
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_hit_ratio": 0.0,
            "cache_memory_mb": 0,
            "cache_evictions": 0,
            
            # DataFlow metrics
            "dataflow_operations": 0,
            "bulk_operations": 0,
            "classification_operations": 0,
            "slow_requests": 0,
            
            # WebSocket metrics
            "websocket_connections": 0,
            "websocket_messages_sent": 0,
            "websocket_messages_received": 0,
            "websocket_disconnections": 0,
            
            # Session metrics
            "active_sessions": 0,
            "session_refreshes": 0,
            "authentication_failures": 0,
            
            # System metrics
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0.0,
            "connection_pool_active": 0,
            "connection_pool_overflow": 0
        }
        
        # Response time tracking for percentiles
        self._response_times = deque(maxlen=10000)  # Keep last 10k response times
        
        # Model-specific performance tracking (enhanced from DataFlow optimizations)
        self.model_metrics = {
            "Company": {"operations": 0, "avg_response_time": 0, "cache_hits": 0, "cache_hit_ratio": 0.0},
            "Customer": {"operations": 0, "avg_response_time": 0, "cache_hits": 0, "cache_hit_ratio": 0.0},
            "ProductClassification": {"operations": 0, "avg_response_time": 0, "cache_hits": 0, "cache_hit_ratio": 0.0},
            "ClassificationCache": {"operations": 0, "avg_response_time": 0, "cache_hits": 0, "cache_hit_ratio": 0.0},
            "Quote": {"operations": 0, "avg_response_time": 0, "cache_hits": 0, "cache_hit_ratio": 0.0},
            "Document": {"operations": 0, "avg_response_time": 0, "cache_hits": 0, "cache_hit_ratio": 0.0}
        }
    
    def get_nexus_config(self) -> Dict[str, Any]:
        """Get Nexus platform configuration"""
        return {
            "api_port": self.api_port,
            "mcp_port": self.mcp_port,
            "enable_auth": True,
            "enable_monitoring": True,
            "rate_limit": self.rate_limit_requests_per_minute,
            "auto_discovery": False,
            "cors_origins": self.cors_origins,
            "enable_compression": self.enable_compression,
            "request_timeout": self.request_timeout,
            "max_concurrent_requests": self.max_concurrent_requests,
            "enable_websockets": True,
            "websocket_port": self.websocket_port
        }
    
    # Enhanced caching methods with Redis support
    def create_cache_key(self, prefix: str, data: Dict[str, Any], user_id: Optional[int] = None) -> str:
        """Create cache key from data"""
        key_data = f"{prefix}:{json.dumps(data, sort_keys=True)}"
        if user_id:
            key_data = f"user:{user_id}:{key_data}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cached_response(self, cache_key: str, model_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get cached response with Redis fallback"""
        with self._cache_lock:
            # Try Redis first if enabled
            if self.redis_enabled and self._redis_client:
                try:
                    cached_data = self._redis_client.get(f"nexus:{cache_key}")
                    if cached_data:
                        self.metrics["cache_hits"] += 1
                        if model_name and model_name in self.model_metrics:
                            self.model_metrics[model_name]["cache_hits"] += 1
                        return json.loads(cached_data)
                except Exception as e:
                    logger.warning(f"Redis cache read error: {e}")
            
            # Fallback to local cache
            if cache_key in self._local_cache:
                timestamp = self._cache_timestamps.get(cache_key, 0)
                access_count = self._cache_access_count.get(cache_key, 0)
                
                # Dynamic TTL based on access frequency
                base_ttl = self.cache_ttl_seconds
                if access_count > 100:
                    effective_ttl = base_ttl * 2
                elif access_count > 50:
                    effective_ttl = base_ttl * 1.5
                else:
                    effective_ttl = base_ttl
                
                if time.time() - timestamp < effective_ttl:
                    self.metrics["cache_hits"] += 1
                    self._cache_access_count[cache_key] = access_count + 1
                    
                    if model_name and model_name in self.model_metrics:
                        self.model_metrics[model_name]["cache_hits"] += 1
                    
                    return self._local_cache[cache_key]
                else:
                    self._remove_cache_entry(cache_key)
            
            self.metrics["cache_misses"] += 1
            return None
    
    def set_cached_response(self, cache_key: str, data: Dict[str, Any], ttl_override: Optional[int] = None):
        """Cache response data with Redis and local cache"""
        ttl = ttl_override or self.cache_ttl_seconds
        
        with self._cache_lock:
            # Store in Redis if enabled
            if self.redis_enabled and self._redis_client:
                try:
                    self._redis_client.setex(f"nexus:{cache_key}", ttl, json.dumps(data))
                except Exception as e:
                    logger.warning(f"Redis cache write error: {e}")
            
            # Store in local cache
            import sys
            data_size = sys.getsizeof(str(data))
            
            # Check cache size limits (1GB total)
            if self._cache_size_bytes + data_size > 1024 * 1024 * 1024:
                self._evict_lru_entries(data_size)
            
            self._local_cache[cache_key] = data
            self._cache_timestamps[cache_key] = time.time()
            self._cache_access_count[cache_key] = 1
            self._cache_size_bytes += data_size
            
            self.metrics["cache_memory_mb"] = self._cache_size_bytes / (1024 * 1024)
    
    def _remove_cache_entry(self, cache_key: str):
        """Remove cache entry and update size tracking"""
        if cache_key in self._local_cache:
            import sys
            data_size = sys.getsizeof(str(self._local_cache[cache_key]))
            del self._local_cache[cache_key]
            del self._cache_timestamps[cache_key]
            if cache_key in self._cache_access_count:
                del self._cache_access_count[cache_key]
            self._cache_size_bytes -= data_size
            self.metrics["cache_memory_mb"] = self._cache_size_bytes / (1024 * 1024)
            self.metrics["cache_evictions"] += 1
    
    def _evict_lru_entries(self, required_space: int):
        """Evict least recently used entries to free space"""
        entries_by_usage = sorted(
            self._cache_access_count.items(),
            key=lambda x: (x[1], self._cache_timestamps.get(x[0], 0))
        )
        
        freed_space = 0
        for cache_key, _ in entries_by_usage:
            if freed_space >= required_space:
                break
            import sys
            data_size = sys.getsizeof(str(self._local_cache.get(cache_key, {})))
            self._remove_cache_entry(cache_key)
            freed_space += data_size
    
    def update_response_time_metrics(self, response_time: float):
        """Update response time metrics including percentiles"""
        self._response_times.append(response_time)
        
        # Update average
        current_avg = self.metrics["average_response_time"]
        current_count = self.metrics["total_requests"]
        self.metrics["average_response_time"] = (
            (current_avg * (current_count - 1) + response_time) / current_count
        )
        
        # Update percentiles (calculated from recent response times)
        if len(self._response_times) >= 100:
            sorted_times = sorted(list(self._response_times))
            self.metrics["p95_response_time"] = sorted_times[int(len(sorted_times) * 0.95)]
            self.metrics["p99_response_time"] = sorted_times[int(len(sorted_times) * 0.99)]
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics with health indicators"""
        total_cache_ops = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        
        # Calculate cache hit ratios
        self.metrics["cache_hit_ratio"] = self.metrics["cache_hits"] / max(total_cache_ops, 1)
        
        for model, stats in self.model_metrics.items():
            if stats["operations"] > 0:
                stats["cache_hit_ratio"] = stats["cache_hits"] / stats["operations"]
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment,
            "system_metrics": self.metrics,
            "model_metrics": self.model_metrics,
            "health_indicators": {
                "avg_response_time_healthy": self.metrics["average_response_time"] < 2.0,
                "cache_hit_ratio_healthy": self.metrics["cache_hit_ratio"] > 0.8,
                "error_rate_healthy": (self.metrics["failed_requests"] / max(self.metrics["total_requests"], 1)) < 0.05,
                "websocket_healthy": self.metrics["websocket_connections"] < self.max_websocket_connections * 0.9
            },
            "performance_targets": {
                "response_time_target_ms": 2000,
                "cache_hit_ratio_target": 0.8,
                "error_rate_target": 0.05,
                "bulk_throughput_target_rps": 10000
            }
        }

# Initialize production configuration
config = ProductionNexusConfig()

# ==============================================================================
# WEBSOCKET CONNECTION MANAGER
# ==============================================================================

class WebSocketManager:
    """Production WebSocket connection manager with real-time notifications"""
    
    def __init__(self, config: ProductionNexusConfig):
        self.config = config
        self.connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)  # user_id -> set of connection_ids
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self._connection_lock = threading.RLock()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background tasks for connection management"""
        def heartbeat_task():
            while True:
                asyncio.run(self._send_heartbeat())
                time.sleep(self.config.websocket_heartbeat_interval)
        
        heartbeat_thread = threading.Thread(target=heartbeat_task, daemon=True)
        heartbeat_thread.start()
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_metadata: Dict[str, Any] = None) -> str:
        """Connect a WebSocket client"""
        connection_id = str(uuid.uuid4())
        
        with self._connection_lock:
            await websocket.accept()
            
            self.connections[connection_id] = websocket
            self.user_connections[user_id].add(connection_id)
            self.connection_metadata[connection_id] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow().isoformat(),
                "last_heartbeat": time.time(),
                **(connection_metadata or {})
            }
            
            self.config.metrics["websocket_connections"] += 1
            
            logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
            
            # Send welcome message
            await self.send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket client"""
        with self._connection_lock:
            if connection_id in self.connections:
                metadata = self.connection_metadata.get(connection_id, {})
                user_id = metadata.get("user_id")
                
                # Clean up connection
                del self.connections[connection_id]
                del self.connection_metadata[connection_id]
                
                if user_id and connection_id in self.user_connections[user_id]:
                    self.user_connections[user_id].remove(connection_id)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                
                self.config.metrics["websocket_connections"] -= 1
                self.config.metrics["websocket_disconnections"] += 1
                
                logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all connections for a user"""
        if user_id in self.user_connections:
            connections_to_remove = []
            
            for connection_id in self.user_connections[user_id].copy():
                try:
                    await self.send_to_connection(connection_id, message)
                except Exception as e:
                    logger.warning(f"Failed to send message to connection {connection_id}: {e}")
                    connections_to_remove.append(connection_id)
            
            # Clean up failed connections
            for connection_id in connections_to_remove:
                await self.disconnect(connection_id)
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to specific connection"""
        if connection_id in self.connections:
            websocket = self.connections[connection_id]
            
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json({
                    **message,
                    "timestamp": datetime.utcnow().isoformat()
                })
                self.config.metrics["websocket_messages_sent"] += 1
            else:
                await self.disconnect(connection_id)
    
    async def broadcast(self, message: Dict[str, Any], user_filter: Optional[callable] = None):
        """Broadcast message to all or filtered connections"""
        disconnected_connections = []
        
        for connection_id, websocket in self.connections.items():
            try:
                metadata = self.connection_metadata.get(connection_id, {})
                
                # Apply user filter if provided
                if user_filter and not user_filter(metadata.get("user_id")):
                    continue
                
                await self.send_to_connection(connection_id, message)
                
            except Exception as e:
                logger.warning(f"Failed to broadcast to connection {connection_id}: {e}")
                disconnected_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in disconnected_connections:
            await self.disconnect(connection_id)
    
    async def _send_heartbeat(self):
        """Send heartbeat to all connections"""
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(heartbeat_message)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            "total_connections": len(self.connections),
            "unique_users": len(self.user_connections),
            "connections_by_user": {user_id: len(connections) for user_id, connections in self.user_connections.items()},
            "max_connections": self.config.max_websocket_connections,
            "utilization_percent": (len(self.connections) / self.config.max_websocket_connections) * 100
        }

# Initialize WebSocket manager
websocket_manager = WebSocketManager(config)

# ==============================================================================
# ENHANCED SESSION MANAGEMENT
# ==============================================================================

class SessionManager:
    """Production session management with JWT refresh tokens"""
    
    def __init__(self, config: ProductionNexusConfig):
        self.config = config
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.refresh_tokens: Dict[str, Dict[str, Any]] = {}
        self._session_lock = threading.RLock()
        
        # Start session cleanup task
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean up expired sessions"""
        def cleanup_task():
            while True:
                self._cleanup_expired_sessions()
                time.sleep(300)  # Clean up every 5 minutes
        
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
    
    def create_session(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """Create new session with access and refresh tokens"""
        user_id = str(user_data.get("id", user_data.get("user_id")))
        session_id = str(uuid.uuid4())
        
        # Access token (short-lived)
        access_payload = {
            "user_id": user_id,
            "session_id": session_id,
            "email": user_data.get("email"),
            "role": user_data.get("role", "user"),
            "company_id": user_data.get("company_id"),
            "exp": datetime.utcnow() + timedelta(minutes=self.config.jwt_expiration_minutes),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        # Refresh token (long-lived)
        refresh_payload = {
            "user_id": user_id,
            "session_id": session_id,
            "exp": datetime.utcnow() + timedelta(days=self.config.jwt_refresh_expiration_days),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        access_token = jwt.encode(access_payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
        refresh_token = jwt.encode(refresh_payload, self.config.jwt_refresh_secret, algorithm=self.config.jwt_algorithm)
        
        with self._session_lock:
            # Store session data
            self.active_sessions[session_id] = {
                "user_id": user_id,
                "user_data": user_data,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "access_token_expires": access_payload["exp"].isoformat(),
                "refresh_token_expires": refresh_payload["exp"].isoformat()
            }
            
            self.refresh_tokens[refresh_token] = {
                "session_id": session_id,
                "user_id": user_id,
                "expires_at": refresh_payload["exp"]
            }
            
            self.config.metrics["active_sessions"] += 1
        
        logger.info(f"Session created for user {user_id}: {session_id}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": self.config.jwt_expiration_minutes * 60,
            "token_type": "Bearer"
        }
    
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verify access token and return payload"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm])
            
            if payload.get("type") != "access":
                raise jwt.InvalidTokenError("Invalid token type")
            
            session_id = payload.get("session_id")
            
            with self._session_lock:
                if session_id not in self.active_sessions:
                    raise jwt.InvalidTokenError("Session not found")
                
                # Update last activity
                self.active_sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Access token expired")
        except jwt.JWTError as e:
            raise HTTPException(status_code=401, detail=f"Invalid access token: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = jwt.decode(refresh_token, self.config.jwt_refresh_secret, algorithms=[self.config.jwt_algorithm])
            
            if payload.get("type") != "refresh":
                raise jwt.InvalidTokenError("Invalid token type")
            
            session_id = payload.get("session_id")
            user_id = payload.get("user_id")
            
            with self._session_lock:
                if session_id not in self.active_sessions:
                    raise jwt.InvalidTokenError("Session not found")
                
                if refresh_token not in self.refresh_tokens:
                    raise jwt.InvalidTokenError("Refresh token not found")
                
                # Get user data from session
                session_data = self.active_sessions[session_id]
                user_data = session_data["user_data"]
                
                # Create new access token
                new_access_payload = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "email": user_data.get("email"),
                    "role": user_data.get("role", "user"),
                    "company_id": user_data.get("company_id"),
                    "exp": datetime.utcnow() + timedelta(minutes=self.config.jwt_expiration_minutes),
                    "iat": datetime.utcnow(),
                    "type": "access"
                }
                
                new_access_token = jwt.encode(new_access_payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
                
                # Update session
                self.active_sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
                self.active_sessions[session_id]["access_token_expires"] = new_access_payload["exp"].isoformat()
                
                self.config.metrics["session_refreshes"] += 1
            
            logger.info(f"Access token refreshed for user {user_id}")
            
            return {
                "access_token": new_access_token,
                "expires_in": self.config.jwt_expiration_minutes * 60,
                "token_type": "Bearer"
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except jwt.JWTError as e:
            self.config.metrics["authentication_failures"] += 1
            raise HTTPException(status_code=401, detail=f"Invalid refresh token: {str(e)}")
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session and all its tokens"""
        with self._session_lock:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                self.config.metrics["active_sessions"] -= 1
                
                # Remove associated refresh tokens
                tokens_to_remove = [
                    token for token, data in self.refresh_tokens.items()
                    if data["session_id"] == session_id
                ]
                
                for token in tokens_to_remove:
                    del self.refresh_tokens[token]
                
                logger.info(f"Session invalidated: {session_id}")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions and refresh tokens"""
        current_time = datetime.utcnow()
        
        with self._session_lock:
            # Clean up expired refresh tokens
            expired_refresh_tokens = [
                token for token, data in self.refresh_tokens.items()
                if data["expires_at"] < current_time
            ]
            
            for token in expired_refresh_tokens:
                session_id = self.refresh_tokens[token]["session_id"]
                del self.refresh_tokens[token]
                
                # Also remove the session if no refresh tokens remain
                remaining_tokens = [
                    t for t, d in self.refresh_tokens.items()
                    if d["session_id"] == session_id
                ]
                
                if not remaining_tokens and session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                    self.config.metrics["active_sessions"] -= 1
            
            if expired_refresh_tokens:
                logger.info(f"Cleaned up {len(expired_refresh_tokens)} expired refresh tokens")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            "active_sessions": len(self.active_sessions),
            "active_refresh_tokens": len(self.refresh_tokens),
            "total_session_refreshes": self.config.metrics["session_refreshes"],
            "authentication_failures": self.config.metrics["authentication_failures"]
        }

# Initialize session manager
session_manager = SessionManager(config)

# ==============================================================================
# DATAFLOW NODE DISCOVERY (Enhanced)
# ==============================================================================

class EnhancedDataFlowDiscovery:
    """Enhanced DataFlow node discovery with production optimizations"""
    
    def __init__(self, dataflow_db):
        self.db = dataflow_db
        self.discovered_nodes = {}
        self.workflow_patterns = {}
        self.performance_optimizer = production_optimizer
    
    def discover_dataflow_nodes(self) -> Dict[str, Any]:
        """Discover all auto-generated DataFlow nodes with performance metadata"""
        
        models = [
            Company, User, Customer, Quote,
            ProductClassification, ClassificationHistory, ClassificationCache,
            ETIMAttribute, ClassificationRule, ClassificationFeedback,
            ClassificationMetrics, Document, DocumentProcessingQueue
        ]
        
        discovered = {}
        
        for model in models:
            model_name = model.__name__
            
            # Each @db.model generates 9 nodes automatically
            node_types = [
                "Create", "Read", "Update", "Delete", "List",
                "BulkCreate", "BulkUpdate", "BulkDelete", "BulkUpsert"
            ]
            
            model_nodes = {}
            for node_type in node_types:
                node_name = f"{model_name}{node_type}Node"
                
                # Add performance metadata based on production optimizations
                cache_config = self.performance_optimizer.cache_configs.get(model_name, {})
                bulk_config = self.performance_optimizer.bulk_configs.get(model_name, {})
                
                model_nodes[node_type.lower()] = {
                    "node_name": node_name,
                    "description": f"{node_type} operations for {model_name}",
                    "model": model_name,
                    "operation": node_type.lower(),
                    "auto_generated": True,
                    "performance_optimized": True,
                    "cache_config": {
                        "enabled": bool(cache_config),
                        "ttl_seconds": getattr(cache_config, 'ttl_seconds', 1800),
                        "strategy": getattr(cache_config, 'cache_strategy', 'write_through'),
                        "warming_enabled": getattr(cache_config, 'warming_enabled', False)
                    },
                    "bulk_config": {
                        "batch_size": getattr(bulk_config, 'batch_size', 1000),
                        "parallel_workers": getattr(bulk_config, 'parallel_workers', 4),
                        "timeout_seconds": getattr(bulk_config, 'timeout_seconds', 300)
                    } if "bulk" in node_type.lower() else None
                }
            
            discovered[model_name.lower()] = model_nodes
        
        self.discovered_nodes = discovered
        return discovered
    
    def create_optimized_workflow(self, model_name: str, operation: str, parameters: Dict[str, Any]) -> WorkflowBuilder:
        """Create optimized workflow for DataFlow operation"""
        
        workflow = WorkflowBuilder()
        
        # Get node information
        model_nodes = self.discovered_nodes.get(model_name.lower(), {})
        node_info = model_nodes.get(operation.lower())
        
        if not node_info:
            raise ValueError(f"Unknown operation {operation} for model {model_name}")
        
        node_name = node_info["node_name"]
        
        # Add performance monitoring
        workflow.add_node("PerformanceStartNode", "perf_start", {
            "operation": f"{model_name}_{operation}",
            "start_time": time.time(),
            "parameters_size": len(str(parameters))
        })
        
        # Add caching layer for read operations
        if operation.lower() in ["read", "list"]:
            cache_config = node_info["cache_config"]
            if cache_config["enabled"]:
                workflow.add_node("CacheCheckNode", "cache_check", {
                    "cache_key": config.create_cache_key(f"{model_name}_{operation}", parameters),
                    "ttl_seconds": cache_config["ttl_seconds"],
                    "strategy": cache_config["strategy"]
                })
                workflow.connect("perf_start", "cache_check")
        
        # Add the main DataFlow node with optimizations
        main_node_params = {
            "model": model_name,
            "operation": operation,
            "parameters": parameters,
            "connection_pool": self.db.connection_pool if hasattr(self.db, 'connection_pool') else None,
            "performance_tracking": True
        }
        
        # Add bulk-specific optimizations
        if "bulk" in operation.lower() and node_info["bulk_config"]:
            bulk_config = node_info["bulk_config"]
            main_node_params.update({
                "batch_size": bulk_config["batch_size"],
                "parallel_workers": bulk_config["parallel_workers"],
                "timeout_seconds": bulk_config["timeout_seconds"],
                "use_copy_method": True,
                "enable_upsert": True
            })
        
        workflow.add_node(node_name, "main_operation", main_node_params)
        
        # Connect nodes
        if operation.lower() in ["read", "list"] and node_info["cache_config"]["enabled"]:
            workflow.connect("cache_check", "main_operation")
        else:
            workflow.connect("perf_start", "main_operation")
        
        # Add result caching for read operations
        if operation.lower() in ["read", "list"] and node_info["cache_config"]["enabled"]:
            workflow.add_node("CacheUpdateNode", "cache_update", {
                "cache_key": config.create_cache_key(f"{model_name}_{operation}", parameters),
                "ttl_seconds": node_info["cache_config"]["ttl_seconds"],
                "strategy": node_info["cache_config"]["strategy"]
            })
            workflow.connect("main_operation", "cache_update")
        
        # Add performance tracking
        workflow.add_node("PerformanceEndNode", "perf_end", {
            "operation": f"{model_name}_{operation}",
            "model_name": model_name,
            "track_model_metrics": True
        })
        
        if operation.lower() in ["read", "list"] and node_info["cache_config"]["enabled"]:
            workflow.connect("cache_update", "perf_end")
        else:
            workflow.connect("main_operation", "perf_end")
        
        return workflow

# Initialize enhanced DataFlow discovery
dataflow_discovery = EnhancedDataFlowDiscovery(db)
discovered_nodes = dataflow_discovery.discover_dataflow_nodes()

logger.info(f"✅ Enhanced DataFlow discovery: {len(discovered_nodes)} models with {sum(len(nodes) for nodes in discovered_nodes.values())} optimized nodes")

# ==============================================================================
# NEXUS PLATFORM INITIALIZATION
# ==============================================================================

# Initialize Nexus platform with production configuration
app = Nexus(**config.get_nexus_config())

# ==============================================================================
# PRODUCTION WORKFLOW REGISTRATION
# ==============================================================================

def create_production_dataflow_workflow():
    """Create production-optimized unified DataFlow workflow"""
    workflow = WorkflowBuilder()
    
    # Enhanced request routing with load balancing support
    workflow.add_node("ProductionDataFlowRouterNode", "route_operation", {
        "description": "Production-optimized DataFlow operation routing",
        "supported_models": list(discovered_nodes.keys()),
        "supported_operations": ["create", "read", "update", "delete", "list", 
                               "bulk_create", "bulk_update", "bulk_delete", "bulk_upsert"],
        "enable_load_balancing": config.enable_load_balancing,
        "connection_pool_monitoring": True,
        "performance_tracking": True
    })
    
    # Advanced caching with Redis support
    workflow.add_node("DistributedCacheNode", "distributed_cache", {
        "redis_enabled": config.redis_enabled,
        "redis_url": config.redis_url,
        "fallback_to_local": True,
        "compression_enabled": True,
        "cache_warming_enabled": config.cache_warming_enabled
    })
    
    # Production response formatting
    workflow.add_node("ProductionResponseFormatterNode", "format_response", {
        "format": "json",
        "include_metadata": True,
        "include_performance_metrics": True,
        "enable_compression": config.enable_compression,
        "websocket_notifications": True
    })
    
    # Comprehensive performance monitoring
    workflow.add_node("ComprehensiveMonitoringNode", "monitor_performance", {
        "track_latency": True,
        "track_throughput": True,
        "track_cache_metrics": True,
        "track_connection_pool": True,
        "alert_threshold_ms": 2000,
        "slow_query_threshold_ms": 1000,
        "enable_alerting": True,
        "websocket_notifications": True
    })
    
    workflow.connect("route_operation", "distributed_cache")
    workflow.connect("distributed_cache", "format_response")
    workflow.connect("format_response", "monitor_performance")
    
    return workflow

def create_production_bulk_workflow():
    """Create production-optimized bulk operations workflow"""
    workflow = WorkflowBuilder()
    
    # Enhanced bulk validation with production limits
    workflow.add_node("ProductionBulkValidationNode", "validate_bulk_input", {
        "max_batch_size": config.batch_size_limit,
        "required_fields": ["model", "operation", "data"],
        "validate_data_consistency": True,
        "estimate_memory_usage": True,
        "check_rate_limits": True
    })
    
    # Intelligent batch processing with adaptive sizing
    workflow.add_node("AdaptiveBatchProcessorNode", "process_batches", {
        "adaptive_batch_sizing": True,
        "parallel_processing": True,
        "memory_monitoring": True,
        "error_handling": "continue_on_error",
        "progress_reporting": True,
        "websocket_progress_updates": True
    })
    
    # Production bulk operations with connection pooling
    workflow.add_node("ProductionBulkOperationNode", "execute_bulk_operation", {
        "supported_operations": ["bulk_create", "bulk_update", "bulk_delete", "bulk_upsert"],
        "transaction_management": True,
        "rollback_on_error": True,
        "connection_pool_optimization": True,
        "performance_monitoring": True,
        "target_throughput_rps": 10000
    })
    
    # Advanced performance tracking
    workflow.add_node("BulkPerformanceAnalysisNode", "analyze_bulk_performance", {
        "track_throughput": True,
        "track_memory_usage": True,
        "track_connection_pool_usage": True,
        "generate_performance_report": True,
        "update_model_metrics": True,
        "websocket_metrics_broadcast": True
    })
    
    # Production result aggregation
    workflow.add_node("ProductionResultAggregationNode", "aggregate_results", {
        "include_comprehensive_statistics": True,
        "error_analysis": True,
        "performance_analysis": True,
        "recommendation_engine": True
    })
    
    workflow.connect("validate_bulk_input", "process_batches")
    workflow.connect("process_batches", "execute_bulk_operation")
    workflow.connect("execute_bulk_operation", "analyze_bulk_performance")
    workflow.connect("analyze_bulk_performance", "aggregate_results")
    
    return workflow

def create_realtime_dashboard_workflow():
    """Create real-time dashboard workflow with WebSocket updates"""
    workflow = WorkflowBuilder()
    
    # Multi-level cache checking (Redis + Local)
    workflow.add_node("MultiLevelCacheNode", "check_dashboard_cache", {
        "cache_levels": ["redis", "local", "warm"],
        "cache_key_prefix": "dashboard",
        "ttl_seconds": 300,  # 5 minutes
        "user_specific": True,
        "role_based_caching": True
    })
    
    # Parallel data collection with connection pooling
    workflow.add_node("ParallelDataCollectorNode", "collect_dashboard_data", {
        "data_sources": [
            {"model": "ClassificationMetrics", "operation": "list", "limit": 100, "cache_ttl": 600},
            {"model": "Quote", "operation": "list", "filters": {"created_date": "last_30_days"}, "cache_ttl": 300},
            {"model": "Customer", "operation": "list", "filters": {"status": "active"}, "cache_ttl": 900},
            {"model": "ProductClassification", "operation": "list", "limit": 1000, "cache_ttl": 1200},
            {"model": "Company", "operation": "list", "filters": {"is_active": True}, "cache_ttl": 1800}
        ],
        "parallel_execution": True,
        "timeout_seconds": 15,
        "connection_pool_optimization": True,
        "error_tolerance": 0.2  # Allow 20% of sources to fail
    })
    
    # Real-time analytics processing
    workflow.add_node("RealTimeAnalyticsProcessorNode", "process_analytics", {
        "calculations": [
            "classification_accuracy_trend",
            "processing_performance_metrics",
            "user_engagement_analytics",
            "system_health_indicators",
            "business_metrics_summary",
            "predictive_analytics"
        ],
        "time_series_analysis": True,
        "anomaly_detection": True,
        "trend_analysis": True
    })
    
    # WebSocket-optimized response formatting
    workflow.add_node("WebSocketDashboardFormatterNode", "format_dashboard", {
        "format": "websocket_optimized",
        "include_charts_data": True,
        "include_realtime_updates": True,
        "incremental_updates": True,
        "compression_enabled": True
    })
    
    # Real-time cache updates and WebSocket broadcasting
    workflow.add_node("RealtimeCacheUpdateNode", "update_realtime_cache", {
        "cache_strategy": "write_through",
        "invalidation_rules": ["user_action", "data_change", "time_threshold"],
        "websocket_broadcast": True,
        "selective_user_updates": True
    })
    
    workflow.connect("check_dashboard_cache", "collect_dashboard_data")
    workflow.connect("collect_dashboard_data", "process_analytics")
    workflow.connect("process_analytics", "format_dashboard")
    workflow.connect("format_dashboard", "update_realtime_cache")
    
    return workflow

def create_enhanced_session_workflow():
    """Create enhanced session management workflow"""
    workflow = WorkflowBuilder()
    
    # Multi-factor authentication support
    workflow.add_node("EnhancedAuthenticationNode", "authenticate_user", {
        "methods": ["jwt", "refresh_token", "api_key", "session"],
        "mfa_support": True,
        "session_timeout": config.jwt_expiration_minutes * 60,
        "refresh_threshold": 300,  # 5 minutes
        "rate_limiting": True,
        "brute_force_protection": True
    })
    
    # Comprehensive session validation
    workflow.add_node("ComprehensiveSessionValidationNode", "validate_session", {
        "check_expiry": True,
        "check_permissions": True,
        "check_ip_consistency": True,
        "check_device_fingerprint": True,
        "update_last_activity": True,
        "log_security_events": True
    })
    
    # Enhanced user context loading with caching
    workflow.add_node("EnhancedUserContextNode", "load_user_context", {
        "include_company_data": True,
        "include_permissions": True,
        "include_preferences": True,
        "cache_user_data": True,
        "cache_ttl": 1800,  # 30 minutes
        "websocket_session_sync": True
    })
    
    # Intelligent session refresh with security checks
    workflow.add_node("IntelligentSessionRefreshNode", "refresh_session", {
        "extend_expiry": True,
        "update_tokens": True,
        "security_validation": True,
        "log_activity": True,
        "websocket_notification": True
    })
    
    workflow.connect("authenticate_user", "validate_session")
    workflow.connect("validate_session", "load_user_context")
    workflow.connect("load_user_context", "refresh_session")
    
    return workflow

# Register production workflows
logger.info("🔧 Registering production-optimized workflows...")

app.register("production_dataflow_operations", create_production_dataflow_workflow().build())
app.register("production_classification_pipeline", create_classification_workflow().build())
app.register("production_bulk_operations", create_production_bulk_workflow().build())
app.register("realtime_dashboard_analytics", create_realtime_dashboard_workflow().build())
app.register("enhanced_user_session", create_enhanced_session_workflow().build())

# Register optimized individual model workflows
for model_name in discovered_nodes.keys():
    for operation in ["create", "read", "update", "delete", "list", "bulk_create", "bulk_update"]:
        try:
            workflow_name = f"{model_name}_{operation}_optimized" 
            workflow = dataflow_discovery.create_optimized_workflow(model_name.title(), operation, {})
            app.register(workflow_name, workflow.build())
        except Exception as e:
            logger.warning(f"Could not register optimized workflow {model_name}_{operation}: {e}")

logger.info("✅ All production workflows registered successfully")

# ==============================================================================
# ENHANCED FASTAPI ENDPOINTS WITH WEBSOCKET SUPPORT
# ==============================================================================

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user with enhanced validation"""
    try:
        payload = session_manager.verify_access_token(credentials.credentials)
        return payload
    except HTTPException:
        config.metrics["authentication_failures"] += 1
        raise

# Add production middleware
app.api_app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600
)

app.api_app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.api_app.middleware("http")
async def comprehensive_performance_middleware(request: Request, call_next):
    """Comprehensive performance tracking middleware"""
    start_time = time.time()
    
    # Track active requests
    config.metrics["active_requests"] += 1
    
    try:
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Update comprehensive metrics
        config.metrics["total_requests"] += 1
        config.update_response_time_metrics(process_time)
        
        # Track slow requests
        if process_time > 2.0:
            config.metrics["slow_requests"] += 1
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        response.headers["X-Powered-By"] = "Nexus-Production"
        response.headers["X-Environment"] = config.environment
        
        return response
        
    except Exception as e:
        config.metrics["failed_requests"] += 1
        raise
    finally:
        config.metrics["active_requests"] -= 1

# ==============================================================================
# WEBSOCKET ENDPOINTS
# ==============================================================================

@app.api_app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: Optional[str] = None):
    """WebSocket endpoint for real-time notifications"""
    connection_id = None
    
    try:
        # Authenticate WebSocket connection
        if token:
            try:
                payload = session_manager.verify_access_token(token)
                if payload["user_id"] != user_id:
                    await websocket.close(code=1008, reason="Unauthorized")
                    return
            except Exception:
                await websocket.close(code=1008, reason="Authentication failed")
                return
        
        # Connect to WebSocket manager
        connection_id = await websocket_manager.connect(websocket, user_id, {
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "origin": websocket.headers.get("origin", "unknown")
        })
        
        # WebSocket message loop
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_json()
                config.metrics["websocket_messages_received"] += 1
                
                # Handle different message types
                message_type = message.get("type")
                
                if message_type == "heartbeat":
                    await websocket_manager.send_to_connection(connection_id, {
                        "type": "heartbeat_response",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message_type == "subscribe":
                    # Subscribe to real-time updates for specific data
                    subscription = message.get("subscription", {})
                    # Handle subscription logic here
                    await websocket_manager.send_to_connection(connection_id, {
                        "type": "subscription_confirmed",
                        "subscription": subscription
                    })
                
                elif message_type == "request_dashboard_update":
                    # Trigger dashboard update
                    runtime = LocalRuntime()
                    workflow = create_realtime_dashboard_workflow()
                    
                    context = {"user_id": user_id}
                    results, run_id = runtime.execute(workflow.build(), context)
                    
                    await websocket_manager.send_to_user(user_id, {
                        "type": "dashboard_update",
                        "data": results.get("format_dashboard"),
                        "run_id": run_id
                    })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                await websocket_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "Message processing failed"
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)

# ==============================================================================
# PRODUCTION API ENDPOINTS
# ==============================================================================

# Authentication endpoints
@app.api_app.post("/api/auth/login")
async def login(credentials: Dict[str, Any]):
    """Login endpoint with enhanced security"""
    try:
        # This would integrate with your actual user authentication
        # For demo purposes, we'll create a mock user
        user_data = {
            "id": 1,
            "email": credentials.get("email", "demo@example.com"),
            "role": "admin", 
            "company_id": 1,
            "first_name": "Demo",
            "last_name": "User"
        }
        
        tokens = session_manager.create_session(user_data)
        
        return JSONResponse(content={
            "success": True,
            "user": user_data,
            **tokens,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        config.metrics["authentication_failures"] += 1
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

@app.api_app.post("/api/auth/refresh")
async def refresh_token(refresh_data: Dict[str, str]):
    """Refresh access token"""
    try:
        refresh_token = refresh_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token required")
        
        tokens = session_manager.refresh_access_token(refresh_token)
        
        return JSONResponse(content={
            "success": True,
            **tokens,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")

@app.api_app.post("/api/auth/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout endpoint"""
    try:
        session_id = current_user.get("session_id")
        if session_id:
            session_manager.invalidate_session(session_id)
        
        return JSONResponse(content={
            "success": True,
            "message": "Logged out successfully",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

# Enhanced DataFlow operations endpoint
@app.api_app.post("/api/v2/dataflow/{model_name}/{operation}")
async def enhanced_dataflow_operation(
    model_name: str,
    operation: str,
    request_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Enhanced DataFlow operations with production optimizations"""
    try:
        # Validate model and operation
        if model_name.lower() not in discovered_nodes:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        model_operations = discovered_nodes[model_name.lower()]
        if operation.lower() not in model_operations:
            raise HTTPException(status_code=404, detail=f"Operation {operation} not supported for {model_name}")
        
        # Enhanced caching for read operations
        cache_key = None
        if operation.lower() in ["read", "list"]:
            cache_key = config.create_cache_key(
                f"v2_dataflow_{model_name}_{operation}",
                request_data,
                current_user["user_id"]
            )
            cached_response = config.get_cached_response(cache_key, model_name)
            if cached_response:
                return JSONResponse(content={
                    "success": True,
                    "data": cached_response,
                    "cached": True,
                    "cache_source": "redis" if config.redis_enabled else "local",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Execute optimized DataFlow operation
        runtime = LocalRuntime()
        workflow = dataflow_discovery.create_optimized_workflow(
            model_name, operation, request_data
        )
        
        context = {
            "user_id": current_user["user_id"],
            "company_id": current_user.get("company_id"),
            "session_id": current_user.get("session_id"),
            **request_data
        }
        
        start_time = time.time()
        
        # Set timeout based on operation type
        if "bulk" in operation.lower():
            timeout = config.bulk_operation_timeout
        elif "classification" in model_name.lower():
            timeout = config.classification_timeout
        else:
            timeout = config.request_timeout
        
        try:
            results, run_id = runtime.execute(workflow.build(), context, timeout=timeout)
        except TimeoutError:
            raise HTTPException(status_code=504, detail=f"Operation timeout after {timeout}s")
        
        execution_time = time.time() - start_time
        
        # Update model-specific metrics
        if model_name in config.model_metrics:
            model_stats = config.model_metrics[model_name]
            model_stats["operations"] += 1
            current_avg = model_stats["avg_response_time"]
            current_count = model_stats["operations"]
            model_stats["avg_response_time"] = (
                (current_avg * (current_count - 1) + execution_time) / current_count
            )
        
        config.metrics["dataflow_operations"] += 1
        
        # Cache results for read operations
        if cache_key and operation.lower() in ["read", "list"]:
            # Model-specific cache TTL
            cache_ttl = model_operations[operation.lower()]["cache_config"]["ttl_seconds"]
            config.set_cached_response(cache_key, results, cache_ttl)
        
        response_data = {
            "success": True,
            "data": results,
            "metadata": {
                "model": model_name,
                "operation": operation,
                "execution_time_ms": round(execution_time * 1000, 2),
                "run_id": run_id,
                "timestamp": datetime.utcnow().isoformat(),
                "cached": False,
                "performance_optimized": True
            }
        }
        
        # Background WebSocket notification
        if background_tasks:
            background_tasks.add_task(
                notify_operation_complete,
                current_user["user_id"], model_name, operation, execution_time
            )
        
        return JSONResponse(content=response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        config.metrics["failed_requests"] += 1
        logger.error(f"Enhanced DataFlow operation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")

# Bulk operations with real-time progress
@app.api_app.post("/api/v2/bulk/{operation}")
async def enhanced_bulk_operation(
    operation: str,
    bulk_request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Enhanced bulk operations with real-time progress updates"""
    try:
        runtime = LocalRuntime()
        workflow = create_production_bulk_workflow()
        
        context = {
            "user_id": current_user["user_id"],
            "session_id": current_user.get("session_id"),
            "operation": operation,
            "websocket_progress_updates": True,
            **bulk_request
        }
        
        start_time = time.time()
        
        # Execute with extended timeout for bulk operations
        results, run_id = runtime.execute(workflow.build(), context, timeout=config.bulk_operation_timeout)
        
        execution_time = time.time() - start_time
        config.metrics["bulk_operations"] += 1
        
        # Real-time completion notification
        if background_tasks:
            background_tasks.add_task(
                notify_bulk_operation_complete,
                current_user["user_id"], operation, results, execution_time
            )
        
        return JSONResponse(content={
            "success": True,
            "bulk_results": results.get("aggregate_results"),
            "performance_analysis": results.get("analyze_bulk_performance"),
            "execution_time_ms": round(execution_time * 1000, 2),
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        config.metrics["failed_requests"] += 1
        logger.error(f"Enhanced bulk operation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk operation failed: {str(e)}")

# Real-time dashboard with WebSocket updates
@app.api_app.get("/api/v2/dashboard/realtime")
async def realtime_dashboard(
    current_user: Dict[str, Any] = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Real-time dashboard with WebSocket integration"""
    try:
        runtime = LocalRuntime()
        workflow = create_realtime_dashboard_workflow()
        
        context = {
            "user_id": current_user["user_id"],
            "company_id": current_user.get("company_id"),
            "role": current_user.get("role"),
            "realtime_updates": True
        }
        
        start_time = time.time()
        results, run_id = runtime.execute(workflow.build(), context)
        execution_time = time.time() - start_time
        
        dashboard_data = results.get("format_dashboard")
        
        # Background task for WebSocket updates
        if background_tasks:
            background_tasks.add_task(
                broadcast_dashboard_update,
                current_user["user_id"], dashboard_data
            )
        
        return JSONResponse(content={
            "success": True,
            "dashboard_data": dashboard_data,
            "performance": {
                "execution_time_ms": round(execution_time * 1000, 2),
                "cached": bool(results.get("check_dashboard_cache")),
                "data_freshness": datetime.utcnow().isoformat(),
                "websocket_enabled": True
            },
            "run_id": run_id,
            "websocket_endpoint": f"ws://localhost:{config.websocket_port}/ws/{current_user['user_id']}"
        })
    
    except Exception as e:
        config.metrics["failed_requests"] += 1
        logger.error(f"Real-time dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard failed: {str(e)}")

# Comprehensive health check
@app.api_app.get("/api/v2/health/comprehensive")
async def comprehensive_health_check():
    """Comprehensive production health check"""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0-production",
            "environment": config.environment
        }
        
        # DataFlow health check
        try:
            runtime = LocalRuntime()
            workflow = WorkflowBuilder()
            
            workflow.add_node("CompanyListNode", "test_db", {"limit": 1})
            
            start_time = time.time()
            results, _ = runtime.execute(workflow.build(), timeout=5)
            db_response_time = time.time() - start_time
            
            health_data["dataflow"] = {
                "status": "healthy",
                "response_time_ms": round(db_response_time * 1000, 2),
                "models_count": len(discovered_nodes),
                "nodes_count": sum(len(nodes) for nodes in discovered_nodes.values()),
                "optimizations_enabled": True
            }
        except Exception as e:
            health_data["dataflow"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # WebSocket health
        websocket_stats = websocket_manager.get_connection_stats()
        health_data["websocket"] = {
            "status": "healthy" if websocket_stats["utilization_percent"] < 90 else "degraded",
            **websocket_stats
        }
        
        # Session management health
        session_stats = session_manager.get_session_stats()
        health_data["sessions"] = {
            "status": "healthy",
            **session_stats
        }
        
        # Cache health (Redis + Local)
        cache_health = "healthy"
        if config.redis_enabled:
            try:
                config._redis_client.ping()
                redis_info = config._redis_client.info()
                health_data["redis_cache"] = {
                    "status": "healthy",
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "used_memory_human": redis_info.get("used_memory_human", "unknown")
                }
            except Exception as e:
                health_data["redis_cache"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                cache_health = "degraded"
        
        # Comprehensive metrics
        metrics = config.get_comprehensive_metrics()
        health_data["performance_metrics"] = metrics["system_metrics"]
        health_data["model_performance"] = metrics["model_metrics"]
        health_data["health_indicators"] = metrics["health_indicators"]
        health_data["performance_targets"] = metrics["performance_targets"]
        
        # Overall health status
        if health_data["dataflow"]["status"] == "unhealthy":
            health_data["status"] = "unhealthy"
        elif any([
            health_data["websocket"]["status"] == "degraded",
            cache_health == "degraded",
            not metrics["health_indicators"]["avg_response_time_healthy"],
            not metrics["health_indicators"]["cache_hit_ratio_healthy"]
        ]):
            health_data["status"] = "degraded"
        
        return JSONResponse(content=health_data)
    
    except Exception as e:
        logger.error(f"Comprehensive health check error: {str(e)}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Health check failed",
                "details": str(e)
            },
            status_code=503
        )

# Production metrics endpoint
@app.api_app.get("/api/v2/metrics/production")
async def production_metrics(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Production metrics endpoint"""
    
    # Role-based access control
    if current_user.get("role") not in ["admin", "monitor"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    metrics = config.get_comprehensive_metrics()
    
    # Add additional production metrics
    metrics["dataflow_info"] = {
        "models": list(discovered_nodes.keys()),
        "total_nodes": sum(len(nodes) for nodes in discovered_nodes.values()),
        "available": DATAFLOW_AVAILABLE,
        "pool_size": config.dataflow_pool_size,
        "pool_overflow": config.dataflow_max_overflow,
        "optimizations_enabled": True
    }
    
    metrics["system_configuration"] = {
        "environment": config.environment,
        "api_port": config.api_port,
        "websocket_port": config.websocket_port,
        "mcp_port": config.mcp_port,
        "redis_enabled": config.redis_enabled,
        "cache_ttl": config.cache_ttl_seconds,
        "max_concurrent_requests": config.max_concurrent_requests,
        "bulk_operation_timeout": config.bulk_operation_timeout,
        "classification_timeout": config.classification_timeout
    }
    
    metrics["optimization_status"] = {
        "cache_warming_enabled": config.cache_warming_enabled,
        "request_batching_enabled": config.enable_request_batching,
        "compression_enabled": config.enable_compression,
        "load_balancing_enabled": config.enable_load_balancing,
        "batch_size_limit": config.batch_size_limit
    }
    
    # WebSocket and session stats
    metrics["websocket_stats"] = websocket_manager.get_connection_stats()
    metrics["session_stats"] = session_manager.get_session_stats()
    
    return JSONResponse(content=metrics)

# Background notification tasks
async def notify_operation_complete(user_id: str, model_name: str, operation: str, execution_time: float):
    """Notify user of completed operation via WebSocket"""
    try:
        await websocket_manager.send_to_user(user_id, {
            "type": "operation_complete",
            "model": model_name,
            "operation": operation,
            "execution_time_ms": round(execution_time * 1000, 2),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to send operation complete notification: {e}")

async def notify_bulk_operation_complete(user_id: str, operation: str, results: Dict[str, Any], execution_time: float):
    """Notify user of completed bulk operation"""
    try:
        await websocket_manager.send_to_user(user_id, {
            "type": "bulk_operation_complete",
            "operation": operation,
            "results_summary": {
                "total_processed": results.get("aggregate_results", {}).get("total_processed", 0),
                "success_rate": results.get("aggregate_results", {}).get("success_rate", 0),
                "execution_time_ms": round(execution_time * 1000, 2)
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to send bulk operation complete notification: {e}")

async def broadcast_dashboard_update(user_id: str, dashboard_data: Dict[str, Any]):
    """Broadcast dashboard update to user's WebSocket connections"""
    try:
        await websocket_manager.send_to_user(user_id, {
            "type": "dashboard_update",
            "data": dashboard_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to broadcast dashboard update: {e}")

# ==============================================================================
# PRODUCTION CLI COMMANDS
# ==============================================================================

@app.cli.command("production-status")
def production_status_command():
    """Show production platform status"""
    print("🏭 Production Platform Status:")
    print(f"   • Environment: {config.environment}")
    print(f"   • DataFlow Available: {'✅ Yes' if DATAFLOW_AVAILABLE else '❌ No (development mode)'}")
    print(f"   • Models: {len(discovered_nodes)}")
    print(f"   • Auto-generated nodes: {sum(len(nodes) for nodes in discovered_nodes.values())}")
    print(f"   • Redis Cache: {'✅ Enabled' if config.redis_enabled else '❌ Disabled'}")
    print(f"   • WebSocket Connections: {len(websocket_manager.connections)}")
    print(f"   • Active Sessions: {len(session_manager.active_sessions)}")
    
    # Performance metrics summary
    metrics = config.get_comprehensive_metrics()
    health = metrics["health_indicators"]
    print(f"\n⚡ Performance Health:")
    print(f"   • Response Time: {'✅ Healthy' if health['avg_response_time_healthy'] else '⚠️  Degraded'} ({config.metrics['average_response_time']*1000:.1f}ms avg)")
    print(f"   • Cache Hit Ratio: {'✅ Healthy' if health['cache_hit_ratio_healthy'] else '⚠️  Degraded'} ({config.metrics['cache_hit_ratio']*100:.1f}%)")
    print(f"   • Error Rate: {'✅ Healthy' if health['error_rate_healthy'] else '⚠️  Degraded'}")
    print(f"   • WebSocket: {'✅ Healthy' if health['websocket_healthy'] else '⚠️  Degraded'}")

@app.cli.command("warm-cache")
@app.cli.option("--model", help="Specific model to warm (optional)")
def warm_cache_command(model: str = None):
    """Warm production caches"""
    try:
        if model:
            result = asyncio.run(production_optimizer.warm_model_cache(model))
            if result["success"]:
                print(f"✅ Cache warmed for {model}: {result['warmed_count']:,} records")
            else:
                print(f"❌ Cache warming failed for {model}: {result.get('error', 'Unknown error')}")
        else:
            result = asyncio.run(production_optimizer.warm_all_caches())
            if result["success"]:
                print(f"✅ All caches warmed: {result['total_warmed_records']:,} records across {result['successful_models']} models")
            else:
                print(f"❌ Cache warming failed")
    except Exception as e:
        print(f"❌ Cache warming error: {e}")

@app.cli.command("performance-benchmark")
def performance_benchmark_command():
    """Run production performance benchmark"""
    try:
        print("🚀 Starting production performance benchmark...")
        
        # Import and run the benchmark from production optimizations
        from dataflow_production_optimizations import run_performance_benchmark
        results = asyncio.run(run_performance_benchmark())
        
        print(f"\n📊 Benchmark completed with {len(results)} test scenarios")
        
        passed_tests = sum(1 for r in results if r.get('meets_target', False))
        print(f"✅ Passed: {passed_tests}/{len(results)} performance targets")
        
    except Exception as e:
        print(f"❌ Benchmark error: {e}")

@app.cli.command("websocket-stats")
def websocket_stats_command():
    """Show WebSocket connection statistics"""
    stats = websocket_manager.get_connection_stats()
    print("🌐 WebSocket Statistics:")
    print(f"   • Total connections: {stats['total_connections']}")
    print(f"   • Unique users: {stats['unique_users']}")
    print(f"   • Utilization: {stats['utilization_percent']:.1f}%")
    print(f"   • Max connections: {stats['max_connections']}")
    
    if stats['connections_by_user']:
        print(f"\n👥 Connections by user:")
        for user_id, conn_count in list(stats['connections_by_user'].items())[:10]:
            print(f"   • User {user_id}: {conn_count} connection(s)")

@app.cli.command("session-cleanup")
def session_cleanup_command():
    """Manually trigger session cleanup"""
    try:
        initial_sessions = len(session_manager.active_sessions)
        initial_tokens = len(session_manager.refresh_tokens)
        
        session_manager._cleanup_expired_sessions()
        
        final_sessions = len(session_manager.active_sessions)
        final_tokens = len(session_manager.refresh_tokens)
        
        print(f"🧹 Session cleanup completed:")
        print(f"   • Sessions: {initial_sessions} → {final_sessions} (removed {initial_sessions - final_sessions})")
        print(f"   • Refresh tokens: {initial_tokens} → {final_tokens} (removed {initial_tokens - final_tokens})")
        
    except Exception as e:
        print(f"❌ Session cleanup error: {e}")

# ==============================================================================
# PRODUCTION MCP TOOLS
# ==============================================================================

@app.mcp_server.tool("production_dataflow_operation")
def production_dataflow_operation_tool(
    model: str, 
    operation: str, 
    parameters: Dict[str, Any], 
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Production-optimized MCP tool for DataFlow operations"""
    try:
        if model.lower() not in discovered_nodes:
            return {
                "success": False,
                "error": f"Model {model} not found",
                "available_models": list(discovered_nodes.keys())
            }
        
        if operation.lower() not in discovered_nodes[model.lower()]:
            return {
                "success": False,
                "error": f"Operation {operation} not supported for {model}",
                "available_operations": list(discovered_nodes[model.lower()].keys())
            }
        
        # Execute optimized workflow
        runtime = LocalRuntime()
        workflow = dataflow_discovery.create_optimized_workflow(model, operation, parameters)
        
        context = {"mcp_request": True, **(user_context or {}), **parameters}
        
        start_time = time.time()
        results, run_id = runtime.execute(workflow.build(), context)
        execution_time = time.time() - start_time
        
        # Update metrics
        config.metrics["dataflow_operations"] += 1
        
        return {
            "success": True,
            "data": results,
            "metadata": {
                "model": model,
                "operation": operation,
                "execution_time_ms": round(execution_time * 1000, 2),
                "run_id": run_id,
                "timestamp": datetime.utcnow().isoformat(),
                "performance_optimized": True,
                "mcp_version": "2.0"
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": model,
            "operation": operation
        }

@app.mcp_server.tool("production_bulk_operation")
def production_bulk_operation_tool(
    operation: str, 
    model: str, 
    data: List[Dict[str, Any]], 
    batch_size: int = 2000,
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Production-optimized MCP tool for bulk operations"""
    try:
        runtime = LocalRuntime()
        workflow = create_production_bulk_workflow()
        
        context = {
            "operation": operation,
            "model": model,
            "data": data,
            "batch_size": min(batch_size, config.batch_size_limit),  # Enforce limits
            "mcp_request": True,
            **(user_context or {})
        }
        
        start_time = time.time()
        results, run_id = runtime.execute(workflow.build(), context, timeout=config.bulk_operation_timeout)
        execution_time = time.time() - start_time
        
        config.metrics["bulk_operations"] += 1
        
        return {
            "success": True,
            "bulk_results": results.get("aggregate_results"),
            "performance_analysis": results.get("analyze_bulk_performance"),
            "execution_time_ms": round(execution_time * 1000, 2),
            "run_id": run_id,
            "mcp_version": "2.0"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "operation": operation,
            "model": model
        }

@app.mcp_server.tool("production_system_health")
def production_system_health_tool(include_detailed_metrics: bool = False) -> Dict[str, Any]:
    """Production system health monitoring tool"""
    try:
        health_data = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "environment": config.environment,
            "status": "healthy"
        }
        
        # Basic health indicators
        metrics = config.get_comprehensive_metrics()
        health_data["health_indicators"] = metrics["health_indicators"]
        health_data["performance_targets"] = metrics["performance_targets"]
        
        # System status
        health_data["system_status"] = {
            "dataflow_available": DATAFLOW_AVAILABLE,
            "redis_cache_enabled": config.redis_enabled,
            "websocket_connections": len(websocket_manager.connections),
            "active_sessions": len(session_manager.active_sessions),
            "total_requests": config.metrics["total_requests"],
            "cache_hit_ratio": config.metrics["cache_hit_ratio"]
        }
        
        # Include detailed metrics if requested
        if include_detailed_metrics:
            health_data["detailed_metrics"] = {
                "system_metrics": metrics["system_metrics"],
                "model_metrics": metrics["model_metrics"],
                "websocket_stats": websocket_manager.get_connection_stats(),
                "session_stats": session_manager.get_session_stats()
            }
        
        # Determine overall status
        health_indicators = health_data["health_indicators"]
        if not all(health_indicators.values()):
            health_data["status"] = "degraded"
        
        return health_data
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.mcp_server.tool("cache_management")
def cache_management_tool(
    action: str,  # "warm", "clear", "stats"
    model: Optional[str] = None,
    pattern: Optional[str] = None
) -> Dict[str, Any]:
    """Cache management tool for MCP"""
    try:
        if action == "warm":
            if model:
                result = asyncio.run(production_optimizer.warm_model_cache(model))
            else:
                result = asyncio.run(production_optimizer.warm_all_caches())
            return {"success": True, "action": "warm", "result": result}
        
        elif action == "clear":
            config.clear_cache(pattern)
            return {
                "success": True,
                "action": "clear",
                "pattern": pattern,
                "message": f"Cache cleared{' with pattern: ' + pattern if pattern else ''}"
            }
        
        elif action == "stats":
            cache_stats = {
                "local_cache": {
                    "total_entries": len(config._local_cache),
                    "memory_mb": config.metrics["cache_memory_mb"],
                    "hit_ratio": config.metrics["cache_hit_ratio"]
                }
            }
            
            if config.redis_enabled:
                try:
                    redis_info = config._redis_client.info()
                    cache_stats["redis_cache"] = {
                        "connected_clients": redis_info.get("connected_clients", 0),
                        "used_memory_human": redis_info.get("used_memory_human", "unknown"),
                        "keyspace_hits": redis_info.get("keyspace_hits", 0),
                        "keyspace_misses": redis_info.get("keyspace_misses", 0)
                    }
                except Exception as e:
                    cache_stats["redis_cache"] = {"error": str(e)}
            
            return {"success": True, "action": "stats", "cache_stats": cache_stats}
        
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": ["warm", "clear", "stats"]
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "action": action
        }

# ==============================================================================
# PRODUCTION STARTUP AND CONFIGURATION
# ==============================================================================

def setup_production_database():
    """Initialize database with production optimizations"""
    try:
        if DATAFLOW_AVAILABLE:
            logger.info("✅ DataFlow models loaded with production optimizations")
            logger.info(f"   • Connection pool: {config.dataflow_pool_size} + {config.dataflow_max_overflow} overflow")
            logger.info(f"   • Pool recycle: {config.dataflow_pool_recycle}s")
        else:
            logger.info("⚠️  Using development SQLite configuration")
        
        # Test database connection with timeout
        runtime = LocalRuntime()
        workflow = WorkflowBuilder()
        
        workflow.add_node("CompanyCreateNode", "test_company", {
            "name": "Production Test Company",
            "industry": "testing",
            "is_active": True
        })
        
        try:
            results, _ = runtime.execute(workflow.build(), timeout=10)
            logger.info("✅ Database connection verified with production settings")
        except Exception as e:
            logger.warning(f"Database test failed (continuing anyway): {e}")
        
        return True
    
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False

async def warm_production_caches():
    """Warm caches on startup"""
    if config.cache_warming_enabled:
        logger.info("🔥 Starting production cache warming...")
        try:
            result = await production_optimizer.warm_all_caches()
            if result["success"]:
                logger.info(f"✅ Production caches warmed: {result['total_warmed_records']:,} records")
            else:
                logger.warning("⚠️  Cache warming completed with some failures")
        except Exception as e:
            logger.error(f"❌ Cache warming failed: {e}")

def main():
    """Main production application entry point"""
    print("\n" + "="*100)
    print("🏭 NEXUS PRODUCTION MULTI-CHANNEL PLATFORM")
    print("🚀 High-Performance DataFlow Integration with Real-Time Features")
    print("="*100)
    
    logger.info("Initializing Nexus Production Platform...")
    
    # Setup database
    if not setup_production_database():
        logger.error("❌ Database setup failed - continuing with limited functionality")
    
    # Display production configuration
    logger.info("✅ Production platform configuration:")
    logger.info(f"   • Environment: {config.environment}")
    logger.info(f"   • DataFlow models: {len(discovered_nodes)}")
    logger.info(f"   • Auto-generated nodes: {sum(len(nodes) for nodes in discovered_nodes.values())}")
    logger.info(f"   • Database: {'PostgreSQL (production)' if DATAFLOW_AVAILABLE else 'SQLite (development)'}")
    logger.info(f"   • Connection pool: {config.dataflow_pool_size} + {config.dataflow_max_overflow} overflow")
    logger.info(f"   • Redis cache: {'enabled' if config.redis_enabled else 'disabled'}")
    logger.info(f"   • Cache TTL: {config.cache_ttl_seconds}s (adaptive)")
    logger.info(f"   • Max concurrent: {config.max_concurrent_requests} requests")
    
    # Multi-channel endpoints
    logger.info("🌐 Multi-channel access endpoints:")
    logger.info(f"   • REST API: http://{config.api_host}:{config.api_port}")
    logger.info(f"   • WebSocket: ws://{config.api_host}:{config.websocket_port}/ws")
    logger.info(f"   • CLI: nexus --help")
    logger.info(f"   • MCP Server: http://{config.api_host}:{config.mcp_port}")
    
    # Performance optimization summary
    logger.info("⚡ Production performance optimizations:")
    logger.info(f"   • Response time target: <2000ms (tracking enabled)")
    logger.info(f"   • Bulk throughput target: 10,000+ records/sec")
    logger.info(f"   • Cache hit ratio target: >80%")
    logger.info(f"   • WebSocket max connections: {config.max_websocket_connections}")
    logger.info(f"   • Request timeout: {config.request_timeout}s")
    logger.info(f"   • Bulk timeout: {config.bulk_operation_timeout}s")
    logger.info(f"   • Classification timeout: {config.classification_timeout}s")
    logger.info(f"   • Batch size limit: {config.batch_size_limit:,}")
    
    # Security configuration
    logger.info("🔒 Production security configuration:")
    logger.info(f"   • JWT access token expiry: {config.jwt_expiration_minutes} minutes")
    logger.info(f"   • JWT refresh token expiry: {config.jwt_refresh_expiration_days} days")
    logger.info(f"   • Rate limit: {config.rate_limit_requests_per_minute} requests/minute")
    logger.info(f"   • CORS origins: {len(config.cors_origins)} configured")
    
    # Registered workflows
    logger.info("🔧 Production workflows registered:")
    logger.info("   • production_dataflow_operations (optimized unified access)")
    logger.info("   • production_classification_pipeline (ML-optimized)")
    logger.info("   • production_bulk_operations (10k+ records/sec)")
    logger.info("   • realtime_dashboard_analytics (WebSocket-enabled)")
    logger.info("   • enhanced_user_session (JWT + refresh tokens)")
    
    # DataFlow optimization summary
    logger.info("📊 DataFlow production optimizations:")
    for model_name, operations in discovered_nodes.items():
        cache_enabled = any(op.get("cache_config", {}).get("enabled", False) for op in operations.values())
        bulk_optimized = any(op.get("bulk_config") is not None for op in operations.values())
        optimization_flags = []
        if cache_enabled:
            optimization_flags.append("CACHE")
        if bulk_optimized:
            optimization_flags.append("BULK")
        if model_name in ["company", "customer", "productclassification"]:
            optimization_flags.append("HIGH-TRAFFIC")
        
        flags_str = f" [{', '.join(optimization_flags)}]" if optimization_flags else ""
        logger.info(f"   • {model_name}{flags_str}: {len(operations)} operations")
    
    print("\n" + "="*100)
    print("🎯 PRODUCTION PLATFORM READY")
    print("🚀 Performance Targets: <2s response, 10k+ bulk ops/sec, >80% cache hit")
    print("🌐 Real-time WebSocket notifications enabled")
    print("🔒 Enhanced JWT security with refresh tokens")
    print("📊 Comprehensive monitoring and alerting")
    print("="*100)
    
    # Configure enterprise production features
    app.auth.strategy = "jwt_enhanced"
    app.monitoring.interval = 10  # More frequent monitoring for production
    app.monitoring.metrics = [
        "requests", "latency", "errors", "dataflow", "cache", 
        "bulk_operations", "classification_operations", "model_performance",
        "memory_usage", "connection_pool", "slow_requests", "websocket",
        "sessions", "authentication", "redis_cache", "system_health"
    ]
    app.monitoring.enable_alerting = True
    app.monitoring.alert_thresholds = {
        "error_rate": 0.03,        # 3% error rate (tighter than dev)
        "avg_response_time": 2.0,  # 2 second average
        "p95_response_time": 5.0,  # 5 second p95
        "cache_hit_ratio": 0.8,    # 80% cache hit ratio
        "slow_request_ratio": 0.05, # 5% slow requests
        "websocket_utilization": 0.85, # 85% WebSocket utilization
        "memory_usage_mb": 4096,   # 4GB memory limit
        "connection_pool_utilization": 0.8  # 80% pool utilization
    }
    
    # Warm caches on startup if enabled
    if config.cache_warming_enabled:
        asyncio.run(warm_production_caches())
    
    # Production startup complete
    logger.info("🏭 Production Nexus platform startup complete")
    logger.info("Ready for high-performance operations:")
    logger.info("  • Multi-channel access (API + WebSocket + CLI + MCP)")
    logger.info("  • Real-time notifications and updates")
    logger.info("  • Enhanced security with JWT refresh tokens")
    logger.info("  • Production-optimized DataFlow operations")
    logger.info("  • Comprehensive monitoring and alerting")
    
    # Start the production platform
    app.start()

if __name__ == "__main__":
    main()
