-- Add pgvector extension and vector columns for AI model support
-- This script enables semantic search and embedding-based features

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to products table (if it exists)
-- Using 1536 dimensions for OpenAI text-embedding-3-small model
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'products'
    ) THEN
        -- Add embedding column if it doesn't exist
        IF NOT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'products'
            AND column_name = 'embedding'
        ) THEN
            ALTER TABLE products ADD COLUMN embedding vector(1536);

            -- Create index for faster similarity search
            CREATE INDEX IF NOT EXISTS products_embedding_idx
            ON products USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);

            RAISE NOTICE 'Added embedding column (1536 dimensions) to products table';
        ELSE
            -- Check if dimension needs updating from 384 to 1536
            DECLARE
                current_dim int;
            BEGIN
                SELECT atttypmod - 4 INTO current_dim
                FROM pg_attribute
                WHERE attrelid = 'products'::regclass
                AND attname = 'embedding';

                IF current_dim = 384 THEN
                    RAISE NOTICE 'Updating embedding dimension from 384 to 1536...';
                    ALTER TABLE products ALTER COLUMN embedding TYPE vector(1536);
                    RAISE NOTICE 'Embedding column updated to 1536 dimensions';
                ELSIF current_dim = 1536 THEN
                    RAISE NOTICE 'Embedding column already has correct dimensions (1536)';
                ELSE
                    RAISE NOTICE 'Embedding column exists with % dimensions', current_dim;
                END IF;
            END;
        END IF;
    ELSE
        RAISE NOTICE 'Products table does not exist yet - will be created later';
    END IF;
END$$;

-- Add embedding column to work_recommendations table (if it exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'work_recommendations'
    ) THEN
        IF NOT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'work_recommendations'
            AND column_name = 'embedding'
        ) THEN
            ALTER TABLE work_recommendations ADD COLUMN embedding vector(1536);

            CREATE INDEX IF NOT EXISTS work_recommendations_embedding_idx
            ON work_recommendations USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 50);

            RAISE NOTICE 'Added embedding column (1536 dimensions) to work_recommendations table';
        ELSE
            RAISE NOTICE 'Embedding column already exists in work_recommendations table';
        END IF;
    ELSE
        RAISE NOTICE 'Work_recommendations table does not exist yet - will be created later';
    END IF;
END$$;

-- Add embedding column to quotations table (if it exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'quotations'
    ) THEN
        IF NOT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'quotations'
            AND column_name = 'embedding'
        ) THEN
            ALTER TABLE quotations ADD COLUMN embedding vector(1536);

            CREATE INDEX IF NOT EXISTS quotations_embedding_idx
            ON quotations USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 50);

            RAISE NOTICE 'Added embedding column (1536 dimensions) to quotations table';
        ELSE
            RAISE NOTICE 'Embedding column already exists in quotations table';
        END IF;
    ELSE
        RAISE NOTICE 'Quotations table does not exist yet - will be created later';
    END IF;
END$$;

-- Create function for cosine similarity (helper for semantic search)
CREATE OR REPLACE FUNCTION cosine_similarity(a vector, b vector)
RETURNS float
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    RETURN 1 - (a <=> b);
END;
$$;

-- Create function to find similar products
CREATE OR REPLACE FUNCTION find_similar_products(
    query_embedding vector(1536),
    limit_count integer DEFAULT 10,
    min_similarity float DEFAULT 0.7
)
RETURNS TABLE(
    product_id integer,
    product_name text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.name,
        cosine_similarity(p.embedding, query_embedding) as similarity
    FROM products p
    WHERE p.embedding IS NOT NULL
    AND cosine_similarity(p.embedding, query_embedding) >= min_similarity
    ORDER BY p.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$;

-- Create function to find similar work recommendations
CREATE OR REPLACE FUNCTION find_similar_work_recommendations(
    query_embedding vector(1536),
    limit_count integer DEFAULT 10,
    min_similarity float DEFAULT 0.6
)
RETURNS TABLE(
    recommendation_id integer,
    recommendation_title text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        w.id,
        w.title,
        cosine_similarity(w.embedding, query_embedding) as similarity
    FROM work_recommendations w
    WHERE w.embedding IS NOT NULL
    AND cosine_similarity(w.embedding, query_embedding) >= min_similarity
    ORDER BY w.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION cosine_similarity(vector, vector) TO horme_user;
GRANT EXECUTE ON FUNCTION find_similar_products(vector, integer, float) TO horme_user;
GRANT EXECUTE ON FUNCTION find_similar_work_recommendations(vector, integer, float) TO horme_user;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension and vector columns configured successfully';
    RAISE NOTICE 'Embedding dimension: 1536 (OpenAI text-embedding-3-small compatible)';
    RAISE NOTICE 'Created similarity search functions for products and work recommendations';
    RAISE NOTICE 'Use scripts/generate_product_embeddings.py to populate embeddings';
END$$;
