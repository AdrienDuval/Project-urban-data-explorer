import os

import geopandas as gpd
import pandas as pd

from src.config import (
    IRIS_GEOJSON,
    THERMAL_COMFORT_SILVER,
    TREES_RAW,
    ISLAND_OF_FRESHNESS_RAW
)


# Fonction de chargement des données géographiques 
# On les projette en Lambert-93 (EPSG:2154) pour faire des calculs de distance en mètres
def _load(path):
    df = gpd.read_file(path).to_crs(epsg=2154)
    return df


def process_thermal_comfort_silver() -> pd.DataFrame:
    
    # On charge les données géographiques des IRIS, des arbres et des îlots de fraîcheur
    iris = _load(IRIS_GEOJSON)
    ilots = _load(ISLAND_OF_FRESHNESS_RAW)
    arbres = _load(TREES_RAW)

    output_dir = os.path.dirname(THERMAL_COMFORT_SILVER)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # On prend uniquement les IRIS dans Paris (dep=75)
    iris = iris[iris['dep'] == '75']

    # Calcul de la densité des arbres par iris : 
    # Jointure entre jeu de données des iris et localisation des arbres
    # On sait donc à quel iris appartient chaque arbre
    arbres_iris = gpd.sjoin(arbres[['geometry']], iris[['code_iris', 'geometry']], how="inner", predicate="within")
    count_arbres = arbres_iris.groupby("code_iris").size().reset_index(name="nb_arbres")

    # Calcul de la surface totale des îlots de fraîcheur par iris :
    # On fait une intersection entre les îlots et les iris pour connaître la surface 
    # d'ilot dans chaque iris
    ilots_iris = gpd.overlay(ilots, iris[['code_iris', 'geometry']], how="intersection")
    ilots_iris["area_ilot"] = ilots_iris.geometry.area
    
    # Agrégation par IRIS
    surf_ilots = ilots_iris.groupby("code_iris")["area_ilot"].sum().reset_index(name="total_area_ilot")

    # On ajoute la surface de l'IRIS lui-même
    iris["surface_iris"] = iris.geometry.area
    # Merge des stats sur le GeoDataFrame IRIS
    silver_gdf = iris.merge(count_arbres, on="code_iris", how="left")
    silver_gdf = silver_gdf.merge(surf_ilots, on="code_iris", how="left")
    
    # Remplir les quartiers sans arbres/îlots par 0
    silver_gdf[["nb_arbres", "total_area_ilot"]] = silver_gdf[["nb_arbres", "total_area_ilot"]].fillna(0)

    # Sauvegarde
    silver_gdf.to_file(THERMAL_COMFORT_SILVER, driver="GeoJSON")
    print("Silver : thermal_comfort_base.geojson créé.")

if __name__ == "__main__":
    process_thermal_comfort_silver()