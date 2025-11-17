-- ============================================================================
-- Seed Script: Grade Salary Bands
-- ============================================================================
-- Populates the grade_salary_bands table with company salary grade structure
-- Based on Mercer career levels and market positioning
--
-- Run with: psql -U job_pricing_user -d job_pricing_db -f 02-grade-salary-bands.sql
-- ============================================================================

\c job_pricing_db

-- Insert salary bands for each grade
-- Grades align with Mercer career levels (M1-M6, P1-P6, E1-E5)
-- Salaries are in SGD and represent P50 (median) market position

INSERT INTO grade_salary_bands (
    grade,
    grade_description,
    salary_min,
    salary_max,
    midpoint,
    currency,
    market_position,
    effective_date,
    remarks
) VALUES

-- ============================================================================
-- Management Grades (M1-M6)
-- ============================================================================

('M1', 'Junior Manager / Supervisor', 3500, 5000, 4250, 'SGD', 'P50', '2025-01-01',
 'Entry-level management. Supervises small teams or projects.'),

('M2', 'Manager / Team Lead', 4500, 6500, 5500, 'SGD', 'P50', '2025-01-01',
 'Manages team operations. 3-5 years experience.'),

('M3', 'Senior Manager', 6000, 9000, 7500, 'SGD', 'P50', '2025-01-01',
 'Manages multiple teams or large projects. 5-8 years experience.'),

('M4', 'Principal Manager / Associate Director', 8000, 12000, 10000, 'SGD', 'P50', '2025-01-01',
 'Strategic leadership role. 8-12 years experience.'),

('M5', 'Director', 12000, 18000, 15000, 'SGD', 'P50', '2025-01-01',
 'Department head. Sets strategic direction. 12-15 years experience.'),

('M6', 'Senior Director / VP', 18000, 28000, 23000, 'SGD', 'P50', '2025-01-01',
 'Executive leadership. Multi-department oversight. 15+ years experience.'),

-- ============================================================================
-- Professional Grades (P1-P6)
-- ============================================================================

('P1', 'Junior Professional', 3000, 4500, 3750, 'SGD', 'P50', '2025-01-01',
 'Entry-level professional. Fresh graduates. 0-2 years experience.'),

('P2', 'Professional', 4000, 6000, 5000, 'SGD', 'P50', '2025-01-01',
 'Experienced professional. 2-4 years experience.'),

('P3', 'Senior Professional', 5500, 8000, 6750, 'SGD', 'P50', '2025-01-01',
 'Subject matter expert. 4-7 years experience.'),

('P4', 'Principal Professional / Lead', 7500, 11000, 9250, 'SGD', 'P50', '2025-01-01',
 'Technical leadership. 7-10 years experience.'),

('P5', 'Senior Principal / Architect', 11000, 16000, 13500, 'SGD', 'P50', '2025-01-01',
 'Domain expert. 10-15 years experience.'),

('P6', 'Distinguished Professional / Fellow', 16000, 24000, 20000, 'SGD', 'P50', '2025-01-01',
 'Industry expert. Thought leader. 15+ years experience.'),

-- ============================================================================
-- Executive Grades (E1-E5)
-- ============================================================================

('E1', 'Vice President (VP)', 20000, 30000, 25000, 'SGD', 'P50', '2025-01-01',
 'Senior executive. Business unit leadership.'),

('E2', 'Senior Vice President (SVP)', 30000, 45000, 37500, 'SGD', 'P50', '2025-01-01',
 'Executive management. Division leadership.'),

('E3', 'Executive Vice President (EVP)', 45000, 70000, 57500, 'SGD', 'P50', '2025-01-01',
 'C-suite support. Strategic business leadership.'),

('E4', 'Chief Officer (COO, CTO, CFO)', 70000, 120000, 95000, 'SGD', 'P50', '2025-01-01',
 'C-level executive. Company-wide strategic leadership.'),

('E5', 'Chief Executive Officer (CEO)', 100000, 200000, 150000, 'SGD', 'P50', '2025-01-01',
 'Top executive. Overall company leadership.')

ON CONFLICT (grade) DO NOTHING;

-- ============================================================================
-- Add career progression path metadata (optional but useful)
-- ============================================================================
-- This helps with understanding typical career progression

COMMENT ON TABLE grade_salary_bands IS
'Salary bands aligned with Mercer career levels.
Management track (M): Leadership and people management focus.
Professional track (P): Individual contributor and technical expertise focus.
Executive track (E): Senior executive and C-suite positions.
Typical progression: P1→P2→P3→P4→P5→P6 or P3→M2→M3→M4→M5→E1→E2→E3→E4→E5';

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- View all salary bands ordered by minimum salary
-- SELECT grade, grade_description, salary_min, salary_max, midpoint
-- FROM grade_salary_bands
-- ORDER BY salary_min;

-- View management track only
-- SELECT grade, grade_description, salary_min, salary_max, midpoint
-- FROM grade_salary_bands
-- WHERE grade LIKE 'M%'
-- ORDER BY salary_min;

-- View professional track only
-- SELECT grade, grade_description, salary_min, salary_max, midpoint
-- FROM grade_salary_bands
-- WHERE grade LIKE 'P%'
-- ORDER BY salary_min;

-- View executive track only
-- SELECT grade, grade_description, salary_min, salary_max, midpoint
-- FROM grade_salary_bands
-- WHERE grade LIKE 'E%'
-- ORDER BY salary_min;

-- ============================================================================
