
"""Validate spatial relationships between coal districts and regions."""

import json
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
DISTRICTS = ROOT / "data/processed/coal_districts.gpkg"
REGIONS = ROOT / "data/processed/coal_regions.gpkg"
REPORT = ROOT / "reports/spatial_validation.json"

districts = gpd.read_file(DISTRICTS)
regions = gpd.read_file(REGIONS)

if districts.crs != regions.crs:
    raise ValueError("District and region CRS do not match")

if len(districts) != 22 or len(regions) != 3:
    raise ValueError("Unexpected number of districts or regions")

if not districts.geometry.is_valid.all():
    raise ValueError("Invalid district geometries")

if not regions.geometry.is_valid.all():
    raise ValueError("Invalid region geometries")

# A district must have its representative point inside its assigned region.
points = districts[["district_code", "region", "geometry"]].copy()
points["geometry"] = points.geometry.representative_point()

joined = gpd.sjoin(
    points,
    regions.rename(columns={"region": "joined_region"}),
    how="left",
    predicate="within",
)

matches = (
    joined["region"] == joined["joined_region"]
).fillna(False)

if len(joined) != 22 or not matches.all():
    raise ValueError("Spatial join failed: district-region mismatch")

report = {
    "district_count": len(districts),
    "region_count": len(regions),
    "spatial_matches": int(matches.sum()),
    "spatial_mismatches": int((~matches).sum()),
    "crs": str(districts.crs),
    "method": "Representative-point within region polygon",
    "result": "PASS",
}

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8",
)

print("PASS: 22 districts matched their assigned regions")
print(f"Report: {REPORT}")
