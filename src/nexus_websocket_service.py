"""
Nexus WebSocket Service
Dedicated WebSocket server for real-time communication with load balancing and session management
"""

import asyncio
import json
import logging
import signal
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from pathlib import Path

import aioredis
import jwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

# Metrics
websocket_connections = Gauge('nexus_websocket_connections_total', 'Total WebSocket connections')
websocket_messages_sent = Counter('nexus_websocket_messages_sent_total', 'Total messages sent')
websocket_messages_received = Counter('nexus_websocket_messages_received_total', 'Total messages received')
websocket_connection_duration = Histogram('nexus_websocket_connection_duration_seconds', 'Connection duration')
websocket_message_processing_time = Histogram('nexus_websocket_message_processing_seconds', 'Message processing time')

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

class WebSocketConnectionManager:
    """Enhanced WebSocket connection manager with Redis pub/sub and sticky sessions"""
    
    def __init__(self, redis_url: str, instance_id: str):
        self.redis_url = redis_url
        self.instance_id = instance_id
        self.connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self.connection_metadata: Dict[str, Dict] = {}
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        
        # Configuration
        self.max_connections = int(os.getenv('WEBSOCKET_MAX_CONNECTIONS', 1000))
        self.heartbeat_interval = int(os.getenv('WEBSOCKET_HEARTBEAT_INTERVAL', 30))
        self.message_timeout = int(os.getenv('WEBSOCKET_MESSAGE_TIMEOUT', 30))
        self.max_message_size = int(os.getenv('WEBSOCKET_MAX_MESSAGE_SIZE', 65536))
        
        logger.info("WebSocket manager initialized", 
                   instance_id=instance_id,
                   max_connections=self.max_connections)

    async def initialize(self):
        """Initialize Redis connection and pub/sub"""
        try:
            self.redis = aioredis.from_url(self.redis_url)
            await self.redis.ping()
            
            # Set up pub/sub for cross-instance communication
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(f"nexus:websocket:broadcast")
            await self.pubsub.subscribe(f"nexus:websocket:user:*")
            
            # Start pub/sub listener
            asyncio.create_task(self._pubsub_listener())
            
            # Register this instance
            await self.redis.setex(
                f"nexus:websocket:instances:{self.instance_id}",
                60,
                json.dumps({
                    "instance_id": self.instance_id,
                    "started_at": datetime.utcnow().isoformat(),
                    "max_connections": self.max_connections
                })
            )
            
            logger.info("Redis connection initialized", instance_id=self.instance_id)
            
        except Exception as e:
            logger.error("Failed to initialize Redis", error=str(e))
            raise

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str, 
                     auth_token: str) -> bool:
        """Accept WebSocket connection with authentication and session management"""
        try:
            # Check connection limits
            if len(self.connections) >= self.max_connections:
                await websocket.close(code=1013, reason="Connection limit exceeded")
                logger.warning("Connection limit exceeded", 
                             current=len(self.connections),
                             max_connections=self.max_connections)
                return False
            
            # Verify JWT token
            try:
                payload = jwt.decode(
                    auth_token, 
                    os.getenv('NEXUS_JWT_SECRET'), 
                    algorithms=['HS256']
                )
                if payload.get('user_id') != user_id:
                    await websocket.close(code=1008, reason="Invalid token")
                    return False
            except jwt.JWTError:
                await websocket.close(code=1008, reason="Invalid token")
                return False
            
            # Accept connection
            await websocket.accept()
            
            # Store connection
            self.connections[connection_id] = websocket
            
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Store metadata
            self.connection_metadata[connection_id] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "messages_sent": 0,
                "messages_received": 0,
                "instance_id": self.instance_id
            }
            
            # Register connection in Redis for cross-instance awareness
            await self.redis.setex(
                f"nexus:websocket:connections:{connection_id}",
                3600,  # 1 hour TTL
                json.dumps({
                    "user_id": user_id,
                    "instance_id": self.instance_id,
                    "connected_at": datetime.utcnow().isoformat()
                })
            )
            
            # Start heartbeat
            self.heartbeat_tasks[connection_id] = asyncio.create_task(
                self._heartbeat_loop(connection_id)
            )
            
            # Update metrics
            websocket_connections.inc()
            
            # Send welcome message
            await self._send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "instance_id": self.instance_id,
                "features": {
                    "heartbeat_interval": self.heartbeat_interval,
                    "max_message_size": self.max_message_size,
                    "compression": True
                }
            })
            
            logger.info("WebSocket connection established", 
                       connection_id=connection_id,
                       user_id=user_id,
                       total_connections=len(self.connections))
            
            return True
            
        except Exception as e:
            logger.error("Failed to establish WebSocket connection", 
                        connection_id=connection_id,
                        error=str(e))
            return False

    async def disconnect(self, connection_id: str):
        """Disconnect WebSocket and cleanup resources"""
        try:
            if connection_id not in self.connections:
                return
            
            metadata = self.connection_metadata.get(connection_id, {})
            user_id = metadata.get("user_id")
            connected_at = metadata.get("connected_at")
            
            # Calculate connection duration
            if connected_at:
                duration = (datetime.utcnow() - connected_at).total_seconds()
                websocket_connection_duration.observe(duration)
            
            # Remove from local storage
            del self.connections[connection_id]
            
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]
            
            # Cancel heartbeat task
            if connection_id in self.heartbeat_tasks:
                self.heartbeat_tasks[connection_id].cancel()
                del self.heartbeat_tasks[connection_id]
            
            # Remove from Redis
            await self.redis.delete(f"nexus:websocket:connections:{connection_id}")
            
            # Update metrics
            websocket_connections.dec()
            
            logger.info("WebSocket connection disconnected", 
                       connection_id=connection_id,
                       user_id=user_id,
                       remaining_connections=len(self.connections))
                       
        except Exception as e:
            logger.error("Error during disconnect", 
                        connection_id=connection_id,
                        error=str(e))

    async def _send_to_connection(self, connection_id: str, message: Dict) -> bool:
        """Send message to specific connection"""
        if connection_id not in self.connections:
            return False
        
        try:
            websocket = self.connections[connection_id]
            
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()
            
            await websocket.send_json(message)
            
            # Update metadata
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]["messages_sent"] += 1
                self.connection_metadata[connection_id]["last_activity"] = datetime.utcnow()
            
            websocket_messages_sent.inc()
            return True
            
        except Exception as e:
            logger.error("Failed to send message", 
                        connection_id=connection_id,
                        error=str(e))
            # Remove failed connection
            await self.disconnect(connection_id)
            return False

    async def send_to_user(self, user_id: str, message: Dict):
        """Send message to all connections for a specific user"""
        if user_id in self.user_connections:
            tasks = []
            for connection_id in list(self.user_connections[user_id]):
                tasks.append(self._send_to_connection(connection_id, message))
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Also send via Redis pub/sub for other instances
        await self.redis.publish(
            f"nexus:websocket:user:{user_id}",
            json.dumps(message)
        )

    async def broadcast(self, message: Dict):
        """Broadcast message to all connections"""
        # Send to local connections
        tasks = []
        for connection_id in list(self.connections.keys()):
            tasks.append(self._send_to_connection(connection_id, message))
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Send via Redis pub/sub for other instances
        await self.redis.publish(
            "nexus:websocket:broadcast",
            json.dumps(message)
        )

    async def _heartbeat_loop(self, connection_id: str):
        """Send periodic heartbeat messages"""
        try:
            while connection_id in self.connections:
                await asyncio.sleep(self.heartbeat_interval)
                
                if connection_id in self.connections:
                    success = await self._send_to_connection(connection_id, {
                        "type": "heartbeat",
                        "instance_id": self.instance_id
                    })
                    
                    if not success:
                        break
                        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Heartbeat error", 
                        connection_id=connection_id,
                        error=str(e))

    async def _pubsub_listener(self):
        """Listen for Redis pub/sub messages"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        channel = message["channel"].decode()
                        
                        if channel == "nexus:websocket:broadcast":
                            # Broadcast to local connections
                            tasks = []
                            for connection_id in list(self.connections.keys()):
                                tasks.append(self._send_to_connection(connection_id, data))
                            await asyncio.gather(*tasks, return_exceptions=True)
                            
                        elif channel.startswith("nexus:websocket:user:"):
                            user_id = channel.split(":")[-1]
                            # Send to local connections for this user
                            if user_id in self.user_connections:
                                tasks = []
                                for connection_id in list(self.user_connections[user_id]):
                                    tasks.append(self._send_to_connection(connection_id, data))
                                await asyncio.gather(*tasks, return_exceptions=True)
                                
                    except Exception as e:
                        logger.error("Error processing pub/sub message", error=str(e))
                        
        except Exception as e:
            logger.error("Pub/sub listener error", error=str(e))

    async def handle_message(self, connection_id: str, message: Dict):
        """Handle incoming WebSocket message"""
        start_time = time.time()
        
        try:
            # Update activity
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]["messages_received"] += 1
                self.connection_metadata[connection_id]["last_activity"] = datetime.utcnow()
            
            websocket_messages_received.inc()
            
            message_type = message.get("type")
            logger.debug("Processing WebSocket message", 
                        connection_id=connection_id,
                        message_type=message_type)
            
            if message_type == "ping":
                await self._send_to_connection(connection_id, {
                    "type": "pong",
                    "original_timestamp": message.get("timestamp")
                })
                
            elif message_type == "chat_message":
                # Echo chat message (in production, this would route to AI service)
                response = {
                    "type": "chat_response",
                    "message": f"Echo: {message.get('content', '')}",
                    "connection_id": connection_id
                }
                await self._send_to_connection(connection_id, response)
                
            elif message_type == "broadcast_request":
                # Handle broadcast requests (admin only)
                user_id = self.connection_metadata.get(connection_id, {}).get("user_id")
                if user_id:  # Add proper admin check in production
                    await self.broadcast({
                        "type": "system_broadcast",
                        "message": message.get("content", ""),
                        "from_user": user_id
                    })
                    
            else:
                logger.warning("Unknown message type", 
                              connection_id=connection_id,
                              message_type=message_type)
                
        except Exception as e:
            logger.error("Error handling message", 
                        connection_id=connection_id,
                        error=str(e))
        finally:
            processing_time = time.time() - start_time
            websocket_message_processing_time.observe(processing_time)

    def get_stats(self) -> Dict:
        """Get connection statistics"""
        total_messages_sent = sum(
            meta.get("messages_sent", 0) 
            for meta in self.connection_metadata.values()
        )
        total_messages_received = sum(
            meta.get("messages_received", 0) 
            for meta in self.connection_metadata.values()
        )
        
        return {
            "instance_id": self.instance_id,
            "active_connections": len(self.connections),
            "unique_users": len(self.user_connections),
            "total_messages_sent": total_messages_sent,
            "total_messages_received": total_messages_received,
            "max_connections": self.max_connections,
            "heartbeat_interval": self.heartbeat_interval
        }

# Global connection manager
manager: Optional[WebSocketConnectionManager] = None

# FastAPI app
app = FastAPI(title="Nexus WebSocket Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize WebSocket service"""
    global manager
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    instance_id = os.getenv("NEXUS_INSTANCE_ID", f"websocket-{uuid.uuid4().hex[:8]}")
    
    manager = WebSocketConnectionManager(redis_url, instance_id)
    await manager.initialize()
    
    # Start metrics server
    metrics_port = int(os.getenv("METRICS_PORT", 9091))
    start_http_server(metrics_port)
    
    logger.info("Nexus WebSocket service started", 
               instance_id=instance_id,
               metrics_port=metrics_port)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global manager
    
    if manager:
        # Disconnect all connections gracefully
        disconnect_tasks = []
        for connection_id in list(manager.connections.keys()):
            disconnect_tasks.append(manager.disconnect(connection_id))
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        # Close Redis connection
        if manager.redis:
            await manager.redis.close()
    
    logger.info("Nexus WebSocket service shutdown complete")

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(...),
    client_id: Optional[str] = Query(None)
):
    """WebSocket endpoint with authentication and session management"""
    connection_id = client_id or f"{user_id}-{uuid.uuid4().hex[:8]}"
    
    if not manager:
        await websocket.close(code=1011, reason="Service not initialized")
        return
    
    # Establish connection
    connected = await manager.connect(websocket, connection_id, user_id, token)
    if not connected:
        return
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Validate message size
            message_size = len(json.dumps(data))
            if message_size > manager.max_message_size:
                await manager._send_to_connection(connection_id, {
                    "type": "error",
                    "message": "Message too large",
                    "max_size": manager.max_message_size
                })
                continue
            
            # Handle message
            await manager.handle_message(connection_id, data)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WebSocket error", 
                    connection_id=connection_id,
                    error=str(e))
    finally:
        await manager.disconnect(connection_id)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not manager:
        return {"status": "unhealthy", "error": "Manager not initialized"}
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "stats": manager.get_stats()
    }

@app.get("/stats")
async def get_stats():
    """Get WebSocket statistics"""
    if not manager:
        return {"error": "Manager not initialized"}
    
    return manager.get_stats()

# Graceful shutdown handler
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal", signal=signum)
    asyncio.create_task(shutdown_event())
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    import os
    
    port = int(os.getenv("WEBSOCKET_PORT", 8080))
    host = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
    
    uvicorn.run(
        "nexus_websocket_service:app",
        host=host,
        port=port,
        log_config=None,  # Use structlog
        access_log=False
    )