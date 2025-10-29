-- Migration: Add Email Quotation Request Tables
-- Version: 0006
-- Date: 2025-10-22
-- Description: Add support for email-based quotation requests with AI processing
-- NO MOCK DATA - Production-ready schema

BEGIN;

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Create or replace the updated_at trigger function in public schema
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =============================================================================
-- EMAIL QUOTATION REQUESTS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS email_quotation_requests (
    id SERIAL PRIMARY KEY,

    -- Email Metadata (from IMAP)
    message_id VARCHAR(500) UNIQUE NOT NULL,
    sender_email VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255),
    subject VARCHAR(500) NOT NULL,
    received_date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Email Content
    body_text TEXT,
    body_html TEXT,
    has_attachments BOOLEAN DEFAULT false,
    attachment_count INTEGER DEFAULT 0,

    -- Processing Status
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    -- Status values:
    --   'pending' - Email detected, waiting for processing
    --   'processing' - AI extraction in progress
    --   'completed' - AI extraction complete, ready for quotation
    --   'quotation_processing' - Quotation generation in progress
    --   'quotation_created' - Quotation successfully created
    --   'failed' - Processing failed (see error_message)
    --   'ignored' - Manually marked as non-RFQ

    -- AI Extraction Results (populated by DocumentProcessor)
    extracted_requirements JSONB,
    ai_confidence_score DECIMAL(3,2) CHECK (ai_confidence_score >= 0 AND ai_confidence_score <= 1),
    extracted_at TIMESTAMP WITH TIME ZONE,

    -- Linked Records
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    quotation_id INTEGER REFERENCES quotes(id) ON DELETE SET NULL,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,

    -- Processing Metadata
    processing_notes TEXT,
    error_message TEXT,
    processed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_status_values CHECK (
        status IN ('pending', 'processing', 'completed', 'quotation_processing',
                   'quotation_created', 'failed', 'ignored')
    )
);

-- Indexes for performance
CREATE INDEX idx_email_quotation_message_id ON email_quotation_requests(message_id);
CREATE INDEX idx_email_quotation_status ON email_quotation_requests(status);
CREATE INDEX idx_email_quotation_received_date ON email_quotation_requests(received_date DESC);
CREATE INDEX idx_email_quotation_sender ON email_quotation_requests(sender_email);
CREATE INDEX idx_email_quotation_created_at ON email_quotation_requests(created_at DESC);
CREATE INDEX idx_email_quotation_quotation_id ON email_quotation_requests(quotation_id) WHERE quotation_id IS NOT NULL;

-- Comment for documentation
COMMENT ON TABLE email_quotation_requests IS
'Email-based quotation requests detected from integrum@horme.com.sg inbox.
All data extracted from real emails with AI processing - NO MOCK DATA.
Linked to existing quotes table when quotation is generated.';

COMMENT ON COLUMN email_quotation_requests.message_id IS
'Email Message-ID header - used for duplicate detection';

COMMENT ON COLUMN email_quotation_requests.extracted_requirements IS
'AI-extracted requirements in JSON format matching DocumentProcessor output schema';

COMMENT ON COLUMN email_quotation_requests.ai_confidence_score IS
'AI extraction confidence score (0.0-1.0) - higher is better';

-- =============================================================================
-- EMAIL ATTACHMENTS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS email_attachments (
    id SERIAL PRIMARY KEY,
    email_request_id INTEGER NOT NULL REFERENCES email_quotation_requests(id) ON DELETE CASCADE,

    -- File Information
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size > 0),
    mime_type VARCHAR(100),

    -- Processing Status
    processed BOOLEAN DEFAULT false,
    processing_status VARCHAR(50) DEFAULT 'pending',
    -- Status values: 'pending', 'processing', 'completed', 'failed', 'skipped'
    processing_error TEXT,

    -- Link to documents table (for processed attachments)
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_attachment_status CHECK (
        processing_status IN ('pending', 'processing', 'completed', 'failed', 'skipped')
    )
);

-- Indexes for performance
CREATE INDEX idx_email_attachments_request ON email_attachments(email_request_id);
CREATE INDEX idx_email_attachments_processed ON email_attachments(processed);
CREATE INDEX idx_email_attachments_document ON email_attachments(document_id) WHERE document_id IS NOT NULL;

-- Comment for documentation
COMMENT ON TABLE email_attachments IS
'Email attachments (PDF, DOCX, XLSX) linked to quotation requests.
Files stored in /app/email-attachments/ directory with 600 permissions.
Processed using existing DocumentProcessor service.';

COMMENT ON COLUMN email_attachments.file_path IS
'Absolute path to attachment file on disk (/app/email-attachments/)';

COMMENT ON COLUMN email_attachments.document_id IS
'Links to documents table after attachment is processed by DocumentProcessor';

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE TRIGGER update_email_quotation_requests_updated_at
BEFORE UPDATE ON email_quotation_requests
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify tables created
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'email_quotation_requests') THEN
        RAISE EXCEPTION 'Table email_quotation_requests was not created';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'email_attachments') THEN
        RAISE EXCEPTION 'Table email_attachments was not created';
    END IF;

    RAISE NOTICE 'Email quotation tables created successfully';
END $$;

COMMIT;

-- Display table structures for verification
\d email_quotation_requests
\d email_attachments

-- Display indexes
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('email_quotation_requests', 'email_attachments')
ORDER BY tablename, indexname;
