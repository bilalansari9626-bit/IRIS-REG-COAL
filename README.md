# IRIS-REG-COAL — Coal Phase-Out Structural Revier Zones

**Technical Assignment:** Task 124  
**Technology:** Python 3.12, GeoPandas, PostgreSQL/PostGIS, Docker, QGIS

## 1. Overview

This project implements a reproducible geospatial data-processing workflow for identifying and mapping German coal-transition regions under the *Investitionsgesetz Kohleregionen* (InvKG).

The workflow processes official German administrative boundaries, associates district polygons with designated coal-transition regions, validates spatial data, and loads the results into an isolated PostgreSQL/PostGIS staging environment.

The implementation is intended for preliminary regulatory and spatial screening, not for legal eligibility determinations.

## 2. Data Sources and Provenance

**Administrative boundaries**

- Provider: Bundesamt für Kartographie und Geodäsie (BKG)
- Dataset: VG250 — German administrative boundaries
- Spatial reference system: EPSG:25832 (ETRS89 / UTM zone 32N)

**Legal reference**

- Legislation: Investitionsgesetz Kohleregionen (InvKG)
- Relevant provision: § 2
- Official reference: https://www.gesetze-im-internet.de/invkg/__2.html

District-to-region assignments are maintained in `config/coal_region_membership.csv`.

The repository includes processed GeoPackage datasets. The original BKG archive is excluded because of its size. The exact boundary edition and legal-version alignment remain subject to verification.

## 3. Processing Workflow

The pipeline performs the following operations:

1. Processes official administrative boundary polygons.
2. Normalizes district identifiers and geometry attributes.
3. Associates districts with coal-transition regions using a configured membership mapping.
4. Validates required attributes, district counts, identifiers, coordinate reference systems, and geometries.
5. Generates district-level and dissolved regional spatial outputs.
6. Loads the district records into an isolated PostGIS staging table using conflict-aware upserts.
7. Generates validation and ingestion reports.

## 4. Output Dataset

**Database table:** `iris_staging.coal_phaseout_reviere`

The current dataset contains **22 district records** distributed across three coal-transition regions.

| Region | District records |
|---|---:|
| Lausitzer Revier | 7 |
| Rheinisches Revier | 7 |
| Mitteldeutsches Revier | 8 |
| **Total** | **22** |

The project also produces processed GeoPackage files for district boundaries, coal-region districts, and dissolved regional geometries.

The staging records include district identifiers, district names, regional assignments, legal references, source metadata, and spatial geometries.

## 5. Setup and Reproducible Execution

### Requirements

- Docker Desktop with Docker Compose
- Python 3.11 or later for optional local execution
- Git for cloning the repository

### Docker workflow — recommended

Clone the repository:

`git clone https://github.com/bilalansari9626-bit/IRIS-REG-COAL.git`

Enter the project directory:

`cd IRIS-REG-COAL`

Copy `.env.example` to `.env` and configure a local development database password.

Start the isolated PostGIS database:

`docker compose up -d`

Build the ETL image:

`docker compose --profile etl build etl`

Run the ingestion pipeline:

`docker compose --profile etl run --rm etl`

Review the generated ingestion report:

`reports/postgis_ingestion.json`

For a newly initialized database volume, the Docker configuration executes `sql/create_staging_table.sql` to initialize the staging database objects.

The ETL reads the included processed GeoPackage through a read-only volume mount and loads records into `iris_staging.coal_phaseout_reviere`.

Repeated execution uses conflict-aware upserts to avoid duplicate district records.

**Important:** Docker database volumes persist between runs. Do not remove the database volume unless intentionally resetting the development environment.

### Optional local Python execution

Install the Python dependencies:

`python -m pip install -r requirements.txt`

Start the PostGIS service:

`docker compose up -d`

Run the ingestion script:

`python src/load_coal_postgis.py`

Local execution uses the database connection settings defined in the Python loader and environment configuration.

## 6. Automated Testing

Run the test suite from the project directory:

`python -m pytest tests -v`

**Latest verified result: 11 tests passed.**

The test suite covers:

- Expected dataset counts
- Unique district identifiers
- Coal-region membership counts
- Coordinate reference system checks
- Geometry validity
- PostGIS staging record counts
- Representative missing, malformed, and duplicate input conditions

The four negative-input tests use a standalone validation helper rather than directly exercising the production loader's validation path. This is a known test-coverage limitation.

The tests that query PostGIS require a running database populated with the representative staging dataset.

## 7. Validation Query

The following SQL query verifies the regional record distribution:

```sql
SELECT
    region,
    COUNT(*) AS district_count
FROM iris_staging.coal_phaseout_reviere
GROUP BY region
ORDER BY region;
```

Expected result:

| Region | district_count |
|---|---:|
| Lausitzer Revier | 7 |
| Mitteldeutsches Revier | 8 |
| Rheinisches Revier | 7 |

## 8. Validation and Quality Reports

The workflow provides the following report artifacts:

- `reports/coal_region_validation.json` — coal-region spatial validation and coverage information.
- `reports/postgis_ingestion.json` — staging ingestion results and database record counts.

The latest successful PostGIS ingestion confirmed 22 records with the expected regional distribution.

## Map Deliverables

The repository includes a cartographic visualization of Germany's three coal-transition regions, prepared using QGIS.

- **[View Map (PNG)](Maps/IRIS_Coal_Transition_Regions.png)**
- **[Download Map (PDF)](Maps/IRIS_Coal_Transition_Regions.pdf)**
- **[Editable QGIS Project](IRIS_Coal_Transition_Regions.qgz)**

The map displays the Rheinisches, Mitteldeutsches, and Lausitzer Reviere over German administrative district boundaries.

The layout includes a legend, north arrow, scale bar, and source attribution. The QGIS project uses relative paths to support portability.

**Data source:** BKG VG250  
**Legal reference:** InvKG § 2  
**Coordinate reference system:** EPSG:25832

The visualization represents the configured district-level coal-transition regions and should not be interpreted as a definitive legal eligibility map.

## 9. Assumptions and Known Limitations

- The workflow is designed for preliminary spatial and regulatory screening. It does not provide legal advice or establish project eligibility.
- District membership is configured with reference to InvKG § 2.
- The exact edition of the BKG boundary dataset must be verified against the official source archive for temporal and legal consistency.
- Administrative district membership does not necessarily represent every legally relevant subdistrict boundary or special eligibility condition.
- The dataset does not independently establish facility-specific closure dates, coal phase-out milestones, or operational status.
- The current output focuses on administrative region membership. Additional opportunity overlays and facility-level attributes would require separate sourced datasets.
- The original BKG source archive is not included in the repository. Full regeneration from raw boundaries requires obtaining the corresponding official source dataset.
- Processed GeoPackage files are included to support repeatable ingestion and validation.
- Automated negative-input tests do not yet exercise the production validation function directly.

## 10. Data Safety and Environment Isolation

The implementation writes only to the designated staging table:

`iris_staging.coal_phaseout_reviere`

The workflow does not require access to or modify production systems or the `iris_core` schema.

Database credentials are configured locally through environment variables and should not be committed to version control.

## 11. Submission Scope

This repository provides Python processing scripts, pinned Python dependencies, an example environment configuration, Docker build and Compose configurations, staging SQL, processed spatial datasets, automated tests, and validation reports.

The deliverable demonstrates a working, reproducible staging ingestion workflow for coal-transition district membership, with documented assumptions and limitations.

## Validation and known limitations

- PostGIS ingestion: 22 coal districts across 3 regions.
- Geometry validation: all 22 district geometries valid.
- Spatial validation: 22 district-to-region matches, 0 mismatches.
- Regional status represents InvKG funding eligibility, not individual
  power plant closure status.
- Opportunity overlay: not implemented; requires a separate sourced dataset.
- Legal version date and source edition require verification.

Reports:
- reports/postgis_ingestion.json
- reports/spatial_validation.json

## Supplementary Coal Power Plant Status Data

The project includes a supplementary extraction from the official
Bundesnetzagentur Power Plant List (Kraftwerksliste).

Run:

    python src/process_powerplant_status.py

Outputs:
- data/opportunities/coal_powerplant_status.csv
- reports/coal_powerplant_status.json

Validation results:
- 2,614 source records
- 232 coal power plant records
- 20 records with missing identifiers
- 0 duplicate non-empty identifiers

Limitations:
- The source CSV does not contain geographic coordinates or district codes.
- Individual plants cannot be reliably assigned to the 22 coal districts.
- Plant operating status is distinct from regional eligibility under InvKG.
- This supplementary dataset is not used for the spatial join.