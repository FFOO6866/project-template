"""
Nexus Backend API Server
Production-ready FastAPI server for the Nexus multi-channel platform
Designed to integrate with PostgreSQL and Redis, providing all endpoints for the frontend
"""

import asyncio
import os
import sys
import time
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import asyncpg
from redis import asyncio as aioredis
import jwt
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, ValidationError
import structlog
from contextlib import asynccontextmanager

# Import our production services
from src.services.document_processor import DocumentProcessor
from src.services.product_matcher import ProductMatcher
from src.services.quotation_generator import QuotationGenerator

# Pydantic models for request/response
class LoginCredentials(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]

class User(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    company_name: str
    company_id: int

class Customer(BaseModel):
    id: Optional[int] = None
    name: str
    type: str
    industry: str
    primary_contact: str
    email: str
    phone: str
    billing_address: str
    status: str = "active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class QuoteLineItem(BaseModel):
    line_number: int
    product_name: str
    quantity: int
    unit_price: float
    discount_percent: float
    line_total: float

class Quote(BaseModel):
    id: Optional[int] = None
    quote_number: Optional[str] = None
    customer_id: int
    title: str
    description: str
    status: str = "draft"
    created_date: Optional[str] = None
    expiry_date: str
    created_by: Optional[int] = None
    currency: str = "USD"
    subtotal: float
    total_amount: float
    line_items: List[QuoteLineItem]

class Document(BaseModel):
    id: Optional[int] = None
    name: str
    type: str
    category: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    customer_id: Optional[int] = None
    upload_date: Optional[str] = None
    uploaded_by: Optional[int] = None
    ai_status: str = "pending"
    ai_extracted_data: Optional[str] = None
    ai_confidence_score: Optional[float] = None

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

class NexusBackendAPI:
    """Production Nexus Backend API with PostgreSQL and Redis integration"""
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis: Optional[aioredis.Redis] = None
        self.security = HTTPBearer()

        # Configuration - NO FALLBACKS, fail fast if not configured
        self.instance_id = os.getenv("NEXUS_INSTANCE_ID", f"nexus-{uuid.uuid4().hex[:8]}")

        # Critical secrets - MUST be set via environment variables
        self.jwt_secret = os.getenv("NEXUS_JWT_SECRET") or os.getenv("JWT_SECRET")
        if not self.jwt_secret:
            raise ValueError("NEXUS_JWT_SECRET or JWT_SECRET environment variable is required")

        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        self.redis_url = os.getenv("REDIS_URL")
        if not self.redis_url:
            raise ValueError("REDIS_URL environment variable is required")

        logger.info("Nexus Backend API initialized", instance_id=self.instance_id)

    async def initialize(self):
        """Initialize database and Redis connections"""
        try:
            # Initialize PostgreSQL connection pool
            self.db_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # Initialize Redis
            self.redis = aioredis.from_url(self.redis_url)
            await self.redis.ping()
            
            # Create database tables if they don't exist
            await self._create_tables()
            
            logger.info("Database and Redis connections initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize connections", error=str(e))
            raise

    async def cleanup(self):
        """Cleanup resources on shutdown"""
        logger.info("Shutting down Nexus Backend API", instance_id=self.instance_id)
        
        if self.db_pool:
            await self.db_pool.close()
        
        if self.redis:
            await self.redis.close()

    async def _create_tables(self):
        """Create database tables if they don't exist"""
        create_tables_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            role VARCHAR(50) DEFAULT 'user',
            company_name VARCHAR(255),
            company_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Customers table
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(100),
            industry VARCHAR(100),
            primary_contact VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            billing_address TEXT,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Quotes table
        CREATE TABLE IF NOT EXISTS quotes (
            id SERIAL PRIMARY KEY,
            quote_number VARCHAR(100) UNIQUE NOT NULL,
            customer_id INTEGER REFERENCES customers(id),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(50) DEFAULT 'draft',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expiry_date TIMESTAMP,
            created_by INTEGER REFERENCES users(id),
            currency VARCHAR(3) DEFAULT 'USD',
            subtotal DECIMAL(10,2),
            total_amount DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Quote line items table
        CREATE TABLE IF NOT EXISTS quote_line_items (
            id SERIAL PRIMARY KEY,
            quote_id INTEGER REFERENCES quotes(id) ON DELETE CASCADE,
            line_number INTEGER NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            discount_percent DECIMAL(5,2) DEFAULT 0,
            line_total DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Documents table
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(100),
            category VARCHAR(100),
            file_path VARCHAR(500),
            file_size INTEGER,
            mime_type VARCHAR(100),
            customer_id INTEGER REFERENCES customers(id),
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER REFERENCES users(id),
            ai_status VARCHAR(50) DEFAULT 'pending',
            ai_extracted_data TEXT,
            ai_confidence_score DECIMAL(3,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Activity log table
        CREATE TABLE IF NOT EXISTS activity_log (
            id SERIAL PRIMARY KEY,
            entity_type VARCHAR(100) NOT NULL,
            entity_id INTEGER NOT NULL,
            action VARCHAR(100) NOT NULL,
            user_id INTEGER REFERENCES users(id),
            user_name VARCHAR(255),
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        async with self.db_pool.acquire() as conn:
            await conn.execute(create_tables_sql)

            # Create admin user from environment variables (secure)
            admin_email = os.getenv("ADMIN_EMAIL")
            admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")

            if admin_email and admin_password_hash:
                try:
                    await conn.execute("""
                        INSERT INTO users (email, password_hash, first_name, last_name, role, company_name, company_id)
                        VALUES ($1, $2, 'Admin', 'User', 'admin', 'System', 1)
                        ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
                    """, admin_email, admin_password_hash)
                    logger.info("Admin user created/updated from environment variables", email=admin_email)
                except Exception as e:
                    logger.error("Failed to create admin user", error=str(e))
            else:
                logger.warning("Admin user credentials not configured - skipping admin user creation. Set ADMIN_EMAIL and ADMIN_PASSWORD_HASH environment variables.")

        logger.info("Database tables created/verified successfully")


# Create the application with lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    await api_instance.initialize()
    yield
    # Shutdown
    await api_instance.cleanup()

# Initialize API instance
api_instance = NexusBackendAPI()

# Create FastAPI app
app = FastAPI(
    title="Nexus Backend API",
    version="1.0.0",
    description="Production Nexus Backend API with PostgreSQL and Redis integration",
    lifespan=lifespan
)

# Configure CORS origins (MUST be set for production)
cors_origins_str = os.getenv("CORS_ORIGINS")
environment = os.getenv("ENVIRONMENT", "development")

if not cors_origins_str:
    if environment == "production":
        raise ValueError("CORS_ORIGINS environment variable is required in production")
    else:
        # Development fallback only
        logger.warning("CORS_ORIGINS not set, using development defaults (localhost)")
        cors_origins_str = "http://localhost:3000,http://localhost:8080"

# Parse CORS origins (handle both comma-separated and JSON array formats)
if cors_origins_str.startswith("["):
    import json
    cors_origins = json.loads(cors_origins_str)
else:
    cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

logger.info("CORS configured", origins=cors_origins, environment=environment)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods, not "*"
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request tracking middleware
@app.middleware("http")
async def track_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Add response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        response.headers["X-Instance-ID"] = api_instance.instance_id
        
        logger.info("API request completed",
                   request_id=request_id,
                   method=request.method,
                   path=request.url.path,
                   status=response.status_code,
                   duration=duration)
        
        return response
        
    except Exception as e:
        logger.error("Request failed", request_id=request_id, error=str(e))
        raise

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        
        # Try to get from Redis cache first
        if api_instance.redis:
            cached_user = await api_instance.redis.get(f"nexus:session:{token}")
            if cached_user:
                return json.loads(cached_user)
        
        # Decode JWT token
        payload = jwt.decode(token, api_instance.jwt_secret, algorithms=["HS256"])
        
        # Validate token
        if payload.get("exp", 0) < datetime.utcnow().timestamp():
            raise HTTPException(status_code=401, detail="Token expired")
        
        return payload
        
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============================================================================
# Background Processing Pipeline
# ============================================================================

async def process_document_pipeline(document_id: int, file_path: str):
    """
    Complete document processing pipeline
    NO SHORTCUTS - Real AI extraction, product matching, quotation generation

    Flow: Document Upload → Text Extraction → Requirement Analysis →
          Product Matching → Quotation Generation → PDF Creation
    """
    logger.info(f"Starting processing pipeline for document {document_id}")

    try:
        # Initialize services
        doc_processor = DocumentProcessor()
        product_matcher = ProductMatcher()
        quotation_generator = QuotationGenerator()

        # Step 1: Process document and extract requirements
        logger.info(f"Step 1/4: Processing document {document_id}")
        processing_result = await doc_processor.process_document(
            document_id,
            file_path,
            api_instance.db_pool
        )

        requirements = processing_result.get('requirements', {})

        if not requirements.get('items'):
            logger.warning(f"No items found in document {document_id}")
            return

        logger.info(f"Extracted {len(requirements['items'])} requirement items")

        # Step 2: Match products from database
        logger.info(f"Step 2/4: Matching products for document {document_id}")
        matched_products = await product_matcher.match_products(
            requirements,
            api_instance.db_pool
        )

        if not matched_products:
            logger.error(f"No products matched for document {document_id}")
            return

        logger.info(f"Matched {len(matched_products)} products")

        # Step 3: Calculate pricing
        logger.info(f"Step 3/4: Calculating pricing for document {document_id}")
        pricing = await product_matcher.calculate_pricing(matched_products)

        logger.info(f"Total quotation value: {pricing['currency']} {pricing['total']}")

        # Step 4: Generate quotation
        logger.info(f"Step 4/4: Generating quotation for document {document_id}")
        quotation_id = await quotation_generator.generate_quotation(
            document_id,
            requirements,
            matched_products,
            pricing,
            api_instance.db_pool
        )

        logger.info(f"Created quotation {quotation_id} for document {document_id}")

        # Step 5: Generate PDF
        logger.info(f"Generating PDF for quotation {quotation_id}")
        pdf_path = await quotation_generator.generate_pdf(
            quotation_id,
            api_instance.db_pool
        )

        logger.info(f"✅ Pipeline complete for document {document_id}")
        logger.info(f"   - Requirements: {len(requirements['items'])} items")
        logger.info(f"   - Products matched: {len(matched_products)}")
        logger.info(f"   - Quotation ID: {quotation_id}")
        logger.info(f"   - Total value: {pricing['currency']} {pricing['total']}")
        logger.info(f"   - PDF: {pdf_path}")

    except Exception as e:
        logger.error(f"❌ Pipeline failed for document {document_id}: {str(e)}", exc_info=True)
        # Error already logged in individual services


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Comprehensive health check"""
    checks = {}
    overall_status = "healthy"
    
    # Database check
    try:
        if api_instance.db_pool:
            async with api_instance.db_pool.acquire() as conn:
                start = time.time()
                await conn.fetchval("SELECT 1")
                response_time = (time.time() - start) * 1000
                checks["database"] = {"status": "healthy", "response_time_ms": response_time}
        else:
            checks["database"] = {"status": "unhealthy", "error": "Not connected"}
            overall_status = "unhealthy"
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "unhealthy"
    
    # Redis check
    try:
        if api_instance.redis:
            start = time.time()
            await api_instance.redis.ping()
            response_time = (time.time() - start) * 1000
            checks["redis"] = {"status": "healthy", "response_time_ms": response_time}
        else:
            checks["redis"] = {"status": "unhealthy", "error": "Not connected"}
            overall_status = "unhealthy"
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "instance_id": api_instance.instance_id,
        "version": "1.0.0",
        "checks": checks
    }

# Basic health endpoint (for Docker health checks)
@app.get("/health")
async def basic_health():
    """Basic health check for Docker"""
    return {"status": "healthy"}

# Authentication endpoints
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(credentials: LoginCredentials):
    """Authenticate user and return JWT token - PRODUCTION: Uses database verification"""
    try:
        # PRODUCTION: Authenticate against database with bcrypt password verification
        import bcrypt

        async with api_instance.db_pool.acquire() as conn:
            # Fetch user from database
            user = await conn.fetchrow(
                "SELECT id, email, password_hash, first_name, last_name, role, company_name, company_id FROM users WHERE email = $1",
                credentials.email
            )

            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Verify password using bcrypt
            if not bcrypt.checkpw(credentials.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # User authenticated successfully
            user_data = {
                "id": user["id"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role": user["role"],
                "company_name": user["company_name"],
                "company_id": user["company_id"]
            }

            token_data = {
                "user_id": str(user_data["id"]),
                "email": user_data["email"],
                "role": user_data["role"],
                "exp": datetime.utcnow() + timedelta(hours=24),
                "iat": datetime.utcnow(),
                "iss": "nexus-api",
                "aud": "nexus-platform"
            }

            token = jwt.encode(token_data, api_instance.jwt_secret, algorithm="HS256")
            
            # Cache user session in Redis
            if api_instance.redis:
                await api_instance.redis.setex(
                    f"nexus:session:{token}",
                    86400,  # 24 hours
                    json.dumps(token_data, default=str)
                )
            
            return LoginResponse(
                access_token=token,
                token_type="bearer",
                expires_in=86400,
                user=user_data
            )

    except HTTPException:
        # Re-raise HTTP exceptions (authentication failures)
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(status_code=500, detail="Login failed")

# User endpoints
@app.get("/api/user/profile")
async def get_user_profile(current_user: Dict = Depends(get_current_user)):
    """Get current user profile"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, first_name, last_name, role, company_name, company_id FROM users WHERE id = $1",
                int(current_user["user_id"])
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {"user": dict(user)}
            
    except Exception as e:
        logger.error("Failed to get user profile", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get user profile")

@app.put("/api/user/preferences")
async def update_user_preferences(
    preferences: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Update user preferences"""
    try:
        # Store preferences in Redis
        if api_instance.redis:
            await api_instance.redis.setex(
                f"nexus:preferences:{current_user['user_id']}",
                86400 * 30,  # 30 days
                json.dumps(preferences)
            )
        
        return {"preferences": preferences}
        
    except Exception as e:
        logger.error("Failed to update preferences", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update preferences")

# Dashboard endpoint
@app.get("/api/dashboard")
async def get_dashboard_data():
    """Get dashboard metrics and data - PUBLIC endpoint"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            # Get basic counts
            total_customers = await conn.fetchval("SELECT COUNT(*) FROM customers")
            total_quotes = await conn.fetchval("SELECT COUNT(*) FROM quotes")
            total_documents = await conn.fetchval("SELECT COUNT(*) FROM documents")
            
            # Get recent activity
            recent_activity = await conn.fetch("""
                SELECT entity_type, entity_id, action, user_name, timestamp, description
                FROM activity_log
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            
            activity_items = [
                {
                    "id": i + 1,
                    "entity_type": activity["entity_type"],
                    "entity_id": activity["entity_id"],
                    "action": activity["action"],
                    "user_name": activity["user_name"] or "System",
                    "timestamp": activity["timestamp"].isoformat(),
                    "description": activity["description"]
                }
                for i, activity in enumerate(recent_activity)
            ]
            
            return {
                "total_customers": total_customers or 0,
                "total_quotes": total_quotes or 0,
                "total_documents": total_documents or 0,
                "recent_activity": activity_items,
                "metrics": {
                    "active_quotes": await conn.fetchval("SELECT COUNT(*) FROM quotes WHERE status = 'active'") or 0,
                    "pending_documents": await conn.fetchval("SELECT COUNT(*) FROM documents WHERE ai_status = 'pending'") or 0
                }
            }
            
    except Exception as e:
        logger.error("Failed to get dashboard data", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")

# Customer endpoints
@app.get("/api/customers")
async def get_customers(current_user: Dict = Depends(get_current_user)):
    """Get all customers"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            customers = await conn.fetch("""
                SELECT id, name, type, industry, primary_contact, email, phone, 
                       billing_address, status, created_at, updated_at
                FROM customers
                ORDER BY created_at DESC
            """)
            
            return [dict(customer) for customer in customers]
            
    except Exception as e:
        logger.error("Failed to get customers", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get customers")

@app.get("/api/customers/{customer_id}")
async def get_customer(customer_id: int, current_user: Dict = Depends(get_current_user)):
    """Get specific customer"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            customer = await conn.fetchrow("""
                SELECT id, name, type, industry, primary_contact, email, phone, 
                       billing_address, status, created_at, updated_at
                FROM customers
                WHERE id = $1
            """, customer_id)
            
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            return dict(customer)
            
    except Exception as e:
        logger.error("Failed to get customer", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get customer")

@app.post("/api/customers")
async def create_customer(customer: Customer, current_user: Dict = Depends(get_current_user)):
    """Create new customer"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            customer_id = await conn.fetchval("""
                INSERT INTO customers (name, type, industry, primary_contact, email, phone, billing_address, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """, customer.name, customer.type, customer.industry, customer.primary_contact,
                customer.email, customer.phone, customer.billing_address, customer.status)
            
            # Log activity
            await conn.execute("""
                INSERT INTO activity_log (entity_type, entity_id, action, user_id, user_name, description)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, "customer", customer_id, "created", int(current_user["user_id"]), 
                current_user.get("email", "Unknown"), f"Customer '{customer.name}' created")
            
            return {"customer_id": customer_id}
            
    except Exception as e:
        logger.error("Failed to create customer", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create customer")

@app.put("/api/customers/{customer_id}")
async def update_customer(
    customer_id: int, 
    customer: Customer, 
    current_user: Dict = Depends(get_current_user)
):
    """Update customer"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE customers 
                SET name=$1, type=$2, industry=$3, primary_contact=$4, email=$5, 
                    phone=$6, billing_address=$7, status=$8, updated_at=CURRENT_TIMESTAMP
                WHERE id=$9
            """, customer.name, customer.type, customer.industry, customer.primary_contact,
                customer.email, customer.phone, customer.billing_address, customer.status, customer_id)
            
            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Customer not found")
            
            # Log activity
            await conn.execute("""
                INSERT INTO activity_log (entity_type, entity_id, action, user_id, user_name, description)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, "customer", customer_id, "updated", int(current_user["user_id"]), 
                current_user.get("email", "Unknown"), f"Customer '{customer.name}' updated")
            
            return {"success": True}
            
    except Exception as e:
        logger.error("Failed to update customer", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update customer")

# Quote endpoints
@app.get("/api/quotes")
async def get_quotes():
    """Get all quotes - PUBLIC endpoint for demo/POC"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            quotes = await conn.fetch("""
                SELECT q.id, q.quote_number, q.customer_id, q.title, q.description, 
                       q.status, q.created_date, q.expiry_date, q.created_by, 
                       q.currency, q.subtotal, q.total_amount, c.name as customer_name
                FROM quotes q
                LEFT JOIN customers c ON q.customer_id = c.id
                ORDER BY q.created_date DESC
            """)
            
            result = []
            for quote in quotes:
                quote_dict = dict(quote)
                
                # Get line items
                line_items = await conn.fetch("""
                    SELECT line_number, product_name, quantity, unit_price, discount_percent, line_total
                    FROM quote_line_items
                    WHERE quote_id = $1
                    ORDER BY line_number
                """, quote["id"])
                
                quote_dict["line_items"] = [dict(item) for item in line_items]
                result.append(quote_dict)
            
            return result
            
    except Exception as e:
        logger.error("Failed to get quotes", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get quotes")

@app.get("/api/quotes/{quote_id}")
async def get_quote(quote_id: int):
    """Get specific quote - PUBLIC endpoint for demo/POC"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            quote = await conn.fetchrow("""
                SELECT id, quote_number, customer_id, title, description, status, 
                       created_date, expiry_date, created_by, currency, subtotal, total_amount
                FROM quotes
                WHERE id = $1
            """, quote_id)
            
            if not quote:
                raise HTTPException(status_code=404, detail="Quote not found")
            
            # Get line items
            line_items = await conn.fetch("""
                SELECT line_number, product_name, quantity, unit_price, discount_percent, line_total
                FROM quote_line_items
                WHERE quote_id = $1
                ORDER BY line_number
            """, quote_id)
            
            result = dict(quote)
            result["line_items"] = [dict(item) for item in line_items]
            
            return result
            
    except Exception as e:
        logger.error("Failed to get quote", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get quote")

@app.post("/api/quotes")
async def create_quote(quote: Quote, current_user: Dict = Depends(get_current_user)):
    """Create new quote"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            # Generate quote number
            quote_number = f"Q-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            quote_id = await conn.fetchval("""
                INSERT INTO quotes (quote_number, customer_id, title, description, status, 
                                  expiry_date, created_by, currency, subtotal, total_amount)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """, quote_number, quote.customer_id, quote.title, quote.description, quote.status,
                quote.expiry_date, int(current_user["user_id"]), quote.currency, quote.subtotal, quote.total_amount)
            
            # Insert line items
            for item in quote.line_items:
                await conn.execute("""
                    INSERT INTO quote_line_items (quote_id, line_number, product_name, quantity, 
                                                unit_price, discount_percent, line_total)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, quote_id, item.line_number, item.product_name, item.quantity,
                    item.unit_price, item.discount_percent, item.line_total)
            
            # Log activity
            await conn.execute("""
                INSERT INTO activity_log (entity_type, entity_id, action, user_id, user_name, description)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, "quote", quote_id, "created", int(current_user["user_id"]), 
                current_user.get("email", "Unknown"), f"Quote '{quote_number}' created")
            
            return {"quote_id": quote_id, "quote_number": quote_number}
            
    except Exception as e:
        logger.error("Failed to create quote", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create quote")

@app.put("/api/quotes/{quote_id}/status")
async def update_quote_status(
    quote_id: int, 
    status_data: Dict[str, Any], 
    current_user: Dict = Depends(get_current_user)
):
    """Update quote status"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE quotes 
                SET status = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, status_data["status"], quote_id)
            
            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Quote not found")
            
            # Log activity
            await conn.execute("""
                INSERT INTO activity_log (entity_type, entity_id, action, user_id, user_name, description)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, "quote", quote_id, "status_updated", int(current_user["user_id"]), 
                current_user.get("email", "Unknown"), f"Quote status changed to '{status_data['status']}'")
            
            return {"success": True}
            
    except Exception as e:
        logger.error("Failed to update quote status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update quote status")

# Document endpoints
@app.get("/api/documents")
async def get_documents():
    """Get all documents - PUBLIC endpoint for demo/POC

    Returns ALL documents from database (not paginated for backward compatibility)
    """
    try:
        async with api_instance.db_pool.acquire() as conn:
            documents = await conn.fetch("""
                SELECT d.id, d.name, d.type, d.category, d.file_path, d.file_size,
                       d.mime_type, d.customer_id, d.upload_date, d.uploaded_by,
                       d.ai_status, d.ai_extracted_data, d.ai_confidence_score,
                       c.name as customer_name
                FROM documents d
                LEFT JOIN customers c ON d.customer_id = c.id
                ORDER BY d.upload_date DESC
            """)

            # Return simple array for backward compatibility with existing frontend
            return [dict(doc) for doc in documents]

    except Exception as e:
        logger.error("Failed to get documents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get documents")

# Recent documents endpoint - PUBLIC (no authentication required)
# IMPORTANT: This must come BEFORE /api/documents/{document_id} to avoid path conflicts
@app.get("/api/documents/recent")
async def get_recent_documents(limit: int = 20):
    """Get recently uploaded documents - PUBLIC endpoint"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            documents = await conn.fetch("""
                SELECT d.id, d.name, d.type, d.category, d.file_path, d.file_size,
                       d.mime_type, d.customer_id, d.upload_date, d.uploaded_by,
                       d.ai_status, d.ai_extracted_data, d.ai_confidence_score,
                       c.name as customer_name
                FROM documents d
                LEFT JOIN customers c ON d.customer_id = c.id
                ORDER BY d.upload_date DESC
                LIMIT $1
            """, limit)

            # CRITICAL FIX: Parse ai_extracted_data from JSON string to object
            results = []
            for doc in documents:
                result = dict(doc)
                if result.get('ai_extracted_data'):
                    try:
                        result['ai_extracted_data'] = json.loads(result['ai_extracted_data'])
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"Failed to parse ai_extracted_data for document {result.get('id')}")
                        result['ai_extracted_data'] = None
                results.append(result)

            return results

    except Exception as e:
        logger.error("Failed to get recent documents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get recent documents")

@app.get("/api/documents/{document_id}")
async def get_document(document_id: int):
    """Get specific document - PUBLIC endpoint for demo/POC"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            document = await conn.fetchrow("""
                SELECT id, name, type, category, file_path, file_size, mime_type,
                       customer_id, upload_date, uploaded_by, ai_status,
                       ai_extracted_data, ai_confidence_score
                FROM documents
                WHERE id = $1
            """, document_id)

            if not document:
                raise HTTPException(status_code=404, detail="Document not found")

            # CRITICAL FIX: Parse ai_extracted_data from JSON string to object
            # Frontend expects object, not string
            result = dict(document)
            if result.get('ai_extracted_data'):
                try:
                    result['ai_extracted_data'] = json.loads(result['ai_extracted_data'])
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse ai_extracted_data for document {document_id}")
                    result['ai_extracted_data'] = None

            return result

    except Exception as e:
        logger.error("Failed to get document", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get document")

@app.post("/api/files/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    customer_id: Optional[int] = Form(None),
    document_type: str = Form(...),
    category: Optional[str] = Form(None)
):
    """
    Upload file and create document record
    PRODUCTION: Triggers real background processing with AI
    NO AUTHENTICATION REQUIRED - For demo/POC use
    """
    try:
        # Save file to uploads directory
        upload_dir = "/app/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}_{file.filename}")

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Use demo user for uploads (no authentication required)
        demo_user_id = 1  # Default admin user
        demo_user_email = "demo@horme.com"

        # Create document record
        async with api_instance.db_pool.acquire() as conn:
            document_id = await conn.fetchval("""
                INSERT INTO documents (name, type, category, file_path, file_size,
                                     mime_type, customer_id, uploaded_by, ai_status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """, file.filename, document_type, category, file_path, len(content),
                file.content_type, customer_id, demo_user_id, "pending")

            # Log activity
            await conn.execute("""
                INSERT INTO activity_log (entity_type, entity_id, action, user_id, user_name, description)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, "document", document_id, "uploaded", demo_user_id,
                demo_user_email, f"Document '{file.filename}' uploaded")

        # PRODUCTION: Trigger background processing
        # This will: extract text → analyze requirements → match products → generate quotation
        background_tasks.add_task(
            process_document_pipeline,
            document_id,
            file_path
        )

        logger.info(f"Document {document_id} uploaded, background processing started")

        return {
            "message": "File uploaded successfully. Processing started.",
            "document_id": document_id,
            "filename": file.filename,  # Frontend expects "filename" not "file_name"
            "status": "pending"
        }

    except Exception as e:
        logger.error("Failed to upload file", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to upload file")

# Metrics endpoint - PUBLIC (no authentication required)
@app.get("/api/metrics")
async def get_metrics():
    """Get business metrics for dashboard - PUBLIC endpoint"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            # Get counts
            total_customers = await conn.fetchval("SELECT COUNT(*) FROM customers") or 0
            total_quotes = await conn.fetchval("SELECT COUNT(*) FROM quotes") or 0
            total_documents = await conn.fetchval("SELECT COUNT(*) FROM documents") or 0
            active_quotes = await conn.fetchval("SELECT COUNT(*) FROM quotes WHERE status = 'active'") or 0
            pending_documents = await conn.fetchval("SELECT COUNT(*) FROM documents WHERE ai_status = 'pending'") or 0

            # Get recent quotes count (last 30 days)
            recent_quotes = await conn.fetchval("""
                SELECT COUNT(*) FROM quotes
                WHERE created_date >= CURRENT_DATE - INTERVAL '30 days'
            """) or 0

            # Get recent documents count (last 30 days)
            recent_documents = await conn.fetchval("""
                SELECT COUNT(*) FROM documents
                WHERE upload_date >= CURRENT_DATE - INTERVAL '30 days'
            """) or 0

            return {
                "total_customers": total_customers,
                "total_quotes": total_quotes,
                "total_documents": total_documents,
                "active_quotes": active_quotes,
                "pending_documents": pending_documents,
                "recent_quotes": recent_quotes,
                "recent_documents": recent_documents,
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get metrics")

# Chat endpoint
class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    document_id: Optional[int] = None

@app.post("/api/chat")
async def chat(
    chat_message: ChatMessage
):
    """
    AI Sales Specialist Chat - Enterprise Grade
    ==========================================

    Integrates:
    - Neo4j Knowledge Graph (product relationships, compatibility)
    - Hybrid Recommendation Engine (4 algorithms)
    - Product Intelligence (rich context)
    - Dynamic conversational AI (GPT-4)

    NO AUTHENTICATION REQUIRED - For demo/POC
    NO MOCK DATA - All real data from production databases
    """
    try:
        # Get document context if provided
        document_context = None
        if chat_message.document_id:
            async with api_instance.db_pool.acquire() as conn:
                document = await conn.fetchrow("""
                    SELECT id, name, type, ai_extracted_data, ai_confidence_score
                    FROM documents
                    WHERE id = $1
                """, chat_message.document_id)

                if document:
                    # Clean up document name (remove ANY duplicate prefix like ABC_ABC_)
                    clean_name = document["name"]
                    import re
                    # Remove duplicate prefix pattern: word_word_ → word_
                    clean_name = re.sub(r'^([A-Za-z0-9]+)_\1_', r'\1_', clean_name, flags=re.IGNORECASE)

                    # Parse ai_extracted_data if it's a string
                    extracted_data = document["ai_extracted_data"]
                    if isinstance(extracted_data, str):
                        extracted_data = json.loads(extracted_data)

                    document_context = {
                        "document_id": document["id"],  # Add document_id
                        "document_name": clean_name,
                        "document_type": document["type"],
                        "extracted_data": extracted_data,  # Already parsed
                        "confidence_score": document["ai_confidence_score"]
                    }

        # Initialize AI Sales Specialist Service
        from src.services.ai_sales_specialist_service import AISalesSpecialistService

        specialist = AISalesSpecialistService(api_instance.db_pool)

        # Process chat with full AI capabilities
        result = await specialist.chat(
            message=chat_message.message,
            document_context=document_context,
            conversation_history=chat_message.context.get('history') if chat_message.context else None
        )

        return result

    except Exception as e:
        logger.error("Failed to process chat message", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process chat message: {str(e)}")

# =============================================================================
# EMAIL QUOTATION REQUEST ENDPOINTS
# =============================================================================

from src.models.email_quotation_models import (
    EmailQuotationRequest,
    EmailQuotationRequestResponse,
    EmailQuotationRequestDetail,
    EmailQuotationRequestUpdate,
    QuotationGenerationRequest,
    QuotationGenerationResponse
)

@app.get("/api/email-quotation-requests/recent", response_model=List[EmailQuotationRequestResponse])
async def get_recent_email_quotation_requests(limit: int = 20):
    """
    Get recent email quotation requests for dashboard
    PUBLIC endpoint - no authentication required
    """
    try:
        async with api_instance.db_pool.acquire() as conn:
            requests = await conn.fetch("""
                SELECT
                    id, received_date, sender_name, sender_email, subject,
                    status, ai_confidence_score, attachment_count, quotation_id, created_at
                FROM email_quotation_requests
                WHERE status IN ('pending', 'processing', 'completed', 'quotation_created')
                ORDER BY received_date DESC
                LIMIT $1
            """, limit)

            return [
                {
                    "id": r["id"],
                    "received_date": r["received_date"],
                    "sender_name": r["sender_name"],
                    "sender_email": r["sender_email"],
                    "subject": r["subject"],
                    "status": r["status"],
                    "ai_confidence_score": r["ai_confidence_score"],
                    "attachment_count": r["attachment_count"] or 0,
                    "quotation_id": r["quotation_id"],
                    "created_at": r["created_at"]
                }
                for r in requests
            ]
    except Exception as e:
        logger.error("Failed to get recent email quotation requests", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get email quotation requests")


@app.get("/api/email-quotation-requests/{request_id}")
async def get_email_quotation_request_detail(
    request_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Get detailed email quotation request with attachments"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            # Get email request
            request = await conn.fetchrow("""
                SELECT * FROM email_quotation_requests WHERE id = $1
            """, request_id)

            if not request:
                raise HTTPException(status_code=404, detail="Email request not found")

            # Get attachments
            attachments = await conn.fetch("""
                SELECT * FROM email_attachments WHERE email_request_id = $1
                ORDER BY created_at
            """, request_id)

            return {
                **dict(request),
                "attachments": [dict(a) for a in attachments]
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email request {request_id}", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get email request")


@app.post("/api/email-quotation-requests/{request_id}/process")
async def process_email_quotation_request(
    request_id: int,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Trigger quotation generation from email request
    Uses existing quotation processing pipeline - NO DUPLICATION
    """
    try:
        async with api_instance.db_pool.acquire() as conn:
            # Get email request
            request = await conn.fetchrow("""
                SELECT * FROM email_quotation_requests WHERE id = $1
            """, request_id)

            if not request:
                raise HTTPException(status_code=404, detail="Email request not found")

            if request["status"] != "completed":
                raise HTTPException(
                    status_code=400,
                    detail=f"Email request must be in 'completed' status (current: {request['status']})"
                )

            if request["quotation_id"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Quotation already created (ID: {request['quotation_id']})"
                )

            # Extract requirements from email
            requirements_json = request["extracted_requirements"]
            if not requirements_json:
                raise HTTPException(status_code=400, detail="No extracted requirements found")

            # Parse JSON string to dictionary
            import json as json_module
            requirements = json_module.loads(requirements_json) if isinstance(requirements_json, str) else requirements_json

            # Get attachments for document reference
            attachments = await conn.fetch("""
                SELECT document_id FROM email_attachments
                WHERE email_request_id = $1 AND processed = true
                ORDER BY created_at
                LIMIT 1
            """, request_id)

            # Use first attachment's document_id if available, otherwise create temp document
            document_id = None
            if attachments and attachments[0]["document_id"]:
                document_id = attachments[0]["document_id"]
            elif request["document_id"]:
                document_id = request["document_id"]
            else:
                # Create temporary document for email body
                document_id = await conn.fetchval("""
                    INSERT INTO documents (
                        name, type, ai_status, ai_extracted_data, uploaded_by
                    ) VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                """, f"Email: {request['subject']}", 'email_rfq', 'completed',
                    request['body_text'], int(current_user["user_id"]))

                # Link document to email request
                await conn.execute("""
                    UPDATE email_quotation_requests
                    SET document_id = $1
                    WHERE id = $2
                """, document_id, request_id)

            # Update status to quotation_processing
            await conn.execute("""
                UPDATE email_quotation_requests
                SET status = 'quotation_processing',
                    processed_by = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, int(current_user["user_id"]), request_id)

        # Trigger existing quotation generation pipeline
        background_tasks.add_task(
            process_email_quotation_pipeline,
            request_id,
            document_id,
            requirements
        )

        logger.info(f"Email quotation request {request_id} processing started by user {current_user['user_id']}")

        return {
            "message": "Quotation processing started",
            "request_id": request_id,
            "document_id": document_id,
            "status": "quotation_processing"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process email request {request_id}", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process email request")


@app.put("/api/email-quotation-requests/{request_id}/status")
async def update_email_quotation_request_status(
    request_id: int,
    status_update: EmailQuotationRequestUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Update email quotation request status (mark as ignored, etc.)"""
    try:
        async with api_instance.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE email_quotation_requests
                SET status = COALESCE($1, status),
                    processing_notes = COALESCE($2, processing_notes),
                    processed_by = $3,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $4
            """, status_update.status, status_update.processing_notes,
                int(current_user["user_id"]), request_id)

            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Email request not found")

            return {"success": True, "request_id": request_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update email request {request_id}", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update email request")


@app.post("/api/email-quotation-requests/{request_id}/reprocess")
async def reprocess_email_quotation_request(
    request_id: int,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Manually reprocess an email request (re-run AI extraction)
    Useful if initial processing failed or produced low confidence
    """
    try:
        async with api_instance.db_pool.acquire() as conn:
            request = await conn.fetchrow("""
                SELECT * FROM email_quotation_requests WHERE id = $1
            """, request_id)

            if not request:
                raise HTTPException(status_code=404, detail="Email request not found")

            # Update status back to processing
            await conn.execute("""
                UPDATE email_quotation_requests
                SET status = 'processing',
                    error_message = NULL,
                    processed_by = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, int(current_user["user_id"]), request_id)

        # Trigger reprocessing
        background_tasks.add_task(
            reprocess_email_requirements,
            request_id
        )

        logger.info(f"Email request {request_id} reprocessing started by user {current_user['user_id']}")

        return {
            "message": "Email request reprocessing started",
            "request_id": request_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess email request {request_id}", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to reprocess email request")


# Background task functions for email quotation processing
async def process_email_quotation_pipeline(
    email_request_id: int,
    document_id: int,
    requirements: Dict[str, Any]
):
    """
    Generate quotation from email request
    REUSES existing quotation_generator and product_matcher - NO DUPLICATION
    """
    logger.info(f"Starting email quotation pipeline for request {email_request_id}")

    try:
        from src.services.product_matcher import ProductMatcher
        from src.services.quotation_generator import QuotationGenerator

        product_matcher = ProductMatcher()
        quotation_generator = QuotationGenerator()

        # Match products (reuses existing service)
        matched_products = await product_matcher.match_products(
            requirements,
            api_instance.db_pool
        )

        if not matched_products:
            raise ValueError("No products matched from requirements")

        logger.info(f"Matched {len(matched_products)} products")

        # Calculate pricing (reuses existing service)
        pricing = await product_matcher.calculate_pricing(matched_products)

        logger.info(f"Calculated pricing: {pricing['currency']} {pricing['total']}")

        # Generate quotation (reuses existing service)
        quotation_id = await quotation_generator.generate_quotation(
            document_id,
            requirements,
            matched_products,
            pricing,
            api_instance.db_pool
        )

        logger.info(f"Created quotation ID {quotation_id}")

        # Generate PDF (reuses existing service)
        pdf_path = await quotation_generator.generate_pdf(
            quotation_id,
            api_instance.db_pool
        )

        logger.info(f"Generated PDF: {pdf_path}")

        # Update email request with quotation link
        async with api_instance.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE email_quotation_requests
                SET quotation_id = $1,
                    status = 'quotation_created',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, quotation_id, email_request_id)

        logger.info(f"✅ Email quotation pipeline complete: request={email_request_id}, quotation={quotation_id}")

    except Exception as e:
        logger.error(f"❌ Email quotation pipeline failed for request {email_request_id}: {str(e)}")
        async with api_instance.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE email_quotation_requests
                SET status = 'failed',
                    error_message = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, str(e), email_request_id)


async def reprocess_email_requirements(email_request_id: int):
    """Reprocess email request to extract requirements again"""
    logger.info(f"Reprocessing email request {email_request_id}")

    try:
        from src.services.email_processor import EmailProcessor

        email_processor = EmailProcessor()

        # Reprocess email
        await email_processor.process_email_request(
            email_request_id,
            api_instance.db_pool
        )

        logger.info(f"Email request {email_request_id} reprocessed successfully")

    except Exception as e:
        logger.error(f"Email request reprocessing failed: {str(e)}")
        async with api_instance.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE email_quotation_requests
                SET status = 'failed',
                    error_message = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, str(e), email_request_id)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("NEXUS_API_PORT", 8000))
    host = os.getenv("NEXUS_API_HOST", "0.0.0.0")

    uvicorn.run(
        "nexus_backend_api:app",
        host=host,
        port=port,
        reload=False,  # Set to False for production
        log_config=None,  # Use structlog
        access_log=False
    )