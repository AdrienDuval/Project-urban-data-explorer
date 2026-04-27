import os

import geopandas as gpd
from src.config import THERMAL_COMFORT_SILVER, THERMAL_COMFORT_GOLD



def process_thermal_comfort_gold():
    # 1. Chargement du Silver
    df = gpd.read_file(THERMAL_COMFORT_SILVER)

    output_dir = os.path.dirname(THERMAL_COMFORT_GOLD)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


    # 2. Indicateurs bruts
    # nb arbres / hectares
    df["densite_arbres"] = df["nb_arbres"] / (df["surface_iris"] / 10000)
    # % de surface en îlot de fraîcheur
    df["ratio_fraicheur"] = df["total_area_ilot"] / df["surface_iris"]

    # 3. Normalisation Min-Max (0 à 100)
    for col in ["densite_arbres", "ratio_fraicheur"]:
        min_val = df[col].min()
        max_val = df[col].max()
        df[f"score_{col}"] = (df[col] - min_val) / (max_val - min_val) * 100

    # 4. Indice Final (0.4 Arbres + 0.6 Fraîcheur)
    df["indice_confort_thermique"] = (df["score_densite_arbres"] * 0.4) + (df["score_ratio_fraicheur"] * 0.6)

    # 5. Export des colonnes essentielles pour le Dashboard
    cols_to_keep = [
        "code_iris", "nom_iris", "densite_arbres", 
        "ratio_fraicheur", "indice_confort_thermique", "geometry"
    ]
    df[cols_to_keep].to_file(f"{THERMAL_COMFORT_GOLD}", driver="GeoJSON")
    print("🏆Gold : urban_comfort_index.geojson prêt pour le Dashboard.")

if __name__ == "__main__":
    process_thermal_comfort_gold()