-- Database Schema Updates for Enhanced Document Processing
-- Implements analytics tracking as per RFP_DOCUMENT_PARSING_RESEARCH.md

-- Add extraction analytics columns to documents table
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(50),
ADD COLUMN IF NOT EXISTS extraction_confidence DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS processing_time_ms INTEGER;

-- Add comments for documentation
COMMENT ON COLUMN documents.extraction_method IS 'Method used for document extraction: specialized, docling, vision, or basic_fallback';
COMMENT ON COLUMN documents.extraction_confidence IS 'Confidence score (0.0-1.0) for extraction quality';
COMMENT ON COLUMN documents.processing_time_ms IS 'Processing time in milliseconds';

-- Create index for analytics queries
CREATE INDEX IF NOT EXISTS idx_documents_extraction_method ON documents(extraction_method);
CREATE INDEX IF NOT EXISTS idx_documents_extraction_confidence ON documents(extraction_confidence);
CREATE INDEX IF NOT EXISTS idx_documents_processing_time ON documents(processing_time_ms);

-- Create view for extraction analytics
CREATE OR REPLACE VIEW extraction_analytics AS
SELECT
    extraction_method,
    COUNT(*) as documents_processed,
    AVG(extraction_confidence) as avg_confidence,
    MIN(extraction_confidence) as min_confidence,
    MAX(extraction_confidence) as max_confidence,
    AVG(processing_time_ms) as avg_time_ms,
    MIN(processing_time_ms) as min_time_ms,
    MAX(processing_time_ms) as max_time_ms,
    COUNT(CASE WHEN ai_status = 'completed' THEN 1 END) as successful_extractions,
    COUNT(CASE WHEN ai_status = 'failed' THEN 1 END) as failed_extractions,
    ROUND(COUNT(CASE WHEN ai_status = 'completed' THEN 1 END)::numeric / COUNT(*)::numeric * 100, 2) as success_rate_pct
FROM documents
WHERE extraction_method IS NOT NULL
GROUP BY extraction_method
ORDER BY avg_confidence DESC;

COMMENT ON VIEW extraction_analytics IS 'Analytics view showing performance metrics for each extraction method';

-- Create view for document format analytics
CREATE OR REPLACE VIEW format_analytics AS
SELECT
    CASE
        WHEN file_path ILIKE '%.pdf' THEN 'PDF'
        WHEN file_path ILIKE '%.docx' OR file_path ILIKE '%.doc' THEN 'Word'
        WHEN file_path ILIKE '%.xlsx' OR file_path ILIKE '%.xls' THEN 'Excel'
        WHEN file_path ILIKE '%.txt' THEN 'Text'
        ELSE 'Other'
    END as file_format,
    COUNT(*) as total_documents,
    COUNT(CASE WHEN ai_status = 'completed' THEN 1 END) as successful,
    AVG(extraction_confidence) as avg_confidence,
    AVG(processing_time_ms) as avg_processing_time_ms
FROM documents
WHERE file_path IS NOT NULL
GROUP BY file_format
ORDER BY total_documents DESC;

COMMENT ON VIEW format_analytics IS 'Analytics view showing extraction success by file format';

-- Query examples for analytics
COMMENT ON VIEW extraction_analytics IS 'Example query: SELECT * FROM extraction_analytics ORDER BY avg_confidence DESC;';
COMMENT ON VIEW format_analytics IS 'Example query: SELECT * FROM format_analytics WHERE avg_confidence > 0.8;';
