-- Seed test data for comprehensive testing
-- This script populates the database with realistic test data

-- Insert sample products for testing
INSERT INTO horme.products (sku, name, description, enriched_description, technical_specs, category_id, brand_id, currency, availability, is_published) 
SELECT 
    'TEST-' || LPAD(s::text, 6, '0'),
    'Test Product ' || s,
    'Description for test product ' || s || '. This product is designed for testing purposes.',
    'Enhanced description for test product ' || s || '. Features advanced functionality and superior quality. Perfect for testing search and filtering capabilities.',
    'Specifications: Weight: ' || (s % 10 + 1) || 'kg, Dimensions: ' || (s % 50 + 10) || 'x' || (s % 30 + 5) || 'x' || (s % 20 + 3) || 'cm, Power: ' || (s % 1000 + 100) || 'W',
    ((s % 6) + 1), -- Random category
    ((s % 4) + 1), -- Random brand
    'USD',
    CASE s % 4 
        WHEN 0 THEN 'in_stock'
        WHEN 1 THEN 'low_stock'
        WHEN 2 THEN 'out_of_stock'
        ELSE 'discontinued'
    END,
    CASE WHEN s % 10 = 0 THEN false ELSE true END -- 10% unpublished
FROM generate_series(1, 1000) s
ON CONFLICT (sku) DO NOTHING;

-- Insert product pricing
INSERT INTO horme.product_pricing (product_id, list_price, cost_price, discount_price)
SELECT 
    p.id,
    ROUND((RANDOM() * 1000 + 50)::numeric, 2), -- List price $50-$1050
    ROUND((RANDOM() * 500 + 25)::numeric, 2),  -- Cost price $25-$525
    ROUND((RANDOM() * 800 + 40)::numeric, 2)   -- Discount price $40-$840
FROM horme.products p
WHERE NOT EXISTS (
    SELECT 1 FROM horme.product_pricing pp WHERE pp.product_id = p.id
);

-- Insert sample quotations
INSERT INTO horme.quotations (quote_number, user_id, status, total_amount, currency, valid_until, notes, metadata)
SELECT 
    'Q-2024-' || LPAD(s::text, 6, '0'),
    1, -- Test user
    CASE s % 5 
        WHEN 0 THEN 'draft'
        WHEN 1 THEN 'sent'
        WHEN 2 THEN 'approved' 
        WHEN 3 THEN 'rejected'
        ELSE 'expired'
    END,
    ROUND((RANDOM() * 10000 + 500)::numeric, 2), -- Total $500-$10500
    'USD',
    CURRENT_TIMESTAMP + INTERVAL '30 days',
    'Test quotation ' || s || ' for integration testing',
    ('{"source": "test", "priority": "' || (CASE s % 3 WHEN 0 THEN 'high' WHEN 1 THEN 'medium' ELSE 'low' END) || '"}')::jsonb
FROM generate_series(1, 100) s
ON CONFLICT (quote_number) DO NOTHING;

-- Insert quotation items
INSERT INTO horme.quotation_items (quotation_id, product_id, quantity, unit_price, total_price, notes)
SELECT 
    q.id,
    p.id,
    (RANDOM() * 10 + 1)::integer, -- Quantity 1-11
    pp.list_price,
    pp.list_price * (RANDOM() * 10 + 1)::integer,
    'Test quotation item for product ' || p.name
FROM horme.quotations q
CROSS JOIN LATERAL (
    SELECT id, name FROM horme.products 
    WHERE is_published = true 
    ORDER BY RANDOM() 
    LIMIT (RANDOM() * 5 + 1)::integer
) p
JOIN horme.product_pricing pp ON pp.product_id = p.id
WHERE NOT EXISTS (
    SELECT 1 FROM horme.quotation_items qi 
    WHERE qi.quotation_id = q.id AND qi.product_id = p.id
);

-- Insert sample documents
INSERT INTO horme.documents (original_name, stored_name, file_path, file_size, mime_type, checksum, user_id, status, metadata)
SELECT 
    'test-document-' || s || '.txt',
    'stored-doc-' || s || '-' || EXTRACT(epoch FROM CURRENT_TIMESTAMP)::bigint || '.txt',
    '/test_data/documents/test-document-' || s || '.txt',
    (RANDOM() * 1024000 + 1000)::integer, -- Size 1KB-1MB
    'text/plain',
    md5('test content ' || s),
    1, -- Test user
    CASE s % 4 
        WHEN 0 THEN 'uploaded'
        WHEN 1 THEN 'processing' 
        WHEN 2 THEN 'processed'
        ELSE 'error'
    END,
    ('{"type": "test", "category": "' || (CASE s % 3 WHEN 0 THEN 'rfp' WHEN 1 THEN 'invoice' ELSE 'catalog' END) || '"}')::jsonb
FROM generate_series(1, 50) s;

-- Insert sample processing jobs
INSERT INTO horme.processing_jobs (job_id, user_id, status, progress, message, context_id, started_at, completed_at, metadata)
SELECT 
    'job-' || LPAD(s::text, 8, '0'),
    1, -- Test user
    CASE s % 6
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'processing'
        WHEN 2 THEN 'completed'
        WHEN 3 THEN 'error'
        WHEN 4 THEN 'cancelled'
        ELSE 'timeout'
    END,
    CASE 
        WHEN s % 6 IN (0, 1) THEN (RANDOM() * 100)::integer
        WHEN s % 6 = 2 THEN 100
        ELSE (RANDOM() * 80)::integer
    END,
    'Processing test job ' || s,
    'ctx-' || s,
    CURRENT_TIMESTAMP - INTERVAL '1 hour' * (RANDOM() * 24),
    CASE WHEN s % 6 IN (2, 3, 4, 5) THEN CURRENT_TIMESTAMP - INTERVAL '1 minute' * (RANDOM() * 60) ELSE NULL END,
    ('{"files_processed": ' || (RANDOM() * 10 + 1)::integer || ', "items_extracted": ' || (RANDOM() * 100 + 10)::integer || '}')::jsonb
FROM generate_series(1, 20) s
ON CONFLICT (job_id) DO NOTHING;

-- Insert search cache entries
INSERT INTO horme.search_cache (cache_key, query_hash, results, result_count, expires_at)
SELECT 
    'cache-key-' || s,
    md5('test query ' || s),
    ('[{"id": ' || (s * 10) || ', "name": "Test Result ' || s || '", "score": 0.9}]')::jsonb,
    1,
    CURRENT_TIMESTAMP + INTERVAL '5 minutes'
FROM generate_series(1, 10) s
ON CONFLICT (cache_key) DO NOTHING;

-- Update statistics for query planner
ANALYZE horme.products;
ANALYZE horme.quotations;
ANALYZE horme.quotation_items;
ANALYZE horme.documents;
ANALYZE horme.processing_jobs;