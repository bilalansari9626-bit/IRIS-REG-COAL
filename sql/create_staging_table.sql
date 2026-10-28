
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS iris_staging;

CREATE TABLE IF NOT EXISTS iris_staging.coal_phaseout_reviere (
    district_code VARCHAR(10) PRIMARY KEY,
    district_name TEXT NOT NULL,
    region TEXT NOT NULL,
    legal_reference TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_version TEXT NOT NULL,
    geometry geometry(MultiPolygon, 25832) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_coal_reviere_geometry
ON iris_staging.coal_phaseout_reviere
USING GIST (geometry);

ALTER TABLE iris_staging.coal_phaseout_reviere
    ADD COLUMN IF NOT EXISTS phaseout_status TEXT,
    ADD COLUMN IF NOT EXISTS status_as_of DATE,
    ADD COLUMN IF NOT EXISTS status_source_url TEXT,
    ADD COLUMN IF NOT EXISTS legal_version_date DATE;