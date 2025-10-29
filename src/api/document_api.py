"""
Document Processing API
Handles document uploads, text extraction, and AI-powered requirement analysis
Uses EnhancedDocumentProcessor for multi-strategy extraction
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import tempfile
import os
import asyncpg
from datetime import datetime
from pathlib import Path

from ..core.auth import User, Permission, require_permission
from ..services.enhanced_document_processor import EnhancedDocumentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Pydantic models
class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    file_size: int
    file_type: str
    status: str
    message: str
    upload_date: str

class DocumentProcessingStatus(BaseModel):
    document_id: int
    filename: str
    status: str  # pending, processing, completed, failed
    progress: Optional[str] = None
    extracted_items: int = 0
    extraction_method: Optional[str] = None
    extraction_confidence: Optional[float] = None
    processing_time_ms: Optional[int] = None
    error: Optional[str] = None
    updated_at: str

class DocumentRequirements(BaseModel):
    document_id: int
    filename: str
    customer_name: Optional[str] = None
    project_name: Optional[str] = None
    deadline: Optional[str] = None
    items: List[Dict[str, Any]]
    additional_requirements: List[str]
    delivery_address: Optional[str] = None
    contact_email: Optional[str] = None
    extraction_metadata: Dict[str, Any]

class DocumentListResponse(BaseModel):
    documents: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


# Database configuration (using environment variables in production)
async def get_db_pool() -> asyncpg.Pool:
    """Get database connection pool"""
    database_url = os.getenv('DATABASE_URL', 'postgresql://horme_user:horme_pass@localhost:5433/horme_db')

    # Convert to asyncpg format if needed
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

    try:
        pool = await asyncpg.create_pool(database_url, min_size=1, max_size=10)
        return pool
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")


# Helper function to save uploaded file
async def save_uploaded_file(file: UploadFile) -> tuple[str, int]:
    """
    Save uploaded file to temporary location

    Returns:
        tuple: (file_path, file_size)
    """
    # Create uploads directory if it doesn't exist
    upload_dir = Path(os.getenv('UPLOAD_DIR', '/tmp/horme_uploads'))
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    file_extension = Path(file.filename).suffix
    safe_filename = f"{timestamp}_{Path(file.filename).stem}{file_extension}"
    file_path = upload_dir / safe_filename

    # Save file
    content = await file.read()
    file_size = len(content)

    with open(file_path, 'wb') as f:
        f.write(content)

    logger.info(f"Saved uploaded file: {file_path} ({file_size} bytes)")
    return str(file_path), file_size


# API Endpoints

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    client_name: Optional[str] = Form(None),
    project_title: Optional[str] = Form(None),
    current_user: User = Depends(require_permission(Permission.WRITE))
):
    """
    Upload RFP document for processing

    Supports: PDF, DOCX, TXT, XLSX
    Processing happens in background, check status with /status/{document_id}
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls'}
        file_extension = Path(file.filename).suffix.lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported types: {', '.join(allowed_extensions)}"
            )

        # Save uploaded file
        file_path, file_size = await save_uploaded_file(file)

        # Get database pool
        db_pool = await get_db_pool()

        # Insert document record into database
        async with db_pool.acquire() as conn:
            document_id = await conn.fetchval("""
                INSERT INTO documents (
                    filename,
                    file_path,
                    file_size,
                    file_type,
                    client_name,
                    project_title,
                    uploaded_by,
                    ai_status,
                    uploaded_at,
                    updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            """,
            file.filename,
            file_path,
            file_size,
            file_extension,
            client_name,
            project_title,
            current_user.username,
            'pending'
            )

        logger.info(f"Document uploaded: ID={document_id}, file={file.filename}, user={current_user.username}")

        # Start background processing
        background_tasks.add_task(process_document_async, document_id, file_path, db_pool)

        await db_pool.close()

        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            file_type=file_extension,
            status="pending",
            message="Document uploaded successfully. Processing started in background.",
            upload_date=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def process_document_async(document_id: int, file_path: str, db_pool: asyncpg.Pool):
    """
    Background task to process document with Enhanced Document Processor

    This function runs in the background after upload completes
    """
    try:
        logger.info(f"Starting background processing for document {document_id}")

        # Initialize enhanced document processor
        processor = EnhancedDocumentProcessor()

        # Process document with multi-strategy extraction
        results = await processor.process_document(document_id, file_path, db_pool)

        logger.info(
            f"Document {document_id} processed successfully: "
            f"{len(results['requirements'].get('items', []))} items extracted"
        )

    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {e}", exc_info=True)
        # Error is already logged in the database by the processor


@router.get("/status/{document_id}", response_model=DocumentProcessingStatus)
async def get_document_status(
    document_id: int,
    current_user: User = Depends(require_permission(Permission.READ))
):
    """
    Get processing status of uploaded document
    """
    try:
        db_pool = await get_db_pool()

        async with db_pool.acquire() as conn:
            doc = await conn.fetchrow("""
                SELECT
                    id,
                    filename,
                    ai_status,
                    extraction_method,
                    extraction_confidence,
                    processing_time_ms,
                    ai_extracted_data,
                    updated_at
                FROM documents
                WHERE id = $1
            """, document_id)

        await db_pool.close()

        if not doc:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

        # Parse extracted data if available
        extracted_data = doc['ai_extracted_data']
        extracted_items = 0
        error_message = None

        if extracted_data:
            if isinstance(extracted_data, dict):
                if 'requirements' in extracted_data:
                    extracted_items = len(extracted_data['requirements'].get('items', []))
                elif 'error' in extracted_data:
                    error_message = extracted_data['error']

        return DocumentProcessingStatus(
            document_id=doc['id'],
            filename=doc['filename'],
            status=doc['ai_status'],
            extracted_items=extracted_items,
            extraction_method=doc['extraction_method'],
            extraction_confidence=float(doc['extraction_confidence']) if doc['extraction_confidence'] else None,
            processing_time_ms=doc['processing_time_ms'],
            error=error_message,
            updated_at=doc['updated_at'].isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/requirements", response_model=DocumentRequirements)
async def get_document_requirements(
    document_id: int,
    current_user: User = Depends(require_permission(Permission.READ))
):
    """
    Get extracted requirements from processed document

    Returns structured requirements including:
    - Customer and project information
    - Product line items with quantities
    - Additional requirements (delivery, payment terms, etc.)
    """
    try:
        db_pool = await get_db_pool()

        async with db_pool.acquire() as conn:
            doc = await conn.fetchrow("""
                SELECT
                    id,
                    filename,
                    ai_status,
                    ai_extracted_data,
                    extraction_method,
                    extraction_confidence,
                    processing_time_ms
                FROM documents
                WHERE id = $1
            """, document_id)

        await db_pool.close()

        if not doc:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

        if doc['ai_status'] == 'pending':
            raise HTTPException(
                status_code=202,
                detail="Document is still being processed. Please check status endpoint."
            )

        if doc['ai_status'] == 'processing':
            raise HTTPException(
                status_code=202,
                detail="Document processing is in progress. Please try again in a moment."
            )

        if doc['ai_status'] == 'failed':
            error_data = doc['ai_extracted_data']
            error_msg = error_data.get('error', 'Unknown error') if error_data else 'Unknown error'
            raise HTTPException(
                status_code=422,
                detail=f"Document processing failed: {error_msg}"
            )

        # Extract requirements from processed data
        extracted_data = doc['ai_extracted_data']
        if not extracted_data or 'requirements' not in extracted_data:
            raise HTTPException(
                status_code=422,
                detail="No requirements found in document. The document may be empty or in an unsupported format."
            )

        requirements = extracted_data['requirements']

        return DocumentRequirements(
            document_id=doc['id'],
            filename=doc['filename'],
            customer_name=requirements.get('customer_name'),
            project_name=requirements.get('project_name'),
            deadline=requirements.get('deadline'),
            items=requirements.get('items', []),
            additional_requirements=requirements.get('additional_requirements', []),
            delivery_address=requirements.get('delivery_address'),
            contact_email=requirements.get('contact_email'),
            extraction_metadata={
                'extraction_method': doc['extraction_method'],
                'extraction_confidence': float(doc['extraction_confidence']) if doc['extraction_confidence'] else None,
                'processing_time_ms': doc['processing_time_ms'],
                'extracted_text_length': extracted_data.get('full_text_length', 0),
                'processor_version': extracted_data.get('processor_version', 'unknown')
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document requirements: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(require_permission(Permission.READ))
):
    """
    List uploaded documents with pagination

    Optional filtering by processing status: pending, processing, completed, failed
    """
    try:
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20

        offset = (page - 1) * page_size

        db_pool = await get_db_pool()

        # Build query with optional status filter - FIXED to match actual database schema
        query = """
            SELECT
                id,
                name,
                file_size,
                type,
                mime_type,
                ai_status,
                ai_confidence_score,
                upload_date,
                updated_at,
                customer_id
            FROM documents
        """

        count_query = "SELECT COUNT(*) FROM documents"
        params = []

        if status:
            query += " WHERE ai_status = $1"
            count_query += " WHERE ai_status = $1"
            params.append(status)

        query += f" ORDER BY upload_date DESC LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
        params.extend([page_size, offset])

        async with db_pool.acquire() as conn:
            # Get total count
            if status:
                total = await conn.fetchval(count_query, status)
            else:
                total = await conn.fetchval(count_query)

            # Get documents
            rows = await conn.fetch(query, *params)

        await db_pool.close()

        documents = [
            {
                'id': row['id'],
                'filename': row['name'],  # Map 'name' to 'filename' for API response
                'file_size': row['file_size'],
                'file_type': row['type'],  # Map 'type' to 'file_type'
                'mime_type': row['mime_type'],
                'client_name': None,  # TODO: Join with customers table when needed
                'project_title': None,  # TODO: Extract from ai_extracted_data if needed
                'status': row['ai_status'],
                'confidence': float(row['ai_confidence_score']) if row['ai_confidence_score'] else None,
                'uploaded_at': row['upload_date'].isoformat(),
                'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
            }
            for row in rows
        ]

        return DocumentListResponse(
            documents=documents,
            total=total,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(require_permission(Permission.DELETE))
):
    """
    Delete uploaded document and its extracted data
    """
    try:
        db_pool = await get_db_pool()

        async with db_pool.acquire() as conn:
            # Get file path before deleting
            doc = await conn.fetchrow("""
                SELECT file_path FROM documents WHERE id = $1
            """, document_id)

            if not doc:
                raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

            # Delete from database
            await conn.execute("""
                DELETE FROM documents WHERE id = $1
            """, document_id)

        await db_pool.close()

        # Delete physical file if it exists
        file_path = doc['file_path']
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
                logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete physical file {file_path}: {e}")

        logger.info(f"Document {document_id} deleted by user {current_user.username}")

        return {
            "message": f"Document {document_id} deleted successfully",
            "document_id": document_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
