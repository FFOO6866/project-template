-- ============================================================================
-- Seed Script: Grade Salary Bands (Fixed)
-- ============================================================================
-- Populates the grade_salary_bands table with company salary grade structure
-- Based on Mercer career levels and market positioning
--
-- Schema: internal_grade, absolute_min, absolute_max, currency, market_position,
--         effective_date, expiry_date, created_at, updated_at
-- ============================================================================

-- Insert salary bands for each grade
-- Grades align with Mercer career levels (M1-M6, P1-P6, E1-E5)
-- Salaries are in SGD and represent P50 (median) market position

INSERT INTO grade_salary_bands (
    internal_grade,
    absolute_min,
    absolute_max,
    currency,
    market_position,
    effective_date,
    expiry_date,
    created_at,
    updated_at
) VALUES

-- ============================================================================
-- Management Grades (M1-M6)
-- ============================================================================

('M1', 3500.00, 5000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('M2', 4500.00, 6500.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('M3', 6000.00, 9000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('M4', 8000.00, 12000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('M5', 12000.00, 18000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('M6', 18000.00, 28000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),

-- ============================================================================
-- Professional Grades (P1-P6)
-- ============================================================================

('P1', 2500.00, 3500.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('P2', 3000.00, 4500.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('P3', 4000.00, 6000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('P4', 5500.00, 8000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('P5', 7500.00, 11000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('P6', 10000.00, 15000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),

-- ============================================================================
-- Executive Grades (E1-E5)
-- ============================================================================

('E1', 18000.00, 28000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('E2', 25000.00, 40000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('E3', 35000.00, 55000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('E4', 50000.00, 80000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW()),
('E5', 80000.00, 150000.00, 'SGD', 50.00, '2025-01-01', NULL, NOW(), NOW())

ON CONFLICT (internal_grade) DO UPDATE
SET
    absolute_min = EXCLUDED.absolute_min,
    absolute_max = EXCLUDED.absolute_max,
    currency = EXCLUDED.currency,
    market_position = EXCLUDED.market_position,
    effective_date = EXCLUDED.effective_date,
    expiry_date = EXCLUDED.expiry_date,
    updated_at = NOW();

-- Verification
SELECT COUNT(*) as total_grades FROM grade_salary_bands;
SELECT internal_grade, absolute_min, absolute_max FROM grade_salary_bands ORDER BY internal_grade;
