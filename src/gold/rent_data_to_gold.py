from src.config import (
    ARRONDISSEMENTS,
    RENT_PRICE_SILVER,
    RENT_PRICE_GOLD
)
import geopandas as gpd
import pandas as pd
import os

def process_rent_data_to_gold():
    # Charger les données de loyers (Silver)
    loyers_complets = pd.read_csv(RENT_PRICE_SILVER, sep=";")


    # Nettoyage des chaînes et conversion en Float
    # On remplace la virgule par le point et on convertit en numérique
    cols_loyers = ["loyer_median", "loyer_1_quartile", "loyer_3_quartile"]

    for col in cols_loyers:
        # On s'assure que c'est du texte, on enlève les espaces, on remplace la virgule
        loyers_complets[col] = (
            loyers_complets[col]
            .astype(str)
            .str.replace(",", ".")
        )
        # Conversion en float (les erreurs deviennent des NaN)
        loyers_complets[col] = pd.to_numeric(loyers_complets[col], errors='coerce')

    # Agrégation par Arrondissement (c_ar)
    # .groupby() regroupe, .agg() calcule les moyennes
    loyers_par_arrdt = (
        loyers_complets.groupby("c_ar")
        .agg({
            "loyer_median": "mean",
            "loyer_1_quartile": "mean",
            "loyer_3_quartile": "mean"
        })
        .round(2) # On arrondit à 2 décimales
        .reset_index() # Pour que 'c_ar' redevienne une colonne normale
    )

    # Renommage des colonnes pour plus de clarté
    loyers_par_arrdt = loyers_par_arrdt.rename(columns={
        "loyer_median": "loyer_median_m2",
        "loyer_1_quartile": "loyer_q1_m2",
        "loyer_3_quartile": "loyer_q3_m2"
    })

    # Tri par arrondissement
    loyers_par_arrdt = loyers_par_arrdt.sort_values("c_ar")


    # Chargement des arrondissements en GeoDataFrame pour faire la jointure spatiale
    gdf_arrdt = gpd.read_file(ARRONDISSEMENTS)
    
    # S'assurer que le type de c_ar est identique pour la fusion (en string)
    gdf_arrdt["c_ar"] = gdf_arrdt["c_ar"].astype(str)
    loyers_par_arrdt["c_ar"] = loyers_par_arrdt["c_ar"].astype(str)
    
    # Jointure entre les données de loyers agrégées et les arrondissements pour obtenir un GeoDataFrame final
    gdf_final = gdf_arrdt.merge(loyers_par_arrdt, on="c_ar", how="inner")


    output_dir = os.path.dirname(RENT_PRICE_GOLD)
    os.makedirs(output_dir, exist_ok=True)

    gdf_final.to_parquet(RENT_PRICE_GOLD, engine="pyarrow")

if __name__ == "__main__":
    process_rent_data_to_gold()