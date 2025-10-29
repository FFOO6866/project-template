-- Horme POV Production Database Initialization
-- This script sets up the basic database schema for production deployment

-- Create database if not exists (handled by Docker)
-- CREATE DATABASE IF NOT EXISTS horme_db;

-- Use the database
\c horme_db;

-- Create basic tables for RFP processing
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    price DECIMAL(10, 2),
    keywords TEXT,
    specifications TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create RFP requests table
CREATE TABLE IF NOT EXISTS rfp_requests (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255),
    text TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create quotations table
CREATE TABLE IF NOT EXISTS quotations (
    id SERIAL PRIMARY KEY,
    rfp_id INTEGER REFERENCES rfp_requests(id),
    customer_name VARCHAR(255),
    total_amount DECIMAL(10, 2),
    items_json TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    api_key VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Insert sample products
INSERT INTO products (name, description, category, price, keywords, specifications) VALUES
('Industrial LED Light 50W', 'High-efficiency LED lighting for industrial use', 'Lighting', 89.99, 'led,light,industrial,50w', '50W,IP65,5000K'),
('Motion Sensor PIR', 'PIR motion detection sensor for automation', 'Sensors', 24.99, 'motion,sensor,pir,detection', 'PIR,12V,10m range'),
('Power Supply 24V 10A', 'Switching power supply for industrial applications', 'Power', 45.00, 'power,supply,24v,10a', '24V DC,10A,240W'),
('Ethernet Cable Cat6', 'Network cable for data transmission', 'Networking', 125.00, 'ethernet,cable,cat6,network', 'Cat6,UTP,100m'),
('IP Camera 1080p', 'Security camera with night vision', 'Security', 199.99, 'security,camera,ip,1080p', '1080p,IP66,Night Vision'),
('Safety Helmet', 'Industrial safety helmet with adjustable fit', 'Safety', 29.99, 'safety,helmet,protection,head', 'ABS,Adjustable,CE certified'),
('Work Gloves', 'Cut-resistant work gloves for industrial use', 'Safety', 19.99, 'gloves,safety,protection,cut', 'Cut level 3,Size M-XL'),
('Tool Set Professional', 'Complete professional tool set', 'Tools', 299.99, 'tools,professional,complete,set', '150 pieces,Steel case'),
('Extension Cord 15m', 'Heavy-duty extension cord for outdoor use', 'Electrical', 49.99, 'extension,cord,outdoor,heavy', '15m,IP44,16A'),
('First Aid Kit', 'Complete first aid kit for workplace safety', 'Safety', 79.99, 'first,aid,kit,safety,medical', 'DIN 13157,50 items')
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_products_keywords ON products USING GIN (to_tsvector('english', keywords));
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_rfp_requests_status ON rfp_requests (status);
CREATE INDEX IF NOT EXISTS idx_quotations_rfp_id ON quotations (rfp_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users (api_key);

-- Grant permissions to the application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO horme_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO horme_user;

-- Success message
\echo 'Horme POV production database initialized successfully!';
\echo 'Sample products loaded: ' || (SELECT COUNT(*) FROM products);
\echo 'Database ready for use.';