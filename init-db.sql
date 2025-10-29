-- Database Initialization for Clean MCP Server
-- UTF-8 encoding, no Windows-specific features

-- Set UTF-8 encoding
SET client_encoding = 'UTF8';

-- Create basic tables for MCP functionality
CREATE TABLE IF NOT EXISTS mcp_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS mcp_requests (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) REFERENCES mcp_sessions(session_id),
    tool_name VARCHAR(255) NOT NULL,
    parameters JSONB DEFAULT '{}',
    response JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT true,
    execution_time_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mcp_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_type VARCHAR(50) DEFAULT 'counter',
    labels JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_mcp_sessions_agent_id ON mcp_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_mcp_sessions_active ON mcp_sessions(active) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_mcp_requests_session_id ON mcp_requests(session_id);
CREATE INDEX IF NOT EXISTS idx_mcp_requests_tool_name ON mcp_requests(tool_name);
CREATE INDEX IF NOT EXISTS idx_mcp_requests_created_at ON mcp_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_mcp_metrics_name_time ON mcp_metrics(metric_name, recorded_at);

-- Insert some sample data for testing
INSERT INTO mcp_sessions (session_id, agent_id, metadata) VALUES 
('test-session-1', 'test-agent', '{"type": "test", "version": "1.0"}');

-- Create a simple test table
CREATE TABLE IF NOT EXISTS test_data (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    value INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO test_data (name, value) VALUES 
('sample1', 100),
('sample2', 200),
('sample3', 300);

-- Grant permissions (if needed for specific user)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;