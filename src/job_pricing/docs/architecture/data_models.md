# Data Models Specification

**Version**: 1.0
**Date**: 2025-01-10
**Status**: Production-Ready

## Overview

This document defines the complete data model for the Dynamic Job Pricing Engine, including all entities, relationships, database schemas, and data structures. The system uses **PostgreSQL** as the primary database with additional extensions for full-text search (pg_trgm) and vector similarity (pgvector).

## Entity Relationship Diagram

```
┌──────────────────┐         ┌──────────────────┐
│  Job Requests    │────────>│ Pricing Results  │
│  (User Input)    │   1:1   │  (Algorithm      │
│                  │         │   Output)        │
└─────────┬────────┘         └────────┬─────────┘
          │                           │
          │ 1:1                       │ N:1
          ▼                           ▼
┌──────────────────┐         ┌──────────────────┐
│ Mercer Job       │         │  Data Source     │
│ Mappings         │<───────>│  Contributions   │
│                  │   1:N   │                  │
└──────────────────┘         └──────────────────┘
          │
          │ N:1
          ▼
┌──────────────────────────────────────────────────┐
│          Mercer Job Library                      │
│  (18,000+ standardized jobs)                     │
└────────────┬─────────────────────────────────────┘
             │
             │ 1:N
             ▼
┌──────────────────────────────────────────────────┐
│        Mercer Market Data                        │
│  (Compensation benchmarks)                       │
└──────────────────────────────────────────────────┘


┌──────────────────┐         ┌──────────────────┐
│ SSG Skills       │────────>│ Job Skills       │
│ Framework        │   N:M   │ Extracted        │
│ (38 sectors)     │         │                  │
└──────────────────┘         └──────────────────┘


┌──────────────────┐         ┌──────────────────┐
│ Scraped Job      │────────>│ Scraped Company  │
│ Listings         │   N:1   │ Data             │
│ (MCF, Glassdoor) │         │                  │
└──────────────────┘         └──────────────────┘


┌──────────────────┐         ┌──────────────────┐
│ Internal HRIS    │         │ Grade Salary     │
│ Employees        │<───────>│ Bands            │
│                  │   N:1   │                  │
└──────────────────┘         └──────────────────┘
```

## Core Entities

### 1. Job Requests

**Purpose**: Store user input for job pricing requests

**Table**: `job_pricing_requests`

```sql
CREATE TABLE job_pricing_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Input Data
    job_title VARCHAR(200) NOT NULL,
    job_description TEXT NOT NULL,
    location VARCHAR(100) NOT NULL,
    portfolio VARCHAR(100),
    department VARCHAR(100),
    employment_type VARCHAR(50) NOT NULL CHECK (employment_type IN ('Full-time', 'Contract', 'Part-time')),
    internal_grade VARCHAR(10) NOT NULL,
    job_family VARCHAR(100) NOT NULL,
    skills JSONB, -- Array of skill objects
    alternative_titles TEXT[],

    -- Request Metadata
    requested_by VARCHAR(100) NOT NULL, -- User email/ID
    request_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),

    -- Processing Tracking
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    processing_duration_seconds INTEGER,

    -- Audit Fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    CONSTRAINT valid_grade CHECK (internal_grade ~ '^[0-9]{1,2}$')
);

-- Indexes
CREATE INDEX idx_job_requests_status ON job_pricing_requests(status);
CREATE INDEX idx_job_requests_requested_by ON job_pricing_requests(requested_by);
CREATE INDEX idx_job_requests_date ON job_pricing_requests(request_date DESC);
CREATE INDEX idx_job_requests_job_family ON job_pricing_requests(job_family);
CREATE INDEX idx_job_requests_location ON job_pricing_requests(location);

-- Full-text search on job titles and descriptions
CREATE INDEX idx_job_requests_title_fts ON job_pricing_requests
USING gin(to_tsvector('english', job_title));

CREATE INDEX idx_job_requests_description_fts ON job_pricing_requests
USING gin(to_tsvector('english', job_description));
```

### 2. Pricing Results

**Purpose**: Store algorithm output and recommendations

**Table**: `job_pricing_results`

```sql
CREATE TABLE job_pricing_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES job_pricing_requests(id) ON DELETE CASCADE,

    -- Salary Recommendations
    currency VARCHAR(3) DEFAULT 'SGD',
    period VARCHAR(20) DEFAULT 'annual',

    recommended_min NUMERIC(12, 2) NOT NULL,
    recommended_max NUMERIC(12, 2) NOT NULL,
    target_salary NUMERIC(12, 2) NOT NULL,

    -- Full Distribution
    p10 NUMERIC(12, 2),
    p25 NUMERIC(12, 2),
    p50 NUMERIC(12, 2),
    p75 NUMERIC(12, 2),
    p90 NUMERIC(12, 2),

    market_position VARCHAR(50), -- "55th percentile"

    -- Confidence Metrics
    confidence_score NUMERIC(5, 2) NOT NULL, -- 0-100
    confidence_level VARCHAR(20) NOT NULL CHECK (confidence_level IN ('High', 'Medium', 'Low')),

    confidence_factors JSONB, -- Breakdown of confidence components

    -- Explanation
    summary_text TEXT,
    key_factors TEXT[],
    considerations TEXT[],

    -- Alternative Scenarios
    alternative_scenarios JSONB, -- Array of scenario objects

    -- Data Quality Metadata
    total_data_points INTEGER,
    data_sources_used INTEGER,
    data_consistency_score NUMERIC(5, 2),

    -- Audit Fields
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(request_id)
);

-- Indexes
CREATE INDEX idx_pricing_results_request ON job_pricing_results(request_id);
CREATE INDEX idx_pricing_results_confidence ON job_pricing_results(confidence_level);
CREATE INDEX idx_pricing_results_created ON job_pricing_results(created_at DESC);
```

### 3. Data Source Contributions

**Purpose**: Track individual data source contributions to each pricing result

**Table**: `data_source_contributions`

```sql
CREATE TABLE data_source_contributions (
    id SERIAL PRIMARY KEY,
    result_id UUID NOT NULL REFERENCES job_pricing_results(id) ON DELETE CASCADE,

    source_name VARCHAR(50) NOT NULL CHECK (source_name IN ('mercer', 'my_careers_future', 'glassdoor', 'internal_hris', 'applicant_data')),

    -- Weight Applied
    weight_applied NUMERIC(5, 4), -- 0.0000 - 1.0000

    -- Source Data
    p10 NUMERIC(12, 2),
    p25 NUMERIC(12, 2),
    p50 NUMERIC(12, 2),
    p75 NUMERIC(12, 2),
    p90 NUMERIC(12, 2),

    -- Metadata
    sample_size INTEGER,
    data_date DATE,
    quality_score NUMERIC(5, 2), -- 0.00 - 1.00
    recency_weight NUMERIC(5, 2), -- 0.00 - 1.00

    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_data_contrib_result ON data_source_contributions(result_id);
CREATE INDEX idx_data_contrib_source ON data_source_contributions(source_name);
```

## Mercer Integration

### 4. Mercer Job Library

**Purpose**: Store Mercer's standardized job catalog

**Table**: `mercer_job_library`

```sql
CREATE TABLE mercer_job_library (
    id SERIAL PRIMARY KEY,

    -- Job Identification
    job_code VARCHAR(50) UNIQUE NOT NULL, -- e.g., "HRM.04.005.M50"
    job_title VARCHAR(255) NOT NULL,

    -- Hierarchy
    family VARCHAR(100) NOT NULL,
    subfamily VARCHAR(100),
    career_level VARCHAR(10), -- M3, M4, M5, etc.
    position_class INTEGER, -- 40-87

    -- Job Content
    job_description TEXT,
    typical_titles TEXT[],
    specialization_notes TEXT,

    -- IPE Factors (Point Ranges)
    impact_min INTEGER,
    impact_max INTEGER,
    communication_min INTEGER,
    communication_max INTEGER,
    innovation_min INTEGER,
    innovation_max INTEGER,
    knowledge_min INTEGER,
    knowledge_max INTEGER,
    risk_min INTEGER,
    risk_max INTEGER,

    -- Vector Embedding for Semantic Search
    embedding vector(1536), -- OpenAI text-embedding-3-large dimension

    -- Audit Fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_mercer_job_code ON mercer_job_library(job_code);
CREATE INDEX idx_mercer_family ON mercer_job_library(family);
CREATE INDEX idx_mercer_subfamily ON mercer_job_library(subfamily);
CREATE INDEX idx_mercer_level ON mercer_job_library(career_level);
CREATE INDEX idx_mercer_position_class ON mercer_job_library(position_class);

-- Vector similarity search index
CREATE INDEX idx_mercer_embedding ON mercer_job_library
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Full-text search
CREATE INDEX idx_mercer_job_description_fts ON mercer_job_library
USING gin(to_tsvector('english', job_description));
```

### 5. Mercer Job Mappings

**Purpose**: Store AI-powered mappings from user jobs to Mercer library

**Table**: `mercer_job_mappings`

```sql
CREATE TABLE mercer_job_mappings (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES job_pricing_requests(id) ON DELETE CASCADE,
    mercer_job_id INTEGER NOT NULL REFERENCES mercer_job_library(id),

    -- Match Quality
    confidence_score NUMERIC(5, 2) NOT NULL, -- 0.00 - 1.00
    match_method VARCHAR(50), -- 'semantic', 'rule_based', 'hybrid', 'manual'

    -- Similarity Scores
    semantic_similarity NUMERIC(5, 4),
    title_similarity NUMERIC(5, 4),
    skills_overlap NUMERIC(5, 4),
    grade_alignment_score NUMERIC(5, 4),

    -- Explanation
    explanation TEXT,
    key_similarities TEXT[],
    key_differences TEXT[],

    -- Alternative Matches (Top 5)
    alternative_matches JSONB, -- Array of {job_code, score, reason}

    -- Manual Review
    requires_manual_review BOOLEAN DEFAULT FALSE,
    manually_reviewed BOOLEAN DEFAULT FALSE,
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(request_id)
);

-- Indexes
CREATE INDEX idx_mercer_mapping_request ON mercer_job_mappings(request_id);
CREATE INDEX idx_mercer_mapping_job ON mercer_job_mappings(mercer_job_id);
CREATE INDEX idx_mercer_mapping_confidence ON mercer_job_mappings(confidence_score DESC);
CREATE INDEX idx_mercer_mapping_review ON mercer_job_mappings(requires_manual_review)
WHERE requires_manual_review = TRUE;
```

### 6. Mercer Market Data

**Purpose**: Store Mercer compensation survey data

**Table**: `mercer_market_data`

```sql
CREATE TABLE mercer_market_data (
    id SERIAL PRIMARY KEY,

    job_code VARCHAR(50) NOT NULL,

    -- Geography
    country_code VARCHAR(2) NOT NULL,
    location VARCHAR(100),

    -- Survey Details
    currency VARCHAR(3) DEFAULT 'SGD',
    industry VARCHAR(100),
    benchmark_cut VARCHAR(50) NOT NULL, -- 'by_job', 'by_family_level', 'by_family_position_class', etc.

    -- Compensation Data (Annual)
    p10 NUMERIC(12, 2),
    p25 NUMERIC(12, 2),
    p50 NUMERIC(12, 2),
    p75 NUMERIC(12, 2),
    p90 NUMERIC(12, 2),

    sample_size INTEGER,

    -- Survey Metadata
    survey_date DATE NOT NULL,
    survey_name VARCHAR(255),
    participant_count INTEGER,

    -- Data Quality
    data_quality_flag VARCHAR(20) DEFAULT 'normal' CHECK (data_quality_flag IN ('high', 'normal', 'low', 'outlier')),

    data_retrieved_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(job_code, country_code, benchmark_cut, survey_date)
);

-- Indexes
CREATE INDEX idx_mercer_market_job ON mercer_market_data(job_code);
CREATE INDEX idx_mercer_market_country ON mercer_market_data(country_code);
CREATE INDEX idx_mercer_market_date ON mercer_market_data(survey_date DESC);
CREATE INDEX idx_mercer_market_benchmark ON mercer_market_data(benchmark_cut);
```

## SSG SkillsFuture Integration

### 7. SSG Skills Framework

**Purpose**: Store Singapore's national skills taxonomy

**Table**: `ssg_skills_framework`

```sql
CREATE TABLE ssg_skills_framework (
    id SERIAL PRIMARY KEY,

    -- Hierarchy
    sector VARCHAR(100) NOT NULL,
    track VARCHAR(200) NOT NULL,

    -- Job Role
    job_role_code VARCHAR(50) NOT NULL,
    job_role_title VARCHAR(255) NOT NULL,
    job_role_description TEXT,

    -- Career Level
    career_level VARCHAR(50), -- 'Entry', 'Mid', 'Senior', 'Lead'

    -- Critical Work Functions
    critical_work_function VARCHAR(255),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(job_role_code)
);

-- Indexes
CREATE INDEX idx_ssg_sector ON ssg_skills_framework(sector);
CREATE INDEX idx_ssg_track ON ssg_skills_framework(track);
CREATE INDEX idx_ssg_job_role_code ON ssg_skills_framework(job_role_code);
CREATE INDEX idx_ssg_career_level ON ssg_skills_framework(career_level);
```

### 8. SSG Technical Skills & Competencies (TSC)

**Purpose**: Store technical skills mapped to job roles

**Table**: `ssg_tsc`

```sql
CREATE TABLE ssg_tsc (
    id SERIAL PRIMARY KEY,

    tsc_code VARCHAR(50) UNIQUE NOT NULL,
    tsc_title VARCHAR(255) NOT NULL,
    tsc_description TEXT,

    skill_category VARCHAR(100),
    proficiency_level VARCHAR(50), -- 'Basic', 'Intermediate', 'Advanced'

    -- Job Role Mapping (Many-to-Many handled via junction table)

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ssg_tsc_code ON ssg_tsc(tsc_code);
CREATE INDEX idx_ssg_tsc_category ON ssg_tsc(skill_category);

-- Full-text search for skill matching
CREATE INDEX idx_ssg_tsc_title_fts ON ssg_tsc
USING gin(to_tsvector('english', tsc_title));

-- Trigram index for fuzzy matching
CREATE INDEX idx_ssg_tsc_title_trgm ON ssg_tsc
USING gin(tsc_title gin_trgm_ops);
```

### 9. SSG Job Role to TSC Mapping

**Purpose**: Many-to-many relationship between job roles and skills

**Table**: `ssg_job_role_tsc_mapping`

```sql
CREATE TABLE ssg_job_role_tsc_mapping (
    id SERIAL PRIMARY KEY,

    job_role_code VARCHAR(50) NOT NULL REFERENCES ssg_skills_framework(job_role_code),
    tsc_code VARCHAR(50) NOT NULL REFERENCES ssg_tsc(tsc_code),

    proficiency_level VARCHAR(50), -- Required proficiency for this role
    is_core_skill BOOLEAN DEFAULT FALSE,

    UNIQUE(job_role_code, tsc_code)
);

-- Indexes
CREATE INDEX idx_ssg_mapping_job_role ON ssg_job_role_tsc_mapping(job_role_code);
CREATE INDEX idx_ssg_mapping_tsc ON ssg_job_role_tsc_mapping(tsc_code);
```

### 10. Job Skills Extracted

**Purpose**: Store skills extracted from user job descriptions

**Table**: `job_skills_extracted`

```sql
CREATE TABLE job_skills_extracted (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES job_pricing_requests(id) ON DELETE CASCADE,

    -- Extracted Skill
    skill_name VARCHAR(255) NOT NULL,
    skill_category VARCHAR(100),

    -- SSG Mapping
    matched_tsc_code VARCHAR(50) REFERENCES ssg_tsc(tsc_code),
    match_confidence NUMERIC(5, 2), -- 0.00 - 1.00
    match_method VARCHAR(50), -- 'exact', 'fuzzy', 'semantic', 'manual'

    -- Skill Importance
    proficiency_required VARCHAR(50),
    is_core_skill BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_skills_request ON job_skills_extracted(request_id);
CREATE INDEX idx_skills_tsc ON job_skills_extracted(matched_tsc_code);
```

## Web Scraping Data

### 11. Scraped Job Listings

**Purpose**: Store job data scraped from MCF and Glassdoor

**Table**: `scraped_job_listings`

```sql
CREATE TABLE scraped_job_listings (
    id SERIAL PRIMARY KEY,

    -- Source Identification
    source VARCHAR(50) NOT NULL CHECK (source IN ('my_careers_future', 'glassdoor')),
    job_id VARCHAR(255) NOT NULL,
    job_url TEXT NOT NULL,

    -- Job Details
    job_title VARCHAR(500) NOT NULL,
    company_name VARCHAR(500) NOT NULL,

    -- Salary Data
    salary_min NUMERIC(12, 2),
    salary_max NUMERIC(12, 2),
    salary_currency VARCHAR(3) DEFAULT 'SGD',
    salary_type VARCHAR(20), -- 'actual', 'estimated'

    -- Location
    location VARCHAR(255),

    -- Job Characteristics
    employment_type VARCHAR(50),
    seniority_level VARCHAR(100),
    job_description TEXT,
    requirements TEXT,
    skills TEXT[],
    benefits TEXT[],

    -- Company Data (Glassdoor)
    company_rating NUMERIC(3, 2),
    company_size VARCHAR(50),
    industry VARCHAR(100),

    -- Data Quality
    has_salary_data BOOLEAN DEFAULT TRUE,

    -- Temporal Tracking
    posted_date TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,

    UNIQUE(source, job_id)
);

-- Indexes
CREATE INDEX idx_scraped_jobs_source ON scraped_job_listings(source);
CREATE INDEX idx_scraped_jobs_title ON scraped_job_listings(job_title);
CREATE INDEX idx_scraped_jobs_company ON scraped_job_listings(company_name);
CREATE INDEX idx_scraped_jobs_location ON scraped_job_listings(location);
CREATE INDEX idx_scraped_jobs_posted ON scraped_job_listings(posted_date DESC);
CREATE INDEX idx_scraped_jobs_active ON scraped_job_listings(is_active);
CREATE INDEX idx_scraped_jobs_salary ON scraped_job_listings(salary_min, salary_max);
CREATE INDEX idx_scraped_jobs_salary_data ON scraped_job_listings(has_salary_data)
WHERE has_salary_data = TRUE;

-- Full-text search
CREATE INDEX idx_scraped_jobs_description_fts ON scraped_job_listings
USING gin(to_tsvector('english', job_description));

-- Trigram index for fuzzy title matching
CREATE INDEX idx_scraped_jobs_title_trgm ON scraped_job_listings
USING gin(job_title gin_trgm_ops);
```

### 12. Scraped Company Data

**Purpose**: Aggregate company information from multiple sources

**Table**: `scraped_company_data`

```sql
CREATE TABLE scraped_company_data (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(500) NOT NULL UNIQUE,

    -- Company Profile
    glassdoor_rating NUMERIC(3, 2),
    company_size VARCHAR(50),
    industry VARCHAR(100),
    headquarters_location VARCHAR(255),

    -- Hiring Activity
    total_jobs_posted INTEGER DEFAULT 0,
    active_jobs_count INTEGER DEFAULT 0,

    -- Compensation Insights
    avg_salary_min NUMERIC(12, 2),
    avg_salary_max NUMERIC(12, 2),

    last_updated TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_company_name ON scraped_company_data(company_name);
CREATE INDEX idx_company_industry ON scraped_company_data(industry);
CREATE INDEX idx_company_rating ON scraped_company_data(glassdoor_rating DESC);
```

### 13. Scraping Audit Log

**Purpose**: Track web scraping batch jobs

**Table**: `scraping_audit_log`

```sql
CREATE TABLE scraping_audit_log (
    id SERIAL PRIMARY KEY,

    run_date TIMESTAMP NOT NULL,
    run_type VARCHAR(20) DEFAULT 'weekly' CHECK (run_type IN ('weekly', 'daily', 'manual')),

    -- Source Breakdown
    source VARCHAR(50),
    mcf_count INTEGER DEFAULT 0,
    glassdoor_count INTEGER DEFAULT 0,

    -- Processing Metrics
    validated_count INTEGER DEFAULT 0,
    deduplicated_count INTEGER DEFAULT 0,
    stored_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,

    -- Execution
    status VARCHAR(20) NOT NULL CHECK (status IN ('completed', 'failed', 'partial')),
    error_message TEXT,
    execution_time_seconds INTEGER,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_log_date ON scraping_audit_log(run_date DESC);
CREATE INDEX idx_audit_log_status ON scraping_audit_log(status);
CREATE INDEX idx_audit_log_source ON scraping_audit_log(source);
```

## Internal HRIS Integration

### 14. Internal Employees (Simplified)

**Purpose**: Store relevant employee data for internal benchmarking

**Note**: This is a simplified view. Actual HRIS integration would be read-only from existing system.

**Table**: `internal_employees`

```sql
CREATE TABLE internal_employees (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE NOT NULL,

    -- Job Information
    job_title VARCHAR(200) NOT NULL,
    department VARCHAR(100),
    job_family VARCHAR(100),

    -- Grade & Compensation
    internal_grade VARCHAR(10),
    current_salary NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'SGD',

    -- Employment Details
    employment_type VARCHAR(50),
    location VARCHAR(100),
    employment_status VARCHAR(20) DEFAULT 'Active',

    -- Career Progression
    years_of_experience INTEGER,
    years_in_company INTEGER,
    years_in_grade INTEGER,

    -- Performance
    performance_rating VARCHAR(20),
    last_salary_review_date DATE,

    -- Privacy Protection
    data_anonymized BOOLEAN DEFAULT TRUE,

    -- Temporal
    hire_date DATE,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_employees_job_title ON internal_employees(job_title);
CREATE INDEX idx_employees_grade ON internal_employees(internal_grade);
CREATE INDEX idx_employees_department ON internal_employees(department);
CREATE INDEX idx_employees_status ON internal_employees(employment_status);
CREATE INDEX idx_employees_salary ON internal_employees(current_salary);
```

### 15. Grade Salary Bands

**Purpose**: Define company-specific salary bands per grade

**Table**: `grade_salary_bands`

```sql
CREATE TABLE grade_salary_bands (
    id SERIAL PRIMARY KEY,
    internal_grade VARCHAR(10) UNIQUE NOT NULL,

    -- Salary Band
    absolute_min NUMERIC(12, 2) NOT NULL,
    absolute_max NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'SGD',

    -- Market Positioning Strategy
    market_position NUMERIC(5, 2), -- Target percentile (e.g., 0.50 = P50)

    -- Metadata
    effective_date DATE NOT NULL,
    expiry_date DATE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_grade_bands_grade ON grade_salary_bands(internal_grade);
CREATE INDEX idx_grade_bands_effective ON grade_salary_bands(effective_date DESC);
```

## Applicant Data

### 16. Applicants (Simplified)

**Purpose**: Track applicant salary expectations for market intelligence

**Note**: This is a simplified view. Actual ATS integration would be read-only.

**Table**: `applicants`

```sql
CREATE TABLE applicants (
    id SERIAL PRIMARY KEY,
    applicant_id VARCHAR(50) UNIQUE NOT NULL,

    -- Applied Position
    applied_job_title VARCHAR(200) NOT NULL,
    job_family VARCHAR(100),

    -- Salary Expectations
    expected_salary NUMERIC(12, 2),
    current_salary NUMERIC(12, 2),
    currency VARCHAR(3) DEFAULT 'SGD',

    -- Applicant Profile
    years_of_experience INTEGER,
    education_level VARCHAR(50),
    location VARCHAR(100),

    -- Application Status
    application_status VARCHAR(50) CHECK (application_status IN ('Applied', 'Shortlisted', 'Interviewed', 'Offered', 'Rejected', 'Withdrawn')),
    application_date DATE NOT NULL,

    -- Privacy Protection
    data_anonymized BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_applicants_job_title ON applicants(applied_job_title);
CREATE INDEX idx_applicants_status ON applicants(application_status);
CREATE INDEX idx_applicants_date ON applicants(application_date DESC);
```

## Supporting Tables

### 17. Location Index

**Purpose**: Store location-specific cost-of-living adjustments

**Table**: `location_index`

```sql
CREATE TABLE location_index (
    id SERIAL PRIMARY KEY,
    location_name VARCHAR(100) UNIQUE NOT NULL,

    -- Cost of Living Index (Singapore CBD = 1.0)
    cost_of_living_index NUMERIC(5, 2) NOT NULL,

    -- Geographic Details
    region VARCHAR(50),
    postal_code_prefix VARCHAR(10),

    -- Metadata
    effective_date DATE NOT NULL,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_location_name ON location_index(location_name);
```

### 18. Currency Exchange Rates

**Purpose**: Store historical exchange rates for currency conversion

**Table**: `currency_exchange_rates`

```sql
CREATE TABLE currency_exchange_rates (
    id SERIAL PRIMARY KEY,

    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    exchange_rate NUMERIC(12, 6) NOT NULL,

    rate_date DATE NOT NULL,
    source VARCHAR(50), -- 'MAS', 'XE', 'ECB', etc.

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(from_currency, to_currency, rate_date)
);

-- Indexes
CREATE INDEX idx_exchange_from_to ON currency_exchange_rates(from_currency, to_currency);
CREATE INDEX idx_exchange_date ON currency_exchange_rates(rate_date DESC);
```

### 19. Audit Log

**Purpose**: Comprehensive audit trail for all system actions

**Table**: `audit_log`

```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,

    -- Action Details
    action_type VARCHAR(50) NOT NULL, -- 'job_request', 'pricing_result', 'data_update', etc.
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(255),

    -- User Context
    performed_by VARCHAR(100) NOT NULL,
    ip_address INET,
    user_agent TEXT,

    -- Change Details
    action_description TEXT,
    old_values JSONB,
    new_values JSONB,

    -- Temporal
    performed_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_action_type ON audit_log(action_type);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_user ON audit_log(performed_by);
CREATE INDEX idx_audit_time ON audit_log(performed_at DESC);

-- Partition by month for scalability
-- (Add partitioning strategy as data grows)
```

## Data Relationships Summary

### Primary Relationships

1. **Job Request → Pricing Result**: 1:1
2. **Pricing Result → Data Source Contributions**: 1:N
3. **Job Request → Mercer Job Mapping**: 1:1
4. **Job Request → Job Skills Extracted**: 1:N
5. **Mercer Job Library → Market Data**: 1:N
6. **SSG Job Role → TSC**: N:M (via junction table)
7. **Scraped Job → Company Data**: N:1
8. **Internal Employee → Grade Band**: N:1

## Database Extensions Required

```sql
-- Enable required PostgreSQL extensions

-- For fuzzy string matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- For vector similarity search (requires pgvector installation)
CREATE EXTENSION IF NOT EXISTS vector;

-- For UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

## Data Retention Policy

| Table | Retention Period | Archive Strategy |
|-------|------------------|------------------|
| job_pricing_requests | 2 years | Archive to cold storage |
| job_pricing_results | 2 years | Archive to cold storage |
| scraped_job_listings | 1 year (active), 3 years (inactive) | Soft delete after 1 year |
| mercer_market_data | 5 years | Keep all historical data |
| internal_employees | Active only | Sync from HRIS |
| audit_log | 7 years | Partition by month, archive yearly |

## Data Privacy & Compliance

### PDPA (Singapore) Compliance

1. **Personal Data Minimization**:
   - Do not store unnecessary personal identifiers
   - Anonymize employee and applicant data
   - Apply differential privacy to aggregations

2. **Purpose Limitation**:
   - Data used only for compensation analysis
   - Clear consent for data usage
   - No secondary use without consent

3. **Data Access Controls**:
   - Role-based access control (RBAC)
   - Audit all data access
   - Encrypt sensitive fields at rest

4. **Right to Access & Deletion**:
   - Provide data export functionality
   - Support deletion requests
   - Cascade deletions properly

## Performance Considerations

### Indexing Strategy
- B-tree indexes for equality/range queries
- GIN indexes for full-text search
- GiST/ivfflat indexes for vector similarity
- Composite indexes for common query patterns

### Query Optimization
- Use prepared statements
- Implement connection pooling
- Cache frequently accessed data (Redis)
- Monitor slow queries (pg_stat_statements)

### Scalability
- Partition large tables by date
- Implement table archiving
- Use read replicas for analytics
- Consider sharding for extreme scale

## Next Steps

1. Create database migration scripts for all tables
2. Populate Mercer Job Library from Excel
3. Generate embeddings for all Mercer jobs
4. Load SSG Skills Framework data
5. Set up database replication and backups
6. Implement data validation triggers
7. Create database access layer (ORM/SQL queries)
8. Set up monitoring and alerting
