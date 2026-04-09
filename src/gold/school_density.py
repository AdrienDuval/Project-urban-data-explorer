"""
Silver → Gold: School density per IRIS zone

For each Paris IRIS zone, counts the number of schools reachable within
BUFFER_METERS (default 500 m) and computes a normalised score
(schools per 1 000 residents).

Spatial workflow:
    1. Load Paris IRIS polygons (GeoJSON) and project to Lambert-93 (EPSG:2154)
       so that buffer distances are in metres.
    2. Buffer each IRIS polygon by BUFFER_METERS.
    3. Load school points and project to the same CRS.
    4. Spatial join: for each school, find which IRIS buffer it falls in.
    5. Group by IRIS → school_count.
    6. Merge with population, compute schools_per_1000.
"""
import geopandas as gpd
import pandas as pd

from src.config import (
    BUFFER_METERS,
    IRIS_GEOJSON,
    IRIS_SILVER,
    POPULATION_SILVER,
    SCHOOL_DENSITY_GOLD,
    SCHOOLS_SILVER,
)
from src.db import engine


def compute_school_density() -> pd.DataFrame:
    """
    Compute schools per IRIS zone (with buffer) and save to gold.

    Returns:
        DataFrame with columns:
            IRIS, LIBCOM, LIBIRIS, GRD_QUART, population,
            school_count, schools_per_1000
    """
    # ── Load silver data ─────────────────────────────────────────────────────
    iris = gpd.read_file(IRIS_GEOJSON)
    iris = iris[iris["dep"] == "75"].copy()

    iris_meta = pd.read_csv(IRIS_SILVER, dtype={"CODE_IRIS": str})
    iris_meta = iris_meta[["CODE_IRIS", "NOM_COM", "NOM_IRIS", "IRIS"]].rename(columns={
        "CODE_IRIS": "code_iris",
        "NOM_COM":   "LIBCOM",
        "NOM_IRIS":  "LIBIRIS",
        "IRIS":      "GRD_QUART",
    })

    population = pd.read_csv(POPULATION_SILVER, dtype={"IRIS": str})
    schools    = pd.read_csv(SCHOOLS_SILVER)

    # ── Build school GeoDataFrame and reproject ──────────────────────────────
    schools_geo = gpd.GeoDataFrame(
        schools.reset_index(drop=True),
        geometry=gpd.points_from_xy(schools["lng"], schools["lat"]),
        crs="EPSG:4326",
    )
    schools_proj = schools_geo.to_crs(epsg=2154)

    # ── Buffer IRIS polygons (metres, Lambert-93) ─────────────────────────────
    iris_proj = iris.to_crs(epsg=2154)
    iris_buffer = iris_proj[["code_iris", "geometry"]].copy()
    iris_buffer["geometry"] = iris_buffer.geometry.buffer(BUFFER_METERS)
    iris_buffer = iris_buffer.rename(columns={"code_iris": "IRIS"})
    iris_buffer["IRIS"] = iris_buffer["IRIS"].astype(str)

    # ── Spatial join: school points → IRIS buffers ───────────────────────────
    joined = gpd.sjoin(schools_proj, iris_buffer, how="inner", predicate="within")
    school_counts = joined.groupby("IRIS").size().reset_index(name="school_count")

    # ── Merge counts with population ─────────────────────────────────────────
    population["IRIS"] = population["IRIS"].astype(str)
    result = population.merge(school_counts, on="IRIS", how="left")
    result["school_count"]     = result["school_count"].fillna(0).astype(int)
    result["schools_per_1000"] = (
        result["school_count"] / result["population"] * 1000
    ).round(2)

    # ── Add IRIS metadata (LIBCOM, LIBIRIS, GRD_QUART) for API compatibility ─
    iris_meta["code_iris"] = iris_meta["code_iris"].astype(str).str.zfill(9)
    result["code_iris"] = result["IRIS"].str.zfill(9)
    result = result.merge(iris_meta, on="code_iris", how="left")

    SCHOOL_DENSITY_GOLD.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(SCHOOL_DENSITY_GOLD, index=False)
    result.to_sql("school_density", engine, if_exists="replace", index=False)
    print(f"[school_density] {len(result)} IRIS zones saved → {SCHOOL_DENSITY_GOLD.name} + DB")
    print(f"  Avg schools per 1000 residents: {result['schools_per_1000'].mean():.2f}")
    return result
