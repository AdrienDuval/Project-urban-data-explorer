"""
Silver → Gold: transport scoring for IRIS zones (two outputs)

1) ``compute_transport_score`` — geopandas buffer join, 0–10 score, ``IRIS`` column.
   Feeds the vivabilité familiale composite. Writes ``TRANSPORT_SCORE_GOLD``.

2) ``compute_transport_indicator_score`` — haversine radius from centroids, density +
   proximity components 0–1. Feeds the REST API ``/indicators/transport``.
   Writes ``TRANSPORT_INDICATOR_GOLD``.
"""
import numpy as np
import geopandas as gpd
import pandas as pd

from src.config import (
    BUFFER_METERS,
    IRIS_GEOJSON,
    IRIS_RAW,
    IRIS_SILVER,
    POPULATION_SILVER,
    TRANSPORT_ARRETS_SILVER,
    TRANSPORT_INDICATOR_GOLD,
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
    Weighted transport accessibility per IRIS (buffer join), normalised 0–10.

    Returns:
        DataFrame with columns including IRIS, transport_score, weighted_stops.
    """
    print("[transport_score] Loading Silver transport data...")
    arrets = pd.read_csv(TRANSPORT_ARRETS_SILVER)
    velib = pd.read_csv(TRANSPORT_VELIB_SILVER)

    arrets["type"] = arrets["type"].astype(str).str.strip().str.lower()
    velib["type"] = "velib"

    stops = pd.concat(
        [arrets[["lat", "lng", "type"]], velib[["lat", "lng", "type"]]],
        ignore_index=True,
    )
    stops = stops.dropna(subset=["lat", "lng"])
    print(f"[transport_score]   {len(stops):,} stops total")
    print(f"[transport_score]   Types: {stops['type'].value_counts().to_dict()}")

    stops["weight"] = stops["type"].map(TRANSPORT_WEIGHTS).fillna(0.3)

    stops_geo = gpd.GeoDataFrame(
        stops,
        geometry=gpd.points_from_xy(stops["lng"], stops["lat"]),
        crs="EPSG:4326",
    ).to_crs(epsg=2154)

    iris = gpd.read_file(IRIS_GEOJSON)
    iris = iris[iris["dep"] == "75"].copy()
    iris_proj = iris[["code_iris", "geometry"]].to_crs(epsg=2154).copy()
    iris_buffer = iris_proj.copy()
    iris_buffer["geometry"] = iris_buffer.geometry.buffer(BUFFER_METERS)
    iris_buffer["IRIS"] = iris_buffer["code_iris"].astype(str)

    joined = gpd.sjoin(stops_geo, iris_buffer[["IRIS", "geometry"]], how="inner", predicate="within")

    agg = joined.groupby("IRIS").agg(
        stop_count=("weight", "count"),
        weighted_stops=("weight", "sum"),
    ).reset_index()

    population = pd.read_csv(POPULATION_SILVER, dtype={"IRIS": str})
    population["IRIS"] = population["IRIS"].str.zfill(9)

    iris_meta = pd.read_csv(IRIS_SILVER, dtype={"CODE_IRIS": str})
    iris_meta = iris_meta[["CODE_IRIS", "NOM_COM", "NOM_IRIS", "IRIS"]].rename(columns={
        "CODE_IRIS": "code_iris",
        "NOM_COM": "LIBCOM",
        "NOM_IRIS": "LIBIRIS",
        "IRIS": "GRD_QUART",
    })
    iris_meta["code_iris"] = iris_meta["code_iris"].str.zfill(9)

    agg["IRIS"] = agg["IRIS"].astype(str).str.zfill(9)
    result = population.merge(agg, on="IRIS", how="left")
    result["stop_count"] = result["stop_count"].fillna(0).astype(int)
    result["weighted_stops"] = result["weighted_stops"].fillna(0.0)

    result["code_iris"] = result["IRIS"]
    result = result.merge(iris_meta, on="code_iris", how="left")

    result["transport_score"] = _normalize_0_10(result["weighted_stops"])

    TRANSPORT_SCORE_GOLD.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(TRANSPORT_SCORE_GOLD, index=False)
    result.to_sql("transport_score", engine, if_exists="replace", index=False)
    print(f"[transport_score] {len(result)} IRIS zones saved → {TRANSPORT_SCORE_GOLD.name} + DB")
    print(f"  Avg weighted stops per zone: {result['weighted_stops'].mean():.1f}")
    print(f"  Avg transport score: {result['transport_score'].mean():.2f}/10")
    return result


# ── API transport indicator (haversine / centroid-based) ─────────────────────

TRANSPORT_RADIUS_METERS = 800


def parse_geo_point(value):
    """Convertit 'lat, lng' en tuple (lat, lng)."""
    if pd.isna(value):
        return np.nan, np.nan

    try:
        lat_str, lng_str = str(value).split(",")
        return float(lat_str.strip()), float(lng_str.strip())
    except Exception:
        return np.nan, np.nan


def haversine_distance_m(lat1, lon1, lat2_array, lon2_array):
    """Distance haversine en mètres entre un point et des tableaux de points."""
    r = 6371000

    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2_array)
    lon2_rad = np.radians(lon2_array)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return r * c


def load_transport_points_for_indicator():
    """Charge arrêts + vélib silver pour le score indicateur API."""
    arrets = pd.read_csv(TRANSPORT_ARRETS_SILVER, encoding="utf-8")
    velib = pd.read_csv(TRANSPORT_VELIB_SILVER, encoding="utf-8")

    arrets = arrets[["id", "name", "type", "lat", "lng"]].copy()
    velib = velib[["id", "name", "type", "lat", "lng"]].copy()

    arrets["type"] = arrets["type"].astype(str).str.strip().str.lower()
    velib["type"] = velib["type"].astype(str).str.strip().str.lower()

    transport_points = pd.concat([arrets, velib], ignore_index=True)

    valid_types = set(TRANSPORT_WEIGHTS.keys())
    transport_points = transport_points[transport_points["type"].isin(valid_types)].copy()

    transport_points["weight"] = transport_points["type"].map(TRANSPORT_WEIGHTS)

    transport_points["lat"] = pd.to_numeric(transport_points["lat"], errors="coerce")
    transport_points["lng"] = pd.to_numeric(transport_points["lng"], errors="coerce")
    transport_points = transport_points.dropna(subset=["lat", "lng", "weight"]).copy()

    return transport_points


def load_iris_centroids():
    """IRIS silver + Geo Point → centroides pour le score haversine."""
    if not IRIS_SILVER.exists():
        df = pd.read_excel(IRIS_RAW)
        df.to_csv(IRIS_SILVER, index=False, encoding="utf-8-sig")
        print("iris_paris.csv créé")

    iris = pd.read_csv(IRIS_SILVER, encoding="utf-8-sig")
    iris = iris[["CODE_IRIS", "Geo Point"]].copy()

    iris[["iris_lat", "iris_lng"]] = iris["Geo Point"].apply(
        lambda x: pd.Series(parse_geo_point(x))
    )

    iris["CODE_IRIS"] = iris["CODE_IRIS"].astype(str)
    iris = iris.dropna(subset=["iris_lat", "iris_lng"]).copy()
    iris = iris[iris["CODE_IRIS"].astype(str).str.startswith("75")].copy()
    return iris


def min_max_normalize(series):
    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return pd.Series(0.0, index=series.index)

    return (series - min_val) / (max_val - min_val)


def compute_transport_indicator_score(radius_m: float = TRANSPORT_RADIUS_METERS) -> pd.DataFrame:
    """
    Score transport pour l'API (densité + proximité, 0–1), par CODE_IRIS.
    """
    iris = load_iris_centroids()
    transport_points = load_transport_points_for_indicator()

    tp_lat = transport_points["lat"].to_numpy()
    tp_lng = transport_points["lng"].to_numpy()
    tp_weight = transport_points["weight"].to_numpy()

    results = []

    for _, iris_row in iris.iterrows():
        code_iris = iris_row["CODE_IRIS"]
        iris_lat = iris_row["iris_lat"]
        iris_lng = iris_row["iris_lng"]

        distances = haversine_distance_m(iris_lat, iris_lng, tp_lat, tp_lng)

        mask = distances <= radius_m

        if not mask.any():
            results.append(
                {
                    "CODE_IRIS": code_iris,
                    "x_sum_weights": 0.0,
                    "density_raw": 0.0,
                    "weighted_mean_distance": 0.0,
                    "proximity_score": 0.0,
                }
            )
            continue

        selected_weights = tp_weight[mask]
        selected_distances = distances[mask]

        x_sum_weights = float(selected_weights.sum())
        density_raw = float(np.log1p(x_sum_weights))

        if x_sum_weights > 0:
            weighted_mean_distance = float(
                np.sum(selected_weights * selected_distances) / np.sum(selected_weights)
            )
        else:
            weighted_mean_distance = 0.0

        results.append(
            {
                "CODE_IRIS": code_iris,
                "x_sum_weights": x_sum_weights,
                "density_raw": density_raw,
                "weighted_mean_distance": weighted_mean_distance,
            }
        )

    score_df = pd.DataFrame(results)

    score_df["density_score"] = min_max_normalize(score_df["density_raw"])

    score_df["proximity_score"] = np.where(
        score_df["x_sum_weights"] > 0,
        1 - (score_df["weighted_mean_distance"] / radius_m),
        0,
    )

    score_df["proximity_score"] = score_df["proximity_score"].clip(0, 1)
    score_df["transport_score"] = (
        0.6 * score_df["density_score"]
        + 0.4 * score_df["proximity_score"]
    )

    score_df = score_df[
        [
            "CODE_IRIS",
            "x_sum_weights",
            "density_raw",
            "density_score",
            "weighted_mean_distance",
            "proximity_score",
            "transport_score",
        ]
    ].copy()

    TRANSPORT_INDICATOR_GOLD.parent.mkdir(parents=True, exist_ok=True)
    score_df.to_csv(TRANSPORT_INDICATOR_GOLD, index=False, encoding="utf-8-sig")
    score_df.to_sql("transport_score_iris", engine, if_exists="replace", index=False)
    print(
        f"[transport_indicator] {len(score_df)} rows saved → {TRANSPORT_INDICATOR_GOLD.name} + DB"
    )
    print(score_df.head())

    return score_df


if __name__ == "__main__":
    compute_transport_score()
    compute_transport_indicator_score()
