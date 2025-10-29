-- Create products table for Horme catalog
-- NO MOCK DATA - Table structure only, data loaded separately

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_code VARCHAR(100) UNIQUE,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(200),
    subcategory VARCHAR(200),
    brand VARCHAR(200),
    supplier VARCHAR(200) DEFAULT 'Horme Hardware',
    price DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'SGD',
    unit VARCHAR(50) DEFAULT 'pieces',
    stock_quantity INTEGER DEFAULT 0,
    minimum_order_quantity INTEGER DEFAULT 1,
    lead_time_days INTEGER DEFAULT 7,
    image_url TEXT,
    specifications JSONB,
    tags TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for search performance
CREATE INDEX IF NOT EXISTS idx_products_name ON products USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_products_description ON products USING gin(to_tsvector('english', description));
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active) WHERE is_active = TRUE;

-- Add quotation_id column to documents if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='documents' AND column_name='quotation_id') THEN
        ALTER TABLE documents ADD COLUMN quotation_id INTEGER REFERENCES quotes(id);
    END IF;
END $$;

-- Add pdf_path column to quotes if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='quotes' AND column_name='pdf_path') THEN
        ALTER TABLE quotes ADD COLUMN pdf_path TEXT;
    END IF;
END $$;

-- Rename quote_line_items to quote_items for consistency
ALTER TABLE IF EXISTS quote_line_items RENAME TO quote_items;

COMMENT ON TABLE products IS 'Product catalog from Horme Hardware - real data only';
