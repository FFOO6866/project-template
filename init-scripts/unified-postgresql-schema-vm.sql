-- Unified PostgreSQL Schema for Horme POV (VM-Optimized)
-- Database initialization with connection pooling support

-- Set connection parameters for better VM performance
SET shared_preload_libraries = 'pg_stat_statements';
SET log_statement = 'ddl';
SET log_min_duration_statement = 1000; -- Log queries taking > 1 second

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For full-text search

-- Drop existing tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS document_analysis CASCADE;
DROP TABLE IF EXISTS rfp_quotations CASCADE;  
DROP TABLE IF EXISTS work_recommendations CASCADE;
DROP TABLE IF EXISTS supplier_intelligence CASCADE;
DROP TABLE IF EXISTS product_enrichments CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS health_checks CASCADE;

-- Users table for authentication and session management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Indexes for better performance
    CONSTRAINT users_role_check CHECK (role IN ('admin', 'user', 'viewer'))
);

-- Sessions table for session management (VM-optimized)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true
);

-- Suppliers table
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    
    -- Business information
    business_type VARCHAR(100),
    industry VARCHAR(100),
    established_year INTEGER,
    employee_count VARCHAR(50),
    annual_revenue VARCHAR(50),
    
    -- Contact and engagement
    contact_person VARCHAR(255),
    contact_title VARCHAR(100),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    
    -- Metadata
    source VARCHAR(100), -- Where this supplier was discovered
    confidence_score DECIMAL(3,2) DEFAULT 0.00,
    verification_status VARCHAR(20) DEFAULT 'unverified',
    notes TEXT,
    tags TEXT[], -- Array of tags for categorization
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_contacted TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT suppliers_confidence_check CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00),
    CONSTRAINT suppliers_verification_check CHECK (verification_status IN ('verified', 'unverified', 'pending', 'rejected'))
);

-- Products table (enhanced for VM performance)
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    
    -- Basic product information
    name VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    brand VARCHAR(255),
    model VARCHAR(255),
    sku VARCHAR(100),
    barcode VARCHAR(50),
    
    -- Pricing information
    price DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'USD',
    price_unit VARCHAR(50), -- per unit, per kg, etc.
    minimum_order_quantity INTEGER,
    bulk_discount_available BOOLEAN DEFAULT false,
    
    -- Physical specifications
    dimensions_length DECIMAL(10,2),
    dimensions_width DECIMAL(10,2), 
    dimensions_height DECIMAL(10,2),
    weight DECIMAL(10,2),
    color VARCHAR(100),
    material VARCHAR(255),
    
    -- Availability and logistics
    availability_status VARCHAR(20) DEFAULT 'available',
    stock_quantity INTEGER,
    lead_time_days INTEGER,
    shipping_weight DECIMAL(10,2),
    shipping_dimensions VARCHAR(255),
    
    -- Quality and certifications
    certifications TEXT[],
    quality_grade VARCHAR(50),
    warranty_period VARCHAR(100),
    compliance_standards TEXT[],
    
    -- Metadata and enrichment
    image_urls TEXT[],
    specification_urls TEXT[],
    datasheet_url VARCHAR(500),
    source_url VARCHAR(500),
    confidence_score DECIMAL(3,2) DEFAULT 0.00,
    enrichment_status VARCHAR(20) DEFAULT 'pending',
    ai_tags TEXT[],
    search_vector tsvector, -- For full-text search
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_scraped TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT products_availability_check CHECK (availability_status IN ('available', 'unavailable', 'discontinued', 'backorder')),
    CONSTRAINT products_confidence_check CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00),
    CONSTRAINT products_enrichment_check CHECK (enrichment_status IN ('pending', 'processing', 'completed', 'failed'))
);

-- Product enrichments table for AI-enhanced data
CREATE TABLE product_enrichments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    
    -- AI-generated enrichments
    ai_category VARCHAR(100),
    ai_subcategory VARCHAR(100),
    ai_description TEXT,
    ai_features TEXT[],
    ai_applications TEXT[],
    ai_compatibility TEXT[],
    technical_specifications JSONB,
    
    -- Market analysis
    market_price_range VARCHAR(100),
    competitor_products JSONB,
    market_position VARCHAR(50),
    
    -- Quality scores
    description_quality_score DECIMAL(3,2),
    image_quality_score DECIMAL(3,2),
    specification_completeness DECIMAL(3,2),
    overall_quality_score DECIMAL(3,2),
    
    -- Processing metadata
    enrichment_version INTEGER DEFAULT 1,
    processing_time_seconds INTEGER,
    ai_model_used VARCHAR(100),
    confidence_scores JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT enrichments_quality_check CHECK (
        description_quality_score >= 0.00 AND description_quality_score <= 1.00 AND
        image_quality_score >= 0.00 AND image_quality_score <= 1.00 AND
        specification_completeness >= 0.00 AND specification_completeness <= 1.00 AND
        overall_quality_score >= 0.00 AND overall_quality_score <= 1.00
    )
);

-- Supplier intelligence table for AI-driven insights
CREATE TABLE supplier_intelligence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    
    -- Capability analysis
    core_capabilities TEXT[],
    manufacturing_capabilities TEXT[],
    quality_certifications TEXT[],
    geographic_reach TEXT[],
    
    -- Performance metrics
    reliability_score DECIMAL(3,2),
    quality_score DECIMAL(3,2),
    price_competitiveness DECIMAL(3,2),
    delivery_performance DECIMAL(3,2),
    communication_score DECIMAL(3,2),
    overall_score DECIMAL(3,2),
    
    -- Market intelligence
    market_position VARCHAR(50),
    key_competitors TEXT[],
    unique_selling_points TEXT[],
    risk_factors TEXT[],
    opportunities TEXT[],
    
    -- Analysis metadata
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    data_sources TEXT[],
    confidence_level DECIMAL(3,2),
    analyst_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT supplier_intel_scores_check CHECK (
        reliability_score >= 0.00 AND reliability_score <= 1.00 AND
        quality_score >= 0.00 AND quality_score <= 1.00 AND
        price_competitiveness >= 0.00 AND price_competitiveness <= 1.00 AND
        delivery_performance >= 0.00 AND delivery_performance <= 1.00 AND
        communication_score >= 0.00 AND communication_score <= 1.00 AND
        overall_score >= 0.00 AND overall_score <= 1.00 AND
        confidence_level >= 0.00 AND confidence_level <= 1.00
    )
);

-- Work recommendations table for AI-driven project matching
CREATE TABLE work_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Project/RFP context
    project_title VARCHAR(500),
    project_description TEXT,
    project_category VARCHAR(100),
    budget_range VARCHAR(100),
    timeline_weeks INTEGER,
    location VARCHAR(255),
    
    -- Requirements analysis
    required_products JSONB, -- Array of product requirements
    required_capabilities TEXT[],
    technical_requirements JSONB,
    quality_requirements TEXT[],
    compliance_requirements TEXT[],
    
    -- Recommendations
    recommended_suppliers JSONB, -- Array of supplier recommendations with scores
    recommended_products JSONB, -- Array of product recommendations with matches
    alternative_solutions JSONB,
    
    -- Scoring and confidence
    match_confidence DECIMAL(3,2),
    recommendation_type VARCHAR(50),
    priority_score DECIMAL(3,2),
    risk_assessment TEXT[],
    
    -- Processing metadata
    ai_model_version VARCHAR(50),
    processing_time_seconds INTEGER,
    data_sources TEXT[],
    recommendation_basis TEXT,
    
    -- Status and workflow
    status VARCHAR(20) DEFAULT 'generated',
    assigned_to UUID REFERENCES users(id),
    reviewed_by UUID REFERENCES users(id),
    review_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT work_rec_confidence_check CHECK (match_confidence >= 0.00 AND match_confidence <= 1.00),
    CONSTRAINT work_rec_priority_check CHECK (priority_score >= 0.00 AND priority_score <= 1.00),
    CONSTRAINT work_rec_status_check CHECK (status IN ('generated', 'reviewed', 'approved', 'rejected', 'implemented'))
);

-- RFP quotations table for proposal management
CREATE TABLE rfp_quotations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recommendation_id UUID REFERENCES work_recommendations(id),
    supplier_id UUID REFERENCES suppliers(id),
    
    -- RFP information
    rfp_title VARCHAR(500),
    rfp_number VARCHAR(100),
    rfp_description TEXT,
    submission_deadline TIMESTAMP WITH TIME ZONE,
    
    -- Quotation details
    quoted_products JSONB, -- Array of products with quantities and prices
    total_amount DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'USD',
    delivery_timeframe VARCHAR(100),
    validity_period VARCHAR(100),
    
    -- Terms and conditions
    payment_terms VARCHAR(255),
    warranty_terms VARCHAR(255),
    delivery_terms VARCHAR(255),
    special_conditions TEXT,
    
    -- Documents and attachments
    quotation_document_url VARCHAR(500),
    technical_specifications_url VARCHAR(500),
    supporting_documents JSONB,
    
    -- Evaluation and scoring
    technical_score DECIMAL(3,2),
    commercial_score DECIMAL(3,2),
    compliance_score DECIMAL(3,2),
    overall_score DECIMAL(3,2),
    evaluator_notes TEXT,
    
    -- Status and workflow
    status VARCHAR(20) DEFAULT 'draft',
    submitted_at TIMESTAMP WITH TIME ZONE,
    evaluated_at TIMESTAMP WITH TIME ZONE,
    evaluated_by UUID REFERENCES users(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT rfp_scores_check CHECK (
        technical_score >= 0.00 AND technical_score <= 1.00 AND
        commercial_score >= 0.00 AND commercial_score <= 1.00 AND
        compliance_score >= 0.00 AND compliance_score <= 1.00 AND
        overall_score >= 0.00 AND overall_score <= 1.00
    ),
    CONSTRAINT rfp_status_check CHECK (status IN ('draft', 'submitted', 'under_review', 'evaluated', 'awarded', 'rejected'))
);

-- Document analysis table for uploaded document processing
CREATE TABLE document_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Document information
    document_name VARCHAR(500),
    document_type VARCHAR(100),
    file_path VARCHAR(1000),
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    uploaded_by UUID REFERENCES users(id),
    
    -- Analysis results
    extracted_text TEXT,
    document_structure JSONB,
    key_information JSONB,
    entities_extracted JSONB,
    requirements_identified TEXT[],
    
    -- AI processing
    ai_summary TEXT,
    ai_tags TEXT[],
    confidence_scores JSONB,
    processing_time_seconds INTEGER,
    ai_model_used VARCHAR(100),
    
    -- Relationships
    related_recommendations UUID[], -- Array of work_recommendation IDs
    related_products UUID[], -- Array of product IDs
    related_suppliers UUID[], -- Array of supplier IDs
    
    -- Status
    processing_status VARCHAR(20) DEFAULT 'uploaded',
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT doc_status_check CHECK (processing_status IN ('uploaded', 'processing', 'completed', 'failed'))
);

-- Health checks table for infrastructure monitoring
CREATE TABLE health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Check information
    service_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    
    -- Results
    response_time_ms INTEGER,
    details JSONB,
    error_message TEXT,
    
    -- Metadata
    check_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    environment VARCHAR(50) DEFAULT 'production',
    
    CONSTRAINT health_status_check CHECK (status IN ('healthy', 'unhealthy', 'degraded'))
);

-- Create indexes for better performance (VM-optimized)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_active ON sessions(is_active) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_name ON suppliers(name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_company ON suppliers(company);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_industry ON suppliers(industry);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_confidence ON suppliers(confidence_score DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_verification ON suppliers(verification_status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_tags ON suppliers USING gin(tags);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_supplier ON products(supplier_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_category ON products(category, subcategory);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_availability ON products(availability_status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_confidence ON products(confidence_score DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_enrichment ON products(enrichment_status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_search ON products USING gin(search_vector);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_tags ON products USING gin(ai_tags);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enrichments_product ON product_enrichments(product_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_enrichments_quality ON product_enrichments(overall_quality_score DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_supplier_intel_supplier ON supplier_intelligence(supplier_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_supplier_intel_overall_score ON supplier_intelligence(overall_score DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_supplier_intel_analysis_date ON supplier_intelligence(analysis_date DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_rec_category ON work_recommendations(project_category);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_rec_confidence ON work_recommendations(match_confidence DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_rec_status ON work_recommendations(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_rec_assigned ON work_recommendations(assigned_to);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_rec_created ON work_recommendations(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rfp_quotations_supplier ON rfp_quotations(supplier_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rfp_quotations_recommendation ON rfp_quotations(recommendation_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rfp_quotations_status ON rfp_quotations(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rfp_quotations_overall_score ON rfp_quotations(overall_score DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rfp_quotations_deadline ON rfp_quotations(submission_deadline);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_analysis_uploaded_by ON document_analysis(uploaded_by);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_analysis_status ON document_analysis(processing_status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_analysis_type ON document_analysis(document_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_analysis_created ON document_analysis(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_checks_service ON health_checks(service_name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_checks_timestamp ON health_checks(check_timestamp DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_checks_status ON health_checks(status);

-- Create full-text search index for products (VM-optimized)
CREATE OR REPLACE FUNCTION products_search_trigger() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.name, '') || ' ' ||
        COALESCE(NEW.description, '') || ' ' ||
        COALESCE(NEW.category, '') || ' ' ||
        COALESCE(NEW.subcategory, '') || ' ' ||
        COALESCE(NEW.brand, '') || ' ' ||
        COALESCE(NEW.model, '') || ' ' ||
        COALESCE(array_to_string(NEW.ai_tags, ' '), '')
    );
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER products_search_update 
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW 
    EXECUTE FUNCTION products_search_trigger();

-- Create update timestamp triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_product_enrichments_updated_at BEFORE UPDATE ON product_enrichments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_supplier_intelligence_updated_at BEFORE UPDATE ON supplier_intelligence FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_work_recommendations_updated_at BEFORE UPDATE ON work_recommendations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_rfp_quotations_updated_at BEFORE UPDATE ON rfp_quotations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_document_analysis_updated_at BEFORE UPDATE ON document_analysis FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO users (username, email, password_hash, full_name, role) VALUES 
('admin', 'admin@horme.local', '$2b$12$example_hash_here', 'System Administrator', 'admin'),
('demo', 'demo@horme.local', '$2b$12$example_hash_here', 'Demo User', 'user');

-- Insert sample health check data
INSERT INTO health_checks (service_name, check_type, status, response_time_ms, details) VALUES 
('database', 'connectivity', 'healthy', 15, '{"connection_pool": "active", "tables": 9}'),
('redis', 'connectivity', 'healthy', 5, '{"memory_usage": "12MB", "connections": 2}');

-- Grant permissions for application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO current_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO current_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO current_user;

-- Log successful initialization
INSERT INTO health_checks (service_name, check_type, status, response_time_ms, details) VALUES 
('schema_init', 'initialization', 'healthy', 0, '{"schema_version": "1.0.0", "vm_optimized": true, "tables_created": 9}');

-- Performance optimization settings for VM environment
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '512MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Load configuration (requires superuser, will be skipped if not available)
SELECT pg_reload_conf();

COMMIT;