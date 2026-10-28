
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "processed" / "germany_districts.gpkg"
OUTPUT = ROOT / "data" / "processed" / "districts_normalized.gpkg"

FIELD_MAP = {
    "Regionalschlüssel_ARS": "district_code",
    "GeografischerName_GEN": "district_name",
    "Bezeichnung": "district_type",
    "Länderkürzel_LKZ": "state_code",
    "Objektidentifikator": "source_object_id",
}

def main():
    print("IRIS | District normalization started")

    gdf = gpd.read_file(INPUT)

    missing = set(FIELD_MAP) - set(gdf.columns)
    if missing:
        raise ValueError(f"Missing source fields: {sorted(missing)}")

    gdf = gdf.rename(columns=FIELD_MAP)

    fields = list(FIELD_MAP.values()) + ["geometry"]
    gdf = gdf[fields].copy()

    gdf["district_code"] = (
        gdf["district_code"].astype("string").str.strip()
    )

    if gdf["district_code"].isna().any():
        raise ValueError("Missing district identifiers")

    # Check consistency of repeated district identifiers
    for code, group in gdf.groupby("district_code"):
        if len(group) > 1:
            for field in ["district_name", "district_type", "state_code"]:
                if group[field].nunique(dropna=False) > 1:
                    raise ValueError(
                        f"Conflicting {field} for district {code}"
                    )

    # Merge geographic components by district identifier
    original_count = len(gdf)

    gdf = gdf.dissolve(
        by="district_code",
        as_index=False,
        aggfunc="first"
    )

    print(f"Original features: {original_count}")
    print(f"Unique districts: {len(gdf)}")


    if not gdf.geometry.is_valid.all():
        raise ValueError("Invalid geometries detected")

    if gdf.geometry.is_empty.any():
        raise ValueError("Empty geometries detected")

    if gdf.crs is None:
        raise ValueError("Missing coordinate reference system")

    gdf.to_file(
        OUTPUT,
        layer="districts_normalized",
        driver="GPKG",
    )

    print(f"Records processed: {len(gdf)}")
    print(f"CRS: {gdf.crs}")
    print(f"Output: {OUTPUT}")
    print("IRIS | District normalization completed")

if __name__ == "__main__":
    main()
