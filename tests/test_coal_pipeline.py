import os

from pathlib import Path

import geopandas as gpd
import pytest
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


@pytest.fixture(scope="module")
def districts():
    return gpd.read_file(PROCESSED / "districts_normalized.gpkg")


@pytest.fixture(scope="module")
def coal_districts():
    return gpd.read_file(PROCESSED / "coal_districts.gpkg")


@pytest.fixture(scope="module")
def coal_regions():
    return gpd.read_file(PROCESSED / "coal_regions.gpkg")


def test_normalized_district_count(districts):
    assert len(districts) == 400


def test_unique_district_identifiers(districts):
    assert districts["district_code"].is_unique


def test_coal_district_count(coal_districts):
    assert len(coal_districts) == 22


def test_coal_district_identifiers_unique(coal_districts):
    assert coal_districts["district_code"].is_unique


def test_coal_region_count(coal_regions):
    assert len(coal_regions) == 3


def test_valid_geometries(districts, coal_districts, coal_regions):
    for layer in [districts, coal_districts, coal_regions]:
        assert layer.geometry.notna().all()
        assert (~layer.geometry.is_empty).all()
        assert layer.geometry.is_valid.all()
        assert layer.crs.to_epsg() == 25832




def test_postgis_record_count():
    host = os.getenv("PGHOST", "127.0.0.1")
    port = os.getenv("PGPORT", "5433")
    user = os.getenv("POSTGRES_USER", "iris")
    password = os.environ["POSTGRES_PASSWORD"]
    database = os.getenv("POSTGRES_DB", "iris_coal")

    engine = create_engine(
        "postgresql+psycopg://",
        connect_args={
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "dbname": database,
            "connect_timeout": 5,
        },
    )

    try:
        with engine.connect() as connection:
            count = connection.execute(
                text("SELECT COUNT(*) FROM iris_staging.coal_phaseout_reviere")
            ).scalar_one()

        assert count == 22
    finally:
        engine.dispose()
