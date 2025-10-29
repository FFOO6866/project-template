-- Product Data Database Schema
-- Optimized for 17,266 products with proper indexing

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_sku VARCHAR(50) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    catalogue_item_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(product_sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_catalogue_id ON products(catalogue_item_id) WHERE catalogue_item_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_description_fulltext ON products USING gin(to_tsvector('english', description));

-- Create categories lookup table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create brands lookup table  
CREATE TABLE IF NOT EXISTS brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert categories from known data
INSERT INTO categories (name) VALUES 
    ('05 - Cleaning Products'),
    ('21 - Safety Products'),
    ('18 - Tools')
ON CONFLICT (name) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_products_updated_at 
    BEFORE UPDATE ON products 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create view for products with statistics
CREATE OR REPLACE VIEW products_stats AS
SELECT 
    category,
    brand,
    COUNT(*) as product_count,
    COUNT(CASE WHEN catalogue_item_id IS NOT NULL THEN 1 END) as with_catalogue_id,
    COUNT(CASE WHEN catalogue_item_id IS NULL THEN 1 END) as without_catalogue_id
FROM products 
GROUP BY category, brand
ORDER BY category, product_count DESC;

-- Create view for search optimization
CREATE OR REPLACE VIEW products_search AS
SELECT 
    id,
    product_sku,
    description,
    category,
    brand,
    catalogue_item_id,
    to_tsvector('english', description || ' ' || brand || ' ' || category) as search_vector
FROM products;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO horme_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO horme_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO horme_user;