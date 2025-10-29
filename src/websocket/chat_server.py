"""
Production WebSocket Chat Server with OpenAI GPT-4 Integration
==============================================================

Real-time AI chat with context awareness for documents, quotations, and products.

Features:
- WebSocket server using websockets library
- OpenAI GPT-4 integration for intelligent responses
- Context-aware responses (current document, quotation, product)
- Connection management and authentication
- Message history tracking
- Session management
- Multi-client support
- Error handling and recovery

Author: Horme POV Production Team
Date: 2025-01-27
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict

import websockets
from websockets.server import WebSocketServerProtocol
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
import asyncpg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Chat message data structure"""
    id: str
    session_id: str
    type: str  # 'user' or 'ai'
    content: str
    timestamp: str
    context: Optional[Dict] = None  # Document, quotation, or product context


@dataclass
class ChatSession:
    """Chat session data structure"""
    session_id: str
    user_id: str
    created_at: str
    last_active: str
    context: Optional[Dict] = None
    messages: List[ChatMessage] = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = []


class WebSocketChatServer:
    """
    Production WebSocket chat server with OpenAI GPT-4 integration.

    Manages multiple client connections, chat sessions, and AI responses.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8001,
        openai_api_key: Optional[str] = None,
        database_url: Optional[str] = None
    ):
        self.host = host
        self.port = port

        # OpenAI client
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not set - AI responses will be limited")
        self.openai_client = AsyncOpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

        # Database connection (optional - for persistent storage)
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.db_engine = None
        if self.database_url:
            # Convert postgresql:// to postgresql+asyncpg://
            if self.database_url.startswith("postgresql://"):
                self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            try:
                self.db_engine = create_async_engine(self.database_url)
                logger.info("Database connection initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")

        # Active connections and sessions
        self.connections: Set[WebSocketServerProtocol] = set()
        self.sessions: Dict[str, ChatSession] = {}
        self.connection_sessions: Dict[WebSocketServerProtocol, str] = {}

        # Database pool for document queries
        self.db_pool = None
        if self.database_url:
            self._init_db_pool()

        logger.info(f"WebSocket chat server initialized: {self.host}:{self.port}")

    def _init_db_pool(self):
        """Initialize asyncpg connection pool for document queries"""
        try:
            # Convert sqlalchemy URL to asyncpg format
            db_url = self.database_url
            if db_url.startswith("postgresql+asyncpg://"):
                db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)

            # Create pool (will be initialized on first use)
            logger.info("Database pool configuration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")

    async def get_db_pool(self) -> asyncpg.Pool:
        """Get or create database pool"""
        if self.db_pool is None:
            try:
                db_url = self.database_url
                if db_url.startswith("postgresql+asyncpg://"):
                    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)

                self.db_pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5)
                logger.info("Database pool created successfully")
            except Exception as e:
                logger.error(f"Failed to create database pool: {e}")
                raise

        return self.db_pool

    async def fetch_document_data(self, document_id: int) -> Optional[Dict]:
        """
        Fetch processed document data from database

        Args:
            document_id: Document ID to fetch

        Returns:
            Dict with document data including extracted requirements, or None if not found
        """
        try:
            pool = await self.get_db_pool()

            async with pool.acquire() as conn:
                doc = await conn.fetchrow("""
                    SELECT
                        id,
                        filename,
                        client_name,
                        project_title,
                        ai_status,
                        ai_extracted_data,
                        extraction_method,
                        extraction_confidence,
                        processing_time_ms,
                        uploaded_at,
                        updated_at
                    FROM documents
                    WHERE id = $1
                """, document_id)

            if not doc:
                logger.warning(f"Document {document_id} not found in database")
                return None

            if doc['ai_status'] != 'completed':
                logger.warning(f"Document {document_id} is not yet processed (status: {doc['ai_status']})")
                return {
                    'id': doc['id'],
                    'filename': doc['filename'],
                    'status': doc['ai_status'],
                    'message': f"Document is {doc['ai_status']}. Please wait for processing to complete."
                }

            # Extract requirements from processed data
            extracted_data = doc['ai_extracted_data']
            if not extracted_data or 'requirements' not in extracted_data:
                logger.warning(f"Document {document_id} has no extracted requirements")
                return {
                    'id': doc['id'],
                    'filename': doc['filename'],
                    'status': 'completed',
                    'error': 'No requirements found in document'
                }

            requirements = extracted_data['requirements']

            return {
                'id': doc['id'],
                'filename': doc['filename'],
                'client_name': doc['client_name'] or requirements.get('customer_name'),
                'project_title': doc['project_title'] or requirements.get('project_name'),
                'status': 'completed',
                'requirements': requirements,
                'metadata': {
                    'extraction_method': doc['extraction_method'],
                    'confidence': float(doc['extraction_confidence']) if doc['extraction_confidence'] else None,
                    'processing_time_ms': doc['processing_time_ms'],
                    'items_count': len(requirements.get('items', []))
                }
            }

        except Exception as e:
            logger.error(f"Error fetching document {document_id}: {e}")
            return None

    async def start(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket chat server on {self.host}:{self.port}")

        async with websockets.serve(
            self.handle_connection,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=20
        ):
            logger.info(f"✅ WebSocket chat server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        connection_id = str(uuid.uuid4())[:8]
        logger.info(f"New connection: {connection_id} from {websocket.remote_address}")

        self.connections.add(websocket)

        try:
            # Send welcome message
            await self.send_message(websocket, {
                "type": "system",
                "content": "Connected to Horme AI Chat Server",
                "timestamp": datetime.utcnow().isoformat()
            })

            # Handle messages
            async for message in websocket:
                await self.handle_message(websocket, message, connection_id)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {connection_id}")
        except Exception as e:
            logger.error(f"Error handling connection {connection_id}: {e}")
        finally:
            self.connections.remove(websocket)
            if websocket in self.connection_sessions:
                session_id = self.connection_sessions[websocket]
                del self.connection_sessions[websocket]
                logger.info(f"Cleaned up session {session_id} for connection {connection_id}")

    async def handle_message(self, websocket: WebSocketServerProtocol, message: str, connection_id: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "chat")

            logger.debug(f"Received message type '{msg_type}' from {connection_id}")

            if msg_type == "auth":
                await self.handle_auth(websocket, data)
            elif msg_type == "chat":
                await self.handle_chat(websocket, data)
            elif msg_type == "context":
                await self.handle_context(websocket, data)
            elif msg_type == "history":
                await self.handle_history(websocket, data)
            elif msg_type == "ping":
                await self.send_message(websocket, {"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                await self.send_error(websocket, f"Unknown message type: {msg_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {connection_id}: {e}")
            await self.send_error(websocket, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            await self.send_error(websocket, f"Server error: {str(e)}")

    async def handle_auth(self, websocket: WebSocketServerProtocol, data: dict):
        """Handle authentication and session creation"""
        user_id = data.get("user_id", "anonymous")
        session_id = data.get("session_id")

        if not session_id:
            session_id = str(uuid.uuid4())

        # Create or retrieve session
        if session_id not in self.sessions:
            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.utcnow().isoformat(),
                last_active=datetime.utcnow().isoformat(),
                context=data.get("context")
            )
            self.sessions[session_id] = session
            logger.info(f"Created new session: {session_id} for user {user_id}")
        else:
            session = self.sessions[session_id]
            session.last_active = datetime.utcnow().isoformat()
            logger.info(f"Restored session: {session_id} for user {user_id}")

        self.connection_sessions[websocket] = session_id

        # Send authentication response
        await self.send_message(websocket, {
            "type": "auth_success",
            "session_id": session_id,
            "user_id": user_id,
            "message_count": len(session.messages),
            "timestamp": datetime.utcnow().isoformat()
        })

        # Send initial AI greeting
        greeting = self.get_context_greeting(session.context)
        await self.send_ai_message(websocket, session_id, greeting)

    async def handle_chat(self, websocket: WebSocketServerProtocol, data: dict):
        """Handle chat message and generate AI response"""
        session_id = self.connection_sessions.get(websocket)
        if not session_id:
            await self.send_error(websocket, "Not authenticated. Please send auth message first.")
            return

        session = self.sessions.get(session_id)
        if not session:
            await self.send_error(websocket, "Session not found")
            return

        content = data.get("content", "").strip()
        if not content:
            await self.send_error(websocket, "Empty message")
            return

        # Create user message
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            type="user",
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            context=session.context
        )
        session.messages.append(user_message)
        session.last_active = datetime.utcnow().isoformat()

        # Echo user message
        await self.send_message(websocket, {
            "type": "message",
            "message": asdict(user_message)
        })

        # Generate AI response
        try:
            # Send typing indicator
            await self.send_message(websocket, {
                "type": "typing",
                "typing": True
            })

            ai_content = await self.generate_ai_response(session, content)

            # Stop typing indicator
            await self.send_message(websocket, {
                "type": "typing",
                "typing": False
            })

            # Send AI response
            await self.send_ai_message(websocket, session_id, ai_content, session.context)

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            await self.send_error(websocket, "Failed to generate AI response")

    async def handle_context(self, websocket: WebSocketServerProtocol, data: dict):
        """Handle context update (document, quotation, product)"""
        session_id = self.connection_sessions.get(websocket)
        if not session_id:
            await self.send_error(websocket, "Not authenticated")
            return

        session = self.sessions.get(session_id)
        if not session:
            await self.send_error(websocket, "Session not found")
            return

        # Get context from request
        context = data.get("context")

        # If context is a document, fetch its data from database
        if context and context.get("type") == "document":
            document_id = context.get("document_id")
            if document_id:
                try:
                    logger.info(f"Fetching document data for document_id: {document_id}")
                    doc_data = await self.fetch_document_data(document_id)

                    if doc_data:
                        # Enrich context with document data
                        context["document_data"] = doc_data
                        logger.info(f"Document data loaded: {doc_data.get('filename')} - {doc_data.get('status')}")
                    else:
                        logger.warning(f"Could not fetch data for document_id: {document_id}")
                except Exception as e:
                    logger.error(f"Error fetching document data: {e}")

        # Update session context
        session.context = context
        session.last_active = datetime.utcnow().isoformat()

        logger.info(f"Updated context for session {session_id}: {session.context.get('type', 'unknown') if session.context else 'none'}")

        # Send context update confirmation
        await self.send_message(websocket, {
            "type": "context_updated",
            "context": session.context,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Send contextual AI message
        context_message = self.get_context_update_message(session.context)
        await self.send_ai_message(websocket, session_id, context_message, session.context)

    async def handle_history(self, websocket: WebSocketServerProtocol, data: dict):
        """Handle message history request"""
        session_id = self.connection_sessions.get(websocket)
        if not session_id:
            await self.send_error(websocket, "Not authenticated")
            return

        session = self.sessions.get(session_id)
        if not session:
            await self.send_error(websocket, "Session not found")
            return

        # Send message history
        await self.send_message(websocket, {
            "type": "history",
            "messages": [asdict(msg) for msg in session.messages],
            "count": len(session.messages),
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_ai_message(self, websocket: WebSocketServerProtocol, session_id: str, content: str, context: Optional[Dict] = None):
        """Send AI message to client"""
        session = self.sessions.get(session_id)
        if not session:
            return

        ai_message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            type="ai",
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            context=context
        )
        session.messages.append(ai_message)

        await self.send_message(websocket, {
            "type": "message",
            "message": asdict(ai_message)
        })

    async def send_message(self, websocket: WebSocketServerProtocol, data: dict):
        """Send message to WebSocket client"""
        try:
            await websocket.send(json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def send_error(self, websocket: WebSocketServerProtocol, error: str):
        """Send error message to client"""
        await self.send_message(websocket, {
            "type": "error",
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def generate_ai_response(self, session: ChatSession, user_message: str) -> str:
        """Generate AI response using OpenAI GPT-4"""
        if not self.openai_client:
            return "AI integration is not configured. Please contact your administrator."

        try:
            # Build conversation history
            messages = [
                {
                    "role": "system",
                    "content": self.get_system_prompt(session.context)
                }
            ]

            # Add recent message history (last 10 messages)
            recent_messages = session.messages[-10:]
            for msg in recent_messages:
                messages.append({
                    "role": "user" if msg.type == "user" else "assistant",
                    "content": msg.content
                })

            # Add current user message (if not already in history)
            if not recent_messages or recent_messages[-1].content != user_message:
                messages.append({
                    "role": "user",
                    "content": user_message
                })

            # Call OpenAI API
            logger.debug(f"Calling OpenAI API with {len(messages)} messages")
            response = await self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
                messages=messages,
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "2000")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
                stream=False
            )

            ai_content = response.choices[0].message.content
            logger.debug(f"OpenAI response received: {len(ai_content)} characters")

            return ai_content

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again in a moment."

    def get_system_prompt(self, context: Optional[Dict] = None) -> str:
        """Get system prompt based on context"""
        base_prompt = """You are an intelligent AI assistant for Horme POV, an enterprise quotation and recommendation system.

You help sales representatives with:
- Analyzing customer requirements and RFPs
- Generating accurate quotations
- Finding suitable products and alternatives
- Providing delivery timelines and pricing
- Answering questions about products, suppliers, and projects

Always be professional, accurate, and helpful. Provide specific details when available.
Format responses clearly with bullet points and sections when appropriate."""

        if not context:
            return base_prompt

        context_type = context.get("type", "unknown")

        if context_type == "document":
            doc_name = context.get("name", "the document")
            doc_data = context.get("document_data", {})

            # Build context with document requirements if available
            requirements = doc_data.get("requirements", {})
            items = requirements.get("items", [])
            items_count = len(items)

            context_info = f"""
Current Context: Document Analysis
Document: {doc_name}
Status: {doc_data.get("status", "unknown")}
"""

            if items_count > 0:
                context_info += f"""
Extracted Requirements Summary:
- Total Items: {items_count}
- Customer: {requirements.get("customer_name", "Not specified")}
- Project: {requirements.get("project_name", "Not specified")}
- Deadline: {requirements.get("deadline", "Not specified")}

You have access to the complete list of {items_count} product requirements from this RFP.
Help the user understand the requirements, suggest products, prepare quotations, and answer specific questions about items.

When the user asks about specific products or requirements, reference the actual items from the document."""
            else:
                context_info += "\nNote: Document is being processed or no requirements were extracted yet."

            return f"{base_prompt}{context_info}"

        elif context_type == "quotation":
            quot_id = context.get("quotation_id", "unknown")
            customer = context.get("customer", "the customer")
            return f"""{base_prompt}

Current Context: Quotation
Quotation ID: {quot_id}
Customer: {customer}
The user is working on a quotation. Help them with pricing, product selection, delivery options, and customer questions."""

        elif context_type == "product":
            product_name = context.get("name", "the product")
            return f"""{base_prompt}

Current Context: Product Information
Product: {product_name}
The user is inquiring about this specific product. Provide details about specifications, pricing, alternatives, and availability."""

        return base_prompt

    def get_context_greeting(self, context: Optional[Dict] = None) -> str:
        """Get initial greeting based on context"""
        if not context:
            return """Hello! I'm your AI assistant for the Horme POV system. I can help you with:

• Analyzing customer requirements and RFPs
• Generating accurate quotations
• Finding suitable products and alternatives
• Providing delivery timelines and pricing
• Answering questions about your projects

What would you like to work on today?"""

        context_type = context.get("type", "unknown")

        if context_type == "document":
            doc_name = context.get("name", "this document")
            doc_data = context.get("document_data", {})
            status = doc_data.get("status", "unknown")

            if status == "completed":
                requirements = doc_data.get("requirements", {})
                items_count = len(requirements.get("items", []))
                customer = requirements.get("customer_name", "Not specified")
                project = requirements.get("project_name", "Not specified")

                if items_count > 0:
                    return f"""Hello! I've successfully analyzed **{doc_name}**.

**Document Summary:**
• Customer: {customer}
• Project: {project}
• Total Items: {items_count} product requirements

I'm ready to help you with:
• Reviewing specific product requirements
• Finding suitable products from our catalog
• Generating quotations
• Answering questions about the RFP

What would you like to know?"""
                else:
                    return f"""Hello! I've processed **{doc_name}**, but I couldn't extract specific product requirements.

This could mean:
• The document format is unusual
• It contains mainly text without clear product lists
• Requirements are embedded in prose

Please let me know what you're looking for and I'll search our product catalog for you."""
            elif status == "processing":
                return f"""Hello! I'm currently processing **{doc_name}**.

The document is being analyzed with advanced extraction techniques. This may take a moment for complex PDFs.

You can:
• Wait for processing to complete
• Tell me what you're looking for and I'll search our catalog
• Ask general questions about products

What would you like to do?"""
            elif status == "failed":
                error = doc_data.get("error", "unknown error")
                return f"""Hello! I encountered an issue processing **{doc_name}**.

Error: {error}

Don't worry! I can still help you:
• Tell me what products you need and I'll search our catalog
• Ask me questions about specific items
• I can help create quotations manually

What would you like to do?"""
            else:
                return f"""Hello! I've loaded **{doc_name}** for analysis.

The document is being processed. I'm ready to help you with:
• Extracting key requirements
• Identifying product needs
• Searching our product catalog
• Generating preliminary quotations

What would you like to know?"""

        elif context_type == "quotation":
            customer = context.get("customer", "the customer")
            return f"""Hello! I'm ready to help with the quotation for **{customer}**.

I can assist with:
• Product selection and alternatives
• Pricing and discounts
• Delivery options and timelines
• Customer questions and modifications

What would you like to discuss?"""

        elif context_type == "product":
            product_name = context.get("name", "this product")
            return f"""Hello! I'm ready to provide information about **{product_name}**.

I can help with:
• Product specifications and features
• Pricing and availability
• Alternative options
• Supplier information

What would you like to know?"""

        return "Hello! How can I assist you today?"

    def get_context_update_message(self, context: Optional[Dict] = None) -> str:
        """Get message for context updates"""
        if not context:
            return "Context cleared. I'm ready to help with any general inquiries."

        context_type = context.get("type", "unknown")

        if context_type == "document":
            doc_name = context.get("name", "the document")
            return f"✅ Context updated to **{doc_name}**. I'm now focused on analyzing this document. What would you like to know?"

        elif context_type == "quotation":
            customer = context.get("customer", "the customer")
            return f"✅ Context updated to quotation for **{customer}**. I'm now focused on this quotation. How can I help?"

        elif context_type == "product":
            product_name = context.get("name", "the product")
            return f"✅ Context updated to **{product_name}**. I'm now focused on this product. What information do you need?"

        return "Context updated."

    async def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        """Clean up inactive sessions (can be called periodically)"""
        current_time = datetime.utcnow()
        sessions_to_remove = []

        for session_id, session in self.sessions.items():
            last_active = datetime.fromisoformat(session.last_active)
            age_hours = (current_time - last_active).total_seconds() / 3600

            if age_hours > max_age_hours:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            logger.info(f"Cleaned up inactive session: {session_id}")

        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} inactive sessions")


async def main():
    """Main entry point"""
    server = WebSocketChatServer(
        host=os.getenv("WEBSOCKET_HOST", "0.0.0.0"),
        port=int(os.getenv("WEBSOCKET_PORT", "8001")),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        database_url=os.getenv("DATABASE_URL")
    )

    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
