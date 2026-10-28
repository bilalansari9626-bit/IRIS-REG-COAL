import geopandas as gpd
import pytest
from shapely.geometry import Point


def validate_input(data):
    required = {"district_code", "region", "geometry"}

    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    if data["district_code"].isna().any():
        raise ValueError("Missing district code")

    if data["district_code"].duplicated().any():
        raise ValueError("Duplicate district code")

    if data.geometry.isna().any() or data.geometry.is_empty.any():
        raise ValueError("Missing or empty geometry")

    if not data.geometry.is_valid.all():
        raise ValueError("Invalid geometry")

    if not data.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all():
        raise ValueError("Unsupported geometry type")


def sample_data():
    return gpd.GeoDataFrame(
        {
            "district_code": ["12052"],
            "region": ["Lausitzer Revier"],
        },
        geometry=[Point(1, 1)],
        crs="EPSG:25832",
    )


def test_missing_column():
    data = sample_data().drop(columns=["region"])
    with pytest.raises(ValueError, match="Missing columns"):
        validate_input(data)


def test_missing_identifier():
    data = sample_data()
    data.loc[0, "district_code"] = None
    with pytest.raises(ValueError, match="Missing district code"):
        validate_input(data)


def test_duplicate_identifier():
    data = sample_data()
    data = gpd.GeoDataFrame(
        [data.iloc[0].to_dict(), data.iloc[0].to_dict()],
        geometry="geometry",
        crs=data.crs,
    )
    with pytest.raises(ValueError, match="Duplicate district code"):
        validate_input(data)


def test_malformed_geometry():
    data = sample_data()
    with pytest.raises(ValueError, match="Unsupported geometry type"):
        validate_input(data)