import json

import geopandas as gpd
import pandas as pd
from src.config import SALE_PRICE_SILVER, SALE_PRICE_GOLD, ARRONDISSEMENTS
from src.db import engine
import os



def process_sale_price_median_to_gold():

    df_price = pd.read_csv(SALE_PRICE_SILVER, sep=";")
    df_arrdt = gpd.read_file(ARRONDISSEMENTS)

    gdf_final = df_arrdt.merge(df_price, left_on="c_ar", right_on="arrondissement")
    
    # Sauvegarde en Parquet (conserve la géométrie native pour d'autres usages)
    gdf_final.to_parquet(SALE_PRICE_GOLD, engine="pyarrow")
    print("🏆 Gold : sale_price_median.parquet prêt pour le Dashboard.")
    
    # 6. Insertion en base de données MySQL
    # Convertir la géométrie en WKT (Well-Known Text) pour MySQL
    df_sql = gdf_final.copy()
    df_sql['geometry'] = df_sql['geometry'].apply(lambda geom: geom.wkt if geom else None)

    for col in df_sql.columns:
        # Si une colonne contient des listes ou des dictionnaires, on les convertit en JSON (texte)
        if df_sql[col].apply(lambda x: isinstance(x, (dict, list))).any():
            print(f"  -> Conversion de la colonne '{col}' en format texte (JSON)")
            df_sql[col] = df_sql[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
    
    # Insertion dans la table 'sale_price_median'
    df_sql.to_sql("sale_price_median", engine, if_exists="replace", index=False)
    print("💾 Données insérées dans la table MySQL 'sale_price_median'.")



if __name__ == "__main__":
    process_sale_price_median_to_gold()