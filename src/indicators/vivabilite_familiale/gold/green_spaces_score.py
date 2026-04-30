"""
Silver → Gold: Green spaces score per IRIS zone

Quantifies access to usable green space for each Paris IRIS zone using a
two-radius formula:

    green_m2 = interior_area + GREEN_SPACES_BUFFER_METERS_BONUS × adjacent_area

Where:
    interior_area  — m² of green space whose centroid is inside the IRIS zone.
    adjacent_area  — m² of green space whose centroid is within 300 m of the
                     IRIS boundary but outside it (50 % bonus for proximity).

The raw value is then divided by the zone's residential population to produce
green space per resident, and finally normalised to 0–10.

Spatial workflow:
    1. Load Silver green spaces GeoJSON (already filtered to open, usable spaces).
    2. Compute centroids, project to Lambert-93 (EPSG:2154).
    3. Load Paris IRIS polygons, project to EPSG:2154.
    4. Spatial join (centroid inside IRIS) → interior assignment.
    5. Buffer each IRIS by GREEN_SPACES_BUFFER_METERS (300 m), subtract
       interior → find adjacent green spaces.
    6. Aggregate area by IRIS with weights (1.0 interior, 0.5 adjacent).
    7. Divide by population, normalise to 0–10.
    8. Write CSV + DB table  green_spaces_score.
"""
import geopandas as gpd
import pandas as pd

from src.config import (
    ESPACES_VERTS_SILVER,
    GREEN_SPACES_BUFFER_METERS,
    GREEN_SPACES_SCORE_GOLD,
    IRIS_GEOJSON,
    IRIS_SILVER,
    POPULATION_SILVER,
)
from src.db import engine

ADJACENT_BONUS = 0.5  # 50 % weight for nearby (non-interior) green spaces


def _normalize_0_10(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(5.0, index=series.index)
    return ((series - mn) / (mx - mn) * 10).round(2)


def compute_green_spaces_score() -> pd.DataFrame:
    """
    Compute green-space accessibility score per IRIS zone.

    Returns:
        DataFrame with columns:
            IRIS, LIBCOM, LIBIRIS, GRD_QUART, population,
            interior_m2, adjacent_m2, total_green_m2,
            green_m2_per_resident, green_spaces_score
    """
    # ── Load Silver green spaces ──────────────────────────────────────────────
    print("[green_spaces_score] Loading Silver green spaces...")
    gdf_green = gpd.read_file(ESPACES_VERTS_SILVER)
    print(f"[green_spaces_score]   {len(gdf_green):,} spaces loaded")

    if "surface_totale_reelle" not in gdf_green.columns:
        # Robust fallback for schema drifts from source data.
        if len(gdf_green) == 0:
            gdf_green["surface_totale_reelle"] = pd.Series(dtype="float64")
        else:
            projected_area = gdf_green.to_crs(epsg=2154).geometry.area
            gdf_green["surface_totale_reelle"] = projected_area.values

    # Work in Lambert-93 so distances and areas are in metres / m²
    gdf_green = gdf_green.to_crs(epsg=2154)

    # Use centroid for the spatial join (avoids large parks spanning multiple zones)
    green_centroids = gdf_green.copy()
    green_centroids["geometry"] = gdf_green.geometry.centroid
    green_centroids = green_centroids[["surface_totale_reelle", "geometry"]].copy()

    # ── Load Paris IRIS ───────────────────────────────────────────────────────
    iris = gpd.read_file(IRIS_GEOJSON)
    iris = iris[iris["dep"] == "75"].copy()
    iris_proj = iris[["code_iris", "geometry"]].to_crs(epsg=2154).copy()
    iris_proj["IRIS"] = iris_proj["code_iris"].astype(str)

    # ── Step 1: interior — centroid inside the IRIS ───────────────────────────
    interior_join = gpd.sjoin(
        green_centroids, iris_proj[["IRIS", "geometry"]], how="inner", predicate="within"
    )
    interior_agg = (
        interior_join.groupby("IRIS")["surface_totale_reelle"]
        .sum()
        .reset_index()
        .rename(columns={"surface_totale_reelle": "interior_m2"})
    )

    # ── Step 2: adjacent — centroid within 300 m buffer but NOT interior ──────
    iris_buffer = iris_proj.copy()
    iris_buffer["geometry"] = iris_buffer.geometry.buffer(GREEN_SPACES_BUFFER_METERS)

    buffer_join = gpd.sjoin(
        green_centroids, iris_buffer[["IRIS", "geometry"]], how="inner", predicate="within"
    )

    # Keep only spaces not already in the interior for this IRIS zone
    interior_ids = set(zip(interior_join.index, interior_join["IRIS"]))
    buffer_join["_key"] = list(zip(buffer_join.index, buffer_join["IRIS"]))
    adjacent_join = buffer_join[~buffer_join["_key"].isin(interior_ids)].copy()

    adjacent_agg = (
        adjacent_join.groupby("IRIS")["surface_totale_reelle"]
        .sum()
        .reset_index()
        .rename(columns={"surface_totale_reelle": "adjacent_m2"})
    )

    # ── Step 3: combine ───────────────────────────────────────────────────────
    all_iris = iris_proj[["IRIS"]].copy()
    result = all_iris.merge(interior_agg, on="IRIS", how="left")
    result = result.merge(adjacent_agg,  on="IRIS", how="left")
    result["interior_m2"] = result["interior_m2"].fillna(0.0)
    result["adjacent_m2"] = result["adjacent_m2"].fillna(0.0)
    result["total_green_m2"] = result["interior_m2"] + ADJACENT_BONUS * result["adjacent_m2"]

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
    result["IRIS"] = result["IRIS"].astype(str).str.zfill(9)
    result = population.merge(result, on="IRIS", how="left")
    result["total_green_m2"] = result["total_green_m2"].fillna(0.0)
    result["interior_m2"]    = result["interior_m2"].fillna(0.0)
    result["adjacent_m2"]    = result["adjacent_m2"].fillna(0.0)

    # m² of green space per resident (avoid division by zero)
    result["green_m2_per_resident"] = result.apply(
        lambda r: round(r["total_green_m2"] / r["population"], 2)
        if r["population"] > 0 else 0.0,
        axis=1,
    )

    result["code_iris"] = result["IRIS"]
    result = result.merge(iris_meta, on="code_iris", how="left")

    # ── Normalise ─────────────────────────────────────────────────────────────
    result["green_spaces_score"] = _normalize_0_10(result["green_m2_per_resident"])

    # ── Save ──────────────────────────────────────────────────────────────────
    GREEN_SPACES_SCORE_GOLD.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(GREEN_SPACES_SCORE_GOLD, index=False)
    result.to_sql("green_spaces_score", engine, if_exists="replace", index=False)
    print(f"[green_spaces_score] {len(result)} IRIS zones saved → {GREEN_SPACES_SCORE_GOLD.name} + DB")
    print(f"  Avg green m²/resident: {result['green_m2_per_resident'].mean():.1f}")
    print(f"  Avg green spaces score: {result['green_spaces_score'].mean():.2f}/10")
    return result
