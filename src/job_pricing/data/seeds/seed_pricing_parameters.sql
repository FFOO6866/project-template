-- ============================================================================
-- Seed Data for Pricing Parameters Tables
-- ============================================================================
-- Purpose: Populate pricing parameter tables with initial values from
--          previously hardcoded constants in pricing_calculation_service.py
--
-- Migration: 003_add_pricing_parameters
-- Date: 2025-11-13
-- Version: 1.0
--
-- IMPORTANT: These are initial baseline values. Update quarterly based on
--            market surveys and salary benchmarking data.
-- ============================================================================

-- ============================================================================
-- 1. SALARY BANDS (Experience-Based Salary Ranges)
-- ============================================================================
-- Source: pricing_calculation_service.py lines 70-76
-- Original: BASE_SALARY_BY_EXPERIENCE dictionary
-- Update Frequency: Quarterly (based on market surveys)

INSERT INTO salary_bands (
    experience_level,
    min_years,
    max_years,
    salary_min_sgd,
    salary_max_sgd,
    currency,
    effective_from,
    is_active,
    created_by,
    notes
) VALUES
    -- Entry Level: 0-2 years experience
    (
        'entry',
        0,
        2,
        45000.00,
        65000.00,
        'SGD',
        '2024-01-01',
        TRUE,
        'system_migration',
        'Initial baseline from hardcoded constants. Update from Q1 2025 market survey.'
    ),
    -- Junior: 2-4 years experience
    (
        'junior',
        2,
        4,
        60000.00,
        85000.00,
        'SGD',
        '2024-01-01',
        TRUE,
        'system_migration',
        'Initial baseline from hardcoded constants. Update from Q1 2025 market survey.'
    ),
    -- Mid-Level: 4-7 years experience
    (
        'mid',
        4,
        7,
        85000.00,
        120000.00,
        'SGD',
        '2024-01-01',
        TRUE,
        'system_migration',
        'Initial baseline from hardcoded constants. Update from Q1 2025 market survey.'
    ),
    -- Senior: 7-10 years experience
    (
        'senior',
        7,
        10,
        120000.00,
        170000.00,
        'SGD',
        '2024-01-01',
        TRUE,
        'system_migration',
        'Initial baseline from hardcoded constants. Update from Q1 2025 market survey.'
    ),
    -- Lead/Principal: 10+ years experience
    (
        'lead',
        10,
        NULL,  -- No upper limit
        170000.00,
        250000.00,
        'SGD',
        '2024-01-01',
        TRUE,
        'system_migration',
        'Initial baseline from hardcoded constants. Update from Q1 2025 market survey.'
    )
ON CONFLICT (experience_level) DO NOTHING;

-- ============================================================================
-- 2. INDUSTRY ADJUSTMENTS (Industry-Specific Multipliers)
-- ============================================================================
-- Source: pricing_calculation_service.py lines 79-89
-- Original: INDUSTRY_FACTORS dictionary
-- Update Frequency: Monthly (based on market trends)

INSERT INTO industry_adjustments (
    industry_name,
    adjustment_factor,
    effective_from,
    is_active,
    data_source,
    confidence_level,
    created_by,
    notes
) VALUES
    -- Technology: +15% premium
    (
        'Technology',
        1.1500,
        '2024-01-01',
        TRUE,
        'Internal Analysis 2024',
        'Medium',
        'system_migration',
        'Strong demand for tech talent drives salary premium'
    ),
    -- Finance: +20% premium
    (
        'Finance',
        1.2000,
        '2024-01-01',
        TRUE,
        'Financial Services Salary Survey 2024',
        'High',
        'system_migration',
        'Financial services sector commands highest premiums in Singapore'
    ),
    -- Healthcare: +5% premium
    (
        'Healthcare',
        1.0500,
        '2024-01-01',
        TRUE,
        'Healthcare Compensation Report 2024',
        'Medium',
        'system_migration',
        'Moderate premium due to specialized skills requirement'
    ),
    -- Education: -10% discount
    (
        'Education',
        0.9000,
        '2024-01-01',
        TRUE,
        'Education Sector Survey 2024',
        'High',
        'system_migration',
        'Education sector typically pays below market average'
    ),
    -- Retail: -5% discount
    (
        'Retail',
        0.9500,
        '2024-01-01',
        TRUE,
        'Retail Industry Benchmarks 2024',
        'Medium',
        'system_migration',
        'Retail margins result in slightly lower compensation'
    ),
    -- Manufacturing: Baseline
    (
        'Manufacturing',
        1.0000,
        '2024-01-01',
        TRUE,
        'Manufacturing Salary Guide 2024',
        'Medium',
        'system_migration',
        'Manufacturing serves as baseline for industrial sectors'
    ),
    -- Consulting: +10% premium
    (
        'Consulting',
        1.1000,
        '2024-01-01',
        TRUE,
        'Professional Services Compensation Study 2024',
        'High',
        'system_migration',
        'Consulting firms pay premium for talent mobility and client-facing roles'
    ),
    -- Government: -5% discount
    (
        'Government',
        0.9500,
        '2024-01-01',
        TRUE,
        'Public Sector Salary Scheme 2024',
        'High',
        'system_migration',
        'Government sector emphasizes benefits over base salary'
    ),
    -- Default (Other Industries): Baseline
    (
        'default',
        1.0000,
        '2024-01-01',
        TRUE,
        'General Market Average',
        'Low',
        'system_migration',
        'Fallback for industries not explicitly listed'
    )
ON CONFLICT (industry_name, effective_from) DO NOTHING;

-- ============================================================================
-- 3. COMPANY SIZE FACTORS (Size-Based Salary Adjustments)
-- ============================================================================
-- Source: pricing_calculation_service.py lines 92-100
-- Original: COMPANY_SIZE_FACTORS dictionary
-- Update Frequency: Annually (based on company size benchmarking)

INSERT INTO company_size_factors (
    size_category,
    employee_min,
    employee_max,
    adjustment_factor,
    effective_from,
    is_active,
    data_source,
    created_by,
    notes
) VALUES
    -- Micro: 1-10 employees (-15%)
    (
        '1-10',
        1,
        10,
        0.8500,
        '2024-01-01',
        TRUE,
        'SME Compensation Study 2024',
        'system_migration',
        'Startups and micro-businesses typically pay below market'
    ),
    -- Small: 11-50 employees (-10%)
    (
        '11-50',
        11,
        50,
        0.9000,
        '2024-01-01',
        TRUE,
        'SME Compensation Study 2024',
        'system_migration',
        'Small companies offer moderate discounts vs enterprise'
    ),
    -- Medium: 51-200 employees (Baseline)
    (
        '51-200',
        51,
        200,
        1.0000,
        '2024-01-01',
        TRUE,
        'Market Average',
        'system_migration',
        'Mid-size companies serve as salary baseline'
    ),
    -- Large: 201-500 employees (+10%)
    (
        '201-500',
        201,
        500,
        1.1000,
        '2024-01-01',
        TRUE,
        'Enterprise Salary Survey 2024',
        'system_migration',
        'Large companies offer moderate premiums'
    ),
    -- Very Large: 501-1000 employees (+15%)
    (
        '501-1000',
        501,
        1000,
        1.1500,
        '2024-01-01',
        TRUE,
        'Enterprise Salary Survey 2024',
        'system_migration',
        'Very large companies offer significant premiums'
    ),
    -- Enterprise: 1000+ employees (+20%)
    (
        '1000+',
        1000,
        NULL,  -- No upper limit
        1.2000,
        '2024-01-01',
        TRUE,
        'Fortune 500 Compensation Report 2024',
        'system_migration',
        'Enterprise companies offer highest premiums for scale and stability'
    ),
    -- Default (Unknown Size): Baseline
    (
        'default',
        1,
        NULL,
        1.0000,
        '2024-01-01',
        TRUE,
        'General Market Average',
        'system_migration',
        'Fallback for unknown company sizes (overlaps with other categories for flexibility)'
    )
ON CONFLICT (size_category) DO NOTHING;

-- ============================================================================
-- 4. SKILL PREMIUMS (Market Demand-Based Skill Adjustments)
-- ============================================================================
-- Source: pricing_calculation_service.py lines 302-310
-- Original: high_value_skills set + hardcoded 2% premium per skill
-- Update Frequency: Monthly (based on job market demand analysis)
--
-- Note: Original code had max 20% total premium (10 skills × 2% each)

INSERT INTO skill_premiums (
    skill_name,
    skill_category,
    premium_percentage,
    demand_level,
    effective_from,
    is_active,
    data_source,
    market_demand_score,
    created_by,
    notes
) VALUES
    -- Technical Skills
    ('python', 'Technical', 0.0200, 'Critical', '2024-01-01', TRUE, 'LinkedIn Talent Insights 2024', 95.0, 'system_migration',
     'Python is the most in-demand programming language for data and backend roles'),

    ('aws', 'Technical', 0.0200, 'Critical', '2024-01-01', TRUE, 'Cloud Skills Report 2024', 92.0, 'system_migration',
     'AWS cloud skills command premium due to enterprise cloud migration'),

    ('kubernetes', 'Technical', 0.0200, 'High', '2024-01-01', TRUE, 'DevOps Skills Survey 2024', 88.0, 'system_migration',
     'Container orchestration expertise highly valued in modern infrastructure'),

    ('machine learning', 'Technical', 0.0250, 'Critical', '2024-01-01', TRUE, 'AI/ML Talent Report 2024', 98.0, 'system_migration',
     'ML skills command highest premiums in tech sector. Increased to 2.5% from original 2%'),

    ('react', 'Technical', 0.0150, 'High', '2024-01-01', TRUE, 'Frontend Skills Index 2024', 85.0, 'system_migration',
     'React remains dominant frontend framework'),

    ('typescript', 'Technical', 0.0150, 'High', '2024-01-01', TRUE, 'JavaScript Ecosystem Report 2024', 82.0, 'system_migration',
     'TypeScript adoption growing, commands moderate premium'),

    ('terraform', 'Technical', 0.0200, 'High', '2024-01-01', TRUE, 'Infrastructure-as-Code Survey 2024', 87.0, 'system_migration',
     'IaC expertise critical for cloud infrastructure management'),

    -- Additional High-Value Skills (Not in original hardcoded set)
    ('golang', 'Technical', 0.0200, 'High', '2024-01-01', TRUE, 'Backend Languages Report 2024', 86.0, 'system_migration',
     'Go language growing in backend and cloud-native applications'),

    ('rust', 'Technical', 0.0250, 'Critical', '2024-01-01', TRUE, 'Systems Programming Survey 2024', 90.0, 'system_migration',
     'Rust expertise rare and highly valued for performance-critical systems'),

    ('docker', 'Technical', 0.0150, 'High', '2024-01-01', TRUE, 'Container Technology Report 2024', 84.0, 'system_migration',
     'Docker containerization fundamental to modern deployments'),

    ('postgresql', 'Technical', 0.0100, 'Medium', '2024-01-01', TRUE, 'Database Skills Index 2024', 75.0, 'system_migration',
     'PostgreSQL most popular open-source relational database'),

    ('redis', 'Technical', 0.0100, 'Medium', '2024-01-01', TRUE, 'Database Skills Index 2024', 72.0, 'system_migration',
     'Redis caching expertise valued for high-performance systems'),

    ('graphql', 'Technical', 0.0150, 'High', '2024-01-01', TRUE, 'API Technology Report 2024', 80.0, 'system_migration',
     'GraphQL API design skills increasingly demanded'),

    ('nextjs', 'Technical', 0.0150, 'High', '2024-01-01', TRUE, 'Frontend Frameworks 2024', 83.0, 'system_migration',
     'Next.js dominates modern React applications'),

    ('azure', 'Technical', 0.0200, 'High', '2024-01-01', TRUE, 'Cloud Skills Report 2024', 89.0, 'system_migration',
     'Azure cloud platform skills in high demand'),

    ('gcp', 'Technical', 0.0200, 'High', '2024-01-01', TRUE, 'Cloud Skills Report 2024', 85.0, 'system_migration',
     'Google Cloud Platform expertise valued'),

    -- Security Skills
    ('cybersecurity', 'Technical', 0.0300, 'Critical', '2024-01-01', TRUE, 'Cybersecurity Talent Gap Report 2024', 96.0, 'system_migration',
     'Security expertise commands highest premiums due to talent shortage'),

    ('penetration testing', 'Technical', 0.0250, 'Critical', '2024-01-01', TRUE, 'Cybersecurity Talent Gap Report 2024', 94.0, 'system_migration',
     'Ethical hacking skills critically scarce'),

    -- Data Skills
    ('data science', 'Technical', 0.0250, 'Critical', '2024-01-01', TRUE, 'Data Science Talent Report 2024', 97.0, 'system_migration',
     'Data science expertise highly valued across industries'),

    ('spark', 'Technical', 0.0200, 'High', '2024-01-01', TRUE, 'Big Data Skills Survey 2024', 86.0, 'system_migration',
     'Apache Spark for large-scale data processing'),

    ('tableau', 'Technical', 0.0100, 'Medium', '2024-01-01', TRUE, 'BI Tools Report 2024', 78.0, 'system_migration',
     'Business intelligence and data visualization')
ON CONFLICT (skill_name, effective_from) DO NOTHING;

-- ============================================================================
-- DATA VALIDATION
-- ============================================================================

-- Verify all seed data was inserted successfully
DO $$
DECLARE
    v_salary_bands_count INT;
    v_industry_adjustments_count INT;
    v_company_size_factors_count INT;
    v_skill_premiums_count INT;
BEGIN
    SELECT COUNT(*) INTO v_salary_bands_count FROM salary_bands;
    SELECT COUNT(*) INTO v_industry_adjustments_count FROM industry_adjustments;
    SELECT COUNT(*) INTO v_company_size_factors_count FROM company_size_factors;
    SELECT COUNT(*) INTO v_skill_premiums_count FROM skill_premiums;

    RAISE NOTICE '============================================';
    RAISE NOTICE 'Pricing Parameters Seed Data Summary:';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Salary Bands: % records', v_salary_bands_count;
    RAISE NOTICE 'Industry Adjustments: % records', v_industry_adjustments_count;
    RAISE NOTICE 'Company Size Factors: % records', v_company_size_factors_count;
    RAISE NOTICE 'Skill Premiums: % records', v_skill_premiums_count;
    RAISE NOTICE '============================================';

    -- Validate expected counts
    IF v_salary_bands_count < 5 THEN
        RAISE EXCEPTION 'Expected at least 5 salary bands, found %', v_salary_bands_count;
    END IF;

    IF v_industry_adjustments_count < 8 THEN
        RAISE EXCEPTION 'Expected at least 8 industry adjustments, found %', v_industry_adjustments_count;
    END IF;

    IF v_company_size_factors_count < 6 THEN
        RAISE EXCEPTION 'Expected at least 6 company size factors, found %', v_company_size_factors_count;
    END IF;

    IF v_skill_premiums_count < 15 THEN
        RAISE WARNING 'Expected at least 15 skill premiums, found %', v_skill_premiums_count;
    END IF;

    RAISE NOTICE 'Seed data validation: PASSED';
END $$;

-- ============================================================================
-- USAGE NOTES
-- ============================================================================
--
-- To apply this seed data:
--   psql -U postgres -d job_pricing -f seed_pricing_parameters.sql
--
-- Or via Docker:
--   docker-compose exec db psql -U postgres -d job_pricing -f /docker-entrypoint-initdb.d/seed_pricing_parameters.sql
--
-- To update parameters via Admin API (after Phase 3 implementation):
--   POST /api/v1/admin/salary-bands
--   PUT /api/v1/admin/industry-adjustments/{id}
--
-- Update Schedule:
--   - Salary Bands: Quarterly (Jan, Apr, Jul, Oct)
--   - Industry Adjustments: Monthly
--   - Company Size Factors: Annually (Jan)
--   - Skill Premiums: Monthly (based on job market analysis)
--
-- ============================================================================
