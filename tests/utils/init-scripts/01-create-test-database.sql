-- Initialize Horme POV Test Database
-- This script sets up the complete database schema for testing

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create main schema
CREATE SCHEMA IF NOT EXISTS horme;

-- Create users table
CREATE TABLE IF NOT EXISTS horme.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Create categories table
CREATE TABLE IF NOT EXISTS horme.categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES horme.categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create brands table
CREATE TABLE IF NOT EXISTS horme.brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create products table
CREATE TABLE IF NOT EXISTS horme.products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    enriched_description TEXT,
    technical_specs TEXT,
    category_id INTEGER REFERENCES horme.categories(id),
    brand_id INTEGER REFERENCES horme.brands(id),
    currency VARCHAR(10) DEFAULT 'USD',
    availability VARCHAR(50) DEFAULT 'in_stock',
    is_published BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embeddings VECTOR(1536) -- OpenAI embedding dimension
);

-- Create product_pricing table
CREATE TABLE IF NOT EXISTS horme.product_pricing (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES horme.products(id) ON DELETE CASCADE,
    list_price DECIMAL(10,2),
    cost_price DECIMAL(10,2),
    discount_price DECIMAL(10,2),
    effective_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create quotations table
CREATE TABLE IF NOT EXISTS horme.quotations (
    id SERIAL PRIMARY KEY,
    quote_number VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES horme.users(id),
    status VARCHAR(50) DEFAULT 'draft',
    total_amount DECIMAL(10,2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'USD',
    valid_until TIMESTAMP,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create quotation_items table  
CREATE TABLE IF NOT EXISTS horme.quotation_items (
    id SERIAL PRIMARY KEY,
    quotation_id INTEGER REFERENCES horme.quotations(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES horme.products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create documents table for file uploads
CREATE TABLE IF NOT EXISTS horme.documents (
    id SERIAL PRIMARY KEY,
    original_name VARCHAR(255) NOT NULL,
    stored_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100),
    checksum VARCHAR(255),
    user_id INTEGER REFERENCES horme.users(id),
    status VARCHAR(50) DEFAULT 'uploaded',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create processing_jobs table for background processing
CREATE TABLE IF NOT EXISTS horme.processing_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES horme.users(id),
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    message TEXT,
    context_id VARCHAR(255),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create search_cache table for search optimization
CREATE TABLE IF NOT EXISTS horme.search_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    query_hash VARCHAR(255) NOT NULL,
    results JSONB NOT NULL,
    result_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Create FTS5 virtual table for full-text search (PostgreSQL equivalent)
-- Using GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_products_fts ON horme.products 
USING GIN (to_tsvector('english', 
    COALESCE(name, '') || ' ' || 
    COALESCE(description, '') || ' ' || 
    COALESCE(enriched_description, '') || ' ' ||
    COALESCE(technical_specs, '')
));

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_category ON horme.products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_brand ON horme.products(brand_id);
CREATE INDEX IF NOT EXISTS idx_products_sku ON horme.products(sku);
CREATE INDEX IF NOT EXISTS idx_products_published ON horme.products(is_published);
CREATE INDEX IF NOT EXISTS idx_quotations_user ON horme.quotations(user_id);
CREATE INDEX IF NOT EXISTS idx_quotations_status ON horme.quotations(status);
CREATE INDEX IF NOT EXISTS idx_quotation_items_quotation ON horme.quotation_items(quotation_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON horme.processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_documents_user ON horme.documents(user_id);

-- Create vector similarity search index
CREATE INDEX IF NOT EXISTS idx_products_embeddings ON horme.products 
USING ivfflat (embeddings vector_cosine_ops) WITH (lists = 100);

-- Insert test data
INSERT INTO horme.categories (name, slug, description) VALUES
('Electronics', 'electronics', 'Electronic components and devices'),
('Tools', 'tools', 'Hand tools and power tools'),
('Materials', 'materials', 'Building and construction materials'),
('Safety', 'safety', 'Safety equipment and protective gear'),
('HVAC', 'hvac', 'Heating, ventilation, and air conditioning'),
('Electrical', 'electrical', 'Electrical components and supplies')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO horme.brands (name, slug, description, website) VALUES
('TestBrand', 'testbrand', 'Test brand for integration testing', 'https://testbrand.com'),
('QualityTools', 'qualitytools', 'High quality tools and equipment', 'https://qualitytools.com'),
('SafetyFirst', 'safetyfirst', 'Professional safety equipment', 'https://safetyfirst.com'),
('TechComponents', 'techcomponents', 'Electronic components supplier', 'https://techcomponents.com')
ON CONFLICT (slug) DO NOTHING;

-- Create test user
INSERT INTO horme.users (email, name, password_hash, is_active) VALUES
('test@example.com', 'Test User', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewHdz9WQV6aNxhUC', true)
ON CONFLICT (email) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA horme TO test_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA horme TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA horme TO test_user;