"""
Email Quotation Request Models
Pydantic models for email-based RFQ processing
NO MOCK DATA - All models validated against real database schema
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator
from decimal import Decimal


class EmailAttachmentBase(BaseModel):
    """Base email attachment model"""
    filename: str = Field(..., min_length=1, max_length=500)
    file_path: str = Field(..., min_length=1, max_length=1000)
    file_size: int = Field(..., gt=0, description="File size in bytes")
    mime_type: Optional[str] = Field(None, max_length=100)


class EmailAttachmentCreate(EmailAttachmentBase):
    """Create email attachment"""
    email_request_id: int = Field(..., gt=0)


class EmailAttachment(EmailAttachmentBase):
    """Email attachment model with processing status"""
    id: int
    email_request_id: int
    processed: bool = False
    processing_status: str = Field(default="pending")
    processing_error: Optional[str] = None
    document_id: Optional[int] = None
    created_at: datetime

    @field_validator('processing_status')
    @classmethod
    def validate_processing_status(cls, v: str) -> str:
        allowed = ['pending', 'processing', 'completed', 'failed', 'skipped']
        if v not in allowed:
            raise ValueError(f"processing_status must be one of {allowed}")
        return v

    class Config:
        from_attributes = True


class EmailQuotationRequestBase(BaseModel):
    """Base email quotation request model"""
    message_id: str = Field(..., min_length=1, max_length=500, description="Email Message-ID header")
    sender_email: EmailStr
    sender_name: Optional[str] = Field(None, max_length=255)
    subject: str = Field(..., min_length=1, max_length=500)
    received_date: datetime


class EmailQuotationRequestCreate(EmailQuotationRequestBase):
    """Create email quotation request"""
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    has_attachments: bool = False
    attachment_count: int = Field(default=0, ge=0)


class EmailQuotationRequestUpdate(BaseModel):
    """Update email quotation request"""
    status: Optional[str] = None
    extracted_requirements: Optional[Dict[str, Any]] = None
    ai_confidence_score: Optional[Decimal] = Field(None, ge=0, le=1)
    extracted_at: Optional[datetime] = None
    document_id: Optional[int] = None
    quotation_id: Optional[int] = None
    customer_id: Optional[int] = None
    processing_notes: Optional[str] = None
    error_message: Optional[str] = None
    processed_by: Optional[int] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = [
            'pending', 'processing', 'completed', 'quotation_processing',
            'quotation_created', 'failed', 'ignored'
        ]
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class EmailQuotationRequest(EmailQuotationRequestBase):
    """Full email quotation request model"""
    id: int
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    has_attachments: bool = False
    attachment_count: int = 0
    status: str = "pending"
    extracted_requirements: Optional[Dict[str, Any]] = None
    ai_confidence_score: Optional[Decimal] = None
    extracted_at: Optional[datetime] = None
    document_id: Optional[int] = None
    quotation_id: Optional[int] = None
    customer_id: Optional[int] = None
    processing_notes: Optional[str] = None
    error_message: Optional[str] = None
    processed_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = [
            'pending', 'processing', 'completed', 'quotation_processing',
            'quotation_created', 'failed', 'ignored'
        ]
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v

    class Config:
        from_attributes = True


class EmailQuotationRequestResponse(BaseModel):
    """Email quotation request response for dashboard - lightweight"""
    id: int
    received_date: datetime
    sender_name: Optional[str]
    sender_email: str
    subject: str
    status: str
    ai_confidence_score: Optional[Decimal]
    attachment_count: int
    quotation_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class EmailQuotationRequestDetail(EmailQuotationRequest):
    """Detailed email quotation request with attachments"""
    attachments: List[EmailAttachment] = Field(default_factory=list)

    class Config:
        from_attributes = True


class EmailProcessingResult(BaseModel):
    """Result of email processing (AI extraction)"""
    success: bool
    email_request_id: int
    extracted_requirements: Optional[Dict[str, Any]] = None
    ai_confidence_score: Optional[Decimal] = None
    error_message: Optional[str] = None
    processing_time_seconds: float


class QuotationGenerationRequest(BaseModel):
    """Request to generate quotation from email"""
    email_request_id: int = Field(..., gt=0)
    force_reprocess: bool = Field(
        default=False,
        description="Force reprocessing even if quotation already exists"
    )


class QuotationGenerationResponse(BaseModel):
    """Response from quotation generation"""
    success: bool
    message: str
    email_request_id: int
    quotation_id: Optional[int] = None
    quotation_number: Optional[str] = None
    pdf_path: Optional[str] = None
    error: Optional[str] = None
