-- DataFlow Import Monitoring Queries
-- Real-time monitoring of the import process

\echo '=================================================='
\echo 'DataFlow Import Progress Monitor'
\echo '=================================================='

-- Current timestamp
SELECT 'Current Time: ' || NOW()::TEXT as status;

-- Overall import statistics
\echo ''
\echo 'Overall Import Statistics:'
\echo '--------------------------'
SELECT * FROM get_import_stats();

-- Detailed table counts
\echo ''
\echo 'Table Record Counts:'
\echo '--------------------'
SELECT * FROM import_progress ORDER BY table_name;

-- Recent import activity (last 10 operations)
\echo ''
\echo 'Recent Import Activity:'
\echo '-----------------------'
SELECT 
    timestamp,
    operation,
    records_processed,
    records_total,
    CASE 
        WHEN records_total > 0 
        THEN ROUND((records_processed::float / records_total * 100), 1) || '%'
        ELSE 'N/A' 
    END as progress,
    status,
    execution_time_ms || 'ms' as duration,
    COALESCE(message, 'No message') as message
FROM import_monitoring 
ORDER BY timestamp DESC 
LIMIT 10;

-- Current import status by operation
\echo ''
\echo 'Current Status by Operation:'
\echo '----------------------------'
SELECT 
    operation,
    current_records || '/' || total_records as progress,
    progress_percentage || '%' as completion,
    current_status as status,
    last_update
FROM current_import_status;

-- Database performance metrics
\echo ''
\echo 'Database Performance:'
\echo '---------------------'
SELECT 
    'Active Connections' as metric,
    COUNT(*) as value
FROM pg_stat_activity 
WHERE state = 'active'
UNION ALL
SELECT 
    'Database Size',
    pg_size_pretty(pg_database_size(current_database()))
UNION ALL
SELECT 
    'Shared Buffers Hit Ratio',
    ROUND(
        100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2
    )::TEXT || '%'
FROM pg_stat_database 
WHERE datname = current_database();

-- Top queries by execution time (if pg_stat_statements is available)
\echo ''
\echo 'Recent Query Performance:'
\echo '-------------------------'
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements') THEN
        PERFORM 1;
        RAISE NOTICE 'Top queries by mean execution time:';
    ELSE
        RAISE NOTICE 'pg_stat_statements extension not available';
    END IF;
END $$;

-- Show table sizes for imported data
\echo ''
\echo 'Table Sizes:'
\echo '------------'
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('products', 'categories', 'brands', 'import_monitoring')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Sample of recently imported products
\echo ''
\echo 'Sample Recent Products:'
\echo '-----------------------'
SELECT 
    sku,
    LEFT(name, 50) || CASE WHEN LENGTH(name) > 50 THEN '...' ELSE '' END as name,
    status,
    created_at
FROM products 
WHERE deleted_at IS NULL
ORDER BY created_at DESC 
LIMIT 5;

\echo '=================================================='
\echo 'Monitor Update Complete'
\echo '=================================================='