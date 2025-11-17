-- ============================================================================
-- PostgreSQL Extensions Installation
-- Dynamic Job Pricing Engine
-- ============================================================================
-- This script installs required PostgreSQL extensions
-- Runs after 01-init.sql
-- ============================================================================

-- Connect to the job_pricing_db database
\c job_pricing_db

-- ============================================================================
-- Extension 1: pgvector - Vector similarity search
-- ============================================================================
-- Used for semantic search of Mercer jobs using OpenAI embeddings
-- Stores and searches 1536-dimension vectors
CREATE EXTENSION IF NOT EXISTS vector;

\echo 'Extension "vector" (pgvector) installed successfully'
\echo 'Vector search enabled for semantic job matching'

-- ============================================================================
-- Extension 2: pg_trgm - Trigram matching for fuzzy text search
-- ============================================================================
-- Used for fuzzy matching of job titles, skills, and descriptions
-- Enables LIKE patterns and similarity scoring
CREATE EXTENSION IF NOT EXISTS pg_trgm;

\echo 'Extension "pg_trgm" installed successfully'
\echo 'Fuzzy text search enabled'

-- ============================================================================
-- Extension 3: uuid-ossp - UUID generation
-- ============================================================================
-- Used for generating UUIDs for primary keys
-- Better than SERIAL for distributed systems
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\echo 'Extension "uuid-ossp" installed successfully'
\echo 'UUID generation enabled'

-- ============================================================================
-- Extension 4: btree_gin - GIN indexes for btree-indexable types
-- ============================================================================
-- Used for composite indexes with JSONB and other types
-- Improves query performance on complex filters
CREATE EXTENSION IF NOT EXISTS btree_gin;

\echo 'Extension "btree_gin" installed successfully'
\echo 'Composite indexing enhanced'

-- ============================================================================
-- Extension 5: unaccent - Remove accents from text
-- ============================================================================
-- Used for international text matching (names, locations)
-- Normalizes accented characters
CREATE EXTENSION IF NOT EXISTS unaccent;

\echo 'Extension "unaccent" installed successfully'
\echo 'International text matching enabled'

-- ============================================================================
-- Verify Extensions Installed
-- ============================================================================
\echo ''
\echo '========================================='
\echo 'Installed Extensions:'
\echo '========================================='
SELECT extname AS "Extension Name",
       extversion AS "Version"
FROM pg_extension
WHERE extname IN ('vector', 'pg_trgm', 'uuid-ossp', 'btree_gin', 'unaccent')
ORDER BY extname;

-- ============================================================================
-- Extension Configuration
-- ============================================================================

-- Configure pg_trgm similarity threshold (0.0 - 1.0)
-- Lower = more fuzzy matches (default is 0.3)
SET pg_trgm.similarity_threshold = 0.2;

\echo ''
\echo '========================================='
\echo 'All extensions installed successfully!'
\echo 'Database ready for schema creation'
\echo '========================================='
