#!/usr/bin/env python3
"""
Scraping System API Endpoints
============================

FastAPI-based REST API for the production web scraping system.
Provides endpoints for supplier discovery, product scraping, and data enrichment.

Features:
- RESTful API for scraping operations
- Async processing for large scraping jobs
- Real-time progress tracking
- Data validation and error handling
- Rate limiting and authentication
- Database integration
- Docker container support
"""

import os
import uuid
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from concurrent.futures import ThreadPoolExecutor
import traceback

# FastAPI and async components
try:
    from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Query, Path
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from pydantic import BaseModel, Field, validator
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Database
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Import scraping components
from .production_scraper import ProductionScraper, ProductData, SupplierInfo, ScrapingConfig
from .horme_scraper import HormeScraper
from .supplier_discovery import SupplierDiscovery, DiscoveryConfig
from .product_enrichment import ProductEnrichmentPipeline, EnrichmentConfig, EnrichmentResult


# Pydantic models for API requests/responses
class ScrapingJobRequest(BaseModel):
    """Request model for scraping jobs."""
    job_type: str = Field(..., description="Type of scraping job")
    parameters: Dict[str, Any] = Field(default={}, description="Job-specific parameters")
    priority: int = Field(default=1, description="Job priority (1-5, 5 being highest)")
    callback_url: Optional[str] = Field(None, description="Optional callback URL for job completion")


class ProductSearchRequest(BaseModel):
    """Request model for product search."""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    max_results: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    supplier: Optional[str] = Field(None, description="Specific supplier to search")


class SupplierDiscoveryRequest(BaseModel):
    """Request model for supplier discovery."""
    industry: str = Field(..., description="Industry category to discover suppliers for")
    location: str = Field(default="Singapore", description="Geographic location")
    max_suppliers: int = Field(default=50, ge=1, le=200, description="Maximum number of suppliers")


class ProductEnrichmentRequest(BaseModel):
    """Request model for product enrichment."""
    product_skus: List[str] = Field(..., description="List of product SKUs to enrich")
    enrichment_options: Dict[str, bool] = Field(
        default={
            "ai_classification": True,
            "image_analysis": True,
            "specification_extraction": True
        },
        description="Enrichment options"
    )


class JobStatus(BaseModel):
    """Job status response model."""
    job_id: str
    status: str  # pending, running, completed, failed
    progress: float = Field(ge=0.0, le=100.0)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ProductResponse(BaseModel):
    """Product data response model."""
    sku: str
    name: str
    price: str
    currency: str = "SGD"
    description: str
    specifications: Dict[str, str]
    images: List[str]
    categories: List[str]
    availability: str
    brand: str
    supplier: str
    url: str
    scraped_at: datetime
    data_quality_score: float


class SupplierResponse(BaseModel):
    """Supplier information response model."""
    name: str
    domain: str
    url: str
    contact_info: Dict[str, str]
    categories: List[str]
    location: str
    verified: bool
    product_count: int


# Job management system
class JobManager:
    """Manages background scraping jobs."""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.logger = logging.getLogger("job_manager")
    
    def create_job(self, job_type: str, parameters: Dict[str, Any], priority: int = 1) -> str:
        """Create a new scraping job."""
        job_id = str(uuid.uuid4())
        
        self.jobs[job_id] = {
            'job_id': job_id,
            'job_type': job_type,
            'parameters': parameters,
            'priority': priority,
            'status': 'pending',
            'progress': 0.0,
            'created_at': datetime.now(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error_message': None
        }
        
        self.logger.info(f"Created job {job_id}: {job_type}")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job."""
        return self.jobs.get(job_id)
    
    def update_job_progress(self, job_id: str, progress: float, status: str = None):
        """Update job progress."""
        if job_id in self.jobs:
            self.jobs[job_id]['progress'] = progress
            if status:
                self.jobs[job_id]['status'] = status
    
    def complete_job(self, job_id: str, result: Any, error: str = None):
        """Mark job as completed."""
        if job_id in self.jobs:
            self.jobs[job_id]['completed_at'] = datetime.now()
            if error:
                self.jobs[job_id]['status'] = 'failed'
                self.jobs[job_id]['error_message'] = error
            else:
                self.jobs[job_id]['status'] = 'completed'
                self.jobs[job_id]['result'] = result
                self.jobs[job_id]['progress'] = 100.0


# Initialize FastAPI app
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Production Web Scraping API",
        description="Advanced web scraping system for industrial suppliers and product data",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security
    security = HTTPBearer(optional=True)
    
    # Global components
    job_manager = JobManager()
    
    # Initialize scraping components
    scraping_config = ScrapingConfig(
        browser_type="headless_chrome",
        rate_limit_seconds=2.0,
        simulate_human_behavior=True,
        save_to_database=True
    )
    
    production_scraper = ProductionScraper(scraping_config)
    horme_scraper = HormeScraper(scraping_config)
    
    discovery_config = DiscoveryConfig()
    supplier_discovery = SupplierDiscovery(discovery_config)
    
    enrichment_config = EnrichmentConfig()
    enrichment_pipeline = ProductEnrichmentPipeline(enrichment_config)


    def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Simple authentication check - extend as needed."""
        # In production, implement proper JWT token validation
        if credentials and credentials.credentials == "your-api-key":
            return {"user_id": "authenticated_user"}
        return {"user_id": "anonymous"}


    @app.get("/", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "version": "1.0.0",
            "components": {
                "production_scraper": "active",
                "horme_scraper": "active", 
                "supplier_discovery": "active",
                "enrichment_pipeline": "active",
                "database": "connected" if POSTGRES_AVAILABLE else "disabled"
            }
        }


    @app.post("/scraping/search-products", response_model=Dict[str, Any], tags=["Product Scraping"])
    async def search_products(
        request: ProductSearchRequest,
        background_tasks: BackgroundTasks,
        user: dict = Depends(get_current_user)
    ):
        """
        Search for products across configured suppliers.
        
        Returns product URLs and basic information.
        """
        try:
            # Create background job for large searches
            if request.max_results > 10:
                job_id = job_manager.create_job(
                    "product_search",
                    {
                        "query": request.query,
                        "max_results": request.max_results,
                        "supplier": request.supplier
                    }
                )
                
                background_tasks.add_task(execute_product_search_job, job_id, request)
                
                return {
                    "job_id": job_id,
                    "status": "started",
                    "message": f"Product search job started for query: '{request.query}'"
                }
            
            # Execute immediately for small searches
            if request.supplier == "horme" or not request.supplier:
                results = horme_scraper.search_products(request.query, request.max_results)
            else:
                # Could extend to other suppliers here
                results = []
            
            return {
                "query": request.query,
                "total_results": len(results),
                "product_urls": results,
                "execution_time": "immediate"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Product search failed: {str(e)}")


    @app.post("/scraping/scrape-product", response_model=ProductResponse, tags=["Product Scraping"])
    async def scrape_single_product(
        url: str = Query(..., description="Product URL to scrape"),
        enrich: bool = Query(default=False, description="Apply enrichment pipeline"),
        user: dict = Depends(get_current_user)
    ):
        """
        Scrape a single product from its URL.
        
        Optionally applies enrichment pipeline for enhanced data quality.
        """
        try:
            # Determine which scraper to use based on URL
            if "horme.com.sg" in url:
                product = horme_scraper.scrape_product(url)
            else:
                # Use general production scraper
                def extract_product_data(content, url):
                    # Generic product extraction logic
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract basic information
                    title = soup.find('title')
                    name = title.text if title else ""
                    
                    return ProductData(
                        sku=url.split('/')[-1],  # Simple SKU from URL
                        name=name,
                        url=url,
                        supplier="Unknown"
                    )
                
                product = production_scraper.scrape_with_requests(url, extract_product_data)
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found or scraping failed")
            
            # Apply enrichment if requested
            if enrich:
                enrichment_result = enrichment_pipeline.enrich_product(product)
                product = enrichment_result.enriched_product
            
            # Save to database if configured
            if production_scraper.config.save_to_database:
                production_scraper.save_product_to_database(product)
            
            return ProductResponse(
                sku=product.sku,
                name=product.name,
                price=product.price,
                currency=product.currency,
                description=product.description,
                specifications=product.specifications,
                images=product.images,
                categories=product.categories,
                availability=product.availability,
                brand=product.brand,
                supplier=product.supplier,
                url=product.url,
                scraped_at=product.scraped_at,
                data_quality_score=product.data_quality_score
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Product scraping failed: {str(e)}")


    @app.post("/scraping/discover-suppliers", response_model=Dict[str, Any], tags=["Supplier Discovery"])
    async def discover_suppliers(
        request: SupplierDiscoveryRequest,
        background_tasks: BackgroundTasks,
        user: dict = Depends(get_current_user)
    ):
        """
        Discover suppliers in a specific industry and location.
        
        Returns a job ID for tracking the discovery process.
        """
        try:
            job_id = job_manager.create_job(
                "supplier_discovery",
                {
                    "industry": request.industry,
                    "location": request.location,
                    "max_suppliers": request.max_suppliers
                }
            )
            
            background_tasks.add_task(execute_supplier_discovery_job, job_id, request)
            
            return {
                "job_id": job_id,
                "status": "started",
                "message": f"Supplier discovery started for industry: {request.industry}",
                "estimated_duration": "5-15 minutes"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Supplier discovery failed: {str(e)}")


    @app.post("/enrichment/enrich-products", response_model=Dict[str, Any], tags=["Data Enrichment"])
    async def enrich_products(
        request: ProductEnrichmentRequest,
        background_tasks: BackgroundTasks,
        user: dict = Depends(get_current_user)
    ):
        """
        Enrich product data using AI and machine learning.
        
        Improves data quality, extracts specifications, and classifies products.
        """
        try:
            job_id = job_manager.create_job(
                "product_enrichment",
                {
                    "product_skus": request.product_skus,
                    "enrichment_options": request.enrichment_options
                }
            )
            
            background_tasks.add_task(execute_product_enrichment_job, job_id, request)
            
            return {
                "job_id": job_id,
                "status": "started",
                "message": f"Product enrichment started for {len(request.product_skus)} products",
                "estimated_duration": f"{len(request.product_skus) * 2} seconds"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Product enrichment failed: {str(e)}")


    @app.get("/jobs/{job_id}", response_model=JobStatus, tags=["Job Management"])
    async def get_job_status(
        job_id: str = Path(..., description="Job ID to check status"),
        user: dict = Depends(get_current_user)
    ):
        """
        Get the status and progress of a background job.
        """
        job = job_manager.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatus(**job)


    @app.get("/jobs", response_model=List[JobStatus], tags=["Job Management"])
    async def list_jobs(
        status: Optional[str] = Query(None, description="Filter by job status"),
        limit: int = Query(default=50, le=100, description="Maximum number of jobs to return"),
        user: dict = Depends(get_current_user)
    ):
        """
        List recent jobs with optional status filtering.
        """
        jobs = list(job_manager.jobs.values())
        
        # Filter by status if provided
        if status:
            jobs = [job for job in jobs if job['status'] == status]
        
        # Sort by creation date (newest first)
        jobs.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Apply limit
        jobs = jobs[:limit]
        
        return [JobStatus(**job) for job in jobs]


    @app.get("/suppliers", response_model=List[SupplierResponse], tags=["Supplier Management"])
    async def list_suppliers(
        category: Optional[str] = Query(None, description="Filter by category"),
        verified_only: bool = Query(default=False, description="Return only verified suppliers"),
        limit: int = Query(default=50, le=200, description="Maximum number of suppliers"),
        user: dict = Depends(get_current_user)
    ):
        """
        List discovered suppliers with optional filtering.
        """
        if not POSTGRES_AVAILABLE or not production_scraper.db_connection:
            raise HTTPException(status_code=503, detail="Database not available")
        
        try:
            with production_scraper.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM suppliers WHERE 1=1"
                params = []
                
                if category:
                    query += " AND categories::text ILIKE %s"
                    params.append(f"%{category}%")
                
                if verified_only:
                    query += " AND verified = true"
                
                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(query, params)
                suppliers = cursor.fetchall()
                
                return [
                    SupplierResponse(
                        name=s['name'],
                        domain=s['domain'],
                        url=s['url'] or '',
                        contact_info=s['contact_info'] or {},
                        categories=s['categories'] or [],
                        location=s['location'] or '',
                        verified=s['verified'],
                        product_count=s['product_count']
                    )
                    for s in suppliers
                ]
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")


    @app.get("/products", response_model=List[ProductResponse], tags=["Product Management"])
    async def list_products(
        supplier: Optional[str] = Query(None, description="Filter by supplier"),
        category: Optional[str] = Query(None, description="Filter by category"),
        min_quality: float = Query(default=0.0, ge=0.0, le=1.0, description="Minimum quality score"),
        limit: int = Query(default=50, le=200, description="Maximum number of products"),
        user: dict = Depends(get_current_user)
    ):
        """
        List scraped products with optional filtering.
        """
        if not POSTGRES_AVAILABLE or not production_scraper.db_connection:
            raise HTTPException(status_code=503, detail="Database not available")
        
        try:
            with production_scraper.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM scraped_products WHERE data_quality_score >= %s"
                params = [min_quality]
                
                if supplier:
                    query += " AND supplier ILIKE %s"
                    params.append(f"%{supplier}%")
                
                if category:
                    query += " AND categories::text ILIKE %s"
                    params.append(f"%{category}%")
                
                query += " ORDER BY scraped_at DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(query, params)
                products = cursor.fetchall()
                
                return [
                    ProductResponse(
                        sku=p['sku'],
                        name=p['name'] or '',
                        price=p['price'] or '',
                        currency=p['currency'] or 'SGD',
                        description=p['description'] or '',
                        specifications=p['specifications'] or {},
                        images=p['images'] or [],
                        categories=p['categories'] or [],
                        availability=p['availability'] or '',
                        brand=p['brand'] or '',
                        supplier=p['supplier'] or '',
                        url=p['url'] or '',
                        scraped_at=p['scraped_at'],
                        data_quality_score=p['data_quality_score'] or 0.0
                    )
                    for p in products
                ]
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")


    # Background job execution functions
    async def execute_product_search_job(job_id: str, request: ProductSearchRequest):
        """Execute product search job in background."""
        try:
            job_manager.update_job_progress(job_id, 10.0, "running")
            
            # Execute search
            if request.supplier == "horme" or not request.supplier:
                results = horme_scraper.search_products(request.query, request.max_results)
            else:
                results = []
            
            job_manager.update_job_progress(job_id, 100.0)
            job_manager.complete_job(job_id, {
                "query": request.query,
                "total_results": len(results),
                "product_urls": results
            })
            
        except Exception as e:
            job_manager.complete_job(job_id, None, str(e))


    async def execute_supplier_discovery_job(job_id: str, request: SupplierDiscoveryRequest):
        """Execute supplier discovery job in background."""
        try:
            job_manager.update_job_progress(job_id, 10.0, "running")
            
            # Execute discovery
            suppliers = supplier_discovery.discover_suppliers_by_industry(request.industry)
            
            job_manager.update_job_progress(job_id, 80.0)
            
            # Format results
            supplier_data = [
                {
                    "name": s.name,
                    "domain": s.domain,
                    "url": s.url,
                    "categories": s.categories,
                    "location": s.location,
                    "verified": s.verified
                }
                for s in suppliers
            ]
            
            job_manager.complete_job(job_id, {
                "industry": request.industry,
                "total_suppliers": len(suppliers),
                "suppliers": supplier_data
            })
            
        except Exception as e:
            job_manager.complete_job(job_id, None, str(e))


    async def execute_product_enrichment_job(job_id: str, request: ProductEnrichmentRequest):
        """Execute product enrichment job in background."""
        try:
            job_manager.update_job_progress(job_id, 10.0, "running")
            
            # Load products from database
            products = []
            if POSTGRES_AVAILABLE and production_scraper.db_connection:
                with production_scraper.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM scraped_products WHERE sku = ANY(%s)",
                        (request.product_skus,)
                    )
                    db_products = cursor.fetchall()
                    
                    for p in db_products:
                        product = ProductData(
                            sku=p['sku'],
                            name=p['name'] or '',
                            price=p['price'] or '',
                            currency=p['currency'] or 'SGD',
                            description=p['description'] or '',
                            specifications=p['specifications'] or {},
                            images=p['images'] or [],
                            categories=p['categories'] or [],
                            availability=p['availability'] or '',
                            brand=p['brand'] or '',
                            supplier=p['supplier'] or '',
                            url=p['url'] or '',
                            scraped_at=p['scraped_at']
                        )
                        products.append(product)
            
            job_manager.update_job_progress(job_id, 30.0)
            
            if not products:
                job_manager.complete_job(job_id, None, "No products found for given SKUs")
                return
            
            # Apply enrichment
            results = enrichment_pipeline.enrich_products_batch(products)
            
            job_manager.update_job_progress(job_id, 90.0)
            
            # Format results
            enrichment_data = [
                {
                    "sku": r.enriched_product.sku,
                    "enrichment_score": r.enrichment_score,
                    "quality_improvements": r.quality_improvements,
                    "processing_time": r.processing_time
                }
                for r in results
            ]
            
            job_manager.complete_job(job_id, {
                "total_products": len(results),
                "average_enrichment_score": sum(r.enrichment_score for r in results) / len(results),
                "enrichment_results": enrichment_data
            })
            
        except Exception as e:
            job_manager.complete_job(job_id, None, str(e))


    if __name__ == "__main__":
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Run the API server
        uvicorn.run(
            "scraping_api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )

else:
    # Fallback when FastAPI is not available
    print("FastAPI not available. Install with: pip install fastapi uvicorn")
    
    def create_flask_app():
        """Create a simple Flask app as fallback."""
        try:
            from flask import Flask, jsonify, request
            
            app = Flask(__name__)
            
            @app.route('/', methods=['GET'])
            def health_check():
                return jsonify({
                    "status": "healthy",
                    "message": "Scraping API (Flask fallback)",
                    "timestamp": datetime.now().isoformat()
                })
            
            @app.route('/api/search-products', methods=['POST'])
            def search_products():
                data = request.get_json()
                query = data.get('query', '')
                
                # Simple response
                return jsonify({
                    "query": query,
                    "message": "FastAPI recommended for full functionality",
                    "results": []
                })
            
            return app
            
        except ImportError:
            return None
    
    # Try to create Flask fallback
    flask_app = create_flask_app()
    
    if flask_app and __name__ == "__main__":
        flask_app.run(host="0.0.0.0", port=8000, debug=True)