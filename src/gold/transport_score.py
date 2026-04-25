import numpy as np
import pandas as pd
from src.db import engine

from src.config import (
    IRIS_RAW,
    TRANSPORT_ARRETS_SILVER,
    TRANSPORT_VELIB_SILVER,
    IRIS_SILVER,
    TRANSPORT_SCORE_GOLD,
    TRANSPORT_WEIGHTS,
)

# Rayon d'analyse en mètres
TRANSPORT_RADIUS_METERS = 800


def parse_geo_point(value):
    """
    Convertit 'lat, lng' en tuple (lat, lng).
    Exemple: '48.862297570166575, 2.34534858519305'
    """
    if pd.isna(value):
        return np.nan, np.nan

    try:
        lat_str, lng_str = str(value).split(",")
        return float(lat_str.strip()), float(lng_str.strip())
    except Exception:
        return np.nan, np.nan


def haversine_distance_m(lat1, lon1, lat2_array, lon2_array):
    """
    Distance haversine entre un point (lat1, lon1) et des tableaux de points.
    Retourne les distances en mètres.
    """
    r = 6371000  # rayon terrestre en mètres

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


def load_transport_points():
    """
    Charge et fusionne les points de transport silver :
    - arrets
    - velib

    Garde uniquement les colonnes utiles au scoring.
    """
    arrets = pd.read_csv(TRANSPORT_ARRETS_SILVER, encoding="utf-8")
    velib = pd.read_csv(TRANSPORT_VELIB_SILVER, encoding="utf-8")

    arrets = arrets[["id", "name", "type", "lat", "lng"]].copy()
    velib = velib[["id", "name", "type", "lat", "lng"]].copy()

    # Harmonisation minimale
    arrets["type"] = arrets["type"].astype(str).str.strip().str.lower()
    velib["type"] = velib["type"].astype(str).str.strip().str.lower()

    transport_points = pd.concat([arrets, velib], ignore_index=True)

    # On garde seulement les types présents dans la config
    valid_types = set(TRANSPORT_WEIGHTS.keys())
    transport_points = transport_points[transport_points["type"].isin(valid_types)].copy()

    # Poids
    transport_points["weight"] = transport_points["type"].map(TRANSPORT_WEIGHTS)

    # Sécurité sur coordonnées
    transport_points["lat"] = pd.to_numeric(transport_points["lat"], errors="coerce")
    transport_points["lng"] = pd.to_numeric(transport_points["lng"], errors="coerce")
    transport_points = transport_points.dropna(subset=["lat", "lng", "weight"]).copy()

    return transport_points


def load_iris_centroids():
    """
    Charge le fichier IRIS silver et, s'il n'existe pas encore,
    le crée à partir du bronze Excel.
    """
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
    """
    Normalisation min-max entre 0 et 1.
    Si toutes les valeurs sont identiques, renvoie 0.
    """
    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return pd.Series(0.0, index=series.index)

    return (series - min_val) / (max_val - min_val)


def compute_transport_score(radius_m=TRANSPORT_RADIUS_METERS):
    """
    Calcule le score transport par IRIS selon la formule :
    - x_sum_weights = somme des poids des points dans le rayon
    - density_raw = log(1 + x_sum_weights)
    - density_score = normalisation min-max de density_raw
    - weighted_mean_distance = moyenne pondérée des distances
    - proximity_score = 1 - weighted_mean_distance / radius
    - transport_score = 0.6 * density_score + 0.4 * proximity_score
    """
    iris = load_iris_centroids()
    transport_points = load_transport_points()

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

    # Densité normalisée
    score_df["density_score"] = min_max_normalize(score_df["density_raw"])

    # Proximité normalisée dans [0, 1]
    score_df["proximity_score"] = np.where(
    score_df["x_sum_weights"] > 0,
    1 - (score_df["weighted_mean_distance"] / radius_m),
    0
)

    score_df["proximity_score"] = score_df["proximity_score"].clip(0, 1)
    # Score final
    score_df["transport_score"] = (
        0.6 * score_df["density_score"]
        + 0.4 * score_df["proximity_score"]
    )

    # Ordre final des colonnes
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

    # Export
    score_df.to_csv(TRANSPORT_SCORE_GOLD, index=False, encoding="utf-8-sig")
    score_df.to_sql("transport_score_iris", engine, if_exists="replace", index=False)
    print(f"[transport_score] {len(score_df)} rows saved → {TRANSPORT_SCORE_GOLD}")
    print(score_df.head())

    return score_df


if __name__ == "__main__":
    compute_transport_score()