-- Horme POV System - Production Database Initialization
-- ====================================================
-- This script initializes the production database with all required schemas,
-- tables, indexes, and permissions for the complete Horme POV system.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create application schemas
CREATE SCHEMA IF NOT EXISTS nexus;
CREATE SCHEMA IF NOT EXISTS dataflow;
CREATE SCHEMA IF NOT EXISTS mcp;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- =============================================================================
-- NEXUS PLATFORM TABLES
-- =============================================================================

-- Users and authentication
CREATE TABLE IF NOT EXISTS nexus.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- API keys and tokens
CREATE TABLE IF NOT EXISTS nexus.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES nexus.users(id) ON DELETE CASCADE,
    key_name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    permissions JSONB DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE
);

-- Workflow executions
CREATE TABLE IF NOT EXISTS nexus.workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES nexus.users(id),
    workflow_name VARCHAR(255) NOT NULL,
    parameters JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB,
    error_message TEXT,
    execution_time_ms INTEGER
);

-- Sessions (for web interface)
CREATE TABLE IF NOT EXISTS nexus.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES nexus.users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- =============================================================================
-- DATAFLOW TABLES - Product Management
-- =============================================================================

-- Products (main product catalog)
CREATE TABLE IF NOT EXISTS dataflow.products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(255),
    subcategory VARCHAR(255),
    brand VARCHAR(255),
    model VARCHAR(255),
    sku VARCHAR(255),
    price DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    availability VARCHAR(50),
    specifications JSONB DEFAULT '{}',
    attributes JSONB DEFAULT '{}',
    images JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Product enrichment data
CREATE TABLE IF NOT EXISTS dataflow.product_enrichment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES dataflow.products(id) ON DELETE CASCADE,
    enrichment_type VARCHAR(100) NOT NULL,
    enrichment_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    source VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_by VARCHAR(255)
);

-- Suppliers
CREATE TABLE IF NOT EXISTS dataflow.suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    website VARCHAR(500),
    contact_info JSONB DEFAULT '{}',
    location JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '{}',
    certifications JSONB DEFAULT '[]',
    rating DECIMAL(3,2),
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Product-Supplier relationships
CREATE TABLE IF NOT EXISTS dataflow.product_suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES dataflow.products(id) ON DELETE CASCADE,
    supplier_id UUID REFERENCES dataflow.suppliers(id) ON DELETE CASCADE,
    supplier_product_id VARCHAR(255),
    price DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    minimum_order_quantity INTEGER,
    lead_time_days INTEGER,
    availability VARCHAR(50),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, supplier_id)
);

-- Quotations
CREATE TABLE IF NOT EXISTS dataflow.quotations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quotation_number VARCHAR(255) UNIQUE NOT NULL,
    customer_id UUID,
    status VARCHAR(50) DEFAULT 'draft',
    items JSONB NOT NULL DEFAULT '[]',
    subtotal DECIMAL(12,2),
    tax_amount DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    valid_until DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES nexus.users(id)
);

-- =============================================================================
-- MCP SERVER TABLES
-- =============================================================================

-- MCP connections and clients
CREATE TABLE IF NOT EXISTS mcp.connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id VARCHAR(255) UNIQUE NOT NULL,
    client_info JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '{}',
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'
);

-- MCP tool executions
CREATE TABLE IF NOT EXISTS mcp.tool_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID REFERENCES mcp.connections(id),
    tool_name VARCHAR(255) NOT NULL,
    parameters JSONB DEFAULT '{}',
    result JSONB,
    execution_time_ms INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- MONITORING AND LOGGING TABLES
-- =============================================================================

-- System metrics
CREATE TABLE IF NOT EXISTS monitoring.system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(12,4) NOT NULL,
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Application logs
CREATE TABLE IF NOT EXISTS monitoring.application_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    trace_id VARCHAR(255),
    span_id VARCHAR(255)
);

-- Health checks
CREATE TABLE IF NOT EXISTS monitoring.health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    check_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_time_ms INTEGER,
    details JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Nexus indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON nexus.users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON nexus.users(email);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON nexus.api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_user_id ON nexus.workflow_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON nexus.workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON nexus.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON nexus.sessions(session_token);

-- DataFlow indexes
CREATE INDEX IF NOT EXISTS idx_products_product_id ON dataflow.products(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON dataflow.products(category);
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON dataflow.products USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_products_active ON dataflow.products(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_product_enrichment_product_id ON dataflow.product_enrichment(product_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_supplier_id ON dataflow.suppliers(supplier_id);
CREATE INDEX IF NOT EXISTS idx_product_suppliers_product_id ON dataflow.product_suppliers(product_id);
CREATE INDEX IF NOT EXISTS idx_product_suppliers_supplier_id ON dataflow.product_suppliers(supplier_id);
CREATE INDEX IF NOT EXISTS idx_quotations_number ON dataflow.quotations(quotation_number);
CREATE INDEX IF NOT EXISTS idx_quotations_status ON dataflow.quotations(status);

-- MCP indexes
CREATE INDEX IF NOT EXISTS idx_connections_connection_id ON mcp.connections(connection_id);
CREATE INDEX IF NOT EXISTS idx_connections_active ON mcp.connections(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_tool_executions_connection_id ON mcp.tool_executions(connection_id);
CREATE INDEX IF NOT EXISTS idx_tool_executions_tool_name ON mcp.tool_executions(tool_name);

-- Monitoring indexes
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON monitoring.system_metrics(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_application_logs_service_timestamp ON monitoring.application_logs(service_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_application_logs_level ON monitoring.application_logs(level);
CREATE INDEX IF NOT EXISTS idx_health_checks_service_timestamp ON monitoring.health_checks(service_name, timestamp);

-- =============================================================================
-- STORED PROCEDURES AND FUNCTIONS
-- =============================================================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
DROP TRIGGER IF EXISTS update_products_updated_at ON dataflow.products;
CREATE TRIGGER update_products_updated_at 
    BEFORE UPDATE ON dataflow.products 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_suppliers_updated_at ON dataflow.suppliers;
CREATE TRIGGER update_suppliers_updated_at 
    BEFORE UPDATE ON dataflow.suppliers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_quotations_updated_at ON dataflow.quotations;
CREATE TRIGGER update_quotations_updated_at 
    BEFORE UPDATE ON dataflow.quotations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to generate quotation numbers
CREATE OR REPLACE FUNCTION generate_quotation_number()
RETURNS TEXT AS $$
DECLARE
    new_number TEXT;
    current_date_part TEXT;
    sequence_part INTEGER;
BEGIN
    current_date_part := TO_CHAR(CURRENT_DATE, 'YYYYMMDD');
    
    SELECT COALESCE(MAX(
        CAST(SUBSTRING(quotation_number FROM 10) AS INTEGER)
    ), 0) + 1
    INTO sequence_part
    FROM dataflow.quotations
    WHERE quotation_number LIKE 'Q' || current_date_part || '%';
    
    new_number := 'Q' || current_date_part || LPAD(sequence_part::TEXT, 4, '0');
    
    RETURN new_number;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- INITIAL DATA AND CONFIGURATION
-- =============================================================================

-- Create default admin user (password: admin123 - CHANGE IN PRODUCTION!)
INSERT INTO nexus.users (username, email, password_hash, is_admin) 
VALUES (
    'admin',
    'admin@horme.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XY5KYzYLQ1MS', -- admin123
    true
) ON CONFLICT (username) DO NOTHING;

-- Create default API key for testing
INSERT INTO nexus.api_keys (user_id, key_name, key_hash, permissions)
SELECT 
    u.id,
    'default-test-key',
    '$2b$12$test_api_key_hash_change_in_production',
    '{"read": true, "write": true, "admin": false}'::jsonb
FROM nexus.users u 
WHERE u.username = 'admin'
ON CONFLICT DO NOTHING;

-- Insert sample product categories
INSERT INTO dataflow.products (product_id, name, category, subcategory, description, price) VALUES
    ('SAMPLE-001', 'Sample Product 1', 'Electronics', 'Components', 'Sample electronic component for testing', 29.99),
    ('SAMPLE-002', 'Sample Product 2', 'Industrial', 'Tools', 'Sample industrial tool for testing', 149.99),
    ('SAMPLE-003', 'Sample Product 3', 'Materials', 'Raw Materials', 'Sample raw material for testing', 9.99)
ON CONFLICT (product_id) DO NOTHING;

-- =============================================================================
-- PERFORMANCE OPTIMIZATION
-- =============================================================================

-- Analyze all tables for query optimization
ANALYZE nexus.users;
ANALYZE nexus.api_keys;
ANALYZE nexus.workflow_executions;
ANALYZE nexus.sessions;
ANALYZE dataflow.products;
ANALYZE dataflow.product_enrichment;
ANALYZE dataflow.suppliers;
ANALYZE dataflow.product_suppliers;
ANALYZE dataflow.quotations;
ANALYZE mcp.connections;
ANALYZE mcp.tool_executions;
ANALYZE monitoring.system_metrics;
ANALYZE monitoring.application_logs;
ANALYZE monitoring.health_checks;

-- =============================================================================
-- SECURITY AND PERMISSIONS
-- =============================================================================

-- Create application roles
CREATE ROLE IF NOT EXISTS horme_app_read;
CREATE ROLE IF NOT EXISTS horme_app_write;
CREATE ROLE IF NOT EXISTS horme_app_admin;

-- Grant schema permissions
GRANT USAGE ON SCHEMA nexus TO horme_app_read, horme_app_write, horme_app_admin;
GRANT USAGE ON SCHEMA dataflow TO horme_app_read, horme_app_write, horme_app_admin;
GRANT USAGE ON SCHEMA mcp TO horme_app_read, horme_app_write, horme_app_admin;
GRANT USAGE ON SCHEMA monitoring TO horme_app_read, horme_app_write, horme_app_admin;

-- Grant table permissions
-- Read permissions
GRANT SELECT ON ALL TABLES IN SCHEMA nexus TO horme_app_read;
GRANT SELECT ON ALL TABLES IN SCHEMA dataflow TO horme_app_read;
GRANT SELECT ON ALL TABLES IN SCHEMA mcp TO horme_app_read;
GRANT SELECT ON ALL TABLES IN SCHEMA monitoring TO horme_app_read;

-- Write permissions (includes read)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA nexus TO horme_app_write;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA dataflow TO horme_app_write;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mcp TO horme_app_write;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA monitoring TO horme_app_write;

-- Admin permissions (includes write)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA nexus TO horme_app_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dataflow TO horme_app_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA mcp TO horme_app_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA monitoring TO horme_app_admin;

-- Grant sequence permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA nexus TO horme_app_write, horme_app_admin;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dataflow TO horme_app_write, horme_app_admin;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA mcp TO horme_app_write, horme_app_admin;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA monitoring TO horme_app_write, horme_app_admin;

-- Grant function permissions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA nexus TO horme_app_write, horme_app_admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dataflow TO horme_app_write, horme_app_admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA mcp TO horme_app_write, horme_app_admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA monitoring TO horme_app_write, horme_app_admin;

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '================================================================';
    RAISE NOTICE 'Horme POV System Database Initialization Complete';
    RAISE NOTICE '================================================================';
    RAISE NOTICE 'Database initialized with:';
    RAISE NOTICE '• 4 schemas: nexus, dataflow, mcp, monitoring';
    RAISE NOTICE '• 13 tables with proper relationships and constraints';
    RAISE NOTICE '• Performance indexes for all major queries';
    RAISE NOTICE '• Security roles and permissions';
    RAISE NOTICE '• Sample data for testing';
    RAISE NOTICE '• Automated triggers for timestamp management';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Change default admin password';
    RAISE NOTICE '2. Create production API keys';
    RAISE NOTICE '3. Configure monitoring and logging';
    RAISE NOTICE '4. Run validation tests';
    RAISE NOTICE '================================================================';
END
$$;