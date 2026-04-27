"""
Silver → Gold: Transport accessibility score per IRIS zone

For each Paris IRIS zone, counts the weighted number of transport stops
reachable within BUFFER_METERS (500 m) and computes a normalised 0–10 score.

Weights per stop type (from config.TRANSPORT_WEIGHTS):
    metro    1.0   — heaviest, direct city connectivity
    rail     1.2   — RER / Transilien, highest capacity
    tram     0.7
    bus      0.4   — most common but least impact per stop
    cableway 0.5
    velib    0.3   — active mobility

Spatial workflow:
    1. Load Silver transport stops (arrets + velib) and project to EPSG:2154.
    2. Load Paris IRIS polygons, buffer by BUFFER_METERS.
    3. Spatial join: for each stop, find which IRIS buffer it falls in.
    4. Group by IRIS, sum weighted counts.
    5. Normalize to 0–10 relative to all Paris IRIS zones.
    6. Write CSV + DB table  transport_score.
"""
import geopandas as gpd
import pandas as pd

from src.config import (
    BUFFER_METERS,
    IRIS_GEOJSON,
    IRIS_SILVER,
    POPULATION_SILVER,
    TRANSPORT_ARRETS_SILVER,
    TRANSPORT_SCORE_GOLD,
    TRANSPORT_VELIB_SILVER,
    TRANSPORT_WEIGHTS,
)
from src.db import engine


def _normalize_0_10(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(5.0, index=series.index)
    return ((series - mn) / (mx - mn) * 10).round(2)


def compute_transport_score() -> pd.DataFrame:
    """
    Compute weighted transport accessibility per IRIS zone.

    Returns:
        DataFrame with columns:
            IRIS, LIBCOM, LIBIRIS, GRD_QUART, population,
            stop_count, weighted_stops, transport_score
    """
    # ── Load Silver transport data ────────────────────────────────────────────
    print("[transport_score] Loading Silver transport data...")
    arrets = pd.read_csv(TRANSPORT_ARRETS_SILVER)
    velib  = pd.read_csv(TRANSPORT_VELIB_SILVER)

    # Normalise type to lowercase so it matches TRANSPORT_WEIGHTS keys
    arrets["type"] = arrets["type"].astype(str).str.strip().str.lower()
    velib["type"]  = "velib"

    stops = pd.concat(
        [arrets[["lat", "lng", "type"]], velib[["lat", "lng", "type"]]],
        ignore_index=True,
    )
    stops = stops.dropna(subset=["lat", "lng"])
    print(f"[transport_score]   {len(stops):,} stops total")
    print(f"[transport_score]   Types: {stops['type'].value_counts().to_dict()}")

    # ── Assign weight per stop ────────────────────────────────────────────────
    stops["weight"] = stops["type"].map(TRANSPORT_WEIGHTS).fillna(0.3)

    # ── Build GeoDataFrame and project ───────────────────────────────────────
    stops_geo = gpd.GeoDataFrame(
        stops,
        geometry=gpd.points_from_xy(stops["lng"], stops["lat"]),
        crs="EPSG:4326",
    ).to_crs(epsg=2154)

    # ── Load and buffer IRIS polygons ─────────────────────────────────────────
    iris = gpd.read_file(IRIS_GEOJSON)
    iris = iris[iris["dep"] == "75"].copy()
    iris_proj = iris[["code_iris", "geometry"]].to_crs(epsg=2154).copy()
    iris_buffer = iris_proj.copy()
    iris_buffer["geometry"] = iris_buffer.geometry.buffer(BUFFER_METERS)
    iris_buffer["IRIS"] = iris_buffer["code_iris"].astype(str)

    # ── Spatial join: stops → IRIS buffers ───────────────────────────────────
    joined = gpd.sjoin(stops_geo, iris_buffer[["IRIS", "geometry"]], how="inner", predicate="within")

    # ── Aggregate: stop count + weighted sum ─────────────────────────────────
    agg = joined.groupby("IRIS").agg(
        stop_count=("weight", "count"),
        weighted_stops=("weight", "sum"),
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

    # ── Merge everything ──────────────────────────────────────────────────────
    agg["IRIS"] = agg["IRIS"].astype(str).str.zfill(9)
    result = population.merge(agg, on="IRIS", how="left")
    result["stop_count"]     = result["stop_count"].fillna(0).astype(int)
    result["weighted_stops"] = result["weighted_stops"].fillna(0.0)

    result["code_iris"] = result["IRIS"]
    result = result.merge(iris_meta, on="code_iris", how="left")

    # ── Normalise ─────────────────────────────────────────────────────────────
    result["transport_score"] = _normalize_0_10(result["weighted_stops"])

    # ── Save ──────────────────────────────────────────────────────────────────
    TRANSPORT_SCORE_GOLD.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(TRANSPORT_SCORE_GOLD, index=False)
    result.to_sql("transport_score", engine, if_exists="replace", index=False)
    print(f"[transport_score] {len(result)} IRIS zones saved → {TRANSPORT_SCORE_GOLD.name} + DB")
    print(f"  Avg weighted stops per zone: {result['weighted_stops'].mean():.1f}")
    print(f"  Avg transport score: {result['transport_score'].mean():.2f}/10")
    return result
