"""
Enrichment API
Real-time supplier/brand enrichment APIs for AI processing
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
import asyncio
import logging

from src.workflows.supplier_enrichment_workflows import SupplierEnrichmentWorkflows
from src.models.production_models import db
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Horme Enrichment API",
    description="Real-time supplier/brand intelligence enrichment for AI processing",
    version="1.0.0"
)

# Initialize workflows
enrichment_workflows = SupplierEnrichmentWorkflows()

# Pydantic models for API requests/responses

class EnrichmentRequest(BaseModel):
    """Base enrichment request"""
    priority: str = Field(default="normal", description="Priority: low, normal, high, urgent")
    force_refresh: bool = Field(default=False, description="Force refresh even if recent data exists")
    data_sources: Optional[List[str]] = Field(default=None, description="Specific data sources to use")

class SupplierEnrichmentRequest(EnrichmentRequest):
    """Supplier enrichment request"""
    supplier_id: int = Field(description="Supplier ID to enrich")
    enrichment_scope: str = Field(default="full", description="Scope: basic, full, comprehensive")
    include_performance_metrics: bool = Field(default=True, description="Include performance metrics")

class BrandEnrichmentRequest(EnrichmentRequest):
    """Brand enrichment request"""
    brand_id: int = Field(description="Brand ID to enrich")
    include_market_intelligence: bool = Field(default=True, description="Include market intelligence")
    include_competitive_analysis: bool = Field(default=True, description="Include competitive analysis")

class ProductEnrichmentRequest(EnrichmentRequest):
    """Product enrichment request"""
    product_id: int = Field(description="Product ID to enrich")
    include_compatibility_matrix: bool = Field(default=True, description="Include compatibility matrix")
    include_use_case_analysis: bool = Field(default=True, description="Include use case analysis")

class MarketIntelligenceRequest(EnrichmentRequest):
    """Market intelligence request"""
    product_id: int = Field(description="Product ID")
    supplier_id: int = Field(description="Supplier ID")
    include_pricing_optimization: bool = Field(default=True, description="Include pricing optimization")
    include_demand_forecasting: bool = Field(default=True, description="Include demand forecasting")

class BulkEnrichmentRequest(BaseModel):
    """Bulk enrichment request"""
    enrichment_type: str = Field(description="Type: supplier, brand, product, market")
    entity_ids: List[int] = Field(description="List of entity IDs to enrich")
    batch_size: int = Field(default=10, description="Batch processing size")
    max_concurrent: int = Field(default=3, description="Maximum concurrent jobs")
    priority: str = Field(default="normal", description="Priority: low, normal, high, urgent")

class EnrichmentResponse(BaseModel):
    """Enrichment response"""
    success: bool
    message: str
    enrichment_id: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None

class EnrichmentStatus(BaseModel):
    """Enrichment status"""
    enrichment_id: str
    status: str  # queued, processing, completed, failed
    progress_percentage: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None

# In-memory job tracking (in production, use Redis or database)
enrichment_jobs = {}

# API Endpoints

@app.post("/api/v1/enrichment/supplier", response_model=EnrichmentResponse)
async def enrich_supplier(
    request: SupplierEnrichmentRequest,
    background_tasks: BackgroundTasks
):
    """
    Enrich supplier profile with comprehensive business intelligence
    """
    try:
        # Check if supplier exists
        workflow = WorkflowBuilder()
        workflow.add_node("SupplierReadNode", "check_supplier", {
            "id": request.supplier_id
        })
        
        runtime = LocalRuntime()
        results, _ = runtime.execute(workflow.build())
        
        if not results.get("check_supplier"):
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Generate enrichment ID
        enrichment_id = f"supplier_{request.supplier_id}_{datetime.now().timestamp()}"
        
        # Add to job tracking
        enrichment_jobs[enrichment_id] = {
            "status": "queued",
            "type": "supplier",
            "entity_id": request.supplier_id,
            "progress_percentage": 0.0,
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "results": None
        }
        
        # Execute enrichment in background
        background_tasks.add_task(
            execute_supplier_enrichment,
            enrichment_id,
            request.supplier_id,
            request
        )
        
        return EnrichmentResponse(
            success=True,
            message="Supplier enrichment started",
            enrichment_id=enrichment_id,
            estimated_completion=datetime.now().replace(hour=datetime.now().hour + 1)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting supplier enrichment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/v1/enrichment/brand", response_model=EnrichmentResponse)
async def enrich_brand(
    request: BrandEnrichmentRequest,
    background_tasks: BackgroundTasks
):
    """
    Enrich brand intelligence with market position and competitive analysis
    """
    try:
        # Check if brand exists
        workflow = WorkflowBuilder()
        workflow.add_node("BrandReadNode", "check_brand", {
            "id": request.brand_id
        })
        
        runtime = LocalRuntime()
        results, _ = runtime.execute(workflow.build())
        
        if not results.get("check_brand"):
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Generate enrichment ID
        enrichment_id = f"brand_{request.brand_id}_{datetime.now().timestamp()}"
        
        # Add to job tracking
        enrichment_jobs[enrichment_id] = {
            "status": "queued",
            "type": "brand",
            "entity_id": request.brand_id,
            "progress_percentage": 0.0,
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "results": None
        }
        
        # Execute enrichment in background
        background_tasks.add_task(
            execute_brand_enrichment,
            enrichment_id,
            request.brand_id,
            request
        )
        
        return EnrichmentResponse(
            success=True,
            message="Brand enrichment started",
            enrichment_id=enrichment_id,
            estimated_completion=datetime.now().replace(hour=datetime.now().hour + 1)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting brand enrichment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/v1/enrichment/product", response_model=EnrichmentResponse)
async def enrich_product(
    request: ProductEnrichmentRequest,
    background_tasks: BackgroundTasks
):
    """
    Enrich product intelligence with AI context and compatibility data
    """
    try:
        # Check if product exists
        workflow = WorkflowBuilder()
        workflow.add_node("ProductReadNode", "check_product", {
            "id": request.product_id
        })
        
        runtime = LocalRuntime()
        results, _ = runtime.execute(workflow.build())
        
        if not results.get("check_product"):
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Generate enrichment ID
        enrichment_id = f"product_{request.product_id}_{datetime.now().timestamp()}"
        
        # Add to job tracking
        enrichment_jobs[enrichment_id] = {
            "status": "queued",
            "type": "product",
            "entity_id": request.product_id,
            "progress_percentage": 0.0,
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "results": None
        }
        
        # Execute enrichment in background
        background_tasks.add_task(
            execute_product_enrichment,
            enrichment_id,
            request.product_id,
            request
        )
        
        return EnrichmentResponse(
            success=True,
            message="Product enrichment started",
            enrichment_id=enrichment_id,
            estimated_completion=datetime.now().replace(hour=datetime.now().hour + 1)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting product enrichment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/v1/enrichment/market", response_model=EnrichmentResponse)
async def enrich_market_intelligence(
    request: MarketIntelligenceRequest,
    background_tasks: BackgroundTasks
):
    """
    Enrich market intelligence with real-time pricing and demand data
    """
    try:
        # Check if product and supplier exist
        workflow = WorkflowBuilder()
        workflow.add_node("ProductReadNode", "check_product", {
            "id": request.product_id
        })
        workflow.add_node("SupplierReadNode", "check_supplier", {
            "id": request.supplier_id
        })
        
        runtime = LocalRuntime()
        results, _ = runtime.execute(workflow.build())
        
        if not results.get("check_product"):
            raise HTTPException(status_code=404, detail="Product not found")
        if not results.get("check_supplier"):
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Generate enrichment ID
        enrichment_id = f"market_{request.product_id}_{request.supplier_id}_{datetime.now().timestamp()}"
        
        # Add to job tracking
        enrichment_jobs[enrichment_id] = {
            "status": "queued",
            "type": "market",
            "entity_id": f"{request.product_id}_{request.supplier_id}",
            "progress_percentage": 0.0,
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "results": None
        }
        
        # Execute enrichment in background
        background_tasks.add_task(
            execute_market_enrichment,
            enrichment_id,
            request.product_id,
            request.supplier_id,
            request
        )
        
        return EnrichmentResponse(
            success=True,
            message="Market intelligence enrichment started",
            enrichment_id=enrichment_id,
            estimated_completion=datetime.now().replace(minute=datetime.now().minute + 30)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting market enrichment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/v1/enrichment/bulk", response_model=EnrichmentResponse)
async def bulk_enrichment(
    request: BulkEnrichmentRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute bulk enrichment for multiple entities
    """
    try:
        if len(request.entity_ids) == 0:
            raise HTTPException(status_code=400, detail="No entity IDs provided")
        
        if len(request.entity_ids) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 entities per bulk request")
        
        # Generate enrichment ID
        enrichment_id = f"bulk_{request.enrichment_type}_{datetime.now().timestamp()}"
        
        # Add to job tracking
        enrichment_jobs[enrichment_id] = {
            "status": "queued",
            "type": f"bulk_{request.enrichment_type}",
            "entity_id": f"{len(request.entity_ids)}_entities",
            "progress_percentage": 0.0,
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "results": None,
            "total_entities": len(request.entity_ids),
            "completed_entities": 0
        }
        
        # Execute bulk enrichment in background
        background_tasks.add_task(
            execute_bulk_enrichment,
            enrichment_id,
            request
        )
        
        estimated_time_hours = max(1, len(request.entity_ids) // request.max_concurrent)
        estimated_completion = datetime.now().replace(hour=datetime.now().hour + estimated_time_hours)
        
        return EnrichmentResponse(
            success=True,
            message=f"Bulk {request.enrichment_type} enrichment started for {len(request.entity_ids)} entities",
            enrichment_id=enrichment_id,
            estimated_completion=estimated_completion
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting bulk enrichment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/enrichment/status/{enrichment_id}", response_model=EnrichmentStatus)
async def get_enrichment_status(enrichment_id: str):
    """
    Get status of an enrichment job
    """
    if enrichment_id not in enrichment_jobs:
        raise HTTPException(status_code=404, detail="Enrichment job not found")
    
    job = enrichment_jobs[enrichment_id]
    
    return EnrichmentStatus(
        enrichment_id=enrichment_id,
        status=job["status"],
        progress_percentage=job["progress_percentage"],
        started_at=job["started_at"],
        completed_at=job["completed_at"],
        error_message=job["error_message"],
        results=job["results"]
    )

@app.get("/api/v1/enrichment/jobs")
async def get_active_jobs():
    """
    Get list of all enrichment jobs
    """
    return {
        "active_jobs": len([j for j in enrichment_jobs.values() if j["status"] in ["queued", "processing"]]),
        "completed_jobs": len([j for j in enrichment_jobs.values() if j["status"] == "completed"]),
        "failed_jobs": len([j for j in enrichment_jobs.values() if j["status"] == "failed"]),
        "jobs": {
            job_id: {
                "status": job["status"],
                "type": job["type"],
                "progress_percentage": job["progress_percentage"],
                "started_at": job["started_at"],
                "completed_at": job["completed_at"]
            }
            for job_id, job in enrichment_jobs.items()
        }
    }

@app.delete("/api/v1/enrichment/jobs/{enrichment_id}")
async def cancel_enrichment_job(enrichment_id: str):
    """
    Cancel an enrichment job (if not completed)
    """
    if enrichment_id not in enrichment_jobs:
        raise HTTPException(status_code=404, detail="Enrichment job not found")
    
    job = enrichment_jobs[enrichment_id]
    
    if job["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed or failed job")
    
    # In a real implementation, you would cancel the background task
    job["status"] = "cancelled"
    job["completed_at"] = datetime.now()
    
    return {"message": f"Enrichment job {enrichment_id} cancelled"}

# Background task functions

async def execute_supplier_enrichment(enrichment_id: str, supplier_id: int, request: SupplierEnrichmentRequest):
    """Execute supplier enrichment in background"""
    try:
        enrichment_jobs[enrichment_id]["status"] = "processing"
        enrichment_jobs[enrichment_id]["started_at"] = datetime.now()
        enrichment_jobs[enrichment_id]["progress_percentage"] = 10.0
        
        # Execute the enrichment workflow
        result = enrichment_workflows.run_supplier_enrichment(supplier_id)
        
        enrichment_jobs[enrichment_id]["progress_percentage"] = 100.0
        
        if result["success"]:
            enrichment_jobs[enrichment_id]["status"] = "completed"
            enrichment_jobs[enrichment_id]["results"] = result
        else:
            enrichment_jobs[enrichment_id]["status"] = "failed"
            enrichment_jobs[enrichment_id]["error_message"] = result.get("error", "Unknown error")
        
        enrichment_jobs[enrichment_id]["completed_at"] = datetime.now()
        
    except Exception as e:
        enrichment_jobs[enrichment_id]["status"] = "failed"
        enrichment_jobs[enrichment_id]["error_message"] = str(e)
        enrichment_jobs[enrichment_id]["completed_at"] = datetime.now()
        logger.error(f"Supplier enrichment failed for ID {supplier_id}: {str(e)}")

async def execute_brand_enrichment(enrichment_id: str, brand_id: int, request: BrandEnrichmentRequest):
    """Execute brand enrichment in background"""
    try:
        enrichment_jobs[enrichment_id]["status"] = "processing"
        enrichment_jobs[enrichment_id]["started_at"] = datetime.now()
        enrichment_jobs[enrichment_id]["progress_percentage"] = 10.0
        
        # Execute the enrichment workflow
        result = enrichment_workflows.run_brand_intelligence(brand_id)
        
        enrichment_jobs[enrichment_id]["progress_percentage"] = 100.0
        
        if result["success"]:
            enrichment_jobs[enrichment_id]["status"] = "completed"
            enrichment_jobs[enrichment_id]["results"] = result
        else:
            enrichment_jobs[enrichment_id]["status"] = "failed"
            enrichment_jobs[enrichment_id]["error_message"] = result.get("error", "Unknown error")
        
        enrichment_jobs[enrichment_id]["completed_at"] = datetime.now()
        
    except Exception as e:
        enrichment_jobs[enrichment_id]["status"] = "failed"
        enrichment_jobs[enrichment_id]["error_message"] = str(e)
        enrichment_jobs[enrichment_id]["completed_at"] = datetime.now()
        logger.error(f"Brand enrichment failed for ID {brand_id}: {str(e)}")

async def execute_product_enrichment(enrichment_id: str, product_id: int, request: ProductEnrichmentRequest):
    """Execute product enrichment in background"""
    try:
        enrichment_jobs[enrichment_id]["status"] = "processing"
        enrichment_jobs[enrichment_id]["started_at"] = datetime.now()
        enrichment_jobs[enrichment_id]["progress_percentage"] = 10.0
        
        # Execute the enrichment workflow
        result = enrichment_workflows.run_product_intelligence(product_id)
        
        enrichment_jobs[enrichment_id]["progress_percentage"] = 100.0
        
        if result["success"]:
            enrichment_jobs[enrichment_id]["status"] = "completed"
            enrichment_jobs[enrichment_id]["results"] = result
        else:
            enrichment_jobs[enrichment_id]["status"] = "failed"
            enrichment_jobs[enrichment_id]["error_message"] = result.get("error", "Unknown error")
        
        enrichment_jobs[enrichment_id]["completed_at"] = datetime.now()
        
    except Exception as e:
        enrichment_jobs[enrichment_id]["status"] = "failed"
        enrichment_jobs[enrichment_id]["error_message"] = str(e)
        enrichment_jobs[enrichment_id]["completed_at"] = datetime.now()
        logger.error(f"Product enrichment failed for ID {product_id}: {str(e)}")

async def execute_market_enrichment(enrichment_id: str, product_id: int, supplier_id: int, request: MarketIntelligenceRequest):
    """Execute market intelligence enrichment in background"""
    try:
        enrichment_jobs[enrichment_id]["status"] = "processing"
        enrichment_jobs[enrichment_id]["started_at"] = datetime.now()
        enrichment_jobs[enrichment_id]["progress_percentage"] = 10.0
        
        # Execute the enrichment workflow
        result = enrichment_workflows.run_market_intelligence(product_id, supplier_id)
        
        enrichment_jobs[enrichment_id]["progress_percentage"] = 100.0
        
        if result["success"]:
            enrichment_jobs[enrichment_id]["status"] = "completed"
            enrichment_jobs[enrichment_id]["results"] = result
        else:
            enrichment_jobs[enrichment_id]["status"] = "failed"
            enrichment_jobs[enrichment_id]["error_message"] = result.get("error", "Unknown error")
        
        enrichment_jobs[enrichment_id]["completed_at"] = datetime.now()
        
    except Exception as e:
        enrichment_jobs[enrichment_id]["status"] = "failed"
        enrichment_jobs[enrichment_id]["error_message"] = str(e)
        enrichment_jobs[enrichment_id]["completed_at"] = datetime.now()
        logger.error(f"Market enrichment failed for product {product_id}, supplier {supplier_id}: {str(e)}")

async def execute_bulk_enrichment(enrichment_id: str, request: BulkEnrichmentRequest):
    """Execute bulk enrichment in background"""
    try:
        enrichment_jobs[enrichment_id]["status"] = "processing"
        enrichment_jobs[enrichment_id]["started_at"] = datetime.now()
        enrichment_jobs[enrichment_id]["progress_percentage"] = 1.0
        
        total_entities = len(request.entity_ids)
        completed_entities = 0
        successful_enrichments = []
        failed_enrichments = []
        
        # Process entities in batches
        for i in range(0, total_entities, request.batch_size):
            batch = request.entity_ids[i:i + request.batch_size]
            
            # Process batch with limited concurrency
            semaphore = asyncio.Semaphore(request.max_concurrent)
            
            async def process_entity(entity_id):
                async with semaphore:
                    try:
                        if request.enrichment_type == "supplier":
                            result = enrichment_workflows.run_supplier_enrichment(entity_id)
                        elif request.enrichment_type == "brand":
                            result = enrichment_workflows.run_brand_intelligence(entity_id)
                        elif request.enrichment_type == "product":
                            result = enrichment_workflows.run_product_intelligence(entity_id)
                        else:
                            raise ValueError(f"Unknown enrichment type: {request.enrichment_type}")
                        
                        if result["success"]:
                            successful_enrichments.append(entity_id)
                        else:
                            failed_enrichments.append({"entity_id": entity_id, "error": result.get("error")})
                        
                        return result
                        
                    except Exception as e:
                        failed_enrichments.append({"entity_id": entity_id, "error": str(e)})
                        return {"success": False, "error": str(e)}
            
            # Execute batch
            batch_tasks = [process_entity(entity_id) for entity_id in batch]
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            completed_entities += len(batch)
            progress = (completed_entities / total_entities) * 100
            enrichment_jobs[enrichment_id]["progress_percentage"] = progress
            enrichment_jobs[enrichment_id]["completed_entities"] = completed_entities
        
        # Complete the job
        enrichment_jobs[enrichment_id]["status"] = "completed"
        enrichment_jobs[enrichment_id]["progress_percentage"] = 100.0
        enrichment_jobs[enrichment_id]["results"] = {
            "total_entities": total_entities,
            "successful_enrichments": len(successful_enrichments),
            "failed_enrichments": len(failed_enrichments),
            "successful_entity_ids": successful_enrichments,
            "failed_entities": failed_enrichments
        }
        enrichment_jobs[enrichment_id]["completed_at"] = datetime.now()
        
    except Exception as e:
        enrichment_jobs[enrichment_id]["status"] = "failed"
        enrichment_jobs[enrichment_id]["error_message"] = str(e)
        enrichment_jobs[enrichment_id]["completed_at"] = datetime.now()
        logger.error(f"Bulk enrichment failed: {str(e)}")

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "active_jobs": len([j for j in enrichment_jobs.values() if j["status"] in ["queued", "processing"]])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)