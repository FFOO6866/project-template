-- Testing Infrastructure - PostgreSQL Schema Initialization
-- Creates tables for test data and enables pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create products table with vector embeddings
CREATE TABLE IF NOT EXISTS test_products (
    product_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    unspsc_code VARCHAR(20),
    etim_class VARCHAR(20),
    price DECIMAL(10,2) NOT NULL,
    description TEXT,
    safety_standards TEXT[], -- Array of safety standard IDs
    vendor_id VARCHAR(20),
    skill_level_required VARCHAR(20),
    complexity_score INTEGER CHECK (complexity_score BETWEEN 1 AND 10),
    embedding_vector vector(384), -- 384-dimensional vectors for sentence transformers
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create users table
CREATE TABLE IF NOT EXISTS test_users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,
    skill_level VARCHAR(20),
    experience_years INTEGER DEFAULT 0,
    certifications TEXT[],
    safety_training TEXT[],
    preferred_categories TEXT[],
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create safety standards table
CREATE TABLE IF NOT EXISTS test_safety_standards (
    standard_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    organization VARCHAR(50) NOT NULL, -- OSHA, ANSI, ISO, etc.
    category VARCHAR(100) NOT NULL,
    description TEXT,
    requirements TEXT[],
    applicable_products TEXT[], -- Array of product codes
    compliance_level VARCHAR(20) NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user sessions table for testing session management
CREATE TABLE IF NOT EXISTS test_user_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES test_users(user_id) ON DELETE CASCADE,
    session_data JSONB,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create search queries table for performance testing
CREATE TABLE IF NOT EXISTS test_search_queries (
    query_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES test_users(user_id),
    query_type VARCHAR(50) NOT NULL, -- search, recommendation, safety_check
    query_text TEXT,
    query_params JSONB,
    response_time_ms INTEGER,
    results_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance testing
CREATE INDEX IF NOT EXISTS idx_products_category ON test_products(category);
CREATE INDEX IF NOT EXISTS idx_products_skill_level ON test_products(skill_level_required);
CREATE INDEX IF NOT EXISTS idx_products_price ON test_products(price);
CREATE INDEX IF NOT EXISTS idx_products_embedding_vector ON test_products USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_users_skill_level ON test_users(skill_level);
CREATE INDEX IF NOT EXISTS idx_users_role ON test_users(role);
CREATE INDEX IF NOT EXISTS idx_users_location ON test_users(location);

CREATE INDEX IF NOT EXISTS idx_safety_standards_org ON test_safety_standards(organization);
CREATE INDEX IF NOT EXISTS idx_safety_standards_category ON test_safety_standards(category);
CREATE INDEX IF NOT EXISTS idx_safety_standards_compliance ON test_safety_standards(compliance_level);

CREATE INDEX IF NOT EXISTS idx_search_queries_user ON test_search_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_search_queries_type ON test_search_queries(query_type);
CREATE INDEX IF NOT EXISTS idx_search_queries_created ON test_search_queries(created_at);
CREATE INDEX IF NOT EXISTS idx_search_queries_response_time ON test_search_queries(response_time_ms);

-- Create GIN indexes for array columns
CREATE INDEX IF NOT EXISTS idx_products_safety_standards ON test_products USING GIN(safety_standards);
CREATE INDEX IF NOT EXISTS idx_users_certifications ON test_users USING GIN(certifications);
CREATE INDEX IF NOT EXISTS idx_users_safety_training ON test_users USING GIN(safety_training);
CREATE INDEX IF NOT EXISTS idx_users_preferred_categories ON test_users USING GIN(preferred_categories);
CREATE INDEX IF NOT EXISTS idx_safety_standards_requirements ON test_safety_standards USING GIN(requirements);
CREATE INDEX IF NOT EXISTS idx_safety_standards_applicable_products ON test_safety_standards USING GIN(applicable_products);

-- Create text search indexes
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON test_products USING GIN(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_products_description_trgm ON test_products USING GIN(description gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_safety_standards_name_trgm ON test_safety_standards USING GIN(name gin_trgm_ops);

-- Create functions for vector similarity search
CREATE OR REPLACE FUNCTION find_similar_products(
    query_vector vector(384),
    similarity_threshold float8 DEFAULT 0.7,
    max_results integer DEFAULT 10
)
RETURNS TABLE(
    product_code varchar(20),
    name varchar(255),
    category varchar(100),
    similarity float8
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.product_code,
        p.name,
        p.category,
        1 - (p.embedding_vector <=> query_vector) as similarity
    FROM test_products p
    WHERE p.embedding_vector IS NOT NULL
      AND 1 - (p.embedding_vector <=> query_vector) >= similarity_threshold
    ORDER BY p.embedding_vector <=> query_vector
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Create function for performance testing
CREATE OR REPLACE FUNCTION log_search_performance(
    p_user_id UUID,
    p_query_type VARCHAR(50),
    p_query_text TEXT,
    p_query_params JSONB,
    p_response_time_ms INTEGER,
    p_results_count INTEGER
)
RETURNS UUID AS $$
DECLARE
    query_id UUID;
BEGIN
    INSERT INTO test_search_queries (
        user_id, query_type, query_text, query_params, 
        response_time_ms, results_count
    ) VALUES (
        p_user_id, p_query_type, p_query_text, p_query_params,
        p_response_time_ms, p_results_count
    ) RETURNING test_search_queries.query_id INTO query_id;
    
    RETURN query_id;
END;
$$ LANGUAGE plpgsql;

-- Create view for performance metrics
CREATE OR REPLACE VIEW test_performance_metrics AS
SELECT 
    query_type,
    COUNT(*) as total_queries,
    AVG(response_time_ms) as avg_response_time_ms,
    MIN(response_time_ms) as min_response_time_ms,
    MAX(response_time_ms) as max_response_time_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms) as median_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99_response_time_ms,
    AVG(results_count) as avg_results_count,
    DATE_TRUNC('hour', created_at) as hour_bucket
FROM test_search_queries
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY query_type, DATE_TRUNC('hour', created_at)
ORDER BY hour_bucket DESC, query_type;

-- Insert sample data for immediate testing
INSERT INTO test_users (username, email, role, skill_level, experience_years) VALUES
('test_admin', 'admin@test.example.com', 'admin', 'expert', 10),
('test_user1', 'user1@test.example.com', 'user', 'intermediate', 5),
('test_user2', 'user2@test.example.com', 'user', 'beginner', 1),
('safety_officer', 'safety@test.example.com', 'safety_officer', 'expert', 15)
ON CONFLICT (username) DO NOTHING;

-- Grant permissions for test user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO test_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO test_user;