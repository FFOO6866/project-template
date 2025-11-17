-- ==============================================================================
-- Migration 003: Add Pricing Parameters Tables
-- ==============================================================================
-- Date: 2025-11-13
-- Purpose: Deploy database-driven pricing parameter tables
-- Replaces: Hardcoded constants in pricing_calculation_service.py
-- ==============================================================================

-- 1. Create salary_bands table
CREATE TABLE IF NOT EXISTS salary_bands (
    id SERIAL PRIMARY KEY,
    experience_level VARCHAR(50) NOT NULL UNIQUE,
    min_years INTEGER NOT NULL CHECK (min_years >= 0),
    max_years INTEGER CHECK (max_years IS NULL OR max_years > min_years),
    salary_min_sgd NUMERIC(12, 2) NOT NULL CHECK (salary_min_sgd > 0),
    salary_max_sgd NUMERIC(12, 2) NOT NULL CHECK (salary_max_sgd > salary_min_sgd),
    currency VARCHAR(3) NOT NULL DEFAULT 'SGD',
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    created_by VARCHAR(255),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS ix_salary_bands_experience_level ON salary_bands(experience_level);
CREATE INDEX IF NOT EXISTS ix_salary_bands_active ON salary_bands(is_active, effective_from, effective_to);

-- 2. Create industry_adjustments table
CREATE TABLE IF NOT EXISTS industry_adjustments (
    id SERIAL PRIMARY KEY,
    industry_name VARCHAR(100) NOT NULL,
    adjustment_factor NUMERIC(5, 4) NOT NULL CHECK (adjustment_factor > 0 AND adjustment_factor BETWEEN 0.5 AND 2.0),
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    data_source VARCHAR(255),
    sample_size INTEGER,
    confidence_level VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    created_by VARCHAR(255),
    notes TEXT,
    CONSTRAINT uq_industry_effective_date UNIQUE (industry_name, effective_from)
);

CREATE INDEX IF NOT EXISTS ix_industry_adjustments_industry_name ON industry_adjustments(industry_name);
CREATE INDEX IF NOT EXISTS ix_industry_adjustments_active ON industry_adjustments(is_active, industry_name);

-- 3. Create company_size_factors table
CREATE TABLE IF NOT EXISTS company_size_factors (
    id SERIAL PRIMARY KEY,
    size_category VARCHAR(50) NOT NULL UNIQUE,
    employee_min INTEGER NOT NULL CHECK (employee_min > 0),
    employee_max INTEGER CHECK (employee_max IS NULL OR employee_max > employee_min),
    adjustment_factor NUMERIC(5, 4) NOT NULL CHECK (adjustment_factor > 0 AND adjustment_factor BETWEEN 0.5 AND 2.0),
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    data_source VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    created_by VARCHAR(255),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS ix_company_size_factors_size_category ON company_size_factors(size_category);
CREATE INDEX IF NOT EXISTS ix_company_size_factors_active ON company_size_factors(is_active, size_category);

-- 4. Create skill_premiums table
CREATE TABLE IF NOT EXISTS skill_premiums (
    id SERIAL PRIMARY KEY,
    skill_name VARCHAR(255) NOT NULL,
    skill_category VARCHAR(100),
    premium_percentage NUMERIC(5, 4) NOT NULL CHECK (premium_percentage >= 0 AND premium_percentage <= 0.50),
    demand_level VARCHAR(20),
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    data_source VARCHAR(255),
    market_demand_score NUMERIC(5, 2) CHECK (market_demand_score IS NULL OR (market_demand_score >= 0 AND market_demand_score <= 100)),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    created_by VARCHAR(255),
    notes TEXT,
    CONSTRAINT uq_skill_effective_date UNIQUE (skill_name, effective_from)
);

CREATE INDEX IF NOT EXISTS ix_skill_premiums_skill_name ON skill_premiums(skill_name);
CREATE INDEX IF NOT EXISTS ix_skill_premiums_active ON skill_premiums(is_active, skill_name);

-- 5. Create parameter_change_history table (audit trail)
CREATE TABLE IF NOT EXISTS parameter_change_history (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT now(),
    change_reason TEXT,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_parameter_change_history_table_name ON parameter_change_history(table_name);
CREATE INDEX IF NOT EXISTS ix_parameter_change_history_record_id ON parameter_change_history(record_id);
CREATE INDEX IF NOT EXISTS ix_parameter_change_history_table_record ON parameter_change_history(table_name, record_id);

-- ==============================================================================
-- Verification Queries
-- ==============================================================================
-- Run after migration to verify tables were created:
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE '%salary%' OR tablename LIKE '%industry%' OR tablename LIKE '%skill%' OR tablename LIKE '%company%' OR tablename LIKE '%parameter%';
-- ==============================================================================
