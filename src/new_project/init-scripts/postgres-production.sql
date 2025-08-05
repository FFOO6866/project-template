-- PostgreSQL Production Initialization for Nexus Platform
-- Optimized for high-performance DataFlow operations

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create production schema
CREATE SCHEMA IF NOT EXISTS nexus_production;

-- Create monitoring user
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'nexus_monitor') THEN
        CREATE USER nexus_monitor WITH PASSWORD 'monitor_password';
    END IF;
END
$$;

-- Grant monitoring permissions
GRANT CONNECT ON DATABASE horme_classification_db TO nexus_monitor;
GRANT USAGE ON SCHEMA public TO nexus_monitor;
GRANT USAGE ON SCHEMA nexus_production TO nexus_monitor;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nexus_monitor;
GRANT SELECT ON ALL TABLES IN SCHEMA nexus_production TO nexus_monitor;

-- Performance optimization settings
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET track_activity_query_size = 4096;
ALTER SYSTEM SET track_io_timing = on;

-- Connection pooling optimization
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET superuser_reserved_connections = 3;

-- Memory optimization
ALTER SYSTEM SET shared_buffers = '512MB';
ALTER SYSTEM SET effective_cache_size = '2GB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET work_mem = '8MB';

-- WAL optimization
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.7;
ALTER SYSTEM SET min_wal_size = '1GB';  
ALTER SYSTEM SET max_wal_size = '4GB';

-- Query optimization
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET default_statistics_target = 100;

-- Parallel processing
ALTER SYSTEM SET max_worker_processes = 8;
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;
ALTER SYSTEM SET max_parallel_maintenance_workers = 4;

-- Autovacuum optimization
ALTER SYSTEM SET autovacuum_naptime = '30s';
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;
ALTER SYSTEM SET autovacuum_max_workers = 4;

-- Create production tables with optimizations
CREATE TABLE IF NOT EXISTS nexus_production.performance_metrics (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    tags JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON nexus_production.performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON nexus_production.performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_tags ON nexus_production.performance_metrics USING GIN(tags);

-- Session tracking table
CREATE TABLE IF NOT EXISTS nexus_production.user_sessions (
    session_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id INTEGER NOT NULL,
    access_token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    user_agent TEXT,
    ip_address INET,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON nexus_production.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON nexus_production.user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON nexus_production.user_sessions(is_active, last_activity);

-- WebSocket connections tracking
CREATE TABLE IF NOT EXISTS nexus_production.websocket_connections (
    connection_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id INTEGER NOT NULL,
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    connection_metadata JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_websocket_connections_user_id ON nexus_production.websocket_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_websocket_connections_active ON nexus_production.websocket_connections(is_active, last_heartbeat);

-- API request logs
CREATE TABLE IF NOT EXISTS nexus_production.api_request_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    user_id INTEGER,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms DECIMAL(10,2) NOT NULL,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    ip_address INET,
    user_agent TEXT
);

-- Partition by month for performance
CREATE TABLE IF NOT EXISTS nexus_production.api_request_logs_y2025m01 PARTITION OF nexus_production.api_request_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE INDEX IF NOT EXISTS idx_api_request_logs_timestamp ON nexus_production.api_request_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_request_logs_user_id ON nexus_production.api_request_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_request_logs_endpoint ON nexus_production.api_request_logs(endpoint);

-- Cache statistics
CREATE TABLE IF NOT EXISTS nexus_production.cache_statistics (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    cache_type VARCHAR(50) NOT NULL, -- 'redis', 'local', 'model_specific'
    model_name VARCHAR(100),
    hit_count INTEGER DEFAULT 0,
    miss_count INTEGER DEFAULT 0,
    eviction_count INTEGER DEFAULT 0,
    memory_usage_bytes BIGINT DEFAULT 0,
    avg_response_time_ms DECIMAL(10,2) DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_cache_statistics_timestamp ON nexus_production.cache_statistics(timestamp);
CREATE INDEX IF NOT EXISTS idx_cache_statistics_type_model ON nexus_production.cache_statistics(cache_type, model_name);

-- Bulk operation tracking
CREATE TABLE IF NOT EXISTS nexus_production.bulk_operations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id INTEGER NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    total_records INTEGER NOT NULL,
    processed_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    execution_time_ms INTEGER,
    throughput_records_per_second DECIMAL(10,2),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_bulk_operations_user_id ON nexus_production.bulk_operations(user_id);
CREATE INDEX IF NOT EXISTS idx_bulk_operations_status ON nexus_production.bulk_operations(status);
CREATE INDEX IF NOT EXISTS idx_bulk_operations_started_at ON nexus_production.bulk_operations(started_at);

-- Create stored procedures for common operations

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION nexus_production.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM nexus_production.user_sessions 
    WHERE expires_at < NOW() OR (is_active = FALSE AND last_activity < NOW() - INTERVAL '24 hours');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    INSERT INTO nexus_production.performance_metrics (metric_name, metric_value, tags)
    VALUES ('sessions_cleaned_up', deleted_count, '{"source": "cleanup_job"}'::jsonb);
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate cache hit ratios
CREATE OR REPLACE FUNCTION nexus_production.calculate_cache_hit_ratio(
    cache_type_param VARCHAR(50) DEFAULT NULL,
    time_window_hours INTEGER DEFAULT 24
)
RETURNS TABLE(
    cache_type VARCHAR(50),
    model_name VARCHAR(100),
    hit_ratio DECIMAL(5,4),
    total_requests INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cs.cache_type,
        cs.model_name,
        CASE 
            WHEN (cs.hit_count + cs.miss_count) > 0 
            THEN ROUND(cs.hit_count::DECIMAL / (cs.hit_count + cs.miss_count), 4)
            ELSE 0.0000
        END as hit_ratio,
        (cs.hit_count + cs.miss_count) as total_requests
    FROM nexus_production.cache_statistics cs
    WHERE cs.timestamp >= NOW() - (time_window_hours || ' hours')::INTERVAL
        AND (cache_type_param IS NULL OR cs.cache_type = cache_type_param)
    GROUP BY cs.cache_type, cs.model_name, cs.hit_count, cs.miss_count
    ORDER BY hit_ratio DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get performance summary
CREATE OR REPLACE FUNCTION nexus_production.get_performance_summary(
    time_window_hours INTEGER DEFAULT 24
)
RETURNS TABLE(
    metric_category VARCHAR(100),
    avg_value DECIMAL(15,4),
    max_value DECIMAL(15,4),
    min_value DECIMAL(15,4),
    sample_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pm.metric_name as metric_category,
        ROUND(AVG(pm.metric_value), 4) as avg_value,
        ROUND(MAX(pm.metric_value), 4) as max_value,
        ROUND(MIN(pm.metric_value), 4) as min_value,
        COUNT(*)::INTEGER as sample_count
    FROM nexus_production.performance_metrics pm
    WHERE pm.timestamp >= NOW() - (time_window_hours || ' hours')::INTERVAL
    GROUP BY pm.metric_name
    ORDER BY pm.metric_name;
END;
$$ LANGUAGE plpgsql;

-- Create automated cleanup job (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-expired-sessions', '0 */6 * * *', 'SELECT nexus_production.cleanup_expired_sessions();');

-- Insert initial performance metrics
INSERT INTO nexus_production.performance_metrics (metric_name, metric_value, tags)
VALUES 
    ('database_initialized', 1, '{"version": "2.0", "environment": "production"}'::jsonb),
    ('connection_pool_size', 75, '{"type": "base_pool"}'::jsonb),
    ('connection_pool_overflow', 150, '{"type": "overflow_pool"}'::jsonb);

-- Grant permissions to application user
GRANT USAGE ON SCHEMA nexus_production TO horme_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA nexus_production TO horme_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA nexus_production TO horme_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA nexus_production TO horme_user;

-- Final optimization: Update table statistics
ANALYZE;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Nexus Production Database initialized successfully at %', NOW();
    RAISE NOTICE 'Performance optimizations applied';
    RAISE NOTICE 'Monitoring tables created';
    RAISE NOTICE 'Stored procedures installed';
END
$$;