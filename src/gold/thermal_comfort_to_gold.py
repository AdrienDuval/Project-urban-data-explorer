import os

import geopandas as gpd
from src.config import THERMAL_COMFORT_SILVER, THERMAL_COMFORT_GOLD
from src.db import engine



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
    
    gdf_final = df[cols_to_keep].copy()
    
    # Sauvegarde en Parquet (conserve la géométrie native pour d'autres usages)
    gdf_final.to_parquet(THERMAL_COMFORT_GOLD, engine="pyarrow")
    print("🏆 Gold : urban_comfort_index.parquet prêt pour le Dashboard.")
    
    # 6. Insertion en base de données MySQL
    # Convertir la géométrie en WKT (Well-Known Text) pour MySQL
    df_sql = gdf_final.copy()
    df_sql['geometry'] = df_sql['geometry'].apply(lambda geom: geom.wkt if geom else None)
    
    # Insertion dans la table 'thermal_comfort'
    df_sql.to_sql("thermal_comfort", engine, if_exists="replace", index=False)
    print("💾 Données insérées dans la table MySQL 'thermal_comfort'.")

if __name__ == "__main__":
    process_thermal_comfort_gold()