
import os
from src.config import (
    ARRONDISSEMENTS, 
    MAPPING_ZONES_XLSX, 
    QUARTIERS_KML, 
    RENT_DATA_CSV,
    RENT_PRICE_SILVER)
import geopandas as gpd
import pandas as pd


def process_rent_data_to_silver():

    # 1. Charger les quartiers depuis le KML (Source Bronze)
    # Note: 'fiona' est nécessaire pour lire le KML
    # gpd.io.file_io.pyogrio_drivers['KML'] = 'rw'
    df_quartiers_geo = gpd.read_file(QUARTIERS_KML, driver='KML')

    # 2. Charger les arrondissements
    df_arrondissements_geo = gpd.read_file(ARRONDISSEMENTS)

    df_quartiers_geo = df_quartiers_geo.to_crs(epsg=4326)
    df_arrondissements_geo = df_arrondissements_geo.to_crs(epsg=4326)

    quartiers_points = df_quartiers_geo.copy()
    quartiers_points['geometry'] = quartiers_points.geometry.representative_point()

    # Jointure spatiale entre les POINTS des quartiers et les POLYGONES des arrondissements
    df_correspondance = gpd.sjoin(quartiers_points, df_arrondissements_geo, how="left", predicate="intersects")


    # 4. Nettoyer pour n'avoir que le mapping (VAR5 <-> Code Arrondissement)
    # On récupère VAR5 (le code quartier ex: L7501.75229) et le nom de l'arrondissement
    mapping = df_correspondance[['VAR5', 'c_ar']]
    mapping_pd = mapping.copy()


    mapping_zone = pd.read_excel(MAPPING_ZONES_XLSX)

    #Jointure entre le mapping spatial et le mapping de correspondance des zones pour récupérer les codes de quartiers associés à chaque zone de calcul
    mapping_pd = mapping_pd.merge(mapping_zone, left_on="VAR5", right_on="var5", how="inner")

    # 4. Charger les données de loyers (Bronze)
    loyers = pd.read_csv(
        RENT_DATA_CSV, 
        sep=";", 
        encoding="latin1"
    )

    # 5. Filtrage (Lignes où les deux colonnes sont vides/NaN)
    loyers = loyers[
        (loyers["epoque_construction_local"].isna()) & 
        (loyers["epoque_construction_homogene"].isna())
    ]

    # on ne garde que les colonnes qui nous intéressent
    cols_to_keep = ["Zone_calcul", "loyer_median", "loyer_1_quartile", "loyer_3_quartile"]
    loyers = loyers[cols_to_keep]


    # 7. Jointure finale
    # On lie le loyer du quartier à son arrondissement via le mapping spatial
    loyers_complets = loyers.merge(mapping_pd, left_on="Zone_calcul", right_on="var4", how="inner")


    output_dir = os.path.dirname(RENT_PRICE_SILVER)
    os.makedirs(output_dir, exist_ok=True)
    loyers_complets.to_csv(RENT_PRICE_SILVER, sep=";", index=False, encoding="utf-8")

if __name__ == "__main__":  
    process_rent_data_to_silver()  