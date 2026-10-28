"""Idempotent IRIS coal-district loader into iris_staging.coal_phaseout_reviere.

Run from the project root: python src/load_coal_postgis.py
Requires: geopandas, psycopg, shapely, and a running local PostGIS instance.
Set IRIS_DB_PASSWORD, IRIS_DB_PORT, IRIS_SOURCE_VERSION as needed.
"""
import json
import logging
import os
from pathlib import Path

import geopandas as gpd
from dotenv import load_dotenv

import psycopg
from shapely.geometry import MultiPolygon, Polygon
load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "coal_districts.gpkg"
REPORT = ROOT / "reports" / "postgis_ingestion.json"
SOURCE_URL = "https://gdz.bkg.bund.de/index.php/default/open-data/verwaltungsgebiete-1-250-000-stand-31-12-vg250-31-12.html"
LEGAL_URL = "https://www.gesetze-im-internet.de/invkg/__2.html"
EXPECTED_COUNTS = {"Lausitzer Revier": 7, "Rheinisches Revier": 7, "Mitteldeutsches Revier": 8}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("iris.ingest")


def main():
    if not INPUT.is_file():
        raise FileNotFoundError(f"Missing processed GIS dataset: {INPUT}")
    data = gpd.read_file(INPUT)
    required = {"district_code", "district_name", "region", "legal_reference", "geometry"}
    if not required.issubset(data.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(data.columns))}")
    if data.crs is None or data.crs.to_epsg() != 25832:
        raise ValueError(f"Expected EPSG:25832, got {data.crs}")
    data["district_code"] = data["district_code"].astype(str).str.strip().str.zfill(5)
    if len(data) != 22 or data.district_code.duplicated().any():
        raise ValueError("Expected exactly 22 uniquely identified coal districts")
    if data.region.value_counts().to_dict() != EXPECTED_COUNTS:
        raise ValueError("Unexpected region counts; review legal membership source")
    if data[list(required - {"geometry"})].isna().any().any():
        raise ValueError("Missing required attributes")
    if data.geometry.isna().any() or data.geometry.is_empty.any() or not data.geometry.is_valid.all():
        raise ValueError("Missing, empty or invalid geometry")

    source_version = os.getenv("IRIS_SOURCE_VERSION", "BKG VG250 31.12 edition; verify year in source archive")
    rows = []
    for rec in data.itertuples(index=False):
        geom = rec.geometry
        if isinstance(geom, Polygon):
            geom = MultiPolygon([geom])
        if not isinstance(geom, MultiPolygon):
            raise ValueError(f"Unsupported geometry type for {rec.district_code}: {geom.geom_type}")
        rows.append((rec.district_code, rec.district_name, rec.region, rec.legal_reference,
                     "BKG VG250; InvKG §2", f"{SOURCE_URL} | {LEGAL_URL}", source_version, geom.wkb))

    conninfo = dict(host=os.getenv("IRIS_DB_HOST", "127.0.0.1"),
                    port=int(os.getenv("IRIS_DB_PORT", "5433")),
                    dbname=os.getenv("IRIS_DB_NAME", "iris_coal"),
                    user=os.getenv("IRIS_DB_USER", "iris"),
                    password=os.environ["POSTGRES_PASSWORD"],
                    connect_timeout=10)
    log.info("Loading %d records into iris_staging.coal_phaseout_reviere", len(rows))
    statement = """
        INSERT INTO iris_staging.coal_phaseout_reviere
            (district_code, district_name, region, legal_reference, source_name,
             source_url, source_version, geometry)
        VALUES (%s, %s, %s, %s, %s, %s, %s, ST_GeomFromWKB(%s, 25832))
        ON CONFLICT (district_code) DO UPDATE SET
            district_name = EXCLUDED.district_name,
            region = EXCLUDED.region,
            legal_reference = EXCLUDED.legal_reference,
            source_name = EXCLUDED.source_name,
            source_url = EXCLUDED.source_url,
            source_version = EXCLUDED.source_version,
            geometry = EXCLUDED.geometry,
            updated_at = NOW()
        WHERE (iris_staging.coal_phaseout_reviere.district_name,
               iris_staging.coal_phaseout_reviere.region,
               iris_staging.coal_phaseout_reviere.legal_reference,
               iris_staging.coal_phaseout_reviere.source_name,
               iris_staging.coal_phaseout_reviere.source_url,
               iris_staging.coal_phaseout_reviere.source_version,
               iris_staging.coal_phaseout_reviere.geometry)
          IS DISTINCT FROM
              (EXCLUDED.district_name, EXCLUDED.region, EXCLUDED.legal_reference,
               EXCLUDED.source_name, EXCLUDED.source_url, EXCLUDED.source_version,
               EXCLUDED.geometry)
    """
    with psycopg.connect(**conninfo) as conn:
        with conn.cursor() as cur:
            cur.executemany(statement, rows)
            cur.execute("""SELECT region, COUNT(*), COUNT(*) FILTER (WHERE NOT ST_IsValid(geometry))
                           FROM iris_staging.coal_phaseout_reviere GROUP BY region ORDER BY region""")
            results = cur.fetchall()
            actual = {name: count for name, count, _ in results}
            if actual != EXPECTED_COUNTS or any(invalid for _, _, invalid in results):
                raise ValueError(f"PostGIS validation failed: {results}")
            cur.execute("SELECT COUNT(*) FROM iris_staging.coal_phaseout_reviere")
            total = cur.fetchone()[0]
            if total != 22:
                raise ValueError(f"Unexpected total database rows: {total}")
        # Commits automatically on successful exit; rolls back on any exception.
    report = {"input": str(INPUT), "target": "iris_staging.coal_phaseout_reviere",
              "row_count": total, "region_counts": actual, "crs": "EPSG:25832",
              "legal_source": LEGAL_URL, "source_version": source_version,
              "note": "District membership and legal version require independent source review."}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("SUCCESS: %d rows; counts %s; report %s", total, actual, REPORT)


if __name__ == "__main__":
    main()
