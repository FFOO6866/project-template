-- ============================================================================
-- Seed Script: Location Index (Fixed)
-- ============================================================================
-- Populates the location_index table with Singapore location data
-- Includes cost-of-living adjustments
--
-- Schema: location_name, cost_of_living_index, region, postal_code_prefix,
--         effective_date, last_updated
-- ============================================================================

-- Insert Singapore locations with cost-of-living adjustments
INSERT INTO location_index (
    location_name,
    cost_of_living_index,
    region,
    postal_code_prefix,
    effective_date,
    last_updated
) VALUES
-- Central Business District (CBD) - Premium locations
('Singapore CBD - Raffles Place', 1.15, 'Central', '01', '2025-01-01', NOW()),
('Singapore CBD - Marina Bay', 1.15, 'Central', '01', '2025-01-01', NOW()),
('Singapore CBD - Shenton Way', 1.15, 'Central', '06', '2025-01-01', NOW()),

-- City Area - Slightly lower than CBD
('Singapore City - Orchard', 1.10, 'Central', '23', '2025-01-01', NOW()),
('Singapore City - Bugis', 1.08, 'Central', '18', '2025-01-01', NOW()),
('Singapore City - Chinatown', 1.08, 'Central', '05', '2025-01-01', NOW()),

-- East Region
('Singapore East - Tampines', 0.95, 'East', '52', '2025-01-01', NOW()),
('Singapore East - Bedok', 0.93, 'East', '46', '2025-01-01', NOW()),
('Singapore East - Pasir Ris', 0.92, 'East', '51', '2025-01-01', NOW()),
('Singapore East - Changi', 0.90, 'East', '50', '2025-01-01', NOW()),

-- West Region
('Singapore West - Jurong East', 0.92, 'West', '60', '2025-01-01', NOW()),
('Singapore West - Clementi', 0.95, 'West', '12', '2025-01-01', NOW()),
('Singapore West - Bukit Batok', 0.90, 'West', '65', '2025-01-01', NOW()),
('Singapore West - Choa Chu Kang', 0.88, 'West', '68', '2025-01-01', NOW()),

-- North Region
('Singapore North - Woodlands', 0.88, 'North', '73', '2025-01-01', NOW()),
('Singapore North - Yishun', 0.90, 'North', '76', '2025-01-01', NOW()),
('Singapore North - Sembawang', 0.88, 'North', '75', '2025-01-01', NOW()),

-- Northeast Region
('Singapore Northeast - Serangoon', 0.95, 'Northeast', '55', '2025-01-01', NOW()),
('Singapore Northeast - Punggol', 0.93, 'Northeast', '82', '2025-01-01', NOW()),
('Singapore Northeast - Sengkang', 0.93, 'Northeast', '54', '2025-01-01', NOW()),
('Singapore Northeast - Hougang', 0.92, 'Northeast', '53', '2025-01-01', NOW()),

-- Central Suburbs
('Singapore Central - Bishan', 1.00, 'Central', '57', '2025-01-01', NOW()),
('Singapore Central - Toa Payoh', 0.98, 'Central', '31', '2025-01-01', NOW()),
('Singapore Central - Queenstown', 1.02, 'Central', '14', '2025-01-01', NOW())

ON CONFLICT (location_name) DO UPDATE
SET
    cost_of_living_index = EXCLUDED.cost_of_living_index,
    region = EXCLUDED.region,
    postal_code_prefix = EXCLUDED.postal_code_prefix,
    effective_date = EXCLUDED.effective_date,
    last_updated = NOW();

-- Verification
SELECT COUNT(*) as total_locations FROM location_index;
