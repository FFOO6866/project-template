-- ============================================================================
-- Database Initialization Script
-- Dynamic Job Pricing Engine
-- ============================================================================
-- This script runs automatically when PostgreSQL container starts
-- It creates the database, user, and grants necessary permissions
-- ============================================================================

-- Create database (if it doesn't exist)
SELECT 'CREATE DATABASE job_pricing_db WITH ENCODING ''UTF8'' LC_COLLATE ''en_US.utf8'' LC_CTYPE ''en_US.utf8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'job_pricing_db')\gexec

-- Note: User creation is handled by docker-compose environment variables
-- POSTGRES_USER and POSTGRES_PASSWORD from .env

-- Connect to the job_pricing_db database
\c job_pricing_db

-- Grant all privileges to the user (set via POSTGRES_USER in .env)
GRANT ALL PRIVILEGES ON DATABASE job_pricing_db TO :POSTGRES_USER;
GRANT ALL PRIVILEGES ON SCHEMA public TO :POSTGRES_USER;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO :POSTGRES_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO :POSTGRES_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO :POSTGRES_USER;

-- ============================================================================
-- Database Configuration
-- ============================================================================

-- Enable logging for better debugging
ALTER DATABASE job_pricing_db SET log_statement = 'all';
ALTER DATABASE job_pricing_db SET log_duration = on;

-- Set timezone to UTC (CRITICAL for consistency)
ALTER DATABASE job_pricing_db SET timezone = 'UTC';

-- Optimize for read-heavy workload with some writes
ALTER DATABASE job_pricing_db SET shared_buffers = '256MB';
ALTER DATABASE job_pricing_db SET effective_cache_size = '1GB';
ALTER DATABASE job_pricing_db SET maintenance_work_mem = '128MB';
ALTER DATABASE job_pricing_db SET work_mem = '16MB';

-- ============================================================================
-- Success Message
-- ============================================================================
\echo 'Database job_pricing_db initialized successfully'
\echo 'Timezone: UTC'
\echo 'Encoding: UTF8'
\echo 'Ready for extensions and schema installation'
