"""
WebSocket Handlers for Real-Time Sales Assistant Features
========================================================

Comprehensive WebSocket handling for:
- Real-time chat interface
- Live document processing updates
- Quote generation progress
- System notifications
- User presence tracking
- Collaborative features
- AI agent communication
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Import DataFlow models
from dataflow_models import db, User, ActivityLog, Document, Quote

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """WebSocket message types"""
    # Connection management
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    
    # Chat messages
    CHAT_MESSAGE = "chat_message"
    CHAT_RESPONSE = "chat_response"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    
    # System notifications
    NOTIFICATION = "notification"
    ALERT = "alert"
    STATUS_UPDATE = "status_update"
    
    # Document processing
    DOCUMENT_UPLOAD_START = "document_upload_start"
    DOCUMENT_UPLOAD_PROGRESS = "document_upload_progress"
    DOCUMENT_UPLOAD_COMPLETE = "document_upload_complete"
    DOCUMENT_PROCESSING_START = "document_processing_start"
    DOCUMENT_PROCESSING_PROGRESS = "document_processing_progress"
    DOCUMENT_PROCESSING_COMPLETE = "document_processing_complete"
    DOCUMENT_ERROR = "document_error"
    
    # Quote generation
    QUOTE_GENERATION_START = "quote_generation_start"
    QUOTE_GENERATION_PROGRESS = "quote_generation_progress"
    QUOTE_GENERATION_COMPLETE = "quote_generation_complete"
    QUOTE_UPDATE = "quote_update"
    
    # Collaboration
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"
    USER_ACTIVITY = "user_activity"
    PRESENCE_UPDATE = "presence_update"
    
    # AI Agent integration
    AI_THINKING = "ai_thinking"
    AI_RESPONSE = "ai_response"
    AI_ERROR = "ai_error"
    AI_TOOL_CALL = "ai_tool_call"
    AI_TOOL_RESULT = "ai_tool_result"

@dataclass
class WebSocketMessage:
    """Structured WebSocket message"""
    type: MessageType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[str] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())

@dataclass
class UserConnection:
    """Represents a user's WebSocket connection"""
    websocket: WebSocket
    user_id: int
    connection_id: str
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    subscriptions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

class WebSocketManager:
    """Enhanced WebSocket connection manager with advanced features"""
    
    def __init__(self):
        # Connection management
        self.connections: Dict[str, UserConnection] = {}
        self.user_connections: Dict[int, List[str]] = {}
        self.room_connections: Dict[str, Set[str]] = {}
        
        # Message queues for offline users
        self.message_queues: Dict[int, List[WebSocketMessage]] = {}
        
        # Typing indicators
        self.typing_users: Dict[str, Set[int]] = {}  # room_id -> set of user_ids
        
        # Presence tracking
        self.user_presence: Dict[int, str] = {}  # user_id -> status (online, away, busy)
        
        # Background tasks
        self._cleanup_task = None
        self._heartbeat_task = None
    
    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        self._cleanup_task = asyncio.create_task(self._cleanup_stale_connections())
        self._heartbeat_task = asyncio.create_task(self._send_heartbeats())
    
    async def stop_background_tasks(self):
        """Stop background maintenance tasks"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: int, metadata: Dict[str, Any] = None):
        """Connect a new WebSocket client"""
        await websocket.accept()
        
        connection = UserConnection(
            websocket=websocket,
            user_id=user_id,
            connection_id=connection_id,
            metadata=metadata or {}
        )
        
        # Store connection
        self.connections[connection_id] = connection
        
        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        
        # Update presence
        self.user_presence[user_id] = "online"
        
        # Send queued messages
        if user_id in self.message_queues:
            for message in self.message_queues[user_id]:
                await self.send_to_connection(message, connection_id)
            del self.message_queues[user_id]
        
        # Notify other users
        await self.broadcast_to_room("general", WebSocketMessage(
            type=MessageType.USER_JOIN,
            data={"user_id": user_id, "connection_id": connection_id},
            user_id=user_id
        ))
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
    
    async def disconnect(self, connection_id: str, code: int = 1000, reason: str = "Normal closure"):
        """Disconnect a WebSocket client"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        user_id = connection.user_id
        
        # Remove from connections
        del self.connections[connection_id]
        
        # Update user connections
        if user_id in self.user_connections:
            self.user_connections[user_id] = [
                conn for conn in self.user_connections[user_id] 
                if conn != connection_id
            ]
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
                # Update presence if no more connections
                self.user_presence[user_id] = "offline"
        
        # Remove from rooms
        for room_id, connections in self.room_connections.items():
            connections.discard(connection_id)
        
        # Stop typing indicators
        for room_id, typing_users in self.typing_users.items():
            typing_users.discard(user_id)
        
        # Notify other users
        await self.broadcast_to_room("general", WebSocketMessage(
            type=MessageType.USER_LEAVE,
            data={"user_id": user_id, "connection_id": connection_id},
            user_id=user_id
        ))
        
        logger.info(f"WebSocket disconnected: {connection_id} (code: {code}, reason: {reason})")
    
    async def send_to_connection(self, message: WebSocketMessage, connection_id: str) -> bool:
        """Send message to a specific connection"""
        if connection_id not in self.connections:
            return False
        
        try:
            connection = self.connections[connection_id]
            await connection.websocket.send_text(message.to_json())
            connection.last_activity = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.disconnect(connection_id, code=1011, reason="Send error")
            return False
    
    async def send_to_user(self, message: WebSocketMessage, user_id: int) -> int:
        """Send message to all connections for a user"""
        sent_count = 0
        
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if await self.send_to_connection(message, connection_id):
                    sent_count += 1
        else:
            # Queue message for offline user
            if user_id not in self.message_queues:
                self.message_queues[user_id] = []
            self.message_queues[user_id].append(message)
            
            # Limit queue size
            if len(self.message_queues[user_id]) > 100:
                self.message_queues[user_id] = self.message_queues[user_id][-100:]
        
        return sent_count
    
    async def broadcast_to_room(self, room_id: str, message: WebSocketMessage, exclude_user: int = None) -> int:
        """Broadcast message to all users in a room"""
        sent_count = 0
        
        if room_id in self.room_connections:
            for connection_id in self.room_connections[room_id].copy():
                connection = self.connections.get(connection_id)
                if connection and (exclude_user is None or connection.user_id != exclude_user):
                    if await self.send_to_connection(message, connection_id):
                        sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(self, message: WebSocketMessage, exclude_user: int = None) -> int:
        """Broadcast message to all connected users"""
        sent_count = 0
        
        for connection_id, connection in self.connections.items():
            if exclude_user is None or connection.user_id != exclude_user:
                if await self.send_to_connection(message, connection_id):
                    sent_count += 1
        
        return sent_count
    
    def join_room(self, connection_id: str, room_id: str):
        """Add connection to a room"""
        if connection_id in self.connections:
            if room_id not in self.room_connections:
                self.room_connections[room_id] = set()
            self.room_connections[room_id].add(connection_id)
            self.connections[connection_id].subscriptions.add(room_id)
    
    def leave_room(self, connection_id: str, room_id: str):
        """Remove connection from a room"""
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(connection_id)
        if connection_id in self.connections:
            self.connections[connection_id].subscriptions.discard(room_id)
    
    async def set_typing_status(self, user_id: int, room_id: str, is_typing: bool):
        """Update user typing status"""
        if room_id not in self.typing_users:
            self.typing_users[room_id] = set()
        
        if is_typing:
            self.typing_users[room_id].add(user_id)
        else:
            self.typing_users[room_id].discard(user_id)
        
        # Broadcast typing status
        message = WebSocketMessage(
            type=MessageType.TYPING_START if is_typing else MessageType.TYPING_STOP,
            data={"user_id": user_id, "room_id": room_id},
            user_id=user_id
        )
        await self.broadcast_to_room(room_id, message, exclude_user=user_id)
    
    async def update_presence(self, user_id: int, status: str):
        """Update user presence status"""
        self.user_presence[user_id] = status
        
        message = WebSocketMessage(
            type=MessageType.PRESENCE_UPDATE,
            data={"user_id": user_id, "status": status},
            user_id=user_id
        )
        await self.broadcast_to_all(message, exclude_user=user_id)
    
    def get_room_users(self, room_id: str) -> List[int]:
        """Get list of users in a room"""
        users = set()
        if room_id in self.room_connections:
            for connection_id in self.room_connections[room_id]:
                if connection_id in self.connections:
                    users.add(self.connections[connection_id].user_id)
        return list(users)
    
    def get_online_users(self) -> List[int]:
        """Get list of all online users"""
        return [user_id for user_id, status in self.user_presence.items() if status == "online"]
    
    async def _cleanup_stale_connections(self):
        """Background task to cleanup stale connections"""
        while True:
            try:
                now = datetime.now()
                stale_connections = []
                
                for connection_id, connection in self.connections.items():
                    # Check if connection is stale (no activity for 5 minutes)
                    if (now - connection.last_activity).total_seconds() > 300:
                        stale_connections.append(connection_id)
                
                # Disconnect stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id, code=1000, reason="Stale connection")
                
                # Clean up empty message queues
                empty_queues = [
                    user_id for user_id, queue in self.message_queues.items() 
                    if not queue
                ]
                for user_id in empty_queues:
                    del self.message_queues[user_id]
                
                await asyncio.sleep(60)  # Run every minute
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)
    
    async def _send_heartbeats(self):
        """Background task to send heartbeats"""
        while True:
            try:
                heartbeat = WebSocketMessage(type=MessageType.HEARTBEAT)
                await self.broadcast_to_all(heartbeat)
                await asyncio.sleep(30)  # Send every 30 seconds
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}")
                await asyncio.sleep(30)

class WebSocketHandlers:
    """WebSocket message handlers for different features"""
    
    def __init__(self, manager: WebSocketManager):
        self.manager = manager
        self.runtime = LocalRuntime()
    
    async def handle_message(self, message: Dict[str, Any], connection_id: str):
        """Route incoming messages to appropriate handlers"""
        try:
            message_type = MessageType(message.get("type"))
            data = message.get("data", {})
            user_id = message.get("user_id")
            
            # Update connection activity
            if connection_id in self.manager.connections:
                self.manager.connections[connection_id].last_activity = datetime.now()
            
            # Route to handler
            handler_map = {
                MessageType.CHAT_MESSAGE: self.handle_chat_message,
                MessageType.TYPING_START: self.handle_typing_start,
                MessageType.TYPING_STOP: self.handle_typing_stop,
                MessageType.DOCUMENT_UPLOAD_START: self.handle_document_upload_start,
                MessageType.QUOTE_GENERATION_START: self.handle_quote_generation_start,
                MessageType.AI_TOOL_CALL: self.handle_ai_tool_call,
                MessageType.PRESENCE_UPDATE: self.handle_presence_update,
                MessageType.HEARTBEAT: self.handle_heartbeat,
            }
            
            handler = handler_map.get(message_type)
            if handler:
                await handler(data, connection_id, user_id)
            else:
                logger.warning(f"No handler for message type: {message_type}")
        
        except ValueError:
            logger.error(f"Invalid message type: {message.get('type')}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(connection_id, f"Message handling error: {str(e)}")
    
    async def handle_chat_message(self, data: Dict[str, Any], connection_id: str, user_id: int):
        """Handle chat messages with AI integration"""
        message_text = data.get("message", "")
        room_id = data.get("room_id", "general")
        
        # Store message in database
        await self.store_chat_message(user_id, room_id, message_text)
        
        # Broadcast message to room
        response = WebSocketMessage(
            type=MessageType.CHAT_RESPONSE,
            data={
                "message": message_text,
                "user_id": user_id,
                "room_id": room_id,
                "timestamp": datetime.now().isoformat()
            },
            user_id=user_id
        )
        await self.manager.broadcast_to_room(room_id, response)
        
        # Check if AI should respond
        if self.should_ai_respond(message_text):
            await self.generate_ai_response(message_text, room_id, user_id)
    
    async def handle_typing_start(self, data: Dict[str, Any], connection_id: str, user_id: int):
        """Handle typing start indicator"""
        room_id = data.get("room_id", "general")
        await self.manager.set_typing_status(user_id, room_id, True)
    
    async def handle_typing_stop(self, data: Dict[str, Any], connection_id: str, user_id: int):
        """Handle typing stop indicator"""
        room_id = data.get("room_id", "general")
        await self.manager.set_typing_status(user_id, room_id, False)
    
    async def handle_document_upload_start(self, data: Dict[str, Any], connection_id: str, user_id: int):
        """Handle document upload start notification"""
        file_name = data.get("file_name", "")
        file_size = data.get("file_size", 0)
        
        # Notify user about upload start
        response = WebSocketMessage(
            type=MessageType.DOCUMENT_UPLOAD_START,
            data={
                "file_name": file_name,
                "file_size": file_size,
                "status": "starting",
                "progress": 0
            },
            user_id=user_id
        )
        await self.manager.send_to_user(response, user_id)
    
    async def handle_quote_generation_start(self, data: Dict[str, Any], connection_id: str, user_id: int):
        """Handle quote generation request"""
        customer_id = data.get("customer_id")
        requirements = data.get("requirements", "")
        
        # Start quote generation workflow
        await self.start_quote_generation(customer_id, requirements, user_id)
    
    async def handle_ai_tool_call(self, data: Dict[str, Any], connection_id: str, user_id: int):
        """Handle AI tool execution request"""
        tool_name = data.get("tool_name", "")
        tool_args = data.get("args", {})
        
        # Execute tool and return result
        await self.execute_ai_tool(tool_name, tool_args, user_id)
    
    async def handle_presence_update(self, data: Dict[str, Any], connection_id: str, user_id: int):
        """Handle user presence update"""
        status = data.get("status", "online")
        await self.manager.update_presence(user_id, status)
    
    async def handle_heartbeat(self, data: Dict[str, Any], connection_id: str, user_id: int):
        """Handle heartbeat response"""
        # Just update last activity (already done in handle_message)
        pass
    
    async def store_chat_message(self, user_id: int, room_id: str, message: str):
        """Store chat message in database"""
        try:
            workflow = WorkflowBuilder()
            
            workflow.add_node("AsyncSQLExecuteNode", "store_message", {
                "query": """
                    INSERT INTO chat_messages (user_id, room_id, message, created_at)
                    VALUES (%(user_id)s, %(room_id)s, %(message)s, NOW())
                """,
                "parameters": {
                    "user_id": user_id,
                    "room_id": room_id,
                    "message": message
                },
                "connection_pool": db.connection_pool
            })
            
            await self.runtime.execute_async(workflow.build())
        
        except Exception as e:
            logger.error(f"Error storing chat message: {e}")
    
    def should_ai_respond(self, message: str) -> bool:
        """Determine if AI should respond to a message"""
        ai_triggers = ["@ai", "@assistant", "help", "quote", "price", "product"]
        return any(trigger in message.lower() for trigger in ai_triggers)
    
    async def generate_ai_response(self, message: str, room_id: str, user_id: int):
        """Generate AI response to user message"""
        try:
            # Show AI thinking indicator
            thinking_msg = WebSocketMessage(
                type=MessageType.AI_THINKING,
                data={"room_id": room_id},
                user_id=None  # System message
            )
            await self.manager.broadcast_to_room(room_id, thinking_msg)
            
            # Simulate AI processing (replace with actual AI integration)
            await asyncio.sleep(2)
            
            # Generate response based on message content
            if "quote" in message.lower():
                ai_response = "I can help you generate a quote. Please provide the customer information and product requirements."
            elif "product" in message.lower():
                ai_response = "I can search our product catalog. What specific products are you looking for?"
            elif "price" in message.lower():
                ai_response = "I can help with pricing information. Which products would you like pricing for?"
            else:
                ai_response = f"I understand you said: '{message}'. How can I assist you with your sales tasks?"
            
            # Send AI response
            response = WebSocketMessage(
                type=MessageType.AI_RESPONSE,
                data={
                    "message": ai_response,
                    "room_id": room_id,
                    "in_response_to": message
                },
                user_id=None  # System message
            )
            await self.manager.broadcast_to_room(room_id, response)
        
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            await self.send_error_to_room(room_id, "AI response generation failed")
    
    async def start_quote_generation(self, customer_id: int, requirements: str, user_id: int):
        """Start asynchronous quote generation process"""
        try:
            # Notify start
            start_msg = WebSocketMessage(
                type=MessageType.QUOTE_GENERATION_START,
                data={
                    "customer_id": customer_id,
                    "status": "starting"
                },
                user_id=user_id
            )
            await self.manager.send_to_user(start_msg, user_id)
            
            # Start background quote generation
            asyncio.create_task(self._generate_quote_async(customer_id, requirements, user_id))
        
        except Exception as e:
            logger.error(f"Error starting quote generation: {e}")
            await self.send_error_to_user(user_id, "Quote generation failed to start")
    
    async def _generate_quote_async(self, customer_id: int, requirements: str, user_id: int):
        """Background quote generation process"""
        try:
            # Progress updates
            progress_steps = [
                ("Analyzing requirements", 20),
                ("Searching products", 40),
                ("Calculating pricing", 60),
                ("Generating quote", 80),
                ("Finalizing", 100)
            ]
            
            for step, progress in progress_steps:
                progress_msg = WebSocketMessage(
                    type=MessageType.QUOTE_GENERATION_PROGRESS,
                    data={
                        "step": step,
                        "progress": progress,
                        "customer_id": customer_id
                    },
                    user_id=user_id
                )
                await self.manager.send_to_user(progress_msg, user_id)
                await asyncio.sleep(1)  # Simulate processing time
            
            # Complete quote generation
            complete_msg = WebSocketMessage(
                type=MessageType.QUOTE_GENERATION_COMPLETE,
                data={
                    "quote_id": "Q2024001",  # Mock quote ID
                    "customer_id": customer_id,
                    "total_amount": 25000.00,
                    "status": "completed"
                },
                user_id=user_id
            )
            await self.manager.send_to_user(complete_msg, user_id)
        
        except Exception as e:
            logger.error(f"Error in async quote generation: {e}")
            await self.send_error_to_user(user_id, "Quote generation failed")
    
    async def execute_ai_tool(self, tool_name: str, tool_args: Dict[str, Any], user_id: int):
        """Execute AI tool and return result"""
        try:
            # Show tool execution start
            start_msg = WebSocketMessage(
                type=MessageType.AI_TOOL_CALL,
                data={
                    "tool_name": tool_name,
                    "status": "executing"
                },
                user_id=user_id
            )
            await self.manager.send_to_user(start_msg, user_id)
            
            # Mock tool execution (replace with actual tool integration)
            await asyncio.sleep(1)
            
            # Mock result
            result = {
                "tool_name": tool_name,
                "status": "completed",
                "result": f"Tool '{tool_name}' executed successfully with args: {tool_args}"
            }
            
            # Send result
            result_msg = WebSocketMessage(
                type=MessageType.AI_TOOL_RESULT,
                data=result,
                user_id=user_id
            )
            await self.manager.send_to_user(result_msg, user_id)
        
        except Exception as e:
            logger.error(f"Error executing AI tool: {e}")
            await self.send_error_to_user(user_id, f"Tool execution failed: {tool_name}")
    
    async def send_error(self, connection_id: str, error_message: str):
        """Send error message to specific connection"""
        error_msg = WebSocketMessage(
            type=MessageType.ALERT,
            data={
                "level": "error",
                "message": error_message
            }
        )
        await self.manager.send_to_connection(error_msg, connection_id)
    
    async def send_error_to_user(self, user_id: int, error_message: str):
        """Send error message to user"""
        error_msg = WebSocketMessage(
            type=MessageType.ALERT,
            data={
                "level": "error",
                "message": error_message
            }
        )
        await self.manager.send_to_user(error_msg, user_id)
    
    async def send_error_to_room(self, room_id: str, error_message: str):
        """Send error message to room"""
        error_msg = WebSocketMessage(
            type=MessageType.ALERT,
            data={
                "level": "error",
                "message": error_message
            }
        )
        await self.manager.broadcast_to_room(room_id, error_msg)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
websocket_handlers = WebSocketHandlers(websocket_manager)