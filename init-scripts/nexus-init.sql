-- Nexus Platform Database Initialization
-- Creates necessary extensions and basic schema

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create application schema
CREATE SCHEMA IF NOT EXISTS nexus;

-- Create sessions table for multi-channel session management
CREATE TABLE IF NOT EXISTS nexus.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    channel VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    data JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(20) DEFAULT 'active'
);

-- Create workflows table for workflow registry
CREATE TABLE IF NOT EXISTS nexus.workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    definition JSONB NOT NULL,
    version VARCHAR(50) DEFAULT '1.0.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    tags TEXT[]
);

-- Create executions table for workflow execution tracking
CREATE TABLE IF NOT EXISTS nexus.executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_name VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    channel VARCHAR(50) NOT NULL,
    parameters JSONB DEFAULT '{}'::jsonb,
    results JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    execution_time_ms INTEGER
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON nexus.sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_workflows_name ON nexus.workflows(name);
CREATE INDEX IF NOT EXISTS idx_executions_run_id ON nexus.executions(run_id);

-- Insert default health check workflow
INSERT INTO nexus.workflows (name, description, definition, created_by, tags) 
VALUES (
    'health_check',
    'System health check workflow',
    '{"nodes": [{"type": "PythonCodeNode", "id": "health", "parameters": {"code": "result = {\"status\": \"healthy\", \"version\": \"1.0.0\"}"}}], "edges": []}',
    'system',
    ARRAY['system', 'health']
) ON CONFLICT (name) DO NOTHING;
