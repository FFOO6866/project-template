"""
Enhanced WebSocket Handlers for Nexus Platform
==============================================

Optimized WebSocket implementation for real-time features:
- Message compression and optimization
- Connection pooling and load balancing
- Real-time notifications and chat
- Performance monitoring and metrics
- Automatic reconnection handling
"""

import asyncio
import json
import gzip
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from nexus_enhanced_config import enhanced_config

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """WebSocket message types"""
    WELCOME = "welcome"
    HEARTBEAT = "heartbeat"
    PONG = "pong"
    CHAT_MESSAGE = "chat_message"
    CHAT_RESPONSE = "chat_response"
    NOTIFICATION = "notification"
    QUOTE_REQUEST = "quote_request"
    QUOTE_PROCESSING = "quote_processing"
    QUOTE_READY = "quote_ready"
    DOCUMENT_UPLOADED = "document_uploaded"
    USER_STATUS = "user_status"
    ERROR = "error"
    TYPING = "typing"
    FILE_UPLOAD_PROGRESS = "file_upload_progress"

@dataclass
class WebSocketMessage:
    """Structured WebSocket message"""
    type: MessageType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    user_id: Optional[int] = None
    connection_id: Optional[str] = None
    priority: int = 5  # 1 = highest, 10 = lowest
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "connection_id": self.connection_id,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSocketMessage':
        """Create from dictionary"""
        return cls(
            type=MessageType(data["type"]),
            data=data.get("data", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            user_id=data.get("user_id"),
            connection_id=data.get("connection_id"),
            priority=data.get("priority", 5)
        )

@dataclass
class ConnectionInfo:
    """WebSocket connection information"""
    connection_id: str
    user_id: int
    websocket: WebSocket
    connected_at: datetime
    last_activity: datetime
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    compression_enabled: bool = False
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def get_connection_duration(self) -> timedelta:
        """Get connection duration"""
        return datetime.now() - self.connected_at
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        duration = self.get_connection_duration()
        return {
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "connected_at": self.connected_at.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "last_activity": self.last_activity.isoformat(),
            "compression_enabled": self.compression_enabled
        }

class MessageQueue:
    """Priority-based message queue for WebSocket connections"""
    
    def __init__(self, max_size: int = None):
        self.max_size = max_size or enhanced_config.enhanced_websocket.message_queue_size
        self.queue: List[WebSocketMessage] = []
        self._lock = asyncio.Lock()
    
    async def put(self, message: WebSocketMessage) -> bool:
        """Add message to queue with priority sorting"""
        async with self._lock:
            if len(self.queue) >= self.max_size:
                # Remove lowest priority message if queue is full
                self.queue.sort(key=lambda m: m.priority, reverse=True)
                if message.priority < self.queue[-1].priority:
                    self.queue.pop()
                else:
                    return False  # Message dropped
            
            self.queue.append(message)
            self.queue.sort(key=lambda m: m.priority)
            return True
    
    async def get(self) -> Optional[WebSocketMessage]:
        """Get highest priority message from queue"""
        async with self._lock:
            if self.queue:
                return self.queue.pop(0)
            return None
    
    async def size(self) -> int:
        """Get queue size"""
        async with self._lock:
            return len(self.queue)
    
    async def clear(self):
        """Clear all messages from queue"""
        async with self._lock:
            self.queue.clear()

class EnhancedWebSocketManager:
    """Enhanced WebSocket manager with advanced features"""
    
    def __init__(self):
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[int, List[str]] = {}
        self.message_queues: Dict[str, MessageQueue] = {}
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.broadcast_handlers: List[Callable] = []
        
        # Configuration
        self.max_connections = enhanced_config.enhanced_websocket.max_connections
        self.heartbeat_interval = enhanced_config.enhanced_websocket.heartbeat_interval
        self.compression_threshold = enhanced_config.enhanced_websocket.compression_threshold
        self.max_message_size = enhanced_config.enhanced_websocket.max_message_size
        
        # Statistics
        self.total_connections = 0
        self.total_messages_sent = 0
        self.total_messages_received = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # Setup default message handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default message handlers"""
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        self.register_handler(MessageType.CHAT_MESSAGE, self._handle_chat_message)
        self.register_handler(MessageType.QUOTE_REQUEST, self._handle_quote_request)
        self.register_handler(MessageType.TYPING, self._handle_typing)
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register message handler"""
        self.message_handlers[message_type] = handler
    
    def register_broadcast_handler(self, handler: Callable):
        """Register broadcast handler"""
        self.broadcast_handlers.append(handler)
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: int, 
                     user_agent: str = None, ip_address: str = None) -> bool:
        """Connect WebSocket with enhanced features"""
        try:
            # Check connection limits
            if len(self.connections) >= self.max_connections:
                await websocket.close(code=1013, reason="Connection limit exceeded")
                return False
            
            # Accept connection
            await websocket.accept()
            
            # Create connection info
            connection_info = ConnectionInfo(
                connection_id=connection_id,
                user_id=user_id,
                websocket=websocket,
                connected_at=datetime.now(),
                last_activity=datetime.now(),
                user_agent=user_agent,
                ip_address=ip_address,
                compression_enabled=enhanced_config.enhanced_websocket.enable_compression
            )
            
            # Store connection
            self.connections[connection_id] = connection_info
            
            # Map user to connection
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(connection_id)
            
            # Create message queue
            self.message_queues[connection_id] = MessageQueue()
            
            # Update statistics
            self.total_connections += 1
            
            # Start background tasks if not running
            if self.cleanup_task is None or self.cleanup_task.done():
                self.cleanup_task = asyncio.create_task(self._cleanup_connections())
            
            if self.heartbeat_task is None or self.heartbeat_task.done():
                self.heartbeat_task = asyncio.create_task(self._send_heartbeats())
            
            logger.info(f"WebSocket connected: {connection_id} for user {user_id} (total: {len(self.connections)})")
            
            # Send welcome message
            welcome_message = WebSocketMessage(
                type=MessageType.WELCOME,
                data={
                    "message": "Connected to enhanced sales assistant",
                    "connection_id": connection_id,
                    "features": {
                        "compression": connection_info.compression_enabled,
                        "heartbeat_interval": self.heartbeat_interval,
                        "max_message_size": self.max_message_size,
                        "priority_queuing": True
                    },
                    "server_time": datetime.now().isoformat()
                },
                user_id=user_id,
                connection_id=connection_id,
                priority=1  # High priority for welcome
            )
            
            await self._send_message_to_connection(welcome_message, connection_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket {connection_id}: {e}")
            return False
    
    async def disconnect(self, connection_id: str):
        """Disconnect WebSocket connection"""
        if connection_id not in self.connections:
            return
        
        connection_info = self.connections[connection_id]
        user_id = connection_info.user_id
        
        # Remove from connections
        del self.connections[connection_id]
        
        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id] = [
                conn for conn in self.user_connections[user_id] 
                if conn != connection_id
            ]
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Clear message queue
        if connection_id in self.message_queues:
            await self.message_queues[connection_id].clear()
            del self.message_queues[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id} (total: {len(self.connections)})")
    
    async def send_message(self, message: WebSocketMessage, connection_id: str) -> bool:
        """Send message to specific connection"""
        return await self._send_message_to_connection(message, connection_id)
    
    async def send_to_user(self, message: WebSocketMessage, user_id: int) -> int:
        """Send message to all connections for a user"""
        sent_count = 0
        if user_id in self.user_connections:
            tasks = []
            for connection_id in self.user_connections[user_id]:
                message.connection_id = connection_id
                tasks.append(self._send_message_to_connection(message, connection_id))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            sent_count = sum(1 for result in results if result is True)
        
        return sent_count
    
    async def broadcast(self, message: WebSocketMessage) -> int:
        """Broadcast message to all connections"""
        tasks = []
        for connection_id in self.connections.keys():
            message.connection_id = connection_id
            tasks.append(self._send_message_to_connection(message, connection_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        sent_count = sum(1 for result in results if result is True)
        
        # Notify broadcast handlers
        for handler in self.broadcast_handlers:
            try:
                await handler(message, sent_count)
            except Exception as e:
                logger.error(f"Broadcast handler error: {e}")
        
        return sent_count
    
    async def handle_message(self, raw_message: dict, connection_id: str):
        """Handle incoming message from WebSocket"""
        try:
            # Update connection activity
            if connection_id in self.connections:
                self.connections[connection_id].update_activity()
                self.connections[connection_id].messages_received += 1
                self.total_messages_received += 1
            
            # Parse message
            message = WebSocketMessage.from_dict(raw_message)
            message.connection_id = connection_id
            
            # Check message size
            message_size = len(json.dumps(raw_message).encode())
            if message_size > self.max_message_size:
                error_message = WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": "Message too large", "max_size": self.max_message_size},
                    connection_id=connection_id
                )
                await self._send_message_to_connection(error_message, connection_id)
                return
            
            # Update bytes received
            if connection_id in self.connections:
                self.connections[connection_id].bytes_received += message_size
                self.total_bytes_received += message_size
            
            # Route to handler
            if message.type in self.message_handlers:
                await self.message_handlers[message.type](message, connection_id)
            else:
                logger.warning(f"No handler for message type: {message.type}")
                
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            error_message = WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Message processing failed"},
                connection_id=connection_id
            )
            await self._send_message_to_connection(error_message, connection_id)
    
    async def _send_message_to_connection(self, message: WebSocketMessage, connection_id: str) -> bool:
        """Internal method to send message to connection"""
        if connection_id not in self.connections:
            return False
        
        try:
            connection_info = self.connections[connection_id]
            websocket = connection_info.websocket
            
            # Convert message to dict
            message_dict = message.to_dict()
            message_json = json.dumps(message_dict)
            message_bytes = message_json.encode()
            
            # Compress if enabled and message is large enough
            if (connection_info.compression_enabled and 
                len(message_bytes) > self.compression_threshold):
                
                compressed_bytes = gzip.compress(message_bytes)
                if len(compressed_bytes) < len(message_bytes):
                    # Send compressed message with header
                    await websocket.send_bytes(b'GZIP:' + compressed_bytes)
                else:
                    # Send uncompressed if compression doesn't help
                    await websocket.send_text(message_json)
            else:
                # Send uncompressed
                await websocket.send_text(message_json)
            
            # Update statistics
            connection_info.messages_sent += 1
            connection_info.bytes_sent += len(message_bytes)
            connection_info.update_activity()
            
            self.total_messages_sent += 1
            self.total_bytes_sent += len(message_bytes)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            # Connection is broken, clean it up
            await self.disconnect(connection_id)
            return False
    
    async def _cleanup_connections(self):
        """Background task to clean up stale connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                now = datetime.now()
                stale_connections = []
                
                for connection_id, connection_info in self.connections.items():
                    # Check for stale connections (no activity for 10 minutes)
                    if (now - connection_info.last_activity).total_seconds() > 600:
                        stale_connections.append(connection_id)
                
                # Clean up stale connections
                for connection_id in stale_connections:
                    logger.info(f"Cleaning up stale connection: {connection_id}")
                    await self.disconnect(connection_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection cleanup error: {e}")
    
    async def _send_heartbeats(self):
        """Background task to send heartbeat messages"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                heartbeat_message = WebSocketMessage(
                    type=MessageType.HEARTBEAT,
                    data={"timestamp": datetime.now().isoformat()},
                    priority=10  # Low priority
                )
                
                # Send to all connections
                await self.broadcast(heartbeat_message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
    
    # Default message handlers
    async def _handle_heartbeat(self, message: WebSocketMessage, connection_id: str):
        """Handle heartbeat response"""
        pong_message = WebSocketMessage(
            type=MessageType.PONG,
            data={"timestamp": datetime.now().isoformat()},
            connection_id=connection_id
        )
        await self._send_message_to_connection(pong_message, connection_id)
    
    async def _handle_chat_message(self, message: WebSocketMessage, connection_id: str):
        """Handle chat message"""
        # Echo back with processing
        response_message = WebSocketMessage(
            type=MessageType.CHAT_RESPONSE,
            data={
                "original_message": message.data.get("message", ""),
                "response": f"Received: {message.data.get('message', '')}",
                "processed_at": datetime.now().isoformat(),
                "connection_id": connection_id
            },
            user_id=message.user_id,
            connection_id=connection_id
        )
        await self._send_message_to_connection(response_message, connection_id)
    
    async def _handle_quote_request(self, message: WebSocketMessage, connection_id: str):
        """Handle quote generation request"""
        # Send processing message
        processing_message = WebSocketMessage(
            type=MessageType.QUOTE_PROCESSING,
            data={
                "message": "Processing quote request...",
                "request_id": message.data.get("request_id")
            },
            user_id=message.user_id,
            connection_id=connection_id
        )
        await self._send_message_to_connection(processing_message, connection_id)
        
        # Simulate processing
        await asyncio.sleep(2)
        
        # Send completion message
        completion_message = WebSocketMessage(
            type=MessageType.QUOTE_READY,
            data={
                "message": "Quote generated successfully",
                "quote_id": f"Q{int(time.time())}",
                "request_id": message.data.get("request_id"),
                "processing_time_ms": 2000
            },
            user_id=message.user_id,
            connection_id=connection_id
        )
        await self._send_message_to_connection(completion_message, connection_id)
    
    async def _handle_typing(self, message: WebSocketMessage, connection_id: str):
        """Handle typing indicator"""
        # Broadcast typing status to other users in the same context
        if message.user_id:
            typing_message = WebSocketMessage(
                type=MessageType.TYPING,
                data={
                    "user_id": message.user_id,
                    "typing": message.data.get("typing", False),
                    "context": message.data.get("context", "general")
                }
            )
            
            # Send to all other connections for the same user
            await self.send_to_user(typing_message, message.user_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        now = datetime.now()
        
        # Calculate connection durations
        connection_durations = [
            (now - conn.connected_at).total_seconds() 
            for conn in self.connections.values()
        ]
        avg_duration = sum(connection_durations) / len(connection_durations) if connection_durations else 0
        
        # Calculate message rates
        total_duration_hours = sum(connection_durations) / 3600 if connection_durations else 1
        messages_per_hour = self.total_messages_sent / max(total_duration_hours, 1)
        
        return {
            "active_connections": len(self.connections),
            "unique_users": len(self.user_connections),
            "total_connections": self.total_connections,
            "total_messages_sent": self.total_messages_sent,
            "total_messages_received": self.total_messages_received,
            "total_bytes_sent": self.total_bytes_sent,
            "total_bytes_received": self.total_bytes_received,
            "average_connection_duration_seconds": avg_duration,
            "messages_per_hour": messages_per_hour,
            "compression_enabled": enhanced_config.enhanced_websocket.enable_compression,
            "max_connections": self.max_connections,
            "heartbeat_interval": self.heartbeat_interval,
            "message_queues": len(self.message_queues)
        }
    
    def get_connection_details(self) -> List[Dict[str, Any]]:
        """Get detailed connection information"""
        return [conn.get_stats() for conn in self.connections.values()]

# Global enhanced WebSocket manager instance
enhanced_websocket_manager = EnhancedWebSocketManager()

# Export for use in main application
__all__ = [
    'MessageType',
    'WebSocketMessage', 
    'ConnectionInfo',
    'EnhancedWebSocketManager',
    'enhanced_websocket_manager'
]