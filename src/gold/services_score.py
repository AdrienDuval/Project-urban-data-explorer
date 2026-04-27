"""
Silver → Gold: Services accessibility score per IRIS zone

Measures proximity to essential family services within a 500 m radius of
each IRIS zone.  Two sources are combined:

    1. Hospitals (hospitals_paris_clean.csv)
       Healthcare establishments — weighted ×3 per establishment since
       hospitals have outsized importance for families.

    2. BDCOM essential services (bdcom_paris_clean.csv)
       Filtered to niv8 categories 2 (Alimentaire) and 4 (Service commercial):
       groceries, pharmacies, banks, post offices, and general services.
       These represent the day-to-day service fabric a family depends on.

Spatial workflow:
    1. Load both Silver files, build GeoDataFrames.
       - Hospitals: lat/lng in WGS84 (EPSG:4326) → project to EPSG:2154.
       - BDCOM: X/Y already in Lambert-93 (EPSG:2154).
    2. Buffer each IRIS polygon by BUFFER_METERS (500 m).
    3. Spatial join → count weighted services per IRIS.
    4. Normalize to 0–10.
    5. Write CSV + DB table  services_score.
"""
import geopandas as gpd
import pandas as pd

from src.config import (
    BDCOM_SILVER,
    BUFFER_METERS,
    HOSPITALS_SILVER,
    IRIS_GEOJSON,
    IRIS_SILVER,
    POPULATION_SILVER,
    SERVICES_SCORE_GOLD,
)
from src.db import engine

# BDCOM niv8 categories kept for the services indicator
BDCOM_SERVICE_CATEGORIES = {2, 4}  # Alimentaire + Service commercial

# How much more a hospital counts vs a general service
HOSPITAL_WEIGHT = 3.0
BDCOM_WEIGHT    = 1.0


def _normalize_0_10(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(5.0, index=series.index)
    return ((series - mn) / (mx - mn) * 10).round(2)


def compute_services_score() -> pd.DataFrame:
    """
    Compute proximity-to-services score per IRIS zone.

    Returns:
        DataFrame with columns:
            IRIS, LIBCOM, LIBIRIS, GRD_QUART, population,
            hospital_count, service_count, weighted_services, services_score
    """
    # ── Load Silver files ─────────────────────────────────────────────────────
    print("[services_score] Loading Silver data...")

    hospitals = pd.read_csv(HOSPITALS_SILVER, encoding="utf-8-sig")
    hospitals = hospitals[hospitals["has_coordinates"] == 1].copy()
    hospitals = hospitals[["lat", "lng"]].dropna()
    hospitals["weight"] = HOSPITAL_WEIGHT
    hospitals["source"] = "hospital"
    print(f"[services_score]   {len(hospitals):,} hospitals with coordinates")

    bdcom = pd.read_csv(BDCOM_SILVER, encoding="utf-8-sig")
    bdcom = bdcom[bdcom["niv8"].isin(BDCOM_SERVICE_CATEGORIES)].copy()
    bdcom = bdcom[["X", "Y"]].dropna()
    bdcom["weight"] = BDCOM_WEIGHT
    bdcom["source"] = "service"
    print(f"[services_score]   {len(bdcom):,} BDCOM services (niv8 ∈ {BDCOM_SERVICE_CATEGORIES})")

    # ── Build GeoDataFrames ───────────────────────────────────────────────────
    hospitals_geo = gpd.GeoDataFrame(
        hospitals,
        geometry=gpd.points_from_xy(hospitals["lng"], hospitals["lat"]),
        crs="EPSG:4326",
    ).to_crs(epsg=2154)
    hospitals_geo = hospitals_geo[["weight", "source", "geometry"]].copy()

    bdcom_geo = gpd.GeoDataFrame(
        bdcom,
        geometry=gpd.points_from_xy(bdcom["X"], bdcom["Y"]),
        crs="EPSG:2154",
    )
    bdcom_geo = bdcom_geo[["weight", "source", "geometry"]].copy()

    all_services = pd.concat([hospitals_geo, bdcom_geo], ignore_index=True)
    all_services = gpd.GeoDataFrame(all_services, geometry="geometry", crs="EPSG:2154")

    # ── Load and buffer IRIS polygons ─────────────────────────────────────────
    iris = gpd.read_file(IRIS_GEOJSON)
    iris = iris[iris["dep"] == "75"].copy()
    iris_proj = iris[["code_iris", "geometry"]].to_crs(epsg=2154).copy()
    iris_buffer = iris_proj.copy()
    iris_buffer["geometry"] = iris_buffer.geometry.buffer(BUFFER_METERS)
    iris_buffer["IRIS"] = iris_buffer["code_iris"].astype(str)

    # ── Spatial join ──────────────────────────────────────────────────────────
    joined = gpd.sjoin(
        all_services, iris_buffer[["IRIS", "geometry"]], how="inner", predicate="within"
    )

    # ── Aggregate ─────────────────────────────────────────────────────────────
    agg = joined.groupby("IRIS").agg(
        hospital_count=("source", lambda s: (s == "hospital").sum()),
        service_count=("source",  lambda s: (s == "service").sum()),
        weighted_services=("weight", "sum"),
    ).reset_index()

    # ── Load population and IRIS metadata ────────────────────────────────────
    population = pd.read_csv(POPULATION_SILVER, dtype={"IRIS": str})
    population["IRIS"] = population["IRIS"].str.zfill(9)

    iris_meta = pd.read_csv(IRIS_SILVER, dtype={"CODE_IRIS": str})
    iris_meta = iris_meta[["CODE_IRIS", "NOM_COM", "NOM_IRIS", "IRIS"]].rename(columns={
        "CODE_IRIS": "code_iris",
        "NOM_COM":   "LIBCOM",
        "NOM_IRIS":  "LIBIRIS",
        "IRIS":      "GRD_QUART",
    })
    iris_meta["code_iris"] = iris_meta["code_iris"].str.zfill(9)

    # ── Merge ─────────────────────────────────────────────────────────────────
    agg["IRIS"] = agg["IRIS"].astype(str).str.zfill(9)
    result = population.merge(agg, on="IRIS", how="left")
    result["hospital_count"]      = result["hospital_count"].fillna(0).astype(int)
    result["service_count"]       = result["service_count"].fillna(0).astype(int)
    result["weighted_services"]   = result["weighted_services"].fillna(0.0)

    result["code_iris"] = result["IRIS"]
    result = result.merge(iris_meta, on="code_iris", how="left")

    # ── Normalise ─────────────────────────────────────────────────────────────
    result["services_score"] = _normalize_0_10(result["weighted_services"])

    # ── Save ──────────────────────────────────────────────────────────────────
    SERVICES_SCORE_GOLD.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(SERVICES_SCORE_GOLD, index=False)
    result.to_sql("services_score", engine, if_exists="replace", index=False)
    print(f"[services_score] {len(result)} IRIS zones saved → {SERVICES_SCORE_GOLD.name} + DB")
    print(f"  Avg hospitals per zone: {result['hospital_count'].mean():.2f}")
    print(f"  Avg services per zone:  {result['service_count'].mean():.1f}")
    print(f"  Avg services score:     {result['services_score'].mean():.2f}/10")
    return result
