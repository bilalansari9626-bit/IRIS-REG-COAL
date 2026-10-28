IRIS-REG-COAL — Coal Phase-Out Structural Revier Zones

Technical Assignment: Task 124

Technology: Python 3.12, GeoPandas, PostgreSQL/PostGIS, Docker, QGIS 

Overview

This project implements a reproducible geospatial processing workflow for identifying and mapping German coal-transition regions under the Investitionsgesetz Kohleregionen (InvKG).

The workflow normalizes official German administrative boundaries, associates districts with coal-transition regions, validates spatial geometries, and loads results into an isolated PostGIS staging table.

Data Sources

	• Administrative boundaries: Bundesamt für Kartographie und Geodäsie (BKG), VG250
	• Legal reference: InvKG § 2 — https://www.gesetze-im-internet.de/invkg/__2.html
	• Coordinate reference system: EPSG:25832

The repository includes processed GeoPackage outputs and the district-to-region membership configuration.

Output

Database destination: iris_staging.coal_phaseout_reviere

The current dataset contains 22 district records:

Region			 Records
Lausitzer Revier	 7
Rheinisches Revier	 7
Mitteldeutsches Revier	 8

The project also produces district-level and dissolved regional GeoPackages.

Setup

	1.	Install Docker Desktop and Python 3.11 or later.
	2.	Copy .env.example to .env and configure a local development password.
	3.	Install Python dependencies:
		python -m pip install -r requirements.txt
	4.	Start the database:
		docker compose up -d
	5.	Initialize the staging table using sql/create_staging_table.sql against the local database.
	6.	Load the supplied processed GeoPackage:

	python src/load_coal_postgis.py

Testing

Run the automated checks:

python -m pytest tests -v

The existing tests check dataset counts, unique district identifiers, CRS, geometry validity, and the PostGIS row count.

Validation Query

SELECT region, COUNT(*) AS district_count

FROM iris_staging.coal_phaseout_reviere

GROUP BY region

ORDER BY region;

Reports
	• reports/coal_region_validation.json
	• reports/postgis_ingestion.json

Assumptions and Limitations

	• This is a preliminary spatial regulatory screening workflow, not a legal eligibility or permit determination.
	• District membership is configured using InvKG § 2.
	• The administrative boundary dataset and its edition must be checked against the source archive for legal and temporal consistency.
	• Region membership alone does not establish project eligibility or an individual facility's phase-out status.
	• The current staging output contains administrative membership polygons; it does not independently establish facility-specific closure dates or phase-out milestones.
	• The raw BKG source archive is excluded from GitHub because of its size. Processed GeoPackages are included for reproducible loading and testing.
	• Full regeneration from raw data requires the corresponding official BKG input dataset.

Data Safety

The implementation writes only to the isolated iris_staging.coal_phaseout_reviere table. It does not require or modify iris_core or production systems.

