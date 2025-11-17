-- ============================================================================
-- Seed Script: Location Index
-- ============================================================================
-- Populates the location_index table with Singapore location data
-- Includes cost-of-living adjustments and location-based factors
--
-- Run with: psql -U job_pricing_user -d job_pricing_db -f 01-locations.sql
-- ============================================================================

\c job_pricing_db

-- Insert Singapore locations with cost-of-living adjustments
INSERT INTO location_index (
    location_name,
    location_code,
    country_code,
    region,
    city,
    cost_of_living_index,
    housing_index,
    transport_index,
    remarks,
    is_active
) VALUES
-- Central Business District (CBD) - Premium locations
('Singapore CBD - Raffles Place', 'SG-CBD-RP', 'SG', 'Central', 'Singapore', 1.15, 1.30, 1.10, 'Prime CBD location with highest real estate costs', true),
('Singapore CBD - Marina Bay', 'SG-CBD-MB', 'SG', 'Central', 'Singapore', 1.15, 1.30, 1.10, 'Central financial district', true),
('Singapore CBD - Shenton Way', 'SG-CBD-SW', 'SG', 'Central', 'Singapore', 1.15, 1.30, 1.10, 'Major business district', true),

-- City Area - Slightly lower than CBD
('Singapore - City Area', 'SG-CITY', 'SG', 'Central', 'Singapore', 1.10, 1.20, 1.05, 'General city area outside CBD', true),
('Singapore - Orchard', 'SG-ORCHARD', 'SG', 'Central', 'Singapore', 1.12, 1.25, 1.08, 'Retail and commercial hub', true),

-- Central Region - Residential/Commercial Mix
('Singapore - Central', 'SG-CENTRAL', 'SG', 'Central', 'Singapore', 1.08, 1.15, 1.05, 'Central residential areas', true),
('Singapore - Novena', 'SG-NOVENA', 'SG', 'Central', 'Singapore', 1.08, 1.15, 1.05, 'Medical and business hub', true),
('Singapore - Buona Vista', 'SG-BV', 'SG', 'Central', 'Singapore', 1.08, 1.15, 1.05, 'One-North tech hub', true),

-- East Region
('Singapore - East', 'SG-EAST', 'SG', 'East', 'Singapore', 1.00, 1.00, 1.00, 'Eastern residential areas', true),
('Singapore - Changi Business Park', 'SG-CBP', 'SG', 'East', 'Singapore', 1.02, 1.05, 1.02, 'Business park near airport', true),
('Singapore - Paya Lebar', 'SG-PL', 'SG', 'East', 'Singapore', 1.03, 1.08, 1.02, 'Emerging business district', true),
('Singapore - Tampines', 'SG-TAMP', 'SG', 'East', 'Singapore', 0.98, 0.95, 1.00, 'Regional center', true),

-- West Region
('Singapore - West', 'SG-WEST', 'SG', 'West', 'Singapore', 0.98, 0.95, 1.00, 'Western residential areas', true),
('Singapore - Jurong East', 'SG-JE', 'SG', 'West', 'Singapore', 1.00, 0.95, 1.05, 'Regional center with industrial areas', true),
('Singapore - Jurong Island', 'SG-JI', 'SG', 'West', 'Singapore', 0.95, 0.90, 1.10, 'Industrial area', true),
('Singapore - Tuas', 'SG-TUAS', 'SG', 'West', 'Singapore', 0.93, 0.88, 1.15, 'Industrial area', true),

-- North Region
('Singapore - North', 'SG-NORTH', 'SG', 'North', 'Singapore', 0.95, 0.92, 1.00, 'Northern residential areas', true),
('Singapore - Woodlands', 'SG-WL', 'SG', 'North', 'Singapore', 0.95, 0.92, 1.05, 'Near Malaysia border', true),

-- Northeast Region
('Singapore - Northeast', 'SG-NE', 'SG', 'Northeast', 'Singapore', 0.97, 0.93, 1.00, 'Northeastern residential areas', true),
('Singapore - Seletar', 'SG-SEL', 'SG', 'Northeast', 'Singapore', 0.98, 0.95, 1.02, 'Aerospace hub', true),
('Singapore - Punggol', 'SG-PGL', 'SG', 'Northeast', 'Singapore', 0.97, 0.93, 1.00, 'Digital district', true),

-- Islandwide / Flexible
('Singapore - Islandwide', 'SG-ISLAND', 'SG', 'Islandwide', 'Singapore', 1.00, 1.00, 1.00, 'No specific location, islandwide position', true),
('Singapore - Multiple Locations', 'SG-MULTI', 'SG', 'Multiple', 'Singapore', 1.00, 1.00, 1.00, 'Position spans multiple locations', true),
('Singapore - Remote', 'SG-REMOTE', 'SG', 'Remote', 'Singapore', 0.95, 0.90, 0.80, 'Work from home position', true)

ON CONFLICT (location_code) DO NOTHING;

-- ============================================================================
-- Verification Query
-- ============================================================================
-- SELECT location_name, location_code, cost_of_living_index, remarks
-- FROM location_index
-- WHERE country_code = 'SG'
-- ORDER BY cost_of_living_index DESC;
-- ============================================================================
