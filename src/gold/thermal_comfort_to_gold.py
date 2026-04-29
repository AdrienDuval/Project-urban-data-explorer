import os
import numpy as np
import geopandas as gpd
from src.config import THERMAL_COMFORT_SILVER, THERMAL_COMFORT_GOLD
from src.db import engine


def process_thermal_comfort_gold():
    print("[thermal_comfort] Loading Silver thermal comfort data...")
    df = gpd.read_file(THERMAL_COMFORT_SILVER)
    print(f"[thermal_comfort]   {len(df):,} zones loaded")

    output_dir = os.path.dirname(THERMAL_COMFORT_GOLD)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # ── 1. Indicateurs bruts ──────────────────────────────────────────────
    df["densite_arbres"] = df["nb_arbres"] / (df["surface_iris"] / 10000)
    df["ratio_fraicheur"] = df["total_area_ilot"] / df["surface_iris"]

    # ── 2. Normalisation robuste (percentile) sur 0-10 ───────────────────
    # Min-Max classique est écrasé par les outliers (max=129 arbres/ha).
    # On cappe à P95 pour que 95% des zones soient bien réparties sur [0,10].
    def robust_score(series, cap_percentile=95):
        cap = np.percentile(series.dropna(), cap_percentile)
        clipped = series.clip(upper=cap)
        min_val = clipped.min()
        return ((clipped - min_val) / (cap - min_val) * 10).round(4)

    df["tree_density_score"] = robust_score(df["densite_arbres"], cap_percentile=95)

    # ratio_fraicheur : 53% de zéros → on normalise sur les zones non nulles
    # puis on applique une racine carrée pour étaler la distribution
    df["ratio_fraicheur_sqrt"] = np.sqrt(df["ratio_fraicheur"])
    df["cooling_area_score"] = robust_score(df["ratio_fraicheur_sqrt"], cap_percentile=95)

    # ── 3. Score de proximité aux îlots de fraîcheur ─────────────────────
    # Pour les 527 zones sans îlot, on leur attribue un bonus
    # basé sur la moyenne pondérée (1/distance²) des zones voisines.
    # On travaille en Lambert 93 (mètres) pour les distances.
    print("[thermal_comfort] Computing proximity score...")
    centroids = df.geometry.centroid
    coords = np.array([(c.x, c.y) for c in centroids])
    fraicheur_vals = df["ratio_fraicheur_sqrt"].values

    proximity_scores = np.zeros(len(df))
    RADIUS = 800  # mètres — rayon de voisinage

    for i in range(len(df)):
        dx = coords[:, 0] - coords[i, 0]
        dy = coords[:, 1] - coords[i, 1]
        distances = np.sqrt(dx**2 + dy**2)

        # Voisins dans le rayon (exclu soi-même)
        mask = (distances > 0) & (distances <= RADIUS)
        if mask.sum() == 0:
            proximity_scores[i] = fraicheur_vals[i]
            continue

        weights = 1 / (distances[mask] ** 2)
        proximity_scores[i] = np.average(fraicheur_vals[mask], weights=weights)

    df["proximity_score_raw"] = proximity_scores
    df["proximity_score"] = robust_score(
        gpd.pd.Series(proximity_scores), cap_percentile=95
    )

    # ── 4. Score final ────────────────────────────────────────────────────
    # 35% arbres directs + 30% îlots directs + 35% proximité voisinage
    df["thermal_score"] = (
        df["tree_density_score"] * 0.35
        + df["cooling_area_score"] * 0.30
        + df["proximity_score"] * 0.35
    ).round(4)

    df["indice_confort_thermique"] = df["thermal_score"]

    # ── 5. Arrondissement ─────────────────────────────────────────────────
    def code_to_arrondissement(code_iris):
        try:
            num = int(str(code_iris)[3:5])
            suffix = "er" if num == 1 else "e"
            return f"Paris {num}{suffix}"
        except Exception:
            return "Paris"

    df["arrondissement"] = df["code_iris"].apply(code_to_arrondissement)

    # ── 6. Export ─────────────────────────────────────────────────────────
    cols_to_keep = [
        "code_iris", "nom_iris", "arrondissement",
        "densite_arbres", "ratio_fraicheur",
        "tree_density_score", "cooling_area_score",
        "proximity_score", "thermal_score",
        "indice_confort_thermique",
        "geometry"
    ]

    gdf_final = df[cols_to_keep].copy()

    # Reprojection WGS84 pour Mapbox
    if gdf_final.crs and gdf_final.crs.to_epsg() != 4326:
        gdf_final = gdf_final.to_crs(epsg=4326)
        print("[thermal_comfort] Reprojected to WGS84.")

    gdf_final.to_parquet(THERMAL_COMFORT_GOLD, engine="pyarrow")
    print("🏆 Gold : urban_comfort_index.parquet prêt.")

    # Export MySQL
    df_sql = gdf_final.copy()
    df_sql["geometry"] = df_sql["geometry"].apply(lambda g: g.wkt if g else None)
    df_sql.to_sql("thermal_comfort", engine, if_exists="replace", index=False)
    print("💾 Données insérées dans MySQL 'thermal_comfort'.")


if __name__ == "__main__":
    process_thermal_comfort_gold()