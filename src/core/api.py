"""
FastAPI Endpoints - Direct Database Integration
Production-ready API without SDK dependencies
Handles product search, RFP analysis, and work recommendations
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import traceback
from datetime import datetime
import os
import tempfile
import json

from .database import get_database, DatabaseConfig, close_database
from .business_logic import (
    get_search_engine, get_rfp_analyzer, get_recommendation_engine,
    SearchResult, RFPAnalysis, WorkRecommendation
)
from .auth import (
    User, UserRole, Permission, get_current_user, require_role, require_permission,
    auth_system, AuthMiddleware, rate_limiter
)

# Import document API router
try:
    from ..api.document_api import router as document_router
    DOCUMENT_API_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Document API not available: {e}")
    DOCUMENT_API_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class ProductSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    category: Optional[str] = Field(None, description="Filter by category")
    brand: Optional[str] = Field(None, description="Filter by brand")
    limit: int = Field(100, description="Maximum results", ge=1, le=500)

class ProductSearchResponse(BaseModel):
    products: List[Dict]
    total_results: int
    query: str
    execution_time_ms: float

class RFPAnalysisRequest(BaseModel):
    document_text: str = Field(..., description="RFP document text")
    document_id: Optional[str] = Field(None, description="Optional document ID")

class RFPAnalysisResponse(BaseModel):
    document_id: str
    work_type: str
    required_products: List[str]
    recommended_products: List[Dict]
    confidence_score: float
    analysis_summary: str
    created_at: str

class WorkRecommendationRequest(BaseModel):
    work_type: str = Field(..., description="Type of work (e.g., 'cement work', 'cleaning')")
    context: Optional[str] = Field(None, description="Additional context")

class WorkRecommendationResponse(BaseModel):
    work_type: str
    products: List[Dict]
    total_score: float
    reasoning: str

class HealthResponse(BaseModel):
    status: str
    database_status: str
    total_products: int
    version: str
    timestamp: str

class LoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    expires_in: int

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    role: UserRole = Field(UserRole.USER, description="User role")

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str]

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

# Create FastAPI app
app = FastAPI(
    title="Horme Product Management API",
    description="Direct database API for product search, RFP analysis, and work recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Authentication middleware
app.add_middleware(
    AuthMiddleware,
    excluded_paths=[
        "/", "/health", "/docs", "/redoc", "/openapi.json",
        "/api/v1/auth/login", "/api/v1/auth/register"
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Restrict origins in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include document API router if available
if DOCUMENT_API_AVAILABLE:
    app.include_router(document_router)
    logger.info("Document API router registered")

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        logger.info("Starting Horme Product API...")
        
        # Initialize database
        db = get_database()
        stats = db.get_statistics()
        logger.info(f"Database initialized with {stats.get('total_products', 0)} products")
        
        # Initialize business logic components
        get_search_engine()
        get_rfp_analyzer()
        get_recommendation_engine()
        
        logger.info("All components initialized successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        close_database()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# Authentication endpoints
@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """User login endpoint"""
    try:
        # Rate limiting
        client_ip = "unknown"  # In production, get real IP
        if not rate_limiter.is_allowed(f"login_{client_ip}"):
            raise HTTPException(status_code=429, detail="Too many login attempts")
        
        # Authenticate user
        user = auth_system.authenticate_user(request.username, request.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Generate tokens
        access_token = auth_system.create_access_token(user)
        refresh_token = auth_system.create_refresh_token(user)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "permissions": [p.value for p in user.permissions]
            },
            expires_in=auth_system.access_token_expire * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """User registration endpoint (Admin only)"""
    try:
        user = auth_system.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            role=request.role
        )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            last_login=user.last_login.isoformat() if user.last_login else None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/v1/auth/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token"""
    try:
        payload = auth_system.verify_token(request.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        username = payload.get("sub")
        user = auth_system.users.get(username)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        # Generate new access token
        access_token = auth_system.create_access_token(user)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": auth_system.access_token_expire * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None
    )

# Health check endpoint (Public)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        db = get_database()
        stats = db.get_statistics()
        
        return HealthResponse(
            status="healthy",
            database_status="connected",
            total_products=stats.get('total_products', 0),
            version="1.0.0",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            database_status="error",
            total_products=0,
            version="1.0.0",
            timestamp=datetime.now().isoformat()
        )

# Product search endpoints (Requires authentication)
@app.post("/api/v1/products/search", response_model=ProductSearchResponse)
async def search_products(
    request: ProductSearchRequest,
    current_user: User = Depends(require_permission(Permission.READ))
):
    """Search products with relevance scoring"""
    start_time = datetime.now()
    
    try:
        search_engine = get_search_engine()
        
        # Build filters
        filters = {}
        if request.category:
            filters['category'] = request.category
        if request.brand:
            filters['brand'] = request.brand
        
        # Perform search
        results = search_engine.search(
            query=request.query,
            filters=filters,
            limit=request.limit
        )
        
        # Convert results to API format
        products = []
        for result in results:
            product_data = result.product.copy()
            product_data['relevance_score'] = result.relevance_score
            product_data['match_reasons'] = result.match_reasons
            products.append(product_data)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ProductSearchResponse(
            products=products,
            total_results=len(products),
            query=request.query,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        logger.error(f"Product search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/products/{product_sku}")
async def get_product_by_sku(
    product_sku: str,
    current_user: User = Depends(require_permission(Permission.READ))
):
    """Get single product by SKU"""
    try:
        db = get_database()
        product = db.get_product_by_sku(product_sku)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {"product": product}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product {product_sku}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/products/categories")
async def get_categories(
    current_user: User = Depends(require_permission(Permission.READ))
):
    """Get all available product categories"""
    try:
        db = get_database()
        stats = db.get_statistics()
        
        categories = []
        for category, count in stats.get('by_category', {}).items():
            categories.append({
                "name": category,
                "product_count": count
            })
        
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/products/brands")
async def get_brands(
    current_user: User = Depends(require_permission(Permission.READ))
):
    """Get top product brands"""
    try:
        db = get_database()
        stats = db.get_statistics()
        
        brands = []
        for brand, count in stats.get('top_brands', {}).items():
            brands.append({
                "name": brand,
                "product_count": count
            })
        
        return {"brands": brands}
        
    except Exception as e:
        logger.error(f"Failed to get brands: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# RFP analysis endpoints (Requires API access)
@app.post("/api/v1/rfp/analyze", response_model=RFPAnalysisResponse)
async def analyze_rfp(
    request: RFPAnalysisRequest,
    current_user: User = Depends(require_permission(Permission.API_ACCESS))
):
    """Analyze RFP document and recommend products"""
    try:
        rfp_analyzer = get_rfp_analyzer()
        
        analysis = rfp_analyzer.analyze_rfp(
            document_text=request.document_text,
            document_id=request.document_id
        )
        
        # Convert to API format
        recommended_products = []
        for result in analysis.recommended_products:
            product_data = result.product.copy()
            product_data['relevance_score'] = result.relevance_score
            product_data['match_reasons'] = result.match_reasons
            recommended_products.append(product_data)
        
        return RFPAnalysisResponse(
            document_id=analysis.document_id,
            work_type=analysis.work_type,
            required_products=analysis.required_products,
            recommended_products=recommended_products,
            confidence_score=analysis.confidence_score,
            analysis_summary=analysis.analysis_summary,
            created_at=analysis.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"RFP analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/rfp/analyze/file")
async def analyze_rfp_file(
    file: UploadFile = File(...), 
    document_id: Optional[str] = Form(None),
    current_user: User = Depends(require_permission(Permission.API_ACCESS))
):
    """Analyze RFP from uploaded file"""
    try:
        # Read file content
        content = await file.read()
        
        # Handle different file types
        if file.filename.endswith('.txt'):
            document_text = content.decode('utf-8')
        elif file.filename.endswith('.pdf'):
            # For now, return error - PDF parsing would require additional dependencies
            raise HTTPException(
                status_code=400, 
                detail="PDF files not supported yet. Please upload text files."
            )
        else:
            # Try to decode as text
            try:
                document_text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file format. Please upload text files."
                )
        
        # Analyze document
        rfp_analyzer = get_rfp_analyzer()
        analysis = rfp_analyzer.analyze_rfp(
            document_text=document_text,
            document_id=document_id or file.filename
        )
        
        # Convert to API format
        recommended_products = []
        for result in analysis.recommended_products:
            product_data = result.product.copy()
            product_data['relevance_score'] = result.relevance_score
            product_data['match_reasons'] = result.match_reasons
            recommended_products.append(product_data)
        
        return RFPAnalysisResponse(
            document_id=analysis.document_id,
            work_type=analysis.work_type,
            required_products=analysis.required_products,
            recommended_products=recommended_products,
            confidence_score=analysis.confidence_score,
            analysis_summary=analysis.analysis_summary,
            created_at=analysis.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RFP file analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Work recommendation endpoints (Requires API access)
@app.post("/api/v1/recommendations/work", response_model=WorkRecommendationResponse)
async def get_work_recommendations(
    request: WorkRecommendationRequest,
    current_user: User = Depends(require_permission(Permission.API_ACCESS))
):
    """Get product recommendations for specific work type"""
    try:
        recommendation_engine = get_recommendation_engine()
        
        recommendations = recommendation_engine.get_recommendations(
            work_type=request.work_type,
            context=request.context
        )
        
        # Convert to API format
        products = []
        for result in recommendations.products:
            product_data = result.product.copy()
            product_data['relevance_score'] = result.relevance_score
            product_data['match_reasons'] = result.match_reasons
            products.append(product_data)
        
        return WorkRecommendationResponse(
            work_type=recommendations.work_type,
            products=products,
            total_score=recommendations.total_score,
            reasoning=recommendations.reasoning
        )
        
    except Exception as e:
        logger.error(f"Work recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/recommendations/work-types")
async def get_supported_work_types(
    current_user: User = Depends(require_permission(Permission.READ))
):
    """Get list of supported work types"""
    work_types = [
        {
            "name": "cement work",
            "description": "Tools and equipment for concrete and cement work",
            "examples": ["cement mixer", "trowel", "float", "vibrator"]
        },
        {
            "name": "cleaning",
            "description": "Cleaning products and supplies",
            "examples": ["detergent", "disinfectant", "sanitizer", "cleaning cloths"]
        },
        {
            "name": "safety",
            "description": "Personal protective equipment and safety gear",
            "examples": ["helmet", "gloves", "safety vest", "goggles"]
        },
        {
            "name": "tools",
            "description": "General tools and equipment",
            "examples": ["drill", "hammer", "saw", "wrench"]
        },
        {
            "name": "construction",
            "description": "Construction materials and equipment",
            "examples": ["scaffold", "building materials", "construction tools"]
        },
        {
            "name": "maintenance",
            "description": "Maintenance and repair supplies",
            "examples": ["lubricants", "sealants", "repair tools"]
        }
    ]
    
    return {"work_types": work_types}

# Statistics and admin endpoints (Admin only)
@app.get("/api/v1/admin/statistics")
async def get_database_statistics(
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Get detailed database statistics"""
    try:
        db = get_database()
        stats = db.get_statistics()
        
        return {
            "database_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/admin/import-products")
async def import_products(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Import products from Excel file (background task)"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Start background import
        background_tasks.add_task(perform_import, tmp_file_path)
        
        return {
            "message": "Import started in background",
            "status": "processing",
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Import initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def perform_import(file_path: str):
    """Background task to import products"""
    try:
        logger.info(f"Starting product import from {file_path}")
        db = get_database()
        success = db.import_products_from_excel(file_path)
        
        if success:
            logger.info("Product import completed successfully")
        else:
            logger.error("Product import failed")
            
    except Exception as e:
        logger.error(f"Background import failed: {e}")
    finally:
        # Clean up temporary file
        try:
            os.unlink(file_path)
        except:
            pass

# Test endpoints for development (Read access)
@app.get("/api/v1/test/sample-products")
async def get_sample_products(
    current_user: User = Depends(require_permission(Permission.READ))
):
    """Get sample products for testing"""
    try:
        db = get_database()
        products = db.search_products("", limit=10)
        return {"sample_products": products}
        
    except Exception as e:
        logger.error(f"Failed to get sample products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/test/search")
async def test_search(
    query: str = "drill",
    current_user: User = Depends(require_permission(Permission.READ))
):
    """Test search functionality"""
    try:
        search_engine = get_search_engine()
        results = search_engine.search(query, limit=5)
        
        products = []
        for result in results:
            product_data = result.product.copy()
            product_data['relevance_score'] = result.relevance_score
            product_data['match_reasons'] = result.match_reasons
            products.append(product_data)
        
        return {
            "test_query": query,
            "results": products,
            "count": len(products)
        }
        
    except Exception as e:
        logger.error(f"Test search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.core.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )