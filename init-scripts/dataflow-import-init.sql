-- DataFlow Import Database Initialization
-- PostgreSQL setup for DataFlow 0.4.2 with performance optimizations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create performance monitoring view
CREATE OR REPLACE VIEW import_progress AS
SELECT 
    'categories' as table_name,
    COUNT(*) as record_count,
    MAX(created_at) as last_created
FROM categories
WHERE deleted_at IS NULL
UNION ALL
SELECT 
    'brands' as table_name,
    COUNT(*) as record_count,
    MAX(created_at) as last_created
FROM brands
WHERE deleted_at IS NULL
UNION ALL
SELECT 
    'products' as table_name,
    COUNT(*) as record_count,
    MAX(created_at) as last_created
FROM products
WHERE deleted_at IS NULL;

-- Create import statistics function
CREATE OR REPLACE FUNCTION get_import_stats()
RETURNS TABLE(
    total_products BIGINT,
    active_products BIGINT,
    total_categories BIGINT,
    total_brands BIGINT,
    products_with_categories BIGINT,
    products_with_brands BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM products WHERE deleted_at IS NULL)::BIGINT,
        (SELECT COUNT(*) FROM products WHERE deleted_at IS NULL AND status = 'active')::BIGINT,
        (SELECT COUNT(*) FROM categories WHERE deleted_at IS NULL)::BIGINT,
        (SELECT COUNT(*) FROM brands WHERE deleted_at IS NULL)::BIGINT,
        (SELECT COUNT(*) FROM products WHERE deleted_at IS NULL AND category_id IS NOT NULL)::BIGINT,
        (SELECT COUNT(*) FROM products WHERE deleted_at IS NULL AND brand_id IS NOT NULL)::BIGINT;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to the horme_user
GRANT USAGE ON SCHEMA public TO horme_user;
GRANT CREATE ON SCHEMA public TO horme_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO horme_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO horme_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO horme_user;

-- Set default permissions for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO horme_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO horme_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO horme_user;

-- Performance settings for bulk imports
-- These will be applied to all connections
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Reload configuration
SELECT pg_reload_conf();

-- Create monitoring table for real-time progress tracking
CREATE TABLE IF NOT EXISTS import_monitoring (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operation VARCHAR(50) NOT NULL,
    records_processed INTEGER DEFAULT 0,
    records_total INTEGER DEFAULT 0,
    batch_number INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running',
    message TEXT,
    execution_time_ms INTEGER DEFAULT 0
);

-- Grant permissions on monitoring table
GRANT ALL PRIVILEGES ON import_monitoring TO horme_user;
GRANT ALL PRIVILEGES ON import_monitoring_id_seq TO horme_user;

-- Create function to log import progress
CREATE OR REPLACE FUNCTION log_import_progress(
    p_operation VARCHAR(50),
    p_records_processed INTEGER DEFAULT 0,
    p_records_total INTEGER DEFAULT 0,
    p_batch_number INTEGER DEFAULT 0,
    p_status VARCHAR(20) DEFAULT 'running',
    p_message TEXT DEFAULT NULL,
    p_execution_time_ms INTEGER DEFAULT 0
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO import_monitoring (
        operation, records_processed, records_total, 
        batch_number, status, message, execution_time_ms
    ) VALUES (
        p_operation, p_records_processed, p_records_total,
        p_batch_number, p_status, p_message, p_execution_time_ms
    );
END;
$$ LANGUAGE plpgsql;

-- Create view for current import status
CREATE OR REPLACE VIEW current_import_status AS
SELECT 
    operation,
    MAX(records_processed) as current_records,
    MAX(records_total) as total_records,
    CASE 
        WHEN MAX(records_total) > 0 
        THEN ROUND((MAX(records_processed::float) / MAX(records_total) * 100), 2)
        ELSE 0 
    END as progress_percentage,
    MAX(timestamp) as last_update,
    (SELECT status FROM import_monitoring im WHERE im.operation = m.operation ORDER BY timestamp DESC LIMIT 1) as current_status
FROM import_monitoring m
GROUP BY operation
ORDER BY last_update DESC;

-- Grant permissions on views and functions
GRANT SELECT ON import_progress TO horme_user;
GRANT SELECT ON current_import_status TO horme_user;
GRANT EXECUTE ON FUNCTION get_import_stats() TO horme_user;
GRANT EXECUTE ON FUNCTION log_import_progress(VARCHAR, INTEGER, INTEGER, INTEGER, VARCHAR, TEXT, INTEGER) TO horme_user;

-- Initialize monitoring with startup message
INSERT INTO import_monitoring (operation, status, message) 
VALUES ('system', 'initialized', 'DataFlow import database initialized successfully');

COMMIT;