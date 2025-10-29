-- Migration: Create documents table for RFP document processing
-- Date: 2025-01-27
-- Description: Stores uploaded RFP documents with AI extraction status and results

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,

    -- File information
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,

    -- Client information
    client_name VARCHAR(255),
    project_title VARCHAR(255),

    -- Upload metadata
    uploaded_by VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- AI processing status
    ai_status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    ai_extracted_data JSONB,

    -- Extraction metadata
    extraction_method VARCHAR(100),
    extraction_confidence DECIMAL(5,2),
    processing_time_ms INTEGER,

    -- Indexes for common queries
    CONSTRAINT chk_ai_status CHECK (ai_status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT chk_file_type CHECK (file_type IN ('.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(ai_status);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_client ON documents(client_name);
CREATE INDEX IF NOT EXISTS idx_documents_confidence ON documents(extraction_confidence DESC);

-- GIN index for JSON data search
CREATE INDEX IF NOT EXISTS idx_documents_extracted_data ON documents USING gin(ai_extracted_data);

-- Comments for documentation
COMMENT ON TABLE documents IS 'Stores uploaded RFP documents with AI extraction results';
COMMENT ON COLUMN documents.ai_status IS 'Processing status: pending, processing, completed, failed';
COMMENT ON COLUMN documents.ai_extracted_data IS 'JSON data containing extracted requirements and metadata';
COMMENT ON COLUMN documents.extraction_method IS 'Method used for extraction: pdf_camelot, pdf_pdfplumber, docling, vision, etc.';
COMMENT ON COLUMN documents.extraction_confidence IS 'Confidence score (0.00-1.00) of the extraction quality';
COMMENT ON COLUMN documents.processing_time_ms IS 'Time taken to process the document in milliseconds';
