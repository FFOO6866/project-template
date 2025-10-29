#!/bin/bash
# Database Migration Script for Documents Table
# Safely creates documents table if it doesn't exist

set -e  # Exit on error

echo "========================================="
echo "Horme POV - Documents Table Migration"
echo "========================================="
echo ""

# Configuration from environment or defaults
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_NAME="${DB_NAME:-horme_db}"
DB_USER="${DB_USER:-horme_user}"
DB_PASSWORD="${DB_PASSWORD:-horme_pass}"

echo "Database Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ ERROR: psql command not found"
    echo "   Please install PostgreSQL client tools"
    exit 1
fi

echo "📋 Checking database connection..."

# Test database connection
if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1" &> /dev/null; then
    echo "✅ Database connection successful"
else
    echo "❌ ERROR: Could not connect to database"
    echo "   Please check your database credentials and ensure PostgreSQL is running"
    exit 1
fi

echo ""
echo "📝 Creating documents table..."

# Run migration SQL
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << 'EOF'

-- Create documents table if it doesn't exist
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
    ai_status VARCHAR(50) DEFAULT 'pending',
    ai_extracted_data JSONB,

    -- Extraction metadata
    extraction_method VARCHAR(100),
    extraction_confidence DECIMAL(5,2),
    processing_time_ms INTEGER,

    -- Constraints
    CONSTRAINT chk_ai_status CHECK (ai_status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT chk_file_type CHECK (file_type IN ('.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls'))
);

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(ai_status);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_client ON documents(client_name);
CREATE INDEX IF NOT EXISTS idx_documents_confidence ON documents(extraction_confidence DESC);
CREATE INDEX IF NOT EXISTS idx_documents_extracted_data ON documents USING gin(ai_extracted_data);

-- Add comments
COMMENT ON TABLE documents IS 'Stores uploaded RFP documents with AI extraction results';
COMMENT ON COLUMN documents.ai_status IS 'Processing status: pending, processing, completed, failed';
COMMENT ON COLUMN documents.ai_extracted_data IS 'JSON data containing extracted requirements and metadata';
COMMENT ON COLUMN documents.extraction_method IS 'Method used for extraction: pdf_camelot, pdf_pdfplumber, docling, vision, etc.';
COMMENT ON COLUMN documents.extraction_confidence IS 'Confidence score (0.00-1.00) of the extraction quality';
COMMENT ON COLUMN documents.processing_time_ms IS 'Time taken to process the document in milliseconds';

\echo '✅ Documents table created successfully'
\echo ''

-- Show table structure
\echo '📊 Table Structure:'
\d documents

\echo ''
\echo '📈 Current Statistics:'

-- Show current document count
SELECT
    COUNT(*) as total_documents,
    COUNT(CASE WHEN ai_status = 'pending' THEN 1 END) as pending,
    COUNT(CASE WHEN ai_status = 'processing' THEN 1 END) as processing,
    COUNT(CASE WHEN ai_status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN ai_status = 'failed' THEN 1 END) as failed
FROM documents;

EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ Migration completed successfully!"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo "1. Restart your API server to load the new document endpoints"
    echo "2. Test document upload: POST /api/v1/documents/upload"
    echo "3. Monitor processing: GET /api/v1/documents/status/{id}"
    echo ""
else
    echo ""
    echo "========================================="
    echo "❌ Migration failed!"
    echo "========================================="
    echo ""
    echo "Please check the error messages above and try again."
    exit 1
fi
