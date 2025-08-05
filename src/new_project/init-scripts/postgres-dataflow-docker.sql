-- PostgreSQL DataFlow Docker Initialization Script
-- Optimized for DataFlow classification system with pgvector support
-- Container-ready with no Windows-specific paths

-- Create required PostgreSQL extensions for DataFlow
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Text similarity for search
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- Enhanced indexing
CREATE EXTENSION IF NOT EXISTS "pgvector";       -- Vector similarity search

-- Create DataFlow classification schema
CREATE SCHEMA IF NOT EXISTS dataflow_classification;

-- Create dedicated users for different access levels
DO $$
BEGIN
    -- DataFlow application user (already exists from docker-compose)
    -- horme_user with password horme_password
    
    -- Create read-only monitoring user
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dataflow_monitor') THEN
        CREATE USER dataflow_monitor WITH PASSWORD 'monitor_dataflow_2025';
    END IF;
    
    -- Create backup user
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dataflow_backup') THEN
        CREATE USER dataflow_backup WITH PASSWORD 'backup_dataflow_2025';
    END IF;
END
$$;

-- Grant appropriate permissions
GRANT CONNECT ON DATABASE horme_classification_db TO dataflow_monitor;
GRANT CONNECT ON DATABASE horme_classification_db TO dataflow_backup;

GRANT USAGE ON SCHEMA public TO dataflow_monitor;
GRANT USAGE ON SCHEMA dataflow_classification TO dataflow_monitor;

GRANT USAGE ON SCHEMA public TO dataflow_backup;
GRANT USAGE ON SCHEMA dataflow_classification TO dataflow_backup;

-- DataFlow application user gets full access
GRANT USAGE ON SCHEMA dataflow_classification TO horme_user;
GRANT ALL PRIVILEGES ON SCHEMA dataflow_classification TO horme_user;

-- Performance optimization settings for DataFlow workloads
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements,pg_trgm';

-- Connection optimization for Docker containers
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET superuser_reserved_connections = 3;

-- Memory optimization for classification workloads
ALTER SYSTEM SET shared_buffers = '512MB';
ALTER SYSTEM SET effective_cache_size = '2GB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET work_mem = '8MB';

-- WAL optimization for bulk operations
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.7;
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

-- Query optimization for classification patterns
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET default_statistics_target = 100;

-- Parallel processing for bulk classification
ALTER SYSTEM SET max_worker_processes = 8;
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;
ALTER SYSTEM SET max_parallel_maintenance_workers = 4;

-- Autovacuum optimization for high-traffic models
ALTER SYSTEM SET autovacuum_naptime = '30s';
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;
ALTER SYSTEM SET autovacuum_max_workers = 4;

-- Logging for DataFlow monitoring
ALTER SYSTEM SET log_statement = 'mod';  -- Log modifications only
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log slow queries
ALTER SYSTEM SET track_activity_query_size = 4096;
ALTER SYSTEM SET track_io_timing = on;

-- pgvector optimization
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements,pg_trgm,vector';
ALTER SYSTEM SET max_prepared_transactions = 100;

-- Create DataFlow system tables for monitoring and caching

-- DataFlow model metadata table
CREATE TABLE IF NOT EXISTS dataflow_classification.model_metadata (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL UNIQUE,
    model_version VARCHAR(50) DEFAULT '1.0',
    schema_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    auto_generated_nodes INTEGER DEFAULT 9,
    indexes_count INTEGER DEFAULT 0,
    performance_level VARCHAR(20) DEFAULT 'standard',
    cache_enabled BOOLEAN DEFAULT TRUE,
    multi_tenant BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_model_metadata_name ON dataflow_classification.model_metadata(model_name);
CREATE INDEX IF NOT EXISTS idx_model_metadata_version ON dataflow_classification.model_metadata(model_version);

-- DataFlow node execution statistics
CREATE TABLE IF NOT EXISTS dataflow_classification.node_execution_stats (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    node_name VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50) NOT NULL, -- Create, Read, Update, Delete, List, BulkCreate, etc.
    execution_time_ms DECIMAL(10,2) NOT NULL,
    records_processed INTEGER DEFAULT 1,
    records_per_second DECIMAL(10,2),
    cache_hit BOOLEAN DEFAULT FALSE,
    error_occurred BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    executed_at TIMESTAMPTZ DEFAULT NOW(),
    user_id INTEGER,
    tenant_id VARCHAR(100),
    workflow_id UUID
);

-- Partition by month for performance
CREATE TABLE IF NOT EXISTS dataflow_classification.node_execution_stats_y2025m01 
PARTITION OF dataflow_classification.node_execution_stats
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE IF NOT EXISTS dataflow_classification.node_execution_stats_y2025m02 
PARTITION OF dataflow_classification.node_execution_stats
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

CREATE INDEX IF NOT EXISTS idx_node_execution_stats_node_model ON dataflow_classification.node_execution_stats(node_name, model_name);
CREATE INDEX IF NOT EXISTS idx_node_execution_stats_execution_time ON dataflow_classification.node_execution_stats(execution_time_ms);
CREATE INDEX IF NOT EXISTS idx_node_execution_stats_executed_at ON dataflow_classification.node_execution_stats(executed_at);

-- DataFlow cache performance tracking
CREATE TABLE IF NOT EXISTS dataflow_classification.cache_performance (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    cache_key VARCHAR(255) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    hit_count INTEGER DEFAULT 0,
    miss_count INTEGER DEFAULT 0,
    last_hit_at TIMESTAMPTZ,
    cache_size_bytes INTEGER DEFAULT 0,
    ttl_seconds INTEGER DEFAULT 3600,
    efficiency_ratio DECIMAL(5,4) DEFAULT 0.0000,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cache_performance_model ON dataflow_classification.cache_performance(model_name);
CREATE INDEX IF NOT EXISTS idx_cache_performance_efficiency ON dataflow_classification.cache_performance(efficiency_ratio);
CREATE INDEX IF NOT EXISTS idx_cache_performance_last_hit ON dataflow_classification.cache_performance(last_hit_at);

-- DataFlow migration history
CREATE TABLE IF NOT EXISTS dataflow_classification.migration_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    migration_type VARCHAR(50) NOT NULL, -- create_table, add_column, add_index, etc.
    sql_executed TEXT NOT NULL,
    execution_time_ms DECIMAL(10,2) NOT NULL,
    records_affected INTEGER DEFAULT 0,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    rollback_sql TEXT,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    applied_by VARCHAR(100) DEFAULT 'dataflow_auto_migrate'
);

CREATE INDEX IF NOT EXISTS idx_migration_history_model ON dataflow_classification.migration_history(model_name);
CREATE INDEX IF NOT EXISTS idx_migration_history_applied_at ON dataflow_classification.migration_history(applied_at);
CREATE INDEX IF NOT EXISTS idx_migration_history_success ON dataflow_classification.migration_history(success);

-- DataFlow bulk operation tracking
CREATE TABLE IF NOT EXISTS dataflow_classification.bulk_operation_tracking (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    operation_id UUID NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50) NOT NULL, -- BulkCreate, BulkUpdate, BulkDelete, BulkUpsert
    total_records INTEGER NOT NULL,
    processed_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    batch_size INTEGER DEFAULT 1000,
    batches_completed INTEGER DEFAULT 0,
    total_batches INTEGER NOT NULL,
    throughput_records_per_second DECIMAL(10,2),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'running', -- running, paused, completed, failed
    error_summary TEXT,
    progress_percentage DECIMAL(5,2) DEFAULT 0.00
);

CREATE INDEX IF NOT EXISTS idx_bulk_operation_tracking_operation_id ON dataflow_classification.bulk_operation_tracking(operation_id);
CREATE INDEX IF NOT EXISTS idx_bulk_operation_tracking_status ON dataflow_classification.bulk_operation_tracking(status);
CREATE INDEX IF NOT EXISTS idx_bulk_operation_tracking_started_at ON dataflow_classification.bulk_operation_tracking(started_at);

-- Create stored functions for DataFlow operations

-- Function to calculate node performance metrics
CREATE OR REPLACE FUNCTION dataflow_classification.calculate_node_performance(
    model_name_param VARCHAR(100) DEFAULT NULL,
    time_window_hours INTEGER DEFAULT 24
)
RETURNS TABLE(
    node_name VARCHAR(100),
    model_name VARCHAR(100),
    avg_execution_time_ms DECIMAL(10,2),
    max_execution_time_ms DECIMAL(10,2),
    total_executions INTEGER,
    total_records_processed BIGINT,
    avg_records_per_second DECIMAL(10,2),
    cache_hit_ratio DECIMAL(5,4),
    error_ratio DECIMAL(5,4)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        nes.node_name,
        nes.model_name,
        ROUND(AVG(nes.execution_time_ms), 2) as avg_execution_time_ms,
        ROUND(MAX(nes.execution_time_ms), 2) as max_execution_time_ms,
        COUNT(*)::INTEGER as total_executions,
        SUM(nes.records_processed)::BIGINT as total_records_processed,
        ROUND(AVG(nes.records_per_second), 2) as avg_records_per_second,
        ROUND(
            CASE 
                WHEN COUNT(*) > 0 
                THEN SUM(CASE WHEN nes.cache_hit THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)
                ELSE 0.0000
            END, 4
        ) as cache_hit_ratio,
        ROUND(
            CASE 
                WHEN COUNT(*) > 0 
                THEN SUM(CASE WHEN nes.error_occurred THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)
                ELSE 0.0000
            END, 4
        ) as error_ratio
    FROM dataflow_classification.node_execution_stats nes
    WHERE nes.executed_at >= NOW() - (time_window_hours || ' hours')::INTERVAL
        AND (model_name_param IS NULL OR nes.model_name = model_name_param)
    GROUP BY nes.node_name, nes.model_name
    ORDER BY avg_execution_time_ms ASC;
END;
$$ LANGUAGE plpgsql;

-- Function to get DataFlow system health
CREATE OR REPLACE FUNCTION dataflow_classification.get_system_health()
RETURNS TABLE(
    component VARCHAR(100),
    status VARCHAR(20),
    metric_value DECIMAL(15,4),
    last_check TIMESTAMPTZ,
    details JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'PostgreSQL Extensions'::VARCHAR(100) as component,
        CASE WHEN COUNT(*) >= 6 THEN 'healthy' ELSE 'warning' END::VARCHAR(20) as status,
        COUNT(*)::DECIMAL(15,4) as metric_value,
        NOW() as last_check,
        jsonb_build_object(
            'installed_extensions', array_agg(extname),
            'required_extensions', ARRAY['uuid-ossp', 'pg_stat_statements', 'pgcrypto', 'pg_trgm', 'btree_gin', 'vector']
        ) as details
    FROM pg_extension 
    WHERE extname IN ('uuid-ossp', 'pg_stat_statements', 'pgcrypto', 'pg_trgm', 'btree_gin', 'vector')
    
    UNION ALL
    
    SELECT 
        'DataFlow Models'::VARCHAR(100) as component,
        CASE WHEN COUNT(*) > 0 THEN 'healthy' ELSE 'error' END::VARCHAR(20) as status,
        COUNT(*)::DECIMAL(15,4) as metric_value,
        NOW() as last_check,
        jsonb_build_object(
            'registered_models', array_agg(model_name),
            'total_models', COUNT(*)
        ) as details
    FROM dataflow_classification.model_metadata
    
    UNION ALL
    
    SELECT 
        'Database Performance'::VARCHAR(100) as component,
        CASE 
            WHEN AVG(execution_time_ms) < 100 THEN 'healthy'
            WHEN AVG(execution_time_ms) < 500 THEN 'warning'
            ELSE 'error'
        END::VARCHAR(20) as status,
        ROUND(AVG(execution_time_ms), 2)::DECIMAL(15,4) as metric_value,
        NOW() as last_check,
        jsonb_build_object(
            'avg_execution_time_ms', ROUND(AVG(execution_time_ms), 2),
            'total_operations_24h', COUNT(*),
            'error_ratio', ROUND(SUM(CASE WHEN error_occurred THEN 1 ELSE 0 END)::DECIMAL / COUNT(*), 4)
        ) as details
    FROM dataflow_classification.node_execution_stats
    WHERE executed_at >= NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

-- Function to register DataFlow model
CREATE OR REPLACE FUNCTION dataflow_classification.register_model(
    model_name_param VARCHAR(100),
    schema_hash_param VARCHAR(64),
    indexes_count_param INTEGER DEFAULT 0
)
RETURNS UUID AS $$
DECLARE
    model_id UUID;
BEGIN
    INSERT INTO dataflow_classification.model_metadata 
        (model_name, schema_hash, indexes_count, updated_at)
    VALUES 
        (model_name_param, schema_hash_param, indexes_count_param, NOW())
    ON CONFLICT (model_name) 
    DO UPDATE SET 
        schema_hash = EXCLUDED.schema_hash,
        indexes_count = EXCLUDED.indexes_count,
        updated_at = NOW()
    RETURNING id INTO model_id;
    
    RETURN model_id;
END;
$$ LANGUAGE plpgsql;

-- Create initial DataFlow models metadata
INSERT INTO dataflow_classification.model_metadata 
    (model_name, schema_hash, indexes_count, performance_level, cache_enabled)
VALUES 
    ('Company', md5('Company_v1.0'), 9, 'high', true),
    ('User', md5('User_v1.0'), 8, 'high', true),
    ('Customer', md5('Customer_v1.0'), 13, 'high', true),
    ('Quote', md5('Quote_v1.0'), 11, 'high', true),
    ('ProductClassification', md5('ProductClassification_v1.0'), 11, 'critical', true),
    ('ClassificationHistory', md5('ClassificationHistory_v1.0'), 7, 'standard', false),
    ('ClassificationCache', md5('ClassificationCache_v1.0'), 8, 'critical', true),
    ('ETIMAttribute', md5('ETIMAttribute_v1.0'), 11, 'high', true),
    ('ClassificationRule', md5('ClassificationRule_v1.0'), 9, 'high', true),
    ('ClassificationFeedback', md5('ClassificationFeedback_v1.0'), 8, 'standard', true),
    ('ClassificationMetrics', md5('ClassificationMetrics_v1.0'), 6, 'standard', true),
    ('Document', md5('Document_v1.0'), 5, 'standard', true),
    ('DocumentProcessingQueue', md5('DocumentProcessingQueue_v1.0'), 3, 'standard', false)
ON CONFLICT (model_name) DO NOTHING;

-- Grant permissions to DataFlow users
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dataflow_classification TO horme_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA dataflow_classification TO horme_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dataflow_classification TO horme_user;

-- Grant read-only access to monitoring user
GRANT SELECT ON ALL TABLES IN SCHEMA dataflow_classification TO dataflow_monitor;
GRANT EXECUTE ON FUNCTION dataflow_classification.calculate_node_performance TO dataflow_monitor;
GRANT EXECUTE ON FUNCTION dataflow_classification.get_system_health TO dataflow_monitor;

-- Grant backup access
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dataflow_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA dataflow_classification TO dataflow_backup;

-- Create health check view for Docker containers
CREATE OR REPLACE VIEW dataflow_classification.docker_health_check AS
SELECT 
    'dataflow_docker_ready' as service,
    CASE 
        WHEN 
            (SELECT COUNT(*) FROM pg_extension WHERE extname IN ('vector', 'pg_trgm', 'btree_gin')) >= 3
            AND
            (SELECT COUNT(*) FROM dataflow_classification.model_metadata) >= 10
        THEN 'ready'
        ELSE 'not_ready'
    END as status,
    NOW() as checked_at,
    jsonb_build_object(
        'extensions_ready', (SELECT COUNT(*) FROM pg_extension WHERE extname IN ('vector', 'pg_trgm', 'btree_gin')),
        'models_registered', (SELECT COUNT(*) FROM dataflow_classification.model_metadata),
        'database_name', current_database(),
        'postgres_version', version()
    ) as details;

-- Grant access to health check view
GRANT SELECT ON dataflow_classification.docker_health_check TO horme_user;
GRANT SELECT ON dataflow_classification.docker_health_check TO dataflow_monitor;

-- Final optimization: Update all table statistics  
ANALYZE;

-- Success confirmation
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'DataFlow Docker PostgreSQL initialized successfully at %', NOW();
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'Extensions installed: %', (SELECT COUNT(*) FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_stat_statements', 'pgcrypto', 'pg_trgm', 'btree_gin', 'vector'));
    RAISE NOTICE 'DataFlow models registered: %', (SELECT COUNT(*) FROM dataflow_classification.model_metadata);
    RAISE NOTICE 'Performance optimizations: Applied';
    RAISE NOTICE 'Container health check: Available';
    RAISE NOTICE 'Docker service names: Configured';
    RAISE NOTICE '========================================';
END
$$;