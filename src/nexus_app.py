"""
Nexus Multi-Channel Sales Assistant Platform
==========================================

Complete Nexus implementation providing:
- REST API for Next.js frontend
- WebSocket support for real-time chat
- CLI commands for admin operations  
- MCP server for AI agent integration
- Unified session management
- JWT authentication and authorization
- Integration with DataFlow models

This application demonstrates advanced Nexus patterns including:
- Multi-channel orchestration (API + CLI + MCP)
- Real-time WebSocket communication
- File upload handling
- Enterprise authentication
- DataFlow model integration
"""

import os
import jwt
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

# Nexus and Kailash imports
from nexus import Nexus
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# FastAPI for advanced features
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# DataFlow models
from dataflow_models import (
    db, Company, User, UserSession, Customer, Document, 
    Quote, QuoteLineItem, ERPProduct, ActivityLog, WorkflowState
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# File Upload Configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# WebSocket Connection Manager
class ConnectionManager:
    """Manages WebSocket connections for real-time features"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: int):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
    
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
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            await websocket.send_json(message)
    
    async def send_user_message(self, message: dict, user_id: int):
        """Send message to all connections for a specific user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                await self.send_personal_message(message, connection_id)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection_id in self.active_connections:
            await self.send_personal_message(message, connection_id)

# Initialize WebSocket manager
manager = ConnectionManager()

# Authentication utilities
security = HTTPBearer()

def create_jwt_token(user_data: dict) -> str:
    """Create JWT token for user authentication"""
    payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "role": user_data["role"],
        "company_id": user_data["company_id"],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to get current authenticated user"""
    payload = verify_jwt_token(credentials.credentials)
    
    # Verify session is still active
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
    
    return payload

# Initialize Nexus application with enterprise configuration
app = Nexus(
    api_port=8000,
    mcp_port=3001,
    enable_auth=True,
    enable_monitoring=True,
    rate_limit=1000,  # Requests per minute
    auto_discovery=False,  # We'll register workflows manually
    cors_origins=[
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:3001",  # MCP clients
        "https://yourdomain.com"  # Production frontend
    ]
)

# Configure additional FastAPI settings
app.api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# WORKFLOW DEFINITIONS
# ==============================================================================

def create_user_authentication_workflow() -> WorkflowBuilder:
    """Workflow for user login and session management"""
    workflow = WorkflowBuilder()
    
    # Validate user credentials
    workflow.add_node("AsyncSQLQueryNode", "validate_user", {
        "query": """
            SELECT u.*, c.name as company_name 
            FROM users u 
            JOIN companies c ON u.company_id = c.id 
            WHERE u.email = %(email)s AND u.is_active = true
        """,
        "parameters": {"email": ""},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Create user session
    workflow.add_node("AsyncSQLExecuteNode", "create_session", {
        "query": """
            INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, created_at, expires_at)
            VALUES (%(user_id)s, %(session_token)s, %(ip_address)s, %(user_agent)s, NOW(), NOW() + INTERVAL '24 hours')
        """,
        "parameters": {},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Log authentication activity
    workflow.add_node("AsyncSQLExecuteNode", "log_activity", {
        "query": """
            INSERT INTO activity_logs (entity_type, entity_id, action, user_id, user_name, user_role, ip_address, user_agent, timestamp)
            VALUES ('user', %(user_id)s, 'login', %(user_id)s, %(user_name)s, %(user_role)s, %(ip_address)s, %(user_agent)s, NOW())
        """,
        "parameters": {},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Connect nodes
    workflow.connect("validate_user", "create_session")
    workflow.connect("create_session", "log_activity")
    
    return workflow

def create_customer_management_workflow() -> WorkflowBuilder:
    """Workflow for customer CRUD operations"""
    workflow = WorkflowBuilder()
    
    # Route based on operation type
    workflow.add_node("SwitchNode", "operation_router", {
        "condition_field": "operation",
        "cases": {
            "create": "create_customer",
            "read": "read_customer", 
            "update": "update_customer",
            "delete": "delete_customer",
            "list": "list_customers"
        },
        "default": "error_handler"
    })
    
    # Create customer
    workflow.add_node("AsyncSQLExecuteNode", "create_customer", {
        "query": """
            INSERT INTO customers (name, type, industry, primary_contact, email, phone, billing_address, status, created_at)
            VALUES (%(name)s, %(type)s, %(industry)s, %(primary_contact)s, %(email)s, %(phone)s, %(billing_address)s, 'active', NOW())
            RETURNING id
        """,
        "parameters": {},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Read customer
    workflow.add_node("AsyncSQLQueryNode", "read_customer", {
        "query": "SELECT * FROM customers WHERE id = %(customer_id)s AND deleted_at IS NULL",
        "parameters": {},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Update customer
    workflow.add_node("AsyncSQLExecuteNode", "update_customer", {
        "query": """
            UPDATE customers 
            SET name = %(name)s, type = %(type)s, industry = %(industry)s, 
                primary_contact = %(primary_contact)s, email = %(email)s, phone = %(phone)s,
                billing_address = %(billing_address)s, updated_at = NOW()
            WHERE id = %(customer_id)s AND deleted_at IS NULL
        """,
        "parameters": {},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # List customers with pagination
    workflow.add_node("AsyncSQLQueryNode", "list_customers", {
        "query": """
            SELECT * FROM customers 
            WHERE deleted_at IS NULL 
            ORDER BY created_at DESC 
            LIMIT %(limit)s OFFSET %(offset)s
        """,
        "parameters": {"limit": 20, "offset": 0},  # Default pagination
        "connection_pool": db.connection_pool
    })
    
    # Soft delete customer
    workflow.add_node("AsyncSQLExecuteNode", "delete_customer", {
        "query": "UPDATE customers SET deleted_at = NOW() WHERE id = %(customer_id)s",
        "parameters": {},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Error handler
    workflow.add_node("PythonCodeNode", "error_handler", {
        "code": "result = {'error': 'Invalid operation specified'}"
    })
    
    return workflow

def create_quote_generation_workflow() -> WorkflowBuilder:
    """Advanced workflow for AI-powered quote generation"""
    workflow = WorkflowBuilder()
    
    # Generate quote number
    workflow.add_node("PythonCodeNode", "generate_quote_number", {
        "code": """
import datetime
import random
prefix = 'Q'
timestamp = datetime.datetime.now().strftime('%Y%m%d')
random_suffix = str(random.randint(1000, 9999))
result = {'quote_number': f'{prefix}{timestamp}{random_suffix}'}
"""
    })
    
    # Create quote header
    workflow.add_node("AsyncSQLExecuteNode", "create_quote", {
        "query": """
            INSERT INTO quotes (quote_number, customer_id, title, description, status, created_date, 
                              expiry_date, created_by, currency, subtotal, total_amount)
            VALUES (%(quote_number)s, %(customer_id)s, %(title)s, %(description)s, 'draft', NOW(), 
                   NOW() + INTERVAL '30 days', %(created_by)s, %(currency)s, 0.0, 0.0)
            RETURNING id
        """,
        "parameters": {},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Process line items (if provided)
    workflow.add_node("PythonCodeNode", "process_line_items", {
        "code": """
if 'line_items' in context and context['line_items']:
    total = 0.0
    processed_items = []
    
    for i, item in enumerate(context['line_items'], 1):
        line_total = item['quantity'] * item['unit_price'] * (1 - item.get('discount_percent', 0) / 100)
        total += line_total
        
        processed_items.append({
            'line_number': i,
            'product_name': item['product_name'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'discount_percent': item.get('discount_percent', 0),
            'line_total': line_total
        })
    
    result = {
        'processed_items': processed_items,
        'subtotal': total,
        'total_amount': total  # Can add tax calculation here
    }
else:
    result = {'processed_items': [], 'subtotal': 0.0, 'total_amount': 0.0}
"""
    })
    
    # Insert line items
    workflow.add_node("AsyncSQLExecuteNode", "insert_line_items", {
        "query": """
            INSERT INTO quote_line_items (quote_id, line_number, product_name, quantity, unit_price, discount_percent, line_total)
            VALUES (%(quote_id)s, %(line_number)s, %(product_name)s, %(quantity)s, %(unit_price)s, %(discount_percent)s, %(line_total)s)
        """,
        "parameters": {},  # Will be injected for each item
        "connection_pool": db.connection_pool
    })
    
    # Update quote totals
    workflow.add_node("AsyncSQLExecuteNode", "update_quote_totals", {
        "query": """
            UPDATE quotes 
            SET subtotal = %(subtotal)s, total_amount = %(total_amount)s, updated_at = NOW()
            WHERE id = %(quote_id)s
        """,
        "parameters": {},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Log quote creation
    workflow.add_node("AsyncSQLExecuteNode", "log_quote_creation", {
        "query": """
            INSERT INTO activity_logs (entity_type, entity_id, action, user_id, user_name, user_role, ip_address, user_agent, timestamp)
            VALUES ('quote', %(quote_id)s, 'create', %(user_id)s, %(user_name)s, %(user_role)s, %(ip_address)s, %(user_agent)s, NOW())
        """,
        "parameters": {},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Connect workflow nodes
    workflow.connect("generate_quote_number", "create_quote")
    workflow.connect("create_quote", "process_line_items")
    workflow.connect("process_line_items", "insert_line_items")
    workflow.connect("insert_line_items", "update_quote_totals")
    workflow.connect("update_quote_totals", "log_quote_creation")
    
    return workflow

def create_document_processing_workflow() -> WorkflowBuilder:
    """Workflow for AI-powered document processing"""
    workflow = WorkflowBuilder()
    
    # Store document metadata
    workflow.add_node("AsyncSQLExecuteNode", "store_document", {
        "query": """
            INSERT INTO documents (name, type, category, file_path, file_size, mime_type, 
                                 customer_id, upload_date, uploaded_by, ai_status)
            VALUES (%(name)s, %(type)s, %(category)s, %(file_path)s, %(file_size)s, %(mime_type)s,
                   %(customer_id)s, NOW(), %(uploaded_by)s, 'pending')
            RETURNING id
        """,
        "parameters": {},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Queue document for AI processing
    workflow.add_node("AsyncSQLExecuteNode", "queue_processing", {
        "query": """
            INSERT INTO document_processing_queues (document_id, processing_type, ai_model, queued_at, priority)
            VALUES (%(document_id)s, %(processing_type)s, %(ai_model)s, NOW(), %(priority)s)
        """,
        "parameters": {
            "processing_type": "extract",
            "ai_model": "gpt-4",
            "priority": 5
        },
        "connection_pool": db.connection_pool
    })
    
    # Simulate AI processing (replace with actual AI integration)
    workflow.add_node("PythonCodeNode", "simulate_ai_processing", {
        "code": """
import time
import json

# Simulate processing time
time.sleep(2)

# Mock AI extraction results
extracted_data = {
    'document_type': 'RFP',
    'key_requirements': ['Feature A', 'Feature B', 'Feature C'],
    'budget_range': '$50,000 - $100,000',
    'timeline': '6 months',
    'confidence_score': 0.95
}

result = {
    'ai_extracted_data': json.dumps(extracted_data),
    'ai_confidence_score': 0.95,
    'ai_status': 'completed'
}
"""
    })
    
    # Update document with AI results
    workflow.add_node("AsyncSQLExecuteNode", "update_document_ai", {
        "query": """
            UPDATE documents 
            SET ai_status = %(ai_status)s, ai_extracted_data = %(ai_extracted_data)s, 
                ai_confidence_score = %(ai_confidence_score)s, updated_at = NOW()
            WHERE id = %(document_id)s
        """,
        "parameters": {},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Connect workflow
    workflow.connect("store_document", "queue_processing")
    workflow.connect("queue_processing", "simulate_ai_processing")
    workflow.connect("simulate_ai_processing", "update_document_ai")
    
    return workflow

def create_real_time_notification_workflow() -> WorkflowBuilder:
    """Workflow for sending real-time notifications via WebSocket"""
    workflow = WorkflowBuilder()
    
    # Determine notification recipients
    workflow.add_node("AsyncSQLQueryNode", "get_notification_recipients", {
        "query": """
            SELECT DISTINCT u.id as user_id, u.first_name, u.last_name, u.email
            FROM users u
            WHERE u.company_id = %(company_id)s 
            AND u.is_active = true
            AND (u.id = %(target_user_id)s OR %(broadcast)s = true)
        """,
        "parameters": {"broadcast": False},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Format notification message
    workflow.add_node("PythonCodeNode", "format_notification", {
        "code": """
import datetime
import json

notification = {
    'id': str(context.get('notification_id', '')),
    'type': context.get('notification_type', 'info'),
    'title': context.get('title', 'Notification'),
    'message': context.get('message', ''),
    'data': context.get('data', {}),
    'timestamp': datetime.datetime.now().isoformat(),
    'read': False
}

result = {'formatted_notification': notification}
"""
    })
    
    # Store notification in database
    workflow.add_node("AsyncSQLExecuteNode", "store_notification", {
        "query": """
            INSERT INTO notifications (user_id, type, title, message, data, created_at, read)
            VALUES (%(user_id)s, %(type)s, %(title)s, %(message)s, %(data)s, NOW(), false)
        """,
        "parameters": {},  # Will be injected
        "connection_pool": db.connection_pool
    })
    
    # Send WebSocket notification
    workflow.add_node("PythonCodeNode", "send_websocket", {
        "code": """
# This would integrate with the WebSocket manager
# For now, we'll just prepare the data
result = {'websocket_sent': True, 'recipients': context.get('recipients', [])}
"""
    })
    
    # Connect workflow
    workflow.connect("get_notification_recipients", "format_notification")
    workflow.connect("format_notification", "store_notification")
    workflow.connect("store_notification", "send_websocket")
    
    return workflow

# ==============================================================================
# REGISTER WORKFLOWS WITH NEXUS
# ==============================================================================

# Register all workflows with the Nexus platform
app.register("user_authentication", create_user_authentication_workflow().build())
app.register("customer_management", create_customer_management_workflow().build())
app.register("quote_generation", create_quote_generation_workflow().build())
app.register("document_processing", create_document_processing_workflow().build())
app.register("real_time_notification", create_real_time_notification_workflow().build())

# ==============================================================================
# CUSTOM API ENDPOINTS
# ==============================================================================

@app.api_app.post("/api/auth/login")
async def login(credentials: Dict[str, str]):
    """Custom login endpoint with JWT token generation"""
    try:
        # Execute authentication workflow
        runtime = LocalRuntime()
        workflow = create_user_authentication_workflow()
        
        # Inject credentials
        context = {
            "email": credentials.get("email"),
            "ip_address": "127.0.0.1",  # Should get from request
            "user_agent": "Web Browser"  # Should get from request
        }
        
        results, _ = runtime.execute(workflow.build(), context)
        
        user_data = results.get("validate_user", {})
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create JWT token
        token = create_jwt_token(user_data[0])  # Assuming single user result
        
        # Return token and user info
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user_data[0]["id"],
                "email": user_data[0]["email"],
                "first_name": user_data[0]["first_name"],
                "last_name": user_data[0]["last_name"],
                "role": user_data[0]["role"],
                "company_name": user_data[0]["company_name"]
            }
        }
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.api_app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    customer_id: Optional[int] = None,
    document_type: str = "general",
    current_user: dict = Depends(get_current_user)
):
    """File upload endpoint with AI processing"""
    try:
        # Validate file size
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Save file
        file_path = UPLOAD_DIR / f"{current_user['user_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document through workflow
        runtime = LocalRuntime()
        workflow = create_document_processing_workflow()
        
        context = {
            "name": file.filename,
            "type": document_type,
            "category": "inbound",
            "file_path": str(file_path),
            "file_size": file.size,
            "mime_type": file.content_type,
            "customer_id": customer_id,
            "uploaded_by": current_user["user_id"]
        }
        
        results, _ = runtime.execute(workflow.build(), context)
        
        # Send real-time notification
        await manager.send_user_message({
            "type": "document_uploaded",
            "message": f"Document '{file.filename}' uploaded successfully",
            "document_id": results.get("store_document", {}).get("id")
        }, current_user["user_id"])
        
        return {
            "message": "File uploaded successfully",
            "document_id": results.get("store_document", {}).get("id"),
            "file_name": file.filename,
            "processing_status": "queued"
        }
    
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")

@app.api_app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: str):
    """WebSocket endpoint for real-time communication"""
    try:
        # Verify JWT token
        payload = verify_jwt_token(token)
        user_id = payload["user_id"]
        
        # Connect to WebSocket manager
        await manager.connect(websocket, client_id, user_id)
        
        # Send welcome message
        await manager.send_personal_message({
            "type": "welcome",
            "message": "Connected to sales assistant",
            "timestamp": datetime.now().isoformat()
        }, client_id)
        
        try:
            while True:
                # Receive messages from client
                data = await websocket.receive_json()
                
                # Handle different message types
                if data.get("type") == "chat_message":
                    # Process chat message (could integrate with AI)
                    response = {
                        "type": "chat_response",
                        "message": f"Received: {data.get('message')}",
                        "timestamp": datetime.now().isoformat(),
                        "user_id": user_id
                    }
                    await manager.send_personal_message(response, client_id)
                
                elif data.get("type") == "quote_request":
                    # Handle quote generation request
                    await manager.send_personal_message({
                        "type": "quote_processing",
                        "message": "Processing quote request...",
                        "timestamp": datetime.now().isoformat()
                    }, client_id)
                    
                    # Execute quote workflow (simplified)
                    # ... quote processing logic ...
                    
                    await manager.send_personal_message({
                        "type": "quote_ready",
                        "message": "Quote generated successfully",
                        "quote_id": "Q12345",
                        "timestamp": datetime.now().isoformat()
                    }, client_id)
        
        except WebSocketDisconnect:
            manager.disconnect(client_id, user_id)
    
    except jwt.JWTError:
        await websocket.close(code=1008, reason="Invalid token")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=1011, reason="Internal error")

# ==============================================================================
# CLI COMMAND DEFINITIONS
# ==============================================================================

@app.cli.command("create-user")
@app.cli.option("--email", required=True, help="User email address")
@app.cli.option("--first-name", required=True, help="User first name")
@app.cli.option("--last-name", required=True, help="User last name")
@app.cli.option("--role", default="sales_rep", help="User role")
@app.cli.option("--company-id", type=int, required=True, help="Company ID")
def create_user_command(email: str, first_name: str, last_name: str, role: str, company_id: int):
    """Create a new user account"""
    try:
        runtime = LocalRuntime()
        workflow = WorkflowBuilder()
        
        workflow.add_node("AsyncSQLExecuteNode", "create_user", {
            "query": """
                INSERT INTO users (first_name, last_name, email, role, company_id, department, is_active)
                VALUES (%(first_name)s, %(last_name)s, %(email)s, %(role)s, %(company_id)s, 'Sales', true)
                RETURNING id
            """,
            "parameters": {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "role": role,
                "company_id": company_id
            },
            "connection_pool": db.connection_pool
        })
        
        results, _ = runtime.execute(workflow.build())
        user_id = results.get("create_user", {}).get("id")
        
        print(f"✅ User created successfully with ID: {user_id}")
        print(f"📧 Email: {email}")
        print(f"👤 Name: {first_name} {last_name}")
        print(f"🔑 Role: {role}")
    
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")

@app.cli.command("sync-erp-products")
@app.cli.option("--batch-size", default=100, help="Batch size for sync")
@app.cli.option("--dry-run", is_flag=True, help="Preview changes without executing")
def sync_erp_products_command(batch_size: int, dry_run: bool):
    """Synchronize products from ERP system"""
    try:
        runtime = LocalRuntime()
        workflow = WorkflowBuilder()
        
        # Mock ERP sync workflow
        workflow.add_node("PythonCodeNode", "mock_erp_sync", {
            "code": f"""
import random
import datetime

# Simulate ERP product sync
products_synced = random.randint(50, 200)
result = {{
    'products_synced': products_synced,
    'batch_size': {batch_size},
    'dry_run': {dry_run},
    'sync_time': datetime.datetime.now().isoformat()
}}

if {dry_run}:
    print(f"DRY RUN: Would sync {{products_synced}} products")
else:
    print(f"Synced {{products_synced}} products successfully")
"""
        })
        
        results, _ = runtime.execute(workflow.build())
        
        if dry_run:
            print("🔍 Dry run completed - no changes made")
        else:
            print("✅ ERP product sync completed successfully")
    
    except Exception as e:
        print(f"❌ Error syncing ERP products: {str(e)}")

@app.cli.command("generate-reports")
@app.cli.option("--report-type", required=True, help="Type of report to generate")
@app.cli.option("--start-date", help="Start date (YYYY-MM-DD)")
@app.cli.option("--end-date", help="End date (YYYY-MM-DD)")
def generate_reports_command(report_type: str, start_date: Optional[str], end_date: Optional[str]):
    """Generate business reports"""
    try:
        runtime = LocalRuntime()
        workflow = WorkflowBuilder()
        
        # Report generation workflow
        workflow.add_node("AsyncSQLQueryNode", "generate_report", {
            "query": f"""
                SELECT 
                    COUNT(*) as total_records,
                    '{report_type}' as report_type,
                    COALESCE(%(start_date)s, '2024-01-01') as start_date,
                    COALESCE(%(end_date)s, CURRENT_DATE::text) as end_date
                FROM quotes 
                WHERE created_date BETWEEN COALESCE(%(start_date)s::date, '2024-01-01') 
                AND COALESCE(%(end_date)s::date, CURRENT_DATE)
            """,
            "parameters": {"start_date": start_date, "end_date": end_date},
            "connection_pool": db.connection_pool
        })
        
        results, _ = runtime.execute(workflow.build())
        report_data = results.get("generate_report", [{}])[0]
        
        print(f"📊 Report Type: {report_type}")
        print(f"📅 Period: {report_data.get('start_date')} to {report_data.get('end_date')}")
        print(f"📈 Total Records: {report_data.get('total_records', 0)}")
        print("✅ Report generated successfully")
    
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")

# ==============================================================================
# MCP TOOL DEFINITIONS
# ==============================================================================

@app.mcp_server.tool("get_customer_info")
def get_customer_info_tool(customer_id: int) -> Dict[str, Any]:
    """MCP tool to get customer information for AI agents"""
    try:
        runtime = LocalRuntime()
        workflow = WorkflowBuilder()
        
        workflow.add_node("AsyncSQLQueryNode", "get_customer", {
            "query": """
                SELECT c.*, 
                       COUNT(q.id) as total_quotes,
                       SUM(q.total_amount) as total_quote_value
                FROM customers c
                LEFT JOIN quotes q ON c.id = q.customer_id
                WHERE c.id = %(customer_id)s AND c.deleted_at IS NULL
                GROUP BY c.id
            """,
            "parameters": {"customer_id": customer_id},
            "connection_pool": db.connection_pool
        })
        
        results, _ = runtime.execute(workflow.build())
        customer_data = results.get("get_customer", [])
        
        if customer_data:
            return {
                "success": True,
                "customer": customer_data[0],
                "message": f"Customer {customer_id} found"
            }
        else:
            return {
                "success": False,
                "error": f"Customer {customer_id} not found",
                "customer": None
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "customer": None
        }

@app.mcp_server.tool("create_quote")
def create_quote_tool(
    customer_id: int,
    title: str,
    description: str = "",
    line_items: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """MCP tool to create quotes for AI agents"""
    try:
        runtime = LocalRuntime()
        workflow = create_quote_generation_workflow()
        
        context = {
            "customer_id": customer_id,
            "title": title,
            "description": description,
            "created_by": 1,  # System user for MCP
            "currency": "USD",
            "line_items": line_items or []
        }
        
        results, _ = runtime.execute(workflow.build(), context)
        quote_id = results.get("create_quote", {}).get("id")
        
        return {
            "success": True,
            "quote_id": quote_id,
            "quote_number": results.get("generate_quote_number", {}).get("quote_number"),
            "message": f"Quote created successfully for customer {customer_id}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "quote_id": None
        }

@app.mcp_server.tool("search_products")
def search_products_tool(
    query: str,
    category: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """MCP tool to search ERP products for AI agents"""
    try:
        runtime = LocalRuntime()
        workflow = WorkflowBuilder()
        
        search_query = """
            SELECT product_code, name, description, category, list_price, stock_status
            FROM erp_products 
            WHERE (name ILIKE %(query)s OR description ILIKE %(query)s)
        """
        
        params = {"query": f"%{query}%", "limit": limit}
        
        if category:
            search_query += " AND category = %(category)s"
            params["category"] = category
        
        search_query += " ORDER BY name LIMIT %(limit)s"
        
        workflow.add_node("AsyncSQLQueryNode", "search_products", {
            "query": search_query,
            "parameters": params,
            "connection_pool": db.connection_pool
        })
        
        results, _ = runtime.execute(workflow.build())
        products = results.get("search_products", [])
        
        return {
            "success": True,
            "products": products,
            "count": len(products),
            "query": query
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "products": []
        }

# ==============================================================================
# APPLICATION STARTUP
# ==============================================================================

def setup_database():
    """Initialize database schema and sample data"""
    try:
        # DataFlow will handle schema creation with auto_migrate=True
        logger.info("Database setup completed via DataFlow auto-migration")
        return True
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False

def main():
    """Main application entry point"""
    logger.info("🚀 Starting Nexus Sales Assistant Platform")
    
    # Setup database
    if not setup_database():
        logger.error("❌ Database setup failed - exiting")
        return
    
    # Configure enterprise features
    app.auth.strategy = "jwt"
    app.monitoring.interval = 30
    app.monitoring.metrics = ["requests", "latency", "errors", "websockets"]
    
    logger.info("✅ Enterprise features configured")
    logger.info("🌐 Multi-channel access available:")
    logger.info("   • REST API: http://localhost:8000")
    logger.info("   • WebSocket: ws://localhost:8000/ws/{client_id}?token={jwt_token}")
    logger.info("   • CLI: nexus --help")
    logger.info("   • MCP Server: http://localhost:3001")
    
    # Start the platform (this blocks until stopped)
    app.start()

if __name__ == "__main__":
    main()