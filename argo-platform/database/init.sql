-- Initialize PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'argo_user') THEN
        CREATE ROLE argo_user WITH LOGIN PASSWORD 'argo_password';
    END IF;
END
$$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE argo_platform TO argo_user;
GRANT ALL ON SCHEMA public TO argo_user;

-- Create sample ARGO float data for demonstration
INSERT INTO argo_floats (id, float_id, platform_number, project_name, pi_name, data_center, deployment_date, status, location, created_at) 
VALUES 
    (uuid_generate_v4(), 'ARGO_1001', '1001', 'Global Ocean Monitoring', 'Dr. Ocean Smith', 'AOML', '2023-01-15'::timestamp, 'active', ST_Point(145.5, -25.3), NOW()),
    (uuid_generate_v4(), 'ARGO_1002', '1002', 'Pacific Climate Study', 'Dr. Marine Johnson', 'PMEL', '2023-02-20'::timestamp, 'active', ST_Point(175.2, -35.7), NOW()),
    (uuid_generate_v4(), 'ARGO_1003', '1003', 'Atlantic Research', 'Dr. Deep Waters', 'WHOI', '2023-03-10'::timestamp, 'active', ST_Point(-45.8, 20.1), NOW())
ON CONFLICT (float_id) DO NOTHING;

-- Function to generate sample ARGO profile data
CREATE OR REPLACE FUNCTION generate_sample_profiles() RETURNS VOID AS $$
DECLARE
    float_rec RECORD;
    profile_id UUID;
    profile_date TIMESTAMP;
    lat FLOAT;
    lon FLOAT;
    i INTEGER;
    j INTEGER;
    depth_val FLOAT;
    temp_val FLOAT;
    sal_val FLOAT;
BEGIN
    -- For each float, generate sample profiles
    FOR float_rec IN SELECT id, float_id FROM argo_floats LOOP
        -- Generate 10 profiles per float
        FOR i IN 1..10 LOOP
            profile_id := uuid_generate_v4();
            profile_date := NOW() - INTERVAL '1 day' * (i * 5);
            
            -- Simulate float movement
            lat := -30 + (RANDOM() * 20);  -- Southern Ocean region
            lon := 140 + (RANDOM() * 40);  -- Pacific region
            
            -- Insert profile
            INSERT INTO argo_profiles (
                id, float_id, cycle_number, profile_date, latitude, longitude, 
                location, profile_type, data_mode, created_at
            ) VALUES (
                profile_id, float_rec.id, i, profile_date, lat, lon,
                ST_Point(lon, lat), 'primary', 'R', NOW()
            );
            
            -- Generate measurements for this profile (0 to 2000m depth)
            FOR j IN 0..20 LOOP
                depth_val := j * 100;  -- 0, 100, 200, ... 2000m
                
                -- Realistic temperature profile (warm at surface, cold at depth)
                IF depth_val <= 50 THEN
                    temp_val := 25 + (RANDOM() * 5);  -- 25-30°C surface
                ELSIF depth_val <= 200 THEN
                    temp_val := 15 + (RANDOM() * 5);  -- 15-20°C thermocline
                ELSE
                    temp_val := 2 + (RANDOM() * 6);   -- 2-8°C deep water
                END IF;
                
                -- Realistic salinity (34-37 PSU)
                sal_val := 34.0 + (RANDOM() * 3.0);
                
                -- Insert measurement
                INSERT INTO argo_measurements (
                    id, profile_id, pressure, depth, temperature, salinity, 
                    oxygen, quality_flag, created_at
                ) VALUES (
                    uuid_generate_v4(), profile_id, depth_val * 1.02, depth_val, 
                    temp_val, sal_val, 200 + (RANDOM() * 100), '1', NOW()
                );
            END LOOP;
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Generate sample data
SELECT generate_sample_profiles();

-- Create sample ocean anomalies
INSERT INTO ocean_anomalies (
    id, anomaly_type, severity, start_date, end_date, latitude, longitude, 
    location, description, confidence_score, data_source, created_at
) VALUES 
    (uuid_generate_v4(), 'heatwave', 'high', NOW() - INTERVAL '5 days', NOW() - INTERVAL '2 days', 
     -20.5, 155.3, ST_Point(155.3, -20.5), 
     'Marine heatwave detected with temperatures 3°C above normal', 0.89, 'ARGO', NOW()),
    (uuid_generate_v4(), 'cold_spell', 'medium', NOW() - INTERVAL '10 days', NOW() - INTERVAL '7 days',
     -35.2, 175.8, ST_Point(175.8, -35.2),
     'Cold water mass intrusion detected', 0.76, 'ARGO', NOW()),
    (uuid_generate_v4(), 'high_salinity', 'low', NOW() - INTERVAL '3 days', NULL,
     -25.1, 140.7, ST_Point(140.7, -25.1),
     'Elevated salinity levels observed', 0.65, 'ARGO', NOW())
ON CONFLICT DO NOTHING;

-- Create sample satellite data
INSERT INTO satellite_data (
    id, satellite_name, instrument, data_type, measurement_date, 
    latitude, longitude, location, value, unit, quality_level, created_at
) VALUES
    (uuid_generate_v4(), 'MODIS-Aqua', 'MODIS', 'SST', NOW() - INTERVAL '1 day', -22.5, 150.3, ST_Point(150.3, -22.5), 28.5, 'Celsius', 'L2', NOW()),
    (uuid_generate_v4(), 'VIIRS-SNPP', 'VIIRS', 'SST', NOW() - INTERVAL '1 day', -25.8, 155.7, ST_Point(155.7, -25.8), 26.2, 'Celsius', 'L2', NOW()),
    (uuid_generate_v4(), 'Sentinel-3A', 'SLSTR', 'SST', NOW() - INTERVAL '2 days', -30.1, 145.9, ST_Point(145.9, -30.1), 24.8, 'Celsius', 'L2', NOW())
ON CONFLICT DO NOTHING;

-- Create sample users
INSERT INTO users (
    id, email, full_name, role, is_active, created_at, updated_at
) VALUES
    (uuid_generate_v4(), 'scientist@argo.com', 'Dr. Ocean Researcher', 'scientist', true, NOW(), NOW()),
    (uuid_generate_v4(), 'policy@argo.com', 'Policy Maker', 'policymaker', true, NOW(), NOW()),
    (uuid_generate_v4(), 'student@argo.com', 'Marine Student', 'student', true, NOW(), NOW()),
    (uuid_generate_v4(), 'admin@argo.com', 'System Administrator', 'admin', true, NOW(), NOW())
ON CONFLICT (email) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_argo_profiles_date ON argo_profiles(profile_date);
CREATE INDEX IF NOT EXISTS idx_argo_profiles_location ON argo_profiles USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_argo_measurements_profile_id ON argo_measurements(profile_id);
CREATE INDEX IF NOT EXISTS idx_argo_measurements_depth ON argo_measurements(depth);
CREATE INDEX IF NOT EXISTS idx_satellite_data_date ON satellite_data(measurement_date);
CREATE INDEX IF NOT EXISTS idx_satellite_data_location ON satellite_data USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_ocean_anomalies_date ON ocean_anomalies(start_date);
CREATE INDEX IF NOT EXISTS idx_ocean_anomalies_location ON ocean_anomalies USING GIST(location);

COMMIT;